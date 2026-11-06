"""Independent read-only original counters, code, timers, and stop audit."""
import datetime,hashlib,json,math,os,shlex,subprocess,time
from pathlib import Path
root=Path('/home/ybc/projects/CL-FoReM-task9');base=Path(__file__).resolve().parent
run=root/'forem/results/task9/t9.10-paired-20261103T144811+0800'
cfg=json.loads((run/'run.json').read_text());logs=Path(cfg['log_root'])
window=json.loads((root/'forem/doc/agent_logs/task9/task9.10/execution-window.json').read_text())
for key in ('start_epoch','deadline_epoch','max_episodes','max_gpu_seconds','max_output_bytes'):assert cfg[key]==window[key]
state=json.loads((logs/'supervisor-state.json').read_text());assert state['status']=='complete_pending_independent_review' and len(state['runs'])==6
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inventory=json.loads((run/'source-inventory.json').read_text())
for item in inventory:assert sha(item['path'])==sha(item['snapshot'])==item['sha256']
production_code=json.loads((base/'runtime-instrumentation-audit.json').read_text())
phases=[];total=0;costs={};delays={}
def quantile(values,p):
 values=sorted(values);x=(len(values)-1)*p;lo=math.floor(x);hi=math.ceil(x);return values[lo]+(values[hi]-values[lo])*(x-lo)
for arm in ('C','T'):
 costs[arm]={};delays[arm]={}
 for seed in (4718,4719,4720):
  phase=run/f'{arm}-{seed}';status=json.loads((phase/'status.json').read_text())
  assert status['status']=='done' and status['exit_code']==0 and status['started_episodes']==status['completed_episodes']==196
  ledger=[json.loads(x) for x in (phase/'episodes-started.jsonl').read_text().splitlines()]
  started=sum(x['count'] for x in ledger);assert started==196
  identities=[]
  for row in ledger:
   assert row['count']==len(row['jobs'])
   identities.extend((j['map_id'],j['seed'],j['stream_index'],j['role'],j['source_split']) for j in row['jobs'])
  assert len(set(identities))==196
  assert cfg['start_epoch']<=status['started_epoch']<status['end_epoch']<=cfg['deadline_epoch']
  total+=started
  for record in production_code:assert sha(phase/Path(record['runtime_file']).name)==record['sha256']
  loaded=json.loads((phase/'loaded.json').read_text());assert loaded['script_sha256']==sha(root/'forem/scripts/task9_10/replay.py')
  assert loaded['policy_device']==loaded['critic_device']=='cuda:0' and set(loaded['optimizer_devices'])=={'cuda:0'}
  supervised=next(x for x in state['runs'] if x['arm']==arm and x['seed']==seed)
  assert supervised['exit_code']==0 and supervised['status']=='done'
  costs[arm][seed]=dict(worker_wall_s=status['wall_s'],supervised_segment_s=supervised['wall_s'])
  timings=json.loads((phase/'timing.json').read_text())['samples'];actor=timings['actor_s'];assert actor and all(math.isfinite(x) and x>=0 for x in actor)
  delays[arm][seed]=dict(n=len(actor),p50_s=quantile(actor,.5),p95_s=quantile(actor,.95),p99_s=quantile(actor,.99),definition='synchronized host batch select_action timer; mixed last-batch shapes, not per-episode latency')
  phases.append(dict(arm=arm,seed=seed,started=started,completed=196,status_sha256=sha(phase/'status.json'),write_ahead_sha256=sha(phase/'episodes-started.jsonl')))
assert total==1176==state['started_episodes']
assert state['end_epoch']<=cfg['deadline_epoch'] and state['gpu_resource_window_s']<=cfg['max_gpu_seconds']
original_id=json.loads((run/'container-create.json').read_text())['stdout'].strip();assert len(original_id)==64
result=subprocess.run(['sg','docker','-c',shlex.join(['docker','inspect',original_id])],capture_output=True,text=True,check=True)
container=json.loads(result.stdout)[0];assert container['Id']==original_id and container['Image']==cfg['image']
assert container['State']['Running'] is False and container['State']['Pid']==0
def parse(value):
 stamp=value.rstrip('Z');whole,dot,fraction=stamp.partition('.')
 return datetime.datetime.fromisoformat(whole+'+00:00').timestamp()+(float('0.'+fraction) if dot else 0.)
actual_container_window=parse(container['State']['FinishedAt'])-parse(container['State']['StartedAt'])
assert actual_container_window<=state['gpu_resource_window_s']
run_bytes=sum(p.stat().st_size for path in (run,logs) for p in path.rglob('*') if p.is_file())
external_roots=[root/'forem/doc/agent_logs/task9/task9.10',root/'forem/doc/tasks/task9/task9.10',root/'forem/scripts/task9_10']
external_files=[root/'forem/doc'/name for name in ('PROGRESS.md','SOURCES.md','DECISIONS.md')]
external_bytes=sum(p.stat().st_size for path in external_roots for p in path.rglob('*') if p.is_file())+sum(p.stat().st_size for p in external_files)
assert external_bytes<cfg['external_charge_reserve_bytes']
assert run_bytes+cfg['external_charge_reserve_bytes']<=cfg['max_output_bytes']
out=dict(status='PASS',checked_epoch=time.time(),episodes=total,phases=phases,source_inventory_sha256=sha(run/'source-inventory.json'),source_and_snapshot_files_verified=len(inventory),runtime_instrumented_function_files_verified=18,all_actor_critic_optimizer_parameters_cuda=True,container_stopped=True,container_id=original_id,container_state=container['State'],gpu_uuid=cfg['gpu_uuid'],actual_container_window_s=actual_container_window,conservative_gpu_window_s=state['gpu_resource_window_s'],global_wall_to_supervisor_stop_s=state['end_epoch']-cfg['start_epoch'],worker_costs=costs,worker_wall_s=sum(v['worker_wall_s'] for arm in costs.values() for v in arm.values()),cost_ratios_T_over_C={seed:{key:costs['T'][seed][key]/costs['C'][seed][key] for key in ('worker_wall_s','supervised_segment_s')} for seed in (4718,4719,4720)},actor_batch_latency=delays,run_and_log_bytes=run_bytes,external_scope_measured_bytes=external_bytes,external_reserve_charged_bytes=cfg['external_charge_reserve_bytes'],conservatively_charged_bytes=run_bytes+cfg['external_charge_reserve_bytes'],timing_limitations='reset/core_step/emit have nested coverage; sample timer omits pre-RNG digest; environment creation/candidates/save/cleanup lack separate complete timers; do not add component timings or claim production throughput gain')
(base/'independent-final-integrity.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('phases','container_state','actor_batch_latency')},ensure_ascii=False,indent=2))
