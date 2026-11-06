import sys,os,json,time,hashlib
from pathlib import Path
import numpy as np,torch
sys.path[:0]=['/workspace/src','/work/src']
from task9_lr.runtime import activate
activate()
from task7_sim.kinematics import Kinematics,LOW,HIGH,fk,metrics
from task8_sim.robot import GhostRobotGeometry
from backend import Bridge,BioKinematics

def stats(x):return dict(n=len(x),mean=float(np.mean(x)),p50=float(np.quantile(x,.5)),p95=float(np.quantile(x,.95)),max=float(np.max(x)))
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def main():
 torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.manual_seed(471812)
 rng=np.random.default_rng(91220261106);kin=Kinematics();robot=GhostRobotGeometry();bridge=Bridge()
 try:
  q=rng.uniform(LOW+.2,HIGH-.2,(32,6));seed=np.clip(q+rng.normal(0,.04,q.shape),LOW,HIGH);base=rng.uniform(-1,1,(32,3))
  Q=torch.tensor(q,device='cuda',dtype=torch.float32);P=torch.tensor(seed,device='cuda',dtype=torch.float32);B=torch.tensor(base,device='cuda',dtype=torch.float32)
  target=kin.world_tcp(B,Q);target[-4:,:3,3]+=torch.tensor([2.,0,0],device='cuda')
  dump('/output/calibration-inputs.json',dict(engineering_calibration=True,independent_of_diagnostic=True,seed=91220261106,q=q.tolist(),q_seed=seed.tolist(),base=base.tolist(),target_world=target.cpu().tolist(),purpose='24+4 reachable random and 4 shifted targets; FK/coordinates/limits/residual acceptance and local budget',dtype='float32'))
  fk_errors=[];bridge_overhead=[]
  for row in q:
   f,w=bridge.fk(row);t=fk(torch.tensor(row[None],dtype=torch.float64)).numpy()[0];fk_errors.append(float(np.abs(f-t).max()));bridge_overhead.append(w)
  assert max(fk_errors)<1e-7,('FK mismatch',max(fk_errors))
  # Warm-up separated and retained; does not enter warmed p95 budget estimate.
  warm=time.perf_counter();kin.dls_cuda_graph=True;kin.solve_world(B[-1:],target[-1:],P[-1:],robot=robot);torch.cuda.synchronize();warm=time.perf_counter()-warm
  times=[];baseline=[]
  for i in range(32):
   torch.cuda.synchronize();t=time.perf_counter();r=kin.solve_world(B[i:i+1],target[i:i+1],P[i:i+1],robot=robot);torch.cuda.synchronize();times.append(time.perf_counter()-t);baseline.append(bool(r.accepted[0]))
  timeout=float(np.ceil(max(np.quantile(times,.95),np.quantile(bridge_overhead,.95))/.001)*.001)
  budget=dict(timeout_s=timeout,formula='ceil(max(calibration32 warmed current IK p95, FK stdio roundtrip p95)/0.001)*0.001',granularity_s=.001,action_period_s=.1,baseline_wall_s=stats(times),bridge_roundtrip_wall_s=stats(bridge_overhead),warmup_wall_s=warm,fk_max_element_error=max(fk_errors),main_frozen_before_diagnostic=True,baseline_budget_enforced=False,comparison='actual accuracy-cost; existing algorithm not truncated',plugin=dict(mode='bio2_memetic',threads=1,random_seed=471812,approximate=True,soft_goals={'MinimalDisplacement':1,'AvoidJointLimits':1},collision_callback=False,internal_candidates='not exposed',final_collision='unchanged FoReM geometry'),calibration_frozen_epoch=time.time())
  dump('/work/config/frozen-budget.json',budget)
  bio=BioKinematics(bridge,timeout);rows=[]
  for i in range(32):
   torch.cuda.synchronize();start=time.perf_counter();r=bio.solve_execution(B[i:i+1],target[i:i+1],P[i:i+1]);torch.cuda.synchronize();wall=time.perf_counter()-start
   raw=bio.last_raw;arm=torch.linalg.solve(__import__('task7_sim.kinematics',fromlist=['base_transform']).base_transform(B[i:i+1])@kin.fixed('mount',P),target[i:i+1]);rr=kin._result(raw,arm,torch.tensor([-2],device='cuda'),torch.tensor([False],device='cuda'))
   assert torch.equal(rr.accepted,r.accepted),'unified acceptance mismatch'
   assert torch.all(r.q>=torch.tensor(LOW,device='cuda')-1e-6) and torch.all(r.q<=torch.tensor(HIGH,device='cuda')+1e-6)
   rows.append(dict(case=i,baseline_accepted=baseline[i],bio_accepted=bool(r.accepted[0]),position_m=float(rr.position[0]),cbl=float(rr.cbl[0]),angle_rad=float(rr.angle[0]),q_raw=raw.cpu().tolist(),meta=bio.last_meta,wall_s=wall))
  # Nonfinite must not be accepted; no target/seed substitution can turn it into success.
  invalid=target[:1].clone();invalid[0,0,3]=float('nan');r=bio.solve_execution(B[:1],invalid,P[:1]);assert not bool(r.accepted[0])
  dump('/output/calibration.json',dict(status='PASS',budget=budget,rows=rows,nonfinite_rejected=True,policy_device='not_loaded',torch_version=torch.__version__,gpu_name=torch.cuda.get_device_name(),gpu_uuid=os.environ.get('NVIDIA_VISIBLE_DEVICES'),cpuset=sorted(os.sched_getaffinity(0)),threads=torch.get_num_threads(),interop=torch.get_num_interop_threads()))
  print(json.dumps(dict(status='PASS',timeout_s=timeout,baseline=sum(baseline),bio=sum(r['bio_accepted'] for r in rows),fk_max=max(fk_errors))),flush=True)
 finally:bridge.close()
if __name__=='__main__':main()
