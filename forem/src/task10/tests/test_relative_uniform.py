"""Bounded CPU algebra/config/checkpoint checks; no real interaction or train run."""
from copy import deepcopy
import json
import math
from pathlib import Path

import pytest
import torch

from task7_upper.sac_discrete import distribution, DiscreteSAC
from task10.entry import ROOT, resolve_profile
from task10.learning import (Stage1Learner, bellman, objective_contract,
                             RELATIVE_UNIFORM_ALPHA, EpisodeReplay)
from task10.runner import create_learner
from task10.tests.test_learning import model, make_replay


@pytest.mark.parametrize('n', [1, 2, 5])
def test_uniform_is_zero_and_padding_is_ignored(n):
    mask = torch.tensor([[True]*n + [False, False]])
    logits = torch.tensor([[0.]*n + [float('nan'), float('nan')]], dtype=torch.float64)
    q = torch.tensor([[2.]*n + [float('nan'), float('nan')]], dtype=torch.float64)
    value = bellman(torch.zeros(1), torch.ones(1), torch.zeros(1), logits, q, q, mask, .35,
                    objective='relative_uniform')
    torch.testing.assert_close(value, torch.tensor([2.], dtype=torch.float64))


def test_nonuniform_expected_regularizer_is_nonpositive_and_dt_terminal_unchanged():
    mask = torch.tensor([[True, True, False], [True, True, True], [False, True, False]])
    logits = torch.tensor([[2., -1., float('nan')], [3., 0., -2.], [float('nan'), 2., float('nan')]], dtype=torch.float64)
    q = torch.tensor([[1., 2., float('nan')], [0., 2., -1.], [float('nan'), 7., float('nan')]], dtype=torch.float64)
    p, logp = distribution(logits, mask)
    regularizer = -.35 * (p*(logp + mask.sum(-1).double().log()[:, None])).sum(-1)
    assert (regularizer <= 0).all()
    reward, bm, dt = torch.tensor([0., -.4, 1.]), torch.tensor([1., 0., 1.]), torch.tensor([0., .1, .05])
    relative = bellman(reward, bm, dt, logits, q, q, mask, .35, objective='relative_uniform')
    legacy = bellman(reward, bm, dt, logits, q, q, mask, .35)
    torch.testing.assert_close(relative, reward + bm*(.99**(dt/.1))*((p*q.masked_fill(~mask, 0.)).sum(-1)+regularizer))
    torch.testing.assert_close(relative-legacy, -bm*(.99**(dt/.1))*.35*mask.sum(-1).double().log())
    assert relative[1] == pytest.approx(-.4)


def test_actor_relative_autograd_matches_legacy_and_analytic_gradient():
    mask = torch.tensor([[True, True, False], [True, True, True]])
    logits = torch.tensor([[1., -2., 50.], [-.4, 0., .6]], dtype=torch.float64, requires_grad=True)
    q = torch.tensor([[.3, -.2, 900.], [-.5, 2., .1]], dtype=torch.float64)
    p, logp = distribution(logits, mask)
    base = .35*logp-q.masked_fill(~mask, 0.)
    old = (p*base).sum(-1).mean()
    relative = (p*(base+.35*mask.sum(-1).double().log()[:, None])).sum(-1).mean()
    old_grad, = torch.autograd.grad(old, logits, retain_graph=True)
    actual, = torch.autograd.grad(relative, logits)
    analytic = p*(base-(p*base).sum(-1, keepdim=True))/len(mask)
    torch.testing.assert_close(actual, old_grad)
    torch.testing.assert_close(actual, analytic)
    assert actual[0, 2] == 0


def outputs_and_batch(learner):
    mask = torch.tensor([[True, True, False], [True, True, True]])
    out = learner.model(torch.zeros(2, 128), torch.zeros(2, 3, 6), torch.ones(2, 3, 19), mask)
    nxt = {k: v.detach().clone() for k, v in out.items() if isinstance(v, torch.Tensor)}
    batch = dict(reward=torch.tensor([0., -.4]), bootstrap_mask=torch.tensor([1., 0.]),
                 dt=torch.tensor([0., .1]), selected=torch.tensor([0, 1]), mask=mask, next_mask=mask)
    return out, nxt, batch


