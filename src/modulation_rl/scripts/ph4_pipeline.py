"""PH4.1 unattended pipeline (D62; also runs the PH3-OBSMAP diagnostics, D60). Spec: 20260929-ph3-obsmap-spec.md S6.

Run inside the mmhusky-node01 container (see doc/agent_logs/20260929-ph4-launch.sh):
  python3 -u ph4_pipeline.py --output-root /root/mm_husky_ws/results/ph4-train
Resumable: training jobs resume from their newest checkpoint with the same --steps; finished evaluation episodes are
reused; DONE markers skip finished jobs. Status: <output-root>/status.json.

  S0 preflight        GPU/memory/disk/analytical sim/policy SHA/git
  S1 training         5 runs in parallel (4 GPUs): K-std-r3 s11/s22, K-std-r5 s11/s22 (--obsmap-radius), G-std s22 (global);
                      100k steps like policy-100k (+ --replay-compact-maps), budget-end checkpoint exported policy-only (D55)
  S1L long training   D64 convergence check, started together with S1: K-std-r3-long / K-std-r5-long, seed 11, --steps 300000
                      --save-interval 50000 (the budget must stay 300000 on every resume)
  S2 PH3 diagnostics  policy-100k on 4 configs (nominal with --obsmap-log-reroutes, r=10, 5, 3), 100 episodes each -> results/ph3-obsmap/
  S3 random controls  --policy-override random with --obsmap-radius 3 / 5, 100 episodes each
  S4 trained eval     each finished policy, deterministic, in its own training condition, seeds 10000-10099
  S6 learning curves  (diagnostic) every intermediate checkpoint (100k runs: 20k/40k/60k/80k; long runs: 50k-250k) exported and
                      evaluated with 100 episodes while training runs; only when no final-policy evaluation is pending
  S5 analysis         PH3 (D60, diagnostic) as soon as S2 is done; PH4.1 interim report (D62, 100k runs) when those are evaluated;
                      final report (D62 + D64) when the long runs are evaluated too; reports + analysis.json

ROS masters: every training job gets its own analytical ROS stack (rosmaster + move_group, ports TRAIN_MASTER_BASE+i) and the
evaluation workers are spread over EVAL_MASTERS further stacks (by seed). Reason (measured 2026-09-29): non-global planning
recomputes the planner weights through three ROS-costmap inflations per recompute, each of which talks to the master; 47
processes on the single default master saturated it (rosmaster at 100% CPU) and slowed training ~4x. The stacks are started
(if not alive) by the pipeline as detached processes and are identical to the default one (verified: same trajectory hashes).

Resources (enforced in code, one shared slot pool of --max-workers, default 47 = 7 training + <=40 evaluation workers so
training keeps priority): a new batch starts only with >=60 GiB MemAvailable and no new process starts below 40 GiB.
"""
import argparse
import json
import re
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
import p0_runner  # noqa: E402
import ph4_analysis as pa  # noqa: E402
import screen_analysis as sa  # noqa: E402
import screen_pipeline as sp  # noqa: E402
from followup_pipeline import (available_memory_gb, now, stage_done, mark_done, mark_failed, _disk_free_gb,  # noqa: E402
                               _gpu_status, _ensure_analytical_running)

WS = sp.WS
TASK_ID = 'PH4-1'
REGISTERED_TRAIN_SEEDS = (11, 22)
EVAL_SEED_RANGE = (10000, 10100)  # 20000-20299, 9000-9199, 8000-8099 forbidden
BASELINE_DIR = WS + '/results/stage0-028-r03c/gain1.0_delay0'
MIN_DISK_GB = 100

# (job name, task, training seed, extra flags) -- D62 pre-registered
JOB_SPECS = [('K-std-r3-s11', 11, dict(obsmap_radius=3.0)), ('K-std-r3-s22', 22, dict(obsmap_radius=3.0)),
             ('K-std-r5-s11', 11, dict(obsmap_radius=5.0)), ('K-std-r5-s22', 22, dict(obsmap_radius=5.0)),
             ('G-std-s22', 22, {})]
