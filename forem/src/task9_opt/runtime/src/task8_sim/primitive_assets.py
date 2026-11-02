"""JSON primitive assets for task8.10 primitive-obb-v1 (SRC-1181 / SRC-1220).

The JSON ``boxes`` (semantic pool sidecars, cube-pool sidecars) or the 8.1
``fixture_boxes`` are the only geometric truth read here. The PCD is never
opened or hash-checked: it is a derived/visualisation artefact (task8.10 TASK).

Box row layout, task7 ``load_map`` / mapgen ``save_boxes_json`` convention:
``[x, y, z, sx, sy, sz, cos(theta), sin(theta)]`` where ``(x, y, z)`` is the
*minimum corner* of the local frame and the box is rotated by ``theta`` about
that corner (x then y local axes), i.e. ``world = corner + R(theta) @ local``.

``objects``/``parts`` expansion rule (semantic maps) was read from the mapgen
bytecode ``mapgen/mapgen/__pycache__/map_builder.cpython-314.pyc`` (source
``.../mapgen/mapgen/map_builder.py`` is absent from the repository; the line
numbers below are the pyc line table):
  * ``_expand_object_with_sources`` L119-156 (and ``_expand_obstacle_boxes``
    L89-116): an object without ``parts`` yields one box
    ``position, size, theta``; with ``parts`` each part yields
    ``xy = position[:2] + R(theta_obj) @ offset[:2]``, ``z = position[2] +
    offset[2]``, ``size = part.size``, ``theta = theta_obj + part.get('theta', 0)``
    with ``R = [[cos, -sin], [sin, cos]]`` (numpy);
  * rows are serialised as ``[x, y, z, sx, sy, sz, cos(theta), sin(theta)]``
    (``serialize_final_boxes`` L239; ``save_boxes_json`` L391).
"""
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from .assets import sha256_file

BACKEND = 'primitive-obb-v1'
DOMAIN_MIN = np.array([-5., -5., 0.])
DOMAIN_MAX = np.array([5., 5., 1.6])
ROTATION_TOLERANCE = 1e-6      # task7 load_map P1 (SRC-0425)
OBJECTS_BOXES_TOLERANCE = 1e-9  # PROCEDURE A gate, metres
SCHEMA = 'task8-pcd-v1'


class PrimitiveAssetError(ValueError):
    """Import error (unknown type, invalid number, bad hash, ...)."""


class PrimitiveObjectsMismatch(PrimitiveAssetError):
    """objects/parts expansion disagrees with ``boxes``; stop, never repair."""

    def __init__(self, message, report):
        super().__init__(message)
        self.report = report


@dataclass(frozen=True)
class PrimitiveAsset:
    map_id: str
    boxes: np.ndarray                 # [N,8] float64, immutable
    metadata: dict
    hashes: dict                      # sidecar (file bytes) / boxes (array bytes); no PCD
    source: dict
    categories: tuple                 # per-box category (str|None), len N
    domain: dict
    objects_check: dict | None = None
    declared_pcd_sha256: str | None = None   # manifest claim only, never read or verified here


def _immutable(array):
    array = np.ascontiguousarray(array, dtype=np.float64)
    return np.frombuffer(array.tobytes(), dtype=np.float64).reshape(array.shape)


def boxes_sha256(boxes):
    return hashlib.sha256(np.ascontiguousarray(boxes, dtype=np.float64).tobytes()).hexdigest()


