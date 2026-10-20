#!/usr/bin/env python3
"""Process manager for task0 runs (stdlib only; Linux; runs inside forem-dev or on a host in tests).

Purpose: start a long-lived process (roslaunch / rosbag record) and later stop exactly the
processes that belong to it - never anything matched by name, and never anything adopted from a
bare PID.

Ownership model (task0.10):
  * `start` launches a small SUPERVISOR (this script, `_supervise`) that marks itself a Linux
    child sub-reaper (PR_SET_CHILD_SUBREAPER) and starts the command in its own session. Any
    descendant that loses its parent is re-parented to the supervisor, not to PID 1, so the whole
    tree stays reachable while the supervisor lives.
  * The supervisor polls /proc every 0.1 s and persists every member's identity
    (pid + kernel start time + command) to DIR/NAME.tree.json. Identity = (pid, start time), so a
    recycled PID never matches.
  * `stop` rebuilds ownership ONLY from identity-verified live members (supervisor, root, the
    persisted members) and from descendants of those verified members. A member whose identity no
    longer matches is dropped and its bare PID is never used to find children (PID reuse safe).
    Works even if the supervisor or the root died first, because the persisted identities remain.
  * Signals: SIGINT to the root (or, if the root is gone, to all live members) -> SIGTERM -> SIGKILL,
    each stage re-verifying identity right before signalling. Success = no verified member alive.
    Repeated stop re-verifies survivors instead of trusting an earlier "stopped" record.

  task0_proc.py start  --dir DIR --name NAME [--allow-foreign] -- CMD...
  task0_proc.py status --dir DIR --name NAME [--tree]     0 if root (or any member with --tree) alive
  task0_proc.py stop   --dir DIR --name NAME [--int-wait S --term-wait S --kill-wait S]
  task0_proc.py exitcode --dir DIR --name NAME            recorded exit status of the managed root (3 if not recorded)
  task0_proc.py foreign                                   exit 10 if ROS/Gazebo-like processes exist
  task0_proc.py grep --needle TEXT                        exit 10 if any process command line contains TEXT
"""
import argparse
import ctypes
import json
import os
import signal
import subprocess
import sys
import time

WATCH = ("roslaunch", "rosmaster", "roscore", "rosout", "gzserver", "gzclient", "rosbag", "gazebo_ros", "robot_state_publisher",
         "check_feedback", "collect_task1", "throttle", "collect_task2", "task2_delay_node")
PR_SET_CHILD_SUBREAPER = 36


# ------------------------------------------------------------------ /proc helpers
def proc_stat(pid):
    """(ppid, starttime_ticks, comm, state) or None."""
    try:
        with open("/proc/%d/stat" % pid) as f:
            s = f.read()
    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
        return None
    rp = s.rindex(")")
    comm = s[s.index("(") + 1:rp]
    rest = s[rp + 2:].split()
    return int(rest[1]), int(rest[19]), comm, rest[0]


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
    """All descendants of `root` by the parent links visible now. Callers must only pass a PID whose
    identity they have just verified (see alive())."""
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
    """True iff a live, non-zombie process with exactly this (pid, start time) exists."""
    if not idn:
        return False
    st = proc_stat(idn["pid"])
    return bool(st and st[1] == idn["start"] and st[3] != "Z")


def foreign():
    me = os.getpid()
    res = []
    for p in all_pids():
        if p == me:
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
    j = lambda suffix: os.path.join(d, name + suffix)
    return {"meta": j(".json"), "log": j(".log"), "tree": j(".tree.json"), "suplog": j(".supervisor.log"), "cleanup": j(".cleanup.json"),
            "exit": j(".exit.json")}


def write_json_atomic(path, obj):
    tmp = path + ".tmp%d" % os.getpid()
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


def load_json(path):
    with open(path) as f:
        return json.load(f)


# ------------------------------------------------------------------ supervisor
def cmd_supervise(a):
    """Runs detached. Owns the tree: sub-reaper + persistent identity record."""
    p = paths(a.dir, a.name)
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        subreaper = libc.prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) == 0
    except Exception:
        subreaper = False
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # stop escalates to the supervisor last, with SIGTERM
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    logf = open(p["log"], "ab")
    child = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             start_new_session=True, cwd=os.getcwd())
    me = identity(os.getpid())
    root = identity(child.pid) or {"pid": child.pid, "start": -1, "comm": "?", "cmd": " ".join(cmd)}
    members = {root["pid"]: root}
    write_json_atomic(p["tree"], {"supervisor": me, "members": list(members.values())})
    write_json_atomic(p["meta"], {"supervisor": me, "root": root, "argv": cmd, "subreaper": subreaper, "name": a.name,
                                  "started_unix": time.time()})
    empty_scans = 0  # a single empty scan is not proof: an exiting parent can be visible before its orphan is re-parented
    while True:
        # reap every child we adopted so zombies do not linger (we are their parent now)
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if pid == 0:
                break
            if pid == child.pid:  # the managed root itself: keep its exit status (negative = killed by that signal)
                code = os.waitstatus_to_exitcode(status)
                write_json_atomic(p["exit"], {"root_pid": pid, "exit_code": code, "signal": -code if code < 0 else None,
                                              "time_unix": time.time()})
        changed = False
        live = 0
        for c in descendants(os.getpid()):
            st = proc_stat(c)
            if not st or st[3] == "Z":
                continue
            live += 1
            if c not in members or members[c]["start"] != st[1]:
                i = identity(c)
                if i:
                    members[c] = i
                    changed = True
        if changed:
            write_json_atomic(p["tree"], {"supervisor": me, "members": list(members.values())})
        empty_scans = empty_scans + 1 if live == 0 else 0
        if empty_scans >= 15:  # ~1.5 s of continuous emptiness
            break
        time.sleep(0.1)
    return 0


