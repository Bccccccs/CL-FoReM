"""FOLLOWUP-028: unattended pipeline orchestrator (S0-S6, 20260928-followup-spec.md S5).

Run inside the mmhusky-node01 container (see doc/agent_logs/20260928-followup-launch.sh) with
`python3 -u followup_pipeline.py --output-root /root/mm_husky_ws/results/followup-028`. Resumable:
each stage writes a DONE or FAILED marker in its own subdirectory and is skipped on a re-run if
already DONE. Writes <output-root>/status.json continuously.

Stages:
  S0 preflight  - GPU/mem/disk, analytical sim check, checkpoint SHA, git HEAD/clean, manifest.
  S1 (|| S2,S3) - A-line structured_adaptation.py on the 10 existing R0-4/R0-4b conditions.
  S2 (|| S1,S3) - B1 b1_avoidability.py on the existing R0-3/R0-3c episodes.
  S3 (|| S1,S2) - B2 data collection: 1000 episodes (seeds 1000-1999), deterministic policy,
                  nominal condition, --save-observations --save-step-info. Uses this file's own
                  memory-guarded seed pool (run_seed_pool), not shard-eval.py's static sharding,
                  so the >=60GiB-before-a-batch / pause-under-40GiB rules are enforced for real.
  S4 (needs S3) - b2_train.py: features/labels/classifiers/thresholds/ClassifierPacks.
  S5 (needs S4) - B3: six shield arms (none/random/geo/cur/hist/wm), 100 episodes each, seeds
                  10000-10099, run sequentially (worker cap per arm well under 64).
  S6 (needs all)- aggregate report -> doc/agent_logs/20260928-followup-report.md.

Resource guard (hard constraint, not just documented): before starting a new *stage* that spawns
workers (S3, each S5 arm), requires >=60GiB available; while a pool is running, refuses to start a
*new* worker to replace a finished one while available memory is <40GiB (it waits, polling). Total
concurrent episode-workers across the whole process is capped by --max-workers (default 64).
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
import p0_runner  # noqa: E402 (for episode_command/dump/jsonable - reuses the tested flag-forwarding path)

DEFAULT_ENCODER_CHECKPOINT = '/root/mm_husky_ws/results/p1a-20260923/policy-100k.pt'
DEFAULT_DYNAMICS_CHECKPOINT = '/root/mm_husky_ws/results/p1-retrain-20260928/trainval-1000-r1/action.pt'
A_LINE_CONDITIONS = [
    ('gain0.6_delay0', '/root/mm_husky_ws/results/stage0-028-r04/gain0.6_delay0/dataset.json', 'cond'),
    ('gain0.8_delay0', '/root/mm_husky_ws/results/stage0-028-r04/gain0.8_delay0/dataset.json', 'cond'),
    ('gain1.0_delay0', '/root/mm_husky_ws/results/stage0-028-r04/gain1.0_delay0/dataset.json', 'cond'),
    ('gain1.2_delay0', '/root/mm_husky_ws/results/stage0-028-r04/gain1.2_delay0/dataset.json', 'cond'),
    ('gain1.4_delay0', '/root/mm_husky_ws/results/stage0-028-r04/gain1.4_delay0/dataset.json', 'cond'),
    ('gain1.0_delay1', '/root/mm_husky_ws/results/stage0-028-r04/gain1.0_delay1/dataset.json', 'cond'),
    ('gain1.0_delay2', '/root/mm_husky_ws/results/stage0-028-r04/gain1.0_delay2/dataset.json', 'cond'),
    ('gain1.8_delay0', '/root/mm_husky_ws/results/stage0-028-r04b/gain1.8_delay0/dataset.json', 'cond'),
    ('gain1.0_delay5', '/root/mm_husky_ws/results/stage0-028-r04b/gain1.0_delay5/dataset.json', 'cond'),
    ('gain1.4_delay5', '/root/mm_husky_ws/results/stage0-028-r04b/gain1.4_delay5/dataset.json', 'cond'),
]
B1_ROOTS = ['/root/mm_husky_ws/results/stage0-028-r03', '/root/mm_husky_ws/results/stage0-028-r03c']
B3_ARMS = ['none', 'random', 'geo', 'cur', 'hist', 'wm']


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%S%z')


def parse_seed_spec(spec):
    """'1000:2000' -> range(1000,2000); '1000,1001,1700,1800' -> explicit list (smoke-test use, to
    hit all three D51 splits with a handful of seeds without inventing an unregistered range)."""
    if ':' in spec:
        lo, hi = (int(x) for x in spec.split(':'))
        return list(range(lo, hi))
    return [int(x) for x in spec.split(',')]


def available_memory_gb():
    with open('/proc/meminfo') as f:
        for line in f:
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) / (1024 * 1024)
    raise RuntimeError('MemAvailable not found in /proc/meminfo')


class Status:
    def __init__(self, path):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text()) if self.path.exists() else dict(stages={})

    def update(self, stage, **fields):
        self.data['stages'].setdefault(stage, {}).update(fields)
        self.data['updated'] = now()
        self.data['available_memory_gb'] = round(available_memory_gb(), 1)
        self.path.write_text(json.dumps(self.data, indent=2))


def stage_done(stage_dir):
    return (Path(stage_dir) / 'DONE').exists()


def mark_done(stage_dir, **info):
    Path(stage_dir).mkdir(parents=True, exist_ok=True)
    (Path(stage_dir) / 'DONE').write_text(json.dumps(dict(finished=now(), **info), indent=2))


def mark_failed(stage_dir, error):
    Path(stage_dir).mkdir(parents=True, exist_ok=True)
    (Path(stage_dir) / 'FAILED').write_text(json.dumps(dict(finished=now(), error=str(error)), indent=2))


# ---------------------------------------------------------------------------
# S0 preflight
# ---------------------------------------------------------------------------

def s0_preflight(root, status, encoder_checkpoint, dynamics_checkpoint):
    stage_dir = root / 's0-preflight'
    if stage_done(stage_dir):
        status.update('S0', state='done (resumed)'); return
    status.update('S0', state='running', started=now())
    stage_dir.mkdir(parents=True, exist_ok=True)
    manifest = dict(checked=now())
    manifest['available_memory_gb'] = available_memory_gb()
    manifest['disk_free_gb'] = _disk_free_gb(root)
    manifest['gpu'] = _gpu_status()
    manifest['analytical_running'] = _ensure_analytical_running()
    manifest['encoder_checkpoint_sha256'] = p0_runner.sha(encoder_checkpoint)
    manifest['dynamics_checkpoint_sha256'] = p0_runner.sha(dynamics_checkpoint)
    manifest['git'] = _git_status()
    (stage_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    if manifest['available_memory_gb'] < 60:
        raise SystemExit('S0 preflight: available memory %.1fGiB < 60GiB floor' % manifest['available_memory_gb'])
    if not manifest['analytical_running']:
        raise SystemExit('S0 preflight: analytical simulator is not running and could not be started')
    mark_done(stage_dir, **manifest)
    status.update('S0', state='done', finished=now())


def _disk_free_gb(path):
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize / (1024 ** 3)


def _gpu_status():
    try:
        out = subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used,memory.total',
                                        '--format=csv,noheader'], text=True)
        return out.strip().splitlines()
    except Exception as exc:
        return ['unavailable: %s' % exc]


def _ensure_analytical_running():
    try:
        out = subprocess.check_output(['pgrep', '-af', 'n2m2_husky_analytical'], text=True)
        if out.strip():
            return True
    except subprocess.CalledProcessError:
        pass
    return False  # deliberately does not auto-start a new roslaunch inside a shared container


def _git_status():
    root = SCRIPTS_DIR.resolve().parents[2]
    try:
        head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(root), 'status', '--short'], text=True)
        branch = subprocess.check_output(['git', '-C', str(root), 'branch', '--show-current'], text=True).strip()
        return dict(head=head, branch=branch, dirty=bool(dirty.strip()), status=dirty)
    except Exception as exc:
        return dict(error=str(exc))


# ---------------------------------------------------------------------------
# S1: A-line
# ---------------------------------------------------------------------------

def s1_a_line(root, status, encoder_checkpoint, dynamics_checkpoint, device, condition_names=None):
    stage_dir = root / 's1-a-structured'
    if stage_done(stage_dir):
        status.update('S1', state='done (resumed)'); return
    status.update('S1', state='running', started=now())
    out = stage_dir / 'probe'
    if not out.exists():
        selected = [c for c in A_LINE_CONDITIONS if condition_names is None or c[0] in condition_names]
        conditions = ','.join('%s:%s:%s' % c for c in selected)
        cmd = [sys.executable, '-u', str(SCRIPTS_DIR / 'structured_adaptation.py'),
               '--conditions', conditions, '--nominal', 'gain1.0_delay0',
               '--model', dynamics_checkpoint, '--encoder-checkpoint', encoder_checkpoint,
               '--cache-dir', str(stage_dir / 'feature-cache'), '--output', str(out), '--device', device]
        _run_logged(cmd, stage_dir / 'run.log', timeout=2 * 3600)
    mark_done(stage_dir)
    status.update('S1', state='done', finished=now())


# ---------------------------------------------------------------------------
# S2: B1
# ---------------------------------------------------------------------------

def s2_b1(root, status):
    stage_dir = root / 's2-b1-avoidability'
    if stage_done(stage_dir):
        status.update('S2', state='done (resumed)'); return
    status.update('S2', state='running', started=now())
    out = stage_dir / 'analysis'
    if not out.exists():
        cmd = [sys.executable, '-u', str(SCRIPTS_DIR / 'b1_avoidability.py'),
               '--roots', ','.join(B1_ROOTS), '--output', str(out)]
        _run_logged(cmd, stage_dir / 'run.log', timeout=2 * 3600)
    mark_done(stage_dir)
    status.update('S2', state='done', finished=now())


def _run_logged(cmd, log_path, timeout):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('w') as log:
        result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError('command failed (%s): %s' % (result.returncode, ' '.join(cmd)))


# ---------------------------------------------------------------------------
# Memory-guarded seed pool (used by S3 collection and each S5 arm)
# ---------------------------------------------------------------------------

def run_seed_pool(base_args, seeds, output_dir, max_workers, min_free_start_gb, min_free_pause_gb,
                   status, status_key, poll_s=2.0, stage_timeout_s=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if available_memory_gb() < min_free_start_gb:
        raise RuntimeError('%s: available memory below %.0fGiB floor before starting a new batch' % (status_key, min_free_start_gb))
    queue = list(seeds)
    running = {}  # seed -> (Popen, log_file, worker_dir)
    rows = []
    started_at = time.monotonic()
    while queue or running:
        if stage_timeout_s and time.monotonic() - started_at > stage_timeout_s:
            for seed, (proc, log, _) in running.items():
                proc.kill(); log.close()
            raise TimeoutError('%s: exceeded stage timeout %ss with %d seeds still incomplete' % (status_key, stage_timeout_s, len(queue) + len(running)))
        while queue and len(running) < max_workers and available_memory_gb() >= min_free_pause_gb:
            seed = queue.pop(0)
            command = p0_runner.episode_command(base_args, output_dir, seed)
            worker_dir = output_dir / ('worker-%05d' % seed)
            log = (output_dir / ('worker-%05d.log' % seed)).open('w')
            proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            running[seed] = (proc, log, worker_dir)
        finished = [s for s, (proc, _, _) in running.items() if proc.poll() is not None]
        for seed in finished:
            proc, log, worker_dir = running.pop(seed)
            log.close()
            rows.append(_collect_worker_result(seed, proc.returncode, worker_dir, output_dir))
        status.update(status_key, running=len(running), queued=len(queue), completed=len(rows),
                       available_memory_gb=round(available_memory_gb(), 1))
        if queue or running:
            time.sleep(poll_s)
    with (output_dir / 'episodes.jsonl').open('w') as f:
        for row in sorted(rows, key=lambda r: r['seed']):
            f.write(json.dumps(row, default=str) + '\n')
    return rows


def _collect_worker_result(seed, returncode, worker_dir, output_dir):
    import shutil
    episode_file = worker_dir / 'episodes.jsonl'
    if episode_file.exists():
        row = json.loads(episode_file.read_text().strip())
        if returncode and row.get('exception') is None:
            row.update(exception='Worker exit %s' % returncode, success=False, perfect_success=False,
                       primary_reason='exception', reasons=['exception'])
    else:
        row = dict(seed=seed, exception='Worker exit %s before episode record; see worker log' % returncode,
                   success=False, perfect_success=False, primary_reason='exception', reasons=['exception'],
                   trajectory_length_m=0., steps=0, terminated=False, truncated=False)
    for artifact in worker_dir.glob('episode-*'):
        shutil.copy2(str(artifact), str(output_dir / artifact.name))
    return row


def _b2_collect_args(encoder_checkpoint):
    return SimpleNamespace(checkpoint=encoder_checkpoint, task='simpleobstacle', world_type='sim',
                            device='cuda', seed=11, max_episode_steps=2000, ik_mode='fixed', ik_iterations=100,
                            policy_mode='deterministic', save_observations=True, base_vel_gain=1.0,
                            base_vel_gain_range=None, action_delay_steps=0, save_step_info=True, shield_config=None)


# ---------------------------------------------------------------------------
# S3: B2 data collection
# ---------------------------------------------------------------------------

def s3_b2_collect(root, status, encoder_checkpoint, max_workers, seeds=None):
    stage_dir = root / 's3-b2-collect'
    if stage_done(stage_dir):
        status.update('S3', state='done (resumed)'); return
    status.update('S3', state='running', started=now())
    seeds = list(seeds) if seeds is not None else list(range(1000, 2000))
    args = _b2_collect_args(encoder_checkpoint)
    rows = run_seed_pool(args, seeds, stage_dir / 'episodes', max_workers,
                          min_free_start_gb=60, min_free_pause_gb=40, status=status, status_key='S3',
                          stage_timeout_s=3 * 3600)
    failures = sum(1 for r in rows if r.get('exception'))
    mark_done(stage_dir, episodes=len(rows), failures=failures)
    status.update('S3', state='done', finished=now(), failures=failures)


# ---------------------------------------------------------------------------
# S4: B2 features/classifiers
# ---------------------------------------------------------------------------

def s4_b2_train(root, status, encoder_checkpoint, dynamics_checkpoint, device, split_ranges=None,
                 data_efficiency_episodes=None):
    stage_dir = root / 's4-b2-foresight'
    if stage_done(stage_dir):
        status.update('S4', state='done (resumed)'); return
    status.update('S4', state='running', started=now())
    out = stage_dir / 'train'
    if not out.exists():
        cmd = [sys.executable, '-u', str(SCRIPTS_DIR / 'b2_train.py'),
               '--data-dir', str(root / 's3-b2-collect' / 'episodes'),
               '--encoder-checkpoint', encoder_checkpoint, '--dynamics-checkpoint', dynamics_checkpoint,
               '--output', str(out), '--device', device]
        if split_ranges:
            cmd += ['--split-ranges', json.dumps(split_ranges)]
        if data_efficiency_episodes:
            cmd += ['--data-efficiency-episodes', ','.join(str(x) for x in data_efficiency_episodes)]
        _run_logged(cmd, stage_dir / 'run.log', timeout=2 * 3600)
    mark_done(stage_dir)
    status.update('S4', state='done', finished=now())


# ---------------------------------------------------------------------------
# S5: B3 shield arms
# ---------------------------------------------------------------------------

def s5_b3(root, status, encoder_checkpoint, dynamics_checkpoint, max_workers, seeds=None):
    stage_dir = root / 's5-b3-shield'
    if stage_done(stage_dir):
        status.update('S5', state='done (resumed)'); return
    status.update('S5', state='running', started=now())
    b2_report = json.loads((root / 's4-b2-foresight' / 'train' / 'report.json').read_text())
    classifier_dir = root / 's4-b2-foresight' / 'train' / 'classifiers'
    random_probability = b2_report['random_probability']
    thresholds = b2_report['thresholds']
    key_of = dict(geo='geo', cur='cur', hist='hist', wm='wm')
    cname_of = dict(geo='C-geo', cur='C-cur', hist='C-hist', wm='C-wm')
    seeds = list(seeds) if seeds is not None else list(range(10000, 10100))
    for arm in B3_ARMS:
        arm_dir = stage_dir / arm
        if stage_done(arm_dir):
            continue
        status.update('S5', current_arm=arm)
        config = dict(arm=arm, device='cpu', history_k=5)
        if arm == 'random':
            config['random_probability'] = random_probability
        elif arm != 'none':
            config['threshold'] = thresholds[cname_of[arm]]['threshold']
            config['classifier_dir'] = str(classifier_dir / key_of[arm])
            if arm in ('cur', 'hist', 'wm'):
                config['encoder_checkpoint'] = encoder_checkpoint
            if arm == 'wm':
                config['dynamics_checkpoint'] = dynamics_checkpoint
        config_path = arm_dir / 'shield-config.json'
        arm_dir.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2))
        args = SimpleNamespace(checkpoint=encoder_checkpoint, task='simpleobstacle', world_type='sim',
                                device='cuda', seed=11, max_episode_steps=2000, ik_mode='fixed', ik_iterations=100,
                                policy_mode='deterministic', save_observations=False, base_vel_gain=1.0,
                                base_vel_gain_range=None, action_delay_steps=0, save_step_info=True,
                                shield_config=str(config_path))
        rows = run_seed_pool(args, seeds, arm_dir / 'episodes', min(max_workers, 32),
                              min_free_start_gb=60, min_free_pause_gb=40, status=status, status_key='S5-%s' % arm,
                              stage_timeout_s=3600)
        failures = sum(1 for r in rows if r.get('exception'))
        mark_done(arm_dir, episodes=len(rows), failures=failures)
    mark_done(stage_dir)
    status.update('S5', state='done', finished=now())


# ---------------------------------------------------------------------------
# S6: report
# ---------------------------------------------------------------------------

def s6_report(root, status, report_path):
    status.update('S6', state='running', started=now())
    from followup_report import build_report  # local import: keeps report-formatting separate/testable
    text = build_report(root)
    Path(report_path).write_text(text)
    mark_done(root / 's6-report')
    status.update('S6', state='done', finished=now())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output-root', default='/root/mm_husky_ws/results/followup-028')
    p.add_argument('--encoder-checkpoint', default=DEFAULT_ENCODER_CHECKPOINT)
    p.add_argument('--dynamics-checkpoint', default=DEFAULT_DYNAMICS_CHECKPOINT)
    p.add_argument('--device', default='cuda')
    p.add_argument('--max-workers', type=int, default=64)
    p.add_argument('--report-path', default='/root/mm_husky_ws/doc/agent_logs/20260928-followup-report.md')
    p.add_argument('--only', default=None, help='comma-separated subset of stages to run (S0,S1,...,S6), for smoke tests')
    p.add_argument('--b2-seeds', default='1000:2000', help='LO:HI or explicit comma-list (must stay within the D51 1000-1999 registration); smoke-test override only')
    p.add_argument('--b2-split-ranges', default=None, help='JSON split ranges passthrough to b2_train.py; smoke-test override only')
    p.add_argument('--b2-data-efficiency-episodes', default=None, help='comma-separated counts passthrough to b2_train.py; smoke-test override only')
    p.add_argument('--b3-seeds', default='10000:10100', help='LO:HI or explicit comma-list (must stay within the D51 10000-10099 registration); smoke-test override only')
    p.add_argument('--a-line-conditions', default=None, help='comma-separated subset of A-line condition names (must include gain1.0_delay0); smoke-test override only')
    a = p.parse_args()
    a_line_conditions = set(a.a_line_conditions.split(',')) if a.a_line_conditions else None
    b2_seeds = parse_seed_spec(a.b2_seeds)
    b3_seeds = parse_seed_spec(a.b3_seeds)
    if min(b2_seeds) < 1000 or max(b2_seeds) >= 2000:
        raise SystemExit('B2 seeds must stay within the D51 registration 1000-1999')
    if min(b3_seeds) < 10000 or max(b3_seeds) >= 10100:
        raise SystemExit('B3 seeds must stay within the D51 registration 10000-10099')
    b2_split_ranges = json.loads(a.b2_split_ranges) if a.b2_split_ranges else None
    b2_data_efficiency_episodes = [int(x) for x in a.b2_data_efficiency_episodes.split(',')] if a.b2_data_efficiency_episodes else None
    root = Path(a.output_root)
    root.mkdir(parents=True, exist_ok=True)
    status = Status(root / 'status.json')
    wanted = set(a.only.split(',')) if a.only else None

    stage_fns = {
        'S0': lambda: s0_preflight(root, status, a.encoder_checkpoint, a.dynamics_checkpoint),
        'S1': lambda: s1_a_line(root, status, a.encoder_checkpoint, a.dynamics_checkpoint, a.device, a_line_conditions),
        'S2': lambda: s2_b1(root, status),
        'S3': lambda: s3_b2_collect(root, status, a.encoder_checkpoint, a.max_workers, b2_seeds),
        'S4': lambda: s4_b2_train(root, status, a.encoder_checkpoint, a.dynamics_checkpoint, a.device, b2_split_ranges, b2_data_efficiency_episodes),
        'S5': lambda: s5_b3(root, status, a.encoder_checkpoint, a.dynamics_checkpoint, a.max_workers, b3_seeds),
        'S6': lambda: s6_report(root, status, a.report_path),
    }
    stage_dirs = {'S0': 's0-preflight', 'S1': 's1-a-structured', 'S2': 's2-b1-avoidability',
                  'S3': 's3-b2-collect', 'S4': 's4-b2-foresight', 'S5': 's5-b3-shield', 'S6': 's6-report'}

    def run_stage(name):
        try:
            stage_fns[name]()
            return True
        except Exception as exc:
            mark_failed(root / stage_dirs[name], exc)
            status.update(name, state='failed', error=str(exc), finished=now())
            print('STAGE FAILED:', name, exc, flush=True)
            return False

    # S0 must succeed before anything else can safely start (checkpoints, sim, resources).
    if not wanted or 'S0' in wanted:
        if not run_stage('S0'):
            raise SystemExit('S0 preflight failed; not starting any other stage')

    # S1 (A-line), S2 (B1) and S3 (B2 collection) are mutually independent (spec S5 table) and
    # run concurrently in separate threads; each shells out to its own subprocess/worker pool, so
    # the GIL is not a bottleneck here.
    from concurrent.futures import ThreadPoolExecutor
    parallel = [n for n in ('S1', 'S2', 'S3') if not wanted or n in wanted]
    ok = {'S1': True, 'S2': True, 'S3': True}
    if parallel:
        with ThreadPoolExecutor(max_workers=len(parallel)) as pool:
            futures = {pool.submit(run_stage, n): n for n in parallel}
            for future in futures:
                ok[futures[future]] = future.result()

    if (not wanted or 'S4' in wanted):
        if ok.get('S3', True):
            run_stage('S4')
        else:
            mark_failed(root / stage_dirs['S4'], 'skipped: S3 (its dependency) failed')
            status.update('S4', state='skipped (S3 failed)')

    if (not wanted or 'S5' in wanted):
        if stage_done(root / stage_dirs['S4']):
            run_stage('S5')
        else:
            mark_failed(root / stage_dirs['S5'], 'skipped: S4 (its dependency) did not complete')
            status.update('S5', state='skipped (S4 not done)')

    if not wanted or 'S6' in wanted:
        run_stage('S6')

    print('PIPELINE DONE', json.dumps(status.data['stages'], indent=2, default=str))


if __name__ == '__main__':
    main()
