"""Deterministic CPU integration; no sampled train/validation episodes."""
from copy import deepcopy
import time
import torch
from task7_sim.episode import CBL_Q
from task7_sim.kinematics import Kinematics
from task7_sim.motion import Route, matrix_quat
from task7_sim.candidates import CandidateBatch
from task8_sim.episode import PcdEpisode
from task8_sim.primitive_assets import asset_from_boxes
from task8_sim.primitive_scene import PrimitiveScene
from task10.environment import Task10Env


def test_pending_execution_features_cannot_enter_replay():
    import pytest
    from task10.learning import EpisodeReplay
    from task10.tests.test_learning import transition
    row = transition(0, end=True)
    row['next_candidates']['pending'] = True
    replay = EpisodeReplay(10)
    with pytest.raises(ValueError, match='pending'):
        replay.append('a', row)
    assert len(replay) == 0


def test_mixed_reset_preserves_survivor_state_and_candidate_batch(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    manifest = tmp_path/'manifest.json'
    manifest.write_text('{}')
    scene = PrimitiveScene.from_asset(asset_from_boxes('fixture', [], allow_empty=True), device='cpu', dtype=torch.float32)
    def factory(i, rng):
        base = torch.zeros(1, 3)
        base[:, 0] = i*.1
        q = torch.tensor(CBL_Q)[None]
        tcp = Kinematics().world_tcp(base, q)
        xyz = tcp[:, None, :3, 3].repeat(1, 2, 1)
        xyz[:, 1, 0] += .0075
        route = Route(xyz, matrix_quat(tcp[:, :3, :3])[:, None].repeat(1, 2, 1))
        return PcdEpisode(base, q, route, scene, 'fixture', seed=i)
    def generate(local, state, route, kin, synchronous):
        n = len(state.s)
        mask = torch.zeros(n, 13, dtype=torch.bool)
        mask[:, 12] = True
        return CandidateBatch(torch.zeros(n, 13, 3), mask, None, mask.clone(), {})
    monkeypatch.setattr('task7_sim.candidates.generate_candidates', generate)
    def policy(obs):
        return obs['q'].new_tensor([1., 0., 0.]).expand(len(obs['q']), -1)
    env = Task10Env(2, policy, seed=101, pool=manifest, factory=factory, device='cpu')
    obs, candidates = env.reset(deadline=time.monotonic()+20)
    c = env.episodes.core
    before = dict(base=c.state.base[1].clone(), q=c.state.q[1].clone(),
                  s=c.state.s[1].clone(), observed=c.grid.observed[1].clone(),
                  height=c.grid.height[1].clone(), timestamp=c.grid.timestamp[1].clone())
    c.terminated[0] = True
    env.reset(indices=[0], deadline=time.monotonic()+20)
    for key, value in before.items():
        actual = getattr(c.state, key)[1] if key in ('base', 'q', 's') else getattr(c.grid, key)[1]
        assert torch.equal(actual, value)
    for key, value in obs.items():
        if isinstance(value, torch.Tensor):
            assert torch.equal(env.observation[key][1], value[1]), key
        elif isinstance(value, dict):
            for k, v in value.items():
                assert torch.equal(env.observation[key][k][1], v[1]), (key, k)
    for key, value in candidates.items():
        if isinstance(value, torch.Tensor):
            assert torch.equal(env.candidates[key][1], value[1]), key
    assert c.retain_transitions is False
