#!/usr/bin/env python3
"""Single publisher of the policy-facing base pose TF (odom -> base_footprint).

Replaces the reference `pcl_configure/gdt_tf` node, which re-stamped every /ground_truth/state sample
with ros::Time::now() (receipt time) and published no source/status information.

Input : nav_msgs/Odometry on ~input_topic (default /ground_truth/state, the Gazebo p3d plugin;
        pose_source=gazebo_reference). Task4 replaces ONLY the source of this message (an estimator that
        publishes the same message type/frames) -- the TF publisher stays unique.
Output: TF ~parent_frame -> ~child_frame stamped with the INPUT message stamp (original sample time),
        plus a JSON status string on ~status_topic (source, frames, counters, last stamp, epoch).

A sample is rejected (not published, counted) when: any pose/quaternion component is non-finite; the
quaternion norm is not within 1 +- 0.05; header.frame_id is not in ~expected_frames; child_frame_id is
non-empty and differs from ~child_frame; the stamp is zero; the stamp is not strictly increasing (late/old
sample, however far back); the stamp is ahead of the simulation clock by more than ~future_tolerance; or the
bridge has halted.

Simulation reset (T3-A02): never inferred from sample stamps. The bridge subscribes the independent /clock
topic; a /clock rewind of more than ~reset_jump seconds is the reset event. The epoch counter is incremented
once, the bridge HALTS (publishes nothing more, status halted=true, every later sample counted as
rejected_halted) and the simulation + bridge must be restarted: /gazebo/reset_simulation is not supported for
the Task3 core. Samples keep their original stamp.
"""
import json
import math
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rosgraph_msgs.msg import Clock
from std_msgs.msg import String

from pose_gate import PoseGate


class PoseBridge:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/ground_truth/state")
        self.pose_source = rospy.get_param("~pose_source", "gazebo_reference")
        self.parent_frame = rospy.get_param("~parent_frame", "odom")
        self.child_frame = rospy.get_param("~child_frame", "base_footprint")
        self.gate = PoseGate(expected_frames=rospy.get_param("~expected_frames", ["world", "map", "odom"]),
                             child_frame=self.child_frame,
                             reset_jump_ns=int(float(rospy.get_param("~reset_jump", 1.0)) * 1e9),
                             future_tol_ns=int(float(rospy.get_param("~future_tolerance", 1.0)) * 1e9))
        self.published = 0
        self.br = tf2_ros.TransformBroadcaster()
        self.status_pub = rospy.Publisher(rospy.get_param("~status_topic", "~status"), String, queue_size=1, latch=True)
        self.lock = threading.Lock()                # /clock and pose callbacks run in different threads
        self.clock_sub = rospy.Subscriber("/clock", Clock, self.on_clock, queue_size=100)
        self.sub = rospy.Subscriber(self.input_topic, Odometry, self.cb, queue_size=50)
        rospy.Timer(rospy.Duration(1.0), self.publish_status)
        rospy.loginfo("pose_bridge: %s -> TF %s->%s (source=%s)", self.input_topic, self.parent_frame,
                      self.child_frame, self.pose_source)

    def on_clock(self, msg):
        with self.lock:
            event = self.gate.observe_clock(msg.clock.to_nsec())
        if event == "reset":
            rospy.logerr("pose_bridge: %s -- HALTED, no pose is published any more; restart the simulation and the bridge",
                         self.gate.halt_reason)
            self.publish_status(None)

    def cb(self, msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        with self.lock:          # check + publish atomically w.r.t. the clock thread: no sample is published after a reset was observed
            verdict, _ = self.gate.check(msg.header.frame_id, msg.child_frame_id, msg.header.stamp.to_nsec(),
                                         (p.x, p.y, p.z), (q.x, q.y, q.z, q.w))
            if verdict != "accept":
                return
            self._publish_tf(msg, p, q)

    def _publish_tf(self, msg, p, q):
        norm = math.sqrt(q.x ** 2 + q.y ** 2 + q.z ** 2 + q.w ** 2)
        t = TransformStamped()
        t.header.stamp = msg.header.stamp          # original sample stamp, never re-stamped
        t.header.frame_id = self.parent_frame
        t.child_frame_id = self.child_frame
        t.transform.translation.x, t.transform.translation.y, t.transform.translation.z = p.x, p.y, p.z
        t.transform.rotation.x, t.transform.rotation.y = q.x / norm, q.y / norm
        t.transform.rotation.z, t.transform.rotation.w = q.z / norm, q.w / norm
        self.br.sendTransform(t)
        self.published += 1

    def publish_status(self, _evt):
        with self.lock:
            last, clock = self.gate.last_stamp_ns, self.gate.clock_ns
            st = dict(pose_source=self.pose_source, input_topic=self.input_topic, parent_frame=self.parent_frame,
                      child_frame=self.child_frame, last_stamp=None if last is None else last * 1e-9,
                      clock=None if clock is None else clock * 1e-9, epoch=self.gate.epoch, halted=self.gate.halted,
                      halt_reason=self.gate.halt_reason, published=self.published, **self.gate.counts)
        self.status_pub.publish(String(data=json.dumps(st, sort_keys=True)))


if __name__ == "__main__":
    rospy.init_node("pose_bridge")
    PoseBridge()
    rospy.spin()
