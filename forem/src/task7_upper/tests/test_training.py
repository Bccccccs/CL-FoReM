"""TASK7.22 tests. Synthetic tensors never assert environment adapter semantics."""
from copy import deepcopy
import math
import os
import pytest
import torch
from task7_upper.model import UpperModel
from task7_upper.replay import SequenceReplay, exact_cpu, row
from task7_upper.sac_discrete import bellman, distribution, CappedTemperature, DiscreteSAC
from task7_upper.fp_trainer import FPTrainer, fit_g3_alignment, split_episodes, prediction_diagnostics
from task7_upper.stages import enter_stage, sequence_outputs, save_checkpoint, load_checkpoint
from task7_upper.evaluate import ValidationSelector, evaluate_maps
from task7_lower.observation import encode_grid, decode_grid


def transition(t, terminal=False):
    return dict(decision_index=t, terminated=torch.tensor(terminal), truncated=torch.tensor(False),
                selected=torch.tensor(0), reward=torch.tensor(1.), dt=torch.tensor(.1),
                candidates=dict(mask=torch.tensor([True,False])),
                next_candidates=dict(mask=torch.tensor([False,True])), arrival_label_valid=torch.tensor(True))


def replay_fixture():
    r = SequenceReplay(1000, seed=722)
    for ep in range(40):
        for t in range(8):
            r.append(('run',0,ep), transition(t, t==7))
    return r


def model_fixture(stage='1', asynchronous=False):
    torch.manual_seed(722)
    m = UpperModel(vector_dim=12, asynchronous=asynchronous)
    m.set_stage(stage)
    return m


def candidate_fixture(n=4, asynchronous=False):
    g = torch.randn(n,3,7 if asynchronous else 6)
    f = torch.randn(n,3,19); f[...,8] = 2.
    mask = torch.tensor([True,True,False]).expand(n,-1).clone()
    return g,f,mask


def test_replay_episodes_capacity_readiness_and_resume():
    r = replay_fixture()
    assert not r.ready(999) and r.ready(1000)
    samples = r.sample()
    assert len(samples)==32 and all([int(x['decision_index']) for x in seq]==list(range(8)) for seq in samples)
    assert all(not bool(x['terminated']) for seq in samples for x in seq[:-1])
    state = r.state_dict(); expected = r.sample()
    new = SequenceReplay(1000); new.load_state_dict(state)
    assert [[int(x['decision_index']) for x in seq] for seq in expected] == [[int(x['decision_index']) for x in seq] for seq in new.sample()]
    with pytest.raises(ValueError, match='episode end'): r.append(('run',0,0), transition(8))
    r = SequenceReplay(10)
    for t in range(20): r.append('a', transition(t))
    assert len(r)==10 and [int(x['decision_index']) for x in r.episodes['a']]==list(range(10,20))
    assert len(r.starts())==3


def test_exact_uint8_and_next_candidate_not_latents():
    grid=torch.rand(1,128,128,3); grid[...,0]=1; grid[...,2]=0
    data=exact_cpu(dict(observation=dict(grid=grid)))
    assert 'grid' not in data['observation']
    assert data['observation']['grid_uint8'].dtype==torch.uint8
    assert torch.equal(decode_grid(data['observation']['grid_uint8']),decode_grid(encode_grid(grid)))
    r=SequenceReplay(); r.append('a',transition(0))
    assert torch.equal(r.episodes['a'][0]['next_candidates']['mask'],torch.tensor([False,True]))
    with pytest.raises(ValueError,match='latent'): r.append('b',dict(transition(0),hidden=torch.zeros(128)))


