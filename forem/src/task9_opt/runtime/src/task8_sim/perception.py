"""PCD-authorized ghost panorama; unchanged task7 Depth/Grid landing contract."""
import copy
import json
import math
from pathlib import Path
import torch
from task7_sim.perception import Depth

_DEFAULT = Path(__file__).resolve().parents[2]/'config/task8/sensor.json'


class PcdPanorama:
    """Fixed base-relative sensor ignores all own geometry, never scene geometry.

    self_hit/origin_inside_self=False mean own occlusion is disabled. They do
    not assert the physical sensor lies outside the robot. Scene-inside rays
    retain the scene's zero-distance response.
    """
    def __init__(self, scene_batch, *, sensor_config):
        expected = json.loads(_DEFAULT.read_text())
        if sensor_config != expected:
            raise ValueError('unsupported ghost-v1 sensor configuration')
        self.scene_batch = scene_batch
        self.sensor_config = copy.deepcopy(sensor_config)
        self.sensor_policy = 'ghost-v1'
        self.self_occlusion = 'ignored'

    def __call__(self, base, caps, body_boxes=None):
        device, dtype = base.device, base.dtype
        batch = len(base)
        yaw = (torch.arange(360, device=device, dtype=dtype)+.5)*math.pi/180
        pitch = (torch.arange(90, device=device, dtype=dtype)+.5)*math.pi/180-math.pi/4
        az = yaw[None,None,:]+base[:,2,None,None]
        el = pitch[None,:,None]
        directions = torch.stack([(el.cos()*az.cos()).expand(batch,90,360),
                                  (el.cos()*az.sin()).expand(batch,90,360),
                                  el.sin().expand(batch,90,360)], -1).reshape(batch,-1,3)
        origins = torch.cat([base[:,:2],torch.full((batch,1),.5,device=device,dtype=dtype)],-1)[:,None].expand_as(directions)
        world = self.scene_batch.raycast(origins,directions,max_range=6.)
        dz = directions[...,2]
        ground = torch.where(dz<0,-origins[...,2]/torch.where(dz!=0,dz,torch.ones_like(dz)),float('inf'))
        world = torch.minimum(world,ground)
        valid = torch.isfinite(world)&(world>=0)&(world<=6)
        distance = world.masked_fill(~valid,float('inf'))
        points = origins+directions*torch.where(valid,distance,torch.zeros_like(distance))[...,None]
        self_hit = torch.zeros_like(valid)
        inside = torch.zeros(batch,device=device,dtype=torch.bool)
        depth = Depth(distance.reshape(batch,90,360), valid.reshape(batch,90,360),
                      self_hit.reshape(batch,90,360), points.reshape(batch,90,360,3), inside)
        depth.sensor_policy = self.sensor_policy
        depth.self_occlusion = self.self_occlusion
        return depth
