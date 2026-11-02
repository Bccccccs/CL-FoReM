#!/usr/bin/env python3
"""Rebuild two old batches, compare to journals, then profile same episodes.

One invocation only: <=32 newly executed rows, <=900 wall seconds, no training.
"""
import argparse
import copy
from contextlib import nullcontext
import json
from pathlib import Path
import signal
import time
import traceback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--old-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=900)
    parser.add_argument('--baseline-batches', type=int, default=2)
    parser.add_argument('--profile-batches', type=int, default=2)
    parser.add_argument('--max-decisions', type=int, default=32)
    args = parser.parse_args()
    from task10.profiling import validate_batch_budget
    try:
        validate_batch_budget(args.baseline_batches, args.profile_batches, args.max_decisions)
    except ValueError as exc:
        parser.error(str(exc))
    if not 0 < args.seconds <= 900:
        parser.error('seconds must be in (0, 900]')
    if args.output.exists():
        raise RuntimeError('output exists; automatic restart prohibited')
    started = time.monotonic()
    deadline = started + args.seconds
    def alarm(*_): raise TimeoutError('probe deadline')
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    import torch
    from task10.runtime import atomic_json
    from task10.runner import initialize
    from task10.lower import FrozenB3
    from task10.environment import Task10Env
    from task10.profiling import Profiler, patch_methods, comparison_snapshot, snapshot_digest
    from task7_upper.replay import exact_cpu
    from task7_sim.core import Core
    from task7_sim.kinematics import Kinematics
    from task7_sim.perception import Grid, LocalCollision
    from task8_sim.env import PcdEpisodeEnv
    from task8_sim.episode import PcdEpisodeSampler, SceneCollision
    from task8_sim.routes import PcdTruthPlanner
    from task7_sim import candidates, risk
    from task10 import environment
    torch.set_num_threads(2)
    result = dict(status='active', max_seconds=args.seconds, max_decisions=args.max_decisions, baseline_batches=args.baseline_batches, profile_batches=args.profile_batches,
                  reserved=0, completed=0, passes=[], error=None,
                  gpu_event_note='inclusive CUDA stream intervals may include CPU submission gaps; not kernel compute; never add to wall or nested intervals',
                  comparison_excluded_paths=['candidates.diagnostics.search_wall_seconds'])
    atomic_json(args.output, result)
    def flush():
        result['wall_seconds'] = time.monotonic()-started
        atomic_json(args.output, result)
    def compare(a, b, path):
        if isinstance(a, torch.Tensor):
            if not isinstance(b, torch.Tensor) or a.shape != b.shape or a.dtype != b.dtype or not torch.equal(a.cpu(), b.cpu()):
                raise AssertionError('mismatch: '+path)
        elif isinstance(a, dict):
            if not isinstance(b, dict) or a.keys() != b.keys(): raise AssertionError('keys mismatch: '+path)
            for key in a: compare(a[key], b[key], path+'.'+str(key))
        elif isinstance(a, (tuple, list)):
            if not isinstance(b, (tuple, list)) or len(a) != len(b): raise AssertionError('length mismatch: '+path)
            for i, (x, y) in enumerate(zip(a,b)): compare(x,y,path+f'[{i}]')
        elif a != b: raise AssertionError('value mismatch: '+path)
    try:
        journals = [torch.load(args.old_run/f'real-executions/batch-{n:06}.pt', map_location='cpu', weights_only=False)['fields'] for n in (8,16)]
        log = [json.loads(line) for line in (args.old_run/'real-executions.jsonl').read_text().splitlines()]
        if len(log) != 2: raise ValueError('expected exactly two old batches')
        initialize(101)
        policy = FrozenB3(device='cuda:0', artifact_root='/reference', source_root='/reference/source')
        episodes = {i: [] for i in range(8)}
        baseline = []
        boundary_baseline = []
        for instrumented in (False, True):
            initialize(101)
            env = Task10Env(8, policy, seed=101, pool='/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json', split='train', device='cuda:0', risk_chunk_size=256, observation_chunk_size=128, reuse_route_raster=True)
            env.episodes.kin.dls_cuda_graph = True
            sampler = env.episodes.sampler
            if not instrumented:
                def factory(i, rng):
                    episode = sampler.sample(rng, deadline=deadline)
                    episodes[i].append(copy.deepcopy(episode))
                    return episode
            else:
                offsets = [0]*8
                def factory(i, rng):
                    episode = copy.deepcopy(episodes[i][offsets[i]])
                    offsets[i] += 1
                    return episode
            env.episodes.factory = factory
            profiler = Profiler(cuda=instrumented)
            targets = [(PcdEpisodeEnv,'reset','reset_sampling_and_setup'), (PcdEpisodeSampler,'sample','sampling'),
                (PcdTruthPlanner,'plan','planning'), (candidates,'generate_candidates','candidate_generation','candidate_generation'),
                (environment,'predict_candidates','prediction','prediction'), (type(policy),'__call__','b3_inference'),
                (Kinematics,'solve_world','ik'), (LocalCollision,'__call__','local_collision'),
                (SceneCollision,'__call__','scene_collision'), (Grid,'crop','grid_crop'),
                (Grid,'update','grid_update'), (Core,'observe','observe'), (risk,'sweep_metrics','risk'),
                (Task10Env,'_boundary','boundary'), (Task10Env,'step','actual_execution')]
            boundaries = []
            def boundary(*a, **kw):
                obs, cand, timing = Task10Env._boundary(env, *a, **kw)
                snapshot = comparison_snapshot(dict(observation=obs, candidates=cand), exact_cpu)
                index = len(boundaries)
                digest = snapshot_digest(snapshot)
                compared = False
                if instrumented:
                    if index >= len(boundary_baseline):
                        raise AssertionError('instrumented boundary exceeds baseline coverage')
                    compare(boundary_baseline[index], snapshot, f'baseline.boundary{index}')
                    compared = True
                else:
                    boundary_baseline.append(snapshot)
                boundaries.append(dict(timing=copy.deepcopy(timing), compared=compared, sha256=digest))
                return obs,cand,timing
            env._boundary = boundary
            record = dict(instrumented=instrumented, boundaries=boundaries, batches=[])
            result['passes'].append(record)
            record['business_wall_s'] = {}
            pass_started = time.monotonic()
            def call(stage, function, *a, **kw):
                started_call = time.perf_counter()
                try:
                    with profiler.phase(stage):
                        return function(*a, **kw)
                finally:
                    elapsed = time.perf_counter() - started_call
                    record['business_wall_s'][stage] = record['business_wall_s'].get(stage, 0.) + elapsed
            with patch_methods(profiler, targets) if instrumented else nullcontext():
                call('reset', env.reset, deadline=deadline)
                for j in range(args.profile_batches if instrumented else args.baseline_batches):
                    selected = torch.tensor(log[j]['selected'], device='cuda:0', dtype=torch.long)
                    if result['reserved'] + 8 > args.max_decisions:
                        raise RuntimeError('probe decision budget exceeded')
                    result['reserved'] += 8
                    flush()
                    step = call('actual', env.step, selected, deadline=deadline)
                    result['completed'] += 8
                    fields = step.replay_fields
                    keys = ('observation','candidates','selected','selected_prediction','actual_result_v1',
                            'r_t','attempted_substeps','committed_substeps','terminated','truncated','triggers')
                    expected = comparison_snapshot({key: journals[j][key] for key in keys}, exact_cpu)
                    snapshot = comparison_snapshot({key: fields[key] for key in keys}, exact_cpu)
                    compare(expected, snapshot, f'old.batch{j}')
                    if not instrumented: baseline.append(snapshot)
                    else: compare(baseline[j], snapshot, f'baseline.batch{j}')
                    record['batches'].append(dict(old_equal=True, selected=log[j]['selected'],
                        actual_attempted=int(fields['attempted_substeps'].sum()), actual_committed=int(fields['committed_substeps'].sum()),
                        execution_b3_calls=step.info['timing']['execution_b3_calls'], execution_b3_row_calls=step.info['timing']['execution_b3_row_calls']))
                    ended = step.terminated | step.truncated
                    call('prepare', env.prepare_next, step, deadline=deadline)
                    if ended.any(): call('reset', env.reset, indices=torch.where(ended)[0].tolist(), deadline=deadline)
                    flush()
            record['pass_wall_s'] = time.monotonic() - pass_started
            if instrumented: record['timings'] = profiler.report()
            record['sample_stats'] = dict(sampler.stats)
            record['sample_timing'] = dict(sampler.timing)
            flush()
        result['boundary_coverage'] = dict(baseline=len(boundary_baseline), instrumented=len(result['passes'][1]['boundaries']), compared=sum(x['compared'] for x in result['passes'][1]['boundaries']))
        result['status'] = 'complete'
    except BaseException as exc:
        result['status'] = 'failed'
        if result['passes'] and 'pass_started' in locals() and 'pass_wall_s' not in result['passes'][-1]:
            result['passes'][-1]['pass_wall_s'] = time.monotonic() - pass_started
        result['error'] = repr(exc)
        traceback.print_exc()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        flush()
    return 0 if result['status'] == 'complete' else 1

if __name__ == '__main__': raise SystemExit(main())
