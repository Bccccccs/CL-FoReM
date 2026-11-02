"""CPU deterministic A/B mechanics, not training or performance evaluation."""
from types import SimpleNamespace
import time
import pytest
import torch

from task7_sim.core import Core, Candidate, State
from task7_sim.motion import Route
from task7_sim.perception import Grid, LocalCollision, Depth
from task7_sim.candidates import CandidateBatch
from task10.environment import (PredictionCore, predict_candidates, attempt_features,
                                _first_failure_step, Task10Env)


@pytest.fixture(autouse=True)
def bounded_threads():
    old = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(old)


class KinematicsFixture:
    """Exact translational IK fixture isolates clocks and collision semantics."""
    def fixed(self, name, q):
        return torch.eye(4).expand(len(q), 4, 4).clone()

    def world_tcp(self, base, q):
        out = self.fixed(None, q)
        out[:, :3, 3] = q[:, :3]
        return out

    def solve_world(self, base, target, q, **kwargs):
        out = q.clone()
        out[:, :3] = target[:, :3, 3]
        n = len(q)
        z = q.new_zeros(n)
        return SimpleNamespace(q=out, accepted=torch.ones(n, dtype=torch.bool),
            position=z, cbl=z, angle=z, branch=torch.zeros(n, dtype=torch.long),
            status=torch.zeros(n, dtype=torch.long))


def capsules(base, q):
    return base.new_empty(len(base), 0, 7)


def renderer(base, caps):
    n = len(base)
    return Depth(torch.zeros(n, 1, 1), torch.zeros(n, 1, 1, dtype=torch.bool),
        torch.zeros(n, 1, 1, dtype=torch.bool), torch.zeros(n, 1, 1, 3),
        torch.zeros(n, dtype=torch.bool))


def fixture_core(*, occupied=False, truth_occupied=None, length=.06):
    grid = Grid.empty(1)
    grid.observed[:] = True
    if occupied:
        grid.height[:, 100, 100] = 1
    truth = grid.snapshot()
    if truth_occupied is not None:
        truth.height[:] = 0
        if truth_occupied:
            truth.height[:, 100, 100] = 1
    route = Route(torch.tensor([[[0., 0., .8], [length, 0., .8]]]),
        torch.tensor([[[0., 0., 0., 1.], [0., 0., 0., 1.]]]))
    state = State(torch.zeros(1, 3), torch.tensor([[0., 0., .8, 0., 0., 0.]]), torch.zeros(1))
    return Core(state, route, grid, KinematicsFixture(), capsules, LocalCollision(truth),
        renderer=renderer, synchronous=True, failure_mode='cbl_continue',
        episode_end_bootstrap=True, retain_transitions=False)


def generated(*, slots=(0,), x=1.):
    pose = torch.zeros(1, 13, 3)
    pose[0, :, 0] = x
    mask = torch.zeros(1, 13, dtype=torch.bool)
    mask[0, list(slots)] = True
    return CandidateBatch(pose, mask, None, torch.zeros_like(mask), {})


def policy(obs):
    return obs['q'].new_tensor([1., 0., 0.]).expand(len(obs['q']), 3)


def execute(core, batch, slot=0):
    core.begin(Candidate(batch.world_pose(core.state.base)[:, slot], None,
                         batch.inplace[:, slot]))
    while not core.done.all():
        _first_failure_step(core, lambda: core.step(policy(core.current_observation())))


def test_known_collision_prediction_matches_real_continuation_and_attempt_clock():
    core = fixture_core(occupied=True)
    batch = generated()
    predicted, diag = predict_candidates(core, batch, policy)
    execute(core, batch)
    actual = attempt_features(core)
    torch.testing.assert_close(predicted[:, 0], actual)
    assert core.failures.item() == 20
    assert core.attempted_segment.item() == 20 and core.segment_substeps.item() == 0
    assert actual[0, 7].item() == pytest.approx(1.)
    assert actual[0, 6].item() == pytest.approx(.05/core.timeout.item())
    assert diag['first_failure_time'].item() == pytest.approx(.05)
    assert core.first_failure_time.item() == pytest.approx(.05)
    assert core.terminated.item() and not core.strict_success.item()


def test_partial_observation_prediction_can_disagree_with_truth_without_leak():
    core = fixture_core(truth_occupied=True)
    batch = generated()
    f, _ = predict_candidates(core, batch, policy)
    assert f[0, 0, 2].item() == 1  # route end, no predicted collision
    execute(core, batch)
    assert core.failure_kind.item() == 2 and core.failures.item() == 20
    assert core.state.s.item() == 0


