#!/usr/bin/env python3
"""One unique online-trial launch, never retries or extends its original epoch."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import time


def write(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)
    descriptor=os.open(str(path.parent),os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True);p.add_argument('--commit',required=True)
    p.add_argument('--config',type=Path)
    args=p.parse_args();root=args.run.resolve()
    config_args=[]
    if args.config is not None:
        config_path=args.config.resolve()
        config_relative=config_path.relative_to(Path(__file__).resolve().parents[1])
        if not config_path.is_file():
            raise ValueError('configuration file does not exist')
        config_args=['--config',str(Path('/workspace')/config_relative)]
    root.mkdir(parents=True,exist_ok=False)
    epoch=time.time();started=time.monotonic()
    output='/workspace/results/task10/'+root.name
    log=Path(__file__).resolve().parents[1]/'logs/task10'/f'{root.name}-train.log'
    words=['docker','exec','--user','1004:1004','-e','PYTHONPATH=/workspace/src',
           '-e','TASK10_PHYSICAL_GPU=1','-e',f'TASK10_CODE_COMMIT={args.commit}',
           '-e',f'TASK10_STARTED_EPOCH={epoch}','forem-task10-runtime',
           'bash','/workspace/scripts/task10_run_bounded.sh','train',output,'--run-profile','online-trial']
    words.extend(config_args)
    command=['sg','docker','-c',shlex.join(words)]
    evidence=dict(run_id=root.name,code_commit=args.commit,parent_pid=os.getpid(),command=command,
        started_epoch=epoch,deadline_epoch=epoch+25200,started_monotonic=started,
        max_seconds=25200,max_real_decisions=1200,max_online_updates=200,log=str(log),
        status='launching',retries=0,collector_resume_attempted=False)
    write(root/'launch.json',evidence)
    with log.open('w') as stream:
        child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT)
        evidence.update(status='running',docker_client_pid=child.pid);write(root/'launch.json',evidence)
        # The actual hard supervisor is inside the container, covering imports,
        # all worker phases and cleanup. This parent never restarts the child.
        rc=child.wait()
    evidence.update(status='process_exited',returncode=rc,finished_epoch=time.time(),
                    wall_seconds=time.monotonic()-started)
    write(root/'launch.json',evidence)
    print(json.dumps(evidence),flush=True)
    return 0 if rc==0 else 1
if __name__=='__main__':raise SystemExit(main())
