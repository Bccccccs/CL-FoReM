"""R_pre safety and exact reachable-prefix equivalence against frozen r1 logic."""
import torch
import pytest
from task7_sim import search
from task7_sim.core import State
from task7_sim.kinematics import Kinematics,LOW,HIGH,base_transform
from task7_sim.motion import Route,matrix_quat
from test_core import fixture


def unfiltered_progress(state,route,kin,*,return_info=False):
    # Frozen r1 algorithm, independent of the new prefilter implementation.
    remaining=(route.length-state.s).clamp_min(0)
    count=int(torch.ceil(remaining.max()/.05).item())+1
    offsets=torch.arange(count,device=state.s.device,dtype=state.s.dtype)*.05
    samples=torch.minimum(state.s[:,None]+offsets[None],route.length[:,None])
    if (samples[:,-1]<route.length).any():samples=torch.cat([samples,route.length[:,None]],-1)
    B,N=samples.shape
    solved=kin.solve_world(state.base[:,None].expand(-1,N,-1).reshape(-1,3),
                           route.at(samples).reshape(-1,4,4),
                           state.q[:,None].expand(-1,N,-1).reshape(-1,6))
    prefix=solved.accepted.reshape(B,N).long().cumprod(-1)
    result=samples[torch.arange(B,device=state.s.device),(prefix.sum(-1)-1).clamp_min(0)]
    result=torch.where(prefix[:,0]>0,result,state.s)
    info=dict(targets=B*N,dls_fallbacks=int((~solved.exact).sum()),accepted=int(solved.accepted.sum()))
    return (result,info) if return_info else result


def test_all_far_targets_are_rejected_without_ik():
    c=fixture(length=.11);c.route.xyz+=100
    original=c.kin.solve_world
    calls=[]
    def counted(base,target,previous):
        calls.append(len(target));return original(base,target,previous)
    c.kin.solve_world=counted
    s,info=search.inplace_progress(c.state,c.route,c.kin,return_info=True)
    assert torch.equal(s,c.state.s)
    assert calls==[] and info['targets']==0 and info['coarse_rejected']==4


@pytest.mark.parametrize('device,dtype',[('cpu',torch.float64),('cuda',torch.float32)])
def test_uniform_10000_fk_and_approximate_tcp_targets_are_not_filtered(device,dtype):
    kin=Kinematics();rng=torch.Generator().manual_seed(20261021)
    low=torch.tensor(LOW,dtype=torch.float64);high=torch.tensor(HIGH,dtype=torch.float64)
    q=(low+(high-low)*torch.rand(10000,6,generator=rng,dtype=torch.float64)).to(device=device,dtype=dtype)
    base=torch.zeros(10000,3,device=device,dtype=dtype)
    base[:,0]=1.3;base[:,1]=-.7;base[:,2]=.9
    exact=kin.world_tcp(base,q)
    keep=search._within_reach(base,exact,q,kin)
    assert keep.all()
    # TCP targets displaced radially by the accepted positional bound, with
    # orientation held, require the tool-offset allowance used by the filter.
    approximate=exact.clone();centre=(base_transform(base)@kin.fixed('mount',q))[:,:3,3]
    direction=exact[:,:3,3]-centre;direction/=direction.norm(dim=-1,keepdim=True)
    approximate[:,:3,3]+=(.1+1e-6)*direction
    assert search._within_reach(base,approximate,q,kin).all()


@pytest.mark.parametrize('kind',['straight','bent','folded','unreachable'])
@pytest.mark.parametrize('device,dtype',[('cpu',torch.float64),('cuda',torch.float32)])
def test_search_and_generated_sync_async_progress_match_r1(kind,device,dtype,monkeypatch):
    from task7_sim import candidates
    c=fixture(device=device,dtype=dtype,length=.11)
    offsets={'straight':[[0,0,0],[.2,0,0]],
             'bent':[[0,0,0],[.1,.1,0],[.2,.1,0]],
             'folded':[[0,0,0],[2,0,0],[0,0,0]],
             'unreachable':[[5,0,0],[5.2,0,0]]}[kind]
    offsets=torch.tensor(offsets,device=device,dtype=dtype)
    c.route=Route(c.route.xyz[:,:1]+offsets[None],c.route.quat[:,:1].expand(-1,len(offsets),-1))
    c.state.s[:]=.01
    actual=search.inplace_progress(c.state,c.route,c.kin)
    expected=unfiltered_progress(c.state,c.route,c.kin)
    assert torch.equal(actual,expected)
    local=c.grid.crop(c.state.base)
    for sync in [False,True]:
        actual=candidates.generate_candidates(local,c.state,c.route,c.kin,synchronous=sync)
        with monkeypatch.context() as m:
            m.setattr(candidates,'inplace_progress',unfiltered_progress)
            reference=candidates.generate_candidates(local,c.state,c.route,c.kin,synchronous=sync)
        assert torch.equal(actual.info['inplace_progress'],reference.info['inplace_progress'])
        if not sync:assert torch.equal(actual.progress,reference.progress)
