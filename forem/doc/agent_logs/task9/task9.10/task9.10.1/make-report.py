"""Post-run read-only aggregation; no models, environments or network calls."""
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time

ROOT = Path('/home/ybc/projects/CL-FoReM-task9')
RUN = ROOT / 'forem/results/task9/t9.10-paired-20261103T144811+0800'
LOG = ROOT / 'forem/logs/task9' / RUN.name
REPORT = RUN / 'report'
sys.path.insert(0, str(ROOT / 'forem/scripts/task9_8'))
from analysis import compare, coverage, remaining, score


def read(path):
    return json.loads(path.read_text())


def dump(name, value):
    (REPORT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def percentile(values, q):
    if not values:
        return None
    x = sorted(values)
    position = (len(x) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    return x[lo] + (x[hi] - x[lo]) * (position - lo)


def summarize(values):
    return dict(count=len(values), sum_s=sum(values),
                p50_s=percentile(values, .5), p95_s=percentile(values, .95),
                p99_s=percentile(values, .99), max_s=max(values) if values else None)


def trace_metrics(events, row):
    checked = coverage(events, row)
    assert checked['complete'], checked
    scored = score(events, row)
    events = [record['comparison'] for record in events]
    first_index = next(i for i, event in enumerate(events)
                       if event['event'] == 'substep' and event['pending'] and event['failed'])
    first = events[first_index]
    baseline = remaining(first)
    same = []
    for event in events[first_index + 1:]:
        if event['event'] == 'begin' or event.get('segment', first['segment']) != first['segment']:
            break
        if event['event'] in ('substep', 'action_end'):
            same.append(event)
    last = same[-1] if same else first
    commits = [event for event in same if event['event'] == 'substep' and event['commit']]
    max_reduction = max([0.] + [baseline - remaining(event) for event in commits])
    dx = last['state']['base'][0] - first['state']['base'][0]
    dy = last['state']['base'][1] - first['state']['base'][1]
    return dict(classification=scored['classification'], complete=True,
                total_rejections=checked['counts']['rejections'],
                total_committed_substeps=checked['counts']['committed'],
                first_segment=first['segment'], first_action=first['action'], first_substep=first['substep'],
                baseline_remaining_m=baseline, full_same_segment_max_reduction_m=max_reduction,
                same_segment_net_reduction_m=baseline - remaining(last),
                same_segment_net_progress_s_m=last['state']['s'] - first['state']['s'],
                same_segment_net_xy_m=math.hypot(dx, dy),
                same_segment_arrived=any(event['arrived'] for event in same),
                same_segment_post_rejection_commits=len(commits),
                strict_success=row['strict_success'], final_failures=row['failures'],
                total_actions=row['transfers'], final_state=events[-1]['state'], original_evaluation_row=row)


def main():
    assert not REPORT.exists(), 'Never overwrite a prior report'
    state = read(LOG / 'supervisor-state.json')
    assert state['status'] == 'complete_pending_independent_review'
    assert state['started_episodes'] == 1176
    REPORT.mkdir()
    paired, strict, timings = [], [], []
    four = dict(retained_R=[], gained_R=[], lost_R=[], retained_N=[])
    non_target = []
    for seed in (4718, 4719, 4720):
        cdir, tdir = RUN / f'C-{seed}', RUN / f'T-{seed}'
        controls, treatments = read(cdir / 'case-reports.json'), read(tdir / 'case-reports.json')
        assert controls.keys() == treatments.keys()
        for case in controls:
            both = {}
            for arm, directory in [('C', cdir), ('T', tdir)]:
                events = [json.loads(line) for line in (directory / f'case{int(case):02d}.jsonl').open()]
                row = events[-1]['comparison']['outcome']
                actual = read(directory / 'case-reports.json')[case]
                metrics = trace_metrics(events, row)
                assert actual['score']['classification'] == metrics['classification']
                metrics.update(original_final_success=actual['original_finish']['success'],
                               final_stalls=actual['original_final_stalls'],
                               original_finish_raw=actual['original_finish'],
                               cbl_rotation_residual_dimensionless=actual['original_finish']['r_rad'])
                metrics['source_trace'] = str(directory / f'case{int(case):02d}.jsonl')
                if arm == 'T':
                    substitutions = [event['detail']['intervention'] for event in events
                                     if 'intervention' in event['detail']]
                    assert len(substitutions) == 1
                    intervention = substitutions[0]
                    assert intervention['rng_unchanged'] and intervention['rng_before'] == intervention['rng_after']
                    metrics.update(intervention=intervention, substitution_count=len(substitutions),
                                   action_changed=intervention['mean_action'] != intervention['replacement_action'],
                                   exact_prefix_events=actual['exact_prefix_events'],
                                   prefix_verified=actual['prefix_verified'], unavailable=actual['unavailable'])
                both[arm] = metrics
            identifier = f'{seed}/case{int(case):02d}'
            cr, tr = both['C']['classification'] == 'R', both['T']['classification'] == 'R'
            group = 'retained_R' if cr and tr else 'gained_R' if tr else 'lost_R' if cr else 'retained_N'
            four[group].append(identifier)
            paired.append(dict(id=identifier, training_seed=seed, case_no=int(case), transition=group,
                               target_row_first_difference=compare(both['C']['original_evaluation_row'], both['T']['original_evaluation_row']), **both))
        for arm, directory in [('C', cdir), ('T', tdir)]:
            evaluation = read(directory / 'evaluation.json')
            assert evaluation['complete']
            for split in ('validation', 'transfer'):
                rows = evaluation[split]['rows']
                strict.append(dict(arm=arm, training_seed=seed, split=split, episodes=len(rows),
                                   strict_success=sum(row['strict_success'] for row in rows)))
            status = read(directory / 'status.json')
            process = next(run for run in state['runs'] if run['arm'] == arm and run['seed'] == seed)
            stage = read(directory / 'timing.json')['samples']
            timings.append(dict(arm=arm, training_seed=seed, worker_internal_wall_s=status['wall_s'],
                                supervisor_process_wall_s=process['wall_s'],
                                original_evaluate_wall_s=evaluation['wall_s'],
                                stages={name:summarize(values) for name, values in stage.items()}))
        non_target.append(dict(training_seed=seed, **read(tdir / 'non-target-differences.json')))
    summary = dict(C_R=sum(row['C']['classification'] == 'R' for row in paired),
                   T_R=sum(row['T']['classification'] == 'R' for row in paired),
                   C_N=sum(row['C']['classification'] == 'N' for row in paired),
                   T_N=sum(row['T']['classification'] == 'N' for row in paired),
                   C_U=sum(row['C']['classification'] == 'U' for row in paired),
                   T_U=sum(row['T']['classification'] == 'U' for row in paired), denominator=12,
                   C_original_final_success=sum(row['C']['original_final_success'] for row in paired),
                   T_original_final_success=sum(row['T']['original_final_success'] for row in paired),
                   all_once=all(row['T']['substitution_count'] == 1 for row in paired),
                   all_actions_changed=all(row['T']['action_changed'] for row in paired),
                   all_prefix_verified=all(row['T']['prefix_verified'] for row in paired),
                   all_available=all(row['T']['unavailable'] is None for row in paired),
                   transition_groups=four)
    assert len(paired) == 12
    dump('paired-cases.json', dict(summary=summary, cases=paired,
         unit_correction='raw original_finish.r_rad is dimensionless CBL rotation residual 1-(qa dot qb)^2; not radians',
         scope='12 fixed development diagnostic model-case pairs; no population significance or deployment claim'))
    with (REPORT / 'paired-cases.csv').open('w') as f:
        fields = ['id','training_seed','case_no','transition','C_RNU','T_RNU','C_success','T_success',
                  'C_strict','T_strict','C_rejections','T_rejections','C_commits','T_commits',
                  'C_max_reduction_m','T_max_reduction_m','C_net_reduction_m','T_net_reduction_m',
                  'C_net_progress_s_m','T_net_progress_s_m','T_action_changed','T_substitution_action']
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for row in paired:
            writer.writerow(dict(id=row['id'],training_seed=row['training_seed'],case_no=row['case_no'],transition=row['transition'],
                C_RNU=row['C']['classification'],T_RNU=row['T']['classification'],
                C_success=row['C']['original_final_success'],T_success=row['T']['original_final_success'],
                C_strict=row['C']['strict_success'],T_strict=row['T']['strict_success'],
                C_rejections=row['C']['total_rejections'],T_rejections=row['T']['total_rejections'],
                C_commits=row['C']['total_committed_substeps'],T_commits=row['T']['total_committed_substeps'],
                C_max_reduction_m=row['C']['full_same_segment_max_reduction_m'],T_max_reduction_m=row['T']['full_same_segment_max_reduction_m'],
                C_net_reduction_m=row['C']['same_segment_net_reduction_m'],T_net_reduction_m=row['T']['same_segment_net_reduction_m'],
                C_net_progress_s_m=row['C']['same_segment_net_progress_s_m'],T_net_progress_s_m=row['T']['same_segment_net_progress_s_m'],
                T_action_changed=row['T']['action_changed'],T_substitution_action=row['T']['intervention']['action']))
    dump('strict-success.json', dict(rows=strict, independent_test=False,
         reason='Existing analyzed development validation and semantic transfer pools; 1176 is repeated evaluation budget, not independent task sample count'))
    dump('non-target-differences.json', dict(rows=non_target, total_different_rows=sum(len(row['differences']) for row in non_target)))
    dump('timings.json', dict(rows=timings, quantile_method='linear interpolation at q*(n-1), sorted host perf_counter samples',
         nesting='core_step_s includes emit_s; reset_s includes write-ahead logging; totals are not additive; sample_s excludes pre-snapshot overhead; no isolated save timer',
         synchronization='actor host timer synchronizes CUDA before and after every call; diagnostic cost only, not production throughput evidence'))
    cfg = read(RUN / 'run.json')
    monitor = [json.loads(line) for line in (LOG / 'monitor.jsonl').open()]
    memory = []
    active = 0
    for sample in monitor:
        lines = [line for line in sample['gpu'].splitlines() if cfg['gpu_uuid'] in line]
        active += bool(lines)
        for line in lines:
            match = re.search(r'(\d+) MiB\s*$', line)
            if match: memory.append(int(match.group(1)))
    pre_bytes = sum(path.stat().st_size for root in (RUN,LOG) for path in root.rglob('*') if path.is_file())
    dump('resources.json', dict(gpu_uuid=cfg['gpu_uuid'], gpu_allocation_start_epoch=cfg['gpu_allocation_start_epoch'],
         gpu_resource_window_s=state['gpu_resource_window_s'], supervisor_start_epoch=state['start_epoch'],
         cleanup_end_epoch=state['end_epoch'], preparation_start_epoch=cfg['start_epoch'],
         total_prepare_through_cleanup_wall_s=state['end_epoch']-cfg['start_epoch'],
         worker_process_wall_sum_s=sum(run['wall_s'] for run in state['runs']),
         started_episodes=state['started_episodes'], completed_episodes=sum(read(RUN/f'{arm}-{seed}'/'status.json')['completed_episodes'] for arm,seed in [('C',4718),('C',4719),('C',4720),('T',4718),('T',4719),('T',4720)]),
         output_log_bytes_before_final_report_manifest=pre_bytes, external_charge_reserve_bytes=cfg['external_charge_reserve_bytes'],
         max_episodes=cfg['max_episodes'],max_gpu_seconds=cfg['max_gpu_seconds'],max_output_bytes=cfg['max_output_bytes'],
         deadline_epoch=cfg['deadline_epoch'], deadline_met=state['end_epoch'] < cfg['deadline_epoch'],
         monitor_samples=len(monitor),samples_with_selected_gpu_compute_process=active,
         compute_process_memory_mib_min=min(memory) if memory else None,
         compute_process_memory_mib_max=max(memory) if memory else None,
         GPU_utilization_percent='not sampled; process/memory occupancy and reserved single-GPU window only',
         cleanup=read(RUN/'cleanup.json'), final_external_accounting='see task9.10.3 final audit; this pre-final byte count excludes later report and shared-doc writes'))
    source = []
    for record in read(RUN / 'source-inventory.json'):
        actual, snapshot = digest(Path(record['path'])), digest(Path(record['snapshot']))
        source.append(dict(**record, actual_sha256_after=actual, snapshot_sha256_after=snapshot,
                           match=actual == snapshot == record['sha256']))
    assert all(record['match'] for record in source)
    dependencies = set()
    blocked_path = ROOT/'forem/results/task9/t9.9-offline-20261102-repeat/blocked-cases-12.csv'
    frozen_path = ROOT/'forem/doc/agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.csv'
    dependencies.update([blocked_path,frozen_path])
    for row in csv.DictReader(blocked_path.open()):
        dependencies.add(Path(row['source']))
    for seed,name in [(4718,'03-4718-remaining'),(4719,'04-4719-all'),(4720,'05-4720-all')]:
        dependencies.add(ROOT/'forem/results/task9'/cfg['baseline_run_id']/name/'evaluation.json')
    dump('hash-closeout.json', dict(source_inventory_sha256=digest(RUN/'source-inventory.json'),sources=source,
         observer_inputs=[dict(path=str(path),bytes=path.stat().st_size,sha256=digest(path)) for path in sorted(dependencies)],
         input_admission=read(RUN/'input-admission.json'),
         final_large_model_note='Opening complete hashes plus read-only mounts; closing large-model stat stability and small-dependency hashes are independently recorded by task9.10.3. Do not describe large closing files as rehashed.'))
    hashes = [dict(path=str(path),bytes=path.stat().st_size,sha256=digest(path)) for path in REPORT.iterdir() if path.is_file()]
    dump('manifest.json',dict(created_epoch=time.time(),files=hashes,aggregation_script=str(Path(__file__).resolve()),
                             aggregation_script_sha256=digest(Path(__file__))))
    print(json.dumps(summary,ensure_ascii=False))


if __name__ == '__main__':
    main()
