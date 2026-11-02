"""Real train control flow with CPU-only synthetic batch8 natural episodes.

No real environment, frozen-policy inference, online learning, or GPU work.
Budget, replay, journal durability and collector serialization remain real.
"""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import json
import random
import subprocess
import sys
import time

import numpy as np
import pytest
import torch

from task7_sim.episode import RandomStreams
from task10.runtime import sha256


class SyntheticBatch8:
    instances = []

    def __init__(self, batch, policy=None, *, seed=101, pool=None, run_id='fixture',
                 code_commit='fixture', config_hash='fixture', **kwargs):
        assert batch == 8
        self.batch, self.seed, self.run_id = batch, seed, run_id
        self.code_commit, self.config_hash = code_commit, config_hash
        self.versions = {'fixture': 'CPU-only-v1'}
        self.episodes = SimpleNamespace(batch=batch, streams=RandomStreams(seed, batch),
            pool=Path(pool), profile='fixture-natural', map_backend='fixture', factory=None,
            sampler=SimpleNamespace(entries=[{'id': 'synthetic'}], stats={'accepted': 0}, timing={}),
            kin=SimpleNamespace(dls_cuda_graph=False), core=None, episode_count=None, totals=None,
            proposal_seeds=[None]*batch)
        self.observation = self.candidates = None
        self._pending_result = None
        self.last_timing = {}
        self.reset_rows = []
        self.proposals = torch.zeros(batch, 3)
        type(self).instances.append(self)

    def reset(self, indices=None, *, deadline=None):
        assert self._pending_result is None
        assert time.monotonic() < deadline
        ep = self.episodes
        ids = list(range(8)) if indices is None else list(indices)
        if ep.core is None:
            ep.episode_count = torch.zeros(8, dtype=torch.long)
            ep.totals = {'sensor_frames': torch.zeros(8, dtype=torch.long)}
            ep.core = SimpleNamespace(terminated=torch.zeros(8, dtype=torch.bool),
                truncated=torch.zeros(8, dtype=torch.bool), decisions=torch.zeros(8, dtype=torch.long),
                strict_success=torch.zeros(8, dtype=torch.bool), failures=torch.zeros(8, dtype=torch.long),
                stalls=torch.zeros(8, dtype=torch.long), attempt_time=torch.zeros(8), time=torch.zeros(8),
                state=SimpleNamespace(s=torch.zeros(8)), route=SimpleNamespace(length=torch.ones(8)),
                failure_limit=3)
        else:
            # A mixed end must reset immediately; no active rows may be discarded.
            assert all(bool((ep.core.terminated | ep.core.truncated)[i]) for i in ids)
        for i in ids:
            self.proposals[i] = torch.tensor([int(getattr(ep.streams.for_env(i), p).integers(10000))
                                              for p in ('maps', 'initial', 'other')]) / 10000
        for i in ids: ep.proposal_seeds[i] = tuple(self.proposals[i].tolist())
        ep.episode_count[ids] += 1
        ep.totals['sensor_frames'][ids] += 1
        ep.sampler.stats['accepted'] += len(ids)
        ep.core.decisions[ids] = 0
        ep.core.terminated[ids] = False
        ep.core.truncated[ids] = False
        self.reset_rows.append(ids)
        self.observation = {'vector': self.proposals.clone()}
        self.candidates = {'mask': torch.ones(8, 3, dtype=torch.bool), 'pending': False}
        return self.observation, self.candidates

    def step(self, selected, *, deadline):
        assert self._pending_result is None
        c, ep = self.episodes.core, self.episodes
        assert not bool((c.terminated | c.truncated).any())
        decision_index = c.decisions.clone()
        c.decisions += 1
        ended = c.decisions >= torch.tensor([1]*4 + [2]*4)
        c.terminated = ended & (torch.arange(8) % 2 == 0)
        c.truncated = ended & ~c.terminated
        fields = dict(run_id=self.run_id, environment_id=torch.arange(8),
            episode_id=ep.episode_count.clone(), decision_index=decision_index,
            terminated=c.terminated.clone(), truncated=c.truncated.clone(),
            bootstrap_mask=(~ended).float(), selected=selected.clone(), reward=torch.zeros(8),
            dt=torch.full((8,), .1), candidates={'mask': self.candidates['mask'].clone()},
            next_candidates={'mask': self.candidates['mask'].clone(), 'pending': True},
            attempted_substeps=torch.ones(8, dtype=torch.long),
            committed_substeps=torch.ones(8, dtype=torch.long), map_ids=['synthetic']*8,
            observation={'vector': self.proposals.clone()},
            link=[(int(ep.episode_count[i]), int(decision_index[i])) for i in range(8)])
        result = SimpleNamespace(replay_fields=fields, terminated=c.terminated.clone(),
            truncated=c.truncated.clone(), reward=fields['reward'], info={'timing': {}})
        self._pending_result = result
        return result

    def prepare_next(self, result, *, deadline):
        assert self._pending_result is result
        result.replay_fields['next_candidates']['pending'] = False
        self._pending_result = None
        return result


