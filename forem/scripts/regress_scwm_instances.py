#!/usr/bin/env python3
"""Isolation regression for scripts/scwm_instance.py (task4.8.1). Runs INSIDE forem-dev and starts/stops REAL simulations
(2 instances, numbers --a/--b). The caller must own the machine (logs/task4/.sim_exclusive).

  python3 scripts/regress_scwm_instances.py --run-id t4.8.1-regress-r1

Also contains the child modes used by the test and by the throughput benchmark:
  --child pose-pub   publish a base velocity for a few seconds, then print the model pose before/after (JSON)
  --child env-driver Task3Env reset/step driver (import ray FIRST, see task3_env.py)
Result: results/task4/<run-id>/regress.json (every check true/false) ; exit 0 only if all checks pass.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

FOREM = Path(__file__).resolve().parent.parent
INST = FOREM / "scripts" / "scwm_instance.py"


# ------------------------------------------------------------------ child modes
def child_pose_pub(a):
    import rospy
    from gazebo_msgs.msg import ModelStates
    from geometry_msgs.msg import Twist

    def pose():
        m = rospy.wait_for_message("/gazebo/model_states", ModelStates, timeout=10)
        i = m.name.index("husky_ur5")
        return [m.pose[i].position.x, m.pose[i].position.y], list(m.name)

    rospy.init_node("regress_pose_pub", anonymous=True)
    p0, names = pose()
    if a.speed:
        pub = rospy.Publisher("/husky_velocity_controller/cmd_vel", Twist, queue_size=1)
        rospy.sleep(0.5)
        t = Twist()
        t.linear.x = a.speed
        end = time.time() + a.seconds
        while time.time() < end:
            pub.publish(t)
            time.sleep(0.05)
        pub.publish(Twist())
        time.sleep(0.5)
    p1, _ = pose()
    print(json.dumps({"p0": p0, "p1": p1, "names": names, "n_husky": names.count("husky_ur5")}))


def child_env_driver(a):
    import ray  # noqa: F401  -- MUST be the first heavy import
    import torch  # noqa: F401
    import numpy as np
    sys.path.insert(0, str(FOREM / "scripts"))
    import task3_env as T
    import rospy

    out = {"inst": os.environ.get("FOREM_INSTANCE"), "ros_master": os.environ.get("ROS_MASTER_URI"), "phases": []}
    rng = np.random.default_rng(1000 + int(os.environ.get("FOREM_INSTANCE", 0)))
    env = T.Task3Env(seed=a.seed)
    t0 = time.time()
    env.reset(seed=a.seed)
    out["reset_s"] = round(time.time() - t0, 3)
    out["spec_hash"] = env.episode_spec["hash"]
    out["models_seen"] = env.gazebo_model_names()
    nres = 1
    reset_times = [out["reset_s"]]

    def run(n):
        nonlocal nres
        s0, w0 = rospy.get_time(), time.time()
        done_n = 0
        reset_wall = 0.0
        reset_sim = 0.0
        for _ in range(n):
            _, _, done, _ = env.step(rng.uniform(-1, 1, 3))
            if done:
                t1, ts1 = time.time(), rospy.get_time()
                env.reset(seed=a.seed + 1 + nres)
                reset_wall += time.time() - t1
                reset_sim += rospy.get_time() - ts1
                reset_times.append(round(time.time() - t1, 3))
                nres += 1
                done_n += 1
        s1, w1 = rospy.get_time(), time.time()
        # rates exclude time spent in env.reset() (reported separately in reset_times_s)
        ww, ss = (w1 - w0) - reset_wall, (s1 - s0) - reset_sim
        return {"steps": n, "t_start": w0, "t_end": w1, "wall_s": round(w1 - w0, 3), "reset_wall_s": round(reset_wall, 3),
                "sim_s": round(s1 - s0, 3), "steps_per_s": round(n / ww, 2), "sim_per_wall": round(ss / ww, 3),
                "wall_per_step_ms": round(1000 * ww / n, 2), "episodes_reset_in_phase": done_n}

    if a.ready_file:
        Path(a.ready_file).write_text("ready")
    if a.start_flag:       # synchronous start so that K drivers measure the same time window
        while not os.path.exists(a.start_flag):
            time.sleep(0.05)
    out["phases"].append(run(a.steps))
    if a.force_reset_mid:  # guarantee at least one reset inside the measured window
        t1 = time.time()
        env.reset(seed=a.seed + 100)
        reset_times.append(round(time.time() - t1, 3))
    if a.wait_flag:
        out["waiting"] = True
        Path(a.out).write_text(json.dumps(out))
        while not os.path.exists(a.wait_flag):
            time.sleep(0.1)
        ok, err = True, None
        try:
            out["phases"].append(run(a.steps2))
        except BaseException as e:  # noqa: BLE001
            ok, err = False, repr(e)
        out["phase2_ok"] = ok
        out["phase2_error"] = err
        out["waiting"] = False
    out["reset_times_s"] = reset_times
    Path(a.out).write_text(json.dumps(out))
    try:
        env.close()
    except Exception:
        pass
    print(json.dumps(out))


# ------------------------------------------------------------------ harness
def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def inst(*args):
    return sh([sys.executable, str(INST)] + [str(x) for x in args])


def ex(k, cmd, timeout=180):
    return sh([sys.executable, str(INST), "exec", "--inst", str(k), "--"] + cmd, timeout=timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", choices=("pose-pub", "env-driver"))
    ap.add_argument("--run-id")
    ap.add_argument("--a", type=int, default=0)
    ap.add_argument("--b", type=int, default=1)
    ap.add_argument("--speed", type=float, default=0.0)
    ap.add_argument("--seconds", type=float, default=3.0)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--steps2", type=int, default=20)
    ap.add_argument("--out")
    ap.add_argument("--wait-flag")
    ap.add_argument("--start-flag")
    ap.add_argument("--ready-file")
    ap.add_argument("--force-reset-mid", action="store_true")
    a = ap.parse_args()
    if a.child == "pose-pub":
        return child_pose_pub(a)
    if a.child == "env-driver":
        return child_env_driver(a)
    if not a.run_id:
        ap.error("--run-id required")

    A, B = a.a, a.b
    res_dir = FOREM / "results" / "task4" / a.run_id
    log_dir = FOREM / "logs" / "task4" / a.run_id
    res_dir.mkdir(parents=True, exist_ok=True)
    C = {}          # check name -> bool
    N = {}          # notes / evidence
    me = str(Path(__file__))

    def check(name, ok, note=None):
        C[name] = bool(ok)
        if note is not None:
            N[name] = note
        print(("PASS " if ok else "FAIL ") + name, flush=True)

    def start(k, rid):
        r = inst("start", "--inst", k, "--run-id", rid)
        return r

    try:
        # 0. both numbers must be unused
        for k in (A, B):
            check("pre_instance_%d_unregistered" % k, inst("status", "--inst", k).returncode == 2)
        # 1. start A and B concurrently
        ps = [subprocess.Popen([sys.executable, str(INST), "start", "--inst", str(k), "--run-id", a.run_id],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) for k in (A, B)]
        outs = [p.communicate()[0] for p in ps]
        check("start_A_B_rc0", all(p.returncode == 0 for p in ps), outs)
        # 2. duplicate start refused
        r = inst("start", "--inst", A, "--run-id", a.run_id + "-dup")
        check("duplicate_start_refused_rc11", r.returncode == 11, r.stdout.strip())
        check("duplicate_start_created_no_evidence", not (log_dir.parent / (a.run_id + "-dup")).exists())

        # 3. separate masters, node sets disjoint, params disjoint
        nodes = {}
        for k in (A, B):
            r = ex(k, ["rosnode", "list", "-a"])
            nodes[k] = [l.split() for l in r.stdout.strip().splitlines()]
        uris = {k: {l[0] for l in nodes[k]} for k in nodes}
        check("node_uris_disjoint_between_masters", uris[A] and uris[B] and not (uris[A] & uris[B]), {str(k): sorted(v)[:6] for k, v in uris.items()})
        exp = ["/gazebo", "/move_group", "/pose_bridge", "/robot_state_publisher", "/twist_mux"]
        for k in (A, B):
            r = ex(k, ["rosnode", "list"])
            names = set(r.stdout.split())
            check("expected_nodes_in_master_%d" % k, all(n in names for n in exp), sorted(names)[:40])
        ex(A, ["rosparam", "set", "/isolation_marker", "from_A"])
        pa = ex(A, ["rosparam", "get", "/isolation_marker"]).stdout.strip()
        pb = ex(B, ["rosparam", "get", "/isolation_marker"])
        check("param_set_on_A_invisible_on_B", pa == "from_A" and pb.returncode != 0 and "from_A" not in pb.stdout, [pa, pb.stderr.strip()[:80]])
        # topic publisher check: /clock publishers each in own master
        # 4. each instance: exactly one husky_ur5; motion only in A
        pm = {}
        for k, sp in ((A, 0.5), (B, 0.0)):
            pm[k] = None
        pA = subprocess.Popen([sys.executable, str(INST), "exec", "--inst", str(A), "--", sys.executable, me, "--child", "pose-pub", "--speed", "0.5", "--seconds", "3"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        pB = subprocess.Popen([sys.executable, str(INST), "exec", "--inst", str(B), "--", sys.executable, me, "--child", "pose-pub", "--speed", "0", "--seconds", "3"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        oa, ea = pA.communicate()
        ob, eb = pB.communicate()
        try:
            ja, jb = json.loads(oa.strip().splitlines()[-1]), json.loads(ob.strip().splitlines()[-1])
        except Exception as e:  # noqa: BLE001
            ja = jb = None
            N["pose_pub_error"] = [oa[-300:], ea[-300:], ob[-300:], eb[-300:], repr(e)]
        check("one_husky_ur5_per_instance", ja and jb and ja["n_husky"] == 1 and jb["n_husky"] == 1 and "husky_ur5" in ja["names"],
              [ja and ja["names"], jb and jb["names"]])
        if ja and jb:
            dA = ((ja["p1"][0] - ja["p0"][0]) ** 2 + (ja["p1"][1] - ja["p0"][1]) ** 2) ** 0.5
            dB = ((jb["p1"][0] - jb["p0"][0]) ** 2 + (jb["p1"][1] - jb["p0"][1]) ** 2) ** 0.5
            check("only_A_moves_on_A_velocity_command", dA > 0.5 and dB < 0.02, {"displacement_A_m": dA, "displacement_B_m": dB})
        else:
            check("only_A_moves_on_A_velocity_command", False)

        # 5. Task3Env on both simultaneously, spec hash equal; B waits for the flag
        flag = res_dir / "b_go.flag"
        outA, outB = res_dir / "driver_A.json", res_dir / "driver_B.json"
        for f in (flag, outA, outB):
            f.unlink(missing_ok=True)
        dA = subprocess.Popen([sys.executable, str(INST), "exec", "--inst", str(A), "--", sys.executable, me, "--child", "env-driver", "--seed", "7",
                               "--steps", "10", "--out", str(outA)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        dB = subprocess.Popen([sys.executable, str(INST), "exec", "--inst", str(B), "--", sys.executable, me, "--child", "env-driver", "--seed", "7",
                               "--steps", "10", "--steps2", "20", "--wait-flag", str(flag), "--out", str(outB)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        a_out, a_err = dA.communicate(timeout=600)
        check("env_driver_A_rc0", dA.returncode == 0, a_err[-300:])
        # wait for B's phase 1
        t0 = time.time()
        while time.time() - t0 < 300:
            try:
                if json.loads(outB.read_text()).get("waiting"):
                    break
            except Exception:
                pass
            time.sleep(0.5)
        jA = json.loads(outA.read_text()) if outA.exists() else {}
        jB = json.loads(outB.read_text()) if outB.exists() else {}
        check("spec_hash_equal_between_instances", jA.get("spec_hash") and jA.get("spec_hash") == jB.get("spec_hash"), [jA.get("spec_hash"), jB.get("spec_hash")])
        check("each_env_sees_own_master", jA.get("ros_master", "").endswith(str(11400 + A)) and jB.get("ros_master", "").endswith(str(11400 + B)))
        check("each_env_sees_single_husky", jA.get("models_seen", []).count("husky_ur5") == 1 and jB.get("models_seen", []).count("husky_ur5") == 1)

        # 6. stop A while B's env is alive; B must still step
        r = inst("stop", "--inst", A)
        check("stop_A_rc0_clean", r.returncode == 0, r.stdout.strip())
        check("residue_A_empty_after_stop", inst("residue", "--inst", A).returncode == 0)
        check("B_still_alive_after_A_stop", inst("status", "--inst", B).returncode == 0)
        flag.write_text("go")
        b_out, b_err = dB.communicate(timeout=300)
        jB = json.loads(outB.read_text())
        check("B_steps_after_A_stopped", dB.returncode == 0 and jB.get("phase2_ok") is True, [jB.get("phase2_error"), b_err[-200:]])

        # 7. solo hash: restart A as 'solo' (only B+A: B has no env) -> same hash from a fresh single env process
        r = inst("start", "--inst", A, "--run-id", a.run_id + "-r2")
        check("restart_A_rc0", r.returncode == 0, r.stdout.strip())
        outS = res_dir / "driver_A_again.json"
        outS.unlink(missing_ok=True)
        rs = ex(A, [sys.executable, me, "--child", "env-driver", "--seed", "7", "--steps", "5", "--out", str(outS)], timeout=600)
        jS = json.loads(outS.read_text()) if outS.exists() else {}
        check("spec_hash_equal_after_restart", jS.get("spec_hash") == jA.get("spec_hash"), [jS.get("spec_hash"), rs.stderr[-200:]])

        # 8. failure path: kill B's gzserver; A unaffected; stop B is clean
        killed = []
        for p in os.listdir("/proc"):
            if not p.isdigit():
                continue
            try:
                env = open("/proc/%s/environ" % p, "rb").read().split(b"\0")
                cl = open("/proc/%s/cmdline" % p, "rb").read().split(b"\0")[0].decode()
            except OSError:
                continue
            if ("IGN_PARTITION=forem_inst%d" % B).encode() in env and cl.endswith("gzserver"):
                os.kill(int(p), 9)
                killed.append(int(p))
        N["killed_gzserver_B"] = killed
        check("killed_B_gzserver", bool(killed))
        time.sleep(2)
        pr = ex(A, [sys.executable, me, "--child", "pose-pub", "--speed", "0", "--seconds", "1"])
        check("A_unaffected_by_B_gzserver_kill", pr.returncode == 0 and '"n_husky": 1' in pr.stdout, pr.stderr[-200:])
        r = inst("stop", "--inst", B)
        check("stop_B_after_gzserver_kill_clean", r.returncode == 0, r.stdout.strip())
        check("residue_B_empty", inst("residue", "--inst", B).returncode == 0)
        check("A_alive_after_B_stop", inst("status", "--inst", A).returncode == 0)
    finally:
        # cleanup of this test's own instances only
        for k in (A, B):
            if inst("status", "--inst", k).returncode != 2:
                r = inst("stop", "--inst", k)
                N["final_stop_%d" % k] = [r.returncode, r.stdout.strip()[:300]]
        for k in (A, B):
            C["final_residue_%d_empty" % k] = inst("residue", "--inst", k).returncode == 0
            ports = __import__("socket")
            import scwm_instance as S  # noqa: E402
            C["final_ports_free_%d" % k] = S.port_free(S.ROS_BASE + k) and S.port_free(S.GZ_BASE + k)
        (res_dir / "regress.json").write_text(json.dumps({"checks": C, "notes": N, "all_pass": all(C.values())}, indent=2))
        print("ALL PASS" if all(C.values()) else "SOME FAILED", "->", res_dir / "regress.json")
    sys.exit(0 if all(C.values()) else 1)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
