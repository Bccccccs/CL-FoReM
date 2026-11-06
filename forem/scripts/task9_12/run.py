"""Isolated fixed-policy BioIK comparison. No training and no reference writes."""
import sys,os,time,json,gzip,hashlib,signal,argparse,traceback
from pathlib import Path
import numpy as np,torch
sys.path[:0]=['/workspace/src','/work/src']
from task9_lr.runtime import activate
activate()
from task9_lr.diagnostics import observing,plain
from task7_sim.kinematics import Kinematics,base_transform,metrics,LOW,HIGH
from task7_lower.inference import DeterministicActor
from task7_lower.training import choose_candidate,drain_history
from task8_lower.evaluation import evaluation_plan,evaluation_environment
from backend import Bridge,BioKinematics
OUT=Path('/output');CONFIG=Path('/work/config');RUN='/history/results/task9/t9-stage2-20261029'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
 p=Path(p);tmp=Path(str(p)+'.tmp');tmp.write_text(json.dumps(plain(x),indent=2,allow_nan=False)+'\n');os.replace(tmp,p)
def check():
 if (OUT/'STOP').exists():raise InterruptedError('task9.12 STOP requested; current partial batch retained, no automatic skipped episodes')
def load_config(seed):
 p=Path(RUN)/f'B3_5M-seed{seed}';cfg=json.loads((p/'config.json').read_text())
 for key in ('pool','transfer_pool','evaluation_seeds'):cfg[key]=cfg[key].replace('/root/mm_husky_ws','/history')
 return cfg,p

def prepare():
 jobs=[];identities=[]
 for seed in (4718,4719,4720):
  cfg,p=load_config(seed);cube=json.loads(Path(cfg['pool']).read_text());sem=json.loads(Path(cfg['transfer_pool']).read_text());val,transfer=evaluation_plan(cube,sem,cfg)
  assert len(val)==100 and len(transfer)==96
  identities.append(dict(training_seed=seed,actor=str(p/'final.actor.pt'),actor_sha256=sha(p/'final.actor.pt'),config=str(p/'config.json'),config_sha256=sha(p/'config.json'),evaluation_seeds=cfg['evaluation_seeds'],seeds_sha256=sha(cfg['evaluation_seeds'])))
  for domain,js,pool in [('random',val,cfg['pool']),('semantic',transfer,cfg['transfer_pool'])]:
   for i,j in enumerate(js):jobs.append(dict(training_seed=seed,domain=domain,domain_index=i,pool=pool,**j))
 manifest=dict(schema='task9.12-fixed-b3-development-v1',jobs=jobs,models=identities,episode_count=588,counts={'random':300,'semantic':288},dev_repeated=True,smoke='seed4718 first8 per domain; separate counted',selection='original evaluation_plan order; no outcome-based selection',created_epoch=time.time())
 target=CONFIG/'development-manifest.json'
 if target.exists():
  old=json.loads(target.read_text());assert old['jobs']==jobs and old['models']==identities
 else:dump(target,manifest)
 return json.loads(target.read_text())

