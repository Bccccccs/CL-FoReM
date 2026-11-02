"""Bounded read-only diagnostic command launcher, task7.18.1."""
import sys,subprocess,time,json,datetime,os
from pathlib import Path
root=Path(__file__).resolve().parents[1];logs=root/'logs/task7/t7.18.1-r1-20261021';logs.mkdir(parents=True,exist_ok=True)
name,*args=sys.argv[1:]
q=subprocess.run(['nvidia-smi','--query-gpu=index,uuid','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout
uuid=[x.split(',')[1].strip() for x in q.splitlines() if x.split(',')[0].strip()=='0'][0]
comp=subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_memory','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout
if uuid in comp:raise SystemExit('GPU0 occupied: '+comp)
ledger=logs/'commands.jsonl';used=sum(json.loads(x)['wall_s'] for x in ledger.read_text().splitlines()) if ledger.exists() else 0
if used+590>3600:raise SystemExit('Conservative remaining budget below 590 seconds')
import shlex
cmd=['sg','docker','-c',shlex.join(['docker','exec','-e','CUDA_VISIBLE_DEVICES=0','-e','PYTHONPATH=/root/mm_husky_ws/src','-e','PYTHONDONTWRITEBYTECODE=1','-e','OMP_NUM_THREADS=2','-e','MKL_NUM_THREADS=2','-w','/root/mm_husky_ws','forem-dev','timeout','--signal=TERM','590']+args)]
start=time.monotonic()
with (logs/(name+'.log')).open('w') as f:
 p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT)
 (logs/(name+'.pid.json')).write_text(json.dumps({'host_launcher_pid':os.getpid(),'host_sg_pid':p.pid,'command':cmd,'stop':'docker timeout kills only this diagnostic child after 590s; never stop container/training'}))
 code=p.wait()
record={'time':datetime.datetime.now().astimezone().isoformat(),'name':name,'argv':cmd,'gpu_compute_before':comp,'wall_s':time.monotonic()-start,'exit_code':code}
with ledger.open('a') as f:f.write(json.dumps(record)+'\n')
print(json.dumps(record));print((logs/(name+'.log')).read_text()[-9000:]);sys.exit(code)
