#!/usr/bin/env python3
"""Write results/task0/<run>/manifest.json for a smoke run (host side, stdlib only).

Records identity of everything that could change behaviour: hashes of *all* executable
sources/configs of the forem workspace (not just a dirty-file count), image, container,
mounts, exact commands and the outcome of launch / check / cleanup.
Usage: task0_manifest.py ROOT RUN_ID STATE_JSON   (STATE_JSON is written by run_task0_smoke.sh)
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys

SRC_GLOBS = ["src/forem_sim", "config", "docker/run.sh", "docker/forem-entrypoint.sh", "scripts", "tests"]
SKIP_DIRS = {"__pycache__", ".pytest_cache"}


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_sources(root):
    out = {}
    for rel in SRC_GLOBS:
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            out[rel] = sha(p)
        elif os.path.isdir(p):
            for d, dirs, files in os.walk(p):
                dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
                for fn in sorted(files):
                    if fn.endswith((".pyc", ".bag")):
                        continue
                    fp = os.path.join(d, fn)
                    out[os.path.relpath(fp, root)] = sha(fp)
    return out


def main():
    root, run, state_path = sys.argv[1:4]
    state = json.load(open(state_path))
    container = state.get("container", "forem-dev")
    m = {
        "run_id": run,
        "finished": datetime.datetime.now().astimezone().isoformat(),
        "git_head": sh("git -C %s rev-parse HEAD" % root),
        "git_forem_status_lines": sh("git -C %s status --short -- . | wc -l" % root),
        "source_sha256": hash_sources(root),
        "container": container,
        "image_id": sh("docker inspect %s --format '{{.Image}}'" % container),
        "container_mounts": sh("docker inspect %s --format '{{range .Mounts}}{{.Source}}->{{.Destination}} rw={{.RW}}; {{end}}'" % container),
        "versions": sh("bash %s/docker/run.sh exec bash -c 'echo ROS=$(rosversion -d) $(gazebo --version 2>&1 | sed -n 1p)'" % root),
        "error_injection": "none",
        "seed": "not applicable (no randomness introduced)",
    }
    m.update(state)
    dst = os.path.join(root, "results", "task0", run, "manifest.json")
    tmp = dst + ".tmp"
    json.dump(m, open(tmp, "w"), indent=2)
    os.replace(tmp, dst)
    print("manifest written:", dst)


if __name__ == "__main__":
    main()
