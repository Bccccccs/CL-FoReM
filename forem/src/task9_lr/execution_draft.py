"""Real continuation preparation contract, permanently non-executing draft.

User acceptance is separate from measured readiness. This reader cannot issue a
release, reconcile unknown history, change the original window, or create a run.
"""
import copy
import datetime as dt
import json
from pathlib import Path
import re

from . import clock, continuation, real_receipts
from .runtime import ASSET_ROOT, artifact_files, sha256, validate_matrix

PREP_RUN = 't9.11.17-preparation-20261104'
FORMAT = 'task9-lr-execution-draft-v1'
STOP_SHA = '8dbf5405fe038a2b9e1b83971b8e282fb86c4947813ff4481e22d40360a44158'
BASE_SHA = 'b44f7419fff3b0921229dc5f16ff39cd1b899beea0127b065c785ad5a0f49ee0'
APPROVAL = ASSET_ROOT/'doc/agent_logs/task9/task9.11/task9.11.17/user-approval.json'
REVIEW = ASSET_ROOT/'doc/agent_logs/task9/task9.11/release-review-final-check-20261104.json'
ACCOUNT = ASSET_ROOT/'doc/agent_logs/task9/task9.11/task9.11.15/budget-final.stdout.txt'


def is_draft(p):
    return p.get('format') == FORMAT


def bound(path):
    return real_receipts.bound(Path(path).resolve())


def approval(ref):
    if ref.get('path') != str(APPROVAL) or ref != bound(APPROVAL):
        raise ValueError('exact recorded user preparation decision required')
    v = real_receipts.read(ref)
    approved = v.get('approved', {})
    if v.get('format') != 'task9-lr-user-preparation-approval-v1' or v.get('user_text') != '全部按照你的推荐运行' or approved.get('C_host_policy_charge_s') != 1800 or approved.get('C_host_replaced_lower_s') != 618.7961928844452:
        raise ValueError('preparation approval mismatch')
    if v.get('unchanged') != dict(deadline=continuation.DEADLINE, worker_cap_s=208800, output_cap_bytes=2*1024**4):
        raise ValueError('user approval cannot reset resources')
    return v


def policy_accounting(review_ref, account_ref, *, receipts=()):
    # A lower bound plus one approved local charge is not an exact reconciliation.
    review = real_receipts.read(review_ref); old = real_receipts.read(account_ref)
    if review_ref != bound(REVIEW) or account_ref != bound(ACCOUNT):
        raise ValueError('protected original budget provenance required')
    baseline = continuation.number(review['worker_known_lower_s'], 'review worker lower')
    delta = 1800 - 618.7961928844452
    unique = set(); new = []; measured = 0.
    for ref in receipts:
        if ref['path'] in unique:
            raise ValueError('duplicate actual wait receipt')
        unique.add(ref['path']); wait = real_receipts.validate_wait(ref)
        if wait['run_id'] != PREP_RUN or not Path(ref['path']).is_relative_to(APPROVAL.parent):
            raise ValueError('new cost receipt outside approved preparation namespace')
        if wait['stage'] not in ('prepare', 'review'):
            raise ValueError('only new preparation/review costs allowed')
        # These are lower bounds, not an exact worker reconciliation. Without
        # complete parent provenance, interval union safely avoids charging a
        # nested command twice; concurrent-worker/session costs stay UNKNOWN.
        if wait['started_epoch'] < dt.datetime.fromisoformat(review['checked_at']).timestamp():
            raise ValueError('new receipt overlaps inherited budget period')
        new.append(dict(reference=ref, start=wait['started_epoch'], end=wait['finished_epoch'], wall_s=wait['wall_s']))
        measured += wait['wall_s']
    merged=[]
    for row in sorted(new,key=lambda x:x['start']):
        if merged and row['start'] <= merged[-1][1]:merged[-1][1]=max(merged[-1][1],row['end'])
        else:merged.append([row['start'],row['end']])
    lower=sum(end-start for start,end in merged)
    return dict(format='task9-lr-policy-accounting-draft-v1', baseline_review=review_ref,
        baseline_account=account_ref, measurement_lower_s=baseline,
        C_host=dict(classification='USER_APPROVED_POLICY_CHARGE_NOT_MEASUREMENT',
            old_host_lower_s=618.7961928844452, policy_charge_s=1800,
            retained_prelaunch_s=6.389356851577759, increase_s=delta,
            original_integrity='FAIL_INCOMPLETE_SUPERVISION', actual_host_exit_code=None),
        new_measured_waits=new, root_wait_wall_sum_s=measured,
        new_measured_wait_s=lower, new_wait_union_lower_intervals=merged,
        overlap_cost_status='UNKNOWN-parent-or-concurrent-provenance-not-reconciled',
        worker_policy_lower_s=baseline+delta+lower,
        worker_remaining_upper_s=208800-baseline-delta-lower,
        worker_exact_remaining_s=None, gpu_old_exposure_s=old['gpu_old_exposure_s'],
        gpu_exact_remaining_s=None, unknown=list(old['unknown'])+[
            'This preparation and independent-review complete sessions and publisher exits remain UNKNOWN',
            'New root waits do not certify descendants, CPU/GPU allocation or complete control costs'],
        consumed=continuation.CONSUMED, remaining=continuation.REMAINING,
        execution_release=False)


