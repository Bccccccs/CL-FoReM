import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(HERE/'scripts')]
from task4_formal_gate import choose_checkpoint,full_denominator,performance_gate
CFG=json.loads((HERE/'config/task4/sac_baseline.json').read_text())
CRITERION={'metric':'confirmed_success_per_seed','minimum_confirmed_success_per_seed':1,'declared_before_formal_test':True,'source_id':'SRC-0108',
'require_all_requested_test_episodes_attempted':True,'require_all_requested_test_episodes_initialized':True,'require_all_requested_test_episodes_completed':True,'require_all_requested_test_episodes_complete_physical_feedback':True,'physical_success_contract':{'position_distance_lt_m':.025,'rotation_metric':'1-dot(q)^2','rotation_distance_lt_dimensionless':.05,'nr_kin_failures':0,'nr_base_collisions':0,'requires_original_done_and_internal_success':True}}

def episode(seed,instance,success=False,phase='test'):
 return {'seed':seed,'instance':instance,'phase':phase,'attempted_episode':True,'initialized':True,'completed':True,'all_actual_feedback_valid':True,'status':'completed','original_internal_success':success,'actual_task_success':success,'confirmed_success':success,'return':-10.0}

class PredefinedPerformanceRiskTests(unittest.TestCase):
 def setUp(self):
  self.cfg=copy.deepcopy(CFG);self.cfg['actual_task_acceptance']=copy.deepcopy(CRITERION)
  self.rows=[episode(s,i,i==106) for s in self.cfg['training_seeds'] for i in self.cfg['test_instance_seeds']]
 def test_zero_success_complete_negative_return_beats_no_init_zero_return(self):
  candidates={'early-no-init':{'steps':5000},'late-valid':{'steps':10000}}
  rows={'early-no-init':[dict(episode(0,i,phase='validation'),attempted_episode=True,initialized=False,completed=False,all_actual_feedback_valid=False,status='failed',**{'return':0.0}) for i in range(101,106)],
        'late-valid':[episode(0,i,phase='validation') for i in range(101,106)]}
  self.assertEqual(choose_checkpoint(candidates,rows,list(range(101,106))),'late-valid')
 def test_all_fifteen_valid_with_each_seed_one_physical_success_pass(self):
  r=full_denominator(self.cfg,self.rows)
  self.assertTrue(r['performance_accepted']);self.assertEqual(r['test_success_count'],3)
 def test_every_episode_requires_attempt_init_complete_and_feedback(self):
  for key in ('attempted_episode','initialized','completed','all_actual_feedback_valid'):
   rows=copy.deepcopy(self.rows);rows[-1][key]=False
   with self.subTest(key=key):self.assertFalse(full_denominator(self.cfg,rows)['performance_accepted'])
 def test_missing_request_or_missing_all_records_cannot_pass(self):
  self.assertFalse(full_denominator(self.cfg,self.rows[:-1])['performance_accepted'])
  r=full_denominator(self.cfg,[]);self.assertFalse(r['performance_accepted']);self.assertEqual(r['unattempted_test_failures'],15)
 def test_no_success_in_one_seed_or_inconsistent_physical_marker_cannot_pass(self):
  rows=copy.deepcopy(self.rows)
  for r in rows:
   if r['seed']==2:r['confirmed_success']=False
  self.assertFalse(full_denominator(self.cfg,rows)['performance_accepted'])
  for key in ('actual_task_success','original_internal_success'):
   rows=copy.deepcopy(self.rows);rows[0][key]=False
   with self.subTest(key=key):self.assertFalse(full_denominator(self.cfg,rows)['performance_accepted'])
 def test_unfrozen_all_episode_requirements_or_changed_minimum_refuse_gate(self):
  for key,value in [('require_all_requested_test_episodes_attempted',False),('require_all_requested_test_episodes_initialized',None),('require_all_requested_test_episodes_completed',False),('require_all_requested_test_episodes_complete_physical_feedback',False),('minimum_confirmed_success_per_seed',2)]:
   cfg=copy.deepcopy(self.cfg);cfg['actual_task_acceptance'][key]=value
   with self.subTest(key=key):
    with self.assertRaises(ValueError):performance_gate(cfg)
 def test_relaxed_physical_threshold_or_wrong_rotation_units_refuse_gate(self):
  for key,value in [('position_distance_lt_m',.1),('rotation_metric','yaw_rad'),('nr_kin_failures',1),('requires_original_done_and_internal_success',False)]:
   cfg=copy.deepcopy(self.cfg);cfg['actual_task_acceptance']['physical_success_contract'][key]=value
   with self.subTest(key=key):
    with self.assertRaises(ValueError):performance_gate(cfg)
if __name__=='__main__':unittest.main()
