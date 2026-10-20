#!/usr/bin/env python3
"""Bounded VIO-initialization availability survey over Task4 training instances (task4.5 diagnostic, SRC0151).
Original Task4Env reset lifecycle only (begin -> C++ reset -> re-placement -> fresh VIO -> READY or 120 s timeout).
No actions, no learning, no truth. One raw stereo pair per instance is saved when reset returns or fails.
"""
import json,os,signal,sys,threading,time
from pathlib import Path
WHOLE_CAP=1800
WORST_INSTANCE_S=200   # 120 s init timeout + original reset/teardown margin
MAX_INSTANCES=40

def parse_instances(text):
 a,_,b=text.partition('-');lo,hi=int(a),int(b)
 if lo<0 or hi>99 or hi<lo or hi-lo+1>MAX_INSTANCES:raise ValueError('training instances 0-99 only, at most %d'%MAX_INSTANCES)
 return list(range(lo,hi+1))

def may_start(wall):return wall<=WHOLE_CAP-WORST_INSTANCE_S

def survey(env,instances,clock,wall,emit,snapshot):
 for inst in instances:
  if not may_start(wall()):emit({'instance':inst,'attempted':False,'reason':'wall_gate'});continue
  row={'instance':inst,'attempted':True,'sim_start':clock(),'wall_start':wall()}
  try:env.reset(seed=inst);row.update(initialized=True,error=None)
  except Exception as e:row.update(initialized=False,error=repr(e))
  row.update(sim_end=clock(),wall_end=wall());snapshot(inst,'initialized' if row['initialized'] else 'failed');emit(row)

def main():
 import ray  # inherited pybind import order
 import rospy,cv2
 from sensor_msgs.msg import Image
 from rosgraph_msgs.msg import Clock
 from cv_bridge import CvBridge
 from task4_env import Task4Env
 from task4_identity import verify_runtime,semantic_identity
 out=Path(os.environ['FOREM_RES_DIR']);t0=time.monotonic();instances=parse_instances(sys.argv[1]);bridge=CvBridge();latest={};lock=threading.Lock()
 rospy.init_node('task4_init_survey',disable_signals=True)
 def keep(msg,side):
  with lock:latest[side]=msg
 rospy.Subscriber('/task4/stereo/left/image_raw',Image,keep,callback_args='left',queue_size=1,buff_size=4000000)
 rospy.Subscriber('/task4/stereo/right/image_raw',Image,keep,callback_args='right',queue_size=1,buff_size=4000000)
 rospy.Subscriber('/clock',Clock,lambda m:None,queue_size=1)
 (out/'container_identity_start.json').write_text(json.dumps(verify_runtime(),indent=1))
 def emit(row):
  with (out/'survey.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 def snapshot(inst,status):
  with lock:pair=dict(latest)
  for side,msg in pair.items():
   cv2.imwrite(str(out/('inst%02d_%s_%s_%d.png'%(inst,status,side,msg.header.stamp.to_nsec()))),bridge.imgmsg_to_cv2(msg,desired_encoding='bgr8'))
 env=None;error=None
 try:
  env=Task4Env(seed=0)
  survey(env,instances,rospy.get_time,lambda:time.monotonic()-t0,emit,snapshot)
 except BaseException as e:error=repr(e)
 finally:
  if env:
   try:env.close()
   except BaseException as e:error=error or repr(e)
  rows=[json.loads(l) for l in (out/'survey.jsonl').read_text().splitlines()] if (out/'survey.jsonl').exists() else []
  summary={'instances':instances,'attempted':sum(r.get('attempted',False) for r in rows),'initialized':sum(r.get('initialized',False) for r in rows),'failed':[r['instance'] for r in rows if r.get('attempted') and not r.get('initialized')],'not_attempted':[r['instance'] for r in rows if not r.get('attempted')],'error':error,'wall_s':time.monotonic()-t0,'actions':0,'training_updates':0}
  (out/'summary.json').write_text(json.dumps(summary,indent=1));(out/'container_identity_end.json').write_text(json.dumps(semantic_identity(),indent=1))
 print(json.dumps(summary));return 0 if error is None else 1
if __name__=='__main__':raise SystemExit(main())
