#!/usr/bin/env python3
"""Detached single-owner task12.2 driver; finite 32-state run and document handoff."""
import argparse,fcntl,hashlib,json,math,os,shlex,signal,subprocess,sys,time,traceback
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path('/home/ybc/projects/CL-FoReM/forem')
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
def freeze(run):
    import shutil
    code=run/'code';code.mkdir(exist_ok=True)
    if (run/'code-version.json').exists():return
    for name in ('task12_cost32.py','task12_cost32_coverage.py','task12_cost32_tests.py','task12_cost32_launch.py'):shutil.copy(ROOT/'scripts'/name,code/name)
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in code.glob('*.py')};atomic(run/'code-version.json',dict(frozen_at=now(),files=files,source_inherited='t12-abc-20261104-r1/frozen-source, accepted SRC-T12-009',plan_sha256=hashlib.sha256((run/'plan.json').read_bytes()).hexdigest()))
    old=json.loads((ROOT/'results/task12/t12-bc-20261104-r2/handoff.json').read_text());atomic(run/'prototype-reference.json',dict(excluded_from_denominator=True,map_id='sparse_train_00000',scene_seed=1204,category=3,source='SRC-T12-009',known_grid_positive=1,selected_positive=0,worker_wall_s=old['wall_s'],training_updates_this_run=0))
def summarize(run):
    sys.path.insert(0,str(run/'code'));from task12_cost32_coverage import build_summary
    return build_summary(run)
