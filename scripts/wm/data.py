"""P1 world-model trajectory data: validation, transitions and within-episode windows.

Episode files are written by `p0_runner.py eval --save-observations` (observations[0:T+1], actions[0:T]).
Splits are by whole episode and fixed in the dataset manifest; shuffling never moves an episode across splits.
"""
import hashlib
import json
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
        if not np.isfinite(ep[name]).all():
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


def load_episode(path, seed=None):
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
    """In-memory set of validated episodes of one split. Indices never cross episodes."""

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
        manifest_path = Path(manifest_path)
        manifest = json.loads(manifest_path.read_text())
        episodes = []
        for rec in manifest['episodes']:
            if rec['split'] != split or not rec.get('usable', True):
                continue
            path = manifest_path.parent / rec['path']
            if file_sha256(path) != rec['sha256']:
                raise DataError('checksum mismatch: %s' % path)
            ep = load_episode(path, rec['seed'])
            ep['success'] = rec.get('primary_reason') == 'success'
            episodes.append(ep)
        if not episodes:
            raise DataError('no episodes for split ' + split)
        return cls(episodes, split)

    def windows(self, k, exclude_goal_switch=False):
        """(episode, t) such that targets t+1..t+k all exist inside the same episode."""
        out = []
        for i, e in enumerate(self.episodes):
            for t in range(0, e['n_valid'] - k + 1):
                if exclude_goal_switch and (np.diff(e['subgoal_index'][t:t + k + 1]) != 0).any():
                    continue
                out.append((i, t))
        return np.asarray(out, dtype=np.int64).reshape(-1, 2)

    def gather(self, idx, k=1):
        """Observations o_t..o_{t+k}, actions a_t..a_{t+k-1}, dt, for window indices (episode, t)."""
        e, t = idx[:, 0], idx[:, 1]
        o = self.obs_offset[e] + t
        a = self.act_offset[e] + t
        if (t + k > self.n_valid[e]).any():
            raise DataError('window crosses episode end')
        steps = np.arange(k + 1)
        return dict(robot=self.robot[o[:, None] + steps], map=self.map[o[:, None] + steps],
                    action=self.action[a[:, None] + steps[:-1]], dt=self.dt[a[:, None] + steps[:-1]])

    def batches(self, windows, batch_size, seed, k=1):
        order = np.random.default_rng(seed).permutation(len(windows))
        for s in range(0, len(order), batch_size):
            yield self.gather(windows[order[s:s + batch_size]], k)
