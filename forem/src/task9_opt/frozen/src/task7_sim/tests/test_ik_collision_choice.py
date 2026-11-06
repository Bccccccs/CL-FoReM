"""IK branch choice avoids robot self-collision / ground (SRC-0915, task7.18.6); robot geometry only, never the map."""
import pytest
import torch
from task7_sim.kinematics import Kinematics, LOW, analytic, fk
from task7_sim.robot import RobotGeometry
from task7_sim.core import Core

D = torch.float64


@pytest.fixture(scope='module')
def setup():
    kin = Kinematics(); robot = RobotGeometry(); g = torch.Generator().manual_seed(0); N = 1500
    low = torch.as_tensor(LOW, dtype=D)
    q = (torch.rand(N, 6, generator=g, dtype=D) * 2 - 1) * (-low) * .6
    base = torch.zeros(N, 3, dtype=D); base[:, :2] = torch.randn(N, 2, generator=g, dtype=D); base[:, 2] = torch.rand(N, generator=g, dtype=D) * 6.28
    target = kin.world_tcp(base, q)
    prev = torch.maximum(low, torch.minimum(-low, q + torch.randn(N, 6, generator=g, dtype=D) * .3))
    return kin, robot, base, target, prev


def hit(robot, base, q):
    caps = robot(base, q)
    return robot.self_collision(base, caps, q=q) | (caps[..., [2, 5]].amin(-1) - caps[..., 6] <= 0).any(-1)


def branches(kin, base, target, prev):
    arm = torch.linalg.solve(__import__('task7_sim.kinematics', fromlist=['base_transform']).base_transform(base) @ kin.fixed('mount', prev), target)
    sol, valid = analytic(arm @ kin.fixed('tool_tcp_inverse', prev), prev)
    d, r, angle = __import__('task7_sim.kinematics', fromlist=['metrics']).metrics(fk(sol) @ kin.fixed('tool_tcp', prev), arm[:, None])
    low = torch.as_tensor(LOW, dtype=D)
    valid = valid & torch.isfinite(sol).all(-1) & (d <= 1e-4) & (angle <= 1e-4) & (sol >= low).all(-1) & (sol <= -low).all(-1)
    return sol, valid


def test_n1_acceptance_and_unaffected_rows_are_unchanged(setup):
    kin, robot, base, target, prev = setup
    a = kin.solve_world(base, target, prev); b = kin.solve_world(base, target, prev, robot=robot)
    for name in ('accepted', 'exact', 'status'):
        assert torch.equal(getattr(a, name), getattr(b, name)), name
    sol, valid = branches(kin, base, target, prev)
    one = valid.sum(-1) < 2
    assert torch.equal(a.q[one], b.q[one]) and torch.equal(a.branch[one], b.branch[one])   # rows with <2 valid branches (if any)
    same_free = ~hit(robot, base, a.q)
    assert torch.equal(a.q[same_free], b.q[same_free])           # nearest already collision-free -> identical


def test_picks_nearest_collision_free_branch_and_reduces_collisions(setup):
    kin, robot, base, target, prev = setup
    a = kin.solve_world(base, target, prev); b = kin.solve_world(base, target, prev, robot=robot)
    sol, valid = branches(kin, base, target, prev)
    N = len(base); coll = torch.zeros_like(valid)
    r, k = torch.where(valid)
    coll[r, k] = hit(robot, base[r], sol[r, k])
    dist = (sol - prev[:, None]).square().sum(-1)
    free_dist = dist.masked_fill(~valid | coll, float('inf'))
    any_free = torch.isfinite(free_dist.min(-1).values) & (valid.sum(-1) >= 2)
    changed = a.branch != b.branch
    assert changed.sum() > 20 and (changed & ~any_free).sum() == 0
    expect = free_dist.argmin(-1)
    assert torch.equal(b.branch[any_free], expect[any_free])
    assert not hit(robot, base[changed], b.q[changed]).any()      # every changed row ends collision-free
    assert hit(robot, base, b.q).float().mean() < hit(robot, base, a.q).float().mean()


def test_all_branches_colliding_keeps_original_nearest(setup):
    kin, robot, base, target, prev = setup
    a = kin.solve_world(base, target, prev); b = kin.solve_world(base, target, prev, robot=robot)
    sol, valid = branches(kin, base, target, prev)
    r, k = torch.where(valid); coll = torch.zeros_like(valid); coll[r, k] = hit(robot, base[r], sol[r, k])
    allhit = valid.any(-1) & ((coll | ~valid).all(-1)) & (valid.sum(-1) >= 2)
    assert allhit.sum() > 5
    assert torch.equal(a.branch[allhit], b.branch[allhit]) and torch.equal(a.q[allhit], b.q[allhit])


def test_dls_fallback_unchanged(setup):
    kin, robot, base, target, prev = setup
    far = target.clone(); far[:, :3, 3] += 5.                       # unreachable -> no exact branch
    a = kin.solve_world(base[:50], far[:50], prev[:50]); b = kin.solve_world(base[:50], far[:50], prev[:50], robot=robot)
    assert not a.exact.any()
    for name in ('q', 'accepted', 'exact', 'status', 'branch', 'position'):
        assert torch.equal(getattr(a, name), getattr(b, name)), name


def test_uses_only_robot_geometry_not_the_map(setup):
    kin, robot, base, target, prev = setup

    class OnlyRobot:   # exposes exactly the robot-geometry calls; any other attribute (grid, boxes, map...) would raise
        __slots__ = ()
        def __call__(self, b, q): return robot(b, q)
        def self_collision(self, b, caps, allowed=None, *, q=None): return robot.self_collision(b, caps, allowed, q=q)
    out = kin.solve_world(base, target, prev, robot=OnlyRobot())
    ref = kin.solve_world(base, target, prev, robot=robot)
    assert torch.equal(out.q, ref.q)


def test_execution_and_rollout_cores_choose_the_same_branch():
    from task7_sim.bench_full import scene
    from task7_sim.core import Candidate
    results = []
    for execute in (True, False):
        c, _ = scene(device='cpu', dtype=D); c.execute = execute
        poses = c.state.base.clone(); poses[:, 0] += .03
        c.begin(Candidate(poses, torch.full_like(c.state.s, .03), torch.zeros_like(c.done)))
        c.step(torch.tensor([[.3, .2, 1.]], dtype=D)); results.append(c.attempts[0])
    assert torch.equal(results[0]['candidate_q'], results[1]['candidate_q']) and torch.equal(results[0]['branch'], results[1]['branch'])


def test_core_flag_off_restores_previous_rule(setup):
    kin, robot, base, target, prev = setup
    import inspect
    assert inspect.signature(Core.__init__).parameters['ik_avoid_collision'].default is True
    from task7_sim.bench_full import scene
    c, _ = scene(device='cpu', dtype=D); assert c.ik_avoid_collision is True and c.robot is not None
