"""CPU-only evidence contracts; synthetic replay is never real warmup."""
from copy import deepcopy
import json
import random
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch import nn

from task7_upper.model import UpperModel
from task7_upper.vcm import VCM
from task10.learning import EpisodeReplay, Stage1Learner, update_sequences
from task10.recovery import tree_equal
from importlib import import_module


class TinyEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(3, 128)

    def forward(self, observation):
        return self.linear(observation[1])


def setup():
    torch.set_num_threads(2)
    torch.manual_seed(102)
    learner = Stage1Learner(UpperModel(vcm=VCM(f_enc=TinyEncoder())), 200)
    lower = SimpleNamespace(actor=nn.Linear(3, 2).eval().requires_grad_(False))
    replay = EpisodeReplay(1000, seed=101)
    for ep in range(32):
        replay.append(ep, dict(decision_index=0, terminated=torch.tensor(True),
            truncated=torch.tensor(False), bootstrap_mask=torch.tensor(0.),
            selected=torch.tensor(ep % 2), reward=torch.tensor(.2), dt=torch.tensor(.1),
            candidates={'mask': torch.tensor([True, True, False])},
            next_candidates={'mask': torch.tensor([True, True, False])}, marker=ep))
    return learner, lower, replay


def adapter(rows, *, next_state=False):
    n = len(rows)
    vector = torch.tensor([[float(r['marker']) / 32, float(next_state), 1.] for r in rows])
    return dict(vcm_inputs=dict(observation=(torch.zeros(n, 1), vector),
        action_result=torch.zeros(n, 23), pose=torch.zeros(n, 3),
        step=torch.full((n,), int(next_state)), env_ids=list(range(n))),
        geometry=torch.tensor([[[0., 0., 0., 1., 0., 0.],
                               [.8, .2, .1, .9, .7, 0.],
                               [0., 0., 0., 1., 0., 0.]]]).expand(n, -1, -1),
        features=torch.ones(n, 3, 19),
        mask=torch.stack([r['candidates']['mask'] for r in rows]))


def updated(evidence):
    learner, lower, replay = setup()
    before = evidence.snapshot_before(learner, lower)
    result = update_sequences(learner, replay, 1000, adapter)
    return learner, lower, before, result


def test_real_cpu_update_records_separate_heads_and_recomputable_tensors(tmp_path):
    evidence = import_module("task10.training_evidence")
    learner, lower, before, result = updated(evidence)
    payload = evidence.finish_evidence(before, learner, lower, update_result=result)
    summary = payload['summary']
    assert summary['status'] == 'verified_cpu'
    assert not summary['gpu_update_verified'] and not summary['must_stop']
    assert set(summary['heads']) == {'actor', 'q1', 'q2'}
    for head in ('actor', 'q1', 'q2'):
        names = set(payload['before']['heads'][head]['parameters'])
        assert names and all(n.startswith('head_a.' + head + '.') for n in names)
        assert summary['heads'][head]['finite_nonzero_gradient']
        assert summary['heads'][head]['parameters_changed']
        for name in names:
            old = payload['before']['heads'][head]['parameters'][name]
            new = payload['after']['heads'][head]['parameters'][name]
            assert old.device.type == new.device.type == 'cpu'
            assert torch.isfinite(payload['after']['heads'][head]['gradients'][name]).all()
            state = payload['after']['optimizer']['parameters'][name]
            assert state['parameter_device'] == 'cpu'
            assert set(state['state']) >= {'step', 'exp_avg', 'exp_avg_sq'}
    assert summary['lower']['unchanged'] and summary['lower']['no_grad']
    path = tmp_path / 'evidence.pt'
    torch.save(payload, path)
    loaded = torch.load(path, weights_only=True)
    loaded['summary'] = {'corrupt': 'stored summary must not be trusted'}
    assert evidence.summarize_evidence(loaded) == summary
    json.dumps(summary, allow_nan=False)


def test_snapshot_and_finish_do_not_consume_rng_or_mutate_model_state():
    evidence = import_module("task10.training_evidence")
    learner, lower, replay = setup()
    learner.model.eval()
    rng = (random.getstate(), np.random.get_state(), torch.get_rng_state(), replay.rng.getstate())
    state = deepcopy(learner.state_dict())
    flags = [(m.training, [(p.requires_grad, p.grad) for p in m.parameters()])
             for m in (learner.model, lower.actor)]
    before = evidence.snapshot_before(learner, lower)
    evidence.finish_evidence(before, learner, lower, error='not run')
    assert tree_equal(rng, (random.getstate(), np.random.get_state(), torch.get_rng_state(), replay.rng.getstate()))
    assert tree_equal(state, learner.state_dict())
    assert flags == [(m.training, [(p.requires_grad, p.grad) for p in m.parameters()])
                     for m in (learner.model, lower.actor)]


@pytest.mark.parametrize('head', ['actor', 'q1', 'q2'])
def test_each_independent_head_without_nonzero_gradient_must_stop(head):
    evidence = import_module("task10.training_evidence")
    learner, lower, before, result = updated(evidence)
    for p in getattr(learner.model.head_a, head).parameters():
        p.grad = torch.zeros_like(p)
    summary = evidence.finish_evidence(before, learner, lower, update_result=result)['summary']
    assert summary['must_stop'] and not summary['heads'][head]['finite_nonzero_gradient']
    assert not summary['gpu_update_verified']


