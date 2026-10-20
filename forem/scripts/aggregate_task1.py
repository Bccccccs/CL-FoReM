#!/usr/bin/env python3
"""Task1.4 aggregation: repeatability of the normal tracking baseline from VALID runs only (runs in forem-dev; numpy+matplotlib).

Usage: aggregate_task1.py --index results/task1/<matrix>/run_index.json --out results/task1/<analysis-id>
Reads each valid run's run_metrics.json and curves.npz (written by analyze_task1.py) - nothing is re-measured and nothing
is invented. Per case and per metric the three independent fresh runs are reported individually plus mean, sample std
(ddof=1), min, max and range; the curves are compared run against run on the common grid points that are valid in ALL runs.
Excluded runs (invalid or superseded) are listed with the reason. hf diagnostics are reported separately.
Outputs: metrics.json, repeatability.csv, summary_table.md, fig_*.png.
"""
import argparse
import csv
import itertools
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task1_lib as L  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
J = L.JOINTS
SHORT = [j.replace("ur5_", "").replace("_joint", "") for j in J]


def jload(p):
    with open(p) as f:
        return json.load(f)


def stat(vals):
    v = np.asarray(vals, dtype=float)
    return {"values": v.tolist(), "mean": float(v.mean()), "std": float(v.std(ddof=1)) if v.size > 1 else None,
            "min": float(v.min()), "max": float(v.max()), "range": float(v.max() - v.min()), "n": int(v.size)}


def pick_runs(index):
    """Per (case, role, round): the latest valid attempt; everything else is an exclusion with a reason."""
    valid, excluded, chosen = {}, [], {}
    for r in index["runs"]:
        key = (r["case"], r["role"], r["round"])
        if r["valid"]:
            valid.setdefault(key, []).append(r)
        else:
            excluded.append({"run_id": r["run_id"], "case": r["case"], "round": r["round"], "role": r["role"], "reason": "invalid",
                             "entry_exit": r["entry_exit"], "failed_gates": r["failed_gates"], "invalid_reasons": r["invalid_reasons"], "stage_exits": r["stage_exits"]})
    for key, rs in valid.items():
        chosen[key] = rs[-1]
        for extra in rs[:-1]:
            excluded.append({"run_id": extra["run_id"], "case": key[0], "round": key[2], "role": key[1], "reason": "superseded by a later valid attempt"})
    return chosen, excluded


def per_window_stats(runs_m, window):
    out = {}
    ms = [m["metrics"][window] for m in runs_m]
    out["e_q"] = {k: {SHORT[i]: stat([m["e_q"][k][i] for m in ms]) for i in range(6)} for k in ("rmse", "max_abs", "mean")}
    out["e_v"] = {k: {SHORT[i]: stat([m["e_v"][k][i] for m in ms]) for i in range(6)} for k in ("rmse", "max_abs")}
    if "final_mean" in ms[0]["e_q"]:
        out["e_q"]["final_mean"] = {SHORT[i]: stat([m["e_q"]["final_mean"][i] for m in ms]) for i in range(6)}
    out["ee_pos_err_m"] = {k: stat([m["ee_pos_err_m"][k] for m in ms]) for k in ("rmse", "max")}
    out["ee_rot_err_rad"] = {k: stat([m["ee_rot_err_rad"][k] for m in ms]) for k in ("rmse", "max")}
    if "hold" in ms[0]:
        out["hold"] = {"pos_peak_to_peak_rad": {SHORT[i]: stat([m["hold"]["pos_peak_to_peak_rad"][i] for m in ms]) for i in range(6)},
                       "vel_rms_rad_s": {SHORT[i]: stat([m["hold"]["vel_rms_rad_s"][i] for m in ms]) for i in range(6)}}
    return out


