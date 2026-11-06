"""G7-1..5 rule paths (SRC-0434/0435); units m, rad, s.

Evaluation accepts only proprioception, route and sensor Grid. It never receives
an environment, renderer or truth collision object. The same trial() is used by
prediction and execution; only the collision oracle differs.
"""
from dataclasses import dataclass
from types import SimpleNamespace
import math
import time
import torch
from .core import State, Candidate, Core, feature_vector
from .motion import arc, advance, wrap
from .perception import LocalCollision
from .risk import sweep_metrics

DT = .05


@dataclass
class Paths:
    controls: torch.Tensor  # [E,N,C,3], physical [u,omega,v]
    steps: torch.Tensor
    mask: torch.Tensor
    cap: torch.Tensor
    progress: torch.Tensor  # absolute s curve at the same substeps
    duration: torch.Tensor  # full planned duration, including very large arcs


@dataclass
class Evaluation:
    paths: Paths
    feasible: torch.Tensor
    best: torch.Tensor
    features: torch.Tensor
    path_features: torch.Tensor
    first_bad: torch.Tensor  # normalized first failure position; no failure = 1.0
    failure_kind: torch.Tensor
    traces: list
    info: dict


@dataclass
class Execution:
    reason: torch.Tensor
    failure_kind: torch.Tensor
    arrived: torch.Tensor
    elapsed: torch.Tensor
    timeout: torch.Tensor
    attempted: torch.Tensor
    trace: list
    replans: list
    info: dict


def _setup(state, route, candidate, kin, robot, grid, synchronous):
    # Reuse D7 and D15, including the fixed start-of-decision in-place cap.
    core=Core(state,route,grid,kin,robot,LocalCollision(grid,robot=robot if hasattr(robot,'self_collision') else None),synchronous=synchronous,execute=False)
    core.begin(candidate)
    return core


