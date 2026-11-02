"""L.2 / D20 v1. Sensor grid only; no truth, scan timestamp or global pose.

Vector order is q,tcp,next_tcp,route_points(flat xyz),subgoal,synchronous,
previous_action. Sync=74, async=75. All raw metric fields retain their units.
"""
import torch
VERSION='lower-observation-d20-v1'
ACTION_VERSION='lower-action-l1-d8-v1'
FIELDS=('q','tcp','next_tcp','route_points','subgoal','synchronous','previous_action')

def encode_grid(grid):
    out=torch.empty_like(grid,dtype=torch.uint8)
    out[...,0]=grid[...,0].to(torch.uint8)
    out[...,1]=torch.round(grid[...,1]/.01).clamp(0,255).to(torch.uint8)
    out[...,2]=grid[...,2].to(torch.uint8)
    return out

def decode_grid(encoded):
    out=encoded.float();out[...,1]*=.01
    return out

def vector(observation):
    return torch.cat([observation[k].flatten(1) for k in FIELDS],-1)

def preprocess(observation):
    return decode_grid(encode_grid(observation['grid'])),vector(observation)
