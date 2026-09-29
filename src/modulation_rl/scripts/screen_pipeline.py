"""SCREEN-028 unattended pipeline (S0-S8, 20260929-screen-spec.md S6).

Run inside the mmhusky-node01 container (see doc/agent_logs/20260929-screen-launch.sh):
  python3 -u screen_pipeline.py --output-root /root/mm_husky_ws/results/screen-028
Resumable: each stage writes DONE/FAILED (plus result.json); training jobs resume from their newest
checkpoint; finished evaluation episodes are reused. Status: <output-root>/status.json.

  S0 preflight         GPU/memory/disk/analytical sim/checkpoint SHA/git
  S1 L1 harm test      policy-100k, 7 delay configs, deterministic, seeds 10000-10099 (no training)
  S2 D0 feasibility    dynObstacle: 2000-step training smoke + 6 eval episodes (current/future/past)
  S3 D1 training       D-std/D-oracle/D-hist x seeds 11,22 (6 jobs, needs S2)
  S4 L2 training       L-oracle/L-stale/L-hist x seeds 11,22 (6 jobs, needs S1 pass, else skipped)
  S5 L3 exploratory    world-model compensation arm (needs S1)
  S6 D2 evaluation     6 checkpoints (+2 frozen D-std) (needs S3)
  S7 L2 evaluation     6 checkpoints (needs S4)
  S8 report            doc/agent_logs/20260929-screen-report.md (needs everything; gaps stated)

Resources (hard limits, enforced in code): every process (training or evaluation episode worker)
holds one slot of a --max-workers (default 64) pool; a new batch starts only with >=60 GiB
MemAvailable and no new process starts below 40 GiB. Training jobs are spread over the GPUs; eval
workers use GPU = seed % n_gpus so a seed is always evaluated on the same card.
"""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
import p0_runner  # noqa: E402
import screen_analysis as sa  # noqa: E402
import screen_stats as st  # noqa: E402
from followup_pipeline import (available_memory_gb, now, stage_done, mark_done, mark_failed, _disk_free_gb,  # noqa: E402
                               _gpu_status, _ensure_analytical_running, _collect_worker_result)

WS = '/root/mm_husky_ws'
DEFAULT_POLICY = WS + '/results/p1a-20260923/policy-100k.pt'
DEFAULT_DYNAMICS = WS + '/results/p1-retrain-20260928/trainval-1000-r1/action.pt'
REGISTERED_TRAIN_SEEDS = (11, 22)
EVAL_SEED_RANGE = (10000, 10100)  # D53/D54 registration; 20000-20299, 9000-9199, 8000-8099 forbidden
L1_CONFIGS = [(name, {} if name == 'nominal' else
               ({'obs_latency_steps': k} if kind == 'full' else {'map_latency_steps': k}))
              for name, kind, k in sa.L1_ARMS]
STAGE_DIRS = {'S0': 's0-preflight', 'S1': 's1-l1', 'S2': 's2-d0', 'S3': 's3-d1-train', 'S4': 's4-l2-train',
              'S5': 's5-l3', 'S6': 's6-d2-eval', 'S7': 's7-l2-eval', 'S8': 's8-report'}
MIN_FREE_START_GB, MIN_FREE_PAUSE_GB = 60, 40


class SafeStatus:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.data = json.loads(self.path.read_text()) if self.path.exists() else dict(stages={})

    def update(self, stage, **fields):
        with self.lock:
            self.data['stages'].setdefault(stage, {}).update(fields)
            self.data['updated'] = now()
            self.data['available_memory_gb'] = round(available_memory_gb(), 1)
            self.path.write_text(json.dumps(self.data, indent=2, default=str))

    def snapshot(self):
        with self.lock:
            return json.loads(json.dumps(self.data, default=str))


