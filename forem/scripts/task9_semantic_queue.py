#!/usr/bin/env python3
"""Bounded serial task9.6 evaluation supervisor; no training or retries."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

ROOT=Path('/home/ybc/projects/CL-FoReM')
LOG=ROOT/'forem/logs/task9/t9-semantic-20261102'
OUT=ROOT/'forem/results/task9/t9-semantic-20261102'
def now():return dt.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def write(p,x):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def main():
    state=dict(started=now(),pid=os.getpid(),status='active',runs=[])
    write(LOG/'queue-state.json',state)
    for seed in (4718,4719,4720):
        target=f'/root/mm_husky_ws/results/task9/t9-semantic-20261102/seed{seed}'
        command=['sg','docker','-c',f'docker exec -e PYTHONPATH=/root/mm_husky_ws/src -e CUDA_VISIBLE_DEVICES=0 -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=2 forem-dev timeout --signal=TERM --kill-after=60s 1800s python3 -B -u /root/mm_husky_ws/scripts/task9_semantic_eval.py --seed {seed} --output {target}']
        record=dict(seed=seed,started=now(),command=command,status='running');state['runs'].append(record)
        with (LOG/f'seed{seed}.log').open('x') as stream:
            start=time.monotonic();p=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT)
            record['host_pid']=p.pid;write(LOG/'queue-state.json',state)
            record['exit_code']=p.wait();record['wall_s']=time.monotonic()-start
        record['ended']=now();record['status']='done' if record['exit_code']==0 else 'failed';write(LOG/'queue-state.json',state)
        if record['exit_code']!=0:
            state.update(status='failed',ended=now());write(LOG/'queue-state.json',state);return 1
    summary=dict(started=state['started'],ended=now(),runs=[],scope='repeat existing semantic evaluation; not independent test',episodes=288)
    for seed in (4718,4719,4720):
        result=json.loads((OUT/f'seed{seed}/evaluation.json').read_text());rows=result['transfer']['rows']
        old=json.loads((ROOT/f'forem/results/task9/t9-stage2-20261029/B3_5M-seed{seed}/validation-5000000.json').read_text())['transfer']['rows']
        keys=lambda r:(r['map_id'],r['seed'],r['stream_index'])
        old_by={keys(r):r for r in old};assert len(rows)==len(old_by)==96 and len({keys(r) for r in rows})==96
        assert {keys(r) for r in rows}==set(old_by)
        count=sum(bool(r['strict_success']) for r in rows);assert abs(count/96-result['transfer']['strict_success_rate'])<1e-12
        maps={r['map_id'] for r in rows};assert len(maps)==24 and all(sum(r['map_id']==m for r in rows)==4 for m in maps)
        cats={}
        for category in sorted({r['difficulty'] for r in rows}):
            group=[r for r in rows if r['difficulty']==category];cats[category]=dict(success=sum(bool(r['strict_success']) for r in group),episodes=len(group))
        summary['runs'].append(dict(seed=seed,success=count,episodes=96,rate=count/96,categories=cats,
            old_success=sum(bool(r['strict_success']) for r in old),outcome_changed_cases=sum(r['strict_success']!=old_by[keys(r)]['strict_success'] for r in rows),
            wall_s=result['wall_s']))
    summary['success']=sum(r['success'] for r in summary['runs']);summary['rate']=summary['success']/288
    summary['categories']={}
    for r in summary['runs']:
        for k,v in r['categories'].items():
            item=summary['categories'].setdefault(k,dict(success=0,episodes=0));item['success']+=v['success'];item['episodes']+=v['episodes']
    write(OUT/'summary.json',summary)
    lines=['# task9.6 语义地图复评结果','',f"完成：{summary['ended']}。24地图×4固定回合×3模型，共288回合。重复原有固定评估，不是新的独立测试。",'', '|训练seed|成功/96|成功率|相对旧评估结果变化回合数|','|---|---:|---:|---:|']
    for r in summary['runs']:lines.append(f"|{r['seed']}|{r['success']}/96|{r['rate']:.2%}|{r['outcome_changed_cases']}|")
    lines+=['','|类别|三模型合计成功/回合|成功率|','|---|---:|---:|']
    for k,v in summary['categories'].items():lines.append(f"|{k}|{v['success']}/{v['episodes']}|{v['success']/v['episodes']:.2%}|")
    lines+=['', '合计为三个已训练模型在相同地图和固定episode上的描述性汇总，不视为288个独立地图或训练种子；不用于选模、冻结或统计显著性结论。']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')
    state.update(status='completed_pending_review',ended=now(),summary=str(OUT/'summary.json'),report=str(OUT/'report.md'));write(LOG/'queue-state.json',state)
    print(json.dumps(state),flush=True);return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        write(LOG/'supervisor-error.json',dict(time=now(),error=repr(e)));raise
