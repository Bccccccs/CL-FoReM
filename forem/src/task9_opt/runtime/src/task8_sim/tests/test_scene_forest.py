"""Exact old/new raycast regression; catches row offsets and stale replace caches."""
import io
import numpy as np
import pytest
import torch
from task8_sim.assets import MapAsset
from task8_sim.scene import SceneBatch, VoxelScene


def scene(points, device='cpu', dtype=torch.float64):
    xyz=np.asarray(points,dtype=np.float64).reshape(-1,3)
    return VoxelScene.from_asset(MapAsset('forest-fixture',xyz,{},None,{'pcd':'fixture','sidecar':None}),device=device,dtype=dtype)


def test_forest_loop_exact_rows_empty_select_replace_and_restore():
    a=scene([[.021,.021,.521]]);b=scene([[1.021,.021,.521]]);empty=scene([])
    batch=SceneBatch([a,empty,b,a],raycast_backend='forest')
    origins=torch.tensor([[[-1.,.025,.525],[.025,.025,.525],[-6.,0.,.5],[-1.,0.,.5]]],dtype=torch.float64).expand(4,-1,-1)
    directions=torch.tensor([[[1.,0.,0.],[1.,0.,0.],[-1.,0.,0.],[1.,0.,0.]]],dtype=torch.float64).expand_as(origins)
    reference=SceneBatch(batch.scenes,raycast_backend='loop')
    assert torch.equal(batch.raycast(origins,directions,max_range=6),reference.raycast(origins,directions,max_range=6))
    assert batch.raycast(origins,directions,max_range=6)[:,0].tolist()==[1.,float('inf'),2.,1.]
    selected=batch.select([2,0]);assert selected.raycast_backend=='forest'
    batch.replace([0],[b]);reference.replace([0],[b])
    assert torch.equal(batch.raycast(origins,directions,max_range=6),reference.raycast(origins,directions,max_range=6))
    assert selected.raycast(origins[:2],directions[:2],max_range=6)[:,0].tolist()==[2.,1.]
    buf=io.BytesIO();torch.save(batch,buf);buf.seek(0)
    restored=torch.load(buf,weights_only=False)
    assert torch.equal(restored.raycast(origins,directions,max_range=6),reference.raycast(origins,directions,max_range=6))
    all_empty=SceneBatch([empty,empty],raycast_backend='forest')
    assert torch.isinf(all_empty.raycast(origins[:2],directions[:2],max_range=6)).all()
    assert all_empty.raycast(origins[:2,:0],directions[:2,:0],max_range=0).shape==(2,0)


@pytest.mark.parametrize('backend',['forest','loop'])
def test_forest_retains_query_validation(backend):
    batch=SceneBatch([scene([])],raycast_backend=backend)
    o=torch.zeros(1,2,3,dtype=torch.float64);d=o.clone();d[...,0]=1
    for oo,dd,maximum in [(o,d, float('inf')),(o,d,-1),(o.float(),d.float(),6),(o,d*2,6),(o[0],d[0],6),(o,d[:,:1],6)]:
        with pytest.raises(ValueError):batch.raycast(oo,dd,max_range=maximum)
    with pytest.raises(ValueError):SceneBatch(batch.scenes,raycast_backend='other')