def test_nonfinite_gradient_and_unchanged_parameters_cannot_pass():
    evidence = import_module("task10.training_evidence")
    learner, lower, before, result = updated(evidence)
    next(learner.model.head_a.q2.parameters()).grad.flatten()[0] = float('nan')
    with torch.no_grad():
        for name, p in learner.model.head_a.actor.named_parameters():
            p.copy_(before['heads']['actor']['parameters']['head_a.actor.' + name])
    summary = evidence.finish_evidence(before, learner, lower, update_result=result)['summary']
    assert summary['must_stop'] and not summary['heads']['q2']['finite_nonzero_gradient']
    assert not summary['heads']['actor']['parameters_changed']
    json.dumps(summary, allow_nan=False)


@pytest.mark.parametrize('violation', ['state', 'grad', 'requires_grad', 'mode'])
def test_b3_state_grad_or_freezing_violation_must_stop(violation):
    evidence = import_module("task10.training_evidence")
    learner, lower, before, result = updated(evidence)
    p = next(lower.actor.parameters())
    if violation == 'state':
        with torch.no_grad():
            p.flatten()[0] += 1
    elif violation == 'grad':
        p.grad = torch.zeros_like(p)  # Even a zero grad is forbidden for B3.
    elif violation == 'requires_grad':
        p.requires_grad_(True)
    else:
        lower.actor.train()
    summary = evidence.finish_evidence(before, learner, lower, update_result=result)['summary']
    assert summary['must_stop'] and not summary['gpu_update_verified']


def test_no_update_and_exception_record_incomplete_instead_of_passing():
    evidence = import_module("task10.training_evidence")
    learner, lower, replay = setup()
    before = evidence.snapshot_before(learner, lower)
    result = update_sequences(learner, replay, 999, adapter)
    summary = evidence.finish_evidence(before, learner, lower, update_result=result)['summary']
    assert summary['status'] == 'incomplete' and summary['must_stop']
    learner, lower, before, result = updated(evidence)
    payload = evidence.finish_evidence(before, learner, lower, update_result=result,
                                       error='write failed after optimizer')
    assert payload['summary']['status'] == 'incomplete'
    assert payload['summary']['must_stop'] and not payload['summary']['gpu_update_verified']


def test_adam_parameter_identity_and_moment_device_are_checked():
    evidence = import_module("task10.training_evidence")
    learner, lower, before, result = updated(evidence)
    p = next(learner.model.head_a.q1.parameters())
    learner.optimizer.state[p]['exp_avg'] = torch.zeros(1)  # Wrong shape.
    summary = evidence.finish_evidence(before, learner, lower, update_result=result)['summary']
    assert summary['must_stop'] and not summary['optimizer']['valid']
    learner.optimizer.param_groups[0]['params'] = [
        q for q in learner.optimizer.param_groups[0]['params'] if q is not p]
    summary = evidence.finish_evidence(before, learner, lower, update_result=result)['summary']
    assert not summary['optimizer']['valid']


def test_offline_recompute_checks_original_adam_devices_and_lower_hashes():
    evidence = import_module("task10.training_evidence")
    learner, lower, before, result = updated(evidence)
    payload = evidence.finish_evidence(before, learner, lower, update_result=result)
    name = 'head_a.q1.0.weight'
    payload['after']['optimizer']['parameters'][name]['state_devices']['exp_avg'] = 'cuda:0'
    summary = evidence.summarize_evidence(payload)
    assert summary['must_stop'] and not summary['optimizer']['valid']
    # Recompute must inspect raw B3 tensors instead of trusting stored hashes.
    payload['after']['lower']['state']['weight'].flatten()[0] += 1
    summary = evidence.summarize_evidence(payload)
    assert not summary['lower']['unchanged']
    assert summary['lower']['before_sha256'] != summary['lower']['after_sha256']


def test_symmetric_candidates_are_not_misreported_as_actor_learning():
    evidence = import_module("task10.training_evidence")
    learner, lower, replay = setup()
    before = evidence.snapshot_before(learner, lower)
    def symmetric(rows, **kwargs):
        item = adapter(rows, **kwargs)
        item['geometry'] = torch.zeros(len(rows), 3, 6)
        return item
    result = update_sequences(learner, replay, 1000, symmetric)
    summary = evidence.finish_evidence(before, learner, lower, update_result=result)['summary']
    assert summary['must_stop'] and summary['status'] == 'failed'
    assert not summary['heads']['actor']['finite_nonzero_gradient']
    assert not summary['heads']['actor']['parameters_changed']
    assert summary['heads']['q1']['parameters_changed']
    assert summary['heads']['q2']['parameters_changed']


def test_unused_non_head_without_adam_state_is_allowed_but_partial_state_rejected():
    evidence = import_module("task10.training_evidence")
    learner, lower, before, result = updated(evidence)
    unused = learner.model.vcm.retrieval.q_proj.weight
    # A branch with no autograd participation has no lazy Adam state.
    unused.grad = None
    learner.optimizer.state.pop(unused, None)
    summary = evidence.finish_evidence(before, learner, lower, update_result=result)['summary']
    assert summary['status'] == 'verified_cpu' and summary['optimizer']['valid']
    learner.optimizer.state[unused] = {'step': torch.tensor(1.)}
    summary = evidence.finish_evidence(before, learner, lower, update_result=result)['summary']
    assert summary['must_stop'] and not summary['optimizer']['valid']
