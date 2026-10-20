#!/usr/bin/env python3
"""Task1 measurement/analysis library (numpy; runs in forem-dev or anywhere numpy exists).

Pure functions, no ROS. Conventions (fixed by doc/tasks/task1/PROCEDURE.md):
  e_q = q_actual - q_desired, e_v = v_actual - v_desired, both taken from ONE controller state message
  (header stamp). Nothing is ever copied from desired/command into actual.
  Joints are always mapped by NAME, never by position in a message.
  No interpolation across gaps or across reset; cross-stream comparisons use nearest neighbours inside a
  stated time distance and report the distance.
"""
import math
import xml.etree.ElementTree as ET

import numpy as np

JOINTS = ["ur5_shoulder_pan_joint", "ur5_shoulder_lift_joint", "ur5_elbow_joint",
          "ur5_wrist_1_joint", "ur5_wrist_2_joint", "ur5_wrist_3_joint"]


class InvalidInput(Exception):
    """Data cannot be analysed (missing/duplicate joints, non-finite values, wrong shapes)."""


# ---------------------------------------------------------------- name mapping
def map_by_name(names, values, joints=JOINTS):
    """Return values ordered as `joints`. Missing/duplicate/unknown-count names are an error."""
    names = list(names)
    if len(set(names)) != len(names):
        raise InvalidInput("duplicate joint names in message: %s" % names)
    idx = {n: i for i, n in enumerate(names)}
    miss = [j for j in joints if j not in idx]
    if miss:
        raise InvalidInput("joints missing from message: %s" % miss)
    if len(values) != len(names):
        raise InvalidInput("%d values for %d names" % (len(values), len(names)))
    return [values[idx[j]] for j in joints]


def require_finite(a, what):
    a = np.asarray(a, dtype=float)
    if not np.all(np.isfinite(a)):
        raise InvalidInput("non-finite values in %s" % what)
    return a


# ---------------------------------------------------------------- stream quality
def stream_quality(t, t0, t1, nominal, max_gap_periods=3, dedup_rate_max=0.01, coverage_min=0.99):
    """Quality of one stream's raw timestamps t (arrival order) for the window [t0, t1].

    Fails on: any backward step (clock went back / reordering), duplicate rate above the limit, an
    inside-window gap (including the two window edges) above max_gap_periods*nominal, coverage below the limit.
    Returns a dict with `pass` and, for a failed gate, `reasons`. Never fills gaps.
    """
    t = np.asarray(t, dtype=float)
    res = {"window": [float(t0), float(t1)], "nominal_period_s": nominal, "reasons": []}
    if t.size == 0 or not np.all(np.isfinite(t)):
        res.update(n_total=int(t.size), pass_=False)
        res["reasons"].append("empty or non-finite timestamps")
        res["pass"] = False
        return res
    dt_all = np.diff(t)
    backward = int(np.sum(dt_all < 0))
    # gaps are judged on the time-ordered, de-duplicated samples inside the window
    w = t[(t >= t0) & (t <= t1)]
    n_in = int(w.size)
    dup = int(np.sum(np.diff(w) == 0)) if n_in > 1 else 0
    res.update({"n_total": int(t.size), "n_in_window": n_in, "backward_steps_total": backward,
                "duplicates_in_window": dup, "dedup_rate": (dup / n_in) if n_in else None})
    if n_in < 2:
        res["reasons"].append("fewer than 2 samples in window")
        res["pass"] = False
        return res
    ws = np.unique(np.sort(w))
    gaps = np.diff(ws)
    edge_lo, edge_hi = float(ws[0] - t0), float(t1 - ws[-1])
    all_gaps = np.concatenate([gaps, [edge_lo, edge_hi]])
    limit = max_gap_periods * nominal
    bad = all_gaps[all_gaps > limit + 1e-9]
    length = float(t1 - t0)
    res.update({"max_gap_s": float(all_gaps.max()), "gap_limit_s": limit, "edge_gap_start_s": edge_lo, "edge_gap_end_s": edge_hi,
                "gaps_over_limit": int(bad.size), "coverage": float(1.0 - bad.sum() / length) if length > 0 else None,
                "mean_hz": float((ws.size - 1) / (ws[-1] - ws[0])) if ws[-1] > ws[0] else None})
    if backward:
        res["reasons"].append("%d backward timestamp steps" % backward)
    if res["dedup_rate"] is not None and res["dedup_rate"] > dedup_rate_max:
        res["reasons"].append("duplicate rate %.4f > %.4f" % (res["dedup_rate"], dedup_rate_max))
    if bad.size:
        res["reasons"].append("gap %.4f s > %.4f s" % (all_gaps.max(), limit))
    if res["coverage"] is None or res["coverage"] < coverage_min:
        res["reasons"].append("coverage %s < %.3f" % (res["coverage"], coverage_min))
    res["pass"] = not res["reasons"]
    return res


