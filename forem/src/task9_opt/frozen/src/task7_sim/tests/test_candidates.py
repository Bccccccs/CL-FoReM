"""A.8: regressions for corridor, shared-prefix, slots and information boundary."""
import math
import torch
import pytest
from task7_sim import candidates
from task7_sim.core import State
from task7_sim.motion import Route, matrix_quat
from task7_sim.perception import Grid, LocalCollision, Panorama
from task7_sim.kinematics import Kinematics
from test_core import fixture


def generate(core, synchronous=False, local=None):
    return candidates.generate_candidates(core.grid.crop(core.state.base) if local is None else local,
                                          core.state, core.route, core.kin,
                                          synchronous=synchronous)


def test_twelve_directions_fixed_slots_and_world_anchor():
    c=fixture(length=.01);c.state.base[:]=torch.tensor([1.,2.,math.pi/2])
    out=generate(c,True)
    assert out.pose.shape==(1,13,3) and out.mask.all()
    torch.testing.assert_close(out.pose[0,0],torch.tensor([1.,0.,0.],dtype=torch.float64))
    torch.testing.assert_close(out.pose[0,3],torch.tensor([0.,1.,math.pi/2],dtype=torch.float64),atol=1e-14,rtol=0)
    torch.testing.assert_close(out.pose[0,6,:2],torch.tensor([-1.,0.],dtype=torch.float64),atol=1e-14,rtol=0)
    assert torch.equal(out.pose[0,12],torch.zeros(3,dtype=torch.float64))
    assert out.inplace[0,12] and not out.inplace[0,:12].any()
    world=out.world_pose(c.state.base)
    torch.testing.assert_close(world[0,0],torch.tensor([1.,3.,math.pi/2],dtype=torch.float64))
    assert torch.equal(world[0,12],c.state.base[0])
    assert out.progress is None


@pytest.mark.parametrize('iy,ix,blocked',[(70,84,True),(71,84,False),
                                          (64,95,True),(64,96,True),(64,97,False),
                                          (64,63,True),(64,62,False)])
def test_closed_corridor_cell_edges_and_end(iy,ix,blocked):
    # Cell squares intersect y=.335 and x=1.6 by edges, not centres alone.
    c=fixture(length=.01);g=torch.zeros(1,128,128,2,dtype=torch.float64)
    g[0,iy,ix]=torch.tensor([1.,1.])
    out=generate(c,True,g)
    assert bool(out.mask[0,0]) is not blocked
    assert out.mask[0,12]
    assert out.info['n_gen'][0]==out.mask[0,:12].sum()
    assert out.info['discard_reason'][0,0]==int(blocked)


def test_unknown_height_and_observed_ground_do_not_discard():
    c=fixture(length=.01);g=torch.zeros(1,128,128,2,dtype=torch.float64)
    g[0,64,84,1]=2 # height without an observed flag is unknown
    a=generate(c,True,g);assert a.mask.all()
    g[0,64,84]=torch.tensor([1.,0.]);assert generate(c,True,g).mask.all()


def test_corridor_same_cell_coverage_as_local_collision():
    # Front 0.99m of the corridor equals a LocalCollision footprint centred x=.495.
    c=fixture(length=.01)
    for iy,ix in [(106,115),(107,115),(100,119),(100,120)]:
        g=Grid.empty(1,dtype=torch.float64);g.observed[0,iy,ix]=True;g.height[0,iy,ix]=1
        local=g.crop(c.state.base)
        blocked=not generate(c,True,local).mask[0,0]
        base=c.state.base.clone();base[:,0]=.495
        # Both overlapping footprints are tested by LocalCollision independently.
        caps=torch.empty(1,0,7,dtype=torch.float64)
        first=LocalCollision(g)(base,caps).base
        base[:,0]=1.105;second=LocalCollision(g)(base,caps).base
        assert blocked==bool(first|second)


def test_ik_failure_keeps_generated_candidate_and_only_inplace_diagnostic():
    c=fixture(length=.01);g=torch.ones(1,128,128,2,dtype=torch.float64)
    out=generate(c,False,g)
    assert not out.mask[0,:12].any() and out.mask[0,12]
    assert out.info['only_inplace'].item() and out.info['n_gen'].item()==0
    c.route.xyz+=100 # all IK targets are unreachable; candidate geometry still exists
    out=generate(c,False,torch.zeros_like(g))
    assert out.mask.all() and torch.equal(out.progress,torch.zeros(1,13,dtype=torch.float64))


@pytest.mark.parametrize('kind',['straight','bent','folded'])
def test_progress_reuses_first_continuous_prefix_real_ik(kind):
    from task7_sim.search import inplace_progress
    c=fixture(length=.11)
    start=c.route.xyz[:,0];quat=c.route.quat[:,:1]
    offsets={'straight':[[0,0,0],[.11,0,0]],
             'bent':[[0,0,0],[.05,0,0],[.05,.06,0]],
             'folded':[[0,0,0],[2.,0,0],[0,0,0]]}[kind]
    xyz=start[:,None]+torch.tensor(offsets,dtype=torch.float64)[None]
    c.route=Route(xyz,quat.expand(-1,len(offsets),-1));c.state.s[:]=.01
    out=generate(c)
    for j in [0,3,6,12]:
        state=State(out.world_pose(c.state.base)[:,j],c.state.q,c.state.s)
        want=inplace_progress(state,c.route,c.kin)
        torch.testing.assert_close(out.progress[:,j],want,atol=0,rtol=0)
    assert (out.progress>=.01).all() and (out.progress<=c.route.length[:,None]).all()
    if kind=='folded':assert (out.progress<c.route.length[:,None]).all()


