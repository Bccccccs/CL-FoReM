#!/usr/bin/env python3
"""task8.10 A-H gate fixed entry (written by S1, executed by S3; no verdict authority).

One mode per gate; each writes raw JSON to ``<run-dir>/gate_<X>.json``:
  A import      B analytic (P vs R)   C structure     D diff (P/PV/V3, report)
  E intervene   F interface/chain     G perf (report) H fidelity (snapshot/compare)

The independent reference R is loaded from a file path (default
``results/task8/t8-prim-20261027/reference/reference.py``) and called only through the
contract of task8.10 PROCEDURE section 6; this script never reads R's source.
Parameters/tolerances/seeds come from ``config/task8/primitive_scene.json``.
No training, no optimizer, no model weights. Ledger: the script refuses to start (and
stops mid-gate, writing ``status=incomplete_budget``) when the shared wall-clock ledger
``logs/task8/t8-prim-20261027/ledger-*.jsonl`` leaves too little of its limit.
"""
import argparse
import glob
import hashlib
import importlib.util
import inspect
import json
import math
import os
import pickle
import shutil
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from task8_sim import primitive_assets as pa            # noqa: E402
from task8_sim import primitive_scene as ps            # noqa: E402
from task8_sim.assets import load_asset, sha256_file   # noqa: E402
from task8_sim.scene import H, ORIGIN, SHAPE_ZYX, SceneBatch, VoxelScene   # noqa: E402

CFG_PATH = ROOT / 'config/task8/primitive_scene.json'
ps_DOMAIN_MIN, ps_DOMAIN_MAX = np.array([-5., -5., 0.]), np.array([5., 5., 1.6])
GATES = {'A': 'import', 'B': 'analytic', 'C': 'structure', 'D': 'diff', 'E': 'intervene', 'F': 'interface', 'G': 'perf', 'H': 'fidelity'}
REF_FUNCS = ('contains', 'signed_gap', 'raycast', 'ray_box_intervals', 'chassis_hits', 'capsule_distance', 'voxelize_closed_sat')


class BudgetExceeded(RuntimeError):
    pass


class Lap:
    """Sub-item wall times (s)."""
    def __init__(self):
        self.t = time.perf_counter(); self.d = {}

    def __call__(self, name):
        n = time.perf_counter(); self.d[name] = round(n - self.t, 3); self.t = n


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def jsonable(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().tolist()
    if isinstance(x, (Path, torch.device, torch.dtype)):
        return str(x)
    if isinstance(x, float) and not math.isfinite(x):
        return str(x)
    raise TypeError(f'not serialisable: {type(x)}')


def dump(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=1, default=jsonable, allow_nan=True) + '\n'); tmp.replace(path)


def stats(x):
    x = np.asarray(x, dtype=np.float64).ravel()
    if not len(x):
        return dict(n=0)
    q = np.quantile(x, [0, .01, .05, .25, .5, .75, .95, .99, 1])
    return dict(n=int(len(x)), min=q[0], p01=q[1], p05=q[2], p25=q[3], median=q[4], p75=q[5], p95=q[6], p99=q[7], max=q[8], mean=float(x.mean()))


class Ctx:
    def __init__(self, a):
        self.a = a
        self.cfg = json.loads(CFG_PATH.read_text())
        self.smoke = bool(a.smoke)
        self.P = self.cfg['smoke' if self.smoke else 'full']
        self.tol = self.cfg['tolerances']
        self.device = torch.device(a.device)
        self.dtype = {'float64': torch.float64, 'float32': torch.float32}[a.dtype]
        self.run_dir = Path(a.run_dir)
        self.start = time.monotonic()
        self.ledger_dir = ROOT / self.cfg['paths']['ledger_dir']
        self.limit = self.cfg['ledger']['limit_s']
        self.used_at_start = self.ledger_used()
        self.deadline = self.start + min(a.mode_budget_s, max(0., self.limit - self.used_at_start))
        self._ref = None
        self.maps_only = set(a.maps_only.split(',')) if a.maps_only else set()
        self.prev = None; self.res = None; self.key = None; self.all_ids = []; self.head = {}; self.gate = '?'

    def selected(self, it):
        if not self.maps_only:
            return True
        ids = {it.get('id')}
        if isinstance(it.get('m'), dict):
            ids.add(it['m'].get('id'))
        return bool(ids & self.maps_only)

    def flush(self, res, status='running'):
        """Atomically persist the current (partial) result after every finished item."""
        out = dict(self.head); out.update(res); out['status'] = status
        done = [r.get('id') for r in res.get(self.key, [])]
        out['completed_maps'] = done; out['remaining_maps'] = [i for i in self.all_ids if i not in set(done)]
        out['elapsed_so_far_s'] = round(time.monotonic() - self.start, 3)
        dump(self.run_dir / f'gate_{self.gate}.json', out)

    def iter_items(self, res, key, items):
        """Per-map loop driver: --maps-only filter, --resume skip/merge, progress line, atomic flush after each item."""
        self.res, self.key = res, key
        res.setdefault(key, [])
        if self.prev:
            for k, v in self.prev.items():
                if isinstance(res.get(k), list) and isinstance(v, list):
                    res[k] = v
        items = [it for it in items if self.selected(it)]
        self.all_ids = [it['id'] for it in items]
        done = {r.get('id') for r in res[key]}
        n = len(items)
        for i, it in enumerate(items, 1):
            if it['id'] in done:
                continue
            self.tick()
            t = time.monotonic(); before = len(res[key])
            yield it
            took = time.monotonic() - t
            if len(res[key]) > before:
                rec = res[key][-1]; rec.setdefault('id', it['id']); rec['elapsed_s'] = round(took, 3)
            print(f'[gate {self.gate}] map {i}/{n} {it["id"]} {took:.1f}s', flush=True)
            self.flush(res)

    def partial(self, status, reason, tb=None):
        res = self.res if self.res is not None else {}
        done = [r.get('id') for r in res.get(self.key, [])] if self.key else []
        res.update(status=status, stopped_reason=reason, completed_maps=done, remaining_maps=[i for i in self.all_ids if i not in set(done)])
        if tb:
            res['traceback'] = tb
        return res

    def path(self, key):
        return (ROOT / self.cfg['paths'][key]).resolve()

    def ledger_used(self):
        total = 0.
        for f in sorted(self.ledger_dir.glob('ledger-*.jsonl')):
            for line in f.read_text().splitlines():
                if line.strip():
                    total += float(json.loads(line).get('wall_s', 0))
        return total

    def tick(self):
        if time.monotonic() > self.deadline:
            raise BudgetExceeded('mode wall budget / ledger remainder exhausted')

    def reference(self):
        if self._ref is None:
            path = Path(self.a.reference) if self.a.reference else self.path('reference')
            if not path.is_file():
                return None
            spec = importlib.util.spec_from_file_location('task8_prim_reference', path)
            mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            missing = [f for f in REF_FUNCS if not callable(getattr(mod, f, None))]
            if missing:
                raise RuntimeError(f'reference lacks contract functions: {missing}')
            self._ref = mod
            self.reference_sha256 = sha256_file(path)
        return self._ref

    def scene(self, asset, dtype=None, device=None):
        return ps.PrimitiveScene.from_asset(asset, device=device or self.device, dtype=dtype or self.dtype)


# ----------------------------------------------------------------------------- map sets and geometry helpers
def pool_entries(manifest):
    return json.loads(Path(manifest).read_text())['maps']


def spaced(items, n):
    if n >= len(items):
        return list(items)
    return [items[i] for i in np.linspace(0, len(items) - 1, n, dtype=int)]


def map_sets(ctx, kinds=('semantic', 'fixture', 'cube'), cube_n=None):
    out = []
    if 'semantic' in kinds:
        m = ctx.path('semantic_manifest'); ids = [e['id'] for e in pool_entries(m)]
        out += [dict(kind='semantic', manifest=m, id=i) for i in (spaced(ids, ctx.P['A']['semantic']) if ctx.smoke else ids)]
    if 'fixture' in kinds:
        m = ctx.path('fixture_manifest'); ids = [e['id'] for e in pool_entries(m)]
        if ctx.smoke:
            ids = ['axis_aligned', 'rotated', 'random_cubes']
        out += [dict(kind='fixture', manifest=m, id=i) for i in ids]
    if 'cube' in kinds:
        m = ctx.path('cube_manifest')
        sel = json.loads(ctx.path('cube_audit_selection').read_text())['maps']
        n = cube_n if cube_n is not None else ctx.P['cube_maps']
        out += [dict(kind='cube', manifest=m, id=i) for i in spaced(sel, n)]
    for i, m in enumerate(out):
        m['idx'] = i       # stable index in the full list: seeds do not depend on --maps-only/--resume
    return out


def load_asset_for(m, strict=True):
    return pa.load_primitive_asset(m['manifest'], m['id'], strict_objects=strict)


def scan_dirs(yaw):
    az = (np.arange(360) + .5) * math.pi / 180 + yaw
    el = (np.arange(90) + .5) * math.pi / 180 - math.pi / 4
    A, E = np.meshgrid(az, el)       # [90,360]
    return np.stack([np.cos(E) * np.cos(A), np.cos(E) * np.sin(A), np.sin(E)], -1).reshape(-1, 3)


def legal_poses(R, boxes, rng, n):
    """Uniform base poses whose sensor origin (z=.5) is outside every primitive (reference containment)."""
    poses = []
    for _ in range(50 * max(n, 1)):
        x, y, yaw = rng.uniform(-4.5, 4.5), rng.uniform(-4.5, 4.5), rng.uniform(0, 2 * math.pi)
        if len(boxes) == 0 or not R.contains(boxes, np.array([[x, y, .5]]))[0]:
            poses.append((x, y, yaw))
        if len(poses) == n:
            break
    return poses


def rchunks(fn, arrays, n=20000):
    outs = []
    for s in range(0, len(arrays[0]), n):
        outs.append(fn(*[a[s:s + n] for a in arrays]))
    return np.concatenate(outs) if outs and not isinstance(outs[0], tuple) else outs


def box_world_frame(b):
    x0, y0, z0, sx, sy, sz, c, s = b
    u = np.array([c, s, 0.]); v = np.array([-s, c, 0.]); w = np.array([0., 0., 1.]); corner = np.array([x0, y0, z0])
    return corner, u, v, w, np.array([sx, sy, sz])


def boundary_points(boxes, eps):
    """Per box: 8 corners, 12 edge midpoints, 6 face centres; plus +-eps along all six local axes."""
    pts = []
    for b in boxes:
        corner, u, v, w, size = box_world_frame(b)
        axes = np.stack([u, v, w])
        base = []
        for fx in (0, .5, 1):
            for fy in (0, .5, 1):
                for fz in (0, .5, 1):
                    if (fx, fy, fz) != (.5, .5, .5):
                        base.append(corner + (np.array([fx, fy, fz]) * size) @ axes)
        base = np.array(base)
        pts.append(base)
        for sgn in (-1, 1):
            for k in range(3):
                pts.append(base + sgn * eps * axes[k])
    return np.concatenate(pts) if pts else np.zeros((0, 3))


