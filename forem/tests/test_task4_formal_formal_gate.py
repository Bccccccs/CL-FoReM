import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(HERE/'scripts')]
from task4_resources import digest,atomic_write
try:
    from task4_formal_gate import guard, full_denominator, choose_checkpoint, registered_checkpoint, reject_training_resume
except ImportError:
    guard=full_denominator=choose_checkpoint=registered_checkpoint=reject_training_resume=None

class FormalGateRiskTests(unittest.TestCase):
    def test_gate_api_exists(self):
        self.assertTrue(callable(guard),'formal gate missing')
    def test_missing_actual_freeze_and_performance_gate_refuse_before_importing_ros(self):
        if guard is None:self.fail('formal gate missing')
        # Hermetic (task4.5 r2): live budget/config copied into a temp root WITHOUT execution_freeze.json.
        import shutil
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'config/task4').mkdir(parents=True)
            shutil.copy(HERE/'config/task4/sac_baseline.json',root/'config/task4/sac_baseline.json')
            with self.assertRaisesRegex(ValueError,'disabled|freeze|acceptance'):
                guard(root,'not-existing-parent-acceptance.json',actual_identity={'groups':{}},host=False)
    def test_missing_episodes_remain_in_fixed_denominator(self):
        if full_denominator is None:self.fail('fixed denominator missing')
        cfg=json.loads((HERE/'config/task4/sac_baseline.json').read_text())
        rows=[{'seed':0,'instance':106,'confirmed_success':True,'completed':True,'all_actual_feedback_valid':True,'attempted_episode':True,'initialized':True,'status':'completed','actual_task_success':True,'original_internal_success':True}]
        r=full_denominator(cfg,rows)
        self.assertEqual(r['requested_test_episodes'],15)
        self.assertEqual(r['unattempted_test_failures'],14)
        self.assertEqual(r['test_success_rate'],1/15)
        self.assertFalse(r['performance_accepted'])
    def test_selection_uses_validation_only_fixed_denominator_tie_schedule(self):
        if choose_checkpoint is None:self.fail('immutable selection missing')
        candidates={'step5000':{'steps':5000},'step10000':{'steps':10000}}
        rows={p:[{'instance':i,'confirmed_success':False,'return':0.0} for i in range(101,106)] for p in candidates}
        self.assertEqual(choose_checkpoint(candidates,rows,[101,102,103,104,105]),'step5000')
        rows['step10000'][0]['phase']='test'
        with self.assertRaises(ValueError):choose_checkpoint(candidates,rows,[101,102,103,104,105])
    def test_unregistered_or_failed_attempt_checkpoint_refused_before_load(self):
        if registered_checkpoint is None:self.fail('formal registry check missing')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'checkpoint.pt';p.write_bytes(b'actual checkpoint')
            ledger={'freeze_id':'A','checkpoints':{},'jobs':[]}
            with self.assertRaises(ValueError):registered_checkpoint(p,ledger,0)
    def test_inference_only_checkpoint_training_resume_refused(self):
        if reject_training_resume is None:self.fail('resume guard missing')
        with self.assertRaisesRegex(ValueError,'unsupported'):
            reject_training_resume({'policy_state_dict':{},'task4_state':{}})

if __name__=='__main__':unittest.main()

