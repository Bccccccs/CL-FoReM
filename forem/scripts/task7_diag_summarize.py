"""Summarize task7.18.1 raw evidence, no source mutation."""
import json,collections,csv
from pathlib import Path
import numpy as np
from task7_diag_analyze import stat,P
names=json.loads((P/'sync/playback.json').read_text())['names']
result={};rows=[]
for dataset in ['chain','sync','async']:
 files=list(P.glob('mesh-'+dataset+'-*.jsonl'));poses={}
 for f in sorted(files):
  for line in f.read_text().splitlines():
   r=json.loads(line);poses[r['pose']]=r
 pairs={};frame=collections.Counter();repair={m:collections.Counter() for m in ['no_arm_margin','split_gripper','slabs_4cm','slabs_arm_only','guarded_slabs_arm_only']}
 for idx,r in poses.items():
  checked=[x for x in r['pairs'] if not x.get('allowed',False)]
  for x in checked:
   j=int(x['pair'].split(',')[1]);x['estimates']['slabs_arm_only']=x['estimates']['slabs_4cm'] if j<8 else x['envelope_hit'];x['estimates']['guarded_slabs_arm_only']=(x['estimates']['slabs_4cm'] and x['estimates']['no_arm_margin']) if j<8 else x['envelope_hit']
  truth=any(x['reference']['hit'] for x in checked);pred=any(x['envelope_hit'] for x in checked)
  frame[('TP' if truth else 'FP') if pred else ('FN' if truth else 'TN')]+=1
  for m in repair:
   pr=any(x['estimates'][m] for x in checked);repair[m][('TP' if truth else 'FP') if pr else ('FN' if truth else 'TN')]+=1
  for x in r['pairs']:
   key=x['pair'];c=pairs.setdefault(key,dict(counts=collections.Counter(),clearances=[],allowed=x.get('allowed',False),repair={m:collections.Counter() for m in repair}));tr=x['reference']['hit'];pr=x['envelope_hit'];c['counts'][('TP' if tr else 'FP') if pr else ('FN' if tr else 'TN')]+=1
   if x['reference']['distance'] is not None:c['clearances'].append(x['reference']['distance'])
   elif x['reference'].get('lower') is not None:c['clearances'].append(x['reference']['lower'])
   for m,pr in x.get('estimates',{}).items():c['repair'][m][('TP' if tr else 'FP') if pr else ('FN' if tr else 'TN')]+=1
 summary={}
 for key,c in pairs.items():
  cn=c['counts'];i,j=map(int,key.split(','));summary[key]={'names':[names[i],names[j]],'counts':dict(cn),'allowed':c['allowed'],'clearance_lower_or_exact_m':stat(c['clearances']),'false_alarm_fraction':cn['FP']/(cn['TP']+cn['FP']) if cn['TP']+cn['FP'] else None,'FPR':cn['FP']/(cn['FP']+cn['TN']) if cn['FP']+cn['TN'] else None,'FNR':cn['FN']/(cn['FN']+cn['TP']) if cn['FN']+cn['TP'] else None,'repair':{m:dict(c) for m,c in c['repair'].items()}}
  rows.append(dict(dataset=dataset,pair=key,link_a=names[i],link_b=names[j],allowed=c['allowed'],N=sum(cn.values()),TP=cn['TP'],FP=cn['FP'],TN=cn['TN'],FN=cn['FN']))
 result[dataset]=dict(n=len(poses),frame=dict(frame),repair={m:dict(c) for m,c in repair.items()},pairs=summary)
(P/'mesh-summary.json').write_text(json.dumps(result,indent=2))
with (P/'pair-confusion.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
actions={}
for variant in ['sync','async']:
 a=np.load(P/variant/'playback.npz');s=json.loads((P/variant/'segments.json').read_text());ss=[r for r in s if r.get('reason')==4];act=np.array([x for r in ss for x in r['actions']]);z={'segments':len(ss),'actions':len(act)}
 if len(act):
  z.update(abs_v_lt_001_fraction=float((abs(act[:,1])<.01).mean()),abs_w_lt_005_fraction=float((abs(act[:,2])<.05).mean()),base_both_near_zero_fraction=float(((abs(act[:,1])<.01)&(abs(act[:,2])<.05)).mean()),u_lt_001_fraction=float((act[:,0]<.01).mean()))
 if ss and all('end_cap' in r for r in ss):
  z.update(cap_reached=sum(abs(r['end_s']-r['end_cap'])<1e-6 for r in ss),end_xy_error_m=stat([np.linalg.norm(np.array(r['end_base'][:2])-r['candidate_pose'][:2]) for r in ss]),end_heading_error_rad=stat([abs(np.arctan2(np.sin(r['end_base'][2]-r['candidate_pose'][2]),np.cos(r['end_base'][2]-r['candidate_pose'][2]))) for r in ss]))
 actions[variant]=z
 # Each actual self-collision attempted posture remains directly reproducible.
 ids=np.where(a['pairs'].any(axis=(1,2)))[0]
 examples=[]
 for i in ids:
  examples.append(dict(index=int(i),env=int(a['env_id'][i]),segment=int(a['segment'][i]),substep=int(a['substep'][i]),time_s=.05*int(a['substep'][i]),q_rad=a['q'][i].tolist(),previous_q_rad=a['prev'][i].tolist(),target_world=a['target'][i].tolist(),trial_base=a['base'][i].tolist(),exact=bool(a['exact'][i]),status=int(a['status'][i]),branch=int(a['branch'][i]),position_residual_m=float(a['position'][i]),rotation_residual_cbl=float(a['cbl'][i]),pairs=np.argwhere(a['pairs'][i]).tolist()))
 (P/variant/'collision-events.json').write_text(json.dumps(examples,indent=2))
(P/'timeout-summary.json').write_text(json.dumps(actions,indent=2))
for dataset,z in result.items():
 print(dataset,z['n'],'frames',z['frame'],'repair',z['repair'])
 for key,c in z['pairs'].items():
  if c['counts'].get('FP',0) or c['counts'].get('TP',0) or c['counts'].get('FN',0):print(key,c)
print('timeout',json.dumps(actions))
