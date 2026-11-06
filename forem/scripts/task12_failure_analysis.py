#!/usr/bin/env python3
"""Read-only CPU attribution of saved B3 records. No policy calls, step or relabel."""
import argparse,csv,json,time,hashlib,collections,math
from pathlib import Path
import numpy as np
import torch
from task10.boundary_state import decode
from task7_sim.kinematics import Kinematics,metrics

def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvwrite(p,rows):
 if not rows:return
 with p.open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
  for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})
def wrap(x):return np.arctan2(np.sin(x),np.cos(x))
def stats(v):
 a=np.asarray(v,float);return dict(n=len(a),min=float(a.min()),p25=float(np.quantile(a,.25)),p50=float(np.median(a)),p75=float(np.quantile(a,.75)),max=float(a.max())) if len(a) else {'n':0}
def counts(rows,key):return dict(collections.Counter(str(r[key]) for r in rows))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',default='/baseline');ap.add_argument('--probe',default='/probe');ap.add_argument('--out',default='/output');ap.add_argument('--run-id',default='t12-causes-20261105-r5');a=ap.parse_args()
 torch.set_num_threads(2);start=time.monotonic();base=Path(a.baseline);probe=Path(a.probe);out=Path(a.out);out.mkdir(exist_ok=True);(out/'trajectories').mkdir(exist_ok=True);(out/'cases').mkdir(exist_ok=True)
 rows0=[json.loads(p.read_text()) for p in sorted((base/'states').glob('*/row.json'))];zero=[r['state_id'] for r in rows0 if r['category']==1];assert len(zero)==13
 js(out/'analysis-plan.json',dict(scope=zero,expected_primary_candidates=312,diagnostic_extra_states=['state-13','state-15'],representative_rule='lexicographic first state/candidate per Core reason and first failure type; force state07 recovered probe and state13/15 lost far positives',thresholds={'arrival_xy_m':.1,'arrival_yaw_rad':.35,'stall_route_m':.01,'stall_base_m':.05,'task_tcp_m':.025,'task_cbl':.05},teacher_calls=0,updates=0))
 kin=Kinematics();allrows=[];stateinfo={};examples={};attempt_file=(out/'attempts.jsonl').open('w');wallreads=0.;extraction=0.
 for sid in sorted(set(zero+['state-13','state-15'])):
  begin=time.monotonic();d=base/'states'/sid;source=decode(torch.load(d/'source.pt',map_location='cpu',weights_only=False)['core'],device='cpu');spec=json.loads((d/'row.json').read_text());initialfail=int(source['failures'][0]);wallreads+=time.monotonic()-begin
  stateinfo[sid]=dict(map_id=spec['map_id'],difficulty=spec['difficulty'],route_length_m=float(source['route'].length[0]),source_failures=initialfail)
  batches=[(d/'grid-0','original_grid'),(d/'grid-1','original_grid'),(d/'rules','rule_reference'),(d/'decoded-extra','inplace'),(probe/'states'/sid/'probe075','probe075')]
  for path,kind in batches:
   begin=time.monotonic();data=torch.load(path/'data.pt',map_location='cpu',weights_only=False);c=decode(data['core'],device='cpu');wallreads+=time.monotonic()-begin;begin=time.monotonic();records=data['records'];n=len(records);ats=c['attempts'];trace=c['trace'];traceptr=0;state=trace[0][0];assert bool(trace[0][1].all())
   attempts_count=np.zeros(n,dtype=int);commits=np.zeros(n,dtype=int);failcounts=np.zeros(n,dtype=int);first=[None]*n;types=[collections.Counter() for _ in range(n)];concurrent=[collections.Counter() for _ in range(n)];hist=[dict(base=[state.base[i].tolist()],s=[float(state.s[i])],attempt_s=[0.],commit_s=[0.],failed=[False],global_attempt=[-1]) for i in range(n)]
   for j,at in enumerate(ats):
    before=state
    if bool(at['committed'].any()):
     traceptr+=1;state,mask=trace[traceptr];assert torch.equal(mask,at['committed'])
    for i in torch.where(at['active'])[0].tolist():
     attempts_count[i]+=1;commit=bool(at['committed'][i]);commits[i]+=int(commit);failed=not commit
     triggers=[]
     if int(at['ik_status'][i])>=2:triggers.append('ik_reject')
     for k,t in [('base_collision','base_collision'),('arm_collision','arm_collision'),('self_collision','self_collision')]:
      if bool(at[k][i]):triggers.append(t)
     if failed:
      failcounts[i]+=1;typ=next((t for t in ['ik_reject','base_collision','arm_collision','self_collision'] if t in triggers),'unknown');types[i][typ]+=1;concurrent[i]['+'.join(triggers)]+=1
      entry=dict(global_attempt_index=j,candidate_attempt_index=int(attempts_count[i]),attempt_time_s=float(attempts_count[i]*.05),commit_time_before_s=float((commits[i]-int(commit))*.05),triggers=triggers,core_priority_type=typ,actual_base_before=before.base[i].tolist(),actual_s_before=float(before.s[i]),ik_status=int(at['ik_status'][i]),ik_position_residual_m=float(at['position_m'][i]),ik_cbl=float(at['cbl'][i]),ik_angle_residual_rad=float(at['angle_rad'][i]),uncommitted_trial_base=None)
      if first[i] is None:first[i]=entry
     else:entry=None
     attempt_file.write(json.dumps(dict(state_id=sid,kind=kind,candidate_id=records[i]['candidate_id'],global_attempt_index=j,candidate_attempt_index=int(attempts_count[i]),attempt_time_s=float(attempts_count[i]*.05),committed=commit,commit_time_s=float(commits[i]*.05),triggers=triggers,actual_base=state.base[i].tolist(),actual_s=float(state.s[i]),ik_status=int(at['ik_status'][i]),failure=entry),allow_nan=False)+'\n')
     h=hist[i];h['base'].append(state.base[i].tolist());h['s'].append(float(state.s[i]));h['attempt_s'].append(float(attempts_count[i]*.05));h['commit_s'].append(float(commits[i]*.05));h['failed'].append(failed);h['global_attempt'].append(j)
   assert traceptr==len(trace)-1
   actual_tcp=kin.world_tcp(c['state'].base,c['state'].q);end_tcp=c['route'].at(c['route'].length);tcpdist,cbl,angle=metrics(actual_tcp,end_tcp)
   for i,r in enumerate(records):
    assert attempts_count[i]==int(c['attempted_segment'][i]);assert commits[i]==int(c['segment_substeps'][i]);assert failcounts[i]==r['failed'];assert torch.equal(state.base[i],c['state'].base[i]);assert torch.equal(state.q[i],c['state'].q[i]);assert float(state.s[i])==float(c['state'].s[i])
    h=hist[i];b=np.array(h['base']);s=np.array(h['s']);target=c['candidate'].pose[i].numpy();dist=np.linalg.norm(b[:,:2]-target[:2],axis=1);yaw=np.abs(wrap(target[2]-b[:,2]));route_len=float(c['route'].length[i]);delta_s=float(s[-1]-s[0]);disp=float(np.linalg.norm(b[-1,:2]-b[0,:2]));travel=float(np.linalg.norm(np.diff(b[:,:2],axis=0),axis=1).sum());attempts_s=float(attempts_count[i]*.05);timeout=float(c['timeout'][i]);reason=int(c['reason'][i]);routeend=bool(c['state'].s[i]==c['route'].length[i]);reached=bool(float(dist[-1])<=.1 and float(yaw[-1])<=.35);progress_required=bool(c['candidate'].inplace[i]) or not c['synchronous'];capreached=bool(c['state'].s[i]==c['cap'][i]);timeoutflag=attempts_s>=timeout;limitflag=int(c['failures'][i])>=c['failure_limit'];success=routeend and float(tcpdist[i])<=.025 and float(cbl[i])<=.05
    cell=('arrived_' if r['arrived'] else 'not_arrived_')+('with_failure' if r['failed'] else 'zero_failure');f=first[i];timefirst=float(c['first_failure_time'][i]) if f else None
    if f:assert abs(timefirst-f['attempt_time_s'])<1e-4
    row=dict(state_id=sid,map_id=spec['map_id'],difficulty=spec['difficulty'],population='primary_13' if sid in zero and kind=='original_grid' else 'diagnostic',kind=kind,candidate_id=r['candidate_id'],sector=r['sector'],compact_row=i,local_pose=r['pose'],world_target=target.tolist(),arrived=r['arrived'],failed=r['failed'],label=r['label'],arrival_failure_class=cell,core_reason=reason,core_reason_name={0:'candidate_arrival',1:'route_end',2:'ik_failure_limit',3:'collision_failure_limit',4:'segment_timeout'}[reason],first_failure_type=f['core_priority_type'] if f else 'none',first_failure_time_s=timefirst,first_failure_global_attempt=f['global_attempt_index'] if f else None,first_failure_triggers=f['triggers'] if f else [],first_failure_actual_base=f['actual_base_before'] if f else None,attempt_count=int(attempts_count[i]),committed_count=int(commits[i]),attempt_time_s=attempts_s,committed_time_s=float(commits[i]*.05),timeout_s=timeout,native_failure_kind=int(c['failure_kind'][i]),failure_limit=int(c['failure_limit']),failure_priority_counts=dict(types[i]),concurrent_failure_counts=dict(concurrent[i]),final_distance_m=float(dist[-1]),min_distance_m=float(dist.min()),initial_distance_m=float(dist[0]),distance_reduction_m=float(dist[0]-dist[-1]),final_yaw_error_rad=float(yaw[-1]),min_yaw_error_rad=float(yaw.min()),final_within_xy=bool(dist[-1]<=.1),final_within_yaw=bool(yaw[-1]<=.35),ever_within_xy=bool((dist<=.1).any()),ever_joint_arrival_geometry=bool(((dist<=.1)&(yaw<=.35)).any()),base_displacement_m=disp,base_path_length_m=travel,route_progress_m=delta_s,route_length_m=route_len,route_progress_fraction=delta_s/max(route_len-s[0],1e-12),below_stall_route=delta_s<.01,below_stall_base=disp<.05,exceeds_stall_route_threshold=delta_s>=.01,route_end=routeend,actual_task_success_geometry=success,strict_success=bool(c['strict_success'][i]),final_task_tcp_error_m=float(tcpdist[i]),final_task_cbl=float(cbl[i]),final_task_angle_rad=float(angle[i]),terminal_conditions={'route_end':routeend,'arrival_geometry':reached,'progress_required':progress_required,'cap_reached':capreached,'attempt_timeout':timeoutflag,'failure_limit':limitflag},native_terminated=bool(c['terminated'][i]),native_truncated=bool(c['truncated'][i]),raw_path=str(path/'data.pt'),trace_path=f'trajectories/{sid}-{kind}-{r["candidate_id"]}.npz',trajectory_complete=True)
    np.savez_compressed(out/row['trace_path'],base=b,s=s,attempt_time_s=np.array(h['attempt_s']),committed_time_s=np.array(h['commit_s']),failed=np.array(h['failed']),global_attempt=np.array(h['global_attempt']),target=target,distance_m=dist,yaw_error_rad=yaw,route_xyz=c['route'].xyz[i].numpy(),route_s=c['route'].s[i].numpy(),route_length_m=route_len)
    allrows.append(row)
   extraction+=time.monotonic()-begin
  print(sid,'done',flush=True)
 attempt_file.close();primary=[r for r in allrows if r['population']=='primary_13'];assert len(primary)==312 and all(r['label']==0 for r in primary)
 csvwrite(out/'candidates.csv',allrows);js(out/'candidates.json',allrows)
 state_rows=[]
 for sid in zero:
  rr=[r for r in primary if r['state_id']==sid];diag=[r for r in allrows if r['state_id']==sid and r['kind']!='original_grid'];state_rows.append(dict(state_id=sid,**stateinfo[sid],candidates=len(rr),arrival_failure_classes=counts(rr,'arrival_failure_class'),effective_reasons=counts(rr,'core_reason_name'),first_failure_types=counts(rr,'first_failure_type'),with_route_progress_ge_001=sum(r['exceeds_stall_route_threshold'] for r in rr),both_below_stall_thresholds=sum(r['below_stall_route'] and r['below_stall_base'] for r in rr),within_xy=sum(r['final_within_xy'] for r in rr),route_end=sum(r['route_end'] for r in rr),actual_task_success=sum(r['actual_task_success_geometry'] for r in rr),distance=stats([r['final_distance_m'] for r in rr]),progress_m=stats([r['route_progress_m'] for r in rr]),progress_fraction=stats([r['route_progress_fraction'] for r in rr]),max_base_displacement_m=max(r['base_displacement_m'] for r in rr),diagnostic_positive={k:[r['candidate_id'] for r in diag if r['kind']==k and r['label']==1] for k in ['rule_reference','inplace','probe075']}))
 csvwrite(out/'states.csv',state_rows);js(out/'states.json',state_rows)
 summary=dict(run_id=a.run_id,teacher_calls=0,updates=0,states=13,primary_candidates=312,source_runs=['t12-cost32-20261104-r3','t12-radius075-20261104-r4'],arrival_failure_classes=counts(primary,'arrival_failure_class'),effective_reasons=counts(primary,'core_reason_name'),first_failure_types=counts(primary,'first_failure_type'),failure_priority_attempts=dict(sum((collections.Counter(r['failure_priority_counts']) for r in primary),collections.Counter())),concurrent_failure_attempts=dict(sum((collections.Counter(r['concurrent_failure_counts']) for r in primary),collections.Counter())),route_progress_ge_stall_001=sum(r['route_progress_m']>=.01 for r in primary),both_below_stall_thresholds=sum(r['below_stall_route'] and r['below_stall_base'] for r in primary),route_end=sum(r['route_end'] for r in primary),actual_task_success=sum(r['actual_task_success_geometry'] for r in primary),strict_success=sum(r['strict_success'] for r in primary),final_within_xy=sum(r['final_within_xy'] for r in primary),ever_within_xy=sum(r['ever_within_xy'] for r in primary),progress=stats([r['route_progress_m'] for r in primary]),progress_fraction=stats([r['route_progress_fraction'] for r in primary]),final_distance=stats([r['final_distance_m'] for r in primary]),yaw=stats([r['final_yaw_error_rad'] for r in primary]),first_failure_s=stats([r['first_failure_time_s'] for r in primary if r['failed']]),max_source_failures=max(x['source_failures'] for x in stateinfo.values()),by_difficulty={},by_reason={},diagnostics={},gaps=['Uncommitted trial base positions not retained; failure markers show actual pre-attempt committed base, not rejected pose.','Actor-call boundaries not saved per attempt; time axis uses candidate attempted substeps, each 0.05s.','Local sensor-only prediction is not full-route physical execution.'],costs={'read_decode_s':wallreads,'extraction_write_s':extraction})
 for k in ['sparse','standard']:
  rr=[r for r in primary if r['difficulty']==k];summary['by_difficulty'][k]=dict(states=len(set(r['state_id'] for r in rr)),candidates=len(rr),classes=counts(rr,'arrival_failure_class'),reasons=counts(rr,'core_reason_name'))
 for k in sorted(set(r['core_reason_name'] for r in primary)):
  rr=[r for r in primary if r['core_reason_name']==k];summary['by_reason'][k]=dict(candidates=len(rr),states=len(set(r['state_id'] for r in rr)),route_end=sum(r['route_end'] for r in rr),within_xy=sum(r['final_within_xy'] for r in rr),progress_m=stats([r['route_progress_m'] for r in rr]),distance_m=stats([r['final_distance_m'] for r in rr]),yaw_rad=stats([r['final_yaw_error_rad'] for r in rr]))
 for k in ['rule_reference','inplace','probe075']:
  rr=[r for r in allrows if r['state_id'] in zero and r['kind']==k];summary['diagnostics'][k]=dict(candidates=len(rr),positive=sum(r['label'] for r in rr),positive_states=sorted(set(r['state_id'] for r in rr if r['label'])),reasons=counts(rr,'core_reason_name'))
 for key in ['core_reason_name','first_failure_type']:
  for typ in sorted(set(r[key] for r in primary)):
   if typ=='none':continue
   examples[key+':'+typ]=next(r for r in primary if r[key]==typ)
 for sid,kind in [('state-07','probe075'),('state-13','original_grid'),('state-15','original_grid')]:
  examples[sid+'-positive']=next(r for r in allrows if r['state_id']==sid and r['kind']==kind and r['label'])
 # Also closest old candidate for recovered state07, defined solely by final distance.
 examples['state-07-closest-old']=min([r for r in primary if r['state_id']=='state-07'],key=lambda r:(r['final_distance_m'],r['candidate_id']))
 js(out/'case-selection.json',{k:{f:r[f] for f in ['state_id','candidate_id','kind','core_reason_name','first_failure_type','trace_path']} for k,r in examples.items()})
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 for name,r in examples.items():
  h=np.load(out/r['trace_path']);b=h['base'];t=h['attempt_time_s'];failed=h['failed'];target=h['target'];fig,ax=plt.subplots(1,3,figsize=(15,4));ax[0].plot(h['route_xyz'][:,0],h['route_xyz'][:,1],color='.7',label='TCP route projection');ax[0].plot(b[:,0],b[:,1],'k-',label='committed base');ax[0].scatter(b[0,0],b[0,1],c='green',label='start');ax[0].scatter(b[-1,0],b[-1,1],c='blue',label='terminal');ax[0].scatter(*target[:2],marker='*',s=120,c='orange',label='candidate');ax[0].scatter(b[failed,0],b[failed,1],marker='x',c='red',label='failed attempt: actual base');ax[0].set_aspect('equal');ax[0].set(xlabel='world x (m)',ylabel='world y (m)');ax[0].legend(fontsize=6)
  ax[1].plot(t,h['s'],label='actual route s');ax[1].axhline(r['route_length_m'],ls='--',color='.5',label='route end');ax[1].scatter(t[failed],h['s'][failed],c='red',s=6);ax[1].set(xlabel='attempt clock (s)',ylabel='route progress s (m)');ax[1].legend(fontsize=7)
  ax[2].plot(t,h['distance_m'],label='target xy distance (m)');ax[2].axhline(.1,color='blue',ls='--',label='xy threshold .1m');ay=ax[2].twinx();ay.plot(t,h['yaw_error_rad'],c='orange',label='yaw error (rad)');ay.axhline(.35,color='orange',ls='--');ax[2].set(xlabel='attempt clock (s)',ylabel='distance (m)');ay.set_ylabel('yaw error (rad)');ax[2].legend(fontsize=7)
  fig.suptitle(f'{name} | {r["state_id"]}/{r["candidate_id"]} | {r["core_reason_name"]}, label={r["label"]}');fig.tight_layout();fig.savefig(out/'cases'/(name.replace(':','-')+'.png'),dpi=150);plt.close(fig)
 summary['costs']['total_analysis_s']=time.monotonic()-start;summary['case_count']=len(examples);js(out/'summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
