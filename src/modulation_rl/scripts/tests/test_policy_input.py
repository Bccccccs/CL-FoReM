"""SCREEN-028: latency-v1 delay line / action history, dynmap-v1 future-past-freeze, wrapper.

Pure tests need no ROS. Tests marked env_* run the real DynamicObstacleTask and need the analytical
simulator's ROS master (they skip cleanly otherwise; the pipeline log records the in-container run).
"""
import copy
import os
import sys
from types import SimpleNamespace

import numpy as np
import pytest

import modulation.utils  # noqa: F401  (import order workaround, see test_robotenv_mismatch.py)
from policy_input import (PolicyInputTransform, PolicyInputWrapper, DynMapAugmenter, future_positions,
                          positions, wrap_if_needed, SIM_DT, DYN_HORIZON)


def obs(t, dim=4):
    """Distinguishable fake observation: robot = t everywhere, map = t at every pixel."""
    return ([float(t)] * dim, np.full((3, 3, 1), t, dtype=np.float32))


def run(tr, n, action=lambda t: np.array([t, -t, 0.5 * t], dtype=np.float32)):
    out = [tr.reset(obs(0))]
    for t in range(1, n + 1):
        out.append(tr.step(action(t - 1), obs(t)))
    return out


def test_time_step_matches_env_constant():
    from modulation.envs.eeplanner import TIME_STEP_TRAIN
    assert SIM_DT == TIME_STEP_TRAIN


def test_k0_is_identity():
    tr = PolicyInputTransform(0, 0, 0)
    for t, (robot, m) in enumerate(run(tr, 5)):
        assert robot == [float(t)] * 4 and (m == t).all()


@pytest.mark.parametrize('k', [1, 2, 3, 5])
def test_full_latency_start_and_lag(k):
    outs = run(PolicyInputTransform(obs_latency=k), 9)
    for t, (robot, m) in enumerate(outs):
        expect = max(t - k, 0)  # t < k -> initial observation
        assert robot == [float(expect)] * 4 and (m == expect).all(), (t, k)


def test_map_only_latency_keeps_robot_current():
    outs = run(PolicyInputTransform(map_latency=3), 7)
    for t, (robot, m) in enumerate(outs):
        assert robot == [float(t)] * 4
        assert (m == max(t - 3, 0)).all()


def test_full_and_map_latency_combined_uses_larger_for_map():
    tr = PolicyInputTransform(obs_latency=1, map_latency=4)
    assert tr.robot_delay == 1 and tr.map_delay == 4
    for t, (robot, m) in enumerate(run(tr, 8)):
        assert robot == [float(max(t - 1, 0))] * 4 and (m == max(t - 4, 0)).all()


def test_action_history_layout_padding_and_dimension():
    k = 3
    outs = run(PolicyInputTransform(action_history=k), 6)
    assert all(len(r) == 4 + 3 * k for r, _ in outs)
    a = lambda t: np.array([t, -t, 0.5 * t], dtype=np.float32)
    robot0 = outs[0][0]
    assert np.all(robot0[4:] == 0), 'no actions executed yet -> all zero padding'
    robot2 = outs[2][0]  # actions a_0, a_1 executed; oldest first, padded in front
    assert np.array_equal(robot2[4:7], np.zeros(3)) and np.array_equal(robot2[7:10], a(0)) and np.array_equal(robot2[10:13], a(1))
    robot5 = outs[5][0]  # a_2, a_3, a_4
    assert np.array_equal(robot5[4:7], a(2)) and np.array_equal(robot5[10:13], a(4))


def test_latency_plus_history_history_is_relative_to_now_not_to_delayed_obs():
    k = 2
    outs = run(PolicyInputTransform(obs_latency=k, action_history=k), 6)
    a = lambda t: np.array([t, -t, 0.5 * t], dtype=np.float32)
    robot = outs[5][0]
    assert list(robot[:4]) == [3.0] * 4  # o_{5-2}
    assert np.array_equal(robot[4:7], a(3)) and np.array_equal(robot[7:10], a(4))  # a_{t-k}..a_{t-1}


