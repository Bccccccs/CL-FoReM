#!/usr/bin/env python3
"""Read-only task10 artifact audit; never runs a policy, environment or update."""
import argparse
import hashlib
import json
from pathlib import Path
import torch
from task10.lower import verify_frozen_manifest


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--reference', type=Path, default=Path('/reference'))
    args = parser.parse_args()
    p = args.run
    read = lambda name: json.loads((p/name).read_text())
    budget, training, paired = map(read, ('training-budget.json', 'training-summary.json', 'paired-summary.json'))
    frozen = verify_frozen_manifest(args.reference)
    state = torch.load(p/'offline-learner.pt', map_location='cpu', weights_only=False)
    actor = torch.load(p/'final.actor.pt', map_location='cpu', weights_only=False)
    rows = [r for seq in state['replay']['episodes'].values() for r in seq]
    identity = lambda r: (int(r['environment_id']), int(r['episode_id']), int(r['decision_index']))
    replay = {identity(r): r for r in rows}
    assert len(replay) == len(rows) == budget['completed_decisions'] == actor['decisions'] == 16
    assert state['counters']['decisions'] == 16
    assert state['learner']['updates'] == actor['updates'] == budget['updates'] == 0
    assert budget['reserved_decisions'] == 16 and budget['in_flight'] == 0
    assert training['status'] == 'failed' and training['replay_transitions'] == 16
    journal_rows = 0
    failed_rows, failures = 0, 0
    for path in sorted((p/'real-executions').glob('batch-*.pt')):
        journal = torch.load(path, map_location='cpu', weights_only=False)['fields']
        for i, selected in enumerate(journal['selected']):
            key = (i, int(journal['episode_id'][i]), int(journal['decision_index'][i]))
            r = replay[key]
            assert int(selected) == int(r['selected']) and bool(r['candidates']['mask'][selected])
            assert torch.equal(journal['reward'][i], r['reward'])
            assert torch.equal(journal['r_t']['n_fail'][i], r['r_t']['n_fail'])
            n_fail = int(r['r_t']['n_fail'])
            failures += n_fail
            failed_rows += int(n_fail > 0)
            assert abs(float(r['dt'])-int(r['attempted_substeps'])*.05) < 2e-6
            assert abs(float(r['discount'])-.99**(float(r['dt'])/.1)) < 2e-6
            assert abs(float(r['reward'])-sum(float(v) for v in r['reward_components'].values())) < 2e-6
            assert float(r['bootstrap_mask']) == float(not (r['terminated'] or r['truncated']))
            assert not r['next_candidates'].get('pending', False)
            journal_rows += 1
    assert journal_rows == 16 and failed_rows == 3 and failures == 60
    assert read('pending-intent.json')['reserved_through'] == budget['completed_decisions']
    contract = read('paired-execution-contract.json')
    assert digest(p/'final.actor.pt') == contract['actor_sha256']
    manifest = json.loads((args.reference/'results/task8/t8-pool-20261027/cube-pool-v2/manifest.json').read_text())
    expected = sorted(m['id'] for m in manifest['maps'] if m['split'] == 'validation')[:4]
    assert expected == contract['maps']
    assert len(paired['rows']) == 8 and all(r['complete'] for r in paired['rows'])
    outcomes = dict(win=0, loss=0, tie=0, missing=0)
    for key in expected:
        pair = {r['strategy']: r for r in paired['rows'] if r['map_id'] == key}
        a, b = pair['actor'], pair['uniform']
        assert a['seed'] == b['seed'] == 101 and a['random_seed'] == b['random_seed'] == 102
        for name in ('initial_hash', 'proposal_seed'):
            assert a[name] == b[name]
        assert a['scene_provenance'][0]['hashes'] == b['scene_provenance'][0]['hashes']
        outcomes['tie' if a['strict_success'] == b['strict_success'] else 'win' if a['strict_success'] else 'loss'] += 1
    assert outcomes == paired['pairs']
    assert sum(r['strict_success'] for r in paired['rows'] if r['strategy'] == 'actor') == 0
    assert sum(r['strict_success'] for r in paired['rows'] if r['strategy'] == 'uniform') == 3
    assert training['wall_seconds'] < 1800 and paired['wall_seconds'] < 1800
    result = dict(artifact_consistency='PASS', training_gate='NOT_READY',
                  decisions=16, updates=0, journal_rows=journal_rows, failed_decision_rows=failed_rows,
                  failure_events=failures, frozen_source_files=frozen['source_count'],
                  frozen_artifacts=len(frozen['artifacts']), paired_complete=8, paired_missing=0,
                  actor_strict_success=0, uniform_strict_success=3, paired_outcomes=outcomes,
                  actor_sha256=digest(p/'final.actor.pt'),
                  checked_sha256={name: digest(p/name) for name in
                    ('contract.json', 'training-budget.json', 'training-summary.json', 'offline-learner.pt',
                     'paired-execution-contract.json', 'paired-budget.json', 'paired-summary.json')})
    (p/'audit-final.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
