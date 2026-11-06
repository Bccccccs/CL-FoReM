"""Finite candidate metadata sessions; full envelope charged, never elapsed=0.

The existing proposed control envelope is reserved once per independent source,
append, or review publication. It remains an unapplied engineering policy. The
payload's actual wait is separate; pending/failed publication never becomes 0.
"""
import json
import os
from pathlib import Path
import uuid
from . import clock
from .runtime import sha256


def root_path(p):
    root=Path(p['dynamic_cost_policy']['root']);output=Path(p['new_output_root'])
    if root.resolve()!=root or output.resolve()!=output or not root.is_relative_to(output):raise ValueError('cost control root escaped canonical output')
    return root


def artifact_path(p, ref, operation):
    if not isinstance(ref,dict) or 'path' not in ref:raise ValueError('cost control artifact missing')
    path=Path(ref['path']);root=root_path(p)
    if not path.is_absolute() or path.resolve()!=path or path.is_symlink():raise ValueError('cost control artifact symlink/noncanonical')
    if operation=='source-publish':
        allowed=path.name.endswith('command.json') and any(path.is_relative_to(Path(r)) for r in p['external_activity_roots'])
    elif operation=='event-append':allowed=path.parent==root/'events'
    elif operation=='snapshot-review':allowed=path.parent in (root/'snapshots',root/'review-denials')
    else:allowed=False
    if not allowed:raise ValueError('cost control artifact outside allowed root/operation')
    return path


def begin(p, operation, *, started_clock=None):
    from .continuation import number
    envelope=number(p['candidate_accounting']['control_envelope_s'],'cost control envelope')
    if envelope<=0:raise ValueError('positive cost control envelope required')
    capture=started_clock or clock.capture(p);ident=uuid.uuid4().hex
    base=root_path(p);root=base/'controls'/ident
    if root.resolve()!=root or (base/'control-journal').resolve()!=base/'control-journal':raise ValueError('cost control directories escaped root')
    ref=clock.publish(root/'reservation.json',dict(format='task9-lr-cost-control-v1',
        operation=operation,session_id=ident,run_id=p['run_id'],protocol_sha256=p['_sealed_sha256'],
        started_clock=capture,charged_s=envelope,classification='engineering-upper-bound-pending-approval',applied=False))
    journals=sorted((base/'control-journal').glob('*.json'));n=len(journals)+1
    previous=bound(journals[-1]) if journals else None
    clock.publish(base/'control-journal'/f'{n:08d}.json',dict(generation=n,previous=previous,reservation=ref,run_id=p['run_id'],protocol_sha256=p['_sealed_sha256']))
    clock.publish(root/'pending.json',dict(reservation=ref,status='UNKNOWN'))
    return ref


def bound(path):return dict(path=str(path),sha256=sha256(path))


def read(ref):
    if not isinstance(ref,dict) or 'path' not in ref:raise ValueError('cost control reference missing')
    path=Path(ref['path'])
    if not path.is_absolute() or path.resolve()!=path or path.is_symlink() or not path.is_file() or sha256(path)!=ref.get('sha256'):raise ValueError('cost control evidence missing/changed')
    return json.loads(path.read_text())


def finish(p, ref, artifact, *, payload_s=0):
    from .continuation import number
    value=read(ref);root=Path(ref['path']).parent;start=value['started_clock']
    artifact_path(p,artifact,value['operation'])
    payload=number(payload_s,'cost control payload wait')
    end=clock.capture(p);clock.validate_interval(p,start,end)
    observed=end['monotonic']-start['monotonic']-payload
    if observed<-.000001 or observed>value['charged_s']:raise ValueError('cost control envelope exceeded/invalid payload; UNKNOWN')
    receipt=dict(format='task9-lr-cost-control-completed-v1',reservation=ref,artifact=artifact,
        payload_s=payload,observed_before_publication_s=max(0.,observed),completed_clock=end,status='CLOSED')
    clock.publish(root/'completed.json',receipt)
    def exceeded():return clock.capture(p)['monotonic']-start['monotonic']-payload>value['charged_s']
    if exceeded():raise ValueError('cost control envelope exceeded during publication; UNKNOWN')
    (root/'pending.json').unlink()
    if exceeded():
        try:clock.publish(root/'pending.json',dict(reservation=ref,status='UNKNOWN',reason='cost control tail exceeded'))
        except BaseException as marker_error:
            try:
                try:os.link(root/'completed.json',root/'rejected.json')
                except OSError:pass
                os.unlink(root/'completed.json')
            except BaseException as rollback_error:raise RuntimeError('cost control invalidation UNKNOWN') from rollback_error
            raise ValueError('cost control publication rejected') from marker_error
        raise ValueError('cost control envelope exceeded after marker removal; UNKNOWN')
    return ref


