"""Synthetic CPU batch8 restoration fixtures; no real collection or GPU budget."""
from copy import deepcopy
from pathlib import Path
from collections import deque
import json
import os
import subprocess
import sys
import time

import numpy as np
import pytest
import torch

from task10.boundary_state import encode, decode, capture_environment
from task10.environment import Task10Env
from task10.learning import EpisodeReplay, Stage1Learner
from task10.recovery import (save_decision_boundary, load_decision_boundary,
    fixture_update, fragment_identity, tree_equal, mismatch_report)
from task10.runtime import Budget, atomic_torch, state_digest
from task10.tests.test_learning import model, transition, adapter
from task7_lower.training import rng_state
from task7_sim.core import Core, State, Candidate
from task7_sim.episode import CBL_Q
from task7_sim.motion import Route, matrix_quat
from task7_sim.routes import PackedRoute
from task7_sim.perception import Grid
from task7_upper.vcm import MemoryEntry
from task8_sim.primitive_assets import PrimitiveAsset
from task8_sim.primitive_scene import PrimitiveScene, PrimitiveSceneBatch
from task8_sim.episode import SceneCollision
from task8_sim.env import profile_options
from task8_sim.perception import PcdPanorama
from task8_sim.routes import PcdTruthPlanner


@pytest.fixture(autouse=True)
def threads():
    old = torch.get_num_threads()
    torch.set_num_threads(2)
    yield
    torch.set_num_threads(old)


def fresh(pool):
    return Task10Env(8, lambda obs: obs['q'].new_zeros(8, 3), seed=101,
        pool=pool, split='train', device='cpu', run_id='synthetic-batch8',
        code_commit='fixture', config_hash='fixture')


