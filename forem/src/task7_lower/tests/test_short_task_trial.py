"""Fixed-case mutation, conflated route ends and duplicate transfers break these."""
import copy
import functools
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch
from task7_sim.env import EpisodeEnv
from task7_sim.tests.test_env import factory,target
from task7_lower.training import rng_state,restore_rng


class FixtureTrainingEnv(EpisodeEnv):
    def __init__(self,batch,**kwargs):
        super().__init__(batch,functools.partial(factory,device='cuda',dtype=torch.float32),seed=kwargs['seed'],synchronous=True,failure_mode=kwargs['failure_mode'],episode_end_bootstrap=kwargs['episode_end_bootstrap'])
        self.sampler=SimpleNamespace(stats={'rejections':{}},device=torch.device('cuda'))


def fixture_env(device='cuda'):
    env=EpisodeEnv(1,functools.partial(factory,device=device,dtype=torch.float32),seed=14718,synchronous=True,failure_mode='cbl_continue',episode_end_bootstrap=True)
    env.reset();env.begin(target(env.core,.03));return env


def test_route_end_can_coincide_actual_candidate_pose_and_preserves_arrival():
    from task7_lower.short_task_trial import case_outcome
    env=fixture_env();c=env.core;c.reason[:]=1;c.state.s[:]=c.route.length;c.done[:]=True
    first=case_outcome(c,c.state.base.clone(),False)
    assert first['candidate_pose_reached'] and first['route_end'] and first['old_arrival']
    assert not first['route_end_first']
    c.candidate.pose[:,0]+=1
    second=case_outcome(c,c.state.base.clone(),False)
    assert second['route_end_first'] and not second['candidate_pose_reached'] and second['old_arrival']


def test_fixed_case_is_identical_for_both_actors_and_does_not_leak_rng(tmp_path):
    from task7_lower.short_task_trial import freeze_case,evaluate_cases,sha256
    env=fixture_env();c=env.core
    row=freeze_case(env,tmp_path/'case.pt',dict(case_id='original-m0',distribution='original',map_id='m0',difficulty='sparse'))
    digest=sha256(tmp_path/'case.pt');torch.manual_seed(981);before=torch.get_rng_state().clone()
    inputs=[]
    def actor(obs):
        inputs.append({k:v.clone() for k,v in obs.items()})
        # Deliberately consume global RNG: evaluation must restore it anyway.
        torch.rand(3)
        return torch.zeros(len(obs['q']),3,device=obs['q'].device,dtype=obs['q'].dtype)
    a=evaluate_cases(actor,[row],tmp_path/'a.json',device='cuda')
    b=evaluate_cases(actor,[row],tmp_path/'b.json',device='cuda')
    assert torch.equal(before,torch.get_rng_state())
    assert sha256(tmp_path/'case.pt')==digest
    assert a['rows']==b['rows'] and a['rows'][0]['case_sha256']==digest
    halfway=len(inputs)//2
    assert all(torch.equal(inputs[0][key],inputs[halfway][key]) for key in inputs[0])
    assert c.time.eq(0).all()  # evaluator loaded a separate snapshot


def test_zero_time_case_emits_no_action_or_fake_interaction(tmp_path):
    from task7_lower.short_task_trial import freeze_case,evaluate_cases
    env=fixture_env();env.core.done[:]=True;env.core.reason[:]=0
    row=freeze_case(env,tmp_path/'zero.pt',dict(case_id='short-m0',distribution='short',map_id='m0',difficulty='sparse'))
    def forbidden(obs):raise AssertionError('zero-time case must not invoke actor')
    result=evaluate_cases(forbidden,[row],tmp_path/'eval.json',device='cuda')
    assert result['rows'][0]['zero_time'] and result['rows'][0]['action_calls']==0
    assert result['rows'][0]['attempted_substeps']==0


def test_case_hash_mismatch_is_rejected(tmp_path):
    from task7_lower.short_task_trial import freeze_case,evaluate_cases
    row=freeze_case(fixture_env(),tmp_path/'case.pt',dict(case_id='x',distribution='short',map_id='m0',difficulty='sparse'))
    with (tmp_path/'case.pt').open('ab') as f:f.write(b'changed')
    with pytest.raises(ValueError,match='case hash'):evaluate_cases(lambda x:None,[row],tmp_path/'eval.json',device='cuda')


