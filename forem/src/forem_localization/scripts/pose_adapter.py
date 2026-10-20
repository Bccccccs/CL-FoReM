#!/usr/bin/env python3
"""Single Task4 TF authority, public reset bootstrap and raw-only VIO lifecycle.
No simulator pose subscriber/service, no IMU orientation. SRC0075/0076.
"""
import json,threading,time,subprocess,os,signal,sys
sys.path.insert(0,os.path.dirname(os.path.realpath(__file__)))
import numpy as np
import rospy,tf2_ros
from geometry_msgs.msg import PoseWithCovarianceStamped,TransformStamped,Twist
from nav_msgs.msg import Odometry
from rosgraph_msgs.msg import Clock
from std_msgs.msg import String
from std_srvs.srv import Trigger,TriggerResponse
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory,JointTrajectoryPoint
from actionlib_msgs.msg import GoalID
from estimate_gate import EstimateGate
from scipy.spatial.transform import Rotation

class Adapter:
 def __init__(self):
  self.g=EstimateGate();self.lock=threading.RLock();self.proc=None;self.raw_counts={'left':0,'right':0,'imu':0};self.joints=None;self.logs=[]
  self.br=tf2_ros.TransformBroadcaster();self.pub=rospy.Publisher('/forem/pose/estimated',Odometry,queue_size=10)
  self.status=rospy.Publisher('/task4/localization/status',String,queue_size=1,latch=True)
  self.vel=rospy.Publisher('/cmd_vel',Twist,queue_size=1);self.arm=rospy.Publisher('/eff_joint_traj_controller/command',JointTrajectory,queue_size=1);self.cancel=rospy.Publisher('/eff_joint_traj_controller/follow_joint_trajectory/cancel',GoalID,queue_size=1)
  rospy.Subscriber('/clock',Clock,self.clock,queue_size=100);rospy.Subscriber('/joint_states',JointState,self.joint,queue_size=1)
  self.sub=None
  rospy.Service('/task4/localization/begin',Trigger,self.begin);rospy.Service('/task4/localization/initialize',Trigger,self.initialize);rospy.Service('/task4/localization/ready',Trigger,self.ready);rospy.Service('/task4/localization/stop',Trigger,self.stop)
  rospy.on_shutdown(self.shutdown)
 def joint(self,m):self.joints=m
 def hold(self):
  self.vel.publish(Twist());self.cancel.publish(GoalID())
  if self.joints:
   names=['ur5_shoulder_pan_joint','ur5_shoulder_lift_joint','ur5_elbow_joint','ur5_wrist_1_joint','ur5_wrist_2_joint','ur5_wrist_3_joint']
   try:
    q=[self.joints.position[self.joints.name.index(n)] for n in names]
    m=JointTrajectory();m.header.stamp=rospy.Time.now();m.joint_names=names;p=JointTrajectoryPoint();p.positions=q;p.velocities=[0.]*6;p.time_from_start=rospy.Duration(.1);m.points=[p];self.arm.publish(m)
   except (ValueError,IndexError):pass
 def stop_vio(self):
  if self.sub:self.sub.unregister();self.sub=None
  if self.proc:
   self.proc.send_signal(signal.SIGINT)
   try:self.proc.wait(timeout=8)
   except subprocess.TimeoutExpired:self.proc.terminate();self.proc.wait(timeout=5)
   self.logs.append({'event':'vio_stopped','exit':self.proc.returncode,'epoch':self.g.epoch});self.proc=None
 def message(self):
  return json.dumps({'pose_source':'openvins_stereo_imu','current_TF_source':('public_commanded_bootstrap' if self.g.state=='BOOTSTRAP_PUBLIC_POSE' else 'openvins_stereo_imu' if self.g.ready() else 'none'),'state':self.g.state,'ready':self.g.ready(),'epoch':self.g.epoch,'clock':self.g.now,'last_stamp':self.g.last,'accepted':self.g.accepted,'reason':self.g.reason,'bootstrap_authority':'pose_bridge','vio_pid':self.proc.pid if self.proc else None,'lifecycle_exits':self.logs,'alignment_once':self.g.align.tolist() if self.g.align is not None else None})
 def publish_status(self):self.status.publish(self.message())
 def begin(self,_):
  with self.lock:
   self.hold();self.stop_vio()
   try:self.g.begin(rospy.get_param('/task4/localization/commanded_pose'));self.publish_status();return TriggerResponse(True,self.message())
   except Exception as e:return TriggerResponse(False,str(e))
 def initialize(self,_):
  with self.lock:
   try:
    self.hold();self.stop_vio();self.g.initialize(rospy.get_time())
    self.sub=rospy.Subscriber('/ov_msckf/poseimu',PoseWithCovarianceStamped,lambda m,epoch=self.g.epoch: self.pose(m,epoch),queue_size=10)
    self.proc=subprocess.Popen(['rosrun','ov_msckf','run_subscribe_msckf','__name:=ov_msckf','_config_path:=/root/mm_husky_ws/config/task4/estimator.yaml','_publish_global_to_imu_tf:=false','_publish_calibration_tf:=false'])
    self.publish_status();return TriggerResponse(True,self.message())
   except Exception as e:self.g.invalidate(str(e));return TriggerResponse(False,str(e))
 def ready(self,_):
  with self.lock:return TriggerResponse(self.g.ready(),self.message())
 def stop(self,_):
  with self.lock:self.g.invalidate('explicit_stop');self.hold();self.stop_vio();self.publish_status();return TriggerResponse(True,self.message())
 def clock(self,m):
  with self.lock:
   old=self.g.state;self.g.clock(m.clock.to_sec())
   if self.proc and self.proc.poll() is not None:self.g.invalidate('estimator_exited:'+str(self.proc.returncode))
   if self.g.state=='BOOTSTRAP_PUBLIC_POSE':self.tf(self.g.anchor[:3,3],Rotation.from_matrix(self.g.anchor[:3,:3]).as_quat(),m.clock)
   elif self.g.state=='INVALID_STOP':
    if old!='INVALID_STOP':self.hold()
    else:self.vel.publish(Twist())
   if old!=self.g.state or int(m.clock.to_nsec())%100000000==0:self.publish_status()
 def tf(self,p,q,stamp):
  t=TransformStamped();t.header.stamp=stamp;t.header.frame_id='odom';t.child_frame_id='base_footprint';t.transform.translation.x,t.transform.translation.y,t.transform.translation.z=p;t.transform.rotation.x,t.transform.rotation.y,t.transform.rotation.z,t.transform.rotation.w=q;self.br.sendTransform(t)
 def pose(self,m,epoch):
  with self.lock:
   if epoch!=self.g.epoch:return  # callback from unregistered previous reset subscription
   if getattr(m,'_connection_header',{}).get('callerid')!='/ov_msckf':
    self.g.invalidate('unregistered_estimator_authority');self.hold();self.publish_status();return
   p=m.pose.pose.position;q=m.pose.pose.orientation
   try:
    po,c=self.g.accept(m.header.stamp.to_sec(),m.header.frame_id,[p.x,p.y,p.z,q.x,q.y,q.z,q.w],m.pose.covariance)
    o=Odometry();o.header=m.header;o.header.frame_id='odom';o.child_frame_id='base_footprint';o.pose.pose.position.x,o.pose.pose.position.y,o.pose.pose.position.z=po[:3];o.pose.pose.orientation.x,o.pose.pose.orientation.y,o.pose.pose.orientation.z,o.pose.pose.orientation.w=po[3:];o.pose.covariance=c.flatten().tolist();self.pub.publish(o);self.tf(po[:3],po[3:],m.header.stamp)
   except ValueError:self.hold()
   self.publish_status()
 def shutdown(self):
  with self.lock:self.hold();self.stop_vio()
if __name__=='__main__':rospy.init_node('pose_bridge');Adapter();rospy.spin()
