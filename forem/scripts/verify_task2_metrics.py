#!/usr/bin/env python3
"""Independent hand-recomputation of stored Task2 run results (stdlib only: csv/json/math/xml - shares NO code with task1_lib, analyze_task1,
analyze_task2, task2_delay_queue).

For every valid run of a run index it re-reads the raw files and re-derives, with its own formulas:
  * the command chain: downstream/upstream message counts, downstream message == sent message (every field), proxy events: t_due = t_in + tau,
    eps = t_pub_before - t_in - tau in [0, 8 ms], d_queue, event/file agreement, no forbidden events, hash fields consistent between events
  * t_ref (first controller `desired` change > 1e-6 rad from the pre-hold median), the sender midpoint t0, the windows
  * q_nom = q_start + dq*(3u^2-2u^3) at the stored t0, e_servo/e_schedule/e_total RMSE / max|.| / mean for each stored window and joint,
    the identity e_total = e_servo + e_schedule per sample, and the end-effector position error |FK(a)-FK(b)| via an independent URDF forward kinematics
  * the stored fitted start: residual of `desired` against the cubic at the stored start
Exit 0 iff every comparison agrees (abs 1e-10 or rel 1e-6, whichever is looser; FK positions abs 1e-9 m). Prints one line per run and each mismatch.
(index entries may carry `raw_dir` for the raw run and `results_dir` for the metrics, as written by reanalyze_task2.py.)
Usage: verify_task2_metrics.py --index results/.../run_index.json [--runs N] [--seed S] [--only-run RUN_ID] [--report FILE]
"""
import argparse
import csv
import json
import math
import os
import random
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
JN = ["ur5_shoulder_pan_joint", "ur5_shoulder_lift_joint", "ur5_elbow_joint", "ur5_wrist_1_joint", "ur5_wrist_2_joint", "ur5_wrist_3_joint"]
TOL_ABS, TOL_REL = 1e-10, 1e-6
EPS_MAX_NS = 8_000_000


def close(a, b, abs_tol=TOL_ABS, rel=TOL_REL):
    return abs(a - b) <= max(abs_tol, rel * abs(b))


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


