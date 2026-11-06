"""Launch a CPU-only audit in the frozen image; do not touch run originals."""
import hashlib,json,os,shlex,subprocess,time
from pathlib import Path
workspace=Path('/home/ybc/projects/CL-FoReM-task9')
audit=Path(__file__).resolve().parent
run=workspace/'forem/results/task9/t9.10-paired-20261103T144811+0800'
cfg=json.loads((run/'run.json').read_text())
args=['docker','run','--rm','--read-only','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
 '--env','CUDA_VISIBLE_DEVICES=','--env','NVIDIA_VISIBLE_DEVICES=void','--env','PYTHONDONTWRITEBYTECODE=1','--env','OMP_NUM_THREADS=1','--env','OPENBLAS_NUM_THREADS=1',
 '--mount',f'type=bind,src={run},dst=/run-originals,readonly',
 '--mount',f'type=bind,src={audit},dst=/audit,readonly',
 '--mount',f'type=bind,src={workspace}/forem/doc/agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.csv,dst=/frozen.csv,readonly',
 '--workdir','/','--entrypoint','python3',cfg['image'],'-B','/audit/independent_sample_check.py','--run','/run-originals','--frozen','/frozen.csv']
assert '--gpus' not in args
before=time.time();result=subprocess.run(['sg','docker','-c',shlex.join(args)],capture_output=True,text=True);after=time.time()
(audit/'independent-cpu-sampling.stdout.json').write_text(result.stdout)
(audit/'independent-cpu-sampling.stderr.log').write_text(result.stderr)
report=dict(command=['sg','docker','-c',shlex.join(args)],exit_code=result.returncode,start_epoch=before,end_epoch=after,wall_s=after-before,no_gpus_requested=True,all_bind_mounts_readonly=True,outputs_in_original_run=False,stdout_bytes=len(result.stdout.encode()),stderr_bytes=len(result.stderr.encode()),script_sha256=hashlib.sha256((audit/'independent_sample_check.py').read_bytes()).hexdigest())
(audit/'independent-cpu-sampling-command.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(result.returncode)
