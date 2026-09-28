"""STAGE0-028 mismatch-v1: unit tests for RobotEnv._apply_execution_mismatch/_reset_mismatch/seed.

These call the unbound RobotEnv methods against a bare SimpleNamespace standing in for `self`,
since constructing a real RobotEnv requires a live ROS/BioIK/robot_config stack. The methods
under test only touch the private mismatch attributes (never ROS/C++ state), so this exercises
the real production code paths without a simulator.
"""
from collections import deque
from types import SimpleNamespace

import numpy as np
import pytest

# Import order workaround (pre-existing, not introduced by mismatch-v1; reproduces on
# unmodified robotenv.py too): a bare `from modulation.envs.robotenv import RobotEnv` as the
# first native-extension import in the process throws std::bad_cast while loading pybindings
# via modulation.envs's package __init__ (envs -> tasks -> combined_env -> ...). Importing
# modulation.utils first — which is how every real entry point (p0_runner.py, main.py) reaches
# RobotEnv — avoids it; see ENV.md §4 "已知现象" for the same class of native-import-order issue.
import modulation.utils  # noqa: F401
from modulation.envs.robotenv import RobotEnv


def fake_env(**overrides):
    base = dict(_mismatch_delay_queue=deque(), _episode_base_vel_gain=1.0,
                _velocity_ranges=np.array([1.0, 1.0]), learn_torso=False,
                _action_delay_steps=0, _base_vel_gain=1.0, _base_vel_gain_range=None,
                _mismatch_rng=np.random.RandomState(0))
    base.update(overrides)
    return SimpleNamespace(**base)


def test_apply_execution_mismatch_default_is_identity():
    env = fake_env()
    for arr in [np.array([0.3, -0.7]), np.array([0.0, 0.0]), np.array([1.0, -1.0])]:
        out = RobotEnv._apply_execution_mismatch(env, arr)
        np.testing.assert_array_equal(out, arr)
    assert len(env._mismatch_delay_queue) == 0, 'delay_steps=0 must never accumulate a backlog'


def test_apply_execution_mismatch_gain_only_scales_exactly():
    env = fake_env(_episode_base_vel_gain=0.6)
    out = RobotEnv._apply_execution_mismatch(env, np.array([2.0, -4.0]))
    np.testing.assert_array_equal(out, np.array([1.2, -2.4]))


def test_apply_execution_mismatch_delay_queue_order():
    # action_delay_steps=2: queue starts with two zero commands (as reset() would build it).
    env = fake_env(_mismatch_delay_queue=deque([np.zeros(2), np.zeros(2)]))
    cmds = [np.array([1.0, 2.0]), np.array([3.0, 4.0]), np.array([5.0, 6.0]), np.array([7.0, 8.0])]
    outs = [RobotEnv._apply_execution_mismatch(env, c) for c in cmds]
    np.testing.assert_array_equal(outs[0], np.zeros(2))
    np.testing.assert_array_equal(outs[1], np.zeros(2))
    np.testing.assert_array_equal(outs[2], cmds[0])
    np.testing.assert_array_equal(outs[3], cmds[1])
    assert len(env._mismatch_delay_queue) == 2, 'queue depth must stay == action_delay_steps'


def test_apply_execution_mismatch_gain_applied_after_delay_not_before():
    env = fake_env(_mismatch_delay_queue=deque([np.zeros(2)]), _episode_base_vel_gain=0.5)
    out0 = RobotEnv._apply_execution_mismatch(env, np.array([2.0, 4.0]))
    np.testing.assert_array_equal(out0, np.zeros(2))  # delayed zero, gain on zero is still zero
    out1 = RobotEnv._apply_execution_mismatch(env, np.array([6.0, 8.0]))
    # out1 is the delayed cmd0=[2,4] scaled by 0.5, NOT cmd1 scaled
    np.testing.assert_array_equal(out1, np.array([1.0, 2.0]))


def test_apply_execution_mismatch_does_not_mutate_caller_array():
    env = fake_env(_episode_base_vel_gain=0.5)
    cmd = np.array([2.0, 4.0])
    original = cmd.copy()
    RobotEnv._apply_execution_mismatch(env, cmd)
    np.testing.assert_array_equal(cmd, original)


def test_reset_mismatch_builds_zero_queue_of_configured_depth():
    env = fake_env(_action_delay_steps=3, _velocity_ranges=np.array([1.0, 1.0]), learn_torso=False)
    RobotEnv._reset_mismatch(env)
    assert len(env._mismatch_delay_queue) == 3
    for entry in env._mismatch_delay_queue:
        np.testing.assert_array_equal(entry, np.zeros(2))


def test_reset_mismatch_excludes_torso_dimension():
    env = fake_env(_action_delay_steps=1, _velocity_ranges=np.array([1.0, 1.0, 1.0]), learn_torso=True)
    RobotEnv._reset_mismatch(env)
    assert len(env._mismatch_delay_queue) == 1
    np.testing.assert_array_equal(next(iter(env._mismatch_delay_queue)), np.zeros(2))


def test_reset_mismatch_drops_stale_in_flight_command_from_previous_episode():
    env = fake_env(_action_delay_steps=2, _velocity_ranges=np.array([1.0, 1.0]), learn_torso=False)
    RobotEnv._reset_mismatch(env)
    # simulate mid-episode activity leaving a non-zero command in flight
    RobotEnv._apply_execution_mismatch(env, np.array([9.0, 9.0]))
    assert any(np.any(e != 0) for e in env._mismatch_delay_queue)
    RobotEnv._reset_mismatch(env)
    for entry in env._mismatch_delay_queue:
        np.testing.assert_array_equal(entry, np.zeros(2))


