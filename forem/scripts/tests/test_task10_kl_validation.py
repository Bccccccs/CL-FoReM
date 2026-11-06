"""CPU tests only: no environment creation, GPU, subprocess evaluation or updates."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import time

import pytest
import torch

SCRIPTS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SCRIPTS))
import task10_kl_validation as kl
from task10.runtime import atomic_json


def identities():
    return [dict(episode_id=f'{d}_{i}__{s}',map_id=f'{d}_{i}',difficulty=d,strategy=s,
                 scene_seed=101,policy_seed=102 if s=='uniform' else None,order=n)
            for n,(d,i,s) in enumerate((d,i,s) for i in range(6) for d in ('sparse','standard') for s in ('trained','initial','uniform'))]


def manifest():
    rows=kl.trained_only(identities())
    return dict(schema=kl.SCHEMA,learning_objective=kl.OBJECTIVE,expected=rows,
                config=dict(max_episodes=12,max_decisions=1800,max_updates=0,max_seconds=5400),
                kl_reference=dict(snapshots={r['episode_id']:{} for r in rows}))


def test_filter_exactly_twelve_unique_consecutive_trained():
    rows=kl.trained_only(identities())
    assert len(rows)==12 and [r['order'] for r in rows]==list(range(12))
    assert all(r['strategy']=='trained' for r in rows)
    with pytest.raises(ValueError):kl.trained_only(identities()+[identities()[0]])
    with pytest.raises(ValueError):kl.trained_only(identities()[3:])


@pytest.mark.parametrize('change',[{'schema':'unknown'},{'learning_objective':dict(kl.OBJECTIVE,version='bad')},
    {'config':dict(max_episodes=36,max_decisions=5400,max_updates=0,max_seconds=5400)}])
def test_manifest_rejects_version_and_loose_caps(change):
    value=manifest();value.update(change)
    with pytest.raises(ValueError):kl.check_manifest(value)


def test_manifest_rejects_hidden_other_strategy():
    value=manifest();value['expected'][0]['strategy']='uniform'
    with pytest.raises(ValueError):kl.check_manifest(value)


def test_budget_1800_reservation_cap_and_twelve_episode_cap(tmp_path):
    budget=kl.EvalBudget(tmp_path/'budget.json',time.monotonic(),time.time())
    assert (budget.state['max_episodes'],budget.state['max_decisions'],budget.state['max_seconds'])==(12,1800,5400)
    budget.state['reserved_decisions']=1799;budget.state['completed_decisions']=1799
    assert budget.reserve('last',149)==1800
    budget.complete()
    with pytest.raises(StopIteration,match='1800'):budget.reserve('extra',150)
    budget.state['started_episodes']=13
    with pytest.raises(StopIteration,match='12 episode'):budget.check()
    assert budget.state['updates']==0
    with pytest.raises(RuntimeError):kl.EvalBudget(tmp_path/'budget.json',time.monotonic(),time.time())


@pytest.mark.parametrize('change',[{'learning_objective':dict(kl.OBJECTIVE,objective='legacy')},
    {'learning_objective':dict(kl.OBJECTIVE,version='bad')},{'alpha':.2}])
def test_objective_rejects_reference_or_new_model_mismatch(change):
    actor=dict(learning_objective=kl.OBJECTIVE,alpha=float(torch.tensor(.35)));actor.update(change)
    with pytest.raises(ValueError):kl.check_objective(actor)


def test_fixed_temperature_contract_checked():
    actor=dict(learning_objective=kl.OBJECTIVE,alpha=float(torch.tensor(.35)))
    kl.check_objective(actor)
    state=dict(actor,temperature=dict(format='task10-fixed-temperature-v1',alpha=.35))
    kl.check_objective({'learner':state},learner=True)
    state['temperature']['alpha']=.2
    with pytest.raises(ValueError):kl.check_objective({'learner':state},learner=True)


def snapshot_reference(tmp_path,snapshot):
    path=tmp_path/'original.pt';torch.save(snapshot,path)
    return dict(path=str(path),file_sha256=kl.sha256(path),tree_sha256=kl.base.tree_hash(snapshot),
                hashes={k:kl.base.tree_hash(v) for k,v in snapshot.items()})


def test_initial_exact_typed_comparison_and_difference_record(tmp_path):
    snapshot=dict(physical=torch.tensor([1.]),mask=torch.tensor([True]),proposal_seed=7)
    ref=snapshot_reference(tmp_path,snapshot);identity={'episode_id':'test__trained'}
    assert kl.compare_initial(tmp_path/'run',identity,snapshot,ref) is snapshot
    changed=dict(snapshot,physical=torch.tensor([1.],dtype=torch.float64))
    with pytest.raises(ValueError,match='before execution'):kl.compare_initial(tmp_path/'run',identity,changed,ref)
    record=json.loads((tmp_path/'run/initial-comparisons/test__trained.json').read_text())
    assert record['match'] is False and record['differing_keys']==['physical']
    assert (tmp_path/'run/initial/test__trained.pt').exists()


def test_initial_modified_reference_file_rejected(tmp_path):
    snapshot={'x':torch.tensor([1.])};ref=snapshot_reference(tmp_path,snapshot)
    torch.save({'x':torch.tensor([2.])},ref['path'])
    with pytest.raises(ValueError,match='file changed'):kl.compare_initial(tmp_path,{'episode_id':'a'},snapshot,ref)


def test_worker_initial_mismatch_prevents_execution_and_restores_base(tmp_path,monkeypatch):
    value=manifest();value.update(files={},source_run=str(tmp_path/'source'))
    snapshot={'x':torch.tensor([1.])};ref=snapshot_reference(tmp_path,snapshot)
    value['kl_reference']['snapshots']={r['episode_id']:ref for r in value['expected']}
    atomic_json(tmp_path/'manifest.json',value)
    monkeypatch.setattr(kl,'check_source',lambda source:{})
    monkeypatch.setattr(kl.base,'initial_snapshot',lambda env,geometry:{'x':torch.tensor([2.])})
    before=kl.base.initial_snapshot;budget=kl.base.EvalBudget;executions=[]
    def fake_worker(run):
        kl.base.initial_snapshot(None,None)
        executions.append(True)
    monkeypatch.setattr(kl.base,'worker',fake_worker)
    with pytest.raises(ValueError,match='before execution'):kl.worker(tmp_path)
    assert executions==[] and kl.base.initial_snapshot is before and kl.base.EvalBudget is budget


def setup_report(tmp_path,monkeypatch,*,complete=False,status='incomplete_budget'):
    import task10_validation_audit_v2 as audit
    value=manifest();reference=tmp_path/'old';value['kl_reference']['run']=str(reference)
    value.update(files={},source_run=str(tmp_path/'source'),source_objective_check={},initial_weight_comparison={'equal':True})
    for row in identities():atomic_json(reference/'episodes'/(row['episode_id']+'.json'),dict(row,complete=True,strict_success=False))
    for row in value['expected']:
        value['kl_reference']['snapshots'][row['episode_id']]={'tree_sha256':kl.base.tree_hash({'x':1})}
        if complete:
            atomic_json(tmp_path/'episodes'/(row['episode_id']+'.json'),dict(row,complete=True,strict_success=False,decisions=1,reason='stall_limit'))
            torch_path=tmp_path/'initial'/(row['episode_id']+'.pt');torch_path.parent.mkdir(exist_ok=True);torch.save({'x':1},torch_path)
    budget=dict(max_episodes=12,max_decisions=1800,max_updates=0,max_seconds=5400,updates=0,
        completed_decisions=12 if complete else 0,reserved_decisions=12 if complete else 0,in_flight=0,
        started_epoch=1.,deadline_epoch=5401.,started_monotonic=2.,deadline_monotonic=5402.,
        completed_episodes=12 if complete else 0,started_episodes=12 if complete else 0,wall_seconds=1.,status=status)
    atomic_json(tmp_path/'budget.json',budget);atomic_json(tmp_path/'summary.json',{'status':status})
    atomic_json(tmp_path/'launch.json',{'status':'process_exited','returncode':0})
    atomic_json(tmp_path/'manifest.json',value)
    monkeypatch.setattr(kl,'check_source',lambda path:{})
    monkeypatch.setattr(audit,'decision_checks',lambda *args:([],{}))
    monkeypatch.setattr(audit,'snapshot_checks',lambda *args:([],{}))
    monkeypatch.setattr(audit,'weights_checks',lambda *args:([],{'weights':{'updates':0}}))


def test_partial_report_keeps_fixed_denominator_and_missing(tmp_path,monkeypatch):
    setup_report(tmp_path,monkeypatch)
    result=kl.report(tmp_path)
    assert result['status']=='verified_partial' and result['scores']['expected']==12
    assert result['scores']['missing']==12 and len(result['missing'])==12
    assert result['paired']['new_trained_vs_old_uniform']['missing']==12


@pytest.mark.parametrize('problem',['failed_status','launcher_rc','inflight','summary_status'])
def test_full_rows_cannot_hide_failed_worker_or_launcher(tmp_path,monkeypatch,problem):
    setup_report(tmp_path,monkeypatch,complete=True,status='failed' if problem=='failed_status' else 'complete')
    filename={'launcher_rc':'launch.json','inflight':'budget.json','summary_status':'summary.json'}.get(problem)
    if filename:
        value=json.loads((tmp_path/filename).read_text())
        value[{'launcher_rc':'returncode','inflight':'in_flight','summary_status':'status'}[problem]]=1 if problem!='summary_status' else 'failed'
        atomic_json(tmp_path/filename,value)
    result=kl.report(tmp_path)
    assert result['scores']['completed']==12 and result['status']=='failed' and result['issues']


def test_full_report_requires_clean_completion(tmp_path,monkeypatch):
    setup_report(tmp_path,monkeypatch,complete=True,status='complete')
    result=kl.report(tmp_path)
    assert result['status']=='verified_complete' and result['no_updates']
    assert result['scores']['missing']==0 and all(result['initial_hash_match'].values())
