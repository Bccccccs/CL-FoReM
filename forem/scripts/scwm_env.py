"""FoReM Task4 environment wrapper (SCWM-style feedback study).

ScwmEnv wraps Task3Env (reference Husky+UR5 SimpleObstacle chain, Gazebo base feedback through TF, local laser costmap) and ADDS
measurements without touching observation, reward, done or action semantics:

  per step     sim times (before/after the env.step call, i.e. t_cmd / t_next), wall time, previous obs time (t_obs), planned vs actual
               arm joints, TF-based achieved gripper pose, the planner/IK residuals the env already reports;
  at episode   a fresh Gazebo LinkStates read of husky_ur5::ur5_wrist_3_link times the static wrist->gripper transform = the INDEPENDENT physical
  end          gripper pose; physical success = pos < 0.025 m, 1-(qa.qb)^2 < 0.05 against the planner goal (same numbers as the internal
               _is_done, SRC0108), 0 kin failures, 0 base collisions. Evaluation/reporting only: it never enters reward, done or replay.

`import ray` must precede torch/pybindings (task3_env.py does it). Needs a running simulation.
"""
import json
import math
import time
import xml.etree.ElementTree as ET

import numpy as np

import task3_env as T3   # noqa: E402  (imports ray first)

PHYS_LINK = "husky_ur5::ur5_wrist_3_link"
SUCCESS_POS_M = 0.025
SUCCESS_ROT = 0.05


def _quat_mul_rot(q):
    from scipy.spatial.transform import Rotation
    return Rotation.from_quat(q)