def dedupe_sorted(t, *arrays):
    """Keep the first of samples with equal timestamps; arrays are row-aligned with t (already ordered)."""
    t = np.asarray(t, dtype=float)
    keep = np.ones(t.size, dtype=bool)
    keep[1:] = np.diff(t) != 0
    return (t[keep],) + tuple(np.asarray(a)[keep] for a in arrays)


# ---------------------------------------------------------------- tracking metrics
def window_mask(t, t0, t1):
    t = np.asarray(t)
    return (t >= t0) & (t <= t1)


def error_stats(e, t=None, final_window_s=1.0):
    """Per-column RMSE, max|e|, mean, and mean over the last final_window_s of the samples (needs t)."""
    e = np.asarray(e, dtype=float)
    out = {"n": int(e.shape[0]), "rmse": np.sqrt(np.mean(e ** 2, axis=0)).tolist(), "max_abs": np.max(np.abs(e), axis=0).tolist(),
           "mean": np.mean(e, axis=0).tolist()}
    if t is not None and e.shape[0]:
        t = np.asarray(t)
        m = t >= t[-1] - final_window_s
        out["final_mean"] = np.mean(e[m], axis=0).tolist()
    return out


def scalar_stats(x):
    x = np.asarray(x, dtype=float)
    return {"n": int(x.size), "rmse": float(np.sqrt(np.mean(x ** 2))), "max": float(np.max(x)), "mean": float(np.mean(x))}


# ---------------------------------------------------------------- t_ref and windows
def find_t_ref(t, desired, hold_ref, moving_idx, thr=1e-6):
    """First time any MOVING joint's desired differs from the hold reference by more than thr (per joint too).

    Returns (t_ref, per_joint dict). Raises InvalidInput if none of them ever leaves the hold reference.
    """
    t = np.asarray(t, dtype=float)
    d = np.asarray(desired, dtype=float)
    per = {}
    for i in moving_idx:
        hit = np.nonzero(np.abs(d[:, i] - hold_ref[i]) > thr)[0]
        per[JOINTS[i]] = float(t[hit[0]]) if hit.size else None
    vals = [v for v in per.values() if v is not None]
    if not vals:
        raise InvalidInput("desired never left the hold reference: no motion observed")
    return min(vals), per


