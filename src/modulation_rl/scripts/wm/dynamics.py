"""P1a one-step predictors in the fixed, standardized feature space.

predict(h_t, a_t, dt) -> h_pred_next. All models predict a residual (increment) on standardized features:
- CopyModel: h_next = h (baseline 1)
- MLP with use_action=False: no-action baseline, input [h, dt] (baseline 2)
- MLP with use_action=True: action-conditioned model, input [h, a, dt]
Initial config (two 256-wide ReLU layers) is an engineering choice, not a paper hyperparameter.
"""
import torch
from torch import nn


class Normalizer(nn.Module):
    """Per-dimension standardization with training-set statistics. Dimensions that are (near) constant in the
    training set are centred but not scaled (std set to 1), so held-out variation is not amplified ~1/floor."""

    def __init__(self, mean, std, floor=1e-3):
        super().__init__()
        std = torch.as_tensor(std, dtype=torch.float32)
        self.register_buffer('mean', torch.as_tensor(mean, dtype=torch.float32))
        self.register_buffer('std', torch.where(std < floor, torch.ones_like(std), std))

    def forward(self, h):
        return (h - self.mean) / self.std

    def inverse(self, z):
        return z * self.std + self.mean


class CopyModel(nn.Module):
    use_action = False

    def forward(self, z, action, dt):
        return z


class MLPDynamics(nn.Module):
    def __init__(self, dim, action_dim=3, hidden=(256, 256), use_action=True):
        super().__init__()
        self.use_action = use_action
        layers, size = [], dim + (action_dim if use_action else 0) + 1
        for width in hidden:
            layers += [nn.Linear(size, width), nn.ReLU()]
            size = width
        layers.append(nn.Linear(size, dim))
        self.net = nn.Sequential(*layers)
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)  # starts as the copy model

    def forward(self, z, action, dt):
        parts = [z] + ([action] if self.use_action else []) + [dt.reshape(-1, 1)]
        return z + self.net(torch.cat(parts, dim=-1))


def rollout(model, z0, actions, dts):
    """Open-loop k-step prediction from z0 with the recorded actions; never sees true intermediate features."""
    z, out = z0, []
    for i in range(actions.shape[1]):
        z = model(z, actions[:, i], dts[:, i])
        out.append(z)
    return torch.stack(out, dim=1)
