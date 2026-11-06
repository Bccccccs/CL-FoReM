"""Mesh-referenced adjacency/fixed/zero-overlap table and 10000-q pair audit."""
import json,time,argparse,hashlib
from pathlib import Path
import numpy as np
from task7_diag_mesh import load,reference,components,dense,inside,exact_surface
P=Path('results/task7/t7.18.2-r2-20261021');AP=P/'allowed-audit.json'

def prepare():
 cfg=json.loads((P/'candidate-config.json').read_text());model,meshes,sources=load();names=cfg['self_names'];parts=list(meshes['gripper_base_link']['parts'])
 for name,tr in zip(names[7:],parts):
  reps,bad=components(tr);meshes[name]=dict(tri=tr,points=dense(tr),reps=reps,parts=[tr],boundary_edges=bad)
 return cfg,model,meshes,sources

def frame(n,names):return 'gripper_base_link' if n in names[7:] else n

def check(a,b,ha,hb):
 r=reference(a,b,ha,hb)
 # Independently resolve the prior component-union containment ambiguity by
 # exact triangle distance before trusting a purely contained classification.
 if r['hit'] and r['method']=='containment':
  A=a['tri']@ha[:3,:3].T+ha[:3,3];B=b['tri']@hb[:3,:3].T+hb[:3,3]
  # An interior representative in either *individual* raw part confirms solid
  # containment. Exact surface handles remaining boundary ambiguity.
  hit=any(inside(tr[0,0],s) for tr in [A] for s in [B]) or any(inside(tr[0,0],s) for tr in [B] for s in [A])
  if not hit:
   d=exact_surface(A,B,r['sample_upper']);r.update(hit=d<=1e-7,distance=d,method='containment_checked_by_exact_surface')
 return r

def init():
 import torch
 from task7_sim.robot import RobotGeometry
 cfg,model,meshes,sources=prepare();names=cfg['self_names'];body=[x['link'] for x in cfg['body']];allnames=names+body;n=len(names);allow=np.eye(n,dtype=bool);ab=np.zeros((n,len(body)),bool);rows=[];q=np.zeros((1,6));H={x:model.transform(frame(x,names),'base_footprint',q)[0] for x in allnames}
 zero_contacts=RobotGeometry(cfg).self_contacts(torch.zeros(1,3,dtype=torch.float64),torch.zeros(1,6,dtype=torch.float64))[0].numpy()
 # Physical nearest collision-link adjacency along URDF paths.
 adjacent=set()
 for child in allnames:
  cur=child
  while cur!='base_footprint' and cur in model.joints:
   parent=model.joints[cur][0]
   if parent in allnames:
    adjacent.add(tuple(sorted([allnames.index(child),allnames.index(parent)])));break
   cur=parent
 for i in range(n):
  for j in range(i+1,len(allnames)):
   na,nb=allnames[i],allnames[j];r=check(meshes[na],meshes[nb],H[na],H[nb]);adj=(i,j) in adjacent
   # Same rigid gripper is one old collision group; preserve it as fixed assembly.
   fixed=(i>=7 and j<n) or (i==6 and 7<=j<n) or (i==0 and j>=n)
   reason='adjacent' if adj else 'fixed_installation' if fixed and r['hit'] else 'zero_sphere_overlap' if zero_contacts[i,j] else None
   if i==2 and nb=='top_plate_link':reason=None
   if reason:
    if j<n:allow[i,j]=allow[j,i]=True
    else:ab[i,j-n]=True
    rows.append(dict(pair=[i,j],links=[na,nb],reason=reason,zero_sphere_contact=bool(zero_contacts[i,j]),zero_reference=r))
 cfg.update(self_allowed=allow.tolist(),self_body_allowed=ab.tolist(),self_allowed_reasons={','.join(map(str,r['pair'])):r['reason'] for r in rows},allowed_audit=str(AP))
 # Public legacy group table reflects the selected new arm/body checks.
 legacy=np.array(cfg['adjacent']);legacy[:8,:8]=allow[:8,:8]
 for i in range(7):legacy[i,8:]=ab[i]
 legacy[7,8:]=ab[7:].all(0);legacy[8:,:8]=legacy[:8,8:].T;cfg['allowed']=legacy.tolist()
 cfg['v1_always']=cfg.pop('always',cfg.get('v1_always'));cfg['allowed_reasons']={'note':'Production self checks use self_allowed/self_body_allowed; legacy 16x16 is aggregate compatibility only'}
 (P/'robot_geometry_v3.json').write_text(json.dumps(cfg,indent=2)+'\n');AP.write_text(json.dumps(dict(samples=10000,seed=20261021,sources=sources,rows=rows,zero_excluded_upper_topplate=True),indent=2)+'\n');print(json.dumps(rows,indent=2),flush=True)

def audit(maxwall):
 start=time.monotonic();cfg,model,meshes,sources=prepare();q=np.load(P/'allowed-q.npz')['q'];path=AP;data=json.loads(path.read_text());names=cfg['self_names'];allnames=names+[x['link'] for x in cfg['body']]
 for row in data['rows']:
  if row.get('complete'):continue
  i,j=row['pair'];na,nb=allnames[i],allnames[j];HA=model.transform(frame(na,names),'base_footprint',q);HB=model.transform(frame(nb,names),'base_footprint',q);rel=np.linalg.inv(HA)@HB;err=float(abs(rel-rel[0]).max());fixed=err<1e-12
  row['max_relative_transform_element_difference']=err;row['constant_relative_transform']=fixed
  if fixed:
   r=check(meshes[na],meshes[nb],HA[0],HB[0]);row.update(complete=True,samples=10000,mesh_queries=1,mesh_hit_count=10000 if r['hit'] else 0,method='one original-mesh query plus all 10000 relative transforms equal within 1e-12; fixed URDF joint path',fixed_reference=r);print(row,flush=True)
  else:
   done=row.get('samples',0);hits=row.get('mesh_hit_count',0);fn=P/('allowed-pair-'+str(i)+'-'+str(j)+'.jsonl')
   with fn.open('a') as f:
    for k in range(done,10000):
     r=check(meshes[na],meshes[nb],HA[k],HB[k]);hits+=int(r['hit']);f.write(json.dumps(dict(sample=k,reference=r))+'\n')
     row.update(samples=k+1,mesh_queries=k+1,mesh_hit_count=hits,complete=k+1==10000,method='10000 original-mesh references on uniform limited q')
     if k%100==0:
      f.flush();print(na,nb,k+1,hits,'wall',time.monotonic()-start,flush=True)
     if time.monotonic()-start>maxwall:
      path.write_text(json.dumps(data,indent=2)+'\n');print('RESUMABLE',row,flush=True);return
  path.write_text(json.dumps(data,indent=2)+'\n')
 print('ALL_COMPLETE',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['init','audit']);p.add_argument('--maxwall',type=float,default=480);p.add_argument('--table-name',default='allowed-audit.json');a=p.parse_args();AP=P/a.table_name;init() if a.mode=='init' else audit(a.maxwall)
