"""Task2.4 aggregation tests on synthetic runs (numpy + PyYAML + matplotlib optional; no ROS). Builds run directories with the generator of
test_task2_measurement.py, analyses them, writes a run index and aggregates: statistics, B/Z gates (pass and deliberate fail), non-zero servo gate,
failure listing, hf separation, refusal to overwrite."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

try:
    import numpy as np
    import yaml
except ImportError as e:
    raise unittest.SkipTest("numpy/PyYAML not available: %s" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, HERE)
import aggregate_task2 as G  # noqa: E402
import analyze_task2 as A2  # noqa: E402
from test_task2_measurement import CFG, make_run  # noqa: E402

COND = {"B": ("bypass", 0), "Z": ("queue", 0), "D80": ("queue", 80), "D160": ("queue", 160)}


class Pure(unittest.TestCase):
    def test_describe_sample_std(self):
        d = G.describe([1.0, 2.0, 4.0])
        self.assertAlmostEqual(d["std"], np.std([1, 2, 4], ddof=1))
        self.assertEqual(d["range"], 3.0)
        self.assertIsNone(G.describe([1.0])["std"])

    def test_curve_diff_known_and_nan_not_filled(self):
        a = np.zeros((100, 2)); b = a.copy(); b[:, 0] = 1e-5
        s = G.curve_diff_stats(a, b)
        self.assertAlmostEqual(s["rmse"][0], 1e-5); self.assertAlmostEqual(s["peak"][0], 1e-5); self.assertEqual(s["rmse"][1], 0.0)
        b[:50] = np.nan
        self.assertIsNone(G.curve_diff_stats(a, b))      # too many invalid samples: refuse rather than compare a fragment
        b = a.copy(); b[:5] = np.nan
        self.assertEqual(G.curve_diff_stats(a, b)["n_valid"], 95)
        self.assertIsNone(G.curve_diff_stats(np.zeros((100, 2)), np.zeros((80, 2))))

    def test_pairwise_counts(self):
        c = {k: np.zeros((50, 1)) + i * 1e-6 for i, k in enumerate("abc")}
        self.assertEqual(len(G.pairwise(c, "x")), 3)


class EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="t2agg-")
        cls.runs = []
        cls.build("good", z_amp_scale=1.0)
        cls.build("badz", z_amp_scale=100.0)
        cls.build("quant", z_amp_scale=1.0, quant=True)

    @classmethod
    def build(cls, name, z_amp_scale, quant=False):
        root = os.path.join(cls.tmp, name)
        recs = []
        for rd in (1, 2, 3):
            for cond, (mode, tau) in COND.items():
                amp = 2e-6 * (1 + 0.1 * rd) * (z_amp_scale if cond == "Z" else 1.0)
                rid = "syn-%s-M3-%s-r%d" % (name, cond, rd)
                kw = {}
                if quant:   # identical servo error, but the true start falls at a different phase of the 8 ms sample lattice in B and in Z
                    kw = {"t_ref_after_pub_s": 0.0010 if cond == "B" else 0.0070, "in_lag_ns": 0}
                d = make_run(os.path.join(root, rid), case="M3", mode=mode, tau_ms=tau, servo_amp=amp, run_id=rid, **kw)
                res = A2.analyze_run(d, cfg=CFG)
                recs.append({"run_id": rid, "case": "M3", "condition": cond, "mode": mode, "tau_ms": tau, "round": rd, "role": "formal", "attempt": 1, "valid": bool(res["pass"]),
                             "results_dir": d, "failed_gates": res["failed_gates"], "invalid_reasons": res["invalid_reasons"]})
        # one invalid attempt (kept in the failure table) and one hf run
        recs.append({"run_id": "syn-failed", "case": "M3", "condition": "D80", "mode": "queue", "tau_ms": 80, "round": 1, "role": "formal", "attempt": 1, "valid": False,
                     "results_dir": os.path.join(root, "nothing"), "failed_gates": ["x"], "invalid_reasons": ["synthetic"], "retry_of": None, "entry_exit": 1})
        idx = {"matrix_id": "syn-" + name, "freeze_id": "syn", "stage": "pilot", "runs": recs}
        p = os.path.join(root, "run_index.json")
        json.dump(idx, open(p, "w"))
        setattr(cls, name + "_index", p)
        setattr(cls, name + "_root", root)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def agg(self, name, figures=False):
        out = os.path.join(self.tmp, name + "_out_%d" % len(os.listdir(self.tmp)))
        argv = [sys.executable, os.path.join(HERE, "..", "scripts", "aggregate_task2.py"), "--index", getattr(self, name + "_index"), "--analysis-id", "syn", "--out", out,
                "--task1-curves", os.path.join(self.tmp, "none")] + ([] if figures else ["--no-figures"])
        r = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return out

    def test_good_gates_and_statistics(self):
        out = self.agg("good")
        s = json.load(open(os.path.join(out, "summary.json")))
        self.assertEqual((s["n_valid_125hz"], s["n_invalid_attempts"]), (12, 1))
        eqj = json.load(open(os.path.join(out, "equivalence_bz.json")))
        self.assertEqual(set(eqj), {"protocol_v1_t_ref", "protocol_v1_1_fit", "alignment_explanation", "labels"})
        self.assertTrue(s["gates"]["equivalence_bz_protocol_v1_1_fit"], eqj["protocol_v1_1_fit"]["cases"]["M3"]["curves"])
        self.assertIn("equivalence_bz_protocol_v1_t_ref", s["gates"])           # both verdicts are always present and separately labelled
        self.assertTrue(s["gates"]["nonzero_servo"])
        g = json.load(open(os.path.join(out, "groups.json")))
        self.assertEqual(g["M3|D80"]["n_runs"], 3)
        e = g["M3|D80"]["exec_nom_e_total_rmse"]
        self.assertEqual(len(e["std"]), 6)
        self.assertGreater(min(e["mean"]), 1e-3)             # the 80 ms shift is far above the servo noise
        f = json.load(open(os.path.join(out, "failures.json")))
        self.assertEqual([x["run_id"] for x in f], ["syn-failed"])
        d = json.load(open(os.path.join(out, "dose.json")))["M3"]
        self.assertGreater(d["D160"]["pos_rmse_ratio_vs_B"], d["D80"]["pos_rmse_ratio_vs_B"])     # more delay, more original-axis error (synthetic, by construction)
        self.assertTrue(os.path.exists(os.path.join(out, "summary.md")))

    def test_bz_gate_fails_when_zero_delay_proxy_changes_the_servo(self):
        out = self.agg("badz")
        eq = json.load(open(os.path.join(out, "equivalence_bz.json")))
        for key in ("protocol_v1_t_ref", "protocol_v1_1_fit"):
            self.assertFalse(eq[key]["pass"], key)
            self.assertFalse(eq[key]["cases"]["M3"]["curves"]["e_servo"]["pass"], key)

    def test_t_ref_alignment_fails_but_fit_alignment_passes_when_samples_quantise_differently(self):
        out = self.agg("quant")
        eq = json.load(open(os.path.join(out, "equivalence_bz.json")))
        tref, fit = eq["protocol_v1_t_ref"]["cases"]["M3"], eq["protocol_v1_1_fit"]["cases"]["M3"]
        self.assertFalse(tref["curves"]["q_actual"]["pass"])          # the v1 verdict is NOT turned into a pass
        self.assertTrue(fit["curves"]["q_actual"]["pass"], fit["curves"]["q_actual"])
        self.assertGreater(tref["curves"]["q_actual"]["matched_max_rmse"], 1e-5)
        self.assertLess(fit["curves"]["q_actual"]["matched_max_rmse"], 1e-5)
        # the quantisation model explains the t_ref-aligned difference (observed ~ predicted)
        ex = eq["alignment_explanation"]
        self.assertGreater(ex["observed_over_predicted_min"], 0.7)
        self.assertLess(ex["observed_over_predicted_max"], 1.4)
        s = json.load(open(os.path.join(out, "summary.json")))
        self.assertFalse(s["gates"]["equivalence_bz_protocol_v1_t_ref"])
        self.assertTrue(s["gates"]["equivalence_bz_protocol_v1_1_fit"])

    def test_overwrite_refused_and_figures(self):
        out = self.agg("good", figures=True)
        self.assertTrue(os.path.exists(os.path.join(out, "figures", "dose_ee_total.png")) or os.path.exists(os.path.join(out, "figures_error.txt")))
        r = subprocess.run([sys.executable, os.path.join(HERE, "..", "scripts", "aggregate_task2.py"), "--index", self.good_index, "--analysis-id", "x", "--out", out], capture_output=True, text=True)
        self.assertEqual(r.returncode, 12)


if __name__ == "__main__":
    unittest.main()
