"""task4.8 tests: FixedGaussianPolicy single-tanh consistency, GpuReplay vs reference ReplayMemory, ScwmSAC update parity with the
reference SAC.update_parameters, full-state save/load continuation. CPU by default (SCWM_TEST_DEVICE=cuda to also run on a GPU)."""
import os
import random
import sys
import unittest

try:
    import ray  # noqa: F401  (must precede torch)
    import torch
    import numpy as np
    import gym
except ImportError as e:  # pragma: no cover
    raise unittest.SkipTest("container python stack not available: %s" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
FOREM = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(FOREM, "scripts"))
sys.path.insert(0, os.path.join(FOREM, "src", "modulation_rl", "scripts"))

from replay_memory import ReplayMemory  # noqa: E402
from sac import SAC  # noqa: E402
from scwm_policy import FixedGaussianPolicy  # noqa: E402
from scwm_sac import GpuReplay, ScwmSAC  # noqa: E402

DEV = os.environ.get("SCWM_TEST_DEVICE", "cpu")
HID = [64, 64, 256]       # the reference Q head hard-codes in_size=256 for the logits layer, so the last hidden size must be 256


def spaces():
    rs = gym.spaces.Box(-100, 100, (41,), dtype=np.float32)
    ms = gym.spaces.Box(-1.1, 10.1, (120, 120, 1), dtype=np.float32)
    return gym.spaces.Tuple([rs, ms]), gym.spaces.Box(-1.0, 1.0, (3,), dtype=np.float32)


def args(device):
    return dict(gamma=0.99, tau=0.001, initial_alpha=1.0, device=device, model=dict(custom_model_config=dict(post_fcnet_hiddens=HID)))


def fake_transitions(n, seed=0):
    r = np.random.RandomState(seed)
    out = []
    for i in range(n):
        ms = (r.rand(120, 120, 1) > 0.93).astype(np.float32)
        mn = (r.rand(120, 120, 1) > 0.93).astype(np.float32)
        out.append((ms, r.randn(41).astype(np.float32), np.tanh(r.randn(3)).astype(np.float32), float(r.randn()),
                    mn, r.randn(41).astype(np.float32), float(r.rand() > 0.1)))
    return out


