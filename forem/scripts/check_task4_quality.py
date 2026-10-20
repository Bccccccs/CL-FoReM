#!/usr/bin/env python3
"""One complete original zero-action diagnostic; independent evaluator owns truth."""
import ray
import torch
import json,os,signal,subprocess,time
from pathlib import Path
from task4_env import Task4Env
from task4_identity import verify_runtime,semantic_identity
import rospy
rospy.init_node('task4_quality_actor',disable_signals=True)
out=Path(os.environ['FOREM_RES_DIR']);t0=time.monotonic();env=None;steps=[];error=None;done=False;info={};spec=None
verify_runtime();(out/'container_identity_start.json').write_text(json.dumps(semantic_identity(),indent=2))
bag=subprocess.Popen(['rosbag','record','-q','-O',str(out/'evaluation.bag'),'/ground_truth/state']);evaluation=subprocess.Popen(['python3','-u','scripts/record_task4_quality.py'])
try:
 time.sleep(1);env=Task4Env(seed=0);st=time.monotonic();obs=env.reset(seed=0);init=time.monotonic()-st;spec=env.episode_spec
 (out/'episode_spec.json').write_text(json.dumps(spec,indent=2));(out/'commanded_initial.json').write_text(json.dumps(rospy.get_param('/task4/localization/commanded_pose')))
 while not done and len(steps)<1000 and time.monotonic()-t0<850:
  st=time.monotonic();row={'step':len(steps),'stamp_before':rospy.get_time(),'attempted':True};steps.append(row)
  try:obs,reward,done,info=env.step([0,0,0])
  except BaseException as e:row.update(error=repr(e),stamp=rospy.get_time());raise
  row.update(stamp=rospy.get_time(),wall_s=time.monotonic()-st,reward=reward,done=done,info=info)
  with (out/'task_steps.jsonl').open('a') as f:f.write(json.dumps(row,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n');f.flush()
except BaseException as e:error=repr(e)
finally:
 if env:
  try:env.close()
  except BaseException:pass
 for p in (evaluation,bag):
  p.send_signal(signal.SIGINT)
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)
 (out/'task_steps.json').write_text(json.dumps(steps,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
 (out/'poses.json').write_text(json.dumps([json.loads(s) for s in (out/'poses.jsonl').read_text().splitlines()]))
 (out/'summary.json').write_text(json.dumps({'steps':len(steps),'done':done,'success':info.get('success'),'error':error,'wall_s':time.monotonic()-t0,'init_wall_s':locals().get('init'),'info':info,'evaluator_exit':evaluation.returncode,'truth_recorder_exit':bag.returncode},default=lambda x:x.item() if hasattr(x,'item') else str(x),indent=2))
 (out/'container_identity_end.json').write_text(json.dumps(semantic_identity(),indent=2))
raise SystemExit(0 if done and error is None else 1)
