"""Shared P5 reachable-prefix search. IK only, no map/collision input.
R_pre derivation and safety evidence: task7.15 r2 / SRC-0442–0443.
"""
from functools import lru_cache
import math
import torch
from .kinematics import base_transform


@lru_cache(maxsize=32)
def _tool0_radius(model):
    """Triangle-inequality bound from the supplied expanded URDF joint origins.
    Rotations preserve each origin translation's norm; include all fixed joints.
    """
    tip='ur5_tool0';lengths=[]
    while tip!='ur5_base_link':
        parent,origin,axis,name,kind=model.joints[tip]
        lengths.append(math.hypot(*origin[:3,3]))
        tip=parent
    return math.fsum(lengths)


def _within_reach(base,target,previous,kin):
    # Custom IK or test doubles without a URDF model have no proven bound.
    # Preserve the existing solve_world-only interface by passing all samples.
    if not hasattr(kin,'model') or not hasattr(kin,'fixed'):
        return torch.ones(len(target),device=base.device,dtype=torch.bool)
    centre=(base_transform(base)@kin.fixed('mount',previous))[:,:3,3]
    tcp_offset=kin.fixed('tool_tcp',previous)[:3,3].norm()
    # N1 measures position error at TCP, not at the target tool0 frame.
    # A rotated tool offset cannot be treated as an invariant residual vector.
    # ||base->target_TCP|| - ||tool0->TCP|| is a conservative tool0 radial
    # lower bound. R_tool0 + 0.1 is the requested nominal R_pre. The 1e-6
    # term below is N1's existing acceptance guard, not a new tolerance.
    lower=(target[:,:3,3]-centre).norm(dim=-1)-tcp_offset
    return lower<=_tool0_radius(kin.model)+.1+1e-6


def inplace_progress(state,route,kin,*,return_info=False):
    remaining=(route.length-state.s).clamp_min(0)
    count=int(torch.ceil(remaining.max()/.05).item())+1
    offsets=torch.arange(count,device=state.s.device,dtype=state.s.dtype)*.05
    samples=torch.minimum(state.s[:,None]+offsets[None],route.length[:,None])
    # Include the clipped route endpoint, including a final <0.05m interval.
    if (samples[:,-1]<route.length).any():samples=torch.cat([samples,route.length[:,None]],-1)
    B,N=samples.shape;base=state.base[:,None].expand(-1,N,-1).reshape(-1,3)
    previous=state.q[:,None].expand(-1,N,-1).reshape(-1,6)
    target=route.at(samples).reshape(-1,4,4)
    keep=_within_reach(base,target,previous,kin)
    accepted=torch.zeros(B*N,device=base.device,dtype=torch.bool)
    dls=0
    if keep.any():
        solved=kin.solve_world(base[keep],target[keep],previous[keep])
        accepted[keep]=solved.accepted
        dls=int((~solved.exact).sum().item())
    prefix=accepted.reshape(B,N).long().cumprod(-1)
    indices=(prefix.sum(-1)-1).clamp_min(0)
    result=samples[torch.arange(B,device=state.s.device),indices]
    result=torch.where(prefix[:,0]>0,result,state.s)
    count_kept=int(keep.sum().item())
    info=dict(targets=count_kept,dls_fallbacks=dls,accepted=int(accepted.sum().item()),
              sampled_targets=B*N,coarse_rejected=B*N-count_kept,
              ik_batch_calls=int(count_kept>0))
    return (result,info) if return_info else result
