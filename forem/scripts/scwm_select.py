#!/usr/bin/env python3
"""task4.11: validation-only checkpoint selection (rule of SRC0108, no test data):
 1. most physical successes on the validation episodes, 2. most completed (not capped) episodes with valid physical feedback,
 3. highest summed return, 4. earliest step.   python3 scripts/scwm_select.py RESULTS_DIR [--json]"""
import json, sys
from pathlib import Path


def score(rec):
    eps = rec["episodes"]
    phys = sum(bool(e.get("physical_success")) for e in eps)
    complete = sum((not e.get("capped")) and (e.get("physical") or {}).get("valid", False) for e in eps)
    ret = sum(float(e.get("return_", 0.0)) for e in eps)
    return (phys, complete, ret, -rec["step"])


def main():
    d = Path(sys.argv[1])
    recs = [json.loads(p.read_text()) for p in sorted(d.glob("validation_step*.json"))]
    if not recs:
        raise SystemExit("no validation records in %s" % d)
    best = max(recs, key=score)
    table = [dict(step=r["step"], physical_successes=score(r)[0], complete=score(r)[1], return_sum=round(score(r)[2], 3), n=r["n"]) for r in recs]
    out = dict(selected_step=best["step"], policy_file=str(d / "ckpt" / ("policy_step%08d.pt" % best["step"])), table=table)
    print(json.dumps(out, indent=1))
    if "--json" in sys.argv:
        (d / "selected_checkpoint.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
