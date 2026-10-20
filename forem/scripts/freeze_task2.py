#!/usr/bin/env python3
"""Task2 protocol / execution freeze (host; stdlib + PyYAML; no ROS).

  freeze_task2.py create --freeze-id ID --stage protocol|execution [--agent-model TEXT] [--protocol-version exp2.1-v1.1]
        -> results/task2/ID/freeze.json (schema 2) + snapshots. Never overwrites an existing ID (exit 12).
  freeze_task2.py verify --freeze-id ID [--need execution]
        -> exit 0 if every frozen file still matches its recorded hash, 1 with the list of differences, 2 if ID/stage unusable.
  freeze_task2.py audit  --freeze-id ID
        -> integrity of the freeze's OWN snapshots and an informational drift report of the live tree; exit 0 iff the snapshots are intact
           (works for the historical schema-1 freezes t2.1-protocol1 / t2.3-exec1, which `verify` rightly still rejects).

Schema 2 (task2.6, T2-A03) separates what must never change from progress prose:
  * IMMUTABLE and strictly hashed: the seven Task1 files, fixed_delay.yaml, the exp2.1 PROCEDURE.md (the protocol text, including its amendments),
    and - in the execution stage - every acquisition-side source (queue, proxy, sender, converter, per-run analysis, entry, freeze tool, shared libs).
  * MUTABLE STATUS TEXT: in exp2.1 TASK.md a line among the first six that starts with "状态：" or "定位：" (the progress/status statement) is excluded from its hash; every other
    line of that file (goal, scope, acceptance) is still hashed, so a real change of the protocol statement is rejected exactly as before.
    RESULTS.md files, PROGRESS and the task documents are not part of any freeze (they are progress records).
Schema 1 (t2.1-protocol1, t2.3-exec1) hashed TASK.md in full; that is why updating its status line made them fail. They are kept unchanged as historical records.
Stage "protocol": the frozen Task1 files, the protocol documents and fixed_delay.yaml (and its agreement with the Task1 config) are fixed.
Stage "execution": additionally every acquisition-side Task2 source. Aggregation/analysis of many runs (aggregate_task2.py) may be re-run under a newer analysis id.
Exit codes: 0 ok; 1 verification found differences / a pre-registration check failed; 2 bad request (id/stage); 12 id exists.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CONFIG = "config/experiments/exp2/fixed_delay.yaml"
TASK1_YAML = "config/experiments/task1/baseline.yaml"
TASK1_FREEZE = "t1.1-freeze1"
PROC_DOC = "doc/experiment/备选/exp2/exp2.1/PROCEDURE.md"
TASK_DOC = "doc/experiment/备选/exp2/exp2.1/TASK.md"
PROTOCOL_DOCS = [PROC_DOC, TASK_DOC]                       # schema 1 list (both hashed in full)
PROTOCOL_DOC_MODES = {PROC_DOC: "strict", TASK_DOC: "status_line_excluded"}   # schema 2
STATUS_LINE_RE = re.compile(r"^(状态|定位)：")
STATUS_LINE_WINDOW = 6          # only a matching line among the FIRST six lines is the status line; the same prefix further down is ordinary (hashed) text
DEFAULT_PROTOCOL_VERSION = "exp2.1-v1.1"
# the seven Task1 frozen files, same keys/paths as run_task1_baseline.sh
TASK1_SEVEN = {"world": "src/forem_sim/worlds/ur5_empty.world", "launch": "src/forem_sim/launch/ur5_sim.launch",
               "urdf_xacro": "src/forem_sim/urdf/ur5_fixed.urdf.xacro", "controllers_normal": "config/control/ur5_controllers.yaml",
               "controllers_hf2000": "config/diagnostics/task0.7/ur5_controllers_hf2000.yaml",
               "start_controllers": "src/forem_sim/scripts/start_controllers.py", "baseline_yaml": TASK1_YAML}
ACQUISITION = ["scripts/task2_delay_queue.py", "scripts/task2_delay_node.py", "scripts/collect_task2.py", "scripts/task2_bag_to_csv.py",
               "scripts/analyze_task2.py", "scripts/run_task2_delay.sh", "scripts/freeze_task2.py",
               "scripts/task1_lib.py", "scripts/analyze_task1.py", "scripts/task1_freeze.py", "scripts/task0_proc.py", "scripts/task0_manifest.py",
               "scripts/evaluate_hf_windows.py", "scripts/analyze_task0_feedback.py", "docker/run.sh", "docker/forem-entrypoint.sh"]
CASES_COPIED = ["H", "M3", "M6", "MR3"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def doc_hash(path, mode):
    """strict: sha256 of the file bytes. status_line_excluded: sha256 of the text with every line matching ^(状态|定位)： removed (the mutable progress line)."""
    if mode == "strict":
        return sha256(path)
    if mode == "status_line_excluded":
        with open(path, encoding="utf-8") as f:
            kept = [ln for i, ln in enumerate(f.read().split("\n")) if not (i < STATUS_LINE_WINDOW and STATUS_LINE_RE.match(ln))]
        return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest()
    raise ValueError("unknown doc hash mode %r" % mode)


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip()


def preregistration_checks(cfg, t1):
    """Pre-registered facts that must hold before any run: copy-equality with Task1 and a well-formed matrix. Returns (problems, n_formal)."""
    bad = []
    for key in ("robot", "timing", "trajectory", "quality"):
        if cfg[key] != t1[key]:
            bad.append("config section '%s' differs from the Task1 frozen config" % key)
    for c in CASES_COPIED:
        if cfg["cases"].get(c) != t1["cases"].get(c):
            bad.append("case %s differs from Task1" % c)
    if set(cfg["cases"]) != set(CASES_COPIED):
        bad.append("cases must be exactly %s" % CASES_COPIED)
    d = cfg["delay"]
    allowed = d["allowed_tau_ms"]
    for cid, cond in d["conditions"].items():
        if cond["mode"] not in ("bypass", "queue"):
            bad.append("condition %s: bad mode" % cid)
        if cond["tau_ms"] not in allowed:
            bad.append("condition %s: tau %s not in allowed %s" % (cid, cond["tau_ms"], allowed))
        if cond["mode"] == "bypass" and cond["tau_ms"] != 0:
            bad.append("condition %s: bypass with non-zero tau" % cid)
    if sorted(d["conditions"]) != ["B", "D160", "D80", "Z"]:
        bad.append("conditions must be B, Z, D80, D160")
    m = cfg["matrix"]
    for r in range(1, m["rounds"] + 1):
        if sorted(m["condition_order_by_round"].get(r, [])) != sorted(d["conditions"]):
            bad.append("round %d order is not a permutation of the conditions" % r)
    n_formal = len(m["case_order"]) * len(d["conditions"]) * m["rounds"]
    if n_formal != 48:
        bad.append("formal matrix has %d runs, protocol says 48" % n_formal)
    if len(m["hf_diagnostic"]) != 2:
        bad.append("protocol has exactly 2 hf diagnostic runs")
    return bad, n_formal


def file_table(root, rel_list):
    return {rel: sha256(os.path.join(root, rel)) for rel in rel_list}


def create_freeze(root, freeze_id, stage, agent_model="unknown", protocol_version=DEFAULT_PROTOCOL_VERSION, take_environment=True):
    """Returns (rc, message_or_path). Writes root/results/task2/<id>/freeze.json (schema 2) and snapshots."""
    d = os.path.join(root, "results", "task2", freeze_id)
    if not freeze_id or os.path.exists(d):
        return 12, "refused: freeze id missing or results/task2/%s already exists" % freeze_id
    cfg = yaml.safe_load(open(os.path.join(root, CONFIG)))
    t1 = yaml.safe_load(open(os.path.join(root, TASK1_YAML)))
    base = json.load(open(os.path.join(root, "results", "task1", TASK1_FREEZE, "baseline.json")))
    problems, n_formal = preregistration_checks(cfg, t1)
    seven = file_table(root, TASK1_SEVEN.values())
    seven_by_key = {k: seven[v] for k, v in TASK1_SEVEN.items()}
    if seven_by_key != base["file_sha256"]:
        problems.append("Task1 seven frozen files differ from results/task1/%s/baseline.json: %s" % (
            TASK1_FREEZE, [k for k in seven_by_key if seven_by_key[k] != base["file_sha256"].get(k)]))
    missing_docs = [p for p in PROTOCOL_DOCS if not os.path.exists(os.path.join(root, p))]
    if missing_docs:
        problems.append("protocol documents missing: %s" % missing_docs)
    elif ("protocol-version: %s" % protocol_version) not in open(os.path.join(root, PROC_DOC), encoding="utf-8").read():
        problems.append("the protocol PROCEDURE.md does not declare 'protocol-version: %s'" % protocol_version)
    files = {"task1_seven": seven_by_key, "config": {CONFIG: sha256(os.path.join(root, CONFIG))}}
    if not missing_docs:
        files["protocol_docs"] = {p: {"mode": PROTOCOL_DOC_MODES[p], "sha256": doc_hash(os.path.join(root, p), PROTOCOL_DOC_MODES[p])} for p in PROTOCOL_DOCS}
    if stage == "execution":
        miss = [f for f in ACQUISITION if not os.path.exists(os.path.join(root, f))]
        if miss:
            problems.append("acquisition files missing: %s" % miss)
        else:
            files["acquisition"] = file_table(root, ACQUISITION)
            sys.path.insert(0, os.path.join(root, "scripts"))
            from task0_manifest import hash_sources
            files["all_sources_sha256"] = hash_sources(root)   # includes tests and aggregate scripts, for the audit trail
    if problems:
        return 1, "FREEZE REFUSED:\n  " + "\n  ".join(problems)
    st = sh("git -C %s status --short -- ." % root).splitlines() if take_environment else []
    out = {
        "schema": "task2-freeze/2", "freeze_id": freeze_id, "stage": stage, "protocol_version": protocol_version,
        "created": datetime.datetime.now().astimezone().isoformat(), "agent_model": agent_model,
        "protocol": cfg["protocol"], "task1_freeze_id": TASK1_FREEZE, "task1_analysis_reference": "results/task1/t1.9-a3 (analysis task1.9-1)",
        "mutable_status_rule": {"doc": TASK_DOC, "excluded_line_regex": STATUS_LINE_RE.pattern, "only_within_first_lines": STATUS_LINE_WINDOW,
                                "meaning": "progress/status prose may change without a new freeze; every other line of the protocol documents is hashed",
                                "strict_docs": [p for p, m in PROTOCOL_DOC_MODES.items() if m == "strict"]},
        "supersedes_historical": ["t2.1-protocol1", "t2.3-exec1"],
        "matrix": {"formal_runs": n_formal, "hf_runs": len(cfg["matrix"]["hf_diagnostic"]), "case_order": cfg["matrix"]["case_order"],
                   "condition_order_by_round": cfg["matrix"]["condition_order_by_round"], "hf_diagnostic": cfg["matrix"]["hf_diagnostic"]},
        "frozen_config": cfg, "files": files,
        "pre_registered_gates": cfg["gates"], "eps_max_ms": cfg["delay"]["eps_max_ms"],
        "message_support": cfg["delay"]["supported_message"], "queue_capacity": cfg["delay"]["queue_capacity"],
        "time_quantisation": cfg["delay"]["time_quantisation"],
        "git_head": sh("git -C %s rev-parse HEAD" % root) if take_environment else None, "git_forem_status_lines": len(st),
        "git_forem_status_sha256": hashlib.sha256("\n".join(sorted(st)).encode()).hexdigest(),
        "image_id": sh("docker inspect forem-dev --format '{{.Image}}'") if take_environment else None,
        "container_id": sh("docker inspect forem-dev --format '{{.Id}}'") if take_environment else None,
        "versions": sh("bash %s/docker/run.sh exec bash -c 'echo ROS=$(rosversion -d) $(gazebo --version 2>&1 | sed -n 1p) py=$(python3 --version 2>&1) "
                       "numpy=$(python3 -c \"import numpy;print(numpy.__version__)\")'" % root) if take_environment else None,
        "note": ("protocol stage: protocol and Task1 baseline frozen; no acquisition sources hashed" if stage == "protocol"
                 else "execution stage: acquisition sources frozen; analysis of many runs (aggregate_task2.py) may be re-run under a newer analysis id"),
    }
    os.makedirs(d)
    with open(os.path.join(d, "freeze.json"), "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    for rel in [CONFIG] + PROTOCOL_DOCS:
        with open(os.path.join(d, "snapshot_" + os.path.basename(rel)), "wb") as f:
            f.write(open(os.path.join(root, rel), "rb").read())
    return 0, os.path.join(d, "freeze.json")


def _live_path(root, group, rel):
    return os.path.join(root, TASK1_SEVEN.get(rel, rel) if group == "task1_seven" else rel)


def freeze_diffs(root, fz):
    """Paths whose live content no longer matches the freeze record."""
    diffs = []
    for group, table in fz["files"].items():
        if group == "all_sources_sha256":
            continue
        for rel, h in table.items():
            full = _live_path(root, group, rel)
            if group == "protocol_docs" and isinstance(h, dict):          # schema 2: (mode, hash)
                ok = os.path.exists(full) and doc_hash(full, h["mode"]) == h["sha256"]
            else:                                                         # schema 1 docs and all other files: full-file hash
                ok = os.path.exists(full) and sha256(full) == h
            if not ok:
                diffs.append(rel if group != "task1_seven" else TASK1_SEVEN.get(rel, rel))
    return diffs


def verify_freeze(root, freeze_id, need="protocol"):
    """Returns (rc, message). 0 ok, 1 files changed, 2 unusable id/stage."""
    p = os.path.join(root, "results", "task2", freeze_id or "none", "freeze.json")
    if not freeze_id or not os.path.isfile(p):
        return 2, "freeze %s not found (results/task2/<id>/freeze.json)" % freeze_id
    fz = json.load(open(p))
    if need == "execution" and fz.get("stage") != "execution":
        return 2, "freeze %s is stage %s; an execution freeze is required" % (freeze_id, fz.get("stage"))
    diffs = freeze_diffs(root, fz)
    if diffs:
        return 1, "frozen files changed since %s: %s" % (freeze_id, diffs)
    return 0, json.dumps({"freeze_id": freeze_id, "stage": fz["stage"], "schema": fz.get("schema"), "ok": True})


def audit_freeze(root, freeze_id):
    """Integrity of a freeze's own snapshots + informational drift of the live tree. Returns (rc, report dict)."""
    d = os.path.join(root, "results", "task2", freeze_id)
    fz = json.load(open(os.path.join(d, "freeze.json")))
    rep = {"freeze_id": freeze_id, "schema": fz.get("schema"), "stage": fz.get("stage"), "snapshot_problems": [], "live_drift": [], "live_drift_only_status_lines": None}
    for rel, entry in fz["files"].get("protocol_docs", {}).items():
        snap = os.path.join(d, "snapshot_" + os.path.basename(rel))
        mode = entry["mode"] if isinstance(entry, dict) else "strict"
        want = entry["sha256"] if isinstance(entry, dict) else entry
        if not os.path.exists(snap) or doc_hash(snap, mode) != want:
            rep["snapshot_problems"].append(rel)
    for rel, want in fz["files"].get("config", {}).items():
        snap = os.path.join(d, "snapshot_" + os.path.basename(rel))
        if not os.path.exists(snap) or sha256(snap) != want:
            rep["snapshot_problems"].append(rel)
    rep["live_drift"] = freeze_diffs(root, fz)
    # is the only difference to the snapshots the status line(s) of the protocol task document?
    live = os.path.join(root, TASK_DOC)
    snap = os.path.join(d, "snapshot_TASK.md")
    if os.path.exists(live) and os.path.exists(snap):
        rep["task_doc_full_hash_equal"] = sha256(live) == sha256(snap)
        rep["task_doc_equal_ignoring_status_lines"] = doc_hash(live, "status_line_excluded") == doc_hash(snap, "status_line_excluded")
        rep["live_drift_only_status_lines"] = bool(rep["live_drift"] == [TASK_DOC] and rep["task_doc_equal_ignoring_status_lines"]) if rep["live_drift"] else None
    return (0 if not rep["snapshot_problems"] else 1), rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT, help=argparse.SUPPRESS)       # tests only
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--freeze-id", required=True)
    c.add_argument("--stage", choices=["protocol", "execution"], required=True)
    c.add_argument("--agent-model", default="unknown")
    c.add_argument("--protocol-version", default=DEFAULT_PROTOCOL_VERSION)
    v = sub.add_parser("verify")
    v.add_argument("--freeze-id", required=True)
    v.add_argument("--need", choices=["protocol", "execution"], default="protocol")
    u = sub.add_parser("audit")
    u.add_argument("--freeze-id", required=True)
    a = ap.parse_args()
    if a.cmd == "create":
        rc, msg = create_freeze(a.root, a.freeze_id, a.stage, a.agent_model, a.protocol_version)
        if rc:
            print(msg, file=sys.stderr)
            sys.exit(rc)
        print(json.dumps({"freeze": msg, "stage": a.stage, "protocol_version": a.protocol_version}))
    elif a.cmd == "verify":
        rc, msg = verify_freeze(a.root, a.freeze_id, a.need)
        print(msg, file=sys.stderr if rc else sys.stdout)
        sys.exit(rc)
    else:
        rc, rep = audit_freeze(a.root, a.freeze_id)
        print(json.dumps(rep, indent=1, ensure_ascii=False))
        sys.exit(rc)


if __name__ == "__main__":
    main()