class SlotPool:
    """Counts running processes (training + eval workers) against --max-workers. Training jobs are
    long-lived and start rarely, so while one is waiting for a slot eval workers may not take new ones."""

    def __init__(self, capacity):
        self.capacity, self.used, self.waiting, self.lock = capacity, 0, 0, threading.Lock()

    def try_acquire(self, priority=False):
        with self.lock:
            if self.used < self.capacity and (priority or self.waiting == 0):
                self.used += 1
                return True
            return False

    def release(self):
        with self.lock:
            self.used = max(0, self.used - 1)

    def acquire(self, poll=2.0):
        """Priority acquire (training / smoke jobs)."""
        with self.lock:
            self.waiting += 1
        try:
            while not self.try_acquire(priority=True):
                time.sleep(poll)
        finally:
            with self.lock:
                self.waiting -= 1


def log(*args):
    print(now(), *args, flush=True)


def wait_for_memory(min_gb, timeout_s=1800, poll=10):
    """Batch-start guard: block until MemAvailable >= min_gb (fail after timeout_s)."""
    t0 = time.monotonic()
    while available_memory_gb() < min_gb:
        if time.monotonic() - t0 > timeout_s:
            raise RuntimeError('available memory stayed below %.0f GiB for %ds' % (min_gb, timeout_s))
        time.sleep(poll)


def _git_status():
    """Like followup_pipeline._git_status but immune to 'dubious ownership' (the workspace is a host bind mount)."""
    root = SCRIPTS_DIR.resolve().parents[2]

    home = Path('/tmp/screen028-githome')  # container git is old (no GIT_CONFIG_GLOBAL); a private HOME carries safe.directory
    home.mkdir(exist_ok=True)
    (home / '.gitconfig').write_text('[safe]\n\tdirectory = %s\n' % root)

    def git(*a):
        return subprocess.check_output(['git', '-C', str(root), *a], text=True, env=dict(os.environ, HOME=str(home))).strip()
    try:
        status = git('status', '--short')
        return dict(head=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'), dirty=bool(status), status=status)
    except Exception as exc:
        return dict(error=str(exc))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 22), b''):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Evaluation pool
# ---------------------------------------------------------------------------

def eval_args(cfg, checkpoint, task, flags):
    return SimpleNamespace(checkpoint=checkpoint, task=task, world_type='sim', device=cfg.device, seed=11,
                           max_episode_steps=2000, ik_mode='fixed', ik_iterations=100, policy_mode='deterministic',
                           save_observations=False, base_vel_gain=1.0, base_vel_gain_range=None,
                           action_delay_steps=0, save_step_info=False, shield_config=None, **flags)


def worker_env(cfg, seed):
    env = dict(os.environ)
    env['P0_TASK_ID'] = getattr(cfg, 'task_id', 'SCREEN-028')  # CEIL-028 reuses this pool with its own id
    env['P0_AGENT'] = 'Claude Sonnet 5.5 /ybc'
    env['CUDA_VISIBLE_DEVICES'] = str(cfg.gpus[seed % len(cfg.gpus)])
    return env


