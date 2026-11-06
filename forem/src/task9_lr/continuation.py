"""Non-executing continuation namespace adapter; no model/environment imports.

Candidate admission is inspectable by production readers. Only an isolated,
explicit synthetic JSON fixture can have resolved decisions and exact old costs.
Neither that fixture nor a real candidate grants execution permission.
"""
import datetime as dt
import json
import math
from pathlib import Path
import re
import tempfile

from .runtime import ASSET_ROOT, sha256

FORMAT = 'task9-lr-continuation-candidate-v1'
ORIGINAL_RUN = 't9.11-lr-20261103T171820+0800'
START = '2026-11-03T17:18:20+08:00'
DEADLINE = '2026-11-06T03:18:20+08:00'
LIMITS = dict(max_wall_seconds=208800, max_worker_seconds=208800,
              max_gpu_seconds=208800, max_output_bytes=2*1024**4,
              max_diagnostic_log_bytes=8*1024**3)
CONSUMED = dict(smoke=4000, smoke_env_actions=4000, updates=300,
                evaluation_episodes=980, formal=0, final_test=0)
REMAINING = dict(smoke=0, formal=12000000, evaluation_episodes=10788,
                 L_ON=196, formal_validation=9408, final_test=1184, extra_C_ON=0)
ORDER = [['C',4718], ['L',4718], ['C',4719], ['L',4719]]
DECISIONS = {'C-gate-reuse', 'full-cost-boundary', 'continuation-admission'}


def is_continuation(protocol):
    return protocol.get('format') == FORMAT


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or value < 0:
        raise ValueError('UNKNOWN/nonfinite continuation resource: '+label)
    return value


def absolute(value):
    path = Path(value)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('absolute traversal-free declared path required')
    return path


def resolve_path(path, protocol, *, container=None):
    """Map only declared mounts, longest prefix first; never existence fallback."""
    path = absolute(path)
    mounts = protocol['path_mappings']
    if container is None:
        container = ASSET_ROOT == Path('/workspace')
    pairs = [(absolute(m['host']), absolute(m['container'])) for m in mounts]
    for host, inside in sorted(pairs, key=lambda p: len(p[0].parts), reverse=True):
        if path.is_relative_to(host):
            return inside/path.relative_to(host) if container else path
    for host, inside in sorted(pairs, key=lambda p: len(p[1].parts), reverse=True):
        if path.is_relative_to(inside):
            return path if container else host/path.relative_to(inside)
    raise ValueError('path outside declared continuation mounts: '+str(path))


def evidence(entry, protocol):
    path = resolve_path(entry['path'], protocol)
    if not path.is_file() or sha256(path) != entry.get('sha256'):
        raise ValueError('continuation evidence hash mismatch: '+str(path))
    return path


def bound_json(entry, protocol):
    return json.loads(evidence(entry, protocol).read_text())


def assert_execution_allowed(protocol):
    if is_continuation(protocol) or protocol.get('execution_allowed') is False:
        raise ValueError('NOT_READY: non-executing continuation candidate; no Docker/worker/CLI execution')


