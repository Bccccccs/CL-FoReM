#!/usr/bin/env python3
"""task3.5 in-container integration run (use through run_task3_core.sh, ONE fresh launch):
physics -> env -> plain-SAC smoke -> checkpoint-checked eval -> clock-reset check, then an independent recomputation of the physics
metrics from the raw timeseries.csv. Every stage's attempt is recorded (no selective summary). Exit 0 iff every stage and the
independent comparison pass. Outputs: results/task3/<run>/<stage>/..., integration_summary.json."""
import argparse
import csv
import json
import math
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task3_lib import wrap, yaw_of  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def stage(name, cmd, res_root, run, timeout):
    d = os.path.join(res_root, name)
    os.makedirs(d, exist_ok=True)
    env = dict(os.environ, FOREM_RES_DIR=d, FOREM_RUN_ID=run + "-" + name)
    t0 = time.time()
    with open(os.path.join(d, "stdout.log"), "w") as f:
        try:
            rc = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            rc = 124
    return dict(stage=name, cmd=" ".join(cmd), returncode=rc, wall_s=round(time.time() - t0, 1), dir=d)


def independent_physics(csv_path):
    """Recompute straight/turn metrics from the raw truth columns without the check script's code path."""
    rows = list(csv.DictReader(open(csv_path)))
    out = {}
    for ph in ("hold", "straight", "turn", "coord"):
        r = [x for x in rows if x["phase"] == ph]
        t = [float(x["t_sim"]) for x in r]
        xs, ys = [float(x["truth_x"]) for x in r], [float(x["truth_y"]) for x in r]
        yaw = [float(x["truth_yaw"]) for x in r]
        dt = t[-1] - t[0]
        path = sum(math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) for i in range(len(xs) - 1))
        f = (math.cos(yaw[0]), math.sin(yaw[0]))
        along = (xs[-1] - xs[0]) * f[0] + (ys[-1] - ys[0]) * f[1]
        out[ph] = dict(duration=dt, path_speed=path / dt, along_speed=along / dt, yaw_rate=wrap(yaw[-1] - yaw[0]) / dt,
                       xy=math.hypot(xs[-1] - xs[0], ys[-1] - ys[0]))
    gaps = []                                   # sample gaps WITHIN each phase (the harness does not sample while it waits for the arm action result)
    for ph in dict.fromkeys(x["phase"] for x in rows):
        ts = [float(x["t_sim"]) for x in rows if x["phase"] == ph]
        gaps += [b - a for a, b in zip(ts, ts[1:]) if b >= a]
    out["sample_period"] = dict(median=sorted(gaps)[len(gaps) // 2], max=max(gaps))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--device", default="auto", help="SAC device for smoke and eval: auto prefers CUDA; cpu/cuda[:index] override")
    a = ap.parse_args()
    res = os.environ.get("FOREM_RES_DIR", os.path.join("results/task3", a.run_id))
    os.makedirs(res, exist_ok=True)
    py = sys.executable
    S = []
    S.append(stage("physics", [py, os.path.join(HERE, "check_task3_physics.py"), "--run-id", a.run_id + "-physics"], res, a.run_id, 600))
    S.append(stage("env", [py, os.path.join(HERE, "check_task3_env.py"), "--run-id", a.run_id + "-env"], res, a.run_id, 1500))
    S.append(stage("sac_smoke", [py, os.path.join(HERE, "task3_sac_entry.py"), "--mode", "smoke", "--run-id", a.run_id + "-sac", "--seed", str(a.seed), "--device", a.device], res, a.run_id, 900))
    ck = os.path.join(res, "sac_smoke", "checkpoints", "smoke_ckpt.pt")
    S.append(stage("sac_eval", [py, os.path.join(HERE, "task3_sac_entry.py"), "--mode", "eval", "--run-id", a.run_id + "-eval", "--seed", str(a.seed + 1), "--device", a.device,
                                "--checkpoint", ck, "--episodes", "2", "--max-steps-per-episode", "40"], res, a.run_id, 900))
    S.append(stage("clock", [py, os.path.join(HERE, "check_task3_clock.py")], res, a.run_id, 900))   # last: it resets the simulation clock
    out = dict(run_id=a.run_id, requested_sac_device=a.device, stages=S, verdicts={})
    for s in S:
        out["verdicts"]["stage_" + s["stage"]] = s["returncode"] == 0
    # independent recomputation of physics evidence from the raw series
    try:
        ps = json.load(open(os.path.join(res, "physics", "physics_summary.json")))
        ind = independent_physics(os.path.join(res, "physics", "timeseries.csv"))
        out["independent_physics"] = ind
        cmp_ = {}
        for ph, key_ind, key_sum in (("straight", "path_speed", "path_speed"), ("turn", "yaw_rate", "mean_rate"), ("coord", "path_speed", "path_speed"), ("coord", "yaw_rate", "mean_rate")):
            cmp_[f"{ph}.{key_sum}"] = (ind[ph][key_ind], ps["phases"][ph][key_sum])
        out["independent_vs_summary"] = cmp_
        out["verdicts"]["independent_recompute_matches"] = all(abs(x - y) <= 0.02 * max(abs(y), 0.05) for x, y in cmp_.values())
        out["verdicts"]["control_period_sane"] = ind["sample_period"]["median"] <= 0.05 and ind["sample_period"]["max"] <= 0.5
        out["verdicts"]["commanded_motion_followed"] = (abs(ind["straight"]["along_speed"] - 0.2) <= 0.04 and ind["hold"]["xy"] <= 0.01)
    except Exception as e:  # noqa: BLE001
        out["verdicts"]["independent_recompute_matches"] = False
        out["independent_error"] = repr(e)
    out["ok"] = all(out["verdicts"].values())
    json.dump(out, open(os.path.join(res, "integration_summary.json"), "w"), indent=1, default=str)
    for k, v in out["verdicts"].items():
        print(("PASS " if v else "FAIL ") + k)
    print("OK" if out["ok"] else "NOT OK")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
