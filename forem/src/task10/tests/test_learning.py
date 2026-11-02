"""Deterministic task10.2 protocol checks; no environment sampling or training run."""
from copy import deepcopy
import math
import random
import numpy as np
import pytest
import torch
from torch import nn
from task7_upper.model import UpperModel
from task7_upper.vcm import VCM
from task7_upper.stages import save_checkpoint, load_checkpoint
from task10.learning import (
    attempt_reward, bellman, EpisodeReplay, Stage1Learner, sequence_outputs,
    update_sequences,
)


class SmallEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(3, 128)

    def forward(self, observation):
        return self.linear(observation[1])


def model():
    torch.manual_seed(102)
    return UpperModel(vcm=VCM(f_enc=SmallEncoder()))


def transition(t, *, end=False, truncated=False, marker=0):
    return dict(decision_index=t, terminated=torch.tensor(end and not truncated),
                truncated=torch.tensor(truncated), bootstrap_mask=torch.tensor(float(not end)),
                selected=torch.tensor(t % 2), reward=torch.tensor(.2), dt=torch.tensor(.1),
                candidates={'mask': torch.tensor([True, True, False])},
                next_candidates={'mask': torch.tensor([True, True, False])},
                marker=marker)


def adapter(rows, *, next_state=False):
    times = torch.tensor([r['decision_index'] + int(next_state) for r in rows])
    vector = torch.stack((times.float() / 10, torch.ones(len(rows)),
                          torch.tensor([r['marker'] for r in rows], dtype=torch.float)), -1)
    return dict(vcm_inputs=dict(observation=(torch.zeros(len(rows), 1), vector),
                               action_result=torch.zeros(len(rows), 23),
                               pose=torch.zeros(len(rows), 3), step=times,
                               env_ids=list(range(len(rows)))),
                geometry=torch.zeros(len(rows), 3, 6), features=torch.ones(len(rows), 3, 19),
                mask=torch.stack([r['next_candidates' if next_state else 'candidates']['mask'] for r in rows]))


def make_replay():
    replay = EpisodeReplay(1000, seed=101)
    for ep in range(32):
        replay.append(ep, transition(0, end=True, marker=ep))
    return replay


def test_failed_zero_commit_uses_attempt_clock_and_terminal_potential():
    result = attempt_reward(.2, .4, 1., 2)
    assert result['dt'] == pytest.approx(.1)
    assert result['discount'] == pytest.approx(.99)
    assert result['reward'] == pytest.approx(.99 * .4 - .2)
    failed = attempt_reward(.4, .8, 1., 3, terminated=True)
    assert failed['base_reward'] == 0 and failed['bootstrap_mask'] == 0
    assert failed['reward'] == pytest.approx(-.4)
    # No committed-time input exists: a rejected attempt still advances dt.
    assert failed['dt'] == pytest.approx(.15)
    with pytest.raises(ValueError):
        attempt_reward(0, 0, 0, 1)
    with pytest.raises(ValueError):
        attempt_reward(0, 0, 1, -1)


@pytest.mark.parametrize('terminated,truncated,success', [(True, False, True),
                         (True, False, False), (False, True, False)])
def test_strict_success_and_task_limits_disable_bootstrap(terminated, truncated, success):
    r = attempt_reward(.7, 1., 1., 1, terminated=terminated,
                       truncated=truncated, strict_success=success)
    assert r['base_reward'] == float(success)
    assert r['bootstrap_mask'] == 0
    assert r['reward'] == pytest.approx(float(success) - .7)
    if success:
        again = attempt_reward(.7, 1., 1., 1, terminated=True,
                               strict_success=True, success_already=True)
        assert again['base_reward'] == 0


def test_potential_telescopes_to_initial_for_failed_and_successful_episodes():
    for success in (False, True):
        first = attempt_reward(.1, .6, 1., 2)
        last = attempt_reward(.6, .9, 1., 4, truncated=True, strict_success=success)
        assert first['reward'] + first['discount'] * last['reward'] == pytest.approx(
            -.1 + first['discount'] * int(success))


def test_single_valid_slot_bellman_and_independent_mask():
    logits = torch.tensor([[float('nan'), 7., float('nan')]]).expand(4, -1)
    q1 = torch.tensor([[float('nan'), 2., float('nan')]]).expand(4, -1)
    q2 = torch.tensor([[float('nan'), 3., float('nan')]]).expand(4, -1)
    mask = torch.tensor([[False, True, False]]).expand(4, -1)
    target = bellman(torch.ones(4), torch.tensor([1., 0., 0., 1.]),
                     torch.tensor([.1, .1, .05, .05]), logits, q1, q2, mask, .35)
    torch.testing.assert_close(target, torch.tensor([1 + .99 * 2, 1., 1., 1 + .99 ** .5 * 2]))


