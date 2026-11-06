"""Mapgen corner boxes and exact geometric primitives. Units: m and rad.
Contract: task7.5 B.2/B.5; provenance in task7.14 RESULTS. No ROS dependency.
Boxes are [..., cx,cy,cz,hx,hy,hz,cos(yaw),sin(yaw)]. Touching is collision.
"""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import torch

WALLS=[[-5,-5,0,.15,10,1.6,1,0],[4.85,-5,0,.15,10,1.6,1,0],[-4.85,-5,0,9.7,.15,1.6,1,0],[-4.85,4.85,0,9.7,.15,1.6,1,0]]

def load_map(data, *, rotation_tolerance=1e-6, map_id='<memory>'):
    """P1 rotation validation defaults to 1e-6 (SRC-0425).
    Accept existing corner-array schema, append each missing canonical wall once.
    No correction of invalid input and no PCD access.
    """
    if isinstance(data,(str,Path)):
        map_id=str(data); data=json.loads(Path(data).read_text())
    try:
        rows=torch.tensor(data['boxes'],dtype=torch.float64).reshape(-1,8)
        if not torch.isfinite(rows).all() or (rows[:,3:6]<=0).any():raise ValueError('nonfinite/nonpositive size')
        if ((rows[:,6:8].square().sum(-1)-1).abs()>rotation_tolerance).any():raise ValueError('invalid rotation')
        def centre(x):
            c=x.clone();c[:,0]+=x[:,6]*x[:,3]/2-x[:,7]*x[:,4]/2
            c[:,1]+=x[:,7]*x[:,3]/2+x[:,6]*x[:,4]/2
            c[:,2]+=x[:,5]/2;c[:,3:6]/=2
            return c
        c=centre(rows)
        ext=torch.stack([c[:,6].abs()*c[:,3]+c[:,7].abs()*c[:,4],c[:,7].abs()*c[:,3]+c[:,6].abs()*c[:,4]],-1)
        # Only roundoff allowance; map validity must not use a geometric margin.
        eps=torch.finfo(c.dtype).eps*32
        if (c[:,:2].abs()+ext>5+eps).any() or (c[:,2]-c[:,5]<-eps).any():raise ValueError('outside map')
        walls=centre(torch.tensor(WALLS,dtype=c.dtype))
        add=[]
        for w in walls:
            same=(c-w).abs().amax(-1)<=eps
            if same.sum()>1:raise ValueError('duplicate wall')
            if not same.any():add.append(w)
        return torch.cat([c,torch.stack(add)],0) if add else c
    except (ValueError,KeyError,RuntimeError,TypeError) as e:
        raise ValueError(f'{map_id}: {e}') from e

def pad_maps(maps, *, device='cpu', dtype=torch.float64):
    n=max(map(len,maps));v=torch.zeros(len(maps),n,8,dtype=dtype,device=device)
    mask=torch.zeros(len(maps),n,dtype=torch.bool,device=device)
    for i,m in enumerate(maps):v[i,:len(m)]=m.to(v);mask[i,:len(m)]=True
    return v,mask

def to_box(p,box):
    d=p-box[...,:3];c,s=box[...,6],box[...,7]
    return torch.stack([c*d[...,0]+s*d[...,1],-s*d[...,0]+c*d[...,1],d[...,2]],-1)

def rectangle_hits(base,boxes,mask=None):
    """SAT on footprint (0.99 x 0.67) and all obstacle XY projections."""
    angle=base[:,2]; c,s=angle.cos(),angle.sin()
    u=torch.stack([c,s],-1);v=torch.stack([-s,c],-1)
    bu=torch.stack([boxes[...,6],boxes[...,7]],-1);bv=torch.stack([-boxes[...,7],boxes[...,6]],-1)
    axes=torch.stack([u[:,None,:].expand_as(bu),v[:,None,:].expand_as(bu),bu,bv],-2)
    d=boxes[...,:2]-base[:,None,:2]
    gap=(d[:,:,None,:]*axes).sum(-1).abs()
    r=.495*(u[:,None,None,:]*axes).sum(-1).abs()+.335*(v[:,None,None,:]*axes).sum(-1).abs()
    r+=boxes[...,3,None]*(bu[:,:,None,:]*axes).sum(-1).abs()+boxes[...,4,None]*(bv[:,:,None,:]*axes).sum(-1).abs()
    out=(gap<=r).all(-1)
    return out if mask is None else out&mask

