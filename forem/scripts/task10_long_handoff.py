#!/usr/bin/env python3
"""Task10.17 persistent B->C->D driver and independent CPU raw training audit."""
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from task10.runtime import atomic_json,sha256


def read(path):return json.loads(Path(path).read_text())
def stamp():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()


def audit(run,output):
    import torch
    from task10.recovery import tree_equal
    from task10.training_evidence import summarize_evidence
    from task7_upper.replay import row
    load=lambda p:torch.load(p,map_location='cpu',weights_only=False)
    issues=[];checks={}
    summary=read(run/'training-summary.json');ledger=read(run/'training-budget.json');launch=read(run/'launch.json')
    checkpoint=run/'checkpoints/decision-010000.boundary.pt'
    if summary.get('status')!='complete':issues.append('training did not reach complete terminal budget')
    if not checkpoint.exists():issues.append('missing 10000 boundary checkpoint')
    if launch.get('status')!='process_exited' or launch.get('returncode')!=0:issues.append('launcher exit missing/nonzero')
    if (ledger['reserved_decisions'],ledger['completed_decisions'],ledger['in_flight'],ledger['updates'])!=(10000,10000,0,9000):issues.append('terminal budget differs')
    if (ledger['max_decisions'],ledger['max_updates'],ledger['max_seconds'])!=(10000,9000,194400):issues.append('authorized limits differ')
    if launch.get('deadline_epoch')!=ledger['deadline_epoch'] or launch.get('started_epoch')!=ledger['started_epoch']:issues.append('epoch mismatch')
    if launch.get('finished_epoch',float('inf'))>ledger['deadline_epoch']:issues.append('training outer wall exceeded 54h')
    cfg=read(run/'contract.json')
    changed=[p for p,h in cfg['code_sha256'].items() if not (ROOT/p).exists() or sha256(ROOT/p)!=h]
    checks['changed_training_code']=changed
    if changed:issues.append('training source code changed')
    if sha256(Path(cfg['config_path']))!=cfg['config_sha256']:issues.append('training config hash changed')
    initial=read(run/'initial-comparison.json')
    if not initial.get('full_model_state_equal'):issues.append('initial full weight mismatch')
    updates=[json.loads(x) for x in (run/'updates.jsonl').read_text().splitlines()] if (run/'updates.jsonl').exists() else []
    if len(updates)!=ledger['updates']:issues.append('updates log/ledger mismatch')
    for i,event in enumerate(updates,1):
        expected_decisions=1000+8*math.ceil(i/8)
        if event['updates']!=i or event['decisions']!=expected_decisions:issues.append(f'update identity {i} differs');break
        if event.get('scheduler_total_updates')!=9000 or not math.isclose(event['lr'],1e-4*.01**(i/9000),rel_tol=1e-12,abs_tol=1e-16):issues.append(f'LR update {i} differs');break
        if not math.isclose(event['alpha'],.35,rel_tol=1e-6):issues.append(f'alpha update {i} differs');break
        if any(not math.isfinite(event[key]) for key in ('critic','actor','gradient_norm','alpha')):issues.append(f'nonfinite update {i}');break
    records={};journal_hashes={}
    for path in sorted((run/'real-executions').glob('batch-*.pt')):
        raw=load(path);f=raw['fields'];journal_hashes[str(path.relative_to(run))]=sha256(path)
        if not raw.get('next_boundary_ready'):issues.append(f'pending next boundary {path.name}')
        for i in range(len(f['episode_id'])):
            identity=(str(f['run_id']),int(f['environment_id'][i]),int(f['episode_id'][i]),int(f['decision_index'][i]))
            if identity in records:issues.append(f'duplicate transition {identity}')
            records[identity]=row(f,i,len(f['episode_id']))
    if len(records)!=ledger['completed_decisions']:issues.append('journal completed count mismatch')
    warmup=load(run/'warmup-complete.pt') if (run/'warmup-complete.pt').exists() else None
    if warmup is None or warmup['counters']['decisions']!=1000 or warmup['learner']['updates']!=0 or warmup['replay']['size']!=1000:issues.append('fresh 1000/0 warmup missing')
    execution=[json.loads(x) for x in (run/'real-executions.jsonl').read_text().splitlines()] if (run/'real-executions.jsonl').exists() else []
    if any(x['selection_mode']!=('uniform_warmup' if x['completed']<=1000 else 'sac') for x in execution):issues.append('warmup selection modes differ')
    if checkpoint.exists():
        final=load(checkpoint)
        if (final['counters']['decisions'],final['counters']['updates'],final['learner']['updates'],final['learner']['total_updates'])!=(10000,9000,9000,9000):issues.append('final checkpoint counters differ')
        if final['ledger_sha256']!=sha256(run/'training-budget.json'):issues.append('final checkpoint ledger hash differs')
        compared=0
        for key,sequence in final['replay']['episodes'].items():
            for record in sequence:
                identity=(str(key[0]),int(key[1]),int(key[2]),int(record['decision_index']))
                if identity not in records or not tree_equal(records[identity],record):issues.append(f'journal/replay differs {identity}')
                compared+=1
        if compared!=10000:issues.append('final replay size differs')
        actor=load(run/'final.actor.pt')
        if not tree_equal(actor['model'],final['learner']['model']):issues.append('terminal actor is not budget endpoint')
        checks['terminal_checkpoint_sha256']=sha256(checkpoint)
    if not summary.get('lower_unchanged'):issues.append('B3 frozen check missing/failed')
    if (run/'first-update-evidence.pt').exists():
        evidence=summarize_evidence(load(run/'first-update-evidence.pt'))
        checks['first_update']=evidence
        if not evidence.get('gpu_update_verified'):issues.append('raw first GPU update audit failed')
    else:issues.append('first GPU update evidence missing')
    expected=set(range(256,10001,256))|{2000,5000,10000}
    checks['checkpoint_metadata']={}
    for decision in sorted(expected):
        path=run/'checkpoints'/f'decision-{decision:06d}.json'
        if not path.exists():issues.append(f'missing scheduled checkpoint {decision}');continue
        item=read(path)
        valid=item['decisions']==decision and item['updates']==max(0,decision-1000)
        for kind in ('boundary','learner','actor'):
            p=run/item[kind]['path'];valid=valid and p.is_file() and sha256(p)==item[kind]['sha256']
        checks['checkpoint_metadata'][str(decision)]=valid
        if not valid:issues.append(f'checkpoint metadata/hash {decision} differs')
    checks.update(unique_journal_transitions=len(records),updates=len(updates),initial=initial,
        launch_returncode=launch.get('returncode'),training_wall_seconds=launch.get('wall_seconds'),
        training_worker_seconds=summary.get('worker_seconds'),ledger=ledger)
    result=dict(status='verified_complete' if not issues else 'incomplete_or_failed',issues=issues,
        checks=checks,journal_hashes=journal_hashes,verified_at=stamp(),zero_new_decisions=True,zero_updates=True)
    atomic_json(output,result)
    training_curves(run, output.parent)
    return 0 if not issues else 1


