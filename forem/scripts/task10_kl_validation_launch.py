#!/usr/bin/env python3
"""Launch one frozen KL validation; no retries or new training process."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

from task10_validation_launch import write


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--commit',required=True);args=p.parse_args(argv);root=args.run.resolve()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from task10_kl_validation import check_manifest
    check_manifest(json.loads((root/'manifest.json').read_text()))
    if (root/'launch.json').exists() or (root/'budget.json').exists():raise ValueError('run already launched; no restart')
    workspace=Path(__file__).resolve().parents[1]
    if root.parent != (workspace/'results/task10').resolve():raise ValueError('run must be directly under results/task10')
    epoch=time.time();started=time.monotonic();log=workspace/'logs/task10'/f'{root.name}-eval.log'
    log.parent.mkdir(parents=True,exist_ok=True)
    shell='''remaining=$(awk -v start="$TASK10_STARTED_EPOCH" -v now="$(date +%s.%N)" 'BEGIN {left=start+5400-now-2; if(left<=0)exit 124; printf "%.9f",left}'); exec timeout --signal=TERM --kill-after=2s "${remaining}s" python3 -u /workspace/scripts/task10_kl_validation.py supervise --run "$1"'''
    words=['docker','exec','--user','1004:1004','-e','PYTHONPATH=/workspace/src','-e','CUBLAS_WORKSPACE_CONFIG=:4096:8',
        '-e','TASK10_PHYSICAL_GPU=1','-e',f'TASK10_CODE_COMMIT={args.commit}','-e',f'TASK10_STARTED_EPOCH={epoch}',
        'forem-task10-runtime','bash','-c',shell,'task10.16.3','/workspace/results/task10/'+root.name]
    command=['sg','docker','-c',shlex.join(words)]
    evidence=dict(run_id=root.name,code_commit=args.commit,parent_pid=os.getpid(),command=command,
        started_epoch=epoch,deadline_epoch=epoch+5400,started_monotonic=started,max_seconds=5400,
        max_real_decisions=1800,max_episodes=12,max_updates=0,log=str(log),status='launching',retries=0)
    # Exclusive claim prevents concurrent callers from both starting workers.
    with (root/'launch.json').open('x') as stream:
        json.dump(evidence,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    with log.open('x') as stream:
        child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT)
        evidence.update(status='running',docker_client_pid=child.pid);write(root/'launch.json',evidence)
        rc=child.wait()
    evidence.update(status='process_exited',returncode=rc,finished_epoch=time.time(),wall_seconds=time.monotonic()-started)
    write(root/'launch.json',evidence);print(json.dumps(evidence),flush=True)
    return 0 if rc==0 else 1


if __name__=='__main__':raise SystemExit(main())
