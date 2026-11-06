"""Explicit task10.17 single-seed 10k collector. Never retries or rewinds.

The old smoke/trial runners and authorization limits remain unchanged. This
module is entered only through the new supervised ``long-10k`` profile.
"""
import argparse
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import signal
import time
import traceback

from .runtime import Budget, atomic_json, atomic_torch, sha256, timing_summary

FORMAT = 'task10-long-checkpoint-index-v1'
CHECKPOINTS = (2000, 5000, 10000)


class LongBudget(Budget):
    """Exact one-run authorization; inherited methods preserve write-ahead costs."""
    def __init__(self, path, *, started, started_epoch=None, seconds=194400,
                 decisions=10000, updates=9000):
        self.path = Path(path)
        if self.path.exists():
            raise RuntimeError('existing budget ledger: automatic restart is prohibited')
        if (seconds, decisions, updates) != (194400, 10000, 9000):
            raise ValueError('long-10k requires exact approved limits')
        if not math.isfinite(started) or started > time.monotonic():
            raise ValueError('invalid original start')
        if started_epoch is None:
            started_epoch = float(os.environ.get('TASK10_STARTED_EPOCH',
                time.time() - (time.monotonic() - started)))
        if not math.isfinite(started_epoch) or started_epoch > time.time():
            raise ValueError('invalid original epoch')
        self.started, self.deadline = started, started + seconds
        self.state = dict(run_profile='long-10k', started_monotonic=started,
            deadline_monotonic=self.deadline, started_epoch=started_epoch,
            deadline_epoch=started_epoch+seconds, max_seconds=seconds,
            max_decisions=decisions, max_updates=updates, reserved_decisions=0,
            completed_decisions=0, updates=0, in_flight=0, status='active',
            pid=os.getpid(), cleanup_reserve_seconds=120,
            work_deadline_monotonic=self.deadline-120)
        self.flush()


def updates_due(decisions, updates):
    if decisions % 8 or not 0 <= decisions <= 10000 or not 0 <= updates <= 9000:
        raise ValueError('invalid long-10k batch counters')
    target = max(0, decisions-1000)
    if updates > target:
        raise ValueError('updates exceed new real post-warmup decisions')
    due = target-updates
    if due > 8:
        raise ValueError('more than one real batch of uncommitted updates')
    return due


def checkpoint_due(decisions):
    return decisions > 0 and (decisions % 256 == 0 or decisions in CHECKPOINTS)


def checkpoint_paths(root, decisions):
    prefix = Path(root)/'checkpoints'/f'decision-{decisions:06d}'
    return {kind: Path(str(prefix)+suffix) for kind, suffix in
            (('boundary', '.boundary.pt'), ('learner', '.learner.pt'),
             ('actor', '.actor.pt'), ('metadata', '.json'))}


