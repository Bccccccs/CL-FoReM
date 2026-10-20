"""FoReM Task4 (SCWM-style feedback study): policy classes.

FixedGaussianPolicy = the migrated reference GaussianPolicy with ONE explicit, common correctness fix (task4.7 finding):
the reference predict() applied tanh to actions that SB3's SquashedDiagGaussianDistribution had already squashed, so the
EXECUTED action was tanh(tanh(g)) (bounded by +-0.7616) while sample() / update_parameters optimise a single-tanh policy.
Here predict() returns the same squashed action that sample() would draw (deterministic: the mode tanh(mean)), so online
acting, log-prob, actor loss, critic target and temperature update all refer to ONE distribution. The migrated model.py /
sac.py stay byte-identical (Task3 hashes untouched). Both methods (plain / feedback) use this class.

Import `ray` before torch (see task3_env.py); this module imports the reference model, so the caller must do so.
"""
import sys
from pathlib import Path

import torch

FOREM_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = str(FOREM_ROOT / "src" / "modulation_rl" / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from model import GaussianPolicy  # noqa: E402


class FixedGaussianPolicy(GaussianPolicy):
    """Reference GaussianPolicy with a single-tanh predict(). Action space must be [-1, 1]^n (scale 1, bias 0), which makes
    sample() (no scale/bias) and predict() (scale/bias) coincide; this is asserted."""

    def __init__(self, map_space, robot_state_space, num_actions, hidden_dim, action_space=None, use_sde=False):
        super().__init__(map_space, robot_state_space, num_actions, hidden_dim, action_space, use_sde)
        if use_sde:
            raise NotImplementedError("gSDE is not used in this study")
        if not (torch.all(self.action_scale == 1.0) and torch.all(self.action_bias == 0.0)):
            raise ValueError("FixedGaussianPolicy requires an action space [-1, 1]^n")

    def distribution_params(self, map_obs, robot_state):
        """(mean, log_std) before squashing; the single place subclasses (feedback policy) override."""
        mean, log_std, _ = self.forward(map_obs, robot_state)
        return mean, log_std

    def sample(self, map_obs, robot_state):
        mean, log_std = self.distribution_params(map_obs, robot_state)
        return self.action_dist.log_prob_from_params(mean, log_std)

    def predict(self, map_obs, robot_state, eval=False):
        mean, log_std = self.distribution_params(map_obs, robot_state)
        # actions_from_params already returns tanh(gaussian action) (mode() when eval): do NOT squash again
        return self.action_dist.actions_from_params(mean, log_std, deterministic=eval)

    def sample_with_action(self, map_obs, robot_state, actions):
        mean, log_std = self.distribution_params(map_obs, robot_state)
        return self.action_dist.log_prob_from_params_given_action(mean, log_std, actions)
