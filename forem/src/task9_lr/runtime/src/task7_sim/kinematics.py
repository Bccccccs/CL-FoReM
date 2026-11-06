"""URDF FK and analytic->DLS IK, task7.5 B.R / SRC-0417/0418.
Adapted from bench_task7_ik.py commit 2380ff51c31ac30fc8506ac2dbac5c6cad24d42a.
Analytic equations: ROS-Industrial ur_kin.cpp 06d8b9e2 (see prototype attribution).
No map access. Output metrics refer to returned q, never to the requested target.
"""
import argparse, csv, hashlib, json, os, platform, subprocess, time
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import torch
from task9_lr.diagnostics import hook
from scipy.spatial.transform import Rotation
PI=np.pi
LOW=np.array([-2*PI,-2*PI,-PI,-2*PI,-2*PI,-2*PI]); HIGH=-LOW
A=[0,-.425,-.39225,0,0,0]; D=[.089159,0,0,.10915,.09465,.0823]
ALPHA=[PI/2,0,0,PI/2,-PI/2,0]
def eye(q,shape=None): return torch.eye(4,device=q.device,dtype=q.dtype).expand(*(q.shape[:-1] if shape is None else shape),4,4).clone()
def fk(q,jac=False):
    """Classical UR5 DH with explicit Rz(pi) from URDF base_link to DH base."""
    T=eye(q); T[...,0,0]=-1; T[...,1,1]=-1
    origins=[]; axes=[]
    for i in range(6):
        origins.append(T[...,:3,3]); axes.append(T[...,:3,2])
        c,s=torch.cos(q[...,i]),torch.sin(q[...,i]); ca,sa=np.cos(ALPHA[i]),np.sin(ALPHA[i])
        H=eye(q); H[...,0,0]=c; H[...,0,1]=-s*ca; H[...,0,2]=s*sa; H[...,0,3]=A[i]*c
        H[...,1,0]=s; H[...,1,1]=c*ca; H[...,1,2]=-c*sa; H[...,1,3]=A[i]*s
        H[...,2,0]=0; H[...,2,1]=sa; H[...,2,2]=ca; H[...,2,3]=D[i]
        T=T@H
    if not jac: return T
    J=torch.stack([torch.cat([torch.linalg.cross(z,T[...,:3,3]-p),z],-1) for p,z in zip(origins,axes)],-1)
    return T,J
class Model:
    """URDF origin*axis-angle recursion; does not use DH constants."""
    def __init__(self,path):
        root=ET.parse(path).getroot(); self.joints={}; self.indices={}
        names=['shoulder_pan','shoulder_lift','elbow','wrist_1','wrist_2','wrist_3']
        for i,n in enumerate(names): self.indices['ur5_'+n+'_joint']=i
        self.limits=[]
        for j in root.findall('joint'):
            ori=j.find('origin'); H=np.eye(4)
            if ori is not None:
                H[:3,:3]=Rotation.from_euler('xyz',list(map(float,ori.get('rpy','0 0 0').split()))).as_matrix()
                H[:3,3]=list(map(float,ori.get('xyz','0 0 0').split()))
            axis=j.find('axis'); axis=np.array(list(map(float,axis.get('xyz','1 0 0').split()))) if axis is not None else np.array([1.,0,0])
            self.joints[j.find('child').get('link')]=(j.find('parent').get('link'),H,axis,j.get('name'),j.get('type'))
        for n in self.indices:
            j=root.find("joint[@name='%s']"%n); self.limits.append([float(j.find('limit').get(k)) for k in ['lower','upper']])
        self.mount=self.transform('ur5_base_link','base_link',np.zeros((1,6)))[0]
        tool=self.transform('ur5_tool0','ur5_wrist_3_link',np.zeros((1,6)))[0]
        grip=self.transform('gripper_base_link','ur5_wrist_3_link',np.zeros((1,6)))[0]
        tcp=np.eye(4); tcp[0,3]=.15
        self.tool_tcp=np.linalg.inv(tool)@grip@tcp
    def transform(self,tip,base,q):
        chain=[]
        while tip!=base:
            parent,H,axis,n,typ=self.joints[tip]; chain.append((H,axis,n,typ)); tip=parent
        T=np.broadcast_to(np.eye(4),(len(q),4,4)).copy()
        for H,axis,n,typ in reversed(chain):
            T=T@H
            if n in self.indices:
                R=np.broadcast_to(np.eye(4),(len(q),4,4)).copy()
                R[:,:3,:3]=Rotation.from_rotvec(q[:,self.indices[n],None]*axis).as_matrix(); T=T@R
        return T
    def fk(self,q): return self.transform('ur5_tool0','ur5_base_link',q)
