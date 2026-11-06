"""Read-only independent scoring of B evidence; no torch/model/env imports."""
import argparse,csv,hashlib,json,datetime,sys
from pathlib import Path
from analysis import coverage,score
KEY=('map_id','seed','stream_index','role','source_split','proposal_seed')
PHASES=['01-4718-off','02-4718-on-gate','03-4718-remaining','04-4719-all','05-4720-all']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--run-config',required=True);parser.add_argument('--destination',required=True);args=parser.parse_args()
 cfg=read(Path(args.run_config));out=Path(cfg['output_root']);dest=Path(args.destination);dest.mkdir(exist_ok=False)
 csvpath=Path(cfg['workspace'])/'forem/doc/agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.csv';assert sha(csvpath)=='e36d1888b3bb5621f4a8c70d2eb2cea5316ae5883361017dead80de4169a57b8'
 frozen=list(csv.DictReader(csvpath.open()));records=[];historical=[]
 for f in frozen:
  seed=int(f['training_seed']);case=int(f['case_no'])
  phase=('02-4718-on-gate' if case in (1,3) else '03-4718-remaining') if seed==4718 else f'0{4 if seed==4719 else 5}-{seed}-all'
  root=out/phase;trace=root/f'case{case:02d}.jsonl';evaluation=root/'evaluation.json'
  r=dict(case_no=case,training_seed=seed,map_id=f['map_id'],episode_seed=int(f['seed']),historical={k:f[k] for k in ('strict_success','failures','terminated','truncated','transfers')},phase=phase,trace_path=str(trace) if trace.exists() else None,trace_sha256=sha(trace) if trace.exists() else None)
  if not trace.exists():r.update(execution_status='not_executed',classification='not_executed',missing_reasons=['target trace not collected'])
  elif not evaluation.exists():r.update(execution_status='partial_trace',classification='U',missing_reasons=['current original evaluate row unavailable; cannot establish transfers/terminal coverage'])
  else:
   ev=read(evaluation);name=f['source_collection'].split('.')[0];rows=ev[name]['rows'];row=next(x for x in rows if all(str(x[k])==f[k] for k in KEY));events=[json.loads(line) for line in trace.open()]
   result=score(events,row);r.update(result);r.update(execution_status='complete' if result['coverage']['complete'] else 'incomplete',outcome=row)
   diffs={k:dict(historical=f[k],current=row[k]) for k in ('strict_success','failures','terminated','truncated','transfers') if str(row[k])!=f[k]}
   r['historical_differences']=diffs
   if diffs:historical.append(dict(case_no=case,training_seed=seed,differences=diffs))
   first=r.get('first_rejection');recovery=r.get('recovery_event')
   if first:
    for event in events:
     if event.get('comparison',event)==first:r['first_rejection_detail']=event.get('detail',{});break
  records.append(r)
 counts={k:sum(r['classification']==k for r in records) for k in ('no_rejection','R','N','U','not_executed')};R,N,U=(counts[k] for k in ('R','N','U'));complete=[r for r in records if r['execution_status']=='complete'];blocked=sum(bool(r.get('first_rejection')) for r in complete)
 groups=[]
 for seed in (4718,4719,4720):
  for mapid in sorted({f['map_id'] for f in frozen}):
   group=[r for r in records if r['training_seed']==seed and r['map_id']==mapid]
   if group:groups.append(dict(seed=seed,map_id=mapid,cases=len(group),counts={k:sum(r['classification']==k for r in group) for k in counts}))
 evals=[];started=0
 for phase in PHASES:
  root=out/phase;status=read(root/'status.json') if (root/'status.json').exists() else None;evalpath=root/'evaluation.json';phase_started=sum(json.loads(line)['count'] for line in (root/'episodes-started.jsonl').open()) if (root/'episodes-started.jsonl').exists() else 0;started+=phase_started
  data=dict(phase=phase,started=phase_started,status=status)
  if evalpath.exists():
   e=read(evalpath);data['complete_episodes']=sum(len(e[name]['rows']) for name in ('validation','transfer'));data['evaluation_sha256']=sha(evalpath)
   # Keep full original historical differences separate from target-case diagnoses.
   seed=4718 if '4718' in phase else 4719 if '4719' in phase else 4720
   oldroot=Path(cfg['historical_root'])/f'results/task9/t9-stage2-20261029/B3_5M-seed{seed}'
   old=read(oldroot/'validation-5000000.json');changed=[]
   for name in ('validation','transfer'):
    by={tuple(str(x[k]) for k in KEY):x for x in old[name]['rows']}
    for row in e[name]['rows']:
     previous=by[tuple(str(row[k]) for k in KEY)];diff={k:dict(historical=previous[k],current=row[k]) for k in ('strict_success','failures','terminated','truncated','transfers') if row[k]!=previous[k]}
     if diff:changed.append(dict(collection=name,key={k:row[k] for k in KEY},differences=diff))
   data['historical_changed_episodes']=len(changed);data['historical_differences']=changed
  evals.append(data)
 summary=dict(run_id=cfg['run_id'],generated_shanghai=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),counts=counts,complete_target_cases=len(complete),strict_success_count=sum(r['outcome']['strict_success'] for r in complete),recovery_numerator=R,recovery_denominator=R+N,recovery_rate=R/(R+N) if R+N else None,all_blocked_R_N_U=R+N+U,first_rejection_episodes=blocked,first_rejection_rate=blocked/len(complete) if complete else None,actual_started_episodes=started,complete_evaluation_episodes=sum(e.get('complete_episodes',0) for e in evals),groups=groups,evaluations=evals,target_historical_differences=historical,case_results=records,scope='diagnostic selected cases, not population inference; B self-check, C remains independent')
 (dest/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 fields=['case_no','training_seed','map_id','episode_seed','execution_status','classification','strict_success','transfers','first_segment','first_action','first_substep','first_failure_kind','first_base','first_q','first_s','baseline_remaining_m','recovery_action','recovery_substep','max_reduction_m','unknown_reasons','trace_path','trace_sha256']
 with (dest/'case-results-30.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
  for r in records:
   row={k:r.get(k) for k in fields};first=r.get('first_rejection',{});rec=r.get('recovery_event',{});state=first.get('state',{});row.update(strict_success=r.get('outcome',{}).get('strict_success'),transfers=r.get('outcome',{}).get('transfers'),first_action=first.get('action'),first_substep=first.get('substep'),first_failure_kind=first.get('failure_kind'),first_base=json.dumps(state.get('base')),first_q=json.dumps(state.get('q')),first_s=state.get('s'),recovery_action=rec.get('action'),recovery_substep=rec.get('substep'),unknown_reasons='; '.join(r.get('missing_reasons',[])));writer.writerow(row)
 print(json.dumps({k:summary[k] for k in ('run_id','counts','complete_target_cases','actual_started_episodes','complete_evaluation_episodes','recovery_rate')}))
if __name__=='__main__':main()
