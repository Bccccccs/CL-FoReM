#!/usr/bin/env python3
"""Task2 per-run analysis: command-chain audit, data-quality gates, original-send-axis and controller-axis error decomposition
(runs in forem-dev; needs numpy, PyYAML).

  analyze_task2.py run --run-dir DIR [--out OUT_DIR] [--hf] [--config fixed_delay.yaml]
      -> OUT_DIR/run_metrics.json, OUT_DIR/curves.npz   (OUT_DIR defaults to the run dir; an existing run_metrics.json is never overwritten)

Inputs in the run dir: raw/*.csv, raw/bag_commands.json, raw/bag_commands_in.json, raw/bag_events.json, raw/bag_summary.json (task2_bag_to_csv.py),
commands.json (collect_task2.py), delay_events.jsonl (the proxy's own file, queue mode), robot_description.urdf.
Exit: 0 every gate passed; 1 a gate failed (metrics still written, marked invalid); 2 input unusable.

Signals (exp2.1 section 2/4), all in simulation time:
  t_send_before/after  sender, around publish          t_in   proxy receive-callback clock      t_due = t_in + tau
  t_pub_before/after   proxy, around the downstream publish
  t_ref                first controller `desired` change   (controller axis)
  q_nom(t; t0) = q_start + dq * s((t - t0)/T),  s(u)=3u^2-2u^3 clipped, t0 = middle of [t_send_before, t_send_after]  (original-send axis)
Errors at the SAME controller state stamp, joint order fixed:
  e_servo  = q_actual - q_ref          e_schedule = q_ref - q_nom          e_total = q_actual - q_nom = e_servo + e_schedule
q_ref is the controller's `desired`, q_actual the controller state `actual` (cross-checked with joint_states and the Gazebo link truth).
Nothing is ever copied from desired/command into actual, and the nominal axis is never re-based on t_ref.
Thresholds come from the frozen config (quality section = Task1's; gates section = exp2.1). They are measurement-quality gates, not accuracy goals.
"""
import argparse
import json
import math
import os
import sys
from collections import Counter

import numpy as np
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_task1 as A1  # noqa: E402  (shared, unchanged Task1 gate/curve functions)
import task1_lib as L  # noqa: E402
import task2_delay_queue as Q  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CONFIG = os.path.join(ROOT, "config", "experiments", "exp2", "fixed_delay.yaml")
J = L.JOINTS
ANALYSIS_VERSION = "task2.8-1"   # task2.8-1: sender-record well-formedness (types/shape/finiteness) checked BEFORE any tolerance comparison, moving joints from validated data (T2-A04);
#                                  task2.6-1: task2.3-1: original; task2.3-2: sub-sample fitted start added before any pilot run;
#                                  task2.6-1: frozen-contract gates (T2-A02) + fit validity/identifiability flags and t_ref-vs-fit bookkeeping (T2-A01)
FIT_RESIDUAL_MAX_RAD = 1e-7          # fitted start is accepted only if desired matches the cubic within this (max-abs, rad)
FIT_SHIFT_SENSITIVITY_RAD = 1e-6     # ... and a +-0.5 ms shift of the start must worsen the match by at least this (the start is identifiable)
FIT_SHIFT_PROBE_S = 0.0005
START_POSE_MARGIN_RAD = 0.01         # |q_start - q_init| bound = the margin of the Task1 preflight (task1_freeze.preflight)
CONTRACT_DQ_TOL_RAD = 1e-9
ALLOWED_PROXY_EVENTS = {"ready", "enqueue", "publish", "shutdown", "node_exit"}
FORBIDDEN_PROXY_EVENTS = {"reject", "drop", "reset", "clock_backward", "fatal", "due"}


def _json(path):
    with open(path) as f:
        return json.load(f)


def _text(path):
    with open(path) as f:
        return f.read()


# ---------------------------------------------------------------------------------------------------------------- pure helpers
def q_nominal(t, q_start, dq, T, t0):
    """Original-schedule joint reference at times t for a trajectory sent at t0: q_start + dq * (3u^2 - 2u^3), u clipped to [0, 1]."""
    u = np.clip((np.asarray(t, dtype=float) - t0) / T, 0.0, 1.0)
    return np.asarray(q_start)[None, :] + np.asarray(dq)[None, :] * (3 * u * u - 2 * u ** 3)[:, None]


def v_nominal(t, dq, T, t0):
    """Derivative of q_nominal (rad/s): dq * 6u(1-u)/T inside [t0, t0+T], 0 outside."""
    u = (np.asarray(t, dtype=float) - t0) / T
    s1 = np.where((u >= 0) & (u <= 1), 6 * u * (1 - u), 0.0) / T
    return np.asarray(dq)[None, :] * s1[:, None]


def fit_start_time(t, des, hold_ref, q_target, T, t_ref, ladder_half_s=0.03, ladder_s=0.0005, refine_half_s=0.0006, tol_s=1e-8):
    """Sub-sample start time of the controller reference: the ts that makes hold_ref + (q_target-hold_ref)*s((t-ts)/T) best match the recorded
    `desired` samples (max-abs residual on a 0.5 ms ladder around t_ref, then golden-section refinement of the RMS residual). The controller's reference IS that
    cubic, so this recovers its start to far better than the 8 ms sample spacing that limits the threshold-detected t_ref.
    Returns (ts, max_abs_residual_rad, ladder_ts, ladder_residual)."""
    mm = (t >= t_ref - 0.05) & (t <= t_ref + T + 0.05)
    tm_, dm = t[mm], des[mm]
    span = q_target - hold_ref

    def model(ts):
        u = np.clip((tm_ - ts) / T, 0.0, 1.0)
        return hold_ref[None, :] + span[None, :] * (3 * u * u - 2 * u ** 3)[:, None]

    best = None
    for ts in t_ref + np.arange(-ladder_half_s, ladder_half_s + 1e-12, ladder_s):
        r = float(np.max(np.abs(dm - model(ts))))
        if best is None or r < best[1]:
            best = (float(ts), r)
    f = lambda ts: float(np.mean((dm - model(ts)) ** 2))
    a, b = best[0] - refine_half_s, best[0] + refine_half_s
    g = (math.sqrt(5) - 1) / 2
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = f(c), f(d)
    while b - a > tol_s:
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a); fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a); fd = f(d)
    ts = 0.5 * (a + b)
    return ts, float(np.max(np.abs(dm - model(ts)))), best[0], best[1]


