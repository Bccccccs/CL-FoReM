"""Targeted actual-request replay/acceptance/collision wiring check; never counted as formal."""
import sys,gzip,json,time
from pathlib import Path
import torch,numpy as np
sys.path[:0]=['/workspace/src','/work/src','/work/scripts']
from task9_lr.runtime import activate
activate()
from task7_sim.kinematics import Kinematics,LOW,HIGH,base_transform
from task8_sim.robot import GhostRobotGeometry
from task8_sim.primitive_scene import load_backend_scene
from task9_lr.diagnostics import observing
from diagnostic import Capture,collision
from backend import Bridge,BioKinematics
from run import dump,OUT,CONFIG

def main():
 torch.set_num_threads(2);torch.set_num_interop_threads(1)
 kin=Kinematics();assert np.array_equal(np.array(kin.model.limits),np.stack([LOW,HIGH],axis=-1))
 with gzip.open(OUT/'smoke-current-4718-random-000/requests.jsonl.gz','rt') as f:row=json.loads(next(f))
 tensor=lambda x:torch.tensor(x,device='cuda',dtype=torch.float32).unsqueeze(0)
 base,target,prev=map(tensor,[row['base_trial'],row['target_world'],row['q_seed']]);scene=load_backend_scene('primitive-obb-v1',row['pool'],row['map_id'],device='cuda',dtype=torch.float32);robot=GhostRobotGeometry();bridge=Bridge();result=[]
 try:
  for solver in [kin,BioKinematics(bridge,json.loads((CONFIG/'frozen-budget.json').read_text())['timeout_s'])]:
   capture=Capture()
   with observing(capture):r=solver.solve_world(base,target,prev,robot=robot)
   arm=torch.linalg.solve(base_transform(base)@kin.fixed('mount',prev),target)
   direct=kin._result(capture.q,arm,torch.tensor([-2],device='cuda'),torch.tensor([False],device='cuda'))
   assert torch.equal(r.accepted,direct.accepted)
   c=collision(scene,robot,base,r.q)
   result.append(dict(backend=type(solver).__name__,ik_accepted=bool(r.accepted[0]),collision=c,q=capture.q.cpu().tolist()))
  assert result[0]['ik_accepted']==row['ik_accepted'] and result[0]['collision']['any']==(row['base_collision'] or row['arm_collision'] or row['self_collision'])
 finally:bridge.close()
 dump(OUT/'actual-request-interface-check.json',dict(status='PASS',scope='one real request; both backends independent same seed/target; unified residual/limits/collision; baseline original acceptance/collision matches',results=result,counts='2 extra diagnostic calls, not calibration32, not formal evaluation'))
 print('PASS real-request interface and model limits',flush=True)
if __name__=='__main__':main()
