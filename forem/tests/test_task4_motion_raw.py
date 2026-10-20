import ast,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import task4_motion_raw as m

class MotionCapture(unittest.TestCase):
 def test_original_fixture_only_first28_and_no_mutation(self):
  root=Path(__file__).resolve().parents[1];p=root/'config/task4/quality_action_replay.json';before=p.read_bytes();a=m.load_prefix(p)
  self.assertEqual(a,json.loads(before)['actions'][:28]);self.assertEqual(p.read_bytes(),before);self.assertEqual(len(a),28)
 def test_cap28_done_and_failed_call_remain_denominators(self):
  class Env:
   def __init__(self,done=None,fail=None):self.calls=[];self.done=done;self.fail=fail
   def step(self,a):
    self.calls.append(a)
    if len(self.calls)==self.fail:raise RuntimeError('lost estimate')
    return None,0,len(self.calls)==self.done,{}
  for done,fail,count in [(None,None,28),(3,None,3),(None,2,2)]:
   env=Env(done,fail);rows=[];r=m.execute_prefix(env,[[0,0,0]]*28,lambda:12.345,lambda:0,450,rows.append)
   self.assertEqual(len(env.calls),count);self.assertEqual(len(rows),count);self.assertEqual(r['unattempted_steps'],28-count)
   self.assertTrue(all(x['stamp_before']==12.345 and x['stamp']==12.345 for x in rows))
   self.assertEqual(r['error'] is not None,fail is not None)
 def test_guard_wall_sim_disk_and_equal_boundary(self):
  self.assertIsNone(m.limit_reason(449,119,10*1024**3-1));self.assertEqual(m.limit_reason(450,0,0),'body_wall_cap');self.assertEqual(m.limit_reason(0,120,0),'raw_sim_cap');self.assertEqual(m.limit_reason(0,0,10*1024**3),'disk_cap')
 def test_header_preserved_and_payload_not_fabricated(self):
  class Stamp:
   def to_nsec(self):return 1234567890123
  class Header:stamp=Stamp();frame_id='original';seq=42
  class Msg:header=Header()
  self.assertEqual(m.header_metadata(Msg()),{'stamp_ns':1234567890123,'frame_id':'original','seq':42})
  self.assertEqual(Msg.header.frame_id,'original')
 def test_actor_no_truth_or_image_subscribers_and_recorder_separate(self):
  source=(Path(__file__).resolve().parents[1]/'scripts/task4_motion_raw.py').read_text();tree=ast.parse(source)
  calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='Subscriber']
  self.assertTrue(calls);self.assertTrue(all(n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='/clock' for n in calls))
  self.assertIn('/ground_truth/state',m.RECORD_TOPICS);self.assertIn('/ov_msckf/poseimu',m.RECORD_TOPICS);self.assertIn('/ov_msckf/trackhist',m.RECORD_TOPICS)
 def test_identity_includes_actual_diagnostic_file(self):
  from task4_identity import RUNTIME_FILES
  self.assertIn('task4_motion_raw.py',RUNTIME_FILES)
if __name__=='__main__':unittest.main()