def run_eval_arms(cfg, arms, stage_dir, pool, status, key, timeout_s, seeds=None):
    """arms: {name: SimpleNamespace(args for p0_runner.episode_command)}. All arms share one queue,
    interleaved by seed, and each writes <stage_dir>/<name>/episodes.jsonl. Episodes whose worker
    already produced a clean record are reused (resume)."""
    stage_dir = Path(stage_dir)
    seeds = list(cfg.eval_seeds if seeds is None else seeds)
    rows = {name: {} for name in arms}
    queue = []
    for seed in seeds:
        for name in arms:
            out = stage_dir / name / 'episodes'
            out.mkdir(parents=True, exist_ok=True)
            done_file = out / ('worker-%05d' % seed) / 'episodes.jsonl'
            reuse = None
            if done_file.exists():
                try:
                    row = json.loads(done_file.read_text().strip())
                    if row.get('exception') is None:
                        reuse = _collect_worker_result(seed, 0, done_file.parent, out)
                except Exception:
                    reuse = None
            if reuse is not None:
                rows[name][seed] = reuse
            else:
                queue.append((name, seed))
    wait_for_memory(MIN_FREE_START_GB)
    running = {}
    started = time.monotonic()
    total = len(queue) + sum(len(v) for v in rows.values())
    try:
        while queue or running:
            if time.monotonic() - started > timeout_s:
                raise TimeoutError('%s: eval timeout %.0fs, %d items unfinished' % (key, timeout_s, len(queue) + len(running)))
            while queue and available_memory_gb() >= MIN_FREE_PAUSE_GB and pool.try_acquire():
                name, seed = queue.pop(0)
                out = stage_dir / name / 'episodes'
                command = p0_runner.episode_command(arms[name], out, seed)
                logf = (out / ('worker-%05d.log' % seed)).open('w')
                proc = subprocess.Popen(command, stdout=logf, stderr=subprocess.STDOUT, env=worker_env(cfg, seed),
                                        cwd=str(SCRIPTS_DIR))
                running[(name, seed)] = (proc, logf, out / ('worker-%05d' % seed))
            for item in [k for k, (proc, _, _) in running.items() if proc.poll() is not None]:
                proc, logf, worker_dir = running.pop(item)
                logf.close()
                pool.release()
                name, seed = item
                rows[name][seed] = _collect_worker_result(seed, proc.returncode, worker_dir, stage_dir / name / 'episodes')
            status.update(key, running=len(running), queued=len(queue), completed=sum(len(v) for v in rows.values()),
                          total=total, available_memory_gb=round(available_memory_gb(), 1))
            time.sleep(2.0)
    finally:
        for proc, logf, _ in running.values():
            proc.kill(); logf.close(); pool.release()
    summary = {}
    for name in arms:
        with (stage_dir / name / 'episodes.jsonl').open('w') as f:
            for seed in sorted(rows[name]):
                f.write(json.dumps(rows[name][seed], default=str) + '\n')
        summary[name] = dict(episodes=len(rows[name]), exceptions=sum(1 for r in rows[name].values() if r.get('exception')))
    return summary


# ---------------------------------------------------------------------------
# Training jobs
# ---------------------------------------------------------------------------

def train_command(cfg, job, output, resume=None):
    args = SimpleNamespace(**job['flags'])
    cmd = [sys.executable, '-u', str(SCRIPTS_DIR / 'p0_runner.py'), 'train', '--task', job['task'], '--seed', str(job['seed']),
           '--steps', str(cfg.train_steps), '--batch', str(cfg.batch), '--random-steps', str(cfg.random_steps),
           '--replay-capacity', str(cfg.replay_capacity), '--save-interval', str(cfg.save_interval), '--eval-interval', '0',
           '--ik-mode', 'fixed', '--ik-iterations', '100', '--replay-compact-maps'] + p0_runner.screen_flags(args)
    if resume:
        cmd += ['--resume', str(resume)]
    return cmd + ['--output', str(output)]


def newest_checkpoint(job_dir):
    files = [p for p in Path(job_dir).glob('a*/*.pt') if p.name == 'latest.pt' or p.name.startswith('step-')]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def last_progress(log_path):
    try:
        data = Path(log_path).read_bytes()[-4096:].decode(errors='ignore')
        for line in reversed(data.splitlines()):
            if line.startswith('TRAIN '):
                return line
    except Exception:
        pass
    return None


EXPORT_LOCK = threading.Semaphore(2)
JOBS_LOCK = threading.Lock()


def export_policy(src, dst):
    """Policy-only checkpoint in the same v2 layout as policy-100k.pt (an eval worker must not load a
    checkpoint that carries the replay buffer: 64 workers x that file would exhaust host memory)."""
    import torch
    from checkpointing import SEMANTICS, load_trusted
    with EXPORT_LOCK:
        data = load_trusted(src, map_location='cpu')
        light = dict(version=2, semantics=data.get('semantics', SEMANTICS), agent=dict(policy=data['agent']['policy']),
                     counters=data['counters'], agent_config=data['agent_config'],
                     derived_from=dict(source=str(src), source_sha256=sha256_file(src),
                                       note='policy-only export for SCREEN-028 evaluation'))
        del data
        tmp = Path(str(dst) + '.tmp')
        torch.save(light, str(tmp))
        os.replace(str(tmp), str(dst))


