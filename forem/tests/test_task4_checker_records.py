import sys,json,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_task4_localization import json_native,dump
class Records(unittest.TestCase):
 def test_actual_numpy_info_preserves_booleans_numbers_arrays(self):
  self.assertEqual(json.loads(dump({'done':np.bool_(True),'n':np.int64(2),'a':np.asarray([.1,.2])})),{'done':True,'n':2,'a':[.1,.2]})
 def test_nonfinite_and_unknown_are_not_stringified(self):
  self.assertRaises(ValueError,dump,{'value':float('nan')});self.assertRaises(TypeError,dump,{'value':object()})
 def test_faults_zero_steps_are_not_task_success(self):
  from check_task4_localization import summarize_online
  s=summarize_online([],[],None,False,1.,{'ok':True})
  self.assertTrue(s['ok']);self.assertFalse(s['done']);self.assertFalse(s['task_attempted']);self.assertIsNone(s['success']);self.assertTrue(s['lifecycle_tests_passed'])
