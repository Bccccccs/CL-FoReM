"""SCREEN-028: orchestration pieces, analyses on synthetic episodes, report, CLI plumbing."""
import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

import p0_runner
import screen_analysis as sa
import screen_pipeline as sp
import screen_report
import screen_stats as st

SEEDS = list(range(10000, 10040))


def write_arm(stage_dir, arm, success_prob, seed=0, collision_prob=0.3):
    import zlib
    rng = np.random.default_rng(zlib.crc32(arm.encode()) + seed)
    d = Path(stage_dir) / arm
    d.mkdir(parents=True, exist_ok=True)
    with (d / 'episodes.jsonl').open('w') as f:
        for s in SEEDS:
            ok = bool(rng.random() < success_prob)
            f.write(json.dumps(dict(seed=s, success=ok, perfect_success=ok and rng.random() < .6,
                                    primary_reason='success' if ok else 'collision_limit', exception=None,
                                    collision_count=int(rng.random() < collision_prob) * 3, ik_count=int(rng.random() < .3),
                                    steps=100)) + '\n')


def test_cli_default_worker_command_has_no_screen_flags_and_flags_forward_when_set(tmp_path):
    base = SimpleNamespace(checkpoint='c.pt', task='simpleobstacle', world_type='sim', device='cpu', seed=11, max_episode_steps=2000,
                           ik_mode='fixed', ik_iterations=100, policy_mode='deterministic')
    plain = p0_runner.episode_command(base, tmp_path, 10000)
    assert not any(a.startswith(('--obs-', '--map-', '--dyn-', '--latency-')) for a in plain)
    args = SimpleNamespace(**dict(vars(base), obs_latency_steps=3, obs_action_history=3, dyn_map_mode='future', dyn_freeze=True,
                                  latency_wm_comp='cfg.json'))
    cmd = p0_runner.episode_command(args, tmp_path, 10000)
    for flag, val in [('--obs-latency-steps', '3'), ('--obs-action-history', '3'), ('--dyn-map-mode', 'future'), ('--latency-wm-comp', 'cfg.json')]:
        assert cmd[cmd.index(flag) + 1] == val
    assert '--dyn-freeze' in cmd and '--map-latency-steps' not in cmd and '--dyn-map-horizon' not in cmd


def test_argparse_rejects_bad_combinations(monkeypatch, tmp_path):
    def run(*argv):
        monkeypatch.setattr('sys.argv', ['p0_runner.py', *argv, '--output', str(tmp_path / 'o')])
        with pytest.raises(SystemExit):
            p0_runner.main()
    run('train', '--dyn-map-mode', 'future')                                   # simpleobstacle + dynmap
    run('train', '--dyn-freeze')
    run('eval', '--checkpoint', 'x', '--seeds', 'y', '--latency-wm-comp', 'z')  # no latency switch
    run('eval', '--checkpoint', 'x', '--seeds', 'y', '--obs-latency-steps', '2', '--obs-action-history', '2', '--latency-wm-comp', 'z')
    run('train', '--obs-latency-steps', '-1')


def test_job_definitions_and_gpu_balance():
    cfg = SimpleNamespace(train_seeds=(11, 22), gpus=[0, 1, 2, 3])
    d, l = sp.d_jobs(cfg), sp.l_jobs(cfg, 3, 'full', 6)
    assert [j['name'] for j in d] == ['D-std-s11', 'D-oracle-s11', 'D-hist-s11', 'D-std-s22', 'D-oracle-s22', 'D-hist-s22']
    assert [j['flags'] for j in d[:3]] == [{}, {'dyn_map_mode': 'future'}, {'dyn_map_mode': 'past'}]
    assert [j['flags'] for j in l[:3]] == [{}, {'obs_latency_steps': 3}, {'obs_latency_steps': 3, 'obs_action_history': 3}]
    assert l[1]['flags'] != l[0]['flags'] and all(j['task'] == 'dynobstacle' for j in d) and all(j['task'] == 'simpleobstacle' for j in l)
    counts = {g: sum(1 for j in d + l if j['gpu'] == g) for g in range(4)}
    assert set(counts.values()) == {3}, counts
    lm = sp.l_jobs(cfg, 2, 'map', 6)
    assert lm[1]['flags'] == {'map_latency_steps': 2} and lm[2]['flags'] == {'map_latency_steps': 2, 'obs_action_history': 2}


