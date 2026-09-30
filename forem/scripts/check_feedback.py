#!/usr/bin/env python3
"""task0 feedback check for the fixed-base UR5 sim (no error injection).

Records /clock, /joint_states and /eff_joint_traj_controller/state for a number of simulated
seconds, optionally sends one smooth two-point trajectory first (--move), writes CSV samples and
a JSON summary, and decides pass/fail with scripts/task0_validation.py (task0.7 rewrite).
Exit code 0 only if every check passes; 3 if the request itself is invalid (e.g. the window is
too short to contain the commanded move).

Command (desired) and feedback (actual) stay separate:
  * controller state.desired  = the controller's instantaneous interpolated reference
  * controller state.actual / joint_states = measured joint state from Gazebo
No value is ever copied from one into the other. Tracking error in this script is
actual - desired; final error is actual - command_target.

Usage (inside forem-dev, sim already running):
  python3 scripts/check_feedback.py --run-id RUN --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3
"""
import argparse
import csv
import json
import os
import sys
import threading
import time
import xml.etree.ElementTree as ET

import rospy
from control_msgs.msg import JointTrajectoryControllerState
from gazebo_msgs.srv import GetModelState
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task0_validation as V  # noqa: E402

JOINTS = V.JOINTS
CTRL = "/eff_joint_traj_controller"


