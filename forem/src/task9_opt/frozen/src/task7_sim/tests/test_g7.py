import math
import torch
import pytest
from test_core import fixture
from task7_sim.core import Candidate, State
from task7_sim.g7 import generate_paths, evaluate, execute, rank_paths


def target(c, distance=.03, progress=.015, inplace=False):
    pose=c.state.base.clone();pose[:,0]+=distance
    return Candidate(pose,torch.full_like(c.state.s,progress),torch.full_like(c.done,inplace))


@pytest.mark.parametrize('sync,n',[(False,14),(True,7)])
def test_paths_endpoints_and_limits(sync,n):
    c=fixture();a=target(c,.3,.03);a.pose[:,1]=.2;a.pose[:,2]=.7
    p=generate_paths(c.state,a,c.route,synchronous=sync)
    assert p.mask.shape==(1,n) and p.mask.all()
    from task7_sim.motion import arc
    base=c.state.base[:,None].expand(-1,n,-1).clone()
    for j in range(p.controls.shape[2]):
        u,w,v=p.controls[:,:,j].unbind(-1)
        base=arc(base,v,w,.05)
    from task7_sim.motion import wrap
    delta=base-a.pose[:,None];delta[...,2]=wrap(delta[...,2])
    torch.testing.assert_close(delta,torch.zeros_like(delta),atol=1e-10,rtol=0)
    assert (p.controls[...,1].abs()<=1).all() and (p.controls[...,2].abs()<=.3).all()
    assert (p.controls[...,0]>=0).all() and (p.controls[...,0]<=.3).all()
    if sync:
        active=torch.arange(p.controls.shape[2])[None,None]<p.steps[...,None]
        assert p.controls[...,0][active].eq(.1).all()


def test_inplace_degenerate_and_ranking():
    c=fixture();a=target(c,0,.015,True)
    p=generate_paths(c.state,a,c.route,synchronous=False)
    assert p.mask.sum()==1 and p.mask[0,0]
    assert p.controls[...,1:].eq(0).all()
    p=generate_paths(c.state,target(c,.3),c.route,synchronous=False)
    assert not p.mask[0,4:6].any()  # P3, both progress modes
    feasible=torch.tensor([[False,True,True,True]])
    assert rank_paths(feasible,torch.tensor([[99,0,0,0]]),torch.tensor([[1.,.09,.1,.1]]),torch.tensor([[1.,1.,3.,2.]]),torch.zeros(1,4),torch.ones(1,4,dtype=torch.bool)).item()==3
    assert rank_paths(~torch.ones_like(feasible),torch.tensor([[2,3,3,1]]),torch.ones(1,4),torch.ones(1,4),torch.zeros(1,4),torch.ones(1,4,dtype=torch.bool)).item()==1


def test_pure_evaluation_and_scored_execution():
    c=fixture();a=target(c,.03,.015)
    before=c.state.clone();grid=c.grid.snapshot();rng=torch.random.get_rng_state().clone()
    e=evaluate(c.state,c.route,c.grid,a,c.kin,c.capsules,synchronous=False)
    f=evaluate(c.state,c.route,c.grid,a,c.kin,c.capsules,synchronous=False)
    assert torch.equal(e.features,f.features) and torch.equal(rng,torch.random.get_rng_state())
    for name in ('base','q','s'):assert torch.equal(getattr(c.state,name),getattr(before,name))
    assert torch.equal(grid.height,c.grid.height)
    out=execute(c,a)
    assert out.reason.item() in (0,1) and e.feasible.any()
    path=int(e.best[0]);expected=e.traces
    for j,(state,present) in enumerate(out.trace[1:]):
        scored=expected[j+1][0]
        for name in ('base','q','s'):
            torch.testing.assert_close(getattr(state,name)[0],getattr(scored,name)[path],atol=1e-12 if name=='q' else 0,rtol=0)
    assert out.timeout.item()==pytest.approx(3*max(.03/.3,.015/.3)+2)


def test_first_failure_prefix_and_information_boundary():
    c=fixture();a=target(c,0,.015,True)
    c.grid.observed[:]=True;c.grid.height[:,100,100]=1
    e=evaluate(c.state,c.route,c.grid,a,c.kin,c.capsules,synchronous=False)
    assert not e.feasible.any() and e.features[0,7]==0 and e.features[0,12:16].eq(0).all()
    assert torch.isfinite(e.features).all()
    # A separate truth-geometry mutation is checked by the rollback test below.
    # Local-only predicted failure does not stop truth execution.
    out=execute(c,a)
    assert out.reason.item()==0


@pytest.mark.parametrize('sync',[False,True])
def test_cpu64_gpu32(sync):
    a=fixture();b=fixture(device='cuda',dtype=torch.float32)
    x=evaluate(a.state,a.route,a.grid,target(a,.03,.015),a.kin,a.capsules,synchronous=sync)
    y=evaluate(b.state,b.route,b.grid,target(b,.03,.015),b.kin,b.capsules,synchronous=sync)
    assert torch.equal(x.feasible,y.feasible.cpu()) and torch.equal(x.best,y.best.cpu())
    torch.testing.assert_close(x.features,y.features.cpu().double(),atol=1e-4,rtol=0)


