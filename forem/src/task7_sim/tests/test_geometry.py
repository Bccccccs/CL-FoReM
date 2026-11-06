import math
import pytest
import torch
from task7_sim.geometry import load_map, pad_maps, rectangle_hits, segment_box_distance, segment_distance, TruthCollision

def t(x):return torch.tensor(x,dtype=torch.float64)
def test_map_corner_rotation_walls_and_padding():
    m=load_map({"boxes":[[1,0,0,2,1,1,0,1]]},rotation_tolerance=1e-8)
    torch.testing.assert_close(m[0,:3],t([.5,1,.5]))
    assert len(m)==5
    # Re-reading serialized centre-independent corner walls must not double them.
    walls=[[-5,-5,0,.15,10,1.6,1,0],[4.85,-5,0,.15,10,1.6,1,0],[-4.85,-5,0,9.7,.15,1.6,1,0],[-4.85,4.85,0,9.7,.15,1.6,1,0]]
    assert len(load_map({"boxes":walls},rotation_tolerance=1e-8))==4
    a,mask=pad_maps([m,load_map({"boxes":[]},rotation_tolerance=1e-8)])
    assert a.shape==(2,5,8) and mask.sum().item()==9

@pytest.mark.parametrize("box",[[0,0,0,0,1,1,1,0],[0,0,0,1,1,1,2,0],[float('nan'),0,0,1,1,1,1,0],[4.9,0,0,1,1,1,1,0]])
def test_bad_map_rejected_with_identity(box):
    with pytest.raises(ValueError,match='map-9'):load_map({"boxes":[box]},map_id='map-9',rotation_tolerance=1e-8)

def test_rectangles_touch_rotate_and_height_independent():
    box=t([[[1,0,10,.5,.5,.1,1,0]]])
    assert rectangle_hits(t([[0,0,0]]),box).item() is False
    assert rectangle_hits(t([[.005,0,0]]),box).item() is True
    # a turned 0.99 x .67 footprint reaches y=.495
    box=t([[[0,.6,0,.01,.11,.1,1,0]]])
    assert rectangle_hits(t([[0,0,math.pi/2]]),box).item()

def test_segment_box_exact_distance_not_expanded_aabb():
    # corner distance sqrt(2), distinguishes rounded capsule from expanded box.
    a=t([[2,2,0]]);b=t([[2,2,2]]);h=t([[1,1,1]])
    torch.testing.assert_close(segment_box_distance(a,b,h),t([math.sqrt(2)]))
    torch.testing.assert_close(segment_box_distance(t([[-2,0,0]]),t([[2,0,0]]),h),t([0]))
    torch.testing.assert_close(segment_distance(t([[0,0,0]]),t([[1,0,0]]),t([[.5,1,0]]),t([[.5,-1,0]])),t([0]))

def test_truth_collision_separates_base_arm_floor_and_self():
    boxes=t([[[2,0,1,.2,.2,1,1,0]]]);mask=torch.ones(1,1,dtype=torch.bool)
    coll=TruthCollision(boxes,mask)
    caps=t([[[1.5,0,1,2.5,0,1,.05]]])
    out=coll(t([[0,0,0]]),caps)
    assert not out.base.item() and out.arm.item()
    floor=t([[[0,0,.03,0,0,.5,.04]]])
    assert coll(t([[0,0,0]]),floor).arm.item()
    caps=t([[[0,0,1,1,0,1,.1],[.5,-1,1,.5,1,1,.1]]])
    assert coll(t([[0,0,0]]),caps).self_collision.item()
    allowed=torch.ones(2,2,dtype=torch.bool)
    assert not coll(t([[0,0,0]]),caps,allowed).self_collision.item()

def test_geometry_gpu_float32_matches_cpu_float64():
    a=t([[-2,.3,.2],[2,2,0],[0,0,0]]);b=t([[2,.3,.2],[2,2,2],[0,0,0]]);h=t([[1,1,1]]).expand(3,-1)
    ref=segment_box_distance(a,b,h)
    got=segment_box_distance(a.cuda().float(),b.cuda().float(),h.cuda().float()).cpu().double()
    torch.testing.assert_close(got,ref,atol=1e-6,rtol=0)


def test_truth_and_self_gpu32_cpu64_reference():
    boxes=t([[[2,0,1,.2,.2,1,1,0]],[[2,0,1,.2,.2,1,1,0]]]);mask=torch.ones(2,1,dtype=torch.bool)
    caps=t([[[1.5,0,1,2.5,0,1,.05],[2,-1,1,2,1,1,.05]],[[0,0,.03,0,0,.5,.04],[1,1,1,1,1,2,.02]]])
    base=t([[0,0,0],[0,0,1]])
    a=TruthCollision(boxes,mask)(base,caps);b=TruthCollision(boxes.cuda().float(),mask.cuda())(base.cuda().float(),caps.cuda().float())
    assert torch.equal(a.base,b.base.cpu()) and torch.equal(a.arm,b.arm.cpu()) and torch.equal(a.self_collision,b.self_collision.cpu())
