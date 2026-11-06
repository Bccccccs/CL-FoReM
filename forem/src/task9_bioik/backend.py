"""Isolated official BioIK process bridge; frozen FoReM terminal checks remain authoritative."""
import os,subprocess,time,select
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from task7_sim.kinematics import Kinematics,base_transform,metrics,fk
from task9_lr.diagnostics import hook

class Bridge:
 def __init__(self,log='/runlogs/bridge.log'):
  self.log=open(log,'a');self.proc=subprocess.Popen(['/work/build/devel/lib/task9_bioik_bridge/task9_bioik_bridge','/workspace/src/task9_lr/runtime/config/task7/model.urdf','/history/src/husky_ur5/config/ur5.srdf'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)
  self.calls=0
 def request(self,line,prefix):
  t=time.perf_counter();self.proc.stdin.write(line+'\n');self.proc.stdin.flush()
  while True:
   if not select.select([self.proc.stdout],[],[],30)[0]:raise TimeoutError('BioIK bridge response timeout')
   out=self.proc.stdout.readline()
   if not out:raise RuntimeError('BioIK bridge exited '+str(self.proc.poll()))
   if out.startswith(prefix+' '):return out.split()[1:],time.perf_counter()-t
 def fk(self,q):
  x,t=self.request('F '+' '.join(map(str,q)),'F');return np.array(list(map(float,x))).reshape(4,4),t
 def solve(self,target_tool,prev,timeout):
  quat=Rotation.from_matrix(target_tool[:3,:3]).as_quat()
  x,t=self.request('I '+' '.join(map(str,[*prev,timeout,*target_tool[:3,3],*quat])),'I');self.calls+=1
  success,code=int(x[0]),int(x[1]);wall,cpu=float(x[2]),float(x[3]);n=int(x[4]);q=np.array(list(map(float,x[5:])))
  if len(q)!=n:raise RuntimeError('bridge protocol q length')
  return q,dict(solver_success=bool(success),code=code,solver_wall_s=wall,solver_cpu_s=cpu,bridge_wall_s=t,timeout_s=timeout,random_seed=471812,threads=1,candidate_count=1,internal_candidates='not exposed by official plugin',rng='fixed plugin initialization seed; persistent call-order state')
 def close(self):
  if self.proc.poll() is None:
   self.proc.stdin.close()
   try:self.proc.wait(10)
   except subprocess.TimeoutExpired:self.proc.terminate();self.proc.wait(5)
  self.log.close()

class BioKinematics(Kinematics):
 def __init__(self,bridge,timeout):
  super().__init__();self.bridge=bridge;self.timeout=timeout;self.last_raw=None;self.last_meta=[]
 def solve_world(self,base,target,prev,robot=None):
  # Candidate generation/search has robot=None and keeps the frozen analytic+DLS path.
  # Only Core execution sends robot geometry, isolating IK from candidate selection.
  if robot is None:return super().solve_world(base,target,prev,robot=robot)
  return self.solve_execution(base,target,prev)
 def solve_execution(self,base,target,prev):
  shape=prev.shape[:-1];p=prev.reshape(-1,6);base=base.reshape(-1,3);world=target.reshape(-1,4,4)
  arm=torch.linalg.solve(base_transform(base)@self.fixed('mount',p),world)
  tool=arm@self.fixed('tool_tcp_inverse',p)
  # GPU->CPU and CPU->GPU copies are included in this caller's wall time.
  tt=tool.detach().double().cpu().numpy();pp=p.detach().double().cpu().numpy();out=[];valid=[];meta=[]
  for t,q in zip(tt,pp):
   if not np.isfinite(t).all() or not np.isfinite(q).all():
    out.append(q);valid.append(False);meta.append(dict(solver_success=False,code=None,reason='nonfinite input'));continue
   result,m=self.bridge.solve(t,q,self.timeout);finite=len(result)==6 and np.isfinite(result).all()
   out.append(result if finite else q);valid.append(finite);meta.append(m)
  q=torch.as_tensor(np.array(out),device=p.device,dtype=p.dtype)
  finite=torch.tensor(valid,device=p.device,dtype=torch.bool)
  r=self._result(q,arm,torch.full((len(q),),-2,device=p.device,dtype=torch.long),torch.zeros_like(finite),finite)
  self.last_raw=q.detach().clone();self.last_meta=meta
  hook('ik_pre_hold',self,q,r,p)
  r.q=torch.where(r.accepted[:,None],q,p);r.position,r.cbl,r.angle=metrics(fk(r.q)@self.fixed('tool_tcp',p),arm)
  for name in r.__dataclass_fields__:
   x=getattr(r,name);setattr(r,name,x.reshape(*shape,*x.shape[1:]))
  return r
