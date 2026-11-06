"""Generate full pair confusion tables and mesh-referenced acceptance summary."""
import json,csv
from pathlib import Path
P=Path('results/task7/t7.18.2-r2-20261021');old=json.loads(Path('config/task7/robot_geometry_v1.json').read_text());names=old['names'];summ={}
for d in ['chain','sync','async']:
 f=P/f'reference-{d}.jsonl'
 if not f.exists():continue
 rows=[json.loads(l) for l in f.read_text().splitlines()];pairs={};old_pairs={};tot=[0,0,0,0];old_tot=[0,0,0,0]
 for r in rows:
  h=t=oh=False
  for x in r['pairs']:
   h|=x['new_hit'];t|=x['reference']['hit'];v=pairs.setdefault(x['pair'],[0,0,0,0]);v[0 if x['new_hit'] and x['reference']['hit'] else 1 if x['new_hit'] else 3 if x['reference']['hit'] else 2]+=1
   oh|=x['old_hit'];v=old_pairs.setdefault(x['pair'],[0,0,0,0]);v[0 if x['old_hit'] and x['reference']['hit'] else 1 if x['old_hit'] else 3 if x['reference']['hit'] else 2]+=1
  tot[0 if h and t else 1 if h else 3 if t else 2]+=1
  old_tot[0 if oh and t else 1 if oh else 3 if t else 2]+=1
 with (P/f'pair-confusion-{d}.csv').open('w') as out:
  w=csv.writer(out);w.writerow(['pair','link_a','link_b','TP','FP','TN','FN','FPR','FNR','old_TP','old_FP','old_TN','old_FN'])
  for k,v in sorted(pairs.items(),key=lambda kv:tuple(map(int,kv[0].split(',')))):
   i,j=map(int,k.split(','));w.writerow([k,names[i],names[j],*v,v[1]/(v[1]+v[2]) if v[1]+v[2] else None,v[3]/(v[0]+v[3]) if v[0]+v[3] else None,*old_pairs[k]])
 summ[d]=dict(complete=len(rows)=={'chain':388,'sync':1582,'async':19308}[d],N=len(rows),TP=tot[0],FP=tot[1],TN=tot[2],FN=tot[3],FPR=tot[1]/(tot[1]+tot[2]) if tot[1]+tot[2] else None,pairs=pairs,old_pairs=old_pairs,old_pose_confusion=old_tot)
 print(d,summ[d]['N'],tot,flush=True)
(P/'summary.json').write_text(json.dumps(summ,indent=2)+'\n')