LONG_SPECS = [('K-std-r3-long', 11, dict(obsmap_radius=3.0)), ('K-std-r5-long', 11, dict(obsmap_radius=5.0))]  # D64
LONG_STEPS, LONG_SAVE_INTERVAL = 300000, 50000
PH3_CONFIGS = [('nominal', dict(obsmap_log_reroutes=True)), ('r10', dict(obsmap_radius=10.0)),
               ('r5', dict(obsmap_radius=5.0)), ('r3', dict(obsmap_radius=3.0))]
RANDOM_CONFIGS = [('random-r3', dict(policy_override='random', obsmap_radius=3.0)),
                  ('random-r5', dict(policy_override='random', obsmap_radius=5.0))]

TRAIN_MASTER_BASE = 11421   # one master per training job (7 jobs)
EVAL_MASTER_BASE, EVAL_MASTERS = 11431, 4
ROS_IP = '127.0.0.1'


def master_env(port):
    return {'ROS_MASTER_URI': 'http://%s:%d' % (ROS_IP, port), 'ROS_IP': ROS_IP}


def eval_master_port(seed):
    return EVAL_MASTER_BASE + seed % EVAL_MASTERS


_orig_worker_env = sp.worker_env


def worker_env(cfg, seed):
    """screen_pipeline.worker_env + the ROS master of this evaluation seed (spread over EVAL_MASTERS stacks)."""
    env = _orig_worker_env(cfg, seed)
    env.update(master_env(eval_master_port(seed)))
    return env


sp.worker_env = worker_env  # run_eval_arms looks the function up in its own module at call time

_orig_train_command = sp.train_command


def train_command(cfg, job, output, resume=None):
    """screen_pipeline.train_command + the obsmap switches of the job (inserted before --resume/--output)."""
    cmd = _orig_train_command(cfg, job, output, resume)
    return cmd[:-2] + p0_runner.obsmap_flags(SimpleNamespace(**job['flags'])) + cmd[-2:]


sp.train_command = train_command  # run_training_job looks the function up in its own module at call time


def log(*args):
    print(now(), *args, flush=True)


def train_jobs(cfg):
    return [dict(name=name, task='simpleobstacle', seed=seed, flags=dict(flags), gpu=cfg.gpus[i % len(cfg.gpus)],
                 env=master_env(TRAIN_MASTER_BASE + i))
            for i, (name, seed, flags) in enumerate(JOB_SPECS)]


def long_jobs(cfg):
    return [dict(name=name, task='simpleobstacle', seed=seed, flags=dict(flags), gpu=cfg.gpus[(len(JOB_SPECS) + i) % len(cfg.gpus)],
                 env=master_env(TRAIN_MASTER_BASE + len(JOB_SPECS) + i))
            for i, (name, seed, flags) in enumerate(LONG_SPECS)]


def ros_ports():
    return [TRAIN_MASTER_BASE + i for i in range(len(JOB_SPECS) + len(LONG_SPECS))] + [EVAL_MASTER_BASE + i for i in range(EVAL_MASTERS)]


