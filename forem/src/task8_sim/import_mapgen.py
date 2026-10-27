"""Lossless mapgen import; sidecar boxes are audit references, never geometry.

Protocol / diagnostic engineering choices: task8.5 PROCEDURE, SRC-0987.
Corner OBB convention audited in mapgen/mapgen/map_builder.py:_voxelize_box.
"""
import json
from pathlib import Path
import shutil
import time
import numpy as np
from .assets import load_asset, sha256_file

BOUNDS = {'min': [-5,-5,0], 'max': [5,5,1.6], 'upper_exclusive': True}
TOL = 1e-6  # diagnostic only; does not alter asset parsing or voxelization


def geometry_diagnostic(xyz, side):
    covered = np.zeros(len(xyz), dtype=bool)
    strict_covered = covered.copy()
    records, valid_boxes = [], []
    for i, raw in enumerate(side.get('boxes', [])):
        record = {'box_index': i}
        try:
            b = np.asarray(raw, dtype=np.float64)
            if b.shape != (8,) or not np.isfinite(b).all() or np.any(b[3:6] <= 0):
                raise ValueError('expected finite corner/positive-size/cos/sin 8-vector')
            if not np.isclose(b[6]**2+b[7]**2, 1, atol=1e-8, rtol=0):
                raise ValueError('non-unit rotation')
            delta = xyz-b[:3]
            local = np.column_stack((delta[:,0]*b[6]+delta[:,1]*b[7],
                                     -delta[:,0]*b[7]+delta[:,1]*b[6], delta[:,2]))
            strict = ((local >= 0) & (local <= b[3:6])).all(axis=1)
            inside = ((local >= -TOL) & (local <= b[3:6]+TOL)).all(axis=1)
            strict_covered |= strict
            covered |= inside
            corners = np.asarray([[x,y,z] for x in (0,b[3]) for y in (0,b[4]) for z in (0,b[5])])
            corners[:,:2] = corners[:,:2] @ np.array([[b[6],b[7]],[-b[7],b[6]]])
            corners += b[:3]
            record.update(point_count=int(inside.sum()), strict_point_count=int(strict.sum()),
                          rotated=bool(abs(b[7]) > 1e-8),
                          touches_or_crosses_data_boundary=bool(np.any((corners <= BOUNDS['min']) | (corners >= BOUNDS['max']))))
            valid_boxes.append((i,b))
        except (ValueError, TypeError) as exc:
            record['error'] = str(exc)
        records.append(record)
    mappings = []
    for i, obj in enumerate(side.get('objects', [])):
        matches = []
        try:
            # Composite objects have no asserted one-box mapping, even if their envelope matches.
            if not isinstance(obj, dict) or obj.get('parts'):
                raise ValueError('no single primitive correspondence')
            theta = float(obj['theta'])
            signature = np.array([*obj['position'], *obj['size'], np.cos(theta), np.sin(theta)])
            if signature.shape != (8,) or not np.isfinite(signature).all():
                raise ValueError('invalid object geometry')
            matches = [j for j,b in valid_boxes if np.allclose(signature, b, atol=1e-10, rtol=0)]
        except (KeyError, ValueError, TypeError):
            pass
        mappings.append({'object_index': i, 'name': obj.get('name') if isinstance(obj, dict) else None,
                         'status': 'unique_box' if len(matches)==1 else 'ambiguous' if matches else 'unknown',
                         'box_indices': matches})
    return ({'box_convention': 'corner_xyz_size_xyz_cos_sin', 'rounding_tolerance_m': TOL,
             'outside_declared_boxes_count': int((~covered).sum()),
             'strict_outside_declared_boxes_count': int((~strict_covered).sum()),
             'empty_box_indices': [r['box_index'] for r in records if r.get('point_count') == 0],
             'boxes': records, 'geometry_repaired': False,
             'interpretation_limit': 'Differences may reflect historical generation/filtering, rotation, clipping or rounding; no cause inferred from counts.'}, mappings)


def import_pool(source_dir, output_dir):
    source, output = Path(source_dir).resolve(), Path(output_dir).resolve()
    if source == output or source in output.parents:
        raise ValueError('output must be outside source directory')
    output.mkdir(parents=True, exist_ok=False)
    manifest = {'schema_version': 'task8-pcd-v1', 'cache_backend_version': 'pcd-voxel-v3', 'maps': []}
    report = {'ok': False, 'source_directory': str(source), 'maps': [], 'runtime_validation': 'not_run'}
    stems = sorted({p.stem for suffix in ('*.pcd','*.json') for p in source.glob(suffix)})
    for stem in stems:
        start = time.monotonic()
        record = {'id': stem, 'status': 'load_failed'}
        try:
            paths = {'pcd':source/(stem+'.pcd'), 'sidecar':source/(stem+'.json')}
            hashes = {kind:sha256_file(path) for kind,path in paths.items()}
            record['sha256'] = hashes
            side = json.loads(paths['sidecar'].read_text())
            if not isinstance(side, dict):
                raise ValueError('sidecar must be a JSON object')
            for key, expected in {'frame_id':'world','length_unit':'m','resolution':.05,
                                  'map_size':[10,10,1.6], 'point_representation':'solid_volume_samples',
                                  'point_bounds':BOUNDS}.items():
                if key in side and side[key] != expected:
                    raise ValueError(f'incompatible sidecar {key}')
            category = stem.rsplit('_map_',1)[0]
            if category not in ('home','hospital','laboratory','library','office','restaurant','warehouse','workshop'):
                raise ValueError('unrecognized source filename category')
            entry = dict(id=stem, pcd_path=stem+'.pcd', sidecar_path=stem+'.json', sha256=hashes,
                         frame_id='world', length_unit='m', resolution_m=.05,
                         point_representation='solid_volume_samples', geometry_backend='pcd-voxel-v3',
                         bounds=BOUNDS, semantic_policy_input=False, split='smoke', difficulty=category,
                         difficulty_basis='source_filename_category_not_calibrated_difficulty',
                         source_paths={k:str(p) for k,p in paths.items()})
            for path in paths.values():
                shutil.copyfile(path, output/path.name)
            # Validate through the consumer protocol, including every actual PCD point.
            candidate = output/'candidate.json'
            candidate.write_text(json.dumps({'schema_version':'task8-pcd-v1','maps':[entry]}))
            try:
                asset = load_asset(candidate, stem)
            finally:
                candidate.unlink(missing_ok=True)
            diagnostic, mappings = geometry_diagnostic(asset.xyz, side)
            record.update(status='validated', point_count=len(asset.xyz),
                          duplicate_point_count=len(asset.xyz)-len(np.unique(asset.xyz,axis=0)),
                          actual_bounds={'min':asset.xyz.min(axis=0).tolist(), 'max':asset.xyz.max(axis=0).tolist()},
                          geometry_diagnostic=diagnostic, object_mapping=mappings)
            manifest['maps'].append(entry)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            record['error'] = f'{type(exc).__name__}: {exc}'
        record['elapsed_s'] = time.monotonic()-start
        report['maps'].append(record)
    report['ok'] = bool(stems) and all(m['status']=='validated' for m in report['maps'])
    (output/'index.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (output/'diagnostics.json').write_text(json.dumps(report, indent=2)+'\n')
    return report
