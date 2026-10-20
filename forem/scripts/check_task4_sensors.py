#!/usr/bin/env python3
"""Raw sensor validation and exact stereo synchronization; simulation epochs only."""
import math
from collections import OrderedDict

class SensorTime:
    def __init__(self, cap=10):
        self.cap = cap
        self.epoch = 0
        self.clock = None
        self.halted = False
        self.last = {}
        self.buffers = {'left': OrderedDict(), 'right': OrderedDict()}
    def on_clock(self, stamp):
        if self.clock is not None and stamp < self.clock:
            self.epoch += 1
            self.halted = True
            self.last.clear()
            for q in self.buffers.values(): q.clear()
        self.clock = stamp
    def accept(self, stream, stamp):
        if self.halted: raise ValueError('clock rollback halted sensor epoch; restart run')
        if not isinstance(stamp, int) or stamp <= 0: raise ValueError('invalid stamp')
        if stamp <= self.last.get(stream, -1): raise ValueError('nonmonotonic stamp')
        self.last[stream] = stamp
    def pair(self, left_stamp, right_stamp):
        if left_stamp != right_stamp: raise ValueError('stereo stamp mismatch')
        return left_stamp
    def push(self, side, stamp, value):
        self.accept(side, stamp)
        q = self.buffers[side]
        q[stamp] = value
        other = 'right' if side == 'left' else 'left'
        if stamp in self.buffers[other]:
            left = self.buffers['left'].pop(stamp)
            right = self.buffers['right'].pop(stamp)
            return stamp, left, right
        while len(q) > self.cap: q.popitem(last=False)
        return None

def validate_intrinsics(info, side):
    if (info.width, info.height) != (640, 480): raise ValueError('image geometry')
    if not all(math.isfinite(x) for x in list(info.K)+list(info.P)+list(info.D)): raise ValueError('nonfinite calibration')
    expected = [320.,0.,320.5,0.,320.,240.5,0.,0.,1.]
    if any(abs(a-b)>0.002 for a,b in zip(info.K,expected)): raise ValueError('K inconsistent with rendered FOV')
    if any(abs(x)>1e-9 for x in info.D): raise ValueError('unexpected distortion')
    f = info.K[0]
    expected_p = [f,0.,320.5, -f*0.12 if side=='right' else 0., 0.,f,240.5,0.,0.,0.,1.,0.]
    if any(abs(a-b)>1e-6 for a,b in zip(info.P,expected_p)): raise ValueError('projection baseline')
    if info.header.frame_id != 'task4_'+side+'_optical': raise ValueError('optical frame')
    return True


def validate_imu(acc, gyro):
    if len(acc)!=3 or len(gyro)!=3 or not all(math.isfinite(x) for x in list(acc)+list(gyro)):
        raise ValueError('nonfinite IMU measurement')
    return True
