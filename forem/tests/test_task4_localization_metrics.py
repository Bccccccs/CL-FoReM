import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_task4_localization import evaluate_rows,actual_success,public_instance
class Metrics(unittest.TestCase):
 def test_missing_pose_counted_failure(self):
  r=evaluate_rows([],[],[{'stamp':1},{'stamp':2}],.02)
  self.assertEqual(r['attempted_control_steps'],2);self.assertEqual(r['valid_control_fraction'],0)
 def test_timestamp_mismatch_invalid(self):
  p=[{'stamp':1,'p':[0,0,0],'q':[0,0,0,1]}]
  r=evaluate_rows(p,[(1.1,[0,0,0,0,0,0,1])],[{'stamp':1}],.02)
  self.assertEqual(r['matched'],0)
 def test_localization_error_fixed_frame(self):
  p=[{'stamp':1,'p':[1,0,.05],'q':[0,0,0,1]},{'stamp':2,'p':[2,0,.05],'q':[0,0,0,1]}]
  r=evaluate_rows(p,[(1,[0,0,0,0,0,0,1]),(2,[0,0,0,0,0,0,1])],[{'stamp':1},{'stamp':2}],.02)
  self.assertGreater(r['XY_RMSE_m'],1.5)
 def test_estimated_goal_not_true_success(self):
  self.assertFalse(actual_success([1,0,0,0,0,0,1],[0,0,0,0,0,0,1],0,0)['success'])
 def test_original_task_quaternion_distance_units(self):
  import math
  q=[0,0,math.sin(.3/2),math.cos(.3/2)]
  self.assertTrue(actual_success([0,0,0]+q,[0,0,0,0,0,0,1],0,0)['success'])
 def test_invalid_physical_feedback(self):
  for q in ([0,0,0,2],[0,0,0,float('nan')]):
   self.assertFalse(actual_success([0,0,0]+q,[0,0,0,0,0,0,1],0,0)['valid'])
 def test_nonfinite_pose_counted_invalid(self):
  r=evaluate_rows([{'stamp':1,'p':[float('nan'),0,0],'q':[0,0,0,1]}],[(1,[0,0,0,0,0,0,1])],[{'stamp':1}])
  self.assertEqual(r['matched'],0);self.assertEqual(r['invalid_control_steps'],1)
 def test_public_spec_only_feedback_removed(self):
  a={'seed':101,'base_tf':[0]*7,'hash':'old','goal_tip':[1],'goal_wrist':[2],'arm_joints_planned':[3],'map_size_m':[4],'obstacles':[5]};b=dict(a,base_tf=[1]*7,hash='new')
  self.assertEqual(public_instance(a),public_instance(b));b['goal_tip']=[9];self.assertNotEqual(public_instance(a),public_instance(b))
if __name__=='__main__':unittest.main()
