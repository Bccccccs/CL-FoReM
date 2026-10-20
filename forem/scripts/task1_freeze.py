#!/usr/bin/env python3
"""Task1.1 baseline freeze.

  probe    (inside forem-dev, sim running): live facts from the running fresh sim -> results/task1/<freeze-id>/probe_<label>.json
  finalize (host; stdlib + PyYAML):         merges probes with config/source hashes, versions and the trajectory preflight
                                            -> results/task1/<freeze-id>/baseline.json (+ robot_description.urdf)

Facts are labelled by evidence class: measured (live probe), source (file/package inspection), inferred.
Nothing here changes physics, gains or limits.
"""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config", "experiments", "task1", "baseline.yaml")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def urdf_joint_limits(urdf_xml, joints):
    root = ET.fromstring(urdf_xml)
    lim = {}
    for j in root.findall("joint"):
        if j.get("name") in joints:
            l = j.find("limit")
            lim[j.get("name")] = {k: float(l.get(k)) for k in ("lower", "upper", "velocity", "effort")}
    missing = [j for j in joints if j not in lim]
    if missing:
        raise RuntimeError("URDF limits missing for %s" % missing)
    return lim


def dt_stats(ts):
    dts = [b - a for a, b in zip(ts, ts[1:])]
    if not dts:
        return {"n": len(ts)}
    s = sorted(dts)
    return {"n": len(ts), "span_s": ts[-1] - ts[0], "mean_hz": (len(ts) - 1) / (ts[-1] - ts[0]) if ts[-1] > ts[0] else None,
            "dt_min": s[0], "dt_median": s[len(s) // 2], "dt_max": s[-1], "dt_zero_or_negative": sum(1 for d in dts if d <= 0),
            "dt_histogram_ms": {str(round(k * 1e3, 3)): sum(1 for d in dts if abs(d - k) < 1e-6) for k in (0.0005, 0.001, 0.0015, 0.002, 0.004, 0.008)}}


# ---------------------------------------------------------------- probe (ROS)
def probe(a):
    import rospy
    from control_msgs.msg import JointTrajectoryControllerState
    from controller_manager_msgs.srv import ListControllers
    from gazebo_msgs.msg import LinkStates
    from gazebo_msgs.srv import GetModelState, GetPhysicsProperties
    from rosgraph_msgs.msg import Clock
    from sensor_msgs.msg import JointState

    cfg = yaml.safe_load(open(CONFIG))
    joints = cfg["robot"]["joints"]
    rospy.init_node("task1_freeze_probe", anonymous=True)
    clock, js, st, link_names = [], [], [], {}
    js_first = {}

    def on_clock(m):
        clock.append(m.clock.to_sec())

    def on_js(m):
        idx = {n: i for i, n in enumerate(m.name)}
        if all(j in idx for j in joints):
            js.append(m.header.stamp.to_sec())
            js_first.setdefault("q", [m.position[idx[j]] for j in joints])
            js_first["q_last"] = [m.position[idx[j]] for j in joints]

    def on_state(m):
        if list(m.joint_names) == joints:
            st.append(m.header.stamp.to_sec())

    def on_links(m):
        link_names["names"] = list(m.name)

    rospy.Subscriber("/clock", Clock, on_clock, queue_size=5000)
    rospy.Subscriber("/joint_states", JointState, on_js, queue_size=5000)
    rospy.Subscriber("/eff_joint_traj_controller/state", JointTrajectoryControllerState, on_state, queue_size=5000)
    rospy.Subscriber("/gazebo/link_states", LinkStates, on_links, queue_size=1)
    rospy.wait_for_service("/gazebo/get_physics_properties", 30)
    phys = rospy.ServiceProxy("/gazebo/get_physics_properties", GetPhysicsProperties)()
    lst = rospy.ServiceProxy("/controller_manager/list_controllers", ListControllers)()
    pose = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)(cfg["robot"]["model_name"], "world")

    import time
    w0 = time.time()
    while rospy.Time.now().to_sec() <= 0.0 and time.time() - w0 < 30:
        time.sleep(0.05)
    t0 = rospy.Time.now().to_sec()
    n0 = len(clock)
    while rospy.Time.now().to_sec() < t0 + a.duration and time.time() - w0 < 600:
        time.sleep(0.05)
    t1 = rospy.Time.now().to_sec()
    wall = time.time() - w0
    urdf = rospy.get_param("/robot_description")
    out = {
        "label": a.label, "evidence": "measured (live probe of a fresh sim)",
        "sim_window": [t0, t1], "sim_seconds": t1 - t0, "wall_seconds_incl_setup": wall,
        "clock_dt": dt_stats(clock[n0:]), "joint_states_dt": dt_stats([t for t in js if t0 <= t <= t1]),
        "controller_state_dt": dt_stats([t for t in st if t0 <= t <= t1]),
        "physics_properties": {"time_step": phys.time_step, "max_update_rate": phys.max_update_rate,
                               "gravity": [phys.gravity.x, phys.gravity.y, phys.gravity.z],
                               "ode": {"sor_pgs_iters": phys.ode_config.sor_pgs_iters, "sor_pgs_w": phys.ode_config.sor_pgs_w,
                                       "erp": phys.ode_config.erp, "cfm": phys.ode_config.cfm,
                                       "contact_max_correcting_vel": phys.ode_config.contact_max_correcting_vel,
                                       "contact_surface_layer": phys.ode_config.contact_surface_layer,
                                       "max_contacts": phys.ode_config.max_contacts}},
        "controllers": {c.name: {"state": c.state, "type": c.type, "claimed": [r.resources for r in c.claimed_resources]} for c in lst.controller},
        "q_at_probe_start": js_first.get("q"), "q_at_probe_end": js_first.get("q_last"),
        "q_init_config": cfg["robot"]["q_init"],
        "model_pose_world": {"ok": bool(pose.success), "position": [pose.pose.position.x, pose.pose.position.y, pose.pose.position.z],
                             "orientation_xyzw": [pose.pose.orientation.x, pose.pose.orientation.y, pose.pose.orientation.z, pose.pose.orientation.w]},
        "gazebo_link_names": link_names.get("names"),
        "rosparam": {"eff_joint_traj_controller": rospy.get_param("/eff_joint_traj_controller"),
                     "joint_state_controller": rospy.get_param("/joint_state_controller")},
        "robot_description_sha256": hashlib.sha256(urdf.encode()).hexdigest(),
        "urdf_limits": urdf_joint_limits(urdf, joints),
    }
    d = os.path.join(ROOT, "results", "task1", a.freeze_id)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "robot_description_%s.urdf" % a.label), "w").write(urdf)
    p = os.path.join(d, "probe_%s.json" % a.label)
    if os.path.exists(p):
        print("refused: %s exists" % p)
        sys.exit(12)
    json.dump(out, open(p, "w"), indent=2)
    print(json.dumps({k: out[k] for k in ("label", "sim_seconds", "wall_seconds_incl_setup")}, indent=1))
    bad = []
    if not out["model_pose_world"]["ok"]:
        bad.append("model pose service failed")
    if not out["controller_state_dt"].get("n") or not out["joint_states_dt"].get("n"):
        bad.append("no feedback samples")
    if out["gazebo_link_names"] is None:
        bad.append("no /gazebo/link_states")
    if bad:
        print("PROBE FAILED:", bad)
        sys.exit(1)