def grazing_rays(boxes, rng, count, eps):
    """Rays in the plane of a face (shift 0, +-eps) and rays aimed at edges/corners."""
    o, d = [], []
    for bi in rng.choice(len(boxes), size=min(count, len(boxes)), replace=False) if len(boxes) else []:
        corner, u, v, w, size = box_world_frame(boxes[bi])
        axes = np.stack([u, v, w])
        for a in range(3):
            t1, t2 = [k for k in range(3) if k != a]
            for side in (0., 1.):
                for shift in (0., eps, -eps):
                    centre = corner + (np.array([.5, .5, .5]) * size) @ axes
                    centre = centre + (side - .5) * size[a] * axes[a]
                    origin = centre - 2.5 * axes[t1] + (shift) * axes[a] * (1 if side else -1)
                    o.append(origin); d.append(axes[t1])
        for fx in (0., 1.):
            for fy in (0., 1.):
                target = corner + (np.array([fx, fy, .5]) * size) @ axes
                direction = target - np.array([target[0] - 2.0, target[1] - 1.3, target[2]])
                o.append(target - direction); d.append(direction / np.linalg.norm(direction))
    if not o:
        return np.zeros((0, 3)), np.zeros((0, 3))
    return np.array(o), np.array(d)


def ray_band(R, boxes, o, d, maxr, eps):
    """True where R's first hit changes discontinuously (hit/miss flip, or jump > 1e-6 m) under +-2.5 eps
    perpendicular origin shifts, i.e. the ray lies within ~2.5e-9 m of a primitive silhouette/tie (boundary band).

    2.5 eps (not eps) so a reference closure slack of exactly eps still sees the flip; the smooth change of the
    distance under such a shift is << 1e-6 m, so generic (non-boundary) disagreements are never forgiven.
    """
    shift = 2.5 * eps
    out = np.zeros(len(o), bool)
    n = np.cross(d, np.array([1., 0., 0.]) + 0 * d); bad = np.linalg.norm(n, axis=1) < 1e-6
    n[bad] = np.cross(d[bad], np.array([0., 1., 0.])); n /= np.linalg.norm(n, axis=1, keepdims=True)
    m = np.cross(d, n)
    base = np.asarray(R.raycast(boxes, o, d, maxr))
    for vec in (n, -n, m, -m):
        pert = np.asarray(R.raycast(boxes, o + shift * vec, d, maxr))
        flip = np.isfinite(pert) != np.isfinite(base)
        jump = np.isfinite(pert) & np.isfinite(base) & (np.abs(pert - base) > 1e-6)
        out |= flip | jump
    out |= np.isfinite(base) & (np.abs(base - maxr) <= shift)
    return out


def pose_band(R, boxes, base_poses, eps):
    eps = 2.5 * eps
    out = np.zeros(len(base_poses), bool); ref = R.chassis_hits(boxes, base_poses)
    for dx, dy in ((eps, 0), (-eps, 0), (0, eps), (0, -eps)):
        out |= R.chassis_hits(boxes, base_poses + np.array([dx, dy, 0.])) != ref
    return out


def tT(x, ctx, dtype=None):
    return torch.as_tensor(np.asarray(x), device=ctx.device, dtype=dtype or ctx.dtype)


def p_raycast_flat(ctx, scene, o, d, maxr, chunk=65536):
    out = []
    for s in range(0, len(o), chunk):
        out.append(scene.raycast(tT(o[s:s + chunk][None], ctx, scene.dtype), tT(d[s:s + chunk][None], ctx, scene.dtype), max_range=maxr)[0].double().cpu().numpy())
    return np.concatenate(out) if out else np.zeros(0)


def occupancy_compare(boxes, p_occ, ref_occ, eps):
    """Strict cell equality plus classification of mismatches against the +-eps contact band."""
    tie = ps.derive_occupancy(boxes, slack=eps) & ~ps.derive_occupancy(boxes, slack=-eps)
    mism = p_occ != ref_occ
    return dict(p_cells=int(p_occ.sum()), r_cells=int(ref_occ.sum()), mismatch=int(mism.sum()), mismatch_in_tie_band=int((mism & tie).sum()),
                mismatch_outside_tie_band=int((mism & ~tie).sum()), tie_band_cells=int(tie.sum()))


