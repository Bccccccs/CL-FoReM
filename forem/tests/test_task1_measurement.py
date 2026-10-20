"""Task1 measurement-chain tests (numpy + PyYAML; no ROS, no simulator).

Covers the five failure-input classes named in doc/tasks/task1/PROCEDURE.md:
  1 actual backfilled from the target/reference      -> audit + gates must flag it
  2 clock backward / gap / duplicate / reorder       -> quality gates must reject, never fill
  3 zero velocity / correlation peak on the boundary -> lag NOT identifiable (never 0 ms)
  4 FK frame and quaternion sign                     -> known analytic poses, q and -q give the same orientation
  5 (process/exit-code cases live in scripts/regress_task1_entry.py, which needs the live container)
plus exact RMSE/peak on fixed-bias fixtures and by-name joint mapping.

Run (container has numpy): bash forem/docker/run.sh exec python3 -m unittest discover -s tests -p 'test_task1*.py' -v
"""
import copy
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace

try:
    import numpy as np
    import yaml
except ImportError as e:  # the host python has no numpy: these tests run in forem-dev
    raise unittest.SkipTest("numpy/PyYAML not available: %s (run inside forem-dev)" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import analyze_task1 as A  # noqa: E402
import task1_lib as L  # noqa: E402

def _read(path):
    with open(path) as f:
        return f.read()


CFG = yaml.safe_load(_read(os.path.join(HERE, "..", "config", "experiments", "task1", "baseline.yaml")))
URDF = _read(os.path.join(HERE, "fixtures", "ur5_fixed.urdf"))
J = L.JOINTS

PLANAR = """<robot name="p"><link name="b"/><link name="l1"/><link name="l2"/><link name="tip"/>
<joint name="j1" type="revolute"><parent link="b"/><child link="l1"/><origin xyz="0 0 0" rpy="0 0 0"/><axis xyz="0 0 1"/><limit lower="-7" upper="7" velocity="1" effort="1"/></joint>
<joint name="j2" type="revolute"><parent link="l1"/><child link="l2"/><origin xyz="1 0 0" rpy="0 0 0"/><axis xyz="0 0 1"/><limit lower="-7" upper="7" velocity="1" effort="1"/></joint>
<joint name="jt" type="fixed"><parent link="l2"/><child link="tip"/><origin xyz="1 0 0" rpy="0 0 0"/></joint></robot>"""



def fake_msg(points, stamp=(0, 0), frame_id="", names=None):
    """A duck-typed JointTrajectory with the attributes task1_lib.command_record reads."""
    def pt(pos, vel, acc, eff, tfs):
        return SimpleNamespace(positions=list(pos), velocities=list(vel), accelerations=list(acc), effort=list(eff),
                               time_from_start=SimpleNamespace(secs=int(tfs[0]), nsecs=int(tfs[1])))
    return SimpleNamespace(header=SimpleNamespace(stamp=SimpleNamespace(secs=stamp[0], nsecs=stamp[1]), frame_id=frame_id),
                           joint_names=list(J if names is None else names), points=[pt(*p) for p in points])


def legacy_record(rec):
    """The pre-task1.7 commands.json message layout (float seconds, header_stamp pair, no frame_id)."""
    rec = json.loads(json.dumps(rec))   # deep copy: the legacy record must not alias the source lists
    return {"header_stamp": list(rec["header"]["stamp"]), "joint_names": list(rec["joint_names"]),
            "points": [dict(p, time_from_start=p["time_from_start"][0] + p["time_from_start"][1] * 1e-9) for p in rec["points"]]}


class Stats(unittest.TestCase):
    def test_fixed_bias_exact(self):
        e = np.tile([0.001, -0.002, 0, 0, 0, 0.004], (200, 1))
        t = np.arange(200) * 0.008
        s = L.error_stats(e, t)
        self.assertTrue(np.allclose(s["rmse"], [0.001, 0.002, 0, 0, 0, 0.004]))
        self.assertTrue(np.allclose(s["max_abs"], [0.001, 0.002, 0, 0, 0, 0.004]))
        self.assertTrue(np.allclose(s["mean"], [0.001, -0.002, 0, 0, 0, 0.004]))
        self.assertTrue(np.allclose(s["final_mean"], s["mean"]))

    def test_peak_vs_rmse(self):
        e = np.zeros((100, 6)); e[50, 0] = 0.01
        s = L.error_stats(e, np.arange(100) * 0.008)
        self.assertAlmostEqual(s["max_abs"][0], 0.01)
        self.assertAlmostEqual(s["rmse"][0], 0.01 / 10.0)

    def test_map_by_name_reordered(self):
        names = [J[i] for i in (3, 0, 5, 1, 4, 2)]
        vals = [30, 0, 50, 10, 40, 20]
        self.assertEqual(L.map_by_name(names, vals), [0, 10, 20, 30, 40, 50])

    def test_map_by_name_rejects_missing_duplicate(self):
        with self.assertRaises(L.InvalidInput):
            L.map_by_name(J[:5], [0] * 5)
        with self.assertRaises(L.InvalidInput):
            L.map_by_name(J[:5] + [J[0]], [0] * 6)
        with self.assertRaises(L.InvalidInput):
            L.map_by_name(J, [0] * 5)

    def test_non_finite_rejected(self):
        with self.assertRaises(L.InvalidInput):
            L.require_finite([0.0, float("nan")], "x")


class Quality(unittest.TestCase):
    def good(self, n=400, dt=0.008, t0=0.0):
        return t0 + np.arange(n) * dt

    def q(self, t, t0=0.1, t1=3.0):
        return L.stream_quality(t, t0, t1, 0.008, 3, 0.01, 0.99)

    def test_clean_passes(self):
        self.assertTrue(self.q(self.good())["pass"])

    def test_clock_backward_rejected(self):
        t = self.good(); t[200:] -= 0.5
        r = self.q(t)
        self.assertFalse(r["pass"]); self.assertIn("backward", " ".join(r["reasons"]))

    def test_gap_rejected_not_filled(self):
        t = np.delete(self.good(), np.arange(100, 106))   # 6 missing samples = 56 ms gap
        r = self.q(t)
        self.assertFalse(r["pass"]); self.assertGreater(r["max_gap_s"], 0.024)

    def test_gap_of_three_periods_allowed(self):
        t = np.delete(self.good(), np.arange(100, 102))   # 24 ms gap exactly
        self.assertTrue(self.q(t)["pass"])

    def test_duplicates_over_limit(self):
        t = self.good(); t[1::20] = t[0::20][:len(t[1::20])]   # 5% duplicate stamps
        r = self.q(np.sort(t))
        self.assertFalse(r["pass"])

    def test_window_edge_needs_support(self):
        t = self.good(n=400)   # stream ends at 3.192; window to 3.5 has no support for the last 0.3 s
        self.assertFalse(self.q(t, 0.1, 3.5)["pass"])
        self.assertFalse(self.q(t, -0.5, 3.0)["pass"])   # nothing before t=0

    def test_non_finite_time(self):
        t = self.good(); t[10] = float("nan")
        self.assertFalse(self.q(t)["pass"])

    def test_dedupe_keeps_first(self):
        t, x = L.dedupe_sorted(np.array([0, 1, 1, 2.0]), np.array([10, 11, 99, 12]))
        self.assertEqual(list(t), [0, 1, 2]); self.assertEqual(list(x), [10, 11, 12])


class Lag(unittest.TestCase):
    def sig(self, delay, n=800):
        t = np.arange(n) * 0.004
        vd = np.where((t > 0.5) & (t < 2.5), np.sin(np.pi * (t - 0.5) / 2.0) ** 2, 0.0) * 0.2
        va = np.interp(t - delay, t, vd, left=0.0)
        return t, vd, va

    def test_known_delay_recovered(self):
        t, vd, va = self.sig(0.040)
        r = L.lag_estimate(t, vd, va, 0.3, 3.0, grid=0.008)
        self.assertTrue(r["identifiable"]); self.assertAlmostEqual(r["tau_s"], 0.040, delta=0.008)
        self.assertTrue(r["resolvable"])

    def test_zero_velocity_not_identifiable(self):
        t = np.arange(800) * 0.004
        r = L.lag_estimate(t, np.zeros_like(t), np.zeros_like(t), 0.3, 3.0)
        self.assertFalse(r["identifiable"]); self.assertIsNone(r["tau_s"])

    def test_boundary_peak_not_identifiable(self):
        t, vd, va = self.sig(0.30)   # true delay far outside the +-0.1 s search
        r = L.lag_estimate(t, vd, va, 0.3, 3.0)
        self.assertFalse(r["identifiable"]); self.assertIsNone(r["tau_s"])

    def test_sub_grid_delay_flagged_unresolvable(self):
        t, vd, va = self.sig(0.0)
        r = L.lag_estimate(t, vd, va, 0.3, 3.0, grid=0.008)
        self.assertTrue(r["identifiable"]); self.assertTrue(r["below_resolution"]); self.assertFalse(r["resolvable"])

    def test_flat_curve_not_identifiable(self):
        t = np.arange(800) * 0.004
        vd = np.full_like(t, 0.1); va = np.full_like(t, 0.1)   # constant velocity: correlation flat in tau
        r = L.lag_estimate(t, vd, va, 0.3, 3.0)
        self.assertFalse(r["identifiable"])


class Audit(unittest.TestCase):
    def setUp(self):
        t = np.linspace(0, 1, 200)
        self.des = np.outer(3 * t ** 2 - 2 * t ** 3, np.ones(6)) * 0.2
        self.act = self.des + 1e-4 * np.sin(20 * t)[:, None]

    def test_distinct_passes(self):
        self.assertTrue(L.audit_backfill(self.act, self.des, target=self.des[-1])["pass"])

    def test_actual_copied_from_desired_flagged(self):
        r = L.audit_backfill(self.des.copy(), self.des)
        self.assertFalse(r["pass"]); self.assertIn("backfilled", r["flags"][0])

    def test_actual_copied_from_target_flagged(self):
        act = np.tile(self.des[-1], (200, 1))
        self.assertFalse(L.audit_backfill(act, self.des, target=self.des[-1])["pass"])

    def test_joint_states_copied_from_desired_flagged(self):
        self.assertFalse(L.audit_backfill(self.act, self.des, js_pos=self.des.copy())["pass"])

    def test_difference_is_preserved(self):
        r = L.audit_backfill(self.act, self.des)
        self.assertAlmostEqual(r["max_abs_act_minus_des"], float(np.max(np.abs(self.act - self.des))))


class Kinematics(unittest.TestCase):
    def test_planar_analytic(self):
        ch = L.parse_chain(PLANAR, "b", "tip")
        for a, b in [(0.0, 0.0), (0.3, -0.5), (1.2, 0.7), (-2.0, 1.0)]:
            T = L.fk(ch, {"j1": a, "j2": b})
            # joint 2 sits 1 m along link 1, the tip a further 1 m along link 2
            exp = [math.cos(a) + math.cos(a + b), math.sin(a) + math.sin(a + b)]
            self.assertAlmostEqual(T[0, 3], exp[0], places=12); self.assertAlmostEqual(T[1, 3], exp[1], places=12)
            self.assertAlmostEqual(math.atan2(T[1, 0], T[0, 0]), math.atan2(math.sin(a + b), math.cos(a + b)), places=12)

    def test_batch_equals_single(self):
        ch = L.parse_chain(URDF, "ur5_base_link", "ur5_wrist_3_link")
        q = np.array([[0, -1.5708, 0, -1.5708, 0, 0], [0.3, -1.2, 0.5, -1.0, 0.2, 0.1], [-2.0, -0.5, 1.7, -2.2, 1.1, 3.0]])
        P, R = L.fk_batch(ch, q)
        for i in range(3):
            T = L.fk(ch, dict(zip(J, q[i])))
            self.assertTrue(np.allclose(P[i], T[:3, 3], atol=1e-12)); self.assertTrue(np.allclose(R[i], T[:3, :3], atol=1e-12))

    def test_ur5_upright_pose_known(self):
        ch = L.parse_chain(URDF, "ur5_base_link", "ur5_wrist_3_link")
        P, _ = L.fk_batch(ch, np.array([[0, -math.pi / 2, 0, -math.pi / 2, 0, 0]]))
        # upright arm: x~0; y = wrist offsets (0.1333-0.0997+0.0996...), z = 0.0892+0.425+0.3922+0.0947+... (from the URDF)
        self.assertAlmostEqual(P[0, 0], 0.0, places=4)
        self.assertGreater(P[0, 2], 0.9)
        self.assertLess(P[0, 2], 1.1)

    def test_quaternion_sign_equivalent(self):
        q = np.array([0.1, -0.3, 0.5, 0.8]); q = q / np.linalg.norm(q)
        self.assertTrue(np.allclose(L.quat_to_R(q), L.quat_to_R(-q)))
        self.assertAlmostEqual(float(L.rot_angle(L.quat_to_R(q), L.quat_to_R(-q))), 0.0, places=7)

    def test_rot_angle_known(self):
        c, s = math.cos(0.3), math.sin(0.3)
        Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        self.assertAlmostEqual(float(L.rot_angle(np.eye(3), Rz)), 0.3, places=12)
        self.assertAlmostEqual(float(L.rot_angle(Rz, np.eye(3))), 0.3, places=12)   # symmetric

    def test_wrong_frame_chain_detected(self):
        with self.assertRaises(L.InvalidInput):
            L.parse_chain(PLANAR, "b", "nonexistent")

    def test_ee_bound_positive_and_covers_speed(self):
        ch = L.parse_chain(URDF, "ur5_base_link", "ur5_wrist_3_link")
        q = np.array([[0.3, -1.2, 0.5, -1.0, 0.2, 0.1]])
        vb, wb = L.ee_bounds_batch(ch, q, {j: 3.14 for j in J})
        dq = np.array([0.0, 0.01, 0.0, 0.0, 0.0, 0.0])
        P0, _ = L.fk_batch(ch, q); P1, _ = L.fk_batch(ch, q + dq * 1e-3)
        self.assertLess(np.linalg.norm(P1 - P0) / 1e-3, vb[0])


class Pairing(unittest.TestCase):
    def test_nearest_and_limit(self):
        ta = np.array([0.0, 0.1, 0.2]); tb = np.array([0.001, 0.2005, 0.5])
        pick, dt = L.nearest_pairs(ta, tb, 0.004)
        self.assertEqual(list(pick), [0, -1, 1]); self.assertAlmostEqual(dt[0], 0.001)

    def test_t_ref_detection(self):
        t = np.arange(0, 2, 0.01); d = np.zeros((t.size, 6)); d[t > 1.0, 2] = 1e-3 * (t[t > 1.0] - 1.0)
        tr, per = L.find_t_ref(t, d, np.zeros(6), [2], 1e-6)
        self.assertAlmostEqual(tr, 1.01, places=6)
        with self.assertRaises(L.InvalidInput):
            L.find_t_ref(t, np.zeros((t.size, 6)), np.zeros(6), [2], 1e-6)


# ---------------------------------------------------------------- synthetic end-to-end runs
def R_to_quat(R):
    tr = np.trace(R)
    if tr > 0:
        s = math.sqrt(tr + 1) * 2
        return [(R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, 0.25 * s]
    i = int(np.argmax(np.diag(R))); j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(1 + R[i, i] - R[j, j] - R[k, k]) * 2
    q = [0.0] * 4
    q[i] = 0.25 * s; q[j] = (R[j, i] + R[i, j]) / s; q[k] = (R[k, i] + R[i, k]) / s; q[3] = (R[k, j] - R[j, k]) / s
    return q


def write_csv(path, header, rows):
    np.savetxt(path, np.asarray(rows), delimiter=",", header=",".join(header), comments="", fmt="%.17g")


def make_run(d, case="P+", err_amp=2e-5, backfill=False):
    """A synthetic but physically consistent run: cubic reference, small sinusoidal tracking error, joint_states = actual,
    Gazebo truth = FK(actual). 125 Hz streams with 8 ms spacing."""
    c = CFG["cases"][case]; tm = CFG["timing"]
    q0 = np.array(CFG["robot"]["q_init"]); dq = np.array(c["dq"]); T = c["T"]
    rec_t0 = 5.0; sent = rec_t0 + tm["pre_hold_s"]; t_ref = sent + 0.008
    rec_t1 = sent + T + tm["settle_s"] + 1.0
    t = np.arange(rec_t0 - 1.0, rec_t1 + 1.0, 0.008)
    u = np.clip((t - t_ref) / T, 0, 1); s = 3 * u ** 2 - 2 * u ** 3
    sd = 6 * u * (1 - u) / T * ((t >= t_ref) & (t <= t_ref + T))
    des = q0 + np.outer(s, dq); dv = np.outer(sd, dq)
    act = des + err_amp * np.sin(7 * t)[:, None] * np.linspace(0.2, 1, 6)
    av = dv + 1e-4 * np.cos(7 * t)[:, None]
    if backfill:
        act, av = des.copy(), dv.copy()
    err = des - act; ev = dv - av
    os.makedirs(os.path.join(d, "raw"))
    z = np.zeros_like(act)
    seq = np.arange(t.size)
    hdr_st = ["t_header", "t_bag", "seq"] + ["%s%s" % (p, j) for p in ("des_", "act_", "err_", "desvel_", "actvel_", "errvel_") for j in J]
    write_csv(os.path.join(d, "raw", "controller_state.csv"), hdr_st, np.column_stack([t, t, seq, des, act, err, dv, av, ev]))
    hdr_js = ["t_header", "t_bag", "seq"] + ["pos_" + j for j in J] + ["vel_" + j for j in J] + ["eff_" + j for j in J]
    write_csv(os.path.join(d, "raw", "joint_states.csv"), hdr_js, np.column_stack([t + 0.0005, t + 0.0005, seq, act, av, z]))
    ch = L.parse_chain(URDF, "ur5_base_link", "ur5_wrist_3_link")
    P, R = L.fk_batch(ch, act)
    tl = t[::2]  # 62.5 Hz would be too coarse for pairing; use every sample
    rows = []
    for i in range(t.size):
        qt = R_to_quat(R[i])
        rows.append([t[i] + 0.001, 0, 0, 0, 0, 0, 0, 1, P[i, 0], P[i, 1], P[i, 2]] + qt)
    write_csv(os.path.join(d, "raw", "link_truth.csv"), ["t_bag"] + ["b_" + k for k in ("x", "y", "z", "qx", "qy", "qz", "qw")] + ["t_" + k for k in ("x", "y", "z", "qx", "qy", "qz", "qw")], rows)
    write_csv(os.path.join(d, "raw", "clock.csv"), ["t", "t_bag"], np.column_stack([np.arange(rec_t0 - 1, rec_t1 + 1, 0.0005), np.arange(rec_t0 - 1, rec_t1 + 1, 0.0005)]))
    json.dump({"counts": {}, "incomplete_joint_states": 0, "incomplete_controller_state": 0, "non_finite_rows": 0, "missing_link_messages": 0, "rows": {}},
              open(os.path.join(d, "raw", "bag_summary.json"), "w"))
    q_target = (q0 + dq).tolist()
    msg = L.command_record(fake_msg([(q0.tolist(), [0.0] * 6, [], [], (0, 0)), (q_target, [0.0] * 6, [], [], (int(T), int(round((T % 1) * 1e9))))]))
    json.dump([{"t_bag": sent, "seq": 0, "message": msg}], open(os.path.join(d, "raw", "bag_commands.json"), "w"))
    json.dump({"run_id": "synthetic", "case": case, "rec_t0": rec_t0, "rec_t1": rec_t1, "base_pose_start": [0, 0, 0, 0, 0, 0, 1], "base_pose_end": [0, 0, 0, 0, 0, 0, 1],
               "commands": [{"sim_time_before_publish": sent, "sim_time_after_publish": sent, "q_start_observed": q0.tolist(), "q_start_minus_q_init": [0.0] * 6,
                             "dq": dq.tolist(), "q_target": q_target, "duration_s": T, "message": msg}]}, open(os.path.join(d, "commands.json"), "w"))
    open(os.path.join(d, "robot_description.urdf"), "w").write(URDF)
    return d


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="t1e2e-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_dir(self, name, **kw):
        return make_run(os.path.join(self.tmp, name), **kw)

    def test_good_run_passes_and_reports_known_error(self):
        d = self.run_dir("good", err_amp=2e-5)
        res = A.analyze_run(d, cfg=CFG)
        self.assertTrue(res["pass"], res["failed_gates"])
        # amplitude-scaled sinusoid error: the largest joint (x1.0) has peak ~2e-5 and RMSE ~2e-5/sqrt(2)
        eq = res["metrics"]["motion"]["e_q"]
        self.assertAlmostEqual(max(eq["max_abs"]), 2e-5, delta=2e-6)
        self.assertAlmostEqual(max(eq["rmse"]), 2e-5 / math.sqrt(2), delta=2e-6)
        self.assertTrue(os.path.exists(os.path.join(d, "curves.npz")))
        self.assertAlmostEqual(res["t_ref"]["t_ref_s"], 10.008, delta=0.0085)
        self.assertLess(res["quality"]["interpolation"]["max_abs_residual_rad"], 1e-9)
        self.assertEqual(res["quality"]["source_audit"]["controller_error_field"]["convention"], "desired - actual")

    def test_backfilled_actual_rejected(self):
        res = A.analyze_run(self.run_dir("bf", backfill=True), cfg=CFG)
        self.assertFalse(res["pass"]); self.assertIn("actual_not_backfilled", res["failed_gates"])

    def test_different_reference_and_actual_preserved(self):
        res = A.analyze_run(self.run_dir("diff", err_amp=1e-3), cfg=CFG)
        self.assertGreater(max(res["metrics"]["motion"]["e_q"]["max_abs"]), 9e-4)

    def test_clock_backward_fails(self):
        d = self.run_dir("clk")
        a = np.loadtxt(os.path.join(d, "raw", "clock.csv"), delimiter=",", skiprows=1)
        a[5000:, 0] -= 0.5
        write_csv(os.path.join(d, "raw", "clock.csv"), ["t", "t_bag"], a)
        res = A.analyze_run(d, cfg=CFG)
        self.assertFalse(res["pass"]); self.assertIn("clock_monotonic", res["failed_gates"])

    def test_controller_gap_fails(self):
        d = self.run_dir("gap")
        p = os.path.join(d, "raw", "controller_state.csv")
        a = np.loadtxt(p, delimiter=",", skiprows=1)
        hdr = open(p).readline().strip().split(",")
        a = np.delete(a, np.arange(600, 620), axis=0)   # 160 ms hole inside the motion/settle region
        write_csv(p, hdr, a)
        res = A.analyze_run(d, cfg=CFG)
        self.assertFalse(res["pass"])
        self.assertTrue(any(g.startswith("quality_") for g in res["failed_gates"]))

    def test_backward_timestamps_in_stream_fail(self):
        d = self.run_dir("back")
        p = os.path.join(d, "raw", "joint_states.csv")
        a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
        a[[700, 701]] = a[[701, 700]]   # reordered pair -> one backward step
        write_csv(p, hdr, a)
        res = A.analyze_run(d, cfg=CFG)
        self.assertFalse(res["pass"]); self.assertIn("streams_time_ordered", res["failed_gates"])

    def test_incomplete_messages_fail(self):
        d = self.run_dir("inc")
        p = os.path.join(d, "raw", "bag_summary.json")
        s = json.load(open(p)); s["incomplete_controller_state"] = 3
        json.dump(s, open(p, "w"))
        res = A.analyze_run(d, cfg=CFG)
        self.assertFalse(res["pass"]); self.assertIn("bag_integrity", res["failed_gates"])

    def test_truth_mismatch_fails(self):
        d = self.run_dir("truth")
        p = os.path.join(d, "raw", "link_truth.csv")
        a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
        a[:, 8] += 0.01   # tip x shifted by 1 cm: a wrong frame / link would look like this
        write_csv(p, hdr, a)
        res = A.analyze_run(d, cfg=CFG)
        self.assertFalse(res["pass"]); self.assertIn("gazebo_truth_consistent", res["failed_gates"])

    def test_truth_quaternion_sign_flip_still_passes(self):
        d = self.run_dir("qflip")
        p = os.path.join(d, "raw", "link_truth.csv")
        a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
        a[:, 11:15] *= -1   # q and -q are the same orientation
        write_csv(p, hdr, a)
        self.assertTrue(A.analyze_run(d, cfg=CFG)["pass"])

    def test_joint_states_disagree_fails(self):
        d = self.run_dir("js")
        p = os.path.join(d, "raw", "joint_states.csv")
        a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
        a[:, 3] += 1e-2
        write_csv(p, hdr, a)
        res = A.analyze_run(d, cfg=CFG)
        self.assertFalse(res["pass"]); self.assertIn("joint_states_consistent", res["failed_gates"])

    def test_base_drift_fails(self):
        d = self.run_dir("base")
        p = os.path.join(d, "commands.json")
        c = json.load(open(p)); c["base_pose_end"][0] = 1e-3
        json.dump(c, open(p, "w"))
        res = A.analyze_run(d, cfg=CFG)
        self.assertFalse(res["pass"]); self.assertIn("base_fixed", res["failed_gates"])

    def test_commands_bag_mismatch_fails(self):
        d = self.run_dir("cmd")
        p = os.path.join(d, "raw", "bag_commands.json")
        b = json.load(open(p)); b[0]["message"]["points"][1]["positions"][0] += 1e-6
        json.dump(b, open(p, "w"))
        res = A.analyze_run(d, cfg=CFG)
        self.assertFalse(res["pass"]); self.assertIn("commands_match_bag", res["failed_gates"])

    def test_wrong_interpolation_detected(self):
        d = self.run_dir("interp")
        p = os.path.join(d, "raw", "controller_state.csv")
        a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
        t = a[:, 0]; T = CFG["cases"]["P+"]["T"]; t_ref = 10.008
        u = np.clip((t - t_ref) / T, 0, 1)
        lin = np.array(CFG["robot"]["q_init"]) + np.outer(u, CFG["cases"]["P+"]["dq"])   # linear ramp instead of the cubic
        a[:, 3:9] = lin; a[:, 9:15] = lin; a[:, 15:21] = 0
        write_csv(p, hdr, a)
        res = A.analyze_run(d, cfg=CFG)
        self.assertIn("interpolation_matches_cubic", res["failed_gates"])

    def test_missing_input_is_invalid_not_pass(self):
        d = self.run_dir("miss")
        os.remove(os.path.join(d, "raw", "link_truth.csv"))
        with self.assertRaises(L.InvalidInput):
            A.analyze_run(d, cfg=CFG)

    def test_no_motion_observed_is_invalid_run(self):
        d = self.run_dir("nomove", case="P+")
        p = os.path.join(d, "raw", "controller_state.csv")
        a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
        a[:, 3:9] = np.array(CFG["robot"]["q_init"])   # desired never moves
        write_csv(p, hdr, a)
        res = A.analyze_run(d, cfg=CFG)
        self.assertFalse(res["pass"]); self.assertIn("motion_observed", res["failed_gates"])


def good_record(T=3.0):
    q0 = [0.0, -1.5708, 0.0, -1.5708, 0.0, 0.0]
    q1 = [0.2, -1.5708, 0.0, -1.5708, 0.0, 0.0]
    return L.command_record(fake_msg([(q0, [0.0] * 6, [0.1] * 6, [0.5] * 6, (0, 0)), (q1, [0.0] * 6, [], [], (int(T), 0))], stamp=(0, 0), frame_id=""))


def as_bag(rec):
    return [{"t_bag": 1.0, "seq": 0, "message": json.loads(json.dumps(rec))}]


class Quaternions(unittest.TestCase):
    """task1.7 P2-1: zero / non-finite quaternion norm must be rejected, never turned into NaN."""

    def test_zero_nan_inf_rejected(self):
        for q in ([0, 0, 0, 0], [float("nan"), 0, 0, 1], [0, float("inf"), 0, 1], [0, 0, 0, -float("inf")], [1e-9, 0, 0, 0], [0, 0, 0]):
            with self.assertRaises(L.InvalidInput, msg=str(q)):
                L.quat_to_R(q)
            self.assertFalse(L.quat_norm_ok(q))

    def test_valid_and_sign_equivalent_accepted(self):
        q = np.array([0.1, -0.3, 0.5, 0.8]); q = q / np.linalg.norm(q)
        R1, R2, R3 = L.quat_to_R(q), L.quat_to_R(-q), L.quat_to_R(2.0 * q)
        self.assertTrue(np.all(np.isfinite(R1)))
        self.assertTrue(np.allclose(R1, R2) and np.allclose(R1, R3))
        self.assertAlmostEqual(float(L.rot_angle(R1, R2)), 0.0, places=7)
        self.assertTrue(L.quat_norm_ok([0, 0, 0, 1]))

    def test_zero_quaternion_in_truth_fails_run_not_nan_pass(self):
        for name, cols in (("base", (4, 5, 6, 7)), ("tip", (11, 12, 13, 14))):
            tmp = tempfile.mkdtemp(prefix="t1q-")
            try:
                d = make_run(os.path.join(tmp, "z"))
                p = os.path.join(d, "raw", "link_truth.csv")
                a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
                a[:, list(cols)] = 0.0
                write_csv(p, hdr, a)
                res = A.analyze_run(d, cfg=CFG)
                g = res["quality"]["gazebo_truth"]
                self.assertFalse(res["pass"], name); self.assertIn("gazebo_truth_consistent", res["failed_gates"])
                self.assertFalse(g["pass"]); self.assertIn("quaternions", g["reason"]); self.assertGreater(g["quat_bad_rows"][name], 0)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    def test_single_bad_row_fails(self):
        tmp = tempfile.mkdtemp(prefix="t1q-")
        try:
            d = make_run(os.path.join(tmp, "one"))
            p = os.path.join(d, "raw", "link_truth.csv")
            a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
            a[300, 11:15] = 0.0   # one tip row only
            write_csv(p, hdr, a)
            res = A.analyze_run(d, cfg=CFG)
            self.assertFalse(res["pass"]); self.assertEqual(res["quality"]["gazebo_truth"]["quat_bad_rows"]["tip"], 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_nan_quaternion_in_csv_is_invalid_input(self):
        tmp = tempfile.mkdtemp(prefix="t1q-")
        try:
            d = make_run(os.path.join(tmp, "nan"))
            p = os.path.join(d, "raw", "link_truth.csv")
            a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
            a[10, 4] = float("nan")
            write_csv(p, hdr, a)
            with self.assertRaises(L.InvalidInput):
                A.analyze_run(d, cfg=CFG)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_unpaired_in_window_overflow_norm_row_fails(self):
        """task1.9: components are finite but their norm overflows to Inf, on a row the nearest-neighbour pairing never selects."""
        for name, cols in (("base", (4, 5, 6, 7)), ("tip", (11, 12, 13, 14))):
            tmp = tempfile.mkdtemp(prefix="t1q-")
            try:
                d = make_run(os.path.join(tmp, "ovf"))
                self.assertTrue(A.analyze_run(d, cfg=CFG)["pass"])        # control: unmodified run passes
                p = os.path.join(d, "raw", "link_truth.csv")
                a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
                k = 400
                extra = a[k].copy()
                extra[0] += 0.004                       # between two controller samples: its nearest truth row is a different, closer one
                extra[list(cols)] = [1e308, 0.0, 0.0, 1.0]
                a = np.insert(a, k + 1, extra, axis=0)
                self.assertTrue(np.all(np.diff(a[:, 0]) > 0))
                with np.errstate(over="ignore"):
                    self.assertTrue(np.isinf(np.linalg.norm(a[k + 1, list(cols)])) and np.all(np.isfinite(a[k + 1, list(cols)])))
                cm = np.loadtxt(os.path.join(d, "raw", "controller_state.csv"), delimiter=",", skiprows=1)
                pick, _ = L.nearest_pairs(cm[:, 0], a[:, 0], CFG["quality"]["truth_dt_max_s"])
                self.assertNotIn(k + 1, set(pick.tolist()))              # the bad row is NOT used by any pairing
                self.assertTrue(cm[0, 0] < a[k + 1, 0] < cm[-1, 0])      # ... and it lies inside the recording
                write_csv(p, hdr, a)
                res = A.analyze_run(d, cfg=CFG)
                g = res["quality"]["gazebo_truth"]
                self.assertFalse(res["pass"], name); self.assertIn("gazebo_truth_consistent", res["failed_gates"])
                self.assertEqual(g["quat_bad_rows"][name], 1); self.assertEqual(g["quat_bad_rows"]["tip" if name == "base" else "base"], 0)
                self.assertFalse(g["pass"]); self.assertIn("quaternions", g["reason"])
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    def test_unpaired_in_window_nan_zero_rows_also_counted(self):
        for val in (0.0,):
            tmp = tempfile.mkdtemp(prefix="t1q-")
            try:
                d = make_run(os.path.join(tmp, "unp"))
                p = os.path.join(d, "raw", "link_truth.csv")
                a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
                extra = a[400].copy(); extra[0] += 0.004; extra[11:15] = [val] * 4
                write_csv(p, hdr, np.insert(a, 401, extra, axis=0))
                res = A.analyze_run(d, cfg=CFG)
                self.assertFalse(res["pass"]); self.assertEqual(res["quality"]["gazebo_truth"]["quat_bad_rows"]["tip"], 1)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    def test_large_finite_norm_is_not_an_overflow(self):
        """Boundary: a huge but finite norm satisfies the stated criterion (finite and >= min); only the overflow/zero/NaN/Inf cases are bad."""
        tmp = tempfile.mkdtemp(prefix="t1q-")
        try:
            d = make_run(os.path.join(tmp, "big"))
            p = os.path.join(d, "raw", "link_truth.csv")
            a = np.loadtxt(p, delimiter=",", skiprows=1); hdr = open(p).readline().strip().split(",")
            extra = a[400].copy(); extra[0] += 0.004; extra[11:15] = [1e100, 0.0, 0.0, 1.0]
            write_csv(p, hdr, np.insert(a, 401, extra, axis=0))
            g = A.analyze_run(d, cfg=CFG)["quality"]["gazebo_truth"]
            self.assertEqual(g["quat_bad_rows"], {"base": 0, "tip": 0})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_non_finite_error_cannot_pass(self):
        """Direct call with an infinite position in the truth stream: the finiteness guard must reject (NaN/inf compare as 'no violation')."""
        ch = L.parse_chain(URDF, "ur5_base_link", "ur5_wrist_3_link")
        n = 300
        t = np.arange(n) * 0.008
        q = np.tile(CFG["robot"]["q_init"], (n, 1)); qd = np.zeros((n, 6))
        P, R = L.fk_batch(ch, q)
        truth = {"t_bag": t, "b_x": np.zeros(n), "b_y": np.zeros(n), "b_z": np.zeros(n), "b_qx": np.zeros(n), "b_qy": np.zeros(n), "b_qz": np.zeros(n), "b_qw": np.ones(n),
                 "t_x": P[:, 0], "t_y": P[:, 1], "t_z": P[:, 2]}
        for k, c in enumerate(("t_qx", "t_qy", "t_qz", "t_qw")):
            truth[c] = np.array([R_to_quat(R[0])[k]] * n)
        vlim = {j: 3.14 for j in J}
        ok = A.check_truth(ch, vlim, t, q, qd, truth, CFG["quality"], {})
        self.assertTrue(ok["pass"], ok)                      # control: the clean input passes
        truth["t_x"] = truth["t_x"].copy(); truth["t_x"][5] = float("inf")
        bad = A.check_truth(ch, vlim, t, q, qd, truth, CFG["quality"], {})
        self.assertFalse(bad["pass"])
        self.assertFalse(bad.get("all_finite", True))

    def test_zero_base_pose_quaternion_fails_drift_gate(self):
        tmp = tempfile.mkdtemp(prefix="t1q-")
        try:
            d = make_run(os.path.join(tmp, "bp"))
            p = os.path.join(d, "commands.json")
            c = json.load(open(p)); c["base_pose_end"][3:] = [0, 0, 0, 0]
            json.dump(c, open(p, "w"))
            res = A.analyze_run(d, cfg=CFG)
            self.assertFalse(res["pass"]); self.assertIn("base_fixed", res["failed_gates"])
            self.assertIn("invalid quaternion", res["quality"]["base_drift"]["invalid_quaternion"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_clean_run_reports_quaternion_norms(self):
        tmp = tempfile.mkdtemp(prefix="t1q-")
        try:
            res = A.analyze_run(make_run(os.path.join(tmp, "ok")), cfg=CFG)
            self.assertTrue(res["pass"], res["failed_gates"])
            g = res["quality"]["gazebo_truth"]
            self.assertAlmostEqual(g["quat_norm"]["base_min"], 1.0, places=9); self.assertEqual(g["quat_bad_rows"], {"base": 0, "tip": 0})
            self.assertEqual(res["analysis_version"], A.ANALYSIS_VERSION)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class CommandSchema(unittest.TestCase):
    """task1.7 P2-2: sent record and bag record share one schema; every field of every point is compared."""

    def test_record_shape(self):
        r = good_record()
        self.assertEqual(r["schema"], L.COMMAND_SCHEMA)
        self.assertEqual(r["header"], {"stamp": [0, 0], "frame_id": ""})
        self.assertEqual(r["points"][1]["time_from_start"], [3, 0])
        self.assertEqual(set(r["points"][0]), {"positions", "velocities", "accelerations", "effort", "time_from_start"})

    def test_identical_records_match(self):
        r = good_record()
        res = L.compare_commands(r, as_bag(r))
        self.assertTrue(res["match"], res["mismatches"]); self.assertEqual(res["not_compared"], [])

    def test_every_single_field_mutation_is_caught(self):
        base = good_record()
        muts = []
        for pi in (0, 1):
            for f in ("positions", "velocities"):
                for ji in (0, 5):
                    muts.append(("point %d %s[%d]" % (pi, f, ji), lambda m, pi=pi, f=f, ji=ji: m["points"][pi][f].__setitem__(ji, m["points"][pi][f][ji] + 1e-9)))
        muts += [("point 0 accelerations", lambda m: m["points"][0]["accelerations"].__setitem__(0, 0.2)),
                 ("point 0 accel dropped", lambda m: m["points"][0].__setitem__("accelerations", [])),
                 ("point 1 accel added", lambda m: m["points"][1].__setitem__("accelerations", [0.0] * 6)),
                 ("point 0 effort", lambda m: m["points"][0]["effort"].__setitem__(2, 0.0)),
                 ("point 1 effort added", lambda m: m["points"][1].__setitem__("effort", [1.0] * 6)),
                 ("tfs[1] secs", lambda m: m["points"][1]["time_from_start"].__setitem__(0, 4)),
                 ("tfs[1] nsecs", lambda m: m["points"][1]["time_from_start"].__setitem__(1, 1)),
                 ("tfs[0] nsecs", lambda m: m["points"][0]["time_from_start"].__setitem__(1, 1)),
                 ("header secs", lambda m: m["header"]["stamp"].__setitem__(0, 1)),
                 ("header nsecs", lambda m: m["header"]["stamp"].__setitem__(1, 1)),
                 ("frame_id", lambda m: m["header"].__setitem__("frame_id", "base")),
                 ("joint order", lambda m: m["joint_names"].reverse()),
                 ("joint rename", lambda m: m["joint_names"].__setitem__(0, "other")),
                 ("point dropped", lambda m: m["points"].pop()),
                 ("point added", lambda m: m["points"].append(json.loads(json.dumps(m["points"][0])))),
                 ("first point swapped", lambda m: m["points"].reverse())]
        for name, mut in muts:
            bag = as_bag(base); mut(bag[0]["message"])
            res = L.compare_commands(base, bag)
            self.assertFalse(res["match"], "mutation not caught: " + name)
            sent_mut = json.loads(json.dumps(base)); mut(sent_mut)
            self.assertFalse(L.compare_commands(sent_mut, as_bag(base))["match"], "sent-side mutation not caught: " + name)

    def test_nan_and_inf_never_match(self):
        r = good_record()
        for val in (float("nan"), float("inf")):
            both = json.loads(json.dumps(r, allow_nan=True)); both["points"][1]["velocities"][0] = val
            res = L.compare_commands(both, as_bag(both))
            self.assertFalse(res["match"], val)

    def test_message_count_must_be_one(self):
        r = good_record()
        self.assertFalse(L.compare_commands(r, [])["match"])
        self.assertFalse(L.compare_commands(r, as_bag(r) + as_bag(r))["match"])

    def test_wrong_bag_schema_rejected(self):
        r = good_record()
        old_bag = [{"t_bag": 1.0, "header_stamp": 0.0, "joint_names": J, "points": []}]
        res = L.compare_commands(r, old_bag)
        self.assertFalse(res["match"]); self.assertIn("schema", res["mismatches"][0])

    def test_legacy_sent_record_compared_and_limitation_stated(self):
        r = good_record()
        leg = legacy_record(r)
        res = L.compare_commands(leg, as_bag(r))
        self.assertTrue(res["match"], res["mismatches"]); self.assertTrue(any("frame_id" in n for n in res["not_compared"]))
        leg["points"][1]["velocities"][3] = 0.5
        self.assertFalse(L.compare_commands(leg, as_bag(r))["match"])
        leg = legacy_record(r); leg["points"][1]["time_from_start"] += 0.001
        self.assertFalse(L.compare_commands(leg, as_bag(r))["match"])
        leg = legacy_record(r); leg["header_stamp"] = [0, 1]
        self.assertFalse(L.compare_commands(leg, as_bag(r))["match"])

    def test_end_to_end_velocity_mutation_in_bag_fails_run(self):
        """The exact task1.6 reproduction: only the second point's pan velocity changed in the bag record."""
        tmp = tempfile.mkdtemp(prefix="t1c-")
        try:
            d = make_run(os.path.join(tmp, "v"))
            self.assertTrue(A.analyze_run(d, cfg=CFG)["pass"])       # control: unmodified run passes
            p = os.path.join(d, "raw", "bag_commands.json")
            b = json.load(open(p)); b[0]["message"]["points"][1]["velocities"][0] = 0.5
            json.dump(b, open(p, "w"))
            res = A.analyze_run(d, cfg=CFG)
            self.assertFalse(res["pass"]); self.assertIn("commands_match_bag", res["failed_gates"])
            self.assertTrue(any("velocities" in m for m in res["quality"]["commands_match_bag"]["mismatches"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_end_to_end_each_field_in_sent_record_fails_run(self):
        for name, mut in (("effort", lambda m: m["points"][0].__setitem__("effort", [1.0] * 6)),
                          ("header frame", lambda m: m["header"].__setitem__("frame_id", "x")),
                          ("first point position", lambda m: m["points"][0]["positions"].__setitem__(1, 0.0))):
            tmp = tempfile.mkdtemp(prefix="t1c-")
            try:
                d = make_run(os.path.join(tmp, "s"))
                p = os.path.join(d, "commands.json")
                c = json.load(open(p)); mut(c["commands"][0]["message"]); json.dump(c, open(p, "w"))
                res = A.analyze_run(d, cfg=CFG)
                self.assertFalse(res["pass"], name); self.assertIn("commands_match_bag", res["failed_gates"])
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    def test_legacy_commands_json_still_analyzable_with_new_bag_record(self):
        tmp = tempfile.mkdtemp(prefix="t1c-")
        try:
            d = make_run(os.path.join(tmp, "l"))
            p = os.path.join(d, "commands.json")
            c = json.load(open(p)); c["commands"][0]["message"] = legacy_record(c["commands"][0]["message"]); json.dump(c, open(p, "w"))
            res = A.analyze_run(d, cfg=CFG)
            self.assertTrue(res["pass"], res["failed_gates"])
            self.assertTrue(any("frame_id" in n for n in res["quality"]["commands_match_bag"]["not_compared"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)



if __name__ == "__main__":
    unittest.main()