# ---------------------------------------------------------------- lag diagnostic
def lag_estimate(t, v_des, v_act, t0, t1, grid=0.008, search=0.1, min_peak_vel=1e-3, flat_tol=1e-3, multimodal_frac=0.98):
    """Cross-correlation of v_act(t) with v_des(t - tau), tau in [-search, search] on a `grid` ladder.

    Uses only samples of ONE stream pair (same controller messages) inside a time range; linear interpolation
    is done inside a stream between consecutive samples whose spacing is <= 3 nominal grid steps (else NaN).
    Not identifiable (returns identifiable=False, never 0 ms) when: too little velocity energy, flat curve,
    peak on the search boundary, or several near-equal peaks. `below_resolution` flags |tau|<grid.
    This is a diagnostic of the normal servo response, not a pure transport delay.
    """
    t = np.asarray(t, dtype=float)
    v_des = np.asarray(v_des, dtype=float)
    v_act = np.asarray(v_act, dtype=float)
    taus = np.arange(-round(search / grid), round(search / grid) + 1) * grid
    res = {"grid_s": grid, "search_s": search, "taus_s": taus.tolist(), "identifiable": False, "reason": None,
           "tau_s": None, "peak_corr": None, "curve": None, "below_resolution": None, "resolvable": False,
           "v_des_peak": float(np.max(np.abs(v_des))) if v_des.size else 0.0}
    if t.size < 10 or np.max(np.abs(v_des)) < min_peak_vel:
        res["reason"] = "insufficient velocity energy (peak |v_des| %.2e < %.1e)" % (res["v_des_peak"], min_peak_vel)
        return res

    def interp(x, tq):
        y = np.interp(tq, t, x, left=np.nan, right=np.nan)
        j = np.searchsorted(t, tq)
        j = np.clip(j, 1, t.size - 1)
        ok = (t[j] - t[j - 1]) <= 3 * grid + 1e-9
        y[~ok] = np.nan
        return y

    tg = np.arange(t0, t1 + 1e-12, grid)
    va = interp(v_act, tg)
    curve = []
    for tau in taus:
        vd = interp(v_des, tg - tau)
        ok = np.isfinite(va) & np.isfinite(vd)
        if ok.sum() < 10:
            curve.append(float("nan"))
            continue
        num = float(np.sum(va[ok] * vd[ok]))
        den = float(np.sqrt(np.sum(va[ok] ** 2) * np.sum(vd[ok] ** 2)))
        curve.append(num / den if den > 0 else float("nan"))
    c = np.array(curve)
    res["curve"] = c.tolist()
    if not np.all(np.isfinite(c)):
        res["reason"] = "correlation undefined for part of the search range (gap or zero energy)"
        return res
    k = int(np.argmax(c))
    res["peak_corr"] = float(c[k])
    if c.max() - c.min() < flat_tol:
        res["reason"] = "flat correlation curve"
        return res
    if k == 0 or k == c.size - 1:
        res["reason"] = "peak on the search boundary"
        res["tau_s_at_boundary"] = float(taus[k])
        return res
    near = [i for i in range(1, c.size - 1) if c[i] >= c[i - 1] and c[i] >= c[i + 1] and c[i] >= multimodal_frac * c[k]]
    if len(near) > 1:
        res["reason"] = "multiple near-equal peaks at tau=%s" % [float(taus[i]) for i in near]
        return res
    # parabolic refinement is only reported, the ladder value is the estimate
    y0, y1, y2 = c[k - 1], c[k], c[k + 1]
    den = y0 - 2 * y1 + y2
    refined = float(taus[k] + 0.5 * (y0 - y2) / den * grid) if den != 0 else float(taus[k])
    res.update({"identifiable": True, "tau_s": float(taus[k]), "tau_refined_s": refined,
                "below_resolution": bool(abs(taus[k]) < grid - 1e-12)})
    res["resolvable"] = not res["below_resolution"]
    if res["below_resolution"]:
        res["note"] = "|tau| below the %.0f ms grid: sampling cannot resolve a lag this small" % (grid * 1e3)
    return res


# ---------------------------------------------------------------- source audit
def audit_backfill(act, des, js_pos=None, target=None, tol=1e-12):
    """Detect that "actual" is really the reference/command.

    Flags: actual identical to desired over the window although desired moves; actual equals the commanded
    target for the whole window; joint_states equal to desired. Returns dict, `pass` False on any flag.
    """
    act = np.asarray(act, dtype=float)
    des = np.asarray(des, dtype=float)
    flags = []
    moving = float(np.max(np.ptp(des, axis=0))) > 1e-6
    if act.shape == des.shape and moving and float(np.max(np.abs(act - des))) <= tol:
        flags.append("actual identical to desired while desired moves (backfilled)")
    if target is not None and act.shape[0] > 10:
        tg = np.asarray(target, dtype=float)
        if float(np.max(np.abs(act - tg))) <= tol:
            flags.append("actual constant equal to the commanded target")
    if js_pos is not None:
        js = np.asarray(js_pos, dtype=float)
        if js.shape == des.shape and moving and float(np.max(np.abs(js - des))) <= tol:
            flags.append("joint_states identical to desired while desired moves")
    return {"pass": not flags, "flags": flags, "desired_moves": moving,
            "max_abs_act_minus_des": float(np.max(np.abs(act - des))) if act.shape == des.shape else None}


