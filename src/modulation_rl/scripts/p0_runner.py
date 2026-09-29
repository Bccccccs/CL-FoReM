"""Auditable P0 training/evaluation. All outputs go to a new explicit directory."""
import argparse
from collections import Counter, deque
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import numpy as np
import torch
from checkpointing import SEMANTICS, save_training, load_training, load_trusted
from replay_memory import ReplayMemory
from rollouts import termination, step_with_limit, reset_seeded, observation_fingerprint
from sac import SAC


def jsonable(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, Path): return str(value)
    return str(value)


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, default=jsonable))


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def read_seeds(path, episodes, allow_training=False):
    """Evaluation uses validation/test seeds only. World-model data collection (allow_training)
    uses the training range 0-9999 only, so evaluation sets are never consumed as data."""
    seeds=json.loads(Path(path).read_text())
    if allow_training:
        if not isinstance(seeds,list) or len(seeds)<episodes or len(set(seeds))!=len(seeds):
            raise ValueError('Need enough unique episode seeds')
        if any(type(s) is not int or not 0<=s<=9999 for s in seeds):
            raise ValueError('Data collection seeds must be in the training range 0-9999')
        return seeds[:episodes]
    if not isinstance(seeds,list) or len(seeds)<episodes or len(set(seeds))!=len(seeds):
        raise ValueError('Need enough unique episode seeds')
    if any(type(s) is not int or not 10000<=s<=20299 for s in seeds):
        raise ValueError('Evaluation seeds must be in validation/test ranges')
    if any(10100<=s<20000 for s in seeds): raise ValueError('Unallocated seed range')
    return seeds[:episodes]


def provenance(args, config, agent_config, env):
    import stable_baselines3, model, sac
    root=Path(__file__).resolve().parents[3]
    repos={}
    for path in [root,Path(__file__).resolve().parents[1]]:
        def git(*command):
            return subprocess.check_output(['git','--git-dir='+str(path/'.git'),'--work-tree='+str(path),*command])
        try:
            diff=git('diff','HEAD')
            repos[str(path)]={'head':git('rev-parse','HEAD').decode().strip(),
                              'dirty_diff_sha256':hashlib.sha256(diff).hexdigest(),
                              'status':git('status','--short').decode()}
        except subprocess.CalledProcessError: repos[str(path)]={'error':'git unavailable'}
    sources={str(p.relative_to(Path(__file__).parent)):sha(p) for p in Path(__file__).parent.glob('*.py')}
    return dict(run_id=Path(args.output).name, timestamp=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                task_id=os.environ.get('P0_TASK_ID','P0-RUN-022'),agent=os.environ.get('P0_AGENT','P0完成人 /root'),arguments=vars(args),environment=config,
                agent_config=agent_config,semantics=SEMANTICS,repositories=repos,source_sha256=sources,
                container=os.environ.get('P0_CONTAINER',os.environ.get('HOSTNAME')),image_id=os.environ.get('P0_IMAGE_ID','see host docker-inspect.json'),
                python=platform.python_version(),torch=torch.__version__,
                module_paths=dict(sb3=stable_baselines3.__file__,sac=sac.__file__,model=model.__file__),
                checkpoint_sha256=sha(args.checkpoint) if args.checkpoint else None,
                prior_checkpoint_sha256=sha(args.prior_checkpoint) if args.prior_checkpoint else None,
                resume_checkpoint_sha256=sha(args.resume) if args.resume else None,
                checkpoint_counters=load_trusted(args.checkpoint,map_location='cpu').get('counters',{'unknown_legacy':True}) if args.checkpoint else None,
                seed_manifest_sha256=sha(args.seeds) if args.seeds else None,
                observation_shapes=[s.shape for s in env.observation_space.spaces],
                action_low=env.action_space.low,action_high=env.action_space.high,
                resume_kind='partial_environment_reset',collision_ik_counts='cumulative step counts, not independent events')


def checkpoint_hidden_sizes(path):
    data=load_trusted(path,map_location='cpu')
    weights=data['agent']['policy'] if data.get('version')==2 else data['policy_state_dict']
    return [int(v.shape[0]) for k,v in sorted(weights.items()) if k.startswith('post_fc_stack.') and k.endswith('weight')]


def load_weights(agent,path):
    data=load_trusted(path,map_location=next(agent.policy.parameters()).device)
    weights=data['agent']['policy'] if data.get('version')==2 else data['policy_state_dict']
    agent.policy.load_state_dict(weights)
    return data.get('semantics','legacy_weights_reinterpreted_v2')


