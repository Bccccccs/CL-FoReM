#!/usr/bin/env python3
"""Failure-path regression for scripts/run_task2_delay.sh (task2.2/2.3). Needs forem-dev up; only its own processes are signalled.

  E1  invalid run ids are refused (12) and create nothing
  E2  unknown case / mode / argument, missing or unknown freeze, --experiment with a protocol-only freeze or an unknown experiment: refused (12), nothing created
  E2b bad delays (nan, inf, negative, 100 ms, text) and bypass with a non-zero delay: refused (12), nothing created
  E3  reused run-id refused (12) and the existing evidence is byte-identical afterwards
  E4  concurrent entry refused (11) without touching the first run
  E5  foreign ROS-like process in the container -> exit 10, nothing started, the foreign process still alive
  E6  collector safety abort in queue mode -> exit 1, evidence kept, nothing left by full command line
  E7  cleanup residue injected (--test-fault residue) -> exit 15 wins
  E8  TERM mid-collection (queue mode, case H) -> 143, collector/proxy/bag/throttle/launch gone, manifest records interrupt, collect_exit != 0
  E9  INT  mid-collection -> 130, same
  E10 normal short run (M3, bypass) -> 0, every stage exit 0, nothing left, no proxy process ever existed
  E11 normal short run (M3, queue 80 ms) -> 0, every stage exit 0 incl. the proxy, nothing left
  E12 proxy killed (SIGKILL) during the pre-hold of a queue run -> the run is INVALID (exit 1, command chain gates fail), cleanup 0, nothing left
Usage: python3 forem/scripts/regress_task2_entry.py --tag task2.2-reg1 --freeze-id t2.1-protocol1
Writes results/task2/<tag>-report/report.json. Exit 0 iff all pass.
"""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ENTRY = "bash %s/scripts/run_task2_delay.sh" % ROOT
CONTAINER = os.environ.get("FOREM_CONTAINER", "forem-dev")


def sg(cmd, **kw):
    return subprocess.run(["sg", "docker", "-c", cmd], capture_output=True, text=True, **kw)


