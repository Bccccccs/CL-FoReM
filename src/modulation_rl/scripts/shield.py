"""FOLLOWUP-028 B3: closed-loop shield (--shield-config, default off).

Loaded by p0_runner.py's evaluate() only when --shield-config PATH is given. Every step, after the
policy proposes an action, the shield computes a risk score with one of the four classifiers built
offline by b2_train.py (or a 'random'/'none' control) using EXACTLY the feature functions in
foresight.py (the module both this file and b2_train.py import), so the online and offline features
are guaranteed identical. If risk exceeds the (pre-registered, D51) threshold, the end-effector
reference-velocity dimension (action[0]) is forced to -1 (minimum speed, giving the chassis time to
catch up); otherwise the policy's action passes through unchanged.

Config schema (JSON, see --shield-config):
  {
    "arm": "none"|"random"|"geo"|"cur"|"hist"|"wm",
    "threshold": <float>,                 # required for geo/cur/hist/wm
    "random_probability": <float>,        # required for random
    "history_k": 5,                       # optional, default foresight.HISTORY_K
    "encoder_checkpoint": "path",         # required for cur/hist/wm
    "dynamics_checkpoint": "path",        # required for wm only
    "classifier_dir": "path",             # required for geo/cur/hist/wm (a ClassifierPack dir)
    "device": "cpu"                       # optional, default cpu (shield runs one step at a time)
  }

'none' loads nothing and never triggers - it exists so B3's 'none' arm can be run through the exact
same --shield-config code path as the other five arms (for a code-path sanity check against a
plain, no-flag run) while being causally a complete no-op.
"""
import json
from pathlib import Path

import numpy as np
import torch

import foresight

VALID_ARMS = ('none', 'random', 'geo', 'cur', 'hist', 'wm')


class Shield:
    def __init__(self, config):
        self.config = config
        self.arm = config['arm']
        if self.arm not in VALID_ARMS:
            raise ValueError('unknown shield arm: %r' % self.arm)
        self.device = config.get('device', 'cpu')
        self.history_k = config.get('history_k', foresight.HISTORY_K)
        self.threshold = config.get('threshold')
        self.random_probability = config.get('random_probability')
        self.pack = None
        self.encoder = None
        self.dynamics = None
        self.dyn_norm = None
        self.policy = None
        if self.arm in ('geo', 'cur', 'hist', 'wm'):
            if self.threshold is None:
                raise ValueError('shield arm %r requires "threshold"' % self.arm)
            from foresight import ClassifierPack
            self.pack = ClassifierPack.load(config['classifier_dir'], device=self.device)
        if self.arm in ('cur', 'hist', 'wm'):
            from wm.encoder import FixedEncoder
            self.encoder = FixedEncoder(config['encoder_checkpoint'], self.device)
        if self.arm == 'wm':
            from residual_probe import load_model
            self.dynamics, self.dyn_norm, _ = load_model(config['dynamics_checkpoint'], self.device)
            self.policy = foresight.load_full_policy(config['encoder_checkpoint'], self.device)
        if self.arm == 'random' and self.random_probability is None:
            raise ValueError('shield arm "random" requires "random_probability"')
        self._rng = np.random.default_rng(0)
        self._history = []
        self._prev_geo = (0.0, 0.0, 0.0)
        self._trigger_count = 0
        self._risk_log = []
        self._triggered_log = []

    @classmethod
    def from_config(cls, path):
        return cls(json.loads(Path(path).read_text()))

    def reset(self, seed):
        # Deterministic per-episode stream, independent of any other RNG in the process (matches
        # mismatch-v1's independent-RNG convention in robotenv.py so the shield's own randomness
        # never perturbs env/policy sampling).
        self._rng = np.random.default_rng([int(seed), 0xB3_5D1E1D])
        self._history = []
        self._prev_geo = (0.0, 0.0, 0.0)
        self._trigger_count = 0
        self._risk_log = []
        self._triggered_log = []

    @torch.no_grad()
    def _encode_std(self, robot, local_map):
        raw = self.encoder(np.asarray(robot, dtype=np.float32)[None], np.asarray(local_map, dtype=np.float32)[None])
        return self.dyn_norm(raw)[0].cpu().numpy().astype(np.float64) if self.dyn_norm is not None else raw[0].cpu().numpy().astype(np.float64)

    def decide(self, robot_state, local_map, action):
        """Called after the policy proposes `action`, before env.step. Returns (action_out, risk,
        triggered); never mutates its inputs."""
        action = np.asarray(action)
        action_dtype = action.dtype
        action = action.astype(np.float64)
        if self.arm == 'none':
            risk, triggered = 0.0, False
        elif self.arm == 'random':
            draw = float(self._rng.random())
            risk, triggered = draw, draw < self.random_probability
        elif self.arm == 'geo':
            feat = foresight.geo_feature(*self._prev_geo)
            risk = float(self.pack.score(feat)[0])
            triggered = risk > self.threshold
        else:
            z_std = self._encode_std(robot_state, local_map)
            if self.arm == 'cur':
                feat = foresight.cur_feature(z_std, action)
            elif self.arm == 'hist':
                feat = foresight.hist_feature(z_std, action, list(reversed(self._history)), K=self.history_k)
            else:  # wm
                feat = foresight.wm_feature(z_std, action, self.dynamics, self.dyn_norm, self.policy,
                                             K=self.history_k, device=self.device)
            risk = float(self.pack.score(feat)[0])
            triggered = risk > self.threshold
        action_out = action.copy()
        if triggered:
            action_out[0] = -1.0
        if self.arm in ('cur', 'hist', 'wm'):
            self._history.insert(0, (z_std, action_out))
            del self._history[self.history_k:]
        self._trigger_count += int(triggered)
        self._risk_log.append(risk)
        self._triggered_log.append(bool(triggered))
        return action_out.astype(action_dtype), risk, triggered

    def observe(self, env, info):
        """Called after env.step executes the (possibly shielded) action; updates the 'previous
        step' geometric state the geo arm (and, implicitly, the next decide() call) reads."""
        self._prev_geo = (float(info.get('dist_to_desired', 0.0)), float(info.get('rot_dist_to_desired', 0.0)),
                           foresight.goal_to_base_distance(env))

    def episode_summary(self):
        return dict(arm=self.arm, shield_trigger_count=self._trigger_count,
                    shield_risk=list(self._risk_log), shield_triggered=list(self._triggered_log))
