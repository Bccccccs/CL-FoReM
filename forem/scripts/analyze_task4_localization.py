#!/usr/bin/env python3
"""Evaluation-only. Original p3d stamps; no error fitting or actor truth access."""
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

from task4_instances import public_instance

def actual_success(actual,goal,kin_failures,collisions):
 if actual is None or len(actual)!=7 or len(goal)!=7 or not np.isfinite(actual+goal).all() or abs(np.linalg.norm(actual[3:])-1)>1e-3 or abs(np.linalg.norm(goal[3:])-1)>1e-3:return {'success':False,'valid':False,'reason':'missing_physical_feedback'}
 d=float(np.linalg.norm(np.asarray(actual[:3])-goal[:3]));r=float((Rotation.from_quat(goal[3:]).inv()*Rotation.from_quat(actual[3:])).magnitude());qd=float(1-np.dot(actual[3:],goal[3:])**2)
 return {'success':bool(d<.025 and qd<.05 and kin_failures==0 and collisions==0),'valid':True,'position_error_m':d,'rotation_error_rad':r,'quaternion_distance':qd}

def evaluate_rows(poses,truth,steps,max_skew=.02):
 result={'pose_count':len(poses),'matched':0,'attempted_control_steps':len(steps),'valid_control_steps':0,'valid_control_fraction':0.,'truth_evaluation_only':True,'alignment':'none_additional_already_public_once_aligned','max_matching_skew_s':max_skew}
 rows=[];times=np.asarray([v[0] for v in truth]);matchedstamps=[]
 for p in poses:
  if not np.isfinite(p.get('p',[])+p.get('q',[])+[p.get('stamp',float('nan'))]).all() or len(p.get('p',[]))!=3 or len(p.get('q',[]))!=4 or abs(np.linalg.norm(p['q'])-1)>1e-3:continue
  if not len(times):continue
  idx=int(np.argmin(abs(times-p['stamp'])));dt=float(abs(times[idx]-p['stamp']))
  if dt>max_skew:continue
  actual=truth[idx][1]
  if len(actual)!=7 or not np.isfinite(actual).all() or abs(np.linalg.norm(actual[3:])-1)>1e-3:continue
  err=np.asarray(p['p'])-actual[:3];ye=float((Rotation.from_quat(actual[3:]).inv()*Rotation.from_quat(p['q'])).as_euler('xyz')[2])
  rows.append({'estimate_stamp':p['stamp'],'truth_stamp':float(times[idx]),'position_error_m':err.tolist(),'yaw_error_rad':ye,'matching_skew_s':dt});matchedstamps.append(p['stamp'])
 valid=sum(any(0<=s['stamp']-t<=.1 for t in matchedstamps) for s in steps)
 result.update(matched=len(rows),matching_coverage=len(rows)/len(poses) if poses else 0.,valid_control_steps=valid,valid_control_fraction=valid/len(steps) if steps else 0.,invalid_control_steps=len(steps)-valid)
 if rows:
  e=np.asarray([r['position_error_m'] for r in rows]);y=np.asarray([r['yaw_error_rad'] for r in rows]);xy=np.linalg.norm(e[:,:2],axis=1)
  result.update(XY_RMSE_m=float(np.sqrt(np.mean(xy**2))),XY_peak_m=float(max(xy)),position_RMSE_m=float(np.sqrt(np.mean(np.sum(e**2,axis=1)))),yaw_RMSE_rad=float(np.sqrt(np.mean(y*y))),yaw_peak_rad=float(max(abs(y))),XY_final_m=float(xy[-1]),max_actual_matching_skew_s=max(r['matching_skew_s'] for r in rows))
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();out=Path(a.run)
 import rosbag
 truth=[]
 with rosbag.Bag(str(out/'evaluation.bag')) as b:
  for _,m,_ in b.read_messages(topics=['/ground_truth/state']):
   p=m.pose.pose.position;q=m.pose.pose.orientation;truth.append((m.header.stamp.to_sec(),[p.x,p.y,p.z,q.x,q.y,q.z,q.w]))
 poses=json.loads((out/'poses.json').read_text());steps=json.loads((out/'task_steps.json').read_text());r=evaluate_rows(poses,truth,steps)
 r['limitations']=['p3d gaussianNoise=.01; not instrument-grade truth','commanded initial z=.05 differs physical settling; XY gates only','unknown public-anchor covariance','missing/no-init/control errors remain attempted denominators']
 (out/'evaluation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r));return 0 if r['matched'] else 1
if __name__=='__main__':raise SystemExit(main())
