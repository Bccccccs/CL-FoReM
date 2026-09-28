"""STAGE0-028 R0-3c analysis (D48): same method as r03-analyze.py, applied to the wider
gain{0.6,1.0,1.4,1.6,1.8} x delay{0,5,10} grid, with its own freshly-rerun nominal.
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path('/root/mm_husky_ws/results/stage0-028-r03c')
NOMINAL = (1.0, 0)


def bootstrap_ci(values, seed=0, n=10000):
    values = np.asarray(values, dtype=np.float64)
    if not len(values):
        return [float('nan'), float('nan')]
    rng = np.random.default_rng(seed)
    means = np.empty(n, np.float64)
    batch = max(1, min(128, (1 << 20) // len(values)))
    for start in range(0, n, batch):
        count = min(batch, n - start)
        idx = rng.integers(0, len(values), size=(count, len(values)))
        means[start:start + count] = values[idx].mean(1)
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def load_rows(config_dir):
    rows = {}
    for line in (config_dir / 'episodes.jsonl').read_text().splitlines():
        r = json.loads(line)
        rows[r['seed']] = r
    return rows


def parse_name(name):
    gain_s, delay_s = name.split('_')
    return float(gain_s.replace('gain', '')), int(delay_s.replace('delay', ''))


def main():
    configs = {}
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir() or not (d / 'episodes.jsonl').exists():
            continue
        configs[parse_name(d.name)] = load_rows(d)
    assert NOMINAL in configs, 'nominal (gain=1.0,delay=0) missing'
    seeds = sorted(configs[NOMINAL].keys())
    for key, rows in configs.items():
        assert sorted(rows.keys()) == seeds, ('seed set mismatch', key)
    nominal_rows = configs[NOMINAL]
    nominal_success = np.array([nominal_rows[s]['success'] for s in seeds], dtype=np.float64)
    nominal_perfect = np.array([nominal_rows[s]['perfect_success'] for s in seeds], dtype=np.float64)
    nominal_sr, nominal_perfect_rate = float(nominal_success.mean()), float(nominal_perfect.mean())

    report = dict(nominal_sr=nominal_sr, nominal_perfect_rate=nominal_perfect_rate, episodes=len(seeds), configs={})
    any_pass = []
    for (gain, delay), rows in sorted(configs.items()):
        success = np.array([rows[s]['success'] for s in seeds], dtype=np.float64)
        perfect = np.array([rows[s]['perfect_success'] for s in seeds], dtype=np.float64)
        sr, perfect_rate = float(success.mean()), float(perfect.mean())
        diff = success - nominal_success
        perfect_diff = perfect - nominal_perfect
        ci = bootstrap_ci(diff)
        perfect_ci = bootstrap_ci(perfect_diff)
        sr_drop = nominal_sr - sr
        perfect_drop = nominal_perfect_rate - perfect_rate
        passes = (gain, delay) != NOMINAL and sr_drop >= 0.15 and ci[1] < 0
        any_pass.append(passes)
        ik_fail_ep = np.array([rows[s].get('ik_count', 0) > 0 for s in seeds], dtype=np.float64)
        coll_ep = np.array([rows[s].get('collision_count', 0) > 0 for s in seeds], dtype=np.float64)
        cmd_exec = [rows[s].get('mismatch_cmd_exec_mean_abs_diff') for s in seeds if 'mismatch_cmd_exec_mean_abs_diff' in rows[s]]
        failure_dist = {}
        for s in seeds:
            reason = rows[s].get('primary_reason', 'unknown')
            failure_dist[reason] = failure_dist.get(reason, 0) + 1
        report['configs']['gain%s_delay%d' % (gain, delay)] = dict(
            gain=gain, delay=delay, sr=sr, sr_drop_vs_nominal=sr_drop, paired_diff_ci95=ci,
            passes_d45_criterion=bool(passes),
            perfect_success_rate=perfect_rate, perfect_drop_vs_nominal=perfect_drop, perfect_paired_diff_ci95=perfect_ci,
            perfect_ci_upper_negative=bool(perfect_ci[1] < 0),
            ik_fail_episode_fraction=float(ik_fail_ep.mean()), collision_episode_fraction=float(coll_ep.mean()),
            mean_mismatch_cmd_exec_diff=(float(np.mean(cmd_exec)) if cmd_exec else None),
            failure_distribution=failure_dist)
    report['g0_r03c_pass'] = bool(any(any_pass))
    report['seeds'] = seeds
    out = ROOT / 'r03c-analysis.json'
    out.write_text(json.dumps(report, indent=2))
    print('nominal SR:', nominal_sr, 'nominal perfect:', nominal_perfect_rate)
    for name, c in sorted(report['configs'].items(), key=lambda kv: (kv[1]['gain'], kv[1]['delay'])):
        print('%-16s SR=%.3f drop=%.3f CI=%s pass(D45)=%s | perfect=%.3f drop=%.3f CI=%s sig=%s | ik_ep=%.2f coll_ep=%.2f' % (
            name, c['sr'], c['sr_drop_vs_nominal'], c['paired_diff_ci95'], c['passes_d45_criterion'],
            c['perfect_success_rate'], c['perfect_drop_vs_nominal'], c['perfect_paired_diff_ci95'],
            c['perfect_ci_upper_negative'], c['ik_fail_episode_fraction'], c['collision_episode_fraction']))
    print('G0 R0-3c pass (>=1 config meets D45 criterion, success-based):', report['g0_r03c_pass'])


if __name__ == '__main__':
    main()
