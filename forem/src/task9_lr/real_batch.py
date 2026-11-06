"""SRC-1435 real-batch contract and actual control receipt integration.

This separate schema cannot turn a historical candidate into an executable
protocol. It fixes authorization, science, namespaces and literal commands while
keeping historical cost, independent releases and the production worker adapter
as explicit admission dependencies. No model or environment imports occur here.
"""
import copy
import hashlib
import datetime as dt
import json
from pathlib import Path
import re
import shlex

from . import clock, continuation, execution_draft, gpu_costs, real_receipts as receipts
from .runtime import ASSET_ROOT, artifact_digest, artifact_files, sha256, validate_matrix

FORMAT = 'task9-lr-real-batch-contract-v1'
HOST_ROOT = Path('/home/ybc/projects/CL-FoReM-task9/forem')
DEADLINE = '2026-11-07T03:18:20+08:00'
CALENDAR_S = 295200
REVIEWER = 'task9.11.18.2'
REVIEW_ROOT = ASSET_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18'
APPROVAL = REVIEW_ROOT/'direct-dispatch-authorization-20261104.json'
BASELINE = ASSET_ROOT/'config/task9/task9_11/protocol.json'
HISTORY = ASSET_ROOT/'doc/agent_logs/task9/task9.11/task9.11.17/execution-protocol-draft-v3.json'
RECEIPT_ROOT = REVIEW_ROOT/'task9.11.18.1/commands'
CONTROL_PROBE = ['python3','-B','-c',
                 "import json; print(json.dumps({'control_probe': True}))"]
DEPENDENCIES = ['independent-source-review', 'evidence-bounded-historical-costs',
                'actual-control-publication-exit-closure',
                'independent-real-G1-worker-admission', 'independent-stage-release']



def local_path(path):
    path=Path(path)
    if ASSET_ROOT == Path('/workspace'):
        for host,inside in [(HOST_ROOT,'/workspace'),
                            (Path('/home/ybc/projects/CL-FoReM/forem'),'/history')]:
            if path.is_relative_to(host):
                return Path(inside)/path.relative_to(host)
    return path


def bound(path):
    path=Path(path);original=path
    if ASSET_ROOT == Path('/workspace') and path.is_relative_to(ASSET_ROOT):
        original=HOST_ROOT/path.relative_to(ASSET_ROOT)
    return dict(path=str(original),sha256=sha256(local_path(path)))


def read_ref(ref):
    path=local_path(ref['path'])
    if sha256(path)!=ref.get('sha256'):raise ValueError('real-batch evidence hash changed')
    return json.loads(path.read_text())

def approval(ref):
    if ref != bound(APPROVAL):
        raise ValueError('exact parent-recorded SRC-1435 authorization required')
    value = read_ref(ref)
    expected = dict(format='task9-lr-real-batch-user-approval-v2',
        source_id='SRC-1435', original_started_at=continuation.START, deadline=DEADLINE,
        max_wall_seconds=CALENDAR_S, max_worker_seconds=208800, max_gpu_seconds=208800,
        max_output_bytes=2*1024**4, max_diagnostic_log_bytes=8*1024**3,
        scientific_budget_changed=False, execution_allowed=True, old_authorization_withdrawn=True,
        old_C_integrity_FAIL_preserved=True, C_host_policy_s=1800, no_extra_C_ON_or_smoke=True,
        consumed=dict(smoke_transitions=4000,evaluation_episodes=980),
        remaining=dict(L_ON=196,periodic=9408,final=1184))
    if any(value.get(k) != v for k, v in expected.items()):
        raise ValueError('SRC-1435 authorization identity/limits mismatch')
    return value


def build(run_id, *, l_on=False, program=False, budget_envelope=None):
    if sha256(BASELINE) != execution_draft.BASE_SHA:
        raise ValueError('protected original protocol changed')
    value = json.loads(BASELINE.read_text())
    value.update(format=FORMAT, run_id=run_id, started_at=continuation.START,
        deadline=DEADLINE, max_wall_seconds=CALENDAR_S,
        authorization=bound(APPROVAL), baseline_protocol=bound(BASELINE),
        historical_preparation=bound(HISTORY),
        new_output_root=str(HOST_ROOT/'results/task9'/run_id),
        new_log_root=str(HOST_ROOT/'logs/task9'/run_id), reviewer=REVIEWER,
        stage_releases=[], source_manifest=artifact_files(), source_digest=artifact_digest(),
        scientific_configs={f'{a}-{s}':bound(ASSET_ROOT/f'config/task9/task9_11/{a}_seed{s}.json')
                            for a,s in validate_matrix()},
        input_manifest=copy.deepcopy(json.loads(HISTORY.read_text())['input_manifest']),
        consumed=copy.deepcopy(continuation.CONSUMED), remaining=copy.deepcopy(continuation.REMAINING),
        stage_dag=execution_draft.stages(), real_receipt_policy=receipts.POLICY,
        admission_dependencies=list(DEPENDENCIES),
        production_worker_adapter='REAL_G1_ONLY_NO_FORMAL_DISPATCH',
        science_dispatch_available=False)
    if l_on:
        from .real_lon import ADAPTER,INPUTS,BRIDGE,g1_reference
        value.update(production_worker_adapter=ADAPTER,science_dispatch_available=True,science_dispatch_scope='L_ON196_ONLY',lon_inputs=copy.deepcopy(INPUTS),legacy_contract_basis=copy.deepcopy(BRIDGE),completed_G1=g1_reference())
    if program:
        from .real_program import configure
        configure(value,budget_envelope=budget_envelope)
    return validate(value)


