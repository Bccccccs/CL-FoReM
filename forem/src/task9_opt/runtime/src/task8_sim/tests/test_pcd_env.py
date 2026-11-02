"""Task8.4 integration: real FK/PCD/Core, no truth mocks."""
import copy
import json
import os
from pathlib import Path
import time
import numpy as np
import pytest
import torch
from task7_sim.core import Candidate
from task7_sim.kinematics import Kinematics
from task7_sim.motion import Route, matrix_quat
from task7_sim.robot import ROOT
from task8_sim.assets import MapAsset, load_asset
from task8_sim.scene import VoxelScene

POOL=ROOT/'results/task8/t8-exec-20261026/cube-pool'
DEVICE=os.environ.get('TASK84_DEVICE','cpu')
DTYPE=torch.float32 if DEVICE.startswith('cuda') else torch.float64

def make_scene(key='empty',device=DEVICE,dtype=DTYPE):
    return VoxelScene.from_asset(load_asset(POOL/'manifest.json',key),device=device,dtype=dtype)

def factory(i,streams,device=DEVICE,dtype=DTYPE,key='empty'):
    from task8_sim.episode import PcdEpisode
    qdata=json.loads((ROOT/'results/task7/t7.14-r2-20261021-0000/fixture.json').read_text())['q']
    base=torch.zeros(1,3,device=device,dtype=dtype)
    base[:,0]=float(streams.initial.uniform(-.05,.05))
    q=torch.tensor(qdata,device=device,dtype=dtype)[None]
    tcp=Kinematics().world_tcp(base,q)
    xyz=tcp[:,None,:3,3].expand(-1,2,-1).clone();xyz[:,1,0]+=.0075
    route=Route(xyz,matrix_quat(tcp[:,:3,:3])[:,None].expand(-1,2,-1).clone())
    return PcdEpisode(base,q,route,make_scene(key,device,dtype),key,seed=123+i)

def test_explicit_profiles_and_no_old_pool_or_environment_restore():
    from task8_sim.env import PcdEpisodeEnv, profile_options
    assert profile_options('sync_v5')==dict(synchronous=True,failure_mode='cbl_continue',async_time_penalty=0.,episode_end_bootstrap=True,ik_avoid_collision=True)
    for name,sync in [('decision_sync_legacy',True),('decision_async_legacy',False)]:
        p=profile_options(name);assert p['synchronous']==sync and p['failure_mode']=='terminal' and p['async_time_penalty']==1 and not p['episode_end_bootstrap']
    with pytest.raises(ValueError,match='profile'):profile_options('implicit')
    with pytest.raises(ValueError,match='pool'):PcdEpisodeEnv(1,seed=1,pool=None,profile='sync_v5',device=DEVICE,dtype=DTYPE)
    e=PcdEpisodeEnv(1,seed=1,pool=POOL,profile='sync_v5',factory=factory,device=DEVICE,dtype=DTYPE)
    with pytest.raises(ValueError,match='restore'):e.load_state_dict({'format':'task7-lower-full-v1','env':object()})

def test_pcd_only_reset_nonzero_step_actual_q_fk_and_new_scan():
    from task8_sim.env import PcdEpisodeEnv
    e=PcdEpisodeEnv(1,seed=1,pool=POOL,profile='sync_v5',factory=factory,device=DEVICE,dtype=DTYPE)
    e.reset();c=e.core;before=c.state.clone();count=c.sensor_frames.clone()
    e.begin(Candidate(c.state.base.clone(),c.route.length.clone(),torch.ones_like(c.done)))
    raw=torch.tensor([[0.,0.,1.]],device=DEVICE,dtype=DTYPE)
    tr=e.step(raw).transition
    assert tr.committed.item()>0 and c.state.s.item()>0
    assert not torch.equal(c.state.q,before.q)
    assert torch.equal(c.state.q,c.attempts[-1]['candidate_q'])
    actual=c.kin.world_tcp(c.state.base,c.state.q)
    assert torch.isfinite(actual).all() and not torch.equal(actual,c.kin.world_tcp(before.base,before.q))
    assert c.sensor_frames.item()==count.item()+1 and c.grid.timestamp.item()>0
    assert tr.next_observation['grid'].shape==(1,128,128,3)
    assert c.state.q.device.type==torch.device(DEVICE).type
    assert not hasattr(c.collision,'boxes') and not hasattr(c.renderer,'boxes')
    assert e.versions['map_backend']=='pcd-voxel-v3' and e.versions['sensor_policy']=='ghost-v1'

