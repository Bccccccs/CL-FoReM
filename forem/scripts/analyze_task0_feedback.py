#!/usr/bin/env python3
"""High-rate feedback analysis for task0 (stdlib only; host or container).

Input: joint_states CSV (t,pos_*,vel_*,eff_*) - e.g. hf_joint_states.csv from bag_to_csv.py -
plus the physics step. Only sample pairs whose dt equals ONE physics step (within tolerance)
are used for step-to-step statistics; pairs across dropped samples are never treated as
consecutive steps. Nothing is filtered, resampled or removed.

Per joint: position peak-to-peak, velocity/effort min/max/RMS, fraction of consecutive-step
pairs whose velocities have opposite sign (both |v| > --vel-eps), median |v|, and the residual
between the reported velocity and the finite difference of position over the same step.
"period-2 alternation" = high opposite-sign fraction together with |v| above the noise floor.

Also reports the high-frequency residual x_i - (x_{i-1}+x_{i+1})/2 on consecutive triples
(pos_hf_residual_rms, vel_hf_residual_rms): ~0 for smooth motion, 2A for a period-2 alternation
of amplitude A - so it detects the alternation even while the joint is moving.

Optional verdict (only when thresholds are given): a joint FAILS if alternation fraction >
--alt-frac-max, velocity RMS > --vel-rms-max, position p2p > --pos-p2p-max, vel_hf_residual_rms >
--vel-hf-max or pos_hf_residual_rms > --pos-hf-max (missing evidence counts as failure for hf).
Usage: analyze_task0_feedback.py --joint-states CSV --out JSON [--physics-step 0.0005] [--t-min T] [--t-max T]
"""
import argparse
import csv
import json
import math
import sys

MIN_PAIRS = 100
MIN_TRIPLES = 100   # declared in task0.7 RESULTS: fewer consecutive-step triples per joint = evidence insufficient = FAIL
JOINTS = ["ur5_shoulder_pan_joint", "ur5_shoulder_lift_joint", "ur5_elbow_joint",
          "ur5_wrist_1_joint", "ur5_wrist_2_joint", "ur5_wrist_3_joint"]


class InvalidInput(Exception):
    """Input cannot be analysed at all (empty, missing columns, non-finite or non-increasing time/values)."""


def rms(xs):
    return math.sqrt(sum(x * x for x in xs) / len(xs)) if xs else None


def median(xs):
    s = sorted(xs)
    n = len(s)
    return None if not n else (s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2]))


