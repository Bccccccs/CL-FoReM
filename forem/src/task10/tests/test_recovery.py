"""CPU deterministic checkpoint fixtures; no real collection or GPU training."""
from copy import deepcopy
import json
from types import SimpleNamespace
import time
import numpy as np
import pytest
import torch

from task7_lower.training import rng_state
from task7_sim.episode import RandomStreams
from task10.learning import EpisodeReplay, Stage1Learner
from task10.recovery import (verify_learner_checkpoint, tree_equal, fixture_update,
    derived_replay, save_episode_boundary, load_episode_boundary)
from task10.runtime import Budget, atomic_torch
from task10.tests.test_learning import model, transition, adapter


@pytest.mark.parametrize('count', [0, 1, 16, 32])
def test_nonempty_identity_or_explicit_not_verified_and_no_rng_side_effect(tmp_path, count):
    torch.set_num_threads(2)
    learner = Stage1Learner(model(), 200)
    replay = EpisodeReplay(1000, seed=101)
    for i in range(count):
        replay.append(('real-fixture', i, 1), transition(0, end=True, marker=i))
    before_rng, before_replay = rng_state(), replay.state_dict()
    evidence = verify_learner_checkpoint(tmp_path/'learner.pt', learner, replay, {},
        {'decisions': count}, learner_factory=lambda: Stage1Learner(model(), 200))
    assert evidence['sampled_anchors'] == count
    assert evidence['learner_rng_next_sample'] == ('verified' if count else 'not_verified')
    assert len(evidence['sample_identity']) == count
    assert evidence['optimizer_after_update'] == 'not_verified'
    assert tree_equal(rng_state(), before_rng) and tree_equal(replay.state_dict(), before_replay)
    assert not replay.ready(count)  # No fabricated online warmup count.


def test_updated_optimizer_and_exact_next_update_on_derived_fixture(tmp_path):
    torch.set_num_threads(2)
    replay = EpisodeReplay(1000, seed=101)
    for i in range(16):
        replay.append(('real-source', i, 1), transition(0, end=True, marker=i))
    fixture = derived_replay(replay)
    assert len(fixture) == 32 and len(replay) == 16
    assert all(not r['fixture_provenance']['counts_as_real_decision']
               for seq in fixture.episodes.values() for r in seq)
    learner = Stage1Learner(model(), 200)
    fixture_update(learner, fixture, adapter)
    before, before_rng, before_replay = deepcopy(learner.state_dict()), rng_state(), fixture.state_dict()
    report = verify_learner_checkpoint(tmp_path/'updated.pt', learner, fixture, {},
        {'decisions': 16, 'updates': 1}, learner_factory=lambda: Stage1Learner(model(), 200),
        next_update=lambda l, r: fixture_update(l, r, adapter))
    assert report['optimizer_after_update'] == report['next_update'] == 'verified'
    assert tree_equal(before, learner.state_dict())
    assert tree_equal(before_rng, rng_state()) and tree_equal(before_replay, fixture.state_dict())


class BoundaryFixture:
    """Explicit synthetic sampler facade; never a physical environment result."""
    def __init__(self, pool, *, ended=False):
        self.batch, self.seed, self.run_id = 1, 101, 'fixture-only'
        self.code_commit, self.config_hash, self.versions = 'fixture', 'fixture', {'fixture': True}
        sampler = SimpleNamespace(entries=[{'id': 'fixture'}], stats={'accepted': 1}, timing={'sample_s': 0.})
        self.episodes = SimpleNamespace(batch=1, streams=RandomStreams(101, 1), pool=pool,
            profile='fixture', map_backend='fixture', sampler=sampler,
            episode_count=torch.tensor([1]) if ended else None,
            totals={'sensor_frames': torch.tensor([2])} if ended else None,
            core=SimpleNamespace(terminated=torch.tensor([True]), truncated=torch.tensor([False]),
                                 decisions=torch.tensor([1])) if ended else None)
        self._pending_result = None
        self.observation = {} if ended else None

    def reset(self, deadline):
        assert time.monotonic() < deadline
        ep = self.episodes
        self.observation = {'next_proposal': tuple(int(getattr(ep.streams.for_env(0), p).integers(1000000))
                             for p in ('maps', 'initial', 'other'))}
        ep.episode_count = torch.tensor([1])
        ep.totals = {'sensor_frames': torch.tensor([1])}
        ep.core = SimpleNamespace(terminated=torch.tensor([False]), truncated=torch.tensor([False]))
        ep.sampler.stats['accepted'] += 1


