"""Stage L consumers of read-only EpisodeEnv, full-state persistence, evaluation.
Each active transition is consumed in ascending environment-id order. Update
uses OLD replay (>256) before insertion, preserving the CBL start at #258.
"""
import contextlib
import json
import os
from pathlib import Path
import random
import signal
import time
import numpy as np
import torch
from task7_sim.core import State,Candidate
from task7_sim.candidates import generate_candidates
from .observation import VERSION,ACTION_VERSION
from .sac import LowerSAC
from .replay import Replay

class Timings:
    def __init__(self):self.values={}
    @contextlib.contextmanager
    def measure(self,name):
        if torch.cuda.is_available():torch.cuda.synchronize()
        start=time.perf_counter();yield
        if torch.cuda.is_available():torch.cuda.synchronize()
        self.values.setdefault(name,[]).append(time.perf_counter()-start)
    def summary(self):
        return {k:dict(n=len(v),sum_s=sum(v),p50_s=float(np.quantile(v,.5)),p95_s=float(np.quantile(v,.95)),p99_s=float(np.quantile(v,.99)),max_s=max(v)) for k,v in self.values.items() if v}

@torch.no_grad()
def choose_candidate(env):
    c=env.core;ids=torch.where(c.done&~(c.terminated|c.truncated))[0]
    if not len(ids):return None
    local=c.grid.crop(c.state.base)[ids]
    state=State(c.state.base[ids],c.state.q[ids],c.state.s[ids])
    generated=generate_candidates(local,state,c.route.select(ids),c.kin,synchronous=c.synchronous)
    slot=[]
    for row,i in enumerate(ids.tolist()):
        valid=torch.where(generated.mask[row])[0].tolist();slot.append(valid[int(env.streams.for_env(i).other.integers(len(valid)))])
    slots=torch.tensor(slot,device=ids.device);rows=torch.arange(len(ids),device=ids.device)
    pose=c.state.base.clone();progress=c.state.s.clone();inplace=torch.zeros_like(c.done)
    pose[ids]=generated.world_pose(state.base)[rows,slots]
    progress[ids]=c.route.length[ids] if c.synchronous else generated.progress[rows,slots]
    inplace[ids]=generated.inplace[rows,slots]
    mask=torch.zeros_like(c.done);mask[ids]=True
    env.begin(Candidate(pose,progress,inplace),mask)
    return generated.info

def limited_step(env,raw,remaining):
    """Suspend excess rows only at the exact budget boundary, without transitions.
    Core's public active mask is segment-done. Save/restore all suspended row
    state, including finished/previous-action/cache; suppress boundary finish.
    Selected rows execute the unchanged Core.step. No attempted row is dropped.
    """
    c=env.core;active=torch.where(~c.done)[0]
    if len(active)<=remaining:return env.step(raw).transition
    frozen=active[remaining:];snapshots=[]
    for owner in (c,c.state,c.grid):
        for name,value in vars(owner).items():
            if torch.is_tensor(value) and value.ndim and value.shape[0]==env.batch:
                snapshots.append((owner,name,value[frozen].clone()))
    c.done[frozen]=True;c.finished[frozen]=True
    try:return env.step(raw).transition
    finally:
        for owner,name,value in snapshots:getattr(owner,name)[frozen]=value
        # Spatial state never moved in suspended rows. current_observation
        # replaces previous_action from restored first/queue/visible_previous.
        if c._cached_observation is not None:
            previous=torch.where(c.first[:,None],c.visible_previous,c.queue)
            c._cached_observation['previous_action'][frozen]=previous[frozen]

def drain_history(core):
    """Consume lower-only diagnostics; histories are not transition state.
    No f_k request is made in stage L. Totals are accumulated before draining.
    """
    core.transitions.clear();core.trace.clear();core.attempts=[]

@contextlib.contextmanager
def without_graph_cache(env):
    kin=env.kin;cache=getattr(kin,'_dls_graph_cache',None)
    if cache is not None:kin._dls_graph_cache={}
    try:yield
    finally:
        if cache is not None:kin._dls_graph_cache=cache

