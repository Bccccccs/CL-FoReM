"""SCREEN-028 statistics: vectorized bootstrap equals a slow reference; decision rules; replay compaction."""
import numpy as np
import pytest

import screen_stats as st


def slow_paired(a, b, n, seed):
    a, b = np.atleast_2d(a), np.atleast_2d(b)
    S, N = a.shape
    rng = np.random.default_rng(seed)
    out = []
    for start in range(0, n, st.CHUNK):
        count = min(st.CHUNK, n - start)
        idx = rng.integers(0, N, size=(count, S, N))
        for c in range(count):
            out.append(np.mean([ (a[s][idx[c, s]] - b[s][idx[c, s]]).mean() for s in range(S)]))
    return np.array(out)


def test_vectorized_bootstrap_matches_slow_reference():
    rng = np.random.default_rng(1)
    a = (rng.random((2, 40)) < 0.7).astype(float)
    b = (rng.random((2, 40)) < 0.5).astype(float)
    fast = st.bootstrap_diffs(a, b, n_boot=1200, seed=5)
    slow = slow_paired(a, b, 1200, 5)
    assert np.allclose(fast, slow)


def test_diff_point_and_ci_sane_and_pairing_matters():
    a = np.ones(100); b = np.zeros(100)
    r = st.diff_with_ci(a, b, n_boot=500)
    assert r['point'] == 1.0 and r['ci95'] == [1.0, 1.0]
    same = np.tile([1.0, 0.0], 50)
    r = st.diff_with_ci(same, same, n_boot=500)
    assert r['point'] == 0.0 and r['ci95'] == [0.0, 0.0]  # identical paired arrays -> zero-width CI


def test_stratified_resampling_stays_within_stratum():
    a = np.stack([np.ones(50), np.zeros(50)])  # stratum 0 all ones, stratum 1 all zeros
    b = np.zeros((2, 50))
    s = st.bootstrap_diffs(a, b, n_boot=300)
    assert np.allclose(s, 0.5), 'pooled mean must always be exactly the mean of the two strata'


def test_bootstrap_10000_resamples_is_fast():
    import time
    a = (np.random.default_rng(0).random((2, 100)) < .6).astype(float)
    t = time.time(); st.diff_with_ci(a, 1 - a); assert time.time() - t < 5


def test_shape_mismatch_rejected():
    with pytest.raises(ValueError):
        st.bootstrap_diffs(np.ones((2, 10)), np.ones((2, 9)))


def test_recovery_ratio_point_and_degenerate():
    n = np.array([1.0] * 80 + [0.0] * 20); s = np.array([1.0] * 40 + [0.0] * 60); c = np.array([1.0] * 60 + [0.0] * 40)
    r = st.recovery_ratio(n, s, c, n_boot=500)
    assert r['point'] == pytest.approx(0.5) and r['denominator'] == pytest.approx(0.4)
    r0 = st.recovery_ratio(s, n, c, n_boot=200)  # nominal worse than stale -> undefined
    assert r0['point'] is None


def test_l1_pass_rule_boundaries():
    assert st.l1_config_passes(-0.15, [-0.25, -0.05])
    assert not st.l1_config_passes(-0.14, [-0.25, -0.05])       # drop too small
    assert not st.l1_config_passes(-0.20, [-0.30, 0.01])        # CI upper bound not < 0
    assert not st.l1_config_passes(-0.20, [-0.30, 0.0])         # 0 is not < 0


def test_l1_decision_k_sel_rules():
    d = st.l1_decision(dict(full={1: False, 2: False, 3: True, 5: True}, map={2: True, 5: True}))
    assert d == dict(tier='realistic', k_sel=3, mode='full', l2_runs=True)
    d = st.l1_decision(dict(full={1: False, 2: False, 3: False, 5: True}, map={2: False, 5: False}))
    assert d == dict(tier='stress', k_sel=5, mode='full', l2_runs=True)
    d = st.l1_decision(dict(full={1: False, 2: False, 3: False, 5: False}, map={2: True, 5: True}))
    assert d == dict(tier='realistic', k_sel=2, mode='map', l2_runs=True), 'only map-only passes -> train map-only'
    d = st.l1_decision(dict(full={1: False, 2: False, 3: False, 5: False}, map={2: False, 5: True}))
    assert d == dict(tier='stress', k_sel=5, mode='map', l2_runs=True)
    d = st.l1_decision(dict(full={1: False, 2: False, 3: False, 5: False}, map={2: False, 5: False}))
    assert d == dict(tier='none', k_sel=None, mode=None, l2_runs=False)


def test_headroom_rule():
    assert st.headroom_passes(0.10, [0.01, 0.2]) and not st.headroom_passes(0.09, [0.01, 0.2]) and not st.headroom_passes(0.2, [0.0, 0.3])


def test_flags_missing_episode_raises_and_exception_counts_as_failure():
    rows = {1: dict(seed=1, success=True), 2: dict(seed=2, success=False, exception='x')}
    assert list(st.flags(rows, [1, 2])) == [1.0, 0.0]
    with pytest.raises(KeyError):
        st.flags(rows, [1, 3])


def test_replay_compact_maps_samples_bit_identical_to_float32_storage():
    from replay_memory import ReplayMemory
    rng = np.random.default_rng(0)
    plain, compact = ReplayMemory(50, 7), ReplayMemory(50, 7, compact_maps=True)
    for i in range(80):  # also wraps around the capacity
        m = (rng.random((120, 120, 1)) < 0.05).astype(np.float32)
        n = (rng.random((120, 120, 1)) < 0.05).astype(np.float32)
        item = (m, rng.normal(size=41).astype(np.float32), rng.normal(size=3), float(i), n, rng.normal(size=41).astype(np.float32), 1.0)
        plain.push(*item); compact.push(*item)
    assert compact.buffer[0][0].dtype == np.bool_ and plain.buffer[0][0].dtype == np.float32
    for _ in range(5):
        for x, y in zip(plain.sample(16), compact.sample(16)):
            assert x.dtype == y.dtype and np.array_equal(x, y)


def test_replay_compact_rejects_non_binary_map():
    from replay_memory import ReplayMemory
    mem = ReplayMemory(4, 0, compact_maps=True)
    bad = np.full((2, 2, 1), 0.5, dtype=np.float32)
    with pytest.raises(ValueError):
        mem.push(bad, np.zeros(1), np.zeros(1), 0., bad, np.zeros(1), 1.)
