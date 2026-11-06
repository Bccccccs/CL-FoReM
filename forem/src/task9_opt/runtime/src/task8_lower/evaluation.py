"""Fixed 100 cube episodes plus 24 x 4 transfer episodes; no model selection."""
import hashlib
import json
from pathlib import Path
import time
import torch
from task7_lower.training import choose_candidate,drain_history,rng_state,restore_rng,atomic_json
from task7_lower.observation import preprocess
from task7_sim.episode import RandomStreams
from task8_sim.env import PcdEpisodeEnv
from task8_sim.episode import PcdEpisodeSampler,SamplingIncomplete,check_sampling
from task8_sim.primitive_scene import V3_BACKEND,resolve_backend


def resolve_map_backend(config):
    """Config key map_backend (default pcd-voxel-v3). environment_geometry_version, when present, must name the same backend."""
    backend=resolve_backend(config.get('map_backend',V3_BACKEND))
    version=config.get('environment_geometry_version')
    if version is not None and version!=backend:
        raise ValueError(f'environment_geometry_version {version!r} contradicts map_backend {backend!r}')
    return backend


def evaluation_plan(cube,semantic,config,seeds=None):
    entries=sorted((e for e in cube['maps'] if e['split']=='validation'),key=lambda e:e['id'])
    if len(entries)!=100 or len({e['id'] for e in entries})!=100:raise ValueError('exactly 100 unique cube validation maps required')
    if any(sum(e['difficulty']==d for e in entries)!=50 for d in ('sparse','standard')):raise ValueError('validation requires 50 sparse / 50 standard maps')
    maps=sorted(semantic['maps'],key=lambda e:e['id'])
    if len(maps)!=24 or len({e['id'] for e in maps})!=24:raise ValueError('exactly 24 unique semantic transfer maps required')
    if seeds is None:seeds=json.loads(Path(config['evaluation_seeds']).read_text())
    if seeds.get('schema_version')!='task8-eval-seeds-v1':raise ValueError('evaluation seed schema mismatch')
    # Producer v1 uses record.split as the evaluation ROLE. The authoritative
    # semantic manifest retains its source split='smoke'; bind that source by
    # both canonical path and byte hash, rather than weakening ID validation.
    from task9_opt.runtime import ASSET_ROOT
    root=ASSET_ROOT
    semantic_path=Path(config['transfer_pool']).resolve()
    declared=Path(seeds['semantic_manifest'])
    declared=(root/declared).resolve() if not declared.is_absolute() else declared.resolve()
    if declared!=semantic_path:raise ValueError('semantic manifest path identity mismatch')
    raw=semantic_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=seeds['semantic_manifest_sha256']:
        raise ValueError('semantic manifest hash identity mismatch')
    if semantic!=json.loads(raw):raise ValueError('semantic manifest content identity mismatch')
    def jobs(records,assets,count,role,source_split):
        by_id={e['id']:e for e in assets};result=[]
        if len(records)!=len(assets)*count:raise ValueError('evaluation job count mismatch')
        seen=set()
        for record in records:
            key=(record['map_id'],record['episode_index'])
            if key in seen or key[0] not in by_id or key[1] not in range(count):raise ValueError('evaluation job identity mismatch')
            entry=by_id[key[0]]
            if record['split']!=role or entry['split']!=source_split or record.get('stream_index',0)!=0:
                raise ValueError('evaluation seed role/source split/stream mismatch')
            if record.get('source_split',source_split)!=source_split:
                raise ValueError('evaluation explicit source split mismatch')
            seen.add(key);result.append(dict(map_id=key[0],seed=record['episode_seed'],episode_index=key[1],stream_index=0,role=role,source_split=source_split,entry=entry))
        for key in by_id:
            if len({r['seed'] for r in result if r['map_id']==key})!=count:raise ValueError('evaluation seeds not distinct per map')
        return result
    return jobs(seeds['validation'],entries,1,'validation','validation'),jobs(seeds['semantic_transfer'],maps,4,'semantic_transfer','smoke')


class EvaluationStreams(RandomStreams):
    """One independently seeded episode per row, preserving purpose substreams."""
    def __init__(self,jobs):
        if not jobs:raise ValueError('nonempty evaluation batch required')
        if any(job['stream_index']!=0 for job in jobs):raise ValueError('evaluation job stream index must be zero')
        self._streams=[RandomStreams(job['seed'],1).for_env(0) for job in jobs]


def evaluation_environment(jobs,config,pool,device,*,deadline=None,cancel=None):
    backend=resolve_map_backend(config);samplers=[]
    for job in jobs:
        sampler=PcdEpisodeSampler(pool,split=job['entry']['split'],difficulty=None,
            device=device,dtype=torch.float32,kin=None,robot=None,profile=config['profile'],map_backend=backend)
        sampler.entries=[job['entry']];sampler.kin.dls_cuda_graph=config['dls_cuda_graph']
        samplers.append(sampler)
    def factory(i,streams):
        return samplers[i].sample(streams,deadline=deadline,cancel=cancel)
    env=PcdEpisodeEnv(len(jobs),seed=config['validation_seed'],pool=pool,profile=config['profile'],
        device=device,dtype=torch.float32,factory=factory,map_backend=backend)
    # reset passes this SAME per-job object to sampler; choose_candidate consumes
    # its independent .other stream. Row position never enters the job seed.
    env.streams=EvaluationStreams(jobs)
    env.kin.dls_cuda_graph=config['dls_cuda_graph']
    return env


