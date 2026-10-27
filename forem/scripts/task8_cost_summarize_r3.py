#!/usr/bin/env python3
"""Pure stdlib task8 A/P5 evidence snapshot. Never load tensor/checkpoint code."""
import csv
import datetime
import hashlib
import json
from pathlib import Path
from task8_profile_summarize import gpu_csv

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/task8/t8-perf-opt-20261027'
SMOKE=ROOT/'results/task8/t8-train-stage0-smoke-r2-20261027'
LOG=ROOT/'logs/task8/t8-train-stage0-20261027'
OPT=ROOT/'logs/task8/t8-perf-opt-20261027/budget.json'


def updates(n,k):return max(0,n//k-257//k)
def read(path,notes):
    if not path.exists():return None
    try:return json.loads(path.read_text())
    except json.JSONDecodeError:
        notes.append(str(path.relative_to(ROOT))+': JSON in progress, no conclusion taken');return None

def csv_or_pending(path):
    if not path.exists():return dict(n=0,status='not_present')
    result=gpu_csv(path);result['status']='partial_if_command_running';return result

def hash_small(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,text):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(text);tmp.replace(path)

def main():
    notes=[];execution=read(LOG/'r3-smoke-serial-execution.json',notes) or dict(status='not_present',jobs=[])
    plan=read(LOG/'r3-smoke-plan.json',notes) or {};opt=read(OPT,notes) or {};c_budget=read(LOG/'budget.json',notes) or {}
    groups={};files=[LOG/'r3-smoke-serial-execution.json',LOG/'r3-smoke-plan.json'];alerts=[]
    for job in execution.get('jobs',[]):
        if job.get('exit_code') not in (None,0):alerts.append(dict(job=job['id'],exit_code=job['exit_code'],status='failed',raw_job_status=job['status'],action='REPORT_PARENT_ONLY_NO_FIX_NO_RETRY'))
    for group,k in (('B0',1),('B3',10)):
        folder=SMOKE/group;docs={}
        for name in ('primary-summary.json','summary.json','primary-runtime.json','runtime.json','primary-final.meta.json','final.meta.json','interrupted.meta.json','diverged.meta.json','validation-0001000.json','validation-0001000.incomplete.json','primary-preserved.json'):
            path=folder/name;data=read(path,notes)
            if data is not None:docs[name]=data;files.append(path)
        learning=folder/'learning.jsonl';records=[]
        if learning.exists():
            raw=learning.read_text();files.append(learning)
            for line in raw.splitlines():
                try:records.append(json.loads(line))
                except json.JSONDecodeError:notes.append(group+': incomplete JSONL line ignored')
        phases={}
        for phase in ('primary','resume'):
            command_path=LOG/f'smoke-{group}-{phase}-command.json';command=read(command_path,notes)
            if command is not None:files.append(command_path)
            monitor=LOG/f'smoke-{group}-{phase}-gpu.csv'
            if monitor.exists():files.append(monitor)
            phases[phase]=dict(command=command,gpu_monitor=csv_or_pending(monitor))
            if command and command.get('status')=='finished':phases[phase]['gpu_monitor']['status']='complete_whole_command_sampled'
        # Primary may have finished but not yet been atomically renamed by preserve.
        primary=docs.get('primary-summary.json')
        final=docs.get('summary.json')
        if primary is None and final and final.get('state',{}).get('steps')==512:primary=final
        resumed=final if final and final.get('state',{}).get('steps',0)>512 else None
        phases['primary']['summary']=primary;phases['resume']['summary']=resumed
        for phase in ('primary','resume'):
            command=phases[phase]['command'];summary=phases[phase]['summary']
            if command and summary and command.get('status')=='finished':
                phases[phase]['cli_outer_minus_training_function_wall_s']=command['wall_s']-summary['wall_s']
                phases[phase]['residual_scope']='Includes Python/torch import, CLI parsing/wrapper/process exit; restore happens INSIDE train.started, so this residual is NOT restore time.'
            if summary:
                n=summary['state']['steps'];expected=updates(n,k)
                phases[phase]['cumulative_transfer_count']=n
                phases[phase]['expected_cumulative_update_count']=expected
                phases[phase]['actual_cumulative_update_count']=summary.get('updates')
                phases[phase]['update_count_exact']=summary.get('updates')==expected
                if summary.get('updates')!=expected:alerts.append(dict(group=group,phase=phase,actual=summary.get('updates'),expected=expected,action='REPORT_PARENT_ONLY_NO_FIX_NO_RETRY'))
        diagnostic=next((r for r in records if r.get('step')==1000),None)
        train_metric=None
        if primary and diagnostic:
            seconds=primary['wall_s']+diagnostic['elapsed_s']
            train_metric=dict(transfers=1000,worker_wall_s=seconds,transfers_per_s=1000/seconds,
                primary_summary_wall_s=primary['wall_s'],resume_elapsed_through1000_diagnostic_s=diagnostic['elapsed_s'],
                includes=['primary cold reset/model creation,512 final checkpoint','resume load/restore and488 consumed transfers through diagnostic'],
                excludes=['inter-command preserve and process startup outside training function','100+96 evaluation and1000 periodic/final checkpoints after diagnostic'],
                scope='Observed short warmup random-action CLI metric; neither steady-state throughput nor a3M cost estimate')
        evaluation=docs.get('validation-0001000.json');complete_eval=bool(evaluation and evaluation.get('complete') is True and evaluation.get('validation',{}).get('episodes')==100 and evaluation.get('transfer',{}).get('episodes')==96)
        complete=bool(resumed and resumed.get('state',{}).get('steps')==1000 and resumed.get('updates')==updates(1000,k) and complete_eval and phases['resume']['command'] and phases['resume']['command'].get('exit_code')==0)
        if evaluation and evaluation.get('complete') and not complete_eval:alerts.append(dict(group=group,error='evaluation completeness/count mismatch',action='REPORT_PARENT_ONLY_NO_FIX_NO_RETRY'))
        checkpoint_files=[]
        if folder.exists():
            for path in sorted(folder.glob('*.pt')):
                checkpoint_files.append(dict(name=path.name,bytes=path.stat().st_size,method='filesystem stat only; no tensor/checkpoint loading or hashing of large payload'))
        g=dict(status='COMPLETE_SMOKE_OBSERVED_P5_UNRESOLVED' if complete else 'SMOKE_PENDING_OR_INCOMPLETE_NO_P5_PASS',update_interval=k,
            phases=phases,documents=docs,diagnostics=records,observed_training_to1000=train_metric,
            complete_smoke=complete,evaluation196=dict(complete=complete_eval,combined_wall_s=evaluation.get('wall_s') if complete_eval else None,
                validation100_wall_s=None,transfer96_wall_s=None,note='Source only gives combined196 wall; no invented split. Missing/incomplete cost remains unknown.'),
            checkpoint_files=checkpoint_files,restore_exact_wall_s=None,
            restore_scope='Not independently timed by current source. Resume train elapsed contains restore plus setup/training; CLI minus train wall is startup/exit residual, not restore.',
            update_density=dict(smoke1000=updates(1000,k)/1000,formal3M=updates(3000000,k)/3000000,
                smoke1000_updates=updates(1000,k),formal3M_updates=updates(3000000,k),density_gap=updates(3000000,k)/3000000-updates(1000,k)/1000),
            periodic_costs=dict(formal_scheduled_checkpoints=12,formal_final_checkpoints=1,formal_eval196_cycles=12,formal_diagnostics=3000,
                measured_checkpoint_summary_scope='CLI timings checkpoint combines periodic/final saves; n/sum/p50/p95/p99/max preserved, not raw per-save traces.',
                full100k_valid_checkpoint_wall_s=None,full100k_restore_wall_s=None,
                reason='Smoke replay capacity100k is allocated, but persisted valid rows only512/1000. Formal CP at250k has100k valid rows. Payload/latency cannot be equated.'),
            expected_resume_increment=dict(transfers=488,updates=updates(1000,k)-updates(512,k)),
            conditional_3M_wall_h=None,gate48h='NOT_ESTABLISHED',policy_scope='All smoke1000 transfer actions are within warmup random-action stage; not later policy distribution.')
        if alerts and phases['primary']['command'] and phases['primary']['command'].get('exit_code') not in (None,0):
            meta=docs.get('interrupted.meta.json',{})
            g['status']='FAILED_BEFORE_FIRST_ACTION' if meta.get('steps')==meta.get('action_calls')==meta.get('env_actions')==0 else 'FAILED_SMOKE_NO_COMPLETION'
            g['failure_metadata']=meta
            g['forensic_checkpoint_scope']='interrupted.pt/actor/meta are failure artifacts; their existence and resume_safe flag do not measure save/load cost, validate a successful512/1000 training checkpoint, or authorize resume.'
        elif alerts and not phases['primary']['command']:
            g['status']='NOT_RUN_AFTER_FIRST_FAILURE'
        groups[group]=g
    failure=None
    failed_job=next((j for j in execution.get('jobs',[]) if j.get('exit_code') not in (None,0)),None)
    if failed_job:
        entry=(failed_job.get('ledger_entries') or [{}])[-1]
        logpath=LOG/Path(entry.get('log','missing')).name
        trace=logpath.read_text() if logpath.exists() else None
        if logpath.exists():files.append(logpath)
        command=groups['B0']['phases']['primary']['command']
        failure=dict(job=failed_job['id'],exit_code=failed_job['exit_code'],cli_wall_s=command.get('wall_s') if command else None,
            c_ledger_command_wall_s=entry.get('elapsed_s'),ledger_timeout_flag=entry.get('timeout'),
            trace_path=str(logpath.relative_to(ROOT)),trace_text=trace,
            observed_stage='train.py::train initial reset -> env.py::reset serial episode sampling -> episode.py::sample line100 check_sampling after asset/scene/planner block -> SamplingIncomplete deadline',
            provenance='Source line100 is where the deadline was detected, not proof that asset/scene/planner alone consumed the budget. No per-phase initial-reset timing summary was emitted.',
            action_calls=groups['B0'].get('failure_metadata',{}).get('action_calls'),steps=groups['B0'].get('failure_metadata',{}).get('steps'),
            env_actions=groups['B0'].get('failure_metadata',{}).get('env_actions'),effective_training_throughput=None,
            note='No successful512/1000 training, no196 evaluation, no independently measured CP/save/restore cost. Do not report0/failurewall as training throughput.')
    report=dict(status='C_SMOKE_FAILED_OR_INCONSISTENT_P5_NOT_ESTABLISHED' if alerts else 'C_SMOKE_COMPLETE_P5_STILL_UNRESOLVED' if all(g['complete_smoke'] for g in groups.values()) else 'C_SMOKE_RUNNING_OR_PARTIAL_P5_NOT_ESTABLISHED',
        source='SRC-1201',generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        author=dict(agent='/root/opt_r3',model='gpt-6.1-sol/high (parent explicit)',recommended='GPT6.1sol / Sonnet5.5 high, causal cost/recovery analysis'),
        execution_status=execution.get('status'),execution_note='Serial job raw status may remain running after failure; overall stopped plus exit_code/end and finished command establish process completion. Original execution table is preserved.',execution_jobs=[{k:j.get(k) for k in ('id','status','exit_code','started','end','limit_s')} for j in execution.get('jobs',[])],
        groups=groups,observed_failure=failure,alerts=alerts,notes=notes,source_sha256={str(p.relative_to(ROOT)):hash_small(p) for p in files if p.exists()},
        cost_formula=dict(units='seconds',updates='U_k(N)=max(0,floor(N/k)-floor(257/k)); B0k1/B3k10, resumed(a,b] increment U(b)-U(a)',
            density_correction='T_loop_g(N)=N*c_observed_loop_g+(U_k(N)-N*rho_observed_g)*c_update_g+Delta_replay_state_g(N)',
            total='T_g(N)=T_start_g+T_loop_g(N)+R_g(N)*c_random_reset_g+3000*c_diag_g+12*c_eval196_g+sum(j=1..12)c_full_cp_g(250000*j,100000)+c_final_cp_g(N,100000)+J_g*c_restore_full_g+T_uninstrumented_logging_g+T_contention_g',
            c_observed_loop='Needs consistent removal of cold/restore/reset/diagnostic/CP/eval from CLI timing. Current raw short metric explicitly includes some of these; if not identifiable keep unknown.',
            c_update='Group-specific incremental sample+SAC cost. consume_transition mixes push/set_transfer/sample/update; current timing alone does not identify incremental cost. Not transplanted from task7.',
            unknowns=['full100k-valid replay CP/restore time and I/O','isolated incremental group SAC/sample cost to correct density','after-warmup policy distribution and replay occupancy/cache effects','random reset frequency/cost over3M','four concurrent workers CPU/GPU/storage contention']),
        next_decision='Claude/user to decide whether to authorize a bounded initial256 reset/sampling phase diagnosis with explicit budget, preserving all sampling/geometry/acceptance contracts; then decide initialization/training/evaluation execution-bound segmentation from evidence. No optimization/retry/new run is authorized by this report.',
        candidate_runs_reference='results/task8/t8-phase2-20261027/long-run-commands-r3.json; prepared only, never executed by this tool',
        P5='BLOCKED_MISSING_ACTUAL_CLI_COSTS' if alerts else 'NOT_ESTABLISHED',gate48h='NOT_ESTABLISHED',long_training_started_by_this_tool=False,
        budgets_snapshot=dict(opt={k:opt.get(k) for k in ('budget_s','used_s','active')},C={k:c_budget.get(k) for k in ('limit_s','used_s','active')}))
    atomic(OUT/'cost-r3.json',json.dumps(report,indent=2)+'\n')
    lines=['# task8.9.1 r3 P5成本记录','',f"状态：**{report['status']}**。P5与48h门未成立，未启动3M。来源[SRC-1201](../../../doc/SOURCES.md#src-1201)；本工具只读JSON/JSONL/CSV和文件stat，不import torch、不加载checkpoint、不触发GPU/optimizer。",'',f"取证UTC：{report['generated_utc']}；固定执行状态{report['execution_status']}。",'', '|组|smoke状态|累计转移/更新|到1000训练短窗吞吐|196完整wall|精确restore计时|','|---|---|---|---|---|']
    for group,g in groups.items():
        last=g['phases']['resume']['summary'] or g['phases']['primary']['summary'];counts=f"{last['state']['steps']}/{last['updates']}" if last else '0/无summary更新记录' if g.get('failure_metadata',{}).get('steps')==0 else '未运行/无summary'
        m=g['observed_training_to1000'];rate=f"{m['transfers_per_s']:.6f}/s（{m['worker_wall_s']:.6f}s）" if m else '未知'
        e=g['evaluation196'];ev=f"{e['combined_wall_s']:.6f}s" if e['complete'] else '未知/未完整'
        lines.append(f"|{group}|{g['status']}|{counts}|{rate}|{ev}|未单独测时|")
    lines+=['', '到1000短窗按primary summary.wall＋resume diagnostic.elapsed_s计算，含初始构建/reset、512保存、恢复与诊断；不含后续196评估/1000保存，不是稳态。CLI外层wall、runtime和CSV原分布已保留；summary.timings/optimizer设备等仅存在时保留，本次没有成功summary，不伪造分项或更新数。详见[JSON](cost-r3.json)，不把启动退出残差叫恢复时间。','', '1000更新B0/B3应为743/75（密度.743/.075），3M为2999743/299975（密度.9999143/.0999917）。只用原短窗吞吐乘3M会漏更新密度差，需同组增量sample+SAC成本修正；当前consume_transition混合更新与push等，不足独立识别。更新公式/总成本公式与缺项见JSON。','', '正式3M含12周期100+96合并评估、12周期CP+1finalCP、3000诊断；196只有合并wall，无100/96独立wall。若既定smoke成功到512/1000，保存也仅相应有效行，非满100k；本次在0转移已停止，正式满回放保存/restore未知不能填0或当已测。计划smoke动作仍在warmup随机阶段，本次0动作，随机reset频率、长期缓存/状态分布、四worker争用仍未认证。','', '推荐/实际：本汇总实际父指定gpt-6.1-sol/high；推荐GPT6.1sol/Sonnet5.5 high作成本因果核查。固定执行由父安排Terra；不在本工具修复、重试或追加验证。候选四run命令仍原long-run-commands-r3.json，禁止本工具启动。']
    if failure:
        monitor=groups['B0']['phases']['primary']['gpu_monitor']
        mem=next((v['max'] for k,v in monitor.get('metrics',{}).items() if k.startswith('memory.used')),None)
        lines+=['','## 实际失败与冷启动证据','',f"B0-primary rc{failure['exit_code']}，CLI wall {failure['cli_wall_s']:.6f}s，原C账本命令{failure['c_ledger_command_wall_s']:.6f}s；账本timeout标志{failure['ledger_timeout_flag']}（异常为内部sampling deadline）。interrupted.meta显示steps/action_calls/env_actions均0，尚无interactions.jsonl或成功summary。B0-resume/B3/postflight未执行。",'',f"GPU1 CSV共{monitor.get('n')}个1Hz全命令样本，采样峰值{mem}MiB；只是采样到的设备memory.used（含启动/分配/失败收尾），没有PyTorch allocated/reserved峰值实测，也不认证正式训练显存。",'', '原始trace：training.py:200首次env.reset → env.py:64逐环境sampler.sample → episode.py:100（asset/scene/planner块后）check_sampling → SamplingIncomplete。这是deadline检出位置；没有分项flush，不能断言该块是唯一耗时根因。初始配置/模型/100k容量分配、采样、失败取证保存的独立成本未知。', '', 'interrupted.pt/actor/meta仅失败取证产物，filesystem stat见JSON；未单独计时，不是成功训练CP/恢复成本，也不因resume_safe=true自动恢复。无有效训练吞吐，0/失败wall不作为吞吐。196评估和周期保存/恢复成本全部未知，不能据此计算每run3M或判48h。', '', '最小待决定事项：是否授权一次保持原256环境/采样/几何/接受规则的有界初始化分项诊断及预算；再依据诊断决定初始化、训练及评估执行限额如何分段。不自动延限、缩规模、改接受条件、优化或重试。']
    if alerts:lines+=['', '失败/不一致立即交父：', '', *['- '+json.dumps(a,ensure_ascii=False) for a in alerts]]
    atomic(OUT/'cost-r3.md','\n'.join(lines)+'\n')
    print(json.dumps(dict(status=report['status'],execution=report['execution_status'],jobs=report['execution_jobs'],alerts=alerts,groups={k:dict(complete=g['complete_smoke'],training=g['observed_training_to1000'],eval196=g['evaluation196']) for k,g in groups.items()})))

if __name__=='__main__':main()