# ---------------------------------------------------------------- nearest-neighbour pairing
def nearest_pairs(ta, tb, max_dt):
    """For each time in ta, the index of the nearest time in tb and the signed dt (tb - ta); -1 if none within max_dt.

    ta, tb must be sorted. Reports nothing about values: the caller decides which value pairs to compare.
    """
    ta = np.asarray(ta, dtype=float)
    tb = np.asarray(tb, dtype=float)
    if tb.size == 0:
        return np.full(ta.size, -1), np.full(ta.size, np.nan)
    j = np.searchsorted(tb, ta)
    j0 = np.clip(j - 1, 0, tb.size - 1)
    j1 = np.clip(j, 0, tb.size - 1)
    pick = np.where(np.abs(tb[j0] - ta) <= np.abs(tb[j1] - ta), j0, j1)
    dt = tb[pick] - ta
    pick = np.where(np.abs(dt) <= max_dt + 1e-12, pick, -1)
    return pick, dt


# ---------------------------------------------------------------- URDF forward kinematics
def _rpy(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def _axis_angle(axis, a):
    ax = np.asarray(axis, dtype=float)
    ax = ax / np.linalg.norm(ax)
    x, y, z = ax
    c, s = math.cos(a), math.sin(a)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def parse_chain(urdf_xml, base_link, tip_link):
    """Joint chain from base_link to tip_link as a list of dicts (name, type, origin T, axis), found by walking parents."""
    root = ET.fromstring(urdf_xml)
    by_child = {}
    for j in root.findall("joint"):
        by_child[j.find("child").get("link")] = j
    chain, link = [], tip_link
    while link != base_link:
        if link not in by_child:
            raise InvalidInput("link %s is not connected to %s" % (tip_link, base_link))
        j = by_child[link]
        o = j.find("origin")
        xyz = [float(v) for v in (o.get("xyz", "0 0 0").split() if o is not None else "0 0 0".split())]
        rpy = [float(v) for v in (o.get("rpy", "0 0 0").split() if o is not None else "0 0 0".split())]
        T = np.eye(4)
        T[:3, :3] = _rpy(*rpy)
        T[:3, 3] = xyz
        ax = j.find("axis")
        chain.append({"name": j.get("name"), "type": j.get("type"), "T": T,
                      "axis": [float(v) for v in ax.get("xyz").split()] if ax is not None else [1.0, 0.0, 0.0]})
        link = j.find("parent").get("link")
    chain.reverse()
    return chain


def fk(chain, q_by_name, joints_out=False):
    """T_base_tip (4x4). q_by_name: dict joint name -> angle. Fixed joints ignore q. With joints_out also the
    list of (joint name, origin position, axis in base frame) for each revolute joint (for Jacobian bounds)."""
    T = np.eye(4)
    info = []
    for j in chain:
        T = T @ j["T"]
        if j["type"] in ("revolute", "continuous"):
            R = T[:3, :3]
            info.append((j["name"], T[:3, 3].copy(), R @ (np.asarray(j["axis"]) / np.linalg.norm(j["axis"]))))
            Tj = np.eye(4)
            Tj[:3, :3] = _axis_angle(j["axis"], q_by_name[j["name"]])
            T = T @ Tj
        elif j["type"] == "prismatic":
            raise InvalidInput("prismatic joints are not supported")
    return (T, info) if joints_out else T


def _axis_angle_batch(axis, ang):
    ax = np.asarray(axis, dtype=float)
    ax = ax / np.linalg.norm(ax)
    x, y, z = ax
    c = np.cos(ang)[:, None, None]
    s = np.sin(ang)[:, None, None]
    C = 1 - c
    K = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return c * np.eye(3) + s * K + C * np.outer(ax, ax)


def fk_batch(chain, q, joints=JOINTS, with_origins=False):
    """Vectorised FK. q: (N,6) in `joints` order -> positions (N,3), rotations (N,3,3)
    (and revolute-joint origins (N,nj,3) with with_origins, for the Jacobian bounds)."""
    q = np.asarray(q, dtype=float)
    N = q.shape[0]
    idx = {n: i for i, n in enumerate(joints)}
    T = np.tile(np.eye(4), (N, 1, 1))
    origins = []
    for j in chain:
        T = T @ j["T"]
        if j["type"] in ("revolute", "continuous"):
            origins.append(T[:, :3, 3].copy())
            Tj = np.tile(np.eye(4), (N, 1, 1))
            Tj[:, :3, :3] = _axis_angle_batch(j["axis"], q[:, idx[j["name"]]])
            T = T @ Tj
        elif j["type"] == "prismatic":
            raise InvalidInput("prismatic joints are not supported")
    out = (T[:, :3, 3], T[:, :3, :3])
    return out + (np.stack(origins, axis=1),) if with_origins else out


QUAT_NORM_MIN = 1e-6   # task1.7: Gazebo publishes unit quaternions; a norm below this (or non-finite) cannot encode an orientation


def quat_norm_ok(q):
    """True iff q is a finite 4-vector with norm >= QUAT_NORM_MIN."""
    q = np.asarray(q, dtype=float)
    if q.shape != (4,) or not np.all(np.isfinite(q)):
        return False
    n = float(np.linalg.norm(q))
    return bool(np.isfinite(n) and n >= QUAT_NORM_MIN)


def quat_to_R(q):
    """(x, y, z, w) -> rotation matrix. q and -q give the same matrix.
    Raises InvalidInput for non-finite components or a (near-)zero norm instead of dividing by it (task1.7)."""
    q = np.asarray(q, dtype=float)
    if not quat_norm_ok(q):
        raise InvalidInput("invalid quaternion %s: non-finite or norm < %g" % (q.tolist(), QUAT_NORM_MIN))
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def rot_angle(Ra, Rb):
    """SO(3) geodesic angle between rotation matrices (broadcasts over a leading axis)."""
    Rrel = np.matmul(np.swapaxes(Ra, -1, -2), Rb)
    c = (np.trace(Rrel, axis1=-2, axis2=-1) - 1.0) / 2.0
    return np.arccos(np.clip(c, -1.0, 1.0))


def ee_bounds_batch(chain, q, vel_limit, joints=JOINTS):
    """Conservative URDF-based bounds per sample: v_ee <= sum_i vlim_i*|p_tip - p_joint_i| (m/s), omega <= sum_i vlim_i (rad/s).
    vel_limit: dict joint name -> URDF velocity limit. Returns (v_bound (N,), w_bound (N,))."""
    P, _, O = fk_batch(chain, q, joints, with_origins=True)
    names = [j["name"] for j in chain if j["type"] in ("revolute", "continuous")]
    vl = np.array([vel_limit[n] for n in names])
    return np.sum(vl[None, :] * np.linalg.norm(P[:, None, :] - O, axis=2), axis=1), np.full(q.shape[0], float(vl.sum()))


# ---------------------------------------------------------------- command messages (task1.7)
COMMAND_SCHEMA = "task1-command/1"
_POINT_FIELDS = ("positions", "velocities", "accelerations", "effort")


def command_record(msg):
    """JointTrajectory message -> plain dict, the ONE schema used by the sender (commands.json) and by the bag converter
    (bag_commands.json). Times are exact [secs, nsecs] integers. Works on rospy/rosbag messages and on duck-typed objects."""
    return {"schema": COMMAND_SCHEMA,
            "header": {"stamp": [int(msg.header.stamp.secs), int(msg.header.stamp.nsecs)], "frame_id": str(msg.header.frame_id)},
            "joint_names": [str(n) for n in msg.joint_names],
            "points": [dict({f: [float(x) for x in getattr(p, f)] for f in _POINT_FIELDS},
                            time_from_start=[int(p.time_from_start.secs), int(p.time_from_start.nsecs)]) for p in msg.points]}


def compare_commands(sent, bag_records):
    """Check the sent command record against ALL command messages found in the bag.

    Compares header stamp (secs, nsecs), frame_id, joint_names, the number of points and, for EVERY point, positions,
    velocities, accelerations, effort and time_from_start, exactly (NaN never equals anything; non-finite values are flagged).
    `sent` is a task1-command/1 record or the legacy pre-task1.7 commands.json message (header_stamp, float time_from_start,
    no frame_id): for legacy records frame_id cannot be compared and this is stated in `not_compared`.
    `bag_records` is the list from bag_commands.json: [{"t_bag", "message": task1-command/1 record}, ...].
    Returns {"match": bool, "mismatches": [...], "not_compared": [...], "fields": [...]}.
    """
    mism, notes = [], []
    res = {"mismatches": mism, "not_compared": notes, "bag_messages": len(bag_records), "schema_sent": sent.get("schema", "legacy"),
           "fields": ["header.stamp", "header.frame_id", "joint_names", "n_points"] + ["points[i].%s" % f for f in _POINT_FIELDS + ("time_from_start",)]}
    if len(bag_records) != 1:
        mism.append("expected exactly 1 command message in the bag, found %d" % len(bag_records))
        res["match"] = False
        return res
    b = bag_records[0].get("message", {})
    if b.get("schema") != COMMAND_SCHEMA:
        mism.append("bag record schema %r is not %s (re-convert the bag with the current task1_bag_to_csv.py)" % (b.get("schema"), COMMAND_SCHEMA))
        res["match"] = False
        return res
    legacy = sent.get("schema") != COMMAND_SCHEMA
    if legacy:
        s_stamp, s_frame = list(sent["header_stamp"]), None
        notes.append("header.frame_id: legacy sent record does not store it")
    else:
        s_stamp, s_frame = list(sent["header"]["stamp"]), sent["header"]["frame_id"]
    if [int(x) for x in s_stamp] != b["header"]["stamp"]:
        mism.append("header.stamp sent %s bag %s" % (s_stamp, b["header"]["stamp"]))
    if s_frame is not None and s_frame != b["header"]["frame_id"]:
        mism.append("header.frame_id sent %r bag %r" % (s_frame, b["header"]["frame_id"]))
    if list(sent["joint_names"]) != b["joint_names"]:
        mism.append("joint_names sent %s bag %s" % (sent["joint_names"], b["joint_names"]))
    sp, bp = sent["points"], b["points"]
    if len(sp) != len(bp):
        mism.append("number of points sent %d bag %d" % (len(sp), len(bp)))
    for i, (x, y) in enumerate(zip(sp, bp)):
        for f in _POINT_FIELDS:
            xs, ys = [float(v) for v in x.get(f, [])], y[f]
            if len(xs) != len(ys) or any(not (u == v) for u, v in zip(xs, ys)):
                mism.append("point %d %s sent %s bag %s" % (i, f, xs, ys))
            if any(not math.isfinite(v) for v in xs + ys):
                mism.append("point %d %s contains non-finite values" % (i, f))
        if legacy:
            t_b = y["time_from_start"][0] + y["time_from_start"][1] * 1e-9
            if not abs(float(x["time_from_start"]) - t_b) <= 1e-12:
                mism.append("point %d time_from_start sent %r bag %r s" % (i, x["time_from_start"], t_b))
        elif [int(v) for v in x["time_from_start"]] != y["time_from_start"]:
            mism.append("point %d time_from_start sent %s bag %s" % (i, x["time_from_start"], y["time_from_start"]))
    res["match"] = not mism
    return res
