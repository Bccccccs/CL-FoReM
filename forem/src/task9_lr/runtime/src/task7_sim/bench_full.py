"""Bounded full-geometry validation/profiling fixtures. No learning or policy eval."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import torch
from .robot import RobotGeometry,ROOT
from .kinematics import Kinematics
from .geometry import load_map,pad_maps,TruthCollision
from .perception import Grid,Panorama
from .motion import Route,matrix_quat
from .core import State,Candidate,Core,rollout

ARTIFACT=ROOT/'results/task7/t7.14-r2-20261021-0000'

def scene(E=1,*,device='cpu',dtype=torch.float64,nodes=16,core_class=Core):
    info=json.loads((ARTIFACT/'fixture.json').read_text());q0=torch.tensor(info['q'],device=device,dtype=dtype)
    robot=RobotGeometry();kin=Kinematics();base=torch.zeros(E,3,device=device,dtype=dtype);q=q0.expand(E,-1).clone()
    state=State(base,q,torch.zeros(E,device=device,dtype=dtype));tcp=kin.world_tcp(base,q)
    t=torch.linspace(0,.12,nodes,device=device,dtype=dtype)
    delta=torch.stack([t,.01*torch.sin(t/.12*torch.pi),torch.zeros_like(t)],-1)
    xyz=tcp[:,None,:3,3]+delta[None];quat=matrix_quat(tcp[:,:3,:3])[:,None].expand(-1,nodes,-1)
    route=Route(xyz,quat)
    boxes,mask=pad_maps([load_map({'boxes':[[1.8,-1,0,.2,2,1.6,1,0],[-2,-1,0,.2,2,1.6,1,0]]})],device=device,dtype=dtype)
    boxes=boxes.expand(E,-1,-1);mask=mask.expand(E,-1)
    render=Panorama(boxes,mask,robot=robot);grid=Grid.empty(E,device=device,dtype=dtype)
    depth=render(base,robot(base,q));grid.update(depth.points,depth.valid,state.s)
    core=core_class(state,route,grid,kin,robot,TruthCollision(boxes,mask,robot=robot),synchronous=False,renderer=render)
    return core,depth

def candidates(core,K=13):
    theta=torch.linspace(-.2,.2,K,device=core.state.s.device,dtype=core.state.s.dtype)
    poses=core.state.base[:,None].expand(-1,K,-1).clone()
    poses[:,:,0]+=.04*theta.cos();poses[:,:,1]+=.04*theta.sin();poses[:,:,2]+=theta
    progress=torch.linspace(.015,.03,K,device=theta.device,dtype=theta.dtype)[None].expand(len(poses),-1).clone()
    inplace=torch.zeros_like(progress,dtype=torch.bool);inplace[:,0]=True;poses[:,0]=core.state.base
    return poses,progress,inplace

def script(obs):return torch.zeros(len(obs['q']),3,device=obs['q'].device,dtype=obs['q'].dtype)
