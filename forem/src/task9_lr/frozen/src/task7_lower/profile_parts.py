"""Additional real-path instrumentation; transfer timings are synchronized
and intentionally separate from uninstrumented throughput in profile_env.
"""
import argparse,copy,json,time,torch,numpy as np
from pathlib import Path
from task7_sim.env import EpisodeEnv
from .training import Timings,choose_candidate,drain_history,without_graph_cache

class CallTimer:
    def __init__(self,original,tm,name):self.original=original;self.tm=tm;self.name=name
    def __call__(self,*a,**kw):
        with self.tm.measure(self.name):return self.original(*a,**kw)
    def __getattr__(self,name):return getattr(self.original,name)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();report={};torch.set_num_threads(2)
    env=EpisodeEnv(16,seed=4718);env.kin.dls_cuda_graph=True;transfers=[];originals={}
    for name in ('as_tensor','tensor'):
        fn=getattr(torch,name);originals[name]=fn
        def wrapper(*args,_fn=fn,**kw):
            host=bool(args) and not torch.is_tensor(args[0]) and str(kw.get('device','')).startswith('cuda')
            if host:torch.cuda.synchronize();start=time.perf_counter()
            out=_fn(*args,**kw)
            if host:
                torch.cuda.synchronize();transfers.append(dict(bytes=out.numel()*out.element_size(),wall_s=time.perf_counter()-start))
            return out
        setattr(torch,name,wrapper)
    tm=Timings()
    try:
        with tm.measure('instrumented_reset'):env.reset()
    finally:
        for name,fn in originals.items():setattr(torch,name,fn)
    report['H2D_reset_calls']=transfers;report['instrumented_reset']=tm.summary()
    with without_graph_cache(env):base=copy.deepcopy(env)
    reference=None
    for threads in (1,2,4):
        torch.set_num_threads(threads);e=copy.deepcopy(base);c=e.core;tm=Timings()
        c.kin.solve_world=CallTimer(c.kin.solve_world,tm,'IK')
        c.collision=CallTimer(c.collision,tm,'collision')
        c.renderer=CallTimer(c.renderer,tm,'render')
        c.observe=CallTimer(c.observe,tm,'observation_build')
        c.grid.update=CallTimer(c.grid.update,tm,'grid_update')
        c.grid.crop=CallTimer(c.grid.crop,tm,'grid_crop')
        outputs=[]
        for step in range(12):
            with tm.measure('candidates'):choose_candidate(e)
            if c.done.all():continue
            with tm.measure('step'):tr=e.step(torch.zeros(16,3,device='cuda')).transition
            outputs.append({k:({n:v.cpu().clone() for n,v in x.items()} if isinstance(x,dict) else x.cpu().clone()) for k,x in vars(tr).items()})
            drain_history(c)
        from .profile_env import equal
        if reference is None:reference=outputs
        exact=len(reference)==len(outputs) and all(equal(x,y) for x,y in zip(reference,outputs))
        report[str(threads)]=dict(timings=tm.summary(),exact=exact);assert exact
        del e;torch.cuda.empty_cache()
    Path(a.output).write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
