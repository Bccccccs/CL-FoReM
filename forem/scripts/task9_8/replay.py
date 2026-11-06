"""B-only observer around frozen full evaluate; never runs training or retries."""
import argparse, csv, hashlib, inspect, json, os, signal, sys, textwrap, time, traceback
from pathlib import Path
import torch
from analysis import compare, coverage

ROOT=Path('/root/mm_husky_ws')
OUT=Path('/output')
KEY=('map_id','seed','stream_index','role','source_split','proposal_seed')

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()

def dump(path,obj):
 text=json.dumps(obj,ensure_ascii=False,allow_nan=False,indent=2)+'\n'
 tmp=Path(str(path)+'.tmp');tmp.write_text(text);os.replace(tmp,path)

def convert(v):
 if torch.is_tensor(v):return v.detach().cpu().tolist()
 if isinstance(v,dict):return {k:convert(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [convert(x) for x in v]
 return v

class Observer:
 def __init__(self,args,rows,output):
  self.args=args;self.output=output;self.rows=rows;self.counter={};self.current={};self.files={};self.off={};self.events={};self.last_guard=0;self.started=0;self.completed=0;self.cores=[]
  self.selected={}
  for r in rows:
   if int(r['training_seed'])!=args.seed:continue
   isgate=int(r['case_no']) in (1,3)
   if args.phase in ('off','gate') and not isgate:continue
   if args.phase=='remaining' and isgate:continue
   self.selected[(r['map_id'],int(r['seed']))]=r
  assert len(self.selected)==(2 if args.phase in ('off','gate') else 8 if args.phase=='remaining' else 10)
 def guard(self):
  now=time.time()
  if now>self.args.deadline_epoch-self.args.config['drain_seconds']:raise TimeoutError('configured drain reserve reached')
  if (OUT/'STOP').exists():raise InterruptedError('STOP requested')
  if now-self.last_guard<5:return
  self.last_guard=now
  size=sum(p.stat().st_size for root in (OUT,Path('/runlogs')) for p in root.rglob('*') if p.is_file())
  if size+self.args.config['prior_output_bytes']+self.args.config['external_charge_reserve_bytes']>1024**3-16*1024**2:raise OSError('output budget drain reserve reached')
  dump(self.output/'progress.json',dict(epoch=now,started=self.started,completed=self.completed,events=self.events,output_bytes=size))
 def emit(self,c,i,event,detail=None):
  r=c._diag_targets[i];case=r['case_no'];event=dict(event,case_no=int(case),training_seed=self.args.seed)
  # Comparison also validates finite values before any write.
  d=compare(event,event)
  if d:raise FloatingPointError(str(d))
  if case not in self.files:self.files[case]=(self.output/f'case{int(case):02d}.jsonl').open('x',buffering=1)
  record=event if self.args.phase=='off' else dict(comparison=event,detail=detail or {})
  self.files[case].write(json.dumps(record,allow_nan=False,separators=(',',':'))+'\n')
  self.events[case]=self.events.get(case,0)+1
 def state(self,c,i):return convert(dict(base=c.state.base[i],q=c.state.q[i],s=c.state.s[i]))
 def target(self,c,i):return convert(dict(pose=c.candidate.pose[i],inplace=c.candidate.inplace[i],cap=c.cap[i],progress=c.candidate.progress[i]))
 def substep(self,c,loc):
  if not hasattr(c,'_diag_targets'):return
  self.guard()
  for i in c._diag_targets:
   if not bool(loc['pending'][i]):continue
   e=dict(event='substep',segment=c._diag_segments[i],action=c._diag_actions[i],substep=loc['_'],raw_action=convert(loc['raw'][i]),execution_action=convert([loc['u'][i],loc['w'][i],loc['v'][i]]),pending=bool(loc['pending'][i]),ik_accepted=bool(loc['ik'].accepted[i]),failed=bool(loc['failed'][i]),failure_kind=int(loc['kind'][i]),commit=bool(loc['commit'][i]),state=self.state(c,i),target=self.target(c,i),arrived=bool(c.arrived[i]),route_end=bool(loc['route_end'][i]),reason=int(c.reason[i]),done=bool(c.done[i]))
   detail={}
   if self.args.phase!='off':
    ik=loc['ik'];coll=loc['coll']
    detail=convert(dict(trial_base=loc['trialbase'][i],trial_s=loc['trials'][i],returned_ik_q_may_be_held=ik.q[i],ik_position_m=ik.position[i],ik_cbl=ik.cbl[i],ik_angle_rad=ik.angle[i],ik_status=ik.status[i],ik_branch=ik.branch[i],failure_kind=loc['kind'][i],base_collision=coll.base[i],arm_collision=coll.arm[i],self_collision=coll.self_collision[i],previous_q=c.attempts[-1]['previous_q'][i],joint_delta=c.attempts[-1]['joint_delta'][i],attempted_segment=c.attempted_segment[i],segment_committed_substeps=c.segment_substeps[i],object_id=None,geometry_witness=None,raw_rejected_ik_solution=None,concurrent_cause='unknown_if_masked_by_ik_or_priority'))
   self.emit(c,i,e,detail)
 def begin(self,c,candidate,mask,original):
  chosen=convert(c._mask(mask)) if hasattr(c,'_diag_targets') else []
  previous={i:self.state(c,i) for i in getattr(c,'_diag_targets',{}) if chosen[i]}
  result=original(c,candidate,mask)
  if hasattr(c,'_diag_targets'):
   for i,done in enumerate((c.terminated|c.truncated).detach().cpu().tolist()):
    if done and i not in c._diag_completed_rows:
     c._diag_completed_rows.add(i);self.completed+=1
  if hasattr(c,'_diag_targets'):
   for i in c._diag_targets:
    if not chosen[i]:continue
    c._diag_segments[i]+=1
    self.emit(c,i,dict(event='begin',segment=c._diag_segments[i],action=c._diag_actions[i],target=self.target(c,i),state=self.state(c,i),arrived=bool(c.arrived[i]),reason=int(c.reason[i]),done=bool(c.done[i]),terminated=bool(c.terminated[i]),truncated=bool(c.truncated[i]),strict_success=bool(c.strict_success[i]),failures=int(c.failures[i])),dict(previous_state=previous[i],slot=c._diag_slots.get(i)))
  return result
 def step(self,c,raw,original):
  if hasattr(c,'_diag_targets'):
   self.guard()
   for i in c._diag_targets:
    if not bool(c.done[i]):
     c._diag_actions[i]+=1
     self.emit(c,i,dict(event='action_start',segment=c._diag_segments[i],action=c._diag_actions[i],state=self.state(c,i),target=self.target(c,i),raw_action=convert(raw[i])))
  result=original(c,raw)
  if hasattr(c,'_diag_targets'):
   ended=(c.terminated|c.truncated).detach().cpu().tolist()
   for i,done in enumerate(ended):
    if done and i not in c._diag_completed_rows:
     c._diag_completed_rows.add(i);self.completed+=1
  if hasattr(c,'_diag_targets'):
   for i in c._diag_targets:
    if bool(result.active[i]):
     self.emit(c,i,dict(event='action_end',segment=c._diag_segments[i],action=c._diag_actions[i],state=self.state(c,i),target=self.target(c,i),reason=int(c.reason[i]),done=bool(c.done[i]),terminated=bool(c.terminated[i]),truncated=bool(c.truncated[i]),strict_success=bool(c.strict_success[i]),failures=int(c.failures[i]),arrived=bool(c.arrived[i]),attempted=int(result.attempted[i]),committed=int(result.committed[i])))
  return result
 def attach(self,env,jobs,original_reset,*a,**kw):
  self.guard();self.started+=len(jobs)
  with (self.output/'episodes-started.jsonl').open('a') as f:f.write(json.dumps(dict(epoch=time.time(),count=len(jobs),jobs=[{k:v for k,v in j.items() if k!='entry'} for j in jobs]))+'\n')
  assert self.started<=196
  result=original_reset(*a,**kw);c=env.core
  c._diag_targets={i:self.selected[(j['map_id'],j['seed'])] for i,j in enumerate(jobs) if (j['map_id'],j['seed']) in self.selected}
  c._diag_completed_rows=set()
  c._diag_segments={i:0 for i in c._diag_targets};c._diag_actions={i:0 for i in c._diag_targets};c._diag_slots={}
  for i,r in c._diag_targets.items():
   j=jobs[i]
   for k in ('map_id','seed','stream_index','role','source_split'):
    assert str(j[k])==r[k],(k,j,r)
   assert str(env.proposal_seeds[i])==r['proposal_seed']
   self.emit(c,i,dict(event='reset',case_key={k:r[k] for k in KEY},batch_jobs=[{k:v for k,v in j.items() if k!='entry'} for j in jobs],batch_local_index=i,state=self.state(c,i)),dict(route_xyz=convert(c.route.xyz[i]),route_length=convert(c.route.length[i]),map_provenance=env.scenes.provenance() if hasattr(env.scenes,'provenance') else None))
  self.cores.append((c,jobs))
  return result
 def choice(self,env,ids,slots):
  c=env.core
  if hasattr(c,'_diag_targets'):
   for i,s in zip(ids.tolist(),slots.tolist()):c._diag_slots[i]=s
 def finish(self,result):
  target_rows={}
  for c,jobs in self.cores:
   assert len(c._diag_completed_rows)==len(jobs)
   for i,r in c._diag_targets.items():
    name='validation' if r['role']=='validation' else 'transfer'
    row=next(x for x in result[name]['rows'] if x['map_id']==r['map_id'] and str(x['seed'])==r['seed'])
    self.emit(c,i,dict(event='final',state=self.state(c,i),outcome=row))
    target_rows[r['case_no']]=row
  for f in self.files.values():f.close()
  reports={};current_events={}
  for case,row in target_rows.items():
   path=self.output/f'case{int(case):02d}.jsonl'
   events=[json.loads(line) for line in path.open()]
   current_events[case]=events
   reports[case]=coverage(events,row)
  dump(self.output/'coverage.json',reports)
  bad={k:v for k,v in reports.items() if not v['complete']}
  if bad:
   dump(self.output/'first-difference.json',dict(cause='incomplete_current_trace',cases=bad))
   raise RuntimeError('trace coverage failed')
  if self.args.phase=='gate':
   off_eval=json.loads((OUT/'01-4718-off/evaluation.json').read_text())
   off_reports={};off_events={}
   for case,row in target_rows.items():
    oldrow=next(x for name in ('validation','transfer') for x in off_eval[name]['rows'] if all(str(x[k])==str(row[k]) for k in KEY))
    old=[json.loads(line) for line in (OUT/'01-4718-off'/f'case{int(case):02d}.jsonl').open()]
    off_events[case]=old;off_reports[case]=coverage(old,oldrow)
   dump(self.output/'gate-independent-coverage.json',dict(off=off_reports,on=reports))
   bad={k:v for k,v in off_reports.items() if not v['complete']}
   if bad:
    dump(self.output/'first-difference.json',dict(cause='incomplete_OFF_trace',cases=bad))
    raise RuntimeError('OFF coverage failed; comparison forbidden')
   comparisons={}
   for case in target_rows:
    old=off_events[case];new=[e['comparison'] for e in current_events[case]]
    difference=compare(old,new)
    comparisons[case]=dict(status='FAIL' if difference else 'PASS',events_off=len(old),events_on=len(new),difference=difference)
    if difference:
     dump(self.output/'first-difference.json',dict(case_no=case,cause='exact_value_mismatch',difference=difference))
     dump(self.output/'gate-comparison.json',comparisons)
     raise RuntimeError('OFF/ON exact value comparison failed')
   dump(self.output/'gate-comparison.json',comparisons)
   dump(self.output/'gate.json',dict(status='PASS',comparison='independently complete; all finite values exact; no tolerance',cases=sorted(target_rows),event_counts=self.events))
  self.guard()

def install(observer):
 import task7_sim.core as core
 import task7_lower.training as training
 import task8_lower.evaluation as evaluation
 original_begin=core.Core.begin;source=textwrap.dedent(inspect.getsource(core.Core.step))
 marker='        self.reason=torch.where(ended,reason,self.reason);self.done|=ended\n'
 assert source.count(marker)==1
 source=source.replace(marker,marker+'        _diag_substep(self,locals())\n')
 namespace=dict(vars(core),_diag_substep=observer.substep);exec(compile(source,'<B diagnostic Core.step>','exec'),namespace)
 diagnostic_step=namespace['step']
 core.Core.begin=lambda c,candidate,mask=None:observer.begin(c,candidate,mask,original_begin)
 core.Core.step=lambda c,raw:observer.step(c,raw,diagnostic_step)
 choice_source=textwrap.dedent(inspect.getsource(training.choose_candidate.__wrapped__))
 marker='    env.begin(Candidate(pose,progress,inplace),mask)\n';assert choice_source.count(marker)==1
 choice_source=choice_source.replace(marker,'    _diag_choice(env,ids,slots)\n'+marker)
 ns=dict(vars(training),_diag_choice=observer.choice);exec(compile(choice_source,'<B diagnostic choose_candidate>','exec'),ns)
 evaluation.choose_candidate=ns['choose_candidate']
 original_environment=evaluation.evaluation_environment
 def environment(jobs,*a,**kw):
  env=original_environment(jobs,*a,**kw);original_reset=env.reset
  env.reset=lambda *a,**kw:observer.attach(env,jobs,original_reset,*a,**kw)
  return env
 evaluation.evaluation_environment=environment
 (observer.output/'instrumented-core-step.py').write_text(source)
 (observer.output/'instrumented-choose-candidate.py').write_text(choice_source)
 return evaluation

def import_check(args):
 print(json.dumps(dict(event='zero_import_context',uid=os.getuid(),cwd=os.getcwd(),sys_path=sys.path,pythonpath=os.environ.get('PYTHONPATH'),root_access=os.access('/root',os.X_OK),project_access=os.access('/root/mm_husky_ws/src/task7_sim',os.R_OK))),flush=True)
 import queue
 from queue import Queue
 import task7_sim.core, task7_lower.training, task8_lower.evaluation
 import task8_sim.env, task8_sim.episode, task8_sim.primitive_scene
 import task8_lower.sac, task7_lower.inference
 import supervisor
 import tempfile
 with tempfile.TemporaryDirectory(prefix='b-zero-',dir=os.environ['TMPDIR']) as directory:
  probe=Path(directory)/'write-read-check';probe.write_bytes(b'B-zero');assert probe.read_bytes()==b'B-zero'
 assert Path(tempfile.gettempdir())==OUT/'tmp'
 import torch._dynamo
 import torch.distributed.nn.jit.instantiator
 assert Queue.__module__=='queue'
 assert '/workspace/scripts/' not in queue.__file__
 assert not Path(__file__).with_name('queue.py').exists()
 assert args.config['run_id']==Path(args.config['output_root']).name
 assert OUT==Path('/output')
 assert args.config['deadline_epoch']==1793617320.0
 result=dict(status='PASS',zero_episodes=True,models_loaded=False,environment_reset=False,evaluate_called=False,queue_file=queue.__file__,temporary_directory=tempfile.gettempdir(),temporary_write_read_delete_passed=True,optimizer_dynamic_imports_passed=True,torch_version=torch.__version__,replay_file=__file__,supervisor_file=supervisor.__file__,sys_path=sys.path,cwd=os.getcwd(),python=sys.version,image=args.config['image'],run_id=args.config['run_id'],argv=sys.argv,modules={name:getattr(sys.modules[name],'__file__',None) for name in ('queue','torch','task7_sim.core','task7_lower.training','task8_lower.evaluation','task8_sim.env','task8_sim.episode','task8_sim.primitive_scene','task8_lower.sac','task7_lower.inference')})
 dump(OUT/'zero-import-check.json',result)
 print(json.dumps(result),flush=True)
 return 0

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int);parser.add_argument('--phase',choices=('off','gate','remaining','all'));parser.add_argument('--name');parser.add_argument('--run-config',required=True);parser.add_argument('--import-check',action='store_true');args=parser.parse_args()
 global OUT
 args.config=json.loads(Path(args.run_config).read_text());OUT=Path(args.run_config).resolve().parent
 args.deadline_epoch=args.config['deadline_epoch']
 if args.import_check:return import_check(args)
 assert args.seed and args.phase and args.name
 output=OUT/args.name;output.mkdir(exist_ok=False)
 started=time.time();observer=None
 def stop(signum,frame):raise InterruptedError(f'signal {signum}')
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 torch.set_num_threads(2)
 try:
  with Path('/workspace/doc/agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.csv').open() as f:rows=list(csv.DictReader(f))
  assert torch.cuda.device_count()==1
  from task8_lower.sac import LowerSAC
  from task7_lower.inference import DeterministicActor
  run=ROOT/f'results/task9/t9-stage2-20261029/B3_5M-seed{args.seed}'
  cfg=json.loads((run/'config.json').read_text());assert cfg['seed']==args.seed
  ck=torch.load(run/'final.pt',map_location='cpu',weights_only=False,mmap=True)
  assert ck['state']['steps']==5000000 and ck['config']==cfg
  sac=LowerSAC(74,'cuda',cfg);sac.policy.load_state_dict(ck['sac']['policy']);sac.critic.load_state_dict(ck['sac']['critic']);sac.env_steps=ck['state']['steps']
  actor=DeterministicActor(run/'final.actor.pt','cuda');assert actor.synchronous and actor.steps==sac.env_steps
  assert all(torch.equal(v,actor.policy.state_dict()[k]) for k,v in sac.policy.state_dict().items())
  del ck,actor
  dump(output/'loaded.json',dict(seed=args.seed,checkpoint=str(run/'final.pt'),steps=sac.env_steps,policy_device=str(next(sac.policy.parameters()).device),critic_device=str(next(sac.critic.parameters()).device),actor_tensors_equal=True,config_sha256=sha(run/'config.json'),actor_sha256=sha(run/'final.actor.pt'),evaluation_sha256=sha(ROOT/'src/task8_lower/evaluation.py'),core_sha256=sha(ROOT/'src/task7_sim/core.py'),script_sha256=sha(__file__),torch=torch.__version__,threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads(),affinity=sorted(os.sched_getaffinity(0)),tf32_matmul=torch.backends.cuda.matmul.allow_tf32,tf32_cudnn=torch.backends.cudnn.allow_tf32,device_name=torch.cuda.get_device_name(),cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),nvidia_visible_devices=os.environ.get('NVIDIA_VISIBLE_DEVICES')))
  print(json.dumps(dict(event='loaded',phase=args.phase,seed=args.seed,epoch=time.time())),flush=True)
  observer=Observer(args,rows,output);evaluation=install(observer)
  deadline=time.monotonic()+args.deadline_epoch-time.time()-args.config['drain_seconds']
  result=evaluation.evaluate(sac,cfg,output/'evaluation.json',deadline=deadline,cancel=lambda:(OUT/'STOP').exists())
  assert result['complete'] and len(result['validation']['rows'])==100 and len(result['transfer']['rows'])==96
  observer.finish(result)
  dump(output/'status.json',dict(status='done',exit_code=0,started_epoch=started,end_epoch=time.time(),wall_s=time.time()-started,started_episodes=observer.started,completed_episodes=observer.completed,events=observer.events))
  print(json.dumps(dict(event='done',phase=args.phase,seed=args.seed,wall_s=time.time()-started)),flush=True)
 except BaseException as ex:
  dump(output/'status.json',dict(status='failed',exit_code=1,started_epoch=started,end_epoch=time.time(),wall_s=time.time()-started,error=repr(ex),started_episodes=observer.started if observer else 0,completed_episodes=observer.completed if observer else 0))
  traceback.print_exc();raise

if __name__=='__main__':main()
