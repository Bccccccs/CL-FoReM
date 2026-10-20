#!/usr/bin/env python3
"""Task1 per-run analysis: data quality gates + tracking error metrics (runs in forem-dev; needs numpy, PyYAML).

  analyze_task1.py run --run-dir results/task1/<run-id> [--hf]      -> run_metrics.json, curves.npz
  analyze_task1.py aggregate --index results/task1/<matrix>/run_index.json --out DIR   (task1.4; see that section)

Inputs in the run dir: raw/*.csv (task1_bag_to_csv.py), commands.json (collect_task1.py), robot_description.urdf.
Exit: 0 every quality gate passed; 1 a gate failed (metrics are still written, marked invalid); 2 input unusable.

Errors: e_q = actual - desired and e_v = actual_vel - desired_vel, from the SAME controller state message.
The controller's own `error` field is kept only as a cross-check (ROS defines it as desired - actual).
Thresholds and windows come from the frozen config/experiments/task1/baseline.yaml. They are measurement-quality
gates, not accuracy requirements of the arm.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task1_lib as L  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CONFIG = os.path.join(ROOT, "config", "experiments", "task1", "baseline.yaml")
J = L.JOINTS
ANALYSIS_VERSION = "task1.9-1"   # task1.4 original analysis has no marker ("task1.4-original")


def _json(path):
    with open(path) as f:
        return json.load(f)


def _text(path):
    with open(path) as f:
        return f.read()


def load_csv(path, required):
    if not os.path.exists(path):
        raise L.InvalidInput("missing %s" % path)
    with open(path) as f:
        header = f.readline().strip().split(",")
    miss = [c for c in required if c not in header]
    if miss:
        raise L.InvalidInput("%s lacks columns %s" % (path, miss))
    a = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    if a.size == 0:
        raise L.InvalidInput("%s has no rows" % path)
    if a.shape[1] != len(header):
        raise L.InvalidInput("%s: %d columns, header has %d" % (path, a.shape[1], len(header)))
    if not np.all(np.isfinite(a)):
        raise L.InvalidInput("%s contains non-finite values" % path)
    return {h: a[:, i] for i, h in enumerate(header)}


def cols(d, prefix):
    return np.stack([d[prefix + j] for j in J], axis=1)


def urdf_vel_limits(urdf):
    import xml.etree.ElementTree as ET
    out = {}
    for j in ET.fromstring(urdf).findall("joint"):
        if j.get("name") in J:
            out[j.get("name")] = float(j.find("limit").get("velocity"))
    return out


def urdf_pos_limits(urdf):
    import xml.etree.ElementTree as ET
    out = {}
    for j in ET.fromstring(urdf).findall("joint"):
        if j.get("name") in J:
            l = j.find("limit")
            out[j.get("name")] = (float(l.get("lower")), float(l.get("upper")))
    return out


def cubic(u):
    u = np.clip(u, 0.0, 1.0)
    return 3 * u * u - 2 * u ** 3


# ------------------------------------------------------------------ checks used by `run`
def check_js_consistency(t_c, q_c, t_j, q_j, vlim, q_cfg):
    """controller actual vs joint_states, nearest neighbour within js_pair_dt_max_s."""
    pick, dt = L.nearest_pairs(t_c, t_j, q_cfg["js_pair_dt_max_s"])
    ok = pick >= 0
    res = {"controller_samples": int(t_c.size), "paired": int(ok.sum()), "pair_rate": float(ok.mean()) if t_c.size else 0.0,
           "pair_rate_min": q_cfg["js_pair_rate_min"], "dt_abs_max_s": float(np.max(np.abs(dt[ok]))) if ok.any() else None,
           "dt_zero_pairs": int(np.sum(dt[ok] == 0))}
    vb = max(vlim.values())
    diff = np.abs(q_j[pick[ok]] - q_c[ok])
    bound = q_cfg["js_pos_tol_rad"] + vb * np.abs(dt[ok])[:, None]
    res["max_abs_pos_diff_rad"] = float(diff.max()) if diff.size else None
    res["violations"] = int(np.sum(diff > bound))
    res["max_abs_pos_diff_at_dt0_rad"] = float(diff[dt[ok] == 0].max()) if np.any(dt[ok] == 0) else None
    res["v_bound_rad_s"] = vb
    res["note"] = "bound = %.0e + v_bound*|dt| with v_bound the URDF velocity limit (loose when dt>0); an interface check, not proof of sensor independence" % q_cfg["js_pos_tol_rad"]
    res["pass"] = bool(res["pair_rate"] >= q_cfg["js_pair_rate_min"] and res["violations"] == 0)
    return res


def check_truth(chain, vlim, t_c, q_act, qd_act, truth, q_cfg, frame_cfg):
    """FK(controller actual) versus the Gazebo link transform base->tip at nearest link sample (t_bag)."""
    tl = truth["t_bag"]
    pick, dt = L.nearest_pairs(t_c, tl, q_cfg["truth_dt_max_s"])
    ok = np.nonzero(pick >= 0)[0]
    res = {"pairs": int(ok.size), "pairs_min": q_cfg["truth_pairs_min"], "frames": frame_cfg}
    if ok.size == 0:
        res["pass"] = False
        res["reason"] = "no pairs within %.0f ms" % (q_cfg["truth_dt_max_s"] * 1e3)
        return res
    k = pick[ok]
    # task1.7: every Gazebo quaternion of the run must be finite with a usable norm, else the truth stream is unusable
    qcols = [("b_qx", "b_qy", "b_qz", "b_qw"), ("t_qx", "t_qy", "t_qz", "t_qw")]
    with np.errstate(over="ignore", invalid="ignore"):   # finite components can still overflow the norm to Inf
        norms = [np.linalg.norm(np.stack([truth[c] for c in cs], axis=1), axis=1) for cs in qcols]
    res["quat_norm"] = {"base_min": float(norms[0].min()), "base_max": float(norms[0].max()), "tip_min": float(norms[1].min()), "tip_max": float(norms[1].max()),
                        "min_allowed": L.QUAT_NORM_MIN}
    # task1.9: a row is valid only if its norm is finite AND >= QUAT_NORM_MIN (Inf >= min is true, so >= alone misses overflow);
    # this runs over ALL rows of the stream, not only the nearest-neighbour pairs used below
    bad_rows = [int(np.sum(~(np.isfinite(n) & (n >= L.QUAT_NORM_MIN)))) for n in norms]
    res["quat_bad_rows"] = {"base": bad_rows[0], "tip": bad_rows[1]}
    if any(bad_rows):
        res.update(reason="Gazebo quaternions with non-finite components, non-finite norm or norm < %g (base %d rows, tip %d rows)" % (L.QUAT_NORM_MIN, *bad_rows))
        res["pass"] = False
        return res
    Rb = np.stack([L.quat_to_R([truth[c][i] for c in qcols[0]]) for i in k])
    Rt = np.stack([L.quat_to_R([truth[c][i] for c in qcols[1]]) for i in k])
    pb = np.stack([truth["b_x"][k], truth["b_y"][k], truth["b_z"][k]], axis=1)
    pt = np.stack([truth["t_x"][k], truth["t_y"][k], truth["t_z"][k]], axis=1)
    p_rel = np.einsum("nji,nj->ni", Rb, pt - pb)       # R_b^T (p_t - p_b)
    R_rel = np.matmul(np.swapaxes(Rb, 1, 2), Rt)
    P, R, _ = L.fk_batch(chain, q_act[ok], with_origins=True)
    pos_err = np.linalg.norm(P - p_rel, axis=1)
    ang_err = L.rot_angle(R, R_rel)
    vb, wb = L.ee_bounds_batch(chain, q_act[ok], vlim)
    absdt = np.abs(dt[ok])
    pos_tol = q_cfg["truth_pos_tol_m"] + vb * absdt
    ang_tol = q_cfg["truth_ang_tol_rad"] + wb * absdt
    # static pairs: measured joint speed ~0 -> the bare tolerances apply (no speed allowance)
    static = np.max(np.abs(qd_act[ok]), axis=1) < 1e-3
    finite = bool(all(np.all(np.isfinite(x)) for x in (p_rel, R_rel, P, R, pos_err, ang_err, vb, wb, pos_tol, ang_tol)))
    res["all_finite"] = finite
    if not finite:
        res["pass"] = False
        res["reason"] = "non-finite transform or error in the truth comparison"
        return res
    res.update({"pos_err_max_m": float(pos_err.max()), "pos_err_rmse_m": float(np.sqrt(np.mean(pos_err ** 2))),
                "ang_err_max_rad": float(ang_err.max()), "ang_err_rmse_rad": float(np.sqrt(np.mean(ang_err ** 2))),
                "dt_abs_max_s": float(absdt.max()), "v_ee_bound_max_m_s": float(vb.max()), "omega_bound_rad_s": float(wb.max()),
                "violations_pos": int(np.sum(pos_err > pos_tol)), "violations_ang": int(np.sum(ang_err > ang_tol)),
                "static_pairs": int(static.sum()),
                "static_pos_err_max_m": float(pos_err[static].max()) if static.any() else None,
                "static_ang_err_max_rad": float(ang_err[static].max()) if static.any() else None,
                "static_violations": int(np.sum((pos_err[static] > q_cfg["truth_pos_tol_m"]) | (ang_err[static] > q_cfg["truth_ang_tol_rad"]))),
                "tolerances": {"pos_m": "%.0e + v_ee_bound*|dt|" % q_cfg["truth_pos_tol_m"], "ang_rad": "%.0e + omega_bound*|dt|" % q_cfg["truth_ang_tol_rad"]},
                "note": "link pose stamps are recorder receive times; the URDF speed bound is loose, so the static-pair check is the tight one"})
    res["pass"] = bool(ok.size >= q_cfg["truth_pairs_min"] and res["violations_pos"] == 0 and res["violations_ang"] == 0 and res["static_violations"] == 0)
    return res


def grid_curves(t, arrays, t_ref, length, grid, nominal, max_gap_periods):
    """Resample onto t_ref + k*grid, k*grid in [0, length], by linear interpolation INSIDE a stream only;
    grid points whose bracketing samples are further apart than max_gap_periods*nominal become NaN."""
    tg = t_ref + np.arange(0, int(round(length / grid)) + 1) * grid
    j = np.clip(np.searchsorted(t, tg), 1, t.size - 1)
    gap_ok = (t[j] - t[j - 1]) <= max_gap_periods * nominal + 1e-9
    inside = (tg >= t[0]) & (tg <= t[-1])
    out = {}
    for name, a in arrays.items():
        a = np.asarray(a, dtype=float)
        if a.ndim == 1:
            y = np.interp(tg, t, a)
        else:
            y = np.stack([np.interp(tg, t, a[:, i]) for i in range(a.shape[1])], axis=1)
        bad = ~(gap_ok & inside)
        y[bad] = np.nan
        out[name] = y
    return tg - t_ref, out


# ------------------------------------------------------------------ run
def analyze_run(run_dir, hf=False, cfg=None):
    cfg = cfg or yaml.safe_load(_text(CONFIG))
    q_cfg = cfg["quality"]
    tmg = cfg["timing"]
    nominal = 1.0 / (tmg["hf_rate_hz"] if hf else tmg["joint_rate_hz"])
    raw = os.path.join(run_dir, "raw")
    cmd = _json(os.path.join(run_dir, "commands.json"))
    urdf = _text(os.path.join(run_dir, "robot_description.urdf"))
    bsum = _json(os.path.join(raw, "bag_summary.json"))
    frames = cfg["robot"]["frames"]
    chain = L.parse_chain(urdf, frames["base"], frames["tip"])
    vlim, plim = urdf_vel_limits(urdf), urdf_pos_limits(urdf)

    st = load_csv(os.path.join(raw, "controller_state.csv"),
                  ["t_header"] + ["%s%s" % (p, j) for p in ("des_", "act_", "err_", "desvel_", "actvel_", "errvel_") for j in J])
    js = load_csv(os.path.join(raw, "joint_states.csv"), ["t_header"] + ["pos_" + j for j in J] + ["vel_" + j for j in J])
    truth = load_csv(os.path.join(raw, "link_truth.csv"), ["t_bag"] + ["b_x", "t_x", "b_qw", "t_qw"])
    clk = load_csv(os.path.join(raw, "clock.csv"), ["t"])

    res = {"analysis_version": ANALYSIS_VERSION, "run_id": cmd["run_id"], "case": cmd["case"], "hf": hf, "nominal_period_s": nominal, "quality": {}, "gates": {}, "invalid_reasons": []}
    gates = res["gates"]

    # --- bag-level integrity
    res["quality"]["bag_summary"] = {k: bsum[k] for k in bsum if k != "rows"}
    gates["bag_integrity"] = bool(bsum["incomplete_joint_states"] == 0 and bsum["incomplete_controller_state"] == 0 and bsum["non_finite_rows"] == 0
                                  and bsum["missing_link_messages"] == 0)
    if "aborted" in cmd:
        gates["run_not_aborted"] = False
        res["invalid_reasons"].append("collector aborted: %s" % cmd["aborted"])
    clk_back = int(np.sum(np.diff(clk["t"]) < 0))
    res["quality"]["clock"] = {"n": int(clk["t"].size), "backward_steps": clk_back}
    gates["clock_monotonic"] = clk_back == 0

    t_c_raw = st["t_header"]
    t_j_raw = js["t_header"]
    rec_t0, rec_t1 = cmd["rec_t0"], cmd["rec_t1"]
    moving = bool(cmd["commands"])

    # --- time order of raw streams, then de-duplicate equal stamps (keep first)
    back_c = int(np.sum(np.diff(t_c_raw) < 0)); back_j = int(np.sum(np.diff(t_j_raw) < 0))
    if back_c or back_j:
        gates["streams_time_ordered"] = False
        res["invalid_reasons"].append("backward timestamps: controller %d joint_states %d" % (back_c, back_j))
        res["gates"]["streams_time_ordered"] = False
    else:
        gates["streams_time_ordered"] = True
    des_all, act_all = cols(st, "des_"), cols(st, "act_")
    errf_all, dv_all, av_all = cols(st, "err_"), cols(st, "desvel_"), cols(st, "actvel_")
    t_c, des, act, errf, dv, av = L.dedupe_sorted(t_c_raw, des_all, act_all, errf_all, dv_all, av_all)
    qj_all = cols(js, "pos_")
    t_j, qj = L.dedupe_sorted(t_j_raw, qj_all)

    # --- windows
    pre = [rec_t0, rec_t0 + tmg["pre_hold_s"]]
    wins = {"pre_hold": pre}
    t_ref = None
    T = None
    if moving:
        c0 = cmd["commands"][0]
        T = c0["duration_s"]
        q_target = np.array(c0["q_target"])
        moving_idx = [i for i, d in enumerate(c0["dq"]) if abs(d) > 0]
        m_pre = (t_c >= pre[1] - 1.0) & (t_c <= pre[1])
        hold_ref = np.median(des[m_pre], axis=0) if m_pre.any() else des[0]
        try:
            t_ref, per_joint = L.find_t_ref(t_c[t_c >= pre[0]], des[t_c >= pre[0]], hold_ref, moving_idx, q_cfg["t_ref_threshold_rad"])
        except L.InvalidInput as e:
            gates["motion_observed"] = False
            res["invalid_reasons"].append(str(e))
            t_ref = None
        if t_ref is not None:
            res["t_ref"] = {"t_ref_s": t_ref, "per_joint": per_joint, "threshold_rad": q_cfg["t_ref_threshold_rad"],
                            "sim_time_before_publish": c0["sim_time_before_publish"], "sim_time_after_publish": c0["sim_time_after_publish"],
                            "t_ref_minus_before_s": t_ref - c0["sim_time_before_publish"], "t_ref_minus_after_s": t_ref - c0["sim_time_after_publish"],
                            "note": "includes ROS transport, update scheduling and sample quantisation; NOT a physical delay"}
            gates["motion_observed"] = True
            gates["t_ref_not_before_send"] = bool(t_ref >= c0["sim_time_before_publish"] - 1e-9)
            wins["motion"] = [t_ref, t_ref + T]
            wins["settle"] = [t_ref + T, t_ref + T + tmg["settle_s"]]
            res["q_start_vs_hold_ref"] = {"hold_ref_desired": hold_ref.tolist(), "q_start_observed": c0["q_start_observed"],
                                          "q_start_minus_q_init": c0["q_start_minus_q_init"]}
    else:
        wins["hold"] = [rec_t0 + tmg["pre_hold_s"], rec_t0 + tmg["pre_hold_s"] + tmg["hold_s"]]
        hold_ref = None
    res["windows"] = wins
    if moving and t_ref is None:
        res["pass"] = False
        res["invalid_reasons"].append("no windows without observed motion")
        return _finish(run_dir, res, gates, None, hf)

    # --- stream quality per window
    for wn, (w0, w1) in wins.items():
        if hf:
            qc = L.stream_quality(t_c_raw, w0, w1, nominal, max_gap_periods=1e9, dedup_rate_max=q_cfg["dedup_rate_max"], coverage_min=0.0)
            qj_ = L.stream_quality(t_j_raw, w0, w1, nominal, max_gap_periods=1e9, dedup_rate_max=q_cfg["dedup_rate_max"], coverage_min=0.0)
        else:
            qc = L.stream_quality(t_c_raw, w0, w1, nominal, q_cfg["max_gap_periods"], q_cfg["dedup_rate_max"], q_cfg["window_coverage_min"])
            qj_ = L.stream_quality(t_j_raw, w0, w1, nominal, q_cfg["max_gap_periods"], q_cfg["dedup_rate_max"], q_cfg["window_coverage_min"])
        res["quality"][wn] = {"controller_state": qc, "joint_states": qj_}
        gates["quality_%s_controller" % wn] = bool(qc["pass"])
        gates["quality_%s_joint_states" % wn] = bool(qj_["pass"])
    if hf:
        res["quality"]["hf_note"] = "gap/coverage gates are replaced by the task0.7 consecutive-step criteria (evaluate_hf_windows.py); ~9% of 2 kHz samples are not published"

    # --- source audit and interpolation check
    full = (t_c >= rec_t0) & (t_c <= rec_t1)
    audit_w = wins.get("motion") or wins["hold"]
    mw = (t_c >= audit_w[0]) & (t_c <= audit_w[1])
    js_near, _ = L.nearest_pairs(t_c[mw], t_j, q_cfg["js_pair_dt_max_s"])
    js_pos_in = qj[js_near[js_near >= 0]] if (js_near >= 0).any() else None
    target_vec = np.array(cmd["commands"][0]["q_target"]) if moving else None
    aud = L.audit_backfill(act[mw], des[mw], js_pos=None if js_pos_in is None or js_pos_in.shape != des[mw].shape else js_pos_in, target=target_vec)
    # controller error field sign convention: expected error = desired - actual
    e_field = float(np.max(np.abs(errf[full] - (des[full] - act[full])))) if full.any() else None
    e_field_flip = float(np.max(np.abs(errf[full] - (act[full] - des[full])))) if full.any() else None
    aud["controller_error_field"] = {"max_abs_err_minus_(des-act)": e_field, "max_abs_err_minus_(act-des)": e_field_flip,
                                     "convention": "desired - actual" if (e_field is not None and e_field < 1e-9) else "unexpected"}
    res["quality"]["source_audit"] = aud
    gates["actual_not_backfilled"] = bool(aud["pass"])
    gates["error_field_convention_checked"] = bool(e_field is not None and e_field < 1e-9)
    if moving:
        bagc = _json(os.path.join(raw, "bag_commands.json"))
        c0 = cmd["commands"][0]
        cmpres = L.compare_commands(c0["message"], bagc)   # task1.7: header, joint_names and EVERY field of EVERY point
        res["quality"]["commands_match_bag"] = cmpres
        gates["commands_match_bag"] = bool(cmpres["match"])
        # interpolation: controller desired vs cubic(hold_ref -> q_target), start time fitted on a fine ladder
        mm = (t_c >= t_ref - 0.05) & (t_c <= t_ref + T + 0.05)
        best = None
        for ts in t_ref + np.arange(-0.03, 0.0301, 0.0005):
            model = hold_ref + (q_target - hold_ref) * cubic(((t_c[mm] - ts) / T))[:, None]
            r = float(np.max(np.abs(des[mm] - model)))
            if best is None or r < best[1]:
                best = (float(ts), r)
        end_res = float(np.max(np.abs(des[(t_c >= t_ref + T + 0.05) & (t_c <= t_ref + T + 1.0)] - q_target)))
        res["quality"]["interpolation"] = {"model": "hold_ref + (q_target-hold_ref)*(3u^2-2u^3)", "fitted_start_s": best[0],
                                           "max_abs_residual_rad": best[1], "end_value_residual_rad": end_res,
                                           "fitted_start_minus_t_ref_s": best[0] - t_ref, "tolerance_rad": 1e-5}
        gates["interpolation_matches_cubic"] = bool(best[1] < 1e-5 and end_res < 1e-6)

    # --- cross checks: joint_states and Gazebo truth
    cw = (t_c >= rec_t0) & (t_c <= rec_t1)
    res["quality"]["joint_states_vs_controller"] = check_js_consistency(t_c[cw], act[cw], t_j, qj, vlim, q_cfg)
    gates["joint_states_consistent"] = res["quality"]["joint_states_vs_controller"]["pass"]
    res["quality"]["gazebo_truth"] = check_truth(chain, vlim, t_c[cw], act[cw], av[cw], truth, q_cfg,
                                                 {"base": frames["gazebo_base"], "tip": frames["gazebo_tip"], "urdf_base": frames["base"], "urdf_tip": frames["tip"]})
    gates["gazebo_truth_consistent"] = res["quality"]["gazebo_truth"]["pass"]

    # --- base drift and limits
    bs, be = np.array(cmd["base_pose_start"]), np.array(cmd["base_pose_end"])
    dpos = float(np.linalg.norm(bs[:3] - be[:3]))
    try:
        dang = float(L.rot_angle(L.quat_to_R(bs[3:]), L.quat_to_R(be[3:])))
        drift_reason = None
    except L.InvalidInput as e:   # task1.7: a zero / non-finite base quaternion cannot show that the base stayed fixed
        dang, drift_reason = float("nan"), str(e)
    res["quality"]["base_drift"] = {"position_m": dpos, "rotation_rad": dang, "max": q_cfg["base_drift_max"], "invalid_quaternion": drift_reason}
    gates["base_fixed"] = bool(drift_reason is None and math.isfinite(dpos) and math.isfinite(dang) and dpos <= q_cfg["base_drift_max"] and dang <= q_cfg["base_drift_max"])
    lim_ok = all(plim[j][0] <= act[cw, i].min() and act[cw, i].max() <= plim[j][1] for i, j in enumerate(J))
    res["quality"]["joint_limits"] = {"within_urdf_limits": bool(lim_ok), "q_min": act[cw].min(axis=0).tolist(), "q_max": act[cw].max(axis=0).tolist()}
    gates["within_joint_limits"] = bool(lim_ok)

    # --- metrics per window
    Pa, Ra = L.fk_batch(chain, act[cw])
    Pd, Rd = L.fk_batch(chain, des[cw])
    ee_pos = np.linalg.norm(Pa - Pd, axis=1)
    ee_rot = L.rot_angle(Ra, Rd)
    tcw = t_c[cw]
    metrics = {}
    for wn, (w0, w1) in wins.items():
        m = (tcw >= w0) & (tcw <= w1)
        if m.sum() < 3:
            metrics[wn] = {"error": "fewer than 3 samples"}
            continue
        eq = act[cw][m] - des[cw][m]
        ev = av[cw][m] - dv[cw][m]
        ent = {"window": [w0, w1], "e_q": L.error_stats(eq, tcw[m]), "e_v": L.error_stats(ev, tcw[m]),
               "ee_pos_err_m": L.scalar_stats(ee_pos[m]), "ee_rot_err_rad": L.scalar_stats(ee_rot[m]),
               "joint_order": J}
        if wn in ("pre_hold", "hold", "settle"):
            qa = act[cw][m]
            ent["hold"] = {"pos_peak_to_peak_rad": np.ptp(qa, axis=0).tolist(), "vel_rms_rad_s": np.sqrt(np.mean(av[cw][m] ** 2, axis=0)).tolist()}
        if wn == "settle":
            fm = tcw[m] >= w1 - 1.0
            ent["final_1s"] = {"e_q_mean": np.mean(eq[fm], axis=0).tolist(), "ee_pos_err_mean_m": float(np.mean(ee_pos[m][fm])),
                               "final_minus_target_rad": (act[cw][m][fm].mean(axis=0) - q_target).tolist() if moving else None}
        metrics[wn] = ent
    res["metrics"] = metrics

    # --- lag diagnostic (moving joints only)
    lag = {}
    if moving:
        for i in moving_idx:
            lag[J[i]] = L.lag_estimate(t_c, dv[:, i], av[:, i], t_ref, t_ref + T + 1.0, grid=(nominal if hf else q_cfg["grid_s"]), search=q_cfg["lag_search_s"])
            lag[J[i]].update({"joint": J[i], "sampling_hz": 1.0 / nominal})
    res["lag"] = lag

    # --- aligned curves on the 8 ms grid
    if moving:
        length = T + tmg["settle_s"]
        ref = t_ref
    else:
        length = tmg["hold_s"]
        ref = wins["hold"][0]
    arrays = {}
    e_all = act - des
    ev_all = av - dv
    Pa_all, Ra_all = L.fk_batch(chain, act)
    Pd_all, Rd_all = L.fk_batch(chain, des)
    arrays["e_q"] = e_all
    arrays["e_v"] = ev_all
    arrays["ee_pos_err"] = np.linalg.norm(Pa_all - Pd_all, axis=1)
    arrays["ee_rot_err"] = L.rot_angle(Ra_all, Rd_all)
    tg, curves = grid_curves(t_c, arrays, ref, length, q_cfg["grid_s"], nominal, q_cfg["max_gap_periods"] if not hf else 1e9)
    np.savez_compressed(os.path.join(run_dir, "curves.npz"), t_rel=tg, t_ref=ref, joints=np.array(J), **curves)
    res["curves"] = {"file": "curves.npz", "grid_s": q_cfg["grid_s"], "length_s": length, "origin": "t_ref" if moving else "hold window start",
                     "nan_fraction": float(np.mean(np.isnan(curves["e_q"][:, 0])))}
    return _finish(run_dir, res, gates, moving, hf)


def _finish(run_dir, res, gates, moving, hf):
    res["pass"] = bool(all(gates.values()))
    res["failed_gates"] = [k for k, v in gates.items() if not v]
    res["note"] = "pass = every measurement-quality gate passed; it says nothing about how accurate the arm is"
    with open(os.path.join(run_dir, "run_metrics.json"), "w") as f:
        json.dump(res, f, indent=1, default=float)
    return res


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--run-dir", required=True)
    r.add_argument("--hf", action="store_true")
    r.add_argument("--config", default=CONFIG)
    a = ap.parse_args()
    try:
        res = analyze_run(a.run_dir, a.hf, yaml.safe_load(_text(a.config)))
    except (L.InvalidInput, OSError, KeyError, ValueError) as e:
        print("INVALID INPUT:", e)
        sys.exit(2)
    print(json.dumps({"run_id": res["run_id"], "pass": res["pass"], "failed_gates": res["failed_gates"], "invalid_reasons": res["invalid_reasons"]}, indent=1))
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