def evaluate(args,agent,env,output,config):
    seeds=read_seeds(args.seeds,args.episodes,args.save_observations)
    agent.policy.eval()
    records=[];latencies=[]
    sensor_stamps={};subscriptions=[]
    # FOLLOWUP-028: both default off (None/False); when off, nothing below this point runs and
    # episodes.jsonl/trajectory npz are byte-identical to before these two flags existed (see
    # 20260928-followup-spec.md S2, regression-tested in the pipeline log).
    shield=None
    if getattr(args,'shield_config',None):
        import foresight  # noqa: F401 (lazy: only touched when --shield-config is set)
        from shield import Shield
        shield=Shield.from_config(args.shield_config)
    elif args.save_step_info:
        import foresight
    # SCREEN-028 L3 (default off): world-model compensation of a delayed observation. Needs the
    # latency-v1 wrapper (env.transform); lazily imported so a plain run never touches the module.
    wm_comp=None
    if getattr(args,'latency_wm_comp',None):
        from latency_comp import WMCompensator
        wm_comp=WMCompensator.from_config(args.latency_wm_comp)
    if args.world_type=='gazebo':
        import rospy
        from nav_msgs.msg import OccupancyGrid
        from sensor_msgs.msg import LaserScan
        for key,topic,kind in [('costmap','/costmap_node/costmap/costmap',OccupancyGrid),
                               ('lidar','/front/scan',LaserScan)]:
            subscriptions.append(rospy.Subscriber(topic,kind,
                lambda msg,k=key:sensor_stamps.update({k:msg.header.stamp.to_sec()})))
    for index,seed in enumerate(seeds):
        started=time.monotonic(); tail=deque(maxlen=50); poses=[]; episode_latency=[]; states=[]; actions=[]
        row=dict(seed=seed,task=args.task,world=args.world_type,exception=None,success=False,
                 perfect_success=False,checkpoint_sha256=sha(args.checkpoint))
        total_reward=0.; info={}; step=0
        obs_rob=[]; obs_map=[]; rewards=[]; step_dt=[]; subgoal=[]; step_done=[]
        mismatch_cmd=[]; mismatch_exec=[]
        sim_start=rospy.get_time() if args.world_type=='gazebo' else None
        ages=[]
        step_info_rows=[] if args.save_step_info else None
        if shield is not None: shield.reset(seed)
        try:
            state=reset_seeded(env,seed)
            row['initial_observation_sha256']=observation_fingerprint(state)
            row['initial_base_tf']=list(env.get_robot_obs().base_tf)
            row['initial_goal']=list(env.unwrapped._ee_planner.gripper_goal_wrist)
            row['layout_sha256']=hashlib.sha256(np.asarray(env.map._floorplan_img,dtype='<f4').tobytes()).hexdigest()
            poses.append(env.get_robot_obs().base_tf[:2])
            if args.save_observations:
                obs_rob.append(np.asarray(state[0],dtype=np.float32));obs_map.append(np.asarray(state[1],dtype=np.float32))
                subgoal.append(int(getattr(env,'current_goal',0)))
            trajectory_hash=hashlib.sha256()
            for step in range(1,args.max_episode_steps+1):
                tick=time.monotonic(); sim_tick=rospy.get_time() if args.world_type=='gazebo' else None
                with torch.no_grad():
                    action=(agent.select_action(state,eval=args.policy_mode=='deterministic') if wm_comp is None
                            else wm_comp.act(env.transform))
                shield_risk=shield_triggered=None
                if shield is not None:
                    action,shield_risk,shield_triggered=shield.decide(state[0],state[1],action)
                next_state,reward,done,info=step_with_limit(env,action,step,args.max_episode_steps)
                if shield is not None: shield.observe(env,info)
                if step_info_rows is not None: step_info_rows.append(foresight.step_info_row(env,info))
                duration=time.monotonic()-tick
                episode_latency.append(duration);latencies.append(duration)
                if args.world_type=='gazebo':
                    ages.append({k:rospy.get_time()-stamp for k,stamp in sensor_stamps.items()})
                poses.append(env.get_robot_obs().base_tf[:2])
                states.append(np.asarray(next_state[0],dtype=np.float32));actions.append(action)
                if 'mismatch_cmd_base_vel' in info:
                    mismatch_cmd.append(info['mismatch_cmd_base_vel']);mismatch_exec.append(info['mismatch_exec_base_vel'])
                tail.append(dict(step=step,state=state[0],action=action,info=info,next_state=next_state[0]))
                trajectory_hash.update(observation_fingerprint(next_state).encode())
                trajectory_hash.update(np.asarray(action,dtype='<f4').tobytes())
                total_reward+=reward;state=next_state
                if args.save_observations:
                    obs_rob.append(np.asarray(next_state[0],dtype=np.float32));obs_map.append(np.asarray(next_state[1],dtype=np.float32))
                    rewards.append(float(reward));step_done.append(bool(done));subgoal.append(int(getattr(env,'current_goal',0)))
                    step_dt.append(.1 if args.world_type=='sim' else rospy.get_time()-sim_tick)
                if done: break
            end=termination(done,info,config['ik_fail_thresh'])
            success=end['primary_reason']=='success'
            row.update(end,subtasks_completed=int(getattr(env,'current_goal',0))+int(success),
                       subtasks_total=len(getattr(env,'goals',[])) or 1,success=success,perfect_success=success and info['nr_base_collisions']==0 and info['nr_kin_failures']==0,
                       collision_count=int(info['nr_base_collisions']),ik_count=int(info['nr_kin_failures']),
                       final_state=state[0],final_info=info,trajectory_sha256=trajectory_hash.hexdigest())
        except Exception as exc:
            row.update(exception=repr(exc),primary_reason='exception',reasons=['exception'],terminated=False,truncated=False)
        if mismatch_cmd:
            # STAGE0-028 mismatch-v1: only present when RobotEnv actually injected a mismatch
            # (base_vel_gain!=1.0, base_vel_gain_range set, or action_delay_steps!=0); a default
            # (off) run never populates mismatch_cmd, so no new field is added here or below.
            mismatch_diff=np.asarray(mismatch_exec,dtype=np.float64)-np.asarray(mismatch_cmd,dtype=np.float64)
            row.update(mismatch_base_vel_gain=info.get('mismatch_base_vel_gain'),
                       mismatch_action_delay_steps=info.get('mismatch_action_delay_steps'),
                       mismatch_cmd_exec_mean_abs_diff=float(np.abs(mismatch_diff).mean()),
                       mismatch_cmd_exec_max_abs_diff=float(np.abs(mismatch_diff).max()))
        row.update(steps=step,reward=total_reward,wall_seconds=time.monotonic()-started,
                   trajectory_length_m=float(np.linalg.norm(np.diff(np.asarray(poses),axis=0),axis=1).sum()) if len(poses)>1 else 0.,
                   simulation_seconds=step*.1 if args.world_type=='sim' else rospy.get_time()-sim_start,
                   sensor_age_seconds=ages)
        if shield is not None:
            # FOLLOWUP-028 B3: only present when --shield-config is set; a plain run never gets
            # this field. shield.episode_summary()'s per-step risk/triggered arrays only go into
            # the stepinfo npz (gated separately on --save-step-info), not into episodes.jsonl.
            row.update(shield_arm=shield.arm,shield_trigger_count=shield.episode_summary()['shield_trigger_count'])
        if step_info_rows is not None:
            summary=shield.episode_summary() if shield is not None else None
            np.savez_compressed(output/('episode-%05d-stepinfo.npz'%seed),
                kin_failure=np.asarray([r['kin_failure'] for r in step_info_rows],dtype=bool),
                selfcollision=np.asarray([r['selfcollision'] for r in step_info_rows],dtype=bool),
                base_collision=np.asarray([r['base_collision'] for r in step_info_rows],dtype=bool),
                dist_to_desired=np.asarray([r['dist_to_desired'] for r in step_info_rows],dtype=np.float32),
                rot_dist_to_desired=np.asarray([r['rot_dist_to_desired'] for r in step_info_rows],dtype=np.float32),
                nr_kin_failures=np.asarray([r['nr_kin_failures'] for r in step_info_rows],dtype=np.int32),
                goal_to_base_distance=np.asarray([r['goal_to_base_distance'] for r in step_info_rows],dtype=np.float32),
                **({} if summary is None else dict(
                    shield_arm=summary['arm'],
                    shield_risk=np.asarray(summary['shield_risk'],dtype=np.float32),
                    shield_triggered=np.asarray(summary['shield_triggered'],dtype=bool))))
        dump(output/('episode-%05d-tail.json'%seed),list(tail))
        mismatch_npz=dict(mismatch_cmd_base_vel=mismatch_cmd,mismatch_exec_base_vel=mismatch_exec) if mismatch_cmd else {}
        np.savez_compressed(output/('episode-%05d-trajectory.npz'%seed),base_xy=poses,states=states,actions=actions,control_seconds=episode_latency,**mismatch_npz)
        if args.save_observations:
            # observations[0:T+1] with actions[0:T]; the normalized action is what env.step received.
            complete=row['exception'] is None and len(obs_rob)==len(actions)+1
            np.savez_compressed(output/('episode-%05d-observations.npz'%seed),
                robot_state=np.asarray(obs_rob,dtype=np.float32).reshape(-1,*(env.observation_space.spaces[0].shape)),
                local_map=np.asarray(obs_map,dtype=np.float32).reshape(-1,*(env.observation_space.spaces[1].shape)),
                action=np.asarray(actions,dtype=np.float32).reshape(-1,env.action_space.shape[0]),
                reward=np.asarray(rewards,dtype=np.float32),dt=np.asarray(step_dt,dtype=np.float32),
                done=np.asarray(step_done,dtype=bool),subgoal_index=np.asarray(subgoal,dtype=np.int16),
                terminated=bool(row.get('terminated',False)),truncated=bool(row.get('truncated',False)),
                complete=complete,seed=seed,policy_mode=args.policy_mode,
                checkpoint_sha256=row['checkpoint_sha256'],semantics=SEMANTICS)
        with (output/'episodes.jsonl').open('a') as f:f.write(json.dumps(row,default=jsonable)+'\n')
        records.append(row)
        print('EVAL',index+1,len(seeds),seed,row['primary_reason'],step,flush=True)
    summary=summarize(records,latencies,args.world_type,config)
    dump(output/'summary.json',summary)
    if summary['exceptions']:raise RuntimeError('Evaluation contains exceptions; see episodes.jsonl')


