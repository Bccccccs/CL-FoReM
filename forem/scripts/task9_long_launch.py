#!/usr/bin/env python3
"""task9.2 launcher: preflight, freeze snapshot, start 4 detached 3M runs (one per GPU) in forem-dev.

Host-side only. Without --execute it runs preflight and writes the plan, starting nothing.
Never stops or restarts existing processes; refuses if any precondition fails.
"""
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CROOT='/root/mm_husky_ws'
CONTAINER='forem-dev'
MAX_WALL_S=172800  # 48h x 3600 s/h, SRC-1158 wall cap; save-and-exit boundary, not a step cut
RUNS=[('B0',4718,0),('B0',4719,1),('B3',4718,2),('B3',4719,3)]
SMOKE_SNAPSHOT=ROOT/'logs/task9/t9-smoke-20261028/implementation-snapshot.json'
EXTRA=['scripts/task8_lower_train.py','src/task7_lower/recovery.py','src/task7_lower/training.py',
       'config/task8/lower_train_B0_prim.json','config/task8/lower_train_B3_prim.json','config/task8/primitive_scene.json',
       'scripts/task9_long_launch.py','scripts/task9_long_monitor.py']
MIN_FREE_BYTES=10**12  # derived ~660 GB for 4 runs x 13 full checkpoints; engineering margin


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.datetime.now().astimezone().isoformat()
def sh(argv,**kw):return subprocess.run(argv,capture_output=True,text=True,**kw)
def dexec(cmd):return sh(['docker','exec',CONTAINER,'sh','-c',cmd])


def contract_files():
    text=(ROOT/'src/task8_lower/training.py').read_text()
    start=text.index("names=[",text.index('def _contract'));end=text.index(']',start)
    return [s.strip().strip("'") for s in text[start+7:end].replace('\n','').split(',') if s.strip()]


def to_host(path):return ROOT/Path(path).relative_to(CROOT)