def install_cpu_fixture(monkeypatch, output):
    import task10.runner as runner
    import task10.lower as lower
    import task10.environment as environment
    import task7_upper.model as upper
    import task7_upper.stages as stages
    from task10.tests.test_learning import model as small_model

    pool = Path(output)/'fixture-pool.json'
    pool.parent.mkdir(parents=True, exist_ok=True)
    if not pool.exists():
        pool.write_text('{}')
    class FakeLower:
        def __init__(self, **kwargs):
            self.actor = torch.nn.Linear(1, 1)
            self.hash_report, self.actor_sha256 = {}, 'fixture'
    class CpuTimers:
        def __init__(self): self.records = {}
        @contextmanager
        def measure(self, name):
            start = time.monotonic()
            try: yield
            finally: self.records.setdefault(name, []).append(time.monotonic()-start)
    def initialize(seed):
        torch.set_num_threads(2)
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    def factory(batch, policy, **kwargs):
        kwargs['pool'] = pool
        return SyntheticBatch8(batch, policy, **kwargs)
    def inputs(obs, candidates, **kwargs):
        return dict(vcm_inputs=dict(observation=(torch.zeros(8, 1), obs['vector']),
            action_result=torch.zeros(8, 23), pose=torch.zeros(8, 3), step=torch.zeros(8, dtype=torch.long),
            env_ids=list(range(8))), geometry=torch.zeros(8, 3, 6), features=torch.ones(8, 3, 19),
            mask=candidates['mask'])
    monkeypatch.setattr(runner, 'initialize', initialize)
    monkeypatch.setattr(runner, 'Timers', CpuTimers)
    monkeypatch.setattr(runner, 'contract', lambda args, policy, unused: dict(
        code_commit='fixture', config_sha256='fixture', gpu='CPU-fixture', physical_gpu='none',
        lower_actor='fixture', lower_hashes={}, code_sha256={}, seed=101))
    monkeypatch.setattr(lower, 'FrozenB3', FakeLower)
    monkeypatch.setattr(environment, 'Task10Env', factory)
    monkeypatch.setattr(upper, 'UpperModel', lambda **kwargs: small_model())
    monkeypatch.setattr(stages, 'environment_inputs', inputs)
    monkeypatch.setattr(stages, 'rebuild_online', lambda model, *args, **kwargs: model.vcm.reset())
    monkeypatch.setattr(runner, 'state_digest', lambda env: __import__('hashlib').sha256(
        env.proposals.numpy().tobytes()).hexdigest())
    monkeypatch.setattr(torch.nn.Module, 'cuda', lambda self, *a, **kw: self)
    original_generator = torch.Generator
    monkeypatch.setattr(torch, 'Generator', lambda device='cpu': original_generator(device='cpu'))
    monkeypatch.setattr(torch.cuda, 'max_memory_allocated', lambda: 0)
    # Learner-only audit is tested elsewhere; it constructs an unrelated full encoder.
    monkeypatch.setattr(runner, 'restore_evidence', lambda *a, **kw: {'fixture': True})
    return runner


def run_fixture(output, *, resume=None, stop=True, reference=False, max_decisions=24):
    with pytest.MonkeyPatch.context() as monkeypatch:
        runner = install_cpu_fixture(monkeypatch, output)
        args = SimpleNamespace(output=Path(output), resume=resume, stop_at_boundary=stop,
            boundary_reference=reference, max_decisions=max_decisions, max_updates=0, seconds=120)
        return runner.train(args, time.monotonic())


