"""PCD training consumer: ordered old-replay updates and explicit full recovery.

Core, observation, candidate selection and limited stepping are reused read-only.
The environment object itself is never pickled: named fields reconstruct its
state without calling reset or bypassing its production pickle rejection.
"""
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import time
import numpy as np
import torch
from task7_lower.observation import VERSION,ACTION_VERSION
from task7_lower.training import (Timings,choose_candidate,limited_step,drain_history,
    without_graph_cache,rng_state,restore_rng,atomic_json,append_json,durable_event)
from task8_sim.env import PcdEpisodeEnv,profile_options
from task8_sim.episode import SamplingIncomplete
from task7_sim.core import Core
from .sac import LowerSAC,update_due
from .replay import Replay
from .diagnostics import diagnostic_record,check_watchdog
from .evaluation import evaluate

FORMAT='task8-lower-full-v1'


def _contract():
    root=Path(__file__).resolve().parents[2]
    names=['src/task8_sim/assets.py','src/task8_sim/scene_cache.py','src/task8_sim/env.py','src/task8_sim/scene.py','src/task8_sim/episode.py',
           'src/task8_sim/robot.py','src/task8_sim/routes.py','src/task8_sim/perception.py',
           'src/task7_sim/core.py','src/task7_lower/observation.py','config/task8/sensor.json',
           'config/task7/robot_geometry.json','src/task8_lower/training.py','src/task8_lower/sac.py',
           'src/task8_lower/replay.py','src/task8_lower/diagnostics.py','src/task8_lower/evaluation.py']
    contract={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}
    cache_root=os.environ.get('TASK8_SCENE_CACHE')
    contract['runtime_scene_cache']=None if not cache_root else dict(root=str(Path(cache_root).resolve()),index_sha256=hashlib.sha256((Path(cache_root)/'index.json').read_bytes()).hexdigest())
    return contract


def _pool_hashes(config):
    return {key:hashlib.sha256(Path(config[key]).read_bytes()).hexdigest()
            for key in ('pool','transfer_pool','evaluation_seeds') if key in config}


def environment_state(env):
    if not isinstance(env,PcdEpisodeEnv):raise TypeError('PCD environment required')
    if env.factory is not None:raise ValueError('checkpoint requires production sampler, not a transient factory')
    attrs=vars(env).copy()
    for key in ('core','factory','sampling_deadline','sampling_cancel'):attrs.pop(key,None)
    # Only pure acceleration caches are omitted. RNG, planners, occupancy, route,
    # Grid, sensor counters, action queues and cached observations are preserved.
    return dict(format='pcd-explicit-state-v1',attributes=attrs,
                core=None if env.core is None else vars(env.core).copy())


def restore_environment(saved,device):
    if saved['format']!='pcd-explicit-state-v1':raise ValueError('PCD state format mismatch')
    env=PcdEpisodeEnv.__new__(PcdEpisodeEnv)
    env.__dict__.update(saved['attributes'])
    env.factory=None;env.sampling_deadline=None;env.sampling_cancel=None
    if saved['core'] is None:env.core=None
    else:
        env.core=Core.__new__(Core);env.core.__dict__.update(saved['core'])
    env.device=torch.empty(0,device=device).device
    env.kin._fixed_cache={};env.kin._dls_graph_cache={}
    if env.sampler is not None:
        env.sampler.device=env.device;env.sampler.deadline=None;env.sampler.cancel=None
        for planner in env.sampler.planners.values():planner.scene.device=env.device
    if env.scenes is not None:
        for scene in env.scenes.scenes:scene.device=env.device
    return env


