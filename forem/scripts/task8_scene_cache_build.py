#!/usr/bin/env python3
"""Fixed CPU-only full-pool parser bits/cache tensor validation; no sampling."""
import argparse, concurrent.futures, hashlib, inspect, json, multiprocessing, os, time
from pathlib import Path
import numpy as np
import torch
from task8_sim import assets, scene, scene_cache
from task8_sim.tests import assets_reference_r3 as reference
from task8_sim.scene import VoxelScene
from task8_sim.scene_cache import TENSORS,SceneCache,write_scene,write_index
from task8_sim.profile_lower import prohibit_training

DOCS={};ROOT=None


def offline_loader(module):
    # Same original validation function and parser; only the manifest JSON is
    # read once per fixed offline job instead of being reparsed for every map.
    source=inspect.getsource(module.load_asset)
    needle='doc = json.loads(manifest_path.read_text())'
    assert source.count(needle)==1
    namespace=dict(vars(module));namespace['_OFFLINE_DOCS']=DOCS
    exec(compile(source.replace(needle,'doc = _OFFLINE_DOCS[str(manifest_path)]'),module.__file__+'[offline-manifest-only]','exec'),namespace)
    return namespace['load_asset']


def job(task):
    manifest,map_id=task;t=time.monotonic();old=offline_loader(reference)(manifest,map_id)
    parsed=time.monotonic();new=offline_loader(assets)(manifest,map_id)
    if not np.array_equal(old.xyz.view(np.uint64),new.xyz.view(np.uint64)):raise ValueError(f'{map_id}: parser bits differ')
    snap=VoxelScene.from_asset(old,device='cpu',dtype=torch.float64)
    record=write_scene(ROOT,old,snap)
    # Index is shared only after all workers finish. Load through a private,
    # one-record index to execute the exact production loader for every map.
    local=SceneCache.__new__(SceneCache);local.root=ROOT;local.records={map_id:record}
    restored=local.load(manifest,old.metadata,device='cpu',dtype=torch.float64)
    for name in TENSORS:
        if not torch.equal(getattr(snap,name),getattr(restored,name)):raise ValueError(f'{map_id}: {name} unequal')
    return dict(record=record,wall_s=time.monotonic()-t,old_asset_s=parsed-t,points=len(old.xyz))


def main():
    global ROOT,DOCS
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--output',required=True);p.add_argument('--workers',type=int,required=True);a=p.parse_args()
    guards=prohibit_training();torch.set_num_threads(1)
    plan=json.loads(Path(a.plan).read_text());ROOT=Path(plan['cache_root']);ROOT.mkdir(parents=True,exist_ok=True)
    for manifest in plan['manifests']:DOCS[manifest]=json.loads(Path(manifest).read_text())
    tasks=[(r['manifest'],r['map_id']) for r in plan['maps']]
    if len(set(tasks))!=len(tasks):raise ValueError('duplicate fixed map')
    source_paths=[Path(__file__),Path(assets.__file__),Path(scene.__file__),Path(scene_cache.__file__),Path(reference.__file__)]
    source_hashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in source_paths}
    manifest_hashes={path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in DOCS}
    previous=[]
    for path in plan.get('reuse_reports',[]):
        report=json.loads(Path(path).read_text())
        if report.get('status')!='pass' or report['source_hashes']!=source_hashes or report['manifest_hashes']!=manifest_hashes:raise ValueError('reused report source mismatch')
        previous.extend(report['rows'])
    started=time.monotonic();rows=[]
    progress=Path(a.output+'.progress.jsonl').open('x')
    progress.write(json.dumps(dict(source_hashes=source_hashes,manifest_hashes=manifest_hashes,plan_sha256=hashlib.sha256(Path(a.plan).read_bytes()).hexdigest()))+'\n');progress.flush()
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers,mp_context=multiprocessing.get_context('fork')) as executor:
        for result in executor.map(job,tasks,chunksize=1):
            rows.append(result);progress.write(json.dumps(result)+'\n');progress.flush()
    progress.close()
    wall=time.monotonic()-started
    records=[r['record'] for r in previous+rows]
    if len(records)!=plan['expected_maps']:raise ValueError('fixed pool count mismatch')
    # A pilot index stays separate and cannot be mistaken for the final pool.
    write_index(ROOT,records)
    doc=dict(status='pass',maps=len(records),new_maps=len(rows),reused_maps=len(previous),wall_s=wall,worker_wall_s=sum(r['wall_s'] for r in rows),workers=a.workers,points=sum(r['points'] for r in rows),rows=previous+rows,guards=guards,
             input_plan_sha256=hashlib.sha256(Path(a.plan).read_bytes()).hexdigest(),parser_reference_sha256=hashlib.sha256(Path(reference.__file__).read_bytes()).hexdigest(),
             source_hashes=source_hashes,manifest_hashes=manifest_hashes)
    Path(a.output).write_text(json.dumps(doc,indent=2)+'\n');print(json.dumps({k:v for k,v in doc.items() if k!='rows'}),flush=True)

if __name__=='__main__':main()
