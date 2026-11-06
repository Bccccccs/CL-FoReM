#!/usr/bin/env python3
"""External incremental issuer for the eight frozen task9.11 training stages.

This file is outside runtime.artifact_files: it never changes native model source
contracts, scientific configuration, checkpoints, or running workers. Final
scientific acceptance deliberately remains an explicit independent decision.
"""
import argparse,datetime as dt,importlib.util,json,math,sys,time,traceback
from pathlib import Path
F=Path(__file__).resolve().parents[1];sys.path.insert(0,str(F/'src'))
from task9_lr import real_batch as b,real_g1 as g,real_program as m,real_receipts as r,clock
from task9_lr.admission import validate_profile,save_readiness,evaluation_complete
from task9_lr.real_lon import stream_sha
ROLE=b.REVIEWER
SOURCE_PASS=F/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/resume-v1/PROGRAM-SOURCE-PASS-v3.json'
INITIAL_BUDGET=SOURCE_PASS.parent/'program-budget-admission-v3-r2.json'
PLAN=SOURCE_PASS.parent/'FINITE-RESOURCE-POLICY-REVIEW-v1.json'
POLICY=SOURCE_PASS.parents[2]/'budget-policy-adoption-20261104-v1.json'
def load(p):return json.loads(Path(p).read_text())
def ref(p,full=False):return dict(path=str(Path(p).resolve()),sha256=stream_sha(Path(p)) if full else b.sha256(p))
def emit(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if load(p)!=v:raise ValueError('immutable reviewer artifact differs: '+str(p))
 else:
  with p.open('x') as stream:json.dump(v,stream,sort_keys=True,indent=2);stream.write('\n')
 return ref(p)
def verdict(p,mode):
 q=Path(p['new_output_root'])/'reviews'/(mode['name']+'.json');pointer=load(q)
 if set(pointer)!={'independent_verdict'}:raise ValueError('invalid review pointer')
 v=m.review(pointer['independent_verdict'])
 if v.get('status')!='PASS_COMPLETE' or v.get('activity')!=mode['name'] or v.get('source_digest')!=p['source_digest']:raise ValueError('prior review identity/status')
 return v,pointer['independent_verdict']
def all_prior(p,mode):
 seq=m.stages();return [verdict(p,x)[0] for x in seq[:seq.index(mode)]]
def caps(p,mode):
 if mode['phase']=='profile':return dict(infra=6000,control=420,worker=5400,tail=120,save=600,lease=6420)
 if mode['phase']!='remaining':raise ValueError('NEEDS_FINAL_SCIENTIFIC_ACCEPTANCE')
 previous,_=verdict(p,m.stage(p,'profile',mode['arm'],mode['seed']))
 available=43200-math.ceil(previous['worker_enclosing_upper_s'])
 if available<4000:raise ValueError('NEEDS_RUN_CAP_REVIEW')
 return dict(infra=available-600,control=420,worker=available-1000,tail=120,save=1800,lease=available-180)
def make_budget(p,mode,O):
 dest=O/(mode['name']+'-budget.json')
 if dest.exists():return ref(dest)
 prior=all_prior(p,mode);paidroots={q.resolve() for folder in ('results','logs') for q in (F/folder/'task9').glob('t9.11*') if q.is_dir()}|{F/'doc/agent_logs/task9/task9.11'}
 files={q.resolve() for root in paidroots for q in root.rglob('*') if q.is_file()};items={str(q):dict(bytes=q.stat().st_size,diagnostic=q.is_relative_to(F/'doc/agent_logs/task9/task9.11') or any('diagnostics' in x for x in q.parts) or q.suffix in ('.json','.jsonl','.txt','.bin','.log','.gz','.zip','.npz')) for q in sorted(files)}
 total=sum(x['bytes'] for x in items.values());diag=sum(x['bytes'] for x in items.values() if x['diagnostic'])
 ss=emit(O/(mode['name']+'-paid-storage.json'),dict(format='task9-lr-program-storage-snapshot-v1',status='PASS',reviewer=ROLE,files=items,covered_external_roots=[str(F/Path(x).relative_to('/workspace')) for x in p['external_output_roots']],observed_epoch=time.time()))
 # Four original per-run 12h ceilings; each completed actual envelope reduces
 # its own remaining reservation. Final4h and explicit control6h remain once.
 used=sum(v['worker_enclosing_upper_s'] for v in prior)
 initial=load(INITIAL_BUDGET)
 future=initial['future_reserved']['worker_seconds']-used
 if future<0:raise ValueError('negative future reservation')
 profiles={(x['activity'].split('-')[1],int(x['activity'].split('-')[2])):x for x in prior if x['activity'].startswith('profile-') and x.get('cost')}
 if profiles:
  completed={x['activity'] for x in prior}
  reference_remaining=max(x['cost']['remaining_proxy_s'] for x in profiles.values())
  reference_profile=max(x.get('actual_owner_wait_s',x['worker_enclosing_upper_s']) for x in profiles.values())
  projected=0
  for arm,seed in m.ORDER:
   if f'remaining-{arm}-{seed}' in completed:continue
   own=profiles.get((arm,seed))
   projected+=own['cost']['remaining_proxy_s'] if own else reference_profile+reference_remaining
  # Engineering forecast, not a physical lower/upper:5% observed-workload
  # variation plus original final4h and explicit control/restore6h.
  future=math.ceil(projected*1.05+14400+21600)
  if any(x['activity'].startswith('remaining-') for x in prior):
   full_reference=36953.44800706208
   for x in prior:
    if x['activity'].startswith('remaining-'):
     _,arm,seed=x['activity'].split('-');own_profile=profiles.get((arm,int(seed)))
     if own_profile:full_reference=max(full_reference,x.get('aggregate_actual_enclosing_s',x['worker_enclosing_upper_s'])+own_profile.get('actual_owner_wait_s',own_profile['worker_enclosing_upper_s']))
   work=0
   for arm,seed in m.ORDER:
    if f'remaining-{arm}-{seed}' in completed:continue
    own=profiles.get((arm,seed))
    work+=own['cost']['remaining_proxy_s'] if own else full_reference
   future=math.ceil(work+9892.491192812213+7200)
 now=time.time();T0=dt.datetime.fromisoformat(p['started_at']).timestamp()
 # Initial historical physical bound + actual single-GPU stage allocations;
 # do not charge unrelated second-GPU work or multiply waiting by four cards.
 initial=load(INITIAL_BUDGET)
 gpu=initial['gpu_upper_s']+sum(v['actual_allocation_s'] for v in prior)
 worker=345600+used
 # Neutral forecast remains conservative after completed stages. It is not a
 # hard lower bound and never causes added scientific episodes or deleted data.
 future_eval=sum(x['evaluation_episodes'] for x in m.stages())
 evalleft=future_eval-sum(v['evaluation_episodes'] for v in prior)
 future_diag=math.ceil(initial['future_reserved']['diagnostic_bytes']*evalleft/future_eval)
 completed_runs=sum(x['phase']=='remaining' for x in m.stages()[:m.stages().index(mode)])
 future_storage=math.ceil(initial['future_reserved']['storage_bytes']*(4-completed_runs)/4)
 basis={'historical-worker':ref(PLAN),'historical-gpu':ref(PLAN),'C-policy':ref(POLICY),'open-participants':ref(PLAN),'background-inventory':ref(SOURCE_PASS.parent/'host-turn-current-v1.json'),'full-program-future-reservation':ref(PLAN),'storage':ss}
 v=dict(format='task9-lr-real-program-budget-admission-v1',status='PASS_PROGRAM',reviewer=ROLE,run_id=p['run_id'],original_started_at=p['started_at'],deadline=p['deadline'],classification='EVIDENCE_AND_EXPLICIT_AUTHORIZED_POLICY_RESERVE_NOT_EXACT_HISTORY',historical_unknown_preserved=True,full_program_feasible=True,storage_accounting='HISTORICAL_SNAPSHOT_PLUS_NEW_PATH_GROWTH_ONCE',worker_upper_s=worker,gpu_upper_s=gpu,open_worker_upper_rate=0,open_gpu_upper_rate=0,participants=[dict(thread_id='external-program-driver',turn_id=mode['name'])],bound_clock=clock.capture(p),basis=basis,rolling_rule='EVIDENCE_BOUND_PARTICIPANTS_PLUS_EXPLICIT_STAGE_RESERVE',open_rates_exclude_explicit_stage_reservations=True,policy_adoption=ref(POLICY),storage_upper_bytes=total,diagnostic_upper_bytes=diag,historical_storage_snapshot=ss,future_reserved=dict(worker_seconds=future,gpu_seconds=future,calendar_seconds=future,storage_bytes=future_storage,diagnostic_bytes=future_diag),accounting_note='Historical worker96h explicit authorized policy. Exact completed enclosing/allocation costs charged once. Preparation/debug/audit remain recorded separately under AGENTS budget-review. Waiting not4card usage.')
 # Keep the forecast evidence and fail honestly before allocating if a real
 # user deadline or finite safety cap would be crossed.
 v['actual_stage_forecasts']=[dict(activity=x['activity'],cost=x.get('cost'),actual_enclosing_s=x['worker_enclosing_upper_s'],actual_allocation_s=x['actual_allocation_s']) for x in prior]
 br=emit(dest,v);m.checked_budget(p,br);return br
def base_token(p,mode,O):
 prior=all_prior(p,mode);cap=caps(p,mode);br=make_budget(p,mode,O)
 v=dict(format='task9-lr-real-program-release-v1',status='PASS',reviewer_task=ROLE,run_id=p['run_id'],code_hash=p['source_digest'],protocol_sha256=p['_sealed_sha256'],arm=mode['arm'],seed=mode['seed'],intended_activity=mode['name'],automatic_retry=False,image=g.IMAGE,gpu_uuid=p['preferred_gpu_uuid'],source_review=ref(SOURCE_PASS),budget_review=br,expected_evaluation_before=m.expected_before(mode),evaluation_reservation=mode['evaluation_episodes'],completed_G1=p['completed_G1'],completed_LON=p['completed_LON'],expires_at=p['deadline'])
 if prior:v['predecessor_review']=verdict(p,m.stages()[m.stages().index(mode)-1])[1]
 if mode['phase']=='remaining':v['profile_evidence']=prior[-1]['profile_evidence']
 return v,cap
def plan_stage(p,mode,O):
 path=g.ISSUER_ROOT/p['run_id']/(mode['name']+'-infrastructure-release.json')
 if path.exists():return dict(status='PASS',infrastructure_release=str(path))
 token,cap=base_token(p,mode,O);token.update(stage='infrastructure',max_worker_seconds=cap['infra'],control_reserve_s=cap['control'],save_reserve_s=cap['save'],max_gpu_seconds=cap['lease'],independent_release_path=str(path))
 emit(path,token);m.release(path,p,infrastructure=True);return dict(status='PASS',infrastructure_release=str(path))
def review_allocation(p,mode,O):
 out=Path(p['new_output_root']);ar=out/'allocations'/mode['name'];v=load(ar/'container.json');state=load(ar/'container-inspect.json');ident=v['container_id']
 if ident!=state['Id'] or not state['State']['Running'] or state['Image']!=g.IMAGE:raise ValueError('exact container/image/live mismatch')
 m.validate_single_gpu_allocation(state,p);r.validate_wait(v['launch_wait']);r.inspection(v['observation'])
 token,cap=base_token(p,mode,O);lease=load(ar/'allocation-lease.json')
 if lease['lease_seconds']!=cap['lease']:raise ValueError('allocation lease differs from plan')
 path=g.ISSUER_ROOT/p['run_id']/(mode['name']+'-release.json');token.update(stage=mode['phase'],max_worker_seconds=cap['worker'],control_reserve_s=cap['tail'],save_reserve_s=cap['save'],max_gpu_seconds=cap['lease'],container_id=ident,allocation_lease=m.allocation_reference(p),independent_release_path=str(path))
 emit(path,token);target=out/'releases'/(mode['name']+'.json');emit(target,token);m.release(target,p)
 return dict(status='PASS',stage_release=str(path),container_id=ident)
def review_stage(p,mode,O):
 out=Path(p['new_output_root']);name=mode['name'];path=O/(name+'-verdict.json')
 if path.exists():return dict(status='PASS',independent_verdict=ref(path))
 folder=out/mode['folder'];supervision=out/'supervision'/name
 waitpath=b.receipt_root(p)/name/'real-program-root-wait'/'wait-receipt.json'
 recovered=None
 if waitpath.exists():
  wait=r.validate_wait(ref(waitpath))
  if wait['exit_code']!=0 or wait['run_id']!=p['run_id'] or wait['stage']!=mode['phase']:raise ValueError('real rootwait incomplete/failed')
  closure_ref=ref(waitpath)
 else:
  authorization=SOURCE_PASS.parent/'authorized-native-recoveries'/p['run_id']/(name+'.json')
  recovered=load(authorization)
  if any(recovered.get(k)!=v for k,v in dict(status='PASS_NATIVE_CLOSURE_RECOVERY',reviewer=ROLE,run_id=p['run_id'],source_digest=p['source_digest'],activity=name,outer_rootwait_status='MISSING_KEEP_UNKNOWN').items()):raise ValueError('missing independent native-closure recovery authorization')
  if not recovered.get('evidence'):raise ValueError('native recovery raw evidence missing')
  for e in recovered['evidence']:b.read_ref(e)
  if recovered['worker_enclosing_upper_s']<=0:raise ValueError('invalid recovered policy reserve')
  wait={'wall_s':recovered['worker_enclosing_upper_s']}
  closure_ref=ref(authorization)
 life=load(supervision/'lifecycle.json')
 if life.get('chain_status')!='PASS' or life['owner']['exit_code']!=0 or any(x['exit_code']!=0 for x in life['waits'].values()):raise ValueError('owner/guardian/watcher lifecycle failed')
 stopped=load(out/'allocations'/name/'container-stopped.json');state=stopped['inspect'];token=load(out/'releases'/(name+'.json'))
 if not stopped.get('container_stopped') or state['Id']!=token['container_id'] or state['State']['Running'] or state['State']['Pid']!=0:raise ValueError('exactStopped missing')
 m.validate_single_gpu_allocation(state,p)
 worker=load(folder/(mode['phase']+'-worker.json'))
 if worker.get('status')!='PASS':raise ValueError('worker terminal notPASS')
 count=0
 for q in out.rglob('episodes-started.jsonl'):
  with q.open() as stream:count+=sum(json.loads(line)['count'] for line in stream)
 if count!=m.expected_before(mode)+mode['evaluation_episodes']:raise ValueError('global writeahead episode quota mismatch')
 evidence=[closure_ref,ref(supervision/'lifecycle.json'),ref(out/'allocations'/name/'container-stopped.json'),ref(folder/(mode['phase']+'-worker.json'))]
 extra={}
 if mode['phase']=='profile':
  summary=load(folder/'profile-summary.json');ev=load(folder/'validation-0250000.json');config=load(folder/'config.json');restore=load(folder/'profile-restore.json')
  cost=validate_profile(summary,ev,config['replay_capacity']);ready=save_readiness(cost,summary,p)
  if ready['status']!='ready':raise ValueError(ready['status'])
  if restore.get('steps')!=250000 or restore.get('scientific_limit')!=3000000 or not restore.get('actual_devices'):raise ValueError('native full restore/device evidence missing')
  checkpoint=folder/'profile.pt'
  if not checkpoint.is_file():raise ValueError('full profile missing')
  diagfiles=[q for q in folder.rglob('*') if q.is_file() and (any('diagnostics' in x for x in q.parts) or q.suffix in ('.json','.jsonl','.txt','.bin'))]
  account_path=O/(name+'-diagnostic-account.json')
  stat=ref(account_path) if account_path.exists() else emit(account_path,dict(bytes=sum(q.stat().st_size for q in diagfiles),files=len(diagfiles),steps=250000,ordinary_250k_eval_in_9408=True))
  costs=folder/'checkpoint-costs.jsonl'
  if not costs.exists():raise ValueError('raw checkpoint-costs absent')
  # Freeze only small append-only log prefixes. Remaining naturally appends
  # the originals; never bind mutable logs as immutable predecessor evidence.
  frozen_costs=folder/'profile-checkpoint-costs.jsonl';frozen_interactions=folder/'profile-interactions.jsonl'
  for source,target in [(costs,frozen_costs),(folder/'interactions.jsonl',frozen_interactions)]:
   if not target.exists():
    with target.open('xb') as stream:stream.write(source.read_bytes())
  extra=dict(cost=cost,save_readiness=ready,profile_evidence=dict(profile_checkpoint=ref(checkpoint,True),profile_summary=ref(folder/'profile-summary.json'),profile_restore=ref(folder/'profile-restore.json'),profile_evaluation=ref(folder/'validation-0250000.json'),checkpoint_costs=ref(frozen_costs),interactions=ref(frozen_interactions),diagnostic_account=stat))
  # Frozen release requires all own profile refs inside its own folder. Store
  # the small diagnostic account there as metadata only, never alter models.
  local=folder/'profile-diagnostic-account.json';emit(local,load(stat['path']));extra['profile_evidence']['diagnostic_account']=ref(local)
  evidence += [ref(folder/'profile-summary.json'),ref(folder/'profile-restore.json'),ref(folder/'validation-0250000.json')]
 else:
  summary=load(folder/'summary.json');state_summary=summary['state']
  if state_summary['steps']!=3000000 or state_summary['env_actions']!=3000000 or summary['updates']!=299975 or state_summary.get('unsafe_update'):raise ValueError('3M scientific/update boundary failed')
  evaluations=[]
  for step in range(250000,3000001,250000):
   q=folder/f'validation-{step:07d}.json';ev=load(q);evaluation_complete(ev)
   if ev['step']!=step:raise ValueError('wrong periodic boundary')
   evaluations.append(ref(q))
  if not (folder/'final.pt').exists() or not (folder/'final.actor.pt').exists():raise ValueError('full final checkpoint/actor missing')
  evidence += [ref(folder/'summary.json')]+evaluations
 def docker_ns(text):
  base,_,fraction=text.rstrip('Z').partition('.')
  return int(dt.datetime.fromisoformat(base).replace(tzinfo=dt.timezone.utc).timestamp())*10**9+int((fraction+'000000000')[:9])
 allocation=(docker_ns(state['State']['FinishedAt'])-docker_ns(state['State']['StartedAt']))/1e9
 v=dict(format='task9-lr-real-program-stage-verdict-v1',status='PASS_COMPLETE',reviewer=ROLE,run_id=p['run_id'],activity=name,source_digest=p['source_digest'],evaluation_episodes=mode['evaluation_episodes'],consumed_transfers=mode['transfers'],exact_container_stopped=True,worker_enclosing_upper_s=wait['wall_s'],actual_allocation_s=allocation,evidence=evidence,actual_owner_wait_s=life['actual_owner_wait_wall_s'],actual_worker_wall_s=worker.get('worker_wall_s'),outer_rootwait_status='MISSING_KEEP_UNKNOWN' if recovered else 'ACTUAL_EXIT0',worker_enclosing_classification='AUTHORIZED_POLICY_RESERVE_NOT_ACTUAL' if recovered else 'ACTUAL_ROOTWAIT_ENVELOPE',**extra)
 vr=emit(path,v);emit(out/'reviews'/(name+'.json'),{'independent_verdict':vr});return dict(status='PASS',independent_verdict=vr,cost=extra.get('cost'),actual_allocation_s=allocation)
def review_recovery(p,mode,O,authorization):
 auth=m.review(ref(Path(authorization).resolve()))
 expected=dict(format='task9-lr-external-resume-authorization-v1',status='PASS_CONDITIONAL_NATIVE_RESTORE',reviewer=ROLE,run_id=p['run_id'],source_digest=p['source_digest'],activity='remaining-C-4718')
 if any(auth.get(k)!=v for k,v in expected.items()) or mode['name']!='remaining-C-4718':raise ValueError('foreign recovery authority')
 attempt=Path(auth['attempt_root']);out=Path(p['new_output_root']);folder=out/'formal-C-seed4718'
 if not attempt.is_relative_to(out/'recovery'):raise ValueError('recovery attempt namespace')
 path=O/'remaining-C-4718-aggregate-verdict.json'
 if path.exists():return dict(status='PASS',independent_verdict=ref(path))
 result=load(attempt/'result.json')
 expected_result=dict(status='PASS',run_id=p['run_id'],source_digest=p['source_digest'],activity=mode['name'],attempt_id=attempt.name,episodes_before=1568,episodes_after=2352,steps=3000000,updates=299975)
 if any(result.get(k)!=v for k,v in expected_result.items()):raise ValueError('recovery completion boundary/status mismatch')
 if result['actual_worker_wall_s']>auth['max_worker_seconds'] or result['actual_outer_wall_s']>auth['allocation_lease_s']+5:raise ValueError('new recovery exceeded its finite execution envelope')
 stopped=result['exact_stopped'];state=stopped['inspect']
 if not stopped.get('container_stopped') or state['Id']!=result['container_id'] or state['State']['Running'] or state['State']['Pid'] or state['Image']!=g.IMAGE:raise ValueError('recovery exactStopped/image missing')
 m.validate_single_gpu_allocation(state,p)
 restore=b.read_ref(result['native_restore']);journal=b.read_ref(result['safe_to_resume'])
 if restore.get('status')!='PASS_NATIVE_FULL_RESTORE' or not restore.get('full_config_equals_frozen') or not restore.get('original_loader_and_RNG_restore') or not restore.get('actual_devices') or not journal.get('safe'):raise ValueError('original full loader/journal/devices not proven')
 if any(restore.get(k)!=v for k,v in auth['expected_state'].items()):raise ValueError('2250k full pending restore mismatch')
 summary=b.read_ref(result['summary']);st=summary['state']
 if st['steps']!=3000000 or st['env_actions']!=3000000 or summary['updates']!=299975 or st.get('unsafe_update'):raise ValueError('native final3M state mismatch')
 evidence=[ref(Path(authorization).resolve()),ref(attempt/'result.json'),result['native_restore'],result['safe_to_resume'],result['summary'],ref(attempt/'container-stopped.json')]
 for step in range(250000,3000001,250000):
  q=folder/f'validation-{step:07d}.json';ev=load(q);evaluation_complete(ev)
  if ev['step']!=step:raise ValueError('wrong full cycle boundary')
  evidence.append(ref(q))
 episodes=0
 for q in out.rglob('episodes-started.jsonl'):
  with q.open() as stream:episodes+=sum(json.loads(row)['count'] for row in stream)
 if episodes!=2352:raise ValueError('aggregate own12cycle quota mismatch')
 if not (folder/'final.pt').is_file() or not (folder/'final.actor.pt').is_file():raise ValueError('fullfinal/actor missing')
 old=b.read_ref(auth['old_attempt_evidence'])
 if old['status']!='FAIL_RETAINED' or old['outer_exit_code']!=1:raise ValueError('old failed attempt must remain explicit')
 evidence.append(auth['old_attempt_evidence'])
 def ns(text):
  base,_,frac=text.rstrip('Z').partition('.')
  return int(dt.datetime.fromisoformat(base).replace(tzinfo=dt.timezone.utc).timestamp())*10**9+int((frac+'000000000')[:9])
 allocation=(ns(state['State']['FinishedAt'])-ns(state['State']['StartedAt']))/1e9
 enclosing=old['outer_wall_s']+result['actual_outer_wall_s']
 v=dict(format='task9-lr-real-program-stage-verdict-v1',status='PASS_COMPLETE',reviewer=ROLE,run_id=p['run_id'],activity=mode['name'],source_digest=p['source_digest'],evaluation_episodes=2156,consumed_transfers=2750000,exact_container_stopped=True,worker_enclosing_upper_s=enclosing,actual_allocation_s=old['allocation_s']+allocation,aggregate_actual_enclosing_s=enclosing,evidence=evidence,attempts=[dict(status='FAIL_RETAINED',outer_wall_s=old['outer_wall_s'],evidence=auth['old_attempt_evidence']),dict(status='PASS',outer_wall_s=result['actual_outer_wall_s'],actual_worker_wall_s=result['actual_worker_wall_s'],evidence=ref(attempt/'result.json'))],outer_rootwait_status='ORIGINAL_FAIL_RETAINED_PLUS_CLOSED_NATIVE_RECOVERY',worker_enclosing_classification='SUM_REAL_DISJOINT_ATTEMPT_ENVELOPES',scientific_recovery=dict(checkpoint=auth['checkpoint'],from_steps=2250000,new_consumed=750000,new_evaluations=784,reused_complete_evaluations=1568,final_valid_transfers=3000000,not_a_restart=True))
 vr=emit(path,v);emit(out/'reviews'/(mode['name']+'.json'),{'independent_verdict':vr});return dict(status='PASS',independent_verdict=vr)

def main():
 global SOURCE_PASS,INITIAL_BUDGET
 parser=argparse.ArgumentParser();parser.add_argument('--action',required=True,choices=['plan-stage','review-allocation','review-stage','review-development','review-recovery']);parser.add_argument('--protocol',required=True);parser.add_argument('--phase',choices=['profile','remaining','final-test']);parser.add_argument('--arm',choices=['C','L']);parser.add_argument('--seed',type=int);parser.add_argument('--output',required=True);parser.add_argument('--recovery-authorization');a=parser.parse_args()
 O=Path(a.output).resolve()
 if not O.is_relative_to(m.AUDIT):raise ValueError('independent external review output required')
 protocol_path=Path(a.protocol).resolve();p=b.read(protocol_path);p['_sealed_sha256']=b.sha256(protocol_path)
 context=m.AUDIT/'resume-v1'/(p['run_id']+'-review-context.json')
 if context.exists():
  identity=load(context)
  if identity.get('run_id')!=p['run_id'] or identity.get('source_digest')!=p['source_digest']:raise ValueError('external reviewer context identity mismatch')
  SOURCE_PASS=Path(identity['source_review']['path']);m.source_review(p,identity['source_review'])
  INITIAL_BUDGET=Path(identity['initial_budget']['path']);initial=m.checked_budget(p,identity['initial_budget'])
  if initial['run_id']!=p['run_id']:raise ValueError('initial budget history identity mismatch')
 if a.action=='review-development':return dict(status='STOP',reason='NEEDS_FINAL_SCIENTIFIC_ACCEPTANCE',training_complete=all((Path(p['new_output_root'])/'reviews'/f'remaining-{arm}-{seed}.json').exists() for arm,seed in m.ORDER),note='No final bundle/test manifest or release generated until actual independent B-E mechanism/cost/natural inference checks; no test has run.')
 mode=m.select(p,a.phase,a.arm,a.seed)
 if a.action=='review-recovery':
  if not a.recovery_authorization:raise ValueError('explicit recovery authorization required')
  return review_recovery(p,mode,O,a.recovery_authorization)
 return {'plan-stage':plan_stage,'review-allocation':review_allocation,'review-stage':review_stage}[a.action](p,mode,O)
if __name__=='__main__':
 try:print(json.dumps(main(),sort_keys=True))
 except Exception as error:
  print(json.dumps(dict(status='STOP',reason=str(error),exception=type(error).__name__)),flush=True);traceback.print_exc(file=sys.stderr);sys.exit(1)
