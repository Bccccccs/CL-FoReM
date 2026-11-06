"""Hand-constructed outcome tables exercise the independent scoring contract."""
import importlib.util
from pathlib import Path
import pytest

path = Path(__file__).resolve().parents[3]/'scripts/task10_validation_audit.py'
spec = importlib.util.spec_from_file_location('task10_validation_audit', path)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def expected():
    return [dict(map_id=m, strategy=s, difficulty=d)
            for m, d in [('sparse_a', 'sparse'), ('standard_b', 'standard')]
            for s in ('trained', 'initial', 'uniform')]


def row(m, s, success, complete=True, reason='natural'):
    return dict(map_id=m, strategy=s, strict_success=success, complete=complete, reason=reason)


def test_scores_do_not_treat_timeout_or_unstarted_as_failure():
    rows = [row('sparse_a','trained',True), row('sparse_a','initial',False),
            row('sparse_a','uniform',False,False,'timeout'),
            row('standard_b','trained',False), row('standard_b','uniform',True)]
    result = audit.recompute_scores(expected(), rows)
    assert result['scores']['trained'] == dict(expected=2, completed=2, strict_success=1,
        missing=0, strict_success_rate_bounds=[.5,.5])
    assert result['scores']['initial'] == dict(expected=2, completed=1, strict_success=0,
        missing=1, strict_success_rate_bounds=[0,.5])
    assert result['scores']['uniform'] == dict(expected=2, completed=1, strict_success=1,
        missing=1, strict_success_rate_bounds=[.5,1])
    assert result['by_difficulty']['sparse']['uniform']['missing'] == 1
    assert result['by_difficulty']['standard']['initial']['missing'] == 1
    assert result['pairs']['trained_vs_initial'] == dict(win=1,loss=0,tie=0,missing=1)
    assert result['pairs']['trained_vs_uniform'] == dict(win=0,loss=1,tie=0,missing=1)
    assert {(v['map_id'],v['strategy'],v['missing_reason']) for v in result['missing']} == {
        ('sparse_a','uniform','timeout'), ('standard_b','initial','not_started')}


def test_pairwise_ties_include_success_success_and_failure_failure():
    rows = [row(m,s,m == 'sparse_a') for m in ('sparse_a','standard_b')
            for s in ('trained','initial','uniform')]
    report = audit.recompute_scores(expected(),rows)
    assert all(v == dict(win=0,loss=0,tie=2,missing=0) for v in report['pairs'].values())
    assert report['completed_identities'] == 6


@pytest.mark.parametrize('change', ['duplicate_actual','duplicate_expected','unexpected','difficulty','incomplete_success'])
def test_bad_identity_and_incomplete_success_are_rejected(change):
    exp = expected()
    rows = [row('sparse_a','trained',True)]
    if change == 'duplicate_actual': rows += rows
    elif change == 'duplicate_expected': exp += exp[:1]
    elif change == 'unexpected': rows[0]['map_id'] = 'test_a'
    elif change == 'difficulty': rows[0]['difficulty'] = 'standard'
    elif change == 'incomplete_success': rows[0]['complete'] = False
    with pytest.raises(ValueError): audit.recompute_scores(exp,rows)


def journal_fixture(tmp_path):
    import json
    import torch
    item=dict(episode_id='sparse_a__trained',map_id='sparse_a',strategy='trained',difficulty='sparse')
    fields=dict(decision_index=torch.tensor([0]),selected=torch.tensor([1]),
        candidates={'mask':torch.tensor([[False,True,True]])},map_ids=['sparse_a'],map_seeds=[12345],
        r_t={'n_fail':torch.tensor([20])},attempted_substeps=torch.tensor([40]),
        committed_substeps=torch.tensor([20]),terminated=torch.tensor([True]),
        truncated=torch.tensor([False]),strict_success=torch.tensor([False]),
        triggers={'failure_limit':torch.tensor([True]),'stall_limit':torch.tensor([True]),
                  'route_end':torch.tensor([False])})
    raw=dict(reservation=1,episode_id=item['episode_id'],fields=fields)
    (tmp_path/'decisions').mkdir()
    import os
    torch.save(raw,tmp_path/'decisions'/'one.pt')
    row=dict(item,complete=True,strict_success=False,terminated=True,truncated=False,
             failures=20,decisions=1,triggers={'failure_limit':True,'stall_limit':True,'route_end':False})
    record=dict(episode_id=item['episode_id'],decision_index=0,reservation=1,selected=1,
                mask=[False,True,True],logits=[None,.3,.2],r_t={'n_fail':[20]},core=row)
    (tmp_path/'decisions.jsonl').write_text(json.dumps(record)+'\n')
    budget=dict(reserved_decisions=1,completed_decisions=1,in_flight=0)
    return item,row,record,budget


def test_raw_terminal_journal_supports_multiple_simultaneous_end_triggers(tmp_path):
    item,row,record,budget=journal_fixture(tmp_path)
    issues,report=audit.decision_checks(tmp_path,[item],[row],budget)
    assert issues==[]
    assert report['episodes']==[dict(episode_id='sparse_a__trained',raw_decisions=1,
        failed_attempts=20,failure_kinds={},attempts_available=False,attempted_substeps=40,committed_substeps=20)]


@pytest.mark.parametrize('corruption',['ledger','mask','argmax','trigger','episode_success'])
def test_raw_journal_recomputation_detects_corrupt_derived_records(tmp_path,corruption):
    import json
    item,row,record,budget=journal_fixture(tmp_path)
    if corruption=='ledger': budget['completed_decisions']=0
    elif corruption=='mask': record['mask']=[True,False,True]
    elif corruption=='argmax': record['logits']=[None,.3,.5]
    elif corruption=='trigger': row['triggers']['stall_limit']=False
    elif corruption=='episode_success': row['strict_success']=True
    (tmp_path/'decisions.jsonl').write_text(json.dumps(record)+'\n')
    issues,_=audit.decision_checks(tmp_path,[item],[row],budget)
    assert issues
