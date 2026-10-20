"""Pure-data acceptance logic for task0 feedback records (stdlib only; no ROS imports).

evaluate_feedback(js_rows, st_rows, clock_times, command, limits, policy) -> (checks, metrics)

Row layouts (same as check_feedback.py / bag_to_csv.py):
  js_rows : [t, pos x6, vel x6, eff x6]                       (/joint_states, simulated time)
  st_rows : [t, des x6, act x6, err x6, desvel x6, actvel x6] (controller state)
  clock_times : simulated seconds from /clock
command : None (hold) or {"sim_time_sent", "q_start", "q_target", "duration_s"}
limits  : {joint: {"lower","upper","velocity","effort"}}
policy  : thresholds; see DEFAULT_POLICY. Tolerances are connectivity criteria, not research
          performance targets. Nothing here copies desired values into actual or vice versa.

Design rule (task0.7): every check must be able to FAIL on bad data. Early-stopped streams,
gaps, reversed motion, sustained departure from the reference, out-of-limit or non-finite
values and windows too short to contain the commanded move are all rejected.
"""
import math

JOINTS = ["ur5_shoulder_pan_joint", "ur5_shoulder_lift_joint", "ur5_elbow_joint",
          "ur5_wrist_1_joint", "ur5_wrist_2_joint", "ur5_wrist_3_joint"]

DEFAULT_POLICY = {
    "window_start": 0.0,          # simulated time at which recording started
    "window_end": None,           # simulated time at which recording stopped (start + requested duration)
    "joint_rate_hz": 125.0,       # configured publish rate of joint_states and controller state
    "max_gap_periods": 10,        # largest allowed dt between samples, in publish periods (10 -> 80 ms at 125 Hz)
    "min_coverage": 0.95,         # fraction of the requested window every stream must cover
    "clock_max_gap_s": 0.05,      # /clock is 2 kHz; allow 50 ms
    "goal_tol_rad": 0.1,          # existing controller goal tolerance (ur5_controllers.yaml constraints.goal)
    "traj_tol_rad": 0.1,          # existing controller trajectory tolerance
    "min_move_fraction": 0.5,     # at least half of each commanded offset, in the commanded direction
    "min_settle_after_move_s": 1.0,
    "hold_range_tol_rad": 0.05,   # hold: max-min of each joint
    "pose_change_tol": 1e-3,      # fixed-base check on GetModelState pose
    "limit_eps": 1e-6,
    "check_velocity_limit": True,
    "check_effort_limit": True,
}


def _finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def _stream(ts, name, policy, expect_period, max_gap, checks, metrics):
    """Coverage / monotonicity / gap checks for one time series."""
    m = {"n": len(ts)}
    ok_n = len(ts) >= 3
    checks[name + "_has_samples"] = ok_n
    if not ok_n:
        checks[name + "_time_strictly_increasing"] = False
        checks[name + "_covers_window"] = False
        checks[name + "_max_gap_ok"] = False
        metrics[name] = m
        return
    dts = [b - a for a, b in zip(ts, ts[1:])]
    checks[name + "_time_strictly_increasing"] = all(d > 0 for d in dts) and all(_finite(t) for t in ts)
    ws, we = policy["window_start"], policy["window_end"]
    req = we - ws
    covered = min(ts[-1], we) - max(ts[0], ws)
    m.update({"first": ts[0], "last": ts[-1], "span": ts[-1] - ts[0], "covered_s": covered, "max_dt": max(dts),
              "mean_hz": (len(ts) - 1) / (ts[-1] - ts[0]) if ts[-1] > ts[0] else None})
    # coverage: fraction of the window covered AND the stream must reach both ends (within one allowed gap)
    checks[name + "_covers_window"] = bool(covered >= policy["min_coverage"] * req and ts[0] <= ws + max_gap and ts[-1] >= we - max_gap)
    checks[name + "_max_gap_ok"] = max(dts) <= max_gap
    metrics[name] = m


