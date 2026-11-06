"""Validated derived v3 snapshots. Raw PCD hashes remain authoritative."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
import torch
from . import scene
from .assets import sha256_file

TENSORS=('_occupancy','_lo','_hi','_node_lo','_node_hi','_children','_leaves','_height')
FLOATS=('_lo','_hi','_node_lo','_node_hi','_height')
SCHEMA='task8-scene-cache-v1'


def implementation_hash():return sha256_file(scene.__file__)


def source_key(pcd_sha256):
    return dict(pcd_sha256=pcd_sha256,scene_sha256=implementation_hash(),backend=scene.BACKEND)


def write_scene(root,asset,snapshot):
    """Offline only: store canonical CPU64 geometry after its caller validates."""
    if snapshot.device.type!='cpu' or snapshot.dtype!=torch.float64:raise ValueError('cache generation requires CPU float64')
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    key=source_key(asset.hashes['pcd'])
    filename=hashlib.sha256((asset.map_id+json.dumps(key,sort_keys=True)).encode()).hexdigest()+'.pt'
    payload=dict(schema=SCHEMA,key=key,metadata=deepcopy(asset.metadata),provenance=snapshot.provenance(),tensors={n:getattr(snapshot,n).clone() for n in TENSORS})
    tmp=root/(filename+'.tmp');torch.save(payload,tmp);tmp.replace(root/filename)
    return dict(map_id=asset.map_id,key=key,file=filename,sha256=sha256_file(root/filename))


def write_index(root,records):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    ids=[r['map_id'] for r in records]
    if len(set(ids))!=len(ids):raise ValueError('duplicate cache map id')
    doc=dict(schema=SCHEMA,scene_sha256=implementation_hash(),backend=scene.BACKEND,maps=records)
    tmp=root/'index.tmp';tmp.write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n');tmp.replace(root/'index.json')


class SceneCache:
    def __init__(self,root):
        self.root=Path(root);self.index_sha256=sha256_file(self.root/'index.json')
        doc=json.loads((self.root/'index.json').read_text())
        if doc.get('schema')!=SCHEMA or doc.get('scene_sha256')!=implementation_hash() or doc.get('backend')!=scene.BACKEND:raise ValueError('scene cache key mismatch')
        self.records={r['map_id']:r for r in doc['maps']}
        if len(self.records)!=len(doc['maps']):raise ValueError('duplicate scene cache map id')

    def load(self,manifest,entry,*,device,dtype):
        start=time.perf_counter();device=torch.device(device)
        if dtype not in (torch.float64,torch.float32) or device.type not in ('cpu','cuda'):raise ValueError('scene cache device/dtype')
        if device.type=='cuda' and not torch.cuda.is_available():raise RuntimeError('requested CUDA is unavailable; no CPU fallback')
        key=source_key(entry['sha256']['pcd']);record=self.records.get(entry['id'])
        if record is None or record.get('key')!=key:raise ValueError('scene cache key missing/mismatch')
        name=record['file']
        if Path(name).name!=name:raise ValueError('scene cache payload path')
        for kind,path_key in (('pcd','pcd_path'),('sidecar','sidecar_path')):
            relative=entry.get(path_key);expected=entry['sha256'].get(kind)
            if relative is None:
                if expected is not None:raise ValueError('scene cache source hash/path mismatch')
                continue
            if Path(relative).is_absolute() or sha256_file(Path(manifest).parent/relative)!=expected:raise ValueError('scene cache source hash mismatch')
        path=self.root/name
        if sha256_file(path)!=record['sha256']:raise ValueError('scene cache payload hash mismatch')
        payload=torch.load(path,map_location='cpu',weights_only=True)
        if payload.get('schema')!=SCHEMA or payload.get('key')!=key:raise ValueError('scene cache payload key mismatch')
        if payload.get('metadata')!=entry:raise ValueError('scene cache metadata mismatch')
        data=payload['tensors']
        if set(data)!=set(TENSORS):raise ValueError('scene cache tensor fields')
        for name,tensor in data.items():
            expected=torch.float64 if name in FLOATS else torch.bool if name=='_occupancy' else torch.int64
            if not isinstance(tensor,torch.Tensor) or tensor.device.type!='cpu' or tensor.dtype!=expected:raise ValueError('scene cache tensor dtype')
        obj=scene.VoxelScene();obj.device=device;obj.dtype=dtype
        upload=time.perf_counter()
        for name in TENSORS:setattr(obj,name,data[name].to(device=device,dtype=dtype if name in FLOATS else data[name].dtype))
        if device.type=='cuda':torch.cuda.synchronize(device)
        obj.device=obj._lo.device;obj._provenance=deepcopy(payload['provenance'])
        obj._provenance.update(device=str(obj.device),dtype=str(dtype),cpu_preprocess_s=0.,device_upload_wall_s=time.perf_counter()-upload,
            tensor_bytes=sum(getattr(obj,n).numel()*getattr(obj,n).element_size() for n in TENSORS),
            cache_key=[deepcopy(entry['sha256']),scene.H,list(scene.ORIGIN),scene.BACKEND,str(obj.device),str(dtype)])
        return obj
