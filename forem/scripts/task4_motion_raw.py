#!/usr/bin/env python3
"""Bounded raw diagnostic actor; truth is recorded by a separate rosbag process.
SRC0124. No VIO/control/physics change and no learning. Original stamps survive.
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

def load_prefix(path):
 data=json.loads(Path(path).read_text());a=data['actions']
 if data.get('initial_seed')!=0 or len(a)!=76:raise ValueError('original seed0/76 fixture required')
 if any(len(v)!=3 or any(not math.isfinite(x) or abs(x)>1 for x in v) for v in a):raise ValueError('malformed action fixture')
 return a[:28]

def header_metadata(msg):
 return {'stamp_ns':msg.header.stamp.to_nsec(),'frame_id':msg.header.frame_id,'seq':msg.header.seq}

def limit_reason(wall,sim,size):
 if wall>=450:return 'body_wall_cap'
 if sim>=120:return 'raw_sim_cap'
 if size>=10*1024**3:return 'disk_cap'
 return None

def execute_prefix(env,actions,clock,wall,deadline,emit):
 rows=[];done=False;error=None;info={}
 for action in actions[:28]:
  if wall()>=deadline:error='body_wall_cap';break
  row={'step':len(rows),'stamp_before':clock(),'attempted':True,'action':list(action)};rows.append(row)
  try:
   _,reward,done,info=env.step(action);row.update(stamp=clock(),reward=reward,done=done,info=info)
  except BaseException as e:
   error=repr(e);row.update(stamp=clock(),error=error)
  emit(row)
  if error or done:break
 return {'steps':rows,'done':done,'info':info,'error':error,'unattempted_steps':28-len(rows),'requested_commands':28,'training_updates':0}

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
 summary={'run_id':os.environ['FOREM_RUN_ID'],'fresh_history':'fresh simulator; one explicit outer seed0 reset; no 20 seals/seed101 predecessor','fixture_prefix':28,'fixture_total':76,'steps':[],'training_updates':0,'error':None,'events':[]}
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
 rospy.init_node('task4_motion_raw_actor',disable_signals=True);signal.signal(signal.SIGTERM,abort);signal.signal(signal.SIGINT,abort)
 rospy.Subscriber('/clock',Clock,onclock,queue_size=100)
 threading.Thread(target=watch,daemon=True).start()
 try:
  actions=load_prefix(root/'config/task4/quality_action_replay.json');write('container_identity_start.json',verify_runtime())
  write('diagnostic_source_start.json',{'scripts/task4_motion_raw.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
  (out/'task4_motion_raw.py').write_bytes(Path(__file__).read_bytes());write('actor_identity.json',process_identity(os.getpid()))
  summary['fixture_sha256']=hashlib.sha256((root/'config/task4/quality_action_replay.json').read_bytes()).hexdigest()
  (out/'robot_description.urdf').write_text(rospy.get_param('/robot_description'))
  bag=subprocess.Popen(['rosbag','record','-q','--buffsize=512','-O',str(out/'raw.bag'),*RECORD_TOPICS,'__name:=task4_motion_raw_record'])
  physical=subprocess.Popen(['python3','-u','scripts/record_task4_quality.py'])
  waitstart=time.monotonic()
  while not (out/'raw.bag.active').exists():
   if bag.poll() is not None or time.monotonic()-waitstart>10:raise RuntimeError('raw recorder unavailable before initialization')
   time.sleep(.02)
  write('recorder_identities.json',{'bag':process_identity(bag.pid),'physical':process_identity(physical.pid),'topics_requested':RECORD_TOPICS})
  event('raw_recorders_started_before_constructor');env=Task4Env(seed=0);event('constructor_complete_before_explicit_reset')
  env.reset(seed=0);event('explicit_reset_returned_ready');write('episode_spec.json',env.episode_spec)
  write('commanded_initial.json',rospy.get_param('/task4/localization/commanded_pose'))
  write('graph_ready.json',rosgraph.Master(rospy.get_name()).getSystemState())
  def emit(row):
   with (out/'task_steps.jsonl').open('a') as file:file.write(json.dumps(row,default=plain)+'\n');file.flush()
  summary.update(execute_prefix(env,actions,rospy.get_time,time.monotonic,t0+450,emit));event('motion_stopped_original_done_or_prefix_cap')
 except BaseException as e:summary['error']=repr(e)
 finally:
  stop.set();signal.signal(signal.SIGTERM,signal.SIG_IGN);signal.signal(signal.SIGINT,signal.SIG_IGN)
  if env:
   try:env.close()
   except BaseException as e:summary['close_error']=repr(e)
  for name,proc in [('physical',physical),('bag',bag)]:
   if proc:
    if proc.poll() is None:
     proc.send_signal(signal.SIGINT)
     try:proc.wait(timeout=12)
     except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=5)
    summary[name+'_exit']=proc.returncode
  summary.update(wall_s=time.monotonic()-t0,guard=guard,raw_sim_first_last=[rawtime['first'],rawtime['last']],actual_attempts=len(summary.get('steps',[])),unattempted_steps=28-len(summary.get('steps',[])))
  write('task_steps.json',summary.get('steps',[]));write('summary.json',summary)
  try:write('container_identity_end.json',semantic_identity());write('graph_end.json',rosgraph.Master(rospy.get_name()).getSystemState())
  except BaseException as e:summary['identity_error']=repr(e);write('summary.json',summary)
 print(json.dumps(summary,default=plain));return 0 if summary.get('error') is None and summary.get('bag_exit')==0 and summary.get('physical_exit')==0 else 1
if __name__=='__main__':raise SystemExit(main())
