"""E5 single-Core batch environment with episode-local masked reset.

Only reset sampling/JSON planning uses per-environment host work. Every action
step is one E-dimensional Core.step with shared kinematics/robot geometry.
No networks, training, implicit policy, sensor snapping or autoreset.
"""
from dataclasses import dataclass
import torch
from .episode import RandomStreams, EpisodeSampler, validate_initial_state
from .core import Core, State
from .routes import batch_routes
from .kinematics import Kinematics, metrics
from .robot import RobotGeometry
from .geometry import pad_maps, TruthCollision
from .perception import Grid, Panorama


@dataclass
class BatchStep:
    transition: object
    info: dict

    @property
    def active(self):return self.transition.active


class EpisodeEnv:
    def __init__(self,batch,factory=None,*,seed,pool=None,split='train',difficulty=None,
                 device='cuda',dtype=torch.float32,synchronous=False,failure_mode='terminal',async_time_penalty=1.0,episode_end_bootstrap=False,ik_avoid_collision=True):
        self.failure_mode=failure_mode;self.async_time_penalty=async_time_penalty;self.episode_end_bootstrap=episode_end_bootstrap;self.ik_avoid_collision=ik_avoid_collision
        self.batch=batch;self.streams=RandomStreams(seed,batch);self.synchronous=synchronous
        self.kin=Kinematics();self.robot=RobotGeometry();self.core=None
        self.sampler=None if factory is not None else EpisodeSampler(pool,split=split,difficulty=difficulty,device=device,dtype=dtype,kin=self.kin,robot=self.robot)
        self.factory=factory
        self.map_ids=['<uninitialized>']*batch;self.proposal_seeds=[None]*batch
        self.episode_count=None;self.totals=None

    def _ids(self,indices):
        if indices is None:
            if self.core is None:return list(range(self.batch))
            return torch.where(self.core.terminated|self.core.truncated)[0].tolist()
        if isinstance(indices,torch.Tensor) and indices.dtype==torch.bool:
            if indices.shape!=(self.batch,):raise ValueError('reset mask shape')
            indices=torch.where(indices)[0].tolist()
        ids=list(indices)
        if len(set(ids))!=len(ids) or any(not isinstance(i,int) or not 0<=i<self.batch for i in ids):raise ValueError('unique environment ids required')
        return sorted(ids)

    def reset(self,indices=None):
        ids=self._ids(indices)
        if self.core is None and ids!=list(range(self.batch)):raise RuntimeError('initial reset requires the whole batch')
        if self.core is not None and any(not (self.core.terminated[i]|self.core.truncated[i]) for i in ids):raise RuntimeError('reset requires ended episodes')
        if not ids:return self.info()
        episodes=[self.factory(i,self.streams.for_env(i)) if self.factory is not None else self.sampler.sample(self.streams.for_env(i)) for i in ids]
        reference=episodes[0].base;device,dtype=reference.device,reference.dtype
        if self.core is not None and (device!=self.core.state.s.device or dtype!=self.core.state.s.dtype):raise ValueError('reset device/dtype mismatch')
        state=State(torch.cat([e.base for e in episodes]),torch.cat([e.q for e in episodes]),torch.zeros(len(ids),device=device,dtype=dtype))
        route=batch_routes([e.route for e in episodes],device=device,dtype=dtype)
        boxes,occupied=pad_maps([e.boxes for e in episodes],device=device,dtype=dtype)
        actual=validate_initial_state(state.base,state.q,self.kin,self.robot,TruthCollision(boxes,occupied,robot=self.robot))
        distance,_,angle=metrics(actual,route.at(state.s))
        if (distance>1e-4).any() or (angle>1e-4).any():raise ValueError('initial route must start at actual FK (N1 exact tolerances)')
        selected=torch.tensor(ids,device=device,dtype=torch.long)
        if self.core is None:
            self.core=Core(state,route,Grid.empty(self.batch,device=device,dtype=dtype),self.kin,self.robot,TruthCollision(boxes,occupied,robot=self.robot),synchronous=self.synchronous,renderer=Panorama(boxes,occupied,robot=self.robot),failure_mode=self.failure_mode,async_time_penalty=self.async_time_penalty,episode_end_bootstrap=self.episode_end_bootstrap,ik_avoid_collision=self.ik_avoid_collision)
            self.episode_count=torch.zeros(self.batch,device=device,dtype=torch.long)
            self.totals={key:torch.zeros_like(self.episode_count) for key in ('sensor_frames','origin_inside_self_frames','fully_occluded_frames')}
        else:
            c=self.core;mask=torch.zeros_like(c.done);mask[selected]=True
            width=max(c.collision.boxes.shape[1],boxes.shape[1])
            all_boxes=boxes.new_zeros(self.batch,width,8);all_mask=torch.zeros(self.batch,width,device=device,dtype=torch.bool)
            old=c.collision.boxes.shape[1];all_boxes[:,:old]=c.collision.boxes;all_mask[:,:old]=c.collision.mask
            all_boxes[selected]=0;all_mask[selected]=False
            all_boxes[selected,:boxes.shape[1]]=boxes;all_mask[selected,:boxes.shape[1]]=occupied
            c.reset(mask,state,route)
            c.collision.boxes=c.renderer.boxes=all_boxes;c.collision.mask=c.renderer.mask=all_mask
        c=self.core
        # Render only reset rows; no unselected grid, timestamp or counter write.
        depth=Panorama(c.renderer.boxes[selected],c.renderer.mask[selected],robot=self.robot)(c.state.base[selected],self.robot(c.state.base[selected],c.state.q[selected]))
        grid=Grid.empty(len(ids),device=device,dtype=dtype);grid.update(depth.points,depth.valid,c.state.s[selected])
        c.grid.observed[selected]=grid.observed;c.grid.height[selected]=grid.height;c.grid.timestamp[selected]=grid.timestamp
        c.record_render(depth,torch.ones(len(ids),device=device,dtype=torch.bool),indices=selected)
        for key in self.totals:self.totals[key][selected]+=getattr(c,key)[selected]
        self.episode_count[selected]+=1
        for i,e in zip(ids,episodes):self.map_ids[i]=e.map_id;self.proposal_seeds[i]=e.seed
        return self.info()

    def begin(self,candidate,mask=None):
        if self.core is None:raise RuntimeError('reset first')
        return self.core.begin(candidate,mask)

    def step(self,raw):
        if self.core is None:raise RuntimeError('reset first')
        c=self.core
        if raw.shape!=(self.batch,3) or raw.device!=c.state.s.device or raw.dtype!=c.state.s.dtype:raise ValueError('raw batch/device/dtype')
        if not torch.isfinite(raw).all() or (raw.abs()>1).any():raise ValueError('raw actions must be finite in [-1,1]')
        before={key:getattr(c,key).clone() for key in self.totals}
        transition=c.step(raw)
        for key in self.totals:self.totals[key]+=getattr(c,key)-before[key]
        return BatchStep(transition,self.info())

    def info(self):
        if self.core is None:return {}
        c=self.core
        result={key:getattr(c,key).clone() for key in ('terminated','truncated','strict_success','sensor_frames','origin_inside_self_frames','fully_occluded_frames')}
        result.update({'total_'+key:value.clone() for key,value in self.totals.items()})
        result['episode_count']=self.episode_count.clone();result['map_ids']=tuple(self.map_ids);result['proposal_seeds']=tuple(self.proposal_seeds)
        if self.sampler is not None:
            result['sampling']=dict(self.sampler.stats,rejections=self.sampler.stats['rejections'].copy())
        return result
