#!/usr/bin/env python3
"""Compact, reproducible read-only aggregation of the three task10.8 runs."""
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(root, verify_raw=False):
    runs = []
    for tag in ('gpu-default', 'gpu-deterministic', 'gpu-default-repeat'):
        folder = root/tag
        source = folder/'diagnosis.json'
        value = json.loads(source.read_text())
        controls = []
        for c in value['controls']:
            raw_path = folder/(c['name']+'.pt')
            if verify_raw:
                import torch
                torch.set_num_threads(2)
                from task10.gpu_diagnosis import compare_tree
                raw = torch.load(raw_path, map_location='cpu', weights_only=False)
                rebuilt = dict(pre_state=compare_tree(raw['pre_left'], raw['pre_right']),
                               sample=compare_tree(raw['sample_left'], raw['sample_right']))
                for k in ('losses', 'gradients_preclip', 'gradients_postclip', 'state', 'adam_by_parameter', 'rng_after', 'sample_rng_after'):
                    rebuilt['post_state' if k == 'state' else k] = compare_tree(raw['left'][k], raw['right'][k])
                if rebuilt != c['comparisons']:
                    raise AssertionError(f'{tag}/{c["name"]}: raw recomputation differs')
            stages = {}
            for key, cmp in c['comparisons'].items():
                finite_differences = [v for v in cmp['differences'] if v.get('max_abs') is not None]
                largest = max(finite_differences, key=lambda v: v['max_abs'], default=None)
                stages[key] = dict(exact=cmp['exact'], tensor_leaves=len(cmp['tensor_leaves']),
                                   differing_leaves=len(cmp['differences']), first_difference=cmp['first_difference'],
                                   largest_difference=largest)
            controls.append(dict(name=c['name'], exact=c['exact'], first_difference=c['first_difference'],
                                 stages=stages, losses=c['losses'], update_seconds=c['update_seconds'],
                                 setup_save_load_seconds=c['setup_save_load_seconds'],
                                 raw_path=str(raw_path), raw_sha256=sha256(raw_path)))
        times = [x for c in controls for x in c['update_seconds']]
        runs.append(dict(run=tag, status=value['status'], fixture_update_calls=value['fixture_update_calls'],
                         new_real_decisions=value['new_real_decisions'], controls=controls,
                         source_json=str(source), source_sha256=sha256(source), input_sha256=value['input_sha256'],
                         measured_module_sha256=value['module_sha256'], measured_script_sha256=value['script_sha256'],
                         settings=value['settings'], cublas_workspace_config=value['cublas_workspace_config'],
                         model_device=value['model_device'], optimizer_devices=value['optimizer_devices'],
                         total_process_seconds=value['total_wall_seconds'], controls_wall_seconds=value['wall_seconds'],
                         first_update_in_fresh_process_seconds=times[0], subsequent_update_seconds=times[1:],
                         sum_update_seconds=sum(times)))
    if len({r['input_sha256'] for r in runs}) != 1 or len({r['measured_module_sha256'] for r in runs}) != 1 or len({r['measured_script_sha256'] for r in runs}) != 1:
        raise AssertionError('the three measurements did not share one fixture/code version')
    calls = sum(r['fixture_update_calls'] for r in runs)
    if calls != 12 or sum(r['new_real_decisions'] for r in runs) != 0:
        raise AssertionError('unexpected update/real decision accounting')
    return dict(kind='task10.8 compact same-memory control analysis', runs=runs,
                fixture_update_calls=calls, new_real_decisions=0,
                source_and_measured_code_identical=True, raw_recomputed=verify_raw,
                report_script_sha256=sha256(__file__),
                conclusions=dict(default_and_repeat_exact=all(c['exact'] for i in (0, 2) for c in runs[i]['controls']),
                    deterministic_fixture_both_controls_exact=all(c['exact'] for c in runs[1]['controls']),
                    observed_first_divergence='CNN parameter gradients captured before clipping',
                    save_load_not_necessary_for_divergence=all(not runs[i]['controls'][0]['exact'] for i in (0, 2)),
                    specific_cuda_kernel_cause='not identified',
                    limitations='One old derived fixture, 40 loss positions per update, three fresh processes. Deterministic settings are a bundled diagnostic intervention. No new real decisions, full training or online update throughput validation. First path is stage/key order, not kernel execution order. Timings include gradient hooks; fresh first update is retained. Default next-update acceptance remains failed.'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--verify-raw', action='store_true')
    args = p.parse_args()
    value = build(args.root, args.verify_raw)
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    print('controls', sum(len(r['controls']) for r in value['runs']), 'updates', value['fixture_update_calls'], 'raw_recomputed', value['raw_recomputed'])

if __name__ == '__main__':
    main()
