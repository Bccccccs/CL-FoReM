"""failure_mode='cbl_continue' (stage-L training only, SRC-0912, task7.18.4).

A failed sub-step is not committed, the action step makes no further attempt, the segment continues;
the episode ends after 20 failed action steps. 'terminal' (default) is unchanged and covered by the
existing suite plus the old-vs-new bitwise comparison script in results/task7/t7.18.4-diag-20261022.
"""
import dataclasses
import pytest
import torch
from task7_sim.core import Core
from task7_sim.tests.test_core import fixture, candidate

D = torch.float64
WALL_FIRST = [.515, 0, .5, .005, .1, .5, 1, 0]    # fails at the first sub-step (base collision)
WALL_SECOND = [.53, 0, .5, .005, .1, .5, 1, 0]    # first sub-step commits, second fails
WALL_FAR = [5., 0, .5, .005, .1, .5, 1, 0]
ACTION = [0., 0, 1]


def batch(walls, synchronous=False, mode='cbl_continue', **kw):
    c = fixture(batch=len(walls), wall=walls[0], **kw)
    boxes = torch.tensor([[w] for w in walls], dtype=D)
    mask = torch.ones(boxes.shape[:2], dtype=torch.bool)
    c.collision.boxes, c.collision.mask = boxes, mask
    c.renderer.boxes, c.renderer.mask = boxes, mask
    c.synchronous = synchronous
    c.failure_mode = mode
    c.failure_limit = 5 if mode == 'terminal' else 20
    return c


def act(n=1, action=ACTION):
    return torch.tensor([action] * n, dtype=D)


def force_ik(c, calls):
    """Make solve_world fail (accepted=False, given residuals) on the listed 0-based calls."""
    original = c.kin.solve_world
    counter = {'n': 0}

    def patched(base, target, prev, **kw):
        result = original(base, target, prev, **kw)
        n = counter['n']; counter['n'] += 1
        if n in calls:
            result = dataclasses.replace(result, accepted=torch.zeros_like(result.accepted),
                                         position=torch.full_like(result.position, calls[n][0]),
                                         cbl=torch.full_like(result.cbl, calls[n][1]))
        return result
    c.kin.solve_world = patched


def smooth(c, raw):
    return .05 * (raw[:, 1:] - torch.zeros_like(raw[:, 1:])).square().sum(-1)


def test_constructor_validation():
    with pytest.raises(ValueError):
        Core.__init__(object.__new__(Core), None, None, None, None, None, None, synchronous=False, failure_mode='bogus')
    c = fixture()
    assert c.failure_mode == 'terminal' and c.failure_limit == 5
    # rollout / decision-level execution (execute=False) cannot be switched into the training mode
    with pytest.raises(ValueError):
        Core(c.state, c.route, c.grid, c.kin, c.capsules, c.collision, synchronous=False, execute=False, failure_mode='cbl_continue')


def test_base_collision_failure_does_not_end_segment_and_pays_cbl_terms():
    c = batch([WALL_FIRST]); q0 = c.state.q.clone(); base0 = c.state.base.clone()
    c.begin(candidate(c)); tr = c.step(act())
    assert c.last_step_failure.item() == 2 and c.failure_kind.item() == 2
    assert not tr.done.item() and tr.reason.item() == -1 and tr.mask.item() == 1
    assert tr.committed.item() == 0 and tr.attempted.item() == 1 and tr.dt.item() == 0
    assert torch.equal(c.state.q, q0) and torch.equal(c.state.base, base0) and c.state.s.item() == 0
    assert c.render_count.item() == 0 and torch.equal(c.queue, torch.zeros_like(c.queue))
    assert c.failures.item() == 1 and not c.terminated.item() and not c.truncated.item()
    s = smooth(c, act())
    assert abs(tr.B.item() - (-10 - s.item())) < 1e-12           # D18 collision penalty, no residual (nothing committed)
    assert abs(tr.G.item() - (-2)) < 1e-12                        # R_fail, rho and ds unchanged
    assert abs(tr.reward.item() - (tr.B.item() + tr.G.item())) < 1e-12
    # the segment really continues: the next action is accepted
    tr2 = c.step(act())
    assert tr2.active.item() and c.attempted_segment.item() == 2 and c.failures.item() == 2