def run_training_job(cfg, job, root, pool, status, stage_key, jobs_state, deadline):
    job_dir = Path(root) / 'train' / job['name']
    job_dir.mkdir(parents=True, exist_ok=True)
    policy_path = job_dir / 'policy.pt'

    def note(**fields):
        with JOBS_LOCK:
            jobs_state[job['name']].update(fields)
            snapshot = {k: dict(v) for k, v in jobs_state.items()}
        status.update(stage_key, jobs=snapshot)

    with JOBS_LOCK:
        jobs_state[job['name']] = dict(state='queued', attempt=0)
    if (job_dir / 'DONE').exists() and policy_path.exists():
        note(state='done (resumed)')
        return True
    def finished_summaries():
        return [x for x in sorted(job_dir.glob('a*/summary.json')) if json.loads(x.read_text()).get('steps') == cfg.train_steps]

    for _ in range(cfg.max_attempts):
        if finished_summaries():
            break
        attempt = 0
        while (job_dir / ('a%d' % attempt)).exists():
            attempt += 1
        resume = newest_checkpoint(job_dir)
        out = job_dir / ('a%d' % attempt)
        pool.acquire()
        try:
            wait_for_memory(MIN_FREE_START_GB)
            env = dict(os.environ, P0_TASK_ID=getattr(cfg, 'task_id', 'SCREEN-028'), P0_AGENT='Claude Sonnet 5.5 /ybc',
                       CUDA_VISIBLE_DEVICES=str(job['gpu']))
            logf = open(str(job_dir / ('a%d.log' % attempt)), 'w')
            proc = subprocess.Popen(train_command(cfg, job, out, resume), stdout=logf, stderr=subprocess.STDOUT,
                                    env=env, cwd=str(SCRIPTS_DIR))
            note(state='running', attempt=attempt, pid=proc.pid, resumed_from=str(resume) if resume else None, started=now())
            while proc.poll() is None:
                if time.monotonic() > deadline:
                    proc.kill()
                    note(state='timeout', progress=last_progress(job_dir / ('a%d.log' % attempt)))
                    logf.close()
                    mark_failed(job_dir, 'training timeout')
                    return False
                note(progress=last_progress(job_dir / ('a%d.log' % attempt)))
                time.sleep(30)
            logf.close()
        finally:
            pool.release()
        note(returncode=proc.returncode, progress=last_progress(job_dir / ('a%d.log' % attempt)))
    finished = finished_summaries()
    if not finished:
        note(state='failed')
        mark_failed(job_dir, 'no finished attempt after %d tries' % cfg.max_attempts)
        return False
    final = finished[-1].parent / 'latest.pt'
    note(state='exporting', final_checkpoint=str(final))
    export_policy(final, policy_path)
    mark_done(job_dir, final_checkpoint=str(final), policy=str(policy_path), policy_sha256=sha256_file(policy_path),
              summary=json.loads(finished[-1].read_text()))
    note(state='done')
    return True


def run_training_stage(cfg, jobs, root, pool, status, stage_key):
    jobs_state = {}
    deadline = time.monotonic() + cfg.train_timeout_hours * 3600
    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        futures = {j['name']: ex.submit(run_training_job, cfg, j, root, pool, status, stage_key, jobs_state, deadline) for j in jobs}
        outcome = {name: bool(f.result()) for name, f in futures.items()}
    return outcome


# ---------------------------------------------------------------------------
# Job/arm definitions
# ---------------------------------------------------------------------------

def d_jobs(cfg):
    out = []
    for i, seed in enumerate(cfg.train_seeds):
        for j, (arm, flags) in enumerate([('D-std', {}), ('D-oracle', dict(dyn_map_mode='future')), ('D-hist', dict(dyn_map_mode='past'))]):
            out.append(dict(name='%s-s%d' % (arm, seed), task='dynobstacle', seed=seed, flags=flags,
                            gpu=cfg.gpus[(len(out)) % len(cfg.gpus)]))
    return out


def l_jobs(cfg, k_sel, mode, offset):
    lat = {'obs_latency_steps': k_sel} if mode == 'full' else {'map_latency_steps': k_sel}
    out = []
    for seed in cfg.train_seeds:
        for arm, flags in [('L-oracle', {}), ('L-stale', dict(lat)), ('L-hist', dict(lat, obs_action_history=k_sel))]:
            out.append(dict(name='%s-s%d' % (arm, seed), task='simpleobstacle', seed=seed, flags=flags,
                            gpu=cfg.gpus[(offset + len(out)) % len(cfg.gpus)]))
    return out