class Recorder:
 def __init__(self,path,arm,seed,env,jobs):
  self.path=Path(path);self.arm=arm;self.seed=seed;self.env=env;self.jobs=jobs;self.action=[0]*len(jobs);self.segment=[0]*len(jobs);self.raw=None;self.phase='idle'
  self.first={};self.finishes={};self.finish_history=[];self.request_count=0;self.stream=gzip.open(self.path/'requests.jsonl.gz','wt',compresslevel=1);self.timing=[];self.inference=[];self.noop=0;self.all_fail={k:0 for k in ('ik','base','arm','self')}
 def __getattr__(self,name):return lambda *a,**kw:None
 def candidates_before(self,*a):pass
 def candidates_after(self,*a):pass
 def begin_before(self,c,candidate,mask):
  for i in c._mask(mask).nonzero().flatten().tolist():self.segment[i]+=1
 def begin_after(self,c):pass
 def policy_input(self,*args):pass
 def step_start(self,c,obs,raw,u,w,v):
  self.phase='step';self.raw=None
  for i in (~c.done).nonzero().flatten().tolist():self.action[i]+=1
 def ik_pre_hold(self,kin,q,r,prev):
  if self.phase=='step':self.raw={name:x.detach().clone() for name,x in dict(q=q,accepted=r.accepted,position=r.position,cbl=r.cbl,angle=r.angle,status=r.status,branch=r.branch).items()}
 def substep(self,c,loc):
  check();ids=loc['pending'].nonzero().flatten().tolist()
  if not ids:return
  arm=torch.linalg.solve(base_transform(loc['trialbase'])@c.kin.fixed('mount',c.state.q),loc['target_tcp'])
  values=plain(dict(q_seed=c.state.q,base_before=c.state.base,base_trial=loc['trialbase'],target_world=loc['target_tcp'],target_arm_tcp=arm,target_arm_tool=arm@c.kin.fixed('tool_tcp_inverse',c.state.q),raw=self.raw,held_q=loc['ik'].q,ik_accepted=loc['ik'].accepted,kind=loc['kind'],failed=loc['failed'],commit=loc['commit'],base_collision=loc['coll'].base,arm_collision=loc['coll'].arm,self_collision=loc['coll'].self_collision,raw_action=loc['raw'],u=loc['u'],omega=loc['w'],v=loc['v'],failures=c.failures,candidate_pose=c.candidate.pose,candidate_inplace=c.candidate.inplace,candidate_progress=c.candidate.progress,s=c.state.s,trials=loc['trials']))
  meta=c.kin.last_meta if isinstance(c.kin,BioKinematics) else None
  for i in ids:
   j=self.jobs[i];case_id=f"{self.seed}/{j['domain']}/{j['domain_index']:03d}/{self.action[i]:05d}/{loc['_']}"
   row=dict(case_id=case_id,training_seed=self.seed,domain=j['domain'],domain_index=j['domain_index'],map_id=j['map_id'],episode_seed=j['seed'],stream_index=j['stream_index'],source_split=j['source_split'],proposal_seed=self.env.proposal_seeds[i],pool=j['pool'],request_id=self.request_count,step_id=self.action[i],segment=self.segment[i],substep=loc['_'],backend=self.arm,pre_failure_count=values['failures'][i],joint_low=LOW.tolist(),joint_high=HIGH.tolist(),dtype=str(c.state.q.dtype),robot_model='runtime/config/task7/model.urdf',robot_geometry='selfcoll-multisphere-v4-spherepairs-20261021',environment_geometry='primitive-obb-v1',collision_pair='unknown: original boolean API has no witness',ik_batch_wall_s=self.last_ik_wall,ik_batch_count=len(c.state.q),**{k:(None if v is None else {n:z[i] for n,z in v.items()} if k=='raw' else v[i]) for k,v in values.items() if k!='failures'},solver=None if meta is None else meta[i])
   if row['failed'] and i not in self.first:self.first[i]=row
   self.stream.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n');self.request_count+=1
   for name,key in [('ik','ik_accepted'),('base','base_collision'),('arm','arm_collision'),('self','self_collision')]:self.all_fail[name]+=int((not row[key]) if name=='ik' else row[key])
 def finish(self,c,loc):
  for i in loc['ended'].nonzero().flatten().tolist():
   r=dict(index=i,segment=self.segment[i],step_id=self.action[i],original_success=bool(loc['success'][i]),position_to_final_m=float(loc['d'][i]),cbl_to_final=float(loc['r'][i]),stuck=bool(loc['stuck'][i]),route_complete=bool(c.state.s[i]==c.route.length[i]),failures=int(c.failures[i]),stalls=int(c.stalls[i]),reason=int(c.reason[i]),terminated=bool(c.terminated[i]),truncated=bool(c.truncated[i]),triggers=dict(fail_limit=bool(c.failures[i]>=c.failure_limit),stall_limit=bool(c.stalls[i]>=5),decision_limit=bool(c.decisions[i]>=150),time_limit=bool((c.time if c.failure_mode=='terminal' else c.attempt_time)[i]>=200)))
   self.finishes[i]=r;self.finish_history.append(r)
 def step_end(self,c,tr):self.phase='idle'
 def close(self):self.stream.close()

