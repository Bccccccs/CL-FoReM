#!/usr/bin/env python3
"""One fixed task10 first-action pair; plan/CPU check/host launcher/worker.

No implicit restart. A must reproduce the old run before B starts. The only
intervention is B's first action. Read STOP only at safe decision boundaries.
"""
import argparse, json, os, shlex, signal, subprocess, sys, time, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'results/task10/t10-diagnosis-20261106/first-action'
OLD=ROOT/'results/task10/t10-long-eval-20261104-s101-r2/checkpoint-010000'
WEIGHT=ROOT/'results/task10/t10-long-20261104-s101-r2/checkpoints/decision-010000.actor.pt'
LOG=ROOT/'logs/task10/t10-first-action-20261106'
MAP='standard_validation_00001'; EID=MAP+'__trained'; MAXD=300; ATOL=1e-4
sys.path.insert(0,str(ROOT/'src'))
from task10.runtime import atomic_json,atomic_torch,sha256

def select(mask,logits,arm,index):
 import torch
 from task10.validation import masked_select
 if arm not in ('A','B') or index<0:raise ValueError('invalid identity')
 original=masked_select(mask,logits=logits)
 if arm=='B' and index==0:
  if mask.shape != (1,13) or not bool(mask[0,9]):raise ValueError('forced slot9 invalid')
  return torch.full_like(original,9),original
 return original,original

def cpu_check():
 import torch
 m=torch.tensor([[False,True,False,False,False,False,False,False,False,True,False,False,True]])
 l=torch.tensor([[0.,1.,0.,0.,0.,0.,0.,0.,0.,2.,0.,0.,3.]])
 assert [int(select(m,l,a,i)[0]) for a,i in [('A',0),('B',0),('B',1),('A',1)]]==[12,9,12,12]
 m[0,9]=False
 try:select(m,l,'B',0)
 except ValueError:pass
 else:raise AssertionError('invalid force accepted')
 m[0,1]=True;m[0,12]=True;l[0,1]=l[0,12]=5
 assert int(select(m,l,'A',0)[0])==1
 out={'status':'passed','cases':['A argmax','B first valid force','B later argmax','invalid force rejected','lowest-index tie'],'gpu_used':False,'environment_steps':0,'updates':0,'script_sha256':sha256(Path(__file__))}
 atomic_json(RUN/'cpu-check.json',out);print(json.dumps(out));return 0

def plan():
 import torch
 from task10.validation import tree_hash
 p=RUN/'plan.json'
 if p.exists() or (RUN/'launch.json').exists() or (RUN/'budget.json').exists():raise RuntimeError('plan/run exists: no automatic restart')
 old=json.loads((OLD/'manifest.json').read_text());ep=json.loads((OLD/'episodes'/f'{EID}.json').read_text());rec=[json.loads(x) for x in (OLD/'decisions.jsonl').read_text().splitlines() if json.loads(x)['episode_id']==EID]
 ck=torch.load(WEIGHT,map_location='cpu',weights_only=False)
 assert (ck['format'],ck['decisions'],ck['updates'])==('task10-stage1-actor-v1',10000,9000)
 assert tree_hash(ck['model'])==old['source_checkpoint']['trained_state_sha256']==ep['weights_before']['trained']
 conf=old['config'];assert (conf['environments'],conf['scene_seed'],conf['profile'],conf['failure_mode'],conf['map_backend'],conf['physical_gpu'])==(1,101,'sync_v5','cbl_continue','primitive-obb-v1',1)
 assert conf['performance']=={'risk_chunk_size':256,'observation_chunk_size':128,'reuse_route_raster':True,'dls_cuda_graph':True}
 scene=next(s for s in old['scenes'] if s['id']==MAP); pool=Path(old['pool']);side=pool.parent/scene['sidecar_path'];assert sha256(side)==scene['sha256']['sidecar']
 assert ep['complete'] and len(rec)==ep['decisions'] and [r['decision_index'] for r in rec]==list(range(len(rec)))
 files=[Path(__file__),WEIGHT,OLD/'manifest.json',OLD/'episodes'/f'{EID}.json',OLD/'decisions.jsonl',pool,side]
 # Audit current source against original frozen source where present; omit all large assets.
 changed=[];source={}
 for name,h in old['files'].items():
  if name.startswith('/workspace/src/') and name.endswith('.py'):
   q=Path(name);actual=sha256(q) if q.exists() else None;source[name]=actual
   if actual!=h:changed.append(name)
 if changed:raise ValueError('original frozen source differs: '+str(changed))
 test=json.loads((RUN/'cpu-check.json').read_text());assert test['status']=='passed' and test['script_sha256']==sha256(Path(__file__))
 value={'schema':'task10-first-action-pair-v1','map_id':MAP,'seed':101,'arms':[{'name':'A','choice':'argmax every decision'},{'name':'B','choice':'slot9 on first decision; argmax thereafter'}], 'limits':{'episodes':2,'decisions':MAXD,'updates':0,'per_episode_native_decisions':150,'per_episode_native_attempt_seconds':200},'gpu_physical':1,'source_code_commit':old['source_code_commit'],'source_manifest':str(OLD/'manifest.json'),'pool':str(pool),'scene_sidecar_sha256':scene['sha256']['sidecar'],'model_state_sha256':tree_hash(ck['model']),'old_initial_hashes':ep['initial_hashes'],'old_episode':ep,'old_decisions':rec,'config':conf,'float_abs_tolerance':ATOL,'files':{str(x):sha256(x) for x in files},'source_files':source,'cpu_check':test,'stop':'create STOP; worker stops at next safe boundary; no automatic resume','conditions':'A must match old selected sequence, native terminal flags, counts, route/time/base/q within absolute tolerance before B'}
 atomic_json(p,value);print(json.dumps({'status':'planned','plan':str(p),'old_actions':[r['selected'] for r in rec],'source_files':len(source),'plan_sha256':sha256(p)}));return 0

