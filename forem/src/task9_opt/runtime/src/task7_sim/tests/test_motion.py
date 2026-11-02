import math
import pytest
import torch
from task7_sim.motion import arc, actions, Route, quat_matrix, matrix_quat, advance

def t(x):return torch.tensor(x,dtype=torch.float64)
def test_arc_quarter_circle_straight_and_semigroup():
    x=t([[0,0,0]])
    got=arc(x,t([.3]),t([1]),math.pi/2)
    torch.testing.assert_close(got,t([[.3,.3,math.pi/2]]),atol=1e-12,rtol=0)
    for v,w in [(0.,1.),(-.3,-1.),(.3,1e-12),(.3,0.)]:
        full=arc(x,t([v]),t([w]),.1)
        half=arc(arc(x,t([v]),t([w]),.05),t([v]),t([w]),.05)
        torch.testing.assert_close(full,half,atol=1e-12,rtol=0)
    with pytest.raises(ValueError):arc(x,t([.4]),t([0]),.1)

def test_cbl_action_order_and_raw_zero_inplace():
    a=t([[-1,1,-1],[1,-1,1]])
    u,w,v=actions(a,True)
    torch.testing.assert_close(u,t([.01,.3]));torch.testing.assert_close(w,t([1,-1]));torch.testing.assert_close(v,t([-.3,.3]))
    u,w,v=actions(a,False,torch.tensor([True,False]))
    assert u[0]==0 and w[0]==0 and v[0]==0 and a[0,1]==1
    torch.testing.assert_close(advance(t([.9,.3]),t([.3,0]),t([1,.7])),t([.915,.3]))

def test_route_linear_slerp_sign_and_duplicate_pose():
    route=Route(t([[[0,0,1],[1,0,1],[2,0,1]]]),t([[[0,0,0,1],[0,0,0,-1],[0,0,1,0]]]))
    T=route.at(t([[.5,1.5,4]]))
    torch.testing.assert_close(T[0,:,:3,3],t([[.5,0,1],[1.5,0,1],[2,0,1]]))
    torch.testing.assert_close(T[0,1,:2,:2],t([[0,-1],[1,0]]),atol=1e-12,rtol=0)
    dup=Route(t([[[0,0,1],[0,0,1],[1,0,1]]]),t([[[0,0,0,1]]*3]))
    assert torch.isfinite(dup.at(t([[0,.5,1]]))).all()
    with pytest.raises(ValueError,match='orientation-only'):Route(t([[[0,0,0],[0,0,0]]]),t([[[0,0,0,1],[0,0,1,0]]]))

def test_motion_gpu32_cpu64():
    x=t([[1,2,.4],[-1,0,-2]])
    torch.testing.assert_close(arc(x.cuda().float(),t([.3,-.2]).cuda().float(),t([.5,-1]).cuda().float(),.05).cpu().double(),arc(x,t([.3,-.2]),t([.5,-1]),.05),atol=1e-6,rtol=0)
    q=t([[.2,.3,.4,.5],[-.3,.2,.1,.4]]);q=q/q.norm(dim=-1,keepdim=True)
    torch.testing.assert_close(quat_matrix(matrix_quat(quat_matrix(q))),quat_matrix(q),atol=1e-12,rtol=0)


def test_route_gpu32_cpu64_slerp_and_endpoint():
    xyz=t([[[0,0,1],[.5,.4,1.1],[1,0,.8]]]);quat=t([[[0,0,0,1],[0,0,.3,.9],[0,.4,0,.8]]])
    a=Route(xyz,quat);b=Route(xyz.cuda().float(),quat.cuda().float())
    s=t([[0,.2,.6,2]])
    torch.testing.assert_close(b.at(s.cuda().float()).cpu().double(),a.at(s),atol=1e-6,rtol=0)


def test_float32_small_orientation_only_segment_is_explicitly_rejected():
    xyz=torch.zeros(1,2,3,dtype=torch.float32)
    q=torch.tensor([[[0,0,0,1],[0,0,.0005,1]]],dtype=torch.float32)
    with pytest.raises(ValueError,match='orientation-only'):Route(xyz,q)
