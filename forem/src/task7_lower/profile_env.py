"""Bounded E expansion on the real pool; eager/graph paired exact inputs."""
import argparse,copy,json,time,torch
from pathlib import Path
from task7_sim.env import EpisodeEnv
from .training import choose_candidate,drain_history,Timings


def equal(a,b):
    if isinstance(a,dict):return all(equal(v,b[k]) for k,v in a.items())
    return torch.equal(a,b)


def main():
    p=argparse.ArgumentParser();p.add_argument('--E',type=int,required=True);p.add_argument('--sync',action='store_true');p.add_argument('--output',required=True);args=p.parse_args()
    torch.set_num_threads(2)
    report=dict(E=args.E,synchronous=args.sync,versions={})
    snapshots=[]
    for graph in (False,True):
        env=EpisodeEnv(args.E,seed=4718,synchronous=args.sync);env.kin.dls_cuda_graph=graph;tm=Timings()
        with tm.measure('reset'):env.reset()
        ds=targets=active=committed=0;outputs=[]
        for step in range(8):
            with tm.measure('candidates'):choose_candidate(env)
            with tm.measure('observation'):env.core.current_observation()
            if env.core.done.all():continue
            with tm.measure('step'):tr=env.step(torch.zeros(args.E,3,device='cuda')).transition
            for at in env.core.attempts:ds+=int(((at['branch']<0)&at['active']).sum());targets+=int(at['active'].sum())
            active+=int(tr.active.sum());committed+=int(tr.committed.sum())
            outputs.append({k:({n:v.cpu().clone() for n,v in val.items()} if isinstance(val,dict) else val.cpu().clone()) for k,val in vars(tr).items()})
            drain_history(env.core)
        report['versions'][str(graph)]=dict(timings=tm.summary(),active=active,committed=committed,dls=ds,ik=targets,step_throughput=active/sum(tm.values['step']),sampler=env.sampler.stats,maps=env.map_ids,proposal_seeds=env.proposal_seeds,graph_buckets=[key[-1] for key in getattr(env.kin,'_dls_graph_cache',{})])
        snapshots.append(outputs)
        del env;torch.cuda.empty_cache()
    report['exact_fields_equal']=len(snapshots[0])==len(snapshots[1]) and all(equal(a,b) for a,b in zip(*snapshots))
    report['peak_bytes']=torch.cuda.max_memory_allocated()
    Path(args.output).write_text(json.dumps(report,indent=2));print(json.dumps(report));assert report['exact_fields_equal']
if __name__=='__main__':main()
