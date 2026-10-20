#!/usr/bin/env python3
"""Task1.3 matrix driver (host): runs the frozen matrix through run_task1_baseline.sh, one fresh sim per run, sequentially.

Order: round 1..R, each round executes the cases of baseline.yaml `matrix.order`; afterwards the hf diagnostics (H, M3).
A run that fails (non-zero exit) is KEPT; it is retried once with a new run-id (attempt 2); more than one retry or exit
codes 10/11/12/13/15 (foreign process, lock, refusal, launch/cleanup problems) stop the whole matrix for a human look.
Writes results/task1/<matrix-id>/run_index.json after every run (resumable: existing run-ids are never reused).
Usage: python3 forem/scripts/run_task1_matrix.py --matrix-id t1.3-m1 --freeze-id t1.1-freeze1 [--only-hf] [--rounds N]
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ENTRY = "bash %s/scripts/run_task1_baseline.sh" % ROOT
SAFE = {"P+": "Pp", "P-": "Pm", "L+": "Lp", "L-": "Lm"}
STOP_CODES = {10, 11, 12, 13, 15}


def sha(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def describe(rid, case, role, rnd, attempt, retry_of, rc):
    d = os.path.join(ROOT, "results", "task1", rid)
    man = load(os.path.join(d, "manifest.json")) or {}
    met = load(os.path.join(d, "run_metrics.json")) or {}
    hf_ok = True
    if role == "hf_diagnostic":
        hf_ok = man.get("hf_eval_exit") == 0
    stages = [man.get(k) for k in ("collect_exit", "convert_exit", "analyze_exit", "cleanup_exit")]
    valid = bool(rc == 0 and all(s == 0 for s in stages) and met.get("pass") is True and hf_ok and man.get("final_exit") == 0)
    return {"run_id": rid, "case": case, "role": role, "round": rnd, "attempt": attempt, "retry_of": retry_of, "entry_exit": rc,
            "final_exit": man.get("final_exit"), "stage_exits": dict(zip(("collect", "convert", "analyze", "cleanup"), stages)), "hf_eval_exit": man.get("hf_eval_exit"),
            "valid": valid, "failed_gates": met.get("failed_gates"), "invalid_reasons": met.get("invalid_reasons"),
            "sha256": {"manifest": sha(os.path.join(d, "manifest.json")), "run_metrics": sha(os.path.join(d, "run_metrics.json")),
                       "commands": sha(os.path.join(d, "commands.json")), "bag": sha(os.path.join(d, "run.bag")),
                       "curves": sha(os.path.join(d, "curves.npz"))},
            "results_dir": "results/task1/" + rid, "logs_dir": "logs/task1/" + rid}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-id", required=True)
    ap.add_argument("--freeze-id", required=True)
    ap.add_argument("--rounds", type=int, default=None)
    ap.add_argument("--only-hf", action="store_true")
    ap.add_argument("--skip-hf", action="store_true")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config", "experiments", "task1", "baseline.yaml")))
    rounds = a.rounds or cfg["matrix"]["rounds"]
    plan = []
    if not a.only_hf:
        for r in range(1, rounds + 1):
            for c in cfg["matrix"]["order"]:
                plan.append((c, "formal", r))
    if not a.skip_hf:
        for c in cfg["matrix"]["hf_diagnostic"]:
            plan.append((c, "hf_diagnostic", None))
    out = os.path.join(ROOT, "results", "task1", a.matrix_id)
    os.makedirs(out, exist_ok=True)
    idx_path = os.path.join(out, "run_index.json")
    index = load(idx_path) or {"matrix_id": a.matrix_id, "freeze_id": a.freeze_id, "plan": [list(p) for p in plan], "runs": [],
                               "agent_model": os.environ.get("T1_AGENT_MODEL", "unknown")}

    def save(status):
        index["status"] = status
        index["updated"] = time.strftime("%F %T %z")
        tmp = idx_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(index, f, indent=1)
        os.replace(tmp, idx_path)

    done = {(r["case"], r["role"], r["round"]) for r in index["runs"] if r["valid"]}
    for case, role, rnd in plan:
        if (case, role, rnd) in done:
            continue
        prev = None
        for attempt in (1, 2):
            tag = "r%d" % rnd if rnd else "hf"
            rid = "task1.3-%s-%s-%s-a%d" % (SAFE.get(case, case), tag, time.strftime("%m%d%H%M%S"), attempt)
            cmd = "%s %s--freeze-id %s %s %s" % (ENTRY, "--hf " if role == "hf_diagnostic" else "", a.freeze_id, case, rid)
            print("%s RUN %s (%s round=%s attempt=%d)" % (time.strftime("%T"), rid, case, rnd, attempt), flush=True)
            save("running " + rid)
            t0 = time.time()
            rc = subprocess.run(["sg", "docker", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
            rec = describe(rid, case, role, rnd, attempt, prev, rc)
            rec["wall_s"] = round(time.time() - t0, 1)
            index["runs"].append(rec)
            print("%s   exit=%d valid=%s failed_gates=%s wall=%.0fs" % (time.strftime("%T"), rc, rec["valid"], rec["failed_gates"], rec["wall_s"]), flush=True)
            save("running")
            if rc in STOP_CODES:
                save("stopped: exit %d on %s needs a human look" % (rc, rid))
                print("STOP: exit %d" % rc, flush=True)
                sys.exit(rc)
            if rec["valid"]:
                break
            prev = rid
        else:
            save("stopped: %s/%s round %s invalid after retry" % (case, role, rnd))
            print("STOP: invalid after retry", flush=True)
            sys.exit(1)
    save("complete")
    n_ok = sum(1 for r in index["runs"] if r["valid"])
    print("COMPLETE: %d valid runs of %d attempts" % (n_ok, len(index["runs"])), flush=True)


if __name__ == "__main__":
    main()