def host_gpu_free():
 f=subprocess.run(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=5)
 rows=[x.strip().split(', ') for x in f.stdout.splitlines()];row=next(r for r in rows if r[0]=='1')
 q=subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
 if q.returncode!=0:raise RuntimeError('cannot check active compute processes')
 if int(row[2])>256 or int(row[3])!=0 or any(x.strip().startswith(row[1]+',') for x in q.stdout.splitlines()):raise RuntimeError('physical GPU1 busy')
 return {'index':1,'uuid':row[1],'memory_used_mib':int(row[2]),'utilization_percent':int(row[3]),'compute_processes':q.stdout.strip()}

def launcher():
 # Host process is intended to be started with nohup; it waits for worker and persists exit.
 planpath=RUN/'plan.json';value=json.loads(planpath.read_text());gpu=host_gpu_free();LOG.mkdir(parents=True,exist_ok=True)
 inspect=subprocess.run(['sg','docker','-c',"docker inspect forem-task10-runtime --format '{{json .HostConfig.DeviceRequests}}'"],capture_output=True,text=True,check=True,timeout=10)
 requests=json.loads(inspect.stdout.strip());assert len(requests)==1 and requests[0]['DeviceIDs']==['1']
 if (RUN/'budget.json').exists() or (RUN/'STOP').exists():raise RuntimeError('budget or STOP exists')
 script='/workspace/scripts/task10_first_action_probe.py';cmd=['docker','exec','--user','1004:1004','-e','PYTHONPATH=/workspace/src','-e','CUBLAS_WORKSPACE_CONFIG=:4096:8','-e','TASK10_PHYSICAL_GPU=1','forem-task10-runtime','python3','-u',script,'worker']
 command=['sg','docker','-c',shlex.join(cmd)];start=time.time();info={'status':'launching','pid':os.getpid(),'started_epoch':start,'gpu_check':gpu,'device_requests':requests,'command':command,'plan_sha256':sha256(planpath),'log':str(LOG/'worker.log')}
 with (RUN/'launch.json').open('x') as f:json.dump(info,f,indent=2);f.flush();os.fsync(f.fileno())
 rc=1
 try:
  with (LOG/'worker.log').open('x') as f:
   proc=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);info.update(status='running',client_pid=proc.pid);atomic_json(RUN/'launch.json',info);rc=proc.wait()
 finally:
  info.update(status='exited',returncode=rc,finished_epoch=time.time());atomic_json(RUN/'launch.json',info)
  if not (RUN/'worker-exit.json').exists():
   atomic_json(RUN/'worker-exit.json',{'status':'failed','error':'worker exited without final record','launcher_returncode':rc})
   append_result('failed','worker exited without final record; inspect launcher and logs')
 return rc

def append_result(status,detail):
 path=ROOT/'doc/tasks/task10/task10.18/task10.18.4/RESULTS.md'
 with path.open('a') as f:
  f.write('\n## 自动运行交接\n\n状态：'+status+'。'+detail+'\n\n详细账本、每步原件、summary 和 worker-exit：`forem/results/task10/t10-diagnosis-20261106/first-action/`；日志：`forem/logs/task10/t10-first-action-20261106/worker.log`。无训练更新。\n');f.flush();os.fsync(f.fileno())

