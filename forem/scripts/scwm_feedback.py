"""FoReM Task4.10: SCWM-style pre-execution internal feedback for the Husky SAC actor.

  h        = actor trunk(o)                      (map CNN + post-concat FC stack, 256-d, the policy's OWN trunk, keeps learning)
  a0       = tanh(mean_linear(h))                deterministic candidate, never executed
  z        = E_ref(o)                            frozen reference representation (task4.9)
  delta    = F_phi(z, a0) - z                    predicted change of the task-relevant representation (frozen weights; the input gradient
                                                 d delta / d a0 is KEPT, so the actor sees the full chain rule through the frozen model)
  h'       = h + sigmoid(W_g [h; delta_n]) * (W_d [h; delta_n])      W_d zero-initialised => the policy equals the plain policy at the fork
  (mean, log_std) = heads(h')   -> ONE squashed Gaussian; sample / log-prob / mode all come from it, for acting, actor loss and critic target.

Only the final action is executed. delta is a prediction, not an error label: nothing minimises it. `feedback_enabled=False` bypasses G
and reproduces FixedGaussianPolicy exactly (interface regression, not a third experimental arm).
"""
import torch
import torch.nn as nn

from scwm_policy import FixedGaussianPolicy


class FeedbackGaussianPolicy(FixedGaussianPolicy):
    def __init__(self, map_space, robot_state_space, num_actions, hidden_dim, action_space=None, use_sde=False,
                 ref_encoder=None, world_model=None, feedback_enabled=True):
        super().__init__(map_space, robot_state_space, num_actions, hidden_dim, action_space, use_sde)
        if ref_encoder is None or world_model is None:
            raise ValueError("FeedbackGaussianPolicy needs a frozen reference encoder and a trained world model")
        H = hidden_dim[-1]
        self.ref_encoder = ref_encoder
        self.world_model = world_model
        for m in (self.ref_encoder, self.world_model):
            for p in m.parameters():
                p.requires_grad_(False)
        zd = int(world_model.z_dim)
        self.feedback_gate = nn.Linear(H + zd, H)
        self.feedback_delta = nn.Linear(H + zd, H)
        nn.init.zeros_(self.feedback_delta.weight)
        nn.init.zeros_(self.feedback_delta.bias)
        self.feedback_enabled = bool(feedback_enabled)
        self.last_diag = {}

    def train(self, mode=True):
        super().train(mode)
        self.ref_encoder.eval()          # frozen modules never leave eval mode
        self.world_model.eval()
        return self

    def trunk(self, map_obs, robot_state):
        local_map = map_obs.permute([0, 3, 1, 2]).contiguous(memory_format=torch.channels_last)
        out = torch.cat([robot_state, self.cnn(local_map)], dim=-1)
        return self.post_fc_stack(out)

    def heads(self, h):
        mean = self.mean_linear(h)
        log_std = torch.clamp(self.log_std_linear(h), min=-20, max=2)
        return mean, log_std

    def distribution_params(self, map_obs, robot_state, z_ref=None, return_diag=False):
        h = self.trunk(map_obs, robot_state)
        mean0, log_std0 = self.heads(h)
        if not self.feedback_enabled:
            return (mean0, log_std0, {}) if return_diag else (mean0, log_std0)
        a0 = torch.tanh(mean0)                                   # candidate; part of the autograd graph on purpose
        z = self.ref_encoder(map_obs, robot_state) if z_ref is None else z_ref
        z_hat = self.world_model(z, a0)                          # frozen weights, differentiable in a0
        if not torch.isfinite(z_hat).all():
            raise FloatingPointError("world model produced a non-finite prediction")
        delta_n = (z_hat - z - self.world_model.d_mean) / self.world_model.d_std
        x = torch.cat([h, delta_n], dim=-1)
        h2 = h + torch.sigmoid(self.feedback_gate(x)) * self.feedback_delta(x)
        mean, log_std = self.heads(h2)
        if return_diag:
            return mean, log_std, dict(a0=a0.detach(), delta_n=delta_n.detach(), z=z.detach(), z_hat=z_hat.detach(),
                                       mean0=mean0.detach(), shift=(mean - mean0).detach())
        return mean, log_std
