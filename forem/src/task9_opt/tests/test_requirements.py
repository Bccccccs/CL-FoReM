"""Behavioral regressions for isolated SAC variants and charged vector pauses."""
from pathlib import Path


def test_isolated_runtime_exists():
    # Removing the isolated root (or using the old entry) must fail this gate.
    root=Path(__file__).resolve().parents[1]
    assert (root/'runtime/src/task8_lower/training.py').is_file(), 'isolated training runtime absent'
    assert (root/'runtime/config/task7/model.urdf').is_file(), 'isolated robot asset absent'

import copy
import importlib.util
import json
import math
import os
import random
import numpy as np
import pytest
import torch
from task9_opt.runtime import PACKAGE_ROOT, ASSET_ROOT, GROUP_AXES, validate_formal_config, import_manifest, scientific_config
from task8_lower.sac import LowerSAC, update_due
from task8_lower.replay import Replay
from task7_lower.observation import preprocess
from task7_lower.training import rng_state as snapshot_rng, restore_rng
DEVICE=os.environ.get('TASK9_TEST_DEVICE','cpu')


def cfg(group='B3'):
    name=f'lower_train_{group}_prim.json'
    path=PACKAGE_ROOT/'frozen/config/task8'/name
    if not path.exists():
        path=ASSET_ROOT/'config/task8'/f'lower_train_{group}.json'
    return json.loads(path.read_text())


def obs(n=2):
    shapes=dict(grid=(128,128,3),q=(6,),tcp=(7,),next_tcp=(7,),route_points=(15,3),subgoal=(5,),synchronous=(1,),previous_action=(3,))
    return {k:torch.zeros((n,)+v) for k,v in shapes.items()}


def batch():
    m,v=preprocess(obs())
    return m,v,torch.zeros(2,3),torch.ones(2,1),m,v,torch.ones(2,1)


def exact(a,b):
    if torch.is_tensor(a):assert torch.equal(a,b)
    elif isinstance(a,np.ndarray):assert np.array_equal(a,b)
    elif isinstance(a,dict):
        assert a.keys()==b.keys()
        for k in a:exact(a[k],b[k])
    elif isinstance(a,(tuple,list)):
        assert len(a)==len(b)
        for x,y in zip(a,b):exact(x,y)
    else:assert a==b


def baseline_class():
    spec=importlib.util.spec_from_file_location('original_sac',PACKAGE_ROOT/'frozen/src/task8_lower/sac.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.LowerSAC


@pytest.mark.parametrize('group',['B0','B3'])
def test_default_update_action_and_restore_equal_original(group):
    # Any drift in default update/target/LR/network or action ordering breaks this.
    config=cfg(group);torch.manual_seed(81);old=baseline_class()(74,DEVICE,config)
    torch.manual_seed(81);new=LowerSAC(74,DEVICE,config)
    for transfer in [260,1000]:
        rng=snapshot_rng();a=old.update_from_batch(batch(),old.update_count,transfer=transfer)
        restore_rng(rng);b=new.update_from_batch(batch(),new.update_count,transfer=transfer)
        exact(a,b)
        for key in ['policy','critic','critic_target','policy_optim','critic_optim','alpha_optim','sched_policy','sched_critic']:
            exact(old.full_state_dict()[key],new.full_state_dict()[key])
        rng=snapshot_rng();a=old.select_action(obs(),False)
        restore_rng(rng);b=new.select_action(obs(),False);exact(a,b)
    restored=LowerSAC(74,DEVICE,config);restored.load_full_state_dict(copy.deepcopy(new.full_state_dict()))
    rng=snapshot_rng();a=new.update_from_batch(batch(),new.update_count,transfer=2000)
    restore_rng(rng);b=restored.update_from_batch(batch(),restored.update_count,transfer=2000)
    exact(a,b);exact(new.full_state_dict(),restored.full_state_dict())


def test_entropy_override_changes_actual_alpha_gradient():
    # Ignoring target_entropy passes a scalar loss at log_alpha0; gradient catches it.
    config=cfg();torch.manual_seed(7);base=LowerSAC(74,DEVICE,config)
    torch.manual_seed(7);variant=LowerSAC(74,DEVICE,dict(config,target_entropy=-1.5))
    rng=snapshot_rng();base.update_from_batch(batch(),0,transfer=260)
    restore_rng(rng);variant.update_from_batch(batch(),0,transfer=260)
    assert float(base.log_alpha.grad-variant.log_alpha.grad)==pytest.approx(1.5,abs=1e-6)
    assert variant.target_entropy==-1.5
    assert variant.full_state_dict()['task9_opt_scientific_config']['target_entropy']==-1.5


@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-float('inf'),None,True,'-1.5'])
def test_entropy_invalid_rejected(bad):
    with pytest.raises(ValueError,match='target_entropy'):LowerSAC(74,DEVICE,dict(cfg(),target_entropy=bad))