def row_snapshot(e,i):
    c=e.core
    out={}
    for owner,names in [(c.state,('base','q','s')),(c.grid,('height','observed','timestamp')),(c,('time','attempt_time','failures','stalls','decisions','render_count','terminated','truncated','strict_success','committed_total','attempted_total','sensor_frames','origin_inside_self_frames','fully_occluded_frames','queue','visible_previous','done','finished')),(c.route,('xyz','quat','s','length'))]:
        for k in names:out[f'{id(owner)}:{k}']=getattr(owner,k)[i].clone()
    if hasattr(c,'candidate'):
        for owner,names in [(c.candidate,('pose','progress','inplace')),(c.start,('base','q','s')),(c,('segment_substeps','attempted_segment','failure_kind','arrived','first_failure_time','max_position','max_cbl','max_angle','cap','timeout','reason','first'))]:
            for k in names:out[f'segment:{k}']=getattr(owner,k)[i].clone()
    out['rng']=[copy.deepcopy(getattr(e.streams.for_env(i),k).bit_generator.state) for k in ('maps','initial','other')]
    out['id']=(e.map_ids[i],e.proposal_seeds[i],id(e.scenes.scenes[i]))
    out['counter']=(e.episode_count[i].clone(),{k:v[i].clone() for k,v in e.totals.items()})
    return out

def test_mask_reset_preserves_unselected_fields_and_rng_and_seed_reproducibility():
    from task8_sim.env import PcdEpisodeEnv
    mixed=lambda i,r:factory(i,r,key='empty' if i==0 else 'axis_aligned')
    a=PcdEpisodeEnv(2,seed=8,pool=POOL,profile='sync_v5',factory=mixed,device=DEVICE,dtype=DTYPE)
    b=PcdEpisodeEnv(2,seed=8,pool=POOL,profile='sync_v5',factory=mixed,device=DEVICE,dtype=DTYPE)
    a.reset();b.reset();assert torch.equal(a.core.state.base,b.core.state.base)
    a.begin(Candidate(a.core.state.base.clone(),a.core.route.length.clone(),torch.ones_like(a.core.done)))
    before=row_snapshot(a,1);a.core.terminated[0]=True;a.core.done[0]=True;a.reset(torch.tensor([True,False],device=DEVICE))
    after=row_snapshot(a,1)
    # Owner identity may change for route on reset; compare field order/value.
    for (ka,va),(kb,vb) in zip(before.items(),after.items()):
        if isinstance(va,torch.Tensor):assert torch.equal(va,vb),(ka,kb)
        elif ka=='counter':
            assert torch.equal(va[0],vb[0]);assert all(torch.equal(va[1][k],vb[1][k]) for k in va[1])
        else:assert va==vb,ka
    assert a.episode_count.tolist()==[2,1]

def test_single_scene_witness_64_and_three_collision_flags_and_no_domain_wall():
    from task8_sim.episode import SceneCollision
    from task8_sim.robot import GhostRobotGeometry
    scene=make_scene('axis_aligned');robot=GhostRobotGeometry()
    base=torch.tensor([[0.,0.,0.]],device=DEVICE,dtype=DTYPE).expand(64,-1).clone()
    q=torch.tensor(json.loads((ROOT/'results/task7/t7.14-r2-20261021-0000/fixture.json').read_text())['q'],device=DEVICE,dtype=DTYPE)[None].expand(64,-1).clone()
    flags=SceneCollision(scene,robot)(base,robot(base,q),q=q)
    assert flags.any.shape==(64,)
    empty=make_scene();caps=torch.tensor([[[0.,0.,.2,0.,0.,.2,.01]]],device=DEVICE,dtype=DTYPE)
    outside=base[:1].clone();outside[:,0]=5.2
    f=empty.collide(outside,caps,robot=None);assert not f.base.item() and not f.arm.item()
    floor=caps.clone();floor[...,2]=floor[...,5]=0
    assert empty.collide(outside,floor,robot=None).arm.item()
    # Real ghost robot self collision is still used, including folded zero q.
    zero=torch.tensor([[0.,0.,torch.pi,0.,0.,0.]],device=DEVICE,dtype=DTYPE);assert empty.collide(base[:1],robot(base[:1],zero),robot=robot,q=zero).self_collision.item()

def test_sampler_manifest_entry_deadline_and_cancel_without_proposals():
    from task8_sim.episode import PcdEpisodeSampler, SamplingIncomplete
    from task7_sim.episode import RandomStreams
    for pool in (POOL,POOL/'manifest.json'):
        s=PcdEpisodeSampler(pool,split='smoke',difficulty='random_cubes',device=DEVICE,dtype=DTYPE,kin=None,robot=None,profile='sync_v5')
        for kw in ({'deadline':time.monotonic()-1},{'cancel':lambda:True}):
            with pytest.raises(SamplingIncomplete):s.sample(RandomStreams(4,1).for_env(0),**kw)
        assert s.stats['proposals']==0