def analyze(rows, names, step, vel_eps, t_min=None, t_max=None, min_coverage=0.5):
    rows = [r for r in rows if (t_min is None or r["t"] >= t_min) and (t_max is None or r["t"] <= t_max)]
    out = {"n_samples": len(rows), "physics_step_s": step}
    if len(rows) < 3:
        out["insufficient_evidence"] = "fewer than 3 samples"
        return out
    ts = [r["t"] for r in rows]
    dts = [b - a for a, b in zip(ts, ts[1:])]
    tol = step * 0.02
    consec = [i for i, d in enumerate(dts) if abs(d - step) <= tol]
    win = (t_max - t_min) if (t_min is not None and t_max is not None) else (ts[-1] - ts[0])
    expected_pairs = win / step if win > 0 else 0
    out["window_s"] = win
    out["expected_consecutive_pairs"] = expected_pairs
    out["coverage_of_expected_pairs"] = (len(consec) / expected_pairs) if expected_pairs else 0.0
    out.update({
        "span_s": ts[-1] - ts[0], "mean_hz": (len(ts) - 1) / (ts[-1] - ts[0]) if ts[-1] > ts[0] else None,
        "dt_min": min(dts), "dt_max": max(dts), "non_increasing_dt_count": sum(1 for d in dts if d <= 0),
        "consecutive_step_pairs": len(consec), "gaps_gt_1p5_step": sum(1 for d in dts if d > 1.5 * step),
        "fraction_pairs_consecutive": len(consec) / len(dts),
    })
    joints = {}
    for n in names:
        q = [r["pos_" + n] for r in rows]; v = [r["vel_" + n] for r in rows]; e = [r["eff_" + n] for r in rows]
        j = {"pos_peak_to_peak": max(q) - min(q), "vel_min": min(v), "vel_max": max(v), "vel_rms": rms(v),
             "eff_min": min(e), "eff_max": max(e), "eff_rms": rms(e), "eff_median": median(e)}
        flips = tot = 0
        resid = []
        for i in consec:
            v0, v1 = v[i], v[i + 1]
            if abs(v0) > vel_eps and abs(v1) > vel_eps:
                tot += 1
                flips += (v0 > 0) != (v1 > 0)
            resid.append(abs((q[i + 1] - q[i]) / step - v[i + 1]))
        # high-frequency residual on consecutive triples (dt == one step on both sides):
        # x_i - (x_{i-1}+x_{i+1})/2. ~0 for smooth motion, = 2A for a period-2 alternation of amplitude A.
        rq, rv = [], []
        cset = set(consec)
        for i in range(1, len(rows) - 1):
            if (i - 1) in cset and i in cset:
                rq.append(q[i] - 0.5 * (q[i - 1] + q[i + 1]))
                rv.append(v[i] - 0.5 * (v[i - 1] + v[i + 1]))
        j["triples"] = len(rq)
        j["pos_hf_residual_rms"] = rms(rq)
        j["vel_hf_residual_rms"] = rms(rv)
        j["pairs_above_noise"] = tot
        j["alternation_fraction"] = (flips / tot) if tot else None
        j["median_abs_vel"] = median([abs(x) for x in v])
        j["vel_minus_position_derivative_median_abs"] = median(resid)
        j["vel_minus_position_derivative_max_abs"] = max(resid) if resid else None
        why = []
        if len(consec) < MIN_PAIRS:
            why.append("only %d consecutive-step pairs (<%d)" % (len(consec), MIN_PAIRS))
        if len(rq) < MIN_TRIPLES:
            why.append("only %d consecutive-step triples (<%d)" % (len(rq), MIN_TRIPLES))
        if out["coverage_of_expected_pairs"] < min_coverage:
            why.append("consecutive pairs cover %.2f of the window (<%.2f)" % (out["coverage_of_expected_pairs"], min_coverage))
        if why:
            j["insufficient_evidence"] = "; ".join(why)
        joints[n] = j
    out["joints"] = joints
    return out


def evaluate(res, names, crit):
    """Apply declared criteria to an analyze() result. NaN/None/insufficient evidence never pass."""
    verdict = {}
    for n in names:
        jn = res.get("joints", {}).get(n)
        if jn is None or "insufficient_evidence" in jn:
            verdict[n] = "INSUFFICIENT_EVIDENCE"
            continue
        bad = []

        def over(val, limit):
            return val is None or not (val <= limit)
        if crit.get("alt_frac_max") is not None and jn["alternation_fraction"] is not None and over(jn["alternation_fraction"], crit["alt_frac_max"]):
            bad.append("alternation")
        if crit.get("vel_rms_max") is not None and over(jn["vel_rms"], crit["vel_rms_max"]):
            bad.append("vel_rms")
        if crit.get("pos_p2p_max") is not None and over(jn["pos_peak_to_peak"], crit["pos_p2p_max"]):
            bad.append("pos_p2p")
        if crit.get("vel_hf_max") is not None and over(jn["vel_hf_residual_rms"], crit["vel_hf_max"]):
            bad.append("vel_hf")
        if crit.get("pos_hf_max") is not None and over(jn["pos_hf_residual_rms"], crit["pos_hf_max"]):
            bad.append("pos_hf")
        verdict[n] = "FAIL:" + ",".join(bad) if bad else "PASS"
    ok = ("insufficient_evidence" not in res) and len(verdict) == len(JOINTS) and all(v == "PASS" for v in verdict.values())
    return verdict, ok


