#!/usr/bin/env python3
"""Parent checks original first-update tensors, source hashes and derived tables."""
import csv,json,hashlib,time
from pathlib import Path
import torch
R=Path('/workspace/results/task10');D=R/'t10-diag-20261103-s101';T=R/'t10-online-20261102-s101';E=R/'t10-eval-20261103-s101'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def load(p):return torch.load(p,map_location='cpu',weights_only=False)
def main():
 start=time.perf_counter();torch.set_num_threads(2);hashes=json.loads((D/'signal-evidence-hashes.json').read_text());assert all(sha(D/n)==h for n,h in hashes.items());assert sha(Path('/workspace/scripts/task10_signal_diagnostic.py'))==hashes['signal-code.py']
 a=load(D/'signal-first-update-tensors.pt');s=json.loads((D/'signal-summary.json').read_text());original=load(T/'first-update-evidence.pt')['update_result'];c=a['current'];n=a['following'];q=a['target_following'];b=a['batch'];m=a['mask'];nm=a['nextmask'];alpha=.35
 lp=n['logits'].masked_fill(~nm,-torch.inf).log_softmax(-1);p=lp.exp();lp=lp.masked_fill(~nm,0);minq=torch.minimum(q['q1'],q['q2']).masked_fill(~nm,0)
 y=b['reward']+b['bootstrap_mask']*.99**(b['dt']/.1)*(p*(minq-alpha*lp)).sum(-1);err=float((y-a['target']).abs().max());assert err<2e-7
 loss=.5*sum((c[k].gather(-1,b['selected'].long()[:,None]).squeeze()-y).square().mean()for k in ('q1','q2'));assert abs(float(loss)-original['critic'])<2e-7
 lp=c['logits'].masked_fill(~m,-torch.inf).log_softmax(-1);p=lp.exp();lp=lp.masked_fill(~m,0);aq=torch.minimum(c['actor_q1'],c['actor_q2']).masked_fill(~m,0);actor=(p*(alpha*lp-aq)).sum(-1).mean();assert abs(float(actor)-original['actor'])<2e-7
 rows=list(csv.DictReader((D/'signal-first-update-rows.csv').open()));assert len(rows)==49
 source=load(T/'first-update-before.pt');replay=source['replay']['episodes'];ident_count=0
 for rr in rows:
  key=('t10-online-20261102-s101',int(rr['environment']),int(rr['episode']));t=replay[key][int(rr['decision'])]
  assert int(rr['selected'])==int(t['selected']) and float(rr['reward'])==float(t['reward']) and float(rr['bootstrap_mask'])==float(t['bootstrap_mask']);ident_count+=1
 chain=list(csv.DictReader((D/'signal-stall-chain-rows.csv').open()));ends=[x for x in chain if x['model']=='final' and x['bootstrap_mask']=='0.0'];failure=[x for x in ends if x['strict_success']=='False'];assert len(ends)==8 and len(failure)==7
 final_replay=load(T/'offline-learner.pt')['replay']['episodes']
 for rr in failure:
  t=final_replay[('t10-online-20261102-s101',int(rr['environment']),int(rr['episode']))][int(rr['decision'])]
  assert int(t['selected'])==int(rr['selected']) and float(t['reward'])==-1 and float(t['bootstrap_mask'])==0 and bool(t['triggers']['stall_limit']) and not bool(t['strict_success'])
  assert rr['selected']in ('1','2','3')and float(rr['target'])==-1 and float(rr['target_entropy_contribution'])==0 and float(rr['target_Q_contribution'])==0
 frozen=json.loads((D/'input-freeze.json').read_text());changed=[n for n,h in frozen['files'].items()if sha(Path('/workspace')/n)!=h];assert not changed
 transitions=list(csv.DictReader((D/'replay-transitions.csv').open()));assert all(float(x['phi_after'])==0 for x in transitions if x['terminal']=='True')
 assert len(transitions)==1200 and len({(x['environment'],x['episode_id'],x['decision'])for x in transitions})==1200
 rankings=list(csv.DictReader((D/'state-rankings.csv').open()));assert len(rankings)==104 and all(float(x['record_logit_gap'])>0 for x in rankings)
 result=dict(status='verified',signal_hashes_verified=len(hashes),first_update_loss_rows_original_identity_checked=ident_count,target_max_abs_error=err,critic_cpu=float(loss),actor_cpu=float(actor),critic_original_gpu=original['critic'],actor_original_gpu=original['actor'],stall_trigger_terminal_rows=len(ends),stall_failure_terminal_rows=len(failure),original_input_files_unchanged=len(frozen['files']),new_environment_decisions=0,new_updates=0,gpu_seconds=0,wall_seconds=time.perf_counter()-start)
 (D/'parent-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
