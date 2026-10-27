#!/usr/bin/env python3
"""Fail-closed task8 acceptance verifier. Does not execute environments/train.

Human gate review is explicit in acceptance.json. This tool verifies every gate,
its immutable evidence hashes, frozen source/assets and the raw 24-map records.
It does not infer scientific success from exit codes or map availability.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(Path(path).read_text())

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(condition,message):
    if not condition:raise ValueError(message)

def execution_is_compliant(data):
    # Explicit violation records take precedence over contradictory summary flags.
    return (data.get('no_network_optimizer_execution') is True
            and data.get('execution_compliance')=='pass'
            and not data.get('execution_deviation'))

def check_evidence(base,item):
    path=base/item['path']
    require(path.is_file(),f'missing evidence: {path}')
    require(digest(path)==item['sha256'],f'evidence hash mismatch: {path}')
    return path

def audit_maps(run):
    import numpy as np
    from task8_sim.assets import load_asset
    manifest=run/'semantic-pool/index.json';index=read(manifest)
    entries=index['maps'];require(len(entries)==24,'24 map entries required')
    require(len({e['id'] for e in entries})==24,'duplicate map IDs')
    records=[];fk_max=0.
    # Read-only FK re-computation is deliberately separate from reported targets.
    import torch
    from task7_sim.kinematics import Kinematics
    kin=Kinematics()
    for entry in entries:
        key=entry['id'];asset=load_asset(manifest,key)
        g=read(run/'map-diagnostics'/f'{key}-geometry.json')
        r=read(run/'map-diagnostics'/f'{key}-runtime.json')
        for value in (g,r):
            require(value['map_id']==key,f'{key}: record ID')
            require(value['hashes']==asset.hashes,f'{key}: asset hash record')
            require(value['environment_version']=='task8-pcd-v1' and value['map_backend']=='pcd-voxel-v1' and value['sensor_policy']=='ghost-v1',f'{key}: version')
        require(g['status']=='geometry_checked' and g['geometry_gate']=='passed',f'{key}: geometry gate')
        ids=np.floor((asset.xyz-np.array([-5.,-5.,0.]))/.05).astype(np.int64)
        occupied=np.zeros((32,200,200),dtype=bool);occupied[ids[:,2],ids[:,1],ids[:,0]]=True
        query=g['query'];z,y,x=np.argwhere(occupied)[0]
        expected=1+np.flatnonzero(occupied[z,y])[0]*.05
        require(query['occupied_count']==int(occupied.sum()),f'{key}: occupancy')
        require(abs(query['actual_hit_m']-expected)<1e-10 and abs(query['expected_positive_hit_m']-expected)<1e-10,f'{key}: ray geometry')
        require(query['occupied_contains'] is True and query['outside_contains'] is False and query['base_collision_at_occupied_xy'] is True,f'{key}: geometry assertions')
        status=r['status'];item=dict(map_id=key,status=status,geometry='pass',runtime='not_run')
        if status=='step_checked':
            require(r['runtime_gate']=='passed',f'{key}: runtime gate')
            step=r['step'];attempted=sum(step['attempted']);committed=sum(step['committed'])
            require(attempted>0 and committed>0 and attempted>=committed,f'{key}: real committed step required')
            require(r['sampling']['accepted']==1,f'{key}: default sampling')
            states=[r['initial_state'],r['final_state']]
            for state in states:
                base=torch.tensor(state['base'],dtype=torch.float32);q=torch.tensor(state['q'],dtype=torch.float32)
                actual=kin.world_tcp(base,q).numpy();reported=np.array(state['actual_fk'])
                err=float(np.abs(actual-reported).max());fk_max=max(fk_max,err)
                require(err<=3e-6,f'{key}: actual FK mismatch')
            require(states[0]['base']!=states[1]['base'] or states[0]['q']!=states[1]['q'],f'{key}: no actual movement')
            require(sum(r['next_scan']['scan_timestamp'])>sum(r['initial_scan']['scan_timestamp']),f'{key}: stale scan')
            for suffix,dk,vk,gk,ok in [('initial-scan','initial_depth','initial_valid','initial_grid_height','initial_grid_observed'),('next-scan','depth','valid','grid_height','grid_observed')]:
                with np.load(run/'map-diagnostics'/f'{key}-{suffix}.npz',allow_pickle=False) as arrays:
                    depth,valid=arrays[dk],arrays[vk]
                    require(depth.shape==(1,90,360) and valid.shape==depth.shape and valid.dtype==np.bool_,f'{key}: scan shape')
                    require(valid.any() and np.isfinite(depth[valid]).all() and ((depth[valid]>=0)&(depth[valid]<=6)).all(),f'{key}: depth values')
                    require(int(valid.sum())==r['initial_scan' if suffix=='initial-scan' else 'next_scan']['valid_count'],f'{key}: valid count')
                    require(np.isfinite(arrays[gk]).all() and int(arrays[ok].sum())==r['initial_scan' if suffix=='initial-scan' else 'next_scan']['grid_observed_count'],f'{key}: Grid data')
            item.update(runtime='pass',attempted=attempted,committed=committed)
        else:
            require(status in ('reset_timeout','reset_cancelled','reset_rejected'),f'{key}: runtime exception/non-sampling failure {status}')
            require(r.get('stage')=='reset' and r.get('sampling',{}).get('accepted',0)==0,f'{key}: only unaccepted sampling limitation permitted')
        records.append(item)
    count=sum(r['runtime']=='pass' for r in records)
    require(count>0,'no semantic default sample-to-step chain passed')
    return dict(maps=records,total=24,step_checked=count,all_maps_runnable=count==24,actual_fk_cpu_max_abs=fk_max,
                limitation='one accepted episode/one action per map; no general feasibility or SAC success estimate')

def verify(run_dir):
    run=Path(run_dir).resolve()
    file=run/'acceptance.json'
    if not file.is_file():file=run/'acceptance/acceptance.json'
    data=read(file);gates=data.get('required_gates',{})
    require(set(gates)==set('ABCDEF'),'required gates A-F missing or unexpected')
    for key,gate in gates.items():
        require(gate.get('status')=='pass',f'required gate {key}: {gate.get("status","missing")}')
        require(gate.get('evidence'),f'required gate {key}: no evidence')
        for item in gate['evidence']:check_evidence(file.parent,item)
    require(data.get('environment_version')=='task8-pcd-v1','acceptance version')
    manifest=read(check_evidence(file.parent,data['manifest']))
    require(manifest.get('files'),'empty frozen manifest')
    external=read(check_evidence(file.parent,manifest['external_source_evidence']))
    require(external.get('status')=='pass' and external.get('checked')==9 and not external.get('drift'),'external source hash snapshot failed')
    for path,expected in manifest['files'].items():
        require((ROOT/path).is_file() and digest(ROOT/path)==expected,f'frozen source/asset hash mismatch: {path}')
    run=(file.parent/data['map_run_dir']).resolve()
    maps=audit_maps(run)
    functional='pass' if maps['all_maps_runnable'] else 'pass_with_map_limitations'
    compliant=execution_is_compliant(data)
    return dict(status=functional if compliant else 'fail',functional_status=functional,execution_compliance='pass' if compliant else 'fail',execution_deviation=data.get('execution_deviation'),required_gates={k:'pass' for k in 'ABCDEF'},map_diagnostics=maps)

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-dir',required=True);a=p.parse_args()
    try:result=verify(a.run_dir)
    except Exception as exc:
        print(json.dumps({'status':'fail','error':f'{type(exc).__name__}: {exc}'}));return 1
    print(json.dumps(result,indent=2));return 0 if result['status'] in ('pass','pass_with_map_limitations') else 1

if __name__=='__main__':sys.exit(main())
