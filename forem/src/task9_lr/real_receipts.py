"""Real preparation wait receipts and evidence-bound allocation attribution.

This module issues no execution authority. A root wait does not certify its
publisher's exit, descendants, device isolation, or complete session costs.
Missing independent allocation evidence stays UNKNOWN even for CPU commands.
"""
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import shlex
import signal
import shutil
import subprocess
import time
import uuid

from . import clock
from .runtime import sha256

WAIT = 'task9-lr-real-root-wait-v1'
OBSERVATION = 'task9-lr-real-inspect-observation-v1'
ALLOCATION = 'task9-lr-real-allocation-review-v1'
WRITER = 'task9.11.17-receipt-owner'
REVIEWER = 'task9.11.17.1-device-reviewer'
POLICY = dict(format='task9-lr-real-receipt-policy-v1', writer=WRITER,
              reviewer=REVIEWER, cpu_basis='strict-container-allocation',
              host_cpu_inference=False, control_tail='UNKNOWN-until-externally-closed')


def number(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
        raise ValueError('real receipt UNKNOWN/nonfinite number')
    return v


def canonical(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path or path.is_symlink():
        raise ValueError('canonical absolute receipt path required')
    return path


def bound(path):
    path = canonical(path)
    return dict(path=str(path), sha256=sha256(path))


def read(ref):
    if not isinstance(ref, dict):
        raise ValueError('real receipt reference missing')
    path = canonical(ref['path'])
    if not path.is_file() or sha256(path) != ref.get('sha256'):
        raise ValueError('real receipt missing/changed')
    return json.loads(path.read_text())


def identity(pid):
    # comm may contain spaces/parentheses; starttime is field 22 after its last ).
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, start_ticks=int(fields[19]), boot=clock.boot())


def capture(offset=None):
    mono = time.monotonic()
    offset = time.time()-mono if offset is None else offset
    boot = clock.boot()
    return dict(monotonic=mono, epoch=mono+offset, offset=offset,
                boot=boot, domain='system:'+boot, generation=None)


def wait_command(root, argv, *, cwd, run_id, stage='prepare', writer=WRITER,
                 timeout=60, sources=()):
    """Measure an explicitly authorized CPU preparation command; no device claim.

    The caller owns scope authorization. This helper records nonzero and timeout
    costs too; it is never a replacement for stage admission or release checks.
    """
    root = canonical(root); cwd = canonical(cwd)
    if writer != WRITER or stage not in ('prepare', 'review', 'g1', 'gate-evaluate', 'profile', 'remaining', 'final-test'):
        raise ValueError('preparation receipt owner/stage mismatch')
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) and '\0' not in a for a in argv):
        raise ValueError('literal argv required')
    if not isinstance(run_id, str) or not run_id or number(timeout) <= 0:
        raise ValueError('run identity/positive timeout required')
    before = [bound(p) for p in sources]
    root.mkdir(parents=True, exist_ok=False)
    snapshots_before = []
    for n, original in enumerate(before):
        target = root/'sources-before'/str(n)
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(original['path'], target)
        snap = bound(target)
        if snap['sha256'] != original['sha256']:raise ValueError('source changed before launch')
        snapshots_before.append(snap)
    launch = capture(); offset = launch['epoch']-launch['monotonic']
    reservation = dict(format='task9-lr-real-wait-reservation-v1', run_id=run_id,
        stage=stage, writer=writer, argv=argv, cwd=str(cwd), timeout_s=timeout,
        writer_process=identity(os.getpid()), started_clock=launch,
        source_before=before, synthetic_fixture=False, execution_authority=False)
    reservation_ref = clock.publish(root/'reservation.json', reservation)
    start = capture(offset); process = None; child_identity = None
    error = None; timed_out = False; rc = None
    # Regular files cannot keep communicate() blocked on an escaped descendant.
    # Descendant completion is still UNKNOWN and never promoted by this wait.
    with (root/'stdout.bin').open('xb') as stdout, (root/'stderr.bin').open('xb') as stderr:
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr, close_fds=True, start_new_session=True)
            child_identity = identity(process.pid)
            try:
                rc = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                # Only the pinned root identity is reaped. A missing wait remains
                # LAUNCH/WAIT UNKNOWN rather than spending an unbounded drain.
                try: rc = process.wait(timeout=1)
                except subprocess.TimeoutExpired: error = 'root wait still UNKNOWN after kill'
        except BaseException as exc:
            error = repr(exc)
            if process is not None and process.returncode is None:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                try: rc = process.wait(timeout=1)
                except subprocess.TimeoutExpired: pass
        end = capture(offset)
        for f in (stdout, stderr):
            f.flush(); os.fsync(f.fileno())
    after = [bound(p) for p in sources]
    snapshots_after = []
    for n, original in enumerate(after):
        target = root/'sources-after'/str(n)
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(original['path'], target)
        snap = bound(target)
        if snap['sha256'] != original['sha256']:raise ValueError('source changed while closing receipt')
        snapshots_after.append(snap)
    receipt = dict(format=WAIT, status='ROOT_WAIT_RETURNED' if process is not None and rc is not None else 'LAUNCH_FAILED',
        run_id=run_id, stage=stage, writer=writer, argv=argv, cwd=str(cwd),
        reservation=reservation_ref, child=child_identity, exit_code=rc,
        timed_out=timed_out, error=error, started_clock=start, completed_clock=end,
        started_epoch=start['epoch'], finished_epoch=end['epoch'],
        wall_s=end['monotonic']-start['monotonic'], stdout=bound(root/'stdout.bin'),
        stderr=bound(root/'stderr.bin'), source_before=before, source_after=after,
        source_snapshots_before=snapshots_before, source_snapshots_after=snapshots_after,
        source_integrity='UNCHANGED' if before == after else 'CHANGED',
        synthetic_fixture=False, execution_authority=False,
        publisher_exit='UNKNOWN', descendant_completion='UNKNOWN',
        device_attribution='UNKNOWN', full_session_cost='UNKNOWN')
    ref = clock.publish(root/'wait-receipt.json', receipt)
    return ref


