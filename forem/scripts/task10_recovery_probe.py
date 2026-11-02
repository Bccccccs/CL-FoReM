#!/usr/bin/env python3
"""Bounded recovery probes: offline derived fixture or explicit new online namespace."""
import argparse
from pathlib import Path
import os
from copy import deepcopy
import time
import torch
from task7_upper.model import UpperModel
from task7_upper.stages import load_checkpoint
from task10.learning import EpisodeReplay, Stage1Learner, ReplayAdapter
from task10.recovery import verify_learner_checkpoint, derived_replay, fixture_update
from task10.runtime import atomic_json, sha256


def offline_fixture(args):
    if not 1 <= args.fixture_updates <= 6:
        raise ValueError('fixture updates plus two verification branches must be <=8')
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    started = time.monotonic()
    device = torch.device(args.device)
    if device.type == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA fixture requires GPU; no fallback')
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    source = torch.load(args.source, map_location='cpu', weights_only=False)
    counters, config = source['counters'], source['config']
    factory = lambda: Stage1Learner(UpperModel(vector_dim=counters['vector_dim']).to(device),
                                  source['learner']['total_updates'])
    learner = factory()
    replay = EpisodeReplay(capacity=source['replay']['capacity'])
    load_checkpoint(args.source, learner, replay, config=config)
    real_count = len(replay)
    nonempty = verify_learner_checkpoint(args.output/'real-replay-check.pt', learner, replay,
        config, counters, learner_factory=factory)
    derived = derived_replay(replay)
    adapter = ReplayAdapter(False, device)
    updates = []
    update_seconds = []
    if device.type == 'cuda':
        torch.cuda.reset_peak_memory_stats(device)
    def measured_update(l, r):
        if device.type == 'cuda':
            torch.cuda.synchronize(device)
        before = time.monotonic()
        value = fixture_update(l, r, adapter)
        if device.type == 'cuda':
            torch.cuda.synchronize(device)
        update_seconds.append(time.monotonic()-before)
        return value
    for _ in range(args.fixture_updates):
        if time.monotonic()-started > 280:
            raise TimeoutError('fixture cleanup reserve reached')
        updates.append(measured_update(learner, derived))
    fixture_counters = dict(counters, updates=learner.updates,
                            evidence_kind='derived-replay-fixture', real_decisions=real_count)
    evidence = verify_learner_checkpoint(args.output/'derived-fixture.pt', learner, derived,
        dict(config, evidence_kind='derived-replay-fixture'), fixture_counters,
        learner_factory=factory, next_update=measured_update)
    if device.type == 'cuda':
        torch.cuda.synchronize(device)
    result = dict(status='verified', source=str(args.source), source_sha256=sha256(args.source),
        kind='offline derived replay fixture; not online training or warmup',
        probe_code_commit=os.environ.get('TASK10_CODE_COMMIT', 'unknown'),
        probe_sha256=sha256(__file__),
        recovery_sha256=sha256(Path(__file__).resolve().parents[1]/'src/task10/recovery.py'),
        source_real_decisions=real_count, new_real_decisions=0,
        online_warmup_complete=False, real_replay_evidence=nonempty,
        derived_anchors=len(derived), fixture_update_calls=args.fixture_updates+2,
        fixture_updates=updates, recovery=evidence, wall_seconds=time.monotonic()-started,
        update_wall_seconds=update_seconds,
        gradient_report=__import__('task10.runner', fromlist=['gradients']).gradients(learner.model),
        peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(device) if device.type == 'cuda' else None,
        model_device=str(next(learner.model.parameters()).device),
        optimizer_devices=sorted({str(v.device) for s in learner.optimizer.state.values()
                                  for v in s.values() if isinstance(v, torch.Tensor)}))
    atomic_json(args.output/'summary.json', result)
    print(result['status'], result['wall_seconds'], flush=True)




