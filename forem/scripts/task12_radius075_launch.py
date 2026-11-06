#!/usr/bin/env python3
import argparse,fcntl,hashlib,json,math,os,shlex,signal,subprocess,sys,time,traceback
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path("/home/ybc/projects/CL-FoReM/forem")

def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()

def atomic(p,data):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)

def shell(args):return subprocess.run(args,capture_output=True,text=True)

def append(p,text):
    # Shared fact files are re-read under a single task12 append lock.
    lock=ROOT/'doc/.task12-doc-append.lock'
    with lock.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX);existing=p.read_text() if p.exists() else '';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(existing+text)

def gpu_info(run):
    r=shell(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits']);assert r.returncode==0
    apps=shell(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits']);assert apps.returncode==0
    atomic(run/'gpu-before.json',dict(at=now(),gpus=r.stdout,apps=apps.stdout));busy={x.split(',')[0].strip() for x in apps.stdout.splitlines() if x.strip()}
    for line in r.stdout.splitlines():
        bits=[x.strip() for x in line.split(',')]
        if int(bits[0]) in (2,3) and bits[1] not in busy:return dict(index=int(bits[0]),uuid=bits[1],baseline_memory_mib=int(bits[2]))
    raise RuntimeError('No isolated GPU2/3 free; GPU0/1 left untouched')

def drive(run):
    run=run.resolve();lock=(run/'driver.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);(run/'driver.pid').write_text(str(os.getpid())+'\n');signal.signal(signal.SIGHUP,signal.SIG_IGN)
    def request_stop(*a):(run/'STOP').touch()
    signal.signal(signal.SIGTERM,request_stop);signal.signal(signal.SIGINT,request_stop)
    if (run/'STOP').exists():raise RuntimeError('STOP exists; honor user stop, remove deliberately before resume')
    if all((run/'states'/f'state-{i:02d}'/'row.json').exists() for i in range(32)):
        old=json.loads((run/'driver.json').read_text());finalize(run,old['last_attempt'],old.get('sampled_device_peak_mib',0));return 0
    gpu=gpu_info(run);container='forem-task12-radius075-r4';log=ROOT/'logs/task12'/run.name;log.mkdir(parents=True,exist_ok=True)
    original=ROOT/'results/task12/t12-abc-20261104-r1';prototype=ROOT/'results/task12/t12-bc-20261104-r2'
    argv=['docker','run','--rm','--name',container,'--gpus',f"device={gpu['index']}",'--network','none','--user','1004:1004','--cpuset-cpus','8-9','--shm-size','1g','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH=/run/code:/original/frozen-source/src','-e','OMP_NUM_THREADS=2','-e','CUDA_VISIBLE_DEVICES=0','-e','PYTORCH_KERNEL_CACHE_PATH=/tmp/torch-kernels','-e','CUBLAS_WORKSPACE_CONFIG=:4096:8','-v',f'{ROOT}:/workspace:ro','-v',f'{original}:/original:ro','-v',f'{prototype}:/prototype:ro','-v',f'{ROOT}/results/task12/t12-cost32-20261104-r3:/baseline:ro','-v',f'{run}:/run','--entrypoint','/opt/python310/bin/python3','mm_husky:node01','-u','/run/code/task12_radius075.py','--run','/run']
    cmd=['sg','docker','-c',shlex.join(argv)];history=run/'attempts.jsonl';number=1+sum(1 for x in history.read_text().splitlines() if json.loads(x).get('event')=='start') if history.exists() else 1
    began=time.monotonic();attempt=dict(attempt=number,event='start',started=now(),started_epoch=time.time(),driver_pid=os.getpid(),gpu=gpu,argv=cmd);history.open('a').write(json.dumps(attempt)+'\n')
    with (log/f'worker-{number:02d}.log').open('a') as stream:worker=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
    state=dict(run_id=run.name,status='running',started=attempt['started'],driver_pid=os.getpid(),docker_client_pid=worker.pid,container=container,gpu=gpu,argv=cmd,engineering_window_s=7200,network_updates=0,last_attempt=attempt);atomic(run/'driver.json',state);peak=0;last_doc=time.monotonic();device_checked=False
    while True:
        memory=shell(['nvidia-smi','-i',str(gpu['index']),'--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'])
        if memory.returncode==0:
            bits=memory.stdout.strip().split(',');peak=max(peak,int(bits[0]));sample=dict(at=now(),gpu=gpu['index'],memory_mib=int(bits[0]),utilization_percent=int(bits[1]));(run/'resource-samples.jsonl').open('a').write(json.dumps(sample)+'\n')
        if (run/'runtime.json').exists() and not device_checked:
            rt=json.loads((run/'runtime.json').read_text());assert 'GPU-'+rt['gpu_uuid']==gpu['uuid'] and rt['actor_device']=='cuda:0' and rt['network_device']=='cuda:0';device_checked=True;state['device_verified']=True;atomic(run/'driver.json',state)
        count=sum((run/'states'/f'state-{i:02d}'/'row.json').exists() for i in range(32))
        if count:
            label_elapsed=max(0.,time.time()-(run/'inputs-frozen.json').stat().st_mtime) if (run/'inputs-frozen.json').exists() else 0.
            estimate=(time.monotonic()-began)+label_elapsed/count*(32-count)
            if estimate>state['engineering_window_s']:
                state['engineering_window_s']=math.ceil(estimate*1.25/3600)*3600;state.setdefault('window_adjustments',[]).append(dict(at=now(),completed=count,estimate_s=estimate,new_window_s=state['engineering_window_s'],reason='same fixed32 workload, update estimate from actual progress; no scale or science change'));atomic(run/'driver.json',state)
        if time.monotonic()-last_doc>=1800:
            append(ROOT/'doc/agent_logs/task12/task12.3/20261104-codex-radius075.md',f"\n{now()} 持久进度：完成{count}/32，本次墙钟{time.monotonic()-began:.1f}s，工程窗{state['engineering_window_s']}s，状态/阶段见current.json；未增加状态或更新。\n");last_doc=time.monotonic()
        try:rc=worker.wait(timeout=30);break
        except subprocess.TimeoutExpired:pass
    attempt.update(event='end',ended=now(),wall_s=time.monotonic()-began,returncode=rc);history.open('a').write(json.dumps(attempt)+'\n');state.update(status='returned',returncode=rc,last_attempt=attempt,sampled_device_peak_mib=peak,ended=attempt['ended']);atomic(run/'driver.json',state)
    finalize(run,attempt,peak);return rc

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['launch','drive']);ap.add_argument('--run',type=Path,required=True);args=ap.parse_args();run=args.run.resolve()
    if args.action=='drive':return drive(run)
    assert json.loads((run/'targeted-tests.json').read_text())['all_pass'];freeze(run)
    if (run/'driver.pid').exists():
        try:os.kill(int((run/'driver.pid').read_text()),0)
        except ProcessLookupError:pass
        else:raise RuntimeError('driver PID still exists; do not duplicate launch')
    log=ROOT/'logs/task12'/run.name;log.mkdir(parents=True,exist_ok=True)
    with (log/'driver.log').open('a') as stream:
        p=subprocess.Popen([sys.executable,'-u',str(run/'code/task12_radius075_launch.py'),'drive','--run',str(run)],stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,close_fds=True)
    atomic(run/'launch.json',dict(at=now(),driver_pid=p.pid,detached=True,log=str(log/'driver.log'),command=[sys.executable,'-u',str(run/'code/task12_radius075_launch.py'),'drive','--run',str(run)]));print(json.dumps(dict(driver_pid=p.pid,run=str(run),log=str(log/'driver.log'))));return 0


def freeze(run):
    import shutil
    code=run/'code'
    if (run/'code-version.json').exists():return
    for name in ('task12_radius075.py','task12_radius075_stats.py','task12_radius075_tests.py','task12_radius075_launch.py'):shutil.copy(ROOT/'scripts'/name,code/name)
    atomic(run/'code-version.json',dict(frozen_at=now(),files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in code.glob('*.py')},teacher_source='r1 frozen-source unchanged',base_resume_and_label_loop='r3 code/task12_cost32.py unchanged',decoder='r3 code/task12_frozen_decoder.py unchanged',network='r2 C-network.pt frozen; cached r3 predictions reused',plan_sha256=hashlib.sha256((run/'plan.json').read_bytes()).hexdigest()))

def summarize(run):
    sys.path.insert(0,str(run/'code'));from task12_radius075_stats import summarize as calc
    return calc(run)

def finalize(run,attempt,peak):
    summary=summarize(run);finished=sum((run/'states'/f'state-{i:02d}'/'row.json').exists() for i in range(32));o=summary['overall'];old=o['groups']['old'];new=o['groups']['new'];post=o['paired_post'];pre=o['paired_pre'];costs=summary['costs'];complete=finished==32 and attempt['returncode']==0
    names=dict(candidate_coverage='候选覆盖',geometry='几何筛选',network_ranking='网络排序');bottleneck='、'.join(names[x] for x in summary['next_bottlenecks']) or '本批未见明确三类状态漏失，不能据此认定无瓶颈'
    summary.update(status='review' if complete else 'interrupted',processed_states=finished,driver=json.loads((run/'driver.json').read_text()),sampled_device_peak_mib=peak,completed_at=now(),answers=dict(retain=summary['decision'],bottleneck=bottleneck),selector_warning='采样后几何覆盖与网络排序分开；网络若输最近点不抹去采样增益。局部教师标签不代表完整路线成功率。')
    atomic(run/'summary.json',summary);atomic(run/'handoff.json',summary)
    table='\n'.join(f"|{g}|{x['complete']}/{x['planned']}|{x['pre_cover']}|{x['post_cover']}|{x['network']['hit_states']}/{x['network']['conditional_denominator']}|{x['network']['hit_states']}/{x['network']['overall_denominator']}|{x['nearest']['hit_states']}/{x['nearest']['conditional_denominator']}|{x['nearest']['hit_states']}/{x['nearest']['overall_denominator']}|" for g,x in [('旧0.5＋1.5',old),('新0.5＋0.75',new)])
    diff='\n'.join(f"|{d}|{x['paired_complete']}/{x['planned']}|{x['groups']['old']['pre_cover']}→{x['groups']['new']['pre_cover']}|{x['groups']['old']['post_cover']}→{x['groups']['new']['post_cover']}|{x['paired_post']}|" for d,x in summary['by_difficulty'].items())
    cost='\n'.join(f"|{k}|{v['total']:.3f}|{v['p50']}|{v['p90']}|{v['max']}|" for k,v in costs.items())
    body=f'''\n## {now()} · {run.name} 等点数配对交接\n\n状态{summary['status']}，负责人Codex；实际模型/强度未知，推荐GPT6.1sol/medium、Sonnet5.5/medium，理由是冻结合同的配对/成本核查。独立执行，保留根选模及先建档委派权限。当前决策者最终验收，本节为持久launcher按原始记录自动汇总。[SRC-T12-012](../../../SOURCES.md#src-t12-012)。\n\n已处理{finished}/32，完整配对{o['paired_complete']}、缺失{o['paired_missing']}；新旧各24点、0更新。**是否保留：{summary['decision']}。下个更接近的瓶颈：{bottleneck}。** 原因按新组各门漏失状态数{summary['loss_states_new']}定位，不是方法收益/泛化的统计证明。\n\n|组|完整/计划|筛前覆盖|筛后覆盖|网络条件命中|网络整体命中|最近条件命中|最近整体命中|\n|---|---|---:|---:|---|---|---|---|\n{table}\n\n严格配对分母{o['paired_complete']}：筛前{pre}；筛后{post}。原13无正状态中，已配对原无正分母{o['original_no_positive']}，找回{o['rescued_original_no_positive']}、其中筛后保留{o['rescued_original_no_positive_after_geometry']}。筛前新增状态{o['gained_state_ids_pre']}，损失{o['lost_state_ids_pre']}；筛后新增{o['gained_state_ids_post']}，损失{o['lost_state_ids_post']}。损失状态的old_far_positive_ids、三半径标签及原姿态在逐状态原件，不能以新三环并集抵消新24点丢失。\n\n|难度|完整配对/计划|筛前旧→新|筛后旧→新|后配对|\n|---|---|---|---|---|\n{diff}\n\n新组网络命中{new['network']['hit_states']}，最近允许点命中{new['nearest']['hit_states']}；两者几何集合相同、选择不读标签，条件分母{new['post_cover']}、整体分母{new['complete']}，旧组分母另列于表。若后覆盖净增加而网络低于最近点，采样收益可保留但排序问题独立；若相当/下降则保留旧方案。只筛前增加而后无净增加时，读各状态geometry-positive-exclusions.json中的可见正高度格及实际距离走廊SAT条件，并与后覆盖损失同时分析，不能仅归因于几何。36点并集仅诊断：{summary['diagnostic_union_only']}，不是新24点成绩。\n\n新增推演/复用计数{summary['counts']}；其中旧两环768标签、规则及原地只引用，不重跑；新增移动最大384硬限，只有同源SHA/实际世界姿态/inplace/教师配置合同一致才复用。冻结热力图来自同输入/同权重r3缓存，核旧分数和选择一致，新前向0（不是网络训练）；预测读取/解码/写盘分项实测如下。新状态取得0，快照读取单列。\n\n|成本项|总秒|逐状态p50|p90|max|\n|---|---:|---:|---:|---:|\n{cost}\n\n本次墙钟{attempt['wall_s']:.3f}s，rc{attempt['returncode']}；主进程起止与历次中断成本在driver.json/attempts.jsonl。B3计时扣定时快照写盘、write_s单列，active_state_wall_s不可与其子项重复相加。PyTorch峰值allocated={summary['peak_allocated_bytes']}bytes/reserved={summary['peak_reserved_bytes']}bytes；设备采样峰值{peak}MiB（含驱动）。GPU1长训不动、独立单GPU，退出后容器--rm。\n\n原件`forem/results/task12/{run.name}/`：plan.json、inputs-frozen.json、code-version.json、paired-states.csv/jsonl、gain-loss-cases.json、summary.json/handoff.json；states/<id>包含候选/纯分数选择/复用依据/新增probe075原件及在途resume.pt/标签/几何排除条件/成本。来源快照和旧记录位于r3，只读挂载。主命令`python3 -u forem/scripts/task12_radius075_launch.py launch --run {run}`；具体argv/PID/设备/退出在driver.json/launch.json，日志forem/logs/task12/{run.name}/。STOP及恢复沿本run独立标记，已完成状态/批跳过，未进行教师A/旧重放/新网络训练。\n\n剩余：{'已到本轮预登记单探针对照边界，交当前决策者；未继续试半径或实施后续建议。' if complete else '有中断或缺失，先读worker-error/在途快照定向处理，不能据不完整配对采纳方案。'}\n'''
    marker=f'<!-- task12-radius-final-{run.name}-{attempt["attempt"]} -->'
    def publish(path,text):
        if marker not in path.read_text():append(path,text+'\n'+marker+'\n')
    publish(ROOT/'doc/tasks/task12/task12.3/RESULTS.md',body)
    publish(ROOT/'doc/tasks/task12/RESULTS.md',f"\n## {run.name} · 0.75m等点数对照\n{summary['status']}，处理{finished}/32、完整配对{o['paired_complete']}；筛后配对{post}，旧/新网络命中{old['network']['hit_states']}/{new['network']['hit_states']}，旧/新最近命中{old['nearest']['hit_states']}/{new['nearest']['hit_states']}。结论建议：{summary['decision']}；下一瓶颈{bottleneck}，未实施下一阶段。详见[task12.3结果](task12.3/RESULTS.md)、[SRC-T12-012](../../SOURCES.md#src-t12-012)，局部标签非路线成功率。\n")
    publish(ROOT/'doc/PROGRESS.md',f"\n{now()} · TASK12.3-RADIUS075-20261104 · Codex · {summary['status']}。{run.name}完成{finished}/32，筛后配对{post}，新增/复用{summary['counts']}，更新0。{summary['decision']}；下一瓶颈{bottleneck}，未试第二半径。[结果](tasks/task12/task12.3/RESULTS.md)。\n")
    publish(ROOT/'doc/SOURCES.md',f"\nSRC-T12-012 项目实测追加（Codex持久launcher，{now()}）：run `{run.name}`，精确原件summary.json的overall/by_difficulty/counts/costs及paired-states.csv、各state labels/selectors/geometry-positive-exclusions。完成{finished}/32，完整配对{o['paired_complete']}；前配对{pre}、后配对{post}，原无正找回{o['rescued_original_no_positive']}/{o['original_no_positive']}，筛后保留{o['rescued_original_no_positive_after_geometry']}。旧/新网路命中{old['network']['hit_states']}/{new['network']['hit_states']}，旧/新最近命中{old['nearest']['hit_states']}/{new['nearest']['hit_states']}，各分母见原件；新增/复用{summary['counts']}、0更新/新前向0。主墙钟{attempt['wall_s']:.3f}s、rc{attempt['returncode']}。结论建议{summary['decision']}，下瓶颈{bottleneck}；按预登记后覆盖净增加决定保留，未以36并集当24方案，未实施后续，局部标签不证明路线成功或跨状态泛化。\n")
    publish(ROOT/'doc/agent_logs/task12/task12.3/20261104-codex-radius075.md',f"\n{now()} 持久交接{summary['status']}，wall={attempt['wall_s']:.3f}s/rc{attempt['returncode']}，完成{finished}/32；配对后{post}。决策建议{summary['decision']}，瓶颈{bottleneck}。计数{summary['counts']}，0更新。完整表/案例/成本在原件和RESULTS，原旧记录只读；没有额外半径/训练。最终交当前决策者。\n")
    atomic(run/'documentation-status.json',dict(at=now(),status='written',attempt=attempt['attempt']))

if __name__=='__main__':
    try:raise SystemExit(main())
    except BaseException as e:
        if not isinstance(e,SystemExit):traceback.print_exc()
        raise