def test_hand_bellman_dt_terminal_truncation_and_padding_nan():
    logits=torch.tensor([[0.,0.,float('nan')]]).expand(3,-1)
    q1=torch.tensor([[2.,4.,float('nan')]]).expand(3,-1)
    q2=torch.tensor([[3.,3.,float('nan')]]).expand(3,-1)
    mask=torch.tensor([[True,True,False]]).expand(3,-1)
    y=bellman(torch.tensor([1.,1.,1.]),torch.tensor([False,True,False]),torch.tensor([.1,.1,.05]),logits,q1,q2,mask,.35)
    v=2.5+.35*math.log(2)
    torch.testing.assert_close(y,torch.tensor([1+.99*v,1.,1+.99**.5*v]))
    p,l=distribution(logits,mask)
    assert torch.isfinite(l).all() and (p[:,2]==0).all()
    # The first and last can be truncated; only terminated suppresses bootstrap.
    with pytest.raises(ValueError): distribution(torch.zeros(1,2),torch.zeros(1,2,dtype=torch.bool))


def test_capped_temperature_and_entropy_sign():
    p=torch.tensor([[.9,.1]]); logp=p.log(); mask=torch.ones_like(p,dtype=torch.bool)
    a=CappedTemperature('cpu'); before=float(a.alpha)
    a.update(p,logp,mask)
    assert float(a.alpha)>before  # low entropy increases alpha using specified CBL sign
    with torch.no_grad(): a.log_alpha.fill_(-3.)
    a.update(p,logp,mask)
    assert a.fixed and float(a.alpha)==pytest.approx(.05)
    saved=a.log_alpha.detach().clone(); assert a.update(p,logp,mask)==0
    assert torch.equal(saved,a.log_alpha)
    b=CappedTemperature('cpu'); b.load_state_dict(a.state_dict()); assert b.fixed


@pytest.mark.parametrize('asynchronous',[False,True])
def test_stage_entry_and_g3_fixed_alignment(asynchronous):
    m=model_fixture(asynchronous=asynchronous); g,f,mask=candidate_fixture(asynchronous=asynchronous)
    report=enter_stage(m,'3',torch.randn(4,128),g,f,mask)
    assert report['atol']==1e-6
    h=torch.randn(50,128); z=torch.randn(50,128)
    scale,shift=fit_g3_alignment(m.random_world_model,h,z)
    aligned=z*scale+shift
    torch.testing.assert_close(aligned.mean(0),h.mean(0),atol=1e-6,rtol=1e-6)
    torch.testing.assert_close(aligned.std(0,unbiased=False),h.std(0,unbiased=False))
    with pytest.raises(RuntimeError): fit_g3_alignment(m.random_world_model,h,z)
    n=model_fixture()
    scale,shift=fit_g3_alignment(n.random_world_model,h,torch.ones_like(z))
    assert torch.equal(scale,torch.zeros_like(scale))
    torch.testing.assert_close(shift,h.mean(0))


def test_fp_arrival_only_freeze_patience_and_holdout():
    m=model_fixture('2'); trainer=FPTrainer(m)
    g,f,mask=candidate_fixture(); out=m(torch.randn(4,128),g,f,mask)
    before=deepcopy(m.state_dict())
    result=trainer.update(out['prediction'],torch.randn(4,128),torch.zeros(4,dtype=torch.long),torch.tensor([True,False,False,False]))
    assert result['arrivals']==1
    assert any(not torch.equal(v,m.state_dict()[k]) for k,v in before.items() if k.startswith('world_model.'))
    assert all(torch.equal(v,m.state_dict()[k]) for k,v in before.items() if not k.startswith('world_model.'))
    assert not trainer.end_epoch(1.)
    assert [trainer.end_epoch(1.) for _ in range(5)]==[False]*4+[True]
    train,hold=split_episodes(list(range(40)),123)
    assert len(hold)==4 and not train&hold
    d=prediction_diagnostics(out['prediction'].detach(),torch.randn(4,128),torch.zeros(4,dtype=torch.long),mask,torch.ones(4,dtype=torch.bool))
    assert d['comparable_count']==4 and d['loss'].numel()==4


