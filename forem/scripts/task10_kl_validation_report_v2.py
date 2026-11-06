#!/usr/bin/env python3
"""CPU-only report adapter; preserve frozen evaluation code and original reports."""
import argparse
from pathlib import Path

import task10_kl_validation as frozen
import task10_validation_audit_v2 as audit


def report(run, workspace=frozen.ROOT, artifacts_root=Path('/reference/source')):
    # The frozen report passes its budget to both checks. The independent
    # snapshot checker has a three-argument interface and does not use a budget.
    original = audit.snapshot_checks

    def snapshot_checks(run, expected, rows, unused_budget):
        return original(run, expected, rows)

    audit.snapshot_checks = snapshot_checks
    try:
        result = frozen.report(run, workspace, artifacts_root)
    finally:
        audit.snapshot_checks = original
    result['report_adapter_sha256'] = frozen.sha256(Path(__file__))
    result['report_adapter'] = 'snapshot_checks: omit unused fourth budget argument; scoring and all checks unchanged'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, default=frozen.ROOT)
    parser.add_argument('--artifacts-root', type=Path, default=Path('/reference/source'))
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('new output required; preserve original reports')
    result = report(args.run.resolve(), args.workspace, args.artifacts_root)
    frozen.atomic_json(args.output, result)
    import json
    print(json.dumps({k: result[k] for k in ('status', 'issues', 'scores', 'paired', 'no_updates')}), flush=True)
    return int(bool(result['issues']))


if __name__ == '__main__':
    raise SystemExit(main())
