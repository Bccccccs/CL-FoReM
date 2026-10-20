#!/usr/bin/env python3
"""Task7.6 benchmark-only additional independent checks and overhead prototype."""
import json, time
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from bench_task7_ik import Model,fk,residual,analytic,solve,checked,measure,dump,sha,stats,LOW,HIGH,PI
ROOT=Path('/root/mm_husky_ws');OUT=ROOT/'results/task7/t7.6-bench-20261020-r7'
def main():
    start=time.perf_counter();torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.set_grad_enabled(False);OUT.mkdir(parents=True,exist_ok=True)
    model=Model(ROOT/'results/task7/t7.6-bench-20261020-r1/model.urdf');d=np.load(ROOT/'results/task7/t7.6-bench-20261020-r1/inputs.npz');result={}
    target=torch.tensor(d['target']);prev=torch.tensor(d['prev']);q=torch.tensor(d['q'])
    # True first solver call for each method/device/dtype in this process.
    # Import, context creation and upload are measured separately/excluded as labeled.
    result['cold_solver_calls']=[]
    for dev,dtype in [('cpu',torch.float64),('cuda',torch.float64),('cuda',torch.float32)]:
        before=time.perf_counter();tt=target[1000:1013].to(device=dev,dtype=dtype);ss=prev[1000:1013].to(device=dev,dtype=dtype)
        if dev=='cuda':torch.cuda.synchronize()
        prep=time.perf_counter()-before
        for method in ['analytic','dls']:
            if dev=='cuda':
                a,b=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True);a.record()
            c=time.process_time();t=time.perf_counter();solve(tt,ss,method)
            if dev=='cuda':b.record();torch.cuda.synchronize()
            result['cold_solver_calls'].append({'device':dev,'dtype':str(dtype),'method':method,'batch':13,'first_solver_wall_s':time.perf_counter()-t,'first_solver_process_cpu_s':time.process_time()-c,'first_solver_cuda_s':a.elapsed_time(b)/1000 if dev=='cuda' else None,'input_prepare_context_upload_s':prep,'warm':measure(lambda:solve(tt,ss,method),dev,20 if method=='analytic' else 8)})
    def selection(tt,ss):
        sol,v=analytic(tt,ss);p,r=residual(fk(sol),tt[:,None]);low=torch.tensor(LOW,device=tt.device,dtype=tt.dtype);high=-low
        valid=v&(p<=1e-5)&(r<=1e-5)&(sol>=low).all(-1)&(sol<=high).all(-1)
        distances=((sol-ss[:,None])**2).sum(-1); idx=distances.masked_fill(~valid,float('inf')).argmin(-1);ok=valid.any(-1)
        return idx.cpu().numpy(),ok.cpu().numpy(),sol.cpu().double().numpy(),valid.cpu().numpy(),distances.cpu().numpy()
    bi,bo,bs,bv,bd=selection(target,prev); result['branch_id_agreement']=[]
    for dev in ['cpu','cuda']:
        for dtype in [torch.float64,torch.float32]:
            ii,oo,ss,vv,dd=selection(target.to(device=dev,dtype=dtype),prev.to(device=dev,dtype=dtype));common=oo&bo
            np.savez_compressed(OUT/f'branch_{dev}_{dtype}.npz',index=ii,ok=oo,q=ss,valid=vv,distance_squared=dd)
            result['branch_id_agreement'].append({'device':dev,'dtype':str(dtype),'common_n':int(common.sum()),'same_branch_id_rate':float((ii[common]==bi[common]).mean()),'by_group':{str(g):{'n_common':int((common&(d['label']==g)).sum()),'disagree':int((common&(d['label']==g)&(ii!=bi)).sum())} for g in np.unique(d['label'])}})
    # Check selected distance independently in numpy; no rounding/fk performed by selector under test.
    z,ok,_,_=solve(target,prev);ok=ok.numpy();zd=((z.numpy()-d['prev'])**2).sum(-1);minimum=np.where(bv,bd,np.inf).min(-1)
    result['nearest_distance_max_error']=float(np.abs(zd[ok]-minimum[ok]).max())
    # Same 1200 samples used by DLS and BioIK.
    ids=np.r_[0:1200];result['analytic_same1200']={}
    for tol in [1e-7,1e-5,1e-3]:
        _,oo,_,_=solve(target[ids],prev[ids],ptol=tol,rtol=tol); result['analytic_same1200'][str(tol)]=int(oo.sum())
    # q_prev-dependent continuity along smooth near-singular reachable FK trajectories.
    rng=np.random.default_rng(78);base=rng.uniform(-1,1,(24,6));base[:,1]=-1.;base[:,2]=1.;base[:,4]=np.tile([0,1e-6,.2],8)
    current=torch.tensor(base);history=[current.numpy().copy()]; failures=[];resids=[]; generated=[]
    for j in range(64):
        qq=base.copy(); qq[:,0]+=.001*(j+1);qq[:,2]+=.0001*(j+1); generated.append(qq)
        tt=torch.tensor(model.fk(qq)); new,oo,pe,re=solve(tt,current);failures.append(~oo.numpy());resids.append(np.stack([pe.numpy(),re.numpy()],-1));current=new;history.append(current.numpy().copy())
    hist=np.stack(history);jumps=np.linalg.norm(np.diff(hist,axis=0),axis=-1)
    np.savez_compressed(OUT/'continuity.npz',q=hist,generated_q=np.stack(generated),failure=np.array(failures),residual=np.array(resids),jump_rad=jumps)
    result['continuity']={'paths':24,'C':64,'failures':int(np.array(failures).sum()),'joint_jump_norm_rad':stats(jumps.ravel()),'note':'24 smooth FK target families; wrist singular/near/regular; failures retained, q held'}
    # URDF Jacobian finite difference: DLS derivative oracle including tool0 orientation.
    qn=rng.uniform(-1,1,(32,6));F,J=fk(torch.tensor(qn),True); fd=np.zeros((32,6,6));h=1e-6
    for i in range(6):
        a=qn.copy();b=qn.copy();a[:,i]+=h;b[:,i]-=h;pa=model.fk(a);pb=model.fk(b)
        fd[:,:3,i]=(pa[:,:3,3]-pb[:,:3,3])/(2*h)
        # Spatial angular derivative from R_plus R_minus^-1.
        fd[:,3:,i]=Rotation.from_matrix(pa[:,:3,:3]@pb[:,:3,:3].transpose(0,2,1)).as_rotvec()/(2*h)
    result['jacobian_urdf_central_difference_max_abs']=float(np.abs(J.numpy()-fd).max())
    assert result['jacobian_urdf_central_difference_max_abs']<1e-7
    # World/base/TCP equation compared with full URDF composition for 10000 poses.
    n=10000;B=np.broadcast_to(np.eye(4),(n,4,4)).copy();B[:,:3,:3]=Rotation.from_euler('z',rng.uniform(-PI,PI,n)).as_matrix();B[:,:3,3]=rng.uniform(-4,4,(n,3));B[:,2,3]=.132
    W=B@model.mount@model.fk(d['q'])@model.tool_tcp
    recovered=np.linalg.inv(B@model.mount)@W@np.linalg.inv(model.tool_tcp)
    pe,re=residual(torch.tensor(recovered),torch.tensor(model.fk(d['q'])));result['world_chain']={'n':n,'position_m':stats(pe.numpy()),'rotation_rad':stats(re.numpy())}
    # Batch path versus truly scalar path oracle, every checkpoint sequential.
    pp=np.load(ROOT/'results/task7/t7.6-bench-20261020-r2/path_B13_C10.npz');tt=torch.tensor(pp['target']);seed=torch.tensor(pp['seed']);lengths=pp['lengths'];batch=seed.clone();scalar=seed.clone();active=np.ones(13,bool);maxdiff=0.;disagreements=0
    for j in range(10):
        zb,ob,_,_=solve(tt[j],batch)
        for i in range(13):
            if active[i] and j<lengths[i]:
                zs,os,_,_=solve(tt[j,i:i+1],scalar[i:i+1]);disagreements+=int(bool(os[0])!=bool(ob[i]));scalar[i]=zs[0]
                if ob[i]:batch[i]=zb[i]
                else:active[i]=False
        maxdiff=max(maxdiff,float((batch-scalar).abs().max()))
    result['scalar_vs_batch_path']={'max_joint_abs_difference_rad':maxdiff,'success_disagreements':disagreements};assert maxdiff<1e-9 and disagreements==0
    # Other checkpoint overhead prototype: exact arc + coordinate conversion only.
    # Does not implement collisions, route interpolation, or rendering; those stay unknown.
    result['overhead']=[]
    for dev in ['cpu','cuda']:
        for batchsize in [1,13,104,416,1664]:
            ss=torch.tensor(d['prev'][1000:1000+batchsize],device=dev);mount=torch.tensor(model.mount,device=dev);tool=torch.tensor(model.tool_tcp,device=dev)
            W=mount@fk(ss)@tool;v=torch.linspace(-.3,.3,batchsize,device=dev,dtype=torch.float64);w=torch.linspace(-1,1,batchsize,device=dev,dtype=torch.float64);dt=.05
            def prototype():
                B=torch.eye(4,device=dev,dtype=torch.float64).expand(batchsize,4,4).clone();a=w*dt;c,s=torch.cos(a),torch.sin(a)
                B[:,0,0]=c;B[:,0,1]=-s;B[:,1,0]=s;B[:,1,1]=c
                B[:,0,3]=v*dt*torch.sinc(a/(2*PI))*torch.cos(a/2);B[:,1,3]=v*dt*torch.sinc(a/(2*PI))*torch.sin(a/2)
                # Rigid inverse explicitly, preserving same transform semantics.
                X=B@mount;Xi=torch.eye(4,device=dev,dtype=torch.float64).expand(batchsize,4,4).clone();Xi[:,:3,:3]=X[:,:3,:3].transpose(-1,-2);Xi[:,:3,3]=-(Xi[:,:3,:3]@X[:,:3,3,None]).squeeze(-1)
                return Xi@W@torch.linalg.inv(tool)
            row={'kind':'arc_and_target_benchmark_prototype','device':dev,'batch':batchsize,**measure(prototype,dev,30)};result['overhead'].append(row)
    # Data transfer: blocking upload and synchronize, not mixed into device-resident IK.
    cpu=torch.tensor(d['target']);result['transfer_cpu_to_gpu']={'n':len(cpu),'bytes':cpu.numel()*cpu.element_size(),**measure(lambda:cpu.to('cuda'),'cuda',30)}
    result['wall_s']=time.perf_counter()-start;result['script_sha256']=sha(__file__);dump(OUT/'supplement.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
