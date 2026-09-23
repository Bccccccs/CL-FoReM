from pathlib import Path
import pytest

def test_seed_manifest_rejects_duplicate_or_training_seeds(tmp_path):
    from p0_runner import read_seeds
    p=tmp_path/'seeds.json'
    p.write_text('[10000,10001]')
    assert read_seeds(p,2) == [10000,10001]
    for text in ['[10000,10000]','[11,22]','[10000]']:
        p.write_text(text)
        with pytest.raises(ValueError): read_seeds(p,2)


def test_legacy_prior_loads_without_critic_or_device_attribute(tmp_path):
    import torch
    from types import SimpleNamespace
    from model import GaussianPolicy
    from test_sac_updates import spaces
    from p0_runner import checkpoint_hidden_sizes,load_weights
    obs,act=spaces()
    original=GaussianPolicy(obs[1],obs[0],3,[512,512,256],act,use_sde=False)
    path=tmp_path/'legacy.pt'
    torch.save({'policy_state_dict':original.state_dict()},path)
    sizes=checkpoint_hidden_sizes(path)
    assert sizes == [512,512,256]
    restored=SimpleNamespace(policy=GaussianPolicy(obs[1],obs[0],3,sizes,act,use_sde=False))
    assert load_weights(restored,path)=='legacy_weights_reinterpreted_v2'
    maps=torch.zeros(1,120,120,1);robots=torch.ones(1,41)
    assert torch.equal(original.predict(maps,robots,True),restored.policy.predict(maps,robots,True))


def test_environment_parser_ignores_outer_resume_flag(monkeypatch):
    import sys
    from modulation.utils import parse_args
    monkeypatch.setattr(sys,'argv',['p0_runner.py','train','--resume','checkpoint.pt'])
    _,_,config,_=parse_args(Path(__file__).resolve().parents[1],framework='ray',
                           raw_args=['--env','husky_ur5','--task','simpleobstacle','--seed','11'])
    assert config['seed']==11 and config['env']=='husky_ur5'


def test_gazebo_training_rejects_shared_simulator_periodic_evaluation(tmp_path):
    import subprocess,sys
    result=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'p0_runner.py'),
        'train','--world-type','gazebo','--output',str(tmp_path/'out')],capture_output=True,text=True,timeout=30)
    assert result.returncode!=0
    assert 'evaluation must use an isolated simulator' in result.stderr
    assert not (tmp_path/'out').exists()


def test_episode_command_always_isolates_one_seed_and_retains_protocol(tmp_path):
    from argparse import Namespace
    from p0_runner import episode_command
    args=Namespace(checkpoint='/tmp/weights.pt',task='picknplace',world_type='sim',device='cpu',
                   seed=11,max_episode_steps=317)
    command=episode_command(args,tmp_path,10019)
    assert command.count('--episode-worker')==1
    assert command[command.index('--episodes')+1]=='1'
    assert command[command.index('--max-episode-steps')+1]=='317'
    import json
    assert json.loads(Path(command[command.index('--seeds')+1]).read_text())==[10019]


def test_fixed_ik_worker_keeps_budget(tmp_path):
    from argparse import Namespace
    from p0_runner import episode_command
    args=Namespace(checkpoint='/tmp/weights.pt',task='simpleobstacle',world_type='sim',device='cpu',seed=11,max_episode_steps=80,ik_mode='fixed',ik_iterations=12)
    command=episode_command(args,tmp_path,10008)
    assert command[command.index('--ik-mode')+1]=='fixed'
    assert command[command.index('--ik-iterations')+1]=='12'
