"""Evidence-only GPU allocation intervals, distinct from worker/control costs.

External-command attribution is currently supported only for explicit inert
synthetic fixtures. The production command API has no genuine device attribution
receipt: missing evidence or a real command is UNKNOWN, never inferred CPU-only.
Container allocation uses the existing exact Docker inspect device identity.
"""
import math

FORMAT='task9-lr-gpu-attribution-v1'


def number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise ValueError('GPU attribution UNKNOWN/nonfinite interval')
    return value


def synthetic(p):
    return p.get('execution_allowed') is False and (p.get('continuation',{}).get('synthetic_fixture') is True or p.get('synthetic_fixture') is True)


def fixture_evidence(p, start, end, devices):
    """Explicit fixture input only; never evidence about an actual GPU command."""
    if not synthetic(p):raise ValueError('GPU attribution UNKNOWN: real external command API has no device receipt')
    return dict(format=FORMAT,synthetic_fixture=True,execution_allowed=False,complete=True,
        started_epoch=start,finished_epoch=end,devices=list(devices),
        intervals=[dict(device=d,started_epoch=start,finished_epoch=end) for d in devices])


def evidence(p, item, *, scope=None):
    v=item.get('gpu_evidence')
    if isinstance(v,dict) and v.get('format')=='task9-lr-real-allocation-review-v1':
        from . import real_receipts
        if item.get('synthetic_fixture') is not False or item.get('execution_allowed') is not False:
            raise ValueError('real allocation source flags invalid')
        return real_receipts.reviewed_intervals(p,item,scope=scope)
    if not isinstance(v,dict):raise ValueError('GPU attribution UNKNOWN: evidence missing')
    if not synthetic(p) or item.get('synthetic_fixture') is not True or v.get('synthetic_fixture') is not True or v.get('execution_allowed') is not False:
        raise ValueError('GPU attribution UNKNOWN: real external attribution unsupported')
    if v.get('format')!=FORMAT or v.get('complete') is not True:raise ValueError('GPU attribution UNKNOWN: incomplete evidence')
    start=number(v.get('started_epoch'));end=number(v.get('finished_epoch'))
    from . import clock
    if end<start or end>clock.epoch(p)+.001:raise ValueError('GPU attribution invalid/unclosed scope')
    if scope is not None and (abs(start-scope[0])>.000001 or abs(end-scope[1])>.000001):raise ValueError('GPU attribution/source scope mismatch')
    devices=v.get('devices');intervals=v.get('intervals')
    if not isinstance(devices,list) or any(not isinstance(d,str) or d!=p.get('preferred_gpu_uuid') for d in devices) or len(set(devices))!=len(devices):raise ValueError('GPU attribution unauthorized/ambiguous device')
    if not isinstance(intervals,list):raise ValueError('GPU attribution intervals UNKNOWN')
    for i in intervals:
        if not isinstance(i,dict) or i.get('device') not in devices or number(i.get('started_epoch'))<start or number(i.get('finished_epoch'))>end or i['finished_epoch']<i['started_epoch']:
            raise ValueError('GPU attribution contradictory/outside scope interval')
    merged=union(intervals)
    if {i['device'] for i in merged}!=set(devices) and end>start:raise ValueError('GPU attribution incomplete/contradictory device intervals')
    if not devices and intervals:raise ValueError('GPU attribution CPU scope has allocation intervals')
    return merged


def command(p, item):
    start=number(item.get('started_epoch'));end=number(item.get('finished_epoch'))
    if abs(end-start-number(item.get('wall_s')))>.001:raise ValueError('GPU attribution command wall mismatch')
    return evidence(p,item,scope=(start,end))


def union(intervals):
    by={}
    for i in intervals:
        start=number(i.get('started_epoch'));end=number(i.get('finished_epoch'));device=i.get('device')
        if not isinstance(device,str) or not device or end<start:raise ValueError('GPU attribution invalid interval')
        if end>start:by.setdefault(device,[]).append((start,end))
    result=[]
    for device,spans in sorted(by.items()):
        merged=[]
        for start,end in sorted(spans):
            if merged and start<=merged[-1][1]:merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
            else:merged.append((start,end))
        result.extend(dict(device=device,started_epoch=a,finished_epoch=b) for a,b in merged)
    return result


def require_covered(intervals, inherited):
    if union(inherited+intervals)!=union(inherited):raise ValueError('inherited GPU command attribution contradicts aggregate intervals UNKNOWN')


def seconds(intervals):return sum(i['finished_epoch']-i['started_epoch'] for i in union(intervals))


def allocation(p, inspect):
    requests=inspect.get('HostConfig',{}).get('DeviceRequests')
    if requests==[]:
        if synthetic(p) or p.get('synthetic_fixture') is True:return []
        raise ValueError('GPU attribution UNKNOWN: CPU fixture inspect required')
    if not isinstance(requests,list) or len(requests)!=1:raise ValueError('GPU attribution UNKNOWN: allocation ambiguous')
    request=requests[0]
    if not isinstance(request,dict) or request.get('DeviceIDs')!=[p.get('preferred_gpu_uuid')] or request.get('Count',0)!=0 or not p.get('preferred_gpu_uuid'):
        raise ValueError('GPU attribution UNKNOWN: unauthorized/all-device allocation')
    return [p['preferred_gpu_uuid']]


def container_allocation(p, record, sealed, current):
    """Match launch intent and both inspect receipts, including empty sets.

    The launcher writes gpu_uuid. Legacy omission retains the protocol's
    preferred-device default; explicit null declares no device. Neither an
    absent inspect field nor contradictory evidence proves CPU-only execution.
    """
    declared=record.get('gpu_uuid',p.get('preferred_gpu_uuid'))
    if declared is not None and (not isinstance(declared,str) or not declared or declared!=p.get('preferred_gpu_uuid')):
        raise ValueError('GPU record allocation unauthorized/ambiguous UNKNOWN')
    expected=[] if declared is None else [declared]
    devices=allocation(p,sealed)
    if allocation(p,current)!=devices:
        raise ValueError('GPU allocation differs from sealed inspect UNKNOWN')
    if expected!=devices:
        raise ValueError('GPU record/allocation contradiction UNKNOWN')
    return devices


def validate_container_history(basis, record, sealed, state, ended):
    """An independently reviewed allocation cannot be rewritten or shortened.

    Reuse already stored evidence only; running to stopped is the sole supported
    state progression in one container namespace. A restart needs a new record.
    """
    if record!=basis.get('record') or sealed!=basis.get('sealed_inspect'):
        raise ValueError('GPU container evidence changed since reviewed snapshot UNKNOWN')
    previous=basis.get('inspect',{}).get('State',{})
    if previous.get('Running') is False:
        import datetime as dt
        prior_end=dt.datetime.fromisoformat(previous['FinishedAt'].replace('Z','+00:00')).timestamp()
        if state.get('Running') is not False or ended!=prior_end:
            raise ValueError('GPU verified stopped interval changed/restarted UNKNOWN')
    elif previous.get('Running') is True:
        if ended<number(basis.get('resource_observed_epoch')):
            raise ValueError('GPU observed allocation interval shortened UNKNOWN')
    else:raise ValueError('GPU historical container state UNKNOWN')
