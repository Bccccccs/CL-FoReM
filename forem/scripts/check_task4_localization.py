#!/usr/bin/env python3
"""Bounded actual OpenVINS raw-only offline/online checker; no training."""
import argparse,json,os,time,subprocess,signal,hashlib
from pathlib import Path
import numpy as np

def json_native(value):
 if isinstance(value,np.generic):return value.item()
 if isinstance(value,np.ndarray):return value.tolist()
 raise TypeError('unsupported record type:'+type(value).__name__)

def dump(value,**kwargs):return json.dumps(value,default=json_native,allow_nan=False,**kwargs)

def summarize_online(steps,poses,error,done,elapsed,fault_result=None):
 faults=fault_result is not None
 passed=bool(fault_result.get('ok',False)) if faults else bool(done)
 return {'ok':error is None and passed,'task_attempted':not faults,'done':bool(done),'lifecycle_tests_passed':passed if faults else None,'step_count':len(steps),'pose_count':len(poses),'error':error,'elapsed_wall_s':elapsed,'training':False,'success':steps[-1]['info'].get('success') if done and steps and not faults else None}

def stop(p):
 if p and p.poll() is None:
  p.send_signal(signal.SIGINT)
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)

def offline(out,log):
 import rosbag
 src=Path('results/task4/t4.2-raw-r4/inputs.bag');dst=out/'continuous_task.bag';counts={}
 with rosbag.Bag(str(src)) as b,rosbag.Bag(str(dst),'w',compression='bz2') as w:
  for t,m,s in b.read_messages():
   stamp=m.clock.to_sec() if t=='/clock' else m.header.stamp.to_sec()
   if 25.605<=stamp<=29.8835:w.write(t,m,s);counts[t]=counts.get(t,0)+1
 (out/'segment.json').write_text(dump({'input':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'public_phase_range':[25.605,29.8835],'counts':counts,'truth_access':False},indent=2))
 master=subprocess.Popen(['roscore']);vio=None;play=None
 poses=[]
 try:
  time.sleep(3)
  import rospy
  from geometry_msgs.msg import PoseWithCovarianceStamped
  rospy.init_node('task4_offline_checker',disable_signals=True);rospy.set_param('/use_sim_time',True)
  def cb(m):
   p=m.pose.pose.position;q=m.pose.pose.orientation;poses.append({'stamp':m.header.stamp.to_sec(),'frame':m.header.frame_id,'p':[p.x,p.y,p.z],'q':[q.x,q.y,q.z,q.w],'cov':list(m.pose.covariance)})
  sub=rospy.Subscriber('/ov_msckf/poseimu',PoseWithCovarianceStamped,cb,queue_size=10000)
  debugging=os.environ.get('FOREM_VIO_DEBUG')=='1'
  if debugging:
   vio=subprocess.Popen(['gdb','--batch','-ex','handle SIGINT nostop noprint pass','-ex','run','-ex','thread apply all bt','--args','/root/mm_husky_ws/devel/.private/ov_msckf/lib/ov_msckf/run_subscribe_msckf','__name:=ov_msckf','_config_path:=/root/mm_husky_ws/config/task4/estimator.yaml','_publish_global_to_imu_tf:=false','_publish_calibration_tf:=false'])
  else:vio=subprocess.Popen(['rosrun','ov_msckf','run_subscribe_msckf','__name:=ov_msckf','_config_path:=/root/mm_husky_ws/config/task4/estimator.yaml','_publish_global_to_imu_tf:=false','_publish_calibration_tf:=false'])
  time.sleep(3)
  play=subprocess.Popen(['rosbag','play','-r','0.25','-d','2',str(dst)]);play.wait(timeout=120);time.sleep(3)
  import rosgraph
  raw_graph=rosgraph.Master(rospy.get_name()).getSystemState();(out/'graph_system.json').write_text(dump(raw_graph))
  ok=bool(poses) and all(np.isfinite(row['p']+row['q']+row['cov']).all() for row in poses)
  (out/'poses.json').write_text(dump(poses));(out/'summary.json').write_text(dump({'ok':ok,'pose_count':len(poses),'initialize_output':bool(poses),'first_stamp':poses[0]['stamp'] if poses else None,'last_stamp':poses[-1]['stamp'] if poses else None,'bag_play_exit':play.returncode,'evaluation_truth_read':False},indent=2));return 0 if ok else 1
 finally:
  stop(play)
  if os.environ.get('FOREM_VIO_DEBUG')=='1' and vio and vio.poll() is None:
   for rawpid in Path('/proc/%d/task/%d/children'%(vio.pid,vio.pid)).read_text().split():
    pid=int(rawpid)
    try:
     cmd=Path('/proc/%d/cmdline'%pid).read_bytes()
     if b'run_subscribe_msckf' in cmd:os.kill(pid,signal.SIGINT)
    except (OSError,ValueError):pass
   try:vio.wait(timeout=15)
   except subprocess.TimeoutExpired:pass
  stop(vio);stop(master)
  (out/'owned_subprocess_exits.json').write_text(dump({'rosbag':play.returncode if play else None,'official_vio_node_or_gdb':vio.returncode if vio else None,'roscore':master.returncode},indent=2))
  if (out/'summary.json').exists():
   summary=json.loads((out/'summary.json').read_text());summary['VIO_process_exit']=vio.returncode if vio else None
   if os.environ.get('FOREM_VIO_DEBUG')!='1' and vio and vio.returncode!=0:summary['ok']=False
   (out/'summary.json').write_text(dump(summary,indent=2))
  if os.environ.get('FOREM_VIO_DEBUG')!='1' and vio and vio.returncode!=0:return 1