def cmd_start(a):
    fp = foreign()
    if fp and not a.allow_foreign:
        print(json.dumps({"error": "foreign ROS/Gazebo processes present", "processes": fp}))
        return 10
    p = paths(a.dir, a.name)
    if os.path.exists(p["meta"]):
        print(json.dumps({"error": "already started: " + p["meta"]}))
        return 11
    os.makedirs(a.dir, exist_ok=True)
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    suplog = open(p["suplog"], "ab")
    subprocess.Popen([sys.executable, os.path.abspath(__file__), "_supervise", "--dir", a.dir, "--name", a.name, "--"] + cmd,
                     stdout=suplog, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True, cwd=os.getcwd())
    deadline = time.time() + 10
    while time.time() < deadline and not os.path.exists(p["meta"]):
        time.sleep(0.05)
    if not os.path.exists(p["meta"]):
        print(json.dumps({"error": "supervisor did not start (see %s)" % p["suplog"]}))
        return 12
    time.sleep(0.2)
    meta = load_json(p["meta"])
    if not alive(meta["root"]) and not any(alive(m) for m in load_json(p["tree"])["members"]) and not os.path.exists(p["exit"]):
        print(json.dumps({"error": "process exited immediately without a recorded exit status", "log": p["log"]}))
        return 12
    print(json.dumps({"started": meta["root"]["pid"], "supervisor": meta["supervisor"]["pid"], "meta": p["meta"]}))
    return 0


def cmd_status(a):
    p = paths(a.dir, a.name)
    try:
        meta = load_json(p["meta"])
    except FileNotFoundError:
        return 2
    if a.tree:
        try:
            members = load_json(p["tree"])["members"]
        except FileNotFoundError:
            members = []
        return 0 if any(alive(m) for m in members + [meta["root"], meta["supervisor"]]) else 1
    return 0 if alive(meta["root"]) else 1


# ------------------------------------------------------------------ stop
def owned_alive(seed_identities):
    """Identity-verified live members and their descendants. Ownership only ever flows from a member
    whose (pid, start) was verified alive right now; a stale/recycled PID contributes nothing."""
    members = {}
    frontier = []
    for i in seed_identities:
        if i and alive(i):
            members[i["pid"]] = i
            frontier.append(i["pid"])
    while frontier:
        pid = frontier.pop()
        for c in descendants(pid):
            if c not in members:
                j = identity(c)
                if j and alive(j):
                    members[c] = j
                    frontier.append(c)
    return members


def next_cleanup_path(base):
    if not os.path.exists(base):
        return base
    n = 2
    while os.path.exists(base.replace(".cleanup.json", ".cleanup-%d.json" % n)):
        n += 1
    return base.replace(".cleanup.json", ".cleanup-%d.json" % n)


