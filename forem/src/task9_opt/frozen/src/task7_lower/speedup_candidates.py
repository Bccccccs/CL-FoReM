"""Task7.18.3 audit candidates, NOT available to production training.

The >=1000-step strict equivalence gate must pass before adoption. These
candidates failed it under the original GPU nondeterministic flags. Preserve
for inspection and reproducible benchmarks only. SAC math below is copied
from sac.LowerSAC.update_from_batch; only sampling argument validation and
target update dispatch change.
"""
import torch
from torch.nn import functional as F
from torch.distributions import Normal
from .sac import LowerSAC, soft_update


class CandidateSAC(LowerSAC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_backend = "eager"
        self._target_update_graph = None

    def set_update_backend(self, backend):
        """Opt-in audit candidates; eager remains the accepted default.

        async_checks uses the SAME Normal argument constraints on the GPU,
        avoiding their host bool synchronization. The target graph contains
        only the original elementwise soft-update operations, with no RNG,
        optimizer, scheduler, or precision changes.
        """
        if backend not in ("eager", "async_checks", "async_checks_target_graph"):
            raise ValueError("unknown SAC update backend: " + str(backend))
        if backend != "eager" and self.device.type != "cuda":
            raise ValueError("SAC performance candidates require CUDA")
        self.update_backend = backend
        self._target_update_graph = None

    def _sample_update(self, m, v):
        if self.update_backend == "eager":
            return self.policy.sample(m, v)
        mean, std = self.policy.params(m, v)
        scale = std.exp()
        # Normal's real constraint is value == value, and positive is > 0.
        # Preserve validation without synchronizing GPU data back to Python.
        torch._assert_async((mean == mean).all(), "Normal loc constraint failed")
        torch._assert_async((scale > 0).all(), "Normal scale constraint failed")
        dist = Normal(mean, scale, validate_args=False)
        raw = dist.rsample()
        torch._assert_async((raw == raw).all(), "Normal sample constraint failed")
        action = raw.tanh()
        return action, dist.log_prob(raw).sum(-1)-torch.log(1-action.square()+1e-6).sum(-1)

    def _update_target(self):
        if self.update_backend != "async_checks_target_graph":
            soft_update(self.critic_target, self.critic, self.tau)
            return
        if self._target_update_graph is None:
            self._target_update_graph = torch.cuda.CUDAGraph()
            with torch.cuda.graph(self._target_update_graph):
                soft_update(self.critic_target, self.critic, self.tau)
        self._target_update_graph.replay()

    def update_from_batch(self, batch, updates):
        (map_state_batch, rob_state_batch, action_batch, reward_batch,
         next_map_state_batch, next_rob_state_batch, mask_batch) = batch
        with torch.no_grad():
            next_state_action, next_state_log_pi = self._sample_update(next_map_state_batch, next_rob_state_batch)
            qf1_next_target, qf2_next_target = self.critic_target(next_map_state_batch, next_rob_state_batch, next_state_action)
            min_qf_next_target = torch.min(qf1_next_target, qf2_next_target) - self.alpha * next_state_log_pi.unsqueeze(1)
            next_q_value = reward_batch + mask_batch * self.gamma * (min_qf_next_target)
        qf1, qf2 = self.critic(map_state_batch, rob_state_batch, action_batch)
        qf1_loss = F.mse_loss(qf1, next_q_value)
        qf2_loss = F.mse_loss(qf2, next_q_value)
        qf_loss = qf1_loss + qf2_loss

        self.critic_optim.zero_grad()
        qf_loss.backward()
        self._clip(self.critic_optim)
        self.critic_optim.step()
        if self.lr_schedule == "exp_updates":
            self.scheduler_critic_optim.step()

        pi, log_pi = self._sample_update(map_state_batch, rob_state_batch)
        qf1_pi, qf2_pi = self.critic(map_state_batch, rob_state_batch, pi)
        min_qf_pi = torch.min(qf1_pi, qf2_pi)
        policy_loss = ((self.alpha * log_pi) - min_qf_pi).mean()

        self.policy_optim.zero_grad()
        policy_loss.backward()
        self._clip(self.policy_optim)
        self.policy_optim.step()
        if self.lr_schedule == "exp_updates":
            self.scheduler_policy_optim.step()

        if self.automatic_entropy_tuning:
            alpha_loss = -(self.log_alpha * (log_pi + self.target_entropy).detach()).mean()
            self.alpha_optim.zero_grad()
            alpha_loss.backward()
            self._clip(self.alpha_optim)
            self.alpha_optim.step()
            self.alpha = self.log_alpha.exp() * self.max_alpha if self.alpha_rule == "capped" else self.log_alpha.exp()
            alpha_tlogs = self.alpha.clone()
            if self.alpha_rule == "capped" and self.alpha <= self.min_alpha:
                self.alpha = torch.tensor(self.min_alpha)
                self.automatic_entropy_tuning = False
                alpha_tlogs = self.alpha
        else:
            alpha_loss = torch.tensor(0.).to(self.device)
            alpha_tlogs = torch.tensor(self.alpha)

        if updates % self.target_update_interval == 0:
            self._update_target()
        self.update_count += 1
        return qf1_loss.detach(), qf2_loss.detach(), policy_loss.detach(), alpha_loss.detach(), torch.as_tensor(alpha_tlogs).detach()

