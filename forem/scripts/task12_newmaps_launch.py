#!/usr/bin/env python3
"""Detached finite task12.6 driver; persists exits, stats and document handoff."""
import argparse,fcntl,hashlib,json,math,os,shlex,shutil,signal,subprocess,sys,time,traceback
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path('/home/ybc/projects/CL-FoReM/forem')
LOGDOC=ROOT/'doc/agent_logs/task12/task12.6/20261105-codex-newmaps.md'
def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,x):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n');q.replace(p)
def append(p,text,marker=None):
 with (ROOT/'doc/.task12-doc-append.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);existing=p.read_text() if p.exists() else '';p.parent.mkdir(parents=True,exist_ok=True)
  if marker and marker in existing:return
  p.write_text(existing+text+('\n'+marker+'\n' if marker else ''))
def shell(argv):return subprocess.run(argv,capture_output=True,text=True)
def gpu_info(run):
 r=shell(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits']);assert r.returncode==0
 apps=shell(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits']);assert apps.returncode==0
 atomic(run/'gpu-before.json',dict(at=now(),gpus=r.stdout,apps=apps.stdout));busy={x.split(',')[0].strip() for x in apps.stdout.splitlines() if x.strip()}
 for line in r.stdout.splitlines():
  bits=[x.strip() for x in line.split(',')]
  if int(bits[0]) in (2,3) and bits[1] not in busy:return dict(index=int(bits[0]),uuid=bits[1],baseline_memory_mib=int(bits[2]))
 raise RuntimeError('No free GPU2/3; GPU0/1 left untouched')
def freeze_code(run):
 if (run/'code-version.json').exists():return
 code=run/'code';code.mkdir(exist_ok=True)
 for name in ('task12_newmaps.py','task12_newmaps_stats.py','task12_newmaps_launch.py','task12_newmaps_freeze.py','task12_newmaps_tests.py'):shutil.copy(ROOT/'scripts'/name,code/name)
 base=ROOT/'results/task12/t12-cost32-20261104-r3/code';r6=ROOT/'results/task12/t12-utility-20261105-r6/code'
 for name in ('task12_cost32.py','task12_cost32_coverage.py'):shutil.copy(base/name,code/name)
 for name in ('task12_heatmap.py','task12_frozen_decoder.py','task12_utility_train.py'):shutil.copy(r6/name,code/name)
 atomic(run/'code-version.json',dict(frozen_at=now(),head=shell(['git','-C',str(ROOT.parent),'rev-parse','HEAD']).stdout.strip(),head_covers_uncommitted=False,files={p.name:sha(p) for p in code.glob('*.py')},teacher_source='r1 frozen-source accepted SRC-T12-007/009',rollout_restore_source='immutable accepted r3/code/task12_cost32.py',model_and_decoder_source='accepted r6/code and final model SRC-T12-018/019',plan_sha256=sha(run/'plan.json'),manifest_sha256=sha(run/'manifest.json'),actual_agent_model='unknown',actual_reasoning='unknown',recommended='GPT6.1sol/medium or Sonnet5.5/medium; autonomous model/reasoning/delegation within parent scope'))
def summarize(run):
 sys.path.insert(0,str(run/'code'));from task12_newmaps_stats import build_summary
 return build_summary(run)
def finalize(run,attempt,peak):
 from task12_newmaps_stats import render_report
 summary=summarize(run);main=summary['overall']['utility'];ready=main['complete_states']==32 and attempt['returncode']==0
 summary.update(status='review' if ready else 'interrupted',completed_at=now(),driver=json.loads((run/'driver.json').read_text()),sampled_device_peak_mib=peak)
 summary['artifacts']=dict(plan_sha256=sha(run/'plan.json'),manifest_sha256=sha(run/'manifest.json'),model_sha256=json.loads((run/'plan.json').read_text())['model_sha256'],code_version=json.loads((run/'code-version.json').read_text()))
 atomic(run/'summary.json',summary);atomic(run/'handoff.json',summary)
 marker=f"<!-- task12-newmaps-final-{run.name}-{attempt['attempt']} -->"
 rootrel=f'forem/results/task12/{run.name}'
 extra=f'''\n\n负责人Codex父执行者，实际平台模型/推理强度未知；推荐GPT6.1sol/medium、Sonnet5.5/medium，地图身份/指标因果核查；执行者可自主选模强度及先建档委派，统计由task12.6.1子Agent提供并由父针对性核查。当前状态{summary['status']}，交当前决策者审核，未自动扩大制数或训练。\n\n权重固定r6/model-weights.pt SHA256 {summary['artifacts']['model_sha256']}，epoch200/训练历史600更新，本轮更新0。效用版本task12-utility-v1；32地图manifest/排除清单在任何新标签之前保存；正式test池保留，不按正点数换图。source.pt初始s=0、原sync_v5采样接受；每候选独立clone行、原B3教师，只运行grid-0/1两批。strict_success与实际提交终态FK共同核验；旧arrive标签并列。rule候选mask/姿态与inplace槽12有效/零姿态合同保留，无新规则/原地教师标签。两选择器只读24支持点/可见几何/固定分数，按candidate-ID关联唯一推演。\n\n本次driver主墙钟{attempt['wall_s']:.3f}秒，returncode={attempt['returncode']}，设备采样峰值{peak}MiB。多次尝试总消耗见attempts.jsonl；初始化/准备、状态获取、源快照恢复读取解码与H2D、网络输入构造、一次前向、几何、解码、教师、终态读取/FK、写盘分列。源状态构造内资产/采样细项见source.pt/sampler_timing，不能把同步墙钟当纯GPU时间。grid计时复用r3并扣快照写盘；active_state_wall与driver墙钟及子项不可相加。最初2–3h只是沿用SRC-T12-010/020排期，实际估计变更记driver.json，不改768/32/0更新。\n\n原件 `{rootrel}/`：exclusions.json、manifest.json、plan.json、inputs-frozen.json；states/<id>/source.pt/candidates.json/selection.json/network.pt、grid-0/1/{{data.pt,result.json,resume.pt,utility.json}}、labels.json/row.json/cost.json；per-state.csv/json、candidate-scores.csv、rank-misses.json、case-selection.json、summary.json、handoff.json。冻结代码在code/及code-version.json（根HEAD不代表未提交源码）；targeted-tests.json包含新入口核查，原A/标签/坐标/恢复证据引用SRC-T12-007/009/018/019，未全量重复审核。资源/PID/启动argv/退出状态见gpu-before.json、launch.json、driver.json、runtime.json、attempts.jsonl、resource-samples.jsonl，日志forem/logs/task12/{run.name}/。\n\n只读原件复算（输出副本避免覆盖终态）：复制plan.json和states到独立输出目录，再执行 `python3 -u {rootrel}/code/task12_newmaps_stats.py --run <副本绝对目录>`；仅标准库，不需要GPU/教师，不再推演。原始终态FK对应提取函数code/task12_newmaps.py::Worker.utility_records，按已存data.pt可另目录重提取；部署分数及原logit在network.pt和逐候选CSV。\n\n持久恢复命令：`python3 -u forem/scripts/task12_newmaps_launch.py launch --run {run}`，先确认本run driver已退出，无STOP；若用户要求停止则创建本run/STOP，worker在安全边界保存；仅在用户撤销暂停后移除STOP。完成批/result及utility/row跳过，timeout恢复保存PredictionCore，不重推已完成candidate；旧失败文件保留。自动收尾不依赖聊天，写盘失败见finalization-error.json后可用同run恢复仅收尾。\n\n未解决/下一步：{'本轮已达到固定32图边界，收益及反例见上表，当前决策者最终验收。' if ready else '存在缺失/中断或运行错误，保留冻结身份和原件，查worker-error.json/driver-error.json并定向修复后同run恢复；未将缺失记负。'}\n'''
 append(ROOT/'doc/tasks/task12/task12.6/RESULTS.md',render_report(summary)+extra,marker)
 a=summary['answers'];short=f"{a['point']} {a['state']} {a['large_margin']} {a['next_step']}"
 append(ROOT/'doc/PROGRESS.md',f"\n{now()} · TASK12.6-NEWMAPS · Codex · {summary['status']}（持久自动交接）。{run.name}完整{main['complete_states']}/32，0更新，主{attempt['wall_s']:.3f}s/rc{attempt['returncode']}。{short} [结果](tasks/task12/task12.6/RESULTS.md) · [SRC-T12-021](SOURCES.md#src-t12-021)。\n",marker)
 append(ROOT/'doc/SOURCES.md',f"\nSRC-T12-021 项目实测追加，Codex持久launcher，{now()}。run `{run.name}`，原件`{rootrel}/summary.json`的overall/by_difficulty/costs/rows/answers、candidate-scores.csv、rank-misses.json及每状态source/终态data.pt/utility.json，精确版本code-version.json/manifest.json/plan.json；核查为保存原件自动一致性统计及新入口targeted-tests，不声称无bug或完整任务收益。{short} 缺失{main['missing_states']}/32，0更新；本次{attempt['wall_s']:.3f}s/rc{attempt['returncode']}。32张新train图、同24支持/几何、单初始状态且扇区相关，分数未校准；不可将本轮已观察图当未来未观察验证集，最终交当前决策者。\n",marker)
 append(LOGDOC,f"\n{now()} 自动收尾：{summary['status']}，完整{main['complete_states']}/32，rc{attempt['returncode']}，本次{attempt['wall_s']:.3f}s。{short} 原件handoff.json及RESULTS/SOURCES/PROGRESS已更新，0更新，未进入后续实验。\n",marker)
 atomic(run/'documentation-status.json',dict(at=now(),status='written',attempt=attempt['attempt']))

def drive(run):
 run=run.resolve();lock=(run/'driver.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);(run/'driver.pid').write_text(str(os.getpid())+'\n');signal.signal(signal.SIGHUP,signal.SIG_IGN)
 signal.signal(signal.SIGTERM,lambda *a:(run/'STOP').touch());signal.signal(signal.SIGINT,lambda *a:(run/'STOP').touch())
 if (run/'STOP').exists():raise RuntimeError('STOP exists; honor explicit pause until revoked')
 sys.path.insert(0,str(run/'code'))
 if all((run/'states'/f'state-{i:02d}'/'row.json').exists() and json.loads((run/'states'/f'state-{i:02d}'/'row.json').read_text())['status']=='complete' for i in range(32)):
  old=json.loads((run/'driver.json').read_text());finalize(run,old['last_attempt'],old.get('sampled_device_peak_mib',0));return 0
 gpu=gpu_info(run);container='forem-task12-newmaps-r7';log=ROOT/'logs/task12'/run.name;log.mkdir(parents=True,exist_ok=True)
 original=ROOT/'results/task12/t12-abc-20261104-r1'
 argv=['docker','run','--rm','--name',container,'--gpus',f"device={gpu['uuid']}",'--network','none','--user',f'{os.getuid()}:{os.getgid()}','--cpuset-cpus','10-11','--shm-size','1g','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH=/run/code:/original/frozen-source/src','-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=2','-e','CUDA_VISIBLE_DEVICES=0','-e','PYTORCH_KERNEL_CACHE_PATH=/tmp/torch-kernels','-e','CUBLAS_WORKSPACE_CONFIG=:4096:8','-v',f'{ROOT}:/workspace:ro','-v',f'{original}:/original:ro','-v',f'{run}:/run','--entrypoint','/opt/python310/bin/python3','mm_husky:node01','-u','/run/code/task12_newmaps.py','--run','/run']
 cmd=['sg','docker','-c',shlex.join(argv)];history=run/'attempts.jsonl';number=1+sum(1 for x in history.read_text().splitlines() if json.loads(x).get('event')=='start') if history.exists() else 1
 began=time.monotonic();attempt=dict(attempt=number,event='start',started=now(),started_epoch=time.time(),driver_pid=os.getpid(),gpu=gpu,argv=cmd);history.open('a').write(json.dumps(attempt)+'\n')
 with (log/f'worker-{number:02d}.log').open('a') as stream:worker=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
 state=dict(run_id=run.name,status='running',started=attempt['started'],driver_pid=os.getpid(),docker_client_pid=worker.pid,container=container,gpu=gpu,argv=cmd,engineering_estimate_s=10800,network_updates=0,last_attempt=attempt);atomic(run/'driver.json',state);peak=0;last_doc=began;device_checked=False
 while True:
  memory=shell(['nvidia-smi','-i',str(gpu['index']),'--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'])
  if memory.returncode==0:
   bits=memory.stdout.strip().split(',');peak=max(peak,int(bits[0]));(run/'resource-samples.jsonl').open('a').write(json.dumps(dict(at=now(),gpu=gpu['index'],memory_mib=int(bits[0]),utilization_percent=int(bits[1])))+'\n')
  if (run/'runtime.json').exists() and not device_checked:
   rt=json.loads((run/'runtime.json').read_text());uuid=rt['gpu_uuid'];uuid=uuid if uuid.startswith('GPU-') else 'GPU-'+uuid
   if uuid!=gpu['uuid'] or rt['actor_device']!='cuda:0' or rt['network_device']!='cuda:0':
    (run/'STOP').touch();state['device_verification_error']=dict(expected=gpu,actual=rt)
   else:state['device_verified']=True
   device_checked=True;atomic(run/'driver.json',state)
  count=sum((run/'states'/f'state-{i:02d}'/'row.json').exists() for i in range(32))
  if count:
   elapsed=max(0.,time.time()-(run/'inputs-frozen.json').stat().st_mtime) if (run/'inputs-frozen.json').exists() else 0.
   estimate=(time.monotonic()-began)+elapsed/count*(32-count)
   if estimate>state['engineering_estimate_s']:
    state['engineering_estimate_s']=math.ceil(estimate*1.25/3600)*3600;state.setdefault('estimate_adjustments',[]).append(dict(at=now(),completed=count,estimate_s=estimate,reason='same32 workload actual throughput; no scale/scientific changes'));atomic(run/'driver.json',state)
  if time.monotonic()-last_doc>=1800:
   append(LOGDOC,f"\n{now()} 持久进度：已写状态{count}/32，本次{time.monotonic()-began:.1f}s；工程预计{state['engineering_estimate_s']}s，当前阶段current.json，更新0。\n");last_doc=time.monotonic()
  try:rc=worker.wait(timeout=30);break
  except subprocess.TimeoutExpired:pass
 attempt.update(event='end',ended=now(),wall_s=time.monotonic()-began,returncode=rc);history.open('a').write(json.dumps(attempt)+'\n');state.update(status='returned',returncode=rc,last_attempt=attempt,sampled_device_peak_mib=peak,ended=attempt['ended']);atomic(run/'driver.json',state)
 try:finalize(run,attempt,peak)
 except BaseException:atomic(run/'finalization-error.json',dict(at=now(),traceback=traceback.format_exc()));raise
 return rc

def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze-code','launch','drive','finalize']);ap.add_argument('--run',type=Path,required=True);args=ap.parse_args();run=args.run.resolve()
 if args.action=='freeze-code':freeze_code(run);return 0
 if args.action=='drive':return drive(run)
 if args.action=='finalize':
  sys.path.insert(0,str(run/'code'));old=json.loads((run/'driver.json').read_text());finalize(run,old['last_attempt'],old.get('sampled_device_peak_mib',0));return 0
 assert json.loads((run/'targeted-tests.json').read_text())['all_pass'];assert (run/'code-version.json').exists()
 for name,digest in json.loads((run/'code-version.json').read_text())['files'].items():assert sha(run/'code'/name)==digest
 if (run/'driver.pid').exists():
  try:os.kill(int((run/'driver.pid').read_text()),0)
  except ProcessLookupError:pass
  else:raise RuntimeError('driver PID exists, do not duplicate launch')
 log=ROOT/'logs/task12'/run.name;log.mkdir(parents=True,exist_ok=True)
 with (log/'driver.log').open('a') as stream:p=subprocess.Popen([sys.executable,'-u',str(run/'code/task12_newmaps_launch.py'),'drive','--run',str(run)],stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,close_fds=True)
 atomic(run/'launch.json',dict(at=now(),driver_pid=p.pid,detached=True,log=str(log/'driver.log')));print(json.dumps(dict(driver_pid=p.pid,run=str(run),log=str(log/'driver.log'))));return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except BaseException as e:
  if not isinstance(e,SystemExit):
   traceback.print_exc()
   if '--run' in sys.argv:
    run=Path(sys.argv[sys.argv.index('--run')+1]);atomic(run/'driver-error.json',dict(at=now(),traceback=traceback.format_exc()))
  raise