def boundary_setup(tmp_path):
    pool = tmp_path/'pool.json'; pool.write_text('{}')
    env = BoundaryFixture(pool, ended=True)
    for purpose in ('maps', 'initial', 'other'):
        getattr(env.episodes.streams.for_env(0), purpose).integers(1000, size=3)
    replay = EpisodeReplay(1000, seed=101)
    replay.append(('fixture-only', 0, 1), transition(0, end=True))
    learner = Stage1Learner(model(), 200)
    budget = Budget(tmp_path/'budget.json', started=time.monotonic(), seconds=60, decisions=4)
    budget.reserve(1); budget.complete(1)
    journal = tmp_path/'journal.pt'
    atomic_torch(journal, {'fields': dict(run_id='fixture-only', environment_id=torch.tensor([0]),
        episode_id=torch.tensor([1]), decision_index=torch.tensor([0]))})
    generator = torch.Generator().manual_seed(101)
    return env, learner, replay, budget, journal, generator


def test_episode_boundary_rebuild_same_next_proposal_ids_generator_and_budget(tmp_path):
    env, learner, replay, budget, journal, generator = boundary_setup(tmp_path)
    path = tmp_path/'boundary.pt'
    save_episode_boundary(path, learner, replay, environment=env, policy_generator=generator,
        budget=budget, config={}, counters={'decisions': 1, 'updates': 0}, journal_paths=[journal])
    expected_proposal = tuple(int(getattr(env.episodes.streams.for_env(0), p).integers(1000000))
                              for p in ('maps', 'initial', 'other'))
    expected_policy = torch.rand(3, generator=generator)
    restored = load_episode_boundary(path, learner, replay,
        environment_factory=lambda: BoundaryFixture(env.episodes.pool), config={},
        test_only_allow_same_pid=True)
    actual = restored['environment']
    assert actual.observation['next_proposal'] == expected_proposal
    assert actual.episodes.episode_count.tolist() == [2]
    assert actual.episodes.totals['sensor_frames'].tolist() == [3]
    assert torch.equal(torch.rand(3, generator=restored['policy_generator']), expected_policy)
    resumed = restored['budget']
    assert resumed.state['reserved_decisions'] == resumed.state['completed_decisions'] == 1
    assert resumed.deadline <= budget.deadline+.01
    resumed.reserve(1); resumed.complete(1)
    assert resumed.state['completed_decisions'] == 2
    resumed._resume_lock.close()
    with pytest.raises(ValueError, match='ledger changed'):
        load_episode_boundary(path, learner, replay,
            environment_factory=lambda: BoundaryFixture(env.episodes.pool), config={},
        test_only_allow_same_pid=True)


@pytest.mark.parametrize('condition', ['active', 'pending', 'in_flight', 'missing_journal', 'missing_replay'])
def test_episode_boundary_rejects_uncommitted_or_unnatural_boundaries(tmp_path, condition):
    env, learner, replay, budget, journal, generator = boundary_setup(tmp_path)
    if condition == 'active': env.episodes.core.terminated[:] = False
    if condition == 'pending': env._pending_result = object()
    if condition == 'in_flight': budget.reserve(1)
    if condition == 'missing_replay': replay = EpisodeReplay(1000)
    with pytest.raises(ValueError):
        save_episode_boundary(tmp_path/'bad.pt', learner, replay, environment=env,
            policy_generator=generator, budget=budget, config={},
            counters={'decisions': 1, 'updates': 0},
            journal_paths=[] if condition == 'missing_journal' else [journal])


def test_resumed_collector_excludes_second_owner_even_before_next_decision(tmp_path):
    env, learner, replay, budget, journal, generator = boundary_setup(tmp_path)
    path = tmp_path/'boundary.pt'
    save_episode_boundary(path, learner, replay, environment=env, policy_generator=generator,
        budget=budget, config={}, counters={'decisions': 1, 'updates': 0}, journal_paths=[journal])
    first = load_episode_boundary(path, learner, replay,
        environment_factory=lambda: BoundaryFixture(env.episodes.pool), config={},
        test_only_allow_same_pid=True)
    with pytest.raises(ValueError, match='another resumed collector'):
        load_episode_boundary(path, learner, replay,
            environment_factory=lambda: BoundaryFixture(env.episodes.pool), config={},
        test_only_allow_same_pid=True)
    first['budget']._resume_lock.close()


