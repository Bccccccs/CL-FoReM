#!/usr/bin/env python3
"""Offline independent actual task outcomes. Never actor/estimator imported."""
import argparse,json
from pathlib import Path
import numpy as np
from analyze_task4_localization import actual_success

def evaluate_physical(run):
 run=Path(run);steps=json.loads((run/'task_steps.json').read_text());spec=json.loads((run/'episode_spec.json').read_text());rows=[json.loads(s) for s in (run/'physical.jsonl').read_text().splitlines()];joints=[json.loads(s) for s in (run/'joint_feedback.jsonl').read_text().splitlines()];times=np.asarray([r['stamp'] for r in rows]);jtimes=np.asarray([r['stamp'] for r in joints]);required=['ur5_'+n+'_joint' for n in ['shoulder_pan','shoulder_lift','elbow','wrist_1','wrist_2','wrist_3']];evaluated=[]
 for step in steps:
  result={'step':step['step'],'stamp':step['stamp'],'success':False,'valid':False};info=step.get('info',{})
  if len(times) and len(jtimes):
   idx=int(np.argmin(abs(times-step['stamp'])));ji=int(np.argmin(abs(jtimes-step['stamp'])));j=joints[ji];lookup=dict(zip(j['name'],j['position']));complete=all(n in lookup and np.isfinite(lookup[n]) for n in required);skew=float(abs(times[idx]-step['stamp']));jskew=float(abs(jtimes[ji]-step['stamp']))
   result.update(physical_matching_skew_s=skew,joint_matching_skew_s=jskew,joint_feedback_complete=complete)
   if skew<=.02 and jskew<=.04 and complete and 'nr_kin_failures' in info and 'nr_base_collisions' in info:
    result.update(actual_success(rows[idx]['pose'],spec['goal_wrist'],info['nr_kin_failures'],info['nr_base_collisions']));result['actual_pose']=rows[idx]['pose']
  evaluated.append(result)
 return {'attempted_control_steps':len(steps),'valid_actual_feedback_steps':sum(r['valid'] for r in evaluated),'missing_or_invalid_actual_feedback_steps':sum(not r['valid'] for r in evaluated),'original_internal_success':steps[-1].get('info',{}).get('success') if steps else None,'actual_task_success':bool(evaluated and evaluated[-1]['success'] and steps[-1].get('done')),'final_actual':evaluated[-1] if evaluated else None,'actual_goal_achieved_samples':sum(r['success'] for r in evaluated),'physical_time_limitation':'Gazebo LinkStates has no header; sim receipt nearest matching, not exact physical measurement timestamp','feedback_rule':'six finite JointState feedback required, no fallback','physical_link_contract':json.loads((run/'physical_link_contract.json').read_text()),'steps':evaluated}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();r=evaluate_physical(a.run);Path(a.run,'actual_task_evaluation.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='steps'}))
