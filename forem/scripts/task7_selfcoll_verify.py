"""Final provenance, device, complete-sample and deliberately failed-gate checks."""
import json,os,hashlib,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
import torch
P=Path('results/task7/t7.18.2-r1-20261021')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
old=json.loads(Path('config/task7/robot_geometry_v1.json').read_text());new=json.loads((P/'robot_geometry_v2.json').read_text());summary=json.loads((P/'summary.json').read_text());accept=json.loads((P/'acceptance.json').read_text())
assert not accept['passed'] and accept['checks']['chain_true_13_detected'] and accept['checks']['upper_topplate_true_6_detected']
assert old['capsules']==new['capsules'] and old['body']==new['body']
assert sha('config/task7/robot_geometry.json')==sha('config/task7/robot_geometry_v1.json')
assert sha('config/task7/model.urdf')==old['urdf_sha256']
for p,spec in old['mesh_sources'].items():assert sha(p)==spec['sha256'],p
for d,n in [('chain',388),('sync',1582),('async',19308)]:
 rows=[json.loads(l) for l in (P/f'reference-{d}.jsonl').read_text().splitlines()]
 assert [r['pose'] for r in rows]==list(range(n));assert summary[d]['complete']
tests={}
for name in ['task7_sim','task7_lower','task7_upper']:
 root=ET.parse(P/f'pytest-{name}.xml').getroot();s=list(root)[0] if root.tag=='testsuites' else root;tests[name]=dict(s.attrib)
 assert int(s.attrib.get('failures',0))==0 and int(s.attrib.get('errors',0))==0 and int(s.attrib.get('skipped',0))==0
assert os.environ['CUDA_VISIBLE_DEVICES']=='2' and torch.cuda.device_count()==1
probe=torch.zeros(1,device='cuda');assert probe.device.type=='cuda';torch.cuda.synchronize()
manifest=json.loads((P/'tests-manifest.json').read_text());profile=json.loads((P/'profile-g1.json').read_text())
out=dict(root_head='cac6c15599efcbe47a1a7ed30f59a475e4997fd4 (host verified; uncommitted files separately hashed)',production_geometry_unchanged=True,production_activated=False,acceptance_passed=False,tests=tests,test_source_changed_during_final=manifest['changed_during_tests'],profile_source_changed=[p for p in profile['source_before'] if profile['source_before'][p]!=profile['source_after'].get(p)],cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES'],probe_device=str(probe.device),gpu=torch.cuda.get_device_name(0),torch=torch.__version__,cuda=torch.version.cuda,gpu_inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name','--format=csv'],text=True),formal_STOP={name:(Path('results/task7/t7.18-20261021')/name/'STOP').exists() for name in ['formal-sync','formal-async']},source_sha256={str(p):sha(p) for p in [*Path('src').glob('task7*/*.py'),*Path('scripts').glob('task7_selfcoll_*.py')]},artifact_sha256={str(p):sha(p) for p in P.iterdir() if p.is_file() and p.name!='verification.json'})
(P/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','artifact_sha256']},indent=2))
owner=(P/'robot_v1.py').stat()
for p in [*P.rglob('*'),P]:os.chown(p,owner.st_uid,owner.st_gid,follow_symlinks=False)
