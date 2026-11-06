#!/usr/bin/env python3
"""Host-only serial dispatch; exact releases, immutable evidence, no retries."""
import argparse
import datetime as dt
import fcntl
import json
import os
import math
import signal
import uuid
from pathlib import Path
import shlex
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from task9_lr.runtime import artifact_digest,sha256
from task9_lr.admission import protocol_read,load_protocol,read_release,check_resources,activity_rows,prerequisites,candidate_accounting
from task9_lr import continuation, clock as trusted_clock, costs
IMAGE='sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430'


def dump(path,value):
    """Durable replace; a publication failure is fatal to supervision."""
    path=Path(path);temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('x') as stream:
            json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        temp.replace(path)
        fd=os.open(path.parent,os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if temp.exists():temp.unlink()


def create_json(path,value):
    """Publish complete immutable JSON atomically; never expose a partial file."""
    path=Path(path);temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('x') as stream:
            json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.link(temp,path)  # Atomic exclusive publication; existing target fails.
        fd=os.open(path.parent,os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if temp.exists():temp.unlink()


def process_identity(pid=None):
    pid=pid or os.getpid()
    fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
    return dict(pid=pid,start_ticks=fields[19])


def alive(identity):
    try:
        fields=Path(f"/proc/{identity['pid']}/stat").read_text().rsplit(')',1)[1].split()
        return fields[0]!='Z' and fields[19]==identity['start_ticks']
    except FileNotFoundError:return False


def internal_command(mode,spec):
    return [sys.executable,'-B','-u',str(Path(__file__).resolve()),mode,str(spec)]


class DockerBackend:
    """All destructive actions require the full immutable container identity."""
    terminal_budget_s=25  # inspect+probe (2x5s), then inspect+kill+inspect (3x5s).
    def __init__(self,spec):
        if spec.get('protocol',{}).get('format')=='task9-lr-real-batch-contract-v1':
            from task9_lr.real_g1 import spec_gate
            spec_gate(spec)
        else:continuation.assert_execution_allowed(spec.get('protocol',{}))
        self.spec=spec

    def timeout(self):
        budget=remaining(self.spec) if 'started_monotonic' in self.spec else 5
        if budget<=0:raise TimeoutError('original cap exhausted; exact Docker state UNKNOWN')
        return min(5,budget)

    def inspect(self):
        result=subprocess.run(docker(['inspect',self.spec['container_id']]),capture_output=True,text=True,timeout=self.timeout())
        if result.returncode:raise RuntimeError('exact container inspect unavailable')
        value=json.loads(result.stdout)[0]
        expected=self.spec['container_identity']
        actual=dict(Id=value['Id'],Image=value['Image'],Mounts=value['Mounts'],
                    User=value['Config']['User'],DeviceRequests=value['HostConfig']['DeviceRequests'])
        if self.spec.get('protocol',{}).get('format')=='task9-lr-real-batch-contract-v1':
            from task9_lr.real_g1 import container_identity
            actual=container_identity(value)
        if actual!=expected:raise RuntimeError('container namespace identity changed; refuse stop')
        return value

    def resources(self):
        state=self.inspect()
        dump(Path(self.spec['supervision_dir'])/'container-observed.json',dict(observed_epoch=trusted_clock.epoch(self.spec['protocol']),inspect=state))
        return check_resources(self.spec['protocol'],self.spec['output'],active_name=self.spec['activity'],container_state=state)

    def quiet(self):
        self.inspect()
        # An exited docker-exec client alone is insufficient. Query the exact
        # container PID namespace independently, without importing project code.
        code="import pathlib,sys; needle=b'/workspace/scripts/task9_11/worker.py'; found=[p.name for p in pathlib.Path('/proc').glob('[0-9]*') if p.name!=str(__import__('os').getpid()) and (p/'cmdline').exists() and needle in (p/'cmdline').read_bytes().split(b'\\0')]; print(found); sys.exit(bool(found))"
        result=subprocess.run(docker(['exec',self.spec['container_id'],'python3','-B','-c',code]),capture_output=True,text=True,timeout=self.timeout())
        if result.returncode:raise RuntimeError('container worker absent proof failed: '+result.stdout+result.stderr)
        return dict(worker_absent=True,probe_stdout=result.stdout)

    def stop(self):
        state=self.inspect()
        if state['State']['Running']:
            result=subprocess.run(docker(['kill','--signal','KILL',self.spec['container_id']]),capture_output=True,text=True,timeout=self.timeout())
            if result.returncode:raise RuntimeError('exact container kill failed')
        state=self.inspect()
        if state['State']['Running'] is not False:raise RuntimeError('container still active; exit UNKNOWN')
        return dict(container_stopped=True,inspect=state)


def watch(spec,backend):
    """Independent witness and bounded guard. It never starts a worker."""
    folder=Path(spec['supervision_dir']);failure=None;proof={};result=None
    tail=max(spec['force_stop_tail_s'],getattr(backend,'terminal_budget_s',25))
    try:
        create_json(folder/'watcher-ready.json',dict(identity=process_identity(),reservation_id=spec['reservation_id']))
        while True:
            elapsed=time.monotonic()-spec['started_monotonic']
            if (folder/'guardian-failure.json').exists():raise RuntimeError('guardian reported failure')
            # Parent death wins even if a worker result arrives concurrently.
            if spec.get('outer') and not alive(spec['outer']):raise RuntimeError('outer dispatcher exited')
            if not alive(spec['owner']):raise RuntimeError('dispatch owner exited')
            if not alive(spec['guardian']):raise RuntimeError('exit guardian exited')
            if trusted_clock.epoch(spec.get('protocol',{}))>=spec['deadline_epoch']-tail or elapsed>=spec['cap_s']-tail:raise TimeoutError('hard stop threshold reached inside reserved budget tail')
            if elapsed>=spec['cap_s']-spec['save_reserve_s']:
                Path(spec['stop_path']).parent.mkdir(parents=True,exist_ok=True)
                Path(spec['stop_path']).touch(exist_ok=True)
            request=folder/'launch-request.json'
            if request.is_file() and not (folder/'launch-ack.json').exists():
                value=json.loads(request.read_text())
                if value.get('reservation_id')!=spec['reservation_id'] or value.get('guardian')!=spec['guardian']:
                    raise RuntimeError('launch request identity mismatch')
                create_json(folder/'launch-ack.json',dict(reservation_id=spec['reservation_id'],
                            watcher=process_identity(),guardian=spec['guardian'],request_sha256=sha256(request)))
            result_path=folder/'worker-result.json'
            if result_path.is_file():
                result=json.loads(result_path.read_text())
                if result['exit_code']!=0:raise RuntimeError('worker client returned nonzero')
                proof=backend.quiet();break
            time.sleep(min(.1,spec['poll_s'],max(.01,spec['cap_s']-elapsed)))
    except BaseException as error:
        failure=repr(error)
        try:proof=backend.stop()
        except BaseException as stop_error:proof=dict(stop_error=repr(stop_error),container_stopped='UNKNOWN')
    record=dict(spec['record'],exit_code=result['exit_code'] if result else None,
                finished_epoch=trusted_clock.epoch(spec.get('protocol',{})),wall_s=time.monotonic()-spec['started_monotonic'],
                status='PASS' if failure is None else 'FAIL',supervision_error=failure,
                client_exit_code=result['exit_code'] if result else None,exit_code_scope='docker-exec client; not independent worker wait status',
                stage_terminal_wall_s=time.monotonic()-spec['started_monotonic'],
                owner_exit_code='UNKNOWN',owner_full_wall_s='UNKNOWN',container_worker_exit_code='UNKNOWN',
                worker_absence_verified=proof.get('worker_absent',False),termination_proof=proof)
    try:
        dump(spec['record_path'],record)
        create_json(folder/'terminal.json',dict(activity=spec['activity'],status=record['status'],
                    record_sha256=sha256(spec['record_path']),watcher=process_identity(),
                    owner_alive=alive(spec['owner']),guardian_alive=alive(spec['guardian'])))
    except BaseException:
        # A partially published PASS has no matching terminal receipt and cannot
        # be admitted. Force shutdown even when the worker already returned.
        if proof.get('container_stopped') is not True:backend.stop()
        raise
    return 0 if record['status']=='PASS' else 1


def launch_gate(spec,watcher,backend):
    """Fail closed on observed invalidity; no claim to eliminate all OS races."""
    folder=Path(spec['supervision_dir'])
    ready=json.loads((folder/'watcher-ready.json').read_text())
    if ready.get('reservation_id')!=spec['reservation_id'] or ready.get('identity',{}).get('pid')!=watcher.pid:
        raise RuntimeError('watcher ready identity mismatch')
    if watcher.poll() is not None or not alive(ready['identity']):raise RuntimeError('budget watcher dead before worker launch')
    if (folder/'terminal.json').exists():raise RuntimeError('watcher terminal before worker launch')
    if spec.get('outer') and not alive(spec['outer']):raise RuntimeError('outer dispatcher exited before worker launch')
    if not alive(spec['owner']):raise RuntimeError('dispatch owner exited before worker launch')
    tail=max(spec['force_stop_tail_s'],getattr(backend,'terminal_budget_s',25))
    if trusted_clock.epoch(spec.get('protocol',{}))>=spec['deadline_epoch']-tail or time.monotonic()-spec['started_monotonic']>=spec['cap_s']-tail:
        raise TimeoutError('launch budget exhausted inside stop tail')
    return ready['identity']


def wait_receipt(folder,role,process,identity,reservation_id,timeout,protocol=None):
    rc=process.wait(timeout=max(0,timeout))
    create_json(Path(folder)/(role+'-wait.json'),dict(reservation_id=reservation_id,
                identity=identity,waiter=process_identity(),exit_code=rc,finished_epoch=trusted_clock.epoch(protocol or {})))
    return rc


def remaining(spec):
    """Every wait/stop tail shares the original absolute cap; no cap+N."""
    return max(0.,min(spec['started_monotonic']+spec['cap_s']-time.monotonic(),spec['deadline_epoch']-trusted_clock.epoch(spec.get('protocol',{}))))


def exact_kill(identity, *, group=False):
    if alive(identity):
        # start_ticks prevents signalling a recycled PID. Each launched child
        # owns a session; no task-agnostic process scan or broad kill is used.
        try:(os.killpg if group else os.kill)(identity['pid'],signal.SIGKILL)
        except ProcessLookupError:pass


def stop_reap(process,identity,spec):
    exact_kill(identity,group=True)
    return process.wait(timeout=remaining(spec))


def guard(spec_path,lock_fd,*,backend_factory=DockerBackend,watch_command=None):
    spec_path=Path(spec_path);spec=json.loads(spec_path.read_text());folder=Path(spec['supervision_dir'])
    spec['guardian']=process_identity()
    create_json(folder/'guardian-ready.json',dict(identity=spec['guardian'],reservation_id=spec['reservation_id']))
    create_json(folder/'watch-spec.json',spec)
    command=watch_command or internal_command('--_watch',folder/'watch-spec.json')
    backend=backend_factory(spec);watcher=None;process=None;identity=None;watcher_identity=None
    try:
        watcher=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                 start_new_session=True,pass_fds=(lock_fd,),env=dict(os.environ,TASK9_LR_LOCK_FD=str(lock_fd)))
        watcher_identity=process_identity(watcher.pid)
        while not (folder/'watcher-ready.json').exists():
            if watcher.poll() is not None:raise RuntimeError('budget watcher failed before worker launch')
            if remaining(spec)<=0:raise TimeoutError('watcher arm timeout inside cap')
            time.sleep(.01)
        launch_gate(spec,watcher,backend);backend.resources();launch_gate(spec,watcher,backend)
        create_json(folder/'launch-request.json',dict(reservation_id=spec['reservation_id'],guardian=spec['guardian']))
        while not (folder/'launch-ack.json').is_file():
            launch_gate(spec,watcher,backend);time.sleep(.01)
        ack=json.loads((folder/'launch-ack.json').read_text())
        if ack!=dict(reservation_id=spec['reservation_id'],watcher=watcher_identity,
                     guardian=spec['guardian'],request_sha256=sha256(folder/'launch-request.json')):
            raise RuntimeError('launch acknowledgement identity mismatch')
        launch_gate(spec,watcher,backend)
        with Path(spec['log_path']).open('x') as stream:
            with costs.locked(spec.get('protocol',{})):
                if costs.enabled(spec.get('protocol',{})):
                    record=spec['record'];p=spec['protocol']
                    read_release(Path(spec['output'])/'releases'/(spec['activity']+'.json'),record['phase'],p,arm=record['arm'],seed=record['seed'])
                    backend.resources()
                launch_gate(spec,watcher,backend)
                process=subprocess.Popen(spec['command'],stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                identity=process_identity(process.pid)
                create_json(folder/'worker-started.json',dict(identity=identity))
            next_resource_check=time.monotonic()+spec['poll_s']
            while process.poll() is None:
                if watcher.poll() is not None:raise RuntimeError('budget watcher exited before worker')
                if remaining(spec)<=0:raise TimeoutError('worker exceeded original cap')
                if time.monotonic()>=next_resource_check:
                    backend.resources();next_resource_check=time.monotonic()+spec['poll_s']
                time.sleep(min(.05,spec['poll_s'],remaining(spec)))
            rc=process.wait(timeout=remaining(spec))
            backend.resources()
            create_json(folder/'worker-result.json',dict(exit_code=rc,finished_epoch=trusted_clock.epoch(spec.get('protocol',{})),host_pid=process.pid))
        return wait_receipt(folder,'watcher',watcher,watcher_identity,spec['reservation_id'],remaining(spec),protocol=spec.get('protocol'))
    except BaseException as error:
        try:create_json(folder/'guardian-failure.json',dict(error=repr(error),reservation_id=spec['reservation_id']))
        except BaseException:pass  # No receipt still blocks closure; continue exact stop.
        try:backend.stop()
        finally:
            if process is not None:
                if identity is None:identity=process_identity(process.pid)
                stop_reap(process,identity,spec)
        raise
    finally:
        if watcher is not None and not (folder/'watcher-wait.json').exists():
            # On a guard error the watcher usually observes worker failure or
            # budget stop. If that evidence fails, exact termination + real wait
            # preserves UNKNOWN instead of leaving an unbounded watcher.
            if watcher_identity is None:watcher_identity=process_identity(watcher.pid)
            try:
                wait_receipt(folder,'watcher',watcher,watcher_identity,spec['reservation_id'],min(.2,remaining(spec)),protocol=spec.get('protocol'))
            except subprocess.TimeoutExpired:
                stop_reap(watcher,watcher_identity,spec)
                wait_receipt(folder,'watcher',watcher,watcher_identity,spec['reservation_id'],remaining(spec),protocol=spec.get('protocol'))


def owner(spec_path,lock_fd,*,guard_command=None):
    """Dedicated dispatch owner. The outer process independently waits this PID."""
    spec_path=Path(spec_path);spec=json.loads(spec_path.read_text());folder=Path(spec['supervision_dir'])
    spec['owner']=process_identity()
    create_json(folder/'owner-ready.json',dict(identity=spec['owner'],reservation_id=spec['reservation_id']))
    create_json(folder/'owned-spec.json',spec)
    process=subprocess.Popen(guard_command or internal_command('--_guard',folder/'owned-spec.json'),
                stdin=subprocess.DEVNULL,pass_fds=(lock_fd,),start_new_session=True,
                env=dict(os.environ,TASK9_LR_LOCK_FD=str(lock_fd)))
    identity=process_identity(process.pid)
    try:return wait_receipt(folder,'guardian',process,identity,spec['reservation_id'],remaining(spec),protocol=spec.get('protocol'))
    except BaseException:
        stop_reap(process,identity,spec)
        raise


def outer_wait(spec,process,*,backend_factory=DockerBackend):
    """Witness actual owner.wait return, independently of all child publications."""
    folder=Path(spec['supervision_dir']);waits={};errors=[];evidence_hashes={};owner_identity=None;rc=None
    try:
        owner_identity=process_identity(process.pid)
        backend=backend_factory(spec)
        rc=process.wait(timeout=max(0.,remaining(spec)-getattr(backend,'terminal_budget_s',25)-min(.1,spec['cap_s']/10)))
    except BaseException as error:
        errors.append('owner wait: '+repr(error))
        try:backend_factory(spec).stop()
        except BaseException as stop_error:errors.append('stop: '+repr(stop_error))
        try:
            if owner_identity is None:owner_identity=process_identity(process.pid)
            rc=stop_reap(process,owner_identity,spec)
        except BaseException as reap_error:
            errors.append('owner identity/stop UNKNOWN: '+repr(reap_error))
            try:rc=process.wait(timeout=remaining(spec))
            except BaseException as wait_error:errors.append('owner reap UNKNOWN: '+repr(wait_error))
    completion_clock=trusted_clock.capture(spec.get('protocol',{}));wait_returned=completion_clock['monotonic']
    job_started=spec.get('job_started_monotonic',spec['started_monotonic'])
    actual_wait_wall=wait_returned-job_started
    if actual_wait_wall>spec['cap_s']:errors.append('actual owner wait exceeded original cap')
    try:
        ready_path=folder/'owner-ready.json';ready=json.loads(ready_path.read_text())
        if ready.get('identity')!=owner_identity or ready.get('reservation_id')!=spec['reservation_id']:
            raise ValueError('owner ready identity mismatch')
        evidence_hashes['owner-ready.json']=sha256(ready_path)
    except (OSError,ValueError,KeyError,IndexError) as error:errors.append('owner: '+repr(error))
    for role,waiter in (('guardian',owner_identity),('watcher',None)):
        try:
            value=json.loads((folder/(role+'-wait.json')).read_text())
            ready=json.loads((folder/(role+'-ready.json')).read_text())
            if value['reservation_id']!=spec['reservation_id'] or ready['reservation_id']!=spec['reservation_id'] or value['identity']!=ready['identity']:
                raise ValueError('wait/ready identity mismatch')
            if role=='watcher':waiter=waits['guardian']['identity']
            if value['waiter']!=waiter or isinstance(value['exit_code'],bool) or not isinstance(value['exit_code'],int):
                raise ValueError('actual wait witness mismatch')
            if alive(value['identity']):raise ValueError('waited member still alive')
            waits[role]=value
            evidence_hashes[role+'-wait.json']=sha256(folder/(role+'-wait.json'))
            evidence_hashes[role+'-ready.json']=sha256(folder/(role+'-ready.json'))
        except (OSError,ValueError,KeyError,IndexError) as error:errors.append(role+': '+repr(error))
    try:
        terminal=json.loads((folder/'terminal.json').read_text())
        if terminal.get('record_sha256')!=sha256(spec['record_path']):raise ValueError('stage receipt hash mismatch')
        if terminal.get('activity')!=spec['activity'] or terminal.get('watcher')!=waits['watcher']['identity']:
            raise ValueError('stage terminal activity/publisher identity mismatch')
        record=json.loads(Path(spec['record_path']).read_text())
        for key in ('run_id','phase','arm','seed','reservation_id','protocol_sha256','code_hash','release_sha256'):
            if record.get(key)!=spec['record'].get(key):raise ValueError('stage record identity mismatch: '+key)
        evidence_hashes['terminal.json']=sha256(folder/'terminal.json')
        evidence_hashes['activity_record']=sha256(spec['record_path'])
        if terminal.get('status')!='PASS':errors.append('stage terminal is not PASS')
    except (OSError,ValueError,KeyError,IndexError) as error:errors.append('terminal: '+repr(error))
    if rc or errors:
        try:backend_factory(spec).stop()
        except BaseException as error:errors.append('stop: '+repr(error))
        for role in ('guardian','watcher'):
            try:
                path=folder/(role+'-ready.json')
                if path.exists():
                    identity=json.loads(path.read_text())['identity']
                    if alive(identity):exact_kill(identity,group=True);errors.append(role+' exact stop; actual wait UNKNOWN')
            except BaseException as error:errors.append(role+' identity/stop UNKNOWN: '+repr(error))
    value=dict(format='task9-lr-lifecycle-v1',reservation_id=spec['reservation_id'],
               owner=dict(identity=owner_identity,exit_code=rc,waiter=process_identity()),waits=waits,
               chain_status='PASS' if not errors and rc==0 and len(waits)==2 and all(v['exit_code']==0 for v in waits.values()) else 'UNKNOWN',
               errors=errors,evidence_sha256=evidence_hashes,actual_owner_wait_wall_s=actual_wait_wall,
               job_started_monotonic=job_started,owner_wait_returned_monotonic=wait_returned,completion_clock=completion_clock,
               observed_chain_wall_s=time.monotonic()-spec['started_monotonic'],
               accounting_status='UNKNOWN',outer_exit_code='UNKNOWN',outer_publication_exit_tail_s='UNKNOWN',
               closed_wall_s='UNKNOWN',cost_scope='single enclosing interval; subordinate stage walls are not additive')
    try:create_json(folder/'lifecycle.json',value)
    except BaseException:
        backend_factory(spec).stop()
        raise
    return value


def close_candidate(spec,lifecycle,session_started):
    """Finite actual-wait job plus full pending engineering control envelope."""
    policy=candidate_accounting(spec['protocol'])
    if lifecycle['chain_status']!='PASS':raise ValueError('lifecycle UNKNOWN; no candidate closure')
    control=max(0.,time.monotonic()-session_started-lifecycle['actual_owner_wait_wall_s'])
    if control>policy['control_envelope_s']:raise ValueError('control session envelope exceeded; accounting UNKNOWN')
    value=dict(format='task9-lr-candidate-closed-v1',status='CLOSED',execution_allowed=False,
               **{key:spec['record'][key] for key in ('run_id','phase','arm','seed','reservation_id','reservation_sha256','protocol_sha256','code_hash','release_sha256')},
               record_sha256=sha256(spec['record_path']),lifecycle_sha256=sha256(Path(spec['supervision_dir'])/'lifecycle.json'),
               owner_wait=lifecycle['owner'],job_wall_s=lifecycle['actual_owner_wait_wall_s'],
               control_session=dict(charged_s=policy['control_envelope_s'],observed_before_publication_s=control,
                                    classification='engineering-upper-bound-pending-approval',
                                    publication_exit_tail='included in full envelope; not measured or proven'),
               charged_wall_s=lifecycle['actual_owner_wait_wall_s']+policy['control_envelope_s'])
    folder=Path(spec['supervision_dir'])
    # A durable deny marker survives publication/fsync failure and slow writes.
    # Remove it only after publication and the after-publication envelope check.
    # Its removal need not be durable: crash resurrection only denies admission.
    pending=folder/'closure-pending.json'
    create_json(pending,dict(reservation_id=spec['reservation_id'],status='UNKNOWN',reason='closure publication in progress'))
    create_json(folder/'closure.json',value)
    if time.monotonic()-session_started-lifecycle['actual_owner_wait_wall_s']>policy['control_envelope_s']:
        raise ValueError('control session envelope exceeded after publication; accounting UNKNOWN')
    pending.unlink()
    if time.monotonic()-session_started-lifecycle['actual_owner_wait_wall_s']>policy['control_envelope_s']:
        # Unlink is also real control work. Reinstall durable denial; if that
        # publication fails, revoke this invocation's candidate closure instead.
        try:create_json(pending,dict(reservation_id=spec['reservation_id'],status='UNKNOWN',reason='control envelope exceeded after marker unlink'))
        except BaseException as marker_error:
            try:
                try:os.link(folder/'closure.json',folder/'closure-rejected.json')
                except OSError:pass  # Preserve the failed candidate when possible.
                os.unlink(folder/'closure.json')
            except BaseException as rollback_error:
                raise RuntimeError('closure invalidation UNKNOWN; deny/rollback failure: '+repr((marker_error,rollback_error)))
            raise ValueError('control envelope exceeded after marker unlink; closure revoked') from marker_error
        raise ValueError('control envelope exceeded after marker unlink; accounting UNKNOWN')
    return value


def docker(args):return ['sg','docker','-c',shlex.join(['docker']+args)]


def create_container(protocol):
    continuation.assert_execution_allowed(protocol)
    out=Path(protocol['new_output_root']);logs=Path(protocol['new_log_root'])
    if not (out/'activities/prepare-C-4718.json').is_file():raise RuntimeError('write-ahead preparation activity missing')
    logs.mkdir(parents=True,exist_ok=False)
    (out/'tmp').mkdir();(out/'releases').mkdir()
    gpu=protocol['preferred_gpu_uuid'];apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
    if gpu in apps:raise RuntimeError('selected GPU occupied; no launch')
    name='forem-task9-lr-'+protocol['run_id'].split('T')[1].split('+')[0]
    cmd=['run','-d','--name',name,'--gpus','device='+gpu,'--user',f'{os.getuid()}:{os.getgid()}','--read-only','--network','none','--shm-size','2g']
    for src,dst,ro in [(str(ROOT),'/workspace',True),('/home/ybc/projects/CL-FoReM/forem','/history',True),(str(out),'/output',False),(str(logs),'/runlogs',False)]:
        cmd+=['--mount',f'type=bind,src={src},dst={dst}'+(',readonly' if ro else '')]
    for env in ['PYTHONDONTWRITEBYTECODE=1','PYTHONUNBUFFERED=1','PYTHONPATH=/workspace/src','CUDA_VISIBLE_DEVICES=0','TASK9_PHYSICAL_GPU_UUID='+gpu,'OMP_NUM_THREADS=2','OPENBLAS_NUM_THREADS=2','TMPDIR=/output/tmp']:
        cmd+=['--env',env]
    cmd+=['--workdir','/output','--entrypoint','/bin/sleep',IMAGE,str(max(1,int(dt.datetime.fromisoformat(protocol['deadline']).timestamp()-time.time())))]
    started=time.time();result=subprocess.run(docker(cmd),capture_output=True,text=True)
    record=dict(command=docker(cmd),started_epoch=started,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,name=name,image=IMAGE,gpu_uuid=gpu,uid=os.getuid(),gid=os.getgid())
    dump(out/'container.json',record)
    if result.returncode:raise RuntimeError('container creation failed; no retry')
    inspect=json.loads(subprocess.check_output(docker(['inspect',name]),text=True))[0]
    if inspect['Image']!=IMAGE or not inspect['HostConfig']['ReadonlyRootfs']:raise RuntimeError('container identity/root isolation')
    mounts={m['Destination']:m for m in inspect['Mounts']}
    if any(mounts[k]['RW'] for k in ('/workspace','/history')) or any(not mounts[k]['RW'] for k in ('/output','/runlogs')):raise RuntimeError('mount write isolation')
    if inspect['HostConfig']['DeviceRequests'][0]['DeviceIDs']!=[gpu]:raise RuntimeError('GPU isolation')
    dump(out/'container-inspect.json',inspect)
    return name


def host_release(path,phase,arm,seed,p):
    # Shared release validation includes protocol hash, expiry, finite caps,
    # reviewed remaining budget and all independently bound evidence.
    return read_release(path,phase,p,arm=arm,seed=seed)


def dispatch(p,container,phase,arm,seed,*,execution_adapter=None):
    session_started=time.monotonic()
    if execution_adapter is None:continuation.assert_execution_allowed(p)
    elif p.get('execution_allowed') is not False or not p.get('continuation',{}).get('synthetic_fixture'):
        raise ValueError('external execution adapter restricted to explicit nonexecuting synthetic candidate')
    out=Path(p['new_output_root']);logs=Path(p['new_log_root']);name=f'{phase}-{arm}-{seed}'
    with (out/'supervisor.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with costs.locked(p):
            previous=activity_rows(out,protocol=p)
            record_path=out/'activities'/f'{name}.json'
            if record_path.exists():
                old=json.loads(record_path.read_text())
                if (old.get('supervision_format')=='task9-lr-supervision-v2' and old.get('status')=='PASS'
                    and old.get('code_hash')==artifact_digest() and old.get('protocol_sha256')==p.get('_sealed_sha256')
                    and old.get('release_sha256')==sha256(out/'releases'/f'{name}.json')):
                    return 'already_passed'
                raise RuntimeError('activity identity already consumed; no duplicate dispatch: '+name)
            prerequisites(out,phase,arm,seed,protocol=p)
            release=out/'releases'/f'{name}.json'
            if not release.is_file():
                print(json.dumps(dict(status='NEEDS_INDEPENDENT_REVIEW',stage=phase,arm=arm,seed=seed,release=str(release))),flush=True);return 'hold'
            token=host_release(release,phase,arm,seed,p)
            if phase.startswith('smoke'):
                spent=sum(q.get('job_wall_s',q['wall_s']) for q in previous if q['phase'].startswith('smoke') and q['arm']==arm);ceiling=p['smoke_group_max_worker_seconds']
            elif phase=='gate-evaluate':spent=sum(q.get('job_wall_s',q['wall_s']) for q in previous if q['phase']==phase);ceiling=p['recording_gates_max_worker_seconds']
            elif phase in ('profile','remaining'):
                spent=sum(q.get('job_wall_s',q['wall_s']) for q in previous if q['phase'] in ('profile','remaining') and q['arm']==arm and q['seed']==seed);ceiling=p['formal_run_max_worker_seconds']
            elif phase=='final-test':spent=sum(q.get('job_wall_s',q['wall_s']) for q in previous if q['phase']==phase);ceiling=p['final_test_max_worker_seconds']
            else:spent=0;ceiling=p['g1_max_worker_seconds']
            cap=token['max_worker_seconds']
            terminal_budget=getattr(execution_adapter,'terminal_budget_s',25)
            if cap<=terminal_budget or cap>ceiling-spent:raise RuntimeError('released cap exceeds cumulative stage allowance')
            admission_clock=trusted_clock.capture(p);now=admission_clock['epoch'];deadline=min(dt.datetime.fromisoformat(p['deadline']).timestamp(),dt.datetime.fromisoformat(token['expires_at']).timestamp())
            if cap+p['save_allowance_s']>deadline-now:raise RuntimeError('global deadline reserve cannot fit phase')
            inspect=(execution_adapter.inspect(container) if execution_adapter is not None else json.loads(subprocess.check_output(docker(['inspect',container]),text=True,timeout=5))[0])
            if inspect['Name'].lstrip('/')!=container or not inspect['State']['Running']:raise RuntimeError('container not running/identity mismatch')
            sealed=json.loads((out/'container-inspect.json').read_text())
            keys=lambda v:dict(Id=v['Id'],Image=v['Image'],Mounts=v['Mounts'],User=v['Config']['User'],DeviceRequests=v['HostConfig']['DeviceRequests'])
            if keys(inspect)!=keys(sealed):raise RuntimeError('container differs from sealed namespace')
            control_envelope=candidate_accounting(p)['control_envelope_s'] if continuation.is_continuation(p) else 0
            check_resources(p,out,new_worker_seconds=cap+control_envelope,new_gpu_seconds=cap,container_state=inspect)
            folder='g1' if phase=='g1' else f'{"smoke" if phase.startswith("smoke") or phase=="gate-evaluate" else "test" if phase=="final-test" else "formal"}-{arm}-seed{seed}'
            reservation=uuid.uuid4().hex
            command=docker(['exec','-e','TASK9_LR_ACTIVITY='+name,'-e','TASK9_LR_RESERVATION='+reservation,
                            '-e','TASK9_LR_LOG_PATH=/runlogs/'+name+'.txt',inspect['Id'],'python3','-B','-u',
                            '/workspace/scripts/task9_11/worker.py','--arm',arm,'--seed',str(seed),'--phase',phase,
                            '--protocol','/output/freeze/protocol.json','--output','/output/'+folder])
            if execution_adapter is not None:command=execution_adapter.worker_command(phase,arm,seed,reservation)
            record=dict(run_id=p['run_id'],phase=phase,arm=arm,seed=seed,started_epoch=now,command=command,cap_s=cap,status='reserved',
                        automatic_retry=False,control_envelope_s=control_envelope,supervision_format='task9-lr-supervision-v2',reservation_id=reservation,
                        code_hash=artifact_digest(),protocol_sha256=p['_sealed_sha256'],release_sha256=sha256(release))
            supervision=out/'supervision'/name;supervision.mkdir(parents=True,exist_ok=False)
            spec=dict(protocol=p,output=str(out),activity=name,supervision_dir=str(supervision),record=record,
                      record_path=str(record_path),outer=process_identity(),owner=process_identity(),started_monotonic=admission_clock['monotonic'],admission_clock=admission_clock,
                      command=command,container_id=inspect['Id'],container_identity=keys(inspect),
                      cap_s=cap,save_reserve_s=token['save_reserve_s'],force_stop_tail_s=max(terminal_budget,min(.15,cap/4)),deadline_epoch=deadline,
                      poll_s=p['poll_s'],stop_path=str(out/folder/'STOP'),log_path=str(logs/(name+'.txt')),reservation_id=reservation)
            if costs.enabled(p):spec['budget_snapshot']=token['budget_snapshot']
            create_json(supervision/'reservation.json',spec)
            record['reservation_sha256']=sha256(supervision/'reservation.json');spec['record']=record
            create_json(record_path,record)
            # Spec is separate from the immutable reservation to avoid a hash cycle.
            create_json(supervision/'guard-spec.json',spec)
        owner_command=execution_adapter.owner_command(supervision/'guard-spec.json') if execution_adapter is not None else internal_command('--_owner',supervision/'guard-spec.json')
        # The outer directly witnesses the enclosing launch; reservation/spec
        # preparation remains in the separately charged control session.
        spec['job_started_monotonic']=time.monotonic()
        process=subprocess.Popen(owner_command,stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,
                                 pass_fds=(lock.fileno(),),env=dict(os.environ,TASK9_LR_LOCK_FD=str(lock.fileno())))
        backend_factory=execution_adapter.backend_factory if execution_adapter is not None else DockerBackend
        try:
            lifecycle=outer_wait(spec,process,backend_factory=backend_factory)
            rc=lifecycle['owner']['exit_code']
            value=json.loads(record_path.read_text())
            receipt=json.loads((supervision/'terminal.json').read_text())
            if rc or value.get('status')!='PASS' or receipt.get('record_sha256')!=sha256(record_path):
                raise RuntimeError('stage supervision failed; no retry: '+name)
            if execution_adapter is None:raise RuntimeError('full lifecycle accounting UNKNOWN: outer publication/exit tail requires independent witness; no next stage')
            close_candidate(spec,lifecycle,session_started)
            activity_rows(out,protocol=p)
        except BaseException:
            backend_factory(spec).stop()
            raise
        return 'passed' 


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--protocol',required=True);parser.add_argument('--phase',required=True,choices=['prepare','smoke-and-gates','train','final-test']);parser.add_argument('--release');a=parser.parse_args()
    p=load_protocol(a.protocol);continuation.assert_execution_allowed(p);out=Path(p['new_output_root'])
    if a.phase=='prepare':
        raise RuntimeError('NOT_READY: prepare lifecycle not released by this supervision repair; old run/STOP unchanged')
    container=json.loads((out/'container.json').read_text())['name']
    if a.phase=='smoke-and-gates':jobs=[('g1','C',4718)]+[(phase,arm,seed) for arm,seed in p['formal_order'] for phase in ('smoke512','smoke1000')]+[('gate-evaluate',arm,4718) for arm in ('C','L')]
    elif a.phase=='train':jobs=[(phase,arm,seed) for arm,seed in p['formal_order'] for phase in ('profile','remaining')]
    else:jobs=[('final-test',arm,seed) for arm,seed in p['formal_order']]
    if continuation.is_continuation(p):jobs=continuation.jobs(p,a.phase)
    for phase,arm,seed in jobs:
        if dispatch(p,container,phase,arm,seed)=='hold':return 0
    return 0


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1] in ('--_owner','--_guard','--_watch'):
        if sys.argv[1]=='--_owner':sys.exit(owner(sys.argv[2],int(os.environ['TASK9_LR_LOCK_FD'])))
        if sys.argv[1]=='--_guard':sys.exit(guard(sys.argv[2],int(os.environ['TASK9_LR_LOCK_FD'])))
        value=json.loads(Path(sys.argv[2]).read_text());sys.exit(watch(value,DockerBackend(value)))
    sys.exit(main())
