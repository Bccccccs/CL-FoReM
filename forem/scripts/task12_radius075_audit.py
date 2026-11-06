"""CPU-only validation of new teacher terminal records; no inference or stepping."""
from pathlib import Path
import json,time,torch
from task10.boundary_state import decode
p=Path('/run');base=Path('/baseline');plan=json.loads((p/'plan.json').read_text());start=time.monotonic();rows=[]
for spec in plan['states']:
 d=p/'states'/spec['state_id'];data=torch.load(d/'probe075/data.pt',map_location='cpu',weights_only=False);resume=torch.load(d/'probe075/resume.pt',map_location='cpu',weights_only=False);source=torch.load(base/'states'/spec['state_id']/'source.pt',map_location='cpu',weights_only=False);terminal=decode(data['core'],device='cpu');initial=decode(source['core'],device='cpu');records=json.loads((d/'probe075/result.json').read_text())['records'];assert records==data['records'];assert resume['source_hash']==spec['source_sha256']
 assert len(records)==12 and bool(terminal['done'].all())
 for i,r in enumerate(records):
  assert r['compact_row']==i and r['sector']==i and data['mapping'][i]['candidate_id']==r['candidate_id'];assert bool(terminal['arrived'][i])==r['arrived'];assert int(terminal['failures'][i])-int(initial['failures'][0])==r['failed'];assert r['label']==int(r['arrived'] and r['failed']==0)
 rows.append(dict(state_id=spec['state_id'],records=12,positive=sum(r['label'] for r in records),all_done=True,source_bound=True))
r=dict(all_pass=True,states=32,teacher_records=384,positive=sum(x['positive'] for x in rows),rows=rows,wall_s=time.monotonic()-start,teacher_calls=0,optimizer_updates=0);(p/'native-record-audit.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'}))
