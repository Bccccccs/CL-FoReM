"""FOLLOWUP-028 B1 (D51-B1): offline avoidability analysis on R0-3/R0-3c's already-collected
episodes.jsonl (30 configs total, seeds 10000-10099, no new data collection).

For every seed that fails with primary_reason=='ik_limit' under the nominal config
(gain=1.0,delay=0), checks how often the SAME seed succeeds under at least one of the 8 "mild
perturbation" configs (gain in {0.8,1.0,1.2} x delay in {0,1,2}, excluding nominal itself) ->
fail_to_success_fraction. As a chaos/variance control, does the mirror check for nominal-success
seeds failing at least once in the same 8 configs -> success_to_fail_fraction. Also reports the
"any of the other 29 configs" version and the tail dist_to_desired trend for nominal ik_limit
failures.

D51-B1 criterion (pre-registered, not re-derived here): fail_to_success_fraction >= 0.30 AND the
bootstrap 95% CI lower bound of (fail_to_success_fraction - success_to_fail_fraction) > 0.
"""
import argparse
import json
from pathlib import Path

import numpy as np

NOMINAL = (1.0, 0)
MILD_GAINS = (0.8, 1.0, 1.2)
MILD_DELAYS = (0, 1, 2)


def parse_name(name):
    gain_s, delay_s = name.split('_')
    return float(gain_s.replace('gain', '')), int(delay_s.replace('delay', ''))


def load_configs(roots):
    """R0-3 and R0-3c each independently ran (gain=0.6/1.0/1.4, delay=0) (D48: R0-3c reruns
    nominal-adjacent points fresh rather than reusing R0-3's, "因为这15组要用同一批同种子完整重
    跑以保证跨组配对一致"), so the 15+15 directories on disk cover 27 distinct (gain,delay) grid
    points, 3 of them run twice. Later roots win on a shared key; every overlap is checked for
    exact per-seed success agreement (both runs are supposed to be a deterministic, identical
    sim) and any mismatch is recorded (not silently resolved) rather than raising, since this is
    a diagnostic, not a D51 judgement criterion."""
    configs, sources, overlap_checks = {}, {}, []
    for root in roots:
        root = Path(root)
        for d in sorted(root.iterdir()):
            if not d.is_dir() or not (d / 'episodes.jsonl').exists():
                continue
            key = parse_name(d.name)
            rows = {}
            for line in (d / 'episodes.jsonl').read_text().splitlines():
                r = json.loads(line)
                rows[r['seed']] = r
            if key in configs:
                prev_rows, prev_source = configs[key], sources[key]
                common = set(prev_rows) & set(rows)
                agree = all(bool(prev_rows[s].get('success')) == bool(rows[s].get('success')) for s in common)
                overlap_checks.append(dict(config='gain%s_delay%d' % key, sources=[prev_source, str(d)],
                                            seeds_compared=len(common), success_agrees=agree))
            configs[key] = rows
            sources[key] = str(d)
    return configs, overlap_checks, sources


