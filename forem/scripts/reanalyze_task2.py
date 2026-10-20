#!/usr/bin/env python3
"""Re-analyse existing Task2 runs with the CURRENT analyzer into a NEW directory (runs in forem-dev; numpy, PyYAML). Never touches the original run directories.

  reanalyze_task2.py --index OLD_RUN_INDEX.json --analysis-id ID --out-root results/experiment/exp2 [--limit N]
      -> OUT_ROOT/ID/runs/<run-id>/{run_metrics.json,curves.npz}, OUT_ROOT/ID/run_index.json (same schema as the matrix index; `results_dir` points at the new
         analysis, `raw_dir` at the untouched original run, `valid_old`/`pass_old` keep the historical verdict), OUT_ROOT/ID/diff_report.json.
Validity of the new index: process_ok (collector, converter, proxy, cleanup and hf exit codes of the ORIGINAL run, from its manifest) AND the new analysis passes.
Every attempt of the old index is re-analysed (including the invalid ones: their failure is kept and their denominator stays), nothing is dropped or replaced.
diff_report: per run old/new verdict, gates that appeared/disappeared, and the maximum absolute difference of every numeric leaf present in both metrics and of every curve
array present in both (a pure analyzer-version change must reproduce the old numbers exactly; anything else is reported).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_task2 as A2  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def numeric_leaves(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(numeric_leaves(v, prefix + "/" + str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(numeric_leaves(v, prefix + "[%d]" % i))
    elif isinstance(obj, bool) or obj is None or isinstance(obj, str):
        pass
    elif isinstance(obj, (int, float)):
        out[prefix] = float(obj)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--analysis-id", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--config", default=A2.CONFIG)
    a = ap.parse_args()
    out = os.path.join(ROOT, a.out_root, a.analysis_id) if not os.path.isabs(a.out_root) else os.path.join(a.out_root, a.analysis_id)
    if os.path.exists(out):
        print("refused: %s exists (analyses are never overwritten)" % out)
        sys.exit(12)
    cfg = yaml.safe_load(open(a.config))
    old = json.load(open(a.index))
    os.makedirs(os.path.join(out, "runs"))
    new_runs, diffs = [], []
    for k, rec in enumerate(old["runs"]):
        if a.limit is not None and k >= a.limit:
            break
        # an index written by this tool (re-analysis) keeps the untouched raw run in `raw_dir` and the previous analysis in `results_dir`
        raw_dir = rec.get("raw_dir") or rec["results_dir"]
        raw_dir = raw_dir if os.path.isabs(raw_dir) else os.path.join(ROOT, raw_dir)
        old_dir = rec["results_dir"] if os.path.isabs(rec["results_dir"]) else os.path.join(ROOT, rec["results_dir"])
        man = json.load(open(os.path.join(raw_dir, "manifest.json")))
        hf = bool(man.get("hf_diagnostic"))
        o_metrics = json.load(open(os.path.join(old_dir, "run_metrics.json")))
        new_dir = os.path.join(out, "runs", rec["run_id"])
        try:
            res = A2.analyze_run(raw_dir, hf=hf, cfg=cfg, out_dir=new_dir)
            err = None
        except Exception as e:  # noqa: BLE001 - an unusable input is a recorded failure, not a silent skip
            res, err = None, repr(e)
        stages = [man.get(x) for x in ("collect_exit", "convert_exit", "cleanup_exit")] + ([man.get("delay_exit")] if rec["mode"] == "queue" else []) + \
                 ([man.get("hf_eval_exit")] if hf else [])
        process_ok = bool(all(s == 0 for s in stages))
        valid_new = bool(process_ok and res is not None and res["pass"])
        nrec = dict(rec, raw_dir=rec.get("raw_dir") or rec["results_dir"], results_dir=os.path.relpath(new_dir, ROOT) if not os.path.isabs(a.out_root) else new_dir,
                    valid_old=rec["valid"], pass_old=o_metrics.get("pass"), valid=valid_new, process_ok=process_ok,
                    failed_gates=(res or {}).get("failed_gates", ["analysis_error"]), invalid_reasons=(res or {}).get("invalid_reasons", [err]),
                    analysis_version_old=o_metrics.get("analysis_version"), analysis_version_new=(res or {}).get("analysis_version"))
        d = {"run_id": rec["run_id"], "valid_old": rec["valid"], "valid_new": valid_new, "pass_old": o_metrics.get("pass"), "pass_new": (res or {}).get("pass"),
             "error": err, "gates_added": [], "gates_removed": [], "gates_changed": [], "numeric_leaves_compared": 0, "numeric_max_abs_diff": 0.0, "numeric_diffs_over_1e-12": [],
             "curves_compared": 0, "curves_max_abs_diff": 0.0, "curves_keys_missing_in_new": []}
        if res is not None:
            og, ng = o_metrics.get("gates", {}), res["gates"]
            d["gates_added"] = sorted(set(ng) - set(og))
            d["gates_removed"] = sorted(set(og) - set(ng))
            d["gates_changed"] = sorted(g for g in set(og) & set(ng) if og[g] != ng[g])
            ol, nl = numeric_leaves(o_metrics.get("metrics", {})), numeric_leaves(res["metrics"])
            for key in set(ol) & set(nl):
                if math.isfinite(ol[key]) and math.isfinite(nl[key]):
                    diff = abs(ol[key] - nl[key])
                    d["numeric_leaves_compared"] += 1
                    d["numeric_max_abs_diff"] = max(d["numeric_max_abs_diff"], diff)
                    if diff > 1e-12:
                        d["numeric_diffs_over_1e-12"].append([key, ol[key], nl[key]])
            oc, nc = np.load(os.path.join(old_dir, "curves.npz")), np.load(os.path.join(new_dir, "curves.npz"))
            for key in oc.files:
                if key not in nc.files:
                    d["curves_keys_missing_in_new"].append(key)
                    continue
                if oc[key].dtype.kind in "fi":
                    x, y = np.asarray(oc[key], dtype=float), np.asarray(nc[key], dtype=float)
                    both = np.isfinite(x) & np.isfinite(y)
                    d["curves_compared"] += 1
                    if x.shape != y.shape or not np.array_equal(np.isnan(x), np.isnan(y)):
                        d["curves_max_abs_diff"] = float("inf")
                    elif both.any():
                        d["curves_max_abs_diff"] = max(d["curves_max_abs_diff"], float(np.max(np.abs(x[both] - y[both]))))
        new_runs.append(nrec)
        diffs.append(d)
        print("%s old_valid=%s new_valid=%s added_gates=%d changed_gates=%s" % (rec["run_id"], rec["valid"], valid_new, len(d["gates_added"]), d["gates_changed"]), flush=True)
    idx = dict(old, matrix_id=old["matrix_id"], analysis_id=a.analysis_id, source_index=os.path.abspath(a.index), analysis_version=A2.ANALYSIS_VERSION, runs=new_runs,
               note="re-analysis of existing raw data; original run directories untouched; raw_dir = original, results_dir = new analysis")
    json.dump(idx, open(os.path.join(out, "run_index.json"), "w"), indent=1)
    summ = {"analysis_id": a.analysis_id, "analysis_version": A2.ANALYSIS_VERSION, "n_runs": len(new_runs), "n_valid_old": sum(1 for r in new_runs if r["valid_old"]),
            "n_valid_new": sum(1 for r in new_runs if r["valid"]), "verdict_changes": [d["run_id"] for d in diffs if d["valid_old"] != d["valid_new"]],
            "max_numeric_abs_diff": max([d["numeric_max_abs_diff"] for d in diffs] or [0.0]), "max_curve_abs_diff": max([d["curves_max_abs_diff"] for d in diffs] or [0.0]),
            "runs_with_numeric_diffs_over_1e-12": [d["run_id"] for d in diffs if d["numeric_diffs_over_1e-12"]],
            "runs_with_new_failed_gates": [d["run_id"] for d in diffs if d["pass_old"] and not d["pass_new"]]}
    json.dump({"summary": summ, "runs": diffs}, open(os.path.join(out, "diff_report.json"), "w"), indent=1)
    print(json.dumps(summ))
    sys.exit(0)


if __name__ == "__main__":
    main()