def preflight(run_id):
    errors=[];facts={}
    files=sorted(set(contract_files()+EXTRA+[f'config/task9/lower_train_{g}_prim_seed{s}.json' for g,s,_ in RUNS]))
    snapshot={f:sha(ROOT/f) for f in files}
    template=json.loads((ROOT/'config/task8/lower_train_B0_prim.json').read_text())
    pools={template[k] for k in ('pool','transfer_pool','evaluation_seeds')}
    for p in sorted(pools):snapshot[p]=sha(to_host(p))
    smoke={k.removeprefix('forem/'):v for k,v in json.loads(SMOKE_SNAPSHOT.read_text())['files'].items()}
    drift=sorted(f for f in snapshot if f in smoke and smoke[f]!=snapshot[f])
    facts['smoke_snapshot_common']=sorted(f for f in snapshot if f in smoke)
    if drift:errors.append(f'code/config drift since task9.1 smoke: {drift}')
    for g,s,gpu in RUNS:
        cfg=json.loads((ROOT/f'config/task9/lower_train_{g}_prim_seed{s}.json').read_text())
        base=json.loads((ROOT/f'config/task8/lower_train_{g}_prim.json').read_text())
        diff=sorted(k for k in set(cfg)|set(base) if cfg.get(k)!=base.get(k))
        if diff not in ([],['seed']) or cfg['seed']!=s:errors.append(f'{g}-{s} config differs from template beyond seed: {diff}')
        for k,v in dict(total_transfers=3000000,total_updates=4999743,environments=256,replay_capacity=100000,batch_size=256,
                        checkpoint_interval=250000,log_interval=1000,warmup_transfers=1000,map_backend='primitive-obb-v1',
                        environment_geometry_version='primitive-obb-v1',group=g).items():
            if cfg.get(k)!=v:errors.append(f'{g}-{s} {k}={cfg.get(k)!r} expected {v!r}')
        out=ROOT/f'results/task9/{run_id}/{g}-seed{s}'
        if out.exists() and any(out.iterdir()):errors.append(f'output not empty: {out}')
    q=sh(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'])
    facts['gpu_compute_apps']=q.stdout.strip()
    if q.returncode!=0 or q.stdout.strip():errors.append(f'GPU compute not empty: {q.stdout.strip()!r}')
    g=sh(['nvidia-smi','--query-gpu=index,uuid,memory.used,memory.total','--format=csv,noheader'])
    facts['gpus']=g.stdout.strip().splitlines()
    p=dexec('pgrep -af "[t]ask8_lower_train|[t]ask7_lower_train" || true')
    facts['container_train_procs']=p.stdout.strip()
    if p.returncode!=0 or p.stdout.strip():errors.append(f'training processes present: {p.stdout.strip()!r} rc={p.returncode}')
    free=shutil.disk_usage(ROOT).free;facts['disk_free_bytes']=free
    if free<MIN_FREE_BYTES:errors.append(f'disk free {free} < {MIN_FREE_BYTES}')
    return errors,facts,snapshot


def main():
    a=argparse.ArgumentParser();a.add_argument('--run-id',default='t9-long-20261028');a.add_argument('--execute',action='store_true')
    a=a.parse_args()
    logs=ROOT/f'logs/task9/{a.run_id}';logs.mkdir(parents=True,exist_ok=True)
    if (logs/'launch.json').exists():sys.exit('launch.json exists: refusing to relaunch')
    errors,facts,snapshot=preflight(a.run_id)
    plan=dict(run_id=a.run_id,time=now(),max_wall_s=MAX_WALL_S,runs=[],facts=facts,errors=errors,snapshot=snapshot)
    for g,s,gpu in RUNS:
        cfg=f'{CROOT}/config/task9/lower_train_{g}_prim_seed{s}.json';out=f'{CROOT}/results/task9/{a.run_id}/{g}-seed{s}'
        log=f'{CROOT}/logs/task9/{a.run_id}/{g}-seed{s}.log'
        inner=f'exec python3 -B -u {CROOT}/scripts/task8_lower_train.py --config {cfg} --output {out} --max-wall-s {MAX_WALL_S} > {log} 2>&1'
        argv=['docker','exec','-d','-e',f'CUDA_VISIBLE_DEVICES={gpu}','-e','PYTHONDONTWRITEBYTECODE=1','-e',f'PYTHONPATH={CROOT}/src',CONTAINER,'sh','-c',inner]
        plan['runs'].append(dict(group=g,seed=s,gpu=gpu,config=cfg,output=out,log=log,argv=argv))
    (logs/'preflight.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(errors=errors,facts={k:v for k,v in facts.items() if k!='smoke_snapshot_common'},common_with_smoke=len(facts['smoke_snapshot_common'])),indent=1,ensure_ascii=False))
    if errors:sys.exit('preflight failed; nothing started')
    if not a.execute:print('preflight ok; dry run, nothing started');return
    mon=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,index,memory.used,utilization.gpu','--format=csv','-l','10'],
                         stdout=(logs/'gpu.csv').open('a'),stderr=subprocess.STDOUT,start_new_session=True)
    plan['gpu_monitor_host_pid']=mon.pid
    for r in plan['runs']:
        res=sh(r['argv']);r['launch_rc']=res.returncode;r['launch_stderr']=res.stderr.strip();r['launched_at']=now()
        if res.returncode!=0:plan['status']='LAUNCH_FAILED';break
    time.sleep(10)
    for r in plan['runs']:
        p=dexec(f'pgrep -f "[t]ask8_lower_train.py --config {r["config"]}" || true')
        r['container_pids']=p.stdout.split()
    plan.setdefault('status','LAUNCHED' if all(r.get('container_pids') for r in plan['runs']) else 'LAUNCH_INCOMPLETE')
    (logs/'launch.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(status=plan['status'],gpu_monitor=mon.pid,runs=[(r['group'],r['seed'],r['gpu'],r.get('launch_rc'),r.get('container_pids')) for r in plan['runs']])))


if __name__=='__main__':main()
