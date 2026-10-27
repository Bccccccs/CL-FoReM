"""Task8 ghost policy: real geometry/query regressions, CPU float64."""
import copy
import json
from pathlib import Path
import torch
from task7_sim.robot import RobotGeometry

ROOT = Path(__file__).resolve().parents[3]

def t(x):
    return torch.tensor(x, dtype=torch.float64)

def sphere_fixture(world_points, links):
    """Relocate selected fitted spheres, retaining real FK/body/permission engine."""
    old = RobotGeometry()
    data = copy.deepcopy(old.data)
    q = t([[0, 0, 0, 0, 0, 0]])
    base = t([[0, 0, 0]])
    transforms = old._transforms(base, q)
    specs = []
    for point, link in zip(world_points, links):
        transform = transforms[link][0]
        local = transform[:3, :3].T @ (t(point)-transform[:3, 3])
        specs.append(dict(link=link, centre=local.tolist(), radius_m=.0001,
                          group=data['self_names'].index(link)))
    data['self_spheres'] = specs
    data['self_zero_sphere_pairs'] = []
    data['self_zero_sphere_body_pairs'] = []
    return data, base, q

def test_sensor_only_body_contacts_ignored_without_index_or_permission_changes():
    from task8_sim.robot import GhostRobotGeometry
    original = RobotGeometry()
    for sensor in ('velodyne1_base_link', 'velodyne2_base_link'):
        body = next(x for x in original.data['body'] if x['link'] == sensor)
        data, base, q = sphere_fixture([body['centre']], ['ur5_wrist_3_link'])
        old, ghost = RobotGeometry(data), GhostRobotGeometry(data)
        assert old.self_collision(base, old(base,q),q=q).item()
        assert not ghost.self_collision(base, ghost(base,q),q=q).item()
        assert ghost.data == data
        assert ghost.names == old.names
        assert torch.equal(ghost.allowed, old.allowed)
        assert ghost.body_boxes(base).shape == old.body_boxes(base).shape
        assert data == old.data

def test_top_plate_and_arm_arm_contacts_remain_active():
    from task8_sim.robot import GhostRobotGeometry
    original = RobotGeometry()
    plate = next(x for x in original.data['body'] if x['link'] == 'top_plate_link')
    data, base, q = sphere_fixture([plate['centre']], ['ur5_wrist_3_link'])
    ghost = GhostRobotGeometry(data)
    assert ghost.self_collision(base, ghost(base,q),q=q).item()
    data, base, q = sphere_fixture([[0,0,3], [0,0,3]], ['ur5_upper_arm_link','ur5_wrist_3_link'])
    ghost = GhostRobotGeometry(data)
    assert ghost.self_collision(base, ghost(base,q),q=q).item()

def scene(name):
    from task8_sim.assets import load_asset
    from task8_sim.scene import VoxelScene, SceneBatch
    asset = load_asset(ROOT/'results/task8/t8-exec-20261026/cube-pool/manifest.json', name)
    return SceneBatch([VoxelScene.from_asset(asset, device='cpu', dtype=torch.float64)])

def config():
    return json.loads((ROOT/'config/task8/sensor.json').read_text())

def test_real_pcd_ghost_inside_self_and_nearest_scene_occlusion():
    from task8_sim.perception import PcdPanorama
    base = t([[0,0,0]])
    inside = t([[[0,0,.4,0,0,.6,.2]]])
    body = t([[[0,0,.5,1,1,1,1,0]]])
    pano = PcdPanorama(scene('occlusion'), sensor_config=config())
    depth = pano(base, inside, body)
    empty = torch.empty(1,0,7,dtype=torch.float64)
    plain = pano(base, empty)
    assert depth.distance.shape == (1,90,360)
    assert depth.points.shape == (1,90,360,3)
    assert depth.valid.any() and not depth.self_hit.any() and not depth.origin_inside_self.any()
    torch.testing.assert_close(depth.distance, plain.distance)
    assert depth.sensor_policy == 'ghost-v1'
    # Pixel +.5 degree azimuth/elevation hits x=1.25 near block, not x=2.75 far block.
    ray_distance = 1.25/(torch.cos(t(.5*torch.pi/180))**2)
    torch.testing.assert_close(depth.distance[0,45,0],ray_distance,atol=1e-12,rtol=0)
    assert depth.points[0,45,0,0] < 2

def test_fixed_base_extrinsics_pixel_centres_ground_and_range():
    from task8_sim.perception import PcdPanorama
    empty = torch.empty(1,0,7,dtype=torch.float64)
    base = t([[1,-2,torch.pi/2]])
    depth = PcdPanorama(scene('empty'),sensor_config=config())(base,empty)
    # Empty map preserves analytical ground and no upper-half returns.
    assert not depth.valid[:,45:].any()
    assert depth.valid[:,:40].all()
    pitch = t((-44.5)*torch.pi/180)
    az = t(90.5*torch.pi/180)
    distance = -.5/torch.sin(pitch)
    expected = t([1,-2,.5])+distance*torch.stack([torch.cos(pitch)*torch.cos(az),torch.cos(pitch)*torch.sin(az),torch.sin(pitch)])
    torch.testing.assert_close(depth.points[0,0,0],expected,atol=1e-12,rtol=0)
    invalid = depth.points[~depth.valid]
    torch.testing.assert_close(invalid, t([1,-2,.5]).expand_as(invalid))
    assert depth.distance[depth.valid].max() <= 6