def segment_box_distance(a,b,h):
    """Exact segment-to-AABB distance by piecewise quadratic minimisation."""
    d=b-a;nonzero=d!=0;den=torch.where(nonzero,d,torch.ones_like(d))
    cuts=torch.cat([torch.zeros_like(a[...,:1]),torch.ones_like(a[...,:1]),(-h-a)/den,(h-a)/den],-1)
    cuts[...,2:]=torch.where(torch.cat([nonzero,nonzero],-1),cuts[...,2:],torch.zeros_like(cuts[...,2:]))
    cuts=cuts.clamp(0,1).sort(-1).values
    lo,hi=cuts[...,:-1],cuts[...,1:];mid=(lo+hi)/2
    p=a[...,None,:]+mid[...,None]*d[...,None,:]
    outside=(p.abs()>h[...,None,:]);edge=p.sign()*h[...,None,:]
    dd=(d[...,None,:].square()*outside).sum(-1)
    nd=((a[...,None,:]-edge)*d[...,None,:]*outside).sum(-1)
    t=(-nd/torch.where(dd>0,dd,torch.ones_like(dd))).maximum(lo).minimum(hi)
    dist=(a[...,None,:]+t[...,None]*d[...,None,:]).abs()-h[...,None,:]
    return dist.clamp_min(0).square().sum(-1).amin(-1).sqrt()

def segment_distance(a,b,c,d):
    """Closed segment distance including zero-length and parallel cases."""
    u,v,w=b-a,d-c,a-c
    aa=(u*u).sum(-1);bb=(u*v).sum(-1);cc=(v*v).sum(-1);dd=(u*w).sum(-1);ee=(v*w).sum(-1)
    def safe(n,z):return n/torch.where(z!=0,z,torch.ones_like(z))
    det=aa*cc-bb*bb
    si=safe(bb*ee-cc*dd,det);ti=safe(aa*ee-bb*dd,det)
    valid=(det>0)&(si>=0)&(si<=1)&(ti>=0)&(ti<=1)
    si=si.clamp(0,1);ti=ti.clamp(0,1)
    candidates=[torch.linalg.vector_norm(w+si[...,None]*u-ti[...,None]*v,dim=-1).masked_fill(~valid,float('inf'))]
    for s in (0.,1.):
        t=safe(ee+s*bb,cc).clamp(0,1)
        candidates.append(torch.linalg.vector_norm(w+s*u-t[...,None]*v,dim=-1))
    for t in (0.,1.):
        s=safe(t*bb-dd,aa).clamp(0,1)
        candidates.append(torch.linalg.vector_norm(w+s[...,None]*u-t*v,dim=-1))
    return torch.stack(candidates,-1).amin(-1)

@dataclass
class Collision:
    base:torch.Tensor
    arm:torch.Tensor
    self_collision:torch.Tensor
    @property
    def any(self):return self.base|self.arm|self.self_collision

def self_hits(caps,allowed=None):
    n=caps.shape[-2]
    if n==0:return torch.zeros(caps.shape[0],dtype=torch.bool,device=caps.device)
    dist=segment_distance(caps[:,:,None,:3],caps[:,:,None,3:6],caps[:,None,:,:3],caps[:,None,:,3:6])
    hit=dist<=caps[:,:,None,6]+caps[:,None,:,6]
    check=torch.ones(n,n,dtype=torch.bool,device=caps.device).triu(1)
    if allowed is not None:check=check&~allowed
    return (hit&check).any(dim=(-1,-2))

class TruthCollision:
    """Only truth consumer besides rendering. Capsules must be in world frame.
    Self pairs/URDF body geometry are supplied explicitly, never a sampled SRDF.
    """
    def __init__(self,boxes,mask,robot=None):self.boxes,self.mask,self.robot=boxes,mask,robot
    def __call__(self,base,caps,allowed=None,*,q=None):
        boxes=self.boxes.expand(base.shape[0],-1,-1);mask=self.mask.expand(base.shape[0],-1)
        cb=rectangle_hits(base,boxes,mask).any(-1)
        if caps.shape[1]:
            a=to_box(caps[:,:,None,:3],boxes[:,None]);b=to_box(caps[:,:,None,3:6],boxes[:,None])
            dist=segment_box_distance(a,b,boxes[:,None,:,3:6])
            arm=((dist<=caps[:,:,None,6])&mask[:,None]).any(dim=(-1,-2))
            arm|=(caps[...,[2,5]].amin(-1)-caps[...,6]<=0).any(-1)
        else:arm=torch.zeros_like(cb)
        return Collision(cb,arm,self_hits(caps,allowed) if self.robot is None else self.robot.self_collision(base,caps,allowed,q=q))