def synthetic_adapter(rows, *, next_state):
    n=len(rows); t=int(rows[0]['decision_index'])+int(next_state)
    return dict(vcm_inputs=dict(observation=(torch.full((n,3,128,128),t/100),torch.full((n,12),t/10)),
                               action_result=torch.zeros(n,23),pose=torch.zeros(n,3),
                               step=torch.full((n,),t,dtype=torch.long),env_ids=list(range(n))),
                geometry=torch.zeros(n,3,6),features=torch.ones(n,3,19),mask=torch.ones(n,3,dtype=torch.bool))


def test_sequence_burn_in_no_gradient_and_no_double_next_recurrence():
    m=model_fixture(); seq=[[transition(t) for t in range(8)] for _ in range(2)]
    captured=[]
    handle=m.vcm.register_forward_hook(lambda module, inp, out: captured.append(out.requires_grad))
    outputs,next_outputs,target=sequence_outputs(m,seq,synthetic_adapter,gradients=True)
    handle.remove()
    assert captured[:4]==[False]*4
    assert captured[4:]==[True,False]*4
    assert len(outputs)==4 and target.shape==(8,128) and not target.requires_grad
    assert [int(x.step) for x in m.vcm.memory[0]]==[4,5,6,7]
    outputs[-1]['q1'].sum().backward()
    assert m.vcm.gru.weight_hh.grad is not None


def update_fixture(learner):
    m=learner.model; g,f,mask=candidate_fixture()
    device=next(m.parameters()).device
    g,f,mask=(x.to(device) for x in (g,f,mask))
    out=m(torch.randn(4,128,device=device),g,f,mask)
    with torch.no_grad():
        nxt=m(torch.randn(4,128,device=device),g,f,mask)
        target=learner.target(torch.randn(4,128,device=device),g,f,mask)
    batch=dict(reward=torch.randn(4),terminated=torch.tensor([True,False,False,False]),dt=torch.ones(4)*.1,
               selected=torch.tensor([0,1,0,1]),mask=mask,next_mask=mask)
    batch={k:v.to(device) for k,v in batch.items()}
    return learner.update(out,nxt,target,batch)


@pytest.mark.parametrize('stage',['1','3','G2','G3'])
def test_optimizer_routes_target_and_resume_exact(tmp_path,stage):
    m=model_fixture(stage); learner=DiscreteSAC(m,100)
    update_fixture(learner)
    r=replay_fixture(); config=dict(stage=stage)
    path=tmp_path/'checkpoint.pt'
    save_checkpoint(path,learner,r,counters=dict(decisions=1001),config=config)
    expected=update_fixture(learner); weights=deepcopy(m.state_dict())
    restored=DiscreteSAC(model_fixture(stage),100); replay=SequenceReplay(1000)
    counters,environment=load_checkpoint(path,restored,replay,config=config)
    actual=update_fixture(restored)
    assert expected==actual and counters['decisions']==1001 and environment is None
    assert all(torch.equal(weights[k],v) for k,v in restored.model.state_dict().items())
    assert restored.optimizer.param_groups[0]['lr']==learner.optimizer.param_groups[0]['lr']
    with pytest.raises(ValueError,match='environment'): load_checkpoint(path,restored,replay,config=config,require_environment=True)
    assert next(iter(restored.optimizer.state.values()))['exp_avg'].device==next(restored.model.parameters()).device


def test_invalid_values_stop_before_step():
    m=model_fixture(); l=DiscreteSAC(m,100)
    g,f,mask=candidate_fixture(); out=m(torch.randn(4,128),g,f,mask)
    before=deepcopy(m.state_dict())
    batch=dict(reward=torch.full((4,),float('nan')),terminated=torch.zeros(4,dtype=torch.bool),dt=torch.ones(4),selected=torch.zeros(4,dtype=torch.long),mask=mask,next_mask=mask)
    with pytest.raises(FloatingPointError): l.update(out,out,out,batch)
    assert all(torch.equal(before[k],v) for k,v in m.state_dict().items())


