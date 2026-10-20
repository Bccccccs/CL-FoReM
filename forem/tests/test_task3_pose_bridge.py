"""task3.2 unit tests: pose bridge acceptance logic and TF authority verdict (pure python, no ROS)."""
import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "forem_husky", "scripts"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from pose_gate import PoseGate  # noqa: E402
from task3_lib import tf_authority, wrap, yaw_of  # noqa: E402

Q = (0.0, 0.0, 0.0, 1.0)
P = (1.0, 2.0, 0.0)
S = 1_000_000_000


class PoseGateTest(unittest.TestCase):
    def gate(self, clock_s=100):
        g = PoseGate()
        g.observe_clock(clock_s * S)           # the independent simulation clock (/clock); samples are checked against it
        return g

    def test_good_sample_accepted(self):
        g = self.gate()
        self.assertEqual(g.check("world", "base_footprint", 5 * S, P, Q), ("accept", False))

    def test_wrong_frame_rejected(self):
        g = self.gate()
        self.assertEqual(g.check("base_link", "base_footprint", 5 * S, P, Q), ("reject", "frame"))
        self.assertEqual(g.check("world", "other_child", 5 * S, P, Q), ("reject", "child"))
        self.assertEqual(g.counts["accepted"], 0)

    def test_nonfinite_and_bad_quaternion_rejected(self):
        g = self.gate()
        self.assertEqual(g.check("world", "", 5 * S, (float("nan"), 0, 0), Q), ("reject", "nonfinite"))
        self.assertEqual(g.check("world", "", 5 * S, (0, float("inf"), 0), Q), ("reject", "nonfinite"))
        self.assertEqual(g.check("world", "", 5 * S, P, (0.0, 0.0, 0.0, 0.0)), ("reject", "quat"))
        self.assertEqual(g.check("world", "", 5 * S, P, (0.0, 0.0, 0.0, 2.0)), ("reject", "quat"))
        self.assertEqual(g.check("world", "", 0, P, Q), ("reject", "stamp_zero"))

    def test_backdated_and_duplicate_rejected(self):
        g = self.gate()
        g.check("world", "", 10 * S, P, Q)
        # a small backwards step is a backdated sample: rejected, last stamp unchanged
        self.assertEqual(g.check("world", "", 10 * S - 100_000_000, P, Q), ("reject", "backdated"))
        self.assertEqual(g.last_stamp_ns, 10 * S)
        # equal stamp is a duplicate, not republished
        self.assertEqual(g.check("world", "", 10 * S, P, Q), ("reject", "duplicate"))
        self.assertEqual(g.check("world", "", 10 * S + 20_000_000, P, Q), ("accept", False))
        self.assertEqual(g.epoch, 0)

    def test_no_clock_means_no_acceptance(self):
        g = PoseGate()
        self.assertEqual(g.check("world", "", 5 * S, P, Q), ("reject", "no_clock"))
        self.assertEqual(g.counts["accepted"], 0)

    def test_late_sample_without_reset_is_rejected_not_an_epoch(self):
        # T3-A02 counterexample 1: no reset, the simulation clock never goes back; a sample stamped 10 -> 8 s arrives late
        g = self.gate(clock_s=10)
        self.assertEqual(g.check("world", "", 10 * S, P, Q), ("accept", False))
        g.observe_clock(10 * S + 100_000_000)
        self.assertEqual(g.check("world", "", 8 * S, P, Q), ("reject", "backdated"))
        self.assertEqual((g.epoch, g.halted, g.last_stamp_ns), (0, False, 10 * S))
        # the stream continues normally afterwards
        self.assertEqual(g.check("world", "", 10 * S + 20_000_000, P, Q), ("accept", False))
        self.assertEqual((g.epoch, g.counts["accepted"], g.counts["rejected_backdated"]), (0, 2, 1))
        # even a >1 s jump back of the SAMPLE stamp alone is not a reset
        self.assertEqual(g.check("world", "", S // 10, P, Q), ("reject", "backdated"))
        self.assertEqual((g.epoch, g.halted), (0, False))

    def test_real_reset_halts_and_old_epoch_samples_are_never_published(self):
        # T3-A02 counterexample 2: 10 -> 0.1 -> 10.02 (old-epoch message still queued) -> 0.12, with a real /clock rewind
        g = self.gate(clock_s=10)
        self.assertEqual(g.check("world", "", 10 * S, P, Q), ("accept", False))
        self.assertEqual(g.observe_clock(S // 10), "reset")                  # the independent clock confirms the reset
        self.assertEqual((g.epoch, g.halted), (1, True))
        self.assertIn("reset", g.halt_reason)
        for stamp in (S // 10, 10 * S + 20_000_000, 120_000_000, 11 * S):    # new, OLD, new, future
            self.assertEqual(g.check("world", "", stamp, P, Q), ("reject", "halted"), stamp)
        self.assertEqual(g.epoch, 1)                                          # never wrongly incremented by the samples
        self.assertEqual((g.counts["accepted"], g.counts["rejected_halted"]), (1, 4))
        self.assertEqual(g.last_stamp_ns, 10 * S)                             # state of the old epoch is not mixed with the new one
        g.observe_clock(S // 10 + 1_000_000)                                  # the clock keeps running: stays halted, no new epoch
        self.assertEqual((g.epoch, g.halted), (1, True))

    def test_sample_ahead_of_clock_is_rejected(self):
        g = self.gate(clock_s=5)
        self.assertEqual(g.check("world", "", 10 * S + 20_000_000, P, Q), ("reject", "future"))
        self.assertEqual(g.check("world", "", 5 * S + 500_000_000, P, Q), ("accept", False))     # within the 1 s transport tolerance
        self.assertEqual(g.counts["rejected_future"], 1)

    def test_clock_stall_small_rewind_and_forward_jump_are_not_resets(self):
        g = self.gate(clock_s=10)
        self.assertEqual(g.observe_clock(10 * S), "ok")                       # stalled
        self.assertEqual(g.observe_clock(10 * S - 500_000_000), "ok")         # small rewind (<= 1 s): ignored, clock stays at its maximum
        self.assertEqual(g.clock_ns, 10 * S)
        self.assertEqual(g.observe_clock(500 * S), "ok")                      # jump forward
        self.assertEqual((g.epoch, g.halted), (0, False))

    def test_each_real_reset_event_counts_one_epoch(self):
        g = self.gate(clock_s=50)
        self.assertEqual(g.observe_clock(S), "reset")
        self.assertEqual(g.observe_clock(2 * S), "ok")
        self.assertEqual(g.observe_clock(100 * S), "ok")
        self.assertEqual(g.observe_clock(S), "reset")
        self.assertEqual(g.epoch, 2)

    def test_counters_consistent(self):
        g = self.gate()
        for i in range(5):
            g.check("world", "", (i + 1) * S, P, Q)
        g.check("map2", "", 9 * S, P, Q)
        self.assertEqual(g.counts["received"], 6)
        self.assertEqual(g.counts["accepted"], 5)
        self.assertEqual(g.counts["rejected_frame"], 1)


class TfAuthorityTest(unittest.TestCase):
    def test_single_authority_ok(self):
        r = tf_authority({"/pose_bridge": {("odom", "base_footprint")}, "/robot_state_publisher": {("base_link", "x")}})
        self.assertTrue(r["unique"] and r["allowed"])

    def test_duplicate_pose_authority_rejected(self):
        # the reference chain: gdt_tf AND a second node publishing odom->base_footprint (e.g. EKF or gazebo)
        r = tf_authority({"/pose_bridge": {("odom", "base_footprint")}, "/gdt_tf": {("odom", "base_footprint")}})
        self.assertFalse(r["unique"])
        self.assertFalse(r["allowed"])
        self.assertEqual(r["odom_base_authors"], ["/gdt_tf", "/pose_bridge"])

    def test_missing_authority_rejected(self):
        self.assertFalse(tf_authority({"/robot_state_publisher": {("base_link", "x")}})["unique"])

    def test_foreign_publisher_rejected(self):
        self.assertFalse(tf_authority({"/pose_bridge": {("odom", "base_footprint")}, "/gazebo": {("a", "b")}})["allowed"])


class MathTest(unittest.TestCase):
    def test_yaw_and_wrap(self):
        s = math.sin(math.pi / 4)
        self.assertAlmostEqual(yaw_of((0, 0, s, math.cos(math.pi / 4))), math.pi / 2)
        self.assertAlmostEqual(wrap(3 * math.pi), -math.pi if wrap(3 * math.pi) < 0 else math.pi, places=6)
        self.assertAlmostEqual(abs(wrap(2 * math.pi + 0.1)), 0.1, places=9)


if __name__ == "__main__":
    unittest.main()