def test_reset_mismatch_uses_fixed_gain_when_no_range():
    env = fake_env(_base_vel_gain=0.8, _base_vel_gain_range=None,
                   _mismatch_rng=np.random.RandomState(123))
    for _ in range(3):
        RobotEnv._reset_mismatch(env)
        assert env._episode_base_vel_gain == 0.8


def test_reset_mismatch_samples_gain_range_within_bounds_and_is_rng_deterministic():
    env_a = fake_env(_base_vel_gain_range=(0.6, 1.4), _mismatch_rng=np.random.RandomState(42))
    env_b = fake_env(_base_vel_gain_range=(0.6, 1.4), _mismatch_rng=np.random.RandomState(42))
    RobotEnv._reset_mismatch(env_a)
    RobotEnv._reset_mismatch(env_b)
    assert 0.6 <= env_a._episode_base_vel_gain <= 1.4
    assert env_a._episode_base_vel_gain == env_b._episode_base_vel_gain, 'same RNG seed must reproduce the same sampled gain'


def test_reset_mismatch_gain_range_varies_across_episodes_with_same_rng_stream():
    env = fake_env(_base_vel_gain_range=(0.6, 1.4), _mismatch_rng=np.random.RandomState(7))
    RobotEnv._reset_mismatch(env)
    first = env._episode_base_vel_gain
    RobotEnv._reset_mismatch(env)
    second = env._episode_base_vel_gain
    assert first != second, 'consecutive episodes on the same env must draw fresh gains, not repeat'


def test_seed_derives_independent_mismatch_rng_without_touching_np_random():
    from gym.utils import seeding
    calls = []
    env = SimpleNamespace(_robot_cpp=SimpleNamespace(set_rng=lambda s: calls.append(s)))
    RobotEnv.seed(env, 10007)
    expected_np_random, expected_strong_seed = seeding.np_random(10007)
    # np_random must match exactly what plain gym seeding would produce for this seed: the
    # mismatch RNG construction must not consume/perturb it.
    assert env.np_random.randint(0, 2**31, size=8).tolist() == expected_np_random.randint(0, 2**31, size=8).tolist()
    assert calls == [expected_strong_seed]
    assert isinstance(env._mismatch_rng, np.random.RandomState)


def test_seed_mismatch_rng_is_deterministic_per_seed_and_differs_across_seeds():
    env_a = SimpleNamespace(_robot_cpp=SimpleNamespace(set_rng=lambda s: None))
    env_b = SimpleNamespace(_robot_cpp=SimpleNamespace(set_rng=lambda s: None))
    RobotEnv.seed(env_a, 555)
    RobotEnv.seed(env_b, 555)
    draw_a = env_a._mismatch_rng.uniform(0, 1, size=5).tolist()
    draw_b = env_b._mismatch_rng.uniform(0, 1, size=5).tolist()
    assert draw_a == draw_b, 'same episode seed must reproduce the same mismatch RNG stream'

    env_c = SimpleNamespace(_robot_cpp=SimpleNamespace(set_rng=lambda s: None))
    RobotEnv.seed(env_c, 556)
    draw_c = env_c._mismatch_rng.uniform(0, 1, size=5).tolist()
    assert draw_c != draw_a, 'different episode seeds must not collide onto the same mismatch RNG stream'


def test_seed_mismatch_rng_independent_of_bioik_strong_seed_stream():
    """The mismatch RNG must be a distinct stream from the one implicitly available via
    strong_seed/set_rng, not merely a different object wrapping the same numbers."""
    env = SimpleNamespace(_robot_cpp=SimpleNamespace(set_rng=lambda s: None))
    RobotEnv.seed(env, 999)
    mismatch_draw = env._mismatch_rng.uniform(0, 1, size=5).tolist()
    same_seed_direct = np.random.RandomState(999).uniform(0, 1, size=5).tolist()
    assert mismatch_draw != same_seed_direct


def test_init_gain_range_and_delay_assertions_match_p0_runner_cli_validation(tmp_path):
    """RobotEnv.__init__ asserts 0 < lo <= hi and action_delay_steps >= 0 (can't unit-construct
    a full RobotEnv without ROS/BioIK/robot_config; exercised end-to-end by the fixed100
    regression gate). This test pins down that the same bounds are enforced earlier, at the
    p0_runner.py CLI layer, so a bad value is rejected before any container/ROS process starts."""
    import subprocess, sys
    from pathlib import Path
    runner = Path(__file__).resolve().parents[1] / 'p0_runner.py'
    for i, extra_args in enumerate([['--base-vel-gain-range', '1.5', '0.5'],
                                    ['--base-vel-gain-range', '0.0', '1.0'],
                                    ['--action-delay-steps', '-1']]):
        out = tmp_path / f'does-not-run-{i}'
        result = subprocess.run([sys.executable, str(runner), 'eval', '--output', str(out),
                                 '--checkpoint', 'x', '--seeds', 'x'] + extra_args,
                                capture_output=True, text=True, timeout=30)
        assert result.returncode != 0, extra_args
        assert not out.exists()
