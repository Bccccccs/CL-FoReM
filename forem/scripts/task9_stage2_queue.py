#!/usr/bin/env python3
"""task9.4 宿主侧分离队列：每卡串行，失败不重试；训练由容器自建输出。"""
import argparse, concurrent.futures, datetime, hashlib, json, os, pathlib, shlex
import shutil, subprocess, threading, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
LOG=ROOT/'logs/task9/t9-stage2-20261029'
CROOT=pathlib.Path('/root/mm_husky_ws')
LOCK=threading.RLock()
HALT=threading.Event()
def now():return datetime.datetime.now().astimezone().isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(x):
    with LOCK:
        p=LOG/'queue-state.tmp';p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');p.replace(LOG/'queue-state.json')
def docker(args):
    return subprocess.check_output(['sg','docker','-c',shlex.join(['docker']+args)],text=True)
def frozen(plan):
    for name,h in plan['files'].items():assert sha(ROOT/name)==h,'冻结文件变化：'+name
def memory():
    return int(next(s.split()[1] for s in pathlib.Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
def preflight(plan,state,run=None):
    frozen(plan)
    assert 'TASK8_SCENE_CACHE' not in os.environ and 'CUBLAS_WORKSPACE_CONFIG' not in os.environ
    top=docker(['top','forem-dev','-eo','pid,ppid,args'])
    owned={r['config'] for r in state['runs'] if r['status']=='running'}
    training=[s for s in top.splitlines() if 'task8_lower_train.py' in s or 'task7_lower_train.py' in s]
    assert all(any(c in line for c in owned) for line in training),training
    owned_pids={line.split()[0] for line in training}
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'],text=True)
    uuid=None if run is None else subprocess.check_output(['nvidia-smi','-i',str(run['gpu']),'--query-gpu=uuid','--format=csv,noheader'],text=True).strip()
    for row in apps.splitlines():
        gpu,pid,_=map(str.strip,row.split(','))
        assert pid in owned_pids,'非本队列GPU进程：'+row
        if uuid is not None:assert gpu!=uuid,'目标GPU非空：'+row
    remaining=[r for r in state['runs'] if r['status'] in ('queued','running')]
    disk_need=sum((r['total_transfers']//250000+1)*35_000_000_000 for r in remaining)
    free=shutil.disk_usage(ROOT).free
    assert free>=disk_need,(free,disk_need)
    # task9.2四卡长训宿主已用约84GiB（SRC-1317）。这是既有实测参照，不保证新run峰值。
    available=memory()
    if not owned:assert available>=84*1024**3,available
    for r in ([run] if run else state['runs']):
        out=ROOT/pathlib.Path(r['output']).relative_to(CROOT)
        assert not out.exists() or not any(out.iterdir()),'输出已存在：'+str(out)
    return dict(time=now(),compute_apps=apps,container_top=top,disk_free_bytes=free,
        remaining_checkpoint_estimate_bytes=disk_need,mem_available_bytes=available)
def terminal(run,rc):
    out=ROOT/pathlib.Path(run['output']).relative_to(CROOT)
    if (out/'summary.json').is_file():
        s=json.loads((out/'summary.json').read_text())
        assert rc==0 and s['state']['steps']==run['total_transfers'] and s['state']['validation_pending'] is None
        return dict(kind='summary',steps=s['state']['steps'],updates=s['updates'],wall_s=s['wall_s'])
    for kind in ('diverged','interrupted'):
        if (out/f'{kind}.meta.json').is_file():
            meta=json.loads((out/f'{kind}.meta.json').read_text())
            assert (out/f'{kind}.pt').is_file()
            if kind=='diverged':
                text=(LOG/run['log_name']).read_text()
                assert 'FloatingPointError' in text,'不能将未知异常归为预注册发散'
            return dict(kind=kind,steps=meta['steps'],resume_safe=meta['resume_safe'])
    raise RuntimeError('退出但无合法终态：'+run['name']+' rc='+str(rc))
def lane(gpu,plan,state):
    for r in [r for r in state['runs'] if r['gpu']==gpu]:
        if HALT.is_set():return
        try:
            # 序列化启动预检，防止其他卡尚未登记PID时被误认作陌生进程。
            with LOCK:
                if HALT.is_set():return
                facts=preflight(plan,state,r)
                pidfile=f'{CROOT}/logs/task9/t9-stage2-20261029/{r["name"]}.container-pid'
                command=['python3','-B','-u',str(CROOT/'scripts/task8_lower_train.py'),
                    '--config',r['config'],'--output',r['output'],'--max-wall-s','172800']
                inner='echo $$ > '+shlex.quote(pidfile)+'\nexec '+shlex.join(command)
                argv=['sg','docker','-c',shlex.join(['docker','exec','-e','CUDA_VISIBLE_DEVICES='+str(gpu),
                    '-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH='+str(CROOT/'src'),'forem-dev','sh','-c',inner])]
                stream=(LOG/r['log_name']).open('x')
                proc=subprocess.Popen(argv,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                r.update(status='running',started=now(),host_docker_exec_pid=proc.pid,argv=argv,preflight=facts)
                save(state)
                deadline=time.monotonic()+15
                hostpidfile=ROOT/pathlib.Path(pidfile).relative_to(CROOT)
                while not hostpidfile.exists() and time.monotonic()<deadline and proc.poll() is None:time.sleep(.2)
                assert hostpidfile.exists(),'未获得容器PID'
                r['container_pid']=int(hostpidfile.read_text());save(state)
                # 等待exec完成，使后继卡预检能以config识别进程。
                deadline=time.monotonic()+10
                while time.monotonic()<deadline:
                    top=docker(['top','forem-dev','-eo','pid,ppid,args'])
                    matches=[s for s in top.splitlines() if r['config'] in s and 'python3' in s]
                    if matches:
                        r['host_training_pids']=[int(s.split()[0]) for s in matches];save(state);break
                    if proc.poll() is not None:break
                    time.sleep(.2)
                assert r.get('host_training_pids'),'未核实训练进程'
            rc=proc.wait();stream.close()
            with LOCK:
                end=terminal(r,rc);r.update(status='ended',ended=now(),exit_code=rc,terminal=end);save(state)
        except BaseException as e:
            with LOCK:
                r['queue_error']=repr(e);state.update(status='stopped_on_error',error=repr(e));HALT.set();save(state)
            raise
def main():
    a=argparse.ArgumentParser();a.add_argument('--execute',action='store_true');args=a.parse_args()
    plan=json.loads((LOG/'queue-plan.json').read_text())
    assert not (LOG/'queue-state.json').exists(),'已有执行状态，禁止重跑'
    state=dict(status='prepared',queue_host_pid=os.getpid(),started=now(),runs=plan['runs'],plan_sha256=sha(LOG/'queue-plan.json'))
    facts=preflight(plan,state)
    (LOG/'queue-preflight.json').write_text(json.dumps(facts,indent=2)+'\n')
    if not args.execute:print('预检通过，尚未启动');return
    gpu_stream=(LOG/'long-gpu.csv').open('x')
    monitor=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,index,memory.used,utilization.gpu','--format=csv','-l','10'],stdout=gpu_stream,stderr=subprocess.STDOUT,start_new_session=True)
    state.update(status='running',gpu_monitor_host_pid=monitor.pid);save(state)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as workers:
            futures=[workers.submit(lane,gpu,plan,state) for gpu in range(4)]
            for f in concurrent.futures.as_completed(futures):
                try:f.result()
                except BaseException as e:print(repr(e),flush=True)
    finally:
        monitor.terminate();monitor.wait();gpu_stream.close()
    if not HALT.is_set():state.update(status='complete',ended=now());save(state)
if __name__=='__main__':main()