def compare_p_r(ctx, scene, boxes, R, rng, params, label):
    """Shared B/E comparison: contains, raycast (+grazing), chassis, capsule distance/flags, occupancy."""
    eps = ctx.tol['boundary_band_m']; tol = ctx.tol['float64_distance_m']; res = dict(label=label, primitive_count=len(boxes)); lap = Lap()
    if len(boxes) == 0:
        probe = np.c_[rng.uniform(-4, 4, (500, 2)), np.full(500, .5)]
        d = rng.normal(size=(500, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
        res.update(empty_map=True, contains_any=bool(scene.contains(tT(probe, ctx)).any()), rays_hit=int(np.isfinite(p_raycast_flat(ctx, scene, probe, d, 6.)).sum()),
                   occupied=int(scene.occupancy.sum()), pass_=None)
        res['pass'] = not res['contains_any'] and res['rays_hit'] == 0 and res['occupied'] == 0
        return res
    # ---- contains
    n = params['contains_random']
    pts = np.c_[rng.uniform(-5.3, 5.3, (n, 2)), rng.uniform(-.1, 1.7, n)]
    pts = np.concatenate([pts, boundary_points(boxes, eps)])
    ctx.tick()
    pc = scene.contains(tT(pts, ctx))[:].cpu().numpy() if len(pts) else np.zeros(0, bool)
    rc = rchunks(lambda p: R.contains(boxes, p), [pts])
    dis = np.flatnonzero(pc != rc)
    gap = np.asarray(rchunks(lambda p: R.signed_gap(boxes, p), [pts[dis]])) if len(dis) else np.zeros(0)
    band = np.abs(gap) <= eps
    res['contains'] = dict(points=len(pts), disagreements=len(dis), in_band=int(band.sum()), out_of_band=int((~band).sum()),
                           band_samples=[dict(point=pts[i].tolist(), gap=float(g)) for i, g in zip(dis[band][:20], gap[band][:20])],
                           violations=[dict(point=pts[i].tolist(), gap=float(g)) for i, g in zip(dis[~band][:20], gap[~band][:20])])
    lap('contains')
    # ---- raycast
    maxr = self_max = ctx.cfg['sensor']['max_range_m']
    poses = legal_poses(R, boxes, rng, params['ray_poses'])
    O, D = [], []
    for x, y, yaw in poses:
        d = scan_dirs(yaw); D.append(d); O.append(np.tile([x, y, ctx.cfg['sensor']['origin_z_m']], (len(d), 1)))
    go, gd = grazing_rays(boxes, rng, params['grazing_boxes_per_map'], eps)
    O.append(go); D.append(gd)
    O, D = np.concatenate(O), np.concatenate(D) if D else np.zeros((0, 3))
    D = D / np.linalg.norm(D, axis=1, keepdims=True) if len(D) else D
    ctx.tick()
    pr = p_raycast_flat(ctx, scene, O, D, maxr) if len(O) else np.zeros(0)
    rr = rchunks(lambda o, d: R.raycast(boxes, o, d, maxr), [O, D])
    both = np.isfinite(pr) & np.isfinite(rr)
    diff = np.abs(pr - rr)
    bad = np.flatnonzero((np.isfinite(pr) != np.isfinite(rr)) | (both & (diff > tol)))
    inband = ray_band(R, boxes, O[bad], D[bad], maxr, eps) if len(bad) else np.zeros(0, bool)
    res['raycast'] = dict(rays=len(O), poses=len(poses), grazing_rays=len(go), both_hit=int(both.sum()), max_abs_diff=float(diff[both].max()) if both.any() else 0.,
                          disagreements=len(bad), in_band=int(inband.sum()), out_of_band=int((~inband).sum()),
                          violations=[dict(ray=int(i), origin=O[i].tolist(), direction=D[i].tolist(), p=float(pr[i]), r=float(rr[i])) for i in bad[~inband][:20]])
    lap('raycast')
    # float32 report (device dtype float32)
    sub = O[:min(len(O), params['float32_ray_poses'] * 32400)]
    if len(sub):
        s32 = ps.PrimitiveScene.from_asset(pa.asset_from_boxes('f32', boxes, allow_empty=True), device=ctx.device, dtype=torch.float32)
        p32 = p_raycast_flat(ctx, s32, sub, D[:len(sub)], maxr)
        r32 = rr[:len(sub)]; b32 = np.isfinite(p32) & np.isfinite(r32)
        res['raycast_float32_report'] = dict(rays=len(sub), disagree_hit_miss=int((np.isfinite(p32) != np.isfinite(r32)).sum()), error=stats(np.abs(p32 - r32)[b32]))
    lap('raycast_float32')
    # ---- chassis
    k = params['chassis_poses']
    base = np.c_[rng.uniform(-4.8, 4.8, (k, 2)), rng.uniform(-math.pi, math.pi, k)]
    touch = []
    for bi in rng.choice(len(boxes), size=min(len(boxes), max(1, k // 20)), replace=False) if len(boxes) else []:
        corner, u, v, w, size = box_world_frame(boxes[bi]); centre = corner[:2] + (size[0] / 2) * u[:2] + (size[1] / 2) * v[:2]
        yaw = math.atan2(boxes[bi][7], boxes[bi][6])
        for shift in (0., eps, -eps):
            for sgn in (-1, 1):
                touch.append([*(centre + sgn * (size[0] / 2 + .495 + shift) * u[:2]), yaw])
                touch.append([*(centre + sgn * (size[1] / 2 + .335 + shift) * v[:2]), yaw])
    base = np.concatenate([base, np.array(touch).reshape(-1, 3)])
    ctx.tick()
    caps0 = torch.empty(len(base), 0, 7, device=ctx.device, dtype=ctx.dtype)
    pcol = scene.collide(tT(base, ctx), caps0, robot=None).base.cpu().numpy()
    rcol = rchunks(lambda b: R.chassis_hits(boxes, b), [base])
    dis = np.flatnonzero(pcol != rcol)
    inb = pose_band(R, boxes, base[dis], eps) if len(dis) else np.zeros(0, bool)
    res['chassis'] = dict(poses=len(base), touching_poses=len(touch), hits=int(rcol.sum()), disagreements=len(dis), in_band=int(inb.sum()), out_of_band=int((~inb).sum()),
                          violations=[dict(pose=base[i].tolist(), p=bool(pcol[i]), r=bool(rcol[i])) for i in dis[~inb][:20]])
    lap('chassis')
    # ---- capsules
    k = params['capsules']
    a = np.c_[rng.uniform(-5, 5, (k, 2)), rng.uniform(.25, 1.55, k)]
    b = a + rng.normal(size=(k, 3)) * .6; b[:, 2] = np.clip(b[:, 2], .25, 1.55)
    r = rng.uniform(.02, .2, k)
    ta, tb, tr = [], [], []
    for bi in rng.choice(len(boxes), size=min(len(boxes), max(1, k // 20)), replace=False) if len(boxes) else []:
        corner, u, v, w, size = box_world_frame(boxes[bi]); axes = np.stack([u, v, w])
        centre = corner + (size / 2) @ axes
        for ax in (0, 1):
            for sgn in (-1, 1):
                rad = .1
                for shift in (0., eps, -eps):
                    p = centre + sgn * (size[ax] / 2 + rad + shift) * axes[ax]
                    if rad + .02 < p[2] < 1.5:
                        ta.append(p); tb.append(p); tr.append(rad)
    if ta:
        a, b, r = np.concatenate([a, np.array(ta)]), np.concatenate([b, np.array(tb)]), np.concatenate([r, np.array(tr)])
    ctx.tick()
    pd = np.concatenate([scene.capsule_distance(tT(a[s:s + 4096], ctx), tT(b[s:s + 4096], ctx)).double().cpu().numpy() for s in range(0, len(a), 4096)]) if len(boxes) else np.full(len(a), np.inf)
    rd = rchunks(lambda aa, bb, rr_: R.capsule_distance(boxes, aa, bb, rr_), [a, b, r]) + r     # R: distance - r
    fin = np.isfinite(pd) & np.isfinite(rd)
    caps = torch.tensor(np.c_[a, b, r], device=ctx.device, dtype=ctx.dtype)[:, None, :]
    far = tT(np.c_[np.full((len(a), 2), 50.), np.zeros(len(a))], ctx)
    pf = scene.collide(far, caps, robot=None).arm.cpu().numpy() if len(boxes) else np.zeros(len(a), bool)
    rf = (rd - r) <= 0
    dis = np.flatnonzero(pf != rf)
    inb = np.abs(rd - r)[dis] <= eps
    res['capsule'] = dict(capsules=len(a), touching=len(ta), max_abs_distance_diff=float(np.abs(pd - rd)[fin].max()) if fin.any() else 0., distance_violations=int((np.abs(pd - rd)[fin] > tol).sum()),
                          flag_disagreements=len(dis), in_band=int(inb.sum()), out_of_band=int((~inb).sum()),
                          violations=[dict(a=a[i].tolist(), b=b[i].tolist(), r=float(r[i]), p_dist=float(pd[i]), r_dist=float(rd[i])) for i in dis[~inb][:20]])
    lap('capsule')
    # ---- derived occupancy
    ref_occ = R.voxelize_closed_sat(boxes, np.asarray(ORIGIN), H, SHAPE_ZYX)
    res['occupancy'] = occupancy_compare(boxes, scene.occupancy.cpu().numpy(), ref_occ, eps)
    lap('voxelize'); res['timing_s'] = lap.d
    res['pass'] = (res['contains']['out_of_band'] == 0 and res['raycast']['out_of_band'] == 0 and res['chassis']['out_of_band'] == 0 and
                   res['capsule']['out_of_band'] == 0 and res['capsule']['distance_violations'] == 0 and res['occupancy']['mismatch_outside_tie_band'] == 0)
    return res


# ----------------------------------------------------------------------------- gate A
def file_hashes(paths):
    return {str(p): sha256_file(p) for p in paths}


def gate_A(ctx):
    A = ctx.P['A']; res = dict(semantic=[], fixtures=[], cube={}, errors=[])
    sem = ctx.path('semantic_manifest'); fix = ctx.path('fixture_manifest'); cube = ctx.path('cube_manifest')
    sem_entries = pool_entries(sem); fix_entries = pool_entries(fix); cube_entries = pool_entries(cube)
    sem_ids = spaced([e['id'] for e in sem_entries], A['semantic']) if ctx.smoke else [e['id'] for e in sem_entries]
    cube_pick = cube_entries if A.get('cube_all') else spaced(cube_entries, A['cube'])
    pcd_pick = set(e['id'] for e in spaced(cube_entries, A['cube_pcd_hash_sample'])) if A['cube_pcd_hash'] == 'sample' else (set(e['id'] for e in cube_entries) if A['cube_pcd_hash'] == 'all' else set())
    watched = [sem, fix, cube]
    for e in sem_entries:
        if e['id'] in sem_ids:
            watched += [sem.parent / e['pcd_path'], sem.parent / e['sidecar_path']]
    watched += [fix.parent / e['pcd_path'] for e in fix_entries]
    for e in cube_pick:
        watched.append(cube.parent / e['sidecar_path'])
        if e['id'] in pcd_pick:
            watched.append(cube.parent / e['pcd_path'])
    before = file_hashes(watched); ctx.tick()
    for e in sem_entries:
        if e['id'] not in sem_ids:
            continue
        ctx.tick()
        rec = dict(id=e['id'])
        try:
            asset = pa.load_primitive_asset(sem, e['id'], strict_objects=False)
            chk = asset.objects_check
            rec.update(boxes=len(asset.boxes), objects=chk['object_count'], part_boxes=chk['part_box_count'], objects_consistent=chk['consistent'],
                       objects_max_abs_diff=chk['max_abs_diff'], worst_source=chk['worst_source'], domain=asset.domain,
                       categories={c: asset.categories.count(c) for c in set(asset.categories)},
                       pcd_actual_sha256=sha256_file(sem.parent / e['pcd_path']), pcd_declared_sha256=e['sha256']['pcd'])
            mg = ROOT.parent / 'mapgen/outputs/all_maps' / (e['id'] + '.json')
            rec['mapgen_all_maps_json_identical'] = (sha256_file(mg) == asset.hashes['sidecar']) if mg.is_file() else None     # None: mapgen/ is not mounted in the container
            rec['pcd_hash_ok'] = rec['pcd_actual_sha256'] == rec['pcd_declared_sha256']
        except Exception as exc:       # noqa: BLE001 - recorded, gate fails
            rec['error'] = f'{type(exc).__name__}: {exc}'; res['errors'].append(rec)
        res['semantic'].append(rec)
    for e in fix_entries:
        rec = dict(id=e['id'])
        try:
            asset = pa.load_primitive_asset(fix, e['id'])
            rec.update(boxes=len(asset.boxes), domain=asset.domain, pcd_hash_ok=sha256_file(fix.parent / e['pcd_path']) == e['sha256']['pcd'])
        except Exception as exc:       # noqa: BLE001
            rec['error'] = f'{type(exc).__name__}: {exc}'; res['errors'].append(rec)
        res['fixtures'].append(rec)
    tot = dict(maps=0, errors=0, boxes=0, out_of_domain_maps=0, out_of_domain_boxes=0, fully_outside_boxes=0, max_out_of_domain_m=0., source_json_mismatch=0, hash_mismatch=0, min_size_m=1e9)
    worst = []
    for e in cube_pick:
        ctx.tick()
        try:
            asset = pa.asset_from_entry(cube, e)
            tot['maps'] += 1; tot['boxes'] += len(asset.boxes)
            dom = asset.domain
            tot['out_of_domain_maps'] += dom['out_of_domain_box_count'] > 0
            tot['out_of_domain_boxes'] += dom['out_of_domain_box_count']; tot['fully_outside_boxes'] += dom['fully_outside_box_count']
            if dom['max_out_of_domain_m'] > tot['max_out_of_domain_m']:
                tot['max_out_of_domain_m'] = dom['max_out_of_domain_m']
            if dom['out_of_domain_box_count']:
                worst.append((dom['max_out_of_domain_m'], e['id']))
            tot['min_size_m'] = min(tot['min_size_m'], float(asset.boxes[:, 3:6].min()))
            if e.get('source_json_sha256') != asset.hashes['sidecar']:
                tot['source_json_mismatch'] += 1      # sidecar must be the byte copy of the JSON the exporter read
            if e['id'] in pcd_pick and sha256_file(cube.parent / e['pcd_path']) != e['sha256']['pcd']:
                tot['hash_mismatch'] += 1
        except Exception as exc:       # noqa: BLE001
            tot['errors'] += 1; res['errors'].append(dict(id=e['id'], error=f'{type(exc).__name__}: {exc}'))
    worst.sort(reverse=True); tot['worst_out_of_domain'] = worst[:10]; tot['pcd_hash_checked'] = len(pcd_pick)
    res['cube'] = tot
    after = file_hashes(watched)
    res['source_hashes'] = dict(files=len(before), unchanged=before == after, changed=[k for k in before if before[k] != after[k]][:20])
    res['semantic_summary'] = dict(maps=len(res['semantic']), objects_all_consistent=all(r.get('objects_consistent') for r in res['semantic']),
                                   max_abs_diff=max([r.get('objects_max_abs_diff') or 0. for r in res['semantic']] or [0.]),
                                   out_of_domain_maps=sum(1 for r in res['semantic'] if r.get('domain', {}).get('out_of_domain_box_count')),
                                   pcd_hash_failures=sum(1 for r in res['semantic'] if not r.get('pcd_hash_ok', True)),
                                   mapgen_json_identical=sum(1 for r in res['semantic'] if r.get('mapgen_all_maps_json_identical')))
    ok = (not res['errors'] and res['semantic_summary']['objects_all_consistent'] and res['source_hashes']['unchanged'] and tot['source_json_mismatch'] == 0
          and tot['hash_mismatch'] == 0 and res['semantic_summary']['pcd_hash_failures'] == 0)
    res['status'] = 'pass' if ok else 'fail'
    res['note'] = 'Out-of-domain primitives are reported only (not a failure). In smoke mode only a subset is checked.'
    return res


# ----------------------------------------------------------------------------- gate B
def gate_B(ctx):
    R = ctx.reference()
    if R is None:
        return dict(status='reference_unavailable')
    params = ctx.P['B']; res = dict(maps=[], reference_sha256=getattr(ctx, 'reference_sha256', None))
    for m in ctx.iter_items(res, 'maps', map_sets(ctx)):
        asset = load_asset_for(m); boxes = np.asarray(asset.boxes)
        rng = np.random.default_rng([ctx.cfg['seeds']['master'], ctx.cfg['seeds']['rays'], m['idx']])
        r = compare_p_r(ctx, ctx.scene(asset), boxes, R, rng, params, m['id']); r.update(kind=m['kind'])
        res['maps'].append(r)
    res['status'] = 'pass' if all(r['pass'] for r in res['maps']) else 'fail'
    res['totals'] = {k: sum(r.get(k, {}).get(f, 0) for r in res['maps']) for k, f in (('contains', 'out_of_band'), ('raycast', 'out_of_band'), ('chassis', 'out_of_band'), ('capsule', 'out_of_band'))}
    res['empty_maps'] = [r['id'] for r in res['maps'] if r.get('empty_map')]
    return res


# ----------------------------------------------------------------------------- gate C
def gate_C(ctx):
    R = ctx.reference()
    if R is None:
        return dict(status='reference_unavailable')
    C = ctx.P['C']; eps = ctx.tol['boundary_band_m']; res = dict(maps=[], reference_sha256=getattr(ctx, 'reference_sha256', None))
    for m in ctx.iter_items(res, 'maps', map_sets(ctx)):
        lap = Lap()
        asset = load_asset_for(m); boxes = np.asarray(asset.boxes); rec = dict(id=m['id'], kind=m['kind'], primitive_count=len(boxes))
        occ, counts = ps.derive_occupancy(boxes, per_box=True)
        ref = R.voxelize_closed_sat(boxes, np.asarray(ORIGIN), H, SHAPE_ZYX)
        rec['occupancy'] = occupancy_compare(boxes, occ, ref, eps)
        # SRC-1221 approved criterion: band given by R itself, R(-1e-9) subset of P subset of R(+1e-9)
        r_lo = R.voxelize_closed_sat(boxes, np.asarray(ORIGIN), H, SHAPE_ZYX, tol=-eps)
        r_hi = R.voxelize_closed_sat(boxes, np.asarray(ORIGIN), H, SHAPE_ZYX, tol=eps)
        band = r_hi & ~r_lo; diff0 = occ != ref
        rec['occupancy_band'] = dict(lo_not_in_p=int((r_lo & ~occ).sum()), p_not_in_hi=int((occ & ~r_hi).sum()), r_lo_cells=int(r_lo.sum()), r_hi_cells=int(r_hi.sum()),
                                     p_vs_r0_mismatch=int(diff0.sum()), p_vs_r0_in_band=int((diff0 & band).sum()), p_vs_r0_outside_band=int((diff0 & ~band).sum()))
        occupancy_band_ok = rec['occupancy_band']['lo_not_in_p'] == 0 and rec['occupancy_band']['p_not_in_hi'] == 0
        rec['occupancy_band_ok'] = bool(occupancy_band_ok)
        lap('voxelize')
        rec['per_box_min_cells'] = int(min(counts)) if counts else None
        zero = [i for i, c in enumerate(counts) if c == 0]
        lo_w, hi_w = ps._world_bounds(boxes)
        outside_closed = lambda i: bool((hi_w[i] + 1e-5 < ps_DOMAIN_MIN).any() or (lo_w[i] - 1e-5 > ps_DOMAIN_MAX).any())
        rec['boxes_without_cell'] = dict(count=len(zero), indices=zero[:20], expected_fully_outside_closed_domain=[i for i in zero if outside_closed(i)][:20],
                                         unexpected=[i for i in zero if not outside_closed(i)][:20])
        if C['per_box_voxelize'] and len(boxes) <= C['per_box_max_boxes']:
            bad = []; bad_band = []
            for i in range(len(boxes)):
                ctx.tick()
                one = R.voxelize_closed_sat(boxes[i:i + 1], np.asarray(ORIGIN), H, SHAPE_ZYX)
                if int(one.sum()) != counts[i]:
                    bad.append(dict(box=i, p=counts[i], r=int(one.sum())))
                # approved per-box criterion: R_i(-eps) subset of P_i subset of R_i(+eps)
                p_i = ps.derive_occupancy(boxes[i:i + 1])
                lo_i_ = R.voxelize_closed_sat(boxes[i:i + 1], np.asarray(ORIGIN), H, SHAPE_ZYX, tol=-eps)
                hi_i_ = R.voxelize_closed_sat(boxes[i:i + 1], np.asarray(ORIGIN), H, SHAPE_ZYX, tol=eps)
                if (lo_i_ & ~p_i).any() or (p_i & ~hi_i_).any():
                    bad_band.append(dict(box=i, lo_not_in_p=int((lo_i_ & ~p_i).sum()), p_not_in_hi=int((p_i & ~hi_i_).sum())))
            rec['per_box_cells_mismatch'] = bad[:20]; rec['per_box_cells_mismatch_count'] = len(bad)
            rec['per_box_band_violations'] = bad_band[:20]; rec['per_box_band_violation_count'] = len(bad_band)
        lap('per_box')
        # strictly-inside voxels (all eight corners deeper than eps inside the union) must be occupied
        missing = 0; checked = 0; crng = np.random.default_rng([ctx.cfg['seeds']['master'], 77, m['idx']])
        per_box_cap = max(50, C['deep_cells_per_map'] // max(1, len(boxes)))
        for i in range(min(len(boxes), C['deep_holes_max_boxes'])):
            x0, y0, z0, sx, sy, sz, c, s_ = boxes[i]
            cx = x0 + np.array([0., sx * c, -sy * s_, sx * c - sy * s_]); cy = y0 + np.array([0., sx * s_, sy * c, sx * s_ + sy * c])
            lo_i = np.maximum(0, np.floor((np.array([cx.min(), cy.min()]) - ORIGIN[:2]) / H).astype(int) - 1)
            hi_i = np.minimum(200, np.ceil((np.array([cx.max(), cy.max()]) - ORIGIN[:2]) / H).astype(int) + 1)
            k0, k1 = max(0, int(z0 // H) - 1), min(32, int((z0 + sz) // H) + 2)
            if (hi_i <= lo_i).any() or k1 <= k0:
                continue
            X, Y, Z = np.meshgrid(np.arange(lo_i[0], hi_i[0]), np.arange(lo_i[1], hi_i[1]), np.arange(k0, k1), indexing='ij')
            cells = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
            if len(cells) > per_box_cap:
                cells = cells[crng.choice(len(cells), per_box_cap, replace=False)]
            corners = np.stack([ORIGIN[0] + (cells[:, 0][:, None] + np.array([0, 1] * 4)[None]) * H,
                                ORIGIN[1] + (cells[:, 1][:, None] + np.array([0, 0, 1, 1] * 2)[None]) * H,
                                (cells[:, 2][:, None] + np.array([0] * 4 + [1] * 4)[None]) * H], -1)       # [C,8,3]
            gaps = np.asarray(rchunks(lambda p: R.signed_gap(boxes, p), [corners.reshape(-1, 3)], 100000)).reshape(len(cells), 8)
            deep = (gaps <= -eps).all(1)
            checked += int(deep.sum())
            missing += int((~occ[cells[deep, 2], cells[deep, 1], cells[deep, 0]]).sum())
        rec['deep_interior_cells_checked'] = checked; rec['deep_interior_cells_missing'] = missing
        lap('deep_interior')
        # deep wall rays (SRC-1081 penetration-depth gate)
        walls = [i for i, c in enumerate(asset.categories) if c == 'wall']
        rec['wall_boxes'] = len(walls)
        if walls:
            wb = boxes[walls]; maxr = ctx.tol['deep_wall_max_range_m']; chord = ctx.tol['deep_wall_chord_m']
            rng = np.random.default_rng([ctx.cfg['seeds']['master'], ctx.cfg['seeds']['rays'], 99, m['idx']])
            scene = ctx.scene(asset); elig_total = shell = miss = mism_ray = 0; worst = 0.
            for (x, y, yaw) in legal_poses(R, boxes, rng, C['wall_ray_poses']):
                ctx.tick()
                d = scan_dirs(yaw); o = np.tile([x, y, ctx.cfg['sensor']['origin_z_m']], (len(d), 1))
                t_in, t_out = R.ray_box_intervals(wb, o, d)
                inside = np.isfinite(t_in) & np.isfinite(t_out) & (t_in >= 0)
                eligible_w = inside & (t_out - t_in >= chord)
                eligible = eligible_w.any(1); entry = np.where(eligible_w, t_in, np.inf).min(1)
                shell += int((inside.any(1) & ~eligible).sum()); elig_total += int(eligible.sum())
                pr = p_raycast_flat(ctx, scene, o, d, maxr); rr = np.asarray(R.raycast(boxes, o, d, maxr))
                miss += int((eligible & ~(pr <= entry + eps)).sum())
                both = np.isfinite(pr) & np.isfinite(rr)
                mism_ray += int(((np.isfinite(pr) != np.isfinite(rr)) | (both & (np.abs(pr - rr) > ctx.tol['float64_distance_m']))).sum())
                worst = max(worst, float(np.abs(pr - rr)[both].max()) if both.any() else 0.)
            rec['deep_wall_rays'] = dict(eligible=elig_total, shell=shell, misses=miss, distance_mismatch=mism_ray, max_abs_diff=worst)
        lap('deep_wall'); rec['timing_s'] = lap.d
        walls_ok = rec.get('deep_wall_rays', {}).get('misses', 0) == 0 and rec.get('deep_wall_rays', {}).get('distance_mismatch', 0) == 0
        rec['pass_approved'] = bool(occupancy_band_ok and missing == 0 and rec.get('per_box_band_violation_count', 0) == 0 and not rec['boxes_without_cell']['unexpected'] and walls_ok)
        rec['pass_strict'] = bool(rec['occupancy']['mismatch'] == 0 and missing == 0 and rec.get('per_box_cells_mismatch_count', 0) == 0 and walls_ok and not rec['boxes_without_cell']['unexpected'])
        rec['pass'] = rec['pass_strict']
        rec['pass_modulo_tie_band'] = (rec['occupancy']['mismatch_outside_tie_band'] == 0 and missing == 0 and rec.get('deep_wall_rays', {}).get('misses', 0) == 0)
        res['maps'].append(rec)
    res['criterion'] = 'SRC-1221 R(-1e-9)\u2286P\u2286R(+1e-9)'
    res['status'] = 'pass' if res['maps'] and all(r['pass_approved'] for r in res['maps']) else 'fail'
    res['all_pass_strict'] = all(r['pass_strict'] for r in res['maps'])
    res['all_pass_modulo_tie_band'] = all(r['pass_modulo_tie_band'] for r in res['maps'])
    return res


# ----------------------------------------------------------------------------- gate D
def v3_scene(ctx, m):
    return VoxelScene.from_asset(load_asset(m['manifest'], m['id']), device=ctx.device, dtype=ctx.dtype)


def gate_D(ctx):
    from task7_sim.episode import CBL_Q
    from task7_sim.perception import Grid
    from task8_sim.perception import PcdPanorama
    from task8_sim.robot import GhostRobotGeometry
    from scipy.ndimage import binary_dilation
    D = ctx.P['D']; res = dict(maps=[]); sensor = json.loads((ROOT / 'config/task8/sensor.json').read_text())
    robot = GhostRobotGeometry(); layer = ctx.tol['diff_layer_m']; maxr = ctx.cfg['sensor']['max_range_m']
    q0 = torch.tensor(CBL_Q, device=ctx.device, dtype=ctx.dtype)[None]
    for m in ctx.iter_items(res, 'maps', map_sets(ctx)):
        asset = load_asset_for(m); boxes = np.asarray(asset.boxes)
        lap = Lap()
        p, pv, v3 = ctx.scene(asset), ps.PrimitiveVoxelDiagScene.from_asset(asset, device=ctx.device, dtype=ctx.dtype), v3_scene(ctx, m)
        rec = dict(id=m['id'], kind=m['kind'], primitive_count=len(boxes))
        rng = np.random.default_rng([ctx.cfg['seeds']['master'], ctx.cfg['seeds']['diff'], m['idx']])
        lap('build')
        # occupancy
        po, vo, pvo = p.occupancy.cpu().numpy(), v3.occupancy.cpu().numpy(), pv.occupancy.cpu().numpy()
        near_v3 = binary_dilation(vo, structure=np.ones((3, 3, 3), bool)); near_p = binary_dilation(po, structure=np.ones((3, 3, 3), bool))
        only_p, only_v = po & ~vo, vo & ~po
        rec['occupancy'] = dict(p=int(po.sum()), v3=int(vo.sum()), pv_equals_p=bool((pvo == po).all()), only_p=int(only_p.sum()), only_v3=int(only_v.sum()),
                                only_p_within_1_voxel_of_v3=int((only_p & near_v3).sum()), only_v3_within_1_voxel_of_p=int((only_v & near_p).sum()),
                                only_p_by_z=np.bincount(np.nonzero(only_p)[0], minlength=32).tolist(), only_v3_by_z=np.bincount(np.nonzero(only_v)[0], minlength=32).tolist(),
                                height_max_abs_diff=float((p.planning_height() - v3.planning_height()).abs().max()))
        lap('occupancy')
        # rays
        wall = np.array([c == 'wall' for c in asset.categories], bool)
        pairs = {'P-V3': [], 'PV-V3': [], 'P-PV': []}; classes = dict(hit_miss={}, delta_gt_layer=0, rays=0, wall=dict(n=0, gt_layer=0), nonwall=dict(n=0, gt_layer=0)); worst = []
        for (x, y, yaw) in [(rng.uniform(-4.5, 4.5), rng.uniform(-4.5, 4.5), rng.uniform(0, 2 * math.pi)) for _ in range(D['ray_poses'])]:
            ctx.tick()
            d = scan_dirs(yaw); o = np.tile([x, y, ctx.cfg['sensor']['origin_z_m']], (len(d), 1))
            ot, dt = tT(o[None], ctx), tT(d[None], ctx)
            dp, idx = p.raycast_with_index(ot, dt, max_range=maxr); dp = dp[0].double().cpu().numpy(); idx = idx[0].cpu().numpy()
            dv = v3.raycast(ot, dt, max_range=maxr)[0].double().cpu().numpy(); dpv = pv.raycast(ot, dt, max_range=maxr)[0].double().cpu().numpy()
            for name, a, b in (('P-V3', dp, dv), ('PV-V3', dpv, dv), ('P-PV', dp, dpv)):
                both = np.isfinite(a) & np.isfinite(b); pairs[name].append((a - b)[both])
                classes['hit_miss'].setdefault(name, dict(both_hit=0, only_first=0, only_second=0, both_miss=0))
                c = classes['hit_miss'][name]
                c['both_hit'] += int(both.sum()); c['only_first'] += int((np.isfinite(a) & ~np.isfinite(b)).sum()); c['only_second'] += int((~np.isfinite(a) & np.isfinite(b)).sum()); c['both_miss'] += int((~np.isfinite(a) & ~np.isfinite(b)).sum())
            both = np.isfinite(dp) & np.isfinite(dv); delta = np.abs(dp - dv); big = both & (delta > layer)
            classes['rays'] += int(both.sum()); classes['delta_gt_layer'] += int(big.sum())
            is_wall = np.where(idx >= 0, wall[np.clip(idx, 0, max(len(wall) - 1, 0))] if len(wall) else False, False)
            for tag, mask in (('wall', both & is_wall), ('nonwall', both & ~is_wall)):
                classes[tag]['n'] += int(mask.sum()); classes[tag]['gt_layer'] += int((mask & big).sum())
            for i in np.flatnonzero(big)[:3]:
                worst.append(dict(origin=o[i].tolist(), direction=d[i].tolist(), p=float(dp[i]), v3=float(dv[i]), pv=float(dpv[i]), p_box=int(idx[i]), p_box_category=asset.categories[idx[i]] if idx[i] >= 0 else None))
        rec['rays'] = dict(classification=classes, deltas={k: stats(np.concatenate(v) if v else []) for k, v in pairs.items()},
                           fraction_abs_gt_layer={k: float((np.abs(np.concatenate(v)) > layer).mean()) if v and len(np.concatenate(v)) else None for k, v in pairs.items()},
                           beyond_one_voxel_examples=worst[:20])
        lap('rays')
        # collisions with the real ghost robot
        n = D['collision_poses']; base = np.c_[rng.uniform(-4.8, 4.8, (n, 2)), rng.uniform(0, 2 * math.pi, n)]
        bt = tT(base, ctx); qt = q0.expand(n, -1).clone(); caps = robot(bt, qt)
        flags = {}
        for name, sc in (('P', p), ('PV', pv), ('V3', v3)):
            out = sc.collide(bt, caps, robot=robot, q=qt)
            flags[name] = (out.base.cpu().numpy(), out.arm.cpu().numpy())
        conf = {}
        for a_, b_ in (('P', 'V3'), ('PV', 'V3'), ('P', 'PV')):
            conf[f'{a_}-{b_}'] = {kind: dict(disagree=int((flags[a_][k] != flags[b_][k]).sum()), first_only=int((flags[a_][k] & ~flags[b_][k]).sum()), second_only=int((~flags[a_][k] & flags[b_][k]).sum()),
                                             hits_first=int(flags[a_][k].sum()), hits_second=int(flags[b_][k].sum())) for k, kind in ((0, 'base'), (1, 'arm'))}
        rec['collision'] = dict(poses=n, confusion=conf)
        lap('collision')
        # Grid after identical scan sequence
        poses = [(rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(0, 2 * math.pi)) for _ in range(D['grid_scans'])]
        grids = {}
        for name, batch in (('P', ps.PrimitiveSceneBatch([p])), ('PV', SceneBatch([pv])), ('V3', SceneBatch([v3]))):
            g = Grid.empty(1, device=ctx.device, dtype=ctx.dtype); pan = PcdPanorama(batch, sensor_config=sensor)
            for k, (x, y, yaw) in enumerate(poses):
                b1 = torch.tensor([[x, y, yaw]], device=ctx.device, dtype=ctx.dtype)
                dep = pan(b1, robot(b1, q0)); g.update(dep.points, dep.valid, torch.tensor([float(k)], device=ctx.device, dtype=ctx.dtype))
            grids[name] = g
        rec['grid'] = {f'{a_}-V3': dict(observed_diff_cells=int((grids[a_].observed != grids['V3'].observed).sum()), height_diff_cells=int(((grids[a_].height - grids['V3'].height).abs() > 1e-6).sum()),
                                        height_max_abs_diff=float((grids[a_].height - grids['V3'].height).abs().max()), observed_V3=int(grids['V3'].observed.sum())) for a_ in ('P', 'PV')}
        lap('grid'); rec['timing_s'] = lap.d
        res['maps'].append(rec)
    if D['reset_episodes'] > 0:
        res['reset'] = reset_diff(ctx, D['reset_episodes'])
    res['status'] = 'report'
    return res


def reset_diff(ctx, n):
    from task7_sim.episode import RandomStreams
    from task8_sim.episode import PcdEpisodeSampler
    out = []
    for m in map_sets(ctx, kinds=('semantic', 'fixture', 'cube'), cube_n=1)[:6]:
        ctx.tick()
        entry = [e for e in pool_entries(m['manifest']) if e['id'] == m['id']][0]
        recs = {}
        for backend in (ps.V3_BACKEND, ps.BACKEND):
            s = PcdEpisodeSampler(m['manifest'], split=entry['split'], difficulty=entry['difficulty'], device=ctx.device, dtype=ctx.dtype, kin=None, robot=None, profile='sync_v5', map_backend=backend)
            s.entries = [e for e in s.entries if e['id'] == m['id']]
            streams = RandomStreams(ctx.cfg['seeds']['reset'], 1).for_env(0); eps_ = []
            for _ in range(n):
                t = time.monotonic()
                try:
                    e = s.sample(streams, deadline=time.monotonic() + 60)
                    eps_.append(dict(seed=e.seed, base=e.base.tolist(), wall_s=time.monotonic() - t))
                except Exception as exc:   # noqa: BLE001
                    eps_.append(dict(error=f'{type(exc).__name__}: {exc}'))
            recs[backend] = dict(episodes=eps_, stats={k: v for k, v in s.stats.items()})
        out.append(dict(id=m['id'], runs=recs, accepted_seeds_equal=[e.get('seed') for e in recs[ps.V3_BACKEND]['episodes']] == [e.get('seed') for e in recs[ps.BACKEND]['episodes']]))
    return out


# ----------------------------------------------------------------------------- gate E
def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def write_map_copy(ctx, m, out, asset_json=None, fixture_boxes=None, extra_entry=None):
    """Write a manifest+sidecar(+PCD copy) for one map under ``out`` (copies only; originals untouched)."""
    out.mkdir(parents=True, exist_ok=True)
    entry = [dict(e) for e in pool_entries(m['manifest']) if e['id'] == m['id']][0]
    src = m['manifest'].parent
    for k in ('per_box_target_counts', 'per_box_numerics', 'production_provenance'):
        entry.pop(k, None)
    if entry.get('pcd_path'):
        shutil.copyfile(src / entry['pcd_path'], out / Path(entry['pcd_path']).name); entry['pcd_path'] = Path(entry['pcd_path']).name
    if asset_json is not None:
        text = json.dumps(asset_json, indent=1)
        (out / (m['id'] + '.json')).write_text(text); entry['sidecar_path'] = m['id'] + '.json'; entry['sha256'] = dict(entry['sha256'], sidecar=sha_bytes(text.encode()))
    if fixture_boxes is not None:
        entry['fixture_boxes'] = fixture_boxes
    if extra_entry:
        entry.update(extra_entry)
    (out / 'manifest.json').write_text(json.dumps(dict(schema_version='task8-pcd-v1', maps=[entry]), indent=1))
    return out / 'manifest.json'


def gate_E(ctx):
    R = ctx.reference()
    if R is None:
        return dict(status='reference_unavailable')
    from task7_sim.perception import Grid
    from task8_sim.perception import PcdPanorama
    E = ctx.P['E']; res = dict(cases=[], pcd_only=[], done_items=[], reference_sha256=getattr(ctx, 'reference_sha256', None))
    sensor = json.loads((ROOT / 'config/task8/sensor.json').read_text()); shift = E['translate_m']
    lookup = {m['id']: m for m in map_sets(ctx, cube_n=ctx.P['cube_maps']) + [dict(kind='semantic', manifest=ctx.path('semantic_manifest'), id=i) for i in ('home_map_000',)]
              + [dict(kind='cube', manifest=ctx.path('cube_manifest'), id='sparse_validation_00000')]}
    new_box = [1.2, -3.1, 0., .4, .4, 1., math.cos(.3), math.sin(.3)]
    params = dict(contains_random=E['contains_random'], boundary_offset_m=1e-9, ray_poses=E['ray_poses'], grazing_boxes_per_map=3, chassis_poses=E['chassis_poses'], capsules=E['capsules'], float32_ray_poses=0)
    for item in ctx.iter_items(res, 'done_items', [dict(id=i) for i in E['maps']]):
        mid = item['id']; m = lookup[mid]
        base_dir = ctx.run_dir / 'E' / mid
        src_asset = pa.load_primitive_asset(m['manifest'], mid)
        entry = [e for e in pool_entries(m['manifest']) if e['id'] == mid][0]
        orig_json = json.loads((m['manifest'].parent / entry['sidecar_path']).read_text()) if entry.get('sidecar_path') else None
        orig_fix = entry.get('fixture_boxes')
        variants = {}
        for kind in ('translate', 'delete', 'add'):
            if orig_json is not None and isinstance(orig_json.get('objects'), list):
                objs = json.loads(json.dumps(orig_json['objects']))
                rows0, src0, _ = pa.expand_objects(objs)
                vol = {}
                for (oi, _pi), r in zip(src0, rows0):
                    vol[oi] = vol.get(oi, 0.) + float(np.prod(r[3:6]))
                tgt = max((i for i, o in enumerate(objs) if o.get('category') != 'wall'), key=lambda i: vol[i])       # largest furniture object
                if kind == 'translate':
                    objs[tgt]['position'][0] += shift
                elif kind == 'delete':
                    del objs[tgt]
                else:
                    objs.append(dict(name='E_added', room='', position=new_box[:3], theta=.3, size=new_box[3:6]))
                rows, _, _ = pa.expand_objects(objs)
                js = dict(orig_json, objects=objs, boxes=rows.tolist(), num_boxes=len(rows))
                path = write_map_copy(ctx, m, base_dir / kind, asset_json=js)
            elif orig_json is not None:
                rows = [list(b) for b in orig_json['boxes']]
                meta = list(orig_json.get('box_metadata', []))
                tgt = max((i for i, md in enumerate(meta) if md.get('category') != 'wall'), key=lambda i: float(np.prod(rows[i][3:6]))) if meta else 0
                if kind == 'translate':
                    rows[tgt][0] += shift
                elif kind == 'delete':
                    del rows[tgt]
                    if meta:
                        del meta[tgt]
                else:
                    rows.append(new_box)
                    if meta:
                        meta.append(dict(category='E_added', name='E_added'))
                js = dict(orig_json, boxes=rows, box_metadata=meta) if meta else dict(orig_json, boxes=rows)
                path = write_map_copy(ctx, m, base_dir / kind, asset_json=js)
            else:
                fb = json.loads(json.dumps(orig_fix)); tgt = 0
                if kind == 'translate':
                    fb[tgt]['center'][0] += shift
                elif kind == 'delete':
                    del fb[tgt]
                else:
                    fb.append(dict(center=[1.0, -3.0, .5], size=[.4, .4, 1.], yaw=.3))
                path = write_map_copy(ctx, m, base_dir / kind, fixture_boxes=fb, extra_entry=dict(allow_empty=True, fixture=True))
            asset_m = pa.load_primitive_asset(path, mid)
            variants[kind] = asset_m
        s0 = ctx.scene(src_asset); b0 = np.asarray(src_asset.boxes)
        rng_seed = [ctx.cfg['seeds']['master'], ctx.cfg['seeds']['intervene'], 3 * E['maps'].index(mid)]
        for kind, asset_m in variants.items():
            ctx.tick()
            boxes = np.asarray(asset_m.boxes); s1 = ctx.scene(asset_m)
            rng = np.random.default_rng(rng_seed); case = compare_p_r(ctx, s1, boxes, R, rng, params, f'{mid}:{kind}')
            # changed-vs-original agreement with R on the identical query set
            rng = np.random.default_rng(rng_seed + [1])
            poses = legal_poses(R, np.concatenate([b0, boxes]), rng, E['ray_poses'])
            changed_p = changed_r = scans_equal = changed_mismatch = changed_mismatch_out_of_band = scan_out_of_band = 0; maxdiff = 0.
            tol_d = ctx.tol['float64_distance_m']; eps_b = ctx.tol['boundary_band_m']
            for (x, y, yaw) in poses:
                d = scan_dirs(yaw); o = np.tile([x, y, .5], (len(d), 1))
                a0, a1 = p_raycast_flat(ctx, s0, o, d, 6.), p_raycast_flat(ctx, s1, o, d, 6.)
                r0, r1 = np.asarray(R.raycast(b0, o, d, 6.)), np.asarray(R.raycast(boxes, o, d, 6.))
                fin = lambda u, v: (np.isfinite(u) != np.isfinite(v)) | (np.isfinite(u) & np.isfinite(v) & (np.abs(np.where(np.isfinite(u), u, 0) - np.where(np.isfinite(v), v, 0)) > tol_d))
                cp, cr = fin(a0, a1), fin(r0, r1)
                changed_p += int(cp.sum()); changed_r += int(cr.sum())
                mm = np.flatnonzero(cp != cr); changed_mismatch += len(mm)
                if len(mm):
                    band = ray_band(R, b0, o[mm], d[mm], 6., eps_b) | ray_band(R, boxes, o[mm], d[mm], 6., eps_b)
                    changed_mismatch_out_of_band += int((~band).sum())
                dis = np.flatnonzero(fin(a1, r1))
                if len(dis):
                    scan_out_of_band += int((~ray_band(R, boxes, o[dis], d[dis], 6., eps_b)).sum())
                both = np.isfinite(a1) & np.isfinite(r1); maxdiff = max(maxdiff, float(np.abs(a1 - r1)[both].max()) if both.any() else 0.)
                r_eff = np.where(fin(a1, r1), a1, r1)      # in-band disagreements take P's value; out-of-band ones are counted above
                # Grid from P scan vs Grid from reference scan (same landing/ground rules as PcdPanorama)
                base_t = torch.tensor([[x, y, yaw]], device=ctx.device, dtype=ctx.dtype)
                dep = PcdPanorama(ps.PrimitiveSceneBatch([s1]), sensor_config=sensor)(base_t, torch.empty(1, 0, 7, device=ctx.device, dtype=ctx.dtype))
                dz = d[:, 2]; ground = np.where(dz < 0, -.5 / np.where(dz != 0, dz, 1.), np.inf)
                world = np.minimum(r_eff, ground); valid = np.isfinite(world) & (world >= 0) & (world <= 6.)
                pts = o + d * np.where(valid, world, 0.)[:, None]
                frac = (pts[:, :2] + 5) / H
                tie = (np.abs(frac - np.rint(frac)) * H <= eps_b).any(1)        # landings on a Grid-cell boundary: floor() is rounding-noise sensitive
                valid = valid & ~tie
                g_ref, g_p = Grid.empty(1, device=ctx.device, dtype=ctx.dtype), Grid.empty(1, device=ctx.device, dtype=ctx.dtype)
                g_ref.update(tT(pts[None], ctx), tT(valid[None], ctx, torch.bool), torch.zeros(1, device=ctx.device, dtype=ctx.dtype))
                g_p.update(dep.points.reshape(1, -1, 3), dep.valid.reshape(1, -1) & tT(~tie[None], ctx, torch.bool), torch.zeros(1, device=ctx.device, dtype=ctx.dtype))
                scans_equal += int((g_ref.observed == g_p.observed).all().item() and (g_ref.height - g_p.height).abs().max().item() <= 1e-6)
            ref_occ = R.voxelize_closed_sat(boxes, np.asarray(ORIGIN), H, SHAPE_ZYX)
            hgt = lambda o_: np.where(o_, np.arange(1, 33)[:, None, None] * H, 0).max(0)
            tie_cols = hgt(ps.derive_occupancy(boxes, slack=eps_b)) != hgt(ps.derive_occupancy(boxes, slack=-eps_b))
            dh = np.abs(s1.planning_height().cpu().numpy() - hgt(ref_occ))
            case['intervention'] = dict(kind=kind, primitive_count_before=len(b0), primitive_count_after=len(boxes), scan_changed_rays_p=changed_p, scan_changed_rays_r=changed_r,
                                        changed_mask_mismatch=changed_mismatch, changed_mask_mismatch_out_of_band=changed_mismatch_out_of_band, scan_out_of_band=scan_out_of_band,
                                        p_vs_r_max_abs_diff_after=maxdiff, grid_poses=len(poses), grid_equal_poses=scans_equal,
                                        planning_height_diff_columns=int((dh > 1e-9).sum()), planning_height_diff_columns_outside_tie_band=int(((dh > 1e-9) & ~tie_cols).sum()),
                                        json_hash_changed=asset_m.hashes['boxes'] != src_asset.hashes['boxes'])
            iv = case['intervention']
            case['pass'] = bool(case['pass'] and iv['changed_mask_mismatch_out_of_band'] == 0 and iv['scan_out_of_band'] == 0 and iv['planning_height_diff_columns_outside_tie_band'] == 0 and iv['grid_equal_poses'] == len(poses) and iv['json_hash_changed'])
            res['cases'].append(case)
        # PCD-only interventions: P output must be bit-identical
        if entry.get('pcd_path'):
            ctx.tick()
            out = base_dir / 'pcd_only'; out.mkdir(parents=True, exist_ok=True)
            pcd = (m['manifest'].parent / entry['pcd_path']).read_text().splitlines()
            head = [l for l in pcd if not l[:1].isdigit() and not l[:1] == '-']; rows = [l for l in pcd if l[:1].isdigit() or l[:1] == '-']
            rows = rows[:max(1, len(rows) // 2)] + ['0.025 0.025 0.525', '1.025 -1.025 0.525']       # delete half the points, add two
            head = [f'WIDTH {len(rows)}' if l.startswith('WIDTH') else f'POINTS {len(rows)}' if l.startswith('POINTS') else l for l in head]
            kw = dict(asset_json=orig_json) if orig_json is not None else dict(fixture_boxes=orig_fix, extra_entry=dict(allow_empty=True, fixture=True))
            man = write_map_copy(ctx, m, out, **kw)
            doc = json.loads(man.read_text()); doc['maps'][0]['pcd_path'] = Path(entry['pcd_path']).name; man.write_text(json.dumps(doc))
            # copy of the manifest keeps the ORIGINAL pcd hash (stale on purpose): P must not look at the PCD at all
            (out / Path(entry['pcd_path']).name).write_text('\n'.join(head + rows) + '\n')
            a_edit = pa.load_primitive_asset(man, mid)
            s_edit = ctx.scene(a_edit)
            rng = np.random.default_rng(rng_seed + [2]); o = np.c_[rng.uniform(-4, 4, (2000, 2)), np.full(2000, .5)]; d = rng.normal(size=(2000, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
            same = dict(rays=bool(torch.equal(s0.raycast(tT(o[None], ctx), tT(d[None], ctx), max_range=6.), s_edit.raycast(tT(o[None], ctx), tT(d[None], ctx), max_range=6.))),
                        contains=bool(torch.equal(s0.contains(tT(o, ctx)), s_edit.contains(tT(o, ctx)))), occupancy=bool(torch.equal(s0.occupancy, s_edit.occupancy)),
                        height=bool(torch.equal(s0.planning_height(), s_edit.planning_height())), provenance=s0.provenance().keys() == s_edit.provenance().keys() and {k: v for k, v in s0.provenance().items() if k not in ('box_source', 'cpu_preprocess_s', 'device_upload_wall_s', 'hashes')} == {k: v for k, v in s_edit.provenance().items() if k not in ('box_source', 'cpu_preprocess_s', 'device_upload_wall_s', 'hashes')},
                        boxes_hash=a_edit.hashes['boxes'] == src_asset.hashes['boxes'])
            v3_changed = None
            try:
                dq = json.loads(man.read_text()); dq['maps'][0]['sha256']['pcd'] = sha256_file(out / Path(entry['pcd_path']).name); dq['maps'][0]['geometry_backend'] = 'pcd-voxel-v3'
                (out / 'manifest_v3.json').write_text(json.dumps(dq))
                v_orig, v_edit = v3_scene(ctx, m), VoxelScene.from_asset(load_asset(out / 'manifest_v3.json', mid), device=ctx.device, dtype=ctx.dtype)
                v3_changed = dict(occupancy_changed=not torch.equal(v_orig.occupancy, v_edit.occupancy), changed_cells=int((v_orig.occupancy != v_edit.occupancy).sum()))
            except Exception as exc:    # noqa: BLE001
                v3_changed = dict(error=f'{type(exc).__name__}: {exc}')
            res['pcd_only'].append(dict(id=mid, p_bitwise_unchanged=all(same.values()), details=same, v3_control=v3_changed))
        res['done_items'].append(dict(id=mid))
    res['status'] = 'pass' if all(c['pass'] for c in res['cases']) and all(c['p_bitwise_unchanged'] for c in res['pcd_only']) and (len(res['cases']) >= 9 or ctx.maps_only) else 'fail'
    res['original_assets_untouched_note'] = 'all edits are on copies under run_dir/E; originals are only read'
    return res


# ----------------------------------------------------------------------------- gate F
def contains_scene_refs(obj, depth=0, seen=None):
    seen = seen if seen is not None else set()
    if id(obj) in seen or depth > 7:
        return []
    seen.add(id(obj)); found = []
    banned = (ps.PrimitiveScene, ps.PrimitiveSceneBatch, VoxelScene, SceneBatch, pa.PrimitiveAsset)
    if isinstance(obj, banned):
        return [type(obj).__name__]
    if isinstance(obj, str):
        return [f'path:{obj}'] if obj.endswith('.json') else []
    if isinstance(obj, dict):
        for k, v in obj.items():
            found += contains_scene_refs(k, depth + 1, seen) + contains_scene_refs(v, depth + 1, seen)
    elif isinstance(obj, (list, tuple, set)):
        for v in obj:
            found += contains_scene_refs(v, depth + 1, seen)
    elif hasattr(obj, '__dict__') and not isinstance(obj, (torch.Tensor, type)):
        for v in vars(obj).values():
            found += contains_scene_refs(v, depth + 1, seen)
    return found


def gate_F(ctx):
    from task7_sim.core import Candidate
    from task8_sim.decision_env import PcdDecisionEnv
    from task8_sim.env import PcdEpisodeEnv
    F = dict(ctx.P['F'])
    if ctx.a.profiles:
        F['profiles'] = ctx.a.profiles.split(',')
    res = dict(signatures={}, pickle={}, chain=[], information_boundary=[], profiles=F['profiles'])
    # signatures
    for name in ('raycast', 'contains', 'collide', 'planning_height', 'provenance'):
        res['signatures'][f'scene.{name}'] = str(inspect.signature(getattr(ps.PrimitiveScene, name))) == str(inspect.signature(getattr(VoxelScene, name)))
    res['signatures']['scene.occupancy_property'] = isinstance(ps.PrimitiveScene.occupancy, property) and isinstance(VoxelScene.occupancy, property)
    res['signatures']['scene.from_asset'] = str(inspect.signature(ps.PrimitiveScene.from_asset)) == str(inspect.signature(VoxelScene.from_asset))
    for name in ('raycast', 'contains', 'collide', 'planning_height', 'provenance', 'select', 'replace', '__len__', '__init__'):
        res['signatures'][f'batch.{name}'] = str(inspect.signature(getattr(ps.PrimitiveSceneBatch, name))) == str(inspect.signature(getattr(SceneBatch, name)))
    res['signatures']['backend_default_v3'] = all(inspect.signature(c.__init__).parameters['map_backend'].default == 'pcd-voxel-v3' for c in (PcdEpisodeEnv, PcdDecisionEnv, __import__('task8_sim.episode', fromlist=['x']).PcdEpisodeSampler))
    dev = ctx.device; dtype = ctx.dtype
    maps = map_sets(ctx, kinds=('semantic',))[:F['semantic_maps']] + map_sets(ctx, kinds=('cube',), cube_n=F['cube_maps']) + (map_sets(ctx, kinds=('fixture',)) if not ctx.smoke else [])
    if ctx.a.maps_limit:
        maps = maps[:ctx.a.maps_limit]
    # pickle round trip
    m0 = maps[0]; a = load_asset_for(m0); s = ctx.scene(a); b = ps.PrimitiveSceneBatch([s, s])
    rng = np.random.default_rng(1); o = tT(np.concatenate([rng.uniform(-4, 4, (2, 50, 2)), np.full((2, 50, 1), .5)], -1), ctx); d = tT(rng.normal(size=(2, 50, 3)), ctx); d = d / d.norm(dim=-1, keepdim=True)
    before = b.raycast(o, d, max_range=6.); b2 = pickle.loads(pickle.dumps(b)); s2 = pickle.loads(pickle.dumps(s))
    res['pickle'] = dict(batch_equal=bool(torch.equal(b2.raycast(o, d, max_range=6.), before)), scene_equal=bool(torch.equal(s2.raycast(o[:1], d[:1], max_range=6.), before[:1])), provenance_equal=s2.provenance() == s.provenance(), device=str(s2.device))
    pool_for = lambda m: m['manifest']
    combos = [dict(id=f"{m_['id']}:{p_}", m=m_, profile=p_) for m_ in maps for p_ in F['profiles']]
    if True:
        for item in ctx.iter_items(res, 'chain', combos):
            m, profile = item['m'], item['profile']
            entry = [e for e in pool_entries(m['manifest']) if e['id'] == m['id']][0]
            ctx.tick(); rec = dict(map=m['id'], kind=m['kind'], profile=profile, device=str(dev), dtype=str(dtype), backend=ps.BACKEND)
            t0 = time.monotonic()
            try:
                if profile == 'sync_v5':
                    env = PcdEpisodeEnv(1, seed=ctx.cfg['seeds']['reset'], pool=pool_for(m), profile=profile, device=dev, dtype=dtype, split=entry['split'], difficulty=entry['difficulty'], map_backend=ps.BACKEND)
                    env.sampler.entries = [e for e in env.sampler.entries if e['id'] == m['id']]
                    env.reset(deadline=time.monotonic() + 90)
                    c = env.core; frames = c.sensor_frames.clone(); before_q = c.state.q.clone()
                    rec['reset_wall_s'] = time.monotonic() - t0
                    env.begin(Candidate(c.state.base.clone(), c.route.length.clone(), torch.ones_like(c.done)))
                    out = env.step(c.state.base.new_tensor([[0., 0., 1.]]))
                    rec.update(committed=out.transition.committed.tolist(), failure_kind=c.failure_kind.tolist(), q_changed=bool((c.state.q != before_q).any()), sensor_frames_delta=(c.sensor_frames - frames).tolist(),
                               grid_observed_cells=int(c.grid.observed.sum()), grid_timestamp=c.grid.timestamp.tolist(), scene_batch=type(env.scenes).__name__, versions=env.versions, map_ids=env.map_ids)
                    rec['information_leak'] = contains_scene_refs({k: v for k, v in out.transition.next_observation.items()})
                else:
                    def script(obs):
                        z = obs['q'].new_zeros(len(obs['q']), 3); z[:, 2] = 1
                        return z
                    env = PcdDecisionEnv(1, script, seed=ctx.cfg['seeds']['reset'], pool=pool_for(m), profile=profile, device=dev, dtype=dtype, run_id='t8-prim-verify-F', split=entry['split'], difficulty=entry['difficulty'], map_backend=ps.BACKEND)
                    obs, cand = env.reset(map_ids=[m['id']], deadline=time.monotonic() + 90)
                    rec['reset_wall_s'] = time.monotonic() - t0
                    out = env.step(torch.tensor([12], device=dev))
                    rec.update(reward=float(out.reward), terminated=bool(out.terminated), truncated=bool(out.truncated), dt=float(out.dt), scene_batch=type(env.episodes.scenes).__name__, versions=env.episodes.versions)
                    rec['information_leak'] = contains_scene_refs(dict(obs=out.observation, cand=out.candidates, replay=out.replay_fields))
                rec['ok'] = True
            except Exception as exc:       # noqa: BLE001
                rec.update(ok=False, error=f'{type(exc).__name__}: {exc}')
            res['chain'].append(rec)
    res['existing_tests_note'] = 'Existing task8 tests are v3-specific; geometry-independent ones are run unchanged by the executor from a parent-approved node list. Not executed in this mode.'
    leaks = [r.get('information_leak') for r in res['chain'] if r.get('information_leak')]
    res['status'] = 'pass' if (all(res['signatures'].values()) and res['pickle'].get('batch_equal') and res['pickle'].get('scene_equal') and res['pickle'].get('provenance_equal')
                               and res['chain'] and all(r['ok'] for r in res['chain']) and not leaks) else 'fail'
    return res


# ----------------------------------------------------------------------------- gate G
def gpu_state():
    try:
        out = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader'], capture_output=True, text=True, timeout=20)
        return dict(compute_apps=[l for l in out.stdout.splitlines() if l.strip()], rc=out.returncode)
    except Exception as exc:       # noqa: BLE001
        return dict(error=str(exc))


def timed(fn, device, warmup, repeats):
    cuda = device.type == 'cuda'
    if cuda:
        torch.cuda.synchronize(device)
    t = time.perf_counter(); fn()
    if cuda:
        torch.cuda.synchronize(device)
    cold = time.perf_counter() - t
    for _ in range(warmup):
        fn()
    events, walls = [], []
    for _ in range(repeats):
        if cuda:
            torch.cuda.synchronize(device); a = torch.cuda.Event(enable_timing=True); b = torch.cuda.Event(enable_timing=True); a.record()
        t = time.perf_counter(); fn()
        if cuda:
            b.record(); torch.cuda.synchronize(device); events.append(a.elapsed_time(b) / 1000)
        walls.append(time.perf_counter() - t)
    return dict(cold_wall_s=cold, wall_s=stats(walls), cuda_event_s=stats(events) if events else None, wall_samples=walls, cuda_event_samples=events)


def gate_G(ctx):
    from task7_sim.episode import CBL_Q
    from task8_sim.robot import GhostRobotGeometry
    G = ctx.P['G']; dev = ctx.device; dtype = {'float32': torch.float32, 'float64': torch.float64}[G['dtype']] if not ctx.a.dtype_explicit else ctx.dtype
    res = dict(device=str(dev), dtype=str(dtype), gpu_before=gpu_state(), cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES'), builds=[], scan=[], collide=[])
    if dev.type == 'cuda':
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA requested but unavailable; no CPU fallback')
        res['gpu_name'] = torch.cuda.get_device_name(dev); res['mem_used_before_bytes'] = torch.cuda.mem_get_info(dev)[1] - torch.cuda.mem_get_info(dev)[0]
        if res['gpu_before'].get('compute_apps') and not ctx.a.allow_busy_gpu:
            return dict(res, status='gpu_busy')
    sem_ids = {e['id'] for e in pool_entries(ctx.path('semantic_manifest'))}
    lookup = {mid: dict(kind='semantic' if mid in sem_ids else 'cube', manifest=ctx.path('semantic_manifest' if mid in sem_ids else 'cube_manifest'), id=mid) for mid in G['maps']}
    scenes = {}
    for mid, m in lookup.items():
        ctx.tick(); rec = dict(id=mid, kind=m['kind'])
        for arm in ('P', 'PV', 'V3'):
            walls, pre = [], []
            for r in range(3 if not ctx.smoke else 2):
                if dev.type == 'cuda':
                    torch.cuda.synchronize(dev)
                t = time.perf_counter()
                if arm == 'V3':
                    sc = VoxelScene.from_asset(load_asset(m['manifest'], mid), device=dev, dtype=dtype)
                else:
                    asset = pa.load_primitive_asset(m['manifest'], mid)
                    sc = (ps.PrimitiveScene if arm == 'P' else ps.PrimitiveVoxelDiagScene).from_asset(asset, device=dev, dtype=dtype)
                if dev.type == 'cuda':
                    torch.cuda.synchronize(dev)
                walls.append(time.perf_counter() - t); pre.append(sc.provenance().get('cpu_preprocess_s'))
            rec[arm] = dict(build_wall_s=stats(walls), build_samples=walls, cpu_preprocess_s=stats(pre), tensor_bytes=sc.provenance().get('tensor_bytes'), samples_note='includes manifest/asset read and, for V3, PCD parse')
            scenes[(arm, mid)] = sc
        res['builds'].append(rec)
    rng = np.random.default_rng(ctx.cfg['seeds']['perf'])
    robot = GhostRobotGeometry(); q0 = torch.tensor(CBL_Q, device=dev, dtype=dtype)[None]
    mids = list(lookup)
    for B in G['batches']:
        base = np.c_[rng.uniform(-4.5, 4.5, (B, 2)), rng.uniform(0, 2 * math.pi, B)]
        dirs = np.stack([scan_dirs(y) for y in base[:, 2]]); org = np.concatenate([base[:, None, :2].repeat(32400, 1), np.full((B, 32400, 1), .5)], -1)
        o, d = tT(org, ctx, dtype), tT(dirs, ctx, dtype)
        for layout in ('same', 'hetero'):
            ids = [mids[0]] * B if layout == 'same' else [mids[i % len(mids)] for i in range(B)]
            for arm in ('P', 'PV', 'V3'):
                ctx.tick()
                rows = [scenes[(arm, i)] for i in ids]
                batch = ps.PrimitiveSceneBatch(rows) if arm == 'P' else SceneBatch(rows)
                if dev.type == 'cuda':
                    torch.cuda.reset_peak_memory_stats(dev)
                r = timed(lambda: batch.raycast(o, d, max_range=6.), dev, G['warmup'], G['repeats'])
                r.update(batch=B, layout=layout, arm=arm, rays=B * 32400, peak_bytes=torch.cuda.max_memory_allocated(dev) if dev.type == 'cuda' else None)
                r['rays_per_s_median_wall'] = B * 32400 / r['wall_s']['median']
                res['scan'].append(r)
    for B in G['collision_batches']:
        bt = tT(np.c_[rng.uniform(-4.8, 4.8, (B, 2)), rng.uniform(0, 2 * math.pi, B)], ctx, dtype); qt = q0.expand(B, -1).clone(); caps = robot(bt, qt)
        for layout in ('same', 'hetero'):
            ids = [mids[0]] * B if layout == 'same' else [mids[i % len(mids)] for i in range(B)]
            for arm in ('P', 'PV', 'V3'):
                ctx.tick()
                rows = [scenes[(arm, i)] for i in ids]
                batch = ps.PrimitiveSceneBatch(rows) if arm == 'P' else SceneBatch(rows)
                if dev.type == 'cuda':
                    torch.cuda.reset_peak_memory_stats(dev)
                r = timed(lambda: batch.collide(bt, caps, robot=robot, q=qt), dev, G['warmup'], G['repeats'])
                r.update(batch=B, layout=layout, arm=arm, peak_bytes=torch.cuda.max_memory_allocated(dev) if dev.type == 'cuda' else None)
                res['collide'].append(r)
    res['gpu_after'] = gpu_state()
    if dev.type == 'cuda':
        res['mem_peak_overall_bytes'] = torch.cuda.max_memory_allocated(dev)
    res['status'] = 'report'
    res['note'] = 'Report only: no throughput gate. Compare arms P/PV/V3 on identical inputs; hetero cycles through the listed maps.'
    return res


# ----------------------------------------------------------------------------- gate H
def snapshot(ctx):
    H_ = ctx.cfg['H']; files = {}
    for pattern in H_['protected_globs']:
        for f in glob.glob(str(ROOT / pattern), recursive=True):
            if os.path.isfile(f) and '__pycache__' not in f:
                files[os.path.relpath(f, ROOT)] = sha256_file(f)
    for d in H_['asset_dirs']:
        for f in sorted(glob.glob(str(ROOT / d / '**'), recursive=True)):
            if os.path.isfile(f):
                files[os.path.relpath(f, ROOT)] = sha256_file(f)
    for f in H_['asset_manifests']:
        if (ROOT / f).is_file():
            files[f] = sha256_file(ROOT / f)
    mg = ROOT.parent / 'mapgen/outputs/all_maps'
    for f in sorted(mg.glob('*')) if mg.is_dir() else []:
        files[os.path.relpath(f, ROOT)] = sha256_file(f)
    return files


def gate_H(ctx):
    res = dict(action=ctx.a.h_action)
    snap = snapshot(ctx); res['files'] = len(snap)
    if ctx.a.h_action == 'snapshot':
        res['snapshot'] = snap; res['status'] = 'snapshot'
        return res
    base = json.loads(Path(ctx.a.baseline).read_text())['snapshot']
    allowed = set(ctx.cfg['H']['allowed_changed']); globs = ctx.cfg['H']['allowed_changed_globs']
    import fnmatch
    changed = sorted(k for k in snap if k in base and snap[k] != base[k]); added = sorted(k for k in snap if k not in base); removed = sorted(k for k in base if k not in snap)
    ok = lambda k: k in allowed or any(fnmatch.fnmatch(k, g) for g in globs)
    res.update(changed=changed, added=added, removed=removed, unexpected_changed=[k for k in changed if not ok(k)], unexpected_added=[k for k in added if not ok(k)], unexpected_removed=removed,
               allowed_changed_seen=[k for k in changed if ok(k)])
    tokens = ctx.cfg['H']['forbidden_tokens_in_new_files']; hits = {}
    for f in ['src/task8_sim/primitive_assets.py', 'src/task8_sim/primitive_scene.py', 'scripts/task8_prim_verify.py'] + [os.path.relpath(f, ROOT) for f in glob.glob(str(ROOT / 'src/task8_sim/tests/test_primitive_*.py'))]:
        text = (ROOT / f).read_text(); found = [t for t in tokens if t in text and f != 'scripts/task8_prim_verify.py']
        if found:
            hits[f] = found
    res['forbidden_token_hits'] = hits
    cmds = []
    for f in sorted(Path(ctx.ledger_dir).glob('ledger-*.jsonl')):
        cmds += [json.loads(l)['cmd'] for l in f.read_text().splitlines() if l.strip()]
    bad = [c for c in cmds if any(t in c.lower() for t in ('task7_lower', 'test_lower', 'train', 'optim'))]
    res['ledger_commands'] = len(cmds); res['training_like_commands'] = bad
    ps_out = subprocess.run(['ps', '-eo', 'pid,etimes,cmd'], capture_output=True, text=True).stdout.splitlines()
    res['stray_python_processes'] = [l.strip() for l in ps_out if ('python' in l or 'pytest' in l) and str(os.getpid()) not in l.split()[:1] and 'task8_prim_verify' not in l and 'ps -eo' not in l]
    res['no_stray_python_process'] = not res['stray_python_processes']
    res['stray_python_process_count'] = len(res['stray_python_processes']); res['stray_python_processes'] = [l[:200] for l in res['stray_python_processes'][:20]]
    res['status'] = 'pass' if not res['unexpected_changed'] and not res['unexpected_added'] and not removed and not hits and not bad else 'fail'
    return res


# ----------------------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--mode', required=True, help='A-H or name (import/analytic/structure/diff/intervene/interface/perf/fidelity)')
    p.add_argument('--run-dir', required=True)
    p.add_argument('--smoke', action='store_true')
    p.add_argument('--device', default='cpu')
    p.add_argument('--dtype', default=None, choices=[None, 'float32', 'float64'])
    p.add_argument('--reference', default=None)
    p.add_argument('--role', default=None, help='ledger role; with --append-ledger an entry is written to ledger-<role>.jsonl')
    p.add_argument('--append-ledger', action='store_true')
    p.add_argument('--mode-budget-s', type=float, default=600.)
    p.add_argument('--min-remaining-s', type=float, default=30.)
    p.add_argument('--allow-busy-gpu', action='store_true')
    p.add_argument('--h-action', default='snapshot', choices=['snapshot', 'compare'])
    p.add_argument('--baseline', default=None)
    p.add_argument('--maps-only', default=None, help='all gates: comma list of map ids (F: map ids) to run, for timing pilots/resume')
    p.add_argument('--resume', action='store_true', help='merge into an existing gate_X.json, skipping maps already completed')
    p.add_argument('--profiles', default=None, help='F only: comma list overriding the configured profiles')
    p.add_argument('--maps-limit', type=int, default=None, help='F only: use at most this many maps')
    a = p.parse_args()
    a.dtype_explicit = a.dtype is not None
    a.dtype = a.dtype or ('float32' if a.device.startswith('cuda') else 'float64')
    gate = a.mode.upper() if a.mode.upper() in GATES else next(k for k, v in GATES.items() if v == a.mode.lower())
    ctx = Ctx(a)
    remaining = ctx.limit - ctx.used_at_start
    if remaining < a.min_remaining_s:
        print(json.dumps(dict(gate=gate, status='ledger_exhausted', used_s=ctx.used_at_start, limit_s=ctx.limit)))
        return 3
    if a.device.startswith('cuda') and not torch.cuda.is_available():
        print('CUDA requested but unavailable; no CPU fallback', file=sys.stderr); return 4
    head = dict(gate=gate, mode=GATES[gate], smoke=ctx.smoke, started_utc=utc(), device=str(ctx.device), dtype=str(ctx.dtype), argv=sys.argv, role=a.role,
                ledger_used_at_start_s=ctx.used_at_start, ledger_limit_s=ctx.limit, mode_budget_s=min(a.mode_budget_s, remaining),
                config_sha256=sha256_file(CFG_PATH), code_sha256={f: sha256_file(ROOT / f) for f in ('src/task8_sim/primitive_assets.py', 'src/task8_sim/primitive_scene.py', 'scripts/task8_prim_verify.py')},
                torch=torch.__version__, cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES'))
    ctx.head = head; ctx.gate = gate
    target = ctx.run_dir / f'gate_{gate}.json'
    if a.resume and target.is_file():
        ctx.prev = json.loads(target.read_text())
    rc = 1; result = None
    try:
        result = globals()['gate_' + gate](ctx)
        rc = 0
        if ctx.key and result is ctx.res:
            done = [r.get('id') for r in result.get(ctx.key, [])]
            result.update(completed_maps=done, remaining_maps=[i for i in ctx.all_ids if i not in set(done)], subset=bool(ctx.maps_only), resumed=bool(ctx.prev))
    except BudgetExceeded as exc:
        result = ctx.partial('incomplete_budget', f'BudgetExceeded: {exc}'); rc = 2
    except Exception as exc:        # noqa: BLE001
        import traceback
        result = ctx.partial('error', f'{type(exc).__name__}: {exc}', traceback.format_exc()[-4000:]); rc = 1
    out = dict(head, **result, wall_s=time.monotonic() - ctx.start, finished_utc=utc())
    dump(ctx.run_dir / f'gate_{gate}.json', out)
    if a.append_ledger and a.role:
        ctx.ledger_dir.mkdir(parents=True, exist_ok=True)
        with (ctx.ledger_dir / f'ledger-{a.role}.jsonl').open('a') as f:
            f.write(json.dumps(dict(role=a.role, cmd=' '.join(sys.argv), start_utc=head['started_utc'], wall_s=round(out['wall_s'], 3), rc=rc, device=str(ctx.device))) + '\n')
    summary = {k: result.get(k) for k in ('status', 'error') if k in result}
    print(json.dumps(dict(gate=gate, smoke=ctx.smoke, rc=rc, wall_s=round(out['wall_s'], 2), out=str(ctx.run_dir / f'gate_{gate}.json'), **summary)))
    return rc


if __name__ == '__main__':
    sys.exit(main())
