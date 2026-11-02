"""Task10 checkpoint evidence and fresh-episode collector recovery.

No live Core/environment is pickled. Only a fully committed natural episode
boundary can be resumed; a changed ledger or unfinished reservation is rejected.
"""
from copy import deepcopy
import fcntl
import os
from pathlib import Path
import random
import struct
import time

import numpy as np
import torch

from task7_lower.training import rng_state, restore_rng
from task7_upper.stages import save_checkpoint, load_checkpoint
from .runtime import atomic_torch, Budget, sha256


def tree_equal(a, b):
    if isinstance(a, torch.Tensor):
        return (isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape
                and torch.equal(a.detach().cpu().contiguous().reshape(-1).view(torch.uint8),
                                b.detach().cpu().contiguous().reshape(-1).view(torch.uint8)))
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(tree_equal(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return type(a) is type(b) and len(a) == len(b) and all(tree_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return type(a) is type(b) and struct.pack('d', a) == struct.pack('d', b)
    if isinstance(a, np.generic):
        return type(a) is type(b) and a.tobytes() == b.tobytes()
    return type(a) is type(b) and a == b


def _scalar(value):
    return value.item() if isinstance(value, torch.Tensor) else value


def fragment_identity(items):
    """Include actual source IDs/links, beyond the fragment list's length."""
    return [(f.episode_key, f.start, len(f.steps),
             [(r.get('run_id'), _scalar(r.get('environment_id')), _scalar(r.get('episode_id')),
               _scalar(r['decision_index']), r.get('link')) for r in f.steps]) for f in items]


def _random_draw(device):
    return (random.random(), np.random.random(4), torch.rand(4),
            torch.rand(4, device=device) if device.type == 'cuda' else None)


def verify_learner_checkpoint(path, learner, replay, config, counters, *, learner_factory=None,
                              next_update=None):
    """Verify nonempty sampling and optional next update without advancing caller RNG.

    ``next_update`` is a fixture callback, not permission to fabricate online
    warmup counters. A fresh learner is constructed for each comparison branch.
    """
    from .learning import EpisodeReplay, Stage1Learner
    from task7_upper.model import UpperModel
    entry_rng, entry_replay = rng_state(), replay.state_dict()
    device = next(learner.model.parameters()).device
    if learner_factory is None:
        learner_factory = lambda: Stage1Learner(
            UpperModel(vector_dim=counters['vector_dim']).to(device), learner.total_updates)
    try:
        save_checkpoint(path, learner, replay, counters=counters, config=config)
        count = min(32, len(replay))
        first = replay.sample(count) if count else []
        draw = _random_draw(device)
        other = learner_factory()
        other_replay = EpisodeReplay(capacity=replay.capacity)
        saved, environment = load_checkpoint(path, other, other_replay, config=config)
        second = other_replay.sample(count) if count else []
        if not tree_equal(fragment_identity(first), fragment_identity(second)) or not tree_equal(draw, _random_draw(device)):
            raise AssertionError('checkpoint nonempty sample/RNG mismatch')
        if saved != counters or environment is not None:
            raise AssertionError('checkpoint counter/environment mismatch')
        if not tree_equal(learner.state_dict(), other.state_dict()):
            raise AssertionError('checkpoint learner/optimizer/target/scheduler mismatch')
        optimizer_nonempty = bool(learner.optimizer.state) and learner.updates > 0
        next_result = 'not_verified'
        if next_update is not None:
            if not optimizer_nonempty:
                raise ValueError('next-update evidence requires an already updated optimizer')
            reference = learner_factory()
            reference_replay = EpisodeReplay(capacity=replay.capacity)
            load_checkpoint(path, reference, reference_replay, config=config)
            expected = next_update(reference, reference_replay)
            load_checkpoint(path, other, other_replay, config=config)
            actual = next_update(other, other_replay)
            if not tree_equal(expected, actual) or not tree_equal(reference.state_dict(), other.state_dict()):
                raise AssertionError('restored next update differs')
            next_result = 'verified'
        return dict(learner_rng_next_sample='verified' if count else 'not_verified',
                    sampled_anchors=count, sample_identity=fragment_identity(first), rng=True,
                    counters=True, updates=learner.updates,
                    optimizer_after_update='verified' if optimizer_nonempty else 'not_verified',
                    next_update=next_result, collector_resumable=False,
                    snapshot='offline learner; collector recovery requires natural episode boundary')
    finally:
        replay.load_state_dict(entry_replay)
        restore_rng(entry_rng)


def fixture_update(learner, replay, adapter):
    """Explicit derived fixture batch32; never calls/fakes online warmup logic."""
    from .learning import sequence_outputs
    from task7_upper.stages import runtime, restore_runtime
    fragments = replay.sample(32)
    model = learner.model
    saved, target_saved = runtime(model.vcm), runtime(learner.target.vcm)
    model.train()
    try:
        current, following, rows = sequence_outputs(model, fragments, adapter, gradients=True)
        _, target, target_rows = sequence_outputs(learner.target, fragments, adapter, gradients=False)
        if [id(r) for r in rows] != [id(r) for r in target_rows]:
            raise AssertionError('fixture loss alignment')
        device = next(model.parameters()).device
        batch = {k: torch.stack([torch.as_tensor(r[k]) for r in rows]).to(device)
                 for k in ('selected', 'reward', 'dt', 'terminated', 'truncated', 'bootstrap_mask')}
        batch['selected'] = batch['selected'].long()
        for key, field in (('mask', 'candidates'), ('next_mask', 'next_candidates')):
            batch[key] = torch.stack([r[field]['mask'] for r in rows]).to(device)
        return dict(loss_transitions=len(rows), **learner.update(current, following, target, batch))
    finally:
        restore_runtime(model.vcm, saved)
        restore_runtime(learner.target.vcm, target_saved)


def derived_replay(source):
    """Duplicate exact episodes with provenance, explicitly not new real data."""
    from .learning import EpisodeReplay
    if not len(source):
        raise ValueError('nonempty real source required')
    result = EpisodeReplay(capacity=max(source.capacity, 64), seed=101)
    copy_index = 0
    while len(result) < 32:
        for key, sequence in source.episodes.items():
            for original in sequence:
                item = deepcopy(original)
                item['fixture_provenance'] = dict(kind='derived-replay-copy', source_episode_key=key,
                    source_link=deepcopy(original.get('link')), source_decision_index=int(original['decision_index']),
                    copy_index=copy_index, counts_as_real_decision=False)
                result.append(('derived-fixture', copy_index, key), item)
        copy_index += 1
    return result


def _streams_state(episodes):
    return [{name: deepcopy(getattr(episodes.streams.for_env(i), name).bit_generator.state)
             for name in ('maps', 'initial', 'other')} for i in range(episodes.batch)]


def _restore_streams(episodes, states):
    if len(states) != episodes.batch:
        raise ValueError('sampler batch mismatch')
    for i, state in enumerate(states):
        for name in ('maps', 'initial', 'other'):
            getattr(episodes.streams.for_env(i), name).bit_generator.state = deepcopy(state[name])


def _boundary_contract(env):
    ep = env.episodes
    return dict(batch=env.batch, seed=env.seed, run_id=env.run_id, code_commit=env.code_commit,
                config_hash=env.config_hash, versions=deepcopy(env.versions),
                pool=str(ep.pool), pool_sha256=sha256(ep.pool), profile=ep.profile,
                map_backend=ep.map_backend,
                sampler_entries=None if ep.sampler is None else deepcopy(ep.sampler.entries))


def save_episode_boundary(path, learner, replay, *, environment, policy_generator,
                          budget, config, counters, journal_paths):
    """Save after *all* natural episode ends, journal + replay commit, before reset.

    No abandoned active rows, chunk truncation, pending transition or replaying
    charged decisions is supported. ``journal_paths`` must cover every last row.
    """
    env, ep = environment, environment.episodes
    c = ep.core
    if getattr(ep, 'factory', None) is not None:
        raise ValueError('custom mutable sampling factories are not resumable')
    if c is None or not bool((c.terminated | c.truncated).all()) or env._pending_result is not None:
        raise ValueError('all rows must naturally end and prepare_next must commit first')
    if budget.state['in_flight'] or budget.state['reserved_decisions'] != budget.state['completed_decisions']:
        raise ValueError('unfinished decision reservation')
    if counters['decisions'] != budget.state['completed_decisions'] or counters['updates'] != learner.updates or learner.updates != budget.state['updates']:
        raise ValueError('learner/counter/ledger mismatch')
    journals, covered = [], {}
    for value in journal_paths:
        p = Path(value)
        # Accept only durable readable journals, including callers other than the
        # atomic_torch writer used by the normal train path.
        with p.open('rb') as stream:
            os.fsync(stream.fileno())
            journal = torch.load(stream, map_location='cpu', weights_only=False)
        f = journal['fields']
        for i in range(len(f['episode_id'])):
            identity = (str(f['run_id']), int(f['environment_id'][i]), int(f['episode_id'][i]), int(f['decision_index'][i]))
            if identity in covered:
                raise ValueError('duplicate committed journal transition identity')
            covered[identity] = {key: f[key][i] for key in
                ('terminated', 'truncated', 'selected', 'reward', 'dt', 'bootstrap_mask') if key in f}
        journals.append(dict(path=str(p.resolve()), sha256=sha256(p)))
    for i in range(env.batch):
        key = (env.run_id, i, int(ep.episode_count[i]))
        last = replay.episodes.get(key, [None])[-1]
        identity = (*key, int(c.decisions[i])-1)
        if last is None or int(last['decision_index']) != identity[-1] or not bool(last['terminated'] | last['truncated']) or identity not in covered:
            raise ValueError('last natural transition missing from replay/journal')
        if bool(last['terminated']) != bool(c.terminated[i]) or bool(last['truncated']) != bool(c.truncated[i]):
            raise ValueError('replay terminal flags differ from live core')
        committed = covered[identity]
        for key in ('terminated', 'truncated', 'selected', 'reward', 'dt', 'bootstrap_mask'):
            if key not in committed or not tree_equal(torch.as_tensor(last[key]).cpu(), torch.as_tensor(committed[key]).cpu()):
                raise ValueError(f'journal real transition differs from replay: {key}')
    # Flush keeps elapsed wall time current; the exact ledger digest forbids stale rewind.
    budget.flush()
    payload = dict(format='task10-natural-episode-boundary-v1', config=deepcopy(config),
        counters=deepcopy(counters), learner=deepcopy(learner.state_dict()), replay=replay.state_dict(),
        rng=rng_state(), policy_generator=policy_generator.get_state(),
        policy_generator_device=str(policy_generator.device), contract=_boundary_contract(env),
        streams=_streams_state(ep), episode_count=ep.episode_count.cpu().clone(),
        totals={k: v.cpu().clone() for k, v in ep.totals.items()},
        sampler_stats=None if ep.sampler is None else deepcopy(ep.sampler.stats),
        sampler_timing=None if ep.sampler is None else deepcopy(ep.sampler.timing),
        ledger_path=str(budget.path.resolve()), ledger_sha256=sha256(budget.path),
        ledger=deepcopy(budget.state), started_epoch=time.time()-(time.monotonic()-budget.started),
        started_monotonic=budget.started, deadline_monotonic=budget.deadline,
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), journals=journals,
        boundary='all natural episode ends; next episode not yet sampled')
    atomic_torch(path, payload)
    return dict(collector_resumable=True, boundary=payload['boundary'],
                completed_decisions=counters['decisions'], episode_count=payload['episode_count'].tolist())


def load_episode_boundary(path, learner, replay, *, environment_factory, config,
                          test_only_allow_same_pid=False):
    """Rebuild the *next* episode without resetting global counters or wall clock.

    Validation happens before scene sampling. The old process must have stopped;
    caller owns exclusive ledger access, as with the original single collector.
    """
    state = torch.load(path, map_location='cpu', weights_only=False)
    if state.get('format') != 'task10-natural-episode-boundary-v1' or state['config'] != config:
        raise ValueError('collector boundary/config mismatch')
    ledger_path = Path(state['ledger_path'])
    lock = ledger_path.with_suffix(ledger_path.suffix+'.resume.lock').open('a')
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('another resumed collector owns this ledger')
        # All mutable evidence is checked AFTER exclusive ownership. A caller
        # that observed old evidence before acquiring this lock cannot rewind it.
        if sha256(ledger_path) != state['ledger_sha256']:
            raise ValueError('ledger changed since boundary; refuse budget rewind')
        for item in state['journals']:
            if sha256(item['path']) != item['sha256']:
                raise ValueError('committed journal changed')
        if state['boot_id'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip():
            raise ValueError('host reboot changed monotonic clock; refuse deadline reset')
        old_pid = state['ledger']['pid']
        if old_pid == os.getpid() and not test_only_allow_same_pid:
            raise ValueError('same-PID collector restore is a test-only fixture')
        if old_pid != os.getpid():
            try:
                os.kill(old_pid, 0)
            except ProcessLookupError:
                pass
            else:
                raise ValueError('previous collector PID still exists; stop it before resume')
        budget = Budget.__new__(Budget)
        budget.path, budget.state = ledger_path, deepcopy(state['ledger'])
        budget.started, budget.deadline = state['started_monotonic'], state['deadline_monotonic']
        budget.check()
        budget._resume_lock = lock
        budget.state['pid'] = os.getpid()
        env = environment_factory()
        if env.episodes.core is not None or env.observation is not None or _boundary_contract(env) != state['contract']:
            raise ValueError('fresh environment constructor/identity mismatch')
        learner.load_state_dict(state['learner']); replay.load_state_dict(state['replay'])
        learner.model.vcm.reset(); learner.target.vcm.reset()
        _restore_streams(env.episodes, state['streams'])
        if env.episodes.sampler is not None:
            env.episodes.sampler.stats = deepcopy(state['sampler_stats'])
            env.episodes.sampler.timing = deepcopy(state['sampler_timing'])
        restore_rng(state['rng'])
        generator = torch.Generator(device=state['policy_generator_device'])
        generator.set_state(state['policy_generator'].cpu())
        env.reset(deadline=budget.deadline)
        ep = env.episodes
        ep.episode_count.copy_(state['episode_count'].to(ep.episode_count.device)+1)
        for key in ep.totals:
            ep.totals[key] += state['totals'][key].to(ep.totals[key].device)
        budget.check()
        return dict(counters=deepcopy(state['counters']), environment=env,
                    policy_generator=generator, budget=budget, histories=[[] for _ in range(env.batch)])
    except BaseException:
        lock.close()
        raise


def mismatch_report(left, right, prefix='root'):
    """Exact diagnostic only: list every differing leaf and its magnitude."""
    result = []
    if isinstance(left, dict) and isinstance(right, dict):
        for key in left.keys() | right.keys():
            if key not in left or key not in right:
                result.append(dict(path=f'{prefix}.{key}', reason='missing key'))
            else:
                result.extend(mismatch_report(left[key], right[key], f'{prefix}.{key}'))
    elif isinstance(left, (tuple, list)) and isinstance(right, type(left)) and len(left) == len(right):
        for i, (a, b) in enumerate(zip(left, right)):
            result.extend(mismatch_report(a, b, f'{prefix}[{i}]'))
    elif not tree_equal(left, right):
        entry = dict(path=prefix, bitwise_equal=False)
        if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor) and left.shape == right.shape:
            a, b = left.detach().cpu().double(), right.detach().cpu().double()
            entry.update(shape=list(left.shape), dtype=str(left.dtype),
                max_abs=float((a-b).abs().max()) if a.numel() else 0.,
                different_elements=int((a != b).sum()), finite=bool(torch.isfinite(a).all() and torch.isfinite(b).all()))
        elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
            entry.update(left=float(left), right=float(right), abs_difference=abs(float(left)-float(right)))
        else:
            entry.update(reason='non-tensor unequal', left=str(left)[:200], right=str(right)[:200])
        result.append(entry)
    return result