def load_result(root, stage):
    path = Path(root) / STAGE_DIRS[stage] / 'result.json'
    return json.loads(path.read_text()) if path.exists() else None


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

def s0_preflight(cfg, root, status):
    d = root / STAGE_DIRS['S0']
    d.mkdir(parents=True, exist_ok=True)
    status.update('S0', state='running', started=now())
    m = dict(checked=now(), available_memory_gb=available_memory_gb(), disk_free_gb=_disk_free_gb(root),
             gpu=_gpu_status(), analytical_running=_ensure_analytical_running(), git=_git_status(),
             policy_sha256=p0_runner.sha(cfg.policy), dynamics_sha256=p0_runner.sha(cfg.dynamics),
             eval_seeds=[cfg.eval_seeds[0], cfg.eval_seeds[-1]], train_seeds=list(cfg.train_seeds),
             max_workers=cfg.max_workers, gpus=cfg.gpus, omp_num_threads=os.environ.get('OMP_NUM_THREADS'),
             args={k: v for k, v in vars(cfg).items() if k != 'eval_seeds'})
    (d / 'manifest.json').write_text(json.dumps(m, indent=2, default=str))
    if m['available_memory_gb'] < MIN_FREE_START_GB:
        raise SystemExit('S0: available memory %.1f GiB < %d GiB' % (m['available_memory_gb'], MIN_FREE_START_GB))
    if not m['analytical_running']:
        raise SystemExit('S0: analytical simulator not running')
    mark_done(d, **m)
    status.update('S0', state='done', finished=now())


def s1_l1(cfg, root, status, pool):
    d = root / STAGE_DIRS['S1']
    status.update('S1', state='running', started=now())
    arms = {name: eval_args(cfg, cfg.policy, 'simpleobstacle', flags) for name, flags in L1_CONFIGS}
    summary = run_eval_arms(cfg, arms, d, pool, status, 'S1', 1.5 * 3600 * len(arms))
    forced = cfg.smoke_force_l1
    result = sa.analyze_l1(d, cfg.eval_seeds, d / 'analysis')
    if forced:
        kind, k = forced.split(':')
        result['decision'] = dict(tier='smoke-forced', k_sel=int(k), mode=kind, l2_runs=True, smoke_override=True)
        (d / 'analysis' / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True))
    (d / 'result.json').write_text(json.dumps(dict(eval=summary, analysis=result), indent=2, sort_keys=True))
    mark_done(d, decision=result['decision'])
    status.update('S1', state='done', finished=now(), decision=result['decision'])


def l1_decision(root):
    r = load_result(root, 'S1')
    return r['analysis']['decision'] if r else None


def s2_d0(cfg, root, status, pool):
    d = root / STAGE_DIRS['S2']
    d.mkdir(parents=True, exist_ok=True)
    status.update('S2', state='running', started=now())
    smoke_job = dict(name='d0-smoke', task='dynobstacle', seed=11, flags={}, gpu=cfg.gpus[0])
    train_cfg = SimpleNamespace(**dict(vars(cfg), train_steps=cfg.d0_steps, save_interval=cfg.d0_steps))
    out = d / 'train-smoke'
    result = dict(train_steps=cfg.d0_steps, checks={})
    if not (out / 'summary.json').exists():
        pool.acquire()
        try:
            wait_for_memory(MIN_FREE_START_GB)
            with (d / 'train-smoke.log').open('w') as logf:
                rc = subprocess.run(train_command(train_cfg, smoke_job, out), stdout=logf, stderr=subprocess.STDOUT,
                                    env=dict(os.environ, P0_TASK_ID='SCREEN-028', CUDA_VISIBLE_DEVICES=str(cfg.gpus[0])),
                                    cwd=str(SCRIPTS_DIR), timeout=3 * 3600).returncode
        finally:
            pool.release()
        result['checks']['train_returncode'] = rc
    summary = json.loads((out / 'summary.json').read_text()) if (out / 'summary.json').exists() else None
    result['checks']['train_completed'] = bool(summary and summary.get('steps') == cfg.d0_steps)
    result['train_summary'] = summary
    if result['checks']['train_completed']:
        policy = d / 'smoke-policy.pt'
        if not policy.exists():
            export_policy(out / 'latest.pt', policy)
        arms = {m: eval_args(cfg, str(policy), 'dynobstacle', {} if m == 'current' else dict(dyn_map_mode=m))
                for m in ('current', 'future', 'past')}
        arms['frozen'] = eval_args(cfg, str(policy), 'dynobstacle', dict(dyn_freeze=True))
        summary_eval = run_eval_arms(cfg, arms, d / 'eval-smoke', pool, status, 'S2', 3600, seeds=cfg.eval_seeds[:2])
        result['eval'] = summary_eval
        result['checks']['eval_no_exceptions'] = all(v['exceptions'] == 0 and v['episodes'] == 2 for v in summary_eval.values())
    result['passes'] = bool(result['checks'].get('train_completed') and result['checks'].get('eval_no_exceptions'))
    (d / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True, default=str))
    if not result['passes']:
        raise RuntimeError('D0 feasibility failed: %s' % json.dumps(result['checks']))
    mark_done(d, **result['checks'])
    status.update('S2', state='done', finished=now())


