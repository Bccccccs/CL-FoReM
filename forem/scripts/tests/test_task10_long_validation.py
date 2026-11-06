"""CPU contract tests only; no GPU, environment, training, or actual evaluation."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import time

import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import task10_long_validation as long
from task10.runtime import atomic_json


def config():
    return dict(objective='relative_uniform', objective_version=long.OBJECTIVE['version'], alpha=.35,
        max_decisions=10000, max_updates=9000, random_warmup_decisions=1000)


def boundary(decisions=2000):
    updates = long.CHECKPOINTS[decisions]
    return dict(format=long.BOUNDARY_SCHEMA, counters=dict(decisions=decisions, updates=updates, vector_dim=7),
        learner=dict(learning_objective=long.OBJECTIVE, alpha=float(torch.tensor(.35)),
            temperature=dict(format='task10-fixed-temperature-v1', alpha=.35), updates=updates, stage='1', total_updates=9000, model={'a': torch.tensor([2.])}),
        ledger=dict(completed_decisions=decisions, reserved_decisions=decisions, updates=updates, in_flight=0, max_decisions=10000, max_updates=9000, max_seconds=194400),
        replay=dict(episodes={'one': [{}] * decisions}, size=decisions), config={'config': config()})


def write_boundary(tmp_path, decisions=2000):
    p = long.checkpoint_path(tmp_path, decisions); p.parent.mkdir(parents=True, exist_ok=True)
    torch.save(boundary(decisions), p)
    atomic_json(p.with_name(f'decision-{decisions:06d}.json'), dict(format='task10-long-checkpoint-index-v1',
        decisions=decisions, updates=long.CHECKPOINTS[decisions], scheduler_total_updates=9000, collector_resumable=True,
        boundary=dict(path=str(p.relative_to(tmp_path)), sha256=long.sha256(p))))
    return p


@pytest.mark.parametrize('decisions,updates', [(2000, 1000), (5000, 4000), (10000, 9000)])
def test_real_long_checkpoint_counters_and_schema(tmp_path, decisions, updates):
    p = write_boundary(tmp_path, decisions)
    result = long.checked_boundary(p, decisions)
    state, width, meta = long.payload_state(p, 'trained')
    assert result['counters']['updates'] == updates and meta['updates'] == updates
    assert meta['decisions'] == decisions and meta['source_schema'] == long.BOUNDARY_SCHEMA and width == 7
    assert torch.equal(state['a'], torch.tensor([2.]))


@pytest.mark.parametrize('mutation', ['old_schema', 'old_counters', 'learner_updates', 'ledger', 'inflight', 'replay', 'temperature', 'scheduler_scale', 'learner_total', 'budget_cap', 'budget_time'])
def test_rejects_old_or_inconsistent_metadata(tmp_path, mutation):
    p = write_boundary(tmp_path); value = boundary()
    if mutation == 'old_schema': value['format'] = 'task10-stage1-actor-v1'
    if mutation == 'old_counters': value['counters'].update(decisions=1200, updates=200)
    if mutation == 'learner_updates': value['learner']['updates'] = 200
    if mutation == 'ledger': value['ledger']['reserved_decisions'] += 8
    if mutation == 'inflight': value['ledger']['in_flight'] = 8
    if mutation == 'replay': value['replay']['size'] -= 1
    if mutation == 'temperature': value['learner']['temperature']['alpha'] = .2
    if mutation == 'scheduler_scale': value['config']['config']['max_updates'] = 200
    if mutation == 'learner_total': value['learner']['total_updates'] = 200
    if mutation == 'budget_cap': value['ledger']['max_decisions'] = 1200
    if mutation == 'budget_time': value['ledger']['max_seconds'] = 25200
    torch.save(value, p)
    with pytest.raises(ValueError): long.checked_boundary(p, 2000)


def identities():
    return [dict(episode_id=f'{d}_{i}__trained', map_id=f'{d}_{i}', difficulty=d, strategy='trained',
        scene_seed=101, policy_seed=None, order=n)
        for n, (i, d) in enumerate((i, d) for i in range(6) for d in ('sparse', 'standard'))]


def manifest():
    expected = identities()
    return dict(schema=long.SCHEMA, learning_objective=long.OBJECTIVE,
        source_checkpoint=dict(decisions=2000, updates=1000), expected=expected,
        config=dict(max_episodes=12, max_decisions=1800, max_updates=0, max_seconds=5400),
        kl_reference=dict(snapshots={r['episode_id']: {} for r in expected}))


def test_manifest_does_not_accept_legacy_checkpoint_or_loose_budget():
    long.check_manifest(manifest())
    for change in ['counter', 'budget', 'identity']:
        value = manifest()
        if change == 'counter': value['source_checkpoint']['updates'] = 200
        if change == 'budget': value['config']['max_decisions'] = 5400
        if change == 'identity': value['expected'][0]['strategy'] = 'uniform'
        with pytest.raises(ValueError): long.check_manifest(value)


def test_source_requires_training_to_end_and_fresh_initial(tmp_path):
    write_boundary(tmp_path)
    initial = boundary(); initial['learner']['updates'] = 0; initial['counters'].update(decisions=0, updates=0)
    torch.save(initial, tmp_path / 'initial-learner.pt'); atomic_json(tmp_path / 'contract.json', {'config': config()})
    atomic_json(tmp_path / 'training-summary.json', dict(status='active'))
    with pytest.raises(ValueError, match='has not ended'): long.source_check(tmp_path, 2000)
    atomic_json(tmp_path / 'training-summary.json', dict(status='partial'))
    assert long.source_check(tmp_path, 2000)['training_status'] == 'partial'
    initial['counters']['decisions'] = 8; torch.save(initial, tmp_path / 'initial-learner.pt')
    with pytest.raises(ValueError, match='fresh'): long.source_check(tmp_path, 2000)


def test_initial_typed_difference_refuses_worker_before_execution(tmp_path, monkeypatch):
    value = manifest(); snapshot = {'physical': torch.tensor([1.])}
    original_path = tmp_path / 'reference.pt'; torch.save(snapshot, original_path)
    ref = dict(path=str(original_path), file_sha256=long.sha256(original_path), tree_sha256=long.base.tree_hash(snapshot),
        hashes={k: long.base.tree_hash(v) for k, v in snapshot.items()})
    value['kl_reference']['snapshots'] = {r['episode_id']: ref for r in value['expected']}
    value.update(files={}, source_run=str(tmp_path / 'source'))
    atomic_json(tmp_path / 'manifest.json', value)
    monkeypatch.setattr(long, 'source_check', lambda *args: value['source_checkpoint'])
    monkeypatch.setattr(long.base, 'initial_snapshot', lambda *args: {'physical': torch.tensor([1.], dtype=torch.float64)})
    original = long.base.initial_snapshot; budget = long.base.EvalBudget; before_payload = long.base.payload_state; calls = []
    def worker(run):
        long.base.initial_snapshot(None, None)
        calls.append('executed')
    monkeypatch.setattr(long.base, 'worker', worker)
    with pytest.raises(ValueError, match='before execution'): long.worker(tmp_path)
    assert calls == [] and long.base.initial_snapshot is original and long.base.EvalBudget is budget
    assert long.base.payload_state is before_payload
    assert json.loads((tmp_path / 'initial-comparisons' / (identities()[0]['episode_id'] + '.json')).read_text())['match'] is False


def test_paired_missing_keeps_denominator_twelve(tmp_path):
    rows = [dict(r, complete=True, strict_success=True) for r in identities()]
    for i, row in enumerate(rows):
        atomic_json(tmp_path / 'episodes' / (row['map_id'] + '__trained.json'), dict(row, strict_success=i < 10))
    rows[0]['complete'] = False
    assert long.paired_score(rows, tmp_path, 'trained') == dict(win=2, loss=0, tie=9, missing=1)


def test_sequence_all_missing_never_calls_worker_and_refuses_retry(tmp_path, monkeypatch):
    source = tmp_path / 'source'; atomic_json(source / 'training-summary.json', dict(status='partial'))
    run = tmp_path / 'eval'; calls = []
    monkeypatch.setattr(long, 'curves', lambda run: long.curve_rows({}))
    monkeypatch.setattr(long.subprocess, 'run', lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('no subprocess allowed')))
    original_time = long.time.time
    time_calls = iter([1., 16202., 16203., 16204.])
    monkeypatch.setattr(long.time, 'time', lambda: next(time_calls, 16204.))
    assert long.sequence(source, run, 'code', tmp_path / 'old', tmp_path / 'oldkl') == 0
    value = json.loads((run / 'sequence.json').read_text())
    assert value['status'] == 'partial' and value['reserved_decisions'] == 0 and value['updates'] == 0
    assert len(value['checkpoints']) == 3 and calls == []
    with pytest.raises(RuntimeError, match='claimed'): long.sequence(source, run, 'code', tmp_path, tmp_path)


def test_budget_caps_and_shared_epoch(tmp_path):
    b = long.kl.EvalBudget(tmp_path / 'budget.json', time.monotonic(), time.time())
    assert b.state['max_seconds'] == 5400 and b.state['max_updates'] == 0
    b.state.update(reserved_decisions=1800, completed_decisions=1800)
    with pytest.raises(StopIteration, match='1800'): b.reserve('extra', 1)
    assert b.state['deadline_epoch'] - b.state['started_epoch'] == 5400


def test_curve_missing_is_not_zero_or_model_selection():
    rows = long.curve_rows({})
    assert [r['decisions'] for r in rows] == [2000, 5000, 10000]
    assert all(r['strict_success'] is None and r['missing'] == 12 and r['status'] == 'missing' for r in rows)


def test_stopped_boundary_and_resumed_terminal_summary(tmp_path):
    atomic_json(tmp_path / 'training-summary.json', dict(status='stopped_boundary'))
    assert long.training_end_summary(tmp_path)[0]['status'] == 'stopped_boundary'
    atomic_json(tmp_path / 'resume-summary.json', dict(status='complete'))
    atomic_json(tmp_path / 'worker-exit.json', dict(status='complete'))
    assert long.training_end_summary(tmp_path)[0]['status'] == 'complete'
    atomic_json(tmp_path / 'worker-exit.json', dict(status='failed'))
    with pytest.raises(ValueError, match='exit status'): long.training_end_summary(tmp_path)


def test_source_index_hash_cannot_hide_changed_checkpoint(tmp_path):
    p = write_boundary(tmp_path)
    value = boundary(); value['learner']['model']['a'][0] += 1; torch.save(value, p)
    with pytest.raises(ValueError, match='index path/content hash'): long.source_check(tmp_path, 2000)


@pytest.mark.parametrize('corrupt', [False, True])
def test_report_calls_real_raw_and_three_argument_snapshot_audits(tmp_path, monkeypatch, corrupt):
    """Model construction is stubbed; real decision and snapshot audit interfaces run."""
    import task10_validation_audit_v2 as audit
    value = manifest(); expected = value['expected']; ref = tmp_path / 'old'
    value.update(files={}, source_run=str(tmp_path / 'source'), initial_weight_comparison={},
        old_kl_reference=dict(run=str(ref)), scenes=[dict(id=r['map_id'], sha256=dict(sidecar='geometry')) for r in expected])
    value['source_checkpoint']['checkpoint'] = 'immutable-fixture.pt'
    value['kl_reference']['run'] = str(ref)
    name = expected[0]['episode_id']
    candidates = dict(mask=torch.tensor([[True, True]]), inplace=torch.tensor([[True, False]]))
    snapshot = dict(observation=dict(q=torch.tensor([[1.]])), candidates=candidates, proposal_seed=7, map_geometry='geometry')
    for identity in expected:
        value['kl_reference']['snapshots'][identity['episode_id']] = {'tree_sha256': long.base.tree_hash(snapshot)}
        for strategy in ('trained', 'uniform'):
            atomic_json(ref / 'episodes' / (identity['map_id'] + '__' + strategy + '.json'), dict(identity,
                strategy=strategy, complete=True, strict_success=False))
    row = dict(expected[0], complete=True, strict_success=True, decisions=1, reason='strict_success',
        memory_reset=True, proposal_seed=7, initial_hashes={k: long.base.tree_hash(v) for k, v in snapshot.items()},
        terminated=True, truncated=False, failures=0, triggers={'route_end': True})
    atomic_json(tmp_path / 'episodes' / (name + '.json'), row)
    initial = tmp_path / 'initial' / (name + '.pt'); initial.parent.mkdir(); torch.save(snapshot, initial)
    fields = dict(decision_index=torch.tensor([0]), selected=torch.tensor([1]), candidates=deepcopy(candidates),
        observation=deepcopy(snapshot['observation']), map_ids=[expected[0]['map_id']],
        r_t=dict(n_fail=torch.tensor([0])), attempted_substeps=torch.tensor([0]), committed_substeps=torch.tensor([0]),
        terminated=torch.tensor([True]), truncated=torch.tensor([False]), strict_success=torch.tensor([True]),
        triggers={'route_end': torch.tensor([True])})
    if corrupt: fields['observation']['q'][0, 0] = 2.
    raw = tmp_path / 'decisions' / (name + '-0001.pt'); raw.parent.mkdir()
    torch.save(dict(episode_id=name, reservation=1, fields=fields, attempts=[]), raw)
    record = dict(episode_id=name, decision_index=0, reservation=1, selected=1, mask=[True, True], logits=[0., 1.],
        probabilities=None, r_t={'n_fail': [0]}, triggers={'route_end': [True]}, raw_path=str(raw.relative_to(tmp_path)), raw_sha256=long.sha256(raw))
    (tmp_path / 'decisions.jsonl').write_text(json.dumps(record) + '\n')
    budget = dict(max_episodes=12, max_decisions=1800, max_updates=0, max_seconds=5400, updates=0,
        completed_decisions=1, reserved_decisions=1, in_flight=0, started_epoch=1., deadline_epoch=5401.,
        started_monotonic=2., deadline_monotonic=5402., completed_episodes=1, started_episodes=1,
        wall_seconds=1., status='incomplete_budget')
    atomic_json(tmp_path / 'manifest.json', value); atomic_json(tmp_path / 'budget.json', budget)
    atomic_json(tmp_path / 'summary.json', {'status': 'incomplete_budget'})
    atomic_json(tmp_path / 'launch.json', {'status': 'process_exited', 'returncode': 0})
    monkeypatch.setattr(long, 'source_check', lambda *args: dict(value['source_checkpoint']))
    monkeypatch.setattr(long, 'weights_checks', lambda *args: ([], {'weights': {'updates': 0}}))
    result = long.report(tmp_path)
    assert result['checks']['snapshots']['paired_maps'] == 1
    assert result['checks']['decisions']['raw_journals'] == 1
    assert result['scores']['expected'] == 12 and result['scores']['missing'] == 11
    assert result['paired']['old_KL200'] == dict(win=1, loss=0, tie=0, missing=11)
    assert (result['status'] == 'failed') == corrupt
    if corrupt:
        assert 'initial observation differs from first raw decision: ' + name in result['issues']
    else:
        assert result['status'] == 'verified_partial' and result['issues'] == []


def test_host_launch_has_one_claim_original_epoch_and_global_shell_cap(tmp_path, monkeypatch):
    run = tmp_path / 'results/task10/new-eval/checkpoint-002000'
    atomic_json(run / 'manifest.json', manifest())
    monkeypatch.setattr(long, 'ROOT', tmp_path)
    commands = []
    class FakeProcess:
        pid = 123
        def wait(self): return 0
    def popen(command, **kwargs):
        commands.append(command)
        return FakeProcess()
    monkeypatch.setattr(long.subprocess, 'Popen', popen)
    assert long.launch(run, 'commit', epoch=10., global_deadline=100.) == 0
    value = json.loads((run / 'launch.json').read_text())
    assert value['started_epoch'] == 10. and value['deadline_epoch'] == 5410.
    assert 'TASK10_STARTED_EPOCH=10.0' in commands[0][3]
    assert 'TASK10_EVAL_GLOBAL_DEADLINE_EPOCH=100.0' in commands[0][3]
    assert 'global_deadline-now-2<left' in commands[0][3]
    assert value['status'] == 'process_exited' and value['returncode'] == 0
    assert Path(value['log']).name == 'new-eval-checkpoint-002000-eval.log'
    with pytest.raises(ValueError, match='already launched'): long.launch(run, 'commit')
    assert len(commands) == 1


@pytest.mark.parametrize('late_group,expired', [(False, False), (False, True), (True, False), (True, True)])
def test_sequence_report_obeys_both_original_group_and_global_deadlines(tmp_path, monkeypatch, late_group, expired):
    """A finished worker cannot acquire an extra report window beyond its epoch."""
    source = tmp_path / 'results/task10/train'; run = tmp_path / 'results/task10/eval'
    atomic_json(source / 'training-summary.json', {'status': 'partial'})
    checkpoint = source / 'checkpoints/decision-002000.boundary.pt'
    checkpoint.parent.mkdir(); checkpoint.touch()
    monkeypatch.setattr(long, 'ROOT', tmp_path)
    monkeypatch.setattr(long, 'CHECKPOINTS', {2000: 1000})
    clock = {'now': 1000., 'initial_calls': 0}
    def now():
        # The sequence begins at 1000; a late group is queued near its global cap.
        clock['initial_calls'] += 1
        if late_group and clock['initial_calls'] == 2: clock['now'] = 16000.
        return clock['now']
    monkeypatch.setattr(long.time, 'time', now)
    calls = []
    monkeypatch.setattr(long, 'container_command', lambda arguments, **kwargs: (arguments[0], kwargs['seconds']))
    class Result:
        returncode = 0
    def execute(command, **kwargs):
        calls.append(command)
        return Result()
    monkeypatch.setattr(long.subprocess, 'run', execute)
    def launch(*args, **kwargs):
        clock['now'] = (17201. if expired else 17190.) if late_group else (6401. if expired else 6390.)
        return 0
    monkeypatch.setattr(long, 'launch', launch)
    monkeypatch.setattr(long, 'curves', lambda run: long.curve_rows({}))
    assert long.sequence(source, run, 'commit', tmp_path, tmp_path) == 0
    state = json.loads((run / 'sequence.json').read_text())
    stage = state['checkpoints']['2000']
    reports = [seconds for phase, seconds in calls if phase == 'report']
    if expired:
        assert reports == []
        assert stage['report_status'] == ('missing_global_deadline' if late_group else 'missing_group_deadline')
        assert 'report_returncode' not in stage
    else:
        assert reports == [8.]  # min(group/global deadline - current epoch - kill grace)
        assert stage['report_returncode'] == 0
    assert checkpoint.exists() and state['status'] == 'partial'
