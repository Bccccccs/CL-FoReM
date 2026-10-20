#!/usr/bin/env python3
"""Verify task6.4 upstream logs/offline metrics and count printed contact objects."""
import argparse,ast,collections,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--label',choices=['A','B'],required=True);p.add_argument('--episodes',type=int,required=True);a=p.parse_args()
out=ROOT/'results/task6'/a.run;status=json.loads((out/'status.json').read_text());text=(ROOT/'logs/task6'/a.run/'eval.log').read_text(errors='replace')
pattern=re.compile(r'Eval ep (\d+): ([\d.]+) min, ([\d.]+) ros-min, (\d+) steps\. (\d+)/(\d+) success,.*?Ik failures: (\d+), base coll: (\d+), steps_w_jump: (\d+)')
episodes=[];contacts=[];prev_success=0;entered_task=False;before_task=[];all_objects=collections.Counter()
for line_no,line in enumerate(text.splitlines(),1):
 if 'Evaluating on task ' in line:entered_task=True
 if 'Collision:' in line:
  try:pair=ast.literal_eval(line.split('Collision:',1)[1].strip());assert isinstance(pair,tuple) and len(pair)==2
  except (SyntaxError,ValueError,AssertionError):raise ValueError('Unparsed collision line '+str(line_no))
  record={'line':line_no,'objects':list(pair)}
  if entered_task:contacts.append(record)
  else:before_task.append(record)
 m=pattern.search(line)
 if m:
  i,wall,sim,steps,success,n,ik,coll,jumps=m.groups();assert int(i)==len(episodes) and int(n)==len(episodes)+1
  objs=collections.Counter()
  for item in contacts:
   for obj in item['objects']:
    if not obj.startswith(('pr2::','husky_ur5::')):objs[obj]+=1;all_objects[obj]+=1
  episodes.append({'index':int(i),'seed':status['seed']+int(i),'steps':int(steps),'success':int(success)>prev_success,'wall_s_from_rounded_log':float(wall)*60,'sim_s_from_rounded_log':float(sim)*60,'ik_failures':int(ik),'base_collisions':int(coll),'steps_w_jump':int(jumps),'completion_log_line':line_no,'printed_collision_count':len(contacts),'collision_objects':dict(objs),'collision_log_entries':contacts})
  prev_success=int(success);contacts=[]
assert len(episodes)==a.episodes,(a.run,len(episodes),a.episodes)
raw=json.loads((out/'offline_raw_export.json').read_text());metrics=[h for r in raw for h in r['history'] if any(k.endswith('/success') for k in h)];assert len(metrics)==1
metric=metrics[0];prefix=next(k[:-8] for k in metric if k.endswith('/success'));get=lambda k:metric[prefix+'/'+k]
assert abs(get('success')-sum(e['success'] for e in episodes)/a.episodes)<1e-12
assert abs(get('epoch_len')-sum(e['steps'] for e in episodes)/a.episodes)<1e-10
assert abs(get('ik_fails')-sum(e['ik_failures'] for e in episodes)/a.episodes)<1e-12
assert abs(get('base_collisions')-sum(e['base_collisions']>0 for e in episodes)/a.episodes)<1e-12
assert status['rc']==0 or (a.label=='A' and status['rc']==134)
assert json.loads((out/'cleanup.json').read_text())['after']==[]
r={'run_id':a.run,'label':a.label,'episodes':episodes,'success_count':sum(e['success'] for e in episodes),'denominator':a.episodes,'metrics':{k:get(k) for k in ['success','goal_reached','base_collisions','ik_fails','selfcollisions','epoch_len','success_nojumps']},'raw_prefix':prefix,'raw_exit_code':status['rc'],'T64_D3_deviation':status['rc']==134,'valid':True,'collisions_before_task':before_task,'trailing_collision_entries':contacts,'all_collision_objects':dict(all_objects),'collision_assignment_note':'Collision lines in log interval before each Eval ep completion, including its reset/rollout; printed events differ from upstream base collision counter. Trailing/before-task retained separately; not an independent detector.','start':status['start'],'end':status['end'],'runner_wall_s':status['end']-status['start']}
(out/'verified_eval.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:r[k] for k in ['run_id','valid','success_count','denominator','metrics','raw_exit_code','T64_D3_deviation']}))
