"""FoReM Task3 environment interface around the migrated reference core (modulation_rl).

    env = Task3Env(seed=0)               # builds the reference SimpleObstacleTask for husky_ur5 in the gazebo world
    obs = env.reset(seed=7)              # obs = (robot_state[41] float32, local_map[120,120,1] float32)
    obs, reward, done, info = env.step(a)  # a: float vector (3,), finite, in [-1, 1] -- classic 4-tuple like the reference

Contract (config/task3/task_contract.yaml): the action is [vel_norm, base_rot, base_vel] (NOT six arm joints); the arm joint
values inside the observation are the IK/PLANNED values; the Gazebo-measured arm joints are reported separately in
info['actual_arm_joints']; the base pose in the observation comes from the pose source (gazebo_reference now, an estimator in
Task4). Gazebo truth is available ONLY through evaluation_truth() and never enters observations or rewards.

Import order: `ray` MUST be imported before `torch`/`pybindings` (dual libpython 3.8/3.10 in the ROS libraries makes the
pybind modules abort with std::bad_cast otherwise; measured in task3.2). This module does it first.
"""
import ray  # noqa: F401  -- must stay the first heavy import
import torch  # noqa: F401

import copy
import hashlib
import json
import math
import os
import sys
import threading
from pathlib import Path

import numpy as np
import yaml

FOREM_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = FOREM_ROOT / "src" / "modulation_rl" / "scripts"
CONFIG_DIR = FOREM_ROOT / "config" / "task3"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

ACTION_DIM = 3
ACTION_NAMES = ("vel_norm", "base_rot", "base_vel")
ROBOT_STATE_DIM = 41
LOCAL_MAP_SHAPE = (120, 120, 1)
# robot_state field map (index ranges); `origin` says whether a field reflects the plan or measured feedback
OBS_FIELDS = (
    ("relative_gripper_tf", 0, 7, "planned_arm_and_actual_base"),
    ("next_gripper_tf_rel", 7, 14, "plan"),
    ("ee_velocities_rel", 14, 21, "plan"),
    ("goal_relative_to_base", 21, 28, "plan_and_actual_base"),
    ("joint_values_scaled", 28, 34, "PLANNED_ik_joints_not_actual_feedback"),
    ("wrist_to_goal_relative_to_base", 34, 37, "plan_and_actual_base"),
    ("in_selfcollision", 37, 38, "planned_ik_state"),
    ("previous_action_mean", 38, 41, "policy_actions"),
)
POSE_SOURCE = "gazebo_reference"


def validate_action(action):
    """Reject anything that is not a finite float vector of shape (3,) inside [-1, 1]; returns float32 (clipped by 1e-6 slack)."""
    a = np.asarray(action, dtype=np.float64)
    if a.shape != (ACTION_DIM,):
        raise ValueError(f"action must have shape ({ACTION_DIM},), got {a.shape}")
    if not np.all(np.isfinite(a)):
        raise ValueError("action contains non-finite values")
    if np.any(np.abs(a) > 1.0 + 1e-6):
        raise ValueError("action outside [-1, 1]")
    return np.clip(a, -1.0, 1.0).astype(np.float32)


def load_env_config(path=None, overrides=None):
    path = Path(path) if path else CONFIG_DIR / "task_contract.yaml"
    contract = yaml.safe_load(open(path, encoding="utf-8"))
    cfg = copy.deepcopy(contract["env_config"])
    cfg.update(overrides or {})
    return cfg, contract


