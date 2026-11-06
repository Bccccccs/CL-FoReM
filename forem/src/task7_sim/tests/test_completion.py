import torch
from task7_sim.core import Candidate,Core,rollout
from task7_sim.search import inplace_progress
from task7_sim.risk import sweep_metrics
from task7_sim.perception import Grid
from test_core import fixture,candidate

def test_defaults_and_internal_sync_search():
    c=fixture();c=Core(c.state,c.route,c.grid,c.kin,c.capsules,c.collision,synchronous=True,renderer=c.renderer)
    assert c.future_offsets.shape==(15,)
    c.begin(Candidate(c.state.base.clone(),None,torch.ones(1,dtype=torch.bool)))
    assert c.cap[0]>0 and c.cap[0]<=c.route.length[0]
    expected=inplace_progress(c.start,c.route,c.kin)
    torch.testing.assert_close(c.cap,expected)
    obs=c.observe();assert obs['route_points'].shape==(1,15,3)
    assert torch.equal(obs['route_points'][0,-1],obs['route_points'][0,-2])

def test_discrete_sweep_union_and_gap_unknown_metrics():
    c=fixture();g=Grid.empty(1,dtype=torch.float64);g.observed[:]=True
    state=c.state.clone();trace=[(state,torch.ones(1,dtype=torch.bool)),(state.clone(),torch.ones(1,dtype=torch.bool))]
    a=sweep_metrics(trace,g,c.capsules)
    torch.testing.assert_close(a,torch.tensor([[3.2,0,3.2]],dtype=torch.float64))
    g.observed[0,100,100]=False;b=sweep_metrics(trace,g,c.capsules)
    assert abs(b[0,1].item()-1/280)<1e-12 and b[0,2]==0
    g.observed[:]=True;g.observed[0,100,140]=False
    d=sweep_metrics(trace,g,c.capsules)
    assert abs(d[0,2].item()-1.55)<1e-12
    g.observed[:]=True;g.height[0,100,120]=1
    e=sweep_metrics(trace,g,c.capsules)
    assert abs(e[0,0].item()-.505)<1e-12
    gd=Grid.empty(1,dtype=torch.float64);f=sweep_metrics(trace,gd,c.capsules)
    torch.testing.assert_close(f,torch.tensor([[3.2,1,0]],dtype=torch.float64))

def test_risk_cpu_gpu_and_failed_trace_exclusion():
    c=fixture();g=Grid.empty(1,dtype=torch.float64);g.observed[:]=True;g.height[0,100,120]=1
    a=sweep_metrics([(c.state,torch.ones(1,dtype=torch.bool))],g,c.capsules)
    b=fixture(device='cuda',dtype=torch.float32);gg=Grid(g.observed.cuda(),g.height.cuda().float(),g.timestamp.cuda().float())
    ref=sweep_metrics([(b.state,torch.ones(1,device='cuda',dtype=torch.bool))],gg,b.capsules)
    torch.testing.assert_close(ref.cpu().double(),a,atol=1e-6,rtol=0)

def test_rollout_automatic_metrics_no_external_callback():
    c=fixture();poses=c.state.base[:,None];s=torch.tensor([[.015]],dtype=torch.float64);ip=torch.ones(1,1,dtype=torch.bool)
    policy=lambda obs:torch.zeros(len(obs['q']),3,dtype=obs['q'].dtype,device=obs['q'].device)
    result=rollout(c.state,c.route,c.grid,poses,s,ip,policy,c.kin,c.capsules,synchronous=False)
    assert result.shape==(1,1,19) and torch.equal(result[0,0,16:],torch.tensor([3.2,1,0],dtype=torch.float64))


def test_p1_default_rotation_tolerance():
    import math,pytest
    from task7_sim.geometry import load_map
    box=[0,0,0,.1,.1,.1,math.sqrt(1+.9e-6),0]
    assert len(load_map({'boxes':[box]}))==5
    box[6]=math.sqrt(1+1.1e-6)
    with pytest.raises(ValueError,match='invalid rotation'):load_map({'boxes':[box]})

def test_p5_prefix_stops_at_first_unreachable_and_all_unreachable():
    from types import SimpleNamespace
    c=fixture(length=.14)
    class PrefixIK:
        def __init__(self,pattern):self.pattern=pattern
        def solve_world(self,base,target,previous):
            assert torch.equal(previous,c.state.q.expand(len(target),-1))
            expected=c.route.at(torch.tensor([[0,.05,.1,.14]],dtype=torch.float64)).reshape(-1,4,4)
            torch.testing.assert_close(target,expected)
            flags=torch.tensor(self.pattern,dtype=torch.bool)
            return SimpleNamespace(accepted=flags,exact=flags)
    assert inplace_progress(c.state,c.route,PrefixIK([1,1,0,1])).item()==.05
    assert inplace_progress(c.state,c.route,PrefixIK([0,0,0,0])).item()==0
    assert inplace_progress(c.state,c.route,PrefixIK([0,1,1,1])).item()==0

def test_failed_uncommitted_state_does_not_enter_risk_union():
    c=fixture();g=Grid.empty(1,dtype=torch.float64);g.observed[:]=True
    original=[(c.state,torch.ones(1,dtype=torch.bool))];far=c.state.clone();far.base[:,0]=4.5
    assert torch.equal(sweep_metrics(original,g,c.capsules),sweep_metrics(original+[(far,torch.zeros(1,dtype=torch.bool))],g,c.capsules))


def test_sync_rollout_accepts_no_external_progress():
    c=fixture(length=.02);poses=c.state.base[:,None];ip=torch.ones(1,1,dtype=torch.bool)
    policy=lambda obs:torch.zeros(len(obs['q']),3,dtype=obs['q'].dtype,device=obs['q'].device)
    a=rollout(c.state,c.route,c.grid,poses,None,ip,policy,c.kin,c.capsules,synchronous=True)
    b=rollout(c.state,c.route,c.grid,poses,torch.zeros(1,1,dtype=torch.float64),ip,policy,c.kin,c.capsules,synchronous=True)
    assert torch.equal(a,b) and a[0,0,12]==c.route.length[0]