def save_checkpoint(path,sac,replay,env,state,config):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
    with without_graph_cache(env):
        data=dict(format=FORMAT,observation_version=VERSION,action_version=ACTION_VERSION,
                  contract=_contract(),pool_hashes=_pool_hashes(config),config=config,
                  sac=sac.full_state_dict(),replay=replay.state_dict(),
                  environment=environment_state(env),state=state,rng=rng_state())
        torch.save(data,tmp)
    with tmp.open('rb') as stream:os.fsync(stream.fileno())
    os.replace(tmp,path)
    # Standalone actor remains compatible with the existing frozen-policy loader.
    actor=path.with_name(path.stem+'.actor.pt');actor_tmp=actor.with_suffix('.tmp')
    torch.save(dict(format='task7-lower-actor-v1',observation_version=VERSION,
        action_version=ACTION_VERSION,synchronous=config['synchronous'],
        versions=dict(checkpoint='task7-lower-actor-v1',observation=VERSION,action=ACTION_VERSION,synchronous=config['synchronous']),
        vector_dim=74 if config['synchronous'] else 75,policy=sac.policy.state_dict(),
        steps=state['steps'],step=state['steps']),actor_tmp)
    with actor_tmp.open('rb') as stream:os.fsync(stream.fileno())
    os.replace(actor_tmp,actor)
    atomic_json(path.with_suffix('.meta.json'),dict(format=FORMAT,steps=state['steps'],
        action_calls=state.get('action_calls',0),env_actions=state.get('env_actions',state['steps']),
        resume_safe=not state.get('unsafe_update',False)))


def load_checkpoint(path,device):
    s=torch.load(path,map_location=device,weights_only=False)
    if s['format']!=FORMAT or s['observation_version']!=VERSION or s['action_version']!=ACTION_VERSION:
        raise ValueError('checkpoint protocol mismatch')
    if s['contract']!=_contract():raise ValueError('environment/observation source contract changed')
    cfg=s['config']
    if s['pool_hashes']!=_pool_hashes(cfg):raise ValueError('pool or evaluation manifest changed')
    if s['state'].get('unsafe_update'):raise ValueError('nonfinite/failed partial optimizer update: forensic checkpoint cannot resume')
    sac=LowerSAC(74 if cfg['synchronous'] else 75,device,cfg);sac.load_full_state_dict(s['sac'])
    for optimizer in (sac.policy_optim,sac.critic_optim,sac.alpha_optim):
        for group in optimizer.param_groups:
            if not group.get('capturable',False) and not group.get('fused',False):
                for parameter in group['params']:
                    entry=optimizer.state.get(parameter,{})
                    if torch.is_tensor(entry.get('step')):entry['step']=entry['step'].cpu()
    replay=Replay(s['replay']['capacity'],74 if cfg['synchronous'] else 75,0,device)
    replay.load_state_dict(s['replay'])
    env=restore_environment(s['environment'],device)
    restore_rng(s['rng'])
    return sac,replay,env,s['state'],cfg


def consume_transition(sac,replay,state,tr,i,config,failed):
    transfer=state['steps']+1;losses=state.get('losses')
    sac.set_transfer(transfer)
    if update_due(transfer,len(replay),config):
        state['unsafe_update']=True
        losses=sac.update_from_batch(replay.sample(config['batch_size']),sac.update_count,transfer=transfer)
        state['unsafe_update']=False
    replay.push({k:v[i:i+1] for k,v in tr.observation.items()},tr.raw_action[i:i+1],tr.reward[i:i+1],
                {k:v[i:i+1] for k,v in tr.next_observation.items()},tr.mask[i:i+1],
                transfer=transfer,failed=failed[i:i+1])
    state['steps']=transfer;state['pending']['cursor']+=1
    state['losses']=losses
    state['attempted']+=int(tr.attempted[i]);state['committed']+=int(tr.committed[i]);state['sim_s']+=float(tr.dt[i])
    return state['losses']


def validate_config(config):
    options=profile_options(config['profile'])
    for key,value in options.items():
        if config.get(key,value)!=value:raise ValueError('profile contradicts '+key)
    if config['update_every_transfers']<1:raise ValueError('UTD interval must be positive')
    if config['log_interval']!=1000:raise ValueError('diagnostics must be every 1000 transitions')
    if not (0<config['batch_size']<config['replay_capacity']):raise ValueError('replay capacity/batch size')


