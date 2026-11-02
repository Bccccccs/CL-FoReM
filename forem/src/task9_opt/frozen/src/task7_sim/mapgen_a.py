"""Seeded A maps. Runtime dependency: numpy only (no torch, ROS or API).

Contract/provenance: task7.16 TASK M1–M4; SOURCES SRC-0433/SRC-0450.
All boxes use [corner_x,corner_y,z,length,width,height,cos(theta),sin(theta)].
Sampling and checks are pure functions; only the CLI writes batch artifacts.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import time
import zlib

import numpy as np

EPS = np.finfo(np.float64).eps * 32  # arithmetic roundoff only, as geometry.load_map


def canonical_walls():
    """Same four non-overlapping wall strips as geometry.load_map."""
    return [[-5., -5., 0., .15, 10., 1.6, 1., 0.],
            [4.85, -5., 0., .15, 10., 1.6, 1., 0.],
            [-4.85, -5., 0., 9.7, .15, 1.6, 1., 0.],
            [-4.85, 4.85, 0., 9.7, .15, 1.6, 1., 0.]]


def corners(box):
    b = np.asarray(box, dtype=np.float64)
    local = np.array([[0., 0.], [b[3], 0.], [b[3], b[4]], [0., b[4]]])
    return local @ np.array([[b[6], b[7]], [-b[7], b[6]]]) + b[:2]


def _overlap(a, b):
    """Positive interior overlap by SAT; touching faces have no volume overlap."""
    ca, cb = corners(a), corners(b)
    axes = np.array([[a[6], a[7]], [-a[7], a[6]],
                     [b[6], b[7]], [-b[7], b[6]]])
    pa, pb = ca @ axes.T, cb @ axes.T
    return bool(np.all(np.minimum(pa.max(0), pb.max(0)) -
                       np.maximum(pa.min(0), pb.min(0)) > EPS))


def _origin_distance(b):
    delta = -np.asarray(b[:2])
    q = np.array([b[6]*delta[0]+b[7]*delta[1],
                  -b[7]*delta[0]+b[6]*delta[1]])
    return float(np.linalg.norm(q - np.clip(q, 0., b[3:5])))


def _box_reasons(b):
    if not np.isfinite(b).all():
        return ['nonfinite']
    reasons = []
    if abs(b[6]**2+b[7]**2-1) > 1e-6:
        reasons.append('rotation')
    if min(b[3:6]) < .10:
        reasons.append('minimum_size')
    xy = corners(b)
    if (np.abs(xy) > 5+EPS).any() or b[2] < -EPS or b[2]+b[5] > 1.6+EPS:
        reasons.append('out_of_bounds')
    if _origin_distance(b) < .7-EPS:
        reasons.append('origin_clearance')
    return reasons


def geometry_report(data):
    rows = np.asarray(data['boxes'], dtype=np.float64)
    if rows.ndim != 2 or rows.shape[1] != 8:
        raise ValueError('boxes must have shape (N,8)')
    reasons = []
    walls = np.array(canonical_walls())
    wall_mask = np.zeros(len(rows), dtype=bool)
    for w in walls:
        matched = np.all(np.abs(rows-w) <= EPS, axis=1)
        if matched.sum() != 1:
            reasons.append('walls')
        wall_mask |= matched
    layers = {key: {'count': 0, 'area_m2': 0.} for key in
              ('base_only', 'arm_band', 'full_height', 'outside_sampling_bands')}
    for i, b in enumerate(rows):
        reasons.extend(_box_reasons(b))
        if np.isfinite(b).all() and not wall_mask[i]:
            key = ('base_only' if .1 <= b[5] <= .38 else
                   'arm_band' if .4 <= b[5] <= 1.1 else
                   'full_height' if 1.2 <= b[5] <= 1.6 else 'outside_sampling_bands')
            layers[key]['count'] += 1
            layers[key]['area_m2'] += float(b[3]*b[4])
        if np.isfinite(b).all() and abs(b[6]**2+b[7]**2-1) <= 1e-6:
            if any(_overlap(b, p) and min(b[2]+b[5], p[2]+p[5])-max(b[2], p[2]) > EPS
                   for p in rows[:i] if np.isfinite(p).all() and abs(p[6]**2+p[7]**2-1) <= 1e-6):
                reasons.append('overlap')
    return {'geometry_valid': not reasons, 'reasons': sorted(set(reasons)),
            'height_layers': layers, 'obstacle_count': int((~wall_mask).sum())}


def generate_candidate(seed, *, grid_spacing, grid_origin, generator_version):
    """One geometrically filtered candidate. No grid acceptance or seed retry.

    M4: initial draw plus at most 20 redraws per grid point, then skip.
    Origin-clearance failures are redrawn like other geometric failures.
    """
    if grid_spacing not in (3., 4.) or len(grid_origin) != 2 or not np.isfinite(grid_origin).all():
        raise ValueError('M1 requires spacing 3 or 4 and a finite XY grid origin')
    rng = np.random.default_rng(seed)
    boxes = canonical_walls()
    metadata = [{'name': 'wall_'+str(i), 'category': 'wall'} for i in range(4)]
    rejected = Counter()
    skipped = 0
    grid_points = 0
    for col, x in enumerate(np.arange(grid_origin[0], 5., grid_spacing)):
        for y in np.arange(grid_origin[1]+(col % 2)*grid_spacing/2, 5., grid_spacing):
            grid_points += 1
            for attempt in range(21):
                px, py = np.array([x, y]) + rng.normal(0., .8, 2)
                length, width = rng.uniform(.1, 1.5), rng.uniform(.1, 1.)
                theta = rng.uniform(0., np.pi)
                layer = int(rng.choice(3, p=[.25, .40, .35]))
                lo, hi = ((.1, .38), (.4, 1.1), (1.2, 1.6))[layer]
                b = [float(px), float(py), 0., float(length), float(width),
                     float(rng.uniform(lo, hi)), float(np.cos(theta)), float(np.sin(theta))]
                reasons = _box_reasons(b)
                if any(_overlap(b, prev) for prev in boxes):
                    reasons.append('overlap')
                if reasons:
                    rejected.update(set(reasons))
                    continue
                boxes.append(b)
                metadata.append({'name': 'box_'+str(grid_points),
                                 'category': ('base_only', 'arm_band', 'full_height')[layer]})
                break
            else:
                skipped += 1
    data = {'boxes': boxes, 'box_metadata': metadata,
            'metadata': {'method': 'programmatic_numpy', 'seed': int(seed),
                         'generator_version': dict(generator_version),
                         'acceptance': 'geometry_only',
                         'parameters': {'grid_spacing_m': float(grid_spacing),
                                        'grid_origin': list(grid_origin), 'offset_std_m': .8,
                                        'length_range_m': [.1, 1.5], 'width_range_m': [.1, 1.],
                                        'theta_range_rad': [0., float(np.pi)],
                                        'height_probabilities': [.25, .40, .35],
                                        'height_ranges_m': [[.1, .38], [.4, 1.1], [1.2, 1.6]],
                                        'origin_clearance_m': .7, 'max_redraws_per_point': 20},
                         'sampling': {'grid_points': grid_points, 'skipped_points': skipped,
                                      'rejected_draw_reasons': dict(rejected)}}}
    data['checks'] = geometry_report(data)
    return data


def rasterize(data, resolution=.05):
    """Closed cell-square/OBB intersection (SAT); map covers [-5,5]^2."""
    n = round(10/resolution)
    coord = -5+(np.arange(n)+.5)*resolution
    xx, yy = np.meshgrid(coord, coord)
    occupied = np.zeros((n, n), dtype=bool)
    for b in data['boxes']:
        if b[5] < .1:
            continue
        c, s = b[6:8]
        cx, cy = b[0]+c*b[3]/2-s*b[4]/2, b[1]+s*b[3]/2+c*b[4]/2
        dx, dy = xx-cx, yy-cy
        hit = ((abs(dx) <= abs(c)*b[3]/2+abs(s)*b[4]/2+resolution/2+EPS) &
               (abs(dy) <= abs(s)*b[3]/2+abs(c)*b[4]/2+resolution/2+EPS) &
               (abs(c*dx+s*dy) <= b[3]/2+resolution/2*(abs(c)+abs(s))+EPS) &
               (abs(-s*dx+c*dy) <= b[4]/2+resolution/2*(abs(c)+abs(s))+EPS))
        occupied |= hit
    return occupied


def distance_transform(occupied, resolution=.05):
    """Exact separable squared Euclidean transform of cell centres, float64.

    Vectorized min-plus along both axes; no scipy dependency or approximate metric.
    """
    f = np.where(occupied, 0., np.inf)
    for axis in (0, 1):
        a = np.moveaxis(f, axis, -1)
        indices = np.arange(a.shape[-1], dtype=np.float64)
        squared = (indices[:, None]-indices[None, :])**2
        # One row at a time bounds temporary memory independent of map area.
        result = np.empty_like(a)
        for i in range(len(a)):
            result[i] = np.min(a[i, None, :]+squared, axis=1)
        f = np.moveaxis(result, -1, axis)
    return np.sqrt(f)*resolution


def connectivity_ratio(free):
    """Largest four-neighbour component / all free cells; no free cells => 0."""
    remaining = free.copy()
    total = int(free.sum())
    maximum = 0
    while remaining.any():
        seed = np.argwhere(remaining)[0]
        region = np.zeros_like(free)
        region[tuple(seed)] = True
        while True:
            grown = region.copy()
            grown[1:] |= region[:-1]
            grown[:-1] |= region[1:]
            grown[:, 1:] |= region[:, :-1]
            grown[:, :-1] |= region[:, 1:]
            grown &= remaining
            if np.array_equal(grown, region):
                break
            region = grown
        size = int(region.sum())
        maximum = max(maximum, size)
        remaining &= ~region
    return maximum/total if total else 0.


def skeletonize(free):
    """Zhang–Suen two-subiteration thinning, padded occupied exterior.

    Engineering implementation of M2's free-space skeleton, not a new gate.
    """
    image = np.pad(free, 1).astype(bool)
    while True:
        removed = 0
        for step in (0, 1):
            p = [image[:-2, 1:-1], image[:-2, 2:], image[1:-1, 2:], image[2:, 2:],
                 image[2:, 1:-1], image[2:, :-2], image[1:-1, :-2], image[:-2, :-2]]
            neighbors = sum(x.astype(np.uint8) for x in p)
            transitions = sum((~p[i] & p[(i+1) % 8]).astype(np.uint8) for i in range(8))
            if step == 0:
                keep1, keep2 = p[0] & p[2] & p[4], p[2] & p[4] & p[6]
            else:
                keep1, keep2 = p[0] & p[2] & p[6], p[0] & p[4] & p[6]
            delete = image[1:-1, 1:-1] & (neighbors >= 2) & (neighbors <= 6) & (transitions == 1) & ~keep1 & ~keep2
            removed += int(delete.sum())
            image[1:-1, 1:-1] &= ~delete
        if removed == 0:
            return image[1:-1, 1:-1]


def _distribution(values):
    if not len(values):
        return {'count': 0, 'min': None, 'p05': None, 'p50': None, 'p95': None, 'max': None}
    q = np.quantile(values, [0, .05, .5, .95, 1])
    return dict(count=int(len(values)), **dict(zip(('min', 'p05', 'p50', 'p95', 'max'), map(float, q))))


def check_map(data):
    report = geometry_report(data)
    if not report['geometry_valid']:
        return dict(report, accepted=False)
    occupied = rasterize(data)
    distance = distance_transform(occupied)
    free = ~occupied
    ratio = connectivity_ratio(distance > .40+EPS)
    widths = 2*distance[skeletonize(free)]
    report.update(accepted=bool(ratio >= .9), connectivity_ratio=ratio,
                  turning_fraction=float(((distance >= .60-EPS) & free).sum()/free.sum()) if free.any() else 0.,
                  channel_width_m=_distribution(widths), resolution_m=.05,
                  raster_rule='closed_cell_intersection', connectivity_neighbors=4,
                  distance_rule='euclidean_cell_centres', skeleton_rule='zhang_suen')
    if ratio < .9:
        report['reasons'].append('connectivity')
    return report


def preview_rgb(data):
    """Top-down cell-intersection rendering from the serialized corner boxes."""
    palette = {'wall': (40, 40, 40), 'base_only': (55, 145, 230),
               'arm_band': (245, 165, 40), 'full_height': (160, 65, 175)}
    rgb = np.full((200, 200, 3), 255, dtype=np.uint8)
    for b, info in zip(data['boxes'], data['box_metadata']):
        rgb[rasterize({'boxes': [b]})] = palette[info['category']]
    return rgb[::-1].copy()  # PNG top row is positive world y.


def _write_png(path, rgb):
    def chunk(kind, content):
        return struct.pack('!I', len(content))+kind+content+struct.pack('!I', zlib.crc32(kind+content) & 0xffffffff)
    raw = b''.join(b'\0'+row.tobytes() for row in rgb)
    height, width = rgb.shape[:2]
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))+
                     chunk(b'IDAT', zlib.compress(raw))+chunk(b'IEND', b''))


def _evaluate(job):
    seed, difficulty, version = job
    start = time.perf_counter()
    data = generate_candidate(seed, grid_spacing={'sparse': 4., 'standard': 3.}[difficulty],
                              grid_origin=(-5., -5.), generator_version=version)
    data['metadata']['difficulty'] = difficulty
    data['checks'] = check_map(data)
    data['metadata']['acceptance'] = 'accepted' if data['checks']['accepted'] else 'rejected'
    return data, time.perf_counter()-start


def run_batch(output, config, *, mode, version, workers):
    """Bounded, ordered CPU multiprocessing. Distinct seed per attempted map."""
    from concurrent.futures import ProcessPoolExecutor
    if not 1 <= workers <= 16:
        raise ValueError('workers must be in [1,16]')
    intervals = []
    for difficulty in ('sparse', 'standard'):
        for split in ('pilot', 'train', 'validation', 'test'):
            lo, hi = config['seed_ranges'][difficulty][split]
            count = config['counts'][split]
            if not isinstance(count, int) or count <= 0 or lo < 0 or hi-lo+1 < count*10:
                raise ValueError('seed range must cover the positive target times ten')
            if any(lo <= prev_hi and hi >= prev_lo for prev_lo, prev_hi in intervals):
                raise ValueError('overlapping seed ranges')
            intervals.append((lo, hi))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output/'maps').mkdir()
    (output/'reports').mkdir()
    index = {'mode': mode, 'generator_version': version, 'workers': workers,
             'seed_ranges': config['seed_ranges'], 'maps': [], 'collections': [],
             'pcd': 'not_exported_optional', 'preview_palette': {
                 'wall': [40, 40, 40], 'base_only': [55, 145, 230],
                 'arm_band': [245, 165, 40], 'full_height': [160, 65, 175]}}
    global_start = time.perf_counter()
    worker_seconds = 0.
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for difficulty in ('sparse', 'standard'):
            sets = ['pilot'] if mode == 'pilot' else ['validation', 'test', 'train']
            for split in sets:
                target = config['counts'][split]
                first_seed = config['seed_ranges'][difficulty][split][0]
                attempts, accepted, unused = 0, 0, 0
                reasons = Counter()
                samples = []
                skips = 0
                collection_start = time.perf_counter()
                records = []
                while accepted < target and attempts < target*10:
                    n = min(workers, target*10-attempts)
                    jobs = [(seed, difficulty, version) for seed in range(first_seed+attempts, first_seed+attempts+n)]
                    results = list(pool.map(_evaluate, jobs))
                    worker_seconds += sum(elapsed for _, elapsed in results)
                    for data, elapsed in results:
                        if accepted >= target:
                            unused += 1
                            continue
                        attempts += 1
                        check = data['checks']
                        skips += data['metadata']['sampling']['skipped_points']
                        samples.append(elapsed)
                        records.append({'seed': data['metadata']['seed'], 'checks': check,
                                        'sampling': data['metadata']['sampling'], 'seconds': elapsed})
                        if not check['accepted']:
                            reasons.update(check['reasons'])
                            continue
                        name = f'{difficulty}_{split}_{accepted:05d}'
                        relative = 'maps/map_'+name
                        t_io = time.perf_counter()
                        (output/(relative+'.json')).write_text(json.dumps(data, sort_keys=True, allow_nan=False))
                        (output/(relative+'_check.json')).write_text(json.dumps(check, sort_keys=True, allow_nan=False))
                        _write_png(output/(relative+'.png'), preview_rgb(data))
                        index['maps'].append({'id': name, 'path': relative+'.json',
                                              'seed': data['metadata']['seed'], 'difficulty': difficulty,
                                              'split': split, 'artifact_write_seconds': time.perf_counter()-t_io})
                        accepted += 1
                collection = {'difficulty': difficulty, 'split': split, 'target': target,
                              'attempts': attempts, 'accepted': accepted, 'unused_evaluations': unused,
                              'acceptance_rate': accepted/attempts if attempts else 0.,
                              'rejection_reasons': dict(reasons), 'skipped_grid_points': skips,
                              'evaluation_seconds': _distribution(samples),
                              'wall_seconds': time.perf_counter()-collection_start,
                              'stopped': accepted < target or (split == 'pilot' and accepted/attempts < .20)}
                index['collections'].append(collection)
                (output/'reports'/f'{difficulty}_{split}.json').write_text(json.dumps(
                    {'summary': collection, 'attempt_records': records}, sort_keys=True, allow_nan=False))
                print(json.dumps(collection, sort_keys=True), flush=True)
                (output/'index.json').write_text(json.dumps(index, sort_keys=True, allow_nan=False))
                if collection['stopped']:
                    break  # Stop only this difficulty; never relax gates.
    index['wall_seconds'] = time.perf_counter()-global_start
    index['worker_evaluation_seconds'] = worker_seconds
    index['stopped'] = any(c['stopped'] for c in index['collections'])
    sample_rng = np.random.default_rng(716)
    chosen = sample_rng.choice(len(index['maps']), size=min(10, len(index['maps'])), replace=False)
    (output/'reports'/'sample_10.json').write_text(json.dumps([index['maps'][int(i)] for i in chosen], sort_keys=True))
    (output/'index.json').write_text(json.dumps(index, sort_keys=True, allow_nan=False))
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--root-head', required=True)
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--mode', choices=['pilot', 'full'], required=True)
    args = parser.parse_args()
    version = {'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'root_head': args.root_head}
    index = run_batch(args.output, json.loads(Path(args.config).read_text()),
                      mode=args.mode, version=version, workers=args.workers)
    return 1 if index['stopped'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
