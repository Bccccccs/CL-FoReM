"""A single real G1 with independent budget/source/infrastructure/stage gates.

Reuses the existing owner/guardian/watcher wait chain. The dispatcher itself is
measured by a separate root wait. Complete session/control publication tails are
covered only by independent rolling participant bounds, never by a self-signed
fixed envelope. Formal and L-recording execution are separate, unopened gates.
"""
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
import uuid

from . import clock, real_batch as b, real_receipts as r
from .runtime import ASSET_ROOT, artifact_digest, sha256

IMAGE='sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430'
ROLE='task9.11.18.2'
ISSUER_ROOT=b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/releases'


def number(x):return r.number(x)

def reference(ref):
    path=Path(ref['path'])
    if not path.is_relative_to(b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2'):
        raise ValueError('independent evidence must be in .18.2 namespace')
    return b.read_ref(ref)


def checked_budget(p, ref):
    from . import real_program
    if real_program.enabled(p):return real_program.checked_budget(p,ref)
    v=reference(ref)
    mode=b.stage(p)
    expected=dict(format='task9-lr-real-'+mode['tag']+'-budget-admission-v1',
                  status='PASS_G1_ONLY' if mode['tag']=='G1' else 'PASS_L_ON_ONLY',reviewer=ROLE,
                  run_id=p['run_id'],original_started_at=p['started_at'],deadline=p['deadline'])
    if any(v.get(k)!=x for k,x in expected.items()):raise ValueError('independent bounded G1 budget admission required')
    if v.get('classification')!='EVIDENCE_UPPER_BOUND_NOT_EXACT_HISTORY':raise ValueError('upper bound must not erase historical UNKNOWN')
    required={'historical-worker','historical-gpu','C-policy','open-participants','background-inventory'}
    refs=v.get('basis',{})
    if set(refs)!=required:raise ValueError('complete independent bound provenance required')
    for e in refs.values():b.read_ref(e)
    point=v['bound_clock'];clock.validate_capture(p,point)
    if point['epoch']>time.time()+.001:raise ValueError('budget bound is in future')
    concurrency=number(v.get('open_worker_upper_rate'))
    if concurrency<4:raise ValueError('rolling worker reserve must cover all four supported team slots')
    participants=v.get('participants')
    if not isinstance(participants,list) or not participants or len({(x.get('thread_id'),x.get('turn_id')) for x in participants})!=len(participants):
        raise ValueError('bound active participant identities required')
    if any(not x.get('thread_id') or not x.get('turn_id') for x in participants):raise ValueError('participant identity missing')
    if v.get('rolling_rule')!='sum-each-listed-open-turn-to-current-monotonic-plus-stage-reservation':
        raise ValueError('explicit conservative rolling participant rule required')
    for key in ('worker_upper_s','gpu_upper_s','open_gpu_upper_rate','storage_upper_bytes','diagnostic_upper_bytes'):number(v.get(key))
    if v.get('historical_unknown_preserved') is not True:raise ValueError('historical UNKNOWN preservation required')
    return v


def source_review(p,ref):
    from . import real_program
    if real_program.enabled(p):return real_program.source_review(p,ref)
    v=reference(ref)
    mode=b.stage(p)
    expected=dict(format='task9-lr-real-'+mode['tag']+'-source-review-v1',status='PASS',reviewer=ROLE,
        run_id=p['run_id'],source_digest=p['source_digest'],source_manifest=p['source_manifest'],
        scope=mode['scope'])
    if any(v.get(k)!=x for k,x in expected.items()):raise ValueError('independent exact-source real G1 review missing')
    for e in v.get('evidence',[]):b.read_ref(e)
    if not v.get('evidence'):raise ValueError('source review must bind actual checks')
    return v


def allocation_reference(p):
    # Evidence identity always uses the canonical host namespace. In a worker
    # b.bound reads its /workspace mirror, never emits an /output-only ref.
    return b.bound(Path(p['new_output_root'])/'allocation-lease.json')


def release_provenance(path,token):
    original=Path(token.get('independent_release_path',''))
    if not original.is_absolute() or not original.is_relative_to(ISSUER_ROOT) or original.suffix!='.json':
        raise ValueError('independent immutable stage-release original required')
    original_local=b.local_path(original)
    if original_local.resolve()!=original_local or original_local.is_symlink() or sha256(original_local)!=sha256(b.local_path(path)):
        raise ValueError('stage release differs from independent original')


def release(path,p,*,infrastructure=False,arm=None,seed=None):
    from . import real_program
    if real_program.enabled(p):return real_program.release(path,p,infrastructure=infrastructure,arm=arm,seed=seed)
    seed=4718 if seed is None else seed
    token=json.loads(b.local_path(path).read_text())
    release_provenance(path,token)
    mode=b.stage(p)
    expected=dict(format='task9-lr-real-'+mode['tag']+'-release-v1',status='PASS',reviewer_task=ROLE,
        run_id=p['run_id'],code_hash=artifact_digest(),protocol_sha256=p.get('_sealed_sha256'),
        stage='infrastructure' if infrastructure else mode['phase'],arm=mode['arm'],seed=4718,automatic_retry=False,
        image=IMAGE,gpu_uuid=p['preferred_gpu_uuid'])
    if arm not in (None,mode['arm']) or seed!=4718 or any(token.get(k)!=v for k,v in expected.items()):raise ValueError('exact independent G1 release identity required')
    if not re.fullmatch(r'[a-f0-9]{64}',p.get('_sealed_sha256','')):raise ValueError('sealed real protocol SHA required')
    source_review(p,token['source_review']);budget=checked_budget(p,token['budget_review'])
    if mode['tag']=='L-ON':
        from .real_lon import validate_inputs
        validate_inputs(p)
        if token.get('completed_G1')!=p['completed_G1'] or token.get('lon_inputs')!=p['lon_inputs'] or token.get('evaluation_reservation')!=196 or token.get('legacy_contract_basis')!=p['legacy_contract_basis']:
            raise ValueError('L ON release exact legacy/G1/quota binding required')
    expiry=dt.datetime.fromisoformat(token['expires_at'])
    cap=number(token['max_worker_seconds']);tail=number(token['control_reserve_s'])
    save=number(token['save_reserve_s'])
    if expiry.tzinfo is None or expiry>dt.datetime.fromisoformat(p['deadline']) or cap<=25 or cap>1800 or save>=cap or tail<=0:
        raise ValueError('G1 release cap/save/control/expiry invalid')
    if time.time()+cap+tail>=expiry.timestamp():raise ValueError('G1 full reserved execution cannot fit release')
    if not infrastructure and not re.fullmatch(r'[0-9a-f]{64}',token.get('container_id','')):raise ValueError('G1 exact immutable container ID required')
    elapsed=max(0.,time.monotonic()-budget['bound_clock']['monotonic'])
    worker=budget['worker_upper_s']+budget['open_worker_upper_rate']*elapsed+cap+tail
    # gpu_upper includes all historically unclassified allocations. Reserving
    # one preferred GPU for both the job and control tail cannot charge it 0.
    gpu_reserve=number(token.get('max_gpu_seconds'))
    if infrastructure:
        if gpu_reserve!=cap+tail:raise ValueError('explicit complete infrastructure GPU reservation required')
    else:
        lease_ref=token.get('allocation_lease')
        expected_lease=allocation_reference(p)
        if lease_ref!=expected_lease:raise ValueError('G1 allocation lease evidence required')
        lease=b.read_ref(lease_ref)
        # Retain the entire independently allocated lease until exact stopped
        # inspect. A short G1 worker cap cannot silently refund its idle tail.
        if gpu_reserve<max(cap+tail,number(lease.get('lease_seconds'))):
            raise ValueError('explicit complete G1 GPU allocation reservation required')
    gpu=budget['gpu_upper_s']+number(budget['open_gpu_upper_rate'])*elapsed+gpu_reserve
    if worker>p['max_worker_seconds'] or gpu>p['max_gpu_seconds']:raise ValueError('bounded cumulative worker/GPU budget exceeded')
    return token


def root(p):return Path('/output') if ASSET_ROOT==Path('/workspace') else Path(p['new_output_root'])

def resources(p,output,*,new_worker_seconds=0,active_name=None,container_state=None,new_gpu_seconds=None):
    from . import real_program
    if real_program.enabled(p):return real_program.resources(p,output,new_worker_seconds=new_worker_seconds,active_name=active_name,container_state=container_state,new_gpu_seconds=new_gpu_seconds)
    b.validate(p)
    if active_name is None and ASSET_ROOT==Path('/workspace'):active_name=os.environ.get('TASK9_LR_ACTIVITY')
    mode=b.stage(p);name=mode['name']
    if active_name!=name:raise ValueError('only independently released G1 may use real resource reader')
    out=root(p)
    if Path(output).resolve()!=out.resolve():raise ValueError('real G1 resource output namespace mismatch')
    token=release(out/'releases'/f'{name}.json',p)
    if number(new_worker_seconds) not in (0,token['max_worker_seconds']):raise ValueError('real G1 worker cap mismatch')
    if new_gpu_seconds is not None and number(new_gpu_seconds) not in (0,token['max_worker_seconds']):raise ValueError('real G1 GPU cap mismatch')
    spec=json.loads((out/'supervision'/name/'reservation.json').read_text())
    if spec['record']['release_sha256']!=sha256(out/'releases'/f'{name}.json') or spec['record']['cap_s']!=token['max_worker_seconds']:
        raise ValueError('G1 active reservation/release mismatch')
    if ASSET_ROOT==Path('/workspace') and not os.environ.get('TASK9_LR_RESERVATION'):raise ValueError('real G1 worker reservation nonce required')
    if os.environ.get('TASK9_LR_RESERVATION') and os.environ['TASK9_LR_RESERVATION']!=spec['reservation_id']:
        raise ValueError('G1 active reservation nonce mismatch')
    if container_state is not None and container_state.get('Id')!=token['container_id']:raise ValueError('G1 allocation container mismatch')
    budget=checked_budget(p,token['budget_review'])
    directories=[out,b.local_path(p['new_log_root']),b.local_path(b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18')]
    files={q for directory in directories for q in directory.rglob('*') if q.is_file()}
    output_bytes=budget['storage_upper_bytes']+sum(q.stat().st_size for q in files)
    diagnostic=budget['diagnostic_upper_bytes']+sum(q.stat().st_size for q in files if q.suffix in ('.json','.txt','.jsonl','.bin') or any('diagnostics' in part for part in q.parts) or q.is_relative_to(b.local_path(p['new_log_root'])) or q.is_relative_to(directories[2]))
    if output_bytes+40*1024**3>p['max_output_bytes'] or diagnostic>p['max_diagnostic_log_bytes']:
        raise ValueError('real G1 storage/diagnostic plus unchanged save reserve exceeds cap')
    episodes=sum(json.loads(line)['count'] for path in out.rglob('episodes-started.jsonl') for line in path.open())
    quota=0 if mode['tag']=='G1' else 196
    if episodes>quota or 980+max(episodes,quota)>p['max_evaluation_episodes']:
        raise ValueError('real stage inherited evaluation quota exceeded')
    return dict(worker_seconds=budget['worker_upper_s'],gpu_seconds=budget['gpu_upper_s'],
                evaluation_episodes=980+episodes,output_bytes=output_bytes,classification='INDEPENDENT_CONSERVATIVE_UPPER_BOUND')


def supervisor():
    path=ASSET_ROOT/'scripts/task9_11/supervise.py'
    spec=importlib.util.spec_from_file_location('task9_real_G1_supervisor',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def spec_gate(spec):
    from . import real_program
    if real_program.enabled(spec.get('protocol',{})):return real_program.spec_gate(spec)
    # Constructing an exact-ID cleanup backend grants no launch permission.
    # Do not re-run expiring budget admission here: after expiry/source drift the
    # watchdog must still be able to stop only its originally sealed allocation.
    p=spec['protocol'];mode=b.stage(p);name=mode['name'];path=root(p)/'releases'/f'{name}.json'
    token=json.loads(path.read_text());release_provenance(path,token)
    mode=b.stage(p)
    expected=dict(format='task9-lr-real-'+mode['tag']+'-release-v1',status='PASS',reviewer_task=ROLE,
        run_id=p['run_id'],code_hash=p['source_digest'],protocol_sha256=p.get('_sealed_sha256'),
        stage=mode['phase'],arm=mode['arm'],seed=4718,automatic_retry=False,image=IMAGE,gpu_uuid=p['preferred_gpu_uuid'])
    if any(token.get(k)!=v for k,v in expected.items()) or spec.get('activity')!=name or spec.get('container_id')!=token.get('container_id') or spec['record'].get('release_sha256')!=sha256(path):
        raise ValueError('G1 backend spec/release/container identity mismatch')
    if not re.fullmatch(r'[0-9a-f]{64}',token.get('container_id','')):
        raise ValueError('cleanup requires exact immutable container ID')
    return token


def prepare(p, infrastructure_release):
    """Actual isolated container creation needs a separate independent lease."""
    from . import real_program
    if real_program.enabled(p):return real_program.prepare(p,infrastructure_release)
    b.validate(p);token=release(infrastructure_release,p,infrastructure=True)
    out=root(p);logs=Path(p['new_log_root'])
    if out.exists() or logs.exists():raise ValueError('real namespace already consumed; no retry')
    # No GPU allocations before the source/budget/infrastructure gate above.
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
    if p['preferred_gpu_uuid'] in apps:raise ValueError('preferred GPU occupied')
    out.mkdir(parents=True);logs.mkdir(parents=True)
    for name in ('freeze','activities','supervision','releases','tmp'):(out/name).mkdir()
    clock.publish(out/'activities/infrastructure.json',dict(status='RESERVED',run_id=p['run_id'],
        release=b.bound(infrastructure_release),automatic_retry=False,started_clock=clock.capture(p)))
    original=p.pop('_sealed_sha256',None)
    try:
        clock.publish(out/'freeze/protocol.json',p)
        if sha256(out/'freeze/protocol.json')!=original:raise ValueError('frozen protocol differs from sealed review bytes')
        for name,ref in p['scientific_configs'].items():
            arm,seed=name.split('-');(out/f'freeze/{arm}_seed{seed}.json').write_bytes(b.local_path(ref['path']).read_bytes())
    finally:
        if original is not None:p['_sealed_sha256']=original
    container_name='forem-task9-real-'+sha256(out/'freeze/protocol.json')[:12]
    command=['docker','run','-d','--name',container_name,'--cidfile',str(out/'container.cid'),
        '--gpus','device='+p['preferred_gpu_uuid'],'--user',f'{os.getuid()}:{os.getgid()}',
        '--read-only','--network','none','--shm-size','2g']
    for host,inside,ro in [(str(ASSET_ROOT),'/workspace',True),('/home/ybc/projects/CL-FoReM/forem','/history',True),(str(out),'/output',False),(str(logs),'/runlogs',False)]:
        command+=['--mount',f'type=bind,src={host},dst={inside}'+(',readonly' if ro else '')]
    for env in ['PYTHONDONTWRITEBYTECODE=1','PYTHONUNBUFFERED=1','PYTHONPATH=/workspace/src','CUDA_VISIBLE_DEVICES=0',
                'TASK9_PHYSICAL_GPU_UUID='+p['preferred_gpu_uuid'],'OMP_NUM_THREADS=2','OPENBLAS_NUM_THREADS=2','TMPDIR=/output/tmp']:
        command+=['--env',env]
    # Fixed lease contains the whole infrastructure+G1 interval. Its sleep exit
    # is a second finite allocation bound, independently verified after wait.
    lease=int(token['max_worker_seconds']+token['control_reserve_s'])
    cutoff=min(dt.datetime.fromisoformat(p['deadline']).timestamp(),dt.datetime.fromisoformat(token['expires_at']).timestamp())
    allocation_deadline=min(cutoff,time.time()+lease)
    clock.publish(out/'allocation-lease.json',dict(lease_seconds=lease,admission_deadline_epoch=allocation_deadline,
        infrastructure_release=b.bound(infrastructure_release),classification='CONSERVATIVE_ADMISSION_CUTOFF_NOT_OBSERVED_DAEMON_EXIT'))
    lease_code='import time; time.sleep(max(0.0,min('+str(lease)+','+repr(allocation_deadline)+'-time.time())))'
    command+=['--workdir','/output','--entrypoint','python3',IMAGE,'-I','-S','-c',lease_code]
    argv=['sg','docker','-c',shlex.join(command)]
    wait=r.wait_command(b.receipt_root(p)/'infrastructure-launch',argv,cwd=ASSET_ROOT.parent,
        run_id=p['run_id'],stage='prepare',timeout=token['control_reserve_s'],sources=[out/'freeze/protocol.json']+[ASSET_ROOT/path for path in p['source_manifest']])
    actual=r.validate_wait(wait)
    ident=Path(actual['stdout']['path']).read_text().strip()
    if actual['exit_code']!=0 or not re.fullmatch(r'[0-9a-f]{64}',ident):
        cidfile=out/'container.cid'
        clock.publish(out/'infrastructure-failure.json',dict(status='ALLOCATION_UNKNOWN_NO_RETRY',
            launch_wait=wait,deterministic_name=container_name,cidfile=str(cidfile),
            observed_cid=cidfile.read_text() if cidfile.is_file() else None,
            admission_reserve_retained_s=token['max_gpu_seconds'],no_refund=True,
            lease_seconds=lease,absolute_process_exit_target=cutoff,
            limitation='Container daemon/create/start/publication tails remain UNKNOWN until independent exact-ID stopped inspect; lease is not a measured daemon completion bound'))
        raise RuntimeError('real container launch/ID failed; full allocation reserve retained, late create UNKNOWN; no retry')
    observation=r.observe_container(b.receipt_root(p)/'infrastructure-inspect',ident,run_id=p['run_id'])
    state,_=r.inspection(observation)
    clock.publish(out/'container-inspect.json',state)
    clock.publish(out/'container.json',dict(container_id=ident,name=state['Name'].lstrip('/'),
        image=IMAGE,gpu_uuid=p['preferred_gpu_uuid'],launch_wait=wait,observation=observation,
        infrastructure_release=b.bound(infrastructure_release)))
    return dict(container_id=ident,observation=observation,launch_wait=wait,stage_release='REQUIRED')



def container_identity(state):
    return dict(Id=state['Id'],Image=state['Image'],
        Mounts=sorted(state['Mounts'],key=lambda item:json.dumps(item,sort_keys=True,separators=(',',':'))),
        User=state['Config']['User'],
        DeviceRequests=state['HostConfig']['DeviceRequests'],StartedAt=state['State']['StartedAt'],
        RestartCount=state['RestartCount'])

def inner(p):
    """One G1 chain; caller must externally wait and retain its terminal output."""
    import fcntl
    mode=b.stage(p);out=root(p);name=mode['name'];token=release(out/'releases'/f'{name}.json',p)
    from . import real_program
    allocation=real_program.allocation_root(p) if real_program.enabled(p) else out
    lease=json.loads((allocation/'allocation-lease.json').read_text())
    if lease.get('infrastructure_release')!=json.loads((allocation/'container.json').read_text()).get('infrastructure_release'):
        raise ValueError('allocation lease/infrastructure evidence mismatch')
    allocation_deadline=number(lease.get('admission_deadline_epoch'))
    if time.time()+token['max_worker_seconds']+token['control_reserve_s']>=allocation_deadline:
        raise ValueError('G1 full execution and shutdown cannot fit remaining allocation lease; no retry')
    record_path=out/'activities'/f'{name}.json'
    with (out/'supervisor.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if record_path.exists():raise ValueError('G1 identity already consumed; no retry')
        if (out/'ledger'/f'{name}.json').exists():raise ValueError('G1 worker ledger already consumed; no retry')
        m=supervisor();ident=token['container_id']
        observed=subprocess.run(['sg','docker','-c',shlex.join(['docker','inspect',ident])],capture_output=True,text=True,timeout=5,check=True)
        state=json.loads(observed.stdout)[0];sealed=json.loads((allocation/'container-inspect.json').read_text())
        keys=container_identity
        if keys(state)!=keys(sealed) or state['Image']!=IMAGE or state['State'].get('Running') is not True:raise ValueError('real G1 immutable container identity changed')
        if real_program.enabled(p):real_program.validate_single_gpu_allocation(state,p)
        if state['HostConfig']['DeviceRequests'][0]['DeviceIDs']!=[p['preferred_gpu_uuid']]:raise ValueError('real G1 GPU allocation mismatch')
        reservation=uuid.uuid4().hex;point=clock.capture(p);folder=out/'supervision'/name;folder.mkdir(exist_ok=False)
        command=b.worker_argv(p,ident,mode['phase'],mode['arm'],mode['seed'],reservation)
        record=dict(run_id=p['run_id'],phase=mode['phase'],arm=mode['arm'],seed=mode['seed'],started_epoch=point['epoch'],
            command=command,cap_s=token['max_worker_seconds'],status='reserved',automatic_retry=False,
            supervision_format='task9-lr-supervision-v2',reservation_id=reservation,code_hash=artifact_digest(),
            protocol_sha256=p['_sealed_sha256'],release_sha256=sha256(out/'releases'/f'{name}.json'))
        spec=dict(protocol=p,output=str(out),activity=name,supervision_dir=str(folder),record=record,
            record_path=str(record_path),outer=m.process_identity(),owner=m.process_identity(),
            started_monotonic=point['monotonic'],admission_clock=point,command=command,
            container_id=ident,container_identity=keys(state),cap_s=token['max_worker_seconds'],
            save_reserve_s=token['save_reserve_s'],force_stop_tail_s=25,
            deadline_epoch=min(dt.datetime.fromisoformat(token['expires_at']).timestamp(),allocation_deadline),poll_s=p['poll_s'],
            stop_path=str(out/mode['folder']/'STOP'),log_path=str(Path(p['new_log_root'])/(name+'.txt')),reservation_id=reservation)
        m.create_json(folder/'reservation.json',spec);record['reservation_sha256']=sha256(folder/'reservation.json')
        spec['record']=record;m.create_json(record_path,record);m.create_json(folder/'guard-spec.json',spec)
        spec['job_started_monotonic']=time.monotonic()
        process=subprocess.Popen(m.internal_command('--_owner',folder/'guard-spec.json'),stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,pass_fds=(lock.fileno(),),
            env=dict(os.environ,TASK9_LR_LOCK_FD=str(lock.fileno())))
        lifecycle=m.outer_wait(spec,process)
        if lifecycle['chain_status']!='PASS':raise RuntimeError('real G1 lifecycle failed; preserved, no retry')
        stopped=m.DockerBackend(spec).stop()
        m.create_json(allocation/'container-stopped.json',stopped)
        return dict(status=mode['tag']+'_CHAIN_RETURNED_REQUIRES_INDEPENDENT_CLOSURE',lifecycle=b.bound(folder/'lifecycle.json'))
