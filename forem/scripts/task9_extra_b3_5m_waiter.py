#!/usr/bin/env python3
"""task9.4追加run（SRC-1326）：等Codex队列12个run全部派发、某卡道结束且GPU空闲后，启动B3-5M种子4720。

不进入Codex队列：队列每次派发前会拒绝非本队列的GPU/训练进程，所以只在没有queued run后才启动。
队列stopped_on_error、长时间无队列或超时则不启动并记录。只记录250k外推，不写STOP（48h由--max-wall-s兜底）。
"""
import argparse, datetime, hashlib, json, os, pathlib, shlex, shutil, subprocess, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
CROOT=pathlib.Path('/root/mm_husky_ws')
NAME='B3_5M-seed4720'
CONFIG=ROOT/'config/task9/stage2-extra/B3_5M_seed4720.json'
CONFIG_SHA='fb1c043faf99c7bcfcbab5e022a4e40ee98cdda4934e143521299f42e362d16d'
OUTPUT=CROOT/'results/task9/t9-stage2-20261029'/NAME
TOTAL=5_000_000
def now():return datetime.datetime.now().astimezone().isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sh(args):return subprocess.check_output(['sg','docker','-c',shlex.join(args)],text=True)
def host(p):return ROOT/pathlib.Path(p).relative_to(CROOT)
class Waiter:
    def __init__(self,log,dry):
        self.log=log;self.dry=dry;self.extra=log/'extra';self.extra.mkdir(exist_ok=True)
        self.state=dict(name=NAME,config=str(CONFIG),config_sha256=CONFIG_SHA,authorization='SRC-1326',
            waiter_host_pid=os.getpid(),started=now(),status='waiting',events=[])
    def save(self):
        p=self.extra/'waiter-state.tmp';p.write_text(json.dumps(self.state,indent=2,ensure_ascii=False)+'\n');p.replace(self.extra/'waiter-state.json')
    def event(self,msg,**kw):
        self.state['events'].append(dict(time=now(),msg=msg,**kw));self.save();print(now(),msg,kw,flush=True)
    def compute_apps(self):
        return [tuple(map(str.strip,r.split(','))) for r in subprocess.check_output(
            ['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True).splitlines() if r.strip()]
    def uuid(self,gpu):
        return subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-gpu=uuid','--format=csv,noheader'],text=True).strip()
    def decide(self,queue,codex_alive,codex_gone_s):
        """返回('wait'|'abort'|'launch', 说明, gpu)。纯逻辑，便于离线自测。"""
        if queue is None:
            if not codex_alive and codex_gone_s>1800:return 'abort','Codex已退出且无queue-state',None
            return 'wait','队列未启动',None
        if queue.get('status')=='stopped_on_error':return 'abort','队列stopped_on_error：'+str(queue.get('error')),None
        runs=queue['runs']
        if any(r['status']=='queued' for r in runs):return 'wait','仍有queued run',None
        done=[g for g in range(4) if all(r['status']=='ended' for r in runs if r['gpu']==g)]
        if not done:return 'wait','无卡道结束',None
        return 'launch','卡道已结束：'+str(done),done
    def preflight(self,gpu):
        assert sha(CONFIG)==CONFIG_SHA,'配置hash变化'
        assert 'CUBLAS_WORKSPACE_CONFIG' not in os.environ
        target=self.uuid(gpu)
        busy=[a for a in self.compute_apps() if a[0]==target]
        if busy:return None,'目标GPU非空：'+str(busy)
        top=sh(['docker','top','forem-dev','-eo','pid,ppid,args'])
        training=[s for s in top.splitlines() if 'task8_lower_train.py' in s or 'task7_lower_train.py' in s]
        if len(training)>=4:return None,'容器内已有4个训练进程'
        out=host(OUTPUT)
        assert not out.exists() or not any(out.iterdir()),'输出已存在：'+str(out)
        free=shutil.disk_usage(ROOT).free;need=(TOTAL//250000+1)*35_000_000_000
        assert free>=need,(free,need)
        mem=int(next(s.split()[1] for s in pathlib.Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
        assert mem>=40*1024**3,('MemAvailable',mem)
        return dict(gpu=gpu,gpu_uuid=target,container_training=training,disk_free_bytes=free,mem_available_bytes=mem),None
    def launch(self,gpu,facts):
        pidfile=f'{CROOT}/logs/task9/t9-stage2-20261029/extra/{NAME}.container-pid'
        command=['python3','-B','-u',str(CROOT/'scripts/task8_lower_train.py'),'--config',
            str(CROOT/CONFIG.relative_to(ROOT)),'--output',str(OUTPUT),'--max-wall-s','172800']
        inner='echo $$ > '+shlex.quote(pidfile)+'\nexec '+shlex.join(command)
        argv=['sg','docker','-c',shlex.join(['docker','exec','-e','CUDA_VISIBLE_DEVICES='+str(gpu),
            '-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH='+str(CROOT/'src'),'forem-dev','sh','-c',inner])]
        stream=(self.extra/(NAME+'.log')).open('x')
        proc=subprocess.Popen(argv,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        self.state.update(status='running',launched=now(),gpu=gpu,host_docker_exec_pid=proc.pid,argv=argv,preflight=facts)
        self.event('已启动',gpu=gpu,host_docker_exec_pid=proc.pid)
        deadline=time.monotonic()+30;hp=host(pidfile)
        while not hp.exists() and time.monotonic()<deadline and proc.poll() is None:time.sleep(.5)
        if hp.exists():self.state['container_pid']=int(hp.read_text());self.save()
        return proc,stream
    def record_250k(self):
        out=host(OUTPUT);ev=sorted(out.glob('validation-*.json')) if out.exists() else []
        ev=[json.loads(p.read_text()) for p in ev if '.incomplete.' not in p.name]
        path=out/'learning.jsonl'
        if not ev or 'projection_250k' in self.state or not path.exists():return
        rec=[json.loads(s) for s in path.read_text().splitlines()]
        first,last=rec[0],rec[-1];e0=first['elapsed_s'];el=last['elapsed_s']
        done=sum(e['wall_s'] for e in ev if first['step']<=e['step']<last['step'])
        est=e0+(el-e0-done)*(TOTAL-first['step'])/max(last['step']-first['step'],1)+(TOTAL//250000)*ev[-1]['wall_s']
        self.state['projection_250k']=dict(time=now(),step=last['step'],estimate_h=est/3600,over_48h=est>172800,
            validation=ev[0]['validation']['strict_success_rate'],note='同task9_stage2_monitor公式；只记录，不写STOP')
        self.event('250k外推',estimate_h=round(est/3600,2),over_48h=est>172800)
    def terminal(self,rc):
        out=host(OUTPUT)
        if (out/'summary.json').is_file():
            s=json.loads((out/'summary.json').read_text());return dict(kind='summary',steps=s['state']['steps'],updates=s['updates'],wall_s=s['wall_s'])
        for kind in ('diverged','interrupted'):
            if (out/f'{kind}.meta.json').is_file():
                m=json.loads((out/f'{kind}.meta.json').read_text());return dict(kind=kind,steps=m['steps'],resume_safe=m['resume_safe'])
        return dict(kind='unknown',rc=rc)
    def run(self,poll,max_wait_s):
        self.save();self.event('开始等待',poll_s=poll,max_wait_s=max_wait_s)
        t0=time.monotonic();gone=None;last=None
        while True:
            qp=self.log/'queue-state.json'
            queue=json.loads(qp.read_text()) if qp.exists() else None
            alive=subprocess.run(['pgrep','-f','[c]odex exec -C /home/ybc/projects/CL-FoReM'],capture_output=True).returncode==0
            gone=None if alive else (gone or time.monotonic())
            action,why,gpus=self.decide(queue,alive,0 if gone is None else time.monotonic()-gone)
            if why!=last:self.event('判定：'+action,reason=why);last=why
            if action=='abort':self.state['status']='aborted';self.event('不启动',reason=why);return
            if action=='launch':
                for g in gpus:
                    facts,busy=self.preflight(g)
                    if facts:
                        if self.dry:self.state['status']='dry_run_would_launch';self.event('dry-run：将启动',**facts);return
                        proc,stream=self.launch(g,facts)
                        while proc.poll() is None:
                            try:self.record_250k()
                            except Exception as e:self.event('250k记录失败',error=repr(e))
                            time.sleep(poll)
                        stream.close();end=self.terminal(proc.returncode)
                        self.state.update(status='ended',ended=now(),exit_code=proc.returncode,terminal=end);self.event('结束',**end);return
                    if busy!=last:self.event('卡道结束但不可用',gpu=g,reason=busy);last=busy
            if time.monotonic()-t0>max_wait_s:self.state['status']='timeout';self.event('等待超时，不启动');return
            time.sleep(poll)
def main():
    a=argparse.ArgumentParser();a.add_argument('--log',default=str(ROOT/'logs/task9/t9-stage2-20261029'))
    a.add_argument('--dry-run',action='store_true');a.add_argument('--poll',type=float,default=60)
    a.add_argument('--max-wait-s',type=float,default=7*86400);args=a.parse_args()
    Waiter(pathlib.Path(args.log),args.dry_run).run(args.poll,args.max_wait_s)
if __name__=='__main__':main()
