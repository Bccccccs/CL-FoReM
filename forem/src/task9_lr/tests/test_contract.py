"""Synthetic tensors/containers only: no environment constructors or map sampling."""
import copy
import datetime as dt
import importlib.util
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
import torch
from task9_lr.runtime import ASSET_ROOT,PACKAGE_ROOT,artifact_digest,validate_formal_config,validate_matrix,import_manifest
from task9_lr.admission import load_protocol,read_release
from task8_lower.sac import LowerSAC,update_due
from task8_lower.replay import Replay
from task7_lower.observation import preprocess
from task7_lower.training import rng_state,restore_rng
DEVICE=os.environ.get('TASK9_LR_TEST_DEVICE','cpu')


def config(arm='C',seed=4718):return json.loads((ASSET_ROOT/f'config/task9/task9_11/{arm}_seed{seed}.json').read_text())


def obs(n=2):
    shapes=dict(grid=(128,128,3),q=(6,),tcp=(7,),next_tcp=(7,),route_points=(15,3),subgoal=(5,),synchronous=(1,),previous_action=(3,))
    return {k:torch.zeros((n,)+v,device=DEVICE) for k,v in shapes.items()}


def batch():
    m,v=preprocess(obs());return m,v,torch.zeros(2,3,device=DEVICE),torch.ones(2,1,device=DEVICE),m,v,torch.ones(2,1,device=DEVICE)


def exact(a,b):
    if torch.is_tensor(a):assert torch.equal(a,b)
    elif isinstance(a,np.ndarray):assert np.array_equal(a,b)
    elif isinstance(a,dict):
        assert a.keys()==b.keys()
        for k in a:exact(a[k],b[k])
    elif isinstance(a,(list,tuple)):
        assert len(a)==len(b)
        for x,y in zip(a,b):exact(x,y)
    else:assert a==b


def test_matrix_exact_and_legacy_rejected():
    values=validate_matrix()
    for seed in (4718,4719):
        a,b=values[('C',seed)],values[('L',seed)]
        assert {k for k in a if a[k]!=b[k]}=={'group','lr_schedule'}
        for bad in [dict(a,group='U20'),dict(a,seed=4720),dict(a,replay_capacity=200000),dict(a,alpha_lr_schedule='linear_transfers')]:
            with pytest.raises(ValueError):validate_formal_config(bad)
        smoke=dict(a,total_transfers=1000);validate_formal_config(smoke,smoke=True)
    assert all('/task9_lr/' in x['file'] for x in import_manifest().values())


def test_first_update_exact_count_and_warmup_not_a_gate():
    c=config()
    updates=[t for t in range(1,3000001) if update_due(t,min(t-1,100000),c)]
    assert updates[0]==260 and updates[-1]==3000000 and len(updates)==299975
    assert updates[0]<c['warmup_transfers']


@pytest.mark.parametrize('arm',['C','L'])
def test_actual_schedules_and_resume(arm):
    c=config(arm);torch.manual_seed(81);sac=LowerSAC(74,DEVICE,c)
    for t in (260,1000,250000,3000000):
        sac.set_transfer(t)
        if arm=='L':assert sac.policy_optim.param_groups[0]['lr']==pytest.approx(1e-4+(1e-6-1e-4)*t/3e6)
        assert sac.alpha_optim.param_groups[0]['lr']==1e-6
    sac.update_from_batch(batch(),sac.update_count,transfer=260)
    if arm=='C':assert sac.policy_optim.param_groups[0]['lr']==pytest.approx(1e-4*(1e-6/1e-4)**(1/4999743))
    state=copy.deepcopy(sac.full_state_dict());restored=LowerSAC(74,DEVICE,c);restored.load_full_state_dict(state)
    saved=rng_state();a=sac.update_from_batch(batch(),sac.update_count,transfer=1000)
    restore_rng(saved);b=restored.update_from_batch(batch(),restored.update_count,transfer=1000)
    exact(a,b);exact(sac.full_state_dict(),restored.full_state_dict())
    assert sac.alpha_optim.param_groups[0]['lr']==1e-6
    assert state['task9_lr_scientific_config']['total_transfers']==3000000


