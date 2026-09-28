"""Verify controllers, costmap and physical base motion in the empty world."""
import json
import argparse
import math
import time

import rospy
import rosgraph
from controller_manager_msgs.srv import ListControllers
from gazebo_msgs.srv import GetWorldProperties, GetModelState
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid

parser = argparse.ArgumentParser()
parser.add_argument("--startup-only", action="store_true",
                    help="Check P0 environment readiness without testing robot motion")
args = parser.parse_args()
# Read parameters before init_node so rospy subscribes to the simulation clock.
# wait_for_service before init_node can itself fail while logging a missing master.
deadline = time.monotonic() + 30
while True:
    if rosgraph.is_master_online() and rospy.get_param("/use_sim_time", False):
        break
    assert time.monotonic() < deadline, "Start the Gazebo launch before this check"
    time.sleep(0.1)
rospy.init_node("docker_gazebo_smoke", anonymous=True)
rospy.wait_for_service("/controller_manager/list_controllers", timeout=30)
assert rospy.get_param("/use_sim_time")
assert rospy.get_param("/robot_description_kinematics/manipulator/kinematics_solver") == "bio_ik/BioIKKinematicsPlugin"
deadline = time.monotonic() + 30
while True:
    controllers = rospy.ServiceProxy("/controller_manager/list_controllers", ListControllers)().controller
    running = [c.name for c in controllers if c.state == "running"]
    if all(c in running for c in ["husky_velocity_controller", "eff_joint_traj_controller", "gripper_controller"]):
        break
    assert time.monotonic() < deadline, running
    time.sleep(0.1)
costmap = rospy.wait_for_message("/costmap_node/costmap/costmap", OccupancyGrid, timeout=30)
assert costmap.info.width > 0 and costmap.info.height > 0
world = rospy.ServiceProxy("/gazebo/get_world_properties", GetWorldProperties)()
names = [n for n in world.model_names if "husky" in n]
assert len(names) == 1, world.model_names
get_state = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)
before = get_state(names[0], "world")
assert before.success
if args.startup_only:
    print(json.dumps({"result": "PASS", "scope": "Gazebo startup only; motion not tested",
                      "model": names[0], "running_controllers": running,
                      "costmap_shape": [costmap.info.width, costmap.info.height],
                      "simulation_time": world.sim_time}, indent=2))
    raise SystemExit(0)
pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
deadline = time.monotonic() + 10
while not pub.get_num_connections() and time.monotonic() < deadline:
    time.sleep(0.05)
assert pub.get_num_connections(), "No velocity controller subscriber"
cmd = Twist()
cmd.linear.x = 0.15
try:
    start_sim = rospy.get_time()
    deadline = time.monotonic() + 45
    while rospy.get_time() - start_sim < 2.0:
        assert time.monotonic() < deadline, "Simulation clock did not advance by 2 seconds"
        pub.publish(cmd)
        time.sleep(0.05)
finally:
    for _ in range(5):
        pub.publish(Twist())
        time.sleep(0.05)
after = get_state(names[0], "world")
assert after.success
distance = math.hypot(after.pose.position.x - before.pose.position.x,
                      after.pose.position.y - before.pose.position.y)
print(json.dumps({"result": "PASS" if distance > 0.03 else "FAIL", "running_controllers": running,
                  "costmap_shape": [costmap.info.width, costmap.info.height],
                  "base_displacement_m": distance}, indent=2))
assert distance > 0.03, distance
