#!/usr/bin/env python3
"""Explicit parallel native training shards; external control only, b8f3 unchanged."""
import argparse,datetime as dt,fcntl,functools,importlib.util,json,os,shlex,shutil,signal,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import task9_11_program_recover_v2 as u
from task9_lr import real_batch as b,real_program as m,diagnostics,evaluation,real_lon
from task9_lr.runtime import activate,artifact_digest
SOURCE=u.SOURCE
STOP=False
class ResourceBusy(Exception):
 """A shared GPU becoming busy is a scheduling event, not a worker failure."""

def busy_gpu_uuids():
 output=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True,timeout=15)
 return {line.split(',')[0].strip() for line in output.splitlines() if line.strip()}

OUTPUT_HOST=None

def ref(path,full=False):
 path=Path(path);canonical=path
 if ROOT==Path('/workspace'):
  if path.is_relative_to('/output'):canonical=Path(OUTPUT_HOST)/path.relative_to('/output')
  elif path.is_relative_to(ROOT):canonical=b.HOST_ROOT/path.relative_to(ROOT)
 return dict(path=str(canonical),sha256=u.sha(path))
def load_context(path):
 global OUTPUT_HOST
 a=u.read(path)
 expected=dict(format='task9-lr-parallel-shards-authorization-v1',status='PASS_PARALLEL_SHARDS',reviewer=b.REVIEWER,run_id='t9.11-real-program-20261104-r3',source_digest=SOURCE,own_episode_quota=2352)
 if any(a.get(k)!=v for k,v in expected.items()):raise ValueError('parallel authorization identity/quotas')
 for name,digest in a['adapter_files'].items():
  if u.sha(u.local(name))!=digest:raise ValueError('parallel adapter changed')
 p=b.read(u.refpath(a['protocol']));p['_sealed_sha256']=a['protocol']['sha256'];OUTPUT_HOST=p['new_output_root']
 policy=u.read(u.refpath(a['policy']))
 if policy.get('status')!='PASS_FINITE_SHARED_RESOURCE_POLICY' or policy['source_digest']!=SOURCE or policy['run_id']!=p['run_id']:raise ValueError('unique shared policy identity')
 names=[x['name'] for x in a['jobs']]
 if names!=['L4718','C4719','L4719']:raise ValueError('fixed three original independent runs')
 for job in a['jobs']:
  if job['name']!=job['arm']+str(job['seed']) or policy['allocation_seconds'][job['name']]!=50400 or job['config']!=p['scientific_configs'][f"{job['arm']}-{job['seed']}"]:raise ValueError('run budget/config isolation')
 if [x['gpu_index'] for x in a['jobs']]!=[0,1,'ANY_FREE'] or len(policy['allowed_gpu_uuids'])!=2:raise ValueError('authorized GPU scheduling')
 if artifact_digest()!=SOURCE:raise ValueError('native source drift')
 return a,p,policy

def install_bridge(refvalue):
 sys.path.insert(0,str(ROOT/'scripts/task9_io_bridge'));import task9_io_bridge_impl as io
 u.refpath(refvalue);os.environ.update(io.environment(refvalue['path'],refvalue['sha256'],ROOT==Path('/workspace')));io.install()
 if not all(getattr(fn,'_task9_io_rescan_v1',False) for fn in (m.scan_growth,diagnostics.OutputBudget.refresh,evaluation.guarded_size)):raise RuntimeError('parallel IO bridge not installed')
 return io

def folder(p,job):return Path(p['new_output_root'])/f"formal-{job['arm']}-seed{job['seed']}"
def own_episodes(path):
 count=0
 for ledger in Path(path).rglob('episodes-started.jsonl'):
  with ledger.open() as stream:
   for line in stream:count+=json.loads(line)['count']
 return count

