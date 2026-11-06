#!/usr/bin/env python3
"""Standard-library paired statistics for task12.7's frozen sealed evaluation."""
import csv,json
from pathlib import Path
METHODS=('new','r6','nearest')
LABELS=('utility','arrival')
def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n');tmp.replace(path)
def csvwrite(path,rows):
 if not rows:return
 keys=list(dict.fromkeys(k for row in rows for k in row))
 with Path(path).open('w') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
  for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})
def state_metrics(labels,allowed,selected,support):
 known={i for i,v in enumerate(labels) if v is not None};positive={i for i in known if labels[i]==1};eligible=positive&{i for i,v in enumerate(allowed) if v};sel=set(selected);sectors={support[i]['sector'] for i in eligible};selected_pos=eligible&sel
 return dict(known=len(known),unknown=24-len(known),positive_points=len(positive),allowed_positive_points=len(eligible),positive_sectors=len(sectors),coverage_pre=bool(positive),coverage_post=bool(eligible),hit=bool(selected_pos),selected_positive_points=len(selected_pos),selected_negative_points=sum(labels[i]==0 for i in sel if i in known),selected_unknown_points=len(sel-known),missed_positive_state=bool(eligible) and not selected_pos,missed_positive_points=len(eligible-sel),avoidable_slot_misses=len(sectors)-len(selected_pos),selected_candidate_ids=[support[i]['candidate_id'] for i in selected],positive_candidate_ids=[support[i]['candidate_id'] for i in sorted(selected_pos)],allowed_positive_candidate_ids=[support[i]['candidate_id'] for i in sorted(eligible)],valid_moving_slots=len(sel))
def aggregate(rows,denominator=None):
 n=len(rows) if denominator is None else denominator;coverage=sum(r['coverage_post'] for r in rows);hits=sum(r['hit'] for r in rows);tp=sum(r['selected_positive_points'] for r in rows);eligible=sum(r['allowed_positive_points'] for r in rows);positive_sectors=sum(r['positive_sectors'] for r in rows)
 return dict(states=n,observed_states=len(rows),complete_states=sum(r['known']==24 for r in rows),missing_states=n-sum(r['known']==24 for r in rows),unknown_candidates=sum(r['unknown'] for r in rows)+24*(n-len(rows)),coverage_pre=sum(r['coverage_pre'] for r in rows),coverage_post=coverage,confirmed_no_allowed_positive_states=sum(r['known']==24 and not r['coverage_post'] for r in rows),unknown_positive_existence_states=sum(r['known']<24 and not r['coverage_post'] for r in rows),hit_states=hits,overall_hit_rate=hits/n if n else None,conditional_hit_rate=hits/coverage if coverage else None,missed_positive_states=sum(r['missed_positive_state'] for r in rows),allowed_positive_points=eligible,positive_sectors=positive_sectors,selected_positive_points=tp,selected_negative_points=sum(r['selected_negative_points'] for r in rows),selected_unknown_points=sum(r['selected_unknown_points'] for r in rows),missed_positive_points=sum(r['missed_positive_points'] for r in rows),avoidable_slot_misses=sum(r['avoidable_slot_misses'] for r in rows),positive_sector_hit_rate=tp/positive_sectors if positive_sectors else None,positive_point_recall=tp/eligible if eligible else None,valid_moving_slots=sum(r['valid_moving_slots'] for r in rows))
def paired(rows,baseline):
 out={}
 for label in LABELS:
  lookup={(r['state_id'],r['method']):r for r in rows if r['label']==label};items=[]
  for sid in sorted({r['state_id'] for r in rows}):
   a=lookup[(sid,'new')];b=lookup[(sid,baseline)];gained=sorted(set(a['positive_candidate_ids'])-set(b['positive_candidate_ids']));lost=sorted(set(b['positive_candidate_ids'])-set(a['positive_candidate_ids']))
   items.append(dict(state_id=sid,map_id=a['map_id'],difficulty=a['difficulty'],new_hit=a['hit'],baseline_hit=b['hit'],point_delta=a['selected_positive_points']-b['selected_positive_points'],state_delta=int(a['hit'])-int(b['hit']),gained_positive_candidates=gained,lost_positive_candidates=lost,new_selected=a['selected_candidate_ids'],baseline_selected=b['selected_candidate_ids']))
  out[label]=dict(baseline=baseline,point_gain_states=sum(r['point_delta']>0 for r in items),point_loss_states=sum(r['point_delta']<0 for r in items),point_equal_states=sum(r['point_delta']==0 for r in items),state_gain=sum(r['state_delta']>0 for r in items),state_loss=sum(r['state_delta']<0 for r in items),state_equal=sum(r['state_delta']==0 for r in items),both_hit=sum(r['new_hit'] and r['baseline_hit'] for r in items),both_miss=sum(not r['new_hit'] and not r['baseline_hit'] for r in items),all_pairs=items,all_point_or_state_degradations=[r for r in items if r['point_delta']<0 or r['state_delta']<0 or r['lost_positive_candidates']])
 return out

