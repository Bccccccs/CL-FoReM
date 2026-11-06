"""Post-trial GPU full-state continuation, saturated-ring I/O and 100-map eval.
Synthetic ring expansion is for byte/IO profiling only, never a training run.
"""
import argparse,gc,hashlib,json,time,torch
from pathlib import Path
from .training import load_checkpoint,save_checkpoint,evaluate,atomic_json,choose_candidate,limited_step,drain_history
from .inference import DeterministicActor


def parameter_digest(sac):
    h=hashlib.sha256()
    for module in (sac.policy,sac.critic,sac.critic_target):
        for p in module.parameters():h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()

def state_digest(value):
    h=hashlib.sha256()
    def visit(x):
        if torch.is_tensor(x):
            h.update(str((x.dtype,tuple(x.shape))).encode());h.update(x.detach().cpu().numpy().tobytes())
        elif isinstance(x,dict):
            for key in sorted(x,key=str):h.update(str(key).encode());visit(x[key])
        elif isinstance(x,(list,tuple)):
            for v in x:visit(v)
        else:h.update(repr(x).encode())
    visit(value);return h.hexdigest()

def continuation(path,*,include_parameters=False):
    sac,r,env,state,cfg=load_checkpoint(path,'cuda')
    initial_state_sha256=state_digest(sac.full_state_dict())
    if (env.core.terminated|env.core.truncated).any():env.reset()
    choose_candidate(env)
    raw=sac.select_action(env.core.current_observation(),False)
    batch=r.sample(256);begin=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
    torch.cuda.synchronize();wall_start=time.perf_counter();begin.record()
    loss=sac.update_from_batch(batch,sac.update_count);end.record();end.synchronize()
    update_wall_s=time.perf_counter()-wall_start;update_gpu_ms=begin.elapsed_time(end)
    tr=None if env.core.done.all() else limited_step(env,raw,1)
    result=dict(initial_state_sha256=initial_state_sha256,update_wall_s=update_wall_s,update_gpu_event_ms=update_gpu_ms,action=raw.cpu(),loss=[float(x) for x in loss],parameter_sha256=parameter_digest(sac),sample_rng=repr(r.rng.getstate()),tr=None if tr is None else {k:({n:v.cpu().clone() for n,v in val.items()} if isinstance(val,dict) else val.cpu().clone()) for k,val in vars(tr).items()})
    if include_parameters:
        from .profile_gpu_repeat import parameters
        result['parameters']=parameters(sac)
    del sac,r,env;gc.collect();torch.cuda.empty_cache();return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--variant',choices=['sync','async'],required=True);p.add_argument('--full-io',action='store_true');a=p.parse_args()
    torch.set_num_threads(2);root=Path(a.root);trial=root/f'pilot-{a.variant}';report={}
    # Preserve historical trial checkpoint bytes. Only attach explicit versions
    # to a separate actor export; weights are verified byte-for-byte unchanged.
    from .observation import VERSION,ACTION_VERSION
    payload=torch.load(trial/'final.actor.pt',map_location='cpu',weights_only=False)
    original={k:v.clone() for k,v in payload['policy'].items()}
    payload.update(action_version=ACTION_VERSION,step=payload['steps'],versions=dict(checkpoint='task7-lower-actor-v1',observation=VERSION,action=ACTION_VERSION,synchronous=payload['synchronous']))
    torch.save(payload,trial/'compatible.actor.pt')
    checked=torch.load(trial/'compatible.actor.pt',map_location='cpu',weights_only=True)
    assert all(torch.equal(v,checked['policy'][k]) for k,v in original.items())
    report['compatible_actor_weights_exact']=True

    x=continuation(trial/'final.pt');y=continuation(trial/'final.pt')
    from .profile_env import equal
    report['resume_exact']=torch.equal(x['action'],y['action']) and x['loss']==y['loss'] and x['parameter_sha256']==y['parameter_sha256'] and x['sample_rng']==y['sample_rng'] and ((x['tr'] is None and y['tr'] is None) or equal(x['tr'],y['tr']))
    report['resume_comparison']=dict(initial_state_equal=x['initial_state_sha256']==y['initial_state_sha256'],initial_state_x=x['initial_state_sha256'],initial_state_y=y['initial_state_sha256'],action_equal=torch.equal(x['action'],y['action']),action_max_abs=float((x['action']-y['action']).abs().max()),loss_x=x['loss'],loss_y=y['loss'],parameter_hash_x=x['parameter_sha256'],parameter_hash_y=y['parameter_sha256'],sample_rng_equal=x['sample_rng']==y['sample_rng'])
    if x['tr'] is not None and y['tr'] is not None:
        details={}
        for key,value in x['tr'].items():
            pairs=value.items() if isinstance(value,dict) else [(key,value)]
            for field,v in pairs:
                other=y['tr'][key][field] if isinstance(value,dict) else y['tr'][key]
                details[key+'.'+field]=dict(equal=torch.equal(v,other),max_abs=float((v.to(torch.float64)-other.to(torch.float64)).abs().max()))
        report['resume_comparison']['transition_fields']=details
    atomic_json(root/f'resume-comparison-{a.variant}.json',report)
    comparison=report['resume_comparison']
    report['state_restore_exact']=comparison['initial_state_equal'] and comparison['action_equal'] and comparison['sample_rng_equal'] and comparison['loss_x']==comparison['loss_y'] and all(v['equal'] for v in comparison.get('transition_fields',{}).values())
    # Keep the stricter GPU trajectory bit test result, including a failure.
    # The unmodified reference also has sub-ULP convolution-update differences
    # (gpu-reference-repeat.json); never add a tolerance or training flag here.
    assert report['state_restore_exact']
    report['resumed_update_timing']=[{k:z[k] for k in ('update_wall_s','update_gpu_event_ms')} for z in (x,y)];del x,y
    if a.full_io:
        sac,r,env,state,cfg=load_checkpoint(trial/'final.pt','cuda');n=len(r)
        import numpy as np,zipfile
        planners=env.sampler.planners
        per_cache=[sum(v.nbytes for v in vars(p).values() if isinstance(v,np.ndarray)) for p in planners.values()]
        report['resource_cache']=dict(planners=len(planners),pool_maps=len(env.sampler.entries),numpy_bytes=sum(per_cache),max_numpy_bytes_per_map=max(per_cache),full_pool_numpy_bound_bytes=max(per_cache)*len(env.sampler.entries))
        with zipfile.ZipFile(trial/'final.pt') as archive:report['trial_pickle_bytes']=sum(x.file_size for x in archive.infolist() if x.filename.endswith('data.pkl'))

        # Duplicate existing encoded bytes; no learned transition or RNG draw.
        for key in ('map_s','map_n','rob_s','rob_n','act','rew','mask'):
            tensor=getattr(r,key)
            for start in range(n,r.capacity,n):tensor[start:min(start+n,r.capacity)]=tensor[:min(n,r.capacity-start)]
        r.size=r.capacity;r.position=0;state['IO_BENCHMARK_SYNTHETIC_RING']=True
        torch.cuda.synchronize();start=time.perf_counter();save_checkpoint(root/'io-benchmark-full.pt',sac,r,env,state,cfg);torch.cuda.synchronize();report['full_checkpoint_save_s']=time.perf_counter()-start
        report['full_checkpoint_bytes']=(root/'io-benchmark-full.pt').stat().st_size
        del sac,r,env;gc.collect();torch.cuda.empty_cache()
        torch.cuda.synchronize();start=time.perf_counter();ss,rr,ee,st,cc=load_checkpoint(root/'io-benchmark-full.pt','cuda');torch.cuda.synchronize();report['full_checkpoint_load_s']=time.perf_counter()-start
        report['full_replay_size']=len(rr);report['full_height_uint8']=str(rr.map_s.dtype);report['synthetic_io_only']=bool(st['IO_BENCHMARK_SYNTHETIC_RING'])
        assert len(rr)==100000 and rr.map_s.dtype==torch.uint8
        del ss,rr,ee;gc.collect();torch.cuda.empty_cache()
    class Adapter:
        device=torch.device('cuda')
        def __init__(self):self.actor=DeterministicActor(trial/'compatible.actor.pt','cuda')
        def select_action(self,observation,deterministic=True):return self.actor(observation)
    cfg=json.loads((trial/'config.json').read_text());actor=Adapter()
    report['validation']=evaluate(actor,cfg,root/f'pilot-validation-{a.variant}.json')
    atomic_json(root/f'finish-{a.variant}.json',report)
    print(json.dumps({k:v if k!='validation' else {n:x for n,x in v.items() if n!='rows'} for k,v in report.items()}))
if __name__=='__main__':main()
