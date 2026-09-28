"""P1 world-model trajectory data: validation, transitions and within-episode windows.

Episode files are written by `p0_runner.py eval --save-observations` (observations[0:T+1], actions[0:T]).
Splits are by whole episode and fixed in the dataset manifest; shuffling never moves an episode across splits.
"""
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np

ROBOT_DIM = 41
MAP_SHAPE = (120, 120, 1)
ACTION_DIM = 3


class DataError(ValueError):
    pass


def validate_episode(ep, seed=None, action_low=-1., action_high=1.):
    """Check one episode dict; returns the number of transitions with a valid target."""
    rob, maps, act, dt = ep['robot_state'], ep['local_map'], ep['action'], ep['dt']
    T = act.shape[0]
    if act.ndim != 2 or act.shape[1] != ACTION_DIM or act.dtype != np.float32:
        raise DataError('action must be float32 (T,%d)' % ACTION_DIM)
    if rob.dtype != np.float32 or maps.dtype != np.float32:
        raise DataError('observations must be float32')
    if rob.shape[1:] != (ROBOT_DIM,) or maps.shape[1:] != MAP_SHAPE:
        raise DataError('observation shape mismatch %s %s' % (rob.shape, maps.shape))
    if rob.shape[0] != maps.shape[0]:
        raise DataError('robot/map length mismatch')
    complete = bool(ep['complete'])
    if complete and rob.shape[0] != T + 1:
        raise DataError('complete episode needs T+1 observations, got %d for T=%d' % (rob.shape[0], T))
    if not complete and rob.shape[0] not in (T, T + 1):
        raise DataError('incomplete episode has inconsistent length')
    if dt.shape != (T,) or ep['reward'].shape != (T,) or ep['done'].shape != (T,):
        raise DataError('per-step arrays must have length T')
    if ep['subgoal_index'].shape[0] != rob.shape[0]:
        raise DataError('subgoal_index must align with observations')
    for name in ['robot_state', 'local_map', 'action', 'reward', 'dt']:
        for start in range(0, len(ep[name]), 128):
            if not np.isfinite(ep[name][start:start + 128]).all():
                raise DataError('non-finite values in ' + name)
    if (dt <= 0).any():
        raise DataError('dt must be positive')
    if (act < action_low - 1e-6).any() or (act > action_high + 1e-6).any():
        raise DataError('action outside normalized bounds')
    if T and ep['done'][:-1].any():
        raise DataError('done before final step: episode identity broken')
    if seed is not None and int(ep['seed']) != int(seed):
        raise DataError('episode seed %s does not match manifest %s' % (ep['seed'], seed))
    return rob.shape[0] - 1


def check_episode_size(path, limit=256 << 20):
    # NPZ members are decompressed arrays, never frame-level mmap. Reject before unpacking.
    with zipfile.ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist()) > limit:
            raise DataError('episode exceeds decompression budget: %s' % path)


def load_episode(path, seed=None):
    check_episode_size(path)
    with np.load(path) as d:
        ep = {k: d[k] for k in d.files}
    ep['n_valid'] = validate_episode(ep, seed)
    return ep


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