def validate_protocol(protocol):
    if not is_continuation(protocol) or protocol.get('execution_allowed') is not False:
        raise ValueError('non-executing continuation candidate required')
    p = protocol; c = p.get('continuation', {})
    if c.get('format') != 'task9-lr-continuation-adapter-v1':
        raise ValueError('continuation adapter missing')
    name = p.get('run_id','')
    if not re.fullmatch(r't9\.11-continuation-[A-Za-z0-9_+\-]+', name) or name == ORIGINAL_RUN:
        raise ValueError('new continuation namespace required')
    if p.get('started_at') != START or p.get('deadline') != DEADLINE or any(p.get(k) != v for k,v in LIMITS.items()):
        raise ValueError('original T0/deadline/58h/2TiB limits changed')
    if p.get('arms') != ['C','L'] or p.get('seeds') != [4718,4719] or p.get('formal_order') != ORDER or p.get('automatic_retry') is not False:
        raise ValueError('continuation matrix/retry changed')
    if p.get('reviewer') != 'task9.11.10' or c.get('reviewer') != p['reviewer']:
        raise ValueError('exact continuation reviewer identity required')
    if c.get('consumed') != CONSUMED or c.get('remaining') != REMAINING or p.get('max_evaluation_episodes') != 11768:
        raise ValueError('inherited episode/transfer allocation changed')
    if p.get('smoke_consumed') != 4000 or p.get('formal_consumed') != 12000000 or p.get('max_formal_transfers') != 3000000:
        raise ValueError('inherited interaction limits changed')
    if c.get('legacy_PASS_migration') is not False or c.get('legacy_C_integrity') != 'FAIL_INCOMPLETE_SUPERVISION':
        raise ValueError('legacy FAIL/PASS migration forbidden')
    workspace = absolute(c['host_workspace'])
    output = workspace/'results/task9'/name; logs = workspace/'logs/task9'/name
    if absolute(p['new_output_root']) != output or absolute(p['new_log_root']) != logs:
        raise ValueError('new output/log namespace mismatch')
    expected = [dict(host=str(output),container='/output'),dict(host=str(logs),container='/runlogs'),
                dict(host=str(workspace),container='/workspace'),dict(host=c['host_history'],container='/history')]
    if p.get('path_mappings') != expected or p.get('container_output') != '/output' or p.get('container_logs') != '/runlogs':
        raise ValueError('explicit host/container mounts mismatch')
    history = absolute(c['host_history'])
    if history == workspace or history.is_relative_to(workspace) or workspace.is_relative_to(history):
        raise ValueError('history and active workspace overlap')
    fixture = c.get('synthetic_fixture')
    if not isinstance(fixture, bool):
        raise ValueError('explicit synthetic fixture flag required')
    if fixture and (not workspace.is_relative_to(Path(tempfile.gettempdir())) or workspace == Path(tempfile.gettempdir())):
        raise ValueError('synthetic fixture must use an isolated temporary workspace')
    if fixture and (workspace.resolve()!=workspace or history.resolve()!=history or not history.is_relative_to(workspace.parent)):
        raise ValueError('synthetic fixture mounts must stay in their canonical temporary workspace')
    if not fixture and workspace != Path('/home/ybc/projects/CL-FoReM-task9/forem'):
        raise ValueError('real baseline workspace mismatch')
    for key, expected_path in [('baseline_protocol', workspace/'config/task9/task9_11/protocol.json'),
                               ('legacy_stop', workspace/'doc/agent_logs/task9/task9.11/task9.11.4/gate-evaluate-C-4718-FAIL-STOP.json')]:
        if resolve_path(c[key]['path'],p,container=False) != expected_path:
            raise ValueError('protected baseline/STOP path mismatch')
    old = bound_json(c['baseline_protocol'],p)
    if old.get('format') != 'task9-lr-protocol-v1' or old.get('run_id') != ORIGINAL_RUN:
        raise ValueError('wrong original protocol lineage')
    for k in ('started_at','deadline',*LIMITS):
        if old.get(k) != p[k]:raise ValueError('baseline budget/window mismatch: '+k)
    changed={'format','run_id','new_output_root','new_log_root','authorization','reviewer',
             'external_activity_roots','external_output_roots','unknown_resource_costs'}
    for key,value in old.items():
        if key not in changed and p.get(key) != value:
            raise ValueError('original scientific/resource contract changed: '+key)
    if not fixture and (c['baseline_protocol']['sha256'] != 'b44f7419fff3b0921229dc5f16ff39cd1b899beea0127b065c785ad5a0f49ee0'
                        or c['legacy_stop']['sha256'] != '8dbf5405fe038a2b9e1b83971b8e282fb86c4947813ff4481e22d40360a44158'):
        raise ValueError('protected original protocol/STOP identity changed')
    stop = bound_json(c['legacy_stop'],p)
    if stop.get('run_id') != ORIGINAL_RUN or stop.get('status') != 'FAIL_INCOMPLETE_SUPERVISION' or stop.get('next_stage_release') is not False:
        raise ValueError('legacy STOP must remain failed and unreleased')
    for entry in stop.get('evidence',[]): evidence(entry,p)
    account = bound_json(c['accounting_snapshot'],p)
    if account.get('original_run_id') != ORIGINAL_RUN or account.get('consumed') != CONSUMED or account.get('remaining') != REMAINING:
        raise ValueError('accounting lineage/allocation mismatch')
    if account.get('started_at') != START or account.get('deadline') != DEADLINE or account.get('original_limits') != LIMITS:
        raise ValueError('accounting original window/limits changed')
    if fixture:
        if account.get('format') != 'task9-lr-synthetic-accounting-v1' or account.get('synthetic_fixture') is not True:
            raise ValueError('synthetic ledger cannot import real historical UNKNOWN')
    else:
        if account.get('format') != 'task9-lr-cumulative-budget-lower-bound-v2' or not account.get('unknown') or account.get('worker_exact_remaining_s') is not None or account.get('execution_release') is not False:
            raise ValueError('real historical UNKNOWN must be preserved')
    decisions = c.get('pending_user_decisions',[])
    if len(decisions) != len(DECISIONS) or {x.get('id') for x in decisions} != DECISIONS:
        raise ValueError('explicit complete continuation decisions required')
    status = 'SYNTHETIC_FIXTURE_ONLY' if fixture else 'PENDING_USER_DECISION'
    if any(x.get('status') != status or x.get('applied') is not False for x in decisions):
        raise ValueError('unapproved continuation acceptance decisions')
    policy=p.get('candidate_accounting',{})
    if policy.get('format') != 'task9-lr-candidate-accounting-v1' or policy.get('job_scope') != 'launch-through-actual-owner-wait' or number(policy.get('control_envelope_s'),'control envelope') <= 0:
        raise ValueError('explicit finite candidate accounting policy required')
    if p.get('stage_releases') != []:
        raise ValueError('candidate cannot carry execution releases')
    # Roots are frozen, including all preparation/review generations, not only .3/.4.
    expected_root=str(workspace/'doc/agent_logs/task9/task9.11')
    if p.get('external_activity_roots') != [expected_root] or p.get('external_output_roots') != [expected_root]:
        raise ValueError('complete preparation/review roots required')
    from . import clock, costs
    clock.chain(p)
    if costs.enabled(p):costs.policy(p)
    return p