def stack_alive(port):
    import os
    import subprocess
    env = dict(os.environ, **master_env(port))
    try:
        out = subprocess.run(['rosnode', 'list'], env=env, capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return False
    return '/move_group' in out


def ensure_ros_stacks(root, ports, wait_s=180):
    """Start (detached, surviving a pipeline restart) the analytical stacks that are not alive and wait until move_group is up."""
    import os
    import subprocess
    logdir = Path(root) / 'ros-stacks'
    logdir.mkdir(parents=True, exist_ok=True)
    started = []
    for port in ports:
        if not stack_alive(port):
            logf = open(str(logdir / ('ros-%d.log' % port)), 'a')
            subprocess.Popen(['roslaunch', 'modulation_rl', 'n2m2_husky_analytical.launch', 'gui:=false'],
                             env=dict(os.environ, **master_env(port)), stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
            started.append(port)
    t0 = time.monotonic()
    pending = list(ports)
    while pending:
        pending = [p for p in pending if not stack_alive(p)]
        if pending and time.monotonic() - t0 > wait_s:
            raise RuntimeError('ROS stacks not up after %ds: %s' % (wait_s, pending))
        if pending:
            time.sleep(3)
    return started


def all_jobs(cfg):
    return train_jobs(cfg) + long_jobs(cfg)


def long_cfg(cfg):
    """The same configuration with the 300k budget (screen_pipeline reads train_steps/save_interval from cfg)."""
    return SimpleNamespace(**dict(vars(cfg), train_steps=cfg.long_steps, save_interval=cfg.long_save_interval,
                                  train_timeout_hours=cfg.long_timeout_hours))


def job_cfg(cfg, name):
    return long_cfg(cfg) if name.endswith('-long') else cfg


def ph3_arms(cfg):
    return {name: sp.eval_args(cfg, cfg.policy, 'simpleobstacle', dict(flags)) for name, flags in PH3_CONFIGS}


def random_arms(cfg):
    return {name: sp.eval_args(cfg, cfg.policy, 'simpleobstacle', dict(flags)) for name, flags in RANDOM_CONFIGS}


def trained_arm(cfg, job, policy):
    return sp.eval_args(cfg, str(policy), 'simpleobstacle', dict(job['flags']))


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

def s0_preflight(cfg, root, status):
    d = root / 's0-preflight'
    d.mkdir(parents=True, exist_ok=True)
    status.update('S0', state='running', started=now())
    started_stacks = ensure_ros_stacks(root, ros_ports())
    m = dict(checked=now(), ros_stacks=dict(train_base=TRAIN_MASTER_BASE, eval_base=EVAL_MASTER_BASE, eval_masters=EVAL_MASTERS,
                                            started_now=started_stacks), available_memory_gb=available_memory_gb(), disk_free_gb=_disk_free_gb(root), gpu=_gpu_status(),
             analytical_running=_ensure_analytical_running(), git=sp._git_status(), policy_sha256=p0_runner.sha(cfg.policy),
             baseline_dir=cfg.baseline_dir, eval_seeds=[cfg.eval_seeds[0], cfg.eval_seeds[-1]], max_workers=cfg.max_workers, gpus=cfg.gpus,
             train_commands={j['name']: train_command(job_cfg(cfg, j['name']), j, root / 'train' / j['name'] / 'a0') for j in all_jobs(cfg)},
             ph3_eval_flags={k: {a: b for a, b in vars(v).items() if a.startswith('obsmap')} for k, v in ph3_arms(cfg).items()},
             args={k: v for k, v in vars(cfg).items() if k != 'eval_seeds'})
    (d / 'manifest.json').write_text(json.dumps(m, indent=2, default=str))
    if m['available_memory_gb'] < sp.MIN_FREE_START_GB:
        raise SystemExit('S0: available memory %.1f GiB < %d GiB' % (m['available_memory_gb'], sp.MIN_FREE_START_GB))
    if m['disk_free_gb'] < cfg.min_disk_gb:
        raise SystemExit('S0: free disk %.0f GiB < %d GiB' % (m['disk_free_gb'], cfg.min_disk_gb))
    if not m['analytical_running']:
        raise SystemExit('S0: analytical simulator not running')
    mark_done(d, **{k: m[k] for k in ('checked', 'policy_sha256')})
    status.update('S0', state='done', finished=now())


def s1_train(cfg, root, status, pool):
    d = root / 's1-train'
    d.mkdir(parents=True, exist_ok=True)
    if not (d / 'started.json').exists():
        (d / 'started.json').write_text(json.dumps(dict(started=now(), epoch=time.time())))
    status.update('S1', state='running', started=now(), train_steps=cfg.train_steps)
    outcome = sp.run_training_stage(cfg, train_jobs(cfg), root, pool, status, 'S1')
    (d / 'result.json').write_text(json.dumps(dict(jobs=outcome), indent=2))
    if not any(outcome.values()):
        raise RuntimeError('S1: every training job failed')
    mark_done(d, jobs=outcome)
    status.update('S1', state='done' if all(outcome.values()) else 'done (partial: %s)' % [k for k, v in outcome.items() if not v], finished=now())
    return outcome


def s1_long(cfg, root, status, pool):
    d = root / 's1-long'
    d.mkdir(parents=True, exist_ok=True)
    if not (d / 'started.json').exists():
        (d / 'started.json').write_text(json.dumps(dict(started=now(), epoch=time.time())))
    lc = long_cfg(cfg)
    status.update('S1L', state='running', started=now(), train_steps=lc.train_steps)
    outcome = sp.run_training_stage(lc, long_jobs(cfg), root, pool, status, 'S1L')
    (d / 'result.json').write_text(json.dumps(dict(jobs=outcome), indent=2))
    if not any(outcome.values()):
        raise RuntimeError('S1L: every long training job failed')
    mark_done(d, jobs=outcome)
    status.update('S1L', state='done' if all(outcome.values()) else 'done (partial: %s)' % [k for k, v in outcome.items() if not v], finished=now())
    return outcome


def s2_ph3(cfg, root, status, pool):
    d = Path(cfg.ph3_dir)
    status.update('S2', state='running', started=now())
    summary = sp.run_eval_arms(cfg, ph3_arms(cfg), d, pool, status, 'S2', cfg.eval_timeout_hours * 3600 * 4)
    mark_done(root / 's2-ph3', eval=summary)
    status.update('S2', state='done', finished=now(), eval=summary)


def s3_random(cfg, root, status, pool):
    d = root / 's3-eval'
    status.update('S3', state='running', started=now())
    summary = sp.run_eval_arms(cfg, random_arms(cfg), d, pool, status, 'S3', cfg.eval_timeout_hours * 3600 * 2)
    mark_done(root / 's3-random', eval=summary)
    status.update('S3', state='done', finished=now(), eval=summary)


FINAL_BUSY = {'n': 0}
FINAL_LOCK = threading.Lock()


def s4_trained_eval(cfg, root, status, pool, train_finished, main_evaluated):
    """Evaluate every trained policy as soon as its job is done (policy-only export written by the training supervisor).
    `train_finished` = both training stages ended; `main_evaluated` is set once the five 100k jobs are evaluated (or failed)."""
    d = root / 's3-eval'
    jobs = {j['name']: j for j in all_jobs(cfg)}
    main_names = [j['name'] for j in train_jobs(cfg)]
    status.update('S4', state='running', started=now(), expected=list(jobs))
    evaluated, failed = [], []
    while True:
        finished_before_scan = train_finished.is_set()
        for name, job in jobs.items():
            marker = root / 's4-marker' / name
            policy = root / 'train' / name / 'policy.pt'
            if name in evaluated or name in failed:
                continue
            if stage_done(marker):
                evaluated.append(name)
                continue
            if (root / 'train' / name / 'DONE').exists() and policy.exists():
                with FINAL_LOCK:
                    FINAL_BUSY['n'] += 1
                try:
                    summary = sp.run_eval_arms(cfg, {name: trained_arm(cfg, job, policy)}, d, pool, status, 'S4', cfg.eval_timeout_hours * 3600)
                    mark_done(marker, policy=str(policy), policy_sha256=sp.sha256_file(policy), eval=summary[name])
                    evaluated.append(name)
                except BaseException as exc:  # noqa: BLE001 - one failed arm must not stop the others
                    failed.append(name)
                    mark_failed(marker, repr(exc))
                    log('S4 arm', name, 'FAILED:', repr(exc))
                finally:
                    with FINAL_LOCK:
                        FINAL_BUSY['n'] -= 1
                status.update('S4', evaluated=evaluated, failed=failed)
        if all(n in evaluated or n in failed for n in main_names):
            main_evaluated.set()
        if finished_before_scan:
            break
        time.sleep(30)
    main_evaluated.set()
    missing = [n for n in jobs if n not in evaluated]
    if missing:
        raise RuntimeError('S4: trained-policy evaluations missing: %s' % missing)
    status.update('S4', state='done', finished=now(), evaluated=evaluated)


def find_step_checkpoints(job_dir):
    """{step: newest complete step-XXXXXXX.pt across attempts} (save_training renames a finished *.tmp, so a match is complete)."""
    found = {}
    for path in Path(job_dir).glob('a*/step-*.pt'):
        m = re.match(r'^step-(\d+)\.pt$', path.name)
        if m:
            step = int(m.group(1))
            if step not in found or path.stat().st_mtime > found[step].stat().st_mtime:
                found[step] = path
    return found


def s6_curves(cfg, root, status, pool, train_finished):
    """Diagnostic learning curves: intermediate checkpoints, one batch of 100 episodes at a time, never while a final-policy
    evaluation is pending. The end-of-budget checkpoint is evaluated by S4 and reused for the curve."""
    d = root / 's6-curves'
    pol_dir = root / 'curve-policies'
    d.mkdir(parents=True, exist_ok=True)
    pol_dir.mkdir(parents=True, exist_ok=True)
    jobs = {j['name']: j for j in all_jobs(cfg)}
    status.update('S6', state='running', started=now())
    evaluated, failed = [], []
    while True:
        finished_before_scan = train_finished.is_set()
        todo = []
        for name, job in jobs.items():
            steps = pa.curve_steps(name)
            found = find_step_checkpoints(root / 'train' / name)
            for step in steps[:-1]:                      # the last step is the final policy (S4)
                arm = pa.curve_arm(name, step)
                if step in found and arm not in evaluated and arm not in failed and not stage_done(d / arm):
                    todo.append((step, name, arm, found[step]))
                elif stage_done(d / arm) and arm not in evaluated:
                    evaluated.append(arm)
        if todo and FINAL_BUSY['n'] == 0:
            step, name, arm, src = sorted(todo)[0]
            try:
                policy = pol_dir / (arm + '.pt')
                if not policy.exists():
                    sp.export_policy(src, policy)
                summary = sp.run_eval_arms(cfg, {arm: trained_arm(cfg, jobs[name], policy)}, d, pool, status, 'S6', cfg.eval_timeout_hours * 3600)
                mark_done(d / arm, checkpoint=str(src), eval=summary[arm])
                evaluated.append(arm)
            except BaseException as exc:  # noqa: BLE001 - diagnostics must never stop anything else
                failed.append(arm)
                mark_failed(d / arm, repr(exc))
                log('S6 arm', arm, 'FAILED:', repr(exc))
            try:
                (policy).unlink()                         # the exported policy is only needed for the evaluation (re-exportable)
            except OSError:
                pass
            status.update('S6', evaluated=len(evaluated), failed=failed, last=arm)
            continue
        if finished_before_scan and not todo:
            break
        time.sleep(30 if not todo else 10)
    status.update('S6', state='done', finished=now(), evaluated=len(evaluated), failed=failed)


def analysis_ph3(cfg, root, status):
    status.update('S5a', state='running', started=now())
    report = Path(cfg.ph3_report)
    report.parent.mkdir(parents=True, exist_ok=True)

    def draft(points):
        report.write_text(pa.build_ph3_report(points, final=False))
        status.update('S5a', draft_written=now())
    points, result = pa.analyze_ph3(cfg.ph3_dir, cfg.eval_seeds, cfg.baseline_dir, on_points=draft)
    report.write_text(pa.build_ph3_report(points, result=result, final=True))
    status.update('S5a', state='done', finished=now(), d60=result.get('d60'))


def analysis_ph4(cfg, root, status, tag='S5b'):
    """tag S5b = interim (100k runs; the long runs may be missing), S5c = final. Both write the same report path."""
    status.update(tag, state='running', started=now())
    report = Path(cfg.ph4_report)
    report.parent.mkdir(parents=True, exist_ok=True)
    training = pa.training_info(root, [j['name'] for j in all_jobs(cfg)])

    def draft(points):
        report.write_text(pa.build_ph4_report(points, final=False, training=training))
        status.update(tag, draft_written=now())
    points, result = pa.analyze_ph4(cfg.ph3_dir, root, cfg.eval_seeds, on_points=draft)
    text = pa.build_ph4_report(points, result=result, final=True, training=training)
    report.write_text(text)
    if tag == 'S5b':   # keep the interim report (100k part) next to the final one that will overwrite the main path
        report.with_name(report.stem + '-interim' + report.suffix).write_text(text)
    status.update(tag, state='done', finished=now(), d62=result.get('d62'))


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def validate(cfg):
    lo, hi = EVAL_SEED_RANGE
    if not cfg.eval_seeds or min(cfg.eval_seeds) < lo or max(cfg.eval_seeds) >= hi:
        raise SystemExit('eval seeds must stay inside the D62 registration %d-%d' % (lo, hi - 1))
    if cfg.max_workers > 64:
        raise SystemExit('--max-workers must be <= 64')
    if cfg.train_steps % cfg.save_interval or cfg.long_steps % cfg.long_save_interval:
        raise SystemExit('--train-steps/--long-steps must be multiples of their save intervals')


def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument('--output-root', default=WS + '/results/ph4-train')
    p.add_argument('--ph3-dir', default=WS + '/results/ph3-obsmap')
    p.add_argument('--policy', default=sp.DEFAULT_POLICY)
    p.add_argument('--baseline-dir', default=BASELINE_DIR)
    p.add_argument('--device', default='cuda')
    p.add_argument('--gpus', default='0,1,2,3')
    p.add_argument('--max-workers', type=int, default=47, help='shared slot pool: 7 training + evaluation workers (<= 40 by default)')
    p.add_argument('--eval-seeds', default='10000:10100')
    p.add_argument('--train-steps', type=int, default=100000)
    p.add_argument('--save-interval', type=int, default=20000)
    p.add_argument('--long-steps', type=int, default=LONG_STEPS, help='D64 long runs: budget must stay the same on every resume')
    p.add_argument('--long-save-interval', type=int, default=LONG_SAVE_INTERVAL)
    p.add_argument('--random-steps', type=int, default=1000)
    p.add_argument('--batch', type=int, default=256)
    p.add_argument('--replay-capacity', type=int, default=100000)
    p.add_argument('--train-timeout-hours', type=float, default=24.0)
    p.add_argument('--long-timeout-hours', type=float, default=72.0)
    p.add_argument('--eval-timeout-hours', type=float, default=3.0, help='per evaluation batch (scaled x4 for PH3, x2 for the random controls)')
    p.add_argument('--max-attempts', type=int, default=4)
    p.add_argument('--min-disk-gb', type=int, default=MIN_DISK_GB)
    p.add_argument('--ph3-report', default=WS + '/doc/agent_logs/20260929-ph3-obsmap-report.md')
    p.add_argument('--ph4-report', default=WS + '/doc/agent_logs/20260929-ph4-1-report.md')
    p.add_argument('--only', default=None, help='comma-separated subset of S1,S1L,S2,S3,S4,S5,S6 (smoke/debug only)')
    return p


def main(argv=None):
    cfg = build_parser().parse_args(argv)
    cfg.eval_seeds = sp.parse_seed_spec(cfg.eval_seeds)
    cfg.gpus = [int(x) for x in cfg.gpus.split(',')]
    cfg.task_id = TASK_ID
    cfg.train_seeds = REGISTERED_TRAIN_SEEDS
    validate(cfg)
    pa.configure_schedule(cfg.train_steps, cfg.save_interval, cfg.long_steps, cfg.long_save_interval)
    root = Path(cfg.output_root)
    root.mkdir(parents=True, exist_ok=True)
    status = sp.SafeStatus(root / 'status.json')
    pool = sp.SlotPool(cfg.max_workers)
    wanted = set(cfg.only.split(',')) if cfg.only else None

    if wanted is None or 'S0' in wanted:
        if not stage_done(root / 's0-preflight'):
            s0_preflight(cfg, root, status)
        else:
            status.update('S0', state='done (resumed)')

    if wanted is None or 'S0' in wanted:
        ensure_ros_stacks(root, ros_ports())   # no-op when alive; after a restart/reboot the detached stacks must be back
    train_finished = threading.Event()      # both training stages ended
    training_ended = {'S1': threading.Event(), 'S1L': threading.Event()}
    main_evaluated = threading.Event()      # the five 100k policies are evaluated (or failed)
    names = ('S1', 'S1L', 'S2', 'S3', 'S4', 'S6')
    events = {k: threading.Event() for k in names}
    outcome = {}
    for k in ('S1', 'S1L'):
        if wanted is not None and k not in wanted:
            training_ended[k].set()

    def guarded(name, fn):
        try:
            if wanted is not None and name not in wanted:
                outcome[name] = 'not selected'
                return
            fn()
            outcome[name] = 'done'
        except BaseException as exc:  # noqa: BLE001 - a failing stage must surface in status, never kill sibling stages
            outcome[name] = 'failed'
            mark_failed(root / ('failed-' + name), repr(exc))
            status.update(name, state='failed', error=repr(exc)[:500], finished=now())
            log('STAGE', name, 'FAILED:', repr(exc))
        finally:
            if name in training_ended:
                training_ended[name].set()
                if all(e.is_set() for e in training_ended.values()):
                    train_finished.set()
            events[name].set()

    def stage_marker(name, marker, fn):
        def run():
            if stage_done(root / marker):
                status.update(name, state='done (resumed)')
            else:
                fn()
        return run

    def s4_run():
        try:
            s4_trained_eval(cfg, root, status, pool, train_finished, main_evaluated)
        finally:
            main_evaluated.set()

    plan = [('S1', lambda: s1_train(cfg, root, status, pool)), ('S1L', lambda: s1_long(cfg, root, status, pool)),
            ('S2', stage_marker('S2', 's2-ph3', lambda: s2_ph3(cfg, root, status, pool))),
            ('S3', stage_marker('S3', 's3-random', lambda: s3_random(cfg, root, status, pool))),
            ('S4', s4_run), ('S6', lambda: s6_curves(cfg, root, status, pool, train_finished))]
    if wanted is not None and 'S1' not in wanted and 'S1L' not in wanted:
        train_finished.set()
    threads = [threading.Thread(target=guarded, args=(n, fn), name=n) for n, fn in plan]
    for t in threads:
        t.start()

    do_analysis = wanted is None or 'S5' in wanted
    # PH3 analysis as soon as the PH3 evaluations are complete (independent of training)
    events['S2'].wait()
    if outcome.get('S2') == 'done' and do_analysis:
        try:
            analysis_ph3(cfg, root, status)
        except BaseException as exc:  # noqa: BLE001
            status.update('S5a', state='failed', error=repr(exc)[:500])
            log('S5a FAILED:', repr(exc))
    # interim PH4.1 report: the five 100k policies and the random controls are evaluated
    main_evaluated.wait()
    events['S3'].wait()
    if do_analysis:
        try:
            analysis_ph4(cfg, root, status, tag='S5b')
        except BaseException as exc:  # noqa: BLE001
            status.update('S5b', state='failed', error=repr(exc)[:500])
            log('S5b FAILED:', repr(exc))
    for t in threads:
        t.join()
    if do_analysis:
        try:
            analysis_ph4(cfg, root, status, tag='S5c')   # final: includes the long runs and the curves
        except BaseException as exc:  # noqa: BLE001
            status.update('S5c', state='failed', error=repr(exc)[:500])
            log('S5c FAILED:', repr(exc))
    log('PIPELINE DONE', json.dumps(outcome))


if __name__ == '__main__':
    main()
