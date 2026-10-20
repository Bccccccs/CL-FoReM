#!/usr/bin/env python3
"""FoReM Task4: supervise ONE long training worker (simulation instance K + scwm_train.py) for days.

Loop: make sure instance K is up (fresh run-id suffix each time) -> run scwm_train.py (--resume when a manifest exists) -> on a crash, on a
stalled heartbeat (no progress/event line for --stall-s) or on a dead simulation: stop the training process group, stop the instance,
start a new instance and resume from the last checkpoint. Stops when train_summary.json reports steps >= the target, after --max-restarts
failures, or on SIGTERM (graceful: asks the trainer to checkpoint and exit). Never touches other instances or other users' processes
(instance stop is identity based, scripts/scwm_instance.py). Stdlib only; run inside forem-dev:
  python3 -u scripts/scwm_supervise.py --inst 0 --run-id RID --seed 0 --device cuda:0 --steps 1000000 [-- extra scwm_train.py args]
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

FOREM = Path(__file__).resolve().parent.parent
INST = FOREM / "scripts" / "scwm_instance.py"


def log(fh, msg):
    line = "%s %s" % (time.strftime("%F %T %z"), msg)
    print(line, flush=True)
    fh.write(line + "\n")
    fh.flush()


def inst(*args, timeout=600):
    return subprocess.run([sys.executable, str(INST)] + [str(a) for a in args], capture_output=True, text=True, timeout=timeout)


def newest_activity(logdir):
    t = 0.0
    for n in ("progress.jsonl", "events.jsonl", "episodes.jsonl"):
        p = logdir / n
        if p.exists():
            t = max(t, p.stat().st_mtime)
    return t


def done(resdir, target):
    p = resdir / "train_summary.json"
    if not p.exists():
        return False
    try:
        s = json.loads(p.read_text())
    except ValueError:
        return False
    return s.get("steps", 0) >= target and s.get("stop") is None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", choices=("sim", "gazebo"), default="gazebo")
    ap.add_argument("--inst", type=int, required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--device", required=True)
    ap.add_argument("--steps", type=int, required=True)
    ap.add_argument("--stall-s", type=float, default=3600.0)
    ap.add_argument("--max-restarts", type=int, default=40)
    ap.add_argument("--cpus", default=None)
    ap.add_argument("--train-script", default="scwm_train.py")
    ap.add_argument("train_args", nargs="*")
    a = ap.parse_args()
    task_dir = "task6" if a.world == "sim" else "task4"
    logdir, resdir = FOREM / "logs" / task_dir / a.run_id, FOREM / "results" / task_dir / a.run_id
    logdir.mkdir(parents=True, exist_ok=True)
    sup = open(logdir / "supervisor.log", "a")
    stop = {"flag": None}
    child = {"p": None}

    def on_term(sig, frm):
        stop["flag"] = signal.Signals(sig).name
        if child["p"] and child["p"].poll() is None:
            os.killpg(child["p"].pid, signal.SIGTERM)       # trainer checkpoints and exits cleanly
    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)

    restarts, sim_n = 0, 0
    log(sup, "supervisor start run=%s inst=%d seed=%d device=%s target=%d" % (a.run_id, a.inst, a.seed, a.device, a.steps))
    while not stop["flag"] and not done(resdir, a.steps):
        if restarts > a.max_restarts:
            log(sup, "ABORT: more than %d restarts" % a.max_restarts)
            break
        # --- simulation instance -------------------------------------------------------------------------------
        st = inst("status", "--inst", a.inst)
        if st.returncode != 0:
            inst("stop", "--inst", a.inst)
            sim_n += 1
            sid = "%s-sim%d-%d" % (a.run_id, sim_n, int(time.time()))
            r = inst("start", "--inst", a.inst, "--run-id", sid, *(["--world", "sim"] if a.world == "sim" else []), *(["--cpus", a.cpus] if a.cpus else []))
            log(sup, "instance start rc=%d %s" % (r.returncode, r.stdout.strip()[-200:]))
            if r.returncode != 0:
                restarts += 1
                time.sleep(30)
                continue
        # --- trainer -------------------------------------------------------------------------------------------
        cmd = [sys.executable, str(INST), "exec", "--inst", str(a.inst), "--", sys.executable, "-u", "-W", "ignore", str(FOREM / "scripts" / a.train_script),
               "--run-id", a.run_id, "--seed", str(a.seed), "--device", a.device, "--steps", str(a.steps)]
        if (resdir / "run_manifest.json").exists():
            cmd.append("--resume")
        if a.world == "sim":
            cmd += ["--world", "sim"]
        cmd += a.train_args
        out = open(logdir / "train.out", "a")
        p = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, start_new_session=True, cwd=str(FOREM), **({"env": dict(os.environ, FOREM_LOG_DIR=str(logdir), FOREM_RES_DIR=str(resdir))} if a.world == "sim" else {}))
        child["p"] = p
        log(sup, "trainer pid=%d resume=%s" % (p.pid, "--resume" in cmd))
        t_start = time.time()
        reason = None
        while True:
            try:
                rc = p.wait(timeout=30)
                reason = "exit rc=%s" % rc
                break
            except subprocess.TimeoutExpired:
                pass
            if time.time() - max(newest_activity(logdir), t_start) > a.stall_s:
                reason = "stall > %.0f s" % a.stall_s
                os.killpg(p.pid, signal.SIGTERM)
                time.sleep(60)
                if p.poll() is None:
                    os.killpg(p.pid, signal.SIGKILL)
                p.wait()
                break
            if inst("status", "--inst", a.inst).returncode != 0:
                reason = "simulation instance died"
                os.killpg(p.pid, signal.SIGTERM)
                time.sleep(30)
                if p.poll() is None:
                    os.killpg(p.pid, signal.SIGKILL)
                p.wait()
                break
        out.close()
        log(sup, "trainer ended: %s" % reason)
        if done(resdir, a.steps) or stop["flag"]:
            break
        restarts += 1
        inst("stop", "--inst", a.inst)          # fresh simulation for the resumed run
        time.sleep(10)
    r = inst("stop", "--inst", a.inst)
    log(sup, "supervisor end: done=%s stop=%s restarts=%d stop_inst_rc=%d" % (done(resdir, a.steps), stop["flag"], restarts, r.returncode))
    return 0 if done(resdir, a.steps) else 1


if __name__ == "__main__":
    sys.exit(main())
