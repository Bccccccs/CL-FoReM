"""task4.9 tests (synthetic, no ROS): causality filter, whole-episode split, WM beats identity when the action matters, detects an action-blind dynamics."""
import os
import sys
import unittest

try:
    import ray  # noqa: F401
    import torch
    import numpy as np
except ImportError as e:  # pragma: no cover
    raise unittest.SkipTest("container python stack not available: %s" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import scwm_wm as W  # noqa: E402


def make_meta(n_ep=6, L=20):
    m = {k: [] for k in ("episode_id", "step_in_episode", "epoch", "t_obs", "t_cmd", "t_next")}
    t = 0.0
    for e in range(n_ep):
        for s in range(L):
            m["episode_id"].append(e); m["step_in_episode"].append(s); m["epoch"].append(e)
            m["t_obs"].append(t); m["t_cmd"].append(t + 0.001); m["t_next"].append(t + 0.03); t += 0.03
        t += 5.0   # reset gap
    return {k: np.array(v) for k, v in m.items()}


class Causality(unittest.TestCase):
    def test_clean_meta_is_all_valid(self):
        ok, r = W.valid_pairs(make_meta())
        self.assertTrue(ok.all(), r)

    def test_gap_and_backwards_time_rejected(self):
        m = make_meta()
        m["step_in_episode"][30] += 2          # lost transition inside an episode
        m["t_next"][70] = m["t_cmd"][70] - 0.1  # next observation before the command
        ok, r = W.valid_pairs(m)
        self.assertFalse(ok[29]); self.assertFalse(ok[70])
        self.assertTrue(ok[:28].all() and ok[40:69].all())     # damage stays local (neighbouring rows are conservatively dropped)
        self.assertLessEqual(int((~ok).sum()), 5, r)

    def test_split_is_by_whole_episode_and_stable(self):
        ids = np.repeat(np.arange(200), 5)
        v1 = W.stable_split(ids, 20, "s0"); v2 = W.stable_split(ids, 20, "s0")
        self.assertTrue(np.array_equal(v1, v2))
        for e in range(200):
            self.assertEqual(len(set(v1[ids == e])), 1)
        self.assertTrue(0.1 < v1.mean() < 0.3)


class Learns(unittest.TestCase):
    def _data(self, action_matters, n=6000, seed=0):
        g = torch.Generator().manual_seed(seed)
        z = torch.randn(n, 16, generator=g)
        a = torch.rand(n, 3, generator=g) * 2 - 1
        Wm = torch.randn(3, 16, generator=g) * 0.5
        dz = (a @ Wm if action_matters else torch.zeros(n, 16)) + 0.01 * torch.randn(n, 16, generator=g)
        return z, a, z + dz

    def test_beats_identity_and_uses_actions(self):
        z, a, zn = self._data(True)
        val = np.arange(len(z)) % 5 == 0
        model, hist, ev = W.train_world_model(z, a, zn, val, hidden=64, layers=2, max_epochs=40, patience=5, log=lambda *_: None)
        self.assertGreater(ev["skill_vs_identity"], 0.9)
        self.assertGreater(ev["action_shuffle_increase"], 1.0)

    def test_action_blind_dynamics_shows_no_action_use(self):
        z, a, zn = self._data(False)
        val = np.arange(len(z)) % 5 == 0
        model, hist, ev = W.train_world_model(z, a, zn, val, hidden=64, layers=2, max_epochs=20, patience=5, log=lambda *_: None)
        self.assertLess(abs(ev["action_shuffle_increase"]), 0.5)


if __name__ == "__main__":
    unittest.main()
