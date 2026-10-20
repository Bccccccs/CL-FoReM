#!/usr/bin/env python3
"""Evaluate a high-rate run against the declared oscillation criteria on the REQUESTED windows (task0.10).

Reads results/task0/<run>/summary.json (requested recording window, move time/duration) and
hf_joint_states.csv, and scores separate windows instead of the whole bag:

  hold mode : requested window                           -> hold criteria
  move mode : requested window                           -> hf residual criteria
              motion segment  [sent, sent+T]             -> hf residual criteria
              settle segment  [sent+T+settle, window end]-> hf residual criteria + alternation fraction
Every window needs enough consecutive-step triples (>=100 per joint) and coverage (>= 50% of the
consecutive pairs expected for that window) or it is INSUFFICIENT_EVIDENCE = FAIL.
Extra quiet samples before/after the recorded window never enter a verdict. Writes
hf_analysis_windows.json (all windows) and returns 0 iff every window passes.

Usage: evaluate_hf_windows.py --run-dir results/task0/RUN --mode hold|move [--physics-step 0.0005]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_task0_feedback as A  # noqa: E402

HF = {"vel_hf_max": 1e-4, "pos_hf_max": 1e-7}
HOLD = dict(HF, alt_frac_max=0.2, vel_rms_max=1e-4, pos_p2p_max=1e-6)
SETTLE = dict(HF, alt_frac_max=0.2)


def windows(summary, mode, settle_after_move):
    ws, we = summary["recording_window_sim_s"]
    if mode == "hold":
        return [("requested_window", ws, we, HOLD)]
    mv = summary.get("move")
    if not mv:
        raise A.InvalidInput("move mode needs a move in summary.json")
    t0, dur = mv["sim_time_sent"], mv["duration_s"]
    out = [("requested_window", ws, we, HF), ("motion", t0, t0 + dur, HF)]
    if t0 + dur + settle_after_move < we:
        out.append(("settle", t0 + dur + settle_after_move, we, SETTLE))
    else:
        raise A.InvalidInput("no settle segment fits in the requested window")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--mode", required=True, choices=["hold", "move"])
    ap.add_argument("--physics-step", type=float, default=0.0005)
    ap.add_argument("--settle-after-move", type=float, default=1.0)
    ap.add_argument("--min-coverage", type=float, default=0.5)
    ap.add_argument("--out", default=None, help="default: RUN_DIR/hf_analysis_windows.json (never overwrites older hf_analysis.json)")
    a = ap.parse_args()
    out_path = a.out or os.path.join(a.run_dir, "hf_analysis_windows.json")
    result = {"mode": a.mode, "windows": {}}
    try:
        summary = json.load(open(os.path.join(a.run_dir, "summary.json")))
        rows, names = A.load(os.path.join(a.run_dir, "hf_joint_states.csv"))
        for name, t0, t1, crit in windows(summary, a.mode, a.settle_after_move):
            res = A.analyze(rows, names, a.physics_step, 1e-4, t0, t1, a.min_coverage)
            verdict, ok = A.evaluate(res, names, crit)
            res.update({"window": [t0, t1], "criteria": crit, "verdict": verdict, "pass": ok})
            result["windows"][name] = res
        result["pass"] = all(w["pass"] for w in result["windows"].values())
        rc = 0 if result["pass"] else 1
    except (A.InvalidInput, OSError, KeyError, ValueError) as e:
        result.update({"error": str(e), "pass": False})
        rc = 2
    json.dump(result, open(out_path, "w"), indent=2)
    summ = {n: {"pass": w["pass"], "pairs": w.get("consecutive_step_pairs"), "coverage": round(w.get("coverage_of_expected_pairs", 0), 3),
                "max_vel_hf": max((j["vel_hf_residual_rms"] for j in w.get("joints", {}).values() if j.get("vel_hf_residual_rms") is not None), default=None),
                "verdicts": sorted(set(w["verdict"].values()))} for n, w in result["windows"].items()}
    print(json.dumps({"mode": a.mode, "pass": result["pass"], "error": result.get("error"), "windows": summ}, indent=1))
    sys.exit(rc)


if __name__ == "__main__":
    main()
