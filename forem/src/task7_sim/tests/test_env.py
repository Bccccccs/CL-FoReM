import importlib.util
from pathlib import Path
import json
import math
import pytest
import torch
from task7_sim.env import EpisodeEnv
from task7_sim.core import Core, Candidate
from task7_sim.episode import Episode
from task7_sim.bench_full import scene


def factory(i,streams,*,device='cpu',dtype=torch.float64):
    c,_=scene(device=device,dtype=dtype)
    shift=float(streams.initial.uniform(-.1,.1));c.state.base[:,0]+=shift;c.route.xyz[:,:,0]+=shift
    return Episode(c.state.base,c.state.q,c.route,c.collision.boxes[0])


def target(c,progress=.03):
    return Candidate(c.state.base.clone(),torch.full_like(c.state.s,progress),torch.ones_like(c.done))


def assert_transition_equal(x,y,ids=None):
    ids=slice(None) if ids is None else ids
    for name,value in vars(x).items():
        other=getattr(y,name)
        if isinstance(value,dict):
            assert all(torch.equal(t[ids],other[k][ids]) for k,t in value.items()),name
        else:assert torch.equal(value[ids],other[ids]),name


@pytest.mark.parametrize('device,dtype',[('cpu',torch.float64),('cuda',torch.float32)])
def test_single_batched_core_and_mask_reset_do_not_touch_other_rng_or_state(device,dtype):
    make=lambda i,r:factory(i,r,device=device,dtype=dtype)
    a=EpisodeEnv(2,make,seed=123);b=EpisodeEnv(2,make,seed=123)
    a.reset();b.reset()
    assert isinstance(a.core,Core) and a.core.state.q.shape==(2,6)
    assert not hasattr(a,'cores')
    a.core.stalls[0]=b.core.stalls[0]=4
    for env in (a,b):
        candidate=target(env.core);candidate.progress[:]=torch.tensor([.0075,.09],device=device,dtype=dtype)
        env.begin(candidate);env.step(torch.zeros(2,3,device=device,dtype=dtype))
    assert a.core.terminated.tolist()==[True,False]
    before=a.core.state.clone();grid=a.core.grid.snapshot()
    a.reset([0]);assert torch.equal(a.core.state.q[1],before.q[1])
    for name in ('observed','height','timestamp'):
        assert torch.equal(getattr(a.core.grid,name)[1],getattr(grid,name)[1])
    for name in ('maps','initial','other'):
        assert repr(getattr(a.streams.for_env(1),name).bit_generator.state)==repr(getattr(b.streams.for_env(1),name).bit_generator.state)
    candidate=target(a.core);a.begin(candidate,mask=torch.tensor([True,False],device=device))
    for _ in range(3):
        x=a.step(torch.zeros(2,3,device=device,dtype=dtype));y=b.step(torch.zeros(2,3,device=device,dtype=dtype))
        assert_transition_equal(x.transition,y.transition,torch.tensor([1],device=device))
        assert torch.equal(a.core.state.q[1],b.core.state.q[1])
        assert torch.equal(a.core.queue[1],b.core.queue[1])
        for name in ('observed','height','timestamp'):
            assert torch.equal(getattr(a.core.grid,name)[1],getattr(b.core.grid,name)[1])
        for name in ('time','failures','stalls','decisions','render_count','attempted_total','committed_total'):
            assert torch.equal(getattr(a.core,name)[1],getattr(b.core,name)[1])
    assert a.info()['episode_count'].tolist()==[2,1]


def test_reset_rejects_active_episode_and_invalid_action_is_atomic():
    env=EpisodeEnv(2,factory,seed=2);env.reset();env.begin(target(env.core))
    with pytest.raises(RuntimeError):env.reset([0])
    raw=torch.zeros(2,3,dtype=torch.float64);raw[1,1]=2
    with pytest.raises(ValueError):env.step(raw)
    assert env.core.time.eq(0).all() and not env.core.transitions


def test_same_seed_and_reset_sequence_reproduces_whole_batch():
    a=EpisodeEnv(2,factory,seed=43);b=EpisodeEnv(2,factory,seed=43)
    a.reset();b.reset()
    for selected in ([1],[0],[0],[1]):
        for env in (a,b):
            env.core.terminated[selected]=True;env.core.done[selected]=True
            env.reset(selected)
        for name in ('base','q','s'):assert torch.equal(getattr(a.core.state,name),getattr(b.core.state,name))
        assert torch.equal(a.core.route.xyz,b.core.route.xyz)
        assert torch.equal(a.core.grid.observed,b.core.grid.observed)
        assert torch.equal(a.core.grid.height,b.core.grid.height)


