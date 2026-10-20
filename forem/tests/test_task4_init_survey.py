import ast,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import task4_init_survey as s

class InitSurvey(unittest.TestCase):
 def test_instances_only_training_range_unique_and_bounded(self):
  self.assertEqual(s.parse_instances('0-29'),list(range(30)))
  for bad in ('0-100','-1-3','5-2','0-60'):
   with self.assertRaises(ValueError):s.parse_instances(bad)
 def test_no_new_instance_after_wall_gate(self):
  self.assertTrue(s.may_start(0));self.assertTrue(s.may_start(s.WHOLE_CAP-s.WORST_INSTANCE_S));self.assertFalse(s.may_start(s.WHOLE_CAP-s.WORST_INSTANCE_S+1))
 def test_failure_recorded_and_survey_continues(self):
  class Env:
   def __init__(self):self.calls=[]
   def reset(self,seed):
    self.calls.append(seed)
    if seed==1:raise RuntimeError('raw VIO initialization timeout')
    return None
  env=Env();rows=[];s.survey(env,[0,1,2],lambda:0.0,lambda:0.0,rows.append,lambda inst,status:None)
  self.assertEqual(env.calls,[0,1,2]);self.assertEqual([r['initialized'] for r in rows],[True,False,True]);self.assertIn('timeout',rows[1]['error'])
 def test_actor_subscribes_only_clock_and_raw_images_no_truth_no_actions(self):
  tree=ast.parse((Path(__file__).resolve().parents[1]/'scripts/task4_init_survey.py').read_text())
  subs=[n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='Subscriber']
  self.assertEqual(sorted(set(subs)),['/clock','/task4/stereo/left/image_raw','/task4/stereo/right/image_raw'])
  self.assertFalse([n for n in ast.walk(tree) if isinstance(n,ast.Attribute) and n.attr=='step'])
 def test_identity_includes_survey(self):
  from task4_identity import RUNTIME_FILES
  self.assertIn('task4_init_survey.py',RUNTIME_FILES)
if __name__=='__main__':unittest.main()