def test_inplace_zero_progress_and_sync_has_no_sector_progress():
    c=fixture(length=.013);c.state.s[:]=c.route.length
    for sync in [False,True]:
        out=generate(c,sync)
        assert out.mask[0,12] and torch.equal(out.info['inplace_progress'],c.state.s)
        assert out.info['inplace_delta_s'].item()==0
        assert out.progress is None if sync else torch.equal(out.progress[:,12],c.state.s)
    assert generate(c,True).info['ik_targets']==1


def test_pure_repeat_and_inputs_rng_unchanged():
    c=fixture(length=.013);g=c.grid.crop(c.state.base)
    originals=[t.clone() for t in [g,c.state.base,c.state.q,c.state.s,c.route.xyz,c.route.quat]]
    rng=torch.random.get_rng_state().clone();a=generate(c,False,g);b=generate(c,False,g)
    for k in ['pose','mask','progress','inplace']:assert torch.equal(getattr(a,k),getattr(b,k))
    assert torch.equal(rng,torch.random.get_rng_state())
    for t,ref in zip([g,c.state.base,c.state.q,c.state.s,c.route.xyz,c.route.quat],originals):assert torch.equal(t,ref)


def test_occluded_truth_box_change_preserves_scan_grid_and_candidates():
    c=fixture(length=.013)
    # Wide front wall completely occludes the smaller box behind it.
    boxes=torch.tensor([[[1.,0.,.8,.05,2.,.8,1.,0.],
                         [2.,0.,.5,.1,.1,.5,1.,0.]]],dtype=torch.float64)
    mask=torch.ones(1,2,dtype=torch.bool);caps=torch.empty(1,0,7,dtype=torch.float64)
    scans=[];outs=[]
    for height in [.5,1.]:
        boxes[0,1,2]=height;boxes[0,1,5]=height
        depth=Panorama(boxes.clone(),mask)(c.state.base,caps)
        g=Grid.empty(1,dtype=torch.float64);g.update(depth.points,depth.valid,torch.zeros(1,dtype=torch.float64))
        scans.append(g.crop(c.state.base));outs.append(generate(c,True,scans[-1]))
    assert torch.equal(scans[0],scans[1])
    assert torch.equal(outs[0].pose,outs[1].pose) and torch.equal(outs[0].mask,outs[1].mask)
    assert torch.equal(outs[0].info['inplace_progress'],outs[1].info['inplace_progress'])


@pytest.mark.parametrize('sync',[False,True])
def test_gpu32_matches_cpu64_real_ik(sync):
    a=fixture(batch=2,length=.11);b=fixture(batch=2,device='cuda',dtype=torch.float32,length=.11)
    ga=a.grid.crop(a.state.base);ga[0,70,84]=torch.tensor([1.,1.]);ga[1,64,97]=torch.tensor([1.,1.])
    x=generate(a,sync,ga);y=generate(b,sync,ga.cuda().float())
    assert y.pose.device.type=='cuda' and y.pose.dtype==torch.float32
    assert torch.equal(y.mask.cpu(),x.mask) and torch.equal(y.inplace.cpu(),x.inplace)
    torch.testing.assert_close(y.pose.cpu().double(),x.pose,atol=1e-6,rtol=0)
    if not sync:torch.testing.assert_close(y.progress.cpu().double(),x.progress,atol=1e-6,rtol=0)
    torch.testing.assert_close(y.info['inplace_progress'].cpu().double(),x.info['inplace_progress'],atol=1e-6,rtol=0)


def corridor_sat_separation():
    """Independent full-corridor SAT signed separation in metres, CPU64.
    Positive means separated; negative means overlap on all axes.
    This helper sets only the precision-comparison domain, never collision rules.
    """
    axis=(torch.arange(128,dtype=torch.float64)+.5-64)*.05
    yy,xx=torch.meshgrid(axis,axis,indexing='ij')
    cells=torch.stack([xx.flatten(),yy.flatten()],-1)
    theta=torch.arange(12,dtype=torch.float64)*(math.pi/6)
    c,s=theta.cos()[:,None],theta.sin()[:,None]
    dx=cells[None,:,0]-.8*c;dy=cells[None,:,1]-.8*s
    projections=torch.stack([
        (c*dx+s*dy).abs()-.8-.025*(c.abs()+s.abs()),
        (-s*dx+c*dy).abs()-.335-.025*(c.abs()+s.abs()),
        dx.abs()-.8*c.abs()-.335*s.abs()-.025,
        dy.abs()-.8*s.abs()-.335*c.abs()-.025],-1)
    return projections.amax(-1)


def test_all_sector_cell_boundaries_gpu32_cpu64(record_property):
    cpu=candidates._corridor_coverage(torch.empty(0,dtype=torch.float64))
    gpu=candidates._corridor_coverage(torch.empty(0,device='cuda',dtype=torch.float32)).cpu()
    separation=corridor_sat_separation()
    strict=separation.abs()>1e-5
    mismatch=cpu!=gpu
    assert not (mismatch&strict).any(),torch.nonzero(mismatch&strict).tolist()
    record_property('boundary_band_cells',int((~strict).sum()))
    record_property('boundary_band_mismatches',int((mismatch&~strict).sum()))
    record_property('strict_cells',int(strict.sum()))
    print('SAT comparison',dict(strict_cells=int(strict.sum()),boundary_band_cells=int((~strict).sum()),
                                boundary_band_mismatches=int((mismatch&~strict).sum()),
                                max_abs_separation_mismatched=float(separation[mismatch].abs().max()) if mismatch.any() else 0))