def curve_repeat(dirs):
    """Run-vs-run differences on grid points valid in all runs. Returns per-signal RMS/max pairwise difference and the signal scale."""
    cs = [np.load(os.path.join(d, "curves.npz")) for d in dirs]
    t = cs[0]["t_rel"]
    for c in cs:
        if c["t_rel"].shape != t.shape or not np.allclose(c["t_rel"], t):
            return {"error": "runs use different grids"}
    res = {"grid_points": int(t.size)}
    for name in ("e_q", "e_v", "ee_pos_err", "ee_rot_err"):
        arr = [np.asarray(c[name], dtype=float) for c in cs]
        arr = [a if a.ndim == 2 else a[:, None] for a in arr]
        ok = np.all([np.all(np.isfinite(a), axis=1) for a in arr], axis=0)
        res.setdefault("common_valid_fraction", float(ok.mean()))
        pairs = []
        for (i, a), (j, b) in itertools.combinations(list(enumerate(arr)), 2):
            d = (a - b)[ok]
            pairs.append({"runs": [i, j], "rms_diff": np.sqrt(np.mean(d ** 2, axis=0)).tolist(), "max_abs_diff": np.max(np.abs(d), axis=0).tolist()})
        mean_curve = np.mean([a[ok] for a in arr], axis=0)
        res[name] = {"signal_rms": np.sqrt(np.mean(mean_curve ** 2, axis=0)).tolist(),
                     "max_pairwise_rms_diff": np.max([p["rms_diff"] for p in pairs], axis=0).tolist(),
                     "max_pairwise_max_abs_diff": np.max([p["max_abs_diff"] for p in pairs], axis=0).tolist(), "pairs": pairs}
    return res


