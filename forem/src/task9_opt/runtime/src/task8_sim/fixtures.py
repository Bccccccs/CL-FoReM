"""Deterministic, PCD-only test assets; engineering fixtures, not training maps.

Parameters inherit task8.1 PROCEDURE / SRC-0987. No task7 asset is modified.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from .assets import load_asset, sha256_file


def _box(center, size, yaw=0.):
    return {'center':list(center), 'size':list(size), 'yaw':float(yaw)}


def fixture_specs(seed=20261026):
    rng = np.random.default_rng(seed)
    random = []
    for x, y in ((-2,-2),(-2,2),(2,-2),(2,2)):
        side = float(rng.uniform(.5,1.))
        random.append(_box((x+float(rng.uniform(-.3,.3)), y+float(rng.uniform(-.3,.3)),side/2), (side,)*3, float(rng.uniform(-np.pi,np.pi))))
    return {
        'empty': [],
        'axis_aligned': [_box((2,0,.5),(1,1,1))],
        'rotated': [_box((2,0,.5),(1,1,1),np.pi/4)],
        'occlusion': [_box((1.5,0,.5),(.5,1,1)),_box((3,0,.5),(.5,1,1))],
        'boundary': [_box((4.75,0,.5),(.5,.5,1))],
        'floating_slab': [_box((2,0,1.025),(1,1,.05))],
        'random_cubes': random,
    }


def _sample(box):
    # Sample cell centers, retaining thin/slanted volume; no inferred box geometry at load.
    size = np.asarray(box['size'])
    counts = np.maximum(1,np.ceil(size/.05).astype(int))
    axes = [(np.arange(n)+.5)*s/n-s/2 for s,n in zip(size,counts)]
    points = np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1).reshape(-1,3)
    c,s=np.cos(box['yaw']),np.sin(box['yaw'])
    points[:,:2] = points[:,:2] @ np.array([[c,s],[-s,c]])
    return points+box['center']


def export_fixtures(output, seed=20261026):
    output = Path(output)
    # A fresh directory is mandatory; neither maps nor manifest can be overwritten.
    output.mkdir(parents=True,exist_ok=False)
    entries=[]
    for name,boxes in fixture_specs(seed).items():
        xyz=np.concatenate([_sample(box) for box in boxes]) if boxes else np.empty((0,3))
        pcd=output/(name+'.pcd'); temporary=output/(name+'.pcd.tmp')
        with temporary.open('x') as stream:
            stream.write(f'VERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH {len(xyz)}\nHEIGHT 1\nPOINTS {len(xyz)}\nDATA ascii\n')
            np.savetxt(stream,xyz,fmt='%.12g')
        temporary.rename(pcd)
        entries.append(dict(id=name,pcd_path=pcd.name,sidecar_path=None,
            sha256={'pcd':sha256_file(pcd),'sidecar':None},split='smoke',difficulty=name,
            frame_id='world',length_unit='m',resolution_m=.05,
            point_representation='solid_volume_samples',bounds={'min':[-5,-5,0],'max':[5,5,1.6],'upper_exclusive':True},
            geometry_backend='pcd-voxel-v3',semantic_policy_input=False,
            fixture=True,allow_empty=name=='empty',fixture_seed=seed,fixture_boxes=boxes))
    temporary=output/'manifest.json.tmp'
    temporary.write_text(json.dumps({'schema_version':'task8-pcd-v1','maps':entries},sort_keys=True,indent=2)+'\n')
    manifest=output/'manifest.json'; temporary.rename(manifest)
    # Every runtime geometry comes from the just-persisted PCD.
    for entry in entries:load_asset(manifest,entry['id'])
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--seed',type=int,default=20261026)
    args=parser.parse_args()
    print(export_fixtures(args.output,args.seed))
