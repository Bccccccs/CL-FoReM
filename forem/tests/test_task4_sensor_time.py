import sys, unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_task4_sensors import SensorTime,validate_intrinsics,validate_imu
class SensorTests(unittest.TestCase):
    def test_nonmonotonic_sensor_stamp_rejected(self):
        s=SensorTime(); s.accept('imu',100)
        for stamp in [100,99,0]:
            with self.assertRaises(ValueError): s.accept('imu',stamp)
    def test_stereo_time_mismatch_rejected(self):
        s=SensorTime(); self.assertEqual(s.pair(100,100),100)
        with self.assertRaises(ValueError): s.pair(100,101)
    def test_epoch_reset_clears_sync_buffers(self):
        s=SensorTime();s.on_clock(1000);s.push('left',900,'old');s.accept('imu',950)
        s.on_clock(0);self.assertEqual(s.epoch,1);self.assertFalse(s.last)
        self.assertFalse(s.buffers['left']);self.assertTrue(s.halted)
        for stamp in [1,900,10000000000]:
            with self.assertRaises(ValueError):s.push('right',stamp,'old epoch')
    def test_bounded_queue_and_out_of_order(self):
        s=SensorTime(cap=2)
        for i in [1,2,3]:s.push('left',i,i)
        self.assertNotIn(1,s.buffers['left'])
        with self.assertRaises(ValueError):s.push('left',2,2)
    def test_camera_intrinsics_consistent(self):
        for side in ['left','right']:
            i=SimpleNamespace(width=640,height=480,K=[320,0,320.5,0,320,240.5,0,0,1],P=[320,0,320.5,-38.4 if side=='right' else 0,0,320,240.5,0,0,0,1,0],D=[0]*5,header=SimpleNamespace(frame_id='task4_'+side+'_optical'))
            self.assertTrue(validate_intrinsics(i,side)); i.P[3]=1
            with self.assertRaises(ValueError):validate_intrinsics(i,side)

    def test_nonfinite_imu_rejected(self):
        self.assertTrue(validate_imu([0,0,9.8],[0,0,0]))
        for x in [float('nan'),float('inf'),float('-inf')]:
            with self.assertRaises(ValueError):validate_imu([0,x,9.8],[0,0,0])
            with self.assertRaises(ValueError):validate_imu([0,0,9.8],[x,0,0])
