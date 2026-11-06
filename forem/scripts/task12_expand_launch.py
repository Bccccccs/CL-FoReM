#!/usr/bin/env python3
"""Detached task12.7 finite pipeline with sealed outcomes gated by model hash."""
import argparse,fcntl,json,os,shlex,shutil,signal,subprocess,sys,time,traceback
from pathlib import Path
from task12_newmaps_launch import ROOT,now,sha,atomic,append,shell,gpu_info
LOGDOC=ROOT/'doc/agent_logs/task12/task12.7/20261105-codex-expand.md'

def freeze_code(run):
 if (run/'code-version.json').exists():raise RuntimeError('immutable code already frozen')
 code=run/'code';code.mkdir(exist_ok=True)
 r7=ROOT/'results/task12/t12-newmaps-20261105-r7/code'
 for p in r7.glob('*.py'):shutil.copy(p,code/p.name)
 for n in ('task12_expand_freeze.py','task12_expand_collect.py','task12_expand_launch.py','task12_expand_train.py','task12_expand_stats.py','task12_expand_checks.py','task12_newmaps_freeze.py','task12_newmaps_launch.py'):
  shutil.copy(ROOT/'scripts'/n,code/n)
 atomic(run/'code-version.json',dict(at=now(),head=shell(['git','-C',str(ROOT.parent),'rev-parse','HEAD']).stdout.strip(),head_covers_uncommitted=False,files={p.name:sha(p) for p in code.glob('*.py')},plan_sha256=sha(run/'plan.json'),actual_agent_model='unknown',actual_reasoning='unknown',recommended='GPT6.1sol/medium or Sonnet5.5/medium',teacher='r1 frozen-source; r3 accepted independent-row recovery; r7 extraction unchanged'))

def docs(run,status,reason=''):
 plan=json.loads((run/'plan.json').read_text());driver=json.loads((run/'driver.json').read_text());audit=json.loads((run/'existing-label-audit.json').read_text());evaluation=run/'evaluation/summary.json';training=run/'training/summary.json'
 ev=json.loads(evaluation.read_text()) if evaluation.exists() else {};tr=json.loads(training.read_text()) if training.exists() else {}
 result=dict(at=now(),status=status,reason=reason,run_id=run.name,driver=driver,training=tr,evaluation=ev,actual_agent_model='unknown',actual_reasoning='unknown',final_acceptance='current review chat',limitations=['initial s=0 only; local teacher labels not full physical route success','development selection and data scale both changed; no pure data-size causal claim','sealed maps are observed after evaluation; no future pristine reuse'])
 atomic(run/'handoff.json',result)
 marker=f'<!-- task12-expand-final-{run.name}-{driver["attempt"]}-{status} -->'
 rel=f'forem/results/task12/{run.name}'
 text=f'''\n\n## {now()} 持久流水线交接\n\n状态 **{status}**；{reason}。run `{run.name}`，负责人Codex；实际平台模型/推理强度未知，推荐GPT6.1sol/medium、Sonnet5.5/medium，选模/先建档委派权限沿根AGENTS。最终验收由当前审核聊天负责。依据[SRC-T12-025](../../../SOURCES.md#src-t12-025)。\n\n原件 `{rel}/`：plan/manifest/exclusions/split、partitions三份清单、existing-label-audit.json、inputs-frozen.json、states/*的source/network/candidates/labels及grid-0/1终态和resume、training/曲线/更新/epoch检查点/完整优化器RNG、selected-model.json及model-weights.pt、evaluation/逐状态/逐点/配对全部退化/缺失、attempts.jsonl、stage-ledger.jsonl、driver/runtime/code-version、handoff.json。精确数值以下原件摘录为准，未完成阶段不作结果。\n\n训练原件摘要：\n```json\n{json.dumps(tr,ensure_ascii=False,indent=2)}\n```\n\n封存评价摘要（点级、状态、分难度、唯一有效点及原安全到点分别保留）：\n```json\n{json.dumps(ev,ensure_ascii=False,indent=2)}\n```\n\n完整成本、每次失败及阶段退出码见attempts/stage-ledger/driver，单worker累计与墙钟分开；分项cost.json与总墙钟不可重复相加。失败未知不记负，身份不替换。工程完整性与收益门分别由evaluation给出，未满足不追加调参或接上层。输入/标签/教师/两环/网络/损失合同未更改；开发选模与扩图同时变化，不将差异全部归因数据量。64封存集分析后不再为未观察集。\n\n监控 `{rel}/driver.json`、current.json、stage-ledger.jsonl；日志 `forem/logs/task12/{run.name}/`。停止在本run创建STOP，安全边界保存；恢复先确认driver及容器已退出、暂停已撤销，再移除STOP并运行 `python3 -u forem/scripts/task12_expand_launch.py launch --run {run}`。已完成制数跳过；在途沿原PredictionCore恢复；训练沿完整epoch保存含optimizer/RNG恢复，不伪称未保存部分精确续训；封存evaluation-ledger锁定权重，已有结果不重复评估。无需聊天在线。风险/下一步：由审核聊天核验原始证据及接入条件，不自动启动后续实验。\n'''
 append(ROOT/'doc/tasks/task12/task12.7/RESULTS.md',text,marker)
 for name in ('TASK.md','PROCEDURE.md'):append(ROOT/'doc/tasks/task12/task12.7'/name,f'\n{now()} 自动终态：{status}；run {run.name}，原因{reason or "固定流水线结束"}。实际配置与完整交接见[RESULTS](RESULTS.md)，仅完成本合同，无后续实验。',marker)
 append(ROOT/'doc/PROGRESS.md',f'\n{now()} · TASK12.7-EXPAND · Codex · {status}。{run.name}：{reason or "固定流水线已结束，交当前审核聊天"}；训练与封存详见[RESULTS](tasks/task12/task12.7/RESULTS.md)及[SRC-T12-025](SOURCES.md#src-t12-025)。',marker)
 append(ROOT/'doc/SOURCES.md',f'\nSRC-T12-025 项目实测追加，{now()} Codex。原件 `{rel}/handoff.json`、training/summary.json、evaluation/summary.json及per-state/candidate-scores/paired-comparisons，精确位置为JSON字段与state/candidate_id，版本code-version.json。状态{status}，原因{reason}；本条由持久程序摘录原件，不是独立最终审核。最终验收当前审核聊天。初始s=0/局部标签限制、训练选模同时变化限制沿SRC-T12-024。',marker)
 append(LOGDOC,f'\n{now()} 自动交接{status}：{reason}。handoff.json及三文档/SOURCES/PROGRESS已追加。driver终态和成本见原件，未启动任何下一轮。',marker)
 atomic(run/'documentation-status.json',dict(at=now(),status='written',handoff_status=status))

