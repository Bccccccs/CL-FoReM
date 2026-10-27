#!/usr/bin/env python3
"""Bounded reset-only I1 instrumentation; no training or sampling rule changes."""
import argparse, collections, copy, hashlib, json, os, time
from pathlib import Path
import numpy as np
import torch
from task8_sim import assets, episode, scene
from task8_sim.env import PcdEpisodeEnv
from task8_sim.profile_lower import prohibit_training, runtime


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--wall-s',type=float,default=380)
    a=p.parse_args();cfg=json.loads(Path(a.config).read_text());out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    guards=prohibit_training();torch.set_num_threads(cfg['threads']);totals=collections.defaultdict(float);counts=collections.Counter();rows=[]
    parse_active=False
    original_read=Path.read_bytes
    def read_bytes(path):
        t=time.monotonic()
        try:return original_read(path)
        finally:
            if str(path).endswith('.pcd'):
                totals['pcd_read_s']+=time.monotonic()-t;counts['pcd_reads']+=1
                totals['pcd_parse_read_s' if parse_active else 'pcd_hash_read_s']+=time.monotonic()-t
    Path.read_bytes=read_bytes
    def wrap(obj,name,label):
        original=getattr(obj,name)
        def call(*args,**kw):
            t=time.monotonic()
            try:return original(*args,**kw)
            finally:totals[label]+=time.monotonic()-t;counts[label]+=1
        setattr(obj,name,call)
    original_parse=assets._read_pcd
    def parse(*args,**kw):
        nonlocal parse_active
        t=time.monotonic();parse_active=True
        try:return original_parse(*args,**kw)
        finally:totals['pcd_parse_including_read_s']+=time.monotonic()-t;parse_active=False
    assets._read_pcd=parse
    wrap(episode,'load_asset','asset_total_s')
    wrap(scene,'_pack','pack_s');wrap(scene,'_bvh','bvh_s')
    original_from=scene.VoxelScene.from_asset
    def from_asset(cls,*args,**kw):
        t=time.monotonic();result=original_from(*args,**kw)
        pr=result.provenance();totals['scene_preprocess_s']+=pr['cpu_preprocess_s'];totals['scene_upload_s']+=pr['device_upload_wall_s'];totals['scene_total_s']+=time.monotonic()-t;counts['scenes']+=1
        return result
    scene.VoxelScene.from_asset=classmethod(from_asset)
    wrap(episode.PcdTruthPlanner,'__init__','planner_build_s')
    wrap(episode.PcdTruthPlanner,'witness_cells','witness_cells_s')
    start=time.monotonic();env=PcdEpisodeEnv(cfg['environments'],seed=cfg['seed'],pool=cfg['pool'],profile=cfg['profile'],device='cuda:0',dtype=torch.float32,split=cfg['train_split'])
    env.kin.dls_cuda_graph=cfg['dls_cuda_graph']
    original_sample=env.sampler.sample
    def save(status,error=None):
        elapsed=time.monotonic()-start
        disjoint=dict(pcd_read_s=totals['pcd_read_s'],pcd_parse_s=totals['pcd_parse_including_read_s']-totals['pcd_parse_read_s'],
                      asset_other_s=totals['asset_total_s']-totals['pcd_parse_including_read_s']-totals['pcd_hash_read_s'],
                      voxel_height_s=totals['scene_preprocess_s']-totals['pack_s']-totals['bvh_s'],pack_s=totals['pack_s'],bvh_s=totals['bvh_s'],upload_s=totals['scene_upload_s'],planner_build_s=totals['planner_build_s'],initial_s=env.sampler.timing['initial_s'],planning_s=env.sampler.timing['planning_s'],witness_s=env.sampler.timing['witness_s'],witness_cells_s=totals['witness_cells_s'])
        # load_asset hashes each PCD, then parser reads it again; time both reads.
        doc=dict(status=status,error=error,elapsed_s=elapsed,config=cfg,stats=env.sampler.stats,timing=env.sampler.timing,raw=dict(totals),counts=dict(counts),components=disjoint,rows=rows,guards=guards,runtime=runtime(),hashes={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [Path(__file__),Path(scene.__file__),Path(assets.__file__),Path(episode.__file__)]})
        tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(doc,indent=2)+'\n');tmp.replace(out)
    def sample(*args,**kw):
        t=time.monotonic();e=original_sample(*args,**kw);rows.append(dict(index=len(rows),map_id=e.map_id,seed=e.seed,wall_s=time.monotonic()-t,stats=copy.deepcopy(env.sampler.stats)));save('running');return e
    env.sampler.sample=sample
    status='pass';error=None
    try:
        with torch.no_grad():env.reset(deadline=start+a.wall_s)
    except Exception as exc:status='incomplete';error=repr(exc)
    finally:save(status,error)
    print(json.dumps(dict(status=status,elapsed_s=time.monotonic()-start,accepted=len(rows),stats=env.sampler.stats,timing=env.sampler.timing)),flush=True)
    return 0 if status=='pass' else 2

if __name__=='__main__':raise SystemExit(main())
