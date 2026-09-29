"""PH3-OBSMAP diagnostics (D60) + PH4.1 (D62): analysis rules, reroute pooling, report building, pipeline job/arm definitions."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import p0_runner
import ph4_analysis as pa
import ph4_pipeline as pp
import screen_stats as st

SEEDS = list(range(10000, 10100))


def write_arm(directory, name, success_flags, perfect=None, extra=None, ik=None, col=None):
    d = Path(directory) / name
    d.mkdir(parents=True, exist_ok=True)
    perfect = success_flags if perfect is None else perfect
    with (d / 'episodes.jsonl').open('w') as f:
        for i, seed in enumerate(SEEDS):
            row = dict(seed=seed, success=bool(success_flags[i]), perfect_success=bool(perfect[i]), exception=None,
                       primary_reason='success' if success_flags[i] else 'ik_limit', steps=100 + i,
                       collision_count=int(col[i]) if col is not None else 0, ik_count=int(ik[i]) if ik is not None else 0,
                       trajectory_sha256='h%d' % seed)
            if extra:
                row.update(extra(i))
            f.write(json.dumps(row) + '\n')


def flags(n_success, offset=0):
    a = np.zeros(100, dtype=bool)
    a[[(offset + i) % 100 for i in range(n_success)]] = True
    return a


def reroute_extra(i):
    n = i % 3
    return dict(obsmap_reroute_count=n, obsmap_reroute_steps=list(range(1, n + 1)), obsmap_reroute_dists=[0.35] * n,
                obsmap_weight_updates=10 + i % 5, obsmap_post_reroute_ik_rate=(0.5 if n else None),
                obsmap_post_reroute_collision_rate=(0.0 if n else None), obsmap_observed_fraction_final=0.2,
                obsmap_seconds_mean=0.05)


# ---- reroute pooling --------------------------------------------------------------------------------------------

def test_reroute_stats_pool_rates_by_reroute_count():
    rows = {10000: dict(success=True, obsmap_reroute_count=2, obsmap_reroute_dists=[0.4, 0.5], obsmap_post_reroute_ik_rate=0.5,
                        obsmap_post_reroute_collision_rate=0.0, obsmap_weight_updates=3, obsmap_observed_fraction_final=0.1, obsmap_seconds_mean=0.01),
            10001: dict(success=False, obsmap_reroute_count=1, obsmap_reroute_dists=[0.31], obsmap_post_reroute_ik_rate=1.0,
                        obsmap_post_reroute_collision_rate=1.0, obsmap_weight_updates=5, obsmap_observed_fraction_final=0.3, obsmap_seconds_mean=0.03),
            10002: dict(success=True, obsmap_reroute_count=0, obsmap_reroute_dists=[], obsmap_post_reroute_ik_rate=None,
                        obsmap_post_reroute_collision_rate=None, obsmap_weight_updates=0, obsmap_observed_fraction_final=0.2, obsmap_seconds_mean=0.02)}
    s = pa.reroute_stats(rows, [10000, 10001, 10002])
    assert s['reroutes_total'] == 3 and s['episodes_with_reroute'] == pytest.approx(2 / 3)
    assert s['post_reroute_ik_rate'] == pytest.approx((0.5 * 2 + 1.0 * 1) / 3)      # weighted by the number of reroutes
    assert s['post_reroute_collision_rate'] == pytest.approx(1 / 3)
    assert s['reroutes_per_episode_failed'] == 1.0 and s['reroutes_per_episode_success'] == 1.0
    assert s['reroute_dist_max_m'] == 0.5 and s['reroute_count_distribution'] == {'0': 1, '1': 1, '2': 1}
    assert pa.reroute_stats({10000: dict(success=True)}, [10000]) is None            # no obsmap fields


# ---- D60 ---------------------------------------------------------------------------------------------------------

def make_ph3(tmp_path, sr):
    for name, n in sr.items():
        write_arm(tmp_path, name, flags(n), extra=reroute_extra)
    write_arm(tmp_path / 'base', '.', flags(sr['nominal']))   # baseline dir with episodes.jsonl at its root


def test_d60_harm_needs_a_drop_of_at_least_015_and_a_ci_upper_bound_below_zero(tmp_path):
    make_ph3(tmp_path, dict(nominal=70, r10=68, r5=60, r3=40))
    points, result = pa.analyze_ph3(tmp_path, SEEDS, tmp_path / 'base')
    d = result['diffs_point']
    assert d['r10']['success'] == pytest.approx(-0.02) and d['r10']['harm_passes'] is False
    assert d['r5']['success'] == pytest.approx(-0.10) and d['r5']['point_meets_drop'] is False and d['r5']['harm_passes'] is False
    assert d['r3']['success'] == pytest.approx(-0.30) and d['r3']['point_meets_drop'] is True
    assert d['r3']['success_ci95'][1] < 0 and d['r3']['harm_passes'] is True
    assert result['d60']['passing_radii'] == [3.0] and result['d60']['r_largest_passing'] == 3.0
    assert (tmp_path / 'analysis-point.json').exists() and (tmp_path / 'analysis.json').exists()
    assert result['nominal_reproduction']['reproduces'] is True and result['nominal_reproduction']['reference_sr'] == 0.70


def test_d60_a_drop_of_015_with_a_ci_that_includes_zero_does_not_pass(tmp_path):
    # identical success pattern except a few episodes: the paired difference is tiny relative to noise only if the flags overlap
    nominal, r3 = flags(70), flags(55)
    write_arm(tmp_path, 'nominal', nominal, extra=reroute_extra)
    write_arm(tmp_path, 'r10', nominal, extra=reroute_extra)
    write_arm(tmp_path, 'r5', nominal, extra=reroute_extra)
    write_arm(tmp_path, 'r3', np.roll(r3, 40), extra=reroute_extra)          # 55 successes, mostly not aligned with the nominal ones
    write_arm(tmp_path / 'base', '.', nominal)
    _, result = pa.analyze_ph3(tmp_path, SEEDS, tmp_path / 'base')
    d = result['diffs_point']['r3']
    assert d['point_meets_drop'] is True
    assert d['harm_passes'] == bool(d['success_ci95'][1] < 0)                # the rule is exactly: point and upper bound < 0


def test_ph3_points_are_written_before_any_ci_and_missing_arms_are_not_imputed(tmp_path):
    for name, n in dict(nominal=70, r10=68, r5=60).items():
        write_arm(tmp_path, name, flags(n))
    seen = []
    points, result = pa.analyze_ph3(tmp_path, SEEDS, None, on_points=lambda p: seen.append((tmp_path / 'analysis-point.json').exists()
                                                                                     and not (tmp_path / 'analysis.json').exists()))
    assert seen == [True]
    assert points['arms']['r3'] is None and 'd60' not in result and 'success_ci95' not in result['diffs_point'].get('r5', {})
    assert pa.build_ph3_report(points, result=result, final=True)


def test_nominal_reproduction_reports_hash_mismatches(tmp_path):
    write_arm(tmp_path, 'nominal', flags(70))
    base = tmp_path / 'base'
    write_arm(base, '.', flags(70))
    rows = [json.loads(l) for l in (base / 'episodes.jsonl').read_text().splitlines()]
    rows[3]['trajectory_sha256'] = 'other'
    (base / 'episodes.jsonl').write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
    p = pa.ph3_points(tmp_path, SEEDS, base)
    assert p['nominal_reproduction']['trajectory_sha256_identical'] == 99 and p['nominal_reproduction']['reproduces'] is False


# ---- D62 ---------------------------------------------------------------------------------------------------------

def make_ph4(tmp_path, sr, long=True):
    ph3, ph4 = tmp_path / 'ph3', tmp_path / 'ph4'
    write_arm(ph3, 'nominal', flags(sr['G11'], 0))
    ev = ph4 / 's3-eval'
    write_arm(ev, 'G-std-s22', flags(sr['G22'], 5))
    for rk in ('r3', 'r5'):
        write_arm(ev, 'K-std-%s-s11' % rk, flags(sr['K' + rk][0], 0), extra=reroute_extra)
        write_arm(ev, 'K-std-%s-s22' % rk, flags(sr['K' + rk][1], 5), extra=reroute_extra)
        write_arm(ev, 'random-%s' % rk, flags(sr['rand'], 20), extra=reroute_extra)
        if long:
            write_arm(ev, 'K-std-%s-long' % rk, flags(sr.get('L' + rk, sr['K' + rk][0]), 0), extra=reroute_extra)
    return ph3, ph4


def test_d62_passes_per_radius_and_r_sel_is_the_largest_passing_radius(tmp_path):
    ph3, ph4 = make_ph4(tmp_path, dict(G11=70, G22=72, Kr3=(45, 47), Kr5=(66, 68), rand=8))
    points, result = pa.analyze_ph4(ph3, ph4, SEEDS)
    r3, r5 = result['per_r']['r3'], result['per_r']['r5']
    assert r3['gap'] == pytest.approx(0.71 - 0.46) and r3['gap_ci95'][0] > 0 and r3['passes'] is True
    assert r5['gap'] == pytest.approx(0.04) and r5['gap_point_passes'] is False and r5['passes'] is False
    assert result['d62']['interim_passing_radii'] == [3.0] and result['d62']['interim_r_sel'] == 3.0
    assert result['d62']['passing_radii'] == [3.0] and result['d62']['r_sel'] == 3.0 and result['d62']['complete'] is True
    assert (ph4 / 'point.json').exists() and (ph4 / 'analysis.json').exists()
    assert pa.build_ph4_report(points, result=result, final=True)


def test_d62_random_margin_is_a_separate_condition(tmp_path):
    ph3, ph4 = make_ph4(tmp_path, dict(G11=70, G22=72, Kr3=(30, 32), Kr5=(30, 32), rand=8))     # gap big, K - random = 0.23 < 0.30
    _, result = pa.analyze_ph4(ph3, ph4, SEEDS)
    r3 = result['per_r']['r3']
    assert r3['gap_passes'] is True and r3['random_passes'] is False and r3['passes'] is False
    assert result['d62']['r_sel'] is None and result['d62']['complete'] is True and 'stop and discuss' in result['d62']['outcome']
    assert result['d62']['interim_passing_radii'] == []


def test_d62_both_radii_can_pass_and_the_larger_is_chosen(tmp_path):
    ph3, ph4 = make_ph4(tmp_path, dict(G11=80, G22=82, Kr3=(40, 42), Kr5=(50, 52), rand=8))
    _, result = pa.analyze_ph4(ph3, ph4, SEEDS)
    assert result['d62']['passing_radii'] == [5.0, 3.0] and result['d62']['r_sel'] == 5.0


def test_d62_incomplete_data_gives_no_verdict(tmp_path):
    ph3, ph4 = make_ph4(tmp_path, dict(G11=70, G22=72, Kr3=(45, 47), Kr5=(66, 68), rand=8))
    (ph4 / 's3-eval' / 'K-std-r5-s22' / 'episodes.jsonl').unlink()
    points, result = pa.analyze_ph4(ph3, ph4, SEEDS)
    assert 'r5' not in result['per_r'] and result['d62']['complete'] is False and result['d62']['outcome'] == 'incomplete data'
    assert pa.build_ph4_report(points, result=result, final=True)


def test_d62_uses_the_paired_stratified_bootstrap_with_seed_zero(tmp_path):
    ph3, ph4 = make_ph4(tmp_path, dict(G11=70, G22=72, Kr3=(45, 47), Kr5=(66, 68), rand=8))
    _, result = pa.analyze_ph4(ph3, ph4, SEEDS)
    G = np.stack([flags(70, 0), flags(72, 5)]).astype(float)
    K = np.stack([flags(45, 0), flags(47, 5)]).astype(float)
    ref = st.diff_with_ci(G, K, n_boot=10000, seed=0)
    assert result['per_r']['r3']['gap_ci95'] == pytest.approx(ref['ci95']) and result['per_r']['r3']['n_boot'] == 10000


# ---- pipeline definitions ---------------------------------------------------------------------------------------

def cfg():
    return SimpleNamespace(gpus=[0, 1, 2, 3], policy='/p/policy-100k.pt', device='cuda', train_steps=100000, batch=256, random_steps=1000,
                           replay_capacity=100000, save_interval=20000, task_id='PH4-1', eval_seeds=SEEDS)


def test_registered_jobs_match_d62():
    jobs = pp.train_jobs(cfg())
    assert [(j['name'], j['seed'], j['flags'].get('obsmap_radius')) for j in jobs] == [
        ('K-std-r3-s11', 11, 3.0), ('K-std-r3-s22', 22, 3.0), ('K-std-r5-s11', 11, 5.0), ('K-std-r5-s22', 22, 5.0), ('G-std-s22', 22, None)]
    assert all(j['task'] == 'simpleobstacle' for j in jobs) and {j['gpu'] for j in jobs} == {0, 1, 2, 3}


def test_train_commands_carry_the_obsmap_switch_and_the_policy_100k_configuration(tmp_path):
    k = [j for j in pp.train_jobs(cfg()) if j['name'] == 'K-std-r5-s22'][0]
    cmd = pp.train_command(cfg(), k, tmp_path / 'a0')
    assert cmd[cmd.index('--obsmap-radius') + 1] == '5.0' and cmd[-2:] == ['--output', str(tmp_path / 'a0')]
    for flag, value in [('--steps', '100000'), ('--save-interval', '20000'), ('--batch', '256'), ('--replay-capacity', '100000'),
                        ('--random-steps', '1000'), ('--ik-mode', 'fixed'), ('--ik-iterations', '100'), ('--eval-interval', '0'), ('--seed', '22')]:
        assert cmd[cmd.index(flag) + 1] == value
    assert '--replay-compact-maps' in cmd
    g = [j for j in pp.train_jobs(cfg()) if j['name'] == 'G-std-s22'][0]
    assert not any(a.startswith('--obsmap') for a in pp.train_command(cfg(), g, tmp_path / 'a0'))
    resumed = pp.train_command(cfg(), k, tmp_path / 'a1', resume=tmp_path / 'a0' / 'latest.pt')
    assert resumed[resumed.index('--resume') + 1] == str(tmp_path / 'a0' / 'latest.pt') and resumed[-2:] == ['--output', str(tmp_path / 'a1')]
    assert '--obsmap-radius' in resumed and '--steps' in resumed


def test_eval_arm_flags(tmp_path):
    c = cfg()
    ph3 = {n: p0_runner.episode_command(a, tmp_path, 10000) for n, a in pp.ph3_arms(c).items()}
    assert '--obsmap-log-reroutes' in ph3['nominal'] and '--obsmap-radius' not in ph3['nominal']
    for n, r in (('r10', '10.0'), ('r5', '5.0'), ('r3', '3.0')):
        assert ph3[n][ph3[n].index('--obsmap-radius') + 1] == r
    rnd = {n: p0_runner.episode_command(a, tmp_path, 10000) for n, a in pp.random_arms(c).items()}
    assert rnd['random-r3'][rnd['random-r3'].index('--policy-override') + 1] == 'random' and '--obsmap-radius' in rnd['random-r3']
    assert rnd['random-r5'][rnd['random-r5'].index('--obsmap-radius') + 1] == '5.0'
    k = [j for j in pp.train_jobs(c) if j['name'] == 'K-std-r3-s11'][0]
    cmd = p0_runner.episode_command(pp.trained_arm(c, k, '/x/policy.pt'), tmp_path, 10000)
    assert cmd[cmd.index('--checkpoint') + 1] == '/x/policy.pt' and cmd[cmd.index('--obsmap-radius') + 1] == '3.0'
    g = [j for j in pp.train_jobs(c) if j['name'] == 'G-std-s22'][0]
    assert not any(a.startswith('--obsmap') for a in p0_runner.episode_command(pp.trained_arm(c, g, '/x/policy.pt'), tmp_path, 10000))


def test_validation_keeps_the_registered_ranges():
    ok = SimpleNamespace(eval_seeds=SEEDS, max_workers=47, train_steps=100000, save_interval=20000, long_steps=300000, long_save_interval=50000)
    pp.validate(ok)
    for bad in (SimpleNamespace(**dict(vars(ok), eval_seeds=list(range(20000, 20100)))), SimpleNamespace(**dict(vars(ok), eval_seeds=list(range(9000, 9100)))),
                SimpleNamespace(**dict(vars(ok), max_workers=65)), SimpleNamespace(**dict(vars(ok), train_steps=100001)),
                SimpleNamespace(**dict(vars(ok), long_steps=310000))):
        with pytest.raises(SystemExit):
            pp.validate(bad)
    assert pp.build_parser().parse_args([]).max_workers == 47      # 7 training processes + <= 40 evaluation workers


# ---- D64 convergence check ---------------------------------------------------------------------------------------------

def test_d64_long_run_that_catches_up_makes_the_100k_pass_an_under_training_failure(tmp_path):
    # r3: D62 passes at 100k (gap 0.25) but the 300k run reaches 0.66 vs G 0.71 -> gap 0.05 < 0.10 -> "under-trained, not passed"
    ph3, ph4 = make_ph4(tmp_path, dict(G11=70, G22=72, Kr3=(45, 47), Kr5=(66, 68), rand=8, Lr3=66, Lr5=40))
    points, result = pa.analyze_ph4(ph3, ph4, SEEDS)
    r3, r5 = result['per_r']['r3'], result['per_r']['r5']
    assert r3['passes_100k'] is True and r3['gap_long'] == pytest.approx(0.05) and r3['long_passes'] is False and r3['passes'] is False
    assert 'under-trained' in r3['not_passed_reason'] and 'gap_long_ci95_descriptive' in r3
    assert r5['passes_100k'] is False and r5['gap_long'] == pytest.approx(0.31) and r5['long_passes'] is True and r5['passes'] is False
    assert result['d62']['interim_passing_radii'] == [3.0] and result['d62']['passing_radii'] == [] and result['d62']['r_sel'] is None
    assert result['d62']['complete'] is True and 'under-training' in result['d62']['outcome']


def test_d64_long_gap_of_exactly_010_counts_and_r_sel_needs_both_conditions(tmp_path):
    ph3, ph4 = make_ph4(tmp_path, dict(G11=70, G22=72, Kr3=(45, 47), Kr5=(45, 47), rand=8, Lr3=61, Lr5=50))
    _, result = pa.analyze_ph4(ph3, ph4, SEEDS)
    assert result['per_r']['r3']['gap_long'] == pytest.approx(0.10) and result['per_r']['r3']['long_passes'] is True    # >= is inclusive
    assert result['per_r']['r3']['passes'] is True and result['per_r']['r5']['passes'] is True and result['d62']['r_sel'] == 5.0


def test_interim_result_without_the_long_runs_is_labelled_and_not_final(tmp_path):
    ph3, ph4 = make_ph4(tmp_path, dict(G11=70, G22=72, Kr3=(45, 47), Kr5=(66, 68), rand=8), long=False)
    points, result = pa.analyze_ph4(ph3, ph4, SEEDS)
    d = result['d62']
    assert d['complete_100k'] is True and d['complete'] is False and d['r_sel'] is None and d['interim_r_sel'] == 3.0
    assert d['outcome'].startswith('interim (100k runs only)')
    text = pa.build_ph4_report(points, result=result, final=True)
    assert '中间报告' in text and '终稿' not in text.split('\n')[2]


def test_learning_curves_use_intermediate_checkpoint_arms_and_the_final_arm(tmp_path):
    ph3, ph4 = make_ph4(tmp_path, dict(G11=70, G22=72, Kr3=(45, 47), Kr5=(66, 68), rand=8, Lr3=50, Lr5=50))
    for name in pa.job_names():
        for step in pa.curve_steps(name)[:-1]:
            write_arm(ph4 / 's6-curves', pa.curve_arm(name, step), flags(20 + step // 10000))
    points, result = pa.analyze_ph4(ph3, ph4, SEEDS)
    c = result['curves']
    assert set(c) == set(pa.job_names()) and len(pa.job_names()) == 7
    assert list(c['K-std-r3-s11']) == ['20000', '40000', '60000', '80000', '100000']
    assert list(c['K-std-r5-long']) == ['50000', '100000', '150000', '200000', '250000', '300000']
    assert c['K-std-r3-s11']['40000']['success_rate'] == pytest.approx(0.24) and c['K-std-r3-s11']['100000']['success_rate'] == pytest.approx(0.45)
    assert c['K-std-r3-long']['300000']['success_rate'] == pytest.approx(0.50)
    text = pa.build_ph4_report(points, result=result, final=True)
    assert '学习曲线' in text and '末 3 点极差' in text


def test_long_jobs_are_registered_like_d64(tmp_path):
    c = cfg()
    c.long_steps, c.long_save_interval, c.long_timeout_hours, c.train_timeout_hours = 300000, 50000, 72.0, 24.0
    jobs = pp.long_jobs(c)
    assert [(j['name'], j['seed'], j['flags']['obsmap_radius']) for j in jobs] == [('K-std-r3-long', 11, 3.0), ('K-std-r5-long', 11, 5.0)]
    assert len(pp.all_jobs(c)) == 7 and len({j['gpu'] for j in pp.all_jobs(c)}) == 4
    lc = pp.long_cfg(c)
    cmd = pp.train_command(lc, jobs[1], tmp_path / 'a0')
    assert cmd[cmd.index('--steps') + 1] == '300000' and cmd[cmd.index('--save-interval') + 1] == '50000'
    assert cmd[cmd.index('--obsmap-radius') + 1] == '5.0' and cmd[cmd.index('--seed') + 1] == '11'
    assert cmd[cmd.index('--replay-capacity') + 1] == '100000' and cmd[cmd.index('--batch') + 1] == '256'
    resumed = pp.train_command(lc, jobs[0], tmp_path / 'a1', resume=tmp_path / 'a0' / 'latest.pt')
    assert resumed[resumed.index('--steps') + 1] == '300000' and '--resume' in resumed
    assert pp.job_cfg(c, 'K-std-r3-long').train_steps == 300000 and pp.job_cfg(c, 'K-std-r3-s11').train_steps == 100000
    assert lc.train_timeout_hours == 72.0 and c.train_timeout_hours == 24.0


def test_find_step_checkpoints_takes_the_newest_complete_file_per_step(tmp_path):
    import os
    for a, step, t in [('a0', 20000, 1), ('a1', 20000, 5), ('a0', 40000, 2)]:
        f = tmp_path / a / ('step-%07d.pt' % step)
        f.parent.mkdir(exist_ok=True)
        f.write_bytes(b'x')
        os.utime(f, (t, t))
    (tmp_path / 'a0' / 'step-0060000.pt.tmp').write_bytes(b'x')
    (tmp_path / 'a0' / 'latest.pt').write_bytes(b'x')
    found = pp.find_step_checkpoints(tmp_path)
    assert sorted(found) == [20000, 40000] and found[20000].parent.name == 'a1'


# ---- ROS masters (measured bottleneck: one rosmaster saturated by ~47 processes doing costmap inflations) --------------

def test_every_training_job_has_its_own_ros_master_and_evaluation_is_spread_over_four_more():
    c = cfg()
    c.long_steps, c.long_save_interval, c.long_timeout_hours, c.train_timeout_hours = 300000, 50000, 72.0, 24.0
    jobs = pp.all_jobs(c)
    ports = [int(j['env']['ROS_MASTER_URI'].rsplit(':', 1)[1]) for j in jobs]
    assert ports == list(range(pp.TRAIN_MASTER_BASE, pp.TRAIN_MASTER_BASE + 7)) and all(j['env']['ROS_IP'] == '127.0.0.1' for j in jobs)
    assert pp.ros_ports() == ports + [pp.EVAL_MASTER_BASE + i for i in range(pp.EVAL_MASTERS)] and len(set(pp.ros_ports())) == 11
    assert not set(ports) & {11311} and not set(pp.ros_ports()) & {11311}                        # never the shared default master
    used = {pp.eval_master_port(s) for s in SEEDS}
    assert used == {pp.EVAL_MASTER_BASE + i for i in range(pp.EVAL_MASTERS)}
    env = pp.worker_env(cfg(), 10003)
    assert env['ROS_MASTER_URI'] == 'http://127.0.0.1:%d' % (pp.EVAL_MASTER_BASE + 10003 % pp.EVAL_MASTERS) and env['P0_TASK_ID'] == 'PH4-1'
    assert env['CUDA_VISIBLE_DEVICES'] == str([0, 1, 2, 3][10003 % 4])                            # the original GPU mapping is kept
    assert pp.worker_env(cfg(), 10003) == env                                                    # deterministic


def test_training_job_env_is_merged_into_the_training_process_environment(monkeypatch, tmp_path):
    import screen_pipeline as sp
    captured = {}

    class Boom(Exception):
        pass

    def fake_popen(cmd, **kw):
        captured['env'] = kw['env']
        raise Boom()
    monkeypatch.setattr(sp.subprocess, 'Popen', fake_popen)
    monkeypatch.setattr(sp, 'wait_for_memory', lambda *a, **k: None)
    c = cfg()
    c.max_attempts, c.train_timeout_hours = 1, 1.0
    job = pp.train_jobs(c)[0]
    status = SimpleNamespace(update=lambda *a, **k: None)
    with pytest.raises(Boom):
        sp.run_training_job(c, job, tmp_path, sp.SlotPool(4), status, 'S1', {}, 1e18)
    assert captured['env']['ROS_MASTER_URI'] == 'http://127.0.0.1:%d' % pp.TRAIN_MASTER_BASE and captured['env']['CUDA_VISIBLE_DEVICES'] == '0'