def test_reset_starts_a_fresh_episode():
    tr = PolicyInputTransform(obs_latency=2, action_history=2)
    run(tr, 5)
    robot, m = tr.reset(obs(100))
    assert list(robot[:4]) == [100.0] * 4 and np.all(robot[4:] == 0) and (m == 100).all() and tr.t == 0
    robot, m = tr.step(np.ones(3), obs(101))
    assert list(robot[:4]) == [100.0] * 4, 'stale initial obs, not the previous episode'


def test_transform_does_not_alias_caller_action():
    tr = PolicyInputTransform(action_history=1)
    tr.reset(obs(0))
    a = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    tr.step(a, obs(1))
    a[:] = 9
    assert np.allclose(tr.recent_actions(1)[0], [0.1, 0.2, 0.3])


def test_negative_arguments_rejected():
    with pytest.raises(ValueError):
        PolicyInputTransform(obs_latency=-1)


def test_wrap_if_needed_default_returns_same_env_and_no_tags():
    args = SimpleNamespace(obs_latency_steps=0, map_latency_steps=0, obs_action_history=0,
                           dyn_map_mode='current', dyn_map_horizon=5, dyn_freeze=False)
    env = object()
    out, tags = wrap_if_needed(env, args)
    assert out is env and tags == {}


def test_augmenter_mode_validation():
    with pytest.raises(ValueError):
        DynMapAugmenter('sideways')


# ---------------------------------------------------------------------------
# Obstacle future without env: real DynObstacle objects, shared RandomState
# ---------------------------------------------------------------------------

def make_obstacles(seed=0, n=16):
    from geometry_msgs.msg import Point, Pose, Quaternion
    from modulation.envs.simulator_api import DynObstacle, WorldObjects
    rng = np.random.RandomState(seed)
    values = [-3.5, -1.5, 1.5, 3.5]
    poses = [Pose(Point(x, y, 0), Quaternion(0, 0, 0, 1)) for x in values for y in values]
    return rng, [DynObstacle('dyn_obstacle%d' % i, WorldObjects.dyn_obstacle_sim, pose=p, map_W_meter=10, map_H_meter=10,
                             np_random=rng) for i, p in enumerate(poses[:n])]


def advance(obstacles, steps):
    for _ in range(steps):
        for o in obstacles:
            o.move(SIM_DT)


def test_future_positions_equal_real_future_and_leave_real_state_untouched():
    rng, obstacles = make_obstacles(3)
    state_before = rng.get_state()
    pos_before = positions(obstacles)
    goals_before = [o._goal.copy() for o in obstacles]
    predicted = future_positions(obstacles, DYN_HORIZON)
    # nothing about the real objects or the shared RNG stream changed
    assert all(np.array_equal(a, b) for a, b in zip(state_before[1:], rng.get_state()[1:]))
    assert np.array_equal(pos_before, positions(obstacles))
    assert all(np.array_equal(g, o._goal) for g, o in zip(goals_before, obstacles))
    advance(obstacles, DYN_HORIZON)
    assert np.allclose(predicted, positions(obstacles), atol=0, rtol=0)


def test_default_horizon_is_d56_twenty_steps():
    assert DYN_HORIZON == 20 and DynMapAugmenter('future').horizon == 20


def test_future_positions_exact_through_goal_resampling_events():
    rng, obstacles = make_obstacles(7)
    # make some obstacles hit their goal (and draw new goals from the shared RNG) inside the horizon
    for i, o in enumerate(obstacles[::2]):
        o._goal = o._current_xyz + np.array([0.02 + 0.03 * (i % 4), 0.0, 0.0])
        o.velocity = 0.15
    predicted = future_positions(obstacles, DYN_HORIZON)
    resampled_before = [o._goal.copy() for o in obstacles]
    advance(obstacles, DYN_HORIZON)
    assert not all(np.array_equal(g, o._goal) for g, o in zip(resampled_before, obstacles)), 'test must exercise resampling'
    assert np.allclose(predicted, positions(obstacles), atol=0, rtol=0)


def test_future_positions_zero_steps_is_current():
    _, obstacles = make_obstacles(1)
    assert np.array_equal(future_positions(obstacles, 0), positions(obstacles))


