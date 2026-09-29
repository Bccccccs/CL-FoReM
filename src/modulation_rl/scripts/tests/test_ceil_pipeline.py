"""CEIL-028: pipeline pieces, D57 decision logic on synthetic episodes, report, resume/checkpoint plumbing."""
import json
import threading
import zlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import ceil_analysis as ca
import ceil_pipeline as cp
import screen_pipeline as sp

SEEDS = list(range(10000, 10100))


def make_cfg(tmp_path, **over):
    base = dict(eval_seeds=SEEDS, train_seeds=(11, 22), train_steps=300000, save_interval=50000, baseline_dir=str(tmp_path / 'baseline'),
                policy='policy.pt', device='cpu', gpus=[0, 1, 2, 3], max_workers=64, batch=256, random_steps=1000,
                replay_capacity=100000, train_timeout_hours=20.0, eval_timeout_hours=1.0, max_attempts=4, min_disk_gb=1,
                report_path=str(tmp_path / 'report.md'), task_id='CEIL-028')
    base.update(over)
    return SimpleNamespace(**base)


def write_arm(directory, n_success, name=None):
    """First n_success seeds succeed, the rest fail (collision_limit); deterministic layout."""
    d = Path(directory) if name is None else Path(directory) / name
    d.mkdir(parents=True, exist_ok=True)
    with (d / 'episodes.jsonl').open('w') as f:
        for i, s in enumerate(SEEDS):
            ok = i < n_success
            f.write(json.dumps(dict(seed=s, success=ok, perfect_success=ok, primary_reason='success' if ok else 'collision_limit',
                                    exception=None, collision_count=0 if ok else 3, ik_count=0, steps=100)) + '\n')


def write_shifted_arm(directory, name, n_success, offset):
    """n_success successes starting at seed index `offset` (wrapping), to vary the pairing with the baseline."""
    d = Path(directory) / name
    d.mkdir(parents=True, exist_ok=True)
    ok_idx = {(offset + i) % 100 for i in range(n_success)}
    with (d / 'episodes.jsonl').open('w') as f:
        for i, s in enumerate(SEEDS):
            ok = i in ok_idx
            f.write(json.dumps(dict(seed=s, success=ok, perfect_success=ok, primary_reason='success' if ok else 'ik_limit',
                                    exception=None, collision_count=0, ik_count=0 if ok else 5, steps=90)) + '\n')


def build_results(tmp_path, base, rand, mean, slow, final11, final22, mid=None):
    root = tmp_path / 'root'
    write_arm(tmp_path, base, name='baseline')
    write_shifted_arm(root / 's1-e2-simple', 'random', rand, 0)
    write_shifted_arm(root / 's1-e2-simple', 'mean', mean, 0)
    write_shifted_arm(root / 's1-e2-simple', 'slow-ee', slow, 0)
    for step in range(50000, 300001, 50000):
        for seed, fin in ((11, final11), (22, final22)):
            n = fin if step == 300000 else (mid if mid is not None else 40)
            write_shifted_arm(root / 's3-ckpt-eval', ca.ckpt_arm(seed, step), n, seed)
    return root


# ---- registration / plumbing ------------------------------------------------------------------

def test_registered_seeds_and_limits_are_enforced(tmp_path):
    ok = make_cfg(tmp_path)
    cp.validate_seeds(ok)
    for bad in (dict(eval_seeds=list(range(10000, 10101))), dict(eval_seeds=[20000]), dict(eval_seeds=[8000]),
                dict(eval_seeds=[9000]), dict(train_seeds=(33,)), dict(train_seeds=()), dict(max_workers=65),
                dict(train_steps=310000)):
        with pytest.raises(SystemExit):
            cp.validate_seeds(make_cfg(tmp_path, **bad))
    parsed = cp.build_parser().parse_args([])
    assert (parsed.train_steps, parsed.save_interval, parsed.train_seeds, parsed.eval_seeds) == (300000, 50000, '11,22', '10000:10100')
    assert parsed.train_timeout_hours == 20 and parsed.eval_timeout_hours == 1 and parsed.max_workers == 64