def _stage_from_outcome(root, key, stage, outcome, status):
    d = root / STAGE_DIRS[stage]
    d.mkdir(parents=True, exist_ok=True)
    (d / 'result.json').write_text(json.dumps(dict(jobs=outcome), indent=2))
    if not any(outcome.values()):
        raise RuntimeError('%s: every training job failed' % key)
    mark_done(d, jobs=outcome)
    status.update(key, state='done' if all(outcome.values()) else 'done (partial: %s)' % [k for k, v in outcome.items() if not v],
                  finished=now())


def s3_d1(cfg, root, status, pool):
    status.update('S3', state='running', started=now())
    outcome = run_training_stage(cfg, d_jobs(cfg), root, pool, status, 'S3')
    _stage_from_outcome(root, 'S3', 'S3', outcome, status)


def s4_l2(cfg, root, status, pool):
    decision = l1_decision(root)
    if not decision or not decision.get('l2_runs'):
        raise RuntimeError('skipped: L1 did not pass (decision=%s)' % decision)
    status.update('S4', state='running', started=now(), k_sel=decision['k_sel'], mode=decision['mode'])
    outcome = run_training_stage(cfg, l_jobs(cfg, decision['k_sel'], decision['mode'], 6), root, pool, status, 'S4')
    _stage_from_outcome(root, 'S4', 'S4', outcome, status)


def s5_l3(cfg, root, status, pool):
    d = root / STAGE_DIRS['S5']
    d.mkdir(parents=True, exist_ok=True)
    status.update('S5', state='running', started=now())
    decision = l1_decision(root)
    if decision and decision.get('l2_runs'):
        mode, k = decision['mode'], decision['k_sel']
    else:
        mode, k = 'full', 3  # D53 L3: k=3 if L1 did not pass
    stale_arm = ('full%d' if mode == 'full' else 'map%d') % k
    config = dict(encoder_checkpoint=cfg.policy, dynamics_checkpoint=cfg.dynamics, device='cuda')
    (d / 'wm-comp-config.json').write_text(json.dumps(config, indent=2))
    flags = ({'obs_latency_steps': k} if mode == 'full' else {'map_latency_steps': k})
    flags['latency_wm_comp'] = str(d / 'wm-comp-config.json')
    arms = {'wm-comp': eval_args(cfg, cfg.policy, 'simpleobstacle', flags)}
    summary = run_eval_arms(cfg, arms, d, pool, status, 'S5', 1.5 * 3600)
    result = sa.analyze_l3(root / STAGE_DIRS['S1'], d, cfg.eval_seeds, d / 'analysis', stale_arm)
    (d / 'result.json').write_text(json.dumps(dict(eval=summary, analysis=result, mode=mode, k=k), indent=2, sort_keys=True))
    mark_done(d, mode=mode, k=k)
    status.update('S5', state='done', finished=now())