def meta(i):
    return dict(episode_id=i // 7, step_in_episode=i % 7, epoch=0, t_obs=i * 0.02, t_cmd=i * 0.02, t_next=i * 0.02 + 0.02, done=(i % 7 == 6))


class PolicyConsistency(unittest.TestCase):
    def test_predict_is_single_tanh_and_matches_sample(self):
        torch.manual_seed(1)
        obs, act = spaces()
        pol = FixedGaussianPolicy(obs[1], obs[0], 3, HID, act, False)
        rob = torch.randn(16, 41)
        mp = (torch.rand(16, 120, 120, 1) > 0.9).float()
        with torch.no_grad():
            mean, log_std = pol.distribution_params(mp, rob)
            self.assertTrue(torch.allclose(pol.predict(mp, rob, True), torch.tanh(mean), atol=1e-6))
            torch.manual_seed(5)
            a_s, lp = pol.sample(mp, rob)
            torch.manual_seed(5)
            a_p = pol.predict(mp, rob, False)
        self.assertTrue(torch.allclose(a_s, a_p, atol=1e-6))
        self.assertLessEqual(float(a_p.abs().max()), 1.0)
        # log-prob of the executed action under the same distribution equals the sampled log-prob
        with torch.no_grad():
            lp2 = pol.sample_with_action(mp, rob, a_s)
        self.assertTrue(torch.allclose(lp, lp2.reshape(-1), atol=1e-3), (lp - lp2.reshape(-1)).abs().max())


class ReplayParity(unittest.TestCase):
    def test_same_batches_as_reference(self):
        data = fake_transitions(40)
        random.seed(11)
        ref = ReplayMemory(100, 11)
        gpu = GpuReplay(100, 11, DEV)
        for i, t in enumerate(data):
            ref.push(*t)
            gpu.push(*t, meta=meta(i))
        for _ in range(3):
            rm = ref.sample(8)
            gm = [x.cpu().numpy() for x in gpu.sample(8)]
            self.assertTrue(np.array_equal(rm[0], gm[0]))
            self.assertTrue(np.allclose(rm[1], gm[1]))
            self.assertTrue(np.allclose(rm[2], gm[2]))
            self.assertTrue(np.allclose(rm[3], gm[3][:, 0]))
            self.assertTrue(np.array_equal(rm[4], gm[4]))
            self.assertTrue(np.allclose(rm[5], gm[5]))
            self.assertTrue(np.allclose(rm[6], gm[6][:, 0]))

    def test_ring_wrap_and_state_roundtrip(self):
        data = fake_transitions(12)
        a = GpuReplay(8, 3, DEV)
        for i, t in enumerate(data):
            a.push(*t, meta=meta(i))
        self.assertEqual(len(a), 8)
        s = a.state_dict()
        b = GpuReplay(8, 99, DEV)
        b.load_state_dict(s)
        for x, y in zip(a.sample(5), b.sample(5)):
            self.assertTrue(torch.equal(x, y))
        self.assertTrue(np.array_equal(a.meta["episode_id"], b.meta["episode_id"]))

    def test_non_binary_map_rejected(self):
        a = GpuReplay(4, 0, DEV)
        t = list(fake_transitions(1)[0])
        t[0] = t[0] * 0.5
        with self.assertRaises(ValueError):
            a.push(*t, meta=meta(0))


class SacParity(unittest.TestCase):
    def _agents(self, seed=7):
        obs, act = spaces()
        torch.manual_seed(seed)
        ref = SAC(obs, act, 1, args(DEV), 5000001)
        torch.manual_seed(seed)
        new = ScwmSAC(obs, act, 1, args(DEV), 5000001)
        return ref, new

    def test_update_equals_reference_update(self):
        ref, new = self._agents()
        data = fake_transitions(24, seed=3)
        random.seed(21)
        mem_ref = ReplayMemory(100, 21)
        mem_new = GpuReplay(100, 21, DEV)
        for i, t in enumerate(data):
            mem_ref.push(*t)
            mem_new.push(*t, meta=meta(i))
        for k in range(3):
            torch.manual_seed(100 + k)
            l_ref = ref.update_parameters(mem_ref, 8, k)
            torch.manual_seed(100 + k)
            l_new = new.update_parameters(mem_new, 8, k)
            for a, b in zip(l_ref, l_new):
                self.assertAlmostEqual(a, b, places=4)
        for p, q in zip(ref.policy.parameters(), new.policy.parameters()):
            self.assertTrue(torch.allclose(p, q, atol=1e-5))
        for p, q in zip(ref.critic.parameters(), new.critic.parameters()):
            self.assertTrue(torch.allclose(p, q, atol=1e-5))
        self.assertAlmostEqual(float(ref.alpha), float(new.alpha), places=5)

    def test_full_state_resume_matches_uninterrupted(self):
        obs, act = spaces()
        data = fake_transitions(24, seed=4)

        def build():
            torch.manual_seed(5)
            ag = ScwmSAC(obs, act, 1, args(DEV), 5000001)
            m = GpuReplay(100, 8, DEV)
            for i, t in enumerate(data):
                m.push(*t, meta=meta(i))
            return ag, m

        a, ma = build()
        b, mb = build()
        for k in range(2):
            torch.manual_seed(k)
            a.update_parameters(ma, 8, k)
            torch.manual_seed(k)
            b.update_parameters(mb, 8, k)
        state = b.full_state_dict()
        rstate = mb.state_dict()
        c, mc = build()
        c.load_full_state_dict(state)
        mc.load_state_dict(rstate)
        for k in range(2, 4):
            torch.manual_seed(k)
            la = a.update_parameters(ma, 8, k)
            torch.manual_seed(k)
            lc = c.update_parameters(mc, 8, k)
            for x, y in zip(la, lc):
                self.assertAlmostEqual(x, y, places=5)




class ReplayNpz(unittest.TestCase):
    def test_npz_roundtrip_keeps_samples(self):
        import tempfile
        from scwm_sac import save_replay_npz, load_replay_npz
        a = GpuReplay(10, 5, DEV)
        for i, t in enumerate(fake_transitions(13, seed=9)):
            a.push(*t, meta=meta(i))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.npz")
            save_replay_npz(a, p)
            b = GpuReplay(10, 77, DEV)
            load_replay_npz(b, p, a.rng.getstate())
        self.assertEqual((len(a), a.position), (len(b), b.position))
        for x, y in zip(a.sample(6), b.sample(6)):
            self.assertTrue(torch.equal(x, y))

if __name__ == "__main__":
    unittest.main()