def stages():
    result = [dict(id='new-g1', phase='g1', arm='C', seed=4718,
                   prerequisites=['independent-source-review'], transfers=0, evaluation_episodes=0),
              dict(id='L-recording-4718', phase='gate-evaluate', arm='L', seed=4718,
                   prerequisites=['new-g1', 'independent-legacy-C-limited-acceptance'],
                   transfers=0, evaluation_episodes=196)]
    previous = 'L-recording-4718'
    for arm, seed in continuation.ORDER:
        profile = f'profile-{arm}-{seed}'; remaining = f'remaining-{arm}-{seed}'
        result += [dict(id=profile, phase='profile', arm=arm, seed=seed,
            prerequisites=[previous, 'whole-program-feasibility', 'independent-stage-release'],
            transfers=250000, evaluation_episodes=196),
            dict(id=remaining, phase='remaining', arm=arm, seed=seed,
            prerequisites=[profile, 'own-mature-profile-save-restore-review', 'independent-stage-release'],
            transfers=2750000, evaluation_episodes=2156)]
        previous = remaining
    result.append(dict(id='independent-test', phase='final-test', prerequisites=[previous,
        'development-gates-pass', 'independent-test-manifest-model-freeze', 'independent-stage-release'],
        transfers=0, evaluation_episodes=1184))
    return result


def blockers():
    return ['unresolved-historical-and-current-session-costs',
            'real-control-value-and-publication-exit-evidence',
            'independent-real-device-attribution-and-legacy-time-basis',
            'new-source-independent-review-and-real-G1',
            'new-L-ON-integrity-and-limited-C-combination-review',
            'whole-program-time-storage-feasibility', 'independent-stage-releases']


def build(run_id, *, receipts=()):
    baseline = ASSET_ROOT/'config/task9/task9_11/protocol.json'
    if sha256(baseline) != BASE_SHA:
        raise ValueError('original protocol changed')
    old = json.loads(baseline.read_text())
    approved = bound(APPROVAL); approval(approved)
    configs = validate_matrix()
    source = artifact_files()
    account = policy_accounting(bound(REVIEW), bound(ACCOUNT), receipts=receipts)
    output = ASSET_ROOT/'results/task9'/run_id; logs = ASSET_ROOT/'logs/task9'/run_id
    p = copy.deepcopy(old)
    p.update(format=FORMAT, execution_allowed=False, authorization='Preparation only; SRC-1429',
        run_id=run_id, new_output_root=str(output), new_log_root=str(logs),
        reviewer='task9.11.17.1', stage_releases=[], user_approval=approved,
        baseline_protocol=bound(baseline), real_receipt_policy=real_receipts.POLICY,
        accounting=account, remaining_blockers=blockers(), stage_dag=stages(),
        control_accounting=dict(job='launch-through-actual-root-owner-wait',
            CPU_control='separate measured or explicitly approved charge',
            control_envelope_s=None, proposed_reservations_are_not_used=True),
        source_manifest=source,
        scientific_configs={f'{a}-{s}':bound(ASSET_ROOT/f'config/task9/task9_11/{a}_seed{s}.json') for a,s in configs},
        input_manifest={value:bound(continuation_path(value)) for c in configs.values()
                        for k,value in c.items() if k in ('pool','transfer_pool','evaluation_seeds')},
        legacy_C=dict(stop=bound(ASSET_ROOT/'doc/agent_logs/task9/task9.11/task9.11.4/gate-evaluate-C-4718-FAIL-STOP.json'),
            scientific_acceptance='LIMITED_OLD_C4718_1000_CHECKPOINT_TRAJECTORY_ONLY',
            host_integrity='FAIL_INCOMPLETE_SUPERVISION', new_integrity_required=True,
            PASS_migration=False),
        path_mappings=[dict(host=str(output),container='/output'), dict(host=str(logs),container='/runlogs'),
            dict(host=str(ASSET_ROOT),container='/workspace'),
            dict(host='/home/ybc/projects/CL-FoReM/forem',container='/history')],
        namespace_created=False, independent_review=None,
        readiness='NOT_READY', execution_protocol_status='DRAFT_NOT_RELEASED')
    validate(p)
    return p


def continuation_path(value):
    path = Path(value)
    for inside, host in [('/history', '/home/ybc/projects/CL-FoReM/forem'), ('/workspace', str(ASSET_ROOT))]:
        if path.is_relative_to(inside):
            return Path(host)/path.relative_to(inside)
    if not path.is_absolute():
        raise ValueError('input path must be absolute')
    return path


