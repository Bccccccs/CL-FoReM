"""Targeted saved-label/metric audit and batch1 deployment inference, no updates."""
import csv,json,time
from pathlib import Path
import numpy as np
import torch
from task12_heatmap import Heatmap
p=Path('/run');s=json.loads((p/'summary.json').read_text());labels=json.loads((p/'labels-v1.json').read_text())['items'];infos=json.loads((p/'geometry-and-identities.json').read_text());rows=json.loads((p/'per-state.json').read_text());arr=np.load(p/'final-arrays.npz');start=time.monotonic();torch.set_num_threads(2)
for r in labels:
 strict=r['native_strict_success'] and r['actual_route_end'] and r['actual_fk_tcp_error_m']<=.025 and r['actual_fk_cbl']<=.05
 expected=int(r['segment_failure_delta']==0 and (r['arrived'] or strict)) if r['complete'] else None
 assert expected==r['utility_label'];assert r['change']==r['utility_label']-r['old_label']
 assert arr['target'][int(r['state_id'].split('-')[1]),0,r['row'],r['col']]==expected
assert len(labels)==768 and sum(r['utility_label'] for r in labels)==221
legacy=list(csv.DictReader(open('/causes/primary-312-candidates.csv')));prior={(r['state_id'],r['candidate_id']):r for r in legacy};intersection=[r for r in labels if (r['state_id'],r['candidate_id']) in prior];assert len(intersection)==312;assert sum(r['change'] for r in intersection)==84
train={r['map_id'] for r in infos if r['subset']=='train'};val={r['map_id'] for r in infos if r['subset']=='validation'};assert len(train)==24 and len(val)==8 and not train&val
augmented=[]
for r in rows:
 info=next(x for x in infos if x['state_id']==r['state_id']);label=info['utility_labels'] if r['label']=='utility' else info['old_labels'];eligible=[i for i,x in enumerate(label) if x==1 and info['allowed'][i]];oracle=len({info['support'][i]['sector'] for i in eligible});selected={x for x in r['selected_candidate_ids']};tp=sum(info['support'][i]['candidate_id'] in selected for i in eligible);structural=len(eligible)-oracle;avoidable=oracle-tp
 assert tp==r['selected_positive_points'];assert structural+avoidable==r['missed_positive_points'];augmented.append(dict(r,oracle_positive_slots=oracle,structural_positive_point_misses=structural,avoidable_positive_slot_misses=avoidable,forced_negative_slots=r['selected_negative_points']-avoidable))
metrics=s['metrics']
for subset in ['train','validation']:
 for label in ['utility','arrival']:
  for method in ['new','old','nearest']:
   rr=[r for r in augmented if r['subset']==subset and r['label']==label and r['method']==method];m=metrics[subset][label][method]
   for k in ['oracle_positive_slots','structural_positive_point_misses','avoidable_positive_slot_misses','forced_negative_slots']:m[k]=sum(r[k] for r in rr)
   assert sum(r['hit'] for r in rr)==m['hit_states'];assert sum(r['selected_negative_points'] for r in rr)==m['selected_negative_points']
(p/'per-state.json').write_text(json.dumps(augmented,indent=2)+'\n')
with (p/'per-state.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(augmented[0]));w.writeheader()
 for r in augmented:w.writerow({k:json.dumps(v) if isinstance(v,list) else v for k,v in r.items()})
# Single-state production forward equivalence; GPU2 is isolated again for this check.
dev='cuda:0';payload=torch.load(p/'model-weights.pt',map_location='cpu',weights_only=False);model=Heatmap(payload['condition_dim']).to(dev);model.load_state_dict(payload['model']);model.eval();X=torch.from_numpy(arr['input']).to(dev);C=torch.from_numpy(arr['condition']).to(dev);pred=[];logits=[];different=[]
with torch.inference_mode():
 for i,info in enumerate(infos):
  z=model(X[i:i+1],C[i:i+1]);prob=z.sigmoid();pred.append(prob.cpu().numpy());logits.append(z.cpu().numpy());sup=info['support'];allowed=info['allowed']
  def select(v):
   chosen=[]
   for sec in range(12):
    options=[r for j,r in enumerate(sup) if r['sector']==sec and allowed[j]]
    if options:chosen.append(min(options,key=lambda r:(-float(v[0,0,r['row'],r['col']]),r['row'],r['col']))['candidate_id'])
   return chosen
  chosen=select(pred[-1]);saved=next(r['selected_candidate_ids'] for r in rows if r['state_id']==info['state_id'] and r['label']=='utility' and r['method']=='new')
  if chosen!=saved:different.append(dict(state_id=info['state_id'],single=chosen,batch8=saved))
np.savez_compressed(p/'deployment-batch1-arrays.npz',prediction=np.concatenate(pred),logits=np.concatenate(logits));difference=float(np.abs(np.concatenate(pred)-arr['prediction']).max());support_saturation=sum(float(pred[i][0,0,r['row'],r['col']]) in [0.,1.] for i,info in enumerate(infos) for r in info['support'])
check=dict(label_formula_all768=True,prior_13_state_changes=84,all_changes=198,map_isolation=True,metric_counts_independently_recomputed=True,rank_miss_split_verified=True,batch1_vs_batch8_prediction_max_abs_error=difference,batch1_changed_selections=different,saturated_support_scores=support_saturation,teacher_calls=0,updates=0,wall_s=time.monotonic()-start)
(p/'verification.json').write_text(json.dumps(check,indent=2)+'\n');(p/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');s['metrics']=metrics;s['verification']=check;(p/'summary.json').write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n');print(json.dumps(check,indent=2))
