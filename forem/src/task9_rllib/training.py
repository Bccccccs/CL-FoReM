"""PCD training consumer: ordered old-replay updates and explicit full recovery.

Core, observation, candidate selection and limited stepping are reused read-only.
The environment object itself is never pickled: named fields reconstruct its
state without calling reset or bypassing its production pickle rejection.
"""
import hashlib
import contextlib
import json
import os
from pathlib import Path
import random
import signal
import time
import numpy as np
import torch
from task9_lr.diagnostics import BudgetFile, print_record
from task7_lower.observation import VERSION,ACTION_VERSION
from task7_lower.training import (Timings,choose_candidate,limited_step,drain_history,
    without_graph_cache,rng_state,restore_rng,atomic_json,append_json,durable_event)
from task8_sim.env import PcdEpisodeEnv,profile_options
from task8_sim.episode import SamplingIncomplete
from task7_sim.core import Core
from task8_lower.sac import LowerSAC as ControlSAC,update_due
from .native import NativeSAC
from .replay import NativeReplayView

def LowerSAC(vector_dim,device,config):
    torch.backends.cudnn.deterministic=True
    torch.backends.cudnn.benchmark=False
    return (NativeSAC if config.get("learner_stack")=="rllib" else ControlSAC)(vector_dim,device,config)

def make_replay(sac,config,device):
    return NativeReplayView(sac,config["replay_capacity"],device) if config.get("learner_stack")=="rllib" else Replay(config["replay_capacity"],74,config["seed"],device)
from task8_lower.replay import Replay
from .validation import diagnostic_record,check_watchdog
from task8_lower.evaluation import resolve_map_backend
from .evaluation import evaluate

FORMAT='task9.13-full-v1'


def adapter_contract():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))}

def _contract():
    from task9_lr.runtime import source_contract
    return dict(environment=source_contract(),adapter=adapter_contract())


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
    cost_started=time.monotonic();save_costs={}
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
    with without_graph_cache(env):
        data=dict(format=FORMAT,observation_version=VERSION,action_version=ACTION_VERSION,
                  contract=_contract(),map_backend=resolve_map_backend(config),pool_hashes=_pool_hashes(config),config=config,
                  sac=sac.full_state_dict(),replay=replay.state_dict(),
                  environment=environment_state(env),state=state,rng=rng_state())
        write_started=time.monotonic()
        with BudgetFile(tmp) as stream:torch.save(data,stream)
        save_costs['full_write_s']=time.monotonic()-write_started
    sync_started=time.monotonic()
    with tmp.open('rb') as stream:os.fsync(stream.fileno())
    save_costs['full_fsync_s']=time.monotonic()-sync_started
    os.replace(tmp,path)
    # Standalone actor remains compatible with the existing frozen-policy loader.
    actor=path.with_name(path.stem+'.actor.pt');actor_tmp=actor.with_suffix('.tmp')
    actor_started=time.monotonic()
    with BudgetFile(actor_tmp) as stream:torch.save(dict(format='task7-lower-actor-v1',observation_version=VERSION,
        action_version=ACTION_VERSION,synchronous=config['synchronous'],
        versions=dict(checkpoint='task7-lower-actor-v1',observation=VERSION,action=ACTION_VERSION,synchronous=config['synchronous']),
        vector_dim=74 if config['synchronous'] else 75,policy=sac.policy.state_dict(),
        steps=state['steps'],step=state['steps']),stream)
    save_costs['actor_write_s']=time.monotonic()-actor_started
    sync_started=time.monotonic()
    with actor_tmp.open('rb') as stream:os.fsync(stream.fileno())
    save_costs['actor_fsync_s']=time.monotonic()-sync_started
    os.replace(actor_tmp,actor)
    atomic_json(path.with_suffix('.meta.json'),dict(format=FORMAT,steps=state['steps'],
        action_calls=state.get('action_calls',0),env_actions=state.get('env_actions',state['steps']),
        resume_safe=not state.get('unsafe_update',False),stop_reason=state.get('stop_reason')))
    append_json(path.parent/'checkpoint-costs.jsonl',dict(path=path.name,step=state['steps'],full_bytes=path.stat().st_size,actor_bytes=actor.stat().st_size,total_wall_s=time.monotonic()-cost_started,**save_costs))