def test_strict_restore_rejects_same_pid_and_releases_lock(tmp_path):
    env, learner, replay, budget, journal, generator = boundary_setup(tmp_path)
    path = tmp_path/'boundary.pt'
    save_episode_boundary(path, learner, replay, environment=env, policy_generator=generator,
        budget=budget, config={}, counters={'decisions': 1, 'updates': 0}, journal_paths=[journal])
    with pytest.raises(ValueError, match='same-PID'):
        load_episode_boundary(path, learner, replay,
            environment_factory=lambda: BoundaryFixture(env.episodes.pool), config={})
    # A rejected load released its lock, so an explicit synthetic fixture can run.
    restored = load_episode_boundary(path, learner, replay,
        environment_factory=lambda: BoundaryFixture(env.episodes.pool), config={},
        test_only_allow_same_pid=True)
    restored['budget']._resume_lock.close()


def test_ledger_change_at_lock_acquisition_is_rejected_without_reset(tmp_path, monkeypatch):
    import task10.recovery as recovery
    env, learner, replay, budget, journal, generator = boundary_setup(tmp_path)
    path = tmp_path/'boundary.pt'
    save_episode_boundary(path, learner, replay, environment=env, policy_generator=generator,
        budget=budget, config={}, counters={'decisions': 1, 'updates': 0}, journal_paths=[journal])
    real_flock = recovery.fcntl.flock
    def prior_owner_commits_then_lock_is_obtained(file, operation):
        # Deterministic TOCTOU reproduction: another owner commits between the
        # stale checkpoint read and successful lock acquisition.
        budget.reserve(1); budget.complete(1)
        return real_flock(file, operation)
    monkeypatch.setattr(recovery.fcntl, 'flock', prior_owner_commits_then_lock_is_obtained)
    def forbidden_factory():
        raise AssertionError('stale snapshot must fail before constructing/resetting')
    with pytest.raises(ValueError, match='ledger changed'):
        load_episode_boundary(path, learner, replay, environment_factory=forbidden_factory,
            config={}, test_only_allow_same_pid=True)
    assert json.loads(budget.path.read_text())['completed_decisions'] == 2
    # Rejection closed the descriptor; no stale owner holds the ledger lock.
    with budget.path.with_suffix('.json.resume.lock').open('a') as lock:
        real_flock(lock, recovery.fcntl.LOCK_EX | recovery.fcntl.LOCK_NB)


def test_child_save_exit_then_new_pid_rebuilds_and_continues_original_budget(tmp_path):
    import subprocess
    import sys
    code = '''
from pathlib import Path
import sys
from task10.tests.test_recovery import boundary_setup
from task10.recovery import save_episode_boundary
p=Path(sys.argv[1])
env, learner, replay, budget, journal, generator=boundary_setup(p)
save_episode_boundary(p/'child-boundary.pt',learner,replay,environment=env,
    policy_generator=generator,budget=budget,config={},counters={'decisions':1,'updates':0},
    journal_paths=[journal])
'''
    child = subprocess.run([sys.executable, '-c', code, str(tmp_path)], capture_output=True, text=True)
    assert child.returncode == 0, child.stderr
    learner, replay = Stage1Learner(model(), 200), EpisodeReplay(1000)
    restored = load_episode_boundary(tmp_path/'child-boundary.pt', learner, replay,
        environment_factory=lambda: BoundaryFixture(tmp_path/'pool.json'), config={})
    assert restored['environment'].episodes.episode_count.tolist() == [2]
    budget = restored['budget']
    budget.reserve(1); budget.complete(1)
    assert budget.state['completed_decisions'] == 2
    budget._resume_lock.close()
    with pytest.raises(ValueError, match='ledger changed'):
        load_episode_boundary(tmp_path/'child-boundary.pt', learner, replay,
            environment_factory=lambda: BoundaryFixture(tmp_path/'pool.json'), config={})
