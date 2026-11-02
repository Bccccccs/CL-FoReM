"""Attach already complete original-mesh audits to the final sphere zero table."""
import json
from pathlib import Path
P=Path('results/task7/t7.18.2-r2-20261021');target=P/'allowed-audit-final-v3.json';data=json.loads(target.read_text());cache={}
for path in P.glob('allowed-audit*.json'):
 for row in json.loads(path.read_text()).get('rows',[]):
  if row.get('complete') and row.get('samples')==10000:cache[tuple(row['pair'])]=(path,row)
for row in data['rows']:
 key=tuple(row['pair'])
 if key in cache:
  path,ref=cache[key];old=dict(row);row.update(ref)
  for k in ['reason','zero_sphere_contact','zero_reference']:row[k]=old[k]
  row['raw_mesh_audit_source']=str(path)
target.write_text(json.dumps(data,indent=2)+'\n');print('pairs',len(data['rows']),'complete',sum(r.get('complete',False) for r in data['rows']),flush=True)
assert all(r.get('complete') for r in data['rows'])
