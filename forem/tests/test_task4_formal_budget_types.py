import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path[:0]=[str(HERE/'scripts')]
from task4_budget import validate_budget
CFG=json.loads((HERE/'config/task4/sac_baseline.json').read_text())
class BudgetTypeRiskTests(unittest.TestCase):
 def test_fractional_boolean_duplicate_and_zero_counts_refused(self):
  for key,value in [('steps_per_seed',1.5),('batch_size',True),('batch_size',0),('training_seeds',[0,0,1]),('test_instance_seeds',[106,106,107,108,109]),('checkpoint_schedule_steps',[5000,5000,20000]),('replay_capacity',256)]:
   cfg=copy.deepcopy(CFG);cfg[key]=value
   with self.subTest(key=key,value=value):
    with self.assertRaises(ValueError):validate_budget(cfg)
 def test_original_update_cap_matches_steps_minus_batch(self):
  cfg=copy.deepcopy(CFG);cfg['gradient_updates_per_seed_cap']=20000
  with self.assertRaises(ValueError):validate_budget(cfg)
 def test_all_cap_cannot_be_smaller_than_training_plus_eval(self):
  cfg=copy.deepcopy(CFG);cfg['all_wall_total_cap_s']=1
  with self.assertRaises(ValueError):validate_budget(cfg)
if __name__=='__main__':unittest.main()