@pytest.mark.parametrize('axis,value',[('target_entropy',-1.5),('update_every_transfers',20),('replay_capacity',200000),('episode_end_bootstrap',False)])
def test_restore_rejects_any_scientific_config_drift(axis,value):
    original=LowerSAC(74,DEVICE,cfg());saved=copy.deepcopy(original.full_state_dict())
    changed=LowerSAC(74,DEVICE,dict(cfg(),**{axis:value}))
    with pytest.raises(ValueError,match='scientific'):changed.load_full_state_dict(saved)


def test_u20_old_replay_order_and_exact_count():
    from types import SimpleNamespace
    from task8_lower.training import consume_transition
    config=dict(cfg(),batch_size=2,replay_capacity=16,update_every_transfers=20)
    sac=LowerSAC(74,DEVICE,config);r=Replay(16,74,4,DEVICE)
    tr=SimpleNamespace(observation=obs(1),raw_action=torch.zeros(1,3),reward=torch.ones(1),next_observation=obs(1),mask=torch.ones(1),attempted=torch.ones(1),committed=torch.ones(1),dt=torch.ones(1))
    state=dict(steps=0,pending=dict(cursor=0),attempted=0,committed=0,sim_s=0.)
    assert not update_due(20,2,config)
    assert [x for x in range(1,101) if update_due(x,3,config)]==[20,40,60,80,100]
    for _ in range(41):consume_transition(sac,r,state,tr,0,config,torch.zeros(1,dtype=torch.bool))
    assert sac.update_count==2 and state['steps']==41
    assert r.inserted_at[r.position-1].item()==41


def test_r200_actual_capacity_shapes_and_uniform_sampling():
    # Real storage allocation is virtual on CPU: touch only the inserted rows.
    replay=Replay(200000,74,41,DEVICE)
    assert replay.map_s.shape==(200000,128,128,3) and replay.map_n.shape==replay.map_s.shape
    assert replay.rob_s.shape==(200000,74) and replay.map_s.dtype==torch.uint8
    for i in range(12):
        replay.push(obs(1),torch.full((1,3),float(i)),torch.ones(1),obs(1),torch.ones(1),transfer=i+1,failed=torch.zeros(1,dtype=torch.bool))
    expected=random.Random(41).sample(range(12),8)
    assert replay.sample_indices(8)==expected and len(set(expected))==8
    saved=replay.state_dict();clone=Replay(200000,74,0,DEVICE);clone.load_state_dict(saved)
    assert clone.sample_indices(8)==replay.sample_indices(8)
    exact(replay.gather([0,11]),clone.gather([0,11]))


def test_formal_configs_exact_one_axis_and_identity_rejection():
    from task8_lower.evaluation import evaluation_plan
    for group in GROUP_AXES:
        for seed in (4718,4719):
            value=json.loads((ASSET_ROOT/f'config/task9/opt/{group}_seed{seed}.json').read_text())
            validate_formal_config(value)
            with pytest.raises(ValueError):validate_formal_config(dict(value,batch_size=128))
            cube=json.loads(Path(value['pool']).read_text());semantic=json.loads(Path(value['transfer_pool']).read_text())
            val,trans=evaluation_plan(cube,semantic,value)
            assert len(val)==100 and len(trans)==96
    files=import_manifest()
    assert all('/task9_opt/' in v['file'] for k,v in files.items())
    seeds=json.loads(Path(value['evaluation_seeds']).read_text());seeds['semantic_manifest']='wrong/path'
    with pytest.raises(ValueError,match='path identity'):evaluation_plan(cube,semantic,value,seeds)


def test_actual_policy_replay_and_optimizer_device_path(tmp_path):
    config=dict(cfg(),replay_capacity=4)
    sac=LowerSAC(74,DEVICE,config);sac.update_from_batch(batch(),0,transfer=260)
    replay=Replay(4,74,7,DEVICE)
    evidence=dict(policy_device=str(next(sac.policy.parameters()).device),replay_device=str(replay.map_s.device),
        optimizer_devices={name:sorted({str(v.device) for entry in optimizer.state.values() for v in entry.values() if torch.is_tensor(v)})
            for name,optimizer in [('actor',sac.policy_optim),('critic',sac.critic_optim),('alpha',sac.alpha_optim)]},
        torch=torch.__version__,cuda=torch.version.cuda,test_device=DEVICE)
    assert evidence['policy_device'].startswith(DEVICE) and evidence['replay_device'].startswith(DEVICE)
    assert all(any(d.startswith(DEVICE) for d in values) for values in evidence['optimizer_devices'].values())
    directory=Path(os.environ.get('TASK9_EVIDENCE_DIR',str(tmp_path)))
    (directory/'device-path.json').write_text(json.dumps(evidence,indent=2)+'\n')


def test_pause_gate_rejects_scientific_limit_alias(tmp_path):
    from task8_lower.training import train
    # This validation runs before any environment or GPU construction.
    with pytest.raises(ValueError,match='strictly inside'):train(dict(cfg(),device='cpu'),tmp_path,pause_after_consumed=3000000)
