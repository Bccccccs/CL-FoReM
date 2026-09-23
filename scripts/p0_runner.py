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


def read_seeds(path, episodes):
    seeds=json.loads(Path(path).read_text())
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
    seeds=read_seeds(args.seeds,args.episodes)
    agent.policy.eval()
    records=[];latencies=[]
    sensor_stamps={};subscriptions=[]
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
        sim_start=rospy.get_time() if args.world_type=='gazebo' else None
        ages=[]
        try:
            state=reset_seeded(env,seed)
            row['initial_observation_sha256']=observation_fingerprint(state)
            row['initial_base_tf']=list(env.get_robot_obs().base_tf)
            row['initial_goal']=list(env.unwrapped._ee_planner.gripper_goal_wrist)
            row['layout_sha256']=hashlib.sha256(np.asarray(env.map._floorplan_img,dtype='<f4').tobytes()).hexdigest()
            poses.append(env.get_robot_obs().base_tf[:2])
            trajectory_hash=hashlib.sha256()
            for step in range(1,args.max_episode_steps+1):
                tick=time.monotonic()
                with torch.no_grad(): action=agent.select_action(state,eval=True)
                next_state,reward,done,info=step_with_limit(env,action,step,args.max_episode_steps)
                duration=time.monotonic()-tick
                episode_latency.append(duration);latencies.append(duration)
                if args.world_type=='gazebo':
                    ages.append({k:rospy.get_time()-stamp for k,stamp in sensor_stamps.items()})
                poses.append(env.get_robot_obs().base_tf[:2])
                states.append(np.asarray(next_state[0],dtype=np.float32));actions.append(action)
                tail.append(dict(step=step,state=state[0],action=action,info=info,next_state=next_state[0]))
                trajectory_hash.update(observation_fingerprint(next_state).encode())
                trajectory_hash.update(np.asarray(action,dtype='<f4').tobytes())
                total_reward+=reward;state=next_state
                if done: break
            end=termination(done,info,config['ik_fail_thresh'])
            success=end['primary_reason']=='success'
            row.update(end,subtasks_completed=int(getattr(env,'current_goal',0))+int(success),
                       subtasks_total=len(getattr(env,'goals',[])) or 1,success=success,perfect_success=success and info['nr_base_collisions']==0 and info['nr_kin_failures']==0,
                       collision_count=int(info['nr_base_collisions']),ik_count=int(info['nr_kin_failures']),
                       final_state=state[0],final_info=info,trajectory_sha256=trajectory_hash.hexdigest())
        except Exception as exc:
            row.update(exception=repr(exc),primary_reason='exception',reasons=['exception'],terminated=False,truncated=False)
        row.update(steps=step,reward=total_reward,wall_seconds=time.monotonic()-started,
                   trajectory_length_m=float(np.linalg.norm(np.diff(np.asarray(poses),axis=0),axis=1).sum()) if len(poses)>1 else 0.,
                   simulation_seconds=step*.1 if args.world_type=='sim' else rospy.get_time()-sim_start,
                   sensor_age_seconds=ages)
        dump(output/('episode-%05d-tail.json'%seed),list(tail))
        np.savez_compressed(output/('episode-%05d-trajectory.npz'%seed),base_xy=poses,states=states,actions=actions,control_seconds=episode_latency)
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


def episode_command(args,output,seed):
    seed_file=output/('seed-%05d.json'%seed)
    dump(seed_file,[seed])
    return [sys.executable,'-u',str(Path(__file__).resolve()),'eval','--episode-worker',
            '--checkpoint',args.checkpoint,'--seeds',str(seed_file),'--episodes','1',
            '--output',str(output/('worker-%05d'%seed)),'--task',args.task,
            '--world-type',args.world_type,'--device',args.device,'--seed',str(args.seed),
            '--max-episode-steps',str(args.max_episode_steps),
            '--ik-mode',getattr(args,'ik_mode','legacy'),
            '--ik-iterations',str(getattr(args,'ik_iterations',0))]


def evaluate_isolated(args,output,config):
    """A new solver process per episode prevents BioIK RNG leakage across resets."""
    records=[];latencies=[]
    seeds=read_seeds(args.seeds,args.episodes)
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
    memory=ReplayMemory(args.replay_capacity,args.seed)
    counters=dict(steps=0,updates=0,episodes=0)
    protocol=dict(environment=config,algorithm=args.algorithm,beta=args.beta,seed=args.seed,
                  total_steps=args.steps,batch=args.batch,random_steps=args.random_steps,
                  max_episode_steps=args.max_episode_steps,replay_capacity=args.replay_capacity)
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
    args=p.parse_args()
    if args.ik_mode=='fixed' and args.ik_iterations<1:p.error('fixed IK requires positive --ik-iterations')
    if args.mode=='train' and args.world_type=='gazebo' and args.eval_interval:
        p.error('Gazebo training requires --eval-interval 0; evaluation must use an isolated simulator')
    if args.mode=='eval' and (not args.checkpoint or not args.seeds):p.error('eval requires checkpoint and seeds')
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
    env=env_creator(config)
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