def test_prediction_isolates_state_counters_grid_queue_rng_and_invalid_slots():
    import random
    import numpy as np
    core = fixture_core(occupied=True)
    core.time[:] = 4.2
    core.attempt_time[:] = 9.8
    core.failures[:] = 19
    core.stalls[:] = 3
    core.decisions[:] = 149
    core.queue[:] = .2
    core.visible_previous[:] = -.2
    core.grid.timestamp[:] = 4.2
    batch = generated(slots=(2, 9))
    names = ('time', 'attempt_time', 'failures', 'stalls', 'decisions', 'queue',
             'visible_previous', 'attempted_total', 'committed_total')
    before = {k: getattr(core, k).clone() for k in names}
    state, grid = core.state.clone(), core.grid.snapshot()
    py_rng, np_rng, torch_rng = random.getstate(), np.random.get_state(), torch.get_rng_state()
    calls = []
    def checked(obs):
        calls.append(len(obs['q']))
        assert len(obs['q']) == 2
        torch.testing.assert_close(obs['previous_action'], torch.full((2, 3), -.2))
        return policy(obs)
    f, diag = predict_candidates(core, batch, checked)
    assert calls == [2] and diag['attempted_substeps'] == 2
    assert diag['cumulative_failures'].tolist() == [20, 20]
    assert (f[~batch.mask] == 0).all()
    for name in names:
        assert torch.equal(getattr(core, name), before[name])
    for name in ('base', 'q', 's'):
        assert torch.equal(getattr(core.state, name), getattr(state, name))
    for name in ('observed', 'height', 'timestamp'):
        assert torch.equal(getattr(core.grid, name), getattr(grid, name))
    assert random.getstate() == py_rng
    assert np.array_equal(np.random.get_state()[1], np_rng[1])
    assert torch.equal(torch.get_rng_state(), torch_rng)
    assert core.renderer is renderer and core.done.item()


@pytest.mark.parametrize('counter,value,flag', [('decisions', 149, 'truncated'),
    ('attempt_time', 200., 'truncated'), ('stalls', 4, 'terminated')])
def test_prediction_copies_remaining_limits(counter, value, flag, monkeypatch):
    core = fixture_core(length=1.)
    setattr(core, counter, torch.full_like(getattr(core, counter), value))
    # One successful zero-base-motion segment times out, giving a stall. The
    # chosen fixture progress stays below .01 so a previous stall can terminate.
    def slow(obs):
        return obs['q'].new_tensor([-1., 0., 0.]).expand(len(obs['q']), 3)
    batch = generated(x=0.)
    # Inspect prediction finish directly via feature_metrics; no new capability.
    observed = {}
    def metric(c):
        observed.update(terminated=c.terminated.clone(), truncated=c.truncated.clone(),
                        decisions=c.decisions.clone(), attempt_time=c.attempt_time.clone())
        return torch.zeros(len(c.state.s), 3)
    predict_candidates(core, batch, slow, feature_metrics=metric)
    assert observed[flag].item()
    assert observed['decisions'].item() >= 1


def reward_fixture(before, after, length, attempts, **flags):
    ended = flags['terminated'] or flags['truncated']
    discount = .99**(attempts*.05/.1)
    base = float(flags['strict_success'])
    shaping = discount*(0 if ended else after/length)-before/length
    return dict(reward=base+shaping, base_reward=base, shaping=shaping,
        dt=attempts*.05, discount=discount, bootstrap_mask=float(not ended))


def make_decision_fixture(core, batch):
    e = Task10Env.__new__(Task10Env)
    e.batch, e.policy = 1, policy
    e.risk_chunk_size, e.observation_chunk_size = 32, 32
    e.reuse_route_raster = False
    e.reward_fn = reward_fixture
    e.run_id = e.code_commit = e.config_hash = '<fixture>'
    e.versions = {'environment_adapter': 'cpu-fixture'}
    def info():
        return dict(episode_count=torch.ones(1, dtype=torch.long), map_ids=('fixture',),
            proposal_seeds=(1,), strict_success=core.strict_success.clone())
    e.episodes = SimpleNamespace(core=core, info=info, begin=core.begin,
        step=lambda raw: SimpleNamespace(transition=core.step(raw)))
    e.previous_result = e._empty_result()
    e.previous_result_v1 = torch.zeros(1, 19)
    e.previous_candidate = core.state.base.clone()
    e.previous_target_delta_s = torch.zeros(1)
    e.previous_link = [None]
    e.last_timing = {}
    e.candidates = dict(c_k=batch.pose.clone(), mask=batch.mask.clone(),
        f_k=torch.zeros(1, 13, 19), progress=None, inplace=batch.inplace.clone(),
        world_pose=batch.world_pose(core.state.base))
    e.observation = e._upper_observation()
    return e


