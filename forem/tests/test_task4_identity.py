import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from task4_identity import semantic_identity,assert_checkpoint_identity
class IdentityTests(unittest.TestCase):
 def test_actual_runtime_and_old_checkpoint(self):
  root=Path(__file__).resolve().parents[1];i=semantic_identity(root)
  self.assertIn('runtime:task4_identity.py',i['groups']);self.assertIn('src/open_vins',i['groups']);self.assertIn('src/forem_localization',i['groups']);self.assertIn('binary:ov_msckf/run_subscribe_msckf',i['groups'])
  self.assertRaises(ValueError,assert_checkpoint_identity,{'task_namespace':'task3','semantic_identity':i},i)
  assert_checkpoint_identity({'task_namespace':'task4_openvins_stereo_imu','semantic_identity':i},i)
  wrong=dict(i);wrong['pose_source']='gazebo_reference';self.assertRaises(ValueError,assert_checkpoint_identity,{'task_namespace':'task4_openvins_stereo_imu','semantic_identity':wrong},i)
 def test_real_helper_mutation_changes_identity(self):
  import shutil
  root=Path(__file__).resolve().parents[1]
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);(r/'scripts').mkdir()
   shutil.copyfile(root/'scripts/check_task4_sensors.py',r/'scripts/check_task4_sensors.py')
   before=semantic_identity(r);(r/'scripts/check_task4_sensors.py').write_text((r/'scripts/check_task4_sensors.py').read_text()+'\n# real raw gate mutation\n')
   after=semantic_identity(r);self.assertNotEqual(before,after)
if __name__=='__main__':unittest.main()
