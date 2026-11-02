import math
import torch
from task7_sim.perception import ray_boxes, ray_capsules, Panorama, Grid, LocalCollision
from task7_sim.geometry import TruthCollision

def t(x):return torch.tensor(x,dtype=torch.float64)
def test_rays_parallel_inside_rotated_and_clipped():
    b=t([[[2,0,1,.5,.5,1,1,0]]]);o=t([[[0,0,1],[2,0,1],[0,2,1],[0,.5,1]]]);d=t([[[1,0,0],[1,0,0],[1,0,0],[1,0,0]]])
    hit=ray_boxes(o,d,b,torch.ones(1,1,dtype=torch.bool))
    torch.testing.assert_close(hit[0,[0,1,3]],t([1.5,.5,1.5]))
    assert hit[0,2].isinf()
    cap=t([[[1,0,0,1,0,2,.1]]])
    torch.testing.assert_close(ray_capsules(o[:,:1],d[:,:1],cap),t([[.9]]),atol=1e-12,rtol=0)

def test_grid_landing_only_max_height_ground_and_crop():
    g=Grid.empty(1,dtype=torch.float64)
    points=t([[[1,0,.3],[1,0,.8],[1,0,.02],[0,0,.05],[9,9,1]]])
    g.update(points,torch.ones(1,5,dtype=torch.bool),t([0]))
    assert g.observed.sum()==2 and g.height.max()==.8
    local=g.crop(t([[0,0,0]]))
    assert local.shape==(1,128,128,2)
    assert local[0,64,84,1]==.8
    assert local[0,64,64,1]==0
    rot=g.crop(t([[0,0,math.pi/2]]))
    assert rot[0,43,64,0]==1
    # immutable decision snapshot cannot see future updates
    snap=g.snapshot();g.update(t([[[2,0,1.2]]]),torch.ones(1,1,dtype=torch.bool),t([.1]))
    assert snap.observed.sum()==2 and g.observed.sum()==3

def test_panorama_shapes_occlusion_and_sensor_inside_self_report():
    b=t([[[2,0,.8,.2,2,.8,1,0],[3,0,.8,.2,2,.8,1,0]]]);mask=torch.ones(1,2,dtype=torch.bool)
    pano=Panorama(b,mask)
    empty=torch.empty(1,0,7,dtype=torch.float64);base=t([[0,0,0]])
    a=pano(base,empty)
    assert a.distance.shape==(1,90,360) and a.valid.any() and not a.origin_inside_self.item()
    b2=b.clone();b2[:,1,0]=4
    c=Panorama(b2,mask)(base,empty)
    torch.testing.assert_close(a.distance,c.distance)
    inside=t([[[0,0,.4,0,0,.6,.1]]])
    d=pano(base,inside)
    assert d.origin_inside_self.item() and not d.valid.any()
    near=t([[[.5,0,.2,.5,0,.8,.1]]]);e=pano(base,near)
    assert e.self_hit.any() and (e.valid.sum()<a.valid.sum())

def test_local_collision_never_uses_truth_and_unknown_is_free():
    g=Grid.empty(1,dtype=torch.float64);base=t([[0,0,0]])
    empty=torch.empty(1,0,7,dtype=torch.float64)
    local=LocalCollision(g.snapshot())
    assert not local(base,empty).any.item()
    b=t([[[0,0,.5,.1,.1,.5,1,0]]]);mask=torch.ones(1,1,dtype=torch.bool)
    assert TruthCollision(b,mask)(base,empty).base.item()
    g.update(t([[[0,0,.2]]]),torch.ones(1,1,dtype=torch.bool),t([0]))
    assert LocalCollision(g.snapshot())(base,empty).base.item()
    # Arm above low column clears it, arm at the column height collides.
    caps=t([[[0,0,.4,.2,0,.4,.05]]])
    assert not LocalCollision(g.snapshot())(base,caps).arm.item()
    caps[:,:,2]=.2;caps[:,:,5]=.2
    assert LocalCollision(g.snapshot())(base,caps).arm.item()

def test_perception_gpu32_cpu64():
    boxes=t([[[2,0,.8,.2,2,.8,1,0]]]);mask=torch.ones(1,1,dtype=torch.bool);base=t([[0,0,0]])
    caps=torch.empty(1,0,7,dtype=torch.float64)
    a=Panorama(boxes,mask)(base,caps)
    b=Panorama(boxes.cuda().float(),mask.cuda())(base.cuda().float(),caps.cuda().float())
    assert torch.equal(a.valid,b.valid.cpu())
    torch.testing.assert_close(a.distance[a.valid],b.distance.cpu()[a.valid].double(),atol=2e-6,rtol=0)


def test_range_no_return_and_local_cpu_gpu_alignment():
    base=t([[0,0,.3]]);mask=torch.ones(1,1,dtype=torch.bool)
    boxes=t([[[9,0,.5,.1,.1,.5,1,0]]]);caps=torch.empty(1,0,7,dtype=torch.float64)
    depth=Panorama(boxes,mask)(base,caps)
    assert depth.distance[depth.valid].max()<=6
    # upper half rays miss floor and beyond-range box -> no updates.
    assert not depth.valid[:,45:].any()
    g=Grid.empty(1,dtype=torch.float64);g.update(t([[[.02,.03,.333],[1.12,.23,.4]]]),torch.ones(1,2,dtype=torch.bool),t([.1]))
    gg=Grid(g.observed.cuda(),g.height.cuda().float(),g.timestamp.cuda().float())
    torch.testing.assert_close(gg.crop(base.cuda().float()).cpu().double(),g.crop(base),atol=1e-6,rtol=0)
    c=t([[[1.1,.2,.4,1.2,.2,.4,.03]]])
    a=LocalCollision(g)(base,c);b=LocalCollision(gg)(base.cuda().float(),c.cuda().float())
    assert torch.equal(a.base,b.base.cpu()) and torch.equal(a.arm,b.arm.cpu()) and torch.equal(a.self_collision,b.self_collision.cpu())


def test_grid_gpu32_accumulation_cpu64_reference():
    p=t([[[.023,.032,.3],[.023,.032,.8],[.023,.032,.02],[1.123,.234,.041]]]);v=torch.ones(1,4,dtype=torch.bool)
    a=Grid.empty(1,dtype=torch.float64);b=Grid.empty(1,device='cuda',dtype=torch.float32)
    a.update(p,v,t([.1]));b.update(p.cuda().float(),v.cuda(),t([.1]).cuda().float())
    assert torch.equal(a.observed,b.observed.cpu())
    torch.testing.assert_close(a.height,b.height.cpu().double(),atol=1e-6,rtol=0)