@torch.no_grad()
def evaluate_batch(arm,seed,jobs,actor,cfg,path,bridge):
 check();path.mkdir(parents=True,exist_ok=False);start=time.perf_counter();cpu=time.process_time();env=evaluation_environment(jobs,cfg,jobs[0]['pool'],torch.device('cuda'))
 # Sampling/initial states and all candidate search retain original IK. Only execution is replaced.
 if arm=='bioik':
  env.kin=BioKinematics(bridge,json.loads((CONFIG/'frozen-budget.json').read_text())['timeout_s']);env.kin.dls_cuda_graph=cfg['dls_cuda_graph']
 rec=Recorder(path,arm,seed,env,jobs);original=env.kin.solve_world
 def timed(*a,**kw):
  torch.cuda.synchronize();t=time.perf_counter();r=original(*a,**kw);torch.cuda.synchronize();wall=time.perf_counter()-t;rec.last_ik_wall=wall
  if rec.phase=='step':rec.timing.append(dict(wall_s=wall,batch=len(a[0]),backend=arm))
  return r
 env.kin.solve_world=timed
 dump(path/'started.json',dict(arm=arm,seed=seed,jobs=jobs,epoch=time.time(),pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21]))
 try:
  with observing(rec):
   t=time.perf_counter();env.reset(cancel=lambda:(OUT/'STOP').exists());torch.cuda.synchronize();reset_s=time.perf_counter()-t
   dump(path/'initial.json',dict(base=env.core.state.base,q=env.core.state.q,route_xyz=env.core.route.xyz,route_length=env.core.route.length,proposal_seeds=env.proposal_seeds))
   steps=torch.zeros(env.batch,device='cuda',dtype=torch.long);iterations=0
   while not (env.core.terminated|env.core.truncated).all():
    check();choose_candidate(env);c=env.core
    if c.done.all():continue
    torch.cuda.synchronize();t=time.perf_counter();raw=actor(c.current_observation());torch.cuda.synchronize();rec.inference.append(time.perf_counter()-t)
    tr=env.step(raw).transition;steps+=tr.active;drain_history(c);iterations+=1
    if iterations%50==0:dump(path/'progress.json',dict(iterations=iterations,transfers=int(steps.sum()),ended=int((c.terminated|c.truncated).sum()),requests=rec.request_count,wall_s=time.perf_counter()-start,epoch=time.time()))
   c=env.core;rows=[]
   for i,j in enumerate(jobs):
    first=rec.first.get(i);finish=rec.finishes.get(i);assert finish is not None;rows.append(dict(final_arrival=finish['original_success'],original_success=finish['original_success'],position_to_final_m=finish['position_to_final_m'],cbl_to_final=finish['cbl_to_final'],last_finish=finish,**{k:v for k,v in j.items() if k!='entry'},backend=arm,strict_success=bool(c.strict_success[i]),terminated=bool(c.terminated[i]),truncated=bool(c.truncated[i]),failures=int(c.failures[i]),stalls=int(c.stalls[i]),decisions=int(c.decisions[i]),time_s=float(c.time[i]),attempt_time_s=float(c.attempt_time[i]),transfers=int(steps[i]),attempted_substeps=int(c.attempted_total[i]),committed_substeps=int(c.committed_total[i]),route_s=float(c.state.s[i]),route_length=float(c.route.length[i]),route_complete=bool(c.state.s[i]==c.route.length[i]),first_failure_case=None if first is None else first['case_id'],first_failure_kind=None if first is None else first['kind'],first_failure_step=None if first is None else first['step_id']))
   rec.close();dump(path/'finishes.json',rec.finish_history);result=dict(complete=True,backend=arm,training_seed=seed,rows=rows,wall_s=time.perf_counter()-start,cpu_s=time.process_time()-cpu,reset_s=reset_s,ik_timing=rec.timing,inference_wall_s=rec.inference,request_count=rec.request_count,all_raw_cause_counts=rec.all_fail,epoch=time.time());dump(path/'result.json',result);return result
 except BaseException:
  rec.close();dump(path/'incomplete.json',dict(complete=False,wall_s=time.perf_counter()-start,cpu_s=time.process_time()-cpu,request_count=rec.request_count,traceback=traceback.format_exc()));raise

