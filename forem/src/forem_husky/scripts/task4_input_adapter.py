#!/usr/bin/env python3
"""Normalize verified multicamera frame names; expose only IMU gyro/accel.
No fabricated images, no orientation/pose use and no restamping. SRC-0071.
"""
import copy
import rospy
from sensor_msgs.msg import Image, CameraInfo, Imu
from rosgraph_msgs.msg import Clock
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from check_task4_sensors import SensorTime, validate_imu

class Adapter:
    def __init__(self):
        self.time=SensorTime()
        self.pubs={}
        for side in ['left','right']:
            for kind,typ in [('image_raw',Image),('camera_info',CameraInfo)]:
                key=side+'/'+kind
                self.pubs[key]=rospy.Publisher('/task4/stereo/'+key,typ,queue_size=3)
                rospy.Subscriber('/task4/plugin/stereo/'+key,typ,self.camera,callback_args=(side,key),queue_size=3)
        self.imu_pub=rospy.Publisher('/task4/imu/data_raw',Imu,queue_size=100)
        rospy.Subscriber('/task4/plugin/imu',Imu,self.imu,queue_size=100)
        rospy.Subscriber('/clock',Clock,lambda m:self.time.on_clock(m.clock.to_nsec()),queue_size=100)
    def camera(self,m,args):
        side,key=args
        try:self.time.accept(key,m.header.stamp.to_nsec())
        except ValueError as e:rospy.logerr_throttle(2,str(e));return
        out=copy.deepcopy(m);out.header.frame_id='task4_'+side+'_optical'
        self.pubs[key].publish(out)
    def imu(self,m):
        try:
            self.time.accept('imu',m.header.stamp.to_nsec())
            validate_imu([m.linear_acceleration.x,m.linear_acceleration.y,m.linear_acceleration.z],[m.angular_velocity.x,m.angular_velocity.y,m.angular_velocity.z])
        except ValueError as e:rospy.logerr_throttle(2,str(e));return
        out=Imu();out.header=copy.deepcopy(m.header);out.header.frame_id='task4_imu_link'
        out.angular_velocity=copy.deepcopy(m.angular_velocity)
        out.linear_acceleration=copy.deepcopy(m.linear_acceleration)
        out.angular_velocity_covariance=list(m.angular_velocity_covariance)
        out.linear_acceleration_covariance=list(m.linear_acceleration_covariance)
        out.orientation_covariance[0]=-1
        self.imu_pub.publish(out)
if __name__=='__main__':
    rospy.init_node('task4_input_adapter'); Adapter();rospy.spin()
