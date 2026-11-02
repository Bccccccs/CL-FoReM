"""Geometric contract fixtures; map acceptance protocol is still pending."""
import json
import math

import numpy as np
import pytest

from task7_sim.mapgen_a import (
    canonical_walls, corners, geometry_report, generate_candidate,
    distance_transform, skeletonize, connectivity_ratio, check_map,
    run_batch, preview_rgb,
)


def scene(*obstacles):
    return {'boxes': canonical_walls() + list(obstacles)}


def test_rotation_is_about_corner_not_centre():
    np.testing.assert_allclose(corners([1, 2, 0, 2, 1, 1, 0, 1]),
                               [[1, 2], [1, 4], [0, 4], [0, 2]])


def test_walls_serialized_once_and_reader_round_trip(tmp_path):
    from task7_sim.geometry import load_map
    data = scene([1, 1, 0, 1, .5, .4, 0, 1])
    path = tmp_path / 'map.json'
    path.write_text(json.dumps(data))
    loaded = load_map(path)
    assert loaded.shape == (5, 8)
    np.testing.assert_allclose(loaded[-1, :6].numpy(), [.75, 1.5, .2, .5, .25, .2])
    assert geometry_report(data)['geometry_valid']


@pytest.mark.parametrize('box,reason', [
    ([4.7, 1, 0, 1, 1, 1, 1, 0], 'out_of_bounds'),
    ([0, 0, 0, .1, .1, .1, 1, 0], 'origin_clearance'),
    ([-1, -.1, 0, 2, .2, .2, 1, 0], 'origin_clearance'),
    ([1, 1, 0, .099, 1, 1, 1, 0], 'minimum_size'),
    ([1, 1, 0, 1, 1, 1.61, 1, 0], 'out_of_bounds'),
    ([1, 1, 0, 1, 1, 1, 2, 0], 'rotation'),
    ([1, 1, 0, float('nan'), 1, 1, 1, 0], 'nonfinite'),
])
def test_rejects_geometry_without_clipping_or_repair(box, reason):
    data = scene(box)
    before = json.dumps(data)
    report = geometry_report(data)
    assert not report['geometry_valid']
    assert reason in report['reasons']
    assert json.dumps(data) == before


def test_overlap_and_wall_collision_rejected():
    assert 'overlap' in geometry_report(scene(
        [1, 1, 0, 1, 1, .2, 1, 0], [1.5, 1.5, 0, 1, 1, .2, 1, 0]))['reasons']
    assert 'overlap' in geometry_report(scene(
        [4.8, 1, 0, .1, 1, .2, 1, 0]))['reasons']


def test_sat_does_not_reject_separated_parallel_diagonal_rectangles():
    c = math.sqrt(.5)
    report = geometry_report(scene(
        [1, 1, 0, 1.5, .1, .4, c, c],
        [1, 1.5, 0, 1.5, .1, .4, c, c]))
    assert report['geometry_valid']


def test_missing_wall_not_silently_fixed_by_report():
    report = geometry_report({'boxes': canonical_walls()[:3]})
    assert not report['geometry_valid']
    assert 'walls' in report['reasons']


def test_height_counts_and_areas_exclude_walls():
    report = geometry_report(scene(
        [1, 1, 0, 1, 1, .2, 1, 0],
        [-3, 1, 0, 2, 1, .8, 1, 0],
        [1, -3, 0, 1, 2, 1.4, 1, 0]))
    assert report['geometry_valid']
    assert report['height_layers'] == {
        'base_only': {'count': 1, 'area_m2': 1.},
        'arm_band': {'count': 1, 'area_m2': 2.},
        'full_height': {'count': 1, 'area_m2': 2.},
        'outside_sampling_bands': {'count': 0, 'area_m2': 0.},
    }


