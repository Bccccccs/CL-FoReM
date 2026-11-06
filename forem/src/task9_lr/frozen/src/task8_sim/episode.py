"""PCD-only proposals; task7 RNG/distribution/CBL joints/IK witness preserved.

Sampling control never becomes an episode failure/truncation or relaxed task.
Adapted EpisodeSampler.sample from task7_sim/episode.py (SHA256
 db831097bebe98037bb705870d6d2f6a4ad0af20998c5bf3cb4506bf8e78b5ae).
"""
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import time
import numpy as np
import torch
from task7_sim.episode import (RandomStreams, CBL_Q, sample_base, sample_goal,
                              validate_initial_state, validate_goal_witness)
from task7_sim.kinematics import Kinematics
from .assets import load_asset
from .scene import VoxelScene
from .robot import GhostRobotGeometry
from .routes import PcdTruthPlanner
from .primitive_scene import V3_BACKEND, load_backend_scene, resolve_backend


class SamplingIncomplete(TimeoutError):
    """External execution budget/cancel, never natural environment truncated."""


def check_sampling(deadline=None,cancel=None):
    if cancel is not None and (cancel() if callable(cancel) else cancel.is_set()):raise SamplingIncomplete('sampling cancelled; incomplete')
    if deadline is not None and time.monotonic()>=deadline:raise SamplingIncomplete('sampling deadline; incomplete')


def manifest_path(pool):
    if pool is None:raise ValueError('explicit PCD pool required; no legacy pool fallback')
    path=Path(pool)
    if path.is_dir():
        choices=[p for p in (path/'manifest.json',path/'index.json') if p.is_file()]
        if len(choices)!=1:raise ValueError('PCD pool requires exactly one manifest.json or index.json')
        path=choices[0]
    if not path.is_file():raise ValueError(f'PCD pool manifest missing: {path}')
    return path


@dataclass
class PcdEpisode:
    base:torch.Tensor
    q:torch.Tensor
    route:object
    scene:VoxelScene
    map_id:str='<fixture>'
    witness_base:torch.Tensor|None=None
    witness_q:torch.Tensor|None=None
    seed:int|None=None


class SceneCollision:
    """Core callable; single VoxelScene also accepts witness batches of 64."""
    def __init__(self,scene,robot):self.scene=scene;self.robot=robot
    def __call__(self,base,caps,allowed=None,q=None):
        return self.scene.collide(base,caps,robot=self.robot,q=q,allowed=allowed)


def validate_goal_position(goal,start_base,scene):
    if goal.shape!=(len(start_base),3) or not torch.isfinite(goal).all():raise ValueError('goal shape/finite')
    radius=(goal[:,:2]-start_base[:,:2]).norm(dim=-1)
    valid=(goal[:,:2].abs()<5).all(-1)&(radius>=.5)&(radius<=8)&(goal[:,2]>=.7)&(goal[:,2]<=1.15)
    return valid&~scene.contains(goal)


