#!/usr/bin/env python3
"""Launch exactly one already frozen task10.14 run; no automatic retry."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import time


def write(path,value):
    temporary=path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)
    fd=os.open(str(path.parent),os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True);p.add_argument('--commit',required=True)
    args=p.parse_args();root=args.run.resolve()
    if not (root/'manifest.json').is_file():raise ValueError('freeze manifest before launch')
    if (root/'launch.json').exists() or (root/'budget.json').exists():raise ValueError('run already launched; no restart')
    epoch=time.time();started=time.monotonic()
    log=Path(__file__).resolve().parents[1]/'logs/task10'/f'{root.name}-eval.log'
    log.parent.mkdir(parents=True,exist_ok=True)
    # Shell guard exists before Python startup; inner timeout and worker share
    # this original epoch. TERM at hard-2, KILL at hard; cleanup starts hard-20.
    shell='''remaining=$(awk -v start="$TASK10_STARTED_EPOCH" -v now="$(date +%s.%N)" 'BEGIN {left=start+5400-now-2; if(left<=0)exit 124; printf "%.9f",left}'); exec timeout --signal=TERM --kill-after=2s "${remaining}s" python3 -u -m task10.validation supervise --run "$1"'''
    words=['docker','exec','--user','1004:1004','-e','PYTHONPATH=/workspace/src',
        '-e','CUBLAS_WORKSPACE_CONFIG=:4096:8','-e','TASK10_PHYSICAL_GPU=1',
        '-e',f'TASK10_CODE_COMMIT={args.commit}','-e',f'TASK10_STARTED_EPOCH={epoch}',
        'forem-task10-runtime','bash','-c',shell,'task10.14','/workspace/results/task10/'+root.name]
    command=['sg','docker','-c',shlex.join(words)]
    evidence=dict(run_id=root.name,code_commit=args.commit,parent_pid=os.getpid(),command=command,
        started_epoch=epoch,deadline_epoch=epoch+5400,started_monotonic=started,max_seconds=5400,
        max_real_decisions=5400,max_episodes=36,max_updates=0,log=str(log),status='launching',retries=0)
    write(root/'launch.json',evidence)
    with log.open('x') as stream:
        child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT)
        evidence.update(status='running',docker_client_pid=child.pid);write(root/'launch.json',evidence)
        rc=child.wait()
    evidence.update(status='process_exited',returncode=rc,finished_epoch=time.time(),wall_seconds=time.monotonic()-started)
    write(root/'launch.json',evidence)
    print(json.dumps(evidence),flush=True)
    return 0 if rc==0 else 1


if __name__=='__main__':raise SystemExit(main())
