#!/usr/bin/env python3
"""Freeze task12.6 identities before any new labels; standard library only."""
import argparse,collections,hashlib,json,random,re,struct,subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path('/home/ybc/projects/CL-FoReM/forem')
def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n');t.replace(p)
def hashes(doc):
 rows=[[float(x) for x in row] for row in doc['boxes']]
 native=hashlib.sha256(b''.join(struct.pack('<8d',*r) for r in rows)).hexdigest()
 canonical=hashlib.sha256(b''.join(struct.pack('<8d',*r) for r in sorted(rows))).hexdigest()
 return native,canonical

def freeze(run):
 run=Path(run).resolve()
 if (run/'plan.json').exists():raise RuntimeError('plan already frozen; do not rewrite identities')
 run.mkdir(parents=True,exist_ok=True)
 pool=ROOT/'results/task8/t8-pool-20261027/cube-pool-v2/manifest.json'
 entries=json.loads(pool.read_text())['maps'];byid={e['id']:e for e in entries}
 used=collections.defaultdict(list);scanned=[]
 for old in sorted((ROOT/'results/task12').iterdir()):
  if old==run or not old.is_dir():continue
  for p in sorted(old.rglob('*')):
   if 'frozen-source' in p.relative_to(old).parts:continue  # copied pool/config catalogs are not usage
   if not p.is_file() or p.suffix not in ('.json','.jsonl','.csv'):continue
   text=p.read_text(errors='replace');ids=set(re.findall(r'(?:sparse|standard)_(?:train|validation|test)_\d{5}',text))&byid.keys()
   if ids:
    scanned.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),map_ids=sorted(ids)))
    for mid in ids:used[mid].append(str(p.relative_to(ROOT)))
 assert 'sparse_train_00000' in used
 assert set(x['map_id'] for x in json.loads((ROOT/'results/task12/t12-cost32-20261104-r3/plan.json').read_text())['states'])<=used.keys()
 geometries={}
 # Geometry identity is the primitive source boxes, not a PCD hash or metadata.
 for e in entries:
  if e['split']=='train' or e['id'] in used:
   p=pool.parent/e['sidecar_path'];doc=json.loads(p.read_text());native,canonical=hashes(doc)
   geometries[e['id']]=dict(native_boxes_sha256=native,canonical_geometry_sha256=canonical,source_json_sha256=e['source_json_sha256'])
 oldhashes={geometries[mid]['canonical_geometry_sha256'] for mid in used}
 oldsource={geometries[mid]['source_json_sha256'] for mid in used}
 excluded=[];eligible={d:[] for d in ('sparse','standard')}
 for e in entries:
  if e['split']!='train':continue
  mid=e['id'];g=geometries[mid];reasons=[]
  if mid in used:reasons.append('task12_prior_identity')
  if g['canonical_geometry_sha256'] in oldhashes:reasons.append('task12_prior_geometry')
  if g['source_json_sha256'] in oldsource:reasons.append('task12_prior_source_hash')
  if reasons:excluded.append(dict(map_id=mid,difficulty=e['difficulty'],reasons=reasons,prior_evidence=used.get(mid,[]),**g))
  else:eligible[e['difficulty']].append(e)
 rng=random.Random(1206);states=[];selected_hashes=set();duplicate_skips=[]
 for difficulty in ('sparse','standard'):
  candidates=sorted(eligible[difficulty],key=lambda e:e['id']);rng.shuffle(candidates);n=0
  for e in candidates:
   g=geometries[e['id']]
   if g['canonical_geometry_sha256'] in selected_hashes:
    duplicate_skips.append(dict(map_id=e['id'],reason='same_geometry_as_earlier_frozen_selection',**g));continue
   i=len(states);states.append(dict(state_id=f'state-{i:02d}',index=i,map_id=e['id'],difficulty=difficulty,split='train',scene_seed=126000+i,state_rule='first native sync_v5 sampler accepted initial decision boundary, s=0; fixed identity; no label-based replacement',acquisition_timeout_s=300,**g));selected_hashes.add(g['canonical_geometry_sha256']);n+=1
   if n==16:break
  assert n==16
 exclusion=dict(at=now(),scope='all map identities in prior task12 run JSON/JSONL/CSV artifacts, excluding frozen-source copied catalogs; conservatively includes mentions; r1 and r3 explicitly asserted',old_used_map_ids=sorted(used),prior_artifacts=scanned,excluded_train_maps=excluded,within_selection_geometry_skips=duplicate_skips,geometry_hash_definition='SHA256(sorted float64 little-endian primitive boxes rows); native box-order hash retained too',eligible_counts={k:len(v) for k,v in eligible.items()},formal_test_pool_used=False)
 write(run/'exclusions.json',exclusion)
 old=json.loads((ROOT/'results/task12/t12-cost32-20261104-r3/plan.json').read_text())
 model=ROOT/'results/task12/t12-utility-20261105-r6/model-weights.pt';assert sha(model)=='32ebfd305dd297eca4b0831b0b960ba8a051868020897bba3c0a8e4e06914ce5'
 plan=dict(run_id=run.name,frozen_at=now(),planned_states=32,difficulty_denominators={'sparse':16,'standard':16},states=states,pool=str(pool.relative_to(ROOT)),pool_manifest_sha256=sha(pool),candidate_template=old['candidate_template'],model_source=str(model.relative_to(ROOT)),model_sha256=sha(model),label_version='task12-utility-v1',map_seed=1206,scene_seed_base=126000,updates=0,max_moving_candidates=768,batch_timeout_s=1800,engineering_estimate_s=[7200,10800],exclusions_sha256=sha(run/'exclusions.json'),selection_rule='map_id sort then single Random(1206), sparse shuffle then standard shuffle,16 each; deduplicate geometry without labels',teacher_source='r1 frozen-source, accepted SRC-T12-007/009',inplace_and_rules='preserve slots/identities; no new teacher labels; moving metrics only',cases_rule='top3 avoidable miss score(negative)-score(best positive) descending then state_id/sector; first improvement/degradation state per difficulty; save logits too',score_semantics='ranking scores only, weighted BCE outputs not calibrated probabilities')
 write(run/'plan.json',plan);write(run/'manifest.json',dict(frozen_at=now(),states=states,plan_sha256=sha(run/'plan.json'),exclusions_sha256=sha(run/'exclusions.json'),new_teacher_calls_before_freeze=0,updates=0))
 print(json.dumps(dict(run=str(run),excluded=len(excluded),old_used_maps=len(used),eligible=exclusion['eligible_counts'],selected=[s['map_id'] for s in states]),ensure_ascii=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);freeze(ap.parse_args().run)
