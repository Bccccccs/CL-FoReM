import torch
from task7_sim.core import Core, Candidate, State, feature_vector, rollout
from task7_sim.motion import Route, matrix_quat
from task7_sim.kinematics import Kinematics
from task7_sim.geometry import TruthCollision
from task7_sim.perception import Grid,LocalCollision,Panorama

def fixture(batch=1,device='cpu',dtype=torch.float64,wall=None,length=.4):
    kin=Kinematics();base=torch.zeros(batch,3,device=device,dtype=dtype)
    q=torch.tensor([0,-1.,1.,-.5,1.,0],device=device,dtype=dtype).expand(batch,-1).clone()
    T=kin.world_tcp(base,q);xyz=torch.stack([T[:,:3,3],T[:,:3,3]+torch.tensor([length,0,0],device=device,dtype=dtype)],1)
    quat=matrix_quat(T[:,:3,:3])[:,None].expand(-1,2,-1)
    route=Route(xyz,quat);state=State(base,q,torch.zeros(batch,device=device,dtype=dtype))
    grid=Grid.empty(batch,device=device,dtype=dtype)
    boxes=torch.empty(batch,0,8,device=device,dtype=dtype) if wall is None else torch.tensor([[wall]],device=device,dtype=dtype).expand(batch,-1,-1)
    mask=torch.ones(boxes.shape[:2],device=device,dtype=torch.bool)
    caps=lambda b,q:torch.empty(len(q),0,7,device=q.device,dtype=q.dtype)
    core=Core(state,route,grid,kin,caps,TruthCollision(boxes,mask),synchronous=False,future_offsets=torch.tensor([.01,.1],device=device,dtype=dtype),renderer=Panorama(boxes,mask))
    return core

def candidate(core,x=1.,cap=.4,inplace=False):
    b=core.state.base.clone();b[:,0]+=x
    return Candidate(b,torch.full_like(core.state.s,cap),torch.full_like(core.state.s,inplace,dtype=torch.bool))

def test_failed_attempts_do_not_commit_first_or_second_substep():
    for x,committed in [(.515,0),(.53,1)]:
        c=fixture(wall=[x,0,.5,.005,.1,.5,1,0]);q0=c.state.q.clone();base0=c.state.base.clone()
        c.begin(candidate(c));tr=c.step(torch.tensor([[0.,0,1]],dtype=torch.float64))
        assert tr.done.item() and tr.reason.item()==3 and tr.mask.item()==0
        assert tr.committed.item()==committed and tr.attempted.item()==committed+1
        assert abs(tr.dt.item()-.05*committed)<1e-12
        if committed==0:
            assert torch.equal(c.state.q,q0) and torch.equal(c.state.base,base0) and c.state.s.item()==0
            assert c.render_count.item()==0 and torch.equal(c.queue,torch.zeros_like(c.queue))
        else:
            assert abs(c.state.base[0,0].item()-.015)<1e-12 and c.render_count.item()==1
        assert c.failures.item()==1

def test_zero_progress_no_action_no_render_stall_and_termination_priority():
    c=fixture();c.decisions[:]=149;c.stalls[:]=4
    out=c.begin(candidate(c,x=0,cap=0,inplace=True))
    assert out.item() and c.reason.item()==0 and c.time.item()==0 and c.render_count.item()==0
    assert c.terminated.item() and not c.truncated.item() and c.transitions==[]

def test_queue_lag_across_steps_and_new_candidate():
    c=fixture();c.begin(candidate(c));a=torch.tensor([[0,.2,.1]],dtype=torch.float64)
    tr=c.step(a)
    assert torch.equal(tr.observation['previous_action'],torch.zeros_like(a))
    assert torch.equal(tr.next_observation['previous_action'],torch.zeros_like(a))
    b=torch.tensor([[0,.3,.1]],dtype=torch.float64);tr2=c.step(b)
    assert torch.equal(tr2.observation['previous_action'],a)
    assert torch.equal(tr2.next_observation['previous_action'],a)
    # Start another segment only after current segment times out.
    while not c.done.all():c.step(torch.tensor([[-1.,0,0]],dtype=torch.float64))
    old=c.visible_previous.clone();c.begin(candidate(c,x=0,cap=.4,inplace=True))
    tr3=c.step(torch.zeros_like(a))
    assert torch.equal(tr3.observation['previous_action'],old)

def test_route_end_priority_half_step_and_success():
    c=fixture(length=.0075);cand=candidate(c,x=0,cap=0,inplace=True);cand.progress=c.route.length.clone();c.begin(cand)
    tr=c.step(torch.zeros(1,3,dtype=torch.float64))
    assert tr.reason.item()==1 and tr.committed.item()==1 and tr.dt.item()==.05
    assert tr.mask.item()==0 and c.terminated.item() and c.strict_success.item()
    assert c.render_count.item()==1

