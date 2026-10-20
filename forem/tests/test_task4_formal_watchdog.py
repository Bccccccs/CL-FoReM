import copy,json,os,subprocess,sys,time,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(HERE/'scripts')]
from task0_proc import identity
try:
 from task4_budget_watchdog import violations, stop_owner
except ImportError:
 violations=stop_owner=None
CFG=json.loads((HERE/'config/task4/sac_baseline.json').read_text())
class WatchdogRiskTests(unittest.TestCase):
 def test_blocked_call_per_job_wall_is_detected_without_actor_cooperation(self):
  if violations is None:self.fail('independent watchdog missing')
  data={'spent_training_s':0,'spent_evaluation_s':0,'spent_all_s':0,'active':{'phase':'training','started_unix':0,'observed_s':0,'wall_cap_s':CFG['wall_time_cap_per_training_attempt_s']},'session':None}
  self.assertIn('per_job_wall',violations(CFG,data,{},CFG['wall_time_cap_per_training_attempt_s']+1))
 def test_no_active_job_does_not_disable_overall_session_budget(self):
  if violations is None:self.fail('independent watchdog missing')
  data={'spent_training_s':0,'spent_evaluation_s':0,'spent_all_s':CFG['all_wall_total_cap_s']-1,'active':None,'session':{'started_unix':0,'observed_s':0}}
  self.assertIn('all_wall',violations(CFG,data,{},2))
 def test_command_mutation_prevents_signal_to_same_pid(self):
  if stop_owner is None:self.fail('identity stop missing')
  p=subprocess.Popen([sys.executable,'-c','import time;print("ready",flush=True);time.sleep(30)'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:
   self.assertEqual(p.stdout.readline().strip(),'ready')
   owner=identity(p.pid);bad=copy.deepcopy(owner);bad['cmd']+=' changed'
   self.assertFalse(stop_owner(bad,grace_s=.03))
   self.assertIsNone(p.poll())
   self.assertTrue(stop_owner(owner,grace_s=.03));p.wait(timeout=2)
  finally:
   if p.poll() is None:p.kill();p.wait()
   p.stdout.close();p.stderr.close()
 def test_invalid_gpu_measurement_refuses_resource_monitoring(self):
  if violations is None:self.fail('independent watchdog missing')
  data={'spent_training_s':0,'spent_evaluation_s':0,'spent_all_s':0,'active':None,'session':None}
  self.assertIn('GPU_measurement_unavailable',violations(CFG,data,{'gpu_valid':False},0))
if __name__=='__main__':unittest.main()

class MonitorShutdownRiskTests(unittest.TestCase):
 def test_monitor_stops_before_session_record_is_cleared(self):
  from task4_formal_entry import Campaign
  p=subprocess.Popen([sys.executable,'-c','import time;print("ready",flush=True);time.sleep(30)'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:
   self.assertEqual(p.stdout.readline().strip(),'ready')
   class L:
    def close(ledger):
     if p.poll() is None:raise AssertionError('live watchdog can kill owner after cleared session')
   c=Campaign.__new__(Campaign);c.env=None;c.ledger=L();c.watchdog=p
   c.close()
  finally:
   if p.poll() is None:p.kill();p.wait()
   p.stdout.close();p.stderr.close()