def diagnose_existing_fixture(args):
    """Exactly two next-update branches from the already updated saved fixture."""
    from task10.recovery import mismatch_report, tree_equal, fragment_identity
    from task7_lower.training import rng_state
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    if args.deterministic:
        if os.environ.get('CUBLAS_WORKSPACE_CONFIG') not in (':4096:8', ':16:8'):
            raise ValueError('set CUBLAS_WORKSPACE_CONFIG before importing torch for deterministic diagnostic')
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic = True
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    payload = torch.load(args.diagnose_checkpoint, map_location='cpu', weights_only=False)
    if payload['learner']['updates'] < 1 or not payload['learner']['optimizer']['state']:
        raise ValueError('diagnostic needs an already updated optimizer fixture')
    if not str(payload['config'].get('evidence_kind', '')).startswith('derived-replay-fixture'):
        raise ValueError('diagnostic accepts only explicitly derived fixture checkpoint')
    factory = lambda: Stage1Learner(UpperModel(vector_dim=payload['counters']['vector_dim']).to(args.device),
                                  payload['learner']['total_updates'])
    learners = [factory(), factory()]
    replays = [EpisodeReplay(capacity=payload['replay']['capacity']) for _ in range(2)]
    adapter = ReplayAdapter(False, args.device)
    states, reports, rngs, identities, initial_states = [], [], [], [], []
    for learner, replay in zip(learners, replays):
        load_checkpoint(args.diagnose_checkpoint, learner, replay, config=payload['config'])
        initial_states.append(deepcopy(learner.state_dict()))
        # Inspect the same next sample without consuming its replay RNG.
        rs = replay.state_dict()
        identities.append(fragment_identity(replay.sample(32)))
        replay.load_state_dict(rs)
        rngs.append(rng_state())
        reports.append(fixture_update(learner, replay, adapter))
        torch.cuda.synchronize()
        states.append(deepcopy(learner.state_dict()))
    differences = dict(initial=mismatch_report(initial_states[0], initial_states[1]),
        sample=mismatch_report(identities[0], identities[1]), rng=mismatch_report(rngs[0], rngs[1]),
        losses=mismatch_report(reports[0], reports[1]), state=mismatch_report(states[0], states[1]))
    exact = all(not v for v in differences.values())
    atomic_json(args.output/'diagnosis.json', dict(status='verified' if exact else 'exact_mismatch',
        kind='two-branch next-update diagnostic from existing derived fixture',
        new_real_decisions=0, fixture_update_calls=2, online_warmup_complete=False,
        input_sha256=sha256(args.diagnose_checkpoint), deterministic_algorithms=args.deterministic,
        cublas_workspace_config=os.environ.get('CUBLAS_WORKSPACE_CONFIG'),
        cudnn_deterministic=torch.backends.cudnn.deterministic, losses=reports,
        differences=differences, wall_seconds=time.monotonic()-started,
        probe_sha256=sha256(__file__),
        recovery_sha256=sha256(Path(__file__).resolve().parents[1]/'src/task10/recovery.py')))
    print('exact_next_update', exact, 'differing_leaves', {k:len(v) for k,v in differences.items()}, flush=True)


def online_snapshot(env):
    from task10.runtime import state_digest
    from task7_upper.replay import exact_cpu
    from task7_lower.training import rng_state
    from task10.recovery import _streams_state
    return dict(digest=state_digest(env), observation=exact_cpu(env.observation),
        candidates=exact_cpu({k: env.candidates[k] for k in ('c_k','mask','f_k','inplace','world_pose')}),
        episode_count=env.episodes.episode_count.cpu().clone(),
        proposal_seeds=env.episodes.proposal_seeds.copy(),
        sampler_streams=_streams_state(env.episodes), rng=rng_state())


