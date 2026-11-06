"""Bounded scripted-fixture timings; no training, policy evaluation or performance gate.
Run python3 -u -m task7_sim.benchmark --out results/task7/<run-id>.
The fixture uses an explicit empty capsule list: NOT full UR5 collision timing.
"""
import argparse,hashlib,json,os,platform,time
from pathlib import Path
import numpy as np
import torch
from .geometry import load_map,pad_maps,TruthCollision,segment_box_distance
from .kinematics import Kinematics,fk,metrics
from .motion import Route,matrix_quat,arc
from .perception import Panorama,Grid,LocalCollision
from .core import State,Candidate,Core,rollout

def stats(values):
    x=np.asarray(values);return dict(zip(['p50','p95','p99','max'],map(float,np.quantile(x,[.5,.95,.99,1]))))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    kin=Kinematics();dev='cuda';dtype=torch.float32
    rows=[]
    def sync():torch.cuda.synchronize()
    def measure(name,fn,repetitions=12,items=1):
        for _ in range(2):fn()
        sync();values=[]
        for _ in range(repetitions):
            sync();start=time.perf_counter();fn();sync();values.append(time.perf_counter()-start)
        total=sum(values)
        row=dict(name=name,repetitions=repetitions,items_per_call=items,wall_s=total,latency_ms=stats(np.asarray(values)*1000),items_per_s=repetitions*items/total)
        rows.append(row);print(json.dumps(row),flush=True)
    q=torch.tensor([[0,-1.,1.,-.5,1.,0]],device=dev,dtype=dtype)
    empty=lambda b,q:torch.empty(len(q),0,7,device=q.device,dtype=q.dtype)
    def setup(E=1):
        base=torch.zeros(E,3,device=dev,dtype=dtype);qs=q.expand(E,-1).clone();tcp=kin.world_tcp(base,qs)
        xyz=torch.stack([tcp[:,:3,3],tcp[:,:3,3]+torch.tensor([.4,0,0],device=dev,dtype=dtype)],1)
        quat=matrix_quat(tcp[:,:3,:3])[:,None].expand(-1,2,-1)
        return State(base,qs,torch.zeros(E,device=dev,dtype=dtype)),Route(xyz,quat),Grid.empty(E,device=dev,dtype=dtype)
    state,route,grid=setup()
    boxes,mask=pad_maps([load_map({'boxes':[[1.8,-1,0,.2,2,1.6,1,0]]},rotation_tolerance=1e-8)],device=dev,dtype=dtype)
    render=Panorama(boxes,mask);caps=empty(state.base,state.q)
    scan=render(state.base,caps);observed=grid.snapshot();observed.update(scan.points,scan.valid,state.s)
    offsets=torch.tensor([.01,.1],device=dev,dtype=dtype) # explicit fixture setting, not an approved M_r protocol
    def make_core():return Core(state,route,grid,kin,empty,TruthCollision(boxes,mask),synchronous=False,future_offsets=offsets,renderer=render)
    def envstep():
        c=make_core();c.begin(Candidate(state.base+torch.tensor([[1,0,0]],device=dev),torch.full_like(state.s,.4),torch.zeros_like(state.s,dtype=torch.bool)))
        return c.step(torch.zeros(1,3,device=dev))
    def policy(obs):return torch.zeros(len(obs['q']),3,device=dev,dtype=dtype)
    def all_unknown_metrics(c):return torch.tensor([[3.2,1,0]],device=dev,dtype=dtype).expand(len(c.state.s),-1)
    measure('fixture_reset_state_route_grid',setup,items=1)
    cpu_map=boxes.cpu()
    measure('host_to_gpu_map_tensor',lambda:cpu_map.to(dev),items=len(boxes[0]))
    measure('arc_batch_13',lambda:arc(state.base.expand(13,-1),torch.full((13,),.3,device=dev),torch.ones(13,device=dev),.05),items=13)
    for B in [1,13]:
        qs=q.expand(B,-1).clone();T=fk(qs)@kin.tool_tcp.to(qs)
        measure(f'ik_analytic_batch_{B}',lambda:kin.solve_tcp_in_arm(T,qs),items=B)
        far=T.clone();far[:,0,3]+=2
        measure(f'ik_dls64_batch_{B}',lambda:kin.dls(far,qs),repetitions=8,items=B)
    measure('panorama_360x90_no_robot_capsules',lambda:render(state.base,caps),items=32400)
    measure('grid_crop_128x128',lambda:observed.crop(state.base),items=16384)
    cap6=torch.tensor([[[0,.8,1,.4,.8,1,.04],[0,1,1,.4,1,1,.04],[0,1.2,1,.4,1.2,1,.04],[0,1.4,1,.4,1.4,1,.04],[0,1.6,1,.4,1.6,1,.04],[0,1.8,1,.4,1.8,1,.04]]],device=dev,dtype=dtype)
    truth=TruthCollision(boxes,mask);local=LocalCollision(observed)
    measure('truth_collision_six_fixture_capsules',lambda:truth(state.base,cap6))
    measure('local_collision_six_fixture_capsules',lambda:local(state.base,cap6))
    measure('scripted_action_transition_with_render_no_arm_geometry',envstep,repetitions=10)
    for E,K in [(1,1),(1,13),(2,3)]:
        st,rt,gr=setup(E);pose=st.base[:,None].expand(-1,K,-1).clone();s=torch.full((E,K),.03,device=dev,dtype=dtype);ip=torch.ones(E,K,device=dev,dtype=torch.bool)
        measure(f'rollout_E{E}_K{K}_4substeps_unknown_fixture',lambda:rollout(st,rt,gr,pose,s,ip,policy,kin,empty,synchronous=False,future_offsets=offsets,feature_metrics=all_unknown_metrics),repetitions=8,items=E*K)
    # Same inputs for inherited library thread settings; no algorithm/config change.
    original_threads=torch.get_num_threads()
    cpu_q=q.cpu().double().expand(128,-1).clone();cpu_target=fk(cpu_q)@kin.tool_tcp.to(cpu_q)
    for threads in [1,2,4]:
        torch.set_num_threads(threads)
        measure(f'cpu64_ik128_threads_{threads}',lambda:kin.solve_tcp_in_arm(cpu_target,cpu_q),repetitions=12,items=128)
    torch.set_num_threads(original_threads)
    # Measured precision comparison, kept separate from timing acceptance.
    generator=torch.Generator().manual_seed(42);qc=(torch.rand(128,6,generator=generator,dtype=torch.float64)-.5)*4
    target=fk(qc)@kin.tool_tcp.to(qc);ref=kin.solve_tcp_in_arm(target,qc+.001);gpu=kin.solve_tcp_in_arm(target.cuda().float(),(qc+.001).cuda().float())
    d,r,a=metrics((fk(gpu.q)@kin.tool_tcp.to(gpu.q)).cpu().double(),target)
    precision=dict(n=128,position_max_m=d.max().item(),cbl_max=r.max().item(),angle_max_rad=a.max().item(),branch_equal=int((ref.branch==gpu.branch.cpu()).sum()),accepted_cpu=int(ref.accepted.sum()),accepted_gpu=int(gpu.accepted.sum()))
    files=[*Path('src/task7_sim').glob('*.py'),Path('config/task7/model.urdf')]
    manifest=dict(torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(0),visible_devices=os.getenv('CUDA_VISIBLE_DEVICES'),python=platform.python_version(),pid=os.getpid(),affinity=sorted(os.sched_getaffinity(0)),threads=original_threads,interop_threads=torch.get_num_interop_threads(),hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},mount=kin.mount.tolist(),tool_tcp=kin.tool_tcp.tolist(),fixture_limitations=['no URDF capsule/body/allowed-pair assembly','explicit two future samples (.01,.1 m), not a protocol default','f_k risk values only analytically known all-unknown empty-capsule fixture','no candidate generation/reset sampling/learning/network','each GPU timing synchronized; CPU loop and launch overhead included','not full training throughput or schedule evidence'])
    (out/'timings.json').write_text(json.dumps(dict(manifest=manifest,precision=precision,measurements=rows),indent=2)+'\n')
    print('precision',json.dumps(precision),flush=True)

if __name__=='__main__':main()
