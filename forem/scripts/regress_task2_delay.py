#!/usr/bin/env python3
"""Task2.2 ROS lifecycle regression of the fixed-delay proxy (RUNS INSIDE forem-dev; no Gazebo, no robot, no controller).

  sg docker -c 'bash forem/docker/run.sh exec python3 scripts/regress_task2_delay.py --tag task2.2-lc1'

A private roscore (port 11411, supervised through task0_proc.py) plus a fake /clock that this script controls (run / pause / jump back)
let the real task2_delay_node run on simulated time. The orchestrating script is itself a ROS node: it plays sender, the downstream
"controller" subscriber and the event recorder. Every scenario starts a fresh proxy process (new run-id, new events file).

 L1 delay 80 ms: no delivery before t_in+80 ms, delivery after, d_queue>=tau (eps>=0, small), message identical, event chain complete
 L2 delay 0: delivered inside the receive callback; same payload
 L3 paused clock: a pending message is NOT published while sim time stands still (1.5 s wall), published only after resume + due
 L4 FIFO: three messages, delivered in order, each not before its own due time
 L5 reset service: pending message dropped (reported), never delivered however far the clock runs; a new message works in the new epoch
 L6 clock jumps back: pending message dropped, node latches failed, nothing is published later, exit code 2
 L7 unsupported messages (non-zero header.stamp, extra point, wrong joint order): reject event, nothing published, failed latch, exit 2
 L8 overflow (65 messages with a paused clock, capacity 64): reject "queue full", nothing silently dropped/published, exit 2
 L9 identical payload twice: two entries, two deliveries (hash is not an identity)
 L10 SIGINT / SIGTERM with a message pending: pending discarded with reason shutdown, nothing published afterwards, no process left
 L11 SIGKILL of the proxy with a message pending: nothing published afterwards, supervisor cleanup leaves no residue
 L12 refusals: delay 100 ms / nan / inf / negative / text refused (exit 3); existing events file refused (3); /use_sim_time=false refused (4)
Writes results/task2/<tag>-report/lifecycle.json; exit 0 iff every scenario passes and no process of this test is left.
"""
import argparse
import json
import math
import os
import signal
import subprocess
import sys
import threading
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
PORT = 11411
os.environ["ROS_MASTER_URI"] = "http://127.0.0.1:%d" % PORT   # the container sets ROS_IP=127.0.0.1
SCRIPTS = os.path.join(ROOT, "scripts")
MS = 1_000_000
JOINTS = ["ur5_shoulder_pan_joint", "ur5_shoulder_lift_joint", "ur5_elbow_joint", "ur5_wrist_1_joint", "ur5_wrist_2_joint", "ur5_wrist_3_joint"]
LIMITS = {j: {"lower": -6.28, "upper": 6.28, "velocity": 3.14} for j in JOINTS}
IN_TOPIC, OUT_TOPIC, EV_TOPIC = "/task2/command_in", "/eff_joint_traj_controller/command", "/task2/delay_events"


# ---------------------------------------------------------------------------------------------- fake clock (subprocess role)
def clock_main(control_file, step_ms, rate_hz):
    import rospy
    from rosgraph_msgs.msg import Clock
    rospy.init_node("task2_fake_clock", disable_signals=False)
    pub = rospy.Publisher("/clock", Clock, queue_size=100)
    sim_ns = 0
    mode = "pause"
    last_cmd = None
    period = 1.0 / rate_hz
    nxt = time.time()
    while not rospy.is_shutdown():
        try:
            cmd = open(control_file).read().strip()
        except OSError:
            cmd = last_cmd or "pause"
        if cmd != last_cmd:
            last_cmd = cmd
            if cmd.startswith("jump "):
                sim_ns = int(cmd.split()[1])
                mode = "run"
            elif cmd in ("run", "pause"):
                mode = cmd
        if mode == "run":
            sim_ns += step_ms * MS
        m = Clock()
        m.clock = rospy.Time(sim_ns // 10 ** 9, sim_ns % 10 ** 9)
        pub.publish(m)
        nxt += period
        time.sleep(max(0.0, nxt - time.time()))


# ---------------------------------------------------------------------------------------------- orchestrator
def proc(*args, check=False):
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "task0_proc.py")] + list(args), capture_output=True, text=True)
    return r


