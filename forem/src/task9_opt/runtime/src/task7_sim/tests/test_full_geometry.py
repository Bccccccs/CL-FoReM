import torch
from task7_sim.bench_full import scene,candidates,script
from task7_sim.core import Candidate,rollout,feature_vector
from task7_sim.geometry import TruthCollision,load_map,pad_maps
from task7_sim.perception import LocalCollision,Panorama,Grid
from task7_sim.risk import sweep_metrics

def test_valid_initial_full_geometry_g1_and_manipulability():
    c,depth=scene();cap=c.capsules(c.state.base,c.state.q)
    assert not c.collision(c.state.base,cap).any.any()
    assert depth.origin_inside_self.shape==(1,)
    p,s,i=candidates(c,1);c.begin(Candidate(p[:,0],s[:,0],i[:,0]));c.step(script(c.observe()))
    assert 'manipulability' in c.attempts[0] and torch.isfinite(c.attempts[0]['manipulability']).all()

def test_full_arm_high_obstacle_and_self_collision_and_floor():
    c,_=scene();robot=c.capsules;cap=robot(c.state.base,c.state.q)
    # Actual link midpoint, deliberately colliding geometry; base flag independent.
    p=(cap[0,3,:3]+cap[0,3,3:6])/2
    box=torch.cat([p,torch.full((3,),.03,dtype=p.dtype),torch.tensor([1.,0],dtype=p.dtype)])[None,None]
    col=TruthCollision(box,torch.ones(1,1,dtype=torch.bool),robot=robot)(c.state.base,cap)
    assert col.arm.item()
    q=torch.tensor([[0,-1.,1.,-.5,1.,0]],dtype=c.state.q.dtype)
    # v1 wrist1/gripper overlap was a proxy false positive (SRC-0548).
    assert not robot.self_collision(c.state.base,robot(c.state.base,q)).item()
    moved=cap.clone();moved[:,:,2]-=2;moved[:,:,5]-=2
    # clone loses q provenance; this artificial floor probe changes only caps.
    assert TruthCollision(box,torch.ones(1,1,dtype=torch.bool),robot=robot)(c.state.base,moved,q=c.state.q).arm.item()

def test_full_geometry_information_boundary_and_automatic_features():
    c,_=scene();robot=c.capsules;dtype=c.state.q.dtype;base=c.state.base;caps=robot(base,c.state.q)
    boxes=torch.tensor([[[2,0,.8,.2,2,.8,1,0],[3,0,.8,.2,2,.8,1,0]]],dtype=dtype);alt=boxes.clone();alt[:,1,0]=4
    mask=torch.ones(1,2,dtype=torch.bool);grids=[]
    for b in [boxes,alt]:
        depth=Panorama(b,mask,robot=robot)(base,caps);g=Grid.empty(1,dtype=dtype);g.update(depth.points,depth.valid,c.state.s);grids.append(g)
    assert torch.equal(grids[0].observed,grids[1].observed) and torch.equal(grids[0].height,grids[1].height)
    poses,s,ip=candidates(c,3)
    values=[rollout(c.state,c.route,g,poses,s,ip,script,c.kin,robot,synchronous=False) for g in grids]
    assert torch.equal(values[0],values[1])
    # Truth still distinguishes the hidden boxes at a probe base pose.
    probe=base.clone();probe[:,0]=3
    assert TruthCollision(boxes,mask,robot=robot)(probe,robot(probe,c.state.q)).base.item()
    assert not TruthCollision(alt,mask,robot=robot)(probe,robot(probe,c.state.q)).base.item()

def test_full_rollout_cpu64_gpu32_and_independence():
    a,_=scene(2);b,_=scene(2,device='cuda',dtype=torch.float32);p,s,ip=candidates(a,3)
    fa=rollout(a.state,a.route,a.grid,p,s,ip,script,a.kin,a.capsules,synchronous=False)
    fb=rollout(b.state,b.route,b.grid,p.cuda().float(),s.cuda().float(),ip.cuda(),script,b.kin,b.capsules,synchronous=False)
    assert fa.shape==(2,3,19)
    torch.testing.assert_close(fb.cpu().double(),fa,atol=1e-4,rtol=0)
    rev=torch.tensor([2,0,1]);fc=rollout(a.state,a.route,a.grid,p[:,rev],s[:,rev],ip[:,rev],script,a.kin,a.capsules,synchronous=False)
    assert torch.equal(fa[:,rev],fc) and torch.equal(fa[0],fa[1])


