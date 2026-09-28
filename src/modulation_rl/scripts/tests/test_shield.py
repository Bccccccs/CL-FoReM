"""FOLLOWUP-028 B3: unit tests for shield.py that need no live env/ROS/GPU - 'none'/'random' arms
are pure numpy, and 'geo' is exercised against a tiny hand-built ClassifierPack fixture."""
import json

import numpy as np
import pytest
import torch

from foresight import ClassifierPack, LogisticHead, FeatureNorm
from shield import Shield


def test_none_arm_never_triggers_and_preserves_action_dtype():
    shield = Shield(dict(arm='none'))
    shield.reset(11)
    action = np.array([0.3, -0.2, 0.1], dtype=np.float32)
    out, risk, triggered = shield.decide(None, None, action)
    assert risk == 0.0 and triggered is False
    assert np.array_equal(out, action) and out.dtype == np.float32
    assert shield.episode_summary()['shield_trigger_count'] == 0


def test_random_arm_triggers_at_roughly_the_configured_rate_and_is_deterministic_per_seed():
    shield = Shield(dict(arm='random', random_probability=0.3))
    shield.reset(42)
    action = np.zeros(3, dtype=np.float32)
    triggers = []
    for _ in range(2000):
        out, risk, triggered = shield.decide(None, None, action)
        triggers.append(triggered)
        if triggered:
            assert out[0] == -1.0
    rate = np.mean(triggers)
    assert 0.2 < rate < 0.4  # loose sanity band around the configured 0.3

    # Same seed -> identical trigger sequence (needed for a reproducible B3 run).
    shield2 = Shield(dict(arm='random', random_probability=0.3))
    shield2.reset(42)
    triggers2 = [shield2.decide(None, None, action)[2] for _ in range(2000)]
    assert triggers == triggers2


def test_geo_arm_uses_previous_step_values_and_respects_threshold(tmp_path):
    # A logistic head that fires purely on the first feature (prev dist_to_desired) being large.
    head = LogisticHead(3)
    with torch.no_grad():
        head.linear.weight[:] = torch.tensor([[10.0, 0.0, 0.0]])
        head.linear.bias[:] = torch.tensor([-5.0])
    norm = FeatureNorm(mean=[0.0, 0.0, 0.0], std=[1.0, 1.0, 1.0])
    pack = ClassifierPack('geo', 'logistic', 3, [head.eval()], norm, threshold=0.5)
    pack.save(tmp_path / 'geo')

    shield = Shield(dict(arm='geo', threshold=0.5, classifier_dir=str(tmp_path / 'geo')))
    shield.reset(7)
    action = np.array([0.5, 0.0, 0.0], dtype=np.float32)

    # Before any observe(), prev_geo defaults to (0,0,0) -> low risk -> no trigger.
    out, risk, triggered = shield.decide(None, None, action)
    assert triggered is False and out[0] == pytest.approx(0.5)

    # observe() with a large dist_to_desired should push the next decide() to trigger.
    class FakeEnv:
        def get_robot_obs(self):
            class Obs:
                base_tf = [0.0, 0.0, 0.0]
            return Obs()

        class unwrapped:
            class _ee_planner:
                gripper_goal_wrist = [0.0, 0.0, 0.0]

    shield.observe(FakeEnv(), dict(dist_to_desired=1.0, rot_dist_to_desired=0.0))
    out2, risk2, triggered2 = shield.decide(None, None, action)
    assert triggered2 is True and out2[0] == -1.0
    assert shield.episode_summary()['shield_trigger_count'] == 1


def test_shield_rejects_unknown_arm():
    with pytest.raises(ValueError):
        Shield(dict(arm='bogus'))


def test_geo_and_cur_hist_wm_require_threshold():
    with pytest.raises(ValueError):
        Shield(dict(arm='geo'))
