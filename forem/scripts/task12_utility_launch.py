#!/usr/bin/env python3
"""Durable single-run CPU preparation / GPU training launcher, no automatic retry."""
import json,os,subprocess,sys,time,hashlib,traceback
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path('/home/ybc/projects/CL-FoReM');RUN=ROOT/'forem/results/task12/t12-utility-20261105-r6';LOG=ROOT/'forem/logs/task12/t12-utility-20261105-r6';GPU='GPU-656ca5c1-681f-48a2-7d1f-a00824723f68'
def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def write(name,x):
 p=RUN/name;q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');q.replace(p)
if len(sys.argv)<2 or sys.argv[1]=='launch':
 if (RUN/'driver.pid').exists():raise SystemExit('driver already registered; inspect status, no duplicate launch')
 LOG.mkdir(parents=True,exist_ok=True);f=(LOG/'driver.log').open('a');p=subprocess.Popen([sys.executable,'-u',__file__,'run'],stdout=f,stderr=subprocess.STDOUT,start_new_session=True);(RUN/'driver.pid').write_text(str(p.pid));print(json.dumps({'driver_pid':p.pid,'run':str(RUN),'log':str(LOG/'driver.log')}));sys.exit()
start=time.monotonic();driver=dict(pid=os.getpid(),start=now(),status='starting',attempt=1)
try:
 gpu_before=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used','--format=csv,noheader'],text=True);(RUN/'gpu-before.txt').write_text(gpu_before);selected=[line for line in gpu_before.splitlines() if GPU in line];assert len(selected)==1 and int(selected[0].split(',')[-1].strip().split()[0])<128
 for f in ['task12_utility_train.py','task12_utility_launch.py']:(RUN/'code'/f).write_bytes((ROOT/'forem/scripts'/f).read_bytes())
 files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (RUN/'code').glob('*.py')};write('code-version.json',dict(at=now(),head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),files=files,frozen_source='r1 frozen-source',baseline_model='r3 accepted code/Heatmap',actual_agent_model='unknown',actual_reasoning='unknown'))
 cmd=['docker','run','--rm','--name','forem-task12-utility-r6','--user',f'{os.getuid()}:{os.getgid()}','--gpus','device='+GPU,'--cpuset-cpus','10-11','-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=2','-e','PYTHONDONTWRITEBYTECODE=1','-e','MPLCONFIGDIR=/tmp/matplotlib','-e','PYTHONPATH=/run/code:/original/frozen-source/src','-v',str(ROOT/'forem/results/task12/t12-abc-20261104-r1')+':/original:ro','-v',str(ROOT/'forem/results/task12/t12-cost32-20261104-r3')+':/baseline:ro','-v',str(RUN)+':/run','mm_husky:node01','/opt/python310/bin/python3','-u','/run/code/task12_utility_train.py']
 driver.update(command=cmd,status='running');write('driver.json',driver)
 with (LOG/'worker.log').open('a') as f:
  p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);driver['docker_client_pid']=p.pid;write('driver.json',driver);rc=p.wait()
 driver.update(status='finished' if rc==0 else 'failed',exit_code=rc,end=now(),wall_s=time.monotonic()-start);write('driver.json',driver)
except BaseException:
 driver.update(status='launcher_failed',end=now(),wall_s=time.monotonic()-start,error=traceback.format_exc());write('driver.json',driver);raise