def evaluate_feedback(js_rows, st_rows, clock_times, command, limits, policy):
    p = dict(DEFAULT_POLICY)
    p.update(policy)
    checks, metrics = {}, {"policy": p}
    ws, we = p["window_start"], p["window_end"]
    if we is None or we <= ws:
        raise ValueError("policy.window_end must be > window_start")
    period = 1.0 / p["joint_rate_hz"]
    max_gap = p["max_gap_periods"] * period

    # ---- input validity: refuse windows that cannot contain the commanded move
    if command is not None:
        need = command["duration_s"] + p["min_settle_after_move_s"]
        # the command is issued at the start of recording, so the window must hold the move plus a settle period
        metrics["required_window_s"] = need
        checks["window_long_enough_for_command"] = (we - ws) >= need - 1e-9
    else:
        checks["window_long_enough_for_command"] = True

    # ---- stream presence, ordering, coverage, gaps
    _stream(list(clock_times), "clock", p, None, p["clock_max_gap_s"], checks, metrics)
    _stream([r[0] for r in js_rows], "joint_states", p, period, max_gap, checks, metrics)
    _stream([r[0] for r in st_rows], "controller_state", p, period, max_gap, checks, metrics)

    # ---- shape and finiteness
    checks["joint_states_rows_well_formed"] = bool(js_rows) and all(len(r) == 19 for r in js_rows)
    checks["controller_state_rows_well_formed"] = bool(st_rows) and all(len(r) == 31 for r in st_rows)
    checks["six_joints_present"] = checks["joint_states_rows_well_formed"] and checks["controller_state_rows_well_formed"]
    checks["all_values_finite"] = all(_finite(x) for r in js_rows for x in r) and all(_finite(x) for r in st_rows for x in r)
    if not (checks["joint_states_rows_well_formed"] and checks["controller_state_rows_well_formed"] and checks["all_values_finite"]):
        # nothing further can be evaluated reliably
        checks["limits_respected"] = False
        checks["tracking_within_trajectory_tolerance"] = False
        checks["motion_direction_and_extent"] = False if command is not None else True
        checks["final_within_goal_tolerance"] = False
        checks["hold_range_ok"] = False if command is None else True
        return checks, metrics

    pos = [r[1:7] for r in js_rows]; vel = [r[7:13] for r in js_rows]; eff = [r[13:19] for r in js_rows]

    # ---- joint limits (from expanded URDF), positions/velocities/efforts of the measured state
    viol = []
    eps = p["limit_eps"]
    for i, j in enumerate(JOINTS):
        lim = limits[j]
        if min(r[i] for r in pos) < lim["lower"] - eps or max(r[i] for r in pos) > lim["upper"] + eps:
            viol.append(j + ":position")
        if p["check_velocity_limit"] and max(abs(r[i]) for r in vel) > lim["velocity"] + eps:
            viol.append(j + ":velocity")
        if p["check_effort_limit"] and max(abs(r[i]) for r in eff) > lim["effort"] * (1 + 1e-3) + eps:
            viol.append(j + ":effort")
    checks["limits_respected"] = not viol
    metrics["limit_violations"] = viol

    # ---- tracking: actual vs the controller's instantaneous reference at the SAME timestamp
    des = [r[1:7] for r in st_rows]; act = [r[7:13] for r in st_rows]
    tracking = [[a - d for a, d in zip(ar, dr)] for ar, dr in zip(act, des)]  # actual - desired
    max_abs = max(abs(x) for r in tracking for x in r)
    metrics["max_abs_tracking_error_rad"] = max_abs
    checks["tracking_within_trajectory_tolerance"] = max_abs <= p["traj_tol_rad"]

    # ---- motion or hold
    if command is not None:
        q0, qt = command["q_start"], command["q_target"]
        q_end = pos[-1]
        okdir, disp = True, {}
        for i, j in enumerate(JOINTS):
            off = qt[i] - q0[i]
            if abs(off) < 1e-6:
                continue
            d = q_end[i] - q0[i]
            disp[j] = {"commanded_offset": off, "achieved_displacement": d}
            if d * off <= 0 or abs(d) < p["min_move_fraction"] * abs(off):
                okdir = False
        metrics["displacement"] = disp
        checks["motion_direction_and_extent"] = okdir
        # final error is defined as actual - command_target
        final_err = [q_end[i] - qt[i] for i in range(6)]
        metrics["final_error_actual_minus_target_rad"] = dict(zip(JOINTS, final_err))
        checks["final_within_goal_tolerance"] = max(abs(x) for x in final_err) <= p["goal_tol_rad"]
        checks["hold_range_ok"] = True
    else:
        checks["motion_direction_and_extent"] = True
        checks["final_within_goal_tolerance"] = True
        rng = [max(r[i] for r in pos) - min(r[i] for r in pos) for i in range(6)]
        metrics["hold_position_range_rad"] = dict(zip(JOINTS, rng))
        checks["hold_range_ok"] = max(rng) <= p["hold_range_tol_rad"]
    return checks, metrics


def model_pose_checks(start, end, ok_start, ok_end, tol):
    """Fixed-base check. Service failure is a failure (never default to a zero pose)."""
    checks = {"model_state_service_ok": bool(ok_start and ok_end)}
    if not checks["model_state_service_ok"] or start is None or end is None or len(start) != 7 or len(end) != 7:
        checks["base_fixed_pose_change_ok"] = False
        return checks, {"model_pose_max_abs_change": None}
    change = max(abs(a - b) for a, b in zip(start, end))
    checks["base_fixed_pose_change_ok"] = _finite(change) and change < tol
    return checks, {"model_pose_max_abs_change": change}


def is_pass(checks):
    return all(bool(v) for v in checks.values())
