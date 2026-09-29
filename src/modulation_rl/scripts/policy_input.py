"""SCREEN-028: policy-input transforms, all default off (latency-v1, dynmap-v1).

Only what the *policy sees* is changed. Reward, termination, collision and IK inside the env keep
using the true current state, because the wrapper sits outside the env and only rewrites the
observation tuple it returns.

latency-v1 (PolicyInputTransform)
  --obs-latency-steps k   policy at step t sees the full observation of step t-k (t<k: initial obs).
  --map-latency-steps m   only local_map is delayed by m; robot_state stays current. If both are
                          given, robot_state is delayed by k and local_map by max(k, m).
  --obs-action-history h  append the h most recent executed actions a_{t-h}..a_{t-1} (oldest first,
                          zero padded in front) to robot_state (3h extra dims).

dynmap-v1 (DynMapAugmenter, dynObstacle task only)
  --dyn-map-mode future|past  local_map = OR(current map, map of the obstacles h=20 steps (2.0 s, D56) ahead/behind)
  --dyn-freeze                obstacles stop (velocity 0) after every reset, for the harm test.
  Alignment: CombinedEnv.step() renders the observation *before* map.update() moves the obstacles,
  so the obstacles the policy sees after step k are P_{k-1} (P_0 right after reset). "Current" is
  defined as exactly that; future/past are P_{c+h}/P_{c-h} with c = max(k-1, 0). The future is
  produced by deep-copying the whole obstacle list (shared memo => one copied RandomState) and
  advancing the copy, so the real obstacles' positions and RNG stream are never touched.
"""
import copy
from collections import deque

import gym
import numpy as np
from gym import spaces

ROBOT_DIM = 41
ACTION_DIM = 3
SIM_DT = 0.1  # modulation.envs.eeplanner.TIME_STEP_TRAIN, asserted equal in tests
DYN_HORIZON = 20  # D56: 2.0 s (D54 originally registered 5 steps; revised before any D-line data existed)


class PolicyInputTransform:
    """Pure (no env, no ROS) delay line + action history over (robot_state, local_map) tuples."""

    def __init__(self, obs_latency=0, map_latency=0, action_history=0):
        if min(obs_latency, map_latency, action_history) < 0:
            raise ValueError('latency/history must be >= 0')
        self.obs_latency, self.map_latency, self.action_history = int(obs_latency), int(map_latency), int(action_history)
        self.robot_delay = self.obs_latency
        self.map_delay = max(self.obs_latency, self.map_latency)
        self.max_delay = self.map_delay
        self._obs = deque(maxlen=self.max_delay + 1)
        self._actions = deque(maxlen=max(self.action_history, self.max_delay, 1))
        self.t = 0

    def reset(self, obs):
        self._obs.clear()
        self._actions.clear()
        self.t = 0
        self._obs.append(obs)
        return self._emit()

    def step(self, action, obs):
        self._actions.append(np.asarray(action, dtype=np.float32).copy())
        self._obs.append(obs)
        self.t += 1
        return self._emit()

    def raw(self, delay):
        """Raw (undelayed-by-us) observation `delay` steps before now, clamped to the initial obs."""
        return self._obs[len(self._obs) - 1 - min(int(delay), self.t)]

    def recent_actions(self, n):
        """Actions a_{t-n}..a_{t-1}, oldest first, zero-padded in front; shape (n, ACTION_DIM)."""
        out = np.zeros((n, ACTION_DIM), dtype=np.float32)
        have = list(self._actions)[-n:] if n else []
        if have:
            out[n - len(have):] = np.stack(have)
        return out

    def _emit(self):
        robot = self.raw(self.robot_delay)[0]
        local_map = self.raw(self.map_delay)[1]
        if self.action_history:
            robot = np.concatenate([np.asarray(robot, dtype=np.float32),
                                    self.recent_actions(self.action_history).reshape(-1)])
        return robot, local_map


# ---------------------------------------------------------------------------
# dynmap-v1
# ---------------------------------------------------------------------------

class GhostObstacle:
    """Minimal stand-in for a SpawnObject: SceneMap.add_shape only reads .pose and .world_object."""

    def __init__(self, x, y, world_object):
        from geometry_msgs.msg import Point, Pose, Quaternion
        self.pose = Pose(Point(float(x), float(y), 0.0), Quaternion(0., 0., 0., 1.))
        self.world_object = world_object


def positions(obstacles):
    return np.array([[o._current_xyz[0], o._current_xyz[1]] for o in obstacles], dtype=np.float64).reshape(-1, 2)


def future_positions(obstacles, steps, dt=SIM_DT):
    """Positions after `steps` more map updates, computed on deep copies (exact, side-effect free)."""
    if steps <= 0:
        return positions(obstacles)
    copies = copy.deepcopy(list(obstacles))
    for _ in range(steps):
        for obstacle in copies:
            obstacle.move(dt)
    return positions(copies)


