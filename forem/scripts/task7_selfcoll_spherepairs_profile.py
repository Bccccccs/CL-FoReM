"""Production q interface, same E256 effective-work benchmark and G1 report."""
import json,time,hashlib
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry
from task7_sim.geometry import segment_distance,TruthCollision
from task7_sim.bench_full import scene
from task7_sim.core import Core,Candidate
P=Path('results/task7/t7.18.2-r3-20261021');torch.set_num_threads(2)
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('src/task7_sim').glob('*.py')}
before=hashes();rows=[];snapshots=[]
for label,path in [('v1',Path('config/task7/robot_geometry_v1.json')),('v4',P/'robot_geometry_v4.json')]:
 robot=RobotGeometry(json.loads(path.read_text()));seed,_=scene(256,device='cuda',dtype=torch.float32);seed.capsules=robot;seed.collision=TruthCollision(seed.collision.boxes,seed.collision.mask,robot=robot)
 lat=[];counts=[];snapshot=[]
 for k in range(9):
  c=Core(seed.state,seed.route,seed.grid,seed.kin,robot,seed.collision,synchronous=False,renderer=seed.renderer);target=c.state.base.clone();target[:,0]+=1;c.begin(Candidate(target,torch.full_like(c.state.s,.03),torch.zeros_like(c.state.s,dtype=torch.bool)))
  torch.cuda.synchronize();start=time.perf_counter();tr=c.step(torch.zeros(256,3,device='cuda'));torch.cuda.synchronize();dt=time.perf_counter()-start
  if k>=2:
   lat.append(dt);counts.append(dict(attempted=int(tr.attempted.sum()),committed=int(tr.committed.sum()),self_failure=int((c.failure_kind==4).sum()),active=int(tr.active.sum())))
   snapshot.append(dict(base=c.state.base.cpu().numpy(),q=c.state.q.cpu().numpy(),s=c.state.s.cpu().numpy(),reward=tr.reward.cpu().numpy(),reason=tr.reason.cpu().numpy(),committed=tr.committed.cpu().numpy()))
 row=dict(label=label,E=256,device=str(c.state.q.device),samples_s=lat,p50_ms=float(np.median(lat)*1000),p95_ms=float(np.quantile(lat,.95)*1000),transitions_per_s=7*256/sum(lat),counts=counts);rows.append(row);snapshots.append(snapshot);print(row,flush=True)
equal=all(np.array_equal(snapshots[0][k][key],snapshots[1][k][key]) for k in range(7) for key in snapshots[0][k]);print('BENCH_EFFECTIVE_WORK_EQUAL',equal,flush=True)
q=np.load(Path('results/task7/t7.18.2-r2-20261021/allowed-q.npz'))['q'];inside=[];legal=[];bodyinside=[];robot=RobotGeometry(json.loads((P/'robot_geometry_v4.json').read_text()));old=RobotGeometry(json.loads(Path('config/task7/robot_geometry_v1.json').read_text()))
for start in range(0,len(q),64):
 qt=torch.tensor(q[start:start+64],device='cuda',dtype=torch.float64);base=torch.zeros(len(qt),3,device=qt.device,dtype=qt.dtype);caps=robot(base,qt);assert torch.equal(caps,old(base,qt)) and torch.equal(robot.body_boxes(base),old.body_boxes(base))
 origin=torch.tensor([0,0,.5],device=qt.device,dtype=qt.dtype).expand(len(qt),1,3);inside.append((segment_distance(origin,origin,caps[...,:3],caps[...,3:6])<=caps[...,6]).any(-1).cpu().numpy())
 legal.append((~robot.self_collision(base,caps,q=qt)&~(caps[...,[2,5]].amin(-1)-caps[...,6]<=0).any(-1)).cpu().numpy())
i=np.concatenate(inside);l=np.concatenate(legal);g1=dict(samples=len(q),origin=[0,0,.5],inside=int(i.sum()),legal=int(l.sum()),inside_legal=int((i&l).sum()),sensor_envelope='v1 eight 0.02m padded capsules and body boxes, identical',inside_legal_indices=np.where(i&l)[0].tolist()[:20])
result=dict(source_before=before,source_after=hashes(),profile=rows,effective_work_equal=equal,g1=g1,limitation='7 bounded measured E256 calls after 2 warmups; external GPU1 task concurrent, no training-time promise');(P/'profile-g1.json').write_text(json.dumps(result,indent=2)+'\n');print(g1,flush=True)
