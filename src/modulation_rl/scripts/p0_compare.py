"""Frozen EVALUATION v1.1 numerical reproducibility gate (no CLI tolerance override)."""
import argparse
import json
from pathlib import Path
import numpy as np


def compare(left,right):
    left,right=Path(left),Path(right)
    rows=[[json.loads(line) for line in (d/'episodes.jsonl').read_text().splitlines()] for d in [left,right]]
    errors=[];maxima={}
    manifests=[json.loads((d/'manifest.json').read_text()) for d in [left,right]]
    for key in ['checkpoint_sha256','semantics']:
        if not manifests[0].get(key) or manifests[0].get(key)!=manifests[1].get(key):errors.append('manifest:'+key)
    if manifests[0].get('environment')!=manifests[1].get('environment'):errors.append('manifest:environment')
    if manifests[0].get('agent_config')!=manifests[1].get('agent_config'):errors.append('manifest:agent_config')
    if not rows[0] or len(rows[0])!=len(rows[1]):errors.append('episode_count')
    strict=['seed','initial_observation_sha256','steps','primary_reason','success','perfect_success','collision_count','ik_count','exception','terminated','truncated','reasons']
    for a,b in zip(*rows):
        for key in strict:
            if a.get(key)!=b.get(key) or key not in a:errors.append([a.get('seed'),key])
        if a.get('exception') is not None:errors.append([a.get('seed'),'exception'])
        for key,tol in [('reward',1e-3),('trajectory_length_m',1e-5)]:
            delta=abs(a[key]-b[key]);maxima[key]=max(maxima.get(key,0.),delta)
            if not np.isfinite(delta) or delta>tol:errors.append([a['seed'],key,delta])
        files=[np.load(d/('episode-%05d-trajectory.npz'%row['seed'])) for d,row in zip([left,right],[a,b])]
        for key in ['states','actions','base_xy']:
            x,y=files[0][key],files[1][key]
            delta=float(np.max(np.abs(x-y))) if x.shape==y.shape and x.size else float('inf')
            maxima[key]=max(maxima.get(key,0.),delta)
            if not np.isfinite(delta) or delta>1e-5:errors.append([a['seed'],key,delta])
        for f in files:f.close()
    return dict(passed=not errors,episodes=len(rows[0]),errors=errors,max_abs_differences=maxima,
                protocol='EVALUATION-v1.1',claim='numerical reproducibility; not bitwise trajectories')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('left');p.add_argument('right');p.add_argument('--output',required=True)
    a=p.parse_args();result=compare(a.left,a.right)
    Path(a.output).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['passed'] else 1)