def spec_hash(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _r(v, nd=6):
    return [round(float(x), nd) for x in v]


class Task3Env:
    def __init__(self, seed=0, task_contract=None, overrides=None):
        cfg, self.contract = load_env_config(task_contract, overrides)
        cfg["seed"] = int(seed)
        self.cfg = cfg
        from modulation.utils import env_creator, episode_is_success   # imports pybindings, ROS, ray, wandb ...
        self._episode_is_success = episode_is_success
        self.env = env_creator(cfg)
        self.unwrapped_env = self.env.unwrapped
        self.action_space = self.env.action_space
        self.observation_space = self.env.observation_space
        self.pose_source = "analytical_sim" if cfg["world_type"] == "sim" else POSE_SOURCE
        self._episode = None
        self._steps = 0
        self._last_sim_time = None
        self._invalid_reason = None      # set when the simulation clock moved backwards: only reset() clears it

    # ---------------------------------------------------------------- spec / truth (evaluation only)
    def _capture_spec(self, seed):
        e = self.unwrapped_env
        ro = e._robot.get_robot_obs()
        planner = e._ee_planner
        objs = []
        for o in e.map.get_scene_objects():
            wo = o.world_object
            p = o.pose() if callable(o.pose) else o.pose
            objs.append(dict(name=o.name, geometry=str(getattr(wo, "geometry", "")), size=_r([wo.x, wo.y, wo.z]),
                             pose=_r([p.position.x, p.position.y, p.position.z,
                                      p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w])))
        spec = dict(seed=seed, base_tf=_r(ro.base_tf), arm_joints_planned=_r(ro.joint_values),
                    goal_tip=_r(planner.gripper_goal_tip), goal_wrist=_r(planner.gripper_goal_wrist),
                    map_size_m=_r([e.map._map_W_meter, e.map._map_H_meter]), obstacles=objs)
        spec["hash"] = spec_hash({k: v for k, v in spec.items() if k != "hash"})
        return spec

    def evaluation_truth(self):
        """Gazebo model pose (x, y, z, qx, qy, qz, qw) of husky_ur5 -- EVALUATION ONLY, never an observation.

        Always a FRESH blocking read of /gazebo/model_states: a cached subscriber was found to deliver a pre-reset message (robot still at the
        out-of-frame spot x=30) for a whole episode after env.reset() (the C++ reset holds the GIL; task3.5 t3.5-int-r2)."""
        import rospy
        from gazebo_msgs.msg import ModelStates
        m = rospy.wait_for_message("/gazebo/model_states", ModelStates, timeout=5)
        p = m.pose[m.name.index("husky_ur5")]
        return (rospy.get_time(), (p.position.x, p.position.y, p.position.z, p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w))

    def gazebo_model_names(self):
        import rospy
        from gazebo_msgs.msg import ModelStates
        return list(rospy.wait_for_message("/gazebo/model_states", ModelStates, timeout=5).name)

    # ---------------------------------------------------------------- gym-like API
    def reset(self, seed=None, episode_spec=None):
        """Real reset (Gazebo set_model_state, new obstacle field, arm back to the start pose, counters/previous action cleared).

        seed: reseeds the env/map/robot RNGs right before the reset (same seed => same drawn episode).
        episode_spec: optional spec from a previous reset(); the freshly drawn episode must hash-match it, else RuntimeError
        (a spec is a verification handle, the draw itself is seed-determined)."""
        if seed is not None:
            self.env.seed(int(seed))
        import rospy
        obs = self.env.reset()
        self._steps = 0
        self._last_sim_time = rospy.get_time()
        self._invalid_reason = None
        self._episode = self._capture_spec(seed)
        if episode_spec is not None and episode_spec.get("hash") != self._episode["hash"]:
            raise RuntimeError("drawn episode does not match the requested episode_spec")
        return self._to_obs(obs)

    @property
    def episode_spec(self):
        return copy.deepcopy(self._episode)

    def step(self, action):
        a = validate_action(action)
        if self._episode is None:
            raise RuntimeError("step() before reset()")
        import rospy
        if self._invalid_reason:
            raise RuntimeError(f"episode invalid ({self._invalid_reason}); call reset()")
        now = rospy.get_time()
        if self._last_sim_time is not None and now < self._last_sim_time - 1e-3:
            self._invalid_reason = f"simulation clock went backwards ({self._last_sim_time:.3f} -> {now:.3f})"
            raise RuntimeError(f"episode invalid ({self._invalid_reason}); call reset()")
        obs, reward, done, info = self.env.step(a)
        self._last_sim_time = rospy.get_time()
        self._steps += 1
        info = dict(info)
        truncated = bool(info.get("max_close_steps", False))
        info["truncated"] = truncated
        info["terminated"] = bool(done and not truncated)
        if done:
            info["success"] = bool(self._episode_is_success(info["nr_kin_failures"], info["nr_base_collisions"], info["ee_done"]))
        ro = self.unwrapped_env.prev_robot_obs                  # the RobotObs this step produced (planned arm, TF base)
        info["planned_arm_joints"] = _r(ro.joint_values, 9)
        try:
            info["actual_arm_joints"] = _r(self.unwrapped_env._robot.get_joint_values_world(), 9)   # controller/joint_states feedback
        except Exception as e:  # noqa: BLE001 -- feedback read failure is reported, never replaced by the plan
            info["actual_arm_joints"] = None
            info["actual_arm_joints_error"] = repr(e)
        info["obs_arm_joint_labels"] = "planned"
        info["base_tf_obs"] = _r(ro.base_tf, 9)
        info["pose_source"] = self.pose_source
        return self._to_obs(obs), float(reward), bool(done), info

    @staticmethod
    def _to_obs(obs):
        vec, local_map = obs
        v = np.asarray(vec, dtype=np.float32)
        m = np.asarray(local_map, dtype=np.float32)
        if v.shape != (ROBOT_STATE_DIM,) or m.shape != LOCAL_MAP_SHAPE:
            raise RuntimeError(f"observation shape contract violated: {v.shape}, {m.shape}")
        if not (np.all(np.isfinite(v)) and np.all(np.isfinite(m))):
            raise RuntimeError("non-finite observation")
        return v, m

    def close(self):
        self.env.close()


def module_provenance():
    """Where the imported core modules really come from (shadow-import evidence)."""
    import importlib
    out = {}
    for n in ("modulation", "modulation.utils", "modulation.envs.robotenv", "modulation.envs.tasks", "sac", "model", "replay_memory",
              "stable_baselines3", "pybindings", "pybindings_robots"):
        m = sys.modules.get(n) or importlib.import_module(n)
        out[n] = os.path.realpath(getattr(m, "__file__", "") or "")
    return out
