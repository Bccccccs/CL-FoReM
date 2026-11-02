"""async_time_penalty (SRC-0913, task7.18.4): weight of the asynchronous -dt reward term; default 1.0 is the original."""
import pytest
import torch
from task7_sim.core import Core
from task7_sim.tests.test_core import fixture, candidate
from task7_sim.tests.test_failure_mode import batch, act, WALL_FAR, WALL_FIRST

D = torch.float64


def run(c, w, steps=3, action=(0., .2, 1.)):
    c.async_time_penalty = w
    c.begin(candidate(c))
    return [c.step(act(len(c.state.s), list(action))) for _ in range(steps)]


def test_default_is_one_and_validated():
    c = fixture()
    assert c.async_time_penalty == 1.0
    with pytest.raises(ValueError):
        Core(c.state, c.route, c.grid, c.kin, c.capsules, c.collision, synchronous=False, async_time_penalty=-.1)
    with pytest.raises(ValueError):
        Core(c.state, c.route, c.grid, c.kin, c.capsules, c.collision, synchronous=False, async_time_penalty=2.)


@pytest.mark.parametrize("mode", ['terminal', 'cbl_continue'])
def test_default_value_is_elementwise_original_reward(mode):
    c = batch([WALL_FAR], mode=mode)
    for tr in run(c, 1.0):
        assert torch.equal(tr.reward, tr.B + tr.G - tr.dt) and tr.dt.item() > 0


@pytest.mark.parametrize("mode", ['terminal', 'cbl_continue'])
def test_zero_removes_async_time_term_only(mode):
    a = batch([WALL_FAR], mode=mode); b = batch([WALL_FAR], mode=mode)
    ta, tb = run(a, 1.0), run(b, 0.0)
    for x, y in zip(ta, tb):
        assert torch.equal(y.reward, y.B + y.G)
        for name in ('B', 'G', 'dt', 'mask', 'done', 'reason', 'committed', 'attempted'):
            assert torch.equal(getattr(x, name), getattr(y, name)), name   # dt itself (sim-time accounting) unchanged
        assert torch.allclose(y.reward - x.reward, x.dt, atol=1e-15, rtol=0)
    assert torch.equal(a.state.base, b.state.base)


def test_partial_weight_scales_dt():
    c = batch([WALL_FAR]); tr = run(c, .25, steps=1)[0]
    assert abs(tr.reward.item() - (tr.B.item() + tr.G.item() - .25 * tr.dt.item())) < 1e-15


def test_failed_step_has_no_time_term_either_way():
    for w in (1.0, 0.0):
        c = batch([WALL_FIRST]); tr = run(c, w, steps=1)[0]
        assert tr.dt.item() == 0 and torch.equal(tr.reward, tr.B + tr.G)


@pytest.mark.parametrize("w", [1.0, 0.0])
def test_synchronous_reward_ignores_the_switch(w):
    c = batch([WALL_FAR], synchronous=True); tr = run(c, w, steps=1)[0]
    u = .01 + .145 * 1.
    assert abs(tr.reward.item() - (u / .3 * tr.B.item() - .1 * ((.3 - u) / .3) ** 2 + tr.G.item())) < 1e-12
    ref = batch([WALL_FAR], synchronous=True); r0 = run(ref, 1.0, steps=1)[0]
    assert torch.equal(tr.reward, r0.reward)


def test_env_wrapper_passes_switch():
    from task7_sim.env import EpisodeEnv
    from task7_sim.tests.test_env import factory
    make = lambda i, r: factory(i, r, device='cpu', dtype=D)
    a = EpisodeEnv(2, make, seed=1, failure_mode='cbl_continue', async_time_penalty=0.0); a.reset()
    assert a.core.async_time_penalty == 0.0
    b = EpisodeEnv(2, make, seed=1); b.reset()
    assert b.core.async_time_penalty == 1.0
