"""Numpy/scipy URDF collision mesh reference, no installed geometry dependency.
Dense barycentric samples provide distance upper/lower bounds; exact triangle
surface distance + ray containment resolves ambiguous overlap. Original URDF
primitives are boxes/cylinders, cylinders have explicit polygon sagitta bound.
"""
import json,math,hashlib,struct,time,argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from task7_sim.robot import _mesh,_origin,fit_capsule,ARMS
from task7_sim.kinematics import Model
P=Path('results/task7/t7.18.1-r1-20261021');ROOT=Path.cwd()

def boxtri(size):
 from scipy.spatial import ConvexHull
 half=np.array(size)/2;v=np.array([[x,y,z] for x in [-half[0],half[0]] for y in [-half[1],half[1]] for z in [-half[2],half[2]]]);return v[ConvexHull(v).simplices]
def cylinder(r,h,n=128):
 t=np.arange(n)*2*np.pi/n;lo=np.stack([r*np.cos(t),r*np.sin(t),np.full(n,-h/2)],-1);hi=lo.copy();hi[:,2]=h/2;out=[]
 for i in range(n):
  j=(i+1)%n;out.extend([[lo[i],lo[j],hi[j]],[lo[i],hi[j],hi[i]],[[0,0,-h/2],lo[j],lo[i]],[[0,0,h/2],hi[i],hi[j]]])
 return np.array(out)
def dense(tri,h=.004):
 out=[]
 for tr in tri:
  n=max(1,int(np.ceil(max(np.linalg.norm(tr[1]-tr[0]),np.linalg.norm(tr[2]-tr[1]),np.linalg.norm(tr[0]-tr[2]))/h)))
  ij=np.array([(i,j) for i in range(n+1) for j in range(n+1-i)],float)/n
  out.append(tr[0]+ij[:,:1]*(tr[1]-tr[0])+ij[:,1:]*(tr[2]-tr[0]))
 return np.unique(np.concatenate(out),axis=0)