def test_training_command_is_from_scratch_with_the_300k_budget_and_policy100k_hyperparameters(tmp_path):
    cfg = make_cfg(tmp_path)
    jobs = cp.train_jobs(cfg)
    assert [j['name'] for j in jobs] == ['E1-s11', 'E1-s22'] and [j['gpu'] for j in jobs] == [0, 1]
    cmd = sp.train_command(cfg, jobs[0], tmp_path / 'out')
    val = lambda flag: cmd[cmd.index(flag) + 1]
    assert (val('--steps'), val('--batch'), val('--random-steps'), val('--replay-capacity'), val('--save-interval')) == \
        ('300000', '256', '1000', '100000', '50000')
    assert (val('--ik-mode'), val('--ik-iterations'), val('--eval-interval'), val('--seed'), val('--task')) == \
        ('fixed', '100', '0', '11', 'simpleobstacle')
    assert '--replay-compact-maps' in cmd and '--resume' not in cmd
    assert not any(a.startswith(('--obs-', '--map-', '--dyn-', '--latency-', '--policy-override')) for a in cmd)
    resumed = sp.train_command(cfg, jobs[1], tmp_path / 'out2', resume=tmp_path / 'step.pt')
    assert resumed[resumed.index('--steps') + 1] == '300000' and resumed[resumed.index('--resume') + 1] == str(tmp_path / 'step.pt')


def test_learning_rate_schedule_follows_the_steps_budget():
    """num_steps=--steps: with a 300k budget the lr at 100k steps is still ~2.2e-5 (policy-100k had reached 1e-6)."""
    from test_sac_updates import spaces
    from sac import SAC
    obs, act = spaces()
    cfg = dict(device='cpu', gamma=.99, tau=.001, initial_alpha=1.0, model={'custom_model_config': {'post_fcnet_hiddens': [256, 256]}})
    long_run, short_run = SAC(obs, act, 1, cfg, 300000), SAC(obs, act, 1, cfg, 100000)
    lr = lambda a, step: a.scheduler_policy_optim.lr_lambdas[0](step) * a.lr_start
    assert lr(short_run, 100000) == pytest.approx(1e-6) and lr(long_run, 100000) == pytest.approx(1e-4 * 1e-2 ** (1 / 3))
    assert lr(long_run, 300000) == pytest.approx(1e-6)


def test_find_step_checkpoints_picks_newest_across_attempts_and_ignores_others(tmp_path):
    import os
    d = tmp_path / 'job'
    for attempt, name in [('a0', 'step-0050000.pt'), ('a0', 'step-0100000.pt'), ('a1', 'step-0100000.pt'), ('a1', 'latest.pt'),
                          ('a1', 'step-0150000.pt.tmp'), ('a1', 'validation-0150000.pt')]:
        (d / attempt).mkdir(parents=True, exist_ok=True)
        (d / attempt / name).write_bytes(b'x')
    os.utime(d / 'a0' / 'step-0100000.pt', (1, 1))
    found = cp.find_step_checkpoints(d)
    assert sorted(found) == [50000, 100000] and found[100000].parent.name == 'a1'


def test_e2_arms_use_policy100k_and_the_computed_mean(tmp_path):
    cfg = make_cfg(tmp_path)
    arms = cp.e2_arms(cfg, tmp_path / 'mean.json')
    assert set(arms) == {'random', 'mean', 'slow-ee'}
    for name, a in arms.items():
        assert a.checkpoint == 'policy.pt' and a.policy_mode == 'deterministic' and a.ik_mode == 'fixed' and a.ik_iterations == 100
        assert a.policy_override == name
    assert arms['mean'].policy_override_mean_file == str(tmp_path / 'mean.json')
    assert not hasattr(arms['random'], 'policy_override_mean_file')


