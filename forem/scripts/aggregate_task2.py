#!/usr/bin/env python3
"""Task2 aggregation over many runs (runs in forem-dev; numpy, PyYAML, matplotlib for the figures).

  aggregate_task2.py --index RUN_INDEX.json --analysis-id ID --out OUT_DIR [--task1-curves results/task1/t1.9-a3/runs] [--no-figures]

OUT_DIR must not exist (analyses are never overwritten). Reads ONLY the run index named on the command line and, for every VALID run in it, that run's
run_metrics.json / curves.npz (written by analyze_task2.py); runs the index marks invalid stay in the failure table and are never silently dropped
or replaced. Writes: run_index_used.json, per_run.json/.csv, groups.json, equivalence_bz.json, nonzero_servo.json, repeatability.json, dose.json,
failures.json, summary.json, summary.md and figures/*.png.

Statistics are descriptive (n = 3 rounds): mean, sample std (ddof=1), min, max, range and pairwise curve RMSE / peak differences. Time samples are
never counted as independent repeats and no confidence interval is claimed. Gates are the pre-registered exp2.1 section 5 values from the frozen
config; a failed gate is reported, not repaired.
"""
import argparse
import csv
import hashlib
import json
import os
import sys

import numpy as np
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task1_lib as L  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CONFIG = os.path.join(ROOT, "config", "experiments", "exp2", "fixed_delay.yaml")
J = L.JOINTS
AGG_VERSION = "task2.6-agg2"   # agg1: B/Z equivalence on fit-aligned curves only (labelled PASS); agg2: protocol-v1 t_ref-aligned AND v1.1 fit-aligned results side by side (T2-A01)
CONDS = ["B", "Z", "D80", "D160"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def jl(path):
    with open(path) as f:
        return json.load(f)


# ------------------------------------------------------------------------------------------------------------ pure statistics
def describe(values):
    """mean, sample std (ddof=1), min, max, range of a 1-D list of per-run numbers; std is None for n<2."""
    x = np.asarray(values, dtype=float)
    if x.size == 0:
        return {"n": 0}
    return {"n": int(x.size), "mean": float(x.mean()), "std": float(x.std(ddof=1)) if x.size > 1 else None, "min": float(x.min()), "max": float(x.max()),
            "range": float(x.max() - x.min()), "values": x.tolist()}


def curve_diff_stats(a, b, min_valid_fraction=0.9):
    """Per-column RMSE and peak |difference| of two curves on the same grid, over samples finite in both. Returns None if the shapes differ
    or too few samples are valid (never extrapolates, never fills NaN)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.shape != b.shape:
        n = min(a.shape[0], b.shape[0])
        if abs(a.shape[0] - b.shape[0]) > 1 or a.shape[1:] != b.shape[1:]:
            return None
        a, b = a[:n], b[:n]
    d = a - b
    ok = np.all(np.isfinite(d.reshape(d.shape[0], -1)), axis=1)
    if ok.mean() < min_valid_fraction:
        return None
    d = d[ok]
    if d.ndim == 1:
        d = d[:, None]
    return {"rmse": np.sqrt(np.mean(d ** 2, axis=0)).tolist(), "peak": np.max(np.abs(d), axis=0).tolist(), "n_valid": int(ok.sum()), "n": int(ok.size)}


def pairwise(curves, key):
    """All unordered pairs of {run_id: array}: curve_diff_stats for each."""
    ids = sorted(curves)
    out = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            s = curve_diff_stats(curves[ids[i]], curves[ids[j]])
            out.append({"a": ids[i], "b": ids[j], "key": key, "stats": s})
    return out


def max_over(stats_list, field):
    vals = [max(s["stats"][field]) for s in stats_list if s["stats"] is not None]
    return max(vals) if vals else None


# ------------------------------------------------------------------------------------------------------------ loading
class Run:
    def __init__(self, rec, root):
        self.rec = rec
        self.id = rec["run_id"]
        self.case, self.cond, self.round, self.role = rec["case"], rec["condition"], rec.get("round"), rec["role"]
        self.dir = os.path.join(root, rec["results_dir"])
        self.valid = bool(rec["valid"])
        self.m = jl(os.path.join(self.dir, "run_metrics.json")) if self.valid else None
        self._curves = None

    @property
    def curves(self):
        if self._curves is None:
            self._curves = dict(np.load(os.path.join(self.dir, "curves.npz")))
        return self._curves


def per_run_row(r):
    m = r.m
    d = m["delay"]
    row = {"run_id": r.id, "case": r.case, "condition": r.cond, "round": r.round, "role": r.role, "mode": m["mode"], "tau_ms": m["tau_ms"], "pass": m["pass"],
           "analysis_version": m["analysis_version"]}
    mt = m["metrics"]
    if r.case == "H":
        h = mt["hold"]
        row.update({"hold_e_servo_rmse": h["e_servo"]["rmse"], "hold_e_servo_max": h["e_servo"]["max_abs"], "hold_e_servo_mean": h["e_servo"]["mean"],
                    "hold_pos_ptp": h["hold"]["pos_peak_to_peak_rad"], "hold_vel_rms": h["hold"]["vel_rms_rad_s"]})
        return row
    for wn in ("motion_nom", "exec_nom", "motion", "settle"):
        w = mt[wn]
        row["%s_e_total_rmse" % wn] = w["e_total"]["rmse"]
        row["%s_e_total_max" % wn] = w["e_total"]["max_abs"]
        row["%s_e_total_mean" % wn] = w["e_total"]["mean"]
        row["%s_e_total_final" % wn] = w["e_total"].get("final_mean")
        row["%s_e_schedule_rmse" % wn] = w["e_schedule"]["rmse"]
        row["%s_e_schedule_max" % wn] = w["e_schedule"]["max_abs"]
        row["%s_e_servo_rmse" % wn] = w["e_servo"]["rmse"]
        row["%s_e_servo_max" % wn] = w["e_servo"]["max_abs"]
        row["%s_e_servo_mean" % wn] = w["e_servo"]["mean"]
        row["%s_e_servo_final" % wn] = w["e_servo"].get("final_mean")
        for k in ("pos_servo_m", "pos_schedule_m", "pos_total_m"):
            row["%s_ee_%s_rmse" % (wn, k)] = w["ee_" + k]["rmse"]
            row["%s_ee_%s_max" % (wn, k)] = w["ee_" + k]["max"]
        for k in ("rot_servo_rad", "rot_schedule_rad", "rot_total_rad"):
            row["%s_ee_%s_rmse" % (wn, k)] = w["ee_" + k]["rmse"]
            row["%s_ee_%s_max" % (wn, k)] = w["ee_" + k]["max"]
    row.update({"t_send_width_s": d["t_send_width_s"], "t_ref_s": d["t_ref_s"], "t_ref_minus_send_before_s": d["t_ref_minus_send_before_s"],
                "t_ref_minus_send_after_s": d["t_ref_minus_send_after_s"], "t_ref_minus_t0_mid_s": d["t_ref_minus_t0_mid_s"],
                "t_ref_minus_t0_mid_minus_tau_s": d["t_ref_minus_t0_mid_minus_tau_s"], "t_ref_minus_pub_before_s": d["t_ref_minus_pub_before_s"],
                "t_ref_minus_pub_after_s": d["t_ref_minus_pub_after_s"], "t_start_fit_s": d["t_start_fit_s"],
                "t_start_fit_minus_send_before_s": d["t_start_fit_minus_send_before_s"], "t_start_fit_minus_send_after_s": d["t_start_fit_minus_send_after_s"],
                "t_start_fit_minus_t0_mid_minus_tau_s": d["t_start_fit_minus_t0_mid_minus_tau_s"],
                "fit_valid": bool(d["fit_validity"]["valid"]) if "fit_validity" in d else None,
                "fit_residual_max_abs_rad": d["fit_validity"]["residual_max_abs_rad"] if "fit_validity" in d else None,
                "t_ref_minus_t_start_fit_s": d.get("t_ref_minus_t_start_fit_s")})
    if d.get("queue"):
        q = d["queue"]
        row.update({"d_queue_ms": q["d_queue_ns"] / 1e6, "eps_ms": q["eps_ns"] / 1e6, "t_in_minus_send_after_ms": q["t_in_minus_t_send_after_ns"] / 1e6,
                    "t_in_minus_send_before_ms": q["t_in_minus_t_send_before_ns"] / 1e6, "pub_interval_ms": q["pub_interval_ns"] / 1e6,
                    "bag_down_minus_pub_before_ms": None if q["bag_down_minus_t_pub_before_ns"] is None else q["bag_down_minus_t_pub_before_ns"] / 1e6})
    for key in ("vs_nominal_actual", "vs_nominal_reference", "servo_desired_to_actual"):
        row["lag_" + key] = {j: (v[key]["tau_s"] if v[key]["identifiable"] else None) for j, v in m["lag"].items()}
        row["lag_%s_note" % key] = {j: v[key].get("reason") or v[key].get("note") for j, v in m["lag"].items()}
    row["send_sensitivity_max_rmse_change"] = {wn: m["send_interval_sensitivity"]["per_window"][wn]["max_abs_rmse_change_vs_mid"] for wn in ("motion_nom", "exec_nom")}
    return row


# ------------------------------------------------------------------------------------------------------------ analyses
def group_stats(rows):
    """(case, condition) -> descriptive statistics over valid formal rounds."""
    groups = {}
    for row in rows:
        groups.setdefault((row["case"], row["condition"]), []).append(row)
    out = {}
    for (case, cond), rs in sorted(groups.items()):
        ent = {"n_runs": len(rs), "runs": [r["run_id"] for r in rs], "rounds": [r["round"] for r in rs]}
        keys = [k for k in rs[0] if isinstance(rs[0][k], list) and not k.endswith("_note")]
        for k in keys:
            arr = np.array([r[k] for r in rs], dtype=float)
            ent[k] = {"mean": arr.mean(axis=0).tolist(), "std": (arr.std(axis=0, ddof=1).tolist() if arr.shape[0] > 1 else None), "min": arr.min(axis=0).tolist(),
                      "max": arr.max(axis=0).tolist(), "range": (arr.max(axis=0) - arr.min(axis=0)).tolist()}
        for k in [k for k in rs[0] if isinstance(rs[0][k], float) and not isinstance(rs[0][k], bool)]:
            vals = [r[k] for r in rs if r.get(k) is not None]
            ent[k] = describe(vals)
        out["%s|%s" % (case, cond)] = ent
    return out


def repeatability(rows, gcfg):
    out = {}
    g = gcfg["repeatability"]
    for (case, cond), rs in sorted({(r["case"], r["condition"]): None for r in rows}.items()):
        sel = [r for r in rows if r["case"] == case and r["condition"] == cond]
        if case == "H" or len(sel) < 2:
            continue
        offs = [r["t_ref_minus_send_before_s"] for r in sel]
        rng = float(max(offs) - min(offs))
        tot = np.array([r["exec_nom_e_total_rmse"] for r in sel])
        rng_j = tot.max(axis=0) - tot.min(axis=0)
        lim_j = np.maximum(g["e_total_rmse_range_rel"] * np.abs(tot.mean(axis=0)), g["e_total_rmse_range_abs_rad"])
        insufficient_j = [J[i] for i in range(6) if rng_j[i] > lim_j[i]]
        out["%s|%s" % (case, cond)] = {
            "n": len(sel), "t_ref_minus_send_before_range_s": rng, "t_ref_offset_limit_s": g["t_ref_offset_range_s_max"],
            "t_ref_offset_insufficient": bool(rng > g["t_ref_offset_range_s_max"]),
            "e_total_exec_rmse_range_rad": rng_j.tolist(), "e_total_exec_rmse_limit_rad": lim_j.tolist(),
            "joints_with_insufficient_repeatability": insufficient_j,
            "rule": "range > max(%.0f%% of |mean|, %.0e rad) per joint, or t_ref offset range > %.0f ms: marked insufficient (reported, not repaired)" %
                    (100 * g["e_total_rmse_range_rel"], g["e_total_rmse_range_abs_rad"], 1e3 * g["t_ref_offset_range_s_max"])}
    return out


def curve_set(runs, case, cond, key):
    return {r.id: r.curves[key] for r in runs if r.case == case and r.cond == cond and key in r.curves}


def equivalence_bz(runs, rows, gcfg, hist, alignment):
    """B vs Z on curves aligned either on the threshold t_ref (alignment="t_ref", protocol v1 as pre-registered) or on the sub-sample fitted start
    (alignment="fit", protocol v1.1 amendment). Same pre-registered numeric limits for both; q_actual, e_servo and FK position error curves + the
    t_ref-t_send median gate (always defined on t_ref). The fit alignment is evaluable only if every involved run has a valid, identifiable fit."""
    assert alignment in ("t_ref", "fit")
    pref = "fit_" if alignment == "fit" else ""
    g = gcfg["equivalence_bz"]
    out = {"alignment": alignment, "gates": g, "cases": {}}
    for case in sorted({r.case for r in runs if r.case != "H"}):
        B = {r.round: r for r in runs if r.case == case and r.cond == "B"}
        Z = {r.round: r for r in runs if r.case == case and r.cond == "Z"}
        if not B or not Z:
            continue
        ent = {"matched_rounds": sorted(set(B) & set(Z)), "curves": {}}
        verdicts = []
        if alignment == "fit":
            bad_fit = [r.id for r in list(B.values()) + list(Z.values()) if not r.m["delay"].get("fit_validity", {}).get("valid")]
            ent["fit_evaluable"] = not bad_fit
            if bad_fit:
                ent["fit_invalid_runs"] = bad_fit
                verdicts.append(False)
        for name, key, fld_rmse, fld_peak in (("q_actual", "q_act", "q_actual_curve_rmse_rad_max", "q_actual_curve_peak_rad_max"),
                                              ("e_servo", "e_q", "e_servo_curve_rmse_rad_max", "e_servo_curve_peak_rad_max"),
                                              ("fk_pos_err", "ee_pos_err", "fk_pos_err_curve_rmse_m_max", "fk_pos_err_curve_peak_m_max")):
            ck = pref + key
            matched = [{"round": rd, "stats": curve_diff_stats(B[rd].curves[ck], Z[rd].curves[ck])} for rd in ent["matched_rounds"]]
            cross = [{"b": B[i].id, "z": Z[j].id, "stats": curve_diff_stats(B[i].curves[ck], Z[j].curves[ck])} for i in sorted(B) for j in sorted(Z)]
            bb = pairwise({B[i].id: B[i].curves[ck] for i in B}, ck)
            zz = pairwise({Z[i].id: Z[i].curves[ck] for i in Z}, ck)
            rm, pk = max_over(matched, "rmse"), max_over(matched, "peak")
            ent["curves"][name] = {"matched_pairs": matched, "all_cross_pairs_max_rmse": max_over(cross, "rmse"), "all_cross_pairs_max_peak": max_over(cross, "peak"),
                                   "within_B_pairs_max_rmse": max_over(bb, "rmse"), "within_B_pairs_max_peak": max_over(bb, "peak"),
                                   "within_Z_pairs_max_rmse": max_over(zz, "rmse"), "within_Z_pairs_max_peak": max_over(zz, "peak"),
                                   "matched_max_rmse": rm, "matched_max_peak": pk, "limit_rmse": g[fld_rmse], "limit_peak": g[fld_peak],
                                   "pass": bool(rm is not None and pk is not None and rm <= g[fld_rmse] and pk <= g[fld_peak]),
                                   "joint_resolved_rmse_matched": [s_["stats"]["rmse"] for s_ in matched if s_["stats"]]}
            verdicts.append(ent["curves"][name]["pass"])
            if alignment == "t_ref" and hist and case in hist and key in ("e_q", "ee_pos_err"):
                hp = pairwise({k: v[key] for k, v in hist[case].items() if key in v}, key)
                ent["curves"][name]["task1_historical_pairwise_max_rmse"] = max_over(hp, "rmse")
                ent["curves"][name]["task1_historical_pairwise_max_peak"] = max_over(hp, "peak")
        med = {}
        for c in ("B", "Z"):
            v = [r["t_ref_minus_send_before_s"] for r in rows if r["case"] == case and r["condition"] == c]
            med[c] = float(np.median(v)) if v else None
        ent["t_ref_minus_send_median_s"] = med
        ent["t_ref_minus_send_median_diff_s"] = abs(med["Z"] - med["B"]) if None not in med.values() else None
        ent["t_ref_median_gate_pass"] = bool(ent["t_ref_minus_send_median_diff_s"] is not None and ent["t_ref_minus_send_median_diff_s"] <= g["t_ref_minus_send_median_diff_s_max"])
        verdicts.append(ent["t_ref_median_gate_pass"])
        ent["pass"] = bool(all(verdicts))
        out["cases"][case] = ent
    out["pass"] = bool(out["cases"]) and all(c["pass"] for c in out["cases"].values())
    out["n_group_comparisons"] = sum(len(c["matched_rounds"]) for c in out["cases"].values())
    out["q_actual_failed_group_comparisons"] = sum(1 for c in out["cases"].values() for p in c["curves"]["q_actual"]["matched_pairs"]
                                                  if p["stats"] is None or max(p["stats"]["rmse"]) > g["q_actual_curve_rmse_rad_max"] or max(p["stats"]["peak"]) > g["q_actual_curve_peak_rad_max"])
    return out


def alignment_explanation(runs, cfg_cases):
    """Why do the t_ref-aligned q_actual curves of B and Z differ by 1e-4 rad? Because t_ref is a threshold crossing on 8 ms samples, so each run's curve is
    shifted by delta = t_ref - t_start_fit (0 .. ~13 ms) against its true start; two runs with different delta differ by ~ v(t) * (delta_B - delta_Z).
    Per matched pair and joint: predicted RMSE = rms of v_nom(t_rel + delta_mean) * (delta_B - delta_Z) over the curve grid vs the observed RMSE."""
    out = {"model": "q_act(t_ref + t_rel) = f(t_rel + delta), delta = t_ref - t_start_fit; difference B-Z ~ f'(t_rel) * (delta_B - delta_Z), f' = cubic speed profile of the case",
           "pairs": []}
    for case in sorted({r.case for r in runs if r.case != "H"}):
        dq = np.array(cfg_cases[case]["dq"], dtype=float)
        T = float(cfg_cases[case]["T"])
        B = {r.round: r for r in runs if r.case == case and r.cond == "B"}
        Z = {r.round: r for r in runs if r.case == case and r.cond == "Z"}
        for rd in sorted(set(B) & set(Z)):
            b, z = B[rd], Z[rd]
            db, dz = b.m["delay"]["t_ref_minus_t_start_fit_s"], z.m["delay"]["t_ref_minus_t_start_fit_s"]
            t_rel = b.curves["t_rel"]
            ok = np.all(np.isfinite(b.curves["q_act"] - z.curves["q_act"]), axis=1)
            tau_ = t_rel + 0.5 * (db + dz)
            u = tau_ / T
            v = np.where((u >= 0) & (u <= 1), 6 * u * (1 - u) / T, 0.0)
            pred = np.sqrt(np.mean((v[ok][:, None] * dq[None, :] * (db - dz)) ** 2, axis=0))
            obs = np.sqrt(np.mean((b.curves["q_act"][ok] - z.curves["q_act"][ok]) ** 2, axis=0))
            moving = np.abs(dq) > 0
            ratio = (obs[moving] / pred[moving]).tolist()
            out["pairs"].append({"case": case, "round": rd, "delta_B_s": db, "delta_Z_s": dz, "delta_difference_s": db - dz,
                                 "observed_rmse_rad": obs.tolist(), "predicted_rmse_rad": pred.tolist(), "observed_over_predicted_per_moving_joint": ratio})
    allr = [x for p in out["pairs"] for x in p["observed_over_predicted_per_moving_joint"]]
    if allr:
        out["observed_over_predicted_min"], out["observed_over_predicted_max"] = float(min(allr)), float(max(allr))
    return out


def nonzero_servo(rows, gcfg):
    g = gcfg["nonzero_servo"]
    out = {"gates": g, "items": [], "note": "D80/D160 vs the B run of the SAME round and case, controller-axis motion window; increase = cond - B (negative is fine)"}
    for r in rows:
        if r["case"] == "H" or r["condition"] not in ("D80", "D160"):
            continue
        b = [x for x in rows if x["case"] == r["case"] and x["condition"] == "B" and x["round"] == r["round"]]
        if not b:
            out["items"].append({"run_id": r["run_id"], "error": "no same-round B run"})
            continue
        b = b[0]
        inc_rmse = (np.array(r["motion_e_servo_rmse"]) - np.array(b["motion_e_servo_rmse"]))
        inc_peak = (np.array(r["motion_e_servo_max"]) - np.array(b["motion_e_servo_max"]))
        out["items"].append({"run_id": r["run_id"], "case": r["case"], "condition": r["condition"], "round": r["round"], "b_run": b["run_id"],
                             "rmse_increase_rad": inc_rmse.tolist(), "peak_increase_rad": inc_peak.tolist(),
                             "pass": bool(inc_rmse.max() <= g["e_servo_rmse_increase_rad_max"] and inc_peak.max() <= g["e_servo_peak_increase_rad_max"])})
    out["pass"] = bool(out["items"]) and all(i.get("pass") for i in out["items"])
    return out


def dose_table(rows):
    """Per (case, condition): mean over rounds of the original-axis totals; ratios relative to B."""
    out = {}
    for case in sorted({r["case"] for r in rows if r["case"] != "H"}):
        ent = {}
        base = [r for r in rows if r["case"] == case and r["condition"] == "B"]
        for cond in CONDS:
            sel = [r for r in rows if r["case"] == case and r["condition"] == cond]
            if not sel:
                continue
            tot = np.array([r["exec_nom_e_total_rmse"] for r in sel]).mean(axis=0)
            pos = np.array([r["exec_nom_ee_pos_total_m_rmse"] for r in sel]).mean()
            pkp = np.array([r["exec_nom_ee_pos_total_m_max"] for r in sel]).mean()
            peak = np.array([r["exec_nom_e_total_max"] for r in sel]).mean(axis=0)
            ent[cond] = {"n": len(sel), "exec_nom_e_total_rmse_mean": tot.tolist(), "exec_nom_e_total_max_mean": peak.tolist(), "exec_nom_ee_pos_total_rmse_m_mean": float(pos),
                         "exec_nom_ee_pos_total_peak_m_mean": float(pkp), "t_ref_minus_send_before_mean_s": float(np.mean([r["t_ref_minus_send_before_s"] for r in sel]))}
        if base and "B" in ent:
            for cond in ent:
                ent[cond]["rmse_ratio_vs_B_per_joint"] = (np.array(ent[cond]["exec_nom_e_total_rmse_mean"]) / np.array(ent["B"]["exec_nom_e_total_rmse_mean"])).tolist()
                ent[cond]["pos_rmse_ratio_vs_B"] = ent[cond]["exec_nom_ee_pos_total_rmse_m_mean"] / ent["B"]["exec_nom_ee_pos_total_rmse_m_mean"]
        out[case] = ent
    return out


def load_task1_curves(path):
    """{case: {run_id: curves}} from a Task1 analysis directory (t1.9-a3/runs); formal rounds only (no hf runs)."""
    out = {}
    if not path or not os.path.isdir(path):
        return out
    for rid in sorted(os.listdir(path)):
        if "-hf-" in rid:
            continue
        cp = os.path.join(path, rid, "curves.npz")
        mp = os.path.join(path, rid, "run_metrics.json")
        if not (os.path.exists(cp) and os.path.exists(mp)):
            continue
        case = jl(mp)["case"]
        if case in ("M3", "M6", "MR3"):
            out.setdefault(case, {})[rid] = dict(np.load(cp))
    return out


# ------------------------------------------------------------------------------------------------------------ figures
def figures(runs, rows, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fd = os.path.join(outdir, "figures")
    os.makedirs(fd, exist_ok=True)
    colors = {"B": "#1f77b4", "Z": "#2ca02c", "D80": "#ff7f0e", "D160": "#d62728"}
    done = []
    for case in sorted({r.case for r in runs if r.case != "H"}):
        rnd = min(r.round for r in runs if r.case == case)
        sel = {r.cond: r for r in runs if r.case == case and r.round == rnd}
        if not sel:
            continue
        ji = int(np.argmax(np.abs(np.array(next(iter(sel.values())).m["metrics"]["motion"]["e_total"]["mean"]) * 0 + 1) * [abs(x) for x in __import__("yaml").safe_load(open(CONFIG))["cases"][case]["dq"]]))
        fig, ax = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
        for cond, r in sel.items():
            c = r.curves
            if "snd_t_rel" not in c:
                continue
            t = c["snd_t_rel"]
            ax[0].plot(t, c["snd_q_act"][:, ji] - c["snd_q_act"][0, ji], color=colors[cond], lw=1.2, label="actual %s" % cond)
            ax[0].plot(t, c["snd_q_ref"][:, ji] - c["snd_q_ref"][0, ji], color=colors[cond], lw=0.8, ls="--")
            ax[1].plot(t, c["snd_e_total"][:, ji], color=colors[cond], label=cond)
            ax[2].plot(t, c["snd_e_servo"][:, ji], color=colors[cond], label="e_servo %s" % cond)
            ev = r.m["delay"].get("queue")
            if ev:
                t0 = r.m["delay"]["t0_mid_s"]
                for nm, key, ls in (("t_in", "t_in_ns", ":"), ("t_due", "t_due_ns", "-."), ):
                    ax[0].axvline(ev[key] / 1e9 - t0, color=colors[cond], ls=ls, lw=0.6)
                ax[0].axvline(r.m["delay"]["t_ref_s"] - t0, color=colors[cond], ls="-", lw=0.6)
        c0 = next(iter(sel.values())).curves
        if "snd_q_nom" in c0:
            ax[0].plot(c0["snd_t_rel"], c0["snd_q_nom"][:, ji] - c0["snd_q_nom"][0, ji], color="k", lw=1.5, label="q_nom (original schedule)")
        ax[0].set_ylabel("%s [rad, rel.]\nsolid=actual dashed=q_ref" % J[ji]); ax[1].set_ylabel("e_total = q_actual - q_nom [rad]"); ax[2].set_ylabel("e_servo = q_actual - q_ref [rad]")
        ax[2].set_xlabel("time since sender t0 [s] (original-send axis; dotted/dash-dot/solid vertical = t_in/t_due/t_ref)")
        ax[0].legend(fontsize=7, ncol=3); ax[1].legend(fontsize=7, ncol=4)
        ax[0].set_title("%s round %s: original-send axis, joint %s" % (case, rnd, J[ji]))
        fig.tight_layout(); p = os.path.join(fd, "send_axis_%s.png" % case); fig.savefig(p, dpi=110); plt.close(fig); done.append(p)
        fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
        for r in runs:
            if r.case != case:
                continue
            c = r.curves
            ax[0].plot(c["t_rel"], c["e_q"][:, ji], color=colors[r.cond], lw=0.8, alpha=0.8, label="%s r%s" % (r.cond, r.round))
            ax[1].plot(c["t_rel"], c["ee_pos_err"] * 1e3, color=colors[r.cond], lw=0.8, alpha=0.8)
        ax[0].set_ylabel("e_servo %s [rad]" % J[ji]); ax[1].set_ylabel("|FK(act)-FK(ref)| [mm]"); ax[1].set_xlabel("time since t_ref [s] (controller axis)")
        ax[0].legend(fontsize=6, ncol=4); ax[0].set_title("%s: servo error aligned on t_ref, all runs" % case)
        fig.tight_layout(); p = os.path.join(fd, "controller_axis_%s.png" % case); fig.savefig(p, dpi=110); plt.close(fig); done.append(p)
    fig, ax = plt.subplots(figsize=(9, 5))
    cases = sorted({r["case"] for r in rows if r["case"] != "H"})
    w = 0.2
    for k, cond in enumerate(CONDS):
        vals = []
        for case in cases:
            sel = [r["exec_nom_ee_pos_total_m_rmse"] for r in rows if r["case"] == case and r["condition"] == cond]
            vals.append(np.mean(sel) * 1e3 if sel else np.nan)
        ax.bar(np.arange(len(cases)) + (k - 1.5) * w, vals, w, color=colors[cond], label=cond)
    ax.set_xticks(np.arange(len(cases))); ax.set_xticklabels(cases); ax.set_ylabel("end-effector |FK(act)-FK(q_nom)| RMSE, exec window [mm], mean over rounds"); ax.legend()
    fig.tight_layout(); p = os.path.join(fd, "dose_ee_total.png"); fig.savefig(p, dpi=110); plt.close(fig); done.append(p)
    return done


# ------------------------------------------------------------------------------------------------------------ main
def fmt(x, nd=5):
    return "n/a" if x is None else ("%.*g" % (nd, x))


def write_summary_md(path, idx, rows, groups, eq, nz, rep, dose, failures, an_id, stage):
    L_ = ["# Aggregate %s (%s, aggregator %s)\n" % (an_id, stage, AGG_VERSION),
          "Index: matrix `%s`, freeze `%s`; valid runs analysed: %d of %d attempts; failures listed in failures.json.\n" % (idx["matrix_id"], idx["freeze_id"], len(rows), len(idx["runs"]))]
    for title, e_all in (("Protocol v1 (as pre-registered): curves aligned on the threshold t_ref", eq["protocol_v1_t_ref"]),
                         ("Protocol v1.1 amendment (post-data): curves aligned on the sub-sample fitted start; SAME numeric limits", eq["protocol_v1_1_fit"])):
        L_.append("## B vs Z equivalence - %s: %s\n" % (title, "ALL GROUPS PASS" if e_all["pass"] else "NOT MET"))
        L_.append("q_actual group comparisons failing the limit: %d of %d\n" % (e_all["q_actual_failed_group_comparisons"], e_all["n_group_comparisons"]))
        for case, e in e_all["cases"].items():
            L_.append("- **%s**: %s; t_ref-t_send median B=%s Z=%s diff=%s s (limit %s)" % (case, "PASS" if e["pass"] else "FAIL", fmt(e["t_ref_minus_send_median_s"]["B"]),
                                                                                       fmt(e["t_ref_minus_send_median_s"]["Z"]), fmt(e["t_ref_minus_send_median_diff_s"]), fmt(e_all["gates"]["t_ref_minus_send_median_diff_s_max"])))
            for n, c in e["curves"].items():
                L_.append("  - %s: matched-round max RMSE %s (limit %s), peak %s (limit %s) -> %s; within-B max RMSE %s, within-Z %s" %
                          (n, fmt(c["matched_max_rmse"]), fmt(c["limit_rmse"]), fmt(c["matched_max_peak"]), fmt(c["limit_peak"]), "pass" if c["pass"] else "FAIL",
                           fmt(c["within_B_pairs_max_rmse"]), fmt(c["within_Z_pairs_max_rmse"])))
        L_.append("")
    ex = eq.get("alignment_explanation", {})
    if "observed_over_predicted_min" in ex:
        L_.append("t_ref-alignment explanation: observed/predicted q_actual RMSE (quantisation shift x speed) per moving joint ranges %s .. %s over all matched pairs.\n" %
                  (fmt(ex["observed_over_predicted_min"], 5), fmt(ex["observed_over_predicted_max"], 5)))
    L_.append("\n## Non-zero delay: servo error vs same-round B\n")
    for it in nz["items"]:
        if "error" in it:
            L_.append("- %s: %s" % (it["run_id"], it["error"])); continue
        L_.append("- %s %s r%s: max RMSE increase %s rad, max peak increase %s rad -> %s" % (it["case"], it["condition"], it["round"], fmt(max(it["rmse_increase_rad"])), fmt(max(it["peak_increase_rad"])), "pass" if it["pass"] else "FAIL"))
    L_.append("\n## Original-axis error (exec window, mean over rounds; EE position |FK(act)-FK(q_nom)| in mm)\n")
    L_.append("|case|cond|n|EE pos RMSE mm|EE pos peak mm|max-joint e_total RMSE mrad|t_ref-t_send mean ms|")
    L_.append("|---|---|---|---|---|---|---|")
    for case, ent in dose.items():
        for cond, v in ent.items():
            L_.append("|%s|%s|%d|%s|%s|%s|%s|" % (case, cond, v["n"], fmt(v["exec_nom_ee_pos_total_rmse_m_mean"] * 1e3, 4), fmt(v["exec_nom_ee_pos_total_peak_m_mean"] * 1e3, 4),
                                                 fmt(max(v["exec_nom_e_total_rmse_mean"]) * 1e3, 4), fmt(v["t_ref_minus_send_before_mean_s"] * 1e3, 4)))
    L_.append("\n## Repeatability (across rounds)\n")
    for k, v in rep.items():
        L_.append("- %s: t_ref offset range %s ms (limit %s) %s; joints with insufficient e_total repeatability: %s" % (
            k, fmt(v["t_ref_minus_send_before_range_s"] * 1e3, 4), fmt(v["t_ref_offset_limit_s"] * 1e3, 3), "INSUFFICIENT" if v["t_ref_offset_insufficient"] else "ok", v["joints_with_insufficient_repeatability"] or "none"))
    L_.append("\n## Failures / exclusions\n")
    L_.append("- attempts not valid: %d (see failures.json); runs excluded from statistics are never replaced silently." % len(failures))
    open(path, "w").write("\n".join(L_) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--analysis-id", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--task1-curves", default=os.path.join(ROOT, "results", "task1", "t1.9-a3", "runs"))
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--config", default=CONFIG)
    a = ap.parse_args()
    if os.path.exists(a.out):
        print("refused: %s exists (analyses are never overwritten)" % a.out)
        sys.exit(12)
    cfg = yaml.safe_load(open(a.config))
    gcfg = cfg["gates"]
    idx = jl(a.index)
    stage = idx.get("stage", "unknown")
    os.makedirs(a.out)
    all_runs = [Run(rec, ROOT) for rec in idx["runs"]]
    runs = [r for r in all_runs if r.valid and r.role != "hf_diagnostic"]
    hf_runs = [r for r in all_runs if r.valid and r.role == "hf_diagnostic"]
    failures = [{"run_id": r.id, "case": r.case, "condition": r.cond, "round": r.round, "role": r.role, "attempt": r.rec.get("attempt"), "retry_of": r.rec.get("retry_of"),
                 "entry_exit": r.rec.get("entry_exit"), "failed_gates": r.rec.get("failed_gates"), "invalid_reasons": r.rec.get("invalid_reasons")} for r in all_runs if not r.valid]
    rows = [per_run_row(r) for r in runs]
    hist = load_task1_curves(a.task1_curves)
    groups = group_stats(rows)
    eq_tref = equivalence_bz(runs, rows, gcfg, hist, "t_ref")
    eq_fit = equivalence_bz(runs, rows, gcfg, hist, "fit")
    expl = alignment_explanation(runs, cfg["cases"]) if runs else {}
    eq = {"protocol_v1_t_ref": eq_tref, "protocol_v1_1_fit": eq_fit, "alignment_explanation": expl,
          "labels": {"protocol_v1_t_ref": "protocol v1 as pre-registered: threshold t_ref alignment",
                     "protocol_v1_1_fit": "protocol v1.1 amendment adopted AFTER the formal data were seen (the fit code itself predates the pilot, see task2.3 RESULTS); same numeric limits"}}
    nz = nonzero_servo(rows, gcfg)
    rep = repeatability(rows, gcfg)
    dose = dose_table(rows)
    hf_rows = [per_run_row(r) for r in hf_runs]
    summary = {"analysis_id": a.analysis_id, "aggregator_version": AGG_VERSION, "stage": stage, "index": os.path.abspath(a.index), "index_sha256": sha(a.index),
               "matrix_id": idx["matrix_id"], "freeze_id": idx["freeze_id"], "config_sha256": sha(a.config),
               "n_attempts": len(all_runs), "n_valid_125hz": len(runs), "n_valid_hf": len(hf_runs), "n_invalid_attempts": len(failures),
               "gates": ({"equivalence_bz_protocol_v1_t_ref": eq_tref["pass"], "equivalence_bz_protocol_v1_1_fit": eq_fit["pass"], "nonzero_servo": nz["pass"]} if runs else
                         {"equivalence_bz_protocol_v1_t_ref": None, "equivalence_bz_protocol_v1_1_fit": None, "nonzero_servo": None, "note": "no valid 125 Hz runs in this index: gates not evaluable"}),
               "repeatability_insufficient": {k: bool(v["t_ref_offset_insufficient"] or v["joints_with_insufficient_repeatability"]) for k, v in rep.items()},
               "note": "descriptive statistics, n=3 rounds; gate results are reported as found, never repaired; the research hypothesis is judged in exp2.1 RESULTS"}
    out = {"run_index_used.json": idx, "per_run.json": rows, "hf_diagnostic_runs.json": hf_rows, "groups.json": groups, "equivalence_bz.json": eq, "nonzero_servo.json": nz,
           "repeatability.json": rep, "dose.json": dose, "failures.json": failures, "summary.json": summary}
    for name, obj in out.items():
        with open(os.path.join(a.out, name), "w") as f:
            json.dump(obj, f, indent=1, default=float)
    flat = [{k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in r.items()} for r in rows]
    if flat:
        with open(os.path.join(a.out, "per_run.csv"), "w", newline="") as f:
            keys = sorted({k for r in flat for k in r})
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader(); w.writerows(flat)
    write_summary_md(os.path.join(a.out, "summary.md"), idx, rows, groups, eq, nz, rep, dose, failures, a.analysis_id, stage)
    if not a.no_figures and runs:
        try:
            figures(runs, rows, a.out)
        except Exception as e:  # noqa: BLE001 - figures never decide a gate; the failure is recorded
            open(os.path.join(a.out, "figures_error.txt"), "w").write(repr(e))
    print(json.dumps({"analysis_id": a.analysis_id, "out": a.out, "valid": len(runs), "invalid_attempts": len(failures), "gates": summary["gates"]}))


if __name__ == "__main__":
    main()
