import ast
import copy
from pathlib import Path
import random
import pytest
import torch
from task7_lower.observation import encode_grid, decode_grid, vector, preprocess
from task7_lower.replay import Replay
from task7_lower.networks import Actor, TwinQ
from task7_lower.sac import LowerSAC


def obs(n=2,sync=True,device='cpu'):
    return dict(grid=torch.rand(n,128,128,3,device=device),q=torch.rand(n,6,device=device),tcp=torch.rand(n,7,device=device),next_tcp=torch.rand(n,7,device=device),route_points=torch.rand(n,15,3,device=device),subgoal=torch.rand(n,5 if sync else 6,device=device),synchronous=torch.full((n,1),float(sync),device=device),previous_action=torch.rand(n,3,device=device),scan_timestamp=torch.zeros(n,device=device))


def test_quantization():
    g=torch.tensor([0.,0.,1.,1.,.005,0.,1.,.015,1.,1.,3.,0.]).reshape(1,2,2,3)
    q=encode_grid(g)
    assert q.dtype==torch.uint8
    assert q[...,1].flatten().tolist()==[0,0,2,255]
    assert torch.equal(decode_grid(q)[...,1],q[...,1].float()*.01)
    assert torch.equal(encode_grid(decode_grid(q)),q)


@pytest.mark.parametrize('sync',[False,True])
def test_vector_order_and_online_replay(sync):
    o=obs(sync=sync);m,v=preprocess(o)
    expected=torch.cat([o[k].flatten(1) for k in ('q','tcp','next_tcp','route_points','subgoal','synchronous','previous_action')],1)
    assert torch.equal(v,expected)
    assert v.shape==(2,74 if sync else 75)
    r=Replay(3,v.shape[1],7,'cpu');r.push(o,torch.zeros(2,3),torch.ones(2),o,torch.ones(2))
    b=r.gather([0,1]);assert torch.equal(b[0],m) and torch.equal(b[1],v)
    s=r.state_dict();rr=Replay(3,v.shape[1],99,'cpu');rr.load_state_dict(s)
    assert r.sample_indices(2)==rr.sample_indices(2)
    for a,b in zip(r.gather([0,1]),rr.gather([0,1])):assert torch.equal(a,b)
    r.push(o,torch.ones(2,3),torch.ones(2),o,torch.zeros(2));assert len(r)==3 and r.position==1


def test_actor_deterministic_and_independent_encoders():
    a=Actor(74);q=TwinQ(74);m,v=preprocess(obs());mean,std=a.params(m,v)
    assert torch.equal(a.predict(m,v,True),mean.tanh())
    assert std.min()>=-20 and std.max()<=2
    action,lp=a.sample(m,v);assert action.shape==(2,3) and lp.shape==(2,) and torch.isfinite(lp).all()
    assert not (set(map(id,a.encoder.parameters())) & set(map(id,q.parameters())))
    assert not (set(map(id,q.q1.encoder.parameters())) & set(map(id,q.q2.encoder.parameters())))


def reference_update():
    tree=ast.parse(Path('/root/mm_husky_ws/scripts/scwm_sac.py').read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ScwmSAC')
    fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='update_from_batch')
    module=ast.Module(body=[fn],type_ignores=[])
    def soft_update(target,source,tau):
        for t,s in zip(target.parameters(),source.parameters()):t.data.copy_(t.data*(1-tau)+s.data*tau)
    scope=dict(torch=torch,F=torch.nn.functional,soft_update=soft_update)
    exec(compile(module,'scwm_sac.py','exec'),scope)
    return scope['update_from_batch']


@pytest.mark.parametrize('floor',[False,True])
def test_sac_matches_reference_and_full_resume(floor):
    torch.manual_seed(47);s=LowerSAC(74,'cpu',100);ref=copy.deepcopy(s)
    if floor:
        s.log_alpha.data.fill_(-10);ref.log_alpha.data.fill_(-10)
    m,v=preprocess(obs());batch=(m,v,torch.rand(2,3),torch.rand(2,1),m,v,torch.ones(2,1))
    state=torch.get_rng_state();a=s.update_from_batch(batch,0)
    torch.set_rng_state(state);b=reference_update()(ref,batch,0)
    for x,y in zip(a,b):assert torch.equal(x,y)
    for name in ('policy','critic','critic_target'):
        for x,y in zip(getattr(s,name).parameters(),getattr(ref,name).parameters()):assert torch.equal(x,y)
    assert s.automatic_entropy_tuning==ref.automatic_entropy_tuning
    saved=copy.deepcopy(s.full_state_dict());clone=LowerSAC(74,'cpu',100);clone.load_full_state_dict(saved)
    state=torch.get_rng_state();a=s.update_from_batch(batch,1)
    torch.set_rng_state(state);b=clone.update_from_batch(batch,1)
    for x,y in zip(a,b):assert torch.equal(x,y)


def test_distribution_matches_cbl_sb3_single_tanh():
    # Load original vendored classes directly, without importing the old
    # ROS/Ray/gym training stack into this standalone task7 process.
    import abc,numpy as np
    source=Path('/root/mm_husky_ws/src/modulation_rl/scripts/stable_baselines3/common/distributions.py')
    tree=ast.parse(source.read_text())
    names={'Distribution','DiagGaussianDistribution','SquashedDiagGaussianDistribution','TanhBijector','sum_independent_dims'}
    nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[])
    ast.fix_missing_locations(module)
    scope=dict(th=torch,nn=torch.nn,np=np,ABC=abc.ABC,abstractmethod=abc.abstractmethod,Normal=torch.distributions.Normal)
    exec(compile(module,str(source),'exec'),scope)
    SquashedDiagGaussianDistribution=scope['SquashedDiagGaussianDistribution']
    a=Actor(74);m,v=preprocess(obs());mean,logstd=a.params(m,v)
    state=torch.get_rng_state();action,lp=a.sample(m,v)
    torch.set_rng_state(state);expected,elp=SquashedDiagGaussianDistribution(3).log_prob_from_params(mean,logstd)
    assert torch.equal(action,expected) and torch.equal(lp,elp)
