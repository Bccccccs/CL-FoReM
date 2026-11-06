import heapq
import math
import numpy as np
import pytest
import torch
from task7_sim.routes import astar, interpolate_route, horizontal_goal


def test_astar_linf_diagonal_optimal_and_unreachable():
    w = np.ones((9, 9)); w[1:8, 4] = np.inf; w[7, 4] = 1
    path = astar(w, (1, 1), (1, 7))
    assert tuple(path[0]) == (1, 1) and tuple(path[-1]) == (1, 7)
    assert np.isfinite(w[tuple(path.T)]).all()
    assert np.abs(np.diff(path, axis=0)).max() == 1
    # Independent Dijkstra reference; destination-cell weights, unit diagonal.
    q = [(0., (1, 1))]; best = {(1, 1): 0.}
    while q:
        d, u = heapq.heappop(q)
        if d != best[u]: continue
        if u == (1, 7): break
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                v = (u[0]+dx, u[1]+dy)
                if (dx or dy) and all(0 <= x < 9 for x in v):
                    nd = d+w[v]
                    if nd < best.get(v, math.inf):
                        best[v] = nd; heapq.heappush(q, (nd, v))
    assert w[tuple(path[1:].T)].sum() == best[(1, 7)]
    w[:, 4] = np.inf
    with pytest.raises(ValueError, match='no path'): astar(w, (1, 1), (1, 7))


def test_astar_explicit_finite_obstacle_cost_is_not_a_collision_guarantee():
    w = np.ones((3, 3)); w[1] = 10001
    path = astar(w, (0, 0), (2, 2))
    assert (path[:, 0] == 1).any()
    for bad in (np.zeros((2, 2)), np.full((2, 2), np.nan)):
        with pytest.raises(ValueError): astar(bad, (0, 0), (1, 1))


def test_astar_matches_original_installed_backend_path_elementwise():
    import pyastar
    rng = np.random.default_rng(460)
    for _ in range(30):
        w = (1+rng.integers(0, 12, (12, 12))).astype(np.float32)
        original = pyastar.astar_path(w, (1, 1), (10, 10), allow_diagonal=True, costfn='linf')
        assert np.array_equal(astar(w, (1, 1), (10, 10)), original)


def test_explicit_linear_height_slerp_and_position_arc_contract():
    xy = torch.tensor([[0., 0.], [.3, 0.], [.3, .4]], dtype=torch.float64)
    start = torch.eye(4, dtype=xy.dtype); start[2, 3] = .8
    goal = horizontal_goal(torch.tensor([.3, .4, 1.1], dtype=xy.dtype), xy[-1]-xy[-2])
    r = interpolate_route(xy, start, goal)
    assert torch.all(r.s.diff(dim=1) > 0)
    torch.testing.assert_close(r.xyz[0, :, 2], torch.tensor([.8, .8+.3/.7*.3, 1.1], dtype=xy.dtype))
    torch.testing.assert_close(r.at(r.length)[0], goal)
    torch.testing.assert_close(r.at(torch.zeros_like(r.length))[0], start)
    assert (r.at(r.length/2)[0, :3, 3]-r.xyz[0, 0]).norm() > 0
    assert goal[2, 0] == 0 and goal[2, 1] == 0
    with pytest.raises(ValueError): horizontal_goal(goal[:3, 3], torch.zeros(2))
    with pytest.raises(ValueError): interpolate_route(xy[:1], start, goal)


def test_interpolation_explicit_height_and_cpu64_gpu32():
    xy = torch.tensor([[0., 0.], [.2, .3], [.4, .3]], dtype=torch.float64)
    a = torch.eye(4, dtype=xy.dtype); a[2, 3] = .8
    b = horizontal_goal(torch.tensor([.4, .3, 1.], dtype=xy.dtype), xy[-1]-xy[-2])
    z = torch.tensor([.8, 1.2, 1.], dtype=xy.dtype)
    r = interpolate_route(xy, a, b, heights=z)
    torch.testing.assert_close(r.xyz[0, :, 2], z)
    if torch.cuda.is_available():
        g = interpolate_route(xy.cuda().float(), a.cuda().float(), b.cuda().float(), heights=z.cuda().float())
        s = torch.linspace(0, r.length.item(), 17, dtype=xy.dtype)[None]
        torch.testing.assert_close(g.at(s.cuda().float()).cpu().double(), r.at(s), atol=1e-4, rtol=0)


def test_original_height_raise_and_continuous_segment_obstacle_rejection():
    from task7_sim.routes import original_heights, TruthPlanner
    s = np.array([0., 1., 2., 3., 4.])
    z = original_heights(s, np.array([0., .8, .8, 0., 0.]), .7, .9)
    np.testing.assert_allclose(z, [.7, 1.05, 1.05, 1.05, .9])
    planner = TruthPlanner({'boxes': [[-.1,-.5,0,.2,1.,1.,1.,0.]]})
    # Exact continuous test catches obstacle crossing between route vertices.
    assert not planner.clear(np.array([[-1.,0,.8],[1.,0,.8]]))
    assert planner.clear(np.array([[-1.,0,1.25],[1.,0,1.25]]))
    assert planner.weights.dtype == np.float32
    assert planner.weights.max() == 10001
    assert np.any(planner.weights == 9801)


def test_packed_route_selection_preserves_stored_metric_and_quaternion():
    from task7_sim.routes import batch_routes
    from task7_sim.motion import Route
    rng=np.random.default_rng(4618)
    xyz=torch.from_numpy(rng.normal(0,.1,(1,40,3)).cumsum(1))
    quat=torch.zeros(1,40,4,dtype=torch.float64);quat[...,3]=1
    source=Route(xyz,quat)
    packed=batch_routes([source,source],device='cuda',dtype=torch.float32)
    selected=packed.select(torch.tensor([1,0,1],device='cuda'))
    for name in ('xyz','quat','s','length'):
        assert torch.equal(getattr(selected,name),getattr(packed,name)[[1,0,1]]),name
