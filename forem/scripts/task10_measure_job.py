#!/usr/bin/env python3
"""One durable, non-retriable bounded measurement phase; no training policy."""
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
        if args.phase in state['jobs'] or any(j['status'] == 'active' for j in state['jobs'].values()):
            raise RuntimeError('phase already consumed or another phase active; no automatic retry')
        if sum(j['cap_seconds'] for j in state['jobs'].values())+args.seconds > 1800:
            raise RuntimeError('cumulative declared caps exceed shared budget')
        started = time.monotonic()
        job = dict(status='active', started_epoch=time.time(), cap_seconds=args.seconds, command=command, supervisor_pid=os.getpid())
        state['jobs'][args.phase] = job
        atomic_json(args.ledger, state)
        process = subprocess.Popen(command, start_new_session=True)
        job['worker_pid'] = process.pid
        atomic_json(args.ledger, state)
        try:
            code = process.wait(timeout=max(.01, args.seconds-(time.monotonic()-started)-2))
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=1)
            code = 124
        job.update(status='done' if code == 0 else 'failed', returncode=code,
                   elapsed_seconds=time.monotonic()-started, finished_epoch=time.time())
        state['consumed_worker_seconds'] = sum(j.get('elapsed_seconds', 0) for j in state['jobs'].values())
        atomic_json(args.ledger, state)
        print(json.dumps(dict(phase=args.phase, **job)), flush=True)
        return code if 0 <= code <= 255 else 128-code


if __name__ == '__main__':
    raise SystemExit(main())