def rng_state():
    return dict(python=random.getstate(),numpy=np.random.get_state(),torch=torch.get_rng_state(),cuda=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [])

def restore_rng(s):
    random.setstate(s['python']);np.random.set_state(s['numpy']);torch.set_rng_state(s['torch'].cpu())
    if torch.cuda.is_available() and s['cuda']:torch.cuda.set_rng_state_all([v.cpu() for v in s['cuda']])

def save_checkpoint(path,sac,replay,env,state,config):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
    with without_graph_cache(env):
        torch.save(dict(format='task7-lower-full-v1',observation_version=VERSION,action_version=ACTION_VERSION,config=config,sac=sac.full_state_dict(),replay=replay.state_dict(),env=env,state=state,rng=rng_state()),tmp)
    with tmp.open('rb') as f:os.fsync(f.fileno())
    os.replace(tmp,path)
    trial_metadata={} if 'trial_identity' not in config else {key:config.get(key) for key in ('trial_identity','route_length_bounds','trial_initial_sha256','trial_run')}
    actor=path.with_name(path.stem+'.actor.pt');actor_tmp=actor.with_suffix('.tmp')
    torch.save(dict(format='task7-lower-actor-v1',observation_version=VERSION,action_version=ACTION_VERSION,versions=dict(checkpoint='task7-lower-actor-v1',observation=VERSION,action=ACTION_VERSION,synchronous=config['synchronous']),synchronous=config['synchronous'],vector_dim=74 if config['synchronous'] else 75,policy=sac.policy.state_dict(),steps=state['steps'],step=state['steps'],**trial_metadata),actor_tmp)
    with actor_tmp.open('rb') as f:os.fsync(f.fileno())
    os.replace(actor_tmp,actor)
    atomic_json(path.with_suffix('.meta.json'),dict(action_calls=state.get('action_calls',0),env_actions=state.get('env_actions',state['steps']),steps=state['steps'],format='task7-lower-full-v1',**trial_metadata))

def load_checkpoint(path,device):
    s=torch.load(path,map_location=device,weights_only=False)
    if s['format']!='task7-lower-full-v1' or s['observation_version']!=VERSION:raise ValueError('checkpoint protocol mismatch')
    cfg=s['config'];dim=74 if cfg['synchronous'] else 75
    sac=LowerSAC(dim,device,cfg['total_updates']);sac.load_full_state_dict(s['sac'])
    # map_location also relocates scalar Adam counters. Non-capturable CBL Adam
    # keeps these on CPU; restore that original layout, with moments on GPU.
    for optimizer in (sac.policy_optim,sac.critic_optim,sac.alpha_optim):
        for group in optimizer.param_groups:
            if not group.get('capturable',False) and not group.get('fused',False):
                for parameter in group['params']:
                    entry=optimizer.state.get(parameter,{})
                    if torch.is_tensor(entry.get('step')):entry['step']=entry['step'].cpu()
    replay=Replay(s['replay']['capacity'],dim,0,device);replay.load_state_dict(s['replay'])
    env=s['env']
    # Fixed tensor caches contain original device keys; rebuild on destination.
    env.kin._fixed_cache={};env.kin._dls_graph_cache={}
    if env.sampler is not None:env.sampler.device=torch.device(device)
    restore_rng(s['rng'])
    return sac,replay,env,s['state'],cfg


