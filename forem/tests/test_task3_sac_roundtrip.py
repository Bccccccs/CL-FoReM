"""task3.4 tests of the plain-SAC interface (no ROS, CPU): update, checkpoint contract, deterministic round trip, truncation mask.
Needs the container python (ray, torch, gym 0.18, the forem pybind-free SAC modules); skipped elsewhere."""
import os
import sys
import tempfile
import unittest

try:
    import ray  # noqa: F401  (must precede torch)
    import torch
    import numpy as np
    from gym import spaces
except ImportError as e:  # pragma: no cover
    raise unittest.SkipTest("container python stack not available: %s" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
FOREM = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(FOREM, "scripts"))
sys.path.insert(0, os.path.join(FOREM, "src", "modulation_rl", "scripts"))
import task3_sac_entry as E  # noqa: E402
from replay_memory import ReplayMemory  # noqa: E402
from sac import SAC  # noqa: E402


def spaces_():
    obs = spaces.Tuple([spaces.Box(low=-100, high=100, shape=[41], dtype=np.float32),
                        spaces.Box(low=-1.1, high=10.1, shape=[120, 120, 1], dtype=np.float32)])
    act = spaces.Box(low=-1.0, high=1.0, shape=[3], dtype=np.float32)
    return obs, act


def make_agent(seed=0, hidden=(32, 32, 256)):   # QNetwork hardcodes a 256-wide last layer
    torch.manual_seed(seed)
    obs, act = spaces_()
    cfg, sha = E.load_sac_config()
    cfg = dict(cfg)
    cfg["network"] = dict(cfg["network"], fcnet_hiddens=list(hidden))
    args = E.build_sac_args(cfg, "cpu", 8)
    agent = SAC(obs, act, 1, args, 5000001)
    return agent, obs, act, cfg, sha


def fill(mem, n=24, seed=0):
    r = np.random.RandomState(seed)
    for i in range(n):
        s_m, s_r = r.rand(120, 120, 1).astype(np.float32), r.randn(41).astype(np.float32)
        n_m, n_r = r.rand(120, 120, 1).astype(np.float32), r.randn(41).astype(np.float32)
        mem.push(s_m, s_r, r.uniform(-1, 1, 3).astype(np.float32), float(r.randn()), n_m, n_r, E.make_mask(i % 7 == 6))


