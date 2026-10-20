#!/usr/bin/env python3
"""task4.8 reset-cost probe: time Gazebo spawn/delete of N boxes sequentially vs from concurrent threads, physics paused vs running. Own models only
(names probe_*), removed at the end. Needs a running simulation; no policy/env."""
import json, sys, threading, time
import rospy
from std_srvs.srv import Empty
from gazebo_msgs.srv import SpawnModel, DeleteModel
from geometry_msgs.msg import Pose

rospy.init_node("scwm_spawn_probe", anonymous=True, disable_signals=True)
for s in ("gazebo/spawn_sdf_model", "gazebo/delete_model", "gazebo/pause_physics", "gazebo/unpause_physics"):
    rospy.wait_for_service(s, timeout=20)
sp = lambda: rospy.ServiceProxy("gazebo/spawn_sdf_model", SpawnModel)
dl = lambda: rospy.ServiceProxy("gazebo/delete_model", DeleteModel)
pause = rospy.ServiceProxy("gazebo/pause_physics", Empty); unpause = rospy.ServiceProxy("gazebo/unpause_physics", Empty)
SDF = """<sdf version="1.6"><model name="b"><static>true</static><link name="l"><collision name="c"><geometry><box><size>0.5 0.5 0.5</size></box></geometry></collision><visual name="v"><geometry><box><size>0.5 0.5 0.5</size></box></geometry></visual></link></model></sdf>"""
N = int(sys.argv[1]) if len(sys.argv) > 1 else 16
def pose(i):
    p = Pose(); p.position.x = 20 + (i % 4) * 2; p.position.y = 20 + (i // 4) * 2; p.position.z = 0.25; p.orientation.w = 1; return p
def run(threads, paused, tag):
    out = {}
    names = ["probe_%s_%d" % (tag, i) for i in range(N)]
    if paused: pause()
    t0 = time.perf_counter()
    if threads:
        ts = [threading.Thread(target=lambda n=n, i=i: sp()(n, SDF, "", pose(i), "world")) for i, n in enumerate(names)]
        [t.start() for t in ts]; [t.join() for t in ts]
    else:
        s = sp()
        for i, n in enumerate(names): s(n, SDF, "", pose(i), "world")
    out["spawn_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    if threads:
        ts = [threading.Thread(target=lambda n=n: dl()(n)) for n in names]
        [t.start() for t in ts]; [t.join() for t in ts]
    else:
        d = dl()
        for n in names: d(n)
    out["delete_s"] = time.perf_counter() - t0
    if paused: unpause()
    return out
res = {}
for paused in (True, False):
    for threads in (False, True):
        res["paused=%s threads=%s" % (paused, threads)] = run(threads, paused, "%d%d" % (paused, threads))
print(json.dumps(res, indent=1))
json.dump(res, open(sys.argv[2], "w"), indent=1) if len(sys.argv) > 2 else None