def save_consistent(root, learner, replay, env, generator, budget, config,
                    vector_dim, histories, *, reason):
    """All mutations complete before this point; publish latest only after fsync."""
    from .recovery import save_decision_boundary
    from .runner import durable_learner_checkpoint
    root = Path(root)
    decisions, updates = budget.state['completed_decisions'], learner.updates
    if updates != max(0, decisions-1000) or updates != budget.state['updates']:
        raise ValueError('checkpoint requires exact UTD=1 update commit')
    paths = checkpoint_paths(root, decisions)
    if any(p.exists() for p in paths.values()):
        if paths['metadata'].is_file():
            prior = json.loads(paths['metadata'].read_text())
            if (prior.get('decisions') == decisions and prior.get('updates') == updates
                    and prior.get('ledger_sha256') == sha256(budget.path)
                    and all(paths[k].is_file() and sha256(paths[k]) == prior[k]['sha256']
                            for k in ('boundary', 'learner', 'actor'))):
                return prior
        raise FileExistsError('immutable checkpoint already exists or ledger no longer matches')
    paths['boundary'].parent.mkdir(parents=True, exist_ok=True)
    counters = dict(decisions=decisions, updates=updates, vector_dim=vector_dim)
    journals = sorted((root/'real-executions').glob('batch-*.pt'))
    report = save_decision_boundary(paths['boundary'], learner, replay,
        environment=env, policy_generator=generator, budget=budget, config=config,
        counters=counters, journal_paths=journals, histories=histories)
    durable_learner_checkpoint(paths['learner'], learner, replay, config, counters)
    metadata = dict(format=FORMAT, run_id=root.name, decisions=decisions,
        updates=updates, vector_dim=vector_dim, scheduler_total_updates=9000,
        warmup_real_decisions=min(1000, decisions), objective='relative_uniform',
        objective_version='task10-relative-uniform-v1', alpha=.35,
        started_epoch=budget.state['started_epoch'], deadline_epoch=budget.state['deadline_epoch'],
        reason=reason, collector_resumable=True, recovery_report=report,
        ledger_sha256=sha256(budget.path))
    atomic_torch(paths['actor'], dict(format='task10-stage1-actor-v1',
        model=learner.model.state_dict(), learning_objective=dict(learner.learning_objective),
        alpha=float(learner.temperature.alpha), vector_dim=vector_dim,
        updates=updates, decisions=decisions, long_checkpoint_contract=deepcopy(metadata)))
    for kind in ('boundary','learner','actor'):
        metadata[kind] = dict(path=str(paths[kind].relative_to(root)), sha256=sha256(paths[kind]))
    atomic_json(paths['metadata'], metadata)
    prior = json.loads((root/'latest-checkpoint.json').read_text()) if (root/'latest-checkpoint.json').exists() else None
    # Retain the immediately preceding index; immutable artifacts remain on disk.
    if prior is not None:
        prior.pop('previous', None)
    atomic_json(root/'latest-checkpoint.json', dict(metadata, previous=prior))
    return metadata