def lag_summary(runs_m):
    out = {}
    for j in sorted({j for m in runs_m for j in m.get("lag", {})}):
        ls = [m["lag"][j] for m in runs_m if j in m.get("lag", {})]
        out[j.replace("ur5_", "").replace("_joint", "")] = {
            "per_run": [{"identifiable": l["identifiable"], "reason": l["reason"], "tau_s": l.get("tau_s"), "tau_refined_s": l.get("tau_refined_s"),
                         "below_resolution": l.get("below_resolution"), "peak_corr": l["peak_corr"], "grid_s": l["grid_s"], "v_des_peak": l["v_des_peak"]} for l in ls],
            "all_identifiable": all(l["identifiable"] for l in ls), "all_resolvable": all(l.get("resolvable") for l in ls)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    index = jload(a.index)
    chosen, excluded = pick_runs(index)
    os.makedirs(a.out, exist_ok=False)
    cases = {}
    quality = {"truth_pairs_min": None, "truth_static_pos_err_max_m": 0.0, "truth_static_ang_err_max_rad": 0.0, "js_pair_rate_min": 1.0, "js_pos_diff_max_rad": 0.0,
               "t_ref_minus_before_s": []}
    rows = []
    figs = {}
    for case in sorted({k[0] for k in chosen if k[1] == "formal"}, key=lambda c: ["H", "P+", "P-", "L+", "L-", "M3", "M6", "MR3"].index(c)):
        rs = [chosen[k] for k in sorted(chosen, key=lambda k: (k[2] or 0)) if k[0] == case and k[1] == "formal"]
        dirs = [os.path.join(ROOT, r["results_dir"]) for r in rs]
        ms = [jload(os.path.join(d, "run_metrics.json")) for d in dirs]
        ent = {"runs": [r["run_id"] for r in rs], "n_runs": len(rs), "windows": {}}
        for w in ms[0]["metrics"]:
            ent["windows"][w] = per_window_stats(ms, w)
        if ms[0]["lag"]:
            ent["lag_125hz"] = lag_summary(ms)
        if "t_ref" in ms[0]:
            ent["t_ref_minus_before_s"] = stat([m["t_ref"]["t_ref_minus_before_s"] for m in ms])
            quality["t_ref_minus_before_s"] += [m["t_ref"]["t_ref_minus_before_s"] for m in ms]
        ent["q_start_minus_hold_ref_rad"] = ([stat([m["q_start_vs_hold_ref"]["q_start_observed"][i] - m["q_start_vs_hold_ref"]["hold_ref_desired"][i] for m in ms]) for i in range(6)]
                                              if "q_start_vs_hold_ref" in ms[0] else None)
        ent["curve_repeatability"] = curve_repeat(dirs)
        cases[case] = ent
        for m in ms:
            g = m["quality"]["gazebo_truth"]; js = m["quality"]["joint_states_vs_controller"]
            quality["truth_pairs_min"] = g["pairs"] if quality["truth_pairs_min"] is None else min(quality["truth_pairs_min"], g["pairs"])
            quality["truth_static_pos_err_max_m"] = max(quality["truth_static_pos_err_max_m"], g["static_pos_err_max_m"] or 0)
            quality["truth_static_ang_err_max_rad"] = max(quality["truth_static_ang_err_max_rad"], g["static_ang_err_max_rad"] or 0)
            quality["js_pair_rate_min"] = min(quality["js_pair_rate_min"], js["pair_rate"])
            quality["js_pos_diff_max_rad"] = max(quality["js_pos_diff_max_rad"], js["max_abs_pos_diff_rad"])
        # flat table
        for w, wd in ent["windows"].items():
            for grp, items in (("e_q", wd["e_q"]), ("e_v", wd["e_v"])):
                for metric, per_j in items.items():
                    for jn, s in per_j.items():
                        rows.append([case, w, grp + "." + metric, jn] + s["values"] + [s["mean"], s["std"], s["min"], s["max"], s["range"]])
            for grp in ("ee_pos_err_m", "ee_rot_err_rad"):
                for metric, s in wd[grp].items():
                    rows.append([case, w, grp + "." + metric, "ee"] + s["values"] + [s["mean"], s["std"], s["min"], s["max"], s["range"]])
            for metric, per_j in wd.get("hold", {}).items():
                for jn, s in per_j.items():
                    rows.append([case, w, "hold." + metric, jn] + s["values"] + [s["mean"], s["std"], s["min"], s["max"], s["range"]])
        figs[case] = [np.load(os.path.join(d, "curves.npz")) for d in dirs]

    # hf diagnostics, reported separately
    hf = {}
    for k, r in chosen.items():
        if k[1] != "hf_diagnostic":
            continue
        d = os.path.join(ROOT, r["results_dir"])
        m = jload(os.path.join(d, "run_metrics.json"))
        hfw = jload(os.path.join(d, "hf_analysis_windows.json"))
        hf[k[0]] = {"run_id": r["run_id"], "windows": {w: {"e_q_rmse": e["e_q"]["rmse"], "e_q_max_abs": e["e_q"]["max_abs"], "ee_pos_err_rmse_m": e["ee_pos_err_m"]["rmse"]} for w, e in m["metrics"].items()},
                    "lag_0p5ms_grid": {j.replace("ur5_", "").replace("_joint", ""): {"identifiable": l["identifiable"], "tau_s": l.get("tau_s"), "tau_refined_s": l.get("tau_refined_s"),
                                                                                     "below_resolution": l.get("below_resolution"), "peak_corr": l["peak_corr"], "reason": l["reason"]} for j, l in m["lag"].items()},
                    "task0_7_criteria": {w: {"pass": v["pass"], "coverage": v.get("coverage_of_expected_pairs"), "verdicts": sorted(set(v["verdict"].values()))} for w, v in hfw["windows"].items()},
                    "criteria_pass": hfw["pass"]}
    quality["t_ref_minus_before_s"] = stat(quality["t_ref_minus_before_s"]) if quality["t_ref_minus_before_s"] else None
    out = {"matrix_id": index["matrix_id"], "freeze_id": index["freeze_id"], "n_valid_formal_runs": sum(c["n_runs"] for c in cases.values()), "cases": cases, "hf_diagnostics": hf,
           "quality_summary": quality, "excluded_runs": excluded, "notes": [
               "std is the sample standard deviation (ddof=1) of 3 independent fresh runs; with n=3 it is itself uncertain",
               "pass/valid refers to measurement quality gates, not arm accuracy",
               "lag is a diagnostic of the normal servo response, not a transport delay; 125 Hz sampling cannot resolve lags below 8 ms"]}
    with open(os.path.join(a.out, "metrics.json"), "w") as f:
        json.dump(out, f, indent=1)
    with open(os.path.join(a.out, "repeatability.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "window", "metric", "joint_or_ee", "run1", "run2", "run3", "mean", "std_ddof1", "min", "max", "range"])
        w.writerows(rows)

    # compact table
    with open(os.path.join(a.out, "summary_table.md"), "w") as f:
        f.write("| case | window | max-joint e_q RMSE (rad) mean±std | max-joint e_q peak (rad) mean | EE pos RMSE (m) mean±std | EE pos peak (m) mean | EE rot peak (rad) mean |\n|---|---|---|---|---|---|---|\n")
        for case, c in cases.items():
            for w, wd in c["windows"].items():
                if w == "pre_hold":
                    continue
                jm = max(SHORT, key=lambda s: wd["e_q"]["rmse"][s]["mean"])
                r = wd["e_q"]["rmse"][jm]
                pk = max(wd["e_q"]["max_abs"][s]["mean"] for s in SHORT)
                f.write("| %s | %s | %.3g±%.2g (%s) | %.3g | %.3g±%.2g | %.3g | %.3g |\n" % (case, w, r["mean"], r["std"] or 0, jm, pk, wd["ee_pos_err_m"]["rmse"]["mean"],
                                                                                    wd["ee_pos_err_m"]["rmse"]["std"] or 0, wd["ee_pos_err_m"]["max"]["mean"], wd["ee_rot_err_rad"]["max"]["mean"]))

    # figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for case, cs in figs.items():
        if case == "H":
            continue
        fig, axs = plt.subplots(2, 3, figsize=(13, 6), sharex=True)
        for i, ax in enumerate(axs.ravel()):
            for k, c in enumerate(cs):
                ax.plot(c["t_rel"], c["e_q"][:, i], lw=1, label="run %d" % (k + 1))
            ax.set_title(SHORT[i]); ax.set_xlabel("t - t_ref (s)"); ax.set_ylabel("actual - desired (rad)"); ax.grid(alpha=.3)
        axs[0, 0].legend(fontsize=7)
        fig.suptitle("Case %s: joint tracking error, 3 independent fresh runs" % case)
        fig.tight_layout(); fig.savefig(os.path.join(a.out, "fig_joint_error_%s.png" % case.replace("+", "p").replace("-", "m")), dpi=110); plt.close(fig)
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.5))
    for case, cs in figs.items():
        if case == "H":
            continue
        for c in cs:
            axs[0].plot(c["t_rel"], c["ee_pos_err"], lw=.8, color="C%d" % list(figs).index(case))
            axs[1].plot(c["t_rel"], c["ee_rot_err"], lw=.8, color="C%d" % list(figs).index(case))
        axs[0].plot([], [], color="C%d" % list(figs).index(case), label=case)
    axs[0].set_ylabel("EE position error (m)"); axs[1].set_ylabel("EE rotation error (rad)")
    for ax in axs:
        ax.set_xlabel("t - t_ref (s)"); ax.grid(alpha=.3)
    axs[0].legend(fontsize=7, ncol=2)
    fig.tight_layout(); fig.savefig(os.path.join(a.out, "fig_ee_error.png"), dpi=110); plt.close(fig)
    print(json.dumps({"out": a.out, "n_valid_formal_runs": out["n_valid_formal_runs"], "cases": list(cases), "hf": list(hf), "excluded": len(excluded)}))


if __name__ == "__main__":
    main()
