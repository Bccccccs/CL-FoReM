"""Same-input measurements for the three authorized optimizations and E scaling."""
import json,time,hashlib
from pathlib import Path
import numpy as np
import torch
from .bench_full import scene,candidates,script,ARTIFACT
from .core import Core,Candidate,rollout

COUNTS={}

def measured_calls():
    original_observe=Core.observe;original_step=Core.step
    def observe(self,*a,**k):
        COUNTS['observe']=COUNTS.get('observe',0)+1
        return original_observe(self,*a,**k)
    def step(self,*a,**k):
        previous=len(self.attempts);tr=original_step(self,*a,**k)
        for attempt in self.attempts[previous:]:
            active=attempt['active'];fallback=(attempt['ik_status']==1)|(attempt['ik_status']==2)
            COUNTS.setdefault('ik',[]).append(active.sum());COUNTS.setdefault('dls',[]).append((active&fallback).sum())
        return tr
    Core.observe=observe;Core.step=step

def profile(label,*,environments=(1,16),reps=5,with_rollout=True):
    measured_calls();rows=[];device='cuda';dtype=torch.float32
    root=ARTIFACT/label;root.mkdir(parents=True,exist_ok=True)
    for E in environments:
        seed,depth=scene(E,device=device,dtype=dtype);poses,progress,inplace=candidates(seed,13)
        def make():return Core(seed.state,seed.route,seed.grid,seed.kin,seed.capsules,seed.collision,synchronous=False,renderer=seed.renderer)
        probe=make();probe.begin(Candidate(poses[:,0],progress[:,0],inplace[:,0]))
        def observe():return probe.observe()
        def body():return probe._body_transform()
        def prepare_execute():
            c=make();target=c.state.base.clone();target[:,0]+=1
            c.begin(Candidate(target,torch.full_like(c.state.s,.03),torch.zeros_like(c.state.s,dtype=torch.bool)))
            return c
        prepared=[None]
        def single():
            c=prepared[0];c.step(torch.zeros(E,3,device=device,dtype=dtype));return c
        def execute():
            c=prepare_execute()
            for j in range(2):
                if c.done.all():break
                c.step(torch.zeros(E,3,device=device,dtype=dtype))
            return c
        def imagine():return rollout(seed.state,seed.route,seed.grid,poses,progress,inplace,script,seed.kin,seed.capsules,synchronous=False)
        for name,fn,items in [('observe',observe,E),('fixed_body_transform',body,E),('execute_one_transition',single,E),('execute_up_to_two_actions',execute,2*E)]+([('rollout_K13_short_segments',imagine,13*E)] if with_rollout else []):
            if name=='execute_one_transition':prepared[0]=prepare_execute()
            fn();torch.cuda.synchronize();lat=[];calls=[];ik=0;dls=0;last=None;commits=[];attempts=[];actual_items=[]
            torch.cuda.reset_peak_memory_stats()
            for repetition in range(reps):
                if name=='execute_one_transition':prepared[0]=prepare_execute()
                COUNTS.clear();torch.cuda.synchronize();start=time.perf_counter();last=fn();torch.cuda.synchronize();lat.append(time.perf_counter()-start)
                calls.append(COUNTS.get('observe',0));ik+=sum(int(x.item()) for x in COUNTS.get('ik',[]));dls+=sum(int(x.item()) for x in COUNTS.get('dls',[]))
                if name.startswith('execute'):
                    commits.append(int(last.committed_total.sum()));attempts.append(int(last.attempted_total.sum()));actual_items.append(sum(int(t.active.sum()) for t in last.transitions))
                else:actual_items.append(items)
            percentiles=dict(zip(['p50','p95','p99','max'],map(float,np.quantile(np.array(lat)*1000,[.5,.95,.99,1]))))
            row=dict(label=label,E=E,K=13 if name.startswith('rollout') else 1,name=name,reps=reps,latency_ms=percentiles,samples_ms=[x*1000 for x in lat],items_per_s=sum(actual_items)/sum(lat),items=sum(actual_items),observe_calls=calls,attempted_active_ik=ik,dls_fallbacks=dls,dls_rate=dls/ik if ik else None,committed_substeps=commits,attempted_substeps=attempts,peak_allocated_bytes=torch.cuda.max_memory_allocated())
            if name.startswith('rollout'):
                torch.save(last.cpu(),root/f'E{E}-fk.pt')
                row['reason_counts']=last[...,1:6].sum(dim=(0,1)).cpu().tolist()
                row['committed_sim_seconds']=last[...,7].sum().item()
            if name.startswith('execute'):
                torch.save(dict(base=last.state.base.cpu(),q=last.state.q.cpu(),s=last.state.s.cpu(),rewards=torch.stack([t.reward for t in last.transitions]).cpu(),mask=torch.stack([t.mask for t in last.transitions]).cpu()),root/f'E{E}-{name}.pt')
            rows.append(row);print(json.dumps(row),flush=True)
            del last
    root=ARTIFACT/label;root.mkdir(parents=True,exist_ok=True)
    record=dict(label=label,torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(0),source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('src/task7_sim').glob('*.py')},robot_config_sha256=hashlib.sha256(Path('config/task7/robot_geometry.json').read_bytes()).hexdigest(),fixture=json.loads((ARTIFACT/'fixture.json').read_text()),scene='16 route knots, full robot/scan snapshot, K13 distinct short endpoints within arrival tolerance; progress .015-.03m; fixed script zeros; no candidate generator or network',notes=['CUDA float32 tensors, synchronized wall time including Python and diagnostic reductions','execution counts actual active transitions; early failures retained','short fixture rates are not long-segment or training performance','initial renderer/init outside transition timing; first warm call excluded','execute_one_transition times only Core.step; prepare Core/begin outside timer; execute_up_to_two_actions includes Core/begin'],measurements=rows)
    (root/'profile.json').write_text(json.dumps(record,indent=2)+'\n')
    return record
