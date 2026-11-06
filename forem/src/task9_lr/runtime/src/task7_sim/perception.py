"""Depth-only global accumulation and local collision: no truth in Grid/LocalCollision.
Sensor contract: N8/N9, G1/G2; metres, pixel-centre rays, slant range.
"""
from dataclasses import dataclass
import math
import torch
from .geometry import to_box, pad_maps, TruthCollision, self_hits, segment_distance

def ray_boxes(origin,direction,boxes,mask):
    if boxes.shape[1]==0:return torch.full(origin.shape[:-1],float('inf'),device=origin.device,dtype=origin.dtype)
    o=to_box(origin[:,:,None],boxes[:,None]);c,s=boxes[:,None,:,6],boxes[:,None,:,7]
    x=direction[:,:,None];d=torch.stack([c*x[...,0]+s*x[...,1],-s*x[...,0]+c*x[...,1],x[...,2].expand_as(c*x[...,0])],-1)
    h=boxes[:,None,:,3:6];nz=d!=0;den=torch.where(nz,d,torch.ones_like(d))
    t1,t2=(-h-o)/den,(h-o)/den
    lo=torch.where(nz,torch.minimum(t1,t2),torch.full_like(t1,-float('inf')))
    hi=torch.where(nz,torch.maximum(t1,t2),torch.full_like(t1,float('inf')))
    near,far=lo.amax(-1),hi.amin(-1)
    valid=(near<=far)&(far>=0)&(~((~nz)&(o.abs()>h))).all(-1)&mask[:,None]
    t=torch.where(near>=0,near,far)
    return t.masked_fill(~valid,float('inf')).amin(-1)

def _quadratic(a,b,c):
    disc=b*b-a*c;valid=(a>0)&(disc>=0)
    root=disc.clamp_min(0).sqrt();den=torch.where(a>0,a,torch.ones_like(a))
    lo,hi=(-b-root)/den,(-b+root)/den
    return torch.where(valid&(hi>=0),torch.where(lo>=0,lo,hi),float('inf'))

def ray_capsules(origin,direction,caps):
    if caps.shape[1]==0:return torch.full(origin.shape[:-1],float('inf'),device=origin.device,dtype=origin.dtype)
    a,b,r=caps[:,None,:,:3],caps[:,None,:,3:6],caps[:,None,:,6]
    o=origin[:,:,None]-a;d=direction[:,:,None];axis=b-a;l2=axis.square().sum(-1)
    unit=axis/l2.sqrt().clamp_min(torch.finfo(origin.dtype).tiny)[...,None]
    od=(o*unit).sum(-1);dd=(d*unit).sum(-1)
    op=o-od[...,None]*unit;dp=d-dd[...,None]*unit
    aa=dp.square().sum(-1);bb=(op*dp).sum(-1);cc=op.square().sum(-1)-r*r
    disc=bb*bb-aa*cc;den=torch.where(aa>0,aa,torch.ones_like(aa))
    roots=torch.stack([(-bb-disc.clamp_min(0).sqrt())/den,(-bb+disc.clamp_min(0).sqrt())/den],-1)
    z=od[...,None]+roots*dd[...,None]
    valid=(aa>0)[...,None]&(disc>=0)[...,None]&(roots>=0)&(z>=0)&(z<=l2.sqrt()[...,None])&(l2>0)[...,None]
    tc=roots.masked_fill(~valid,float('inf')).amin(-1)
    end=[]
    for centre in (a,b):
        v=origin[:,:,None]-centre
        end.append(_quadratic(d.square().sum(-1),(v*d).sum(-1),v.square().sum(-1)-r*r))
    return torch.stack([tc,*end],-1).amin(dim=(-1,-2))

@dataclass
class Depth:
    distance:torch.Tensor
    valid:torch.Tensor
    self_hit:torch.Tensor
    points:torch.Tensor
    origin_inside_self:torch.Tensor

class Panorama:
    """Truth-authorized renderer. Body boxes are optional explicit robot geometry.
    If the G1 origin intersects supplied geometry, report it; never move sensor.
    """
    def __init__(self,boxes,mask,robot=None):self.boxes,self.mask,self.robot=boxes,mask,robot
    def __call__(self,base,caps,body_boxes=None):
        device,dtype=base.device,base.dtype;B=len(base)
        if body_boxes is None and self.robot is not None:body_boxes=self.robot.body_boxes(base)
        yaw=(torch.arange(360,device=device,dtype=dtype)+.5)*math.pi/180
        pitch=(torch.arange(90,device=device,dtype=dtype)+.5)*math.pi/180-math.pi/4
        az=yaw[None,None,:]+base[:,2,None,None];el=pitch[None,:,None]
        d=torch.stack([(el.cos()*az.cos()).expand(B,90,360),(el.cos()*az.sin()).expand(B,90,360),el.sin().expand(B,90,360)],-1).reshape(B,-1,3)
        o=torch.cat([base[:,:2],torch.full((B,1),.5,device=device,dtype=dtype)],-1)[:,None].expand_as(d)
        world=ray_boxes(o,d,self.boxes.expand(B,-1,-1),self.mask.expand(B,-1))
        ground=torch.where(d[...,2]<0,-o[...,2]/torch.where(d[...,2]!=0,d[...,2],torch.ones_like(d[...,2])),float('inf'))
        world=torch.minimum(world,ground)
        own=ray_capsules(o,d,caps)
        inside=torch.zeros(B,device=device,dtype=torch.bool)
        if caps.shape[1]:
            pos=o[:,:1];dist=segment_distance(pos,pos,caps[...,:3],caps[...,3:6]);inside=(dist<=caps[...,6]).any(-1)
        if body_boxes is not None:
            mask=torch.ones(body_boxes.shape[:2],device=device,dtype=torch.bool)
            own=torch.minimum(own,ray_boxes(o,d,body_boxes,mask))
            bodypos=to_box(o[:,:1],body_boxes)
            inside|=(bodypos.abs()<=body_boxes[...,3:6]).all(-1).any(-1)
        selfhit=(own<=world)&(own<=6)
        selfhit|=inside[:,None]
        valid=torch.isfinite(world)&(world<=6)&~selfhit
        distance=world.masked_fill(~valid,float('inf'))
        pts=o+d*torch.where(valid,distance,torch.zeros_like(distance))[...,None]
        return Depth(distance.reshape(B,90,360),valid.reshape(B,90,360),selfhit.reshape(B,90,360),pts.reshape(B,90,360,3),inside)

