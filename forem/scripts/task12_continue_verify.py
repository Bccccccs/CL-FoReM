"""Read saved B/C artifacts once; no teacher/env/optimizer calls."""
import json,time
from pathlib import Path
import numpy as np
p=Path('/run');start=time.monotonic();checks={}
read=lambda f:json.loads((p/f).read_text())
ids=read('candidate-identities.json');rules=[x for x in ids if x['kind']=='rule_reference'];invalid=[x for x in rules if x['status']=='invalid']
checks['invalid_rules_keep_null']=[x['sector'] for x in invalid]==[0,1,7,8] and all(x['pose'] is None and x['label'] is None for x in invalid)
checks['grid_replays_all_24_equal']=all(len(read(f'grid-comparison-{g}.json'))==12 and all(x['equal'] for x in read(f'grid-comparison-{g}.json')) for g in range(2))
checks['rules_replays_all_8_equal']=len(read('rules-comparison.json'))==8 and all(x['equal'] for x in read('rules-comparison.json'))
for name in ('rules-first','rules-replay'):
 rows=read(name+'-records.json');checks[name+'_mapping']=[x['sector'] for x in rows]==[2,3,4,5,6,9,10,11] and all(x['candidate_id']==f"candidate-{x['sector']*3+2:02d}" and x['compact_row']==i for i,x in enumerate(rows))
z=np.load(p/'C-numeric.npz');mask=z['mask'];target=z['target'];grad=z['logit_gradients']
checks['exact_supervision_24_1_23']=int(mask.sum())==24 and int(target[mask].sum())==1 and int((~mask).sum())==16360
checks['ten_logit_gradients']=len(grad)==10 and all(np.count_nonzero(g[mask])==24 and np.count_nonzero(g[~mask])==0 and np.isfinite(g).all() for g in grad)
checks['probability_array']=z['prediction'].shape==(1,1,128,128) and np.isfinite(z['prediction']).all() and np.all((z['prediction']>=0)&(z['prediction']<=1))
d=read('C-decoded.json');rows=d['scored_support'];selected=d['selected'];best=[]
for sector in range(12):
 choices=[x for x in rows if x['sector']==sector and x['geometry_allowed']];choices.sort(key=lambda x:(-x['score'],x['row'],x['col']))
 if choices:best.append(choices[0]['candidate_id'])
checks['sector_peaks_and_ties']=[x['candidate_id'] for x in selected]==best
checks['scores_match_heatmap']=all(x['score']==float(z['prediction'][0,0,x['row'],x['col']]) for x in rows)
checks['grid_to_robot_roundtrip']=all(int(np.floor(x['pose'][0]/.05+64))==x['col'] and int(np.floor(x['pose'][1]/.05+64))==x['row'] for x in rows)
slots=z['valid_slots'];pose=z['pose'];checks['inplace_and_padding']=bool(slots[0,12]) and np.all(pose[0,12]==0) and np.all(pose[~slots]==0) and int(slots.sum())==len(selected)+1
world=z['world'][0];base=world[12];delta=world[:,:2]-base[:2];a=base[2]
back_xy=np.stack([np.cos(a)*delta[:,0]+np.sin(a)*delta[:,1],-np.sin(a)*delta[:,0]+np.cos(a)*delta[:,1]],-1)
back_a=(world[:,2]-a+np.pi)%(2*np.pi)-np.pi
xy_error=float(np.max(np.abs(back_xy[slots[0]]-pose[0,slots[0],:2])))
yaw_error=float(np.max(np.abs((back_a[slots[0]]-pose[0,slots[0],2]+np.pi)%(2*np.pi)-np.pi)))
checks['world_robot_roundtrip']=xy_error<1e-5 and yaw_error<1e-5
checks={k:bool(v) for k,v in checks.items()}
record=dict(all_pass=all(checks.values()),checks=checks,xy_max_error_m=xy_error,yaw_max_error_rad=yaw_error,wall_s=time.monotonic()-start)
(p/'saved-artifacts-verification.json').write_text(json.dumps(record,indent=2));print(json.dumps(record));assert record['all_pass']
