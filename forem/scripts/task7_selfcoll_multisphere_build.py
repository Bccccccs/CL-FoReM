"""Deterministic full-triangle spatial-cell enclosure, offline only (SRC-0545).
Every triangle is clipped at slab planes. Each resulting polygon is enclosed by
one convex sphere, proving continuous surface enclosure, not just vertex cover.
"""
import json,hashlib,time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import ConvexHull,cKDTree
from scipy.stats import qmc
from task7_diag_mesh import load,dense,components
from task7_sim.robot import ARMS
P=Path('results/task7/t7.18.2-r2-20261021');P.mkdir(parents=True,exist_ok=True)

def clip(poly,axis,bound,lower):
 out=[]
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  ina=(a[axis]>=bound) if lower else (a[axis]<=bound)
  inb=(b[axis]>=bound) if lower else (b[axis]<=bound)
  if ina:out.append(a)
  if ina!=inb:out.append(a+(b-a)*((bound-a[axis])/(b[axis]-a[axis])))
 return np.array(out).reshape(-1,3)

def ball(v):
 v=np.unique(v,axis=0)
 if len(v)>4:
  try:v=v[ConvexHull(v).vertices]
  except Exception:pass
 origin=(v.min(0)+v.max(0))/2;scale=max(np.linalg.norm(v-origin,axis=-1).max(),1e-9);w=(v-origin)/scale
 def fun(x):return x[3]
 def jac(x):return np.array([0.,0.,0.,1.])
 def con(x):return x[3]-((w-x[:3])**2).sum(-1)
 def cj(x):return np.c_[2*(w-x[:3]),np.ones(len(w))]
 fit=minimize(fun,np.array([0.,0.,0.,1.]),jac=jac,constraints={'type':'ineq','fun':con,'jac':cj},method='SLSQP',options={'ftol':1e-13,'maxiter':300})
 c=origin+fit.x[:3]*scale;r=np.nextafter(float(np.linalg.norm(v-c,axis=-1).max()),np.inf)
 return c,r,bool(fit.success)

def slab_fit(tr,n):
 vertices=tr.reshape(-1,3);axis=int(np.argmax(np.ptp(vertices,axis=0)));edges=np.linspace(vertices[:,axis].min(),vertices[:,axis].max(),n+1);specs=[];audit=[]
 for lo,hi in zip(edges[:-1],edges[1:]):
  polys=[]
  for triangle in tr[(tr[:,:,axis].max(1)>=lo)&(tr[:,:,axis].min(1)<=hi)]:
   pp=clip(clip(triangle,axis,lo,True),axis,hi,False)
   if len(pp):polys.append(pp)
  if not polys:continue
  points=np.unique(np.concatenate(polys),axis=0);c,r,success=ball(points)
  specs.append(dict(centre=c.tolist(),radius_m=r));audit.append(dict(axis=axis,lo_m=lo,hi_m=hi,clipped_polygon_vertices=len(points),max_clipped_vertex_excess_m=float((np.linalg.norm(points-c,axis=-1)-r).max()),optimizer_success=success))
 return specs,audit

def fit(tr,n):
 # Recursive spatial cells avoid the large end-cap excess of axial-only slabs.
 leaves=[list(tr)]
 while len(leaves)<n:
  scored=[]
  for index,polys in enumerate(leaves):
   v=np.concatenate(polys);lo,hi=v.min(0),v.max(0)
   scored.append((float(np.linalg.norm(hi-lo)),index,lo,hi))
  _,index,lo,hi=max(scored,key=lambda t:t[0]);axis=int(np.argmax(hi-lo));bound=float((lo[axis]+hi[axis])/2)
  left=[];right=[]
  for poly in leaves.pop(index):
   aa=clip(poly,axis,bound,False);bb=clip(poly,axis,bound,True)
   if len(aa):left.append(aa)
   if len(bb):right.append(bb)
  assert left and right
  leaves.extend([left,right])
 specs=[];audit=[]
 for polys in leaves:
  points=np.unique(np.concatenate(polys),axis=0);c,r,success=ball(points)
  specs.append(dict(centre=c.tolist(),radius_m=r));audit.append(dict(cell_min_m=points.min(0).tolist(),cell_max_m=points.max(0).tolist(),clipped_polygon_vertices=len(points),max_clipped_vertex_excess_m=float((np.linalg.norm(points-c,axis=-1)-r).max()),optimizer_success=success))
 return specs,audit