def inherited_accounting(protocol):
    validate_protocol(protocol)
    c=protocol['continuation'];account=bound_json(c['accounting_snapshot'],protocol)
    if not c['synthetic_fixture'] or account.get('unknown'):
        raise ValueError('historical costs UNKNOWN; candidate cannot reconcile or charge zero')
    exact=account.get('exact_costs',{})
    result={key:number(exact.get(key),'inherited '+key) for key in
            ('worker_seconds','gpu_seconds','evaluation_episodes','output_bytes','diagnostic_log_bytes')}
    from . import gpu_costs
    result['gpu_intervals']=gpu_costs.evidence(protocol,account)
    if abs(gpu_costs.seconds(result['gpu_intervals'])-result['gpu_seconds'])>1e-6:raise ValueError('inherited GPU aggregate/interval contradiction UNKNOWN')
    if result['evaluation_episodes'] != 980:
        raise ValueError('old 980 evaluation episodes must be charged')
    return result


def validate_external_costs(protocol, *, active=False):
    """Require exact frozen command set; unknown/new/changed external cost blocks."""
    from . import costs
    if costs.enabled(protocol):return costs.validate_snapshot(protocol,allow_expired=active)
    c=protocol['continuation']; inventory=c.get('external_cost_inventory',[])
    roots=[resolve_path(p,protocol) for p in protocol['external_activity_roots']]
    if any(not r.is_dir() for r in roots):raise ValueError('external preparation/review root missing')
    actual={str(p.resolve()) for root in roots for p in root.rglob('*command.json')}
    declared={str(evidence(e,protocol).resolve()) for e in inventory}
    if len(declared) != len(inventory) or declared != actual:
        raise ValueError('external preparation/review command inventory incomplete or stale')
    account=bound_json(c['accounting_snapshot'],protocol)
    accounted={str(evidence(e,protocol).resolve()) for e in account.get('command_components',[])}
    if not accounted <= actual:raise ValueError('accounted historical commands missing from frozen inventory')
    from . import gpu_costs
    total=0.;gpu_intervals=[];inherited_gpu=gpu_costs.evidence(protocol,account)
    for entry in inventory:
        path=evidence(entry,protocol);item=json.loads(path.read_text())
        wall=number(item.get('wall_s'),'external wall '+str(path))
        attributed=gpu_costs.command(protocol,item)
        if str(path.resolve()) in accounted:gpu_costs.require_covered(attributed,inherited_gpu)
        gpu_intervals.extend(attributed)
        if str(path.resolve()) not in accounted:total+=wall
    return dict(worker_seconds=total,gpu_seconds=gpu_costs.seconds(gpu_intervals),gpu_intervals=gpu_costs.union(gpu_intervals),paths=sorted(actual),accounted_paths=sorted(accounted))


def jobs(protocol, phase):
    validate_protocol(protocol)
    if phase=='prepare':return []
    if phase=='smoke-and-gates':return [('g1','C',4718),('gate-evaluate','L',4718)]
    if phase=='train':return [(stage,arm,seed) for arm,seed in protocol['formal_order'] for stage in ('profile','remaining')]
    if phase=='final-test':return [('final-test',arm,seed) for arm,seed in protocol['formal_order']]
    raise ValueError('unknown continuation host phase')


def allowed_stage(stage,arm,seed):
    if stage=='g1' and (arm,seed)==('C',4718):return
    if stage=='gate-evaluate' and (arm,seed)==('L',4718):return
    if stage in ('profile','remaining','final-test') and [arm,seed] in ORDER:return
    raise ValueError('stage outside continuation DAG; no smoke rerun/extra C ON')