def test_selected_slot_maps_to_real_target_and_terminal_candidates_are_placeholders(monkeypatch):
    core = fixture_core()
    batch = generated(slots=(2, 9))
    batch.pose[0, 9] = torch.tensor([2., .3, .2])
    e = make_decision_fixture(core, batch)
    monkeypatch.setattr('task7_sim.candidates.generate_candidates',
        lambda *a, **kw: pytest.fail('terminal boundary must not generate or predict'))
    before = e.candidates['world_pose'].clone()
    out = e.step(torch.tensor([9]))
    assert torch.equal(core.candidate.pose, before[:, 9])
    assert out.terminated.item() and out.reward.item() == 1
    assert out.replay_fields['bootstrap_mask'].item() == 0
    assert out.candidates['terminal_placeholder'].item()
    assert torch.equal(out.candidates['world_pose'], before)
    assert out.replay_fields['selected'].item() == 9
    assert out.replay_fields['map_ids'] == ('fixture',)
    assert out.replay_fields['episode_id'].item() == 1
    assert core.decisions.item() == 1  # not autoreset
    assert out.info['next_pending']
    assert e.prepare_next(out) is out
    assert not out.info['next_pending']
    assert out.info['timing']['next']['valid_slots'] == 0
    with pytest.raises(RuntimeError, match='reset ended'):
        e.step(torch.tensor([2]))


def test_failed_zero_commit_decision_has_positive_attempt_dt_and_failure_fraction():
    core = fixture_core(occupied=True)
    e = make_decision_fixture(core, generated())
    out = e.step(torch.tensor([0]))
    assert out.dt.item() == pytest.approx(1.)
    assert out.replay_fields['committed_dt'].item() == 0
    assert out.replay_fields['attempted_substeps'].item() == 20
    assert out.replay_fields['committed_substeps'].item() == 0
    assert out.observation['n_f_over_F'].item() == 1
    assert out.reward.item() == 0 and out.replay_fields['bootstrap_mask'].item() == 0


def test_deadline_does_not_fake_task_end_or_mutate_prediction():
    from task8_sim.episode import SamplingIncomplete
    core = fixture_core()
    with pytest.raises(SamplingIncomplete):
        predict_candidates(core, generated(), policy, deadline=time.monotonic()-1)
    assert core.done.item() and not core.terminated.item() and core.decisions.item() == 0


def test_invalid_selection_rejected_before_any_execution():
    core = fixture_core()
    e = make_decision_fixture(core, generated(slots=(4,)))
    with pytest.raises(ValueError, match='valid slot'):
        e.step(torch.tensor([3]))
    assert core.decisions.item() == 0 and core.attempted_total.item() == 0


def test_step_returns_real_transition_before_next_boundary_timeout(monkeypatch):
    from task8_sim.episode import SamplingIncomplete
    core = fixture_core(length=5.)
    e = make_decision_fixture(core, generated(x=.2))
    monkeypatch.setattr(e, '_boundary', lambda **kw: (_ for _ in ()).throw(SamplingIncomplete('deadline')))
    out = e.step(torch.tensor([0]))
    assert out.replay_fields['attempted_substeps'].item() > 0
    assert core.decisions.item() == 1
    with pytest.raises(SamplingIncomplete):
        e.prepare_next(out, deadline=time.monotonic()-1)
    assert core.decisions.item() == 1
    assert not out.terminated.item() and not out.truncated.item()


def test_boundary_timing_is_json_serializable(monkeypatch):
    import json
    core = fixture_core()
    e = make_decision_fixture(core, generated())
    monkeypatch.setattr('task7_sim.candidates.generate_candidates', lambda *a, **kw: generated())
    _, _, timing = e._boundary()
    json.dumps(timing)
    assert timing['valid_slots'] == 1


def test_prepare_next_populates_survivor_and_audits_calls(monkeypatch):
    core = fixture_core(length=5.)
    e = make_decision_fixture(core, generated(x=.2))
    monkeypatch.setattr('task7_sim.candidates.generate_candidates',
        lambda *a, **kw: generated(slots=(2, 9), x=.3))
    out = e.step(torch.tensor([0]))
    assert out.info['next_pending'] and not out.terminated.item()
    assert out.info['timing']['execution_b3_calls'] > 0
    assert out.info['timing']['execution_b3_row_calls'] == out.info['timing']['execution_b3_calls']
    with pytest.raises(RuntimeError, match='prepare next'):
        e.step(torch.tensor([0]))
    e.prepare_next(out)
    assert out.candidates['mask'][0, 2] and out.candidates['mask'][0, 9]
    assert torch.equal(out.replay_fields['next_candidates']['mask'], out.candidates['mask'])
    assert out.info['timing']['next']['valid_slots'] == 2
    assert out.info['timing']['next']['b3_row_calls'] == 2*out.info['timing']['next']['b3_calls']


def test_pending_result_cannot_be_discarded_by_reset():
    e = make_decision_fixture(fixture_core(), generated())
    e.step(torch.tensor([0]))
    with pytest.raises(RuntimeError, match='prepare next'):
        e.reset()