def validate_boxes(boxes, *, map_id='<memory>', rotation_tolerance=ROTATION_TOLERANCE, allow_empty=False):
    """Finite, size>0, unit rotation, z>=0; ``type`` fields other than box are rejected upstream."""
    try:
        array = np.asarray(boxes, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise PrimitiveAssetError(f'{map_id}: boxes not numeric: {exc}') from exc
    if array.size == 0 and allow_empty:
        return np.empty((0, 8), dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 8 or len(array) == 0:
        raise PrimitiveAssetError(f'{map_id}: boxes must be a nonempty [N,8] array, got {array.shape}')
    bad = ~np.isfinite(array).all(axis=1)
    if bad.any():
        raise PrimitiveAssetError(f'{map_id}: box {int(np.flatnonzero(bad)[0])} not finite')
    bad = (array[:, 3:6] <= 0).any(axis=1)
    if bad.any():
        raise PrimitiveAssetError(f'{map_id}: box {int(np.flatnonzero(bad)[0])} size must be > 0')
    bad = np.abs(array[:, 6] ** 2 + array[:, 7] ** 2 - 1) > rotation_tolerance
    if bad.any():
        raise PrimitiveAssetError(f'{map_id}: box {int(np.flatnonzero(bad)[0])} |cos^2+sin^2-1| > {rotation_tolerance}')
    bad = array[:, 2] < 0
    if bad.any():
        raise PrimitiveAssetError(f'{map_id}: box {int(np.flatnonzero(bad)[0])} corner z < 0')
    return array


def fixture_boxes_to_corner(fixture_boxes, *, map_id='<fixture>'):
    """8.1 fixtures: centre/size/yaw (yaw about the centre) -> corner rows."""
    rows = []
    for i, box in enumerate(fixture_boxes):
        try:
            centre = np.asarray(box['center'], dtype=np.float64)
            size = np.asarray(box['size'], dtype=np.float64)
            yaw = float(box['yaw'])
        except (KeyError, TypeError, ValueError) as exc:
            raise PrimitiveAssetError(f'{map_id}: fixture box {i} malformed: {exc}') from exc
        if centre.shape != (3,) or size.shape != (3,):
            raise PrimitiveAssetError(f'{map_id}: fixture box {i} center/size shape')
        c, s = math.cos(yaw), math.sin(yaw)
        # corner = centre - R(yaw) @ (size/2) in xy; z corner = centre_z - size_z/2
        x = centre[0] - (c * size[0] / 2 - s * size[1] / 2)
        y = centre[1] - (s * size[0] / 2 + c * size[1] / 2)
        rows.append([x, y, centre[2] - size[2] / 2, size[0], size[1], size[2], c, s])
    return np.asarray(rows, dtype=np.float64).reshape(-1, 8)


def expand_objects(objects, *, map_id='<memory>'):
    """mapgen part-composition rule (see module docstring). Returns rows, sources, categories."""
    rows, sources, categories = [], [], []
    if not isinstance(objects, list):
        raise PrimitiveAssetError(f'{map_id}: objects must be a list')
    for oi, obj in enumerate(objects):
        try:
            position = np.asarray(obj['position'], dtype=np.float64)
            theta = float(obj.get('theta', 0.0))
            category = obj.get('category')
            parts = obj.get('parts')
            if position.shape != (3,):
                raise ValueError('position must have 3 numbers')
            c, s = np.cos(theta), np.sin(theta)
            rotation = np.array([[c, -s], [s, c]])
            if not parts:
                size = [float(v) for v in obj['size']]
                rows.append([*position, *size, np.cos(theta), np.sin(theta)])
                sources.append((oi, None)); categories.append(category)
                continue
            for pi, part in enumerate(parts):
                offset = np.asarray(part['offset'], dtype=np.float64)
                xy = position[:2] + rotation @ offset[:2]
                theta_part = theta + float(part.get('theta', 0.0))
                rows.append([float(xy[0]), float(xy[1]), float(position[2] + offset[2]),
                             *[float(v) for v in part['size']], np.cos(theta_part), np.sin(theta_part)])
                sources.append((oi, pi)); categories.append(category)
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise PrimitiveAssetError(f'{map_id}: object {oi} malformed: {exc!r}') from exc
    return np.asarray(rows, dtype=np.float64).reshape(-1, 8), sources, categories


def compare_objects_to_boxes(objects, boxes, *, map_id='<memory>', tolerance=OBJECTS_BOXES_TOLERANCE):
    """Row-by-row max abs difference between expanded objects and ``boxes``."""
    expanded, sources, categories = expand_objects(objects, map_id=map_id)
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 8)
    report = dict(map_id=map_id, object_count=len(objects), expanded_box_count=len(expanded),
                  box_count=len(boxes), part_box_count=int(sum(1 for _, p in sources if p is not None)),
                  tolerance_m=tolerance, consistent=False, max_abs_diff=None, worst_box_index=None, worst_source=None)
    if len(expanded) != len(boxes):
        report['reason'] = 'count_mismatch'
        return report, categories
    diff = np.abs(expanded - boxes) if len(boxes) else np.zeros((0, 8))
    per_box = diff.max(axis=1) if len(boxes) else np.zeros(0)
    worst = int(per_box.argmax()) if len(boxes) else None
    report.update(max_abs_diff=float(per_box.max()) if len(boxes) else 0.,
                  worst_box_index=worst, worst_source=None if worst is None else dict(zip(('object', 'part'), sources[worst])),
                  consistent=bool(len(boxes) == 0 or per_box.max() <= tolerance))
    if not report['consistent']:
        report['reason'] = 'value_mismatch'
        report['violating_box_indices'] = [int(i) for i in np.flatnonzero(per_box > tolerance)[:50]]
    return report, categories


def domain_report(boxes):
    """Out-of-domain accounting. Boxes are never clipped; touching the plane is not excess."""
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 8)
    n = len(boxes)
    if n == 0:
        return dict(box_count=0, out_of_domain_box_count=0, fully_outside_box_count=0, max_out_of_domain_m=0.,
                    reaches_upper_plane_box_count=0, out_of_domain_boxes=[])
    x, y, z, sx, sy, sz, c, s = boxes.T
    cx = x[:, None] + np.stack([np.zeros(n), sx * c, -sy * s, sx * c - sy * s], 1)
    cy = y[:, None] + np.stack([np.zeros(n), sx * s, sy * c, sx * s + sy * c], 1)
    lo = np.stack([cx.min(1), cy.min(1), z], 1)
    hi = np.stack([cx.max(1), cy.max(1), z + sz], 1)
    below = np.maximum(DOMAIN_MIN - lo, 0).max(1)
    above = np.maximum(hi - DOMAIN_MAX, 0).max(1)
    excess = np.maximum(below, above)
    outside = (hi < DOMAIN_MIN).any(1) | (lo >= DOMAIN_MAX).any(1)
    reaches = (hi >= DOMAIN_MAX).any(1)
    listed = np.flatnonzero(excess > 0)
    return dict(box_count=n, out_of_domain_box_count=int((excess > 0).sum()),
                fully_outside_box_count=int(outside.sum()), max_out_of_domain_m=float(excess.max()),
                reaches_upper_plane_box_count=int(reaches.sum()),
                out_of_domain_boxes=[dict(index=int(i), excess_m=float(excess[i])) for i in listed[:50]])