def test_short_replay_all_starts_and_no_cross_episode_or_padding():
    replay = make_replay()
    assert not replay.ready(999) and replay.ready(1000)
    fragments = replay.sample()
    assert len(fragments) == 32
    assert {f.episode_key for f in fragments} == set(range(32))
    assert all(len(f.steps) == 1 and not f.prefix and not f.burn_in for f in fragments)
    assert all(f.steps[0]['marker'] == f.episode_key for f in fragments)
    assert all(f.start == 0 for f in fragments)
    with pytest.raises(ValueError, match='episode end'):
        replay.append(0, transition(1))
    with pytest.raises(ValueError, match='initial'):
        replay.append('bad', transition(2))
    long = EpisodeReplay(100)
    for t in range(14):
        long.append('long', transition(t, end=t == 13))
    fragment = long.fragment('long', 6)
    assert [r['decision_index'] for r in fragment.prefix] == [0, 1]
    assert [r['decision_index'] for r in fragment.burn_in] == [2, 3, 4, 5]
    assert [r['decision_index'] for r in fragment.steps] == list(range(6, 14))
    assert len(long.starts()) == 14


def test_capacity_retains_initial_history_and_rejects_latents():
    replay = EpisodeReplay(10)
    for ep in range(3):
        for t in range(4):
            replay.append(ep, transition(t, end=t == 3))
    assert len(replay) == 8 and list(replay.episodes) == [1, 2]
    assert all(seq[0]['decision_index'] == 0 for seq in replay.episodes.values())
    with pytest.raises(ValueError, match='latent'):
        replay.append('bad', {**transition(0), 'hidden': torch.zeros(128)})


def test_sequence_reconstructs_whole_prefix_without_dropping_first_four_losses():
    replay = EpisodeReplay(100)
    for t in range(14):
        replay.append('a', transition(t, end=t == 13))
    m = model()
    captured = []
    handle = m.vcm.register_forward_hook(lambda module, args, out: captured.append(out.requires_grad))
    current, following, rows = sequence_outputs(m, [replay.fragment('a', 6)], adapter, gradients=True)
    handle.remove()
    assert len(rows) == len(current['q1']) == len(following['q1']) == 8
    assert captured[:6] == [False] * 6
    assert captured[6:] == [True, False] * 8
    assert [int(entry.step) for entry in m.vcm.memory[0]] == [10, 11, 12, 13]
    reference = model()
    with torch.no_grad():
        for t in range(14):
            expected = reference.forward_step(**adapter([transition(t)]))
    torch.testing.assert_close(current['q1'][-1], expected['q1'][0])
    initial, _, rows = sequence_outputs(m, [replay.fragment('a', 0)], adapter, gradients=True)
    assert len(rows) == 8 and rows[0]['decision_index'] == 0
    assert initial['q1'].requires_grad


def test_only_selected_q_receives_real_critic_labels():
    learner = Stage1Learner(model(), 200)
    out = learner.model(torch.zeros(2, 128), torch.zeros(2, 3, 6),
                        torch.ones(2, 3, 19), torch.ones(2, 3, dtype=torch.bool))
    out['q1'].retain_grad(); out['q2'].retain_grad()
    nxt = {k: v.detach().clone() for k, v in out.items() if isinstance(v, torch.Tensor)}
    batch = dict(reward=torch.ones(2), bootstrap_mask=torch.zeros(2),
                 terminated=torch.zeros(2, dtype=torch.bool), truncated=torch.ones(2, dtype=torch.bool),
                 dt=torch.ones(2) * .1, selected=torch.tensor([0, 1]),
                 mask=torch.ones(2, 3, dtype=torch.bool), next_mask=torch.ones(2, 3, dtype=torch.bool))
    expected_critic = .5 * sum((out[k].detach().gather(-1, batch['selected'][:, None]).squeeze(-1) - 1.).square().mean() for k in ('q1', 'q2'))
    result = learner.update(out, nxt, nxt, batch)
    assert result['critic'] == pytest.approx(float(expected_critic))
    for name in ('q1', 'q2'):
        gradient = out[name].grad
        assert torch.count_nonzero(gradient) == 2
        assert gradient[0, 0] != 0 and gradient[1, 1] != 0


def test_short_episode_updates_and_keeps_frozen_branches():
    replay = make_replay(); learner = Stage1Learner(model(), 200)
    before = deepcopy(learner.model.state_dict())
    assert not update_sequences(learner, replay, 999, adapter)['updated']
    result = update_sequences(learner, replay, 1000, adapter)
    assert result['updated'] and result['loss_transitions'] == 32 and result['updates'] == 1
    assert math.isfinite(result['critic']) and result['critic'] > 0
    after = learner.model.state_dict()
    assert any(not torch.equal(before[k], after[k]) for k in before if k.startswith('vcm.'))
    assert any(not torch.equal(before[k], after[k]) for k in before if k.startswith('candidate_encoder.'))
    assert any(not torch.equal(before[k], after[k]) for k in before if k.startswith('head_a.'))
    assert all(torch.equal(before[k], after[k]) for k in before if k.startswith(('head_b.', 'world_model.', 'random_world_model.', 'bias.')))