def cubic_residual(t, des, hold_ref, q_target, T, t_ref, ts):
    """Max-abs residual (rad) of `desired` against hold_ref + (q_target-hold_ref)*s((t-ts)/T) around the motion (same window as fit_start_time)."""
    mm = (t >= t_ref - 0.05) & (t <= t_ref + T + 0.05)
    u = np.clip((t[mm] - ts) / T, 0.0, 1.0)
    model = hold_ref[None, :] + (q_target - hold_ref)[None, :] * (3 * u * u - 2 * u ** 3)[:, None]
    return float(np.max(np.abs(des[mm] - model)))


def _is_num(x):
    """A real, finite Python/numpy number (bool, str, None, NaN, +-Inf are not)."""
    return isinstance(x, (int, float, np.integer, np.floating)) and not isinstance(x, (bool, np.bool_)) and math.isfinite(float(x))


def _is_int(x):
    return isinstance(x, (int, np.integer)) and not isinstance(x, (bool, np.bool_))


def _finite_vector(v, n):
    """True iff v is a list/tuple of exactly n finite real numbers (no NaN/Inf/bool/str/None, no nesting, no wrong length)."""
    return isinstance(v, (list, tuple)) and len(v) == n and all(_is_num(x) for x in v)


def validate_sender_record(cmd, n_joints):
    """Type / shape / finiteness check of the sender record (commands.json) BEFORE any value is compared or used (T2-A04: `NaN > tol` is False, `abs(NaN) > 0` is
    False, so a non-finite dq would otherwise pass the tolerance check and silently drop the joint from the lag analysis). Returns a list of problems (empty = ok).
    Checked: run-level fields, base poses, the recording window, and for the (at most one) command: dq / q_target / q_start_observed / q_start_minus_q_init
    (exactly n_joints finite numbers each), duration_s (finite, > 0), the integer simulation send times (before <= after) and their float twins."""
    bad = []
    if not isinstance(cmd, dict):
        return ["sender record is not an object"]
    for k in ("run_id", "case", "mode"):
        if not isinstance(cmd.get(k), str):
            bad.append("%s missing or not a string" % k)
    if not _is_int(cmd.get("tau_ns")) or cmd.get("tau_ns", -1) < 0:
        bad.append("tau_ns missing, not an integer or negative: %r" % (cmd.get("tau_ns"),))
    if not _is_num(cmd.get("delay_ms")):
        bad.append("delay_ms missing or not finite: %r" % (cmd.get("delay_ms"),))
    if not (_is_num(cmd.get("rec_t0")) and _is_num(cmd.get("rec_t1")) and cmd["rec_t1"] > cmd["rec_t0"]):
        bad.append("rec_t0/rec_t1 missing, non-finite or not increasing: %r, %r" % (cmd.get("rec_t0"), cmd.get("rec_t1")))
    for k in ("base_pose_start", "base_pose_end"):
        if not _finite_vector(cmd.get(k), 7):
            bad.append("%s is not 7 finite numbers: %r" % (k, cmd.get(k)))
    cl = cmd.get("commands")
    if not isinstance(cl, list) or len(cl) > 1:
        bad.append("commands missing or not a list of at most one entry")
        return bad
    for c0 in cl:
        if not isinstance(c0, dict):
            bad.append("command entry is not an object")
            continue
        for k in ("dq", "q_target", "q_start_observed", "q_start_minus_q_init"):
            if not _finite_vector(c0.get(k), n_joints):
                bad.append("command.%s must be %d finite numbers, got %r" % (k, n_joints, c0.get(k)))
        if not (_is_num(c0.get("duration_s")) and c0["duration_s"] > 0):
            bad.append("command.duration_s must be finite and > 0, got %r" % (c0.get("duration_s"),))
        b, a_ = c0.get("sim_time_before_publish_ns"), c0.get("sim_time_after_publish_ns")
        if not (_is_int(b) and _is_int(a_) and 0 <= b <= a_):
            bad.append("sim_time_before/after_publish_ns must be integers with 0 <= before <= after, got %r, %r" % (b, a_))
        for k in ("sim_time_before_publish", "sim_time_after_publish"):
            if not _is_num(c0.get(k)):
                bad.append("command.%s missing or not finite: %r" % (k, c0.get(k)))
        if not isinstance(c0.get("payload_sha256"), str):
            bad.append("command.payload_sha256 missing or not a string")
        if not isinstance(c0.get("message"), dict):
            bad.append("command.message missing or not an object")
    return bad