def train(config,output,*,transfers=None,resume=None,max_wall_s=None,env_factory=PcdEpisodeEnv,evaluator=evaluate):
    validate_config(config)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    device=torch.device(config.get('device','cuda'))
    if device.type=='cuda' and not torch.cuda.is_available():raise RuntimeError('requested GPU unavailable; no CPU fallback')
    started=time.monotonic();deadline=None if max_wall_s is None else started+max_wall_s
    tm=Timings();stop={'signal':None};old_handlers={}
    def on_signal(sig,frame):stop['signal']=signal.Signals(sig).name
    def cancelled():return bool(stop['signal'] or (output/'STOP').exists())
    def check_stop():
        if cancelled():raise InterruptedError(stop['signal'] or 'STOP file')
        if deadline is not None and time.monotonic()>=deadline:raise TimeoutError('bounded trial wall budget reached')
    for sig in (signal.SIGTERM,signal.SIGINT):old_handlers[sig]=signal.signal(sig,on_signal)
    state=None;env=None;sac=None;replay=None
    try:
        if resume:
            if (output/'interactions.jsonl').exists():
                from task7_lower.recovery import safe_to_resume
                safe,reason=safe_to_resume(resume,output/'interactions.jsonl')
                if not safe:raise RuntimeError('budget-safe resume blocked: '+reason)
            sac,replay,env,state,stored=load_checkpoint(resume,device)
            if stored!=config:raise ValueError('resume config mismatch')
        else:
            random.seed(config['seed']);np.random.seed(config['seed']);torch.manual_seed(config['seed'])
            if device.type=='cuda':torch.cuda.manual_seed_all(config['seed']);torch.cuda.reset_peak_memory_stats(device)
            env=env_factory(config['environments'],seed=config['seed'],pool=config['pool'],profile=config['profile'],device=device,dtype=torch.float32,split=config['train_split'])
            env.kin.dls_cuda_graph=config['dls_cuda_graph']
            sac=LowerSAC(74 if config['synchronous'] else 75,device,config)
            replay=Replay(config['replay_capacity'],74 if config['synchronous'] else 75,config['seed'],device)
            state=dict(steps=0,pending=None,attempted=0,committed=0,sim_s=0.,segments=0,arrivals=0,timeouts=0,
                failures={str(i):0 for i in range(1,5)},dls=0,ik=0,episodes=0,strict_success=0,wall_s=0.,
                episode_end=dict(fail_limit=0,other_terminated=0,truncated=0),step_failures={str(i):0 for i in range(1,5)},
                action_calls=0,env_actions=0,watchdog={},losses=None,validation_pending=None)
        env.sampling_deadline=deadline;env.sampling_cancel=cancelled
        limit=config['total_transfers'] if transfers is None else transfers
        if limit>config['total_transfers'] or limit<state['steps']:raise ValueError('invalid transfer stop')
        atomic_json(output/'config.json',config)
        runtime=dict(torch=torch.__version__,cuda=torch.version.cuda,physical_gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),
            device=str(device),gpu=torch.cuda.get_device_name(device) if device.type=='cuda' else None,
            threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads(),affinity=sorted(os.sched_getaffinity(0)),
            tf32_matmul=torch.backends.cuda.matmul.allow_tf32,tf32_cudnn=torch.backends.cudnn.allow_tf32)
        atomic_json(output/'runtime.json',runtime)
        def scheduled_evaluation():
            pending=state['validation_pending']
            if pending is not None:
                target=output/f'validation-{pending:07d}.json'
                if not target.exists():
                    with tm.measure('validation'):evaluator(sac,config,target,deadline=deadline,cancel=cancelled)
                else:
                    result=json.loads(target.read_text())
                    if not result.get('complete'):raise ValueError('existing evaluation incomplete')
                state['validation_pending']=None
        scheduled_evaluation()
        if env.core is None:
            check_stop()
            with tm.measure('reset'):env.reset()
        while state['steps']<limit:
            check_stop()
            if state['pending'] is None:
                ended=env.core.terminated|env.core.truncated
                if ended.any():
                    c=env.core;hit=ended&c.terminated&(c.failures>=c.failure_limit)
                    state['episode_end']['fail_limit']+=int(hit.sum());state['episode_end']['other_terminated']+=int((ended&c.terminated&~hit).sum())
                    state['episode_end']['truncated']+=int((ended&c.truncated&~c.terminated).sum())
                    state['episodes']+=int(ended.sum());state['strict_success']+=int((ended&c.strict_success).sum())
                    with tm.measure('reset'):env.reset()
                boundary=env.core.done&~(env.core.terminated|env.core.truncated)
                with tm.measure('candidates'):choose_candidate(env)
                c=env.core;zero=boundary&c.done
                state['segments']+=int(zero.sum());state['arrivals']+=int(zero.sum())
                if c.done.all():continue
                with tm.measure('observation'):observation=c.current_observation()
                with tm.measure('inference'):
                    raw=sac.select_action(observation,False)
                    active_ids=torch.where(~c.done)[0]
                    warm=active_ids[torch.arange(len(active_ids),device=device)+state['steps']<config['warmup_transfers']]
                    if len(warm):raw[warm]=torch.rand(len(warm),3,device=device)*2-1
                check_stop();call=state['action_calls']+1
                durable_event(output/'interactions.jsonl',dict(event='step_intent',action_calls=call,env_actions=state['env_actions'],steps=state['steps'],planned=min(int((~c.done).sum()),limit-state['steps'])))
                with tm.measure('environment_step'):tr=limited_step(env,raw,limit-state['steps'])
                state['action_calls']=call;state['env_actions']+=int(tr.active.sum())
                durable_event(output/'interactions.jsonl',dict(event='step_complete',action_calls=call,env_actions=state['env_actions'],steps=state['steps']))
                for attempt in c.attempts:
                    state['dls']+=int(((attempt['branch']<0)&attempt['active']).sum());state['ik']+=int(attempt['active'].sum())
                ends=tr.active&tr.done;state['segments']+=int(ends.sum());state['arrivals']+=int((ends&((tr.reason==0)|(tr.reason==1))).sum());state['timeouts']+=int((ends&(tr.reason==4)).sum())
                for key in state['failures']:
                    state['failures'][key]+=int((ends&(c.failure_kind==int(key))).sum())
                    state['step_failures'][key]+=int((tr.active&(c.last_step_failure==int(key))).sum())
                state['pending']=dict(transition=tr,ids=torch.where(tr.active)[0].tolist(),cursor=0,failed=(c.last_step_failure>0).clone())
                drain_history(c)
            pending=state['pending'];tr=pending['transition']
            while pending['cursor']<len(pending['ids']) and state['steps']<limit:
                check_stop();i=pending['ids'][pending['cursor']]
                with tm.measure('consume_transition'):losses=consume_transition(sac,replay,state,tr,i,config,pending['failed'])
                step=state['steps']
                if step%config['log_interval']==0:
                    with tm.measure('diagnostics'):rec=diagnostic_record(sac,replay,step,losses)
                    rec.update(arrivals=state['arrivals'],segments=state['segments'],failures=state['failures'],step_failures=state['step_failures'],episodes=state['episodes'],elapsed_s=time.monotonic()-started,previous_wall_s=state['wall_s'])
                    state['last_diagnostic']=rec
                    check_watchdog(state['watchdog'],step,rec)
                    append_json(output/'learning.jsonl',rec);print(json.dumps(rec),flush=True)
                if step%config['checkpoint_interval']==0:
                    state['validation_pending']=step
                    with tm.measure('checkpoint'):save_checkpoint(output/f'checkpoint-{step:07d}.pt',sac,replay,env,state,config)
                    scheduled_evaluation()
            if pending['cursor']==len(pending['ids']):state['pending']=None
        state['wall_s']+=time.monotonic()-started
        with tm.measure('checkpoint'):save_checkpoint(output/'final.pt',sac,replay,env,state,config)
        result=dict(state={k:([float(x) for x in v] if k=='losses' and v is not None else v) for k,v in state.items() if k!='pending'},timings=tm.summary(),wall_s=time.monotonic()-started,
            updates=sac.update_count,policy_device=str(next(sac.policy.parameters()).device),
            optimizer_devices={name:sorted({str(v.device) for entry in opt.state.values() for v in entry.values() if torch.is_tensor(v)}) for name,opt in [('actor',sac.policy_optim),('critic',sac.critic_optim),('alpha',sac.alpha_optim)]},
            replay_device=str(replay.map_s.device),peak_gpu_bytes=torch.cuda.max_memory_allocated(device) if device.type=='cuda' else None,
            sampler=None if env.sampler is None else env.sampler.stats)
        atomic_json(output/'summary.json',result);return result
    except (InterruptedError,TimeoutError,FloatingPointError) as error:
        if state is not None and sac is not None and replay is not None and env is not None:
            state['wall_s']+=time.monotonic()-started;state['stop_reason']=str(error)
            save_checkpoint(output/('diverged.pt' if isinstance(error,FloatingPointError) else 'interrupted.pt'),sac,replay,env,state,config)
        raise
    finally:
        for sig,handler in old_handlers.items():signal.signal(sig,handler)