class SourceReceiptRiskTests(unittest.TestCase):
 def setUp(self):
  if guard is None:self.fail('formal gate missing')
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);p=self.root/'config/task4';p.mkdir(parents=True)
  self.cfg=json.loads((HERE/'config/task4/sac_baseline.json').read_text());self.cfg['enabled']=True
  from task4_formal_gate import SELECTION_RULE,PHYSICAL_SUCCESS_CONTRACT
  self.cfg['checkpoint_selection_rule']=SELECTION_RULE
  self.cfg['actual_task_acceptance']={'metric':'confirmed_success_per_seed','minimum_confirmed_success_per_seed':1,'declared_before_formal_test':True,'source_id':'synthetic-test-only','physical_success_contract':copy.deepcopy(PHYSICAL_SUCCESS_CONTRACT),
   'require_all_requested_test_episodes_attempted':True,'require_all_requested_test_episodes_initialized':True,'require_all_requested_test_episodes_completed':True,'require_all_requested_test_episodes_complete_physical_feedback':True}
  atomic_write(p/'sac_baseline.json',self.cfg)
  from task4_formal_gate import FORMAL_RUNTIME_FILES,sha_file
  self.identity={'schema':4,'namespace':'task4_openvins_stereo_imu','pose_source':'openvins_stereo_imu','groups':{'runtime:'+f:{'files':1,'sha256':'a'*64} for f in FORMAL_RUNTIME_FILES}}
  self.identity['groups']['ros:ur_description']={'files':1,'sha256':'b'*64}
  self.identity['groups']['inherited_binary:pybindings.test.so']={'files':1,'sha256':'c'*64}
  spec={'schema':4,'obstacles':[{'name':'obstacle','frame':'world','pose':[0,0,0,0,0,0,1]}],'spawn_commands':[{'name':'obstacle','frame':'world','pose':[0,0,0,0,0,0,1],'sdf_sha256':'a'*64}]}
  atomic_write(p/'sealed_instances.json',{'true_spawn_seals_complete':True,'episodes':{str(i):spec for i in range(101,111)}})
  evidence={}
  for k in ('quality','sealed_instances','runtime_guard_tests'):
   q=self.root/(k+'.json');atomic_write(q,{'synthetic_fixture_only':True});evidence[k]={'path':q.name,'sha256':sha_file(q)}
  self.freeze={'freeze_id':'synthetic-only','quality_passed':True,'public_instances_passed':True,'formal_runner_complete':True,'budget_sha256':sha_file(p/'sac_baseline.json'),'seals_sha256':sha_file(p/'sealed_instances.json'),'evidence':evidence,'required_identity_groups':list(self.identity['groups']),'semantic_identity':self.identity}
  atomic_write(p/'execution_freeze.json',self.freeze)
  self.acceptance=self.root/'acceptance.json'
  atomic_write(self.acceptance,{'accepted':True,'task_id':'task4.4','freeze_id':'synthetic-only','freeze_sha256':sha_file(p/'execution_freeze.json'),'semantic_identity':self.identity})
 def tearDown(self):self.temp.cleanup()
 def test_matching_synthetic_receipts_pass_without_runtime_import(self):
  cfg,freeze=guard(self.root,self.acceptance,actual_identity=self.identity)
  self.assertTrue(cfg['enabled']);self.assertEqual(freeze['freeze_id'],'synthetic-only')
 def test_each_helper_binary_missing_or_changed_refuses(self):
  for k in self.identity['groups']:
   for mutation in ('absent',{'files':1,'sha256':'d'*64}):
    actual=copy.deepcopy(self.identity);actual['groups'][k]=mutation
    with self.subTest(group=k,mutation=mutation):
     with self.assertRaises(ValueError):guard(self.root,self.acceptance,actual_identity=actual)
 def test_host_ros_absence_requires_separate_container_check(self):
  host=copy.deepcopy(self.identity);host['groups']['ros:ur_description']='absent'
  guard(self.root,self.acceptance,actual_identity=host,host=True)
  with self.assertRaises(ValueError):guard(self.root,self.acceptance,actual_identity=host,host=False)
 def test_parent_receipt_hash_tampering_refuses(self):
  a=json.loads(self.acceptance.read_text());a['freeze_sha256']='e'*64;atomic_write(self.acceptance,a)
  with self.assertRaisesRegex(ValueError,'parent acceptance'):guard(self.root,self.acceptance,actual_identity=self.identity)
 def test_missing_performance_acceptance_refuses_even_if_enabled(self):
  del self.cfg['actual_task_acceptance'];atomic_write(self.root/'config/task4/sac_baseline.json',self.cfg)
  with self.assertRaisesRegex(ValueError,'actual_task_acceptance'):guard(self.root,self.acceptance,actual_identity=self.identity)

class SelectionFailureRiskTests(unittest.TestCase):
 def test_partial_failed_episode_return_is_not_used_to_select(self):
  candidates={'early':{'steps':5000},'late':{'steps':10000}}
  rows={'early':[{'instance':101,'confirmed_success':False,'completed':True,'return':0.0}],
        'late':[{'instance':101,'confirmed_success':False,'completed':False,'return':100.0}]}
  self.assertEqual(choose_checkpoint(candidates,rows,[101]),'early')
