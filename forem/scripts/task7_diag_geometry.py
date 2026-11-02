"""Pairwise mesh confusion and candidate geometry estimate; never modifies config."""
import json,time,argparse
from pathlib import Path
import numpy as np
import torch
from task7_diag_mesh import load,reference,selfcheck,P
from task7_sim.robot import fit_capsule
from task7_sim.geometry import segment_distance,segment_box_distance,to_box

def sliced(tr,width=.04):
 v=tr.reshape(-1,3);axis=int(np.argmax(np.ptp(v,axis=0)));lo=v[:,axis].min();hi=v[:,axis].max();planes=np.linspace(lo,hi,max(1,int(np.ceil((hi-lo)/width)))+1);out=[]
 for l,h in zip(planes[:-1],planes[1:]):
  verts=[v[(v[:,axis]>=l-1e-10)&(v[:,axis]<=h+1e-10)]]
  for p in [l,h]:
   for i,j in [(0,1),(1,2),(2,0)]:
    a=tr[:,i];b=tr[:,j];den=b[:,axis]-a[:,axis];t=(p-a[:,axis])/np.where(den!=0,den,1);ok=(den!=0)&(t>=0)&(t<=1);verts.append(a[ok]+t[ok,None]*(b[ok]-a[ok]))
  vv=np.concatenate(verts)
  if len(vv):
   a,b,r=fit_capsule(vv);out.append(np.r_[a,b,r])
 return np.array(out)

def main(dataset,start,stop):
 torch.set_num_threads(2);beg=time.monotonic();assert selfcheck();model,meshes,sources=load();cfg=json.loads(Path('config/task7/robot_geometry.json').read_text());names=cfg['names'];allow=np.array(cfg['allowed']);specs={};audit={}
 for i,name in enumerate(names):
  m=meshes[name];specs[name]={}
  if i<8:
   raw=np.r_[cfg['capsules'][i]['a'],cfg['capsules'][i]['b'],cfg['capsules'][i]['radius_m']-.02][None]
   split=np.array([np.concatenate([*fit_capsule(t.reshape(-1,3))[:2],np.array([fit_capsule(t.reshape(-1,3))[2]])]) for t in m['parts']]) if i==7 else raw
   # Refit each primitive piece, optionally split into <=4cm axial slabs.
   allsplit=np.concatenate([sliced(t) for t in m['parts']])
   specs[name]={'no_arm_margin':raw,'split_gripper':split,'slabs_4cm':allsplit}
   v=torch.tensor(m['tri'].reshape(-1,3));a=torch.tensor(cfg['capsules'][i]['a']);b=torch.tensor(cfg['capsules'][i]['b']);u=b-a;t=((v-a)*u).sum(-1)/(u@u) if float(u@u)>0 else torch.zeros(len(v));dist=(v-a-t.clamp(0,1)[:,None]*u).norm(dim=-1)
   audit[name]={'max_vertex_capsule_excess_m':float(dist.max())-cfg['capsules'][i]['radius_m']}
  else:
   H=model.transform(name,'base_footprint',np.zeros((1,6)))[0];v=m['tri'].reshape(-1,3)@H[:3,:3].T+H[:3,3];b=cfg['body'][i-8];audit[name]={'max_vertex_box_excess_m':float((abs(v-np.array(b['centre']))-np.array(b['half'])).max())}
  audit.setdefault(name,{}).update(triangles=len(m['tri']),dense_points=len(m['points']),boundary_edges=m['boundary_edges'],components=len(m['reps']))
 (P/'mesh-manifest.json').write_text(json.dumps(dict(sources=sources,meshes=audit,h_m=.004,surface_distance_threshold_m=1e-7,cylinder_sides=128,max_cylinder_sagitta_m=.1651*(1-np.cos(np.pi/128))),indent=2))
 if dataset=='chain':a=np.load(P/'chain.npz');ids=np.arange(len(a['q']))
 else:
  a=np.load(P/dataset/'playback.npz');ids=np.where(a['pairs'].any(axis=(1,2)))[0]
 ids=ids[start:stop];f=P/f'mesh-{dataset}-{start}-{stop}.jsonl';done=set()
 if f.exists():done={json.loads(x)['pose'] for x in f.read_text().splitlines()}
 def Hs(q):return {n:model.transform(n if i<8 else n,'base_footprint',q[None])[0] for i,n in enumerate(names)}
 with f.open('a') as output:
  for seq,idx in enumerate(ids):
   if int(idx) in done:continue
   q=a['q'][idx].astype(float);trans=Hs(q);transcaps={};rows=[]
   for i,n in enumerate(names[:8]):
    H=trans[n];transcaps[n]={}
    for mode,cp in specs[n].items():
     c=cp.copy();c[:,:3]=cp[:,:3]@H[:3,:3].T+H[:3,3];c[:,3:6]=cp[:,3:6]@H[:3,:3].T+H[:3,3];transcaps[n][mode]=torch.tensor(c)
   for i in range(8):
    for j in range(i+1,len(names)):
     if allow[i,j]:continue
     # Envelope-clear is a proof of mesh-clear once enclosure audit passed.
     hit=bool(a['pairs'][idx,i,j]);est={mode:False for mode in ['no_arm_margin','split_gripper','slabs_4cm']}
     if hit:
      ref=reference(meshes[names[i]],meshes[names[j]],trans[names[i]],trans[names[j]])
     else:ref={'hit':False,'method':'enclosing_capsule_clear','lower':None,'sample_upper':None,'distance':None}
     for mode in est:
      ca=transcaps[names[i]][mode]
      if j<8:
       cb=transcaps[names[j]][mode];d=segment_distance(ca[:,None,:3],ca[:,None,3:6],cb[None,:,:3],cb[None,:,3:6]);est[mode]=bool((d<=ca[:,None,6]+cb[None,:,6]).any())
      else:
       box=cfg['body'][j-8];bx=torch.tensor([*box['centre'],*box['half'],1.,0.]);d=segment_box_distance(to_box(ca[:,:3],bx),to_box(ca[:,3:6],bx),bx[3:6]);est[mode]=bool((d<=ca[:,6]+.02).any())
     rows.append(dict(pair=f'{i},{j}',envelope_hit=hit,reference=ref,estimates=est))
   # Audit known Always exclusion upperarm/topplate independently (not adjacent).
   ref=reference(meshes[names[2]],meshes[names[13]],trans[names[2]],trans[names[13]])
   rows.append(dict(pair='2,13',allowed=True,envelope_hit=False,reference=ref))
   output.write(json.dumps(dict(pose=int(idx),pairs=rows))+'\n');output.flush()
   if seq%10==0:print(dataset,start,seq,'/',len(ids),'wall',time.monotonic()-beg,flush=True)
 print('finished',dataset,start,stop,'wall',time.monotonic()-beg,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('dataset',choices=['chain','sync','async']);p.add_argument('start',type=int);p.add_argument('stop',type=int);a=p.parse_args();main(a.dataset,a.start,a.stop)