def tail_dist_trend(root, seed):
    """Mean dist_to_desired over the last 10 vs the preceding 10 steps of the tail (up to 50
    steps kept), for a nominal ik_limit failure - a coarse 'was it converging or diverging'
    diagnostic, not a judgement criterion."""
    path = Path(root) / ('episode-%05d-tail.json' % seed)
    if not path.exists():
        return None
    tail = json.loads(path.read_text())
    dists = [t['info'].get('dist_to_desired') for t in tail if 'dist_to_desired' in t.get('info', {})]
    dists = [d for d in dists if d is not None]
    if len(dists) < 4:
        return None
    half = len(dists) // 2
    return dict(early_mean=float(np.mean(dists[:half])), late_mean=float(np.mean(dists[half:])),
                n=len(dists))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--roots', required=True, help='comma-separated directories, each holding gainX_delayY subdirs (R0-3 and R0-3c)')
    p.add_argument('--output', required=True)
    a = p.parse_args()
    out = Path(a.output)
    if out.exists():
        raise SystemExit('output exists; B1 is one-shot')
    root_paths = a.roots.split(',')
    configs, overlap_checks, sources = load_configs(root_paths)
    if NOMINAL not in configs:
        raise SystemExit('nominal (gain=1.0,delay=0) missing from --roots')
    nominal_rows = configs[NOMINAL]
    seeds = sorted(nominal_rows.keys())
    for key, rows in configs.items():
        missing = set(seeds) - set(rows.keys())
        if missing:
            raise SystemExit('config %s missing seeds also present in nominal: %s' % (key, sorted(missing)[:5]))

    mild_keys = [(g, d) for g in MILD_GAINS for d in MILD_DELAYS if (g, d) != NOMINAL and (g, d) in configs]
    other_keys = [k for k in configs if k != NOMINAL]

    ik_fail_seeds = [s for s in seeds if nominal_rows[s].get('primary_reason') == 'ik_limit']
    success_seeds = [s for s in seeds if nominal_rows[s].get('success')]

    def flip_fraction(seed_list, keys, want_success):
        per_seed = []
        for s in seed_list:
            flips = [bool(configs[k][s].get('success')) == want_success for k in keys]
            per_seed.append(any(flips))
        return per_seed

    fail_to_success_mild = flip_fraction(ik_fail_seeds, mild_keys, True)
    success_to_fail_mild = flip_fraction(success_seeds, mild_keys, False)
    fail_to_success_any = flip_fraction(ik_fail_seeds, other_keys, True)
    success_to_fail_any = flip_fraction(success_seeds, other_keys, False)

    fail_to_success_fraction = float(np.mean(fail_to_success_mild)) if fail_to_success_mild else float('nan')
    success_to_fail_fraction = float(np.mean(success_to_fail_mild)) if success_to_fail_mild else float('nan')
    # The two populations (nominal ik_limit failures vs. nominal successes) are disjoint seed
    # sets, so this is not a paired comparison; use a two-sample bootstrap of the difference.
    rng = np.random.default_rng(0)
    n_boot = 10000
    a_arr = np.asarray(fail_to_success_mild, dtype=np.float64)
    b_arr = np.asarray(success_to_fail_mild, dtype=np.float64)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        sa = rng.choice(a_arr, size=len(a_arr), replace=True) if len(a_arr) else np.array([np.nan])
        sb = rng.choice(b_arr, size=len(b_arr), replace=True) if len(b_arr) else np.array([np.nan])
        diffs[i] = sa.mean() - sb.mean()
    diff_ci = [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]

    nominal_dir = Path(sources[NOMINAL])
    tails = {int(s): tail_dist_trend(nominal_dir, s) for s in ik_fail_seeds}

    report = dict(
        seeds=seeds, nominal_ik_limit_seeds=ik_fail_seeds, nominal_success_seeds=success_seeds,
        mild_configs=['gain%s_delay%d' % k for k in mild_keys],
        fail_to_success_fraction_mild=fail_to_success_fraction,
        success_to_fail_fraction_mild=success_to_fail_fraction,
        diff_mild=(fail_to_success_fraction - success_to_fail_fraction) if np.isfinite(fail_to_success_fraction) and np.isfinite(success_to_fail_fraction) else None,
        diff_mild_ci95=diff_ci,
        fail_to_success_fraction_any=float(np.mean(fail_to_success_any)) if fail_to_success_any else float('nan'),
        success_to_fail_fraction_any=float(np.mean(success_to_fail_any)) if success_to_fail_any else float('nan'),
        tail_dist_to_desired_trend=tails,
        distinct_configs=len(configs), overlap_checks=overlap_checks,
    )
    report['passes_d51_b1'] = bool(np.isfinite(fail_to_success_fraction) and fail_to_success_fraction >= 0.30 and diff_ci[0] > 0)
    out.mkdir(parents=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(fail_to_success_fraction_mild=fail_to_success_fraction,
                           success_to_fail_fraction_mild=success_to_fail_fraction,
                           diff_mild_ci95=diff_ci, passes_d51_b1=report['passes_d51_b1']), indent=2))


if __name__ == '__main__':
    main()
