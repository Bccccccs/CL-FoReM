#!/usr/bin/env python3
"""Write results/task3/<run>/manifest.json for a Task3 core run (host side, stdlib only).

Same record as task0_manifest.py but hashes the Task3 source closure (forem/src of all imported/assembled
packages, config/task3, scripts, tests) and the contract/freeze files.
Usage: task3_manifest.py ROOT RUN_ID STATE_JSON
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task0_manifest as m0

m0.SRC_GLOBS = ["src", "config/task3", "docker/run.sh", "docker/forem-entrypoint.sh", "scripts", "tests"]
m0.SKIP_DIRS = {"__pycache__", ".pytest_cache", "forem_sim_dummy"}

if __name__ == "__main__":
    # task0_manifest.main() writes results/<task_dir>/<run>/manifest.json
    sys.argv = [sys.argv[0]] + sys.argv[1:4] + ["task3"]
    m0.main()
