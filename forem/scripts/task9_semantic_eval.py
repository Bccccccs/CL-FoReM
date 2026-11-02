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


from task8_lower.evaluation import evaluation_plan,evaluation_environment,_action_summary,resolve_map_backend

@torch.no_grad()
def evaluate_transfer(sac,config,output,*,deadline=None,cancel=None):
    saved=rng_state();started=time.monotonic();output=Path(output);all_results={}
    try:
        cube=json.loads(Path(config['pool']).read_text());semantic=json.loads(Path(config['transfer_pool']).read_text())
        val,transfer=evaluation_plan(cube,semantic,config)
        for name,jobs,pool in [('transfer',transfer,config['transfer_pool'])]:
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


if __name__=='__main__':
    import argparse,os,sys,traceback
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    from task8_lower.sac import LowerSAC
    from task7_lower.inference import DeterministicActor
    root=Path('/root/mm_husky_ws')
    run=root/f'results/task9/t9-stage2-20261029/B3_5M-seed{args.seed}'
    output=Path(args.output);output.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    torch.set_num_threads(2)
    try:
        cfg=json.loads((run/'config.json').read_text())
        assert cfg['seed']==args.seed and resolve_map_backend(cfg)=='primitive-obb-v1'
        ck=torch.load(run/'final.pt',map_location='cpu',weights_only=False,mmap=True)
        assert ck['state']['steps']==5000000 and ck['config']==cfg
        sac=LowerSAC(74,'cuda',cfg)
        sac.policy.load_state_dict(ck['sac']['policy'])
        sac.critic.load_state_dict(ck['sac']['critic'])
        sac.env_steps=ck['state']['steps']
        actor=DeterministicActor(run/'final.actor.pt','cuda')
        assert actor.synchronous and actor.steps==sac.env_steps
        assert all(torch.equal(v,actor.policy.state_dict()[k]) for k,v in sac.policy.state_dict().items())
        del ck,actor
        def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
        atomic_json(output/'loaded.json',dict(seed=args.seed,checkpoint=str(run/'final.pt'),steps=sac.env_steps,
            policy_device=str(next(sac.policy.parameters()).device),critic_device=str(next(sac.critic.parameters()).device),
            actor_tensors_equal=True,config_sha256=sha(run/'config.json'),actor_sha256=sha(run/'final.actor.pt'),
            evaluation_source_sha256=sha(root/'src/task8_lower/evaluation.py'),script_sha256=sha(__file__),
            map_backend=resolve_map_backend(cfg),sensor_policy=cfg['sensor_policy'],
            pool_sha256=sha(cfg['transfer_pool']),seeds_sha256=sha(cfg['evaluation_seeds']),
            cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES')))
        print(json.dumps(dict(event='loaded',seed=args.seed,device=str(sac.device))),flush=True)
        result=evaluate_transfer(sac,cfg,output/'evaluation.json',deadline=started+1770)
        t=result['transfer'];assert result['complete'] and len(t['rows'])==96
        atomic_json(output/'status.json',dict(status='done',seed=args.seed,wall_s=time.monotonic()-started,success=sum(bool(r['strict_success']) for r in t['rows']),episodes=96))
        print(json.dumps(dict(event='done',seed=args.seed,success=t['strict_success_rate'],wall_s=time.monotonic()-started)),flush=True)
    except BaseException as error:
        atomic_json(output/'status.json',dict(status='failed',seed=args.seed,wall_s=time.monotonic()-started,error=repr(error)))
        traceback.print_exc();raise
