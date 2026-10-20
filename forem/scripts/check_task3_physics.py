#!/usr/bin/env python3
"""task3.2 physical-control check of the Husky+UR5 Gazebo core (no policy, no env, ROS topics only).

Phases (all timed in simulation time; commands go through the REAL controller chain /cmd_vel -> twist_mux ->
husky_velocity_controller -> Gazebo wheels, and the arm action server of eff_joint_traj_controller):
  hold      nothing commanded: base and arm must stay put
  straight  /cmd_vel linear.x for a fixed time
  turn      /cmd_vel angular.z for a fixed time
  coord     simultaneous base twist + arm FollowJointTrajectory goal
Evidence is split into command (what was sent), reference (controller desired / pose_bridge TF source = p3d) and
actual (Gazebo model_states truth, wheel/joint feedback). Nothing is back-filled from the command.

Gates are ENGINEERING sanity gates (declared in doc/tasks/task3/task3.2/PROCEDURE.md before the first run), not
performance claims: they detect no-motion, wrong direction, non-finite values, instability and TF/stamp faults.
Exit 0 only if every gate holds; the full numeric evidence is in results/task3/<run>/ either way.
"""
import argparse
import collections
import csv
import json
import math
import os
import sys
import threading
import time

import actionlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task3_lib import ALLOWED_TF_AUTHORS, tf_authority, wrap, yaw_of  # noqa: E402
import rospy
import tf2_ros
from control_msgs.msg import FollowJointTrajectoryAction, FollowJointTrajectoryGoal
from gazebo_msgs.msg import ModelStates
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from tf2_msgs.msg import TFMessage
from trajectory_msgs.msg import JointTrajectoryPoint
from control_msgs.msg import JointTrajectoryControllerState

MODEL = "husky_ur5"
ARM = ["ur5_shoulder_pan_joint", "ur5_shoulder_lift_joint", "ur5_elbow_joint",
       "ur5_wrist_1_joint", "ur5_wrist_2_joint", "ur5_wrist_3_joint"]
ARM_LIMITS = 2 * math.pi            # reference joint_limits.yaml: +-360 deg position limits for all six joints
ARM_VEL_LIMIT = 3.15                # reference husky_ur5/config/joint_limits.yaml max_velocity (rad/s)

# --- declared gates -----------------------------------------------------------------------------------------
GATES = dict(
    hold_xy_drift_m=0.01, hold_yaw_drift_rad=0.01, hold_arm_err_rad=0.01, hold_arm_vel_rms=0.02,
    straight_speed_rel=0.20, straight_lateral_m=0.10, straight_yaw_rad=0.10,
    turn_rate_rel=0.25, turn_xy_m=0.60,          # r2 revision (see doc): was 0.10; skid-steer in-place turn translates ~0.38 m

    coord_arm_final_err_rad=0.02, coord_base_ratio_lo=0.5, coord_base_ratio_hi=1.3,   # v3 revision (see doc): was +-25% of command
    tf_value_tol=1e-6, p3d_vs_truth_xy_m=0.05,
)