def summarize(records,latencies,world_type,config):
    return dict(planned=len(records),valid=sum(r['exception'] is None for r in records),
                 exceptions=sum(r['exception'] is not None for r in records),
                 success_rate=float(np.mean([r['success'] for r in records])),
                 perfect_success_rate=float(np.mean([r['perfect_success'] for r in records])),
                 failure_distribution=dict(Counter(r['primary_reason'] for r in records)),
                 mean_collision_count=float(np.mean([r.get('collision_count',0) for r in records])),
                 mean_ik_count=float(np.mean([r.get('ik_count',0) for r in records])),
                 control_seconds=dict(zip(['p50','p95','p99'],np.percentile(latencies,[50,95,99]).tolist())) if latencies else {},
                 control_overrun_rate=float(np.mean(np.asarray(latencies)>(.1 if world_type=='sim' else config['time_step']))) if latencies else None,
                 mean_trajectory_length_m=float(np.mean([r['trajectory_length_m'] for r in records])),
                 semantics=SEMANTICS)


def screen_flags(args):
    """SCREEN-028 switches, forwarded to per-episode workers only when non-default (a default run
    builds exactly the same worker command line as before these flags existed)."""
    out=[]
    for name,default in [('obs_latency_steps',0),('map_latency_steps',0),('obs_action_history',0),
                         ('dyn_map_horizon',20)]:
        if getattr(args,name,default)!=default:out+=['--'+name.replace('_','-'),str(getattr(args,name))]
    if getattr(args,'dyn_map_mode','current')!='current':out+=['--dyn-map-mode',args.dyn_map_mode]
    if getattr(args,'dyn_freeze',False):out+=['--dyn-freeze']
    if getattr(args,'latency_wm_comp',None):out+=['--latency-wm-comp',args.latency_wm_comp]
    return out


