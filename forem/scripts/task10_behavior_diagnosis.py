import json, math, hashlib, time
from pathlib import Path
from collections import Counter
import torch
from task7_upper.model import UpperModel
from task10.learning import ReplayAdapter
from task7_upper.replay import row
from task7_upper.sac_discrete import distribution
ROOT=Path('/workspace/results/task10'); E=ROOT/'t10-long-eval-20261104-s101-r2'; T=ROOT/'t10-long-20261104-s101-r2/checkpoints'; O=ROOT/'t10-diagnosis-20261106/behavior'
torch.set_num_threads(2); start=time.monotonic(); allrows=[]; summary={}
with torch.no_grad():
 for n in (2000,5000,10000):
  p=T/f'decision-{n:06d}.actor.pt'; ck=torch.load(p,map_location='cpu',weights_only=False); model=UpperModel(vector_dim=ck['vector_dim']); model.load_state_dict(ck['model'],strict=True); model.eval().requires_grad_(False); adapter=ReplayAdapter(False,'cpu')
  run=E/f'checkpoint-{n:06d}'; records=[json.loads(x) for x in (run/'decisions.jsonl').read_text().splitlines()]; last=None; prev=None
  for rec in records:
   name=rec['episode_id']
   if name!=last: model.vcm.reset(); prev=None; last=name
   raw=torch.load(run/rec['raw_path'],map_location='cpu',weights_only=False); t=row(raw['fields'],0,1); item=adapter([t]); out=model.forward_step(**item); mask=item['mask'][0]; logits=out['logits'][0]; q1=out['q1'][0];q2=out['q2'][0];q=torch.minimum(q1,q2); prob,_=distribution(out['logits'],item['mask']); prob=prob[0]; valid=mask.nonzero().flatten().tolist(); selected=int(t['selected']); f=t['candidates']['f_k']; act=t['actual_result_v1']; pred=t['selected_prediction']; logged=rec['logits']; err=max(abs(float(logits[i])-logged[i]) for i in valid)
   cont=None if prev is None else {'previous_result_exact':torch.equal(t['observation']['previous_result_v1'],prev['actual_result_v1']), 'observation_route_abs_error':abs(float(t['observation']['route_s'])-float(prev['next_observation']['route_s'])), 'previous_link_match':t['previous_link']==prev['link']}
   scores=[]
   for i in valid:
    scores.append(dict(slot=i,logit=float(logits[i]),probability=float(prob[i]),q1=float(q1[i]),q2=float(q2[i]),min_q=float(q[i]),prediction=f[i].tolist(),inplace=bool(t['candidates']['inplace'][i]),world_pose=t['candidates']['world_pose'][i].tolist()))
   ai=max(valid,key=lambda i:float(logits[i])); qi=max(valid,key=lambda i:float(q[i])); qm=max([i for i in valid if i!=12],key=lambda i:float(q[i]),default=None); lm=max([i for i in valid if i!=12],key=lambda i:float(logits[i]),default=None)
   allrows.append(dict(checkpoint=n,episode=name,decision=rec['decision_index'],selected=selected,mask=valid,scores=scores,actor_argmax=ai,critic_argmax=qi,prob_inplace=float(prob[12]) if 12 in valid else None,uniform_p=1/len(valid),inplace_logit_gap=float(logits[12]-logits[lm]) if 12 in valid and lm is not None else None,inplace_q_gap=float(q[12]-q[qm]) if 12 in valid and qm is not None else None,alpha=.35,logit_error=err,selected_prediction_exact=torch.equal(pred,f[selected]),prediction=pred.tolist(),actual=act.tolist(),failures=int(t['r_t']['n_fail']),result_type=int(t['r_t']['result_type']),delta_s=float(t['r_t']['delta_s']),dt=float(t['dt']),continuity=cont,terminal=bool(t['terminated'] or t['truncated']),strict_success=bool(t['strict_success'])))
   prev=t
  init=[r for r in allrows if r['checkpoint']==n and r['decision']==0]; states=[r for r in allrows if r['checkpoint']==n]; summary[str(n)]={'initial_states':len(init),'inplace_selected_initial':sum(r['selected']==12 for r in init),'actor_critic_agree_initial':sum(r['actor_argmax']==r['critic_argmax'] for r in init),'mean_p_inplace':sum(r['prob_inplace'] for r in init)/len(init),'mean_uniform_p':sum(r['uniform_p'] for r in init)/len(init),'mean_q_gap':sum(r['inplace_q_gap'] for r in init)/len(init),'mean_logit_gap':sum(r['inplace_logit_gap'] for r in init)/len(init),'states':len(states),'max_logit_error':max(r['logit_error'] for r in states),'selected_prediction_match':all(r['selected_prediction_exact'] for r in states),'continuity_all':all(x['continuity']['previous_result_exact'] and x['continuity']['previous_link_match'] and x['continuity']['observation_route_abs_error'] == 0 for x in states if x['continuity'] is not None)}
