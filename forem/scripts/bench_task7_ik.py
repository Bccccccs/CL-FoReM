#!/usr/bin/env python3
"""TASK7.6 benchmark prototype ONLY; not a task7 environment implementation.
Analytic inverse equations adapted to tensors from ROS-Industrial ur_kin.cpp,
commit 06d8b9e2f5f86aa54f9f2845f11edbc84e2f951e, inverse():197-341.
Independent XML URDF FK is the numerical oracle. SRC-0352/0385/0386.
No collision geometry or environment semantics are supplied by this benchmark.
"""
import argparse, csv, hashlib, json, os, platform, subprocess, time
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import torch
from scipy.spatial.transform import Rotation
PI=np.pi
LOW=np.array([-2*PI,-2*PI,-PI,-2*PI,-2*PI,-2*PI]); HIGH=-LOW
A=[0,-.425,-.39225,0,0,0]; D=[.089159,0,0,.10915,.09465,.0823]
ALPHA=[PI/2,0,0,PI/2,-PI/2,0]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def stats(x):
    x=np.asarray(x); return dict(zip(['p50','p95','p99','max'],map(float,np.quantile(x,[.5,.95,.99,1]))))
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
def checked(sol,valid,target,prev,ptol,rtol):
    p,r=residual(fk(sol),target[:,None,:,:])
    low=torch.as_tensor(LOW,device=sol.device,dtype=sol.dtype); high=-low
    valid=valid&torch.isfinite(p)&torch.isfinite(r)&(p<=ptol)&(r<=rtol)&(sol>=low).all(-1)&(sol<=high).all(-1)
    dist=((sol-prev[:,None,:])**2).sum(-1).masked_fill(~valid,float('inf'))
    idx=dist.argmin(-1); rows=torch.arange(len(sol),device=sol.device); ok=valid.any(-1)
    q=torch.where(ok[:,None],sol[rows,idx],prev)
    # A failure reports residual of held previous state, never fabricates achieved target.
    p,r=residual(fk(q),target)
    return q,ok,p,r
def solve(T,prev,method='analytic',ptol=1e-5,rtol=1e-5):
    if method=='analytic': sol,v=analytic(T,prev)
    else:
        q=prev.clone(); low=torch.as_tensor(LOW,device=q.device,dtype=q.dtype); high=-low
        I=torch.eye(6,device=q.device,dtype=q.dtype)
        for _ in range(64):
            F,J=fk(q,True); R=T[:,:3,:3]@F[:,:3,:3].transpose(-1,-2)
            v=torch.stack([R[:,2,1]-R[:,1,2],R[:,0,2]-R[:,2,0],R[:,1,0]-R[:,0,1]],-1)/2
            # sin(theta) orientation error; global convergence is not assumed.
            e=torch.cat([T[:,:3,3]-F[:,:3,3],v],-1)
            dq=(J.transpose(-1,-2)@torch.linalg.solve(J@J.transpose(-1,-2)+.01**2*I,e[...,None])).squeeze(-1)
            dq=dq*torch.minimum(torch.ones_like(dq[:,:1]),.2/torch.linalg.vector_norm(dq,dim=-1,keepdim=True).clamp_min(1e-30))
            p,r=residual(F,T); active=(p>ptol)|(r>rtol)
            q=torch.where(active[:,None],torch.maximum(low,torch.minimum(high,q+dq)),q)
        sol=q[:,None,:]; v=torch.ones((len(q),1),device=q.device,dtype=torch.bool)
    return checked(sol,v,T,prev,ptol,rtol)
def make_inputs(m,n=10000):
    rng=np.random.default_rng(20261020); q=rng.uniform(LOW,HIGH,(n,6)); labels=np.full(n,'random',dtype='<U20')
    # exact/near wrist and elbow singularities, near limits, unreachable targets.
    q[:200,4]=np.tile([0,1e-9,1e-6,PI-1e-8],50); labels[:200]='wrist_singular'
    q[200:400,2]=np.tile([0,1e-9,PI,-PI],50); labels[200:400]='elbow_singular'
    q[400:600]=np.where(rng.random((200,6))>.5,HIGH-1e-9,LOW+1e-9); labels[400:600]='limit'
    T=m.fk(q); labels[600:800]='unreachable'; T[600:800,0,3]=10
    # shoulder-axis/shoulder tangency family (not all geometrically reachable)
    labels[800:1000]='shoulder_boundary'; T[800:1000,0,3]=0; T[800:1000,1,3]=np.linspace(.10,.12,200)
    prev=np.clip(q+rng.normal(0,.05,q.shape),LOW,HIGH)
    return q,T,prev,labels