def differences(actual,expected):
 exact=('strict_success','failures','stalls','decisions','terminated','truncated','attempted_substeps','committed_substeps','failure_limit','triggers')
 floats=('attempted_seconds','committed_seconds','route_s','route_length','final_base','final_q')
 d={k:{'actual':actual.get(k),'expected':expected.get(k)} for k in exact if actual.get(k)!=expected.get(k)}
 for k in floats:
  a=actual[k] if isinstance(actual[k],list) else [actual[k]];b=expected[k] if isinstance(expected[k],list) else [expected[k]]
  if len(a)!=len(b) or any(abs(float(x)-float(y))>ATOL for x,y in zip(a,b)):d[k]={'actual':actual[k],'expected':expected[k],'atol':ATOL}
 return d

def worker():
 import torch
 from task10.validation import tree_hash,initial_snapshot,core_record,terminal_reason,plain,append
 from task10.entry import initialize_determinism
 from task10.environment import Task10Env
 from task10.lower import FrozenB3
 from task7_upper.model import UpperModel
 from task7_upper.stages import environment_inputs
 from task7_upper.replay import exact_cpu
 from task10.runner import check_finite,tensor_state_hash
 plan=json.loads((RUN/'plan.json').read_text());start=time.monotonic();deadline=start+5400; budget={'status':'active','pid':os.getpid(),'started_epoch':time.time(),'max_decisions':MAXD,'max_episodes':2,'max_updates':0,'reserved':0,'completed':0,'in_flight':None,'episodes_started':0,'episodes_completed':0}
 if (RUN/'budget.json').exists():raise RuntimeError('existing ledger; no resume')
 def flush():budget['elapsed_seconds']=time.monotonic()-start;atomic_json(RUN/'budget.json',budget)
 def guard():
  if (RUN/'STOP').exists():raise InterruptedError('STOP at safe boundary')
  if time.monotonic()>=deadline-20:raise TimeoutError('5400s engineering ceiling')
  if budget['reserved']>=MAXD:raise RuntimeError('decision cap')
 def sig(signum,frame):raise InterruptedError('external signal')
 signal.signal(signal.SIGTERM,sig);signal.signal(signal.SIGINT,sig)
 flush();status='failed';error=None;arms={};model=None;policy=None;current=None
 try:
  if os.environ.get('TASK10_PHYSICAL_GPU')!='1':raise RuntimeError('GPU1 identity absent')
  for p,h in {**plan['files'],**plan['source_files']}.items():
   if sha256(p)!=h:raise RuntimeError('frozen input changed: '+p)
  settings=initialize_determinism(101);ck=torch.load(WEIGHT,map_location='cpu',weights_only=False)
  with torch.random.fork_rng(devices=[]):model=UpperModel(vector_dim=ck['vector_dim'])
  model.load_state_dict(ck['model'],strict=True);model.to('cuda:0').eval().requires_grad_(False)
  if tree_hash(model.state_dict())!=plan['model_state_sha256']:raise AssertionError('actor model hash mismatch')
  policy=FrozenB3(device='cuda:0',artifact_root='/reference',source_root='/reference/source');initial_weights={'model':tree_hash(model.state_dict()),'lower':tensor_state_hash(policy.actor)}
  if initial_weights['lower']!=plan['old_episode']['weights_before']['lower']:raise AssertionError('lower actor differs')
  atomic_json(RUN/'entry.json',{'runtime':settings,'weights':initial_weights,'pid':os.getpid(),'config':plan['config']})
  for arm in ('A','B'):
   guard();budget['episodes_started']+=1;flush();current={'arm':arm,'complete':False,'decisions':0};atomic_json(RUN/f'episode-{arm}.json',current)
   env=Task10Env(1,policy,seed=101,pool=plan['pool'],split='validation',device='cuda:0',run_id=RUN.name,code_commit=plan['source_code_commit'],config_hash=sha256(RUN/'plan.json'),risk_chunk_size=256,observation_chunk_size=128,reuse_route_raster=True)
   env.episodes.kin.dls_cuda_graph=True;model.vcm.reset();env.reset(map_ids=[MAP],deadline=deadline-20)
   snapshot=initial_snapshot(env,plan['scene_sidecar_sha256']);atomic_torch(RUN/f'initial-{arm}.pt',snapshot);hashes={k:tree_hash(v) for k,v in snapshot.items()};current['initial_hashes']=hashes;atomic_json(RUN/f'episode-{arm}.json',current)
   diff={k:{'actual':hashes.get(k),'expected':v} for k,v in plan['old_initial_hashes'].items() if hashes.get(k)!=v}
   if diff:atomic_json(RUN/f'initial-difference-{arm}.json',diff);raise RuntimeError('initial typed hashes differ; no decisions')
   while True:
    guard();mask=env.candidates['mask'];check_finite(env.observation);check_finite(env.candidates)
    with torch.no_grad():
     item=environment_inputs(env.observation,env.candidates,env_ids=[0],asynchronous=False,device='cuda:0');out=model.forward_step(**item);selected,unforced=select(mask,out['logits'],arm,current['decisions'])
    i=current['decisions'];choice=int(selected[0]);valid=mask[0];scores={k:[float(out[k][0,j]) if bool(valid[j]) else None for j in range(len(valid))] for k in ('logits','q1','q2')}
    intent={'arm':arm,'decision_index':i,'selected':choice,'unforced_argmax':int(unforced[0]),'mask':plain(valid),'scores':scores}
    atomic_json(RUN/'intent.json',intent)
    if arm=='A' and (i>=len(plan['old_decisions']) or choice!=plan['old_decisions'][i]['selected']):
     atomic_json(RUN/'A-divergence.json',{'reason':'action','current':intent,'old':plan['old_decisions'][i] if i<len(plan['old_decisions']) else None});raise RuntimeError('A action diverged; B prohibited')
    budget['reserved']+=1;budget['in_flight']={'arm':arm,'decision_index':i};flush();t=time.monotonic();result=env.step(selected,deadline=deadline-20)
    rawpath=RUN/'decisions'/f'{arm}-{i:04d}.pt';atomic_torch(rawpath,{'intent':intent,'fields':exact_cpu(result.replay_fields),'attempts':exact_cpu(env.episodes.core.attempts)})
    record=core_record(env.episodes.core,result.info['triggers']);entry={**intent,'core':record,'r_t':result.info['r_t'],'actual_result_v1':result.info['actual_result_v1'],'timing':result.info['timing'],'execution_wall_seconds':time.monotonic()-t,'reward':plain(result.replay_fields['reward']),'raw_path':str(rawpath),'raw_sha256':sha256(rawpath)}
    append(RUN/'decisions.jsonl',entry);budget['completed']+=1;budget['in_flight']=None;flush();current.update(record);atomic_json(RUN/f'episode-{arm}.json',current)
    if arm=='A':
     delta=differences(record,plan['old_decisions'][i]['core'])
     if delta:atomic_json(RUN/'A-divergence.json',{'reason':'step execution','decision_index':i,'differences':delta});raise RuntimeError('A execution diverged; B prohibited')
    if record['terminated'] or record['truncated']:
     current.update(complete=True,reason=terminal_reason(record));break
    guard();env.prepare_next(result,deadline=deadline-20)
   if arm=='A':
    delta=differences(current,plan['old_episode'])
    if len(plan['old_decisions'])!=current['decisions'] or current['reason']!=plan['old_episode']['reason'] or delta:
     atomic_json(RUN/'A-divergence.json',{'reason':'terminal','differences':delta,'actual_reason':current['reason'],'old_reason':plan['old_episode']['reason']});raise RuntimeError('A terminal diverged; B prohibited')
    atomic_json(RUN/'A-reproduced.json',{'status':'passed','decisions':current['decisions'],'float_abs_tolerance':ATOL,'initial_hashes_match':True})
   after={'model':tree_hash(model.state_dict()),'lower':tensor_state_hash(policy.actor)}
   if after!=initial_weights:raise RuntimeError('weights changed')
   current['weights_after']=after;atomic_json(RUN/f'episode-{arm}.json',current);arms[arm]=current;budget['episodes_completed']+=1;flush();current=None
  status='complete'
 except InterruptedError as e:status='partial';error=repr(e)
 except Exception as e:status='failed';error=repr(e);traceback.print_exc()
 finally:
  budget.update(status=status,error=error);flush();summary={'status':status,'error':error,'arms':arms,'budget':budget,'plan_sha256':sha256(RUN/'plan.json'),'updates':0,'limitations':['single map and seed; one first-action intervention; no strategy or generalization claim','STOP only at safe boundary; no exact resume']};atomic_json(RUN/'summary.json',summary);atomic_json(RUN/'worker-exit.json',{'status':status,'error':error,'exit_code':0 if status=='complete' else 1});append_result(status,('A: '+str(arms.get('A'))+'; B: '+str(arms.get('B'))) if status=='complete' else str(error));print(json.dumps({'status':status,'error':error,'completed_decisions':budget['completed']}),flush=True)
 return 0 if status=='complete' else 1

def main():
 parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('cpu-check','plan','launch','worker'));args=parser.parse_args();RUN.mkdir(parents=True,exist_ok=True)
 return {'cpu-check':cpu_check,'plan':plan,'launch':launcher,'worker':worker}[args.phase]()
if __name__=='__main__':raise SystemExit(main())
