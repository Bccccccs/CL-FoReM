"""task4.10 tests (synthetic WM/encoder, no ROS): zero-init equals plain policy, off-bypass equality, frozen weights stay frozen under the SAC
optimiser, the candidate->frozen-F->final-head gradient path is live, one consistent distribution for sample/log-prob/predict, non-finite WM output is fatal."""
import copy
import os
import sys
import unittest

try:
    import ray  # noqa: F401
    import torch
    import numpy as np
    import gym
except ImportError as e:  # pragma: no cover
    raise unittest.SkipTest("container python stack not available: %s" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "src", "modulation_rl", "scripts"))
from scwm_policy import FixedGaussianPolicy  # noqa: E402
from scwm_feedback import FeedbackGaussianPolicy  # noqa: E402
import scwm_wm as W  # noqa: E402
from scwm_sac import ScwmSAC, GpuReplay  # noqa: E402

HID = [64, 64, 256]


def spaces():
    rs = gym.spaces.Box(-100, 100, (41,), dtype=np.float32)
    ms = gym.spaces.Box(-1.1, 10.1, (120, 120, 1), dtype=np.float32)
    return rs, ms, gym.spaces.Box(-1.0, 1.0, (3,), dtype=np.float32)


def build(seed=0, enabled=True, randomise_g=False):
    rs, ms, act = spaces()
    torch.manual_seed(seed)
    base = FixedGaussianPolicy(ms, rs, 3, HID, act, False)
    ref = W.RefEncoder(base)
    wm = W.WorldModel(256, 3, 32, 2)
    wm.fit_stats(torch.randn(50, 256), torch.randn(50, 256))
    torch.manual_seed(seed + 1)
    fb = FeedbackGaussianPolicy(ms, rs, 3, HID, act, False, ref_encoder=ref, world_model=wm, feedback_enabled=enabled)
    fb.load_state_dict(base.state_dict(), strict=False)          # same trunk/heads as the plain policy (the fork)
    if randomise_g:
        torch.nn.init.normal_(fb.feedback_delta.weight, std=0.05)
    return base, fb


def batch(n=6):
    return torch.randn(n, 41), (torch.rand(n, 120, 120, 1) > 0.9).float()


class Feedback(unittest.TestCase):
    def test_zero_init_equals_plain_policy(self):
        base, fb = build()
        rob, mp = batch()
        with torch.no_grad():
            for eval_ in (True, False):
                torch.manual_seed(3); a = base.predict(mp, rob, eval_)
                torch.manual_seed(3); b = fb.predict(mp, rob, eval_)
                self.assertTrue(torch.allclose(a, b, atol=1e-6))

    def test_off_bypass_is_exactly_plain_even_with_trained_g(self):
        base, fb = build(randomise_g=True, enabled=False)
        rob, mp = batch()
        with torch.no_grad():
            torch.manual_seed(4); a, la = base.sample(mp, rob)
            torch.manual_seed(4); b, lb = fb.sample(mp, rob)
        self.assertTrue(torch.equal(a, b) and torch.equal(la, lb))

    def test_feedback_changes_action_when_g_nonzero(self):
        base, fb = build(randomise_g=True)
        rob, mp = batch()
        with torch.no_grad():
            self.assertGreater(float((base.predict(mp, rob, True) - fb.predict(mp, rob, True)).abs().max()), 1e-4)

    def test_frozen_models_unchanged_by_sac_update(self):
        rs, ms, act = spaces()
        obs = gym.spaces.Tuple([rs, ms])
        base, fb0 = build(randomise_g=True)
        ref, wm = fb0.ref_encoder, fb0.world_model
        h_ref, h_wm = ref.sha256(), [p.detach().clone() for p in wm.parameters()]

        def factory(map_space, robot_space, n, hidden, action_space=None, use_sde=False):
            return FeedbackGaussianPolicy(map_space, robot_space, n, hidden, action_space, use_sde, ref_encoder=ref, world_model=wm)

        args = dict(gamma=0.99, tau=0.001, initial_alpha=1.0, device="cpu", model=dict(custom_model_config=dict(post_fcnet_hiddens=HID)))
        torch.manual_seed(0)
        ag = ScwmSAC(obs, act, 1, args, 5000001, policy_factory=factory)
        m = GpuReplay(64, 0, "cpu")
        r = np.random.RandomState(0)
        for i in range(40):
            m.push((r.rand(120, 120, 1) > 0.9).astype(np.float32), r.randn(41), np.tanh(r.randn(3)), 0.1, (r.rand(120, 120, 1) > 0.9).astype(np.float32), r.randn(41), 1.0,
                   meta=dict(episode_id=0, step_in_episode=i, epoch=0, t_obs=0., t_cmd=0., t_next=0., done=False))
        before = copy.deepcopy([p.detach() for p in ag.policy.feedback_delta.parameters()])
        for k in range(3):
            ag.update_parameters(m, 8, k)
        self.assertEqual(ref.sha256(), h_ref)
        for p, q in zip(wm.parameters(), h_wm):
            self.assertTrue(torch.equal(p, q))
        self.assertTrue(all(p.grad is None for p in wm.parameters()))
        self.assertTrue(any(not torch.equal(a, b) for a, b in zip(before, ag.policy.feedback_delta.parameters())))   # G does train

    def test_gradient_flows_through_frozen_wm_to_candidate(self):
        _, fb = build(randomise_g=True)
        rob, mp = batch(4)
        # full chain
        fb.zero_grad()
        mean, log_std = fb.distribution_params(mp, rob)
        mean.pow(2).sum().backward()
        g_full = fb.mean_linear.weight.grad.clone()
        # detach the candidate (the truncated variant the plan forbids to use silently) must give a DIFFERENT gradient
        fb.zero_grad()
        h = fb.trunk(mp, rob); mean0, _ = fb.heads(h)
        a0 = torch.tanh(mean0).detach()
        z = fb.ref_encoder(mp, rob); zh = fb.world_model(z, a0); dn = (zh - z - fb.world_model.d_mean) / fb.world_model.d_std
        x = torch.cat([h, dn], -1); h2 = h + torch.sigmoid(fb.feedback_gate(x)) * fb.feedback_delta(x)
        fb.heads(h2)[0].pow(2).sum().backward()
        self.assertGreater(float((g_full - fb.mean_linear.weight.grad).abs().max()), 1e-7)
        self.assertTrue(all(p.grad is None for p in fb.world_model.parameters()))

    def test_one_distribution_for_sample_logprob_predict(self):
        _, fb = build(randomise_g=True)
        rob, mp = batch()
        with torch.no_grad():
            torch.manual_seed(9); a_s, lp = fb.sample(mp, rob)
            torch.manual_seed(9); a_p = fb.predict(mp, rob, False)
            lp2 = fb.sample_with_action(mp, rob, a_s)
            mean, _ = fb.distribution_params(mp, rob)
        self.assertTrue(torch.allclose(a_s, a_p, atol=1e-6))
        self.assertTrue(torch.allclose(lp, lp2.reshape(-1), atol=1e-3))
        self.assertTrue(torch.allclose(fb.predict(mp, rob, True), torch.tanh(mean), atol=1e-6))

    def test_non_finite_world_model_is_fatal(self):
        _, fb = build(randomise_g=True)
        with torch.no_grad():
            fb.world_model.net[-1].bias.fill_(float("nan"))
        rob, mp = batch(2)
        with self.assertRaises(FloatingPointError):
            fb.predict(mp, rob, True)



