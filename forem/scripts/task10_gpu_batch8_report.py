#!/usr/bin/env python3
"""Read-only recomputation of this bounded verification and conditional estimate."""
import argparse
import hashlib
import json
from pathlib import Path
import math


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report(root):
    ledger = read(root/'measurement-ledger.json')
    gpu = read(root/'gpu-analysis.json', {})
    main = root/'batch8'
    summary = read(main/'training-summary.json', {})
    resumed = read(main/'resume-summary.json', {})
    budget = read(main/'training-budget.json', {})
    reference_budget = read(main/'continuous-reference/training-budget.json', {})
    batches = [json.loads(v) for v in (main/'batch-boundaries.jsonl').read_text().splitlines()] if (main/'batch-boundaries.jsonl').exists() else []
    reference_batches = [json.loads(v) for v in (main/'continuous-reference/batch-boundaries.jsonl').read_text().splitlines()] if (main/'continuous-reference/batch-boundaries.jsonl').exists() else []
    comparison = read(main/'boundary-comparison.json')
    fixture_updates = sum(read(root/name/'attempts.json', {}).get('fixture_update_calls',0)
                          for name in ('gpu-default','gpu-deterministic','gpu-default-repeat'))
    extra_reserved = ledger['phases']['batch8'].get('extra_control_reserved_decisions',0)
    primary_completed = budget.get('completed_decisions',0)
    reference_completed = sum(8 for v in reference_batches)
    charged = budget.get('reserved_decisions',0) + extra_reserved
    completed = primary_completed + reference_completed
    phase_wall = ledger['phases']['batch8'].get('wall_seconds')
    coefficient = phase_wall/completed if phase_wall is not None and completed else None
    conservative = max(15.708732, coefficient) if coefficient is not None else 15.708732
    estimate_seconds = (1200*conservative + 200*4 + 60)*1.25
    evidence = {}
    for p in (root/'measurement-ledger.json',root/'gpu-analysis.json',main/'contract.json',
              main/'training-budget.json',main/'training-summary.json',main/'resume-summary.json',
              main/'boundary-comparison.json'):
        if p.exists():
            evidence[str(p.relative_to(root))] = sha(p)
    return dict(run_id=root.name, phase_status=ledger['phases'], attempts=ledger['attempts'],
        measurement_global_wall_seconds=ledger.get('measurement_global_wall_seconds'),
        supervised_gpu_and_online_worker_wall_seconds=ledger.get('supervised_gpu_and_online_worker_wall_seconds'),
        total_fixture_updates=fixture_updates, charged_real_decisions=charged,
        completed_primary_real_decisions=primary_completed,
        completed_continuous_control_real_decisions=reference_completed,
        confirmed_real_decisions=completed, online_updates=budget.get('updates',0),
        in_flight=budget.get('in_flight',0), replay_transitions=summary.get('replay_transitions'),
        batches=batches, reference_batches=reference_batches,
        real_natural_boundary_saved=(main/'collector-boundary.pt').exists(),
        real_reference_complete=(main/'boundary-reference.pt').exists(),
        real_crossprocess_comparison=comparison,
        normal_entry_code_commit=read(main/'contract.json',{}).get('code_commit'),
        save_status=summary.get('status'), resume_status=resumed.get('status'),
        measured_collection_wall_seconds=phase_wall, measured_seconds_per_confirmed_decision=coefficient,
        estimate=dict(kind='conditional engineering estimate, not approval or confidence bound',
            decisions=1200,updates=200,collection_seconds_per_decision=conservative,
            old_collection_coefficient=15.708732,update_seconds_assumption=4,fixed_seconds_assumption=60,
            multiplier=1.25,seconds=estimate_seconds,hours=estimate_seconds/3600,
            rounded_hours=math.ceil(estimate_seconds/3600),
            formula='(1200*max(old15.708732,new measured collection coefficient) + 200*4 + 60)*1.25',
            limitations=['new online collector has zero updates and remains below 1000 warmup',
                         'GPU fixture has 40 loss positions; full 32x8 and long prefixes unmeasured',
                         'whole-batch natural boundary availability has no guaranteed bound',
                         'deterministic flags validated in diagnosis; normal entry needs explicit configuration decision']),
        evidence_sha256=evidence)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=report(args.root)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('charged_real_decisions','confirmed_real_decisions','total_fixture_updates','real_natural_boundary_saved','save_status')}))

if __name__=='__main__':
    main()