def test_checkpoint_restores_rng_next_sample_exact_update_and_counters(tmp_path):
    random.seed(101); np.random.seed(101)
    replay = make_replay(); learner = Stage1Learner(model(), 200)
    update_sequences(learner, replay, 1000, adapter)
    path = tmp_path / 'checkpoint.pt'
    save_checkpoint(path, learner, replay, counters={'decisions': 1000}, config={'task': 10})
    expected_rng = (random.random(), np.random.rand(), torch.rand(3))
    expected_samples = [(f.episode_key, f.start) for f in replay.sample()]
    expected = update_sequences(learner, replay, 1001, adapter)
    expected_state = deepcopy(learner.model.state_dict())
    restored = Stage1Learner(model(), 200); restored_replay = EpisodeReplay(1000)
    counters, environment = load_checkpoint(path, restored, restored_replay, config={'task': 10})
    actual_rng = (random.random(), np.random.rand(), torch.rand(3))
    assert actual_rng[:2] == expected_rng[:2]
    assert torch.equal(actual_rng[2], expected_rng[2])
    assert [(f.episode_key, f.start) for f in restored_replay.sample()] == expected_samples
    assert counters == {'decisions': 1000} and environment is None
    actual = update_sequences(restored, restored_replay, 1001, adapter)
    assert actual == expected and restored.updates == learner.updates == 2
    assert all(torch.equal(expected_state[k], v) for k, v in restored.model.state_dict().items())


def test_variable_length_batches_retain_episode_identity_and_exclude_padding():
    replay = EpisodeReplay(100)
    for ep, length in enumerate((2, 4, 1)):
        for t in range(length):
            replay.append(ep, transition(t, end=t == length - 1, marker=ep))
    m = model(); reference = model()
    fragments = [replay.fragment(ep, 0) for ep in range(3)]
    current, following, rows = sequence_outputs(m, fragments, adapter, gradients=True)
    assert len(rows) == len(current['q1']) == len(following['q1']) == 7
    assert [(r['marker'], r['decision_index']) for r in rows] == [
        (0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (1, 2), (1, 3)]
    expected = {}
    with torch.no_grad():
        for ep, seq in replay.episodes.items():
            reference.vcm.reset()
            for row in seq:
                out = reference.forward_step(**adapter([row]))
                expected[(ep, row['decision_index'])] = out['q1'][0]
    for i, row in enumerate(rows):
        torch.testing.assert_close(current['q1'][i], expected[(row['marker'], row['decision_index'])], atol=1e-6, rtol=1e-6)


def test_invalid_attempt_or_bootstrap_stops_without_parameter_update():
    learner = Stage1Learner(model(), 200)
    out = learner.model(torch.zeros(1, 128), torch.zeros(1, 3, 6),
                        torch.ones(1, 3, 19), torch.ones(1, 3, dtype=torch.bool))
    batch = dict(reward=torch.ones(1), bootstrap_mask=torch.tensor([.5]), dt=torch.tensor([.1]),
                 selected=torch.tensor([0]), mask=torch.ones(1, 3, dtype=torch.bool),
                 next_mask=torch.ones(1, 3, dtype=torch.bool))
    before = deepcopy(learner.model.state_dict())
    with pytest.raises(ValueError, match='binary'):
        learner.update(out, out, out, batch)
    batch.update(bootstrap_mask=torch.ones(1), dt=-torch.ones(1))
    with pytest.raises(ValueError, match='duration'):
        learner.update(out, out, out, batch)
    assert learner.updates == 0
    assert all(torch.equal(before[k], v) for k, v in learner.model.state_dict().items())


def test_zero_attempt_stall_preserves_clock_and_terminal_does_not_bootstrap():
    ongoing = attempt_reward(.4, .4, 1., 0)
    assert ongoing['dt'] == 0 and ongoing['discount'] == 1
    assert ongoing['reward'] == 0 and ongoing['bootstrap_mask'] == 1
    stopped = attempt_reward(.4, .4, 1., 0, terminated=True)
    assert stopped['dt'] == 0 and stopped['discount'] == 1
    assert stopped['reward'] == pytest.approx(-.4)
    assert stopped['bootstrap_mask'] == 0
    value = bellman(torch.tensor([0., -.4]), torch.tensor([1., 0.]), torch.zeros(2),
                    torch.zeros(2, 1), torch.full((2, 1), 2.), torch.full((2, 1), 3.),
                    torch.ones(2, 1, dtype=torch.bool), .35)
    torch.testing.assert_close(value, torch.tensor([2., -.4]))
    replay = EpisodeReplay(10)
    replay.append('stall', {**transition(0, end=True), 'dt': torch.tensor(0.)})
    assert len(replay) == 1