def stage(value, phase=None, arm=None, seed=None):
    from . import real_program
    if real_program.enabled(value):
        return real_program.stage(value,phase,arm,seed)
    adapter=value.get('production_worker_adapter')
    if adapter=='REAL_G1_ONLY_NO_FORMAL_DISPATCH':return dict(tag='G1',phase='g1',arm='C',seed=4718,name='g1-C-4718',scope='REAL_G1_ONLY',folder='g1')
    if adapter=='REAL_L_ON_ONLY_NO_FORMAL_DISPATCH':return dict(tag='L-ON',phase='gate-evaluate',arm='L',seed=4718,name='gate-evaluate-L-4718',scope='REAL_L_ON_ONLY',folder='smoke-L-seed4718')
    raise ValueError('only single G1 or L ON real adapter supported')


def validate(value):
    if value.get('format') != FORMAT:
        raise ValueError('isolated real-batch schema required')
    from . import real_program
    is_program=real_program.enabled(value)
    approval(value['authorization'])
    if is_program:real_program.validate_contract(value)
    if value['baseline_protocol'] != bound(BASELINE) or value['baseline_protocol']['sha256'] != execution_draft.BASE_SHA:
        raise ValueError('protected original baseline identity changed')
    baseline = read_ref(value['baseline_protocol'])
    allowed = {'max_diagnostic_log_bytes'} if is_program else set()
    if is_program and 'resource_envelope' in value:allowed|={'max_worker_seconds','max_gpu_seconds','max_output_bytes','deadline','max_wall_seconds','max_evaluation_episodes'}
    allowed |= {'format','run_id','started_at','deadline','max_wall_seconds','authorization',
               'new_output_root','new_log_root','reviewer','stage_releases'}
    for key, old in baseline.items():
        if key not in allowed and value.get(key) != old:
            raise ValueError('original resource/scientific condition changed: '+key)
    if value.get('started_at') != continuation.START or (not (is_program and 'resource_envelope' in value) and (value.get('deadline') != DEADLINE or value.get('max_wall_seconds') != CALENDAR_S)):
        raise ValueError('only approved calendar extension is permitted')
    if (dt.datetime.fromisoformat(DEADLINE)-dt.datetime.fromisoformat(continuation.START)).total_seconds() != CALENDAR_S:
        raise ValueError('T0/calendar arithmetic mismatch')
    run_id=value.get('run_id','')
    if not re.fullmatch(r't9\.11-real-[A-Za-z0-9_+\-]+',run_id):
        raise ValueError('fresh real-batch namespace required')
    for key, folder in [('new_output_root','results'),('new_log_root','logs')]:
        expected=HOST_ROOT/folder/'task9'/run_id
        if value.get(key)!=str(expected) or expected.resolve()!=expected:
            raise ValueError('real namespace path mismatch/escape')
    if value.get('reviewer') != REVIEWER or value.get('stage_releases') != []:
        raise ValueError('independent releases must remain external immutable artifacts')
    if value.get('source_manifest') != artifact_files() or value.get('source_digest') != artifact_digest():
        raise ValueError('current real-batch source identity changed')
    configs={f'{a}-{s}':bound(ASSET_ROOT/f'config/task9/task9_11/{a}_seed{s}.json')
             for a,s in validate_matrix()}
    if value.get('scientific_configs') != configs:
        raise ValueError('scientific matrix changed')
    if value.get('historical_preparation') != bound(HISTORY):
        raise ValueError('historical draft lineage changed')
    old=read_ref(value['historical_preparation'])
    if old.get('format') != execution_draft.FORMAT or not old.get('accounting',{}).get('unknown'):
        raise ValueError('historical UNKNOWN must remain visible')
    if value.get('input_manifest') != old['input_manifest']:
        raise ValueError('historical input identity changed')
    for ref in value['input_manifest'].values():
        if bound(Path(ref['path'])) != ref:raise ValueError('historical input bytes changed')
    exact={'consumed':continuation.CONSUMED,'remaining':continuation.REMAINING,
        'stage_dag':execution_draft.stages(),'real_receipt_policy':receipts.POLICY,
        'admission_dependencies':DEPENDENCIES,'production_worker_adapter':value.get('production_worker_adapter'),
        'science_dispatch_available':is_program or value.get('production_worker_adapter')=='REAL_L_ON_ONLY_NO_FORMAL_DISPATCH'}
    mode=dict(tag='PROGRAM') if is_program else stage(value)
    if is_program:
        history=real_program.resource_envelope(value,value['resource_envelope']).get('historical_accounting') if 'resource_envelope' in value else None
        exact.update(consumed=history['consumed'] if history else dict(smoke_transitions=4000,evaluation_episodes=1176),remaining=dict(periodic=9408,final=1184),stage_dag=real_program.stages())
    if mode['tag']=='L-ON':
        from .real_lon import validate_inputs
        validate_inputs(value)
        if value.get('science_dispatch_scope')!='L_ON196_ONLY':raise ValueError('exact remaining L ON196 scope required')
    elif not is_program and any(key in value for key in ('lon_inputs','completed_G1','legacy_contract_basis','science_dispatch_scope')):
        raise ValueError('L ON inputs forbidden in G1-only protocol')
    if any(value.get(k)!=v for k,v in exact.items()):
        raise ValueError('real stage/science/dependency contract changed')
    if 'execution_allowed' in value or 'continuation' in value or 'candidate_accounting' in value:
        raise ValueError('real schema must not flip or reuse candidate execution policy')
    return value