def drive(run):
 lock=(run/'driver.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);(run/'driver.pid').write_text(str(os.getpid())+'\n')
 signal.signal(signal.SIGHUP,signal.SIG_IGN)
 for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *a:(run/'STOP').touch())
 if (run/'STOP').exists():raise RuntimeError('STOP exists, respect pause')
 for n,h in json.loads((run/'code-version.json').read_text())['files'].items():assert sha(run/'code'/n)==h
 attempt=1+sum(1 for x in (run/'attempts.jsonl').read_text().splitlines() if json.loads(x)['event']=='start') if (run/'attempts.jsonl').exists() else 1
 gpu=gpu_info(run);log=ROOT/'logs/task12'/run.name;log.mkdir(parents=True,exist_ok=True);container='forem-task12-expand-r8';begin=time.monotonic()
 state=dict(run_id=run.name,status='running',attempt=attempt,driver_pid=os.getpid(),container=container,gpu=gpu,started=now(),engineering_estimate_s=72000,phases=['collection','training','sealed_evaluation','documentation'],actual_agent_model='unknown',actual_reasoning='unknown');atomic(run/'driver.json',state)
 def record(path,event):
  with (run/path).open('a') as f:f.write(json.dumps(dict(at=now(),attempt=attempt,**event),ensure_ascii=False)+'\n')
 record('attempts.jsonl',dict(event='start',gpu=gpu,driver_pid=os.getpid()))
 original=ROOT/'results/task12/t12-abc-20261104-r1'
 base=['docker','run','--rm','--name',container,'--gpus',f'device={gpu["uuid"]}','--network','none','--user',f'{os.getuid()}:{os.getgid()}','--cpuset-cpus','10-11','--shm-size','1g','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH=/run/code:/original/frozen-source/src','-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=2','-e','CUDA_VISIBLE_DEVICES=0','-e','PYTORCH_KERNEL_CACHE_PATH=/tmp/torch-kernels','-e','CUBLAS_WORKSPACE_CONFIG=:4096:8','-v',f'{ROOT}:/workspace:ro','-v',f'{original}:/original:ro','-v',f'{run}:/run','--entrypoint','/opt/python310/bin/python3','mm_husky:node01','-u']
 stages=[('collection','task12_expand_collect.py',[],run/'collection-complete.json'),('training','task12_expand_train.py',['train'],run/'selected-model.json'),('sealed_evaluation','task12_expand_train.py',['evaluate'],run/'evaluation/summary.json')]
 rc=0;reason=''
 try:
  for phase,script,extra,done in stages:
   if done.exists():record('stage-ledger.jsonl',dict(event='skip_complete',phase=phase,artifact=str(done)));continue
   if (run/'STOP').exists():rc=130;reason='STOP at phase boundary';break
   if phase=='sealed_evaluation':
    selected=json.loads((run/'selected-model.json').read_text());atomic(run/'pre-sealed-model-lock.json',dict(at=now(),model_sha256=sha(run/'model-weights.pt'),selected=selected));assert (run/'training/summary.json').exists()
   argv=base+[f'/run/code/{script}']+extra+['--run','/run'];cmd=['sg','docker','-c',shlex.join(argv)]
   state.update(phase=phase,phase_started=now(),argv=cmd);atomic(run/'driver.json',state);record('stage-ledger.jsonl',dict(event='start',phase=phase,argv=cmd));t=time.monotonic()
   with (log/f'{phase}-{attempt:02d}.log').open('a') as stream:worker=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
   state['docker_client_pid']=worker.pid;atomic(run/'driver.json',state);last=time.monotonic();verified=False
   while True:
    # Device check during collection; training logs additionally record tensors/optimizer.
    if phase=='collection' and (run/'runtime.json').exists() and not verified:
     rt=json.loads((run/'runtime.json').read_text());u=rt['gpu_uuid'];u=u if u.startswith('GPU-') else 'GPU-'+u
     assert u==gpu['uuid'] and rt['actor_device']==rt['network_device']=='cuda:0';state['device_verified']=True;atomic(run/'driver.json',state);verified=True
    if time.monotonic()-last>=1800:
     count=sum(1 for p in (run/'states').glob('*/row.json') if json.loads(p.read_text()).get('status')=='complete');elapsed=time.monotonic()-begin
     if phase=='collection' and count:state['engineering_estimate_s']=max(72000,round(elapsed/count*256*1.2));atomic(run/'driver.json',state)
     append(LOGDOC,f'\n{now()} 自动进度：{phase}，完整状态{count}/256，本次墙钟{elapsed:.1f}s，工程预估{state["engineering_estimate_s"]}s（非硬截止）。');last=time.monotonic()
    try:rc=worker.wait(timeout=20);break
    except subprocess.TimeoutExpired:pass
   record('stage-ledger.jsonl',dict(event='end',phase=phase,returncode=rc,wall_s=time.monotonic()-t))
   if rc:reason=f'{phase} returncode {rc}; preserve artifacts, same-identity recovery required';break
   if not done.exists():raise RuntimeError(f'{phase} rc0 missing completion artifact')
  status='review' if rc==0 else 'paused' if (run/'STOP').exists() else 'review'
  state.update(status=status,finished=now(),returncode=rc,wall_s=time.monotonic()-begin,reason=reason);atomic(run/'driver.json',state);record('attempts.jsonl',dict(event='end',returncode=rc,wall_s=state['wall_s']))
  docs(run,status,reason)
 except BaseException:
  reason=traceback.format_exc();state.update(status='review',finished=now(),error=reason,wall_s=time.monotonic()-begin);atomic(run/'driver.json',state);atomic(run/'driver-error.json',dict(at=now(),traceback=reason));docs(run,'review','Pipeline error; see driver-error.json');raise
 return rc

def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze-code','launch','drive','finalize']);ap.add_argument('--run',type=Path,required=True);a=ap.parse_args();run=a.run.resolve()
 if a.action=='freeze-code':freeze_code(run);return 0
 if a.action=='drive':return drive(run)
 if a.action=='finalize':docs(run,'review','manual documentation recovery from preserved artifacts');return 0
 assert json.loads((run/'targeted-tests.json').read_text())['all_pass']
 lock=(run/'driver.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);lock.close()
 log=ROOT/'logs/task12'/run.name;log.mkdir(parents=True,exist_ok=True)
 with (log/'driver.log').open('a') as stream:p=subprocess.Popen([sys.executable,'-u',str(run/'code/task12_expand_launch.py'),'drive','--run',str(run)],stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,close_fds=True)
 atomic(run/'launch.json',dict(at=now(),driver_pid=p.pid,detached=True,log=str(log/'driver.log')));print(json.dumps(dict(driver_pid=p.pid,run=str(run))));return 0
if __name__=='__main__':raise SystemExit(main())
