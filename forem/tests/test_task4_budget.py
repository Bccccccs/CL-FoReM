import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from task4_budget import validate_budget,assert_formal_ready
class Budget(unittest.TestCase):
 def setUp(self):self.cfg=json.loads((Path(__file__).resolve().parents[1]/'config/task4/sac_baseline.json').read_text())
 def test_real_failure_blocks_formal(self):
  with self.assertRaises(ValueError):assert_formal_ready(self.cfg,{'quality_passed':False,'parent_accepted':False,'formal_runner_complete':False})
 def test_unknown_budget_blocks(self):
  self.cfg['disk_all_cap_gib']=None
  with self.assertRaises(ValueError):validate_budget(self.cfg)
 def test_whole_instance_leakage_blocks(self):
  self.cfg['test_instance_seeds']=[101]
  with self.assertRaises(ValueError):validate_budget(self.cfg)
 def test_infinite_budget_blocks(self):
  self.cfg['steps_per_seed']=float('inf')
  with self.assertRaises(ValueError):validate_budget(self.cfg)
 def test_all_limits_present(self):validate_budget(self.cfg)
if __name__=='__main__':unittest.main()
