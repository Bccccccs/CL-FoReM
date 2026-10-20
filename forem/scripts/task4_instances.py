"""Actual public spawn/draw instance contract. No ROS/truth reads or additional RNG draws."""
import math

def public_instance(spec):
 return {k:v for k,v in spec.items() if k not in ('hash','base_tf')}

def verify_public_instance(actual,expected):
 if expected.get('schema')!=4 or public_instance(actual)!=public_instance(expected):raise ValueError('true public spawned/drawn instance contract mismatch')
 return True

def verify_spawn(spec):
 objects={o['name']:o for o in spec['obstacles']};spawns={o['name']:o for o in spec['spawn_commands']}
 if not objects or set(objects)!=set(spawns):raise ValueError('actual spawn denominator/objects mismatch')
 for n,o in objects.items():
  s=spawns[n]
  if o['frame']!=s['frame'] or o['pose']!=s['pose'] or len(s['sdf_sha256'])!=64:raise ValueError('actual spawn pose/frame/SDF mismatch:'+n)
 return True

def canonical_base(command):
 """Metadata-only XYZ+RPY→XYZ+xyzw using original full precision; never change/reset command."""
 if len(command)==7:return list(command)
 if len(command)!=6:raise ValueError('public base command must be original six RPY or seven xyzw')
 x,y,z,roll,pitch,yaw=map(float,command);sr,cr=math.sin(roll/2),math.cos(roll/2);sp,cp=math.sin(pitch/2),math.cos(pitch/2);sy,cy=math.sin(yaw/2),math.cos(yaw/2)
 return [x,y,z,sr*cp*cy-cr*sp*sy,cr*sp*cy+sr*cp*sy,cr*cp*sy-sr*sp*cy,cr*cp*cy+sr*sp*sy]

def run_quality_steps(env,actions,initialized,stamp,clock,deadline,emit):
 """Bounded measurement commands, never a training loop or task termination override."""
 if not initialized:raise ValueError('measurement action prohibited before successful fresh reset')
 if actions is not None:
  if len(actions)!=76 or any(len(a)!=3 or any(not math.isfinite(float(v)) or abs(float(v))>1 for v in a) for a in actions):raise ValueError('fixed replay needs exactly76 finite bounded3D commands')
 cap=76 if actions is not None else 1000;steps=[];done=False;info={};error=None
 while not done and len(steps)<cap and clock()<deadline:
  tick=clock();index=len(steps);action=list(actions[index]) if actions is not None else [0,0,0]
  row={'step':index,'stamp_before':stamp(),'attempted':True,'action':action};steps.append(row)
  try:
   obs,reward,done,info=env.step(action)
   row.update(stamp=stamp(),reward=reward,done=bool(done),info=info,wall_s=clock()-tick)
  except BaseException as e:
   error=repr(e);row.update(stamp=stamp(),error=error,wall_s=clock()-tick)
  emit(row)
  if error:break
 complete=error is None and ((len(steps)==76) if actions is not None else bool(done))
 return {'steps':steps,'done':bool(done),'info':info,'error':error,'measurement_complete':complete,'requested_step_cap':cap,'unattempted_steps':cap-len(steps),'mode':'fixed76_commands_only' if actions is not None else 'original_zero_until_done','training_updates':0}

def legacy_public_checks(first,legacy):
 """Exact original6dp values; quaternion admits only one whole-vector sign change."""
 p=first['initial_base_pose_xyzw'];old=legacy['base_tf']
 finite=len(p)==7 and len(old)==7 and all(math.isfinite(float(v)) for v in p+old)
 q=p[3:];expected=old[3:]
 same=finite and p[:2]==old[:2] and (q==expected or q==[-v for v in expected])
 return {'initial_base_XY_quaternion_6dp':same,**{k:first[k]==legacy[k] for k in ('arm_joints_planned','goal_tip','goal_wrist','map_size_m')}}

def persist_capture_evidence(path,first,second,commanded,before,middle,after,legacy,expected):
 """Persist actual inputs before validation. A failed draw remains evidence, never a seal."""
 import json
 from pathlib import Path
 evidence={'first':first,'second':second,'commanded_initial':commanded,'capture_rng_before':before,'capture_rng_middle':middle,'capture_rng_after':after,'expected_legacy':legacy,'expected_repeat':expected,'legacy_reliable_fields':legacy_public_checks(first,legacy),'public_capture_repeat_equal':public_instance(first)==public_instance(second),'capture_rng_unchanged':bool(before) and before==middle==after,'repeat_expected_equal':expected is None or public_instance(first)==public_instance(expected)}
 Path(path).write_text(json.dumps(evidence,indent=2,allow_nan=False));return evidence
