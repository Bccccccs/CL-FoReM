#!/usr/bin/env python3
"""Supplemental CPU finalization for r2 tuple-map-id audit compatibility."""
import argparse,fcntl,hashlib,importlib.util,json,os,shlex,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'results/task10/t10-expanded-20261106-r2'
LOG=ROOT/'logs/task10/t10-expanded-20261106-r2'
CONTAINER='forem-task10-19-gpu3'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def atomic(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False));os.replace(tmp,p)
def frozen_module():
 p=ROOT/'scripts/task10_expanded_eval.py';spec=importlib.util.spec_from_file_location('frozen_expanded',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def audit_v2():
 # The shared entry is unchanged. The sole in-memory correction normalizes a
 # sequence container; values/order, scientific identities and all other checks
 # stay exactly the original frozen audit. This never calls an environment.
 source=ROOT/'scripts/task10_expanded_eval.py';s=source.read_text();needle="f['map_ids']==[row['map_id']]";assert s.count(needle)==1
 s=s.replace(needle,"tuple(f['map_ids'])==(row['map_id'],)")
 ns={'__file__':str(source),'__name__':'frozen_expanded_audit_v2'};exec(compile(s,str(source)+'#tuple-normalized-audit','exec'),ns)
 ns['audit']();a=read(RUN/'audit.json');a.update(audit_implementation='tuple-normalized-v2',audit_script_sha256=sha(Path(__file__)),original_frozen_entry_sha256=sha(source),no_environment_execution=True);atomic(RUN/'audit.json',a)
 return 0

def watch():
 lock=(RUN/'finalizer.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 config=read(RUN/'finalization-config.json');assert sha(Path(__file__))==config['script_sha256'];m=frozen_module();started=time.time()
 atomic(RUN/'finalizer.json',{'status':'waiting','pid':os.getpid(),'started_epoch':started,'config_sha256':sha(RUN/'finalization-config.json'),'reason':'CPU audit normalizes exact_cpu map_ids tuple; frozen worker unchanged','will_automatically_update_docs':True})
 while True:
  ex=RUN/'shards/worker0/worker-exit.json';la=RUN/'launch.json'
  if ex.exists() and la.exists() and read(la).get('status')=='exited' and (RUN/'handoff.json').exists():break
  time.sleep(10)
 status='blocked';error=None;rca=rcs=None
 try:
  # Existing failed/partial audit evidence is retained; no original episodes rerun.
  if (RUN/'handoff.json').exists():atomic(RUN/'handoff-initial-audit-format.json',read(RUN/'handoff.json'))
  if (RUN/'audit.json').exists():atomic(RUN/'audit-initial.json',read(RUN/'audit.json'))
  cmd=['docker','exec','--user','1004:1004','-e','PYTHONPATH=/workspace/src',CONTAINER,'python3','-u','/workspace/scripts/task10_expanded_finalize.py','audit']
  with (LOG/'audit-v2.log').open('w') as f:rca=subprocess.run(['sg','docker','-c',shlex.join(cmd)],stdout=f,stderr=subprocess.STDOUT).returncode
  cmd=['docker','exec','--user','1004:1004',CONTAINER,'python3','-u','/workspace/scripts/task10_expanded_report.py','--run','/workspace/results/task10/'+RUN.name]
  with (LOG/'report-final.log').open('w') as f:rcs=subprocess.run(['sg','docker','-c',shlex.join(cmd)],stdout=f,stderr=subprocess.STDOUT).returncode
  audit=read(RUN/'audit.json') if (RUN/'audit.json').exists() else {};report=read(RUN/'report.json') if (RUN/'report.json').exists() else {};ex=read(ex);plan=read(RUN/'plan.json')
  complete=ex['status']=='complete' and rca==0 and rcs==0 and audit.get('status')=='verified_complete' and report.get('status')=='complete' and report.get('valid_episodes')==len(plan['expected'])
  ci=report.get('primary',{}).get('interval') or report.get('primary',{}).get('complete_map_supplement') or {}
  if complete:
   status='review';scores={k:{x:report['arms'][k][x] for x in ('success','planned','missing')} for k in ('T','U1','U2')}
   detail=f"完整{report['valid_episodes']}/{len(plan['expected'])}回合，0缺失/0更新；T/U1/U2成功与分母={scores}；主要地图配对差Δ={report['primary']['effect']}，95%近似区间={ci.get('interval')}、宽={ci.get('width')}，非零效应地图{ci.get('nonzero_map_count')}/{ci.get('map_count')}；{ci.get('information')}。U1/U2不一致={report.get('uniform_discordance')}。成本={report.get('cost_totals')}。原始tuple/list格式审计错误已由CPU v2正常化修复，原handoff/audit日志保留；科学合同及全部回合未改变。当前审核聊天最终验收，仍只有一个训练seed。"
  else:
   detail=f"完整条件未满足：worker={ex['status']}、CPU audit-v2 rc={rca}、report rc={rcs}、有效{report.get('valid_episodes',0)}/{len(plan['expected'])}，固定计划分母及所有partial保留。未恢复/重跑/换图，先查日志与STOP授权。"
  handoff={'status':status,'complete':complete,'worker_exit':ex,'audit_rc':rca,'report_rc':rcs,'audit_path':str(RUN/'audit.json'),'report_path':str(RUN/'report.json'),'report_sha256':sha(RUN/'report.json') if report else None,'plan_sha256':sha(RUN/'plan.json'),'finalization_config_sha256':sha(RUN/'finalization-config.json'),'updates':0,'reviewer':'current audit chat','single_training_seed':101,'original_handoff_preserved':'handoff-initial-audit-format.json','detail':detail}
  atomic(RUN/'handoff.json',handoff);m.update_docs(status,detail)
 except BaseException as e:
  error=repr(e);traceback.print_exc();m.update_docs('blocked','CPU补充收尾异常 '+error+'；评估原件保留，不自动重试环境。')
 atomic(RUN/'finalizer.json',{'status':status,'pid':os.getpid(),'started_epoch':started,'finished_epoch':time.time(),'cpu_audit_rc':rca,'report_rc':rcs,'error':error,'config_sha256':sha(RUN/'finalization-config.json')})
 return 0 if status=='review' else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=('audit','watch'));a=p.parse_args();raise SystemExit(audit_v2() if a.phase=='audit' else watch())