def finalize(run,attempt,peak):
    summary=summarize(run);rows=summary['rows'];finished=sum((run/'states'/x['state_id']/'row.json').exists() for x in rows);overall=summary['overall'];cases=overall['classes'];available=overall['selectable_positive_states'];hit=overall['network_hit_states']
    ledger=json.loads((run/'driver.json').read_text());summary.update(status='review' if finished==32 and attempt['returncode']==0 else 'interrupted',processed_states=finished,driver=ledger,sampled_device_peak_mib=peak,completed_at=now(),answers=dict(sampling=f"格心支持无正例{cases['1']}/{overall['complete_grid_states']}个完整状态；另有{cases['2']}个全被几何排除，缺失{overall['missing']}/32。",ranking=f"有可选正例状态命中{hit}/{available}，漏选{cases['3']}/{available}。" if available else '本批没有可选正例状态，排序命中率无定义。',next_investment=summary['recommendation']['next_investment']))
    atomic(run/'summary.json',summary);atomic(run/'handoff.json',summary)
    cost_rows='\n'.join(f"|{k}|{v['total']:.3f}|{v['p50'] if v['p50'] is not None else 'NA'}|{v['p90'] if v['p90'] is not None else 'NA'}|{v['max'] if v['max'] is not None else 'NA'}|" for k,v in summary['costs'].items())
    diff_rows='\n'.join(f"|{d}|{v['planned']}|{v['classes']['1']}|{v['classes']['2']}|{v['classes']['3']}|{v['classes']['4']}|{v['missing']}|{v['network_hit_states']}/{v['selectable_positive_states']}|{v['rule_cover_states']}/{v['rule_complete_states']}|" for d,v in summary['by_difficulty'].items())
    body=f'''\n## {now()} · {run.name} 持久执行交接\n\n状态{summary['status']}，负责人Codex；实际模型/强度未知，推荐GPT6.1sol/medium、Sonnet5.5/medium，原因是固定合同的成本/覆盖核查。独立执行、保留根选模及先建档委派权限。本节为持久launcher根据保存原件自动汇总，最终结论交当前决策者。依据[SRC-T12-010](../../../SOURCES.md#src-t12-010)。\n\n已处理{finished}/32，完整格心状态{overall['complete_grid_states']}，缺失{overall['missing']}。四类为①无正{cases['1']}、②全被几何排除{cases['2']}、③可选但漏选{cases['3']}、④命中{cases['4']}；可选正状态命中{hit}/{available}。规则覆盖{overall['rule_cover_states']}/{overall['rule_complete_states']}完整规则状态，0有效槽状态{overall['zero_valid_rule_states']}，有效槽分布{json.dumps(overall['rule_valid_slots'],ensure_ascii=False)}。网络更新0；原型训练状态单列，未进32分母。\n\n|难度|计划|①|②|③|④|缺失|可选正命中|规则覆盖|\n|---|---:|---:|---:|---:|---:|---:|---|---|\n{diff_rows}\n\n直接回答：{summary['answers']['sampling']} {summary['answers']['ranking']} 下一轮建议：{summary['answers']['next_investment']}；按本批最多损失门定位，建议不构成实施授权，未继续训练或扩制数。这些是局部教师标签，不是完整路线成功率；单状态原型验收不重复。\n\n|成本项|合计秒|逐状态p50秒|p90秒|最大秒|\n|---|---:|---:|---:|---:|\n{cost_rows}\n\n主进程本次尝试墙钟{attempt['wall_s']:.3f}s、rc{attempt['returncode']}；历次成本见attempts.jsonl，准备/等待另记；分项B3计时已扣定时快照写盘，write_s单列；active_state_wall_s是两阶段实际工作累计，不能与其子项重复相加。未执行阶段以0列于计划状态分布，分母见表；raw snapshots和cost.json可复算。PyTorch峰值allocated={summary['torch_peak_allocated_bytes']}bytes/reserved={summary['torch_peak_reserved_bytes']}bytes；设备采样峰值{peak}MiB（含驱动、非纯tensor分配）。原地无既有证据才补一次，所选格心复用同源/同姿态/同教师ID结果，没有重复移动推演。\n\n原件：`forem/results/task12/{run.name}/`中的plan.json、inputs-frozen.json、states/<id>/source.pt/candidates.json/selection.json、grid-0/grid-1/rules/decoded-extra原件与resume.pt、per-state.csv、per-state.jsonl、summary.json、handoff.json。代码code-version.json及frozen-components.json固定，实际argv/driver及worker PID/退出码见driver.json、launch.json、attempts.jsonl，日志forem/logs/task12/{run.name}/。命令`python3 -u forem/scripts/task12_cost32_launch.py launch --run {run}`；恢复用同命令，移除本run STOP后从未完成阶段继续，已完成文件跳过；停止只创建本run/STOP。\n\n剩余：{'本轮32状态核查已到边界，交决策者，未执行后续方案。' if summary['status']=='review' else '存在中断/异常；读取worker-error.json、current.json和在途快照后定向修复/恢复，不替换地图或盲目重算。'}\n'''
    marker=f"<!-- task12-final-{run.name}-{attempt['attempt']} -->"
    def publish(path,text):
        if marker not in path.read_text():append(path,text+('\n'+marker+'\n' if marker not in text else ''))
    if not (run/'documentation-status.json').exists() or json.loads((run/'documentation-status.json').read_text()).get('attempt')!=attempt['attempt']:
        publish(ROOT/'doc/tasks/task12/task12.2/RESULTS.md',body+'\n'+marker+'\n')
        publish(ROOT/'doc/tasks/task12/RESULTS.md',f"\n## {run.name} · 32状态核查持久交接\n{summary['status']}，已处理{finished}/32，四类{cases}，缺失{overall['missing']}，可选正命中{hit}/{available}，规则覆盖{overall['rule_cover_states']}/{overall['rule_complete_states']}，更新0。建议：{summary['answers']['next_investment']}（未实施）。详细[task12.2结果](task12.2/RESULTS.md)、[原件](../../../results/task12/{run.name}/handoff.json)，依据[SRC-T12-010](../../SOURCES.md#src-t12-010)。交当前决策者，局部标签非完整路线成功率。\n")
        publish(ROOT/'doc/PROGRESS.md',f"\n{now()} · TASK12.2-COST32-20261104 · Codex · {summary['status']}（持久launcher交接）。{run.name}已处理{finished}/32，类别{cases}/缺失{overall['missing']}，可选正命中{hit}/{available}，网络更新0，未继续下一阶段。[结果](tasks/task12/task12.2/RESULTS.md) · [SRC-T12-010](SOURCES.md#src-t12-010)。\n")
        publish(ROOT/'doc/SOURCES.md',f"\nSRC-T12-010 项目实测追加，Codex持久launcher，{now()}；run `{run.name}`，精确原件`forem/results/task12/{run.name}/summary.json`的overall/by_difficulty/costs/rows，及per-state.csv、inputs-frozen.json、各状态快照/标签/selection。已处理{finished}/32，四类{cases}、缺失{overall['missing']}、可选正命中{hit}/{available}、规则覆盖{overall['rule_cover_states']}/{overall['rule_complete_states']}，更新0；本次主墙钟{attempt['wall_s']:.3f}s、rc{attempt['returncode']}。下一轮建议为{summary['answers']['next_investment']}，按预登记最多损失门规则，不是显著性/泛化结论或后续实施授权。分项成本和原始计数可从同目录复算，标签仅局部推演，最终交当前决策者验收。\n")
        publish(ROOT/'doc/agent_logs/task12/task12.2/20261104-codex-cost32.md',f"\n{now()} launcher终态{summary['status']}：本次wall={attempt['wall_s']:.3f}s、rc={attempt['returncode']}，{finished}/32已处理；原件summary/handoff与逐状态CSV/JSONL已保存。四类{cases}、缺失{overall['missing']}、可选正命中{hit}/{available}。三问回答见handoff.answers；未实施后续建议。更新0。GPU隔离/资源采样/退出状态见driver.json与resource-samples.jsonl；异常见worker-error.json，恢复跳过完成阶段。\n")
    atomic(run/'documentation-status.json',dict(at=now(),status='written',attempt=attempt['attempt']))