def summarize(rows,candidates,specs,engineering_checks=True):
 denominators={'all':len(specs),**{d:sum(s['difficulty']==d for s in specs) for d in ('sparse','standard')}}
 groups={}
 for group,n in denominators.items():
  group_rows=rows if group=='all' else [r for r in rows if r['difficulty']==group]
  groups[group]={label:{method:aggregate([r for r in group_rows if r['method']==method and r['label']==label],n) for method in METHODS} for label in LABELS}
 unique={}
 for typ in ('all','arrival','route_only'):
  ids=set()
  for spec in specs:
   points=[r for r in candidates if r['state_id']==spec['state_id'] and r['geometry_allowed'] and r['utility_label']==1]
   known_state=all(r['utility_label'] is not None for r in candidates if r['state_id']==spec['state_id'])
   if len(points)==1 and known_state and (typ=='all' or typ=='arrival' and points[0]['old_label']==1 or typ=='route_only' and points[0]['old_label']!=1):ids.add(spec['state_id'])
  unique[typ]=dict(states=len(ids),state_ids=sorted(ids),methods={m:aggregate([r for r in rows if r['label']=='utility' and r['method']==m and r['state_id'] in ids],len(ids)) for m in METHODS})
 a=groups['all']['utility'];n=a['new'];near=a['nearest'];old=a['r6'];checks=dict(points_above_nearest=n['selected_positive_points']>near['selected_positive_points'],states_above_nearest=n['hit_states']>near['hit_states'],points_not_below_r6=n['selected_positive_points']>=old['selected_positive_points'],states_not_below_r6=n['hit_states']>=old['hit_states'],difficulty_states_not_below_nearest=all(groups[d]['utility']['new']['hit_states']>=groups[d]['utility']['nearest']['hit_states'] for d in ('sparse','standard')),unique_states_not_below_nearest=None if not unique['all']['states'] else unique['all']['methods']['new']['hit_states']>=unique['all']['methods']['nearest']['hit_states'])
 complete=engineering_checks and all(groups['all'][label][m]['complete_states']==len(specs) for label in LABELS for m in METHODS)
 distribution={}
 for group,n in denominators.items():
  points=candidates if group=='all' else [r for r in candidates if r['difficulty']==group]
  distribution[group]=dict(expected_candidates=24*n,stored_candidates=len(points),safe_arrival=sum(r['utility_label']==1 and r['old_label']==1 for r in points),strict_route_only=sum(r['utility_label']==1 and r['old_label']!=1 for r in points),negative=sum(r['utility_label']==0 for r in points),unknown=sum(r['utility_label'] is None for r in points)+24*n-len(points))
 return dict(denominators=denominators,label_distribution=distribution,metrics=groups,unique_positive_states=unique,paired={m:paired(rows,m) for m in ('r6','nearest')},engineering_complete=complete,benefit_checks=checks,benefit_gate_pass=complete and all(v is not False for v in checks.values()),benefit_limit='N/A unique subset is not verified; passing only permits discussion of later integration, not automatic deployment or full route benefit',scope='single initial states, same24 support, same geometry, frozen unique teacher labels; sealed set observed after this evaluation')

def self_test():
 support=[dict(candidate_id=f'c{i}',sector=i//2) for i in range(24)];labels=[None]*24;labels[0]=1;labels[1]=0;allowed=[True]*24
 a=state_metrics(labels,allowed,[0],support);b=state_metrics(labels,allowed,[1],support)
 assert a['hit'] and not b['hit'] and a['unknown']==22 and b['selected_negative_points']==1
 assert aggregate([a],64)['overall_hit_rate']==1/64 and aggregate([a],64)['unknown_candidates']==1534
 rows=[dict(state_id='s',map_id='m',difficulty='sparse',label=l,method=m,**(a if m=='new' else b)) for l in LABELS for m in METHODS]
 p=paired(rows,'nearest')['utility'];assert p['state_gain']==1 and p['all_pairs'][0]['gained_positive_candidates']==['c0']
 candidates=[dict(state_id='s',difficulty='sparse',candidate_id=f'c{i}',geometry_allowed=True,utility_label=int(i==0),old_label=0) for i in range(24)]
 specs=[dict(state_id='s',map_id='m',difficulty='sparse')]
 out=summarize(rows,candidates,specs)
 assert out['unique_positive_states']['route_only']['states']==1 and out['unique_positive_states']['arrival']['states']==0
 assert out['label_distribution']['all']['strict_route_only']==1 and out['label_distribution']['all']['negative']==23
 assert not out['engineering_complete'] and not out['benefit_gate_pass']
 return dict(all_pass=True,checks=['unknown_is_not_negative','fixed_missing_denominator','point_and_state_pairs','all_lost_candidates_retained','unique_route_and_arrival_disjoint','incomplete_data_cannot_pass_gate'])
if __name__=='__main__':print(json.dumps(self_test()))