def test_validation_requires_declared_rules_and_keeps_state():
    with pytest.raises(ValueError): ValidationSelector(None,None)
    selector=ValidationSelector(100,'earliest')
    assert selector.consider(100,.2) and not selector.consider(200,.2) and selector.consider(300,.4)
    new=ValidationSelector(100,'earliest');new.load_state_dict(selector.state_dict());assert new.best_step==300
    with pytest.raises(ValueError): selector.consider(301,.5)


@pytest.mark.skipif(os.getenv('TASK722_GPU')!='1',reason='explicit GPU1 run only')
def test_actual_cuda_optimizer_recovery(tmp_path):
    assert torch.cuda.is_available()
    m=model_fixture('3').cuda(); learner=DiscreteSAC(m,100)
    first=update_fixture(learner)
    assert math.isfinite(first['critic'])
    assert all(p.device.type=='cuda' for g in learner.optimizer.param_groups for p in g['params'])
    assert all(s['exp_avg'].device.type=='cuda' for s in learner.optimizer.state.values())
    replay=replay_fixture();path=tmp_path/'gpu.pt';config={'device':'cuda:0'}
    save_checkpoint(path,learner,replay,counters={'decisions':1001},config=config)
    expected=update_fixture(learner); weights=deepcopy(m.state_dict())
    restored=DiscreteSAC(model_fixture('3').cuda(),100)
    load_checkpoint(path,restored,replay,config=config)
    actual=update_fixture(restored)
    assert expected==actual
    assert all(torch.equal(weights[k],v) for k,v in restored.model.state_dict().items())


def test_evaluation_counts_one_episode_per_map_and_strict_success():
    from types import SimpleNamespace
    calls=[]
    class FakeEnv:
        def reset(self, map_ids):
            self.map_id=map_ids[0]; calls.append(self.map_id); self.t=0
            self.candidates=dict(mask=torch.tensor([[True,False]]),f_k=torch.zeros(1,2,19))
            return {},self.candidates
        def step(self,selected):
            self.t+=1
            return SimpleNamespace(dt=torch.tensor([.1]),terminated=torch.tensor([self.t==2]),truncated=torch.tensor([False]),
                                   info=dict(r_t=dict(lower_steps=torch.tensor([1])),strict_success=torch.tensor([self.map_id=='ok'])),
                                   observation={},candidates=self.candidates)
    r=evaluate_maps(lambda _:FakeEnv(),['ok','bad'],group='G1')
    assert calls==['ok','bad'] and r['strict_success_rate']==.5
    assert [x['decisions'] for x in r['episodes']]==[2,2]
    assert [x['lower_steps'] for x in r['episodes']]==[2,2]


def test_recurrent_update_and_fp_batch_full32():
    from task7_upper.stages import update_sequences,fp_sequence_batch,select_training_action
    r=replay_fixture()
    for seq in r.episodes.values():
        for x in seq:
            x['candidates']['mask']=torch.ones(3,dtype=torch.bool)
            x['next_candidates']['mask']=torch.ones(3,dtype=torch.bool)
    m=model_fixture();learner=DiscreteSAC(m,100)
    skipped=update_sequences(learner,r,999,synthetic_adapter)
    assert not skipped['updated'] and learner.updates==0
    result=update_sequences(learner,r,1000,synthetic_adapter)
    assert result['updated'] and learner.updates==1
    m.set_stage('2'); trainer=FPTrainer(m)
    result,diag=fp_sequence_batch(m,r.sample(),synthetic_adapter,trainer)
    assert result['arrivals']==128 and trainer.updates==1 and diag['loss'].numel()==128
    logits=torch.tensor([[100.,-100.,0.],[100.,-100.,0.]])
    mask=torch.tensor([[True,True,False],[True,True,False]])
    selected,p=select_training_action(logits,mask,torch.tensor([999,1000]))
    assert torch.equal(p[0],torch.tensor([.5,.5,0.])) and selected[1]==0


