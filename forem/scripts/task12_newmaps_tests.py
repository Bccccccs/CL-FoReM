#!/usr/bin/env python3
"""Targeted new-entry checks; accepted teacher/recovery evidence reused."""
import argparse,json,random,tempfile,shutil,struct,hashlib,ast
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--workspace',default='/workspace');args=ap.parse_args();run=Path(args.run);root=Path(args.workspace)
 from task12_newmaps_stats import self_test
 checks={'stats_fixture':self_test()['all_pass']}
 plan=json.loads((run/'plan.json').read_text());ex=json.loads((run/'exclusions.json').read_text());manifest=json.loads((run/'manifest.json').read_text());pool=root/plan['pool'];entries=json.loads(pool.read_text())['maps'];byid={e['id']:e for e in entries}
 old_ids=set(ex['old_used_map_ids']);old_geometry={x['canonical_geometry_sha256'] for x in ex['excluded_train_maps']}
 selected=plan['states'];assert len(selected)==32 and len({s['map_id'] for s in selected})==32 and len({s['canonical_geometry_sha256'] for s in selected})==32
 assert all(s['split']=='train' and s['map_id'] not in old_ids and s['canonical_geometry_sha256'] not in old_geometry and s['scene_seed']==126000+i for i,s in enumerate(selected))
 checks['identity_geometry_seed_exclusion']=True
 assert manifest['new_teacher_calls_before_freeze']==0 and manifest['updates']==plan['updates']==0
 assert manifest['plan_sha256']==hashlib.sha256((run/'plan.json').read_bytes()).hexdigest()
 assert plan['exclusions_sha256']==hashlib.sha256((run/'exclusions.json').read_bytes()).hexdigest()
 checks['manifest_prelabels_binding']=True
 rng=random.Random(1206);rep=[]
 for difficulty in ('sparse','standard'):
  e=sorted([x for x in entries if x['split']=='train' and x['difficulty']==difficulty and x['id'] not in {r['map_id'] for r in ex['excluded_train_maps']}],key=lambda x:x['id']);rng.shuffle(e);rep.extend(x['id'] for x in e[:16])
 assert rep==[s['map_id'] for s in selected]  # current selection had no geometry collision
 checks['independent_map_shuffle_reproduction']=True
 assert len([x for x in plan['candidate_template'] if x['kind']=='grid'])==24 and plan['max_moving_candidates']==768
 model=root/plan['model_source'];assert hashlib.sha256(model.read_bytes()).hexdigest()==plan['model_sha256']=='32ebfd305dd297eca4b0831b0b960ba8a051868020897bba3c0a8e4e06914ce5'
 checks['model_support_fixed']=True
 from task12_newmaps import Worker
 from task10.boundary_state import decode
 import torch
 from types import SimpleNamespace
 torch.set_num_threads(2)
 # Exercise actual new utility extraction against an accepted terminal batch,
 # without policy calls or a new rollout. Expected r6 labels remain read-only.
 base=root/'results/task12/t12-cost32-20261104-r3';labels=json.loads((root/'results/task12/t12-utility-20261105-r6/labels-v1.json').read_text())['items']
 with tempfile.TemporaryDirectory(prefix='t12-newmaps-entry-') as temp:
  d=Path(temp)/'state-00';d.mkdir();(d/'grid-0').mkdir();(d/'grid-0'/'data.pt').symlink_to(base/'states/state-00/grid-0/data.pt');shutil.copy(base/'states/state-00/prepared.json',d/'prepared.json')
  worker=Worker.__new__(Worker);worker.plan=plan;worker.add=lambda *a:None
  from task12_cost32 import atomic_json
  worker.write=lambda d,p,v:atomic_json(p,v)
  src=decode(torch.load(base/'states/state-00/source.pt',map_location='cpu',weights_only=False)['core'],device='cpu');rows=worker.utility_records(d,0,SimpleNamespace(failures=src['failures']))
  expected={r['candidate_id']:r for r in labels if r['state_id']=='state-00'}
  assert len(rows)==12
  for row in rows:
   ref=expected[row['candidate_id']]
   assert row['utility_label']==ref['utility_label'] and row['old_label']==ref['old_label'] and row['strict_verified']==ref['strict_verified']
  assert worker.utility_records(d,0,None)==rows  # completed extraction skip, no source read
 checks['actual_utility_extractor_matches_accepted_r6_12_records']=True
 checks['completed_label_skip']=True
 # No added teacher paths for rules/inplace; accepted predict_candidates makes
 # independent clones per row, recovery remains the immutable r3 method.
 assert Worker.label_batch.__module__=='task12_cost32'
 tree=ast.parse((run/'code/task12_newmaps.py').read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='label_batch'];assert len(calls)==1
 assert not any(isinstance(n,ast.Attribute) and n.attr in ('backward','step') for n in ast.walk(tree))
 checks['accepted_rollout_resume_only_two_grid_groups_no_training']=True
 result=dict(all_pass=all(checks.values()),checks=checks,teacher_calls=0,updates=0,scope='new map freeze, actual utility extraction and completed skip; stats fixtures; accepted teacher/coords/recovery reused SRC-T12-007/009/018/019')
 (run/'targeted-tests.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
