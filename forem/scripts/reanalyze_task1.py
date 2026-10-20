#!/usr/bin/env python3
"""Task1.7: re-analyse existing runs with the corrected tools into a NEW directory, and run negative controls (runs in forem-dev).

  reanalyze  --index results/task1/<matrix>/run_index.json --out results/task1/<analysis-id> [--only RUN_ID ...]
      For each run: re-convert the ORIGINAL bag with the current task1_bag_to_csv.py (new command schema), analyse with the
      current analyze_task1.py, and compare against the OLD raw files / run_metrics.json / curves.npz. Old directories are only
      read. Writes <out>/runs/<run-id>/..., <out>/reanalysis_index.json, <out>/diff_report.json.
  negatives  --old-run RUN_DIR --new-run RUN_DIR --out DIR
      The task1.5/1.6 reproductions on a real run, in private copies: zero tip/base quaternion, one zero row, bag command velocity /
      first-point position / effort changed. Runs the OLD code (copies in <out>/../old_code) and the NEW code on the same mutation.
Nothing in an existing results directory is modified.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_task1 as A  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RAW_SAME = ["joint_states.csv", "controller_state.csv", "link_truth.csv", "clock.csv", "bag_summary.json"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def jload(p):
    with open(p) as f:
        return json.load(f)


def walk(old, new, path, out):
    """Collect differences between two JSON-like trees. Numbers are compared exactly."""
    if isinstance(old, dict) and isinstance(new, dict):
        for k in sorted(set(old) | set(new)):
            if k not in new:
                out["keys_removed"].append(path + "/" + k)
            elif k not in old:
                out["keys_added"].append(path + "/" + k)
            else:
                walk(old[k], new[k], path + "/" + k, out)
    elif isinstance(old, list) and isinstance(new, list) and len(old) == len(new):
        for i, (a, b) in enumerate(zip(old, new)):
            walk(a, b, "%s[%d]" % (path, i), out)
    elif isinstance(old, (int, float)) and isinstance(new, (int, float)) and not isinstance(old, bool) and not isinstance(new, bool):
        out["numeric_compared"] += 1
        if not (old == new or (old != old and new != new)):
            out["numeric_differences"].append({"path": path, "old": old, "new": new, "abs_diff": abs(old - new)})
    else:
        out["non_numeric_compared"] += 1
        if old != new:
            out["non_numeric_changes"].append({"path": path, "old": str(old)[:120], "new": str(new)[:120]})


def reanalyze(a):
    index = jload(a.index)
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config", "experiments", "task1", "baseline.yaml")))
    out_root = os.path.join(ROOT, a.out)
    os.makedirs(os.path.join(out_root, "runs"), exist_ok=True)
    recs, diffs = [], {}
    expected_added = ("/analysis_version", "/quality/commands_match_bag/", "/quality/gazebo_truth/quat_", "/quality/gazebo_truth/all_finite", "/quality/base_drift/invalid_quaternion")
    for r in index["runs"]:
        if a.only and r["run_id"] not in a.only:
            continue
        rid = r["run_id"]
        old = os.path.join(ROOT, r["results_dir"])
        new = os.path.join(out_root, "runs", rid)
        if os.path.exists(new):
            print("REFUSED: %s already exists (never overwrite)" % new)
            sys.exit(12)
        os.makedirs(os.path.join(new, "raw"))
        hf = r["role"] == "hf_diagnostic"
        for f in ("commands.json", "robot_description.urdf", "controller_params.json"):
            shutil.copy2(os.path.join(old, f), os.path.join(new, f))
        conv = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "task1_bag_to_csv.py"), "--bag", os.path.join(old, "run.bag"), "--out", os.path.join(new, "raw")] + (["--hf"] if hf else []),
                              capture_output=True, text=True)
        rec = {"run_id": rid, "case": r["case"], "role": r["role"], "old_dir": r["results_dir"], "new_dir": os.path.relpath(new, ROOT), "convert_exit": conv.returncode,
               "bag_sha256": sha(os.path.join(old, "run.bag"))}
        if conv.returncode != 0:
            rec["error"] = conv.stdout[-400:] + conv.stderr[-400:]
            recs.append(rec)
            continue
        rec["raw_identical_to_old"] = {f: sha(os.path.join(old, "raw", f)) == sha(os.path.join(new, "raw", f)) for f in RAW_SAME}
        rec["bag_commands_schema"] = {"old": "legacy (float header stamp, no effort/frame_id)", "new": jload(os.path.join(new, "raw", "bag_commands.json"))[0]["message"]["schema"] if jload(os.path.join(new, "raw", "bag_commands.json")) else "no command messages"}
        try:
            res = A.analyze_run(new, hf=hf, cfg=cfg)
        except Exception as e:  # noqa: BLE001
            rec["analysis_error"] = repr(e)
            recs.append(rec)
            continue
        o = jload(os.path.join(old, "run_metrics.json"))
        n = jload(os.path.join(new, "run_metrics.json"))
        d = {"keys_added": [], "keys_removed": [], "numeric_compared": 0, "numeric_differences": [], "non_numeric_compared": 0, "non_numeric_changes": []}
        walk(o, n, "", d)
        d["keys_added_unexpected"] = [k for k in d["keys_added"] if not any(k.startswith(e) or e in k for e in expected_added)]
        co, cn = np.load(os.path.join(old, "curves.npz")), np.load(os.path.join(new, "curves.npz"))
        d["curves_identical"] = bool(set(co.files) == set(cn.files) and all(
            (np.array_equal(co[k], cn[k], equal_nan=True) if co[k].dtype.kind in "fiu" else np.array_equal(co[k], cn[k])) for k in co.files))
        rec.update({"pass_old": o["pass"], "pass_new": n["pass"], "failed_gates_old": o["failed_gates"], "failed_gates_new": n["failed_gates"],
                    "analysis_version_new": n["analysis_version"], "sha256": {"run_metrics_old": sha(os.path.join(old, "run_metrics.json")), "run_metrics_new": sha(os.path.join(new, "run_metrics.json")),
                                                                              "curves_old": sha(os.path.join(old, "curves.npz")), "curves_new": sha(os.path.join(new, "curves.npz"))},
                    "numeric_compared": d["numeric_compared"], "numeric_differences": len(d["numeric_differences"]), "non_numeric_changes": len(d["non_numeric_changes"]),
                    "keys_removed": len(d["keys_removed"]), "keys_added_unexpected": len(d["keys_added_unexpected"]), "curves_identical": d["curves_identical"],
                    "commands_match_bag_new": n["quality"].get("commands_match_bag", {}).get("match")})
        diffs[rid] = d
        recs.append(rec)
        print("%s pass %s->%s numeric %d/%d differ, changed %d, unexpected-added %d, raw same %s" % (rid, rec["pass_old"], rec["pass_new"], rec["numeric_differences"], rec["numeric_compared"],
              rec["non_numeric_changes"], rec["keys_added_unexpected"], all(rec["raw_identical_to_old"].values())), flush=True)
    summary = {"runs": len(recs), "all_convert_ok": all(r["convert_exit"] == 0 for r in recs),
               "all_pass_new": all(r.get("pass_new") for r in recs), "pass_changed": [r["run_id"] for r in recs if r.get("pass_old") != r.get("pass_new")],
               "runs_with_numeric_differences": [r["run_id"] for r in recs if r.get("numeric_differences")],
               "runs_with_unexpected_added_keys": [r["run_id"] for r in recs if r.get("keys_added_unexpected")],
               "runs_with_raw_csv_changes": [r["run_id"] for r in recs if not all(r.get("raw_identical_to_old", {"x": False}).values())],
               "total_numeric_compared": sum(r.get("numeric_compared", 0) for r in recs)}
    with open(os.path.join(out_root, "reanalysis_index.json"), "w") as f:
        json.dump({"source_index": a.index, "analysis_version_new": A.ANALYSIS_VERSION, "analysis_version_old": "task1.4-original", "summary": summary, "runs": recs}, f, indent=1)
    with open(os.path.join(out_root, "diff_report.json"), "w") as f:
        json.dump(diffs, f, indent=1)
    print(json.dumps(summary, indent=1))
    sys.exit(0 if (summary["all_convert_ok"] and summary["all_pass_new"] and not summary["runs_with_numeric_differences"]) else 1)


# ------------------------------------------------------------------ negative controls
def private_copy(src, dst, mutate_file=None):
    """dst/ gets symlinks to every file of src except those listed in mutate_file (copied)."""
    for d, _, files in os.walk(src):
        rel = os.path.relpath(d, src)
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in files:
            if f in ("run_metrics.json", "curves.npz", "manifest.json", "run.bag"):
                continue
            sp, dp = os.path.join(d, f), os.path.join(dst, rel, f)
            if mutate_file and os.path.normpath(os.path.join(rel, f)) == mutate_file:
                shutil.copy2(sp, dp)
            else:
                os.symlink(os.path.abspath(sp), dp)


def mutate(kind, run_dir, schema):
    raw = os.path.join(run_dir, "raw")
    if kind.startswith("quat_overflow"):
        # task1.9: one extra in-window row between two controller samples (never the nearest truth row of any sample) whose finite
        # components make the norm overflow to Inf
        p = os.path.join(raw, "link_truth.csv")
        lines = open(p).read().splitlines()
        h = lines[0].split(","); rows = [l.split(",") for l in lines[1:]]
        cols = ["t_qx", "t_qy", "t_qz", "t_qw"] if "tip" in kind else ["b_qx", "b_qy", "b_qz", "b_qw"]
        extra = list(rows[400])
        extra[0] = repr(float(extra[0]) + 0.004)
        for c, v in zip(cols, ("1e308", "0", "0", "1")):
            extra[h.index(c)] = v
        rows.insert(401, extra)
        open(p, "w").write("\n".join([",".join(h)] + [",".join(r) for r in rows]) + "\n")
    elif kind.startswith("quat"):
        p = os.path.join(raw, "link_truth.csv")
        lines = open(p).read().splitlines()
        h = lines[0].split(","); rows = [l.split(",") for l in lines[1:]]
        cols = {"quat_zero_tip": ["t_qx", "t_qy", "t_qz", "t_qw"], "quat_zero_base": ["b_qx", "b_qy", "b_qz", "b_qw"], "quat_zero_tip_one_row": ["t_qx", "t_qy", "t_qz", "t_qw"]}[kind]
        idx = [h.index(c) for c in cols]
        targets = [200] if kind.endswith("one_row") else range(len(rows))
        for i in targets:
            for j in idx:
                rows[i][j] = "0"
        open(p, "w").write("\n".join([",".join(h)] + [",".join(r) for r in rows]) + "\n")
    else:
        p = os.path.join(raw, "bag_commands.json")
        b = json.load(open(p))
        msg = b[0]["message"] if schema == "new" else b[0]
        if kind == "bag_velocity_point1":
            msg["points"][1]["velocities"][0] = 0.5
        elif kind == "bag_first_point_position":
            msg["points"][0]["positions"][1] += 0.01
        elif kind == "bag_effort_point1":
            msg["points"][1]["effort"] = [1.0] * 6 if schema == "new" else msg["points"][1].get("effort", [])
        json.dump(b, open(p, "w"))


def negatives(a):
    out = os.path.join(ROOT, a.out)
    os.makedirs(out, exist_ok=False)
    old_pkg = os.path.join(os.path.dirname(out), "old_code", "pkg")
    cfg_path = os.path.join(ROOT, "config", "experiments", "task1", "baseline.yaml")
    kinds = ["control_unmodified", "quat_overflow_tip_unpaired", "quat_overflow_base_unpaired", "quat_zero_tip", "quat_zero_base", "quat_zero_tip_one_row", "bag_velocity_point1", "bag_first_point_position", "bag_effort_point1"]
    results = []
    for kind in kinds:
        row = {"case": kind}
        for ver, run_src, schema, script in (("old", a.old_run, "new", os.path.join(old_pkg, "analyze_task1.py")),
                                              ("new", a.new_run, "new", os.path.join(ROOT, "scripts", "analyze_task1.py"))):
            dst = os.path.join(out, kind, ver)
            if kind == "control_unmodified":
                private_copy(os.path.join(ROOT, run_src), dst)
            else:
                mf = "raw/link_truth.csv" if kind.startswith("quat") else "raw/bag_commands.json"
                private_copy(os.path.join(ROOT, run_src), dst, mutate_file=mf)
                mutate(kind, dst, schema)
            p = subprocess.run([sys.executable, script, "run", "--run-dir", dst, "--config", cfg_path], capture_output=True, text=True)
            m = jload(os.path.join(dst, "run_metrics.json")) if os.path.exists(os.path.join(dst, "run_metrics.json")) else {}
            tr = m.get("quality", {}).get("gazebo_truth", {})
            row[ver] = {"exit": p.returncode, "pass": m.get("pass"), "failed_gates": m.get("failed_gates"), "analysis_version": m.get("analysis_version", "task1.4-original"),
                        "truth_pos_err_max": tr.get("pos_err_max_m"), "stderr_tail": p.stderr[-200:] if p.returncode not in (0, 1) else ""}
        results.append(row)
        print("%-26s old: exit %s pass %s %s | new: exit %s pass %s %s" % (kind, row["old"]["exit"], row["old"]["pass"], row["old"]["failed_gates"], row["new"]["exit"], row["new"]["pass"], row["new"]["failed_gates"]), flush=True)
    ok_new = all((r["new"]["pass"] is True) if r["case"] == "control_unmodified" else (r["new"]["pass"] is False) for r in results)
    ok_ctrl_old = results[0]["old"]["pass"] is True
    with open(os.path.join(out, "negative_controls.json"), "w") as f:
        json.dump({"old_run": a.old_run, "new_run": a.new_run, "all_expected_for_new_code": ok_new, "old_control_passes": ok_ctrl_old, "results": results}, f, indent=1)
    print("new code behaves as required:", ok_new)
    sys.exit(0 if ok_new else 1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reanalyze"); r.add_argument("--index", required=True); r.add_argument("--out", required=True); r.add_argument("--only", nargs="*")
    n = sub.add_parser("negatives"); n.add_argument("--old-run", required=True); n.add_argument("--new-run", required=True); n.add_argument("--out", required=True)
    a = ap.parse_args()
    {"reanalyze": reanalyze, "negatives": negatives}[a.cmd](a)


if __name__ == "__main__":
    main()
