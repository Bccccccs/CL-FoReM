"""Batched L.0 segment execution kernel; no networks, candidate generation or training.
URDF robot geometry, observed-grid risk and in-place progress are assembled here.
"""
from dataclasses import dataclass
import torch
from task9_lr.diagnostics import hook
from .motion import actions,arc,advance,wrap,matrix_quat
from .kinematics import base_transform
from .geometry import segment_box_distance
from .perception import LocalCollision

@dataclass
class State:
    base:torch.Tensor
    q:torch.Tensor
    s:torch.Tensor
    def clone(self):return State(self.base.clone(),self.q.clone(),self.s.clone())

@dataclass
class Candidate:
    pose:torch.Tensor
    progress:torch.Tensor
    inplace:torch.Tensor

@dataclass
class Transition:
    observation:dict
    next_observation:dict
    raw_action:torch.Tensor
    reward:torch.Tensor
    B:torch.Tensor
    G:torch.Tensor
    dt:torch.Tensor
    attempted:torch.Tensor
    committed:torch.Tensor
    done:torch.Tensor
    reason:torch.Tensor
    mask:torch.Tensor
    active:torch.Tensor

class Core:
    """Finite batch, no autoreset. Caller supplies a new candidate only at boundary.
    q/base/s are committed atomically; failed IK q is never substituted for state.
    Capsules callback reads only base/q, never environment geometry.
    Sync in-place progress is computed internally using the common P5 search.
    """
    def __init__(self,state,route,grid,kin,capsules,collision,*,synchronous,future_offsets=None,allowed=None,renderer=None,execute=True,queue=None,visible_previous=None,retain_transitions=True,observation_chunk_size=32,reuse_route_raster=False,failure_mode='terminal',async_time_penalty=1.0,episode_end_bootstrap=False,ik_avoid_collision=True):
        # task7.18.4/SRC-0912: 'terminal' (default, L.0: first failure ends the segment) or
        # 'cbl_continue' (stage-L training only: failed sub-step is not committed, segment continues).
        if failure_mode not in ('terminal','cbl_continue'):raise ValueError('failure_mode must be terminal or cbl_continue')
        if failure_mode=='cbl_continue' and not execute:raise ValueError('cbl_continue requires execute=True (training mode)')
        # SRC-0913: weight of the asynchronous time term -dt in the reward (default 1.0 = original; 0 = CBL-style, no fixed time penalty). Synchronous reward ignores it.
        if not 0.<=float(async_time_penalty)<=1. :raise ValueError('async_time_penalty must be in [0,1]')
        self.async_time_penalty=float(async_time_penalty)
        # SRC-0915 C'': True -> only reaching the candidate / route end is terminal (mask 0); failure limit, stalls, D_max/T_max
        # episode ends are truncations (mask 1, bootstrap from the final observation of the same sub-goal). Default False = original mask.
        self.episode_end_bootstrap=bool(episode_end_bootstrap)
        # SRC-0915: IK branch choice avoids robot self-collision / ground (robot geometry only). Default on; False = previous nearest-branch rule.
        self.ik_avoid_collision=bool(ik_avoid_collision)
        self.failure_mode=failure_mode;self.failure_limit=5 if failure_mode=='terminal' else 20
        self.reuse_route_raster=reuse_route_raster
        self._route_raster_cache=None
        self.observation_chunk_size=observation_chunk_size
        self.retain_transitions=retain_transitions
        self.state=state.clone();self.route=route;self.grid=grid.snapshot();self.kin=kin
        self.capsules,self.collision,self.allowed=capsules,collision,allowed
        self.robot=capsules if hasattr(capsules,"self_collision") else None
        if self.robot is not None and hasattr(collision,"robot"):collision.robot=self.robot
        if self.robot is not None and renderer is not None and hasattr(renderer,"robot"):renderer.robot=self.robot
        self.synchronous=synchronous
        if future_offsets is None:future_offsets=torch.arange(1,16,device=state.s.device,dtype=state.s.dtype)*.1
        self.future_offsets=future_offsets.clone();self.renderer=renderer;self.execute=execute
        if future_offsets.ndim!=1 or (future_offsets<0).any():raise ValueError('explicit nonnegative future sample offsets required')
        B=len(state.s);dev=state.s.device;dt=state.s.dtype
        self.queue=torch.zeros(B,3,device=dev,dtype=dt) if queue is None else queue.clone()
        self.visible_previous=self.queue.clone() if visible_previous is None else visible_previous.clone()
        self.time=torch.zeros_like(state.s);self.attempt_time=torch.zeros_like(state.s);self.failures=torch.zeros(B,device=dev,dtype=torch.long);self.last_step_failure=torch.zeros(B,device=dev,dtype=torch.long)
        self.stalls=torch.zeros_like(self.failures);self.decisions=torch.zeros_like(self.failures);self.render_count=torch.zeros_like(self.failures)
        self.terminated=torch.zeros(B,device=dev,dtype=torch.bool);self.truncated=self.terminated.clone();self.strict_success=self.terminated.clone()
        self.done=torch.ones_like(self.terminated);self.finished=self.done.clone();self.transitions=[];self.trace=[]
        self.committed_total=torch.zeros_like(self.failures);self.attempted_total=torch.zeros_like(self.failures)
        self.sensor_frames=torch.zeros_like(self.failures)
        self.origin_inside_self_frames=torch.zeros_like(self.failures)
        self.fully_occluded_frames=torch.zeros_like(self.failures)
    def record_render(self,depth,rendered,indices=None):
        """G1 diagnostics only; rendered excludes inactive/uncommitted rows.
        Reset scans and action-end scans share the same counting definition.
        """
        inside=depth.origin_inside_self&rendered
        ids=slice(None) if indices is None else indices
        self.sensor_frames[ids]+=rendered.long()
        self.origin_inside_self_frames[ids]+=inside.long()
        self.fully_occluded_frames[ids]+=(inside&~depth.valid.flatten(1).any(-1)).long()
    def _mask(self,mask):
        if mask is None:return torch.ones_like(self.done)
        if mask.shape!=self.done.shape or mask.dtype!=torch.bool or mask.device!=self.done.device:raise ValueError('environment mask shape/device/type')
        return mask
    def _clear_history(self,mask):
        # Current-segment histories retain unselected rows, without mutating
        # transition/state objects already returned to the caller.
        from dataclasses import replace
        self.trace=[(x,m&~mask) for x,m in self.trace if (m&~mask).any()]
        self.attempts=[dict(a,active=a['active']&~mask,committed=a['committed']&~mask) for a in getattr(self,'attempts',[]) if (a['active']&~mask).any()]
        self.transitions=[replace(t,active=t.active&~mask) for t in self.transitions if (t.active&~mask).any()]
    def reset(self,mask,state,route):
        """E5: reset ended episode slices only; world geometry is caller-owned.
        State/route inputs contain only selected rows in increasing mask order.
        Initial scans are supplied by the batch environment after this method.
        """
        mask=self._mask(mask);ids=torch.where(mask)[0]
        if (mask&~(self.terminated|self.truncated)).any():raise RuntimeError('reset requires ended episodes')
        if len(ids)!=len(state.s) or len(ids)!=len(route.length):raise ValueError('reset selected batch shape')
        if not len(ids):return
        from .routes import replace_routes
        self.route=replace_routes(self.route,ids,route)
        for key in ('base','q','s'):getattr(self.state,key)[ids]=getattr(state,key)
        for name in ('time','attempt_time','failures','stalls','decisions','render_count','terminated','truncated','strict_success','committed_total','attempted_total','sensor_frames','origin_inside_self_frames','fully_occluded_frames'):
            getattr(self,name)[ids]=0
        self.queue[ids]=0;self.visible_previous[ids]=0
        self.grid.observed[ids]=False;self.grid.height[ids]=0;self.grid.timestamp[ids]=0
        self.done[ids]=True;self.finished[ids]=True
        if hasattr(self,'candidate'):
            self.candidate.pose[ids]=state.base;self.candidate.progress[ids]=state.s;self.candidate.inplace[ids]=False
            for key in ('base','q','s'):getattr(self.start,key)[ids]=getattr(state,key)
            for name in ('segment_substeps','attempted_segment','failure_kind','arrived','first_failure_time','max_position','max_cbl','max_angle','cap','timeout'):getattr(self,name)[ids]=0
            self.reason[ids]=-1;self.first[ids]=True
        self._clear_history(mask);self._cached_observation=None;self._route_raster_cache=None
    def begin(self,candidate,mask=None):
        mask=self._mask(mask)
        if not mask.any():return torch.zeros_like(mask)
        hook('begin_before',self,candidate,mask)
        if (mask&~self.done).any():raise RuntimeError('previous segment still active')
        if (mask&(self.terminated|self.truncated)).any():raise RuntimeError('episode ended; explicit reset/new Core required')
        if candidate.pose.shape!=self.state.base.shape or candidate.inplace.shape!=self.state.s.shape:raise ValueError('candidate shape')
        if self.synchronous:
            from .search import inplace_progress
            progress=self.route.length.clone();self.search_info=dict(targets=0,dls_fallbacks=0,accepted=0)
            ids=torch.where(candidate.inplace&mask)[0]
            if len(ids):progress[ids],self.search_info=inplace_progress(State(self.state.base[ids],self.state.q[ids],self.state.s[ids]),self.route.select(ids),self.kin,return_info=True)
            candidate=Candidate(candidate.pose,progress,candidate.inplace)
        if candidate.progress is None:raise ValueError('asynchronous candidate requires progress')
        if candidate.progress.shape!=self.state.s.shape:raise ValueError('candidate shape')
        if not torch.isfinite(candidate.pose[mask]).all() or not torch.isfinite(candidate.progress[mask]).all():raise ValueError('nonfinite candidate')
        if (candidate.progress[mask]>self.route.length[mask]).any():raise ValueError('progress beyond route')
        def put(name,value):
            previous=getattr(self,name,None)
            select=mask.reshape(-1,*([1]*(value.ndim-1)))
            setattr(self,name,value.clone() if previous is None else torch.where(select,value,previous))
        if not hasattr(self,'candidate'):
            self.candidate=Candidate(self.state.base.clone(),self.state.s.clone(),torch.zeros_like(mask));self.start=self.state.clone()
        for name in ('pose','progress','inplace'):getattr(self.candidate,name)[mask]=getattr(candidate,name)[mask]
        for name in ('base','q','s'):getattr(self.start,name)[mask]=getattr(self.state,name)[mask]
        for name in ('segment_substeps','attempted_segment','failure_kind'):put(name,torch.zeros_like(self.failures))
        put('reason',torch.full_like(self.failures,-1))
        for name in ('done','finished','arrived'):put(name,torch.zeros_like(mask))
        put('first',torch.ones_like(mask))
        for name in ('first_failure_time','max_position','max_cbl','max_angle'):put(name,torch.zeros_like(self.state.s))
        self._cached_observation=None;self._route_raster_cache=None;self._clear_history(mask);self.trace.append((self.state.clone(),mask.clone()))
        isprogress=(~torch.full_like(candidate.inplace,self.synchronous))|candidate.inplace
        cap=torch.where(isprogress,torch.maximum(self.state.s,candidate.progress),self.route.length)
        delta=candidate.pose-self.state.base
        ideal=delta[:,:2].norm(dim=-1)/.3+wrap(delta[:,2]).abs()
        ideal=torch.where(isprogress,torch.maximum(ideal,(cap-self.state.s)/.3),ideal)
        put('cap',cap);put('timeout',3*ideal+2)
        zero=mask&candidate.inplace&(candidate.progress<=self.state.s)
        self.done|=zero;self.reason[zero]=0;self.arrived[zero]=True
        if zero.any():self._finish(zero)
        hook('begin_after',self)
        return zero
    def _body_transform(self):
        # B_t denotes URDF base_link, above base_footprint by the URDF fixed offset.
        return base_transform(self.state.base)@self.kin.fixed("body_mount",self.state.q)
    def observe(self,previous=None):
        x=self.state;T=self.kin.world_tcp(x.base,x.q);B=self._body_transform();inv=torch.linalg.inv(B)
        current=inv@T;nextT=inv@self.route.at(torch.minimum(x.s+.01,self.route.length))
        future_s=(x.s[:,None]+self.future_offsets[None]).minimum(self.route.length[:,None])
        future=self.route.at(future_s);future=(inv[:,None]@future)[...,:3,3]
        # Future route rasterisation: exact XY segment-square intersections, not truth.
        local=self.grid.crop(x.base);N=len(x.s);dev=x.s.device;dtype=x.s.dtype
        axis=(torch.arange(128,device=dev,dtype=dtype)+.5-64)*.05
        yy,xx=torch.meshgrid(axis,axis,indexing='ij');cells=torch.stack([xx,yy,torch.zeros_like(xx)],-1).reshape(1,-1,3)
        cache=self._route_raster_cache if self.reuse_route_raster else None
        if cache is None:
            changed=torch.ones(N,device=dev,dtype=torch.bool)
            route_channel=torch.zeros(N,128*128,device=dev,dtype=torch.bool)
        else:
            changed=(x.base!=cache['base']).any(-1)|(x.s!=cache['s'])
            route_channel=cache['raster'].clone();route_channel[changed]=False
        points=torch.cat([self.route.at(x.s)[:,None,:3,3],self.route.xyz],1)
        homogeneous=torch.cat([points,torch.ones_like(points[...,:1])],-1)
        rel=(inv[:,None]@homogeneous[...,None]).squeeze(-1)[...,:3];rel[...,2]=0
        half=torch.tensor([.025,.025,0],device=dev,dtype=dtype)
        # Batch route nodes; reject disjoint XY bounds before exact distance.
        a=rel[:,:-1].clone();b=rel[:,1:];valid=self.route.s>x.s[:,None]
        crossing=(self.route.s[:,:-1]<x.s[:,None])&(self.route.s[:,1:]>=x.s[:,None])
        a[:,1:]=torch.where(crossing[...,None],rel[:,0,None],a[:,1:])
        for lo in range(0,N,self.observation_chunk_size):
            hi=min(N,lo+self.observation_chunk_size)
            if self.reuse_route_raster:
                ids=lo+torch.where(changed[lo:hi])[0]
                if not len(ids):continue
                aa=a[ids,:,None]-cells[:,None];bb=b[ids,:,None]-cells[:,None]
                valid_rows=valid[ids,:,None]
            else:
                aa=a[lo:hi,:,None]-cells[:,None];bb=b[lo:hi,:,None]-cells[:,None]
                valid_rows=valid[lo:hi,:,None]
            potential=(torch.minimum(aa,bb)<=half).all(-1)&(torch.maximum(aa,bb)>=-half).all(-1)&valid_rows
            env,node,cell=torch.where(potential)
            dist=segment_box_distance(aa[env,node,cell],bb[env,node,cell],half)
            hit=dist==0
            rows=ids[env[hit]] if self.reuse_route_raster else lo+env[hit]
            route_channel[rows,cell[hit]]=True
        if self.reuse_route_raster:
            self._route_raster_cache=dict(base=x.base.clone(),s=x.s.clone(),raster=route_channel.clone())
        local=torch.cat([local,route_channel.reshape(N,128,128,1).to(dtype)],-1)
        delta=self.candidate.pose-x.base;c,s=x.base[:,2].cos(),x.base[:,2].sin()
        relxy=torch.stack([c*delta[:,0]+s*delta[:,1],-s*delta[:,0]+c*delta[:,1]],-1);angle=wrap(delta[:,2])
        sub=torch.cat([relxy,angle.sin()[:,None],angle.cos()[:,None],self.candidate.inplace[:,None].to(dtype)],-1)
        if not self.synchronous:sub=torch.cat([sub,(self.candidate.progress-x.s)[:,None]],-1)
        lim=torch.as_tensor([2*torch.pi,2*torch.pi,torch.pi,2*torch.pi,2*torch.pi,2*torch.pi],device=dev,dtype=dtype)
        pose=lambda t:torch.cat([t[...,:3,3],matrix_quat(t[...,:3,:3])],-1)
        return dict(grid=local,q=x.q/lim,tcp=pose(current),next_tcp=pose(nextT),route_points=future,subgoal=sub,synchronous=torch.full((N,1),float(self.synchronous),device=dev,dtype=dtype),previous_action=(self.queue if previous is None else previous).clone(),scan_timestamp=self.grid.timestamp.clone())
    def current_observation(self):
        """Reuse spatial computation; preserve independent returned tensor ownership.
        The after observation remains unchanged when the queue is advanced.
        """
        previous=torch.where(self.first[:,None],self.visible_previous,self.queue)
        if self._cached_observation is None:self._cached_observation=self.observe(previous)
        observation={k:v.clone() for k,v in self._cached_observation.items()}
        observation["previous_action"]=previous.clone()
        return observation
    def _finish(self,ended):
        ended=ended&~self.finished
        if not ended.any():return
        self.finished|=ended
        if not self.execute:return
        self.decisions+=ended.long()
        if self.failure_mode=='terminal':self.failures+=((self.failure_kind>0)&ended).long()  # cbl_continue counts failed action steps in step()
        ds=self.state.s-self.start.s;move=(self.state.base[:,:2]-self.start.base[:,:2]).norm(dim=-1)
        stuck=(ds<.01)&(move<.05)
        self.stalls=torch.where(ended,torch.where(stuck,self.stalls+1,0),self.stalls)
        from .kinematics import metrics
        target=self.route.at(self.route.length);d,r,_=metrics(self.kin.world_tcp(self.state.base,self.state.q),target)
        success=(self.state.s==self.route.length)&(d<=.025)&(r<=.05)
        term=ended&((self.failures>=self.failure_limit)|success|(self.stalls>=5))
        clock=self.time if self.failure_mode=='terminal' else self.attempt_time
        trunc=ended&~term&((self.decisions>=150)|(clock>=200))
        self.terminated|=term;self.truncated|=trunc;self.strict_success|=ended&success&(self.failures==0)
        hook('finish',self,locals())
    def step(self,raw):
        if self.done.all():raise RuntimeError('no active segment')
        active=~self.done;before=self.current_observation();self.first&=~active
        u,w,v=actions(raw,self.synchronous,self.candidate.inplace)
        hook('step_start',self,before,raw,u,w,v)
        qprev=self.queue.clone();start=self.state.clone();rho0=(start.base[:,:2]-self.candidate.pose[:,:2]).norm(dim=-1)
        attempted=torch.zeros_like(self.failures);committed=attempted.clone()
        dlast=torch.zeros_like(u);rlast=dlast.clone()
        cbl=self.failure_mode=='cbl_continue'
        stopped=torch.zeros_like(self.done);step_kind=torch.zeros_like(self.failures);fail_d=dlast.clone();fail_r=dlast.clone()
        for _ in range(2):
            pending=~self.done
            if cbl:pending=pending&~stopped
            if not pending.any():break
            trialbase=arc(self.state.base,v,w,.05);trials=advance(self.state.s,u,self.cap)
            target_tcp=self.route.at(trials)
            ik=self.kin.solve_world(trialbase,target_tcp,self.state.q,**({'robot':self.robot} if self.ik_avoid_collision and self.robot is not None else {}))
            cap=self.capsules(trialbase,ik.q)
            coll=self.collision(trialbase,cap,self.allowed,q=ik.q) if self.robot is not None else self.collision(trialbase,cap,self.allowed)
            attempted+=pending.long();self.attempted_segment+=pending.long()
            failed=pending&(~ik.accepted|coll.any)
            kind=torch.where(~ik.accepted,1,torch.where(coll.base,2,torch.where(coll.arm,3,torch.where(coll.self_collision,4,0))))
            self.failure_kind=torch.where(failed,kind,self.failure_kind)
            self.first_failure_time=torch.where(failed,(self.segment_substeps.to(u.dtype)+1)*.05,self.first_failure_time)
            if cbl:
                # Failed sub-step is not committed; no further attempt in this action step; segment continues.
                stopped|=failed;step_kind=torch.where(failed,kind,step_kind)
                ikfail=failed&(kind==1);fail_d=torch.where(ikfail,ik.position,fail_d);fail_r=torch.where(ikfail,ik.cbl,fail_r)
            else:
                self.reason=torch.where(failed,torch.where(~ik.accepted,2,3),self.reason);self.done|=failed
            commit=pending&~failed
            hook('substep',self,locals())
            joint_delta=ik.q-self.state.q
            from .kinematics import fk
            manipulability=torch.linalg.det(fk(ik.q,True)[1]).abs()
            self.attempts.append(dict(manipulability=manipulability.clone(),active=pending.clone(),committed=commit.clone(),previous_q=self.state.q.clone(),candidate_q=ik.q.clone(),joint_delta=joint_delta.clone(),over_velocity_diagnostic=(joint_delta.abs()>torch.pi*.05).any(-1),branch=ik.branch.clone(),ik_status=ik.status.clone(),position_m=ik.position.clone(),cbl=ik.cbl.clone(),angle_rad=ik.angle.clone(),base_collision=coll.base.clone(),arm_collision=coll.arm.clone(),self_collision=coll.self_collision.clone()))
            self.state.base=torch.where(commit[:,None],trialbase,self.state.base)
            self.state.q=torch.where(commit[:,None],ik.q,self.state.q);self.state.s=torch.where(commit,trials,self.state.s)
            committed+=commit.long();self.segment_substeps+=commit.long();self.time+=commit.to(u.dtype)*.05
            dlast=torch.where(commit,ik.position,dlast);rlast=torch.where(commit,ik.cbl,rlast)
            self.max_position=torch.maximum(self.max_position,torch.where(commit,ik.position,0))
            self.max_cbl=torch.maximum(self.max_cbl,torch.where(commit,ik.cbl,0));self.max_angle=torch.maximum(self.max_angle,torch.where(commit,ik.angle,0))
            if commit.any():self.trace.append((self.state.clone(),commit.clone()))
            delta=self.candidate.pose-self.state.base
            reached=(delta[:,:2].norm(dim=-1)<=.1)&(wrap(delta[:,2]).abs()<=.35)
            progress_required=self.candidate.inplace|(~torch.full_like(commit,self.synchronous))
            reached&=~progress_required|(self.state.s==self.cap)
            self.arrived|=commit&reached
            route_end=commit&(self.state.s==self.route.length)
            if cbl:timeout=(commit|failed)&(self.attempted_segment.to(u.dtype)*.05>=self.timeout)  # attempted time, failed sub-steps count .05 s
            else:timeout=commit&(self.segment_substeps.to(u.dtype)*.05>=self.timeout)
            reason=torch.where(route_end,1,torch.where(reached,0,4))
            ended=commit&(route_end|reached|timeout) if not cbl else (commit&(route_end|reached))|timeout
            self.reason=torch.where(ended,reason,self.reason);self.done|=ended
        self.attempted_total+=attempted;self.committed_total+=committed
        if cbl:
            self.attempt_time+=attempted.to(u.dtype)*.05;self.failures+=stopped.long()
            fail_term=stopped&~self.done&(self.failures>=self.failure_limit)
            self.reason=torch.where(fail_term,torch.where(step_kind==1,2,3),self.reason);self.done|=fail_term
            self.last_step_failure=step_kind
        has_commit=committed>0
        if self.execute and has_commit.any():
            if self.renderer is None:raise RuntimeError('execution requires explicit renderer; no silent no-render mode')
            depth=self.renderer(self.state.base,self.capsules(self.state.base,self.state.q))
            self.record_render(depth,has_commit)
            self.sensor_origin_inside_self=depth.origin_inside_self.clone()
            valid=depth.valid&has_commit[:,None,None]
            stamp=torch.where(has_commit,self.time,self.grid.timestamp)
            self.grid.update(depth.points,valid,stamp);self.render_count+=has_commit.long()
        dt=committed.to(u.dtype)*.05
        dlast=torch.where(has_commit,dlast,0);rlast=torch.where(has_commit,rlast,0)
        if cbl:  # CBL: IK-failure step uses the failed attempt's actual residual
            ikfail=step_kind==1;dlast=torch.where(ikfail,fail_d,dlast);rlast=torch.where(ikfail,fail_r,rlast)
        B=-10*((step_kind if cbl else self.failure_kind)==2).to(u.dtype)-.5*((dlast/.1).square()+(rlast/.05).square())-.05*(raw[:,1:]-qprev[:,1:]).square().sum(-1)
        rho=(self.state.base[:,:2]-self.candidate.pose[:,:2]).norm(dim=-1)
        G=rho0-rho+(self.arrived&active).to(u.dtype)-2*((stopped if cbl else (self.failure_kind>0))&active).to(u.dtype)
        if not self.synchronous:G+=self.state.s-start.s
        reward=(u/.3)*B-.1*((.3-u)/.3).square()+G if self.synchronous else B+G-dt*self.async_time_penalty
        self._finish(self.done)
        after=self.observe() # queue update must be after this observation
        self._cached_observation={k:v.clone() for k,v in after.items()}
        if self.episode_end_bootstrap:mask=torch.where((self.reason==0)|(self.reason==1),0.,1.).to(u.dtype)
        else:mask=torch.where(self.terminated|((self.reason>=0)&(self.reason!=4)),0.,1.).to(u.dtype)
        tr=Transition(before,after,raw.clone(),torch.where(active,reward,0),torch.where(active,B,0),torch.where(active,G,0),dt,attempted,committed,self.done.clone(),self.reason.clone(),mask,active)
        if self.retain_transitions:self.transitions.append(tr)
        self.visible_previous=after['previous_action'].clone()
        self.queue=torch.where(has_commit[:,None],raw,self.queue)
        hook('step_end',self,tr)
        return tr

