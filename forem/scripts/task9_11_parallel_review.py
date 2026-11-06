#!/usr/bin/env python3
"""Independent incremental certificates for isolated task9.11 shards.

Only external control/evidence. Frozen learning source and per-run science are
never edited. Final scientific acceptance is an explicit separate decision.
"""
import argparse,datetime as dt,json,math,sys,hashlib
from pathlib import Path
F=Path(__file__).resolve().parents[1];sys.path.insert(0,str(F/'src'))
from task9_lr import real_batch as b,real_program as m,real_g1 as g
from task9_lr.admission import evaluation_complete,validate_profile
ROLE=b.REVIEWER
SOURCE='b8f3d63b4fb0846156fcfc72663008763a5346d85020daef9025d7f790154c05'
def read(p):return json.loads(Path(p).read_text())
def stream_sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def ref(p):return {'path':str(Path(p).resolve()),'sha256':stream_sha(p)}
def emit(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if read(p)!=v:raise ValueError('immutable certificate conflict: '+str(p))
 else:p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
 return ref(p)
def number(n):
 if isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) or n<0:raise ValueError('finite nonnegative cost required')
 return n
def ns(t):
 base,_,frac=t.rstrip('Z').partition('.')
 return int(dt.datetime.fromisoformat(base).replace(tzinfo=dt.timezone.utc).timestamp())*10**9+int((frac+'000000000')[:9])
def check_authority(path):
 a=read(path)
 for k,v in dict(format='task9-lr-parallel-shards-authorization-v1',status='PASS_PARALLEL_SHARDS',reviewer=ROLE,source_digest=SOURCE,own_episode_quota=2352).items():
  if a.get(k)!=v:raise ValueError('parallel authorization identity: '+k)
 p=b.read_ref(a['protocol']);policy=b.read_ref(a['policy'])
 if a['run_id']!=p['run_id'] or policy['run_id']!=p['run_id'] or policy['source_digest']!=SOURCE or policy['status']!='PASS_FINITE_SHARED_RESOURCE_POLICY':raise ValueError('foreign unified policy')
 if [(j['name'],j['arm'],j['seed']) for j in a['jobs']]!=[('L4718','L',4718),('C4719','C',4719),('L4719','L',4719)]:raise ValueError('scientific job list changed')
 if policy['future_allocation_s']!=sum(policy['allocation_seconds'].values()) or any(policy[k]+policy['future_allocation_s']>policy[limit] for k,limit in [('worker_upper_reserved_s','max_worker_seconds'),('gpu_upper_reserved_s','max_gpu_seconds')]):raise ValueError('duplicate/overallocated global reserve')
 for f,digest in a['adapter_files'].items():
  if b.sha256(f)!=digest:raise ValueError('frozen external shard adapter changed: '+f)
 for j in a['jobs']:
  if j['config']!=p['scientific_configs'][f"{j['arm']}-{j['seed']}"]:raise ValueError('unsealed science configuration')
  b.read_ref(j['config'])
 return a,p,policy

