#!/usr/bin/env python3
"""Task4 fresh ordinary SAC; original networks/update/replay mask unchanged. Finite CUDA pilot only."""
import ray
import torch
import argparse,copy,json,os,resource,subprocess,time
from pathlib import Path
import numpy as np
import task3_sac_entry as base
import task4_identity as ID
from task4_env import Task4Env
from task4_instances import public_instance
ROOT=Path(__file__).resolve().parents[1]
NAMESPACE='task4_openvins_stereo_imu'
def make_contract(env,cfg_sha):
 c=base.make_contract(env.observation_space,env.action_space,cfg_sha,pose_source='openvins_stereo_imu')
 c['schema']=4;c['task_namespace']=NAMESPACE;c['semantic_identity']=ID.verify_runtime();return c

def load_checked(agent,path,expected):
 if expected.get('semantic_identity')!=ID.verify_runtime():raise ValueError('caller expected identity is not actual current runtime')
 ck=torch.load(str(path));c=ck.get('contract',{})
 ID.assert_checkpoint_identity(c,expected['semantic_identity'])
 if c!=expected:raise ValueError('Task4 checkpoint complete contract mismatch')
 # All guards above precede any network/optimizer mutation.
 agent.load_checkpoint(str(path),evaluate=True)
 agent.log_alpha.data.copy_(ck['task4_state']['log_alpha']);agent.alpha_optim.load_state_dict(ck['task4_state']['alpha_optimizer'])
 agent.scheduler_policy_optim.load_state_dict(ck['task4_state']['policy_scheduler']);agent.scheduler_critic_optim.load_state_dict(ck['task4_state']['critic_scheduler'])
 agent.alpha=ck['task4_state']['alpha'];return ck

