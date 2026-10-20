#!/usr/bin/env python3
"""Lifecycle regression of run_task3_core.sh (host side; needs forem-dev up and idle). Only processes started by the cases themselves
are ever stopped. Writes results/task3/<tag>-report/report.json; exit 0 iff every case passes.

  L1 invalid run-ids refused, nothing created           L5 SIGTERM mid-run (real launch + commanding client) -> 143, clean
  L2 duplicate run-id refused, evidence unchanged        L6 SIGINT mid-run -> 130, clean
  L3 foreign ROS-named process: refused (10), NOT killed  L7 client death: base stops, arm settles (task3_lifecycle_driver --mode die)
  L4 concurrent run refused (11), first run unharmed

  python3 forem/scripts/regress_task3_lifecycle.py --tag t3.5-life1
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
RUN = "bash %s/scripts/run_task3_core.sh" % ROOT
RUN_SH = "bash %s/docker/run.sh" % ROOT


def sg(cmd, **kw):
    return subprocess.run(["sg", "docker", "-c", cmd], capture_output=True, text=True, **kw)


def popen(cmd):
    return subprocess.Popen(["sg", "docker", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)


def foreign():
    r = sg("%s exec python3 scripts/task0_proc.py foreign" % RUN_SH)
    return json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else None


def grep_needle(needle):
    r = sg("%s exec python3 scripts/task0_proc.py grep --needle %s" % (RUN_SH, shlex.quote(needle)))
    return r.returncode, r.stdout.strip()[-300:]


def tree_hash(path):
    h = hashlib.sha256()
    for d, _, files in sorted(os.walk(path)):
        for f in sorted(files):
            p = os.path.join(d, f)
            h.update(p.encode())
            h.update(open(p, "rb").read())
    return h.hexdigest()


def state(run):
    p = os.path.join(ROOT, "logs", "task3", run, "state.json")
    return json.load(open(p)) if os.path.exists(p) else None


def wait_for(path, text, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if text in open(path, errors="ignore").read():
                return True
        except FileNotFoundError:
            pass
        time.sleep(0.5)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    tag = a.tag
    cases = []

    def record(name, ok, detail):
        cases.append({"case": name, "pass": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + " :: " + str(detail), flush=True)

    pre = foreign()
    if pre != []:
        print("ABORT: container is not idle:", pre)
        return 3

    # L1
    before = set(os.listdir(os.path.join(ROOT, "results", "task3")))
    codes = {}
    for bad in ("", "../x", "a b", "-lead", "a/b"):
        r = sg("%s --no-launch %s -- python3 -c pass" % (RUN, shlex.quote(bad)))
        codes[repr(bad)] = r.returncode
    r = sg("%s --no-launch %s" % (RUN, tag + "-nocheck"))          # missing '-- CHECK_CMD'
    codes["no check cmd"] = r.returncode
    after = set(os.listdir(os.path.join(ROOT, "results", "task3")))
    record("L1 invalid run-id / usage refused", all(c == 12 for c in codes.values()) and before == after, {"exit_codes": codes, "new_dirs": sorted(after - before)})

    # L2
    rid = tag + "-dup"
    r1 = sg("%s --no-launch %s -- python3 -c 'print(1)'" % (RUN, rid))
    h1 = tree_hash(os.path.join(ROOT, "results", "task3", rid)), tree_hash(os.path.join(ROOT, "logs", "task3", rid))
    r2 = sg("%s --no-launch %s -- python3 -c 'print(1)'" % (RUN, rid))
    h2 = tree_hash(os.path.join(ROOT, "results", "task3", rid)), tree_hash(os.path.join(ROOT, "logs", "task3", rid))
    record("L2 duplicate run-id refused; evidence unchanged", r1.returncode == 0 and r2.returncode == 12 and h1 == h2,
           {"first_exit": r1.returncode, "second_exit": r2.returncode, "hashes_equal": h1 == h2})

    # L3 foreign process not stopped
    fake = sg("%s bg bash -c 'exec -a roslaunch sleep 600'" % RUN_SH)
    time.sleep(1.0)
    f_before = foreign()
    rid = tag + "-foreign"
    r = sg("%s %s -- python3 -c 'print(1)'" % (RUN, rid))
    f_after = foreign()
    st = state(rid)
    alive = bool(f_after) and any("600" in json.dumps(x) for x in f_after)      # the fake's cmdline is 'roslaunch 600'
    record("L3 foreign process refused (exit 10) and NOT stopped", r.returncode == 10 and bool(f_before) and alive and st and st["launch_start_rc"] == "skipped",
           {"exit": r.returncode, "foreign_before": f_before, "foreign_after": f_after, "state_launch_rc": st and st["launch_start_rc"]})
    # remove only the fake we started (by exact command line match)
    sg("%s exec bash -c \"pkill -f '^roslaunch 600' || true\"" % RUN_SH)
    time.sleep(1.0)
    f_clean = foreign()

    # L4 concurrent refused, first run unharmed
    ra, rb = tag + "-conc-a", tag + "-conc-b"
    pa = popen("%s --no-launch %s -- python3 -c 'import time; time.sleep(8)'" % (RUN, ra))
    time.sleep(3.0)
    rb_run = sg("%s --no-launch %s -- python3 -c pass" % (RUN, rb))
    out_a, _ = pa.communicate(timeout=120)
    record("L4 concurrent run refused (exit 11); first run completes", rb_run.returncode == 11 and pa.returncode == 0 and not os.path.exists(os.path.join(ROOT, "logs", "task3", rb)),
           {"second_exit": rb_run.returncode, "first_exit": pa.returncode})

    # L5 / L6 interrupt a real run mid-check
    for sig, name, want in ((signal.SIGTERM, "L5 SIGTERM", 143), (signal.SIGINT, "L6 SIGINT", 130)):
        rid = "%s-%s" % (tag, name.split()[1].lower())
        p = popen("%s %s -- python3 scripts/task3_lifecycle_driver.py --mode hold" % (RUN, rid))
        tl = os.path.join(ROOT, "logs", "task3", rid, "timeline.txt")
        started = wait_for(tl, "check start", 120)
        time.sleep(8.0)
        os.killpg(os.getpgid(p.pid), sig)
        try:
            p.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            p.kill()
        st = state(rid)
        rc_needle, out_needle = grep_needle("--mode hold")
        f_after = foreign()
        mani = os.path.exists(os.path.join(ROOT, "results", "task3", rid, "manifest.json"))
        # the signal is sent to the whole process group (like a Ctrl-C / supervisor TERM), so the `sg` parent may die by the signal itself
        # (returncode -15) while the wrapper's own recorded exit status (state.json final_exit) is the authoritative 143/130
        ok = started and p.returncode in (want, -int(sig)) and st and st.get("final_exit") == want and st.get("interrupted") in ("TERM", "INT") and st.get("cleanup_exit") == 0 \
            and rc_needle == 0 and f_after == [] and mani
        record("%s mid-run: exit %d, own processes cleaned, manifest written" % (name, want), ok,
               {"exit": p.returncode, "final_exit_recorded": st and st.get("final_exit"), "interrupted": st and st.get("interrupted"), "check_exit": st and st.get("check_exit"),
                "cleanup_exit": st and st.get("cleanup_exit"), "client_processes_left": out_needle, "foreign_after": f_after, "manifest": mani})

    # L7 client death
    rid = tag + "-die"
    r = sg("%s %s -- python3 scripts/task3_lifecycle_driver.py --mode die --run-s 5 --observe-s 4" % (RUN, rid), timeout=600)
    d = None
    try:
        d = json.load(open(os.path.join(ROOT, "results", "task3", rid, "lifecycle_die.json")))
    except Exception:  # noqa: BLE001
        pass
    record("L7 client killed: base stops (cmd_vel timeout) and arm settles", r.returncode == 0 and d and d.get("ok"),
           {"exit": r.returncode, "result": d and {k: v for k, v in d.items() if k != "verdicts"}})

    final = foreign()
    record("final: container idle again (no residue from any case)", final == [] and f_clean == [], {"foreign_final": final, "after_L3_cleanup": f_clean})
    rep = os.path.join(ROOT, "results", "task3", tag + "-report")
    os.makedirs(rep, exist_ok=True)
    json.dump(dict(tag=tag, cases=cases, ok=all(c["pass"] for c in cases)), open(os.path.join(rep, "report.json"), "w"), indent=1, default=str)
    return 0 if all(c["pass"] for c in cases) else 1


if __name__ == "__main__":
    sys.exit(main())
