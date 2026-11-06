import numpy as np
import pytest
import torch
from task7_sim.episode import RandomStreams, sample_base, sample_goal, validate_initial_state, sample_initial, validate_goal_position, validate_goal_witness
from task7_sim.bench_full import scene


def test_streams_are_per_environment_and_per_purpose():
    a = RandomStreams(42, 2); b = RandomStreams(42, 2)
    a.for_env(0).maps.random(70); a.for_env(0).initial.random(80)
    a.for_env(1).other.random(90)
    assert np.array_equal(a.for_env(1).initial.random(100), b.for_env(1).initial.random(100))
    assert np.array_equal(a.for_env(1).maps.random(100), b.for_env(1).maps.random(100))
    x = RandomStreams(42, 1); y = RandomStreams(42, 1)
    x.for_env(0).maps.random(300)
    assert np.array_equal(x.for_env(0).initial.random(100), y.for_env(0).initial.random(100))


def test_raw_task_proposals_cover_map_and_preserve_distance_without_clipping():
    rng = np.random.default_rng(512)
    bases = np.array([sample_base(rng) for _ in range(2000)])
    assert (np.abs(bases[:, :2]) < 5).all()
    assert (bases[:, :2].min(0) < -4.8).all() and (bases[:, :2].max(0) > 4.8).all()
    goals = np.array([sample_goal(np.zeros(3), rng) for _ in range(2000)])
    dist = np.linalg.norm(goals[:, :2], axis=1)
    assert (dist >= .5).all() and (dist <= 8).all()
    assert (goals[:, 2] >= .7).all() and (goals[:, 2] <= 1.15).all()
    assert (np.abs(goals[:, :2]) > 5).any()  # caller rejects, never clamps
    assert abs(dist.mean()-4.25) < .2  # statistical test, not protocol threshold
    assert np.linalg.norm(goals[:, :2].mean(0)) < .2


def test_initialization_uses_actual_fk_and_full_collision():
    c, _ = scene()
    target = validate_initial_state(c.state.base, c.state.q, c.kin, c.capsules, c.collision)
    assert torch.equal(target, c.kin.world_tcp(c.state.base, c.state.q))
    q = c.state.q.clone(); q[:, 0] = 100
    with pytest.raises(ValueError, match='joint'): validate_initial_state(c.state.base, q, c.kin, c.capsules, c.collision)
    bad = c.state.base.clone(); bad[:, 0] = 4.9
    with pytest.raises(ValueError, match='collision'): validate_initial_state(bad, c.state.q, c.kin, c.capsules, c.collision)


def test_initial_rejection_budget_and_explicit_joint_policy():
    c, _ = scene()
    q0 = c.state.q[0].cpu().numpy()
    kwargs = dict(kin=c.kin, robot=c.capsules, collision=c.collision, device='cpu', dtype=torch.float64)
    a = sample_initial(np.random.default_rng(10), lambda rng: q0, max_attempts=100, **kwargs)
    b = sample_initial(np.random.default_rng(10), lambda rng: q0, max_attempts=100, **kwargs)
    assert all(torch.equal(x, y) for x, y in zip(a, b))
    validate_initial_state(a[0], a[1], c.kin, c.capsules, c.collision)
    assert torch.equal(a[1][0], c.state.q[0])
    with pytest.raises(RuntimeError, match='budget'):
        sample_initial(np.random.default_rng(10), lambda rng: np.full(6, 100), max_attempts=3, **kwargs)


def test_goal_position_and_actual_ik_witness_are_separate():
    c, _ = scene()
    goals = torch.tensor([[1., 0., .8], [4.99, 0., .8], [0., 0., .8], [1., 0., 1.2]], dtype=torch.float64)
    boxes = c.collision.boxes.expand(4, -1, -1); mask = c.collision.mask.expand(4, -1)
    valid = validate_goal_position(goals, c.state.base.expand(4, -1), boxes, mask)
    assert valid.tolist() == [True, False, False, False]
    target = c.kin.world_tcp(c.state.base, c.state.q)
    solved, valid = validate_goal_witness(c.state.base, c.state.q, target, c.kin, c.capsules, c.collision)
    assert solved.accepted.item() and valid.item()
    bad = target.clone(); bad[:, 0, 3] += 10
    _, valid = validate_goal_witness(c.state.base, c.state.q, bad, c.kin, c.capsules, c.collision)
    assert not valid.item()


def test_default_pool_sampler_fixed_cbl_joints_route_and_actual_witness():
    from task7_sim.episode import EpisodeSampler, CBL_Q
    sampler=EpisodeSampler(split='validation',device='cuda',dtype=torch.float32)
    streams=RandomStreams(4605,1)
    episode=sampler.sample(streams.for_env(0))
    assert torch.equal(episode.q[0],torch.tensor(CBL_Q,device='cuda',dtype=torch.float32))
    assert sampler.stats['accepted']==1 and sampler.stats['proposals']>=1
    goal=episode.route.at(episode.route.length)
    radius=(goal[0,:2,3]-episode.base[0,:2]).norm()
    assert .5<=radius<=8 and .7<=goal[0,2,3]<=1.15
    assert abs(goal[0,2,0])<1e-4 and abs(goal[0,2,1])<1e-4
    planner=sampler.planners[episode.map_id]
    assert planner.clear(episode.route.xyz[0].cpu().double().numpy())
    boxes=episode.boxes[None];mask=torch.ones(boxes.shape[:2],device='cuda',dtype=torch.bool)
    from task7_sim.geometry import TruthCollision
    result,valid=validate_goal_witness(episode.witness_base,episode.witness_q,goal,sampler.kin,sampler.robot,TruthCollision(boxes,mask,robot=sampler.robot))
    assert valid.item()