def test_worker_env_carries_the_ceil_task_id(tmp_path):
    assert sp.worker_env(make_cfg(tmp_path), 10003)['P0_TASK_ID'] == 'CEIL-028'
    assert sp.worker_env(SimpleNamespace(gpus=[0]), 1)['P0_TASK_ID'] == 'SCREEN-028'   # unchanged default


# ---- D57 decision logic -----------------------------------------------------------------------

def points_for(tmp_path, **kw):
    root = build_results(tmp_path, **kw)
    cfg = make_cfg(tmp_path)
    return root, cfg, ca.collect_points(root, cfg)


def test_c_policy_threshold_is_inclusive_and_uses_the_better_simple_policy(tmp_path):
    _, _, p = points_for(tmp_path, base=70, rand=10, mean=40, slow=60, final11=70, final22=70)
    assert p['c_policy']['best_simple'] == pytest.approx(.40) and p['c_policy']['diff'] == pytest.approx(.30)
    assert p['c_policy']['passes'] is True                                    # exactly 0.30 counts (>=)
    assert p['simple']['slow-ee']['success_rate'] == pytest.approx(.60)       # reported, never a criterion


def test_c_policy_fails_below_threshold(tmp_path):
    _, _, p = points_for(tmp_path, base=70, rand=10, mean=41, slow=0, final11=70, final22=70)
    assert p['c_policy']['diff'] == pytest.approx(.29) and p['c_policy']['passes'] is False


def test_c_learn_point_estimate_and_ci_gate_and_per_seed_extras(tmp_path):
    root, cfg, p = points_for(tmp_path, base=70, rand=0, mean=0, slow=0, final11=85, final22=85)
    cl = p['c_learn']
    assert cl['mean_final_sr'] == pytest.approx(.85) and cl['diff_point'] == pytest.approx(.15) and cl['point_passes'] is True
    r = ca.add_cis(root, cfg, p, n_boot=2000)['c_learn']
    assert r['ci95'][0] > 0 and r['passes'] is True and r['both_seeds_each_ge_threshold'] is True
    assert set(r['per_seed']) == {'11', '22'} and all('ci95' in v for v in r['per_seed'].values())


def test_c_learn_needs_the_point_threshold_even_when_the_ci_is_positive(tmp_path):
    root, cfg, p = points_for(tmp_path, base=70, rand=0, mean=0, slow=0, final11=79, final22=79)
    assert p['c_learn']['point_passes'] is False                              # +0.09 < 0.10
    assert ca.add_cis(root, cfg, p, n_boot=1000)['c_learn']['passes'] is False


def test_c_learn_needs_a_positive_ci_lower_bound(tmp_path):
    # +0.10 on average (20 paired episodes, random successes): the point threshold is met, the CI reaches below 0
    root, small = tmp_path / 'root', SEEDS[:20]
    rng = np.random.default_rng(3)
    def write(directory, name, ok):
        d = Path(directory) / name
        d.mkdir(parents=True, exist_ok=True)
        with (d / 'episodes.jsonl').open('w') as f:
            for s_ in small:
                f.write(json.dumps(dict(seed=s_, success=bool(ok[s_ - 10000]), perfect_success=False, primary_reason='x', exception=None,
                                        collision_count=0, ik_count=0, steps=10)) + '\n')
    base = np.zeros(20, dtype=bool); base[rng.permutation(20)[:10]] = True
    write(tmp_path, 'baseline', base)
    for seed in (11, 22):
        for step in range(50000, 300001, 50000):
            trained = np.zeros(20, dtype=bool); trained[rng.permutation(20)[:12]] = True
            write(root / 's3-ckpt-eval', ca.ckpt_arm(seed, step), trained)
    cfg = make_cfg(tmp_path, eval_seeds=small)
    for a in ca.SIMPLE_ARMS:
        write(root / 's1-e2-simple', a, np.zeros(20, dtype=bool))
    p = ca.collect_points(root, cfg)
    assert p['c_learn']['diff_point'] == pytest.approx(.10) and p['c_learn']['point_passes'] is True
    r = ca.add_cis(root, cfg, p, n_boot=4000)['c_learn']
    assert r['ci95'][0] < 0 and r['passes'] is False


