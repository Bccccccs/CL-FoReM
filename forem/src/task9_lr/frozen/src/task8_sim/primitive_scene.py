"""primitive-obb-v1 (P) and primitive-voxel-diag (PV) scene backends, task8.10.

JSON primitives (closed oriented boxes) are the single geometric truth
(SRC-1181). ``PrimitiveScene`` mirrors the ``VoxelScene``/``SceneBatch`` query
interface but answers it analytically:

* raycast: ray transformed into each box's local frame, closed slab test,
  origin inside a box returns 0 (same slab arithmetic as ``scene._slab``);
* contains: closed local-frame test;
* collide: chassis 0.99 x 0.67 full-height XY SAT (touching collides), arm
  capsule-to-OBB distance (task7 piecewise-quadratic segment-box distance in
  the box frame, ``<= r`` collides), ground check, self collision unchanged
  (``scene._self_collision``);
* occupancy/planning_height: derived 0.05 m voxels intersecting the closed OBB
  (exact 3D SAT, see ``derive_occupancy``); never used by scan/collision.

Nothing is padded, scaled, clipped or walled. Primitives beyond the data domain
remain real geometry; only the derived occupancy is limited to the domain.
Batched queries are tensorised across environments (padded per-scene box banks)
with bounded intermediate size; there is no per-environment Python loop.

``PrimitiveVoxelDiagScene`` (PV, diagnostic arm) feeds the same derived
occupancy to the existing v3 packing/BVH query path.
"""
from copy import deepcopy
import math
import time
import numpy as np
import torch
from torch.nn.utils.rnn import pad_sequence
from task7_sim.geometry import Collision
from .scene import (H, ORIGIN, SHAPE_ZYX, SceneBatch, VoxelScene, _bvh, _pack,
                    _segment_bounds_distance_squared, _self_collision)
from .primitive_assets import BACKEND, PrimitiveAsset, load_primitive_asset

DIAG_BACKEND = 'primitive-voxel-diag'
V3_BACKEND = 'pcd-voxel-v3'
BACKENDS = (V3_BACKEND, BACKEND, DIAG_BACKEND)
ENVIRONMENT_VERSION = 'task8-prim-v1'
CONTACT_SLACK = 1e-12      # closure slack of derived occupancy, metres (<< 1e-9 band; engineering choice)
BROAD_PAD = 1e-5           # broad-phase AABB padding only (never decides a hit)
CHASSIS_HALF = (.495, .335)
PAIR_BUDGET = 1 << 22      # ray/point x box pairs per bounded chunk
CAPSULE_PAIR_CHUNK = 1 << 20


def resolve_backend(name):
    if name not in BACKENDS:
        raise ValueError(f'unsupported map_backend {name!r}; choose one of {BACKENDS}')
    return name