# ---------------------------------------------------------------- preflight (pure)
def cubic(u):
    return 3 * u * u - 2 * u ** 3


def preflight(cfg, limits):
    """Per case: endpoints/path inside URDF limits, peak speed/accel of the cubic, speed vs fraction of limit."""
    joints = cfg["robot"]["joints"]
    q0 = cfg["robot"]["q_init"]
    frac = cfg["trajectory"]["max_speed_fraction_of_velocity_limit"]
    margin = 0.01  # rad: the real q_start differs slightly from q_init (gravity sag); tolerated in the path check
    rows = {}
    ok_all = True
    for name, c in cfg["cases"].items():
        if c["dq"] is None:
            rows[name] = {"motion": False, "ok": True}
            continue
        T = float(c["T"])
        per = {}
        ok = True
        for i, j in enumerate(joints):
            dq = float(c["dq"][i])
            lo, hi, vmax = limits[j]["lower"], limits[j]["upper"], limits[j]["velocity"]
            lo_p = min(q0[i], q0[i] + dq) - margin
            hi_p = max(q0[i], q0[i] + dq) + margin
            # sample the cubic path: monotonic between endpoints, so extremes are the endpoints; verify numerically
            path = [q0[i] + dq * cubic(k / 1000.0) for k in range(1001)]
            in_lim = lo <= lo_p and hi_p <= hi and lo <= min(path) and max(path) <= hi
            v_peak = 1.5 * abs(dq) / T
            a_peak = 6.0 * abs(dq) / T ** 2
            v_ok = v_peak <= frac * vmax + 1e-12
            ok = ok and in_lim and v_ok
            per[j] = {"dq": dq, "q_start_nominal": q0[i], "q_target_nominal": q0[i] + dq, "limit": [lo, hi],
                      "v_peak": v_peak, "a_peak": a_peak, "v_limit": vmax, "v_peak_over_limit": v_peak / vmax if vmax else None,
                      "within_limits_with_0p01_margin": in_lim, "speed_ok": v_ok}
        rows[name] = {"motion": True, "T": T, "ok": ok, "joints": per}
        ok_all = ok_all and ok
    return {"rule": "cubic s(u)=3u^2-2u^3: v_peak=1.5|dq|/T, a_peak=6|dq|/T^2; need path within URDF limits (+0.01 rad margin) and v_peak<=%.2f*URDF velocity limit; "
                    "URDF has no acceleration limit -> undefined, not invented" % frac,
            "cases": rows, "all_ok": ok_all}


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip(), r.returncode