def load(path):
    """Read and VALIDATE a joint_states CSV. Raises InvalidInput on anything that would make a verdict meaningless."""
    try:
        with open(path) as f:
            rd = csv.DictReader(f)
            fields = rd.fieldnames or []
            raw = list(rd)
    except OSError as e:
        raise InvalidInput("cannot read %s: %s" % (path, e))
    missing = [c for c in ["t"] + [pre + n for n in JOINTS for pre in ("pos_", "vel_", "eff_")] if c not in fields]
    if missing:
        raise InvalidInput("missing columns (all six joints need pos_/vel_/eff_): %s" % missing[:6])
    if not raw:
        raise InvalidInput("no data rows")
    rows = []
    for k, r in enumerate(raw):
        try:
            row = {c: float(r[c]) for c in fields}
        except (TypeError, ValueError):
            raise InvalidInput("row %d has a non-numeric or missing value" % (k + 2))
        bad = [c for c, v in row.items() if not math.isfinite(v)]
        if bad:
            raise InvalidInput("row %d has non-finite values in %s" % (k + 2, bad[:4]))
        rows.append(row)
    ts = [r["t"] for r in rows]
    if any(b <= a for a, b in zip(ts, ts[1:])):
        raise InvalidInput("time column is not strictly increasing")
    return rows, list(JOINTS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--joint-states", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--physics-step", type=float, default=0.0005)
    ap.add_argument("--vel-eps", type=float, default=1e-4, help="rad/s; velocity noise floor for sign statistics")
    ap.add_argument("--t-min", type=float, default=None)
    ap.add_argument("--t-max", type=float, default=None)
    ap.add_argument("--alt-frac-max", type=float, default=None)
    ap.add_argument("--vel-rms-max", type=float, default=None)
    ap.add_argument("--pos-p2p-max", type=float, default=None)
    ap.add_argument("--vel-hf-max", type=float, default=None, help="max vel_hf_residual_rms (rad/s)")
    ap.add_argument("--pos-hf-max", type=float, default=None, help="max pos_hf_residual_rms (rad)")
    ap.add_argument("--min-coverage", type=float, default=0.5, help="required fraction of the window's expected consecutive-step pairs")
    a = ap.parse_args()
    criteria_given = any(x is not None for x in (a.alt_frac_max, a.vel_rms_max, a.pos_p2p_max, a.vel_hf_max, a.pos_hf_max))
    try:
        rows, names = load(a.joint_states)
    except InvalidInput as e:
        with open(a.out, "w") as f:
            json.dump({"input": a.joint_states, "error": str(e), "pass": False, "verdict": {}}, f, indent=2)
        print("INVALID INPUT: %s" % e, file=sys.stderr)
        raise SystemExit(2)
    res = analyze(rows, names, a.physics_step, a.vel_eps, a.t_min, a.t_max, a.min_coverage)
    res["input"] = a.joint_states
    res["params"] = {"vel_eps": a.vel_eps, "t_min": a.t_min, "t_max": a.t_max}
    if criteria_given:
        crit = {"alt_frac_max": a.alt_frac_max, "vel_rms_max": a.vel_rms_max, "pos_p2p_max": a.pos_p2p_max,
                "vel_hf_max": a.vel_hf_max, "pos_hf_max": a.pos_hf_max}
        verdict, ok = evaluate(res, names, crit)
        res["criteria"] = crit
        res["verdict"] = verdict
        res["pass"] = ok
    with open(a.out, "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps({"n": res["n_samples"], "consecutive_pairs": res.get("consecutive_step_pairs"),
                      "joints": {n: {"alt": round(j["alternation_fraction"], 3) if j.get("alternation_fraction") is not None else None,
                                     "vel_rms": j["vel_rms"], "pos_p2p": j["pos_peak_to_peak"],
                                     "vel_hf": j.get("vel_hf_residual_rms"), "pos_hf": j.get("pos_hf_residual_rms")} for n, j in res.get("joints", {}).items()},
                      "verdict": res.get("verdict")}, indent=1))
    if "insufficient_evidence" in res:  # any top-level shortage of evidence is a failure, criteria or not
        print("INSUFFICIENT EVIDENCE: %s" % res["insufficient_evidence"], file=sys.stderr)
        raise SystemExit(1)
    if "pass" in res:
        raise SystemExit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
