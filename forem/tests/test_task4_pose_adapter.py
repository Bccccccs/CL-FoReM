import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/forem_localization/scripts'))
from estimate_gate import EstimateGate, pose_matrix, transform_pose
class GateTests(unittest.TestCase):
 def test_no_truth_bootstrap_ready(self):
  g=EstimateGate();g.clock(10.);g.begin([0,0,.05,0,0,0,1]);self.assertFalse(g.ready());g.initialize(10.)
  self.assertRaises(ValueError,g.accept,9.99,'global',[0,0,0,0,0,0,1],np.eye(6))
  g.begin([0,0,.05,0,0,0,1]);g.initialize(10.);g.accept(10.,'global',[0,0,0,0,0,0,1],np.eye(6));self.assertTrue(g.ready());g.clock(10.101);self.assertFalse(g.ready());self.assertEqual(g.state,'INVALID_STOP')
 def test_reset_future_frame_nonfinite(self):
  for stamp,frame,pose in [(11.,'global',[0,0,0,0,0,0,1]),(10.,'wrong',[0,0,0,0,0,0,1]),(10.,'global',[float('nan'),0,0,0,0,0,1]),(10.,'global',[0,0,0,0,0,0,0])]:
   g=EstimateGate();g.clock(10);g.begin([0,0,.05,0,0,0,1]);g.initialize(10)
   self.assertRaises(ValueError,g.accept,stamp,frame,pose,np.eye(6));self.assertFalse(g.ready())
  g=EstimateGate();g.clock(10);g.begin([0,0,.05,0,0,0,1]);g.initialize(10);g.clock(0);self.assertEqual(g.state,'INVALID_STOP');self.assertRaises(ValueError,g.begin,[0,0,0,0,0,0,1])
 def test_alignment_lever_arm_yaw_covariance(self):
  g=EstimateGate();g.clock(10);g.begin([2,3,.05,0,0,0,1]);g.initialize(10)
  p,c=g.accept(10,'global',[0,0,0,0,0,0,1],np.eye(6));np.testing.assert_allclose(p,[2,3,.05,0,0,0,1],atol=1e-8)
  g.clock(10.05);p,c=g.accept(10.05,'global',[0,0,0,0,0,np.sqrt(.5),np.sqrt(.5)],np.eye(6));np.testing.assert_allclose(p[:3],[2.35,2.65,.05],atol=1e-8);self.assertGreater(c[0,0],1);self.assertTrue(np.isfinite(c).all())
 def test_unknown_epoch_no_clock_covariance(self):
  g=EstimateGate();self.assertRaises(ValueError,g.begin,[0,0,0,0,0,0,1]);self.assertRaises(ValueError,pose_matrix,[0,0,0,0,0,0,1e200])
 def test_finite_input_overflow_cannot_publish_nonfinite_transform(self):
  g=EstimateGate();g.clock(10);g.begin([1e308,0,.05,0,0,0,1]);g.initialize(10)
  self.assertRaises(ValueError,g.accept,10,'global',[-1e308,0,0,0,0,0,1],np.eye(6));self.assertFalse(g.ready())
if __name__=='__main__':unittest.main()