def _action_summary(actions):
    if not actions:return dict(count=0)
    x=torch.cat(actions).double()
    return dict(count=len(x),mean=x.mean(0).tolist(),std=x.std(0,unbiased=False).tolist(),min=x.min(0).values.tolist(),max=x.max(0).values.tolist(),quantiles=torch.quantile(x,torch.tensor([.05,.5,.95],dtype=x.dtype,device=x.device),dim=0).tolist())


@torch.no_grad()
def evaluate(sac,config,output,*,deadline=None,cancel=None):
    saved=rng_state();started=time.monotonic();output=Path(output);all_results={}
    try:
        cube=json.loads(Path(config['pool']).read_text());semantic=json.loads(Path(config['transfer_pool']).read_text())
        val,transfer=evaluation_plan(cube,semantic,config)
        for name,jobs,pool in [('validation',val,config['pool']),('transfer',transfer,config['transfer_pool'])]:
            rows=[];actions=[];segments=reached=failed=timeout=0;failure_types={str(i):0 for i in range(1,5)}
            for offset in range(0,len(jobs),config['validation_environments']):
                check_sampling(deadline,cancel)
                batch_jobs=jobs[offset:offset+config['validation_environments']]
                env=evaluation_environment(batch_jobs,config,pool,sac.device,deadline=deadline,cancel=cancel)
                env.reset(deadline=deadline,cancel=cancel)
                returns=torch.zeros(env.batch,device=sac.device,dtype=torch.float64);discount=torch.ones_like(returns)
                first_q=[None]*env.batch;steps=torch.zeros(env.batch,device=sac.device,dtype=torch.long)
                while not (env.core.terminated|env.core.truncated).all():
                    check_sampling(deadline,cancel)
                    boundary=env.core.done&~(env.core.terminated|env.core.truncated)
                    choose_candidate(env);c=env.core;zero=boundary&c.done
                    reached+=int(zero.sum());segments+=int(zero.sum())
                    if c.done.all():continue
                    observation=c.current_observation();raw=sac.select_action(observation,True)
                    unseen=torch.tensor([q is None for q in first_q],device=sac.device)&~c.done
                    if unseen.any():
                        m,v=preprocess(observation);qs=sac.critic(m,v,raw)
                        for i in torch.where(unseen)[0].tolist():first_q[i]=[float(q[i]) for q in qs]
                    tr=env.step(raw).transition;active=tr.active
                    actions.append(tr.raw_action[active].cpu());returns+=discount*tr.reward.double()*active;discount[active]*=sac.gamma;steps+=active
                    ended=active&tr.done
                    reached+=int((ended&((tr.reason==0)|(tr.reason==1))).sum());failed+=int((ended&(c.failure_kind>0)).sum());timeout+=int((ended&(tr.reason==4)).sum());segments+=int(ended.sum())
                    for k in failure_types:failure_types[k]+=int((active&(c.last_step_failure==int(k))).sum())
                    drain_history(c)
                for i,job in enumerate(batch_jobs):
                    mc=float(returns[i]);q=first_q[i]
                    rows.append(dict(map_id=job['map_id'],seed=job['seed'],stream_index=job['stream_index'],role=job['role'],source_split=job['source_split'],proposal_seed=env.proposal_seeds[i],difficulty=job['entry'].get('difficulty'),strict_success=bool(c.strict_success[i]),terminated=bool(c.terminated[i]),truncated=bool(c.truncated[i]),failures=int(c.failures[i]),time_s=float(c.time[i]),transfers=int(steps[i]),first_Q=q,discounted_MC_return=mc,Q_minus_MC=None if q is None else [v-mc for v in q]))
            all_results[name]=dict(episodes=len(rows),expected_episodes=len(jobs),complete=True,strict_success_rate=sum(r['strict_success'] for r in rows)/len(rows),segments=segments,arrival_rate=reached/segments if segments else 0.,failed_rate=failed/segments if segments else 0.,timeout_rate=timeout/segments if segments else 0.,step_failure_counts=failure_types,actions=_action_summary(actions),rows=rows,used_for_model_selection=False if name=='transfer' else True)
        result=dict(format='task8-lower-evaluation-v1',complete=True,wall_s=time.monotonic()-started,step=sac.env_steps,**all_results)
        atomic_json(output,result);return result
    except (SamplingIncomplete,InterruptedError,TimeoutError):
        atomic_json(output.with_suffix('.incomplete.json'),dict(complete=False,wall_s=time.monotonic()-started,completed=all_results))
        raise
    finally:restore_rng(saved)