result={'summary':summary,'rows':allrows,'conditions':'CPU replay saved sequential decisions; no environment steps, updates or GPU; same-checkpoint recurrent memory reset each episode. Prediction array index 0 arrival, 1:6 end one-hot, 6 first-failure ratio, 7 committed time, 8 timeout, 9:12 relative pose, 12 progress, 13:16 tracking maxima, 16:19 risk.', 'seconds':time.monotonic()-start}
(O/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(summary,indent=2))
import json, math, statistics
from pathlib import Path
p=Path('/workspace/results/task10/t10-diagnosis-20261106/behavior'); root=Path('/workspace/results/task10/t10-long-eval-20261104-s101-r2'); x=json.loads((p/'analysis.json').read_text()); out={}
def stat(xs):return {'mean':statistics.mean(xs),'max':max(xs),'min':min(xs)}
for n in (2000,5000,10000):
 recs=[json.loads(l) for l in (root/f'checkpoint-{n:06d}'/'decisions.jsonl').read_text().splitlines()]; lookup={(r['episode_id'],r['decision_index']):r for r in recs}; rows=[r for r in x['rows'] if r['checkpoint']==n]
 for r in rows:
  s=r['scores']; qs=[v['min_q'] for v in s]; ps=[v['probability'] for v in s]; qmax=max(qs); exp=[math.exp((q-qmax)/.35) for q in qs]; z=sum(exp); soft=[e/z for e in exp];
  r['q_regret']=qmax-next(v['min_q'] for v in s if v['slot']==r['actor_argmax']);r['kl_actor_to_qsoft']=sum(a*math.log(a/b) for a,b in zip(ps,soft) if a>0);r['probability_top_gap']=sorted(ps,reverse=True)[0]-sorted(ps,reverse=True)[1] if len(ps)>1 else None;r['q_range_over_alpha']=(max(qs)-min(qs))/.35;r['entropy_over_log_n']=-sum(a*math.log(a) for a in ps if a>0)/math.log(len(ps)) if len(ps)>1 else None
  d=lookup[(r['episode'],r['decision'])]['timing']['current']['cumulative_failures']; assert len(d)==len(s); r['predicted_failures_by_slot']={str(v['slot']):int(k) for v,k in zip(s,d)}; r['selected_predicted_failures']=r['predicted_failures_by_slot'][str(r['selected'])];r['alternative_zero_prediction']=any(k==0 and int(slot)!=r['selected'] for slot,k in r['predicted_failures_by_slot'].items())
 def block(a):
  return {'n':len(a),'argmax_disagreements':sum(r['actor_argmax']!=r['critic_argmax'] for r in a),'q_regret':stat([r['q_regret'] for r in a]),'kl_actor_to_qsoft':stat([r['kl_actor_to_qsoft'] for r in a]),'probability_top_gap':stat([r['probability_top_gap'] for r in a if r['probability_top_gap'] is not None]),'q_range_over_alpha':stat([r['q_range_over_alpha'] for r in a]),'entropy_over_log_n':stat([r['entropy_over_log_n'] for r in a if r['entropy_over_log_n'] is not None]),'selected_prediction_failure':sum(r['selected_predicted_failures']>0 for r in a),'selected_failure_with_alternative_zero':sum(r['selected_predicted_failures']>0 and r['alternative_zero_prediction'] for r in a),'actual_failure':sum(r['failures']>0 for r in a),'pred_failure_actual_failure':sum(r['selected_predicted_failures']>0 and r['failures']>0 for r in a),'pred_zero_actual_failure':sum(r['selected_predicted_failures']==0 and r['failures']>0 for r in a),'pred_failure_actual_zero':sum(r['selected_predicted_failures']>0 and r['failures']==0 for r in a)}
 out[str(n)]={'initial':block([r for r in rows if r['decision']==0]),'all':block(rows)}
(p/'metrics.json').write_text(json.dumps({'summary':out,'rows':x['rows'],'interpretation':'Predicted failures come from compact valid candidate timing.current.cumulative_failures aligned to mask order; absence of predicted failures is not evidence of successful counterfactual execution. KL is diagnostic against same-state softmax(minQ/0.35).'},indent=2,allow_nan=False)+'\n');print(json.dumps(out,indent=2))
