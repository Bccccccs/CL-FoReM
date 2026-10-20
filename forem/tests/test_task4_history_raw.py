import ast,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import task4_history_raw as h

class HistoryCapture(unittest.TestCase):
 def test_fixture_is_original_seed0_76_unmodified(self):
  root=Path(__file__).resolve().parents[1];p=root/'config/task4/quality_action_replay.json';before=p.read_bytes();a=h.load_fixture(p)
  self.assertEqual(a,json.loads(before)['actions']);self.assertEqual(len(a),76);self.assertEqual(p.read_bytes(),before)
 def test_fixture_rejects_other_seed_or_malformed(self):
  import tempfile
  for bad in ({'initial_seed':1,'actions':[[0,0,0]]*76},{'initial_seed':0,'actions':[[0,0,0]]*75},{'initial_seed':0,'actions':[[0,0,2]]*76},{'initial_seed':0,'actions':[[0,0,float('nan')]]*76}):
   with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f:f.write(json.dumps(bad));name=f.name
   with self.assertRaises(ValueError):h.load_fixture(name)
 def test_actions_stop_on_done_or_failed_call_and_denominators_remain(self):
  class Env:
   def __init__(self,done=None,fail=None):self.calls=[];self.done=done;self.fail=fail
   def step(self,a):
    self.calls.append(a)
    if len(self.calls)==self.fail:raise RuntimeError('lost estimate')
    return None,0,len(self.calls)==self.done,{}
  for done,fail,count in [(None,None,76),(5,None,5),(None,3,3)]:
   env=Env(done,fail);rows=[];r=h.execute_actions(env,[[0,0,0]]*76,lambda:1.5,lambda:0,450,rows.append,episode=4)
   self.assertEqual(len(env.calls),count);self.assertEqual(len(rows),count);self.assertEqual(r['unattempted_steps'],76-count);self.assertTrue(all(x['episode']==4 for x in rows))
   self.assertEqual(r['error'] is not None,fail is not None);self.assertEqual(r['training_updates'],0)
 def test_wall_deadline_stops_before_next_action(self):
  class Env:
   calls=0
   def step(self,a):Env.calls+=1;return None,0,False,{}
  rows=[];r=h.execute_actions(Env(),[[0,0,0]]*76,lambda:0,lambda:451,450,rows.append,episode=0)
  self.assertEqual(Env.calls,0);self.assertEqual(r['error'],'body_wall_cap')
 def test_guard_limits_equal_boundary(self):
  self.assertIsNone(h.limit_reason(499,399,12*1024**3-1));self.assertEqual(h.limit_reason(500,0,0),'whole_wall_cap');self.assertEqual(h.limit_reason(0,400,0),'raw_sim_cap');self.assertEqual(h.limit_reason(0,0,12*1024**3),'disk_cap')
 def test_no_new_episode_when_remaining_wall_below_one_episode(self):
  self.assertTrue(h.may_start_episode(0,300));self.assertFalse(h.may_start_episode(12,0));self.assertFalse(h.may_start_episode(3,381));self.assertTrue(h.may_start_episode(3,380))
 def test_actor_no_truth_subscribers_and_recorder_separate(self):
  tree=ast.parse((Path(__file__).resolve().parents[1]/'scripts/task4_history_raw.py').read_text())
  calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='Subscriber']
  self.assertTrue(calls);self.assertTrue(all(n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='/clock' for n in calls))
  for topic in ('/ground_truth/state','/task4/imu/data_raw','/task4/plugin/imu','/ov_msckf/poseimu','/task4/stereo/left/image_raw','/gazebo/link_states'):self.assertIn(topic,h.RECORD_TOPICS)
 def test_zero_wheels_wrapper_runs_before_original_reset_and_passes_arguments(self):
  order=[]
  class Robot:
   def reset(self,base,joints,close_gripper=False):order.append(('reset',base,joints,close_gripper));return 'obs'
  r=Robot();log=[]
  h.wrap_reset_zero_wheels(r,lambda:(order.append(('zero',)),{'success':True})[1],log)
  self.assertEqual(r.reset([1,2,3],{'a':1},True),'obs')
  self.assertEqual(order,[('zero',),('reset',[1,2,3],{'a':1},True)]);self.assertEqual(log,[{'success':True}])
  self.assertEqual(h.WHEEL_JOINTS,('front_left_wheel','front_right_wheel','rear_left_wheel','rear_right_wheel'))
 def test_identity_includes_actual_diagnostic_file(self):
  from task4_identity import RUNTIME_FILES
  self.assertIn('task4_history_raw.py',RUNTIME_FILES)
if __name__=='__main__':unittest.main()
