"""CEIL-028 unattended pipeline (SAC ceiling probe; 20260929-ceil-spec.md S3/S6, criteria D57).

Run inside the mmhusky-node01 container (see doc/agent_logs/20260929-ceil-launch.sh):
  python3 -u ceil_pipeline.py --output-root /root/mm_husky_ws/results/ceil-028
Resumable: stages/arms write DONE (or FAILED); training jobs resume from their newest checkpoint with the
same --steps (protocol-compatible); finished evaluation episodes are reused. Status: <output-root>/status.json.

  S0 preflight     GPU/memory/disk/analytical sim/policy SHA/git; mean action from the R0-3c nominal data
  S1 E2 controls   policy-100k with --policy-override random / mean / slow-ee, seeds 10000-10099
  S2 E1 training   from scratch, budget 300000 steps, training seeds 11 and 22 (parallel), checkpoint every 50000
  S3 ckpt eval     every checkpoint as soon as it appears: policy-only export + 100 deterministic episodes
  S4 report        point estimates first (point.json + draft report), then CIs and the final report

Baseline policy-100k is NOT re-evaluated: its R0-3c nominal 100 episodes (identical to SCREEN-028's nominal arm,
100/100 trajectory hashes) are the D57 reference. Resource limits (enforced in code, shared pool): every process
(training or evaluation episode worker) holds one slot of --max-workers (<=64); a new batch starts only with
>=60 GiB MemAvailable and no new process starts below 40 GiB.
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
import ceil_analysis as ca  # noqa: E402
import policy_override as po  # noqa: E402
import screen_pipeline as sp  # noqa: E402
from followup_pipeline import (available_memory_gb, now, stage_done, mark_done, mark_failed, _disk_free_gb,  # noqa: E402
                               _gpu_status, _ensure_analytical_running)

WS = sp.WS
TASK_ID = 'CEIL-028'
REGISTERED_TRAIN_SEEDS = (11, 22)
EVAL_SEED_RANGE = (10000, 10100)  # 20000-20299, 9000-9199, 8000-8099 forbidden
BASELINE_DIR = WS + '/results/stage0-028-r03c/gain1.0_delay0'
STAGE_DIRS = {'S0': 's0-preflight', 'S1': 's1-e2-simple', 'S2': 's2-train', 'S3': 's3-ckpt-eval', 'S4': 's4-report'}
MIN_DISK_GB = 300
STEP_RE = re.compile(r'^step-(\d+)\.pt$')


def log(*args):
    print(now(), *args, flush=True)


def find_step_checkpoints(job_dir):
    """{step: newest complete step-XXXXXXX.pt across attempts}. save_training writes *.tmp then renames, so any
    file matching here is complete."""
    found = {}
    for path in Path(job_dir).glob('a*/step-*.pt'):
        m = STEP_RE.match(path.name)
        if m:
            step = int(m.group(1))
            if step not in found or path.stat().st_mtime > found[step].stat().st_mtime:
                found[step] = path
    return found


def train_jobs(cfg):
    return [dict(name='E1-s%d' % seed, task='simpleobstacle', seed=seed, flags={}, gpu=cfg.gpus[i % len(cfg.gpus)])
            for i, seed in enumerate(cfg.train_seeds)]


def e2_arms(cfg, mean_file):
    flags = {'random': dict(policy_override='random'), 'slow-ee': dict(policy_override='slow-ee'),
             'mean': dict(policy_override='mean', policy_override_mean_file=str(mean_file))}
    return {name: sp.eval_args(cfg, cfg.policy, 'simpleobstacle', f) for name, f in flags.items()}


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

def s0_preflight(cfg, root, status):
    d = root / STAGE_DIRS['S0']
    d.mkdir(parents=True, exist_ok=True)
    status.update('S0', state='running', started=now())
    mean = po.mean_action_from_trajectories(cfg.baseline_dir)
    (d / 'mean-action.json').write_text(json.dumps(mean, indent=2))
    base_rows = ca.load_baseline(cfg.baseline_dir)
    base = ca.sa.describe_arm(base_rows, cfg.eval_seeds)
    m = dict(checked=now(), available_memory_gb=available_memory_gb(), disk_free_gb=_disk_free_gb(root),
             gpu=_gpu_status(), analytical_running=_ensure_analytical_running(), git=sp._git_status(),
             policy_sha256=sp.p0_runner.sha(cfg.policy), baseline_dir=cfg.baseline_dir, baseline=base,
             mean_action=mean, eval_seeds=[cfg.eval_seeds[0], cfg.eval_seeds[-1]], train_seeds=list(cfg.train_seeds),
             max_workers=cfg.max_workers, gpus=cfg.gpus, expected_checkpoint_steps=ca.expected_steps(cfg.train_steps, cfg.save_interval),
             train_commands={j['name']: sp.train_command(cfg, j, root / 'train' / j['name'] / 'a0') for j in train_jobs(cfg)},
             args={k: v for k, v in vars(cfg).items() if k != 'eval_seeds'})
    (d / 'manifest.json').write_text(json.dumps(m, indent=2, default=str))
    if m['available_memory_gb'] < sp.MIN_FREE_START_GB:
        raise SystemExit('S0: available memory %.1f GiB < %d GiB' % (m['available_memory_gb'], sp.MIN_FREE_START_GB))
    if m['disk_free_gb'] < cfg.min_disk_gb:
        raise SystemExit('S0: free disk %.0f GiB < %d GiB' % (m['disk_free_gb'], cfg.min_disk_gb))
    if not m['analytical_running']:
        raise SystemExit('S0: analytical simulator not running')
    if base is None:
        raise SystemExit('S0: baseline episodes missing for the evaluation seeds in %s' % cfg.baseline_dir)
    mark_done(d, **{k: m[k] for k in ('checked', 'policy_sha256', 'mean_action')})
    status.update('S0', state='done', finished=now(), mean_action=mean['mean'], baseline_sr=base['success_rate'])


def s1_e2(cfg, root, status, pool):
    d = root / STAGE_DIRS['S1']
    status.update('S1', state='running', started=now())
    mean_file = root / STAGE_DIRS['S0'] / 'mean-action.json'
    summary = sp.run_eval_arms(cfg, e2_arms(cfg, mean_file), d, pool, status, 'S1', 3600 * 3)
    points = {a: ca.sa.describe_arm(ca.sa.arm_rows(d, a), cfg.eval_seeds) for a in ca.SIMPLE_ARMS}
    (d / 'result.json').write_text(json.dumps(dict(eval=summary, points=points), indent=2, sort_keys=True))
    mark_done(d, eval=summary)
    status.update('S1', state='done', finished=now(), sr={a: (p or {}).get('success_rate') for a, p in points.items()})


def s2_train(cfg, root, status, pool):
    d = root / STAGE_DIRS['S2']
    d.mkdir(parents=True, exist_ok=True)
    if not (d / 'started.json').exists():
        (d / 'started.json').write_text(json.dumps(dict(started=now(), epoch=time.time())))
    status.update('S2', state='running', started=now(), train_steps=cfg.train_steps)
    outcome = sp.run_training_stage(cfg, train_jobs(cfg), root, pool, status, 'S2')
    (d / 'result.json').write_text(json.dumps(dict(jobs=outcome), indent=2))
    if not any(outcome.values()):
        raise RuntimeError('S2: every training job failed')
    mark_done(d, jobs=outcome)
    status.update('S2', state='done' if all(outcome.values()) else 'done (partial: %s)' % [k for k, v in outcome.items() if not v],
                  finished=now())


def s3_ckpt_eval(cfg, root, status, pool, train_finished):
    d = root / STAGE_DIRS['S3']
    d.mkdir(parents=True, exist_ok=True)
    pol_dir = root / 'ckpt-policies'
    pol_dir.mkdir(parents=True, exist_ok=True)
    steps = ca.expected_steps(cfg.train_steps, cfg.save_interval)
    status.update('S3', state='running', started=now(), expected=len(steps) * len(cfg.train_seeds))
    evaluated, failed = [], []
    while True:
        finished_before_scan = train_finished.is_set()  # read first so a checkpoint written just before the end is not missed
        todo = []
        for seed in cfg.train_seeds:
            found = find_step_checkpoints(root / 'train' / ('E1-s%d' % seed))
            for step in steps:
                arm = ca.ckpt_arm(seed, step)
                if step in found and not stage_done(d / arm) and arm not in failed:
                    todo.append((step, seed, arm, found[step]))
        if todo:
            step, seed, arm, src = sorted(todo)[0]
            try:
                policy = pol_dir / (arm + '.pt')
                if not policy.exists():
                    sp.export_policy(src, policy)
                arms = {arm: sp.eval_args(cfg, str(policy), 'simpleobstacle', {})}
                summary = sp.run_eval_arms(cfg, arms, d, pool, status, 'S3', cfg.eval_timeout_hours * 3600)
                mark_done(d / arm, checkpoint=str(src), policy=str(policy), policy_sha256=sp.sha256_file(policy), eval=summary[arm])
                evaluated.append(arm)
            except BaseException as exc:  # noqa: BLE001 - one bad arm must not stop the other checkpoints
                failed.append(arm)
                mark_failed(d / arm, repr(exc))
                log('S3 arm', arm, 'FAILED:', repr(exc))
            status.update('S3', evaluated=evaluated, failed=failed, last=arm)
            continue
        if finished_before_scan:
            break
        time.sleep(30)
    missing = [ca.ckpt_arm(s, st_) for s in cfg.train_seeds for st_ in steps if not stage_done(d / ca.ckpt_arm(s, st_))]
    (d / 'result.json').write_text(json.dumps(dict(evaluated=evaluated, failed=failed, missing=missing), indent=2))
    if missing:
        raise RuntimeError('S3: %d checkpoint evaluations missing: %s' % (len(missing), missing[:4]))
    mark_done(d, evaluated=evaluated)
    status.update('S3', state='done', finished=now())


def s4_report(cfg, root, status):
    status.update('S4', state='running', started=now())
    report = Path(cfg.report_path)
    report.parent.mkdir(parents=True, exist_ok=True)

    def draft(points):  # point estimates are on disk (point.json) and in a draft report before any CI is computed
        report.write_text(ca.build_report(root, cfg, points=points, final=False))
        status.update('S4', draft_written=now())

    points, result = ca.analyze(root, cfg, on_points=draft)
    report.write_text(ca.build_report(root, cfg, points=points, result=result, final=True))
    v = ca.verdict(result)
    mark_done(root / STAGE_DIRS['S4'], verdict=v)
    status.update('S4', state='done', finished=now(), verdict=v)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def parse_seed_spec(spec):
    return sp.parse_seed_spec(spec)


def validate_seeds(cfg):
    lo, hi = EVAL_SEED_RANGE
    if not cfg.eval_seeds or min(cfg.eval_seeds) < lo or max(cfg.eval_seeds) >= hi:
        raise SystemExit('eval seeds must stay inside the D57 registration %d-%d' % (lo, hi - 1))
    if not cfg.train_seeds or any(s not in REGISTERED_TRAIN_SEEDS for s in cfg.train_seeds):
        raise SystemExit('training seeds must be a subset of %s' % (REGISTERED_TRAIN_SEEDS,))
    if cfg.max_workers > 64:
        raise SystemExit('--max-workers must be <= 64')
    if cfg.train_steps % cfg.save_interval:
        raise SystemExit('--train-steps must be a multiple of --save-interval (the budget-end checkpoint must be saved)')


def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument('--output-root', default=WS + '/results/ceil-028')
    p.add_argument('--policy', default=sp.DEFAULT_POLICY)
    p.add_argument('--baseline-dir', default=BASELINE_DIR)
    p.add_argument('--device', default='cuda')
    p.add_argument('--gpus', default='0,1,2,3')
    p.add_argument('--max-workers', type=int, default=64)
    p.add_argument('--eval-seeds', default='10000:10100')
    p.add_argument('--train-seeds', default='11,22')
    p.add_argument('--train-steps', type=int, default=300000)
    p.add_argument('--save-interval', type=int, default=50000)
    p.add_argument('--random-steps', type=int, default=1000)
    p.add_argument('--batch', type=int, default=256)
    p.add_argument('--replay-capacity', type=int, default=100000)
    p.add_argument('--train-timeout-hours', type=float, default=20.0)
    p.add_argument('--eval-timeout-hours', type=float, default=1.0, help='per checkpoint evaluation')
    p.add_argument('--max-attempts', type=int, default=4, help='launch attempts per training job (resume from newest checkpoint)')
    p.add_argument('--min-disk-gb', type=int, default=MIN_DISK_GB)
    p.add_argument('--report-path', default=WS + '/doc/agent_logs/20260929-ceil-report.md')
    p.add_argument('--only', default=None, help='comma-separated subset of stages (smoke/debug only)')
    return p


def main(argv=None):
    cfg = build_parser().parse_args(argv)
    cfg.eval_seeds = parse_seed_spec(cfg.eval_seeds)
    cfg.train_seeds = tuple(parse_seed_spec(cfg.train_seeds))
    cfg.gpus = [int(x) for x in cfg.gpus.split(',')]
    cfg.task_id = TASK_ID
    validate_seeds(cfg)
    root = Path(cfg.output_root)
    root.mkdir(parents=True, exist_ok=True)
    status = sp.SafeStatus(root / 'status.json')
    pool = sp.SlotPool(cfg.max_workers)
    wanted = set(cfg.only.split(',')) if cfg.only else None

    if wanted is None or 'S0' in wanted:
        if not stage_done(root / STAGE_DIRS['S0']):
            s0_preflight(cfg, root, status)
        else:
            status.update('S0', state='done (resumed)')

    train_finished = threading.Event()
    if wanted is not None and 'S2' not in wanted:
        train_finished.set()  # debug runs that evaluate existing checkpoints only
    fns = {'S1': lambda: s1_e2(cfg, root, status, pool), 'S2': lambda: s2_train(cfg, root, status, pool),
           'S3': lambda: s3_ckpt_eval(cfg, root, status, pool, train_finished), 'S4': lambda: s4_report(cfg, root, status)}
    deps = {'S1': [], 'S2': [], 'S3': [], 'S4': ['S1', 'S2', 'S3']}
    order = ['S1', 'S2', 'S3', 'S4']
    events = {s: threading.Event() for s in order}
    outcome = {}

    def run_stage(name):
        try:
            if wanted is not None and name not in wanted:
                outcome[name] = 'not selected'
                return
            for dep in deps[name]:
                events[dep].wait()
            if name != 'S4' and stage_done(root / STAGE_DIRS[name]):  # the report is cheap and always regenerated
                outcome[name] = 'done'
                status.update(name, state='done (resumed)')
                return
            fns[name]()
            outcome[name] = 'done'
        except BaseException as exc:  # noqa: BLE001 - every failure must surface in status, never kill sibling stages
            outcome[name] = 'failed'
            mark_failed(root / STAGE_DIRS[name], repr(exc))
            status.update(name, state='failed', error=repr(exc)[:500], finished=now())
            log('STAGE', name, 'FAILED:', repr(exc))
        finally:
            if name == 'S2':
                train_finished.set()
            events[name].set()

    threads = [threading.Thread(target=run_stage, args=(s,), name=s, daemon=False) for s in order]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    log('PIPELINE DONE', json.dumps(outcome))


if __name__ == '__main__':
    main()
