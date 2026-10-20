#!/usr/bin/env python3
"""Per-instance Husky+UR5 Gazebo/ROS launcher for parallel runs (task4.8.1). Stdlib only; runs inside forem-dev.

Every instance index K gets its own ROS master (11400+K), Gazebo master (11500+K), ignition-transport partition,
HOME / ROS_HOME / ROS_LOG_DIR / Gazebo log directory, and an identity-supervised process tree (scripts/task0_proc.py).
It does NOT touch the single-simulation wrapper run_task3_core.sh and uses no shared lock: mutual exclusion is per instance
number only (flock on logs/task4/.instances/inst<K>.lock while start/stop run, plus the registry record).

  scwm_instance.py start  --inst K --run-id R [--cpus 0-7] [--timeout 240] [--launch-arg k:=v]...
  scwm_instance.py stop   --inst K
  scwm_instance.py status --inst K            (exit 0 alive+ready, 1 not alive, 2 unknown instance, 3 alive but master unreachable)
  scwm_instance.py env    --inst K [--format sh|json]
  scwm_instance.py exec   --inst K [--cpus LIST] -- CMD...      (runs CMD with the instance environment; execvpe)
  scwm_instance.py list
  scwm_instance.py residue --inst K           (exit 10 if any process still carries this instance's environment)

Isolation items (why each exists):
  ROS_MASTER_URI / roslaunch -p   own rosmaster, so no node/topic/param is shared (11311 is left to other users)
  GAZEBO_MASTER_URI               own gzserver master socket
  IGN_PARTITION / GZ_PARTITION    ignition-transport discovery is UDP multicast and ignores the master URI; the partition keeps
                                  topics of different instances apart
  HOME, ROS_HOME, ROS_LOG_DIR     ~/.gazebo (logs, state), ~/.ros, ~/.cache, roslaunch logs would otherwise collide
  ROS_IP/GAZEBO_IP/IGN_IP         loopback only
Start refuses a live instance with the same number, ports that are already bound, and (when run twice concurrently) is
serialised by the instance flock. Stop only signals identity-verified members of this instance (task0_proc.py).
"""
import argparse
import fcntl
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

FOREM = Path(__file__).resolve().parent.parent
PROC = FOREM / "scripts" / "task0_proc.py"
REG = FOREM / "logs" / "task4" / ".instances"
ROS_BASE, GZ_BASE = 11400, 11500
MAX_INST = 99
READY = ("controllers running", "You can start planning now")
FAIL = ("did not succeed", "controllers not running", "Traceback")
ENV_KEYS = ("ROS_MASTER_URI", "GAZEBO_MASTER_URI", "IGN_PARTITION", "GZ_PARTITION", "HOME", "ROS_HOME", "ROS_LOG_DIR",
            "ROS_IP", "GAZEBO_IP", "IGN_IP", "FOREM_INSTANCE")


def inst_env(k, base):
    home = Path(base) / "home"
    return {
        "ROS_MASTER_URI": "http://127.0.0.1:%d" % (ROS_BASE + k),
        "GAZEBO_MASTER_URI": "http://127.0.0.1:%d" % (GZ_BASE + k),
        "IGN_PARTITION": "forem_inst%d" % k,
        "GZ_PARTITION": "forem_inst%d" % k,
        "HOME": str(home),
        "ROS_HOME": str(home / ".ros"),
        "ROS_LOG_DIR": str(Path(base) / "roslog"),
        "ROS_IP": "127.0.0.1", "GAZEBO_IP": "127.0.0.1", "IGN_IP": "127.0.0.1",
        "FOREM_INSTANCE": str(k),
    }


def reg_path(k):
    return REG / ("inst%d.json" % k)


def load_reg(k):
    try:
        return json.loads(reg_path(k).read_text())
    except FileNotFoundError:
        return None


def port_free(port):
    s = socket.socket()
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def proc(args, env=None, timeout=60):
    return subprocess.run([sys.executable, str(PROC)] + args, capture_output=True, text=True, env=env, timeout=timeout)


def master_ok(k, timeout=2.0):
    import xmlrpc.client
    try:
        socket.setdefaulttimeout(timeout)
        code, _, _ = xmlrpc.client.ServerProxy("http://127.0.0.1:%d" % (ROS_BASE + k)).getPid("/scwm_instance")
        return code == 1
    except Exception:
        return False
    finally:
        socket.setdefaulttimeout(None)