def test_actual_adapter_critic_actor_and_fixed_temperature():
    learner = Stage1Learner(model(), 200, objective='relative_uniform')
    assert not hasattr(learner.temperature, 'optimizer')
    assert not learner.temperature.log_alpha.requires_grad
    before_temp = deepcopy(learner.temperature.state_dict())
    out, nxt, batch = outputs_and_batch(learner)
    y = bellman(batch['reward'], batch['bootstrap_mask'], batch['dt'], nxt['logits'],
                nxt['q1'], nxt['q2'], batch['next_mask'], learner.temperature.alpha,
                objective='relative_uniform')
    qloss = .5*sum((out[k].detach().gather(-1, batch['selected'][:, None]).squeeze(-1)-y).square().mean() for k in ('q1', 'q2'))
    p, logp = distribution(out['logits'].detach(), batch['mask'])
    aq = torch.minimum(out['actor_q1'], out['actor_q2']).detach().masked_fill(~batch['mask'], 0.)
    actor = (p*(learner.temperature.alpha*(logp+batch['mask'].sum(-1).float().log()[:, None])-aq)).sum(-1).mean()
    result = learner.update(out, nxt, nxt, batch)
    assert result['critic'] == pytest.approx(float(qloss))
    assert result['actor'] == pytest.approx(float(actor), abs=1e-7)
    assert result['temperature_loss'] == 0 and result['alpha'] == pytest.approx(.35)
    assert learner.temperature.state_dict() == before_temp
    assert learner.updates == 1


def test_legacy_path_is_identical_to_unmodified_discrete_sac():
    legacy = Stage1Learner(model(), 200)
    reference = DiscreteSAC(model(), 200)
    out, nxt, batch = outputs_and_batch(legacy)
    ref_out, ref_nxt, _ = outputs_and_batch(reference)
    expected = reference.update(ref_out, ref_nxt, ref_nxt, dict(batch, terminated=~batch['bootstrap_mask'].bool()))
    actual = legacy.update(out, nxt, nxt, batch)
    assert actual == expected
    assert all(torch.equal(v, reference.model.state_dict()[k]) for k, v in legacy.model.state_dict().items())


def test_checkpoint_objective_version_alpha_and_history_rejection_before_mutation():
    legacy, relative = Stage1Learner(model(), 200), Stage1Learner(model(), 200, objective='relative_uniform')
    old = legacy.state_dict()
    old.pop('learning_objective'); old.pop('alpha')
    legacy.load_state_dict(old)
    for receiver, state in ((relative, old), (legacy, relative.state_dict()), (relative, legacy.state_dict())):
        before = deepcopy(receiver.model.state_dict())
        with pytest.raises(ValueError, match='objective'):
            receiver.load_state_dict(state)
        assert all(torch.equal(before[k], v) for k, v in receiver.model.state_dict().items())
    restored = Stage1Learner(model(), 200, objective='relative_uniform')
    restored.load_state_dict(relative.state_dict())
    assert restored.state_dict()['learning_objective'] == objective_contract('relative_uniform')
    for key, value in [('alpha', .2), ('learning_objective', dict(objective_contract('relative_uniform'), version='unknown'))]:
        invalid = deepcopy(relative.state_dict()); invalid[key] = value
        with pytest.raises(ValueError):
            restored.load_state_dict(invalid)
    invalid = deepcopy(relative.state_dict()); invalid['temperature']['alpha'] = .2
    with pytest.raises(ValueError, match='temperature'):
        restored.load_state_dict(invalid)


def test_normal_config_entry_factory_and_registered_path_only(tmp_path):
    path = ROOT/'config/task10/relative_uniform_trial.json'
    resolved = resolve_profile(run_profile='online-trial', config=path)
    assert resolved['seconds'] == 25200 and resolved['limits']['decisions'] == 1200
    learner = create_learner(model(), 200, resolved['config'])
    assert learner.learning_objective == objective_contract('relative_uniform')
    assert learner.temperature.alpha == pytest.approx(.35)
    assert create_learner(model(), 200, resolve_profile()['config']).learning_objective == objective_contract('legacy')
    copied = tmp_path/'copied.json'; copied.write_text(path.read_text())
    with pytest.raises(ValueError, match='configuration differs'):
        resolve_profile(run_profile='online-trial', config=copied)
    changed = json.loads(path.read_text()); changed['alpha'] = .2
    with pytest.raises(ValueError, match='fixed alpha'):
        create_learner(model(), 200, changed)


