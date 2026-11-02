"""C'' (SRC-0915, task7.18.6): episode_end_bootstrap=True -> only reaching the candidate / route end gives mask 0."""
import pytest
import torch
from task7_sim.core import Core
from task7_sim.tests.test_core import fixture, candidate
from task7_sim.tests.test_failure_mode import batch, act, WALL_FAR, WALL_FIRST, D


def mk(wall, mode='cbl_continue', boot=True, **kw):
    c = batch([wall], mode=mode, **kw)
    c.episode_end_bootstrap = boot
    return c


def test_default_is_false_and_wrapper_passes_it():
    assert fixture().episode_end_bootstrap is False
    from task7_sim.env import EpisodeEnv
    from task7_sim.tests.test_env import factory
    make = lambda i, r: factory(i, r, device='cpu', dtype=D)
    a = EpisodeEnv(2, make, seed=1, episode_end_bootstrap=True); a.reset()
    assert a.core.episode_end_bootstrap is True
    b = EpisodeEnv(2, make, seed=1); b.reset()
    assert b.core.episode_end_bootstrap is False


def test_mask_truth_table_default_unchanged():
    # fail-limit termination (20th failed step) -> mask 0 with the original rule
    c = mk(WALL_FIRST, boot=False); c.begin(candidate(c))
    for _ in range(20):
        tr = c.step(act())
    assert c.terminated.item() and tr.mask.item() == 0
    # timeout -> mask 1
    t = mk(WALL_FIRST, boot=False); t.begin(candidate(t)); t.timeout[:] = .05
    assert t.step(act()).mask.item() == 1


def test_bootstrap_true_arrival_and_route_end_are_terminal():
    c = mk(WALL_FAR, length=.0075); cand = candidate(c, x=0, cap=.0075); cand.progress = c.route.length.clone(); c.begin(cand)
    tr = c.step(act(action=[1., 0, 0]))
    assert tr.done.item() and tr.reason.item() in (0, 1) and tr.mask.item() == 0


def test_bootstrap_true_failure_limit_is_truncation_mask_one():
    c = mk(WALL_FIRST); c.begin(candidate(c))
    for k in range(20):
        tr = c.step(act())
    assert tr.done.item() and c.terminated.item() and c.failures.item() == 20
    assert tr.mask.item() == 1                       # bootstrap from the final observation of the same sub-goal
    assert torch.isfinite(tr.next_observation['q']).all()


def test_bootstrap_true_timeout_stall_and_clock_ends_are_mask_one():
    t = mk(WALL_FIRST); t.begin(candidate(t)); t.timeout[:] = .05
    assert t.step(act()).mask.item() == 1 and not t.terminated.item()
    s = mk(WALL_FIRST); s.begin(candidate(s)); s.timeout[:] = .05; s.stalls[:] = 4
    tr = s.step(act())
    assert s.terminated.item() and tr.mask.item() == 1                 # stuck -> terminated flag, but truncation for learning
    d = mk(WALL_FIRST); d.begin(candidate(d)); d.timeout[:] = .05; d.decisions[:] = 149
    tr = d.step(act()); assert d.truncated.item() and tr.mask.item() == 1
    m = mk(WALL_FIRST); m.begin(candidate(m)); m.timeout[:] = .05; m.attempt_time[:] = 199.96
    tr = m.step(act()); assert m.truncated.item() and tr.mask.item() == 1


def test_bootstrap_true_non_ending_failure_and_terminal_mode_failure():
    c = mk(WALL_FIRST); c.begin(candidate(c))
    assert c.step(act()).mask.item() == 1
    f = mk(WALL_FIRST, mode='terminal'); f.begin(candidate(f))
    tr = f.step(act()); assert tr.done.item() and tr.reason.item() == 3 and tr.mask.item() == 1


def test_bootstrap_flag_changes_only_mask():
    out = []
    for boot in (False, True):
        c = mk(WALL_FIRST, boot=boot); c.begin(candidate(c))
        for _ in range(20):
            tr = c.step(act())
        out.append(tr)
    for name in ('reward', 'B', 'G', 'dt', 'done', 'reason', 'raw_action', 'active', 'attempted', 'committed'):
        assert torch.equal(getattr(out[0], name), getattr(out[1], name)), name
    assert out[0].mask.item() == 0 and out[1].mask.item() == 1