def consistency(args,out,m):
    q,T,prev,labels=make_inputs(m)
    qt=torch.tensor(q,dtype=torch.float64); target=torch.tensor(T); seed=torch.tensor(prev)
    p,r=residual(fk(qt),torch.tensor(m.fk(q)))
    # Random-only 10000 samples separately (mixture has boundary substitutions).
    qr=np.random.default_rng(181).uniform(LOW,HIGH,(10000,6)); pr,rr=residual(fk(torch.tensor(qr)),torch.tensor(m.fk(qr)))
    result={'urdf_fk_random_n':len(qr),'fk_position_m':stats(pr.numpy()),'fk_rotation_rad':stats(rr.numpy()),'mixture_fk_position_m':stats(p.numpy()),'mixture_fk_rotation_rad':stats(r.numpy()),'thresholds':[]}
    np.savez_compressed(out/'inputs.npz',q=q,target=T,prev=prev,label=labels,random_q=qr,random_position_error=pr.numpy(),random_rotation_error=rr.numpy())
    assert pr.max()<1e-8 and rr.max()<1e-8, 'FK oracle mismatch; timing prohibited'
    baseline=None
    for method in ['analytic','dls']:
        take=slice(None) if method=='analytic' else np.r_[0:1000,1000:1200]
        tt=target[take]; ss=seed[take]; ll=labels[take]
        for tol in [1e-7,1e-5,1e-3]:
            z,ok,pe,re=solve(tt,ss,method,tol,tol)
            np.savez_compressed(out/f'consistency_{method}_{tol}.npz',q=z.numpy(),ok=ok.numpy(),position=pe.numpy(),rotation=re.numpy(),labels=ll)
            row={'method':method,'position_tol_m':tol,'rotation_tol_rad':tol,'n':len(tt),'ok':int(ok.sum()),'groups':{g:{'n':int((ll==g).sum()),'ok':int(ok.numpy()[ll==g].sum())} for g in np.unique(ll)}}
            result['thresholds'].append(row)
            if method=='analytic' and tol==1e-5: baseline=(z,ok)
    sol,v=analytic(target,qt); branch_p,branch_r=residual(fk(sol),target[:,None])
    _,b_ok,_,_=checked(sol,v,target,qt,1e-5,1e-5)
    # Known generating q is seed: nearest valid branch should reproduce it except singular families.
    near,near_ok,_,_=checked(sol,v,target,qt,1e-5,1e-5)
    np.savez_compressed(out/'branches.npz',q=sol.numpy(),domain_valid=v.numpy(),position=branch_p.numpy(),rotation=branch_r.numpy(),selected=near.numpy(),ok=near_ok.numpy(),distance=np.linalg.norm(near.numpy()-q,axis=-1))
    result['branch_count_domain_hist']={str(i):int((v.sum(-1)==i).sum()) for i in range(9)}
    result['nearest_seed_random_error_rad']=stats(np.linalg.norm(near.numpy()[1000:]-q[1000:],axis=-1))
    result['precision']=[]
    devices=['cpu']+(['cuda'] if torch.cuda.is_available() else [])
    for dev in devices:
        for dtype in [torch.float64,torch.float32]:
            z,ok,pe,re=solve(target.to(device=dev,dtype=dtype),seed.to(device=dev,dtype=dtype))
            zc=z.cpu().double(); oc=ok.cpu(); common=oc&baseline[1]
            p64,r64=residual(torch.tensor(m.fk(zc.numpy())),target)
            dist=torch.linalg.vector_norm(zc-baseline[0],dim=-1)
            np.savez_compressed(out/f'precision_{dev}_{dtype}.npz',q=zc.numpy(),ok=oc.numpy(),position_cpu64=p64.numpy(),rotation_cpu64=r64.numpy(),joint_difference=dist.numpy())
            result['precision'].append({'device':dev,'dtype':str(dtype),'ok':int(oc.sum()),'success_agreement':float((oc==baseline[1]).double().mean()),'common_n':int(common.sum()),'same_selected_q_within_1e-3_rad':float((dist[common]<1e-3).double().mean()),'cpu64_position_m':stats(p64[common].numpy()),'cpu64_rotation_rad':stats(r64[common].numpy()),'accepted_but_cpu64_over_1e-5':int((oc&((p64>1e-5)|(r64>1e-5))).sum())})
    # Boolean success with wrong pose must be rejected.
    z,ok,_,_=checked(seed[:,None],torch.ones((len(seed),1),dtype=torch.bool),target,seed,1e-7,1e-7)
    result['false_boolean_rejected']=int((~ok).sum()); assert torch.equal(z[~ok],seed[~ok])
    dump(out/'consistency.json',result); print(json.dumps(result),flush=True)

