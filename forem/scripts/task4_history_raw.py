#!/usr/bin/env python3
"""Bounded multi-episode raw diagnostic actor (task4.3.5); truth is recorded by a separate rosbag process.
Same Task4Env, same seed0 reset and original 76-command fixture each episode, 0 learning updates; the only difference to
task4_motion_raw.py is that ONE Gazebo/VIO lifecycle is reused for several consecutive episodes so that the inter-episode
history (previous-episode end state, teleport, settling) is present in the raw record. SRC0132.
"""
import hashlib,json,math,os,signal,subprocess,sys,threading,time
from pathlib import Path

RECORD_TOPICS=('/clock','/task4/stereo/left/image_raw','/task4/stereo/right/image_raw',
 '/task4/stereo/left/camera_info','/task4/stereo/right/camera_info','/task4/plugin/imu',
 '/task4/imu/data_raw','/ov_msckf/poseimu','/ov_msckf/odomimu','/ov_msckf/trackhist',
 '/ov_msckf/points_msckf','/ov_msckf/points_slam','/ov_msckf/loop_feats',
 '/forem/pose/estimated','/task4/localization/status','/cmd_vel',
 '/husky_velocity_controller/cmd_vel','/eff_joint_traj_controller/command',
 '/eff_joint_traj_controller/follow_joint_trajectory/goal','/joint_states',
 '/gazebo/link_states','/ground_truth/state','/tf','/tf_static')
MAX_EPISODES=12
WHOLE_WALL_CAP=500
BODY_WALL_CAP=420
RAW_SIM_CAP=400
DISK_CAP=12*1024**3
EPISODE_WALL_ESTIMATE=40  # original reset ~16.5 s + <=76 steps; refuse a new episode if less than this remains
WHEEL_JOINTS=('front_left_wheel','front_right_wheel','rear_left_wheel','rear_right_wheel')

def wrap_reset_zero_wheels(robot,zero_wheels,log):
 """Diagnostic intervention (task4.3.5, SRC0134): zero the four wheel joint angles BEFORE the original robot reset
 (teleport + arm reset + fresh VIO init). Wheel angles are not part of any observation, action, reward or termination."""
 original=robot.reset
 def reset(initial_base_pose,initial_joint_values,close_gripper=False):
  log.append(zero_wheels())
  return original(initial_base_pose,initial_joint_values,close_gripper)
 robot.reset=reset
 return original

def load_fixture(path):
 data=json.loads(Path(path).read_text());a=data['actions']
 if data.get('initial_seed')!=0 or len(a)!=76:raise ValueError('original seed0/76 fixture required')
 if any(len(v)!=3 or any(not math.isfinite(x) or abs(x)>1 for x in v) for v in a):raise ValueError('malformed action fixture')
 return a

def limit_reason(wall,sim,size):
 if wall>=WHOLE_WALL_CAP:return 'whole_wall_cap'
 if sim>=RAW_SIM_CAP:return 'raw_sim_cap'
 if size>=DISK_CAP:return 'disk_cap'
 return None

def may_start_episode(done_episodes,wall,remaining_wall_needed=EPISODE_WALL_ESTIMATE):
 return done_episodes<MAX_EPISODES and (BODY_WALL_CAP-wall)>=remaining_wall_needed

def execute_actions(env,actions,clock,wall,deadline,emit,episode):
 rows=[];done=False;error=None;info={}
 for action in actions:
  if wall()>=deadline:error='body_wall_cap';break
  row={'episode':episode,'step':len(rows),'stamp_before':clock(),'attempted':True,'action':list(action)};rows.append(row)
  try:
   _,reward,done,info=env.step(action);row.update(stamp=clock(),reward=reward,done=done,info=info)
  except BaseException as e:
   error=repr(e);row.update(stamp=clock(),error=error)
  emit(row)
  if error or done:break
 return {'steps':rows,'done':done,'info':info,'error':error,'unattempted_steps':len(actions)-len(rows),'requested_commands':len(actions),'training_updates':0}

def process_identity(pid):
 try:
  s=Path('/proc/'+str(pid)+'/stat').read_text();fields=s[s.rfind(')')+2:].split()
  return {'pid':pid,'starttime':fields[19],'cmd':Path('/proc/'+str(pid)+'/cmdline').read_bytes().replace(b'\0',b' ').decode()}
 except OSError:return None

class CaptureAbort(BaseException):pass

