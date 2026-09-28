import json
import numpy as np
import pytest

from wm.data import DataError, EpisodeDataset, file_sha256, validate_episode, load_episode


def episode(T=5, seed=3, complete=True, subgoal=None):
    n = T + 1 if complete else T
    rng = np.random.default_rng(seed)
    done = np.zeros(T, bool)
    if complete and T:
        done[-1] = True
    return dict(robot_state=rng.normal(size=(n, 41)).astype(np.float32),
                local_map=rng.integers(0, 2, size=(n, 120, 120, 1)).astype(np.float32),
                action=rng.uniform(-1, 1, size=(T, 3)).astype(np.float32),
                reward=np.zeros(T, np.float32), dt=np.full(T, .1, np.float32), done=done,
                subgoal_index=np.zeros(n, np.int16) if subgoal is None else np.asarray(subgoal, np.int16),
                terminated=True, truncated=False, complete=complete, seed=seed)


def test_valid_episode_counts_targets():
    assert validate_episode(episode(5)) == 5
    assert validate_episode(episode(5, complete=False)) == 4  # final action has no target


@pytest.mark.parametrize('breaker', [
    lambda e: e.update(robot_state=e['robot_state'][:-1], local_map=e['local_map'][:-1], subgoal_index=e['subgoal_index'][:-1]),
    lambda e: e['action'].__setitem__((0, 0), 1.5),
    lambda e: e['robot_state'].__setitem__((2, 3), np.nan),
    lambda e: e['dt'].__setitem__(1, 0.),
    lambda e: e['done'].__setitem__(1, True),
    lambda e: e.update(action=e['action'].astype(np.float64)),
    lambda e: e.update(local_map=np.zeros((6, 150, 150, 1), np.float32)),
])
def test_invalid_episodes_are_rejected(breaker):
    e = episode(5)
    breaker(e)
    with pytest.raises(DataError):
        validate_episode(e)


def test_seed_identity_checked():
    with pytest.raises(DataError):
        validate_episode(episode(5, seed=3), seed=4)


def make_manifest(tmp_path, specs):
    records = []
    for i, (split, T, complete) in enumerate(specs):
        path = tmp_path / ('ep%d.npz' % i)
        np.savez_compressed(path, **episode(T, seed=i, complete=complete))
        records.append(dict(split=split, seed=i, path=path.name, sha256=file_sha256(path), usable=True))
    m = tmp_path / 'dataset.json'
    m.write_text(json.dumps(dict(episodes=records)))
    return m


def test_windows_never_cross_episodes_and_short_episodes_yield_none(tmp_path):
    m = make_manifest(tmp_path, [('train', 7, True), ('train', 1, True), ('train', 4, False), ('val', 5, True)])
    ds = EpisodeDataset.from_manifest(m, 'train')
    assert len(ds.episodes) == 3
    w5 = ds.windows(5)
    assert {tuple(x) for x in w5} == {(0, 0), (0, 1), (0, 2)}  # T=1 and incomplete T=4 (3 targets) give none
    assert len(ds.windows(1)) == 7 + 1 + 3
    batch = ds.gather(w5, 5)
    ep0 = ds.read_episode(0)
    assert np.array_equal(batch['robot'][1], ep0['robot_state'][1:7])
    assert np.array_equal(batch['action'][2], ep0['action'][2:7])
    with pytest.raises(DataError):
        ds.gather(np.array([[2, 1]]), 3)  # incomplete episode: only 3 valid targets


def test_same_seed_reading_is_reproducible_and_shuffle_keeps_split(tmp_path):
    m = make_manifest(tmp_path, [('train', 6, True), ('val', 6, True), ('train', 3, True)])
    a, b = EpisodeDataset.from_manifest(m, 'train'), EpisodeDataset.from_manifest(m, 'train')
    wa, wb = a.windows(1), b.windows(1)
    ba, bb = list(a.batches(wa, 4, seed=7)), list(b.batches(wb, 4, seed=7))
    assert all(np.array_equal(x['robot'], y['robot']) for x, y in zip(ba, bb))
    assert set(a.seeds.tolist()) == {0, 2} and EpisodeDataset.from_manifest(m, 'val').seeds.tolist() == [1]


def test_goal_switch_windows_can_be_excluded(tmp_path):
    path = tmp_path / 'e.npz'
    np.savez_compressed(path, **episode(4, subgoal=[0, 0, 1, 1, 1]))
    ds = EpisodeDataset([load_episode(path)], 'train')
    assert len(ds.windows(1)) == 4 and len(ds.windows(1, exclude_goal_switch=True)) == 3


def test_checksum_mismatch_rejected(tmp_path):
    m = make_manifest(tmp_path, [('train', 3, True)])
    data = json.loads(m.read_text())
    data['episodes'][0]['sha256'] = '0' * 64
    m.write_text(json.dumps(data))
    with pytest.raises(DataError):
        EpisodeDataset.from_manifest(m, 'train')