def online_boundary(args):
    """One child collector phase; all phases share the first absolute deadline."""
    from task10.lower import FrozenB3
    from task10.environment import Task10Env
    from task10.runtime import Budget, atomic_torch
    from task10.recovery import save_episode_boundary, load_episode_boundary, tree_equal
    from task7_upper.replay import exact_cpu, row
    if not 1 <= args.online_decisions <= 4:
        raise ValueError('online boundary probe permits at most four decisions')
    args.output.mkdir(parents=True, exist_ok=bool(args.resume))
    started = args.online_started_monotonic or time.monotonic()
    torch.set_num_threads(2)
    torch.manual_seed(101)
    device = torch.device(args.device)
    if device.type != 'cuda' or not torch.cuda.is_available():
        raise RuntimeError('online boundary requires authorized GPU runtime')
    source = torch.load(args.source, map_location='cpu', weights_only=False)
    config = dict(source['config'], evidence_kind='bounded-online-natural-boundary',
        run_id=args.output.name, code_commit=os.environ.get('TASK10_CODE_COMMIT', 'unknown'),
        probe_sha256=sha256(__file__),
        recovery_sha256=sha256(Path(__file__).resolve().parents[1]/'src/task10/recovery.py'))
    if not args.resume:
        cpu_factory = lambda: Stage1Learner(UpperModel(vector_dim=source['counters']['vector_dim']),
                                          source['learner']['total_updates'])
        cpu_learner, cpu_replay = cpu_factory(), EpisodeReplay(capacity=source['replay']['capacity'])
        load_checkpoint(args.source, cpu_learner, cpu_replay, config=source['config'])
        real_evidence = verify_learner_checkpoint(args.output/'real-replay-evidence.pt', cpu_learner,
            cpu_replay, source['config'], source['counters'], learner_factory=cpu_factory)
        atomic_json(args.output/'real-replay-evidence.json', real_evidence)
    learner = Stage1Learner(UpperModel(vector_dim=source['counters']['vector_dim']).to(device),
                            source['learner']['total_updates'])
    learner.load_state_dict(source['learner'])
    if learner.updates:
        raise ValueError('bounded online collector fixture expects zero-update source actor')
    replay = EpisodeReplay(seed=101)
    policy = FrozenB3(device=device, artifact_root='/reference', source_root='/reference/source')
    pool = '/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json'
    def factory():
        e = Task10Env(1, policy, seed=101, pool=pool, split='train', device=device,
            run_id=args.output.name, code_commit=config['code_commit'],
            config_hash=source['config'].get('config_sha256', 'unknown'),
            risk_chunk_size=256, observation_chunk_size=128, reuse_route_raster=True)
        e.episodes.kin.dls_cuda_graph = True
        return e
    counters = dict(decisions=0, updates=0)
    budget = Budget(args.output/'online-budget.json', started=started, seconds=360,
                    decisions=args.online_decisions, updates=0) if not args.resume else None
    boundary_report, post_resume_commits = None, 0
    status, error, journals, saved_clean = 'not_verified', None, [], False
    expected = None
    try:
        if args.resume:
            bundle = load_episode_boundary(args.resume, learner, replay,
                                           environment_factory=factory, config=config)
            env, generator, budget, counters = (bundle[k] for k in
                ('environment', 'policy_generator', 'budget', 'counters'))
            if args.expected_reference:
                expected = torch.load(args.expected_reference, map_location='cpu', weights_only=False)
                if expected['collector_pid'] == os.getpid():
                    raise AssertionError('expected collector process to exit before resume')
                actual = online_snapshot(env)
                if not tree_equal(expected['snapshot'], actual) or not torch.equal(expected['generator_state'], generator.get_state().cpu()):
                    raise AssertionError('cross-process next episode differs from uninterrupted reset')
                boundary_report = dict(next_scene_observation_candidates_rng_exact=True,
                    policy_generator_exact=True, initial_digest=actual['digest'],
                    old_collector_pid=expected['collector_pid'], new_collector_pid=os.getpid())
        else:
            env, generator = factory(), torch.Generator(device=device).manual_seed(101)
            env.reset(deadline=budget.deadline)
        while budget.state['reserved_decisions'] < budget.state['max_decisions']:
            budget.check()
            probability = env.candidates['mask'].float()
            selected = torch.multinomial(probability/probability.sum(-1, keepdim=True), 1,
                                         generator=generator).squeeze(-1)
            if args.resume and expected is not None and not torch.equal(selected.cpu(), expected['selected']):
                raise AssertionError('cross-process selected slot differs')
            budget.reserve(1)
            result = env.step(selected, deadline=budget.deadline)
            journal = args.output/'real-executions'/f"batch-{budget.state['reserved_decisions']:06d}.pt"
            atomic_torch(journal, dict(reserved_through=budget.state['reserved_decisions'],
                fields=exact_cpu(result.replay_fields), next_boundary_ready=False))
            journals.append(journal)
            budget.complete(1)
            result = env.prepare_next(result, deadline=budget.deadline)
            fields = result.replay_fields
            replay.append((env.run_id, 0, int(fields['episode_id'][0])), row(fields, 0, 1))
            counters['decisions'] = budget.state['completed_decisions']
            atomic_torch(args.output/'replay-progress.pt', replay.state_dict())
            if args.resume:
                post_resume_commits += 1
                # Collection phase ends here; relinquish ownership, then prove
                # even a new owner cannot use the old boundary to rewind it.
                budget._resume_lock.close()
                try:
                    load_episode_boundary(args.resume, learner, replay,
                                           environment_factory=factory, config=config)
                except ValueError as exc:
                    if 'ledger changed' not in str(exc):
                        raise
                else:
                    raise AssertionError('stale checkpoint was accepted after new decision')
                if boundary_report is None:
                    boundary_report = {}
                boundary_report.update(stale_snapshot_rejected=True, selected_exact=expected is not None)
                status = 'verified'
                break
            if bool((result.terminated | result.truncated).all()):
                checkpoint = args.output/'natural-boundary.pt'
                boundary_report = save_episode_boundary(checkpoint, learner, replay,
                    environment=env, policy_generator=generator, budget=budget, config=config,
                    counters=counters, journal_paths=journals)
                # Control reset consumes sampler work, zero real decisions. The
                # durable boundary remains BEFORE this reset and collector exits.
                generator_state = generator.get_state().cpu().clone()
                env.reset(deadline=budget.deadline)
                snapshot = online_snapshot(env)
                p = env.candidates['mask'].float()
                selected_reference = torch.multinomial(p/p.sum(-1, keepdim=True), 1,
                                                        generator=generator).squeeze(-1)
                atomic_torch(args.output/'expected-reference.pt', dict(snapshot=snapshot,
                    generator_state=generator_state, selected=selected_reference.cpu(), collector_pid=os.getpid()))
                saved_clean, status = True, 'checkpoint_saved_collector_exiting'
                break
        if args.resume and not post_resume_commits:
            status = 'boundary_verified_no_post_resume_budget'
    except Exception as exc:
        status, error = 'failed', repr(exc)
        raise
    finally:
        # The save-only process must leave the saved ledger digest untouched.
        if budget is not None and not saved_clean:
            budget.flush()
        atomic_json(args.output/('resume-summary.json' if args.resume else 'save-summary.json'),
            dict(status=status, error=error, kind='bounded online natural-boundary collector phase',
                collector_pid=os.getpid(), source_sha256=sha256(args.source),
                new_real_decisions=counters['decisions'], updates=learner.updates,
                online_warmup_complete=False, boundary=boundary_report,
                post_resume_commits=post_resume_commits, budget=None if budget is None else budget.state,
                wall_seconds=time.monotonic()-started,
                limitation='requires all batch rows to end naturally; only batch1 probed'))