def write(path, run_id, *, l_on=False, program=False, budget_envelope=None):
    path=receipts.canonical(path)
    if not path.is_relative_to(REVIEW_ROOT) or path == REVIEW_ROOT:
        raise ValueError('unreleased contract stays in task9.11.18 review logs')
    value=build(run_id,l_on=l_on,program=program,budget_envelope=budget_envelope)
    if any(Path(value[k]).exists() for k in ('new_output_root','new_log_root')):
        raise ValueError('new real namespace is already consumed')
    return clock.publish(path,value)


def read(path):
    return validate(json.loads(receipts.canonical(path).read_text()))


def container_argv(container_id, argv):
    """Canonical shell serialization around a literal exact-ID Docker exec."""
    if not re.fullmatch(r'[0-9a-f]{64}',container_id):
        raise ValueError('full immutable container ID required; names forbidden')
    if not isinstance(argv,list) or not argv or any(not isinstance(x,str) or '\0' in x for x in argv):
        raise ValueError('literal nonempty container argv required')
    command=['sg','docker','-c',shlex.join(['docker','exec',container_id]+argv)]
    receipts.container_command(command,container_id)
    return command


def worker_argv(value, container_id, stage, arm, seed, reservation):
    """Exact planned worker argv; constructing it grants no execution permission."""
    validate(value)
    if not any(x['phase']==stage and x.get('arm')==arm and x.get('seed')==seed for x in value['stage_dag']):
        raise ValueError('stage/arm/seed outside real-batch DAG')
    if not re.fullmatch(r'[0-9a-f]{32}',reservation):raise ValueError('fresh reservation identity required')
    folder='g1' if stage=='g1' else f'{"smoke" if stage=="gate-evaluate" else "test" if stage=="final-test" else "formal"}-{arm}-seed{seed}'
    return container_argv(container_id,['env','TASK9_LR_ACTIVITY='+f'{stage}-{arm}-{seed}',
        'TASK9_LR_RESERVATION='+reservation,'TASK9_LR_LOG_PATH=/runlogs/'+f'{stage}-{arm}-{seed}.txt',
        'python3','-B','-u','/workspace/scripts/task9_11/worker.py','--arm',arm,'--seed',str(seed),
        '--phase',stage,'--protocol','/output/freeze/protocol.json','--output','/output/'+folder])


def receipt_root(value):
    # A failed namespace remains consumed. Keep every later run's receipts in
    # its own canonical subtree; never reuse the old fixed stage directories.
    run_id=value.get('run_id','')
    if not re.fullmatch(r't9\.11-real-[A-Za-z0-9_+\-]+',run_id):
        raise ValueError('fresh canonical real receipt run identity required')
    return RECEIPT_ROOT/run_id


def record_control(value, root, container_id, argv, *, timeout=60):
    """Record an already authorized control payload; never a science entrypoint.

    Only exact read-only inspect is executable here. The inspect observer itself
    runs on the host; its device/session attribution remains UNKNOWN. New batch
    observations are not misfiled in the old .17 accounting namespace.
    """
    validate(value);root=receipts.canonical(root)
    if not root.is_relative_to(receipt_root(value)):raise ValueError("control receipt outside this real run command namespace")
    if not re.fullmatch(r'[0-9a-f]{64}',container_id):raise ValueError('full container ID required')
    expected=['sg','docker','-c',shlex.join(['docker','inspect',container_id])]
    if argv != expected:raise ValueError('only exact read-only inspect is authorized by control recorder')
    return receipts.wait_command(root,argv,cwd=ASSET_ROOT.parent,run_id=value['run_id'],
        stage='prepare',timeout=timeout,sources=[BASELINE,APPROVAL,HISTORY])




