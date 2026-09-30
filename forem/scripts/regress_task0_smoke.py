#!/usr/bin/env python3
"""Regression tests for run_task0_smoke.sh / task0_proc.py (host side; needs forem-dev up).

Exercises the failure paths that task0.6 found unprotected. Only processes started by the tests
themselves are ever stopped, and faults are injected only in ways that cannot touch foreign
processes. Writes results/task0/<tag>-report/report.json and exits 0 iff all cases pass.

  python3 forem/scripts/regress_task0_smoke.py --tag task0.7-reg1
"""
import argparse
import hashlib
import json
import os
import shlex
import signal
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SMOKE = "bash %s/scripts/run_task0_smoke.sh" % ROOT
CHECK = "--duration 4 --settle 1"


def sg(cmd, **kw):
    return subprocess.run(["sg", "docker", "-c", cmd], capture_output=True, text=True, **kw)


def popen(cmd):
    # own process group so we can signal the wrapper like a user pressing Ctrl-C / a supervisor sending TERM
    return subprocess.Popen(["sg", "docker", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            start_new_session=True)


def residue():
    r = sg("bash %s/docker/run.sh exec python3 scripts/task0_proc.py foreign" % ROOT)
    return json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else None


def tree_hash(path):
    h = hashlib.sha256()
    for d, _, files in sorted(os.walk(path)):
        for f in sorted(files):
            p = os.path.join(d, f)
            h.update(p.encode()); h.update(open(p, "rb").read())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    tag = a.tag
    cases = []

    def record(name, ok, detail):
        cases.append({"case": name, "pass": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + " :: " + str(detail), flush=True)

    # C1 invalid run ids are refused and create nothing
    before = set(os.listdir(os.path.join(ROOT, "results", "task0")))
    codes = {}
    for bad in ("", "../x", "a b", "-lead", "a/b"):
        r = sg("%s %s %s" % (SMOKE, shlex.quote(bad), CHECK))
        codes[repr(bad)] = r.returncode
    after = set(os.listdir(os.path.join(ROOT, "results", "task0")))
    record("C1 invalid run-id refused", all(c == 12 for c in codes.values()) and before == after, {"exit_codes": codes, "new_dirs": sorted(after - before)})

    # C2 duplicate run-id refused, old evidence unchanged
    rid = "%s-dup" % tag
    r1 = sg("%s %s %s" % (SMOKE, rid, CHECK))
    h1 = tree_hash(os.path.join(ROOT, "results", "task0", rid)), tree_hash(os.path.join(ROOT, "logs", "task0", rid))
    r2 = sg("%s %s %s" % (SMOKE, rid, CHECK))
    h2 = tree_hash(os.path.join(ROOT, "results", "task0", rid)), tree_hash(os.path.join(ROOT, "logs", "task0", rid))
    record("C2 duplicate run-id refused; evidence unchanged", r1.returncode == 0 and r2.returncode == 12 and h1 == h2,
           {"first_exit": r1.returncode, "second_exit": r2.returncode, "hashes_equal": h1 == h2})

    # C3 concurrent run refused without harming the first
    ra, rb = "%s-conc-a" % tag, "%s-conc-b" % tag
    pa = popen("%s %s --duration 10 --settle 1" % (SMOKE, ra))
    time.sleep(9)
    rb_res = sg("%s %s %s" % (SMOKE, rb, CHECK))
    out_a, _ = pa.communicate(timeout=120)
    record("C3 concurrent run refused; first run unharmed", rb_res.returncode == 11 and pa.returncode == 0
           and not os.path.exists(os.path.join(ROOT, "results", "task0", rb)),
           {"second_exit": rb_res.returncode, "first_exit": pa.returncode, "second_created_dirs": os.path.exists(os.path.join(ROOT, "results", "task0", rb))})

    # C4 launch failure (roslaunch cannot load config) -> non-zero, nothing left running, manifest written
    rid = "%s-launchfail" % tag
    r = sg("%s --launch-arg controller_config:=/nonexistent.yaml %s %s" % (SMOKE, rid, CHECK))
    m = json.load(open(os.path.join(ROOT, "results", "task0", rid, "manifest.json")))
    record("C4 launch failure exits non-zero, cleans up, writes manifest", r.returncode not in (0,) and m["startup_ok"] is False
           and m["final_exit"] == r.returncode and residue() == [], {"exit": r.returncode, "manifest_final_exit": m["final_exit"], "startup_ok": m["startup_ok"]})

    # C5 container unreachable -> non-zero and no false success from stale logs
    rid = "%s-nocontainer" % tag
    r = sg("FOREM_CONTAINER=no-such-container %s %s %s" % (SMOKE, rid, CHECK))
    record("C5 container unreachable exits non-zero (13)", r.returncode == 13 and not os.path.exists(os.path.join(ROOT, "results", "task0", rid, "summary.json")),
           {"exit": r.returncode})

    # C6 TERM and INT mid-run -> 143/130, own processes gone, manifest records the interrupt, lock released
    for sigval, sname, code in ((signal.SIGTERM, "TERM", 143), (signal.SIGINT, "INT", 130)):
        rid = "%s-%s" % (tag, sname.lower())
        p = popen("%s %s --duration 30 --settle 1" % (SMOKE, rid))
        # wait until the check is running
        tl = os.path.join(ROOT, "logs", "task0", rid, "timeline.txt")
        t0 = time.time()
        while time.time() - t0 < 60 and not (os.path.exists(tl) and "check start" in open(tl).read()):
            time.sleep(0.5)
        time.sleep(3)
        alive_before = residue()
        os.killpg(p.pid, sigval)
        try:
            p.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            p.kill(); p.communicate()
        m = json.load(open(os.path.join(ROOT, "results", "task0", rid, "manifest.json"))) if os.path.exists(os.path.join(ROOT, "results", "task0", rid, "manifest.json")) else {}
        rel = sg("%s %s-after %s" % (SMOKE, rid, CHECK))  # lock must be free again; also proves no leftovers block a new run
        record("C6 %s mid-run: exit %d, own processes cleaned, manifest, lock released" % (sname, code),
               # The wrapper's own exit code is authoritative (manifest final_exit and timeline). The subprocess
               # return code belongs to the `sg` parent, which dies from SIGTERM itself (-15), so it is accepted too.
               p.returncode in (code, -int(sigval)) and m.get("final_exit") == code and bool(alive_before) and residue() == []
               and m.get("interrupted") == sname and m.get("cleanup_exit") == 0 and rel.returncode == 0,
               {"sg_parent_exit": p.returncode, "manifest_final_exit": m.get("final_exit"), "processes_before_signal": len(alive_before or []), "manifest_interrupted": m.get("interrupted"),
                "cleanup_exit": m.get("cleanup_exit"), "next_run_exit": rel.returncode})

    # C7 cleanup failure is non-zero (injected report of residue after really stopping)
    rid = "%s-cleanupfail" % tag
    r = sg("%s --test-fault residue %s %s" % (SMOKE, rid, CHECK))
    m = json.load(open(os.path.join(ROOT, "results", "task0", rid, "manifest.json")))
    record("C7 cleanup failure changes exit code to 15", r.returncode == 15 and m["cleanup_exit"] == 15 and residue() == [],
           {"exit": r.returncode, "manifest_cleanup_exit": m["cleanup_exit"], "real_residue_after": residue()})

    ok = all(c["pass"] for c in cases)
    outdir = os.path.join(ROOT, "results", "task0", tag + "-report")
    os.makedirs(outdir, exist_ok=False)
    json.dump({"tag": tag, "all_pass": ok, "cases": cases, "finished": time.strftime("%F %T %z")}, open(os.path.join(outdir, "report.json"), "w"), indent=2)
    print("ALL PASS" if ok else "FAILURES", flush=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