def test_replanning_anchor_batch_and_timeout():
    c=fixture(batch=2);a=target(c,.19,.019)
    a.pose[1,0]=.03;a.progress[1]=.015
    out=execute(c,a)
    assert len(out.replans)>=2
    initial=out.replans[0]['evaluation'];indices=torch.arange(2)*14+initial.best
    for j,(state,present) in enumerate(out.trace[1:11]):
        scored=initial.traces[j+1][0]
        for field in ('base','q','s'):
            torch.testing.assert_close(getattr(state,field),getattr(scored,field)[indices],atol=1e-12 if field=='q' else 0,rtol=0)
    for replan in out.replans:assert torch.equal(replan['candidate'],a.pose)
    assert out.reason.eq(0).all() and out.elapsed[0]>=.5
    assert c.decisions.eq(1).all()
    assert torch.equal(c.state.s,a.progress)
    # Forced plan overrun: first-start T_seg remains fixed across every replan.
    c=fixture();a=target(c,.01,.4)
    # P1 linked saturates .3; the selected quickest complete plan fits T_seg.
    from types import SimpleNamespace
    class AcceptIK:
        def solve_world(self,base,target,q):
            z=q.new_zeros(len(q))
            return SimpleNamespace(q=q.clone(),accepted=torch.ones(len(q),dtype=torch.bool,device=q.device),position=z,cbl=z,angle=z)
    e=evaluate(c.state,c.route,c.grid,a,AcceptIK(),c.capsules,synchronous=False)
    assert e.info['timeout'].item()==pytest.approx(6.)
    assert e.path_features[0,3,5]==1 and not e.feasible[0,3]
    assert e.path_features[0,3,7]==pytest.approx(6.)


def test_truth_failure_rolls_back_first_substep():
    c=fixture(wall=[.515,0,.5,.005,.1,.5,1,0]);a=target(c,.3,.03)
    near=c.collision.boxes.clone()
    e=evaluate(c.state,c.route,c.grid,a,c.kin,c.capsules,synchronous=False)
    c.collision.boxes[:,:,0]=4.  # Different hidden geometry; sensor Grid unchanged.
    f=evaluate(c.state,c.route,c.grid,a,c.kin,c.capsules,synchronous=False)
    assert torch.equal(e.features,f.features) and e.feasible.any()
    c.collision.boxes=near
    out=execute(c,a)
    assert out.reason.item()==3 and out.elapsed.item()==0
    assert out.attempted.item()==1 and c.failures.item()==1
    assert torch.equal(c.state.base,c.start.base) and torch.equal(c.state.q,c.start.q)
    assert c.render_count.item()==0


def test_candidate_order_and_batch_independence():
    c=fixture(batch=2);a=target(c,.03,.015);a.pose[1,0]=.045
    e=evaluate(c.state,c.route,c.grid,a,c.kin,c.capsules,synchronous=False)
    ids=torch.tensor([1,0]);s=State(c.state.base[ids],c.state.q[ids],c.state.s[ids])
    b=Candidate(a.pose[ids],a.progress[ids],a.inplace[ids])
    f=evaluate(s,c.route.select(ids),c.grid.select(ids),b,c.kin,c.capsules,synchronous=False)
    torch.testing.assert_close(e.features[ids],f.features,atol=0,rtol=0)
    single=fixture();g=evaluate(single.state,single.route,single.grid,target(single,.03,.015),single.kin,single.capsules,synchronous=False)
    torch.testing.assert_close(e.features[0],g.features[0],atol=1e-12,rtol=0)


@pytest.mark.parametrize('sync',[False,True])
def test_zero_and_route_end_inplace(sync):
    for length in (0.,.0075):
        c=fixture(length=length);c.synchronous=sync
        a=target(c,0,length,True);a.progress=c.route.length.clone()
        out=execute(c,a)
        assert out.reason.item() in (0,1)
        assert torch.equal(c.state.base,c.start.base) and c.state.s==c.route.length
        assert c.strict_success and c.decisions==1
        if length==0:assert out.elapsed==0 and c.render_count==0


@pytest.mark.parametrize('sync',[False,True])
def test_full_robot_frozen_grid_cpu64_gpu32(sync):
    from task7_sim.bench_full import scene
    from task7_sim.perception import Grid
    a,_=scene();b,_=scene(device='cuda',dtype=torch.float32)
    b.grid=Grid(a.grid.observed.cuda(),a.grid.height.cuda().float(),a.grid.timestamp.cuda().float())
    x=evaluate(a.state,a.route,a.grid,target(a,.031,.016),a.kin,a.capsules,synchronous=sync)
    y=evaluate(b.state,b.route,b.grid,target(b,.031,.016),b.kin,b.capsules,synchronous=sync)
    assert torch.equal(x.feasible,y.feasible.cpu()) and torch.equal(x.best,y.best.cpu())
    torch.testing.assert_close(y.features.cpu().double(),x.features,atol=1e-4,rtol=0)


