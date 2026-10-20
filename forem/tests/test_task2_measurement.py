"""Task2.3 measurement-chain tests (numpy + PyYAML; no ROS, no simulator).

A synthetic but self-consistent run generator builds a complete run directory (raw CSV/JSON as written by task2_bag_to_csv.py, commands.json as written by
collect_task2.py, the proxy's events file, URDF) with a KNOWN injected delay and a KNOWN small servo error. The analysis must then
  * report e_total / e_schedule that are large and equal to the analytic value, e_servo that is only the small servo error (and exactly 0 for a perfect servo),
  * keep the original-send axis separate from the controller axis (re-basing the time origin on t_ref must make the test fail),
  * reject every bad input class: dropped / extra / altered commands, wrong hash, missing / forbidden proxy events, early or late delivery, header and
    velocity mutations, clock backward, gaps, duplicates, coverage, bad quaternions (incl. unpaired in-window overflow norms), desired moving before delivery.
Run (container has numpy): bash forem/docker/run.sh exec python3 -W ignore -m unittest discover -s tests -p 'test_task2_measurement.py' -v
"""
import copy
import json
import math
import os
import shutil
import sys
import tempfile
import unittest

try:
    import numpy as np
    import yaml
except ImportError as e:  # the host python has no numpy: these tests run in forem-dev
    raise unittest.SkipTest("numpy/PyYAML not available: %s (run inside forem-dev)" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, HERE)
import analyze_task2 as A2  # noqa: E402
import task1_lib as L  # noqa: E402
import task2_delay_queue as Q  # noqa: E402
from test_task1_measurement import R_to_quat, fake_msg, write_csv  # noqa: E402

CFG = yaml.safe_load(open(os.path.join(HERE, "..", "config", "experiments", "exp2", "fixed_delay.yaml")))
URDF = open(os.path.join(HERE, "fixtures", "ur5_fixed.urdf")).read()
J = L.JOINTS
MS = 1_000_000
EPS_MAX = int(CFG["delay"]["eps_max_ms"] * MS)
SAG = 1e-4                       # synthetic: measured q_start differs from the controller's hold reference


def make_run(d, case="M3", mode="queue", tau_ms=80, servo_amp=2e-5, perfect_servo=False, eps_ns=0, in_lag_ns=1_500_000, t_ref_after_pub_s=0.004, run_id="synthetic"):
    c = CFG["cases"][case]
    tm = CFG["timing"]
    tau_ns = int(tau_ms * MS)
    tau = tau_ns / 1e9
    q0 = np.array(CFG["robot"]["q_init"])
    moving = c["dq"] is not None
    rec_t0 = 5.0
    send = rec_t0 + tm["pre_hold_s"]
    send_ns = int(round(send * 1e9))
    t_in_ns = send_ns + in_lag_ns
    t_due_ns = t_in_ns + tau_ns
    t_pub_ns = t_due_ns + eps_ns
    delivered = (send_ns if mode == "bypass" else t_pub_ns) / 1e9
    t_ref = delivered + t_ref_after_pub_s
    if moving:
        dq = np.array(c["dq"]); T = c["T"]
        rec_t1 = send + tau + T + tm["settle_s"] + CFG["runtime"]["tail_margin_s"]
    else:
        T = None
        rec_t1 = rec_t0 + tm["pre_hold_s"] + tm["hold_s"]
    t = np.arange(rec_t0 - 1.0, rec_t1 + 1.0, 0.008)
    if moving:
        u = np.clip((t - t_ref) / T, 0, 1)
        s = 3 * u ** 2 - 2 * u ** 3
        sd = 6 * u * (1 - u) / T * ((t >= t_ref) & (t <= t_ref + T))
        q_target = q0 + SAG + dq
        des = q0 + np.outer(s, q_target - q0)
        dv = np.outer(sd, q_target - q0)
    else:
        des = np.tile(q0, (t.size, 1)); dv = np.zeros_like(des)
    if perfect_servo:
        act, av = des.copy(), dv.copy()
    else:
        act = des + servo_amp * np.sin(7 * t)[:, None] * np.linspace(0.2, 1, 6)
        av = dv + 1e-4 * np.cos(7 * t)[:, None]
    err, ev = des - act, dv - av
    os.makedirs(os.path.join(d, "raw"))
    z = np.zeros_like(act)
    seq = np.arange(t.size)
    hdr_st = ["t_header", "t_bag", "seq"] + ["%s%s" % (p, j) for p in ("des_", "act_", "err_", "desvel_", "actvel_", "errvel_") for j in J]
    write_csv(os.path.join(d, "raw", "controller_state.csv"), hdr_st, np.column_stack([t, t, seq, des, act, err, dv, av, ev]))
    hdr_js = ["t_header", "t_bag", "seq"] + ["pos_" + j for j in J] + ["vel_" + j for j in J] + ["eff_" + j for j in J]
    write_csv(os.path.join(d, "raw", "joint_states.csv"), hdr_js, np.column_stack([t + 0.0005, t + 0.0005, seq, act, av, z]))
    ch = L.parse_chain(URDF, "ur5_base_link", "ur5_wrist_3_link")
    P, R = L.fk_batch(ch, act)
    rows = [[t[i] + 0.001, 0, 0, 0, 0, 0, 0, 1, P[i, 0], P[i, 1], P[i, 2]] + R_to_quat(R[i]) for i in range(t.size)]
    write_csv(os.path.join(d, "raw", "link_truth.csv"), ["t_bag"] + ["b_" + k for k in ("x", "y", "z", "qx", "qy", "qz", "qw")] + ["t_" + k for k in ("x", "y", "z", "qx", "qy", "qz", "qw")], rows)
    ck = np.arange(rec_t0 - 1, rec_t1 + 1, 0.0005)
    write_csv(os.path.join(d, "raw", "clock.csv"), ["t", "t_bag"], np.column_stack([ck, ck]))
    json.dump({"counts": {}, "incomplete_joint_states": 0, "incomplete_controller_state": 0, "non_finite_rows": 0, "missing_link_messages": 0, "unparsable_events": 0, "rows": {}},
              open(os.path.join(d, "raw", "bag_summary.json"), "w"))
    cmd = {"run_id": run_id, "case": case, "mode": mode, "delay_ms": float(tau_ms), "tau_ns": tau_ns, "rec_t0": rec_t0, "rec_t1": rec_t1,
           "base_pose_start": [0, 0, 0, 0, 0, 0, 1], "base_pose_end": [0, 0, 0, 0, 0, 0, 1], "commands": []}
    down, up, events = [], [], []
    if moving:
        q_start = q0 + SAG
        msg = L.command_record(fake_msg([(q_start.tolist(), [0.0] * 6, [], [], (0, 0)), (q_target.tolist(), [0.0] * 6, [], [], (int(T), int(round((T % 1) * 1e9))))]))
        cmd["commands"] = [{"epoch": 0, "seq": 0, "payload_sha256": Q.payload_hash(msg), "sim_time_before_publish": send, "sim_time_after_publish": send,
                            "sim_time_before_publish_ns": send_ns, "sim_time_after_publish_ns": send_ns, "q_start_observed": q_start.tolist(),
                            "q_start_minus_q_init": [SAG] * 6, "dq": dq.tolist(), "q_target": q_target.tolist(), "duration_s": T, "message": msg}]
        down = [{"t_bag": delivered, "seq": 7, "message": msg}]
        if mode == "queue":
            up = [{"t_bag": t_in_ns / 1e9, "seq": 7, "message": msg}]
    if mode == "queue":
        base = {"schema": "task2-delay-event/1", "run_id": run_id, "node": "/task2_delay_node", "epoch": 0}
        events.append(dict(base, type="ready", n=1, queue_len=0, delay_ns=tau_ns, capacity=64, t_node_clock_ns=send_ns - 4_000_000_000))
        if moving:
            h = cmd["commands"][0]["payload_sha256"]
            events.append(dict(base, type="enqueue", n=2, seq=0, t_in_ns=t_in_ns, t_due_ns=t_due_ns, payload_hash=h, queue_len=1, delay_ns=tau_ns, t_node_clock_ns=t_in_ns))
            events.append(dict(base, type="publish", n=3, seq=0, t_in_ns=t_in_ns, t_due_ns=t_due_ns, payload_hash=h, queue_len=0, delay_ns=tau_ns, t_node_clock_ns=t_pub_ns,
                               t_pub_before_ns=t_pub_ns, t_pub_after_ns=t_pub_ns, d_queue_ns=t_pub_ns - t_in_ns, eps_ns=t_pub_ns - t_in_ns - tau_ns))
        n = len(events)
        end_ns = int(round(rec_t1 * 1e9))
        events.append(dict(base, type="shutdown", n=n + 1, queue_len=0, delay_ns=tau_ns, reason="queue closed", t_node_clock_ns=end_ns))
        events.append(dict(base, type="node_exit", n=n + 2, queue_len=0, t_node_clock_ns=end_ns, failed=None, counts={"enqueued": int(moving), "published": int(moving), "rejected": 0, "dropped": 0}))
    json.dump(down, open(os.path.join(d, "raw", "bag_commands.json"), "w"))
    json.dump(up, open(os.path.join(d, "raw", "bag_commands_in.json"), "w"))
    json.dump([{"t_bag": e["t_node_clock_ns"] / 1e9, "event": e} for e in events], open(os.path.join(d, "raw", "bag_events.json"), "w"))
    if mode == "queue":
        open(os.path.join(d, "delay_events.jsonl"), "w").write("".join(json.dumps(e, sort_keys=True) + "\n" for e in events))
    json.dump(cmd, open(os.path.join(d, "commands.json"), "w"))
    open(os.path.join(d, "robot_description.urdf"), "w").write(URDF)
    return d


