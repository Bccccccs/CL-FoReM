"""Regression tests for independent review F1/F2/F3; CPU only, no experiment."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from task9_opt import admission
from task9_opt.runtime import ASSET_ROOT


def module(name):
    spec=importlib.util.spec_from_file_location(name,ASSET_ROOT/f'scripts/task9_opt_{name}.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def save_fixture():
    cost=dict(save_max_s=240.)
    summary=dict(timings={k:dict(max_s=v) for k,v in {'checkpoint':240.,'environment_step':12.,'consume_transition':3.,'validation':3000.}.items()})
    policy=dict(save_allowance_s=60.,cancellation_drain_bound_s=300.,emergency_margin_s=30.)
    return cost,summary,policy


def test_f1_mature_saving_cannot_exceed_deadline_guard():
    # The old continuation path accepted cp240 against policy60. It must stop
    # with NOT_READY, not change3M or silently increase the guard/deadline.
    cost,summary,policy=save_fixture()
    result=admission.save_readiness(cost,summary,policy)
    assert result['status']=='NOT_READY_save_allowance'
    assert result['required_allowance_s']==570. and result['policy_allowance_s']==60.
    assert policy['save_allowance_s']==60. and admission.STOP_AT.isoformat()=='2026-11-02T07:00:00+08:00'
    policy['save_allowance_s']=570.
    assert admission.save_readiness(cost,summary,policy)['status']=='ready'
    assert admission.save_readiness(cost,summary,policy)['observed_chain_floor_s']==255.
    policy['cancellation_drain_bound_s']=254.
    assert admission.save_readiness(cost,summary,policy)['status']=='NOT_READY_cancellation_bound'


@pytest.mark.parametrize('kind,reason',[('interrupted','STOP file'),('diverged','Q maximum exceeds 10 times 500k reference')])
def test_f2_checkpoint_terminal_kind_reason_and_evidence_are_preserved(tmp_path,kind,reason):
    queue=module('queue')
    (tmp_path/f'{kind}.pt').write_bytes(b'fixture checkpoint marker; not torch/model data')
    (tmp_path/f'{kind}.meta.json').write_text(json.dumps(dict(steps=250001,stop_reason=reason,resume_safe=kind=='interrupted')))
    result=queue.classify_terminal(tmp_path,1)
    assert result['status']==kind and result['stop_reason']==reason
    assert Path(result['checkpoint']['path']).name==f'{kind}.pt'
    assert result['metadata']['sha256']==admission.sha256(tmp_path/f'{kind}.meta.json')
    assert result['retry_allowed'] is False


def test_f2_launch_unknown_and_recognized_worker_exceptions_are_distinct(tmp_path):
    queue=module('queue')
    assert queue.classify_terminal(tmp_path,1)['status']=='unknown_worker_failure'
    assert queue.classify_terminal(tmp_path,None,launch_error='Popen failed')['status']=='launch_failed'
    (tmp_path/'worker-terminal.json').write_text(json.dumps(dict(status='interrupted',stop_reason='evaluation wall budget reached',exception_type='TimeoutError')))
    value=queue.classify_terminal(tmp_path,1)
    assert value['status']=='interrupted' and value['exception_type']=='TimeoutError'
    assert value['stop_reason']=='evaluation wall budget reached'


def test_f3_late_g1_never_launches_subprocess_and_writes_not_ready(tmp_path,monkeypatch):
    worker=module('worker');calls=[]
    monkeypatch.setattr(worker,'clock_now',lambda:admission.STOP_AT-dt.timedelta(seconds=1))
    monkeypatch.setattr(worker.subprocess,'run',lambda *a,**k:calls.append(k) or SimpleNamespace(returncode=0))
    result=worker.run_g1(tmp_path,1800,dict(max_worker_s=1800,expires_at=admission.STOP_AT.isoformat()),'0')
    assert result==126 and calls==[]
    evidence=json.loads((tmp_path/'g1-result.json').read_text())
    assert evidence['status']=='NOT_READY_deadline' and evidence['subprocess_started'] is False


def test_f3_near_deadline_g1_timeout_reserves_cleanup_and_evidence(tmp_path,monkeypatch):
    worker=module('worker');timeouts=[]
    clock=admission.STOP_AT-dt.timedelta(seconds=70)
    monkeypatch.setattr(worker,'clock_now',lambda:clock)
    def run(*args,**kwargs):
        timeouts.append(kwargs['timeout'])
        (tmp_path/'device-path.json').write_text(json.dumps(dict(policy_device='cuda:0',replay_device='cuda:0')))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(worker.subprocess,'run',run)
    assert worker.run_g1(tmp_path,1800,dict(max_worker_s=1800,expires_at=admission.STOP_AT.isoformat()),'0')==0
    assert timeouts==[60.]  #70 remaining−existing10 cleanup/evidence seconds
    assert clock+dt.timedelta(seconds=timeouts[0]+10)<=admission.STOP_AT


def test_f1_actual_profile_exit_becomes_not_ready_without_continuation(tmp_path):
    queue=module('queue')
    summary=dict(status='paused_profile',steps=250000,scientific_limit=3000000,env_actions=250112,
        pending=dict(ids=list(range(256)),cursor=144),validation_pending=None,replay_size=200000,replay_capacity=200000,
        policy_device='cuda:0',replay_device='cuda:0',optimizer_devices={k:['cpu','cuda:0'] for k in ('actor','critic','alpha')},
        timings={'checkpoint':{'max_s':240.},'validation':{'max_s':3000.},'consume_transition':{'max_s':3.},'environment_step':{'max_s':12.}},
        mature_window=dict(transfers=50000,wall_s=4200.,checkpoint_s=480.,evaluation_s=3000.))
    evaluation=dict(complete=True,validation=dict(episodes=100,complete=True),transfer=dict(episodes=96,complete=True))
    (tmp_path/'profile-summary.json').write_text(json.dumps(summary))
    (tmp_path/'validation-0250000.json').write_text(json.dumps(evaluation))
    config=tmp_path/'config.json';config.write_text(json.dumps(dict(total_transfers=3000000,replay_capacity=200000)))
    run=dict(output=str(tmp_path),config=str(config),status='running_profile')
    policy=dict(save_allowance_s=60.,cancellation_drain_bound_s=300.,emergency_margin_s=30.,profile_cost_multiplier=1.1,profile_restore_allowance_s=300.)
    assert queue.process_formal_exit(run,dict(exit_code=0,phase='profile'),policy) is False
    assert run['status']=='NOT_READY_save_allowance' and 'estimated_remaining_s' not in run
    policy['save_allowance_s']=570.
    assert queue.process_formal_exit(run,dict(exit_code=0,phase='profile'),policy) is False
    assert run['status']=='profiled' and run['estimated_remaining_s']>=39600
    assert json.loads(config.read_text())['total_transfers']==3000000


@pytest.mark.parametrize('kind,reason',[('interrupted','STOP file'),('diverged','nonfinite SAC losses/Q/policy')])
def test_f2_actual_exit_handler_preserves_terminal_and_quarantines(tmp_path,kind,reason):
    queue=module('queue')
    (tmp_path/f'{kind}.pt').write_bytes(b'fixture')
    (tmp_path/f'{kind}.meta.json').write_text(json.dumps(dict(steps=500001,stop_reason=reason)))
    run=dict(output=str(tmp_path),status='running_remaining')
    assert queue.process_formal_exit(run,dict(exit_code=1,phase='remaining'),{}) is True
    assert run['status']==kind and run['terminal']['stop_reason']==reason
    assert run['terminal']['retry_allowed'] is False


def test_f2_real_stop_checkpoint_metadata_keeps_original_reason(tmp_path):
    from task8_lower import training
    assert Path(training.__file__).resolve().is_relative_to(ASSET_ROOT/'src/task9_opt/runtime/src')
    train=training.train
    from test_requirements import cfg
    queue=module('queue')
    config=dict(cfg(),device='cpu',environments=1,batch_size=2,replay_capacity=4,dls_cuda_graph=False)
    (tmp_path/'STOP').touch()
    with pytest.raises(InterruptedError,match='STOP file'):train(config,tmp_path)
    value=queue.classify_terminal(tmp_path,1)
    assert value['status']=='interrupted' and value['stop_reason']=='STOP file'
    assert value['steps']==0 and value['resume_safe'] is True


def test_new_entry_imports_preserve_isolated_package_priority():
    for name in ('queue','worker','monitor'):module(name)
    import task8_lower.training
    assert Path(task8_lower.training.__file__).resolve().is_relative_to(ASSET_ROOT/'src/task9_opt/runtime/src')


def test_f2_corrupt_terminal_artifact_is_unknown_not_a_known_scientific_failure(tmp_path):
    queue=module('queue')
    (tmp_path/'worker-terminal.json').write_text('{incomplete')
    result=queue.classify_terminal(tmp_path,1)
    assert result['status']=='unknown_worker_failure' and result['retry_allowed'] is False