def train(args, launched):
    import torch
    from .entry import initialize_determinism, resolve_profile
    from .lower import FrozenB3
    from .environment import Task10Env
    from .learning import EpisodeReplay, ReplayAdapter, update_sequences
    from .runner import (Timers, contract, create_learner, tensor_state_hash,
                         durable_learner_checkpoint, emit, check_finite, gradients)
    from .recovery import load_decision_boundary, tree_equal
    from task7_upper.model import UpperModel
    from task7_upper.replay import row, exact_cpu
    from task7_upper.stages import environment_inputs, rebuild_online
    from task7_upper.sac_discrete import distribution
    from .training_evidence import snapshot_before, finish_evidence

    root = args.output
    root.mkdir(parents=True, exist_ok=True)
    resolved = resolve_profile(run_profile='long-10k', config=args.config)
    if not all(k in os.environ for k in ('TASK10_HARD_DEADLINE_MONOTONIC', 'TASK10_HARD_DEADLINE_EPOCH')):
        raise ValueError('long-10k requires original outer supervision deadlines')
    for name in ('initial-learner.pt', 'contract.json', 'training-budget.json'):
        if not args.resume and (root/name).exists():
            raise RuntimeError('fresh training must never reuse an existing run')
    budget = None
    env = learner = replay = policy = None
    history, episodes = [], []
    vector_dim = None
    timers = Timers()
    status, error, rc = 'partial', None, 1
    stop = dict(requested=False)
    previous_handler = signal.signal(signal.SIGTERM, lambda *_: stop.update(requested=True))
    signal.signal(signal.SIGINT, lambda *_: stop.update(requested=True))
    last_checkpoint = None
    pending_result = None
    lower_before = None
    process_started = time.monotonic()
    try:
        if not args.resume:
            budget = LongBudget(root/'training-budget.json', started=launched)
            if (float(os.environ['TASK10_HARD_DEADLINE_MONOTONIC']) != budget.deadline or
                float(os.environ['TASK10_HARD_DEADLINE_EPOCH']) != budget.state['deadline_epoch']):
                raise ValueError('outer and ledger deadline mismatch')
        initialize_determinism(101)
        with timers.measure('lower_load_hashes'):
            policy = FrozenB3(device='cuda:0', artifact_root='/reference', source_root='/reference/source')
        pool = Path('/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json')
        current_args = argparse.Namespace(output=root, run_profile='long-10k', config=args.config)
        current = contract(current_args, policy, pool)
        for relative in ('scripts/task10_long_run.sh', 'scripts/task10_long_launch.py'):
            current['code_sha256'][relative] = sha256(Path(__file__).resolve().parents[2]/relative)
        current['collector_resume'] = 'normal batch8 decision boundary; explicit original-run new-PID resume'
        lower_before = tensor_state_hash(policy.actor)
        cfg = current if not args.resume else json.loads((root/'contract.json').read_text())
        def factory():
            value = Task10Env(8, policy, seed=101, pool=pool, split='train', device='cuda:0',
                run_id=root.name, code_commit=cfg['code_commit'], config_hash=cfg['config_sha256'],
                risk_chunk_size=256, observation_chunk_size=128, reuse_route_raster=True)
            value.episodes.kin.dls_cuda_graph = True
            return value
        if args.resume:
            # Check original run identity before invoking a mutable constructor.
            for key in ('code_sha256','config_sha256','lower_hashes','lower_actor','splits',
                        'seed','dtype','device','threads','torch','gpu','physical_gpu','code_commit','random_seed'):
                if not tree_equal(cfg.get(key), current.get(key)):
                    raise ValueError(f'resume execution contract changed: {key}')
            payload = torch.load(args.resume, map_location='cpu', weights_only=False)
            if Path(payload['ledger_path']).resolve() != (root/'training-budget.json').resolve():
                raise ValueError('resume must retain original run/ledger')
            if (payload['ledger']['max_decisions'],payload['ledger']['max_updates'],payload['ledger']['max_seconds']) != (10000,9000,194400):
                raise ValueError('resume limits mismatch')
            if float(os.environ['TASK10_HARD_DEADLINE_MONOTONIC']) != payload['deadline_monotonic']:
                raise ValueError('resume outer deadline changed')
            vector_dim = payload['counters']['vector_dim']
            learner = create_learner(UpperModel(vector_dim=vector_dim).cuda(),9000,resolved['config'])
            replay = EpisodeReplay(capacity=100000, seed=101)
            bundle = load_decision_boundary(args.resume,learner,replay,environment_factory=factory,config=cfg)
            env, generator, budget, history = (bundle[k] for k in ('environment','policy_generator','budget','histories'))
            if (root/'episodes.jsonl').exists():
                episodes = [json.loads(x) for x in (root/'episodes.jsonl').read_text().splitlines()]
            emit(root/'events.jsonl',dict(event='collector_resumed',pid=os.getpid(),decisions=budget.state['completed_decisions'],deadline_monotonic=budget.deadline))
        else:
            cfg['effective_limits'] = dict(decisions=10000,updates=9000,seconds=194400)
            cfg['deadline'] = dict(started_monotonic=budget.started,hard_deadline_monotonic=budget.deadline,
                started_epoch=budget.state['started_epoch'],hard_deadline_epoch=budget.state['deadline_epoch'],cleanup_reserve_seconds=120)
            atomic_json(root/'contract.json', cfg)
            env = factory()
            with timers.measure('initial_reset'):
                obs,candidates = env.reset(deadline=budget.deadline-120)
            item = environment_inputs(obs,candidates,env_ids=range(8),asynchronous=False,device='cuda:0')
            vector_dim = item['vcm_inputs']['observation'][1].shape[-1]
            cfg['actual_upper_inputs'] = dict(vector_dim=vector_dim,
                observation_shapes={k:list(v.shape) for k,v in obs.items() if isinstance(v,torch.Tensor)},
                geometry_shape=list(item['geometry'].shape),features_shape=list(item['features'].shape),
                mask_shape=list(item['mask'].shape),failure_denominator=env.episodes.core.failure_limit,
                result_order=list(__import__('task7_upper.stages',fromlist=['RESULT_FIELDS']).RESULT_FIELDS))
            atomic_json(root/'contract.json',cfg)
            learner = create_learner(UpperModel(vector_dim=vector_dim).cuda(),9000,resolved['config'])
            replay = EpisodeReplay(capacity=100000,seed=101)
            history = [[] for _ in range(8)]
            generator = torch.Generator(device='cuda:0').manual_seed(101)
            with timers.measure('initial_checkpoint'):
                durable_learner_checkpoint(root/'initial-learner.pt',learner,replay,cfg,
                    dict(decisions=0,updates=0,vector_dim=vector_dim))
            if args.initial_reference is None:
                raise ValueError('full old same-seed initial reference is required')
            reference = torch.load(args.initial_reference,map_location='cpu',weights_only=False)
            expected = reference['learner']['model']
            equal = tree_equal(exact_cpu(learner.model.state_dict()), expected)
            atomic_json(root/'initial-comparison.json',dict(reference=str(args.initial_reference),
                reference_sha256=sha256(args.initial_reference),full_model_state_equal=equal,
                new_initial_sha256=sha256(root/'initial-learner.pt'),scheduler_total_updates=9000,
                reference_scheduler_comparable=False,note='compare full model initialization only; new scheduler intentionally totals 9000'))
            if not equal:
                raise AssertionError('same-seed full initial model differs from task10.16')
        adapter = ReplayAdapter(False,'cuda:0')
        model = learner.model
        emit(root/'events.jsonl',dict(event='training_ready',pid=os.getpid(),decisions=budget.state['completed_decisions'],updates=learner.updates,
            model_device=str(next(model.parameters()).device),lower_tensor_hash=lower_before,lower_actor_sha256=policy.actor_sha256,
            deadline_epoch=budget.state['deadline_epoch'],deadline_monotonic=budget.deadline))
        while budget.state['completed_decisions'] < 10000:
            budget.check()
            if stop['requested'] or time.monotonic() >= budget.deadline-120:
                if budget.state['in_flight']:
                    raise RuntimeError('stop at uncovered physical execution')
                last_checkpoint = save_consistent(root,learner,replay,env,generator,budget,cfg,vector_dim,history,reason='safe_stop')
                status,rc='stopped_boundary',0
                break
            with timers.measure('online_memory_inference'):
                model.eval(); rebuild_online(model,history,adapter)
                item=environment_inputs(env.observation,env.candidates,env_ids=range(8),asynchronous=False,device='cuda:0')
                with torch.no_grad():
                    logits=model.forward_step(**item)['logits']
                    probability,_=distribution(logits,env.candidates['mask'])
                    warmup = budget.state['completed_decisions'] < 1000
                    if warmup:
                        probability=env.candidates['mask'].float()/env.candidates['mask'].sum(-1,keepdim=True)
                    selected=torch.multinomial(probability,1,generator=generator).squeeze(-1)
            budget.reserve(8)
            atomic_json(root/'pending-intent.json',dict(reserved_through=budget.state['reserved_decisions'],completed_before=budget.state['completed_decisions'],selected=selected.tolist(),pid=os.getpid()))
            with timers.measure('decision_total'):
                result=env.step(selected,deadline=budget.deadline-120)
            pending_result=result
            journal=root/'real-executions'/f"batch-{budget.state['reserved_decisions']:06d}.pt"
            with timers.measure('execution_journal'):
                atomic_torch(journal,dict(reserved_through=budget.state['reserved_decisions'],next_boundary_ready=False,fields=exact_cpu(result.replay_fields)))
                emit(root/'real-executions.jsonl',dict(completed=budget.state['reserved_decisions'],journal=str(journal.relative_to(root)),selected=selected.tolist(),
                    selection_mode='uniform_warmup' if warmup else 'sac',epoch=time.time(),wall_seconds=time.monotonic()-budget.started,
                    terminated=result.terminated.tolist(),truncated=result.truncated.tolist(),reward=result.reward.tolist(),
                    attempted=result.replay_fields['attempted_substeps'].tolist(),committed=result.replay_fields['committed_substeps'].tolist()))
            budget.complete(8)
            fields=result.replay_fields; ended=result.terminated|result.truncated
            for i in torch.where(ended)[0].tolist():
                c=env.episodes.core
                record=dict(environment=i,episode_id=int(fields['episode_id'][i]),map_id=fields['map_ids'][i],strict_success=bool(c.strict_success[i]),
                    terminated=bool(result.terminated[i]),truncated=bool(result.truncated[i]),failures=int(c.failures[i]),stalls=int(c.stalls[i]),
                    decisions=int(c.decisions[i]),attempted_seconds=float(c.attempt_time[i]),committed_seconds=float(c.time[i]),
                    route_progress=float(c.state.s[i]),route_length=float(c.route.length[i]),completed=budget.state['completed_decisions'])
                episodes.append(record);emit(root/'episodes.jsonl',record)
            with timers.measure('next_boundary'):
                result=env.prepare_next(result,deadline=budget.deadline-120)
            check_finite(result.replay_fields)
            with timers.measure('replay_to_cpu'):
                fields=result.replay_fields
                for i in range(8):
                    transition=row(fields,i,8)
                    replay.append((root.name,i,int(fields['episode_id'][i])),transition)
                    history[i].append(exact_cpu(transition))
            pending_result=None
            for i in torch.where(ended)[0].tolist():history[i]=[]
            # Replace provisional journal only after all exact next fields exist.
            with timers.measure('execution_commit'):
                atomic_torch(journal,dict(reserved_through=budget.state['reserved_decisions'],next_boundary_ready=True,fields=exact_cpu(fields)))
            if budget.state['completed_decisions']==1000:
                if learner.updates or len(replay)!=1000:
                    raise AssertionError('warmup must contain exactly 1000 new real transitions and zero updates')
                with timers.measure('warmup_checkpoint'):
                    durable_learner_checkpoint(root/'warmup-complete.pt',learner,replay,cfg,
                        dict(decisions=1000,updates=0,vector_dim=vector_dim))
                emit(root/'events.jsonl',dict(event='fresh_warmup_complete',decisions=1000,updates=0,replay=1000))
            for _ in range(updates_due(budget.state['completed_decisions'],learner.updates)):
                budget.check()
                if time.monotonic() >= budget.deadline-120:raise TimeoutError('work deadline during update block')
                first=learner.updates==0
                before=snapshot_before(learner,policy) if first else None
                with timers.measure('update_total'):
                    learned=update_sequences(learner,replay,budget.state['completed_decisions'],adapter,profile=True)
                if learned.get('updated',True) is False:raise RuntimeError('fresh post-warmup replay not ready')
                learned.update(lr=learner.optimizer.param_groups[0]['lr'],scheduler_total_updates=learner.total_updates,decisions=budget.state['completed_decisions'],replay_transitions=len(replay),
                    wall_seconds=time.monotonic()-budget.started,epoch=time.time(),update_wall_seconds=timers.records['update_total'][-1])
                emit(root/'updates.jsonl',learned)
                budget.update()
                if first:
                    evidence=finish_evidence(before,learner,policy,update_result=learned)
                    atomic_torch(root/'first-update-evidence.pt',evidence)
                    atomic_json(root/'first-update-evidence.json',evidence['summary'])
                    if evidence['summary']['must_stop'] or not evidence['summary']['gpu_update_verified']:
                        raise RuntimeError('first actual actor/twin-Q/B3/optimizer GPU update evidence failed')
            if learner.updates != max(0,budget.state['completed_decisions']-1000):
                raise AssertionError('one update per new real post-warmup decision contract')
            if ended.any():
                with timers.measure('reset_ended'):
                    env.reset(indices=torch.where(ended)[0].tolist(),deadline=budget.deadline-120)
            emit(root/'decisions.jsonl',dict(completed=budget.state['completed_decisions'],updates=learner.updates,
                attempted=int(fields['attempted_substeps'].sum()),committed=int(fields['committed_substeps'].sum()),
                selected=selected.tolist(),timing=result.info.get('timing',{}),ended_rows=int(ended.sum())))
            if checkpoint_due(budget.state['completed_decisions']):
                if budget.state['completed_decisions']==10000:
                    budget.state['status']='complete'
                with timers.measure('consistent_checkpoint'):
                    last_checkpoint=save_consistent(root,learner,replay,env,generator,budget,cfg,vector_dim,history,reason='scheduled')
                emit(root/'events.jsonl',dict(event='consistent_checkpoint',decisions=last_checkpoint['decisions'],updates=last_checkpoint['updates'],
                    checkpoint=last_checkpoint['boundary'],wall_seconds=time.monotonic()-budget.started))
        else:
            status,rc='complete',0
        if status=='partial' and budget.state['completed_decisions']==10000:
            status,rc='complete',0
    except TimeoutError as exc:
        status,error,rc='partial',str(exc),0
    except BaseException as exc:
        status,error,rc='failed',repr(exc),1
        traceback.print_exc()
    finally:
        signal.signal(signal.SIGTERM,previous_handler)
        # No final mutation to a safe ledger: a resumable snapshot includes its exact digest.
        if budget is not None and status not in ('complete','stopped_boundary'):
            budget.state.update(status='partial',error=error)
            budget.flush()
        lower_unchanged=None
        if learner is not None:
            try:
                atomic_torch(root/'final.actor.pt',dict(format='task10-stage1-actor-v1',model=learner.model.state_dict(),
                    learning_objective=dict(learner.learning_objective),alpha=float(learner.temperature.alpha),
                    vector_dim=vector_dim,updates=learner.updates,decisions=0 if budget is None else budget.state['completed_decisions']))
                lower_unchanged=lower_before==tensor_state_hash(policy.actor) and not any(p.grad is not None for p in policy.actor.parameters())
                if not lower_unchanged:status,error,rc='failed','frozen B3 changed or acquired gradients',1
            except Exception as exc:
                status,error,rc='failed',f'final artifact failure: {exc!r}',1
        if budget is not None and env is not None and (budget.state['in_flight'] or pending_result is not None):
            c=env.episodes.core
            atomic_torch(root/'partial-execution.pt',dict(state=exact_cpu(dict(base=c.state.base,q=c.state.q,s=c.state.s)),
                attempted_total=c.attempted_total.cpu(),committed_total=c.committed_total.cpu(),attempts=exact_cpu(getattr(c,'attempts',[])),
                budget=deepcopy(budget.state),note='partial consumed interaction; no fabricated terminal or rollback'))
        summary=dict(status=status,error=error,returncode=rc,process_pid=os.getpid(),
            run_profile='long-10k',actual_decisions=0 if budget is None else budget.state['completed_decisions'],
            updates=0 if learner is None else learner.updates,budget=None if budget is None else deepcopy(budget.state),
            wall_seconds=None if budget is None else time.monotonic()-budget.started,
            worker_seconds=time.monotonic()-process_started,completed_episodes=len(episodes),strict_successes=sum(x['strict_success'] for x in episodes),
            incomplete_episodes=[dict(environment=i,decisions=len(h)) for i,h in enumerate(history) if h],
            replay_transitions=0 if replay is None else len(replay),pending_real_transitions=0 if pending_result is None else 8,
            lower_unchanged=lower_unchanged,last_consistent_checkpoint=last_checkpoint,
            timing=timing_summary(timers.records),peak_cuda_memory_bytes=torch.cuda.max_memory_allocated() if torch.cuda.is_available() else None,
            model_device=None if learner is None else str(next(learner.model.parameters()).device),
            optimizer_devices=[] if learner is None else sorted({str(v.device) for s in learner.optimizer.state.values() for v in s.values() if isinstance(v,torch.Tensor)}),
            final_model_selection='fixed terminal budget checkpoint; no validation selection',resume_attempted=bool(args.resume))
        atomic_json(root/('resume-summary.json' if args.resume else 'training-summary.json'),summary)
        atomic_json(root/'worker-exit.json',dict(pid=os.getpid(),status=status,returncode=rc,error=error,finished_epoch=time.time()))
    return rc


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--initial-reference',type=Path)
    args=parser.parse_args(argv)
    from .entry import launched_from_environment
    return train(args,launched_from_environment())


if __name__=='__main__':raise SystemExit(main())