def test_all_infeasible_timeout_is_no_failure():
    c=fixture();a=target(c,.19,.019)
    e=evaluate(c.state,c.route,c.grid,a,c.kin,c.capsules,synchronous=False,cap=a.progress,timeout=torch.full_like(c.state.s,.05))
    assert not e.feasible.any()
    assert e.first_bad[e.paths.mask].eq(1).all()
    assert e.features[0,6]==1 and e.features[0,5]==1


@pytest.mark.parametrize('categories',[(2,1,0),(2,1),(2,0),(1,0),(2,2),(1,1),(0,0)])
def test_timeout_category_combinations_and_fixed_ties(categories):
    # Every order permutation must honor category priority; exact ties use index.
    import itertools
    for values in set(itertools.permutations(categories)):
        x=torch.tensor([values]);n=len(values);z=torch.zeros(1,n)
        best=rank_paths(x==2,torch.full((1,n),.9),z,z,z,torch.ones_like(x,dtype=torch.bool),pure_timeout=x==1)
        assert best.item()==values.index(max(values))


@pytest.mark.parametrize('category',[0,1,2])
def test_each_category_u25_and_masks(category):
    x=torch.full((1,5),category);mask=torch.tensor([[True,True,True,True,False]])
    # Gap threshold, duration, residual, fixed order; masked best never wins.
    assert rank_paths(x==2,torch.ones(1,5),torch.tensor([[.09,.1,.2,.3,1.]]),torch.tensor([[0.,2.,1.,1.,0.]]),torch.tensor([[0.,0.,.2,.1,0.]]),mask,pure_timeout=x==1).item()==3
    if category==0:
        # Failure position takes precedence over every U25 score.
        assert rank_paths(x==2,torch.tensor([[.99,.8,.8,.8,1.]]),torch.ones(1,5),torch.tensor([[9.,1.,1.,1.,0.]]),torch.zeros(1,5),mask,pure_timeout=x==1).item()==0


def test_trial_failure_priority_and_no_input_commit():
    from types import SimpleNamespace
    from task7_sim.g7 import trial
    from task7_sim.geometry import Collision
    c=fixture();original=c.state.clone()
    class IK:
        accepted=True
        def solve_world(self,base,target,q):
            return SimpleNamespace(q=q.clone(),accepted=torch.full((len(q),),self.accepted,dtype=torch.bool))
    ik=IK();flag=torch.ones(1,dtype=torch.bool);no=~flag
    oracle=lambda b,cap,allowed:Collision(flag,flag,flag)
    controls=torch.zeros(1,3,dtype=torch.float64)
    assert trial(c.state,c.route,controls,c.route.length,ik,c.capsules,oracle)[2].item()==4
    ik.accepted=False
    assert trial(c.state,c.route,controls,c.route.length,ik,c.capsules,oracle)[2].item()==1
    ik.accepted=True
    oracle=lambda b,cap,allowed:Collision(flag,flag,no)
    assert trial(c.state,c.route,controls,c.route.length,ik,c.capsules,oracle)[2].item()==3
    oracle=lambda b,cap,allowed:Collision(flag,no,no)
    assert trial(c.state,c.route,controls,c.route.length,ik,c.capsules,oracle)[2].item()==2
    for key in ('base','q','s'):assert torch.equal(getattr(c.state,key),getattr(original,key))


def test_near_degenerate_arc_has_bounded_expansion_but_full_duration():
    c=fixture();a=target(c,-.3,.015);a.pose[:,1]=1e-20
    p=generate_paths(c.state,a,c.route,synchronous=False,max_substeps=2)
    assert p.controls.shape[2]==2 and p.mask[0,4]
    assert torch.isfinite(p.duration).all() and p.duration[0,4]>1e18


def test_masked_and_finished_paths_do_not_keep_calling_ik():
    from types import SimpleNamespace
    c=fixture();calls=[]
    class AcceptIK:
        def solve_world(self,base,target,q):
            calls.append(len(q));z=q.new_zeros(len(q))
            return SimpleNamespace(q=q.clone(),accepted=torch.ones(len(q),dtype=torch.bool),position=z,cbl=z,angle=z)
    evaluate(c.state,c.route,c.grid,target(c,.03,.015),AcceptIK(),c.capsules,synchronous=False)
    assert max(calls)<14 and min(calls)<max(calls)


def test_finished_row_cannot_block_other_rows_replanning_or_advance_queue():
    c=fixture(batch=2);a=target(c,.03,.015);c.begin(a)
    c.done[:]=True;c.finished[:]=True;c.terminated[1]=True
    c.candidate.pose[1,0]=1.;c.timeout[1]=0;c.segment_substeps[1]=100
    c.visible_previous[1]=torch.tensor([-.8,.1,.2]);c.queue[1]=torch.tensor([.2,.3,.4])
    state=c.state.clone();previous=c.visible_previous[1].clone();queue=c.queue[1].clone()
    out=execute(c,a,mask=torch.tensor([True,False]))
    assert out.reason[0]==0
    for name in ('base','q','s'):assert torch.equal(getattr(c.state,name)[1],getattr(state,name)[1])
    assert torch.equal(c.visible_previous[1],previous) and torch.equal(c.queue[1],queue)
