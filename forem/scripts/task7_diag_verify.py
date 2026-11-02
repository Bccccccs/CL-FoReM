"""Final integrity/geometry sanity verification for task7.18.1 evidence."""
import json,hashlib,collections
from pathlib import Path
import numpy as np
from task7_diag_mesh import selfcheck,P
assert selfcheck()
z=json.loads((P/'mesh-summary.json').read_text());chain=np.load(P/'chain.npz');assert len(chain['q'])==388 and chain['pairs'].any((1,2)).sum()==229
for d,n in [('chain',388),('sync',44),('async',21)]:
 rows={}
 for f in P.glob('mesh-'+d+'-*.jsonl'):
  for l in f.read_text().splitlines():
   r=json.loads(l);assert r['pose'] not in rows;rows[r['pose']]=r
 assert len(rows)==n and z[d]['n']==n
 for r in rows.values():
  for x in r['pairs']:
   ref=x['reference']
   if ref['method'] in ['original_mesh_AABB_separation','certified_sample_clear']:assert ref['lower']>0 and not ref['hit']
   if ref['hit']:assert ref['distance']==0
for d in ['sync','async']:
 a=np.load(P/d/'playback.npz');seg=json.loads((P/d/'segments.json').read_text())
 # Match recorded execution attempts directly to each completed segment.
 for s in seg:
  if 'reason' not in s:continue
  mask=(a['env_id']==s['env'])&(a['segment']==s['segment']);expected=s['substeps']+int(s['failure']>0);assert mask.sum()==expected,(d,s['env'],s['segment'],mask.sum(),expected)
 for n in ['checkpoint-0500000.actor.pt','checkpoint-0500000.meta.json']:
  original=Path('results/task7/t7.18-20261021/formal-'+d)/n;assert hashlib.sha256(original.read_bytes()).digest()==hashlib.sha256((P/d/n).read_bytes()).digest()
assert z['chain']['pairs']['4,7']['counts']['FP']==229
assert z['chain']['pairs']['2,13']['counts']['FN']==6
m=json.loads((P/'mesh-manifest.json').read_text());assert all(x['boundary_edges']==0 for x in m['meshes'].values());assert all(x.get('max_vertex_capsule_excess_m',0)<1e-8 and x.get('max_vertex_box_excess_m',0)<1e-8 for x in m['meshes'].values())
methods=collections.Counter();positive=collections.Counter();expanded=collections.Counter()
for f in P.glob('mesh-chain-*.jsonl'):
 for line in f.read_text().splitlines():
  r=json.loads(line);pr=any(x['envelope_hit'] for x in r['pairs']);tr=any(x['reference']['hit'] for x in r['pairs']);expanded[('TP' if tr else 'FP') if pr else ('FN' if tr else 'TN')]+=1
  for x in r['pairs']:
   methods[x['reference']['method']]+=1
   if x['reference']['hit']:positive[x['reference']['method']]+=1
v=dict(geometry_sanity_cases=5,chain_rows=388,playback_collision_rows={'sync':44,'async':21},substep_count_consistency=True,copied_actor_and_meta_hash_equal=True,mesh_all_closed_edges=True,enclosure_vertex_audit=True,mesh_method_counts=dict(methods),positive_reference_methods=dict(positive),frame_including_known_allowed_pair=dict(expanded))
(P/'verification.json').write_text(json.dumps(v,indent=2));print(json.dumps(v,indent=2))