def worker(a,p,policy,job,phase,spec):
 install_bridge(job['io_bridge_authorization'])
 if os.environ.get('CUDA_VISIBLE_DEVICES')!='0' or os.environ.get('TASK9_PHYSICAL_GPU_UUID')!=spec['gpu_uuid']:raise ValueError('shard GPU ordinal/UUID mapping')
 out=u.local(folder(p,job),p['new_output_root']);phase_root=u.local(spec['phase_root'],p['new_output_root']);phase_root.mkdir(parents=True,exist_ok=True)
 config=u.read(u.refpath(job['config']))
 if config['total_transfers']!=3000000 or config['seed']!=job['seed'] or config['group']!=job['arm']:raise ValueError('frozen run scientific config')
 before=0 if phase=='profile' else 196
 if own_episodes(out)!=before:raise ValueError('phase own evaluation count already consumed')
 # Native writers scan only this shard's data and its own mounted logs. The
 # host coordinator alone checks all global roots and two full-save reserves.
 view=dict(p,container_output=str(out),container_logs='/runlogs',external_output_roots=[],
  max_output_bytes=spec['local_output_cap'],max_diagnostic_log_bytes=spec['local_diagnostic_cap'],
  max_evaluation_episodes=p['max_evaluation_episodes']-p['consumed']['evaluation_episodes'])
 diagnostics.install_output_budget(view);activate()
 import torch
 from task8_lower import training
 torch.set_num_threads(config['threads']);original_load=training.load_checkpoint
 def observed_load(path,device):
  began=time.monotonic();result=original_load(path,device);sac,replay,env,state,stored=result
  expected_steps=0 if spec.get('zero_resume') and Path(path).name=='interrupted.pt' else 250000
  if stored!=config or state['steps']!=expected_steps or sac.env_steps!=expected_steps or state.get('unsafe_update') or state.get('validation_pending') is not None:raise ValueError('own native profile full boundary')
  if expected_steps==0:
   if sac.update_count or state['env_actions'] or state['action_calls']:raise ValueError('zero-step recovery has scientific consumption')
   u.publish(phase_root/'zero-restore.json',dict(status='PASS_ZERO_STEP_RESTORE',steps=0,updates=0,original_loader_and_RNG_restore=True));return result
  pending=state['pending'];proof=dict(status='PASS_NATIVE_PROFILE_RESTORE',steps=250000,updates=sac.update_count,scientific_limit=3000000,env_actions=state['env_actions'],pending_remaining=0 if pending is None else len(pending['ids'])-pending['cursor'],validation_pending=state.get('validation_pending'),unsafe_update=False,stored_config_equals_frozen=True,original_loader_and_RNG_restore=True,actual_devices=real_lon.actual_devices(sac,replay),wall_s=time.monotonic()-began)
  if proof['updates']!=24975:raise ValueError('own profile update boundary')
  u.publish(out/('profile-restore.json' if phase=='profile' else 'remaining-restore.json'),proof);return result
 training.load_checkpoint=observed_load
 deadline=min(dt.datetime.fromisoformat(p['deadline']).timestamp(),time.time()+spec['max_worker_seconds'])
 def guard():
  evaluation.guarded_size(view)
  if time.time()>=deadline-a['save_reserve_s'] or (phase_root/'STOP').exists() or (out/'STOP').exists():raise InterruptedError('true phase allocation/deadline/STOP')
 def evaluator(sac,cfg,target,**kwargs):
  if own_episodes(out)+196>2352:raise ValueError('own run cannot exceed twelve periodic evaluations')
  return evaluation.evaluate(sac,cfg,target,protocol=view,recording=True,**kwargs)
 started=time.monotonic()
 try:
  kwargs=dict(max_wall_s=spec['max_worker_seconds']-a['save_reserve_s'],evaluator=evaluator,resource_guard=guard)
  if phase=='profile':value=training.train(config,out,pause_after_consumed=250000,**dict(kwargs,**({'resume':out/'interrupted.pt'} if spec.get('zero_resume') else {})))
  else:value=training.train(config,out,resume=out/'profile.pt',**kwargs)
  if phase=='profile':
   restored=training.load_checkpoint(out/'profile.pt','cuda');del restored
  expected=196 if phase=='profile' else 2352
  if own_episodes(out)!=expected:raise ValueError('own phase evaluation count incomplete')
  summary=out/('profile-summary.json' if phase=='profile' else 'summary.json')
  state=value.get('state',{});steps=value.get('steps',state.get('steps'));updates=value.get('updates')
  expected_boundary=(250000,24975) if phase=='profile' else (3000000,299975)
  if (steps,updates)!=expected_boundary:raise ValueError('native phase consumed/update boundary')
  result=dict(status='PASS',run_id=p['run_id'],source_digest=SOURCE,job=job['name'],phase=phase,arm=job['arm'],seed=job['seed'],folder=str(folder(p,job)),summary=ref(out/'profile-summary.json' if phase=='profile' else out/'summary.json'),profile_restore=ref(out/('profile-restore.json' if phase=='profile' else 'remaining-restore.json')),steps=steps,updates=updates,episodes_before=before,episodes_after=expected,actual_worker_wall_s=time.monotonic()-started,finished_epoch=time.time())
  if phase=='profile':
   evidence_root=out
   for name in ('checkpoint-costs.jsonl','interactions.jsonl'):shutil.copyfile(out/name,evidence_root/('profile-'+name))
   diag=sum(q.stat().st_size for q in out.rglob('*') if q.is_file() and (any('diagnostics' in z for z in q.parts) or q.suffix in ('.json','.jsonl','.txt','.bin')))
   u.publish(evidence_root/'profile-diagnostic-account.json',dict(diagnostic_bytes=diag,steps=250000))
   result.update(profile_evidence=dict(profile_checkpoint=ref(out/'profile.pt',True),profile_summary=ref(out/'profile-summary.json'),profile_restore=result['profile_restore'],profile_evaluation=ref(out/'validation-0250000.json'),checkpoint_costs=ref(evidence_root/'profile-checkpoint-costs.jsonl'),interactions=ref(evidence_root/'profile-interactions.jsonl'),diagnostic_account=ref(evidence_root/'profile-diagnostic-account.json')),profile_costs=ref(evidence_root/'profile-checkpoint-costs.jsonl'),interactions=ref(evidence_root/'profile-interactions.jsonl'))
  u.publish(phase_root/'worker-result.json',result)
 except BaseException as error:
  u.publish(phase_root/'worker-result.json',dict(status='FAIL',error=repr(error),traceback=traceback.format_exc(),actual_worker_wall_s=time.monotonic()-started,finished_epoch=time.time()));raise
 return 0

