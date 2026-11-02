#!/usr/bin/env python3
"""Read-only recomputation of bounded cost/recovery evidence and budget proposal."""
import argparse
import hashlib
import json
from pathlib import Path


def build(root, old):
    read = lambda path: json.loads(path.read_text())
    probe = read(root/'cost-probe-repaired.json')
    baseline = probe['passes'][0]
    timing = [v['timing'] for v in baseline['boundaries']]
    assert len(timing) == 5 and len(baseline['batches']) == 2
    assert all(b['old_equal'] for b in baseline['batches'])
    counts = {k: sum(t.get(k, 0) for t in timing) for k in
              ('valid_slots', 'b3_calls', 'b3_row_calls', 'attempted_substeps', 'committed_substeps')}
    counts.update(actual_attempted=sum(b['actual_attempted'] for b in baseline['batches']),
                  actual_committed=sum(b['actual_committed'] for b in baseline['batches']))
    assert counts['valid_slots'] == 196 and counts['actual_attempted'] == 2359
    profile = read(root/'reset-profile.json')
    assert profile['status'] == 'verified' and profile['compared_to_old']
    assert profile['boundary_sha256'] == baseline['boundaries'][0]['sha256']
    parts = {name.removeprefix('prediction.'): r['wall_exclusive_s'] for name, r in profile['timing'].items()
             if name.startswith('prediction.')}
    assert abs(sum(parts.values())-profile['timing']['prediction.prediction']['wall_inclusive_s']) < 1e-6
    diagnosis = read(root/'recovery-diagnosis/diagnosis.json')
    real = read(root/'collector-boundary/real-replay-evidence.json')
    online = read(root/'collector-boundary/online-summary.json')
    ledger = read(root/'measurement-ledger.json')
    old_summary = read(old/'training-summary.json')
    collection_service = sum(baseline['business_wall_s'].values())
    old_overhead = sum(old_summary['timing'][k]['total_s'] for k in
                       ('online_memory_inference', 'execution_journal', 'replay_to_cpu'))
    collection_coefficient = (collection_service+old_overhead)/16
    # Inclusive diagnostic time is a conservative bound on this short fixture's
    # two-update mean, not a measured distribution for online/long-prefix updates.
    two_update_mean_bound = diagnosis['wall_seconds']/2
    proposal = dict(executed=False, decisions=1200, random_warmup_decisions=1000,
                    updates=200, batch=8, engineering_update_allowance_seconds=4,
                    engineering_fixed_allowance_seconds=60, engineering_margin=1.25,
                    proposed_training_wall_seconds=7*3600,
                    paired_validation_seconds_separate=1800,
                    assumptions='same B3/config/device/batch8 and similar random-warmup workload; no production optimization',
                    limitations='16 distinct old decisions only; GPU next update not bitwise equal; batch8 collector recovery unverified')
    proposal['nominal_seconds'] = 1200*collection_coefficient+200*4+60
    proposal['with_margin_seconds'] = proposal['nominal_seconds']*1.25
    proposal['observed_fixture_loss_positions'] = diagnosis['losses'][0]['loss_transitions']
    proposal['protocol_max_loss_positions'] = 32*8
    proposal['long_episode_prefix_cost_measured'] = False
    proposal['implied_mean_update_headroom_seconds'] = (7*3600-1200*collection_coefficient-60)/200
    assert proposal['with_margin_seconds'] < proposal['proposed_training_wall_seconds']
    first_start = min(j['started_epoch'] for j in ledger['jobs'].values())
    last_finish = max(j['finished_epoch'] for j in ledger['jobs'].values())
    result = dict(kind='bounded support evidence; not a new end-to-end training trial',
        counts_complete_baseline=counts, initial_prediction_exclusive_seconds=parts,
        baseline_service_seconds=baseline['business_wall_s'], sampling_seconds=baseline['sample_timing'],
        collection_seconds_per_decision=collection_coefficient,
        collection_1000_hours=1000*collection_coefficient/3600,
        short_fixture_two_update_mean_upper_bound_seconds=two_update_mean_bound,
        real_replay_nonempty_sample_verified=real['sampled_anchors'] == 16 and real['learner_rng_next_sample'] == 'verified',
        updated_optimizer_initial_state_equal=not diagnosis['differences']['initial'],
        gpu_next_update_exact=diagnosis['status'] == 'verified',
        gpu_next_update_differences=diagnosis['differences']['state'],
        fixture_update_calls=5, original_real_decisions=16, charged_measurement_decision_upper_bound=34,
        confirmed_measurement_decisions=26, reserved_unconfirmed_measurement_decisions=8,
        online_collector_status=online['status'], online_new_decisions=online['new_real_decisions'],
        online_boundary=online['phase_summaries'].get('resume-summary', {}).get('boundary'),
        measured_worker_seconds=ledger['consumed_worker_seconds'], global_measurement_span_seconds=last_finish-first_start,
        optimization_adopted=False, full_instrumented_trajectory_verified=False,
        checkpoint_storage_audit=read(root/'storage-audit.json'),
        proposal=proposal,
        checked_sha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (root/'cost-probe.json', root/'cost-probe-repaired.json', root/'reset-profile.json',
             root/'recovery-diagnosis/diagnosis.json', root/'collector-boundary/online-summary.json',
             root/'collector-boundary/real-replay-evidence.json', root/'measurement-ledger.json')})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--old', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = build(args.root, args.old)
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: value[k] for k in ('collection_seconds_per_decision', 'collection_1000_hours',
          'measured_worker_seconds', 'global_measurement_span_seconds', 'gpu_next_update_exact', 'online_collector_status', 'proposal')}))