def test_core_transitions_elementwise_equal_to_before_snapshot():
    path=Path(__file__).resolve().parents[3]/'results/task7/t7.17-r1-20261021/core_before.py'
    spec=importlib.util.spec_from_file_location('task7_sim._episode_original_core',path);old=importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name]=old;spec.loader.exec_module(old)
    for device,dtype in [('cpu',torch.float64),('cuda',torch.float32)]:
        a,_=scene(3,device=device,dtype=dtype,core_class=old.Core);b,_=scene(3,device=device,dtype=dtype)
        for c in (a,b):c.begin(target(c))
        for _ in range(2):
            raw=torch.tensor([[0.,.2,.1],[.2,-.1,.05],[-.2,.1,-.05]],device=device,dtype=dtype)
            assert_transition_equal(a.step(raw),b.step(raw))
            for name in ('base','q','s'):assert torch.equal(getattr(a.state,name),getattr(b.state,name))


def test_reset_scan_and_g1_counter_semantics():
    env=EpisodeEnv(2,factory,seed=3);env.reset();c=env.core
    assert env.info()['sensor_frames'].tolist()==[1,1] and c.render_count.eq(0).all()
    env.begin(target(c));env.step(torch.zeros(2,3,dtype=torch.float64))
    assert env.info()['sensor_frames'].tolist()==[2,2] and c.render_count.eq(1).all()
    from types import SimpleNamespace
    d=SimpleNamespace(origin_inside_self=torch.tensor([True,True]),valid=torch.zeros(2,2,2,dtype=torch.bool))
    c.record_render(d,torch.tensor([True,False]))
    assert c.origin_inside_self_frames.tolist()==[1,0] and c.fully_occluded_frames.tolist()==[1,0]
    assert c.render_count.eq(1).all()


def boundary_cells(cpu_depth,gpu_depth):
    """E4 affected grid cells: actual arithmetic in each precision, <=1e-5m.
    Only cells touched by near-line valid landings can be excluded; no global
    error band, tolerance dilation or perception modification is allowed.
    """
    a=cpu_depth.points.cpu();b=gpu_depth.points.cpu();valid=cpu_depth.valid.cpu()|gpu_depth.valid.cpu()
    def near(p):
        t=(p[...,:2].double()+5).remainder(.05)
        return torch.minimum(t,.05-t).amin(-1)<=1e-5
    band=(near(a)|near(b))&valid
    affected=torch.zeros(len(a),200,200,dtype=torch.bool)
    for p,v in ((a,cpu_depth.valid.cpu()),(b,gpu_depth.valid.cpu())):
        ij=torch.floor((p[...,:2]+5)/.05).long()
        for i in range(len(a)):
            use=band[i]&v[i]&(ij[i]>=0).all(-1)&(ij[i]<200).all(-1)
            rows=ij[i][use];affected[i,rows[:,1],rows[:,0]]=True
    return affected,int(band.sum())


def test_wrapper_cpu64_gpu32(record_property):
    a=EpisodeEnv(2,factory,seed=17);b=EpisodeEnv(2,lambda i,r:factory(i,r,device='cuda',dtype=torch.float32),seed=17)
    check_boundary_observations(a,b,record_property)


