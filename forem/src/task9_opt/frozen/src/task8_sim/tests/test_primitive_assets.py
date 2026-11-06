"""task8.10 primitive asset import: validation, mapgen objects/parts rule, domain statistics."""
import copy
import json
import math
from pathlib import Path
import numpy as np
import pytest
from task8_sim.assets import sha256_file
from task8_sim.primitive_assets import (
    PrimitiveAssetError, PrimitiveObjectsMismatch, asset_from_boxes, boxes_sha256, compare_objects_to_boxes,
    domain_report, expand_objects, fixture_boxes_to_corner, load_primitive_asset, validate_boxes)

ROOT = Path(__file__).resolve().parents[3]
SEMANTIC = ROOT / 'results/task8/t8-exec-20261026/semantic-pool'
FIXTURES = ROOT / 'results/task8/t8-exec-20261026/cube-pool'
UNIT = [0, 0, 0, 1, 1, 1, 1, 0]


@pytest.mark.parametrize('rows,match', [
    ([[float('nan'), 0, 0, 1, 1, 1, 1, 0]], 'finite'),
    ([[0, 0, 0, 0, 1, 1, 1, 0]], 'size'),
    ([[0, 0, 0, 1, -1, 1, 1, 0]], 'size'),
    ([[0, 0, 0, 1, 1, 1, 1.01, 0]], 'cos'),
    ([[0, 0, -0.1, 1, 1, 1, 1, 0]], 'z < 0'),
    ([[0, 0, 0, 1, 1, 1, 1]], r'\[N,8\]'),
    ([], r'\[N,8\]'),
])
def test_validate_boxes_rejects(rows, match):
    with pytest.raises(PrimitiveAssetError, match=match):
        validate_boxes(rows, map_id='bad')


def test_validate_boxes_accepts_rotation_within_1e6_and_empty_when_allowed():
    ok = [[0, 0, 0, 1, 1, 1, 1 + 4e-7, 0]]
    assert validate_boxes(ok).shape == (1, 8)
    assert validate_boxes([], allow_empty=True).shape == (0, 8)


def test_fixture_center_yaw_converts_to_min_corner():
    # centre (2,0,.5), size 1, yaw 45deg about the centre -> corner is the rotated (-.5,-.5) offset
    row = fixture_boxes_to_corner([{'center': [2, 0, .5], 'size': [1, 1, 1], 'yaw': math.pi / 4}])[0]
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    assert row[6] == pytest.approx(c) and row[7] == pytest.approx(s)
    centre = row[:2] + np.array([[c, -s], [s, c]]) @ row[3:5] / 2
    assert np.allclose(centre, [2, 0], atol=1e-15) and row[2] == 0.0


def test_expand_objects_follows_mapgen_part_rule():
    objects = [
        {'name': 'cuboid', 'position': [1, 2, 0], 'theta': 0.3, 'size': [.5, .6, .7]},
        {'name': 'composite', 'position': [1, 2, .1], 'theta': math.pi / 2,
         'parts': [{'name': 'a', 'offset': [.5, .2, .3], 'size': [.1, .2, .3], 'theta': .1},
                   {'name': 'b', 'offset': [0, 0, 0], 'size': [1, 1, 1]}]},
    ]
    rows, sources, _ = expand_objects(objects)
    assert rows.shape == (3, 8) and sources == [(0, None), (1, 0), (1, 1)]
    assert np.allclose(rows[0], [1, 2, 0, .5, .6, .7, math.cos(.3), math.sin(.3)], atol=1e-15)
    # part a: xy = (1,2) + R(pi/2)@(.5,.2) = (1-.2, 2+.5); theta = pi/2+.1
    th = math.pi / 2 + .1
    assert np.allclose(rows[1], [.8, 2.5, .4, .1, .2, .3, math.cos(th), math.sin(th)], atol=1e-15)
    assert np.allclose(rows[2][:3], [1, 2, .1]) and rows[2][6] == pytest.approx(math.cos(math.pi / 2))


def test_compare_objects_reports_worst_box_and_never_repairs():
    objects = [{'position': [0, 0, 0], 'theta': 0., 'size': [1, 1, 1]}, {'position': [3, 0, 0], 'theta': 0., 'size': [1, 1, 1]}]
    boxes = np.array([UNIT, [3, 0, 0, 1, 1, 1, 1, 0]], dtype=float)
    ok, _ = compare_objects_to_boxes(objects, boxes, map_id='m')
    assert ok['consistent'] and ok['max_abs_diff'] == 0
    boxes[1, 0] += 1e-6
    bad, _ = compare_objects_to_boxes(objects, boxes, map_id='m')
    assert not bad['consistent'] and bad['worst_box_index'] == 1 and bad['reason'] == 'value_mismatch'
    short, _ = compare_objects_to_boxes(objects, boxes[:1], map_id='m')
    assert not short['consistent'] and short['reason'] == 'count_mismatch'


def _manifest(tmp_path, data, *, entry_extra=None, name='m0'):
    side = tmp_path / f'{name}.json'
    side.write_text(json.dumps(data))
    entry = dict(id=name, pcd_path=f'{name}.pcd', sidecar_path=f'{name}.json', sha256={'pcd': '0' * 64, 'sidecar': sha256_file(side)},
                 frame_id='world', length_unit='m', resolution_m=.05, semantic_policy_input=False,
                 bounds={'min': [-5, -5, 0], 'max': [5, 5, 1.6], 'upper_exclusive': True})
    entry.update(entry_extra or {})
    manifest = tmp_path / 'manifest.json'
    from task8_sim import primitive_assets
    primitive_assets._DOCS.clear()      # test rewrites one path within a filesystem timestamp tick
    manifest.write_text(json.dumps({'schema_version': 'task8-pcd-v1', 'maps': [entry]}))
    return manifest


