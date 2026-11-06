"""Read-only task8.9.1 measurement helpers, never imported by production."""
import contextlib
import json
import os
from pathlib import Path
import time
import numpy as np
import torch


class Timings:
    def __init__(self):self.values={};self.events={};self.enabled=True;self.pending=None
    def clear(self):self.values={};self.events={};self.pending=None
    def begin_step(self):self.pending={k:len(v) for k,v in self.values.items()}
    def complete_step(self):self.pending=None
    def rollback_partial(self):
        if self.pending is None:return
        for k in list(self.values):
            n=self.pending.get(k,0)
            self.values[k]=self.values[k][:n];self.events[k]=self.events[k][:n]
            if not n:del self.values[k];del self.events[k]
        self.pending=None
    def samples(self):return {k:dict(wall_s=v,cuda_event_s=self.events[k]) for k,v in self.values.items()}
    @contextlib.contextmanager
    def measure(self,name):
        if not self.enabled:yield;return
        torch.cuda.synchronize();start=time.perf_counter()
        first=torch.cuda.Event(enable_timing=True);last=torch.cuda.Event(enable_timing=True);first.record()
        try:yield
        finally:
            last.record();torch.cuda.synchronize()
            self.values.setdefault(name,[]).append(time.perf_counter()-start)
            self.events.setdefault(name,[]).append(first.elapsed_time(last)/1000.)
    def wrap(self,obj,name,label):
        fn=getattr(obj,name)
        def call(*args,**kwargs):
            with self.measure(label):return fn(*args,**kwargs)
        setattr(obj,name,call)
    def summary(self):
        return {k:dict(n=len(v),sum_s=sum(v),p50_s=float(np.quantile(v,.5)),p95_s=float(np.quantile(v,.95)),max_s=max(v),cuda_event_sum_s=sum(self.events[k])) for k,v in self.values.items()}


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');os.replace(tmp,path)


def prohibit_training():
    calls={'optimizer_constructed':0,'backward_calls':0}
    def optimizer(*a,**kw):calls['optimizer_constructed']+=1;raise RuntimeError('profile forbids optimizer construction')
    def backward(*a,**kw):calls['backward_calls']+=1;raise RuntimeError('profile forbids backward')
    torch.optim.Optimizer.__init__=optimizer
    torch.Tensor.backward=backward
    torch.autograd.backward=backward
    return calls


def runtime():
    import resource
    return dict(pid=os.getpid(),torch=torch.__version__,cuda=torch.version.cuda,physical_gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),device='cuda:0',dtype='torch.float32',gpu=torch.cuda.get_device_name(),threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads(),affinity=sorted(os.sched_getaffinity(0)),env={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')},peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(),peak_host_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,process_cpu_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime)
