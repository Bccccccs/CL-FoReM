#!/usr/bin/env python3
"""Read-only CPU reconstruction of task10's exact first update; never steps optimizers."""
import argparse, csv, hashlib, json, math, random, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import torch
from task10.learning import EpisodeReplay, ReplayAdapter, Stage1Learner, sequence_outputs, attempt_reward, bellman
from task10.recovery import fragment_identity
from task7_upper.model import UpperModel
from task7_upper.sac_discrete import distribution


def load(p): return torch.load(p, map_location='cpu', weights_only=False)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def scalar(x): return x.item() if isinstance(x,torch.Tensor) else x
def clean(x):
    if isinstance(x,torch.Tensor): return x.detach().cpu().tolist()
    if isinstance(x,dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean(v) for v in x]
    return x

def stats(xs):
    xs=[float(x) for x in xs]
    return dict(n=len(xs),min=min(xs) if xs else None,max=max(xs) if xs else None,mean=sum(xs)/len(xs) if xs else None)

def grads_summary(names, grads):
    groups=defaultdict(lambda:dict(parameters=0,present=0,nonzero=0,squared_norm=0.))
    for name,g in zip(names,grads):
        key='.'.join(name.split('.')[:2]) if name.startswith('head_a') else name.split('.')[0]
        d=groups[key];d['parameters']+=1
        if g is not None:
            d['present']+=1;d['nonzero']+=bool(torch.count_nonzero(g));d['squared_norm']+=float(g.square().sum())
    return {k:{**v,'norm':math.sqrt(v.pop('squared_norm'))} for k,v in groups.items()}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    begin=time.perf_counter();torch.set_num_threads(2);src=args.source;out=args.output;out.mkdir(parents=True,exist_ok=True)
    before=load(src/'first-update-before.pt');after=load(src/'first-update-after.pt');evidence=load(src/'first-update-evidence.pt')
    learner=Stage1Learner(UpperModel(vector_dim=before['counters']['vector_dim']),before['learner']['total_updates'])
    learner.load_state_dict(before['learner']);learner.model.train()
    replay=EpisodeReplay(before['replay']['capacity']);replay.load_state_dict(before['replay'])
    random.setstate(before['rng']['python']);np.random.set_state(before['rng']['numpy']);torch.set_rng_state(before['rng']['torch'])
    fragments=replay.sample();saved=json.loads((src/'first-update-sample.json').read_text())
    assert json.loads(json.dumps(fragment_identity(fragments)))==saved['sample_identity']
    adapter=ReplayAdapter(False,'cpu')
    current,following,rows=sequence_outputs(learner.model,fragments,adapter,gradients=True)
    _,target_following,target_rows=sequence_outputs(learner.target,fragments,adapter,gradients=False)
    assert [id(r) for r in rows]==[id(r) for r in target_rows]
    batch={k:torch.stack([torch.as_tensor(r[k]) for r in rows]) for k in ('selected','reward','dt','bootstrap_mask')}
    mask=torch.stack([r['candidates']['mask'] for r in rows]);nextmask=torch.stack([r['next_candidates']['mask'] for r in rows])
    p,logp=distribution(current['logits'],mask);np_,nlp=distribution(following['logits'],nextmask)
    alpha=learner.temperature.alpha;nextq=torch.minimum(target_following['q1'],target_following['q2']).masked_fill(~nextmask,0.)
    eq=(np_*nextq).sum(-1);nh=-(np_*nlp).sum(-1);g=.99**(batch['dt']/.1);bm=batch['bootstrap_mask']
    qcontrib=bm*g*eq;hcontrib=bm*g*alpha*nh;y=batch['reward']+qcontrib+hcontrib
    independent=bellman(batch['reward'],bm,batch['dt'],following['logits'],target_following['q1'],target_following['q2'],nextmask,alpha)
    assert torch.allclose(y,independent,atol=2e-7,rtol=1e-6)
    y=y.detach();idx=batch['selected'].long()[:,None]
    q1=current['q1'].gather(-1,idx).squeeze(-1);q2=current['q2'].gather(-1,idx).squeeze(-1)
    qloss=.5*((q1-y).square().mean()+(q2-y).square().mean())
    aq=torch.minimum(current['actor_q1'],current['actor_q2']).masked_fill(~mask,0.)
    entropy=-(p*logp).sum(-1);actor_q=-(p*aq).sum(-1);actor_h=-alpha*entropy;actor=(actor_q+actor_h).mean()
    names,params=zip(*[(n,p_) for n,p_ in learner.model.named_parameters() if p_.requires_grad])
    ag=torch.autograd.grad(actor,params,retain_graph=True,allow_unused=True)
    qg=torch.autograd.grad(qloss,params,retain_graph=True,allow_unused=True)
    total=torch.autograd.grad(qloss+actor,params,retain_graph=True,allow_unused=True)
    zgrad=torch.autograd.grad(actor,current['logits'],retain_graph=True)[0]
    qz=torch.autograd.grad(actor_q.mean(),current['logits'],retain_graph=True)[0]
    hz=torch.autograd.grad(actor_h.mean(),current['logits'],retain_graph=True)[0]
    expected=p*(alpha*logp-aq-(p*(alpha*logp-aq)).sum(-1,keepdim=True))/len(rows)
    expected=expected.masked_fill(~mask,0.)
    expected_error=float((zgrad-expected).abs().max())
    # All trainable IDs are owned exactly once by the joint optimizer.
    opt_names=[next(n for n,p_ in zip(names,params) if p_ is q) for gr in learner.optimizer.param_groups for q in gr['params']]
    update_comparisons={}
    gradmap=dict(zip(names,total));gradient_cpu_gpu=[]
    for head in ('actor','q1','q2'):
        snapshots=evidence['after']['heads'][head]
        for n,ref in snapshots['gradients'].items():
            if ref is not None:
                gradient_cpu_gpu.append(dict(name=n,max_abs_difference=float((gradmap[n]-ref).abs().max()),cpu_norm=float(gradmap[n].norm()),original_gpu_norm=float(ref.norm())))
    for group in ('vcm','candidate_encoder','head_a','head_b','bias','world_model','random_world_model'):
        keys=[k for k in before['learner']['model'] if k.startswith(group+'.')]
        update_comparisons[group]=dict(tensors=len(keys),changed=sum(not torch.equal(before['learner']['model'][k],after['learner']['model'][k]) for k in keys))
    # Source terminal route lengths are raw episode facts, indexed by real environment/episode.
    episodes={(int(r['environment']),int(r['episode_id'])):r for r in map(json.loads,(src/'episodes.jsonl').read_text().splitlines())}
    table=[];candidate_table=[]
    for i,r in enumerate(rows):
        key=(int(r['environment_id']),int(r['episode_id']));episode=episodes.get(key)
        before_s=float(r['observation']['route_s']);after_s=float(r['next_observation']['route_s']);ended=bool(r['terminated']|r['truncated'])
        row=dict(loss_row=i,environment=key[0],episode=key[1],decision=int(r['decision_index']),map_id=r['map_ids'],selected=int(r['selected']),inplace=bool(r['candidates']['inplace'][int(r['selected'])]),attempted_substeps=int(r['attempted_substeps']),dt=float(batch['dt'][i]),g=float(g[i]),bootstrap_mask=float(bm[i]),terminated=bool(r['terminated']),truncated=bool(r['truncated']),strict_success=bool(r['strict_success']),stall=bool(r['triggers']['stall_limit']),before_s=before_s,after_s=after_s,base_reward=float(r['reward_components']['base_reward']),shaping=float(r['reward_components']['shaping']),reward=float(batch['reward'][i]),next_expected_minQ=float(eq[i]),next_entropy=float(nh[i]),alpha=float(alpha),target_Q_contribution=float(qcontrib[i]),target_entropy_contribution=float(hcontrib[i]),target=float(y[i]),target_without_entropy=float(y[i]-hcontrib[i]),selected_Q1=float(q1[i]),selected_Q2=float(q2[i]),dcritic_dQ1=float((q1[i]-y[i])/len(rows)),dcritic_dQ2=float((q2[i]-y[i])/len(rows)),actor_Q_term=float(actor_q[i]),actor_entropy_term=float(actor_h[i]),entropy=float(entropy[i]),inplace_probability=float(p[i,12]),inplace_dactor_dlogit=float(zgrad[i,12]),inplace_Q_dactor_dlogit=float(qz[i,12]),inplace_entropy_dactor_dlogit=float(hz[i,12]),actor_argmax=int(current['logits'][i].argmax()),critic_argmax=int(aq[i].masked_fill(~mask[i],-torch.inf).argmax()))
        if episode:
            length=episode['route_length'];recomputed=attempt_reward(before_s,after_s,length,int(r['attempted_substeps']),terminated=bool(r['terminated']),truncated=bool(r['truncated']),strict_success=bool(r['strict_success']))
            row.update(route_length=length,phi_before=before_s/length,phi_after=0. if ended else after_s/length,reward_recomputed=recomputed['reward'],reward_abs_error=abs(recomputed['reward']-row['reward']))
        table.append(row)
        for k in range(mask.shape[-1]):
            if not mask[i,k]:continue
            candidate_table.append(dict(loss_row=i,slot=k,selected=k==int(r['selected']),inplace=bool(r['candidates']['inplace'][k]),logit=float(current['logits'][i,k]),probability=float(p[i,k]),Q1=float(current['q1'][i,k]),Q2=float(current['q2'][i,k]),dactor_dlogit=float(zgrad[i,k]),dQterm_dlogit=float(qz[i,k]),dEntropyterm_dlogit=float(hz[i,k])))
    def write_csv(name,values):
        keys=list(dict.fromkeys(k for r in values for k in r))
        with (out/name).open('w') as f:
            w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(values)
    write_csv('signal-first-update-rows.csv',table);write_csv('signal-first-update-candidates.csv',candidate_table)
    refs=evidence['update_result'];norm=math.sqrt(sum(float(x.square().sum()) for x in total if x is not None))
    summary=dict(schema='task10-signal-diagnostic-v1',source_files={n:sha(src/n) for n in ('first-update-before.pt','first-update-after.pt','first-update-evidence.pt','first-update-sample.json')},code_sha256=sha(__file__),device='cpu',updates_executed=0,new_environment_decisions=0,sample_identity_exact=True,anchors=len(fragments),loss_rows=len(rows),prefix_lengths=[len(f.prefix) for f in fragments],burnin_lengths=[len(f.burn_in) for f in fragments],loss_lengths=[len(f.steps) for f in fragments],padding_loss_rows=0,first_decision_loss_rows=sum(int(r['decision_index'])==0 for r in rows),losses=dict(critic=float(qloss),actor=float(actor),gradient_norm=norm,original_gpu={k:refs[k] for k in ('critic','actor','gradient_norm')},abs_differences=dict(critic=abs(float(qloss)-refs['critic']),actor=abs(float(actor)-refs['actor']),gradient_norm=abs(norm-refs['gradient_norm']))),actor_logit_gradient_formula_max_error=expected_error,gradients=dict(actor_only=grads_summary(names,ag),critic_only=grads_summary(names,qg),joint=grads_summary(names,total),head_CPU_original_GPU=gradient_cpu_gpu),optimizer=dict(all_trainable_exactly_once=len(opt_names)==len(set(opt_names))==len(names) and set(opt_names)==set(names),parameter_tensors=len(names),initial_lr=learner.optimizer.param_groups[0]['lr'],after_first_lr=after['learner']['optimizer']['param_groups'][0]['lr'],total_updates=learner.total_updates,before_scheduler=before['learner']['scheduler'],after_scheduler=after['learner']['scheduler']),first_update_parameter_changes=update_comparisons,row_groups={name:dict(count=len(rs),target=stats(r['target'] for r in rs),entropy_contribution=stats(r['target_entropy_contribution'] for r in rs),reward=stats(r['reward'] for r in rs),inplace_logit_gradient=stats(r['inplace_dactor_dlogit'] for r in rs)) for name,rs in [('zero_attempt',[r for r in table if r['attempted_substeps']==0]),('terminal_stall',[r for r in table if r['stall'] and r['bootstrap_mask']==0]),('terminal_success',[r for r in table if r['strict_success']]),('inplace',[r for r in table if r['inplace']]),('moving',[r for r in table if not r['inplace']])]},reward_max_abs_error=max(r.get('reward_abs_error',0) for r in table),examples=dict(zero_attempt=[r for r in table if r['attempted_substeps']==0][:4],terminal_stall=[r for r in table if r['stall'] and r['bootstrap_mask']==0][:4],inplace_gradient_decreases=[r for r in table if r['inplace_dactor_dlogit']>0][:3],inplace_gradient_increases=[r for r in table if r['inplace_dactor_dlogit']<0][:3]),limitations=['CPU replay of original GPU float32 outputs has platform rounding differences; actual differences reported.','Only first-update sample was persisted, not historical samples of all 200 updates.','Analytic no-entropy target is a contribution decomposition, not a changed-objective update.','No optimizer.step called. Gradient descent sign is local logit coordinate, not a guarantee of neural parameter update response.'],wall_seconds=time.perf_counter()-begin)
    # Observe already-saved actual updates without stepping any optimizer.
    observation_changes={}
    for label,payload in [('after_first',after),('final',load(src/'offline-learner.pt'))]:
        learner.load_state_dict(payload['learner']);learner.model.eval()
        with torch.no_grad():
            observed,_,_=sequence_outputs(learner.model,fragments,adapter,gradients=False)
            op,olp=distribution(observed['logits'],mask)
        observation_changes[label]=dict(inplace_probability_before=stats(p[:,12].detach()),inplace_probability_after=stats(op[:,12]),inplace_probability_delta=stats(op[:,12]-p[:,12].detach()),inplace_probability_decreased=int((op[:,12]<p[:,12].detach()).sum()),inplace_probability_increased=int((op[:,12]>p[:,12].detach()).sum()),inplace_argmax=int((observed['logits'].argmax(-1)==12).sum()),inplace_logit_delta=stats(observed['logits'][:,12]-current['logits'][:,12].detach()),selected_Q1_delta=stats(observed['q1'].gather(-1,idx).squeeze()-q1.detach()),selected_Q2_delta=stats(observed['q2'].gather(-1,idx).squeeze()-q2.detach()))
    final_payload=payload;final_replay=EpisodeReplay(final_payload['replay']['capacity']);final_replay.load_state_dict(final_payload['replay'])
    stall_keys=[k for k,seq in final_replay.episodes.items() if any(bool(r['triggers']['stall_limit']) for r in seq)]
    stall_fragments=[final_replay.fragment(k,0) for k in stall_keys]
    stall_table=[];chain_table=[]
    for label,payload in [('before',before),('after_first',after),('final',final_payload)]:
        learner.load_state_dict(payload['learner']);learner.model.eval()
        with torch.no_grad():
            sc,sf,sr=sequence_outputs(learner.model,stall_fragments,adapter,gradients=False)
            _,st,_=sequence_outputs(learner.target,stall_fragments,adapter,gradients=False)
            sm=torch.stack([r['candidates']['mask'] for r in sr]);snm=torch.stack([r['next_candidates']['mask'] for r in sr])
            sp,slp=distribution(sc['logits'],sm);snp,snlp=distribution(sf['logits'],snm)
            sa=learner.temperature.alpha;snh=-(snp*snlp).sum(-1)
            sbm=torch.tensor([float(r['bootstrap_mask']) for r in sr]);sg=.99**(torch.tensor([float(r['dt']) for r in sr])/.1)
            sq=(snp*torch.minimum(st['q1'],st['q2']).masked_fill(~snm,0.)).sum(-1)
            sy=torch.tensor([float(r['reward']) for r in sr])+sbm*sg*(sq+sa*snh)
            saq=torch.minimum(sc['actor_q1'],sc['actor_q2']).masked_fill(~sm,0.)
            cost=sa*slp-saq;sz=sp*(cost-(sp*cost).sum(-1,keepdim=True))
        bykey=defaultdict(list)
        for i,r in enumerate(sr):
            selected=int(r['selected']);key=(r['run_id'],int(r['environment_id']),int(r['episode_id']))
            rr=dict(model=label,environment=key[1],episode=key[2],decision=int(r['decision_index']),selected=selected,zero_attempt=int(r['attempted_substeps'])==0,stall=bool(r['triggers']['stall_limit']),strict_success=bool(r['strict_success']),actor_gradient_reduction='per-row unaveraged',bootstrap_mask=float(sbm[i]),reward=float(r['reward']),g=float(sg[i]),target=float(sy[i]),target_Q_contribution=float(sbm[i]*sg[i]*sq[i]),target_entropy_contribution=float(sbm[i]*sg[i]*sa*snh[i]),next_entropy=float(snh[i]),selected_Q1=float(sc['q1'][i,selected]),selected_Q2=float(sc['q2'][i,selected]),selected_Q1_residual=float(sc['q1'][i,selected]-sy[i]),selected_Q2_residual=float(sc['q2'][i,selected]-sy[i]),inplace_minQ=float(saq[i,12]),best_moving_minQ=float(saq[i,:12].masked_fill(~sm[i,:12],-torch.inf).max()),inplace_probability=float(sp[i,12]),inplace_dactor_dlogit=float(sz[i,12]),actor_argmax=int(sc['logits'][i].argmax()),critic_argmax=int(saq[i].masked_fill(~sm[i],-torch.inf).argmax()))
            stall_table.append(rr);bykey[key].append(rr)
        for key,rs in bykey.items():
            rs.sort(key=lambda x:x['decision']);factor=1.;rawreturn=0.;hreturn=0.
            for rr in rs:
                rawreturn+=factor*rr['reward'];hreturn+=factor*rr['target_entropy_contribution'];factor*=rr['g']
            chain_table.append(dict(model=label,environment=key[1],episode=key[2],strict_success=rs[-1]['strict_success'],decisions=len(rs),zero_attempt_decisions=sum(r['zero_attempt'] for r in rs),discounted_raw_reward=rawreturn,discounted_observed_next_entropy=hreturn,raw_plus_observed_entropy=rawreturn+hreturn,interpretation='Entropy along recorded off-policy path; arithmetic diagnostic, not policy expected return.'))
    write_csv('signal-stall-chain-rows.csv',stall_table);write_csv('signal-stall-chain-returns.csv',chain_table)
    first_adam=[]
    for name,gr in zip(names,total):
        if gr is not None:
            delta=after['learner']['model'][name]-before['learner']['model'][name]
            active=gr.abs()>1e-7
            first_adam.append(dict(name=name,active_gradient_elements=int(active.sum()),delta_opposes_gradient=int(((delta*gr<0)&active).sum()),delta_agrees_gradient=int(((delta*gr>0)&active).sum()),unchanged=int(((delta==0)&active).sum())))
    summary.update(saved_update_observations=observation_changes,first_Adam_sign=first_adam,stall_trigger_episodes=len(stall_keys),stall_failure_episodes=sum(not bool(final_replay.episodes[k][-1]['strict_success']) for k in stall_keys),stall_chain_rows=len(stall_table),stall_terminal_final=[r for r in stall_table if r['model']=='final' and r['stall']],stall_failure_terminal_final=[r for r in stall_table if r['model']=='final' and r['stall'] and not r['strict_success']],stall_path_entropy_returns=[r for r in chain_table if r['model']=='final'],target_following_online_weight_after_200=1-(1-.001)**200,target_following_interpretation='For one online parameter held fixed from update 1 through 200; actual moving online weights form an EMA, not this constant endpoint.',final_lr=final_payload['learner']['optimizer']['param_groups'][0]['lr'],final_alpha=.35*math.exp(float(final_payload['learner']['temperature']['log_alpha'])),wall_seconds=time.perf_counter()-begin)
    (out/'signal-summary.json').write_text(json.dumps(clean(summary),indent=2,allow_nan=False)+'\n');torch.save(dict(current={k:v.detach() for k,v in current.items()},following={k:v.detach() for k,v in following.items()},target_following={k:v.detach() for k,v in target_following.items()},batch=batch,mask=mask,nextmask=nextmask,target=y),out/'signal-first-update-tensors.pt')
    print(json.dumps({k:summary[k] for k in ('anchors','loss_rows','losses','row_groups','wall_seconds')},indent=2))
if __name__=='__main__':main()
