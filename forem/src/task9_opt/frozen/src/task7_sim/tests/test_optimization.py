import importlib.util,sys
import torch
from task7_sim.core import Core,Candidate,rollout
from task7_sim.bench_full import scene,candidates,script,ARTIFACT

def reference():
    name='task7_sim._before_optimizations'
    spec=importlib.util.spec_from_file_location(name,ARTIFACT/'before_optimizations/core.py');m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def equal(a,b):
    if isinstance(a,torch.Tensor):assert torch.equal(a,b)
    elif isinstance(a,dict):
        assert a.keys()==b.keys()
        for k in a:equal(a[k],b[k])
    else:assert a==b

def test_observation_reuse_count():
    from test_core import fixture,candidate
    c=fixture();count=[0];original=c.observe
    def observe(*a,**k):count[0]+=1;return original(*a,**k)
    c.observe=observe;c.begin(candidate(c,x=0,cap=.03,inplace=True))
    while not c.done.all():
        obs=c.current_observation();c.step(torch.zeros(1,3,dtype=torch.float64))
    assert count[0]==3 # one initial, then after each of two actions

def test_same_input_before_after_cache_raw_queue_masks_and_state():
    old=reference();seed,_=scene();a=old.Core(seed.state,seed.route,seed.grid,seed.kin,seed.capsules,seed.collision,synchronous=False,renderer=seed.renderer)
    b=Core(seed.state,seed.route,seed.grid,seed.kin,seed.capsules,seed.collision,synchronous=False,renderer=seed.renderer)
    for segment in range(2):
        progress=torch.minimum(a.state.s+.03,a.route.length);ip=torch.ones(1,dtype=torch.bool)
        a.begin(old.Candidate(a.state.base.clone(),progress,ip));b.begin(Candidate(b.state.base.clone(),progress,ip))
        for raw in [torch.tensor([[0,.1,.1]],dtype=torch.float64),torch.tensor([[.2,-.1,0]],dtype=torch.float64)]:
            if a.done.all():break
            x=a.step(raw);y=b.step(raw)
            for name in x.__dataclass_fields__:equal(getattr(x,name),getattr(y,name))
            equal(a.state.base,b.state.base);equal(a.state.q,b.state.q);equal(a.state.s,b.state.s);equal(a.queue,b.queue)

def test_same_input_whole_rollout_automatic_features_cpu_and_gpu():
    old=reference()
    for device,dtype in [('cpu',torch.float64),('cuda',torch.float32)]:
        c,_=scene(2,device=device,dtype=dtype);p,s,ip=candidates(c,3)
        a=old.rollout(c.state,c.route,c.grid,p,s,ip,script,c.kin,c.capsules,synchronous=False)
        b=rollout(c.state,c.route,c.grid,p,s,ip,script,c.kin,c.capsules,synchronous=False)
        equal(a,b)


def test_raster_exact_progress_yaw_and_many_knots():
    old=reference()
    for device,dtype in [('cpu',torch.float64),('cuda',torch.float32)]:
        c,_=scene(3,device=device,dtype=dtype,nodes=25)
        a=old.Core(c.state,c.route,c.grid,c.kin,c.capsules,c.collision,synchronous=False,renderer=c.renderer)
        for core in [a,c]:
            core.begin(Candidate(core.state.base.clone(),core.route.length.clone(),torch.zeros(3,device=device,dtype=torch.bool)))
            core.state.s[:]=core.route.length*torch.tensor([0,.47,1],device=device,dtype=dtype)
            core.state.base[:,2]=torch.tensor([0,.53,-1.2],device=device,dtype=dtype)
        equal(a.observe(),c.observe())


def test_fixed_mount_exact_cpu64_gpu32():
    old=reference()
    for device,dtype in [('cpu',torch.float64),('cuda',torch.float32)]:
        c,_=scene(3,device=device,dtype=dtype)
        c.state.base[:]=torch.tensor([[1.2,-.3,.9],[-1.,2.,-2.1],[0,0,0]],device=device,dtype=dtype)
        a=old.Core(c.state,c.route,c.grid,c.kin,c.capsules,c.collision,synchronous=False,renderer=c.renderer)
        equal(a._body_transform(),c._body_transform())