def review_phase(a,p,policy,jobname,phase):
 job=next(j for j in a['jobs'] if j['name']==jobname)
 if phase not in ('profile','remaining'):raise ValueError('unknown phase')
 out=Path(p['new_output_root']);stage=out/'shards'/jobname/phase
 control=read(out/'parallel-shards/state.json')['jobs'][jobname]
 pointer=control['phases'][phase]['result'];rp=Path(pointer['path'])
 if rp.parent.parent!=stage.parent or rp.name!='result.json' or stream_sha(rp)!=pointer['sha256']:raise ValueError('foreign/changed phase result')
 stage=rp.parent;r=read(rp)
 existing=m.AUDIT/'parallel-run-v1/certificates'/jobname/(phase+'.json')
 if existing.exists():
  cert=m.review(ref(existing))
  if cert['evidence'][0]!=ref(rp):raise ValueError('closed result changed after independent review')
  return dict(status='PASS',independent_verdict=ref(existing))
 expected=dict(status='PASS',run_id=p['run_id'],source_digest=SOURCE,job=jobname,phase=phase,arm=job['arm'],seed=job['seed'],episodes_before=0 if phase=='profile' else 196,episodes_after=196 if phase=='profile' else 2352)
 if any(r.get(k)!=v for k,v in expected.items()):raise ValueError('phase boundary/identity incomplete')
 folder=Path(r['folder']).resolve()
 if folder!=out/f"formal-{job['arm']}-seed{job['seed']}":raise ValueError('foreign arm/seed artifact directory')
 st=r['exact_stopped'];state=st['inspect'];uuid=r['gpu_uuid']
 allowed=policy['allowed_gpu_uuids'];index=job['gpu_index']
 if uuid not in allowed or (index!='ANY_FREE' and uuid!=allowed[index]):raise ValueError('unauthorized GPU')
 if not st.get('container_stopped') or state['Id']!=r['container_id'] or state['State']['Running'] or state['State']['Pid'] or state['Image']!=g.IMAGE:raise ValueError('actual exactStopped/image missing')
 requests=state['HostConfig']['DeviceRequests']
 if len(requests)!=1 or requests[0].get('DeviceIDs')!=[uuid]:raise ValueError('exact single-card request missing')
 allocation=(ns(state['State']['FinishedAt'])-ns(state['State']['StartedAt']))/1e9
 outer=number(r['actual_outer_wall_s']);worker=number(r['actual_worker_wall_s']);number(allocation)
 if worker>outer+5 or allocation>outer+60:raise ValueError('actual envelope inconsistent')
 previous=None
 if phase=='remaining':
  previous=b.read_ref(read(out/'shards'/jobname/'profile/review.json')['independent_verdict'])
 failed_cost=sum(number(b.read_ref(x['result'])['actual_outer_wall_s']) for x in control.get('failed_phases',[]))
 used=outer+(previous['worker_enclosing_upper_s'] if previous else 0)+failed_cost
 if used>policy['allocation_seconds'][jobname]+a['control_reserve_s']*2:raise ValueError('job exceeded its unique14h allocation')
 evidence=[ref(rp)]+[x['result'] for x in control.get('failed_phases',[])];extra={'prior_failed_outer_wall_s':failed_cost}
 if phase=='profile':
  summary=b.read_ref(r['summary']);ev=read(folder/'validation-0250000.json');config=b.read_ref(job['config']);cost=validate_profile(summary,ev,config['replay_capacity'])
  restore=b.read_ref(r['profile_restore'])
  if restore.get('steps')!=250000 or restore.get('scientific_limit')!=3000000 or not restore.get('actual_devices'):raise ValueError('original native full restore/device evidence missing')
  if cost['save_max_s']*2+120>a['save_reserve_s']:raise ValueError('indivisible save needs larger reviewed reserve')
  pe=r['profile_evidence']
  keys={'profile_checkpoint','profile_summary','profile_restore','profile_evaluation','checkpoint_costs','interactions','diagnostic_account'}
  if set(pe)!=keys:raise ValueError('complete profile evidence required')
  for k,item in pe.items():
   q=Path(item['path'])
   if q.parent.resolve()!=folder or stream_sha(q)!=item['sha256']:raise ValueError('foreign/changed own profile evidence: '+k)
  # Raw JSONL refs belong only in profile_evidence. Generic evidence is JSON.
  for k in ('profile_summary','profile_restore','profile_evaluation','diagnostic_account'):b.read_ref(pe[k]);evidence.append(pe[k])
  extra.update(cost=cost,profile_evidence=pe)
 else:
  summary=b.read_ref(r['summary']);s=summary['state']
  if s['steps']!=3000000 or s['env_actions']!=3000000 or summary['updates']!=299975 or s.get('unsafe_update'):raise ValueError('original3M final state incomplete')
  for step in range(250000,3000001,250000):
   q=folder/f'validation-{step:07d}.json';ev=read(q);evaluation_complete(ev)
   if ev['step']!=step:raise ValueError('wrong periodic evaluation')
   evidence.append(ref(q))
  for name in ('final.pt','final.actor.pt','final.meta.json'):
   if not (folder/name).is_file():raise ValueError('missing native final bundle: '+name)
 count=sum(json.loads(line)['count'] for path in folder.rglob('episodes-started.jsonl') for line in path.read_text().splitlines())
 if count!=r['episodes_after']:raise ValueError('write-ahead own quota differs from completed cycles')
 if phase=='profile':evaluation_complete(read(folder/'validation-0250000.json'))
 evidence.append(r['summary'])
 v=dict(format='task9-lr-real-program-stage-verdict-v1',status='PASS_COMPLETE',reviewer=ROLE,run_id=p['run_id'],activity=f"{phase}-{job['arm']}-{job['seed']}",source_digest=SOURCE,evaluation_episodes=196 if phase=='profile' else 2156,consumed_transfers=250000 if phase=='profile' else 2750000,exact_container_stopped=True,worker_enclosing_upper_s=outer,actual_worker_wall_s=worker,actual_allocation_s=allocation,worker_enclosing_classification='ACTUAL_DISJOINT_SHARD_ENVELOPE',outer_rootwait_status='DETACHED_CONTROLLER_ACTUAL_TERMINAL',evidence=evidence,**extra)
 vr=emit(m.AUDIT/'parallel-run-v1/certificates'/jobname/(phase+'.json'),v);emit(stage/'review.json',{'independent_verdict':vr});emit(out/'shards'/jobname/phase/'review.json',{'independent_verdict':vr})
 return dict(status='PASS',independent_verdict=vr)

def publish_ordered(a,p):
 out=Path(p['new_output_root']);published=[]
 # C4718 has a separate honest aggregate of failed+successful attempts.
 for arm,seed in m.ORDER:
  for phase in ('profile','remaining'):
   name=f'{phase}-{arm}-{seed}';target=out/'reviews'/(name+'.json')
   if target.exists():
    v=m.review(read(target)['independent_verdict'])
    if v.get('status')!='PASS_COMPLETE' or v.get('activity')!=name or v.get('source_digest')!=SOURCE:raise ValueError('existing predecessor certificate invalid')
    continue
   source=out/'shards'/f'{arm}{seed}'/phase/'review.json'
   if not source.exists():return dict(status='PASS',published=published,waiting_for=name)
   pointer=read(source);v=m.review(pointer['independent_verdict'])
   if v.get('status')!='PASS_COMPLETE' or v.get('activity')!=name or v.get('source_digest')!=SOURCE:raise ValueError('shard certificate invalid')
   emit(target,pointer);published.append(name)
 return dict(status='PASS',published=published,state='NEEDS_FINAL_SCIENTIFIC_ACCEPTANCE')
def main():
 cli=argparse.ArgumentParser();cli.add_argument('--authorization',required=True);cli.add_argument('--action',choices=['review-phase','publish-ordered'],required=True);cli.add_argument('--job');cli.add_argument('--phase');x=cli.parse_args();a,p,policy=check_authority(x.authorization)
 result=review_phase(a,p,policy,x.job,x.phase) if x.action=='review-phase' else publish_ordered(a,p)
 print(json.dumps(result));return 0
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as e:print(json.dumps(dict(status='STOP',error=repr(e))));sys.exit(1)
