#!/usr/bin/env python3
"""External continuation from the safe interrupted C checkpoint; no global scans in the learner thread."""
import argparse,datetime as dt,functools,hashlib,json,os,shlex,shutil,signal,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from task9_lr import real_batch as b,real_program as m,real_g1 as g
from task9_lr.runtime import artifact_digest,activate
SOURCE='b8f3d63b4fb0846156fcfc72663008763a5346d85020daef9025d7f790154c05'
STOP=False

def read(p):return json.loads(Path(p).read_text())
def publish(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name('.'+p.name+'.tmp')
 with tmp.open('w') as f:json.dump(v,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for part in iter(lambda:f.read(8*1024*1024),b''):h.update(part)
 return h.hexdigest()
def local(p,out=None):
 p=Path(p)
 if ROOT==Path('/workspace') and out and p.is_relative_to(out):return Path('/output')/p.relative_to(out)
 return b.local_path(p)
def refpath(ref,out=None):
 path=local(ref['path'],out)
 if sha(path)!=ref['sha256']:raise ValueError('recovery evidence SHA changed: '+str(path))
 return path
def auth_read(path):
 a=read(path)
 if a.get('format')!='task9-lr-external-resume-authorization-v1' or a.get('status')!='PASS_CONDITIONAL_NATIVE_RESTORE' or a.get('reviewer')!=b.REVIEWER or a.get('source_digest')!=SOURCE:raise ValueError('explicit frozen-source recovery authorization required')
 if a.get('run_id')!='t9.11-real-program-20261104-r3' or (a.get('arm'),a.get('seed'))!=('C',4718):raise ValueError('only the authorized C4718 recovery is allowed')
 for name,digest in a['adapter_files'].items():
  if sha(local(name))!=digest:raise ValueError('external recovery adapter changed')
 p=b.read(refpath(a['protocol']));p['_sealed_sha256']=a['protocol']['sha256'];m.select(p,'remaining','C',4718)
 if p['source_digest']!=SOURCE or artifact_digest()!=SOURCE:raise ValueError('native source drift')
 expected=dict(steps=2969467,updates=296921,env_actions=2969467,pending_remaining=0,validation_pending=None)
 if a['expected_state']!=expected or a['expected_episode_before']!=2156 or a['expected_episode_after']!=2352:raise ValueError('recovery scientific boundary changed')
 return a,p

def bridge(a):
 sys.path.insert(0,str(ROOT/'scripts/task9_io_bridge'))
 import task9_io_bridge_impl as io
 path=refpath(a['io_bridge_authorization'])
 os.environ.update(io.environment(a['io_bridge_authorization']['path'],a['io_bridge_authorization']['sha256'],container=ROOT==Path('/workspace')))
 io.install()
 from task9_lr import diagnostics,evaluation
 if not all(getattr(fn,'_task9_io_rescan_v1',False) for fn in (m.scan_growth,diagnostics.OutputBudget.refresh,evaluation.guarded_size)):raise RuntimeError('required monitor bridge missing')
 return io

def episodes(out):
 total=0
 for path in out.rglob('episodes-started.jsonl'):
  with path.open() as f:
   for line in f:total+=read_line(line)['count']
 return total
def read_line(line):return json.loads(line)
def resource_check(a,p,budget):
 grow,diag=m.scan_growth(p,budget)
 if budget['storage_upper_bytes']+grow+40*1024**3>p['max_output_bytes']:raise OSError('global output cap/full-save reserve')
 if budget['diagnostic_upper_bytes']+diag+256*1024**2>p['max_diagnostic_log_bytes']:raise OSError('global diagnostic cap/unmetered reserve')
 count=episodes(local(p['new_output_root'],p['new_output_root']))
 if count<a['expected_episode_before'] or count>a['expected_episode_after'] or p['consumed']['evaluation_episodes']+count>p['max_evaluation_episodes']:raise ValueError('write-ahead evaluation quota')
 return dict(output_bytes=budget['storage_upper_bytes']+grow,diagnostic_bytes=budget['diagnostic_upper_bytes']+diag,evaluations=count)


def rollback_reset_counters(state,delta,last_sampling):
 # A reset attempt increments reporting counters before durable ended_reset and
 # before sampling commits a new core. Only the exact uncommitted last reset
 # is debited once, so unchanged train will credit it once on its next loop.
 if state['pending'] is not None or last_sampling.get('event')!='ended_reset' or last_sampling.get('steps')!=state['steps'] or last_sampling.get('count')!=delta['episodes'] or delta['episodes']<=0:raise ValueError('cannot prove one uncommitted accounted reset')
 before=dict(episodes=state['episodes'],strict_success=state['strict_success'],episode_end=dict(state['episode_end']))
 if any(before[key]<delta[key] for key in ('episodes','strict_success')) or any(before['episode_end'][key]<value for key,value in delta['episode_end'].items()):raise ValueError('reset accounting debit exceeds prior statistics')
 for key in ('episodes','strict_success'):state[key]-=delta[key]
 for key,value in delta['episode_end'].items():state['episode_end'][key]-=value
 after=dict(episodes=state['episodes'],strict_success=state['strict_success'],episode_end=dict(state['episode_end']))
 return dict(scope='one uncommitted ended_reset reporting-counter debit only',last_sampling=last_sampling,before=before,subtract=delta,after=after,network_replay_environment_RNG_unchanged=True)

def worker(a,p):
 from task9_lr import diagnostics,evaluation,real_lon
 bridge(a)
 if os.environ.get('CUDA_VISIBLE_DEVICES')!='0' or os.environ.get('TASK9_PHYSICAL_GPU_UUID')!=p['preferred_gpu_uuid']:raise RuntimeError('recovery GPU UUID mapping missing')
 out=local(p['new_output_root'],p['new_output_root']);attempt=local(a['attempt_root'],p['new_output_root']);attempt.mkdir(parents=True,exist_ok=True)
 budget=m.checked_budget(p,a['budget_review']);view=m.resource_view(p,{'budget_review':a['budget_review']})
 diagnostics.install_output_budget(view)
 checkpoint=local(a['checkpoint']['path'],p['new_output_root']);config=read(refpath(a['config']))
 if checkpoint.name!='interrupted.pt' or config['total_transfers']!=3000000:raise ValueError('only full interrupted2969467→original3M recovery allowed')
 # Full SHA is checked by the independent authorization before launch. Native
 # loader still validates the complete source/pools/config/unsafe/RNG contract.
 if checkpoint.stat().st_size!=a['checkpoint_bytes']:raise ValueError('authorized full checkpoint size changed')
 activate()
 import torch
 from task8_lower import training
 from task7_lower.recovery import safe_to_resume
 torch.set_num_threads(config['threads'])
 safe,reason=safe_to_resume(checkpoint,out/'formal-C-seed4718/interactions.jsonl')
 if not safe:raise RuntimeError('original journal recovery refused: '+reason)
 publish(attempt/'journal-check.json',dict(safe=safe,reason=reason,checkpoint=a['checkpoint']))
 original_load=training.load_checkpoint
 def observed_load(path,device):
  if Path(path)!=checkpoint:raise ValueError('foreign resume checkpoint')
  began=time.monotonic();result=original_load(path,device);sac,replay,env,state,stored=result
  pending=state['pending'];remaining=0 if pending is None else len(pending['ids'])-pending['cursor']
  actual=dict(steps=state['steps'],updates=sac.update_count,env_actions=state['env_actions'],pending_remaining=remaining,validation_pending=state['validation_pending'])
  if actual!=a['expected_state'] or stored!=config or sac.env_steps!=a['expected_state']['steps']:raise ValueError('native full restore boundary/config mismatch')
  correction=None
  if a.get('reset_accounting_correction'):
   from task7_lower.recovery import last_record
   c=env.core;ended=c.terminated|c.truncated;hit=ended&c.terminated&(c.failures>=c.failure_limit)
   delta=dict(episodes=int(ended.sum()),strict_success=int((ended&c.strict_success).sum()),episode_end=dict(fail_limit=int(hit.sum()),other_terminated=int((ended&c.terminated&~hit).sum()),truncated=int((ended&c.truncated&~c.terminated).sum())))
   correction=rollback_reset_counters(state,delta,last_record(out/'formal-C-seed4718/sampling-started.jsonl'))
  publish(attempt/'restore.json',dict(status='PASS_NATIVE_FULL_RESTORE',**actual,full_config_equals_frozen=True,
   original_loader_and_RNG_restore=True,reset_accounting_correction=correction,trajectory_equivalence='Complete saved RNG/environment state; aborted local reset sampling is retried, not claimed bitwise identical to uninterrupted training.',safe_to_resume=dict(safe=safe,reason=reason),actual_devices=real_lon.actual_devices(sac,replay),wall_s=time.monotonic()-began,checkpoint=a['checkpoint']))
  return result
 training.load_checkpoint=observed_load
 folder=out/'formal-C-seed4718';start=time.monotonic();deadline=min(dt.datetime.fromisoformat(p['deadline']).timestamp(),time.time()+a['max_worker_seconds'])
 def guard():
  evaluation.guarded_size(view)
  if time.time()>=deadline-a['save_reserve_s'] or (attempt/'STOP').exists():raise InterruptedError('authorized recovery stop/deadline')
 try:
  value=training.train(config,folder,resume=checkpoint,max_wall_s=a['max_worker_seconds']-a['save_reserve_s'],
   evaluator=functools.partial(evaluation.evaluate,protocol=view,recording=True),resource_guard=guard)
  if value['state']['steps']!=3000000 or episodes(out)!=2352:raise ValueError('recovery did not finish original3M/periodic quota')
  publish(attempt/'worker-terminal.json',dict(status='PASS',steps=3000000,updates=value['updates'],worker_wall_s=time.monotonic()-start,finished_epoch=time.time(),source_digest=SOURCE))
 except BaseException as error:
  publish(attempt/'worker-terminal.json',dict(status='FAIL',error=repr(error),traceback=traceback.format_exc(),worker_wall_s=time.monotonic()-start,finished_epoch=time.time()));raise
 return 0

def docker(args,**kw):return subprocess.run(['sg','docker','-c',shlex.join(['docker']+args)],**kw)
def inspection(cid):return json.loads(docker(['inspect',cid],capture_output=True,text=True,timeout=10,check=True).stdout)[0]
def control(a,p,auth_path):
 global STOP
 def stop(*_):
  global STOP
  STOP=True
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 bridge(a);out=Path(p['new_output_root']);attempt=Path(a['attempt_root']);attempt.mkdir(parents=True,exist_ok=False)
 budget=m.checked_budget(p,a['budget_review']);resource_check(a,p,budget)
 folder=out/'formal-C-seed4718'
 # Preserve all previous attempt terminals and native runtime metadata.
 for name in ('runtime.json','last-exit-costs.json','config.json','worker-terminal.json'):
  if (folder/name).exists():shutil.copyfile(folder/name,attempt/('before-'+name))
 if episodes(out)!=a['expected_episode_before']:raise ValueError('unexpected prior evaluation consumption')
 archive_step=a.get('archive_unstarted_evaluation_step',3000000)
 empty=folder/f'validation-{archive_step:07d}.diagnostics'
 if empty.exists():
  files=[q for q in empty.rglob('*') if q.is_file()]
  if not a.get('archive_unstarted_diagnostics') or any(q.stat().st_size for q in files):raise ValueError('cannot archive nonempty or unauthorized diagnostics')
  for ledger in out.rglob('episodes-started.jsonl'):
   with ledger.open() as stream:
    if any(str(archive_step) in json.loads(line).get('evaluation','') for line in stream):raise ValueError('terminal evaluation already started')
  shutil.move(str(empty),str(attempt/f'archived-unstarted-validation-{archive_step:07d}.diagnostics'))
 import task9_io_bridge_impl as io
 env=io.environment(a['io_bridge_authorization']['path'],a['io_bridge_authorization']['sha256'],True)
 # Finite allocation never reuses/restarts a failed native CID.
 apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
 if p['preferred_gpu_uuid'] in apps:raise RuntimeError('authorized GPU is occupied; no existing task stopped')
 name='forem-task9-recover-2250k-'+str(int(time.time()));started=time.time();end=min(dt.datetime.fromisoformat(p['deadline']).timestamp(),started+a['allocation_lease_s'])
 cmd=['run','-d','--name',name,'--cidfile',str(attempt/'container.cid'),'--gpus','device='+p['preferred_gpu_uuid'],'--user',f'{os.getuid()}:{os.getgid()}','--read-only','--network','none','--shm-size','2g']
 for host,inside,ro in [(str(ROOT),'/workspace',True),('/home/ybc/projects/CL-FoReM/forem','/history',True),(str(out),'/output',False),(p['new_log_root'],'/runlogs',False)]:cmd+=['--mount',f'type=bind,src={host},dst={inside}'+(',readonly' if ro else '')]
 for key,value in dict(env,CUDA_VISIBLE_DEVICES='0',TASK9_PHYSICAL_GPU_UUID=p['preferred_gpu_uuid'],PYTHONDONTWRITEBYTECODE='1',TASK9_LR_LOG_PATH='/output/'+str(Path(a['attempt_root']).relative_to(out))+'/worker.txt',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',TMPDIR='/output/tmp').items():cmd+=['--env',key+'='+value]
 cmd+=['--workdir','/output','--entrypoint','python3',g.IMAGE,'-I','-S','-c','import time;time.sleep(max(0,'+repr(end)+'-time.time()))']
 cid=docker(cmd,capture_output=True,text=True,timeout=60,check=True).stdout.strip();state=inspection(cid)
 m.validate_single_gpu_allocation(state,p)
 if state['Image']!=g.IMAGE or not state['State']['Running']:raise ValueError('recovery container identity mismatch')
 publish(attempt/'allocation.json',dict(container_id=cid,inspect=state,started_epoch=started,lease_deadline_epoch=end,authorization=str(auth_path)))
 command=['docker','exec',cid,'python3','-B','-u','/workspace/scripts/task9_11_program_recover_v2.py','--worker','--authorization',str(local(auth_path)) if ROOT==Path('/workspace') else '/workspace/'+str(Path(auth_path).relative_to(ROOT))]
 # The host control is itself launched detached by the parent. Child remains in
 # its own session with durable logs, bounded lease and exact-ID termination.
 with (attempt/'worker.txt').open('xb') as log:
  process=subprocess.Popen(['sg','docker','-c',shlex.join(command)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  publish(attempt/'status.json',dict(status='RUNNING',container_id=cid,exec_pid=process.pid,started_epoch=time.time(),source_digest=SOURCE,command=command))
  cap_end=min(end-a['control_reserve_s'],time.time()+a['max_worker_seconds'])
  error=None
  try:
   while process.poll() is None:
    resource_check(a,p,budget)
    if STOP or (attempt/'STOP').exists() or time.time()>=cap_end:
     (folder/'STOP').touch();error='bounded recovery STOP/cap';break
    time.sleep(5)
   if error:raise RuntimeError(error)
   if process.wait()!=0:raise RuntimeError('recovery worker exited nonzero')
   if read(attempt/'worker-terminal.json').get('status')!='PASS':raise RuntimeError('missing native recovery success')
  except BaseException as exc:
   error=repr(exc);(folder/'STOP').touch()
   while process.poll() is None and time.time()<cap_end:
    time.sleep(2)
  finally:
   current=inspection(cid)
   m.validate_single_gpu_allocation(current,p)
   if current['Id']!=cid or current['Image']!=g.IMAGE or current['State']['StartedAt']!=state['State']['StartedAt']:raise ValueError('refuse foreign CID cleanup')
   docker(['stop','--time','10',cid],capture_output=True,text=True,timeout=30,check=True)
   stopped=inspection(cid);publish(attempt/'container-stopped.json',dict(container_stopped=not stopped['State']['Running'] and stopped['State']['Pid']==0,inspect=stopped))
  if error:
   publish(attempt/'status.json',dict(status='FAIL',error=error,finished_epoch=time.time(),container_id=cid));raise RuntimeError(error)
 terminal=read(attempt/'worker-terminal.json')
 summary=folder/'summary.json'
 result=dict(status='PASS',run_id=p['run_id'],source_digest=SOURCE,activity='remaining-C-4718',attempt_id=attempt.name,container_id=cid,gpu_uuid=p['preferred_gpu_uuid'],exact_stopped=read(attempt/'container-stopped.json'),actual_worker_wall_s=terminal['worker_wall_s'],actual_outer_wall_s=time.time()-started,native_restore=dict(path=str(attempt/'restore.json'),sha256=sha(attempt/'restore.json')),safe_to_resume=dict(path=str(attempt/'journal-check.json'),sha256=sha(attempt/'journal-check.json')),summary=dict(path=str(summary),sha256=sha(summary)),episodes_before=a['expected_episode_before'],episodes_after=episodes(out),steps=terminal['steps'],updates=terminal['updates'])
 publish(attempt/'result.json',result)
 publish(attempt/'status.json',dict(status='PASS_REQUIRES_AGGREGATE_REVIEW',finished_epoch=time.time(),container_id=cid))
 review=subprocess.run(a['completion_review_argv'],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=900)
 (attempt/'aggregate-review.stdout').write_text(review.stdout);(attempt/'aggregate-review.stderr').write_text(review.stderr)
 if review.returncode or json.loads(review.stdout).get('status')!='PASS':
  publish(attempt/'status.json',dict(status='STOPPED_AGGREGATE_REVIEW',error='logical remaining aggregate review did not pass',finished_epoch=time.time()))
  raise RuntimeError('logical remaining aggregate review did not pass')
 dispatch=Path(a['dispatch_ready_file'])
 if not dispatch.is_relative_to(ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2'):raise ValueError('dispatch authorization outside independent namespace')
 while not dispatch.exists():
  if time.time()>=dt.datetime.fromisoformat(p['deadline']).timestamp():raise RuntimeError('true deadline reached awaiting next dispatch')
  publish(attempt/'status.json',dict(status='WAITING_AUTHORIZED_SHARD_DISPATCH',finished_training=True,dispatch_ready_file=str(dispatch),updated_epoch=time.time()))
  time.sleep(5)
 next_plan=read(dispatch)
 if next_plan.get('status')!='PASS_SHARD_DISPATCH' or next_plan.get('run_id')!=p['run_id'] or next_plan.get('source_digest')!=SOURCE:raise ValueError('independent parallel dispatch identity')
 for name,digest in next_plan['adapter_files'].items():
  if sha(local(name))!=digest:raise ValueError('authorized shard dispatcher changed')
 with (attempt/'next-driver.log').open('ab') as log:
  driver=subprocess.Popen(next_plan['argv'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=ROOT.parent)
 publish(attempt/'status.json',dict(status='PASS_DRIVER_RESUMED',driver_pid=driver.pid,finished_epoch=time.time(),container_id=cid))
 return 0

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--authorization',required=True);parser.add_argument('--worker',action='store_true');args=parser.parse_args()
 a,p=auth_read(args.authorization)
 return worker(a,p) if args.worker else control(a,p,Path(args.authorization).resolve())
if __name__=='__main__':sys.exit(main())
