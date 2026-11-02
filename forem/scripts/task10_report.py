#!/usr/bin/env python3
"""Recompute task10 counters, paired scores and cost coefficients from artifacts.

Read-only: does not load a policy, collect transitions or perform updates.
"""
import argparse
import hashlib
import json
from pathlib import Path


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def read(path):
    return json.loads(path.read_text()) if path.exists() else None


def report(run):
    budget = read(run/'training-budget.json')
    training = read(run/'training-summary.json')
    paired = read(run/'paired-summary.json')
    real = lines(run/'real-executions.jsonl')
    episodes = lines(run/'episodes.jsonl')
    decisions = lines(run/'decisions.jsonl')
    journal_errors = []
    for index, row in enumerate(real, 1):
        path = run/row['journal']
        if row['completed'] != index*8 or not path.is_file():
            journal_errors.append(row['completed'])
    actual = sum(len(r['selected']) for r in real)
    attempts = sum(sum(r['attempted']) for r in real)
    commits = sum(sum(r['committed']) for r in real)
    zero_attempts = sum(v == 0 for r in real for v in r['attempted'])
    collected_boundaries = []
    previous_next = None
    for row in decisions:
        timing = row['timing']
        if previous_next != timing['current']:
            collected_boundaries.append(timing['current'])
        collected_boundaries.append(timing['next'])
        previous_next = timing['next']
    # This is explicitly a lower bound if deadline interrupts a prediction or
    # reset before its complete diagnostic timing reaches decisions.jsonl.
    prediction = {k: sum(b.get(k, 0) for b in collected_boundaries)
                  for k in ('valid_slots', 'b3_calls', 'b3_row_calls',
                            'attempted_substeps', 'committed_substeps')}
    prediction['coverage'] = 'completed logged boundaries only; excludes interrupted/unlogged work'
    counts = dict(journal_decisions=actual, attempted_substeps=attempts,
                  committed_substeps=commits, zero_attempt_decisions=zero_attempts,
                  failed_attempt_substeps=attempts-commits,
                  attempted_sim_seconds=attempts*.05, committed_sim_seconds=commits*.05,
                  completed_episodes=len(episodes), strict_success=sum(r['strict_success'] for r in episodes),
                  journal_errors=journal_errors,
                  budget_completed_matches=None if budget is None else actual == budget['completed_decisions'])
    result = dict(run_id=run.name, training=training, budget=budget,
                  recomputed=counts, prediction_work_lower_bound=prediction, paired=paired)
    if training and actual:
        collection_parts = ('lower_load_hashes', 'initial_reset', 'online_memory_inference',
                            'decision_total', 'execution_journal', 'next_boundary', 'replay_to_cpu', 'reset_ended')
        measured = training['timing']
        seconds = sum(measured.get(k, {}).get('total_s', 0) for k in collection_parts)
        cost = dict(collection_component_seconds=seconds,
                    collection_seconds_per_decision=seconds/actual,
                    collection_hours_per_1000_decisions=seconds/actual*1000/3600,
                    includes_interrupted_work=True,
                    update_seconds=None if 'update_total' not in measured else measured['update_total']['mean_s'],
                    checkpoint_recovery_seconds=measured.get('checkpoint_and_recovery_check', {}).get('total_s'),
                    limitation='single smoke, mostly uniform warmup; policy/scene workload can change',
                    formula_seconds='D * collection_seconds_per_decision + U * update_seconds + evaluation + checkpoints')
        if paired:
            complete = sum(r['complete'] for r in paired['rows'])
            cost['paired_seconds_per_completed_episode'] = paired['wall_seconds']/complete if complete else None
        result['cost_coefficients'] = cost
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    value = report(args.run.resolve())
    text = json.dumps(value, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(text+'\n')
    else:
        print(text)