def measure(fn,device,reps=20):
    def sync():
        if device=='cuda':torch.cuda.synchronize()
    sync(); t=time.perf_counter(); c=time.process_time(); fn(); sync(); first=time.perf_counter()-t
    for _ in range(3):fn()
    sync(); wall=[]; cpu=[]; gpu=[]
    for _ in range(reps):
        if device=='cuda':
            a,b=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True); a.record()
        c=time.process_time(); t=time.perf_counter(); fn()
        if device=='cuda':b.record()
        sync(); wall.append(time.perf_counter()-t); cpu.append(time.process_time()-c)
        if device=='cuda':gpu.append(a.elapsed_time(b)/1000)
    return {'first_wall_s':first,'wall_s':wall,'process_cpu_s':cpu,'cuda_event_s':gpu,'wall_stats_s':stats(wall),'cpu_stats_s':stats(cpu),'cuda_stats_s':stats(gpu) if gpu else None}

def paths(targets,seed,lengths,method,mode,ptol=1e-5,rtol=1e-5):
    """Sequential checkpoints, independent paths batched; failure holds q.
    mask computes inactive lanes and masks updates; compact gathers active lanes.
    Both preserve prefix-failure semantics; no collision or route claims.
    """
    q=seed.clone(); active=torch.ones(len(q),device=q.device,dtype=torch.bool); first=torch.full_like(lengths,targets.shape[0])
    for j in range(targets.shape[0]):
        eligible=active&(j<lengths)
        if mode=='compact':
            ids=torch.nonzero(eligible).flatten()
            if len(ids)==0:continue
            z,ok,_,_=solve(targets[j,ids],q[ids],method,ptol,rtol)
            bad=ids[~ok]; first[bad]=j; q[ids]=z; active[bad]=False
        else:
            z,ok,_,_=solve(targets[j],q,method,ptol,rtol)
            bad=eligible&~ok; first=torch.where(bad,j,first)
            q=torch.where((eligible&ok)[:,None],z,q); active=active&~bad
    return q,first