def test_branch_carries_temperature_but_rebuilds_optimizer_and_replay():
    from task7_upper.stages import begin_rl_branch
    m=model_fixture(); old=CappedTemperature('cpu',log_alpha=-.8)
    old.update(torch.tensor([[.9,.1]]),torch.tensor([[.9,.1]]).log(),torch.ones(1,2,dtype=torch.bool))
    assert old.optimizer.state
    g,f,mask=candidate_fixture()
    learner,replay,report=begin_rl_branch(m,'3',old,total_updates=100,replay_seed=722,state=torch.randn(4,128),geometry=g,features=f,mask=mask)
    assert torch.equal(learner.temperature.log_alpha,old.log_alpha)
    assert learner.temperature.optimizer is not old.optimizer and not learner.temperature.optimizer.state
    assert len(replay)==0 and replay.capacity==100000 and learner.updates==0
    assert report['atol']==1e-6 and m.stage=='3'


def test_latest_validation_arrival_then_earliest_and_zero_variance():
    s=ValidationSelector(10000,'arrival_then_earliest')
    assert s.consider(10000,.3,.2)
    assert s.consider(20000,.3,.4)
    assert not s.consider(30000,.3,.4)
    assert not s.consider(40000,.2,.9)
    assert s.consider(50000,.4,.1)
    restored=ValidationSelector(10000,'arrival_then_earliest');restored.load_state_dict(s.state_dict())
    assert restored.best_arrival==.1 and restored.best_step==50000
    m=model_fixture();a=torch.randn(8,128);b=torch.randn(8,128);b[:,7]=3.
    scale,shift=fit_g3_alignment(m.random_world_model,a,b)
    assert scale[7]==0
    torch.testing.assert_close((b*scale+shift)[:,7],a[:,7].mean().expand(8))
    keep=torch.arange(128)!=7
    torch.testing.assert_close((b*scale+shift).std(0,unbiased=False)[keep],a.std(0,unbiased=False)[keep])


def test_real_adapter_uses_exact_decode_result_and_target_progress():
    from task7_upper.stages import environment_inputs,ReplayAdapter,RESULT_FIELDS
    for asynchronous in (False,True):
        n=2;grid=encode_grid(torch.zeros(n,128,128,3));previous=torch.randn(n,4)
        obs=dict(grid_uint8=grid,q=torch.randn(n,6),tcp=torch.randn(n,7),route_points=torch.randn(n,15,3),
                 r_t={k:torch.full((n,),i) for i,k in enumerate(RESULT_FIELDS)},previous_candidate=previous,
                 previous_result_v1=torch.randn(n,19),previous_target_delta_s=torch.tensor([.2,.3]),
                 synchronous=torch.full((n,1),float(not asynchronous)),n_f_over_F=torch.zeros(n,1),m_over_M=torch.zeros(n,1),
                 base_pose=torch.randn(n,3),decision_index=torch.tensor([4,7]),route_s=torch.tensor([.1,.2]))
        candidates=dict(c_k=torch.zeros(n,13,3),inplace=torch.zeros(n,13,dtype=torch.bool),progress=torch.ones(n,13),
                        mask=torch.ones(n,13,dtype=torch.bool),f_k=torch.randn(n,13,19))
        out=environment_inputs(obs,candidates,env_ids=[0,1],asynchronous=asynchronous,device='cpu')
        assert torch.equal(out['vcm_inputs']['observation'][0],decode_grid(grid).permute(0,3,1,2))
        assert torch.equal(out['vcm_inputs']['action_result'][:,-19:],obs['previous_result_v1'])
        assert torch.equal(out['vcm_inputs']['action_result'][:,:4],previous)
        if asynchronous:
            torch.testing.assert_close(out['geometry'][...,6],(candidates['progress']-obs['route_s'][:,None]))
            assert torch.equal(out['vcm_inputs']['action_result'][:,4],obs['previous_target_delta_s'])
        rows=[{k:row(v,i,n) for k,v in dict(observation=obs,candidates=candidates,next_observation=obs,next_candidates=candidates).items()} for i in range(n)]
        adapter=ReplayAdapter(asynchronous,'cpu');recreated=adapter(rows,next_state=True)
        assert torch.equal(recreated['vcm_inputs']['observation'][1],out['vcm_inputs']['observation'][1])


