import json,time,gzip,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,'/work/scripts')
# Avoid model imports: report is plain JSON/statistics only.
O=Path('/output')
def collect(arm):
 rows=[];costs=[]
 for p in sorted(O.glob(f'formal-{arm}-*')):
  if not p.is_dir() or not (p/'result.json').exists():continue
  result=json.loads((p/'result.json').read_text());rows+=result['rows'];costs.append(dict(batch=p.name,wall_s=result['wall_s'],cpu_s=result['cpu_s'],reset_s=result['reset_s'],requests=result['request_count'],inference_wall_s=sum(result['inference_wall_s']),ik_wall_s=sum(x['wall_s'] for x in result['ik_timing'])))
 assert len(rows)==588 and len({(r['training_seed'],r['domain'],r['domain_index']) for r in rows})==588,(arm,len(rows))
 return rows,costs

def summarize(rows):
 return dict(episodes=len(rows),strict_success=sum(r['strict_success'] for r in rows),final_arrival=sum(r['original_success'] for r in rows),arrival_after_failure=sum(r['original_success'] and r['failures']>0 for r in rows),first_rejection=sum(r['first_failure_kind'] is not None for r in rows),first_cause_counts={str(k):sum(r['first_failure_kind']==k for r in rows) for k in [None,1,2,3,4]},no_rejection_stagnation=sum(r['failures']==0 and not r['original_success'] and r['stalls']>=5 for r in rows),no_rejection_failure=sum(r['failures']==0 and not r['original_success'] for r in rows),transfers=sum(r['transfers'] for r in rows),attempted_substeps=sum(r['attempted_substeps'] for r in rows),committed_substeps=sum(r['committed_substeps'] for r in rows))

def main():
 a,ac=collect('current');b,bc=collect('bioik');bykey=lambda rows:{(r['training_seed'],r['domain'],r['domain_index']):r for r in rows};aa,bb=bykey(a),bykey(b);paired=[]
 for key in sorted(aa):
  x,y=aa[key],bb[key]
  for field in ('map_id','seed','pool'):assert x[field]==y[field]
  paired.append(dict(training_seed=key[0],domain=key[1],domain_index=key[2],map_id=x['map_id'],episode_seed=x['seed'],current=x,bioik=y,strict_diff=int(y['strict_success'])-int(x['strict_success'])))
 rng=np.random.default_rng(912112026);intervals={}
 for domain in ('random','semantic'):
  rows=[r for r in paired if r['domain']==domain];maps=sorted({r['map_id'] for r in rows});x=np.array([np.mean([r['strict_diff'] for r in rows if r['map_id']==m]) for m in maps]);resampled=x[rng.integers(0,len(x),size=(10000,len(x)))].mean(1)
  intervals[domain]=dict(method='paired map-cluster bootstrap; preserve all policy seeds/episode seeds within each sampled map',replicates=10000,seed=912112026,estimate=float(x.mean()),percentile95=[float(v) for v in np.quantile(resampled,[.025,.975])],maps=len(maps),episodes=len(rows),unit='strict-success probability difference BioIK minus current',limitation='repeatedly analyzed development maps; three historical training weights, not independent test')
 report=dict(status='complete',created_epoch=time.time(),per_seed={str(seed):{domain:{arm:summarize([r for r in rows if r['training_seed']==seed and r['domain']==domain]) for arm,rows in [('current',a),('bioik',b)]} for domain in ('random','semantic')} for seed in (4718,4719,4720)},aggregate={domain:{arm:summarize([r for r in rows if r['domain']==domain]) for arm,rows in [('current',a),('bioik',b)]} for domain in ('random','semantic')},strict_difference_intervals=intervals,costs={'current':ac,'bioik':bc},policy_learning_updates=0,training_transfers=0,smoke_episodes_separate=32,paired_diagnostic=json.loads((O/'paired-summary.json').read_text()),constraints=dict(rewards_actions_termination_candidates='unchanged',replacement_scope='Core execution solve_world only; sampling and candidate search retain existing IK',collision='same FoReM robot/scene checks',solver_package_difference='BioIK soft-goals/no internal collision callback vs analytic branch self/ground selection; no claim pure mathematical algorithm comparison',randomness='fixed initial seed, timeout-driven variation; all three paired repeats retained'),recommendation='pending_parent_judgement: inspect each domain/seed, first-rejection mechanism and end-to-end cost; aggregate strict total is descriptive only; mixed results are insufficient evidence/tradeoff')
 report['deltas_by_seed']={str(seed):{domain:{'strict_success_count':sum(int(y['strict_success'])-int(x['strict_success']) for key,x in aa.items() for y in [bb[key]] if key[0]==seed and key[1]==domain),'first_rejection_count':sum(int(y['first_failure_kind'] is not None)-int(x['first_failure_kind'] is not None) for key,x in aa.items() for y in [bb[key]] if key[0]==seed and key[1]==domain)} for domain in ('random','semantic')} for seed in (4718,4719,4720)}
 report['cost_totals']={arm:{field:sum(r[field] for r in costs) for field in ('wall_s','cpu_s','reset_s','requests','inference_wall_s','ik_wall_s')} for arm,costs in [('current',ac),('bioik',bc)]}
 (O/'paired-episodes.json').write_text(json.dumps(paired,indent=2)+'\n');(O/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(event='report_complete',recommendation=report['recommendation'],aggregate=report['aggregate'],intervals=intervals)),flush=True)
if __name__=='__main__':main()