def test_c_learn_pools_the_two_seeds_and_reports_the_stricter_reading(tmp_path):
    root, cfg, p = points_for(tmp_path, base=70, rand=0, mean=0, slow=0, final11=95, final22=75)
    cl = ca.add_cis(root, cfg, p, n_boot=1000)['c_learn']
    assert cl['mean_final_sr'] == pytest.approx(.85) and cl['point_passes'] is True     # pooled reading passes ...
    assert cl['both_seeds_each_ge_threshold'] is False                                  # ... the stricter one would not; both are shown


@pytest.mark.parametrize('learn,policy,expected', [(True, True, 'SAC 的决策重要，且还有学习空间'), (False, True, 'SAC 已接近该任务的天花板'),
                                                    (False, False, '任务对策略不敏感'), (True, False, '结果矛盾，需检查实验')])
def test_verdict_maps_to_the_preregistered_table(learn, policy, expected):
    v = ca.verdict(dict(c_learn=dict(passes=learn), c_policy=dict(passes=policy)))
    assert v[0] is learn and v[1] is policy and v[2] == expected
    assert ca.verdict(dict(c_learn=None, c_policy=dict(passes=True))) is None
    assert ca.verdict(dict(c_learn=dict(point_passes=True), c_policy=dict(passes=True))) is None   # no CI yet -> no verdict


def test_missing_data_is_reported_as_unavailable_not_imputed(tmp_path):
    root, cfg, _ = points_for(tmp_path, base=70, rand=0, mean=0, slow=0, final11=85, final22=85)
    import shutil
    shutil.rmtree(root / 's3-ckpt-eval' / ca.ckpt_arm(22, 300000))
    shutil.rmtree(root / 's1-e2-simple' / 'mean')
    p = ca.collect_points(root, cfg)
    assert p['c_learn'] is None and p['c_policy'] is None and p['simple']['mean'] is None
    text = ca.build_report(root, cfg, points=p, final=True)
    assert '数据不全' in text and '不给出映射' in text


def test_point_estimates_reach_disk_before_any_ci_is_computed(tmp_path, monkeypatch):
    root, cfg, _ = points_for(tmp_path, base=70, rand=0, mean=0, slow=0, final11=85, final22=85)
    seen = []
    monkeypatch.setattr(ca, 'add_cis', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('boom during CI')))
    with pytest.raises(RuntimeError):
        ca.analyze(root, cfg, on_points=lambda pts: seen.append(bool((root / 's4-report' / 'point.json').exists())))
    assert seen == [True]
    assert json.loads((root / 's4-report' / 'point.json').read_text())['c_learn']['diff_point'] == pytest.approx(.15)
    assert not (root / 's4-report' / 'result.json').exists()


def test_report_draft_then_final(tmp_path):
    root, cfg, _ = points_for(tmp_path, base=70, rand=10, mean=20, slow=60, final11=85, final22=85)
    points, result = ca.analyze(root, cfg)
    draft = ca.build_report(root, cfg, points=points, final=False)
    final = ca.build_report(root, cfg, points=points, result=result, final=True)
    assert '点估计草稿' in draft and 'CI 待计算' in draft and '判据结论尚未齐备' in draft
    assert '终稿' in final and '通过' in final and 'SAC 的决策重要，且还有学习空间' in final
    for text in (draft, final):
        for needle in ('C-learn', 'C-policy', 'slow-ee', '学习曲线', '训练耗时', '300k'):
            assert needle in text
    assert '20260929-ceil-spec.md' in final and '最终方向由用户确认' in final


# ---- S3 checkpoint evaluation loop ----------------------------------------------------------------

def fake_train_dirs(root, steps_by_seed):
    for seed, steps in steps_by_seed.items():
        for step in steps:
            f = Path(root) / 'train' / ('E1-s%d' % seed) / 'a0' / ('step-%07d.pt' % step)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b'x')


