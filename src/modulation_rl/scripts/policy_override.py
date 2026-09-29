"""CEIL-028 simple-policy controls for evaluation (D57 / 20260929-ceil-spec.md S3 E2).

Only imported when `p0_runner.py eval --policy-override MODE` is given; a plain run never touches this
module and produces no new field. Modes (normalised action space [-1, 1]^3):

  random   uniform in [-1, 1] per step; RNG derived from the episode seed only (reproducible, and
           independent of the environment's / BioIK's own random streams)
  mean     one fixed action every step: per-dimension mean of all actions policy-100k took in the R0-3c
           nominal 100 episodes (computed from data by `mean_action_from_trajectories`, never hand tuned)
  slow-ee  the checkpoint's own (deterministic) action with dimension 0 (gripper speed along the path)
           forced to -1 (slowest); exploratory, not a D57 criterion
"""
import glob
import hashlib
import json
from pathlib import Path

import numpy as np

MODES = ('random', 'mean', 'slow-ee')
ACTION_DIM = 3
RNG_TAG = 0xCE11  # namespaces the seed derivation so it can never coincide with other seeded streams


def mean_action_from_trajectories(directory):
    """Per-dimension mean over every step of every episode trajectory in `directory` (steps pooled,
    each step weighs the same). Returns a JSON-able dict incl. the provenance needed to audit it."""
    files = sorted(glob.glob(str(Path(directory) / 'episode-*-trajectory.npz')))
    if not files:
        raise FileNotFoundError('no episode-*-trajectory.npz in %s' % directory)
    chunks, digest = [], hashlib.sha256()
    for f in files:
        with np.load(f) as data:
            actions = np.asarray(data['actions'], dtype=np.float64).reshape(-1, ACTION_DIM)
        chunks.append(actions)
        digest.update(Path(f).name.encode())
        digest.update(np.ascontiguousarray(actions).tobytes())
    stacked = np.concatenate(chunks, axis=0)
    return dict(mean=[float(x) for x in stacked.mean(axis=0)], n_steps=int(len(stacked)), n_episodes=len(files),
                min=[float(x) for x in stacked.min(axis=0)], max=[float(x) for x in stacked.max(axis=0)],
                source_directory=str(directory), actions_sha256=digest.hexdigest(),
                definition='per-dimension mean over all steps of all episodes (steps pooled)')


class PolicyOverride:
    def __init__(self, mode, mean_action=None):
        if mode not in MODES:
            raise ValueError('unknown policy override %r (expected one of %s)' % (mode, MODES))
        self.mode = mode
        self.mean_action = None
        if mode == 'mean':
            if mean_action is None:
                raise ValueError('--policy-override mean needs --policy-override-mean-file')
            self.mean_action = np.asarray(mean_action, dtype=np.float32).reshape(ACTION_DIM)
            if not np.all(np.abs(self.mean_action) <= 1.0):
                raise ValueError('mean action must lie in [-1, 1]')
        self._rng = None

    @classmethod
    def from_args(cls, args):
        mean_action = None
        if args.policy_override == 'mean':
            path = getattr(args, 'policy_override_mean_file', None)
            if not path:
                raise ValueError('--policy-override mean needs --policy-override-mean-file')
            mean_action = json.loads(Path(path).read_text())['mean']
        return cls(args.policy_override, mean_action)

    @property
    def uses_policy(self):
        """Whether the checkpoint's own action is needed (slow-ee only)."""
        return self.mode == 'slow-ee'

    def reset(self, seed):
        """Call once per episode; for `random` this (re)creates the stream from the episode seed."""
        self._rng = np.random.default_rng([int(seed), RNG_TAG]) if self.mode == 'random' else None

    def act(self, policy_action=None):
        if self.mode == 'random':
            return self._rng.uniform(-1.0, 1.0, size=ACTION_DIM).astype(np.float32)
        if self.mode == 'mean':
            return self.mean_action.copy()
        action = np.array(policy_action, dtype=np.float32, copy=True)
        action[0] = -1.0
        return action