def load(d, name):
    return json.load(open(os.path.join(d, name)))


def save(d, name, obj):
    json.dump(obj, open(os.path.join(d, name), "w"))


class Pure(unittest.TestCase):
    def test_q_nominal_endpoints_and_midpoint(self):
        q = A2.q_nominal(np.array([0.0, 1.5, 3.0, 9.0]), np.zeros(2), np.array([1.0, -2.0]), 3.0, 0.0)
        np.testing.assert_allclose(q, [[0, 0], [0.5, -1.0], [1, -2], [1, -2]], atol=1e-15)
        q2 = A2.q_nominal(np.array([-5.0]), np.ones(2), np.array([1.0, 1.0]), 3.0, 0.0)
        np.testing.assert_allclose(q2, [[1, 1]])

    def test_v_nominal_is_the_derivative(self):
        t = np.linspace(-0.5, 3.5, 4001)
        q = A2.q_nominal(t, np.zeros(1), np.array([0.7]), 3.0, 0.2)
        v = A2.v_nominal(t, np.array([0.7]), 3.0, 0.2)
        num = np.gradient(q[:, 0], t)
        self.assertLess(np.max(np.abs(num - v[:, 0])), 2e-3)

    def test_identity_exact(self):
        rng = np.random.default_rng(1)
        a, r, n = rng.normal(size=(50, 6)), rng.normal(size=(50, 6)), rng.normal(size=(50, 6))
        es, esc, et, ident = A2.error_decomposition(a, r, n)
        self.assertLess(ident, 1e-14)
        np.testing.assert_allclose(et, es + esc, atol=1e-14)

    def test_known_delay_in_synthetic_signals_is_recovered_not_hidden(self):
        # perfect servo, reference delayed by 80 ms against the nominal schedule: e_servo ~ 0 but e_schedule / e_total are NOT
        t = np.arange(0, 12, 0.008)
        dq, T, t0, tau = np.array([0.3]), 3.0, 4.0, 0.080
        q_ref = A2.q_nominal(t, np.zeros(1), dq, T, t0 + tau)
        q_nom = A2.q_nominal(t, np.zeros(1), dq, T, t0)
        es, esc, et, _ = A2.error_decomposition(q_ref.copy(), q_ref, q_nom)
        self.assertEqual(float(np.max(np.abs(es))), 0.0)
        self.assertGreater(float(np.max(np.abs(et))), 0.3 * 1.5 / T * tau * 0.9)      # ~ peak speed * tau
        # re-basing the origin on the delayed start would make the schedule error vanish: this is exactly the mistake the analysis must not make
        q_rebased = A2.q_nominal(t, np.zeros(1), dq, T, t0 + tau)
        self.assertEqual(float(np.max(np.abs(q_ref - q_rebased))), 0.0)
        self.assertGreater(float(np.max(np.abs(q_ref - q_nom))), 1e-3)


