"""STAGE0-028 R0-3 analysis: paired SR-drop test of each mismatch config against nominal, plus
the diagnostic bundle registered in DECISIONS D45 (chassis-tracking proxy, reference-progress
proxy, failure-reason distribution). Judgement criteria are exactly D45's pre-registration; this
script does not choose or tune them.
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path('/root/mm_husky_ws/results/stage0-028-r03')
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
    nominal_sr = float(nominal_success.mean())

    report = dict(nominal_sr=nominal_sr, episodes=len(seeds), configs={})
    any_pass = []
    for (gain, delay), rows in sorted(configs.items()):
        success = np.array([rows[s]['success'] for s in seeds], dtype=np.float64)
        sr = float(success.mean())
        diff = success - nominal_success  # config - nominal, paired by seed
        ci = bootstrap_ci(diff)
        sr_drop = nominal_sr - sr
        passes = (gain, delay) != NOMINAL and sr_drop >= 0.15 and ci[1] < 0
        any_pass.append(passes)
        ik = np.array([rows[s].get('ik_count', 0) for s in seeds], dtype=np.float64)
        coll = np.array([rows[s].get('collision_count', 0) for s in seeds], dtype=np.float64)
        traj_len = np.array([rows[s].get('trajectory_length_m', 0.) for s in seeds], dtype=np.float64)
        subtasks = np.array([rows[s].get('subtasks_completed', 0) for s in seeds], dtype=np.float64)
        cmd_exec_diff = [rows[s].get('mismatch_cmd_exec_mean_abs_diff') for s in seeds if 'mismatch_cmd_exec_mean_abs_diff' in rows[s]]
        failure_dist = {}
        for s in seeds:
            reason = rows[s].get('primary_reason', 'unknown')
            failure_dist[reason] = failure_dist.get(reason, 0) + 1
        report['configs']['gain%s_delay%d' % (gain, delay)] = dict(
            gain=gain, delay=delay, sr=sr, sr_drop_vs_nominal=sr_drop,
            paired_diff_mean=float(diff.mean()), paired_diff_ci95=ci,
            passes_d45_criterion=bool(passes),
            mean_ik_count=float(ik.mean()), mean_collision_count=float(coll.mean()),
            mean_trajectory_length_m=float(traj_len.mean()), mean_subtasks_completed=float(subtasks.mean()),
            mean_mismatch_cmd_exec_diff=(float(np.mean(cmd_exec_diff)) if cmd_exec_diff else None),
            failure_distribution=failure_dist)
    report['g0_r03_pass'] = bool(any(any_pass))
    report['seeds'] = seeds
    out = ROOT / 'r03-analysis.json'
    out.write_text(json.dumps(report, indent=2))
    print('nominal SR:', nominal_sr)
    for name, c in sorted(report['configs'].items()):
        print('%-16s SR=%.3f drop=%.3f CI=%s pass=%s failures=%s' % (
            name, c['sr'], c['sr_drop_vs_nominal'], c['paired_diff_ci95'], c['passes_d45_criterion'], c['failure_distribution']))
    print('G0 R0-3 pass (>=1 config meets D45 criterion):', report['g0_r03_pass'])


if __name__ == '__main__':
    main()
