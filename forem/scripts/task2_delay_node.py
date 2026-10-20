#!/usr/bin/env python3
"""Task2 fixed-delay proxy (runs inside forem-dev). Delays WHOLE JointTrajectory messages by a fixed number of SIMULATED nanoseconds.

  /task2/command_in  --(queue, tau)-->  /eff_joint_traj_controller/command

* Time comes only from /clock messages: a message received at clock time t_in leaves in the /clock callback whose time is >= t_in + tau
  (tau = 0 leaves inside the receive callback). The host wall clock and sleep are never used to delay or release anything; if /clock stops
  (paused simulation) nothing that is not yet due is published.
* Only the frozen supported message is forwarded (header.stamp=0, two points, ...): anything else is a fatal reject, never rewritten.
  The forwarded object is the received message itself: nothing is copied field by field, so nothing can be altered.
* After a fatal reject/overflow the node latches `failed`: it publishes nothing more, keeps reporting rejects, and exits non-zero.
* Events (schema task2-delay-event/1) go to /task2/delay_events (std_msgs/String JSON, recorded in the bag) and, redundantly, to --events-file.
* /task2/reset_delay (std_srvs/Trigger, engineering tests): discards pending messages, new epoch. It cannot recall a trajectory that the
  controller has already received.
* Shutdown (INT/TERM) discards pending messages with reason "shutdown" and does not drain them.
Exit codes: 0 clean; 2 failed (reject/overflow/clock backward during the run); 3 invalid request; 4 setup failed.
"""
import argparse
import json
import os
import signal
import sys
import threading
import time

import rospy
import yaml
from rosgraph_msgs.msg import Clock
from std_msgs.msg import String
from std_srvs.srv import Trigger, TriggerResponse
from trajectory_msgs.msg import JointTrajectory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task1_freeze as F  # noqa: E402  (urdf_joint_limits)
import task1_lib as L  # noqa: E402  (command_record)
import task2_delay_queue as Q  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SCHEMA = "task2-delay-event/1"


