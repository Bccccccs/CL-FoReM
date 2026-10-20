#!/usr/bin/env python3
"""Host receipt wrapper: serial bounded task7.6 runs, no container lifecycle actions."""
import json, subprocess, time, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]; run=sys.argv[1]; extra=sys.argv[2:]
out=root/'results/task7'/run; log=root/'logs/task7'/run; out.mkdir(parents=True,exist_ok=True); log.mkdir(parents=True,exist_ok=True)
base='/root/mm_husky_ws'; args=['docker','exec','-e','CUDA_VISIBLE_DEVICES=0','-e','OMP_NUM_THREADS='+('1' if '--threads' in extra and extra[extra.index('--threads')+1]=='1' else '2'),'-e','MKL_NUM_THREADS='+('1' if '--threads' in extra and extra[extra.index('--threads')+1]=='1' else '2'),'-e','OPENBLAS_NUM_THREADS='+('1' if '--threads' in extra and extra[extra.index('--threads')+1]=='1' else '2'),'-e','NUMEXPR_NUM_THREADS=2','forem-dev','timeout','540','python3','-u',base+'/scripts/bench_task7_ik.py','--urdf',base+'/results/task7/t7.6-bench-20261020-r1/model.urdf','--out',base+'/results/task7/'+run,*extra]
import shlex
if extra and extra[0]=='--entry':
    entry=extra[1]
    assert entry in ['bench_task7_bioik.py','bench_task7_supplement.py','bench_task7_verify.py']
    args=args[:args.index('timeout')]+['bash','-lc','source /opt/ros/noetic/setup.bash; source /root/mm_husky_ws/devel/setup.bash; exec timeout 540 python3 -u '+shlex.quote(base+'/scripts/'+entry)]
cmd=['sg','docker','-c',shlex.join(args)]; start=time.time()
with (log/'run.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=570)
receipt={'command':cmd,'start_unix':start,'end_unix':time.time(),'wall_s':time.time()-start,'exit_code':r.returncode}
(out/'command.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt,flush=True);sys.exit(r.returncode)