def test_default_recovery_factory_preserves_new_objective(tmp_path, monkeypatch):
    from task10.recovery import verify_learner_checkpoint
    import task7_upper.model as model_module
    monkeypatch.setattr(model_module, 'UpperModel', lambda vector_dim: model())
    learner = Stage1Learner(model(), 200, objective='relative_uniform')
    replay = make_replay()
    report = verify_learner_checkpoint(tmp_path/'checkpoint.pt', learner, replay,
                                      {'objective': 'relative_uniform'}, {'vector_dim': 3, 'decisions': 0})
    assert report['learner_rng_next_sample'] == 'verified'
    assert learner.updates == 0 and len(replay) == 32


def test_normal_train_passes_selected_config_to_factory_before_any_collection(tmp_path, monkeypatch):
    """Execute train's setup with CPU stubs; stop at learner creation, before loop."""
    from types import SimpleNamespace
    import time
    import task10.runner as runner
    import task10.lower as lower
    import task10.environment as environment
    import task7_upper.model as upper
    import task7_upper.stages as stages
    class SetupComplete(BaseException):
        pass
    class StubEnv:
        def __init__(self, *args, **kwargs):
            self.episodes = SimpleNamespace(kin=SimpleNamespace(), core=SimpleNamespace(failure_limit=1))
            self.last_timing = {}
        def reset(self, **kwargs):
            return {}, {}
    start, epoch = time.monotonic(), time.time()
    monkeypatch.setenv('TASK10_STARTED_EPOCH', str(epoch))
    monkeypatch.setenv('TASK10_HARD_DEADLINE_MONOTONIC', str(start+25200))
    monkeypatch.setenv('TASK10_HARD_DEADLINE_EPOCH', str(epoch+25200))
    monkeypatch.setattr(runner, 'initialize', lambda seed: None)
    monkeypatch.setattr(torch.cuda, 'synchronize', lambda: None)
    monkeypatch.setattr(torch.cuda, 'max_memory_allocated', lambda: 0)
    monkeypatch.setattr(torch.nn.Module, 'cuda', lambda self: self)
    monkeypatch.setattr(upper, 'UpperModel', lambda **kwargs: model())
    monkeypatch.setattr(lower, 'FrozenB3', lambda **kwargs: SimpleNamespace(actor=torch.nn.Linear(1, 1)))
    monkeypatch.setattr(environment, 'Task10Env', StubEnv)
    monkeypatch.setattr(stages, 'environment_inputs', lambda *args, **kwargs: dict(
        vcm_inputs={'observation': (torch.zeros(8, 1), torch.zeros(8, 3))},
        geometry=torch.zeros(8, 3, 6), features=torch.zeros(8, 3, 19), mask=torch.ones(8, 3, dtype=torch.bool)))
    path = ROOT/'config/task10/relative_uniform_trial.json'
    resolved = resolve_profile(run_profile='online-trial', config=path)
    monkeypatch.setattr(runner, 'contract', lambda *args: dict(code_commit='fixture', config_sha256='fixture',
        gpu='cpu-stub', physical_gpu='none', config=resolved['config']))
    captured = []
    original = runner.create_learner
    def capture(model, total_updates, config):
        captured.append(original(model, total_updates, config))
        raise SetupComplete()
    monkeypatch.setattr(runner, 'create_learner', capture)
    args = SimpleNamespace(output=tmp_path/'setup', run_profile='online-trial', config=path,
        seconds=None, max_decisions=None, max_updates=None)
    with pytest.raises(SetupComplete):
        runner.train(args, start)
    assert len(captured) == 1
    assert captured[0].learning_objective == objective_contract('relative_uniform')
    assert captured[0].updates == 0
    summary = json.loads((args.output/'training-summary.json').read_text())
    assert summary['actual_decisions'] == summary['updates'] == 0
