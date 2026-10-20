#!/usr/bin/env python3
"""task3.5 execution freeze (host side, stdlib + PyYAML).

  freeze_task3.py create --freeze-id ID [--instances RESULTS_JSON] [--receipt-runs a,b,...]
  freeze_task3.py verify                    exit 1 and list every difference if anything frozen changed
The result does not depend on the calling directory: --instances is a FoReM-root-relative path (or an absolute path inside FoReM) and is
stored FoReM-relative (T3-A03).

Freezes the hashes of: contracts/configs/patches/manifest, the assembled and imported source closure (forem/src/*), the Task3 scripts and
tests, container image id, catkin config, plus the fixed episode-instance file. Mutable docs are not frozen."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

FOREM = Path(__file__).resolve().parent.parent
OUT = FOREM / "config" / "task3" / "execution_freeze.json"
SKIP = {"__pycache__", ".pytest_cache"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def tree(rel):
    base = FOREM / rel
    out = {}
    paths = [base] if base.is_file() else [p for p in sorted(base.rglob("*")) if p.is_file()]
    for p in paths:
        if any(s in p.parts for s in SKIP) or p.suffix == ".pyc" or p.name == "execution_freeze.json":
            continue
        out[str(p.relative_to(FOREM))] = sha(p)
    return out


def instance_rel(path, forem=None):
    """Store/resolve the fixed episode-instance file relative to the FoReM root, never the caller's CWD (T3-A03).
    A relative argument is taken as FoReM-relative; an absolute one must lie inside FoReM after symlink resolution. The root `results`
    compatibility link (-> husky/results) therefore cannot take part: it resolves outside FoReM and is refused."""
    forem = Path(forem or FOREM).resolve()
    q = Path(path)
    q = (q if q.is_absolute() else forem / q).resolve()
    try:
        return q.relative_to(forem).as_posix()
    except ValueError:
        raise SystemExit("--instances %s resolves to %s, outside the FoReM root %s (the root results link points to husky/results)" % (path, q, forem))


def instance_path(stored, forem=None):
    """Absolute file for a stored task_instances path: FoReM-relative (current freezes) or absolute (legacy format), never CWD-relative."""
    forem = Path(forem or FOREM)
    q = Path(stored)
    return q if q.is_absolute() else forem / q


def instance_diffs(d, forem=None):
    ti = d.get("task_instances")
    if not ti:
        return []
    forem = Path(forem or FOREM)
    p = instance_path(ti["path"], forem)
    if not Path(ti["path"]).is_absolute() and forem.resolve() not in p.resolve().parents:
        return [("changed", "task_instances (path leaves the FoReM root)")]
    return [] if p.exists() and sha(p) == ti["sha256"] else [("changed", "task_instances")]


def scripts_list():
    names = ["task3_*.py", "check_task3_*.py", "validate_task3_core.py", "audit_task3_core.py", "audit_husky_branches.py", "regress_task3_lifecycle.py",
             "collect_task3_instances.py", "freeze_task3.py", "run_task3_core.sh", "task0_proc.py", "task0_manifest.py"]
    s = set()
    for n in names:
        s.update(p.name for p in (FOREM / "scripts").glob(n))
    return sorted("scripts/" + x for x in s)


def collect():
    files = {}
    for rel in ["config/task3", "src/forem_husky", "src/modulation_rl", "src/husky_ur5", "src/husky_description", "src/husky_control", "src/bio_ik",
                "src/robotiq_85_description", "src/robotiq_85_moveit_config", "src/roboticsgroup_upatras_gazebo_plugins", "src/forem_sim",
                "docker/run.sh", "docker/forem-entrypoint.sh", ".catkin_tools/profiles/default/config.yaml"] + scripts_list() + \
               ["tests/" + p.name for p in sorted((FOREM / "tests").glob("test_task3_*.py"))]:
        files.update(tree(rel))
    return files


def env_facts():
    def sh(c):
        # docker needs the docker group: go through `sg docker` so the facts do not depend on the calling shell's groups
        return subprocess.run(["sg", "docker", "-c", c], capture_output=True, text=True).stdout.strip()
    return dict(image_id=sh("docker inspect forem-dev --format '{{.Image}}'"),
                container_mounts="; ".join(sorted(x for x in sh("docker inspect forem-dev --format '{{range .Mounts}}{{.Source}}->{{.Destination}} rw={{.RW}}\n{{end}}'").splitlines() if x)),   # docker lists mounts in varying order
                gazebo=sh("bash %s/docker/run.sh exec gazebo --version 2>&1 | head -1" % FOREM),
                python=sh("bash %s/docker/run.sh exec python3 --version" % FOREM))


def cmd_create(a):
    d = dict(schema=1, freeze_id=a.freeze_id, created=__import__("datetime").datetime.now().astimezone().isoformat(),
             environment=env_facts(), files=collect(),
             cli=dict(run="sg docker -c 'bash forem/scripts/run_task3_core.sh [--launch-arg K:=V]... RUN_ID -- CHECK_CMD...'",
                      integration="... run_task3_core.sh RUN_ID -- python3 scripts/validate_task3_core.py --run-id RUN_ID",
                      sac="python3 scripts/task3_sac_entry.py --mode smoke|train|eval --run-id ID [--steps N --max-wall-s S] [--checkpoint P] (inside the launched container)"),
             task_instances=None, receipt_runs=[x for x in (a.receipt_runs or "").split(",") if x])
    if a.instances:
        rel = instance_rel(a.instances)
        d["task_instances"] = dict(path=rel, sha256=sha(instance_path(rel)))
    OUT.write_text(json.dumps(d, indent=1), encoding="utf-8")
    print("frozen", len(d["files"]), "files ->", OUT)
    return 0


def cmd_verify(a):
    d = json.loads(OUT.read_text(encoding="utf-8"))
    cur = collect()
    diffs = [("changed", k) for k, v in d["files"].items() if k in cur and cur[k] != v]
    diffs += [("missing", k) for k in d["files"] if k not in cur]
    diffs += [("added", k) for k in cur if k not in d["files"]]
    diffs += instance_diffs(d)
    env = env_facts()
    for k in ("image_id", "container_mounts"):
        if env[k] != d["environment"][k]:
            diffs.append(("changed", "environment." + k))
    for t, k in diffs[:60]:
        print(t, k)
    print("FREEZE OK" if not diffs else "FREEZE DIFFERS (%d)" % len(diffs), d["freeze_id"])
    return 0 if not diffs else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="c", required=True)
    c = sub.add_parser("create")
    c.add_argument("--freeze-id", required=True)
    c.add_argument("--instances")
    c.add_argument("--receipt-runs")
    sub.add_parser("verify")
    a = ap.parse_args()
    sys.exit(cmd_create(a) if a.c == "create" else cmd_verify(a))
