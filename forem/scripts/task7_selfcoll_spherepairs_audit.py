"""Same 10000 q and certified raw-mesh references; masked/unmasked pair counts."""
import json,time
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry
P=Path('results/task7/t7.18.2-r3-20261021');OLD=Path('results/task7/t7.18.2-r2-20261021');torch.set_num_threads(2)
cfg=json.loads((P/'robot_geometry_v4.json').read_text());robot=RobotGeometry(cfg);q=np.load(OLD/'allowed-q.npz')['q'];audit=json.loads((P/'zero-pair-audit.json').read_text());refrows=json.loads((OLD/'allowed-audit-final-v3.json').read_text())['rows'];pred=[];unmasked=[]
for start in range(0,len(q),32):
 qt=torch.tensor(q[start:start+32],device='cuda',dtype=torch.float64);b=torch.zeros(len(qt),3,device=qt.device,dtype=qt.dtype)
 hit=robot.self_contacts(b,qt,masked=True);pred.append(hit.cpu().numpy());raw=robot.self_contacts(b,qt);unmasked.append(raw.cpu().numpy())
 assert torch.equal(hit.any((-1,-2)),robot.self_collision(b,robot(b,qt),q=qt))
 if start%1024==0:print('audit',start,flush=True)
pred=np.concatenate(pred);unmasked=np.concatenate(unmasked);np.savez_compressed(P/'10000-pairs.npz',q=q,masked=pred,unmasked=unmasked)
def counts(h,t):return dict(TP=int((h&t).sum()),FP=int((h&~t).sum()),TN=int((~h&~t).sum()),FN=int((~h&t).sum()))
for row in audit['rows']:
 i,j=row['pair'];r=next(x for x in refrows if x['pair']==[i,j])
 if r['constant_relative_transform']:truth=np.full(len(q),bool(r['mesh_hit_count']),bool);source='allowed-audit-final-v3.json fixed raw mesh and 10000 equal relative transforms'
 else:
  src=np.load(OLD/r['certificates']);truth=src['hit'].astype(bool);source=r['certificates'];assert len(truth)==10000 and int(truth.sum())==r['mesh_hit_count']
 row.update(masked=counts(pred[:,i,j],truth),unmasked=counts(unmasked[:,i,j],truth),r2_whole_link_exemption=counts(np.zeros(len(q),bool),truth),raw_mesh_reference=source)
 print(row,flush=True)
(P/'10000-confusion.json').write_text(json.dumps(audit,indent=2)+'\n')
# Deterministic normal-pose probe, engineering grid, no claim of task frequency.
q=np.zeros((201,6));q[:,0]=np.linspace(-.1,.1,201);qq=np.zeros((201,6));qq[:,1]=np.linspace(-.1,.1,201);q=np.r_[q,qq];hits=[]
for start in range(0,len(q),32):
 qt=torch.tensor(q[start:start+32],device='cuda',dtype=torch.float64);b=torch.zeros(len(qt),3,device=qt.device,dtype=qt.dtype);hits.append(robot.self_contacts(b,qt,masked=True).cpu().numpy())
hits=np.concatenate(hits);np.savez_compressed(P/'near-zero-pairs.npz',q=q,hits=hits)
# The affected dynamic pairs' raw mesh is queried here rather than inferred.
from task7_selfcoll_multisphere_allowed import prepare,frame,check
_,model,meshes,_=prepare();names=cfg['self_names']+[r['link'] for r in cfg['body']];near=[]
for row in audit['rows']:
 i,j=row['pair'];a,b=names[i],names[j];HA=model.transform(frame(a,cfg['self_names']),'base_footprint',q);HB=model.transform(frame(b,cfg['self_names']),'base_footprint',q);truth=[]
 if i>=7 and j<16:
  t=check(meshes[a],meshes[b],HA[0],HB[0])['hit'];truth=[t]*len(q)
 else:
  for k in range(len(q)):truth.append(check(meshes[a],meshes[b],HA[k],HB[k])['hit'])
 truth=np.array(truth);r=dict(pair=[i,j],links=row['links'],samples=len(q),all=counts(hits[:,i,j],truth),shoulder_pan=counts(hits[:201,i,j],truth[:201]),shoulder_lift=counts(hits[201:,i,j],truth[201:]));near.append(r);print('near_zero',r,flush=True)
(P/'near-zero-confusion.json').write_text(json.dumps(dict(samples=len(q),radians=[-.1,.1],step_rad=.001,design='201 pan-only plus 201 lift-only, other joints zero; zero is repeated once per grid',rows=near),indent=2)+'\n')