class Env:
    def __init__(self, tag):
        import rospy
        self.rospy = rospy
        self.tag = tag
        self.logdir = os.path.join(ROOT, "logs", "task2", tag)
        os.makedirs(self.logdir, exist_ok=False)
        self.rel = os.path.relpath(self.logdir, ROOT)
        self.clockfile = os.path.join(self.logdir, "clock.ctl")
        self.out, self.events = [], []
        self.lock = threading.Lock()
        self.pub = None

    def start_master(self):
        r = proc("start", "--dir", self.rel, "--name", "master", "--", "roscore", "-p", str(PORT))
        assert r.returncode == 0, r.stdout + r.stderr
        for _ in range(100):
            if subprocess.run(["rosparam", "list"], capture_output=True).returncode == 0:
                break
            time.sleep(0.1)
        subprocess.run(["rosparam", "set", "/use_sim_time", "true"], check=True, capture_output=True)
        subprocess.run(["rosparam", "set", "/task2/test_limits", json.dumps(LIMITS)], check=True, capture_output=True)

    def start_clock(self, name="clock"):
        self.set_clock("pause")
        r = proc("start", "--dir", self.rel, "--name", name, "--allow-foreign", "--", sys.executable, os.path.abspath(__file__), "clock-role",
                 "--control-file", self.clockfile, "--step-ms", "1", "--rate-hz", "1000")
        assert r.returncode == 0, r.stdout
        self.clock_name = name

    def set_clock(self, cmd):
        tmp = self.clockfile + ".tmp"
        open(tmp, "w").write(cmd)
        os.replace(tmp, self.clockfile)

    def init_node(self):
        rospy = self.rospy
        from std_msgs.msg import String
        from trajectory_msgs.msg import JointTrajectory
        rospy.init_node("task2_regress", disable_signals=True)
        rospy.Subscriber(OUT_TOPIC, JointTrajectory, self._on_out, queue_size=1000)
        rospy.Subscriber(EV_TOPIC, String, self._on_ev, queue_size=1000)
        self.pub = rospy.Publisher(IN_TOPIC, JointTrajectory, queue_size=100)

    def _on_out(self, m):
        with self.lock:
            self.out.append((self.rospy.Time.now().to_nsec(), m))

    def _on_ev(self, m):
        with self.lock:
            self.events.append(json.loads(m.data))

    def now_ns(self):
        return self.rospy.Time.now().to_nsec()

    def wait_sim(self, target_ns, timeout=30.0):
        t0 = time.time()
        while self.now_ns() < target_ns:
            if time.time() - t0 > timeout:
                raise RuntimeError("sim time did not reach %d (now %d)" % (target_ns, self.now_ns()))
            time.sleep(0.002)

    def reset_collect(self):
        with self.lock:
            self.out, self.events = [], []

    def start_node(self, scn, delay_ms, name="node", extra=()):
        d = os.path.join(self.logdir, scn)
        os.makedirs(d, exist_ok=True)
        rel = os.path.relpath(d, ROOT)
        self.node_rel, self.node_name = rel, name
        self.events_file = os.path.join(d, "delay_events.jsonl")
        cmd = [sys.executable, os.path.join(SCRIPTS, "task2_delay_node.py"), "--run-id", "%s-%s" % (self.tag, scn), "--delay-ms", str(delay_ms),
               "--events-file", self.events_file, "--expected-connections", "1"] + list(extra)
        r = proc("start", "--dir", rel, "--name", name, "--allow-foreign", "--", *cmd)
        assert r.returncode == 0, r.stdout
        return rel

    def wait_ready(self, timeout=30):
        logp = os.path.join(ROOT, self.node_rel, self.node_name + ".log")
        t0 = time.time()
        while time.time() - t0 < timeout:
            if os.path.exists(logp) and "ready" in open(logp).read():
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("node not ready: " + (open(logp).read() if os.path.exists(logp) else "no log"))
        t0 = time.time()
        while self.pub.get_num_connections() < 1 and time.time() - t0 < 10:
            time.sleep(0.02)
        assert self.pub.get_num_connections() >= 1, "node did not subscribe to the input topic"

    def stop_node(self):
        r = proc("stop", "--dir", self.node_rel, "--name", self.node_name)
        return r.returncode

    def node_exit_code(self):
        r = proc("exitcode", "--dir", self.node_rel, "--name", self.node_name)
        try:
            return json.loads(r.stdout).get("exit_code")
        except ValueError:
            return None

    def read_events_file(self):
        if not os.path.exists(self.events_file):
            return []
        return [json.loads(l) for l in open(self.events_file) if l.strip()]

    def send(self, record_msg):
        self.pub.publish(record_msg)