def test_ik_failure_uses_failed_attempt_residual_first_substep():
    c = batch([WALL_FAR]); force_ik(c, {0: (.5, .2)})
    c.begin(candidate(c)); tr = c.step(act())
    assert c.last_step_failure.item() == 1 and not tr.done.item() and tr.committed.item() == 0
    expected_B = -.5 * ((.5 / .1) ** 2 + (.2 / .05) ** 2) - smooth(c, act()).item()
    assert abs(tr.B.item() - expected_B) < 1e-9 and abs(tr.G.item() + 2) < 1e-12


def test_ik_failure_second_substep_replaces_committed_residual_and_keeps_first_commit():
    c = batch([WALL_FAR]); force_ik(c, {1: (.3, .1)})
    c.begin(candidate(c)); tr = c.step(act())
    assert tr.committed.item() == 1 and tr.attempted.item() == 2 and abs(tr.dt.item() - .05) < 1e-12
    assert abs(c.state.base[0, 0].item() - .015) < 1e-12 and c.render_count.item() == 1
    expected_B = -.5 * ((.3 / .1) ** 2 + (.1 / .05) ** 2) - smooth(c, act()).item()
    assert abs(tr.B.item() - expected_B) < 1e-9
    rho0 = (c.start.base[0, :2] - c.candidate.pose[0, :2]).norm().item(); rho = (c.state.base[0, :2] - c.candidate.pose[0, :2]).norm().item()
    assert abs(tr.G.item() - (rho0 - rho + (c.state.s - c.start.s).item() - 2)) < 1e-12
    assert abs(tr.reward.item() - (tr.B.item() + tr.G.item() - tr.dt.item())) < 1e-12  # async time penalty unchanged
    assert not tr.done.item() and tr.mask.item() == 1


def test_half_step_collision_failure_commits_first_substep():
    c = batch([WALL_SECOND]); c.begin(candidate(c)); tr = c.step(act())
    assert tr.committed.item() == 1 and c.last_step_failure.item() == 2 and not tr.done.item()
    a = c.attempts[0]; d, r = a['position_m'].item(), a['cbl'].item()
    assert abs(tr.B.item() - (-10 - .5 * ((d / .1) ** 2 + (r / .05) ** 2) - smooth(c, act()).item())) < 1e-9


def test_sync_variant_reward_composition():
    c = batch([WALL_FIRST], synchronous=True); c.begin(candidate(c)); tr = c.step(act())
    u = .01 + .145 * (ACTION[0] + 1)
    B = -10 - smooth(c, act()).item(); G = -2
    assert abs(tr.reward.item() - (u / .3 * B - .1 * ((.3 - u) / .3) ** 2 + G)) < 1e-12 and not tr.done.item()


def test_twenty_failed_action_steps_terminate_with_mask_zero():
    c = batch([WALL_FIRST]); c.begin(candidate(c))
    for k in range(1, 21):
        tr = c.step(act())
        if k < 20:
            assert not tr.done.item() and not c.terminated.item() and tr.mask.item() == 1 and c.failures.item() == k
    assert tr.done.item() and c.terminated.item() and not c.truncated.item() and tr.mask.item() == 0
    assert c.failures.item() == 20 and tr.reason.item() == 3 and abs(c.attempt_time.item() - 1.0) < 1e-12
    assert abs(tr.G.item() + 2) < 1e-12 and not c.strict_success.item()


def test_terminal_mode_threshold_stays_five_failed_segments():
    c = batch([WALL_FIRST], mode='terminal'); n = 0
    c.begin(candidate(c)); tr = c.step(act())
    assert tr.done.item() and tr.reason.item() == 3 and c.failures.item() == 1 and tr.mask.item() == 0
    assert c.failure_limit == 5


