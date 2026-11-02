"""Same stored poses: mesh-referenced aggregate-pair audit; no policy replay."""
import argparse,json,time,csv
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry
from task7_sim.geometry import segment_distance
from task7_diag_mesh import load,reference
P=Path('results/task7/t7.18.2-r1-20261021');OLD=Path('results/task7/t7.18.1-r1-20261021')
p=argparse.ArgumentParser();p.add_argument('dataset');p.add_argument('--start',type=int,default=0);p.add_argument('--stop',type=int,default=1000000);a=p.parse_args();torch.set_num_threads(2)
cfg=json.loads((P/'robot_geometry_v2.json').read_text());new=RobotGeometry(cfg);v1=RobotGeometry(json.loads(Path('config/task7/robot_geometry_v1.json').read_text()));model,meshes,_=load();names=cfg['names']
x=np.load(OLD/('chain.npz' if a.dataset=='chain' else a.dataset+'/playback.npz'));print('keys',x.files,flush=True)
q=torch.tensor(x['q'],device='cuda',dtype=torch.float64);base=torch.zeros(len(q),3,device='cuda',dtype=q.dtype)
# World/global base does not affect self-collision; both sets recomputed at same base zero.
legacy=[];actual=[];B=512
for start in range(0,len(q),B):
 qt=q[start:start+B];bt=base[start:start+B];oldcaps=v1(bt,qt);ncaps=new(bt,qt);assert torch.equal(oldcaps,ncaps);assert torch.equal(v1.body_boxes(bt),new.body_boxes(bt))
 oldpairs=v1.contacts(bt,oldcaps);body=new.contacts(bt,ncaps)&~new.allowed.to('cuda')
 hits=new.self_pair_contacts(bt,qt)&~torch.tensor(cfg['self_allowed'],device='cuda')
 # Aggregate the nine fixed gripper pieces back into the diagnostic's original group.
 out=body.clone();out[:,:8,:8]=False
 for i in range(8):
  for j in range(i+1,8):
   ii=[i] if i<7 else list(range(7,16));jj=[j] if j<7 else list(range(7,16));out[:,i,j]=out[:,j,i]=hits[:,ii][:,:,jj].any((-1,-2))
 actual.append(out.cpu().numpy());legacy.append((oldpairs&~v1.allowed.to('cuda')).cpu().numpy())
newpairs=np.concatenate(actual);oldpairs=np.concatenate(legacy);np.savez_compressed(P/f'pairs-{a.dataset}.npz',new=newpairs,old=oldpairs)
# Reuse exact reference of identical q and original meshes from diagnosis.
cache={}
for f in OLD.glob(f'mesh-{a.dataset}-*.jsonl'):
 for line in f.read_text().splitlines():
  row=json.loads(line)
  for r in row['pairs']:cache[(row['pose'],r['pair'])]=r['reference']
file=P/f'reference-{a.dataset}.jsonl';done=set()
if file.exists():done={json.loads(line)['pose'] for line in file.read_text().splitlines()}
oldallow=np.array(v1.data['allowed']);started=time.monotonic()
with file.open('a') as f:
 for idx in range(a.start,min(a.stop,len(q))):
  if idx in done:continue
  qs=x['q'][idx].astype(float);H={n:model.transform(n,'base_footprint',qs[None])[0] for n in names};rows=[]
  for i in range(8):
   for j in range(i+1,16):
    # Evaluate all pairs inspected by either scheme, plus removed legacy Always pairs.
    newchecked=not cfg['allowed'][i][j] if j>=8 else not (np.array(cfg['self_allowed'])[([i] if i<7 else list(range(7,16)))][:,([j] if j<7 else list(range(7,16)))].all())
    if oldallow[i,j] and not newchecked:continue
    key=f'{i},{j}';r=cache.get((idx,key))
    if r is None:
     if not oldallow[i,j] and not oldpairs[idx,i,j]:r=dict(hit=False,method='v1_envelope_separation')
     else:r=reference(meshes[names[i]],meshes[names[j]],H[names[i]],H[names[j]])
    rows.append(dict(pair=key,new_hit=bool(newpairs[idx,i,j]),old_hit=bool(oldpairs[idx,i,j]),reference=r))
  f.write(json.dumps(dict(pose=idx,pairs=rows))+'\n');f.flush()
  if idx%25==0:print(a.dataset,idx,'/',len(q),'wall_s',time.monotonic()-started,flush=True)
print('done',a.dataset,a.start,a.stop,flush=True)
