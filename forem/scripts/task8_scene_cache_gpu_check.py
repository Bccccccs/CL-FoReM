#!/usr/bin/env python3
"""Fixed GPU32 cache cast equality for 8 cube + 24 semantic pilot maps."""
import argparse,hashlib,json,time
from pathlib import Path
import torch
import task8_scene_cache_build as builder
from task8_sim import assets
from task8_sim.scene import VoxelScene
from task8_sim.scene_cache import SceneCache,TENSORS
from task8_sim.profile_lower import prohibit_training,runtime


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    guards=prohibit_training();torch.set_num_threads(2);plan=json.loads(Path(a.plan).read_text());cache=SceneCache(plan['cache_root']);start=time.monotonic()
    for path in plan['manifests']:builder.DOCS[path]=json.loads(Path(path).read_text())
    loader=builder.offline_loader(assets);maps=[plan['maps'][i] for i in (0,8,16,23,24,47,48,71)]+plan['maps'][-24:];rows=[]
    with torch.no_grad():
        for record in maps:
            manifest=record['manifest'];key=record['map_id'];asset=loader(manifest,key)
            original=VoxelScene.from_asset(asset,device='cuda:0',dtype=torch.float32)
            cached=cache.load(manifest,asset.metadata,device='cuda:0',dtype=torch.float32)
            for name in TENSORS:
                if not torch.equal(getattr(original,name),getattr(cached,name)):raise ValueError(f'{key}: {name} differs')
            old,new=original.provenance(),cached.provenance()
            for field in set(old)-{'cpu_preprocess_s','device_upload_wall_s'}:
                if old[field]!=new[field]:raise ValueError(f'{key}: provenance {field} differs')
            rows.append(dict(map_id=key,tensors_equal=list(TENSORS),provenance_equal_except_timing=True))
    doc=dict(status='pass',plan_sha256=hashlib.sha256(Path(a.plan).read_bytes()).hexdigest(),cache_index_sha256=cache.index_sha256,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),maps=len(rows),wall_s=time.monotonic()-start,rows=rows,guards=guards,runtime=runtime());Path(a.output).write_text(json.dumps(doc,indent=2)+'\n');print(json.dumps({k:v for k,v in doc.items() if k!='rows'}))

if __name__=='__main__':main()
