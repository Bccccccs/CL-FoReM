#!/usr/bin/env python3
"""task3.5: assemble results/task3/<out>/core_receipt.json from the REAL run evidence (no re-computation of verdicts, no summarising away of
failed attempts). Host side; runs the unit tests (host-capable ones here, the full set inside forem-dev) and the static audit again.

  build_task3_receipt.py --out-id t3.5-receipt --int-run t3.5-int-r2 --life-report t3.5-life2 --instances-run t3.5-inst-r1 \
      --attempts t3.5-int-r1 t3.2-motion-r1 ...   (every attempt listed is copied into `all_attempts` with its exit code)"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

FOREM = Path(__file__).resolve().parent.parent


def sh(cmd, **kw):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(FOREM), **kw)
    return r.returncode, (r.stdout + r.stderr)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run_state(run):
    p = FOREM / "logs" / "task3" / run / "state.json"
    if not p.exists():
        return None
    s = json.loads(p.read_text())
    return dict(run=run, final_exit=s.get("final_exit"), check_exit=s.get("check_exit"), cleanup_exit=s.get("cleanup_exit"),
                interrupted=s.get("interrupted"), startup_ok=s.get("startup_ok"), command=s["commands"]["check"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-id", required=True)
    ap.add_argument("--int-run", required=True)
    ap.add_argument("--life-report", required=True)
    ap.add_argument("--instances-run", required=True)
    ap.add_argument("--attempts", nargs="*", default=[])
    a = ap.parse_args()
    out = dict(schema=1, receipt_id=a.out_id)
    m = json.loads((FOREM / "config/task3/source_manifest.json").read_text())
    out["source"] = dict(manifest_sha256=sha(FOREM / "config/task3/source_manifest.json"), counts=m["counts"], packages=[p["destination"] for p in m["packages"]])
    out["build"] = dict(logs=["logs/task3/t3.2-build3/catkin.log"], note="catkin build, Python3.10 cmake args; exit 0 recorded in the log summary line")
    rc, txt = sh("python3 scripts/audit_task3_core.py")
    out["static_audit"] = dict(exit=rc, output=txt.strip().splitlines()[-8:])
    rc, txt = sh("python3 -W ignore -m unittest tests.test_task3_source_contract tests.test_task3_semantics tests.test_task3_pose_bridge 2>&1 | tail -4")
    out["host_unit_tests"] = dict(exit=rc, tail=txt.strip().splitlines()[-3:])
    rc, txt = sh("sg docker -c \"bash docker/run.sh exec bash -c 'cd /root/mm_husky_ws && python3 -W ignore -m unittest discover -s tests -p \\\"test_task3_*.py\\\" 2>&1 | tail -4'\"")
    out["container_unit_tests_task3"] = dict(exit=rc, tail=txt.strip().splitlines()[-3:])
    ip = FOREM / "results/task3" / a.int_run / "integration_summary.json"
    out["integration"] = dict(run=a.int_run, state=run_state(a.int_run), summary=json.loads(ip.read_text()) if ip.exists() else None)
    lp = FOREM / "results/task3" / (a.life_report + "-report") / "report.json"
    out["lifecycle"] = json.loads(lp.read_text()) if lp.exists() else None
    ep = FOREM / "results/task3" / a.instances_run / "episode_instances.json"
    out["instances"] = dict(run=a.instances_run, path=str(ep.relative_to(FOREM)), sha256=sha(ep), state=run_state(a.instances_run)) if ep.exists() else None
    out["all_attempts"] = [run_state(r) or dict(run=r, note="no state.json (dev/diagnostic or not via wrapper)") for r in a.attempts]
    rc, txt = sh("python3 scripts/freeze_task3.py verify")
    out["freeze_verify"] = dict(exit=rc, output=txt.strip().splitlines()[-3:])
    ok = [out["static_audit"]["exit"] == 0, out["host_unit_tests"]["exit"] == 0, out["container_unit_tests_task3"]["exit"] == 0,
          bool(out["integration"]["summary"] and out["integration"]["summary"]["ok"]), bool(out["lifecycle"] and out["lifecycle"]["ok"]),
          bool(out["instances"]), out["freeze_verify"]["exit"] == 0]
    out["all_pass"] = all(ok)
    out["pass_flags"] = ok
    d = FOREM / "results/task3" / a.out_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "core_receipt.json").write_text(json.dumps(out, indent=1, default=str))
    print("receipt all_pass =", out["all_pass"], ok, "->", d / "core_receipt.json")
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
