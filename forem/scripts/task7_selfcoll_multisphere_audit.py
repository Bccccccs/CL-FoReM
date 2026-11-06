"""10000 original-mesh pair audits with exact triangle witnesses, CPU offline.
A reused witness is re-tested against *each* original transformed triangle pair;
no sampled pose implies anything about another, and no runtime mesh narrowphase.
"""
import json,time,argparse
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree,ConvexHull
from task7_diag_mesh import crossing
from task7_selfcoll_multisphere_allowed import prepare,frame,check,P

def find_witness(A,B):
 ca=A.mean(1);cb=B.mean(1);ra=np.linalg.norm(A-ca[:,None],axis=-1).max(1);rb=np.linalg.norm(B-cb[:,None],axis=-1).max(1);tree=cKDTree(cb)
 for start in range(0,len(A),128):
  lists=tree.query_ball_point(ca[start:start+128],ra[start:start+128]+rb.max()+1e-7);ai=[];bi=[]
  for i,js in enumerate(lists):ai.extend([start+i]*len(js));bi.extend(js)
  if not ai:continue
  ai=np.array(ai);bi=np.array(bi);a=A[ai];b=B[bi];mask=(np.maximum(a.min(1),b.min(1))<=np.minimum(a.max(1),b.max(1))+1e-7).all(-1);ai,bi=ai[mask],bi[mask];a,b=a[mask],b[mask]
  if not len(a):continue
  hits=np.zeros(len(a),bool)
  for k in range(3):hits|=crossing(a[:,k],a[:,(k+1)%3],b)|crossing(b[:,k],b[:,(k+1)%3],a)
  if hits.any():k=np.where(hits)[0][0];return int(ai[k]),int(bi[k])
 return None

def component_parts(tr):
 v,inv=np.unique(np.round(tr.reshape(-1,3),10),axis=0,return_inverse=True);ix=inv.reshape(-1,3);parent=np.arange(len(v))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for a,b,c in ix:
  a=find(a);parent[find(b)]=a;parent[find(c)]=a
 labels=np.array([find(i) for i in ix[:,0]])
 return [np.unique(tr[labels==label].reshape(-1,3),axis=0) for label in np.unique(labels)]

def component_separation(A,B,rel):
 partsA=component_parts(A);partsB=component_parts(B);N=len(rel);separated=np.ones(N,bool);proof=[]
 for av in partsA:
  for bv in partsB:
   try:ah=ConvexHull(av);aa=np.unique(np.round(ah.equations[:,:3],10),axis=0);avv=av[ah.vertices]
   except Exception:aa=np.eye(3);avv=av
   try:bh=ConvexHull(bv);bb=np.unique(np.round(bh.equations[:,:3],10),axis=0);bvv=bv[bh.vertices]
   except Exception:bb=np.eye(3);bvv=bv
   ok=np.zeros(N,bool);cert=np.zeros((N,5));amin,amax=(avv@aa.T).min(0),(avv@aa.T).max(0);bmin,bmax=(bvv@bb.T).min(0),(bvv@bb.T).max(0)
   for k in range(0,N,64):
    ids=np.arange(k,min(k+64,N));b=bvv[None]@rel[ids,:3,:3].transpose(0,2,1)+rel[ids,None,:3,3];proj=b@aa.T;gaps=np.maximum(proj.min(1)-amax,amin-proj.max(1));best=gaps.argmax(-1);good=gaps[np.arange(len(ids)),best]>1e-7
    ok[ids[good]]=True;cert[ids[good],:3]=aa[best[good]];cert[ids[good],3]=gaps[np.arange(len(ids))[good],best[good]];cert[ids[good],4]=0
    ids=ids[~good]
    if len(ids):
     inv=np.linalg.inv(rel[ids]);a=avv[None]@inv[:,:3,:3].transpose(0,2,1)+inv[:,None,:3,3];proj=a@bb.T;gaps=np.maximum(proj.min(1)-bmax,bmin-proj.max(1));best=gaps.argmax(-1);good=gaps[np.arange(len(ids)),best]>1e-7
     ok[ids[good]]=True;cert[ids[good],:3]=bb[best[good]];cert[ids[good],3]=gaps[np.arange(len(ids))[good],best[good]];cert[ids[good],4]=1
   separated&=ok;proof.append(cert)
 return separated,np.array(proof)