def residual(X,Y):
    p=torch.linalg.vector_norm(X[...,:3,3]-Y[...,:3,3],dim=-1)
    R=X[...,:3,:3].transpose(-1,-2)@Y[...,:3,:3]
    v=torch.stack([R[...,2,1]-R[...,1,2],R[...,0,2]-R[...,2,0],R[...,1,0]-R[...,0,1]],-1)/2
    c=(R.diagonal(dim1=-2,dim2=-1).sum(-1)-1)/2
    return p,torch.atan2(torch.linalg.vector_norm(v,dim=-1),c)
def analytic(target,prev):
    """Eight shoulder/wrist/elbow branches; singular wrist q6 uses previous q6.
    Out-of-domain acos is masked, never promoted to feasible by clamping.
    Per-joint 2pi lifts are chosen nearest prev within finite software limits.
    """
    T=target.clone(); T[:,:2,:]=-T[:,:2,:] # Rz(pi)^-1 to DH base
    t=lambda i,j:T[:,i,j,None,None,None]
    T00,T01,T02,T03=[t(0,j) for j in range(4)]
    T10,T11,T12,T13=[t(1,j) for j in range(4)]
    T20,T21,T22,T23=[t(2,j) for j in range(4)]
    d1,d4,d5,d6=D[0],D[3],D[4],D[5]; a2,a3=A[1:3]
    aa=d6*T12-T13; bb=d6*T02-T03; rr=aa*aa+bb*bb
    eps=1e-8 # official singular/domain snap, not success tolerance
    ac=torch.acos((d4/torch.sqrt(rr.clamp_min(1e-30))).clamp(-1,1)); at=torch.atan2(-bb,aa)
    signs=torch.tensor([1.,-1.],device=T.device,dtype=T.dtype)
    q1=at+ac*signs.view(1,2,1,1)
    shoulder=(rr>=d4*d4-eps)
    c1,s1=torch.cos(q1),torch.sin(q1)
    div=(T03*s1-T13*c1-d4)/d6
    q5=torch.acos(div.clamp(-1,1))*signs.view(1,1,2,1)
    wrist=div.abs()<=1+eps
    c5,s5=torch.cos(q5),torch.sin(q5)
    sg=torch.where(s5>=0,1.,-1.)
    q6=torch.atan2(sg*-(T01*s1-T11*c1),sg*(T00*s1-T10*c1))
    q6=torch.where(s5.abs()<eps,prev[:,5,None,None,None],q6)
    c6,s6=torch.cos(q6),torch.sin(q6)
    xx=-s5*(T02*c1+T12*s1)-c5*(s6*(T01*c1+T11*s1)-c6*(T00*c1+T10*s1))
    xy=c5*(T20*c6-T21*s6)-T22*s5
    px=d5*(s6*(T00*c1+T10*s1)+c6*(T01*c1+T11*s1))-d6*(T02*c1+T12*s1)+T03*c1+T13*s1
    py=T23-d1-d6*T22+d5*(T21*c6+T20*s6)
    c3=(px*px+py*py-a2*a2-a3*a3)/(2*a2*a3)
    q3=torch.acos(c3.clamp(-1,1))*signs.view(1,1,1,2)
    elbow=c3.abs()<=1+eps
    den=a2*a2+a3*a3+2*a2*a3*c3; den=torch.where(den.abs()<1e-30,torch.full_like(den,1e-30),den)
    aa=a2+a3*c3; bb=a3*torch.sin(q3)
    q2=torch.atan2((aa*py-bb*px)/den,(aa*px+bb*py)/den)
    c23,s23=torch.cos(q2+q3),torch.sin(q2+q3)
    q4=torch.atan2(c23*xy-s23*xx,xx*c23+xy*s23)
    shape=(len(T),2,2,2)
    sol=torch.stack([q.expand(shape) for q in [q1,q2,q3,q4,q5,q6]],-1).reshape(-1,8,6)
    low=torch.as_tensor(LOW,device=T.device,dtype=T.dtype); high=-low
    # Integer lift interval; closest actual finite-turn representative, no modulo distance.
    kmin=torch.ceil((low-sol)/(2*PI)); kmax=torch.floor((high-sol)/(2*PI))
    k=torch.round((prev[:,None,:]-sol)/(2*PI)); k=torch.maximum(kmin,torch.minimum(kmax,k))
    sol=sol+2*PI*k
    valid=(shoulder&wrist&elbow).expand(shape).reshape(-1,8)&(kmin<=kmax).all(-1)&torch.isfinite(sol).all(-1)
    return sol,valid

from dataclasses import dataclass

@dataclass
class IKResult:
    q:torch.Tensor
    accepted:torch.Tensor
    position:torch.Tensor
    cbl:torch.Tensor
    angle:torch.Tensor
    branch:torch.Tensor
    exact:torch.Tensor
    status:torch.Tensor # 0 exact, 1 accepted DLS, 2 residual rejected, 3 nonfinite

