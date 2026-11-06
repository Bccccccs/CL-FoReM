"""Read-only natural-computation observer. Never samples, solves or forwards.

The disabled path is the production computation with empty hooks. Raw IK values
are captured before the existing hold; collision witnesses unsupported by the
original boolean API remain unknown. Full tensor windows are evaluation only.
"""
import contextlib
import hashlib
import json
from pathlib import Path
import time

OBSERVER = None


def hook(name, *args):
    if OBSERVER is not None:
        getattr(OBSERVER, name)(*args)


def plain(x):
    if hasattr(x, 'detach'): return x.detach().cpu().tolist()
    if isinstance(x, dict): return {k: plain(v) for k,v in x.items()}
    if isinstance(x, (tuple,list)): return [plain(v) for v in x]
    if hasattr(x, '__dict__'): return plain(vars(x))
    return x


def digest(x):
    def canonical(v):
        if hasattr(v,'detach'):
            t=v.detach().cpu().contiguous()
            return dict(tensor_dtype=str(t.dtype),shape=list(t.shape),bytes_sha256=hashlib.sha256(t.numpy().tobytes()).hexdigest())
        if isinstance(v,dict):return {k:canonical(item) for k,item in v.items()}
        if isinstance(v,(list,tuple)):return [canonical(item) for item in v]
        if hasattr(v,'__dict__'):return canonical(vars(v))
        return v
    return hashlib.sha256(json.dumps(canonical(x),sort_keys=True,separators=(',',':')).encode()).hexdigest()


@contextlib.contextmanager
def observing(observer):
    global OBSERVER
    if OBSERVER is not None: raise RuntimeError('observer already active')
    OBSERVER = observer
    try: yield observer
    finally: OBSERVER = None


