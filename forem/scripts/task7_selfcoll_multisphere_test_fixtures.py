"""Raw mesh evidence before changing v1-dependent test expectations."""
import json
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry
from task7_sim.bench_full import ARTIFACT
from task7_diag_mesh import load,reference,exact_surface,inside
def solids(tr):
 v,inv=np.unique(np.round(tr.reshape(-1,3),10),axis=0,return_inverse=True);ix=inv.reshape(-1,3);parent=np.arange(len(v))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for a,b,c in ix:
  a=find(a);parent[find(b)]=a;parent[find(c)]=a
 labels=np.array([find(i) for i in ix[:,0]])
 return [tr[labels==label] for label in np.unique(labels)]
P=Path('results/task7/t7.18.2-r2-20261021');model,meshes,_=load();old=RobotGeometry(json.loads(Path('config/task7/robot_geometry_v1.json').read_text()));new=RobotGeometry();names=old.names;rows=[]
for label,qs in [('old_self_fixture',[0,-1.,1.,-.5,1.,0]),('elbow_fixture',json.loads((ARTIFACT/'elbow_fixture.json').read_text())['q'])]:
 q=torch.tensor([qs],dtype=torch.float64);base=torch.zeros(1,3,dtype=q.dtype);v1=old.contacts(base,old(base,q))[0]&~old.allowed;v3=new.self_contacts(base,q)[0];allow=torch.tensor(new.data['self_allowed']);bodyallow=torch.tensor(new.data['self_body_allowed']);N=len(allow);v3[:N,:N]&=~allow;v3[:N,N:]&=~bodyallow;allpairs=[];groups=[[i] for i in range(7)]+[list(range(7,16))]+[[N+i] for i in range(8)]
 for i in range(8):
  for j in range(i+1,16):
   hit=bool(v3[groups[i]][:,groups[j]].any())
   if not v1[i,j] and not hit:continue
   r=reference(meshes[names[i]],meshes[names[j]],model.transform(names[i],'base_footprint',q.numpy())[0],model.transform(names[j],'base_footprint',q.numpy())[0]);
   if r['hit'] and r['method']=='containment':
    HA=model.transform(names[i],'base_footprint',q.numpy())[0];HB=model.transform(names[j],'base_footprint',q.numpy())[0];A=meshes[names[i]]['tri']@HA[:3,:3].T+HA[:3,3];B=meshes[names[j]]['tri']@HB[:3,:3].T+HB[:3,3];distance=exact_surface(A,B,r['sample_upper']);SA,SB=solids(A),solids(B);component_hit=any(inside(t[0,0],other) for t in SA for other in SB) or any(inside(t[0,0],other) for t in SB for other in SA);r.update(hit=bool(component_hit or distance<=1e-7),distance=distance,component_reference_hit=component_hit,method='independent_component_union_and_exact_triangle_audit')
   allpairs.append(dict(pair=[i,j],links=[names[i],names[j]],v1_hit=bool(v1[i,j]),v3_hit=hit,reference=r))
 row=dict(label=label,q=qs,old_hit=bool(old.self_collision(base,old(base,q))),new_hit=bool(new.self_collision(base,new(base,q))),pairs=allpairs);rows.append(row);print(json.dumps(row),flush=True)
(P/'test-expectation-evidence.json').write_text(json.dumps(rows,indent=2)+'\n')
