"""Append-only measured preparation costs and independent budget generations.

Only protocols frozen with this policy opt in. Static legacy inventories stay
strict. This module grants no execution permission or historical reconciliation.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import time
import threading
from .runtime import sha256
from . import clock, cost_control, gpu_costs

FORMAT='task9-lr-dynamic-costs-v1'
_DEPTH={}


def enabled(p):return 'dynamic_cost_policy' in p


def policy(p):
    v=p['dynamic_cost_policy'];root=Path(p['new_output_root'])/'costs'
    expected=dict(format=FORMAT,root=str(root),event_writer='task9.11.11-cost-owner',
        reviewer='task9.11.12-cost-reviewer',source_format='task9-lr-measured-command-v1')
    if v!=expected:raise ValueError('dynamic cost schema/roots/roles changed')
    return v


def make_policy(p):
    return dict(format=FORMAT,root=str(Path(p['new_output_root'])/'costs'),event_writer='task9.11.11-cost-owner',
        reviewer='task9.11.12-cost-reviewer',source_format='task9-lr-measured-command-v1')


@contextmanager
def locked(p, *, historical=False):
    if not enabled(p):yield;return
    root=Path(policy(p)['root'])
    if root.resolve()!=root:raise ValueError('cost lock root noncanonical/escaped')
    root.mkdir(parents=True,exist_ok=True)
    key=(os.getpid(),threading.get_ident(),str(root))
    if key in _DEPTH:
        _DEPTH[key]+=1
        try:yield
        finally:_DEPTH[key]-=1
        return
    with (root/'cost.lock').open('a') as f:
        cutoff=__import__('datetime').datetime.fromisoformat(p['deadline']).timestamp()-p['save_allowance_s']
        while True:
            if not historical and clock.epoch(p)>=cutoff:raise TimeoutError('global stop/save reserve reached while waiting for cost lock')
            try:
                fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                if clock.epoch(p)>=cutoff:raise TimeoutError('cost lock unavailable at global deadline')
                time.sleep(.01)
        _DEPTH[key]=1
        try:yield
        finally:del _DEPTH[key]


def bound(path):return dict(path=str(path),sha256=sha256(path))


def read_bound(entry):
    path=Path(entry['path'])
    if not path.is_file() or sha256(path)!=entry.get('sha256'):raise ValueError('cost evidence missing/changed: '+str(path))
    return json.loads(path.read_text())


def command_set(p):
    from .continuation import resolve_path
    roots=[resolve_path(r,p) for r in p['external_activity_roots']]
    if any(not r.is_dir() or r.resolve()!=r for r in roots):raise ValueError('cost root missing/noncanonical')
    result={}
    for root in roots:
        if any(root.rglob('*.cost-pending')):raise ValueError('external command still executing; wall UNKNOWN')
        for path in root.rglob('*command.json'):
            if path.is_symlink() or path.resolve()!=path or not path.is_file():raise ValueError('cost command escaped root')
            result[str(path)]=bound(path)
    return result


def inventory(p, *, complete=True, active_control=None):
    """Validate every event/source and compute maximal enclosing intervals once."""
    from .continuation import number, bound_json
    cfg=policy(p);root=Path(cfg['root']);controls=cost_control.inventory(p,active=active_control);actual=command_set(p)
    base=p['continuation'].get('external_cost_inventory',[])
    covered={};base_total=0.;gpu_intervals=[]
    account=bound_json(p['continuation']['accounting_snapshot'],p)
    inherited={e['path'] for e in account.get('command_components',[])}
    inherited_gpu=gpu_costs.evidence(p,account)
    for entry in base:
        path=entry['path']
        if path in covered or actual.get(path)!=entry:raise ValueError('frozen base command missing/duplicate/changed')
        item=read_bound(entry);wall=number(item.get('wall_s'),'frozen command wall')
        attributed=gpu_costs.command(p,item)
        if path in inherited:gpu_costs.require_covered(attributed,inherited_gpu)
        gpu_intervals.extend(attributed)
        covered[path]=entry
        if path not in inherited:base_total+=wall
    if not inherited<=set(covered):raise ValueError('inherited command coverage missing')
    events={};sources=set();source_hashes={e['sha256'] for e in base};event_refs=[]
    event_root=root/'events'
    if event_root.exists() and any(not q.is_file() or q.suffix!='.json' or q.is_symlink() for q in event_root.iterdir()):raise ValueError('unexpected/uncommitted cost event file')
    for path in sorted((root/'events').glob('*.json')):
        e=json.loads(path.read_text());ident=e.get('event_id','')
        if not re.fullmatch(r'[A-Za-z0-9_-]+',ident) or path.stem!=ident or ident in events:raise ValueError('duplicate/invalid cost event ID')
        if e.get('format')!='task9-lr-cost-event-v1' or e.get('run_id')!=p['run_id'] or e.get('protocol_sha256')!=p.get('_sealed_sha256') or e.get('writer')!=cfg['event_writer']:raise ValueError('cost event namespace/schema/writer mismatch')
        if e.get('stage') not in ('prepare','review','g1','gate-evaluate','profile','remaining','final-test'):raise ValueError('cost event stage invalid')
        source=e.get('source',{});sp=source.get('path')
        if sp in covered or sp in sources or source.get('sha256') in source_hashes or actual.get(sp)!=source:raise ValueError('cost event duplicate/missing/changed/outside-root source')
        item=read_bound(source)
        cost_control.validate(p,item.get('control_reservation'),artifact=source,operation='source-publish')
        if e.get('control_reservation')!=active_control:cost_control.validate(p,e.get('control_reservation'),artifact=bound(path),operation='event-append')
        wall=number(e.get('wall_s'),'event measured wall')
        if item.get('format')!=cfg['source_format'] or item.get('status')!='CLOSED' or item.get('wall_s')!=wall or item.get('synthetic_fixture')!=p['continuation']['synthetic_fixture'] or item.get('execution_allowed') is not False:
            raise ValueError('cost command not closed/measured or wall mismatch')
        if not isinstance(item.get('argv'),list) or not item['argv'] or not all(isinstance(a,str) for a in item['argv']):raise ValueError('source command argv missing')
        if isinstance(item.get('exit_code'),bool) or not isinstance(item.get('exit_code'),int):raise ValueError('source actual exit missing')
        start=number(item.get('started_epoch'),'source started');end=number(item.get('finished_epoch'),'source finished')
        if end<start or abs(end-start-wall)>.001 or end>clock.epoch(p)+.001:raise ValueError('source measured interval invalid/unclosed')
        if item.get('stage')!=e['stage'] or item.get('parent_event_id')!=e.get('parent_event_id'):raise ValueError('source stage/nesting mismatch')
        clock.validate_interval(p,item.get('started_clock'),item.get('completed_clock'))
        if item['started_clock']['epoch']!=start or item['completed_clock']['epoch']!=end or abs(item['completed_clock']['monotonic']-item['started_clock']['monotonic']-wall)>1e-8:raise ValueError('source actual measured clock mismatch')
        gpu_intervals.extend(gpu_costs.command(p,item))
        e['_start']=start;e['_end']=end
        sources.add(sp);source_hashes.add(source['sha256']);events[ident]=e;event_refs.append(bound(path));covered[sp]=source
    commits=[];previous=None;committed=[]
    for n,path in enumerate(sorted((root/'event-commits').glob('*.json')),1):
        item=json.loads(path.read_text())
        if path.name!=f'{n:08d}.json' or item.get('generation')!=n or item.get('previous')!=previous or item.get('run_id')!=p['run_id'] or item.get('protocol_sha256')!=p.get('_sealed_sha256'):raise ValueError('cost append journal generation/chain invalid')
        read_bound(item['event']);committed.append(item['event'])
        previous=bound(path);commits.append(previous)
    if sorted(committed,key=lambda r:r['path'])!=event_refs:raise ValueError('cost append journal missing/extra event')
    for ident,e in events.items():
        seen={ident};child=e
        while child.get('parent_event_id') is not None:
            parent=child['parent_event_id']
            if parent in seen or parent not in events:raise ValueError('cost nesting cycle/missing parent')
            seen.add(parent);ancestor=events[parent]
            if child['stage']!=ancestor['stage'] or child['_start']<ancestor['_start'] or child['_end']>ancestor['_end']:raise ValueError('nested cost not enclosed')
            child=ancestor
    if complete and set(covered)!=set(actual):raise ValueError('unreviewed/missing event for external command; complete roots coverage required')
    total=base_total+controls['control_charged_s']+sum(e['wall_s'] for e in events.values() if e.get('parent_event_id') is None)
    return dict(worker_seconds=total,gpu_seconds=gpu_costs.seconds(gpu_intervals),gpu_intervals=gpu_costs.union(gpu_intervals),paths=sorted(covered),accounted_paths=sorted(inherited),
        commands=[actual[k] for k in sorted(actual)],events=event_refs,event_ids=sorted(events),event_commits=commits,**controls)


def measured_command(p, event_id, stage, argv, *, writer, timeout=5, parent_event_id=None, gpu_devices=None):
    """Run only an explicitly supplied finite external command; publish after wait.

    The pending marker blocks review/start/runtime accounting until real wait
    finishes. Source/event owners share the admission lock; publication is
    immutable and its source is always covered by a later independent review.
    """
    entered=clock.capture(p)
    if gpu_devices is None:raise ValueError('GPU attribution UNKNOWN: explicit fixture devices required')
    gpu_costs.evidence(p,dict(synthetic_fixture=True,gpu_evidence=gpu_costs.fixture_evidence(p,entered['epoch'],entered['epoch'],gpu_devices)))
    if writer!=policy(p)['event_writer'] or not re.fullmatch(r'[A-Za-z0-9_-]+',event_id):raise ValueError('invalid measured command owner/ID')
    from .continuation import number
    number(timeout,'external command timeout')
    root=Path(p['external_activity_roots'][0]);source=root/(event_id+'-command.json');pending=root/(event_id+'.cost-pending')
    cost_control.artifact_path(p,dict(path=str(source)),'source-publish')
    with locked(p):
        if source.exists() or pending.exists():raise ValueError('external command identity already consumed')
        control=cost_control.begin(p,'source-publish',started_clock=entered)
        start=clock.capture(p)
        clock.publish(pending,dict(event_id=event_id,status='UNKNOWN',owner=writer,started=start))
    start=clock.capture(p)
    result=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
    finish=clock.capture(p);clock.validate_interval(p,start,finish)
    wall=finish['monotonic']-start['monotonic']
    value=dict(format=policy(p)['source_format'],status='CLOSED',argv=argv,exit_code=result.returncode,
        wall_s=wall,started_epoch=start['epoch'],finished_epoch=finish['epoch'],
        started_clock=start,completed_clock=finish,stdout=result.stdout,stderr=result.stderr,
        gpu_evidence=gpu_costs.fixture_evidence(p,start['epoch'],finish['epoch'],gpu_devices),
        synthetic_fixture=p['continuation']['synthetic_fixture'],execution_allowed=False,stage=stage,parent_event_id=parent_event_id,control_reservation=control)
    with locked(p):
        ref=clock.publish(source,value);pending.unlink()
        cost_control.finish(p,control,ref,payload_s=wall)
        return ref


def publish_source(p, event_id, value, *, writer):
    """Publish an already-completed external measured envelope, charging its tail.

    This does not certify its payload: the independent event/reviewer validates
    the original interval and source fields. Synthetic fixtures stay explicit.
    """
    entered=clock.capture(p)
    with locked(p):
        if writer!=policy(p)['event_writer'] or not re.fullmatch(r'[A-Za-z0-9_-]+',event_id):raise ValueError('invalid source owner/ID')
        control=cost_control.begin(p,'source-publish',started_clock=entered)
        source=Path(p['external_activity_roots'][0])/(event_id+'-command.json')
        cost_control.artifact_path(p,dict(path=str(source)),'source-publish')
        value=dict(value,control_reservation=control)
        ref=clock.publish(source,value);cost_control.finish(p,control,ref)
        return ref


def append_event(p, event_id, stage, source, *, parent_event_id=None, writer):
    entered=clock.capture(p)
    with locked(p):
        cfg=policy(p)
        if writer!=cfg['event_writer']:raise ValueError('cost writer identity mismatch')
        before=inventory(p,complete=False)
        if event_id in before['event_ids'] or source['path'] in before['paths']:raise ValueError('duplicate cost event/source')
        # Validate the proposed event in a private staging directory before its
        # exclusive immutable commit. An incomplete command still blocks starts.
        root=Path(cfg['root']);path=root/'events'/(event_id+'.json')
        if not re.fullmatch(r'[A-Za-z0-9_-]+',event_id):raise ValueError('invalid cost event ID')
        cost_control.artifact_path(p,dict(path=str(path)),'event-append')
        control=cost_control.begin(p,'event-append',started_clock=entered)
        item=read_bound(source)
        event=dict(format='task9-lr-cost-event-v1',event_id=event_id,stage=stage,source=source,
            wall_s=item.get('wall_s'),parent_event_id=parent_event_id,writer=writer,
            run_id=p['run_id'],protocol_sha256=p['_sealed_sha256'],control_reservation=control)
        # Publication is append only, including rejected/unknown evidence. Any
        # invalid committed event permanently blocks this namespace, never drops cost.
        ref=clock.publish(path,event)
        commits=before['event_commits'];n=len(commits)+1
        clock.publish(root/'event-commits'/f'{n:08d}.json',dict(generation=n,previous=commits[-1] if commits else None,event=ref,run_id=p['run_id'],protocol_sha256=p['_sealed_sha256']))
        inventory(p,complete=False,active_control=control)
        cost_control.finish(p,control,ref)
        return ref


def snapshots(p, *, through=None):
    root=Path(policy(p)['root']);previous=None;values=[]
    files=sorted((root/'snapshots').glob('*.json'))
    commits=sorted((root/'snapshot-commits').glob('*.json'))
    if through is not None:
        target=Path(through['path'])
        if target.parent!=root/'snapshots' or not re.fullmatch(r'[0-9]{8}\.json',target.name):raise ValueError('historical snapshot path invalid')
        files=[f for f in files if f.name<=target.name];commits=[f for f in commits if f.name<=target.name]
        if not files or bound(files[-1])!=through:raise ValueError('historical snapshot missing/changed')
    if len(files)!=len(commits):raise ValueError('snapshot publication incomplete/missing generation')
    for n,path in enumerate(files,1):
        if commits[n-1].name!=path.name or json.loads(commits[n-1].read_text())!=bound(path):raise ValueError('snapshot commit binding mismatch')
        v=json.loads(path.read_text())
        if path.name!=f'{n:08d}.json' or v.get('version')!=n or v.get('previous')!=previous or v.get('format')!='task9-lr-budget-snapshot-v1' or v.get('reviewer')!=policy(p)['reviewer'] or v.get('run_id')!=p['run_id'] or v.get('protocol_sha256')!=p.get('_sealed_sha256'):raise ValueError('budget snapshot chain/identity invalid')
        clock.validate_interval(p,v.get('review_started'),v.get('review_completed'))
        if v['review_completed']['epoch']>=__import__('datetime').datetime.fromisoformat(v['expires_at']).timestamp():raise ValueError('snapshot published expired')
        cost_control.validate(p,v.get('control_reservation'),artifact=bound(path),operation='snapshot-review')
        # Original snapshots remain immutable evidence even after natural expiry.
        for e in v.get('commands',[])+v.get('events',[])+v.get('event_commits',[])+v.get('control_journal',[]):read_bound(e)
        previous=bound(path);values.append((previous,v))
    return values


def review(p, *, reviewer, expires_at, container_state=None):
    review_started=clock.capture(p)
    with locked(p):
        cfg=policy(p)
        if reviewer!=cfg['reviewer'] or reviewer==cfg['event_writer']:raise ValueError('independent cost reviewer required')
        values=snapshots(p);expiry=__import__('datetime').datetime.fromisoformat(expires_at).timestamp()
        if not clock.epoch(p)<expiry<=__import__('datetime').datetime.fromisoformat(p['deadline']).timestamp():raise ValueError('snapshot expiry invalid')
        control=cost_control.begin(p,'snapshot-review',started_clock=review_started)
        publication_started=False
        try:
            current=inventory(p,active_control=control)
            from .continuation import inherited_accounting
            from .admission import activity_rows, _check_resources
            inherited=inherited_accounting(p)
            rows=activity_rows(p['new_output_root'],protocol=p,eligibility=False)
            # This private call uses the freshly audited external inventory while
            # retaining every production resource/root/episode/save-reserve check.
            # It deliberately avoids reading the stale previous external snapshot.
            observed=_check_resources(p,p['new_output_root'],external_cost_override=current,container_state=container_state)
            formal={}
            for path in (Path(p['new_output_root'])/'ledger').glob('*.json'):
                entry=json.loads(path.read_text())
                if entry.get('phase') not in ('profile','remaining'):continue
                steps=entry.get('result',{}).get('steps')
                # Synthetic inert workers consume no transfers; real candidates
                # cannot resolve UNKNOWN and never receive execution permission.
                if steps is None and entry.get('synthetic_fixture') is True:steps=0
                from .continuation import number
                steps=number(steps,'formal consumed transfers')
                key=(entry.get('arm'),entry.get('seed'));formal[key]=max(formal.get(key,0),steps)
            consumed=sum(formal.values())
            cumulative={k:observed[k] for k in ('worker_seconds','gpu_seconds','wall_seconds','evaluation_episodes','output_bytes')}
            cumulative['consumed_transfers']=consumed
            remaining=dict(worker_seconds=p['max_worker_seconds']-cumulative['worker_seconds'],
                gpu_seconds=p['max_gpu_seconds']-cumulative['gpu_seconds'],
                wall_seconds=p['max_wall_seconds']-cumulative['wall_seconds'],
                evaluation_episodes=p['max_evaluation_episodes']-cumulative['evaluation_episodes'],
                consumed_transfers=12000000-consumed,output_bytes=p['max_output_bytes']-cumulative['output_bytes'])
            reserved=dict(worker_seconds=observed['reserved_worker_seconds'],gpu_seconds=observed['reserved_gpu_seconds'])
            after_reservations=dict(remaining,**{k:remaining[k]-value for k,value in reserved.items()})
            if any(v<0 for v in after_reservations.values()):raise ValueError('reviewed cumulative cost exceeds budget')
            v=dict(format='task9-lr-budget-snapshot-v1',version=len(values)+1,previous=values[-1][0] if values else None,
                reviewer=reviewer,run_id=p['run_id'],protocol_sha256=p['_sealed_sha256'],expires_at=expires_at,
                review_started=review_started,review_completed=clock.capture(p),control_reservation=control,cumulative=cumulative,cumulative_gpu_intervals=observed['gpu_intervals'],resource_observed_epoch=observed['resource_observed_epoch'],gpu_container_evidence=observed['gpu_container_evidence'],remaining_resource_budget=remaining,reserved_resource_budget=reserved,remaining_after_reservations=after_reservations,closed_activities=[dict(reservation_id=r['reservation_id'],closure_sha256=r['closure_sha256']) for r in rows],**current)
            cost_control.artifact_path(p,dict(path=str(Path(cfg['root'])/'snapshots'/f'{len(values)+1:08d}.json')),'snapshot-review')
            if (Path(cfg['root'])/'snapshot-commits').resolve()!=Path(cfg['root'])/'snapshot-commits':raise ValueError('snapshot commit directory escaped root')
            publication_started=True
            ref=clock.publish(Path(cfg['root'])/'snapshots'/f'{len(values)+1:08d}.json',v)
            clock.publish(Path(cfg['root'])/'snapshot-commits'/f'{len(values)+1:08d}.json',ref)
            cost_control.finish(p,control,ref)
            return ref
        except BaseException as error:
            # A closed validation refusal consumes its own finite metadata
            # session. Publication failures remain pending UNKNOWN; no fallback
            # can certify a snapshot whose bytes/commit/tail are uncertain.
            if not publication_started:
                denial=clock.publish(Path(cfg['root'])/'review-denials'/(Path(control['path']).parent.name+'.json'),
                    dict(status='DENIED',reason=repr(error),control_reservation=control,run_id=p['run_id']))
                cost_control.finish(p,control,denial)
            raise


def validate_snapshot(p, ref=None, *, historical=False, allow_expired=False):
    with locked(p,historical=historical):
        values=snapshots(p,through=ref if historical else None)
        if not values:raise ValueError('independently reviewed budget snapshot missing')
        if ref is None:ref=values[-1][0]
        matches=[v for r,v in values if r==ref]
        if len(matches)!=1:raise ValueError('budget snapshot reference missing/changed')
        v=matches[0]
        if not historical:
            current=inventory(p)
            if ref!=values[-1][0] or any(v.get(k)!=current[k] for k in current):raise ValueError('budget snapshot stale/unreviewed new costs')
            if not allow_expired and clock.epoch(p)>=__import__('datetime').datetime.fromisoformat(v['expires_at']).timestamp():raise ValueError('budget snapshot expired')
        return v


def current_ref(p):
    with locked(p):
        validate_snapshot(p)
        return snapshots(p)[-1][0]


def revoked(p,release_sha):
    root=Path(p['new_output_root'])/'revocations'
    for path in root.glob('*.json'):
        v=json.loads(path.read_text())
        if v.get('format')!='task9-lr-release-revocation-v1' or v.get('run_id')!=p['run_id'] or v.get('protocol_sha256')!=p.get('_sealed_sha256') or v.get('reviewer')!=p['reviewer'] or not v.get('reason'):raise ValueError('invalid explicit revocation event')
        clock.validate_capture(p,v.get('issued_clock'))
        if not re.fullmatch(r'[a-f0-9]{64}',v.get('release_sha256','')):raise ValueError('invalid explicit revocation target')
        if v.get('release_sha256')==release_sha:raise ValueError('release explicitly revoked')


def revoke(p, release_ref, *, reason, reviewer):
    with locked(p):
        if reviewer!=p['reviewer'] or not reason:raise ValueError('explicit independent revocation reviewer/reason required')
        read_bound(release_ref)
        return clock.publish(Path(p['new_output_root'])/'revocations'/(release_ref['sha256']+'.json'),
            dict(format='task9-lr-release-revocation-v1',run_id=p['run_id'],protocol_sha256=p['_sealed_sha256'],
                reviewer=reviewer,reason=reason,release_sha256=release_ref['sha256'],issued_clock=clock.capture(p)))
