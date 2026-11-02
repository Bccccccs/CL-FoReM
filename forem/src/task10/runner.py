"""One authorized task10 smoke, then four fixed paired validation cases.

    PYTHONPATH=src python3 -u -m task10.runner train --output results/task10/RUN
    PYTHONPATH=src python3 -u -m task10.runner paired --output results/task10/RUN

Collector restoration is limited to a fully committed natural whole-batch
episode boundary; the original ledger and absolute deadline remain binding.
"""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import random
import signal
import time
import traceback

from .runtime import (Budget, atomic_json, atomic_torch, sha256, split_manifest, state_digest,
                      timing_summary)


ROOT = Path(__file__).resolve().parents[2]


def emit(path, event):
    def serializable(value):
        if hasattr(value, 'detach'):
            return value.detach().cpu().tolist()
        raise TypeError(type(value).__name__)
    with Path(path).open('a') as stream:
        stream.write(json.dumps(event, allow_nan=False, default=serializable) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(event, allow_nan=False, default=serializable), flush=True)


def tensor_state_hash(module):
    import hashlib
    digest = hashlib.sha256()
    for key, value in sorted(module.state_dict().items()):
        digest.update(key.encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def initialize(seed):
    import numpy as np
    import torch
    torch.set_num_threads(2)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    # Neither matmul TF32 nor cuDNN benchmark may silently change comparisons.
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required; no silent CPU fallback')
    torch.cuda.set_device(0)
    torch.cuda.reset_peak_memory_stats()


class Timers:
    def __init__(self):
        self.records = {}

    @contextmanager
    def measure(self, name):
        import torch
        torch.cuda.synchronize()
        start = time.monotonic()
        try:
            yield
        finally:
            torch.cuda.synchronize()
            self.records.setdefault(name, []).append(time.monotonic()-start)


def contract(args, policy, pool):
    import torch
    hashes = {}
    for module in ('task10', 'task7_upper', 'task7_lower', 'task7_sim', 'task8_sim'):
        for path in sorted((ROOT/'src'/module).glob('*.py')):
            hashes[str(path.relative_to(ROOT))] = sha256(path)
    hashes['scripts/task10_run_bounded.sh'] = sha256(ROOT/'scripts/task10_run_bounded.sh')
    return dict(run_id=args.output.name, code_commit=os.environ.get('TASK10_CODE_COMMIT', 'unknown'),
                code_sha256=hashes, config=json.loads((ROOT/'config/task10/smoke.json').read_text()),
                config_sha256=sha256(ROOT/'config/task10/smoke.json'),
                lower_hashes=policy.hash_report, lower_actor=policy.actor_sha256,
                splits=split_manifest(pool), seed=101, random_seed=102,
                dtype='torch.float32', device='cuda:0', gpu=torch.cuda.get_device_name(0),
                physical_gpu=os.environ.get('TASK10_PHYSICAL_GPU', 'unknown'),
                torch=torch.__version__, threads=torch.get_num_threads(),
                collector_resume='all natural episode ends before next reset; explicit new-PID resume only',
                limits=dict(decisions=1200, updates=200, training_seconds=1800, paired_seconds=1800))


def gradients(model):
    import torch
    report = {}
    for name, module in model._groups().items():
        parameters = list(module.parameters())
        report[name] = dict(trainable=sum(p.numel() for p in parameters if p.requires_grad),
                            with_gradient=sum(p.grad is not None for p in parameters),
                            nonzero=sum(p.grad is not None and bool(torch.count_nonzero(p.grad)) for p in parameters))
    return report


def check_finite(tree):
    import torch
    if isinstance(tree, torch.Tensor) and tree.is_floating_point() and not torch.isfinite(tree).all():
        raise FloatingPointError('nonfinite environment/replay field')
    if isinstance(tree, dict):
        for value in tree.values():
            check_finite(value)


def restore_evidence(path, learner, replay, config, counters):
    """Nonempty learner-only evidence without advancing caller replay/global RNG."""
    from .recovery import verify_learner_checkpoint
    return verify_learner_checkpoint(path, learner, replay, config, counters)


def collector_comparable(value):
    """Exclude measured wall time; retain scientific fields and identity."""
    if isinstance(value, dict):
        return {k: collector_comparable(v) for k, v in value.items()
                if k not in ('search_wall_seconds', 'timing')}
    if isinstance(value, list):
        return [collector_comparable(v) for v in value]
    if isinstance(value, tuple):
        return tuple(collector_comparable(v) for v in value)
    return value


def collector_snapshot(env, generator, selected):
    from task7_upper.replay import exact_cpu
    from task7_lower.training import rng_state
    from .recovery import _streams_state
    return dict(scene_digest=state_digest(env), observation=exact_cpu(env.observation),
        candidates=collector_comparable(exact_cpu(env.candidates)), selected=selected.cpu().clone(),
        episode_ids=env.episodes.episode_count.cpu().clone(),
        decision_ids=env.episodes.core.decisions.cpu().clone(),
        proposal_seeds=list(env.episodes.proposal_seeds),
        sampler_streams=_streams_state(env.episodes), policy_generator=generator.get_state().cpu(),
        rng=rng_state())


def train(args, launched):
    import torch
    from task10.lower import FrozenB3
    from task10.environment import Task10Env
    from task10.learning import EpisodeReplay, Stage1Learner, update_sequences, ReplayAdapter
    from task7_upper.model import UpperModel
    from task7_upper.replay import row, exact_cpu
    from task7_upper.stages import environment_inputs, rebuild_online
    from task7_upper.sac_discrete import distribution
    from .recovery import save_episode_boundary, load_episode_boundary, tree_equal, mismatch_report

    args.output.mkdir(parents=True, exist_ok=True)
    resume = getattr(args, 'resume', None)
    stop_at_boundary = getattr(args, 'stop_at_boundary', False)
    boundary_reference = getattr(args, 'boundary_reference', False)
    max_decisions = getattr(args, 'max_decisions', 1200)
    max_updates = getattr(args, 'max_updates', 200)
    seconds = getattr(args, 'seconds', 1800)
    if max_decisions % 8 or not 8 <= max_decisions <= 1200 or not 0 <= max_updates <= 200 or not 20 < seconds <= 1800:
        raise ValueError('invalid bounded batch8 limits')
    if boundary_reference and (not stop_at_boundary or max_updates != 0):
        raise ValueError('boundary reference requires explicit stop and a zero-update diagnostic')
    budget = None
    if not resume:
        budget = Budget(args.output/'training-budget.json', started=launched, seconds=seconds,
                        decisions=max_decisions, updates=max_updates)
        # The inherited deadline includes cleanup; resume never grants a new clock.
        budget.deadline -= 20
        budget.state['cleanup_reserve_seconds'] = 20
    saved_clean = False
    original_budget = None
    reference_mode = False
    output = args.output
    run_name = args.output.name
    resumed_expected = None
    resumed_comparison = None
    timers = Timers()
    started = time.monotonic()
    learner = model = replay = env = cfg = None
    history = []
    completed_episodes = []
    status, error = 'incomplete', None
    pending_result = None
    gradient_report = None
    initialize(101)
    try:
        with timers.measure('lower_load_hashes'):
            policy = FrozenB3(device='cuda:0', artifact_root='/reference', source_root='/reference/source')
        pool = Path('/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json')
        current_contract = contract(args, policy, pool)
        lower_before = tensor_state_hash(policy.actor)
        def factory():
            value = Task10Env(8, policy, seed=101, pool=pool, split='train', device='cuda:0', run_id=run_name,
                           code_commit=cfg['code_commit'], config_hash=cfg['config_sha256'],
                           risk_chunk_size=256, observation_chunk_size=128, reuse_route_raster=True)
            value.episodes.kin.dls_cuda_graph = True
            return value
        if resume:
            cfg = json.loads((args.output/'contract.json').read_text())
            for key in ('code_sha256', 'config_sha256', 'lower_hashes', 'lower_actor', 'splits',
                        'seed', 'dtype', 'device', 'threads', 'torch', 'gpu', 'physical_gpu',
                        'code_commit', 'random_seed'):
                if not tree_equal(cfg.get(key), current_contract.get(key)):
                    raise ValueError(f'resume execution contract changed: {key}')
            payload = torch.load(resume, map_location='cpu', weights_only=False)
            if Path(payload['ledger_path']).resolve() != (args.output/'training-budget.json').resolve():
                raise ValueError('resume must use the original output and ledger')
            if (max_decisions, max_updates, seconds) != (payload['ledger']['max_decisions'], payload['ledger']['max_updates'], payload['ledger']['max_seconds']):
                raise ValueError('resume limits must match the original ledger')
            vector_dim = payload['counters']['vector_dim']
            model = UpperModel(vector_dim=vector_dim).cuda()
            learner = Stage1Learner(model, total_updates=200)
            replay = EpisodeReplay(seed=101)
            bundle = load_episode_boundary(resume, learner, replay, environment_factory=factory, config=cfg)
            env, generator, budget, history = (bundle[k] for k in
                ('environment', 'policy_generator', 'budget', 'histories'))
            if (args.output/'boundary-reference.pt').exists():
                resumed_expected = torch.load(args.output/'boundary-reference.pt', map_location='cpu', weights_only=False)
            completed_episodes = [json.loads(line) for line in (output/'episodes.jsonl').read_text().splitlines()] if (output/'episodes.jsonl').exists() else []
            emit(args.output/'events.jsonl', dict(event='collector_resumed', pid=os.getpid(),
                decisions=budget.state['completed_decisions'], started_monotonic=budget.started,
                deadline_monotonic=budget.deadline))
        else:
            cfg = current_contract
            cfg['effective_limits'] = dict(decisions=max_decisions, updates=max_updates, seconds=seconds)
            atomic_json(args.output/'contract.json', cfg)
            emit(args.output/'events.jsonl', dict(event='training_start', seed=101, code_commit=cfg['code_commit'],
                 deadline_seconds=seconds, gpu=cfg['gpu'], physical_gpu=cfg['physical_gpu']))
            env = factory()
            with timers.measure('initial_reset'):
                obs, candidates = env.reset(deadline=budget.deadline)
            item = environment_inputs(obs, candidates, env_ids=range(8), asynchronous=False, device='cuda:0')
            vector_dim = item['vcm_inputs']['observation'][1].shape[-1]
            cfg['actual_upper_inputs'] = dict(vector_dim=vector_dim,
                observation_shapes={k: list(v.shape) for k, v in obs.items() if isinstance(v, torch.Tensor)},
                geometry_shape=list(item['geometry'].shape), features_shape=list(item['features'].shape),
                mask_shape=list(item['mask'].shape), failure_denominator=env.episodes.core.failure_limit,
                result_order=list(__import__('task7_upper.stages', fromlist=['RESULT_FIELDS']).RESULT_FIELDS))
            atomic_json(args.output/'contract.json', cfg)
            emit(args.output/'events.jsonl', dict(event='initial_boundary_ready', vector_dim=vector_dim,
                 reset_seconds=timers.records['initial_reset'][-1], timing=env.last_timing))
            model = UpperModel(vector_dim=vector_dim).cuda()
            learner = Stage1Learner(model, total_updates=200)
            replay = EpisodeReplay(seed=101)
            history = [[] for _ in range(8)]
            generator = torch.Generator(device='cuda:0').manual_seed(101)
        adapter = ReplayAdapter(False, 'cuda:0')
        while budget.state['reserved_decisions'] < max_decisions and (max_updates == 0 or learner.updates < max_updates):
            budget.check()
            with timers.measure('online_memory_inference'):
                model.eval()
                rebuild_online(model, history, adapter)
                item = environment_inputs(env.observation, env.candidates, env_ids=range(8), asynchronous=False, device='cuda:0')
                with torch.no_grad():
                    logits = model.forward_step(**item)['logits']
                    probability, _ = distribution(logits, env.candidates['mask'])
                    if budget.state['completed_decisions'] < 1000:
                        probability = env.candidates['mask'].float()/env.candidates['mask'].sum(-1, keepdim=True)
                    selected = torch.multinomial(probability, 1, generator=generator).squeeze(-1)
            if reference_mode or resumed_expected is not None:
                boundary_start = collector_snapshot(env, generator, selected)
                if resumed_expected is not None:
                    atomic_torch(args.output/'boundary-resumed.pt', dict(start=boundary_start,
                        collector_pid=os.getpid(), deadline_monotonic=budget.deadline, started_monotonic=budget.started))
                    differences = mismatch_report(resumed_expected['start'], boundary_start)
                    if differences:
                        atomic_json(args.output/'boundary-comparison.json', dict(status='exact_mismatch', phase='next_batch_start', differences=differences))
                        raise AssertionError('resumed next batch scene/observation/candidates/selection differs')
                    resumed_comparison = dict(next_batch_start_exact=True)
            budget.reserve(8)
            atomic_json(output/'pending-intent.json', dict(
                reserved_through=budget.state['reserved_decisions'],
                completed_before=budget.state['completed_decisions'], selected=selected.tolist()))
            with timers.measure('decision_total'):
                result = env.step(selected, deadline=budget.deadline)
            pending_result = result
            # Raw selected-slot execution is durable before an expensive next
            # prediction. Deadline/cancel cannot silently discard failed rows.
            with timers.measure('execution_journal'):
                journal = output/'real-executions'/f"batch-{budget.state['reserved_decisions']:06d}.pt"
                atomic_torch(journal, dict(reserved_through=budget.state['reserved_decisions'],
                    next_boundary_ready=False, fields=exact_cpu(result.replay_fields)))
                emit(output/'real-executions.jsonl', dict(completed=budget.state['reserved_decisions'],
                     journal=str(journal.relative_to(output)),
                     selected=selected.tolist(), terminated=result.terminated.tolist(),
                     truncated=result.truncated.tolist(), reward=result.reward.tolist(),
                     attempted=result.replay_fields['attempted_substeps'].tolist(),
                     committed=result.replay_fields['committed_substeps'].tolist()))
            budget.complete(8)
            fields = result.replay_fields
            ended = result.terminated | result.truncated
            for i in torch.where(ended)[0].tolist():
                c = env.episodes.core
                record = dict(environment=i, episode_id=int(fields['episode_id'][i]),
                              map_id=fields['map_ids'][i], strict_success=bool(c.strict_success[i]),
                              terminated=bool(result.terminated[i]), truncated=bool(result.truncated[i]),
                              failures=int(c.failures[i]), stalls=int(c.stalls[i]), decisions=int(c.decisions[i]),
                              attempted_seconds=float(c.attempt_time[i]), committed_seconds=float(c.time[i]),
                              route_progress=float(c.state.s[i]), route_length=float(c.route.length[i]))
                completed_episodes.append(record)
                emit(output/'episodes.jsonl', record)
            with timers.measure('next_boundary'):
                result = env.prepare_next(result, deadline=budget.deadline)
            check_finite(result.replay_fields)
            with timers.measure('replay_to_cpu'):
                fields = result.replay_fields
                for i in range(8):
                    transition = row(fields, i, 8)
                    key = (run_name, i, int(fields['episode_id'][i]))
                    replay.append(key, transition)
                    history[i].append(exact_cpu(transition))
            pending_result = None
            for i in torch.where(ended)[0].tolist():
                history[i] = []
            for _ in range(min(8, max(0, budget.state['completed_decisions']-1000-learner.updates))):
                budget.check()
                if learner.updates >= max_updates:
                    break
                with timers.measure('update_total'):
                    learned = update_sequences(learner, replay, budget.state['completed_decisions'], adapter, profile=True)
                if learned.get('updated', True) is False:
                    raise RuntimeError('post-warmup replay not ready')
                budget.update()
                gradient_report = gradients(model)
                emit(output/'updates.jsonl', learned)
            emit(output/'decisions.jsonl', dict(completed=budget.state['completed_decisions'],
                 updates=learner.updates, attempted=int(fields['attempted_substeps'].sum()),
                 committed=int(fields['committed_substeps'].sum()),
                 selected=selected.tolist(), timing=result.info.get('timing', {})))
            emit(output/'batch-boundaries.jsonl', dict(batch=budget.state['completed_decisions']//8,
                ended_rows=int(ended.sum()), ended=ended.tolist(),
                completed=budget.state['completed_decisions'], reserved=budget.state['reserved_decisions'],
                in_flight=budget.state['in_flight'], replay=len(replay)))
            if reference_mode or resumed_expected is not None:
                reference_end = dict(fields=collector_comparable(fields), replay=collector_comparable(replay.state_dict()),
                    ledger={k: budget.state[k] for k in ('reserved_decisions','completed_decisions','in_flight','updates','max_decisions','max_updates','max_seconds')},
                    journal=collector_comparable(torch.load(journal, map_location='cpu', weights_only=False)))
                if reference_mode:
                    atomic_torch(args.output/'boundary-reference.pt', dict(start=boundary_start, end=reference_end,
                        collector_pid=os.getpid(), deadline_monotonic=budget.deadline,
                        started_monotonic=budget.started, real_decisions=8))
                    status = 'boundary_saved'
                else:
                    atomic_torch(args.output/'boundary-resumed.pt', dict(start=boundary_start, end=reference_end,
                        collector_pid=os.getpid(), deadline_monotonic=budget.deadline, started_monotonic=budget.started))
                    differences = mismatch_report(resumed_expected['end'], reference_end)
                    deadline_exact = budget.deadline == resumed_expected['deadline_monotonic']
                    started_exact = budget.started == resumed_expected['started_monotonic']
                    resumed_comparison.update(status='verified' if not differences and deadline_exact and started_exact else 'exact_mismatch',
                        next_journal_replay_ledger_exact=not differences, differences=differences,
                        old_pid=resumed_expected['collector_pid'], new_pid=os.getpid(),
                        original_deadline_exact=deadline_exact,
                        original_started_exact=started_exact)
                    atomic_json(args.output/'boundary-comparison.json', resumed_comparison)
                    if differences or not deadline_exact or not started_exact:
                        raise AssertionError('resumed next journal/replay/ledger or original deadline differs')
                    status = 'resumed_batch_verified'
                break
            if stop_at_boundary and bool(ended.all()):
                journals = sorted((args.output/'real-executions').glob('batch-*.pt'))
                report = save_episode_boundary(args.output/'collector-boundary.pt', learner, replay,
                    environment=env, policy_generator=generator, budget=budget, config=cfg,
                    counters=dict(decisions=budget.state['completed_decisions'], updates=learner.updates, vector_dim=vector_dim),
                    journal_paths=journals)
                saved_clean = True
                emit(args.output/'events.jsonl', dict(event='collector_boundary_saved', report=report,
                    pid=os.getpid(), deadline_monotonic=budget.deadline))
                if not boundary_reference:
                    status = 'boundary_saved'
                    break
                if budget.state['max_decisions']-budget.state['completed_decisions'] < 8:
                    status = 'boundary_saved_no_reference_budget'
                    break
                # Continue the same loop through one real batch as a control. Its
                # separate ledger cannot invalidate the saved collector ledger.
                from copy import deepcopy
                original_budget = budget
                shadow = Budget.__new__(Budget)
                shadow.started, shadow.deadline = budget.started, budget.deadline
                shadow.state = deepcopy(budget.state)
                output = args.output/'continuous-reference'
                output.mkdir(exist_ok=False)
                shadow.path = output/'training-budget.json'
                shadow.flush()
                budget = shadow
                reference_mode = True
            if budget.state['completed_decisions'] >= max_decisions or (max_updates and learner.updates >= max_updates):
                break
            if ended.any():
                with timers.measure('reset_ended'):
                    env.reset(indices=torch.where(ended)[0].tolist(), deadline=budget.deadline)
        if status == 'incomplete':
            status = 'bounded_complete'
    except (TimeoutError, StopIteration) as exc:
        status, error = 'budget_stop', str(exc)
    except Exception as exc:
        status, error = 'failed', repr(exc)
        traceback.print_exc()
    finally:
        reference_consumed = 0
        if original_budget is not None:
            reference_consumed = budget.state['reserved_decisions'] - original_budget.state['reserved_decisions']
            budget.state.update(status=status, error=error)
            budget.flush()
            budget = original_budget
            # Keep the ordinary learner artifacts consistent with the original
            # saved ledger; reference artifacts live in their own directory.
            snapshot = torch.load(args.output/'collector-boundary.pt', map_location='cpu', weights_only=False)
            learner.load_state_dict(snapshot['learner'])
            replay.load_state_dict(snapshot['replay'])
            history = [[] for _ in range(8)]
        if budget is None:
            raise RuntimeError('collector restore failed before acquiring a valid budget')
        # Final actor is always the last weights, never selected on validation.
        recovery = None
        if env is not None and budget.state['in_flight']:
            c = env.episodes.core
            atomic_torch(args.output/'partial-execution.pt', dict(state=exact_cpu(dict(base=c.state.base, q=c.state.q, s=c.state.s)),
                attempted_total=c.attempted_total.cpu(), committed_total=c.committed_total.cpu(),
                attempts=exact_cpu(getattr(c, 'attempts', [])),
                budget=budget.state, note='partial real execution; no fabricated terminal transition'))
        if learner is not None:
            with timers.measure('checkpoint_and_recovery_check'):
                model.vcm.reset()
                actor_path = args.output/'final.actor.pt'
                atomic_torch(actor_path, dict(format='task10-stage1-actor-v1', model=model.state_dict(),
                                vector_dim=vector_dim, updates=learner.updates,
                                decisions=budget.state['completed_decisions']))
                # This is an offline learner artifact at a completed append
                # boundary. It cannot restore an in-progress physical episode.
                recovery = restore_evidence(args.output/'offline-learner.pt', learner, replay, cfg,
                              dict(decisions=budget.state['completed_decisions'], updates=learner.updates, vector_dim=vector_dim))
            lower_after = tensor_state_hash(policy.actor)
            if lower_before != lower_after or any(p.grad is not None for p in policy.actor.parameters()):
                status, error = 'failed', 'frozen B3 changed or received gradients'
        timings = timing_summary(timers.records)
        summary = dict(status=status, error=error, budget=budget.state,
                       wall_seconds=time.monotonic()-budget.started, process_pid=os.getpid(),
                       collector_boundary_saved=saved_clean, continuous_reference_reserved_decisions=reference_consumed,
                       original_deadline_monotonic=budget.deadline, original_started_monotonic=budget.started,
                       training_body_seconds=time.monotonic()-started,
                       actual_decisions=budget.state['completed_decisions'], updates=0 if learner is None else learner.updates,
                       completed_episodes=len(completed_episodes), strict_successes=sum(x['strict_success'] for x in completed_episodes),
                       incomplete_episodes=[] if env is None else [dict(environment=i, decisions=len(h)) for i, h in enumerate(history) if h],
                       pending_real_transitions=0 if pending_result is None else 8,
                       replay_transitions=0 if replay is None else len(replay),
                       gradient_report=None if learner is None else gradient_report,
                       lower_unchanged=None if learner is None else lower_before == lower_after,
                       recovery=recovery, timing=timings,
                       peak_cuda_memory_bytes=torch.cuda.max_memory_allocated(),
                       model_device=None if model is None else str(next(model.parameters()).device),
                       optimizer_devices=[] if learner is None else sorted({str(v.device) for s in learner.optimizer.state.values() for v in s.values() if isinstance(v, torch.Tensor)}))
        if not saved_clean:
            budget.state.update(status=status, error=error)
            budget.flush()
        summary['budget'] = budget.state
        atomic_json(args.output/('resume-summary.json' if resume else 'training-summary.json'), summary)
        emit(args.output/'events.jsonl', dict(event='training_exit', status=status, decisions=summary['actual_decisions'], updates=summary['updates'], error=error))
    return 0 if status in ('bounded_complete', 'budget_stop', 'boundary_saved', 'boundary_saved_no_reference_budget', 'resumed_batch_verified') else 1


def paired(args, launched):
    import torch
    from task10.lower import FrozenB3
    from task10.environment import Task10Env
    from task7_upper.model import UpperModel
    from task7_upper.stages import environment_inputs
    initialize(101)
    if (args.output/'paired-budget.json').exists():
        raise RuntimeError('paired budget already started; no automatic restart')
    budget = Budget(args.output/'paired-budget.json', started=launched, seconds=1800, decisions=0, updates=0)
    budget.deadline -= 10
    budget.state['cleanup_reserve_seconds'] = 10
    cfg = json.loads((args.output/'contract.json').read_text())
    maps = cfg['splits']['validation']
    if len(maps) != 4:
        raise ValueError('exactly four validation scenes required')
    policy = FrozenB3(device='cuda:0', artifact_root='/reference', source_root='/reference/source')
    saved = torch.load(args.output/'final.actor.pt', map_location='cuda:0', weights_only=False)
    model = UpperModel(vector_dim=saved['vector_dim']).cuda().eval()
    model.load_state_dict(saved['model'])
    timers, rows, status = Timers(), [], 'complete'
    pool = '/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json'
    try:
        for map_id in maps:
            hashes = []
            for strategy in ('actor', 'uniform'):
                budget.check()
                current = dict(map_id=map_id, strategy=strategy, seed=101, random_seed=102, complete=False,
                               strict_success=False, decisions=0, reason='external_budget')
                rows.append(current)
                env = Task10Env(1, policy, seed=101, pool=pool, split='validation', device='cuda:0', run_id=args.output.name+'-paired',
                               risk_chunk_size=256, observation_chunk_size=128, reuse_route_raster=True)
                env.episodes.kin.dls_cuda_graph = True
                with timers.measure('paired_reset'):
                    env.reset(map_ids=[map_id], deadline=budget.deadline)
                current['initial_hash'] = state_digest(env)
                hashes.append(current['initial_hash'])
                if len(hashes) == 2 and hashes[0] != hashes[1]:
                    raise AssertionError('paired initial-state mismatch')
                current['proposal_seed'] = env.episodes.info()['proposal_seeds'][0]
                current['scene_provenance'] = env.episodes.scenes.select([0]).provenance() if hasattr(env.episodes.scenes.select([0]), 'provenance') else None
                model.vcm.reset()
                generator = torch.Generator(device='cuda:0').manual_seed(102)
                while True:
                    budget.check()
                    with torch.no_grad():
                        if strategy == 'uniform':
                            p = env.candidates['mask'].float()
                            selected = torch.multinomial(p/p.sum(-1, keepdim=True), 1, generator=generator).squeeze(-1)
                        else:
                            item = environment_inputs(env.observation, env.candidates, env_ids=[0], asynchronous=False, device='cuda:0')
                            selected = model.forward_step(**item)['logits'].argmax(-1)
                    with timers.measure('paired_decision'):
                        result = env.step(selected, deadline=budget.deadline)
                    current['decisions'] += 1
                    if bool((result.terminated | result.truncated)[0]):
                        c = env.episodes.core
                        current.update(complete=True, strict_success=bool(c.strict_success[0]),
                                       failures=int(c.failures[0]), stalls=int(c.stalls[0]),
                                       attempted_seconds=float(c.attempt_time[0]), committed_seconds=float(c.time[0]),
                                       terminated=bool(c.terminated[0]), truncated=bool(c.truncated[0]),
                                       reason='strict_success' if bool(c.strict_success[0]) else
                                       'failure_limit' if int(c.failures[0]) >= c.failure_limit else
                                       'stall_limit' if int(c.stalls[0]) >= 5 else
                                       'decision_limit' if int(c.decisions[0]) >= 150 else
                                       'time_limit' if float(c.attempt_time[0]) >= 200 else 'completion_with_failures')
                        break
                    with timers.measure('paired_next_boundary'):
                        env.prepare_next(result, deadline=budget.deadline)
                emit(args.output/'paired-episodes.jsonl', current)
                atomic_json(args.output/'paired-progress.json', rows)
    except TimeoutError:
        status = 'incomplete_budget'
    except Exception as exc:
        traceback.print_exc()
        status = 'failed'
        emit(args.output/'events.jsonl', dict(event='paired_failure', error=repr(exc)))
    present = {(r['map_id'], r['strategy']) for r in rows}
    rows += [dict(map_id=m, strategy=s, seed=101, complete=False, strict_success=False,
                  decisions=0, reason='not_started') for m in maps for s in ('actor', 'uniform') if (m, s) not in present]
    score = {}
    for strategy in ('actor', 'uniform'):
        values = [r for r in rows if r['strategy'] == strategy]
        success = sum(r['complete'] and r['strict_success'] for r in values)
        missing = sum(not r['complete'] for r in values)
        score[strategy] = dict(expected=4, completed=4-missing, strict_success=success, missing=missing,
                               strict_success_rate_bounds=[success/4, (success+missing)/4])
    outcomes = dict(win=0, loss=0, tie=0, missing=0)
    for m in maps:
        a = next(r for r in rows if r['map_id'] == m and r['strategy'] == 'actor')
        b = next(r for r in rows if r['map_id'] == m and r['strategy'] == 'uniform')
        outcomes['missing' if not (a['complete'] and b['complete']) else
                 'tie' if a['strict_success'] == b['strict_success'] else
                 'win' if a['strict_success'] else 'loss'] += 1
    summary = dict(status=status, rows=rows, scores=score, pairs=outcomes,
                   wall_seconds=time.monotonic()-launched, timing=timing_summary(timers.records),
                   training_updates=saved['updates'], training_decisions=saved['decisions'])
    atomic_json(args.output/'paired-summary.json', summary)
    budget.state.update(status=status)
    budget.flush()
    emit(args.output/'events.jsonl', dict(event='paired_exit', status=status, scores=score, pairs=outcomes))
    return 1 if status == 'failed' else 0


def main():
    launched = time.monotonic()
    if 'TASK10_STARTED_EPOCH' in os.environ:
        # An infrastructure failure before ledger creation still consumes the
        # original invocation's wall budget; retry cannot grant a fresh clock.
        launched -= max(0., time.time()-float(os.environ['TASK10_STARTED_EPOCH']))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('train', 'paired'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--stop-at-boundary', action='store_true')
    parser.add_argument('--boundary-reference', action='store_true')
    parser.add_argument('--max-decisions', type=int, default=1200)
    parser.add_argument('--max-updates', type=int, default=200)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args()
    args.output = args.output.resolve()
    def stop(signum, frame):
        raise TimeoutError('external bounded supervisor stop')
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    return (train if args.phase == 'train' else paired)(args, launched)


if __name__ == '__main__':
    raise SystemExit(main())
