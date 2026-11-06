#!/usr/bin/env python3
import json,shutil,hashlib,subprocess,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
root=Path('/home/ybc/projects/CL-FoReM/forem');original=root/'results/task12/t12-abc-20261104-r1';out=root/'results/task12/t12-bc-20261104-r2';logs=root/'logs/task12/t12-bc-20261104-r2'
assert not (out/'ledger.json').exists(), 'refuse overwrite active/completed ledger'
out.mkdir(exist_ok=True);logs.mkdir(exist_ok=True)
for file in ('task12_continue.py','task12_continue_launch.py','task12_heatmap.py'):shutil.copy(root/'scripts'/file,out/file)
(out/'code-version.json').write_text(json.dumps(dict(reference_run=str(original),reference_head=(original/'reference-head.txt').read_text().strip(),source='reuse r1 frozen-source; no full rehash',entry_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.glob('*.py')}),indent=2))
for name,cmd in [('gpu',['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv']),('gpu-processes',['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv']),('containers',['sg','docker','-c','docker ps --format "{{.Names}} {{.Status}}"'])]:
 p=subprocess.run(cmd,capture_output=True,text=True,check=True);(logs/(name+'.txt')).write_text(p.stdout)
assert 'GPU-656ca5c1-681f-48a2-7d1f-a00824723f68' not in (logs/'gpu-processes.txt').read_text()
cmd=['sg','docker','-c',f'docker run --rm --name forem-task12-bc-r2 --gpus device=2 --network none --user 1004:1004 --cpuset-cpus 8-9 --shm-size 1g -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/original/frozen-source/src:/run -e OMP_NUM_THREADS=2 -e CUDA_VISIBLE_DEVICES=0 -e MPLCONFIGDIR=/tmp/matplotlib -e PYTORCH_KERNEL_CACHE_PATH=/tmp/torch-kernels -e CUBLAS_WORKSPACE_CONFIG=:4096:8 -v {root}:/workspace:ro -v {original}:/original:ro -v {out}:/run --entrypoint /opt/python310/bin/python3 mm_husky:node01 -u /run/task12_continue.py --output /run --original /original']
ledger=dict(run_id=out.name,started=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),started_monotonic=time.monotonic(),started_epoch=time.time(),engineering_estimate_s=1500,engineering_window_adjustable=True,stops='semantic mismatch stops C; STOP file interrupts at actor boundary and flushes partial; no A or new states; C at most10 updates',expected_rollouts=dict(grid_replay=24,rule_first=8,rule_replay=8,decoded_max=13),resource=dict(physical_gpu=2,uuid='GPU-656ca5c1-681f-48a2-7d1f-a00824723f68',logical_gpu=0,cpu='8-9',container='forem-task12-bc-r2'),argv=cmd,status='active')
(out/'ledger.json').write_text(json.dumps(ledger,indent=2));(logs/'command.json').write_text(json.dumps(cmd,indent=2))
with (logs/'stdout.txt').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
ledger.update(status='returned',returncode=p.returncode,wall_s=time.monotonic()-ledger['started_monotonic'],ended=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat());(out/'ledger.json').write_text(json.dumps(ledger,indent=2));print(json.dumps(ledger))
