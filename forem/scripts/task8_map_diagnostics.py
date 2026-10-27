#!/usr/bin/env python3
"""One bounded map diagnostic per process. No training or altered sampling.

Run all geometry jobs first, then runtime jobs only after parent authorization.
Atomic stage records survive external timeout; a running record is incomplete.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback

START = time.monotonic()


class StageTimeout(BaseException):
    pass


def serial(value):
    if hasattr(value, 'detach'):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): serial(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)):
        return [serial(v) for v in value]
    return value


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',required=True)
    p.add_argument('--map-id',required=True)
    p.add_argument('--stage',choices=('geometry','runtime'),required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--device',choices=('cpu','cuda:0'),default='cpu')
    p.add_argument('--seed',type=int,default=20261026)
    p.add_argument('--max-wall-s',type=float,default=29)
    a=p.parse_args()
    if not 0<a.max_wall_s<30: p.error('internal wall bound must be positive and <30 seconds')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    result_path=out/(a.map_id+'-'+a.stage+'.json')
    if result_path.exists(): raise FileExistsError(result_path)
    record=dict(map_id=a.map_id,seed=a.seed,status='running',stage='imports',requested_stage=a.stage,
        environment_version='task8-pcd-v3',map_backend='pcd-voxel-v3',sensor_policy='ghost-v1',
        profile='sync_v5',requested_device=a.device,geometry_gate='not_run',runtime_gate='not_run',
        max_wall_s=a.max_wall_s)
    env=None
    SamplingIncomplete=None
    def save(stage=None):
        if stage is not None: record['stage']=stage
        record['elapsed_s']=time.monotonic()-START
        if env is not None and env.sampler is not None:
            record['sampling']=serial(env.sampler.stats)
            record['sampling_timing']=serial(env.sampler.timing)
        temp=result_path.with_suffix('.tmp')
        temp.write_text(json.dumps(serial(record),indent=2)+'\n');temp.replace(result_path)
    def alarm(*_): raise StageTimeout()
    signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,max(.001,a.max_wall_s-(time.monotonic()-START)))
    save()
    try:
        import numpy as np
        import torch
        from task8_sim.assets import load_asset
        from task8_sim.scene import VoxelScene
        torch.set_num_threads(1)
        dtype=torch.float64 if a.stage=='geometry' else torch.float32
        if a.device.startswith('cuda') and not torch.cuda.is_available():
            raise RuntimeError('requested GPU unavailable; no fallback')
        files=[Path(__file__),Path('src/task8_sim/assets.py'),Path('src/task8_sim/scene.py'),Path('src/task8_sim/episode.py'),Path('src/task8_sim/env.py'),Path('config/task8/sensor.json'),Path('config/task8/environment.json')]
        record['implementation_sha256']={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files if path.is_file()}
        save('load')
        asset=load_asset(a.manifest,a.map_id)
        record['hashes']=asset.hashes
        record['point_count']=len(asset.xyz)
        if a.stage=='geometry':
            save('voxelize')
            scene=VoxelScene.from_asset(asset,device=a.device,dtype=dtype)
            record['provenance']=scene.provenance()
            save('geometry_query')
            # Independent integer occupancy reference from actual PCD, no JSON.
            indices=np.floor((asset.xyz-np.array([-5,-5,0]))/.05).astype(np.int64)
            expected=np.zeros((32,200,200),dtype=bool)
            expected[indices[:,2],indices[:,1],indices[:,0]]=True
            assert np.array_equal(scene.occupancy.cpu().numpy(),expected)
            z,y,x=np.argwhere(expected)[0]
            centre=np.array([-5+(x+.5)*.05,-5+(y+.5)*.05,(z+.5)*.05])
            # A positive-distance ray traverses from outside domain to first occupied cell.
            first_x=int(np.flatnonzero(expected[z,y])[0])
            origin=np.array([-6.,centre[1],centre[2]])
            distance_expected=1+first_x*.05
            origins=torch.tensor(origin,device=a.device,dtype=dtype).reshape(1,1,3)
            directions=torch.tensor([1.,0,0],device=a.device,dtype=dtype).reshape(1,1,3)
            hit=scene.raycast(origins,directions,max_range=12.)
            torch.testing.assert_close(hit,hit.new_tensor([[distance_expected]]),atol=1e-10,rtol=0)
            assert scene.contains(torch.tensor(centre,device=a.device,dtype=dtype).reshape(1,1,3)).item()
            assert not scene.contains(torch.tensor([[[-6.,-6.,2.]]],device=a.device,dtype=dtype)).item()
            caps=torch.empty((1,0,7),device=a.device,dtype=dtype)
            base=torch.tensor([[centre[0],centre[1],0]],device=a.device,dtype=dtype)
            collision=scene.collide(base,caps,robot=None)
            assert collision.base.item()
            record['query']=dict(occupied_count=int(expected.sum()),occupied_centre=centre.tolist(),
                ray_origin=origin.tolist(),ray_direction=[1,0,0],expected_positive_hit_m=distance_expected,
                actual_hit_m=hit.item(),occupied_contains=True,outside_contains=False,
                base_collision_at_occupied_xy=True,device=str(hit.device),dtype=str(hit.dtype))
            record.update(status='geometry_checked',geometry_gate='passed')
        else:
            from task8_sim.env import PcdEpisodeEnv
            from task8_sim.episode import SamplingIncomplete
            from task7_sim.core import Candidate
            from task7_sim.candidates import generate_candidates
            # Restrict the pool to this map without changing its proposal distribution.
            original=json.loads(Path(a.manifest).read_text())
            entry=next(m for m in original['maps'] if m['id']==a.map_id)
            one=out/(a.map_id+'-pool.json')
            entry=dict(entry)
            for field in ('pcd_path','sidecar_path'):
                if entry.get(field):entry[field]=os.path.relpath(Path(a.manifest).resolve().parent/entry[field],out.resolve())
            one.write_text(json.dumps(dict(schema_version=original['schema_version'],maps=[entry]),indent=2)+'\n')
            save('env_construct')
            env=PcdEpisodeEnv(1,seed=a.seed,pool=str(one),profile='sync_v5',device=a.device,dtype=dtype)
            save('reset')
            env.reset(deadline=START+a.max_wall_s)
            c=env.core
            record['reset_info']=serial(env.info())
            record['provenance']=env.scenes.provenance()
            record['initial_state']=serial(dict(base=c.state.base,q=c.state.q,s=c.state.s,
                actual_fk=env.kin.world_tcp(c.state.base,c.state.q)))
            record['actual_state_device']=str(c.state.base.device)
            record['actual_state_dtype']=str(c.state.base.dtype)
            save('initial_scan')
            depth=c.renderer(c.state.base,c.capsules(c.state.base,c.state.q))
            record['initial_scan']=dict(valid_count=int(depth.valid.sum()),grid_observed_count=int(c.grid.observed.sum()),
                scan_timestamp=serial(c.grid.timestamp),self_occlusion=depth.self_occlusion)
            assert depth.valid.any() and c.grid.observed.any()
            arrays={'initial_depth':depth.distance.detach().cpu().numpy(),'initial_valid':depth.valid.detach().cpu().numpy(),
                    'initial_grid_height':c.grid.height.detach().cpu().numpy(),'initial_grid_observed':c.grid.observed.detach().cpu().numpy()}
            np.savez_compressed(out/(a.map_id+'-initial-scan.npz'),**arrays)
            save('candidate')
            generated=generate_candidates(c.grid.crop(c.state.base),c.state,c.route,c.kin,synchronous=True)
            eligible=torch.where(generated.mask[0]&~generated.inplace[0])[0]
            if not len(eligible):raise RuntimeError('no generated moving candidate; runtime gate incomplete')
            k=int(eligible[0]);world=generated.world_pose(c.state.base)
            record['candidate_index']=k
            env.begin(Candidate(world[:,k],None,generated.inplace[:,k]))
            save('step')
            raw=c.state.base.new_tensor([[0.,0.,.5]])
            result=env.step(raw)
            tr=result.transition
            record['step']=serial(dict(raw_action=raw,attempted=tr.attempted,committed=tr.committed,
                reason=tr.reason,reward=tr.reward,dt=tr.dt,active=tr.active,done=tr.done,
                attempts=c.attempts,info=env.info()))
            assert tr.attempted.item()>0
            record['final_state']=serial(dict(base=c.state.base,q=c.state.q,s=c.state.s,
                actual_fk=env.kin.world_tcp(c.state.base,c.state.q)))
            save('next_scan')
            next_depth=c.renderer(c.state.base,c.capsules(c.state.base,c.state.q))
            record['next_scan']=dict(valid_count=int(next_depth.valid.sum()),grid_observed_count=int(c.grid.observed.sum()),
                scan_timestamp=serial(c.grid.timestamp),self_occlusion=next_depth.self_occlusion,
                diagnostic_render=True,automatic_render_count=serial(c.render_count))
            assert next_depth.valid.any()
            np.savez_compressed(out/(a.map_id+'-next-scan.npz'),depth=next_depth.distance.detach().cpu().numpy(),
                valid=next_depth.valid.detach().cpu().numpy(),grid_height=c.grid.height.detach().cpu().numpy(),
                grid_observed=c.grid.observed.detach().cpu().numpy())
            record.update(status='step_checked',runtime_gate='passed')
        save('complete')
        return 0
    except StageTimeout:
        sampling_unfinished=record['stage']=='reset' and env is not None and env.sampler.stats['accepted']==0
        record['status']='reset_timeout' if sampling_unfinished else 'stage_timeout'
        if record['stage']=='reset' and not sampling_unfinished:
            record['stage']='reset_after_sample'
        record['interrupted_stage']=record['stage'];save();return 124
    except Exception as exc:
        # Only the documented typed sampling interruption can be a sampling limitation.
        if SamplingIncomplete is not None and isinstance(exc,SamplingIncomplete) and record['stage']=='reset':
            record['status']='reset_cancelled' if 'cancelled' in str(exc) else 'reset_timeout'
            if env is not None and env.sampler.stats['accepted']>0:
                record['status']='stage_timeout'
                record['stage']='reset_after_sample'
        else:record['status']='error'
        record['error']=f'{type(exc).__name__}: {exc}'
        record['traceback']=traceback.format_exc();save();return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__': raise SystemExit(main())