def test_planner_geometry_is_scene_height_and_conservative_top_not_sidecar():
    from task8_sim.routes import PcdTruthPlanner
    scene=make_scene('floating_slab');p=PcdTruthPlanner(scene)
    assert np.array_equal(p.height,scene.planning_height().cpu().double().numpy())
    assert not hasattr(p,'boxes')
    y,x=np.argwhere(p.height>0)[0];xy=-5+(np.array([x,y])+.5)*.05
    top=p.height[y,x]
    assert not p.clear(np.array([[xy[0]-.01,xy[1],top-.01],[xy[0]+.01,xy[1],top-.01]]))
    assert p.clear(np.array([[xy[0]-.01,xy[1],top],[xy[0]+.01,xy[1],top]]))

def test_real_step_crosses_data_domain_without_added_collision_or_termination():
    from task8_sim.env import PcdEpisodeEnv
    def at_edge(i,streams):
        e=factory(i,streams)
        shift=4.99-e.base[0,0];e.base[:,0]+=shift;e.route.xyz[:,:,0]+=shift
        return e
    env=PcdEpisodeEnv(1,seed=13,pool=POOL,profile='sync_v5',factory=at_edge,device=DEVICE,dtype=DTYPE)
    env.reset();c=env.core
    target=c.state.base.clone();target[:,0]+=.2
    env.begin(Candidate(target,c.route.length.clone(),torch.zeros_like(c.done)))
    out=env.step(c.state.base.new_tensor([[0.,0.,1.]]))
    assert out.transition.committed.item()>0 and c.state.base[0,0]>5
    assert out.info['out_of_map'].item() and not c.failure_kind.item()
    assert c.reason.item()==1  # inherited route end, no data-boundary result
    assert c.grid.timestamp.item()>0


def test_sampler_interrupts_in_progress_without_fallback_or_acceptance():
    from task8_sim.episode import PcdEpisodeSampler, SamplingIncomplete
    from task7_sim.episode import RandomStreams
    s=PcdEpisodeSampler(POOL,split='smoke',difficulty='random_cubes',device=DEVICE,dtype=DTYPE,kin=None,robot=None,profile='sync_v5')
    with pytest.raises(SamplingIncomplete,match='cancelled'):
        s.sample(RandomStreams(4,1).for_env(0),cancel=lambda:s.stats['proposals']>=1)
    assert s.stats['proposals']==1 and s.stats['accepted']==0
    assert len(s.entries)==1 and s.entries[0]['id']=='random_cubes'