# --------------------------------------------------------------------------- derived occupancy
def derive_occupancy(boxes, *, slack=CONTACT_SLACK, per_box=False):
    """Voxels (0.05 m, domain [-5,5)^2 x [0,1.6)) intersecting a closed OBB.

    Exact 3D SAT: both solids are prisms along z, so the 15 SAT axes reduce to
    z, world x/y (= OBB AABB overlap) and the OBB axes u, v. Contact counts as
    intersection; ``slack`` absorbs float64 representation of decimal contact
    coordinates. Boxes are not clipped; cells outside the domain do not exist.
    """
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 8)
    nz, ny, nx = SHAPE_ZYX
    occ = np.zeros(SHAPE_ZYX, dtype=np.bool_)
    counts = []
    for x0, y0, z0, sx, sy, sz, c, s in boxes:
        cx = x0 + np.array([0., sx * c, -sy * s, sx * c - sy * s])
        cy = y0 + np.array([0., sx * s, sy * c, sx * s + sy * c])
        ix0 = max(0, int(math.floor((cx.min() - ORIGIN[0]) / H)) - 1)
        ix1 = min(nx, int(math.ceil((cx.max() - ORIGIN[0]) / H)) + 1)
        iy0 = max(0, int(math.floor((cy.min() - ORIGIN[1]) / H)) - 1)
        iy1 = min(ny, int(math.ceil((cy.max() - ORIGIN[1]) / H)) + 1)
        kz0 = max(0, int(math.floor((z0 - slack) / H)) - 1)
        kz1 = min(nz, int(math.ceil((z0 + sz + slack) / H)) + 1)
        if ix0 >= ix1 or iy0 >= iy1 or kz0 >= kz1:
            counts.append(0); continue
        k = np.arange(kz0, kz1)
        zmask = (k * H <= z0 + sz + slack) & ((k + 1) * H >= z0 - slack)
        if not zmask.any():
            counts.append(0); continue
        xa = ORIGIN[0] + np.arange(ix0, ix1) * H
        xb = ORIGIN[0] + (np.arange(ix0, ix1) + 1) * H
        ya = ORIGIN[1] + np.arange(iy0, iy1) * H
        yb = ORIGIN[1] + (np.arange(iy0, iy1) + 1) * H
        X0, X1 = xa[None, :], xb[None, :]
        Y0, Y1 = ya[:, None], yb[:, None]
        m = (X0 <= cx.max() + slack) & (X1 >= cx.min() - slack) & (Y0 <= cy.max() + slack) & (Y1 >= cy.min() - slack)
        # box axis u = (c, s): cell interval vs [u.corner, u.corner + sx]
        pu_lo = np.minimum(c * X0, c * X1) + np.minimum(s * Y0, s * Y1)
        pu_hi = np.maximum(c * X0, c * X1) + np.maximum(s * Y0, s * Y1)
        bu0 = c * x0 + s * y0
        m = m & (pu_lo <= bu0 + sx + slack) & (pu_hi >= bu0 - slack)
        # box axis v = (-s, c)
        pv_lo = np.minimum(-s * X0, -s * X1) + np.minimum(c * Y0, c * Y1)
        pv_hi = np.maximum(-s * X0, -s * X1) + np.maximum(c * Y0, c * Y1)
        bv0 = -s * x0 + c * y0
        m = m & (pv_lo <= bv0 + sy + slack) & (pv_hi >= bv0 - slack)
        selected = k[zmask]
        occ[selected[:, None, None], np.arange(iy0, iy1)[None, :, None], np.arange(ix0, ix1)[None, None, :]] |= m[None]
        counts.append(int(m.sum()) * int(zmask.sum()))
    return (occ, counts) if per_box else occ


def planning_height_from(occ):
    """v3 definition: top face of the highest occupied voxel of each XY column."""
    return np.where(occ, np.arange(1, SHAPE_ZYX[0] + 1)[:, None, None] * H, 0).max(0)


# --------------------------------------------------------------------------- padded box bank
class _Bank:
    """Per-unique-scene boxes padded to a common length (invalid rows are masked)."""

    def __init__(self, scenes):
        lengths = torch.tensor([len(s._corner) for s in scenes], device=scenes[0].device)
        self.N = int(lengths.max())
        pad = lambda name: pad_sequence([getattr(s, name) for s in scenes], batch_first=True)
        if self.N == 0:
            dev, dt = scenes[0].device, scenes[0].dtype
            self.corner = torch.zeros(len(scenes), 0, 3, device=dev, dtype=dt)
            self.size = self.corner.clone(); self.cs = torch.zeros(len(scenes), 0, 2, device=dev, dtype=dt)
            self.valid = torch.zeros(len(scenes), 0, device=dev, dtype=torch.bool)
            self.lo = self.corner.clone(); self.hi = self.corner.clone()
            return
        self.corner, self.size, self.cs = pad('_corner'), pad('_size'), pad('_cs')
        self.valid = torch.arange(self.N, device=lengths.device)[None] < lengths[:, None]
        self.lo = pad('_lo').masked_fill(~self.valid[..., None], float('inf'))
        self.hi = pad('_hi').masked_fill(~self.valid[..., None], -float('inf'))


