"""Frozen formal/final adapter. Independent evidence grants every real launch.

No scientific modules are imported here. Activity selection is transient argv
context; it never changes the sealed protocol or the native checkpoint contract.
"""
import copy
import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
from . import clock, real_batch as b, real_receipts as r
from .runtime import ASSET_ROOT, artifact_digest, sha256

ADAPTER='REAL_FORMAL_FINAL_ONLY_V1'
ORDER=(('C',4718),('L',4718),('C',4719),('L',4719))
AUTH=b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/resume-authorization-20261104-v1.json'
POLICY=b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/budget-policy-adoption-20261104-v1.json'
NECESSARY=b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/all-necessary-budget-authorization-20261104-v1.json'
SINGLE_GPU=b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/single-gpu-authorization-20261104-v1.json'
AUDIT=b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2'
G1=AUDIT/'REAL-G1-r3-INDEPENDENT-VERDICT-v1.json'
LON=AUDIT/'REAL-LON-INDEPENDENT-VERDICT-v1.json'
G1_SHA='75347054af33b3d10cbd4a66d83f2ef0209cf90d985b7bbc8c7fa4a0b23ce2f5'
LON_SHA='71bdb0802f747daf863cb5c0adf69ee202deef434fff24ee4f8af13edb40d06e'


def enabled(p):return p.get('production_worker_adapter')==ADAPTER


def stages():
    result=[];previous=None
    for arm,seed in ORDER:
        for phase,transfers,episodes in [('profile',250000,196),('remaining',2750000,2156)]:
            name=f'{phase}-{arm}-{seed}'
            result.append(dict(name=name,phase=phase,arm=arm,seed=seed,transfers=transfers,
                evaluation_episodes=episodes,previous=previous,folder=f'formal-{arm}-seed{seed}',tag='program',scope='REAL_FORMAL_FINAL_ONLY'))
            previous=name
    for arm,seed in ORDER:
        name=f'final-test-{arm}-{seed}'
        result.append(dict(name=name,phase='final-test',arm=arm,seed=seed,transfers=0,
            evaluation_episodes=296,previous=previous,folder=f'test-{arm}-seed{seed}',tag='program',scope='REAL_FORMAL_FINAL_ONLY'))
        previous=name
    return result


def stage(p,phase=None,arm=None,seed=None):
    if not enabled(p):raise ValueError('formal/final adapter required')
    if phase is None and arm is None and seed is None:
        name=p.get('_activity') or os.environ.get('TASK9_LR_ACTIVITY')
        matches=[s for s in stages() if s['name']==name]
    else:matches=[s for s in stages() if (s['phase'],s['arm'],s['seed'])==(phase,arm,seed)]
    if len(matches)!=1:raise ValueError('explicit fixed program activity required')
    return matches[0]


def select(p,phase,arm,seed):
    mode=stage(p,phase,arm,seed);p['_activity']=mode['name'];return mode


def review(ref):
    path=Path(ref['path'])
    if not path.is_absolute() or not path.is_relative_to(AUDIT):raise ValueError('independent .18.2 evidence required')
    local=b.local_path(path)
    if local.resolve()!=local or local.is_symlink():raise ValueError('canonical independent original required')
    return b.read_ref(ref)


def configure(p,budget_envelope=None):
    p.update(production_worker_adapter=ADAPTER,science_dispatch_available=True,
        science_dispatch_scope='FORMAL_FINAL_ONLY',max_diagnostic_log_bytes=10*1024**3,
        necessary_budget_authorization=b.bound(NECESSARY),resume_authorization=b.bound(AUTH),single_gpu_authorization=b.bound(SINGLE_GPU),simultaneous_gpu_cards=1,completed_G1=dict(path=str(G1),sha256=G1_SHA),
        completed_LON=dict(path=str(LON),sha256=LON_SHA),
        consumed=dict(smoke_transitions=4000,evaluation_episodes=1176),
        remaining=dict(periodic=9408,final=1184),stage_dag=stages())
    if budget_envelope is not None:
        limits=resource_envelope(p,budget_envelope)
        p['resource_envelope']=budget_envelope
        for key in ('max_worker_seconds','max_gpu_seconds','max_output_bytes','max_diagnostic_log_bytes','deadline','max_wall_seconds'):p[key]=limits[key]
        if 'historical_accounting' in limits:
            p['historical_accounting']=copy.deepcopy(limits['historical_accounting'])
            p['consumed']=copy.deepcopy(limits['historical_accounting']['consumed'])
            p['max_evaluation_episodes']=limits['max_evaluation_episodes']