def test_deepcopy_copies_share_one_rng_like_the_originals():
    rng, obstacles = make_obstacles(2)
    copies = copy.deepcopy(obstacles)
    assert len({id(o.np_random) for o in copies}) == 1
    assert copies[0].np_random is not rng


def test_augmenter_target_index_alignment_without_env():
    aug = DynMapAugmenter('past', horizon=5)
    aug._history = [np.full((1, 2), float(j)) for j in range(20)]
    for k, expect in [(0, 0), (1, 0), (5, 0), (6, 0), (7, 1), (12, 6)]:
        aug._k = k
        assert aug.target_positions(None)[0, 0] == expect, k  # observed=max(k-1,0); target=max(observed-5,0)
    fut = DynMapAugmenter('future', horizon=1)
    fut._history = aug._history
    fut._k = 4
    assert fut.target_positions(None)[0, 0] == 4  # observed=3, +1 -> P_4 already in history
    fut0 = DynMapAugmenter('future', horizon=0)
    fut0._history, fut0._k = aug._history, 4
    assert fut0.target_positions(None)[0, 0] == 3  # lag-0 == exactly what the observation shows


# ---------------------------------------------------------------------------
# Real env (needs ROS master + analytical sim)
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def dyn_env_factory():
    try:
        import rospy
        rospy.get_param('/rosdistro')
    except Exception as exc:  # no master
        pytest.skip('ROS master unavailable: %r' % (exc,))
    from pathlib import Path
    from modulation.utils import parse_args, env_creator
    import rospy

    def make(seed=11):
        _, _, config, _ = parse_args(Path(__file__).resolve().parents[1], framework='ray',
                                     raw_args=['--env', 'husky_ur5', '--task', 'dynobstacle', '--world_type', 'sim', '--seed', str(seed)])
        config.update(node_handle='pytest_screen', eval=False)
        os.environ['P0_BIOIK_MAX_ITERATIONS'] = '100'
        for group in ['manipulator', 'whole_body']:
            rospy.set_param('/robot_description_kinematics/' + group + '/kinematics_solver', 'modulation_rl/P0BioIKKinematicsPlugin')
            rospy.set_param('/robot_description_kinematics/' + group + '/random_seed', seed)
            rospy.set_param('/robot_description_kinematics/' + group + '/threads', 1)
        config.update(bioik_random_seed=seed, bioik_threads=1, bioik_mode='fixed', bioik_iterations=100, ik_semantics='p0-ik-budget-v1')
        return env_creator(config)
    return make


def rollout_signature(env, seed, steps, actions):
    env.seed(seed); env.action_space.seed(seed)
    state = env.reset()
    trace = dict(obs=[state], obstacles=[positions(env.unwrapped.map.dyn_obstacles)], reward=[], rng=[])
    for a in actions[:steps]:
        state, reward, done, _ = env.step(a)
        trace['obs'].append(state); trace['reward'].append(reward)
        trace['obstacles'].append(positions(env.unwrapped.map.dyn_obstacles))
        trace['rng'].append(env.unwrapped.map.np_random.get_state()[2])
        if done:
            break
    return trace


def fresh(make, seed, steps, actions, **wrap):
    """Fresh env per rollout: the BioIK solver RNG persists across resets inside one env (that is why
    p0_runner evaluates every episode in a new process), so paired comparisons need a new env."""
    env = make()
    try:
        return rollout_signature(PolicyInputWrapper(env, **wrap) if wrap else env, seed, steps, actions)
    finally:
        env.close()


def test_env_future_and_past_leave_obstacles_rng_reward_and_current_map_unchanged(dyn_env_factory):
    rng = np.random.RandomState(0)
    actions = [np.clip(rng.normal(0, 0.5, 3), -1, 1).astype(np.float32) for _ in range(25)]
    base = fresh(dyn_env_factory, 10000, 25, actions)
    for mode in ('future', 'past'):
        sig = fresh(dyn_env_factory, 10000, 25, actions, dyn_map_mode=mode)
        assert len(sig['obs']) == len(base['obs'])
        for a, b in zip(base['obstacles'], sig['obstacles']):
            assert np.array_equal(a, b), 'real obstacle positions changed by %s map' % mode
        assert base['rng'] == sig['rng'], 'real obstacle RNG stream changed by %s map' % mode
        assert base['reward'] == sig['reward'], 'reward must not depend on the policy-input map'
        for (rob_a, map_a), (rob_b, map_b) in zip(base['obs'], sig['obs']):
            assert np.array_equal(rob_a, rob_b)
            assert (map_b >= map_a).all(), 'union must contain the current map'


