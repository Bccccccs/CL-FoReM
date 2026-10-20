"""task3.5 tests: clock-regression guard of Task3Env, checkpoint reuse with the frozen observation contract, and static properties of the
run wrapper (own-process-only cleanup). Live lifecycle evidence: scripts/regress_task3_lifecycle.py and scripts/check_task3_clock.py."""
import os
import re
import sys
import types
import unittest

try:
    import ray  # noqa: F401
    import torch  # noqa: F401
    import numpy as np
except ImportError as e:  # pragma: no cover
    raise unittest.SkipTest("container python stack not available: %s" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
FOREM = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(FOREM, "scripts"))
sys.path.insert(0, os.path.join(FOREM, "src", "modulation_rl", "scripts"))
import task3_env as T  # noqa: E402


class FakeInner:
    def __init__(self):
        self.calls = 0

    def step(self, a):
        self.calls += 1
        info = dict(nr_kin_failures=0, nr_base_collisions=0, ee_done=False, kin_failure=False, base_collision=False)
        return (list(np.zeros(41)), np.zeros((120, 120, 1))), -0.1, False, info

    def reset(self):
        return (list(np.zeros(41)), np.zeros((120, 120, 1)))


class FakeRobotObs:
    joint_values = [0.0] * 6
    base_tf = [0.0] * 7


class ClockGuardTest(unittest.TestCase):
    def make(self, clock):
        fake_rospy = types.SimpleNamespace(get_time=lambda: clock["t"])
        sys.modules["rospy"] = fake_rospy                    # step() imports rospy lazily
        e = object.__new__(T.Task3Env)
        e.env = FakeInner()
        e.unwrapped_env = types.SimpleNamespace(prev_robot_obs=FakeRobotObs(),
                                                _robot=types.SimpleNamespace(get_joint_values_world=lambda: [0.0] * 6))
        e._episode_is_success = lambda *a: False
        e.pose_source = "gazebo_reference"
        e._episode = {"hash": "x"}
        e._steps = 0
        e._last_sim_time = clock["t"]
        e._invalid_reason = None
        return e

    def test_clock_reset_requires_new_episode(self):
        clock = {"t": 100.0}
        e = self.make(clock)
        try:
            e.step(np.zeros(3, np.float32))
            clock["t"] = 100.05
            e.step(np.zeros(3, np.float32))                  # normal progress is fine
            clock["t"] = 3.0                                 # simulation clock reset
            with self.assertRaises(RuntimeError) as cm:
                e.step(np.zeros(3, np.float32))
            self.assertIn("clock went backwards", str(cm.exception))
            calls = e.env.calls
            clock["t"] = 3.2                                 # even though time moves forward again, the episode stays invalid
            with self.assertRaises(RuntimeError):
                e.step(np.zeros(3, np.float32))
            self.assertEqual(e.env.calls, calls)             # nothing was sent to the simulation
        finally:
            sys.modules.pop("rospy", None)

    def test_small_time_jitter_is_not_a_reset(self):
        clock = {"t": 50.0}
        e = self.make(clock)
        try:
            e.step(np.zeros(3, np.float32))
            clock["t"] = 49.9995                             # < 1 ms backwards: sampling jitter, tolerated
            e.step(np.zeros(3, np.float32))
        finally:
            sys.modules.pop("rospy", None)


class FrozenObsCheckpointTest(unittest.TestCase):
    def test_checkpoint_reload_uses_frozen_obs(self):
        import tempfile
        import task3_sac_entry as E
        from gym import spaces
        from sac import SAC
        torch.manual_seed(0)
        obs = spaces.Tuple([spaces.Box(-100, 100, (41,), np.float32), spaces.Box(-1.1, 10.1, (120, 120, 1), np.float32)])
        act = spaces.Box(-1.0, 1.0, (3,), np.float32)
        cfg, sha = E.load_sac_config()
        cfg = dict(cfg, network=dict(cfg["network"], fcnet_hiddens=[32, 32, 256]))
        agent = SAC(obs, act, 1, E.build_sac_args(cfg, "cpu", 8), 5000001)
        contract = E.make_contract(obs, act, sha)
        path = os.path.join(tempfile.mkdtemp(), "c.pt")
        E.save_checkpoint_with_contract(agent, path, contract)
        # a different observation layout (40-dim robot state) must not load the frozen checkpoint
        obs40 = spaces.Tuple([spaces.Box(-100, 100, (40,), np.float32), obs[1]])
        other = SAC(obs40, act, 1, E.build_sac_args(cfg, "cpu", 8), 5000001)
        with self.assertRaises(ValueError):
            E.load_checkpoint_checked(other, path, E.make_contract(obs40, act, sha))
        # the matching layout loads and acts on a (41,) + (120,120,1) observation, but not on a mismatching one
        same = SAC(obs, act, 1, E.build_sac_args(cfg, "cpu", 8), 5000001)
        E.load_checkpoint_checked(same, path, contract, evaluate=True)
        a = same.select_action((np.zeros(41, np.float32), np.zeros((120, 120, 1), np.float32)), eval=True)
        self.assertEqual(a.shape, (3,))
        with self.assertRaises(Exception):
            same.select_action((np.zeros(40, np.float32), np.zeros((120, 120, 1), np.float32)), eval=True)


class WrapperStaticTest(unittest.TestCase):
    def test_foreign_process_not_stopped_by_design(self):
        sh = open(os.path.join(FOREM, "scripts", "run_task3_core.sh"), encoding="utf-8").read()
        self.assertIn("task0_proc.py foreign", sh)                  # refuses when ROS/Gazebo processes already exist
        self.assertIn("exit 10", sh)
        self.assertIn("task0_proc.py stop --dir", sh)               # identity-based stop of own processes only
        self.assertIsNone(re.search(r"\b(pkill|killall)\b", sh))    # never name-based
        self.assertIn("flock -n 9", sh)                             # shared single-simulation lock
        self.assertIn("[[ -e $log || -e $res ]]", sh)               # run-id evidence never overwritten


if __name__ == "__main__":
    unittest.main()