def test_timeout_bootstrap_and_reward_components():
    c=fixture();c.begin(candidate(c,x=0,cap=.4))
    # u=0, v=0, omega=1: hold route and turn away, cannot reach candidate yaw after first .05? candidate yaw is pi.
    c.candidate.pose[:,2]=3.0
    a=torch.tensor([[-1.,0,0]],dtype=torch.float64)
    while not c.done.all():tr=c.step(a)
    assert tr.reason.item()==4 and tr.mask.item()==1 and tr.reward.item()==-.1
    assert abs(tr.B.item())<1e-12 and tr.G.item()==0
    assert c.committed_total.item()==120 and c.attempted_total.item()==120 # async Tseg=max(0,.4/.3)*3+2=6 s

def test_feature_order_and_failure_time_not_committed_time():
    c=fixture(wall=[.53,0,.5,.005,.1,.5,1,0]);c.begin(candidate(c));c.step(torch.tensor([[0,0,1]],dtype=torch.float64))
    risk=torch.tensor([[.25,.5,.2]],dtype=torch.float64) # gap, unknown fraction, nearest unknown, supplied explicitly
    f=feature_vector(c,risk)
    assert f.shape==(1,19) and f[0,4]==1 and f[0,7]==.05
    assert abs(f[0,6].item()-.1/c.timeout.item())<1e-12
    assert torch.equal(f[0,16:],risk[0])

def test_rollout_batch_pure_order_independent_gpu32_cpu64():
    c=fixture(batch=2);state0=c.state.clone();cand=candidate(c,x=0,cap=.03,inplace=True)
    poses=cand.pose[:,None].expand(-1,2,-1).clone();caps=cand.progress[:,None].expand(-1,2).clone();ins=cand.inplace[:,None].expand(-1,2)
    policy=lambda obs:torch.zeros(len(obs['q']),3,device=obs['q'].device,dtype=obs['q'].dtype)
    # Risk computation is separate; known empty fixture explicitly provides metrics.
    metrics=lambda sim:torch.tensor([[3.2,1,0]],device=sim.state.s.device,dtype=sim.state.s.dtype).expand(len(sim.state.s),-1)
    out=rollout(c.state,c.route,c.grid,poses,caps,ins,policy,c.kin,c.capsules,synchronous=False,future_offsets=c.future_offsets,feature_metrics=metrics)
    assert out.shape==(2,2,19)
    assert torch.equal(c.state.q,state0.q) and torch.equal(c.state.base,state0.base)
    assert torch.equal(out[:,0],out[:,1])
    gpu=fixture(batch=2,device='cuda',dtype=torch.float32)
    out2=rollout(gpu.state,gpu.route,gpu.grid,poses.cuda().float(),caps.cuda().float(),ins.cuda(),policy,gpu.kin,gpu.capsules,synchronous=False,future_offsets=gpu.future_offsets,feature_metrics=metrics)
    torch.testing.assert_close(out2.cpu().double(),out,atol=1e-4,rtol=0)


def test_attempt_diagnostics_preserve_rejected_state_and_joint_delta():
    c=fixture(wall=[.53,0,.5,.005,.1,.5,1,0]);c.begin(candidate(c));q0=c.state.q.clone()
    c.step(torch.tensor([[0.,0,1]],dtype=torch.float64))
    assert len(c.attempts)==2
    assert c.attempts[0]['committed'].item() and not c.attempts[1]['committed'].item()
    torch.testing.assert_close(c.attempts[0]['previous_q'],q0)
    torch.testing.assert_close(c.attempts[1]['previous_q'],c.state.q)
    torch.testing.assert_close(c.attempts[0]['joint_delta'],c.state.q-q0)
    assert c.attempts[1]['base_collision'].item()


def test_core_execution_gpu32_cpu64_reference_rewards_and_commit():
    a=fixture(wall=[.525,0,.5,.005,.1,.5,1,0]);b=fixture(device='cuda',dtype=torch.float32,wall=[.525,0,.5,.005,.1,.5,1,0])
    for c in [a,b]:c.begin(candidate(c))
    raw=torch.tensor([[0.,0,1]],dtype=torch.float64);ta=a.step(raw);tb=b.step(raw.cuda().float())
    assert torch.equal(ta.reason,tb.reason.cpu()) and torch.equal(ta.committed,tb.committed.cpu()) and torch.equal(ta.mask,tb.mask.cpu())
    torch.testing.assert_close(tb.reward.cpu().double(),ta.reward,atol=1e-4,rtol=0)
    torch.testing.assert_close(b.state.base.cpu().double(),a.state.base,atol=1e-6,rtol=0)
    torch.testing.assert_close(b.state.s.cpu().double(),a.state.s,atol=1e-6,rtol=0)
