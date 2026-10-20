"""Task4 fail-closed lifecycle and SE3 conversion. Engineering gate SRC0075/0076.
OpenVINS ROS pose xyzw is Hamilton ItoG (official ROS1Visualizer comment).
Covariance [p_G, theta_I] -> [p_base_G, theta_G], including rigid lever arm.
Alignment is commanded once, never derived from simulator feedback; anchor uncertainty unknown.
"""
import numpy as np
from scipy.spatial.transform import Rotation

def pose_matrix(p):
 p=np.asarray(p,dtype=float)
 if p.shape!=(7,) or not np.isfinite(p).all():raise ValueError('nonfinite/shape')
 n=np.linalg.norm(p[3:])
 if not np.isfinite(n) or abs(n-1)>.05:raise ValueError('quaternion')
 t=np.eye(4);t[:3,:3]=Rotation.from_quat(p[3:]/n).as_matrix();t[:3,3]=p[:3];return t

def skew(p):
 x,y,z=p;return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])

def transform_pose(t):return np.r_[t[:3,3],Rotation.from_matrix(t[:3,:3]).as_quat()]

class EstimateGate:
 def __init__(self,age=.1,future=.0005,lever=(.35,0,.58228)):
  self.age=age;self.future=future;self.Tbi=np.eye(4);self.Tbi[:3,3]=lever
  self.state='STOPPED';self.now=None;self.last=None;self.start=None;self.align=None;self.epoch=0;self.halted=False;self.reason=None;self.accepted=0
 def invalidate(self,reason):self.state='INVALID_STOP';self.reason=reason;self.align=None
 def clock(self,t):
  if not np.isfinite(t) or t<0:return
  if self.now is None and t==0:return
  if self.now is not None and t<self.now:
   self.halted=True;self.epoch+=1;self.invalidate('clock_rollback')
  self.now=t
  if self.state=='ESTIMATE_ONLY_READY' and self.last is not None and t-self.last>self.age:self.invalidate('stale')
 def begin(self,anchor):
  if self.halted or self.now is None:raise ValueError('halted/no_clock')
  self.anchor=pose_matrix(anchor);self.epoch+=1;self.last=None;self.align=None;self.reason=None;self.state='BOOTSTRAP_PUBLIC_POSE'
 def initialize(self,start):
  if self.state!='BOOTSTRAP_PUBLIC_POSE':raise ValueError('not bootstrap')
  self.start=start;self.last=None;self.align=None;self.state='COLLECT_STATIC_RAW'
 def ready(self):return self.state=='ESTIMATE_ONLY_READY' and self.now is not None and self.last is not None and 0<=self.now-self.last<=self.age
 def accept(self,stamp,frame,pose,cov):
  try:
   if self.halted or self.state not in ('COLLECT_STATIC_RAW','ESTIMATE_ONLY_READY'):raise ValueError('invalid lifecycle')
   if self.now is None or frame!='global':raise ValueError('no_clock/frame')
   if not np.isfinite(stamp) or stamp<self.start or stamp<=0 or stamp>self.now+self.future or self.now-stamp>self.age:raise ValueError('epoch/future/stale')
   if self.last is not None and stamp<=self.last:raise ValueError('old/duplicate')
   ti=pose_matrix(pose);cov=np.asarray(cov,dtype=float).reshape(6,6)
   if not np.isfinite(cov).all():raise ValueError('nonfinite covariance')
   if self.align is None:self.align=self.anchor@self.Tbi@np.linalg.inv(ti)
   tb=self.align@ti@np.linalg.inv(self.Tbi)
   if not (np.isfinite(self.align).all() and np.isfinite(tb).all()):raise ValueError('nonfinite derived transform')
   rg=self.align[:3,:3];ri=ti[:3,:3];j=np.zeros((6,6));j[:3,:3]=rg;j[:3,3:]=rg@ri@skew(self.Tbi[:3,3]);j[3:,3:]=rg@ri
   c=j@cov@j.T
   if not np.isfinite(c).all():raise ValueError('nonfinite transformed covariance')
   self.last=stamp;self.state='ESTIMATE_ONLY_READY';self.accepted+=1
   return transform_pose(tb),c
  except (ValueError,TypeError,np.linalg.LinAlgError) as e:self.invalidate(str(e));raise ValueError(str(e))