def validate_wait(ref):
    v = read(ref)
    if v.get('format') != WAIT or v.get('status') != 'ROOT_WAIT_RETURNED' or v.get('synthetic_fixture') is not False or v.get('execution_authority') is not False:
        raise ValueError('real actual root wait missing')
    r = read(v['reservation'])
    if r.get('format') != 'task9-lr-real-wait-reservation-v1' or r.get('synthetic_fixture') is not False:
        raise ValueError('real reservation missing')
    for k in ('run_id', 'stage', 'writer', 'argv', 'cwd', 'source_before'):
        if r.get(k) != v.get(k):
            raise ValueError('real launch/receipt identity mismatch: '+k)
    if v.get('writer') != WRITER or v.get('stage') not in ('prepare', 'review', 'g1', 'gate-evaluate', 'profile', 'remaining', 'final-test'):
        raise ValueError('real wait owner/stage mismatch')
    child = v.get('child', {})
    if not isinstance(child.get('pid'), int) or isinstance(child.get('pid'), bool) or child['pid'] <= 0 or not isinstance(child.get('start_ticks'), int) or child['start_ticks'] < 0:
        raise ValueError('actual child identity missing')
    if isinstance(v.get('exit_code'), bool) or not isinstance(v.get('exit_code'), int):
        raise ValueError('actual root exit code missing')
    start = v['started_clock']; end = v['completed_clock']; reservation_clock = r['started_clock']
    for point in (reservation_clock, start, end):
        number(point.get('epoch')); number(point.get('monotonic'))
        number(point.get('offset'))
        if abs(point['epoch']-point['monotonic']-point['offset']) > 1e-5 or abs(point['offset']-reservation_clock.get('offset', -1)) > 1e-5 or point.get('generation') is not None or point.get('domain') != 'system:'+str(child.get('boot')):
            raise ValueError('real clock capture mapping/domain changed')
        if point.get('boot') != child.get('boot') or point.get('boot') != r.get('writer_process', {}).get('boot'):
            raise ValueError('real wait clock/boot domain mismatch')
    if abs(start['epoch']-reservation_clock['epoch']-(start['monotonic']-reservation_clock['monotonic'])) > .001:
        raise ValueError('reservation/actual launch clock mismatch')
    wall = number(v['wall_s'])
    if start['monotonic'] < reservation_clock['monotonic'] or end['monotonic'] < start['monotonic'] or abs(end['monotonic']-start['monotonic']-wall) > 1e-8:
        raise ValueError('actual root wait monotonic interval invalid')
    if v.get('started_epoch') != start['epoch'] or v.get('finished_epoch') != end['epoch'] or abs(end['epoch']-start['epoch']-wall) > .001:
        raise ValueError('actual wait epoch mapping invalid')
    for key, snapshots in [('source_before','source_snapshots_before'),('source_after','source_snapshots_after')]:
        if len(v[key]) != len(v.get(snapshots, [])):raise ValueError('frozen source coverage missing')
        for original, frozen in zip(v[key],v[snapshots]):
            if bound(frozen['path']) != frozen or frozen['sha256'] != original['sha256']:
                raise ValueError('frozen actual wait source changed')
    if v.get('source_integrity') != ('UNCHANGED' if v['source_before'] == v['source_after'] else 'CHANGED'):
        raise ValueError('actual source integrity status mismatch')
    for key in ('stdout', 'stderr'):
        if bound(v[key]['path']) != v[key]:
            raise ValueError('actual wait output changed')
    if any(v.get(k) != 'UNKNOWN' for k in ('publisher_exit', 'descendant_completion', 'device_attribution', 'full_session_cost')):
        raise ValueError('root wait cannot certify device/control/session completion')
    return v