class ScwmEnv:
    def __init__(self, seed=0, overrides=None, window_s=None, unthrottle=True, fast_reset=False, world="gazebo", max_close_steps=500):
        """window_s=None: reference real-time stepping. window_s=W: fixed-sim-window stepping (scwm_clock.FixedWindowClock)."""
        self.world = world
        if world not in ("sim", "gazebo"):
            raise ValueError("world must be sim or gazebo")
        import rospy
        if world == "sim":
            rospy.set_param("/forem/force_rectangle_obstacles", True)
        else:
            assert not rospy.get_param("/forem/force_rectangle_obstacles", False), "Gazebo requires force_rectangle_obstacles absent or False"
        if world == "sim":
            overrides = dict(overrides or {}, world_type="sim", init_controllers=False, max_close_steps=max_close_steps)
        self.base = T3.Task3Env(seed=seed, overrides=overrides)
        self.clock = None
        self.pacing = None
        if fast_reset and world == "gazebo":
            from scwm_clock import PacingControl
            self.pacing = PacingControl()
        if window_s and world == "gazebo":
            from scwm_clock import FixedWindowClock
            self.clock = FixedWindowClock(window_s, unthrottle=unthrottle)
        self.action_space = self.base.action_space
        self.observation_space = self.base.observation_space
        self.epoch = 0                    # increments at every reset; stamps every transition (data-causality guard)
        self.episode_id = -1
        self.step_in_episode = 0
        self._t_obs = None
        self._wrist_to_gripper = None
        self._get_link = None

    # ---- static wrist->gripper transform from the URDF (Gazebo reduced the fixed joints into wrist_3) -------------
    def _static_transform(self):
        if self._wrist_to_gripper is not None:
            return self._wrist_to_gripper
        import rospy
        from scipy.spatial.transform import Rotation
        root = ET.fromstring(rospy.get_param("/robot_description"))
        joints = {j.find("child").get("link"): j for j in root.findall("joint")}
        chain, n = [], "gripper_base_link"
        while n != "ur5_wrist_3_link":
            j = joints[n]
            if j.get("type") != "fixed":
                raise RuntimeError("wrist-to-gripper path must be static")
            chain.insert(0, j)
            n = j.find("parent").get("link")
        Tm = np.eye(4)
        for j in chain:
            o = j.find("origin")
            xyz = [float(v) for v in o.get("xyz", "0 0 0").split()]
            rpy = [float(v) for v in o.get("rpy", "0 0 0").split()]
            a = np.eye(4)
            a[:3, :3] = Rotation.from_euler("xyz", rpy).as_matrix()
            a[:3, 3] = xyz
            Tm = Tm @ a
        self._wrist_to_gripper = Tm
        return Tm

    def physical_gripper_pose(self, timeout=5.0):
        """(sim_receipt_time, [x,y,z,qx,qy,qz,qw]) of gripper_base_link from a FRESH Gazebo LinkStates message (independent of TF/joint states/the planner). LinkStates has no header: the sim time of receipt is the best available stamp."""
        import rospy
        from gazebo_msgs.srv import GetLinkState
        from scipy.spatial.transform import Rotation
        # the service answers with the CURRENT engine state, also while physics is paused (a topic read would block)
        if self._get_link is None:
            rospy.wait_for_service("/gazebo/get_link_state", timeout=timeout)
            self._get_link = rospy.ServiceProxy("/gazebo/get_link_state", GetLinkState)
        resp = self._get_link(link_name=PHYS_LINK, reference_frame="world")
        if not resp.success:
            raise RuntimeError("get_link_state failed: " + resp.status_message)
        t = rospy.get_time()
        p = resp.link_state.pose
        a = np.eye(4)
        a[:3, 3] = [p.position.x, p.position.y, p.position.z]
        a[:3, :3] = Rotation.from_quat([p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w]).as_matrix()
        g = a @ self._static_transform()
        return t, g[:3, 3].tolist() + Rotation.from_matrix(g[:3, :3]).as_quat().tolist()

    def sim_time(self):
        import rospy
        return rospy.get_time()

    def goal_wrist(self):
        return [float(x) for x in self.base.unwrapped_env._ee_planner.gripper_goal_wrist]

    @staticmethod
    def pose_errors(pose, goal):
        d = float(np.linalg.norm(np.asarray(pose[:3]) - np.asarray(goal[:3])))
        qa, qb = np.asarray(pose[3:7], float), np.asarray(goal[3:7], float)
        na, nb = np.linalg.norm(qa), np.linalg.norm(qb)
        if not (math.isfinite(na) and math.isfinite(nb)) or na < 0.5 or nb < 0.5:
            return d, float("nan")
        return d, float(1.0 - (qa.dot(qb) / (na * nb)) ** 2)

    # ---- gym-like API ---------------------------------------------------------------------------------------------
    def reset(self, seed=None, episode_spec=None):
        import rospy
        if self.clock:
            self.clock._unpause()       # the C++ reset and the map/scene spawn need simulation time to pass
        if self.pacing:
            self.pacing.unthrottle()    # reset has no policy in the loop: run the identical sim-time sequence faster in wall time
        try:
            obs = self.base.reset(seed=seed, episode_spec=episode_spec)
        finally:
            if self.pacing:
                self.pacing.restore()
        if self.clock:
            self.clock.pause()
        self.epoch += 1
        self.episode_id += 1
        self.step_in_episode = 0
        self._t_obs = rospy.get_time()
        return obs

    @property
    def episode_spec(self):
        return self.base.episode_spec

    def step(self, action):
        import rospy
        if self.clock:
            self.clock.advance()        # previous commands act for exactly W sim seconds, then physics pauses again
        t_cmd = rospy.get_time()
        w0 = time.perf_counter()
        obs, reward, done, info = self.base.step(action)
        w1 = time.perf_counter()
        t_next = rospy.get_time()
        info = dict(info)
        info["scwm"] = dict(epoch=self.epoch, episode_id=self.episode_id, step_in_episode=self.step_in_episode,
                            t_obs=self._t_obs, t_cmd=t_cmd, t_next=t_next, env_step_wall_s=w1 - w0)
        meta = dict(episode_id=self.episode_id, step_in_episode=self.step_in_episode, epoch=self.epoch, t_obs=self._t_obs,
                    t_cmd=t_cmd, t_next=t_next, done=bool(done))
        self.step_in_episode += 1
        self._t_obs = t_next
        if done:
            info["physical"] = self.physical_outcome(info)
        return obs, reward, done, info, meta

    def physical_outcome(self, info):
        if self.world == "sim":
            return dict(valid=False, success=None, reason="sim: no physics")
        out = dict(valid=False)
        try:
            t, pose = self.physical_gripper_pose()
            goal = self.goal_wrist()
            d, r = self.pose_errors(pose, goal)
            ok_pose = math.isfinite(d) and math.isfinite(r)
            out.update(valid=ok_pose, pos_err_m=d, rot_err=r, t_receipt=t, pose=pose, goal_wrist=goal)
            out["success"] = bool(ok_pose and d < SUCCESS_POS_M and r < SUCCESS_ROT
                                  and info.get("nr_kin_failures", 1) == 0 and info.get("nr_base_collisions", 1) == 0)
        except Exception as e:  # noqa: BLE001 -- missing feedback is reported, never replaced by the plan
            out["error"] = repr(e)
            out["success"] = False
        return out

    def close(self):
        if self.clock:
            try:
                self.clock._unpause()
                self.clock.restore_pacing()
            except Exception:   # noqa: BLE001 -- best effort on shutdown
                pass
        self.base.close()
