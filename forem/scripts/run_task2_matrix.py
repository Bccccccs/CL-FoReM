#!/usr/bin/env python3
"""Task2 matrix driver (host): runs a stage of the frozen matrix through run_task2_delay.sh, one fresh sim per run, strictly sequentially.

  python3 forem/scripts/run_task2_matrix.py --matrix-id ID --freeze-id FID --stage pilot|formal|hf [--limit N] [--dry-run]

stage pilot  (task2.3 engineering, results/task2, protocol or execution freeze): M3/M6/MR3 x {B,Z} x 3 rounds (18), H x {B,Z} once (2),
             M3 x {D80,D160} once (2) = 22 runs. Not formal data.
stage formal (exp2.1, needs an EXECUTION freeze, results/experiment/exp2): {H,M3,M6,MR3} x {B,Z,D80,D160} x 3 rounds = 48 runs; order per round
             and condition exactly as frozen in fixed_delay.yaml (case order H,M3,M6,MR3; condition order by round).
stage hf     (exp2.1, execution freeze): M3-B and M3-D160 once each with the 2000 Hz config, reported separately.
Failure policy (exp2.1 section 3): every invalid or non-zero run is KEPT. Only a launch/startup failure (exit 13/14, infrastructure) is retried once with a
new run-id; anything else - structural, clock, safety, gate or cleanup failure - stops the matrix at once for a human look. Scientific trends never
trigger a re-run. The run index (results/<area>/<matrix-id>/run_index.json) is rewritten after every run; a restart skips valid planned cells and never
reuses a run-id. This driver never changes delays, thresholds, orders or poses.
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
ENTRY = "bash %s/scripts/run_task2_delay.sh" % ROOT
CFG = os.path.join(ROOT, "config", "experiments", "exp2", "fixed_delay.yaml")
RETRY_CODES = {13, 14}


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


def build_plan(cfg, stage):
    conds = cfg["delay"]["conditions"]
    m = cfg["matrix"]
    plan = []
    if stage == "formal":
        for r in range(1, m["rounds"] + 1):
            for case in m["case_order"]:
                for c in m["condition_order_by_round"][r]:
                    plan.append({"case": case, "condition": c, "round": r, "role": "formal", "hf": False})
    elif stage == "pilot":
        for r in range(1, m["rounds"] + 1):
            for case in ("M3", "M6", "MR3"):
                for c in [x for x in m["condition_order_by_round"][r] if x in ("B", "Z")]:
                    plan.append({"case": case, "condition": c, "round": r, "role": "pilot", "hf": False})
        for c in ("B", "Z"):
            plan.append({"case": "H", "condition": c, "round": 1, "role": "pilot", "hf": False})
        for c in ("D80", "D160"):
            plan.append({"case": "M3", "condition": c, "round": 1, "role": "pilot", "hf": False})
    elif stage == "hf":
        for case, c in m["hf_diagnostic"]:
            plan.append({"case": case, "condition": c, "round": None, "role": "hf_diagnostic", "hf": True})
    else:
        raise SystemExit("unknown stage %s" % stage)
    for p in plan:
        p["mode"], p["tau_ms"] = conds[p["condition"]]["mode"], conds[p["condition"]]["tau_ms"]
    return plan


def describe(rid, cell, area, attempt, retry_of, rc):
    d = os.path.join(ROOT, "results", area, rid)
    man = load(os.path.join(d, "manifest.json")) or {}
    met = load(os.path.join(d, "run_metrics.json")) or {}
    stages = [man.get(k) for k in ("collect_exit", "convert_exit", "analyze_exit", "cleanup_exit")]
    if cell["mode"] == "queue":
        stages.append(man.get("delay_exit"))
    hf_ok = (man.get("hf_eval_exit") == 0) if cell["hf"] else True
    valid = bool(rc == 0 and all(s == 0 for s in stages) and met.get("pass") is True and hf_ok and man.get("final_exit") == 0)
    return dict(cell, run_id=rid, attempt=attempt, retry_of=retry_of, entry_exit=rc, final_exit=man.get("final_exit"),
                stage_exits={k: man.get(k) for k in ("collect_exit", "delay_exit", "convert_exit", "analyze_exit", "cleanup_exit", "hf_eval_exit")},
                valid=valid, failed_gates=met.get("failed_gates"), invalid_reasons=met.get("invalid_reasons"),
                sha256={"manifest": sha(os.path.join(d, "manifest.json")), "run_metrics": sha(os.path.join(d, "run_metrics.json")), "commands": sha(os.path.join(d, "commands.json")),
                        "bag": sha(os.path.join(d, "run.bag")), "curves": sha(os.path.join(d, "curves.npz")), "events": sha(os.path.join(d, "delay_events.jsonl"))},
                results_dir="results/%s/%s" % (area, rid), logs_dir="logs/%s/%s" % (area, rid))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-id", required=True)
    ap.add_argument("--freeze-id", required=True)
    ap.add_argument("--stage", required=True, choices=["pilot", "formal", "hf"])
    ap.add_argument("--limit", type=int, default=None, help="run at most N cells this invocation (for supervised stepping)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--retry-invalid", default=None, metavar="RUN_ID",
                    help="explicit decision to re-run the cell of this invalid attempt ONCE with a new run-id (attempt 2, retry_of recorded); "
                         "never used for scientific reasons, only for an infrastructure-caused invalid run documented in the RESULTS")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(CFG))
    plan = build_plan(cfg, a.stage)
    exp = a.stage in ("formal", "hf")
    area = "experiment/exp2" if exp else "task2"
    prefix = "exp2.1" if exp else "task2.3-pilot"
    if a.dry_run:
        for i, p in enumerate(plan, 1):
            print(i, p)
        print(len(plan), "runs")
        return
    out = os.path.join(ROOT, "results", area, a.matrix_id)
    os.makedirs(out, exist_ok=True)
    idx_path = os.path.join(out, "run_index.json")
    index = load(idx_path) or {"matrix_id": a.matrix_id, "freeze_id": a.freeze_id, "stage": a.stage, "plan": plan, "runs": [],
                               "agent_model": os.environ.get("T2_AGENT_MODEL", "unknown"), "experiment": "exp2.1" if exp else None}
    if index["freeze_id"] != a.freeze_id or index["stage"] != a.stage:
        raise SystemExit("refused: existing index belongs to another freeze/stage")

    def save(status):
        index["status"], index["updated"] = status, time.strftime("%F %T %z")
        tmp = idx_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(index, f, indent=1)
        os.replace(tmp, idx_path)

    key = lambda c: (c["case"], c["condition"], c["round"], c["role"])
    done = {key(r) for r in index["runs"] if r["valid"]}
    ran = 0
    for cell in plan:
        if key(cell) in done:
            continue
        failed_before = [r for r in index["runs"] if key(r) == key(cell) and not r["valid"]]
        first_attempt, prev0 = 1, None
        if failed_before:
            tgt = [r for r in failed_before if r["run_id"] == a.retry_invalid]
            if len(failed_before) >= 2 or not tgt:
                save("stopped: cell %s has %d invalid attempt(s); a further run needs an explicit decision" % (key(cell), len(failed_before)))
                print("STOP: cell %s already has %d invalid attempt(s); only one explicit --retry-invalid RUN_ID retry is allowed per cell" % (key(cell), len(failed_before)), flush=True)
                sys.exit(1)
            first_attempt, prev0 = 2, tgt[0]["run_id"]
        if a.limit is not None and ran >= a.limit:
            save("paused after --limit")
            return
        prev = prev0
        for attempt in range(first_attempt, 3):
            tag = ("r%d" % cell["round"]) if cell["round"] else "hf"
            rid = "%s-%s-%s-%s-%s" % (prefix, cell["case"], cell["condition"], tag, time.strftime("%m%d%H%M%S"))
            if attempt > 1:
                rid += "-a%d" % attempt
            cmd = "%s %s%s--freeze-id %s --mode %s --delay-ms %s --case %s --run-id %s" % (
                ENTRY, "--hf " if cell["hf"] else "", "--experiment exp2.1 " if exp else "", a.freeze_id, cell["mode"], cell["tau_ms"], cell["case"], rid)
            print("%s RUN %s (%s %s round=%s attempt=%d)" % (time.strftime("%T"), rid, cell["case"], cell["condition"], cell["round"], attempt), flush=True)
            save("running " + rid)
            t0 = time.time()
            rc = subprocess.run(["sg", "docker", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
            rec = describe(rid, cell, area, attempt, prev, rc)
            rec["wall_s"] = round(time.time() - t0, 1)
            index["runs"].append(rec)
            ran += 1
            print("%s   exit=%d valid=%s failed_gates=%s wall=%.0fs" % (time.strftime("%T"), rc, rec["valid"], rec["failed_gates"], rec["wall_s"]), flush=True)
            save("running")
            if rec["valid"]:
                break
            if rc in RETRY_CODES and attempt == 1:   # (a retry is only automatic for launch/startup failures, and only from attempt 1)
                prev = rid
                continue
            save("stopped: %s invalid (exit %d); structural/clock/safety/gate failures stop the matrix for a human look" % (rid, rc))
            print("STOP: %s invalid exit=%d" % (rid, rc), flush=True)
            sys.exit(1 if rc == 0 else rc)
        else:
            save("stopped: infrastructure failure repeated for %s" % rid)
            print("STOP: infrastructure failure repeated", flush=True)
            sys.exit(1)
    save("complete")
    print("COMPLETE: %d valid of %d attempts" % (sum(1 for r in index["runs"] if r["valid"]), len(index["runs"])), flush=True)


if __name__ == "__main__":
    main()