def metrics(a,b):
    d,angle=residual(a,b)
    R=a[...,:3,:3].transpose(-1,-2)@b[...,:3,:3]
    # 1-(qa dot qb)^2 = (3-trace(R))/4, dimensionless, not radians.
    r=((3-R.diagonal(dim1=-2,dim2=-1).sum(-1))/4).clamp(0,1)
    return d,r,angle

def base_transform(base):
    T=torch.eye(4,device=base.device,dtype=base.dtype).expand(*base.shape[:-1],4,4).clone()
    c,s=base[...,2].cos(),base[...,2].sin()
    T[...,0,0]=c;T[...,0,1]=-s;T[...,1,0]=s;T[...,1,1]=c
    T[...,:2,3]=base[...,:2]
    return T

class Kinematics:
    def __init__(self,urdf=None):
        if urdf is None:urdf=Path(__file__).resolve().parents[2]/'config/task7/model.urdf'
        self.model=Model(urdf)
        self.tool_tcp=torch.from_numpy(self.model.tool_tcp)
        self.joint_low=torch.from_numpy(LOW) # cached device constant for opt-in DLS graph capture
        # URDF base_footprint is the world floor frame; no rounded ground offset.
        M=self.model.transform('ur5_base_link','base_footprint',np.zeros((1,6)))[0]
        self.mount=torch.from_numpy(M)
        self._fixed_cache={}
        self.body_mount=torch.from_numpy(self.model.transform('base_link','base_footprint',np.zeros((1,6)))[0])
    def fixed(self,name,reference):
        key=(name,reference.device,reference.dtype)
        if key not in self._fixed_cache:
            self._fixed_cache[key]=torch.linalg.inv(self.fixed("tool_tcp",reference)) if name=="tool_tcp_inverse" else getattr(self,name).to(reference)
        return self._fixed_cache[key]
    def world_tcp(self,base,q):return base_transform(base)@self.fixed("mount",q)@fk(q)@self.fixed("tool_tcp",q)
    def solve_world(self,base,target,prev,robot=None):
        # robot (task7.18.6/SRC-0915): optional RobotGeometry; when given, the analytic branch choice avoids branches
        # that self-collide or touch the ground (robot geometry only, never the environment).
        target_arm=torch.linalg.solve(base_transform(base)@self.fixed("mount",prev),target)
        return self.solve_tcp_in_arm(target_arm,prev,base=base,robot=robot)
    def _result(self,q,target,branch,exact,finite=None):
        d,r,angle=metrics(fk(q)@self.fixed("tool_tcp",q),target)
        good=torch.isfinite(q).all(-1)&torch.isfinite(d)&torch.isfinite(r)&torch.isfinite(angle)
        if finite is not None:good&=finite
        low=self.fixed("joint_low",q)
        accepted=good&(d<=.1+1e-6)&(r<=.05+1e-6)&(q>=low).all(-1)&(q<=-low).all(-1)
        status=torch.where(~good,3,torch.where(accepted,torch.where(exact,0,1),2))
        return IKResult(q,accepted,d,r,angle,branch,exact,status)
    def dls(self,target,prev):
        # Task7.18 opt-in launch optimisation; default remains the frozen eager
        # path for all other consumers. Bucketing duplicates independent rows.
        if not getattr(self,'dls_cuda_graph',False) or not target.is_cuda:
            return self._dls_eager(target,prev)
        n=len(prev)
        if not n:return self._dls_eager(target,prev)
        capacity=1<<(n-1).bit_length()
        key=(prev.device,prev.dtype,capacity)
        cache=getattr(self,'_dls_graph_cache',None)
        if cache is None:self._dls_graph_cache={};cache=self._dls_graph_cache
        if key not in cache:
            t=target[:1].expand(capacity,-1,-1).clone();q=prev[:1].expand(capacity,-1).clone()
            t[:n]=target;q[:n]=prev
            stream=torch.cuda.Stream(device=prev.device);stream.wait_stream(torch.cuda.current_stream(prev.device))
            with torch.cuda.stream(stream):
                for _ in range(2):self._dls_eager(t,q,capture=True)
            torch.cuda.current_stream(prev.device).wait_stream(stream)
            graph=torch.cuda.CUDAGraph()
            with torch.cuda.graph(graph,stream=stream):out=self._dls_eager(t,q,capture=True)
            cache[key]=(t,q,graph,out)
        t,q,graph,out=cache[key]
        t[:n].copy_(target);q[:n].copy_(prev);graph.replay()
        # Clones prevent a later replay overwriting a returned result.
        return IKResult(**{name:getattr(out,name)[:n].clone() for name in out.__dataclass_fields__})
    def _dls_eager(self,target,prev,capture=False):
        q=prev.clone();low=self.fixed("joint_low",q)
        finite=torch.isfinite(target).all(dim=(-1,-2))&torch.isfinite(q).all(-1)
        safe_target=torch.where(finite[:,None,None],target,fk(q)@self.fixed("tool_tcp",q))
        tool_target=safe_target@self.fixed("tool_tcp_inverse",q)
        best=q.clone(); best_d=metrics(fk(q)@self.fixed("tool_tcp",q),safe_target)[0]
        I=torch.eye(6,device=q.device,dtype=q.dtype)
        for iteration in range(64):
            F,J=fk(q,True);R=tool_target[:,:3,:3]@F[:,:3,:3].transpose(-1,-2)
            v=torch.stack([R[:,2,1]-R[:,1,2],R[:,0,2]-R[:,2,0],R[:,1,0]-R[:,0,1]],-1)/2
            e=torch.cat([tool_target[:,:3,3]-F[:,:3,3],v],-1)
            matrix=J@J.transpose(-1,-2)+.01**2*I
            # solve_ex uses the same LU solution without host error checking,
            # enabling CUDA graph capture; damping makes each finite matrix SPD.
            solved=torch.linalg.solve_ex(matrix,e[...,None],check_errors=False)[0] if capture else torch.linalg.solve(matrix,e[...,None])
            dq=(J.transpose(-1,-2)@solved).squeeze(-1)
            finite&=torch.isfinite(dq).all(-1)
            dq=torch.nan_to_num(dq)*torch.minimum(torch.ones_like(dq[:,:1]),.2/torch.linalg.vector_norm(dq,dim=-1,keepdim=True).clamp_min(torch.finfo(q.dtype).tiny))
            q=torch.maximum(low,torch.minimum(-low,q+dq))
            dist=metrics(fk(q)@self.fixed("tool_tcp",q),safe_target)[0]
            better=dist<best_d;best=torch.where(better[:,None],q,best);best_d=torch.minimum(dist,best_d)
        return self._result(best,target,torch.full_like(best_d,-1,dtype=torch.long),torch.zeros_like(finite),finite)
    def _avoid_collision(self,idx,dist,valid,sol,base,robot):
        """Among N1-valid analytic branches choose the nearest (same distance metric) that neither self-collides nor
        touches the ground; rows with <2 valid branches or only colliding branches keep the original nearest branch."""
        multi=torch.where(valid.sum(-1)>=2)[0]
        if not len(multi):return idx
        row,branch=torch.where(valid[multi]);row=multi[row]
        b=base[row];q=sol[row,branch]
        caps=robot(b,q)
        hit=robot.self_collision(b,caps,q=q)|(caps[...,[2,5]].amin(-1)-caps[...,6]<=0).any(-1)
        free=torch.zeros_like(valid);free[row,branch]=~hit
        masked=dist.masked_fill(~free,float('inf'))
        use=torch.isfinite(masked.min(-1).values)&(valid.sum(-1)>=2)
        return torch.where(use,masked.argmin(-1),idx)
    def solve_tcp_in_arm(self,target,prev,*,base=None,robot=None):
        shape=prev.shape[:-1];p=prev.reshape(-1,6);target=target.reshape(-1,4,4)
        finite=torch.isfinite(target).all(dim=(-1,-2))&torch.isfinite(p).all(-1)
        safe_target=torch.where(finite[:,None,None],target,fk(p)@self.fixed("tool_tcp",p))
        sol,valid=analytic(safe_target@self.fixed("tool_tcp_inverse",p),p)
        d,r,angle=metrics(fk(sol)@self.fixed("tool_tcp",p),safe_target[:,None])
        low=torch.as_tensor(LOW,device=p.device,dtype=p.dtype)
        valid&=finite[:,None]&torch.isfinite(sol).all(-1)&(d<=1e-4)&(angle<=1e-4)&(sol>=low).all(-1)&(sol<=-low).all(-1)
        dist=(sol-p[:,None]).square().sum(-1).masked_fill(~valid,float('inf'))
        idx=dist.argmin(-1);exact=valid.any(-1);rows=torch.arange(len(p),device=p.device)
        if robot is not None and base is not None:idx=self._avoid_collision(idx,dist,valid,sol,base.reshape(-1,3),robot)
        q=torch.where(exact[:,None],sol[rows,idx],p)
        fallback=(~exact)&finite
        if fallback.any():q[fallback]=self.dls(safe_target[fallback],p[fallback]).q
        result=self._result(q,target,torch.where(exact,idx,-1),exact,finite)
        hook('ik_pre_hold',self,q,result,p)
        held=torch.where(result.accepted[:,None],q,p)
        result.q=held;result.position,result.cbl,result.angle=metrics(fk(held)@self.fixed("tool_tcp",p),target)
        for field in result.__dataclass_fields__:
            x=getattr(result,field);setattr(result,field,x.reshape(*shape,*x.shape[1:]))
        return result