def check_frozen_contract(cmd, down, up, cfg, joint_limits):
    """Offline, self-contained verification that the recorded run belongs to the FROZEN protocol (T2-A02). It does not rely on the sender or the proxy
    having refused anything: it re-checks, from the recorded files only,
      * condition: (mode, tau) is one of the frozen conditions B/Z/D80/D160 (tau_ns must equal the rounded delay_ms)
      * case: the case exists in the frozen config; H has no command, every other case exactly one
      * message: the sent, the downstream and (queue) the upstream message are the frozen supported message (header.stamp=0, frame_id, joint order,
        two points, first point at 0, zero velocities, empty acceleration/effort, finite, URDF limits, peak speed <= fraction of the URDF limit)
      * displacement/duration/pose: q_target-q_start equals the frozen dq of the case, the last time_from_start equals the frozen T, the start pose is within the
        Task1 preflight margin of the frozen q_init, and the sender's own dq/duration records agree with the frozen case.
    Returns (res, gates); every gate is a bool and the reasons say why."""
    res = {"reasons": []}
    gates = {}
    why = res["reasons"]
    rec_problems = validate_sender_record(cmd, len(cfg["robot"]["joints"]))
    gates["contract_sender_record_wellformed"] = not rec_problems
    if rec_problems:
        why.extend(rec_problems)
        return res, gates                       # nothing below may compare or use a malformed/non-finite field
    tau_ns = cmd.get("tau_ns")
    mode = cmd.get("mode")
    conds = cfg["delay"]["conditions"]
    delay_ms = cmd.get("delay_ms")
    ok_cond = False
    if isinstance(tau_ns, int) and not isinstance(tau_ns, bool) and delay_ms is not None and math.isfinite(float(delay_ms)):
        ok_cond = (tau_ns == int(round(float(delay_ms) * 1e6))) and any(c["mode"] == mode and int(round(c["tau_ms"] * 1e6)) == tau_ns for c in conds.values())
    gates["contract_condition_frozen"] = bool(ok_cond)
    if not ok_cond:
        why.append("(mode=%r, tau_ns=%r, delay_ms=%r) is not one of the frozen conditions %s" % (mode, tau_ns, delay_ms, {k: (v["mode"], v["tau_ms"]) for k, v in conds.items()}))
    case = cmd.get("case")
    gates["contract_case_frozen"] = case in cfg["cases"]
    if case not in cfg["cases"]:
        why.append("case %r is not a frozen case %s" % (case, sorted(cfg["cases"])))
        return res, gates
    cdef = cfg["cases"][case]
    want_motion = cdef["dq"] is not None
    n_cmd = len(cmd.get("commands", []))
    gates["contract_case_command_presence"] = bool(n_cmd == (1 if want_motion else 0))
    if not gates["contract_case_command_presence"]:
        why.append("case %s expects %d command(s), the sender recorded %d" % (case, 1 if want_motion else 0, n_cmd))
    if not (want_motion and n_cmd == 1):
        return res, gates
    c0 = cmd["commands"][0]
    joints = cfg["robot"]["joints"]
    frac = cfg["trajectory"]["max_speed_fraction_of_velocity_limit"]
    frame_id = cfg["delay"]["supported_message"]["frame_id"]
    bad = []
    msgs = [("sent", c0.get("message"))] + [("downstream", d["message"]) for d in down] + [("upstream", u["message"]) for u in up]
    for tag, m in msgs:
        for pr in Q.validate_command(m, joints, joint_limits, frac, frame_id=frame_id):
            bad.append("%s message: %s" % (tag, pr))
    gates["contract_message_supported"] = not bad
    why.extend(bad)
    dq_ok = True
    try:
        pts = c0["message"]["points"]
        q0, q1 = np.array(pts[0]["positions"], dtype=float), np.array(pts[1]["positions"], dtype=float)
        T_msg = pts[1]["time_from_start"][0] + pts[1]["time_from_start"][1] * 1e-9
        dq_cfg = np.array(cdef["dq"], dtype=float)
        if q0.shape != dq_cfg.shape or q1.shape != dq_cfg.shape or float(np.max(np.abs((q1 - q0) - dq_cfg))) > CONTRACT_DQ_TOL_RAD:
            dq_ok = False
            why.append("displacement q_target-q_start differs from the frozen dq of case %s" % case)
        if abs(T_msg - float(cdef["T"])) > 1e-9:
            dq_ok = False
            why.append("duration %r s differs from the frozen T=%r of case %s" % (T_msg, cdef["T"], case))
        if float(np.max(np.abs(q0 - np.array(cfg["robot"]["q_init"])))) > START_POSE_MARGIN_RAD:
            dq_ok = False
            why.append("start pose differs from the frozen q_init by more than %.3g rad" % START_POSE_MARGIN_RAD)
        if float(np.max(np.abs(np.array(c0["dq"], dtype=float) - dq_cfg))) > CONTRACT_DQ_TOL_RAD or abs(float(c0["duration_s"]) - float(cdef["T"])) > 1e-9:
            dq_ok = False
            why.append("the sender's own dq/duration record differs from the frozen case")
    except (KeyError, TypeError, ValueError, IndexError) as e:
        dq_ok = False
        why.append("cannot verify displacement/duration: %r" % (e,))
    gates["contract_case_displacement_duration"] = bool(dq_ok)
    return res, gates


def error_decomposition(q_act, q_ref, q_nom):
    """e_servo, e_schedule, e_total at the same samples; e_total = e_servo + e_schedule holds by construction and is checked."""
    e_servo = q_act - q_ref
    e_sched = q_ref - q_nom
    e_total = q_act - q_nom
    return e_servo, e_sched, e_total, float(np.max(np.abs(e_total - (e_servo + e_sched)))) if e_total.size else 0.0


def ee_errors(chain, qa, qb):
    """Position (m) and geodesic orientation (rad) differences of FK(qa) vs FK(qb), base -> tip."""
    Pa, Ra = L.fk_batch(chain, qa)
    Pb, Rb = L.fk_batch(chain, qb)
    return np.linalg.norm(Pa - Pb, axis=1), L.rot_angle(Ra, Rb)


def _sorted_events(rows):
    return sorted(rows, key=lambda r: (r["event"].get("n", 0), r["t_bag"]))