def _eval_trained(cfg, root, status, pool, key, stage, names_flags, task, analyze):
    d = root / STAGE_DIRS[stage]
    d.mkdir(parents=True, exist_ok=True)
    status.update(key, state='running', started=now())
    arms = {}
    for name, job_name, flags in names_flags:
        policy = root / 'train' / job_name / 'policy.pt'
        if policy.exists():
            arms[name] = eval_args(cfg, str(policy), task, flags)
    if not arms:
        raise RuntimeError('%s: no trained policy available' % key)
    summary = run_eval_arms(cfg, arms, d, pool, status, key, 1.5 * 3600 * len(arms))
    result = analyze(d)
    (d / 'result.json').write_text(json.dumps(dict(eval=summary, analysis=result, missing=sorted(set(n for n, _, _ in names_flags) - set(arms))),
                                              indent=2, sort_keys=True))
    mark_done(d)
    status.update(key, state='done', finished=now())


def s6_d2(cfg, root, status, pool):
    names_flags = []
    for seed in cfg.train_seeds:
        names_flags += [('D-std-s%d' % seed, 'D-std-s%d' % seed, {}),
                        ('D-stdfrozen-s%d' % seed, 'D-std-s%d' % seed, dict(dyn_freeze=True)),
                        ('D-oracle-s%d' % seed, 'D-oracle-s%d' % seed, dict(dyn_map_mode='future')),
                        ('D-hist-s%d' % seed, 'D-hist-s%d' % seed, dict(dyn_map_mode='past'))]
    _eval_trained(cfg, root, status, pool, 'S6', 'S6', names_flags, 'dynobstacle',
                  lambda d: sa.analyze_d(d, cfg.eval_seeds, d / 'analysis'))


def s7_l2(cfg, root, status, pool):
    decision = l1_decision(root)
    k, mode = decision['k_sel'], decision['mode']
    lat = {'obs_latency_steps': k} if mode == 'full' else {'map_latency_steps': k}
    names_flags = []
    for seed in cfg.train_seeds:
        names_flags += [('L-oracle-s%d' % seed, 'L-oracle-s%d' % seed, {}),
                        ('L-stale-s%d' % seed, 'L-stale-s%d' % seed, dict(lat)),
                        ('L-hist-s%d' % seed, 'L-hist-s%d' % seed, dict(lat, obs_action_history=k))]
    _eval_trained(cfg, root, status, pool, 'S7', 'S7', names_flags, 'simpleobstacle',
                  lambda d: sa.analyze_l2(d, cfg.eval_seeds, d / 'analysis', k, mode))


def s8_report(cfg, root, status):
    status.update('S8', state='running', started=now())
    from screen_report import build_report
    Path(cfg.report_path).write_text(build_report(root, cfg))
    mark_done(root / STAGE_DIRS['S8'])
    status.update('S8', state='done', finished=now())


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def parse_seed_spec(spec):
    if ':' in spec:
        lo, hi = (int(x) for x in spec.split(':'))
        return list(range(lo, hi))
    return [int(x) for x in spec.split(',')]


def validate_seeds(cfg):
    lo, hi = EVAL_SEED_RANGE
    if not cfg.eval_seeds or min(cfg.eval_seeds) < lo or max(cfg.eval_seeds) >= hi:
        raise SystemExit('eval seeds must stay inside the D53/D54 registration %d-%d' % (lo, hi - 1))
    if any(s not in REGISTERED_TRAIN_SEEDS for s in cfg.train_seeds):
        raise SystemExit('training seeds must be a subset of %s' % (REGISTERED_TRAIN_SEEDS,))
    if cfg.max_workers > 64:
        raise SystemExit('--max-workers must be <= 64')


