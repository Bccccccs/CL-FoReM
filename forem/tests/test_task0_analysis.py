"""Regression tests for scripts/analyze_task0_feedback.py (task0.10, task0.9 findings).

CONSTRUCTED data only (not evidence about the simulator). Each bad input must be rejected; the reviewer's
four false-pass inputs (empty, two rows, all-NaN, 120 pairs but only 60 triples) and the window-dilution
case are reproduced here, plus a clean pass and a real alternation case so the gates are known to be able
to fail AND to pass.

Run: python3 -m unittest discover -s forem/tests -v
"""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "analyze_task0_feedback.py")
sys.path.insert(0, os.path.dirname(SCRIPT))
import analyze_task0_feedback as A  # noqa: E402

J = A.JOINTS
STEP = 0.0005
CRIT = ["--vel-hf-max", "1e-4", "--pos-hf-max", "1e-7"]
HOLD = CRIT + ["--alt-frac-max", "0.2", "--vel-rms-max", "1e-4", "--pos-p2p-max", "1e-6"]


def header(joints=J):
    return ["t"] + ["pos_" + j for j in joints] + ["vel_" + j for j in joints] + ["eff_" + j for j in joints]


def write_csv(path, times, amp_fn=lambda t, k: 0.0, joints=J, cols=None):
    """Held pose; optional period-2 alternation of amplitude amp_fn(t,k) on every joint."""
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols or header(joints))
        for k, t in enumerate(times):
            a = amp_fn(t, k) * (1 if k % 2 == 0 else -1)
            w.writerow([t] + [1.0 + a] * len(joints) + [a / STEP] * len(joints) + [0.0] * len(joints))


def uniform(n, t0=0.0):
    return [round(t0 + k * STEP, 10) for k in range(n)]


def groups_of(size, n_groups, gap=0.01):
    """Runs of `size` consecutive-step samples separated by gaps: pairs=(size-1)*groups, triples=(size-2)*groups."""
    ts, t = [], 0.0
    for _ in range(n_groups):
        for _ in range(size):
            ts.append(round(t, 10)); t += STEP
        t += gap
    return ts


class CliCase(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="t0an-")

    def run_cli(self, name, times=None, extra=(), **kw):
        path = os.path.join(self.d, name + ".csv")
        out = os.path.join(self.d, name + ".json")
        if times is not None:
            write_csv(path, times, **kw)
        r = subprocess.run([sys.executable, SCRIPT, "--joint-states", path, "--out", out] + list(extra), capture_output=True, text=True)
        res = json.load(open(out)) if os.path.exists(out) else None
        return r, res


class BadInputsAreRejected(CliCase):
    def test_header_only_csv(self):
        path = os.path.join(self.d, "e.csv")
        open(path, "w").write(",".join(header()) + "\n")
        out = os.path.join(self.d, "e.json")
        r = subprocess.run([sys.executable, SCRIPT, "--joint-states", path, "--out", out] + HOLD, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertFalse(json.load(open(out))["pass"])

    def test_two_rows(self):
        r, res = self.run_cli("two", uniform(2), HOLD)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("insufficient_evidence", res)
        self.assertFalse(res.get("pass", False))

    def test_all_nan_rows(self):
        path = os.path.join(self.d, "nan.csv"); out = os.path.join(self.d, "nan.json")
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(header())
            for t in uniform(110):
                w.writerow([t] + ["nan"] * 18)
        r = subprocess.run([sys.executable, SCRIPT, "--joint-states", path, "--out", out] + HOLD, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertFalse(json.load(open(out))["pass"])

    def test_120_pairs_but_only_60_triples(self):
        ts = groups_of(3, 60)  # 2 pairs + 1 triple per group -> 120 pairs, 60 triples
        r, res = self.run_cli("t60", ts, HOLD)
        self.assertEqual(res["consecutive_step_pairs"], 120)
        self.assertEqual(min(j["triples"] for j in res["joints"].values()), 60)
        self.assertNotEqual(r.returncode, 0, "60 triples must not pass (declared gate: >=100)")
        self.assertFalse(res["pass"])
        self.assertEqual(set(res["verdict"].values()), {"INSUFFICIENT_EVIDENCE"})

    def test_missing_joint_columns(self):
        r, res = self.run_cli("miss", uniform(500), HOLD, joints=J[:3])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertFalse(res["pass"])

    def test_non_increasing_time(self):
        ts = uniform(500); ts[100] = ts[99]
        r, res = self.run_cli("dup", ts, HOLD)
        self.assertEqual(r.returncode, 2)

    def test_too_little_of_the_window_covered(self):
        # 400 samples in isolated pairs -> few consecutive pairs relative to a 3 s window
        ts = groups_of(4, 100)[:400]
        r, res = self.run_cli("cov", ts, ["--t-min", "0", "--t-max", "3"] + HOLD)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(res["pass"])

    def test_real_alternation_is_failed_in_hold_and_in_move_style_criteria(self):
        ts = uniform(6000)
        r, res = self.run_cli("alt", ts, HOLD, amp_fn=lambda t, k: 2e-6)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(all(v.startswith("FAIL") for v in res["verdict"].values()))
        r, res = self.run_cli("alt2", ts, CRIT, amp_fn=lambda t, k: 2e-6)
        self.assertEqual(r.returncode, 1)


class GoodInputPasses(CliCase):
    def test_quiet_hold_passes(self):
        r, res = self.run_cli("ok", uniform(6000), HOLD, amp_fn=lambda t, k: 1e-13)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(res["pass"])
        self.assertEqual(set(res["verdict"].values()), {"PASS"})


class WindowDilution(unittest.TestCase):
    """Reviewer's finding: a short bad segment is diluted by a long quiet bag when the whole bag is scored."""

    def test_short_alternation_is_hidden_in_whole_bag_but_caught_in_its_window(self):
        rows = []
        for k, t in enumerate(uniform(26001)):  # 13 s
            a = (2e-4 * STEP if (4.9 <= t < 5.2) else 0.0) * (1 if k % 2 == 0 else -1)  # +-2e-4 rad/s velocity alternation
            r = {"t": t}
            for j in J:
                r["pos_" + j] = 1.0 + a; r["vel_" + j] = a / STEP; r["eff_" + j] = 0.0
            rows.append(r)
        whole = A.analyze(rows, J, STEP, 1e-4)
        seg = A.analyze(rows, J, STEP, 1e-4, t_min=4.7685, t_max=7.7685)
        w = max(j["vel_hf_residual_rms"] for j in whole["joints"].values())
        s = max(j["vel_hf_residual_rms"] for j in seg["joints"].values())
        self.assertLess(w, 1e-4, "whole-bag RMS should be diluted below the threshold")
        self.assertGreater(s, 1e-4, "the 3 s window must expose it")


if __name__ == "__main__":
    unittest.main()
