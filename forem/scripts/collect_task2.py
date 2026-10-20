#!/usr/bin/env python3
"""Task2 run protocol node (runs inside forem-dev, sim + rosbag (+ delay proxy in queue mode) already running).

Sends the frozen command of one case ONCE and records what was sent; the measurements themselves are in the rosbag recorded by a
separate supervised process. It never writes feedback values. Differences to collect_task1.py (which stays untouched):
  * --mode bypass : publishes straight to /eff_joint_traj_controller/command (no proxy exists)
    --mode queue  : publishes to /task2/command_in; only the delay proxy publishes downstream
  * the publisher is NOT latched; the node first waits until every topic it relies on is connected (controller + recorder) and, in queue
    mode, until the proxy reported ready, so the single command cannot be lost to a late subscriber
  * topic-graph preflight: no other publisher on the downstream command topic (than the sender in bypass mode / the proxy in queue mode),
    none on the upstream topic besides the sender, and no action-goal publisher: no hidden second command source
  * simulation send time is stored as integer nanoseconds before and after publish (the interval, not a point)
Exit codes: 0 done; 2 safety abort (abort.json written, evidence kept); 3 invalid request; 4 setup failed.
"""
import argparse
import json
import math
import os
import sys
import threading
import time

import rosgraph
import rospy
import yaml
from gazebo_msgs.srv import GetModelState
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task1_freeze as F  # noqa: E402  (urdf_joint_limits)
import task1_lib as L  # noqa: E402  (command_record: the one command schema)
import task2_delay_queue as Q  # noqa: E402  (payload_hash, validate_command)

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ACTION_GOAL = "/eff_joint_traj_controller/follow_joint_trajectory/goal"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--case", required=True)
    ap.add_argument("--mode", required=True, choices=["bypass", "queue"])
    ap.add_argument("--delay-ms", type=float, required=True)
    ap.add_argument("--config", default=os.path.join(ROOT, "config", "experiments", "exp2", "fixed_delay.yaml"))
    ap.add_argument("--results-root", default=os.path.join(ROOT, "results", "task2"))
    ap.add_argument("--test-abort-after-s", type=float, default=None,
                    help="REGRESSION ONLY: raise a safety abort this many simulated seconds after recording starts (tests the failure path)")
    a = ap.parse_args()

    cfg = yaml.safe_load(open(a.config))
    d = cfg["delay"]
    if a.case not in cfg["cases"]:
        print("REFUSED: unknown case %s" % a.case)
        sys.exit(3)
    tau_ms = a.delay_ms
    if not (tau_ms == tau_ms and tau_ms in [float(x) for x in d["allowed_tau_ms"]]):
        print("REFUSED: delay %s ms is not one of the frozen values %s" % (a.delay_ms, d["allowed_tau_ms"]))
        sys.exit(3)
    if a.mode == "bypass" and tau_ms != 0:
        print("REFUSED: bypass with a non-zero delay (%s ms)" % tau_ms)
        sys.exit(3)
    tau_ns = int(round(tau_ms * 1e6))
    case = cfg["cases"][a.case]
    joints = cfg["robot"]["joints"]
    tm = cfg["timing"]
    rt = cfg["runtime"]
    out = os.path.join(a.results_root, a.run_id)
    os.makedirs(out, exist_ok=True)
    moving = case["dq"] is not None
    T = float(case["T"]) if moving else None
    tau_s = tau_ns / 1e9
    total_hold = tm["pre_hold_s"] + tm["hold_s"]

    rospy.init_node("collect_task2", anonymous=True)
    me = rospy.get_name()
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
    topic = d["topics"]["command_out"] if a.mode == "bypass" else d["topics"]["command_in"]
    pub = rospy.Publisher(topic, JointTrajectory, queue_size=1, latch=False) if moving else None
    get_model = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)

    wall0 = time.time()
    wall_limit = float(rt["run_timeout_wall_s"])

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

    def graph():
        """Publishers/subscribers of the topics that matter, from the ROS master."""
        pubs, subs, _ = rosgraph.Master(me).getSystemState()
        pubs, subs = dict((t, sorted(n)) for t, n in pubs), dict((t, sorted(n)) for t, n in subs)
        keep = [d["topics"]["command_out"], d["topics"]["command_in"], ACTION_GOAL, d["topics"]["events"]]
        return {"publishers": {t: pubs.get(t, []) for t in keep}, "subscribers": {t: subs.get(t, []) for t in keep}}

    record = {"run_id": a.run_id, "case": a.case, "case_def": case, "config": a.config, "pre_hold_s": tm["pre_hold_s"], "mode": a.mode,
              "delay_ms": tau_ms, "tau_ns": tau_ns, "publish_topic": topic if moving else None, "commands": [],
              "note": "header.stamp=0 means start immediately; the actual start time is observed in the data (t_ref)"}
    rc = 0
    try:
        while not rospy.is_shutdown() and (sim_now() <= 0.0 or st["js"] is None):
            check()
            if time.time() - wall0 > 60:
                raise RuntimeError("no clock/joint_states within 60 s")
            time.sleep(0.05)
        # ---- readiness of the command path (before the recording window opens, so the pre-hold is not shortened)
        expect = d["publisher_expected_connections"]
        t_setup = time.time()
        while True:
            check()
            ready = True
            if a.mode == "queue":
                ready = bool(rospy.has_param("/task2/delay_ready") and rospy.get_param("/task2/delay_ready"))
                if rospy.has_param("/task2/delay_failed"):
                    raise RuntimeError("delay proxy reported failure: %s" % rospy.get_param("/task2/delay_failed"))
            if moving and pub.get_num_connections() < expect:
                ready = False
            if ready:
                break
            if time.time() - t_setup > 60:
                raise RuntimeError("command path not ready within 60 s (connections=%s, mode=%s)" % (pub.get_num_connections() if pub else None, a.mode))
            time.sleep(0.05)
        g = graph()
        record["topic_graph_before_send"] = g
        pubs = g["publishers"]
        allowed_out = [me] if a.mode == "bypass" else ["/task2_delay_node"]
        allowed_in = [me] if (a.mode == "queue" and moving) else []
        if not moving:
            allowed_out = [] if a.mode == "bypass" else ["/task2_delay_node"]
        bad = []
        if sorted(pubs[d["topics"]["command_out"]]) != sorted(allowed_out):
            bad.append("publishers on %s: %s (allowed %s)" % (d["topics"]["command_out"], pubs[d["topics"]["command_out"]], allowed_out))
        if sorted(pubs[d["topics"]["command_in"]]) != sorted(allowed_in):
            bad.append("publishers on %s: %s (allowed %s)" % (d["topics"]["command_in"], pubs[d["topics"]["command_in"]], allowed_in))
        if pubs[ACTION_GOAL]:
            bad.append("action-goal publishers exist: %s" % pubs[ACTION_GOAL])
        if bad:
            raise RuntimeError("unexpected command sources: " + "; ".join(bad))
        record["base_pose_start"] = base_pose()
        rec_t0 = sim_now()
        record["rec_t0"] = rec_t0
        sim_wait(rec_t0 + tm["pre_hold_s"])
        if moving:
            q_start = list(st["js"]["q"])
            q_target = [q + float(dq) for q, dq in zip(q_start, case["dq"])]
            for j, qt in zip(joints, q_target):
                lim = limits[j]
                if not (lim["lower"] < qt < lim["upper"]):
                    raise RuntimeError("target for %s outside URDF limits" % j)
            traj = JointTrajectory()
            traj.header.stamp = rospy.Time(0)
            traj.joint_names = list(joints)
            traj.points = [JointTrajectoryPoint(positions=q_start, velocities=[0.0] * 6, time_from_start=rospy.Duration(0.0)),
                           JointTrajectoryPoint(positions=q_target, velocities=[0.0] * 6, time_from_start=rospy.Duration(T))]
            rec = L.command_record(traj)
            problems = Q.validate_command(rec, joints, limits, cfg["trajectory"]["max_speed_fraction_of_velocity_limit"])
            if problems:
                raise RuntimeError("the sender's own command is outside the frozen supported message: %s" % problems)
            n_conn = pub.get_num_connections()
            t_before_ns = rospy.Time.now().to_nsec()
            pub.publish(traj)
            t_after_ns = rospy.Time.now().to_nsec()
            record["commands"].append({
                "topic": topic, "epoch": 0, "seq": 0, "payload_sha256": Q.payload_hash(rec),
                "sim_time_before_publish": t_before_ns / 1e9, "sim_time_after_publish": t_after_ns / 1e9,
                "sim_time_before_publish_ns": t_before_ns, "sim_time_after_publish_ns": t_after_ns,
                "publisher_connections": n_conn, "q_start_observed": q_start, "q_start_js_stamp": st["js"]["stamp"],
                "q_init_config": cfg["robot"]["q_init"], "q_start_minus_q_init": [x - y for x, y in zip(q_start, cfg["robot"]["q_init"])],
                "dq": [float(x) for x in case["dq"]], "q_target": q_target, "duration_s": T, "message": rec})
            rec_t1 = t_before_ns / 1e9 + tau_s + T + tm["settle_s"] + rt["tail_margin_s"]
        else:
            rec_t1 = rec_t0 + total_hold
        record["rec_t1"] = rec_t1
        sim_wait(rec_t1)
        record["base_pose_end"] = base_pose()
        record["topic_graph_after"] = graph()
        record["windows_nominal"] = {"pre_hold": [rec_t0, rec_t0 + tm["pre_hold_s"]]}
    except Exception as e:  # noqa: BLE001 - every failure must leave evidence and a non-zero exit
        rc = 2
        record["aborted"] = str(e)
        json.dump({"reason": str(e), "sim_time": st["clock"], "wall_elapsed_s": time.time() - wall0}, open(os.path.join(out, "abort.json"), "w"), indent=2)
        print("ABORT:", e)
    record["finished_wall"] = time.strftime("%F %T %z")
    json.dump(record, open(os.path.join(out, "commands.json"), "w"), indent=2)
    print("collect_task2: %s mode=%s tau=%s ms rc=%d rec_window=[%s, %s]" % (a.run_id, a.mode, tau_ms, rc, record.get("rec_t0"), record.get("rec_t1")))
    sys.exit(rc)


if __name__ == "__main__":
    main()