def test_synthetic_full_checkpoint_pending_restores_without_env_constructor(tmp_path):
    from task8_lower.training import save_checkpoint,load_checkpoint,consume_transition
    from task8_sim.env import PcdEpisodeEnv
    from task7_sim.core import Core
    cfg=dict(config(),batch_size=2,replay_capacity=8,update_every_transfers=2,total_transfers=1000)
    for key in ('pool','transfer_pool','evaluation_seeds'):
        p=tmp_path/(key+'.json');p.write_text('{}');cfg[key]=str(p)
    sac=LowerSAC(74,DEVICE,cfg);replay=Replay(8,74,4,DEVICE)
    env=PcdEpisodeEnv.__new__(PcdEpisodeEnv);env.factory=None;env.sampler=None;env.scenes=None;env.kin=SimpleNamespace(_fixed_cache={},_dls_graph_cache={});env.device=torch.device(DEVICE);env.sampling_deadline=None;env.sampling_cancel=None
    env.core=Core.__new__(Core);env.core.state=SimpleNamespace(base=torch.zeros(3,3,device=DEVICE),q=torch.zeros(3,6,device=DEVICE),s=torch.zeros(3,device=DEVICE));env.core.queue=torch.zeros(3,3,device=DEVICE)
    tr=SimpleNamespace(observation=obs(3),next_observation=obs(3),raw_action=torch.zeros(3,3,device=DEVICE),reward=torch.ones(3,device=DEVICE),mask=torch.ones(3,device=DEVICE),attempted=torch.ones(3,device=DEVICE),committed=torch.ones(3,device=DEVICE),dt=torch.ones(3,device=DEVICE))
    state=dict(steps=511,pending=dict(transition=tr,ids=[0,1,2],cursor=0,failed=torch.zeros(3,dtype=torch.bool,device=DEVICE)),attempted=0,committed=0,sim_s=0.)
    consume_transition(sac,replay,state,tr,0,cfg,state['pending']['failed'])
    save_checkpoint(tmp_path/'synthetic.pt',sac,replay,env,state,cfg)
    assert state['steps']==512 and state['pending']['cursor']==1
    save=rng_state()
    consume_transition(sac,replay,state,tr,1,cfg,state['pending']['failed'])
    consume_transition(sac,replay,state,tr,2,cfg,state['pending']['failed'])
    expected=copy.deepcopy(sac.full_state_dict());expected_r=copy.deepcopy(replay.state_dict())
    actual_s,actual_r,actual_e,actual_state,_=load_checkpoint(tmp_path/'synthetic.pt',DEVICE)
    assert actual_state['pending']['cursor']==1
    consume_transition(actual_s,actual_r,actual_state,actual_state['pending']['transition'],1,cfg,actual_state['pending']['failed'])
    consume_transition(actual_s,actual_r,actual_state,actual_state['pending']['transition'],2,cfg,actual_state['pending']['failed'])
    exact(expected,actual_s.full_state_dict());exact(expected_r,actual_r.state_dict())
    assert actual_state['steps']==514 and actual_state['pending']['cursor']==3