def validate(p, ref, *, artifact=None, operation=None):
    from .continuation import number
    if not isinstance(ref,dict) or 'path' not in ref:raise ValueError('cost control reference missing')
    root=root_path(p)/'controls';path=Path(ref['path'])
    if path.resolve()!=path or path.parent.resolve()!=path.parent or path.parent.parent!=root or path.name!='reservation.json':raise ValueError('cost control reservation path invalid')
    value=read(ref);folder=path.parent
    if value.get('format')!='task9-lr-cost-control-v1' or value.get('session_id')!=folder.name or value.get('run_id')!=p['run_id'] or value.get('protocol_sha256')!=p.get('_sealed_sha256') or value.get('classification')!='engineering-upper-bound-pending-approval' or value.get('applied') is not False or value.get('charged_s')!=p['candidate_accounting']['control_envelope_s']:
        raise ValueError('cost control identity/pending policy mismatch')
    if operation is not None and value.get('operation')!=operation:raise ValueError('cost control operation mismatch')
    clock.validate_capture(p,value.get('started_clock'))
    if (folder/'pending.json').exists() or (folder/'rejected.json').exists():raise ValueError('cost control publication pending/rejected UNKNOWN')
    receipt=read(bound(folder/'completed.json'))
    if receipt.get('format')!='task9-lr-cost-control-completed-v1' or receipt.get('status')!='CLOSED' or receipt.get('reservation')!=ref:raise ValueError('cost control completion identity mismatch')
    clock.validate_interval(p,value['started_clock'],receipt.get('completed_clock'))
    observed=number(receipt.get('observed_before_publication_s'),'cost control observed');payload=number(receipt.get('payload_s'),'cost control payload')
    if observed>value['charged_s'] or abs(receipt['completed_clock']['monotonic']-value['started_clock']['monotonic']-payload-observed)>1e-6:raise ValueError('cost control measured boundary invalid')
    target=receipt.get('artifact')
    artifact_path(p,target,value['operation']);read(target)
    if artifact is not None and target!=artifact:raise ValueError('cost control artifact mismatch')
    return value


def inventory(p, *, active=None):
    base=root_path(p);root=base/'controls';refs=[];total=0.
    for folder in sorted(root.iterdir()) if root.exists() else []:
        if not folder.is_dir() or folder.resolve()!=folder or any(q.name not in {'reservation.json','pending.json','completed.json','rejected.json'} or q.resolve()!=q for q in folder.iterdir()):raise ValueError('unexpected/symlink cost control evidence')
        ref=bound(folder/'reservation.json');value=read(ref)
        if ref==active:
            if value.get('run_id')!=p['run_id'] or value.get('protocol_sha256')!=p['_sealed_sha256']:raise ValueError('active cost control identity mismatch')
        else:validate(p,ref)
        total+=value['charged_s'];refs.append(ref)
    commits=[];previous=None;registered=[]
    for n,path in enumerate(sorted((base/'control-journal').glob('*.json')),1):
        item=read(bound(path))
        if path.name!=f'{n:08d}.json' or item.get('generation')!=n or item.get('previous')!=previous or item.get('run_id')!=p['run_id'] or item.get('protocol_sha256')!=p['_sealed_sha256']:raise ValueError('control reservation journal changed/missing')
        read(item['reservation']);registered.append(item['reservation']);previous=bound(path);commits.append(previous)
    if sorted(registered,key=lambda r:r['path'])!=refs:raise ValueError('control reservation journal incomplete/extra/missing session')
    return dict(control_charged_s=total,control_reservations=refs,control_journal=commits)
