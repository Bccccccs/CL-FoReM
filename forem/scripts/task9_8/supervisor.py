"""Config-driven bounded B supervisor. No retries; zero-episode checks precede load."""
import argparse,datetime,hashlib,json,os,shlex,subprocess,sys,time
from pathlib import Path
PLAN=[(4718,'off','01-4718-off'),(4718,'gate','02-4718-on-gate'),(4718,'remaining','03-4718-remaining'),(4719,'all','04-4719-all'),(4720,'all','05-4720-all')]

def write(path,obj):
 tmp=Path(str(path)+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,path)
def command(argv,**kw):return subprocess.run(argv,**kw)
def docker_argv(argv):return ['sg','docker','-c',shlex.join(['docker']+argv)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def worker_command(cfg,seed,phase,name,remaining):
 return docker_argv(['exec',cfg['container'],'timeout','--signal=TERM','--kill-after=30s',f'{remaining:.3f}s','python3','-B','-u','/workspace/scripts/task9_8/replay.py','--run-config','/output/run.json','--seed',str(seed),'--phase',phase,'--name',name])
def ownership_command(cfg):
 return docker_argv(['exec',cfg['container'],'chown','-R',f'{os.getuid()}:{os.getgid()}','/output','/runlogs'])

def create_command(cfg):
 args=['run','-d','--name',cfg['container'],'--gpus','device='+cfg['gpu_uuid'],'--user',cfg.get('container_user','0:0'),'--read-only','--network','none','--shm-size','2g']
 for src,dst,ro in [(cfg['historical_root'],'/root/mm_husky_ws',True),(cfg['workspace']+'/forem','/workspace',True),(cfg['output_root'],'/output',False),(cfg['log_root'],'/runlogs',False)]:
  args+=['--mount',f'type=bind,src={src},dst={dst}'+(',readonly' if ro else '')]
 for v in ['PYTHONDONTWRITEBYTECODE=1','PYTHONUNBUFFERED=1','CUDA_VISIBLE_DEVICES=0','PYTHONPATH=/root/mm_husky_ws/src','OMP_NUM_THREADS=2','OPENBLAS_NUM_THREADS=2','TMPDIR=/output/tmp']:
  args+=['--env',v]
 args+=['--workdir','/root/mm_husky_ws','--entrypoint','/bin/sleep',cfg['image'],'infinity']
 return docker_argv(args)
def output_size(cfg):
 return sum(p.stat().st_size for r in (Path(cfg['output_root']),Path(cfg['log_root'])) for p in r.rglob('*') if p.is_file())
def apps():
 return command(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout
def started_episodes(out):
 return sum(json.loads(line)['count'] for p in out.glob('*/episodes-started.jsonl') for line in p.open())
def verify_identity(cfg,inspection):
 assert inspection['Image']==cfg['image']
 assert inspection['HostConfig']['DeviceRequests'][0]['DeviceIDs']==[cfg['gpu_uuid']]
 mounts={m['Destination']:m for m in inspection['Mounts']}
 for destination,source in [('/root/mm_husky_ws',cfg['historical_root']),('/workspace',cfg['workspace']+'/forem')]:
  assert not mounts[destination]['RW'] and mounts[destination]['Source']==source
 assert mounts['/output']['RW'] and mounts['/output']['Source']==cfg['output_root']
 assert mounts['/runlogs']['RW'] and mounts['/runlogs']['Source']==cfg['log_root']
 assert inspection['HostConfig']['ReadonlyRootfs']

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--run-config',required=True);args=parser.parse_args()
 cfg=json.loads(Path(args.run_config).read_text());out=Path(cfg['output_root']);log=Path(cfg['log_root']);root=Path(cfg['workspace']);deadline=cfg['deadline_epoch'];state_path=log/'queue-state.json'
 assert Path(args.run_config).resolve()==out/'run.json'
 assert out.name==log.name==cfg['run_id']
 assert not state_path.exists(),'existing queue ledger: never reuse'
 assert not any((out/name).exists() for _,_,name in PLAN),'existing phase directory: never reuse'
 assert not (out/'container-inspect.json').exists(),'existing allocation: never reuse'
 prior_records=cfg.get('prior_runs') or [dict(path=cfg['prior_run'])]
 total_episodes=0;total_gpu=0.;total_bytes=0
 for prior in prior_records:
  old=json.loads((Path(prior['path'])/'final-accounting.json').read_text())
  total_episodes+=old['actual_episodes'];total_gpu+=old['gpu_resource_window_seconds'];total_bytes+=old['conservative_total_output_bytes']
 assert cfg['prior_episodes']==total_episodes
 assert abs(cfg['prior_gpu_seconds']-total_gpu)<1e-6
 assert cfg['prior_output_bytes']==total_bytes
 state=dict(status='zero_episode_checks',host_pid=os.getpid(),started_epoch=time.time(),runs=[],run_id=cfg['run_id'],deadline_epoch=deadline,prior_gpu_seconds=cfg['prior_gpu_seconds'],prior_output_bytes=cfg['prior_output_bytes']);created=False
 write(state_path,state)
 launch=dict(container_create=create_command(cfg),worker_commands=[worker_command(cfg,s,p,n,deadline-time.time()-cfg['drain_seconds']) for s,p,n in PLAN],host_queue=sys.argv)
 write(out/'launch-commands.json',launch)
 try:
  assert deadline-time.time()>5*1331.1+cfg['drain_seconds'],'insufficient remaining window before zero checks'
  assert cfg['gpu_uuid'] not in apps(),'GPU busy before creation'
  assert sha(root/'forem/doc/agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.csv')=='e36d1888b3bb5621f4a8c70d2eb2cea5316ae5883361017dead80de4169a57b8'
  assert json.loads((out/'input-verification.json').read_text())['status']=='PASS'
  (out/'tmp').mkdir(exist_ok=False)
  cfg['gpu_allocation_start_epoch']=time.time();write(out/'run.json',cfg)
  p=command(launch['container_create'],capture_output=True,text=True);write(out/'container-create-result.json',dict(command=launch['container_create'],exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr;created=True
  p=command(docker_argv(['inspect',cfg['container']]),capture_output=True,text=True,check=True);inspection=json.loads(p.stdout)[0];write(out/'container-inspect.json',[inspection]);verify_identity(cfg,inspection)
  check=docker_argv(['exec',cfg['container'],'python3','-B','-u','/workspace/scripts/task9_8/replay.py','--run-config','/output/run.json','--import-check'])
  with (log/'zero-import-check.log').open('x') as f:p=command(check,stdout=f,stderr=subprocess.STDOUT)
  write(out/'zero-import-command.json',dict(command=check,exit_code=p.returncode));assert p.returncode==0,'zero import failed; no rollout'
  test=docker_argv(['exec',cfg['container'],'python3','-B','-m','unittest','discover','-s','/workspace/scripts/task9_8','-p','test_analysis.py'])
  with (log/'zero-regression.log').open('x') as f:p=command(test,stdout=f,stderr=subprocess.STDOUT)
  write(out/'zero-regression-command.json',dict(command=test,exit_code=p.returncode));assert p.returncode==0,'synthetic coverage regression failed; no rollout'
  # Validate all generated commands use current config and the repaired replay entry.
  for cmd in launch['worker_commands']:
   inner=shlex.split(cmd[3]);assert inner[2]==cfg['container']
   assert '/workspace/scripts/task9_8/replay.py' in inner and '/output/run.json' in inner and 'queue.py' not in cmd[3]
  write(out/'zero-command-contract.json',dict(status='PASS',run_id=cfg['run_id'],container=cfg['container'],output_root=str(out),log_root=str(log),worker_commands=launch['worker_commands'],phase_directories_absent=True,zero_episodes=started_episodes(out)==0))
  state['status']='active';write(state_path,state)
  for idx,(seed,phase,name) in enumerate(PLAN):
   used=started_episodes(out);remaining=deadline-time.time();size=output_size(cfg)
   runtime_proxy=max([1331.1]+[r.get('wall_s',0) for r in state['runs']])
   gpu_elapsed=cfg['prior_gpu_seconds']+cfg.get('zero_check_gpu_seconds',0)+time.time()-cfg['gpu_allocation_start_epoch']
   preflight=dict(epoch=time.time(),episodes_already_started=used,remaining_episode_budget=cfg['max_episodes']-cfg['prior_episodes']-used,remaining_wall_s=remaining,remaining_gpu_seconds=cfg['max_gpu_seconds']-gpu_elapsed,remaining_output_bytes=cfg['max_output_bytes']-cfg['prior_output_bytes']-size-cfg['external_charge_reserve_bytes'],remaining_evaluation_count=len(PLAN)-idx,runtime_proxy_plus_drain_s=runtime_proxy*(len(PLAN)-idx)+cfg['drain_seconds'],new_output_bytes=size,disk_available_bytes=os.statvfs(out).f_bavail*os.statvfs(out).f_frsize)
   write(out/f'{name}-preflight.json',preflight)
   assert used+cfg['prior_episodes']+196<=cfg['max_episodes']
   assert preflight['remaining_wall_s']>preflight['runtime_proxy_plus_drain_s'],'remaining wall cannot safely fit remaining evaluations'
   assert preflight['remaining_gpu_seconds']>preflight['runtime_proxy_plus_drain_s'],'remaining GPU budget insufficient'
   assert preflight['remaining_output_bytes']>32*1024**2
   assert preflight['disk_available_bytes']>cfg['max_output_bytes']
   gpu=apps();(out/f'{name}-gpu-before.csv').write_text(gpu);assert cfg['gpu_uuid'] not in gpu,'GPU busy before evaluation'
   if idx==2:assert json.loads((out/PLAN[1][2]/'gate.json').read_text())['status']=='PASS'
   cmd=worker_command(cfg,seed,phase,name,remaining-cfg['drain_seconds']);record=dict(name=name,seed=seed,phase=phase,command=cmd,started_epoch=time.time(),status='running');state['runs'].append(record)
   with (log/f'{name}.log').open('x') as f:
    process=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);record['host_pid']=process.pid;write(state_path,state);start=time.monotonic()
    while process.poll() is None:
     time.sleep(5);now=time.time();nbytes=output_size(cfg);gpu=apps();current=[line for line in gpu.splitlines() if cfg['gpu_uuid'] in line]
     if now>deadline-cfg['drain_seconds'] or nbytes+cfg['prior_output_bytes']+cfg['external_charge_reserve_bytes']>cfg['max_output_bytes']-16*1024**2 or now-cfg['gpu_allocation_start_epoch']+cfg['prior_gpu_seconds']+cfg.get('zero_check_gpu_seconds',0)>cfg['max_gpu_seconds']-cfg['drain_seconds'] or len(current)>1:
      (out/'STOP').touch()
     with (log/'gpu-monitor.jsonl').open('a') as mon:mon.write(json.dumps(dict(epoch=now,compute=gpu,new_output_bytes=nbytes,started_episodes=started_episodes(out)))+'\n')
    record.update(exit_code=process.returncode,wall_s=time.monotonic()-start,ended_epoch=time.time(),status='done' if process.returncode==0 else 'failed')
   write(state_path,state)
   assert process.returncode==0,f'{name} failed rc{process.returncode}; no retry'
  assert started_episodes(out)==980
  state.update(status='completed_pending_C',ended_epoch=time.time(),actual_started_episodes=980)
 except BaseException as ex:
  state.update(status='stopped',error=repr(ex),ended_epoch=time.time());print(repr(ex),flush=True)
 finally:
  if created:
   ownership=command(ownership_command(cfg),capture_output=True,text=True)
   write(out/'output-ownership-cleanup.json',dict(exit_code=ownership.returncode,stderr=ownership.stderr,scope='new isolated output/logs only'))
   p=command(docker_argv(['stop','--time','5',cfg['container']]),capture_output=True,text=True);write(out/'cleanup-command.json',dict(command=docker_argv(['stop','--time','5',cfg['container']]),exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
   p=command(docker_argv(['inspect',cfg['container']]),capture_output=True,text=True);write(out/'container-final-inspect.json',json.loads(p.stdout))
  state.update(new_output_bytes=output_size(cfg),actual_started_episodes=started_episodes(out),cleanup_end_epoch=time.time())
  write(state_path,state)
 return 0 if state['status']=='completed_pending_C' else 1

if __name__=='__main__':sys.exit(main())