@pytest.mark.skipif(not DEVICE.startswith('cuda'),reason='default cube integration allocated GPU0')
@pytest.mark.parametrize('batch',[1,2])
def test_default_random_cube_sample_step_and_scan_evidence(batch):
    from task8_sim.env import PcdEpisodeEnv
    started=time.monotonic();torch.cuda.reset_peak_memory_stats()
    env=PcdEpisodeEnv(batch,seed=20261026,pool=POOL,profile='sync_v5',difficulty='random_cubes',device=DEVICE,dtype=DTYPE)
    t=time.monotonic();env.reset(deadline=started+25);torch.cuda.synchronize();reset_s=time.monotonic()-t
    c=env.core;before=c.state.clone();frames=c.sensor_frames.clone()
    # Real nonzero TCP-progress action; raw speed zero avoids inventing a policy.
    target=c.state.base.clone();target[:,0]+=.2
    env.begin(Candidate(target,c.route.length.clone(),torch.zeros_like(c.done)))
    raw=c.state.base.new_zeros(batch,3);raw[:,0]=1
    t=time.monotonic();out=env.step(raw);torch.cuda.synchronize();step_s=time.monotonic()-t
    actual=c.kin.world_tcp(c.state.base,c.state.q)
    record=dict(batch=batch,device=str(c.state.q.device),dtype=str(c.state.q.dtype),reset_wall_s=reset_s,step_wall_s=step_s,
                elapsed_s=time.monotonic()-started,peak_memory_bytes=torch.cuda.max_memory_allocated(),map_ids=env.map_ids,
                seeds=env.proposal_seeds,provenance=env.scenes.provenance(),sampling=env.sampler.stats,sampling_timing=env.sampler.timing,
                base=c.state.base.tolist(),q=c.state.q.tolist(),actual_tcp=actual.tolist(),s=c.state.s.tolist(),
                committed=out.transition.committed.tolist(),failure_kind=c.failure_kind.tolist(),sensor_frames=c.sensor_frames.tolist(),
                observed_cells=c.grid.observed.sum((1,2)).tolist(),scan_timestamp=c.grid.timestamp.tolist())
    output=Path(os.environ.get('TASK8_TEST_ARTIFACT_ROOT',str(ROOT/'results/task8/t8-voxv3-20261026/integration')));output.mkdir(parents=True,exist_ok=True)
    (output/f'cube-default-batch{batch}.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(record))
    assert env.map_ids==['random_cubes']*batch
    assert out.transition.committed.gt(0).all() and (c.state.q!=before.q).any(-1).all()
    assert (c.sensor_frames>frames).all() and c.grid.timestamp.gt(0).all()
    assert torch.isfinite(actual).all() and actual.device.type=='cuda'

@pytest.mark.parametrize('kind',[2,3])
def test_pcd_real_step_reports_base_or_arm_collision_without_committing(kind):
    from task8_sim.env import PcdEpisodeEnv
    import hashlib
    env=PcdEpisodeEnv(1,seed=3,pool=POOL,profile='decision_sync_legacy',device=DEVICE,dtype=DTYPE,factory=factory)
    env.reset();c=env.core;before=c.state.clone()
    if kind==2:point=np.r_[c.state.base[0,:2].cpu().double().numpy(),.5]
    else:
        caps=env.robot(c.state.base,c.state.q)[0]
        ends=caps[:,:3].cpu().double().numpy()
        margin=np.maximum(np.abs(ends[:,0]-.0)-.495,np.abs(ends[:,1])-.335)
        point=ends[int(margin.argmax())]
    asset=MapAsset(f'collision-{kind}',np.asarray(point)[None],{},None,{'pcd':hashlib.sha256(np.asarray(point).tobytes()).hexdigest(),'sidecar':None})
    scene=VoxelScene.from_asset(asset,device=DEVICE,dtype=DTYPE)
    env.scenes.replace([0],[scene])
    env.begin(Candidate(c.state.base.clone(),c.route.length.clone(),torch.ones_like(c.done)))
    tr=env.step(c.state.base.new_tensor([[0.,0.,1.]])).transition
    assert c.failure_kind.item()==kind
    assert tr.committed.item()==0 and tr.attempted.item()==1
    for key in ('base','q','s'):assert torch.equal(getattr(c.state,key),getattr(before,key))


def test_real_core_profile_transition_matches_original_on_same_ghost_empty_scene():
    from task8_sim.env import PcdEpisodeEnv,profile_options
    from task7_sim.core import Core
    from task7_sim.geometry import TruthCollision
    from task7_sim.perception import Grid
    for profile in ('sync_v5','decision_sync_legacy','decision_async_legacy'):
        env=PcdEpisodeEnv(1,seed=17,pool=POOL,profile=profile,device=DEVICE,dtype=DTYPE,factory=factory)
        env.reset();c=env.core
        original=Core(c.state,c.route,c.grid,c.kin,c.capsules,TruthCollision(c.state.base.new_empty(1,0,8),torch.empty(1,0,device=DEVICE,dtype=torch.bool),robot=c.robot),renderer=c.renderer,**profile_options(profile))
        candidate=Candidate(c.state.base.clone(),c.route.length.clone(),torch.ones_like(c.done))
        c.begin(candidate);original.begin(candidate)
        raw=c.state.base.new_tensor([[0.,0.,1.]])
        a=env.step(raw).transition;b=original.step(raw)
        for key in ('reward','B','G','dt','attempted','committed','done','reason','mask','active'):
            assert torch.equal(getattr(a,key),getattr(b,key)),(profile,key)
        for key in a.next_observation:assert torch.equal(a.next_observation[key],b.next_observation[key]),(profile,key)


def test_completed_witness_batch_is_counted_when_external_cancel_fires():
    from task8_sim.episode import PcdEpisodeSampler,SamplingIncomplete
    from task7_sim.episode import RandomStreams
    interrupted=[False]
    class InstrumentedRealKinematics(Kinematics):
        def solve_world(self,base,target,prev,robot=None):
            result=super().solve_world(base,target,prev,robot=robot)
            if len(base)==64:interrupted[0]=True
            return result
    s=PcdEpisodeSampler(POOL,split='smoke',difficulty='random_cubes',device=DEVICE,dtype=DTYPE,kin=InstrumentedRealKinematics(),robot=None,profile='sync_v5')
    with pytest.raises(SamplingIncomplete):s.sample(RandomStreams(20261026,1).for_env(0),cancel=lambda:interrupted[0])
    assert s.stats['accepted']==0 and s.stats['witness_targets']==64