def save_checked(agent,path,contract,meta):
 agent.save_checkpoint('task4',ckpt_path=str(path));ck=torch.load(str(path));ck['contract']=contract;ck['meta']=meta
 ck['task4_state']={'log_alpha':agent.log_alpha.detach(),'alpha':float(agent.alpha),'alpha_optimizer':agent.alpha_optim.state_dict(),'policy_scheduler':agent.scheduler_policy_optim.state_dict(),'critic_scheduler':agent.scheduler_critic_optim.state_dict()};torch.save(ck,str(path))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['pilot'],required=True);a=ap.parse_args()
 import rospy,rosgraph
 from sac import SAC
 from replay_memory import ReplayMemory
 rospy.init_node('task4_sac_actor',disable_signals=True)
 out=Path(os.environ['FOREM_RES_DIR']);log=Path(os.environ['FOREM_LOG_DIR']);t0=time.monotonic();cfg,csha=base.load_sac_config();quality=json.loads((ROOT/'config/task4/pilot_quality.json').read_text())
 summary={'mode':a.mode,'fresh':True,'seed':0,'update_function':'update_parameters','budget':{'steps':76,'updates':60,'warmup':64,'batch':16,'wall_s':900,'disk_gib':10,'checkpoints':1},'initialization_attempts':[],'error':None,'steps':0,'updates':0,'formal_run':False,'quality_gates':quality}
 env=None;bag=None;evalnode=None;steps=[];episodes=[];losses=[]
 def write(name,v): (out/name).write_text(json.dumps(v,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))
 def reset(seed,phase,expected=None):
  st=time.monotonic();r={'seed':seed,'phase':phase,'success':False};summary['initialization_attempts'].append(r)
  try:
   state=env.reset(seed=seed);spec=env.episode_spec
   if expected is not None and public_instance(spec)!=public_instance(expected):raise RuntimeError('public sealed episode spec mismatch')
   import rospy
   
   commanded=rospy.get_param('/task4/localization/commanded_pose')
   if expected is not None:
    # Task3 base_tf stores the commanded planar start from planning state; Task4 public z=.05 is reset lift only.
    from scipy.spatial.transform import Rotation
    delta_xy=float(np.linalg.norm(np.asarray(commanded[:2])-expected['base_tf'][:2]));delta_yaw=float(abs((Rotation.from_quat(expected['base_tf'][3:]).inv()*Rotation.from_quat(commanded[3:])).as_euler('xyz')[2]))
    r['public_start_check']={'XY_delta_m':delta_xy,'yaw_delta_rad':delta_yaw,'declared_commanded_z_m':commanded[2],'sealed_planar_z_m':expected['base_tf'][2]}
    if delta_xy>1e-6 or delta_yaw>1e-6:raise RuntimeError('public commanded initial mismatch')
   r.update(success=True,wall_s=time.monotonic()-st,spec=spec,commanded_initial=rospy.get_param('/task4/localization/commanded_pose'),public_instance_matches=expected is not None)
   return state
  finally:r['wall_s']=time.monotonic()-st;write('pilot_summary.json',summary)
 try:
  if not torch.cuda.is_available():raise RuntimeError('CUDA unavailable: no CPU fallback')
  ID.verify_runtime();write('container_identity_start.json',ID.semantic_identity());summary['gpu']={'name':torch.cuda.get_device_name(0),'torch':str(torch.__version__),'cuda':str(torch.version.cuda)}
  torch.manual_seed(0);np.random.seed(0);rng=np.random.RandomState(0)
  bag=subprocess.Popen(['rosbag','record','-q','-O',str(out/'evaluation.bag'),'/ground_truth/state'])
  evalnode=subprocess.Popen(['python3','-u',str(ROOT/'scripts/record_task4_quality.py')]);time.sleep(1)
  env=Task4Env(seed=0);state=reset(0,'training');contract=make_contract(env,csha);write('contract.json',contract)
  args=base.build_sac_args(cfg,'cuda',16);agent=SAC(env.observation_space,env.action_space,1,args,5000001);memory=ReplayMemory(76,0)
  summary['fresh_initial_state']={'replay_length':len(memory),'optimizer_lengths':[len(o.state) for o in (agent.policy_optim,agent.critic_optim,agent.alpha_optim)]};before=[p.detach().clone() for p in agent.policy.parameters()]
  episode=0
  while len(steps)<76 and time.monotonic()-t0<900:
   n=len(steps);action=rng.uniform(-1,1,3).astype(np.float32) if n<64 else agent.select_action(state);st=time.monotonic();stamp_before=rospy.get_time()
   row={'step':n,'phase':'train','episode':episode,'stamp_before':stamp_before,'action':action.tolist(),'attempted':True};steps.append(row)
   try:nextstate,reward,done,info=env.step(action)
   except BaseException as e:row.update(error=repr(e),stamp=rospy.get_time());raise
   mask=base.make_mask(done,info.get('truncated',False))
   if not base.finite_transition(state,action,reward,nextstate,mask):raise RuntimeError('nonfinite transition')
   memory.push(state[1],state[0],action,reward,nextstate[1],nextstate[0],mask)
   np.savez_compressed(out/('transition_%03d.npz'%n),robot=state[0],map=state[1],next_robot=nextstate[0],next_map=nextstate[1],action=action,reward=reward,mask=mask)
   row.update(stamp=rospy.get_time(),wall_s=time.monotonic()-st,reward=reward,mask=mask,done=done,info=info)
   if len(memory)>16 and summary['updates']<60:
    st=time.monotonic();ls=agent.update_parameters(memory,16,summary['updates']);torch.cuda.synchronize();losses.append({'losses':list(ls),'wall_s':time.monotonic()-st});summary['updates']+=1
    if not np.isfinite(ls).all():raise RuntimeError('nonfinite SAC loss')
   summary['steps']=len(memory);write('pilot_summary.json',summary)
   with (out/'task_steps.jsonl').open('a') as f:f.write(json.dumps(row,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n');f.flush()
   state=nextstate
   if done:episodes.append({'phase':'train','episode':episode,'steps':len(memory),'info':info,'goal_wrist':env.episode_spec['goal_wrist']});episode+=1;state=reset(episode,'training')
  ckpt=out/'pilot_checkpoint.pt';save_checked(agent,ckpt,contract,{'steps':len(memory),'updates':summary['updates'],'fresh':True,'pilot_only':True})
  summary['checkpoint']={'path':str(ckpt),'sha256':base.sha256_file(ckpt),'bytes':ckpt.stat().st_size}
  agent2=SAC(env.observation_space,env.action_space,1,args,5000001);load_checked(agent2,ckpt,contract)
  diffs=[]
  for i in (0,len(memory)//2,len(memory)-1):
   s=(memory.buffer[i][1],memory.buffer[i][0]);diffs.append(float(abs(agent.select_action(s,eval=True)-agent2.select_action(s,eval=True)).max()))
  summary['roundtrip_action_maxdiff']=max(diffs);summary['policy_delta']=base.policy_delta(agent.policy,before)
  summary['tensor_devices']=sorted({str(p.device) for m in (agent2.policy,agent2.critic,agent2.critic_target) for p in m.parameters()})
  summary['optimizer_tensor_devices']=sorted({str(v.device) for o in (agent2.policy_optim,agent2.critic_optim,agent2.alpha_optim) for values in o.state.values() for k,v in values.items() if torch.is_tensor(v) and k!='step'})
  old=ROOT/'results/task3/t3.5-fix1-gpu/checkpoints/smoke_ckpt.pt';calls=[];original=agent2.load_checkpoint;agent2.load_checkpoint=lambda *x,**y:calls.append('APPLIED')
  try:
   try:load_checked(agent2,old,contract);summary['old_truth_checkpoint_refused_before_apply']=False
   except ValueError:summary['old_truth_checkpoint_refused_before_apply']=not calls
   mutations={}
   for key in contract['semantic_identity']['groups']:
    altered=copy.deepcopy(contract);altered['semantic_identity']['groups'][key]='mutated'
    try:load_checked(agent2,ckpt,altered);mutations[key]=False
    except ValueError:mutations[key]=not calls
   summary['actual_checkpoint_identity_mutations']=mutations
  finally:agent2.load_checkpoint=original
  frozen=json.loads((ROOT/'results/task3/t3.5-inst-r1/episode_instances.json').read_text())['episodes'];state=reset(101,'validation',frozen['101']);ret=0;info={};done=False;evalsteps=0
  while not done and evalsteps<60 and time.monotonic()-t0<900:
   st=time.monotonic();action=agent2.select_action(state,eval=True);row={'step':len(steps),'phase':'validation','episode':101,'stamp_before':rospy.get_time(),'action':action.tolist(),'attempted':True};steps.append(row)
   try:state,r,done,info=env.step(action)
   except BaseException as e:row.update(error=repr(e),stamp=rospy.get_time());raise
   row.update(stamp=rospy.get_time(),wall_s=time.monotonic()-st,reward=r,done=done,info=info);evalsteps+=1;ret+=r
   with (out/'task_steps.jsonl').open('a') as f:f.write(json.dumps(row,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n');f.flush()
  episodes.append({'phase':'validation','episode':101,'steps':evalsteps,'done':done,'return':ret,'info':info,'goal_wrist':env.episode_spec['goal_wrist'],'budget_truncated':not done})
  summary['interface_ok']=summary['steps']==76 and summary['updates']==60 and summary['roundtrip_action_maxdiff']<=1e-6 and summary['old_truth_checkpoint_refused_before_apply'] and all(summary['actual_checkpoint_identity_mutations'].values())
 except BaseException as e:summary['error']=repr(e);summary['interface_ok']=False
 finally:
  if env:
   try:env.close()
   except BaseException as e:summary['close_error']=repr(e)
  for p in (evalnode,bag):
   if p and p.poll() is None:
    p.send_signal(__import__('signal').SIGINT)
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)
  summary.update(wall_s=time.monotonic()-t0,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,gpu_peak_allocated_bytes=torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0,gpu_peak_reserved_bytes=torch.cuda.max_memory_reserved() if torch.cuda.is_available() else 0,episodes=episodes,losses=losses,evaluator_exit=evalnode.returncode if evalnode else None,truth_recorder_exit=bag.returncode if bag else None)
  write('pilot_summary.json',summary);write('task_steps.json',steps);write('container_identity_end.json',ID.semantic_identity())
  poses=[json.loads(s) for s in (out/'poses.jsonl').read_text().splitlines()] if (out/'poses.jsonl').exists() else [];write('poses.json',poses)
  try:write('graph_end.json',rosgraph.Master(rospy.get_name()).getSystemState())
  except Exception:pass
 print(json.dumps(summary,default=str));return 0 if summary.get('interface_ok') else 1
if __name__=='__main__':raise SystemExit(main())
