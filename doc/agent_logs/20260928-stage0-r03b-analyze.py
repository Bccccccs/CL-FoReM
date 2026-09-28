"""STAGE0-028 R0-3b (exploratory, D47): paired SR/perfect-success comparison of 5 stronger
mismatch configs against the R0-3 nominal run's matching 20-seed subset (10000-10019).
Exploratory only - does not alter or substitute the D45 R0-3 judgement.
"""
import json
from pathlib import Path

import numpy as np

R03 = Path('/root/mm_husky_ws/results/stage0-028-r03')
R03B = Path('/root/mm_husky_ws/results/stage0-028-r03b')


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


def main():
    nominal_rows = load_rows(R03 / 'gain1.0_delay0')
    seeds = list(range(10000, 10020))
    nominal_success = np.array([nominal_rows[s]['success'] for s in seeds], dtype=np.float64)
    nominal_perfect = np.array([nominal_rows[s]['perfect_success'] for s in seeds], dtype=np.float64)
    nominal_sr, nominal_perfect_rate = float(nominal_success.mean()), float(nominal_perfect.mean())

    report = dict(nominal_sr_20seed=nominal_sr, nominal_perfect_20seed=nominal_perfect_rate, configs={})
    print('nominal (20-seed subset) SR=%.3f perfect=%.3f' % (nominal_sr, nominal_perfect_rate))
    for d in sorted(R03B.iterdir()):
        if not d.is_dir() or not (d / 'episodes.jsonl').exists():
            continue
        rows = load_rows(d)
        assert sorted(rows.keys()) == seeds, (d.name, 'seed mismatch')
        success = np.array([rows[s]['success'] for s in seeds], dtype=np.float64)
        perfect = np.array([rows[s]['perfect_success'] for s in seeds], dtype=np.float64)
        ik_fail_ep = np.array([rows[s].get('ik_count', 0) > 0 for s in seeds], dtype=np.float64)
        coll_ep = np.array([rows[s].get('collision_count', 0) > 0 for s in seeds], dtype=np.float64)
        cmd_exec = [rows[s].get('mismatch_cmd_exec_mean_abs_diff') for s in seeds if 'mismatch_cmd_exec_mean_abs_diff' in rows[s]]
        sr, perfect_rate = float(success.mean()), float(perfect.mean())
        diff, perfect_diff = success - nominal_success, perfect - nominal_perfect
        ci, perfect_ci = bootstrap_ci(diff), bootstrap_ci(perfect_diff)
        failure_dist = {}
        for s in seeds:
            reason = rows[s].get('primary_reason', 'unknown')
            failure_dist[reason] = failure_dist.get(reason, 0) + 1
        row = dict(sr=sr, sr_drop=nominal_sr - sr, sr_ci95=ci,
                   perfect_rate=perfect_rate, perfect_drop=nominal_perfect_rate - perfect_rate, perfect_ci95=perfect_ci,
                   ik_fail_episode_fraction=float(ik_fail_ep.mean()), collision_episode_fraction=float(coll_ep.mean()),
                   mean_mismatch_cmd_exec_diff=(float(np.mean(cmd_exec)) if cmd_exec else None),
                   failure_distribution=failure_dist)
        report['configs'][d.name] = row
        print('%-18s SR=%.3f(drop%.3f,CI%s) perfect=%.3f(drop%.3f,CI%s) ik_fail_ep=%.2f coll_ep=%.2f cmd_exec_diff=%s failures=%s' % (
            d.name, sr, row['sr_drop'], ci, perfect_rate, row['perfect_drop'], perfect_ci,
            row['ik_fail_episode_fraction'], row['collision_episode_fraction'], row['mean_mismatch_cmd_exec_diff'], failure_dist))
    (R03B / 'r03b-analysis.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
