import numpy as np
import pytest
import torch
from task8_sim.scene import SceneBatch, VoxelScene
from task8_sim.tests.test_scene import make_scene, asset


def inputs(x=2.,y=2.,caps=()):
    return (torch.tensor([[x,y,0]],dtype=torch.float64),
            torch.tensor(caps,dtype=torch.float64).reshape(1,-1,7))


def test_base_all_height_projection_and_contact_no_virtual_walls():
    scene=make_scene([[.021,.021,1.521]])
    base,caps=inputs(x=-.495,y=.025)
    assert scene.collide(base,caps,robot=None).base.item()
    base[:,0]-=1e-8
    assert not scene.collide(base,caps,robot=None).base.item()
    for x,y in [(4.99,0),(5.1,0),(-5.1,0),(0,5.1)]:
        base,caps=inputs(x=x,y=y)
        assert not scene.collide(base,caps,robot=None).any.item()


def test_arm_closed_cube_contact_empty_cavity_ceiling_and_ground():
    scene=make_scene([[.021,.021,1.021]])
    cases=[([-.1,.025,1.025,-.1,.025,1.025,.1],True),
           ([-.10000001,.025,1.025,-.10000001,.025,1.025,.1],False),
           ([0,.025,.5,.5,.025,.5,.03],False),
           ([0,.025,1.025,.5,.025,1.025,.03],True),
           ([0,.025,1.8,.5,.025,1.8,.03],False),
           ([6,0,.1,6,0,.1,.1],True)]
    for cap,expected in cases:
        base,caps=inputs(caps=[cap]);assert scene.collide(base,caps,robot=None).arm.item()==expected


def test_robot_q_provenance_survives_batch_rows_and_explicit_override():
    class ReportingRobot:
        def self_collision(self,base,caps,allowed=None,*,q=None):
            assert q is not None
            assert allowed is mask
            return q[:,0] > 0
    scene=make_scene([]);batch=SceneBatch([scene,scene])
    base=torch.tensor([[6.,0.,0.],[7.,0.,0.]],dtype=torch.float64)
    caps=torch.zeros(2,0,7,dtype=torch.float64)
    caps._self_collision_q=torch.tensor([[1.,0,0,0,0,0],[-1.,0,0,0,0,0]],dtype=torch.float64)
    mask=torch.eye(2,dtype=torch.bool)
    result=batch.collide(base,caps,robot=ReportingRobot(),allowed=mask)
    assert result.self_collision.tolist()==[True,False]
    assert batch.collide(base,caps,robot=ReportingRobot(),allowed=mask,q=-caps._self_collision_q).self_collision.tolist()==[False,True]


def test_capsule_oracle_uncompressed_scipy_minimization():
    # Scalar bounded minimisation checks production exact piecewise distance.
    from scipy.optimize import minimize_scalar
    from task8_sim.tests.test_scene import independent_cells
    rng=np.random.default_rng(84)
    points=rng.uniform([-.3,-.3,.3],[.3,.3,.9],(35,3))
    scene=make_scene(points);cells=independent_cells(points)
    caps=[];expected=[]
    for _ in range(60):
        a,b=rng.uniform([-.5,-.5,.2],[.5,.5,1.2],(2,3));radius=.04
        def distance(lo,hi):
            def f(t):
                p=a+t*(b-a);return np.square(np.maximum(np.maximum(lo-p,p-hi),0)).sum()
            return min(f(0),f(1),minimize_scalar(f,bounds=(0,1),method='bounded',options={'xatol':1e-14}).fun)
        expected.append(any(distance(lo,hi)<=radius**2 for lo,hi in cells))
        caps.append([*a,*b,radius])
    base=torch.tensor([[2.,2.,0.]]*len(caps),dtype=torch.float64)
    result=scene.collide(base,torch.tensor(caps,dtype=torch.float64)[:,None],robot=None)
    assert result.arm.tolist()==expected


def test_pcd_change_controls_collision_with_fixed_semantics():
    full=make_scene([[.021,.021,1.021]]);empty=make_scene([])
    base,caps=inputs(x=0,y=0,caps=[[0,.025,1.025,.2,.025,1.025,.01]])
    assert full.collide(base,caps,robot=None).base.item()
    assert full.collide(base,caps,robot=None).arm.item()
    assert not empty.collide(base,caps,robot=None).any.item()