def test_loader_reads_json_boxes_never_the_pcd(tmp_path):
    manifest = _manifest(tmp_path, {'boxes': [UNIT], 'box_metadata': [{'category': 'wall'}]})
    asset = load_primitive_asset(manifest, 'm0')    # the .pcd named in the manifest does not exist
    assert asset.boxes.shape == (1, 8) and asset.categories == ('wall',)
    assert asset.declared_pcd_sha256 == '0' * 64 and 'pcd' not in asset.hashes
    assert asset.hashes['boxes'] == boxes_sha256(asset.boxes) and asset.hashes['sidecar'] == sha256_file(tmp_path / 'm0.json')
    assert not asset.boxes.flags.writeable


def test_loader_rejects_sidecar_hash_mismatch_and_unsupported_containers(tmp_path):
    manifest = _manifest(tmp_path, {'boxes': [UNIT]})
    (tmp_path / 'm0.json').write_text(json.dumps({'boxes': [UNIT], 'x': 1}))
    with pytest.raises(PrimitiveAssetError, match='hash mismatch'):
        load_primitive_asset(manifest, 'm0')
    manifest = _manifest(tmp_path, {'boxes': [UNIT], 'cylinders': []}, name='m1')
    with pytest.raises(PrimitiveAssetError, match='unsupported primitive'):
        load_primitive_asset(manifest, 'm1')
    with pytest.raises(PrimitiveAssetError, match='expected one manifest entry'):
        load_primitive_asset(manifest, 'absent')


def test_loader_stops_on_objects_boxes_mismatch(tmp_path):
    objects = [{'name': 'o', 'position': [0, 0, 0], 'theta': 0., 'size': [1, 1, 1]}]
    manifest = _manifest(tmp_path, {'boxes': [[0, 0, 0, 1, 1, 1.001, 1, 0]], 'objects': objects})
    with pytest.raises(PrimitiveObjectsMismatch, match='never repaired') as info:
        load_primitive_asset(manifest, 'm0')
    assert info.value.report['worst_box_index'] == 0 and info.value.report['max_abs_diff'] == pytest.approx(.001)
    relaxed = load_primitive_asset(manifest, 'm0', strict_objects=False)   # diagnostic-only mode; boxes remain the truth
    assert relaxed.objects_check['consistent'] is False and relaxed.boxes[0, 5] == pytest.approx(1.001)


def test_domain_report_counts_excess_without_clipping():
    boxes = np.array([UNIT,
                      [4.9, 0, 0, .5, 1, 1, 1, 0],      # x to 5.4: excess .4
                      [5.0, 0, 0, 1, 1, 1, 1, 0],       # starts on the upper plane: fully outside
                      [4.0, 0, 0, 1, 1, 1, 1, 0],       # reaches plane exactly: not excess
                      [0, 0, 1.5, 1, 1, .3, 1, 0]])      # z to 1.8: excess .2
    report = domain_report(boxes)
    assert report['out_of_domain_box_count'] == 3 and report['fully_outside_box_count'] == 1
    assert report['max_out_of_domain_m'] == pytest.approx(1.0)
    assert report['reaches_upper_plane_box_count'] == 4
    assert domain_report(np.empty((0, 8)))['box_count'] == 0


def test_asset_from_boxes_adds_hash_and_categories():
    asset = asset_from_boxes('mem', [UNIT, UNIT], categories=['a', 'b'])
    assert asset.categories == ('a', 'b') and asset.hashes['boxes'] == boxes_sha256(np.array([UNIT, UNIT], float))
    with pytest.raises(PrimitiveAssetError):
        asset_from_boxes('mem', [UNIT], categories=['a', 'b'])


@pytest.mark.skipif(not (SEMANTIC / 'index.json').exists(), reason='semantic pool absent')
def test_all_24_semantic_maps_objects_parts_equal_boxes():
    maps = json.loads((SEMANTIC / 'index.json').read_text())['maps']
    assert len(maps) == 24
    total = 0
    for entry in maps:
        asset = load_primitive_asset(SEMANTIC, entry['id'])     # strict: raises PrimitiveObjectsMismatch otherwise
        check = asset.objects_check
        assert check['consistent'] and check['max_abs_diff'] <= 1e-9 and check['expanded_box_count'] == check['box_count']
        assert len(asset.categories) == len(asset.boxes)
        total += len(asset.boxes)
    assert total == 2848


@pytest.mark.skipif(not (FIXTURES / 'manifest.json').exists(), reason='8.1 fixtures absent')
def test_fixture_manifest_assets_load_from_fixture_boxes_only():
    maps = json.loads((FIXTURES / 'manifest.json').read_text())['maps']
    counts = {}
    for entry in maps:
        asset = load_primitive_asset(FIXTURES, entry['id'])
        assert asset.source['kind'] == 'manifest-fixture-boxes'
        counts[entry['id']] = len(asset.boxes)
    assert counts == dict(empty=0, axis_aligned=1, rotated=1, occlusion=2, boundary=1, floating_slab=1, random_cubes=4)
    boundary = load_primitive_asset(FIXTURES, 'boundary')
    assert boundary.domain['out_of_domain_box_count'] == 0 and boundary.domain['reaches_upper_plane_box_count'] == 1