def episode_command(args,output,seed):
    seed_file=output/('seed-%05d.json'%seed)
    dump(seed_file,[seed])
    return [sys.executable,'-u',str(Path(__file__).resolve()),'eval','--episode-worker',
            '--checkpoint',args.checkpoint,'--seeds',str(seed_file),'--episodes','1',
            '--output',str(output/('worker-%05d'%seed)),'--task',args.task,
            '--world-type',args.world_type,'--device',args.device,'--seed',str(args.seed),
            '--max-episode-steps',str(args.max_episode_steps),
            '--ik-mode',getattr(args,'ik_mode','legacy'),
            '--ik-iterations',str(getattr(args,'ik_iterations',0)),
            '--policy-mode',getattr(args,'policy_mode','deterministic'),
            '--base-vel-gain',str(getattr(args,'base_vel_gain',1.0)),
            '--action-delay-steps',str(getattr(args,'action_delay_steps',0))]+(
            ['--save-observations'] if getattr(args,'save_observations',False) else [])+(
            ['--base-vel-gain-range',str(args.base_vel_gain_range[0]),str(args.base_vel_gain_range[1])]
            if getattr(args,'base_vel_gain_range',None) else [])+(
            ['--save-step-info'] if getattr(args,'save_step_info',False) else [])+(
            ['--shield-config',args.shield_config] if getattr(args,'shield_config',None) else [])+screen_flags(args)


