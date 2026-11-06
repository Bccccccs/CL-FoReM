#!/usr/bin/env python3
"""task10.19: frozen expanded paired evaluation, no training entry."""
import argparse, collections, fcntl, hashlib, json, os, random, shlex, signal, subprocess, sys, time, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'results/task10/t10-expanded-20261106-r2'
LOG=ROOT/'logs/task10/t10-expanded-20261106-r2'
CONTAINER='forem-task10-19-gpu3'
PHYSICAL=3
sys.path.insert(0,str(ROOT/'src'))
from task10.runtime import atomic_json, atomic_torch, sha256

def read(p):return json.loads(Path(p).read_text())
def now():
 from datetime import datetime
 return datetime.now().astimezone().isoformat()
def append(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('a') as f:f.write(json.dumps(x,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
def text_append(p,s):
 with Path(p).open('a') as f:f.write(s);f.flush();os.fsync(f.fileno())
def log_note(s):text_append(ROOT/'doc/agent_logs/task10/task10.19/20261106-codex-expanded-execution.md','\n'+now()+' '+s+'\n')
def hostify(p):return str(p).replace('/workspace',str(ROOT)).replace('/reference/results','/home/ybc/projects/CL-FoReM/forem/results')
def check_gpu():
 q=subprocess.run(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True)
 row=next(x.split(', ') for x in q.stdout.splitlines() if x.startswith(str(PHYSICAL)+','))
 a=subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True)
 if int(row[2])>256 or int(row[3])!=0 or any(x.startswith(row[1]+',') for x in a.stdout.splitlines()):raise RuntimeError('chosen GPU busy')
 return {'index':PHYSICAL,'uuid':row[1],'memory_mib':int(row[2]),'utilization':int(row[3]),'compute_apps':a.stdout}
def freeze():
 import torch
 from task10.validation import tree_hash
 if (RUN/'plan.json').exists():raise RuntimeError('already frozen')
 pool=Path('/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json'); doc=read(pool)
 old=ROOT/'results/task10/t10-long-eval-20261104-s101-r2/checkpoint-010000/manifest.json'; olddoc=read(old)
 source=ROOT/'results/task10/t10-long-20261104-s101-r2'; weight=source/'checkpoints/decision-010000.actor.pt'
 review=read(source/'final-review-20261106.json');assert review['complete'] and review['training_audit_status']=='verified_complete'
 ck=torch.load(weight,map_location='cpu',weights_only=False)
 assert (ck['format'],ck['decisions'],ck['updates'])==('task10-stage1-actor-v1',10000,9000)
 assert tree_hash(ck['model'])==olddoc['source_checkpoint']['trained_state_sha256']
 used={}; evidence=[]
 for p in sorted((ROOT/'results/task10').rglob('episodes.jsonl')):
  if RUN in p.parents:continue
  found=[]
  for ln in p.read_text().splitlines():
   row=json.loads(ln);m=row.get('map_id')
   if isinstance(m,str) and '_validation_' in m:used.setdefault(m,[]).append(str(p));found.append(m)
  evidence.append({'path':str(p),'sha256':sha256(p),'validation_ids':sorted(set(found))})
 # Explicit manual diagnostic inventory, not references to all maps in contracts.
 manual=ROOT/'results/task10/t10-diagnosis-20261106/first-action/plan.json'
 used.setdefault(read(manual)['map_id'],[]).append(str(manual));evidence.append({'path':str(manual),'sha256':sha256(manual),'validation_ids':[read(manual)['map_id']]})
 excluded=set(used)|set(olddoc['excluded'])
 val=[m for m in doc['maps'] if m['split']=='validation']; byid={m['id']:m for m in doc['maps']}
 train_source={m['source_json_sha256'] for m in doc['maps'] if m['split']=='train'}
 train_target={m['target_sha256'] for m in doc['maps'] if m['split']=='train'}
 # Canonical OBB geometry for affected validation pool only; source/target global indices reuse manifest.
 geoms={}; sidefiles={}
 for m in val:
  p=pool.parent/m['sidecar_path'];assert sha256(p)==m['sha256']['sidecar']
  boxes=read(p)['boxes'];canonical=sorted([tuple(float(v) for v in b) for b in boxes])
  g=hashlib.sha256(json.dumps(canonical,separators=(',',':'),allow_nan=False).encode()).hexdigest()
  geoms[m['id']]=g;sidefiles[str(p)]=sha256(p)
 blocked_geometry={geoms[m] for m in excluded if m in geoms}
 blocked_source={byid[m]['source_json_sha256'] for m in excluded if m in byid}
 blocked_target={byid[m]['target_sha256'] for m in excluded if m in byid}
 rng=random.Random(1919); chosen=[]; unavailable=[];capacity={};seen_geometry=set(blocked_geometry);seen_source=set(blocked_source);seen_target=set(blocked_target)
 for diff in ('sparse','standard'):
  candidates=[]
  for m in sorted((x for x in val if x['difficulty']==diff),key=lambda x:x['id']):
   reason=None
   if m['id'] in excluded:reason='used_or_preexcluded'
   elif m['source_json_sha256'] in train_source or m['target_sha256'] in train_target:reason='train_source_or_target_duplicate'
   elif geoms[m['id']] in seen_geometry or m['source_json_sha256'] in seen_source or m['target_sha256'] in seen_target:reason='validation_geometry_or_source_duplicate'
   if reason:unavailable.append({'map_id':m['id'],'reason':reason});continue
   candidates.append(m);seen_geometry.add(geoms[m['id']]);seen_source.add(m['source_json_sha256']);seen_target.add(m['target_sha256'])
  capacity[diff]=len(candidates);rng.shuffle(candidates);chosen.append(candidates)
 n=min(40,*capacity.values());assert n>0
 scenes=[];expected=[]
 for group in chosen:
  for m in group[:n]:
   i=len(scenes);scenes.append({**m,'i':i,'canonical_geometry_sha256':geoms[m['id']]})
   for j in range(2):
    for k in range(3):
     a=('T','U1','U2')[(i*2+j+k)%3];r={'U1':0,'U2':1}.get(a)
     expected.append({'episode_id':f"{m['id']}__j{j}__{a}",'map_id':m['id'],'difficulty':m['difficulty'],'i':i,'j':j,'strategy':a,'scene_seed':190000+2*i+j,'policy_seed':None if r is None else 191000+4*i+2*j+r,'order':len(expected),'shard':0})
 files={str(weight):sha256(weight),str(old):sha256(old),str(pool):sha256(pool),**sidefiles}
 changed=[]
 # Reuse existing frozen source identity, target only current production implementation.
 for p,h in olddoc['files'].items():
  if p.startswith('/workspace/src/') and p.endswith('.py'):
   if sha256(p)!=h:changed.append(p)
   files[p]=h
 if changed:raise RuntimeError('production source changed: '+str(changed))
 for p in sorted((ROOT/'src/task10').glob('*.py')):files[str(p)]=sha256(p)
 for name in ('task10_expanded_eval.py','task10_expanded_report.py'):files[str(ROOT/'scripts'/name)]=sha256(ROOT/'scripts'/name)
 valaudit={'schema':'task10-expanded-exclusions-v1','used':used,'episode_evidence':evidence,'preexcluded':olddoc['excluded'],'unavailable':unavailable,'capacity':capacity,'canonical_validation_geometries':geoms,'geometry_check_scope':'100 validation OBB canonical box sets; global train/validation source and target geometry hashes from existing manifest; original train-val audit reused','test_used':False}
 atomic_json(RUN/'exclusions.json',valaudit)
 prior=ROOT/'results/task10/t10-expanded-20261106-r1'
 if (prior/'shards/worker0/budget.json').exists():
  prior_cost={'run_id':prior.name,'worker_seconds':read(prior/'shards/worker0/budget.json')['elapsed_seconds'],'launch_seconds':read(prior/'launch.json')['wall_seconds'],'environment_decisions':0,'episodes_completed':0,'reason':'boundary rejected map-selection callback before first decision','budget':str(prior/'shards/worker0/budget.json'),'scientific_identity_unchanged':True}
  atomic_json(RUN/'prior-cost.json',prior_cost)
 plan={'schema':'task10-expanded-evaluation-v1','run_id':RUN.name,'frozen_at':now(),'profile':'task10.19-expanded-paired-fixed10k','scenes':scenes,'expected':expected,'capacity':capacity,'maps_per_difficulty':n,'scale_adjustment':None if n==40 else 'Before labels, symmetric reduction to available minimum '+str(n),'pool':str(pool),'weight':str(weight),'model_state_sha256':tree_hash(ck['model']),'objective':olddoc['source_checkpoint']['objective'],'lower_state_sha256':read(old.parent/'episodes'/f"{olddoc['scenes'][0]['id']}__trained.json")['weights_before']['lower'],'files':files,'exclusions_sha256':sha256(RUN/'exclusions.json'),'source_code_commit':olddoc['source_code_commit'],'physical_gpu':PHYSICAL,'container':CONTAINER,'limits':{'maps':2*n,'scenarios':4*n,'episodes':12*n,'decisions':12*n*150,'updates':0,'per_episode_native_decisions':150,'per_episode_attempt_seconds':200,'failure_stall_contract':'unchanged sync_v5 cbl_continue'},'statistics':{'primary':'equal map mean of mean_j(T-(U1+U2)/2)','bootstrap':'difficulty stratified map cluster percentile','replicates':10000,'seed':191901,'fixed_plan_denominators':True},'config':olddoc['config'],'single_training_seed':101,'source_final_review':str(source/'final-review-20261106.json'),'estimated_worker_seconds':1328.065712*len(expected)/12,'engineering_window_hours':[16,24],'automatic_retry':'none on error; explicit resume uses committed boundary else same original identity once; preserve all attempts','ordering':'i sparse then standard; j=0,1; rotate arms by (i*2+j)%3; one map stays worker0'}
 plan['config']={**plan['config'],'profile':'sync_v5','evaluation_profile':'task10.19-expanded-paired-fixed10k','physical_gpu':PHYSICAL,'scene_seed':'per expected manifest','max_episodes':len(expected),'max_decisions':len(expected)*150,'max_updates':0,'max_seconds':None}
 if (ROOT/'results/task10/t10-expanded-20261106-r1/plan.json').exists():
  previous_plan=read(ROOT/'results/task10/t10-expanded-20261106-r1/plan.json');assert plan['expected']==previous_plan['expected'] and [m['id'] for m in scenes]==[m['id'] for m in previous_plan['scenes']]
  plan['prior_failed_run']='t10-expanded-20261106-r1';plan['prior_cost']=read(RUN/'prior-cost.json')
 atomic_json(RUN/'plan.json',plan);atomic_json(RUN/'manifest.json',{'plan_sha256':sha256(RUN/'plan.json'),'exclusions_sha256':sha256(RUN/'exclusions.json'),'schema':plan['schema'],'limits':plan['limits']})
 print(json.dumps({'status':'frozen','maps':len(scenes),'episodes':len(expected),'capacity':capacity,'plan_sha256':sha256(RUN/'plan.json'),'weight_sha256':sha256(weight),'state_sha256':plan['model_state_sha256']}))

def cpu_check():
 import torch
 from task10.validation import masked_select,tree_hash
 m=torch.tensor([[False,True,False,True,True]])
 l=torch.tensor([[999.,2.,0.,2.,1.]])
 assert int(masked_select(m,logits=l))==1
 a=torch.Generator().manual_seed(191000);b=torch.Generator().manual_seed(191001)
 global_before=torch.get_rng_state().clone();b0=b.get_state().clone();saved=a.get_state().clone()
 x=[int(masked_select(m,generator=a)) for _ in range(20)]
 assert torch.equal(b.get_state(),b0) and torch.equal(global_before,torch.get_rng_state())
 a.set_state(saved);assert x==[int(masked_select(m,generator=a)) for _ in range(20)]
 assert all(m[0,k] for k in x) and set(x)=={1,3,4}
 atomic_json(RUN/'cpu-check.json',{'status':'passed','cases':['legal argmax and minimum tie','legal uniform with inplace preserved','independent generators','global RNG unchanged','generator restore reproduces sequence'],'new_environment_decisions':0,'updates':0,'script_sha256':sha256(Path(__file__))})
 print('CPU selection/RNG checks passed')

def worker(resume=False):
 import torch
 from task10.validation import tree_hash,initial_snapshot,core_record,terminal_reason,plain,masked_select
 from task10.entry import initialize_determinism
 from task10.environment import Task10Env
 from task10.lower import FrozenB3
 from task10.runner import check_finite,tensor_state_hash
 from task10.boundary_state import capture_environment,restore_environment,encode,decode
 from task7_upper.model import UpperModel
 from task7_upper.stages import environment_inputs,runtime,restore_runtime
 from task7_upper.replay import exact_cpu
 from task7_lower.training import rng_state,restore_rng
 run=RUN/'shards/worker0';run.mkdir(parents=True,exist_ok=True)
 lock=(run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 plan=read(RUN/'plan.json');started=time.monotonic();epoch=time.time();session=f"{int(epoch)}-{os.getpid()}";status='failed';error=None;current=None;env=None
 if (run/'budget.json').exists() and not resume:raise RuntimeError('existing budget: explicit resume required')
 if (RUN/'STOP').exists():raise RuntimeError('STOP remains: user pause cannot resume')
 for p,h in plan['files'].items():
  if sha256(p)!=h:raise RuntimeError('frozen input changed '+p)
 assert os.environ.get('TASK10_PHYSICAL_GPU')==str(PHYSICAL)
 settings=initialize_determinism(1919)
 ck=torch.load(plan['weight'],map_location='cpu',weights_only=False)
 with torch.random.fork_rng(devices=[]):model=UpperModel(vector_dim=ck['vector_dim'])
 model.load_state_dict(ck['model'],strict=True);model.to('cuda:0').eval().requires_grad_(False)
 policy=FrozenB3(device='cuda:0',artifact_root='/reference',source_root='/reference/source')
 weights={'model':tree_hash(model.state_dict()),'lower':tensor_state_hash(policy.actor)}
 assert weights=={'model':plan['model_state_sha256'],'lower':plan['lower_state_sha256']}
 # CUDA-specific selection isolation checked without environment interactions.
 m=torch.tensor([[True,False,True]],device='cuda:0');a=torch.Generator(device='cuda:0').manual_seed(191000);b=torch.Generator(device='cuda:0').manual_seed(191001)
 g0=torch.cuda.get_rng_state().clone();b0=b.get_state().clone();a0=a.get_state().clone();draw=[int(masked_select(m,generator=a)) for _ in range(16)];a.set_state(a0)
 assert draw==[int(masked_select(m,generator=a)) for _ in range(16)] and torch.equal(b0,b.get_state()) and torch.equal(g0,torch.cuda.get_rng_state())
 assert str(next(model.parameters()).device)==str(next(policy.actor.parameters()).device)=='cuda:0'
 entry={'status':'verified','pid':os.getpid(),'session':session,'runtime':settings,'weights':weights,'model_eval':not model.training,'model_no_grad':all(not p.requires_grad for p in model.parameters()),'lower_eval':not policy.actor.training,'lower_no_grad':all(not p.requires_grad for p in policy.actor.parameters()),'cuda_generator_isolation':True,'cuda_generator_restore':True,'plan_sha256':sha256(RUN/'plan.json'),'physical_gpu':PHYSICAL,'updates':0}
 atomic_json(run/f'entry-{session}.json',entry);atomic_json(run/'entry.json',entry)
 budget={'status':'active','pid':os.getpid(),'session':session,'started_epoch':epoch,'updates':0,'planned_episodes':len(plan['expected']),'planned_decisions':plan['limits']['decisions'],'completed_episodes':len(list((run/'episodes').glob('*.json'))),'completed_decisions':sum(read(p).get('decisions',0) for p in (run/'episodes').glob('*.json')),'in_flight':None,'elapsed_seconds':0}
 previous=sum(x.get('elapsed_seconds',0) for x in [read(p) for p in (run/'sessions').glob('*.json')])
 def flush():
  budget['elapsed_seconds']=time.monotonic()-started;budget['cumulative_worker_seconds']=previous+budget['elapsed_seconds'];atomic_json(run/'budget.json',budget);atomic_json(run/'sessions'/f'{session}.json',budget)
 def stop_boundary():
  if (RUN/'STOP').exists():raise InterruptedError('STOP at committed boundary')
 def new_env(row):
  e=Task10Env(1,policy,seed=row['scene_seed'],pool=plan['pool'],split='validation',device='cuda:0',run_id=RUN.name,code_commit=plan['source_code_commit'],config_hash=sha256(RUN/'plan.json'),risk_chunk_size=256,observation_chunk_size=128,reuse_route_raster=True)
  e.episodes.kin.dls_cuda_graph=True
  e.episodes.sampler.entries=[x for x in e.episodes.sampler.entries if x['id']==row['map_id']]
  if len(e.episodes.sampler.entries)!=1:raise ValueError('one frozen map required')
  return e
 def save_boundary(row,adir,generator,records):
  atomic_torch(adir/'boundary.pt',{'schema':'task10-expanded-boundary-v1','plan_sha256':sha256(RUN/'plan.json'),'episode':row,'environment':capture_environment(env),'vcm':encode(runtime(model.vcm)),'generator':generator.get_state(),'rng':rng_state(),'records':records})
  atomic_json(adir/'boundary-meta.json',{'decisions':row['decisions'],'path':str(adir/'boundary.pt'),'sha256':sha256(adir/'boundary.pt'),'plan_sha256':sha256(RUN/'plan.json')})
 def weight_check():
  after={'model':tree_hash(model.state_dict()),'lower':tensor_state_hash(policy.actor)}
  if after!=weights:raise RuntimeError('weights changed')
  return after
 flush()
 try:
  for row in plan['expected']:
   stop_boundary();eid=row['episode_id'];done=run/'episodes'/f'{eid}.json'
   if done.exists():
    old=read(done);assert old['complete'] and all(old[k]==row[k] for k in row);continue
   attempts=run/'attempts'/eid;existing=sorted(attempts.glob('a[0-9][0-9]'));idx=len(existing)+1
   if idx>2:raise RuntimeError('same identity already attempted twice; diagnose before another attempt')
   adir=attempts/f'a{idx:02d}';adir.mkdir(parents=True,exist_ok=False)
   current={**row,'attempt':idx,'attempt_dir':str(adir),'complete':False,'decisions':0,'inplace_count':0,'failure_kinds':{},'wall_seconds':0.,'weights_before':weights,'session':session,'started_epoch':time.time()}
   records=[];episode_start=time.monotonic();env=new_env(row);model.vcm.reset();generator=torch.Generator(device='cuda:0').manual_seed(row['policy_seed'] if row['policy_seed'] is not None else 0)
   resumed=False
   if existing:
    prior=existing[-1];meta=prior/'boundary-meta.json'
    if meta.exists():
     bmeta=read(meta);bp=Path(bmeta['path']);payload=torch.load(bp,map_location='cpu',weights_only=False)
     # Uncommitted raw tail means the last snapshot is not the latest durable step: keep attempt, rerun original identity once.
     raws=list((prior/'decisions').glob('*.pt'))
     nprev=len(payload['records']);has_tail=len(raws)>nprev
     if sha256(bp)==bmeta['sha256'] and payload['plan_sha256']==sha256(RUN/'plan.json') and not has_tail:
      restore_environment(env,payload['environment']);restore_runtime(model.vcm,decode(payload['vcm'],device='cuda:0'));generator.set_state(payload['generator'].cpu());restore_rng(payload['rng']);records=payload['records'];oldrow=payload['episode'];current={**oldrow,'attempt':idx,'attempt_dir':str(adir),'session':session,'resume_from':str(bp),'resumed_exact_boundary':True,'prior_wall_seconds':oldrow.get('wall_seconds',0.),'started_epoch':time.time()};resumed=True
    append(run/'attempts.jsonl',{'event':'resume','episode_id':eid,'attempt':idx,'exact_boundary':resumed,'previous_attempt':str(prior),'fallback':'same frozen initial identity once' if not resumed else None})
   if not resumed:
    env.reset()
    geo=next(x['sha256']['sidecar'] for x in plan['scenes'] if x['id']==row['map_id'])
    snapshot=initial_snapshot(env,geo);atomic_torch(adir/'initial.pt',snapshot);current['initial_hashes']={k:tree_hash(v) for k,v in snapshot.items()};current['scene_provenance']=plain(env.episodes.scenes.provenance());current['policy_rng_initial_sha256']=tree_hash(generator.get_state())
   if row['order']==0:
    original=ROOT/'results/task10/t10-expanded-20261106-r1/shards/worker0/attempts'/eid/'a01/episode.json'
    if original.exists():
     assert current['initial_hashes']==read(original)['initial_hashes'],'map binding changed initial scientific state'
     atomic_json(run/'map-binding-regression.json',{'status':'passed','initial_hashes_equal':True,'original':str(original),'same_seed_and_identity':True,'new_decisions_for_regression':0})
   pair=run/'pairs'/f"{row['map_id']}__j{row['j']}.json"
   if pair.exists():assert read(pair)['initial_hashes']==current['initial_hashes'],'paired initial typed hashes differ'
   else:atomic_json(pair,{'map_id':row['map_id'],'j':row['j'],'scene_seed':row['scene_seed'],'initial_hashes':current['initial_hashes']})
   atomic_json(adir/'episode.json',current);save_boundary(current,adir,generator,records)
   while True:
    stop_boundary();mask=env.candidates['mask'];check_finite(env.observation);check_finite(env.candidates);i=current['decisions'];logits=None
    before_rng=tree_hash(generator.get_state());global_rng=torch.cuda.get_rng_state().clone()
    with torch.no_grad():
     if row['strategy']=='T':logits=model.forward_step(**environment_inputs(env.observation,env.candidates,env_ids=[0],asynchronous=False,device='cuda:0'))['logits']
     selected=masked_select(mask,logits=logits,generator=generator)
    if row['strategy']!='T' and not torch.equal(global_rng,torch.cuda.get_rng_state()):raise RuntimeError('uniform used global RNG')
    intent={**row,'attempt':idx,'decision_index':i,'selected':int(selected[0]),'selected_inplace':bool(env.candidates['inplace'][0,int(selected[0])]),'mask':plain(mask[0]),'policy_rng_before_sha256':before_rng,'policy_rng_after_sha256':tree_hash(generator.get_state()),'logits':None if logits is None else [float(logits[0,k]) if bool(mask[0,k]) else None for k in range(mask.shape[1])],'probabilities':plain(mask[0].float()/mask[0].sum()) if logits is None else None}
    if i>=150:raise RuntimeError('native decisions overrun')
    atomic_json(adir/'intent.json',intent);budget['in_flight']={'episode_id':eid,'decision_index':i,'attempt':idx};flush();t=time.monotonic()
    result=env.step(selected);rawpath=adir/'decisions'/f'{i:04d}.pt';atomic_torch(rawpath,{'intent':intent,'fields':exact_cpu(result.replay_fields),'attempts':exact_cpu(env.episodes.core.attempts)})
    core=core_record(env.episodes.core,result.info['triggers']);failure_kinds=collections.Counter()
    for a in env.episodes.core.attempts:
     if not bool(a['active'][0]) or bool(a['committed'][0]):continue
     kind='ik_rejected' if int(a['ik_status'][0])>=2 else 'base_collision' if bool(a['base_collision'][0]) else 'arm_collision' if bool(a['arm_collision'][0]) else 'self_collision' if bool(a['self_collision'][0]) else 'unknown'
     failure_kinds[kind]+=1
    dec={**intent,'core':core,'r_t':result.info['r_t'],'actual_result_v1':result.info['actual_result_v1'],'timing':result.info['timing'],'failure_kinds':dict(failure_kinds),'execution_wall_seconds':time.monotonic()-t,'raw_path':str(rawpath),'raw_sha256':sha256(rawpath)}
    append(adir/'decisions.jsonl',plain(dec));records.append(plain(dec));current.update(core);current['inplace_count']=sum(x['selected_inplace'] for x in records);current['failure_kinds']=dict(sum((collections.Counter(x['failure_kinds']) for x in records),collections.Counter()));current['wall_seconds']=current.get('prior_wall_seconds',0.)+time.monotonic()-episode_start
    budget['in_flight']=None;budget['completed_decisions']+=1;flush();atomic_json(adir/'episode.json',current)
    if core['terminated'] or core['truncated']:
     current.update(complete=True,reason=terminal_reason(core),policy_rng_final_sha256=tree_hash(generator.get_state()),weights_after=weight_check(),record_paths=[x['raw_path'] for x in records]);assert sum(current['failure_kinds'].values())==core['failures'];atomic_json(adir/'episode.json',current);atomic_json(done,current);append(run/'episodes.jsonl',current);budget['completed_episodes']+=1;flush()
     print(json.dumps({'event':'episode_complete','episode_id':eid,'completed':budget['completed_episodes'],'decisions':core['decisions'],'wall_seconds':current['wall_seconds']}),flush=True);break
    env.prepare_next(result);save_boundary(current,adir,generator,records)
   env=None;current=None
   if row['order']==5:
    atomic_json(run/'first-map-check.json',{'status':'passed','map_id':row['map_id'],'episodes':6,'three_arm_initial_hashes_equal':True,'typed_components':['physical','route','grid','observation','candidates','mask','proposal_seed','map_geometry'],'no_repeat_smoke':True,'updates':0,'weights':weight_check()})
   if row['order']==11:
    elapsed=time.monotonic()-started;estimate=elapsed/2*len(plan['scenes']);atomic_json(RUN/'throughput-first-two-maps.json',{'maps':2,'episodes':12,'worker_wall_seconds':elapsed,'estimated_total_worker_seconds':estimate,'estimated_total_hours':estimate/3600,'based_on_formal_data':True,'no_extra_profile':True});log_note(f'前2正式地图12回合正常吞吐{elapsed:.3f}s，外推{estimate/3600:.3f}h；首图兼入口核查，无额外profile。仅按成本排期，不根据成绩改变样本/停止。')
  status='complete'
 except InterruptedError as e:status='paused';error=repr(e)
 except BaseException as e:status='failed';error=repr(e);traceback.print_exc()
 finally:
  if current is not None:
   current.update(error=error,complete=False,wall_seconds=current.get('prior_wall_seconds',0.)+time.monotonic()-episode_start);atomic_json(adir/'episode.json',current)
   append(run/'attempts.jsonl',{'event':'partial','episode_id':current['episode_id'],'attempt':current['attempt'],'error':error,'wall_seconds':current['wall_seconds'],'decisions':current['decisions'],'attempt_dir':str(adir)})
  budget.update(status=status,error=error,weights_after=weight_check());flush();atomic_json(run/'worker-exit.json',{'status':status,'error':error,'exit_code':0 if status=='complete' else 1,'session':session,'updates':0});print(json.dumps({'event':'worker_exit','status':status,'error':error}),flush=True)
 return 0 if status=='complete' else 1

def audit():
 import torch
 from task10.validation import tree_hash
 plan=read(RUN/'plan.json');run=RUN/'shards/worker0';issues=[];count=0;decisions=0;initials={};records_seen=set()
 for row in plan['expected']:
  ep=run/'episodes'/f"{row['episode_id']}.json"
  if not ep.exists():continue
  a=read(ep);assert all(a[k]==v for k,v in row.items())
  assert a['complete'] and type(a['strict_success']) is bool
  assert a['terminated'] or a['truncated']
  assert a['weights_before']==a['weights_after']=={'model':plan['model_state_sha256'],'lower':plan['lower_state_sha256']}
  key=(row['map_id'],row['j']);initials.setdefault(key,a['initial_hashes']);assert initials[key]==a['initial_hashes']
  paths=a['record_paths'];assert len(paths)==a['decisions'];fk=collections.Counter();inplace=0;failures=0
  for i,p in enumerate(paths):
   assert p not in records_seen;records_seen.add(p)
   payload=torch.load(p,map_location='cpu',weights_only=False);intent=payload['intent'];f=payload['fields']
   assert intent['episode_id']==row['episode_id'] and intent['decision_index']==i
   chosen=int(f['selected'][0]);assert chosen==intent['selected']
   mask=f['candidates']['mask'][0];assert bool(mask[chosen]) and mask.tolist()==intent['mask']
   inplace+=int(bool(f['candidates']['inplace'][0,chosen]));assert bool(f['candidates']['inplace'][0,chosen])==intent['selected_inplace']
   if row['strategy']=='T':
    logits=intent['logits'];best=max(x for x in logits if x is not None);assert chosen==next(k for k,x in enumerate(logits) if x==best)
    assert intent['policy_rng_before_sha256']==intent['policy_rng_after_sha256']
   else:
    probs=intent['probabilities'];assert all(abs(x-(1/int(mask.sum()) if bool(mask[k]) else 0))<1e-7 for k,x in enumerate(probs))
   assert int(f['decision_index'][0])==i and f['map_ids']==[row['map_id']]
   for q in payload['attempts']:
    if bool(q['active'][0]) and not bool(q['committed'][0]):
     k='ik_rejected' if int(q['ik_status'][0])>=2 else 'base_collision' if bool(q['base_collision'][0]) else 'arm_collision' if bool(q['arm_collision'][0]) else 'self_collision' if bool(q['self_collision'][0]) else 'unknown';fk[k]+=1
   if i==len(paths)-1:
    assert bool(f['terminated'][0])==a['terminated'] and bool(f['truncated'][0])==a['truncated'] and bool(f['strict_success'][0])==a['strict_success']
   decisions+=1
  assert inplace==a['inplace_count'] and dict(fk)==a['failure_kinds'] and sum(fk.values())==a['failures']
  if a['strict_success']:assert a['failures']==0 and a['triggers']['route_end']
  count+=1
 changed=[p for p,h in plan['files'].items() if sha256(p)!=h];assert not changed
 out={'status':'verified_complete' if count==len(plan['expected']) else 'verified_partial','episodes':count,'missing':len(plan['expected'])-count,'decisions':decisions,'paired_initial_states':len(initials),'frozen_files_unchanged':True,'updates':0,'issues':issues,'plan_sha256':sha256(RUN/'plan.json'),'scope':'unique original raw steps, identities, masks, legal argmax/uniform weights, native terminal, failure kinds, counts, weights and typed initial pairing; missing remains unknown'}
 atomic_json(RUN/'audit.json',out);print(json.dumps(out));return 0

def update_docs(state,detail):
 stamp=now();base='forem/results/task10/'+RUN.name;docs=ROOT/'doc';t=docs/'tasks/task10/task10.19'
 msg=f'\n\n## {stamp} 自动交接 · {state}\n\n{detail}\n\n[实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。原件：`{base}/`；日志：`forem/logs/task10/{RUN.name}/`。固定r2 10k、单训练seed101、validation地图、每图2初态、每初态2次随机参照，正式test未使用；0训练更新。推荐GPT6.1sol/medium、Sonnet5.5/medium，入口/随机流/地图组统计需跨模块核查；父实际模型/强度未知，统计子GPT6.1sol/medium。当前审核聊天保留最终验收。\n'
 # Global document writes are short, reread and append only under our advisory lock.
 with (RUN/'docs.lock').open('a') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX)
  for name in ('TASK.md','PROCEDURE.md','RESULTS.md'):text_append(t/name,msg)
  text_append(docs/'PROGRESS.md',f'\n{stamp} · **T10.19-EXPANDED-20261106 · Codex · {state}**：{detail} [结果](tasks/task10/task10.19/RESULTS.md)。\n')
  text_append(docs/'SOURCES.md',f'\n<a id="src-t10-expanded-{state}-{int(time.time())}"></a>\n## task10.19 自动实测/交接 {stamp}\n\n类型：项目原件、工程成本与预登记统计。来源`{base}/plan.json`、`exclusions.json`、`shards/worker0/`、`launch.json`、`handoff.json`、`report.json`（若已生成）。{detail} 固定分母与地图成组统计沿用SRC-T10-EXPANDED-EVAL-PLAN-20261106及SRC-T10-CLUSTER-BOOTSTRAP-20261106；不能据启动状态宣称有收益。\n')
  log_note(f'{state}：{detail}')

def launch(resume=False):
 LOG.mkdir(parents=True,exist_ok=True);lock=(RUN/'launcher.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 plan=read(RUN/'plan.json');assert plan['physical_gpu']==PHYSICAL
 if (RUN/'STOP').exists():raise RuntimeError('STOP present')
 gpu=check_gpu();requests=read_inspect();assert requests[0]['DeviceIDs']==[str(PHYSICAL)]
 if (RUN/'launch.json').exists() and not resume:raise RuntimeError('launch already exists')
 if resume and (RUN/'launch.json').exists():atomic_json(RUN/f'launch-prior-{int(time.time())}.json',read(RUN/'launch.json'))
 cmd=['docker','exec','--user','1004:1004','-e','PYTHONPATH=/workspace/src','-e','CUBLAS_WORKSPACE_CONFIG=:4096:8','-e',f'TASK10_PHYSICAL_GPU={PHYSICAL}',CONTAINER,'python3','-u','/workspace/scripts/task10_expanded_eval.py','worker']+(['--resume'] if resume else [])
 command=['sg','docker','-c',shlex.join(cmd)];session=str(int(time.time()));log=LOG/f'worker-{session}.log';info={'status':'launching','pid':os.getpid(),'started_epoch':time.time(),'gpu_check':gpu,'device_requests':requests,'command':command,'log':str(log),'plan_sha256':sha256(RUN/'plan.json'),'resume':resume,'automatic_finalize':True,'progress_interval_seconds':1800,'stop':str(RUN/'STOP'),'signal_independence':'launcher and worker client separate sessions; stdin closed; nohup host launcher'}
 atomic_json(RUN/'launch.json',info);rc=1;last=0
 with log.open('x') as f:
  proc=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);info.update(status='running',client_pid=proc.pid);atomic_json(RUN/'launch.json',info)
  update_docs('active',f'持久启动，host launcher PID{os.getpid()}、client PID{proc.pid}，GPU{PHYSICAL}，计划{len(plan["expected"])}回合；首条产物和初态核查待运行。工程窗口16–24h，非硬截止；无按成绩提前停止。STOP={RUN}/STOP；恢复先读结果保留partial，再显式launch --resume。')
  while proc.poll() is None:
   if time.time()-last>=1800:
    b=read(RUN/'shards/worker0/budget.json') if (RUN/'shards/worker0/budget.json').exists() else {};append(RUN/'progress.jsonl',{'at':now(),'pid':os.getpid(),'worker_pid':b.get('pid'),'completed_episodes':b.get('completed_episodes',0),'elapsed_seconds':b.get('elapsed_seconds'),'in_flight':b.get('in_flight')});log_note('后台完整性心跳：完成'+str(b.get('completed_episodes',0))+'/'+str(len(plan['expected']))+'，worker PID'+str(b.get('pid'))+'，未读取中途成功率作决策。');last=time.time()
   time.sleep(10)
  rc=proc.returncode
 info.update(status='exited',returncode=rc,finished_epoch=time.time(),wall_seconds=time.time()-info['started_epoch']);atomic_json(RUN/'launch.json',info)
 # Pure CPU final report. No extra environment or optimizer creation.
 auditcmd=['sg','docker','-c',shlex.join(['docker','exec','--user','1004:1004','-e','PYTHONPATH=/workspace/src',CONTAINER,'python3','-u','/workspace/scripts/task10_expanded_eval.py','audit'])]
 with (LOG/f'audit-{session}.log').open('x') as f:audited=subprocess.run(auditcmd,stdout=f,stderr=subprocess.STDOUT)
 reportcmd=['sg','docker','-c',shlex.join(['docker','exec','--user','1004:1004',CONTAINER,'python3','-u','/workspace/scripts/task10_expanded_report.py','--run','/workspace/results/task10/'+RUN.name])]
 with (LOG/f'report-{session}.log').open('x') as f:reported=subprocess.run(reportcmd,stdout=f,stderr=subprocess.STDOUT)
 report=read(RUN/'report.json') if (RUN/'report.json').exists() else None
 complete=rc==0 and audited.returncode==0 and read(RUN/'audit.json')['status']=='verified_complete' and reported.returncode==0 and report is not None and report['status']=='complete' and read(RUN/'shards/worker0/worker-exit.json')['status']=='complete'
 handoff={'status':'review' if complete else 'incomplete','worker_rc':rc,'audit_rc':audited.returncode,'report_rc':reported.returncode,'report_path':str(RUN/'report.json'),'report_sha256':sha256(RUN/'report.json') if report else None,'plan_sha256':sha256(RUN/'plan.json'),'launch':info,'complete':complete,'updates':0,'reviewer':'current audit chat','single_training_seed':101}
 atomic_json(RUN/'handoff.json',handoff)
 detail=f'worker rc={rc}，report rc={reported.returncode}，完整条件={complete}。'+('固定统计报告已生成，结论及区间见REPORT.md/report.json；待审核聊天验收。' if complete else '保留全部partial/缺失与固定分母；未自动换图或重试。先定位日志，再按边界或同身份一次恢复，用户STOP未撤销不得恢复。')
 update_docs('review' if complete else 'blocked',detail);return 0 if complete else 1

def read_inspect():
 p=subprocess.run(['sg','docker','-c',f"docker inspect {CONTAINER} --format '{{{{json .HostConfig.DeviceRequests}}}}'"],capture_output=True,text=True,check=True);return json.loads(p.stdout)
def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=('freeze','cpu-check','worker','launch','audit'));p.add_argument('--resume',action='store_true');a=p.parse_args();RUN.mkdir(parents=True,exist_ok=True)
 return {'freeze':freeze,'cpu-check':cpu_check,'audit':audit,'worker':lambda:worker(a.resume),'launch':lambda:launch(a.resume)}[a.phase]() or 0
if __name__=='__main__':raise SystemExit(main())
