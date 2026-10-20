"""task4.3.5 fixes (SRC0135/SRC0136): IMU-gated ZUPT and wheel joints restored at every Task4 reset."""
import ast,re,sys,types,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))

def estimator():
 v={}
 for line in (ROOT/'config/task4/estimator.yaml').read_text().splitlines():
  m=re.match(r'^([A-Za-z0-9_]+):\s*(\S+)',line)
  if m:v[m.group(1)]=m.group(2)
 return v

class ZuptMode(unittest.TestCase):
 def test_disparity_cannot_force_zupt_and_chi2_gate_active(self):
  v=estimator()
  self.assertEqual(float(v['zupt_max_disparity']),0.0)  # official "only imu-based": no disparity override
  self.assertGreaterEqual(float(v['zupt_chi2_multipler']),1.0)  # official chi2 consistency gate enabled
 def test_other_zupt_and_noise_choices_unchanged(self):
  v=estimator()
  self.assertEqual(v['try_zupt'],'true');self.assertEqual(v['zupt_only_at_beginning'],'true')
  self.assertEqual(float(v['zupt_max_velocity']),0.1);self.assertEqual(float(v['zupt_noise_multiplier']),10.0)
  self.assertEqual(float(v['init_imu_thresh']),1.5);self.assertEqual(float(v['init_window_time']),2.0)

class WheelReset(unittest.TestCase):
 def test_zero_wheels_calls_official_service_for_all_four_wheels(self):
  from task4_env import Task4Env,WHEEL_JOINTS
  calls=[]
  def service(**kw):calls.append(kw);return types.SimpleNamespace(success=True,status_message='ok')
  env=Task4Env.__new__(Task4Env);env._zero_wheels(service)
  self.assertEqual(calls,[{'model_name':'husky_ur5','urdf_param_name':'robot_description','joint_names':list(WHEEL_JOINTS),'joint_positions':[0.,0.,0.,0.]}])
  self.assertEqual(set(WHEEL_JOINTS),{'front_left_wheel','front_right_wheel','rear_left_wheel','rear_right_wheel'})
 def test_zero_wheels_failure_is_fail_closed(self):
  from task4_env import Task4Env
  env=Task4Env.__new__(Task4Env)
  with self.assertRaises(RuntimeError):env._zero_wheels(lambda **kw:types.SimpleNamespace(success=False,status_message='no model'))
 def test_reset_robot_zeroes_wheels_before_bootstrap_and_original_reset(self):
  tree=ast.parse((ROOT/'scripts/task4_env.py').read_text())
  fn=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='reset_robot'][0]
  order=[]
  for n in ast.walk(fn):
   if isinstance(n,ast.Call):
    f=n.func;name=f.attr if isinstance(f,ast.Attribute) else getattr(f,'id',None)
    if name in ('_zero_wheels','_begin','oldreset'):order.append((n.lineno,n.col_offset,name))
  self.assertEqual([x[2] for x in sorted(order)][:3],['_zero_wheels','_begin','oldreset'])
if __name__=='__main__':unittest.main()

class SelfMask(unittest.TestCase):
 """task4.3.5 (SRC0138/SRC0139): official OpenVINS static mask covering only the always-visible robot front plate."""
 SHA={'mask_left.png':'275d6e59ff3784dfb69347adedf5a069e3b67704d59ed3cf48918db6af272c95','mask_right.png':'35d82b7a51216217b3e49f8b7750f21f598c2bc847c1c6b76b715c4608890392'}
 def test_mask_enabled_with_both_cameras(self):
  v=estimator();self.assertEqual(v.get('use_mask'),'true');self.assertEqual(v.get('mask0'),'mask_left.png');self.assertEqual(v.get('mask1'),'mask_right.png')
 def test_mask_files_are_the_evaluated_candidate_and_small(self):
  import hashlib,cv2
  for name,sha in self.SHA.items():
   p=ROOT/'config/task4'/name;self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),sha)
   m=cv2.imread(str(p),0);self.assertEqual(m.shape,(480,640))
   frac=(m>127).mean();self.assertLess(frac,0.05);self.assertGreater(frac,0.0)
   self.assertFalse((m[:400]>127).any())  # only the bottom robot band; no scene region above row 400

class RestPlacement(unittest.TestCase):
 """task4.3.5 (SRC0141/SRC0142): after the original landing, re-place the base at the public commanded pose at rest height."""
 def test_replace_base_uses_public_commanded_pose_rest_height_zero_twist(self):
  from task4_env import Task4Env,REST_Z,PLACE_CLEARANCE
  calls=[];order=[]
  def service(state):calls.append(state);order.append('set');return types.SimpleNamespace(success=True,status_message='ok')
  env=Task4Env.__new__(Task4Env)
  cmd=[4.361373680140629,-2.2825187652325862,.05,0.,0.,0.9093158419353399,0.4161065964454588]
  env._replace_base(cmd,service,lambda:order.append('pause'),lambda:order.append('unpause'))
  self.assertEqual(order,['pause','set','unpause']);s=calls[0]
  self.assertEqual(s.model_name,'husky_ur5');self.assertEqual(s.reference_frame,'world');self.assertEqual(REST_Z,0.0);self.assertEqual(PLACE_CLEARANCE,0.003)
  p=s.pose.position;q=s.pose.orientation
  self.assertEqual([p.x,p.y,p.z],[cmd[0],cmd[1],0.003])  # never teleport into ground contact (rest-history-r1 arm explosion);self.assertEqual([q.x,q.y,q.z,q.w],cmd[3:])
  t=s.twist;self.assertEqual([t.linear.x,t.linear.y,t.linear.z,t.angular.x,t.angular.y,t.angular.z],[0.]*6)
 def test_replace_base_failure_is_fail_closed_and_unpauses(self):
  from task4_env import Task4Env
  order=[];env=Task4Env.__new__(Task4Env)
  with self.assertRaises(RuntimeError):env._replace_base([0,0,.05,0,0,0,1],lambda st:types.SimpleNamespace(success=False,status_message='x'),lambda:order.append('pause'),lambda:order.append('unpause'))
  self.assertEqual(order,['pause','unpause'])
 def test_reset_robot_order_landing_then_replacement_then_vio(self):
  tree=ast.parse((ROOT/'scripts/task4_env.py').read_text())
  fn=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='reset_robot'][0];order=[]
  for n in ast.walk(fn):
   if isinstance(n,ast.Call):
    f=n.func;name=f.attr if isinstance(f,ast.Attribute) else getattr(f,'id',None)
    if name=='_call' and n.args and isinstance(n.args[0],ast.Constant):name='_call:'+n.args[0].value
    if name in ('_zero_wheels','_begin','oldreset','_replace_base','_call:initialize'):order.append((n.lineno,n.col_offset,name))
  self.assertEqual([x[2] for x in sorted(order)],['_zero_wheels','_begin','oldreset','_replace_base','_call:initialize'])
