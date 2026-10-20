import json, sys, time
import rospy
from std_srvs.srv import Empty
rospy.init_node("scwm_pause_probe", anonymous=True, disable_signals=True)
rospy.wait_for_service("gazebo/pause_physics", timeout=20)
p = rospy.ServiceProxy("gazebo/pause_physics", Empty); u = rospy.ServiceProxy("gazebo/unpause_physics", Empty)
res = []
for _ in range(6):
    t0 = time.perf_counter(); p(); t1 = time.perf_counter(); time.sleep(0.2); u(); t2 = time.perf_counter(); time.sleep(0.5)
    res.append((round(t1 - t0, 3), round(t2 - t1 - 0.2, 3)))
print(res)