def prerequisites(protocol,stage,arm,seed,rows):
    validate_protocol(protocol);allowed_stage(stage,arm,seed)
    for row in rows:
        if row.get('run_id') != protocol['run_id'] or row.get('protocol_sha256') != protocol.get('_sealed_sha256'):
            raise ValueError('historical/cross-protocol activity cannot become continuation PASS')
    def passed(phase,a,s):
        if not any((r.get('phase'),r.get('arm'),r.get('seed'),r.get('status'))==(phase,a,s,'PASS') for r in rows):
            raise ValueError('continuation prerequisite not passed: '+f'{phase}-{a}-{s}')
    if stage!='g1':passed('g1','C',4718)
    if stage in ('profile','remaining','final-test'):passed('gate-evaluate','L',4718)
    if stage=='remaining':passed('profile',arm,seed)
    if stage=='final-test':
        for a,s in ORDER:passed('remaining',a,s)


def validate_release(token,stage,protocol,*,arm=None,seed=None,code_hash,clock):
    validate_protocol(protocol);allowed_stage(stage,arm,seed)
    c=protocol['continuation']
    if not c['synthetic_fixture']:
        raise ValueError('NOT_READY: continuation acceptance decisions pending; no actual release')
    if token.get('synthetic_fixture') is not True:
        raise ValueError('explicit fixture release required')
    for key,expected in [('stage',stage),('run_id',protocol['run_id']),('code_hash',code_hash),
                         ('protocol_sha256',protocol.get('_sealed_sha256')),('reviewer_task',protocol['reviewer']),('status','PASS'),('arm',arm),('seed',seed)]:
        if token.get(key) != expected:raise ValueError('continuation release identity mismatch: '+key)
    expiry=dt.datetime.fromisoformat(token['expires_at'])
    if expiry.tzinfo is None or clock.tzinfo is None or expiry>dt.datetime.fromisoformat(DEADLINE) or clock>=expiry:
        raise ValueError('continuation release expired/overlong')
    entries=token.get('evidence',[])
    if not entries:raise ValueError('no independently SHA-bound continuation evidence')
    kinds=set()
    for entry in entries:
        value=bound_json(entry,protocol);kind=entry.get('kind');kinds.add(kind)
        if kind=='legacy-scientific-reference':
            if value.get('reference_only') is not True or value.get('status')!='REFERENCE_ONLY' or value.get('original_run_id')!=ORIGINAL_RUN or value.get('legacy_C_integrity')!='FAIL_INCOMPLETE_SUPERVISION':
                raise ValueError('legacy scientific reference cannot certify new PASS')
            source=value.get('source',{})
            old_sources=bound_json(c['legacy_stop'],protocol).get('evidence',[])
            if source not in old_sources:raise ValueError('legacy scientific source not protected by original STOP')
            evidence(source,protocol)
        elif kind in {'new-code-review','new-lifecycle-review','development-review'}:
            expected=dict(format='task9-lr-continuation-review-v1',status='PASS',
                run_id=protocol['run_id'],protocol_sha256=protocol.get('_sealed_sha256'),
                code_hash=code_hash,reviewer_task=protocol['reviewer'],stage=stage,arm=arm,seed=seed,
                synthetic_fixture=True,execution_allowed=False)
            if any(value.get(k)!=v for k,v in expected.items()):
                raise ValueError('review contents must bind new namespace/stage/code/protocol/reviewer PASS')
        else:raise ValueError('unknown continuation review evidence kind')
    required={'new-code-review'}
    if stage!='g1':required|={'legacy-scientific-reference','new-lifecycle-review'}
    if stage=='final-test':required.add('development-review')
    if not required<=kinds:raise ValueError('missing typed continuation review evidence')
    budget=token.get('remaining_resource_budget',{})
    for key in ('worker_seconds','gpu_seconds','wall_seconds','output_bytes','evaluation_episodes','consumed_transfers'):
        number(budget.get(key),'release '+key)
    cap=number(token.get('max_worker_seconds'),'release cap');reserve=number(token.get('save_reserve_s'),'save reserve')
    if cap<=0 or reserve>=cap or cap>min(budget['worker_seconds'],budget['gpu_seconds'],budget['wall_seconds']):
        raise ValueError('invalid continuation release cap/reserve')
    if budget['evaluation_episodes']>10788 or budget['consumed_transfers']>12000000 or budget['output_bytes']>LIMITS['max_output_bytes']:
        raise ValueError('continuation release resets inherited budget')
    return token