class Observer:
    def __init__(self, output, identity, *, enabled=True, guard=None):
        self.output=Path(output); self.output.mkdir(parents=True,exist_ok=False)
        self.identity=identity; self.enabled=enabled; self.guard=guard or (lambda:None)
        self.env=None; self.jobs=[]; self.segment=[]; self.action=[]
        self.first=[]; self.episode_action=[]; self.windows={}; self.previous={}; self.pending_next=set()
        self.last_input=None; self.current_core=None; self.raw_ik=None
        self.finishes={}; self.first_summary={}; self.inference=[]; self.phase='idle'
        self.stream=(self.output/'events.jsonl').open('xb',buffering=0)

    def emit(self,event,**data):
        if not self.enabled:return
        self.guard();payload=(json.dumps(dict(event=event,identity=self.identity,**plain(data)),sort_keys=True)+'\n').encode()
        reserve_write(self.output/'events.jsonl',len(payload),True);self.stream.write(payload)

    def attach(self,env,jobs):
        self.env=env; self.jobs=jobs; self.segment=[0]*len(jobs);self.action=[0]*len(jobs)
        self.first=[False]*len(jobs);self.episode_action=[0]*len(jobs);self.windows={};self.previous={};self.pending_next=set()
        self.finishes={};self.first_summary={}

    def key(self,i):
        j=self.jobs[i]
        return {k:j[k] for k in ('map_id','seed','stream_index','role','source_split')} | {'proposal_seed':self.env.proposal_seeds[i]}

    def policy_input(self, observation, m, v):
        if self.enabled:self.last_input=(observation,{k:x.detach() for k,x in {'map':m,'vector':v}.items()})

    def candidates_before(self,env,ids):
        if self.enabled:self.candidate_rng=[digest(env.streams.for_env(i).other.bit_generator.state) for i in ids.tolist()]

    def candidates_after(self,env,ids,generated,slots):
        if not self.enabled:return
        for row,i in enumerate(ids.tolist()):
            self.emit('candidates',case=self.key(i),segment=self.segment[i]+1,generated={k:getattr(generated,k)[row] if getattr(generated,k) is not None else None for k in ('pose','mask','progress','inplace')},info={k:(v[row] if hasattr(v,'ndim') and v.ndim and v.shape[0]==len(ids) else v) for k,v in generated.info.items()},selected_slot=int(slots[row]),rng_before=self.candidate_rng[row],rng_after=digest(env.streams.for_env(i).other.bit_generator.state),state={k:getattr(env.core.state,k)[i] for k in ('base','q','s')})

    def begin_before(self,c,candidate,mask):
        if not self.enabled:return
        self.begin_ids=c._mask(mask).nonzero().flatten().tolist()
        for i in self.begin_ids:
            self.segment[i]+=1;self.action[i]=0
            self.emit('begin_before',case=self.key(i),segment=self.segment[i],candidate={k:getattr(candidate,k)[i] for k in ('pose','progress','inplace')},state={k:getattr(c.state,k)[i] for k in ('base','q','s')},stalls=int(c.stalls[i]))

    def begin_after(self,c):
        if not self.enabled:return
        for i in self.begin_ids:
            self.emit('begin_after',case=self.key(i),segment=self.segment[i],candidate={k:getattr(c.candidate,k)[i] for k in ('pose','progress','inplace')},cap=c.cap[i],done=c.done[i],reason=c.reason[i],stalls=c.stalls[i],search_info=c.search_info,state={k:getattr(c.state,k)[i] for k in ('base','q','s')})

    def step_start(self,c,observation,raw,u,w,v):
        if not self.enabled:return
        self.phase='step';self.current_core=c;self.raw_ik=None
        if self.last_input is None:raise RuntimeError('natural actor input missing')
        obs,pre=self.last_input
        for i in (~c.done).nonzero().flatten().tolist():
            self.action[i]+=1;self.episode_action[i]+=1
            previous=self.windows.get(i);self.previous[i]=previous
            self.windows[i]=dict(case=self.key(i),segment=self.segment[i],action=self.action[i],episode_action=self.episode_action[i],state={k:getattr(c.state,k)[i].detach().clone() for k in ('base','q','s')},candidate={k:getattr(c.candidate,k)[i].detach().clone() for k in ('pose','progress','inplace')},queue=c.queue[i].detach().clone(),visible_previous=c.visible_previous[i].detach().clone(),observation={k:x[i].detach().clone() for k,x in obs.items()},preprocessed={k:x[i].detach().clone() for k,x in pre.items()},raw_action=raw[i].detach().clone(),execution=dict(u=u[i].detach().clone(),omega=w[i].detach().clone(),v=v[i].detach().clone()))
            if i in self.pending_next:
                self.snapshot(i,'next',self.windows[i]);self.pending_next.remove(i)

    def ik_pre_hold(self,kin,q,result,previous):
        if self.enabled and self.phase=='step':
            self.raw_ik=dict(q=q.detach().clone(),accepted=result.accepted.detach().clone(),status=result.status.detach().clone(),branch=result.branch.detach().clone(),exact=result.exact.detach().clone(),position_m=result.position.detach().clone(),cbl=result.cbl.detach().clone(),angle_rad=result.angle.detach().clone(),held=(~result.accepted).detach().clone())

    def snapshot(self,i,label,window,extra=None):
        import torch
        if window is None:
            self.emit('input_window',case=self.key(i),label=label,available=False,reason='t-1 absent');return
        item=dict(window=window,extra=extra)
        name=f"{self.jobs[i]['role']}-{self.jobs[i]['map_id']}-{self.jobs[i]['seed']}-{label}.pt"
        target=self.output/name
        if target.exists():raise RuntimeError('duplicate full input snapshot')
        with BudgetFile(target,'xb',diagnostic=True) as destination:torch.save(item,destination)
        self.emit('input_window',case=self.key(i),label=label,available=True,path=name,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),fields={k:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(v.detach().cpu().contiguous().numpy().tobytes()).hexdigest()) for k,v in window['preprocessed'].items()})

    def substep(self,c,loc):
        if not self.enabled:return
        for i in (loc['pending']&loc['failed']).nonzero().flatten().tolist():
            if self.first[i]:continue
            self.first[i]=True;self.pending_next.add(i)
            summary=dict(case=self.key(i),segment=self.segment[i],action=self.action[i],episode_action=self.episode_action[i],accepted_action_prefix=self.episode_action[i]-1,substep=loc['_'],attempted=True,committed=bool(loc['commit'][i]),pending=bool(loc['pending'][i]),failed=bool(loc['failed'][i]),kind=int(loc['kind'][i]),trialbase=loc['trialbase'][i],trials=loc['trials'][i],target_tcp=loc['target_tcp'][i],ik={k:getattr(loc['ik'],k)[i] for k in loc['ik'].__dataclass_fields__},raw_ik=None if self.raw_ik is None else {k:v[i] for k,v in self.raw_ik.items()},collision={k:getattr(loc['coll'],k)[i] for k in ('base','arm','self_collision','any')},collision_witness='unknown: original boolean API has no witness',scan_visibility='unknown: original renderer does not retain per-object visibility',state={k:getattr(c.state,k)[i] for k in ('base','q','s')})
            self.first_summary[i]=plain(summary)
            self.emit('first_rejection',**summary)
            extra=dict(global_observed=c.grid.observed[i].detach().clone(),global_height=c.grid.height[i].detach().clone(),global_timestamp=c.grid.timestamp[i].detach().clone(),geometry_provenance=self.env.scenes.scenes[i].provenance(),grid_encoding=dict(crop_size=128,cell_m=.05,global_origin_xy_m=[-5,-5],global_size=[200,200],crop_center_index=64,crop_cell_center_offset=.5,height_landing_positive_threshold_m=.05,height_quantization_m=.01,height_uint8_clamp=[0,255]),witness='unknown')
            self.snapshot(i,'previous',self.previous.get(i));self.snapshot(i,'first',self.windows[i],extra)

    def finish(self,c,loc):
        if not self.enabled:return
        for i in loc['ended'].nonzero().flatten().tolist():
            record=dict(case=self.key(i),segment=self.segment[i],action=self.action[i],success=bool(loc['success'][i]),strict_success=bool(c.strict_success[i]),d_m=float(loc['d'][i]),cbl_rotation=float(loc['r'][i]),route_complete=bool(c.state.s[i]==c.route.length[i]),s=float(c.state.s[i]),length=float(c.route.length[i]),failures=int(c.failures[i]),stalls=int(c.stalls[i]),stuck=bool(loc['stuck'][i]),arrived=bool(c.arrived[i]),reason=int(c.reason[i]),decisions=int(c.decisions[i]),time_s=float(c.time[i]),attempt_time_s=float(c.attempt_time[i]),terminated=bool(c.terminated[i]),truncated=bool(c.truncated[i]),trigger_masks=dict(success=bool(loc['success'][i]),fail_limit=bool(c.failures[i]>=c.failure_limit),stall_limit=bool(c.stalls[i]>=5),decision_limit=bool(c.decisions[i]>=150),time_limit=bool((c.time if c.failure_mode=='terminal' else c.attempt_time)[i]>=200)))
            self.finishes[i]=record;self.emit('segment_finish',**record)

    def step_end(self,c,tr):
        if not self.enabled:return
        for i in tr.active.nonzero().flatten().tolist():
            self.emit('action_end',case=self.key(i),segment=self.segment[i],action=self.action[i],episode_action=self.episode_action[i],attempted=tr.attempted[i],committed=tr.committed[i],state={k:getattr(c.state,k)[i] for k in ('base','q','s')},rho=(c.state.base[i,:2]-c.candidate.pose[i,:2]).norm(),yaw=c.state.base[i,2],s=c.state.s[i],reason=tr.reason[i],arrived=c.arrived[i],failures=c.failures[i],stalls=c.stalls[i])
        self.phase='idle';self.current_core=None

    def episode_fields(self,i):
        if not self.enabled:return {}
        record=self.finishes.get(i)
        if record is None:raise RuntimeError('original finish observation absent')
        return dict(original_success=record['success'],original_finish=record,first_rejection=self.first_summary.get(i),first_rejection_present=self.first[i],stalls=record['stalls'],attempt_time_s=record['attempt_time_s'],decisions=record['decisions'],unavailable_next_action=i in self.pending_next)

    def close(self):
        self.stream.flush();self.stream.close()


