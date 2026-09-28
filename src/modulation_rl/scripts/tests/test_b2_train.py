"""FOLLOWUP-028 B2 (D51-B2): unit tests for b2_train.py's file discovery, split assignment,
feature-array assembly, and train/threshold wiring - synthetic fixtures, no live encoder/GPU/ROS."""
import numpy as np
import pytest
import torch

from b2_train import build_split_features, discover_episodes, split_of, train_and_evaluate
from wm.dynamics import MLPDynamics, Normalizer


def test_split_of_matches_d51_registration():
    assert split_of(1000) == 'train' and split_of(1699) == 'train'
    assert split_of(1700) == 'val' and split_of(1799) == 'val'
    assert split_of(1800) == 'test' and split_of(1999) == 'test'
    assert split_of(999) is None and split_of(2000) is None


def test_discover_episodes_requires_both_files(tmp_path):
    (tmp_path / 'episode-01000-observations.npz').write_bytes(b'')
    (tmp_path / 'episode-01000-stepinfo.npz').write_bytes(b'')
    (tmp_path / 'episode-01001-observations.npz').write_bytes(b'')  # no matching stepinfo
    found = discover_episodes(tmp_path)
    assert list(found.keys()) == [1000]


def synthetic_episode(seed, n, dim, fail_at=None, rng=None):
    rng = rng or np.random.default_rng(seed)
    z = rng.normal(size=(n + 1, dim))
    a = rng.uniform(-1, 1, size=(n, 3))
    kin = np.zeros(n, dtype=bool)
    if fail_at is not None:
        kin[fail_at] = True
    return dict(z_std=z, action=a, n=n,
                step=dict(kin_failure=kin, dist_to_desired=rng.random(n), rot_dist_to_desired=rng.random(n),
                          goal_to_base_distance=rng.random(n), selfcollision=np.zeros(n, bool),
                          base_collision=np.zeros(n, bool), nr_kin_failures=np.cumsum(kin)))


def test_build_split_features_shapes_and_masks_are_consistent():
    dim = 44
    episodes = {1000: synthetic_episode(1000, 20, dim, fail_at=[5, 12]),
                1001: synthetic_episode(1001, 15, dim, fail_at=None)}
    out = build_split_features([1000, 1001], episodes, dynamics=None, dyn_norm_dyn=None, policy=None,
                                K=5, device='cpu', compute_wm=False)
    assert out['geo'].shape == (35, 3)
    assert out['cur'].shape[0] == 35
    assert out['hist'].shape[0] == 35
    assert out['y5'].shape == (35,) and out['m5'].shape == (35,)
    assert set(out['episode_id'].tolist()) == {1000, 1001}
    # episode 1000 has a real IK failure at t=5 -> some True label should exist among its steps
    ep0_mask = out['episode_id'] == 1000
    assert out['y5'][ep0_mask].any()


def test_train_and_evaluate_masking_alignment_and_threshold(tmp_path):
    rng = np.random.default_rng(0)
    n = 400
    dim = 5
    X_all = rng.normal(size=(n, dim)).astype(np.float64)
    y_all = (X_all[:, 0] > 0.3).astype(bool)  # learnable signal on the first dim
    mask = np.ones(n, dtype=bool)
    mask[::7] = False  # simulate fail[t-1] filtering removing some steps
    episode_id = np.repeat(np.arange(20), n // 20)
    split_data = {}
    for split, sl in [('train', slice(0, 240)), ('val', slice(240, 320)), ('test', slice(320, 400))]:
        split_data[split] = dict(y5=y_all[sl], m5=mask[sl], episode_id=episode_id[sl])
    X = {'train': X_all[0:240], 'val': X_all[240:320], 'test': X_all[320:400]}
    result = train_and_evaluate('C-test', 'logistic', X, split_data, 'y5', 'm5', device='cpu')
    assert result['n_train'] == int(mask[0:240].sum())
    assert result['n_test'] == int(mask[320:400].sum())
    assert 0.5 <= result['test_auroc']['point'] <= 1.0  # learnable signal -> should beat chance
    import foresight
    thr = foresight.select_threshold_for_rate(result['val_scores'], 0.1)
    assert isinstance(thr, float)
