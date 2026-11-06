"""Process-local ENOENT rescan of three resource readers; no model alterations."""
import functools
import hashlib
import json
import os
from pathlib import Path
import shlex
import time
import traceback
ROOT=Path(__file__).resolve().parents[2]
HOST=Path('/home/ybc/projects/CL-FoReM-task9/forem')
INSTALLED=False
AUTH=None

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def local(path):
    path=Path(path)
    if ROOT==Path('/workspace') and path.is_relative_to(HOST):return ROOT/path.relative_to(HOST)
    return path

def log_event(kind,**data):
    if AUTH is None:return
    root=Path(AUTH['event_root'])
    if ROOT==Path('/workspace'):root=Path('/output')/root.relative_to(AUTH['output_root'])
    root.mkdir(parents=True,exist_ok=True)
    with (root/f'process-{os.getpid()}.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(event=kind,pid=os.getpid(),epoch=time.time(),**data))+'\n')

def rescan(function,label):
    @functools.wraps(function)
    def wrapped(*args,**kwargs):
        for attempt in range(1,4):
            try:return function(*args,**kwargs)
            except FileNotFoundError as error:
                log_event('ENOENT_RESCAN',reader=label,attempt=attempt,filename=error.filename,
                    traceback=traceback.format_exc(),action='restart_entire_resource_scan')
                if attempt==3:raise
        raise AssertionError('unreachable')
    wrapped._task9_io_rescan_v1=True
    return wrapped

def environment(auth_path,auth_sha,container=False):
    prefix=Path('/workspace') if container else HOST
    auth_path=Path(auth_path)
    if container and auth_path.is_relative_to(HOST):auth_path=prefix/auth_path.relative_to(HOST)
    return dict(PYTHONPATH=str(prefix/'scripts/task9_io_bridge')+':'+str(prefix/'src'),
        TASK9_IO_BRIDGE_AUTH=str(auth_path),TASK9_IO_BRIDGE_AUTH_SHA256=auth_sha)

def install():
    global INSTALLED,AUTH
    if INSTALLED:return
    path=local(os.environ['TASK9_IO_BRIDGE_AUTH'])
    if sha(path)!=os.environ['TASK9_IO_BRIDGE_AUTH_SHA256']:raise ValueError('I/O bridge authorization SHA changed')
    auth=json.loads(path.read_text())
    expected=dict(format='task9-lr-io-monitor-bridge-authorization-v1',status='PASS_IO_MONITOR_BRIDGE',
        reviewer='task9.11.18.2',run_id='t9.11-real-program-20261104-r3',
        source_digest='b8f3d63b4fb0846156fcfc72663008763a5346d85020daef9025d7f790154c05',
        bounded_rescan_attempts=3,error_scope='FileNotFoundError_ONLY',scientific_semantics_unchanged=True)
    if any(auth.get(k)!=v for k,v in expected.items()):raise ValueError('I/O bridge scope/identity mismatch')
    if not Path(auth['event_root']).is_relative_to(Path(auth['output_root'])/'recovery'):raise ValueError('bridge events outside explicit recovery subtree')
    for name,digest in auth['bridge_files'].items():
        if sha(local(name))!=digest:raise ValueError('I/O bridge implementation changed')
    AUTH=auth
    from task9_lr import real_program as program,diagnostics,evaluation,real_batch as batch
    program.scan_growth=rescan(program.scan_growth,'task9_lr.real_program.scan_growth')
    diagnostics.OutputBudget.refresh=rescan(diagnostics.OutputBudget.refresh,'task9_lr.diagnostics.OutputBudget.refresh')
    evaluation.guarded_size=rescan(evaluation.guarded_size,'task9_lr.evaluation.guarded_size')
    original=batch.worker_argv
    @functools.wraps(original)
    def worker_argv(p,container_id,*args,**kwargs):
        if p['run_id']!=auth['run_id'] or p['source_digest']!=auth['source_digest']:raise ValueError('I/O bridge foreign native worker')
        command=original(p,container_id,*args,**kwargs);payload=shlex.split(command[-1])
        if payload[:4]!=['docker','exec',container_id,'env']:raise ValueError('unexpected exact native worker command')
        updates=environment(Path(os.environ['TASK9_IO_BRIDGE_AUTH']),sha(path),container=True)
        payload[4:4]=[key+'='+value for key,value in updates.items()]
        command[-1]=shlex.join(payload)
        log_event('NATIVE_WORKER_ARGV_BRIDGED',argv=command)
        return command
    batch.worker_argv=worker_argv
    INSTALLED=True
    marker=dict(pid=os.getpid(),argv=__import__('sys').argv,authorization=str(path),authorization_sha256=sha(path),bridge_files=auth['bridge_files'],readers=['scan_growth','OutputBudget.refresh','evaluation.guarded_size'],environment={key:os.environ.get(key) for key in ('PYTHONPATH','TASK9_IO_BRIDGE_AUTH','TASK9_IO_BRIDGE_AUTH_SHA256')})
    event_root=Path(auth['event_root'])
    if ROOT==Path('/workspace'):event_root=Path('/output')/event_root.relative_to(auth['output_root'])
    event_root.mkdir(parents=True,exist_ok=True)
    (event_root/f'install-{os.getpid()}.json').write_text(json.dumps(marker,indent=2)+'\n')
    log_event('BRIDGE_INSTALLED',authorization=str(path),authorization_sha256=sha(path),
        readers=['scan_growth','OutputBudget.refresh','evaluation.guarded_size'],
        code_files=auth['bridge_files'],argv=__import__('sys').argv)
