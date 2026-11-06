"""Separate pytest processes preserve each suite's existing local test imports."""
import subprocess,sys,json,hashlib,os
from pathlib import Path
P=Path('results/task7/t7.18.2-r3-20261021');root=Path.cwd()
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for d in ['task7_sim','task7_lower','task7_upper'] for p in (root/'src'/d).rglob('*.py')}
before=hashes();rows=[]
for suite in ['task7_sim','task7_lower','task7_upper']:
 cmd=[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','src/'+suite,'--junitxml='+str(P/('pytest-'+suite+'.xml'))]
 env=dict(os.environ);env['TASK722_GPU']='1'
 code=subprocess.call(cmd,env=env);rows.append(dict(suite=suite,command=cmd,exit_code=code));print(suite,'exit',code,flush=True)
after=hashes();(P/'tests-manifest.json').write_text(json.dumps(dict(before=before,after=after,changed_during_tests=[p for p in before if before[p]!=after.get(p)],results=rows),indent=2))
sys.exit(max(r['exit_code'] for r in rows))
