#!/usr/bin/env python3
"""Check-side driver for the Task3 lifecycle regressions (container, ROS only).

  --mode hold   publish /cmd_vel (0.2 m/s) at 20 Hz and keep re-sending a 3 s arm goal until killed (interrupt tests)
  --mode die    spawn a child `--mode hold`, SIGKILL it after --run-s simulated seconds, then record what the robot does:
                the base must come to rest (diff_drive cmd_vel_timeout 0.25 s) and the arm must settle at its goal (the action goal
                is finite; a dead client leaves no runaway). Writes lifecycle_die.json, exit 0 iff both hold."""
import argparse
import json
import math
import os
import signal
import subprocess
import sys
import time

import actionlib
import rospy
from control_msgs.msg import FollowJointTrajectoryAction, FollowJointTrajectoryGoal
from gazebo_msgs.msg import ModelStates
from geometry_msgs.msg import Twist
from control_msgs.msg import JointTrajectoryControllerState
from trajectory_msgs.msg import JointTrajectoryPoint

ARM = ["ur5_shoulder_pan_joint", "ur5_shoulder_lift_joint", "ur5_elbow_joint", "ur5_wrist_1_joint", "ur5_wrist_2_joint", "ur5_wrist_3_joint"]


def hold():
    rospy.init_node("lifecycle_hold", anonymous=True)
    pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
    cl = actionlib.SimpleActionClient("/eff_joint_traj_controller/follow_joint_trajectory", FollowJointTrajectoryAction)
    cl.wait_for_server(rospy.Duration(30))
    st = rospy.wait_for_message("/eff_joint_traj_controller/state", JointTrajectoryControllerState, timeout=10)
    q = dict(zip(st.joint_names, st.actual.positions))
    goal = FollowJointTrajectoryGoal()
    goal.trajectory.joint_names = ARM
    pt = JointTrajectoryPoint()
    pt.positions = [q[j] + (0.3 if j == ARM[0] else 0.0) for j in ARM]
    pt.time_from_start = rospy.Duration(3.0)
    goal.trajectory.points = [pt]
    goal.trajectory.header.stamp = rospy.Time.now()
    cl.send_goal(goal)
    while not rospy.is_shutdown():
        t = Twist()
        t.linear.x = 0.2
        pub.publish(t)
        time.sleep(0.05)


def die(run_s, observe_s):
    rospy.init_node("lifecycle_die", anonymous=True)
    truth = {}
    arm = {}

    def cb(m):
        if "husky_ur5" in m.name:
            i = m.name.index("husky_ur5")
            truth["v"] = (rospy.get_time(), m.twist[i].linear.x, m.twist[i].linear.y)

    def cs(m):
        arm["v"] = (rospy.get_time(), list(m.actual.velocities), list(m.desired.positions), list(m.actual.positions))

    rospy.Subscriber("/gazebo/model_states", ModelStates, cb, queue_size=1)
    rospy.Subscriber("/eff_joint_traj_controller/state", JointTrajectoryControllerState, cs, queue_size=1)
    while "v" not in truth or "v" not in arm:
        time.sleep(0.05)
    child = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--mode", "hold"], start_new_session=True)
    t0 = rospy.get_time()
    peak = 0.0
    while rospy.get_time() - t0 < run_s:
        time.sleep(0.05)
        peak = max(peak, math.hypot(truth["v"][1], truth["v"][2]))
    os.killpg(os.getpgid(child.pid), signal.SIGKILL)       # the client dies without sending a stop command
    child.wait()
    t_kill = rospy.get_time()
    while rospy.get_time() - t_kill < observe_s:
        time.sleep(0.05)
    speed_end = math.hypot(truth["v"][1], truth["v"][2])
    vel_end = max(abs(x) for x in arm["v"][1])
    err_end = max(abs(a - b) for a, b in zip(arm["v"][2], arm["v"][3]))
    out = dict(peak_speed_before_kill=peak, speed_after=speed_end, arm_vel_max_after=vel_end, arm_goal_err_after=err_end,
               run_s=run_s, observe_s=observe_s, sim_t_kill=t_kill,
               verdicts=dict(base_was_moving=peak > 0.1, base_stops_without_client=speed_end < 0.02,
                             arm_settles_without_client=vel_end < 0.02 and err_end < 0.02))
    out["ok"] = all(out["verdicts"].values())
    res = os.environ.get("FOREM_RES_DIR", "results/task3/lifecycle")
    os.makedirs(res, exist_ok=True)
    json.dump(out, open(os.path.join(res, "lifecycle_die.json"), "w"), indent=1)
    for k, v in out["verdicts"].items():
        print(("PASS " if v else "FAIL ") + k)
    print("OK" if out["ok"] else "NOT OK", json.dumps({k: v for k, v in out.items() if k != "verdicts"}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["hold", "die"])
    ap.add_argument("--run-s", type=float, default=5.0)
    ap.add_argument("--observe-s", type=float, default=4.0)
    a = ap.parse_args()
    sys.exit(hold() if a.mode == "hold" else die(a.run_s, a.observe_s))
