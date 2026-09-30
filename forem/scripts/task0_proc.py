#!/usr/bin/env python3
"""Container-side process manager for task0 runs (stdlib only; runs inside forem-dev).

Purpose: start a long-lived process (roslaunch / rosbag record) detached, remember its
*identity* (pid + kernel start time), and later stop exactly that process and its
descendants - never anything matched by name only.

  task0_proc.py start --dir DIR --name NAME [--allow-foreign] -- CMD...
      refuse (exit 10) if unknown ROS/Gazebo processes already exist (unless --allow-foreign,
      used for the 2nd managed process of the same run); write DIR/NAME.json, log DIR/NAME.log.
  task0_proc.py status --dir DIR --name NAME     exit 0 if identity still alive, 1 otherwise
  task0_proc.py stop --dir DIR --name NAME       SIGINT -> SIGTERM -> SIGKILL, own tree only;
                                                 writes DIR/NAME.cleanup.json; exit 0 iff no residue
  task0_proc.py foreign                          list ROS/Gazebo-like processes; exit 10 if any

Descendants are re-collected before every signalling stage (roslaunch children may be
re-parented), and each is signalled only if its (pid, start time) matches what was recorded.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time

WATCH = ("roslaunch", "rosmaster", "roscore", "rosout", "gzserver", "gzclient", "rosbag", "gazebo_ros", "robot_state_publisher")
TICKS = os.sysconf("SC_CLK_TCK")


def proc_stat(pid):
    """Return (ppid, starttime_ticks, comm) or None."""
    try:
        with open("/proc/%d/stat" % pid) as f:
            s = f.read()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    rp = s.rindex(")")
    comm = s[s.index("(") + 1:rp]
    rest = s[rp + 2:].split()
    # rest[0]=state rest[1]=ppid ... rest[19]=starttime
    return int(rest[1]), int(rest[19]), comm


def cmdline(pid):
    try:
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            return f.read().replace(b"\0", b" ").decode(errors="replace").strip()
    except OSError:
        return ""


def all_pids():
    return [int(p) for p in os.listdir("/proc") if p.isdigit()]


def children_map():
    m = {}
    for p in all_pids():
        st = proc_stat(p)
        if st:
            m.setdefault(st[0], []).append(p)
    return m


def descendants(root):
    m = children_map()
    out, stack = [], [root]
    while stack:
        p = stack.pop()
        for c in m.get(p, []):
            out.append(c)
            stack.append(c)
    return out


def identity(pid):
    st = proc_stat(pid)
    return {"pid": pid, "start": st[1], "comm": st[2], "cmd": cmdline(pid)} if st else None


def alive(idn):
    st = proc_stat(idn["pid"])
    if not st or st[1] != idn["start"]:
        return False
    try:  # zombie counts as gone
        with open("/proc/%d/stat" % idn["pid"]) as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return False


def foreign():
    me = os.getpid()
    mine = {me, os.getppid()}
    res = []
    for p in all_pids():
        if p in mine:
            continue
        cl = cmdline(p)
        if not cl:
            continue
        exe = cl.split()[0].rsplit("/", 1)[-1]
        args0 = " ".join(cl.split()[:3])
        if any(w in exe or w in args0 for w in WATCH) and "task0_proc.py" not in cl:
            res.append({"pid": p, "cmd": cl[:160]})
    return res


def paths(d, name):
    return os.path.join(d, name + ".json"), os.path.join(d, name + ".log"), os.path.join(d, name + ".cleanup.json")


def cmd_start(a):
    fp = foreign()
    if fp and not a.allow_foreign:
        print(json.dumps({"error": "foreign ROS/Gazebo processes present", "processes": fp}))
        return 10
    meta, logp, _ = paths(a.dir, a.name)
    if os.path.exists(meta):
        print(json.dumps({"error": "already started: " + meta}))
        return 11
    os.makedirs(a.dir, exist_ok=True)
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    logf = open(logp, "ab")
    p = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         start_new_session=True, cwd=os.getcwd())
    time.sleep(0.2)
    idn = identity(p.pid)
    if idn is None:
        print(json.dumps({"error": "process exited immediately", "rc": p.poll()}))
        return 12
    idn.update({"name": a.name, "argv": cmd, "started_unix": time.time()})
    with open(meta, "w") as f:
        json.dump(idn, f, indent=2)
    print(json.dumps({"started": idn["pid"], "meta": meta}))
    return 0


def load(d, name):
    with open(paths(d, name)[0]) as f:
        return json.load(f)


def cmd_status(a):
    try:
        return 0 if alive(load(a.dir, a.name)) else 1
    except FileNotFoundError:
        return 2


def cmd_stop(a):
    meta, _, outp = paths(a.dir, a.name)
    try:
        root = load(a.dir, a.name)
    except FileNotFoundError:
        json.dump({"error": "no meta; nothing stopped", "residue": []}, open(outp, "w"))
        print("no meta for", a.name)
        return 0
    if os.path.exists(outp) and not alive(root):
        print(json.dumps({"already_stopped": a.name}))  # idempotent: keep the first cleanup record
        return 0
    known = {}  # pid -> identity
    def collect():
        if alive(root):
            known[root["pid"]] = root
        base = root["pid"]
        for c in descendants(base):
            i = identity(c)
            if i:
                known.setdefault(c, i)
        # descendants of already known but re-parented children are covered by their own tree
        for pid, i in list(known.items()):
            if pid != base and alive(i):
                for c in descendants(pid):
                    j = identity(c)
                    if j:
                        known.setdefault(c, j)
    def live():
        return [i for i in known.values() if alive(i)]
    def signal_all(sig):
        for i in live():
            if alive(i):  # identity re-checked right before signalling
                try:
                    os.kill(i["pid"], sig)
                except ProcessLookupError:
                    pass
    def wait(secs):
        end = time.time() + secs
        while time.time() < end:
            collect()
            if not live():
                return True
            time.sleep(0.2)
        return not live()
    log = {"name": a.name, "root": root, "stages": []}
    collect()
    log["initial_live"] = [i["pid"] for i in live()]
    if alive(root):
        os.kill(root["pid"], signal.SIGINT)
        log["stages"].append("SIGINT root")
    if not wait(20):
        collect(); signal_all(signal.SIGTERM); log["stages"].append("SIGTERM tree")
        if not wait(10):
            collect(); signal_all(signal.SIGKILL); log["stages"].append("SIGKILL tree")
            wait(5)
    residue = [{"pid": i["pid"], "cmd": i["cmd"][:120]} for i in live()]
    log["known_processes"] = [{"pid": p, "cmd": i["cmd"][:100]} for p, i in known.items()]
    if a.test_fault == "residue":
        residue.append({"pid": -1, "cmd": "INJECTED TEST FAULT (no real process)"})
    log["residue"] = residue
    with open(outp, "w") as f:
        json.dump(log, f, indent=2)
    print(json.dumps({"stopped": a.name, "stages": log["stages"], "residue": residue}))
    return 0 if not residue else 1


def cmd_foreign(a):
    fp = foreign()
    print(json.dumps(fp))
    return 10 if fp else 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd_name", required=True)
    for n in ("start", "status", "stop"):
        s = sub.add_parser(n)
        s.add_argument("--dir", required=True)
        s.add_argument("--name", required=True)
        if n == "start":
            s.add_argument("--allow-foreign", action="store_true")
            s.add_argument("cmd", nargs=argparse.REMAINDER)
        if n == "stop":
            s.add_argument("--test-fault", default=None, help="regression-test hook: 'residue' reports a fake residual process AFTER really stopping")
    sub.add_parser("foreign")
    a = ap.parse_args()
    sys.exit({"start": cmd_start, "status": cmd_status, "stop": cmd_stop, "foreign": cmd_foreign}[a.cmd_name](a))


if __name__ == "__main__":
    main()
