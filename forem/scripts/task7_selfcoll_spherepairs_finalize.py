"""r3 final integrity, inherited-reference provenance and no-training checks."""
import argparse,hashlib,json,os
from pathlib import Path
import xml.etree.ElementTree as ET
P=Path('results/task7/t7.18.2-r3-20261021');L=Path('logs/task7/t7.18.2-r3-20261021');OLD=Path('results/task7/t7.18.2-r2-20261021')
p=argparse.ArgumentParser();p.add_argument('--uid',type=int,required=True);p.add_argument('--gid',type=int,required=True);args=p.parse_args()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prod=Path('config/task7/robot_geometry.json');cfg=json.loads(prod.read_text());old=json.loads((P/'robot_geometry.json.before').read_text());assert cfg==json.loads((P/'robot_geometry_v4.json').read_text());assert cfg['schema']==4
for k in ['capsules','body','self_spheres','mesh_sources','urdf_sha256','self_margin_m','names','self_names']:assert cfg[k]==old[k],k
allowed_changed={k for k in old if cfg[k]!=old[k]};assert allowed_changed<={'schema','geometry_version','self_allowed','self_body_allowed','self_allowed_reasons','allowed','allowed_audit'},allowed_changed
zero=json.loads((P/'zero-pair-audit.json').read_text());assert len(zero['rows'])==6 and zero['sphere_pairs']==14 and zero['sphere_body_pairs']==1
for row in zero['rows']:
 i,j=row['pair']
 assert (not cfg['self_allowed'][i][j]) if j<16 else (not cfg['self_body_allowed'][i][j-16])
for key,reason in old['self_allowed_reasons'].items():
 if reason in ['adjacent','fixed_installation']:
  i,j=map(int,key.split(','));assert cfg['self_allowed'][i][j] if j<16 else cfg['self_body_allowed'][i][j-16]
tested=json.loads((P/'geometry-tested-before-metadata.json').read_text());changes=[k for k in set(cfg)|set(tested) if cfg.get(k)!=tested.get(k)];assert set(changes)<={'allowed_audit','historical_r2_link_audit','zero_pair_policy_source'}
meta=json.loads((P/'metadata-readback.json').read_text());assert meta['json_roundtrip_equal'] and meta['torch_config_roundtrip_equal'];pub=json.loads((P/'publication.json').read_text());assert pub['sha256']==sha(prod)==meta['metadata']['robot_geometry_sha256']
manifest=json.loads((P/'tests-manifest.json').read_text());assert not manifest['changed_during_tests'];assert all(x['exit_code']==0 for x in manifest['results']);suites=[]
for suite in ['task7_sim','task7_lower','task7_upper']:
 nodes=list(ET.parse(P/('pytest-'+suite+'.xml')).getroot().iter('testsuite'));stats={k:sum(int(x.get(k,0)) for x in nodes) for k in ['tests','failures','errors','skipped']};assert stats['failures']==stats['errors']==stats['skipped']==0;suites.append(dict(name=suite,**stats))
for path,h in manifest['after'].items():assert sha(path)==h,('Source changed after full test',path)
start=json.loads((P/'start-snapshot.json').read_text());assert sha('src/task7_sim/core.py')==start['src/task7_sim/core.py'],'core.py differs from r3 start (investigate external changes)'
summary={}
for d,n in [('chain',388),('sync',1582),('async',19308)]:
 r=json.loads((P/f'summary-{d}.json').read_text());assert r['N']==n and r['FN']==0 and r['environment_capsule_body_equal'];assert sha(r['reference_file'])==r['reference_sha256'];assert sha(r['q_file'])==r['q_file_sha256'];assert len(r['pairs'])==83;summary[d]={k:v for k,v in r.items() if k!='pairs'}
assert summary['chain']['TP']==13 and summary['chain']['FP']==17
assert json.loads((P/'summary-chain.json').read_text())['pairs']['2,13']==[6,0,382,0]
audit=json.loads((P/'10000-confusion.json').read_text());assert audit['rows'][0]['masked']==dict(TP=412,FP=1850,TN=7738,FN=0)
for r in audit['rows'][1:]:assert r['masked']==dict(TP=0,FP=0,TN=10000,FN=0)
for r in json.loads((P/'cluster-equivalence.json').read_text()):assert r['differences']==0
for r in json.loads((P/'environment-invariance.json').read_text()):assert r['truth_base_arm_equal'] and r['local_base_arm_equal']
profile=json.loads((P/'profile-g1.json').read_text());assert profile['effective_work_equal'];assert all(c['attempted']==c['committed']==512 and c['self_failure']==0 for r in profile['profile'] for c in r['counts'])
assert profile['source_before']==profile['source_after']
for path,h in profile['source_after'].items():assert sha(path)==h,path
stops={str(Path('results/task7/t7.18-20261021')/('formal-'+v)/'STOP'):(Path('results/task7/t7.18-20261021')/('formal-'+v)/'STOP').exists() for v in ['sync','async']};assert all(stops.values())
inherited=[OLD/'allowed-q.npz',OLD/'allowed-audit-final-v3.json',OLD/'allowed-pair-0-2-certificates.npz',OLD/'allowed-pair-1-21-certificates.npz',OLD/'allowed-independent-verification.json']
ledger=[json.loads(l) for l in (L/'commands.jsonl').read_text().splitlines()];wall=sum(r['wall_s'] for r in ledger);assert wall<3600 and max(r['wall_s'] for r in ledger)<600
result=dict(acceptance=True,run_id=P.name,model='GPT6.1sol',reasoning='high',geometry_version=cfg['geometry_version'],geometry_sha256=sha(prod),suites=suites,tests_total=sum(r['tests'] for r in suites),summary=summary,core_unchanged_since_r3_start=True,metadata_only_changes_after_full_tests=changes,geometry_fields_unchanged_from_r2=True,formal_stop=stops,inherited_reference_sha256={str(f):sha(f) for f in inherited},source_sha256={str(f):sha(f) for d in ['src/task7_sim','src/task7_lower','src/task7_upper'] for f in Path(d).rglob('*.py')},artifact_sha256={str(f):sha(f) for f in P.rglob('*') if f.is_file() and f.name!='verification.json'},profile=profile['profile'],g1=profile['g1'],container_wall_s_before_this_command=wall,limitations=['Uniform 10000 base/upper FP1850/9588 (19.294952%); chain FPR is same-sample, not held out','Near-zero 402 engineering probes do not cover a continuous neighborhood','Adjacent and fixed-contact link exemptions remain; no claim of global zero false negatives','No training, checkpoint creation, git commit or core.py edits'])
(P/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
for root in [P,L]:
 for f in [root,*root.rglob('*')]:
  if not f.is_symlink():os.chown(f,args.uid,args.gid)
print(json.dumps({k:result[k] for k in ['acceptance','tests_total','geometry_version','geometry_sha256','container_wall_s_before_this_command']}),flush=True)
