"""Formal campaign r2 changes (SRC0153): bounded training redraw on VIO-init failure, training-only init timeout,
throttled disk scans, freeze-derived ledger path with explicit budget authorization."""
import ast,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path[:0]=[str(HERE/'scripts')]

class DiskMeterTests(unittest.TestCase):
 def test_full_scan_at_most_once_per_interval_per_path(self):
  from task4_resources import DiskMeter
  t=[0.0];calls=[]
  m=DiskMeter(30,clock=lambda:t[0],scanner=lambda p:(calls.append(p),len(calls))[1])
  self.assertEqual(m.measure('a'),1);t[0]=29.9;self.assertEqual(m.measure('a'),1);self.assertEqual(calls,['a'])
  self.assertEqual(m.measure('b'),2);t[0]=30.0;self.assertEqual(m.measure('a'),3);self.assertEqual(calls,['a','b','a'])

class RedrawTests(unittest.TestCase):
 def setUp(self):
  import task4_formal_entry as E;self.E=E
 def run_case(self,outcomes,cap=5):
  draws=iter(range(100,200));log=[];calls=[]
  def attempt(inst):
   calls.append(inst);o=outcomes.pop(0)
   if o:raise o
   return 'state'
  r=self.E.reset_with_redraw(lambda:next(draws),attempt,lambda inst,err:log.append((inst,err)),cap)
  return r,calls,log
 def test_init_timeout_redraws_and_logs(self):
  t=RuntimeError('raw VIO initialization timeout')
  r,calls,log=self.run_case([t,t,None])
  self.assertEqual((r,calls),('state',[100,101,102]));self.assertEqual([l[0] for l in log],[100,101])
 def test_other_errors_are_not_redrawn(self):
  # r3 (SRC0155) deliberately also redraws 'localization invalid' at reset; other errors still propagate.
  with self.assertRaises(RuntimeError):self.run_case([RuntimeError('nonfinite transition')])
 def test_redraw_cap_is_finite(self):
  t=RuntimeError('raw VIO initialization timeout')
  with self.assertRaises(RuntimeError):self.run_case([t]*6,cap=5)
  r,calls,_=self.run_case([t]*5+[None],cap=5);self.assertEqual(len(calls),6)

class LedgerPathTests(unittest.TestCase):
 def test_new_freeze_needs_authorization_and_gets_own_ledger(self):
  import task4_formal_entry as E
  with self.assertRaises(ValueError):E.ledger_rel({'freeze_id':'x'})
  self.assertEqual(E.ledger_rel({'freeze_id':'t4.4-freeze-20261008-2','budget_authorization':'SRC-0153'}),'results/task4/formal_campaign/t4.4-freeze-20261008-2/ledger.json')
  with self.assertRaises(ValueError):E.ledger_rel({'freeze_id':'../x','budget_authorization':'SRC-0153'})

class TimeoutTests(unittest.TestCase):
 def test_await_ready_uses_instance_timeout_default_120(self):
  src=(HERE/'scripts/task4_env.py').read_text();tree=ast.parse(src)
  fn=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_await_ready'][0];seg=ast.get_source_segment(src,fn)
  self.assertIn("getattr(self,'init_timeout_wall_s',120)",seg);self.assertNotIn('<120',seg)
 def test_config_training_only_timeout_and_cap(self):
  c=json.loads((HERE/'config/task4/sac_baseline.json').read_text())
  self.assertEqual(c['training_init_timeout_wall_s'],30);self.assertEqual(c['training_vio_init_redraws_cap'],5)
if __name__=='__main__':unittest.main()