def validate(p):
    if not is_draft(p) or p.get('execution_allowed') is not False or p.get('readiness') != 'NOT_READY' or p.get('execution_protocol_status') != 'DRAFT_NOT_RELEASED':
        raise ValueError('preparation-only execution draft required')
    approval(p['user_approval'])
    baseline = real_receipts.read(p['baseline_protocol'])
    if p['baseline_protocol'] != bound(ASSET_ROOT/'config/task9/task9_11/protocol.json') or p['baseline_protocol']['sha256'] != BASE_SHA:
        raise ValueError('protected baseline protocol mismatch')
    permitted = {'format','execution_allowed','authorization','run_id','new_output_root','new_log_root','reviewer','stage_releases'}
    for k,v in baseline.items():
        if k not in permitted and p.get(k) != v:
            raise ValueError('original science/resource contract changed: '+k)
    if p.get('started_at') != continuation.START or p.get('deadline') != continuation.DEADLINE or any(p.get(k) != v for k,v in continuation.LIMITS.items()):
        raise ValueError('original T0/deadline/limits changed')
    run_id = p.get('run_id','')
    if not re.fullmatch(r't9\.11-continuation-[A-Za-z0-9_+\-]+',run_id) or run_id == continuation.ORIGINAL_RUN:
        raise ValueError('new continuation namespace required')
    output = ASSET_ROOT/'results/task9'/run_id; logs = ASSET_ROOT/'logs/task9'/run_id
    if p.get('new_output_root') != str(output) or p.get('new_log_root') != str(logs) or output.exists() or logs.exists() or p.get('namespace_created') is not False:
        raise ValueError('draft requires uncreated new namespace')
    expected_mounts=[dict(host=str(output),container='/output'),dict(host=str(logs),container='/runlogs'),
        dict(host=str(ASSET_ROOT),container='/workspace'),dict(host='/home/ybc/projects/CL-FoReM/forem',container='/history')]
    if p.get('path_mappings') != expected_mounts or p.get('reviewer') != 'task9.11.17.1' or p.get('stage_releases') != [] or p.get('independent_review') is not None:
        raise ValueError('draft paths/reviewer/releases changed')
    if p.get('stage_dag') != stages() or p.get('remaining_blockers') != blockers() or p.get('real_receipt_policy') != real_receipts.POLICY:
        raise ValueError('draft stage/gate/device policy changed')
    if p.get('control_accounting') != dict(job='launch-through-actual-root-owner-wait',CPU_control='separate measured or explicitly approved charge',control_envelope_s=None,proposed_reservations_are_not_used=True):
        raise ValueError('unmeasured control value cannot be approved by draft')
    account = p.get('accounting', {})
    expected = policy_accounting(account['baseline_review'], account['baseline_account'],
        receipts=[x['reference'] for x in account.get('new_measured_waits', [])])
    if account != expected:
        raise ValueError('draft historical policy/UNKNOWN/accounting mismatch')
    c = p.get('legacy_C', {})
    stop_ref = bound(ASSET_ROOT/'doc/agent_logs/task9/task9.11/task9.11.4/gate-evaluate-C-4718-FAIL-STOP.json')
    if c != dict(stop=stop_ref,scientific_acceptance='LIMITED_OLD_C4718_1000_CHECKPOINT_TRAJECTORY_ONLY',host_integrity='FAIL_INCOMPLETE_SUPERVISION',new_integrity_required=True,PASS_migration=False):
        raise ValueError('legacy FAIL or limited evidence contract changed')
    if stop_ref['sha256'] != STOP_SHA:raise ValueError('protected original STOP hash changed')
    stop = real_receipts.read(c['stop'])
    if stop.get('actual_host_exit_code') is not None or stop.get('next_stage_release') is not False or stop.get('status') != 'FAIL_INCOMPLETE_SUPERVISION':
        raise ValueError('old STOP integrity changed')
    for e in stop['evidence']:
        if bound(e['path']) != e:
            raise ValueError('old STOP evidence changed')
    if p.get('source_manifest') != artifact_files():
        raise ValueError('draft source identity changed')
    configs = validate_matrix()
    expected_configs={f'{a}-{s}':bound(ASSET_ROOT/f'config/task9/task9_11/{a}_seed{s}.json') for a,s in configs}
    expected_inputs={value:bound(continuation_path(value)) for c in configs.values()
                     for k,value in c.items() if k in ('pool','transfer_pool','evaluation_seeds')}
    if p.get('scientific_configs') != expected_configs or p.get('input_manifest') != expected_inputs:
        raise ValueError('draft input/config manifest incomplete/changed')
    return p


def write(path, run_id, *, receipts=()):
    path = real_receipts.canonical(path)
    review_root = ASSET_ROOT/'doc/agent_logs/task9/task9.11/task9.11.17'
    if not path.is_relative_to(review_root):
        raise ValueError('execution draft must stay in preparation review logs')
    return clock.publish(path, build(run_id, receipts=receipts))
