#!/usr/bin/env python3
"""Bounded task7.22 real pipeline. Formal training is deliberately unauthorized."""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path


def atomic_json(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False));os.replace(tmp,path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    root=Path('/root/mm_husky_ws')
    p.add_argument('--config',type=Path,default=root/'config/task7/upper_train.json')
    p.add_argument('--stage',choices=('1','2','3'),required=True)
    p.add_argument('--decisions',type=int,required=True)
    p.add_argument('--variant',choices=('sync','async'),required=True)
    p.add_argument('--branch',choices=('G2','G3','G4'),default='G4')
    p.add_argument('--environments',type=int,default=16)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source',type=Path);p.add_argument('--phase2',type=Path)
    p.add_argument('--resume',type=Path);p.add_argument('--max-wall-s',type=float,default=500)
    p.add_argument('--seed',type=int,default=722)
    args=p.parse_args();config=json.loads(args.config.read_text())
    key={'1':'stage1_decisions','2':'stage2_decisions','3':'stage3_decisions'}[args.stage]
    if not 0<args.decisions<=min(config['bounded_limits'][key],{'1':5000,'2':2000,'3':2000}[args.stage]):p.error('outside authorized bounded decision budget')
    if args.environments not in (16,64,256):p.error('authorized E is 16/64/256')
    if args.stage!='2' and args.decisions%args.environments:p.error('whole batch required; no budget overshoot')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='1':p.error('only physical GPU1 authorized')
    import random
    import numpy as np
    import torch
    from task7_sim.decision_env import DecisionEnv
    from task7_sim.lower_policy import FrozenLowerPolicy
    from task7_upper.model import UpperModel
    from task7_upper.replay import SequenceReplay,row,exact_cpu
    from task7_upper.sac_discrete import DiscreteSAC
    from task7_upper.stages import (environment_inputs,ReplayAdapter,update_sequences,
        select_training_action,rebuild_online,save_online,load_online,begin_rl_branch)
    from task7_upper.fp_trainer import (FPTrainer,split_episodes,split_arrival_episodes,arrival_samples,
        materialize_samples,fp_arrival_batch,fit_g3_alignment)
    torch.set_num_threads(2);random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed)
    args.output.mkdir(parents=True,exist_ok=True)
    sync=args.variant=='sync';adapter=ReplayAdapter(not sync,'cuda:0')
    start=time.perf_counter()
    hash_start=time.perf_counter()
    def digest(path):
        if path is None:return None
        value=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
        return value.hexdigest()
    code_paths=[p for module in ('task7_sim','task7_upper','task7_lower') for p in (root/'src'/module).glob('*.py')]
    code_paths += [root/'scripts/task7_upper_train.py',root/'config/task7/robot_geometry.json']
    code_hashes={str(path.relative_to(root)):digest(path) for path in sorted(code_paths)}
    contract=dict(source_code_sha256=code_hashes,source_sha256=digest(args.source),phase2_sha256=digest(args.phase2),config=config,variant=args.variant,environments=args.environments,seed=args.seed,
                  target_decisions=args.decisions,stage=args.stage,branch=args.branch)
    invocation_id=str(os.getpid())+'-'+str(time.time_ns())
    records={'source_hash_seconds':[time.perf_counter()-hash_start]}
    atomic_json(args.output/f'contract-stage{args.stage}-{args.decisions}.json',contract)
    def measured(name,call):
        torch.cuda.synchronize();t=time.perf_counter();value=call();torch.cuda.synchronize()
        records.setdefault(name,[]).append(time.perf_counter()-t);return value
    def atomic_torch(path,payload):
        tmp=path.with_suffix('.tmp');torch.save(payload,tmp)
        with tmp.open('rb') as stream:os.fsync(stream.fileno())
        os.replace(tmp,path)
    def emit(event):
        with (args.output/'events.jsonl').open('a') as f:f.write(json.dumps(event,allow_nan=False)+'\n')
        print(json.dumps(event,allow_nan=False),flush=True)
    def source_model(path):
        s=torch.load(path,map_location='cpu',weights_only=False)
        dim=s['counters']['vector_dim'];m=UpperModel(vector_dim=dim,asynchronous=not sync).cuda()
        m.load_state_dict(s['learner']['model']);m.set_stage(s['learner']['stage']);return s,m
    if args.stage=='2':
        if args.source is None:p.error('stage2 requires full stage1 source')
        source,model=source_model(args.source);model.set_stage('2');trainer=FPTrainer(model)
        replay=SequenceReplay();replay.load_state_dict(source['replay'])
        all_samples,omitted_total=arrival_samples(replay,set(replay.episodes))
        eligible_keys={key for key,start in all_samples}
        if len(eligible_keys)<2:
            atomic_json(args.output/'blocked.json',dict(reason='fewer than two eligible arrival episodes',eligible_episodes=len(eligible_keys),eligible_samples=len(all_samples),omitted_early_arrivals=omitted_total))
            raise RuntimeError('stage2 requires two disjoint labelled episodes')
        train,hold=split_arrival_episodes(replay,args.seed)
        train_samples,omitted_train=arrival_samples(replay,train);hold_samples,omitted_hold=arrival_samples(replay,hold)
        # Unique offline decision budget includes both train and holdout, never epochs.
        if len(train_samples)+len(hold_samples)>args.decisions:
            p.error('eligible offline decisions exceed requested stage2 bound; explicit dataset choice required')
        if not train_samples or not hold_samples:
            atomic_json(args.output/'blocked.json',dict(reason='no eligible disjoint arrival samples',train=len(train_samples),holdout=len(hold_samples),omitted_train=omitted_train,omitted_hold=omitted_hold))
            raise RuntimeError('stage2 data prerequisite unmet; no fabricated arrivals')
        from task7_lower.training import rng_state,restore_rng
        epoch=0;edges=None;history=[];done=False;diagnostics=None
        if args.resume:
            s=torch.load(args.resume,map_location='cpu',weights_only=False)
            if s['contract']!=contract:raise ValueError('phase2 resume contract mismatch')
            model.load_state_dict(s['model']);trainer.load_state_dict(s['trainer'])
            epoch,edges,history,done=s['epoch'],s['edges'],s['history'],s['done']
            payload=s;restore_rng(s['rng'])
        while not done and time.perf_counter()-start<args.max_wall_s:
            order=list(train_samples);random.shuffle(order);loss_sum=0.;count=0
            for lo in range(0,len(order),256):
                result,diag=measured('fp_train_batch',lambda:fp_arrival_batch(model,materialize_samples(replay,order[lo:lo+256]),adapter,trainer))
                loss_sum+=result['loss']*result['arrivals'];count+=result['arrivals']
            diagnostics=[]
            with torch.no_grad():
                for lo in range(0,len(hold_samples),256):
                    _,diag=measured('fp_holdout_batch',lambda:fp_arrival_batch(model,materialize_samples(replay,hold_samples[lo:lo+256]),adapter))
                    diagnostics.append(diag)
            losses=torch.cat([d['loss'] for d in diagnostics]);information=torch.cat([d['new_observed_cells'] for d in diagnostics]).float()
            if edges is None:edges=torch.quantile(information,torch.tensor([1/3,2/3],device=information.device)).tolist()
            loss=float(losses.mean());done=trainer.end_epoch(loss);epoch+=1
            bins=torch.bucketize(information,torch.tensor(edges,device=information.device))
            stats=dict(epoch=epoch,train_loss=loss_sum/count,holdout_loss=loss,bad_epochs=trainer.bad_epochs,
                       diagnostics=dict(chosen_minus_other_mean=float(torch.cat([d['chosen_minus_other'] for d in diagnostics]).mean()) if sum(d['chosen_minus_other'].numel() for d in diagnostics) else None,
                         dispersion_mean=float(torch.cat([d['dispersion'] for d in diagnostics]).mean()),
                         information_bins=[dict(count=int((bins==i).sum()),loss=float(losses[bins==i].mean()) if (bins==i).any() else None) for i in range(3)]))
            history.append(stats);emit(stats)
            payload=dict(format='task7-upper-fp-v1',contract=contract,model=model.state_dict(),trainer=trainer.state_dict(),
                epoch=epoch,edges=edges,history=history,done=done,rng=rng_state(),train_samples=len(train_samples),holdout_samples=len(hold_samples),omitted_train=omitted_train,omitted_holdout=omitted_hold,omitted_early_arrivals_total=omitted_total,eligible_episodes=len(eligible_keys),train_episodes=len(train),holdout_episodes=len(hold))
            measured('phase2_checkpoint',lambda:atomic_torch(args.output/'latest.pt',payload))
        if done and not payload.get('g3_alignment_fitted',False):
            if diagnostics is None:
                diagnostics=[]
                with torch.no_grad():
                    for lo in range(0,len(hold_samples),256):
                        _,diag=fp_arrival_batch(model,materialize_samples(replay,hold_samples[lo:lo+256]),adapter)
                        diagnostics.append(diag)
            trained=torch.cat([d['trained_h'] for d in diagnostics]);random_h=torch.cat([d['random_h'] for d in diagnostics])
            scale,shift=fit_g3_alignment(model.random_world_model,trained,random_h)
            payload.update(model=model.state_dict(),g3_alignment_fitted=True,g3_zero_variance_dims=int((random_h.std(0,unbiased=False)==0).sum()),g3_zero_scale_dims=int((scale==0).sum()))
            atomic_torch(args.output/'latest.pt',payload)
        summary=dict(invocation_id=invocation_id,done=done,epochs=epoch,train_samples=len(train_samples),holdout_samples=len(hold_samples),unique_offline_decisions=len(train_samples)+len(hold_samples),edges=edges,history=history,records=records,wall_seconds=time.perf_counter()-start,physical_gpu=1)
        atomic_json(args.output/'summary.json',summary)
        atomic_json(args.output/('chunk-'+invocation_id+'.json'),summary)
        return
    counters=dict(decisions=0,action_calls=0,stage=args.stage,updates=0,vector_dim=None)
    if args.resume:
        from task7_lower.recovery import last_record
        meta=json.loads(args.resume.with_suffix('.meta.json').read_text());last=last_record(args.output/'interaction-ledger.jsonl')
        if last and (last['event']!='complete' or last['decisions']!=meta['decisions'] or last['action_calls']!=meta['action_calls']):
            raise RuntimeError('uncovered environment action; budget rewind blocked')
        preview=torch.load(args.resume,map_location='cpu',weights_only=False)
        model=UpperModel(vector_dim=preview['counters']['vector_dim'],asynchronous=not sync).cuda();model.set_stage(preview['learner']['stage'])
        learner=DiscreteSAC(model,199000 if args.stage=='1' else 99000);replay=SequenceReplay(seed=args.seed)
        fp=FPTrainer(model) if args.stage=='3' and args.branch=='G4' else None
        saved_contract=preview['config']
        old_target=saved_contract['target_decisions']
        if args.decisions<old_target or {k:v for k,v in saved_contract.items() if k!='target_decisions'}!={k:v for k,v in contract.items() if k!='target_decisions'}:
            raise ValueError('resume contract mismatch or budget target rewind')
        counters,env,histories=measured('online_load',lambda:load_online(args.resume,learner,replay,config=saved_contract,fp=fp))
        if args.decisions!=old_target:
            env.config_hash=hashlib.sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest()
            emit(dict(event='bounded_target_extension',old_target=old_target,new_target=args.decisions,consumed=counters['decisions'],config_hash=env.config_hash))
    else:
        policy=measured('lower_load',lambda:FrozenLowerPolicy.load(root/f'results/task7/t7.18-20261021/pilot-{args.variant}/compatible.actor.pt',synchronous=sync,device='cuda:0',checkpoint_version='task7-lower-actor-v1'))
        performance=config.get('performance',{})
        env=DecisionEnv(args.environments,policy,seed=args.seed,synchronous=sync,device='cuda:0',run_id=args.output.name,code_commit=os.getenv('TASK722_CODE_COMMIT','unknown'),
                        config_hash=hashlib.sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest(),
                        risk_chunk_size=performance.get('risk_chunk_size',32),
                        observation_chunk_size=performance.get('observation_chunk_size',32),
                        reuse_route_raster=performance.get('reuse_route_raster',False))
        env.episodes.kin.dls_cuda_graph=True
        obs,candidates=measured('initial_reset',env.reset)
        item=environment_inputs(obs,candidates,env_ids=range(args.environments),asynchronous=not sync,device='cuda:0')
        dim=item['vcm_inputs']['observation'][1].shape[-1];counters['vector_dim']=dim
        if args.stage=='1':
            model=UpperModel(vector_dim=dim,asynchronous=not sync).cuda();learner=DiscreteSAC(model,199000);replay=SequenceReplay(seed=args.seed);fp=None
        else:
            if args.source is None or (args.branch!='G2' and args.phase2 is None):p.error('branch requires stage1 source and G3/G4 completed phase2')
            source,model=source_model(args.source)
            if args.branch!='G2':
                phase2=torch.load(args.phase2,map_location='cpu',weights_only=False)
                if not phase2['done']:raise ValueError('stage2 early stop prerequisite unmet')
                model.load_state_dict(phase2['model'])
                model.random_world_model._alignment_fitted=phase2.get('g3_alignment_fitted',False)
            model.set_stage('1')
            from task7_upper.sac_discrete import CappedTemperature
            temperature=CappedTemperature('cuda');temperature.load_state_dict(source['learner']['temperature'])
            with torch.no_grad():state=model.vcm(**item['vcm_inputs'])
            learner,replay,report=begin_rl_branch(model,{'G2':'G2','G3':'G3','G4':'3'}[args.branch],temperature,total_updates=99000,replay_seed=args.seed,state=state,geometry=item['geometry'],features=item['features'],mask=item['mask'])
            atomic_json(args.output/'entry-assertion.json',report);fp=FPTrainer(model) if args.branch=='G4' else None
        histories=[[] for _ in range(args.environments)]
        measured('online_save',lambda:save_online(args.output/'latest.pt',learner,replay,environment=env,histories=histories,counters=counters,config=contract,fp=fp))
    from task7_upper.evaluate import ValidationSelector,scheduled_validation,evaluate_maps
    selector=ValidationSelector(config['validation_interval'],config['validation_tie_rule'])
    if 'validation_selector' in counters:selector.load_state_dict(counters['validation_selector'])
    E=args.environments
    while counters['decisions']<args.decisions and time.perf_counter()-start<args.max_wall_s:
        model.eval()
        measured('online_prefix_rebuild',lambda:rebuild_online(model,histories,adapter))
        item=environment_inputs(env.observation,env.candidates,env_ids=range(E),asynchronous=not sync,device='cuda:0')
        with torch.no_grad():
            out=measured('online_forward',lambda:model.forward_step(**item))
            selected,pi=select_training_action(out['logits'],item['mask'],torch.arange(E,device='cuda')+counters['decisions'])
        # Graph-free runtime before learner updates and any copy/serialization.
        model.vcm.reset()
        action_calls=counters['action_calls']+1;new_count=counters['decisions']+E
        def ledger(event):
            with (args.output/'interaction-ledger.jsonl').open('a') as f:
                f.write(json.dumps(dict(event=event,action_calls=action_calls,decisions=new_count))+'\n');f.flush();os.fsync(f.fileno())
        if counters['decisions']//selector.interval!=new_count//selector.interval and new_count%selector.interval:
            raise RuntimeError('vector batch would cross exact validation boundary; no step executed')
        ledger('intent')
        step=measured('environment_decision',lambda:env.step(selected));ledger('complete')
        measured('replay_insert',lambda:replay.append_batch(step.replay_fields,diagnostics=dict(decision_alpha=learner.temperature.alpha.expand(E),decision_pi=pi)))
        for i in range(E):
            histories[i].append(exact_cpu(row(step.replay_fields,i,E)))
            if bool(step.terminated[i]|step.truncated[i]):histories[i]=[]
        # Required per-decision fields/failed samples are already in replay.
        # These lower-only scratch histories do not affect a following begin().
        from task7_lower.training import drain_history
        drain_history(env.episodes.core)
        old_count=counters['decisions'];counters.update(decisions=new_count,action_calls=action_calls)
        updates=[]
        for count in range(old_count+1,new_count+1):
            update=measured('sequence_update',lambda:update_sequences(learner,replay,count,adapter,fp=fp,profile=True))
            if update['updated']:
                updates.append(dict(decisions=count,**update))
                records.setdefault('cpu_replay_sample',[]).append(update['timing']['cpu_sample_seconds'])
                records.setdefault('adapter_stack_decode_transfer',[]).append(update['timing']['adapter_stack_decode_transfer_seconds'])
        if updates:
            def write_updates():
                with (args.output/'learner-updates.jsonl').open('a') as stream:
                    stream.write(''.join(json.dumps(value,allow_nan=False)+'\n' for value in updates))
            measured('learner_log_write',write_updates)
        counters['updates']=learner.updates
        def validate():
            from task7_lower.training import rng_state,restore_rng
            saved_rng=rng_state()
            try:
                pool=env.episodes.sampler.pool
                maps=[m['id'] for m in json.loads((pool/'index.json').read_text())['maps'] if m['split']=='validation']
                def make_environment(_):
                    return DecisionEnv(1,env.policy,seed=args.seed,pool=pool,split='validation',synchronous=sync,device='cuda:0')
                def eval_adapter(e,o,c):
                    return environment_inputs(o,c,env_ids=[0],asynchronous=not sync,device='cuda:0')
                return evaluate_maps(make_environment,maps,group={'1':'stage1','3':'G4','G2':'G2','G3':'G3'}[model.stage],model=model,adapter=eval_adapter)
            finally:restore_rng(saved_rng)
        def save_best():
            counters['validation_selector']=selector.state_dict()
            save_online(args.output/'best.pt',learner,replay,environment=env,histories=histories,counters=counters,config=contract,fp=fp)
        validation=scheduled_validation(selector,old_count,new_count,lambda:measured('validation',validate),save_best)
        if validation is not None:
            counters['validation_selector']=selector.state_dict();emit(dict(event='validation',**validation))
        emit(dict(decisions=new_count,updates=learner.updates,reward_mean=float(step.reward.mean()),arrivals=int(step.info['r_t']['arrived'].sum()),ended=int((step.terminated|step.truncated).sum()),last_update=updates[-1] if updates else None,strict_success=int(step.info['strict_success'].sum()),
                  sim_seconds=float(step.dt.sum()),lower_steps=int(step.info['r_t']['lower_steps'].sum()),
                  triggers={k:int(v.sum()) for k,v in step.info['triggers'].items()},environment_timing=step.info['timing']))
        measured('online_save',lambda:save_online(args.output/'latest.pt',learner,replay,environment=env,histories=histories,counters=counters,config=contract,fp=fp))
        all_samples,omitted_total=arrival_samples(replay,set(replay.episodes));eligible_keys={key for key,start in all_samples}
        train_keys,hold_keys=split_arrival_episodes(replay,args.seed) if len(eligible_keys)>1 else (eligible_keys,set())
        train_samples,omitted_train=arrival_samples(replay,train_keys);hold_samples,omitted_hold=arrival_samples(replay,hold_keys)
        replay_stats=dict(transitions=len(replay),episodes=len(replay.episodes),fragments=len(replay.starts()),
                          train_eligible_arrivals=len(train_samples),holdout_eligible_arrivals=len(hold_samples),
                          omitted_early_arrivals=omitted_total,eligible_arrival_episodes=len(eligible_keys))
        summary=dict(invocation_id=invocation_id,done=new_count==args.decisions,counters=counters,replay_stats=replay_stats,fp_updates=None if fp is None else fp.updates,records=records,wall_seconds=time.perf_counter()-start,physical_gpu=1,parameter_device=str(next(model.parameters()).device),optimizer_devices=sorted({str(s['exp_avg'].device) for s in learner.optimizer.state.values()}),lower_versions=env.policy.versions,environment_versions=env.versions,peak_allocated_bytes=torch.cuda.max_memory_allocated(),limitation='pipeline-only pilot lower, no learning conclusion')
        atomic_json(args.output/'summary.json',summary)
        atomic_json(args.output/('chunk-'+invocation_id+'.json'),summary)
    print(json.dumps(dict(done=counters['decisions']==args.decisions,counters=counters)),flush=True)


if __name__=='__main__':main()