def test_explicit_boundary_dyadic_sphere_contact_regression():
    scene=make_scene([[-4.979,-3.979,.521]])
    base,caps=inputs(x=10,y=10,caps=[[-5.03125,-3.975,.525,-5.03125,-3.975,.525,.03125]])
    assert scene.contains(torch.tensor([[-5.,-3.975,.525]],dtype=torch.float64)).item()
    assert scene.raycast(torch.tensor([[[-5.,-3.975,.525]]],dtype=torch.float64),
                         torch.tensor([[[1.,0.,0.]]],dtype=torch.float64),max_range=6).item()==0
    assert scene.collide(base,caps,robot=None).arm.item(), 'exact dyadic sphere tangency at authoritative lo=-5'


def test_zero_radius_and_dyadic_contacts_all_faces_explicit_bounds():
    from task8_sim.tests.test_scene import independent_cells
    points=[[-4.979,-3.979,.521],[.271,-3.979,.521],[-2.729,-3.829,.521],
            [4.971,4.971,1.521],[.021,.021,.521]]
    for p in points:
        scene=make_scene([p]);lo,hi=independent_cells([p])[0];centre=(lo+hi)/2
        caps=[]
        for axis in range(3):
            for side in (-1,1):
                for radius in (0.,.03125,.0625):
                    a=centre.copy();a[axis]=(lo if side<0 else hi)[axis]+side*radius
                    caps.append([*a,*a,radius])
        base=torch.tensor([[10.,10.,0.]]*len(caps),dtype=torch.float64)
        assert scene.collide(base,torch.tensor(caps,dtype=torch.float64)[:,None],robot=None).arm.all()


def test_base_closed_projection_matches_explicit_endpoint_intervals():
    # Construct directly in world coordinates; compare original SAT path against
    # intervals formed from the authoritative voxel endpoints, not its centre.
    from task8_sim.tests.test_scene import independent_cells
    points=[[-4.979,-3.979,.521],[.271,-3.979,.521],[-2.729,-3.829,.521],
            [4.971,4.971,1.521],[.021,.021,.521]]
    for p in points:
        scene=make_scene([p]);lo,hi=independent_cells([p])[0];centre=(lo+hi)/2
        poses=[];expected=[]
        for axis,extent in [(0,.495),(1,.335)]:
            for side in (-1,1):
                xy=centre[:2].copy();xy[axis]=(lo if side<0 else hi)[axis]+side*extent
                poses.append([*xy,0.])
                r=np.array([.495,.335])
                expected.append(bool(((xy+r)>=lo[:2]).all() and ((xy-r)<=hi[:2]).all()))
        base=torch.tensor(poses,dtype=torch.float64)
        result=scene.collide(base,torch.empty(len(base),0,7,dtype=torch.float64),robot=None)
        assert result.base.tolist()==expected, 'base SAT must use explicit world bounds'


@pytest.mark.skipif(not torch.cuda.is_available(),reason='explicit CUDA verification required')
def test_cuda_closed_dyadic_and_zero_radius_contacts():
    from task8_sim.tests.test_scene import independent_cells
    points=[[-4.979,-3.979,.521],[.271,-3.979,.521],[-2.729,-3.829,.521],
            [4.971,4.971,1.521],[.021,.021,.521]]
    for p in points:
        scene=VoxelScene.from_asset(asset([p]),device='cuda:0',dtype=torch.float32)
        lo,hi=independent_cells([p])[0]
        lo,hi=torch.tensor(lo,device='cuda:0',dtype=torch.float32),torch.tensor(hi,device='cuda:0',dtype=torch.float32)
        centre=(lo+hi)/2;caps=[]
        for axis in range(3):
            for side in (-1,1):
                for radius in (0.,.03125,.0625):
                    a=centre.clone();a[axis]=(lo if side<0 else hi)[axis]+side*radius
                    caps.append(torch.cat([a,a,a.new_tensor([radius])]))
        caps=torch.stack(caps)[:,None]
        base=caps.new_tensor([[10.,10.,0.]]).expand(len(caps),-1)
        assert scene.collide(base,caps,robot=None).arm.all()