def urdf_limits(urdf_xml):
    root = ET.fromstring(urdf_xml)
    lim = {}
    for j in root.findall("joint"):
        if j.get("name") in JOINTS:
            l = j.find("limit")
            lim[j.get("name")] = {k: float(l.get(k)) for k in ("lower", "upper", "velocity", "effort")}
    missing = [j for j in JOINTS if j not in lim]
    if missing:
        raise RuntimeError("limits missing for %s" % missing)
    return lim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--duration", type=float, default=6.0, help="simulated seconds to record")
    ap.add_argument("--settle", type=float, default=1.0, help="simulated seconds to wait before recording/command")
    ap.add_argument("--move", type=float, nargs=6, metavar="DQ", default=None,
                    help="send one smooth move of joint offsets (rad) relative to the pose at command time")
    ap.add_argument("--move-time", type=float, default=3.0, help="duration of the commanded move (s)")
    ap.add_argument("--min-settle-after-move", type=float, default=1.0, help="required quiet time after the move inside the window (s)")
    ap.add_argument("--joint-rate", type=float, default=125.0, help="configured publish rate of joint_states / controller state (Hz)")
    ap.add_argument("--max-gap-periods", type=int, default=10, help="largest allowed gap between samples in publish periods")
    ap.add_argument("--results-root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "task0"))
    args = ap.parse_args()

    if args.move is not None and args.duration < args.move_time + args.min_settle_after_move - 1e-9:
        print("REFUSED: --duration %.3f s cannot contain the %.3f s move plus %.3f s settle; "
              "increase --duration" % (args.duration, args.move_time, args.min_settle_after_move))
        sys.exit(3)

    rospy.init_node("check_feedback", anonymous=True)
    out = os.path.abspath(os.path.join(args.results_root, args.run_id))
    os.makedirs(out, exist_ok=True)

    limits = urdf_limits(rospy.get_param("/robot_description"))

    lock = threading.Lock()
    js_rows, st_rows, clock = [], [], []
    latest = {"js": None}
    recording = {"on": False}

    def on_clock(m):
        if recording["on"]:
            with lock:
                clock.append(m.clock.to_sec())

    def on_js(m):
        idx = {n: i for i, n in enumerate(m.name)}
        if not all(j in idx for j in JOINTS):
            return
        row = [m.header.stamp.to_sec()] + [m.position[idx[j]] for j in JOINTS] + \
              [m.velocity[idx[j]] for j in JOINTS] + [m.effort[idx[j]] for j in JOINTS]
        latest["js"] = row
        if recording["on"]:
            with lock:
                js_rows.append(row)

    def on_state(m):
        if recording["on"] and list(m.joint_names) == JOINTS:
            with lock:
                st_rows.append([m.header.stamp.to_sec()] + list(m.desired.positions) + list(m.actual.positions) +
                               list(m.error.positions) + list(m.desired.velocities) + list(m.actual.velocities))

    rospy.Subscriber("/clock", Clock, on_clock, queue_size=1000)
    rospy.Subscriber("/joint_states", JointState, on_js, queue_size=1000)
    rospy.Subscriber(CTRL + "/state", JointTrajectoryControllerState, on_state, queue_size=1000)
    get_model = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)
    pub = rospy.Publisher(CTRL + "/command", JointTrajectory, queue_size=1, latch=True)

    wall_start = time.time()
    while not rospy.is_shutdown() and rospy.Time.now().to_sec() <= 0.0:
        if time.time() - wall_start > 30:
            print("FAIL: /clock never advanced")
            sys.exit(2)
        time.sleep(0.05)

    def pose():
        """(pose list or None, service_ok). A failed call is a failure, never a default pose."""
        try:
            r = get_model("forem_ur5", "world")
        except Exception:
            return None, False
        if not r.success:
            return None, False
        p, o = r.pose.position, r.pose.orientation
        return [p.x, p.y, p.z, o.x, o.y, o.z, o.w], True

    def sim_wait(until):
        while not rospy.is_shutdown() and rospy.Time.now().to_sec() < until:
            if time.time() - wall_start > 900:
                raise RuntimeError("wall timeout")
            time.sleep(0.02)

    t0 = rospy.Time.now().to_sec()
    sim_wait(t0 + args.settle)
    base_start, ok_start = pose()
    if latest["js"] is None:
        for _ in range(100):
            if latest["js"] is not None:
                break
            time.sleep(0.05)
    recording["on"] = True
    rec_t0 = rospy.Time.now().to_sec()

    cmd = None
    if args.move is not None:
        q0 = list(latest["js"][1:7]) if latest["js"] else [0.0] * 6
        target = [q + d for q, d in zip(q0, args.move)]
        traj = JointTrajectory()
        traj.joint_names = JOINTS
        p0 = JointTrajectoryPoint(positions=q0, velocities=[0.0] * 6, time_from_start=rospy.Duration(0.0))
        p1 = JointTrajectoryPoint(positions=target, velocities=[0.0] * 6, time_from_start=rospy.Duration(args.move_time))
        traj.points = [p0, p1]
        traj.header.stamp = rospy.Time(0)  # start immediately
        cmd = {"sim_time_sent": rospy.Time.now().to_sec(), "q_start": q0, "q_target": target,
               "duration_s": args.move_time, "offsets": list(args.move),
               "note": "two-point trajectory; controller interpolates"}
        pub.publish(traj)

    rec_t1 = rec_t0 + args.duration
    sim_wait(rec_t1)
    recording["on"] = False
    base_end, ok_end = pose()

    with lock:
        js = list(js_rows); st = list(st_rows); ck = list(clock)

    def write(name, header, rows):
        with open(os.path.join(out, name), "w", newline="") as f:
            w = csv.writer(f); w.writerow(header); w.writerows(rows)

    write("joint_states.csv", ["t"] + ["pos_" + j for j in JOINTS] + ["vel_" + j for j in JOINTS] + ["eff_" + j for j in JOINTS], js)
    write("controller_state.csv", ["t"] + ["des_" + j for j in JOINTS] + ["act_" + j for j in JOINTS] + ["err_" + j for j in JOINTS] +
          ["desvel_" + j for j in JOINTS] + ["actvel_" + j for j in JOINTS], st)

    policy = {"window_start": rec_t0, "window_end": rec_t1, "joint_rate_hz": args.joint_rate,
              "max_gap_periods": args.max_gap_periods, "min_settle_after_move_s": args.min_settle_after_move}
    checks, metrics = V.evaluate_feedback(js, st, ck, cmd, limits, policy)
    pc, pm = V.model_pose_checks(base_start, base_end, ok_start, ok_end, policy.get("pose_change_tol", V.DEFAULT_POLICY["pose_change_tol"]))
    checks.update(pc)
    metrics.update(pm)
    summary = {
        "run_id": args.run_id, "requested_duration_sim_s": args.duration, "recording_window_sim_s": [rec_t0, rec_t1],
        "move": cmd, "limits_from_urdf": limits, "checks": checks, "metrics": metrics,
        "model_pose_start": base_start, "model_pose_end": base_end,
        "final_actual_positions": js[-1][1:7] if js else None,
        "final_desired_positions": st[-1][1:7] if st else None,
        "error_convention": "tracking error = actual - desired (same timestamp); final error = actual - command_target",
        "pass": V.is_pass(checks),
    }
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps({"run_id": args.run_id, "pass": summary["pass"],
                      "failed_checks": [k for k, v in checks.items() if not v],
                      "joint_states_hz": metrics.get("joint_states", {}).get("mean_hz"),
                      "controller_state_hz": metrics.get("controller_state", {}).get("mean_hz"),
                      "max_abs_tracking_error_rad": metrics.get("max_abs_tracking_error_rad"),
                      "model_pose_max_abs_change": pm.get("model_pose_max_abs_change"), "out": out}, indent=2))
    sys.exit(0 if summary["pass"] else 1)


if __name__ == "__main__":
    main()
