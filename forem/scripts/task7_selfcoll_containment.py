"""Repeat the prior independent connected-component audit on newly checked pairs."""
import json,shutil,time
from pathlib import Path
import numpy as np
from task7_diag_mesh import load,inside,exact_surface
P=Path('results/task7/t7.18.2-r1-20261021');OLD=Path('results/task7/t7.18.1-r1-20261021')
def solids(tr):
 v,inv=np.unique(np.round(tr.reshape(-1,3),10),axis=0,return_inverse=True);ix=inv.reshape(-1,3);p=np.arange(len(v))
 def f(i):
  while p[i]!=i:p[i]=p[p[i]];i=p[i]
  return i
 for a,b,c in ix:
  a=f(a);p[f(b)]=a;p[f(c)]=a
 labels=np.array([f(i) for i in ix[:,0]]);return [tr[labels==l] for l in np.unique(labels)]
model,meshes,_=load();names=json.loads(Path('config/task7/robot_geometry_v1.json').read_text())['names'];sp={n:solids(m['tri']) for n,m in meshes.items()};audit=[]
for dataset in ['chain','sync','async']:
 a=np.load(OLD/('chain.npz' if dataset=='chain' else dataset+'/playback.npz'));file=P/f'reference-{dataset}.jsonl'
 if not file.exists():continue
 backup=P/f'reference-{dataset}-before-containment-audit.jsonl'
 if not backup.exists():shutil.copy2(file,backup)
 # Always use the immutable pre-audit rows for reproducibility.
 with backup.open() as inp,file.open('w') as out:
  for line in inp:
   row=json.loads(line);q=a['q'][row['pose']].astype(float)[None];hs={}
   for x in row['pairs']:
    ref=x['reference']
    if ref['method']!='containment':continue
    i,j=map(int,x['pair'].split(','));na,nb=names[i],names[j]
    for name in [na,nb]:
     if name not in hs:hs[name]=model.transform(name,'base_footprint',q)[0]
    HA,HB=hs[na],hs[nb];SA=[t@HA[:3,:3].T+HA[:3,3] for t in sp[na]];SB=[t@HB[:3,:3].T+HB[:3,3] for t in sp[nb]]
    hit=any(inside(t[0,0],s) for t in SA for s in SB) or any(inside(t[0,0],s) for t in SB for s in SA)
    d=None
    if not hit:
     A=meshes[na]['tri']@HA[:3,:3].T+HA[:3,3];B=meshes[nb]['tri']@HB[:3,:3].T+HB[:3,3];d=exact_surface(A,B,ref['sample_upper']);hit=d<=1e-7
    item=dict(dataset=dataset,pose=row['pose'],pair=x['pair'],original=ref,component_reference_hit=hit,surface_distance_m=d,changed=hit!=ref['hit']);audit.append(item)
    if hit!=ref['hit']:x['reference']=dict(hit=hit,distance=d,sample_upper=ref['sample_upper'],lower=ref['lower'],method='component_union_and_exact_triangle_audit')
   out.write(json.dumps(row)+'\n')
 print('audited',dataset,flush=True)
(P/'containment-audit.json').write_text(json.dumps(dict(checked=len(audit),differences=[x for x in audit if x['changed']],rows=audit),indent=2));print('differences',[x for x in audit if x['changed']],flush=True)
