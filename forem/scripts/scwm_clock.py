"""FoReM Task4: optional fixed-sim-window stepping for the Gazebo environment.

Reference behaviour (mode "realtime", default): Gazebo runs unpaused in real time, so the SIM time between two consecutive command sends is
whatever the Python loop needs (policy inference + SAC update + env.step), i.e. it depends on the method (the feedback policy computes more), the
GPU and the machine load. The planner already uses the measured sim dt, so the dynamics stay self-consistent, but the DECISION INTERVAL differs
between methods/runs.

Mode "fixed": physics is paused whenever Python computes; each env.step first lets the simulation run for exactly W sim seconds under the
commands sent by the previous step, then pauses again. The sequence of reads/commands inside env.step is untouched (the observation still
carries the same one-command latency as in the reference), only the sim time elapsed between two sends is controlled. Physics step, solver,
task, reward, observation and action semantics are not changed. Optional `unthrottle` removes the wall-clock pacing of the physics loop
(max_update_rate=0): it changes how fast the identical sim-time trajectory is computed, not the trajectory.

Needs a running simulation. Services: /gazebo/pause_physics, /gazebo/unpause_physics, /gazebo/get_physics_properties, /gazebo/set_physics_properties.
"""
import time

import rospy
from std_srvs.srv import Empty
from gazebo_msgs.srv import GetPhysicsProperties, SetPhysicsProperties


class FixedWindowClock:
    def __init__(self, window_s, unthrottle=True):
        self.window = float(window_s)
        rospy.wait_for_service("/gazebo/pause_physics", timeout=30)
        self._pause = rospy.ServiceProxy("/gazebo/pause_physics", Empty, persistent=True)
        self._unpause = rospy.ServiceProxy("/gazebo/unpause_physics", Empty, persistent=True)
        self.stats = dict(n=0, overshoot_sum=0.0, overshoot_max=0.0, wall_sum=0.0)
        self.physics_before = None
        if unthrottle:
            self.unthrottle()

    # ---- physics pacing -------------------------------------------------------------------------------------------
    def unthrottle(self):
        get = rospy.ServiceProxy("/gazebo/get_physics_properties", GetPhysicsProperties)
        setp = rospy.ServiceProxy("/gazebo/set_physics_properties", SetPhysicsProperties)
        p = get()
        self.physics_before = dict(time_step=p.time_step, max_update_rate=p.max_update_rate)
        if p.max_update_rate != 0.0:
            setp(time_step=p.time_step, max_update_rate=0.0, gravity=p.gravity, ode_config=p.ode_config)

    def restore_pacing(self):
        if self.physics_before is None:
            return
        get = rospy.ServiceProxy("/gazebo/get_physics_properties", GetPhysicsProperties)
        setp = rospy.ServiceProxy("/gazebo/set_physics_properties", SetPhysicsProperties)
        p = get()
        setp(time_step=p.time_step, max_update_rate=self.physics_before["max_update_rate"], gravity=p.gravity, ode_config=p.ode_config)

    # ---- window control -------------------------------------------------------------------------------------------
    def pause(self):
        self._pause()

    def advance(self):
        """Run the simulation for window_s sim seconds, then pause. Returns the sim time actually elapsed."""
        w0 = time.perf_counter()
        t0 = rospy.get_time()
        target = t0 + self.window
        self._unpause()
        while rospy.get_time() < target:
            time.sleep(0.0002)
        self._pause()
        elapsed = rospy.get_time() - t0
        self.stats["n"] += 1
        over = elapsed - self.window
        self.stats["overshoot_sum"] += over
        self.stats["overshoot_max"] = max(self.stats["overshoot_max"], over)
        self.stats["wall_sum"] += time.perf_counter() - w0
        return elapsed

    def mean_overshoot(self):
        return self.stats["overshoot_sum"] / max(self.stats["n"], 1)


class PacingControl:
    """Wall-clock pacing of the physics loop only (max_update_rate); the physics step, solver and every sim-time quantity are untouched.
    Used to run the scene reset (no policy in the loop) unthrottled and restore the original pacing before the first step."""

    def __init__(self):
        rospy.wait_for_service("/gazebo/get_physics_properties", timeout=30)
        self._get = rospy.ServiceProxy("/gazebo/get_physics_properties", GetPhysicsProperties, persistent=True)
        self._set = rospy.ServiceProxy("/gazebo/set_physics_properties", SetPhysicsProperties, persistent=True)
        self.saved = None

    def unthrottle(self):
        p = self._get()
        self.saved = p.max_update_rate
        if p.max_update_rate != 0.0:
            self._set(time_step=p.time_step, max_update_rate=0.0, gravity=p.gravity, ode_config=p.ode_config)

    def restore(self):
        if self.saved is None:
            return
        p = self._get()
        if p.max_update_rate != self.saved:
            self._set(time_step=p.time_step, max_update_rate=self.saved, gravity=p.gravity, ode_config=p.ode_config)
        self.saved = None
