#!/usr/bin/env python3
"""Load and start the ros_control controllers while Gazebo is paused, then unpause.

Gazebo is started paused so the spawned arm cannot fall before a controller holds it.
Order: wait for the spawned model -> set the initial joint configuration (still paused, so
the controller's hold position is this pose, not the spawn-time zero pose) -> load
controllers -> issue the (blocking) switch request in a thread -> unpause physics -> wait
until every controller is 'running'. controller_manager only completes a switch inside
update(), which needs the physics to step.

Wall-clock time is used on purpose: /clock does not advance while physics is paused.
"""
import sys
import threading
import time

import rospy
from gazebo_msgs.srv import GetModelState, SetModelConfiguration
from controller_manager_msgs.srv import (ListControllers, LoadController,
                                         SwitchController, SwitchControllerRequest)
from std_srvs.srv import Empty

TIMEOUT = 60.0


def wait_service(name, timeout=TIMEOUT):
    rospy.wait_for_service(name, timeout=timeout)


def main():
    rospy.init_node("start_controllers", anonymous=False)
    controllers = rospy.get_param("~controllers", ["joint_state_controller", "eff_joint_traj_controller"])
    cm = rospy.get_param("~controller_manager", "/controller_manager")
    unpause = rospy.get_param("~unpause", True)
    model = rospy.get_param("~model_name", "forem_ur5")
    init_pose = rospy.get_param("~init_pose", {})

    wait_service(cm + "/load_controller")
    wait_service(cm + "/switch_controller")
    wait_service(cm + "/list_controllers")
    load = rospy.ServiceProxy(cm + "/load_controller", LoadController)
    switch = rospy.ServiceProxy(cm + "/switch_controller", SwitchController)
    lst = rospy.ServiceProxy(cm + "/list_controllers", ListControllers)

    if init_pose:
        wait_service("/gazebo/get_model_state")
        wait_service("/gazebo/set_model_configuration")
        get_state = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)
        deadline = time.time() + TIMEOUT
        while not get_state(model, "world").success:
            if time.time() > deadline:
                rospy.logerr("model %s never appeared", model)
                sys.exit(4)
            time.sleep(0.1)
        names = sorted(init_pose)
        res = rospy.ServiceProxy("/gazebo/set_model_configuration", SetModelConfiguration)(
            model, "robot_description", names, [float(init_pose[n]) for n in names])
        rospy.loginfo("set initial configuration %s -> %s (%s)", init_pose, res.success, res.status_message)
        if not res.success:
            sys.exit(5)

    for c in controllers:
        ok = load(c).ok
        rospy.loginfo("load %s -> %s", c, ok)
        if not ok:
            rospy.logerr("failed to load %s", c)
            sys.exit(1)

    result = {}

    def do_switch():
        # Blocks until gazebo_ros_control runs update(), i.e. until physics is stepping.
        result["ok"] = switch(start_controllers=controllers, stop_controllers=[],
                              strictness=SwitchControllerRequest.STRICT).ok

    t = threading.Thread(target=do_switch)
    t.start()
    time.sleep(0.5)

    if unpause:
        wait_service("/gazebo/unpause_physics")
        rospy.ServiceProxy("/gazebo/unpause_physics", Empty)()
        rospy.loginfo("physics unpaused")

    t.join(timeout=TIMEOUT)
    if t.is_alive() or not result.get("ok"):
        rospy.logerr("switch_controller did not succeed: %s", result)
        sys.exit(2)

    deadline = time.time() + 10.0
    while time.time() < deadline:
        states = {c.name: c.state for c in lst().controller}
        if all(states.get(c) == "running" for c in controllers):
            rospy.loginfo("controllers running: %s", states)
            return
        time.sleep(0.1)
    rospy.logerr("controllers not running: %s", states)
    sys.exit(3)


if __name__ == "__main__":
    main()
