#!/usr/bin/env python3
"""Host launcher for an explicitly approved stage-L run in existing forem-dev.
Never starts/stops containers or operates another run. Records exact argv/PID.
"""
import argparse,json,os,shlex,subprocess,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--variant',choices=['sync','async'],required=True)
    p.add_argument('--gate',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    gate_path=Path(a.gate).resolve();out=Path(a.output).resolve()
    container_root=Path('/root/mm_husky_ws')
    container_gate=container_root/gate_path.relative_to(root)
    container_out=container_root/out.relative_to(root)
    gate=json.loads(gate_path.read_text());gpu='2' if a.variant=='sync' else '3'
    if not gate['allow_formal'] or gate['hours_per_5M'][a.variant]>48:
        raise RuntimeError('formal performance gate not satisfied')
    uuid=subprocess.check_output(['nvidia-smi','-i',gpu,'--query-gpu=uuid','--format=csv,noheader'],text=True).strip()
    compute=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name','--format=csv,noheader'],text=True)
    if any(row.split(',')[0].strip()==uuid for row in compute.splitlines()):
        raise RuntimeError('allocated GPU has compute processes')
    if out.exists():raise RuntimeError('new formal output must not exist; use documented supervisor resume for an existing run')
    out.mkdir(parents=True)
    cmd=['docker','exec','-e','CUDA_VISIBLE_DEVICES='+gpu,
         '-e','PYTHONPATH=/root/mm_husky_ws/src','-e','OMP_NUM_THREADS=2',
         '-e','MKL_NUM_THREADS=2','-e','PYTHONDONTWRITEBYTECODE=1',
         '-w',str(container_root),'forem-dev','python3','-u',
         'scripts/task7_lower_supervise.py','--config','config/task7/lower_train.json',
         '--variant',a.variant,'--environments','256','--output',str(container_out),
         '--gate',str(container_gate)]
    with (out/'host.log').open('a') as log:
        proc=subprocess.Popen(['sg','docker','-c',shlex.join(cmd)],
                              stdout=log,stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL,start_new_session=True)
    record=dict(time=time.time(),variant=a.variant,physical_gpu=gpu,gpu_uuid=uuid,
                host_launcher_pid=proc.pid,argv=cmd,compute_before=compute,
                gate=str(gate_path),output=str(out))
    (out/'launch.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(record),flush=True)

if __name__=='__main__':main()
