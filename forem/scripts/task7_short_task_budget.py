#!/usr/bin/env python3
"""Host-only single-worker task7.24 budget launcher. No direct container bypass.
Reserve before launch; stale active reservations fail closed after a host crash.
GNU timeout runs INSIDE the container, so a lost Docker client cannot orphan an
unbounded worker. Entire process group receives TERM, then KILL after five sec.
"""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time


def write(path, value):
    tmp = path.with_suffix('.tmp')
    with tmp.open('w') as f:
        json.dump(value, f, indent=2); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def run(budget, seconds, label, command, log):
    budget = Path(budget); log = Path(log); log.parent.mkdir(parents=True, exist_ok=True)
    with budget.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        data = json.loads(budget.read_text())
        if data['active_jobs']:
            raise RuntimeError('unreconciled active reservation: inspect task container processes before recovery')
        available = data['limit_seconds'] - data['consumed_seconds']
        cap = min(float(seconds), available)
        if cap < 15:
            raise RuntimeError('insufficient cumulative task budget for bounded launch')
        if not command:
            raise ValueError('command required')
        # GPU3 exclusively; do not rely on a previous idle check.
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'], text=True)
        uuid = subprocess.check_output(['nvidia-smi', '-i', '3', '--query-gpu=uuid', '--format=csv,noheader'], text=True).strip()
        if any(uuid in row for row in apps.splitlines()):
            raise RuntimeError('GPU3 has another compute process; no launch')
        stamp = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
        entry = dict(label=label, command=command, start=stamp(), reserved_seconds=cap, host_pid=os.getpid(), log=str(log), physical_gpu=3)
        marker_dir=budget.parent/'budget-completions';marker_dir.mkdir(exist_ok=True)
        marker=marker_dir/f'{os.getpid()}-{time.time_ns()}.json'
        entry['completion_marker']=str(marker)
        data['consumed_seconds'] += cap
        data['active_jobs'] = [entry]
        write(budget, data)
        root = '/root/mm_husky_ws/build/task7.24/source'
        container_marker='/root/mm_husky_ws/results/task7/t7.24-short-20261023/budget-completions/'+marker.name
        supervisor="""import json,os,sys,subprocess
from pathlib import Path
rc=subprocess.call(sys.argv[2:])
p=Path(sys.argv[1]);tmp=p.with_suffix('.tmp')
with tmp.open('w') as f:
 json.dump(dict(job=os.environ['TASK7_SHORT_BUDGET_JOB'],rc=rc,pid=os.getpid()),f);f.flush();os.fsync(f.fileno())
os.replace(tmp,p)
sys.exit(rc)
"""
        inner = ['docker' ,'exec','-e','CUDA_VISIBLE_DEVICES=3','-e',f'TASK7_SHORT_BUDGET_JOB={entry["start"]}','-e',f'TASK7_SHORT_BUDGET_SECONDS={cap}','-e','TASK7_SHORT_BUDGET_FILE=/root/mm_husky_ws/results/task7/t7.24-short-20261023/budget.json','-e',f'PYTHONPATH={root}/src','-e','OMP_NUM_THREADS=2','-e','MKL_NUM_THREADS=2','-e','PYTHONDONTWRITEBYTECODE=1','-w',root,'forem-dev','python3','-u','-c',supervisor,container_marker,'timeout','--signal=TERM','--kill-after=5s',f'{cap-10:.3f}s',*command]
        started = time.monotonic(); rc = None
        # Do not detach on host TERM/INT: wait for the independent inner timeout.
        previous = {sig: signal.signal(sig, lambda *_: None) for sig in (signal.SIGTERM, signal.SIGINT)}
        try:
            with log.open('w') as output:
                output.write(json.dumps(entry)+'\n'); output.flush()
                rc = subprocess.call(['sg','docker','-c',shlex.join(inner)], stdout=output, stderr=subprocess.STDOUT)
        finally:
            wall = time.monotonic()-started
            entry.update(end=stamp(), rc=rc, wall_seconds=wall)
            completion=None
            try:
                payload=json.loads(marker.read_text())
                if payload['job']==entry['start'] and isinstance(payload['rc'],int) and payload['rc']>=0:completion=payload
            except (OSError,ValueError,KeyError,TypeError):pass
            entry['container_completion']=completion
            if completion is None:
                # Neither return code nor Docker-client lifetime proves that the
                # actual inner worker exited. Keep full charge and fail closed.
                data['active_jobs'] = [entry]
            else:
                data['consumed_seconds'] += wall-cap
                data['active_jobs'] = []
            data['commands'].append(entry)
            write(budget, data)
            for sig, handler in previous.items():signal.signal(sig, handler)
        if completion is None:raise RuntimeError('container completion unconfirmed; reservation retained and launches blocked')
        print(json.dumps(dict(label=label, rc=rc, wall_seconds=wall, consumed_seconds=data['consumed_seconds'],remaining_seconds=data['limit_seconds']-data['consumed_seconds'],log=str(log))), flush=True)
        return rc


def main():
    p=argparse.ArgumentParser();p.add_argument('--budget',required=True);p.add_argument('--seconds',type=float,required=True);p.add_argument('--label',required=True);p.add_argument('--log',required=True);p.add_argument('command',nargs=argparse.REMAINDER)
    a=p.parse_args();cmd=a.command[1:] if a.command[:1]==['--'] else a.command
    return run(a.budget,a.seconds,a.label,cmd,a.log)

if __name__=='__main__':raise SystemExit(main())