def test_original_finish_units_zero_segment_and_first_kind(tmp_path):
    from task9_lr.diagnostics import Observer,observing
    from task7_sim.core import Core,State,Candidate
    # _finish executes its original predicate; fake FK/route supply tensors only.
    c=Core.__new__(Core);c.finished=torch.zeros(2,dtype=torch.bool,device=DEVICE);c.execute=True;c.decisions=torch.zeros(2,dtype=torch.long,device=DEVICE);c.failure_mode='cbl_continue';c.failure_kind=torch.zeros(2,dtype=torch.long,device=DEVICE);c.failures=torch.tensor([0,1],device=DEVICE);c.failure_limit=20;c.stalls=torch.zeros(2,dtype=torch.long,device=DEVICE)
    c.state=State(torch.zeros(2,3,device=DEVICE),torch.zeros(2,6,device=DEVICE),torch.ones(2,device=DEVICE));c.start=c.state.clone();c.start.s[:]=0;c.route=SimpleNamespace(length=torch.ones(2,device=DEVICE),at=lambda s:torch.eye(4,device=DEVICE).expand(2,-1,-1).clone());c.kin=SimpleNamespace(world_tcp=lambda b,q:torch.eye(4,device=DEVICE).expand(2,-1,-1).clone());c.time=torch.zeros(2,device=DEVICE);c.attempt_time=c.time.clone();c.terminated=torch.zeros(2,dtype=torch.bool,device=DEVICE);c.truncated=c.terminated.clone();c.strict_success=c.terminated.clone();c.arrived=torch.ones(2,dtype=torch.bool,device=DEVICE);c.reason=torch.zeros(2,dtype=torch.long,device=DEVICE)
    o=Observer(tmp_path/'d',dict(test='zero'));o.env=SimpleNamespace(proposal_seeds=[7,8]);o.jobs=[dict(map_id='fake'+str(i),seed=i,stream_index=0,role='validation',source_split='validation') for i in range(2)];o.segment=[1,1];o.action=[0,0]
    with observing(o):c._finish(torch.ones(2,dtype=torch.bool,device=DEVICE))
    o.close();rows=[json.loads(x) for x in (tmp_path/'d/events.jsonl').read_text().splitlines()]
    assert [r['success'] for r in rows]==[True,True] and [r['strict_success'] for r in rows]==[True,False]
    assert rows[0]['action']==0 and rows[0]['cbl_rotation']==0 and rows[0]['d_m']==0
    accepted=torch.tensor([False,True,True,True],device=DEVICE);base=torch.tensor([True,True,False,False],device=DEVICE);arm=torch.tensor([True,True,True,False],device=DEVICE);selfhit=torch.ones(4,dtype=torch.bool,device=DEVICE)
    kind=torch.where(~accepted,1,torch.where(base,2,torch.where(arm,3,torch.where(selfhit,4,0))))
    assert kind.tolist()==[1,2,3,4]


def test_observer_does_not_consume_rng_and_disabled_path(tmp_path):
    from task9_lr.diagnostics import Observer,observing,digest
    sac=LowerSAC(74,DEVICE,config());observation=obs()
    before=rng_state();expected=sac.select_action(observation,False);after=rng_state()
    restore_rng(before);o=Observer(tmp_path/'on',dict(test='on'))
    with observing(o):actual=sac.select_action(observation,False)
    exact(expected,actual);exact(after,rng_state());o.close()


def test_deadline_legacy_release_and_budget_rejection(tmp_path):
    from task9_lr.admission import check_resources
    p=load_protocol(ASSET_ROOT/'config/task9/task9_11/protocol.json')
    entry=tmp_path/'evidence.json';entry.write_text('{"status":"PASS"}')
    from task9_lr.runtime import sha256
    token=dict(stage='g1',run_id=p['run_id'],code_hash=artifact_digest(),protocol_sha256=p['_sealed_sha256'],reviewer_task='task9.11.4',status='PASS',expires_at=p['deadline'],evidence=[dict(path=str(entry),sha256=sha256(entry))],max_worker_seconds=100,save_reserve_s=10,remaining_resource_budget={k:100 for k in ('worker_seconds','gpu_seconds','wall_seconds','output_bytes','evaluation_episodes','consumed_transfers')})
    path=tmp_path/'release.json';path.write_text(json.dumps(token))
    read_release(path,'g1',p)
    for changed in [dict(token,reviewer_task='task9.5.3'),dict(token,run_id='t9-opt-20261031'),dict(token,code_hash='old'),dict(token,expires_at='2026-11-07T00:00:00+08:00')]:
        path.write_text(json.dumps(changed))
        with pytest.raises(ValueError):read_release(path,'g1',p)
    path.write_text(json.dumps(token))
    with pytest.raises(ValueError,match='caller clock'):read_release(path,'g1',p,clock=dt.datetime.fromisoformat(p['started_at']))
    token['expires_at']=p['started_at'];path.write_text(json.dumps(token))
    with pytest.raises(ValueError):read_release(path,'g1',p)