def check_command_chain(cmd, down, up, events_bag, events_file, mode, tau_ns, eps_max_ns, expect_file=True):
    """Audit sender -> (proxy) -> controller. Returns (res, gates). Every gate is a plain bool; the reasons explain failures.
    down/up: bag_commands.json / bag_commands_in.json lists; events_bag: bag_events.json; events_file: parsed delay_events.jsonl (or None)."""
    res = {"mode": mode, "tau_ns": tau_ns, "reasons": []}
    gates = {}
    why = res["reasons"]
    moving = bool(cmd["commands"])
    n_down_exp = 1 if moving else 0
    n_up_exp = 1 if (moving and mode == "queue") else 0
    res["n_downstream"], res["n_upstream"] = len(down), len(up)
    res["n_downstream_expected"], res["n_upstream_expected"] = n_down_exp, n_up_exp
    gates["downstream_count"] = len(down) == n_down_exp
    gates["upstream_count"] = len(up) == n_up_exp
    if not gates["downstream_count"]:
        why.append("%d downstream command messages in the bag, expected %d" % (len(down), n_down_exp))
    if not gates["upstream_count"]:
        why.append("%d upstream command messages in the bag, expected %d" % (len(up), n_up_exp))
    ev = [r["event"] for r in _sorted_events(events_bag)]
    types = Counter(e["type"] for e in ev)
    res["event_types"] = dict(types)
    if moving:
        c0 = cmd["commands"][0]
        sent = c0["message"]
        res["downstream_vs_sent"] = L.compare_commands(sent, down)
        gates["downstream_matches_sent"] = bool(res["downstream_vs_sent"]["match"])
        if mode == "queue":
            res["upstream_vs_sent"] = L.compare_commands(sent, up)
            gates["upstream_matches_sent"] = bool(res["upstream_vs_sent"]["match"])
            gates["header_seq_preserved"] = bool(len(down) == 1 and len(up) == 1 and down[0]["seq"] == up[0]["seq"])
        gates["sender_hash_matches_message"] = bool(c0.get("payload_sha256") == Q.payload_hash(sent))
        for g in ("downstream_matches_sent", "upstream_matches_sent", "header_seq_preserved", "sender_hash_matches_message"):
            if g in gates and not gates[g]:
                why.append("command chain check failed: " + g)
    if mode == "bypass":
        gates["no_proxy_events"] = len(ev) == 0
        if ev:
            why.append("bypass run has %d proxy events" % len(ev))
        res["events"] = None
        return res, gates
    # ---- queue mode: event audit
    bad_types = sorted(set(types) & FORBIDDEN_PROXY_EVENTS) + sorted(set(types) - ALLOWED_PROXY_EVENTS - FORBIDDEN_PROXY_EVENTS)
    gates["proxy_events_clean"] = not bad_types
    if bad_types:
        why.append("forbidden/unknown proxy events: %s" % bad_types)
    exp_n = 1 if moving else 0
    gates["proxy_event_counts"] = bool(types.get("ready", 0) == 1 and types.get("enqueue", 0) == exp_n and types.get("publish", 0) == exp_n)
    if not gates["proxy_event_counts"]:
        why.append("event counts %s, expected ready=1 enqueue=%d publish=%d" % (dict(types), exp_n, exp_n))
    exits = [e for e in ev if e["type"] == "node_exit"]
    gates["proxy_exit_clean"] = bool(len(exits) <= 1 and all(e.get("failed") is None and e["counts"]["rejected"] == 0 and e["counts"]["dropped"] == 0 for e in exits))
    if not gates["proxy_exit_clean"]:
        why.append("proxy node_exit reports failure/rejects/drops: %s" % exits)
    if expect_file:
        fe = events_file
        gates["events_file_matches_bag"] = bool(fe is not None and sorted(e["n"] for e in fe) == sorted(e["n"] for e in ev) and
                                                {e["n"]: e for e in fe} == {e["n"]: e for e in ev})
        if not gates["events_file_matches_bag"]:
            why.append("proxy events file and bag events differ (file %s, bag %s)" % (None if fe is None else len(fe), len(ev)))
    gates["proxy_delay_matches_condition"] = all(e.get("delay_ns", tau_ns) == tau_ns for e in ev)
    if not gates["proxy_delay_matches_condition"]:
        why.append("proxy events report a delay_ns different from the run condition (%d ns)" % tau_ns)
    gates["proxy_run_id_consistent"] = len({e.get("run_id") for e in ev}) <= 1 and (not ev or ev[0].get("run_id") == cmd["run_id"])
    if not gates["proxy_run_id_consistent"]:
        why.append("proxy events carry another run-id")
    enq = [e for e in ev if e["type"] == "enqueue"]
    pub = [e for e in ev if e["type"] == "publish"]
    res["events"] = {"ready": next((e for e in ev if e["type"] == "ready"), None), "enqueue": enq, "publish": pub, "node_exit": exits}
    if moving and len(enq) == 1 and len(pub) == 1:
        e, p, c0 = enq[0], pub[0], cmd["commands"][0]
        gates["identity_epoch_seq"] = bool(e["epoch"] == 0 and e["seq"] == 0 and p["epoch"] == 0 and p["seq"] == 0)
        gates["hash_chain"] = bool(e["payload_hash"] == p["payload_hash"] == c0["payload_sha256"])
        gates["due_equals_in_plus_tau"] = bool(e["t_due_ns"] == e["t_in_ns"] + tau_ns and p["t_due_ns"] == e["t_due_ns"] and e["delay_ns"] == tau_ns and p["t_in_ns"] == e["t_in_ns"])
        d_queue = p["t_pub_before_ns"] - p["t_in_ns"]
        eps = d_queue - tau_ns
        res["timing"] = {"t_in_ns": p["t_in_ns"], "t_due_ns": p["t_due_ns"], "t_pub_before_ns": p["t_pub_before_ns"], "t_pub_after_ns": p["t_pub_after_ns"],
                         "d_queue_ns": d_queue, "eps_ns": eps, "eps_max_ns": eps_max_ns,
                         "t_in_minus_t_send_after_ns": p["t_in_ns"] - c0["sim_time_after_publish_ns"], "t_in_minus_t_send_before_ns": p["t_in_ns"] - c0["sim_time_before_publish_ns"],
                         "pub_interval_ns": p["t_pub_after_ns"] - p["t_pub_before_ns"],
                         "bag_down_minus_t_pub_before_ns": (int(round(down[0]["t_bag"] * 1e9)) - p["t_pub_before_ns"]) if len(down) == 1 else None}
        gates["event_arithmetic"] = bool(p["d_queue_ns"] == d_queue and p["eps_ns"] == eps and p["t_pub_after_ns"] >= p["t_pub_before_ns"])
        gates["no_early_delivery"] = bool(eps >= 0)
        gates["eps_within_tolerance"] = bool(0 <= eps <= eps_max_ns)
        gates["receive_not_before_send"] = bool(p["t_in_ns"] >= c0["sim_time_before_publish_ns"] - eps_max_ns)
        for g in ("identity_epoch_seq", "hash_chain", "due_equals_in_plus_tau", "event_arithmetic", "no_early_delivery", "eps_within_tolerance", "receive_not_before_send"):
            if not gates[g]:
                why.append("proxy timing/identity check failed: " + g)
    elif moving:
        gates["identity_epoch_seq"] = False
        why.append("expected exactly one enqueue and one publish event")
    return res, gates


