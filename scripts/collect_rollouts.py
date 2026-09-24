"""P1-A1 trajectory collection via the fixed P0 rollout entry (p0_runner eval --save-observations).

Seeds come only from the training range 0-9999 and are split by whole episode into train/val/test.
Shards run in parallel; with the fixed BioIK budget (p0-ik-budget-v1) results do not depend on CPU load.
Writes <output>/dataset.json listing every planned episode (failures included, never silently dropped).
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wm.data import DataError, file_sha256, load_episode  # noqa: E402


def seed_range(text):
    lo, hi = (int(x) for x in text.split(':'))
    if not 0 <= lo < hi <= 10000:
        raise argparse.ArgumentTypeError('ranges are lo:hi within the training range 0:10000')
    return list(range(lo, hi))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--checkpoint', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--train', type=seed_range, required=True)
    p.add_argument('--val', type=seed_range, required=True)
    p.add_argument('--test', type=seed_range, required=True)
    p.add_argument('--shards', type=int, default=8)
    p.add_argument('--task', default='simpleobstacle')
    p.add_argument('--policy-mode', choices=['deterministic', 'stochastic'], default='stochastic')
    p.add_argument('--ik-iterations', type=int, default=100)
    p.add_argument('--max-episode-steps', type=int, default=2000)
    p.add_argument('--device', default='cuda')
    a = p.parse_args()
    splits = dict(train=a.train, val=a.val, test=a.test)
    all_seeds = [s for v in splits.values() for s in v]
    if len(set(all_seeds)) != len(all_seeds):
        raise SystemExit('train/val/test seed ranges overlap')
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=False)
    runner = Path(__file__).resolve().parent / 'p0_runner.py'
    jobs = []
    for split, seeds in splits.items():
        for k in range(a.shards):
            part = seeds[k::a.shards]
            if not part:
                continue
            name = '%s-%02d' % (split, k)
            (out / (name + '-seeds.json')).write_text(json.dumps(part))
            cmd = [sys.executable, '-u', str(runner), 'eval', '--checkpoint', a.checkpoint,
                   '--seeds', str(out / (name + '-seeds.json')), '--episodes', str(len(part)),
                   '--output', str(out / name), '--task', a.task, '--device', a.device,
                   '--max-episode-steps', str(a.max_episode_steps), '--ik-mode', 'fixed',
                   '--ik-iterations', str(a.ik_iterations), '--policy-mode', a.policy_mode, '--save-observations']
            jobs.append((split, name, part, cmd))
    started = time.time()
    procs = []
    for split, name, part, cmd in jobs:
        log = (out / (name + '.log')).open('w')
        procs.append((split, name, part, subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT), log))
    episodes, failures = [], []
    for split, name, part, proc, log in procs:
        code = proc.wait()
        log.close()
        rows = {}
        rows_file = out / name / 'episodes.jsonl'
        if rows_file.exists():
            rows = {r['seed']: r for r in map(json.loads, rows_file.read_text().splitlines())}
        if code:
            failures.append(dict(shard=name, returncode=code))
        for seed in part:
            rel = '%s/episode-%05d-observations.npz' % (name, seed)
            rec = dict(split=split, seed=seed, path=rel, shard=name, usable=False,
                       primary_reason=rows.get(seed, {}).get('primary_reason'),
                       exception=rows.get(seed, {}).get('exception', 'missing episode record'))
            if (out / rel).exists():
                try:
                    ep = load_episode(out / rel, seed)
                    rec.update(sha256=file_sha256(out / rel), steps=int(ep['action'].shape[0]),
                               valid_transitions=int(ep['n_valid']), complete=bool(ep['complete']),
                               terminated=bool(ep['terminated']), truncated=bool(ep['truncated']),
                               usable=ep['n_valid'] > 0)
                except DataError as exc:
                    rec['validation_error'] = str(exc)
            episodes.append(rec)
    manifest = dict(task_id=os.environ.get('P0_TASK_ID', 'P1-A1'), created=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                    arguments=vars(a), seconds=time.time() - started, shard_failures=failures,
                    ik_semantics='p0-ik-budget-v1', checkpoint_sha256=file_sha256(a.checkpoint),
                    counts={s: dict(planned=len(v), usable=sum(e['usable'] for e in episodes if e['split'] == s),
                                    transitions=sum(e.get('valid_transitions', 0) for e in episodes if e['split'] == s))
                            for s, v in splits.items()},
                    bytes=sum((out / e['path']).stat().st_size for e in episodes if (out / e['path']).exists()),
                    episodes=episodes)
    (out / 'dataset.json').write_text(json.dumps(manifest, indent=1))
    print(json.dumps({k: manifest[k] for k in ['counts', 'bytes', 'seconds', 'shard_failures']}, indent=1))
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