# ---------------------------------------------------------------- independent FK (plain lists)
def mm(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def rpy(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    Rz = [[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]]
    Ry = [[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]]
    Rx = [[1, 0, 0], [0, cr, -sr], [0, sr, cr]]
    return mm(Rz, mm(Ry, Rx))


def rodrigues(ax, th):
    n = math.sqrt(sum(a * a for a in ax))
    x, y, z = (a / n for a in ax)
    c, s = math.cos(th), math.sin(th)
    return [[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
            [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
            [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]]


def load_chain(urdf, base, tip):
    root = ET.fromstring(urdf)
    by_child = {j.find("child").get("link"): j for j in root.findall("joint")}
    chain, link = [], tip
    while link != base:
        j = by_child[link]
        o = j.find("origin")
        xyz = [float(v) for v in (o.get("xyz", "0 0 0").split() if o is not None else ["0", "0", "0"])]
        rp = [float(v) for v in (o.get("rpy", "0 0 0").split() if o is not None else ["0", "0", "0"])]
        ax = j.find("axis")
        chain.append((j.get("name"), j.get("type"), xyz, rpy(*rp), [float(v) for v in ax.get("xyz").split()] if ax is not None else [1, 0, 0]))
        link = j.find("parent").get("link")
    chain.reverse()
    return chain


def fk_pos(chain, q):
    R = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    p = [0.0, 0.0, 0.0]
    for name, typ, xyz, Ro, ax in chain:
        p = [p[i] + sum(R[i][k] * xyz[k] for k in range(3)) for i in range(3)]
        R = mm(R, Ro)
        if typ in ("revolute", "continuous"):
            R = mm(R, rodrigues(ax, q[JN.index(name)]))
    return p


def cubic(u):
    u = min(1.0, max(0.0, u))
    return 3 * u * u - 2 * u ** 3


# ---------------------------------------------------------------- per-run verification
def verify_run(rec, say):
    # a re-analysis index (reanalyze_task2.py) keeps the raw run in `raw_dir` and the stored metrics in `results_dir`; a matrix index has both in `results_dir`
    d = rec.get("raw_dir") or rec["results_dir"]
    d = d if os.path.isabs(d) else os.path.join(ROOT, d)
    md = rec["results_dir"] if os.path.isabs(rec["results_dir"]) else os.path.join(ROOT, rec["results_dir"])
    cmd = json.load(open(os.path.join(d, "commands.json")))
    met = json.load(open(os.path.join(md, "run_metrics.json")))
    down = json.load(open(os.path.join(d, "raw", "bag_commands.json")))
    up = json.load(open(os.path.join(d, "raw", "bag_commands_in.json")))
    bag_ev = [e["event"] for e in json.load(open(os.path.join(d, "raw", "bag_events.json")))]
    ef = os.path.join(d, "delay_events.jsonl")
    file_ev = [json.loads(l) for l in open(ef) if l.strip()] if os.path.exists(ef) else []
    mode, tau_ns, moving = cmd["mode"], int(cmd["tau_ns"]), bool(cmd["commands"])
    n = bad = 0

    def chk(cond, what):
        nonlocal n, bad
        n += 1
        if not cond:
            bad += 1
            say("MISMATCH %s: %s" % (rec["run_id"], what))

    # ---- command chain
    chk(len(down) == (1 if moving else 0), "downstream message count %d" % len(down))
    chk(len(up) == (1 if (moving and mode == "queue") else 0), "upstream message count %d" % len(up))
    if mode == "bypass":
        chk(not bag_ev and not file_ev, "bypass run has proxy events")
    else:
        types = [e["type"] for e in bag_ev]
        chk(not (set(types) & {"reject", "drop", "reset", "clock_backward", "fatal"}), "forbidden event types %s" % types)
        chk(types.count("ready") == 1 and types.count("enqueue") == (1 if moving else 0) and types.count("publish") == (1 if moving else 0), "event counts %s" % types)
        chk(sorted(json.dumps(e, sort_keys=True) for e in bag_ev) == sorted(json.dumps(e, sort_keys=True) for e in file_ev), "bag events != events file")
    if moving:
        sent = cmd["commands"][0]["message"]
        for tag, lst in (("downstream", down), ("upstream", up)):
            if lst:
                m = lst[0]["message"]
                chk(m["header"] == sent["header"] and m["joint_names"] == sent["joint_names"] and m["points"] == sent["points"], "%s message != sent message" % tag)
        c0 = cmd["commands"][0]
        send_b, send_a = c0["sim_time_before_publish_ns"], c0["sim_time_after_publish_ns"]
        if mode == "queue":
            enq = [e for e in bag_ev if e["type"] == "enqueue"][0]
            pub = [e for e in bag_ev if e["type"] == "publish"][0]
            chk(enq["t_due_ns"] == enq["t_in_ns"] + tau_ns and pub["t_due_ns"] == enq["t_due_ns"], "t_due != t_in + tau")
            eps = pub["t_pub_before_ns"] - pub["t_in_ns"] - tau_ns
            chk(0 <= eps <= EPS_MAX_NS and pub["eps_ns"] == eps, "eps %d" % eps)
            chk(pub["d_queue_ns"] == pub["t_pub_before_ns"] - pub["t_in_ns"], "d_queue")
            chk(enq["payload_hash"] == pub["payload_hash"] == c0["payload_sha256"] and enq["epoch"] == 0 == pub["epoch"] and enq["seq"] == 0 == pub["seq"], "identity/hash")
            chk(abs(met["delay"]["queue"]["d_queue_ns"] - (pub["t_pub_before_ns"] - pub["t_in_ns"])) == 0, "stored d_queue")
            t_deliver = pub["t_pub_before_ns"] / 1e9
        else:
            t_deliver = send_b / 1e9
    # ---- raw controller state
    ix, rows = read_state(os.path.join(d, "raw", "controller_state.csv"))
    seen, uniq = set(), []
    for r in rows:
        if r[0] not in seen:      # keep the first of equal stamps (same rule as the analysis)
            seen.add(r[0]); uniq.append(r)
    rows = uniq
    des = lambda r: [r[ix["des_" + j]] for j in JN]
    act = lambda r: [r[ix["act_" + j]] for j in JN]
    if not moving:
        say("%s: hold run, chain checked (%d checks, %d mismatches)" % (rec["run_id"], n, bad))
        return n, bad
    pre_end = cmd["rec_t0"] + 5.0
    hold_ref = [median([r[ix["des_" + j]] for r in rows if pre_end - 1.0 <= r[0] <= pre_end]) for j in JN]
    moving_idx = [i for i, x in enumerate(c0["dq"]) if abs(x) > 0]
    hits = []
    for i in moving_idx:
        t_hit = next((r[0] for r in rows if r[0] >= cmd["rec_t0"] and abs(r[ix["des_" + JN[i]]] - hold_ref[i]) > 1e-6), None)
        if t_hit is not None:
            hits.append(t_hit)
    t_ref = min(hits)
    chk(close(t_ref, met["delay"]["t_ref_s"], 1e-9, 0), "t_ref %r vs %r" % (t_ref, met["delay"]["t_ref_s"]))
    chk(t_ref >= t_deliver - 1e-9, "t_ref before delivery")
    t0 = 0.5 * (send_b + send_a) / 1e9
    chk(close(t0, met["delay"]["t0_mid_s"], 1e-12, 0), "t0")
    T = c0["duration_s"]
    q_start = c0["message"]["points"][0]["positions"]
    q_target = c0["message"]["points"][1]["positions"]
    dq = [b - a for a, b in zip(q_start, q_target)]
    tau = tau_ns / 1e9
    wins = {"motion_nom": (t0, t0 + T), "exec_nom": (t0, t0 + tau + T), "motion": (t_ref, t_ref + T), "settle": (t_ref + T, t_ref + T + 5.0)}
    sel = [r for r in rows if cmd["rec_t0"] <= r[0] <= cmd["rec_t1"]]
    nominal = lambda t: [q_start[i] + dq[i] * cubic((t - t0) / T) for i in range(6)]
    ident = 0.0
    ee_cache = {}
    chain = load_chain(open(os.path.join(d, "robot_description.urdf")).read(), "ur5_base_link", "ur5_wrist_3_link")
    for wn, (w0, w1) in wins.items():
        ws = [r for r in sel if w0 <= r[0] <= w1]
        stored = met["metrics"][wn]
        chk(close(stored["window"][0], w0, 1e-9, 0) and close(stored["window"][1], w1, 1e-9, 0), "%s window" % wn)
        chk(stored["n"] == len(ws), "%s n %d vs %d" % (wn, stored["n"], len(ws)))
        series = {"e_servo": [], "e_schedule": [], "e_total": []}
        pos = {"servo": [], "schedule": [], "total": []}
        for r in ws:
            a, p, qn = act(r), des(r), nominal(r[0])
            es = [x - y for x, y in zip(a, p)]
            esc = [x - y for x, y in zip(p, qn)]
            et = [x - y for x, y in zip(a, qn)]
            ident = max(ident, max(abs(et[i] - (es[i] + esc[i])) for i in range(6)))
            series["e_servo"].append(es); series["e_schedule"].append(esc); series["e_total"].append(et)
            key = r[0]
            if key not in ee_cache:
                ee_cache[key] = (fk_pos(chain, a), fk_pos(chain, p), fk_pos(chain, qn))
            Pa, Pd, Pn = ee_cache[key]
            dist = lambda u, v: math.sqrt(sum((x - y) ** 2 for x, y in zip(u, v)))
            pos["servo"].append(dist(Pa, Pd)); pos["schedule"].append(dist(Pd, Pn)); pos["total"].append(dist(Pa, Pn))
        for name, e in series.items():
            for j in range(6):
                col = [row[j] for row in e]
                mine = {"rmse": math.sqrt(sum(x * x for x in col) / len(col)), "max_abs": max(abs(x) for x in col), "mean": sum(col) / len(col)}
                for k, v in mine.items():
                    chk(close(v, stored[name][k][j]), "%s %s %s %s: %r vs %r" % (wn, name, JN[j], k, v, stored[name][k][j]))
        for k in ("servo", "schedule", "total"):
            mine = math.sqrt(sum(x * x for x in pos[k]) / len(pos[k]))
            chk(close(mine, stored["ee_pos_%s_m" % k]["rmse"], 1e-9), "%s EE pos %s rmse %r vs %r" % (wn, k, mine, stored["ee_pos_%s_m" % k]["rmse"]))
            chk(close(max(pos[k]), stored["ee_pos_%s_m" % k]["max"], 1e-9), "%s EE pos %s max" % (wn, k))
    chk(ident < 1e-12, "identity e_total = e_servo + e_schedule violated by %g" % ident)
    # fitted start: residual of desired against the cubic hold_ref -> q_target at the stored start
    ts = met["delay"]["t_start_fit_s"]
    res = max(abs(des(r)[i] - (hold_ref[i] + (q_target[i] - hold_ref[i]) * cubic((r[0] - ts) / T))) for r in rows if t_ref - 0.05 <= r[0] <= t_ref + T + 0.05 for i in range(6))
    chk(res < 1e-7, "fitted start residual %g" % res)
    say("%s: %d checks, %d mismatches (e_total identity %.1e, fit residual %.1e)" % (rec["run_id"], n, bad, ident, res))
    return n, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--runs", type=int, default=None, help="verify a random sample of N valid runs (default: all)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--only-run", default=None)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    idx = json.load(open(a.index))
    runs = [r for r in idx["runs"] if r["valid"]]
    if a.only_run:
        runs = [r for r in runs if r["run_id"] == a.only_run]
    elif a.runs:
        random.Random(a.seed).shuffle(runs)
        runs = runs[:a.runs]
    lines = []

    def say(s):
        print(s, flush=True)
        lines.append(s)

    tn = tb = 0
    for r in runs:
        n, b = verify_run(r, say)
        tn += n; tb += b
    say("verify_task2_metrics: %d runs, %d comparisons, %d mismatches" % (len(runs), tn, tb))
    if a.report:
        json.dump({"index": a.index, "runs": [r["run_id"] for r in runs], "comparisons": tn, "mismatches": tb, "log": lines}, open(a.report, "w"), indent=1)
    sys.exit(0 if tb == 0 and runs else 1)


if __name__ == "__main__":
    main()
