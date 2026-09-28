"""STAGE0-028 R0-3/R0-4: generic sharded p0_runner.py eval launcher.

Same concurrency pattern as collect_rollouts.py (already used for the real P1-A1 training data,
~10k episodes: several p0_runner.py eval subprocesses run concurrently against the same
mmhusky-node01 analytical roslaunch/MoveGroup, each a separate process handling its own seed
shard sequentially via evaluate_isolated's one-fresh-process-per-episode pattern). Unlike
collect_rollouts.py this does not split into train/val/test; the whole seed range is one
condition/config, written straight into <output>/episodes.jsonl + per-episode artifacts, with a
manifest documenting the shard commands and any shard failures. Never silently drops a failed
episode: shard exit codes are recorded, and episodes.jsonl rows carry whatever p0_runner.py wrote
(including an exception row) even on shard failure.
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--checkpoint', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--seeds', required=True, help='lo:hi, half-open, within 0:10000')
    p.add_argument('--shards', type=int, default=8)
    p.add_argument('--task', default='simpleobstacle')
    p.add_argument('--policy-mode', choices=['deterministic', 'stochastic'], default='deterministic')
    p.add_argument('--ik-iterations', type=int, default=100)
    p.add_argument('--max-episode-steps', type=int, default=2000)
    p.add_argument('--device', default='cuda')
    p.add_argument('--save-observations', action='store_true')
    p.add_argument('--base-vel-gain', type=float, default=1.0)
    p.add_argument('--base-vel-gain-range', type=float, nargs=2, default=None, metavar=('LO', 'HI'))
    p.add_argument('--action-delay-steps', type=int, default=0)
    p.add_argument('--save-step-info', action='store_true',
                    help='FOLLOWUP-028 B2: forwarded to p0_runner.py --save-step-info (default off).')
    p.add_argument('--shield-config', default=None,
                    help='FOLLOWUP-028 B3: forwarded to p0_runner.py --shield-config (default off).')
    p.add_argument('--label', default='', help='free-text tag written into manifest.json only')
    a = p.parse_args()
    lo, hi = (int(x) for x in a.seeds.split(':'))
    # Must match p0_runner.py:read_seeds exactly: --save-observations (data collection) is
    # restricted to the training range 0-9999; a plain eval uses the validation/test ranges
    # 10000-10099 (allocated) / 20000-20299 (Stage2), never the 10100-19999 gap.
    if a.save_observations:
        if not 0 <= lo < hi <= 10000:
            raise SystemExit('--save-observations requires seeds within the training range 0:10000')
    else:
        if not ((10000 <= lo < hi <= 10100) or (20000 <= lo < hi <= 20300)):
            raise SystemExit('eval seeds must be within 10000:10100 or 20000:20300 (unallocated 10100:20000 is rejected by read_seeds)')
    seeds = list(range(lo, hi))
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=False)
    runner = Path(__file__).resolve().parents[2] / 'src/modulation_rl/scripts/p0_runner.py'
    assert runner.exists(), runner
    jobs = []
    for k in range(a.shards):
        part = seeds[k::a.shards]
        if not part:
            continue
        name = 'shard-%02d' % k
        (out / (name + '-seeds.json')).write_text(json.dumps(part))
        cmd = [sys.executable, '-u', str(runner), 'eval', '--checkpoint', a.checkpoint,
               '--seeds', str(out / (name + '-seeds.json')), '--episodes', str(len(part)),
               '--output', str(out / name), '--task', a.task, '--device', a.device,
               '--max-episode-steps', str(a.max_episode_steps), '--ik-mode', 'fixed',
               '--ik-iterations', str(a.ik_iterations), '--policy-mode', a.policy_mode,
               '--base-vel-gain', str(a.base_vel_gain), '--action-delay-steps', str(a.action_delay_steps)]
        if a.save_observations:
            cmd.append('--save-observations')
        if a.base_vel_gain_range:
            cmd += ['--base-vel-gain-range', str(a.base_vel_gain_range[0]), str(a.base_vel_gain_range[1])]
        if a.save_step_info:
            cmd.append('--save-step-info')
        if a.shield_config:
            cmd += ['--shield-config', a.shield_config]
        jobs.append((name, part, cmd))
    started = time.time()
    procs = []
    for name, part, cmd in jobs:
        log = (out / (name + '.log')).open('w')
        procs.append((name, part, subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT), log))
    rows, failures = [], []
    for name, part, proc, log in procs:
        code = proc.wait()
        log.close()
        if code:
            failures.append(dict(shard=name, returncode=code))
        shard_rows_file = out / name / 'episodes.jsonl'
        if shard_rows_file.exists():
            rows.extend(json.loads(line) for line in shard_rows_file.read_text().splitlines())
        for artifact in (out / name).glob('episode-*'):
            shutil.copy2(str(artifact), str(out / artifact.name))
    with (out / 'episodes.jsonl').open('w') as f:
        for row in sorted(rows, key=lambda r: r['seed']):
            f.write(json.dumps(row, default=str) + '\n')
    manifest = dict(label=a.label, arguments=vars(a), planned=len(seeds), collected=len(rows),
                    shard_failures=failures, seconds=time.time() - started,
                    checkpoint=a.checkpoint, seeds=[lo, hi])
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(dict(planned=len(seeds), collected=len(rows), shard_failures=failures, seconds=manifest['seconds']), indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
