"""CEIL-028: --policy-override controls (D57 E2): action generation, CLI plumbing, default-off behaviour."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import p0_runner
import policy_override as po


def write_traj(directory, seed, actions):
    np.savez_compressed(Path(directory) / ('episode-%05d-trajectory.npz' % seed), actions=np.asarray(actions, dtype=np.float32))


# ---- action generation -----------------------------------------------------------------------

def test_random_is_reproducible_from_the_episode_seed_and_in_range():
    a, b = po.PolicyOverride('random'), po.PolicyOverride('random')
    a.reset(10007); b.reset(10007)
    seq_a = [a.act() for _ in range(50)]
    seq_b = [b.act() for _ in range(50)]
    assert all(np.array_equal(x, y) for x, y in zip(seq_a, seq_b))
    stacked = np.stack(seq_a)
    assert stacked.shape == (50, 3) and stacked.dtype == np.float32
    assert stacked.min() >= -1.0 and stacked.max() <= 1.0 and stacked.std() > 0.3   # uniform, not constant
    b.reset(10008)
    assert not np.array_equal(b.act(), seq_a[0])                                     # another seed -> another stream
    a.reset(10007)
    assert np.array_equal(a.act(), seq_a[0])                                         # reset restarts the stream


def test_random_does_not_touch_global_or_environment_random_state():
    np.random.seed(123)
    expected = np.random.uniform(size=3)
    np.random.seed(123)
    o = po.PolicyOverride('random'); o.reset(1)
    for _ in range(5):
        o.act()
    assert np.array_equal(np.random.uniform(size=3), expected)


def test_mean_action_is_the_step_pooled_mean_and_written_from_data(tmp_path):
    write_traj(tmp_path, 10000, [[1, 0, 0], [1, 0, 0], [1, 0, 0]])     # 3 steps
    write_traj(tmp_path, 10001, [[-1, 0.5, 0.2]])                      # 1 step: pooled mean differs from the mean of episode means
    m = po.mean_action_from_trajectories(tmp_path)
    assert m['n_steps'] == 4 and m['n_episodes'] == 2
    assert np.allclose(m['mean'], [0.5, 0.125, 0.05])
    assert not np.allclose(m['mean'], [0.0, 0.25, 0.1])                # would be the (wrong) per-episode average
    assert len(m['actions_sha256']) == 64
    with pytest.raises(FileNotFoundError):
        po.mean_action_from_trajectories(tmp_path / 'nowhere')


def test_mean_control_outputs_a_fixed_copy_and_needs_the_mean():
    o = po.PolicyOverride('mean', [-0.3, 0.01, 0.26])
    o.reset(1)
    first, second = o.act(), o.act()
    assert np.array_equal(first, second) and first.dtype == np.float32 and first.shape == (3,)
    first[0] = 5.0
    assert o.act()[0] == np.float32(-0.3)                              # callers cannot corrupt the stored mean
    assert not o.uses_policy
    with pytest.raises(ValueError):
        po.PolicyOverride('mean')
    with pytest.raises(ValueError):
        po.PolicyOverride('mean', [2.0, 0, 0])


def test_slow_ee_changes_only_dimension_zero_and_does_not_mutate_input():
    o = po.PolicyOverride('slow-ee')
    o.reset(1)
    policy_action = np.array([0.7, -0.4, 0.9], dtype=np.float32)
    out = o.act(policy_action)
    assert out.tolist() == [-1.0, np.float32(-0.4), np.float32(0.9)]
    assert policy_action.tolist() == [np.float32(0.7), np.float32(-0.4), np.float32(0.9)]
    assert o.uses_policy


def test_unknown_mode_and_from_args(tmp_path):
    with pytest.raises(ValueError):
        po.PolicyOverride('greedy')
    f = tmp_path / 'mean.json'
    f.write_text(json.dumps(dict(mean=[0.1, 0.2, 0.3])))
    o = po.PolicyOverride.from_args(SimpleNamespace(policy_override='mean', policy_override_mean_file=str(f)))
    assert np.allclose(o.act(), [0.1, 0.2, 0.3])
    with pytest.raises(ValueError):
        po.PolicyOverride.from_args(SimpleNamespace(policy_override='mean', policy_override_mean_file=None))


# ---- CLI plumbing ----------------------------------------------------------------------------

def base_args(**extra):
    return SimpleNamespace(checkpoint='c.pt', task='simpleobstacle', world_type='sim', device='cpu', seed=11, max_episode_steps=2000,
                           ik_mode='fixed', ik_iterations=100, policy_mode='deterministic', **extra)


def test_default_worker_command_has_no_override_flags_and_they_forward_when_set(tmp_path):
    plain = p0_runner.episode_command(base_args(), tmp_path, 10000)
    assert not any(a.startswith('--policy-override') for a in plain)
    assert p0_runner.ceil_flags(base_args()) == []
    cmd = p0_runner.episode_command(base_args(policy_override='mean', policy_override_mean_file='m.json'), tmp_path, 10000)
    assert cmd[cmd.index('--policy-override') + 1] == 'mean' and cmd[cmd.index('--policy-override-mean-file') + 1] == 'm.json'
    cmd = p0_runner.episode_command(base_args(policy_override='slow-ee'), tmp_path, 10000)
    assert cmd[cmd.index('--policy-override') + 1] == 'slow-ee' and '--policy-override-mean-file' not in cmd


def test_argparse_rejects_bad_override_combinations(monkeypatch, tmp_path):
    def run(*argv):
        monkeypatch.setattr('sys.argv', ['p0_runner.py', *argv, '--output', str(tmp_path / 'o')])
        with pytest.raises(SystemExit):
            p0_runner.main()
    run('train', '--policy-override', 'random')                                                # eval only
    run('eval', '--checkpoint', 'x', '--seeds', 'y', '--policy-override', 'mean')             # mean needs its file
    run('eval', '--checkpoint', 'x', '--seeds', 'y', '--policy-override', 'random', '--policy-override-mean-file', 'f')
    run('eval', '--checkpoint', 'x', '--seeds', 'y', '--policy-override', 'slow-ee', '--shield-config', 'z')
    assert not (tmp_path / 'o').exists()


# ---- evaluate() integration with a fake environment --------------------------------------------

class FakeEnv:
    """Minimal env exposing exactly what p0_runner.evaluate touches; succeeds after 3 steps."""
    def __init__(self):
        self.received, self.map = [], SimpleNamespace(_floorplan_img=np.zeros((4, 4), dtype=np.float32))
        self.action_space = SimpleNamespace(seed=lambda s: None)
        self.unwrapped = SimpleNamespace(_ee_planner=SimpleNamespace(gripper_goal_wrist=[0., 0., 0.]))
        self.current_goal, self.goals, self.t = 0, [1], 0

    def seed(self, s): pass
    def get_robot_obs(self): return SimpleNamespace(base_tf=[0., 0., 0.])
    def reset(self):
        self.t = 0
        return [np.zeros(41, dtype=np.float32), np.zeros((120, 120, 1), dtype=np.float32)]

    def step(self, action):
        self.received.append(np.asarray(action).copy()); self.t += 1
        done = self.t >= 3
        info = dict(nr_base_collisions=0, nr_kin_failures=0, ee_done=done)
        return [np.zeros(41, dtype=np.float32), np.zeros((120, 120, 1), dtype=np.float32)], 0.0, done, info


class FakeAgent:
    def __init__(self):
        self.policy, self.calls = SimpleNamespace(eval=lambda: None), 0

    def select_action(self, state, eval=False):
        self.calls += 1
        return np.array([0.5, 0.25, -0.5], dtype=np.float32)


def run_evaluate(tmp_path, **flags):
    seeds = tmp_path / 'seeds.json'
    seeds.write_text('[10000, 10001]')
    ckpt = tmp_path / 'c.pt'
    ckpt.write_bytes(b'x')
    args = SimpleNamespace(seeds=str(seeds), episodes=2, save_observations=False, world_type='sim', task='simpleobstacle',
                           checkpoint=str(ckpt), max_episode_steps=50, policy_mode='deterministic', save_step_info=False,
                           shield_config=None, latency_wm_comp=None, **flags)
    out = tmp_path / 'out'; out.mkdir()
    env, agent = FakeEnv(), FakeAgent()
    p0_runner.evaluate(args, agent, env, out, dict(ik_fail_thresh=10, time_step=.1))
    rows = [json.loads(l) for l in (out / 'episodes.jsonl').read_text().splitlines()]
    return env, agent, rows


def test_default_off_evaluate_uses_the_policy_and_adds_no_field(tmp_path):
    env, agent, rows = run_evaluate(tmp_path)
    assert agent.calls == 6 and all('policy_override' not in r for r in rows)
    assert all(np.allclose(a, [0.5, 0.25, -0.5]) for a in env.received)


def test_random_and_mean_never_query_the_policy_and_tag_the_row(tmp_path):
    mean = tmp_path / 'mean.json'
    mean.write_text(json.dumps(dict(mean=[-0.3, 0.0, 0.25])))
    (tmp_path / 'a').mkdir()
    env, agent, rows = run_evaluate(tmp_path / 'a', policy_override='random')
    assert agent.calls == 0 and all(r['policy_override'] == 'random' for r in rows) and len(env.received) == 6
    (tmp_path / 'b').mkdir()
    env, agent, rows = run_evaluate(tmp_path / 'b', policy_override='mean', policy_override_mean_file=str(mean))
    assert agent.calls == 0 and all(r['policy_override'] == 'mean' for r in rows)
    assert all(np.allclose(a, [-0.3, 0.0, 0.25]) for a in env.received)


def test_slow_ee_queries_the_policy_and_overrides_dimension_zero(tmp_path):
    env, agent, rows = run_evaluate(tmp_path, policy_override='slow-ee')
    assert agent.calls == 6 and all(r['policy_override'] == 'slow-ee' for r in rows)
    assert all(np.allclose(a, [-1.0, 0.25, -0.5]) for a in env.received)


def test_random_evaluate_is_reproducible_across_runs(tmp_path):
    (tmp_path / 'x').mkdir(); (tmp_path / 'y').mkdir()
    env1, _, _ = run_evaluate(tmp_path / 'x', policy_override='random')
    env2, _, _ = run_evaluate(tmp_path / 'y', policy_override='random')
    assert np.array_equal(np.stack(env1.received), np.stack(env2.received))
