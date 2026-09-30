"""Regression tests for scripts/task0_validation.py (task0.7).

These use CONSTRUCTED data. They are not evidence about the simulator; they show that the
acceptance logic can fail. Each bad case is also fed to a copy of the LEGACY (task0.5/0.6)
check logic to document which cases the old check_feedback.py wrongly accepted.

Run (host or container, no ROS needed):  python3 -m unittest discover -s forem/tests -v
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import task0_validation as V  # noqa: E402

J = V.JOINTS
LIMITS = {j: {"lower": -6.283185307, "upper": 6.283185307, "velocity": 3.141592654, "effort": 150.0} for j in J}
Q0 = [0.0, -1.5708, 0.0, -1.5708, 0.0, 0.0]
OFF = [0.3, 0.2, -0.3, 0.2, 0.3, 0.4]
QT = [a + b for a, b in zip(Q0, OFF)]
T_MOVE = 3.0
WS, DUR = 10.0, 8.0
POLICY = {"window_start": WS, "window_end": WS + DUR}


def smooth(s):  # cubic, zero end velocities
    s = min(max(s, 0.0), 1.0)
    return 3 * s * s - 2 * s ** 3


def desired(t, move):
    if not move:
        return list(Q0)
    f = smooth((t - WS) / T_MOVE)
    return [a + f * b for a, b in zip(Q0, OFF)]


def make(move=True, hz=125.0, actual_fn=None, t_end=WS + DUR):
    """Valid records; actual = desired + 1e-5 rad by default."""
    js, st = [], []
    n = int(round((t_end - WS) * hz))
    for k in range(n + 1):
        t = WS + k / hz
        d = desired(t, move)
        a = actual_fn(t, d) if actual_fn else [x + 1e-5 for x in d]
        js.append([t] + a + [0.0] * 6 + [1.0] * 6)
        st.append([t] + d + a + [x - y for x, y in zip(d, a)] + [0.0] * 6 + [0.0] * 6)
    clock = [WS + k / 2000.0 for k in range(int((t_end - WS) * 2000) + 1)]
    cmd = {"sim_time_sent": WS, "q_start": Q0, "q_target": QT, "duration_s": T_MOVE} if move else None
    return js, st, clock, cmd


def evaluate(js, st, clock, cmd, policy=None):
    p = dict(POLICY)
    p.update(policy or {})
    return V.evaluate_feedback(js, st, clock, cmd, LIMITS, p)


def legacy_pass(js, st, clock, cmd, duration=DUR):
    """Copy of the task0.5/0.6 check_feedback.py pass logic (for comparison only)."""
    def inc(ts):
        return len(ts) >= 3 and all(b - a > 0 for a, b in zip(ts, ts[1:]))
    def span(ts):
        return ts[-1] - ts[0] if len(ts) > 1 else 0
    fin = all(math.isfinite(x) for r in js for x in r) and all(math.isfinite(x) for r in st for x in r)
    ok = span(clock) >= duration * 0.99 and inc([r[0] for r in js]) and inc([r[0] for r in st]) \
        and span([r[0] for r in js]) >= duration * 0.95 and fin and bool(js)
    if cmd is not None:
        off = [t - s for t, s in zip(cmd["q_target"], cmd["q_start"])]
        pp = [max(r[1 + i] for r in js) - min(r[1 + i] for r in js) for i in range(6)]
        ok = ok and all(pp[i] > 0.5 * abs(off[i]) for i in range(6) if abs(off[i]) > 1e-6)
    return ok


class ValidRecords(unittest.TestCase):
    def test_valid_move_passes(self):
        c, m = evaluate(*make(move=True))
        self.assertTrue(V.is_pass(c), [k for k, v in c.items() if not v])
        self.assertLess(abs(m["final_error_actual_minus_target_rad"][J[0]]), 1e-4)

    def test_valid_hold_passes(self):
        c, _ = evaluate(*make(move=False))
        self.assertTrue(V.is_pass(c), [k for k, v in c.items() if not v])

    def test_final_error_sign_is_actual_minus_target(self):
        js, st, ck, cmd = make(move=True, actual_fn=lambda t, d: [x - 0.01 for x in d])  # actual below target
        _, m = evaluate(js, st, ck, cmd)
        self.assertLess(m["final_error_actual_minus_target_rad"][J[0]], 0)  # actual - target < 0


class BadRecordsAreRejected(unittest.TestCase):
    def case(self, name, js, st, clock, cmd, expect_check, policy=None):
        c, _ = evaluate(js, st, clock, cmd, policy)
        self.assertFalse(V.is_pass(c), name + ": new logic must fail")
        self.assertFalse(c[expect_check], name + ": expected check %s to fail; failed=%s" % (expect_check, [k for k, v in c.items() if not v]))

    def test_controller_stream_stops_after_three_samples(self):
        js, st, ck, cmd = make(move=True)
        st = st[:3]
        self.case("early stop", js, st, ck, cmd, "controller_state_covers_window")
        self.assertTrue(legacy_pass(js, st, ck, cmd), "legacy logic accepted a 3-sample controller stream")

    def test_controller_stream_gap_in_middle(self):
        js, st, ck, cmd = make(move=True)
        st = [r for r in st if not (WS + 3.0 < r[0] < WS + 3.6)]
        self.case("mid gap", js, st, ck, cmd, "controller_state_max_gap_ok")
        self.assertTrue(legacy_pass(js, st, ck, cmd), "legacy logic accepted a 0.6 s gap")

    def test_joint_stream_gap(self):
        js, st, ck, cmd = make(move=True)
        js = [r for r in js if not (WS + 4.0 < r[0] < WS + 4.5)]
        self.case("js gap", js, st, ck, cmd, "joint_states_max_gap_ok")

    def test_reverse_motion(self):
        # joints wander to the wrong side by the same amount: peak-to-peak is large but direction is wrong
        fn = lambda t, d: [Q0[i] - (d[i] - Q0[i]) for i in range(6)]
        js, st, ck, cmd = make(move=True, actual_fn=fn)
        self.case("reverse", js, st, ck, cmd, "motion_direction_and_extent")
        self.assertTrue(legacy_pass(js, st, ck, cmd), "legacy peak-to-peak logic accepted reverse motion")

    def test_sustained_finite_offset_from_reference(self):
        js, st, ck, cmd = make(move=True, actual_fn=lambda t, d: [x + 0.25 for x in d])
        self.case("offset", js, st, ck, cmd, "tracking_within_trajectory_tolerance")
        self.assertTrue(legacy_pass(js, st, ck, cmd), "legacy logic accepted a 0.25 rad sustained offset")

    def test_final_far_from_target(self):
        # stops halfway
        fn = lambda t, d: [Q0[i] + 0.5 * (d[i] - Q0[i]) + 0.0 for i in range(6)]
        js, st, ck, cmd = make(move=True, actual_fn=fn)
        c, _ = evaluate(js, st, ck, cmd)
        self.assertFalse(V.is_pass(c))

    def test_position_out_of_limit(self):
        js, st, ck, cmd = make(move=False)
        js[10][1] = 7.0
        self.case("limit", js, st, ck, cmd, "limits_respected")

    def test_velocity_or_effort_over_limit(self):
        js, st, ck, cmd = make(move=False)
        js[10][7] = 10.0  # rad/s
        self.case("vel limit", js, st, ck, cmd, "limits_respected")
        js, st, ck, cmd = make(move=False)
        js[10][13] = 500.0  # N*m
        self.case("effort limit", js, st, ck, cmd, "limits_respected")

    def test_non_finite_values(self):
        js, st, ck, cmd = make(move=False)
        js[20][3] = float("nan")
        self.case("nan", js, st, ck, cmd, "all_values_finite")
        js, st, ck, cmd = make(move=False)
        st[20][5] = float("inf")
        self.case("inf", js, st, ck, cmd, "all_values_finite")

    def test_wrong_array_length(self):
        js, st, ck, cmd = make(move=False)
        js[5] = js[5][:-1]
        self.case("row length", js, st, ck, cmd, "joint_states_rows_well_formed")

    def test_no_data(self):
        self.case("empty", [], [], [], None, "joint_states_has_samples")

    def test_window_too_short_for_move(self):
        js, st, ck, cmd = make(move=True, t_end=WS + 3.5)
        self.case("short window", js, st, ck, cmd, "window_long_enough_for_command", {"window_end": WS + 3.5})

    def test_time_not_increasing(self):
        js, st, ck, cmd = make(move=False)
        js[30][0] = js[29][0]
        self.case("dup time", js, st, ck, cmd, "joint_states_time_increasing_wrapper" if False else "joint_states_time_strictly_increasing")

    def test_hold_range_too_large(self):
        fn = lambda t, d: [x + (0.2 if t > WS + 4 else 0.0) for x in d]
        js, st, ck, cmd = make(move=False, actual_fn=fn)
        c, _ = evaluate(js, st, ck, cmd)
        self.assertFalse(V.is_pass(c))
        self.assertFalse(c["hold_range_ok"])

    def test_clock_not_reaching_window(self):
        js, st, ck, cmd = make(move=False)
        ck = ck[:200]
        self.case("clock short", js, st, ck, cmd, "clock_covers_window")


class PoseCheck(unittest.TestCase):
    def test_service_failure_is_failure(self):
        c, m = V.model_pose_checks(None, None, False, False, 1e-3)
        self.assertFalse(c["model_state_service_ok"])
        self.assertFalse(c["base_fixed_pose_change_ok"])

    def test_pose_moved_fails_and_still_passes(self):
        a = [0, 0, 0, 0, 0, 0, 1.0]
        c, _ = V.model_pose_checks(a, [0, 0, 0.01, 0, 0, 0, 1.0], True, True, 1e-3)
        self.assertFalse(c["base_fixed_pose_change_ok"])
        c, _ = V.model_pose_checks(a, [0, 0, 1e-6, 0, 0, 0, 1.0], True, True, 1e-3)
        self.assertTrue(all(c.values()))


if __name__ == "__main__":
    unittest.main()
