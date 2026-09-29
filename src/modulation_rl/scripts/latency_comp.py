"""SCREEN-028 L3 (exploratory, no training): world-model compensation of a delayed observation.

The frozen SAC policy would normally act on the delayed observation o_{t-k}. Here the delayed
observation is encoded (fixed encoder = the policy's own CNN), rolled forward k steps by the
action-conditioned world model with the actions that were actually executed since (a_{t-k}..a_{t-1}),
and the policy's deterministic action head is applied to the estimated current feature:

    z = norm(encoder(o_{t-k}));  z <- model(z, a_j, dt) for j = t-k..t-1;
    action = tanh(mean_linear(post_fc_stack(norm^-1(z)))) * scale + bias

Map-only latency: the world model still starts from the delayed (robot, map) pair, but only the map
block of the rolled feature is used; the robot block is replaced by the true current robot_state
(joint encoders are fast). Reuses foresight.deterministic_action_from_feature, whose equality with
policy.predict(..., eval=True) is unit-tested (tests/test_foresight.py, tests/test_latency_comp.py).
This file deliberately lives outside scripts/wm/ (code_identity()).
"""
import json
from pathlib import Path

import numpy as np
import torch

import foresight
from wm.data import ROBOT_DIM

SIM_DT = foresight.SIM_DT


class WMCompensator:
    def __init__(self, encoder, model, norm, policy, device='cpu'):
        self.encoder, self.model, self.norm, self.policy = encoder, model, norm, policy
        self.device = device

    @classmethod
    def from_config(cls, path):
        config = json.loads(Path(path).read_text())
        device = config.get('device', 'cuda')
        from wm.encoder import FixedEncoder
        from residual_probe import load_model
        encoder = FixedEncoder(config['encoder_checkpoint'], device)
        model, norm, _ = load_model(config['dynamics_checkpoint'], device)
        policy = foresight.load_full_policy(config['encoder_checkpoint'], device)
        return cls(encoder, model, norm, policy, device)

    @torch.no_grad()
    def encode(self, obs):
        robot = np.asarray(obs[0], dtype=np.float32)[None]
        local_map = np.asarray(obs[1], dtype=np.float32)[None]
        return self.encoder(robot, local_map)

    @torch.no_grad()
    def rollout(self, z_std, actions):
        """Roll standardized feature z_std (1,dim) through the recorded `actions` (n,3)."""
        dt = torch.full((1,), SIM_DT, dtype=torch.float32, device=self.device)
        for action in actions:
            a = torch.as_tensor(action, dtype=torch.float32, device=self.device).unsqueeze(0)
            z_std = self.model(z_std, a, dt)
        return z_std

    @torch.no_grad()
    def estimated_feature(self, transform):
        """Estimated current raw (un-standardized) feature [robot | cnn(map)], shape (1, dim)."""
        map_only = transform.robot_delay == 0
        delay = transform.map_delay
        if transform.robot_delay not in (0, delay):
            raise ValueError('WM compensation supports full latency or map-only latency, not a mix')
        start = transform.raw(delay)
        steps = min(delay, transform.t)
        z0 = self.norm(self.encode(start))
        z = self.rollout(z0, transform.recent_actions(steps) if steps else np.zeros((0, 3), np.float32))
        z_raw = self.norm.inverse(z)
        if map_only and delay:
            current_robot = torch.as_tensor(np.asarray(transform.raw(0)[0], dtype=np.float32),
                                            device=self.device).unsqueeze(0)
            z_raw = torch.cat([current_robot, z_raw[:, ROBOT_DIM:]], dim=-1)
        return z_raw

    @torch.no_grad()
    def act(self, transform):
        z_raw = self.estimated_feature(transform)
        action = foresight.deterministic_action_from_feature(self.policy, z_raw)
        return action[0].detach().cpu().numpy()
