"""Task2.2 tests: pure delay queue (no ROS, no sleep, no wall clock), supported-message validation, freeze pre-registration checks.
Runs on the host (stdlib + PyYAML) and in forem-dev:  python3 -W ignore -m unittest discover -s tests
"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import task2_delay_queue as Q  # noqa: E402

MS = 1_000_000
JOINTS = ["ur5_shoulder_pan_joint", "ur5_shoulder_lift_joint", "ur5_elbow_joint", "ur5_wrist_1_joint", "ur5_wrist_2_joint", "ur5_wrist_3_joint"]
LIMITS = {j: {"lower": -6.28, "upper": 6.28, "velocity": 3.14} for j in JOINTS}


def cmd(dq=(0.3, 0.2, -0.3, 0.2, 0.3, 0.4), T=3.0, q0=(0.0, -1.5708, 0.0, -1.5708, 0.0, 0.0)):
    q1 = [a + b for a, b in zip(q0, dq)]
    z = [0.0] * 6
    return {"schema": "task1-command/1", "header": {"stamp": [0, 0], "frame_id": ""}, "joint_names": list(JOINTS),
            "points": [{"positions": list(q0), "velocities": z, "accelerations": [], "effort": [], "time_from_start": [0, 0]},
                       {"positions": q1, "velocities": z, "accelerations": [], "effort": [], "time_from_start": [int(T), int(round((T - int(T)) * 1e9))]}]}


class TestQueueTiming(unittest.TestCase):
    def test_delay_80ms_boundaries(self):
        q = Q.DelayQueue(80 * MS)
        q.enqueue(0, 0, 1000 * MS, "m")
        it, _ = q.advance(1000 * MS + 79_500_000)       # 79.5 ms after receipt: nothing
        self.assertEqual(it, [])
        it, ev = q.advance(1000 * MS + 80 * MS)          # exactly the due time: delivered
        self.assertEqual([i.seq for i in it], [0])
        self.assertEqual(ev[0]["type"], "due")
        self.assertEqual(ev[0]["t_due_ns"], 1080 * MS)

    def test_zero_delay_same_instant(self):
        q = Q.DelayQueue(0)
        q.enqueue(0, 0, 5 * MS, "m")
        it, _ = q.advance(5 * MS)
        self.assertEqual(len(it), 1)

    def test_no_redelivery(self):
        q = Q.DelayQueue(10 * MS)
        q.enqueue(0, 0, 0, "m")
        self.assertEqual(len(q.advance(10 * MS)[0]), 1)
        self.assertEqual(q.advance(10 * MS)[0], [])
        self.assertEqual(q.advance(500 * MS)[0], [])
        self.assertEqual(q.delivered, 1)

    def test_fifo_same_due_and_order(self):
        q = Q.DelayQueue(20 * MS)
        for s in range(5):
            q.enqueue(0, s, 100 * MS, "m%d" % s)           # identical due time
        it, _ = q.advance(120 * MS)
        self.assertEqual([i.seq for i in it], [0, 1, 2, 3, 4])

    def test_staggered_release(self):
        q = Q.DelayQueue(30 * MS)
        q.enqueue(0, 0, 0, "a")
        q.enqueue(0, 1, 10 * MS, "b")
        self.assertEqual([i.seq for i in q.advance(30 * MS)[0]], [0])
        self.assertEqual([i.seq for i in q.advance(39 * MS)[0]], [])
        self.assertEqual([i.seq for i in q.advance(40 * MS)[0]], [1])

    def test_no_wall_clock_dependence(self):
        # the queue exposes no clock and no sleep; the due decision depends only on the integer arguments
        import inspect
        src = inspect.getsource(Q)
        for banned in ("import time", "time.sleep", "time.time", "datetime", "rospy"):
            self.assertNotIn(banned, src)


class TestQueueMisuse(unittest.TestCase):
    def test_bad_construction(self):
        for kw in ({"delay_ns": -1}, {"delay_ns": 1.5}, {"delay_ns": True}, {"delay_ns": float("nan")}, {"delay_ns": 2 ** 63},
                   {"delay_ns": 0, "capacity": 0}, {"delay_ns": 0, "capacity": -3}, {"delay_ns": 0, "epoch": -1}, {"delay_ns": None}):
            with self.assertRaises(Q.QueueError, msg=str(kw)):
                Q.DelayQueue(**kw)

    def test_bad_times_rejected(self):
        q = Q.DelayQueue(0)
        for bad in (-1, 1.0, float("inf"), float("nan"), True, None, "1", 2 ** 63):
            with self.assertRaises(Q.QueueError, msg=repr(bad)):
                q.enqueue(0, 0, bad, "m")
            with self.assertRaises(Q.QueueError, msg=repr(bad)):
                q.advance(bad)
        self.assertEqual(len(q), 0)

    def test_overflow_is_an_error_not_a_drop(self):
        q = Q.DelayQueue(10 * MS, capacity=3)
        for s in range(3):
            q.enqueue(0, s, s, "m")
        with self.assertRaises(Q.QueueError) as cm:
            q.enqueue(0, 3, 3, "m")
        self.assertEqual(cm.exception.event["type"], "reject")
        self.assertIn("full", cm.exception.event["reason"])
        self.assertEqual(len(q), 3)                        # nothing silently dropped or overwritten
        self.assertEqual([i.seq for i in q.advance(20 * MS)[0]], [0, 1, 2])

    def test_duplicate_and_decreasing_seq(self):
        q = Q.DelayQueue(10 * MS)
        q.enqueue(0, 5, 0, "m")
        for s in (5, 4, 0):
            with self.assertRaises(Q.QueueError):
                q.enqueue(0, s, 1, "m")
        self.assertEqual(len(q), 1)

    def test_unknown_epoch_rejected(self):
        q = Q.DelayQueue(10 * MS, epoch=2)
        with self.assertRaises(Q.QueueError) as cm:
            q.enqueue(1, 0, 0, "m")
        self.assertIn("unknown epoch", cm.exception.event["reason"])
        with self.assertRaises(Q.QueueError):
            q.enqueue(3, 0, 0, "m")


class TestReset(unittest.TestCase):
    def test_reset_discards_pending_and_reports(self):
        q = Q.DelayQueue(100 * MS)
        q.enqueue(0, 0, 0, "old0", payload_hash="h0")
        q.enqueue(0, 1, 10 * MS, "old1", payload_hash="h1")
        ev = q.reset(1, 20 * MS)
        drops = [e for e in ev if e["type"] == "drop"]
        self.assertEqual([(e["seq"], e["reason"], e["payload_hash"]) for e in drops], [(0, "reset", "h0"), (1, "reset", "h1")])
        self.assertEqual(ev[-1]["type"], "reset")
        self.assertEqual(len(q), 0)
        self.assertEqual(q.epoch, 1)
        # the old messages never come out, however far the clock advances
        self.assertEqual(q.advance(10_000 * MS)[0], [])
        # the old epoch is dead; the new one works from seq 0 again
        with self.assertRaises(Q.QueueError):
            q.enqueue(0, 2, 10_001 * MS, "late-old")
        q.enqueue(1, 0, 10_001 * MS, "new")
        self.assertEqual([i.payload for i in q.advance(10_101 * MS)[0]], ["new"])

    def test_reset_at_same_sim_time_needs_explicit_call(self):
        q = Q.DelayQueue(50 * MS)
        q.enqueue(0, 0, 100 * MS, "a")
        self.assertEqual(q.advance(100 * MS)[0], [])      # same time again is not a backward step
        self.assertEqual(len(q), 1)
        q.reset(1, 100 * MS)                               # explicit reset at the identical sim time
        self.assertEqual(len(q), 0)

    def test_reset_epoch_must_increase(self):
        q = Q.DelayQueue(0, epoch=3)
        for e in (3, 2, 0):
            with self.assertRaises(Q.QueueError):
                q.reset(e, 0)

    def test_clock_backward_clears_and_changes_epoch(self):
        q = Q.DelayQueue(100 * MS)
        q.enqueue(0, 0, 500 * MS, "old")
        q.advance(520 * MS)
        items, ev = q.advance(10 * MS)                     # sim reset: clock jumps back
        self.assertEqual(items, [])
        self.assertEqual([e["type"] for e in ev], ["drop", "clock_backward"])
        self.assertEqual(ev[0]["reason"], "clock_backward")
        self.assertEqual(q.epoch, 1)
        self.assertEqual(q.clock_backward_count, 1)
        self.assertEqual(q.advance(10_000 * MS)[0], [])    # nothing from the old world is ever delivered
        with self.assertRaises(Q.QueueError):
            q.enqueue(0, 1, 11 * MS, "from-old-epoch")

    def test_enqueue_with_older_time_is_backward_too(self):
        q = Q.DelayQueue(100 * MS)
        q.enqueue(0, 0, 500 * MS, "old")
        with self.assertRaises(Q.QueueError):              # epoch 0 is stale after the backward step the older receive time implies
            q.enqueue(0, 1, 10 * MS, "x")
        self.assertEqual(q.epoch, 1)
        self.assertEqual(len(q), 0)

    def test_shutdown_drops_without_publishing(self):
        q = Q.DelayQueue(10 * MS)
        q.enqueue(0, 0, 0, "m")
        ev = q.shutdown(1)
        self.assertEqual([e["type"] for e in ev], ["drop", "shutdown"])
        self.assertEqual(ev[0]["reason"], "shutdown")
        self.assertEqual(q.advance(10 * MS)[0], [])


class TestValidateCommand(unittest.TestCase):
    def ok(self, rec):
        return Q.validate_command(rec, JOINTS, LIMITS, 0.2)

    def test_frozen_commands_accepted(self):
        self.assertEqual(self.ok(cmd()), [])
        self.assertEqual(self.ok(cmd(T=6.0)), [])
        self.assertEqual(self.ok(cmd(dq=(-0.3, -0.2, 0.3, -0.2, -0.3, -0.4))), [])

    def test_unsupported_rejected_and_input_untouched(self):
        base = cmd()
        mutations = {
            "nonzero stamp": lambda r: r["header"].__setitem__("stamp", [5, 1]),
            "frame id": lambda r: r["header"].__setitem__("frame_id", "world"),
            "joint order": lambda r: r.__setitem__("joint_names", list(reversed(JOINTS))),
            "one point": lambda r: r["points"].pop(),
            "three points": lambda r: r["points"].append(copy.deepcopy(r["points"][1])),
            "velocity nonzero": lambda r: r["points"][1]["velocities"].__setitem__(0, 0.1),
            "acceleration present": lambda r: r["points"][1].__setitem__("accelerations", [0.0] * 6),
            "effort present": lambda r: r["points"][0].__setitem__("effort", [0.0] * 6),
            "first point time": lambda r: r["points"][0].__setitem__("time_from_start", [0, 1]),
            "zero duration": lambda r: r["points"][1].__setitem__("time_from_start", [0, 0]),
            "negative time": lambda r: r["points"][1].__setitem__("time_from_start", [-1, 0]),
            "nan position": lambda r: r["points"][1]["positions"].__setitem__(2, float("nan")),
            "inf position": lambda r: r["points"][0]["positions"].__setitem__(1, float("inf")),
            "outside limit": lambda r: r["points"][1]["positions"].__setitem__(0, 7.0),
            "too fast": lambda r: r["points"][1].__setitem__("time_from_start", [0, 100_000_000]),
            "short positions": lambda r: r["points"][1]["positions"].pop(),
            "missing key": lambda r: r.pop("points"),
        }
        for name, mut in mutations.items():
            rec = copy.deepcopy(base)
            mut(rec)
            snapshot = copy.deepcopy(rec)
            self.assertTrue(self.ok(rec), name)
            self.assertEqual(rec, snapshot, name + ": the record must not be modified")

    def test_hash_is_canonical_but_not_an_identity(self):
        a, b = cmd(), cmd()
        self.assertEqual(Q.payload_hash(a), Q.payload_hash(b))
        b["points"][1]["positions"][0] += 1e-12
        self.assertNotEqual(Q.payload_hash(a), Q.payload_hash(b))
        # two identical payloads are still two entries: identity is (epoch, seq)
        q = Q.DelayQueue(0)
        q.enqueue(0, 0, 0, a, payload_hash=Q.payload_hash(a))
        q.enqueue(0, 1, 0, a, payload_hash=Q.payload_hash(a))
        self.assertEqual([i.seq for i in q.advance(0)[0]], [0, 1])


class TestFreezePreregistration(unittest.TestCase):
    def setUp(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML missing")
        import freeze_task2 as F
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        self.F = F
        self.cfg = yaml.safe_load(open(os.path.join(root, F.CONFIG)))
        self.t1 = yaml.safe_load(open(os.path.join(root, F.TASK1_YAML)))

    def test_shipped_config_passes(self):
        bad, n = self.F.preregistration_checks(self.cfg, self.t1)
        self.assertEqual(bad, [])
        self.assertEqual(n, 48)

    def test_copy_drift_and_matrix_errors_detected(self):
        def mutate(f):
            c = copy.deepcopy(self.cfg)
            f(c)
            return self.F.preregistration_checks(c, self.t1)[0]
        self.assertTrue(mutate(lambda c: c["quality"].__setitem__("grid_s", 0.01)))
        self.assertTrue(mutate(lambda c: c["timing"].__setitem__("pre_hold_s", 4.0)))
        self.assertTrue(mutate(lambda c: c["cases"]["M3"].__setitem__("T", 4.0)))
        self.assertTrue(mutate(lambda c: c["delay"]["conditions"]["D160"].__setitem__("tau_ms", 320)))
        self.assertTrue(mutate(lambda c: c["delay"]["conditions"]["B"].__setitem__("tau_ms", 80)))
        self.assertTrue(mutate(lambda c: c["matrix"]["condition_order_by_round"].__setitem__(2, ["B", "B", "Z", "D80"])))
        self.assertTrue(mutate(lambda c: c["matrix"].__setitem__("rounds", 2)))
        self.assertTrue(mutate(lambda c: c["cases"].__setitem__("P+", self.t1["cases"]["P+"])))


if __name__ == "__main__":
    unittest.main()
