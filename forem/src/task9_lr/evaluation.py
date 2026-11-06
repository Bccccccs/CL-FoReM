"""Evaluation-only observation, complete write-ahead accounting and matched timing."""
import hashlib
import json
from pathlib import Path
import time
from .diagnostics import Observer, observing, digest, plain, BudgetFile


def guarded_size(protocol):
    roots=[Path(protocol.get('container_output','/output')),Path(protocol.get('container_logs','/runlogs'))]+[Path(p) for p in protocol.get('external_output_roots',[])]
    total=diagnostic=0
    for root in roots:
        if not root.exists():continue
        for p in root.rglob('*'):
            if p.is_file():
                n=p.stat().st_size;total+=n
                if any('diagnostics' in x for x in p.parts) or root in roots[1:] or p.suffix in ('.jsonl','.json','.txt'):diagnostic+=n
    if total+40*1024**3>protocol['max_output_bytes']:raise OSError('output budget plus full-save reserve')
    if diagnostic>protocol['max_diagnostic_log_bytes']:raise OSError('diagnostic/log budget exceeded')
    return total,diagnostic


class ParityObserver(Observer):
    """Same non-intervening verification trace in OFF/ON; detailed recording differs."""
    def __init__(self,*args,parity=False,**kw):
        self.parity=parity;self.parity_rows=[]
        super().__init__(*args,**kw)
    def trace(self,event,c,extra=None):
        if not self.parity:return
        from task7_lower.training import rng_state
        state={k:getattr(c,k) for k in ('state','grid','queue','visible_previous','done','finished','terminated','truncated','failures','stalls','decisions','time','attempt_time','first','strict_success') if hasattr(c,k)}
        state['extra']=extra
        global_rng=rng_state(); numpy=global_rng['numpy'];global_rng['numpy']=[numpy[0],numpy[1].tolist(),*numpy[2:]]
        state['global_rng']=global_rng
        state['episode_rng']=[{k:getattr(s,k).bit_generator.state for k in ('maps','initial','other')} for s in self.env.streams._streams]
        self.parity_rows.append(dict(event=event,sha256=digest(state)))
    def begin_before(self,c,candidate,mask):
        self.trace('begin_before',c,dict(candidate=candidate,mask=mask));super().begin_before(c,candidate,mask)
    def begin_after(self,c):
        self.trace('begin_after',c);super().begin_after(c)
    def step_start(self,c,observation,raw,u,w,v):
        self.trace('action_start',c,dict(observation=observation,raw=raw));super().step_start(c,observation,raw,u,w,v)
    def substep(self,c,loc):
        self.trace('substep',c,{k:loc[k] for k in ('_','pending','failed','kind','trialbase','trials','ik','coll')});super().substep(c,loc)
    def finish(self,c,loc):
        self.trace('finish',c,{k:loc[k] for k in ('ended','success','d','r','stuck','term','trunc')});super().finish(c,loc)
    def step_end(self,c,tr):
        self.trace('action_end',c,tr);super().step_end(c,tr)
    def close(self):
        try:
            if self.parity:
                payload=(json.dumps(self.parity_rows,indent=2)+'\n').encode()
                with BudgetFile(self.output/'parity.json','xb',diagnostic=True) as stream:stream.write(payload)
        finally:super().close()


def evaluate(sac,config,output,*,deadline=None,cancel=None,protocol=None,recording=True,parity=False,final_manifest=None):
    from task8_lower import evaluation as base
    import torch
    last_check=[0.]
    def guard():
        if protocol is not None:
            if time.time()>=__import__('datetime').datetime.fromisoformat(protocol['deadline']).timestamp()-protocol['save_allowance_s']:raise TimeoutError('global deadline/save reserve')
            if time.monotonic()-last_check[0]>=protocol['poll_s']:
                guarded_size(protocol);last_check[0]=time.monotonic()
    target=Path(output); observer=ParityObserver(target.with_suffix('.diagnostics'),dict(arm=config['group'],training_seed=config['seed'],checkpoint=sac.env_steps),enabled=recording,parity=parity,guard=guard)
    return base.evaluate(sac,config,target,deadline=deadline,cancel=cancel,observer=observer,protocol=protocol,final_manifest=final_manifest)