def load_checkpoint(path,device):
    s=torch.load(path,map_location=device,weights_only=False)
    if s['format']!=FORMAT or s['observation_version']!=VERSION or s['action_version']!=ACTION_VERSION:
        raise ValueError('checkpoint protocol mismatch')
    if s['contract']!=_contract():raise ValueError('environment/observation source contract changed')
    cfg=s['config']
    if s.get('map_backend','pcd-voxel-v3')!=resolve_map_backend(cfg):raise ValueError('checkpoint map_backend mismatch')
    if s['pool_hashes']!=_pool_hashes(cfg):raise ValueError('pool or evaluation manifest changed')
    if s['state'].get('unsafe_update'):raise ValueError('nonfinite/failed partial optimizer update: forensic checkpoint cannot resume')
    sac=LowerSAC(74 if cfg['synchronous'] else 75,device,cfg);sac.load_full_state_dict(s['sac'])
    for optimizer in (sac.policy_optim,sac.critic_optim,sac.alpha_optim):
        for group in optimizer.param_groups:
            if not group.get('capturable',False) and not group.get('fused',False):
                for parameter in group['params']:
                    entry=optimizer.state.get(parameter,{})
                    if torch.is_tensor(entry.get('step')):entry['step']=entry['step'].cpu()
    replay=make_replay(sac,cfg,device)
    replay.load_state_dict(s['replay'])
    env=restore_environment(s['environment'],device)
    restore_rng(s['rng'])
    return sac,replay,env,s['state'],cfg


def consume_transition(sac,replay,state,tr,i,config,failed,timings=None):
    def measure(name):return timings.measure(name) if timings is not None else contextlib.nullcontext()
    transfer=state['steps']+1;losses=state.get('losses')
    sac.set_transfer(transfer)
    if config.get('learner_stack')!='rllib' and update_due(transfer,len(replay),config):
        state['unsafe_update']=True
        with measure('replay_sample_gather'):sampled=replay.sample(config['batch_size'])
        with measure('update'):losses=sac.update_from_batch(sampled,sac.update_count,transfer=transfer)
        state['unsafe_update']=False
    if config.get('learner_stack')=='rllib':state['unsafe_update']=True
    native_losses=replay.push({k:v[i:i+1] for k,v in tr.observation.items()},tr.raw_action[i:i+1],tr.reward[i:i+1],
                {k:v[i:i+1] for k,v in tr.next_observation.items()},tr.mask[i:i+1],
                transfer=transfer,failed=failed[i:i+1])
    if config.get('learner_stack')=='rllib':
        if native_losses is not None:losses=native_losses
        state['unsafe_update']=False
    state['steps']=transfer;state['pending']['cursor']+=1
    state['losses']=losses
    state['attempted']+=int(tr.attempted[i]);state['committed']+=int(tr.committed[i]);state['sim_s']+=float(tr.dt[i])
    return state['losses']


def validate_config(config):
    from task9_lr.runtime import entropy
    entropy(config)
    options=profile_options(config['profile'])
    for key,value in options.items():
        if config.get(key,value)!=value:raise ValueError('profile contradicts '+key)
    if config['update_every_transfers']<1:raise ValueError('UTD interval must be positive')
    if config['log_interval']!=1000:raise ValueError('diagnostics must be every 1000 transitions')
    if not (0<config['batch_size']<config['replay_capacity']):raise ValueError('replay capacity/batch size')
    if config.get('alpha_lr_schedule',config['lr_schedule']) not in ('exp_updates','linear_transfers'):raise ValueError('unsupported alpha LR schedule')
    if config.get('critic_loss','mse') not in ('mse','huber'):raise ValueError('unsupported critic loss')
    if not config.get('huber_delta',1.0)>0:raise ValueError('Huber delta must be positive')
    resolve_map_backend(config)