def test_actual_elbow_only_high_obstacle_and_endpoint_safe_middle_collision():
    import json
    from task7_sim.bench_full import ARTIFACT
    c,_=scene();info=json.loads((ARTIFACT/'elbow_fixture.json').read_text());q=torch.tensor([info['q']],dtype=torch.float64)
    base=torch.zeros(1,3,dtype=q.dtype);cap=c.capsules(base,q);p=torch.tensor(info['point'],dtype=q.dtype)
    box=torch.cat([p,torch.full((3,),.03,dtype=p.dtype),torch.tensor([1.,0],dtype=p.dtype)])[None,None];mask=torch.ones(1,1,dtype=torch.bool)
    truth=TruthCollision(box,mask,robot=c.capsules);collision=truth(base,cap)
    # The v3 forearm/wrist2 conservative FP at this q is recorded in SRC-0548.
    assert not collision.base.item() and collision.arm.item() and collision.self_collision.item()
    tcp=c.kin.world_tcp(base,q)[0,:3,3]
    assert (tcp-p).abs().max()>.03 # tool point free, elbow/forearm collides
    for shift in [-1.5,1.5]:
        far=base.clone();far[:,0]=shift
        # Environment remains clear; the same q retains the v3 self flag.
        endpoint=truth(far,c.capsules(far,q))
        assert (endpoint.base.item(),endpoint.arm.item(),endpoint.self_collision.item())==(False,False,True)
    # Independently observed column at the elbow also hits LocalCollision.
    g=Grid.empty(1,dtype=q.dtype);ix,iy=torch.floor((p[:2]+5)/.05).long();g.observed[0,iy,ix]=True;g.height[0,iy,ix]=p[2]+.1
    local=LocalCollision(g,robot=c.capsules)(base,cap)
    assert local.arm.item() and not local.base.item()

def test_g1_intersection_is_reported_and_sensor_never_moved():
    import numpy as np
    from task7_sim.bench_full import ARTIFACT
    from task7_sim.geometry import segment_distance
    c,_=scene();q=torch.from_numpy(np.load(ARTIFACT/'allowed_pair_samples.npz')['q']);base=torch.zeros(len(q),3,dtype=q.dtype);caps=c.capsules(base,q)
    origin=torch.tensor([0,0,.5],dtype=q.dtype).expand(len(q),1,3)
    inside=(segment_distance(origin,origin,caps[...,:3],caps[...,3:6])<=caps[...,6]).any(-1)
    legal=~c.capsules.self_collision(base,caps)&~(caps[...,[2,5]].amin(-1)-caps[...,6]<=0).any(-1)
    idx=torch.where(inside&legal)[0][:1];assert len(idx)==1
    d=c.renderer(base[idx],caps[idx]);assert d.origin_inside_self.item() and not d.valid.any()
    assert torch.equal(d.points,torch.tensor([0,0,.5],dtype=q.dtype).expand_as(d.points))


def test_full_robot_failed_substep_atomic_rollback_and_single_failure():
    c,_=scene();box=torch.tensor([[[.53,0,.5,.005,.1,.5,1,0]]],dtype=torch.float64);mask=torch.ones(1,1,dtype=torch.bool)
    c.collision=TruthCollision(box,mask,robot=c.capsules);c.renderer=Panorama(box,mask,robot=c.capsules)
    start=c.state.clone();goal=c.state.base.clone();goal[:,0]=1
    c.begin(Candidate(goal,c.route.length.clone(),torch.zeros(1,dtype=torch.bool)))
    t=c.step(torch.tensor([[0,0,1]],dtype=torch.float64))
    assert t.attempted.item()==2 and t.committed.item()==1 and t.dt.item()==.05
    assert c.failures.item()==1 and c.reason.item()==3 and t.mask.item()==0
    assert torch.equal(c.state.base,torch.tensor([[.015,0,0]],dtype=torch.float64))
    assert c.state.s.item()==.0075 and c.render_count.item()==1
    assert torch.equal(c.state.q,c.attempts[0]['candidate_q']) and torch.equal(c.queue,t.raw_action)
    assert len(c.trace)==2 and c.trace[-1][1].sum()==1
    assert torch.equal(c.trace[-1][0].base,c.state.base) # failed attempt is absent