class SacTest(unittest.TestCase):
    def test_no_prior_checkpoint_required(self):
        # a freshly built agent runs the ordinary update with NO prior agent and NO checkpoint file on disk
        agent, obs, act, cfg, sha = make_agent()
        mem = ReplayMemory(100, 0)
        fill(mem)
        losses = agent.update_parameters(mem, 8, 0)
        self.assertEqual(len(losses), 5)
        self.assertTrue(all(np.isfinite(x) for x in losses))
        # the entry's config refuses a prior-based update
        bad = dict(cfg, algorithm=dict(cfg["algorithm"], update_function="update_parameters_modified"))
        import yaml
        p = os.path.join(tempfile.mkdtemp(), "sac.yaml")
        yaml.safe_dump(bad, open(p, "w"))
        with self.assertRaises(ValueError):
            E.load_sac_config(p)

    def test_modified_update_needs_prior_and_differs(self):
        # documents the reference difference: update_parameters_modified takes a frozen prior agent and adds its log-prob terms
        agent, obs, act, cfg, sha = make_agent(seed=1)
        mem = ReplayMemory(100, 0)
        fill(mem)
        with self.assertRaises(TypeError):
            agent.update_parameters_modified(mem, 8, 0)           # prior_agent is a required argument
        import copy
        a1 = copy.deepcopy(agent)
        a2 = copy.deepcopy(agent)
        import random
        random.seed(5)
        plain = a1.update_parameters(mem, 8, 0)
        prior, _, _, _, _ = make_agent(seed=2)
        random.seed(5)
        mod = a2.update_parameters_modified(mem, 8, 0, prior)
        self.assertNotEqual(plain[2], mod[2])                      # policy loss differs once the prior terms are added

    def test_checkpoint_contract_mismatch_rejected(self):
        agent, obs, act, cfg, sha = make_agent()
        contract = E.make_contract(obs, act, sha)
        d = tempfile.mkdtemp()
        path = os.path.join(d, "c.pt")
        E.save_checkpoint_with_contract(agent, path, contract, meta=dict(steps=0))
        other, *_ = make_agent(seed=3)
        E.load_checkpoint_checked(other, path, contract)           # same contract loads
        for mut in (dict(obs_robot_dim=40), dict(action_dim=2), dict(map_shape=[60, 60, 1]), dict(sac_config_sha256="0" * 64),
                    dict(task_contract_sha256="0" * 64), dict(pose_source="estimator"), dict(update_function="other")):
            with self.assertRaises(ValueError, msg=str(mut)):
                E.load_checkpoint_checked(other, path, dict(contract, **mut))
        # source hash change (a different sac.py/model.py) is refused too
        sh = dict(contract["source_sha256"])
        sh["sac.py"] = "0" * 64
        with self.assertRaises(ValueError):
            E.load_checkpoint_checked(other, path, dict(contract, source_sha256=sh))
        # a legacy checkpoint (reference format, no contract) is refused
        legacy = os.path.join(d, "legacy.pt")
        agent.save_checkpoint("x", ckpt_path=legacy)
        with self.assertRaises(ValueError):
            E.load_checkpoint_checked(other, legacy, contract)

    def test_checkpoint_bound_to_actual_environment_control_model_files(self):
        # T3-A01: shape-preserving edits of reward/termination (python), C++ control, robot model, launch wiring and control config in a COPY of
        # the tree change the contract and the old checkpoint is refused; the unmodified copy gives the same contract and loads.
        import shutil
        sys.path.insert(0, os.path.join(FOREM, "tests"))
        from test_task3_identity import MUT
        agent, obs, act, cfg, sha = make_agent()
        contract = E.make_contract(obs, act, sha)
        d = tempfile.mkdtemp()
        copy = os.path.join(d, "tree")
        for rel in ("src", os.path.join("config", "task3"), "scripts"):
            shutil.copytree(os.path.join(FOREM, rel), os.path.join(copy, rel), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"), symlinks=True)
        path = os.path.join(d, "c.pt")
        E.save_checkpoint_with_contract(agent, path, contract)
        other, *_ = make_agent(seed=3)
        same = E.make_contract(obs, act, sha, root=copy)
        self.assertEqual(same["semantic_identity"], contract["semantic_identity"])
        E.load_checkpoint_checked(other, path, same)                       # same contract: saves and loads consistently
        for name, (rel, old, new, group) in MUT.items():
            p = os.path.join(copy, rel)
            text = open(p, encoding="utf-8").read()
            try:
                open(p, "w", encoding="utf-8").write(text.replace(old, new, 1))
                changed = E.make_contract(obs, act, sha, root=copy)
                self.assertEqual((changed["obs_robot_dim"], changed["map_shape"], changed["action_dim"]),
                                 (contract["obs_robot_dim"], contract["map_shape"], contract["action_dim"]))   # shapes untouched
                with self.assertRaises(ValueError, msg=name) as cm:
                    E.load_checkpoint_checked(other, path, changed)
                self.assertIn(group, str(cm.exception), name)
            finally:
                open(p, "w", encoding="utf-8").write(text)

    def test_legacy_contract_without_semantic_identity_is_refused_not_upgraded(self):
        agent, obs, act, cfg, sha = make_agent()
        contract = E.make_contract(obs, act, sha)
        legacy = {k: v for k, v in contract.items() if k != "semantic_identity"}
        legacy["schema"] = 1                                             # what the task3.4/3.5 code wrote
        d = tempfile.mkdtemp()
        path = os.path.join(d, "legacy.pt")
        E.save_checkpoint_with_contract(agent, path, legacy)
        other, *_ = make_agent(seed=3)
        with self.assertRaises(ValueError) as cm:
            E.load_checkpoint_checked(other, path, contract)
        self.assertIn("semantic identity", str(cm.exception))
        # a schema-2 contract whose identity block was dropped is refused as well
        broken = dict(contract)
        broken.pop("semantic_identity")
        E.save_checkpoint_with_contract(agent, path, broken)
        with self.assertRaises(ValueError):
            E.load_checkpoint_checked(other, path, contract)

    def test_deterministic_eval_roundtrip(self):
        agent, obs, act, cfg, sha = make_agent(seed=4)
        mem = ReplayMemory(100, 0)
        fill(mem)
        agent.update_parameters(mem, 8, 0)
        contract = E.make_contract(obs, act, sha)
        path = os.path.join(tempfile.mkdtemp(), "c.pt")
        E.save_checkpoint_with_contract(agent, path, contract)
        other, *_ = make_agent(seed=9)
        E.load_checkpoint_checked(other, path, contract, evaluate=True)
        agent.policy.eval()
        r = np.random.RandomState(1)
        for _ in range(3):
            st = (r.randn(41).astype(np.float32), r.rand(120, 120, 1).astype(np.float32))
            np.testing.assert_allclose(agent.select_action(st, eval=True), other.select_action(st, eval=True), atol=1e-6)
            self.assertTrue(np.all(np.abs(other.select_action(st, eval=True)) <= 1.0))

    def test_truncation_bootstrap_contract(self):
        # reference semantics: mask = float(not done) for every done; truncation (max_close_steps) is NOT bootstrapped
        self.assertEqual(E.make_mask(True, truncated=True), 0.0)
        self.assertEqual(E.make_mask(True, truncated=False), 0.0)
        self.assertEqual(E.make_mask(False, truncated=False), 1.0)
        mem = ReplayMemory(10, 0)
        fill(mem, 7)
        self.assertEqual(mem.buffer[6][6], 0.0)
        self.assertEqual(mem.buffer[0][6], 1.0)

    def test_finite_transition_gate(self):
        s = (np.zeros(41, np.float32), np.zeros((120, 120, 1), np.float32))
        a = np.zeros(3, np.float32)
        self.assertTrue(E.finite_transition(s, a, 0.5, s, 1.0))
        bad = (np.full(41, np.nan, np.float32), s[1])
        self.assertFalse(E.finite_transition(bad, a, 0.5, s, 1.0))
        self.assertFalse(E.finite_transition(s, a, float("inf"), s, 1.0))
        self.assertFalse(E.finite_transition(s, a, 0.5, s, 0.5))

    def test_train_budget_must_be_explicit(self):
        with self.assertRaises(ValueError):
            E.Budget(None, 10)
        with self.assertRaises(ValueError):
            E.Budget(10, None)
        with self.assertRaises(ValueError):
            E.Budget(0, 10)
        b = E.Budget(5, 100)
        self.assertFalse(b.exhausted(4))
        self.assertTrue(b.exhausted(5))


if __name__ == "__main__":
    unittest.main()