def feature_vector(core,risk=None,*,risk_chunk_size=32):
    """D20 v1 encoder. risk=[minimum gap, unknown fraction, nearest unknown].
    Default P6 metrics use the initial and committed states only.
    An explicit callback remains available for isolated arithmetic fixtures.
    """
    if not core.done.all():raise ValueError('features require completed segments')
    if risk is None:
        from .risk import sweep_metrics
        risk=sweep_metrics(core.trace,core.grid,core.capsules,chunk_size=risk_chunk_size)
    if risk.shape!=(len(core.state.s),3) or not torch.isfinite(risk).all():raise ValueError('explicit finite swept-region metrics required')
    if (risk[:,0]<0).any() or (risk[:,0]>3.2).any() or (risk[:,1]<0).any() or (risk[:,1]>1).any() or (risk[:,2]<0).any() or (risk[:,2]>3.2).any():raise ValueError('risk units/range')
    dtype=core.state.s.dtype;delta=core.state.base-core.candidate.pose
    c,s=core.candidate.pose[:,2].cos(),core.candidate.pose[:,2].sin()
    rel=torch.stack([c*delta[:,0]+s*delta[:,1],-s*delta[:,0]+c*delta[:,1],wrap(delta[:,2])],-1)
    end=torch.nn.functional.one_hot(core.reason,5).to(dtype)
    failure=core.failure_kind>0
    ratio=torch.where(failure,core.first_failure_time/core.timeout,1)
    scalar=lambda x:x[:,None]
    return torch.cat([scalar(core.arrived.to(dtype)),end,scalar(ratio),scalar(core.segment_substeps.to(dtype)*.05),scalar(core.timeout),rel,scalar(core.state.s-core.start.s),scalar(core.max_position),scalar(core.max_cbl),scalar(core.max_angle),risk],-1)

