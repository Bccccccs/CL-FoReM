#!/usr/bin/env python3
"""Bounded original Task4 reset diagnostic; no policy, training or truth reader."""
import ray
import torch
import argparse,json,os,signal,subprocess,time,threading,hashlib
from pathlib import Path
import numpy as np
import cv2
import rospy
from sensor_msgs.msg import Image,Imu
from std_msgs.msg import String
from cv_bridge import CvBridge
from task4_env import Task4Env
from task4_identity import verify_runtime,semantic_identity

def plain(v):
 if isinstance(v,dict):return {str(k):plain(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [plain(x) for x in v]
 if isinstance(v,np.ndarray):return v.tolist()
 if hasattr(v,'item'):return v.item()
 return v

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--seeds',default='101');parser.add_argument('--steps-per-reset',type=int,default=0);args=parser.parse_args();seeds=[int(s) for s in args.seeds.split(',')]
 if len(seeds)>5 or len(set(seeds))!=len(seeds) or any(s not in (0,101,102,103,104,105) for s in seeds):raise ValueError('diagnostic only original101–105/normal0, max5 distinct resets')
 if args.steps_per_reset not in (0,1):raise ValueError('max one original zero-action step per reset')
 rospy.init_node('task4_init_diagnostic',disable_signals=True)
 out=Path(os.environ['FOREM_RES_DIR']);started=time.monotonic();env=None;bag=None;phase='constructor';attempts=[];draws=[];spawns=[];lock=threading.RLock();counts={};last={};bridge=CvBridge()
 verify_runtime();(out/'container_identity_start.json').write_text(json.dumps(semantic_identity(),indent=2))
 # Official YamlParser private-param override; diagnostic verbosity only.
 rospy.set_param('/ov_msckf/verbosity','ALL')
 (out/'diagnostic_parameters.json').write_text(json.dumps({'/ov_msckf/verbosity':'ALL','seeds':seeds,'init_timeout_wall_s':120,'max_run_wall_s':600,'max_body_wall_s':500,'reset_start_margin_wall_s':145,'steps_per_reset':args.steps_per_reset},indent=2))
 def append(kind,row):
  with lock:
   counts[kind]=counts.get(kind,0)+1
   with (out/(kind+'.jsonl')).open('a') as f:f.write(json.dumps(plain(row))+'\n');f.flush()
 def camera(msg,side):
  stamp=msg.header.stamp.to_sec();key=(phase,side)
  if stamp-last.get(key,-100)<1:return
  last[key]=stamp;im=bridge.imgmsg_to_cv2(msg,desired_encoding='passthrough');name=f'{phase}-{side}-{msg.header.stamp.to_nsec()}.png';cv2.imwrite(str(out/name),cv2.cvtColor(im,cv2.COLOR_RGB2BGR) if msg.encoding=='rgb8' else im)
  gray=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY) if msg.encoding=='rgb8' else cv2.cvtColor(im,cv2.COLOR_BGR2GRAY) if msg.encoding=='bgr8' else im
  corners=cv2.FastFeatureDetector_create(threshold=20,nonmaxSuppression=True).detect(gray,None)
  append('images',{'phase':phase,'side':side,'stamp':stamp,'stamp_ns':msg.header.stamp.to_nsec(),'seq':msg.header.seq,'frame':msg.header.frame_id,'encoding':msg.encoding,'shape':im.shape,'raw_sha256':hashlib.sha256(bytes(msg.data)).hexdigest(),'png':name,'min':int(im.min()),'max':int(im.max()),'std':float(im.std()),'unique_gray':len(np.unique(gray)),'opencv_fast20_corners':len(corners),'note':'independent full-image FAST, not actual tracker DB'})
 def imu(msg):append('imu',{'phase':phase,'stamp':msg.header.stamp.to_sec(),'stamp_ns':msg.header.stamp.to_nsec(),'frame':msg.header.frame_id,'acc':[msg.linear_acceleration.x,msg.linear_acceleration.y,msg.linear_acceleration.z],'gyr':[msg.angular_velocity.x,msg.angular_velocity.y,msg.angular_velocity.z]})
 def status(msg):
  row=json.loads(msg.data);row.update(phase=phase,wall_elapsed_s=time.monotonic()-started,commanded_pose=rospy.get_param('/task4/localization/commanded_pose',None));append('statuses',row)
 subs=[rospy.Subscriber('/task4/stereo/'+s+'/image_raw',Image,camera,callback_args=s,queue_size=1,buff_size=4000000) for s in ('left','right')]
 subs += [rospy.Subscriber('/task4/imu/data_raw',Imu,imu,queue_size=100),rospy.Subscriber('/task4/localization/status',String,status,queue_size=10)]
 topics=['/clock','/task4/stereo/left/image_raw','/task4/stereo/right/image_raw','/task4/stereo/left/camera_info','/task4/stereo/right/camera_info','/task4/imu/data_raw','/task4/localization/status','/forem/pose/estimated'];error=None
 try:
  bag=subprocess.Popen(['rosbag','record','--lz4','-q','-O',str(out/'raw.bag')]+topics);env=Task4Env(seed=0)
  (out/'robot_description.urdf').write_text(rospy.get_param('/robot_description'))
  simulator=env.unwrapped_env.map.simulator;original_spawn=simulator.spawn_scene_objects;scene_cache=[]
  def spawn(objects):
   nonlocal scene_cache
   # Only observe objects already drawn by map_reset; never call get_scene_objects.
   scene=[]
   for obj in objects:
    w=obj.world_object;p=obj.pose
    scene.append({'name':obj.name,'frame':obj.frame,'geometry':str(getattr(w,'geometry','')),'size':[w.x,w.y,w.z],'pose':[p.position.x,p.position.y,p.position.z,p.orientation.x,p.orientation.y,p.orientation.z,p.orientation.w]})
   scene_cache=plain(scene);spawns.append({'phase':phase,'stamp':rospy.get_time(),'objects':scene_cache});(out/'spawn_commands.json').write_text(json.dumps(spawns,indent=2));return original_spawn(objects)
  simulator.spawn_scene_objects=spawn
  original_template=simulator.get_model_template
  def template(obj):
   value=original_template(obj)
   digest=hashlib.sha256(value.encode()).hexdigest();(out/('spawn-'+digest+'.sdf')).write_text(value);append('spawn_sdf',{'phase':phase,'sha256':digest,'type':obj.database_name});return value
  simulator.get_model_template=template
  original=env.unwrapped_env.map.draw_startpose_and_goal
  def draw(*a,**kw):
   value=original(*a,**kw);base,joints,goal=value
   draws.append(plain({'phase':phase,'stamp':rospy.get_time(),'base_command':base,'arm_command':joints,'goal_tip':goal,'obstacles':scene_cache,'scene_source':'actual simulator.spawn_scene_objects arguments, no additional RNG draw','map_size_m':[env.unwrapped_env.map._map_W_meter,env.unwrapped_env.map._map_H_meter]}));(out/'public_draws.json').write_text(json.dumps(draws,indent=2));return value
  env.unwrapped_env.map.draw_startpose_and_goal=draw
  for seed in seeds:
   if time.monotonic()-started+145>500:break
   phase='seed'+str(seed);row={'seed':seed,'wall_started_s':time.monotonic()-started,'stamp_before':rospy.get_time(),'initialized':False};attempts.append(row)
   try:
    obs=env.reset(seed=seed);row.update(initialized=True,observation_shapes=[list(x.shape) for x in obs],episode_spec=env.episode_spec)
    import rosgraph
    (out/('graph-seed'+str(seed)+'.json')).write_text(json.dumps(rosgraph.Master(rospy.get_name()).getSystemState()))
    if args.steps_per_reset:
     before=rospy.get_time();obs,reward,done,info=env.step([0.,0.,0.]);row['original_zero_action_step']=plain({'stamp_before':before,'stamp_after':rospy.get_time(),'reward':reward,'done':done,'info':info,'observation_shapes':[list(x.shape) for x in obs]})
   except BaseException as e:row['error']=repr(e)
   row.update(wall_elapsed_s=time.monotonic()-started-row['wall_started_s'],stamp_after=rospy.get_time(),commanded_pose=rospy.get_param('/task4/localization/commanded_pose'));(out/'attempts.json').write_text(json.dumps(plain(attempts),indent=2))
   if not row['initialized']:break
 except BaseException as e:error=repr(e)
 finally:
  if env:
   try:env.close()
   except BaseException as e:append('close_errors',{'error':repr(e)})
  if bag:
   bag.send_signal(signal.SIGINT)
   try:bag.wait(timeout=15)
   except subprocess.TimeoutExpired:bag.terminate();bag.wait(timeout=5)
  for sub in subs:sub.unregister()
  (out/'summary.json').write_text(json.dumps(plain({'requested_seeds':seeds,'requested':len(seeds),'attempted':len(attempts),'initialized':sum(a['initialized'] for a in attempts),'unattempted_seeds':seeds[len(attempts):],'attempts':attempts,'controls':sum('original_zero_action_step' in a for a in attempts),'error':error,'wall_s':time.monotonic()-started,'counts':counts,'raw_recorder_exit':bag.returncode if bag else None}),indent=2));(out/'container_identity_end.json').write_text(json.dumps(semantic_identity(),indent=2))
 return 0 if error is None and len(attempts)==len(seeds) and all(a['initialized'] for a in attempts) else 1
if __name__=='__main__':raise SystemExit(main())