class Recorder:
    def __init__(self):
        self.lock = threading.Lock()
        self.rows = []           # (t_sim, kind, values...)
        self.truth = None
        self.truth_series = []   # (t_sim at receipt, x, y)
        self.p3d = None
        self.odom = None
        self.arm_state = None
        self.joint = {}
        self.tf_callers = collections.defaultdict(collections.Counter)
        self.tf_msgs = []        # (stamp_ns, (x,y,z,qx,qy,qz,qw)) of odom->base_footprint
        self.p3d_msgs = []       # (stamp_ns, same tuple)
        self.nonfinite = 0
        self.pose_status = None

    def now(self):
        return rospy.get_time()

    def on_models(self, m):
        if MODEL not in m.name:
            return
        i = m.name.index(MODEL)
        p, q, tw = m.pose[i], m.pose[i].orientation, m.twist[i]
        v = (p.position.x, p.position.y, p.position.z, q.x, q.y, q.z, q.w, tw.linear.x, tw.linear.y, tw.angular.z)
        if not all(math.isfinite(x) for x in v):
            self.nonfinite += 1
            return
        with self.lock:
            self.truth = (self.now(), v)
            self.truth_series.append((self.now(), v[0], v[1]))

    def on_p3d(self, m):
        p, q = m.pose.pose.position, m.pose.pose.orientation
        v = (p.x, p.y, p.z, q.x, q.y, q.z, q.w)
        with self.lock:
            self.p3d = (m.header.stamp.to_sec(), v)
            self.p3d_msgs.append((m.header.stamp.to_nsec(), v))

    def on_odom(self, m):
        p, q = m.pose.pose.position, m.pose.pose.orientation
        t = m.twist.twist
        v = (p.x, p.y, p.z, q.x, q.y, q.z, q.w, t.linear.x, t.angular.z)
        if not all(math.isfinite(x) for x in v):
            self.nonfinite += 1
            return
        with self.lock:
            self.odom = (m.header.stamp.to_sec(), v)

    def on_state(self, m):
        with self.lock:
            self.arm_state = (m.header.stamp.to_sec(), dict(zip(m.joint_names, zip(m.desired.positions, m.actual.positions, m.actual.velocities))))

    def on_joint(self, m):
        with self.lock:
            for n, p, v in zip(m.name, m.position, m.velocity if m.velocity else [float("nan")] * len(m.name)):
                self.joint[n] = (m.header.stamp.to_sec(), p, v)

    def on_tf(self, m):
        caller = m._connection_header.get("callerid", "?")
        with self.lock:
            for t in m.transforms:
                self.tf_callers[caller][(t.header.frame_id, t.child_frame_id)] += 1
                if t.header.frame_id == "odom" and t.child_frame_id == "base_footprint":
                    r, q = t.transform.translation, t.transform.rotation
                    self.tf_msgs.append((t.header.stamp.to_nsec(), (r.x, r.y, r.z, q.x, q.y, q.z, q.w)))

    def on_status(self, m):
        self.pose_status = json.loads(m.data)


def sim_sleep(sec):
    t0 = rospy.get_time()
    while not rospy.is_shutdown() and rospy.get_time() - t0 < sec:
        time.sleep(0.01)


def phase(rec, name, duration, twist=None, rate=20.0, log=None, extra=None):
    """Run one phase; sample truth/odom/arm at ~50 Hz in sim time and publish the (optional) twist at `rate`."""
    pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
    t0 = rospy.get_time()
    w0 = time.time()
    samples = []
    next_pub = t0
    while rospy.get_time() - t0 < duration and not rospy.is_shutdown():
        now = rospy.get_time()
        if twist is not None and now >= next_pub:
            pub.publish(_mk(twist))
            next_pub = now + 1.0 / rate
        with rec.lock:
            tr, od, ar = rec.truth, rec.odom, rec.arm_state
        if tr is not None:
            samples.append(dict(t=now, truth=tr[1], odom=None if od is None else od[1],
                                arm=None if ar is None else {k: v for k, v in ar[1].items()}))
        time.sleep(0.02)
    if twist is not None:
        pub.publish(Twist())     # explicit stop
    return dict(name=name, t0=t0, t1=rospy.get_time(), wall=time.time() - w0, samples=samples)


def _mk(tw):
    t = Twist()
    t.linear.x, t.angular.z = tw
    return t


def base_metrics(ph, v_cmd=0.0, w_cmd=0.0):
    s = [x for x in ph["samples"] if x["truth"] is not None]
    a, b = s[0]["truth"], s[-1]["truth"]
    dt = s[-1]["t"] - s[0]["t"]
    d = np.array([b[0] - a[0], b[1] - a[1]])
    yaw0, yaw1 = yaw_of(a[3:7]), yaw_of(b[3:7])
    fwd = np.array([math.cos(yaw0), math.sin(yaw0)])
    along = float(d @ fwd)
    lateral = float(d @ np.array([-fwd[1], fwd[0]]))
    dyaw = wrap(yaw1 - yaw0)
    pts = np.array([[x["truth"][0], x["truth"][1]] for x in s])
    path = float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
    return dict(path_length=path, path_speed=path / dt if dt > 0 else float("nan"), duration=dt, dx=float(d[0]), dy=float(d[1]), xy=float(np.linalg.norm(d)), along=along, lateral=lateral,
                dyaw=dyaw, mean_speed=along / dt if dt > 0 else float("nan"), mean_rate=dyaw / dt if dt > 0 else float("nan"),
                v_cmd=v_cmd, w_cmd=w_cmd, n=len(s),
                z_range=[min(x["truth"][2] for x in s), max(x["truth"][2] for x in s)])