def test_seed_repeatable_and_no_global_rng_side_effect():
    params = dict(grid_spacing=3., grid_origin=(-3., -3.),
                  generator_version={'source_sha256': 'test-fixture', 'root_head': 'test-fixture'})
    np.random.seed(41)
    state = np.random.get_state()
    first = generate_candidate(20, **params)
    second = generate_candidate(20, **params)
    assert json.dumps(first, sort_keys=True, allow_nan=False) == json.dumps(second, sort_keys=True, allow_nan=False)
    after = np.random.get_state()
    assert state[0] == after[0] and np.array_equal(state[1], after[1]) and state[2:] == after[2:]
    assert first != generate_candidate(21, **params)
    assert first['boxes'][:4] == canonical_walls()
    assert [m['category'] for m in first['box_metadata'][:4]] == ['wall'] * 4
    assert len(first['boxes']) == len(first['box_metadata'])
    assert first['metadata']['acceptance'] == 'geometry_only'
    assert first['metadata']['parameters']['grid_origin'] == [-3., -3.]
    assert first['metadata']['generator_version'] == params['generator_version']
    assert first['checks'] == geometry_report(first)


@pytest.mark.parametrize('kwargs', [dict(grid_spacing=0), dict(grid_spacing=2.),
                                  dict(grid_origin=(float('nan'), 0))])
def test_invalid_sampling_parameters_rejected(kwargs):
    params = dict(grid_spacing=3., grid_origin=(-3., -3.),
                  generator_version={'source_sha256': 'fixture', 'root_head': 'fixture'})
    params.update(kwargs)
    with pytest.raises(ValueError):
        generate_candidate(1, **params)


def test_exact_euclidean_transform_on_small_mask():
    occupied = np.zeros((5, 5), dtype=bool)
    occupied[1, 1] = True
    got = distance_transform(occupied, resolution=.05)
    assert got[1, 1] == 0
    assert got[4, 1] == pytest.approx(.15)
    assert got[4, 4] == pytest.approx(math.sqrt(18) * .05)


def test_connectivity_four_neighbors_and_empty_grid():
    assert connectivity_ratio(np.eye(3, dtype=bool)) == pytest.approx(1 / 3)
    assert connectivity_ratio(np.ones((4, 4), dtype=bool)) == 1.
    assert connectivity_ratio(np.zeros((4, 4), dtype=bool)) == 0.


def test_thinning_retains_line_and_erases_no_empty_pixels():
    line = np.zeros((9, 9), dtype=bool)
    line[4, 2:7] = True
    np.testing.assert_array_equal(skeletonize(line), line)
    thick = np.zeros((11, 11), dtype=bool)
    thick[3:8, 2:9] = True
    thin = skeletonize(thick)
    assert thin.any() and thin.sum() < thick.sum() and not (thin & ~thick).any()
    assert connectivity_ratio(thin) == 1.


def test_grid_report_and_no_turning_or_channel_rejection():
    result = check_map(scene())
    assert result['accepted']
    assert result['connectivity_ratio'] == 1.
    assert result['turning_fraction'] > .3
    assert result['channel_width_m']['count'] > 0


def test_preview_uses_json_geometry_and_height_color():
    data = scene([1, 1, 0, 1, 1, .2, 1, 0])
    data['box_metadata'] = [{'category': 'wall'} for _ in range(4)] + [{'category': 'base_only'}]
    rgb = preview_rgb(data)
    assert rgb.shape == (200, 200, 3)
    assert rgb[0, 100].tolist() == [40, 40, 40]
    assert rgb[100, 100].tolist() == [255, 255, 255]
    assert rgb[70, 130].tolist() == [55, 145, 230]


def test_batch_rejects_overlapping_seed_ranges_before_creating_output(tmp_path):
    config = {'counts': dict(pilot=1, train=1, validation=1, test=1),
              'seed_ranges': {d: {s: [0, 9] for s in ('pilot', 'train', 'validation', 'test')}
                              for d in ('sparse', 'standard')}}
    with pytest.raises(ValueError, match='seed'):
        run_batch(tmp_path/'maps', config, mode='pilot', version={}, workers=1)
    assert not (tmp_path/'maps').exists()