def test_train_command_uses_policy100k_hyperparameters_and_compact_replay():
    cfg = sp.build_parser().parse_args([])
    job = dict(name='D-oracle-s11', task='dynobstacle', seed=11, flags={'dyn_map_mode': 'future'}, gpu=0)
    cmd = sp.train_command(cfg, job, Path('/o'), resume=Path('/r/step.pt'))
    joined = ' '.join(cmd)
    for frag in ['--steps 100000', '--batch 256', '--random-steps 1000', '--replay-capacity 100000', '--save-interval 20000',
                 '--eval-interval 0', '--ik-mode fixed', '--ik-iterations 100', '--replay-compact-maps', '--dyn-map-mode future',
                 '--task dynobstacle', '--seed 11', '--resume /r/step.pt', '--output /o']:
        assert frag in joined, frag
    assert '--algorithm' not in joined


def test_seed_registration_guards():
    ok = sp.build_parser().parse_args([]); ok.eval_seeds = sp.parse_seed_spec(ok.eval_seeds); ok.train_seeds = (11, 22)
    sp.validate_seeds(ok)
    for bad_eval in ['20000:20010', '9000:9010', '10000:10101', '8000:8005']:
        c = sp.build_parser().parse_args([]); c.eval_seeds = sp.parse_seed_spec(bad_eval); c.train_seeds = (11, 22)
        with pytest.raises(SystemExit):
            sp.validate_seeds(c)
    c = sp.build_parser().parse_args([]); c.eval_seeds = [10000]; c.train_seeds = (33,)
    with pytest.raises(SystemExit):
        sp.validate_seeds(c)
    c = sp.build_parser().parse_args(['--max-workers', '65']); c.eval_seeds = [10000]; c.train_seeds = (11,)
    with pytest.raises(SystemExit):
        sp.validate_seeds(c)


def test_slot_pool_capacity_and_training_priority():
    pool = sp.SlotPool(2)
    assert pool.try_acquire() and pool.try_acquire() and not pool.try_acquire()
    pool.release()
    got = []
    t = threading.Thread(target=lambda: (pool.acquire(poll=0.01), got.append(1)))
    pool.release()  # one free slot
    with pool.lock:
        pool.waiting += 1   # simulate a waiting training job
    assert not pool.try_acquire(), 'eval workers must not take slots while a training job waits'
    assert pool.try_acquire(priority=True)
    with pool.lock:
        pool.waiting -= 1


def test_newest_checkpoint_and_progress_parsing(tmp_path):
    (tmp_path / 'a0').mkdir(); (tmp_path / 'a1').mkdir()
    old = tmp_path / 'a0' / 'step-0020000.pt'; old.write_bytes(b'x'); time.sleep(0.02)
    new = tmp_path / 'a1' / 'latest.pt'; new.write_bytes(b'y')
    (tmp_path / 'a1' / 'other.pt').write_bytes(b'z')
    assert sp.newest_checkpoint(tmp_path) == new
    assert sp.newest_checkpoint(tmp_path / 'none') is None
    log = tmp_path / 'log'
    log.write_text("noise\nTRAIN {'steps': 100} seconds 1\nTRAIN {'steps': 200} seconds 2\nwarning\n")
    assert sp.last_progress(log).startswith("TRAIN {'steps': 200}")


def test_export_policy_drops_replay_and_keeps_loader_layout(tmp_path):
    from checkpointing import load_trusted
    src = tmp_path / 'full.pt'
    torch.save(dict(version=2, semantics='p0-action-terminal-v2', agent=dict(policy={'w': torch.ones(3)}, critic={'c': torch.zeros(2)}),
                    counters=dict(steps=100000, updates=99001, episodes=5), agent_config={'gamma': .99},
                    replay=dict(buffer=[np.zeros(1000)] * 100)), str(src))
    dst = tmp_path / 'policy.pt'
    sp.export_policy(src, dst)
    light = load_trusted(dst, map_location='cpu')
    assert set(light) == {'version', 'semantics', 'agent', 'counters', 'agent_config', 'derived_from'}
    assert set(light['agent']) == {'policy'} and light['version'] == 2 and light['derived_from']['source_sha256'] == sp.sha256_file(src)
    assert dst.stat().st_size < src.stat().st_size


def build_synthetic_root(tmp_path, l1_drops):
    root = tmp_path / 'root'
    s1 = root / 's1-l1'
    for name, kind, k in sa.L1_ARMS:
        write_arm(s1, name, 0.85 - l1_drops.get(name, 0.0))
    return root


