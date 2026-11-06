#!/usr/bin/env python3
"""One shared wall clock, no retries, dedicated GPU0 container."""
import json,subprocess,time,hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
root=Path('/home/ybc/projects/CL-FoReM');run='t12-abc-20261104-r1';out=root/'forem/results/task12'/run;logs=root/'forem/logs/task12'/run;logs.mkdir(parents=True,exist_ok=True)
# Read-only resource inspection immediately before the single launch.
for name,cmd in [('gpu',['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv']),('gpu-processes',['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_memory','--format=csv']),('containers',['sg','docker','-c','docker ps --format "{{.Names}} {{.Status}}"'])]:
 p=subprocess.run(cmd,capture_output=True,text=True,check=True);(logs/(name+'.txt')).write_text(p.stdout)
assert 'GPU-e2eab186-4b18-f63f-2ada-c61aa98ed587' not in (logs/'gpu-processes.txt').read_text()
start=time.monotonic();epoch=time.time();deadline=start+597
argv=['sg','docker','-c',f'docker run --rm --name forem-task12-abc-20261104-r1 --gpus device=0 --network none --user 1004:1004 --cpuset-cpus 8-9 --shm-size 1g -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/run/frozen-source/src:/run -e OMP_NUM_THREADS=2 -e CUDA_VISIBLE_DEVICES=0 -e CUBLAS_WORKSPACE_CONFIG=:4096:8 -v {root}/forem:/workspace:ro -v {out}:/run --entrypoint /usr/bin/timeout mm_husky:node01 --signal=TERM --kill-after=2s 598s /opt/python310/bin/python3 -u /run/task12_abc.py --output /run --deadline {deadline}']
ledger=dict(run_id=run,started=datetime.fromtimestamp(epoch,ZoneInfo('Asia/Shanghai')).isoformat(),started_epoch=epoch,started_monotonic=start,hard_deadline_monotonic=start+600,cooperative_deadline_monotonic=deadline,limits=dict(states=1,moving_per_sector=3,updates=10,wall_s=600),stage_order='A -> B -> C; STOP_A on any causal difference; budget applies to all attempts/control/replay/persistence',resource=dict(physical_gpu=0,uuid='GPU-e2eab186-4b18-f63f-2ada-c61aa98ed587',container='forem-task12-abc-20261104-r1',logical_gpu=0,cpus='8-9'),argv=argv,status='active')
(out/'ledger.json').write_text(json.dumps(ledger,indent=2));(logs/'command.json').write_text(json.dumps(argv,indent=2))
with (logs/'stdout.txt').open('w') as stream:
 p=subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT)
ledger.update(status='returned',returncode=p.returncode,ended=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),wall_s=time.monotonic()-start)
(out/'ledger.json').write_text(json.dumps(ledger,indent=2));print(json.dumps(ledger))
