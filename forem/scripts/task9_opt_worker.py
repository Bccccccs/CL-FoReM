#!/usr/bin/env python3
"""One reviewed task9 opt GPU phase; cannot infer authorization from a G1 token."""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/'src') not in sys.path:sys.path.insert(0,str(ROOT/'src'))
from task9_opt.runtime import activate, artifact_digest, validate_formal_config
from task9_opt.admission import STOP_AT, read_release, validate_profile, save_readiness


def clock_now():
    return dt.datetime.now(dt.timezone.utc)


def run_g1(output,max_worker_s,token,gpu):
    """Bound the test child by both released cap and absolute cutoff/expiry.

    The existing10s tail is an engineering cleanup/evidence-writing reserve,
    not a measured guarantee. A late start never creates a pytest subprocess.
    """
    output=Path(output);started=time.monotonic()
    if not 0<max_worker_s<=token['max_worker_s']:raise ValueError('G1 budget above released cap')
    deadline=min(STOP_AT,dt.datetime.fromisoformat(token['expires_at']))
    tail=10.
    available=min(max_worker_s,(deadline-clock_now()).total_seconds())
    timeout=available-tail
    cmd=[sys.executable,'-B','-u','-m','pytest','-q','-p','no:cacheprovider',str(ROOT/'src/task9_opt/tests')]
    if timeout<=0:
        evidence=dict(status='NOT_READY_deadline',subprocess_started=False,exit_code=126,
            artifact_sha256=artifact_digest(),absolute_cutoff=deadline.isoformat(),
            cleanup_evidence_reserve_s=tail,available_s=available,physical_gpu=gpu)
        (output/'g1-result.json').write_text(json.dumps(evidence,indent=2)+'\n')
        return 126
    env=dict(os.environ,TASK9_TEST_DEVICE='cuda',CUBLAS_WORKSPACE_CONFIG=':4096:8',TASK9_EVIDENCE_DIR=str(output))
    try:
        with (output/'pytest.txt').open('x') as log:
            result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=timeout)
        rc=result.returncode
    except subprocess.TimeoutExpired:
        rc=124
    device_path=output/'device-path.json'
    devices=json.loads(device_path.read_text()) if device_path.is_file() else {}
    if not devices.get('policy_device','').startswith('cuda') or not devices.get('replay_device','').startswith('cuda'):rc=rc or 125
    evidence=dict(devices=devices,status='PASS' if rc==0 else 'FAIL',artifact_sha256=artifact_digest(),exit_code=rc,
        command=cmd,worker_wall_s=time.monotonic()-started,physical_gpu=gpu,subprocess_started=True,
        subprocess_timeout_s=timeout,cleanup_evidence_reserve_s=tail,absolute_cutoff=deadline.isoformat(),
        deterministic_test_only=True,production_settings_unchanged=True)
    (output/'g1-result.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence),flush=True)
    return rc


def record_worker_exception(argv,error):
    """Preserve recognized terminal reasons even if failure happens in smoke eval."""
    try:
        output=Path(argv[argv.index('--output')+1]).resolve()
    except (ValueError,IndexError):return
    owned=(ROOT/'results/task9/t9-opt-20261031').resolve()
    if output==owned or not output.is_relative_to(owned) or not output.is_dir():return
    status=('diverged' if isinstance(error,FloatingPointError) else
            'interrupted' if isinstance(error,(InterruptedError,TimeoutError)) else 'unknown_worker_failure')
    value=dict(status=status,stop_reason=str(error),exception_type=type(error).__name__,retry_allowed=False)
    (output/'worker-terminal.json').write_text(json.dumps(value,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--release',required=True)
    p.add_argument('--config')
    p.add_argument('--output',required=True)
    p.add_argument('--phase',required=True,choices=['g1','smoke512','smoke1000','profile','remaining'])
    p.add_argument('--max-worker-s',required=True,type=float)
    a=p.parse_args()
    stage='g1' if a.phase=='g1' else 'training-policy'
    token=read_release(a.release,stage)
    gpu=os.environ.get('CUDA_VISIBLE_DEVICES')
    if gpu not in ('0','1','2','3'):raise RuntimeError('exactly one physical GPU must be allocated')
    output=Path(a.output).resolve()
    owned=(ROOT/'results/task9/t9-opt-20261031').resolve()
    if not output.is_relative_to(owned) or output==owned:raise ValueError('output outside new owned run root')
    lock_root=ROOT/'logs/task9/t9-opt-20261031/locks';lock_root.mkdir(parents=True,exist_ok=True)
    with (lock_root/f'gpu{gpu}.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Queue and worker have separate checks. Only the selected physical card
        # must be free; old jobs on other cards are observers, never stopped.
        uuid=subprocess.check_output(['nvidia-smi','-i',gpu,'--query-gpu=uuid','--format=csv,noheader'],text=True).strip()
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
        if any(row.split(',')[0].strip()==uuid for row in apps.splitlines()):raise RuntimeError('allocated GPU is occupied')
        if a.max_worker_s<=0:raise ValueError('positive worker budget required')
        output.mkdir(parents=True,exist_ok=True)
        pidfile=output/f'{a.phase}.container-pid';pidfile.write_text(str(os.getpid())+'\n')
        started=time.monotonic()
        if a.phase=='g1':
            return run_g1(output,a.max_worker_s,token,gpu)
        if not a.config:raise ValueError('formal config required')
        config=json.loads(Path(a.config).read_text());validate_formal_config(config)
        if os.environ.get('CUBLAS_WORKSPACE_CONFIG') or os.environ.get('TASK8_SCENE_CACHE'):
            raise ValueError('unreviewed production execution override')
        if a.phase=='remaining':
            summary=json.loads((output/'profile-summary.json').read_text())
            evaluation=json.loads((output/'validation-0250000.json').read_text())
            cost=validate_profile(summary,evaluation,config['replay_capacity'])
            readiness=save_readiness(cost,summary,token)
            (output/'remaining-readiness.json').write_text(json.dumps(readiness,indent=2)+'\n')
            if readiness['status']!='ready':
                (output/'worker-terminal.json').write_text(json.dumps(dict(status=readiness['status'],stop_reason='reviewed policy cannot cover mature shutdown costs',readiness=readiness,retry_allowed=False),indent=2)+'\n')
                return 127
        activate()
        import torch
        from task8_lower.training import train, load_checkpoint
        from task8_lower.evaluation import evaluate
        from task7_lower.training import atomic_json
        if not torch.cuda.is_available():raise RuntimeError('no CPU fallback')
        torch.set_num_threads(config['threads'])
        save_allowance=token['save_allowance_s']
        available=(STOP_AT-dt.datetime.now(dt.timezone.utc)).total_seconds()
        wall=min(a.max_worker_s,available)-save_allowance
        if wall<=0:raise RuntimeError('no remaining execution plus save budget')
        if a.phase=='smoke512':
            if any(x.name!=pidfile.name for x in output.iterdir()):raise ValueError('smoke output already used; no retry')
            value=train(config,output,max_wall_s=wall,pause_after_consumed=512)
            # Atomic replacement of profile.pt at1000 leaves these hardlinked
            #512 evidence files intact; no checkpoint bytes are rewritten.
            for suffix in ('.pt','.meta.json','.actor.pt'):
                os.link(output/('profile'+suffix),output/('smoke512'+suffix))
            os.link(output/'profile-summary.json',output/'smoke512-summary.json')
        elif a.phase=='smoke1000':
            resume=output/'smoke512.pt'
            value=train(config,output,resume=resume,max_wall_s=wall,pause_after_consumed=1000)
            # There are no extra periodic full196 boundaries. This is exactly
            # the one approved smoke evaluation after the resumed1000 state.
            sac,_,_,_,_=load_checkpoint(output/'profile.pt','cuda')
            evaluate(sac,config,output/'smoke-evaluation.json',deadline=started+wall,
                     cancel=lambda:(output/'STOP').exists())
        elif a.phase=='profile':
            if any(x.name!=pidfile.name for x in output.iterdir()):raise ValueError('formal output already used; no budget reset')
            value=train(config,output,max_wall_s=wall,pause_after_consumed=250000)
        else:
            if (output/'final.pt').exists():raise ValueError('formal run already complete')
            value=train(config,output,resume=output/'profile.pt',max_wall_s=wall)
        atomic_json(output/f'{a.phase}-worker.json',dict(status='phase_returned',phase=a.phase,
            artifact_sha256=artifact_digest(),physical_gpu=gpu,container_pid=os.getpid(),
            worker_wall_s=time.monotonic()-started,max_worker_s=a.max_worker_s,
            result_status=value.get('status','final_returned')))
        print(json.dumps(dict(phase=a.phase,steps=value.get('steps',value.get('state',{}).get('steps')))),flush=True)
        return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as error:
        record_worker_exception(sys.argv,error)
        raise