def render_extra_map(combined, base_tf, xy):
    """Local map (same crop/rotation/binarization as the real observation) of only the given
    obstacle positions, drawn like the real floorplan draws them (outline, fill_object=False)."""
    world_map = combined.map
    obstacle_type = world_map.dyn_obstacles[0].world_object
    image = world_map._floorplan_img_orig.copy()
    for x, y in xy:
        world_map.add_shape(image, GhostObstacle(x, y, obstacle_type), fill_object=False)
    saved = world_map._floorplan_img
    world_map._floorplan_img = image
    try:
        return combined.get_local_map(base_tf)
    finally:
        world_map._floorplan_img = saved


class DynMapAugmenter:
    def __init__(self, mode='current', horizon=DYN_HORIZON, freeze=False):
        if mode not in ('current', 'future', 'past'):
            raise ValueError('dyn map mode must be current/future/past, got %r' % (mode,))
        if horizon < 0:
            raise ValueError('horizon must be >= 0')
        self.mode, self.horizon, self.freeze = mode, int(horizon), bool(freeze)
        self._history = []
        self._k = 0

    @staticmethod
    def _obstacles(combined):
        obstacles = getattr(combined.map, 'dyn_obstacles', None)
        if not obstacles:
            raise RuntimeError('dynmap-v1 requires the dynObstacle task (map has no dyn_obstacles)')
        return obstacles

    def on_reset(self, combined, obs):
        obstacles = self._obstacles(combined)
        if self.freeze:
            # Velocity is drawn (from the shared RNG) at obstacle construction, before this point, so
            # the layout, start and goal of a seed are identical to the moving case (paired harm test).
            for obstacle in obstacles:
                obstacle.velocity = 0.0
        self._k = 0
        self._history = [positions(obstacles)]
        return self._augment(combined, obs)

    def on_step(self, combined, obs):
        self._k += 1
        self._history.append(positions(self._obstacles(combined)))
        return self._augment(combined, obs)

    def target_positions(self, combined):
        """Obstacle positions to overlay for the current observation (None for mode 'current')."""
        if self.mode == 'current':
            return None
        k = self._k
        observed = max(k - 1, 0)  # time index of the obstacles present in the observation
        if self.mode == 'past':
            return self._history[max(observed - self.horizon, 0)]
        target = observed + self.horizon
        if target <= k:
            return self._history[target]
        return future_positions(self._obstacles(combined), target - k)

    def _augment(self, combined, obs):
        xy = self.target_positions(combined)
        if xy is None:
            return obs
        extra = render_extra_map(combined, combined.get_robot_obs().base_tf, xy)
        return obs[0], np.logical_or(obs[1], extra)


class PolicyInputWrapper(gym.Wrapper):
    """Outermost wrapper, only created when at least one policy-input switch is on."""

    def __init__(self, env, obs_latency=0, map_latency=0, action_history=0,
                 dyn_map_mode='current', dyn_map_horizon=DYN_HORIZON, dyn_freeze=False):
        super().__init__(env)
        self.transform = PolicyInputTransform(obs_latency, map_latency, action_history)
        self.dynmap = (DynMapAugmenter(dyn_map_mode, dyn_map_horizon, dyn_freeze)
                       if (dyn_map_mode != 'current' or dyn_freeze) else None)
        if action_history:
            robot_space, map_space = env.observation_space[0], env.observation_space[1]
            self.observation_space = spaces.Tuple([
                spaces.Box(low=-100, high=100, shape=[robot_space.shape[0] + ACTION_DIM * action_history], dtype=np.float32),
                map_space])

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        if self.dynmap is not None:
            obs = self.dynmap.on_reset(self.env.unwrapped, obs)
        return self.transform.reset(obs)

    def step(self, action, **kwargs):
        obs, reward, done, info = self.env.step(action, **kwargs)
        if self.dynmap is not None:
            obs = self.dynmap.on_step(self.env.unwrapped, obs)
        return self.transform.step(action, obs), reward, done, info


def wrap_if_needed(env, args):
    """Returns (env, active_semantics_config). env is returned unchanged when everything is default."""
    latency = (args.obs_latency_steps, args.map_latency_steps, args.obs_action_history)
    dyn = (args.dyn_map_mode, args.dyn_freeze)
    tags = {}
    if any(latency):
        tags.update(obs_latency_steps=args.obs_latency_steps, map_latency_steps=args.map_latency_steps,
                    obs_action_history=args.obs_action_history, latency_semantics='latency-v1')
    if args.dyn_map_mode != 'current' or args.dyn_freeze:
        tags.update(dyn_map_mode=args.dyn_map_mode, dyn_map_horizon=args.dyn_map_horizon,
                    dyn_freeze=bool(args.dyn_freeze), dynmap_semantics='dynmap-v1')
    if not tags:
        return env, tags
    return PolicyInputWrapper(env, obs_latency=args.obs_latency_steps, map_latency=args.map_latency_steps,
                              action_history=args.obs_action_history, dyn_map_mode=args.dyn_map_mode,
                              dyn_map_horizon=args.dyn_map_horizon, dyn_freeze=args.dyn_freeze), tags