def test_exact_cap_endpoint_and_resume_identity_without_duplicate_actions(tmp_path,monkeypatch):
    from task7_lower.short_task_trial import phase_training_config
    from task7_lower.training import train,load_checkpoint
    import task7_sim.env as em
    monkeypatch.setattr(em,'EpisodeEnv',FixtureTrainingEnv)
    base=dict(total_transfers=5000000,total_updates=4999743,seed=4718,validation_seed=14718,synchronous=True,environments=2,pool='unused',batch_size=256,replay_capacity=300,warmup_transfers=1000,checkpoint_interval=250000,log_interval=1000,dls_cuda_graph=False,failure_mode='cbl_continue',episode_end_bootstrap=True)
    cfg,tmp_path=phase_training_config(base,'short',dict(protocol='fixture',source='one'),tmp_path,'train',sampling_seconds=5)
    result=train(cfg,tmp_path,transfers=259)
    assert result['state']['steps']==result['state']['env_actions']==259 and result['updates']==2
    assert result['policy_device']=='cuda:0' and result['replay_device']=='cuda:0'
    assert 'cuda:0' in result['optimizer_devices']
    for name in ('final.pt','final.actor.pt','final.meta.json'):assert (tmp_path/name).is_file()
    sac,replay,env,state,stored=load_checkpoint(tmp_path/'final.pt','cuda')
    assert stored['route_length_bounds']==[1.,2.] and stored['trial_identity']['source']=='one'
    assert len(replay)==259 and state['pending'] is None
    resumed=train(cfg,tmp_path,transfers=261,resume=tmp_path/'final.pt')
    assert resumed['state']['steps']==resumed['state']['env_actions']==261
    wrong=copy.deepcopy(cfg);wrong['trial_identity']['source']='two'
    with pytest.raises(ValueError,match='resume config mismatch'):train(wrong,tmp_path,transfers=262,resume=tmp_path/'final.pt')


def test_fresh_groups_load_exact_shared_initial_policy_and_trial_metadata(tmp_path,monkeypatch):
    from task7_lower.short_task_trial import initial_weights,phase_training_config,sha256
    from task7_lower.training import train
    import task7_sim.env as em
    monkeypatch.setattr(em,'EpisodeEnv',FixtureTrainingEnv)
    base=dict(total_transfers=5000000,total_updates=4999743,seed=4718,validation_seed=14718,synchronous=True,environments=1,pool='unused',batch_size=256,replay_capacity=4,warmup_transfers=1000,checkpoint_interval=250000,log_interval=1000,dls_cuda_graph=False,failure_mode='cbl_continue',episode_end_bootstrap=True)
    identity=dict(source='paired')
    init,init_actor=initial_weights(tmp_path,base,identity)
    assert torch.load(init_actor,map_location='cpu',weights_only=False)['trial_identity']==identity
    policies=[]
    for distribution in ('original','short'):
        cfg,_=phase_training_config(base,distribution,identity,tmp_path,'train');cfg['trial_initial_state']=str(init);cfg['trial_initial_sha256']=sha256(init)
        train(cfg,tmp_path/distribution,transfers=1)
        policies.append(torch.load(tmp_path/distribution/'final.actor.pt',map_location='cpu',weights_only=False)['policy'])
        metadata=json.loads((tmp_path/distribution/'final.meta.json').read_text())
        assert metadata['trial_identity']==identity
    initial=torch.load(init,map_location='cpu',weights_only=False)['sac']['policy']
    assert all(torch.equal(policies[0][k],policies[1][k]) and torch.equal(policies[0][k],initial[k]) for k in initial)


def test_manifest_requires_both_distributions_on_every_fixed_map():
    from task7_lower.short_task_trial import validate_case_manifest
    ids=[f'm{i}' for i in range(100)]
    rows=[dict(case_id=f'{d}-{m}',distribution=d,map_id=m) for d in ('original','short') for m in ids]
    manifest=dict(format='task7-short-cases-v1',rows=rows)
    assert validate_case_manifest(manifest,ids)==rows
    broken=copy.deepcopy(manifest);broken['rows'][-1]['map_id']='m0'
    with pytest.raises(ValueError,match='coverage'):validate_case_manifest(broken,ids)
    with pytest.raises(ValueError,match='coverage'):validate_case_manifest(dict(manifest,rows=rows[:-1]),ids)