if __name__=='__main__':
 import argparse
 pa=argparse.ArgumentParser();pa.add_argument('--hybrid',action='store_true');pa.add_argument('--counts',type=str,default='1,1,8,512,256,256,128');args=pa.parse_args()
 model,meshes,sources=load();old=json.loads(Path('config/task7/robot_geometry_v1.json').read_text())
 import xml.etree.ElementTree as ET
 root=ET.parse('config/task7/model.urdf').getroot();grip=[l.get('name') for l in root.findall('link') if l.get('name').startswith('gripper_') and l.findall('collision')]
 names=ARMS[:7]+grip;triangles=[meshes[n]['tri'] for n in ARMS[:7]]+meshes['gripper_base_link']['parts'];counts=list(map(int,args.counts.split(',')))+[16,4,4,8,8,8,8,8,8]
 assert len(counts)==len(names)==len(triangles)==16
 specs=[];rows=[]
 for idx,(name,tr,n) in enumerate(zip(names,triangles,counts)):
  start=time.monotonic();sp,au=(slab_fit(tr,n) if args.hybrid and idx in [2] else fit(tr,n));points=dense(tr);centres=np.array([x['centre'] for x in sp]);radii=np.array([x['radius_m'] for x in sp]);excess=(np.linalg.norm(points[:,None]-centres,axis=-1)-radii).min(-1)
  # QMC union volume estimate in the sphere AABB; signed mesh volume is exact
  # for the closed triangle representation. Estimates are explicitly labelled.
  lo=(centres-radii[:,None]).min(0);hi=(centres+radii[:,None]).max(0);samples=lo+qmc.Sobol(3,scramble=True,seed=20261021).random_base2(16)*(hi-lo)
  inside=(np.linalg.norm(samples[:,None]-centres,axis=-1)<=radii).any(-1);volume=float(np.prod(hi-lo)*inside.mean());meshvol=float(abs(np.einsum('ij,ij->i',tr[:,0],np.cross(tr[:,1],tr[:,2])).sum()/6))
  k=np.arange(1024);z=1-2*(k+.5)/1024;ang=k*np.pi*(3-np.sqrt(5));unit=np.c_[np.sqrt(1-z*z)*np.cos(ang),np.sqrt(1-z*z)*np.sin(ang),z]
  surface=(centres[:,None]+radii[:,None,None]*unit).reshape(-1,3);tree=cKDTree(points);outside=float(tree.query(surface,workers=1)[0].max())
  row=dict(name=name,count=len(sp),requested_count=n,curobo_reference_count=([None,1,8,9,4,4,1][idx] if idx<7 else None),method=('axial_slabs' if args.hybrid and idx in [2] else 'spatial_cells'),raw_vertices=len(tr.reshape(-1,3)),dense_points=len(points),max_dense_point_excess_m=float(excess.max()),mesh_volume_m3=meshvol,union_volume_qmc_m3=volume,envelope_excess_volume_qmc_m3=volume-meshvol,envelope_to_mesh_volume_ratio=volume/meshvol if meshvol else None,sampled_max_protrusion_upper_m=outside,protrusion_bound_m=float(2*radii.max()),cells=au,wall_s=time.monotonic()-start)
  for x in sp:x.update(link='gripper_base_link' if idx>=7 else name,name=name,group=idx)
  specs.extend(sp);rows.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ['slabs','cells']}),flush=True)
  assert excess.max()<1e-12 and max(x['max_clipped_vertex_excess_m'] for x in au)<1e-12
 new=dict(old);new.update(schema=3,geometry_version='selfcoll-multisphere-v3-20261021',self_spheres=specs,self_names=names,self_margin_m=0.,environment_geometry_version='v1-unchanged',fit='recursively clipped full triangle spatial cells, minimum enclosing sphere of each polygon union; no self padding; original 8 padded environment capsules unchanged',self_allowed=np.eye(16,dtype=bool).tolist(),self_body_allowed=np.zeros((16,8),dtype=bool).tolist(),fit_audit=str(P/'fit-audit.json'))
 (P/'candidate-config.json').write_text(json.dumps(new,indent=2)+'\n');(P/'fit-audit.json').write_text(json.dumps(dict(sources=sources,links=rows,total_spheres=len(specs),method='Every clipped triangle polygon enclosed by a convex ball; all mesh vertices and <=4mm dense surface samples additionally verified',volume_samples=65536,surface_samples_per_sphere=1024,limitation='QMC excess volume is estimate; surface sample distance upper is sampled only, 2*max_radius is conservative global protrusion bound'),indent=2)+'\n')
 from task7_sim.kinematics import LOW,HIGH
 q=np.random.default_rng(20261021).uniform(LOW,HIGH,(10000,6));np.savez_compressed(P/'allowed-q.npz',q=q)