def online_orchestrator(args):
    """Serial save/exit and new-PID resume; one namespace, budget and deadline."""
    import json
    import subprocess
    import sys
    started = time.monotonic()
    base = [sys.executable, '-u', str(Path(__file__).resolve()), '--source', str(args.source),
            '--output', str(args.output), '--device', args.device, '--online-boundary',
            '--online-decisions', str(args.online_decisions),
            '--online-started-monotonic', str(started)]
    first = subprocess.run(base+['--online-stage', 'save'], check=False)
    phases = [dict(phase='save', returncode=first.returncode)]
    if first.returncode == 0 and (args.output/'natural-boundary.pt').exists():
        second = subprocess.run(base+['--online-stage', 'resume', '--resume', str(args.output/'natural-boundary.pt'),
            '--expected-reference', str(args.output/'expected-reference.pt')], check=False)
        phases.append(dict(phase='resume', returncode=second.returncode))
    paths = [args.output/name for name in ('save-summary.json', 'resume-summary.json')]
    summaries = {p.stem: json.loads(p.read_text()) for p in paths if p.exists()}
    resumed = summaries.get('resume-summary', {})
    result = dict(status=resumed.get('status', 'not_verified'), phases=phases,
        kind='cross-process bounded online natural-boundary collector probe',
        source_sha256=sha256(args.source), wall_seconds=time.monotonic()-started,
        new_real_decisions=json.loads((args.output/'online-budget.json').read_text())['completed_decisions']
            if (args.output/'online-budget.json').exists() else 0,
        updates=0, online_warmup_complete=False, phase_summaries=summaries)
    if any(p['returncode'] for p in phases):
        result['status'] = 'failed'
    atomic_json(args.output/'online-summary.json', result)
    if result['status'] == 'failed':
        raise RuntimeError('online collector child failed; see phase summaries')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', default='cuda:0')
    parser.add_argument('--fixture-updates', type=int, default=1)
    parser.add_argument('--diagnose-checkpoint', type=Path)
    parser.add_argument('--deterministic', action='store_true')
    parser.add_argument('--online-boundary', action='store_true')
    parser.add_argument('--online-decisions', type=int, default=4)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--expected-reference', type=Path)
    parser.add_argument('--online-stage', choices=('save', 'resume'))
    parser.add_argument('--online-started-monotonic', type=float)
    args = parser.parse_args()
    if args.resume and not args.online_boundary:
        raise ValueError('--resume requires --online-boundary')
    if args.diagnose_checkpoint:
        diagnose_existing_fixture(args)
    elif not args.online_boundary:
        offline_fixture(args)
    elif args.online_stage or args.resume:
        online_boundary(args)
    else:
        online_orchestrator(args)


if __name__ == '__main__':
    main()