def resource_envelope(p,ref):
    v=review(ref)
    expected=dict(format='task9-lr-program-resource-envelope-v1',status='APPROVED_FINITE_LIMITS',reviewer=b.REVIEWER,authorization=p['necessary_budget_authorization'],original_started_at=p['started_at'],simultaneous_gpu_cards=1,historical_consumption_retained=True,historical_unknown_preserved=True,scientific_budget_changed=False)
    if any(v.get(k)!=x for k,x in expected.items()) or not v.get('basis'):raise ValueError('independently supported finite resource envelope required')
    for e in v['basis']:b.read_ref(e)
    for key in ('max_worker_seconds','max_gpu_seconds','max_output_bytes','max_diagnostic_log_bytes','max_wall_seconds'):
        if r.number(v.get(key))<=0:raise ValueError('finite positive resource envelope required')
    for key in ('max_output_bytes','max_diagnostic_log_bytes'):
        if not isinstance(v[key],int) or isinstance(v[key],bool):raise ValueError('integer resource byte envelope required')
    end=dt.datetime.fromisoformat(v['deadline']);start=dt.datetime.fromisoformat(p['started_at'])
    if end.tzinfo is None or (end-start).total_seconds()!=v['max_wall_seconds'] or v['max_diagnostic_log_bytes']>v['max_output_bytes']:raise ValueError('resource envelope calendar/storage arithmetic mismatch')
    if 'historical_accounting' in v:
        history=v['historical_accounting']
        expected_history=dict(consumed=dict(smoke_transitions=4000,evaluation_episodes=1372),failed_training_transfers=250000,failed_updates=24975,failed_evaluation_episodes=196,failed_run_id='t9.11-real-program-20261104-r2')
        if any(history.get(k)!=x for k,x in expected_history.items()) or v.get('max_evaluation_episodes')!=11964:raise ValueError('failed r2 consumption must remain charged before unchanged valid future')
        failure=b.read_ref(history['failure_evidence'])
        if failure.get('training_steps')!=250000 or failure.get('updates')!=24975 or failure.get('new_evaluations')!=196:raise ValueError('actual failed training/evaluation evidence mismatch')
        if 'io_write_repair' not in v:raise ValueError('failed-write restart needs exact repaired I/O evidence')
    elif 'io_write_repair' in v:raise ValueError('I/O restart requires the retained failed-consumption account')
    elif 'max_evaluation_episodes' in v:raise ValueError('evaluation total cannot change without explicit failed consumption')
    return v