def test_segment_timeout_counts_attempted_time():
    c = batch([WALL_FIRST]); c.begin(candidate(c)); c.timeout[:] = .12
    t1 = c.step(act()); t2 = c.step(act())
    assert not t2.done.item() and abs(c.attempted_segment.item() * .05 - .1) < 1e-12
    t3 = c.step(act())
    assert t3.done.item() and t3.reason.item() == 4 and t3.mask.item() == 1       # timeout truncation keeps bootstrap
    assert not c.terminated.item() and not c.truncated.item() and c.failures.item() == 3
    assert abs(t3.G.item() + 2) < 1e-12


def test_mixed_commit_and_failure_count_full_step_attempt_time():
    c = batch([WALL_SECOND]); c.begin(candidate(c)); c.timeout[:] = .1
    tr = c.step(act())     # one committed + one failed sub-step = .1 s attempted
    assert tr.done.item() and tr.reason.item() == 4 and tr.mask.item() == 1


def test_episode_clock_uses_attempt_time():
    c = batch([WALL_FIRST]); c.begin(candidate(c)); c.timeout[:] = .05; c.attempt_time[:] = 199.96
    tr = c.step(act())
    assert tr.done.item() and c.truncated.item() and not c.terminated.item() and tr.mask.item() == 1
    assert c.time.item() == 0   # committed clock untouched (scan timestamps unaffected)
    t = batch([WALL_FIRST], mode='terminal'); t.begin(candidate(t)); t.time[:] = 199.96
    t.step(act())               # terminal: committed clock governs and failure already terminated first


def test_mask_truth_table():
    # arrival / route end -> terminated, mask 0
    c = batch([WALL_FAR], length=.0075); cand = candidate(c, x=0, cap=.0075); cand.progress = c.route.length.clone(); c.begin(cand)
    tr = c.step(act(action=[1., 0, 0]))
    assert tr.done.item() and tr.reason.item() in (0, 1) and tr.mask.item() == 0
    # non-ending failure -> mask 1 ; timeout -> mask 1 ; 20th failure -> mask 0 (tests above)
    f = batch([WALL_FIRST]); f.begin(candidate(f)); assert f.step(act()).mask.item() == 1


def test_mixed_batch_unfailed_env_matches_single_env_bitwise():
    c = batch([WALL_FIRST, WALL_FAR, WALL_SECOND]); c.begin(candidate(c)); tr = c.step(act(3))
    ok = c.last_step_failure == 0
    assert ok.tolist() == [False, True, False]
    single = batch([WALL_FAR]); single.begin(candidate(single)); ts = single.step(act())
    for name in ('reward', 'B', 'G', 'dt', 'mask', 'done', 'reason'):
        assert torch.equal(getattr(tr, name)[1], getattr(ts, name)[0]), name
    assert not tr.done[0].item() and not tr.done[2].item()


def test_failed_env_can_recover_and_arrive_then_strict_success_is_false():
    c = batch([WALL_FAR], length=.0075); cand = candidate(c, x=0, cap=.0075); cand.progress = c.route.length.clone(); c.begin(cand)
    force_ik(c, {0: (.5, .2)})
    tr = c.step(act(action=[1., 0, 0]))          # first sub-step IK fails -> no commit, step ends
    assert not tr.done.item() and c.failures.item() == 1
    tr = c.step(act(action=[1., 0, 0]))
    assert tr.done.item() and tr.mask.item() == 0 and not c.strict_success.item() and c.failures.item() == 1


def test_env_wrapper_passes_failure_mode():
    from task7_sim.env import EpisodeEnv
    from task7_sim.tests.test_env import factory
    a = EpisodeEnv(2, lambda i, r: factory(i, r, device='cpu', dtype=D), seed=1, failure_mode='cbl_continue')
    a.reset(); assert a.core.failure_mode == 'cbl_continue' and a.core.failure_limit == 20
    b = EpisodeEnv(2, lambda i, r: factory(i, r, device='cpu', dtype=D), seed=1)
    b.reset(); assert b.core.failure_mode == 'terminal'
