"""FOLLOWUP-028 A line (D50): unit tests for structured_adaptation.py's V4 (gain)/V5 (delay)
online, gradient-free estimators, using synthetic 'known gain'/'known delay' trajectories built
from a small deterministic MLPDynamics so ground truth is exactly known (no live encoder/GPU)."""
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from wm.dynamics import MLPDynamics
from structured_adaptation import episode_replay, _delayed_action

DIM = 43  # > ROBOT_DIM=41 so the map block (dims 41:) is non-empty, as in test_residual_probe.py


class IdentityNorm:
    def __call__(self, h):
        return h

    def inverse(self, z):
        return z


def make_model(seed=0, dim=DIM, hidden=(8,)):
    torch.manual_seed(seed)
    model = MLPDynamics(dim, action_dim=3, hidden=hidden, use_action=True)
    # zero-init leaves the model an identity (copy) model; give it real, non-trivial weights so
    # delta_hat is a non-zero function of (z,a,dt).
    with torch.no_grad():
        for p in model.net.parameters():
            p.normal_(0, 0.05)
    return model.eval()


def fake_ds(n, actions, dts):
    return SimpleNamespace(n_valid=np.array([n]), obs_offset=np.array([0]), act_offset=np.array([0]),
                            action=actions.numpy(), dt=dts.numpy(), seeds=np.array([1]), episodes=[None])


def synthesize_gain_trajectory(model, n, dim, true_gain, seed=0):
    """z_{t+1} = z_t + true_gain * delta_hat(z_t, a_t) - i.e. the environment behaves exactly like
    the frozen model's own prediction, uniformly scaled by true_gain (chassis dims unmodified/no
    delay: this isolates the gain-only case)."""
    rng = np.random.default_rng(seed)
    actions = torch.as_tensor(rng.uniform(-1, 1, size=(n, 3)), dtype=torch.float32)
    dts = torch.full((n,), 0.1, dtype=torch.float32)
    z = torch.zeros(n + 1, dim)
    z[0] = torch.as_tensor(rng.normal(size=dim), dtype=torch.float32)
    for t in range(n):
        with torch.no_grad():
            delta_hat = model(z[t:t + 1], actions[t:t + 1], dts[t:t + 1]) - z[t:t + 1]
        z[t + 1] = z[t] + true_gain * delta_hat[0]
    return z.numpy(), actions, dts


def synthesize_delay_trajectory(model, n, dim, true_delay, seed=0):
    """z_{t+1} = z_t + delta_hat(z_t, a_{t-true_delay}) (chassis dims only; dim0 is the recorded
    a_t itself, matching _delayed_action's convention) - the environment reacts to a stale chassis
    command, gain=1."""
    rng = np.random.default_rng(seed)
    actions = torch.as_tensor(rng.uniform(-1, 1, size=(n, 3)), dtype=torch.float32)
    dts = torch.full((n,), 0.1, dtype=torch.float32)
    z = torch.zeros(n + 1, dim)
    z[0] = torch.as_tensor(rng.normal(size=dim), dtype=torch.float32)
    for t in range(n):
        a_delayed = _delayed_action(actions, t, true_delay)
        with torch.no_grad():
            delta_hat = model(z[t:t + 1], a_delayed, dts[t:t + 1]) - z[t:t + 1]
        z[t + 1] = z[t] + delta_hat[0]
    return z.numpy(), actions, dts


@pytest.mark.parametrize('true_gain', [0.5, 2.0])
def test_v4_recovers_known_gain_and_beats_frozen(true_gain):
    model = make_model(seed=1)
    n = 80
    z, actions, dts = synthesize_gain_trajectory(model, n, DIM, true_gain, seed=2)
    ds = fake_ds(n, actions, dts)
    rows_v0, _ = episode_replay(model, z, ds, 0, IdentityNorm(), 'cpu', 'V0')
    rows_v4, diag_v4 = episode_replay(model, z, ds, 0, IdentityNorm(), 'cpu', 'V4_robot')
    frozen_mean = np.mean([r['total'] for r in rows_v0])
    v4_mean = np.mean([r['total'] for r in rows_v4])
    # A gain-scaled rollout compounds nonlinearly (the MLP is evaluated at a drifted z_t each
    # step), so a single scalar correction does not zero out the error, but it should still help
    # substantially; the tight check is the gain recovery below.
    assert v4_mean < frozen_mean * 0.75
    # the running gain estimate should converge close to the true gain by the end of the episode
    final_estimates = [d for d in diag_v4[-10:] if d is not None]
    assert np.mean(final_estimates) == pytest.approx(true_gain, abs=0.15)


@pytest.mark.parametrize('true_delay', [2, 5])
def test_v5_recovers_known_delay_and_beats_frozen(true_delay):
    model = make_model(seed=3)
    n = 80
    z, actions, dts = synthesize_delay_trajectory(model, n, DIM, true_delay, seed=4)
    ds = fake_ds(n, actions, dts)
    rows_v0, _ = episode_replay(model, z, ds, 0, IdentityNorm(), 'cpu', 'V0')
    rows_v5, diag_v5 = episode_replay(model, z, ds, 0, IdentityNorm(), 'cpu', 'V5')
    frozen_mean = np.mean([r['total'] for r in rows_v0])
    v5_mean = np.mean([r['total'] for r in rows_v5])
    assert v5_mean < frozen_mean * 0.5
    final_selected = diag_v5[-10:]
    assert max(set(final_selected), key=final_selected.count) == true_delay


def test_delayed_action_zero_pads_before_episode_start():
    actions = torch.arange(9, dtype=torch.float32).reshape(3, 3)
    a = _delayed_action(actions, 0, 2)
    assert torch.equal(a[0, 1:3], torch.zeros(2))
    assert a[0, 0] == actions[0, 0]  # dim 0 always the current, undelayed action
    a2 = _delayed_action(actions, 2, 1)
    assert torch.equal(a2[0, 1:3], actions[1, 1:3])
