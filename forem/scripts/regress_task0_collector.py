#!/usr/bin/env python3
"""Regression for the feedback COLLECTOR lifecycle in run_task0_smoke.sh (task0.12; task0.11 finding).

task0.11 found that after TERM/INT the run's check_feedback.py process was still alive in the container
although the regression reported PASS and the name-based foreign list was empty. These cases identify the
collector by its FULL command line (`--run-id <this run>`), via `docker top`, not by ROS/Gazebo names:

  K1 normal run           -> exit 0, manifest check_exit 0, no collector left
  K2 failing check        -> collector exits 3 (refused window): wrapper exits 1, manifest check_exit 3 (not masked), no collector left
  K3 TERM mid-collection  -> collector existed before the signal, is gone after; wrapper 143; check_exit is not 0
  K4 INT  mid-collection  -> same with INT / 130

Usage: python3 forem/scripts/regress_task0_collector.py --tag task0.12-col1     (needs forem-dev up)
Writes results/task0/<tag>-report/report.json; exit 0 iff all pass. Only its own processes are ever signalled.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SMOKE = "bash %s/scripts/run_task0_smoke.sh" % ROOT
CONTAINER = os.environ.get("FOREM_CONTAINER", "forem-dev")


def sg(cmd):
    return subprocess.run(["sg", "docker", "-c", cmd], capture_output=True, text=True)


def popen(cmd):
    return subprocess.Popen(["sg", "docker", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)


def procs_with(needle):
    """Full command lines in the container containing `needle` (excludes this query itself)."""
    r = sg("docker top %s -eo pid,args" % CONTAINER)
    return [l.strip() for l in r.stdout.splitlines() if needle in l and "docker top" not in l]


def manifest(rid):
    return json.load(open(os.path.join(ROOT, "results", "task0", rid, "manifest.json")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    cases = []

    def record(name, ok, detail):
        cases.append({"case": name, "pass": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + " :: " + str(detail), flush=True)

    # K1 normal
    rid = "%s-normal" % a.tag
    r = sg("%s %s --duration 4 --settle 1" % (SMOKE, rid))
    m = manifest(rid)
    record("K1 normal collection: exit 0, check_exit 0, collector gone", r.returncode == 0 and m["check_exit"] == 0 and not procs_with("--run-id " + rid),
           {"exit": r.returncode, "check_exit": m["check_exit"], "collector_left": procs_with("--run-id " + rid)})

    # K2 failing check (window too short for the move -> collector refuses with 3)
    rid = "%s-refused" % a.tag
    r = sg("%s %s --duration 3 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3" % (SMOKE, rid))
    m = manifest(rid)
    record("K2 failing collector is not masked (wrapper 1, check_exit 3)", r.returncode == 1 and m["check_exit"] == 3 and m["final_exit"] == 1
           and not procs_with("--run-id " + rid), {"exit": r.returncode, "check_exit": m["check_exit"], "final_exit": m["final_exit"]})

    # K3/K4 interrupts while the collector is running
    for sigval, sname, code in ((signal.SIGTERM, "TERM", 143), (signal.SIGINT, "INT", 130)):
        rid = "%s-%s" % (a.tag, sname.lower())
        p = popen("%s %s --duration 40 --settle 1" % (SMOKE, rid))
        tl = os.path.join(ROOT, "logs", "task0", rid, "timeline.txt")
        t0 = time.time()
        while time.time() - t0 < 90 and not (os.path.exists(tl) and "check start" in open(tl).read()):
            time.sleep(0.5)
        time.sleep(3)
        before = procs_with("--run-id " + rid)
        os.killpg(p.pid, sigval)
        try:
            p.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            p.kill(); p.communicate()
        after = procs_with("--run-id " + rid)
        m = manifest(rid) if os.path.exists(os.path.join(ROOT, "results", "task0", rid, "manifest.json")) else {}
        record("K%s %s mid-collection: collector existed before, gone after; wrapper %d; check_exit not success" % (3 if sname == "TERM" else 4, sname, code),
               bool(before) and not after and m.get("final_exit") == code and m.get("interrupted") == sname and m.get("check_exit") not in (0, None) and m.get("cleanup_exit") == 0,
               {"collector_before_signal": len(before), "collector_after": after, "manifest_final_exit": m.get("final_exit"),
                "check_exit": m.get("check_exit"), "cleanup_exit": m.get("cleanup_exit")})

    ok = all(c["pass"] for c in cases)
    outdir = os.path.join(ROOT, "results", "task0", a.tag + "-report")
    os.makedirs(outdir, exist_ok=False)
    json.dump({"tag": a.tag, "all_pass": ok, "cases": cases, "finished": time.strftime("%F %T %z")}, open(os.path.join(outdir, "report.json"), "w"), indent=2)
    print("ALL PASS" if ok else "FAILURES", flush=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
