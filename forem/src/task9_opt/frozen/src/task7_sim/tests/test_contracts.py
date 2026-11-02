import torch
import pytest
from test_core import fixture,candidate
from task7_sim.core import Candidate,feature_vector,rollout
from task7_sim.kinematics import residual
from task7_sim.perception import Panorama,Grid,LocalCollision
from task7_sim.geometry import TruthCollision,load_map

def test_synchronous_inplace_raw_action_penalty_and_cap():
    c=fixture(length=.02);c.synchronous=True;c.begin(candidate(c,x=0,cap=.02,inplace=True))
    a=torch.tensor([[1.,1.,1.]],dtype=torch.float64)
    tr=c.step(a)
    assert torch.equal(c.state.base,torch.zeros_like(c.state.base))
    assert c.state.s.item()==c.route.length.item() and tr.reason.item()==1 # P5 internal cap at route endpoint
    assert abs(tr.B.item()+.1)<1e-12
    assert torch.equal(c.queue,a) and torch.equal(tr.next_observation['previous_action'],torch.zeros_like(a))
    assert abs(tr.reward.item()-.9)<1e-12

def test_truncation_mask_and_final_observation_before_new_target():
    c=fixture();c.decisions[:]=149;c.begin(candidate(c,x=0,cap=.0075,inplace=True))
    tr=c.step(torch.zeros(1,3,dtype=torch.float64))
    assert c.truncated.item() and not c.terminated.item() and tr.mask.item()==0 # arrival outranks pure truncation
    assert tr.next_observation['subgoal'][0,-1]==0
    c=fixture();c.decisions[:]=149;c.begin(candidate(c,x=0,cap=.4))
    c.candidate.pose[:,2]=3
    while not c.done.all():tr=c.step(torch.tensor([[-1.,0,0]],dtype=torch.float64))
    assert c.truncated.item() and tr.mask.item()==1
    assert tr.next_observation['subgoal'][0,2]!=0 # same candidate retained

def test_base_vs_arm_collision_reward_and_failure_limit():
    c=fixture(wall=[.515,0,.5,.005,.1,.5,1,0]);c.synchronous=True;c.failures[:]=4
    c.begin(candidate(c));a=torch.tensor([[1.,0,1.]],dtype=torch.float64);tr=c.step(a)
    assert c.failures.item()==5 and c.terminated.item() and tr.mask.item()==0
    assert abs(tr.B.item()+10.05)<1e-12 and abs(tr.G.item()+2)<1e-12
    c=fixture();c.capsules=lambda b,q:torch.tensor([[[0,0,-.1,0,0,-.05,.01]]],dtype=q.dtype).expand(len(q),-1,-1)
    c.begin(candidate(c));tr=c.step(a)
    assert c.failure_kind.item()==3 and abs(tr.B.item()+.05)<1e-12 and tr.G.item()==-2

def test_next_tcp_preview_uses_fixed_point_zero_zero_one():
    c=fixture();c.begin(candidate(c));o=c.observe();T=c.route.at(torch.tensor([.01],dtype=torch.float64));B=c._body_transform()
    torch.testing.assert_close(o['next_tcp'][:,:3],(torch.linalg.inv(B)@T)[:,:3,3],atol=1e-12,rtol=0)
    assert o['grid'].shape==(1,128,128,3)
    assert o['grid'][...,2].sum()>0

def test_mixed_candidates_order_repeat_single_and_state_purity():
    c=fixture(batch=2);poses=c.state.base[:,None].expand(-1,3,-1).clone()
    progress=torch.tensor([[0,.015,.03],[.03,0,.015]],dtype=torch.float64);inplace=torch.ones(2,3,dtype=torch.bool)
    policy=lambda o:torch.zeros(len(o['q']),3,dtype=o['q'].dtype,device=o['q'].device)
    metrics=lambda sim:torch.tensor([[3.2,1,0]],dtype=sim.state.s.dtype,device=sim.state.s.device).expand(len(sim.state.s),-1)
    args=dict(synchronous=False,future_offsets=c.future_offsets,feature_metrics=metrics)
    run=lambda p,s,i:rollout(c.state,c.route,c.grid,p,s,i,policy,c.kin,c.capsules,**args)
    a=run(poses,progress,inplace);order=torch.tensor([2,0,1]);b=run(poses[:,order],progress[:,order],inplace[:,order])
    assert torch.equal(a[:,order],b) and torch.equal(a,run(poses,progress,inplace))
    for k in range(3):torch.testing.assert_close(a[:,k:k+1],run(poses[:,k:k+1],progress[:,k:k+1],inplace[:,k:k+1]),atol=1e-12,rtol=0)
    assert c.state.s.sum()==0 and c.queue.sum()==0 and c.grid.observed.sum()==0

def test_hidden_truth_change_does_not_change_sensor_grid_or_local_rollout():
    d=torch.float64;base=torch.zeros(1,3,dtype=d)
    boxes=torch.tensor([[[2,0,.8,.2,2,.8,1,0],[3,0,.8,.2,2,.8,1,0]]],dtype=d)
    alt=boxes.clone();alt[:,1,0]=4;mask=torch.ones(1,2,dtype=torch.bool);caps=torch.empty(1,0,7,dtype=d)
    grids=[]
    for b in [boxes,alt]:
        depth=Panorama(b,mask)(base,caps);g=Grid.empty(1,dtype=d);g.update(depth.points,depth.valid,torch.zeros(1,dtype=d));grids.append(g)
    assert torch.equal(grids[0].observed,grids[1].observed) and torch.equal(grids[0].height,grids[1].height)
    x=torch.tensor([[3.,0,0]],dtype=d)
    assert TruthCollision(boxes,mask)(x,caps).base.item() and not TruthCollision(alt,mask)(x,caps).base.item()
    c=fixture();poses=base[:,None];s=torch.tensor([[.015]],dtype=d);ip=torch.ones(1,1,dtype=torch.bool)
    policy=lambda o:torch.zeros(1,3,dtype=d);metrics=lambda sim:torch.tensor([[3.2,1,0]],dtype=d)
    out=[rollout(c.state,c.route,g,poses,s,ip,policy,c.kin,c.capsules,synchronous=False,future_offsets=c.future_offsets,feature_metrics=metrics) for g in grids]
    assert torch.equal(out[0],out[1])

def test_ik_failure_does_not_commit_q_and_metrics_use_committed_prefix():
    c=fixture();c.kin.tool_tcp[0,3]+=20 # intentional fault: current q cannot achieve the original route
    c.begin(candidate(c));tr=c.step(torch.zeros(1,3,dtype=torch.float64))
    assert tr.reason.item()==2 and tr.committed.item()==0
    assert c.state.s.item()==0 and c.failures.item()==1
    f=feature_vector(c,torch.tensor([[3.2,1,0]],dtype=torch.float64))
    assert f[0,7]==0 and torch.equal(f[0,12:16],torch.zeros(4,dtype=f.dtype))