def training_curves(run, output):
    """Exact update CSV and labelled descriptive rolling averages, no model selection."""
    import csv
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    events=[json.loads(x) for x in (run/'updates.jsonl').read_text().splitlines()] if (run/'updates.jsonl').exists() else []
    keys=['decisions','updates','critic','actor','gradient_norm','alpha','lr','wall_seconds']
    with (output/'training-learning-curve.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader()
        writer.writerows({k:event.get(k) for k in keys} for event in events)
    fig,axes=plt.subplots(3,1,figsize=(8,8),sharex=True)
    if events:
        x=[r['decisions'] for r in events]
        def rolling(key):
            values=[r[key] for r in events];return [sum(values[max(0,i-99):i+1])/len(values[max(0,i-99):i+1]) for i in range(len(values))]
        axes[0].plot(x,rolling('critic'),label='critic; trailing 100 updates')
        axes[0].plot(x,rolling('actor'),label='actor; trailing 100 updates');axes[0].legend()
        axes[1].plot(x,rolling('gradient_norm'));axes[1].set_ylabel('Gradient norm; trailing 100')
        axes[2].plot(x,[r['lr'] for r in events]);axes[2].set_yscale('log');axes[2].set_ylabel('Learning rate')
    axes[2].set_xlabel('Real training decisions');fig.suptitle('Task10.17 training diagnostics; loss is not task success')
    fig.tight_layout();fig.savefig(output/'training-learning-curve.png',dpi=180);plt.close(fig)


def interpret(reports):
    ordered=[reports.get(str(d)) for d in (2000,5000,10000)]
    complete=all(r and r.get('status')=='verified_complete' for r in ordered)
    if not complete:
        return dict(learning='检查点或原件审计不完整，无法判断持续改善。',inplace='完整曲线不足，按逐检查点原始结果报告。',
            recovery='A真实恢复证据单独见A结果；未从不完整训练反推恢复可靠。',recommendation='先补齐当前授权内的原件交接并交决策者裁定，本轮不自动进入20k×3。')
    successes=[r['scores']['strict_success'] for r in ordered]
    if successes[0]<successes[1]<successes[2]:learning=f'固定12场景严格成功随2k/5k/10k持续上升：{successes}；仅此单种子清单的观察。'
    elif len(set(successes))==1:learning=f'固定12场景严格成功持平：{successes}，未观察到随预算持续改善。'
    elif successes[-1]>successes[0]:learning=f'严格成功由{successes[0]}/12到{successes[-1]}/12，中间为{successes}；不是各阶段持续改善。'
    else:learning=f'严格成功读数{successes}，不支持随预算持续改善。'
    fractions=[r['selected_inplace']['fraction'] for r in ordered]
    leading=[sum(x.get('new') is not None and x['new']>0 for x in r['initial_logit_comparison']) for r in ordered]
    inplace=f'2k/5k/10k原地选择比例={fractions}，同12初态原地logit领先个数={leading}；原地选择是否形成停滞另见termination_reasons，不能把任何合法原地动作都叫病态。'
    final_pair=ordered[-1]['paired'].get('uniform',{})
    if successes[-1]>successes[0] and successes[-1]>ordered[-1]['reference_scores']['uniform']['strict_success']:
        recommendation='本固定清单观察到训练收益且预算终点超过uniform，可作为另行审议20k×3的有限依据；仍须独立种子/更广验证，不能凭单种子12场景证明泛化。'
    else:
        recommendation='本固定清单未同时显示持续训练收益及预算终点超越uniform，建议先由决策者审查收益/成本，再决定是否投入20k×3；本轮不自动启动。'
    return dict(learning=learning,inplace=inplace,recovery='A精确新PID恢复结果见A comparison.json；证明已测混合边界与下一批/下一更新，不代表所有未来中断均可恢复。',recommendation=recommendation)


def finalise(run,evaluation,started,stage_exits):
    sequence=read(evaluation/'sequence.json') if (evaluation/'sequence.json').exists() else {'status':'missing','checkpoints':[]}
    train_audit=read(run/'parent-training-audit.json') if (run/'parent-training-audit.json').exists() else {'status':'missing','issues':['audit unavailable']}
    curve=read(evaluation/'curve-summary.json') if (evaluation/'curve-summary.json').exists() else {}
    reports={}
    for decision in (2000,5000,10000):
        path=evaluation/f'checkpoint-{decision:06d}'/'report.json'
        supplemental=evaluation/f'checkpoint-{decision:06d}'/'report-D.json'
        if path.exists():reports[str(decision)]=read(path)
        elif supplemental.exists():reports[str(decision)]=read(supplemental)
    launch=read(run/'launch.json') if (run/'launch.json').exists() else {}
    training=read(run/'training-summary.json') if (run/'training-summary.json').exists() else {}
    interpretation=interpret(reports)
    table_rows=['|训练决策|更新|报告状态|严格成功/12|原地比例|对uniform配对|','|---:|---:|---|---:|---:|---|']
    for d,u in ((2000,1000),(5000,4000),(10000,9000)):
        r=reports.get(str(d))
        if r:
            table_rows.append(f"|{d}|{u}|{r.get('status')}|{r.get('scores',{}).get('strict_success')}/12|{r.get('selected_inplace',{}).get('fraction')}|{json.dumps(r.get('paired',{}).get('uniform'),ensure_ascii=False)}|")
        else:table_rows.append(f'|{d}|{u}|missing|missing|missing|missing|')
    checkpoint_table='\n'.join(table_rows)
    audit_a=read(ROOT/'results/task10/t10-17-audit-20261103-s101/audit-budget.json')
    dispatch_epoch=datetime.fromisoformat('2026-11-03T22:51:46.639755+08:00').timestamp()
    handoff=dict(status='review',complete=train_audit.get('status')=='verified_complete' and sequence.get('status')=='complete' and (evaluation/'learning-curve.png').exists() and (run/'training-learning-curve.png').exists(),
        run=str(run),evaluation=str(evaluation),stage_exits=stage_exits,training_audit=train_audit,
        evaluation_sequence=sequence,curve=curve,reports=reports,interpretation=interpretation,
        audit_a=audit_a,full_global_wall_seconds=time.time()-dispatch_epoch,global_wall_seconds=time.monotonic()-started,
        training_wall_seconds=launch.get('wall_seconds'),training_worker_seconds=training.get('worker_seconds'),
        evaluation_worker_seconds=sequence.get('cumulative_worker_seconds'),
        cumulative_worker_seconds=audit_a.get('wall_seconds',0)+training.get('worker_seconds',0)+sequence.get('cumulative_worker_seconds',0),finished_at=stamp(),
        model_selection='fixed 10000 budget endpoint; no validation selection; missing endpoint remains missing',
        finalizer_sha256=sha256(Path(__file__)),
        scope='no additional seeds, training budget, task11, or test pool')
    atomic_json(run/'handoff.json',handoff)
    def compact(obj):return json.dumps(obj,ensure_ascii=False,default=str)
    text=f'''\n\n## {stamp()} · B→C→D 持久收尾\n\n状态review，交决策者原件审核；完整条件={handoff['complete']}。推荐GPT6.1sol/high、Sonnet5.5/high，恢复/训练/原件核验；实际模型/强度未知，父统一GPU/预算/原件复算。依据[SRC-T10-044](../../../SOURCES.md#src-t10-044)。\n\n训练run `{run.name}`，终态 `{training.get('status','missing')}`，真实决策 {training.get('actual_decisions','missing')}/10000，更新 {training.get('updates','missing')}/9000。独立CPU原件审计 `{train_audit['status']}`，issues={compact(train_audit.get('issues'))}。评估顺序终态 `{sequence.get('status')}`，每检查点和缺失见 `{evaluation}/sequence.json` 与report。学习曲线CSV/PNG、同初态logit CSV位于评估根；模型固定预算终点，不按成绩选模。\n\nA实测worker窗口 {audit_a.get('wall_seconds')}s；全任务全局墙钟 {handoff['full_global_wall_seconds']}s，累计测量worker阶段 {handoff['cumulative_worker_seconds']}s（A监督窗口+训练worker+评估子进程；CPU准备/排队另在global中）。训练墙钟 {launch.get('wall_seconds')}s，训练worker {training.get('worker_seconds')}s，评估worker {sequence.get('cumulative_worker_seconds')}s，B→D全局 {handoff['global_wall_seconds']}s；A另见本节点A记录，排队/CPU收尾计入global，不能把worker累计当墙钟。退出码 {compact(stage_exits)}。\n\n学习是否持续改善：{interpretation['learning']}\n\n原地是否复发：{interpretation['inplace']}\n\n保存恢复：{interpretation['recovery']}\n\n20k×3建议：{interpretation['recommendation']}\n\n{checkpoint_table}\n\n三个检查点完整读数见handoff.json/reports及curve-summary.json。仅单种子、固定12validation场景；该曲线不能证明跨种子或test泛化，也不能单凭loss下降确认收益。20k×3须决策者结合曲线与uniform配对裁定，本轮不自动启动。任何不完整/缺失保留，不能声称完整通过。\n\n原件：`{run}/parent-training-audit.json`、`handoff.json`、launch/worker-exit/training-budget/contract与checkpoints；评估原件 `{evaluation}`。复算：CUDA隐藏调用 `task10_long_handoff.py audit --run <container run> --output <new audit path>`；评估各report入口见17.3。完整模型/配置/代码/地图哈希在contract、checkpoint metadata、manifest、parent audit中。\n'''
    doc=ROOT/'doc';results=doc/'tasks/task10/task10.17/RESULTS.md'
    with results.open('a') as stream:stream.write(text)
    log=doc/'agent_logs/task10/task10.17/20261103-codex-execution.md'
    with log.open('a') as stream:stream.write(text.replace('../../../SOURCES.md','../../../SOURCES.md'))
    progress=doc/'PROGRESS.md';current=progress.read_text()
    entry=f"{stamp()} **T10.17-10K-20261103 · Codex · review**：持久B/C/D收尾，完整条件={handoff['complete']}；训练{training.get('actual_decisions','missing')}/10000、{training.get('updates','missing')}/9000，C={sequence.get('status')}。未追加预算/种子/task11。[结果](tasks/task10/task10.17/RESULTS.md)。\n\n"
    progress.write_text(current.replace('# 当前进度\n\n','# 当前进度\n\n'+entry,1))
    with (doc/'SOURCES.md').open('a') as stream:
        stream.write(f'\nSRC-T10-044 实际收尾核查 {stamp()}：项目原件/CPU复算，Codex持久driver；run `{run.name}`、evaluation `{evaluation.name}`，完整条件={handoff["complete"]}；原始结论与限制以[17结果](tasks/task10/task10.17/RESULTS.md)和run/handoff.json、parent-training-audit.json、各checkpoint report及curve-summary.json为准。精确版本/哈希在contract/manifest/checkpoint metadata，退出码见stage-exits.json；未读取原件或缺失不得当已验收，不自动扩大预算。\n')
    return handoff


def drive(args):
    run=args.run.resolve();evaluation=args.evaluation.resolve()
    logs=ROOT/'logs/task10'/run.name;logs.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();exits=[]
    atomic_json(logs/'driver-status.json',dict(status='starting',pid=os.getpid(),ppid=os.getppid(),sid=os.getsid(0),started_at=stamp()))
    stages=[('B',[sys.executable,'-u',str(ROOT/'scripts/task10_long_launch.py'),'--run',str(run),'--commit',args.commit,
        '--initial-reference',str(ROOT/'results/task10/t10-kl-online-20261103-s101/initial-learner.pt')])]
    try:
        for stage,command in stages:
            with (logs/f'driver-{stage}.stdout').open('x') as out,(logs/f'driver-{stage}.stderr').open('x') as err:
                child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
                atomic_json(logs/'driver-status.json',dict(status='running',stage=stage,pid=os.getpid(),child_pid=child.pid,command=command))
                rc=child.wait()
            exits.append(dict(stage=stage,returncode=rc));atomic_json(logs/'stage-exits.json',exits)
        if (run/'training-summary.json').exists():
            command=[sys.executable,'-u',str(ROOT/'scripts/task10_long_validation.py'),'sequence',
                '--source',str(run),'--run',str(evaluation),'--commit',args.commit]
            with (logs/'driver-C.stdout').open('x') as out,(logs/'driver-C.stderr').open('x') as err:
                child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
                atomic_json(logs/'driver-status.json',dict(status='running',stage='C',pid=os.getpid(),child_pid=child.pid,command=command))
                rc=child.wait()
            exits.append(dict(stage='C',returncode=rc));atomic_json(logs/'stage-exits.json',exits)
            import shlex
            for decision in (2000,5000,10000):
                group=evaluation/f'checkpoint-{decision:06d}'
                if not (group/'report.json').exists() and all((group/f).exists() for f in ('manifest.json','budget.json','launch.json')):
                    words=['docker','exec','--user','1004:1004','-e','CUDA_VISIBLE_DEVICES=',
                        '-e','PYTHONPATH=/workspace/src','-e','OMP_NUM_THREADS=2','forem-task10-runtime',
                        'timeout','300s','python3','-u','/workspace/scripts/task10_long_validation.py','report',
                        '--run',str(Path('/workspace')/group.relative_to(ROOT)),
                        '--output',str(Path('/workspace')/group.relative_to(ROOT)/'report-D.json')]
                    with (logs/f'driver-D-report-{decision}.stdout').open('x') as out,(logs/f'driver-D-report-{decision}.stderr').open('x') as err:
                        child=subprocess.run(['sg','docker','-c',shlex.join(words)],stdout=out,stderr=err)
                    exits.append(dict(stage=f'D-readonly-report-{decision}',returncode=child.returncode))
                    atomic_json(logs/'stage-exits.json',exits)
            cmd=['docker','exec','--user','1004:1004','-e','CUDA_VISIBLE_DEVICES=','-e','PYTHONPATH=/workspace/src',
                '-e','OMP_NUM_THREADS=2','forem-task10-runtime','python3','-u','/workspace/scripts/task10_long_handoff.py','audit',
                '--run',str(Path('/workspace')/run.relative_to(ROOT)),
                '--output',str(Path('/workspace')/run.relative_to(ROOT)/'parent-training-audit.json')]
            with (logs/'driver-D-audit.stdout').open('x') as out,(logs/'driver-D-audit.stderr').open('x') as err:
                rc=subprocess.run(['sg','docker','-c',shlex.join(cmd)],stdout=out,stderr=err).returncode
            exits.append(dict(stage='D-audit',returncode=rc));atomic_json(logs/'stage-exits.json',exits)
    except BaseException as exc:
        atomic_json(logs/'driver-error.json',dict(error=repr(exc),traceback=traceback.format_exc()))
    finally:
        handoff=finalise(run,evaluation,started,exits)
        atomic_json(logs/'driver-status.json',dict(status='finished',handoff_complete=handoff['complete'],pid=os.getpid(),finished_at=stamp(),stage_exits=exits))
    return 0 if handoff['complete'] else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('drive','audit'));p.add_argument('--run',type=Path,required=True)
    p.add_argument('--evaluation',type=Path);p.add_argument('--commit');p.add_argument('--output',type=Path);a=p.parse_args()
    if a.mode != 'audit': return drive(a)
    try: return audit(a.run,a.output)
    except BaseException as exc:
        atomic_json(a.output,dict(status='incomplete_or_failed',issues=['CPU audit raised: '+repr(exc)],
            traceback=traceback.format_exc(),verified_at=stamp(),zero_new_decisions=True,zero_updates=True))
        try: training_curves(a.run,a.output.parent)
        except BaseException: pass
        return 1
if __name__=='__main__':raise SystemExit(main())