@torch.no_grad()
def run(arm,phase):
 manifest=prepare();seedgroups=(4718,) if phase=='smoke' else (4718,4719,4720);bridge=Bridge() if arm=='bioik' else None
 try:
  for seed in seedgroups:
   cfg,model=load_config(seed);actor=DeterministicActor(model/'final.actor.pt','cuda');assert actor.steps==5000000 and actor.synchronous
   loaded=dict(training_seed=seed,actor_sha256=sha(model/'final.actor.pt'),device=str(next(actor.policy.parameters()).device),torch=torch.__version__,gpu_name=torch.cuda.get_device_name(),gpu_uuid='GPU-'+str(torch.cuda.get_device_properties(0).uuid),pid=os.getpid(),threads=torch.get_num_threads(),interop=torch.get_num_interop_threads(),cpuset=sorted(os.sched_getaffinity(0)),phase=phase,backend=arm,run_source_sha256=sha(__file__),backend_source_sha256=sha('/work/src/backend.py'))
   dump(OUT/f'{phase}-{arm}-{seed}-loaded.json',loaded)
   for domain in ('random','semantic'):
    jobs=[j for j in manifest['jobs'] if j['training_seed']==seed and j['domain']==domain]
    if phase=='smoke':jobs=jobs[:8]
    for offset in range(0,len(jobs),16):
     tag=f'{phase}-{arm}-{seed}-{domain}-{offset:03d}';path=OUT/tag
     completed=[p for p in [path,*sorted(OUT.glob(tag+'-attempt*'))] if (p/'result.json').exists()]
     if completed:
      assert len(completed)==1,('duplicate complete batches',tag)
      previous=json.loads((completed[0]/'result.json').read_text());assert [(r['map_id'],r['seed']) for r in previous['rows']]==[(j['map_id'],j['seed']) for j in jobs[offset:offset+16]]
      continue
     if path.exists():
      n=2
      while (OUT/(tag+f'-attempt{n}')).exists():n+=1
      path=OUT/(tag+f'-attempt{n}')
     result=evaluate_batch(arm,seed,jobs[offset:offset+16],actor,cfg,path,bridge)
     print(json.dumps(dict(event='batch_done',tag=path.name,episodes=len(result['rows']),strict=sum(x['strict_success'] for x in result['rows']),wall_s=result['wall_s'],requests=result['request_count'])),flush=True)
     dump(OUT/'status.json',dict(phase=phase,backend=arm,latest=path.name,epoch=time.time(),pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21]))
   del actor;torch.cuda.empty_cache()
 finally:
  if bridge is not None:bridge.close()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--arm',choices=['current','bioik'],default='current');parser.add_argument('--phase',choices=['prepare','smoke','formal'],default='prepare');args=parser.parse_args()
 torch.set_num_threads(2);torch.set_num_interop_threads(1)
 signal.signal(signal.SIGTERM,lambda *args:(_ for _ in ()).throw(InterruptedError('SIGTERM')))
 if args.phase=='prepare':print(json.dumps(dict(manifest=str(CONFIG/'development-manifest.json'),episodes=prepare()['episode_count'])),flush=True)
 else:run(args.arm,args.phase)
if __name__=='__main__':main()