def observe_container(root, container_id, *, run_id):
    """Read-only inspect observer, for a future independent allocation review."""
    if not re.fullmatch(r'[0-9a-f]{64}', container_id):
        raise ValueError('exact container ID required')
    root = canonical(root)
    args = ['sg', 'docker', '-c', shlex.join(['docker', 'inspect', container_id])]
    ref = wait_command(root, args, cwd=Path.cwd().resolve(), run_id=run_id)
    wait = validate_wait(ref)
    if wait['exit_code'] != 0:
        raise ValueError('inspect observation failed; charged wait retained')
    result = json.loads(Path(wait['stdout']['path']).read_bytes())
    if not isinstance(result, list) or len(result) != 1 or result[0].get('Id') != container_id:
        raise ValueError('exact inspect observation identity mismatch')
    return clock.publish(root/'inspect-observation.json', dict(format=OBSERVATION,
        wait_receipt=ref, inspect=result[0], synthetic_fixture=False))


def inspection(ref):
    obs = read(ref)
    if obs.get('format') != OBSERVATION or obs.get('synthetic_fixture') is not False:
        raise ValueError('real inspect observation required')
    wait = validate_wait(obs['wait_receipt'])
    if wait['exit_code'] != 0 or json.loads(Path(wait['stdout']['path']).read_bytes()) != [obs['inspect']]:
        raise ValueError('inspect raw output/exit mismatch')
    ident = obs['inspect'].get('Id')
    if wait['argv'] != ['sg', 'docker', '-c', shlex.join(['docker', 'inspect', ident])]:
        raise ValueError('inspect argv not exact read-only observation')
    return obs['inspect'], wait


def container_command(argv, container_id):
    if len(argv) == 3 and argv[:2] == ['sg', 'docker']:
        raise ValueError('literal docker exec command missing')
    if len(argv) == 4 and argv[:3] == ['sg', 'docker', '-c']:
        parsed = shlex.split(argv[3])
        if shlex.join(parsed) != argv[3]:
            raise ValueError('noncanonical shell wrapper cannot prove container-only execution')
        argv = parsed
    if len(argv) < 4 or argv[:3] != ['docker', 'exec', container_id] or any(x in (';', '&&', '|', '||', '&') for x in argv):
        raise ValueError('actual wait not enclosed exact-container exec')


