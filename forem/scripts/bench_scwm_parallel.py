#!/usr/bin/env python3
"""Throughput benchmark for K parallel simulation instances (task4.8.1). Runs INSIDE forem-dev; starts REAL simulations.

  python3 scripts/bench_scwm_parallel.py --run-id t4.8.1-bench-k4 --k 4 [--layout none|numa|part] [--steps 600]

For each instance: scwm_instance start (all K at once) -> one Task3Env driver per instance (random actions, no learning;
reset(seed=7), then --steps steps, then one forced reset) -> synchronized start -> stop all. Layouts (cores of the 64-CPU
machine; NUMA node0 = 0-31, node1 = 32-63; instance i goes to node i%2):
  none  no affinity            numa  instance and its driver bound to ALL cores of their node
  part  disjoint equal core slices inside the node (K=6: 10 cores each)
Output: results/task4/<run-id>/bench.json (per-instance rates, startup, reset times, CPU shares, sampled series).
Rates exclude env.reset() time; the overlap window is [latest driver start, earliest driver end].
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

FOREM = Path(__file__).resolve().parent.parent
INST = FOREM / "scripts" / "scwm_instance.py"
REG = FOREM / "scripts" / "regress_scwm_instances.py"
sys.path.insert(0, str(FOREM / "scripts"))
import scwm_instance as S  # noqa: E402

NODES = [list(range(0, 32)), list(range(32, 64))]


def cpulist(cs):
    return ",".join(str(c) for c in cs)


def layout_cpus(layout, k):
    if layout == "none":
        return [None] * k
    out = []
    per_node_cnt = [sum(1 for i in range(k) if i % 2 == n) for n in (0, 1)]
    seen = [0, 0]
    for i in range(k):
        n = i % 2
        if layout == "numa":
            out.append(cpulist(NODES[n]))
        else:
            w = 32 // per_node_cnt[n]
            lo = NODES[n][0] + seen[n] * w
            out.append("%d-%d" % (lo, lo + w - 1))
            seen[n] += 1
    return out


def read_stat():
    with open("/proc/stat") as f:
        v = [int(x) for x in f.readline().split()[1:]]
    idle = v[3] + v[4]
    return sum(v), idle


def marker_procs():
    """pid -> (inst, role, jiffies) for every process carrying an instance marker."""
    out = {}
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            env = open("/proc/%s/environ" % p, "rb").read().split(b"\0")
            k = next((e for e in env if e.startswith(b"FOREM_INSTANCE=")), None)
            if k is None:
                continue
            cl = open("/proc/%s/cmdline" % p, "rb").read().replace(b"\0", b" ").decode(errors="replace")
            st = open("/proc/%s/stat" % p).read()
            f = st[st.rindex(")") + 2:].split()
            j = int(f[11]) + int(f[12])
            role = "gzserver" if "gzserver" in cl.split(" ")[0] else ("driver" if "env-driver" in cl else "ros_other")
            out[int(p)] = (int(k.split(b"=")[1]), role, j)
        except (OSError, ValueError, IndexError):
            continue
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--layout", choices=("none", "numa", "part"), default="none")
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--first", type=int, default=0, help="first instance number")
    ap.add_argument("--timeout", type=float, default=240.0)
    a = ap.parse_args()
    K = a.k
    ids = list(range(a.first, a.first + K))
    res = FOREM / "results" / "task4" / a.run_id
    res.mkdir(parents=True, exist_ok=False)
    cpus = layout_cpus(a.layout, K)
    out = {"run_id": a.run_id, "k": K, "layout": a.layout, "cpus": dict(zip(ids, cpus)), "steps": a.steps, "start_unix": time.time()}
    rc_stop = {}
    try:
        t0 = time.time()
        sp = []
        for k, c in zip(ids, cpus):
            cmd = [sys.executable, str(INST), "start", "--inst", str(k), "--run-id", a.run_id, "--timeout", str(a.timeout)]
            if c:
                cmd += ["--cpus", c]
            sp.append(subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True))
        so = [p.communicate()[0].strip() for p in sp]
        out["startup_rc"] = [p.returncode for p in sp]
        out["startup_wall_s"] = round(time.time() - t0, 1)
        out["startup_out"] = so
        if any(out["startup_rc"]):
            out["error"] = "startup failed"
            return
        # drivers
        flag = res / "start.flag"
        procs, ready, outs = [], [], []
        for k in ids:
            o, r = res / ("driver_%d.json" % k), res / ("ready_%d" % k)
            outs.append(o), ready.append(r)
            procs.append(subprocess.Popen([sys.executable, str(INST), "exec", "--inst", str(k), "--", sys.executable, str(REG), "--child", "env-driver",
                                           "--seed", "7", "--steps", str(a.steps), "--force-reset-mid", "--out", str(o), "--ready-file", str(r),
                                           "--start-flag", str(flag)],
                                          stdout=subprocess.DEVNULL, stderr=open(res / ("driver_%d.err" % k), "w"), text=True))
        tw = time.time()
        while not all(r.exists() for r in ready):
            if any(p.poll() is not None for p in procs) or time.time() - tw > 900:
                out["error"] = "driver died or timed out before ready"
                for p in procs:
                    if p.poll() is None:
                        p.terminate()
                return
            time.sleep(0.5)
        out["drivers_ready_wall_s"] = round(time.time() - tw, 1)
        time.sleep(2)
        # sampler
        series, stop_s = [], threading.Event()

        def sampler():
            prev_mp = marker_procs()
            while not stop_s.is_set():
                tot, idle = read_stat()
                mp = marker_procs()
                series.append({"t": time.time(), "tot": tot, "idle": idle,
                               "mp": {str(p): list(v) for p, v in mp.items()}})
                time.sleep(1.0)

        th = threading.Thread(target=sampler, daemon=True)
        th.start()
        flag.write_text("go")
        for p in procs:
            p.wait(timeout=1800)
        stop_s.set()
        th.join()
        out["driver_rc"] = [p.returncode for p in procs]
        drv = [json.loads(o.read_text()) if o.exists() else None for o in outs]
        out["drivers"] = drv
        ph = [d["phases"][0] for d in drv if d]
        if ph and len(ph) == K:
            ws, we = max(p["t_start"] for p in ph), min(p["t_end"] for p in ph)
            out["overlap_window_s"] = round(we - ws, 2)
            # CPU in the overlap window
            ss = [s for s in series if ws <= s["t"] <= we]
            if len(ss) >= 2:
                f, l = ss[0], ss[-1]
                out["machine_busy_frac"] = round(1 - (l["idle"] - f["idle"]) / (l["tot"] - f["tot"]), 4)
                hz = os.sysconf("SC_CLK_TCK")
                dt = l["t"] - f["t"]
                roles = {}
                for pid, (k, role, j) in l["mp"].items():
                    if pid in f["mp"]:
                        roles[role] = roles.get(role, 0.0) + (j - f["mp"][pid][2]) / hz / dt
                out["instance_cores_used_by_role"] = {r: round(v, 2) for r, v in roles.items()}
                out["instance_cores_used_total"] = round(sum(roles.values()), 2)
            out["sum_steps_per_s"] = round(sum(p["steps_per_s"] for p in ph), 2)
            sps = [p["steps_per_s"] for p in ph]
            out["per_inst_steps_per_s"] = {"mean": round(sum(sps) / K, 2), "min": min(sps), "max": max(sps)}
            rtf = [p["sim_per_wall"] for p in ph]
            out["per_inst_sim_per_wall"] = {"mean": round(sum(rtf) / K, 3), "min": min(rtf), "max": max(rtf)}
            out["step_ms"] = {"mean": round(sum(p["wall_per_step_ms"] for p in ph) / K, 2), "max": max(p["wall_per_step_ms"] for p in ph)}
            rt = [t for d in drv for t in d["reset_times_s"]]
            out["reset_s"] = {"mean": round(sum(rt) / len(rt), 2), "max": max(rt), "n": len(rt)}
        (res / "series.json").write_text(json.dumps(series))
    finally:
        for k in ids:
            r = subprocess.run([sys.executable, str(INST), "stop", "--inst", str(k)], capture_output=True, text=True)
            rc_stop[k] = [r.returncode, r.stdout.strip()[:200]]
        out["stop_rc"] = rc_stop
        out["residue_after"] = {k: json.loads(subprocess.run([sys.executable, str(INST), "residue", "--inst", str(k)], capture_output=True, text=True).stdout or "[]") for k in ids}
        out["end_unix"] = time.time()
        (res / "bench.json").write_text(json.dumps(out, indent=2))
        print(json.dumps({k: v for k, v in out.items() if k not in ("drivers", "startup_out", "stop_rc")}, indent=1))


if __name__ == "__main__":
    main()
