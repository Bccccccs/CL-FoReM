"""Revalidate concurrent decision_env delta without changing its owner's file."""
import json,hashlib,subprocess,sys,os
from pathlib import Path
P=Path('results/task7/t7.18.2-r2-20261021');root=Path.cwd()
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for d in ['task7_sim','task7_lower','task7_upper'] for p in (root/'src'/d).rglob('*.py')}
before=hashes();runs=[]
for name,paths in [('sim-decision',['src/task7_sim/tests/test_decision_env.py','src/task7_sim/tests/test_full_geometry.py','src/task7_sim/tests/test_selfcoll_multisphere.py']),('lower',['src/task7_lower']),('upper',['src/task7_upper'])]:
 argv=[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',*paths,'--junitxml='+str(P/('post-tests-'+name+'.xml'))];env=dict(os.environ,TASK722_GPU='1');code=subprocess.call(argv,env=env);runs.append(dict(name=name,argv=argv,exit_code=code));print(name,code,flush=True)
after=hashes();result=dict(before=before,after=after,changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k)),runs=runs);(P/'post-test-revalidation.json').write_text(json.dumps(result,indent=2)+'\n');assert not result['changed'] and all(x['exit_code']==0 for x in runs)