@torch.no_grad()
def generate_paths(state, candidate, route, *, synchronous, cap=None, max_substeps=None):
    """Generate fixed P1-a,P1-b,... order (sync: P1,...,P7).

    Segment durations ceil to a substep, with speed reduced to land exactly.
    Host work constructs only the small primitive lists; IK/collision is batched.
    Sync in-place callers must supply the decision-start search cap.
    """
    B=len(state.s);N=7 if synchronous else 14
    if cap is None:
        if synchronous and candidate.inplace.any():raise ValueError('sync in-place requires fixed search cap')
        cap=route.length if synchronous else candidate.progress
    specs=[];valid=[];planned=[]
    starts=state.base.detach().cpu().double().tolist()
    goals=candidate.pose.detach().cpu().double().tolist()
    ds=(cap-state.s).clamp_min(0).detach().cpu().double().tolist()
    inplace=candidate.inplace.tolist()
    def ticks(t):return int(math.ceil(t/DT))
    for i,(start,goal) in enumerate(zip(starts,goals)):
        def turn(a):
            a=math.atan2(math.sin(a),math.cos(a));n=ticks(abs(a))
            return [] if n==0 else [(n,a/(n*DT),0.)]
        def leg(p,q,yaw,back=False):
            dx,dy=q[0]-p[0],q[1]-p[1];distance=math.hypot(dx,dy)
            if distance==0:return [],yaw
            angle=math.atan2(dy,dx)+(math.pi if back else 0)
            n=ticks(distance/.3)
            return turn(angle-yaw)+[(n,0.,(-distance if back else distance)/(n*DT))],angle
        families=[]
        for back in (False,True):
            seg,yaw=leg(start,goal,start[2],back);families.append((seg+turn(goal[2]-yaw),True))
        dx,dy=goal[0]-start[0],goal[1]-start[1]
        x=math.cos(start[2])*dx+math.sin(start[2])*dy
        y=-math.sin(start[2])*dx+math.cos(start[2])*dy
        if y!=0 and math.isfinite((x*x+y*y)/(2*y)):
            radius=(x*x+y*y)/(2*y);angle=2*math.atan2(y,x)
            n=ticks(max(abs(radius*angle)/.3,abs(angle)))
            families.append(([(n,angle/(n*DT),radius*angle/(n*DT))]+turn(goal[2]-start[2]-angle),True))
        else:families.append(([],False))
        distance=math.hypot(dx,dy)
        for offset in (-.5,-.25,.25,.5):
            if distance:
                mid=[(start[0]+goal[0])/2-offset*dy/distance,(start[1]+goal[1])/2+offset*dx/distance]
                a,yaw=leg(start,mid,start[2]);b,yaw=leg(mid,goal,yaw)
                families.append((a+b+turn(goal[2]-yaw),True))
            else:families.append(([],False))
        for p,(segments,ok) in enumerate(families):
            for mode in range(1 if synchronous else 2):
                if inplace[i]:
                    ok=p==0 and mode==0;segments=[]
                controls=[];total=0
                def append(n, value):
                    nonlocal total
                    keep=n if max_substeps is None else max(0,min(n,max_substeps-total))
                    controls.extend([value]*keep);total+=n
                base_steps=sum(n for n,_,_ in segments)
                if synchronous:u=.1
                elif mode==0 and base_steps:u=min(.3,ds[i]/(base_steps*DT))
                else:u=0.
                for n,w,v in segments:append(n,(u,w,v))
                if inplace[i] or (not synchronous and (mode==1 or ds[i]>.3*base_steps*DT)):
                    speed=.1 if inplace[i] or mode==1 else .3
                    remaining=ds[i] if inplace[i] or mode==1 else ds[i]-.3*base_steps*DT
                    append(ticks(max(0.,remaining)/speed),(speed,0.,0.))
                specs.append(controls if ok else []);valid.append(ok);planned.append(total if ok else 0)
    length=max(1,max(map(len,specs)));controls=state.s.new_zeros(B*N,length,3)
    # Counts beyond int64 cannot finish before any finite practical T_seg.
    # Retain the full duration separately: saturation is storage, not a path mask.
    steps=torch.tensor([min(n,torch.iinfo(torch.int64).max) for n in planned],device=state.s.device,dtype=torch.long)
    duration=torch.tensor([n*DT for n in planned],device=state.s.device,dtype=torch.float64).reshape(B,N)
    for i,row in enumerate(specs):
        if row:controls[i,:len(row)]=torch.tensor(row,device=controls.device,dtype=controls.dtype)
    controls=controls.reshape(B,N,length,3);steps=steps.reshape(B,N)
    mask=torch.tensor(valid,device=controls.device,dtype=torch.bool).reshape(B,N)
    progress=torch.minimum(state.s[:,None,None]+controls[...,0].cumsum(-1)*DT,cap[:,None,None])
    if synchronous:
        progress=torch.minimum(state.s[:,None,None]+.1*(torch.arange(1,length+1,device=controls.device,dtype=controls.dtype)*DT)[None,None],cap[:,None,None]).expand(B,N,length).clone()
    # B.9 represents a prescribed s curve, including its exact capped endpoint.
    # Evaluate it from the plan origin, avoiding repeated-addition drift.
    ending=(torch.arange(length,device=controls.device)[None,None,:]+1>=steps[...,None])&mask[...,None]
    required=candidate.inplace if synchronous else torch.ones_like(candidate.inplace)
    progress=torch.where(ending&required[:,None,None],cap[:,None,None],progress)
    return Paths(controls,steps,mask,cap.clone(),progress,duration)


def rank_paths(feasible,first_bad,gap,duration,residual,mask,*,pure_timeout=None):
    """SRC-0904: feasible > pure timeout > later failure, then U25/order."""
    if (~mask.any(-1)).any():raise ValueError('candidate has no generated paths')
    order=torch.arange(mask.shape[1],device=mask.device).expand_as(mask)
    # Stable least-to-most-significant sorting retains the fixed path order.
    if pure_timeout is None:pure_timeout=torch.zeros_like(feasible)
    category=2*feasible.long()+((~feasible)&pure_timeout).long()
    keys=[residual,duration,-(gap>=.10).to(duration.dtype),
          torch.where(category==0,-first_bad,torch.zeros_like(first_bad)),
          -category,-mask.long()]
    for key in keys:
        order=order.gather(1,torch.argsort(key.gather(1,order),dim=1,stable=True))
    return order[:,0]


def trial(state, route, controls, cap, kin, robot, collision, allowed=None, target_s=None):
    """One common attempted substep; no mutation or commit here."""
    u,w,v=controls.unbind(-1)
    base=arc(state.base,v,w,DT);s=advance(state.s,u,cap) if target_s is None else target_s
    ik=kin.solve_world(base,route.at(s),state.q,**({'robot':robot} if hasattr(robot,'self_collision') else {}))
    coll=collision(base,robot(base,ik.q),allowed)
    # Contract ⑨ priority: IK > self > arm > base.
    kind=torch.where(~ik.accepted,1,torch.where(coll.self_collision,4,torch.where(coll.arm,3,torch.where(coll.base,2,0))))
    return State(base,ik.q,s),ik,kind