# ---------------------------------------------------------------------------------------------------------------- run
def analyze_run(run_dir, hf=False, cfg=None, out_dir=None):
    cfg = cfg or yaml.safe_load(_text(CONFIG))
    q_cfg, tmg, gcfg = cfg["quality"], cfg["timing"], cfg["gates"]
    out_dir = out_dir or run_dir
    if os.path.exists(os.path.join(out_dir, "run_metrics.json")):
        raise L.InvalidInput("%s already has run_metrics.json; analyses never overwrite" % out_dir)
    os.makedirs(out_dir, exist_ok=True)
    nominal = 1.0 / (tmg["hf_rate_hz"] if hf else tmg["joint_rate_hz"])
    raw = os.path.join(run_dir, "raw")
    cmd = _json(os.path.join(run_dir, "commands.json"))
    urdf = _text(os.path.join(run_dir, "robot_description.urdf"))
    bsum = _json(os.path.join(raw, "bag_summary.json"))
    frames = cfg["robot"]["frames"]
    chain = L.parse_chain(urdf, frames["base"], frames["tip"])
    vlim, plim = A1.urdf_vel_limits(urdf), A1.urdf_pos_limits(urdf)
    rec_problems = validate_sender_record(cmd, len(J))
    if rec_problems:      # T2-A04: malformed / non-finite sender record = invalid run; no tolerance comparison or joint selection may run on it
        bad_res = {"analysis_version": ANALYSIS_VERSION, "run_id": str(cmd.get("run_id")) if isinstance(cmd, dict) else None,
                   "case": cmd.get("case") if isinstance(cmd, dict) else None, "hf": hf, "quality": {}, "windows": {}, "gates": {"contract_sender_record_wellformed": False},
                   "invalid_reasons": ["sender record: " + r for r in rec_problems]}
        return _finish(out_dir, bad_res, bad_res["gates"])
    mode, tau_ns = cmd["mode"], int(cmd["tau_ns"])
    tau_s = tau_ns / 1e9

    st = A1.load_csv(os.path.join(raw, "controller_state.csv"),
                     ["t_header"] + ["%s%s" % (p, j) for p in ("des_", "act_", "err_", "desvel_", "actvel_", "errvel_") for j in J])
    js = A1.load_csv(os.path.join(raw, "joint_states.csv"), ["t_header"] + ["pos_" + j for j in J] + ["vel_" + j for j in J])
    truth = A1.load_csv(os.path.join(raw, "link_truth.csv"), ["t_bag"] + ["b_x", "t_x", "b_qw", "t_qw"])
    clk = A1.load_csv(os.path.join(raw, "clock.csv"), ["t"])
    down = _json(os.path.join(raw, "bag_commands.json"))
    up = _json(os.path.join(raw, "bag_commands_in.json"))
    events_bag = _json(os.path.join(raw, "bag_events.json"))
    ef = os.path.join(run_dir, "delay_events.jsonl")
    events_file = [json.loads(l) for l in _text(ef).splitlines() if l.strip()] if os.path.exists(ef) else None

    res = {"analysis_version": ANALYSIS_VERSION, "run_id": cmd["run_id"], "case": cmd["case"], "mode": mode, "tau_ms": tau_ns / 1e6, "tau_ns": tau_ns,
           "hf": hf, "nominal_period_s": nominal, "quality": {}, "gates": {}, "invalid_reasons": []}
    gates = res["gates"]

    # ---- bag-level integrity, clock, ordering
    res["quality"]["bag_summary"] = {k: bsum[k] for k in bsum if k != "rows"}
    gates["bag_integrity"] = bool(bsum["incomplete_joint_states"] == 0 and bsum["incomplete_controller_state"] == 0 and bsum["non_finite_rows"] == 0
                                  and bsum["missing_link_messages"] == 0 and bsum.get("unparsable_events", 0) == 0)
    if "aborted" in cmd:
        gates["run_not_aborted"] = False
        res["invalid_reasons"].append("collector aborted: %s" % cmd["aborted"])
    clk_back = int(np.sum(np.diff(clk["t"]) < 0))
    res["quality"]["clock"] = {"n": int(clk["t"].size), "backward_steps": clk_back}
    gates["clock_monotonic"] = clk_back == 0
    t_c_raw, t_j_raw = st["t_header"], js["t_header"]
    rec_t0, rec_t1 = cmd["rec_t0"], cmd["rec_t1"]
    moving = bool(cmd["commands"])
    back_c, back_j = int(np.sum(np.diff(t_c_raw) < 0)), int(np.sum(np.diff(t_j_raw) < 0))
    gates["streams_time_ordered"] = not (back_c or back_j)
    if back_c or back_j:
        res["invalid_reasons"].append("backward timestamps: controller %d joint_states %d" % (back_c, back_j))
    des_all, act_all = A1.cols(st, "des_"), A1.cols(st, "act_")
    errf_all, dv_all, av_all = A1.cols(st, "err_"), A1.cols(st, "desvel_"), A1.cols(st, "actvel_")
    t_c, des, act, errf, dv, av = L.dedupe_sorted(t_c_raw, des_all, act_all, errf_all, dv_all, av_all)
    t_j, qj = L.dedupe_sorted(t_j_raw, A1.cols(js, "pos_"))

    # ---- command chain (sender -> proxy -> controller)
    chain_res, chain_gates = check_command_chain(cmd, down, up, events_bag, events_file, mode, tau_ns, int(round(cfg["delay"]["eps_max_ms"] * 1e6)))
    res["command_chain"] = chain_res
    gates.update({"chain_" + k: v for k, v in chain_gates.items()})
    for r in chain_res["reasons"]:
        res["invalid_reasons"].append(r)
    jl = {j: {"lower": plim[j][0], "upper": plim[j][1], "velocity": vlim[j]} for j in J}
    contract_res, contract_gates = check_frozen_contract(cmd, down, up, cfg, jl)
    res["frozen_contract"] = contract_res
    gates.update(contract_gates)
    res["invalid_reasons"].extend(contract_res["reasons"])

    # ---- windows
    pre = [rec_t0, rec_t0 + tmg["pre_hold_s"]]
    wins = {"pre_hold": pre}
    nom_wins = {}
    t_ref = T = t0 = None
    delay = {"tau_ns": tau_ns, "tau_s": tau_s}
    if moving:
        c0 = cmd["commands"][0]
        T = c0["duration_s"]
        q_start = np.array(c0["message"]["points"][0]["positions"])
        q_target = np.array(c0["q_target"])
        np.testing.assert_allclose(q_target, np.array(c0["message"]["points"][1]["positions"]), rtol=0, atol=0)   # sender record is self-consistent
        dq = q_target - q_start
        moving_idx = [i for i, x in enumerate(c0["dq"]) if abs(x) > 0]       # dq validated finite and of length 6 above
        frozen_dq = cfg["cases"].get(cmd["case"], {}).get("dq")
        gates["moving_joints_match_frozen_case"] = bool(frozen_dq is not None and moving_idx == [i for i, x in enumerate(frozen_dq) if abs(x) > 0])
        if not gates["moving_joints_match_frozen_case"]:
            res["invalid_reasons"].append("moving joints %s differ from the frozen case %s" % ([J[i] for i in moving_idx], cmd["case"]))
        t_lo, t_hi = c0["sim_time_before_publish_ns"] / 1e9, c0["sim_time_after_publish_ns"] / 1e9
        t0 = 0.5 * (t_lo + t_hi)
        m_pre = (t_c >= pre[1] - 1.0) & (t_c <= pre[1])
        hold_ref = np.median(des[m_pre], axis=0) if m_pre.any() else des[0]
        try:
            t_ref, per_joint = L.find_t_ref(t_c[t_c >= pre[0]], des[t_c >= pre[0]], hold_ref, moving_idx, q_cfg["t_ref_threshold_rad"])
        except L.InvalidInput as e:
            gates["motion_observed"] = False
            res["invalid_reasons"].append(str(e))
        if t_ref is not None:
            gates["motion_observed"] = True
            wins["motion"] = [t_ref, t_ref + T]
            wins["settle"] = [t_ref + T, t_ref + T + tmg["settle_s"]]
            nom_wins = {"motion_nom": [t0, t0 + T], "exec_nom": [t0, t0 + tau_s + T]}
            wins["exec_full"] = [t_lo, t_hi + tau_s + T + tmg["settle_s"]]
            tm_ = chain_res.get("timing")
            t_pub_b = tm_["t_pub_before_ns"] / 1e9 if tm_ else None
            t_pub_a = tm_["t_pub_after_ns"] / 1e9 if tm_ else None
            delay.update({
                "t_send_before_s": t_lo, "t_send_after_s": t_hi, "t_send_width_s": t_hi - t_lo, "t0_mid_s": t0, "t_ref_s": t_ref, "t_ref_per_joint": per_joint,
                "t_ref_threshold_rad": q_cfg["t_ref_threshold_rad"],
                "t_ref_minus_send_before_s": t_ref - t_lo, "t_ref_minus_send_after_s": t_ref - t_hi,
                "t_ref_minus_t0_mid_s": t_ref - t0, "t_ref_minus_t0_mid_minus_tau_s": t_ref - t0 - tau_s,
                "t_pub_before_s": t_pub_b, "t_pub_after_s": t_pub_a,
                "t_ref_minus_pub_before_s": (t_ref - t_pub_b) if tm_ else None, "t_ref_minus_pub_after_s": (t_ref - t_pub_a) if tm_ else None,
                "queue": {k: chain_res["timing"][k] for k in ("t_in_ns", "t_due_ns", "d_queue_ns", "eps_ns", "t_in_minus_t_send_after_ns",
                                                              "t_in_minus_t_send_before_ns", "pub_interval_ns", "bag_down_minus_t_pub_before_ns")} if tm_ else None,
                "note": "t_ref includes ROS transport, controller update scheduling and sample quantisation; the injected tau is NOT a servo lag"})
            gates["t_ref_not_before_delivery"] = bool(t_ref >= (t_pub_b if tm_ else t_lo) - 1e-9)
            res["q_start_vs_hold_ref"] = {"hold_ref_desired": hold_ref.tolist(), "q_start_observed": q_start.tolist(),
                                          "q_start_minus_hold_ref": (q_start - hold_ref).tolist(), "q_start_minus_q_init": c0["q_start_minus_q_init"]}
    else:
        hold = [rec_t0 + tmg["pre_hold_s"], rec_t0 + tmg["pre_hold_s"] + tmg["hold_s"]]
        wins["hold"] = hold
        m_pre = (t_c >= pre[1] - 1.0) & (t_c <= pre[1])
        hold_ref = np.median(des[m_pre], axis=0) if m_pre.any() else des[0]
    res["windows"] = wins
    res["windows_nominal"] = nom_wins
    res["delay"] = delay
    if moving and t_ref is None:
        res["pass"] = False
        res["invalid_reasons"].append("no windows without observed motion")
        return _finish(out_dir, res, gates)

    # ---- stream quality per window
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
    gates["window_inside_recording"] = bool(all(w1 <= rec_t1 + 1e-9 for (_, w1) in wins.values()) and all(w0 >= rec_t0 - 1e-9 for (w0, _) in wins.values()))

    # ---- source audit
    audit_w = wins.get("motion") or wins["hold"]
    mw = (t_c >= audit_w[0]) & (t_c <= audit_w[1])
    js_near, _ = L.nearest_pairs(t_c[mw], t_j, q_cfg["js_pair_dt_max_s"])
    js_pos_in = qj[js_near[js_near >= 0]] if (js_near >= 0).any() else None
    target_vec = np.array(cmd["commands"][0]["q_target"]) if moving else None
    aud = L.audit_backfill(act[mw], des[mw], js_pos=None if js_pos_in is None or js_pos_in.shape != des[mw].shape else js_pos_in, target=target_vec)
    full = (t_c >= rec_t0) & (t_c <= rec_t1)
    e_field = float(np.max(np.abs(errf[full] - (des[full] - act[full])))) if full.any() else None
    aud["controller_error_field"] = {"max_abs_err_minus_(des-act)": e_field, "convention": "desired - actual" if (e_field is not None and e_field < 1e-9) else "unexpected"}
    res["quality"]["source_audit"] = aud
    gates["actual_not_backfilled"] = bool(aud["pass"])
    gates["error_field_convention_checked"] = bool(e_field is not None and e_field < 1e-9)
    if moving:
        ts_fit, fit_res, ts_ladder, ladder_res = fit_start_time(t_c, des, hold_ref, q_target, T, t_ref)
        end_res = float(np.max(np.abs(des[(t_c >= t_ref + T + 0.05) & (t_c <= t_ref + T + 1.0)] - q_target)))
        res["quality"]["interpolation"] = {"model": "hold_ref + (q_target-hold_ref)*(3u^2-2u^3)", "fitted_start_s": ts_ladder, "max_abs_residual_rad": ladder_res,
                                           "fitted_start_refined_s": ts_fit, "refined_max_abs_residual_rad": fit_res,
                                           "end_value_residual_rad": end_res, "fitted_start_minus_t_ref_s": ts_fit - t_ref, "tolerance_rad": 1e-5}
        res_minus = cubic_residual(t_c, des, hold_ref, q_target, T, t_ref, ts_fit - FIT_SHIFT_PROBE_S)
        res_plus = cubic_residual(t_c, des, hold_ref, q_target, T, t_ref, ts_fit + FIT_SHIFT_PROBE_S)
        fit_valid = bool(fit_res <= FIT_RESIDUAL_MAX_RAD and min(res_minus, res_plus) >= FIT_SHIFT_SENSITIVITY_RAD)
        res["delay"]["fit_validity"] = {"valid": fit_valid, "residual_max_abs_rad": fit_res, "residual_limit_rad": FIT_RESIDUAL_MAX_RAD,
                                        "residual_at_start_minus_0p5ms_rad": res_minus, "residual_at_start_plus_0p5ms_rad": res_plus,
                                        "shift_sensitivity_required_rad": FIT_SHIFT_SENSITIVITY_RAD, "shift_probe_s": FIT_SHIFT_PROBE_S,
                                        "rule": "valid iff max-abs residual of desired vs the cubic at the fitted start <= residual_limit AND a +-0.5 ms shift of the start worsens the match to >= shift_sensitivity (the start is identifiable from the samples)"}
        res["delay"]["t_ref_minus_t_start_fit_s"] = t_ref - ts_fit
        res["delay"]["t_start_fit_s"] = ts_fit
        res["delay"]["t_start_fit_minus_send_before_s"] = ts_fit - res["delay"]["t_send_before_s"]
        res["delay"]["t_start_fit_minus_send_after_s"] = ts_fit - res["delay"]["t_send_after_s"]
        res["delay"]["t_start_fit_minus_t0_mid_minus_tau_s"] = ts_fit - t0 - tau_s
        if res["delay"].get("t_pub_before_s") is not None:
            res["delay"]["t_start_fit_minus_pub_before_s"] = ts_fit - res["delay"]["t_pub_before_s"]
        res["delay"]["t_start_fit_note"] = ("sub-sample start of the controller reference from a cubic fit of `desired` (resolution far below the 8 ms sample spacing); "
                                            "t_ref (threshold crossing on the 8 ms samples) is kept for the pre-registered gates")
        gates["interpolation_matches_cubic"] = bool(fit_res < 1e-5 and end_res < 1e-6)

    # ---- cross checks: joint_states and Gazebo truth (Task1 functions, unchanged)
    cw = (t_c >= rec_t0) & (t_c <= rec_t1)
    res["quality"]["joint_states_vs_controller"] = A1.check_js_consistency(t_c[cw], act[cw], t_j, qj, vlim, q_cfg)
    gates["joint_states_consistent"] = res["quality"]["joint_states_vs_controller"]["pass"]
    res["quality"]["gazebo_truth"] = A1.check_truth(chain, vlim, t_c[cw], act[cw], av[cw], truth, q_cfg,
                                                    {"base": frames["gazebo_base"], "tip": frames["gazebo_tip"], "urdf_base": frames["base"], "urdf_tip": frames["tip"]})
    gates["gazebo_truth_consistent"] = res["quality"]["gazebo_truth"]["pass"]
    bs, be = np.array(cmd["base_pose_start"]), np.array(cmd["base_pose_end"])
    dpos = float(np.linalg.norm(bs[:3] - be[:3]))
    try:
        dang = float(L.rot_angle(L.quat_to_R(bs[3:]), L.quat_to_R(be[3:])))
        drift_reason = None
    except L.InvalidInput as e:
        dang, drift_reason = float("nan"), str(e)
    res["quality"]["base_drift"] = {"position_m": dpos, "rotation_rad": dang, "max": q_cfg["base_drift_max"], "invalid_quaternion": drift_reason}
    gates["base_fixed"] = bool(drift_reason is None and math.isfinite(dpos) and math.isfinite(dang) and dpos <= q_cfg["base_drift_max"] and dang <= q_cfg["base_drift_max"])
    lim_ok = all(plim[j][0] <= act[cw, i].min() and act[cw, i].max() <= plim[j][1] for i, j in enumerate(J))
    res["quality"]["joint_limits"] = {"within_urdf_limits": bool(lim_ok), "q_min": act[cw].min(axis=0).tolist(), "q_max": act[cw].max(axis=0).tolist()}
    gates["within_joint_limits"] = bool(lim_ok)

    # ---- three-way error decomposition on the controller samples of the recording window
    tcw, des_w, act_w = t_c[cw], des[cw], act[cw]
    if moving:
        qn_w = q_nominal(tcw, q_start, dq, T, t0)
    else:
        qn_w = np.tile(hold_ref, (tcw.size, 1))     # H: the pre-hold reference is the nominal "plan"
    e_servo, e_sched, e_total, ident = error_decomposition(act_w, des_w, qn_w)
    gates["error_identity_exact"] = bool(ident < 1e-12)
    res["quality"]["error_identity_max_abs"] = ident
    pos_servo, rot_servo = ee_errors(chain, act_w, des_w)
    pos_sched, rot_sched = ee_errors(chain, des_w, qn_w)
    pos_total, rot_total = ee_errors(chain, act_w, qn_w)

    def window_block(name, w0, w1, kind):
        m = (tcw >= w0) & (tcw <= w1)
        if m.sum() < 3:
            return {"error": "fewer than 3 samples", "window": [w0, w1]}
        ent = {"window": [w0, w1], "n": int(m.sum()),
               "e_servo": L.error_stats(e_servo[m], tcw[m]), "e_schedule": L.error_stats(e_sched[m], tcw[m]), "e_total": L.error_stats(e_total[m], tcw[m]),
               "ee_pos_servo_m": L.scalar_stats(pos_servo[m]), "ee_pos_schedule_m": L.scalar_stats(pos_sched[m]), "ee_pos_total_m": L.scalar_stats(pos_total[m]),
               "ee_rot_servo_rad": L.scalar_stats(rot_servo[m]), "ee_rot_schedule_rad": L.scalar_stats(rot_sched[m]), "ee_rot_total_rad": L.scalar_stats(rot_total[m]),
               "e_v_servo": L.error_stats(av[cw][m] - dv[cw][m], tcw[m]), "joint_order": J, "axis": kind}
        if kind == "controller" and name in ("pre_hold", "hold", "settle"):
            ent["hold"] = {"pos_peak_to_peak_rad": np.ptp(act_w[m], axis=0).tolist(), "vel_rms_rad_s": np.sqrt(np.mean(av[cw][m] ** 2, axis=0)).tolist()}
        return ent

    metrics = {}
    for wn_, (w0, w1) in wins.items():
        if wn_ == "exec_full":
            continue
        metrics[wn_] = window_block(wn_, w0, w1, "controller")
    for wn_, (w0, w1) in nom_wins.items():
        metrics[wn_] = window_block(wn_, w0, w1, "original_send")
    if moving:
        # sensitivity to the unknown instant of the send inside [t_before, t_after]: recompute e_total / e_schedule with both ends
        speed_peak = 1.5 * np.abs(dq) / T
        sens = {"t_send_width_s": t_hi - t_lo, "q_nom_change_bound_rad": (speed_peak * (t_hi - t_lo)).tolist(), "per_window": {}}
        for wn_, (w0, w1) in nom_wins.items():
            ent = {}
            for tag, tt in (("t0_before", t_lo), ("t0_mid", t0), ("t0_after", t_hi)):
                qn_t = q_nominal(tcw, q_start, dq, T, tt)
                es_, esc_, et_, _ = error_decomposition(act_w, des_w, qn_t)
                # keep the window of the mid t0 so only the instant moves
                m = (tcw >= w0) & (tcw <= w1)
                ent[tag] = {"e_total_rmse": np.sqrt(np.mean(et_[m] ** 2, axis=0)).tolist(), "e_total_max_abs": np.max(np.abs(et_[m]), axis=0).tolist(),
                            "e_schedule_rmse": np.sqrt(np.mean(esc_[m] ** 2, axis=0)).tolist()}
            ent["max_abs_rmse_change_vs_mid"] = max(float(np.max(np.abs(np.array(ent[k]["e_total_rmse"]) - np.array(ent["t0_mid"]["e_total_rmse"])))) for k in ("t0_before", "t0_after"))
            sens["per_window"][wn_] = ent
        res["send_interval_sensitivity"] = sens
    res["metrics"] = metrics

    # ---- delay estimates from velocity correlation (+-0.4 s on the 8 ms ladder; weak/ambiguous/boundary = not identifiable)
    lag = {}
    if moving:
        g = nominal if hf else gcfg["lag_correlation"]["grid_s"]
        s = gcfg["lag_correlation"]["search_s"]
        vn = v_nominal(t_c, dq, T, t0)
        w_lo, w_hi = t0 - 0.2, t0 + tau_s + T + 1.0
        for i in moving_idx:
            ent = {"vs_nominal_actual": L.lag_estimate(t_c, vn[:, i], av[:, i], w_lo, w_hi, grid=g, search=s),
                   "vs_nominal_reference": L.lag_estimate(t_c, vn[:, i], dv[:, i], w_lo, w_hi, grid=g, search=s),
                   "servo_desired_to_actual": L.lag_estimate(t_c, dv[:, i], av[:, i], t_ref, t_ref + T + 1.0, grid=g, search=q_cfg["lag_search_s"])}
            for v in ent.values():
                v.update({"joint": J[i], "sampling_hz": 1.0 / nominal})
                v.pop("curve", None)
                v.pop("taus_s", None)
            lag[J[i]] = ent
        gates["lag_reported_for_all_moving_joints"] = sorted(lag) == sorted(J[i] for i in moving_idx)
        res["lag_note"] = ("vs_nominal_*: velocity correlation against the ORIGINAL schedule (includes the injected delay AND servo/transport); "
                           "servo_desired_to_actual: Task1-style ±0.1 s servo lag. 125 Hz cannot resolve below the 8 ms ladder; the injected delay is not a servo lag.")
    res["lag"] = lag

    # ---- curves: original-send axis and controller axis
    grid = q_cfg["grid_s"]
    gap_periods = q_cfg["max_gap_periods"] if not hf else 1e9
    arrays = {"q_ref": des, "q_act": act, "e_q": act - des, "e_v": av - dv}
    Pa_all, Ra_all = L.fk_batch(chain, act)
    Pd_all, Rd_all = L.fk_batch(chain, des)
    arrays["ee_pos_err"] = np.linalg.norm(Pa_all - Pd_all, axis=1)
    arrays["ee_rot_err"] = L.rot_angle(Ra_all, Rd_all)
    if moving:
        length_ref = T + tmg["settle_s"]
        ref_origin = t_ref
    else:
        length_ref, ref_origin = tmg["hold_s"], wins["hold"][0]
    tg, curves = A1.grid_curves(t_c, arrays, ref_origin, length_ref, grid, nominal, gap_periods)
    out_arrays = {"t_rel": tg, "t_ref": ref_origin, "joints": np.array(J)}
    out_arrays.update(curves)
    if moving:
        # the same curves on the sub-sample fitted start (removes the up-to-8 ms quantisation of t_ref that would otherwise leak speed*dt into q_actual comparisons)
        tfg, fc = A1.grid_curves(t_c, arrays, ts_fit, length_ref, grid, nominal, gap_periods)
        out_arrays.update({"fit_t_rel": tfg, "fit_t_start": ts_fit})
        out_arrays.update({"fit_" + k: v for k, v in fc.items()})
    if moving:
        pre_margin = 0.5
        length_send = pre_margin + tau_s + T + tmg["settle_s"]
        ts, sc = A1.grid_curves(t_c, {"q_ref": des, "q_act": act}, t0 - pre_margin, length_send, grid, nominal, gap_periods)
        tg_abs = t0 - pre_margin + np.arange(0, int(round(length_send / grid)) + 1) * grid
        qn_g = q_nominal(tg_abs, q_start, dq, T, t0)
        es_g, esc_g, et_g, _ = error_decomposition(sc["q_act"], sc["q_ref"], qn_g)
        ok = np.isfinite(sc["q_act"][:, 0])
        fk_pos = {}
        for key, (qa, qb) in {"servo": (sc["q_act"], sc["q_ref"]), "schedule": (sc["q_ref"], qn_g), "total": (sc["q_act"], qn_g)}.items():
            p_ = np.full(tg_abs.size, np.nan)
            r_ = np.full(tg_abs.size, np.nan)
            if ok.any():
                p_[ok], r_[ok] = ee_errors(chain, qa[ok], qb[ok])
            fk_pos[key] = (p_, r_)
        out_arrays.update({"snd_t_rel": tg_abs - t0, "snd_q_nom": qn_g, "snd_q_ref": sc["q_ref"], "snd_q_act": sc["q_act"], "snd_e_servo": es_g,
                           "snd_e_schedule": esc_g, "snd_e_total": et_g, "snd_ee_pos_servo": fk_pos["servo"][0], "snd_ee_pos_schedule": fk_pos["schedule"][0],
                           "snd_ee_pos_total": fk_pos["total"][0], "snd_ee_rot_servo": fk_pos["servo"][1], "snd_ee_rot_schedule": fk_pos["schedule"][1],
                           "snd_ee_rot_total": fk_pos["total"][1], "snd_t0": t0})
        res["curves_send_axis"] = {"file": "curves.npz", "grid_s": grid, "origin": "t0_mid (sender)", "starts_before_t0_s": pre_margin, "length_s": length_send,
                                   "nan_fraction": float(np.mean(np.isnan(sc["q_act"][:, 0])))}
    np.savez_compressed(os.path.join(out_dir, "curves.npz"), **out_arrays)
    res["curves"] = {"file": "curves.npz", "grid_s": grid, "length_s": length_ref, "origin": "t_ref (controller)" if moving else "hold window start",
                     "nan_fraction": float(np.mean(np.isnan(curves["e_q"][:, 0])))}
    return _finish(out_dir, res, gates)


def _finish(out_dir, res, gates):
    res["pass"] = bool(all(gates.values()))
    res["failed_gates"] = [k for k, v in gates.items() if not v]
    res["note"] = "pass = every measurement-quality / protocol gate passed; it says nothing about how accurate the arm is or about a research hypothesis"
    with open(os.path.join(out_dir, "run_metrics.json"), "w") as f:
        json.dump(res, f, indent=1, default=float)
    return res


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--run-dir", required=True)
    r.add_argument("--out", default=None, help="output directory (default: the run dir); never overwrites an existing run_metrics.json")
    r.add_argument("--hf", action="store_true")
    r.add_argument("--config", default=CONFIG)
    a = ap.parse_args()
    try:
        res = analyze_run(a.run_dir, a.hf, yaml.safe_load(_text(a.config)), a.out)
    except (L.InvalidInput, OSError, KeyError, ValueError, AssertionError) as e:
        print("INVALID INPUT:", e)
        sys.exit(2)
    print(json.dumps({"run_id": res["run_id"], "pass": res["pass"], "failed_gates": res["failed_gates"], "invalid_reasons": res["invalid_reasons"]}, indent=1))
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
