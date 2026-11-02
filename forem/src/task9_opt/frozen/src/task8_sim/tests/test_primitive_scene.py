"""task8.10 primitive-obb-v1 / primitive-voxel-diag: analytic oracles and boundary cases (CPU, no training)."""
import math
import pickle
import numpy as np
import pytest
import torch
from task7_sim.geometry import Collision
from task8_sim.primitive_assets import asset_from_boxes
from task8_sim.primitive_scene import (
    BACKEND, CONTACT_SLACK, DIAG_BACKEND, ENVIRONMENT_VERSION, PrimitiveScene, PrimitiveSceneBatch,
    PrimitiveVoxelDiagScene, derive_occupancy, make_scene_batch, planning_height_from, resolve_backend)
from task8_sim.scene import H, ORIGIN, SceneBatch, VoxelScene

torch.set_num_threads(1)
F64 = torch.float64
UNIT = [0, 0, 0, 1, 1, 1, 1, 0]
S2 = math.sqrt(2) / 2
DIAMOND = [0, 0, 0, 1, 1, 1, S2, S2]     # unit square rotated 45 deg about its min corner


def scene(rows, dtype=F64, name='t'):
    return PrimitiveScene.from_asset(asset_from_boxes(name, rows, allow_empty=True), device='cpu', dtype=dtype)


def T(x, dtype=F64):
    return torch.tensor(x, dtype=dtype)


def ray(s, o, d, maximum=10.):
    d = np.asarray(d, float); d = d / np.linalg.norm(d)
    return s.raycast(T([[o]], s.dtype), T([[d.tolist()]], s.dtype), max_range=maximum).item()


# ----------------------------------------------------------------------------- independent oracles
def oracle_ray(box, o, d, max_range):
    """Cyrus-Beck clipping of rays against the six world-frame half-spaces of one OBB."""
    x0, y0, z0, sx, sy, sz, c, s = box
    corner = np.array([x0, y0, z0]); u = np.array([c, s, 0.]); v = np.array([-s, c, 0.]); w = np.array([0., 0., 1.])
    lo = np.zeros(len(o)); hi = np.full(len(o), float(max_range)); ok = np.ones(len(o), bool)
    for n, off in ((-u, 0.), (u, sx), (-v, 0.), (v, sy), (-w, 0.), (w, sz)):
        den = d @ n; num = off - (o - corner) @ n
        par = den == 0
        ok &= ~(par & (num < 0))
        with np.errstate(divide='ignore', invalid='ignore'):
            t = num / den
        hi = np.where(~par & (den > 0), np.minimum(hi, t), hi)
        lo = np.where(~par & (den < 0), np.maximum(lo, t), lo)
    ok &= lo <= hi
    return np.where(ok, lo, np.inf)


def oracle_ray_scene(boxes, o, d, max_range):
    return np.min([oracle_ray(b, o, d, max_range) for b in boxes], axis=0)


def random_boxes(rng, n, spread=3.):
    th = rng.uniform(-math.pi, math.pi, n)
    return np.c_[rng.uniform(-spread, spread, (n, 2)), rng.uniform(0, .6, n), rng.uniform(.2, 1.5, (n, 3)), np.cos(th), np.sin(th)]


def polygon(x0, y0, sx, sy, c, s):
    return np.array([[x0, y0], [x0 + sx * c, y0 + sx * s], [x0 + sx * c - sy * s, y0 + sx * s + sy * c], [x0 - sy * s, y0 + sy * c]])


def point_in_convex(p, poly):
    cross = [(poly[(i + 1) % 4, 0] - poly[i, 0]) * (p[1] - poly[i, 1]) - (poly[(i + 1) % 4, 1] - poly[i, 1]) * (p[0] - poly[i, 0]) for i in range(4)]
    return all(v >= 0 for v in cross) or all(v <= 0 for v in cross)


