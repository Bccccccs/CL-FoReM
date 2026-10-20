#!/usr/bin/env python3
"""task6.1 section 5 profile harness (runs on the HOST, starts supervised sim runs inside forem-dev).

  python3 scripts/bench_task6_perf.py --case NAME --k K --gpu G --protocol PATH [--threads N] [--cpus LIST]
         [--steps 4000] [--first-inst 30] [--train-arg ARG]... [--tag R]

Starts K supervised runs (scwm_supervise.py --world sim, run-id t6.1-perf-r1-<case>-<i>) on one GPU, waits until all reach
--steps, and writes results/task6/t6.1-perf-r1/<case>.json: per-run steps/s from the 1000-step progress windows after
the first (warm-up/cudnn) window, phase means, and CPU seconds per run (utime+stime of the run's trainer and its whole ROS
process tree, read from /proc) divided by the wall time between the first and last measured window.
Measurement only: no scientific setting is changed by this script.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

FOREM = Path(__file__).resolve().parent.parent
OUT = FOREM / "results" / "task6" / "t6.1-perf-r1"
RUN = FOREM / "docker" / "run.sh"
CLK = os.sysconf("SC_CLK_TCK")


def dock(cmd):
    return subprocess.run(["sg", "docker", "-c", cmd], capture_output=True, text=True)


def procs():
    out = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            raw = open("/proc/%s/stat" % d).read()
            cmd = open("/proc/%s/cmdline" % d, "rb").read().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        rest = raw[raw.rindex(")") + 2:].split()
        out[int(d)] = dict(ppid=int(rest[1]), cpu=(int(rest[11]) + int(rest[12])) / CLK, threads=int(rest[17]), cmd=cmd)
    return out


def run_cpu(runid, snap):
    """CPU seconds of every process belonging to run `runid` (trainer + instance tree)."""
    roots = [p for p, v in snap.items() if ("--run-id %s " % runid in v["cmd"] + " " or "/%s-sim" % runid in v["cmd"]) and "bench_task6_perf" not in v["cmd"]]
    keep = set(roots)
    changed = True
    while changed:
        changed = False
        for p, v in snap.items():
            if p not in keep and v["ppid"] in keep:
                keep.add(p)
                changed = True
    return sum(snap[p]["cpu"] for p in keep), len(keep), sum(snap[p]["threads"] for p in keep)


def window_records(runid):
    f = FOREM / "logs" / "task6" / runid / "progress.jsonl"
    if not f.exists():
        return []
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--gpu", type=int, required=True)
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--cpus", default=None, help="taskset list passed to scwm_supervise --cpus (instance processes; trainer inherits via exec)")
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--first-inst", type=int, default=30)
    ap.add_argument("--train-arg", action="append", default=[])
    ap.add_argument("--timeout", type=float, default=1800)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    runs = ["t6.1-perf-r1-%s-%d" % (a.case, i) for i in range(a.k)]
    env = ["env"] + (["OMP_NUM_THREADS=%d" % a.threads, "MKL_NUM_THREADS=%d" % a.threads, "OPENBLAS_NUM_THREADS=%d" % a.threads] if a.threads else [])
    t_launch = time.time()
    for i, rid in enumerate(runs):
        cmd = env + ["python3", "-u", "scripts/scwm_supervise.py", "--world", "sim", "--inst", str(a.first_inst + i), "--run-id", rid, "--seed", str(i),
                     "--device", "cuda:%d" % a.gpu, "--steps", str(a.steps)]
        if a.cpus:
            cmd += ["--cpus", a.cpus]
        cmd += ["--", "--config", a.protocol, "--ckpt-every", "100000", "--val-every", "100000000", "--no-val-final"] + a.train_arg
        r = dock("%s bg %s" % (RUN, " ".join(cmd)))
        if r.returncode:
            print("launch failed", r.stderr)
            return 2
    # sample CPU at each progress record
    samples = {rid: [] for rid in runs}
    seen = {rid: 0 for rid in runs}
    while time.time() - t_launch < a.timeout:
        snap = None
        for rid in runs:
            recs = window_records(rid)
            if len(recs) > seen[rid]:
                snap = snap or procs()
                for rec in recs[seen[rid]:]:
                    samples[rid].append((rec["step"], time.time(), run_cpu(rid, snap)[0], rec))
                seen[rid] = len(recs)
        if all(seen[rid] and samples[rid][-1][0] >= a.steps for rid in runs):
            break
        time.sleep(2)
    snap = procs()
    res = dict(case=a.case, k=a.k, gpu=a.gpu, threads=a.threads or "default", cpus=a.cpus, protocol=a.protocol, train_args=a.train_arg, steps=a.steps, runs={})
    for rid in runs:
        s = samples[rid]
        if len(s) < 3:
            res["runs"][rid] = dict(error="fewer than 3 progress windows", n=len(s))
            continue
        meas = s[1:]                       # drop the first window (warm-up)
        wall = meas[-1][1] - s[0][1]
        cpu = meas[-1][2] - s[0][2]
        recs = [m[3] for m in meas]
        ph = {}
        for r in recs:
            for k2, v in r["phase_ms_mean"].items():
                ph.setdefault(k2, []).append(v)
        res["runs"][rid] = dict(steps_per_s=[round(r["steps_per_s_window"], 2) for r in recs], mean_steps_per_s=sum(r["steps_per_s_window"] for r in recs) / len(recs),
                                phase_ms_mean={k2: sum(v) / len(v) for k2, v in ph.items()}, cpu_cores_mean=cpu / wall if wall > 0 else None, wall_s=wall,
                                window_internal_success=[r["window_internal_success"] for r in recs])
    ok = [v for v in res["runs"].values() if "mean_steps_per_s" in v]
    res["total_steps_per_s"] = sum(v["mean_steps_per_s"] for v in ok)
    res["total_cpu_cores"] = sum(v["cpu_cores_mean"] for v in ok)
    res["elapsed_s"] = time.time() - t_launch
    json.dump(res, open(OUT / ("%s.json" % a.case), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "runs"}, indent=1))
    for rid, v in res["runs"].items():
        print(rid, v.get("mean_steps_per_s"), v.get("cpu_cores_mean"), v.get("phase_ms_mean"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