def test_env_lag0_union_equals_observation_and_horizon_adds_pixels(dyn_env_factory):
    actions = [np.array([0.2, 0.3, 0.0], dtype=np.float32)] * 12
    plain = fresh(dyn_env_factory, 10001, 12, actions)
    for mode in ('future', 'past'):
        lag0 = fresh(dyn_env_factory, 10001, 12, actions, dyn_map_mode=mode, dyn_map_horizon=0)
        for (_, a), (_, b) in zip(plain['obs'], lag0['obs']):
            assert np.array_equal(a, b), 'lag-0 overlay must equal the observed current map (alignment check)'
    fut = fresh(dyn_env_factory, 10001, 12, actions, dyn_map_mode='future')
    extra = sum(int(b.sum() - a.sum()) for (_, a), (_, b) in zip(plain['obs'], fut['obs']))
    assert extra > 0, 'future overlay should add pixels for moving obstacles'


@pytest.mark.parametrize('horizon', [5, DYN_HORIZON])
def test_env_future_target_positions_equal_recorded_real_positions(dyn_env_factory, horizon):
    actions = [np.array([0.1, 0.2, 0.0], dtype=np.float32)] * (horizon + 6)
    plain = fresh(dyn_env_factory, 10002, horizon + 6, actions)
    assert len(plain['obstacles']) >= horizon + 4, 'episode ended too early for this check'
    env = dyn_env_factory()
    try:
        env.seed(10002); env.action_space.seed(10002)
        env.reset()
        combined = env.unwrapped
        aug = DynMapAugmenter('future', horizon)
        aug._history = [positions(combined.map.dyn_obstacles)]
        aug._k = 0
        assert np.array_equal(aug.target_positions(combined), plain['obstacles'][horizon])  # after reset: P_h
        for i in range(3):
            env.step(actions[i])
            aug._k += 1
            aug._history.append(positions(combined.map.dyn_obstacles))
        # after step 3 the observation shows P_2; future target = P_{2+h}, simulated from live P_3
        assert np.array_equal(aug.target_positions(combined), plain['obstacles'][2 + horizon])
    finally:
        env.close()


def test_env_freeze_keeps_obstacles_still_and_layout_identical(dyn_env_factory):
    actions = [np.array([0.2, 0.3, 0.0], dtype=np.float32)] * 10
    moving = fresh(dyn_env_factory, 10003, 10, actions)
    frozen = fresh(dyn_env_factory, 10003, 10, actions, dyn_freeze=True)
    assert np.array_equal(moving['obstacles'][0], frozen['obstacles'][0]), 'same initial layout for a seed'
    for p in frozen['obstacles'][1:]:
        assert np.array_equal(p, frozen['obstacles'][0])
    assert not np.array_equal(moving['obstacles'][-1], moving['obstacles'][0])


def test_env_latency_wrapper_leaves_reward_and_true_dynamics_unchanged(dyn_env_factory):
    actions = [np.array([0.3, 0.1, -0.2], dtype=np.float32)] * 8
    plain = fresh(dyn_env_factory, 10004, 8, actions)
    late = fresh(dyn_env_factory, 10004, 8, actions, obs_latency=3, action_history=2)
    assert plain['reward'] == late['reward']
    assert all(len(r) == 41 + 6 for r, _ in late['obs'])
    for t, (robot, m) in enumerate(late['obs']):
        src = plain['obs'][max(t - 3, 0)]
        assert np.array_equal(np.asarray(robot[:41], dtype=np.float32), np.asarray(src[0], dtype=np.float32))
        assert np.array_equal(m, src[1])
