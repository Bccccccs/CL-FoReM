"""Disambiguate historical and candidate Always metadata without changing geometry."""
import json
from pathlib import Path
P=Path('results/task7/t7.18.2-r1-20261021');p=P/'robot_geometry_v2.json';d=json.loads(p.read_text());caps=d['capsules'];body=d['body'];selfcaps=d['self_capsules'];allowed=d['self_allowed']
d['v1_always']=d.pop('always',d.get('v1_always'));c=json.loads((P/'screen-counts.json').read_text());d['arm_body_always']=[[v==10000 for v in row] for row in c['arm_body_contacts']]
assert d['capsules']==caps and d['body']==body and d['self_capsules']==selfcaps and d['self_allowed']==allowed
p.write_text(json.dumps(d,indent=2)+'\n');print('Historical Always relabelled v1_always; candidate self_always and arm_body_always are distinct.')