def _local(point, corner, c, s):
    rel = point - corner
    return torch.stack([c * rel[..., 0] + s * rel[..., 1], -s * rel[..., 0] + c * rel[..., 1], rel[..., 2]], -1)


def _chunks(total, per):
    for start in range(0, total, per):
        yield start, min(total, start + per)


def _raycast(bank, row, o, d, max_range, want_index=False):
    """Closed slab test in each box frame. Returns distance [E,R] (inf = miss), optional box index."""
    E, R, _ = o.shape
    dist = torch.full((E, R), float('inf'), device=o.device, dtype=o.dtype)
    index = torch.full((E, R), -1, device=o.device, dtype=torch.long) if want_index else None
    N = bank.N
    if N == 0 or E * R == 0:
        return (dist, index) if want_index else dist
    rc = min(R, max(1, PAIR_BUDGET // (3 * N)))
    ec = max(1, PAIR_BUDGET // (3 * N * rc))
    for e0, e1 in _chunks(E, ec):
        r = row[e0:e1]
        corner, size, valid = bank.corner[r][:, None], bank.size[r][:, None], bank.valid[r][:, None]
        c, s = bank.cs[r][:, None, :, 0], bank.cs[r][:, None, :, 1]
        for r0, r1 in _chunks(R, rc):
            oo = o[e0:e1, r0:r1, None, :]
            dd = d[e0:e1, r0:r1, None, :]
            q = _local(oo, corner, c, s)
            dx, dy = c * dd[..., 0] + s * dd[..., 1], -s * dd[..., 0] + c * dd[..., 1]
            dl = torch.stack([dx, dy, dd[..., 2].expand_as(dx)], -1)
            parallel = dl == 0
            div = torch.where(parallel, torch.ones_like(dl), dl)
            a, b = -q / div, (size - q) / div
            lower = torch.minimum(a, b).masked_fill(parallel, -float('inf')).amax(-1).clamp_min(0)
            upper = torch.maximum(a, b).masked_fill(parallel, float('inf')).amin(-1).clamp_max(max_range)
            hit = (lower <= upper) & ~(parallel & ((q < 0) | (q > size))).any(-1) & valid
            entry = lower.masked_fill(~hit, float('inf'))
            best, arg = entry.min(-1)
            dist[e0:e1, r0:r1] = best
            if want_index:
                index[e0:e1, r0:r1] = torch.where(torch.isfinite(best), arg, torch.full_like(arg, -1))
    return (dist, index) if want_index else dist


def _contains(bank, row, p):
    E, M, _ = p.shape
    out = torch.zeros(E, M, device=p.device, dtype=torch.bool)
    N = bank.N
    if N == 0 or E * M == 0:
        return out
    mc = min(M, max(1, PAIR_BUDGET // (3 * N)))
    ec = max(1, PAIR_BUDGET // (3 * N * mc))
    for e0, e1 in _chunks(E, ec):
        r = row[e0:e1]
        corner, size, valid = bank.corner[r][:, None], bank.size[r][:, None], bank.valid[r][:, None]
        c, s = bank.cs[r][:, None, :, 0], bank.cs[r][:, None, :, 1]
        for m0, m1 in _chunks(M, mc):
            q = _local(p[e0:e1, m0:m1, None, :], corner, c, s)
            out[e0:e1, m0:m1] = (((q >= 0) & (q <= size)).all(-1) & valid).any(-1)
    return out


def _chassis(bank, row, base):
    """Bounded chunks over environments (E x N x 4 x 4 x 2 intermediates)."""
    E, N = len(base), bank.N
    if N == 0 or E == 0:
        return torch.zeros(E, device=base.device, dtype=torch.bool)
    per = max(1, (1 << 23) // (N * 32))
    return torch.cat([_chassis_block(bank, row[a:b], base[a:b]) for a, b in _chunks(E, per)])


def _chassis_block(bank, row, base):
    """0.99 x 0.67 footprint (full-height XY projection) vs OBB footprints, closed SAT."""
    E, N = len(base), bank.N
    c, s = base[:, 2].cos(), base[:, 2].sin()
    fu, fv = torch.stack([c, s], -1), torch.stack([-s, c], -1)
    signs = base.new_tensor([[-1, -1], [-1, 1], [1, -1], [1, 1]])
    fc = base[:, None, :2] + CHASSIS_HALF[0] * signs[None, :, 0, None] * fu[:, None] + CHASSIS_HALF[1] * signs[None, :, 1, None] * fv[:, None]
    corner, size, cs, valid = bank.corner[row][..., :2], bank.size[row][..., :2], bank.cs[row], bank.valid[row]
    bu, bv = cs, torch.stack([-cs[..., 1], cs[..., 0]], -1)
    ka = base.new_tensor([0., 1., 0., 1.]); kb = base.new_tensor([0., 0., 1., 1.])
    bc = (corner[:, :, None, :] + ka[None, None, :, None] * size[:, :, None, 0:1] * bu[:, :, None, :]
          + kb[None, None, :, None] * size[:, :, None, 1:2] * bv[:, :, None, :])
    axes = torch.stack([fu[:, None].expand(E, N, 2), fv[:, None].expand(E, N, 2), bu, bv], 2)  # [E,N,4,2]
    pf = (fc[:, None, None, :, :] * axes[:, :, :, None, :]).sum(-1)   # [E,N,4,4]
    pb = (bc[:, :, None, :, :] * axes[:, :, :, None, :]).sum(-1)
    overlap = ((pf.amin(-1) <= pb.amax(-1)) & (pb.amin(-1) <= pf.amax(-1))).all(-1)
    return (overlap & valid).any(-1)


def _arm(bank, row, caps):
    E, C = caps.shape[:2]
    arm = torch.zeros(E, device=caps.device, dtype=torch.bool)
    if C == 0:
        return arm
    if bank.N:
        a, b, r = caps[..., :3], caps[..., 3:6], caps[..., 6]
        lo, hi = bank.lo[row], bank.hi[row]
        possible = ((torch.minimum(a, b)[:, :, None] - r[:, :, None, None] <= hi[:, None])
                    & (torch.maximum(a, b)[:, :, None] + r[:, :, None, None] >= lo[:, None])).all(-1)
        env, cap, box = torch.where(possible)
        for p0, p1 in _chunks(len(env), CAPSULE_PAIR_CHUNK):
            e, k, j = env[p0:p1], cap[p0:p1], box[p0:p1]
            rr = row[e]
            corner, size, c, s = bank.corner[rr, j], bank.size[rr, j], bank.cs[rr, j, 0], bank.cs[rr, j, 1]
            d2 = _segment_bounds_distance_squared(_local(a[e, k], corner, c, s), _local(b[e, k], corner, c, s),
                                                  torch.zeros_like(size), size)
            hit = d2 <= r[e, k].square()
            arm[e[hit]] = True
    return arm | (caps[..., [2, 5]].amin(-1) - caps[..., 6] <= 0).any(-1)


def _capsule_distance(bank, a, b):
    """Minimum segment-to-box distance [K] over all boxes (single-scene bank, no radius)."""
    K = len(a)
    out = torch.full((K,), float('inf'), device=a.device, dtype=a.dtype)
    N = bank.N
    if N == 0 or K == 0:
        return out
    kc = max(1, CAPSULE_PAIR_CHUNK // N)
    corner, size, valid = bank.corner[0][None], bank.size[0][None], bank.valid[0][None]
    c, s = bank.cs[0, :, 0][None], bank.cs[0, :, 1][None]
    for k0, k1 in _chunks(K, kc):
        al = _local(a[k0:k1, None, :], corner, c, s)
        bl = _local(b[k0:k1, None, :], corner, c, s)
        d2 = _segment_bounds_distance_squared(al, bl, torch.zeros_like(size).expand_as(al), size.expand_as(al))
        out[k0:k1] = d2.masked_fill(~valid, float('inf')).amin(-1).sqrt()
    return out


# --------------------------------------------------------------------------- query mixin
class _Queries:
    """Validation + dispatch shared by PrimitiveScene and PrimitiveSceneBatch."""

    def _check(self, tensor, tail):
        if not isinstance(tensor, torch.Tensor) or tensor.shape[-1:] != (tail,):
            raise ValueError(f'expected tensor [...,{tail}]')
        if tensor.device != self.device or tensor.dtype != self.dtype:
            raise ValueError('scene query device/dtype mismatch; no implicit conversion')
        if not torch.isfinite(tensor).all():
            raise ValueError('scene query must be finite')

    def _ray_inputs(self, origins, directions, max_range):
        self._check(origins, 3); self._check(directions, 3)
        if origins.ndim != 3 or origins.shape != directions.shape:
            raise ValueError('ray shape must be [E,R,3]')
        if not math.isfinite(float(max_range)) or max_range < 0:
            raise ValueError('max_range must be finite and nonnegative')
        norms = torch.linalg.vector_norm(directions, dim=-1)
        if ((norms - 1).abs() > 32 * torch.finfo(self.dtype).eps).any():
            raise ValueError('ray directions must be unit vectors')

    def _raycast_impl(self, origins, directions, max_range, want_index=False):
        self._ray_inputs(origins, directions, max_range)
        bank, row = self._context(len(origins))
        return _raycast(bank, row, origins, directions, max_range, want_index)

    def _contains_impl(self, points):
        self._check(points, 3)
        if self._batched and points.ndim < 2:
            raise ValueError('batched points must be [E,...,3]')
        shape = points.shape[:-1]
        bank, row = self._context(shape[0] if self._batched else 1)
        flat = points.reshape(shape[0], -1, 3) if self._batched else points.reshape(1, -1, 3)
        return _contains(bank, row, flat).reshape(shape)

    def _collide_geometry(self, base, caps):
        self._check(base, 3); self._check(caps, 7)
        if base.ndim != 2 or caps.ndim != 3 or len(base) != len(caps):
            raise ValueError('base [E,3] / capsules [E,C,7] required')
        if (caps[..., 6] < 0).any():
            raise ValueError('negative capsule radius')
        bank, row = self._context(len(base))
        return _chassis(bank, row, base), _arm(bank, row, caps)


# --------------------------------------------------------------------------- single scene
def _world_bounds(boxes):
    n = len(boxes)
    if n == 0:
        return np.zeros((0, 3)), np.zeros((0, 3))
    x, y, z, sx, sy, sz, c, s = boxes.T
    cx = x[:, None] + np.stack([np.zeros(n), sx * c, -sy * s, sx * c - sy * s], 1)
    cy = y[:, None] + np.stack([np.zeros(n), sx * s, sy * c, sx * s + sy * c], 1)
    return (np.stack([cx.min(1), cy.min(1), z], 1) - BROAD_PAD, np.stack([cx.max(1), cy.max(1), z + sz], 1) + BROAD_PAD)


def _device_dtype(device, dtype):
    if dtype not in (torch.float64, torch.float32):
        raise ValueError('scene requires float64 or float32')
    device = torch.device(device)
    if device.type not in ('cpu', 'cuda'):
        raise ValueError('scene device must be CPU or CUDA')
    if device.type == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('requested CUDA is unavailable; no CPU fallback')
    return device


class PrimitiveScene(_Queries):
    """Immutable analytic OBB snapshot from one PrimitiveAsset (backend primitive-obb-v1)."""
    _batched = False

    @classmethod
    def from_asset(cls, asset, *, device, dtype):
        device = _device_dtype(device, dtype)
        if not isinstance(asset, PrimitiveAsset):
            raise ValueError('PrimitiveAsset required (JSON boxes; PCD is not an input)')
        start = time.perf_counter()
        boxes = np.asarray(asset.boxes, dtype=np.float64)
        occ, per_box = derive_occupancy(boxes, per_box=True)
        height = planning_height_from(occ)
        lo, hi = _world_bounds(boxes)
        preprocess = time.perf_counter() - start
        obj = cls(); obj.dtype = dtype
        upload = time.perf_counter()
        to = lambda a, dt=dtype: torch.tensor(np.asarray(a), device=device, dtype=dt)
        obj._corner, obj._size = to(boxes[:, :3]).reshape(-1, 3), to(boxes[:, 3:6]).reshape(-1, 3)
        obj._cs = to(boxes[:, 6:8]).reshape(-1, 2)
        obj._lo, obj._hi = to(lo).reshape(-1, 3), to(hi).reshape(-1, 3)
        obj._occupancy = torch.tensor(occ, device=device)
        obj._height = to(height)
        if device.type == 'cuda':
            torch.cuda.synchronize(device)
        obj.device = obj._corner.device
        obj._bank1 = None
        tensors = (obj._corner, obj._size, obj._cs, obj._lo, obj._hi, obj._occupancy, obj._height)
        hashes = deepcopy(asset.hashes)
        obj._provenance = dict(
            map_id=asset.map_id, hashes=hashes, backend=BACKEND, map_backend=BACKEND, environment_version=ENVIRONMENT_VERSION,
            resolution_m=H, origin=list(ORIGIN), shape_zyx=list(SHAPE_ZYX), assignment_rule='closed-obb-sat',
            contact_slack_m=CONTACT_SLACK, box_source=deepcopy(asset.source), primitive_count=len(boxes),
            domain=deepcopy(asset.domain), objects_check=deepcopy(asset.objects_check),
            occupied_count=int(occ.sum()), min_cells_per_box=int(min(per_box)) if per_box else None,
            device=str(obj.device), dtype=str(dtype), cpu_preprocess_s=preprocess,
            device_upload_wall_s=time.perf_counter() - upload,
            tensor_bytes=sum(t.numel() * t.element_size() for t in tensors),
            cache_key=[hashes.get('boxes'), BACKEND, ENVIRONMENT_VERSION, H, list(ORIGIN), CONTACT_SLACK, str(obj.device), str(dtype)])
        return obj

    def __getstate__(self):
        state = self.__dict__.copy(); state['_bank1'] = None
        return state

    @property
    def occupancy(self):
        return self._occupancy.clone()

    def provenance(self):
        return deepcopy(self._provenance)

    def planning_height(self):
        return self._height.clone()

    def primitive_boxes(self):
        """Host copy of [N,8] rows (diagnostics only; not a query path)."""
        return torch.cat([self._corner, self._size, self._cs], 1).double().cpu().numpy()

    def _context(self, rows):
        if self._bank1 is None:
            self._bank1 = _Bank([self])
        return self._bank1, torch.zeros(rows, device=self.device, dtype=torch.long)

    def raycast(self, origins, directions, *, max_range):
        return self._raycast_impl(origins, directions, max_range)

    def raycast_with_index(self, origins, directions, *, max_range):
        """Diagnostic: (distance, index of the hit primitive or -1)."""
        return self._raycast_impl(origins, directions, max_range, want_index=True)

    def contains(self, points):
        return self._contains_impl(points)

    def capsule_distance(self, a, b):
        """Diagnostic: min segment-to-OBB distance [K] (no radius, no ground)."""
        self._check(a, 3); self._check(b, 3)
        if a.shape != b.shape or a.ndim != 2:
            raise ValueError('segment endpoints [K,3] required')
        bank, _ = self._context(1)
        return _capsule_distance(bank, a, b)

    def collide(self, base, caps, *, robot, q=None, allowed=None):
        cb, arm = self._collide_geometry(base, caps)
        return Collision(cb, arm, _self_collision(base, caps, robot, allowed, q))


class PrimitiveSceneBatch(_Queries):
    """One PrimitiveScene reference per environment row; same interface as SceneBatch."""
    _batched = True

    def __init__(self, scenes, *, raycast_backend='forest'):
        if raycast_backend not in ('forest', 'loop'):
            raise ValueError('raycast backend must be forest or loop')
        self.raycast_backend = raycast_backend
        self._scenes = tuple(scenes)
        self._validate(self._scenes)
        self._bank = None

    def __getstate__(self):
        state = self.__dict__.copy(); state.pop('_bank', None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.raycast_backend = state.get('raycast_backend', 'forest')
        self._bank = None

    @staticmethod
    def _validate(scenes):
        if not scenes or any(not isinstance(s, PrimitiveScene) for s in scenes):
            raise ValueError('nonempty PrimitiveScene list required')
        if any((s.device, s.dtype) != (scenes[0].device, scenes[0].dtype) for s in scenes):
            raise ValueError('batch scenes must share device/dtype')

    @property
    def scenes(self):
        return self._scenes

    @property
    def device(self):
        return self._scenes[0].device

    @property
    def dtype(self):
        return self._scenes[0].dtype

    def __len__(self):
        return len(self._scenes)

    def _indices(self, indices):
        if isinstance(indices, torch.Tensor):
            if indices.ndim != 1 or indices.dtype not in (torch.int32, torch.int64):
                raise ValueError('integer scene indices required')
            indices = indices.tolist()
        result = list(indices)
        if any(not isinstance(i, (int, np.integer)) or isinstance(i, bool) or i < 0 or i >= len(self) for i in result):
            raise ValueError('scene index outside batch')
        return result

    def select(self, indices):
        return PrimitiveSceneBatch([self._scenes[i] for i in self._indices(indices)], raycast_backend=self.raycast_backend)

    def replace(self, indices, scenes):
        ids = self._indices(indices); scenes = list(scenes)
        if len(ids) != len(scenes) or len(set(ids)) != len(ids):
            raise ValueError('replacement length/duplicate indices')
        updated = list(self._scenes)
        for i, s in zip(ids, scenes):
            updated[i] = s
        self._validate(updated)
        self._scenes = tuple(updated)
        self._bank = None

    def _rows(self, tensor):
        if tensor.ndim < 1 or tensor.shape[0] != len(self):
            raise ValueError('query rows must match PrimitiveSceneBatch')

    def _context(self, rows):
        if rows != len(self):
            raise ValueError('query rows must match PrimitiveSceneBatch')
        if self._bank is None:
            offsets, unique, rowmap = {}, [], []
            for scene in self._scenes:
                if scene not in offsets:
                    offsets[scene] = len(unique); unique.append(scene)
                rowmap.append(offsets[scene])
            self._bank = (_Bank(unique), torch.tensor(rowmap, device=self.device, dtype=torch.long))
        return self._bank

    def raycast(self, origins, directions, *, max_range):
        self._rows(origins); self._rows(directions)
        if self.raycast_backend == 'loop':
            return torch.cat([s.raycast(origins[i:i + 1], directions[i:i + 1], max_range=max_range)
                              for i, s in enumerate(self._scenes)])
        return self._raycast_impl(origins, directions, max_range)

    def contains(self, points):
        self._rows(points)
        return self._contains_impl(points)

    def planning_height(self):
        return torch.stack([s.planning_height() for s in self._scenes])

    def provenance(self):
        return [s.provenance() for s in self._scenes]

    def collide(self, base, caps, *, robot, q=None, allowed=None):
        self._rows(base); self._rows(caps)
        if q is None:
            q = getattr(caps, '_self_collision_q', None)
        cb, arm = self._collide_geometry(base, caps)
        return Collision(cb, arm, _self_collision(base, caps, robot, allowed, q))


# --------------------------------------------------------------------------- PV diagnostic arm
class PrimitiveVoxelDiagScene(VoxelScene):
    """PV: derived occupancy through the existing v3 packing/BVH query (not a delivery backend)."""

    @classmethod
    def from_asset(cls, asset, *, device, dtype):
        device = _device_dtype(device, dtype)
        if not isinstance(asset, PrimitiveAsset):
            raise ValueError('PrimitiveAsset required (JSON boxes; PCD is not an input)')
        start = time.perf_counter()
        boxes = np.asarray(asset.boxes, dtype=np.float64)
        occ, per_box = derive_occupancy(boxes, per_box=True)
        packed = _pack(occ)
        origin = np.asarray(ORIGIN)
        lo = origin + packed[:, :3] * H; hi = origin + packed[:, 3:] * H
        node_lo, node_hi, children, leaves = _bvh(lo, hi)
        height = planning_height_from(occ)
        preprocess = time.perf_counter() - start
        obj = cls(); obj.dtype = dtype
        upload = time.perf_counter()
        obj._occupancy = torch.tensor(occ, device=device)
        obj._lo = torch.tensor(lo, device=device, dtype=dtype); obj._hi = torch.tensor(hi, device=device, dtype=dtype)
        obj._node_lo = torch.tensor(node_lo, device=device, dtype=dtype); obj._node_hi = torch.tensor(node_hi, device=device, dtype=dtype)
        obj._children = torch.tensor(children, device=device); obj._leaves = torch.tensor(leaves, device=device)
        obj._height = torch.tensor(height, device=device, dtype=dtype)
        if device.type == 'cuda':
            torch.cuda.synchronize(device)
        obj.device = obj._lo.device
        tensors = (obj._occupancy, obj._lo, obj._hi, obj._node_lo, obj._node_hi, obj._children, obj._leaves, obj._height)
        hashes = deepcopy(asset.hashes)
        obj._provenance = dict(
            map_id=asset.map_id, hashes=hashes, backend=DIAG_BACKEND, map_backend=DIAG_BACKEND, environment_version=ENVIRONMENT_VERSION,
            resolution_m=H, origin=list(ORIGIN), shape_zyx=list(SHAPE_ZYX), assignment_rule='closed-obb-sat-derived-occupancy',
            contact_slack_m=CONTACT_SLACK, primitive_count=len(boxes), domain=deepcopy(asset.domain),
            occupied_count=int(occ.sum()), packed_box_count=len(lo), bvh_node_count=len(node_lo),
            min_cells_per_box=int(min(per_box)) if per_box else None, device=str(obj.device), dtype=str(dtype),
            cpu_preprocess_s=preprocess, device_upload_wall_s=time.perf_counter() - upload,
            tensor_bytes=sum(t.numel() * t.element_size() for t in tensors),
            cache_key=[hashes.get('boxes'), DIAG_BACKEND, ENVIRONMENT_VERSION, H, list(ORIGIN), CONTACT_SLACK, str(obj.device), str(dtype)])
        return obj


# --------------------------------------------------------------------------- factory helpers
def load_backend_scene(backend, pool, map_id, *, device, dtype):
    """Scene for one pool entry under a primitive backend (v3 is built by the caller as before)."""
    backend = resolve_backend(backend)
    if backend == V3_BACKEND:
        raise ValueError('v3 scenes are built from PCD assets by the existing path')
    asset = load_primitive_asset(pool, map_id)
    cls = PrimitiveScene if backend == BACKEND else PrimitiveVoxelDiagScene
    return cls.from_asset(asset, device=device, dtype=dtype)


def make_scene_batch(scenes, **kwargs):
    """PrimitiveSceneBatch when every scene is a PrimitiveScene, else the v3 SceneBatch."""
    scenes = list(scenes)
    if scenes and all(isinstance(s, PrimitiveScene) for s in scenes):
        return PrimitiveSceneBatch(scenes, **kwargs)
    return SceneBatch(scenes, **kwargs)