def main():
 import ray  # first extension import: inherited pybind requirement
 import rospy,rosgraph
 from rosgraph_msgs.msg import Clock
 from task4_env import Task4Env
 from task4_identity import verify_runtime,semantic_identity
 root=Path(__file__).resolve().parents[1];out=Path(os.environ['FOREM_RES_DIR']);log=Path(os.environ['FOREM_LOG_DIR'])
 t0=time.monotonic();stop=threading.Event();rawtime={'first':None,'last':None};guard={};env=None;bag=None;physical=None
 summary={'run_id':os.environ['FOREM_RUN_ID'],'history':'one Gazebo/VIO lifecycle; consecutive seed0 episodes, each explicit env.reset(seed=0) then original 76-command fixture until original done; no 20 seals/seed101 predecessor','fixture_total':76,'max_episodes':MAX_EPISODES,'episodes':[],'training_updates':0,'error':None,'events':[]}
 def plain(x):return x.item() if hasattr(x,'item') else str(x)
 def write(name,value): (out/name).write_text(json.dumps(value,indent=2,default=plain))
 def event(name):
  row={'event':name,'wall_s':time.monotonic()-t0,'sim_stamp':rospy.get_time()};summary['events'].append(row);write('summary_live.json',summary)
 def abort(sig,_):raise CaptureAbort('signal:'+str(sig)+':'+str(guard.get('reason')))
 def onclock(msg):
  value=msg.clock.to_sec()
  if rawtime['first'] is None:rawtime['first']=value
  rawtime['last']=value
 def watch():
  while not stop.wait(.5):
   size=sum(p.stat().st_size for d in (out,log) for p in d.rglob('*') if p.is_file())
   sim=0 if rawtime['first'] is None else rawtime['last']-rawtime['first'];reason=limit_reason(time.monotonic()-t0,sim,size)
   guard.update(wall_s=time.monotonic()-t0,raw_sim_span_s=sim,bytes=size,reason=reason)
   if reason:os.kill(os.getpid(),signal.SIGTERM);return
 rospy.init_node('task4_history_raw_actor',disable_signals=True);signal.signal(signal.SIGTERM,abort);signal.signal(signal.SIGINT,abort)
 rospy.Subscriber('/clock',Clock,onclock,queue_size=100)
 threading.Thread(target=watch,daemon=True).start()
 try:
  actions=load_fixture(root/'config/task4/quality_action_replay.json');write('container_identity_start.json',verify_runtime())
  write('diagnostic_source_start.json',{'scripts/task4_history_raw.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
  (out/'task4_history_raw.py').write_bytes(Path(__file__).read_bytes());write('actor_identity.json',process_identity(os.getpid()))
  summary['fixture_sha256']=hashlib.sha256((root/'config/task4/quality_action_replay.json').read_bytes()).hexdigest()
  (out/'robot_description.urdf').write_text(rospy.get_param('/robot_description'))
  bag=subprocess.Popen(['rosbag','record','-q','--buffsize=512','-O',str(out/'raw.bag'),*RECORD_TOPICS,'__name:=task4_history_raw_record'])
  physical=subprocess.Popen(['python3','-u','scripts/record_task4_quality.py'])
  waitstart=time.monotonic()
  while not (out/'raw.bag.active').exists():
   if bag.poll() is not None or time.monotonic()-waitstart>10:raise RuntimeError('raw recorder unavailable before initialization')
   time.sleep(.02)
  write('recorder_identities.json',{'bag':process_identity(bag.pid),'physical':process_identity(physical.pid),'topics_requested':RECORD_TOPICS})
  event('raw_recorders_started_before_constructor');env=Task4Env(seed=0);event('constructor_complete_before_explicit_reset')
  if '--zero-wheels-at-reset' in sys.argv[1:]:
   from gazebo_msgs.srv import SetModelConfiguration
   service=rospy.ServiceProxy('/gazebo/set_model_configuration',SetModelConfiguration);rospy.wait_for_service('/gazebo/set_model_configuration',timeout=10)
   def zero_wheels():
    r=service(model_name='husky_ur5',urdf_param_name='robot_description',joint_names=list(WHEEL_JOINTS),joint_positions=[0.]*4)
    return {'sim':rospy.get_time(),'success':bool(r.success),'message':r.status_message}
   summary['intervention']={'zero_wheels_at_reset':True,'joints':WHEEL_JOINTS,'calls':[]}
   wrap_reset_zero_wheels(env.unwrapped_env._robot,zero_wheels,summary['intervention']['calls'])
  else:summary['intervention']=None
  def emit(row):
   with (out/'task_steps.jsonl').open('a') as file:file.write(json.dumps(row,default=plain)+'\n');file.flush()
  for k in range(MAX_EPISODES):
   if not may_start_episode(k,time.monotonic()-t0):event('no_new_episode_wall_budget');break
   ep={'episode':k,'reset_start_sim':rospy.get_time(),'reset_start_wall':time.monotonic()-t0};summary['episodes'].append(ep);write('summary_live.json',summary)
   try:
    env.reset(seed=0)
   except BaseException as e:
    ep.update(reset_error=repr(e),ready_sim=None);summary['error']='reset_failed_episode_'+str(k)+':'+repr(e);break
   ep.update(ready_sim=rospy.get_time(),ready_wall=time.monotonic()-t0,commanded_pose=rospy.get_param('/task4/localization/commanded_pose',None))
   if k==0:write('episode_spec.json',env.episode_spec)
   result=execute_actions(env,actions,rospy.get_time,time.monotonic,t0+BODY_WALL_CAP,emit,k)
   ep.update(steps=len(result['steps']),done=result['done'],error=result['error'],unattempted_steps=result['unattempted_steps'],end_sim=rospy.get_time(),end_wall=time.monotonic()-t0,final_info=result['info'])
   write('summary_live.json',summary)
   if result['error']:summary['error']='episode_'+str(k)+':'+str(result['error']);break
  event('episodes_finished')
 except BaseException as e:summary['error']=summary['error'] or repr(e)
 finally:
  stop.set();signal.signal(signal.SIGTERM,signal.SIG_IGN);signal.signal(signal.SIGINT,signal.SIG_IGN)
  if env:
   try:env.close()
   except BaseException as e:summary['close_error']=repr(e)
  for name,proc in [('physical',physical),('bag',bag)]:
   if proc:
    if proc.poll() is None:
     proc.send_signal(signal.SIGINT)
     try:proc.wait(timeout=20)
     except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=5)
    summary[name+'_exit']=proc.returncode
  summary.update(wall_s=time.monotonic()-t0,guard=guard,raw_sim_first_last=[rawtime['first'],rawtime['last']])
  write('summary.json',summary)
  try:write('container_identity_end.json',semantic_identity());write('graph_end.json',rosgraph.Master(rospy.get_name()).getSystemState())
  except BaseException as e:summary['identity_error']=repr(e);write('summary.json',summary)
 print(json.dumps(summary,default=plain));return 0 if summary.get('error') is None and summary.get('bag_exit')==0 and summary.get('physical_exit')==0 else 1
if __name__=='__main__':raise SystemExit(main())