def online(out,log,faults=False):
 from task4_env import Task4Env
 import rospy
 from nav_msgs.msg import Odometry
 from std_msgs.msg import String
 poses=[];statuses=[];tf_edges=[];vel_commands=[];arm_holds=[];joint_feedback={};fault_result={} if faults else None
 def pose(m):
  p=m.pose.pose.position;q=m.pose.pose.orientation;poses.append({'stamp':m.header.stamp.to_sec(),'p':[p.x,p.y,p.z],'q':[q.x,q.y,q.z,q.w]})
 rospy.init_node('task4_online_checker',disable_signals=True)
 from tf2_msgs.msg import TFMessage
 def tf_cb(m):
  for t in m.transforms:
   if t.child_frame_id.lstrip('/')=='base_footprint':tf_edges.append({'stamp':t.header.stamp.to_sec(),'parent':t.header.frame_id,'child':t.child_frame_id,'caller':getattr(m,'_connection_header',{}).get('callerid'),'p':[t.transform.translation.x,t.transform.translation.y,t.transform.translation.z]})
 rospy.Subscriber('/tf',TFMessage,tf_cb,queue_size=10000)
 from geometry_msgs.msg import Twist
 from trajectory_msgs.msg import JointTrajectory
 from sensor_msgs.msg import JointState
 def joints_cb(m):joint_feedback.update(zip(m.name,m.position))
 def vel_cb(m):
  if getattr(m,'_connection_header',{}).get('callerid')=='/pose_bridge':vel_commands.append({'sim_receipt':rospy.get_time(),'values':[m.linear.x,m.linear.y,m.linear.z,m.angular.x,m.angular.y,m.angular.z]})
 def hold_cb(m):
  if getattr(m,'_connection_header',{}).get('callerid')=='/pose_bridge' and m.points:
   p=m.points[0];arm_holds.append({'stamp':m.header.stamp.to_sec(),'joint_names':list(m.joint_names),'positions':list(p.positions),'velocities':list(p.velocities),'duration':p.time_from_start.to_sec(),'feedback_max_error':max([abs(pos-joint_feedback.get(n,pos)) for n,pos in zip(m.joint_names,p.positions)])})
 rospy.Subscriber('/joint_states',JointState,joints_cb,queue_size=1);rospy.Subscriber('/cmd_vel',Twist,vel_cb,queue_size=10000);rospy.Subscriber('/eff_joint_traj_controller/command',JointTrajectory,hold_cb,queue_size=1000)

 rospy.Subscriber('/forem/pose/estimated',Odometry,pose,queue_size=10000);rospy.Subscriber('/task4/localization/status',String,lambda m:statuses.append(json.loads(m.data)),queue_size=10000)
 env=None;steps=[];error=None;done=False;started=time.monotonic()
 truth_recorder=subprocess.Popen(['rosbag','record','-q','-O',str(out/'evaluation.bag'),'/ground_truth/state'])
 import rosgraph
 (out/'graph_start.json').write_text(dump(rosgraph.Master(rospy.get_name()).getSystemState()))
 try:
  env=Task4Env(seed=0);obs=env.reset(seed=0)
  (out/'episode_spec.json').write_text(dump(env.episode_spec,indent=2))
  (out/'graph_initialized.json').write_text(dump(rosgraph.Master(rospy.get_name()).getSystemState()))
  if faults:
   import xmlrpc.client
   from std_srvs.srv import Empty,Trigger
   uri=rosgraph.Master(rospy.get_name()).lookupNode('/ov_msckf');code,_,pid=xmlrpc.client.ServerProxy(uri).getPid(rospy.get_name())
   if code!=1 or b'run_subscribe_msckf' not in Path('/proc/%d/cmdline'%pid).read_bytes():raise RuntimeError('own VIO identity mismatch')
   from task0_proc import identity,alive
   wanted=identity(pid)
   if not wanted or not alive(wanted) or 'run_subscribe_msckf' not in wanted['cmd']:raise RuntimeError('actual VIO kernel identity mismatch')
   fault={'node_kernel_identity':wanted,'stopped_node_pid':pid,'before_steps':env._steps,'initial_epoch':env._call('ready')['epoch']}
   os.kill(pid,signal.SIGSTOP)
   try:
    until=time.monotonic()+20;start=rospy.get_time()
    while rospy.get_time()-start<.3 and time.monotonic()<until:time.sleep(.01)
    state=rospy.ServiceProxy('/task4/localization/ready',Trigger)();fault['loss_status']=json.loads(state.message)
    try:env.step([0,0,0]);fault['loss_action_rejected']=False
    except RuntimeError:fault['loss_action_rejected']=True
    fault['after_loss_steps']=env._steps
   finally:
    if not alive(wanted):raise RuntimeError('own VIO identity changed before SIGCONT')
    fault['resume_identity_verified']=True;os.kill(pid,signal.SIGCONT)
   env.reset(seed=0);fault['new_ready']=env._call('ready');fault['fresh_reset_epoch']=fault['new_ready']['epoch']
   # Unsupported simulation reset: final destructive-to-own-run fault, never continue training.
   rospy.ServiceProxy('/gazebo/reset_simulation',Empty)();time.sleep(1)
   r=rospy.ServiceProxy('/task4/localization/ready',Trigger)();fault['rollback_status']=json.loads(r.message)
   try:env.step([0,0,0]);fault['rollback_action_rejected']=False
   except RuntimeError:fault['rollback_action_rejected']=True
   fault['ok']=fault['loss_action_rejected'] and fault['after_loss_steps']==fault['before_steps'] and fault['rollback_action_rejected'] and fault['rollback_status']['state']=='INVALID_STOP' and fault['fresh_reset_epoch']>fault['initial_epoch']
   fault['loss_zero_cmds']=[v for v in vel_commands if start<=v['sim_receipt']<=fault['loss_status']['clock'] and not any(v['values'])]
   fault['loss_arm_holds']=[v for v in arm_holds if start<=v['stamp']<=fault['loss_status']['clock']]
   fault['ok']=fault['ok'] and bool(fault['loss_zero_cmds']) and bool(fault['loss_arm_holds'])
   fault_result=fault;(out/'faults.json').write_text(dump(fault,indent=2))

  while not done and not faults and len(steps)<1000 and time.monotonic()-started<850:
   if len(steps)==5:
    stop(truth_recorder);(out/'graph_truth_recorder_off.json').write_text(dump(rosgraph.Master(rospy.get_name()).getSystemState()))
   obs,reward,done,info=env.step([0.,0.,0.]);steps.append({'step':len(steps),'stamp':rospy.get_time(),'reward':reward,'done':done,'info':info})
   with (out/'task_steps.jsonl').open('a') as stream:stream.write(dump(steps[-1])+'\n');stream.flush()
 except Exception as e:error=repr(e)
 finally:
  stop(truth_recorder)
  if env:
   try:env.close()
   except Exception:pass
  (out/'hold_commands.json').write_text(dump({'cmd_vel':vel_commands,'arm_holds':arm_holds}));(out/'tf_edges.json').write_text(dump(tf_edges));(out/'poses.json').write_text(dump(poses));(out/'statuses.json').write_text(dump(statuses));(out/'task_steps.json').write_text(dump(steps))
  (out/'summary.json').write_text(dump(summarize_online(steps,poses,error,done,time.monotonic()-started,fault_result),indent=2))
 return 0 if error is None and (bool(fault_result.get('ok')) if faults else done) else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['offline','online','faults'],required=True);a=ap.parse_args();out=Path(os.environ['FOREM_RES_DIR']);log=Path(os.environ['FOREM_LOG_DIR']);from task4_identity import semantic_identity,verify_runtime
 verify_runtime()
 (out/'container_identity_start.json').write_text(dump(semantic_identity(),indent=2))
 rc=offline(out,log) if a.mode=='offline' else online(out,log,faults=a.mode=='faults')
 (out/'container_identity_end.json').write_text(dump(semantic_identity(),indent=2))
 raise SystemExit(rc)
