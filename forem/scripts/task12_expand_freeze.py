#!/usr/bin/env python3
"""Freeze task12.7 before teacher labels and audit only existing label artifacts."""
import argparse,collections,json,random
from pathlib import Path
from task12_newmaps_freeze import ROOT,now,sha,write,hashes

def audit(run):
 r6=ROOT/'results/task12/t12-utility-20261105-r6';r7=ROOT/'results/task12/t12-newmaps-20261105-r7'
 old=json.loads((r6/'labels-v1.json').read_text())['items']; infos=json.loads((r6/'geometry-and-identities.json').read_text()); rows=[]
 for info in infos:
  lab=[r for r in old if r['state_id']==info['state_id']];allow={r['candidate_id']:a for r,a in zip(info['support'],info['allowed'])};rows.append(describe('r6',info,lab,allow))
 for s in json.loads((r7/'plan.json').read_text())['states']:
  d=r7/'states'/s['state_id'];lab=json.loads((d/'labels.json').read_text())['grid'];sel=json.loads((d/'selection.json').read_text());allow={r['candidate_id']:r['geometry_allowed'] for r in sel['scored_support']};row=describe('r7',s,lab,allow)
  if s['state_id'] in ('state-11','state-23','state-24'):
   positive=[r for r in lab if allow[r['candidate_id']] and r['utility_label']==1];assert len(positive)==1 and positive[0]['old_label']==1
   assert positive[0]['candidate_id'] not in {r['candidate_id'] for r in sel['selected']};row['prior_unique_arrival_miss']=positive[0]['candidate_id']
  rows.append(row)
 aggregate={}
 for source in ('r6','r7'):
  for difficulty in ('all','sparse','standard'):
   rr=[r for r in rows if r['source']==source and (difficulty=='all' or r['difficulty']==difficulty)]
   aggregate[source+'/'+difficulty]={k:sum(r[k] for r in rr) for k in ('states','arrival','route_only','negative','unknown','positive_sectors','unique_positive_states')}
 write(run/'existing-label-audit.json',dict(at=now(),teacher_calls=0,source_evidence='SRC-T12-018/019/023; saved verified labels and geometry reused, no FK rerun',aggregate=aggregate,rows=rows));return aggregate

def describe(source,info,lab,allow):
 classes=collections.Counter('unknown' if r['utility_label'] is None else 'arrival' if r['old_label']==1 else 'route_only' if r['utility_label']==1 else 'negative' for r in lab)
 assert len(lab)==24
 pos=[r for r in lab if allow[r['candidate_id']] and r['utility_label']==1]
 return dict(source=source,state_id=info['state_id'],map_id=info['map_id'],difficulty=info['difficulty'],states=1,**{k:classes[k] for k in ('arrival','route_only','negative','unknown')},positive_sectors=len({r['sector'] for r in pos}),allowed_positive_points=len(pos),unique_positive_states=int(len(pos)==1),unique_type=('arrival' if pos[0]['old_label']==1 else 'route_only') if len(pos)==1 else None)

def freeze(run):
 # Reuse accepted r7 exclusion scanner, changing only the frozen sampling contract.
 import task12_newmaps_freeze as accepted
 import inspect
 src=inspect.getsource(accepted.freeze)
 src=src.replace('def freeze(run):','def expanded(run):').replace('random.Random(1206)','random.Random(1207)').replace('if n==16:break','if n==128:break').replace('assert n==16','assert n==128').replace("f'state-{i:02d}'","f'state-{i:03d}'").replace('scene_seed=126000+i','scene_seed=127000+i').replace('planned_states=32','planned_states=256').replace("{'sparse':16,'standard':16}","{'sparse':128,'standard':128}").replace('map_seed=1206','map_seed=1207').replace('scene_seed_base=126000','scene_seed_base=127000').replace('max_moving_candidates=768','max_moving_candidates=6144').replace('engineering_estimate_s=[7200,10800]','engineering_estimate_s=[57600,72000]')
 src=src.replace("i=len(states);states.append", "i=len(states);states.append").replace("split='train',scene_seed", "split='train',subset=('train' if n<80 else 'development' if n<96 else 'sealed'),scene_seed")
 # Insert protocol fields before the first plan write, never edit plan after labels.
 insert="""oldstates=json.loads((ROOT/'results/task12/t12-utility-20261105-r6/split.json').read_text())
 plan.update(old_train_states=[s for s in oldstates if s['subset']=='train'],checkpoint_selection=['utility_state_hits_desc','utility_positive_points_desc','arrival_state_hits_desc','development_masked_BCE_asc','epoch_asc'],training=dict(seed=1204,epochs=200,batch_states=8,lr=.001,optimizer='Adam',loss='masked BCE',expected_updates=4600,evaluate_every_epochs=10,initialization='from_scratch'),subset_denominators=dict(train=160,development=32,sealed=64),engineering_estimate_s=[57600,72000],selection_rule='sort eligible map_id; single Random(1207) shuffles sparse then standard; take128/difficulty; first80 train next16 development last32 sealed; scene_seed127000+i',actual_agent_model='unknown',actual_reasoning='unknown',scope='SRC-T12-024; fixed utility-v1/two rings/B3/decoder; no new mechanism')
 """
 src=src.replace("write(run/'plan.json',plan);",insert+"write(run/'plan.json',plan);")
 env=dict(vars(accepted));exec(src,env);env['expanded'](run)
 plan=json.loads((run/'plan.json').read_text());states=plan['states'];assert len(states)==256
 assert collections.Counter(s['subset'] for s in states)==dict(train=160,development=32,sealed=64)
 for subset in ('train','development','sealed'):
  directory=run/'partitions'/subset;directory.mkdir(parents=True,exist_ok=True);write(directory/'manifest.json',dict(subset=subset,states=[s for s in states if s['subset']==subset],plan_sha256=sha(run/'plan.json')))
 write(run/'split.json',dict(new_states=states,old_train_states=plan['old_train_states']))
 result=audit(run);print(json.dumps(result))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);freeze(ap.parse_args().run.resolve())
