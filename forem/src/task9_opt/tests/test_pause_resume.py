"""Production train/Core/replay/save-restore with a nonaligned consumed boundary.

Only CPU test map construction and evaluation cost are bounded fixtures. The
real training consumer, SAC networks, random actions, IK, candidate selection,
transition order, ledgers and explicit environment restore are exercised.
"""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
import torch
from task9_opt.runtime import ASSET_ROOT
from task8_sim.env import PcdEpisodeEnv
from task8_sim.scene import VoxelScene
from task8_sim.assets import load_asset
from task8_sim.episode import PcdEpisode
from task7_sim.kinematics import Kinematics
from task7_sim.motion import Route, matrix_quat
from task7_lower.training import atomic_json, rng_state
from task8_lower.training import train, load_checkpoint
from test_requirements import cfg, exact, DEVICE


POOL=ASSET_ROOT/'results/task8/t8-exec-20261026/cube-pool/manifest.json'


def make_env(batch,**kwargs):
    """Real empty-scene episode: a 1m route keeps this short test inside episode1."""
    fixture=json.loads((ASSET_ROOT/'results/task7/t7.14-r2-20261021-0000/fixture.json').read_text())
    def factory(i,streams):
        base=torch.zeros(1,3);base[:,0]=float(streams.initial.uniform(-.05,.05))
        q=torch.tensor(fixture['q'],dtype=torch.float32)[None]
        tcp=Kinematics().world_tcp(base,q)
        xyz=tcp[:,None,:3,3].expand(-1,2,-1).clone();xyz[:,1,0]+=1.
        route=Route(xyz,matrix_quat(tcp[:,:3,:3])[:,None].expand(-1,2,-1).clone())
        scene=VoxelScene.from_asset(load_asset(POOL,'empty'),device=DEVICE,dtype=torch.float32)
        return PcdEpisode(base,q,route,scene,'empty',seed=123+i)
    kwargs['pool']=POOL;kwargs['map_backend']='pcd-voxel-v3'
    env=PcdEpisodeEnv(batch,factory=factory,**kwargs)
    env.reset()
    # Explicit checkpoint saves an already initialized real environment; no
    # closure or Python reset factory can enter the persisted production state.
    env.factory=None
    return env


def fixture_evaluation(sac,config,path,**kwargs):
    result=dict(complete=True,step=sac.env_steps,fixture_only=True)
    atomic_json(path,result)
    return result


def compare_tree(a,b,path=''):
    if isinstance(a,(torch.Tensor,np.ndarray,dict,list,tuple)):
        if isinstance(a,dict):
            assert a.keys()==b.keys(),path
            for k in a:compare_tree(a[k],b[k],path+'.'+str(k))
        elif isinstance(a,(list,tuple)):
            assert len(a)==len(b),path
            for i,(x,y) in enumerate(zip(a,b)):compare_tree(x,y,path+'.'+str(i))
        else:exact(a,b)
    elif hasattr(a,'__dict__'):
        compare_tree(vars(a),vars(b),path)
    else:assert a==b,path


def test_actual_train_non_aligned_pause_preserves_charged_actions_and_continuation(tmp_path):
    # Capping limited_step at pause7 would produce7 actions, lose pending2,
    # change the next RNG/action/update sequence and fail this comparison.
    config=dict(cfg(),total_transfers=13,environments=3,replay_capacity=16,batch_size=2,
                update_every_transfers=2,device=DEVICE,dls_cuda_graph=False,checkpoint_interval=7,
                pool=str(POOL),map_backend='pcd-voxel-v3',environment_geometry_version='pcd-voxel-v3')
    config.pop('evaluation_seeds',None)
    full=tmp_path/'full';split=tmp_path/'split'
    train(config,full,env_factory=make_env,evaluator=fixture_evaluation)
    expected=load_checkpoint(full/'final.pt',DEVICE)
    expected_rng=copy.deepcopy(rng_state())
    result=train(config,split,env_factory=make_env,evaluator=fixture_evaluation,pause_after_consumed=7)
    assert result['status']=='paused_profile' and result['steps']==7
    assert result['scientific_limit']==13 and result['env_actions']==9
    assert result['pending']==dict(ids=[0,1,2],cursor=1,remaining=2)
    assert result['validation_pending'] is None and not (split/'final.pt').exists()
    checkpoint=torch.load(split/'profile.pt',weights_only=False)
    assert checkpoint['config']['total_transfers']==13
    assert checkpoint['state']['pending']['cursor']==1
    assert checkpoint['state']['validation_pending'] is None
    assert json.loads((split/'validation-0000007.json').read_text())['complete']
    train(config,split,resume=split/'profile.pt',env_factory=make_env,evaluator=fixture_evaluation)
    actual=load_checkpoint(split/'final.pt',DEVICE)
    exact(expected[0].full_state_dict(),actual[0].full_state_dict())
    exact(expected[1].state_dict(),actual[1].state_dict())
    exact(expected_rng,rng_state())
    for key in ('state','candidate','start','grid','route','queue','visible_previous','first','done','terminated','truncated','failures','time'):
        compare_tree(getattr(expected[2].core,key),getattr(actual[2].core,key),key)
    for x,y in zip(expected[2].streams._streams,actual[2].streams._streams):
        for purpose in ('maps','initial','other'):compare_tree(getattr(x,purpose).bit_generator.state,getattr(y,purpose).bit_generator.state)
    left={k:v for k,v in expected[3].items() if k!='wall_s'}
    right={k:v for k,v in actual[3].items() if k!='wall_s'}
    compare_tree(left,right)
    assert (full/'interactions.jsonl').read_text()==(split/'interactions.jsonl').read_text()
    assert actual[3]['steps']==13 and actual[3]['env_actions']==13 and actual[0].update_count==5