def audit(table,maxwall):
 start=time.monotonic();cfg,model,meshes,_=prepare();q=np.load(P/'allowed-q.npz')['q'];names=cfg['self_names'];path=P/table;data=json.loads(path.read_text());allnames=names+[x['link'] for x in cfg['body']]
 for row in data['rows']:
  if not row.get('complete'):
   for earlier in P.glob('allowed-audit*.json'):
    if earlier==path:continue
    matches=[r for r in json.loads(earlier.read_text()).get('rows',[]) if r['pair']==row['pair'] and r.get('complete') and r.get('samples')==10000]
    if matches:
     keep=dict(row);row.update(matches[0]);row.update({k:keep[k] for k in ['reason','zero_sphere_contact','zero_reference'] if k in keep});row['reused_original_mesh_audit']=str(earlier);break

  if row.get('complete'):continue
  i,j=row['pair'];na,nb=allnames[i],allnames[j];HA=model.transform(frame(na,names),'base_footprint',q);HB=model.transform(frame(nb,names),'base_footprint',q);rel=np.linalg.inv(HA)@HB;err=float(abs(rel-rel[0]).max());fixed=err<1e-12;row['max_relative_transform_element_difference']=err;row['constant_relative_transform']=fixed
  # URDF path is also available in model. No moving arm joint on a fixed path.
  if fixed:
   r=check(meshes[na],meshes[nb],np.eye(4),rel[0]);row.update(complete=True,samples=10000,mesh_queries=1,mesh_hit_count=10000 if r['hit'] else 0,method='original mesh plus 10000 equal relative transforms of fixed URDF assembly',fixed_reference=r)
  else:
   A=meshes[na]['tri'];B=meshes[nb]['tri'];N=len(q);classification=np.full(N,-1,np.int8);method=np.zeros(N,np.int8);witness_ids=np.full(N,-1,np.int32);witnesses=[];refrows=[]
   # Exact original-mesh AABB separation in the first link frame.
   alo,ahi=A.min((0,1)),A.max((0,1))
   for k in range(0,N,64):
    b=B[None]@rel[k:k+64,None,:3,:3].transpose(0,1,3,2)+rel[k:k+64,None,None,:3,3];gap=np.maximum(0,np.maximum(alo-b.max((1,2)),b.min((1,2))-ahi));sep=np.linalg.norm(gap,axis=-1)>1e-7;classification[k:k+64][sep]=0;method[k:k+64][sep]=1
   # A separating plane proves separation of every original triangle by
   # convexity. Candidate axes come from raw-mesh convex hull face normals.
   av=np.unique(A.reshape(-1,3),axis=0);bv=np.unique(B.reshape(-1,3),axis=0)
   ah=ConvexHull(av);bh=ConvexHull(bv);av=av[ah.vertices];bv=bv[bh.vertices]
   axes=np.unique(np.round(ah.equations[:,:3],10),axis=0)
   normals=np.unique(np.round(bh.equations[:,:3],10),axis=0)
   certificates=[]
   for k in range(0,N,64):
    ids=np.arange(k,min(k+64,N));ids=ids[classification[ids]<0]
    if not len(ids):continue
    b=bv[None]@rel[ids,:3,:3].transpose(0,2,1)+rel[ids,None,:3,3]
    amin,amax=(av@axes.T).min(0),(av@axes.T).max(0);proj=b@axes.T
    gaps=np.maximum(proj.min(1)-amax,amin-proj.max(1));best=gaps.argmax(-1);good=gaps[np.arange(len(ids)),best]>1e-7
    for ix,axis_id in zip(ids[good],best[good]):certificates.append(dict(sample=int(ix),axis=axes[axis_id].tolist(),frame='first_link',gap_m=float(gaps[np.where(ids==ix)[0][0],axis_id])))
    classification[ids[good]]=0;method[ids[good]]=4
    # Rotating B normals, with A expressed in the B link frame.
    ids=ids[~good]
    if len(ids):
     inv=np.linalg.inv(rel[ids]);a=av[None]@inv[:,:3,:3].transpose(0,2,1)+inv[:,None,:3,3];bmin,bmax=(bv@normals.T).min(0),(bv@normals.T).max(0);proj=a@normals.T
     gaps=np.maximum(proj.min(1)-bmax,bmin-proj.max(1));best=gaps.argmax(-1);good=gaps[np.arange(len(ids)),best]>1e-7
     for ix,axis_id in zip(ids[good],best[good]):certificates.append(dict(sample=int(ix),axis=normals[axis_id].tolist(),frame='second_link',gap_m=float(gaps[np.where(ids==ix)[0][0],axis_id])))
     classification[ids[good]]=0;method[ids[good]]=4
   ids=np.where(classification<0)[0];component_proof=np.zeros((0,0,5));component_pose_ids=ids
   if len(ids):
    separated,component_proof=component_separation(A,B,rel[ids]);classification[ids[separated]]=0;method[ids[separated]]=5
   print('SEPARATION_CERTIFICATES',na,nb,len(certificates),'unresolved',int((classification<0).sum()),flush=True)
   checkpoint=P/f'allowed-progress-{i}-{j}.npz';checkpoint_json=P/f'allowed-progress-{i}-{j}.json'
   if checkpoint.exists():
    saved=np.load(checkpoint);classification=saved['classification'];method=saved['method'];witness_ids=saved['witness_ids'];meta=json.loads(checkpoint_json.read_text());witnesses=meta['witnesses'];refrows=meta['refrows'];certificates=meta['certificates'];print('RESUME',na,nb,'unresolved',int((classification<0).sum()),flush=True)
   while (classification<0).any():
    k=int(np.where(classification<0)[0][0]);b=B@rel[k,:3,:3].T+rel[k,:3,3];wit=find_witness(A,b)
    if wit is not None:
     ia,ib=wit;wid=len(witnesses);witnesses.append([ia,ib]);ids=np.where(classification<0)[0];a=np.broadcast_to(A[ia],(len(ids),3,3));b=B[ib][None]@rel[ids,:3,:3].transpose(0,2,1)+rel[ids,None,:3,3];hit=np.zeros(len(ids),bool)
     for edge in range(3):hit|=crossing(a[:,edge],a[:,(edge+1)%3],b)|crossing(b[:,edge],b[:,(edge+1)%3],a)
     assert hit[0];classification[ids[hit]]=1;method[ids[hit]]=2;witness_ids[ids[hit]]=wid
    else:
     r=check(meshes[na],meshes[nb],np.eye(4),rel[k]);classification[k]=int(r['hit']);method[k]=3;refrows.append(dict(sample=k,reference=r))
    if k%100==0:print('PROGRESS',na,nb,k,'unresolved',int((classification<0).sum()),'wall_s',time.monotonic()-start,flush=True)
    if time.monotonic()-start>maxwall:
     # Current pair remains explicitly incomplete; completed earlier pairs safe.
     np.savez_compressed(checkpoint,classification=classification,method=method,witness_ids=witness_ids);checkpoint_json.write_text(json.dumps(dict(witnesses=witnesses,refrows=refrows,certificates=certificates)))
     print('TIME_BOUND',na,nb,'unresolved',int((classification<0).sum()),flush=True);path.write_text(json.dumps(data,indent=2)+'\n');return
   fn='allowed-pair-'+str(i)+'-'+str(j)+'-certificates.npz';np.savez_compressed(P/fn,hit=classification,method=method,witness_id=witness_ids,witness_triangles=np.array(witnesses),relative=rel,component_proof=component_proof,component_pose_ids=component_pose_ids)
   (P/(fn+'.json')).write_text(json.dumps(dict(full_references=refrows,separating_planes=certificates),indent=2)+'\n')
   row.update(complete=True,samples=10000,mesh_queries=10000,mesh_hit_count=int(classification.sum()),method='per-q original mesh AABB or exact original triangle crossing witness, remaining poses full reference',certificates=fn,witness_triangles=len(witnesses),full_reference_queries=len(refrows),aabb_separated=int((method==1).sum()),separating_plane_confirmed=int((method==4).sum()),component_plane_confirmed=int((method==5).sum()),triangle_intersection_confirmed=int((method==2).sum()))
  path.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(row),flush=True)
 print('ALL_COMPLETE',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--table',default='allowed-audit-cells.json');p.add_argument('--maxwall',type=float,default=480);a=p.parse_args();audit(a.table,a.maxwall)
