import numpy as np
import torch
from task7_sim.kinematics import Kinematics, fk, residual

def test_urdf_independent_fk_and_world_tool_tcp():
    k=Kinematics();g=torch.Generator().manual_seed(23)
    q=(torch.rand(100,6,generator=g,dtype=torch.float64)-.5)*5
    ref=k.model.fk(q.numpy()); torch.testing.assert_close(fk(q),torch.from_numpy(ref),atol=1e-6,rtol=0)
    base=torch.tensor([[1.,2.,1.2]],dtype=q.dtype).expand(100,-1)
    tcp=k.world_tcp(base,q)
    sol=k.solve_world(base,tcp,q)
    assert sol.accepted.all()
    torch.testing.assert_close(sol.q,q,atol=1e-6,rtol=0)
    assert (sol.position<1e-10).all() and (sol.cbl<1e-12).all()

def test_singular_inputs_84_249_and_unreachable():
    data=np.load('results/task7/t7.6-bench-20261020-r1/inputs.npz')
    print('fixture keys',data.files)
    T=torch.from_numpy(data['target'][[84,249]]) if 'target' in data else torch.from_numpy(data['targets'][[84,249]])
    prev=torch.from_numpy(data['prev'][[84,249]])
    k=Kinematics();tcp=T@k.tool_tcp.to(T)
    out=k.solve_tcp_in_arm(tcp,prev)
    assert out.accepted.all() and torch.isfinite(out.q).all()
    assert (out.position<=.100001).all() and (out.cbl<=.050001).all()
    far=tcp.clone();far[:,0,3]=10
    bad=k.solve_tcp_in_arm(far,prev)
    assert not bad.accepted.any()
    torch.testing.assert_close(bad.q,prev)

def test_dls_keeps_best_tcp_residual_and_nonfinite_is_failure():
    k=Kinematics();q=torch.zeros(1,6,dtype=torch.float64);target=fk(q)@k.tool_tcp.to(q)
    target[:,0,3]+=.04
    out=k.dls(target,q)
    initial=residual(fk(q)@k.tool_tcp.to(q),target)[0]
    assert (out.position<=initial).all()
    target[:,0,3]=float('nan')
    out=k.solve_tcp_in_arm(target,q)
    assert not out.accepted.any() and torch.isfinite(out.q).all()

def test_ik_gpu32_cpu64_residuals_and_branch_limits():
    k=Kinematics();g=torch.Generator().manual_seed(42)
    q=(torch.rand(128,6,generator=g,dtype=torch.float64)-.5)*4
    target=fk(q)@k.tool_tcp.to(q);prev=q+.001
    a=k.solve_tcp_in_arm(target,prev);b=k.solve_tcp_in_arm(target.cuda().float(),prev.cuda().float())
    assert a.accepted.all() and b.accepted.all()
    actual=(fk(b.q)@k.tool_tcp.to(b.q)).cpu().double()
    pos,ang=residual(actual,target)
    assert pos.max()<=1e-4 and ang.max()<=1e-4 # B.R exact acceptance, not a tighter invented gate
    assert (b.angle<1e-4).all()
    assert (a.branch>=0).all() and (b.q.abs()<=torch.tensor([2*np.pi,2*np.pi,np.pi,2*np.pi,2*np.pi,2*np.pi],device='cuda')).all()
    # TCP pose is continuous on an ordinary path; no hidden branch smoothing.
    q2=q[:1].repeat(8,1);q2[:,0]+=torch.arange(8,dtype=q.dtype)*.001
    prev=q2[:1]; trace=[]
    for target in (fk(q2)@k.tool_tcp.to(q2)).unbind():
        out=k.solve_tcp_in_arm(target[None],prev);trace.append(out.q);prev=out.q
    assert torch.cat(trace).diff(dim=0).abs().max()<.002


def test_cbl_acceptance_units_margin_and_exact_branch_tie():
    import math
    k=Kinematics();q=torch.zeros(1,6,dtype=torch.float64);actual=fk(q)@k.tool_tcp.to(q)
    for distance,expected in [(.1,True),(.1000005,True),(.100002,False)]:
        target=actual.clone();target[:,0,3]+=distance
        out=k._result(q,target,torch.tensor([-1]),torch.tensor([False]))
        assert out.accepted.item()==expected
    for r,expected in [(.05,True),(.0500005,True),(.050002,False)]:
        angle=2*math.asin(math.sqrt(r));R=torch.eye(4,dtype=q.dtype)[None]
        R[:,0,0]=math.cos(angle);R[:,0,1]=-math.sin(angle);R[:,1,0]=math.sin(angle);R[:,1,1]=math.cos(angle)
        target=actual.clone();target[:,:3,:3]=actual[:,:3,:3]@R[:,:3,:3]
        out=k._result(q,target,torch.tensor([-1]),torch.tensor([False]))
        assert out.accepted.item()==expected and abs(out.cbl.item()-r)<1e-12
        assert abs(out.angle.item()-angle)<1e-12
    original=q.clone();out=k.solve_tcp_in_arm(actual,q)
    assert torch.equal(q,original) and out.exact.item()


def test_historical_large_branch_jump_is_accepted_not_hidden_by_speed_limit():
    x=np.load('results/task7/t7.6-bench-20261020-r7/continuity.npz')
    k=Kinematics();previous=torch.from_numpy(x['q'][0,15][None]);target=fk(torch.from_numpy(x['generated_q'][0,15][None]))@k.tool_tcp
    out=k.solve_tcp_in_arm(target,previous)
    assert out.accepted.item() and (out.q-previous).norm()>np.pi*.05
    assert out.position.item()<=1e-4 and out.angle.item()<=1e-4


def test_dls_and_known_singular_gpu32_cpu64_reference():
    k=Kinematics();q=torch.tensor([[.1,-1,1,-.5,1,.2]],dtype=torch.float64)
    target=fk(q)@k.tool_tcp;target[:,:3,3]+=torch.tensor([[.02,.01,.01]],dtype=q.dtype)
    a=k.dls(target,q);b=k.dls(target.cuda().float(),q.cuda().float())
    assert torch.equal(a.accepted,b.accepted.cpu()) and a.accepted.all()
    d,angle=residual((fk(b.q)@k.tool_tcp.to(b.q)).cpu().double(),fk(a.q)@k.tool_tcp)
    assert d.max()<=1e-4 and angle.max()<=1e-4
    data=np.load('results/task7/t7.6-bench-20261020-r1/inputs.npz');T=torch.from_numpy(data['target'][[84,249]])@k.tool_tcp
    prev=torch.from_numpy(data['prev'][[84,249]])
    a=k.solve_tcp_in_arm(T,prev);b=k.solve_tcp_in_arm(T.cuda().float(),prev.cuda().float())
    assert a.accepted.all() and b.accepted.all()
    # Branches may differ: compare each to CPU64 target, never assume identical q.
    d,angle=residual((fk(b.q)@k.tool_tcp.to(b.q)).cpu().double(),T)
    assert (d<=.100001).all() and torch.isfinite(angle).all()