def drive(run):
    run=run.resolve();lock=(run/'driver.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);(run/'driver.pid').write_text(str(os.getpid())+'\n');signal.signal(signal.SIGHUP,signal.SIG_IGN)
    def request_stop(*a):(run/'STOP').touch()
    signal.signal(signal.SIGTERM,request_stop);signal.signal(signal.SIGINT,request_stop)
    if (run/'STOP').exists():raise RuntimeError('STOP exists; honor user stop, remove deliberately before resume')
    if all((run/'states'/f'state-{i:02d}'/'row.json').exists() for i in range(32)):
        old=json.loads((run/'driver.json').read_text());finalize(run,old['last_attempt'],old.get('sampled_device_peak_mib',0));return 0
    gpu=gpu_info(run);container='forem-task12-cost32-r3';log=ROOT/'logs/task12'/run.name;log.mkdir(parents=True,exist_ok=True)
    original=ROOT/'results/task12/t12-abc-20261104-r1';prototype=ROOT/'results/task12/t12-bc-20261104-r2'
    argv=['docker','run','--rm','--name',container,'--gpus',f"device={gpu['index']}",'--network','none','--user','1004:1004','--cpuset-cpus','8-9','--shm-size','1g','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH=/run/code:/original/frozen-source/src','-e','OMP_NUM_THREADS=2','-e','CUDA_VISIBLE_DEVICES=0','-e','PYTORCH_KERNEL_CACHE_PATH=/tmp/torch-kernels','-e','CUBLAS_WORKSPACE_CONFIG=:4096:8','-v',f'{ROOT}:/workspace:ro','-v',f'{original}:/original:ro','-v',f'{prototype}:/prototype:ro','-v',f'{run}:/run','--entrypoint','/opt/python310/bin/python3','mm_husky:node01','-u','/run/code/task12_cost32.py','--run','/run']
    cmd=['sg','docker','-c',shlex.join(argv)];history=run/'attempts.jsonl';number=1+sum(1 for x in history.read_text().splitlines() if json.loads(x).get('event')=='start') if history.exists() else 1
    began=time.monotonic();attempt=dict(attempt=number,event='start',started=now(),started_epoch=time.time(),driver_pid=os.getpid(),gpu=gpu,argv=cmd);history.open('a').write(json.dumps(attempt)+'\n')
    with (log/f'worker-{number:02d}.log').open('a') as stream:worker=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
    state=dict(run_id=run.name,status='running',started=attempt['started'],driver_pid=os.getpid(),docker_client_pid=worker.pid,container=container,gpu=gpu,argv=cmd,engineering_window_s=28800,network_updates=0,last_attempt=attempt);atomic(run/'driver.json',state);peak=0;last_doc=time.monotonic();device_checked=False
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
            append(ROOT/'doc/agent_logs/task12/task12.2/20261104-codex-cost32.md',f"\n{now()} 持久进度：完成{count}/32，本次墙钟{time.monotonic()-began:.1f}s，工程窗{state['engineering_window_s']}s，状态/阶段见current.json；未增加状态或更新。\n");last_doc=time.monotonic()
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
        p=subprocess.Popen([sys.executable,'-u',str(run/'code/task12_cost32_launch.py'),'drive','--run',str(run)],stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,close_fds=True)
    atomic(run/'launch.json',dict(at=now(),driver_pid=p.pid,detached=True,log=str(log/'driver.log'),command=[sys.executable,'-u',str(run/'code/task12_cost32_launch.py'),'drive','--run',str(run)]));print(json.dumps(dict(driver_pid=p.pid,run=str(run),log=str(log/'driver.log'))));return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except BaseException as e:
        if not isinstance(e,SystemExit):traceback.print_exc()
        raise
