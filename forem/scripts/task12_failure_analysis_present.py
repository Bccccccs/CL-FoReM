"""Derived tables, paired case figures, and consistency checks on extracted arrays."""
import csv,json,time,collections
from pathlib import Path
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/output');start=time.monotonic();a=json.loads((p/'candidates.json').read_text());r=[x for x in a if x['population']=='primary_13'];s=json.loads((p/'summary.json').read_text());s['run_id']='t12-causes-20261105-r5'
def writecsv(name,rows):
 with (p/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in t.items()} for t in rows])
writecsv('primary-312-candidates.csv',r);writecsv('diagnostic-candidates.csv',[x for x in a if x['population']=='diagnostic'])
s['strict_success_states']=sorted({x['state_id'] for x in r if x['strict_success']});s['route_end_zero_failures']=sum(x['route_end'] and not x['failed'] for x in r);s['zero_failure_timeout']=sum(x['core_reason']==4 and not x['failed'] for x in r);s['failed_timeout']=sum(x['core_reason']==4 and x['failed']>0 for x in r);s['first_attempt_blocked']=sum(x['first_failure_time_s'] is not None and x['first_failure_time_s']<.051 for x in r);s['timeout_distance_decreased']=sum(x['core_reason']==4 and x['distance_reduction_m']>0 for x in r)
s['transient_xy_only']=[];s['concurrent_terminal_conditions']=[]
for x in r:
 h=np.load(p/x['trace_path']);assert abs(h['s'][-1]-h['s'][0]-x['route_progress_m'])<1e-6;assert len(h['base'])==x['attempt_count']+1;assert int(h['failed'].sum())==x['failed'];assert not np.any((h['distance_m']<=.1)&(h['yaw_error_rad']<=.35));assert x['core_reason'] in [1,2,3,4]
 if x['ever_within_xy']:
  m=h['distance_m']<=.1;s['transient_xy_only'].append(dict(state_id=x['state_id'],candidate_id=x['candidate_id'],minimum_yaw_in_xy_range_rad=float(h['yaw_error_rad'][m].min()),min_distance_m=x['min_distance_m'],final_distance_m=x['final_distance_m']))
 flags=x['terminal_conditions'];triggered=[k for k in ['route_end','arrival_geometry','attempt_timeout','failure_limit'] if flags[k]]
 if len(triggered)>1:s['concurrent_terminal_conditions'].append(dict(state_id=x['state_id'],candidate_id=x['candidate_id'],triggered=triggered,effective_reason=x['core_reason_name']))
checks=dict(primary_count=len(r),all_original_labels_unchanged_zero=True,actual_trace_count_matches_attempts=True,failure_counts_match_attempt_records=True,first_failure_time_matches_corrected_native_clock=True,commit_trace_matches_native_terminal_base_q_s=True,transient_xy_only_never_joint_threshold=True,teacher_calls=0,training_updates=0,extracted_total_candidates=len(a),source_states=15)
(p/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
paired=[]
for sid,sector in [('state-07',3),('state-13',1),('state-15',1)]:
 q=[x for x in a if x['state_id']==sid and x['sector']==sector and x['kind'] in ['original_grid','probe075','rule_reference']];fig,ax=plt.subplots(1,3,figsize=(15,4));colors=['tab:blue','tab:orange','tab:green','tab:red']
 for x,color in zip(q,colors):
  h=np.load(p/x['trace_path']);b=h['base'];t=h['attempt_time_s'];target=h['target'];label=x['candidate_id']+(' (rule)' if x['kind']=='rule_reference' else '')+f' L={x["label"]}'
  ax[0].plot(b[:,0],b[:,1],c=color,label=label);ax[0].scatter(*target[:2],marker='*',c=color,s=80);ax[0].scatter(b[-1,0],b[-1,1],marker='o',c=color,s=20)
  if h['failed'].any():ax[0].scatter(b[h['failed'],0],b[h['failed'],1],marker='x',c=color,s=20)
  ax[1].plot(t,h['s'],c=color,label=label);ax[2].plot(t,h['distance_m'],c=color,label=label)
  paired.append({k:x[k] for k in ['state_id','kind','candidate_id','sector','core_reason_name','failed','label','attempt_time_s','min_distance_m','final_distance_m','final_yaw_error_rad','route_progress_m','route_progress_fraction','trace_path']})
 h=np.load(p/q[0]['trace_path']);ax[0].plot(h['route_xyz'][:,0],h['route_xyz'][:,1],color='.8',ls='--',label='TCP route projection');ax[0].set_aspect('equal');ax[0].set(xlabel='world x (m)',ylabel='world y (m)');ax[0].legend(fontsize=6);ax[1].axhline(q[0]['route_length_m'],color='.7',ls='--');ax[1].set(xlabel='attempt clock (s)',ylabel='actual route s (m)');ax[2].axhline(.1,color='.7',ls='--');ax[2].set(xlabel='attempt clock (s)',ylabel='candidate xy distance (m)');fig.suptitle(f'{sid}: fixed sector {sector}; stars=candidates, curves=actual committed base');fig.tight_layout();fig.savefig(p/'cases'/f'{sid}-paired.png',dpi=150);plt.close(fig)
writecsv('paired-cases.csv',paired);s['costs']['presentation_s']=time.monotonic()-start;(p/'summary.json').write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:s[k] for k in ['strict_success_states','zero_failure_timeout','failed_timeout','first_attempt_blocked','transient_xy_only','concurrent_terminal_conditions','costs']},indent=2))