def evaluate_isolated(args,output,config):
    """A new solver process per episode prevents BioIK RNG leakage across resets."""
    records=[];latencies=[]
    seeds=read_seeds(args.seeds,args.episodes,args.save_observations)
    for seed in seeds:
        command=episode_command(args,output,seed)
        worker=output/('worker-%05d'%seed)
        with (output/('worker-%05d.log'%seed)).open('w') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        episode_file=worker/'episodes.jsonl'
        if episode_file.exists():
            row=json.loads(episode_file.read_text().strip())
            if result.returncode and row.get('exception') is None:
                row.update(exception='Worker exit %s'%result.returncode,success=False,perfect_success=False,primary_reason='exception',reasons=['exception'])
        else:
            row=dict(seed=seed,task=args.task,world=args.world_type,exception='Worker exit %s before episode record; see worker log'%result.returncode,
                     success=False,perfect_success=False,primary_reason='exception',reasons=['exception'],
                     trajectory_length_m=0.,steps=0,terminated=False,truncated=False)
        for artifact in worker.glob('episode-*'):
            shutil.copy2(str(artifact),str(output/artifact.name))
        trajectory=output/('episode-%05d-trajectory.npz'%seed)
        if trajectory.exists():
            with np.load(trajectory) as data:latencies.extend(data['control_seconds'].tolist())
        records.append(row)
        with (output/'episodes.jsonl').open('a') as f:f.write(json.dumps(row,default=jsonable)+'\n')
        print('EVAL',len(records),len(seeds),seed,row['primary_reason'],row['steps'],flush=True)
    summary=summarize(records,latencies,args.world_type,config)
    summary['episode_isolation']='fresh process, including BioIK RNG'
    dump(output/'summary.json',summary)
    if summary['exceptions']:raise RuntimeError('Evaluation contains exceptions; see episodes.jsonl')