def contract_digest(value):
    return hashlib.sha256(json.dumps({k:v for k,v in value.items() if k!='_sealed_sha256'},
        sort_keys=True,separators=(',',':')).encode()).hexdigest()


def require_control_source_review(value, ref, container_id):
    validate(value)
    review=read_ref(ref)
    expected=dict(format='task9-lr-real-control-source-review-v1',status='PASS',
        reviewer=REVIEWER,run_id=value['run_id'],source_digest=value['source_digest'],
        source_manifest=value['source_manifest'],contract_digest=contract_digest(value),
        scope='CONTROL_RECEIPTS_ONLY',container_id=container_id,
        allowed_argv=[container_argv(container_id,CONTROL_PROBE)])
    if any(review.get(k)!=v for k,v in expected.items()):
        raise ValueError('independent exact-source/container/argv control review required')
    if not Path(ref['path']).is_relative_to(HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2'):
        raise ValueError('independent review outside reviewer namespace')
    inspect=read_ref(review['container_basis'])
    if inspect.get('Id')!=container_id or inspect.get('Image')!=review.get('image') or inspect.get('Mounts')!=review.get('mounts') or inspect.get('HostConfig',{}).get('DeviceRequests')!=review.get('device_requests'):
        raise ValueError('independent control container allocation basis mismatch')
    # The only writable namespace must belong to this real batch; inspection of
    # another task is read-only, but executing a probe there is never permitted.
    mounts={m.get('Destination'):m for m in inspect.get('Mounts',[])}
    if mounts.get('/output',{}).get('Source')!=value['new_output_root'] or mounts.get('/runlogs',{}).get('Source')!=value['new_log_root']:
        raise ValueError('control target is not this batch container')
    return review


def record_container_probe(value, root, container_id, *, source_review, timeout=60):
    """Bounded constant CPU probe after exact container/source/argv approval."""
    review=require_control_source_review(value,source_review,container_id)
    root=receipts.canonical(root)
    if not root.is_relative_to(receipt_root(value)):raise ValueError("control receipt outside this real run command namespace")
    before=receipts.observe_container(root/'before',container_id,run_id=value['run_id'])
    inspect,_=receipts.inspection(before)
    basis=read_ref(review['container_basis'])
    keys=lambda x:{k:x[k] for k in ('Id','Image','Mounts','HostConfig')}
    if keys(inspect)!=keys(basis) or inspect.get('State',{}).get('StartedAt')!=basis.get('State',{}).get('StartedAt') or inspect.get('State',{}).get('Running') is not True:
        raise ValueError('actual control container identity/start differs from independent basis')
    return receipts.wait_command(root/'probe',container_argv(container_id,CONTROL_PROBE),
        cwd=ASSET_ROOT.parent,run_id=value['run_id'],stage='prepare',timeout=timeout,
        sources=[ASSET_ROOT/key for key in value['source_manifest']])

def source_from_wait(value, wait_ref, allocation_review):
    """Connect actual writer bytes to the existing independent device reader.

    A root wait is kept as a root wait. It cannot close publisher/session tails;
    missing allocation review is refused rather than labeled CPU or charged 0.
    """
    validate(value);wait=receipts.validate_wait(wait_ref)
    if wait['run_id'] != value['run_id']:raise ValueError('foreign-batch actual wait')
    if not Path(wait_ref['path']).is_relative_to(receipt_root(value)):raise ValueError('foreign actual receipt root')
    item=receipts.cost_source(wait_ref,allocation_review=allocation_review)
    intervals=gpu_costs.command(value,item)
    return dict(source=item, gpu_intervals=intervals,
        full_session_cost='UNKNOWN',publisher_exit='UNKNOWN',budget_admissible=False)



def require_science_admission(value, *, historical_cost_review=None, source_review=None, stage_release=None):
    validate(value)
    if historical_cost_review is None:
        raise ValueError('NOT_READY: evidence-bounded historical worker/GPU costs missing')
    if source_review is None or stage_release is None:
        raise ValueError('NOT_READY: independent source review and stage release required')
    if not all(isinstance(x,dict) and x.get('path') and x.get('sha256')
               for x in (historical_cost_review,source_review,stage_release)):
        raise ValueError('NOT_READY: exact independent release references required')
    token=read_ref(stage_release)
    if token.get('budget_review')!=historical_cost_review or token.get('source_review')!=source_review:
        raise ValueError('NOT_READY: independent release references differ')
    from .real_g1 import release
    return release(stage_release['path'],value)