OUTPUT_BUDGET = None


class OutputBudget:
    """Conservative write-before-byte admission, shared by synchronous writers.

    Every tracked byte is reserved before its write. Periodic scans reconcile
    other small phase/host/review logs; a separately declared 256MiB envelope
    stays unavailable to tracked diagnostic writers for those unmetered files.
    No output is removed and no scientific sample is discarded to gain space.
    """
    def __init__(self, protocol):
        self.protocol=protocol;self.total=0;self.diagnostic=0;self.last_scan=0
        self.refresh()

    def refresh(self):
        roots=[Path(self.protocol.get('container_output','/output')),Path(self.protocol.get('container_logs','/runlogs'))]+[Path(p) for p in self.protocol.get('external_output_roots',[])]
        total=diag=0
        for index,root in enumerate(roots):
            if not root.exists():continue
            for p in root.rglob('*'):
                if p.is_file():
                    n=p.stat().st_size;total+=n
                    if index>0 or any('diagnostics' in part for part in p.parts) or p.suffix in ('.json','.jsonl','.txt'):diag+=n
        self.total=total;self.diagnostic=diag;self.last_scan=time.monotonic()

    def reserve(self,path,n,diagnostic=None):
        if n<0:raise ValueError('negative write charge')
        if time.monotonic()-self.last_scan>=self.protocol['poll_s']:self.refresh()
        path=Path(path)
        if diagnostic is None:diagnostic=any('diagnostics' in x for x in path.parts) or path.suffix in ('.json','.jsonl','.txt')
        if self.total+n>self.protocol['max_output_bytes']-self.protocol['unmetered_log_reserve_bytes']:raise OSError('write would exceed total output byte quota/reserve')
        if diagnostic and self.diagnostic+n>self.protocol['max_diagnostic_log_bytes']-self.protocol['unmetered_log_reserve_bytes']:raise OSError('write would exceed diagnostic byte quota/reserve')
        self.total+=n
        if diagnostic:self.diagnostic+=n