def reviewed_intervals(p, item, *, scope=None):
    """Consume independently reviewed real allocation evidence in GPU readers.

    No producer here signs an independent verdict. Merely assigning [] devices,
    env flags, a CPU label or a synthetic receipt cannot enter this path.
    """
    if p.get('real_receipt_policy') != POLICY:
        raise ValueError('approved real receipt reader policy missing')
    if p.get('continuation', {}).get('synthetic_fixture') is True or p.get('synthetic_fixture') is True:
        raise ValueError('real attribution cannot enter synthetic scope')
    ref = item.get('real_wait_receipt'); wait = validate_wait(ref)
    if wait['run_id'] != p.get('run_id'):
        raise ValueError('real wait namespace mismatch')
    for key in ('argv','exit_code','wall_s','started_epoch','finished_epoch','started_clock','completed_clock','stage'):
        if item.get(key) != wait.get(key):
            raise ValueError('real source/actual wait mismatch: '+key)
    if scope is not None and (abs(wait['started_epoch']-scope[0]) > 1e-6 or abs(wait['finished_epoch']-scope[1]) > 1e-6):
        raise ValueError('attribution does not cover actual source wait')
    review = read(item.get('gpu_evidence', {}).get('review'))
    if review.get('format') != ALLOCATION or review.get('reviewer') != POLICY['reviewer'] or review.get('reviewer') == wait['writer'] or review.get('status') != 'ACCEPTED' or review.get('synthetic_fixture') is not False or review.get('wait_receipt') != ref or review.get('run_id') != p['run_id']:
        raise ValueError('independent real allocation review missing/identity mismatch')
    before, bw = inspection(review['before']); after, aw = inspection(review['after'])
    ident = before.get('Id')
    if not re.fullmatch(r'[0-9a-f]{64}', ident or '') or after.get('Id') != ident:
        raise ValueError('allocation exact container identity mismatch')
    container_command(wait['argv'], ident)
    if bw['finished_epoch'] > wait['started_epoch'] or aw['started_epoch'] < wait['finished_epoch'] or bw['child']['boot'] != wait['child']['boot'] or aw['child']['boot'] != wait['child']['boot']:
        raise ValueError('allocation observations do not bracket actual wait')
    from .gpu_costs import allocation
    requests = before.get('HostConfig', {}).get('DeviceRequests')
    devices = [] if requests == [] else allocation(p, before)
    after_devices = [] if after.get('HostConfig', {}).get('DeviceRequests') == [] else allocation(p, after)
    if after_devices != devices or before.get('HostConfig') != after.get('HostConfig') or before.get('Mounts') != after.get('Mounts'):
        raise ValueError('allocation changed across actual wait')
    bs = before.get('State', {}); es = after.get('State', {})
    if bs.get('Running') is not True or bs.get('StartedAt') != es.get('StartedAt'):
        raise ValueError('allocation not continuous/no restart proof')
    if es.get('Running') is not True:
        raise ValueError('stopped allocation needs independently closed terminal interval; UNKNOWN')
    text = bs.get('StartedAt', '')
    parsed_start = dt.datetime.fromisoformat(re.sub(r'(\.\d{6})\d+', r'\1', text).replace('Z', '+00:00'))
    if parsed_start.tzinfo is None:
        raise ValueError('allocation start requires an absolute timezone')
    started = parsed_start.timestamp()
    if not 0 <= started <= bw['started_epoch']:
        raise ValueError('allocation start outside witnessed interval')
    if not devices:
        host = before['HostConfig']
        if host.get('DeviceRequests') != [] or host.get('Devices') != [] or host.get('DeviceCgroupRules') not in (None, []) or host.get('Privileged') is not False or host.get('Runtime') != 'runc' or host.get('PidMode') == 'host':
            raise ValueError('CPU allocation isolation incomplete UNKNOWN')
        mounts = before.get('Mounts')
        if not isinstance(mounts, list):
            raise ValueError('CPU allocation mounts evidence missing')
        for m in mounts:
            for key in ('Source', 'Destination'):
                path = Path(m.get(key, '/'))
                if not path.is_absolute() or path == Path('/') or any(path == Path(x) or path.is_relative_to(x) or Path(x).is_relative_to(path) for x in ('/dev', '/proc', '/sys', '/run', '/var/run')):
                    raise ValueError('CPU container exposes host device/control path UNKNOWN')
        return []
    # Full allocated container window includes idle time; union handles overlap.
    return [dict(device=d, started_epoch=started, finished_epoch=aw['finished_epoch']) for d in devices]


def cost_source(ref, *, allocation_review=None):
    """Map verified root wait to the existing cost-event source schema.

    Device evidence is independent and optional here; inventory rejects missing
    attribution. Publication/control reservations are still a separate contract.
    """
    v = validate_wait(ref)
    return dict(format='task9-lr-measured-command-v1', status='CLOSED',
        argv=v['argv'], exit_code=v['exit_code'], wall_s=v['wall_s'],
        started_epoch=v['started_epoch'], finished_epoch=v['finished_epoch'],
        started_clock=v['started_clock'], completed_clock=v['completed_clock'],
        stage=v['stage'], parent_event_id=None, synthetic_fixture=False,
        execution_allowed=False, real_wait_receipt=ref,
        gpu_evidence=dict(format=ALLOCATION, review=allocation_review),
        full_session_cost='UNKNOWN', publisher_exit='UNKNOWN')