def cmd_stop(a):
    p = paths(a.dir, a.name)
    try:
        meta = load_json(p["meta"])
    except FileNotFoundError:
        write_json_atomic(next_cleanup_path(p["cleanup"]), {"error": "no meta; nothing stopped", "residue": []})
        print("no meta for", a.name)
        return 0
    sup, root = meta.get("supervisor"), meta["root"]
    try:
        recorded = load_json(p["tree"])["members"]
    except FileNotFoundError:
        recorded = []
    seeds = recorded + [root, sup]
    known = {}  # every identity we owned during this stop (for the record)

    def is_sup(pid, i):
        return bool(sup) and pid == sup["pid"] and i["start"] == sup["start"]

    def refresh():
        cur = owned_alive(seeds)
        for pid, i in cur.items():
            known.setdefault(pid, i)
        return cur

    def signal_members(sig):
        for pid, i in list(refresh().items()):
            if is_sup(pid, i):
                continue
            if alive(i):  # identity re-verified immediately before signalling
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass

    def wait(secs):
        end = time.time() + secs
        while True:
            rest = [i for pid, i in refresh().items() if not is_sup(pid, i)]
            if not rest:
                return True
            if time.time() >= end:
                return False
            time.sleep(0.1)

    log = {"name": a.name, "root": root, "supervisor": sup, "stages": []}
    before = refresh()
    log["initial_owned_alive"] = [{"pid": p_, "cmd": i["cmd"][:100]} for p_, i in before.items()]
    if not before:
        note = "already stopped" if os.path.exists(p["cleanup"]) else "nothing alive at stop (process ended by itself)"
        if not os.path.exists(p["cleanup"]):
            log.update({"residue": [], "note": note})
            write_json_atomic(p["cleanup"], log)
        print(json.dumps({"stopped": a.name, "note": note, "residue": []}))
        return 0

    if a.test_fault == "no-signal":  # regression hook: pretend the signals did not work
        time.sleep(0.5)
        log["stages"].append("TEST FAULT no-signal")
    else:
        if alive(root):
            os.kill(root["pid"], signal.SIGINT)
            log["stages"].append("SIGINT root")
        else:
            signal_members(signal.SIGINT)
            log["stages"].append("SIGINT members (root already gone)")
        if not wait(a.int_wait):
            signal_members(signal.SIGTERM)
            log["stages"].append("SIGTERM members")
            if not wait(a.term_wait):
                signal_members(signal.SIGKILL)
                log["stages"].append("SIGKILL members")
                wait(a.kill_wait)
        # the supervisor exits by itself once nothing is left; make sure it did
        if sup and alive(sup):
            end = time.time() + 3
            while alive(sup) and time.time() < end:
                time.sleep(0.1)
            if alive(sup):
                os.kill(sup["pid"], signal.SIGTERM)
                log["stages"].append("SIGTERM supervisor")
                end = time.time() + 3
                while alive(sup) and time.time() < end:
                    time.sleep(0.1)
                if alive(sup):
                    os.kill(sup["pid"], signal.SIGKILL)
                    log["stages"].append("SIGKILL supervisor")
                    time.sleep(0.3)

    residue = [{"pid": pid, "cmd": i["cmd"][:120]} for pid, i in refresh().items()]
    if a.test_fault == "residue":
        residue.append({"pid": -1, "cmd": "INJECTED TEST FAULT (no real process)"})
    log["known_processes"] = [{"pid": pid, "cmd": i["cmd"][:100]} for pid, i in known.items()]
    log["residue"] = residue
    write_json_atomic(next_cleanup_path(p["cleanup"]), log)
    print(json.dumps({"stopped": a.name, "stages": log["stages"], "residue": residue}))
    return 0 if not residue else 1


def cmd_exitcode(a):
    """Print the managed root's recorded exit status. Exit 0 with the status if known, 3 if not (yet) recorded."""
    p = paths(a.dir, a.name)
    try:
        d = load_json(p["exit"])
    except FileNotFoundError:
        print(json.dumps({"exit_code": None}))
        return 3
    print(json.dumps(d))
    return 0


def cmd_grep(a):
    """List processes whose full command line contains a string (identification of a run's processes by run-id)."""
    me = os.getpid()
    hits = []
    for p_ in all_pids():
        if p_ == me:
            continue
        cl = cmdline(p_)
        if a.needle in cl and "task0_proc.py" not in cl:
            hits.append({"pid": p_, "cmd": cl[:200]})
    print(json.dumps(hits))
    return 10 if hits else 0


def cmd_foreign(a):
    fp = foreign()
    print(json.dumps(fp))
    return 10 if fp else 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd_name", required=True)
    for n in ("start", "status", "stop", "_supervise", "exitcode"):
        s = sub.add_parser(n)
        s.add_argument("--dir", required=True)
        s.add_argument("--name", required=True)
        if n in ("start", "_supervise"):
            if n == "start":
                s.add_argument("--allow-foreign", action="store_true")
            s.add_argument("cmd", nargs=argparse.REMAINDER)
        if n == "status":
            s.add_argument("--tree", action="store_true")
        if n == "stop":
            s.add_argument("--int-wait", type=float, default=20.0)
            s.add_argument("--term-wait", type=float, default=10.0)
            s.add_argument("--kill-wait", type=float, default=5.0)
            s.add_argument("--test-fault", default=None, help="regression-test hook: 'residue' reports a fake residual process; 'no-signal' skips signalling")
    sub.add_parser("foreign")
    g = sub.add_parser("grep")
    g.add_argument("--needle", required=True)
    a = ap.parse_args()
    sys.exit({"start": cmd_start, "status": cmd_status, "stop": cmd_stop, "foreign": cmd_foreign, "_supervise": cmd_supervise,
              "exitcode": cmd_exitcode, "grep": cmd_grep}[a.cmd_name](a))


if __name__ == "__main__":
    main()
