import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import task4_instances as production
class QualityCommands(unittest.TestCase):
 def run_steps(self,env,actions=None,initialized=True):
  self.assertTrue(hasattr(production,'run_quality_steps'),'fixed measurement loop missing')
  rows=[]
  result=production.run_quality_steps(env,actions,initialized,lambda:1.,lambda:0.,100.,rows.append)
  return result,rows
 def env(self,done_at=None,fail_at=None):
  class Env:
   calls=[]
   def step(self,a):
    self.calls.append(a)
    if fail_at==len(self.calls):raise RuntimeError('localization lost')
    return None,-1.,done_at==len(self.calls),{'success':False}
  return Env()
 def test_no_actions_before_successful_reset(self):
  e=self.env()
  self.assertTrue(hasattr(production,'run_quality_steps'),'fixed measurement loop missing')
  with self.assertRaises(ValueError):self.run_steps(e,[[0,0,0]]*76,False)
  self.assertEqual(e.calls,[])
 def test_fixed76_complete_does_not_invent_task_done(self):
  e=self.env();r,rows=self.run_steps(e,[[.1,0,0]]*76)
  self.assertEqual(len(e.calls),76);self.assertTrue(r['measurement_complete']);self.assertFalse(r['done']);self.assertEqual(len(rows),76)
 def test_original_done_stops_commands_and_keeps_incomplete_denominator(self):
  e=self.env(done_at=3);r,rows=self.run_steps(e,[[.1,0,0]]*76)
  self.assertEqual(len(e.calls),3);self.assertTrue(r['done']);self.assertFalse(r['measurement_complete']);self.assertEqual(r['unattempted_steps'],73)
 def test_failed_action_is_persisted_and_ends_loop(self):
  e=self.env(fail_at=2);r,rows=self.run_steps(e,[[.1,0,0]]*76)
  self.assertEqual(len(e.calls),2);self.assertEqual(len(rows),2);self.assertTrue(rows[-1]['attempted']);self.assertIn('error',rows[-1]);self.assertFalse(r['measurement_complete']);self.assertEqual(r['unattempted_steps'],74)
 def test_zero_diagnostic_requires_original_done(self):
  e=self.env(done_at=4);r,rows=self.run_steps(e)
  self.assertEqual(len(rows),4);self.assertTrue(r['measurement_complete']);self.assertTrue(r['done'])
 def test_nonfinite_and_out_of_bounds_commands_refused_before_action(self):
  for action in ([float('nan'),0,0],[1.01,0,0]):
   e=self.env()
   self.assertTrue(hasattr(production,'run_quality_steps'),'fixed measurement loop missing')
   with self.assertRaises(ValueError):self.run_steps(e,[action]*76)
   self.assertEqual(e.calls,[])