def setup_boundary(directory):
    directory = Path(directory)
    pool = directory/'pool.json'
    pool.write_text(json.dumps(dict(schema_version='task8-pcd-v1', maps=[
        dict(id='synthetic', split='train', difficulty='fixture') ])))
    env = fresh(pool)
    ep = env.episodes
    # Hand-assembled structural fixture: four naturally-ended rows have already
    # been replaced by their next episode, four keep their eight-decision state.
    base = torch.zeros(8, 3)
    base[:, 0] = torch.arange(8)*.01
    q = torch.tensor(CBL_Q).float().expand(8, -1).clone()
    tcp = ep.kin.world_tcp(base, q)
    xyz = torch.stack([tcp[:, :3, 3], tcp[:, :3, 3]+torch.tensor([.5, 0., 0.])], 1)
    route = Route(xyz, matrix_quat(tcp[:, :3, :3])[:, None].expand(-1, 2, -1).clone())
    packed = PackedRoute.__new__(PackedRoute)
    packed.__dict__.update(vars(route))
    scenes = []
    for i in range(8):
        asset = PrimitiveAsset('synthetic', np.array([[4.,4.,0.,.1,.1,.1,1.,0.]]),
                               {}, {'boxes': f'synthetic-{i}'}, {}, (None,), {})
        scenes.append(PrimitiveScene.from_asset(asset, device='cpu', dtype=torch.float32))
    ep.scenes = PrimitiveSceneBatch(scenes)
    c = Core(State(base, q, torch.zeros(8)), packed, Grid.empty(8), ep.kin, ep.robot,
        SceneCollision(ep.scenes, ep.robot), renderer=PcdPanorama(ep.scenes, sensor_config=ep.sensor_config),
        **profile_options(ep.profile))
    c.candidate = Candidate(base.clone(), torch.zeros(8), torch.zeros(8, dtype=torch.bool))
    c.start = c.state.clone()
    c.decisions[4:] = 8
    c.time[4:] = 3.
    c.attempt_time[4:] = 3.5
    c.failures[4:] = 2
    c.queue[4:, 0] = .25
    c.visible_previous[4:, 1] = -.5
    c.grid.observed[:, 100, 100] = True
    c.grid.height[:, 100, 100] = .4
    c.grid.timestamp.copy_(torch.arange(8)*.2)
    c.first = torch.ones(8, dtype=torch.bool)
    c._cached_observation = None
    c._route_raster_cache = None
    c.attempts = [dict(active=torch.tensor([False]*4+[True]*4),
                       committed=torch.tensor([False]*4+[True]*4), raw=torch.arange(8))]
    c.trace = [(c.state.clone(), torch.tensor([False]*4+[True]*4))]
    ep.core = c
    ep.episode_count = torch.tensor([2]*4+[1]*4)
    ep.map_ids = ['synthetic']*8
    ep.proposal_seeds = list(range(8))
    ep.totals = {k: torch.arange(8)+2 for k in ('sensor_frames','origin_inside_self_frames','fully_occluded_frames')}
    ep.sampler.planners = {'synthetic': PcdTruthPlanner(scenes[0])}
    ep.sampler.stats['accepted'] = 12
    env.previous_result = env._empty_result()
    env.previous_candidate = base.clone()
    env.previous_result_v1 = torch.zeros(8, 19)
    env.previous_target_delta_s = torch.zeros(8)
    env.previous_link = [None]*4+[(1, 7)]*4
    env.observation = env._upper_observation()
    mask = torch.ones(8, 13, dtype=torch.bool)
    env.candidates = dict(mask=mask, c_k=torch.zeros(8,13,3), f_k=torch.zeros(8,13,19),
        progress=torch.zeros(8,13), inplace=torch.zeros(8,13,dtype=torch.bool),
        world_pose=base[:,None].expand(-1,13,-1).clone(),
        terminal_placeholder=torch.zeros(8,dtype=torch.bool), pending=False)
    replay = EpisodeReplay(1000, seed=101)
    histories = [[] for _ in range(8)]
    # The journal/replay contain 64 explicitly synthetic decisions. No Core step
    # or real environment decision is performed by this fixture.
    records = []
    for i in range(8):
        for t in range(8):
            r = transition(t, end=i < 4 and t == 7, marker=i)
            r.update(run_id=env.run_id, environment_id=torch.tensor(i), episode_id=torch.tensor(1))
            replay.append((env.run_id, i, 1), r)
            records.append(r)
            if i >= 4: histories[i].append(deepcopy(r))
    fields = dict(run_id=env.run_id)
    for key in records[0]:
        if key == 'run_id': continue
        values = [r[key] for r in records]
        if isinstance(values[0], torch.Tensor): fields[key] = torch.stack(values)
        elif isinstance(values[0], dict):
            fields[key] = {k: torch.stack([v[k] for v in values]) for k in values[0]}
        else: fields[key] = values
    # decision_index and marker are scalar ints; journal batches use tensors.
    fields['decision_index'] = torch.tensor([r['decision_index'] for r in records])
    # Replay stores scalar decision indices as Python ints, so retain the actual
    # batched journal representation that row() yields in normal collector use.
    for r in replay.episodes.values():
        for item in r: item['decision_index'] = torch.tensor(item['decision_index'])
    for h in histories:
        for item in h: item['decision_index'] = torch.tensor(item['decision_index'])
    journal = directory/'journal.pt'
    atomic_torch(journal, dict(fields=fields, next_boundary_ready=True))
    learner = Stage1Learner(model(), 9000, objective='relative_uniform')
    fixture_update(learner, replay, adapter)
    # Retain nonempty recurrent runtime separately from the episode histories.
    learner.model.vcm.memory[4] = deque([MemoryEntry(torch.ones(128), torch.zeros(3), torch.tensor(7))], maxlen=4)
    learner.model.vcm.hidden[4] = torch.arange(128).float()
    budget = Budget(directory/'budget.json', started=time.monotonic(), seconds=120,
                    decisions=128, updates=64)
    budget.reserve(64); budget.complete(64); budget.update()
    generator = torch.Generator().manual_seed(101)
    return env, learner, replay, budget, journal, generator, histories


def save_fixture(directory):
    env, learner, replay, budget, journal, generator, histories = setup_boundary(directory)
    path = Path(directory)/'boundary.pt'
    save_decision_boundary(path, learner, replay, environment=env,
        policy_generator=generator, budget=budget, config={'fixture': True},
        counters={'decisions':64,'updates':1,'vector_dim':3}, journal_paths=[journal], histories=histories)
    return path, env, learner, replay, budget, generator, histories


