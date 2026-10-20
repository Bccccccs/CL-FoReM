#!/usr/bin/env python3
"""Host-only task7.6 parameterized arithmetic from recorded microbenchmark JSON."""
import csv,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/task7';OUT=BASE/'t7.6-bench-20261020-r9';OUT.mkdir(parents=True,exist_ok=True)
def load(k,n):return json.loads((BASE/f't7.6-bench-20261020-r{k}'/n).read_text())
supp=load(7,'supplement.json');over={(r['device'],r['batch']):r['wall_stats_s']['p50'] for r in supp['overhead']};rows=[]
for run in [2,3,4]:
 for r in load(run,'timing.json'):
  if r['kind']!='ik' or r['method']!='analytic' or r['batch'] not in [13,104,416,1664]:continue
  K=13;N=r['batch']//K
  for L in [.5,1.,2.,2.6,8.]:
   for theta in [0.,math.pi/2,math.pi,2*math.pi]:
    for h in [.05,.025]:
     # Rotate-translate path, each chassis point arc bounded by r*angle.
     C=math.ceil(L/h)+math.ceil(.60*abs(theta)/h)
     t=r['wall_stats_s']['p50'];other=over[(r['device'],r['batch'])]
     rows.append({'run':run,'device':r['device'],'threads':r['threads'],'K':K,'N':N,'base_translation_m':L,'sum_abs_rotation_rad':theta,'chassis_point_spacing_m':h,'C_base_only':C,'ik_batch_checkpoint_p50_s':t,'arc_transform_batch_checkpoint_p50_s':other,'estimated_ik_plus_arc_transform_s':C*(t+other),'unknown_collision_and_other_s':'C*t_other(B) + candidate_generation + render + replans','training_budget_B1_B3':'undetermined','hours_per_B_decisions_factor':C*(t+other)/3600})
with (OUT/'cost_scan.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(OUT/'cost_scan.json').write_text(json.dumps({'engineering_scan':{'K':13,'N':[1,8,32,128],'L_m':[.5,1,2,2.6,8],'theta_rad':[0,math.pi/2,math.pi,2*math.pi],'h_m':[.05,.025]},'formula':'C_base=ceil(L/h)+ceil(0.60*abs(theta)/h); cost=C_base*(batch_IK_p50+arc_transform_p50)+unknown. Arm displacement is not bounded by this chassis-only C.','row_count':len(rows),'rows':rows},indent=2)+'\n')
print('cost rows',len(rows))
for run in [3,4]:
 for N in [1,8,32,128]:
  a=next(r for r in rows if r['run']==run and r['N']==N and r['base_translation_m']==1 and r['sum_abs_rotation_rad']==math.pi and r['chassis_point_spacing_m']==.05)
  print('example',run,'K13 N',N,'C',a['C_base_only'],'s',round(a['estimated_ik_plus_arc_transform_s'],6))
