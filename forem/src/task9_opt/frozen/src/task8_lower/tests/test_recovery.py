"""Actual PCD state and optimizer recovery; no fresh-reset substitution."""
import copy
import json
import os
from pathlib import Path
import torch
import pytest
from test_stage0 import config, batch, DEVICE


@pytest.mark.parametrize('group',['B0','B3'])
def test_explicit_environment_resume_next_transition_and_update(tmp_path,group):
    from task8_lower.training import save_checkpoint,load_checkpoint,consume_transition
    from task7_lower.training import choose_candidate,rng_state,restore_rng,limited_step,drain_history
    from task8_lower.sac import LowerSAC
    from task8_lower.replay import Replay
    from task8_sim.env import PcdEpisodeEnv
    pool=Path('/root/mm_husky_ws/results/task8/t8-perf-20261027/cube-pool/manifest.json')
    if not pool.exists():pool=pool.with_name('index.json')
    cfg=config(group);cfg['batch_size']=2;cfg['pool']=str(pool);cfg['environments']=1;cfg['replay_capacity']=8
    cfg['dls_cuda_graph']=True;cfg.pop('evaluation_seeds',None)
    cfg['train_split']=json.loads(pool.read_text())['maps'][0]['split']
    torch.manual_seed(812)
    env=PcdEpisodeEnv(1,seed=812,pool=pool,profile='sync_v5',device=DEVICE,dtype=torch.float32,split=cfg['train_split'])
    env.kin.dls_cuda_graph=cfg['dls_cuda_graph']
    env.reset();choose_candidate(env)
    sac=LowerSAC(74,DEVICE,cfg);sac.update_from_batch(batch(),0,transfer=258)
    replay=Replay(8,74,41,DEVICE)
    observation=env.core.current_observation();raw=sac.select_action(observation,False)
    tr=limited_step(env,raw,1);drain_history(env.core)
    replay.push(tr.observation,tr.raw_action,tr.reward,tr.next_observation,tr.mask,transfer=259,failed=env.core.last_step_failure>0)
    replay.push(tr.observation,tr.raw_action,tr.reward,tr.next_observation,tr.mask,transfer=258,failed=env.core.last_step_failure>0)
    replay.push(tr.observation,tr.raw_action,tr.reward,tr.next_observation,tr.mask,transfer=257,failed=env.core.last_step_failure>0)
    state=dict(steps=259,pending=dict(transition=tr,ids=[0],cursor=0),watchdog={},attempted=0,committed=0,sim_s=0.)
    path=tmp_path/'checkpoint.pt';save_checkpoint(path,sac,replay,env,state,cfg)
    # Observe both independent next operations from the saved stochastic state.
    expected_loss=consume_transition(sac,replay,state,tr,0,cfg,env.core.last_step_failure>0)
    expected_state=copy.deepcopy(sac.full_state_dict())
    choose_candidate(env)
    raw=sac.select_action(env.core.current_observation(),False);expected=limited_step(env,raw,1)
    restored,replay2,env2,state2,cfg2=load_checkpoint(path,DEVICE)
    assert env2.core is not None and env2.episode_count.tolist()==env.episode_count.tolist()
    assert state2['pending']['cursor']==0 and state2['pending']['ids']==[0]
    assert torch.equal(state2['pending']['transition'].reward,tr.reward)
    actual_loss=consume_transition(restored,replay2,state2,state2['pending']['transition'],0,cfg2,env2.core.last_step_failure>0)
    assert expected_loss==actual_loss
    assert state2['pending']['cursor']==1 and state2['steps']==260
    choose_candidate(env2);raw2=restored.select_action(env2.core.current_observation(),False)
    actual=limited_step(env2,raw2,1)
    assert torch.equal(raw,raw2)
    for key,value in vars(expected).items():
        if torch.is_tensor(value):assert torch.equal(value,getattr(actual,key)),key
        elif isinstance(value,dict):
            for k,v in value.items():assert torch.equal(v,getattr(actual,key)[k]),(key,k)
    def exact(a,b):
        if torch.is_tensor(a):assert torch.equal(a,b)
        elif isinstance(a,dict):
            assert a.keys()==b.keys()
            for key in a:exact(a[key],b[key])
        elif isinstance(a,(list,tuple)):
            assert len(a)==len(b)
            for u,v in zip(a,b):exact(u,v)
        else:assert a==b
    exact(expected_state,restored.full_state_dict())
    exact(replay.state_dict(),replay2.state_dict())


def test_train_cli_module_and_consumption_contract():
    from task8_lower.training import consume_transition
    from task8_lower.sac import update_due
    cfg=config('B3')
    assert update_due(260,257,cfg) and not update_due(259,257,cfg)
    assert callable(consume_transition)


@pytest.mark.parametrize('mode',['STOP','SIGTERM'])
def test_stop_controls_save_before_initial_reset_and_restore_handlers(tmp_path,mode):
    import signal
    from task8_lower.training import train,load_checkpoint
    from task8_sim.env import PcdEpisodeEnv
    cfg=config();cfg['batch_size']=2;cfg['replay_capacity']=8;cfg['environments']=1;cfg['device']=DEVICE
    cfg['pool']='/root/mm_husky_ws/results/task8/t8-perf-20261027/cube-pool/manifest.json'
    cfg['train_split']=json.loads(Path(cfg['pool']).read_text())['maps'][0]['split']
    cfg.pop('evaluation_seeds',None)
    before=signal.getsignal(signal.SIGTERM)
    if mode=='STOP':(tmp_path/'STOP').touch()
    def factory(*args,**kwargs):
        env=PcdEpisodeEnv(*args,**kwargs)
        if mode=='SIGTERM':signal.raise_signal(signal.SIGTERM)
        return env
    with pytest.raises(InterruptedError,match='STOP|SIGTERM'):
        train(cfg,tmp_path,transfers=1,env_factory=factory)
    assert signal.getsignal(signal.SIGTERM)==before
    sac,replay,env,state,stored=load_checkpoint(tmp_path/'interrupted.pt',DEVICE)
    assert env.core is None and state['steps']==0 and state['env_actions']==0 and len(replay)==0
    assert mode in state['stop_reason']