def _commit(state,new,mask):
    return State(*(torch.where(mask.reshape(-1,*([1]*(getattr(state,k).ndim-1))),getattr(new,k),getattr(state,k)) for k in ('base','q','s')))


def _route_end(state,route,ik):
    return (state.s==route.length)&(ik.position<=.025)&(ik.cbl<=.05)


@torch.no_grad()
def evaluate(state,route,grid,candidate,kin,robot,*,synchronous,cap=None,timeout=None,allowed=None,sync_origin=None,sync_elapsed=None):
    """Evaluate E candidates x N paths without changing input state or RNG.

    For K candidates flatten E*K before calling, duplicating sensor inputs only.
    Features use committed prefixes, including the start state for clearance.
    """
    setup=_setup(state,route,candidate,kin,robot,grid,synchronous) if cap is None or timeout is None else None
    cap=setup.cap if cap is None else cap;timeout=setup.timeout if timeout is None else timeout
    paths=generate_paths(state,candidate,route,synchronous=synchronous,cap=cap,max_substeps=max(1,int(torch.ceil(timeout.max()/DT))))
    if synchronous and sync_origin is not None:
        t=(sync_elapsed[:,None,None]+torch.arange(1,paths.controls.shape[2]+1,device=state.s.device)[None,None,:])*DT
        paths.progress=torch.minimum(sync_origin[:,None,None]+.1*t,cap[:,None,None]).expand_as(paths.progress).clone()
    B,N=paths.mask.shape;ids=torch.arange(B,device=state.s.device).repeat_interleave(N)
    ss=State(state.base[ids].clone(),state.q[ids].clone(),state.s[ids].clone());start=ss.clone()
    rr=route.select(ids);gg=grid.select(ids)
    valid=paths.mask.flatten();length=paths.steps.flatten();limit=timeout[ids];caps=cap[ids]
    done=~valid|(length==0);reason=torch.where(done,0,-1).long();count=torch.zeros_like(length)
    failure=torch.zeros_like(length);first_time=torch.zeros_like(ss.s)
    maxpos=torch.zeros_like(ss.s);maxcbl=maxpos.clone();maxang=maxpos.clone()
    trace=[(ss.clone(),valid.clone())];live_ids=None
    for j in range(paths.controls.shape[2]):
        pending=~done
        if not pending.any():break
        selected=torch.where(pending)[0]
        if live_ids is None or not torch.equal(selected,live_ids):
            live_ids=selected
            live_route=route.select(ids[selected])
            live_collision=LocalCollision(grid.select(ids[selected]),robot=robot if hasattr(robot,'self_collision') else None)
        live=State(ss.base[selected],ss.q[selected],ss.s[selected])
        proposed,result,kinds=trial(live,live_route,paths.controls[:,:,j].reshape(-1,3)[selected],caps[selected],kin,robot,live_collision,allowed,target_s=paths.progress[:,:,j].reshape(-1)[selected])
        new=ss.clone()
        for name in ('base','q','s'):getattr(new,name)[selected]=getattr(proposed,name)
        kind=torch.zeros_like(length);kind[selected]=kinds
        ik=SimpleNamespace()
        for name in ('position','cbl','angle'):
            value=torch.zeros_like(ss.s);value[selected]=getattr(result,name);setattr(ik,name,value)
        failed=pending&(kind>0);commit=pending&~failed
        failure=torch.where(failed,kind,failure)
        first_time=torch.where(failed,(j+1)*DT,first_time)
        reason=torch.where(failed,torch.where(kind==1,2,3),reason)
        ss=_commit(ss,new,commit);count+=commit.long()
        maxpos=torch.maximum(maxpos,torch.where(commit,ik.position,0));maxcbl=torch.maximum(maxcbl,torch.where(commit,ik.cbl,0));maxang=torch.maximum(maxang,torch.where(commit,ik.angle,0))
        trace.append((ss.clone(),commit.clone()))
        endroute=commit&_route_end(ss,rr,ik);arrive=commit&(count>=length)
        expired=commit&(count.to(ss.s.dtype)*DT>=limit)&~(endroute|arrive)
        reason=torch.where(endroute,1,torch.where(arrive,0,torch.where(expired,4,reason)))
        done|=failed|endroute|arrive|expired
    risk=sweep_metrics(trace,gg,robot)
    arrived=(reason==0)|(reason==1)
    summary=SimpleNamespace(done=done,state=ss,start=start,candidate=Candidate(candidate.pose[ids],cap[ids],candidate.inplace[ids]),reason=reason,arrived=arrived,failure_kind=failure,first_failure_time=first_time,timeout=limit,segment_substeps=count,max_position=maxpos,max_cbl=maxcbl,max_angle=maxang)
    features=feature_vector(summary,risk).reshape(B,N,19)
    feasible=arrived.reshape(B,N)&paths.mask
    # No physical failure (including pure timeout) has normalized position 1.0.
    first_position=torch.where(failure>0,first_time/limit.clamp_min(DT),torch.ones_like(first_time)).reshape(B,N)
    pure_timeout=(reason.reshape(B,N)==4)&(failure.reshape(B,N)==0)
    # Path ranking uses full planned duration, prefix residual/gap per U25/⑨.
    best=rank_paths(feasible,first_position,risk[:,0].reshape(B,N),paths.duration,maxpos.reshape(B,N),paths.mask,pure_timeout=pure_timeout)
    rows=torch.arange(B,device=best.device)
    return Evaluation(paths,feasible,best,features[rows,best],features,first_position,failure.reshape(B,N),trace,dict(feasible_count=feasible.sum(-1),timeout=timeout.clone(),cap=cap.clone()))