def segments_intersect(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    def on(p, q, r):
        return min(p[0], q[0]) <= r[0] <= max(p[0], q[0]) and min(p[1], q[1]) <= r[1] <= max(p[1], q[1])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    return (o1 == 0 and on(a, b, c)) or (o2 == 0 and on(a, b, d)) or (o3 == 0 and on(c, d, a)) or (o4 == 0 and on(c, d, b))


def polygons_intersect(P, Q):
    if any(point_in_convex(p, Q) for p in P) or any(point_in_convex(q, P) for q in Q):
        return True
    return any(segments_intersect(P[i], P[(i + 1) % 4], Q[j], Q[(j + 1) % 4]) for i in range(4) for j in range(4))


def oracle_occupancy(boxes):
    """Cell-by-cell closed intersection with a polygon-polygon test (vertex-in / edge crossing) and a z interval."""
    occ = np.zeros((32, 200, 200), bool)
    for b in boxes:
        x0, y0, z0, sx, sy, sz, c, s = b
        poly = polygon(x0, y0, sx, sy, c, s)
        for iy in range(200):
            ya, yb = ORIGIN[1] + iy * H, ORIGIN[1] + (iy + 1) * H
            if yb < poly[:, 1].min() or ya > poly[:, 1].max():
                continue
            for ix in range(200):
                xa, xb = ORIGIN[0] + ix * H, ORIGIN[0] + (ix + 1) * H
                if xb < poly[:, 0].min() or xa > poly[:, 0].max():
                    continue
                if not polygons_intersect(poly, np.array([[xa, ya], [xb, ya], [xb, yb], [xa, yb]])):
                    continue
                for k in range(32):
                    if k * H <= z0 + sz and (k + 1) * H >= z0:
                        occ[k, iy, ix] = True
    return occ


def oracle_capsule_distance(box, a, b):
    """Convex distance along the segment minimised by ternary search; point-to-OBB distance by clamping."""
    x0, y0, z0, sx, sy, sz, c, s = box
    size = np.array([sx, sy, sz])
    def dist_point(p):
        r = p - np.array([x0, y0, z0]); q = np.array([c * r[0] + s * r[1], -s * r[0] + c * r[1], r[2]])
        return np.linalg.norm(q - np.clip(q, 0, size))
    lo, hi = 0., 1.
    for _ in range(60):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if dist_point(a + m1 * (b - a)) < dist_point(a + m2 * (b - a)):
            hi = m2
        else:
            lo = m1
    return dist_point(a + (lo + hi) / 2 * (b - a))


# ----------------------------------------------------------------------------- raycast
def test_ray_faces_edges_corners_closed_and_one_nanometre_outside():
    s = scene([UNIT])
    assert ray(s, [-1, .5, .5], [1, 0, 0]) == 1.0
    assert ray(s, [-1, 0., .5], [1, 0, 0]) == 1.0          # grazing along the y=0 face: closed
    assert ray(s, [-1, 1., .5], [1, 0, 0]) == 1.0          # grazing along the y=1 face
    assert ray(s, [-1, 0., 0.], [1, 0, 0]) == 1.0          # along an edge
    assert math.isinf(ray(s, [-1, -1e-9, .5], [1, 0, 0]))
    assert math.isinf(ray(s, [-1, 1 + 1e-9, .5], [1, 0, 0]))
    assert math.isinf(ray(s, [-1, .5, 1 + 1e-9], [1, 0, 0]))
    assert ray(s, [-1, -1, .5], [1, 1, 0]) == pytest.approx(math.sqrt(2), abs=1e-12)    # exactly through the corner column


def test_ray_origin_inside_or_on_surface_returns_zero_and_range_cut():
    s = scene([UNIT])
    assert ray(s, [.5, .5, .5], [1, 0, 0]) == 0.0
    assert ray(s, [0., .5, .5], [-1, 0, 0]) == 0.0         # on the face, looking out
    assert ray(s, [1., .5, .5], [1, 0, 0]) == 0.0          # on the opposite face, looking out
    assert math.isinf(ray(s, [1 + 1e-9, .5, .5], [1, 0, 0]))
    assert ray(s, [-1, .5, .5], [1, 0, 0], maximum=1.0) == 1.0      # entry exactly at range
    assert math.isinf(ray(s, [-1, .5, .5], [1, 0, 0], maximum=1.0 - 1e-9))
    assert math.isinf(ray(s, [-1, .5, .5], [-1, 0, 0]))              # box behind


def test_ray_rotated_box_analytic_distances():
    s = scene([DIAMOND])
    assert ray(s, [-2, 1., .5], [1, 0, 0]) == pytest.approx(2 + (1 - math.sqrt(2)), abs=1e-12)
    assert ray(s, [-2, S2, .5], [1, 0, 0]) == pytest.approx(2 - S2, abs=1e-12)     # through the left vertex, chord inside
    assert math.isinf(ray(s, [-2, math.sqrt(2) + 1e-6, .5], [1, 0, 0]))
    assert ray(s, [-2, math.sqrt(2) - 1e-6, .5], [1, 0, 0]) < math.inf
    assert math.isinf(ray(s, [-2, -1e-6, .5], [1, 0, 0]))


def test_ray_matches_cyrus_beck_oracle_float64_and_float32():
    rng = np.random.default_rng(7)
    boxes = random_boxes(rng, 12)
    o = np.c_[rng.uniform(-4, 4, (3000, 2)), rng.uniform(0, 1.2, 3000)]
    d = rng.normal(size=(3000, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
    d[:200, 2] = 0; d[:200] /= np.linalg.norm(d[:200], axis=1, keepdims=True)        # horizontal rays
    d[200:260] = np.eye(3)[rng.integers(0, 3, 60)] * rng.choice([-1., 1.], (60, 1))   # axis-parallel rays
    expected = oracle_ray_scene(boxes, o, d, 6.)
    for dtype, tol in ((F64, 1e-9), (torch.float32, 2e-3)):
        s = scene(boxes, dtype)
        got = s.raycast(T(o[None], dtype), T(d[None], dtype), max_range=6.)[0].double().numpy()
        both = np.isfinite(expected) & np.isfinite(got)
        assert np.abs(got[both] - expected[both]).max() <= tol
        if dtype == F64:
            assert (np.isfinite(got) == np.isfinite(expected)).all()
        else:
            assert (np.isfinite(got) != np.isfinite(expected)).sum() <= 6       # float32 grazing/range-edge disagreements only
    assert np.isfinite(expected).sum() > 300


def test_ray_validation_rejects_bad_input_and_mixed_dtype():
    s = scene([UNIT])
    o, d = T([[[0., 0., 0.]]]), T([[[1., 0., 0.]]])
    with pytest.raises(ValueError, match='unit'):
        s.raycast(o, T([[[2., 0., 0.]]]), max_range=1.)
    with pytest.raises(ValueError, match='device/dtype'):
        s.raycast(o.float(), d.float(), max_range=1.)
    with pytest.raises(ValueError, match='max_range'):
        s.raycast(o, d, max_range=float('inf'))
    with pytest.raises(ValueError, match='finite'):
        s.raycast(T([[[float('nan'), 0., 0.]]]), d, max_range=1.)
    with pytest.raises(ValueError, match='E,R,3'):
        s.raycast(o[0], d[0], max_range=1.)


def test_primitive_outside_data_domain_is_real_geometry_and_no_ground_plane():
    s = scene([[4.9, 0, 0, 2.5, 1, 1, 1, 0]])          # x to 7.4, beyond [-5,5)
    assert ray(s, [7., .5, .5], [-1, 0, 0]) == 0.0      # origin inside the out-of-domain part
    assert ray(s, [7.4 + 1, .5, .5], [-1, 0, 0]) == pytest.approx(1.0, abs=1e-12)
    assert math.isinf(ray(s, [0, 0, .5], [0, 0, -1]))    # PCD-free P has no implicit ground (ground is added by the panorama)
    assert s.contains(T([[6., .5, .5]])).item()


# ----------------------------------------------------------------------------- contains
def test_contains_closed_faces_edges_corners_and_boundary_offsets():
    s = scene([UNIT])
    inside = [[.5, .5, .5], [0, 0, 0], [1, 1, 1], [1, 0, .5], [0, .5, 1], [.3, 1, .3]]
    assert s.contains(T(inside)).all()
    eps = 1e-9
    outside = [[-eps, .5, .5], [1 + eps, .5, .5], [.5, -eps, .5], [.5, 1 + eps, .5], [.5, .5, -eps], [.5, .5, 1 + eps], [1 + eps, 1 + eps, 1 + eps]]
    assert not s.contains(T(outside)).any()
    assert s.contains(T([[.5, .5, .5]] * 2).reshape(2, 1, 3)).shape == (2, 1)
    assert not scene([]).contains(T([[0., 0., 0.]])).any()


def test_contains_rotated_box_matches_oracle_and_corners_in_the_boundary_band():
    s = scene([DIAMOND])
    u, v, e = np.array([S2, S2]), np.array([-S2, S2]), 1e-9
    inward = [a * u + b * v for a, b in ((e, e), (1 - e, e), (1 - e, 1 - e), (e, 1 - e))]       # 1e-9 inside each corner
    assert s.contains(T([[*q, .5] for q in inward])).all()
    assert not s.contains(T([[0, -1e-6, .5], [S2 + 1e-6, S2, .5], [0, math.sqrt(2) + 1e-6, .5]])).any()
    rng = np.random.default_rng(3)
    boxes = random_boxes(rng, 8); p = rng.uniform(-3.5, 3.5, (4000, 3)); p[:, 2] = rng.uniform(-.1, 1.5, 4000)
    poly = lambda b: polygon(b[0], b[1], b[3], b[4], b[6], b[7])
    expected = np.array([any(point_in_convex(q[:2], poly(b)) and b[2] <= q[2] <= b[2] + b[5] for b in boxes) for q in p])
    got = scene(boxes).contains(T(p)).numpy()
    assert (got == expected).all() and expected.sum() > 100


# ----------------------------------------------------------------------------- chassis / arm
def collide_base(s, x, y, yaw):
    base = T([[x, y, yaw]]); caps = torch.empty(1, 0, 7, dtype=F64)
    return s.collide(base, caps, robot=None).base.item()


def test_chassis_touching_collides_and_gap_does_not():
    wall = [.495, -.1, 0, 1, .2, 1, 1, 0]
    assert collide_base(scene([wall]), 0, 0, 0)
    assert not collide_base(scene([[.495 + 1e-9, -.1, 0, 1, .2, 1, 1, 0]]), 0, 0, 0)
    assert collide_base(scene([[.335 - 1e-9, -.1, 0, 1, .2, 1, 1, 0]]), 0, 0, math.pi / 2)
    assert not collide_base(scene([[.335 + 1e-9, -.1, 0, 1, .2, 1, 1, 0]]), 0, 0, math.pi / 2)
    assert collide_base(scene([[.2, -.1, 1.2, 1, .2, .2, 1, 0]]), 0, 0, 0)           # floating obstacle: full-height XY projection
    assert not collide_base(scene([]), 0, 0, 0)


def test_chassis_matches_polygon_oracle_with_rotated_boxes():
    rng = np.random.default_rng(11)
    boxes = random_boxes(rng, 6, spread=2.)
    s = scene(boxes)
    base = np.c_[rng.uniform(-3, 3, (1500, 2)), rng.uniform(-math.pi, math.pi, 1500)]
    got = s.collide(T(base), torch.empty(1500, 0, 7, dtype=F64), robot=None).base.numpy()
    def footprint(x, y, yaw):
        return polygon(x - .495 * math.cos(yaw) + .335 * math.sin(yaw), y - .495 * math.sin(yaw) - .335 * math.cos(yaw), .99, .67, math.cos(yaw), math.sin(yaw))
    expected = np.array([any(polygons_intersect(footprint(*b), polygon(r[0], r[1], r[3], r[4], r[6], r[7])) for r in boxes) for b in base])
    assert (got == expected).all() and 100 < expected.sum() < 1400


def collide_arm(s, a, b, r):
    caps = T([[[*a, *b, r]]])
    return s.collide(T([[9., 9., 0.]]), caps, robot=None).arm.item()


def test_arm_contact_hits_and_gap_misses_axis_aligned():
    s = scene([UNIT])
    assert collide_arm(s, [-.5, .5, .7], [-.5, .5, .7], .5)               # sphere exactly touching the x=0 face
    assert not collide_arm(s, [-.5, .5, .7], [-.5, .5, .7], .5 - 1e-9)
    assert collide_arm(s, [-1, .5, .5], [2, .5, .5], .01)                 # through the box
    assert not collide_arm(s, [-1, .5, 1.5], [2, .5, 1.5], .4)            # passes 0.5 above the top
    assert collide_arm(s, [-1, .5, 1.5], [2, .5, 1.5], .5)                # touching the top face
    assert collide_arm(s, [-.5, -.5, .9], [-.5, -.5, .9], math.sqrt(.5))  # vertical-edge distance sqrt(0.5)


def test_arm_ground_check_and_empty_scene():
    empty = scene([])
    assert collide_arm(empty, [0, 0, .1], [0, 0, .5], .1)                 # lowest sphere surface touches z=0
    assert not collide_arm(empty, [0, 0, .1 + 1e-9], [0, 0, .5], .1)
    assert not empty.collide(T([[0., 0., 0.]]), torch.empty(1, 0, 7, dtype=F64), robot=None).arm.item()


def test_arm_distance_matches_ternary_oracle_for_rotated_boxes_and_collide_agrees():
    rng = np.random.default_rng(5)
    boxes = random_boxes(rng, 5, spread=2.)
    s = scene(boxes)
    n = 150
    a = rng.uniform(-3, 3, (n, 3)); a[:, 2] = rng.uniform(0, 1.5, n)
    b = a + rng.normal(size=(n, 3)) * .8
    got = s.capsule_distance(T(a), T(b)).numpy()
    expected = np.array([min(oracle_capsule_distance(bx, p, q) for bx in boxes) for p, q in zip(a, b)])
    assert np.abs(got - expected).max() <= 1e-9
    r = np.full(n, .15)
    caps = torch.tensor(np.c_[a, b, r])[:, None, :]
    flags = s.collide(T(np.c_[np.full((n, 2), 9.), np.zeros(n)]), caps, robot=None).arm.numpy()
    ground = np.minimum(a[:, 2], b[:, 2]) - r <= 0
    assert (flags == ((expected <= r) | ground)).all()


def test_collide_validation_and_self_collision_path_is_task7_self_hits():
    s = scene([UNIT])
    with pytest.raises(ValueError, match='negative capsule radius'):
        s.collide(T([[0., 0., 0.]]), T([[[0., 0., 0., 0., 0., 1., -.1]]]), robot=None)
    with pytest.raises(ValueError, match='expected tensor'):
        s.collide(T([[0., 0.]]), torch.empty(1, 0, 7, dtype=F64), robot=None)
    # two overlapping capsules of the (robot=None) self_hits path
    caps = T([[[5., 5., .5, 5., 5., .9, .1], [5., 5., .5, 5., 5., .9, .1]]])
    out = s.collide(T([[9., 9., 0.]]), caps, robot=None)
    assert isinstance(out, Collision) and out.self_collision.item() and out.any.item()


# ----------------------------------------------------------------------------- derived occupancy
def test_derived_occupancy_axis_aligned_closed_contact_cells():
    occ, counts = derive_occupancy(np.array([[.1, .2, .05, .3, .3, .3, 1, 0]]), per_box=True)
    # closed: touching neighbour cells included -> 8 per axis
    assert counts == [512] and occ.sum() == 512
    xs, ys, zs = (np.flatnonzero(occ.any(a)) for a in ((0, 1), (0, 2), (1, 2)))
    assert (xs.min(), xs.max(), ys.min(), ys.max(), zs.min(), zs.max()) == (101, 108, 103, 110, 0, 7)
    assert planning_height_from(occ)[110, 108] == pytest.approx(.4)


def test_derived_occupancy_equals_closed_polygon_oracle_for_rotated_boxes():
    rng = np.random.default_rng(21)
    boxes = random_boxes(rng, 4, spread=2.5)
    got = derive_occupancy(boxes)
    expected = oracle_occupancy(boxes)
    assert (got == expected).all() and got.sum() > 500


def test_derived_occupancy_no_internal_gap_and_thin_boxes_keep_a_cell():
    th = .61
    box = np.array([[-1.03, -.77, 0.012, 1.9, 1.3, .8, math.cos(th), math.sin(th)]])
    occ = derive_occupancy(box)
    # every voxel whose eight corners are strictly inside the closed OBB must be occupied
    ii = np.argwhere(np.ones((32, 200, 200), bool))
    centres = np.c_[ORIGIN[0] + (ii[:, 2] + .5) * H, ORIGIN[1] + (ii[:, 1] + .5) * H, (ii[:, 0] + .5) * H]
    c, s = math.cos(th), math.sin(th)
    r = centres - box[0, :3]; q = np.c_[c * r[:, 0] + s * r[:, 1], -s * r[:, 0] + c * r[:, 1], r[:, 2]]
    deep = ((q > H * .8660255) & (q < box[0, 3:6] - H * .8660255)).all(1)
    assert deep.sum() > 100 and occ[ii[deep, 0], ii[deep, 1], ii[deep, 2]].all()
    thin = derive_occupancy(np.array([[0.123, 0.456, 0.789, 1e-3, 1.0, 1e-3, 1, 0]]), per_box=True)
    assert thin[1][0] >= 1 and thin[0].sum() >= 1
    outside, c0 = derive_occupancy(np.array([[7., 7., 0., 1, 1, 1, 1, 0]]), per_box=True)
    assert c0 == [0] and not outside.any()


def test_scene_occupancy_height_and_provenance_fields():
    s = scene([[.1, .2, 0., .3, .3, .82, 1, 0]], name='prov')
    occ = s.occupancy
    assert occ.shape == (32, 200, 200) and occ.sum().item() == 8 * 8 * 17       # z cells 0..16 (cell 16 = [.80,.85] contains the .82 top)
    assert s.planning_height().max().item() == pytest.approx(.85)
    p = s.provenance()
    assert p['backend'] == p['map_backend'] == BACKEND == 'primitive-obb-v1'
    assert p['environment_version'] == ENVIRONMENT_VERSION == 'task8-prim-v1'
    assert p['hashes']['boxes'] and p['primitive_count'] == 1 and p['map_id'] == 'prov'
    assert p['cache_key'][1:3] == [BACKEND, ENVIRONMENT_VERSION] and 'pcd-voxel-v3' not in p['cache_key']
    s.occupancy.zero_(); p['map_id'] = 'x'
    assert s.occupancy.sum().item() > 0 and s.provenance()['map_id'] == 'prov'     # independent copies


def test_empty_scene_and_resolution_constants():
    s = scene([])
    assert s.occupancy.sum().item() == 0 and s.planning_height().sum().item() == 0
    assert math.isinf(ray(s, [0, 0, .5], [1, 0, 0])) and not s.contains(T([[0., 0., 0.]])).any()
    assert CONTACT_SLACK == 1e-12


# ----------------------------------------------------------------------------- PV
def test_pv_uses_derived_occupancy_through_v3_voxel_queries():
    asset = asset_from_boxes('pv', [[.1, .2, .05, .3, .3, .3, 1, 0]])
    p = PrimitiveScene.from_asset(asset, device='cpu', dtype=F64)
    pv = PrimitiveVoxelDiagScene.from_asset(asset, device='cpu', dtype=F64)
    assert isinstance(pv, VoxelScene) and torch.equal(pv.occupancy, p.occupancy) and torch.equal(pv.planning_height(), p.planning_height())
    assert pv.provenance()['backend'] == DIAG_BACKEND == 'primitive-voxel-diag' and pv.provenance()['hashes'] == p.provenance()['hashes']
    # the box starts at x=.1 but the derived voxel face is at x=.05 (cell 101 touches): the 0.05 m discretisation PV isolates
    o, d = T([[[-1., .35, .2]]]), T([[[1., 0., 0.]]])
    assert p.raycast(o, d, max_range=5.).item() == pytest.approx(1.1)
    assert pv.raycast(o, d, max_range=5.).item() == pytest.approx(1.05)
    assert SceneBatch([pv, pv]).raycast(o.expand(2, -1, -1), d.expand(2, -1, -1), max_range=5.).tolist() == [[pytest.approx(1.05)]] * 2


# ----------------------------------------------------------------------------- batch
def test_batch_forest_equals_loop_equals_oracle_for_heterogeneous_scenes():
    rng = np.random.default_rng(13)
    scenes_rows = [random_boxes(rng, n) for n in (3, 9, 1, 6)]
    scenes = [scene(r) for r in scenes_rows]
    batch = PrimitiveSceneBatch([scenes[0], scenes[1], scenes[0], scenes[2], scenes[3]])
    loop = PrimitiveSceneBatch(batch.scenes, raycast_backend='loop')
    o = T(rng.uniform(-3, 3, (5, 40, 3))); o[..., 2] = .5
    d = torch.tensor(rng.normal(size=(5, 40, 3))); d = d / d.norm(dim=-1, keepdim=True)
    a, b = batch.raycast(o, d, max_range=5.), loop.raycast(o, d, max_range=5.)
    assert torch.equal(a, b)
    rows = [scenes_rows[i] for i in (0, 1, 0, 2, 3)]
    for e in range(5):
        expected = oracle_ray_scene(rows[e], o[e].numpy(), d[e].numpy(), 5.)
        assert np.array_equal(np.isfinite(expected), np.isfinite(a[e].numpy())) and np.nanmax(np.abs(np.where(np.isfinite(expected), a[e].numpy() - expected, 0))) < 1e-9
    pts = T(rng.uniform(-3, 3, (5, 17, 3)))
    assert torch.equal(batch.contains(pts), torch.stack([s.contains(pts[i]) for i, s in enumerate(batch.scenes)]))
    base = T(np.c_[rng.uniform(-2, 2, (5, 2)), rng.uniform(-3, 3, 5)]); caps = T(rng.uniform(-2, 2, (5, 3, 7))); caps[..., 6] = .1
    got = batch.collide(base, caps, robot=None)
    for e, s in enumerate(batch.scenes):
        one = s.collide(base[e:e + 1], caps[e:e + 1], robot=None)
        assert got.base[e] == one.base[0] and got.arm[e] == one.arm[0] and got.self_collision[e] == one.self_collision[0]
    assert len(batch) == 5 and batch.device == torch.device('cpu') and batch.dtype == F64
    assert [p['map_id'] for p in batch.provenance()] == ['t'] * 5 and batch.planning_height().shape == (5, 200, 200)


def test_batch_select_replace_validation_and_transaction():
    a, b = scene([UNIT]), scene([[3, 0, 0, 1, 1, 1, 1, 0]])
    batch = PrimitiveSceneBatch([a, b, a])
    sel = batch.select(torch.tensor([2, 1]))
    assert sel.scenes == (a, b) and sel.raycast_backend == 'forest'
    o, d = T([[[-1., .5, .5]]]).expand(3, -1, -1), T([[[1., 0., 0.]]]).expand(3, -1, -1)
    assert batch.raycast(o, d, max_range=10.)[:, 0].tolist() == [1., 4., 1.]
    batch.replace([1], [a])
    assert batch.raycast(o, d, max_range=10.)[:, 0].tolist() == [1., 1., 1.]
    for bad in ([0, 0], [3], [-1], [True]):
        with pytest.raises(ValueError):
            batch.replace(bad, [a] * len(bad))
    with pytest.raises(ValueError, match='nonempty'):
        batch.replace([0], [scene([UNIT]).occupancy])      # not a scene -> transaction rejected
    assert batch.scenes == (a, a, a)
    with pytest.raises(ValueError, match='device/dtype'):
        PrimitiveSceneBatch([a, scene([UNIT], torch.float32)])
    with pytest.raises(ValueError, match='nonempty'):
        PrimitiveSceneBatch([])
    with pytest.raises(ValueError, match='rows'):
        batch.raycast(o[:2], d[:2], max_range=1.)
    with pytest.raises(ValueError, match='forest or loop'):
        PrimitiveSceneBatch([a], raycast_backend='bvh')


def test_scene_and_batch_pickle_roundtrip_rebuilds_bank():
    rng = np.random.default_rng(2)
    s = scene(random_boxes(rng, 5)); batch = PrimitiveSceneBatch([s, s])
    o, d = T(rng.uniform(-2, 2, (2, 10, 3))), torch.tensor(rng.normal(size=(2, 10, 3))); d = d / d.norm(dim=-1, keepdim=True)
    before = batch.raycast(o, d, max_range=5.)        # populates the bank cache
    s2, batch2 = pickle.loads(pickle.dumps(s)), pickle.loads(pickle.dumps(batch))
    assert batch2._bank is None and s2._bank1 is None
    assert torch.equal(batch2.raycast(o, d, max_range=5.), before)
    assert torch.equal(s2.raycast(o[:1], d[:1], max_range=5.), before[:1])
    assert s2.provenance() == s.provenance() and torch.equal(s2.occupancy, s.occupancy)


def test_interface_names_and_signatures_match_v3():
    import inspect
    for name in ('raycast', 'contains', 'collide', 'planning_height', 'provenance'):
        assert str(inspect.signature(getattr(PrimitiveScene, name))) == str(inspect.signature(getattr(VoxelScene, name))), name
    assert isinstance(PrimitiveScene.occupancy, property) and isinstance(VoxelScene.occupancy, property)
    assert str(inspect.signature(PrimitiveScene.from_asset)) == str(inspect.signature(VoxelScene.from_asset))
    for name in ('raycast', 'contains', 'collide', 'planning_height', 'provenance', 'select', 'replace', '__len__'):
        assert str(inspect.signature(getattr(PrimitiveSceneBatch, name))) == str(inspect.signature(getattr(SceneBatch, name))), name
    for name in ('scenes', 'device', 'dtype'):
        assert isinstance(getattr(PrimitiveSceneBatch, name), property)
    assert str(inspect.signature(PrimitiveSceneBatch.__init__)) == str(inspect.signature(SceneBatch.__init__))


def test_backend_names_factory_and_default_is_v3():
    assert resolve_backend('pcd-voxel-v3') == 'pcd-voxel-v3' and resolve_backend(BACKEND) and resolve_backend(DIAG_BACKEND)
    with pytest.raises(ValueError, match='map_backend'):
        resolve_backend('primitive-obb-v2')
    a = scene([UNIT])
    assert isinstance(make_scene_batch([a, a]), PrimitiveSceneBatch)
    pv = PrimitiveVoxelDiagScene.from_asset(asset_from_boxes('pv', [UNIT]), device='cpu', dtype=F64)
    assert type(make_scene_batch([pv])) is SceneBatch
    from task8_sim.episode import PcdEpisodeSampler
    import inspect
    assert inspect.signature(PcdEpisodeSampler.__init__).parameters['map_backend'].default == 'pcd-voxel-v3'
    from task8_sim.env import PcdEpisodeEnv
    assert inspect.signature(PcdEpisodeEnv.__init__).parameters['map_backend'].default == 'pcd-voxel-v3'
    from task8_sim.decision_env import PcdDecisionEnv
    assert inspect.signature(PcdDecisionEnv.__init__).parameters['map_backend'].default == 'pcd-voxel-v3'


def test_config_file_matches_code_constants():
    import json
    from pathlib import Path
    cfg = json.loads((Path(__file__).resolve().parents[3] / 'config/task8/primitive_scene.json').read_text())
    assert cfg['backends'] == dict(default='pcd-voxel-v3', candidate=BACKEND, diagnostic=DIAG_BACKEND)
    assert cfg['environment_version'] == ENVIRONMENT_VERSION
    assert cfg['tolerances']['derived_occupancy_contact_slack_m'] == CONTACT_SLACK
    assert cfg['tolerances']['rotation_unit_error'] == 1e-6 and cfg['tolerances']['objects_vs_boxes_m'] == 1e-9