def finalize(a):
    from task0_manifest import hash_sources
    cfg = yaml.safe_load(open(CONFIG))
    d = os.path.join(ROOT, "results", "task1", a.freeze_id)
    probes = {}
    for lab in a.labels:
        probes[lab] = json.load(open(os.path.join(d, "probe_%s.json" % lab)))
    base = probes[a.labels[0]]
    limits = base["urdf_limits"]
    pre = preflight(cfg, limits)
    # the normal and hf probes must see the same robot description
    desc_hashes = {k: v["robot_description_sha256"] for k, v in probes.items()}
    files = {
        "world": "src/forem_sim/worlds/ur5_empty.world", "launch": "src/forem_sim/launch/ur5_sim.launch",
        "urdf_xacro": "src/forem_sim/urdf/ur5_fixed.urdf.xacro", "controllers_normal": "config/control/ur5_controllers.yaml",
        "controllers_hf2000": cfg["timing"]["hf_controller_config"], "start_controllers": "src/forem_sim/scripts/start_controllers.py",
        "baseline_yaml": "config/experiments/task1/baseline.yaml"}
    container = "forem-dev"
    pk, _ = sh("bash %s/docker/run.sh exec bash -c \"dpkg-query -W ros-noetic-gazebo-ros-control ros-noetic-effort-controllers "
               "ros-noetic-joint-trajectory-controller ros-noetic-ur-description ros-noetic-topic-tools gazebo11; rosversion -d; python3 --version\"" % ROOT)
    out = {
        "freeze_id": a.freeze_id, "schema": "task1-baseline-freeze/1",
        "frozen_config": cfg,
        "evidence_classes": {"measured": "live probes of fresh sims (probe_*.json)", "source": "file hashes, package versions, header inspection",
                             "inferred": "listed under inferred_items; not used as measured"},
        "image_id": sh("docker inspect %s --format '{{.Image}}'" % container)[0],
        "container_id": sh("docker inspect %s --format '{{.Id}}'" % container)[0],
        "packages": pk.splitlines(),
        "git_head": sh("git -C %s rev-parse HEAD" % ROOT)[0],
        "file_sha256": {k: sha256(os.path.join(ROOT, v)) for k, v in files.items()},
        "source_sha256": hash_sources(ROOT),
        "robot_description_sha256": desc_hashes,
        "robot_description_same_in_all_probes": len(set(desc_hashes.values())) == 1,
        "urdf_limits": limits,
        "urdf_acceleration_limit": "undefined (URDF limit tag has no acceleration)",
        "preflight": pre,
        "probes": {k: {kk: vv for kk, vv in v.items() if kk not in ("rosparam", "urdf_limits")} for k, v in probes.items()},
        "controller_params_rosparam": base["rosparam"],
        "inferred_items": {
            "controller_update_period": "gazebo_ros_control (2.9.3) uses the Gazebo physics step when no controlPeriod is given in the URDF plugin "
                                        "(URDF has none) -> inferred 0.5 ms; confirmed only where the hf probe shows joint_states stamps 0.5 ms apart",
            "interpolation": "joint_trajectory_controller 0.22.0 + trajectory_interface quintic spline: two points with position+velocity, no acceleration "
                             "-> cubic Hermite; to be verified against controller desired in task1.2/1.3 data"},
    }
    out["ok"] = bool(pre["all_ok"] and out["robot_description_same_in_all_probes"])
    p = os.path.join(d, "baseline.json")
    if os.path.exists(p):
        print("refused: %s exists" % p)
        sys.exit(12)
    json.dump(out, open(p, "w"), indent=2)
    print(json.dumps({"baseline": p, "ok": out["ok"], "preflight_all_ok": pre["all_ok"]}))
    sys.exit(0 if out["ok"] else 1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe"); p.add_argument("--freeze-id", required=True); p.add_argument("--label", required=True)
    p.add_argument("--duration", type=float, default=6.0, help="simulated seconds to measure")
    f = sub.add_parser("finalize"); f.add_argument("--freeze-id", required=True); f.add_argument("--labels", nargs="+", required=True)
    a = ap.parse_args()
    {"probe": probe, "finalize": finalize}[a.cmd](a)


if __name__ == "__main__":
    main()