def check_boundary_observations(a,b,record_property):
    a.reset();b.reset()
    affected=torch.zeros(2,200,200,dtype=torch.bool);band_points=0
    continuous_errors=[];continuous_max={}
    def close(x,y,label):
        x=x.cpu().double();y=y.cpu().double()
        continuous_max[label]=max(continuous_max.get(label,0.),float((x-y).abs().max()))
        # E6 (SRC-0902): near-singular joints amplify tiny TCP differences; joint fields
        # use task7.6's 1e-3 rad joint-solution criterion (normalized q: /pi), TCP stays 1e-4.
        atol={'observation.q':1e-3/math.pi,'state.q':1e-3}.get(label,1e-4)
        try:torch.testing.assert_close(y,x,atol=atol,rtol=0)
        except AssertionError as exc:continuous_errors.append(label+': '+str(exc))
    def compare_grids():
        nonlocal affected,band_points
        ca,cb=a.core,b.core
        da=ca.renderer(ca.state.base,ca.capsules(ca.state.base,ca.state.q));db=cb.renderer(cb.state.base,cb.capsules(cb.state.base,cb.state.q))
        hit,count=boundary_cells(da,db);affected|=hit;band_points+=count
        stable=~affected
        assert torch.equal(ca.grid.observed[stable],cb.grid.observed.cpu()[stable])
        qa=torch.round(ca.grid.height/.01).clamp(0,255).byte();qb=torch.round(cb.grid.height/.01).clamp(0,255).byte().cpu()
        assert torch.equal(qa[stable],qb[stable])
    compare_grids()
    for env in (a,b):env.begin(target(env.core))
    def compare_observation(x,y,base_cpu,base_gpu,band):
        # Check actual local network input as well as the global accumulator.
        axis=(torch.arange(128,dtype=torch.float64)+.5-64)*.05
        yy,xx=torch.meshgrid(axis,axis,indexing='ij')
        def indices(base):
            t=base.cpu();c,s=t[:,2].cos(),t[:,2].sin();xg=xx.to(t);yg=yy.to(t)
            wx=t[:,0,None,None]+c[:,None,None]*xg-s[:,None,None]*yg
            wy=t[:,1,None,None]+s[:,None,None]*xg+c[:,None,None]*yg
            ij=torch.floor((torch.stack([wx,wy],-1)+5)/.05).long()
            return ij,(ij>=0).all(-1)&(ij<200).all(-1)
        ia,va=indices(base_cpu);ib,vb=indices(base_gpu)
        rows=torch.arange(2)[:,None,None]
        hit_a=band[rows,ia[...,1].clamp(0,199),ia[...,0].clamp(0,199)]&va
        hit_b=band[rows,ib[...,1].clamp(0,199),ib[...,0].clamp(0,199)]&vb
        stable=~(hit_a|hit_b)
        ga=x['grid'].cpu();gb=y['grid'].cpu()
        assert torch.equal(ga[...,0][stable],gb[...,0][stable])
        assert torch.equal(torch.round(ga[...,1][stable]/.01).byte(),torch.round(gb[...,1][stable]/.01).byte())
        assert torch.equal(ga[...,2],gb[...,2])
        for key in x:
            if key!='grid':close(x[key],y[key],'observation.'+key)
    for _ in range(2):
        if a.core.done.all():
            assert b.core.done.all();break
        old_band=affected.clone();old_a=a.core.state.base.clone();old_b=b.core.state.base.clone()
        x=a.step(torch.zeros(2,3,dtype=torch.float64)).transition;y=b.step(torch.zeros(2,3,device='cuda')).transition
        compare_observation(x.observation,y.observation,old_a,old_b,old_band)
        compare_grids()
        compare_observation(x.next_observation,y.next_observation,a.core.state.base,b.core.state.base,affected)
        for name in ('reward','B','G','dt','mask'):
            close(getattr(x,name),getattr(y,name),'transition.'+name)
        for name in ('done','reason','active','attempted','committed'):assert torch.equal(getattr(x,name),getattr(y,name).cpu())
        for name in ('base','q','s'):close(getattr(a.core.state,name),getattr(b.core.state,name),'state.'+name)
    qa=torch.round(a.core.grid.height/.01).clamp(0,255).byte();qb=torch.round(b.core.grid.height/.01).clamp(0,255).byte().cpu()
    report=dict(band_points=band_points,affected_cells=int(affected.sum()),observed_differences=int((a.core.grid.observed!=b.core.grid.observed.cpu()).sum()),height_byte_differences=int((qa!=qb).sum()),stable_observed_differences=int(((a.core.grid.observed!=b.core.grid.observed.cpu())&~affected).sum()),stable_height_byte_differences=int(((qa!=qb)&~affected).sum()))
    report['continuous_max_absolute_difference']=continuous_max
    record_property('E4',json.dumps(report));print('E4',json.dumps(report))
    assert not continuous_errors,'\n'.join(continuous_errors)


