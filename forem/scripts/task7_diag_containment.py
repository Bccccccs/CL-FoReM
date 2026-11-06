"""Independent connected-component union containment audit of near mesh pairs."""
import json,collections,time
import numpy as np
from task7_diag_mesh import P,load,inside,exact_surface

def solids(tr):
 v,inv=np.unique(np.round(tr.reshape(-1,3),10),axis=0,return_inverse=True);ix=inv.reshape(-1,3);p=np.arange(len(v))
 def f(i):
  while p[i]!=i:p[i]=p[p[i]];i=p[i]
  return i
 for a,b,c in ix:
  a=f(a);p[f(b)]=a;p[f(c)]=a
 labels=np.array([f(i) for i in ix[:,0]]);return [tr[labels==l] for l in np.unique(labels)]
model,meshes,src=load();names=list(json.loads((P/'mesh-manifest.json').read_text())['meshes']);sp={n:solids(m['tri']) for n,m in meshes.items()};start=time.monotonic();differences=[];resolved_crossings=[];n=0;counts=collections.Counter()
for dataset in ['chain','sync','async']:
 a=np.load(P/('chain.npz' if dataset=='chain' else dataset+'/playback.npz'))
 for file in P.glob('mesh-'+dataset+'-*.jsonl'):
  for line in file.read_text().splitlines():
   row=json.loads(line);q=a['q'][row['pose']].astype(float)[None];hs={}
   for x in row['pairs']:
    ref=x['reference']
    if ref['method'] in ['original_mesh_AABB_separation','enclosing_capsule_clear']:continue
    if ref['method']=='exact_triangle' and ref['hit']:continue # explicit triangle crossing already proves collision
    i,j=map(int,x['pair'].split(','));na,nb=names[i],names[j]
    for name in [na,nb]:
     if name not in hs:hs[name]=model.transform(name,'base_footprint',q)[0]
    HA,HB=hs[na],hs[nb];SA=[t@HA[:3,:3].T+HA[:3,3] for t in sp[na]];SB=[t@HB[:3,:3].T+HB[:3,3] for t in sp[nb]]
    hit=any(inside(t[0,0],s) for t in SA for s in SB) or any(inside(t[0,0],s) for t in SB for s in SA)
    if not hit and ref['hit']:
     A=meshes[na]['tri']@HA[:3,:3].T+HA[:3,3];B=meshes[nb]['tri']@HB[:3,:3].T+HB[:3,3];d=exact_surface(A,B,ref['sample_upper']);hit=d<=1e-7
     if hit:resolved_crossings.append(dict(dataset=dataset,pose=row['pose'],pair=x['pair'],distance=d))
    if hit!=ref['hit']:differences.append(dict(dataset=dataset,pose=row['pose'],pair=x['pair'],original=ref,component_union_contains=hit))
    n+=1;counts[ref['method']]+=1
out=dict(checked_pairs=n,method_counts=dict(counts),differences=differences,representative_differences_resolved_by_triangle_crossing=resolved_crossings,component_counts={k:len(v) for k,v in sp.items()},wall_s=time.monotonic()-start)
(P/'containment-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out));assert not differences