def restore(path, *, allow_same=True):
    learner = Stage1Learner(model(), 9000, objective='relative_uniform')
    replay = EpisodeReplay(1000, seed=0)
    restored = load_decision_boundary(path, learner, replay,
        environment_factory=lambda: fresh(path.parent/'pool.json'), config={'fixture':True},
        test_only_allow_same_pid=allow_same)
    return restored, learner, replay


def test_complete_boundary_save_restores_nonunit_stride_journal_fields(tmp_path):
    env, learner, replay, budget, journal, generator, histories = setup_boundary(tmp_path)
    # Match the real journal's singleton view into a 13-candidate tensor. It is
    # contiguous according to PyTorch, but its last stride is 13 instead of 1.
    backing = torch.arange(64 * 13 * 13, dtype=torch.float32).reshape(64, 13, 13)
    progress = backing[:, :1, 0]
    raw = torch.load(journal, weights_only=False)
    raw['fields']['layout_probe'] = {'inplace_progress': progress}
    atomic_torch(journal, raw)
    for index, record in enumerate(r for sequence in replay.episodes.values() for r in sequence):
        record['layout_probe'] = {'inplace_progress': progress[index]}
        assert record['layout_probe']['inplace_progress'].stride() == (13,)
        i, t = index // 8, index % 8
        if i >= 4:
            histories[i][t]['layout_probe'] = deepcopy(record['layout_probe'])
    path = tmp_path/'strided-boundary.pt'
    save_decision_boundary(path, learner, replay, environment=env,
        policy_generator=generator, budget=budget, config={'fixture': True},
        counters={'decisions':64,'updates':1,'vector_dim':3},
        journal_paths=[journal], histories=histories)
    bundle, _, restored_replay = restore(path)
    try:
        assert tree_equal(replay.state_dict(), restored_replay.state_dict())
        assert tree_equal(histories, bundle['histories'])
    finally:
        bundle['budget']._resume_lock.close()


def reference(env, learner, replay, generator):
    start = capture_environment(env)
    sample = fragment_identity(replay.sample(32))
    draw = torch.multinomial(torch.ones(8,13)/13, 1, generator=generator)
    streams = [int(env.episodes.streams.for_env(i).maps.integers(2**31)) for i in range(8)]
    next_update = fixture_update(learner, replay, adapter)
    return dict(environment=start, sample=sample, draw=draw, streams=streams,
                update=next_update, learner=deepcopy(learner.state_dict()), rng=rng_state())


def test_mixed_batch8_state_sampler_memory_next_sample_and_update(tmp_path):
    path, env, learner, replay, budget, generator, histories = save_fixture(tmp_path)
    expected_runtime = encode((learner.model.vcm.memory, learner.model.vcm.hidden))
    expected = reference(env, learner, replay, generator)
    bundle, actual_learner, actual_replay = restore(path)
    actual_env = bundle['environment']
    assert tree_equal(expected_runtime, encode((actual_learner.model.vcm.memory,actual_learner.model.vcm.hidden)))
    assert tree_equal(encode(histories), encode(bundle['histories']))
    assert actual_env.episodes.core.decisions.tolist() == [0]*4+[8]*4
    assert actual_env.episodes.episode_count.tolist() == [2]*4+[1]*4
    assert bundle['budget'].started == budget.started
    assert bundle['budget'].deadline == budget.deadline
    assert state_digest(actual_env) == state_digest(env)
    actual = reference(actual_env, actual_learner, actual_replay, bundle['policy_generator'])
    assert not mismatch_report(expected, actual)
    assert tree_equal(actual_env._upper_observation(), env._upper_observation())
    bundle['budget']._resume_lock.close()


def test_save_in_child_new_pid_restore_exact_next_update_and_original_deadline(tmp_path):
    code = '''
from pathlib import Path
import sys, torch, os
from task10.tests.test_decision_recovery import save_fixture, reference
from task10.runtime import atomic_torch
torch.set_num_threads(2)
p=Path(sys.argv[1])
path, env, learner, replay, budget, generator, histories=save_fixture(p)
atomic_torch(p/'expected.pt',dict(result=reference(env,learner,replay,generator),
    pid=os.getpid(),started=budget.started,deadline=budget.deadline))
'''
    child = subprocess.run([sys.executable, '-c', code, str(tmp_path)], capture_output=True, text=True)
    assert child.returncode == 0, child.stderr
    expected = torch.load(tmp_path/'expected.pt', weights_only=False)
    bundle, learner, replay = restore(tmp_path/'boundary.pt', allow_same=False)
    assert expected['pid'] != os.getpid()
    assert bundle['budget'].started == expected['started']
    assert bundle['budget'].deadline == expected['deadline']
    actual = reference(bundle['environment'], learner, replay, bundle['policy_generator'])
    assert not mismatch_report(expected['result'], actual)
    bundle['budget']._resume_lock.close()