def manifest_file(path):
    path = Path(path)
    if path.is_dir():
        choices = [p for p in (path / 'manifest.json', path / 'index.json') if p.is_file()]
        if len(choices) != 1:
            raise PrimitiveAssetError('pool requires exactly one manifest.json or index.json')
        path = choices[0]
    if not path.is_file():
        raise PrimitiveAssetError(f'pool manifest missing: {path}')
    return path


def _check_entry(entry, map_id):
    for key, expected in dict(frame_id='world', length_unit='m', resolution_m=.05).items():
        if entry.get(key) != expected:
            raise PrimitiveAssetError(f'{map_id}: invalid {key}: {entry.get(key)!r}')
    if entry.get('semantic_policy_input') is not False:
        raise PrimitiveAssetError(f'{map_id}: semantic_policy_input must be false')
    if entry.get('bounds') != {'min': [-5, -5, 0], 'max': [5, 5, 1.6], 'upper_exclusive': True}:
        raise PrimitiveAssetError(f'{map_id}: invalid bounds; require fixed world half-open domain')


def asset_from_boxes(map_id, boxes, *, metadata=None, hashes=None, categories=None, source=None,
                     allow_empty=False, objects_check=None):
    """In-memory asset (tests, E-gate interventions). Same validation as the loader."""
    array = validate_boxes(boxes, map_id=map_id, allow_empty=allow_empty)
    cats = tuple(categories) if categories is not None else (None,) * len(array)
    if len(cats) != len(array):
        raise PrimitiveAssetError(f'{map_id}: categories length mismatch')
    hashes = dict(hashes or {}); hashes['boxes'] = boxes_sha256(array)
    return PrimitiveAsset(map_id, _immutable(array), dict(metadata or {}), hashes, dict(source or {'kind': 'memory'}),
                          cats, domain_report(array), objects_check)


_DOCS = {}


def pool_document(manifest):
    """Parsed manifest, cached by (path, mtime, size): a 10300-map pool is 50 MB of JSON."""
    manifest = manifest_file(manifest)
    stat = manifest.stat()
    key = (str(manifest.resolve()), stat.st_mtime_ns, stat.st_size)
    if key not in _DOCS:
        _DOCS.clear()
        _DOCS[key] = json.loads(manifest.read_text())
    return manifest, _DOCS[key]


