"""Auditable staged release and discrete GPU-lane deadline arithmetic.

These are execution gates. Final independent acceptance remains task9.5.3/root.
"""
import datetime as dt
import json
import math
from pathlib import Path
from .runtime import artifact_digest, sha256, ASSET_ROOT

STOP_AT=dt.datetime.fromisoformat('2026-11-02T07:00:00+08:00')
SUMMARY_AT=dt.datetime.fromisoformat('2026-11-02T08:00:00+08:00')


def now():
    return dt.datetime.now(dt.timezone.utc)


def evidence(entry):
    path=Path(entry['path'])
    # The same mounted artifact is addressed by host and container roots.
    # Rewrite only the known FoReM mount prefix; content identity remains exact.
    if not path.is_file():
        for root in (Path('/home/ybc/projects/CL-FoReM/forem'),Path('/root/mm_husky_ws')):
            if path.is_relative_to(root):
                candidate=ASSET_ROOT/path.relative_to(root)
                if candidate.is_file():path=candidate;break
    if not path.is_file() or sha256(path)!=entry['sha256']:
        raise ValueError('review/evidence hash mismatch: '+str(path))
    return path


def read_release(path,stage,*,now=None):
    token=json.loads(Path(path).read_text())
    clock=now or dt.datetime.now(dt.timezone.utc)
    if token.get('stage')!=stage:raise ValueError('release stage mismatch')
    if token.get('artifact_sha256')!=artifact_digest():raise ValueError('release artifact hash mismatch')
    expiry=dt.datetime.fromisoformat(token['expires_at'])
    if expiry.tzinfo is None or clock>=min(expiry,STOP_AT):raise ValueError('release expired')
    review=token['review']
    if review.get('status')!='PASS' or review.get('reviewer')!='task9.5.3':
        raise ValueError('independent task9.5.3 PASS review required')
    evidence(review)
    if stage=='g1':
        if not 0<float(token['max_worker_s'])<=1800:raise ValueError('G1 budget exceeds authorization')
    elif stage=='training-policy':
        result=json.loads(evidence(token['g1_evidence']).read_text())
        if result.get('status')!='PASS' or result.get('artifact_sha256')!=token['artifact_sha256']:
            raise ValueError('actual G1 evidence required before training')
        for key in ('save_allowance_s','profile_cost_multiplier','profile_restore_allowance_s','poll_s','host_available_floor_bytes','profile_max_worker_s','cancellation_drain_bound_s','emergency_margin_s'):
            if not math.isfinite(token[key]) or token[key]<=0:raise ValueError('invalid policy '+key)
        if token['save_allowance_s']<=token['cancellation_drain_bound_s']+token['emergency_margin_s']:
            raise ValueError('save allowance leaves no positive exit-save reservation')
        if token['profile_cost_multiplier']<1:raise ValueError('profile multiplier cannot discount measured cost')
        if token.get('group_smoke_worker_s')!=4300 or token.get('fullrun_proxy_s')!=43200:
            raise ValueError('policy changes approved smoke/proxy budget')
        if token.get('stop_at')!=STOP_AT.isoformat():raise ValueError('policy changes absolute deadline')
        if token.get('retry_experiments') is not False:raise ValueError('experiment retries forbidden')
        if token.get('groups')!=['U20','E15','R200'] or token.get('seeds')!=[4718,4719]:
            raise ValueError('policy changes approved matrix')
    else:raise ValueError('unknown release stage')
    return token


def discrete_schedule(clock,lane_release,jobs,deadline=STOP_AT,save_allowance_s=0):
    """Assign each indivisible job to earliest-finishing lane, no aggregate-hour shortcut."""
    if not lane_release:raise ValueError('no observed or predicted GPU lanes')
    lanes={int(g):max(clock,t) for g,t in lane_release.items()}
    result=[]
    for job in jobs:
        cost=float(job['worker_s'])
        if not math.isfinite(cost) or cost<=0:raise ValueError('invalid worker cost')
        gpu=min(lanes,key=lambda x:(lanes[x],x));start=lanes[gpu]
        end=start+dt.timedelta(seconds=cost+save_allowance_s)
        admitted=end<=deadline
        result.append(dict(name=job['name'],gpu=gpu,start=start.isoformat(),end=end.isoformat(),
                           worker_s=cost,save_allowance_s=save_allowance_s,
                           status='admissible' if admitted else 'not_started_deadline'))
        # Do not pack a rejected job or silently shorten its scientific budget.
        if admitted:lanes[gpu]=end
    return result


def evaluation_complete(value):
    if not value.get('complete'):raise ValueError('evaluation incomplete')
    for key,count in [('validation',100),('transfer',96)]:
        item=value[key]
        if not item.get('complete') or item.get('episodes')!=count:
            raise ValueError('full196 evaluation required')
    return True


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
