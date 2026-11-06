"""Offline v2 construction; original environmental envelopes remain byte-equivalent."""
import json,hashlib
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry,fit_capsule
from task7_diag_mesh import load,reference
from task7_sim.kinematics import LOW,HIGH
P=Path('results/task7/t7.18.2-r1-20261021');P.mkdir(parents=True,exist_ok=True)
old=json.loads(Path('config/task7/robot_geometry_v1.json').read_text());model,meshes,sources=load()
# load() preserves each original gripper link as one part, transformed into base frame.
import xml.etree.ElementTree as ET
root=ET.parse('config/task7/model.urdf').getroot()
grip=[l.get('name') for l in root.findall('link') if l.get('name').startswith('gripper_') and l.findall('collision')]
assert len(grip)==9
specs=[]
for c in old['capsules'][:7]:
 c=dict(c);c['radius_m']-=.02;specs.append(c)
assert len(meshes['gripper_base_link']['parts'])==9
for name,tr in zip(grip,meshes['gripper_base_link']['parts']):
 v=tr.reshape(-1,3);a,b,r=fit_capsule(v);u=b-a;t=np.clip((v-a)@u/(u@u),0,1) if u@u else np.zeros(len(v));d=np.linalg.norm(v-a-t[:,None]*u,axis=-1)
 specs.append(dict(link='gripper_base_link',name=name,a=a.tolist(),b=b.tolist(),radius_m=max(r,float(d.max())),max_vertex_distance_m=float(d.max()),vertex_count=len(v)))
names=[c.get('name',c['link']) for c in specs];adj=np.eye(16,dtype=bool)
# UR5 physical adjacency, fixed gripper mounting and internal gripper contact.
for i in range(6):adj[i,i+1]=adj[i+1,i]=True
adj[6,7:]=True;adj[7:,6]=True;adj[7:,7:]=True
q=np.random.default_rng(20261021).uniform(LOW,HIGH,(10000,6));np.savez_compressed(P/'allowed-q.npz',q=q)
new=dict(old);new.update(schema=2,geometry_version='selfcoll-v2-20261021',self_capsules=specs,self_names=names,self_allowed=adj.tolist(),self_allowed_reasons={f'{i},{j}':('fixed_gripper' if j>=7 and i>=6 else 'adjacent') for i in range(16) for j in range(i+1,16) if adj[i,j]},self_margin_m=0.,environment_geometry_version='v1-unchanged',samples=10000,seed=20261021)
# Candidate Always pairs are evaluated separately, before publication.
(P/'candidate-config.json').write_text(json.dumps(new,indent=2)+'\n')
(P/'fit-audit.json').write_text(json.dumps(dict(gripper_links=grip,sources=sources,vertex_enclosure=[dict(name=names[i],excess_m=c['max_vertex_distance_m']-c['radius_m']) for i,c in enumerate(specs)],q_sha256=hashlib.sha256(q.tobytes()).hexdigest()),indent=2))
print(names);print('v2 candidate written; original environment capsules/body unchanged')
