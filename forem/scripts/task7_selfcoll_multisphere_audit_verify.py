"""Independent spot reference and fixed-path checks of all allowed raw pairs."""
import json,time
from pathlib import Path
import numpy as np
from task7_selfcoll_multisphere_allowed import prepare,frame,check,P
cfg,model,meshes,_=prepare();q=np.load(P/'allowed-q.npz')['q'];path=P/'allowed-audit-final-v3.json';data=json.loads(path.read_text());names=cfg['self_names'];allnames=names+[x['link'] for x in cfg['body']];rows=[]
def moving_path(tip):
 out=[]
 while tip!='base_footprint':
  parent,H,axis,name,kind=model.joints[tip]
  if name in model.indices:out.append(name)
  tip=parent
 return out[::-1]
for row in data['rows']:
 assert row['complete'] and row['samples']==10000
 i,j=row['pair'];na,nb=allnames[i],allnames[j];pa=moving_path(frame(na,names));pb=moving_path(frame(nb,names));fixed=pa==pb
 assert fixed==row['constant_relative_transform']
 if fixed:
  r=check(meshes[na],meshes[nb],np.eye(4),(np.linalg.inv(model.transform(frame(na,names),'base_footprint',q[:1]))@model.transform(frame(nb,names),'base_footprint',q[:1]))[0]);assert int(r['hit'])*10000==row['mesh_hit_count'];checked=1
 else:
  f=np.load(P/row['certificates']);idx=np.unique(np.r_[np.linspace(0,9999,64).astype(int),np.where(f['hit']==1)[0][:8]])
  for k in idx:
   r=check(meshes[na],meshes[nb],np.eye(4),f['relative'][k]);assert r['hit']==bool(f['hit'][k]),(row['pair'],int(k),r,int(f['hit'][k]))
  assert len(f['hit'])==10000 and not (f['hit']<0).any() and f['hit'].sum()==row['mesh_hit_count'];checked=len(idx)
 item=dict(pair=row['pair'],links=row['links'],active_joint_path_a=pa,active_joint_path_b=pb,structural_fixed=fixed,independent_full_reference_queries=int(checked),mesh_hits_of_10000=row['mesh_hit_count']);rows.append(item);print(item,flush=True)
(P/'allowed-independent-verification.json').write_text(json.dumps(rows,indent=2)+'\n')
