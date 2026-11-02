#!/usr/bin/env python3
"""Bounded first-boundary verification: <=8 scenes, <=104 slots, no decisions."""
import argparse
from pathlib import Path
import signal
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise RuntimeError('verification output exists')
    started = time.monotonic()
    deadline = started+220
    def stop(*_):
        raise TimeoutError('220s verification work limit; 20s reserved for report')
    signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, 220)
    import torch
    from task10.runner import initialize
    from task10.runtime import atomic_json, sha256
    from task10.lower import FrozenB3
    from task10.environment import Task10Env
    from task10 import environment
    from task10.profiling import Profiler, patch_methods, comparison_snapshot, snapshot_digest
    from task10.recovery import tree_equal
    from task7_upper.replay import exact_cpu
    from task7_sim.core import Core
    from task7_sim.kinematics import Kinematics
    from task7_sim.perception import Grid, LocalCollision
    from task7_sim import candidates, risk
    from task8_sim.env import PcdEpisodeEnv
    from task8_sim.episode import PcdEpisodeSampler, SceneCollision
    from task8_sim.routes import PcdTruthPlanner
    initialize(101)
    profiler = Profiler(cuda=True)
    result = dict(status='active', new_real_decisions=0, updates=0, max_scenes=8,
                  max_slots=104, max_proposals=256, wall_limit_seconds=240)
    try:
        old = torch.load(args.source, map_location='cpu', weights_only=False)['fields']
        policy = FrozenB3(device='cuda:0', artifact_root='/reference', source_root='/reference/source')
        env = Task10Env(8, policy, seed=101,
            pool='/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json',
            split='train', device='cuda:0', risk_chunk_size=256,
            observation_chunk_size=128, reuse_route_raster=True)
        env.episodes.kin.dls_cuda_graph = True
        env.episodes.sampling_cancel = lambda: env.episodes.sampler.stats['proposals'] >= 256
        targets = [(Task10Env, 'reset', 'reset', 'reset'),
            (PcdEpisodeEnv, 'reset', 'episode_reset'), (PcdEpisodeSampler, 'sample', 'sampling'),
            (PcdTruthPlanner, 'plan', 'planning'), (Task10Env, '_boundary', 'boundary'),
            (candidates, 'generate_candidates', 'candidate_generation', 'candidate_generation'),
            (environment, 'predict_candidates', 'prediction', 'prediction'),
            (type(policy), '__call__', 'b3_inference'), (Kinematics, 'solve_world', 'ik'),
            (LocalCollision, '__call__', 'local_collision'), (SceneCollision, '__call__', 'scene_collision'),
            (Grid, 'crop', 'grid_crop'), (Grid, 'update', 'grid_update'),
            (Core, 'observe', 'observe'), (risk, 'sweep_metrics', 'risk')]
        torch.cuda.synchronize()
        work_started = time.monotonic()
        with patch_methods(profiler, targets):
            obs, cand = env.reset(deadline=deadline)
        torch.cuda.synchronize()
        result['reset_service_wall_seconds'] = time.monotonic()-work_started
        expected = comparison_snapshot(dict(observation=old['observation'], candidates=old['candidates']), exact_cpu)
        actual = comparison_snapshot(dict(observation=obs, candidates=cand), exact_cpu)
        if not tree_equal(expected, actual):
            raise AssertionError('first boundary differs from real journal')
        result.update(status='verified', compared_to_old=True,
                      boundary_sha256=snapshot_digest(actual), source_sha256=sha256(args.source),
                      boundary_counts=env.last_timing, sampler_stats=env.episodes.sampler.stats,
                      sampler_timing=env.episodes.sampler.timing,
                      map_ids=list(env.episodes.map_ids),
                      ignored_paths=['candidates.diagnostics.search_wall_seconds'])
    except BaseException as exc:
        result.update(status='failed', error=repr(exc))
        import traceback
        traceback.print_exc()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        result['timing'] = profiler.report()
        result['wall_seconds'] = time.monotonic()-started
        result['gpu_timing_note'] = 'nested inclusive CUDA stream intervals include CPU submission gaps; not kernel compute'
        atomic_json(args.output, result)
    return 0 if result['status'] == 'verified' else 1


if __name__ == '__main__':
    raise SystemExit(main())