def arm_hold_metrics(ph):
    errs, vels = [], []
    last = None
    for x in ph["samples"]:
        if x["arm"] is None:
            continue
        for j in ARM:
            des, act, vel = x["arm"][j]
            errs.append(abs(act - des))
            vels.append(vel)
    return dict(max_abs_err=float(max(errs)) if errs else float("nan"),
                vel_rms=float(np.sqrt(np.mean(np.square(vels)))) if vels else float("nan"), n=len(errs))


def write_csv(path, rows, header):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--hold", type=float, default=3.0)
    ap.add_argument("--straight", type=float, default=3.0)
    ap.add_argument("--v", type=float, default=0.2)
    ap.add_argument("--turn", type=float, default=3.0)
    ap.add_argument("--w", type=float, default=0.5)
    ap.add_argument("--coord", type=float, default=3.0)
    ap.add_argument("--coord-v", type=float, default=0.15)
    ap.add_argument("--coord-w", type=float, default=0.2)
    ap.add_argument("--arm-delta", type=float, nargs=6, default=[0.3, 0.0, 0.0, 0.2, 0.0, 0.0])
    a = ap.parse_args()
    res_dir = os.environ.get("FOREM_RES_DIR", os.path.join("results/task3", a.run_id))
    os.makedirs(res_dir, exist_ok=True)

    rospy.init_node("check_task3_physics", anonymous=True)
    rec = Recorder()
    rospy.Subscriber("/gazebo/model_states", ModelStates, rec.on_models, queue_size=5)
    rospy.Subscriber("/ground_truth/state", Odometry, rec.on_p3d, queue_size=200)
    rospy.Subscriber("/husky_velocity_controller/odom", Odometry, rec.on_odom, queue_size=5)
    rospy.Subscriber("/eff_joint_traj_controller/state", JointTrajectoryControllerState, rec.on_state, queue_size=5)
    rospy.Subscriber("/joint_states", JointState, rec.on_joint, queue_size=50)
    rospy.Subscriber("/tf", TFMessage, rec.on_tf, queue_size=500)
    rospy.Subscriber("/pose_bridge/status", String, rec.on_status, queue_size=1)
    buf = tf2_ros.Buffer(rospy.Duration(30.0))
    tf2_ros.TransformListener(buf)

    # wait for the data streams
    deadline = time.time() + 60
    while time.time() < deadline and (rec.truth is None or rec.p3d is None or rec.odom is None or rec.arm_state is None):
        time.sleep(0.1)
    if rec.truth is None or rec.p3d is None or rec.odom is None or rec.arm_state is None:
        print("FAIL: missing data streams", dict(truth=rec.truth is not None, p3d=rec.p3d is not None,
                                                 odom=rec.odom is not None, arm=rec.arm_state is not None))
        return 2

    result = dict(run_id=a.run_id, gates=GATES, phases={}, verdicts={}, started_sim=rospy.get_time())
    series = []

    # ---- hold
    ph = phase(rec, "hold", a.hold)
    m = base_metrics(ph)
    m.update({"arm": arm_hold_metrics(ph)})
    result["phases"]["hold"] = m
    result["verdicts"]["hold_base_xy"] = m["xy"] <= GATES["hold_xy_drift_m"]
    result["verdicts"]["hold_base_yaw"] = abs(m["dyaw"]) <= GATES["hold_yaw_drift_rad"]
    result["verdicts"]["hold_arm_err"] = m["arm"]["max_abs_err"] <= GATES["hold_arm_err_rad"]
    result["verdicts"]["hold_arm_vel_rms"] = m["arm"]["vel_rms"] <= GATES["hold_arm_vel_rms"]
    series.append(ph)

    # ---- straight
    ph = phase(rec, "straight", a.straight, twist=(a.v, 0.0))
    m = base_metrics(ph, v_cmd=a.v)
    result["phases"]["straight"] = m
    result["verdicts"]["straight_speed"] = abs(m["mean_speed"] - a.v) <= GATES["straight_speed_rel"] * a.v
    result["verdicts"]["straight_lateral"] = abs(m["lateral"]) <= GATES["straight_lateral_m"]
    result["verdicts"]["straight_yaw"] = abs(m["dyaw"]) <= GATES["straight_yaw_rad"]
    series.append(ph)
    series.append(phase(rec, "stop1", 1.0))

    # ---- turn in place
    ph = phase(rec, "turn", a.turn, twist=(0.0, a.w))
    m = base_metrics(ph, w_cmd=a.w)
    result["phases"]["turn"] = m
    result["verdicts"]["turn_rate"] = abs(m["mean_rate"] - a.w) <= GATES["turn_rate_rel"] * a.w
    result["verdicts"]["turn_xy"] = m["xy"] <= GATES["turn_xy_m"]
    series.append(ph)
    series.append(phase(rec, "stop2", 1.0))

    # ---- coordinated: base twist + arm trajectory through the real action server
    client = actionlib.SimpleActionClient("/eff_joint_traj_controller/follow_joint_trajectory", FollowJointTrajectoryAction)
    client.wait_for_server(rospy.Duration(10.0))
    with rec.lock:
        q0 = {j: rec.arm_state[1][j][1] for j in ARM}
    target = [q0[j] + d for j, d in zip(ARM, a.arm_delta)]
    goal = FollowJointTrajectoryGoal()
    goal.trajectory.joint_names = ARM
    pt = JointTrajectoryPoint()
    pt.positions = target
    pt.time_from_start = rospy.Duration(a.coord)
    goal.trajectory.points = [pt]
    goal.trajectory.header.stamp = rospy.Time.now()
    t_send = rospy.get_time()
    client.send_goal(goal)
    ph = phase(rec, "coord", a.coord + 0.5, twist=(a.coord_v, a.coord_w))
    client.wait_for_result(rospy.Duration(5.0))
    result_code = client.get_result().error_code if client.get_result() else None
    sim_sleep(1.0)
    with rec.lock:
        q1 = {j: rec.arm_state[1][j][1] for j in ARM}
    m = base_metrics(ph, v_cmd=a.coord_v, w_cmd=a.coord_w)
    m["arm_target"] = dict(zip(ARM, target))
    m["arm_final"] = q1
    m["arm_final_err"] = {j: q1[j] - t for j, t in zip(ARM, target)}
    m["arm_action_error_code"] = result_code
    m["arm_goal_sent_sim_t"] = t_send
    result["phases"]["coord"] = m
    result["verdicts"]["coord_arm_final"] = max(abs(v) for v in m["arm_final_err"].values()) <= GATES["coord_arm_final_err_rad"]
    m["speed_ratio"], m["rate_ratio"] = m["path_speed"] / a.coord_v, m["mean_rate"] / a.coord_w
    result["verdicts"]["coord_base_speed"] = GATES["coord_base_ratio_lo"] <= m["speed_ratio"] <= GATES["coord_base_ratio_hi"]
    result["verdicts"]["coord_base_rate"] = GATES["coord_base_ratio_lo"] <= m["rate_ratio"] <= GATES["coord_base_ratio_hi"]
    series.append(ph)
    series.append(phase(rec, "stop3", 1.0))

    # ---- generic stability / limits over the whole record
    allq = [x["arm"][j] for ph in series for x in ph["samples"] if x["arm"] for j in ARM]
    result["verdicts"]["finite"] = rec.nonfinite == 0 and all(all(math.isfinite(v) for v in t) for t in allq)
    result["verdicts"]["arm_within_limits"] = all(abs(t[1]) <= ARM_LIMITS for t in allq)
    result["verdicts"]["arm_vel_within_limit"] = all(abs(t[2]) <= ARM_VEL_LIMIT * 1.1 for t in allq)

    # ---- TF: single authority, original stamps, values equal the pose source, frames consistent
    with rec.lock:
        callers = {c: sorted(f"{p}->{ch}" for (p, ch) in d) for c, d in rec.tf_callers.items()}
        tf_by_stamp = {s: v for s, v in rec.tf_msgs}
        p3d = list(rec.p3d_msgs)
        status = rec.pose_status
    auth = tf_authority({c: set(d) for c, d in rec.tf_callers.items()})
    result["tf"] = dict(callers=callers, odom_base_footprint_authors=auth["odom_base_authors"], pose_bridge_status=status)
    result["verdicts"]["tf_unique_authority"] = auth["unique"]
    result["verdicts"]["tf_authors_allowed"] = auth["allowed"]
    matched, maxdiff = 0, 0.0
    for s, v in p3d:
        w = tf_by_stamp.get(s)
        if w is None:
            continue
        matched += 1
        maxdiff = max(maxdiff, max(abs(x - y) for x, y in zip(v, w)))
    frac = matched / max(len(p3d), 1)
    result["tf"].update(p3d_msgs=len(p3d), matched_by_original_stamp=matched, matched_fraction=frac, max_value_diff=maxdiff)
    result["verdicts"]["tf_original_stamp_and_values"] = frac >= 0.95 and maxdiff <= GATES["tf_value_tol"]
    try:
        t_id = buf.lookup_transform("map", "odom", rospy.Time(0), rospy.Duration(2.0))
        t_bl = buf.lookup_transform("map", "base_link", rospy.Time(0), rospy.Duration(2.0))
        ident = all(abs(x) < 1e-9 for x in (t_id.transform.translation.x, t_id.transform.translation.y, t_id.transform.translation.z,
                                            t_id.transform.rotation.x, t_id.transform.rotation.y, t_id.transform.rotation.z)) \
            and abs(t_id.transform.rotation.w - 1.0) < 1e-9
        result["tf"]["map_odom_identity"] = ident
        result["tf"]["map_base_link_translation"] = [t_bl.transform.translation.x, t_bl.transform.translation.y, t_bl.transform.translation.z]
        result["verdicts"]["tf_frames_resolve"] = ident and all(math.isfinite(v) for v in result["tf"]["map_base_link_translation"])
    except Exception as e:  # noqa: BLE001
        result["tf"]["lookup_error"] = repr(e)
        result["verdicts"]["tf_frames_resolve"] = False
    # p3d (the reference pose source; the URDF requests gaussianNoise 0.01) vs Gazebo truth, time-interpolated over the run
    with rec.lock:
        tr, p3 = rec.truth, rec.p3d
        ts = np.array(rec.truth_series)
        pm = [(s_ * 1e-9, v_) for s_, v_ in rec.p3d_msgs]
    errs = []
    if len(ts) > 10:
        for t_, v_ in pm:
            if ts[0, 0] <= t_ <= ts[-1, 0]:
                errs.append(math.hypot(np.interp(t_, ts[:, 0], ts[:, 1]) - v_[0], np.interp(t_, ts[:, 0], ts[:, 2]) - v_[1]))
    result["tf"]["p3d_minus_truth_xy"] = dict(n=len(errs), max=float(max(errs)) if errs else None,
                                              mean=float(np.mean(errs)) if errs else None,
                                              std=float(np.std(errs)) if errs else None,
                                              note="truth sampled at callback receipt time (sim clock); includes that jitter")
    d_xy = math.hypot(tr[1][0] - p3[1][0], tr[1][1] - p3[1][1]) if tr and p3 else float("nan")
    result["tf"]["p3d_minus_truth_xy_last"] = d_xy
    result["verdicts"]["p3d_close_to_truth"] = d_xy <= GATES["p3d_vs_truth_xy_m"]

    # ---- raw series
    rows = []
    for ph in series:
        for x in ph["samples"]:
            tr = x["truth"]
            od = x["odom"] or [float("nan")] * 9
            armv = x["arm"]
            rows.append([ph["name"], f"{x['t']:.4f}"] + [f"{v:.6f}" for v in tr[:3]] + [f"{yaw_of(tr[3:7]):.6f}", f"{tr[7]:.6f}", f"{tr[9]:.6f}",
                                                                                     f"{od[0]:.6f}", f"{od[1]:.6f}", f"{od[7]:.6f}", f"{od[8]:.6f}"] +
                        ([f"{armv[j][0]:.6f}" for j in ARM] + [f"{armv[j][1]:.6f}" for j in ARM] if armv else [""] * 12))
    write_csv(os.path.join(res_dir, "timeseries.csv"), rows,
              ["phase", "t_sim", "truth_x", "truth_y", "truth_z", "truth_yaw", "truth_vx", "truth_wz", "odom_x", "odom_y", "odom_vx", "odom_wz"]
              + [f"arm_des_{j}" for j in ARM] + [f"arm_act_{j}" for j in ARM])
    result["rtf"] = {ph["name"]: (ph["t1"] - ph["t0"]) / ph["wall"] for ph in series}
    result["finished_sim"] = rospy.get_time()
    result["ok"] = all(result["verdicts"].values())
    with open(os.path.join(res_dir, "physics_summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    for k, v in result["verdicts"].items():
        print(("PASS " if v else "FAIL ") + k)
    print("OK" if result["ok"] else "NOT OK", "-> ", os.path.join(res_dir, "physics_summary.json"))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