def train(args,agent,prior,env,output,config):
    memory=ReplayMemory(args.replay_capacity,args.seed,compact_maps=args.replay_compact_maps)
    counters=dict(steps=0,updates=0,episodes=0)
    protocol=dict(environment=config,algorithm=args.algorithm,beta=args.beta,seed=args.seed,
                  total_steps=args.steps,batch=args.batch,random_steps=args.random_steps,
                  max_episode_steps=args.max_episode_steps,replay_capacity=args.replay_capacity)
    if args.replay_compact_maps:protocol['replay_compact_maps']=True  # SCREEN-028: only recorded when on
    if args.resume:
        counters=load_training(args.resume,agent,memory,protocol,prior)['counters']
    episode_step=0;started=time.monotonic(); losses=[]
    original=[p.detach().clone() for p in agent.policy.parameters()]
    state=reset_seeded(env,(args.seed+counters['episodes'])%10000)
    try:
        while counters['steps']<args.steps:
            with torch.no_grad():
                action=env.action_space.sample() if counters['steps']<args.random_steps else agent.select_action(state)
            episode_step+=1
            next_state,reward,done,info=step_with_limit(env,action,episode_step,args.max_episode_steps)
            end=termination(done,info,config['ik_fail_thresh'])
            memory.push(np.asarray(state[1],dtype=np.float32),np.asarray(state[0],dtype=np.float32),action,reward,
                        np.asarray(next_state[1],dtype=np.float32),np.asarray(next_state[0],dtype=np.float32),end['bootstrap_mask'])
            counters['steps']+=1
            if len(memory)>=max(args.batch,args.random_steps):
                loss=(agent.update_parameters(memory,args.batch,counters['updates']) if prior is None else
                      agent.update_parameters_modified(memory,args.batch,counters['updates'],prior))
                if not np.isfinite(loss).all():raise FloatingPointError('Nonfinite training loss')
                losses.append(loss);counters['updates']+=1
            state=next_state
            if done:
                counters['episodes']+=1;episode_step=0
                state=reset_seeded(env,(args.seed+counters['episodes'])%10000)
            if counters['steps']%args.save_interval==0:
                save_training(output/('step-%07d.pt'%counters['steps']),agent,memory,counters,protocol,prior)
            if args.eval_interval and counters['steps']%args.eval_interval==0:
                checkpoint=output/('validation-%07d.pt'%counters['steps'])
                save_training(checkpoint,agent,memory,counters,protocol,prior)
                seeds=output/'validation-seeds.json'
                dump(seeds,list(range(10000,10020)))
                command=[sys.executable,'-u',str(Path(__file__).resolve()),'eval',
                         '--checkpoint',str(checkpoint),'--seeds',str(seeds),
                         '--output',str(output/('validation-%07d'%counters['steps'])),
                         '--task',args.task,'--world-type',args.world_type,'--device',args.device,
                         '--max-episode-steps',str(args.max_episode_steps),
                         '--ik-mode',args.ik_mode,'--ik-iterations',str(args.ik_iterations)]
                with (output/('validation-%07d.log'%counters['steps'])).open('w') as log:
                    code=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT).returncode
                # A failed validation is recorded, not allowed to silently vanish or kill training.
                with (output/'validation-status.jsonl').open('a') as f:
                    f.write(json.dumps(dict(steps=counters['steps'],returncode=code))+'\n')
            if counters['steps']%100==0:
                print('TRAIN',counters,'seconds',round(time.monotonic()-started,2),flush=True)
    finally:
        save_training(output/'latest.pt',agent,memory,counters,protocol,prior)
    change=max((p-q).abs().max().item() for p,q in zip(agent.policy.parameters(),original))
    summary=dict(counters,actor_max_parameter_change=change,seconds=time.monotonic()-started,
                 losses_last=losses[-1] if losses else None,checkpoint_sha256=sha(output/'latest.pt'),
                 gpu_peak_allocated_bytes=torch.cuda.max_memory_allocated() if agent.device.type=='cuda' else 0,
                 scope='Engineering training correctness; not convergence',resume_kind='partial_environment_reset')
    dump(output/'summary.json',summary)
    if counters['updates'] and change==0:raise RuntimeError('Actor did not change')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['train','eval'])
    p.add_argument('--episode-worker',action='store_true',help=argparse.SUPPRESS)
    p.add_argument('--output',required=True)
    p.add_argument('--checkpoint');p.add_argument('--resume');p.add_argument('--prior-checkpoint')
    p.add_argument('--algorithm',choices=['sac','prior_sac','prior_sac_legacy_alpha'],default='sac')
    p.add_argument('--beta',type=float,default=.2)
    p.add_argument('--task',default='simpleobstacle');p.add_argument('--world-type',default='sim',choices=['sim','gazebo'])
    p.add_argument('--seed',type=int,default=11);p.add_argument('--seeds');p.add_argument('--episodes',type=int,default=20)
    p.add_argument('--steps',type=int,default=2000);p.add_argument('--batch',type=int,default=16)
    p.add_argument('--random-steps',type=int,default=128);p.add_argument('--replay-capacity',type=int,default=5000)
    p.add_argument('--eval-interval',type=int,default=50000)
    p.add_argument('--save-interval',type=int,default=20000);p.add_argument('--max-episode-steps',type=int,default=2000)
    p.add_argument('--device',default='cuda',choices=['cpu','cuda'])
    p.add_argument('--ik-mode',choices=['legacy','diagnostic','fixed'],default='legacy')
    p.add_argument('--ik-iterations',type=int,default=0)
    p.add_argument('--policy-mode',choices=['deterministic','stochastic'],default='deterministic',
                   help='eval action selection; stochastic only for world-model data collection')
    p.add_argument('--save-observations',action='store_true',
                   help='world-model data collection: save observations[0:T+1] incl. maps; training seeds only')
    p.add_argument('--base-vel-gain',type=float,default=1.0,
                   help='STAGE0-028 mismatch-v1: fixed chassis velocity gain applied after exec clipping/delay. Default 1.0 is identity.')
    p.add_argument('--base-vel-gain-range',type=float,nargs=2,default=None,metavar=('LO','HI'),
                   help='STAGE0-028 mismatch-v1: sample chassis velocity gain uniformly in [LO,HI] once per episode; overrides --base-vel-gain when set.')
    p.add_argument('--action-delay-steps',type=int,default=0,
                   help='STAGE0-028 mismatch-v1: delay chassis commands by this many steps (0 = no delay, identity).')
    p.add_argument('--save-step-info',action='store_true',
                   help='FOLLOWUP-028 B2: write episode-XXXXX-stepinfo.npz (kin_failure/selfcollision/'
                        'base_collision/dist_to_desired/rot_dist_to_desired/nr_kin_failures/goal_to_base_distance '
                        'per step). Default off; off produces no new file and no new episodes.jsonl field.')
    p.add_argument('--shield-config',default=None,
                   help='FOLLOWUP-028 B3: path to a shield.py JSON config (default None = shield disabled, '
                        'no new module imported, no new episodes.jsonl/stepinfo field).')
    p.add_argument('--obs-latency-steps',type=int,default=0,
                   help='SCREEN-028 latency-v1: the policy at step t sees the full observation of step t-k '
                        '(initial obs for t<k). Env reward/termination/collision/IK use the true state. Default 0 = off.')
    p.add_argument('--map-latency-steps',type=int,default=0,
                   help='SCREEN-028 latency-v1: delay only local_map by k steps (robot_state stays current). Default 0 = off.')
    p.add_argument('--obs-action-history',type=int,default=0,
                   help='SCREEN-028 latency-v1: append the k most recent executed actions (3k dims, oldest first, '
                        'zero padded) to robot_state; changes the observation dimension. Default 0 = off.')
    p.add_argument('--dyn-map-mode',choices=['current','future','past'],default='current',
                   help='SCREEN-028 dynmap-v1 (dynObstacle task only): additionally draw the obstacles h steps ahead '
                        '(future) or behind (past) in the policy-input local map (union, single channel). Collision '
                        'and reward always use the real current map. Default current = off.')
    p.add_argument('--dyn-map-horizon',type=int,default=20,help='SCREEN-028 dynmap-v1: h in steps of 0.1 s (default 20 = 2.0 s, D56; D54 originally 5).')
    p.add_argument('--dyn-freeze',action='store_true',
                   help='SCREEN-028 dynmap-v1 (harm test): obstacles stay at their initial positions. Default off.')
    p.add_argument('--latency-wm-comp',default=None,
                   help='SCREEN-028 L3 (eval only): JSON with encoder_checkpoint/dynamics_checkpoint(/device); the '
                        'policy head acts on world-model-rolled features of the delayed observation. Default None = off.')
    p.add_argument('--replay-compact-maps',action='store_true',
                   help='SCREEN-028: store replay local maps as bool (bit-identical samples, 4x less RAM/disk). Default off.')
    args=p.parse_args()
    if args.ik_mode=='fixed' and args.ik_iterations<1:p.error('fixed IK requires positive --ik-iterations')
    if min(args.obs_latency_steps,args.map_latency_steps,args.obs_action_history)<0:p.error('latency/history steps must be >=0')
    if args.dyn_map_horizon<0:p.error('--dyn-map-horizon must be >=0')
    if (args.dyn_map_mode!='current' or args.dyn_freeze) and args.task.lower()!='dynobstacle':
        p.error('--dyn-map-mode/--dyn-freeze require --task dynobstacle')
    if args.latency_wm_comp and not (args.mode=='eval' and (args.obs_latency_steps or args.map_latency_steps) and not args.obs_action_history):
        p.error('--latency-wm-comp needs eval mode, a latency switch, and no --obs-action-history')
    if args.base_vel_gain_range is not None and not (0<args.base_vel_gain_range[0]<=args.base_vel_gain_range[1]):
        p.error('--base-vel-gain-range requires 0 < LO <= HI')
    if args.action_delay_steps<0:p.error('--action-delay-steps must be >=0')
    if args.mode=='train' and args.world_type=='gazebo' and args.eval_interval:
        p.error('Gazebo training requires --eval-interval 0; evaluation must use an isolated simulator')
    if args.mode=='eval' and (not args.checkpoint or not args.seeds):p.error('eval requires checkpoint and seeds')
    if args.policy_mode=='stochastic' and not args.save_observations:
        p.error('stochastic policy is only for data collection (--save-observations)')
    if args.mode=='train' and args.algorithm!='sac' and not args.prior_checkpoint:p.error('prior algorithm requires prior checkpoint')
    output=Path(args.output);output.mkdir(parents=True,exist_ok=False)
    from modulation.utils import parse_args,env_creator,set_seed
    _,_,config,_=parse_args(Path(__file__).parent,framework='ray',raw_args=[
        '--env','husky_ur5','--task',args.task,'--world_type',args.world_type,'--seed',str(args.seed)])
    config.update(node_handle='p0_'+args.mode,eval=False)
    if args.mode=='eval':config['logpath']=str(Path(config['logpath']).resolve())
    if args.world_type=='gazebo':
        config.update(perception_style='all',execute_style='direct')
    coordinator=args.mode=='eval' and not args.episode_worker
    if not coordinator:set_seed(args.seed)
    torch.backends.cudnn.benchmark=False
    torch.backends.cudnn.deterministic=True
    agent_config=dict(device=args.device,gamma=config['gamma'],tau=config['tau'],initial_alpha=config['initial_alpha'],
                      prior_beta=None if args.algorithm=='prior_sac_legacy_alpha' else args.beta,
                      model={'custom_model_config':{'post_fcnet_hiddens':[256,256]}})
    # BioIK otherwise seeds from random_device and selects a thread count itself.
    import rospy
    os.environ['P0_BIOIK_MAX_ITERATIONS']=str(args.ik_iterations if args.ik_mode=='fixed' else 0)
    if args.ik_mode!='legacy':os.environ['P0_IK_TRACE']=str(output/'ik-trace')
    else:os.environ.pop('P0_IK_TRACE',None)
    solver='bio_ik/BioIKKinematicsPlugin' if args.ik_mode=='legacy' else 'modulation_rl/P0BioIKKinematicsPlugin'
    for group in ['manipulator','whole_body']:
        rospy.set_param('/robot_description_kinematics/'+group+'/kinematics_solver',solver)
        rospy.set_param('/robot_description_kinematics/'+group+'/random_seed',args.seed)
        rospy.set_param('/robot_description_kinematics/'+group+'/threads',1)
    config.update(bioik_random_seed=args.seed,bioik_threads=1)
    if args.ik_mode!='legacy':config.update(bioik_mode=args.ik_mode,bioik_iterations=args.ik_iterations,ik_semantics='p0-ik-budget-v1')
    config.update(base_vel_gain=args.base_vel_gain,
                 base_vel_gain_range=tuple(args.base_vel_gain_range) if args.base_vel_gain_range else None,
                 action_delay_steps=args.action_delay_steps)
    if args.base_vel_gain!=1.0 or args.base_vel_gain_range is not None or args.action_delay_steps!=0:
        config['mismatch_semantics']='mismatch-v1'
    env=env_creator(config)
    # SCREEN-028: policy-input wrapper only when a latency/dynmap switch is on; tags land in config
    # (=> manifest and the training protocol) only then, so default runs are unchanged.
    from policy_input import wrap_if_needed
    env,screen_tags=wrap_if_needed(env,args)
    config.update(screen_tags)
    try:
        if args.mode=='eval':
            agent_config['model']['custom_model_config']['post_fcnet_hiddens']=checkpoint_hidden_sizes(args.checkpoint)
        agent=None if coordinator else SAC(env.observation_space,env.action_space,1,agent_config,args.steps)
        manifest=provenance(args,config,agent_config,env)
        if args.checkpoint:
            manifest['loaded_weight_semantics']=(load_trusted(args.checkpoint,map_location='cpu').get('semantics','legacy_weights_reinterpreted_v2') if coordinator else load_weights(agent,args.checkpoint))
        dump(output/'manifest.json',manifest)
        if args.mode=='eval':
            if args.episode_worker:evaluate(args,agent,env,output,config)
            else:
                env.close();env=None
                evaluate_isolated(args,output,config)
        else:
            prior=None
            if args.algorithm!='sac':
                from types import SimpleNamespace
                from model import GaussianPolicy
                prior=SimpleNamespace(policy=GaussianPolicy(env.observation_space[1],env.observation_space[0],
                    env.action_space.shape[0],checkpoint_hidden_sizes(args.prior_checkpoint),env.action_space,
                    use_sde=False).to(agent.device))
                load_weights(prior,args.prior_checkpoint)
                prior.policy.requires_grad_(False);prior.policy.eval()
            train(args,agent,prior,env,output,config)
    finally:
        if env is not None:env.close()


if __name__=='__main__':main()