class GoodRuns(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="t2e2e-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_dir(self, name, **kw):
        return make_run(os.path.join(self.tmp, name), **kw)

    def analyse(self, d, **kw):
        return A2.analyze_run(d, cfg=CFG, **kw)

    def test_delayed_run_passes_and_separates_delay_from_servo(self):
        d = self.run_dir("d80", tau_ms=80, servo_amp=2e-5)
        res = self.analyse(d)
        self.assertTrue(res["pass"], res["failed_gates"] + res["invalid_reasons"])
        m = res["metrics"]
        # servo error is only the injected 2e-5 sinusoid (largest joint peak 2e-5, rmse 2e-5/sqrt 2)
        self.assertAlmostEqual(max(m["motion"]["e_servo"]["max_abs"]), 2e-5, delta=2e-6)
        # the schedule / total error is the 80 ms (+4 ms ROS/controller + 1.5 ms upstream) shift of the cubic: tens of times larger than servo error
        speed_peak = max(1.5 * abs(x) / 3.0 for x in CFG["cases"]["M3"]["dq"])
        self.assertGreater(max(m["exec_nom"]["e_total"]["max_abs"]), 0.5 * speed_peak * 0.080)
        self.assertGreater(max(m["exec_nom"]["e_schedule"]["max_abs"]), 30 * max(m["exec_nom"]["e_servo"]["max_abs"]))
        d_ = res["delay"]
        self.assertAlmostEqual(d_["t_ref_minus_t0_mid_s"], 0.0015 + 0.080 + 0.004, delta=0.016)   # sample quantisation + 1e-6 rad threshold crossing
        self.assertAlmostEqual(d_["queue"]["d_queue_ns"] / 1e9, 0.080, places=9)
        self.assertEqual(d_["queue"]["eps_ns"], 0)
        # velocity correlation against the ORIGINAL schedule finds ~ the injected delay (ladder 8 ms)
        for j, ent in res["lag"].items():
            v = ent["vs_nominal_reference"]
            self.assertTrue(v["identifiable"], (j, v["reason"]))
            self.assertAlmostEqual(v["tau_s"], 0.088, delta=0.0085 + 1e-9)

    def test_fitted_start_recovers_subsample_start(self):
        # the true reference start is 3.7 ms after the proxy publish; samples are 8 ms apart, so the threshold t_ref is quantised but the fit is not
        for after in (0.0013, 0.0037, 0.0061):
            d = self.run_dir("fit%d" % int(after * 1e4), tau_ms=80, t_ref_after_pub_s=after)
            res = self.analyse(d)
            self.assertTrue(res["pass"], res["failed_gates"])
            true_start = 10.0 + 0.0015 + 0.080 + after
            self.assertAlmostEqual(res["delay"]["t_start_fit_s"], true_start, delta=2e-6)
            self.assertLess(res["quality"]["interpolation"]["refined_max_abs_residual_rad"], 1e-9)
            z = np.load(os.path.join(d, "curves.npz"))
            self.assertAlmostEqual(float(z["fit_t_start"]), true_start, delta=2e-6)
            self.assertEqual(z["fit_q_act"].shape, z["q_act"].shape)

    def test_fit_validity_and_identifiability_reported(self):
        d = self.run_dir("fitvalid", tau_ms=160, t_ref_after_pub_s=0.0037)
        res = self.analyse(d)
        fv = res["delay"]["fit_validity"]
        self.assertTrue(fv["valid"], fv)
        self.assertLess(fv["residual_max_abs_rad"], A2.FIT_RESIDUAL_MAX_RAD)
        self.assertGreaterEqual(min(fv["residual_at_start_minus_0p5ms_rad"], fv["residual_at_start_plus_0p5ms_rad"]), A2.FIT_SHIFT_SENSITIVITY_RAD)
        self.assertAlmostEqual(res["delay"]["t_ref_minus_t_start_fit_s"], res["delay"]["t_ref_s"] - res["delay"]["t_start_fit_s"], places=12)
        # the threshold t_ref differs from the true start by the sampling/threshold effect (up to ~one 8 ms sample plus threshold crossing), never the other way
        self.assertGreaterEqual(res["delay"]["t_ref_minus_t_start_fit_s"], -1e-6)
        self.assertLess(res["delay"]["t_ref_minus_t_start_fit_s"], 0.016)

    def test_curves_keep_two_time_axes(self):
        d = self.run_dir("axes", tau_ms=160)
        res = self.analyse(d)
        self.assertTrue(res["pass"], res["failed_gates"])
        z = np.load(os.path.join(d, "curves.npz"))
        # send axis: q_nom starts moving at t_rel=0, q_ref only ~tau later; both on the SAME axis
        t_rel = z["snd_t_rel"]
        i_nom = int(np.argmax(np.abs(z["snd_q_nom"][:, 1] - z["snd_q_nom"][0, 1]) > 1e-6))
        i_ref = int(np.argmax(np.abs(z["snd_q_ref"][:, 1] - z["snd_q_ref"][0, 1]) > 1e-6))
        self.assertLess(abs(t_rel[i_nom] - 0.0), 0.016)
        self.assertAlmostEqual(t_rel[i_ref], 0.0015 + 0.160 + 0.004, delta=0.02)
        # controller axis: servo curves start at t_ref
        self.assertAlmostEqual(float(z["t_ref"]), 10.0 + 0.0015 + 0.160 + 0.004, delta=0.016)
        self.assertEqual(z["e_q"].shape[1], 6)
        # e_total = e_servo + e_schedule on the grid too
        np.testing.assert_allclose(z["snd_e_total"], z["snd_e_servo"] + z["snd_e_schedule"], atol=1e-12, equal_nan=True)

    def test_perfect_servo_gives_zero_servo_error_but_nonzero_total(self):
        d = self.run_dir("perfect", tau_ms=80, perfect_servo=True)
        res = self.analyse(d)
        self.assertTrue(res["pass"] or res["failed_gates"] == ["actual_not_backfilled"], res["failed_gates"])   # actual == desired is flagged by the backfill audit
        self.assertEqual(max(res["metrics"]["motion"]["e_servo"]["max_abs"]), 0.0)
        self.assertGreater(max(res["metrics"]["exec_nom"]["e_total"]["max_abs"]), 1e-3)

    def test_bypass_and_zero_delay_queue_pass(self):
        for name, kw in (("bypass", {"mode": "bypass", "tau_ms": 0}), ("z", {"mode": "queue", "tau_ms": 0})):
            d = self.run_dir(name, **kw)
            res = self.analyse(d)
            self.assertTrue(res["pass"], (name, res["failed_gates"]))
            self.assertEqual(res["tau_ns"], 0)

    def test_hold_case_both_modes(self):
        for name, kw in (("hb", {"mode": "bypass", "tau_ms": 0}), ("hz", {"mode": "queue", "tau_ms": 0}), ("h80", {"mode": "queue", "tau_ms": 80})):
            d = self.run_dir(name, case="H", **kw)
            res = self.analyse(d)
            self.assertTrue(res["pass"], (name, res["failed_gates"], res["invalid_reasons"]))
            self.assertIn("hold", res["metrics"])

    def test_send_interval_sensitivity_reported(self):
        d = self.run_dir("sens")
        c = load(d, "commands.json")
        c["commands"][0]["sim_time_after_publish_ns"] += 4_000_000
        c["commands"][0]["sim_time_after_publish"] += 0.004
        save(d, "commands.json", c)
        res = self.analyse(d)
        s = res["send_interval_sensitivity"]
        self.assertAlmostEqual(s["t_send_width_s"], 0.004, places=9)
        self.assertGreater(s["per_window"]["exec_nom"]["max_abs_rmse_change_vs_mid"], 0.0)
        self.assertLess(s["per_window"]["exec_nom"]["max_abs_rmse_change_vs_mid"], max(s["q_nom_change_bound_rad"]) * 1.001)

    def test_existing_analysis_is_never_overwritten_and_out_dir_works(self):
        d = self.run_dir("ow")
        self.analyse(d)
        with self.assertRaises(L.InvalidInput):
            self.analyse(d)
        out = os.path.join(self.tmp, "new_analysis")
        res = self.analyse(d, out_dir=out)
        self.assertTrue(res["pass"])
        self.assertTrue(os.path.exists(os.path.join(out, "curves.npz")))


class BadInputs(unittest.TestCase):
    """Each mutation must produce a FAILED run (pass False), never a pass; the unmutated control passes."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="t2bad-")
        self.n = 0

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def fresh(self, **kw):
        self.n += 1
        return make_run(os.path.join(self.tmp, "r%d" % self.n), **kw)

    def failed(self, d):
        res = A2.analyze_run(d, cfg=CFG)
        return res

    def assertFails(self, d, gate_prefix=None):
        res = self.failed(d)
        self.assertFalse(res["pass"], "mutated run must not pass")
        if gate_prefix:
            self.assertTrue(any(g.startswith(gate_prefix) for g in res["failed_gates"]), (gate_prefix, res["failed_gates"]))
        return res

    def test_control_passes(self):
        self.assertTrue(self.failed(self.fresh())["pass"])

    # ---- command chain
    def test_dropped_downstream_message(self):
        d = self.fresh(); save(d, "raw/bag_commands.json", []); self.assertFails(d, "chain_downstream")

    def test_extra_downstream_message(self):
        d = self.fresh(); x = load(d, "raw/bag_commands.json"); save(d, "raw/bag_commands.json", x + x); self.assertFails(d, "chain_downstream")

    def test_dropped_upstream_message(self):
        d = self.fresh(); save(d, "raw/bag_commands_in.json", []); self.assertFails(d, "chain_upstream")

    def test_upstream_message_in_bypass(self):
        d = self.fresh(mode="bypass", tau_ms=0); save(d, "raw/bag_commands_in.json", load(d, "raw/bag_commands.json")); self.assertFails(d, "chain_upstream")

    def test_downstream_field_mutations(self):
        def m_stamp(r): r["message"]["header"]["stamp"][1] = 1
        def m_vel(r): r["message"]["points"][1]["velocities"][0] = 1e-9
        def m_pos(r): r["message"]["points"][0]["positions"][2] += 1e-12
        def m_tfs(r): r["message"]["points"][1]["time_from_start"][1] += 1
        def m_names(r): r["message"]["joint_names"].reverse()
        def m_acc(r): r["message"]["points"][1]["accelerations"] = [0.0] * 6
        def m_frame(r): r["message"]["header"]["frame_id"] = "x"
        for f in (m_stamp, m_vel, m_pos, m_tfs, m_names, m_acc, m_frame):
            d = self.fresh()
            x = load(d, "raw/bag_commands.json"); f(x[0]); save(d, "raw/bag_commands.json", x)
            self.assertFails(d, "chain_downstream_matches")

    def test_upstream_field_mutation(self):
        d = self.fresh(); x = load(d, "raw/bag_commands_in.json"); x[0]["message"]["points"][1]["positions"][0] += 1e-9; save(d, "raw/bag_commands_in.json", x)
        self.assertFails(d, "chain_upstream_matches")

    def test_header_seq_changed_by_proxy(self):
        d = self.fresh(); x = load(d, "raw/bag_commands.json"); x[0]["seq"] += 1; save(d, "raw/bag_commands.json", x); self.assertFails(d, "chain_header_seq")

    def test_sender_hash_wrong(self):
        d = self.fresh(); c = load(d, "commands.json"); c["commands"][0]["payload_sha256"] = "0" * 64; save(d, "commands.json", c); self.assertFails(d, "chain_sender_hash")

    # ---- proxy events
    def edit_events(self, d, f, file_too=True):
        ev = load(d, "raw/bag_events.json")
        f(ev)
        save(d, "raw/bag_events.json", ev)
        if file_too:
            open(os.path.join(d, "delay_events.jsonl"), "w").write("".join(json.dumps(e["event"], sort_keys=True) + "\n" for e in ev))

    def test_missing_publish_event(self):
        d = self.fresh(); self.edit_events(d, lambda ev: ev.pop(2)); self.assertFails(d, "chain_proxy")

    def test_forbidden_events(self):
        for typ in ("reject", "drop", "reset", "clock_backward", "fatal"):
            d = self.fresh()
            def f(ev, typ=typ):
                e = copy.deepcopy(ev[1]); e["event"]["type"] = typ; e["event"]["n"] = 99; ev.append(e)
            self.edit_events(d, f)
            self.assertFails(d, "chain_proxy_events_clean")

    def test_unknown_epoch_or_seq(self):
        d = self.fresh(); self.edit_events(d, lambda ev: ev[1]["event"].__setitem__("epoch", 3)); self.assertFails(d, "chain_identity")
        d = self.fresh(); self.edit_events(d, lambda ev: ev[2]["event"].__setitem__("seq", 5)); self.assertFails(d, "chain_identity")

    def test_hash_chain_broken(self):
        d = self.fresh(); self.edit_events(d, lambda ev: ev[2]["event"].__setitem__("payload_hash", "f" * 64)); self.assertFails(d, "chain_hash_chain")

    def test_due_time_wrong(self):
        d = self.fresh(); self.edit_events(d, lambda ev: ev[1]["event"].__setitem__("t_due_ns", ev[1]["event"]["t_due_ns"] - 1)); self.assertFails(d, "chain_due")

    def test_early_delivery_rejected(self):
        d = self.fresh(eps_ns=-500_000); self.assertFails(d, "chain_no_early_delivery")

    def test_lateness_over_8ms_rejected_but_8ms_allowed(self):
        d = self.fresh(eps_ns=EPS_MAX + 1); self.assertFails(d, "chain_eps_within")
        d = self.fresh(eps_ns=EPS_MAX)
        self.assertTrue(self.failed(d)["pass"])

    def test_event_arithmetic_inconsistent(self):
        d = self.fresh(); self.edit_events(d, lambda ev: ev[2]["event"].__setitem__("eps_ns", 123)); self.assertFails(d, "chain_event_arithmetic")

    def test_events_file_differs_from_bag(self):
        d = self.fresh(); open(os.path.join(d, "delay_events.jsonl"), "a").write(json.dumps({"n": 77, "type": "ready"}) + "\n"); self.assertFails(d, "chain_events_file")
        d = self.fresh(); os.remove(os.path.join(d, "delay_events.jsonl")); self.assertFails(d, "chain_events_file")

    def test_events_from_another_run(self):
        d = self.fresh(); self.edit_events(d, lambda ev: [e["event"].__setitem__("run_id", "other") for e in ev]); self.assertFails(d, "chain_proxy_run_id")

    def test_proxy_node_exit_reports_failure(self):
        d = self.fresh(); self.edit_events(d, lambda ev: ev[-1]["event"].__setitem__("failed", "boom")); self.assertFails(d, "chain_proxy_exit")

    def test_bypass_with_proxy_events(self):
        d = self.fresh(mode="bypass", tau_ms=0)
        save(d, "raw/bag_events.json", [{"t_bag": 1.0, "event": {"type": "ready", "n": 1}}]); self.assertFails(d, "chain_no_proxy")

    def test_hold_with_a_command_or_enqueue(self):
        d = self.fresh(case="H", mode="bypass", tau_ms=0)
        m = L.command_record(fake_msg([([0.0] * 6, [0.0] * 6, [], [], (0, 0)), ([0.1] * 6, [0.0] * 6, [], [], (3, 0))]))
        save(d, "raw/bag_commands.json", [{"t_bag": 11.0, "seq": 1, "message": m}]); self.assertFails(d, "chain_downstream_count")
        d = self.fresh(case="H", mode="queue", tau_ms=0)
        self.edit_events(d, lambda ev: ev.insert(1, {"t_bag": 1.0, "event": dict(ev[0]["event"], type="enqueue", n=50)}))
        self.assertFails(d, "chain_proxy_event_counts")

    # ---- timing relations and data quality
    def test_desired_moving_before_delivery(self):
        d = self.fresh(tau_ms=160, t_ref_after_pub_s=-0.100)     # desired starts 100 ms before the proxy published
        self.assertFails(d, "t_ref_not_before_delivery")

    def test_clock_backward(self):
        d = self.fresh()
        a = np.loadtxt(os.path.join(d, "raw/clock.csv"), delimiter=",", skiprows=1); a[500, 0] -= 0.01
        write_csv(os.path.join(d, "raw/clock.csv"), ["t", "t_bag"], a); self.assertFails(d, "clock_monotonic")

    def test_gap_in_execution_window_fails_not_filled(self):
        d = self.fresh(tau_ms=160)
        a = np.loadtxt(os.path.join(d, "raw/controller_state.csv"), delimiter=",", skiprows=1)
        hdr = open(os.path.join(d, "raw/controller_state.csv")).readline().strip().split(",")
        keep = ~((a[:, 0] > 10.1) & (a[:, 0] < 10.3))
        write_csv(os.path.join(d, "raw/controller_state.csv"), hdr, a[keep]); self.assertFails(d, "quality_exec_full")

    def test_short_recording_misses_the_delayed_settle_window(self):
        d = self.fresh(tau_ms=160)
        c = load(d, "commands.json"); c["rec_t1"] -= 1.5; save(d, "commands.json", c)       # recording ends before tau + T + settle (tail margin is 1 s): window must NOT be silently truncated
        res = self.assertFails(d)
        self.assertIn("window_inside_recording", res["failed_gates"])

    def test_duplicates_over_limit(self):
        d = self.fresh()
        hdr = open(os.path.join(d, "raw/controller_state.csv")).readline().strip().split(",")
        a = np.loadtxt(os.path.join(d, "raw/controller_state.csv"), delimiter=",", skiprows=1)
        dup = np.repeat(a, 2, axis=0)                          # every sample twice
        write_csv(os.path.join(d, "raw/controller_state.csv"), hdr, dup); self.assertFails(d, "quality_")

    def test_actual_backfilled_from_reference(self):
        d = self.fresh(perfect_servo=True); res = self.assertFails(d, "actual_not_backfilled")

    def test_bad_quaternions_incl_unpaired_overflow_row(self):
        for mutate in ("zero", "nan", "overflow_unpaired"):
            d = self.fresh()
            hdr = open(os.path.join(d, "raw/link_truth.csv")).readline().strip().split(",")
            a = np.loadtxt(os.path.join(d, "raw/link_truth.csv"), delimiter=",", skiprows=1)
            if mutate == "zero":
                a[100, 4:8] = 0.0
            elif mutate == "nan":
                a[100, 12] = np.nan
            else:
                # a row inside the window that no controller sample pairs with (twice-spaced stream: insert between samples)
                extra = a[100].copy(); extra[0] = a[100, 0] + 0.0045; extra[4:8] = [1e308, 1e308, 0, 0]
                a = np.insert(a, 101, extra, axis=0)
            if mutate == "nan":
                with self.assertRaises(L.InvalidInput):
                    np.savetxt(os.path.join(d, "raw/link_truth.csv"), a, delimiter=",", header=",".join(hdr), comments="", fmt="%.17g")
                    A2.analyze_run(d, cfg=CFG)
            else:
                write_csv(os.path.join(d, "raw/link_truth.csv"), hdr, a); self.assertFails(d, "gazebo_truth")

    def test_zero_base_quaternion(self):
        d = self.fresh(); c = load(d, "commands.json"); c["base_pose_end"] = [0, 0, 0, 0, 0, 0, 0]; save(d, "commands.json", c); self.assertFails(d, "base_fixed")

    def test_aborted_collector(self):
        d = self.fresh(); c = load(d, "commands.json"); c["aborted"] = "x"; save(d, "commands.json", c); self.assertFails(d, "run_not_aborted")

    def test_missing_input_is_invalid_not_pass(self):
        d = self.fresh(); os.remove(os.path.join(d, "raw/bag_events.json"))
        with self.assertRaises((L.InvalidInput, OSError)):
            A2.analyze_run(d, cfg=CFG)


class FrozenContract(unittest.TestCase):
    """T2-A02: the OFFLINE analysis must itself reject runs that do not belong to the frozen protocol, even when the recorded sender message, downstream /
    upstream bag messages and proxy events form a fully self-consistent chain (so no chain/hash gate can notice). Includes the two private counterexamples of
    the task2.5 audit (non-zero header with a consistent chain; unfrozen 40 ms) and their relatives. Synthetic inputs, not physical measurements."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="t2contract-")
        self.n = 0

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def fresh(self, **kw):
        self.n += 1
        return make_run(os.path.join(self.tmp, "r%d" % self.n), **kw)

    def consistent_message_change(self, d, fn, update_records=True):
        """Apply fn(message_record) to the sent, downstream and upstream messages and repair every hash/record field so the chain stays self-consistent."""
        cmd = load(d, "commands.json")
        c0 = cmd["commands"][0]
        fn(c0["message"])
        h = Q.payload_hash(c0["message"])
        c0["payload_sha256"] = h
        if update_records:
            pts = c0["message"]["points"]
            if len(pts) >= 2:
                c0["q_target"] = list(pts[1]["positions"])
                c0["dq"] = [b - a for a, b in zip(pts[0]["positions"], pts[1]["positions"])]
                c0["duration_s"] = pts[1]["time_from_start"][0] + pts[1]["time_from_start"][1] * 1e-9
        save(d, "commands.json", cmd)
        for name in ("raw/bag_commands.json", "raw/bag_commands_in.json"):
            v = load(d, name)
            for item in v:
                item["message"] = json.loads(json.dumps(c0["message"]))
            save(d, name, v)
        ev = load(d, "raw/bag_events.json")
        for e in ev:
            if "payload_hash" in e["event"]:
                e["event"]["payload_hash"] = h
        save(d, "raw/bag_events.json", ev)
        if os.path.exists(os.path.join(d, "delay_events.jsonl")):
            open(os.path.join(d, "delay_events.jsonl"), "w").write("".join(json.dumps(e["event"], sort_keys=True) + "\n" for e in ev))

    def verdict(self, d):
        return A2.analyze_run(d, cfg=CFG)

    def assertRejected(self, d, gate):
        res = self.verdict(d)
        self.assertFalse(res["pass"], "run outside the frozen contract must not pass")
        self.assertIn(gate, res["failed_gates"])
        # no OTHER integrity gate is what stopped it: the chain itself is self-consistent
        self.assertFalse([g for g in res["failed_gates"] if g.startswith("chain_")], res["failed_gates"])
        return res

    def test_normal_inputs_still_pass_and_all_contract_gates_exist(self):
        for case, mode, tau in (("M3", "queue", 80), ("M6", "queue", 160), ("MR3", "bypass", 0), ("M3", "queue", 0), ("H", "queue", 80), ("H", "bypass", 0)):
            res = self.verdict(self.fresh(case=case, mode=mode, tau_ms=tau))
            self.assertTrue(res["pass"], (case, mode, tau, res["failed_gates"]))
            self.assertTrue(res["gates"]["contract_condition_frozen"] and res["gates"]["contract_case_frozen"])
        res = self.verdict(self.fresh())
        self.assertTrue(res["gates"]["contract_message_supported"] and res["gates"]["contract_case_displacement_duration"])

    def test_audit_counterexample_nonzero_header_with_consistent_chain(self):
        d = self.fresh()
        self.consistent_message_change(d, lambda m: m["header"].__setitem__("stamp", [17, 1]))
        res = self.assertRejected(d, "contract_message_supported")
        self.assertTrue(any("header.stamp" in r for r in res["invalid_reasons"]))

    def test_audit_counterexample_unfrozen_delay_40ms(self):
        res = self.verdict(self.fresh(tau_ms=40))
        self.assertFalse(res["pass"])
        self.assertIn("contract_condition_frozen", res["failed_gates"])
        self.assertTrue(any("not one of the frozen conditions" in r for r in res["invalid_reasons"]))

    def test_other_unfrozen_conditions(self):
        for kw in ({"mode": "bypass", "tau_ms": 80}, {"mode": "queue", "tau_ms": 120}, {"mode": "queue", "tau_ms": 320}):
            res = self.verdict(self.fresh(**kw))
            self.assertFalse(res["pass"], kw)
            self.assertIn("contract_condition_frozen", res["failed_gates"], kw)
        d = self.fresh(tau_ms=80)                                   # delay_ms and tau_ns disagree
        c = load(d, "commands.json"); c["delay_ms"] = 160.0; save(d, "commands.json", c)
        self.assertIn("contract_condition_frozen", self.verdict(d)["failed_gates"])
        d = self.fresh(tau_ms=80)                                   # proxy ran with another delay than the condition says (self-consistent due arithmetic)
        ev = load(d, "raw/bag_events.json")
        for e in ev:
            if "delay_ns" in e["event"]:
                e["event"]["delay_ns"] = 40_000_000
        save(d, "raw/bag_events.json", ev)
        open(os.path.join(d, "delay_events.jsonl"), "w").write("".join(json.dumps(e["event"], sort_keys=True) + "\n" for e in ev))
        self.assertFalse(self.verdict(d)["pass"])

    def test_unknown_case_and_case_command_presence(self):
        d = self.fresh()
        c = load(d, "commands.json"); c["case"] = "P+"; save(d, "commands.json", c)     # a Task1 case, not an exp2.1 case
        res = self.verdict(d)
        self.assertFalse(res["pass"]); self.assertIn("contract_case_frozen", res["failed_gates"])
        d = self.fresh(case="H", mode="bypass", tau_ms=0)
        c = load(d, "commands.json"); c["case"] = "M3"; save(d, "commands.json", c)       # M3 requires one command, none recorded
        self.assertIn("contract_case_command_presence", self.verdict(d)["failed_gates"])

    def test_unsupported_messages_with_consistent_chain(self):
        def stamp(m): m["header"]["stamp"] = [0, 5]
        def frame(m): m["header"]["frame_id"] = "world"
        def order(m): m["joint_names"] = list(reversed(m["joint_names"]))
        def vel(m): m["points"][1]["velocities"][0] = 0.01
        def acc(m): m["points"][1]["accelerations"] = [0.0] * 6
        def three(m): m["points"].append(json.loads(json.dumps(m["points"][1])))
        def first_t(m): m["points"][0]["time_from_start"] = [0, 1000]
        def fast(m): m["points"][1]["time_from_start"] = [0, 200_000_000]
        for f in (stamp, frame, order, vel, acc, three, first_t, fast):
            d = self.fresh()
            self.consistent_message_change(d, f)
            self.assertRejected(d, "contract_message_supported")

    def test_wrong_displacement_duration_or_start_pose_with_consistent_chain(self):
        def dq(m):
            for i in range(6):
                m["points"][1]["positions"][i] += 0.05 if i == 0 else 0.0           # 0.05 rad more shoulder-pan displacement
        def dur(m): m["points"][1]["time_from_start"] = [4, 0]                         # 4 s instead of 3 s (still a supported message)
        def pose(m):
            for p in m["points"]:
                p["positions"][2] += 0.02                                              # start 0.02 rad away from q_init (> 0.01 margin), same displacement
        for f in (dq, dur, pose):
            d = self.fresh()
            self.consistent_message_change(d, f)
            self.assertRejected(d, "contract_case_displacement_duration")

    def test_sender_record_disagreeing_with_frozen_case(self):
        d = self.fresh()
        c = load(d, "commands.json"); c["commands"][0]["duration_s"] = 6.0; save(d, "commands.json", c)
        self.assertIn("contract_case_displacement_duration", self.verdict(d)["failed_gates"])

    def test_cli_exit_codes(self):
        import subprocess
        script = os.path.join(HERE, "..", "scripts", "analyze_task2.py")

        def rc(d):
            return subprocess.run([sys.executable, "-W", "ignore", script, "run", "--run-dir", d], capture_output=True, text=True).returncode
        self.assertEqual(rc(self.fresh()), 0)
        d = self.fresh(); self.consistent_message_change(d, lambda m: m["header"].__setitem__("stamp", [17, 1]))
        self.assertEqual(rc(d), 1)
        self.assertEqual(rc(self.fresh(tau_ms=40)), 1)


class SenderRecordFiniteness(FrozenContract):
    """T2-A04: a non-finite / mis-shaped / otherwise malformed SENDER RECORD (commands.json) must make the run invalid (CLI exit 1) before any tolerance comparison
    or joint selection happens. The task2.7 audit input (dq[0]=NaN, everything else - message, bag records, events, hashes, feedback - untouched) is reproduced
    here; before the fix it passed with exit 0 and silently lost the shoulder_pan joint in the lag analysis."""

    def record_change(self, d, fn):
        c = load(d, "commands.json")
        fn(c)
        save(d, "commands.json", c)

    def rejected_by_record_gate(self, d, what):
        res = self.verdict(d)
        self.assertFalse(res["pass"], what)
        self.assertIn("contract_sender_record_wellformed", res["failed_gates"], what)
        self.assertTrue(res["invalid_reasons"], what)
        return res

    def test_audit_nan_dq_is_invalid_and_cli_nonzero(self):
        import subprocess
        d = self.fresh()
        self.record_change(d, lambda c: c["commands"][0]["dq"].__setitem__(0, float("nan")))
        res = self.rejected_by_record_gate(d, "dq[0]=NaN")
        self.assertTrue(any("dq" in r for r in res["invalid_reasons"]))
        d2 = self.fresh()
        self.record_change(d2, lambda c: c["commands"][0]["dq"].__setitem__(0, float("nan")))
        script = os.path.join(HERE, "..", "scripts", "analyze_task2.py")
        r = subprocess.run([sys.executable, "-W", "ignore", script, "run", "--run-dir", d2], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('"pass": false', r.stdout)

    def test_non_finite_values_in_every_numeric_record_field(self):
        bad_values = [float("nan"), float("inf"), float("-inf")]
        for field in ("dq", "q_target", "q_start_observed", "q_start_minus_q_init"):
            for j in range(6):
                for v in bad_values:
                    d = self.fresh()
                    self.record_change(d, lambda c, f=field, j=j, v=v: c["commands"][0][f].__setitem__(j, v))
                    self.rejected_by_record_gate(d, "%s[%d]=%r" % (field, j, v))
        for field in ("duration_s", "sim_time_before_publish", "sim_time_after_publish"):
            for v in bad_values:
                d = self.fresh()
                self.record_change(d, lambda c, f=field, v=v: c["commands"][0].__setitem__(f, v))
                self.rejected_by_record_gate(d, "%s=%r" % (field, v))
        for key in ("rec_t0", "rec_t1", "delay_ms"):
            for v in bad_values:
                d = self.fresh()
                self.record_change(d, lambda c, k=key, v=v: c.__setitem__(k, v))
                self.rejected_by_record_gate(d, "%s=%r" % (key, v))
        for key in ("base_pose_start", "base_pose_end"):
            d = self.fresh()
            self.record_change(d, lambda c, k=key: c[k].__setitem__(3, float("nan")))
            self.rejected_by_record_gate(d, key)

    def test_wrong_shape_or_type_of_record_fields(self):
        variants = {"too short": lambda v: v[:5], "too long": lambda v: v + [0.0], "empty": lambda v: [], "scalar": lambda v: 0.3, "none": lambda v: None,
                    "string": lambda v: "abc", "nested": lambda v: [[x] for x in v], "dict": lambda v: {"a": 1}, "bool entries": lambda v: [True] * 6,
                    "string numbers": lambda v: [str(x) for x in v], "None entry": lambda v: [None] + v[1:]}
        for field in ("dq", "q_target", "q_start_observed", "q_start_minus_q_init"):
            for name, fn in variants.items():
                d = self.fresh()
                self.record_change(d, lambda c, f=field, fn=fn: c["commands"][0].__setitem__(f, fn(c["commands"][0][f])))
                self.rejected_by_record_gate(d, "%s %s" % (field, name))
            d = self.fresh()
            self.record_change(d, lambda c, f=field: c["commands"][0].pop(f))
            self.rejected_by_record_gate(d, "%s missing" % field)

    def test_bad_duration_and_time_fields(self):
        for name, v in (("zero", 0.0), ("negative", -3.0), ("string", "3.0"), ("none", None), ("bool", True), ("list", [3.0])):
            d = self.fresh()
            self.record_change(d, lambda c, v=v: c["commands"][0].__setitem__("duration_s", v))
            self.rejected_by_record_gate(d, "duration_s %s" % name)
        d = self.fresh()
        self.record_change(d, lambda c: c["commands"][0].pop("duration_s"))
        self.rejected_by_record_gate(d, "duration_s missing")
        for name, fn in (("ns float", lambda c: c["commands"][0].__setitem__("sim_time_before_publish_ns", 1.5e10)),
                         ("ns negative", lambda c: c["commands"][0].__setitem__("sim_time_before_publish_ns", -1)),
                         ("after < before", lambda c: c["commands"][0].__setitem__("sim_time_after_publish_ns", c["commands"][0]["sim_time_before_publish_ns"] - 1)),
                         ("ns bool", lambda c: c["commands"][0].__setitem__("sim_time_after_publish_ns", True)),
                         ("rec_t1 <= rec_t0", lambda c: c.__setitem__("rec_t1", c["rec_t0"])),
                         ("tau_ns float", lambda c: c.__setitem__("tau_ns", 80_000_000.0)),
                         ("tau_ns bool", lambda c: c.__setitem__("tau_ns", True)),
                         ("tau_ns negative", lambda c: c.__setitem__("tau_ns", -1)),
                         ("commands missing", lambda c: c.pop("commands")),
                         ("two commands", lambda c: c["commands"].append(json.loads(json.dumps(c["commands"][0])))),
                         ("message missing", lambda c: c["commands"][0].pop("message")),
                         ("run_id not string", lambda c: c.__setitem__("run_id", 7))):
            d = self.fresh()
            self.record_change(d, fn)
            self.rejected_by_record_gate(d, name)

    def test_finite_but_wrong_dq_still_rejected_and_never_drops_a_joint(self):
        d = self.fresh()
        self.record_change(d, lambda c: c["commands"][0]["dq"].__setitem__(0, 0.0))   # finite, but the joint would silently leave the moving set
        res = self.verdict(d)
        self.assertFalse(res["pass"])
        self.assertIn("contract_case_displacement_duration", res["failed_gates"])
        self.assertIn("moving_joints_match_frozen_case", res["failed_gates"])

    def test_normal_runs_keep_a_lag_entry_for_every_moving_joint(self):
        for case, mode, tau in (("M3", "queue", 80), ("M6", "bypass", 0), ("MR3", "queue", 160)):
            res = self.verdict(self.fresh(case=case, mode=mode, tau_ms=tau))
            self.assertTrue(res["pass"], (case, res["failed_gates"]))
            self.assertEqual(sorted(res["lag"]), sorted(J))                       # all six joints move in the frozen cases
            self.assertTrue(res["gates"]["lag_reported_for_all_moving_joints"] and res["gates"]["moving_joints_match_frozen_case"])
            for j, ent in res["lag"].items():
                for key in ("vs_nominal_actual", "vs_nominal_reference", "servo_desired_to_actual"):
                    v = ent[key]
                    self.assertTrue(v["identifiable"] or v["reason"], (j, key))    # not identifiable => the reason is recorded explicitly
        res = self.verdict(self.fresh(case="H", mode="queue", tau_ms=80))
        self.assertTrue(res["pass"])
        self.assertEqual(res["lag"], {})

    def test_task2_6_counterexamples_still_rejected(self):
        d = self.fresh()
        self.consistent_message_change(d, lambda m: m["header"].__setitem__("stamp", [17, 1]))
        self.assertRejected(d, "contract_message_supported")
        res = self.verdict(self.fresh(tau_ms=40))
        self.assertIn("contract_condition_frozen", res["failed_gates"])


class ChainUnit(unittest.TestCase):
    def test_bypass_clean(self):
        d = tempfile.mkdtemp()
        try:
            make_run(os.path.join(d, "x"), mode="bypass", tau_ms=0)
            cmd = load(os.path.join(d, "x"), "commands.json")
            res, gates = A2.check_command_chain(cmd, load(os.path.join(d, "x"), "raw/bag_commands.json"), [], [], None, "bypass", 0, EPS_MAX)
            self.assertTrue(all(gates.values()), gates)
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