@pytest.mark.parametrize('mode',['exception','early_exit'])
def test_lost_client_keeps_full_budget_reservation_and_blocks_relaunch(tmp_path,monkeypatch,mode):
    import importlib.util
    path=Path(__file__).resolve().parents[3]/'scripts/task7_short_task_budget.py'
    spec=importlib.util.spec_from_file_location('_short_budget_under_test',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    budget=tmp_path/'budget.json';budget.write_text(json.dumps(dict(limit_seconds=1000,consumed_seconds=1,active_jobs=[],commands=[])))
    # The outer test already owns GPU3; hardware query is the external boundary.
    def query(args,**kwargs):return 'GPU-test\n' if '-i' in args else ''
    monkeypatch.setattr(module.subprocess,'check_output',query)
    def lost(*args,**kwargs):
        if mode=='exception':raise RuntimeError('lost Docker client; worker status unknown')
        return 125
    monkeypatch.setattr(module.subprocess,'call',lost)
    with pytest.raises(RuntimeError,match='lost Docker|completion'):module.run(budget,30,'lost',['python3','-c','pass'],tmp_path/'lost.log')
    saved=json.loads(budget.read_text())
    assert saved['consumed_seconds']==31 and len(saved['active_jobs'])==1
    with pytest.raises(RuntimeError,match='unreconciled active'):module.run(budget,30,'again',['python3','-c','pass'],tmp_path/'again.log')


@pytest.mark.parametrize('violation',['preflight_to_train','wrong_group','wrong_output','copied_preflight','missing_ledger','empty_ledger'])
def test_trial_resume_rejects_foreign_phase_output_or_missing_local_ledger(tmp_path,monkeypatch,violation):
    from task7_lower.short_task_trial import trial_config
    from task7_lower.training import train
    import task7_sim.env as em
    monkeypatch.setattr(em,'EpisodeEnv',FixtureTrainingEnv)
    base=dict(total_updates=4999743,seed=4718,validation_seed=14718,synchronous=True,environments=1,pool='unused',batch_size=256,replay_capacity=4,warmup_transfers=1000,checkpoint_interval=250000,log_interval=1000,dls_cuda_graph=False,failure_mode='cbl_continue',episode_end_bootstrap=True)
    is_preflight=violation in ('preflight_to_train','copied_preflight')
    source=tmp_path/('preflight-original' if is_preflight else 'original')
    cfg=trial_config(base,'original',dict(source='resume-fixture'))
    # Hand-declared operational binding; the old trainer ignored this entirely.
    cfg['trial_run']=dict(phase='preflight' if is_preflight else 'train',distribution='original',run_root=str(tmp_path.resolve()),output=str(source.resolve()))
    train(cfg,source,transfers=1)
    checkpoint=source/'final.pt';target_cfg=copy.deepcopy(cfg)
    if violation in ('preflight_to_train','copied_preflight'):
        target=tmp_path/'original'
        if violation=='copied_preflight':target_cfg['trial_run'].update(phase='train',output=str(target.resolve()))
    elif violation=='wrong_group':
        target=tmp_path/'short'
    elif violation=='wrong_output':
        target=tmp_path/'another-run'/'original'
    else:
        target=source
        if violation=='missing_ledger':(source/'interactions.jsonl').unlink()
        else:(source/'interactions.jsonl').write_text('')
    if violation=='copied_preflight':
        import shutil
        target.mkdir()
        for name in ('final.pt','final.meta.json','interactions.jsonl'):shutil.copy2(source/name,target/name)
        checkpoint=target/'final.pt'
    with pytest.raises((ValueError,RuntimeError),match='trial resume|trial run|local interaction ledger|resume config mismatch|budget-safe resume blocked'):
        train(target_cfg,target,transfers=2,resume=checkpoint)


def test_driver_phase_configs_bind_phase_group_root_and_output(tmp_path):
    from task7_lower.short_task_trial import phase_training_config
    base=dict(synchronous=True,total_updates=4999743)
    preflight,p_dir=phase_training_config(base,'original',{'source':'fixture'},tmp_path,'preflight',sampling_seconds=5)
    formal,f_dir=phase_training_config(base,'original',{'source':'fixture'},tmp_path,'train',sampling_seconds=5)
    short,s_dir=phase_training_config(base,'short',{'source':'fixture'},tmp_path,'train',sampling_seconds=5)
    assert p_dir==tmp_path/'preflight-original' and f_dir==tmp_path/'original' and s_dir==tmp_path/'short'
    assert preflight['trial_run']!=formal['trial_run']!=short['trial_run']
    assert formal['trial_run']==dict(phase='train',distribution='original',run_root=str(tmp_path.resolve()),output=str(f_dir.resolve()))
    assert preflight['trial_identity']==formal['trial_identity']==short['trial_identity']


@pytest.mark.parametrize('phase',['preflight','train'])
def test_bound_trial_resume_accepts_same_directory_and_counts_once(tmp_path,monkeypatch,phase):
    from task7_lower.short_task_trial import phase_training_config
    from task7_lower.training import train
    import task7_sim.env as em
    monkeypatch.setattr(em,'EpisodeEnv',FixtureTrainingEnv)
    base=dict(total_updates=4999743,seed=4718,validation_seed=14718,synchronous=True,environments=1,pool='unused',batch_size=256,replay_capacity=4,warmup_transfers=1000,checkpoint_interval=250000,log_interval=1000,dls_cuda_graph=False,failure_mode='cbl_continue',episode_end_bootstrap=True)
    cfg,directory=phase_training_config(base,'original',{'source':'same-directory'},tmp_path,phase)
    train(cfg,directory,transfers=1)
    resumed=train(cfg,directory,transfers=2,resume=directory/'final.pt')
    assert resumed['state']['steps']==resumed['state']['env_actions']==2
    assert json.loads((directory/'final.meta.json').read_text())['trial_run']==cfg['trial_run']
    headers=[json.loads(line) for line in (directory/'interactions.jsonl').read_text().splitlines() if json.loads(line).get('event')=='trial_header']
    assert len(headers)==1 and headers[0]['trial_run']==cfg['trial_run'] and headers[0]['trial_identity']==cfg['trial_identity']


@pytest.mark.parametrize('foreign_identity',['phase','group','run'])
def test_trial_resume_rejects_only_ledger_swapped_at_equal_counts(tmp_path,monkeypatch,foreign_identity):
    from task7_lower.short_task_trial import phase_training_config,sha256
    from task7_lower.training import train
    from task7_lower.recovery import safe_to_resume
    import task7_sim.env as em
    monkeypatch.setattr(em,'EpisodeEnv',FixtureTrainingEnv)
    base=dict(total_updates=4999743,seed=4718,validation_seed=14718,synchronous=True,environments=1,pool='unused',batch_size=256,replay_capacity=4,warmup_transfers=1000,checkpoint_interval=250000,log_interval=1000,dls_cuda_graph=False,failure_mode='cbl_continue',episode_end_bootstrap=True)
    identity={'source':'ledger-owner-fixture'}
    cfg,target=phase_training_config(base,'original',identity,tmp_path/'current-run','train')
    donor_cfg,donor=phase_training_config(base,'short' if foreign_identity=='group' else 'original',identity,tmp_path/('another-run' if foreign_identity=='run' else 'current-run'),'preflight' if foreign_identity=='phase' else 'train')
    train(cfg,target,transfers=1);train(donor_cfg,donor,transfers=1)
    checkpoint=target/'final.pt';metadata=target/'final.meta.json'
    original_cp,original_meta=sha256(checkpoint),sha256(metadata)
    local_ledger=target/'interactions.jsonl';foreign_ledger=donor/'interactions.jsonl'
    expected=dict(event='step_complete',action_calls=1,env_actions=1,steps=0)
    assert json.loads(local_ledger.read_text().splitlines()[-1])==expected
    assert json.loads(foreign_ledger.read_text().splitlines()[-1])==expected
    # Only this file changes: retain the legitimate local checkpoint and metadata.
    local_ledger.write_bytes(foreign_ledger.read_bytes())
    assert sha256(checkpoint)==original_cp and sha256(metadata)==original_meta
    assert safe_to_resume(checkpoint,local_ledger)[0]  # counters alone cannot detect ownership
    with pytest.raises(ValueError,match='trial resume.*ledger.*identity'):
        train(cfg,target,transfers=2,resume=checkpoint)
    assert sha256(checkpoint)==original_cp and sha256(metadata)==original_meta


def test_zero_action_trial_checkpoint_resumes_only_with_own_header(tmp_path,monkeypatch):
    from task7_lower.short_task_trial import phase_training_config
    from task7_lower.training import train
    import task7_sim.env as em
    monkeypatch.setattr(em,'EpisodeEnv',FixtureTrainingEnv)
    base=dict(total_updates=4999743,seed=4718,validation_seed=14718,synchronous=True,environments=1,pool='unused',batch_size=256,replay_capacity=4,warmup_transfers=1000,checkpoint_interval=250000,log_interval=1000,dls_cuda_graph=False,failure_mode='cbl_continue',episode_end_bootstrap=True)
    cfg,directory=phase_training_config(base,'original',{'source':'zero-action'},tmp_path,'train')
    with pytest.raises(TimeoutError):train(cfg,directory,transfers=1,max_wall_s=0)
    checkpoint=directory/'interrupted.pt';meta=json.loads(checkpoint.with_suffix('.meta.json').read_text())
    assert meta['steps']==meta['env_actions']==meta['action_calls']==0
    ledger=directory/'interactions.jsonl';original=ledger.read_text();header=json.loads(original)
    assert header['event']=='trial_header' and len(original.splitlines())==1
    wrong=copy.deepcopy(header);wrong['trial_run']['phase']='preflight';ledger.write_text(json.dumps(wrong)+'\n')
    with pytest.raises(ValueError,match='trial resume ledger identity'):train(cfg,directory,transfers=1,resume=checkpoint)
    ledger.write_text(original)
    resumed=train(cfg,directory,transfers=1,resume=checkpoint)
    assert resumed['state']['steps']==resumed['state']['env_actions']==1
    assert sum(json.loads(line)['event']=='trial_header' for line in ledger.read_text().splitlines())==1