class Grid:
    """World grid [row=y,col=x], two raw channels; only sensor landings update it."""
    def __init__(self,observed,height,timestamp):self.observed,self.height,self.timestamp=observed,height,timestamp
    @classmethod
    def empty(cls,batch,*,device='cpu',dtype=torch.float32):
        return cls(torch.zeros(batch,200,200,device=device,dtype=torch.bool),torch.zeros(batch,200,200,device=device,dtype=dtype),torch.zeros(batch,device=device,dtype=dtype))
    def snapshot(self):return Grid(self.observed.clone(),self.height.clone(),self.timestamp.clone())
    def select(self,indices):return Grid(self.observed[indices].clone(),self.height[indices].clone(),self.timestamp[indices].clone())
    def update(self,points,valid,timestamp):
        B=len(self.height);p=points.reshape(B,-1,3);valid=valid.reshape(B,-1)&torch.isfinite(p).all(-1)
        ij=torch.floor((p[...,:2]+5)/.05).long();valid&=(ij>=0).all(-1)&(ij<200).all(-1)
        for b in range(B):
            ids=ij[b,valid[b],1]*200+ij[b,valid[b],0]
            h=p[b,valid[b],2];h=torch.where(h>.05,h,torch.zeros_like(h))
            self.observed[b].view(-1)[ids]=True
            self.height[b].view(-1).scatter_reduce_(0,ids,h,reduce='amax',include_self=True)
        self.timestamp.copy_(timestamp)
    def crop(self,base,*,quantized=True):
        d=(torch.arange(128,device=base.device,dtype=base.dtype)+.5-64)*.05
        y,x=torch.meshgrid(d,d,indexing='ij');c,s=base[:,2].cos(),base[:,2].sin()
        wx=base[:,0,None,None]+c[:,None,None]*x-s[:,None,None]*y
        wy=base[:,1,None,None]+s[:,None,None]*x+c[:,None,None]*y
        ix=torch.floor((wx+5)/.05).long();iy=torch.floor((wy+5)/.05).long()
        valid=(ix>=0)&(ix<200)&(iy>=0)&(iy<200);ix=ix.clamp(0,199);iy=iy.clamp(0,199)
        rows=torch.arange(len(base),device=base.device)[:,None,None]
        known=self.observed[rows,iy,ix]&valid;h=self.height[rows,iy,ix]
        if quantized:h=torch.round(h/.01).clamp(0,255).to(torch.uint8).to(h.dtype)*.01
        return torch.stack([known.to(h.dtype),torch.where(known,h,0)],-1)

class LocalCollision:
    """Consumes an owned sensor Grid snapshot; never takes WorldTruth.
    Occupied cells become world-space columns only in this local computation.
    """
    def __init__(self,grid,robot=None):self.grid=grid.snapshot();self.robot=robot
    def __call__(self,base,caps,allowed=None,*,q=None):
        local=self.grid.crop(base);occupied=(local[...,0]>0)&(local[...,1]>0)
        counts=occupied.sum(dim=(1,2));width=max(1,int(counts.max()))
        env,iy,ix=torch.where(occupied)
        rank=torch.arange(len(env),device=base.device)-(counts.cumsum(0)-counts)[env]
        x,y=(ix.to(base.dtype)+.5-64)*.05,(iy.to(base.dtype)+.5-64)*.05
        c,s=base[env,2].cos(),base[env,2].sin();h=local[env,iy,ix,1];one=torch.ones_like(h)
        rows=torch.stack([base[env,0]+c*x-s*y,base[env,1]+s*x+c*y,h/2,.025*one,.025*one,h/2,c*one,s*one],-1)
        boxes=torch.zeros(len(base),width,8,device=base.device,dtype=base.dtype);mask=torch.zeros(len(base),width,device=base.device,dtype=torch.bool)
        boxes[env,rank]=rows;mask[env,rank]=True
        # Shared arithmetic only; this instance contains columns from Grid, no truth.
        return TruthCollision(boxes,mask,robot=self.robot)(base,caps,allowed,q=q)
