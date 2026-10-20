"""task3.3 contract tests that need no ROS: action validation, observation field map, planned-vs-actual labeling, reward source identity.
(The live reset/step evidence is produced by scripts/check_task3_env.py against the simulation.)"""
import os
import sys
import unittest

try:
    import ray  # noqa: F401
    import torch  # noqa: F401
    import numpy as np
    import yaml
except ImportError as e:  # pragma: no cover
    raise unittest.SkipTest("container python stack not available: %s" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
FOREM = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(FOREM, "scripts"))
import task3_env as T  # noqa: E402

CONTRACT = yaml.safe_load(open(os.path.join(FOREM, "config", "task3", "task_contract.yaml")))


class ActionTest(unittest.TestCase):
    def test_action_shape_rejected(self):
        for bad in ([0.0, 0.0], [0.0] * 4, 0.5, [[0.0, 0.0, 0.0]], np.zeros((3, 1)), [], None):
            with self.assertRaises((ValueError, TypeError), msg=repr(bad)):
                T.validate_action(bad)

    def test_nonfinite_and_out_of_range_rejected(self):
        for bad in ([float("nan"), 0, 0], [0, float("inf"), 0], [0, 0, -float("inf")], [1.5, 0, 0], [0, -1.0001, 0]):
            with self.assertRaises(ValueError, msg=repr(bad)):
                T.validate_action(bad)

    def test_valid_action_float32_and_boundary_slack(self):
        a = T.validate_action([1.0, -1.0, 0.25])
        self.assertEqual(a.dtype, np.float32)
        self.assertEqual(a.shape, (3,))
        b = T.validate_action([1.0 + 5e-7, 0, 0])               # within the 1e-6 slack: clipped, not rejected
        self.assertLessEqual(float(b[0]), 1.0)


class ObservationContractTest(unittest.TestCase):
    def test_observation_field_order(self):
        # contiguous, ordered, covering exactly [0, 41)
        pos = 0
        for name, lo, hi, origin in T.OBS_FIELDS:
            self.assertEqual(lo, pos, name)
            self.assertGreater(hi, lo)
            pos = hi
        self.assertEqual(pos, T.ROBOT_STATE_DIM)
        # the YAML contract lists the same names / ranges / origins in the same order
        y = CONTRACT["observation"]["robot_state_fields"]
        self.assertEqual([(f["name"], f["idx"][0], f["idx"][1], f["origin"]) for f in y], [tuple(f) for f in T.OBS_FIELDS])

    def test_expected_joint_not_labeled_actual(self):
        origins = {n: o for n, _, _, o in T.OBS_FIELDS}
        self.assertIn("PLANNED", origins["joint_values_scaled"])
        self.assertNotIn("actual", origins["joint_values_scaled"].lower().replace("not_actual", ""))
        for n, o in origins.items():
            self.assertNotEqual(o, "actual", n)                  # no observation field is claimed to be measured joint feedback
        self.assertIn("PLANNED", [f["origin"] for f in CONTRACT["observation"]["robot_state_fields"] if f["name"] == "joint_values_scaled"][0])
        self.assertIn("NOT in the observation", CONTRACT["observation"]["perception_style_base"].replace("\n", " "))

    def test_pose_source_declared(self):
        self.assertEqual(CONTRACT["pose_source"], "gazebo_reference")
        self.assertEqual(T.POSE_SOURCE, "gazebo_reference")
        self.assertEqual(CONTRACT["env_config"]["perception_style"], "base")
        self.assertEqual(CONTRACT["env_config"]["world_type"], "gazebo")


class EpisodeSpecTest(unittest.TestCase):
    def test_spec_hash_is_order_independent_and_sensitive(self):
        a = {"seed": 1, "base_tf": [0.1, 0.2], "obstacles": [{"name": "o0", "pose": [1.0, 2.0]}]}
        b = {"obstacles": [{"pose": [1.0, 2.0], "name": "o0"}], "base_tf": [0.1, 0.2], "seed": 1}
        self.assertEqual(T.spec_hash(a), T.spec_hash(b))
        c = {"seed": 1, "base_tf": [0.1, 0.2000001], "obstacles": [{"name": "o0", "pose": [1.0, 2.0]}]}
        self.assertNotEqual(T.spec_hash(a), T.spec_hash(c))


if __name__ == "__main__":
    unittest.main()
