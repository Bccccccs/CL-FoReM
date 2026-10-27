#!/usr/bin/env python3
"""Task8.9.1.1 bounded exact forest/loop acceptance, no training operations."""
import argparse
from dataclasses import fields
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import torch
from task8_sim.assets import MapAsset, load_asset
from task8_sim.scene import SceneBatch, VoxelScene
from task8_sim.perception import PcdPanorama
from task8_sim.profile_lower import prohibit_training
from task7_sim.robot import ROOT


def equal(a,b,path='value'):
    if isinstance(a,torch.Tensor):assert torch.equal(a,b),path
    elif isinstance(a,dict):
        assert a.keys()==b.keys(),path
        for k in a:equal(a[k],b[k],path+'.'+k)
    else:assert a==b,path


def core_steps(device,dtype,scenes,prep):
    from task8_sim.env import PcdEpisodeEnv
    from task8_sim.episode import PcdEpisode
    from task7_sim.core import Candidate
    from task7_sim.motion import Route
    # Saved accepted cube episodes give real nonempty geometry/routes. Both
    # paths receive identical converted input tensors, never a fresh sampler.
    episodes=[]
    for i in range(2):
        e=torch.load(prep['maps'][i]['cache'],map_location=device,weights_only=False)
        episodes.append(PcdEpisode(e.base.to(dtype=dtype),e.q.to(dtype=dtype),
            Route(e.route.xyz.to(dtype=dtype),e.route.quat.to(dtype=dtype)),scenes[i],e.map_id,seed=e.seed))
    envs=[PcdEpisodeEnv(2,seed=4819,pool=prep['pool'],profile='sync_v5',device=device,dtype=dtype,
           factory=lambda i,r:episodes[i]) for _ in range(2)]
    for e in envs:e.reset()
    envs[1].scenes.raycast_backend='loop'
    generator=torch.Generator(device=device).manual_seed(81927)
    active=committed=resets=0;names=None
    with torch.no_grad():
        for step in range(50):
            for e in envs:
                if (e.core.terminated|e.core.truncated).any():
                    e.reset();resets+=1
                c=e.core
                mask=c.done&~(c.terminated|c.truncated)
                if mask.any():
                    pose=c.state.base.clone();pose[:,0]+=.2
                    e.begin(Candidate(pose,c.route.length.clone(),torch.zeros_like(c.done)),mask=mask)
            assert [e.scenes.raycast_backend for e in envs]==['forest','loop']
            raw=torch.rand(2,3,device=device,dtype=dtype,generator=generator)*2-1
            aa,bb=[e.step(raw).transition for e in envs]
            names=[f.name for f in fields(aa)]
            for key in names:equal(getattr(aa,key),getattr(bb,key),f'step{step}.{key}')
            for key in ('base','q','s'):equal(getattr(envs[0].core.state,key),getattr(envs[1].core.state,key),'state.'+key)
            equal(envs[0].core.grid.height,envs[1].core.grid.height,'grid.height')
            active+=int(aa.active.sum());committed+=int(aa.committed.sum())
            # Histories retain scans; they are irrelevant after exact comparison.
            for e in envs:e.core.transitions.clear();e.core.trace.clear()
    assert active>=50 and committed>0
    return dict(steps=50,active_transitions=active,committed_substeps=committed,resets=resets,backends=['forest','loop'],fields=names,exact=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--device',choices=('cpu','cuda:0'),required=True)
    p.add_argument('--output',required=True);a=p.parse_args()
    started=time.monotonic();calls=prohibit_training();torch.set_num_threads(2)
    device=a.device;dtype=torch.float64 if device=='cpu' else torch.float32
    if device.startswith('cuda'):
        assert torch.cuda.is_available();torch.cuda.set_device(0);torch.cuda.reset_peak_memory_stats()
    root=ROOT/'results/task8/t8-perf-20261027'
    cube=json.loads((root/'cube-prepare.json').read_text());semantic=json.loads((root/'semantic-prepare.json').read_text())
    report=dict(status='running',device=device,dtype=str(dtype),guard=calls,ray_batches=[],depth_batches=[],sources=[])
    def save():
        report['wall_s']=time.monotonic()-started
        Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
    scenes=[]
    for prep,count in ((cube,32),(semantic,24)):
        for row in prep['maps'][:count]:
            asset=load_asset(prep['pool'],row['map_id'])
            scenes.append(VoxelScene.from_asset(asset,device=device,dtype=dtype))
            report['sources'].append(dict(map_id=asset.map_id,hashes=asset.hashes))
    # Empty plus hand-checked face/edge/corner scene supplements all 56 real maps.
    for points in ([],[[.021,.021,.521],[.121,.121,.621]]):
        scenes.append(VoxelScene.from_asset(MapAsset('edge-fixture',np.asarray(points,dtype=float).reshape(-1,3),{},None,{'pcd':'fixture','sidecar':None}),device=device,dtype=dtype))
    gen=torch.Generator(device=device).manual_seed(49817)
    config=json.loads((ROOT/'config/task8/sensor.json').read_text())
    for batch in (1,16,64,256):
        # Rotate small batches so every real map is tested even at batch1/16.
        for offset in range(0,len(scenes),batch):
            rows=[scenes[(offset+i)%len(scenes)] for i in range(batch)]
            forest=SceneBatch(rows);loop=SceneBatch(rows,raycast_backend='loop')
            o=torch.rand(batch,96,3,device=device,dtype=dtype,generator=gen)*o_scale(device,dtype)+torch.tensor([-6.,-6.,-.2],device=device,dtype=dtype)
            d=torch.randn(batch,96,3,device=device,dtype=dtype,generator=gen)
            d=d/torch.linalg.vector_norm(d,dim=-1,keepdim=True)
            edge_o=torch.tensor([[-1.,.025,.525],[.025,.025,.525],[-6.,0.,.5],[-1.,0.,.5],[-1.,-1.,-.5],[5.1,0.,.5]],device=device,dtype=dtype)
            edge_d=torch.tensor([[1.,0.,0.],[1.,0.,0.],[1.,0.,0.],[1.,0.,0.],[1.,1.,1.],[-1.,0.,0.]],device=device,dtype=dtype)
            edge_d=edge_d/torch.linalg.vector_norm(edge_d,dim=-1,keepdim=True)
            o[:,:6]=edge_o;d[:,:6]=edge_d
            # Explicitly include occupied starts and exact packed faces per row.
            for i,s in enumerate(rows):
                if len(s._lo):
                    o[i,6]=(s._lo[0]+s._hi[0])/2;o[i,7]=s._lo[0]
                    d[i,6:8]=d.new_tensor([1.,0.,0.])
            x=forest.raycast(o,d,max_range=6.);y=loop.raycast(o,d,max_range=6.)
            equal(x,y,'distance');equal(torch.isfinite(x),torch.isfinite(y),'hit')
        report['ray_batches'].append(dict(batch=batch,covered_scenes=len(scenes),rays_per_row=96,exact=True));save()
        # Each size uses a full 360x90 panorama. b64/256 cover all 56 maps.
        rows=[scenes[i%len(scenes)] for i in range(batch)]
        forest=SceneBatch(rows);loop=SceneBatch(rows,raycast_backend='loop')
        base=torch.rand(batch,3,device=device,dtype=dtype,generator=gen)*base_scale(device,dtype)+torch.tensor([-5.5,-5.5,-3.],device=device,dtype=dtype)
        caps=base.new_empty(batch,0,7)
        x=PcdPanorama(forest,sensor_config=config)(base,caps)
        y=PcdPanorama(loop,sensor_config=config)(base,caps)
        equal(vars(x),vars(y),'Depth')
        report['depth_batches'].append(dict(batch=batch,fields=list(vars(x)),pixels=32400,exact=True));save()
    report['core']=core_steps(device,dtype,scenes,cube)
    assert calls==dict(optimizer_constructed=0,backward_calls=0)
    report['status']='pass';report['scene_sha256']=hashlib.sha256((ROOT/'src/task8_sim/scene.py').read_bytes()).hexdigest()
    if device.startswith('cuda'):report['peak_allocated_bytes']=torch.cuda.max_memory_allocated()
    save();print(json.dumps({k:v for k,v in report.items() if k!='sources'}))


def o_scale(device,dtype):return torch.tensor([12.,12.,2.],device=device,dtype=dtype)
def base_scale(device,dtype):return torch.tensor([11.,11.,6.],device=device,dtype=dtype)
if __name__=='__main__':main()