def train(config,output,*,transfers=None,resume=None,max_wall_s=None,env_factory=PcdEpisodeEnv,evaluator=evaluate,pause_after_consumed=None,resource_guard=None):
    validate_config(config)
    if pause_after_consumed is not None and (isinstance(pause_after_consumed,bool) or not isinstance(pause_after_consumed,int) or not 0<pause_after_consumed<config['total_transfers']):
        raise ValueError('pause_after_consumed must lie strictly inside scientific total_transfers')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    device=torch.device(config.get('device','cuda'))
    if device.type=='cuda' and not torch.cuda.is_available():raise RuntimeError('requested GPU unavailable; no CPU fallback')
    started=time.monotonic();deadline=None if max_wall_s is None else started+max_wall_s
    tm=Timings();stop={'signal':None};old_handlers={}
    def on_signal(sig,frame):stop['signal']=signal.Signals(sig).name
    def cancelled():return bool(stop['signal'] or (output/'STOP').exists())
    last_guard=[0.]
    def check_stop():
        if resource_guard is not None and time.monotonic()-last_guard[0]>=5:
            resource_guard();last_guard[0]=time.monotonic()
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
            with tm.measure('restore'):sac,replay,env,state,stored=load_checkpoint(resume,device)
            if stored!=config:raise ValueError('resume config mismatch')
        else:
            random.seed(config['seed']);np.random.seed(config['seed']);torch.manual_seed(config['seed'])
            if device.type=='cuda':torch.cuda.manual_seed_all(config['seed']);torch.cuda.reset_peak_memory_stats(device)
            env=env_factory(config['environments'],seed=config['seed'],pool=config['pool'],profile=config['profile'],device=device,dtype=torch.float32,split=config['train_split'],map_backend=resolve_map_backend(config))
            env.kin.dls_cuda_graph=config['dls_cuda_graph']
            sac=LowerSAC(74 if config['synchronous'] else 75,device,config)
            replay=make_replay(sac,config,device)
            state=dict(steps=0,pending=None,attempted=0,committed=0,sim_s=0.,segments=0,arrivals=0,timeouts=0,
                failures={str(i):0 for i in range(1,5)},dls=0,ik=0,episodes=0,strict_success=0,wall_s=0.,
                episode_end=dict(fail_limit=0,other_terminated=0,truncated=0),step_failures={str(i):0 for i in range(1,5)},
                action_calls=0,env_actions=0,watchdog={},losses=None,validation_pending=None)
        env.sampling_deadline=deadline;env.sampling_cancel=cancelled
        # transfers is retained only for explicitly separate smoke/test budgets.
        # A profile pause never changes scientific limited_step or LR horizon.
        limit=config['total_transfers'] if transfers is None else transfers
        if pause_after_consumed is not None and transfers is not None:
            raise ValueError('pause gate cannot be combined with transfer limit')
        if pause_after_consumed is not None and state['steps']>=pause_after_consumed:
            raise ValueError('pause gate already reached; resume with gate omitted')
        if limit>config['total_transfers'] or limit<state['steps']:raise ValueError('invalid transfer stop')
        atomic_json(output/'config.json',config)
        runtime=dict(map_backend=resolve_map_backend(config),torch=torch.__version__,cuda=torch.version.cuda,physical_gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),
            device=str(device),gpu=torch.cuda.get_device_name(device) if device.type=='cuda' else None,
            threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads(),affinity=sorted(os.sched_getaffinity(0)),
            tf32_matmul=torch.backends.cuda.matmul.allow_tf32,tf32_cudnn=torch.backends.cudnn.allow_tf32)
        from task9_lr.runtime import import_manifest, scientific_config
        runtime['imports']=import_manifest()
        runtime['scientific_config']=scientific_config(config)
        runtime['learner_stack']=config.get('learner_stack','custom')
        runtime['CUBLAS_WORKSPACE_CONFIG']=os.environ.get('CUBLAS_WORKSPACE_CONFIG')
        runtime['cudnn_deterministic']=torch.backends.cudnn.deterministic
        if hasattr(sac,'native_policy'):
            keys=('seed','gamma','tau','initial_alpha','target_entropy','n_step','grad_clip','target_network_update_freq','training_intensity','num_steps_sampled_before_learning_starts','optimization','replay_buffer_config')
            runtime['actual_native_config']={k:sac.algorithm.config[k] for k in keys}
            runtime['actual_native_config'].update(seed_owner='common FoReM trainer; RLlib seed=None avoids2.40 malformed CUBLAS assignment',critic_loss='Huber delta1',optimizer='native4 Adam eps1e-7',sampling='uniform with replacement',target_initialization='native update_target(tau1)',learner_device=str(sac.device))
        runtime['constants']=dict(gamma=sac.gamma,tau=sac.tau,target_entropy=sac.target_entropy,target_update_interval=sac.target_update_interval,gradient_clip=10)
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
        def profile_pause():
            state['wall_s']+=time.monotonic()-started
            with tm.measure('checkpoint'):
                save_checkpoint(output/'profile.pt',sac,replay,env,state,config)
            p=state['pending']
            result=dict(status='paused_profile',steps=state['steps'],scientific_limit=limit,
                env_actions=state['env_actions'],action_calls=state['action_calls'],updates=sac.update_count,
                pending=None if p is None else dict(ids=p['ids'],cursor=p['cursor'],remaining=len(p['ids'])-p['cursor']),
                validation_pending=state['validation_pending'],timings=tm.summary(),wall_s=time.monotonic()-started,
                checkpoint_bytes=(output/'profile.pt').stat().st_size,replay_size=len(replay),replay_capacity=replay.capacity,
                policy_device=str(next(sac.policy.parameters()).device),replay_device=str(replay.map_s.device),
                optimizer_devices={name:sorted({str(v.device) for entry in opt.state.values() for v in entry.values() if torch.is_tensor(v)}) for name,opt in [('actor',sac.policy_optim),('critic',sac.critic_optim),('alpha',sac.alpha_optim)]},
                peak_gpu_bytes=torch.cuda.max_memory_allocated(device) if device.type=='cuda' else None)
            if state['steps']==250000:
                window=state.get('profile_window_start')
                if window is None:raise ValueError('missing mature profile window baseline')
                def delta(name):
                    return result['timings'].get(name,{}).get('sum_s',0.)-window['timings'].get(name,{}).get('sum_s',0.)
                result['mature_window']=dict(transfers=50000,wall_s=time.monotonic()-started-window['elapsed_s'],
                    checkpoint_s=delta('checkpoint'),evaluation_s=delta('validation'),timings_delta={k:delta(k) for k in result['timings']})
            atomic_json(output/'profile-summary.json',result)
            return result
        scheduled_evaluation()
        if env.core is None:
            check_stop()
            durable_event(output/'sampling-started.jsonl',dict(event='initial_reset',count=env.batch,steps=state['steps']))
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
                    durable_event(output/'sampling-started.jsonl',dict(event='ended_reset',count=int(ended.sum()),steps=state['steps']))
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
                with tm.measure('consume_transition'):losses=consume_transition(sac,replay,state,tr,i,config,pending['failed'],timings=tm)
                step=state['steps']
                if step==200000:
                    state['profile_window_start']=dict(elapsed_s=time.monotonic()-started,timings=tm.summary())
                if step%config['log_interval']==0:
                    with tm.measure('diagnostics'):rec=diagnostic_record(sac,replay,step,losses)
                    rec.update(arrivals=state['arrivals'],segments=state['segments'],failures=state['failures'],step_failures=state['step_failures'],episodes=state['episodes'],elapsed_s=time.monotonic()-started,previous_wall_s=state['wall_s'])
                    state['last_diagnostic']=rec
                    check_watchdog(state['watchdog'],step,rec)
                    append_json(output/'learning.jsonl',rec);print_record(rec)
                if step%config['checkpoint_interval']==0:
                    state['validation_pending']=step
                    with tm.measure('checkpoint'):save_checkpoint(output/f'checkpoint-{step:07d}.pt',sac,replay,env,state,config)
                    scheduled_evaluation()
                if pause_after_consumed is not None and step==pause_after_consumed:
                    return profile_pause()
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
        atomic_json(output/'last-exit-costs.json',dict(worker_body_wall_s=time.monotonic()-started,timings=tm.summary(),sampler_stats=None if env is None or env.sampler is None else env.sampler.stats,sampler_timings=None if env is None or env.sampler is None else env.sampler.timing))
        for sig,handler in old_handlers.items():signal.signal(sig,handler)
