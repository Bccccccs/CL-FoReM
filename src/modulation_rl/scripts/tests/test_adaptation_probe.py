"""STAGE0-028 R0-4b: unit tests for adaptation_probe.py's V2 (output-layer-only update) and V3
(gradient-free residual EMA) mechanisms, with a synthetic tiny model/dataset (no ROS/GPU needed)."""
from types import SimpleNamespace

import numpy as np
import torch

from wm.data import ROBOT_DIM
from wm.dynamics import MLPDynamics
from adaptation_probe import episode_errors_output_update, episode_errors_residual_ema


def fake_ds(n_valid=4, dim_action=3, seed=42):
    return SimpleNamespace(n_valid=np.array([n_valid]), obs_offset=np.array([0]), act_offset=np.array([0]),
                            action=np.zeros((n_valid, dim_action), dtype=np.float32),
                            dt=np.full(n_valid, 0.1, dtype=np.float32),
                            seeds=np.array([seed]), episodes=[None])


class IdentityNorm:
    def __call__(self, h):
        return h


DIM = 43  # > ROBOT_DIM=41 so block_mse's map block is non-empty


def zero_init_model(dim=DIM, use_action=True):
    torch.manual_seed(0)
    return MLPDynamics(dim, action_dim=3, hidden=(8,), use_action=use_action)


def test_output_update_only_moves_the_final_layer():
    ds = fake_ds(n_valid=6)
    feats = np.random.default_rng(1).normal(size=(7, DIM)).astype(np.float32) * 3.0
    model = zero_init_model()
    before = {k: v.clone() for k, v in model.state_dict().items()}
    episode_errors_output_update(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=1e-1, k=1)
    for key, value in model.state_dict().items():  # base_model itself must never be mutated
        torch.testing.assert_close(value, before[key])


def test_output_update_returns_one_row_per_step():
    ds = fake_ds(n_valid=5)
    feats = np.random.default_rng(2).normal(size=(6, DIM)).astype(np.float32)
    model = zero_init_model()
    rows = episode_errors_output_update(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=1e-2, k=1)
    assert len(rows) == 5
    assert all(r['step'] == t for t, r in enumerate(rows))


def test_output_update_first_row_matches_frozen_prediction():
    """Before any update fires (step 0, k=1 fires only after step 0 is scored), the prediction
    must equal an unmodified frozen forward pass - same starting weights, no update yet."""
    ds = fake_ds(n_valid=3)
    feats = np.random.default_rng(3).normal(size=(4, DIM)).astype(np.float32)
    model = zero_init_model()
    rows = episode_errors_output_update(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=5e-2, k=5)
    z = torch.as_tensor(feats, dtype=torch.float32)
    a = torch.zeros(1, 3)
    dt = torch.full((1,), 0.1)
    with torch.no_grad():
        expected = model(z[0:1], a, dt)
    total = float(((expected - z[1:2]) ** 2)[..., :41].mean() + ((expected - z[1:2]) ** 2)[..., 41:].mean())
    assert abs(rows[0]['total'] - total) < 1e-5


def test_residual_ema_never_touches_model_parameters():
    ds = fake_ds(n_valid=6)
    feats = np.random.default_rng(4).normal(size=(7, DIM)).astype(np.float32) * 3.0
    model = zero_init_model()
    before = {k: v.clone() for k, v in model.state_dict().items()}
    episode_errors_residual_ema(model, feats, ds, 0, IdentityNorm(), 'cpu', alpha=0.5)
    for key, value in model.state_dict().items():
        torch.testing.assert_close(value, before[key])


def test_residual_ema_first_step_is_uncorrected():
    """ema starts at zero every episode (D11 reset), so step 0's prediction is exactly the raw
    frozen forward pass, with no correction applied yet."""
    ds = fake_ds(n_valid=3)
    feats = np.random.default_rng(5).normal(size=(4, DIM)).astype(np.float32)
    model = zero_init_model()
    rows = episode_errors_residual_ema(model, feats, ds, 0, IdentityNorm(), 'cpu', alpha=0.3)
    z = torch.as_tensor(feats, dtype=torch.float32)
    with torch.no_grad():
        raw = model(z[0:1], torch.zeros(1, 3), torch.full((1,), 0.1))
    expected_total = float((((raw - z[1:2]) ** 2)[..., :41]).mean() + (((raw - z[1:2]) ** 2)[..., 41:]).mean())
    assert abs(rows[0]['total'] - expected_total) < 1e-5


def test_residual_ema_correction_tracks_a_constant_bias():
    """If the model always predicts z_t exactly (identity, since the zero-init net starts as a
    copy model) but the true next feature is offset by a constant vector, the EMA correction
    should converge toward the (unmasked) region of that constant offset and error should shrink
    over the episode."""
    torch.manual_seed(0)
    model = zero_init_model(dim=DIM)
    n = 30
    ds = fake_ds(n_valid=n)
    rng = np.random.default_rng(6)
    base = rng.normal(size=DIM).astype(np.float32)
    bias = np.zeros(DIM, dtype=np.float32)
    bias[:ROBOT_DIM] = 2.0  # only the robot block is biased
    feats = np.stack([base + bias * t for t in range(n + 1)]).astype(np.float32)
    # identity model predicts feats[t] for target feats[t+1] = feats[t] + bias -> constant error=bias every step
    rows = episode_errors_residual_ema(model, feats, ds, 0, IdentityNorm(), 'cpu', alpha=0.5, block='robot')
    assert rows[0]['total'] > rows[-1]['total'], 'EMA correction should shrink the constant-bias error over the episode'
    assert rows[-1]['total'] < 0.05 * rows[0]['total'], 'alpha=0.5 EMA should have converged close to the true bias by step 30'


def test_residual_ema_robot_block_leaves_map_block_uncorrected():
    """block='robot' must never apply the correction to the map (>=ROBOT_DIM) dims, even when
    the map block itself has a large, learnable constant bias."""
    torch.manual_seed(0)
    model = zero_init_model(dim=DIM)
    n = 20
    ds = fake_ds(n_valid=n)
    rng = np.random.default_rng(7)
    base = rng.normal(size=DIM).astype(np.float32)
    bias = np.zeros(DIM, dtype=np.float32)
    bias[ROBOT_DIM:] = 5.0  # only the map block is biased
    feats = np.stack([base + bias * t for t in range(n + 1)]).astype(np.float32)
    rows = episode_errors_residual_ema(model, feats, ds, 0, IdentityNorm(), 'cpu', alpha=0.5, block='robot')
    # map-block error must stay ~constant (uncorrected) since only the robot block is masked in
    maps_errors = [r['maps'] for r in rows]
    assert maps_errors[-1] > 0.5 * maps_errors[0], 'map block must be left uncorrected by block="robot"'
