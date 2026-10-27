"""task8.10 scene-factory wiring: default stays pcd-voxel-v3, primitive backends run the real env chain (CPU, no training)."""
import json
from pathlib import Path
import numpy as np
import pytest
import torch
from task7_sim.core import Candidate
from task7_sim.kinematics import Kinematics
from task7_sim.motion import Route, matrix_quat
from task8_sim.assets import load_asset
from task8_sim.primitive_scene import BACKEND, DIAG_BACKEND, PrimitiveSceneBatch, load_backend_scene
from task8_sim.scene import SceneBatch, VoxelScene

ROOT = Path(__file__).resolve().parents[3]
POOL = ROOT / 'results/task8/t8-exec-20261026/cube-pool'
Q = ROOT / 'results/task7/t7.14-r2-20261021-0000/fixture.json'
pytestmark = pytest.mark.skipif(not (POOL / 'manifest.json').exists(), reason='8.1 fixture pool absent')
F64 = torch.float64


def v3_scene(key):
    return VoxelScene.from_asset(load_asset(POOL / 'manifest.json', key), device='cpu', dtype=F64)


def p_scene(key, backend=BACKEND):
    return load_backend_scene(backend, POOL, key, device='cpu', dtype=F64)


def factory_for(key, backend=BACKEND):
    def factory(i, streams):
        from task8_sim.episode import PcdEpisode
        base = torch.zeros(1, 3, dtype=F64)
        base[:, 0] = float(streams.initial.uniform(-.05, .05))
        q = torch.tensor(json.loads(Q.read_text())['q'], dtype=F64)[None]
        tcp = Kinematics().world_tcp(base, q)
        xyz = tcp[:, None, :3, 3].expand(-1, 2, -1).clone(); xyz[:, 1, 0] += .0075
        route = Route(xyz, matrix_quat(tcp[:, :3, :3])[:, None].expand(-1, 2, -1).clone())
        return PcdEpisode(base, q, route, p_scene(key, backend), key, seed=123 + i)
    return factory


def test_grid_aligned_fixtures_agree_exactly_with_v3_on_rays():
    rng = np.random.default_rng(4)
    for key in ('axis_aligned', 'occlusion', 'floating_slab'):
        p, v = p_scene(key), v3_scene(key)
        o = torch.tensor(np.c_[np.full(300, -2.), rng.uniform(-.45, .45, 300), rng.uniform(.03, .97, 300)])[None]
        d = torch.tensor(np.c_[np.ones(300), np.zeros(300), np.zeros(300)])[None]
        a, b = p.raycast(o, d, max_range=6.), v.raycast(o, d, max_range=6.)
        assert torch.equal(torch.isfinite(a), torch.isfinite(b))
        assert torch.isfinite(a).any() == (key != 'floating_slab')
        if torch.isfinite(a).any():
            assert (a - b)[torch.isfinite(a)].abs().max() <= 1e-12


def test_rotated_fixture_differs_from_v3_only_by_discretisation_layer():
    p, v = p_scene('rotated'), v3_scene('rotated')
    o = torch.tensor(np.c_[np.full(200, -2.), np.linspace(-.6, .6, 200), np.full(200, .5)])[None]
    d = torch.tensor(np.c_[np.ones(200), np.zeros(200), np.zeros(200)])[None]
    a, b = p.raycast(o, d, max_range=6.)[0], v.raycast(o, d, max_range=6.)[0]
    both = torch.isfinite(a) & torch.isfinite(b)
    assert both.sum() > 100 and (a[both] - b[both]).abs().max() < .1          # a few voxels at most: analytic vs PCD voxel union


def test_primitive_and_diag_scenes_share_facade_with_batch_factory():
    p, pv = p_scene('random_cubes'), p_scene('random_cubes', DIAG_BACKEND)
    assert p.provenance()['map_id'] == 'random_cubes' and pv.provenance()['backend'] == DIAG_BACKEND
    assert torch.equal(p.occupancy, pv.occupancy) and p.provenance()['primitive_count'] == 4
    from task8_sim.primitive_scene import make_scene_batch
    assert isinstance(make_scene_batch([p, p]), PrimitiveSceneBatch) and type(make_scene_batch([pv])) is SceneBatch


def test_sampler_default_backend_v3_and_unknown_backend_rejected():
    from task8_sim.episode import PcdEpisodeSampler
    kw = dict(split='smoke', difficulty='axis_aligned', device='cpu', dtype=F64, kin=None, robot=None, profile='sync_v5')
    assert PcdEpisodeSampler(POOL, **kw).map_backend == 'pcd-voxel-v3'
    assert PcdEpisodeSampler(POOL, map_backend=BACKEND, **kw).map_backend == BACKEND
    with pytest.raises(ValueError, match='map_backend'):
        PcdEpisodeSampler(POOL, map_backend='primitive-obb-v2', **kw)


def test_env_chain_with_primitive_scenes_reset_step_scan_and_versions():
    from task8_sim.env import PcdEpisodeEnv
    env = PcdEpisodeEnv(1, seed=1, pool=POOL, profile='sync_v5', factory=factory_for('axis_aligned'), device='cpu', dtype=F64, map_backend=BACKEND)
    env.reset(); c = env.core
    assert isinstance(env.scenes, PrimitiveSceneBatch)
    assert env.versions['map_backend'] == BACKEND and env.versions['environment'] == 'task8-prim-v1'
    # the 360x90 ghost scan from the reset pose must have landed on the grid (sensor sees the box)
    assert c.grid.observed.any() and c.grid.timestamp.item() == 0
    before, frames = c.state.clone(), c.sensor_frames.clone()
    env.begin(Candidate(c.state.base.clone(), c.route.length.clone(), torch.ones_like(c.done)))
    out = env.step(c.state.base.new_tensor([[0., 0., 1.]]))
    assert out.transition.committed.item() > 0 and not torch.equal(c.state.q, before.q)
    assert c.sensor_frames.item() == frames.item() + 1 and c.grid.timestamp.item() > 0
    assert not hasattr(c.collision, 'boxes') and not hasattr(c.renderer, 'boxes')


def test_env_default_still_v3_scene_batch_and_version_string():
    from task8_sim.env import PcdEpisodeEnv

    def v3_factory(i, streams):
        from task8_sim.episode import PcdEpisode
        e = factory_for('axis_aligned')(i, streams)
        return PcdEpisode(e.base, e.q, e.route, v3_scene('axis_aligned'), 'axis_aligned', seed=e.seed)
    env = PcdEpisodeEnv(1, seed=1, pool=POOL, profile='sync_v5', factory=v3_factory, device='cpu', dtype=F64)
    env.reset()
    assert type(env.scenes) is SceneBatch and env.versions['map_backend'] == 'pcd-voxel-v3' and env.versions['environment'] == 'task8-pcd-v3'


def test_panorama_primitive_vs_v3_aligned_fixture_same_depth():
    from task8_sim.perception import PcdPanorama
    sensor = json.loads((ROOT / 'config/task8/sensor.json').read_text())
    base = torch.tensor([[0., 0., 0.]], dtype=F64); caps = torch.empty(1, 0, 7, dtype=F64)
    a = PcdPanorama(PrimitiveSceneBatch([p_scene('occlusion')]), sensor_config=sensor)(base, caps)
    b = PcdPanorama(SceneBatch([v3_scene('occlusion')]), sensor_config=sensor)(base, caps)
    assert torch.equal(a.valid, b.valid)
    assert (a.distance - b.distance)[a.valid].abs().max() < 1e-9