class PcdEpisodeSampler:
    def __init__(self,pool,*,split,difficulty,device,dtype,kin,robot,profile,map_backend=V3_BACKEND):
        from .env import profile_options
        profile_options(profile)
        self.map_backend=resolve_backend(map_backend)
        self.profile=profile;self.pool=manifest_path(pool)
        doc=json.loads(self.pool.read_text())
        if doc.get('schema_version')!='task8-pcd-v1':raise ValueError('unsupported PCD pool schema')
        self.entries=[e for e in doc['maps'] if e['split']==split and (difficulty is None or e['difficulty']==difficulty)]
        if not self.entries:raise ValueError('map pool split/difficulty has no maps')
        self.device=torch.device(device);self.dtype=dtype
        self.kin=Kinematics() if kin is None else kin;self.robot=GhostRobotGeometry() if robot is None else robot
        self.planners={};self.deadline=None;self.cancel=None
        cache_root=os.environ.get('TASK8_SCENE_CACHE')
        from .scene_cache import SceneCache
        self.scene_cache=SceneCache(cache_root) if cache_root else None
        self.stats=dict(proposals=0,accepted=0,rejections={},witness_targets=0,witness_dls=0,initial_targets=0)
        self.timing=dict(asset_scene_s=0.,initial_s=0.,planning_s=0.,witness_s=0.,sample_s=0.)

    def sample(self,streams,*,deadline=None,cancel=None):
        deadline=self.deadline if deadline is None else deadline
        cancel=self.cancel if cancel is None else cancel
        started=time.monotonic()
        try:
            while True:
                check_sampling(deadline,cancel)
                self.stats['proposals']+=1
                entry=self.entries[int(streams.maps.integers(len(self.entries)))];key=entry['id']
                seed=int(streams.initial.integers(0,np.iinfo(np.int64).max));rng=np.random.default_rng(seed)
                t=time.monotonic()
                if key not in self.planners:
                    if self.map_backend!=V3_BACKEND:scene=load_backend_scene(self.map_backend,self.pool,key,device=self.device,dtype=self.dtype)
                    elif self.scene_cache is None:
                        asset=load_asset(self.pool,key)
                        scene=VoxelScene.from_asset(asset,device=self.device,dtype=self.dtype)
                    else:scene=self.scene_cache.load(self.pool,entry,device=self.device,dtype=self.dtype)
                    self.planners[key]=PcdTruthPlanner(scene)
                self.timing['asset_scene_s']+=time.monotonic()-t
                check_sampling(deadline,cancel)
                planner=self.planners[key];scene=planner.scene;collision=SceneCollision(scene,self.robot)
                base=torch.as_tensor(sample_base(rng),device=self.device,dtype=self.dtype)[None]
                q=torch.tensor(CBL_Q,device=self.device,dtype=self.dtype)[None]
                t=time.monotonic()
                try:
                    self.stats['initial_targets']+=1
                    start=validate_initial_state(base,q,self.kin,self.robot,collision)[0]
                except ValueError:
                    self._reject('initial');continue
                finally:self.timing['initial_s']+=time.monotonic()-t
                check_sampling(deadline,cancel)
                goal=torch.as_tensor(sample_goal(base[0].cpu().double().numpy(),rng),device=self.device,dtype=self.dtype)
                if not validate_goal_position(goal[None],base,scene).item():self._reject('goal');continue
                t=time.monotonic()
                try:route=planner.plan(start,goal)
                except ValueError:self._reject('route');continue
                finally:self.timing['planning_s']+=time.monotonic()-t
                check_sampling(deadline,cancel)
                target=route.at(route.length)
                xy=planner.witness_cells(base[0].cpu().double().numpy(),goal.cpu().double().numpy())
                if not len(xy):self._reject('base_connected_region');continue
                order=rng.permutation(len(xy));xy=xy[order];yaw=rng.uniform(0,2*math.pi,len(xy))
                witness=None
                for offset in range(0,len(xy),64):
                    check_sampling(deadline,cancel)
                    end=min(offset+64,len(xy));n=end-offset
                    poses=torch.as_tensor(np.c_[xy[offset:end],yaw[offset:end]],device=self.device,dtype=self.dtype)
                    t=time.monotonic()
                    result,valid=validate_goal_witness(poses,q.expand(n,-1),target.expand(n,-1,-1),self.kin,self.robot,collision)
                    self.stats['witness_targets']+=n;self.stats['witness_dls']+=int((result.branch<0).sum())
                    if self.device.type=='cuda':torch.cuda.synchronize(self.device)
                    self.timing['witness_s']+=time.monotonic()-t
                    check_sampling(deadline,cancel)
                    ids=torch.where(valid)[0]
                    if len(ids):
                        j=int(ids[0]);witness=(poses[j:j+1].clone(),result.q[j:j+1].clone());break
                if witness is None:self._reject('goal_IK_collision_witness');continue
                self.stats['accepted']+=1
                return PcdEpisode(base,q,route,scene,key,*witness,seed)
        finally:self.timing['sample_s']+=time.monotonic()-started

    def _reject(self,reason):
        rejected=self.stats['rejections'];rejected[reason]=rejected.get(reason,0)+1
