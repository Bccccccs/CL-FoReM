"""task8.11 W: map_backend config wiring. Never constructs an optimizer, LowerSAC, or any update."""
import json
from pathlib import Path
import pytest
import torch

ROOT=Path(__file__).resolve().parents[3]
CFG=ROOT/'config/task8'
V3='pcd-voxel-v3';P='primitive-obb-v1'


def cfg(name):return json.loads((CFG/name).read_text())


def test_default_backend_is_v3_and_existing_configs_unchanged():
    from task8_lower.evaluation import resolve_map_backend
    for g in ('B0','B3'):
        c=cfg(f'lower_train_{g}.json')
        assert 'map_backend' not in c and c['environment_geometry_version']==V3
        assert resolve_map_backend(c)==V3


@pytest.mark.parametrize('group',['B0','B3'])
def test_prim_config_differs_only_in_backend_fields(group):
    from task8_lower.evaluation import resolve_map_backend
    a,b=cfg(f'lower_train_{group}.json'),cfg(f'lower_train_{group}_prim.json')
    changed={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
    assert changed=={'map_backend','environment_geometry_version'}
    assert resolve_map_backend(b)==P


def test_mismatch_and_unknown_backend_rejected():
    from task8_lower.evaluation import resolve_map_backend
    from task8_lower.training import validate_config
    c=cfg('lower_train_B0.json')
    with pytest.raises(ValueError,match='contradicts'):resolve_map_backend({**c,'map_backend':P})
    with pytest.raises(ValueError,match='contradicts'):resolve_map_backend({**cfg('lower_train_B0_prim.json'),'environment_geometry_version':V3})
    with pytest.raises(ValueError,match='unsupported map_backend'):resolve_map_backend({**c,'map_backend':'nope','environment_geometry_version':'nope'})
    validate_config(c);validate_config(cfg('lower_train_B0_prim.json'))
    with pytest.raises(ValueError):validate_config({**c,'map_backend':P})


@pytest.mark.parametrize('name,expected',[('lower_train_B0.json',V3),('lower_train_B3_prim.json',P)])
def test_train_passes_backend_to_env_factory_before_any_sac(tmp_path,name,expected):
    """train() calls env_factory before constructing LowerSAC; a sentinel stops it there, so no optimizer exists."""
    from task8_lower.training import train
    seen={}
    class Stop(Exception):pass
    def factory(*args,**kwargs):
        seen['args']=args;seen['kwargs']=kwargs;raise Stop()
    c=cfg(name);c['device']='cpu'
    with pytest.raises(Stop):train(c,tmp_path,transfers=1,env_factory=factory)
    assert seen['kwargs']['map_backend']==expected and seen['args']==(256,)


def test_evaluation_environment_receives_backend_without_loading_scenes():
    from task8_lower.evaluation import evaluation_environment
    pool=ROOT/'results/task8/t8-pool-20261027/cube-pool-v2/manifest.json'
    if not pool.exists():pytest.skip('cube-pool-v2 absent')
    entry=[e for e in json.loads(pool.read_text())['maps'] if e['split']=='validation'][0]
    job=dict(map_id=entry['id'],seed=1,stream_index=0,role='validation',source_split='validation',episode_index=0,entry=entry)
    for name,expected in (('lower_train_B0.json',V3),('lower_train_B0_prim.json',P)):
        c=cfg(name);env=evaluation_environment([job],c,pool,torch.device('cpu'))
        assert env.map_backend==expected and env.versions['map_backend']==expected  # reset (scene load) not called
    with pytest.raises(ValueError,match='contradicts'):evaluation_environment([job],{**cfg('lower_train_B0.json'),'map_backend':P},pool,torch.device('cpu'))


def test_environment_state_roundtrip_keeps_backend():
    from task8_lower.training import environment_state,restore_environment
    from task8_sim.env import PcdEpisodeEnv
    pool=ROOT/'results/task8/t8-pool-20261027/cube-pool-v2/manifest.json'
    if not pool.exists():pytest.skip('cube-pool-v2 absent')
    for backend in (V3,P):
        env=PcdEpisodeEnv(1,seed=1,pool=pool,profile='sync_v5',device='cpu',dtype=torch.float32,split='train',map_backend=backend)
        restored=restore_environment(environment_state(env),'cpu')
        assert restored.map_backend==backend and restored.versions['map_backend']==backend