def rollout(state,route,grid,poses,progress,inplace,policy,kin,capsules,*,synchronous,future_offsets=None,feature_metrics=None,allowed=None,queue=None,visible_previous=None,risk_chunk_size=32,observation_chunk_size=32,reuse_route_raster=False):
    """Full GPU E x K rollout, preserving SIM and NN batch shape/slot order.

    Only scratch-history retention and independent geometry work chunks vary.
    SIM row compaction was rejected by same-input checks (SRC-0515).
    """
    E,K=poses.shape[:2];indices=torch.arange(E,device=poses.device).repeat_interleave(K)
    snapshot=grid.select(indices)
    select=lambda x:None if x is None else x[indices]
    c=Core(State(state.base[indices],state.q[indices],state.s[indices]),route.select(indices),snapshot,kin,capsules,LocalCollision(snapshot,robot=capsules if hasattr(capsules,"self_collision") else None),synchronous=synchronous,future_offsets=future_offsets,execute=False,allowed=allowed,queue=select(queue),visible_previous=select(visible_previous),retain_transitions=feature_metrics is not None,observation_chunk_size=observation_chunk_size,reuse_route_raster=reuse_route_raster)
    c.begin(Candidate(poses.reshape(-1,3),None if progress is None else progress.reshape(-1),inplace.reshape(-1)))
    while not c.done.all():
        obs=c.current_observation()
        with torch.no_grad():raw=policy(obs)
        c.step(raw)
    return feature_vector(c,None if feature_metrics is None else feature_metrics(c),risk_chunk_size=risk_chunk_size).reshape(E,K,19)
