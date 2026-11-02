#!/usr/bin/env python3
"""Durable bounded phases; explicit repairs retain original deadlines/attempts."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from task10.runtime import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, required=True)
    parser.add_argument('--phase', choices=('performance', 'recovery_fixture', 'collector_boundary', 'verification'), required=True)
    parser.add_argument('--seconds', type=float, required=True)
    parser.add_argument('--continue-failed', action='store_true', help='explicit repair within the original absolute phase deadline')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    caps = dict(performance=900, recovery_fixture=300, collector_boundary=360, verification=240)
    if not 2 < args.seconds <= caps[args.phase]:
        parser.error('outside predeclared phase cap')
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('command required')
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    with args.ledger.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(args.ledger.read_text()) if args.ledger.exists() else dict(total_cap_seconds=1800, jobs={})
        old = state['jobs'].get(args.phase)
        if any(j['status'] == 'active' for j in state['jobs'].values()):
            raise RuntimeError('another phase active; GPU measurements are serialized')
        permitted = old is not None and old['cap_seconds'] == args.seconds and args.continue_failed and old['status'] == 'failed'
        if old is not None and not permitted:
            raise RuntimeError('phase already consumed; no automatic retry')
        if old is None and args.continue_failed:
            raise RuntimeError('no failed phase to continue')
        if sum(j['cap_seconds'] for j in state['jobs'].values())+(args.seconds if old is None else 0) > 1800:
            raise RuntimeError('cumulative declared caps exceed shared budget')
        started = time.monotonic()
        origin = time.time() if old is None else old['started_epoch']
        remaining = origin+args.seconds-time.time()
        if remaining <= 2:
            raise RuntimeError('original absolute phase deadline expired')
        history = [] if old is None else old.get('attempts', [old])
        job = dict(status='active', started_epoch=origin, cap_seconds=args.seconds, command=command,
                   supervisor_pid=os.getpid(), attempts=history)
        state['jobs'][args.phase] = job
        atomic_json(args.ledger, state)
        process = subprocess.Popen(command, start_new_session=True)
        job['worker_pid'] = process.pid
        atomic_json(args.ledger, state)
        try:
            code = process.wait(timeout=max(.01, remaining-(time.monotonic()-started)-2))
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=1)
            code = 124
        attempt = dict(returncode=code, command=command, elapsed_seconds=time.monotonic()-started,
                       started_epoch=time.time()-(time.monotonic()-started), finished_epoch=time.time(),
                       worker_pid=process.pid)
        job['attempts'].append(attempt)
        job.update(status='done' if code == 0 else 'failed', returncode=code,
                   elapsed_seconds=time.time()-origin, worker_seconds=sum(a['elapsed_seconds'] for a in job['attempts']),
                   finished_epoch=time.time())
        state['consumed_worker_seconds'] = sum(j.get('worker_seconds', j.get('elapsed_seconds', 0)) for j in state['jobs'].values())
        atomic_json(args.ledger, state)
        print(json.dumps(dict(phase=args.phase, **job)), flush=True)
        return code if 0 <= code <= 255 else 128-code


if __name__ == '__main__':
    raise SystemExit(main())
