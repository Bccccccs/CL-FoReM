"""T3-A01 tests of the semantic identity digest (host, stdlib only): it follows the ACTUAL file contents of the environment/task/control/model/
config closure and ignores only caches and the freeze record."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import task3_identity as I  # noqa: E402

MUT = {   # name -> (file, old, new, expected changed group): all shape-preserving edits of the real files
    "reward": ("src/modulation_rl/scripts/modulation/envs/combined_env.py", "return reward\n", "return reward + 1.0\n", "src:modulation_rl"),
    "termination": ("src/modulation_rl/scripts/modulation/envs/combined_env.py", "or (robot_info['nr_base_collisions'] >= self._ik_fail_thresh))",
                    "or (robot_info['nr_base_collisions'] >= 1))", "src:modulation_rl"),
    "cpp_control": ("src/modulation_rl/src/robot_env.cpp", "ik_options.return_approximate_solution = true;", "ik_options.return_approximate_solution = false;",
                    "src:modulation_rl"),
    "robot_model": ("src/husky_description/urdf/husky.urdf.xacro", '<mass value="46.034" />', '<mass value="60.0" />', "src:husky_description"),
    "launch_wiring": ("src/forem_husky/launch/husky_core.launch", 'name="pose_bridge"', 'name="pose_bridge2"', "src:forem_husky"),
    "control_config": ("config/task3/core_contract.yaml", "cmd_vel_timeout_s: 0.25", "cmd_vel_timeout_s: 0.5", "config:task3"),
}


class IdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = Path(tempfile.mkdtemp(prefix="identity-"))
        for rel in ("src", "config/task3", "scripts"):
            shutil.copytree(ROOT / rel, cls.td / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"), symlinks=True)
        cls.ros = cls.td / "ros_share"
        cls.base = I.semantic_identity(cls.td, cls.ros)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.td, ignore_errors=True)

    def test_copy_has_same_identity_as_original_tree(self):
        self.assertEqual(I.semantic_identity(ROOT, self.ros)["groups"]["src:modulation_rl"], self.base["groups"]["src:modulation_rl"])
        self.assertEqual(I.identity_diffs(I.semantic_identity(self.td, self.ros), self.base), [])

    def test_every_group_is_present_and_nonempty_or_declared_absent(self):
        g = self.base["groups"]
        self.assertEqual(set(g), {"src:" + p for p in I.SRC_PACKAGES} | {"config:task3"} | {"ros:" + p for p in I.ROS_PACKAGES}
                         | {"runtime:" + p for p in I.RUNTIME_FILES})
        for name, v in g.items():
            if name.startswith("ros:"):
                self.assertEqual(v, "absent")             # no ROS share dir on this path
            else:
                self.assertGreater(v["files"], 0, name)
                self.assertEqual(len(v["sha256"]), 64)

    def test_real_semantic_edits_change_the_expected_group_only(self):
        for name, (rel, old, new, group) in MUT.items():
            p = self.td / rel
            text = p.read_text(encoding="utf-8")
            self.assertIn(old, text, name)
            try:
                p.write_text(text.replace(old, new, 1), encoding="utf-8")
                changed = I.semantic_identity(self.td, self.ros)
                self.assertEqual(I.identity_diffs(changed, self.base), [group], name)
            finally:
                p.write_text(text, encoding="utf-8")
        self.assertEqual(I.identity_diffs(I.semantic_identity(self.td, self.ros), self.base), [])

    def test_caches_and_freeze_record_are_ignored_but_new_files_count(self):
        (self.td / "src/modulation_rl/__pycache__").mkdir(exist_ok=True)
        (self.td / "src/modulation_rl/__pycache__/x.cpython-310.pyc").write_bytes(b"x")
        (self.td / "config/task3/execution_freeze.json").write_text("{}")
        try:
            self.assertEqual(I.identity_diffs(I.semantic_identity(self.td, self.ros), self.base), [])
            (self.td / "src/modulation_rl/new_file.py").write_text("x = 1\n")
            self.assertEqual(I.identity_diffs(I.semantic_identity(self.td, self.ros), self.base), ["src:modulation_rl"])
        finally:
            (self.td / "config/task3/execution_freeze.json").unlink()
            (self.td / "src/modulation_rl/new_file.py").unlink(missing_ok=True)

    def test_system_ros_model_package_is_part_of_the_identity(self):
        pkg = self.ros / "ur_description"
        pkg.mkdir(parents=True)
        (pkg / "a.xacro").write_text("<robot/>")
        with_pkg = I.semantic_identity(self.td, self.ros)
        self.assertEqual(I.identity_diffs(with_pkg, self.base), ["ros:ur_description"])
        (pkg / "a.xacro").write_text("<robot name='x'/>")
        self.assertEqual(I.identity_diffs(I.semantic_identity(self.td, self.ros), with_pkg), ["ros:ur_description"])
        shutil.rmtree(self.ros)

    def test_missing_or_foreign_schema_identity_is_never_equal(self):
        self.assertEqual(len(I.identity_diffs(None, self.base)), 1)
        self.assertEqual(len(I.identity_diffs(dict(schema=0, groups={}), self.base)), 1)
        self.assertEqual(len(I.identity_diffs(self.base, dict(self.base, schema=2))), 1)


if __name__ == "__main__":
    unittest.main()
