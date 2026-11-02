#!/usr/bin/env python3
"""Read-only online trial accounting; JSON-only live monitoring, no model calls."""
import argparse
import json
from pathlib import Path
import time


def read(path,default=None):
    return json.loads(path.read_text()) if path.exists() else default


def lines(path):
    if not path.exists():return []
    raw=path.read_text().splitlines();result=[]
    for i,value in enumerate(raw):
        try:result.append(json.loads(value))
        except json.JSONDecodeError:
            if i!=len(raw)-1:raise
    return result


def report(run):
    launch=read(run/'launch.json',{});budget=read(run/'training-budget.json',{})
    summary=read(run/'training-summary.json');events=lines(run/'events.jsonl')
    batches=lines(run/'batch-boundaries.jsonl');updates=lines(run/'updates.jsonl')
    executions=lines(run/'real-executions.jsonl')
    warmup=next((v for v in events if v['event']=='warmup_complete'),None)
    first=next((v for v in events if v['event']=='first_update_complete'),None)
    first_evidence=read(run/'first-update-evidence.json')
    elapsed=(launch.get('wall_seconds') if launch.get('status')=='process_exited' else
             max(0,time.time()-launch.get('started_epoch',time.time())))
    if summary is not None:
        # Use the worker's final elapsed cost; parent supervision is separate.
        worker_seconds=summary['wall_seconds']
    else:worker_seconds=None
    counts={}
    for name in ('actor','q1','q2'):
        observed=[v.get('gradient_report',{}).get('head_a.'+name,{}) for v in updates]
        counts[name]=dict(records_with_gradient=sum(v.get('with_gradient',0)>0 for v in observed),
            records_with_finite_nonzero_gradient=sum(v.get('finite',False) and v.get('nonzero',0)>0 for v in observed),
            records_on_cuda=sum(bool(v.get('parameter_devices')) and all(d.startswith('cuda:') for d in v['parameter_devices']) for v in observed))
    return dict(run_id=run.name,code_commit=launch.get('code_commit'),launch=launch,budget=budget,
        status=summary.get('status') if summary else launch.get('status','not_started'),
        completed_real_decisions=budget.get('completed_decisions',0),reserved_real_decisions=budget.get('reserved_decisions',0),
        in_flight=budget.get('in_flight',0),online_update_ledger=budget.get('updates',0),
        durable_update_journal_records=len(updates),last_durable_update_record=updates[-1] if updates else None,
        uniform_warmup_rows_in_execution_journal=sum(len(v['selected']) for v in executions if v.get('selection_mode')=='uniform_warmup'),
        sac_rows_in_execution_journal=sum(len(v['selected']) for v in executions if v.get('selection_mode')=='sac'),
        warmup_complete_event=warmup,first_update_complete_event=first,
        first_update_evidence=first_evidence,per_head_gradient_records=counts,
        last_completed_replay_count=batches[-1]['replay'] if batches else 0,
        natural_batch_end_counts=[v['ended_rows'] for v in batches],
        completed_batches=len(batches),execution_journal_files=len(list((run/'real-executions').glob('batch-*.pt'))),
        supervisor_wall_seconds=elapsed,worker_wall_seconds=worker_seconds,
        remaining_training_seconds=max(0,launch.get('deadline_epoch',time.time())-time.time()) if summary is None else 0,
        timing=None if summary is None else summary['timing'],final_summary=summary,
        collector_resume_verified=False,paired_run=False,performance_improvement_evaluated=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path);p.add_argument('--compact',action='store_true');args=p.parse_args()
    result=report(args.run)
    if args.output:args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if args.compact:
        print(json.dumps({k:result[k] for k in ('status','completed_real_decisions','reserved_real_decisions','in_flight','online_update_ledger','uniform_warmup_rows_in_execution_journal','completed_batches','supervisor_wall_seconds','remaining_training_seconds')}))
    else:print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':main()
