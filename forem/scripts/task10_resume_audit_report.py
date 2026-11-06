#!/usr/bin/env python3
"""CPU original-artifact A acceptance and explicit 10k/48h cost projection."""
import argparse
import json
import math
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from task10.runtime import atomic_json,sha256


def run(root,output):
    import torch
    import numpy as np
    from task10.recovery import mismatch_report
    from task10.training_evidence import summarize_evidence
    load=lambda p:torch.load(p,map_location='cpu',weights_only=False)
    read=lambda p:json.loads(p.read_text())
    issues=[];shared=read(root/'audit-budget.json');comparison=read(root/'comparison.json')
    capture=load(root/'decision-boundary.pt');reference=load(root/'reference/branch.pt');resumed=load(root/'resumed/branch.pt')
    differences=mismatch_report(reference['before'],resumed['before'])+mismatch_report(reference['after'],resumed['after'])
    if differences:issues.append('reference/resume original tensors differ')
    if reference['pid']==resumed['pid']:issues.append('restore did not use a new PID')
    if capture['started_monotonic']!=reference['started'] or reference['started']!=resumed['started']:issues.append('start changed')
    if capture['deadline_monotonic']!=reference['deadline'] or reference['deadline']!=resumed['deadline']:issues.append('deadline changed')
    if time.time() > shared['deadline_epoch']:issues.append('A review exceeded original one-hour wall')
    if comparison['status']!='verified' or shared['status']!='verified':issues.append('A supervisor/comparison did not pass')
    if not (0<shared['real_decisions']<=128 and 0<shared['diagnostic_updates']<=64 and shared['wall_seconds']<=3600):issues.append('shared resource cap differs')
    save=read(root/'save-report.json')
    if not (any(save['ended']) and not all(save['ended']) and any(save['histories']) and any(h==0 for h in save['histories'])):issues.append('mixed surviving/new rows not covered')
    total=0;identities={};attempted_steps=0;committed_steps=0
    for label,folder in [('capture',root/'capture'),('reference',root/'reference'),('resumed',root/'resumed')]:
        rows=[]
        for p in sorted((folder/'journals').glob('*.pt')):
            raw=load(p);fields=raw['fields']
            attempted_steps+=int(fields['attempted_substeps'].sum())
            committed_steps+=int(fields['committed_substeps'].sum())
            if not raw.get('next_boundary_ready'):issues.append(f'{label}: pending next boundary')
            for i in range(len(fields['episode_id'])):
                rows.append((str(fields['run_id']),int(fields['environment_id'][i]),int(fields['episode_id'][i]),int(fields['decision_index'][i])))
        if len(rows)!=len(set(rows)):issues.append(f'{label}: duplicate identities')
        identities[label]=rows;total+=len(rows)
    if total!=shared['real_decisions']:issues.append('shared decision count differs from actual journals')
    if set(identities['capture'])&set(identities['resumed']):issues.append('restored original collector duplicated charged decisions')
    if identities['reference']!=identities['resumed']:issues.append('paired next batch decision identities differ')
    updates=sum(len(list((root/sub).glob('diagnostic-update-*.pt'))) for sub in ('capture','reference','resumed'))
    if updates!=shared['diagnostic_updates']:issues.append('shared update attempts differ from raw successful updates')
    gpu=summarize_evidence(load(root/'gpu-update-evidence.pt'))
    if not gpu['gpu_update_verified']:issues.append('raw GPU update/optimizer/B3 evidence failed')
    a,b=read(root/'capture/performance.json'),read(root/'resumed/performance.json')
    raw={}
    for report in (a,b):
        for key,values in report['raw'].items():raw.setdefault(key,[]).extend(values)
    stats={key:dict(count=len(v),sum_s=sum(v),mean_s=float(np.mean(v)),p50_s=float(np.percentile(v,50)),
        p95_s=float(np.percentile(v,95)),max_s=max(v)) for key,v in raw.items() if v}
    collection_keys=('collection_inference','collection_execution','candidate_prediction','replay_to_cpu','reset_ended')
    measured_collection=sum(stats[k]['sum_s'] for k in collection_keys if k in stats)
    per_decision=measured_collection/total
    update_mean=stats['diagnostic_update']['mean_s'];update_p95=stats['diagnostic_update']['p95_s']
    decisions=capture['counters']['decisions'];save_seconds=stats['full_save']['mean_s']
    restore_seconds=stats['full_restore']['mean_s']
    checkpoint_decisions=sorted(set(range(256,10001,256))|{2000,5000,10000})
    # Explicit conservative engineering scaling: measured full save grows
    # linearly from the measured checkpoint size with retained transitions.
    scaled_saves=sum(save_seconds*max(1,d/decisions) for d in checkpoint_decisions)
    initialization=stats.get('initial_reset',{'sum_s':0})['sum_s']+stats.get('lower_load',{'mean_s':0})['mean_s']
    nominal=10000*per_decision+9000*update_mean+scaled_saves+initialization+120
    guarded=10000*per_decision+9000*update_p95+scaled_saves+initialization+restore_seconds*10000/decisions+120
    if not math.isfinite(guarded) or guarded>172800:issues.append('measured cost projection does not support 48h')
    result=dict(status='passed' if not issues else 'not_ready',issues=issues,
        sources=dict(checkpoint=sha256(root/'decision-boundary.pt'),frozen_code=sha256(root/'frozen-code.json')),
        budget=shared,total_a_wall_including_cpu_review_seconds=time.time()-shared['started_epoch'],raw_real_decisions=total,raw_diagnostic_updates=updates,
        before_after_differences=differences,old_pid=reference['pid'],new_pid=resumed['pid'],
        original_start=capture['started_monotonic'],original_deadline=capture['deadline_monotonic'],mixed_boundary=save,
        gpu_update=gpu,performance=stats,
        simulation_attempted_seconds=attempted_steps*.05,simulation_committed_seconds=committed_steps*.05,
        timing_scope='CUDA-synchronized wall durations; no claim of CUDA-event kernel timings. Simulated row-seconds summed separately.',
        cuda_memory_scope='torch.cuda.max_memory_allocated; excludes context/driver and unused reserved cache',
        peak_rss_kib=max(a['rss_kib'],b['rss_kib']),peak_cuda_bytes=max(a['cuda_peak_bytes'],b['cuda_peak_bytes']),
        projection=dict(decisions=10000,updates=9000,seconds_per_decision=per_decision,
            update_mean_s=update_mean,update_p95_s=update_p95,checkpoint_count=len(checkpoint_decisions),
            checkpoint_growth_scaling='engineering linear retained-transition scaling, max(1,d/measured_d)',
            projected_checkpoint_s=scaled_saves,nominal_seconds=nominal,guarded_seconds=guarded,
            hard_limit_seconds=172800,supports_48h=guarded<=172800,
            formula='10000*measured_collection_s_per_decision + 9000*update_mean_or_p95 + sum_scaled_saves + initial_reset + lower_load + 120s_cleanup; guarded adds one linearly scaled restore',
            conditions='same batch8/thread2/GPU/data semantics; observed small-run scenario and sequence-length distribution. Not a completion guarantee; no automatic budget extension. Excludes arbitrary repeated failures/waiting; hard deadline still binds.'),
        limits=['one real mixed boundary and its next batch/update, not all possible interruptions',
            'diagnostic current-run replay only, never formal 1000-decision warmup',
            'all CPU/GPU wall profiling is measured; GPU memory metadata from actual worker'])
    atomic_json(output,result);print(json.dumps({k:result[k] for k in ('status','issues','raw_real_decisions','raw_diagnostic_updates','projection')}),flush=True)
    return 0 if not issues else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    return run(a.run,a.output)
if __name__=='__main__':raise SystemExit(main())