def test_l1_analysis_writes_point_first_and_applies_rule(tmp_path):
    root = build_synthetic_root(tmp_path, {'full3': 0.5, 'full5': 0.6, 'map5': 0.5})
    res = sa.analyze_l1(root / 's1-l1', SEEDS, root / 's1-l1' / 'analysis', n_boot=500)
    assert (root / 's1-l1' / 'analysis' / 'point.json').exists() and (root / 's1-l1' / 'analysis' / 'result.json').exists()
    point = json.loads((root / 's1-l1' / 'analysis' / 'point.json').read_text())
    assert 'delta_ci95' not in point['arms']['full3'], 'point file must not depend on the CI step'
    assert res['passes']['full']['3'] and res['passes']['full']['5'] and not res['passes']['full']['1']
    assert res['decision'] == dict(tier='realistic', k_sel=3, mode='full', l2_runs=True)


def test_l1_analysis_missing_arm_is_unavailable_not_imputed(tmp_path):
    root = build_synthetic_root(tmp_path, {})
    (root / 's1-l1' / 'map5' / 'episodes.jsonl').unlink()
    res = sa.analyze_l1(root / 's1-l1', SEEDS, root / 's1-l1' / 'analysis', n_boot=200)
    assert res['arms']['map5'].get('unavailable') and res['passes']['map']['5'] is False


def fake_family(d, template, prob):
    for seed in (11, 22):
        write_arm(d, template % seed, prob, seed=seed)


def test_l2_and_d_analyses_and_full_report(tmp_path):
    root = build_synthetic_root(tmp_path, {'full3': 0.5})
    sa.analyze_l1(root / 's1-l1', SEEDS, root / 's1-l1' / 'analysis', n_boot=200)
    l1 = dict(eval={}, analysis=json.loads((root / 's1-l1' / 'analysis' / 'result.json').read_text()))
    (root / 's1-l1' / 'result.json').write_text(json.dumps(l1))
    s7 = root / 's7-l2-eval'
    fake_family(s7, 'L-oracle-s%d', 0.9); fake_family(s7, 'L-stale-s%d', 0.4); fake_family(s7, 'L-hist-s%d', 0.4)
    l2 = sa.analyze_l2(s7, SEEDS, s7 / 'analysis', 3, 'full', n_boot=300)
    assert l2['verdict']['passes'] is True
    (s7 / 'result.json').write_text(json.dumps(dict(eval={}, analysis=l2, missing=[])))
    s6 = root / 's6-d2-eval'
    fake_family(s6, 'D-std-s%d', 0.7); fake_family(s6, 'D-stdfrozen-s%d', 0.7); fake_family(s6, 'D-oracle-s%d', 0.7); fake_family(s6, 'D-hist-s%d', 0.7)
    d = sa.analyze_d(s6, SEEDS, s6 / 'analysis', n_boot=300)
    assert d['verdict']['passes'] is False and d['verdict']['harm'] is False
    (s6 / 'result.json').write_text(json.dumps(dict(eval={}, analysis=d, missing=[])))
    s5 = root / 's5-l3'
    write_arm(s5, 'wm-comp', 0.6)
    l3 = sa.analyze_l3(root / 's1-l1', s5, SEEDS, s5 / 'analysis', 'full3', n_boot=300)
    assert 'recovery_ratio' in l3 and 'recovery' in l3
    (s5 / 'result.json').write_text(json.dumps(dict(eval={}, analysis=l3, mode='full', k=3)))
    (root / 'status.json').write_text(json.dumps(dict(updated='t', stages={'S1': dict(state='done')})))
    text = screen_report.build_report(root)
    for frag in ['L1 伤害测试', 'D54-harm', '只有 L 线通过', 'L3 探索', '恢复比例', '最终选择由用户确认']:
        assert frag in text, frag


def test_report_handles_everything_missing(tmp_path):
    text = screen_report.build_report(tmp_path)
    assert '无结果' in text and '未评估' in text


def test_d_verdict_thresholds():
    ci = lambda lo: [lo, lo + .2]
    v = sa._d_verdict(dict(frozen_minus_moving=dict(point=.15, ci95=ci(.01)), oracle_minus_hist=dict(point=.10, ci95=ci(.01)),
                           oracle_minus_std=dict(point=.2, ci95=ci(.01))))
    assert v == dict(harm=True, headroom=True, passes=True)
    v = sa._d_verdict(dict(frozen_minus_moving=dict(point=.14, ci95=ci(.01)), oracle_minus_hist=dict(point=.2, ci95=ci(.01)),
                           oracle_minus_std=dict(point=.2, ci95=ci(-.01))))
    assert v == dict(harm=False, headroom=False, passes=False)
