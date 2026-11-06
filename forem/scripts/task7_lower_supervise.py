#!/usr/bin/env python3
"""One lower worker, atomic full-state resume; never operates containers/ROS.
Explicit gate required for formal runs. Crash recovery uses only an intact
checkpoint; repeated failure at the same checkpoint stops for diagnosis.
"""
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from task7_lower.recovery import safe_to_resume

def main():
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--variant',choices=['sync','async'],required=True);p.add_argument('--gate',required=True);p.add_argument('--environments',type=int);a=p.parse_args()
 gate=json.loads(Path(a.gate).read_text());gpu=os.environ.get('CUDA_VISIBLE_DEVICES')
 if gpu not in ('2','3') or not gate['allow_formal'] or gate['hours_per_5M'][a.variant]>48:raise RuntimeError('formal resource/performance gate not satisfied')
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True);(out/'supervisor.pid').write_text(str(os.getpid()));log=(out/'supervisor.log').open('a');stop=False;worker=None;last_failed=None
 def emit(**kw):
  row=dict(time=time.time(),**kw);log.write(json.dumps(row)+'\n');log.flush();print(json.dumps(row),flush=True)
 def terminate(sig,frame):
  nonlocal stop
  stop=True;(out/'STOP').touch()
  if worker and worker.poll() is None:worker.send_signal(signal.SIGTERM)
 signal.signal(signal.SIGTERM,terminate);signal.signal(signal.SIGINT,terminate)
 while not stop and not (out/'STOP').exists():
  summary=out/'summary.json'
  if summary.exists() and json.loads(summary.read_text())['state']['steps']==5000000:emit(event='complete');return 0
  checkpoints=[x for x in out.glob('checkpoint-*.pt') if not x.name.endswith('.actor.pt')]+[x for x in [out/'interrupted.pt',out/'final.pt'] if x.exists()]
  latest=max(checkpoints,key=lambda x:x.stat().st_mtime) if checkpoints else None
  identity=None if latest is None else (str(latest),latest.stat().st_mtime_ns)
  if latest:
   safe,reason=safe_to_resume(latest,out/'interactions.jsonl')
   if not safe:emit(event='budget_safe_resume_blocked',checkpoint=str(latest),reason=reason);return 1
  elif (out/'interactions.jsonl').exists():
   emit(event='budget_safe_restart_blocked',reason='interactions exist without a complete checkpoint');return 1
  cmd=[sys.executable,'-u',str(ROOT/'scripts/task7_lower_train.py'),'--config',a.config,'--output',str(out),'--variant',a.variant]
  if a.environments:cmd+=['--environments',str(a.environments)]
  if latest:cmd+=['--resume',str(latest)]
  with (out/'worker.log').open('a') as f:
   worker=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);(out/'worker.pid').write_text(str(worker.pid));emit(event='worker_start',pid=worker.pid,gpu=gpu,argv=cmd)
   while worker.poll() is None:
    if (out/'STOP').exists():worker.send_signal(signal.SIGTERM)
    (out/'heartbeat.json').write_text(json.dumps(dict(supervisor=os.getpid(),worker=worker.pid,time=time.time(),gpu=gpu)))
    try:worker.wait(timeout=30)
    except subprocess.TimeoutExpired:pass
   emit(event='worker_exit',rc=worker.returncode)
  if worker.returncode==0:continue
  current=[x for x in out.glob('checkpoint-*.pt') if not x.name.endswith('.actor.pt')]+[x for x in [out/'interrupted.pt',out/'final.pt'] if x.exists()]
  if not current:emit(event='failed_before_first_checkpoint');return 1
  newest=max(current,key=lambda x:x.stat().st_mtime)
  identity=(str(newest),newest.stat().st_mtime_ns)
  if last_failed==identity:emit(event='repeated_failure_same_checkpoint',checkpoint=identity);return 1
  last_failed=identity
 return 130
if __name__=='__main__':raise SystemExit(main())