def test_default_entry_uses_single_core_and_real_pool():
    env=EpisodeEnv(2,seed=4606,split='validation',device='cuda',dtype=torch.float32,synchronous=False)
    env.reset()
    assert isinstance(env.core,Core) and env.core.state.base.shape==(2,3)
    assert env.sampler.stats['accepted']==2
    assert all(x!='<fixture>' for x in env.map_ids)
    env.begin(target(env.core,0))
    result=env.step(torch.zeros(2,3,device='cuda')) if not env.core.done.all() else None
    assert env.core.grid.observed.shape==(2,200,200)


@pytest.mark.parametrize('device,dtype',[('cpu',torch.float64),('cuda',torch.float32)])
def test_ragged_route_and_map_padding_reset_preserves_unselected_segment(device,dtype):
    def make():
        count=[0,0]
        def fixture(i,streams):
            count[i]+=1
            c,_=scene(nodes=2 if count[i]==1 else 33,device=device,dtype=dtype)
            boxes=c.collision.boxes[0].clone()
            if count[i]>1:
                extra=boxes.new_tensor([[4.,4.,.1,.01,.01,.1,1.,0.]])
                boxes=torch.cat([boxes,extra])
            return Episode(c.state.base,c.state.q,c.route,boxes)
        return fixture
    a=EpisodeEnv(2,make(),seed=4);b=EpisodeEnv(2,make(),seed=4)
    for env in (a,b):
        env.reset();env.core.stalls[0]=4
        candidate=target(env.core,.09);candidate.progress[0]=.0075
        env.begin(candidate);env.step(torch.zeros(2,3,device=device,dtype=dtype))
    a.reset([0]);assert a.core.route.xyz.shape[1]==33
    assert a.core.collision.boxes.shape[1]>b.core.collision.boxes.shape[1]
    a.begin(target(a.core,.03),mask=torch.tensor([True,False],device=device))
    while not b.core.done.all():
        raw=torch.zeros(2,3,device=device,dtype=dtype)
        assert_transition_equal(a.step(raw).transition,b.step(raw).transition,torch.tensor([1],device=device))
    from task7_sim.core import feature_vector
    torch.testing.assert_close(feature_vector(a.core)[1],feature_vector(b.core)[1],atol=0,rtol=0)


def test_real_pool_boundary_observations_cpu64_gpu32(record_property):
    from task7_sim.episode import EpisodeSampler,RandomStreams
    from task7_sim.routes import batch_routes
    sampler=EpisodeSampler(split='validation',device='cpu',dtype=torch.float64)
    streams=RandomStreams(4617,2)
    episodes=[sampler.sample(streams.for_env(i)) for i in range(2)]
    def converted(i,rng):
        e=episodes[i]
        return Episode(e.base.cuda().float(),e.q.cuda().float(),batch_routes([e.route],device='cuda',dtype=torch.float32),e.boxes.cuda().float(),e.map_id)
    a=EpisodeEnv(2,lambda i,r:episodes[i],seed=17)
    b=EpisodeEnv(2,converted,seed=17)
    check_boundary_observations(a,b,record_property)


@pytest.mark.parametrize('device,dtype',[('cpu',torch.float64),('cuda',torch.float32)])
def test_synchronous_masked_reset_keeps_other_search_segment_exact(device,dtype):
    from task7_sim.motion import Route
    def fixture(i,streams):
        e=factory(i,streams,device=device,dtype=dtype)
        if i==0:
            xyz=e.route.xyz[:,:2].clone();xyz[:,1]=xyz[:,0];xyz[:,1,0]+=.0075
            e.route=Route(xyz,e.route.quat[:,:2])
        return e
    a=EpisodeEnv(2,fixture,seed=24,synchronous=True);b=EpisodeEnv(2,fixture,seed=24,synchronous=True)
    for env in (a,b):
        env.reset();c=env.core
        env.begin(Candidate(c.state.base.clone(),None,torch.ones_like(c.done)))
        env.step(torch.zeros(2,3,device=device,dtype=dtype))
    assert a.core.terminated.tolist()==[True,False]
    a.reset([0]);c=a.core
    a.begin(Candidate(c.state.base.clone(),None,torch.ones_like(c.done)),mask=torch.tensor([True,False],device=device))
    for _ in range(3):
        raw=torch.zeros(2,3,device=device,dtype=dtype)
        assert_transition_equal(a.step(raw).transition,b.step(raw).transition,torch.tensor([1],device=device))
        assert torch.equal(a.core.state.q[1],b.core.state.q[1])
