#!/usr/bin/env python3
"""Task8.8 only: independent JSON diagnostics, real panoramas, unchanged runtime.

JSON is NEVER supplied to scene occupancy. 5^3 subcell centres provide a
finite diagnostic approximation, not proof of continuous OBB equivalence.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time
import traceback

START = time.monotonic()
H=.05
ORIGIN=(-5.,-5.,0.)
SHAPE=(32,200,200)


def dump(path, obj):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(path)


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj


def box_masks(box):
    """Independent separable 5x5 XY / 5 Z evaluation = full 5^3 samples."""
    import numpy as np
    b=np.asarray(box,dtype=np.float64)
    if b.shape!=(8,) or (b[3:6]<=0).any():raise ValueError('invalid OBB')
    if not np.isclose(b[6]**2+b[7]**2,1,atol=1e-8,rtol=0):raise ValueError('invalid OBB rotation')
    corners=np.array([[x,y] for x in (0,b[3]) for y in (0,b[4])])
    world=corners@np.array([[b[6],b[7]],[-b[7],b[6]]])+b[:2]
    lower=np.maximum(np.floor((world.min(0)-np.array(ORIGIN[:2]))/H).astype(int),0)
    upper=np.minimum(np.floor((world.max(0)-np.array(ORIGIN[:2]))/H).astype(int)+1,200)
    zlo=max(0,int(np.floor(b[2]/H)));zhi=min(32,int(np.floor((b[2]+b[5])/H))+1)
    full=np.zeros(SHAPE,bool);anyhit=full.copy()
    if (upper<=lower).any() or zhi<=zlo:return full,anyhit
    yy,xx=np.meshgrid(np.arange(lower[1],upper[1]),np.arange(lower[0],upper[0]),indexing='ij')
    xyall=np.ones(xx.shape,bool);xyany=np.zeros(xx.shape,bool)
    fractions=(.1,.3,.5,.7,.9)
    for fy in fractions:
        for fx in fractions:
            dx=-5+(xx+fx)*H-b[0];dy=-5+(yy+fy)*H-b[1]
            u=dx*b[6]+dy*b[7];v=-dx*b[7]+dy*b[6]
            hit=(u>=0)&(u<=b[3])&(v>=0)&(v<=b[4])
            xyall &= hit;xyany |= hit
    zz=np.arange(zlo,zhi)[:,None]*H+H*np.asarray(fractions)[None,:]-b[2]
    zhit=(zz>=0)&(zz<=b[5])
    sl=np.s_[zlo:zhi,lower[1]:upper[1],lower[0]:upper[0]]
    full[sl]=zhit.all(1)[:,None,None]&xyall[None]
    anyhit[sl]=zhit.any(1)[:,None,None]&xyany[None]
    return full,anyhit


def closed_box_masks(box):
    """Independent yaw-OBB/AABB SAT (world x,y and box u,v), exact Z overlap.

    Contact uses 1e-10 m numerical slack, not the face-assignment tolerance.
    Full interior tests all 8 voxel corners by projected interval containment.
    """
    import numpy as np
    b=np.asarray(box,dtype=np.float64);c,s=b[6:8]
    centre=b[:2]+np.array([c*b[3]/2-s*b[4]/2,s*b[3]/2+c*b[4]/2])
    radius=np.array([abs(c)*b[3]/2+abs(s)*b[4]/2,abs(s)*b[3]/2+abs(c)*b[4]/2])
    lo=np.maximum(0,np.floor((centre-radius-np.array(ORIGIN[:2]))/H).astype(int)-1)
    hi=np.minimum(200,np.ceil((centre+radius-np.array(ORIGIN[:2]))/H).astype(int)+1)
    full=np.zeros(SHAPE,bool);contact=full.copy()
    if (hi<=lo).any():return full,contact
    yy,xx=np.meshgrid(np.arange(lo[1],hi[1]),np.arange(lo[0],hi[0]),indexing='ij')
    dx=-5+(xx+.5)*H-centre[0];dy=-5+(yy+.5)*H-centre[1]
    u=dx*c+dy*s;v=-dx*s+dy*c;rv=H/2*(abs(c)+abs(s));e=1e-10
    touch=(abs(dx)<=radius[0]+H/2+e)&(abs(dy)<=radius[1]+H/2+e)&(abs(u)<=b[3]/2+rv+e)&(abs(v)<=b[4]/2+rv+e)
    inside=(abs(u)+rv<=b[3]/2+e)&(abs(v)+rv<=b[4]/2+e)
    z=(np.arange(32)+.5)*H
    ztouch=(z+H/2>=b[2]-e)&(z-H/2<=b[2]+b[5]+e)
    zinside=(z-H/2>=b[2]-e)&(z+H/2<=b[2]+b[5]+e)
    sl=np.s_[:,lo[1]:hi[1],lo[0]:hi[0]]
    contact[sl]=ztouch[:,None,None]&touch[None]
    full[sl]=zinside[:,None,None]&inside[None]
    return full,contact


def independent_cells(xyz,version):
    """NumPy candidate enumeration independent of torch scene implementation."""
    import itertools
    import numpy as np
    f=(np.asarray(xyz,dtype=np.float64)-np.asarray(ORIGIN))/H
    occ=np.zeros(SHAPE,bool)
    if version=='v2':
        ix=np.minimum(np.floor(f+.001).astype(np.int64),np.array(SHAPE[::-1])-1)
        occ[ix[:,2],ix[:,1],ix[:,0]]=True;return occ
    nearest=np.floor(f+.5).astype(np.int64)
    face=np.abs(f-nearest)<.001
    lower=np.where(face,nearest-1,np.floor(f).astype(np.int64))
    for choice in itertools.product((0,1),repeat=3):
        ch=np.array(choice);valid=(face|(ch==0)).all(1)
        ix=lower+ch
        valid &= ((ix>=0)&(ix<np.array(SHAPE[::-1]))).all(1)
        ix=ix[valid];occ[ix[:,2],ix[:,1],ix[:,0]]=True
    return occ


def object_boxes(side):
    """Match explicit primitive signatures; never infer correspondence by proximity."""
    import numpy as np
    boxes=np.asarray(side['boxes'],dtype=np.float64)
    rows=[]
    for i,obj in enumerate(side['objects']):
        theta=float(obj.get('theta',0));c,s=np.cos(theta),np.sin(theta)
        entries=[]
        if obj.get('parts'):
            for part in obj['parts']:
                offset=np.asarray(part['offset'],dtype=float)
                pos=np.asarray(obj['position'],dtype=float)+[c*offset[0]-s*offset[1],s*offset[0]+c*offset[1],offset[2]]
                angle=theta+float(part.get('theta',0))
                entries.append((part.get('name'),[*pos,*part['size'],np.cos(angle),np.sin(angle)]))
        elif 'size' in obj:entries=[(None,[*obj['position'],*obj['size'],c,s])]
        ids=[];parts=[]
        for name,signature in entries:
            hits=np.flatnonzero(np.isclose(boxes,signature,atol=1e-9,rtol=0).all(1)).tolist()
            parts.append(dict(name=name,box_indices=hits,status='unique' if len(hits)==1 else 'ambiguous' if hits else 'unknown'))
            ids+=hits
        rows.append(dict(object_index=i,name=obj.get('name'),category=obj.get('category'),box_indices=sorted(set(ids)),parts=parts,
                         mapping_complete=bool(parts) and all(p['status']=='unique' for p in parts)))
    return rows


def metrics(occ,full,anyhit):
    hole=full&~occ;spur=occ&~anyhit
    # holeXY = a required column missing all occupied height, spurXY = occupied
    # XY column entirely outside the ANY-subsample reference projection.
    return dict(occupied=int(occ.sum()),reference_full=int(full.sum()),reference_any=int(anyhit.sum()),
                hole=int(hole.sum()),holeXY=int((full.any(0)&~occ.any(0)).sum()),
                spur=int(spur.sum()),spurXY=int((occ.any(0)&~anyhit.any(0)).sum()))


def wall_depth(base,boxes):
    """SRC-1081: all forward wall rays, earliest depth-H point, maximum depth.

    Depth is min perpendicular distance to the six OBB faces. Its maximum
    along a chord is attained at an endpoint or a crossing of two face lines.
    No sensor range or historical leak/chord filter is used here.
    """
    import numpy as np
    yaw=(np.arange(360)+.5)*np.pi/180+base[2]
    pitch=(np.arange(90)+.5)*np.pi/180-np.pi/4
    az,el=np.meshgrid(yaw,pitch)
    d=np.stack([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)],-1).reshape(-1,3)
    o=np.array([base[0],base[1],.5]);best=np.full(len(d),np.inf)
    exit_distance=best.copy();owner=np.full(len(d),-1,dtype=int)
    deep_at=best.copy();deep_owner=owner.copy();maximum=np.zeros(len(d))
    for wall_index,b in enumerate(boxes):
        b=np.asarray(b);delta=o-b[:3]
        oo=np.array([delta[0]*b[6]+delta[1]*b[7],-delta[0]*b[7]+delta[1]*b[6],delta[2]])
        dd=np.column_stack([d[:,0]*b[6]+d[:,1]*b[7],-d[:,0]*b[7]+d[:,1]*b[6],d[:,2]])
        parallel=dd==0;den=np.where(parallel,1,dd)
        def interval(inset):
            a=(inset-oo)/den;z=(b[3:6]-inset-oo)/den
            near=np.where(parallel,-np.inf,np.minimum(a,z)).max(1).clip(0)
            far=np.where(parallel,np.inf,np.maximum(a,z)).min(1)
            valid=(near<=far)&~(parallel&((oo<inset)|(oo>b[3:6]-inset))).any(1)
            return near,far,valid
        near,far,valid=interval(0.)
        update=valid&(near<best)
        best[update]=near[update];exit_distance[update]=far[update];owner[update]=wall_index
        dn,df,dok=interval(H);dok &= (b[3:6]>=2*H).all()
        update=dok&(dn<deep_at);deep_at[update]=dn[update];deep_owner[update]=wall_index
        ix=np.flatnonzero(valid)
        if len(ix):
            slopes=np.concatenate([dd[ix],-dd[ix]],axis=1)
            intercept=np.concatenate([oo,b[3:6]-oo])
            lo=near[ix];hi=far[ix]
            values=lambda t:np.min(intercept[None,:]+slopes*t[:,None],axis=1)
            md=np.maximum(values(lo),values(hi))
            for j in range(6):
                for k in range(j):
                    den2=slopes[:,j]-slopes[:,k]
                    t=np.divide(intercept[k]-intercept[j],den2,out=lo.copy(),where=den2!=0)
                    md=np.maximum(md,values(np.clip(t,lo,hi)))
            maximum[ix]=np.maximum(maximum[ix],np.maximum(md,0))
    candidate=np.isfinite(best);eligible=np.isfinite(deep_at)
    chord=np.zeros(len(d));chord[candidate]=exit_distance[candidate]-best[candidate]
    entry_z=np.full(len(d),np.nan);entry_z[candidate]=.5+best[candidate]*d[candidate,2]
    return best,eligible,dict(candidate=candidate,chord=chord,entry_z=entry_z,wall_index=owner,far=exit_distance,
        deep_at=deep_at,deep_wall_index=deep_owner,max_depth=maximum)


def unbounded_voxel_depth(occupancy,base,candidate):
    """Diagnostic-only NumPy DDA: first occupied cell until domain exit, no range cap.

    Ground and the production PcdPanorama are not part of this voxel query.
    Only explicitly selected analytic wall candidates are queried; no range cap.
    """
    import numpy as np
    yaw=(np.arange(360)+.5)*np.pi/180+base[2]
    pitch=(np.arange(90)+.5)*np.pi/180-np.pi/4
    az,el=np.meshgrid(yaw,pitch)
    directions=np.stack([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)],-1).reshape(-1,3)
    ids=np.flatnonzero(candidate);d=directions[ids];o=np.array([base[0],base[1],.5])
    result=np.full(len(candidate),np.inf)
    cell=np.broadcast_to(np.floor((o-ORIGIN)/H).astype(int),(len(ids),3)).copy()
    step=np.sign(d).astype(int);den=np.where(d==0,1,d)
    boundary=np.asarray(ORIGIN)+(cell+(step>0))*H
    next_t=np.where(d==0,np.inf,(boundary-o)/den)
    delta=np.where(d==0,np.inf,H/np.abs(den));entry=np.zeros(len(ids))
    active=((cell>=0)&(cell<np.array(SHAPE[::-1]))).all(1)
    for _ in range(sum(SHAPE)+3):
        a=np.flatnonzero(active)
        if not len(a):break
        c=cell[a];hit=occupancy[c[:,2],c[:,1],c[:,0]]
        result[ids[a[hit]]]=entry[a[hit]];active[a[hit]]=False
        a=a[~hit]
        if not len(a):continue
        crossing=next_t[a].min(1);axes=next_t[a]<=crossing[:,None]
        cell[a]+=axes*step[a];next_t[a]+=axes*delta[a];entry[a]=crossing
        active[a]=((cell[a]>=0)&(cell[a]<np.array(SHAPE[::-1]))).all(1)
    else:raise RuntimeError('diagnostic DDA exceeded domain crossing bound')
    return result


def geometry(a,rec,out):
    import numpy as np
    import torch
    from task8_sim.assets import load_asset
    from task8_sim.scene import VoxelScene,SceneBatch
    from task8_sim.perception import PcdPanorama
    torch.set_num_threads(1)
    asset=load_asset(a.manifest,a.map_id)
    rec['hashes']=asset.hashes;rec['point_count']=len(asset.xyz)
    rec['stage']='voxelize';dump(out,rec)
    old=module(a.v2_snapshot,'task8_v2_snapshot')
    if old.BACKEND!='pcd-voxel-v2':raise ValueError('wrong v2 snapshot')
    v2=old.VoxelScene.from_asset(asset,device=a.device,dtype=torch.float64)
    v3=VoxelScene.from_asset(asset,device=a.device,dtype=torch.float64)
    if v3.provenance()['backend']!='pcd-voxel-v3':raise ValueError('S1 v3 not active')
    strict=independent_cells(asset.xyz,'v2')
    occ1=v2.occupancy.cpu().numpy();occ2=v3.occupancy.cpu().numpy()
    if not np.array_equal(strict,occ1):raise ValueError('v2 snapshot differs from independent epsilon assignment')
    if not np.array_equal(independent_cells(asset.xyz,'v3'),occ2):raise ValueError('v3 differs from independent closed-face enumeration')
    rec['provenance']={'v2':v2.provenance(),'v3':v3.provenance()}
    rec['stage']='json_reference';dump(out,rec)
    side=asset.semantics;mapping=object_boxes(side)
    full=np.zeros(SHAPE,bool);anyhit=full.copy();closed=full.copy();interior=full.copy();boxstats=[]
    for i,box in enumerate(side['boxes']):
        ff,aa=box_masks(box);full|=ff;anyhit|=aa
        ii,cc=closed_box_masks(box);closed|=cc;interior|=ii
        boxstats.append(dict(box_index=i,box=box,
            v2=dict(interior_cells=int(ff.sum()),hole=int((ff&~occ1).sum()),holeXY=int((ff.any(0)&~occ1.any(0)).sum())),
            v3=dict(interior_cells=int(ff.sum()),hole=int((ff&~occ2).sum()),holeXY=int((ff.any(0)&~occ2.any(0)).sum()),
                exact_interior_cells=int(ii.sum()),exact_interior_hole=int((ii&~occ2).sum()),
                hole_cells_zyx=np.argwhere(ff&~occ2).tolist(),exact_hole_cells_zyx=np.argwhere(ii&~occ2).tolist()),
            closed_contact_cells=int(cc.sum())))
    # Attribute GLOBAL spurs only within a box's one-voxel-expanded AABB.
    # Overlapping AABBs can share spurs; these per-box counts are not additive.
    for row in boxstats:
        b=np.asarray(row['box']);corners=np.array([[x,y,z] for x in (0,b[3]) for y in (0,b[4]) for z in (0,b[5])])
        corners[:,:2]=corners[:,:2]@np.array([[b[6],b[7]],[-b[7],b[6]]]);corners+=b[:3]
        lower=np.maximum(0,np.floor((corners.min(0)-np.array(ORIGIN))/H).astype(int)-1)
        upper=np.minimum(np.array(SHAPE[::-1]),np.ceil((corners.max(0)-np.array(ORIGIN))/H).astype(int)+1)
        sl=np.s_[lower[2]:upper[2],lower[1]:upper[1],lower[0]:upper[0]]
        row['spur_roi_xyz_indices']=[lower.tolist(),upper.tolist()]
        for version,occ in [('v2',occ1),('v3',occ2)]:
            row[version]['global_spur_in_expanded_aabb']=int((occ[sl]&~anyhit[sl]).sum())
            row[version]['global_outside_closed_contact_in_expanded_aabb']=int((occ[sl]&~closed[sl]).sum())
    # Object residual is deficit in its own reference. Global spur stays global;
    # per-object outside count above is intentionally labelled by box, not a
    # causal assignment of all occupancy elsewhere to this object.
    for obj in mapping:
        obj['v2_hole']=sum(boxstats[i]['v2']['hole'] for i in obj['box_indices'])
        obj['v3_hole']=sum(boxstats[i]['v3']['hole'] for i in obj['box_indices'])
        obj['v3_exact_interior_hole']=sum(boxstats[i]['v3']['exact_interior_hole'] for i in obj['box_indices'])
        obj['v3_nearby_outside_closed_contact_nonadditive']=sum(boxstats[i]['v3']['global_outside_closed_contact_in_expanded_aabb'] for i in obj['box_indices'])
        obj['v3_nearby_global_spur_nonadditive']=sum(boxstats[i]['v3']['global_spur_in_expanded_aabb'] for i in obj['box_indices'])
        # These flags are evidence for subsequent S3 interpretation, not a
        # claim that a geometric property proves the source of a residual.
        flags=[]
        for i in obj['box_indices']:
            b=np.asarray(side['boxes'][i]);angle=np.arctan2(b[7],b[6])
            if abs(b[7])>1e-7 or b[6]<0:flags.append('rotation')
            frac=np.mod((b[:3]-np.array(ORIGIN))/H,1)
            if np.any(np.abs(frac-.5)<1e-5):flags.append('half_grid_offset')
            corners=np.array([[x,y,z] for x in (0,b[3]) for y in (0,b[4]) for z in (0,b[5])])
            corners[:,:2]=corners[:,:2]@np.array([[b[6],b[7]],[-b[7],b[6]]]);corners+=b[:3]
            if ((corners<np.array(ORIGIN))|(corners>np.array([5,5,1.6]))).any():flags.append('clipping')
        obj['candidate_residual_mechanisms']=sorted(set(flags)) or ['other_requires_review']
    walls=[o for o in mapping if o['category']=='wall']
    if not walls or any(not o['mapping_complete'] for o in walls):raise ValueError('incomplete wall correspondence')
    rec['metrics']={'v2':metrics(occ1,full,anyhit),'v3':metrics(occ2,full,anyhit)}
    rec['objects']=mapping;rec['boxes']=boxstats
    rec['closed_contact_audit']={v:dict(outside_count=int((occ&~closed).sum()),outside_cells_zyx=np.argwhere(occ&~closed).tolist(),
        subsample_spur_inside_closed_contact=int((occ&~anyhit&closed).sum())) for v,occ in [('v2',occ1),('v3',occ2)]}
    rec['spur_contact_pass']=rec['closed_contact_audit']['v3']['outside_count']==0
    rec['wall_interior_pass']=all(o['v3_hole']==0 and o['v3_exact_interior_hole']==0 for o in walls)
    # Store masks to make independent residual classification/review possible.
    np.savez_compressed(Path(a.output)/(a.map_id+'-geometry.npz'),v2=occ1,v3=occ2,reference_full=full,reference_any=anyhit,closed_contact=closed,exact_interior=interior)
    rec['stage']='real_panorama';dump(out,rec)
    oldrec=json.loads((Path(a.old_runtime)/(a.map_id+'-runtime.json')).read_text())
    base=oldrec['initial_state']['base'][0]
    wallids=sorted({i for o in walls for i in o['box_indices']})
    expected,eligible,wallinfo=wall_depth(base,[side['boxes'][i] for i in wallids])
    sensor=json.loads(Path('config/task8/sensor.json').read_text())
    arrays={'expected_wall_m':expected,'wall_eligible':eligible,'base':np.array(base)}
    for version,scene,batch in [('v2',v2,old.SceneBatch),('v3',v3,SceneBatch)]:
        bt=torch.tensor([base],device=a.device,dtype=torch.float64)
        depth=PcdPanorama(batch([scene]),sensor_config=sensor)(bt,torch.empty((1,0,7),device=a.device,dtype=torch.float64))
        arrays[version+'_depth']=depth.distance.cpu().numpy().reshape(-1)
        arrays[version+'_valid']=depth.valid.cpu().numpy()
    for v,occ in [('v2',occ1),('v3',occ2)]:
        arrays[v+'_unbounded_voxel_depth']=unbounded_voxel_depth(occ,base,wallinfo['candidate'])
    classify_panorama(rec,arrays,expected,eligible,wallinfo,wallids)
    np.savez_compressed(Path(a.output)/(a.map_id+'-panorama.npz'),**arrays)
    rec['status']='geometry_checked';rec['stage']='geometry_complete';rec['geometry_elapsed_s']=time.monotonic()-START;dump(out,rec)
    return rec['geometry_gate']=='passed'


def classify_panorama(rec,arrays,expected,eligible,info,wallids):
    """SRC-1081: every deep-wall ray must hit by earliest depth-H point."""
    import numpy as np
    shell=info['candidate']&~eligible
    names={i:[o['name'] for o in rec['objects'] if i in o['box_indices'] and o['category']=='wall'] for i in wallids}
    def row(p):
        box_id=wallids[int(info['wall_index'][p])]
        deep_id=int(info['deep_wall_index'][p])
        return dict(pixel=[int(p//360),int(p%360)],box_index=box_id,wall_names=names[box_id],
            deep_box_index=wallids[deep_id] if deep_id>=0 else None,
            max_wall_depth_m=float(info['max_depth'][p]),deep_entry_m=float(info['deep_at'][p]),
            chord_m=float(info['chord'][p]),entry_z_m=float(info['entry_z'][p]),d_a_m=float(expected[p]),
            exit_distance_m=float(info['far'][p]),
            **{v:dict(d_v_m=float(arrays[v+'_unbounded_voxel_depth'][p]),
                production_6m_depth_m=float(arrays[v+'_depth'][p]),
                deep_wall_miss=bool(eligible[p] and arrays[v+'_unbounded_voxel_depth'][p]>info['deep_at'][p])) for v in ('v2','v3')})
    scans={};leaks=np.zeros(len(expected),bool)
    for v in ('v2','v3'):
        actual=arrays[v+'_unbounded_voxel_depth'];leak=eligible&(actual>info['deep_at']);leaks|=leak
        scans[v]=dict(ray_count=len(actual),candidate_wall_rays=int(info['candidate'].sum()),deep_wall_rays=int(eligible.sum()),
            deep_wall_misses=int(leak.sum()),shell_rays=int(shell.sum()),shell_no_voxel_hit=int((shell&np.isinf(actual)).sum()),
            deep_entry_beyond_6m=int((eligible&(info['deep_at']>6)).sum()),ratio_all_rays=float(leak.mean()))
    values=info['max_depth'][shell];bins=[0,.01,.02,.03,.04,.05]
    arrays.update(expected_wall_m=expected,wall_eligible=eligible,wall_candidate=info['candidate'],wall_chord_m=info['chord'],
        wall_entry_z_m=info['entry_z'],wall_box_index=np.where(info['wall_index']>=0,np.array(wallids)[np.maximum(info['wall_index'],0)],-1),
        wall_deep_entry_m=info['deep_at'],wall_max_depth_m=info['max_depth'],wall_deep_box_index=np.where(info['deep_wall_index']>=0,np.array(wallids)[np.maximum(info['deep_wall_index'],0)],-1))
    rec['panorama']=dict(base=arrays['base'].tolist(),depth_threshold_m=H,authorization='SRC-1081',
        diagnostic_depth='unbounded first occupied voxel; original production 6m depths retained',
        eligibility='any forward analytic wall reaches nearest-face depth >=0.05m; no range/ground/chord prefilter',
        shell_count=int(shell.sum()),shell_depth_minmax_m=[float(values.min()),float(values.max())] if len(values) else None,
        shell_depth_histogram=dict(edges_m=bins,counts=np.histogram(values,bins)[0].tolist()),
        shell_rows=[row(p) for p in np.flatnonzero(shell)],deep_wall_miss_rows=[row(p) for p in np.flatnonzero(leaks)],versions=scans)
    rec['wall_panorama_pass']=scans['v3']['deep_wall_misses']==0
    rec['geometry_gate']='passed' if rec['wall_interior_pass'] and rec['wall_panorama_pass'] else 'failed_geometry_hard_gate'


def reclassify_saved(a,rec):
    """Read saved arrays/JSON only: never load PCD or invoke scene/sensor."""
    import numpy as np
    source=Path(a.reclassify_from)
    old=json.loads((source/(a.map_id+'-geometry.json')).read_text())
    saved=np.load(Path(a.saved_panorama_from or source)/(a.map_id+'-panorama.npz'))
    arrays={k:saved[k] for k in saved.files}
    rec.update(old);rec['r4_saved_source']=str(source)
    rec['runtime_gate']=old.get('runtime_gate','not_run')
    walls=[o for o in rec['objects'] if o['category']=='wall']
    wallids=sorted({i for o in walls for i in o['box_indices']})
    box_lookup={b['box_index']:b['box'] for b in rec['boxes']}
    expected,eligible,info=wall_depth(arrays['base'],[box_lookup[i] for i in wallids])
    # Existing unbounded DDA is valid only on its saved candidate mask.
    # Preserve it exactly and compute ONLY newly included all-range candidates.
    previous=arrays['wall_candidate'].copy()
    missing=info['candidate']&~previous
    if missing.any():
        masks=np.load(Path(a.saved_geometry_from or source)/(a.map_id+'-geometry.npz'))
        for v in ('v2','v3'):
            extra=unbounded_voxel_depth(masks[v],arrays['base'],missing)
            arrays[v+'_unbounded_voxel_depth'][missing]=extra[missing]
    rec['r4_new_unbounded_rays']=int(missing.sum())
    classify_panorama(rec,arrays,expected,eligible,info,wallids)
    rec['r4_method']='saved panorama/DDA; DDA only for newly included all-range candidates; no PCD voxelization or sensor'
    rec['r4_diagnostic_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    np.savez_compressed(Path(a.output)/(a.map_id+'-panorama.npz'),**arrays)
    return rec['geometry_gate']=='passed'


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--map-id',required=True)
    p.add_argument('--output',required=True);p.add_argument('--v2-snapshot',required=True);p.add_argument('--old-runtime',required=True)
    p.add_argument('--device',choices=('cpu','cuda:0'),default='cpu');p.add_argument('--max-wall-s',type=float,default=28.5)
    p.add_argument('--reclassify-from');p.add_argument('--reclassify-only',action='store_true');p.add_argument('--runtime-only-from');p.add_argument('--saved-geometry-from');p.add_argument('--saved-panorama-from')
    a=p.parse_args();outdir=Path(a.output);outdir.mkdir(parents=True,exist_ok=True);out=outdir/(a.map_id+'-geometry.json')
    if out.exists():raise FileExistsError(out)
    rec=dict(map_id=a.map_id,status='running',stage='imports',geometry_gate='not_run',runtime_gate='not_run',requested_device=a.device,
             method='independent JSON 5^3 subcell centres plus exact closed OBB/AABB SAT; independent NumPy assignments; PCD-only v2/v3 scenes',max_wall_s=a.max_wall_s,
             implementation_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),Path(a.v2_snapshot),Path('src/task8_sim/scene.py'),Path('src/task8_sim/assets.py'),Path('src/task8_sim/env.py'),Path('src/task8_sim/perception.py'),Path('config/task8/sensor.json'),Path('config/task8/environment.json'),Path('scripts/task8_map_diagnostics.py'),Path(a.manifest)]})
    class TimedOut(BaseException):pass
    def alarm(*_):raise TimedOut()
    signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,max(.001,a.max_wall_s-(time.monotonic()-START)))
    try:
        if a.runtime_only_from:
            rec=json.loads(Path(a.runtime_only_from).read_text())
            if rec['geometry_gate']!='passed':raise ValueError('runtime requires passed geometry')
        elif a.reclassify_from:
            if not reclassify_saved(a,rec):return 2
            if a.reclassify_only:return 0
        elif not geometry(a,rec,out):return 2
        remaining=a.max_wall_s-(time.monotonic()-START)
        if remaining<=1:rec['runtime_gate']='budget_exhausted';dump(out,rec);return 124
        # Reuse the exact default-sampler/action/classification implementation.
        runtime=module('scripts/task8_map_diagnostics.py','task8_runtime_diagnostic')
        sys.argv=['task8_map_diagnostics.py','--manifest',a.manifest,'--map-id',a.map_id,'--stage','runtime',
                  '--output',a.output,'--device',a.device,'--seed','20261026','--max-wall-s',str(remaining)]
        rc=runtime.main();rec['runtime_exit_code']=rc
        actual=json.loads((outdir/(a.map_id+'-runtime.json')).read_text())
        historical=json.loads((Path(a.old_runtime)/(a.map_id+'-runtime.json')).read_text())
        rec['runtime_gate']=actual.get('runtime_gate','not_run')
        rec['sampling_comparison']=dict(v1=historical.get('sampling'),v3=actual.get('sampling'),
            limitation='same seed and proposal contract; historical v1 cuda float32 versus v3 CPU float32; do not attribute all differences solely to occupancy')
        return rc
    except TimedOut:
        rec['status']='stage_timeout';rec['interrupted_stage']=rec['stage'];return 124
    except Exception as exc:
        rec['status']='error';rec['error']=f'{type(exc).__name__}: {exc}';rec['traceback']=traceback.format_exc();return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);rec['total_elapsed_s']=time.monotonic()-START;dump(out,rec)


if __name__=='__main__':raise SystemExit(main())