def test_unique_arrival_epoch_samples_no_cross_episode_or_extra_labels():
    from task7_upper.fp_trainer import arrival_samples,materialize_samples
    r=replay_fixture()
    samples,omitted=arrival_samples(r,{('run',0,0),('run',0,1)})
    assert len(samples)==2 and omitted==14
    fragments=materialize_samples(r,samples)
    assert all(sum(bool(x['arrival_label_valid']) for x in f)==1 for f in fragments)
    assert all(bool(f[-1]['arrival_label_valid']) for f in fragments)
    assert all([int(x['decision_index']) for x in f]==list(range(8)) for f in fragments)
    # Labels in authoritative replay remain unchanged by sample views.
    assert all(bool(x['arrival_label_valid']) for x in r.episodes[('run',0,0)])


def test_fp_holdout_splits_labelled_episodes_only():
    from task7_upper.fp_trainer import split_arrival_episodes,arrival_samples
    r=replay_fixture()
    for ep in range(2,40):
        for x in r.episodes[('run',0,ep)]:x['arrival_label_valid']=torch.tensor(False)
    train,hold=split_arrival_episodes(r,722)
    assert len(train)==len(hold)==1
    assert train|hold=={('run',0,0),('run',0,1)}
    assert not train&hold
    assert len(arrival_samples(r,train)[0])==len(arrival_samples(r,hold)[0])==1


def test_scheduled_validation_exact_decision_boundary_and_best_callback():
    from task7_upper.evaluate import scheduled_validation
    selector=ValidationSelector(10000,'arrival_then_earliest');calls=[]
    evaluate=lambda:dict(strict_success_rate=.2,arrival_rate=.3)
    assert scheduled_validation(selector,9000,9999,evaluate,lambda:calls.append('best')) is None
    result=scheduled_validation(selector,9999,10000,evaluate,lambda:calls.append('best'))
    assert result['selected_best'] and calls==['best']
    assert not scheduled_validation(selector,19999,20000,evaluate,lambda:calls.append('best'))['selected_best']
    with pytest.raises(ValueError,match='exact'):scheduled_validation(selector,29984,30048,evaluate,lambda:None)


