"""SCREEN-028 L3: WMCompensator action-head consistency and rollout ordering (synthetic fixtures)."""
import gym
import numpy as np
import pytest
import torch

import foresight
from latency_comp import WMCompensator
from model import GaussianPolicy
from policy_input import PolicyInputTransform
from wm.data import ROBOT_DIM
from wm.dynamics import CopyModel, MLPDynamics, Normalizer


class FakeEncoder:
    """Same computation as wm.encoder.FixedEncoder.forward, from an in-memory policy."""

    def __init__(self, policy):
        self.cnn = policy.cnn

    @torch.no_grad()
    def __call__(self, robot, local_map):
        robot = torch.as_tensor(robot, dtype=torch.float32)
        x = torch.as_tensor(local_map, dtype=torch.float32).permute(0, 3, 1, 2).contiguous(memory_format=torch.channels_last)
        return torch.cat([robot, self.cnn(x)], dim=-1)


def make(model=None, seed=0):
    torch.manual_seed(seed)
    policy = GaussianPolicy(gym.spaces.Box(0., 1., (120, 120, 1), dtype=np.float32),
                            gym.spaces.Box(-np.inf, np.inf, (ROBOT_DIM,), dtype=np.float32), 3, [64, 64],
                            gym.spaces.Box(-1., 1., (3,), dtype=np.float32), use_sde=False).eval()
    dim = ROBOT_DIM + policy.cnn.output_size
    g = torch.Generator().manual_seed(seed + 1)
    norm = Normalizer(torch.randn(dim, generator=g), torch.rand(dim, generator=g) + 0.5)
    return policy, WMCompensator(FakeEncoder(policy), model if model is not None else CopyModel(), norm, policy, 'cpu'), dim


def fake_obs(seed):
    rng = np.random.default_rng(seed)
    return (rng.normal(size=ROBOT_DIM).astype(np.float32).tolist(), rng.random((120, 120, 1)) < 0.05)


def predict(policy, obs):
    with torch.no_grad():
        return policy.predict(torch.as_tensor(obs[1], dtype=torch.float32)[None], torch.as_tensor(obs[0], dtype=torch.float32)[None], eval=True)[0].numpy()


def drive(tr, n):
    obs = [fake_obs(i) for i in range(n + 1)]
    tr.reset(obs[0])
    for t in range(1, n + 1):
        tr.step(np.array([0.1 * t, -0.1 * t, 0.05 * t], dtype=np.float32), obs[t])
    return obs


def test_k0_compensated_action_equals_policy_predict():
    policy, comp, _ = make()
    tr = PolicyInputTransform(obs_latency=0)
    obs = drive(tr, 3)
    assert np.allclose(comp.act(tr), predict(policy, obs[3]), atol=1e-5)


def test_full_latency_with_identity_dynamics_equals_policy_on_delayed_obs():
    policy, comp, _ = make()
    tr = PolicyInputTransform(obs_latency=3)
    obs = drive(tr, 6)
    assert np.allclose(comp.act(tr), predict(policy, obs[3]), atol=1e-5)  # o_{6-3}
    tr2 = PolicyInputTransform(obs_latency=3)
    obs2 = drive(tr2, 1)  # t < k -> initial observation, zero rolled steps
    assert np.allclose(comp.act(tr2), predict(policy, obs2[0]), atol=1e-5)


def test_rollout_applies_recorded_actions_in_order():
    torch.manual_seed(5)
    policy, comp, _ = make()
    model = MLPDynamics(ROBOT_DIM + policy.cnn.output_size, hidden=(16,))
    for p in model.parameters():
        torch.nn.init.normal_(p, std=0.05)
    comp.model = model
    tr = PolicyInputTransform(obs_latency=2)
    obs = drive(tr, 5)
    z = comp.norm(comp.encode(obs[3]))
    dt = torch.full((1,), 0.1)
    # recent_actions(2) at t=5 are the last two executed actions, oldest first
    recent = tr.recent_actions(2)
    expected = z
    for a in recent:
        expected = model(expected, torch.as_tensor(a)[None], dt)
    got = comp.estimated_feature(tr)
    assert torch.allclose(got, comp.norm.inverse(expected), atol=1e-5)
    reversed_order = z
    for a in recent[::-1]:
        reversed_order = model(reversed_order, torch.as_tensor(a)[None], dt)
    assert not torch.allclose(comp.norm.inverse(reversed_order), got, atol=1e-6), 'order must matter'


def test_map_only_uses_true_current_robot_block_and_rolled_map_block():
    policy, comp, dim = make()
    tr = PolicyInputTransform(map_latency=2)
    obs = drive(tr, 5)
    z = comp.estimated_feature(tr)
    assert np.allclose(z[0, :ROBOT_DIM].numpy(), np.asarray(obs[5][0], dtype=np.float32), atol=1e-6)
    delayed_map_feature = comp.norm.inverse(comp.norm(comp.encode(obs[3])))[0, ROBOT_DIM:]
    assert torch.allclose(z[0, ROBOT_DIM:], delayed_map_feature, atol=1e-5)  # identity dynamics


def test_mixed_latency_rejected():
    _, comp, _ = make()
    tr = PolicyInputTransform(obs_latency=1, map_latency=3)
    drive(tr, 4)
    with pytest.raises(ValueError):
        comp.act(tr)
