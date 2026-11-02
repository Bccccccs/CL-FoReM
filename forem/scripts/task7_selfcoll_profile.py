"""Private candidate adapter for controlled E256 comparison, not a production API."""
import json,time,hashlib
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry
from task7_sim.geometry import segment_distance,TruthCollision
from task7_sim.bench_full import scene
from task7_sim.core import Core,Candidate
P=Path('results/task7/t7.18.2-r1-20261021');torch.set_num_threads(2)
class OfflineRobot(RobotGeometry):
 def __call__(self,base,q):
  self.offline_q=q
  return super().__call__(base,q)
 def self_collision(self,base,caps,allowed=None,**kw):return super().self_collision(base,caps,allowed,q=self.offline_q)
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('src/task7_sim').glob('*.py')}
before=hashes()
rows=[]
for label,path in [('v1',Path('config/task7/robot_geometry_v1.json')),('candidate-v2',P/'robot_geometry_v2.json')]:
 robot=OfflineRobot(json.loads(path.read_text()));seed,_=scene(256,device='cuda',dtype=torch.float32)
 seed.capsules=robot;seed.collision=TruthCollision(seed.collision.boxes,seed.collision.mask,robot=robot)
 lat=[];counts=[]
 for k in range(7):
  c=Core(seed.state,seed.route,seed.grid,seed.kin,robot,seed.collision,synchronous=False,renderer=seed.renderer);target=c.state.base.clone();target[:,0]+=1
  c.begin(Candidate(target,torch.full_like(c.state.s,.03),torch.zeros_like(c.state.s,dtype=torch.bool)))
  torch.cuda.synchronize();start=time.perf_counter();tr=c.step(torch.zeros(256,3,device='cuda'));torch.cuda.synchronize();dt=time.perf_counter()-start
  if k>=2:lat.append(dt);counts.append(dict(attempted=int(tr.attempted.sum()),committed=int(tr.committed.sum()),self_failure=int((c.failure_kind==4).sum()),active=int(tr.active.sum())))
 rows.append(dict(label=label,E=256,device=str(c.state.q.device),samples_s=lat,p50_ms=float(np.median(lat)*1000),p95_ms=float(np.quantile(lat,.95)*1000),transitions_per_s=5*256/sum(lat),counts=counts))
 print(rows[-1],flush=True)
# Sensor envelope stays v1; legal-pose subset changes with collision protocol.
q=torch.tensor(np.load(P/'allowed-q.npz')['q'],device='cuda',dtype=torch.float64);inside=[];legal=[];self_counts=np.zeros((16,16),dtype=int);body_counts=np.zeros((8,8),dtype=int)
robot=OfflineRobot(json.loads((P/'robot_geometry_v2.json').read_text()))
for start in range(0,len(q),512):
 qt=q[start:start+512];base=torch.zeros(len(qt),3,device='cuda',dtype=qt.dtype);cap=robot(base,qt);origin=torch.tensor([0,0,.5],device='cuda',dtype=qt.dtype).expand(len(qt),1,3)
 self_counts+=robot.self_pair_contacts(base,qt).sum(0).cpu().numpy();body_counts+=robot.contacts(base,cap)[:,:8,8:].sum(0).cpu().numpy()
 inside.append((segment_distance(origin,origin,cap[...,:3],cap[...,3:6])<=cap[...,6]).any(-1).cpu().numpy())
 legal.append((~robot.self_collision(base,cap)&~(cap[...,[2,5]].amin(-1)-cap[...,6]<=0).any(-1)).cpu().numpy())
i=np.concatenate(inside);l=np.concatenate(legal);g1=dict(samples=len(q),origin=[0,0,.5],inside=int(i.sum()),legal=int(l.sum()),inside_legal=int((i&l).sum()),sensor_envelope='v1 unchanged, not self-only split capsules')
(P/'screen-counts.json').write_text(json.dumps(dict(samples=len(q),self_names=robot.data['self_names'],self_contacts=self_counts.tolist(),arm_body_contacts=body_counts.tolist()),indent=2))
(P/'profile-g1.json').write_text(json.dumps(dict(source_before=before,source_after=hashes(),profile=rows,g1=g1,limitation='Candidate rejects all fixture rows before their first commit; transition rates are not comparable useful-work throughput. No training.'),indent=2));print(g1)
