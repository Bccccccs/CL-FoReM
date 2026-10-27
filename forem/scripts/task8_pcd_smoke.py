#!/usr/bin/env python3
"""Bounded PCD smoke, explicit profiles, actual FK/scan and wall timings.

Scripted actor only; no frozen neural network or optimizer is loaded. Decision
profiles execute at most max_steps lower actions manually after a genuine
Grid-only boundary; interrupted decisions are not called complete decisions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import time

START=time.monotonic()
class SmokeTimeout(BaseException):pass

def serial(value):
    if hasattr(value,'detach'):return value.detach().cpu().tolist()
    if isinstance(value,dict):return {str(k):serial(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [serial(v) for v in value]
    return value

def main():
    p=argparse.ArgumentParser()
    for key in ('config','pool','profile','output'):p.add_argument('--'+key,required=True)
    p.add_argument('--batch',type=int,choices=(1,2),default=1)
    p.add_argument('--max-steps',type=int,default=1);p.add_argument('--max-wall-s',type=float,default=120)
    p.add_argument('--device',default='cuda:0',choices=('cpu','cuda:0'));p.add_argument('--seed',type=int,default=20261026)
    a=p.parse_args()
    if not 1<=a.max_steps<=64 or not 0<a.max_wall_s<=120:p.error('bounded smoke requires 1..64 steps and 0<wall<=120s')
    out=Path(a.output)
    if out.exists():raise FileExistsError(f'refusing to overwrite smoke evidence: {out}')
    out.mkdir(parents=True)
    record=dict(status='running',profile=a.profile,batch=a.batch,seed=a.seed,actor='scripted_no_network',neural_inference='not_run',actual_action_steps=0,steps=[],timing={})
    def save():
        record['wall_s']=time.monotonic()-START
        (out/'smoke.json').write_text(json.dumps(serial(record),indent=2)+'\n')
    def alarm(*_):raise SmokeTimeout()
    signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,max(.001,a.max_wall_s-(time.monotonic()-START)))
    save()
    try:
        import numpy as np
        import torch
        from task8_sim.env import PcdEpisodeEnv,profile_options
        from task8_sim.decision_env import PcdDecisionEnv
        from task7_sim.core import Candidate
        from task7_sim.candidates import generate_candidates
        config=json.loads(Path(a.config).read_text())
        require=lambda x,m: (_ for _ in ()).throw(ValueError(m)) if not x else None
        require(config['profiles'][a.profile]==profile_options(a.profile),'config/profile mismatch')
        require(config['environment_version']=='task8-pcd-v3' and config['map_backend']=='pcd-voxel-v3' and config['sensor_policy']=='ghost-v1' and config['semantic_policy_input'] is False,'config version')
        torch.set_num_threads(1)
        dtype=torch.float32 if a.device.startswith('cuda') else torch.float64
        if a.device.startswith('cuda'):
            require(torch.cuda.is_available(),'GPU unavailable; no fallback');torch.cuda.reset_peak_memory_stats()
        def sync():
            if a.device.startswith('cuda'):torch.cuda.synchronize()
        def timed(name,fn):
            sync();t=time.perf_counter();value=fn();sync();record['timing'].setdefault(name,[]).append(time.perf_counter()-t);return value
        def actor(obs):
            raw=obs['q'].new_zeros(a.batch,3);raw[:,2]=.5;return raw
        # Explicit fixture difficulty avoids accidentally drawing empty/analytic maps.
        manifest=Path(a.pool)
        if manifest.is_dir():manifest=next(x for x in (manifest/'manifest.json',manifest/'index.json') if x.is_file())
        entries=json.loads(manifest.read_text())['maps'];difficulty='random_cubes' if any(x['id']=='random_cubes' for x in entries) else None
        record['config_sha256']=hashlib.sha256(Path(a.config).read_bytes()).hexdigest()
        decision=None
        if a.profile=='sync_v5':
            env=PcdEpisodeEnv(a.batch,seed=a.seed,pool=a.pool,profile=a.profile,device=a.device,dtype=dtype,difficulty=difficulty)
            timed('reset_cold_wall_s',lambda:env.reset(deadline=START+a.max_wall_s))
            c=env.core
            generated=timed('candidate_wall_s',lambda:generate_candidates(c.grid.crop(c.state.base),c.state,c.route,c.kin,synchronous=True))
            rows=torch.arange(a.batch,device=a.device);selected=generated.mask.long().argmax(-1);pose=generated.world_pose(c.state.base)
            env.begin(Candidate(pose[rows,selected],None,generated.inplace[rows,selected]))
        else:
            decision=PcdDecisionEnv(a.batch,actor,seed=a.seed,pool=a.pool,profile=a.profile,device=a.device,dtype=dtype,run_id=out.name,difficulty=difficulty)
            timed('reset_and_boundary_wall_s',lambda:decision.reset(deadline=START+a.max_wall_s))
            env=decision.episodes;c=env.core
            selected=decision.candidates['mask'].long().argmax(-1);rows=torch.arange(a.batch,device=a.device)
            cs=decision.candidates
            env.begin(Candidate(cs['world_pose'][rows,selected],None if cs['progress'] is None else cs['progress'][rows,selected],cs['inplace'][rows,selected]))
            record['decision_boundary_timing']=decision.last_timing
            record['decision_completion']='bounded lower-action slice, not DecisionEnv.step completion'
        record.update(versions=env.versions,device=str(c.state.q.device),dtype=str(c.state.q.dtype),map_ids=env.map_ids,provenance=env.scenes.provenance(),sampling=env.sampler.stats,sampling_timing=env.sampler.timing)
        initial=serial(dict(base=c.state.base,q=c.state.q,s=c.state.s,actual_fk=c.kin.world_tcp(c.state.base,c.state.q),scan_timestamp=c.grid.timestamp,sensor_frames=c.sensor_frames))
        record['initial_state']=initial
        depth=timed('diagnostic_scan_initial_wall_s',lambda:c.renderer(c.state.base,c.capsules(c.state.base,c.state.q)))
        np.savez_compressed(out/'initial-scan.npz',depth=depth.distance.cpu().numpy(),valid=depth.valid.cpu().numpy(),grid_height=c.grid.height.cpu().numpy(),grid_observed=c.grid.observed.cpu().numpy())
        with torch.no_grad():
            for _ in range(a.max_steps):
                if c.done.all():break
                raw=timed('scripted_actor_wall_s',lambda:actor(c.current_observation()))
                tr=timed('core_step_including_IK_collision_scan_wall_s',lambda:env.step(raw).transition)
                record['actual_action_steps']+=1
                record['steps'].append(serial(dict(action=raw,attempted=tr.attempted,committed=tr.committed,reward=tr.reward,dt=tr.dt,reason=tr.reason,done=tr.done,failure_kind=c.failure_kind,base=c.state.base,q=c.state.q,s=c.state.s,actual_fk=c.kin.world_tcp(c.state.base,c.state.q),sensor_frames=c.sensor_frames,scan_timestamp=c.grid.timestamp)))
                save()
        require(record['actual_action_steps']>0,'no real action executed')
        require(any(sum(step['committed'])>0 for step in record['steps']),'no state commit')
        require(c.grid.timestamp.gt(0).all().item(),'no subsequent automatic scan')
        require(initial['base']!=serial(c.state.base) or initial['q']!=serial(c.state.q),'no actual state change')
        depth=timed('diagnostic_scan_final_wall_s',lambda:c.renderer(c.state.base,c.capsules(c.state.base,c.state.q)))
        t=time.perf_counter();np.savez_compressed(out/'final-scan.npz',depth=depth.distance.cpu().numpy(),valid=depth.valid.cpu().numpy(),grid_height=c.grid.height.cpu().numpy(),grid_observed=c.grid.observed.cpu().numpy())
        record['timing']['final_output_wall_s']=[time.perf_counter()-t]
        record.update(status='pass',sim_committed_s=sum(sum(x['committed']) for x in record['steps'])*.05,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated() if a.device.startswith('cuda') else None,gpu_name=torch.cuda.get_device_name() if a.device.startswith('cuda') else None,gpu_event_time_s=None,peak_host_rss_kib=__import__('resource').getrusage(__import__('resource').RUSAGE_SELF).ru_maxrss)
        save();return 0
    except SmokeTimeout:
        record.update(status='incomplete',error='external wall budget; not natural environment truncation');save();return 124
    except Exception as exc:
        record.update(status='fail',error=f'{type(exc).__name__}: {exc}');save();raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':raise SystemExit(main())