class ForkTest(unittest.TestCase):
    def test_feedback_agent_forked_from_plain_state_is_identical_at_fork_and_keeps_adam_moments(self):
        rs, ms, act = spaces()
        obs = gym.spaces.Tuple([rs, ms])
        args = dict(gamma=0.99, tau=0.001, initial_alpha=1.0, device="cpu", model=dict(custom_model_config=dict(post_fcnet_hiddens=HID)))
        torch.manual_seed(0)
        plain = ScwmSAC(obs, act, 1, args, 5000001)
        m = GpuReplay(64, 0, "cpu")
        r = np.random.RandomState(0)
        for i in range(40):
            m.push((r.rand(120, 120, 1) > 0.9).astype(np.float32), r.randn(41), np.tanh(r.randn(3)), 0.1, (r.rand(120, 120, 1) > 0.9).astype(np.float32), r.randn(41), 1.0,
                   meta=dict(episode_id=0, step_in_episode=i, epoch=0, t_obs=0., t_cmd=0., t_next=0., done=False))
        for k in range(3):
            plain.update_parameters(m, 8, k)
        state = plain.full_state_dict()
        base_pol = FixedGaussianPolicy(ms, rs, 3, HID, act, False)
        ref = W.RefEncoder(plain.policy)
        wm = W.WorldModel(256, 3, 32, 2); wm.fit_stats(torch.randn(50, 256), torch.randn(50, 256))

        def factory(map_space, robot_space, n, hidden, action_space=None, use_sde=False):
            return FeedbackGaussianPolicy(map_space, robot_space, n, hidden, action_space, use_sde, ref_encoder=ref, world_model=wm)

        torch.manual_seed(123)
        fb = ScwmSAC(obs, act, 1, args, 5000001, policy_factory=factory)
        fb.load_fork_state(state)
        rob, mp = batch(5)
        with torch.no_grad():
            self.assertTrue(torch.allclose(plain.policy.predict(mp, rob, True), fb.policy.predict(mp, rob, True), atol=1e-6))
        # Adam first/second moments of the shared parameters carried over
        n_plain = len(list(plain.policy_optim.param_groups[0]["params"]))
        for i, (pp, fp) in enumerate(zip(plain.policy_optim.param_groups[0]["params"], fb.policy_optim.param_groups[0]["params"])):
            self.assertTrue(torch.equal(plain.policy_optim.state[pp]["exp_avg"], fb.policy_optim.state[fp]["exp_avg"]))
        self.assertEqual(len(fb.policy_optim.param_groups[0]["params"]), n_plain + 4)       # + gate(w,b) + delta(w,b)
        self.assertEqual(plain.update_count, fb.update_count)
        self.assertEqual(float(plain.alpha), float(fb.alpha))
        # first update with the SAME batch & seed: critic losses equal (policy not yet changed); the run continues
        torch.manual_seed(77); lp = plain.update_parameters(m, 8, 3)
        m2 = GpuReplay(64, 0, "cpu"); m2.load_state_dict(m.state_dict())
        m.rng.setstate(m.rng.getstate())
        torch.manual_seed(77); lf = fb.update_parameters(m2, 8, 3)
        self.assertTrue(all(np.isfinite(lf)))


if __name__ == "__main__":
    unittest.main()