def popen(cmd):
    return subprocess.Popen(["sg", "docker", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)


def top():
    return sg("docker top %s -eo pid,args" % CONTAINER).stdout.splitlines()


def procs_with(needle):
    return [l.strip() for l in top() if needle in l and "docker top" not in l]


def ros_left():
    r = sg("bash %s/docker/run.sh exec python3 scripts/task0_proc.py foreign" % ROOT)
    return json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else None


def tree_hash(path):
    h = hashlib.sha256()
    for d, _, files in sorted(os.walk(path)):
        for f in sorted(files):
            p = os.path.join(d, f)
            h.update(p.encode()); h.update(open(p, "rb").read())
    return h.hexdigest()


def manifest(rid):
    return json.load(open(os.path.join(ROOT, "results", "task2", rid, "manifest.json")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--freeze-id", required=True)
    a = ap.parse_args()
    tag, fz = a.tag, a.freeze_id
    E = "%s --freeze-id %s" % (ENTRY, fz)
    cases = []

    def record(name, ok, detail):
        cases.append({"case": name, "pass": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + " :: " + str(detail), flush=True)

    res_root = os.path.join(ROOT, "results", "task2")
    log_root = os.path.join(ROOT, "logs", "task2")

    def snapshot():
        return (set(os.listdir(res_root)), set(os.listdir(log_root)))

    def args(case="M3", mode="bypass", delay="0", rid="x", extra=""):
        return "%s %s --mode %s --delay-ms '%s' --case %s --run-id '%s'" % (E, extra, mode, delay, case, rid)

    # E1 / E2 / E2b
    before = snapshot()
    rcs = {bad: sg(args(rid=bad)).returncode for bad in ("", "../x", "-x", "a b", "a/b")}
    record("E1 invalid run-ids refused (12), nothing created", all(v == 12 for v in rcs.values()) and snapshot() == before, rcs)
    rid = tag + "-ref"
    r = {"case": sg(args(case="NOPE", rid=rid + "1")).returncode, "mode": sg(args(mode="fast", rid=rid + "2")).returncode,
         "unknown_arg": sg("%s --bogus 1 --mode bypass --case M3 --run-id %s3" % (E, rid)).returncode,
         "no_freeze": sg("%s --mode bypass --delay-ms 0 --case M3 --run-id %s4" % (ENTRY, rid)).returncode,
         "bad_freeze": sg("%s --freeze-id does-not-exist --mode bypass --case M3 --run-id %s5" % (ENTRY, rid)).returncode,
         "experiment_needs_execution_freeze": sg(args(rid=rid + "6", extra="--experiment exp2.1")).returncode,
         "experiment_unknown": sg(args(rid=rid + "7", extra="--experiment exp9")).returncode}
    record("E2 unknown case/mode/arg, missing or unknown freeze, --experiment with a protocol-only freeze or unknown experiment: refused (12), nothing created",
           all(v == 12 for v in r.values()) and snapshot() == before, r)
    r = {d: sg(args(mode="queue", delay=d, rid="%s-bd%d" % (tag, i))).returncode for i, d in enumerate(("nan", "inf", "-80", "100", "abc", "1e9", "79.9"))}
    r["bypass_80"] = sg(args(mode="bypass", delay="80", rid=tag + "-bp80")).returncode
    record("E2b bad delays and bypass with a non-zero delay refused (12), nothing created", all(v == 12 for v in r.values()) and snapshot() == before, r)

    # E3 reused id: existing evidence is hand-made (no simulation needed)
    rid = "%s-reuse" % tag
    os.makedirs(os.path.join(res_root, rid)); os.makedirs(os.path.join(log_root, rid))
    open(os.path.join(res_root, rid, "keep.txt"), "w").write("original evidence")
    h1 = tree_hash(os.path.join(res_root, rid))
    r = sg(args(rid=rid))
    record("E3 reused run-id refused (12), evidence untouched", r.returncode == 12 and tree_hash(os.path.join(res_root, rid)) == h1, {"exit": r.returncode})

    # E4 concurrent: hold the shared lock like another simulation entry would
    lockp = os.path.join(ROOT, "logs", "task0", ".smoke.lock")
    holder = subprocess.Popen(["flock", "-n", lockp, "sleep", "25"], start_new_session=True)
    time.sleep(1)
    rid = "%s-conc" % tag
    r = sg(args(rid=rid))
    alive = holder.poll() is None
    os.killpg(holder.pid, signal.SIGKILL); holder.wait()   # flock forks sleep: kill the group or the lock stays held
    time.sleep(0.5)
    record("E4 concurrent entry refused (11), lock holder unharmed, nothing created", r.returncode == 11 and alive and not os.path.exists(os.path.join(res_root, rid)),
           {"exit": r.returncode, "holder_alive_at_check": alive})

    # E5 foreign ROS-like process: a test-owned process whose argv[0] is 'rosbag' (shows as 'rosbag 120')
    rid = "%s-foreign" % tag
    sg("bash %s/docker/run.sh exec bash -c \"nohup bash -c 'exec -a rosbag sleep 120' >/dev/null 2>&1 & echo started\"" % ROOT)
    time.sleep(1)
    fp = [l for l in top() if "rosbag 120" in l]
    r = sg(args(rid=rid))
    still = [l for l in top() if "rosbag 120" in l]
    for l in still:   # only this test's own decoy
        os.kill(int(l.split()[0]), signal.SIGTERM)   # docker top shows host PIDs; the decoy runs as this user
    m = manifest(rid) if os.path.exists(os.path.join(res_root, rid, "manifest.json")) else {}
    record("E5 foreign process -> exit 10, nothing started, decoy untouched", bool(fp) and r.returncode == 10 and bool(still) and m.get("startup_ok") is False,
           {"exit": r.returncode, "decoy_present_before": bool(fp), "decoy_alive_after": bool(still)})
    time.sleep(1)

    # E6 collector abort (queue mode)
    rid = "%s-abort" % tag
    r = sg(args(mode="queue", delay="80", rid=rid, extra="--test-collect-abort 7"))
    m = manifest(rid)
    ev = all(os.path.exists(os.path.join(res_root, rid, f)) for f in ("abort.json", "commands.json", "run.bag", "delay_events.jsonl"))
    record("E6 collector abort (queue) is non-zero (1), evidence kept, nothing left", r.returncode == 1 and m["collect_exit"] == 2 and ev and m["cleanup_exit"] == 0
           and not procs_with("--run-id " + rid) and ros_left() == [], {"exit": r.returncode, "collect_exit": m["collect_exit"], "evidence_files": ev, "cleanup_exit": m["cleanup_exit"],
                                                                      "delay_exit": m.get("delay_exit")})

    # E7 cleanup residue
    rid = "%s-residue" % tag
    r = sg(args(mode="queue", delay="0", rid=rid, extra="--test-fault residue"))
    m = manifest(rid)
    record("E7 injected cleanup residue -> exit 15 wins", r.returncode == 15 and m["final_exit"] == 15 and m["cleanup_exit"] == 15, {"exit": r.returncode, "manifest": [m["final_exit"], m["cleanup_exit"]]})
    for n in ("collect", "delay", "bag", "throttle", "launch"):   # the injected fault may leave the run's own processes; only logs/task2/<rid> identities are stopped
        sg("bash %s/docker/run.sh exec python3 scripts/task0_proc.py stop --dir logs/task2/%s --name %s" % (ROOT, rid, n))

    # E8 / E9 interrupts (queue mode, case H: long enough to interrupt mid-collection)
    for sigval, sname, code in ((signal.SIGTERM, "TERM", 143), (signal.SIGINT, "INT", 130)):
        rid = "%s-%s" % (tag, sname.lower())
        p = popen(args(case="H", mode="queue", delay="80", rid=rid))
        tl = os.path.join(log_root, rid, "timeline.txt")
        t0 = time.time()
        while time.time() - t0 < 120 and not (os.path.exists(tl) and "collect start" in open(tl).read()):
            time.sleep(0.5)
        time.sleep(5)
        names = ("collect_task2.py --run-id " + rid, "task2_delay_node.py --run-id " + rid, "rosbag record -O results/task2/%s/run.bag" % rid, "topic_tools throttle", "roslaunch forem_sim")
        before = {n: bool(procs_with(n)) for n in names}
        os.killpg(p.pid, sigval)
        try:
            p.communicate(timeout=180)
        except subprocess.TimeoutExpired:
            p.kill(); p.communicate()
        after = {n: procs_with(n) for n in names}
        m = manifest(rid) if os.path.exists(os.path.join(res_root, rid, "manifest.json")) else {}
        record("E%d %s mid-collection: collector/proxy/bag/throttle/launch existed before and are gone after; wrapper %d; collect_exit != 0" % (8 if sname == "TERM" else 9, sname, code),
               all(before.values()) and not any(after.values()) and m.get("final_exit") == code and m.get("interrupted") == sname and m.get("collect_exit") not in (0, None)
               and m.get("cleanup_exit") == 0 and m.get("delay_exit") is not None and ros_left() == [],
               {"alive_before": before, "left_after": {k: v for k, v in after.items() if v}, "final_exit": m.get("final_exit"), "collect_exit": m.get("collect_exit"),
                "delay_exit": m.get("delay_exit"), "cleanup_exit": m.get("cleanup_exit")})

    # E10 / E11 normal short runs
    for eid, mode, delay in (("E10", "bypass", "0"), ("E11", "queue", "80")):
        rid = "%s-%s" % (tag, eid.lower())
        r = sg(args(mode=mode, delay=delay, rid=rid))
        m = manifest(rid)
        stages = ("collect_exit", "convert_exit", "analyze_exit", "cleanup_exit") + (("delay_exit",) if mode == "queue" else ())
        no_proxy = (m.get("delay_exit") is None) if mode == "bypass" else True
        record("%s normal M3 %s run: exit 0, every stage exit 0, nothing left" % (eid, mode), r.returncode == 0 and all(m[k] == 0 for k in stages) and no_proxy and ros_left() == []
               and not procs_with("--run-id " + rid), {"exit": r.returncode, "stages": {k: m.get(k) for k in stages}})

    # E12 proxy killed during the pre-hold of a queue run
    rid = "%s-e12" % tag
    p = popen(args(mode="queue", delay="80", rid=rid))
    tl = os.path.join(log_root, rid, "timeline.txt")
    t0 = time.time()
    while time.time() - t0 < 120 and not (os.path.exists(tl) and "collect start" in open(tl).read()):
        time.sleep(0.3)
    time.sleep(2.0)
    meta_p = os.path.join(log_root, rid, "delay.json")
    killed = False
    if os.path.exists(meta_p):
        pid = json.load(open(meta_p))["root"]["pid"]
        hostpids = [l.split()[0] for l in top() if "task2_delay_node.py --run-id " + rid in l]
        for hp in hostpids:
            os.kill(int(hp), signal.SIGKILL); killed = True
    try:
        out, _ = p.communicate(timeout=240)
    except subprocess.TimeoutExpired:
        p.kill(); out, _ = p.communicate()
    m = manifest(rid) if os.path.exists(os.path.join(res_root, rid, "manifest.json")) else {}
    met = json.load(open(os.path.join(res_root, rid, "run_metrics.json"))) if os.path.exists(os.path.join(res_root, rid, "run_metrics.json")) else {}
    record("E12 proxy SIGKILLed before the send: run INVALID (exit 1), no hidden pass, cleanup 0, nothing left",
           killed and p.returncode == 1 and m.get("cleanup_exit") == 0 and ros_left() == [] and not procs_with("--run-id " + rid) and
           (met.get("pass") is False or m.get("collect_exit") not in (0, None) or m.get("analyze_exit") != 0),
           {"killed": killed, "exit": p.returncode, "collect_exit": m.get("collect_exit"), "delay_exit": m.get("delay_exit"), "analyze_exit": m.get("analyze_exit"),
            "failed_gates": met.get("failed_gates"), "cleanup_exit": m.get("cleanup_exit")})

    ok = all(c["pass"] for c in cases)
    outdir = os.path.join(res_root, tag + "-report")
    os.makedirs(outdir, exist_ok=False)
    json.dump({"tag": tag, "freeze_id": fz, "all_pass": ok, "cases": cases, "finished": time.strftime("%F %T %z")}, open(os.path.join(outdir, "report.json"), "w"), indent=2)
    print("ALL PASS" if ok else "FAILURES", flush=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
