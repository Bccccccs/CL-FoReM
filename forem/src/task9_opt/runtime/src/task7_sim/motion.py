"""Exact unicycle arc, CBL action units and fixed TCP route, task7.5 B.3/B.7."""
import math
import torch

def wrap(x):return torch.atan2(x.sin(),x.cos())
def arc(base,v,w,dt):
    if not torch.isfinite(base).all() or not torch.isfinite(v).all() or not torch.isfinite(w).all():raise ValueError('nonfinite base/action')
    if (v.abs()>.3).any() or (w.abs()>1).any() or dt<0:raise ValueError('action outside v/omega limits')
    h=w*dt/2;travel=v*dt*torch.sinc(h/math.pi);mid=base[...,2]+h
    return base+torch.stack([travel*mid.cos(),travel*mid.sin(),w*dt],-1)

def actions(raw,synchronous,inplace=None):
    if raw.shape[-1]!=3 or not torch.isfinite(raw).all() or (raw.abs()>1).any():raise ValueError('expected raw [u,omega,v] in [-1,1]')
    u=.01+.145*(raw[...,0]+1) if synchronous else .15*(raw[...,0]+1)
    w,v=raw[...,1],raw[...,2]*.3
    if inplace is not None:w=torch.where(inplace,0,w);v=torch.where(inplace,0,v)
    return u,w,v

def advance(s,u,cap):return torch.minimum(s+u*.05,cap)
def quat_matrix(q):
    q=q/torch.linalg.vector_norm(q,dim=-1,keepdim=True)
    x,y,z,w=q.unbind(-1)
    return torch.stack([1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)],-1).reshape(*q.shape[:-1],3,3)

def matrix_quat(R):
    # Choose the largest squared quaternion component to avoid division near zero.
    a,b,c=R[...,0,0],R[...,1,1],R[...,2,2]
    sq=torch.stack([1+a-b-c,1-a+b-c,1-a-b+c,1+a+b+c],-1).clamp_min(0)
    rows=torch.stack([
      torch.stack([sq[...,0],R[...,0,1]+R[...,1,0],R[...,0,2]+R[...,2,0],R[...,2,1]-R[...,1,2]],-1),
      torch.stack([R[...,0,1]+R[...,1,0],sq[...,1],R[...,1,2]+R[...,2,1],R[...,0,2]-R[...,2,0]],-1),
      torch.stack([R[...,0,2]+R[...,2,0],R[...,1,2]+R[...,2,1],sq[...,2],R[...,1,0]-R[...,0,1]],-1),
      torch.stack([R[...,2,1]-R[...,1,2],R[...,0,2]-R[...,2,0],R[...,1,0]-R[...,0,1],sq[...,3]],-1)],-2)
    idx=sq.argmax(-1)
    q=rows.gather(-2,idx[...,None,None].expand(*idx.shape,1,4)).squeeze(-2)
    return q/torch.linalg.vector_norm(q,dim=-1,keepdim=True)

class Route:
    """Batch of fixed position-arc-length routes; xyzw quaternions.
    An orientation-only segment needs a protocol decision, so is rejected.
    """
    def __init__(self,xyz,quat):
        if xyz.ndim!=3 or xyz.shape[-1]!=3 or quat.shape!=(*xyz.shape[:-1],4) or xyz.shape[1]<2:raise ValueError('route shape')
        norm=quat.norm(dim=-1,keepdim=True)
        if not torch.isfinite(xyz).all() or not torch.isfinite(quat).all() or (norm==0).any():raise ValueError('invalid route')
        self.xyz=xyz.clone();self.quat=quat/norm
        for i in range(1,self.quat.shape[1]):
            flip=(self.quat[:,i-1]*self.quat[:,i]).sum(-1)<0
            self.quat[:,i]=torch.where(flip[:,None],-self.quat[:,i],self.quat[:,i])
        ds=xyz.diff(dim=1).norm(dim=-1)
        changed=(self.quat[:,:-1]!=self.quat[:,1:]).any(-1)
        if ((ds==0)&changed).any():raise ValueError('orientation-only route segment: arc-length metric undecided')
        self.s=torch.cat([torch.zeros_like(ds[:,:1]),ds.cumsum(-1)],-1)
        self.length=self.s[:,-1]
    def select(self,indices):return Route(self.xyz[indices],self.quat[indices])
    def at(self,s):
        B=self.xyz.shape[0];ss=s.reshape(B,-1).clamp_min(0).minimum(self.length[:,None])
        i=torch.searchsorted(self.s.contiguous(),ss.contiguous(),right=True).sub(1).clamp(0,self.xyz.shape[1]-2)
        rows=torch.arange(B,device=s.device)[:,None]
        den=self.s[rows,i+1]-self.s[rows,i]
        t=(ss-self.s[rows,i])/torch.where(den>0,den,torch.ones_like(den))
        a,b=self.quat[rows,i],self.quat[rows,i+1]
        b=torch.where((a*b).sum(-1,keepdim=True)<0,-b,b)
        theta=torch.acos((a*b).sum(-1).clamp(-1,1))
        t1,t0=t,1-t
        # sinc ratios are the continuous slerp limit, including identical poses.
        q=(t0*torch.sinc(t0*theta/math.pi)/torch.sinc(theta/math.pi))[...,None]*a+(t1*torch.sinc(t1*theta/math.pi)/torch.sinc(theta/math.pi))[...,None]*b
        pos=self.xyz[rows,i]*(1-t[...,None])+self.xyz[rows,i+1]*t[...,None]
        T=torch.eye(4,device=s.device,dtype=s.dtype).expand(*ss.shape,4,4).clone();T[...,:3,:3]=quat_matrix(q);T[...,:3,3]=pos
        return T.reshape(*s.shape,4,4)