@pytest.mark.parametrize('asynchronous',[False,True])
def test_real_adapter_full_recurrent_learner_integration(asynchronous):
    from task7_upper.stages import ReplayAdapter,RESULT_FIELDS,update_sequences,fp_sequence_batch
    n=32;obs=dict(grid_uint8=torch.zeros(n,128,128,3,dtype=torch.uint8),q=torch.zeros(n,6),tcp=torch.zeros(n,7),
                 route_points=torch.zeros(n,15,3),r_t={k:torch.zeros(n) for k in RESULT_FIELDS},
                 previous_candidate=torch.zeros(n,4),previous_result_v1=torch.zeros(n,19),previous_target_delta_s=torch.zeros(n),
                 synchronous=torch.full((n,1),float(not asynchronous)),n_f_over_F=torch.zeros(n,1),m_over_M=torch.zeros(n,1),
                 base_pose=torch.zeros(n,3),decision_index=torch.zeros(n,dtype=torch.long),route_s=torch.zeros(n))
    candidates=dict(c_k=torch.zeros(n,13,3),inplace=torch.zeros(n,13,dtype=torch.bool),progress=torch.ones(n,13),
                    mask=torch.ones(n,13,dtype=torch.bool),f_k=torch.ones(n,13,19))
    replay=SequenceReplay(seed=722)
    for t in range(8):
        fields=dict(run_id='synthetic-adapter-contract',episode_id=torch.ones(n,dtype=torch.long),environment_id=torch.arange(n),
                    observation={**obs,'decision_index':torch.full((n,),t,dtype=torch.long)},candidates=candidates,
                    next_observation={**obs,'decision_index':torch.full((n,),t+1,dtype=torch.long)},next_candidates=candidates,
                    selected=torch.zeros(n,dtype=torch.long),reward=torch.zeros(n),dt=torch.full((n,),.1),
                    terminated=torch.full((n,),t==7),truncated=torch.zeros(n,dtype=torch.bool),arrival_label_valid=torch.ones(n,dtype=torch.bool),
                    decision_index=torch.full((n,),t,dtype=torch.long))
        replay.append_batch(fields,diagnostics={})
    adapter=ReplayAdapter(asynchronous,'cpu');item=adapter([s[0] for s in replay.episodes.values()])
    model=UpperModel(vector_dim=item['vcm_inputs']['observation'][1].shape[-1],asynchronous=asynchronous)
    learner=DiscreteSAC(model,199000);result=update_sequences(learner,replay,1000,adapter)
    assert result['updated'] and math.isfinite(result['critic']) and learner.updates==1
    model.set_stage('2');trainer=FPTrainer(model)
    result,diag=fp_sequence_batch(model,replay.sample(),adapter,trainer)
    assert result['arrivals']==128 and torch.isfinite(diag['loss']).all()


def test_stage3_target_uses_current_supervised_fp_weights():
    from task7_upper.stages import update_sequences
    replay=replay_fixture()
    for seq in replay.episodes.values():
        for r in seq:
            r['candidates']['mask']=torch.ones(3,dtype=torch.bool)
            r['next_candidates']['mask']=torch.ones(3,dtype=torch.bool)
    model=model_fixture('3');learner=DiscreteSAC(model,100)
    with torch.no_grad():next(model.world_model.parameters()).add_(.1)
    expected=next(model.world_model.parameters()).detach().clone();seen=[]
    handle=learner.target.world_model.register_forward_pre_hook(lambda m,args:seen.append(torch.equal(next(m.parameters()),expected)))
    result=update_sequences(learner,replay,1000,synthetic_adapter,fp=FPTrainer(model))
    handle.remove()
    assert result['updated'] and seen and all(seen)


@pytest.mark.skipif(os.getenv('TASK722_GPU')!='1',reason='explicit GPU1 run only')
def test_online_restore_keeps_cpu_prefix_before_new_cpu_append(tmp_path):
    from types import SimpleNamespace
    from task7_upper.stages import save_online,load_online
    model=model_fixture().cuda();learner=DiscreteSAC(model,100);replay=SequenceReplay()
    environment=SimpleNamespace(marker=torch.tensor([7.],device='cuda'),episodes=SimpleNamespace(
        kin=SimpleNamespace(_dls_graph_cache={},_fixed_cache={}),sampler=SimpleNamespace(device='cuda')))
    histories=[[{'observation':{'q':torch.tensor([1.,2.])}}]]
    path=tmp_path/'online.pt';config={'device':'cuda:0'}
    save_online(path,learner,replay,environment=environment,histories=histories,
                counters={'decisions':1,'action_calls':1},config=config)
    restored=DiscreteSAC(model_fixture().cuda(),100)
    counters,env,prefix=load_online(path,restored,SequenceReplay(),config=config)
    assert env.marker.device.type=='cuda'
    assert prefix[0][0]['observation']['q'].device.type=='cpu'
    prefix[0].append({'observation':{'q':torch.tensor([3.,4.])}})
    # This is the stack that failed after the first real post-restore batch.
    assert torch.equal(torch.stack([r['observation']['q'] for r in prefix[0]]),torch.tensor([[1.,2.],[3.,4.]]))
    assert counters=={'decisions':1,'action_calls':1}