def old_module(stem):
    name='task7_sim._before_'+stem
    spec=importlib.util.spec_from_file_location(name,ARTIFACT/('before_optimizations/'+stem+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def test_batched_local_columns_and_risk_exact():
    from task7_sim.perception import LocalCollision,Grid
    from task7_sim.risk import sweep_metrics
    before_risk=old_module('risk');before_local=old_module('perception')
    for device,dtype in [('cpu',torch.float64),('cuda',torch.float32)]:
        c,_=scene(3,device=device,dtype=dtype);g=Grid.empty(3,device=device,dtype=dtype);g.observed[:]=True
        g.height[:,100:103,120:125]=.8;g.height[1,95:98,100:103]=.1
        for mode in range(3):
            if mode==1:g.observed[:,100,100]=False
            if mode==2:g.observed[:,100,140]=False
            cap=c.capsules(c.state.base,c.state.q)
            a=before_local.LocalCollision(g,robot=c.capsules)(c.state.base,cap)
            b=LocalCollision(g,robot=c.capsules)(c.state.base,cap)
            for k in a.__dataclass_fields__:equal(getattr(a,k),getattr(b,k))
            state2=c.state.clone();state2.base[:]=torch.tensor([[.1,0,.1],[0,0,.4],[-.1,0,-.2]],device=device,dtype=dtype)
            trace=[(c.state,torch.ones(3,device=device,dtype=torch.bool)),(state2,torch.tensor([1,0,1],device=device,dtype=torch.bool))]
            equal(before_risk.sweep_metrics(trace,g,c.capsules),sweep_metrics(trace,g,c.capsules))


def test_fixed_kinematics_cache_exact_to_original_solver():
    from task7_sim.kinematics import Kinematics
    original=old_module('kinematics')
    for device,dtype in [('cpu',torch.float64),('cuda',torch.float32)]:
        a=original.Kinematics('config/task7/model.urdf');b=Kinematics();c,_=scene(2,device=device,dtype=dtype)
        target=a.world_tcp(c.state.base,c.state.q);equal(target,b.world_tcp(c.state.base,c.state.q))
        target[1,0,3]+=2
        x=a.solve_world(c.state.base,target,c.state.q);y=b.solve_world(c.state.base,target,c.state.q)
        for k in x.__dataclass_fields__:equal(getattr(x,k),getattr(y,k))


def test_sparse_raster_matches_original_on_cell_edges_and_reversed_segments():
    from task7_sim.motion import Route
    old=reference()
    for device,dtype in [('cpu',torch.float64),('cuda',torch.float32)]:
        c,_=scene(1,device=device,dtype=dtype)
        xyz=torch.tensor([[[-.025,-.025,1],[.025,-.025,1],[.025,.025,1],[-.025,.025,1],[-.025,-.025,1],[1.25,-.075,1],[-1.25,.075,1]]],device=device,dtype=dtype)
        quat=torch.tensor([0,0,0,1],device=device,dtype=dtype).expand(1,len(xyz[0]),4)
        c.route=Route(xyz,quat);c.begin(Candidate(c.state.base.clone(),c.route.length,torch.zeros(1,device=device,dtype=torch.bool)))
        a=old.Core(c.state,c.route,c.grid,c.kin,c.capsules,c.collision,synchronous=False,renderer=c.renderer);a.begin(Candidate(c.state.base.clone(),c.route.length,torch.zeros(1,device=device,dtype=torch.bool)))
        equal(a.observe(),c.observe())


def test_cached_observations_preserve_original_tensor_ownership():
    old=reference();seed,_=scene()
    a=old.Core(seed.state,seed.route,seed.grid,seed.kin,seed.capsules,seed.collision,synchronous=False,renderer=seed.renderer)
    b=Core(seed.state,seed.route,seed.grid,seed.kin,seed.capsules,seed.collision,synchronous=False,renderer=seed.renderer)
    for core in [a,b]:
        goal=core.state.base.clone();goal[:,0]+=1
        core.begin(Candidate(goal,torch.full_like(core.state.s,.03),torch.zeros_like(core.state.s,dtype=torch.bool)))
        tr=core.step(torch.zeros(1,3,dtype=torch.float64))
        for value in tr.next_observation.values():value.zero_()
        obs=core.observe() if core is a else core.current_observation()
        for value in obs.values():value.zero_() # downstream in-place preprocessing
    x=a.step(torch.zeros(1,3,dtype=torch.float64));y=b.step(torch.zeros(1,3,dtype=torch.float64))
    for name in x.__dataclass_fields__:equal(getattr(x,name),getattr(y,name))
