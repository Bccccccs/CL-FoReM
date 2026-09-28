"""Offline world reference audit: comments do not create asset dependencies."""
import hashlib,json,os
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path('/root/mm_husky_ws')
paths=[Path(p) for p in os.environ['GAZEBO_MODEL_PATH'].split(':')]
report={}
for world in (root/'src/modulation_rl/gazebo_world/worlds').glob('*.world'):
    refs=sorted({u.text.split('/')[2] for u in ET.parse(world).iter('uri') if u.text and u.text.startswith('model://')})
    models={}
    for name in refs:
        found=next((p/name for p in paths if (p/name/'model.config').is_file()),None)
        models[name]=None if found is None else str(found)
    report[world.name]=dict(sha256=hashlib.sha256(world.read_bytes()).hexdigest(),models=models,
                           missing=[n for n,p in models.items() if p is None])
from modulation.envs.simulator_api import get_dyn_obstacle
sdf=get_dyn_obstacle(.3,.3,.35)
model=ET.fromstring(sdf.strip())
assert model.find('.//collision/geometry/box/size').text.strip()=='.3 .3 .35' or [float(v) for v in model.find('.//collision/geometry/box/size').text.split()]==[.3,.3,.35]
report['runtime_dynamic_obstacle']=dict(source='scripts/modulation/envs/simulator_api.py:get_dyn_obstacle',
    sdf_sha256=hashlib.sha256(sdf.encode()).hexdigest(),external_uris=[x.text for x in model.iter('uri')],
    note='generated at runtime; dynamic_world.world obstacle includes are commented out')
print(json.dumps(report,indent=2))
# test4 is a historical unrelated scene; task and bookstore are the P0 required worlds.
assert not report['modulation_tasks.world']['missing']
assert not report['bookstore.world']['missing']
assert not report['dynamic_world.world']['missing']
