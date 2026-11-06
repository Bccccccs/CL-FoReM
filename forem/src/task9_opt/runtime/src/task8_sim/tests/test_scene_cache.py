"""r4 cache contract: changing any source identity must reject, never rebuild."""
import importlib.util
import json
import numpy as np
import pytest
import torch
from task8_sim.assets import load_asset
from task8_sim.scene import VoxelScene
from task8_sim.tests.test_assets import make
from task8_sim.tests import assets_reference_r3 as reference


def cache_api():
    assert importlib.util.find_spec('task8_sim.scene_cache') is not None, 'derived scene cache is missing'
    from task8_sim import scene_cache
    return scene_cache


def test_cache_exact_and_rejects_stale_source(tmp_path):
    api=cache_api();manifest=make(tmp_path);asset=load_asset(manifest,'m');original=VoxelScene.from_asset(asset,device='cpu',dtype=torch.float64)
    root=tmp_path/'cache';record=api.write_scene(root,asset,original)
    api.write_index(root,[record]);cached=api.SceneCache(root).load(manifest,asset.metadata,device='cpu',dtype=torch.float64)
    for name in api.TENSORS:assert torch.equal(getattr(original,name),getattr(cached,name))
    (tmp_path/'map.pcd').write_text('changed')
    with pytest.raises(ValueError,match='hash'):api.SceneCache(root).load(manifest,asset.metadata,device='cpu',dtype=torch.float64)


def test_cache_rejects_key_payload_metadata(tmp_path):
    api=cache_api();manifest=make(tmp_path);asset=load_asset(manifest,'m');scene=VoxelScene.from_asset(asset,device='cpu',dtype=torch.float64)
    root=tmp_path/'cache';record=api.write_scene(root,asset,scene);api.write_index(root,[record])
    entry=dict(asset.metadata,difficulty='changed')
    with pytest.raises(ValueError,match='metadata'):api.SceneCache(root).load(manifest,entry,device='cpu',dtype=torch.float64)
    index=json.loads((root/'index.json').read_text());index['scene_sha256']='0'*64;(root/'index.json').write_text(json.dumps(index))
    with pytest.raises(ValueError,match='key'):api.SceneCache(root)
    api.write_index(root,[record]);(root/record['file']).write_bytes(b'broken')
    with pytest.raises(ValueError,match='payload hash'):api.SceneCache(root).load(manifest,asset.metadata,device='cpu',dtype=torch.float64)


@pytest.mark.parametrize('data',[
 b'0 -0 0.0000000000000001\n',b'1e-310 2.2250738585072014e-308 -0\n',
 b'0 nan 0\n',b'0 inf 0\n',b'0 bad 0\n',b'0 0\n',b'0 0 0 extra\n',b'0 \xff 0\n'])
def test_parser_reference_bits_and_error_identity(tmp_path,data):
    manifest=make(tmp_path);p=tmp_path/'map.pcd';head=p.read_bytes().split(b'DATA ascii\n')[0]+b'DATA ascii\n';p.write_bytes(head+data)
    def result(fn):
        try:return fn(p,'m')
        except Exception as exc:return type(exc),str(exc)
    from task8_sim.assets import _read_pcd
    old,new=result(reference._read_pcd),result(_read_pcd)
    if isinstance(old,tuple):assert old==new
    else:assert np.array_equal(old.view(np.uint64),new.view(np.uint64))


def test_training_contract_binds_cache_module_and_runtime_index(tmp_path,monkeypatch):
    from task8_lower.training import _contract
    monkeypatch.delenv('TASK8_SCENE_CACHE',raising=False);plain=_contract()
    assert 'src/task8_sim/scene_cache.py' in plain
    assert 'src/task8_sim/assets.py' in plain
    assert plain['runtime_scene_cache'] is None
    (tmp_path/'index.json').write_text('{}');monkeypatch.setenv('TASK8_SCENE_CACHE',str(tmp_path))
    first=_contract();assert first!=plain
    (tmp_path/'index.json').write_text('{"changed":true}');assert _contract()!=first