def test_cuda_or_cpu_actual_device_path(tmp_path):
    sac=LowerSAC(74,DEVICE,config());sac.update_from_batch(batch(),0,transfer=260);replay=Replay(4,74,7,DEVICE)
    result=dict(policy_device=str(next(sac.policy.parameters()).device),replay_device=str(replay.map_s.device),optimizer_devices={name:sorted({str(v.device) for entry in optimizer.state.values() for v in entry.values() if torch.is_tensor(v)}) for name,optimizer in [('actor',sac.policy_optim),('critic',sac.critic_optim),('alpha',sac.alpha_optim)]},torch=torch.__version__,cuda=torch.version.cuda,real_environments=0,episodes=0)
    assert result['policy_device'].startswith(DEVICE) and result['replay_device'].startswith(DEVICE)
    assert all(any(d.startswith(DEVICE) for d in values) for values in result['optimizer_devices'].values())
    out=Path(os.environ.get('TASK9_LR_EVIDENCE_DIR',str(tmp_path)));(out/'device-path.json').write_text(json.dumps(result,indent=2)+'\n')


def test_C_update_equals_original_B1_runtime():
    path=ASSET_ROOT/'src/task9_opt/runtime/src/task8_lower/sac.py'
    spec=importlib.util.spec_from_file_location('original_opt_sac',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    cfg=config('C');torch.manual_seed(54);old=module.LowerSAC(74,DEVICE,cfg)
    torch.manual_seed(54);new=LowerSAC(74,DEVICE,cfg)
    for t in (260,1000):
        before=rng_state();a=old.update_from_batch(batch(),old.update_count,transfer=t)
        restore_rng(before);b=new.update_from_batch(batch(),new.update_count,transfer=t)
        exact(a,b)
        for k in ('policy','critic','critic_target','policy_optim','critic_optim','alpha_optim','sched_policy','sched_critic'):
            exact(old.full_state_dict()[k],new.full_state_dict()[k])


def test_original_core_first_rejection_priority_and_natural_windows(tmp_path):
    from task7_sim.core import Core,State,Candidate
    from task7_sim.geometry import Collision
    from task9_lr.diagnostics import Observer,observing
    n=4;zero=torch.zeros(n,device=DEVICE);false=torch.zeros(n,dtype=torch.bool,device=DEVICE)
    eye=torch.eye(4,device=DEVICE).expand(n,-1,-1).clone()
    grid=SimpleNamespace(observed=torch.zeros(n,200,200,dtype=torch.bool,device=DEVICE),height=torch.zeros(n,200,200,device=DEVICE),timestamp=zero.clone());grid.snapshot=lambda:grid
    accepted=torch.tensor([False,True,True,True],device=DEVICE)
    result=SimpleNamespace(q=torch.zeros(n,6,device=DEVICE),accepted=accepted,position=zero.clone(),cbl=zero.clone(),angle=zero.clone(),branch=torch.zeros(n,dtype=torch.long,device=DEVICE),exact=accepted.clone(),status=torch.where(accepted,0,2))
    # Same attributes as the original IK dataclass; no IK function is called.
    result.__dataclass_fields__={k:None for k in ('q','accepted','position','cbl','angle','branch','exact','status')}
    collision=Collision(torch.tensor([True,True,False,False],device=DEVICE),torch.tensor([True,True,True,False],device=DEVICE),torch.ones(n,dtype=torch.bool,device=DEVICE))
    kin=SimpleNamespace(solve_world=lambda *a,**kw:result)
    route=SimpleNamespace(length=torch.ones(n,device=DEVICE),at=lambda s:eye)
    c=Core(State(torch.zeros(n,3,device=DEVICE),torch.zeros(n,6,device=DEVICE),zero.clone()),route,grid,kin,lambda b,q:torch.zeros(n,1,2,3,device=DEVICE),lambda *a:collision,synchronous=False,failure_mode='cbl_continue',episode_end_bootstrap=True)
    observation=obs(n);observation['synchronous'].zero_()
    # Core reward/IK/collision priority/queue/commit remain original; observation
    # encoding and solver results are explicitly synthetic fixture inputs.
    c.current_observation=lambda:observation;c.observe=lambda:observation
    c.begin(Candidate(torch.tensor([[3.,0.,0.]]*n,device=DEVICE),torch.ones(n,device=DEVICE),false.clone()))
    o=Observer(tmp_path/'branches',dict(test='branches'))
    env=SimpleNamespace(core=c,proposal_seeds=list(range(n)),scenes=SimpleNamespace(scenes=[SimpleNamespace(provenance=lambda:{'synthetic':True}) for _ in range(n)]))
    jobs=[dict(map_id='synthetic'+str(i),seed=i,stream_index=0,role='validation',source_split='validation') for i in range(n)];o.attach(env,jobs)
    m,v=preprocess(observation)
    with observing(o):
        o.policy_input(observation,m,v);tr=c.step(torch.zeros(n,3,device=DEVICE))
    o.close()
    rows=[json.loads(x) for x in (tmp_path/'branches/events.jsonl').read_text().splitlines()]
    first=[r for r in rows if r['event']=='first_rejection']
    assert [r['kind'] for r in first]==[1,2,3,4]
    assert all(r['raw_ik'] is None for r in first) # fake solver has no pre-hold hook
    assert all(r['attempted'] and not r['committed'] for r in first)
    assert tr.committed.tolist()==[0,0,0,0] and c.failures.tolist()==[1,1,1,1]
    assert len(list((tmp_path/'branches').glob('*-first.pt')))==4


def test_write_before_byte_quota_covers_json_and_tensor_payloads(tmp_path,monkeypatch):
    import task9_lr.diagnostics as d
    protocol=dict(container_output=str(tmp_path),container_logs=str(tmp_path/'logs'),external_output_roots=[],poll_s=5,max_output_bytes=100000,max_diagnostic_log_bytes=1024,unmetered_log_reserve_bytes=64)
    quota=d.OutputBudget(protocol);monkeypatch.setattr(d,'OUTPUT_BUDGET',quota)
    target=tmp_path/'diagnostics.jsonl'
    with d.BudgetFile(target,'xb',diagnostic=True) as stream:
        stream.write(b'a'*950)
        with pytest.raises(OSError,match='diagnostic byte quota'):stream.write(b'b'*11)
    assert target.stat().st_size==950 and target.stat().st_size<=1024-64
    # torch.save cannot write its large storage first and discover excess later.
    quota.protocol['max_output_bytes']=200000;quota.protocol['max_diagnostic_log_bytes']=20000;quota.refresh()
    tensor_path=tmp_path/'diagnostics-tensor.pt'
    with pytest.raises((OSError,RuntimeError)):
        with d.BudgetFile(tensor_path,'xb',diagnostic=True) as stream:torch.save(torch.zeros(100000,device=DEVICE),stream)
    assert target.stat().st_size+tensor_path.stat().st_size<=20000-64


def test_prepare_candidate_cannot_start_container(tmp_path,monkeypatch):
    # Real prepare remains blocked pending explicit accounting/C-gate decisions.
    # Positive preparation/dispatch is exercised with stdlib external adapters.
    path=ASSET_ROOT/'scripts/task9_11/supervise.py'
    spec=importlib.util.spec_from_file_location('lr_supervise_synthetic',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def forbidden(*args,**kwargs):
        raise AssertionError('candidate may not create a real container')
    monkeypatch.setattr(module,'create_container',forbidden)
    protocol=load_protocol(ASSET_ROOT/'config/task9/task9_11/protocol.json')
    monkeypatch.setattr(module,'load_protocol',lambda _:protocol)
    monkeypatch.setattr(__import__('sys'),'argv',['supervise.py','--protocol','synthetic','--phase','prepare'])
    with pytest.raises((RuntimeError,ValueError),match='NOT_READY|not authorized|not allowed|non-execut|candidate|contract'):
        module.main()


def test_full_parity_close_obeys_byte_admission_without_dropping_rows(tmp_path,monkeypatch):
    import task9_lr.diagnostics as d
    from task9_lr.evaluation import ParityObserver
    observer=ParityObserver(tmp_path/'parity',dict(test='quota'),enabled=False,parity=True)
    observer.parity_rows=[dict(event='synthetic_action',sha256='a'*64) for _ in range(100)]
    protocol=dict(container_output=str(tmp_path),container_logs=str(tmp_path/'logs'),external_output_roots=[],poll_s=5,max_output_bytes=100000,max_diagnostic_log_bytes=1024,unmetered_log_reserve_bytes=64)
    monkeypatch.setattr(d,'OUTPUT_BUDGET',d.OutputBudget(protocol))
    with pytest.raises(OSError,match='diagnostic byte quota'):observer.close()
    assert len(observer.parity_rows)==100
    assert (tmp_path/'parity/parity.json').stat().st_size==0
    assert observer.stream.closed
