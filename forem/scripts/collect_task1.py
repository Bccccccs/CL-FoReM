#!/usr/bin/env python3
"""Task1 run protocol node (runs inside forem-dev, sim + rosbag already running).

Sends the frozen command for one case and records what was sent; the measurements themselves are in the
rosbag (/clock, /joint_states, controller state, command topic, throttled Gazebo link states) recorded by a
separate supervised process. This node never writes feedback values: it only
  * waits for the sim clock,
  * keeps a live safety monitor (non-finite/over-limit joint state, clock going back, feedback stalling),
  * holds for pre_hold_s of simulated time, then sends a two-point trajectory (or nothing for case H),
  * writes commands.json (full message fields, sim send times, observed q_start vs q_init, base pose start/end),
  * saves the URDF and controller parameters of this launch.
Exit codes: 0 done; 2 safety abort (abort.json written, evidence kept); 3 invalid request; 4 setup failed.
"""
import argparse
import json
import math
import os
import sys
import threading
import time

import rospy
import yaml
from gazebo_msgs.srv import GetModelState
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task1_freeze as F  # noqa: E402  (urdf_joint_limits)
import task1_lib as L  # noqa: E402  (command_record: one command schema shared with the bag converter)

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--case", required=True)
    ap.add_argument("--config", default=os.path.join(ROOT, "config", "experiments", "task1", "baseline.yaml"))
    ap.add_argument("--results-root", default=os.path.join(ROOT, "results", "task1"))
    ap.add_argument("--test-abort-after-s", type=float, default=None,
                    help="REGRESSION ONLY: raise a safety abort this many simulated seconds after recording starts (tests the failure path)")
    ap.add_argument("--tail-margin-s", type=float, default=1.0, help="extra recording after the settle window so window edges have support")
    a = ap.parse_args()

    cfg = yaml.safe_load(open(a.config))
    if a.case not in cfg["cases"]:
        print("REFUSED: unknown case %s" % a.case)
        sys.exit(3)
    case = cfg["cases"][a.case]
    joints = cfg["robot"]["joints"]
    tm = cfg["timing"]
    out = os.path.join(a.results_root, a.run_id)
    os.makedirs(out, exist_ok=True)
    moving = case["dq"] is not None
    T = float(case["T"]) if moving else None
    total = tm["pre_hold_s"] + ((T + tm["settle_s"] + a.tail_margin_s) if moving else tm["hold_s"])

    rospy.init_node("collect_task1", anonymous=True)
    urdf = rospy.get_param("/robot_description")
    limits = F.urdf_joint_limits(urdf, joints)
    open(os.path.join(out, "robot_description.urdf"), "w").write(urdf)
    json.dump({"eff_joint_traj_controller": rospy.get_param("/eff_joint_traj_controller"),
               "joint_state_controller": rospy.get_param("/joint_state_controller")}, open(os.path.join(out, "controller_params.json"), "w"), indent=2)

    st = {"clock": None, "js": None, "js_wall": time.time(), "abort": None}
    lock = threading.Lock()

    def abort(reason):
        with lock:
            if st["abort"] is None:
                st["abort"] = reason

    def on_clock(m):
        t = m.clock.to_sec()
        if st["clock"] is not None and t < st["clock"] - 1e-9:
            abort("clock went backwards: %.6f -> %.6f" % (st["clock"], t))
        st["clock"] = t

    def on_js(m):
        idx = {n: i for i, n in enumerate(m.name)}
        if not all(j in idx for j in joints):
            abort("joint_states missing joints: %s" % list(m.name))
            return
        q = [m.position[idx[j]] for j in joints]
        v = [m.velocity[idx[j]] for j in joints]
        if not all(math.isfinite(x) for x in q + v):
            abort("non-finite joint state")
            return
        for j, qi, vi in zip(joints, q, v):
            lim = limits[j]
            if qi < lim["lower"] or qi > lim["upper"]:
                abort("%s position %.4f outside URDF limits" % (j, qi))
            if abs(vi) > lim["velocity"]:
                abort("%s velocity %.4f exceeds URDF limit %.4f" % (j, vi, lim["velocity"]))
        st["js"] = {"stamp": m.header.stamp.to_sec(), "q": q}
        st["js_wall"] = time.time()

    rospy.Subscriber("/clock", Clock, on_clock, queue_size=1000)
    rospy.Subscriber(cfg["robot"]["joint_states_topic"], JointState, on_js, queue_size=1000)
    pub = rospy.Publisher(cfg["robot"]["command_topic"], JointTrajectory, queue_size=1, latch=True)
    get_model = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)

    wall0 = time.time()
    wall_limit = 5.0 * total + 120.0

    def sim_now():
        return rospy.Time.now().to_sec()

    def check():
        if a.test_abort_after_s is not None and "rec_t0" in record and sim_now() >= record["rec_t0"] + a.test_abort_after_s:
            raise RuntimeError("test-injected abort after %.1f s (regression hook)" % a.test_abort_after_s)
        if st["abort"]:
            raise RuntimeError(st["abort"])
        if time.time() - wall0 > wall_limit:
            raise RuntimeError("wall timeout %.0f s" % wall_limit)
        if st["js"] is not None and time.time() - st["js_wall"] > 2.0:
            raise RuntimeError("no joint_states for 2 s wall time")

    def sim_wait(until):
        while not rospy.is_shutdown() and sim_now() < until:
            check()
            time.sleep(0.01)

    def base_pose():
        r = get_model(cfg["robot"]["model_name"], "world")
        if not r.success:
            raise RuntimeError("get_model_state failed: %s" % r.status_message)
        p, o = r.pose.position, r.pose.orientation
        return [p.x, p.y, p.z, o.x, o.y, o.z, o.w]

    record = {"run_id": a.run_id, "case": a.case, "case_def": case, "config": a.config, "pre_hold_s": tm["pre_hold_s"],
              "commands": [], "note": "header.stamp=0 means start immediately; the actual start time is observed in the data (t_ref)"}
    rc = 0
    try:
        while not rospy.is_shutdown() and (sim_now() <= 0.0 or st["js"] is None):
            check()
            if time.time() - wall0 > 60:
                raise RuntimeError("no clock/joint_states within 60 s")
            time.sleep(0.05)
        record["base_pose_start"] = base_pose()
        rec_t0 = sim_now()
        record["rec_t0"] = rec_t0
        sim_wait(rec_t0 + tm["pre_hold_s"])
        if moving:
            q_start = list(st["js"]["q"])
            q_target = [q + float(d) for q, d in zip(q_start, case["dq"])]
            for j, qt in zip(joints, q_target):
                lim = limits[j]
                if not (lim["lower"] < qt < lim["upper"]):
                    raise RuntimeError("target for %s outside URDF limits" % j)
            traj = JointTrajectory()
            traj.header.stamp = rospy.Time(0)
            traj.joint_names = list(joints)
            traj.points = [JointTrajectoryPoint(positions=q_start, velocities=[0.0] * 6, time_from_start=rospy.Duration(0.0)),
                           JointTrajectoryPoint(positions=q_target, velocities=[0.0] * 6, time_from_start=rospy.Duration(T))]
            t_before = sim_now()
            pub.publish(traj)
            t_after = sim_now()
            record["commands"].append({
                "topic": cfg["robot"]["command_topic"], "sim_time_before_publish": t_before, "sim_time_after_publish": t_after,
                "publisher_connections": pub.get_num_connections(), "q_start_observed": q_start, "q_start_js_stamp": st["js"]["stamp"],
                "q_init_config": cfg["robot"]["q_init"], "q_start_minus_q_init": [x - y for x, y in zip(q_start, cfg["robot"]["q_init"])],
                "dq": [float(d) for d in case["dq"]], "q_target": q_target, "duration_s": T,
                "message": L.command_record(traj)})
            rec_t1 = t_before + T + tm["settle_s"] + a.tail_margin_s
        else:
            rec_t1 = rec_t0 + total
        record["rec_t1"] = rec_t1
        sim_wait(rec_t1)
        record["base_pose_end"] = base_pose()
        record["windows_nominal"] = {"pre_hold": [rec_t0, rec_t0 + tm["pre_hold_s"]]}
    except Exception as e:  # noqa: BLE001 - every failure must leave evidence and a non-zero exit
        rc = 2
        record["aborted"] = str(e)
        json.dump({"reason": str(e), "sim_time": st["clock"], "wall_elapsed_s": time.time() - wall0}, open(os.path.join(out, "abort.json"), "w"), indent=2)
        print("ABORT:", e)
    record["finished_wall"] = time.strftime("%F %T %z")
    json.dump(record, open(os.path.join(out, "commands.json"), "w"), indent=2)
    print("collect_task1: %s rc=%d rec_window=[%s, %s]" % (a.run_id, rc, record.get("rec_t0"), record.get("rec_t1")))
    sys.exit(rc)


if __name__ == "__main__":
    main()
