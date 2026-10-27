#!/usr/bin/env python3
"""Authorized task8.9.2 S3 cube-export-v2 (SRC-1161).

Source corner OBB semantics and fixture sampling remain unchanged. No mapgen,
training, production mutation or GPU use. Evidence: SRC-1160 / SRC-1120 onward.
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DOMAIN={'min':[-5,-5,0],'max':[5,5,1.6],'upper_exclusive':True}
SHAPE=(32,200,200)
ORIGIN=np.array([-5.,-5.,0.])
H=.05
EXPORT='cube-export-v2'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');tmp.replace(path)

def sample_corner_box(box):
    b=np.asarray(box,dtype=np.float64)
    if b.shape!=(8,) or not np.isfinite(b).all() or (b[3:6]<=0).any() or not np.isclose(b[6]**2+b[7]**2,1,atol=1e-8,rtol=0):raise ValueError('invalid corner box')
    counts=np.maximum(1,np.ceil(b[3:6]/.05).astype(int))
    axes=[(np.arange(n)+.5)*s/n for s,n in zip(b[3:6],counts)]
    points=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1).reshape(-1,3)
    points[:,:2]=points[:,:2]@np.array([[b[6],b[7]],[-b[7],b[6]]])
    return points+b[:3]

def valid_points(xyz):
    if xyz.ndim!=2 or xyz.shape[1]!=3 or not len(xyz) or not np.isfinite(xyz).all():raise ValueError('invalid XYZ')
    if ((xyz<np.array(DOMAIN['min']))|(xyz>=np.array(DOMAIN['max']))).any():raise ValueError('outside half-open domain')

def target_cells(box,return_details=False):
    """O=A union B; B uses mathematical closed faces, never production tau."""
    b=np.asarray(box,dtype=np.float64);samples=sample_corner_box(b)
    occ=np.zeros(SHAPE,bool)
    corners=np.array([[x,y,z] for x in (0,b[3]) for y in (0,b[4]) for z in (0,b[5])])
    corners[:,:2]=corners[:,:2]@np.array([[b[6],b[7]],[-b[7],b[6]]]);corners+=b[:3]
    lo=np.maximum(0,np.floor((corners.min(0)-ORIGIN)/H).astype(int)-1)
    hi=np.minimum(np.array(SHAPE[::-1]),np.ceil((corners.max(0)-ORIGIN)/H).astype(int)+1)
    if (hi>lo).all():
        z,y,x=np.meshgrid(np.arange(lo[2],hi[2]),np.arange(lo[1],hi[1]),np.arange(lo[0],hi[0]),indexing='ij')
        dx=ORIGIN[0]+(x+.5)*H-b[0];dy=ORIGIN[1]+(y+.5)*H-b[1];dz=(z+.5)*H-b[2]
        u=dx*b[6]+dy*b[7];v=-dx*b[7]+dy*b[6]
        inside=(u>=0)&(u<=b[3])&(v>=0)&(v<=b[4])&(dz>=0)&(dz<=b[5])
        occ[z[inside],y[inside],x[inside]]=True
    f=(samples-ORIGIN)/H;ix=np.floor(f).astype(np.int64)
    # Exact coordinate-to-world-face equality avoids treating nearby samples
    # as face points. Both neighbours are included only for a closed face.
    near=np.rint(f).astype(np.int64)
    face_residual=np.abs(samples-(ORIGIN+near*H))
    # Float64 forward/back grid arithmetic involves subtraction/division and
    # multiplication/addition at |world|<=5m. Bound 16 eps*5 = 1.78e-14m;
    # far below the unchanged production face tolerance 5e-5m. This only
    # reconciles representations of an exact mathematical grid face.
    face_slack=16*np.finfo(np.float64).eps*max(1.,float(np.abs(ORIGIN).max()),float(np.abs(samples).max()))
    face=face_residual<=face_slack
    import itertools
    for choice in itertools.product((0,1),repeat=3):
        ch=np.array(choice);valid=(face|(ch==0)).all(1)
        cells=np.where(face,near-ch,ix)
        valid &= ((cells>=0)&(cells<np.array(SHAPE[::-1]))).all(1)
        cells=cells[valid];occ[cells[:,2],cells[:,1],cells[:,0]]=True
    if not occ.any():raise ValueError('box has no in-domain target cell')
    if return_details:return occ,dict(face_numeric_slack_m=face_slack,max_assigned_face_residual_m=float(face_residual[face].max()) if face.any() else 0.)
    return occ

def production_occupancy(xyz,entry,side):
    sys.path.insert(0,str(ROOT/'src'))
    import torch
    from task8_sim.assets import MapAsset
    from task8_sim.scene import VoxelScene
    torch.set_num_threads(1)
    scene=VoxelScene.from_asset(MapAsset(entry['id'],xyz,entry,side,entry.get('sha256',{})),device='cpu',dtype=torch.float64)
    return scene.occupancy.numpy(),scene.provenance()

def export_one(args):
    source,output,row,generator=args;source=Path(source);output=Path(output)
    start=time.monotonic();src=source/row['path'];data=json.loads(src.read_text());srcsha=sha(src)
    if data['metadata']['seed']!=row['seed'] or data['metadata']['difficulty']!=row['difficulty']:raise ValueError('source index metadata mismatch')
    pcd=output/'maps'/(row['id']+'.pcd');side=output/'sidecars'/(row['id']+'.json');rec=output/'records'/(row['id']+'.json')
    if rec.exists():
        entry=json.loads(rec.read_text())
        if sha(pcd)!=entry['sha256']['pcd'] or sha(side)!=srcsha or entry['source_json_sha256']!=srcsha or entry['generator_sha256']!=generator or entry.get('export_protocol')!=EXPORT:raise ValueError('resume identity mismatch')
        return entry
    if pcd.exists() or side.exists():raise ValueError('incomplete existing asset; preserve and investigate')
    target=np.zeros(SHAPE,bool);per_box=[];numerics=[]
    for box in data['boxes']:
        own,numeric=target_cells(box,True);target|=own;per_box.append(int(own.sum()));numerics.append(numeric)
    xyz=ORIGIN+(np.argwhere(target)[:,::-1]+.5)*H;valid_points(xyz)
    pcd.parent.mkdir(parents=True,exist_ok=True);side.parent.mkdir(parents=True,exist_ok=True)
    tmp=pcd.with_suffix('.pcd.tmp')
    with tmp.open('x') as f:
        f.write(f'VERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH {len(xyz)}\nHEIGHT 1\nPOINTS {len(xyz)}\nDATA ascii\n')
        np.savetxt(f,xyz,fmt='%.12g')
    # Use the real strict production parser and real scene for every graph.
    sys.path.insert(0,str(ROOT/'src'))
    from task8_sim.assets import _read_pcd
    persisted=_read_pcd(tmp,row['id']);valid_points(persisted)
    if persisted.shape!=xyz.shape or not np.allclose(persisted,xyz,atol=5e-11,rtol=0):raise ValueError('persisted coordinate mismatch')
    prod,provenance=production_occupancy(persisted,row,data)
    if not np.array_equal(prod,target):raise ValueError('production v3 differs from target O')
    tmp.rename(pcd);side.write_bytes(src.read_bytes())
    entry=dict(id=row['id'],pcd_path=str(pcd.relative_to(output)),sidecar_path=str(side.relative_to(output)),sha256={'pcd':sha(pcd),'sidecar':sha(side)},split=row['split'],difficulty=row['difficulty'],seed=row['seed'],source_json_path=str(src.relative_to(ROOT)),source_json_sha256=srcsha,source_generator=data['metadata']['generator_version'],generator_sha256=generator,frame_id='world',length_unit='m',resolution_m=.05,point_representation='solid_volume_samples',bounds=DOMAIN,geometry_backend='pcd-voxel-v3',semantic_policy_input=False,point_count=len(persisted),coordinate_min=persisted.min(0).tolist(),coordinate_max=persisted.max(0).tolist(),bytes=pcd.stat().st_size,export_wall_s=time.monotonic()-start)
    entry.update(export_protocol=EXPORT,per_box_target_counts=per_box,production_target_equal=True,occupied=int(prod.sum()),target_sha256=hashlib.sha256(target.tobytes()).hexdigest(),production_provenance=provenance,per_box_numerics=numerics)
    dump(rec,entry);return entry

def load_diag():
    spec=importlib.util.spec_from_file_location('task8_diagnostics',ROOT/'scripts/task8_voxel_diagnostics.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d);return d

def audit_one(args):
    output,entry=args;output=Path(output);start=time.monotonic()
    sys.path.insert(0,str(ROOT/'src'))
    import torch
    from task8_sim.assets import MapAsset,_read_pcd
    from task8_sim.scene import VoxelScene
    torch.set_num_threads(1)
    d=load_diag();src=output/entry['sidecar_path'];side=json.loads(src.read_text());xyz=_read_pcd(output/entry['pcd_path'],entry['id']);valid_points(xyz)
    asset=MapAsset(entry['id'],xyz,entry,side,entry['sha256'])
    scene=VoxelScene.from_asset(asset,device='cpu',dtype=torch.float64);occ=scene.occupancy.numpy()
    independent=d.independent_cells(xyz,'v3')
    if not np.array_equal(occ,independent):raise ValueError('production/independent occupancy mismatch')
    objects=[];walls=[];target=np.zeros(SHAPE,bool);closed_union=target.copy()
    for i,(b,meta) in enumerate(zip(side['boxes'],side['box_metadata'])):
        full,anyhit=d.box_masks(b);exact,contact=d.closed_box_masks(b);own=target_cells(b);target|=own;closed_union|=contact
        sampled_holes=int((full&~occ).sum());exact_holes=int((exact&~occ).sum())
        objects.append(dict(index=i,category=meta['category'],name=meta['name'],sampled_internal_holes=sampled_holes,exact_internal_holes=exact_holes,reference_sampled_full=int(full.sum()),reference_exact_full=int(exact.sum()),own_target_cells=int(own.sum()),own_outside_closed_supercover=int((own&~contact).sum())))
        if meta['category']=='wall':walls.append(b)
    # Same 360x90 pixel-centre directions and 0.05 m inset as task8.8/SRC1081.
    base=[0.,0.,0.];_,eligible,info=d.wall_depth(base,walls)
    first=d.unbounded_voxel_depth(occ,base,info['candidate'])
    misses=eligible&(~np.isfinite(first)|(first>info['deep_at']+1e-9))
    shell=info['candidate']&~eligible
    result=dict(id=entry['id'],split=entry['split'],difficulty=entry['difficulty'],source_json_sha256=entry['source_json_sha256'],pcd_sha256=entry['sha256']['pcd'],point_count=len(xyz),production_independent_equal=True,occupied=int(occ.sum()),objects=objects,sampled_internal_holes=sum(x['sampled_internal_holes'] for x in objects),exact_internal_holes=sum(x['exact_internal_holes'] for x in objects),wall_sampled_holes=sum(x['sampled_internal_holes'] for x in objects if x['category']=='wall'),wall_exact_holes=sum(x['exact_internal_holes'] for x in objects if x['category']=='wall'),deep_rays=int(eligible.sum()),deep_misses=int(misses.sum()),shell_rays=int(shell.sum()),shell_max_depth_m=float(info['max_depth'][shell].max()) if shell.any() else None,elapsed_s=time.monotonic()-start,provenance=scene.provenance())
    result.update(production_target_equal=bool(np.array_equal(occ,target)),outside_closed_supercover=int((occ&~closed_union).sum()),per_box_outside_closed_supercover=sum(r['own_outside_closed_supercover'] for r in objects),every_box_nonempty=all(r['own_target_cells']>=1 for r in objects),export_protocol=EXPORT)
    # SRC1161 replaces the historical 5^3 sampled-full approximation by exact.
    result['passed']=result['production_target_equal'] and result['exact_internal_holes']==result['deep_misses']==result['outside_closed_supercover']==result['per_box_outside_closed_supercover']==0 and result['every_box_nonempty']
    dump(output/'audit'/(entry['id']+'.json'),result);return result

def select(rows,n):
    groups={}
    for r in rows:groups.setdefault((r['split'],r['difficulty']),[]).append(r)
    selected=[]
    # Stable equally spaced coverage of all six split/difficulty strata.
    counts={'train':70,'validation':15,'test':15} if n==200 else None
    for key,group in sorted(groups.items()):
        group=sorted(group,key=lambda r:r['id']);k=counts[key[0]] if counts else min(len(group),max(1,n//len(groups)))
        selected.extend(group[i] for i in np.linspace(0,len(group)-1,k,dtype=int))
    return selected

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['pilot','profile','build','audit','finalize'],required=True);p.add_argument('--config',default=str(ROOT/'config/task8/pool_s3_v2.json'));p.add_argument('--budget-limit',type=float,required=True);p.add_argument('--timeout',type=int,default=300);p.add_argument('--offset',type=int,default=0);p.add_argument('--count',type=int);a=p.parse_args();start=time.monotonic()
    cfg=json.loads(Path(a.config).read_text());source=ROOT/cfg['source'];output=ROOT/cfg['output'];output.mkdir(parents=True,exist_ok=True)
    ledger=ROOT/cfg['ledger'];b=json.loads(ledger.read_text()) if ledger.exists() else {'run_id':cfg['run_id'],'used_wall_s':0.,'entries':[],'active':None}
    if b.get('active'):raise RuntimeError('ledger has active job; reconcile before retry')
    if b['used_wall_s']>=a.budget_limit:raise RuntimeError('budget exhausted')
    timeout=min(a.timeout,int(a.budget_limit-b['used_wall_s']))
    def expired(*_):raise TimeoutError('bounded job timed out')
    signal.signal(signal.SIGALRM,expired);signal.alarm(timeout)
    job={'mode':a.mode,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'pid':os.getpid(),'timeout_s':timeout,'argv':sys.argv};b['budget_limit_wall_s']=a.budget_limit;b['active']=job;dump(ledger,b)
    rc=1
    try:
        index=json.loads((source/'index.json').read_text());rows=index['maps'];counts=Counter(r['split'] for r in rows)
        if counts!={'train':10000,'validation':100,'test':200}:raise ValueError('unexpected source split counts')
        generator=sha(__file__);chosen=select(rows,6 if a.mode=='pilot' else cfg['profile_maps']) if a.mode in ('pilot','profile') else rows
        if a.mode=='build':
            pilot=json.loads((output/'pilot-audit-report.json').read_text())
            if not pilot['passed'] or pilot['generator_sha256']!=generator:raise ValueError('current exporter requires passed six-map pilot')
            chosen=rows[a.offset:a.offset+a.count if a.count is not None else None]
        if a.mode in ('pilot','profile','build'):
            with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:
                entries=list(pool.map(export_one,[(str(source),str(output),r,generator) for r in chosen],chunksize=1))
            report=dict(mode=a.mode,count=len(entries),wall_s=time.monotonic()-start,total_bytes=sum(r['bytes'] for r in entries),point_count=sum(r['point_count'] for r in entries),workers=cfg['workers'],generator_sha256=generator,source_index_sha256=sha(source/'index.json'))
            report['maps_per_s']=len(entries)/report['wall_s'];dump(output/(a.mode+'-report.json'),report)
            if a.mode=='pilot':
                audit_start=time.monotonic()
                with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:results=list(pool.map(audit_one,[(str(output),r) for r in entries],chunksize=1))
                audit=dict(count=len(results),passed=all(r['passed'] for r in results),failed=[r['id'] for r in results if not r['passed']],exact_internal_holes=sum(r['exact_internal_holes'] for r in results),deep_misses=sum(r['deep_misses'] for r in results),deep_rays=sum(r['deep_rays'] for r in results),per_box_outside_closed_supercover=sum(r['per_box_outside_closed_supercover'] for r in results),generator_sha256=generator,wall_s=time.monotonic()-audit_start)
                dump(output/'pilot-audit-report.json',audit)
                if not audit['passed']:raise ValueError('six-map pilot failed; do not build')
            if a.mode=='build':dump(output/('build-%05d-report.json'%a.offset),report)
        elif a.mode=='finalize':
                entries=[json.loads((output/'records'/(r['id']+'.json')).read_text()) for r in rows]
                if any(e['generator_sha256']!=generator or e.get('export_protocol')!=EXPORT or not e['production_target_equal'] or min(e['per_box_target_counts'])<1 for e in entries):raise ValueError('incomplete all-map gates')
                audit=json.loads((output/'audit-report.json').read_text())
                if not audit['passed'] or audit['count']<200:raise ValueError('200-map sample gate not passed')
                # Recheck identity/hash while publishing; coordinates/counts/scene were
                # verified from persisted bytes at export, whose hashes must match.
                for e in entries:
                    if sha(output/e['pcd_path'])!=e['sha256']['pcd'] or sha(output/e['sidecar_path'])!=e['source_json_sha256']:raise ValueError('publication hash mismatch')
                dump(output/'manifest.json',dict(schema_version='task8-pcd-v1',export_protocol=EXPORT,geometry_backend='pcd-voxel-v3',source_index_sha256=sha(source/'index.json'),source_generator=index['generator_version'],generator_sha256=generator,maps=entries))
                semantic=ROOT/cfg['semantic_manifest'];sem=json.loads(semantic.read_text())['maps']
                seed=lambda r,j: int(hashlib.sha256((cfg['run_id']+':'+r['id']+':'+str(j)).encode()).hexdigest()[:8],16)
                seeds={split:[dict(map_id=r['id'],episode_seed=seed(r,0),episode_index=0,stream_index=0,split=split) for r in sorted(entries,key=lambda r:r['id']) if r['split']==split] for split in ('validation','test')}
                seeds['semantic_transfer']=[dict(map_id=r['id'],episode_seed=seed(r,j),episode_index=j,stream_index=0,split='semantic_transfer') for r in sorted(sem,key=lambda r:r['id']) for j in range(4)]
                dump(output/'evaluation-seeds.json',dict(schema_version='task8-eval-seeds-v1',selection_use={'validation':'checkpoint selection','test':'held out, never used by validation','semantic_transfer':'migration only, never used by selection'},semantic_manifest=str(semantic.relative_to(ROOT)),semantic_manifest_sha256=sha(semantic),**seeds))
                report=dict(count=len(entries),passed=True,export_protocol=EXPORT,wall_s=time.monotonic()-start,total_bytes=sum(e['bytes'] for e in entries),point_count=sum(e['point_count'] for e in entries),splits=dict(Counter(e['split'] for e in entries)),generator_sha256=generator)
                dump(output/'final-report.json',report)
        else:
            chosen=select(rows,200);chosen=[json.loads((output/'records'/(r['id']+'.json')).read_text()) for r in chosen]
            dump(output/'audit-selection.json',dict(rule='six strata: train70,validation15,test15 per difficulty; evenly spaced lexicographic IDs, endpoints included',maps=[r['id'] for r in chosen]))
            with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:results=list(pool.map(audit_one,[(str(output),r) for r in chosen],chunksize=1))
            report=dict(count=len(results),passed=all(r['passed'] for r in results),failed=[r['id'] for r in results if not r['passed']],sampled_internal_holes=sum(r['sampled_internal_holes'] for r in results),exact_internal_holes=sum(r['exact_internal_holes'] for r in results),deep_rays=sum(r['deep_rays'] for r in results),deep_misses=sum(r['deep_misses'] for r in results),shell_rays=sum(r['shell_rays'] for r in results),per_box_outside_closed_supercover=sum(r['per_box_outside_closed_supercover'] for r in results),wall_s=time.monotonic()-start)
            dump(output/'audit-report.json',report)
            if not report['passed']:raise ValueError('geometry sample gate failed; preserve evidence')
        print(json.dumps(report,sort_keys=True),flush=True);rc=0
    finally:
        signal.alarm(0);elapsed=time.monotonic()-start;job.update(elapsed_wall_s=elapsed,exit_code=rc);b['entries'].append(job);b['used_wall_s']+=elapsed;b['active']=None;b['remaining_wall_s']=a.budget_limit-b['used_wall_s'];b['status']='r2_active' if rc==0 else 'r2_failed';dump(ledger,b)
    return rc

if __name__=='__main__':sys.exit(main())
