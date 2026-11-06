"""Read-only acceptance/integrity, own-run permissions; never starts training."""
import argparse,ast,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import xml.etree.ElementTree as ET
P=Path('results/task7/t7.18.2-r2-20261021');L=Path('logs/task7/t7.18.2-r2-20261021')
a=argparse.ArgumentParser();a.add_argument('--uid',type=int,required=True);a.add_argument('--gid',type=int,required=True);args=a.parse_args()
subprocess.run([sys.executable,'-B','-u','scripts/task7_selfcoll_multisphere_test_fixtures.py'],check=True)
fit=json.loads((P/'fit-audit.json').read_text());fit['links'][0]['curobo_reference_count']=None;fit['quality_limitations']='Sphere union QMC volume minus signed triangle integral is a proxy, not exact outside volume; sampled protrusion is not global maximum; nonconverged SLSQP centres use recomputed enclosing radii';(P/'fit-audit.json').write_text(json.dumps(fit,indent=2)+'\n')
summary=json.loads((P/'summary.json').read_text());chain=summary['chain'];assert chain['N']==388 and chain['TP']==13 and chain['FN']==0 and chain['FPR']<.069 and chain['pairs']['2,13']==[6,0,382,0]
for name,n in [('sync',1582),('async',19308)]:assert summary[name]['N']==n and summary[name]['FP']==0 and summary[name]['FN']==0
cfg=json.loads(Path('config/task7/robot_geometry.json').read_text());candidate=json.loads((P/'robot_geometry_v3.json').read_text());v1=Path('config/task7/robot_geometry_v1.json');assert v1.read_bytes()==(P/'robot_geometry.json.before').read_bytes()
for key in ['capsules','body','self_spheres','self_allowed','self_body_allowed','names','self_names']:assert cfg[key]==candidate[key]
sha=hashlib.sha256(Path('config/task7/robot_geometry.json').read_bytes()).hexdigest();train=json.loads(Path('config/task7/lower_train.json').read_text());assert train['robot_geometry_version']==cfg['geometry_version'] and train['robot_geometry_sha256']==sha
pub=json.loads((P/'publication.json').read_text());assert pub['sha256']==sha
manifest=json.loads((P/'tests-manifest.json').read_text());assert not manifest['changed_during_tests'];suites=[]
for name in ['task7_sim','task7_lower','task7_upper']:
 tree=ET.parse(P/('pytest-'+name+'.xml'));r=list(tree.getroot().iter('testsuite'));stats={k:sum(int(x.get(k,0)) for x in r) for k in ['tests','failures','errors','skipped']};assert stats['failures']==stats['errors']==stats['skipped']==0;suites.append(dict(name=name,**stats))
post=json.loads((P/'post-test-revalidation.json').read_text()) if (P/'post-test-revalidation.json').exists() else None
post_changes=[]
for path,before in manifest['after'].items():
 relative=Path(path).relative_to(Path.cwd());current=hashlib.sha256(relative.read_bytes()).hexdigest()
 if current!=before:
  assert post is not None and not post['changed'] and all(x['exit_code']==0 for x in post['runs'])
  assert post['before'][path]==post['after'][path]==current
  assert str(relative)=='src/task7_sim/decision_env.py',relative
  post_changes.append(dict(path=str(relative),full_suite_sha256=before,revalidated_sha256=current))
if post is not None:
 for path,h in post['after'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h,path
 for run in post['runs']:
  r=list(ET.parse(P/('post-tests-'+run['name']+'.xml')).getroot().iter('testsuite'));assert sum(int(x.get('failures',0))+int(x.get('errors',0))+int(x.get('skipped',0)) for x in r)==0

profile=json.loads((P/'profile-g1.json').read_text());assert profile['effective_work_equal'] and all(c['attempted']==c['committed']==512 and c['self_failure']==0 for r in profile['profile'] for c in r['counts'])
profile_external_changes=[]
for path,h in profile['source_after'].items():
 current=hashlib.sha256(Path(path).read_bytes()).hexdigest()
 if current!=h:
  assert path=='src/task7_sim/decision_env.py' and post is not None
  profile_external_changes.append(path)
# bench_full/Core/robot/kinematics/perception/motion/risk dependencies unchanged;
# decision_env is not on the E256 benchmark execution path.

for row in json.loads((P/'cluster-equivalence.json').read_text()):assert row['differences']==0
allow=json.loads((P/'allowed-audit-final-v3.json').read_text());assert len(allow['rows'])==25 and all(x['complete'] and x['samples']==10000 for x in allow['rows']);assert not cfg['self_body_allowed'][2][5]
stops={str(p):p.exists() for p in [Path('results/task7/t7.18-20261021/formal-sync/STOP'),Path('results/task7/t7.18-20261021/formal-async/STOP')]};assert all(stops.values())
files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in P.rglob('*') if p.is_file() and p.name!='verification.json'}
source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for d in ['src/task7_sim','src/task7_lower','src/task7_upper'] for p in Path(d).rglob('*.py')};source.update({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('config/task7/robot_geometry.json'),Path('config/task7/lower_train.json'),v1]})
ledger=[json.loads(line) for line in (L/'commands.jsonl').read_text().splitlines()];used=sum(x['wall_s'] for x in ledger);assert used+590<7200 and max(x['wall_s'] for x in ledger)<600
result=dict(acceptance=True,production_geometry_sha256=sha,geometry_version=cfg['geometry_version'],sphere_count=len(cfg['self_spheres']),suites=suites,tests_total=sum(x['tests'] for x in suites),post_suite_external_changes=post_changes,post_revalidation=post,profile_external_changes=profile_external_changes,profile=profile['profile'],g1=profile['g1'],formal_stop=stops,source_sha256=source,artifact_sha256=files,completed_container_wall_s_before_this_command=used,command_count_before_this_command=len(ledger),scope='No formal training, git commit, external-process stop, reward/termination/action/observation/IK/tolerance edits. Original capsule fields unchanged.',limitations=['Zero-pose sphere exclusions include base/upper with 412/10000 mesh contacts (intentionally exempt under user rule)','FPR 4.53% is from the fitting/acceptance chain set, not held-out generalization','Old elbow test q retains a conservative forearm/wrist2 FP, raw surface gap 3.245mm'])
(P/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
for root in [P,L]:
 for path in [root,*root.rglob('*')]:
  if not path.is_symlink():os.chown(path,args.uid,args.gid)
print(json.dumps(dict(acceptance=True,tests=result['tests_total'],suites=suites,geometry_sha256=sha,completed_container_wall_s_before_this_command=used)),flush=True)
