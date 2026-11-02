"""Strict task8 ASCII PCD assets. JSON is retained only as audit metadata.

Bounds and protocol are engineering choices from task8 TASK / SRC-0987.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import numpy as np


@dataclass(frozen=True)
class MapAsset:
    map_id: str
    xyz: np.ndarray
    metadata: dict
    semantics: dict | None
    hashes: dict


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_pcd(path, map_id):
    def fail(line, why):
        raise ValueError(f'{map_id}: PCD line {line}: {why}')
    header = {}
    rows = []
    in_data = False
    for line_no, raw_bytes in enumerate(Path(path).read_bytes().splitlines(), 1):
        try:
            raw = raw_bytes.decode('ascii')
        except UnicodeDecodeError:
            fail(line_no, 'non-ASCII content in ASCII PCD')
        stripped = raw.strip()
        if not stripped or stripped.startswith('#'):
            continue
        words = stripped.split()
        if not in_data:
            key, values = words[0], words[1:]
            if key in header:
                fail(line_no, f'duplicate {key}')
            header[key] = values
            if key == 'DATA':
                if values != ['ascii']:
                    fail(line_no, 'only DATA ascii supported')
                in_data = True
        else:
            if len(words) != 3:
                fail(line_no, 'expected 3 columns')
            try:
                point = [float(x) for x in words]
            except ValueError:
                fail(line_no, 'invalid numeric coordinate')
            if not np.isfinite(point).all():
                fail(line_no, 'coordinates must be finite')
            rows.append(point)
    if not in_data:
        fail(0, 'missing DATA ascii')
    fields = header.get('FIELDS', [])
    if len(fields) != 3 or set(fields) != {'x', 'y', 'z'}:
        fail(0, 'FIELDS must contain x y z exactly once')
    for key, expected in [('VERSION', ['0.7']), ('SIZE', ['4']*3),
                          ('TYPE', ['F']*3), ('COUNT', ['1']*3)]:
        if header.get(key) != expected:
            fail(0, f'unsupported or missing {key}: {header.get(key)}')
    try:
        counts = {k: int(header[k][0]) for k in ('WIDTH', 'HEIGHT', 'POINTS')
                  if len(header[k]) == 1}
        if len(counts) != 3 or counts['WIDTH'] < 0 or counts['HEIGHT'] < 1 or counts['POINTS'] < 0:
            raise ValueError()
    except (KeyError, ValueError, IndexError):
        fail(0, 'invalid WIDTH/HEIGHT/POINTS')
    if counts['WIDTH']*counts['HEIGHT'] != counts['POINTS'] or len(rows) != counts['POINTS']:
        fail(0, f'POINTS mismatch: dimensions={counts}, actual={len(rows)}')
    xyz = np.asarray(rows, dtype=np.float64).reshape(-1, 3)[:, [fields.index(k) for k in ('x','y','z')]]
    # Immutable bytes backing prevents callers from re-enabling ndarray writes.
    return np.frombuffer(xyz.tobytes(), dtype=np.float64).reshape(-1, 3)


def load_asset(manifest_path, map_id):
    manifest_path = Path(manifest_path)
    doc = json.loads(manifest_path.read_text())
    if doc.get('schema_version') != 'task8-pcd-v1':
        raise ValueError(f'{map_id}: unsupported schema_version')
    entries = doc.get('maps', [])
    matches = [m for m in entries if m.get('id') == map_id]
    if len(matches) != 1:
        raise ValueError(f'{map_id}: expected one manifest entry, got {len(matches)}')
    meta = dict(matches[0])
    required = dict(frame_id='world', length_unit='m', resolution_m=.05,
                    point_representation='solid_volume_samples',
                    semantic_policy_input=False)
    for key, expected in required.items():
        value = meta.get(key)
        if value != expected or (key == 'semantic_policy_input' and value is not False):
            raise ValueError(f'{map_id}: invalid {key}: {value!r}')
    # v1/v2/v3 name voxelization, not a changed raw-PCD manifest format.
    # None is a cached scene: every consumer reconstructs using scene.BACKEND.
    if meta.get('geometry_backend') not in ('pcd-voxel-v1','pcd-voxel-v2','pcd-voxel-v3'):
        raise ValueError(f'{map_id}: invalid geometry_backend: {meta.get("geometry_backend")!r}')
    bounds = meta.get('bounds')
    if bounds != {'min': [-5,-5,0], 'max': [5,5,1.6], 'upper_exclusive': True}:
        raise ValueError(f'{map_id}: invalid bounds; require fixed world half-open domain')
    for key in ('split','difficulty'):
        if not isinstance(meta.get(key), str) or not meta[key]:
            raise ValueError(f'{map_id}: missing {key}')
    hashes = meta.get('sha256', {})
    paths = {}
    for kind, key in (('pcd','pcd_path'), ('sidecar','sidecar_path')):
        relative = meta.get(key)
        expected = hashes.get(kind)
        if kind == 'sidecar' and relative is None:
            if expected is not None:
                raise ValueError(f'{map_id}: sidecar hash requires sidecar_path')
            continue
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise ValueError(f'{map_id}: {key} must be relative to manifest')
        path = manifest_path.parent / relative
        if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
            raise ValueError(f'{map_id}: invalid {kind} sha256 hash')
        try:
            actual = sha256_file(path)
        except OSError as exc:
            raise ValueError(f'{map_id}: cannot read {kind}: {exc}') from exc
        if actual != expected:
            raise ValueError(f'{map_id}: {kind} hash mismatch')
        paths[kind] = path
    xyz = _read_pcd(paths['pcd'], map_id)
    if len(xyz) == 0 and not (meta.get('fixture') is True and meta.get('allow_empty') is True):
        raise ValueError(f'{map_id}: empty map requires fixture=true and allow_empty=true')
    invalid = np.any((xyz < np.asarray(bounds['min'])) | (xyz >= np.asarray(bounds['max'])), axis=1)
    if invalid.any():
        raise ValueError(f'{map_id}: point {int(np.flatnonzero(invalid)[0])+1} outside half-open bounds')
    semantics = json.loads(paths['sidecar'].read_text()) if 'sidecar' in paths else None
    if 'sidecar' in paths and not isinstance(semantics, dict):
        raise ValueError(f'{map_id}: sidecar must be a JSON object')
    return MapAsset(map_id, xyz, meta, semantics, dict(hashes))
