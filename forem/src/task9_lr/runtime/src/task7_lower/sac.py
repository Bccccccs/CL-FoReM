"""CBL update math copied verbatim from scwm_sac.py (SRC-0470).
Source commit2380ff51 / SHA256 06e6335cee2ad1dbaa63928942c6eb6aecbf9cec0bc904fa4bc834e3870e08d1.
Only constructor/network/observation path is new; capped rule preserved.
"""
import torch
from task9_lr.diagnostics import hook
from torch import nn
from torch.nn import functional as F
from torch.optim import Adam
from torch.optim.lr_scheduler import LambdaLR
from .networks import Actor,TwinQ
from .observation import preprocess

def soft_update(target,source,tau):
    for t,s in zip(target.parameters(),source.parameters()):t.data.copy_(t.data*(1-tau)+s.data*tau)

class LowerSAC:
    def __init__(self,vector_dim,device,total_updates=4999743):
        self.device=torch.device(device);self.gamma=.99;self.tau=.001;self.alpha=1.0
        self.max_alpha=.35;self.min_alpha=.05;self.lr_start=1e-4;self.lr_end=1e-6
        self.num_steps=total_updates;self.target_update_interval=1;self.target_entropy=-3
        self.automatic_entropy_tuning=True;self.alpha_rule='capped';self.lr_schedule='exp_updates';self.env_steps=0;self.update_count=0
        self.policy=Actor(vector_dim).to(device);self.critic=TwinQ(vector_dim).to(device);self.critic_target=TwinQ(vector_dim).to(device)
        self.critic_target.load_state_dict(self.critic.state_dict())
        self.policy_optim=Adam(self.policy.parameters(),lr=self.lr_start);self.critic_optim=Adam(self.critic.parameters(),lr=self.lr_start)
        schedule=lambda n:(self.lr_end/self.lr_start)**(n/self.num_steps)
        self.scheduler_policy_optim=LambdaLR(self.policy_optim,schedule);self.scheduler_critic_optim=LambdaLR(self.critic_optim,schedule)
        self.log_alpha=torch.zeros(1,requires_grad=True,device=device);self.alpha_optim=Adam([self.log_alpha],lr=1e-6)
    @torch.no_grad()
    def select_action(self,observation,deterministic=True):
        """dict[str,Tensor] batched Core observation -> Tensor[E,3] on same device."""
        m,v=preprocess(observation)
        hook('policy_input',observation,m,v)
        return self.policy.predict(m,v,deterministic)

    def update_from_batch(self, batch, updates):
        (map_state_batch, rob_state_batch, action_batch, reward_batch,
         next_map_state_batch, next_rob_state_batch, mask_batch) = batch
        with torch.no_grad():
            next_state_action, next_state_log_pi = self.policy.sample(next_map_state_batch, next_rob_state_batch)
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

        pi, log_pi = self.policy.sample(map_state_batch, rob_state_batch)
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
            soft_update(self.critic_target, self.critic, self.tau)
        self.update_count += 1
        return qf1_loss.detach(), qf2_loss.detach(), policy_loss.detach(), alpha_loss.detach(), torch.as_tensor(alpha_tlogs).detach()

    @staticmethod
    def _clip(optim, max_norm=10):
        for param_group in optim.param_groups:
            params = list(filter(lambda p: p.grad is not None, param_group["params"]))
            if params:
                nn.utils.clip_grad_norm_(params, max_norm)

    def full_state_dict(self):
        state = dict(policy=self.policy.state_dict(), critic=self.critic.state_dict(), critic_target=self.critic_target.state_dict(),
                    critic_optim=self.critic_optim.state_dict(), policy_optim=self.policy_optim.state_dict(),
                    log_alpha=self.log_alpha.detach().cpu(), alpha_optim=self.alpha_optim.state_dict(),
                    sched_critic=self.scheduler_critic_optim.state_dict(), sched_policy=self.scheduler_policy_optim.state_dict(),
                    alpha=float(self.alpha), automatic_entropy_tuning=bool(self.automatic_entropy_tuning),
                    update_count=int(self.update_count))
        if self.alpha_rule != "capped" or self.lr_schedule != "exp_updates":
            state["d14"] = dict(alpha_rule=self.alpha_rule, lr_schedule=self.lr_schedule, env_steps=self.env_steps)
        return state

    def load_full_state_dict(self, s):
        options = s.get("d14", dict(alpha_rule="capped", lr_schedule="exp_updates", env_steps=0))
        if options["alpha_rule"] != self.alpha_rule or options["lr_schedule"] != self.lr_schedule:
            raise ValueError("D14 resume options mismatch")
        self.env_steps = int(options["env_steps"])
        self.policy.load_state_dict(s["policy"])
        self.critic.load_state_dict(s["critic"])
        self.critic_target.load_state_dict(s["critic_target"])
        self.critic_optim.load_state_dict(s["critic_optim"])
        self.policy_optim.load_state_dict(s["policy_optim"])
        with torch.no_grad():
            self.log_alpha.copy_(s["log_alpha"].to(self.device))
        self.alpha_optim.load_state_dict(s["alpha_optim"])
        self.scheduler_critic_optim.load_state_dict(s["sched_critic"])
        self.scheduler_policy_optim.load_state_dict(s["sched_policy"])
        self.automatic_entropy_tuning = bool(s["automatic_entropy_tuning"])
        # reference: alpha is a tensor derived from log_alpha while tuning, a fixed min_alpha tensor afterwards, a float before the first update
        if self.automatic_entropy_tuning and s["update_count"] > 0:
            self.alpha = self.log_alpha.exp() * self.max_alpha if self.alpha_rule == "capped" else self.log_alpha.exp()
        elif s["update_count"] > 0:
            self.alpha = torch.tensor(self.min_alpha)
        else:
            self.alpha = float(s["alpha"])
        self.update_count = int(s["update_count"])