class Coordinator:
 def __init__(self,a,p,policy,authorization):
  self.a=a;self.p=p;self.policy=policy;self.authorization=authorization;self.root=Path(p['new_output_root'])/'parallel-shards';self.root.mkdir(exist_ok=True)
  self.jobs={x['name']:x for x in a['jobs']};self.active={};self.state=u.read(self.root/'state.json') if (self.root/'state.json').exists() else {'jobs':{},'completed_worker_s':0.,'completed_gpu_s':0.,'status':'STARTED'}
  self.budget=m.checked_budget(p,a['budget_review']);self.io=install_bridge(a['host_io_bridge_authorization'])
 def save(self):self.state['updated_epoch']=time.time();u.publish(self.root/'state.json',self.state)
 def guard(self):
  grow,diag=m.scan_growth(self.p,self.budget)
  if self.budget['storage_upper_bytes']+grow+2*40*1024**3>self.p['max_output_bytes'] or self.budget['diagnostic_upper_bytes']+diag+256*1024**2>self.p['max_diagnostic_log_bytes']:raise OSError('shared two-writer storage/diagnostic cap')
  now=time.time();running=sum(now-x['started_epoch'] for x in self.active.values())
  if self.budget['worker_upper_s']+self.state['completed_worker_s']+running>self.p['max_worker_seconds'] or self.budget['gpu_upper_s']+self.state['completed_gpu_s']+running>self.p['max_gpu_seconds']:raise RuntimeError('shared actual worker/GPU budget')
  if STOP:raise InterruptedError('coordinator signal STOP')
  if now>=dt.datetime.fromisoformat(self.p['deadline']).timestamp() or (self.root/'STOP').exists():raise InterruptedError('true global deadline/STOP')
 def call_review(self,template,job=None,phase=None):
  args=[x.replace('{job}',job or '').replace('{phase}',phase or '') for x in template]
  result=subprocess.run(args,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=900)
  log=self.root/('review-'+str(time.time_ns()));log.mkdir();(log/'stdout.txt').write_text(result.stdout);(log/'stderr.txt').write_text(result.stderr)
  if result.returncode or json.loads(result.stdout).get('status')!='PASS':raise RuntimeError('independent shard review did not pass')
 def launch(self,name,phase,gpu_index):
  if STOP or (self.root/'STOP').exists():raise InterruptedError('no shard dispatch after STOP')
  job=self.jobs[name];record=self.state['jobs'].setdefault(name,{'worker_s':0.,'gpu_s':0.,'phases':{}})
  cap=self.policy['allocation_seconds'][name]-record['worker_s']
  cap=min(cap,dt.datetime.fromisoformat(self.p['deadline']).timestamp()-time.time()-self.a['control_reserve_s'])
  if cap<=self.a['save_reserve_s']:raise RuntimeError('no actual allocation left')
  gpu=self.policy['allowed_gpu_uuids'][gpu_index]
  if gpu in busy_gpu_uuids():raise ResourceBusy(gpu)
  retry=record.get('zero_retry') if phase=='profile' else None
  phase_root=Path(retry['phase_root']) if retry else Path(self.p['new_output_root'])/'shards'/name/phase
  phase_root.mkdir(parents=True,exist_ok=True)
  if any(phase_root.iterdir()):raise ValueError('phase directory contains prior evidence; explicit recovery required')
  logs=Path(self.p['new_log_root'])/'shards'/name;logs.mkdir(parents=True,exist_ok=True)
  spec=dict(job=name,phase=phase,gpu_uuid=gpu,phase_root=str(phase_root),zero_resume=bool(retry),max_worker_seconds=cap,
   local_output_cap=self.p['max_output_bytes']-self.budget['storage_upper_bytes'],local_diagnostic_cap=self.p['max_diagnostic_log_bytes']-self.budget['diagnostic_upper_bytes'])
  u.publish(phase_root/'spec.json',spec)
  env=self.io.environment(job['io_bridge_authorization']['path'],job['io_bridge_authorization']['sha256'],True)
  started=time.time();lease=min(dt.datetime.fromisoformat(self.p['deadline']).timestamp(),started+cap+self.a['control_reserve_s'])
  cmd=['run','-d','--name','forem-t9-'+name+'-'+phase+'-'+str(int(started)),'--gpus','device='+gpu,'--user',f'{os.getuid()}:{os.getgid()}','--read-only','--network','none','--shm-size','2g']
  for host,inside,ro in [(str(ROOT),'/workspace',True),('/home/ybc/projects/CL-FoReM/forem','/history',True),(self.p['new_output_root'],'/output',False),(str(logs),'/runlogs',False)]:cmd+=['--mount',f'type=bind,src={host},dst={inside}'+(',readonly' if ro else '')]
  for key,value in dict(env,CUDA_VISIBLE_DEVICES='0',TASK9_PHYSICAL_GPU_UUID=gpu,TASK9_LR_LOG_PATH='/runlogs/'+phase_root.name+'.txt',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',TMPDIR='/output/tmp').items():cmd+=['--env',key+'='+value]
  cmd+=['--workdir','/output','--entrypoint','python3',u.g.IMAGE,'-I','-S','-c','import time;time.sleep(max(0,'+repr(lease)+'-time.time()))']
  cmd[2:2]=['--cidfile',str(phase_root/'container.cid'),'--label','forem.task9.run_id='+self.p['run_id'],'--label','forem.task9.job='+name,'--label','forem.task9.phase='+phase]
  item=dict(job=name,phase=phase,gpu_index=gpu_index,gpu_uuid=gpu,container_id=None,started_epoch=started,cap_s=cap,phase_root=str(phase_root),exec_pid=None)
  record['active']=dict(item);self.active[name]=dict(item,process=None,log=None);self.save()
  cid=u.docker(cmd,capture_output=True,text=True,timeout=60,check=True).stdout.strip();self.active[name]['container_id']=cid;record['active']['container_id']=cid;self.save();inspect=u.inspection(cid)
  requests=inspect['HostConfig']['DeviceRequests']
  if inspect['Image']!=u.g.IMAGE or len(requests)!=1 or requests[0]['DeviceIDs']!=[gpu]:raise ValueError('shard exact image/single UUID')
  u.publish(phase_root/'allocation.json',dict(container_id=cid,inspect=inspect,lease_deadline_epoch=lease))
  argv=['docker','exec',cid,'python3','-B','-u','/workspace/scripts/task9_11_program_shards.py','--worker','--authorization','/workspace/'+str(self.authorization.relative_to(ROOT)),'--job',name,'--phase',phase,'--phase-spec','/output/'+str((phase_root/'spec.json').relative_to(self.p['new_output_root']))]
  log=(logs/(phase_root.name+'.txt')).open('xb');self.active[name]['log']=log;process=subprocess.Popen(['sg','docker','-c',shlex.join(argv)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  item=dict(job=name,phase=phase,gpu_index=gpu_index,gpu_uuid=gpu,container_id=cid,started_epoch=started,cap_s=cap,phase_root=str(phase_root),exec_pid=process.pid)
  record['active']=item;self.active[name]=dict(item,process=process,log=log);self.state['status']='RUNNING';self.save()
 def finish(self,name):
  item=self.active[name];phase_root=Path(item['phase_root']);job=self.jobs[name];record=self.state['jobs'][name];rc=item['process'].wait();item['log'].close()
  current=u.inspection(item['container_id']);initial=u.read(phase_root/'allocation.json')['inspect']
  if u.g.container_identity(current)!=u.g.container_identity(initial):raise ValueError('refuse foreign/restarted shard cleanup')
  u.docker(['stop','--time','10',item['container_id']],capture_output=True,text=True,timeout=30,check=True);stopped=u.inspection(item['container_id'])
  exact=dict(container_stopped=not stopped['State']['Running'] and stopped['State']['Pid']==0,inspect=stopped);u.publish(phase_root/'container-stopped.json',exact)
  elapsed=time.time()-item['started_epoch'];record['gpu_s']+=elapsed;self.state['completed_gpu_s']+=elapsed
  value=u.read(phase_root/'worker-result.json') if (phase_root/'worker-result.json').exists() else {'status':'FAIL','error':'worker missing terminal'}
  record['worker_s']+=elapsed;self.state['completed_worker_s']+=elapsed
  value.update(container_id=item['container_id'],gpu_uuid=item['gpu_uuid'],exact_stopped=exact,actual_outer_wall_s=elapsed)
  u.publish(phase_root/'result.json',value);record['phases'][item['phase']]=dict(status=value['status'],result=ref(phase_root/'result.json'));record.pop('active',None);self.active.pop(name);self.save()
  if rc or value['status']!='PASS':raise RuntimeError('shard failed; preserved without retry')
  self.call_review(self.a['phase_review_argv'],name,item['phase']);record['phases'][item['phase']]['certified']=True;self.save()
  self.call_review(self.a['publish_argv']);return item['gpu_index'],item['phase']
 def shutdown_owned(self,reason):
  # Shared STOP requests only this controller's workers. Give native save a
  # bounded drain, then close every owned immutable CID even if launch failed
  # between docker create and recording its Popen handle.
  for name,item in self.active.items():
   target=folder(self.p,self.jobs[name]);target.mkdir(parents=True,exist_ok=True);(target/'STOP').touch()
  end=min(time.time()+self.a['save_reserve_s'],dt.datetime.fromisoformat(self.p['deadline']).timestamp())
  while any(x.get('process') is not None and x['process'].poll() is None for x in self.active.values()) and time.time()<end:time.sleep(2)
  failures=[]
  for name,item in list(self.active.items()):
   phase_root=Path(item['phase_root']);cid=item.get('container_id')
   if not cid and (phase_root/'container.cid').exists():cid=(phase_root/'container.cid').read_text().strip()
   try:
    stopped=None
    if cid:
     current=u.inspection(cid);allocation=phase_root/'allocation.json'
     if allocation.exists():
      if u.g.container_identity(current)!=u.g.container_identity(u.read(allocation)['inspect']):raise ValueError('owned shard identity/start changed')
     else:
      labels=current.get('Config',{}).get('Labels',{});requests=current['HostConfig']['DeviceRequests']
      if current.get('Id')!=cid or current.get('Image')!=u.g.IMAGE or labels.get('forem.task9.run_id')!=self.p['run_id'] or labels.get('forem.task9.job')!=name or labels.get('forem.task9.phase')!=item['phase'] or len(requests)!=1 or requests[0].get('DeviceIDs')!=[item['gpu_uuid']]:raise ValueError('unverified partial launch identity')
      u.publish(phase_root/'first-cleanup-inspect.json',current)
     u.docker(['stop','--time','10',cid],capture_output=True,text=True,timeout=30,check=True)
     stopped=u.inspection(cid);u.publish(phase_root/'container-stopped.json',dict(container_stopped=not stopped['State']['Running'] and stopped['State']['Pid']==0,inspect=stopped))
    elapsed=time.time()-item['started_epoch'];value=u.read(phase_root/'worker-result.json') if (phase_root/'worker-result.json').exists() else {'status':'FAIL','error':'no worker terminal'}
    worker=elapsed
    value.update(controller_status='STOPPED_BY_CONTROLLER',controller_reason=reason,container_id=cid,gpu_uuid=item['gpu_uuid'],actual_outer_wall_s=elapsed)
    u.publish(phase_root/'result.json',value)
    record=self.state['jobs'][name];record['worker_s']+=worker;record['gpu_s']+=elapsed if cid else 0;self.state['completed_worker_s']+=worker;self.state['completed_gpu_s']+=elapsed if cid else 0
    record['phases'][item['phase']]=dict(status='FAIL_CONTROL_CLOSURE',result=ref(phase_root/'result.json'));record.pop('active',None);self.active.pop(name)
    if item.get('log'):item['log'].close()
   except BaseException as error:
    failures.append(dict(job=name,container_id=cid,error=repr(error),cost_status='UNKNOWN_RETAIN_RESERVE'))
  self.state['cleanup_failures']=failures;self.save()
 def prepare_zero_retry(self,name):
  if self.active or any(x.get('active') for x in self.state['jobs'].values()):raise ValueError('active controller requires adoption, not recovery preparation')
  record=self.state['jobs'][name];out=folder(self.p,self.jobs[name])
  def clear_original_stop(retry):
   token=out/'STOP'
   if token.exists():
    stat=token.stat();identity=dict(size=stat.st_size,mtime_ns=stat.st_mtime_ns,inode=stat.st_ino)
    if identity!=retry['stop_identity'] or u.sha(token)!=retry['stop_sha256']:raise ValueError('STOP changed after recovery preparation; retain new stop')
    token.unlink()
  if record.get('zero_retry'):
   retry=record['zero_retry'];archive=Path(retry['evidence_root'])
   if u.read(archive/'preparation.json')!=retry or record['phases'].get('profile'):raise ValueError('prepared recovery already consumed or inconsistent')
   clear_original_stop(retry);return retry
  failed=record['phases'].get('profile')
  if not failed or failed['status']!='FAIL_CONTROL_CLOSURE':raise ValueError('only explicit zero-step control recovery is supported')
  old=Path(failed['result']['path']);result=u.read(old)
  if u.sha(old)!=failed['result']['sha256']:raise ValueError('failed evidence changed')
  stop=u.read(old.parent/'container-stopped.json')
  if not stop.get('container_stopped'):raise ValueError('original allocation not closed')
  current=u.inspection(result['container_id'])
  if current['State']['Running'] or current['State']['Pid'] or u.g.container_identity(current)!=u.g.container_identity(stop['inspect']):raise ValueError('failed container identity not safely stopped')
  meta=u.read(out/'interrupted.meta.json')
  if any(meta.get(k)!=0 for k in ('steps','env_actions','action_calls')) or meta.get('resume_safe') is not True or own_episodes(out):raise ValueError('consumed run requires full progress-aware recovery')
  if u.read(out/'config.json')!=u.read(u.refpath(self.jobs[name]['config'])):raise ValueError('zero-step scientific configuration changed')
  if (out/'learning.jsonl').exists() and (out/'learning.jsonl').stat().st_size:raise ValueError('unexpected learning consumption')
  if not (out/'interrupted.pt').is_file() or not (out/'STOP').is_file():raise ValueError('zero-step full checkpoint or original STOP missing')
  paths=sorted(out.iterdir())
  if any(not path.is_file() or path.is_symlink() for path in paths):raise ValueError('unexpected zero-step output entry')
  archive=self.root/(name+'-zero-retry-evidence');archive.mkdir(exist_ok=True)
  files={path.name:dict(size=path.stat().st_size,mtime_ns=path.stat().st_mtime_ns,inode=path.stat().st_ino) for path in paths}
  intent=dict(original_result=failed['result'],source_files=files)
  intent_path=archive/'intent.json'
  if intent_path.exists():
   if u.read(intent_path)!=intent:raise ValueError('zero-step sources changed during preparation')
  else:
   if any(x.name!='.intent.json.tmp' for x in archive.iterdir()):raise ValueError('unrecognized recovery archive')
   u.publish(intent_path,intent)
  # Each copied file is committed atomically; an interrupted copy is retryable.
  # Hard links retain large model bytes across native atomic checkpoint replace.
  for path in paths:
   target=archive/path.name
   if target.exists():
    if path.suffix=='.pt':
     if not os.path.samefile(path,target):raise ValueError('checkpoint snapshot identity changed')
    elif u.sha(path)!=u.sha(target):raise ValueError('snapshot bytes differ from original')
    continue
   if path.suffix=='.pt':os.link(path,target)
   else:
    tmp=target.with_name('.'+target.name+'.copy.tmp');shutil.copy2(path,tmp);os.replace(tmp,target)
  retry=dict(phase_root=str(old.parent.with_name('profile-retry1')),original_result=failed['result'],evidence_root=str(archive),resume_checkpoint=str(out/'interrupted.pt'),stop_sha256=u.sha(out/'STOP'),stop_identity=files['STOP'])
  u.publish(archive/'preparation.json',retry)
  prior=json.loads(json.dumps(self.state))
  record.setdefault('failed_phases',[]).append(dict(phase='profile',**failed))
  record['phases'].pop('profile');record['zero_retry']=retry
  self.state['status']='PREPARED_ZERO_STEP_RECOVERY'
  try:self.save()
  except BaseException:
   self.state=prior;raise
  # Commit durable state before clearing the original token. A crash here is
  # completed idempotently by the same explicit preparation command.
  clear_original_stop(retry)
  return retry
 def schedule(self):
  if STOP or (self.root/'STOP').exists():raise InterruptedError('no shard scheduling after STOP')
  occupied={x['gpu_index'] for x in self.active.values()}
  busy=busy_gpu_uuids()
  occupied.update(i for i,gpu in enumerate(self.policy['allowed_gpu_uuids']) if gpu in busy)
  for name in ('L4718','C4719','L4719'):
   record=self.state['jobs'].get(name,{})
   if name in self.active or record.get('phases',{}).get('remaining',{}).get('certified'):continue
   if name=='L4719':
    if not any(self.state['jobs'].get(x,{}).get('phases',{}).get('remaining',{}).get('certified') for x in ('L4718','C4719')):continue
    available=[x for x in (0,1) if x not in occupied]
    if not available:continue
    gpu=available[0]
   else:
    gpu=0 if name=='L4718' else 1
    if gpu in occupied:continue
   phase='remaining' if record.get('phases',{}).get('profile',{}).get('certified') else 'profile'
   try:self.launch(name,phase,gpu)
   except ResourceBusy:continue  # Recheck caught another task arriving after schedule().
   occupied.add(gpu)
  self.state['waiting_jobs']=[name for name in self.jobs if name not in self.active and not self.state['jobs'].get(name,{}).get('phases',{}).get('remaining',{}).get('certified')]
  self.state['status']='RUNNING' if self.active else 'WAITING_FOR_GPU'
  self.save()
 def run(self):
  if any(x.get('active') for x in self.state['jobs'].values()):raise RuntimeError('existing active shard identity; inspect and adopt, never duplicate launch')
  m.prerequisites(self.p,m.stages()[2]) # Real C profile+remaining independent originals, quotas and closure.
  for name,record in self.state['jobs'].items():
   for phase,data in record['phases'].items():
    if data['status']!='PASS':raise RuntimeError('failed phase requires explicit recovery preparation; original evidence retained: '+name+'/'+phase)
    if data['status']=='PASS' and not data.get('certified'):
     self.call_review(self.a['phase_review_argv'],name,phase);data['certified']=True;self.save()
  while not all(self.state['jobs'].get(x,{}).get('phases',{}).get('remaining',{}).get('certified') for x in self.jobs):
   self.guard()
   for name in list(self.active):
    item=self.active[name]
    if item['process'].poll() is None:
     if time.time()-item['started_epoch']>=item['cap_s']:(folder(self.p,self.jobs[name])/'STOP').touch()
     continue
    self.finish(name)
   self.schedule();time.sleep(5)
  if not all(self.state['jobs'].get(x,{}).get('phases',{}).get('remaining',{}).get('certified') for x in self.jobs):raise RuntimeError('parallel jobs incomplete without active workers')
  self.state['status']='THREE_RUNS_COMPLETE_REQUIRES_SCIENTIFIC_ACCEPTANCE';self.save();return 0

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--authorization',required=True);parser.add_argument('--worker',action='store_true');parser.add_argument('--job');parser.add_argument('--phase',choices=['profile','remaining']);parser.add_argument('--phase-spec');parser.add_argument('--prepare-zero-retry',choices=['L4718','C4719','L4719']);a0=parser.parse_args()
 a,p,policy=load_context(a0.authorization)
 if a0.worker:
  job=next(x for x in a['jobs'] if x['name']==a0.job);return worker(a,p,policy,job,a0.phase,u.read(a0.phase_spec))
 def requested_stop(*_):
  global STOP
  STOP=True
 signal.signal(signal.SIGTERM,requested_stop);signal.signal(signal.SIGINT,requested_stop)
 coordinator=Coordinator(a,p,policy,Path(a0.authorization).resolve())
 with (coordinator.root/'coordinator.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if (coordinator.root/'state.json').exists():coordinator.state=u.read(coordinator.root/'state.json')
  if a0.prepare_zero_retry:
   print(json.dumps(coordinator.prepare_zero_retry(a0.prepare_zero_retry)));return 0
  try:return coordinator.run()
  except BaseException as error:
   coordinator.state.update(status='FAIL_CONTROL_STOPPED',error=repr(error),traceback=traceback.format_exc());coordinator.save()
   coordinator.shutdown_owned(repr(error));raise
if __name__=='__main__':sys.exit(main())