def load_primitive_asset(manifest, map_id, *, strict_objects=True, tolerance=OBJECTS_BOXES_TOLERANCE):
    """Read primitives of one manifest entry from JSON ``boxes`` or ``fixture_boxes``.

    The sidecar bytes are verified against the manifest hash. The PCD is not
    touched: its manifest hash is carried only as ``declared_pcd_sha256``.
    """
    manifest, doc = pool_document(manifest)
    if doc.get('schema_version') != SCHEMA:
        raise PrimitiveAssetError(f'{map_id}: unsupported schema_version')
    matches = [m for m in doc.get('maps', []) if m.get('id') == map_id]
    if len(matches) != 1:
        raise PrimitiveAssetError(f'{map_id}: expected one manifest entry, got {len(matches)}')
    return asset_from_entry(manifest, matches[0], strict_objects=strict_objects, tolerance=tolerance)


def asset_from_entry(manifest, entry, *, strict_objects=True, tolerance=OBJECTS_BOXES_TOLERANCE):
    manifest = Path(manifest)
    entry = dict(entry)
    map_id = entry.get('id')
    _check_entry(entry, map_id)
    declared = (entry.get('sha256') or {}).get('pcd')
    objects_check = None
    categories = None
    semantics = None
    hashes = {}
    if entry.get('sidecar_path') is not None:
        relative = entry['sidecar_path']
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise PrimitiveAssetError(f'{map_id}: sidecar_path must be relative to manifest')
        path = manifest.parent / relative
        expected = (entry.get('sha256') or {}).get('sidecar')
        try:
            actual = sha256_file(path)
        except OSError as exc:
            raise PrimitiveAssetError(f'{map_id}: cannot read sidecar: {exc}') from exc
        if actual != expected:
            raise PrimitiveAssetError(f'{map_id}: sidecar hash mismatch')
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or 'boxes' not in data:
            raise PrimitiveAssetError(f'{map_id}: sidecar must be a JSON object with boxes')
        # v1 supports only box primitives; unknown primitive containers are import errors.
        unsupported = sorted({'primitives', 'shapes', 'cylinders', 'spheres', 'meshes'} & set(data))
        if unsupported:
            raise PrimitiveAssetError(f'{map_id}: unsupported primitive container(s) {unsupported}')
        boxes = validate_boxes(data['boxes'], map_id=map_id, allow_empty=bool(entry.get('allow_empty')))
        hashes['sidecar'] = actual
        source = dict(kind='sidecar-json', path=str(path))
        if isinstance(data.get('objects'), list):
            objects_check, categories = compare_objects_to_boxes(data['objects'], boxes, map_id=map_id, tolerance=tolerance)
            semantics = dict(object_count=len(data['objects']))
            if strict_objects and not objects_check['consistent']:
                raise PrimitiveObjectsMismatch(
                    f"{map_id}: objects/parts expansion != boxes ({objects_check.get('reason')}, "
                    f"max_abs_diff={objects_check['max_abs_diff']}, worst={objects_check['worst_source']}); "
                    'stop: asset is never repaired', objects_check)
            if not objects_check['consistent']:
                categories = None
        elif isinstance(data.get('box_metadata'), list) and len(data['box_metadata']) == len(boxes):
            categories = [m.get('category') for m in data['box_metadata']]
    elif entry.get('fixture_boxes') is not None:
        boxes = fixture_boxes_to_corner(entry['fixture_boxes'], map_id=map_id)
        boxes = validate_boxes(boxes, map_id=map_id, allow_empty=bool(entry.get('fixture') is True and entry.get('allow_empty') is True))
        source = dict(kind='manifest-fixture-boxes', path=str(manifest))
    else:
        raise PrimitiveAssetError(f'{map_id}: entry has neither sidecar_path nor fixture_boxes')
    if categories is not None and len(categories) != len(boxes):
        categories = None
    hashes['boxes'] = boxes_sha256(boxes)
    cats = tuple(categories) if categories is not None else (None,) * len(boxes)
    metadata = {k: v for k, v in entry.items() if k not in ('fixture_boxes', 'per_box_target_counts', 'per_box_numerics', 'production_provenance')}
    return PrimitiveAsset(map_id, _immutable(boxes), metadata, hashes, source, cats, domain_report(boxes),
                          objects_check, declared_pcd_sha256=declared)
