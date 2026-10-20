"""Physical multicamera baseline must agree with optical TF and frozen Kalibr.
Catches rotating only viewing axes while leaving body-Y stereo positions.
"""
import math, unittest, xml.etree.ElementTree as ET
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
XACRO='http://www.ros.org/wiki/xacro'  # actual file namespace below

def rotation(rpy):
 r,p,y=rpy;cr,sr=math.cos(r),math.sin(r);cp,sp=math.cos(p),math.sin(p);cy,sy=math.cos(y),math.sin(y)
 return [[cy*cp,cy*sp*sr-sy*cr,cy*sp*cr+sy*sr],[sy*cp,sy*sp*sr+cy*cr,sy*sp*cr-cy*sr],[-sp,cp*sr,cp*cr]]
def mv(R,v):return [sum(R[i][j]*v[j] for j in range(3)) for i in range(3)]
def add(a,b):return [x+y for x,y in zip(a,b)]
def floats(s):return [float(v) for v in s.split()]

class StereoRigTests(unittest.TestCase):
 def setUp(self):
  self.xml=ET.parse(ROOT/'src/forem_husky/urdf/visual_inertial_sensors.urdf.xacro').getroot()
  self.sensors=yaml.safe_load((ROOT/'config/task4/sensors.yaml').read_text())
  self.chain=yaml.safe_load((ROOT/'config/task4/kalibr_imucam_chain.yaml').read_text().replace('%YAML:1.0',''))
  self.sensor=self.xml.find(".//sensor[@name='task4_stereo']")
 def test_only_declared_side_candidate_and_unchanged_imu(self):
  self.assertAlmostEqual(floats(self.sensor.find('pose').text)[5],math.pi/2)
  self.assertEqual(floats(self.xml.find(".//sensor[@name='task4_imu']/pose").text),[.35,0,.45,0,0,0])
  origin=self.xml.find(".//joint[@name='task4_imu_mount']/origin")
  self.assertEqual(floats(origin.get('xyz')),[.35,0,.45]);self.assertEqual(floats(origin.get('rpy')),[0,0,0])
 def test_physical_baseline_and_optical_axes_agree_with_calibration(self):
  pose=floats(self.sensor.find('pose').text);R=rotation(pose[3:]);centers={}
  for side,index,sign in [('left',0,1),('right',1,-1)]:
   local=floats(self.sensor.find(f"camera[@name='{side}']/pose").text);center=add(pose[:3],mv(R,local[:3]));centers[side]=center
   origin=self.xml.find(".//joint[@name='task4_${side}_mount']/origin")
   # Macro expressions contain only predefined side/sign values, not runtime exec.
   xyz=floats(origin.get('xyz').replace('${y}',str(sign*.06)).replace('${-y}',str(-sign*.06)))
   optical=rotation(floats(origin.get('rpy')));T=self.chain['cam'+str(index)]['T_imu_cam']
   for i in range(3):
    self.assertAlmostEqual(center[i]-.35*(i==0)-.45*(i==2),xyz[i],places=10)
    self.assertAlmostEqual(xyz[i],T[i][3],places=10)
    for j in range(3):self.assertAlmostEqual(optical[i][j],T[i][j],places=10)
   self.assertEqual(T,self.sensors['calibration']['T_imu_'+side+'_camera_optical'])
   for a,b in zip(center,self.sensors['stereo'][side+'_camera_body_xyz_m']):self.assertAlmostEqual(a,b,places=10)
  baseline=[a-b for a,b in zip(centers['right'],centers['left'])];T=self.chain['cam0']['T_imu_cam'];optical_x=[T[i][0] for i in range(3)]
  for a,b in zip(baseline,optical_x):self.assertAlmostEqual(a,.12*b,places=10)
  self.assertAlmostEqual(sum(a*a for a in baseline)**.5,.12,places=10)
  self.assertAlmostEqual(T[1][2],1) # new optical forward +body Y
 def test_projection_and_sampling_contract_preserved(self):
  for side in ['left','right']:
   c=self.sensor.find(f"camera[@name='{side}']")
   self.assertAlmostEqual(float(c.find('horizontal_fov').text),math.pi/2)
   self.assertEqual(c.find('image/width').text,'640');self.assertEqual(c.find('image/height').text,'480')
  self.assertEqual(self.sensor.find('update_rate').text,'20')
  self.assertEqual(self.xml.find(".//sensor[@name='task4_imu']/update_rate").text,'200')
  self.assertEqual(self.sensor.find('plugin/hackBaseline').text,'0.12')
  self.assertEqual(self.chain['cam0']['intrinsics'],self.chain['cam1']['intrinsics'])
  self.assertEqual(self.chain['cam0']['timeshift_cam_imu'],0)
if __name__=='__main__':unittest.main()