def components(tr):
 v,inv=np.unique(np.round(tr.reshape(-1,3),10),axis=0,return_inverse=True);ix=inv.reshape(-1,3);parent=np.arange(len(v))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for a,b,c in ix:
  a=find(a);parent[find(b)]=a;parent[find(c)]=a
 reps={find(i):v[i] for i in range(len(v))}
 edges=np.sort(np.concatenate([ix[:,[0,1]],ix[:,[1,2]],ix[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
 return np.array(list(reps.values())),int((counts!=2).sum())
def load():
 model=Model(ROOT/'config/task7/model.urdf');r=ET.parse(ROOT/'config/task7/model.urdf').getroot();parts={};src={}
 pk={'ur_description':Path('/opt/ros/noetic/share/ur_description'),'husky_description':ROOT/'src/husky_description','robotiq_85_description':ROOT/'src/robotiq_85_description'}
 for l in r.findall('link'):
  name=l.get('name');items=[]
  for c in l.findall('collision'):
   g=c.find('geometry');m=g.find('mesh');b=g.find('box');cy=g.find('cylinder');sp=g.find('sphere');H=_origin(c.find('origin'))
   if m is not None:
    pkg,tail=m.get('filename').removeprefix('package://').split('/',1);p=pk[pkg]/tail;tr=_mesh(p).reshape(-1,3,3)*np.array(list(map(float,m.get('scale','1 1 1').split())));src[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'triangles':len(tr)}
   elif b is not None:tr=boxtri(list(map(float,b.get('size').split())))
   elif cy is not None:tr=cylinder(float(cy.get('radius')),float(cy.get('length')))
   elif sp is not None and float(sp.get('radius'))==0:continue
   else:raise ValueError(ET.tostring(g))
   tr=tr@H[:3,:3].T+H[:3,3];items.append(tr)
  if items:parts[name]=items
 # union gripper in gripper_base frame, retain constituent meshes for split fit
 grip=[]
 for name in parts:
  if name.startswith('gripper_'):
   H=model.transform(name,'gripper_base_link',np.zeros((1,6)))[0]
   grip.extend([t@H[:3,:3].T+H[:3,3] for t in parts[name]])
 parts['gripper_base_link']=grip
 names=json.loads((ROOT/'config/task7/robot_geometry.json').read_text())['names'];meshes={}
 for name in names:
  tr=np.concatenate(parts[name]);reps,bad=components(tr);points=dense(tr)
  meshes[name]=dict(tri=tr,points=points,reps=reps,parts=parts[name],boundary_edges=bad)
 return model,meshes,src

def segpoint(p,a,b):
 d=b-a;den=(d*d).sum(-1);t=np.clip(((p-a)*d).sum(-1)/np.maximum(den,1e-300),0,1);return np.linalg.norm(p-a-t[...,None]*d,axis=-1)
def pointtri(p,tr):
 a,b,c=tr[:,0],tr[:,1],tr[:,2];u=b-a;v=c-a;w=p-a;n=np.cross(u,v);nn=(n*n).sum(-1);proj=p-n*(((w*n).sum(-1)/np.maximum(nn,1e-300))[:,None]);ww=proj-a
 uu=(u*u).sum(-1);vv=(v*v).sum(-1);uv=(u*v).sum(-1);wu=(ww*u).sum(-1);wv=(ww*v).sum(-1);den=uu*vv-uv*uv
 s=(vv*wu-uv*wv)/np.maximum(den,1e-300);t=(uu*wv-uv*wu)/np.maximum(den,1e-300);inside=(den>1e-24)&(s>=-1e-12)&(t>=-1e-12)&(s+t<=1+1e-12)
 ds=np.minimum.reduce([segpoint(p,a,b),segpoint(p,b,c),segpoint(p,c,a)])
 return np.where(inside,np.linalg.norm(p-proj,axis=-1),ds)
def segseg(a,b,c,d):
 u=b-a;v=d-c;w=a-c;aa=(u*u).sum(-1);bb=(u*v).sum(-1);cc=(v*v).sum(-1);dd=(u*w).sum(-1);ee=(v*w).sum(-1);det=aa*cc-bb*bb
 s=(bb*ee-cc*dd)/np.where(det!=0,det,1);t=(aa*ee-bb*dd)/np.where(det!=0,det,1);inside=(det>1e-24)&(s>=0)&(s<=1)&(t>=0)&(t<=1)
 return np.minimum(np.where(inside,np.linalg.norm(w+s[:,None]*u-t[:,None]*v,axis=-1),np.inf),np.minimum.reduce([segpoint(a,c,d),segpoint(b,c,d),segpoint(c,a,b),segpoint(d,a,b)]))
def crossing(a,b,tr):
 v0,v1,v2=tr[:,0],tr[:,1],tr[:,2];e1=v1-v0;e2=v2-v0;di=b-a;h=np.cross(di,e2);det=(e1*h).sum(-1);ok=np.abs(det)>1e-15;f=1/np.where(ok,det,1);s=a-v0;u=f*(s*h).sum(-1);q=np.cross(s,e1);v=f*(di*q).sum(-1);t=f*(e2*q).sum(-1)
 return ok&(u>=-1e-10)&(v>=-1e-10)&(u+v<=1+1e-10)&(t>=-1e-10)&(t<=1+1e-10)
def inside(point,tr):
 # Generic non-axis ray; merge shared-edge triangle crossings.
 direction=np.array([.8944271909999,.38196601125,.231]);a=np.broadcast_to(point,(len(tr),3));b=a+direction*100
 v0,v1,v2=tr[:,0],tr[:,1],tr[:,2];e1=v1-v0;e2=v2-v0;h=np.cross(b-a,e2);det=(e1*h).sum(-1);ok=np.abs(det)>1e-15;f=1/np.where(ok,det,1);s=a-v0;u=f*(s*h).sum(-1);q=np.cross(s,e1);v=f*((b-a)*q).sum(-1);t=f*(e2*q).sum(-1)
 vals=np.sort(t[ok&(u>=0)&(v>=0)&(u+v<=1)&(t>1e-10)])
 return bool((len(vals) and (1+int((np.diff(vals)>1e-9).sum()))%2))
def exact_surface(A,B,upper):
 ca=A.mean(1);cb=B.mean(1);ra=np.linalg.norm(A-ca[:,None],axis=-1).max(1);rb=np.linalg.norm(B-cb[:,None],axis=-1).max(1);tree=cKDTree(cb);best=upper
 for start in range(0,len(A),128):
  lists=tree.query_ball_point(ca[start:start+128],ra[start:start+128]+rb.max()+best+1e-9)
  ai=[];bi=[]
  for i,j in enumerate(lists):ai.extend([start+i]*len(j));bi.extend(j)
  if not ai:continue
  a=A[ai];b=B[bi];gap=np.maximum(0,np.maximum(a.min(1)-b.max(1),b.min(1)-a.max(1)));mask=np.linalg.norm(gap,axis=-1)<=best+1e-9;a=a[mask];b=b[mask]
  if not len(a):continue
  for i in range(3):
   if crossing(a[:,i],a[:,(i+1)%3],b).any() or crossing(b[:,i],b[:,(i+1)%3],a).any():return 0.
   best=min(best,float(pointtri(a[:,i],b).min()),float(pointtri(b[:,i],a).min()))
   for j in range(3):best=min(best,float(segseg(a[:,i],a[:,(i+1)%3],b[:,j],b[:,(j+1)%3]).min()))
 return best

def reference(a,b,HA,HB):
 A=a['tri']@HA[:3,:3].T+HA[:3,3];B=b['tri']@HB[:3,:3].T+HB[:3,3]
 gap=np.maximum(0,np.maximum(A.min((0,1))-B.max((0,1)),B.min((0,1))-A.max((0,1))))
 if np.linalg.norm(gap)>1e-7:
  return dict(hit=False,distance=None,sample_upper=None,lower=float(np.linalg.norm(gap)),method='original_mesh_AABB_separation')
 # Query smaller point cloud in larger cloud's own local frame, reuse tree.
 if len(a['points'])<len(b['points']):a,b=b,a;HA,HB=HB,HA;A,B=B,A
 if '_tree' not in a:a['_tree']=cKDTree(a['points'])
 relative=np.linalg.inv(HA)@HB;pb=b['points']@relative[:3,:3].T+relative[:3,3]
 upper=float(a['_tree'].query(pb[::32],workers=1)[0].min())
 lo=a['points'].min(0);hi=a['points'].max(0);bound=np.linalg.norm(np.maximum(0,np.maximum(lo-pb,pb-hi)),axis=-1)
 subset=pb[bound<=upper+1e-12]
 up=float(a['_tree'].query(subset,distance_upper_bound=upper+1e-10,workers=1)[0].min());lower=max(0,up-a.get('coverage_h',.004)-b.get('coverage_h',.004))
 # Always containment-check each connected component, even when surfaces separate.
 contained=any(inside(p,part@HB[:3,:3].T+HB[:3,3]) for p in (a['reps']@HA[:3,:3].T+HA[:3,3]) for part in b.get('parts',[b['tri']])) or any(inside(p,part@HA[:3,:3].T+HA[:3,3]) for p in (b['reps']@HB[:3,:3].T+HB[:3,3]) for part in a.get('parts',[a['tri']]))
 if contained:return dict(hit=True,distance=0.,sample_upper=up,lower=lower,method='containment')
 if lower>1e-7:return dict(hit=False,distance=None,sample_upper=up,lower=lower,method='certified_sample_clear')
 d=exact_surface(A,B,up)
 return dict(hit=bool(d<=1e-7),distance=d,sample_upper=up,lower=lower,method='exact_triangle')

def selfcheck():
 a=boxtri([1,1,1]);h=np.eye(4);bb=h.copy();bb[0,3]=2
 def m(t):return {'tri':t,'points':dense(t,.05),'reps':components(t)[0],'coverage_h':.05}
 x=m(a);assert not reference(x,x,h,bb)['hit'];bb[0,3]=.75;assert reference(x,x,h,bb)['hit'];y=m(a*.2);assert reference(x,y,h,h)['hit'];bb[0,3]=1;assert reference(x,x,h,bb)['hit']
 # crossed thin triangles with no vertex lying on other triangle
 aa=np.array([[[0,0,0],[2,0,0],[0,2,0]]],float);b=np.array([[[.5,.5,-1],[.5,.5,1],[.7,.5,0]]]);assert exact_surface(aa,b,1)==0
 return True
if __name__=='__main__':print('selfcheck',selfcheck())
