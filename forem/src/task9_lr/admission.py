"""Task9.11-only stage releases and cumulative fail-closed resource checks."""
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import time
from .runtime import artifact_digest, sha256, ASSET_ROOT
from . import continuation, clock as trusted_clock, costs

STAGES=('g1','smoke512','smoke1000','gate-evaluate','profile','remaining','final-test')


def now():return dt.datetime.now(dt.timezone.utc)


def protocol_read(path):
    p=json.loads(Path(path).read_text())
    if p.get('format')=='task9-lr-real-batch-contract-v1':
        from .real_batch import validate
        return validate(p)
    if p.get('format')=='task9-lr-execution-draft-v1':
        from .execution_draft import validate
        return validate(p)
    if continuation.is_continuation(p):
        continuation.validate_protocol(p);return p
    if p.get('format')!='task9-lr-protocol-v1' or p['run_id']!='t9.11-lr-20261103T171820+0800':raise ValueError('wrong protocol namespace')
    if p['arms']!=['C','L'] or p['seeds']!=[4718,4719] or p.get('automatic_retry') is not False:raise ValueError('matrix/retry mismatch')
    if p['deadline']!='2026-11-06T03:18:20+08:00' or p['max_wall_seconds']!=208800:raise ValueError('window mismatch')
    return p


def evidence(entry,protocol=None):
    if protocol is not None and continuation.is_continuation(protocol):return continuation.evidence(entry,protocol)
    p=Path(entry['path'])
    host=Path('/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-lr-20261103T171820+0800')
    if ASSET_ROOT==Path('/home/ybc/projects/CL-FoReM-task9/forem') and p.is_relative_to('/output'):p=host/p.relative_to('/output')
    if p.is_relative_to('/workspace'):p=ASSET_ROOT/p.relative_to('/workspace')
    if not p.is_file() and p.is_relative_to(host):p=Path('/output')/p.relative_to(host)
    host_workspace=Path('/home/ybc/projects/CL-FoReM-task9/forem')
    if not p.is_file() and p.is_relative_to(host_workspace):p=ASSET_ROOT/p.relative_to(host_workspace)
    historical=Path('/home/ybc/projects/CL-FoReM/forem')
    if not p.is_file() and p.is_relative_to(historical):p=Path('/history')/p.relative_to(historical)
    if not p.is_file() or sha256(p)!=entry['sha256']:raise ValueError('evidence hash mismatch: '+str(p))
    return p


def read_release(path,stage,protocol,*,arm=None,seed=None,clock=None):
    if protocol.get('format')=='task9-lr-real-batch-contract-v1':
        from . import real_program
        if real_program.enabled(protocol):
            if clock is not None:raise ValueError('caller clocks forbidden')
            return real_program.release(path,protocol,phase=stage,arm=arm,seed=seed)
        from .real_batch import stage as real_stage
        if clock is not None or stage!=real_stage(protocol)['phase']:raise ValueError('single real stage only; caller clocks forbidden')
        from .real_g1 import release
        return release(path,protocol,arm=arm,seed=seed)
    if protocol.get('format')=='task9-lr-execution-draft-v1':
        raise ValueError('NOT_READY: execution draft cannot receive a stage release')
    token=json.loads(Path(path).read_text())
    # Explicit times remain a legacy synthetic parser test interface only.
    # Dynamic production admission always reads the bound trusted clock service.
    if clock is not None and (costs.enabled(protocol) or not protocol.get('continuation',{}).get('synthetic_fixture')):
        raise ValueError('caller clock cannot authorize production admission')
    clock=clock or trusted_clock.now(protocol)
    costs.revoked(protocol,sha256(path))
    if costs.enabled(protocol):
        snapshot=costs.validate_snapshot(protocol,token.get('budget_snapshot'))
        for key,value in token.get('remaining_resource_budget',{}).items():
            if key not in snapshot['remaining_resource_budget'] or finite_nonnegative(value,'released '+key)>snapshot['remaining_resource_budget'][key]:raise ValueError('release exceeds reviewed remaining snapshot budget')
        if token.get('budget_snapshot') is None:raise ValueError('release budget snapshot binding missing')
    if continuation.is_continuation(protocol):
        return continuation.validate_release(token,stage,protocol,arm=arm,seed=seed,code_hash=artifact_digest(),clock=clock)
    if stage not in STAGES or token.get('stage')!=stage:raise ValueError('stage mismatch')
    if token.get('run_id')!=protocol['run_id'] or token.get('code_hash')!=artifact_digest():raise ValueError('release namespace/code hash mismatch')
    if token.get('protocol_sha256')!=protocol.get('_sealed_sha256'):raise ValueError('release protocol hash mismatch')
    expiry=dt.datetime.fromisoformat(token['expires_at']);deadline=dt.datetime.fromisoformat(protocol['deadline'])
    if expiry.tzinfo is None or expiry>deadline or clock>=expiry:raise ValueError('release expired/overlong')
    if token.get('reviewer_task')!='task9.11.4' or token.get('status')!='PASS':raise ValueError('actual independent task9.11.4 PASS required')
    for entry in token.get('evidence',[]):evidence(entry)
    if not token.get('evidence'):raise ValueError('no independently bound evidence')
    if stage!='g1' and (token.get('arm')!=arm or token.get('seed')!=seed):raise ValueError('release arm/seed mismatch')
    budget=token.get('remaining_resource_budget',{})
    for key in ('worker_seconds','gpu_seconds','wall_seconds','output_bytes','evaluation_episodes','consumed_transfers'):
        if key not in budget or not isinstance(budget[key],(int,float)) or not math.isfinite(budget[key]) or budget[key]<0:raise ValueError('remaining budget missing/invalid '+key)
    cap=finite_nonnegative(token.get('max_worker_seconds'),'release cap')
    if cap<=0:raise ValueError('nonpositive release cap')
    reserve=token.get('save_reserve_s')
    if isinstance(reserve,bool) or not isinstance(reserve,(int,float)) or not math.isfinite(reserve) or reserve<0 or reserve>=token.get('max_worker_seconds',0):raise ValueError('explicit stage save reserve invalid')
    if token.get('max_worker_seconds',0)<=0 or token['max_worker_seconds']>min(budget['worker_seconds'],budget['gpu_seconds'],budget['wall_seconds']):raise ValueError('worker cap exceeds released budget')
    return token


