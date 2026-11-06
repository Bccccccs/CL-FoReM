#!/usr/bin/env python3
"""One exact task10.17 long run; manual resume retains original ledger/epoch.

The caller detaches this launcher using start_new_session=True and independent
stdout/stderr. It never retries. A separate driver may invoke C after it exits.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import time


ROOT=Path(__file__).resolve().parents[1]


def write(path,value):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location('task10_long_runtime',ROOT/'src/task10/runtime.py')
    module=module_from_spec(spec);spec.loader.exec_module(module)
    module.atomic_json(path,value)


def launch(args):
    root=args.run.resolve()
    if root.parent != (ROOT/'results/task10').resolve():
        raise ValueError('run must be directly under this worktree forem/results/task10')
    if args.resume:
        evidence=json.loads((root/'launch.json').read_text())
        ledger=json.loads((root/'training-budget.json').read_text())
        if evidence['code_commit']!=args.commit:
            raise ValueError('resume commit differs')
        if evidence['status']!='process_exited':
            raise ValueError('previous launch has no proven exit; refuse resume')
        if ledger['in_flight'] or ledger['reserved_decisions']!=ledger['completed_decisions']:
            raise ValueError('uncovered real decisions cannot be replayed')
        if evidence['deadline_epoch']!=ledger['deadline_epoch'] or evidence['started_epoch']!=ledger['started_epoch']:
            raise ValueError('original epoch/ledger mismatch')
        # Exact checkpoint ledger/hash/version and prior worker liveness are
        # enforced again by load_decision_boundary before mutable restoration.
        epoch,started=ledger['started_epoch'],ledger['started_monotonic']
        checkpoint=args.resume.resolve()
        checkpoint.relative_to(root/'checkpoints')
        if not checkpoint.is_file():raise ValueError('missing original-run checkpoint')
        attempt=len(evidence.get('attempts',[]))+1
        previous={k:v for k,v in evidence.items() if k!='attempts'}
        attempts=evidence.get('attempts',[])+[previous]
    else:
        root.mkdir(parents=True,exist_ok=False)
        epoch,started=time.time(),time.monotonic()
        attempt=0;attempts=[]
        checkpoint=None
    if time.time()>=epoch+194400:
        raise TimeoutError('original 54-hour wall already exhausted')
    config=(args.config or ROOT/'config/task10/kl_10k.json').resolve()
    config_relative=config.relative_to(ROOT)
    if not config.is_file():raise ValueError('configuration file missing')
    initial=[]
    if args.initial_reference is not None:
        initial_path=args.initial_reference.resolve()
        initial_relative=initial_path.relative_to(ROOT)
        if not initial_path.is_file():raise ValueError('same-seed initial reference missing')
        initial=['--initial-reference',str(Path('/workspace')/initial_relative)]
    if not args.resume and not initial:
        raise ValueError('fresh launch requires same-seed full initial reference')
    output='/workspace/results/task10/'+root.name
    logdir=ROOT/'logs/task10'/root.name
    logdir.mkdir(parents=True,exist_ok=True)
    stdout=logdir/f'train-attempt-{attempt}.stdout'
    stderr=logdir/f'train-attempt-{attempt}.stderr'
    words=['docker','exec','--user','1004:1004',
        '-e','PYTHONPATH=/workspace/src','-e','CUDA_VISIBLE_DEVICES=0',
        '-e','OMP_NUM_THREADS=2','-e','TASK10_PHYSICAL_GPU=1',
        '-e',f'TASK10_CODE_COMMIT={args.commit}',
        '-e',f'TASK10_STARTED_EPOCH={epoch}',
        '-e',f'TASK10_STARTED_MONOTONIC={started}',
        'forem-task10-runtime','bash','/workspace/scripts/task10_long_run.sh',output,
        '--config',str(Path('/workspace')/config_relative),*initial]
    if checkpoint is not None:
        words.extend(['--resume',str(Path('/workspace')/checkpoint.relative_to(ROOT))])
    command=['sg','docker','-c',shlex.join(words)]
    evidence=dict(run_id=root.name,code_commit=args.commit,launcher_pid=os.getpid(),
        launcher_ppid=os.getppid(),launcher_sid=os.getsid(0),command=command,
        started_epoch=epoch,deadline_epoch=epoch+194400,started_monotonic=started,
        deadline_monotonic=started+194400,max_seconds=194400,max_real_decisions=10000,
        max_online_updates=9000,stdout=str(stdout),stderr=str(stderr),status='launching',
        retries=0,resume_attempted=bool(args.resume),attempts=attempts,attempt=attempt)
    write(root/'launch.json',evidence)
    with stdout.open('x') as out,stderr.open('x') as err:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
        evidence.update(status='running',docker_client_pid=child.pid)
        write(root/'launch.json',evidence)
        rc=child.wait()
    evidence.update(status='process_exited',returncode=rc,finished_epoch=time.time(),
        wall_seconds=time.monotonic()-started)
    write(root/'launch.json',evidence)
    print(json.dumps(evidence),flush=True)
    return 0 if rc==0 else 1


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--commit',required=True)
    p.add_argument('--config',type=Path)
    p.add_argument('--resume',type=Path)
    p.add_argument('--initial-reference',type=Path)
    return launch(p.parse_args(argv))


if __name__=='__main__':raise SystemExit(main())