class Proxy:
    def __init__(self, a, cfg, limits):
        d = cfg["delay"]
        self.run_id = a.run_id
        self.joints = cfg["robot"]["joints"]
        self.limits = limits
        self.frac = cfg["trajectory"]["max_speed_fraction_of_velocity_limit"]
        self.queue = Q.DelayQueue(int(a.delay_ms) * 1_000_000, capacity=d["queue_capacity"])
        self.lock = threading.RLock()
        self.clock_ns = None
        self.next_seq = 0
        self.failed = None
        self.closed = False
        self.n_events = 0
        self.counts = {"enqueued": 0, "published": 0, "rejected": 0, "dropped": 0}
        self.events_file = open(a.events_file, "a", buffering=1)
        self.pub_events = rospy.Publisher(d["topics"]["events"], String, queue_size=1000)
        self.pub_out = rospy.Publisher(a.out_topic, JointTrajectory, queue_size=64)
        self.expected_conn = a.expected_connections if a.expected_connections is not None else d["publisher_expected_connections"]

    # ------------------------------------------------------------------ events
    def emit(self, events):
        for e in events:
            self.n_events += 1
            e = dict(e, schema=SCHEMA, run_id=self.run_id, n=self.n_events, t_node_clock_ns=self.clock_ns, node=rospy.get_name())
            for key, c in (("enqueue", "enqueued"), ("publish", "published"), ("reject", "rejected"), ("drop", "dropped")):
                if e["type"] == key:
                    self.counts[c] += 1
            line = json.dumps(e, sort_keys=True)
            self.events_file.write(line + "\n")
            try:
                self.pub_events.publish(String(data=line))
            except Exception:   # noqa: BLE001 - publisher may already be closed during shutdown; the file keeps the record
                pass

    def fail(self, reason, extra=None):
        """Latch the failed state: drop what is pending (reported), publish nothing from now on."""
        if self.failed is None:
            self.failed = reason
            self.emit(self.queue.discard("node_failed", self.clock_ns))
            self.emit([{"type": "fatal", "reason": reason, "epoch": self.queue.epoch, "queue_len": 0}])
            try:
                rospy.set_param("/task2/delay_failed", reason)
            except Exception:   # noqa: BLE001
                pass

    # ------------------------------------------------------------------ queue -> controller
    def deliver(self, now_ns):
        """Called under the lock with the simulation time that has been reached. Publishes everything due, in order."""
        if self.failed or self.closed:
            return
        items, evs = self.queue.advance(now_ns)
        self.emit([e for e in evs if e["type"] != "due"])
        if any(e["type"] == "clock_backward" for e in evs):
            self.fail("simulation clock went backwards while running; pending commands discarded")
            return
        for it in items:
            before = self.clock_ns
            self.pub_out.publish(it.payload)
            after = max(self.clock_ns, rospy.Time.now().to_nsec())
            self.emit([{"type": "publish", "epoch": it.epoch, "seq": it.seq, "payload_hash": it.payload_hash, "t_in_ns": it.recv_ns,
                        "t_due_ns": it.due_ns, "t_pub_before_ns": before, "t_pub_after_ns": after, "d_queue_ns": before - it.recv_ns,
                        "eps_ns": before - it.recv_ns - self.queue.delay_ns, "delay_ns": self.queue.delay_ns, "queue_len": len(self.queue)}])

    # ------------------------------------------------------------------ callbacks
    def on_clock(self, m):
        with self.lock:
            if self.closed:
                return
            ns = m.clock.to_nsec()
            self.clock_ns = ns
            self.deliver(ns)

    def on_command(self, msg):
        with self.lock:
            if self.closed:
                return
            if self.failed:
                self.emit([{"type": "reject", "reason": "node already failed: %s" % self.failed, "epoch": self.queue.epoch, "queue_len": len(self.queue)}])
                return
            t_in = self.clock_ns
            if t_in is None:
                self.fail("command received before the first /clock message")
                return
            rec = L.command_record(msg)
            h = Q.payload_hash(rec)
            problems = Q.validate_command(rec, self.joints, self.limits, self.frac)
            if problems:
                self.emit([{"type": "reject", "reason": "unsupported message: " + "; ".join(problems), "epoch": self.queue.epoch, "t_in_ns": t_in,
                            "payload_hash": h, "queue_len": len(self.queue)}])
                self.fail("unsupported command message")
                return
            seq = self.next_seq
            try:
                evs = self.queue.enqueue(self.queue.epoch, seq, t_in, msg, payload_hash=h)
            except Q.QueueError as e:
                self.emit([e.event])
                self.fail("queue error: %s" % e)
                return
            self.next_seq += 1
            self.emit(evs)
            self.deliver(t_in)

    def on_reset(self, _req):
        with self.lock:
            if self.closed:
                return TriggerResponse(False, "closed")
            now = self.clock_ns if self.clock_ns is not None else 0
            evs = self.queue.reset(self.queue.epoch + 1, now)
            self.emit(evs)
            return TriggerResponse(True, json.dumps({"epoch": self.queue.epoch, "dropped": sum(1 for e in evs if e["type"] == "drop")}))

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.emit(self.queue.shutdown(self.clock_ns))
            self.closed = True
            self.emit([{"type": "node_exit", "epoch": self.queue.epoch, "queue_len": 0, "counts": self.counts, "failed": self.failed}])
            self.events_file.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--delay-ms", required=True, help="fixed delay in simulated milliseconds; only the frozen values")
    ap.add_argument("--config", default=os.path.join(ROOT, "config", "experiments", "exp2", "fixed_delay.yaml"))
    ap.add_argument("--events-file", required=True)
    ap.add_argument("--in-topic", default=None)
    ap.add_argument("--out-topic", default=None)
    ap.add_argument("--expected-connections", type=int, default=None,
                    help="downstream subscribers to wait for before 'ready' (default: frozen config, controller + recorder); engineering tests only")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    d = cfg["delay"]
    try:
        tau = float(a.delay_ms)
    except ValueError:
        print("REFUSED: delay-ms %r is not a number" % a.delay_ms)
        sys.exit(3)
    if not (tau == tau and tau in [float(x) for x in d["allowed_tau_ms"]]):   # NaN never equals anything
        print("REFUSED: delay %s ms is not one of the frozen values %s" % (a.delay_ms, d["allowed_tau_ms"]))
        sys.exit(3)
    a.delay_ms = int(tau)
    a.in_topic = a.in_topic or d["topics"]["command_in"]
    a.out_topic = a.out_topic or d["topics"]["command_out"]
    if os.path.exists(a.events_file):
        print("REFUSED: events file exists: %s" % a.events_file)
        sys.exit(3)
    os.makedirs(os.path.dirname(os.path.abspath(a.events_file)), exist_ok=True)

    rospy.init_node("task2_delay_node")
    if not rospy.get_param("/use_sim_time", False):
        print("REFUSED: /use_sim_time is not true; the delay must run on simulation time")
        sys.exit(4)
    limits = F.urdf_joint_limits(rospy.get_param("/robot_description"), cfg["robot"]["joints"]) if rospy.has_param("/robot_description") else None
    if limits is None:
        # engineering tests without a robot: URDF limits are supplied through a parameter instead
        limits = rospy.get_param("/task2/test_limits")
    p = Proxy(a, cfg, limits)

    def stop(*_):
        rospy.signal_shutdown("signal")
    signal.signal(signal.SIGTERM, stop)
    rospy.on_shutdown(p.close)
    rospy.Subscriber("/clock", Clock, p.on_clock, queue_size=100000)
    rospy.Subscriber(a.in_topic, JointTrajectory, p.on_command, queue_size=1000)
    rospy.Service(d["topics"]["reset_service"], Trigger, p.on_reset)

    # ready: first /clock seen and the downstream/event topics are connected (controller + recorder)
    w0 = time.time()
    while not rospy.is_shutdown():
        if p.clock_ns is not None and p.pub_out.get_num_connections() >= p.expected_conn and p.pub_events.get_num_connections() >= 1:
            break
        if time.time() - w0 > 60:
            print("SETUP FAILED: no /clock or downstream connections within 60 s (clock=%s out_conn=%d events_conn=%d)" %
                  (p.clock_ns, p.pub_out.get_num_connections(), p.pub_events.get_num_connections()))
            rospy.signal_shutdown("setup failed")
            sys.exit(4)
        time.sleep(0.05)
    with p.lock:
        p.emit([{"type": "ready", "epoch": p.queue.epoch, "queue_len": 0, "delay_ns": p.queue.delay_ns, "capacity": p.queue.capacity,
                 "out_connections": p.pub_out.get_num_connections(), "in_topic": a.in_topic, "out_topic": a.out_topic}])
    rospy.set_param("/task2/delay_ready", True)
    print("task2_delay_node ready: run=%s delay=%d ms in=%s out=%s" % (a.run_id, a.delay_ms, a.in_topic, a.out_topic), flush=True)
    rospy.spin()
    p.close()
    sys.exit(2 if p.failed else 0)


if __name__ == "__main__":
    main()
