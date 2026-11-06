"""Container-owned detached pipeline; exact STOP is /output/STOP. No blind retry."""
import os,json,time,subprocess,sys,traceback
from pathlib import Path
O=Path('/output');L=Path('/runlogs')
def dump(x):
 p=O/'driver-state.json';t=O/'driver-state.tmp';t.write_text(json.dumps(x,indent=2)+'\n');os.replace(t,p)
commands=[['run.py','--phase','smoke','--arm','bioik'],['run.py','--phase','formal','--arm','current'],['diagnostic.py'],['run.py','--phase','formal','--arm','bioik'],['report.py']]
identity=dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],started_epoch=time.time(),container='forem-task9-12-bioik',gpu_uuid=os.environ.get('NVIDIA_VISIBLE_DEVICES'),stop='/output/STOP')
try:
 for n,args in enumerate(commands):
  if (O/'STOP').exists():raise InterruptedError('STOP before stage')
  name=f'pipeline-{n}-{args[0][:-3]}';command=[sys.executable,'-B','-u','/work/scripts/'+args[0],*args[1:]]
  with (L/(name+'.log')).open('a') as log:
   start=time.time();p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
   dump(dict(identity,status='running',stage=n,command=command,worker_pid=p.pid,worker_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().split()[21],stage_started_epoch=start))
   rc=p.wait()
  with (O/'stage-costs.jsonl').open('a') as f:f.write(json.dumps(dict(stage=n,command=command,pid=p.pid,start_epoch=start,end_epoch=time.time(),wall_s=time.time()-start,returncode=rc))+'\n')
  if rc:raise RuntimeError(f'stage {n} exit {rc}; inspect {name}.log; no automatic retry')
 dump(dict(identity,status='complete',finished_epoch=time.time()))
except BaseException:
 dump(dict(identity,status='stopped',finished_epoch=time.time(),traceback=traceback.format_exc()));raise