def residue(k):
    """Processes (any) whose environment carries this instance's partition marker."""
    marker = ("IGN_PARTITION=forem_inst%d" % k).encode()
    me = os.getpid()
    out = []
    for p in os.listdir("/proc"):
        if not p.isdigit() or int(p) == me:
            continue
        try:
            with open("/proc/%s/environ" % p, "rb") as f:
                env = f.read().split(b"\0")
            if marker in env:
                cl = open("/proc/%s/cmdline" % p, "rb").read().replace(b"\0", b" ").decode(errors="replace").strip()
                st = open("/proc/%s/stat" % p).read()
                if st[st.rindex(")") + 2] == "Z":
                    continue
                out.append({"pid": int(p), "cmd": cl[:140]})
        except OSError:
            continue
    return out


class Lock:
    def __init__(self, k):
        REG.mkdir(parents=True, exist_ok=True)
        self.f = open(REG / ("inst%d.lock" % k), "w")

    def __enter__(self):
        try:
            fcntl.flock(self.f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print(json.dumps({"error": "another start/stop of this instance number is in progress"}))
            sys.exit(11)
        return self

    def __exit__(self, *a):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


def instance_alive(reg):
    return proc(["status", "--dir", reg["dir"], "--name", "launch", "--tree"]).returncode == 0


def cmd_start(a):
    k = a.inst
    if not 0 <= k <= MAX_INST:
        print(json.dumps({"error": "instance number out of range 0..%d" % MAX_INST}))
        return 12
    if not a.run_id or not all(c.isalnum() or c in "._-" for c in a.run_id):
        print(json.dumps({"error": "bad run-id"}))
        return 12
    with Lock(k):
        old = load_reg(k)
        if old:
            if instance_alive(old):
                print(json.dumps({"error": "instance %d already running (run-id %s); refusing" % (k, old["run_id"])}))
                return 11
            reg_path(k).rename(REG / ("inst%d.stale-%d.json" % (k, int(time.time()))))
        for port in (ROS_BASE + k, GZ_BASE + k):
            if not port_free(port):
                print(json.dumps({"error": "port %d already in use; refusing" % port}))
                return 11
        d = FOREM / "logs" / ("task6" if a.world == "sim" else "task4") / a.run_id / ("inst%d" % k)
        if d.exists():
            print(json.dumps({"error": "evidence dir exists: %s" % d}))
            return 12
        d.mkdir(parents=True)
        env = dict(os.environ)
        e = inst_env(k, d)
        env.update(e)
        for key in ("HOME", "ROS_LOG_DIR"):
            Path(e[key]).mkdir(parents=True, exist_ok=True)
        Path(e["ROS_HOME"]).mkdir(parents=True, exist_ok=True)
        cmd = (["roslaunch", "-p", str(ROS_BASE + k), "forem_husky", "husky_analytical.launch"] if a.world == "sim" else
               ["roslaunch", "-p", str(ROS_BASE + k), "forem_husky", "husky_core.launch", "gui:=false"]) + a.launch_arg
        if a.cpus:
            cmd = ["taskset", "-c", a.cpus] + cmd
        reg = {"inst": k, "run_id": a.run_id, "dir": str(d), "env": e, "cmd": cmd, "cpus": a.cpus,
               "ros_port": ROS_BASE + k, "gz_port": GZ_BASE + k, "started_unix": time.time()}
        reg_path(k).write_text(json.dumps(reg, indent=2))
        r = proc(["start", "--dir", str(d), "--name", "launch", "--allow-foreign", "--"] + cmd, env=env)
        (d / "start_launch.out").write_text(r.stdout + r.stderr)
        if r.returncode != 0:
            print(json.dumps({"error": "launch start failed", "rc": r.returncode, "out": r.stdout[-300:]}))
            reg_path(k).unlink()
            return 13
        log = d / "launch.log"
        t0 = time.time()
        ok = False
        while time.time() - t0 < a.timeout:
            txt = log.read_text(errors="replace") if log.exists() else ""
            if all(m in txt for m in (("You can start planning now",) if a.world == "sim" else READY)):
                ok = True
                break
            if any(m in txt for m in FAIL) or proc(["status", "--dir", str(d), "--name", "launch", "--tree"]).returncode != 0:
                break
            time.sleep(1)
        reg["startup_s"] = round(time.time() - t0, 1)
        reg["ready"] = ok
        reg_path(k).write_text(json.dumps(reg, indent=2))
        print(json.dumps({"inst": k, "ready": ok, "startup_s": reg["startup_s"], "dir": str(d)}))
        if not ok:
            return 14   # caller runs `stop`; the record stays so that stop can clean exactly this instance
        return 0


def cmd_stop(a):
    k = a.inst
    with Lock(k):
        reg = load_reg(k)
        if not reg:
            print(json.dumps({"inst": k, "note": "no registry record; nothing stopped", "residue": residue(k)}))
            return 0
        r = proc(["stop", "--dir", reg["dir"], "--name", "launch"], timeout=120)
        (Path(reg["dir"]) / "stop.out").write_text(r.stdout + r.stderr)
        time.sleep(0.5)
        res = residue(k)
        ports = {"ros": port_free(reg["ros_port"]), "gz": port_free(reg["gz_port"])}
        reg_path(k).rename(REG / ("inst%d.stopped-%d.json" % (k, int(time.time()))))
        print(json.dumps({"inst": k, "stop_rc": r.returncode, "residue": res, "ports_free": ports}))
        return 0 if (r.returncode == 0 and not res and all(ports.values())) else 15


def cmd_status(a):
    reg = load_reg(a.inst)
    if not reg:
        print(json.dumps({"inst": a.inst, "state": "unknown"}))
        return 2
    alive = instance_alive(reg)
    m = master_ok(a.inst) if alive else False
    print(json.dumps({"inst": a.inst, "run_id": reg["run_id"], "alive": alive, "master_reachable": m, "ready": reg.get("ready"),
                      "cpus": reg.get("cpus"), "ros_port": reg["ros_port"], "gz_port": reg["gz_port"]}))
    return 0 if alive and m else (3 if alive else 1)


def cmd_env(a):
    reg = load_reg(a.inst)
    if not reg:
        print("instance %d is not registered" % a.inst, file=sys.stderr)
        return 2
    if a.format == "json":
        print(json.dumps(reg["env"], indent=2))
    else:
        for key, v in reg["env"].items():
            print("export %s=%s" % (key, subprocess.list2cmdline([v]) if " " in v else v))
    return 0


def cmd_exec(a):
    reg = load_reg(a.inst)
    if not reg:
        print("instance %d is not registered" % a.inst, file=sys.stderr)
        return 2
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if not cmd:
        print("empty command", file=sys.stderr)
        return 12
    env = dict(os.environ)
    env.update(reg["env"])
    cpus = a.cpus or reg.get("cpus")
    if cpus:
        cmd = ["taskset", "-c", cpus] + cmd
    os.chdir(FOREM)
    os.execvpe(cmd[0], cmd, env)


def cmd_list(a):
    for p in sorted(REG.glob("inst*.json")) if REG.exists() else []:
        if p.name.count(".") == 1:
            k = int(p.stem[4:])
            cmd_status(argparse.Namespace(inst=k))
    return 0


def cmd_residue(a):
    r = residue(a.inst)
    print(json.dumps(r))
    return 10 if r else 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="c", required=True)
    for n in ("start", "stop", "status", "env", "exec", "list", "residue"):
        s = sub.add_parser(n)
        if n != "list":
            s.add_argument("--inst", type=int, required=True)
        if n == "start":
            s.add_argument("--world", choices=("sim", "gazebo"), default="gazebo")
            s.add_argument("--run-id", required=True)
            s.add_argument("--cpus", default=None)
            s.add_argument("--timeout", type=float, default=240.0)
            s.add_argument("--launch-arg", action="append", default=[])
        if n == "env":
            s.add_argument("--format", choices=("sh", "json"), default="sh")
        if n == "exec":
            s.add_argument("--cpus", default=None)
            s.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    sys.exit({"start": cmd_start, "stop": cmd_stop, "status": cmd_status, "env": cmd_env, "exec": cmd_exec, "list": cmd_list,
              "residue": cmd_residue}[a.c](a))


if __name__ == "__main__":
    main()
