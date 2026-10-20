#!/usr/bin/env python3
"""Independent hand-recomputation of stored Task1 metrics (stdlib only: csv/json/math - shares NO code with task1_lib/analyze_task1).

For sampled (run, window, joint) triples it re-reads raw/controller_state.csv, re-derives t_ref and the window, recomputes
e_q = actual - desired RMSE / max|e| / mean and compares with run_metrics.json. Exit 0 iff all sampled values agree
(abs 1e-10 or rel 1e-6 whichever is looser); prints each comparison. Usage:
  verify_task1_metrics.py --index results/task1/<matrix>/run_index.json [--samples 60] [--seed 1]
"""
import argparse
import csv
import json
import math
import os
import random
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
JN = ["ur5_shoulder_pan_joint", "ur5_shoulder_lift_joint", "ur5_elbow_joint", "ur5_wrist_1_joint", "ur5_wrist_2_joint", "ur5_wrist_3_joint"]
TOL_ABS, TOL_REL = 1e-10, 1e-6


def read_state(path):
    with open(path) as f:
        r = csv.reader(f)
        h = next(r)
        ix = {n: i for i, n in enumerate(h)}
        rows = [[float(x) for x in row] for row in r]
    return ix, rows


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--samples", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    idx = json.load(open(a.index))
    runs = [r for r in idx["runs"] if r["valid"] and r["role"] == "formal"]
    rnd = random.Random(a.seed)
    bad = n = 0
    cache = {}
    for _ in range(a.samples):
        r = rnd.choice(runs)
        d = os.path.join(ROOT, r["results_dir"])
        if d not in cache:
            ix, rows = read_state(os.path.join(d, "raw", "controller_state.csv"))
            cache[d] = (ix, rows, json.load(open(os.path.join(d, "commands.json"))), json.load(open(os.path.join(d, "run_metrics.json"))))
        ix, rows, cmd, met = cache[d]
        # independent t_ref (moving runs): desired leaves the 1 s median before the pre-hold end by > 1e-6 rad
        if cmd["commands"]:
            c0 = cmd["commands"][0]
            pre_end = cmd["rec_t0"] + cmd["pre_hold_s"]
            hold_ref = [median([row[ix["des_" + j]] for row in rows if pre_end - 1.0 <= row[0] <= pre_end]) for j in JN]
            hits = []
            for jn, d_ in zip(range(6), c0["dq"]):
                if abs(d_) > 0:
                    t_hit = next((row[0] for row in rows if row[0] >= cmd["rec_t0"] and abs(row[ix["des_" + JN[jn]]] - hold_ref[jn]) > 1e-6), None)
                    if t_hit is not None:
                        hits.append(t_hit)
            t_ref = min(hits)
            n += 1
            ok = abs(t_ref - met["t_ref"]["t_ref_s"]) < 1e-9
            bad += not ok
            if not ok:
                print("MISMATCH t_ref", r["run_id"], t_ref, met["t_ref"]["t_ref_s"])
        w = rnd.choice(list(met["metrics"]))
        j = rnd.randrange(6)
        w0, w1 = met["metrics"][w]["window"]
        seen, errs = set(), []
        for row in rows:
            if w0 <= row[0] <= w1 and row[0] not in seen:
                seen.add(row[0])
                errs.append(row[ix["act_" + JN[j]]] - row[ix["des_" + JN[j]]])
        mine = {"rmse": math.sqrt(sum(e * e for e in errs) / len(errs)), "max_abs": max(abs(e) for e in errs), "mean": sum(errs) / len(errs)}
        for k, v in mine.items():
            stored = met["metrics"][w]["e_q"][k][j]
            ok = abs(v - stored) <= max(TOL_ABS, TOL_REL * abs(stored))
            n += 1
            bad += not ok
            if not ok:
                print("MISMATCH", r["run_id"], w, JN[j], k, v, stored)
    print("verify_task1_metrics: %d comparisons, %d mismatches (seed %d)" % (n, bad, a.seed))
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
