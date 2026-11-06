#!/usr/bin/env python3
"""Read-only CPU reconstruction for task10.15; never steps an environment or optimizer."""
import csv, hashlib, json, math, subprocess, time
from collections import Counter,defaultdict
from pathlib import Path
import torch
from task10.learning import ReplayAdapter,attempt_reward
from task10.validation import load_model
from task7_upper.replay import row
from task7_upper.stages import runtime,restore_runtime
from task7_upper.candidate_encoder import CandidateEncoder
from task7_upper.sac_discrete import distribution

ROOT=Path('/workspace');BASE=ROOT/'results/task10';TRAIN=BASE/'t10-online-20261102-s101';EVAL=BASE/'t10-eval-20261103-s101';OUT=BASE/'t10-diag-20261103-s101'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def load(p):return torch.load(p,map_location='cpu',weights_only=False)
def dump(name,v): (OUT/name).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def scalar(x):return x.item() if isinstance(x,torch.Tensor) else x
def writecsv(name,rows):
 with (OUT/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
def stats(xs):return dict(min=min(xs),mean=sum(xs)/len(xs),max=max(xs))
def freeze():
 files={str(p.relative_to(ROOT)):sha(p) for r in (TRAIN,EVAL) for p in sorted(r.rglob('*')) if p.is_file()}
 contract=json.loads((TRAIN/'contract.json').read_text());diff=[]
 for n,h in contract['code_sha256'].items():
  p=ROOT/n;a=sha(p) if p.is_file() else None
  if a!=h:diff.append(dict(path=n,training=h,current=a))
 evdiff=[]
 for p in (EVAL/'frozen-code').rglob('*'):
  if p.is_file():
   q=ROOT/p.relative_to(EVAL/'frozen-code')
   if not q.exists() or sha(p)!=sha(q):evdiff.append(str(p.relative_to(EVAL/'frozen-code')))
 dump('input-freeze.json',dict(files=files,training_code_differences=diff,evaluation_code_differences=evdiff))
 return files

def rankings():
 records=[json.loads(x) for x in (EVAL/'decisions.jsonl').read_text().splitlines()]
 models={s:load_model(TRAIN/('final.actor.pt' if s=='trained' else 'initial-learner.pt'),s,'cpu')[0] for s in ('initial','trained')}
 adapter=ReplayAdapter(False,'cpu');summary=[];candidates=[];permerrors=[];normrows=[]
 by=defaultdict(list)
 for rec in records:by[rec['episode_id']].append(rec)
 with torch.no_grad():
  for name,recs in by.items():
   if not name.endswith('__trained'):continue
   initial=by[name.replace('__trained','__initial')]
   for m in models.values():m.vcm.reset()
   for rec,irec in zip(recs,initial):
    raw=load(EVAL/rec['raw_path']);iraw=load(EVAL/irec['raw_path']);f=raw['fields'];t=row(f,0,1);it=row(iraw['fields'],0,1)
    for part in ('observation','candidates'):
     from task10.gpu_diagnosis import compare_tree
     a,b=t[part],it[part]
     if part=='candidates':a,b=({k:z[k] for k in ('c_k','mask','f_k','progress','inplace','world_pose')}for z in (a,b))
     assert compare_tree(a,b)['exact'],(name,rec['decision_index'],part)
    item=adapter([t]);mask=item['mask'][0];g=item['geometry'];feat=item['features'];ng,nf=CandidateEncoder.normalize(g[:,mask],feat[:,mask]);ngfull=torch.zeros_like(g);nffull=torch.zeros_like(feat);ngfull[:,mask]=ng;nffull[:,mask]=nf;ng,nf=ngfull,nffull
    assert bool(t['candidates']['inplace'][12]) and t['candidates']['inplace'].sum()==1
    assert torch.equal(t['selected_prediction'],t['candidates']['f_k'][int(t['selected'])])
    for k in range(13):
     nr=dict(episode=name,decision=rec['decision_index'],slot=k,mask=bool(mask[k]),inplace=bool(t['candidates']['inplace'][k]))
     for prefix,a in [('geometry',g[0,k]),('normalized_geometry',ng[0,k]),('feature',feat[0,k]),('normalized_feature',nf[0,k])]:
      nr.update({prefix+'_'+str(j):float(v) for j,v in enumerate(a)})
     normrows.append(nr)
    for s,m in models.items():
     saved=runtime(m.vcm);out=m.forward_step(**item);p,lp=distribution(out['logits'],item['mask']);q=torch.minimum(out['q1'],out['q2'])[0];l=out['logits'][0]
     bestmove=max([k for k in range(12) if mask[k]],key=lambda k:float(l[k]));bestq=max([k for k in range(13) if mask[k]],key=lambda k:float(q[k]));qm=max([k for k in range(12) if mask[k]],key=lambda k:float(q[k]))
     original=rec if s=='trained' else irec;rawlogits=torch.tensor([z if z is not None else -float('inf') for z in original['logits']]);rawprob=rawlogits.softmax(-1);rawgap=float(rawlogits[12]-rawlogits[:12].max());err=max(abs(float(l[k])-original['logits'][k]) for k in range(13) if mask[k])
     summary.append(dict(episode=name,decision=rec['decision_index'],strategy=s,valid=int(mask.sum()),p_inplace=float(p[0,12]),entropy=float(-(p*lp).sum()),logit_gap=float(l[12]-l[bestmove]),best_move_logit_slot=bestmove,q_gap=float(q[12]-q[qm]),best_q_slot=bestq,actor_critic_agree=bestq==int(l.argmax()),record_logit_max_error=err,record_p_inplace=float(rawprob[12]),record_logit_gap=rawgap))
     for k in range(13):
      candidates.append(dict(episode=name,decision=rec['decision_index'],strategy=s,slot=k,valid=bool(mask[k]),logit=float(l[k]) if mask[k] else None,probability=float(p[0,k]),q1=float(out['q1'][0,k]),q2=float(out['q2'][0,k]),min_q=float(q[k])))
     # Same prior recurrent state; reverse all candidate fields/mask together.
     after=runtime(m.vcm);restore_runtime(m.vcm,saved);perm=torch.arange(12,-1,-1);pi=dict(item,geometry=g[:,perm],features=feat[:,perm],mask=item['mask'][:,perm]);po=m.forward_step(**pi);restore_runtime(m.vcm,after)
     permerrors.append(dict(strategy=s,episode=name,decision=rec['decision_index'],**{key:float((po[key][0,perm][mask]-out[key][0][mask]).abs().max()) for key in ('logits','q1','q2')}))
 writecsv('state-rankings.csv',summary);writecsv('candidate-scores.csv',candidates);writecsv('candidate-features.csv',normrows);writecsv('permutation-check.csv',permerrors)
 result={}
 for s in models:
  ss=[r for r in summary if r['strategy']==s]
  result[s]=dict(states=len(ss),p_inplace=stats([r['p_inplace'] for r in ss]),record_p_inplace=stats([r['record_p_inplace'] for r in ss]),record_logit_gap=stats([r['record_logit_gap'] for r in ss]),logit_gap=stats([r['logit_gap'] for r in ss]),q_gap=stats([r['q_gap'] for r in ss]),entropy=stats([r['entropy'] for r in ss]),actor_critic_agree=sum(r['actor_critic_agree'] for r in ss),critic_inplace=sum(r['best_q_slot']==12 for r in ss),record_logit_max_error=max(r['record_logit_max_error'] for r in ss),permutation_max_error={k:max(r[k] for r in permerrors if r['strategy']==s) for k in ('logits','q1','q2')})
 dump('ranking-summary.json',result);print('rankings',json.dumps(result),flush=True)

def coverage():
 ck=load(TRAIN/'offline-learner.pt');eps=ck['replay']['episodes'];rows=[];episodes=[];rewarderr=0
 # Collection phase comes from durable global order, not episode ordering.
 globalids={}
 for line in (TRAIN/'decisions.jsonl').read_text().splitlines():
  rec=json.loads(line)
  # actual journal inspected below; decision index reservation mapping is recovered from batches
 batches=sorted((TRAIN/'real-executions').glob('batch-*.pt'));seqno=0
 for p in batches:
  f=load(p)['fields'];n=len(f['episode_id'])
  for i in range(n):
   t=row(f,i,n);globalids[(int(t['environment_id']),int(t['episode_id']),int(t['decision_index']))]=seqno;seqno+=1
 episode_records={(x['environment'],x['episode_id']):x for x in [json.loads(z) for z in (TRAIN/'episodes.jsonl').read_text().splitlines()]}
 for key,seq in eps.items():
  er=episode_records.get((key[-2],key[-1]));length=er['route_length'] if er else None
  # Route length does not live in policy obs; complete episodes have durable truth metadata.
  cumulative=1.;ret=0.;bases=0.;shapes=0.;reason='ongoing';ts=[]
  for t in seq:
   end=bool(t['terminated']) or bool(t['truncated']);success=bool(t['strict_success']);sel=int(t['selected']);ident=(int(t['environment_id']),int(t['episode_id']),int(t['decision_index']));order=globalids[ident]
   phi0=float(t['observation']['route_s'])/length if length else None;phi1=float(t['next_observation']['route_s'])/length if length else None
   g=.99**(float(t['dt'])/.1);reward=float(t['reward']);base=float(t['reward_components']['base_reward']);shape=float(t['reward_components']['shaping'])
   if length:
    recompute=attempt_reward(float(t['observation']['route_s']),float(t['next_observation']['route_s']),length,int(t['attempted_substeps']),terminated=bool(t['terminated']),truncated=bool(t['truncated']),strict_success=success)
    rewarderr=max(rewarderr,abs(recompute['reward']-reward),abs(recompute['discount']-float(t['discount'])))
   triggers=[k for k,v in t['triggers'].items() if bool(v)]
   if end:reason='strict_success' if success else ('failure_limit' if 'failure_limit' in triggers else 'stall_limit' if 'stall_limit'in triggers else 'route_end_with_failure' if 'route_end'in triggers else 'other')
   rr=dict(episode=repr(key),environment=ident[0],episode_id=ident[1],decision=ident[2],global_index=order,phase='warmup' if order<1000 else 'policy',slot=sel,inplace=bool(t['candidates']['inplace'][sel]),zero_attempt=int(t['attempted_substeps'])==0,attempted=int(t['attempted_substeps']),failed_attempts=int(t['r_t']['n_fail']),success=success,terminal=end,bootstrap=float(t['bootstrap_mask']),dt=float(t['dt']),discount=g,reward=reward,base_reward=base,shaping=shape,phi_before=phi0,phi_after=0. if end else phi1,raw_route_fraction_after=phi1,triggers='|'.join(triggers));rows.append(rr);ts.append(rr)
   ret+=cumulative*reward;bases+=cumulative*base;shapes+=cumulative*shape;cumulative*=g
  initialphi=ts[0]['phi_before'];terminalphi=0. if ts[-1]['terminal'] else ts[-1]['phi_after']
  telescope=None if initialphi is None else -initialphi+cumulative*terminalphi
  episodes.append(dict(episode=repr(key),length=len(seq),complete=ts[-1]['terminal'],success=ts[-1]['success'],reason=reason,discounted_reward=ret,discounted_base=bases,discounted_shaping=shapes,telescope=telescope,telescope_error=None if telescope is None else shapes-telescope,zero_attempts=sum(r['zero_attempt'] for r in ts),inplace=sum(r['inplace'] for r in ts)))
 writecsv('replay-transitions.csv',rows);writecsv('episode-returns.csv',episodes)
 result=dict(transitions=len(rows),episodes=len(eps),slot_counts=dict(Counter(r['slot'] for r in rows)),phases={p:dict(transitions=len(rs),inplace=sum(r['inplace']for r in rs),zero_attempt=sum(r['zero_attempt']for r in rs),success=sum(r['success']for r in rs),terminal=sum(r['terminal']for r in rs),failed_decisions=sum(r['failed_attempts']>0 for r in rs)) for p in ('warmup','policy') for rs in [[r for r in rows if r['phase']==p]]},terminal_reasons=dict(Counter(e['reason']for e in episodes)),incomplete=sum(not e['complete']for e in episodes),reward_discount_max_error=rewarderr,telescope_max_error=max(abs(e['telescope_error']) for e in episodes if e['telescope_error']is not None),zero_dt_nonterminal=sum(r['zero_attempt'] and not r['terminal']for r in rows),zero_dt_terminal=sum(r['zero_attempt']and r['terminal']for r in rows),lr=dict(total_updates=ck['learner']['total_updates'],updates=ck['learner']['updates'],scheduler=ck['learner']['scheduler'],optimizer_lrs=[g['lr']for g in ck['learner']['optimizer']['param_groups']]))
 dump('coverage-summary.json',result);print('coverage',json.dumps(result),flush=True)

def main():
 start=time.perf_counter();torch.set_num_threads(2);OUT.mkdir(exist_ok=True);files=freeze();rankings();coverage();after={n:sha(ROOT/n) for n in files};assert files==after;dump('input-integrity-after.json',dict(unchanged=True,files=len(files)));dump('cpu-budget.json',dict(wall_seconds=time.perf_counter()-start,environment_decisions=0,optimizer_updates=0,device='cpu',threads=2))
if __name__=='__main__':main()