def atomic_json(path,value):
    path=Path(path);tmp=path.with_suffix('.tmp')
    with tmp.open('w') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def durable_event(path,value):
    with Path(path).open('a') as f:
        f.write(json.dumps(value,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def append_json(path,value):
    with Path(path).open('a') as f:f.write(json.dumps(value,allow_nan=False)+'\n');f.flush()

@torch.no_grad()
def evaluate(sac,config,output):
    """Exactly one accepted episode on each of the 100 fixed validation maps.
    Proposals rejected within a map never cause substitution by another map.
    Evaluation owns separate per-env streams and restores global training RNG.
    """
    from task7_sim.env import EpisodeEnv
    from task7_sim.episode import EpisodeSampler
    saved=rng_state();start=time.perf_counter()
    try:
        sampler=EpisodeSampler(config['pool'],split='validation',device=sac.device)
        sampler.kin.dls_cuda_graph=config['dls_cuda_graph']
        entries=sorted(sampler.entries,key=lambda x:x['id'])
        assert len(entries)==100 and all(sum(e['difficulty']==d for e in entries)==50 for d in ('sparse','standard'))
        def factory(i,streams):
            sampler.entries=[entries[i]];return sampler.sample(streams)
        env=EpisodeEnv(100,factory,seed=config['validation_seed'],synchronous=config['synchronous'],ik_avoid_collision=config.get('ik_avoid_collision',True))
        env.kin.dls_cuda_graph=config['dls_cuda_graph'];env.reset()
        reached=failed=timeout=segments=0;types={str(i):0 for i in range(1,5)};duration=0.
        while not (env.core.terminated|env.core.truncated).all():
            boundary=env.core.done&~(env.core.terminated|env.core.truncated)
            choose_candidate(env);c=env.core
            zero=boundary&c.done
            # Zero-time boundaries are counted immediately, with no transition.
            if zero.any():
                reached+=int(zero.sum());segments+=int(zero.sum())
            if c.done.all():continue
            tr=env.step(sac.select_action(c.current_observation(),True)).transition
            ended=tr.active&tr.done
            reached+=int((ended&((tr.reason==0)|(tr.reason==1))).sum());failed+=int((ended&(c.failure_kind>0)).sum());timeout+=int((ended&(tr.reason==4)).sum());segments+=int(ended.sum())
            duration+=float((tr.dt*tr.active).sum())
            for key in types:types[key]+=int((ended&(c.failure_kind==int(key))).sum())
            drain_history(c)
        end_reasons=dict(fail_limit=int((c.terminated&(c.failures>=c.failure_limit)).sum()),other_terminated=int((c.terminated&(c.failures<c.failure_limit)).sum()),truncated=int((c.truncated&~c.terminated).sum()),failure_limit=int(c.failure_limit))
        rows=[]
        for i,e in enumerate(entries):rows.append(dict(map_id=e['id'],difficulty=e['difficulty'],strict_success=bool(c.strict_success[i]),terminated=bool(c.terminated[i]),truncated=bool(c.truncated[i]),time_s=float(c.time[i]),failures=int(c.failures[i])))
        frames=int(env.totals['sensor_frames'].sum());occ=int(env.totals['fully_occluded_frames'].sum())
        result=dict(episodes=100,segments=segments,arrival_rate=reached/segments if segments else 0,failed_rate=failed/segments if segments else 0,timeout_rate=timeout/segments if segments else 0,failure_type_rates={k:v/segments if segments else 0 for k,v in types.items()},mean_segment_time_s=duration/segments if segments else 0,mean_episode_time_s=float(c.time.mean()),strict_success_rate=float(c.strict_success.float().mean()),G1_fully_occluded_frames=occ,sensor_frames=frames,G1_ratio=occ/frames if frames else 0,episode_end_reasons=end_reasons,wall_s=time.perf_counter()-start,rows=rows)
        atomic_json(output,result);return result
    finally:restore_rng(saved)


def train(config,output,*,transfers=None,resume=None,max_wall_s=None,init_weights=None):
    from task7_sim.env import EpisodeEnv
    output=Path(output)
    if 'trial_identity' in config:
        from .short_task_trial import validate_trial_run,validate_trial_resume
        validate_trial_run(config,output)
        if resume:validate_trial_resume(config,output,resume)
    output.mkdir(parents=True,exist_ok=True)
    if 'trial_identity' in config and not resume:
        ledger=output/'interactions.jsonl'
        if ledger.exists():raise FileExistsError('fresh trial requires a new local interaction ledger; use validated resume')
        durable_event(ledger,dict(event='trial_header',format='task7-short-interactions-v1',trial_run=config['trial_run'],trial_identity=config['trial_identity']))
    tm=Timings();started=time.perf_counter()
    stop={'signal':None}
    def on_signal(sig,frame):stop['signal']=signal.Signals(sig).name
    signal.signal(signal.SIGTERM,on_signal);signal.signal(signal.SIGINT,on_signal)
    if resume:
        if (output/'interactions.jsonl').exists():
            from .recovery import safe_to_resume
            safe,reason=safe_to_resume(resume,output/'interactions.jsonl')
            if not safe:raise RuntimeError('budget-safe resume blocked: '+reason)
        sac,replay,env,state,stored=load_checkpoint(resume,'cuda')
        if stored!=config:raise ValueError('resume config mismatch')
    else:
        random.seed(config['seed']);np.random.seed(config['seed']);torch.manual_seed(config['seed']);torch.cuda.manual_seed_all(config['seed'])
        env=EpisodeEnv(config['environments'],seed=config['seed'],pool=config['pool'],synchronous=config['synchronous'],failure_mode=config.get('failure_mode','terminal'),async_time_penalty=config.get('async_time_penalty',1.0),episode_end_bootstrap=config.get('episode_end_bootstrap',False),ik_avoid_collision=config.get('ik_avoid_collision',True),route_length_bounds=config.get('route_length_bounds'),sampling_deadline=config.get('sampling_deadline'))
        env.kin.dls_cuda_graph=config['dls_cuda_graph']
        with tm.measure('reset'):env.reset()
        sac=LowerSAC(74 if config['synchronous'] else 75,'cuda',config['total_updates'])
        if config.get('trial_initial_state'):
            from .short_task_trial import sha256
            if sha256(config['trial_initial_state'])!=config['trial_initial_sha256']:raise ValueError('trial initialization hash mismatch')
            init=torch.load(config['trial_initial_state'],map_location='cuda',weights_only=False)
            if init['format']!='task7-short-init-v1' or init['identity']!=config['trial_identity']:raise ValueError('trial initialization identity mismatch')
            sac.load_full_state_dict(init['sac']);restore_rng(init['rng'])
        if init_weights:  # task7.18.4 diagnostic only: SAC networks/target/alpha/optimizers from a checkpoint; replay, env and state stay fresh
            ck=torch.load(init_weights,map_location='cpu',weights_only=False,mmap=True)
            if ck['format']!='task7-lower-full-v1' or ck['config']['synchronous']!=config['synchronous']:raise ValueError('init_weights protocol/variant mismatch')
            sac.load_full_state_dict(ck['sac']);del ck
        replay=Replay(config['replay_capacity'],74 if config['synchronous'] else 75,config['seed'],'cuda')
        state=dict(steps=0,pending=None,attempted=0,committed=0,sim_s=0.,segments=0,arrivals=0,timeouts=0,failures={str(i):0 for i in range(1,5)},dls=0,ik=0,episodes=0,strict_success=0,wall_s=0.)
    state.setdefault('episode_end',dict(fail_limit=0,other_terminated=0,truncated=0));state.setdefault('step_failures',{str(i):0 for i in range(1,5)});state.setdefault('action_calls',0);state.setdefault('env_actions',state['steps'])
    limit=config['total_transfers'] if transfers is None else transfers
    last_log=state['steps'];last_cp=state['steps']//config['checkpoint_interval'];losses=None
    Path(output/'config.json').write_text(json.dumps(config,indent=2))
    Path(output/'runtime.json').write_text(json.dumps(dict(torch=torch.__version__,cuda=torch.version.cuda,physical_gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),gpu=torch.cuda.get_device_name(),threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads(),affinity=sorted(os.sched_getaffinity(0)),tf32_matmul=torch.backends.cuda.matmul.allow_tf32,tf32_cudnn=torch.backends.cudnn.allow_tf32,policy_parameters=sum(p.numel() for p in sac.policy.parameters()),critic_parameters=sum(p.numel() for p in sac.critic.parameters())),indent=2))
    validation_pending=state.get('validation_pending')
    if validation_pending and not (output/f'validation-{validation_pending:07d}.json').exists():
        with tm.measure('validation'):evaluate(sac,config,output/f'validation-{validation_pending:07d}.json')
    state['validation_pending']=None
    while state['steps']<limit:
        if stop['signal'] or (output/'STOP').exists():
            state['wall_s']+=time.perf_counter()-started
            save_checkpoint(output/'interrupted.pt',sac,replay,env,state,config)
            raise InterruptedError(stop['signal'] or 'STOP file')
        if max_wall_s is not None and time.perf_counter()-started>=max_wall_s:
            with tm.measure('checkpoint'):save_checkpoint(output/'interrupted.pt',sac,replay,env,state,config)
            raise TimeoutError('bounded trial wall budget reached; full state saved')
        if state['pending'] is None:
            ended=env.core.terminated|env.core.truncated
            if ended.any():
                core=env.core;limit_hit=ended&core.terminated&(core.failures>=core.failure_limit)  # record-only: why episodes ended
                state['episode_end']['fail_limit']+=int(limit_hit.sum());state['episode_end']['other_terminated']+=int((ended&core.terminated).sum())-int(limit_hit.sum());state['episode_end']['truncated']+=int((ended&core.truncated&~core.terminated).sum())
                state['episodes']+=int(ended.sum());state['strict_success']+=int((ended&env.core.strict_success).sum())
                with tm.measure('reset'):env.reset()
            boundary=env.core.done&~(env.core.terminated|env.core.truncated)
            with tm.measure('candidates'):choose_candidate(env)
            c=env.core
            zero=boundary&c.done
            state['segments']+=int(zero.sum());state['arrivals']+=int(zero.sum())
            if c.done.all():continue
            with tm.measure('observation'):
                observation=c.current_observation()
            with tm.measure('inference'):
                raw=sac.select_action(observation,False)
                active_ids=torch.where(~c.done)[0]
                warm_ids=active_ids[torch.arange(len(active_ids),device='cuda')+state['steps']<config['warmup_transfers']]
                if len(warm_ids):raw[warm_ids]=torch.rand(len(warm_ids),3,device='cuda')*2-1
            call=state['action_calls']+1
            with tm.measure('interaction_ledger'):
                durable_event(output/'interactions.jsonl',dict(event='step_intent',action_calls=call,env_actions=state['env_actions'],steps=state['steps'],planned=min(int((~c.done).sum()),limit-state['steps'])))
            with tm.measure('environment_step'):tr=limited_step(env,raw,limit-state['steps'])
            state['action_calls']=call;state['env_actions']+=int(tr.active.sum())
            with tm.measure('interaction_ledger'):
                durable_event(output/'interactions.jsonl',dict(event='step_complete',action_calls=call,env_actions=state['env_actions'],steps=state['steps']))
            active=torch.where(tr.active)[0].tolist()
            for attempt in c.attempts:
                state['dls']+=int(((attempt['branch']<0)&attempt['active']).sum());state['ik']+=int(attempt['active'].sum())
            ends=tr.active&tr.done;state['segments']+=int(ends.sum());state['arrivals']+=int((ends&((tr.reason==0)|(tr.reason==1))).sum());state['timeouts']+=int((ends&(tr.reason==4)).sum())
            for key in state['failures']:state['failures'][key]+=int((ends&(c.failure_kind==int(key))).sum())
            if c.failure_mode=='cbl_continue':  # failed action steps by kind (this step only)
                for key in state['step_failures']:state['step_failures'][key]+=int((tr.active&(c.last_step_failure==int(key))).sum())
            state['pending']=dict(transition=tr,ids=active,cursor=0)
            drain_history(c)
        pending=state['pending'];tr=pending['transition']
        while pending['cursor']<len(pending['ids']) and state['steps']<limit:
            if stop['signal'] or (output/'STOP').exists():
                state['wall_s']+=time.perf_counter()-started
                save_checkpoint(output/'interrupted.pt',sac,replay,env,state,config)
                raise InterruptedError(stop['signal'] or 'STOP file')
            if max_wall_s is not None and time.perf_counter()-started>=max_wall_s:
                with tm.measure('checkpoint'):save_checkpoint(output/'interrupted.pt',sac,replay,env,state,config)
                raise TimeoutError('bounded trial wall budget reached during pending batch; full state saved')
            i=pending['ids'][pending['cursor']]
            if len(replay)>config['batch_size']:
                with tm.measure('replay_sample'):batch=replay.sample(config['batch_size'])
                with tm.measure('sac_update'):losses=sac.update_from_batch(batch,sac.update_count)
            with tm.measure('replay_insert'):
                # Only active rows enter replay. Terminal next-observation belongs
                # to the SAME subgoal, before any new candidate or reset.
                replay.push({k:v[i:i+1] for k,v in tr.observation.items()},tr.raw_action[i:i+1],tr.reward[i:i+1],{k:v[i:i+1] for k,v in tr.next_observation.items()},tr.mask[i:i+1])
            state['steps']+=1;pending['cursor']+=1;state['attempted']+=int(tr.attempted[i]);state['committed']+=int(tr.committed[i]);state['sim_s']+=float(tr.dt[i])
            if state['steps']-last_log>=config['log_interval']:
                rec=dict(step=state['steps'],updates=sac.update_count,elapsed_s=time.perf_counter()-started,previous_wall_s=state['wall_s'],losses=None if losses is None else [float(v) for v in losses],alpha=float(sac.alpha),lr=sac.policy_optim.param_groups[0]['lr'],arrivals=state['arrivals'],segments=state['segments'],failures=state['failures'],timeouts=state['timeouts'],step_failures=state['step_failures'],episode_end=state['episode_end'],episodes=state['episodes'],dls=state['dls'],ik=state['ik'],sensor_frames=int(env.totals['sensor_frames'].sum()),G1_fully_occluded_frames=int(env.totals['fully_occluded_frames'].sum()))
                with torch.no_grad():
                    diagnostic=replay.gather(range(min(256,len(replay))))
                    qs=sac.critic(diagnostic[0],diagnostic[1],diagnostic[2])
                    mean,std=sac.policy.params(diagnostic[0],diagnostic[1])
                    rec.update(Q_mean=[float(q.mean()) for q in qs],Q_abs_max=max(float(q.abs().max()) for q in qs),log_std_min=float(std.min()),log_std_max=float(std.max()),reward_mean=float(diagnostic[3].mean()))
                if losses is not None and not all(np.isfinite(rec['losses']+[rec['Q_abs_max']])):raise FloatingPointError('nonfinite SAC losses/Q')
                with tm.measure('logging'):append_json(output/'learning.jsonl',rec)
                print(json.dumps(rec),flush=True);last_log=state['steps']
            if state['steps']//config['checkpoint_interval']>last_cp:
                state['validation_pending']=state['steps']
                with tm.measure('checkpoint'):save_checkpoint(output/f"checkpoint-{state['steps']:07d}.pt",sac,replay,env,state,config)
                with tm.measure('validation'):evaluate(sac,config,output/f"validation-{state['steps']:07d}.json")
                state['validation_pending']=None
                last_cp=state['steps']//config['checkpoint_interval']
        if pending['cursor']==len(pending['ids']):state['pending']=None
    state['wall_s']+=time.perf_counter()-started
    with tm.measure('checkpoint'):save_checkpoint(output/'final.pt',sac,replay,env,state,config)
    result=dict(state={k:v for k,v in state.items() if k!='pending'},timings=tm.summary(),wall_s=time.perf_counter()-started,updates=sac.update_count,policy_device=str(next(sac.policy.parameters()).device),optimizer_devices=sorted(set(str(v.device) for s in sac.policy_optim.state.values() for v in s.values() if torch.is_tensor(v))),replay_device=str(replay.map_s.device),peak_gpu_bytes=torch.cuda.max_memory_allocated(),sampler=env.sampler.stats)
    atomic_json(output/'summary.json',result);return result