def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument('--output-root', default=WS + '/results/screen-028')
    p.add_argument('--policy', default=DEFAULT_POLICY)
    p.add_argument('--dynamics', default=DEFAULT_DYNAMICS)
    p.add_argument('--device', default='cuda')
    p.add_argument('--gpus', default='0,1,2,3')
    p.add_argument('--max-workers', type=int, default=64)
    p.add_argument('--eval-seeds', default='10000:10100')
    p.add_argument('--train-seeds', default='11,22')
    p.add_argument('--train-steps', type=int, default=100000)
    p.add_argument('--save-interval', type=int, default=20000)
    p.add_argument('--random-steps', type=int, default=1000)
    p.add_argument('--batch', type=int, default=256)
    p.add_argument('--replay-capacity', type=int, default=100000)
    p.add_argument('--d0-steps', type=int, default=2000)
    p.add_argument('--train-timeout-hours', type=float, default=10.0,
                   help='per training job wall limit; spec said 6 h but dynObstacle trains at ~4.2 steps/s (smoke, 12 procs) => ~6.6 h per 100k')
    p.add_argument('--max-attempts', type=int, default=4, help='launch attempts per training job (resume from newest checkpoint)')
    p.add_argument('--report-path', default=WS + '/doc/agent_logs/20260929-screen-report.md')
    p.add_argument('--only', default=None, help='comma-separated subset of stages (smoke/debug only)')
    p.add_argument('--smoke-force-l1', default=None, help='SMOKE ONLY: force the L1 decision, e.g. full:3 (never used for the real run)')
    return p


def main(argv=None):
    cfg = build_parser().parse_args(argv)
    cfg.eval_seeds = parse_seed_spec(cfg.eval_seeds)
    cfg.train_seeds = tuple(parse_seed_spec(cfg.train_seeds))
    cfg.gpus = [int(x) for x in cfg.gpus.split(',')]
    validate_seeds(cfg)
    root = Path(cfg.output_root)
    root.mkdir(parents=True, exist_ok=True)
    status = SafeStatus(root / 'status.json')
    pool = SlotPool(cfg.max_workers)
    wanted = set(cfg.only.split(',')) if cfg.only else None

    if wanted is None or 'S0' in wanted:
        if not stage_done(root / STAGE_DIRS['S0']):
            s0_preflight(cfg, root, status)
        else:
            status.update('S0', state='done (resumed)')

    fns = {'S1': lambda: s1_l1(cfg, root, status, pool), 'S2': lambda: s2_d0(cfg, root, status, pool),
           'S3': lambda: s3_d1(cfg, root, status, pool), 'S4': lambda: s4_l2(cfg, root, status, pool),
           'S5': lambda: s5_l3(cfg, root, status, pool), 'S6': lambda: s6_d2(cfg, root, status, pool),
           'S7': lambda: s7_l2(cfg, root, status, pool), 'S8': lambda: s8_report(cfg, root, status)}
    deps = {'S1': [], 'S2': [], 'S3': ['S2'], 'S4': ['S1'], 'S5': ['S1'], 'S6': ['S3'], 'S7': ['S4'],
            'S8': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7']}
    order = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8']
    events = {s: threading.Event() for s in order}
    outcome = {}

    def run_stage(name):
        try:
            if wanted is not None and name not in wanted:
                outcome[name] = 'not selected'
                return
            for dep in deps[name]:
                events[dep].wait()
            failed = [dep for dep in deps[name] if outcome.get(dep) not in ('done', 'not selected')]
            if name != 'S8' and failed:
                outcome[name] = 'skipped'
                mark_failed(root / STAGE_DIRS[name], 'skipped: dependency %s did not complete' % failed)
                status.update(name, state='skipped (%s)' % ','.join(failed))
                return
            if name != 'S8' and stage_done(root / STAGE_DIRS[name]):
                outcome[name] = 'done'
                status.update(name, state='done (resumed)')
                return
            fns[name]()
            outcome[name] = 'done'
        except BaseException as exc:  # noqa: BLE001 - every failure must surface in status, never kill sibling stages
            outcome[name] = 'failed'
            (root / STAGE_DIRS[name]).mkdir(parents=True, exist_ok=True)
            mark_failed(root / STAGE_DIRS[name], repr(exc))
            status.update(name, state='failed' if not str(exc).startswith('skipped') else 'skipped', error=repr(exc)[:500], finished=now())
            log('STAGE', name, 'FAILED/SKIPPED:', repr(exc))
        finally:
            events[name].set()

    threads = [threading.Thread(target=run_stage, args=(s,), name=s, daemon=False) for s in order]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    log('PIPELINE DONE', json.dumps(outcome))


if __name__ == '__main__':
    main()
