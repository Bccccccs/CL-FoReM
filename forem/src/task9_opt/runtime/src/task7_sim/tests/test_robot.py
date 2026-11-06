import torch
from task7_sim.robot import RobotGeometry,build_robot_config
from task7_sim.geometry import TruthCollision,pad_maps,load_map
from task7_sim.perception import Panorama,LocalCollision,Grid

def test_mesh_capsules_enclose_vertices_and_fixed_gripper():
    data=build_robot_config(samples=10000,seed=20261021)
    assert data['samples']==10000 and len(data['capsules'])==8
    for cap in data['capsules']:
        assert cap['max_vertex_distance_m']<=cap['radius_m']-.02+1e-12
    robot=RobotGeometry(data)
    q=torch.tensor([[0,-1.,1.,-.5,1.,0]],dtype=torch.float64);base=torch.zeros(1,3,dtype=q.dtype)
    c=robot(base,q)
    assert c.shape==(1,8,7) and robot.body_boxes(base).shape[1]>0
    assert torch.isfinite(c).all() and torch.equal(robot.allowed,robot.allowed.T)
    assert all(x in ['adjacent','always','same_link'] for x in data['allowed_reasons'].values())

def test_full_robot_collision_sensor_and_cpu64_gpu32():
    robot=RobotGeometry();q=torch.tensor([[0,-1.,1.,-.5,1.,0]],dtype=torch.float64);base=torch.zeros(1,3,dtype=q.dtype)
    cap=robot(base,q);gpu=robot(base.cuda().float(),q.cuda().float())
    torch.testing.assert_close(gpu.cpu().double(),cap,atol=1e-6,rtol=0)
    boxes,mask=pad_maps([load_map({'boxes':[]})]);truth=TruthCollision(boxes,mask,robot=robot)
    a=truth(base,cap);b=TruthCollision(boxes.cuda().float(),mask.cuda(),robot=robot)(base.cuda().float(),gpu)
    assert torch.equal(a.any,b.any.cpu())
    depth=Panorama(boxes,mask,robot=robot)(base,cap)
    assert depth.origin_inside_self.shape==(1,) and depth.self_hit.any()
    # Obstacle at a selected arm capsule midpoint can hit arm outside chassis.
    idx=2;p=(cap[0,idx,:3]+cap[0,idx,3:6])/2
    obstacle=torch.cat([p,torch.full((3,),.03,dtype=q.dtype),torch.tensor([1.,0],dtype=q.dtype)])[None,None]
    assert TruthCollision(obstacle,torch.ones(1,1,dtype=torch.bool),robot=robot)(base,cap).arm.item()
