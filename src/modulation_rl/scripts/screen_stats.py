"""SCREEN-028 statistics: point estimates first, vectorized bootstrap CIs second.

FOLLOWUP-028's statistics stage timed out because the bootstrap was a Python loop. Everything here
is a numpy gather over an index tensor (10000 resamples x 100-200 episodes is ~1e6-2e6 elements,
well under a second). Callers write the point estimates to disk *before* calling any *_ci function,
so a timeout can never lose them.

Conventions (D53/D54): success = primary_reason == 'success' (an episode with an exception counts as
a failure); paired by evaluation seed (and by training seed where several exist); "CI" is the
percentile 95% interval of the bootstrap distribution; the L2/D2 comparisons pool the two training
seeds and resample episodes *within* each training seed (stratified), the same indices for both arms.
"""
import json
from pathlib import Path

import numpy as np

N_BOOT = 10000
CHUNK = 500


def load_rows(path):
    rows = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            rows[int(row['seed'])] = row
    return rows


def flags(rows, seeds, key='success'):
    """0/1 array over `seeds`; a missing episode raises (silent gaps would break pairing)."""
    missing = [s for s in seeds if s not in rows]
    if missing:
        raise KeyError('missing episodes for seeds %s...' % missing[:5])
    return np.array([bool(rows[s].get(key, False)) for s in seeds], dtype=np.float64)


def episode_flags(rows, seeds):
    """Per-episode diagnostics used in the report tables."""
    out = dict(success=flags(rows, seeds), perfect=flags(rows, seeds, 'perfect_success'))
    out['collision'] = np.array([rows[s].get('collision_count', 0) > 0 for s in seeds], dtype=np.float64)
    out['ik'] = np.array([rows[s].get('ik_count', 0) > 0 for s in seeds], dtype=np.float64)
    out['exception'] = np.array([rows[s].get('exception') is not None for s in seeds], dtype=np.float64)
    return out


def point_diff(a, b):
    """Point estimate of mean(a) - mean(b) for arrays shaped (N,) or (S,N)."""
    return float(np.mean(a) - np.mean(b))


def _resample_indices(rng, strata, n, count):
    return rng.integers(0, n, size=(count, strata, n))


def bootstrap_diffs(a, b, n_boot=N_BOOT, seed=0):
    """Bootstrap distribution of mean(a)-mean(b). a, b: (N,) or (S,N) paired arrays. Episodes are
    resampled independently within each stratum (row), identical indices for a and b."""
    a = np.atleast_2d(np.asarray(a, dtype=np.float64))
    b = np.atleast_2d(np.asarray(b, dtype=np.float64))
    if a.shape != b.shape:
        raise ValueError('paired arrays must have the same shape, got %s vs %s' % (a.shape, b.shape))
    strata, n = a.shape
    delta = a - b
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot, dtype=np.float64)
    rows = np.arange(strata)[None, :, None]
    for start in range(0, n_boot, CHUNK):
        count = min(CHUNK, n_boot - start)
        idx = _resample_indices(rng, strata, n, count)
        out[start:start + count] = delta[rows, idx].mean(axis=(1, 2))
    return out


def ci95(samples):
    return [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))]


def diff_with_ci(a, b, n_boot=N_BOOT, seed=0):
    samples = bootstrap_diffs(a, b, n_boot, seed)
    return dict(point=point_diff(a, b), ci95=ci95(samples), n_boot=n_boot)


def recovery_ratio(nominal, stale, comp, n_boot=N_BOOT, seed=0):
    """(SR_comp - SR_stale) / (SR_nominal - SR_stale): point estimate plus paired bootstrap of the
    ratio (resamples where the denominator is <= 0 are dropped and counted)."""
    nominal, stale, comp = (np.asarray(x, dtype=np.float64).reshape(1, -1) for x in (nominal, stale, comp))
    denom = float(nominal.mean() - stale.mean())
    point = float((comp.mean() - stale.mean()) / denom) if denom > 0 else None
    rng = np.random.default_rng(seed)
    n = nominal.shape[1]
    ratios = []
    for start in range(0, n_boot, CHUNK):
        count = min(CHUNK, n_boot - start)
        idx = rng.integers(0, n, size=(count, n))
        d = nominal[0][idx].mean(1) - stale[0][idx].mean(1)
        num = comp[0][idx].mean(1) - stale[0][idx].mean(1)
        keep = d > 0
        ratios.append(num[keep] / d[keep])
    ratios = np.concatenate(ratios)
    return dict(point=point, denominator=denom, ci95=ci95(ratios) if len(ratios) else None,
                n_valid_resamples=int(len(ratios)), n_boot=n_boot)


# ---------------------------------------------------------------------------
# Pre-registered decision rules (D53, D54). Pure functions of already computed numbers.
# ---------------------------------------------------------------------------

L1_DROP = 0.15
HEADROOM = 0.10


def l1_config_passes(delta_point, delta_ci):
    """D53-L1: SR drop vs nominal >= 0.15 and the paired CI upper bound < 0 (delta = config - nominal)."""
    return bool(delta_point <= -L1_DROP and delta_ci[1] < 0)


def l1_decision(passes):
    """passes: {'full': {k: bool}, 'map': {k: bool}}. Returns tier and the pre-registered k_sel rule."""
    full = sorted(k for k, ok in passes.get('full', {}).items() if ok)
    only_map = sorted(k for k, ok in passes.get('map', {}).items() if ok)
    passed = [('full', k) for k in full] + [('map', k) for k in only_map]
    if not passed:
        return dict(tier='none', k_sel=None, mode=None, l2_runs=False)
    tier = 'realistic' if any(k <= 3 for _, k in passed) else 'stress'
    if full:
        return dict(tier=tier, k_sel=full[0], mode='full', l2_runs=True)
    return dict(tier=tier, k_sel=only_map[0], mode='map', l2_runs=True)


def headroom_passes(point, ci, minimum=HEADROOM):
    return bool(point >= minimum and ci[0] > 0)


def lower_bound_positive(ci):
    return bool(ci[0] > 0)