def timing(args,out,m):
    prior=Path(args.oracle)/'consistency.json'; gate=json.loads(prior.read_text()); assert gate['fk_position_m']['max']<1e-8
    device=args.device; dtype=torch.float64 if args.dtype=='float64' else torch.float32
    data=np.load(Path(args.oracle)/'inputs.npz'); rows=[]
    # Interleave all categories in every batch >=13, preserve unreachable and boundaries.
    index=np.array([1000,0,200,400,600,800,1100,150,350,550,750,950,1200])
    T=torch.tensor(data['target'][index],device=device,dtype=dtype); seeds=torch.tensor(data['prev'][index],device=device,dtype=dtype)
    for method in ['analytic','dls']:
        for batch in [1,13,104,416,1664]:
            inds=torch.arange(batch,device=device)%13
            tt=T[inds]; ss=seeds[inds]
            z,ok,p,r=solve(tt,ss,method)
            counter=[0]
            def one_call():
                if batch==1:
                    i=counter[0]%13; counter[0]+=1
                    return solve(T[i:i+1],seeds[i:i+1],method)
                return solve(tt,ss,method)
            row={'kind':'ik','method':method,'batch':batch,'n_success':int(ok.sum()),'n_failure':int((~ok).sum()),'device':device,'dtype':args.dtype,'threads':args.threads,'input_note':'13-case cyclic mixture; batch1 cycles all cases across calls; failures retained',**measure(one_call,device,26 if method=='analytic' else 13)}
            row['throughput_ik_per_s']=batch/row['wall_stats_s']['p50']; rows.append(row); print(method,batch,row['wall_stats_s'],flush=True)
    # Sequential world TCP targets converted after moving base via exact arc prototype.
    rng=np.random.default_rng(62)
    for batch in [13,104,416]:
        for C in [10,60]:
            q0=torch.tensor(rng.uniform(-1,1,(batch,6)),device=device,dtype=dtype); q0[:,1]=-1; q0[:,2]=1.2; q0[:,4]=.8
            mount=torch.tensor(m.mount,device=device,dtype=dtype); tool=torch.tensor(m.tool_tcp,device=device,dtype=dtype)
            tcp0=mount@fk(q0)@tool; targets=[]
            v=torch.linspace(-.3,.3,batch,device=device,dtype=dtype); w=torch.linspace(-1,1,batch,device=device,dtype=dtype)
            for j in range(C):
                dt=(j+1)*.05; angle=w*dt
                B=eye(q0); B[:,0,0]=torch.cos(angle); B[:,0,1]=-torch.sin(angle); B[:,1,0]=torch.sin(angle); B[:,1,1]=torch.cos(angle)
                # normalized torch.sinc(x/pi)=sin(x)/x.
                B[:,0,3]=v*dt*torch.sinc(angle/(2*PI))*torch.cos(angle/2); B[:,1,3]=v*dt*torch.sinc(angle/(2*PI))*torch.sin(angle/2)
                targets.append(torch.linalg.inv(B@mount)@tcp0@torch.linalg.inv(tool))
            targets=torch.stack(targets); targets[C//2,::7,0,3]=10 # deterministic path failures
            lengths=1+torch.arange(batch,device=device)%C
            ref=paths(targets,q0,lengths,'analytic','mask')
            compact=paths(targets,q0,lengths,'analytic','compact')
            assert torch.equal(ref[1],compact[1]) and torch.allclose(ref[0],compact[0],atol=1e-10 if dtype==torch.float64 else 1e-5)
            np.savez_compressed(out/f'path_B{batch}_C{C}.npz',target=targets.cpu().numpy(),seed=q0.cpu().numpy(),lengths=lengths.cpu().numpy(),q_mask=ref[0].cpu().numpy(),q_compact=compact[0].cpu().numpy(),first_failure=ref[1].cpu().numpy())
            for mode in ['mask','compact']:
                row={'kind':'path','method':'analytic','mode':mode,'batch':batch,'checkpoints':C,'requested_checkpoints':int(lengths.sum()),'device':device,'dtype':args.dtype,'threads':args.threads,**measure(lambda:paths(targets,q0,lengths,'analytic',mode),device,8)}
                rows.append(row); print('path',batch,C,mode,row['wall_stats_s'],flush=True)
    dump(out/'timing.json',rows)
    with (out/'timing.csv').open('w') as f:
        w=csv.writer(f); w.writerow(['kind','method','mode','batch','C','p50_s','p95_s','p99_s','throughput'])
        for r in rows:w.writerow([r['kind'],r['method'],r.get('mode',''),r['batch'],r.get('checkpoints',''),*[r['wall_stats_s'][p] for p in ['p50','p95','p99']],r.get('throughput_ik_per_s','')])

def main():
    p=argparse.ArgumentParser(); p.add_argument('--phase',choices=['check','timing'],required=True); p.add_argument('--out',required=True); p.add_argument('--urdf',required=True); p.add_argument('--oracle'); p.add_argument('--device',default='cpu'); p.add_argument('--dtype',default='float64'); p.add_argument('--threads',type=int,default=2); args=p.parse_args()
    start=time.perf_counter(); torch.set_num_threads(args.threads); torch.set_num_interop_threads(1); torch.set_grad_enabled(False)
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True); m=Model(args.urdf)
    assert np.array_equal(np.array(m.limits),np.stack([LOW,HIGH],-1))
    meta={'argv':__import__('sys').argv,'script_sha256':sha(__file__),'urdf_sha256':sha(args.urdf),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip() if (Path.cwd()/'.git').exists() else 'see host receipt','platform':platform.platform(),'torch':torch.__version__,'numpy':np.__version__,'cpu_count':os.cpu_count(),'affinity':sorted(os.sched_getaffinity(0)),'torch_threads':torch.get_num_threads(),'torch_interop_threads':torch.get_num_interop_threads(),'env':{k:os.getenv(k) for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','CUDA_VISIBLE_DEVICES']},'mount':m.mount.tolist(),'tool0_tcp':m.tool_tcp.tolist(),'limits':m.limits,'device':args.device,'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,'dh':{'a':A,'d':D,'alpha':ALPHA},'dls':{'iterations':64,'lambda':.01,'joint_step_norm_cap_rad':.2,'orientation_error':'sin(angle)*axis; residual uses geodesic rad'},'pid':os.getpid()}
    dump(out/'metadata.json',meta)
    if args.phase=='check': consistency(args,out,m)
    else:timing(args,out,m)
    dump(out/'exit.json',{'exit_code':0,'wall_s':time.perf_counter()-start,'process_cpu_s':time.process_time()}); print('DONE',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