@pytest.mark.parametrize('bad', ['pending','inflight','ended','placeholder','history','journal','replay'])
def test_reject_uncommitted_or_inconsistent_boundary(tmp_path, bad):
    env, learner, replay, budget, journal, generator, histories = setup_boundary(tmp_path)
    if bad == 'pending': env._pending_result = object()
    if bad == 'inflight': budget.reserve(8)
    if bad == 'ended': env.episodes.core.truncated[0] = True
    if bad == 'placeholder': env.candidates['terminal_placeholder'][0] = True
    if bad == 'history': histories[4].pop()
    if bad == 'journal': journal_paths = []
    else: journal_paths = [journal]
    if bad == 'replay': next(iter(replay.episodes.values()))[0]['reward'] += 1
    with pytest.raises(ValueError):
        save_decision_boundary(tmp_path/'bad.pt',learner,replay,environment=env,
            policy_generator=generator,budget=budget,config={'fixture':True},
            counters={'decisions':64,'updates':1,'vector_dim':3},
            journal_paths=journal_paths,histories=histories)


@pytest.mark.parametrize('bad', ['format','source','runtime','config','ledger','journal','schema'])
def test_reject_changed_version_evidence_without_budget_rewind(tmp_path, bad):
    path, *_ = save_fixture(tmp_path)
    state = torch.load(path, weights_only=False)
    if bad == 'format': state['format'] = 'unsupported'
    if bad == 'source': state['sources']['src/task10/environment.py'] = 'changed'
    if bad == 'runtime': state['runtime']['deterministic'] = not state['runtime']['deterministic']
    if bad == 'config': state['config']['fixture'] = False
    if bad == 'schema': state['environment_state']['schema'] = 'unsupported'
    if bad == 'ledger': (tmp_path/'budget.json').write_text('{}')
    if bad == 'journal': (tmp_path/'journal.pt').write_bytes(b'changed')
    atomic_torch(path, state)
    before = (tmp_path/'budget.json').read_bytes()
    with pytest.raises(ValueError): restore(path)
    assert (tmp_path/'budget.json').read_bytes() == before


def test_same_pid_and_second_owner_rejected(tmp_path):
    path, *_ = save_fixture(tmp_path)
    with pytest.raises(ValueError, match='same-PID'): restore(path, allow_same=False)
    bundle, _, _ = restore(path)
    with pytest.raises(ValueError, match='another resumed collector'): restore(path)
    bundle['budget']._resume_lock.close()
    # Loading once durably changes ownership/wall evidence, so a later load
    # from that stale checkpoint fails even without further scientific work.
    with pytest.raises(ValueError, match='ledger changed'): restore(path)


def test_closed_codec_rejects_unknown_object_and_schema():
    with pytest.raises(ValueError, match='unsupported boundary state object'): encode(object())
    with pytest.raises(ValueError, match='schema'): decode({'schema':'other'},device='cpu')


def test_immutable_boundary_and_changed_history_content_rejected(tmp_path):
    path, env, learner, replay, budget, generator, histories = save_fixture(tmp_path)
    with pytest.raises(ValueError, match='immutable'):
        save_decision_boundary(path,learner,replay,environment=env,policy_generator=generator,
            budget=budget,config={'fixture':True},counters={'decisions':64,'updates':1,'vector_dim':3},
            journal_paths=[tmp_path/'journal.pt'],histories=histories)
    histories[4][0]['reward'] += 1
    with pytest.raises(ValueError, match='history differs'):
        save_decision_boundary(tmp_path/'changed.pt',learner,replay,environment=env,policy_generator=generator,
            budget=budget,config={'fixture':True},counters={'decisions':64,'updates':1,'vector_dim':3},
            journal_paths=[tmp_path/'journal.pt'],histories=histories)