def install_output_budget(protocol):
    global OUTPUT_BUDGET
    if OUTPUT_BUDGET is not None:raise RuntimeError('output budget already installed')
    OUTPUT_BUDGET=OutputBudget(protocol)
    return OUTPUT_BUDGET


def reserve_write(path,n,diagnostic=None):
    if OUTPUT_BUDGET is not None:OUTPUT_BUDGET.reserve(path,n,diagnostic)


class BudgetFile:
    def __init__(self,path,mode='wb',diagnostic=None):
        self.path=Path(path);self.file=self.path.open(mode,buffering=0);self.diagnostic=diagnostic
    def write(self,data):
        view=memoryview(data).cast('B')
        total=len(view)
        # Reserve the caller's payload once. Raw FileIO may legally return a
        # positive short count (notably for a single multi-GiB tensor write).
        reserve_write(self.path,total,self.diagnostic)
        offset=0
        while offset<total:
            written=self.file.write(view[offset:])
            if isinstance(written,bool) or not isinstance(written,int) or written<=0 or written>total-offset:
                raise OSError('checkpoint write made no valid byte progress')
            offset+=written
        return total
    def __getattr__(self,name):return getattr(self.file,name)
    def __enter__(self):return self
    def __exit__(self,*args):self.file.close()


def print_record(value):
    import os
    payload=json.dumps(value)
    log=os.environ.get('TASK9_LR_LOG_PATH')
    if log:reserve_write(log,len((payload+'\n').encode()),True)
    print(payload,flush=True)