def load_protocol(path):
    value=protocol_read(path);value['_sealed_sha256']=sha256(path);return value


def finite_nonnegative(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError('unknown/invalid resource: '+label)
    return value


def host_path(path, protocol, output):
    """Resolve frozen container paths on the host; never silently skip a root."""
    if continuation.is_continuation(protocol):return continuation.resolve_path(path,protocol)
    path=Path(path)
    if Path(output).resolve()==Path(protocol['container_output']).resolve():
        for source,target in [(protocol['new_log_root'],protocol.get('container_logs','/runlogs')),
                              (protocol['new_output_root'],protocol['container_output'])]:
            if path.is_relative_to(source):return Path(target)/path.relative_to(source)
    else:
        for source,target in [('/workspace',ASSET_ROOT),('/output',output),('/runlogs',protocol['new_log_root']),('/history','/home/ybc/projects/CL-FoReM/forem')]:
            if path.is_relative_to(source):return Path(target)/path.relative_to(source)
    return path


def candidate_accounting(protocol):
    """A pending engineering policy, never a real execution authorization."""
    if not protocol or not continuation.is_continuation(protocol) or protocol.get('execution_allowed') is not False:
        raise ValueError('full lifecycle accounting UNKNOWN; candidate protocol required')
    value=protocol.get('candidate_accounting',{})
    if value.get('format')!='task9-lr-candidate-accounting-v1' or value.get('job_scope')!='launch-through-actual-owner-wait':
        raise ValueError('full lifecycle accounting UNKNOWN; candidate accounting policy missing')
    envelope=finite_nonnegative(value.get('control_envelope_s'),'control envelope')
    if envelope<=0:raise ValueError('positive control envelope required')
    return value


def candidate_closure(output,path,row,protocol,*,eligibility=True):
    """Read independent actual-wait evidence; never accept a legacy PASS."""
    policy=candidate_accounting(protocol);folder=Path(output)/'supervision'/path.stem
    if (folder/'closure-pending.json').exists() or (folder/'closure-rejected.json').exists():
        raise ValueError('closure publication UNKNOWN/failed; pending/rejected evidence remains')
    closure_path=folder/'closure.json';value=json.loads(closure_path.read_text())
    if value.get('format')!='task9-lr-candidate-closed-v1' or value.get('status')!='CLOSED' or value.get('execution_allowed') is not False:
        raise ValueError('invalid candidate closure')
    for key in ('run_id','phase','arm','seed','reservation_id','reservation_sha256','protocol_sha256','code_hash','release_sha256'):
        if value.get(key)!=row.get(key):raise ValueError('closure identity mismatch: '+key)
    if row.get('run_id')!=protocol['run_id'] or row.get('protocol_sha256')!=protocol.get('_sealed_sha256') or row.get('code_hash')!=artifact_digest():
        raise ValueError('closed activity namespace/protocol/code mismatch')
    release=Path(output)/'releases'/(path.stem+'.json')
    if sha256(release)!=row.get('release_sha256'):raise ValueError('closed release digest mismatch')
    # Historical authorization uses the immutable start capture and actual wait,
    # never a caller-selected clock or the current release/snapshot expiry.
    if eligibility:costs.revoked(protocol,sha256(release))
    if value.get('record_sha256')!=sha256(path) or value.get('lifecycle_sha256')!=sha256(folder/'lifecycle.json'):
        raise ValueError('closure record/lifecycle digest mismatch')
    life=json.loads((folder/'lifecycle.json').read_text())
    if life.get('chain_status')!='PASS' or life.get('reservation_id')!=row['reservation_id'] or life.get('owner',{}).get('exit_code')!=0:
        raise ValueError('closure lacks successful actual wait chain')
    required={'owner-ready.json','guardian-wait.json','guardian-ready.json','watcher-wait.json','watcher-ready.json','terminal.json','activity_record'}
    if set(life.get('evidence_sha256',{}))!=required or set(life.get('waits',{}))!={'guardian','watcher'}:
        raise ValueError('incomplete lifecycle evidence/wait set')
    for name,digest in life['evidence_sha256'].items():
        target=path if name=='activity_record' else folder/name
        if sha256(target)!=digest:raise ValueError('lifecycle evidence changed: '+name)
    reservation=json.loads((folder/'reservation.json').read_text())
    for key in ('run_id','phase','arm','seed','reservation_id','protocol_sha256','code_hash','release_sha256'):
        if reservation['record'].get(key)!=row.get(key):raise ValueError('reservation record identity mismatch: '+key)
    start=reservation.get('admission_clock');finish=life.get('completion_clock')
    trusted_clock.validate_interval(protocol,start,finish)
    if abs(start['monotonic']-reservation['started_monotonic'])>1e-8 or abs(start['epoch']-row['started_epoch'])>1e-8:
        raise ValueError('reservation trusted launch capture mismatch')
    if abs(finish['monotonic']-life['owner_wait_returned_monotonic'])>1e-8:
        raise ValueError('completion not actual owner wait clock capture')
    token=json.loads(release.read_text())
    continuation.validate_release(token,row['phase'],protocol,arm=row['arm'],seed=row['seed'],
        code_hash=artifact_digest(),clock=dt.datetime.fromtimestamp(start['epoch'],dt.timezone.utc))
    end_limit=min(dt.datetime.fromisoformat(token['expires_at']).timestamp(),dt.datetime.fromisoformat(protocol['deadline']).timestamp())
    if start['epoch']+row['cap_s']+protocol['save_allowance_s']>end_limit or finish['epoch']>=end_limit or reservation.get('deadline_epoch')!=end_limit or row['cap_s']!=token['max_worker_seconds']:
        raise ValueError('original completion exceeded release/deadline/cap')
    group_limit=(protocol['g1_max_worker_seconds'] if row['phase']=='g1' else
        protocol['recording_gates_max_worker_seconds'] if row['phase']=='gate-evaluate' else
        protocol['formal_run_max_worker_seconds'] if row['phase'] in ('profile','remaining') else
        protocol['final_test_max_worker_seconds'])
    if row['cap_s']>group_limit:raise ValueError('original stage cap exceeded frozen group allowance')
    if costs.enabled(protocol):
        ref=token.get('budget_snapshot')
        if ref is None or reservation.get('budget_snapshot')!=ref:raise ValueError('historical snapshot identity mismatch')
        snapshot=costs.validate_snapshot(protocol,ref,historical=True)
        if start['epoch']>=dt.datetime.fromisoformat(snapshot['expires_at']).timestamp():raise ValueError('snapshot expired at original start')
    if life['owner']['identity']!=json.loads((folder/'owner-ready.json').read_text())['identity'] or life['owner']['waiter']!=reservation.get('outer'):
        raise ValueError('outer actual wait identity mismatch')
    for role in ('guardian','watcher'):
        waiter=life['owner']['identity'] if role=='guardian' else life['waits']['guardian']['identity']
        wait=life['waits'][role];ready=json.loads((folder/(role+'-ready.json')).read_text())
        if wait['identity']!=ready['identity'] or wait['waiter']!=waiter or wait['reservation_id']!=row['reservation_id'] or ready['reservation_id']!=row['reservation_id']:
            raise ValueError('actual subordinate wait identity mismatch')
        if life['waits'][role]['exit_code']!=0:raise ValueError('nonzero subordinate actual wait')
    if value.get('owner_wait')!=life['owner']:raise ValueError('closure owner wait mismatch')
    job=finite_nonnegative(value.get('job_wall_s'),'job wall')
    job_started=finite_nonnegative(life.get('job_started_monotonic'),'actual launch monotonic')
    waited=finite_nonnegative(life.get('owner_wait_returned_monotonic'),'actual wait returned monotonic')
    if job_started<reservation['started_monotonic'] or waited<job_started or waited>reservation['started_monotonic']+row['cap_s'] or abs(waited-job_started-job)>1e-8:
        raise ValueError('actual launch/wait boundary mismatch')
    control=value.get('control_session',{})
    envelope=finite_nonnegative(control.get('charged_s'),'control charge')
    if envelope!=policy['control_envelope_s'] or control.get('classification')!='engineering-upper-bound-pending-approval':
        raise ValueError('control session policy mismatch')
    if finite_nonnegative(control.get('observed_before_publication_s'),'control observed')>envelope:
        raise ValueError('control session envelope exceeded')
    if job!=life.get('actual_owner_wait_wall_s') or job>finite_nonnegative(row['cap_s'],'closed cap'):
        raise ValueError('job boundary/cap mismatch')
    charged=finite_nonnegative(value.get('charged_wall_s'),'closed charge')
    if abs(charged-job-envelope)>1e-8:raise ValueError('closed charge arithmetic mismatch')
    return dict(row,wall_s=charged,job_wall_s=job,control_charged_s=envelope,closure_sha256=sha256(closure_path))


def activity_rows(output, *, active_name=None, protocol=None, eligibility=True):
    if protocol is None and (Path(output)/'freeze/protocol.json').is_file():protocol=load_protocol(Path(output)/'freeze/protocol.json')
    rows=[];seen=set()
    for path in sorted((Path(output)/'activities').glob('*.json')):
        row=json.loads(path.read_text())
        key=(row['phase'],row['arm'],row['seed'])
        if key in seen or path.stem!='-'.join(map(str,key)):raise ValueError('duplicate/misnamed activity identity')
        seen.add(key)
        if row.get('supervision_format')=='task9-lr-supervision-v2':
            reservation=Path(output)/'supervision'/path.stem/'reservation.json'
            if sha256(reservation)!=row.get('reservation_sha256'):raise ValueError('reservation digest mismatch')
            bound=json.loads(reservation.read_text())
            if bound.get('activity')!=path.stem or bound.get('reservation_id')!=row.get('reservation_id'):
                raise ValueError('reservation identity mismatch')
        if row.get('status') not in ('PASS','started','reserved'):raise ValueError('failed activity blocks all stages: '+path.name)
        if row.get('status')!='PASS':
            if path.stem!=active_name or row.get('supervision_format')!='task9-lr-supervision-v2':
                raise ValueError('unfinished/unknown activity blocks all stages: '+path.name)
            directory=Path(output)/'supervision'/path.stem
            reservation=directory/'reservation.json'
            if sha256(reservation)!=row.get('reservation_sha256'):raise ValueError('active reservation digest mismatch')
            value=json.loads(reservation.read_text())
            if value.get('activity')!=path.stem or value.get('reservation_id')!=row.get('reservation_id') or value.get('cap_s')!=row.get('cap_s'):
                raise ValueError('active reservation identity mismatch')
            for role in ('guardian','watcher'):
                ready=json.loads((directory/(role+'-ready.json')).read_text())
                if ready.get('reservation_id')!=row['reservation_id']:raise ValueError('active watcher identity mismatch')
            require_nonce=Path(output).resolve()==Path('/output') or (protocol is not None and continuation.is_continuation(protocol))
            if require_nonce and os.environ.get('TASK9_LR_RESERVATION')!=row['reservation_id']:
                raise ValueError('worker reservation marker mismatch')
        else:
            if row.get('exit_code')!=0:raise ValueError('terminal activity missing actual exit0')
            finite_nonnegative(row.get('wall_s'),'activity wall '+path.name)
            if row.get('supervision_format')=='task9-lr-supervision-v2':
                receipt=Path(output)/'supervision'/path.stem/'terminal.json'
                value=json.loads(receipt.read_text())
                if value.get('status')!='PASS' or value.get('owner_alive') is not True or value.get('guardian_alive') is not True or value.get('activity')!=path.stem or value.get('record_sha256')!=sha256(path):
                    raise ValueError('independent terminal receipt mismatch')
            # Neither legacy nor v2 PASS certifies the enclosing publication/exit tail.
            # No complete CLOSED accounting format has been authorized.
            if row.get('supervision_format')!='task9-lr-supervision-v2':raise ValueError('full lifecycle accounting UNKNOWN; stage wall is not closed cost')
            row=candidate_closure(output,path,row,protocol,eligibility=eligibility)
        rows.append(row)
    if protocol is not None and continuation.is_continuation(protocol):
        spent={}
        for row in sorted(rows,key=lambda r:r['started_epoch']):
            phase=row['phase']
            if phase=='g1':key=('g1',);limit=protocol['g1_max_worker_seconds']
            elif phase=='gate-evaluate':key=(phase,);limit=protocol['recording_gates_max_worker_seconds']
            elif phase in ('profile','remaining'):key=('formal',row['arm'],row['seed']);limit=protocol['formal_run_max_worker_seconds']
            elif phase=='final-test':key=(phase,);limit=protocol['final_test_max_worker_seconds']
            else:raise ValueError('activity outside continuation stage domain')
            if spent.get(key,0)+finite_nonnegative(row['cap_s'],'original stage cap')>limit:raise ValueError('original cumulative stage allowance exceeded')
            spent[key]=spent.get(key,0)+(row['job_wall_s'] if row['status']=='PASS' else row['cap_s'])
    return rows


def check_resources(protocol, output, *, new_worker_seconds=0, active_name=None, container_state=None, new_gpu_seconds=None):
    if protocol.get('format')=='task9-lr-real-batch-contract-v1':
        from .real_g1 import resources
        return resources(protocol,output,new_worker_seconds=new_worker_seconds,active_name=active_name,container_state=container_state,new_gpu_seconds=new_gpu_seconds)
    if protocol.get('format')=='task9-lr-execution-draft-v1':
        raise ValueError('NOT_READY: draft costs/feasibility are incomplete')
    with costs.locked(protocol):
        return _check_resources(protocol,output,new_worker_seconds=new_worker_seconds,active_name=active_name,container_state=container_state,new_gpu_seconds=new_gpu_seconds)


def _check_resources(protocol, output, *, new_worker_seconds=0, active_name=None, container_state=None, external_cost_override=None, new_gpu_seconds=None):
    from . import gpu_costs
    root=Path(output);clock=trusted_clock.epoch(protocol)
    proposed_gpu=new_worker_seconds if new_gpu_seconds is None else finite_nonnegative(new_gpu_seconds,'new GPU reservation')
    gpu_intervals=[];gpu_reserved=0.
    finite_nonnegative(new_worker_seconds,'new worker reservation')
    cutoff=dt.datetime.fromisoformat(protocol['deadline']).timestamp()
    if clock>=cutoff-protocol['save_allowance_s']:raise TimeoutError('global stop/save reserve reached')
    # The unmodified worker identifies its own host reservation through a pure
    # supervision marker. A stale legacy started row never qualifies.
    if active_name is None and root.resolve()==Path(protocol['container_output']).resolve():
        active_name=os.environ.get('TASK9_LR_ACTIVITY')
    rows=activity_rows(root,active_name=active_name,protocol=protocol,eligibility=False)
    used=0.;reserved=0.
    for row in rows:
        if row['status']=='PASS':used+=finite_nonnegative(row['wall_s'],'closed wall')
        else:
            costs.revoked(protocol,row.get('release_sha256'))
            elapsed=max(0.,clock-finite_nonnegative(row.get('started_epoch'),'started epoch'))
            used+=elapsed
            reserved=max(0.,finite_nonnegative(row.get('cap_s'),'active cap')-elapsed)
            gpu_reserved=reserved
            if continuation.is_continuation(protocol):reserved+=finite_nonnegative(row.get('control_envelope_s'),'active control envelope')
    # Worker admission already has the full host reservation. Do not charge its
    # nested cap a second time. Any different cap is an identity error.
    if active_name and new_worker_seconds:
        own=next((r for r in rows if '-'.join(map(str,(r['phase'],r['arm'],r['seed'])))==active_name),None)
        if own is None or own.get('cap_s')!=new_worker_seconds:raise ValueError('active reservation/cap mismatch')
        new_worker_seconds=0;proposed_gpu=0
    external=0.;external_seen=set()
    for activity_root in ([] if continuation.is_continuation(protocol) else protocol.get('external_activity_roots',[])):
        directory=host_path(activity_root,protocol,root)
        if not directory.is_dir():raise ValueError('external activity root unavailable: '+str(directory))
        for path in directory.rglob('*command.json'):
            if path.resolve() in external_seen:continue
            external_seen.add(path.resolve())
            item=json.loads(path.read_text())
            external+=finite_nonnegative(item.get('wall_s'),'external wall '+str(path))
            gpu_intervals.extend(gpu_costs.command(protocol,item))
    inherited={}
    if continuation.is_continuation(protocol):
        inherited=continuation.inherited_accounting(protocol)
        external_cost=external_cost_override if external_cost_override is not None else continuation.validate_external_costs(protocol,active=bool(active_name))
        external=external_cost['worker_seconds']
        gpu_intervals.extend(inherited['gpu_intervals'])
        gpu_intervals.extend(external_cost['gpu_intervals'])
    used+=external+inherited.get('worker_seconds',0)
    # Unknown historical overhead must remain an explicit admission blocker;
    # no new caller can turn it into zero by omitting command files.
    if protocol.get('unknown_resource_costs'):raise ValueError('historical costs UNKNOWN; independent reconciliation required')
    devices=[];container_basis=None;previous_basis=None
    if costs.enabled(protocol):
        previous_snapshots=costs.snapshots(protocol)
        if previous_snapshots:previous_basis=previous_snapshots[-1][1].get('gpu_container_evidence')
    container_path=root/'container.json'
    if container_path.is_file():
        if not costs.enabled(protocol):raise ValueError('GPU attribution UNKNOWN: static container has no independently reviewed temporal basis')
        record=json.loads(container_path.read_text())
        started=finite_nonnegative(record.get('started_epoch'),'container start')
        if container_state is None and active_name:
            observation=json.loads((root/'supervision'/active_name/'container-observed.json').read_text())
            if not 0<=clock-observation['observed_epoch']<=5:raise ValueError('container observation stale')
            container_state=observation['inspect']
        if container_state is None:
            state_path=root/'container-stopped.json'
            if not state_path.is_file():raise ValueError('GPU exposure UNKNOWN without current inspect or verified stopped receipt')
            container_state=json.loads(state_path.read_text())
        sealed=json.loads((root/'container-inspect.json').read_text()) if (root/'container-inspect.json').is_file() else {}
        devices=gpu_costs.container_allocation(protocol,record,sealed,container_state)
        expected_id=record.get('container_id') or sealed.get('Id')
        if not expected_id or sealed.get('Id')!=expected_id or container_state.get('Id')!=expected_id:
            raise ValueError('GPU container exposure identity mismatch UNKNOWN')
        state=container_state['State']
        if state.get('Running') is True:ended=clock
        elif state.get('Running') is False:
            ended=dt.datetime.fromisoformat(state['FinishedAt'].replace('Z','+00:00')).timestamp()
            if not started<=ended<=clock:raise ValueError('invalid verified container stop time')
        else:raise ValueError('container state UNKNOWN')
        if previous_basis is not None:gpu_costs.validate_container_history(previous_basis,record,sealed,state,ended)
        gpu_intervals.extend(dict(device=d,started_epoch=started,finished_epoch=ended) for d in devices)
        container_basis=dict(record=record,sealed_inspect=sealed,inspect=container_state,resource_observed_epoch=clock)
    elif previous_basis is not None:raise ValueError('GPU reviewed container evidence missing UNKNOWN')
    elif rows or new_worker_seconds or proposed_gpu:
        # Only an explicit inert fixture may execute placeholders without a GPU
        # container record. Real jobs need an existing allocation receipt.
        sealed_path=root/'container-inspect.json'
        if not sealed_path.is_file():raise ValueError('GPU attribution UNKNOWN: job allocation receipt missing')
        devices=gpu_costs.allocation(protocol,json.loads(sealed_path.read_text()))
        if devices:raise ValueError('GPU exposure UNKNOWN: allocation start/stop receipt missing')
    exposure=gpu_costs.seconds(gpu_intervals)
    gpu_reserved=(gpu_reserved+proposed_gpu)*len(devices)
    if used+reserved+new_worker_seconds>protocol['max_worker_seconds']:raise ValueError('cumulative worker cap')
    if exposure+gpu_reserved>protocol['max_gpu_seconds']:raise ValueError('cumulative GPU cap')
    wall=clock-dt.datetime.fromisoformat(protocol['started_at']).timestamp()
    if wall+reserved+new_worker_seconds>protocol['max_wall_seconds']:raise ValueError('cumulative calendar wall cap')
    episodes=inherited.get('evaluation_episodes',0)
    for path in root.rglob('episodes-started.jsonl'):
        with path.open() as stream:
            for line in stream:episodes+=finite_nonnegative(json.loads(line).get('count'),'episode count')
    if episodes>protocol['max_evaluation_episodes']:raise ValueError('cumulative episode cap')
    roots=[root,host_path(protocol['new_log_root'],protocol,root)]
    roots += [host_path(p,protocol,root) for p in protocol.get('external_output_roots',[])]
    files=set()
    for directory in roots:
        if not directory.is_dir():raise ValueError('output accounting root unavailable: '+str(directory))
        files.update(path for path in directory.rglob('*') if path.is_file())
    output_bytes=sum(path.stat().st_size for path in files)+inherited.get('output_bytes',0)
    diagnostic=sum(path.stat().st_size for path in files if any('diagnostics' in x for x in path.parts)
                   or any(path.is_relative_to(directory) for directory in roots[1:]) or path.suffix in ('.jsonl','.json','.txt'))
    diagnostic+=inherited.get('diagnostic_log_bytes',0)
    if output_bytes+40*1024**3>protocol['max_output_bytes']:raise ValueError('cumulative output byte cap plus unchanged full-save reserve')
    if diagnostic>protocol['max_diagnostic_log_bytes']:raise ValueError('diagnostic/log byte cap')
    return dict(worker_seconds=used,reserved_worker_seconds=reserved,evaluation_episodes=episodes,
                wall_seconds=wall,resource_observed_epoch=clock,gpu_container_evidence=container_basis,gpu_seconds=exposure,reserved_gpu_seconds=gpu_reserved,proposed_worker_seconds=new_worker_seconds,proposed_gpu_seconds=proposed_gpu*len(devices),
                resource_reservations=dict(worker_seconds=reserved+new_worker_seconds,gpu_seconds=gpu_reserved),gpu_intervals=gpu_costs.union(gpu_intervals),output_bytes=output_bytes)


def evaluation_complete(value):
    if not value.get('complete'):raise ValueError('evaluation incomplete')
    for key,count in [('validation',100),('transfer',96)]:
        if not value[key].get('complete') or value[key].get('episodes')!=count:raise ValueError('full196 evaluation required')
    return True


# Cost arithmetic copied without scientific changes from task9_opt admission;
# independent review supplies the actual single-lane remaining-time decision.
def validate_profile(summary,evaluation,capacity):
    if summary.get('status')!='paused_profile' or summary.get('steps')!=250000 or summary.get('scientific_limit')!=3000000:
        raise ValueError('profile changed scientific budget or consumed boundary')
    if summary.get('validation_pending') is not None:raise ValueError('ordinary250k evaluation outstanding')
    if summary.get('replay_capacity')!=capacity or summary.get('replay_size')!=capacity:
        raise ValueError('profile replay not mature')
    pending=summary.get('pending')
    remaining=0 if pending is None else len(pending['ids'])-pending['cursor']
    if remaining<0 or summary['env_actions']!=250000+remaining:raise ValueError('pending action ledger mismatch')
    if not summary.get('policy_device','').startswith('cuda') or not summary.get('replay_device','').startswith('cuda'):
        raise ValueError('GPU policy/replay path missing')
    for name in ('actor','critic','alpha'):
        if not any(d.startswith('cuda') for d in summary['optimizer_devices'].get(name,[])):
            raise ValueError('GPU optimizer moments missing: '+name)
    evaluation_complete(evaluation)
    timing=summary['timings'];cp=timing['checkpoint']['max_s'];ev=timing['validation']['max_s']
    mature=summary.get('mature_window')
    if mature is None or mature.get('transfers')!=50000 or mature['wall_s']<=0:
        raise ValueError('mature last50k cost evidence missing')
    nonperiodic=mature['wall_s']-mature['checkpoint_s']-mature['evaluation_s']
    if nonperiodic<=0:raise ValueError('invalid mature window cost decomposition')
    # Remaining11 periodic eval/checkpoints, full final save, explicit restore
    # allowance is supplied by the reviewed policy at admission, not hidden here.
    estimate=nonperiodic/50000*2750000+11*(cp+ev)+cp
    return dict(remaining_proxy_s=estimate,save_max_s=cp,evaluation_max_s=ev,
                mature_nonperiodic_s=nonperiodic,inputs=dict(mature_transfers=50000,remaining_transfers=2750000,remaining_periodic_evaluations=11))


def save_readiness(cost,summary,policy):
    """Check the unchanged STOP reserve against measured save plus reviewed tails.

    A STOP during periodic torch.save can require finishing that current save
    and then saving interrupted.pt. The cancellation/drain bound must therefore
    cover at least the observed indivisible checkpoint, independently of the
    separate exit-save allowance. Reset/evaluation aggregates are cancellable
    internally; their complete wall times are not cancellation lower bounds.
    The policy tail is a reviewed engineering bound, never a measured proof.
    """
    measured_save=float(cost['save_max_s'])
    cancellation=float(policy['cancellation_drain_bound_s'])
    margin=float(policy['emergency_margin_s'])
    allowance=float(policy['save_allowance_s'])
    if not all(math.isfinite(x) and x>0 for x in (measured_save,cancellation,margin,allowance)):
        raise ValueError('invalid shutdown reservation input')
    stages=('checkpoint','candidates','observation','inference','environment_step','consume_transition','diagnostics')
    observed={name:float(summary['timings'][name]['max_s']) for name in stages if name in summary['timings']}
    if not all(math.isfinite(x) and x>=0 for x in observed.values()):raise ValueError('invalid observed cancellation-stage timing')
    indivisible=max([measured_save]+list(observed.values()))
    # Cancellation checks can surround a chain of operations, e.g. consume →
    # diagnostics → periodic checkpoint → first evaluation check. Checking
    # only the largest individual block would not reserve that entire chain.
    chain_floor=sum(observed.values())
    if 'checkpoint' not in observed:chain_floor+=measured_save
    required=measured_save+cancellation+margin
    status='ready'
    if cancellation<chain_floor:status='NOT_READY_cancellation_bound'
    elif allowance<required:status='NOT_READY_save_allowance'
    return dict(status=status,required_allowance_s=required,policy_allowance_s=allowance,
        measured_exit_save_s=measured_save,cancellation_drain_bound_s=cancellation,
        emergency_margin_s=margin,observed_indivisible_max_s=indivisible,observed_chain_floor_s=chain_floor,observed_stages=observed,
        internally_cancellable_aggregates_excluded=['reset','validation'],
        policy_tail_classification='reviewed engineering bound; not a proven runtime upper bound')


def test_jobs(manifest,cube,semantic,config):
    """Accept only independent presealed 200 test + 96 new semantic tasks."""
    if manifest.get('format')!='task9-lr-final-manifest-v1':raise ValueError('wrong final manifest')
    result=[]
    for name,role,source,assets,n in [('random','test','test',cube['maps'],200),('semantic','semantic_test','smoke',semantic['maps'],96)]:
        records=manifest[name];by_id={x['id']:x for x in assets if x['split']==source}
        if len(records)!=n:raise ValueError('test task count')
        rows=[];seen=set()
        for r in records:
            key=(r['map_id'],r['episode_index'])
            if key in seen or r['map_id'] not in by_id or r['role']!=role or r['source_split']!=source or r['stream_index']!=0:raise ValueError('test identity')
            seen.add(key);rows.append(dict(r,entry=by_id[r['map_id']]))
        if set(by_id)!={r['map_id'] for r in rows}:raise ValueError('test map coverage')
        count=1 if name=='random' else 4
        if any({r['episode_index'] for r in rows if r['map_id']==key}!=set(range(count)) for key in by_id):raise ValueError('test episode index coverage')
        result.append(rows)
    old=json.loads(Path(config['evaluation_seeds']).read_text())
    expected={(r['map_id'],r['episode_index'],r['episode_seed'],r.get('stream_index',0)) for r in old['test']}
    actual={(r['map_id'],r['episode_index'],r['seed'],r['stream_index']) for r in result[0]}
    if actual!=expected:raise ValueError('random test differs from fixed held-out seed file')
    collision=manifest.get('collision_check',{})
    if collision.get('status')!='PASS' or not collision.get('sources'):raise ValueError('independent old episode/proposal seed collision audit missing')
    for source in collision['sources']:evidence(source)
    used=set(collision['used_seeds'])
    for key in ('validation','test','semantic_transfer'):
        if not {r['episode_seed'] for r in old[key]}<=used:raise ValueError('collision set omits old evaluation seeds')
    selected=set()
    for r in result[1]:
        n=r.get('nonce')
        if not isinstance(n,int) or isinstance(n,bool) or n<0:raise ValueError('semantic nonce invalid')
        def seed_at(nonce):
            return int(hashlib.sha256(f"task9.11-final-v1|semantic|{r['map_id']}|{r['episode_index']}|{nonce}".encode()).hexdigest()[:8],16)
        if r['seed']!=seed_at(n) or r['seed'] in used or r['seed'] in selected:raise ValueError('semantic hash identity/collision')
        if any(seed_at(k) not in used|selected for k in range(n)):raise ValueError('semantic nonce is not smallest noncolliding')
        selected.add(r['seed'])
    return tuple(result)


def prerequisites(root,stage,arm,seed,protocol=None,*,active_name=None):
    if protocol is not None and protocol.get('format')=='task9-lr-real-batch-contract-v1':
        from . import real_program
        if real_program.enabled(protocol):
            mode=real_program.stage(protocol,stage,arm,seed)
            if active_name!=mode['name']:raise ValueError('program activity marker mismatch')
            return real_program.prerequisites(protocol,mode)
        from .real_batch import stage as real_stage
        mode=real_stage(protocol)
        if (stage,arm,seed)!=(mode['phase'],mode['arm'],4718):raise ValueError('real protocol admits only its single independently released stage')
        return
    root=Path(root);marker=os.environ.get('TASK9_LR_ACTIVITY')
    if active_name is not None and marker and marker!=active_name:
        raise ValueError('explicit active identity differs from environment marker')
    active=active_name if active_name is not None else (marker if root.resolve()==Path('/output') else None)
    if active and active!=f'{stage}-{arm}-{seed}':raise ValueError('cross-stage active marker')
    rows=activity_rows(root,active_name=active,protocol=protocol)
    if protocol is not None and continuation.is_continuation(protocol):return continuation.prerequisites(protocol,stage,arm,seed,rows)
    def passed(phase,a,s):
        if not any(r['phase']==phase and r['arm']==a and r['seed']==s and r.get('status')=='PASS' for r in rows):
            raise ValueError('prerequisite activity not passed: '+f'{phase}-{a}-{s}')
    if stage=='smoke512':passed('g1','C',4718)
    elif stage=='smoke1000':passed('smoke512',arm,seed)
    elif stage=='gate-evaluate':
        if seed!=4718:raise ValueError('only two 4718 recording gates authorized')
        passed('smoke1000',arm,seed)
    elif stage=='profile':
        for a in ('C','L'):
            for s in (4718,4719):passed('smoke1000',a,s)
            passed('gate-evaluate',a,4718)
    elif stage=='remaining':passed('profile',arm,seed)
    elif stage=='final-test':
        for a in ('C','L'):
            for s in (4718,4719):passed('remaining',a,s)
