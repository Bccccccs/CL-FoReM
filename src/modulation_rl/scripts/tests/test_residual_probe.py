"""STAGE0-028 R0-4: unit tests for wm/residual_probe.py's replay logic, with a synthetic tiny
model/dataset so nothing here needs a live encoder, ROS, or GPU."""
from types import SimpleNamespace

import numpy as np
import torch

from wm.dynamics import MLPDynamics
from wm.residual_probe import episode_errors, episode_mean, paired_summary


def fake_ds(n_valid=4, dim_action=3, seed=42):
    return SimpleNamespace(n_valid=np.array([n_valid]), obs_offset=np.array([0]), act_offset=np.array([0]),
                            action=np.zeros((n_valid, dim_action), dtype=np.float32),
                            dt=np.full(n_valid, 0.1, dtype=np.float32),
                            seeds=np.array([seed]), episodes=[None])


class IdentityNorm:
    """norm(h) == h; keeps the arithmetic in these tests transparent."""
    def __call__(self, h):
        return h


# block_mse hardcodes ROBOT_DIM=41 for the robot/map split; DIM must exceed it so the "map"
# block is non-empty (an empty block's torch.mean over 0 elements is NaN, not a real zero error).
DIM = 43


def zero_init_model(dim=DIM, use_action=True):
    torch.manual_seed(0)
    return MLPDynamics(dim, action_dim=3, hidden=(8,), use_action=use_action)


def test_zero_init_model_is_identity_at_construction():
    model = zero_init_model()
    z = torch.randn(2, DIM)
    a = torch.zeros(2, 3)
    dt = torch.full((2,), 0.1)
    out = model(z, a, dt)
    torch.testing.assert_close(out, z)


def test_copy_baseline_ignores_lr_k_and_scores_raw_identity_error():
    ds = fake_ds(n_valid=3)
    feats = np.random.default_rng(0).normal(size=(4, DIM)).astype(np.float32)
    rows = episode_errors(None, feats, ds, 0, IdentityNorm(), 'cpu', lr=1e-3, k=1)
    assert len(rows) == 3
    for t, row in enumerate(rows):
        # block_mse block-balances robot[:41]/map[41:] as two separate means, not a flat mean.
        err = (feats[t] - feats[t + 1]) ** 2
        expected = float(err[:41].mean() + err[41:].mean())
        assert abs(row['total'] - expected) < 1e-5
        assert row['post_warmup'] is False, 'copy baseline never sets post_warmup'


def test_frozen_never_updates_and_reproduces_deterministically():
    ds = fake_ds(n_valid=4)
    feats = np.random.default_rng(1).normal(size=(5, DIM)).astype(np.float32)
    model = zero_init_model()
    before = {k: v.clone() for k, v in model.state_dict().items()}
    rows_a = episode_errors(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=None, k=None)
    rows_b = episode_errors(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=None, k=None)
    assert [r['total'] for r in rows_a] == [r['total'] for r in rows_b]
    assert all(not r['post_warmup'] for r in rows_a), 'lr=None must never mark post_warmup'
    # base_model itself must be untouched (episode_errors deep-copies before any use).
    for key, value in model.state_dict().items():
        torch.testing.assert_close(value, before[key])


def test_updated_treatment_does_not_mutate_base_model():
    ds = fake_ds(n_valid=6)
    feats = np.random.default_rng(2).normal(size=(7, DIM)).astype(np.float32)
    model = zero_init_model()
    before = {k: v.clone() for k, v in model.state_dict().items()}
    episode_errors(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=1e-1, k=1)
    for key, value in model.state_dict().items():
        torch.testing.assert_close(value, before[key])


def test_post_warmup_flag_matches_step_ge_k():
    ds = fake_ds(n_valid=7)
    feats = np.random.default_rng(3).normal(size=(8, DIM)).astype(np.float32)
    model = zero_init_model()
    for k in [1, 3, 5]:
        rows = episode_errors(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=1e-2, k=k)
        assert [r['post_warmup'] for r in rows] == [t >= k for t in range(7)]


def test_update_actually_changes_predictions_after_warmup_when_loss_nonzero():
    """With a non-identity target (so the k-step batch loss is nonzero), the weights must move,
    so at least one post-warmup prediction must differ from what the still-frozen model would
    have predicted at the same step (compared directly, not just via the aggregate error)."""
    ds = fake_ds(n_valid=10)
    rng = np.random.default_rng(4)
    feats = rng.normal(size=(11, DIM)).astype(np.float32) * 3.0  # large-magnitude target drift
    model = zero_init_model()
    k = 2
    frozen_rows = episode_errors(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=None, k=None)
    updated_rows = episode_errors(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=1e-1, k=k)
    post = [t for t in range(10) if t >= k]
    assert post, 'test needs at least one post-warmup step'
    diffs = [abs(updated_rows[t]['total'] - frozen_rows[t]['total']) for t in post]
    assert max(diffs) > 1e-8, 'an update with nonzero loss must change at least one later prediction'


def test_predict_before_update_never_scores_a_transition_the_update_already_used():
    """At step t==k-1 (the last step *before* the first update fires, since the update happens
    after scoring step k-1), the prediction must still come from the pre-update weights: it must
    equal the frozen model's prediction at that same step exactly (same starting weights, no
    update has happened yet by construction of predict-then-update)."""
    ds = fake_ds(n_valid=5)
    feats = np.random.default_rng(5).normal(size=(6, DIM)).astype(np.float32)
    model = zero_init_model()
    k = 3
    frozen_rows = episode_errors(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=None, k=None)
    updated_rows = episode_errors(model, feats, ds, 0, IdentityNorm(), 'cpu', lr=5e-2, k=k)
    for t in range(k):  # steps 0..k-1 predict with the still-untouched clone
        assert abs(updated_rows[t]['total'] - frozen_rows[t]['total']) < 1e-6


def test_episode_mean_respects_post_warmup_filter():
    rows = [dict(total=1.0, post_warmup=False), dict(total=3.0, post_warmup=True), dict(total=5.0, post_warmup=True)]
    assert episode_mean(rows, 'total', post_warmup_only=False) == 3.0
    assert episode_mean(rows, 'total', post_warmup_only=True) == 4.0


def test_paired_summary_matches_manual_diff_and_filters_post_warmup():
    a_by_ep = {0: [dict(total=2.0, post_warmup=True), dict(total=4.0, post_warmup=True)],
               1: [dict(total=10.0, post_warmup=True)]}
    b_by_ep = {0: [dict(total=1.0, post_warmup=True), dict(total=1.0, post_warmup=True)],
               1: [dict(total=9.0, post_warmup=True)]}
    out = paired_summary(a_by_ep, b_by_ep, [0, 1], np.array([1, 2]), 'total', post_warmup_only=True)
    # ep0: mean(a)=3, mean(b)=1 -> diff=2; ep1: mean(a)=10, mean(b)=9 -> diff=1
    assert out['episodes'] == 2
    assert abs(out['mean'] - 1.5) < 1e-9
    assert out['a_better_fraction'] == 0.0  # both diffs positive, a is never "better" (lower)


def test_paired_summary_drops_episodes_with_no_matching_steps():
    a_by_ep = {0: [dict(total=2.0, post_warmup=False)]}  # no post_warmup step at all
    b_by_ep = {0: [dict(total=1.0, post_warmup=False)]}
    out = paired_summary(a_by_ep, b_by_ep, [0], np.array([1]), 'total', post_warmup_only=True)
    assert out['episodes'] == 0
    assert np.isnan(out['mean'])
