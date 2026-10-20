"""Task4 original Task3 environment with reset-only public pose lifecycle.
Policy/replay gets observation only after raw VIO fresh init and once alignment.
Original RobotEnv/CombinedEnv map, draw, arm, task, reward and termination unmodified.
"""
from task3_env import Task3Env,validate_action
import json,time,copy,hashlib
from task3_env import _r,spec_hash
from task4_instances import canonical_base
POSE_SOURCE='openvins_stereo_imu'
# task4.3.5 (SRC0136): wheel joints are restored with the rest of the robot at every reset; never observed by the policy.
WHEEL_JOINTS=('front_left_wheel','front_right_wheel','rear_left_wheel','rear_right_wheel')
# task4.3.5 (SRC0141/SRC0142): measured resting height of the model root base_footprint; the inherited C++ reset teleports at z=.05
REST_Z=0.0
# Teleporting exactly into ground contact scrambled the arm (t4.3.5-rest-history-r1); keep a 3 mm clearance (vs inherited 50 mm drop).
PLACE_CLEARANCE=0.003

class LocalizationAbort(BaseException):
 """Internal: escape original IK/draw-reset retry loop on unavailable localization."""
 pass

class Task4Env(Task3Env):
 def _install_public_capture(self):
  # Observe existing arguments only. Never call map.get_scene_objects(), which draws new RNG objects.
  m=self.unwrapped_env.map;sim=m.simulator;self._scene_cache=[];self._spawn_service_cache=[];self._spawn_sdf_xml={};self._public_draw=None
  original_spawn=sim.spawn_scene_objects
  def spawn(objects):
   objects=list(objects);self._scene_cache=[];self._spawn_service_cache=[];self._spawn_sdf_xml={}
   for o in objects:
    w=o.world_object;p=o.pose
    self._scene_cache.append(dict(name=o.name,geometry=str(getattr(w,'geometry','')),size=_r([w.x,w.y,w.z]),frame=o.frame,pose=_r([p.position.x,p.position.y,p.position.z,p.orientation.x,p.orientation.y,p.orientation.z,p.orientation.w])))
   return original_spawn(objects)
  sim.spawn_scene_objects=spawn
  original_service=sim._spawn_model_srv
  def service(name,xml,namespace,pose,frame):
   digest=hashlib.sha256(xml.encode()).hexdigest();self._spawn_sdf_xml[digest]=xml;p=pose
   self._spawn_service_cache.append(dict(name=name,frame=frame,sdf_sha256=digest,pose=_r([p.position.x,p.position.y,p.position.z,p.orientation.x,p.orientation.y,p.orientation.z,p.orientation.w])))
   return original_service(name,xml,namespace,pose,frame)
  service.close=original_service.close  # preserve original ServiceProxy lifecycle used by Map.map_reset->clear
  sim._spawn_model_srv=service
  original_draw=m.draw_startpose_and_goal
  def draw(*args,**kwargs):
   value=original_draw(*args,**kwargs);base,arm,goal=value
   self._public_draw=dict(base_command=[float(v) for v in base],arm_command={k:round(float(v),6) for k,v in arm.items()} if isinstance(arm,dict) else _r(arm),goal_tip=_r(goal))
   return value
  m.draw_startpose_and_goal=draw
 def _capture_spec(self,seed):
  e=self.unwrapped_env;ro=e._robot.get_robot_obs();planner=e._ee_planner
  if self._public_draw is None:raise RuntimeError('no actual public draw captured')
  # Pure cache snapshot; planned/estimated observation fields are labeled separately from commands.
  spec=dict(schema=4,seed=seed,base_tf=_r(ro.base_tf),initial_base_command=copy.deepcopy(self._public_draw['base_command']),initial_base_pose_xyzw=_r(canonical_base(self._public_draw['base_command'])),arm_command=copy.deepcopy(self._public_draw['arm_command']),arm_joints_planned=_r(ro.joint_values),goal_tip=_r(planner.gripper_goal_tip),goal_wrist=_r(planner.gripper_goal_wrist),map_size_m=_r([e.map._map_W_meter,e.map._map_H_meter]),obstacles=copy.deepcopy(self._scene_cache),spawn_commands=copy.deepcopy(self._spawn_service_cache))
  spec['hash']=spec_hash({k:v for k,v in spec.items() if k!='hash'});return spec

 def _call(self,name):
  import rospy
  from std_srvs.srv import Trigger
  rospy.wait_for_service('/task4/localization/'+name,timeout=10)
  response=rospy.ServiceProxy('/task4/localization/'+name,Trigger)()
  if not response.success:raise RuntimeError('localization '+name+': '+response.message)
  return json.loads(response.message)
 def _begin(self,pose):
  import rospy
  if not self._resetting:raise RuntimeError('bootstrap prohibited outside constructor/reset')
  p=list(pose)
  # Original base reset targets ground plane, Gazebo RobotEnv adds public z .05.
  if len(p)==6:
   from scipy.spatial.transform import Rotation
   p=p[:3]+Rotation.from_euler('xyz',p[3:]).as_quat().tolist()
  p[2]=.05
  rospy.set_param('/task4/localization/commanded_pose',p);return self._call('begin')
 def _zero_wheels(self,service=None):
  if service is None:
   import rospy
   from gazebo_msgs.srv import SetModelConfiguration
   rospy.wait_for_service('/gazebo/set_model_configuration',timeout=10)
   service=rospy.ServiceProxy('/gazebo/set_model_configuration',SetModelConfiguration)
  r=service(model_name='husky_ur5',urdf_param_name='robot_description',joint_names=list(WHEEL_JOINTS),joint_positions=[0.]*len(WHEEL_JOINTS))
  if not r.success:raise RuntimeError('wheel joint reset failed: '+str(r.status_message))
 def _replace_base(self,pose,service=None,pause=None,unpause=None):
  # Re-place the landed base at the PUBLIC commanded pose (the same anchor the estimator uses) at rest height, zero twist.
  from gazebo_msgs.msg import ModelState
  if service is None:
   import rospy
   from gazebo_msgs.srv import SetModelState
   from std_srvs.srv import Empty
   for name in ('/gazebo/set_model_state','/gazebo/pause_physics','/gazebo/unpause_physics'):rospy.wait_for_service(name,timeout=10)
   service=rospy.ServiceProxy('/gazebo/set_model_state',SetModelState);pause=rospy.ServiceProxy('/gazebo/pause_physics',Empty);unpause=rospy.ServiceProxy('/gazebo/unpause_physics',Empty)
  p=list(pose);s=ModelState();s.model_name='husky_ur5';s.reference_frame='world'
  s.pose.position.x,s.pose.position.y,s.pose.position.z=p[0],p[1],REST_Z+PLACE_CLEARANCE
  s.pose.orientation.x,s.pose.orientation.y,s.pose.orientation.z,s.pose.orientation.w=p[3:7]
  pause()
  try:r=service(s)
  finally:unpause()
  if not r.success:raise RuntimeError('rest-height base re-placement failed: '+str(r.status_message))
 def _await_ready(self):
  import rospy
  from std_srvs.srv import Trigger
  t=time.monotonic()
  limit=getattr(self,'init_timeout_wall_s',120)  # training-only override in formal r2 (SRC0153); evaluation/quality keep 120
  while time.monotonic()-t<limit:
   r=rospy.ServiceProxy('/task4/localization/ready',Trigger)();s=json.loads(r.message)
   if r.success:return s
   if s['state']=='INVALID_STOP':raise LocalizationAbort('localization invalid: '+str(s['reason']))
   time.sleep(.02)
  self._call('stop');raise LocalizationAbort('raw VIO initialization timeout')
 def __init__(self,seed=0,task_contract=None,overrides=None):
  self._resetting=True
  import rospy
  self._begin([0,0,.05,0,0,0,1])
  try:super().__init__(seed,task_contract,overrides)
  except Exception:self._call('stop');raise
  self.pose_source=POSE_SOURCE;self.contract['pose_source']=POSE_SOURCE;robot=self.unwrapped_env._robot;oldset=robot.set_base_tf;oldreset=robot.reset
  def set_base_tf(pose):
   self._begin(pose);return oldset(pose)
  def reset_robot(initial_base_pose,initial_joint_values,close_gripper=False):
   self._zero_wheels()
   self._begin(initial_base_pose)
   oldreset(initial_base_pose,initial_joint_values,close_gripper)
   import rospy
   self._replace_base(rospy.get_param('/task4/localization/commanded_pose'))
   # C++ reset completed final commanded start and arm; stop bootstrap, fresh estimator/queues.
   self._call('initialize');self._await_ready()
   base=robot._robot_cpp.get_basetf_world()
   from scipy.spatial.transform import Rotation
   yaw=Rotation.from_quat(base[3:]).as_euler('xyz')[2]
   robot._robot_cpp.set_joint_values({'world_joint/x':base[0],'world_joint/y':base[1],'world_joint/theta':yaw},False)
   robot.prev_robot_obs=robot._robot_cpp.get_robot_obs(False,False)
   return robot.prev_robot_obs
  robot.set_base_tf=set_base_tf;robot.reset=reset_robot;self._install_public_capture();self._resetting=False;self._episode=None
 def reset(self,seed=None,episode_spec=None):
  self._resetting=True;self._episode=None
  try:
   obs=super().reset(seed,None)
   if episode_spec is not None:
    from task4_instances import verify_public_instance
    verify_public_instance(self._episode,episode_spec)
   return obs
  except BaseException as error:
   try:self._call('stop')
   finally:self._episode=None
   if isinstance(error,LocalizationAbort):raise RuntimeError(str(error)) from error
   raise
  finally:self._resetting=False
 def step(self,action):
  if self._resetting:raise RuntimeError('policy prohibited during public bootstrap')
  self._call('ready')
  try:
   value=super().step(validate_action(action));self._call('ready');return value
  except Exception:
   self._episode=None;self._call('stop');raise
 def close(self):
  try:self._call('stop')
  finally:super().close()