def test_scene_inside_origin_is_zero_and_grid_uses_real_landings_only():
    from task8_sim.perception import PcdPanorama
    from task7_sim.perception import Grid
    empty = torch.empty(1,0,7,dtype=torch.float64)
    depth = PcdPanorama(scene('axis_aligned'),sensor_config=config())(t([[2,0,0]]),empty)
    assert depth.valid.all() and not depth.distance.any()
    assert not depth.origin_inside_self.any()
    outside = PcdPanorama(scene('occlusion'),sensor_config=config())(t([[0,0,0]]),empty)
    grid = Grid.empty(1,dtype=torch.float64)
    grid.update(outside.points,outside.valid,t([.1]))
    # Far block hidden in this frontal direction; its centre receives no truth injection.
    assert not grid.observed[0,100,160]
    assert grid.observed.any()

def test_real_scene_environment_and_ground_collisions_preserved():
    from task8_sim.robot import GhostRobotGeometry
    robot = GhostRobotGeometry()
    base = t([[0,0,0]])
    empty_scene = scene('empty')
    low = t([[[2,0,.01,2.1,0,.01,.02]]])
    assert empty_scene.collide(base,low,robot=None).arm.item()
    cap = t([[[2,0,.5,2.1,0,.5,.02]]])
    assert scene('axis_aligned').collide(base,cap,robot=None).arm.item()
    assert scene('axis_aligned').collide(t([[2,0,0]]),torch.empty(1,0,7,dtype=torch.float64),robot=None).base.item()

def test_same_ghost_robot_used_by_real_ik_collision_branch_selection():
    from task7_sim.kinematics import Kinematics
    from task8_sim.robot import GhostRobotGeometry
    robot, kin = GhostRobotGeometry(), Kinematics()
    base, previous = t([[0,0,0]]), t([[0,-1,1,-.5,1,0]])
    target = kin.world_tcp(base,previous)
    result = kin.solve_world(base,target,previous,robot=robot)
    assert result.accepted.item()
    caps = robot(base,result.q)
    assert torch.isfinite(caps).all()
    assert not robot.self_collision(base,caps,q=result.q).item()
    assert (caps[...,[2,5]].amin(-1)-caps[...,6]>0).all()


def test_original_inside_self_regression_and_real_robot_q_independence():
    from task7_sim.perception import Panorama
    from task8_sim.perception import PcdPanorama
    from task8_sim.robot import GhostRobotGeometry
    base = t([[0,0,0]])
    inside = t([[[0,0,.4,0,0,.6,.2]]])
    old = Panorama(torch.empty(1,0,8,dtype=torch.float64),torch.empty(1,0,dtype=torch.bool))(base,inside)
    assert old.origin_inside_self.item() and not old.valid.any()
    robot = GhostRobotGeometry()
    pano = PcdPanorama(scene('empty'),sensor_config=config())
    first = pano(base,robot(base,t([[0,-1,1,-.5,1,0]])),robot.body_boxes(base))
    second = pano(base,robot(base,t([[1,.5,-.5,1,-1,.7]])),robot.body_boxes(base))
    assert first.valid.any() and not first.origin_inside_self.any()
    torch.testing.assert_close(first.distance,second.distance)
    torch.testing.assert_close(first.points,second.points)

def test_gpu32_cpu64_real_pcd_ghost_depth_and_collision_parity():
    import os
    import pytest
    if os.environ.get('TASK8_TEST_CUDA') != '1':
        pytest.skip('requires parent GPU authorization via TASK8_TEST_CUDA=1')
    import time
    from task8_sim.assets import load_asset
    from task8_sim.scene import VoxelScene, SceneBatch
    from task8_sim.perception import PcdPanorama
    from task8_sim.robot import GhostRobotGeometry
    asset = load_asset(ROOT/'results/task8/t8-exec-20261026/cube-pool/manifest.json','occlusion')
    cpu_scene = SceneBatch([VoxelScene.from_asset(asset,device='cpu',dtype=torch.float64)])
    gpu_scene = SceneBatch([VoxelScene.from_asset(asset,device='cuda:0',dtype=torch.float32)])
    robot = GhostRobotGeometry()
    base, q = t([[0,0,0]]), t([[0,-1,1,-.5,1,0]])
    gpu_base, gpu_q = base.cuda().float(), q.cuda().float()
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
    start = time.perf_counter()
    gpu_caps = robot(gpu_base,gpu_q)
    gpu = PcdPanorama(gpu_scene,sensor_config=config())(gpu_base,gpu_caps,robot.body_boxes(gpu_base))
    cpu_caps = robot(base,q)
    cpu = PcdPanorama(cpu_scene,sensor_config=config())(base,cpu_caps,robot.body_boxes(base))
    assert gpu.distance.device.type == 'cuda' and gpu.distance.dtype == torch.float32
    assert torch.equal(cpu.valid,gpu.valid.cpu())
    # task7's existing precision gate is 2e-6m. Here 2e-5m bounds float32
    # ray arithmetic up to 6m; record actual error, not a voxel-size tolerance.
    error = (cpu.distance[cpu.valid]-gpu.distance.cpu()[cpu.valid].double()).abs().max().item()
    assert error <= 2e-5
    assert not gpu.self_hit.any() and not gpu.origin_inside_self.any()
    a = cpu_scene.collide(base,cpu_caps,robot=robot,q=q)
    b = gpu_scene.collide(gpu_base,gpu_caps,robot=robot,q=gpu_q)
    for key in ('base','arm','self_collision'):
        assert torch.equal(getattr(a,key),getattr(b,key).cpu())
    torch.cuda.synchronize()
    print(json.dumps(dict(device=str(gpu.distance.device),dtype=str(gpu.distance.dtype),
                          depth_max_abs_m=error,elapsed_s=time.perf_counter()-start,
                          peak_allocated_bytes=torch.cuda.max_memory_allocated())))