def patch_eval(monkeypatch, calls):
    monkeypatch.setattr(sp, 'export_policy', lambda src, dst: Path(dst).write_bytes(b'p'))
    def fake_eval(cfg, arms, stage_dir, pool, status, key, timeout_s, seeds=None):
        (name,) = arms
        calls.append((name, timeout_s, arms[name].checkpoint))
        return {name: dict(episodes=100, exceptions=0)}
    monkeypatch.setattr(sp, 'run_eval_arms', fake_eval)


def test_s3_evaluates_every_expected_checkpoint_oldest_first_with_the_hour_limit(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path, train_steps=100000)
    fake_train_dirs(tmp_path, {11: [50000, 100000], 22: [50000, 100000]})
    calls = []
    patch_eval(monkeypatch, calls)
    finished = threading.Event(); finished.set()
    status = sp.SafeStatus(tmp_path / 'status.json')
    cp.s3_ckpt_eval(cfg, tmp_path, status, sp.SlotPool(4), finished)
    assert [c[0] for c in calls] == ['E1-s11-step0050000', 'E1-s22-step0050000', 'E1-s11-step0100000', 'E1-s22-step0100000']
    assert all(c[1] == 3600 for c in calls) and all(c[2].endswith('.pt') and 'ckpt-policies' in c[2] for c in calls)
    assert (tmp_path / 's3-ckpt-eval' / 'DONE').exists()
    calls.clear()
    cp.s3_ckpt_eval(cfg, tmp_path, status, sp.SlotPool(4), finished)      # resume: nothing is evaluated twice
    assert calls == []


def test_s3_picks_up_checkpoints_that_appear_while_training_runs_and_reports_gaps(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path, train_steps=100000)
    fake_train_dirs(tmp_path, {11: [50000], 22: [50000]})
    calls = []
    patch_eval(monkeypatch, calls)
    monkeypatch.setattr(cp.time, 'sleep', lambda s: None)
    finished = threading.Event()
    real_eval = sp.run_eval_arms
    def eval_then_grow(*a, **k):
        out = real_eval(*a, **k)
        if len(calls) == 2:                       # training keeps going: seed 11's 100k checkpoint appears, seed 22 never gets one
            fake_train_dirs(tmp_path, {11: [100000]})
            finished.set()
        return out
    monkeypatch.setattr(sp, 'run_eval_arms', eval_then_grow)
    status = sp.SafeStatus(tmp_path / 'status.json')
    with pytest.raises(RuntimeError, match='missing'):
        cp.s3_ckpt_eval(cfg, tmp_path, status, sp.SlotPool(4), finished)
    assert [c[0] for c in calls] == ['E1-s11-step0050000', 'E1-s22-step0050000', 'E1-s11-step0100000']
    assert json.loads((tmp_path / 's3-ckpt-eval' / 'result.json').read_text())['missing'] == ['E1-s22-step0100000']


def test_s3_marks_a_failed_arm_and_continues(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path, train_steps=50000)
    fake_train_dirs(tmp_path, {11: [50000], 22: [50000]})
    calls = []
    patch_eval(monkeypatch, calls)
    good = sp.run_eval_arms
    def flaky(cfg, arms, *a, **k):
        if 'E1-s11-step0050000' in arms:
            raise TimeoutError('eval timeout')
        return good(cfg, arms, *a, **k)
    monkeypatch.setattr(sp, 'run_eval_arms', flaky)
    finished = threading.Event(); finished.set()
    with pytest.raises(RuntimeError):
        cp.s3_ckpt_eval(cfg, tmp_path, sp.SafeStatus(tmp_path / 'status.json'), sp.SlotPool(4), finished)
    assert (tmp_path / 's3-ckpt-eval' / 'E1-s11-step0050000' / 'FAILED').exists()
    assert (tmp_path / 's3-ckpt-eval' / 'E1-s22-step0050000' / 'DONE').exists()