@torch.no_grad()
def execute(env,candidate,*,allowed=None,mask=None):
    """Execute a full G7 decision, replanning every ten committed substeps.

    Accepts Core or EpisodeEnv. Anchored candidate, cap and T_seg stay fixed.
    Rendering occurs after two substeps (or at decision end), including odd
    primitive boundaries; no local prediction is used as an execution veto.
    """
    c=env.core if hasattr(env,'core') else env
    before_totals={k:getattr(c,k).clone() for k in getattr(env,'totals',{})}
    c.begin(candidate,mask=mask);anchor=Candidate(c.candidate.pose.clone(),c.candidate.progress.clone(),c.candidate.inplace.clone())
    B=len(c.state.s);rows=torch.arange(B,device=c.state.s.device)
    trace=[(c.state.clone(),(~c.done).clone())];replans=[];attempted=torch.zeros_like(c.failures)
    chosen=None;offset=0;committed_action=torch.zeros_like(c.done);action_attempted=torch.zeros_like(c.done);last_raw=c.queue.clone()
    while not c.done.all():
        if chosen is None or offset==10:
            if c.state.s.is_cuda:torch.cuda.synchronize(c.state.s.device)
            plan_started=time.perf_counter()
            live=torch.where(~c.done)[0]
            state=State(c.state.base[live],c.state.q[live],c.state.s[live])
            goal=Candidate(anchor.pose[live],anchor.progress[live],anchor.inplace[live])
            ev=evaluate(state,c.route.select(live),c.grid.select(live),goal,c.kin,c.capsules,synchronous=c.synchronous,cap=c.cap[live],timeout=(c.timeout[live]-c.segment_substeps[live]*DT).clamp_min(0),allowed=allowed,sync_origin=c.start.s[live],sync_elapsed=c.segment_substeps[live])
            selected=ev.best;local_rows=torch.arange(len(live),device=live.device)
            chosen=c.state.s.new_zeros(B,ev.paths.controls.shape[2],3)
            chosen_progress=c.state.s[:,None].expand(B,ev.paths.controls.shape[2]).clone()
            length=torch.zeros_like(c.segment_substeps)
            chosen[live]=ev.paths.controls[local_rows,selected]
            chosen_progress[live]=ev.paths.progress[local_rows,selected]
            length[live]=ev.paths.steps[local_rows,selected]
            if c.state.s.is_cuda:torch.cuda.synchronize(c.state.s.device)
            plan_wall=time.perf_counter()-plan_started
            replans.append(dict(indices=live.clone(),wall_seconds=plan_wall,candidate=anchor.pose.clone(),start=c.state.clone(),evaluation=ev,active=(~c.done).clone()))
            offset=0
            zero=(~c.done)&(length==0);c.arrived|=zero;c.reason=torch.where(zero,0,c.reason);c.done|=zero
            if c.done.all():break
        pending=~c.done;action_attempted|=pending;controls=chosen[:,offset]
        previous_q=c.state.q.clone()
        new,ik,kind=trial(c.state,c.route,controls,c.cap,c.kin,c.capsules,c.collision,allowed,target_s=chosen_progress[:,offset])
        attempted+=pending.long();c.attempted_segment+=pending.long();c.attempted_total+=pending.long()
        failed=pending&(kind>0);commit=pending&~failed
        c.failure_kind=torch.where(failed,kind,c.failure_kind)
        c.first_failure_time=torch.where(failed,(c.segment_substeps+1)*DT,c.first_failure_time)
        c.reason=torch.where(failed,torch.where(kind==1,2,3),c.reason)
        from .kinematics import fk
        jump=(ik.q-previous_q).abs()>torch.pi*DT
        c.attempts.append(dict(active=pending.clone(),committed=commit.clone(),previous_q=previous_q,candidate_q=ik.q.clone(),joint_delta=ik.q-previous_q,over_velocity_diagnostic=jump.any(-1),manipulability=torch.linalg.det(fk(ik.q,True)[1]).abs(),branch=ik.branch.clone(),ik_status=ik.status.clone(),position_m=ik.position.clone(),cbl=ik.cbl.clone(),angle_rad=ik.angle.clone()))
        c.state=_commit(c.state,new,commit);c.segment_substeps+=commit.long();c.committed_total+=commit.long();c.time+=commit.to(c.time.dtype)*DT
        for name,value in [('max_position',ik.position),('max_cbl',ik.cbl),('max_angle',ik.angle)]:setattr(c,name,torch.maximum(getattr(c,name),torch.where(commit,value,0)))
        if commit.any():
            trace.append((c.state.clone(),commit.clone()));c.trace.append((c.state.clone(),commit.clone()))
        route_end=commit&_route_end(c.state,c.route,ik)
        reached=commit&(offset+1>=length)
        expired=commit&(c.segment_substeps*DT>=c.timeout)
        c.arrived|=reached|route_end
        c.reason=torch.where(route_end,1,torch.where(reached,0,torch.where(expired,4,c.reason)))
        c.done|=failed|route_end|reached|expired
        committed_action|=commit
        # Store the physical primitive's normalized action for the next segment.
        u,w,v=controls.unbind(-1);raw=torch.stack([2*(u-.01)/.29-1 if c.synchronous else u/.15-1,w,v/.3],-1)
        last_raw=torch.where(commit[:,None],raw,last_raw)
        offset+=1
        # Two substeps per sensor frame; flush a final single committed substep.
        if offset%2==0 or c.done.all():
            if c.execute and committed_action.any():
                if c.renderer is None:raise RuntimeError('G7 execution requires renderer')
                depth=c.renderer(c.state.base,c.capsules(c.state.base,c.state.q));c.record_render(depth,committed_action)
                c.sensor_origin_inside_self=depth.origin_inside_self.clone()
                c.grid.update(depth.points,depth.valid&committed_action[:,None,None],torch.where(committed_action,c.time,c.grid.timestamp));c.render_count+=committed_action.long()
            c.visible_previous=torch.where(action_attempted[:,None],c.queue,c.visible_previous).clone();c.queue=torch.where(committed_action[:,None],last_raw,c.queue);committed_action.zero_();action_attempted.zero_()
    c._cached_observation=None;c._finish(c.done)
    for key in before_totals:env.totals[key]+=getattr(c,key)-before_totals[key]
    return Execution(c.reason.clone(),c.failure_kind.clone(),c.arrived.clone(),c.segment_substeps*DT,c.timeout.clone(),attempted,trace,replans,dict(delta_s=c.state.s-c.start.s,committed=c.segment_substeps.clone(),n_fail=(c.failure_kind>0).long(),max_position=c.max_position.clone(),max_cbl=c.max_cbl.clone(),max_angle=c.max_angle.clone(),joint_jumps=sum(((x['over_velocity_diagnostic']&x['committed']).long() for x in c.attempts),torch.zeros_like(c.failures)),terminated=c.terminated.clone(),truncated=c.truncated.clone(),triggers=dict(failure=c.failure_kind>0,route_end=c.reason==1,arrival=c.arrived.clone(),timeout=c.segment_substeps*DT>=c.timeout,failure_limit=c.failures>=5,stall_limit=c.stalls>=5,decision_limit=c.decisions>=150,time_limit=c.time>=200)))