def validate_contract(p):
    if p.get('necessary_budget_authorization')!=b.bound(NECESSARY):raise ValueError('exact necessary-budget direct authorization required')
    auth_all=b.read_ref(p['necessary_budget_authorization'])
    expected_all=dict(format='task9.11.18-all-necessary-budget-authorization-v1',requires_independent_finite_resource_plan=True,retain_original_T0_all_history_and_UNKNOWN=True,formal_simultaneous_gpu_cards=1,science_unchanged=True,no_new_scientific_retries_or_scale_reduction=True,no_additional_permission_needed_for_reasonably_supported_budget_increase=True)
    if any(auth_all.get(k)!=v for k,v in expected_all.items()):raise ValueError('necessary-budget authorization scope mismatch')
    if 'resource_envelope' in p:
        envelope=resource_envelope(p,p['resource_envelope'])
        if any(p.get(key)!=envelope[key] for key in ('max_worker_seconds','max_gpu_seconds','max_output_bytes','max_diagnostic_log_bytes','deadline','max_wall_seconds')):raise ValueError('sealed protocol differs from independent finite envelope')
        if 'historical_accounting' not in envelope and p.get('max_evaluation_episodes')!=11768:raise ValueError('original global evaluation cap changed without failed account')
        if 'historical_accounting' in envelope and (p.get('historical_accounting')!=envelope['historical_accounting'] or p.get('consumed')!=envelope['historical_accounting']['consumed'] or p.get('max_evaluation_episodes')!=envelope['max_evaluation_episodes']):raise ValueError('sealed failed-consumption accounting changed')
    if p.get('single_gpu_authorization')!=b.bound(SINGLE_GPU) or p.get('simultaneous_gpu_cards')!=1:raise ValueError('exact single-card authorization required')
    single=b.read_ref(p['single_gpu_authorization'])
    if single.get('format')!='task9.11.18-single-gpu-authorization-v1' or single.get('simultaneous_gpu_cards')!=1 or single.get('preferred_gpu_uuid')!=p['preferred_gpu_uuid']:raise ValueError('single physical GPU identity mismatch')
    if p.get('resume_authorization')!=b.bound(AUTH):raise ValueError('exact new direct authorization required')
    auth=b.read_ref(p['resume_authorization'])
    expected=dict(format='task9.11.18-resume-authorization-v1',basis='SRC-1435',diagnostic_log_bytes=10*1024**3,
        storage_bytes=2*1024**4,worker_seconds=208800,gpu_seconds=208800,deadline=b.DEADLINE,
        retain_original_T0_and_all_consumption=True,reuse_passed_G1_LON=True,
        consumed_smoke_transitions=4000,consumed_evaluations=1176,remaining_periodic=9408,remaining_final=1184)
    if any(auth.get(k)!=v for k,v in expected.items()):raise ValueError('new authorization limits mismatch')
    if ('resource_envelope' not in p and p.get('max_diagnostic_log_bytes')!=10*1024**3) or p.get('science_dispatch_scope')!='FORMAL_FINAL_ONLY':raise ValueError('exact formal limits/scope required')
    for key,path,digest,status in [('completed_G1',G1,G1_SHA,'PASS_COMPLETE_REAL_G1_ONLY'),('completed_LON',LON,LON_SHA,'PASS_COMPLETE_REAL_L_ON196_ONLY')]:
        if p.get(key)!=dict(path=str(path),sha256=digest):raise ValueError('completed front gate identity changed')
        v=review(p[key])
        if v.get('reviewer')!=b.REVIEWER or v.get('status')!=status:raise ValueError('completed front gate did not pass')
    # Preserve the original 150 unaffected paths; only the exact independently
    # approved BudgetFile.write repair may replace its prior I/O bytes.
    science=b.read_ref(dict(path=str(b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/parent-science-byte-acceptance.json'),sha256='73642622f79b3b53314dada756026fd09cc8e3415a0b4d2fdc271b7f66db6e81'))
    if len(science['checked'])!=151:raise ValueError('original front gate compatibility inventory incomplete')
    repair_ref=envelope.get('io_write_repair') if 'resource_envelope' in p else None
    repair=review(repair_ref) if repair_ref else None
    if repair is not None:
        expected_repair=dict(format='task9-lr-budgetfile-write-repair-review-v1',status='PASS_IO_ONLY',reviewer=b.REVIEWER,path='src/task9_lr/diagnostics.py',write_only_semantics_unchanged=True,other_150_unchanged=True)
        if any(repair.get(k)!=v for k,v in expected_repair.items()) or not repair.get('evidence'):raise ValueError('exact independently checked write-only repair required')
        for evidence in repair['evidence']:file_ref(evidence)
    for x in science['checked']:
        expected=x['sha256']
        if repair and x['path']==repair['path']:
            if repair.get('old_sha256')!=expected:raise ValueError('I/O repair original identity mismatch')
            expected=repair['new_sha256']
        if sha256(ASSET_ROOT/x['path'])!=expected:raise ValueError('front gate scientific/I/O compatibility changed: '+x['path'])


def checked_budget(p,ref):
    v=review(ref)
    expected=dict(format='task9-lr-real-program-budget-admission-v1',status='PASS_PROGRAM',reviewer=b.REVIEWER,
        run_id=p['run_id'],original_started_at=p['started_at'],deadline=p['deadline'],
        historical_unknown_preserved=True,
        full_program_feasible=True,storage_accounting='HISTORICAL_SNAPSHOT_PLUS_NEW_PATH_GROWTH_ONCE')
    if any(v.get(k)!=x for k,x in expected.items()):raise ValueError('complete independent full program budget required')
    classification=v.get('classification')
    if classification not in ('EVIDENCE_UPPER_BOUND_NOT_EXACT_HISTORY','EVIDENCE_AND_EXPLICIT_AUTHORIZED_POLICY_RESERVE_NOT_EXACT_HISTORY'):raise ValueError('explicit historical evidence/policy classification required')
    if classification=='EVIDENCE_AND_EXPLICIT_AUTHORIZED_POLICY_RESERVE_NOT_EXACT_HISTORY':
        if 'resource_envelope' not in p or v.get('policy_adoption')!=b.bound(POLICY):raise ValueError('explicit authorized finite historical policy required')
        policy=b.read_ref(v['policy_adoption'])
        if policy.get('format')!='task9.11.18-parent-budget-policy-adoption-v1' or policy.get('authority')!=p['necessary_budget_authorization'] or policy.get('retains_all_history_UNKNOWN_FAIL') is not True or policy.get('not_a_stage_release') is not True:raise ValueError('historical policy authority/UNKNOWN preservation mismatch')
        if any(policy.get(key)!=p[key] for key in ('max_worker_seconds','max_gpu_seconds','max_output_bytes','max_diagnostic_log_bytes','deadline')):raise ValueError('finite policy totals differ from sealed resource envelope')
    for key in ('worker_upper_s','gpu_upper_s','open_worker_upper_rate','open_gpu_upper_rate','storage_upper_bytes','diagnostic_upper_bytes'):
        r.number(v.get(key))
    clock.validate_capture(p,v['bound_clock'])
    if v['bound_clock']['epoch']>time.time()+.001:raise ValueError('budget bound in future')
    if not v.get('basis') or not v.get('participants'):raise ValueError('budget provenance/participant identities missing')
    required={'historical-worker','historical-gpu','C-policy','open-participants','background-inventory','full-program-future-reservation','storage'}
    if set(v['basis'])!=required or v.get('rolling_rule')!='EVIDENCE_BOUND_PARTICIPANTS_PLUS_EXPLICIT_STAGE_RESERVE' or v.get('open_rates_exclude_explicit_stage_reservations') is not True:raise ValueError('complete independent resource provenance required')
    for e in v['basis'].values():b.read_ref(e)
    snap=review(v['historical_storage_snapshot'])
    if snap.get('format')!='task9-lr-program-storage-snapshot-v1' or snap.get('status')!='PASS' or snap.get('reviewer')!=b.REVIEWER:raise ValueError('independent deduplicated historical storage snapshot required')
    external=[str(b.HOST_ROOT/Path(path).relative_to('/workspace')) if Path(path).is_relative_to('/workspace') else str(path) for path in p['external_output_roots']]
    if snap.get('covered_external_roots')!=external:raise ValueError('snapshot must explicitly cover all previously scanned external roots')
    files=snap.get('files')
    if not isinstance(files,dict) or not files:raise ValueError('historical path inventory missing')
    total=diagnostic=0
    for path,item in files.items():
        q=Path(path)
        if not q.is_absolute() or not q.is_relative_to(b.HOST_ROOT) or q.resolve()!=q:raise ValueError('canonical historical file identity required')
        n=item.get('bytes')
        if isinstance(n,bool) or not isinstance(n,int) or n<0:raise ValueError('integer snapshot byte count required')
        total+=n
        if item.get('diagnostic') is True:diagnostic+=n
        elif item.get('diagnostic') is not False:raise ValueError('historical diagnostic classification missing')
    if total>v['storage_upper_bytes'] or diagnostic>v['diagnostic_upper_bytes']:raise ValueError('historical snapshot exceeds charged past')
    future=v.get('future_reserved',{})
    if set(future)!={'worker_seconds','gpu_seconds','calendar_seconds','storage_bytes','diagnostic_bytes'}:raise ValueError('complete remaining full-program reservation required')
    for n in future.values():r.number(n)
    if v['worker_upper_s']+future['worker_seconds']>p['max_worker_seconds'] or v['gpu_upper_s']+future['gpu_seconds']>p['max_gpu_seconds'] or v['storage_upper_bytes']+future['storage_bytes']+40*1024**3>p['max_output_bytes'] or v['diagnostic_upper_bytes']+future['diagnostic_bytes']+256*1024**2>p['max_diagnostic_log_bytes'] or v['bound_clock']['epoch']+future['calendar_seconds']>dt.datetime.fromisoformat(p['deadline']).timestamp():raise ValueError('remaining full program cannot fit approved resources')
    return v


def source_review(p,ref):
    v=review(ref)
    expected=dict(format='task9-lr-real-program-source-review-v1',status='PASS',reviewer=b.REVIEWER,
        run_id=p['run_id'],source_digest=p['source_digest'],source_manifest=p['source_manifest'],scope='REAL_FORMAL_FINAL_ONLY')
    if any(v.get(k)!=x for k,x in expected.items()) or not v.get('evidence'):raise ValueError('full formal/final frozen source review required')
    for e in v['evidence']:b.read_ref(e)
    return v


def allocation_root(p,mode=None):
    from .real_g1 import root
    return root(p)/'allocations'/(mode or stage(p))['name']


def allocation_reference(p,mode=None):
    # Tokens always identify HOST evidence. In a worker b.bound reads the
    # /workspace mirror of this same bind mount, never publishes /output refs.
    name=(mode or stage(p))['name']
    return b.bound(Path(p['new_output_root'])/'allocations'/name/'allocation-lease.json')


def receipt_root(p):return b.receipt_root(p)/stage(p)['name']


def expected_before(mode):
    seq=stages();return sum(x['evaluation_episodes'] for x in seq[:seq.index(mode)])


def prerequisites(p,mode,token=None):
    from .real_g1 import root
    out=root(p)
    seq=stages();index=seq.index(mode)
    for previous in seq[:index]:
        path=out/'reviews'/(previous['name']+'.json')
        pointer=json.loads(path.read_text())
        if set(pointer)!={'independent_verdict'}:raise ValueError('stage review pointer must only identify independent original')
        v=review(pointer['independent_verdict'])
        if v.get('format')!='task9-lr-real-program-stage-verdict-v1' or v.get('status')!='PASS_COMPLETE' or v.get('reviewer')!=b.REVIEWER or v.get('run_id')!=p['run_id'] or v.get('activity')!=previous['name'] or v.get('source_digest')!=p['source_digest']:
            raise ValueError('complete independent predecessor verdict required')
        if v.get('evaluation_episodes')!=previous['evaluation_episodes'] or v.get('consumed_transfers')!=previous['transfers'] or v.get('exact_container_stopped') is not True:raise ValueError('predecessor actual quota/closure mismatch')
        r.number(v.get('worker_enclosing_upper_s'))
        if not v.get('evidence'):raise ValueError('predecessor raw evidence missing')
        for e in v['evidence']:b.read_ref(e)
    if token is not None:
        if token.get('expected_evaluation_before')!=expected_before(mode) or token.get('evaluation_reservation')!=mode['evaluation_episodes']:raise ValueError('fixed stage evaluation quota mismatch')
        if index:
            if token.get('predecessor_review')!=json.loads((out/'reviews'/(seq[index-1]['name']+'.json')).read_text())['independent_verdict']:raise ValueError('exact prior independent review binding required')
        elif token.get('completed_LON')!=p['completed_LON'] or token.get('completed_G1')!=p['completed_G1']:raise ValueError('front gate complete reviews required')


def release(path,p,*,phase=None,arm=None,seed=None,infrastructure=False,verify_inputs=True,active_elapsed_s=None):
    from .real_g1 import IMAGE,release_provenance,root
    mode=stage(p,phase,arm,seed) if phase is not None else stage(p)
    if arm not in (None,mode['arm']) or seed not in (None,mode['seed']):raise ValueError('caller stage identity differs')
    token=json.loads(b.local_path(path).read_text());release_provenance(path,token)
    expected=dict(format='task9-lr-real-program-release-v1',status='PASS',reviewer_task=b.REVIEWER,
        run_id=p['run_id'],code_hash=artifact_digest(),protocol_sha256=p.get('_sealed_sha256'),
        stage='infrastructure' if infrastructure else mode['phase'],arm=mode['arm'],seed=mode['seed'],
        intended_activity=mode['name'],automatic_retry=False,image=IMAGE,gpu_uuid=p['preferred_gpu_uuid'])
    if any(token.get(k)!=v for k,v in expected.items()) or not re.fullmatch('[a-f0-9]{64}',p.get('_sealed_sha256','')):raise ValueError('exact independent program stage release required')
    source_review(p,token['source_review']);budget=checked_budget(p,token['budget_review'])
    prerequisites(p,mode,token)
    cap=r.number(token.get('max_worker_seconds'));tail=r.number(token.get('control_reserve_s'));save=r.number(token.get('save_reserve_s'))
    expiry=dt.datetime.fromisoformat(token['expires_at'])
    ceiling=14400 if mode['phase']=='final-test' else 43200
    remaining=cap
    if active_elapsed_s is not None:
        if infrastructure:raise ValueError('infrastructure cannot use active execution admission')
        spent=r.number(active_elapsed_s)
        if spent>=cap:raise ValueError('active stage cap exhausted')
        remaining=cap-spent
    if cap<=25 or cap>ceiling or save>=cap or tail<=0 or expiry.tzinfo is None or expiry>dt.datetime.fromisoformat(p['deadline']) or time.time()+remaining+tail>=expiry.timestamp():raise ValueError('program cap/save/control/expiry invalid')
    # Stage caps cannot escape the original enclosing per-run or all-final caps.
    seq=stages();same=[x for x in seq if x['phase']=='final-test'] if mode['phase']=='final-test' else [x for x in seq if (x['arm'],x['seed'])==(mode['arm'],mode['seed']) and x['phase']!='final-test']
    used=0
    for old in same:
        if seq.index(old)>=seq.index(mode):continue
        v=review(json.loads((root(p)/'reviews'/(old['name']+'.json')).read_text())['independent_verdict']);used+=r.number(v.get('worker_enclosing_upper_s'))
    if used+cap+tail>ceiling:raise ValueError('original enclosing run/final limit exceeded')
    elapsed=max(0,time.monotonic()-budget['bound_clock']['monotonic'])
    worker=budget['worker_upper_s']+budget['open_worker_upper_rate']*elapsed+max(cap+tail,budget['future_reserved']['worker_seconds'])
    gpu_reserve=r.number(token.get('max_gpu_seconds'))
    if infrastructure:
        if gpu_reserve!=cap+tail:raise ValueError('full infrastructure lease must be reserved')
    else:
        if not re.fullmatch('[a-f0-9]{64}',token.get('container_id','')):raise ValueError('full immutable container ID required')
        if token.get('allocation_lease')!=allocation_reference(p,mode):raise ValueError('own activity allocation lease required')
        lease=b.read_ref(token['allocation_lease'])
        if gpu_reserve<max(cap+tail,r.number(lease.get('lease_seconds'))):raise ValueError('entire allocation reserve required')
    gpu=budget['gpu_upper_s']+budget['open_gpu_upper_rate']*elapsed+max(gpu_reserve,budget['future_reserved']['gpu_seconds'])
    if worker>p['max_worker_seconds'] or gpu>p['max_gpu_seconds']:raise ValueError('cumulative program worker/GPU cap exceeded')
    if mode['phase']=='remaining':
        required={'profile_checkpoint','profile_summary','profile_restore','profile_evaluation','checkpoint_costs','interactions','diagnostic_account'}
        refs=token.get('profile_evidence',{})
        if set(refs)!=required:raise ValueError('complete own profile/restore/cost evidence required')
        folder=Path(p['new_output_root'])/mode['folder']
        for key,e in refs.items():
            if not Path(e['path']).is_relative_to(folder):raise ValueError('foreign profile evidence')
            if key=='profile_checkpoint':
                if Path(e['path'])!=folder/'profile.pt':raise ValueError('own full profile required')
                if verify_inputs:file_ref(e)
            elif verify_inputs:file_ref(e)
    if mode['phase']=='final-test':final_admission(p,token,mode['arm'],mode['seed'],verify_files=verify_inputs)
    return token


def file_ref(ref):
    path=b.local_path(ref['path'])
    if not path.is_absolute() or path.resolve()!=path or not path.is_file():raise ValueError('canonical evidence file missing')
    # Stream full replay checkpoints; never allocate their full bytes on host.
    from .real_lon import stream_sha
    if stream_sha(path)!=ref.get('sha256'):raise ValueError('full evidence file hash mismatch')
    return path


def final_admission(p,token,arm,seed,*,verify_files=True):
    dev=review(token['development_review'])
    if dev.get('format')!='task9-lr-real-program-development-verdict-v1' or dev.get('status')!='PASS_B_E' or dev.get('reviewer')!=b.REVIEWER or dev.get('run_id')!=p['run_id'] or dev.get('source_digest')!=p['source_digest']:raise ValueError('independent complete development B-E acceptance required')
    if not dev.get('evidence'):raise ValueError('development original evidence missing')
    for e in dev['evidence']:b.read_ref(e)
    bundle=review(token['final_bundle']);manifest=review(token['test_manifest'])
    if bundle.get('format')!='task9-lr-real-program-final-bundle-v1' or bundle.get('status')!='PASS' or bundle.get('reviewer')!=b.REVIEWER or bundle.get('source_digest')!=p['source_digest'] or bundle.get('run_id')!=p['run_id']:raise ValueError('independent four final checkpoint bundle required')
    if bundle.get('development_review')!=token['development_review'] or bundle.get('test_manifest')!=token['test_manifest']:raise ValueError('final manifest/development binding differs')
    if manifest.get('format')!='task9-lr-final-manifest-v1' or len(manifest.get('random',[]))!=200 or len(manifest.get('semantic',[]))!=96:raise ValueError('fixed final296 tasks required')
    entries=bundle.get('models',{})
    if set(entries)!={f'{a}-{s}' for a,s in ORDER}:raise ValueError('exact four frozen final models required')
    from .real_g1 import root
    for a,s in ORDER:
        key=f'{a}-{s}';entry=entries[key]
        verdict=review(json.loads((root(p)/'reviews'/f'remaining-{a}-{s}.json').read_text())['independent_verdict'])
        if verdict.get('status')!='PASS_COMPLETE' or verdict.get('activity')!=f'remaining-{a}-{s}':raise ValueError('four complete final training verdicts required')
        expected=Path(p['new_output_root'])/f'formal-{a}-seed{s}'/'final.pt'
        if entry.get('steps')!=3000000 or Path(entry['checkpoint']['path'])!=expected or entry.get('configuration')!=p['scientific_configs'][key]:raise ValueError('only own 3M final checkpoint permitted')
        if Path(entry['actor']['path'])!=expected.with_name('final.actor.pt') or Path(entry['metadata']['path'])!=expected.with_suffix('.meta.json'):raise ValueError('own final actor/metadata required')
        if verify_files:
            file_ref(entry['checkpoint']);file_ref(entry['actor']);file_ref(entry['metadata'])
    if token.get('final_checkpoint')!=entries[f'{arm}-{seed}']['checkpoint']:raise ValueError('test token selected wrong model')
    if verify_files:
        config=json.loads(b.local_path(p['scientific_configs'][f'{arm}-{seed}']['path']).read_text())
        check_config=copy.deepcopy(config)
        def mapped(path):
            path=Path(path)
            if ASSET_ROOT!=Path('/workspace'):
                if path.is_relative_to('/history'):return Path('/home/ybc/projects/CL-FoReM/forem')/path.relative_to('/history')
                if path.is_relative_to('/workspace'):return ASSET_ROOT/path.relative_to('/workspace')
            return path
        for key in ('pool','transfer_pool','evaluation_seeds'):check_config[key]=str(mapped(config[key]))
        cube=json.loads(Path(check_config['pool']).read_text());semantic=json.loads(Path(check_config['transfer_pool']).read_text())
        from .admission import test_jobs
        test_jobs(manifest,cube,semantic,check_config)
    return manifest


def validate_profile_restore(sac,replay,state,stored,config):
    if stored!=config or stored.get('total_transfers')!=3000000 or state.get('steps')!=250000 or sac.env_steps!=250000 or state.get('unsafe_update',False) or state.get('validation_pending') is not None:raise ValueError('full profile scientific/RNG continuation boundary invalid')
    from .real_lon import actual_devices
    return actual_devices(sac,replay)


def spec_gate(spec):
    from .real_g1 import release_provenance,IMAGE,root
    p=spec['protocol'];mode=stage(p);name=mode['name'];path=root(p)/'releases'/(name+'.json')
    token=json.loads(path.read_text());release_provenance(path,token)
    expected=dict(format='task9-lr-real-program-release-v1',status='PASS',reviewer_task=b.REVIEWER,
        run_id=p['run_id'],code_hash=p['source_digest'],protocol_sha256=p['_sealed_sha256'],stage=mode['phase'],
        arm=mode['arm'],seed=mode['seed'],intended_activity=name,automatic_retry=False,image=IMAGE,gpu_uuid=p['preferred_gpu_uuid'])
    if any(token.get(k)!=v for k,v in expected.items()) or spec.get('activity')!=name or spec.get('container_id')!=token.get('container_id') or spec['record'].get('release_sha256')!=sha256(path) or not re.fullmatch('[a-f0-9]{64}',token.get('container_id','')):raise ValueError('program sealed cleanup identity mismatch')
    return token


def scan_growth(p,budget):
    """Charge paid historical paths once, and every subsequent byte of growth."""
    from .real_g1 import root
    snap=review(budget['historical_storage_snapshot']);paid=snap['files']
    roots=[root(p),b.local_path(p['new_log_root']),b.local_path(b.HOST_ROOT/'doc/agent_logs/task9/task9.11')]
    files={q.resolve() for directory in roots if directory.exists() for q in directory.rglob('*') if q.is_file()}
    total=diag=0
    for q in files:
        host=b.HOST_ROOT/q.relative_to(ASSET_ROOT) if ASSET_ROOT==Path('/workspace') and q.is_relative_to(ASSET_ROOT) else Path(p['new_output_root'])/q.relative_to('/output') if q.is_relative_to('/output') else Path(p['new_log_root'])/q.relative_to('/runlogs') if q.is_relative_to('/runlogs') else q
        old=paid.get(str(host),{});n=q.stat().st_size
        increment=max(0,n-old.get('bytes',0));total+=increment
        if any('diagnostics' in part for part in q.parts) or q.suffix in ('.json','.jsonl','.txt','.bin') or q.is_relative_to(roots[1]) or q.is_relative_to(roots[2]):
            diag+=max(0,n-(old.get('bytes',0) if old.get('diagnostic') else 0))
    return total,diag


def resource_view(p,token):
    mode=stage(p);budget=checked_budget(p,token['budget_review']);view=copy.deepcopy(p)
    # Original science recorder still scans only the new root/log. All historical
    # evidence roots have already been charged by this independent snapshot.
    view['external_output_roots']=[]
    view['max_evaluation_episodes']=expected_before(mode)+mode['evaluation_episodes']
    view['remaining_global_evaluation_episodes']=10592
    snapshot=review(budget['historical_storage_snapshot'])
    # The unchanged recorder re-counts all new-root/log files. Refund only that
    # scan overlap inside its local view; global past remains fully charged.
    roots=[Path(p['new_output_root']),Path(p['new_log_root'])]
    overlap=sum(x['bytes'] for path,x in snapshot['files'].items() if any(Path(path).is_relative_to(q) for q in roots))
    diag_overlap=sum(x['bytes'] for path,x in snapshot['files'].items() if x['diagnostic'] and any(Path(path).is_relative_to(q) for q in roots))
    view['max_output_bytes']=p['max_output_bytes']-budget['storage_upper_bytes']+overlap
    view['max_diagnostic_log_bytes']=p['max_diagnostic_log_bytes']-budget['diagnostic_upper_bytes']+diag_overlap
    if p['max_evaluation_episodes']-p['consumed']['evaluation_episodes']!=10592 or min(view['max_output_bytes'],view['max_diagnostic_log_bytes'])<=0:raise ValueError('program remaining resources invalid')
    return view


def resources(p,output,*,new_worker_seconds=0,active_name=None,container_state=None,new_gpu_seconds=None):
    from .real_g1 import root
    b.validate(p);mode=stage(p);name=mode['name'];out=root(p)
    active_name=active_name or os.environ.get('TASK9_LR_ACTIVITY')
    if active_name!=name or Path(output).resolve()!=out.resolve():raise ValueError('program resource identity mismatch')
    spec=json.loads((out/'supervision'/name/'reservation.json').read_text())
    sealed=spec_gate(spec)
    if spec['protocol'].get('_activity')!=name or spec['record'].get('phase')!=mode['phase'] or spec['record'].get('arm')!=mode['arm'] or spec['record'].get('seed')!=mode['seed']:raise ValueError('program active spec identity mismatch')
    if spec['record']['cap_s']!=sealed['max_worker_seconds']:raise ValueError('program active cap changed')
    elapsed=time.monotonic()-r.number(spec.get('started_monotonic'))
    if elapsed<0:raise ValueError('program active clock in future')
    token=release(out/'releases'/(name+'.json'),p,verify_inputs=False,active_elapsed_s=elapsed)
    if r.number(new_worker_seconds) not in (0,token['max_worker_seconds']) or new_gpu_seconds is not None and r.number(new_gpu_seconds) not in (0,token['max_worker_seconds']):raise ValueError('program reservation cap mismatch')
    if spec['record']['release_sha256']!=sha256(out/'releases'/(name+'.json')) or spec['record']['cap_s']!=token['max_worker_seconds']:raise ValueError('program reservation changed')
    if ASSET_ROOT==Path('/workspace') and os.environ.get('TASK9_LR_RESERVATION')!=spec['reservation_id']:raise ValueError('program worker reservation nonce mismatch')
    if container_state is not None:
        if container_state.get('Id')!=token['container_id']:raise ValueError('program container mismatch')
        validate_single_gpu_allocation(container_state,p)
    budget=checked_budget(p,token['budget_review']);growth,diag=scan_growth(p,budget)
    total=budget['storage_upper_bytes']+growth;diagnostic=budget['diagnostic_upper_bytes']+diag+256*1024**2
    if total+40*1024**3>p['max_output_bytes'] or diagnostic>p['max_diagnostic_log_bytes']:raise ValueError('program storage/diagnostic reserve exceeds cap')
    episodes=sum(json.loads(line)['count'] for path in out.rglob('episodes-started.jsonl') for line in path.open())
    before=expected_before(mode)
    if episodes<before or episodes>before+mode['evaluation_episodes'] or p['consumed']['evaluation_episodes']+episodes>p['max_evaluation_episodes']:raise ValueError('program write-ahead evaluation quota exceeded')
    return dict(worker_seconds=budget['worker_upper_s'],gpu_seconds=budget['gpu_upper_s'],evaluation_episodes=p['consumed']['evaluation_episodes']+episodes,output_bytes=total,diagnostic_log_bytes=diagnostic,classification='INDEPENDENT_CONSERVATIVE_UPPER_BOUND')


def validate_single_gpu_allocation(state,p):
    requests=state.get('HostConfig',{}).get('DeviceRequests')
    if not isinstance(requests,list) or len(requests)!=1 or requests[0].get('DeviceIDs')!=[p['preferred_gpu_uuid']]:raise ValueError('exactly one authorized physical GPU allocation required')


def prepare(p,infrastructure_release):
    from .real_g1 import root,IMAGE
    b.validate(p);mode=stage(p);token=release(infrastructure_release,p,infrastructure=True)
    out=root(p);logs=Path(p['new_log_root']);allocation=allocation_root(p)
    if not out.exists():
        if logs.exists():raise ValueError('program log namespace consumed')
        out.mkdir(parents=True);logs.mkdir(parents=True)
        for name in ('freeze','activities','supervision','releases','reviews','tmp','allocations'):(out/name).mkdir()
        frozen={k:v for k,v in p.items() if k not in ('_sealed_sha256','_activity')}
        clock.publish(out/'freeze/protocol.json',frozen)
    if sha256(out/'freeze/protocol.json')!=p['_sealed_sha256']:raise ValueError('program frozen protocol mismatch')
    for name,ref in p['scientific_configs'].items():
        target=out/'freeze'/(name.replace('-','_seed')+'.json')
        if not target.exists():target.write_bytes(b.local_path(ref['path']).read_bytes())
        if sha256(target)!=ref['sha256']:raise ValueError('program frozen scientific config mismatch')
    if allocation.exists() or (out/'activities'/(mode['name']+'.json')).exists():raise ValueError('activity namespace consumed; no retry')
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
    if p['preferred_gpu_uuid'] in apps:raise ValueError('program preferred GPU occupied')
    allocation.mkdir()
    clock.publish(allocation/'infrastructure.json',dict(status='RESERVED',run_id=p['run_id'],activity=mode['name'],release=b.bound(infrastructure_release),automatic_retry=False,started_clock=clock.capture(p)))
    lease=token['max_worker_seconds']+token['control_reserve_s'];cutoff=min(dt.datetime.fromisoformat(p['deadline']).timestamp(),dt.datetime.fromisoformat(token['expires_at']).timestamp(),time.time()+lease)
    clock.publish(allocation/'allocation-lease.json',dict(lease_seconds=lease,admission_deadline_epoch=cutoff,infrastructure_release=b.bound(infrastructure_release),classification='CONSERVATIVE_ADMISSION_CUTOFF_NOT_OBSERVED_DAEMON_EXIT'))
    name='forem-task9-program-'+p['_sealed_sha256'][:10]+'-'+mode['name']
    command=['docker','run','-d','--name',name,'--cidfile',str(allocation/'container.cid'),'--gpus','device='+p['preferred_gpu_uuid'],'--user',f'{os.getuid()}:{os.getgid()}','--read-only','--network','none','--shm-size','2g']
    for host,inside,ro in [(str(ASSET_ROOT),'/workspace',True),('/home/ybc/projects/CL-FoReM/forem','/history',True),(str(out),'/output',False),(str(logs),'/runlogs',False)]:command+=['--mount',f'type=bind,src={host},dst={inside}'+(',readonly' if ro else '')]
    for env in ['PYTHONDONTWRITEBYTECODE=1','PYTHONUNBUFFERED=1','PYTHONPATH=/workspace/src','CUDA_VISIBLE_DEVICES=0','TASK9_PHYSICAL_GPU_UUID='+p['preferred_gpu_uuid'],'OMP_NUM_THREADS=2','OPENBLAS_NUM_THREADS=2','TMPDIR=/output/tmp']:command+=['--env',env]
    command+=['--workdir','/output','--entrypoint','python3',IMAGE,'-I','-S','-c','import time;time.sleep(max(0,min('+repr(lease)+','+repr(cutoff)+'-time.time())))']
    wait=r.wait_command(receipt_root(p)/'infrastructure-launch',['sg','docker','-c',shlex.join(command)],cwd=ASSET_ROOT.parent,run_id=p['run_id'],stage='prepare',timeout=token['control_reserve_s'],sources=[out/'freeze/protocol.json']+[ASSET_ROOT/x for x in p['source_manifest']])
    actual=r.validate_wait(wait);ident=Path(actual['stdout']['path']).read_text().strip()
    if actual['exit_code']!=0 or not re.fullmatch('[a-f0-9]{64}',ident):
        clock.publish(allocation/'infrastructure-failure.json',dict(status='ALLOCATION_UNKNOWN_NO_RETRY',launch_wait=wait,reserve_retained_s=token['max_gpu_seconds'],automatic_retry=False));raise RuntimeError('program allocation failed; reserve retained, no retry')
    observation=r.observe_container(receipt_root(p)/'infrastructure-inspect',ident,run_id=p['run_id']);state,_=r.inspection(observation)
    validate_single_gpu_allocation(state,p)
    clock.publish(allocation/'container-inspect.json',state)
    clock.publish(allocation/'container.json',dict(container_id=ident,name=state['Name'].lstrip('/'),image=IMAGE,gpu_uuid=p['preferred_gpu_uuid'],launch_wait=wait,observation=observation,infrastructure_release=b.bound(infrastructure_release)))
    return dict(container_id=ident,activity=mode['name'],observation=observation,launch_wait=wait,stage_release='REQUIRED')