def test_real_train_batch8_mixed_reset_then_natural_boundary(tmp_path):
    SyntheticBatch8.instances.clear()
    assert run_fixture(tmp_path) == 0
    saved = torch.load(tmp_path/'collector-boundary.pt', weights_only=False)
    assert saved['counters']['decisions'] == 16
    assert saved['episode_count'].tolist() == [2]*4 + [1]*4
    assert SyntheticBatch8.instances[-1].reset_rows == [list(range(8)), list(range(4))]
    assert saved['ledger_sha256'] == sha256(tmp_path/'training-budget.json')
    assert saved['ledger']['in_flight'] == 0
    assert saved['ledger']['reserved_decisions'] == saved['ledger']['completed_decisions'] == 16
    assert saved['ledger']['updates'] == 0
    assert len(saved['replay']['episodes']) == 12
    assert len(list((tmp_path/'real-executions').glob('*.pt'))) == 2


def test_real_train_batch8_crossprocess_resume_original_deadline_no_duplicate(tmp_path):
    code = 'import sys; from task10.tests.test_runner_boundary import run_fixture; sys.exit(run_fixture(sys.argv[1]))'
    child = subprocess.run([sys.executable, '-c', code, str(tmp_path)], capture_output=True, text=True)
    assert child.returncode == 0, child.stderr + child.stdout
    path = tmp_path/'collector-boundary.pt'
    saved = torch.load(path, weights_only=False)
    old_journals = {p.name: sha256(p) for p in (tmp_path/'real-executions').glob('*.pt')}
    assert run_fixture(tmp_path, resume=path, stop=False) == 0
    summary = json.loads((tmp_path/'resume-summary.json').read_text())
    assert summary['actual_decisions'] == summary['replay_transitions'] == 24
    assert summary['updates'] == 0
    ledger = json.loads((tmp_path/'training-budget.json').read_text())
    assert ledger['reserved_decisions'] == ledger['completed_decisions'] == 24
    assert ledger['in_flight'] == 0
    assert ledger['max_decisions'] == saved['ledger']['max_decisions']
    resumed = [json.loads(line) for line in (tmp_path/'events.jsonl').read_text().splitlines()
               if json.loads(line).get('event') == 'collector_resumed'][-1]
    assert resumed['deadline_monotonic'] == saved['deadline_monotonic']
    assert resumed['started_monotonic'] == saved['started_monotonic']
    journals = sorted((tmp_path/'real-executions').glob('*.pt'))
    assert len(journals) == 3
    identities = []
    for journal in journals:
        fields = torch.load(journal, weights_only=False)['fields']
        for i in range(8):
            identities.append((int(fields['environment_id'][i]), int(fields['episode_id'][i]),
                               int(fields['decision_index'][i])))
    assert len(identities) == len(set(identities)) == 24
    for name, digest in old_journals.items(): assert sha256(tmp_path/'real-executions'/name) == digest
    final = torch.load(journals[-1], weights_only=False)['fields']
    assert final['episode_id'].tolist() == [3]*4 + [2]*4
    assert final['decision_index'].tolist() == [0]*8


def test_real_train_batch8_continuous_reference_then_new_pid_exact(tmp_path):
    code = ('import sys; from task10.tests.test_runner_boundary import run_fixture; '
            'sys.exit(run_fixture(sys.argv[1], reference=True))')
    child = subprocess.run([sys.executable, '-c', code, str(tmp_path)], capture_output=True, text=True)
    assert child.returncode == 0, child.stderr + child.stdout
    saved = torch.load(tmp_path/'collector-boundary.pt', weights_only=False)
    assert saved['ledger_sha256'] == sha256(tmp_path/'training-budget.json')
    reference = torch.load(tmp_path/'boundary-reference.pt', weights_only=False)
    assert reference['real_decisions'] == 8
    assert run_fixture(tmp_path, resume=tmp_path/'collector-boundary.pt', stop=False) == 0
    comparison = json.loads((tmp_path/'boundary-comparison.json').read_text())
    assert comparison['status'] == 'verified'
    assert comparison['next_batch_start_exact']
    assert comparison['next_journal_replay_ledger_exact']
    assert comparison['original_deadline_exact'] and comparison['original_started_exact']
    assert comparison['old_pid'] != comparison['new_pid']
    assert len(list((tmp_path/'real-executions').glob('*.pt'))) == 3
    assert len(list((tmp_path/'continuous-reference'/'real-executions').glob('*.pt'))) == 1
