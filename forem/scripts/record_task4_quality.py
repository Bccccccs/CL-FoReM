#!/usr/bin/env python3
"""Separate evaluation node; no truth is delivered to actor or estimator."""
import json,os,signal
from pathlib import Path
import rospy
from gazebo_msgs.msg import LinkStates
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
import numpy as np
from scipy.spatial.transform import Rotation
import xml.etree.ElementTree as ET
rospy.init_node('task4_independent_quality',disable_signals=True)
out=Path(os.environ['FOREM_RES_DIR']);description=rospy.get_param('/robot_description');(out/'robot_description.urdf').write_text(description)
root=ET.fromstring(description);joints={j.find('child').get('link'):j for j in root.findall('joint')};chain=[];n='gripper_base_link'
while n!='ur5_wrist_3_link':
 j=joints[n]
 if j.get('type')!='fixed':raise RuntimeError('physical wrist-to-gripper path must be static')
 chain.insert(0,j);n=j.find('parent').get('link')
T=np.eye(4)
for j in chain:
 origin=j.find('origin');xyz=[float(v) for v in origin.get('xyz','0 0 0').split()];rpy=[float(v) for v in origin.get('rpy','0 0 0').split()];a=np.eye(4);a[:3,:3]=Rotation.from_euler('xyz',rpy).as_matrix();a[:3,3]=xyz;T=T@a
(out/'physical_link_contract.json').write_text(json.dumps({'physical_link':'husky_ur5::ur5_wrist_3_link','target_link':'gripper_base_link','static_joint_names':[j.get('name') for j in chain],'T_wrist3_gripper':T.tolist(),'reason':'Gazebo fixed-joint reduction'},indent=2))
streams={n:(out/(n+'.jsonl')).open('a') for n in ('physical','joint_feedback','poses')}
def emit(n,r):streams[n].write(json.dumps(r)+'\n');streams[n].flush()
def physical(m):
 key='husky_ur5::ur5_wrist_3_link'
 if key not in m.name:return
 p=m.pose[m.name.index(key)];v=p.position;q=p.orientation
 # LinkStates has NO header. Explicit receipt sim-time, separate from exact p3d-header localization metrics.
 a=np.eye(4);a[:3,3]=[v.x,v.y,v.z];a[:3,:3]=Rotation.from_quat([q.x,q.y,q.z,q.w]).as_matrix();g=a@T
 emit('physical',{'stamp':rospy.get_time(),'time_source':'link_states_sim_receipt_no_header','link':key,'target_link':'gripper_base_link','pose':g[:3,3].tolist()+Rotation.from_matrix(g[:3,:3]).as_quat().tolist()})
def poses(m):
 p=m.pose.pose.position;q=m.pose.pose.orientation;emit('poses',{'stamp':m.header.stamp.to_sec(),'p':[p.x,p.y,p.z],'q':[q.x,q.y,q.z,q.w],'sim_receipt':rospy.get_time()})
rospy.Subscriber('/gazebo/link_states',LinkStates,physical,queue_size=10000)
rospy.Subscriber('/forem/pose/estimated',Odometry,poses,queue_size=10000)
rospy.Subscriber('/joint_states',JointState,lambda m:emit('joint_feedback',{'stamp':m.header.stamp.to_sec(),'name':list(m.name),'position':list(m.position),'velocity':list(m.velocity)}),queue_size=10000)
signal.signal(signal.SIGINT,lambda *_:rospy.signal_shutdown('own evaluator stopping'))
signal.signal(signal.SIGTERM,lambda *_:rospy.signal_shutdown('own evaluator stopping'))
rospy.spin()
for f in streams.values():f.close()
