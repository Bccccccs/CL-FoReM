import sys,unittest,json,tempfile,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import task4_instances as production
class SealRepresentation(unittest.TestCase):
 def fixtures(self):
  root=Path(__file__).resolve().parents[1]
  legacy=json.loads((root/'results/task3/t3.5-inst-r1/episode_instances.json').read_text())['episodes']['106']
  first={k:copy.deepcopy(legacy[k]) for k in ('arm_joints_planned','goal_tip','goal_wrist','map_size_m')}
  first.update(initial_base_pose_xyzw=legacy['base_tf'][:3]+[-v for v in legacy['base_tf'][3:]],initial_base_command=[1,2,0,0,0,4.6],schema=4)
  return first,legacy
 def compare(self,first,legacy):
  self.assertTrue(hasattr(production,'legacy_public_checks'),'sign-equivalent public comparison missing')
  return production.legacy_public_checks(first,legacy)
 def test_historical106_overall_sign_equivalent_accepted_exactly(self):
  a,b=self.fixtures();self.assertTrue(all(self.compare(a,b).values()))
 def test_original_quaternion_also_accepted(self):
  a,b=self.fixtures();a['initial_base_pose_xyzw']=list(b['base_tf']);self.assertTrue(all(self.compare(a,b).values()))
 def test_xy_one_6dp_unit_change_rejected(self):
  a,b=self.fixtures();a['initial_base_pose_xyzw'][0]+=0.000001;self.assertFalse(all(self.compare(a,b).values()))
 def test_real_rotation_one_6dp_unit_change_rejected(self):
  a,b=self.fixtures();a['initial_base_pose_xyzw'][5]+=0.000001;self.assertFalse(all(self.compare(a,b).values()))
 def test_single_component_flip_rejected(self):
  a,b=self.fixtures();a['initial_base_pose_xyzw'][5]*=-1;self.assertFalse(all(self.compare(a,b).values()))
 def test_failed_actual_input_persisted_before_rejection(self):
  a,b=self.fixtures();a['initial_base_pose_xyzw'][0]+=0.000001
  self.assertTrue(hasattr(production,'persist_capture_evidence'),'failed input persistence missing')
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'capture.json';rng={'map':'x'};command=[1,2,.05,0,0,0,1]
   production.persist_capture_evidence(path,a,a,command,rng,rng,rng,b,None)
   with self.assertRaises(ValueError):
    if not all(self.compare(a,b).values()):raise ValueError('public mismatch')
   actual=json.loads(path.read_text());self.assertEqual(actual['first'],a);self.assertEqual(actual['commanded_initial'],command);self.assertEqual(actual['capture_rng_before'],rng);self.assertEqual(actual['expected_legacy'],b);self.assertFalse(all(actual['legacy_reliable_fields'].values()))

class CollectorFailureEvidence(unittest.TestCase):
 def test_actual_collector_failure_leaves_full_capture(self):
  import ast,os,pickle,types,argparse,time,traceback,hashlib
  root=Path(__file__).resolve().parents[1];source=Path(os.environ.get('TASK4_COLLECTOR_TEST_SOURCE',str(root/'scripts/collect_task4_instances.py')))
  module=ast.parse(source.read_text());tree=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef)],type_ignores=[])
  legacy=json.loads((root/'results/task3/t3.5-inst-r1/episode_instances.json').read_text())['episodes']['101'];first={k:copy.deepcopy(legacy[k]) for k in ('arm_joints_planned','goal_tip','goal_wrist','map_size_m')}
  first.update(schema=4,initial_base_pose_xyzw=list(legacy['base_tf']),obstacles=[],spawn_commands=[]);first['initial_base_pose_xyzw'][0]+=0.000001
  rng=types.SimpleNamespace(get_state=lambda:(1,2,3));m=types.SimpleNamespace(np_random=rng)
  class Env:
   unwrapped_env=types.SimpleNamespace(map=m,_robot=m,np_random=rng);_spawn_sdf_xml={}
   def __init__(self,seed):pass
   def reset(self,**kw):pass
   def _capture_spec(self,seed):return copy.deepcopy(first)
   def close(self):pass
  with tempfile.TemporaryDirectory() as d:
   ns=dict(argparse=argparse,hashlib=hashlib,json=json,os=os,pickle=pickle,time=time,subprocess=None,signal=None,traceback=traceback,Path=Path,Task4Env=Env,verify_runtime=lambda:None,semantic_identity=lambda:{},rospy=types.SimpleNamespace(init_node=lambda *a,**k:None,get_param=lambda *a:[1,2,.05,0,0,0,1]),**{k:getattr(production,k) for k in ('public_instance','verify_spawn','run_quality_steps','legacy_public_checks','persist_capture_evidence','verify_public_instance')})
   ns['verify_spawn']=lambda _:True # isolating public comparison from ROS spawn service, which this unit does not run
   exec(compile(tree,str(source),'exec'),ns);previous=os.getcwd();argv=sys.argv;oldenv=os.environ.get('FOREM_RES_DIR')
   try:
    os.chdir(root);sys.argv=['collect','--passes','1'];os.environ['FOREM_RES_DIR']=d;self.assertEqual(ns['main'](),1)
   finally:
    os.chdir(previous);sys.argv=argv
    if oldenv is None:os.environ.pop('FOREM_RES_DIR',None)
    else:os.environ['FOREM_RES_DIR']=oldenv
   capture=Path(d)/'capture-seed101-pass0.json';self.assertTrue(capture.exists(),'production collector lost failed input before throw');actual=json.loads(capture.read_text());self.assertEqual(actual['first'],first);self.assertFalse(all(actual['legacy_reliable_fields'].values()));self.assertEqual(actual['capture_rng_before'],actual['capture_rng_after'])
