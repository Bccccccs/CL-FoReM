"""r3: preserve v3 spheres, restrict zero-pose exemptions to primitive pairs."""
import copy,hashlib,json
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry
from task7_sim.geometry import to_box
P=Path('results/task7/t7.18.2-r3-20261021');OLD=Path('results/task7/t7.18.2-r2-20261021')
cfg=json.loads((P/'robot_geometry.json.before').read_text());new=copy.deepcopy(cfg)
robot=RobotGeometry(cfg);base=torch.zeros(1,3,dtype=torch.float64);q=torch.zeros(1,6,dtype=torch.float64);sp=robot.self_spheres(base,q)[0];boxes=robot.body_boxes(base)[0]
groups=torch.tensor([s['group'] for s in cfg['self_spheres']]);rows=[];arm_pairs=[];body_pairs=[];n=len(cfg['self_names'])
for r in json.loads((OLD/'allowed-audit-final-v3.json').read_text())['rows']:
 if r['reason']!='zero_sphere_overlap':continue
 i,j=r['pair'];si=torch.where(groups==i)[0]
 if j<n:
  sj=torch.where(groups==j)[0];dist=(sp[si,None,:3]-sp[None,sj,:3]).norm(dim=-1);rad=sp[si,None,3]+sp[None,sj,3];aa,bb=torch.where(dist<rad);pairs=torch.stack([si[aa],sj[bb]],-1).tolist();arm_pairs.extend(pairs)
  new['self_allowed'][i][j]=new['self_allowed'][j][i]=False;kind='sphere_sphere'
  total=len(si)*len(sj)
 else:
  bj=j-n;dist=(to_box(sp[si,:3],boxes[bj]).abs()-boxes[bj,3:6]).clamp_min(0).norm(dim=-1);pairs=[[int(k),bj] for k in si[dist<sp[si,3]]];body_pairs.extend(pairs)
  new['self_body_allowed'][i][bj]=False;kind='sphere_body_box';total=len(si)
 new['self_allowed_reasons'][','.join(map(str,[i,j]))]='zero_pose_primitive_pairs_only'
 rows.append(dict(pair=[i,j],links=r['links'],primitive_kind=kind,total_primitive_pairs=total,zero_exempt_pairs=pairs,exempt_count=len(pairs),checked_count=total-len(pairs),reference_mesh_hits=r['mesh_hit_count'],reference_samples=10000))
new.update(schema=4,geometry_version='selfcoll-multisphere-v4-spherepairs-20261021',self_zero_sphere_pairs=arm_pairs,self_zero_sphere_body_pairs=body_pairs,zero_pair_policy='Strict zero-pose float64 distance < sum of sphere radii; body uses strict sphere-to-existing-box distance < radius. Only zero_sphere_overlap category; adjacency/fixed link exemptions unchanged.',zero_pair_audit=str(P/'zero-pair-audit.json'),historical_r2_link_audit=cfg['allowed_audit'],zero_pair_policy_source='forem/doc/SOURCES.md#src-0560',allowed_audit=str(P/'zero-pair-audit.json'))
# Legacy aggregate compatibility must not continue to exempt the base/upper pair.
new['allowed'][0][2]=new['allowed'][2][0]=False
new['allowed'][1][13]=new['allowed'][13][1]=False
for key in ['capsules','body','self_spheres']:assert new[key]==cfg[key]
(P/'robot_geometry_v4.json').write_text(json.dumps(new,indent=2)+'\n');(P/'zero-pair-audit.json').write_text(json.dumps(dict(rows=rows,sphere_pairs=len(arm_pairs),sphere_body_pairs=len(body_pairs),reference_q_sha256=hashlib.sha256((OLD/'allowed-q.npz').read_bytes()).hexdigest()),indent=2)+'\n')
print(json.dumps(rows,indent=2),flush=True)
