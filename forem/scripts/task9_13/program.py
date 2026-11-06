"""One-GPU recoverable phase queue. Importing this module never launches work."""
import json,os,signal,subprocess,sys,time,traceback,shutil
from pathlib import Path
ROOT=Path('/workspace')
OUT=ROOT/'results/task9/task9.13-formal-20261106-r2'
LOG=ROOT/'logs/task9/task9.13-formal-20261106-r2'
SCRIPTS=Path(os.environ.get('TASK9_13_FROZEN_SCRIPTS',str(ROOT/'scripts/task9_13')))
UUID='GPU-656ca5c1-681f-48a2-7d1f-a00824723f68'
MATRIX=[('C',4718),('R',4718),('C',4719),('R',4719)]
stop=False

def dump(path,value):
    tmp=Path(str(path)+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');os.replace(tmp,path)

def stopped(sig,frame):
    global stop
    stop=True

def resources():
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.used','--format=csv,noheader'],text=True)
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
    if UUID not in gpu:raise RuntimeError('assigned GPU UUID not exposed')
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
    return {'gpu':gpu,'compute_apps':apps,'available_memory_bytes':available,'disk_free_bytes':shutil.disk_usage(OUT).free,'affinity':sorted(os.sched_getaffinity(0)),'epoch':time.time(),'busy':any(line.split(',')[0].strip()==UUID for line in apps.splitlines())}

def forecast(job,arm,seed):
    summary=json.loads((job/'profile-summary.json').read_text());window=summary.get('mature_window') or {}
    result={'arm':arm,'seed':seed,'consumed':summary['steps'],'updates':summary['updates'],'profile_total_wall_s':summary['wall_s'],'mature_window':window,'restore_cost_s':'unknown until actual restore','formula':'2.75M/r +11*E196 +12*full_save +restore; profile250k already consumed'}
    active=window.get('wall_s',0)-window.get('checkpoint_s',0)-window.get('evaluation_s',0)
    if active>0:
        rate=window['transfers']/active;ev=json.loads((job/'validation-0250000.json').read_text());e196=ev.get('total_evaluator_wall_s',ev['wall_s'])
        costs=[json.loads(line)['total_wall_s'] for line in (job/'checkpoint-costs.jsonl').read_text().splitlines()];save_s=sum(costs)/len(costs)
        result.update(active_train_transfers_per_s=rate,E196_s=e196,observed_average_full_save_s=save_s,remaining_training_s=2750000/rate,remaining_evaluation_s=11*e196,remaining_save_s=12*save_s,remaining_total_excluding_restore_s=2750000/rate+11*e196+12*save_s)
    dump(job/'profile-cost-forecast.json',result)

def main():
    OUT.mkdir(parents=True,exist_ok=True);LOG.mkdir(parents=True,exist_ok=True)
    signal.signal(signal.SIGTERM,stopped);signal.signal(signal.SIGINT,stopped)
    dump(OUT/'queue-identity.json',{'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().split()[21],'started_epoch':time.time(),'gpu_uuid':UUID,'affinity':sorted(os.sched_getaffinity(0)),'matrix':MATRIX,'planned_transfers':12000000,'planned_development_episodes':9408})
    try:
        for phase in ('profile','remaining'):
            for arm,seed in MATRIX:
                job=OUT/f'{arm}-seed{seed}';job.mkdir(exist_ok=True);terminal=job/f'{phase}-terminal.json';resume=None
                if terminal.exists():
                    prior=json.loads(terminal.read_text())
                    if prior.get('status')=='PASS':continue
                    if not str(prior.get('error','')).startswith('InterruptedError(') or not (job/'interrupted.pt').exists():
                        raise RuntimeError(f'prior failed phase requires root-cause review:{terminal}')
                    resume=job/'interrupted.pt'
                if stop or (OUT/'STOP').exists():raise InterruptedError('queue STOP before phase')
                while True:
                    resource=resources();dump(job/f'{phase}-resources.json',resource)
                    if resource['busy']:
                        dump(OUT/'queue-state.json',{'status':'WAITING_GPU','arm':arm,'seed':seed,'phase':phase,'resource':resource})
                        if stop or (OUT/'STOP').exists():raise InterruptedError('queue STOP while waiting GPU')
                        time.sleep(5);continue
                    if resource['available_memory_bytes']<30*1024**3 or resource['disk_free_bytes']<200*1024**3:raise RuntimeError('insufficient30GiB RAM or200GiB disk')
                    break
                command=[sys.executable,'-B','-u',str(SCRIPTS/'worker.py'),'--arm',arm,'--seed',str(seed),'--phase',phase,'--output',str(job)]
                if resume is not None:command+=['--resume',str(resume)]
                elif phase=='remaining':command+=['--resume',str(job/'profile.pt')]
                dump(OUT/'queue-state.json',{'status':'RUNNING','arm':arm,'seed':seed,'phase':phase,'command':command,'epoch':time.time()})
                with (LOG/f'{phase}-{arm}-{seed}.log').open('ab',buffering=0) as stream:
                    child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,env={**os.environ,'CUBLAS_WORKSPACE_CONFIG':':4096:8','TASK9_13_RAY_LOGDIR':str(LOG/f'ray-{phase}-{arm}-{seed}')})
                    ticks=Path(f'/proc/{child.pid}/stat').read_text().split()[21]
                    dump(OUT/'active-worker.json',{'pid':child.pid,'start_ticks':ticks,'arm':arm,'seed':seed,'phase':phase,'command':command})
                    sent=False
                    while child.poll() is None:
                        if (stop or (OUT/'STOP').exists()) and not sent:
                            if Path(f'/proc/{child.pid}/stat').read_text().split()[21]!=ticks:raise RuntimeError('worker PID identity changed')
                            child.send_signal(signal.SIGTERM);sent=True
                        time.sleep(5)
                if child.returncode:raise RuntimeError(f'worker rc={child.returncode}:{phase}:{arm}:{seed}; inspect log, no blind retry')
                result=json.loads(terminal.read_text())
                if result.get('status')!='PASS':raise RuntimeError('missing successful phase evidence')
                if phase=='profile':forecast(job,arm,seed)
        subprocess.run([sys.executable,'-B','-u',str(SCRIPTS/'report.py'),'--root',str(OUT)],check=True)
        dump(OUT/'queue-state.json',{'status':'DONE_PENDING_PARENT_JUDGEMENT','epoch':time.time(),'report':'comparison.json'})
    except BaseException as error:
        dump(OUT/'queue-state.json',{'status':'STOPPED' if isinstance(error,InterruptedError) else 'FAILED','epoch':time.time(),'error':repr(error),'traceback':traceback.format_exc()})
        raise

if __name__=='__main__':main()
