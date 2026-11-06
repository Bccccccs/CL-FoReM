"""10k envelope screening and mesh audit, with counterexample rejection."""
import json,time,hashlib
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry
from task7_diag_mesh import load,reference,components,dense
P=Path('results/task7/t7.18.2-r1-20261021');cfg=json.loads((P/'candidate-config.json').read_text());robot=RobotGeometry(cfg);model,meshes,_=load();q=np.load(P/'allowed-q.npz')['q'];names=cfg['self_names'];adj=np.eye(16,dtype=bool)
# Resolve URDF physical adjacency, including intervening massless/fixed links.
for child in names:
 cur=child
 while cur!='base_footprint' and cur in model.joints:
  parent=model.joints[cur][0]
  if parent in names:
   i=names.index(child);j=names.index(parent);adj[i,j]=adj[j,i]=True;break
  cur=parent
# Nine pieces replace one rigid gripper union: retain same-group and its original adjacent wrist3 exclusion.
adj[7:,7:]=True;adj[6,7:]=True;adj[7:,6]=True
cfg['self_allowed']=adj.tolist();cfg['self_allowed_reasons']={f'{i},{j}':('same_rigid_gripper' if i>=7 else 'adjacent_group' if i==6 and j>=7 else 'adjacent') for i in range(16) for j in range(i+1,16) if adj[i,j]}
robot=RobotGeometry(cfg);always=np.ones((16,16),bool);bodyalways=np.ones((8,8),bool)
for start in range(0,len(q),512):
 qt=torch.tensor(q[start:start+512],device='cuda');base=torch.zeros(len(qt),3,device='cuda',dtype=qt.dtype)
 always &= robot.self_pair_contacts(base,qt).all(0).cpu().numpy()
 bodyalways &=robot.contacts(base,robot(base,qt))[:,:8,8:].all(0).cpu().numpy()
# Link meshes kept in gripper_base coordinates for exact correspondence to fits.
gripper_union=meshes['gripper_base_link'];grip_parts=list(gripper_union['parts'])
for i,n in enumerate(names[7:]):
 tr=grip_parts[i];reps,bad=components(tr);meshes[n]=dict(tri=tr,points=dense(tr),reps=reps,parts=[tr],boundary_edges=bad)

def transform(name,qs):return model.transform('gripper_base_link' if name in names[7:] else name,'base_footprint',qs)
rows=[];allow=adj.copy();oldnames=cfg['names'];legacyallow=np.array(cfg['adjacent'])
# Adjacent/body-fixed contacts preserve their physical exclusions; no body-body test.
legacyallow[:8,:8]=np.eye(8,dtype=bool)
# This legacy block is not used for v2 arm-arm; exclude only here for compatibility.
for i in range(7):legacyallow[i,i+1]=legacyallow[i+1,i]=True
candidates=[('arm',i,j,names[i],names[j]) for i in range(16) for j in range(i+1,16) if always[i,j] and not adj[i,j]]
candidates += [('body',i,j+8,oldnames[i],oldnames[j+8]) for i in range(8) for j in range(8) if bodyalways[i,j] and not legacyallow[i,j+8]]
for typ,i,j,na,nb in candidates:
 HA=transform(na,q);HB=transform(nb,q);rel=np.linalg.inv(HA)@HB;err=float(np.max(np.abs(rel-rel[0])));fixed=err<1e-12
 # fixed verified over all samples, plus joint path structure recorded, not merely sample contact.
 tested=0;hits=0;counter=None;start=time.monotonic()
 indices=[0] if fixed else range(len(q))
 for k in indices:
  r=reference(gripper_union if typ=='body' and na=='gripper_base_link' else meshes[na],meshes[nb],HA[k],HB[k]);tested+=1;hits+=int(r['hit'])
  if not r['hit']:counter=dict(index=k,q=q[k].tolist(),reference=r);break
 keep=counter is None and (fixed or tested==len(q))
 if keep:
  if typ=='arm':allow[i,j]=allow[j,i]=True;cfg['self_allowed_reasons'][f'{i},{j}']='mesh_always_10000'
  else:legacyallow[i,j]=legacyallow[j,i]=True
 row=dict(kind=typ,pair=[i,j],links=[na,nb],envelope_hit_count=10000,mesh_queries=tested,mesh_hit_queries=hits,constant_relative_transform=fixed,max_relative_transform_element_difference=err,mesh_hit_count=10000 if keep else None,decision='allow' if keep else 'check',counterexample=counter,wall_s=time.monotonic()-start)
 rows.append(row);(P/'always-audit.json').write_text(json.dumps(rows,indent=2));print(json.dumps(row),flush=True)
# Upper-arm/top plate must never remain exempt regardless of envelope Always status.
i=oldnames.index('ur5_upper_arm_link');j=oldnames.index('top_plate_link');legacyallow[i,j]=legacyallow[j,i]=False
cfg['allowed']=legacyallow.tolist();cfg['self_allowed']=allow.tolist();cfg['self_adjacent']=adj.tolist();cfg['self_always']=always.tolist();cfg['allowed_reasons']={f'{i},{j}':('adjacent' if cfg['adjacent'][i][j] else 'mesh_always_10000') for i in range(16) for j in range(i+1,16) if legacyallow[i,j]};cfg['always_audit']='results/task7/t7.18.2-r1-20261021/always-audit.json'
cfg['v1_always']=cfg.pop('always',cfg.get('v1_always'));cfg['arm_body_always']=bodyalways.tolist()
cfg['fit']='v1 environment envelopes unchanged; self-only arm capsules without 0.02m; gripper each original URDF link in default-zero gripper frame, same fit_capsule'
(P/'robot_geometry_v2.json').write_text(json.dumps(cfg,indent=2)+'\n');print('DONE',len(candidates),'candidates')
