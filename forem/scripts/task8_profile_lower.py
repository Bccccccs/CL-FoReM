#!/usr/bin/env python3
"""Frozen inference profiler. Does not construct LowerSAC or any optimizer.
Production sources and task7 artifacts are read only. External timeout and a
separate cumulative ledger bound every execution; partial reports survive TERM.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

START=time.monotonic()
class ProfileTimeout(BaseException):pass

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','run'))
    p.add_argument('--family',required=True,choices=('cube','semantic','cubepool'),help='cubepool (task8.11): 64 strided train-split maps of the real cube-pool-v2')
    p.add_argument('--map-backend',default='pcd-voxel-v3',help='task8.11: map backend for sampling/prepare and env (default unchanged)')
    p.add_argument('--root',required=True);p.add_argument('--batch',type=int,choices=(1,16,64,256),default=1)
    p.add_argument('--steps',type=int,default=20);p.add_argument('--warmup',type=int,default=2)
    p.add_argument('--window-steps',type=int,default=None,help='Independent bounded window; aggregate >=20 samples per batch separately.')
    p.add_argument('--window-id',default=None,help='Unique output suffix; required with window-steps.')
    p.add_argument('--threads',type=int,default=2);p.add_argument('--wall-s',type=float,default=288.)
    a=p.parse_args()
    if a.steps<20 or a.warmup<1 or not 0<a.wall_s<=290:raise ValueError('fixed profile sample/budget bounds')
    if a.window_steps is not None and (a.mode!='run' or not 1<=a.window_steps<=a.steps or not a.window_id or not a.window_id.replace('-','').isalnum()):raise ValueError('invalid independent measurement window')
    import numpy as np
    import torch
    from task8_sim.profile_lower import Timings,save,runtime,prohibit_training
    calls=prohibit_training();torch.set_num_threads(a.threads)
    if not torch.cuda.is_available():raise RuntimeError('GPU required; no CPU fallback')
    torch.cuda.set_device(0);torch.cuda.reset_peak_memory_stats();torch.manual_seed(4718)
    root=Path(a.root);root.mkdir(parents=True,exist_ok=True)
    name=f'{a.family}-{a.mode}'+(f'-b{a.batch}' if a.mode=='run' else '')
    if a.window_id:name+='-'+a.window_id
    output=root/(name+'.json')
    if output.exists():raise FileExistsError(output)
    report=dict(status='running',map_backend=a.map_backend,family=a.family,mode=a.mode,batch=a.batch,steps_requested=a.steps,warmup_requested=a.warmup,completed_steps=0,completed_warmup=0,guard=calls,notes=['No optimizer or SAC object constructed; no backward/update.', 'Profiling synchronization adds overhead; CUDA events include stream idle during Python/CPU work.', 'Episodes sampled once per map; factory reuses accepted episode on reset. This is a bounded scene rotation workload, not full random training.'])
    report.update(window_id=a.window_id,window_steps_requested=a.window_steps,measurement_protocol='r2-independent-windows-v1',window_note='Each window starts fresh from the same cached episodes and actor RNG seed4718, then independently warms up. Trajectories repeat; timing samples do not establish broader state-distribution coverage.')
    tm=Timings()
    def flush():
        report.update(wall_s=time.monotonic()-START,runtime=runtime(),timings=tm.summary(),timing_samples=tm.samples());save(output,report)
    def alarm(*_):raise ProfileTimeout()
    signal.signal(signal.SIGTERM,alarm);signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,max(.01,a.wall_s-(time.monotonic()-START)))
    flush()
    monitor_file=(root/(name+'-gpu.csv')).open('x')
    monitor=subprocess.Popen(['nvidia-smi','-i',os.environ.get('CUDA_VISIBLE_DEVICES','0').split(',')[0],'--query-gpu=timestamp,index,utilization.gpu,utilization.memory,memory.used','--format=csv,nounits','-l','1'],stdout=monitor_file,stderr=subprocess.STDOUT)
    try:
        if a.mode=='prepare':prepare(a,root,report,tm,flush)
        else:run(a,root,report,tm,flush)
        assert calls==dict(optimizer_constructed=0,backward_calls=0)
        report['status']='window_complete' if a.window_steps is not None and a.window_steps<a.steps else 'pass';flush();return 0
    except ProfileTimeout:
        tm.rollback_partial()
        report.update(status='incomplete',error='External wall limit; samples below protocol are not passed.');flush();return 124
    except Exception as exc:
        tm.rollback_partial()
        report.update(status='fail',error=f'{type(exc).__name__}: {exc}');flush();raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        monitor.terminate();monitor.wait(timeout=3);monitor_file.close()


def prepare(a,root,report,tm,flush):
    import numpy as np
    import torch
    from task8_sim.assets import sha256_file
    from task8_sim.fixtures import fixture_specs,_sample
    from task8_sim.episode import PcdEpisodeSampler,RandomStreams
    from task7_sim.kinematics import Kinematics
    from task8_sim.robot import GhostRobotGeometry
    if a.family=='cubepool':
        manifest=Path('/root/mm_husky_ws/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json')
        train=[e for e in json.loads(manifest.read_text())['maps'] if e['split']=='train']
        entries=train[::len(train)//64][:64]
    elif a.family=='cube':
        pool=root/'cube-pool';pool.mkdir(exist_ok=False);entries=[]
        for i in range(64):
            seed=20261027+i;boxes=fixture_specs(seed)['random_cubes'];xyz=np.concatenate([_sample(box) for box in boxes]);pcd=pool/f'cube_{i:03d}.pcd'
            with pcd.open('x') as f:
                f.write(f'VERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH {len(xyz)}\nHEIGHT 1\nPOINTS {len(xyz)}\nDATA ascii\n');np.savetxt(f,xyz,fmt='%.12g')
            entries.append(dict(id=pcd.stem,pcd_path=pcd.name,sidecar_path=None,sha256=dict(pcd=sha256_file(pcd),sidecar=None),split='smoke',difficulty='random_cubes',frame_id='world',length_unit='m',resolution_m=.05,point_representation='solid_volume_samples',bounds=dict(min=[-5,-5,0],max=[5,5,1.6],upper_exclusive=True),geometry_backend='pcd-voxel-v3',semantic_policy_input=False,fixture=True,allow_empty=False,fixture_seed=seed,fixture_boxes=boxes))
        manifest=pool/'manifest.json';manifest.write_text(json.dumps(dict(schema_version='task8-pcd-v1',maps=entries),indent=2)+'\n')
    else:
        manifest=root.parents[0]/'t8-exec-20261026/semantic-pool/index.json'
        entries=json.loads(manifest.read_text())['maps']
    report.update(pool=str(manifest),maps=[],expected_maps=len(entries))
    cache=root/(a.family+'-episodes');cache.mkdir(exist_ok=False)
    sampler=PcdEpisodeSampler(manifest,split=entries[0]['split'],difficulty=None,device='cuda:0',dtype=torch.float32,kin=Kinematics(),robot=GhostRobotGeometry(),profile='sync_v5',map_backend=a.map_backend)
    streams=RandomStreams(4718,1)
    for i,entry in enumerate(entries):
        sampler.entries=[entry];before=dict(sampler.timing)
        with tm.measure('sample_episode'):
            episode=sampler.sample(streams.for_env(0),deadline=START+a.wall_s-2)
        torch.save(episode,cache/(entry['id']+'.pt'))
        row=dict(map_id=entry['id'],cache=str(cache/(entry['id']+'.pt')),sampling_delta_s={k:v-before[k] for k,v in sampler.timing.items()},provenance=episode.scene.provenance(),memory_allocated_bytes=torch.cuda.memory_allocated())
        report['maps'].append(row);report['sampling_stats']=copy.deepcopy(sampler.stats);flush()
    report['scene_tensor_bytes']=sum(x['provenance']['tensor_bytes'] for x in report['maps'])
    report['scene_cache_extrapolation']=dict(map_count=len(entries),resident_tensor_bytes=report['scene_tensor_bytes'],scope='geometry tensors only; planners/episodes/model/replay/grid excluded')


def run(a,root,report,tm,flush):
    import torch
    from task8_sim.env import PcdEpisodeEnv
    from task8_sim.scene import SceneBatch
    from task7_sim.perception import Grid
    from task7_sim.core import Core
    from task7_lower.networks import Actor
    from task7_lower.observation import preprocess
    from task7_lower.replay import Replay
    from task7_lower.training import choose_candidate,drain_history
    prep=json.loads((root/(a.family+'-prepare.json')).read_text())
    if prep['status']!='pass':raise RuntimeError('prepare incomplete')
    episodes=[torch.load(x['cache'],map_location='cuda:0',weights_only=False) for x in prep['maps']]
    env=PcdEpisodeEnv(a.batch,seed=4718,pool=prep['pool'],profile='sync_v5',device='cuda:0',dtype=torch.float32,factory=lambda i,r:episodes[i%len(episodes)],map_backend=a.map_backend)
    env.kin.dls_cuda_graph=True
    # Instrument only this process; on-disk production source stays unchanged.
    tm.wrap(env.kin,'solve_world','IK_solve_world');tm.wrap(env.kin,'dls','IK_DLS_nested')
    tm.wrap(SceneBatch,'raycast','raycast');tm.wrap(SceneBatch,'collide','collision')
    if a.map_backend!='pcd-voxel-v3':
        from task8_sim.primitive_scene import PrimitiveSceneBatch
        tm.wrap(PrimitiveSceneBatch,'raycast','raycast');tm.wrap(PrimitiveSceneBatch,'collide','collision')
    tm.wrap(Grid,'update','grid_update');tm.wrap(Grid,'crop','grid_crop');tm.wrap(Core,'observe','observation_build')
    with tm.measure('reset_factory_cold'):env.reset(deadline=START+a.wall_s-2)
    report['cold_timings']=tm.summary()
    tm.wrap(env.core,'renderer','panorama_including_raycast')
    checkpoint=Path('/root/mm_husky_ws/results/task7/t7.18-v5-20261022/formal-v5-sync/checkpoint-0500000.actor.pt')
    actor=Actor(74).to('cuda:0');ck=torch.load(checkpoint,map_location='cuda:0',weights_only=False)
    actor.load_state_dict(ck['policy']);actor.eval();actor.requires_grad_(False)
    report.update(actor_checkpoint=str(checkpoint),actor_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),actor_device=str(next(actor.parameters()).device),actor_dtype=str(next(actor.parameters()).dtype),state_device=str(env.core.state.q.device),scene_device=str(env.scenes.device),scene_dtype=str(env.scenes.dtype),scene_map_ids=env.map_ids,unique_scene_count=len(set(env.map_ids)),versions=env.versions,replay_capacity=1024,replay_capacity_note='bounded 1024 instead of formal100000; same production push/sample kernels')
    replay=Replay(1024,74,4718,'cuda:0');report['replay_device']=str(replay.map_s.device)
    report['steps']=[];report['transfers']=0;report['sim_committed_s']=0.;report['measured_loop_s']=0.
    flush()
    # No gradients, no optimizer, same stochastic actor selection as training.
    with torch.no_grad():
        for iteration in range(a.warmup+(a.window_steps if a.window_steps is not None else a.steps)):
            warm=iteration<a.warmup;tm.enabled=not warm
            if iteration==a.warmup:tm.clear()
            tm.begin_step()
            torch.cuda.synchronize();start=time.perf_counter()
            if (env.core.terminated|env.core.truncated).any():
                with tm.measure('reset_factory_ended'):env.reset(deadline=START+a.wall_s-2)
            with tm.measure('candidates'):choose_candidate(env)
            c=env.core
            if c.done.all():raise RuntimeError('all rows done; no valid measured action')
            with tm.measure('observation'):obs=c.current_observation()
            with tm.measure('actor_preprocess'):m,v=preprocess(obs)
            with tm.measure('actor_inference'):raw=actor.predict(m,v,eval=False)
            with tm.measure('interaction_ledger'):
                with (root/(f'{a.family}-b{a.batch}-interactions.jsonl')).open('a') as f:
                    f.write(json.dumps(dict(iteration=iteration,stage='intent',active=int((~c.done).sum())))+'\n');f.flush();os.fsync(f.fileno())
            with tm.measure('environment_step'):tr=env.step(raw).transition
            # Preserve old replay >256 and update-before-insert ordering; update is a no-op.
            with tm.measure('replay_consume_loop'):
                for i in torch.where(tr.active)[0].tolist():
                    if len(replay)>256:
                        with tm.measure('replay_sample'):sample=replay.sample(256)
                        with tm.measure('sac_update_noop'):pass
                    with tm.measure('replay_insert'):
                        replay.push({k:v[i:i+1] for k,v in tr.observation.items()},tr.raw_action[i:i+1],tr.reward[i:i+1],{k:v[i:i+1] for k,v in tr.next_observation.items()},tr.mask[i:i+1])
            with tm.measure('drain_history'):drain_history(c)
            torch.cuda.synchronize();elapsed=time.perf_counter()-start
            if warm:report['completed_warmup']+=1
            else:
                active=int(tr.active.sum());sim=float(tr.dt.sum())
                report['completed_steps']+=1;report['transfers']+=active;report['sim_committed_s']+=sim;report['measured_loop_s']+=elapsed
                report['steps'].append(dict(iteration=iteration,wall_s=elapsed,active=active,committed_substeps=int(tr.committed.sum()),sim_s=sim,failures=int((c.last_step_failure>0).sum()),replay_size=len(replay)))
                report['transfers_per_s']=report['transfers']/report['measured_loop_s']
            tm.complete_step();tm.enabled=True;flush()
    report['timing_note']='Nested timing labels overlap and must not be summed; top-level loop wall is denominator. Warmup excluded from step metrics; cold reset kept separately.'
    report['capacity100k_replay_tensor_bytes']=sum(getattr(replay,k).numel()*getattr(replay,k).element_size() for k in ('map_s','map_n','rob_s','rob_n','act','rew','mask'))*100000/1024


if __name__=='__main__':raise SystemExit(main())
