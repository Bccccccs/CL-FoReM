"""Single task7 Core with PCD-only reset and explicit scientific profiles.

Reuse EpisodeEnv._ids/begin/step/info read-only; reset adapted from env.py
SHA256 ae2c447f12d2a9d7cabf578163a6c71ae9872316a737b9deb7432841ed85e7e3.
"""
import json
from pathlib import Path
import torch
from task7_sim.env import EpisodeEnv, BatchStep
from task7_sim.core import Core, State
from task7_sim.perception import Grid
from task7_sim.kinematics import Kinematics, metrics
from task7_lower.observation import VERSION as OBSERVATION_VERSION
from task7_sim.lower_policy import ACTION_VERSION
from .episode import PcdEpisodeSampler, RandomStreams, SceneCollision, validate_initial_state, manifest_path, check_sampling
from .routes import batch_routes
from .scene import SceneBatch
from .primitive_scene import ENVIRONMENT_VERSION as PRIMITIVE_ENVIRONMENT_VERSION, V3_BACKEND, make_scene_batch, resolve_backend
from .robot import GhostRobotGeometry
from .perception import PcdPanorama

ENVIRONMENT_VERSION='task8-pcd-v3'
PROFILES={
    'sync_v5':dict(synchronous=True,failure_mode='cbl_continue',async_time_penalty=0.,episode_end_bootstrap=True,ik_avoid_collision=True),
    'decision_sync_legacy':dict(synchronous=True,failure_mode='terminal',async_time_penalty=1.,episode_end_bootstrap=False,ik_avoid_collision=True),
    'decision_async_legacy':dict(synchronous=False,failure_mode='terminal',async_time_penalty=1.,episode_end_bootstrap=False,ik_avoid_collision=True),
}

def profile_options(profile):
    if profile not in PROFILES:raise ValueError(f'explicit supported profile required: {profile}')
    return PROFILES[profile].copy()


class PcdEpisodeEnv(EpisodeEnv):
    def __init__(self,batch,*,seed,pool,profile,device,dtype,factory=None,split='smoke',difficulty=None,map_backend=V3_BACKEND):
        options=profile_options(profile);self.profile=profile;self.map_backend=resolve_backend(map_backend)
        self.pool=manifest_path(pool)
        for key,value in options.items():setattr(self,key,value)
        self.batch=batch;self.streams=RandomStreams(seed,batch);self.core=None
        self.kin=Kinematics();self.robot=GhostRobotGeometry()
        self.sampler=None if factory is not None else PcdEpisodeSampler(self.pool,split=split,difficulty=difficulty,device=device,dtype=dtype,kin=self.kin,robot=self.robot,profile=profile,map_backend=self.map_backend)
        self.factory=factory;self.device=torch.empty(0,device=device).device;self.dtype=dtype
        self.map_ids=['<uninitialized>']*batch;self.proposal_seeds=[None]*batch
        self.episode_count=None;self.totals=None;self.scenes=None
        self.sampling_deadline=None;self.sampling_cancel=None
        self.sensor_config=json.loads((Path(__file__).resolve().parents[2]/'config/task8/sensor.json').read_text())
        self.versions=dict(environment=ENVIRONMENT_VERSION if self.map_backend==V3_BACKEND else PRIMITIVE_ENVIRONMENT_VERSION,map_backend=self.map_backend,sensor_policy='ghost-v1',profile=profile,observation=OBSERVATION_VERSION,action=ACTION_VERSION)

    def load_state_dict(self,state):
        raise ValueError('environment restore rejected: construct/reset task8 PCD environment; actor-only policy loading is separate')

    def __setstate__(self,state):
        raise ValueError('environment pickle restore rejected; task8 requires fresh reset')

    def reset(self,indices=None,*,deadline=None,cancel=None):
        deadline=self.sampling_deadline if deadline is None else deadline
        cancel=self.sampling_cancel if cancel is None else cancel
        ids=self._ids(indices)
        if self.core is None and ids!=list(range(self.batch)):raise RuntimeError('initial reset requires the whole batch')
        if self.core is not None and any(not (self.core.terminated[i]|self.core.truncated[i]) for i in ids):raise RuntimeError('reset requires ended episodes')
        if not ids:return self.info()
        episodes=[]
        for i in ids:
            check_sampling(deadline,cancel)
            e=self.factory(i,self.streams.for_env(i)) if self.factory is not None else self.sampler.sample(self.streams.for_env(i),deadline=deadline,cancel=cancel)
            check_sampling(deadline,cancel)
            if e.map_id!=e.scene.provenance()['map_id']:raise ValueError('episode map id must match scene provenance')
            episodes.append(e)
        reference=episodes[0].base;device,dtype=reference.device,reference.dtype
        if (device,dtype)!=(self.device,self.dtype):raise ValueError('reset device/dtype mismatch')
        state=State(torch.cat([e.base for e in episodes]),torch.cat([e.q for e in episodes]),torch.zeros(len(ids),device=device,dtype=dtype))
        route=batch_routes([e.route for e in episodes],device=device,dtype=dtype)
        selected_scenes=make_scene_batch([e.scene for e in episodes])
        actual=validate_initial_state(state.base,state.q,self.kin,self.robot,SceneCollision(selected_scenes,self.robot))
        distance,_,angle=metrics(actual,route.at(state.s))
        if (distance>1e-4).any() or (angle>1e-4).any():raise ValueError('initial route must start at actual FK (N1 exact tolerances)')
        selected=torch.tensor(ids,device=device,dtype=torch.long)
        if self.core is None:
            self.scenes=selected_scenes
            self.core=Core(state,route,Grid.empty(self.batch,device=device,dtype=dtype),self.kin,self.robot,SceneCollision(self.scenes,self.robot),renderer=PcdPanorama(self.scenes,sensor_config=self.sensor_config),**profile_options(self.profile))
            self.episode_count=torch.zeros(self.batch,device=device,dtype=torch.long)
            self.totals={k:torch.zeros_like(self.episode_count) for k in ('sensor_frames','origin_inside_self_frames','fully_occluded_frames')}
        else:
            c=self.core;mask=torch.zeros_like(c.done);mask[selected]=True
            c.reset(mask,state,route)
            self.scenes.replace(ids,[e.scene for e in episodes])
        c=self.core
        depth=PcdPanorama(self.scenes.select(ids),sensor_config=self.sensor_config)(c.state.base[selected],self.robot(c.state.base[selected],c.state.q[selected]))
        grid=Grid.empty(len(ids),device=device,dtype=dtype);grid.update(depth.points,depth.valid,c.state.s[selected])
        c.grid.observed[selected]=grid.observed;c.grid.height[selected]=grid.height;c.grid.timestamp[selected]=grid.timestamp
        c.record_render(depth,torch.ones(len(ids),device=device,dtype=torch.bool),indices=selected)
        for key in self.totals:self.totals[key][selected]+=getattr(c,key)[selected]
        self.episode_count[selected]+=1
        for i,e in zip(ids,episodes):self.map_ids[i]=e.map_id;self.proposal_seeds[i]=e.seed
        return self.info()

    def info(self):
        result=super().info()
        if self.core is not None:
            result['versions']=self.versions.copy()
            result['out_of_map']=(self.core.state.base[:,:2].abs()>=5).any(-1)
        return result