class EpisodeDataset:
    """Episode index of one split. Direct construction is a small in-memory reference only."""

    def __init__(self, episodes, split):
        self.split = split
        self.episodes = episodes
        self.robot = np.concatenate([e['robot_state'] for e in episodes])
        self.map = np.concatenate([e['local_map'] for e in episodes])
        self.action = np.concatenate([e['action'] for e in episodes])
        self.dt = np.concatenate([e['dt'] for e in episodes])
        obs_off = np.cumsum([0] + [len(e['robot_state']) for e in episodes])
        act_off = np.cumsum([0] + [len(e['action']) for e in episodes])
        self.obs_offset, self.act_offset = obs_off[:-1], act_off[:-1]
        self.n_valid = np.array([e['n_valid'] for e in episodes])
        self.seeds = np.array([int(e['seed']) for e in episodes])

    @classmethod
    def from_manifest(cls, manifest_path, split):
        """Only small episode metadata/actions stay resident; maps are loaded one episode at a time.

        split=None includes every usable episode regardless of its manifest split label; only
        wm/residual_probe.py uses this (R0-4 condition manifests are a single stochastic-collection
        batch, not a train/val/test partition). train_offline.py/evaluate_prediction.py always pass
        an explicit split and are unaffected."""
        manifest_path = Path(manifest_path).resolve()
        manifest = json.loads(manifest_path.read_text())
        ds = cls.__new__(cls)
        ds.split, ds.manifest_path = split, manifest_path
        ds.episodes, ds.records = [], []
        obs_lengths, act_lengths = [], []
        for rec in manifest['episodes']:
            if (split is not None and rec['split'] != split) or not rec.get('usable', True):
                continue
            path = manifest_path.parent / rec['path']
            check_episode_size(path)
            if file_sha256(path) != rec['sha256']:
                raise DataError('checksum mismatch: %s' % path)
            with np.load(path) as raw:
                robot = raw['robot_state']
                n, T = len(robot), len(raw['action'])
                complete = bool(raw['complete'])
                if robot.dtype != np.float32 or robot.shape[1:] != (ROBOT_DIM,) or n not in ((T+1,) if complete else (T, T+1)):
                    raise DataError('invalid observation length/shape: %s' % path)
                ep = {key: raw[key] for key in raw.files if key not in ('robot_state', 'local_map', 'n_valid')}
                if int(ep['seed']) != int(rec['seed']):
                    raise DataError('episode seed does not match manifest seed')
                ep.update(n_valid=n-1, path=path, success=rec.get('primary_reason') == 'success')
            ds.episodes.append(ep)
            ds.records.append(rec)
            obs_lengths.append(n)
            act_lengths.append(T)
        if not ds.episodes:
            raise DataError('no episodes for split ' + split)
        ds.obs_offset = np.cumsum([0] + obs_lengths)[:-1]
        ds.act_offset = np.cumsum([0] + act_lengths)[:-1]
        ds.n_valid = np.array([e['n_valid'] for e in ds.episodes])
        ds.seeds = np.array([int(e['seed']) for e in ds.episodes])
        ds.action = np.concatenate([e['action'] for e in ds.episodes])
        ds.dt = np.concatenate([e['dt'] for e in ds.episodes])
        ds.n_observations = sum(obs_lengths)
        return ds

    def read_episode(self, i):
        ep = self.episodes[i]
        if 'path' not in ep:
            return ep
        if file_sha256(ep['path']) != self.records[i]['sha256']:
            raise DataError('checksum changed after indexing: %s' % ep['path'])
        return load_episode(ep['path'], self.seeds[i])

    def windows(self, k, exclude_goal_switch=False):
        """(episode, t) such that targets t+1..t+k all exist inside the same episode."""
        if k < 1:
            raise DataError('window horizon must be positive')
        counts = np.maximum(0, self.n_valid - k + 1)
        out = np.empty((int(counts.sum()), 2), dtype=np.int64)
        pos = 0
        for i, count in enumerate(counts):
            times = np.arange(count, dtype=np.int64)
            if exclude_goal_switch and count:
                goals = self.episodes[i]['subgoal_index']
                switches = np.r_[0, np.cumsum(np.diff(goals) != 0)]
                times = times[switches[times+k] == switches[times]]
            out[pos:pos+len(times), 0] = i
            out[pos:pos+len(times), 1] = times
            pos += len(times)
        return out[:pos]

    def gather(self, idx, k=1):
        """Observations o_t..o_{t+k}, actions a_t..a_{t+k-1}, dt, for window indices (episode, t)."""
        idx = np.asarray(idx, dtype=np.int64)
        e, t = idx[:, 0], idx[:, 1]
        if (e < 0).any() or (e >= len(self.episodes)).any() or (t < 0).any():
            raise DataError('invalid window index')
        o = self.obs_offset[e] + t
        a = self.act_offset[e] + t
        if (t + k > self.n_valid[e]).any():
            raise DataError('window crosses episode end')
        steps = np.arange(k + 1)
        if hasattr(self, 'manifest_path'):
            robot = np.empty((len(idx), k+1, ROBOT_DIM), np.float32)
            maps = np.empty((len(idx), k+1) + MAP_SHAPE, np.float32)
            for episode_id in np.unique(e):
                ep = self.read_episode(int(episode_id))
                rows = np.flatnonzero(e == episode_id)
                ix = t[rows, None] + steps
                robot[rows], maps[rows] = ep['robot_state'][ix], ep['local_map'][ix]
                del ep
            return dict(robot=robot, map=maps, action=self.action[a[:, None]+steps[:-1]], dt=self.dt[a[:, None]+steps[:-1]])
        return dict(robot=self.robot[o[:, None] + steps], map=self.map[o[:, None] + steps],
                    action=self.action[a[:, None] + steps[:-1]], dt=self.dt[a[:, None] + steps[:-1]])

    def batches(self, windows, batch_size, seed, k=1):
        order = np.random.default_rng(seed).permutation(len(windows))
        for s in range(0, len(order), batch_size):
            yield self.gather(windows[order[s:s + batch_size]], k)
