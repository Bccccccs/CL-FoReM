"""Same original poses, mesh-referenced pair confusion; no policy/training."""
import argparse,json,time
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry
from task7_diag_mesh import load,reference
P=Path('results/task7/t7.18.2-r2-20261021');OLD=Path('results/task7/t7.18.1-r1-20261021');R1=Path('results/task7/t7.18.2-r1-20261021')
p=argparse.ArgumentParser();p.add_argument('dataset');p.add_argument('--start',type=int,default=0);p.add_argument('--stop',type=int,default=1000000);a=p.parse_args();torch.set_num_threads(2)
cfg=json.loads((P/'robot_geometry_v3.json').read_text());new=RobotGeometry(cfg);v1=RobotGeometry(json.loads(Path('config/task7/robot_geometry_v1.json').read_text()));model,meshes,_=load();names=cfg['names'];N=len(cfg['self_names']);S=len(cfg['self_spheres'])
x=np.load(OLD/('chain.npz' if a.dataset=='chain' else a.dataset+'/playback.npz'));legacy=[];actual=[];raw=[]
for start in range(0,len(x['q']),32):
 qt=torch.tensor(x['q'][start:start+32],device='cuda',dtype=torch.float64);bt=torch.zeros(len(qt),3,device=qt.device,dtype=qt.dtype);oc=v1(bt,qt);nc=new(bt,qt);assert torch.equal(oc,nc) and torch.equal(v1.body_boxes(bt),new.body_boxes(bt))
 allpairs=new.self_contacts(bt,qt);allow=torch.zeros(N+8,N+8,device=qt.device,dtype=torch.bool);allow[:N,:N]=torch.tensor(cfg['self_allowed'],device=qt.device);allow[:N,N:]=torch.tensor(cfg['self_body_allowed'],device=qt.device);allow[N:,:N]=allow[:N,N:].T
 hit=allpairs&~allow;out=torch.zeros(len(qt),16,16,device=qt.device,dtype=torch.bool)
 groups=[[i] for i in range(7)]+[list(range(7,16))]+[[N+i] for i in range(8)]
 for i in range(8):
  for j in range(i+1,16):out[:,i,j]=out[:,j,i]=hit[:,groups[i]][:,:,groups[j]].any((-1,-2))
 # Any within-gripper collisions count too, so aggregation cannot hide alarms.
 internal=hit[:,7:16,7:16].any((-1,-2));assert not internal.any(),'fixed gripper model changed contact at a nonzero q'
 assert torch.equal(out.any((-1,-2)),new.self_collision(bt,nc,q=qt))
 actual.append(out.cpu().numpy());legacy.append((v1.contacts(bt,oc)&~v1.allowed.to(qt.device)).cpu().numpy())
newpairs=np.concatenate(actual);oldpairs=np.concatenate(legacy);np.savez_compressed(P/f'pairs-{a.dataset}.npz',new=newpairs,old=oldpairs)
cache={}
for line in (R1/f'reference-{a.dataset}.jsonl').read_text().splitlines():
 row=json.loads(line)
 for r in row['pairs']:cache[row['pose'],r['pair']]=r['reference']
# Keep every original r1 inspected pair: same denominator/reference across versions.
checks=sorted({key for idx,key in cache},key=lambda k:tuple(map(int,k.split(','))))
file=P/f'reference-{a.dataset}.jsonl';done=set()
if a.start==0:file.write_text('')
if file.exists():done={json.loads(l)['pose'] for l in file.read_text().splitlines()}
started=time.monotonic()
with file.open('a') as f:
 for idx in range(a.start,min(a.stop,len(x['q']))):
  if idx in done:continue
  rows=[]
  for key in checks:
   i,j=map(int,key.split(','));r=cache.get((idx,key))
   if r is None:
    qs=x['q'][idx].astype(float)[None];r=reference(meshes[names[i]],meshes[names[j]],model.transform(names[i],'base_footprint',qs)[0],model.transform(names[j],'base_footprint',qs)[0])
   rows.append(dict(pair=key,new_hit=bool(newpairs[idx,i,j]),old_hit=bool(oldpairs[idx,i,j]),reference=r))
  f.write(json.dumps(dict(pose=idx,pairs=rows))+'\n')
  if idx%500==0:f.flush();print(a.dataset,idx,'wall_s',time.monotonic()-started,flush=True)
print('DONE',a.dataset,len(x['q']),'alarms',newpairs.any((-1,-2)).sum(),flush=True)