def make_msg(dq=(0.3, 0.2, -0.3, 0.2, 0.3, 0.4), T=3.0, stamp=(0, 0), names=None, npoints=2, q0=(0.0, -1.5708, 0.0, -1.5708, 0.0, 0.0), tag=0.0):
    from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
    import rospy
    m = JointTrajectory()
    m.header.stamp = rospy.Time(*stamp)
    m.joint_names = list(names or JOINTS)
    q0 = [x + tag for x in q0]
    pts = [JointTrajectoryPoint(positions=q0, velocities=[0.0] * 6, time_from_start=rospy.Duration(0.0)),
           JointTrajectoryPoint(positions=[a + b for a, b in zip(q0, dq)], velocities=[0.0] * 6, time_from_start=rospy.Duration(T))]
    if npoints == 3:
        pts.append(JointTrajectoryPoint(positions=q0, velocities=[0.0] * 6, time_from_start=rospy.Duration(T + 1)))
    m.points = pts
    return m


def types(events, t):
    return [e for e in events if e["type"] == t]


# ---------------------------------------------------------------------------------------------- scenarios
def run_all(tag):
    import task1_lib as L
    env = Env(tag)
    report = {"tag": tag, "scenarios": []}
    started = []

    def record(name, ok, detail):
        report["scenarios"].append({"scenario": name, "pass": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + " :: " + json.dumps(detail, default=str)[:900], flush=True)

    try:
        env.start_master(); started.append("master")
        env.start_clock(); started.append("clock")
        env.init_node()
        env.set_clock("run")
        t0 = time.time()
        while env.now_ns() <= 0 and time.time() - t0 < 10:
            time.sleep(0.01)

        # ---- L1
        env.reset_collect(); env.start_node("L1", 80); env.wait_ready()
        m = make_msg()
        t_send = env.now_ns(); env.send(m)
        time.sleep(0.04)                                             # ~40 ms simulated: still before the 80 ms due time
        with env.lock:
            early = len(env.out)
        env.wait_sim(t_send + 200 * MS)
        time.sleep(0.05)
        with env.lock:
            out, evs = list(env.out), list(env.events)
        pubs = types(evs, "publish")
        enq = types(evs, "enqueue")
        same = len(out) == 1 and L.command_record(out[0][1]) == L.command_record(m)
        ok = (early == 0 and len(out) == 1 and same and len(pubs) == 1 and len(enq) == 1 and pubs[0]["eps_ns"] >= 0 and pubs[0]["eps_ns"] < 8 * MS
              and pubs[0]["d_queue_ns"] >= 80 * MS and out[0][0] >= enq[0]["t_in_ns"] + 80 * MS - 2 * MS)
        record("L1_delay_80ms", ok, {"early_deliveries": early, "n_out": len(out), "identical_record": same, "event_publish": pubs, "event_enqueue": enq,
                                     "arrival_minus_t_in_ms": (out[0][0] - enq[0]["t_in_ns"]) / MS if out else None,
                                     "header_seq_sent_vs_received": [m.header.seq, out[0][1].header.seq] if out else None})
        file_ev = env.read_events_file()
        record("L1_events_file_matches_topic", [e["type"] for e in file_ev if e["type"] != "node_exit"][:3] == ["ready", "enqueue", "publish"] and
               [e["n"] for e in file_ev] == sorted(e["n"] for e in file_ev), {"types": [e["type"] for e in file_ev]})
        env.stop_node()

        # ---- L2
        env.reset_collect(); env.start_node("L2", 0); env.wait_ready()
        m = make_msg(); env.send(m); time.sleep(0.3)
        with env.lock:
            out, evs = list(env.out), list(env.events)
        pubs = types(evs, "publish")
        record("L2_delay_0", len(out) == 1 and len(pubs) == 1 and L.command_record(out[0][1]) == L.command_record(m) and pubs[0]["d_queue_ns"] == pubs[0]["eps_ns"]
               and pubs[0]["eps_ns"] >= 0, {"n_out": len(out), "publish": pubs})
        env.stop_node()

        # ---- L3 pause
        env.reset_collect(); env.start_node("L3", 80); env.wait_ready()
        m = make_msg(); t_send = env.now_ns(); env.send(m); time.sleep(0.01)
        env.set_clock("pause"); time.sleep(0.05)
        frozen = env.now_ns()
        time.sleep(1.5)                                              # 1.5 s of WALL time with a standing clock
        with env.lock:
            n_paused = len(env.out)
        stood = env.now_ns() == frozen
        env.set_clock("run"); env.wait_sim(t_send + 300 * MS); time.sleep(0.05)
        with env.lock:
            out, evs = list(env.out), list(env.events)
        pubs = types(evs, "publish")
        record("L3_pause_does_not_deliver", stood and n_paused == 0 and len(out) == 1 and pubs and pubs[0]["t_pub_before_ns"] >= pubs[0]["t_in_ns"] + 80 * MS,
               {"clock_stood_still": stood, "delivered_while_paused": n_paused, "n_out_after_resume": len(out), "publish": pubs})
        env.stop_node()
        env.reset_collect(); env.start_node("L3b", 0); env.wait_ready()
        env.set_clock("pause"); time.sleep(0.05)
        m = make_msg(); env.send(m); time.sleep(0.3)
        with env.lock:
            n0 = len(env.out)
        env.set_clock("run")
        record("L3b_zero_delay_while_paused_is_delivered", n0 == 1, {"n_out_while_paused": n0})
        env.stop_node()

        # ---- L4 FIFO
        env.reset_collect(); env.start_node("L4", 80); env.wait_ready()
        sent = []
        for k in range(3):
            mk = make_msg(tag=0.001 * k)
            sent.append((env.now_ns(), mk)); env.send(mk); env.wait_sim(sent[-1][0] + 12 * MS)
        env.wait_sim(sent[0][0] + 400 * MS); time.sleep(0.05)
        with env.lock:
            out, evs = list(env.out), list(env.events)
        pubs = types(evs, "publish")
        in_order = [L.command_record(o[1]) for o in out] == [L.command_record(s[1]) for s in sent]
        not_early = all(p["t_pub_before_ns"] >= p["t_in_ns"] + 80 * MS for p in pubs)
        record("L4_fifo_three_messages", len(out) == 3 and in_order and not_early and [p["seq"] for p in pubs] == [0, 1, 2], {"n_out": len(out), "in_order": in_order, "seqs": [p["seq"] for p in pubs]})
        env.stop_node()

        # ---- L5 reset
        env.reset_collect(); env.start_node("L5", 80); env.wait_ready()
        env.set_clock("pause"); time.sleep(0.05)                     # the rosservice client needs ~0.3 s wall: keep sim time standing meanwhile
        m = make_msg(); env.send(m); time.sleep(0.2)
        r = subprocess.run(["rosservice", "call", "/task2/reset_delay"], capture_output=True, text=True)
        env.set_clock("run"); env.wait_sim(env.now_ns() + 1000 * MS); time.sleep(0.05)
        with env.lock:
            n_after = len(env.out); evs = list(env.events)
        drops = types(evs, "drop"); resets = types(evs, "reset")
        m2 = make_msg(tag=0.002); env.send(m2); t2 = env.now_ns(); env.wait_sim(t2 + 200 * MS); time.sleep(0.05)
        with env.lock:
            out2 = list(env.out); evs = list(env.events)
        enq2 = types(evs, "enqueue")
        record("L5_reset_no_leak", r.returncode == 0 and n_after == 0 and len(drops) == 1 and drops[0]["reason"] == "reset" and len(resets) == 1
               and len(out2) == 1 and L.command_record(out2[0][1]) == L.command_record(m2) and enq2[-1]["epoch"] == 1,
               {"service": r.stdout.strip(), "delivered_after_reset_old": n_after, "drop": drops, "new_epoch_enqueue": enq2[-1] if enq2 else None, "n_out_after_new": len(out2)})
        env.stop_node()

        # ---- L6 clock backward
        env.reset_collect(); env.start_node("L6", 160); env.wait_ready()
        m = make_msg(); env.send(m); time.sleep(0.02)
        env.set_clock("jump 1000000")                                # clock goes back to 1 ms
        time.sleep(0.3)
        env.set_clock("run"); env.wait_sim(env.now_ns() + 2000 * MS); time.sleep(0.05)
        m2 = make_msg(tag=0.003); env.send(m2); time.sleep(0.3)
        with env.lock:
            n_out = len(env.out); evs = list(env.events)
        rc_stop = env.stop_node()
        code = env.node_exit_code()
        record("L6_clock_backward_fails_and_latches", n_out == 0 and types(evs, "clock_backward") and types(evs, "fatal") and any(e["reason"].startswith("node already failed") for e in types(evs, "reject")) and code == 2,
               {"n_out": n_out, "types": [e["type"] for e in evs], "exit_code": code})
        env.set_clock("jump %d" % (env.now_ns() + 10 ** 9))
        time.sleep(0.1)
        env.set_clock("run")

        # ---- L7 unsupported
        for name, kw in (("nonzero_stamp", {"stamp": (7, 5)}), ("three_points", {"npoints": 3}), ("joint_order", {"names": list(reversed(JOINTS))}), ("too_fast", {"T": 0.2})):
            env.reset_collect(); env.start_node("L7_" + name, 0); env.wait_ready()
            env.send(make_msg(**kw)); time.sleep(0.3)
            env.send(make_msg()); time.sleep(0.3)                    # a valid message after the failure must NOT pass either
            with env.lock:
                n_out = len(env.out); evs = list(env.events)
            env.stop_node(); code = env.node_exit_code()
            rej = types(evs, "reject")
            record("L7_unsupported_" + name, n_out == 0 and rej and "unsupported" in rej[0]["reason"] and types(evs, "fatal") and code == 2, {"n_out": n_out, "reject": rej[:1], "exit_code": code})

        # ---- L8 overflow
        env.reset_collect(); env.start_node("L8", 80); env.wait_ready()
        env.set_clock("pause"); time.sleep(0.05)
        for k in range(65):
            env.send(make_msg(tag=1e-6 * k)); time.sleep(0.002)
        time.sleep(0.5)
        with env.lock:
            evs = list(env.events); n0 = len(env.out)
        env.set_clock("run"); env.wait_sim(env.now_ns() + 500 * MS); time.sleep(0.1)
        with env.lock:
            n1 = len(env.out)
        env.stop_node(); code = env.node_exit_code()
        rej = [e for e in types(evs, "reject") if "queue full" in e.get("reason", "")]
        drops = types(evs, "drop")
        record("L8_overflow_is_an_error", len(types(evs, "enqueue")) == 64 and len(rej) == 1 and len(drops) == 64 and n0 == 0 and n1 == 0 and code == 2,
               {"enqueued": len(types(evs, "enqueue")), "reject": rej[:1], "dropped_with_reason": len(drops), "drop_reasons": sorted({e['reason'] for e in drops}), "delivered": [n0, n1], "exit_code": code})

        # ---- L9 identical payload twice
        env.reset_collect(); env.start_node("L9", 80); env.wait_ready()
        m = make_msg(); t = env.now_ns(); env.send(m); env.wait_sim(t + 12 * MS); env.send(m); env.wait_sim(t + 300 * MS); time.sleep(0.05)
        with env.lock:
            out = list(env.out); evs = list(env.events)
        pubs = types(evs, "publish")
        record("L9_identical_payload_two_entries", len(out) == 2 and len(pubs) == 2 and pubs[0]["payload_hash"] == pubs[1]["payload_hash"] and [p["seq"] for p in pubs] == [0, 1],
               {"n_out": len(out), "seqs": [p["seq"] for p in pubs]})
        env.stop_node()

        # ---- L10 INT / TERM with a pending message
        for sig, nm in ((signal.SIGINT, "INT"), (signal.SIGTERM, "TERM")):
            env.reset_collect(); env.start_node("L10_" + nm, 160); env.wait_ready()
            env.set_clock("pause"); time.sleep(0.05)
            env.send(make_msg()); time.sleep(0.3)
            meta = json.load(open(os.path.join(ROOT, env.node_rel, "node.json"))) if os.path.exists(os.path.join(ROOT, env.node_rel, "node.json")) else None
            root_pid = meta["root"]["pid"] if meta else None
            if root_pid:
                os.kill(root_pid, sig)
            time.sleep(1.0)
            env.set_clock("run"); env.wait_sim(env.now_ns() + 1000 * MS); time.sleep(0.1)
            with env.lock:
                n_out = len(env.out)
            fev = env.read_events_file()
            left = proc("grep", "--needle", "%s-L10_%s" % (tag, nm)).stdout.strip()
            code = env.node_exit_code()
            env.stop_node()
            drops = [e for e in fev if e["type"] == "drop"]
            record("L10_%s_pending_discarded_not_drained" % nm, n_out == 0 and len(drops) == 1 and drops[0]["reason"] == "shutdown" and fev[-1]["type"] == "node_exit" and left in ("", "[]"),
                   {"n_out": n_out, "drops": drops, "last_event": fev[-1]["type"] if fev else None, "left_by_cmdline": left, "exit_code": code})

        # ---- L11 SIGKILL
        env.reset_collect(); env.start_node("L11", 160); env.wait_ready()
        env.set_clock("pause"); time.sleep(0.05)
        env.send(make_msg()); time.sleep(0.3)
        meta = json.load(open(os.path.join(ROOT, env.node_rel, "node.json")))
        os.kill(meta["root"]["pid"], signal.SIGKILL)
        time.sleep(0.5)
        env.set_clock("run"); env.wait_sim(env.now_ns() + 1000 * MS); time.sleep(0.1)
        with env.lock:
            n_out = len(env.out)
        rc = env.stop_node()
        left = proc("grep", "--needle", "%s-L11" % tag).stdout.strip()
        code = env.node_exit_code()
        record("L11_sigkill_nothing_published_no_residue", n_out == 0 and rc == 0 and left in ("", "[]") and code == -9, {"n_out": n_out, "stop_rc": rc, "left": left, "exit_code": code})

        # ---- L12 refusals
        refused = {}
        for val in ("100", "nan", "inf", "-5", "abc", "80.5", "1e9"):
            d = os.path.join(env.logdir, "L12_" + val.replace(".", "p").replace("-", "m"))
            os.makedirs(d)
            r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "task2_delay_node.py"), "--run-id", "x", "--delay-ms", val, "--events-file", os.path.join(d, "e.jsonl")],
                               capture_output=True, text=True, timeout=60)
            refused[val] = r.returncode
        d = os.path.join(env.logdir, "L12_exists"); os.makedirs(d); open(os.path.join(d, "e.jsonl"), "w").write("old\n")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "task2_delay_node.py"), "--run-id", "x", "--delay-ms", "80", "--events-file", os.path.join(d, "e.jsonl")], capture_output=True, text=True, timeout=60)
        refused["events_file_exists"] = r.returncode
        refused["events_file_untouched"] = open(os.path.join(d, "e.jsonl")).read() == "old\n"
        subprocess.run(["rosparam", "set", "/use_sim_time", "false"], check=True, capture_output=True)
        d = os.path.join(env.logdir, "L12_wallclock"); os.makedirs(d)
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "task2_delay_node.py"), "--run-id", "x", "--delay-ms", "80", "--events-file", os.path.join(d, "e.jsonl")], capture_output=True, text=True, timeout=60)
        refused["use_sim_time_false"] = r.returncode
        subprocess.run(["rosparam", "set", "/use_sim_time", "true"], check=True, capture_output=True)
        want3 = all(refused[k] == 3 for k in ("100", "nan", "inf", "-5", "abc", "80.5", "1e9", "events_file_exists"))
        record("L12_refusals", want3 and refused["use_sim_time_false"] == 4 and refused["events_file_untouched"], refused)
    except Exception as e:   # noqa: BLE001 - any harness failure is a failed regression, with the evidence kept
        import traceback
        record("HARNESS_ERROR", False, {"error": repr(e), "trace": traceback.format_exc()[-1500:]})
    finally:
        for nm in ("node", "clock", "master"):
            for rel_dir in {env.logdir} | {os.path.join(env.logdir, d) for d in os.listdir(env.logdir) if os.path.isdir(os.path.join(env.logdir, d))}:
                if os.path.exists(os.path.join(rel_dir, nm + ".json")):
                    proc("stop", "--dir", os.path.relpath(rel_dir, ROOT), "--name", nm)
        left = proc("foreign").stdout.strip()
        left_test = proc("grep", "--needle", "--run-id " + tag).stdout.strip()
        record("NO_RESIDUE", left == "[]" and left_test in ("", "[]"), {"foreign": left, "by_cmdline": left_test})
        outdir = os.path.join(ROOT, "results", "task2", tag + "-report")
        os.makedirs(outdir, exist_ok=True)
        report["pass"] = all(s["pass"] for s in report["scenarios"])
        json.dump(report, open(os.path.join(outdir, "lifecycle.json"), "w"), indent=1, default=str)
    sys.exit(0 if report["pass"] else 1)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "clock-role":
        ap = argparse.ArgumentParser()
        ap.add_argument("role")
        ap.add_argument("--control-file", required=True)
        ap.add_argument("--step-ms", type=int, default=1)
        ap.add_argument("--rate-hz", type=float, default=1000.0)
        a = ap.parse_args()
        clock_main(a.control_file, a.step_ms, a.rate_hz)
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    if os.path.exists(os.path.join(ROOT, "logs", "task2", a.tag)):
        print("refused: tag already has logs")
        sys.exit(12)
    r = proc("foreign")
    if r.returncode != 0:
        print("refused: foreign ROS/Gazebo processes present:", r.stdout)
        sys.exit(10)
    run_all(a.tag)


if __name__ == "__main__":
    main()
