"""Counterexamples change real Task3 call sites or the pinned VIO callback.
The positive baseline check must pass; runtime Task3 must fail, never masquerade as Task4.
"""
import copy
import importlib.util
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/audit_task4_inputs.py'

class Permissions(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), 'Task4 permission auditor is not implemented')
        spec = importlib.util.spec_from_file_location('task4_audit', SCRIPT)
        self.audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.audit)
        self.p = yaml.safe_load((ROOT / 'config/task4/protocol.yaml').read_text())
        self.s = yaml.safe_load((ROOT / 'config/task4/sensors.yaml').read_text())

    def test_protocol_passes(self):
        self.assertEqual(self.audit.validate_protocol(self.p, self.s), [])

    def test_p3d_camera_odom_rejected(self):
        for topic in ['/ground_truth/state', '/camera/odom/sample', '/t265/odom/sample', '/gazebo/model_states']:
            s = copy.deepcopy(self.s)
            s['imu']['topic'] = topic
            self.assertIn('forbidden_pose_input', self.audit.validate_protocol(self.p, s))

    def test_imu_absolute_orientation_not_used(self):
        src = ROOT / self.p['estimator']['reference_callback']
        text = src.read_text()
        self.assertEqual(self.audit.scan_source(text, 'imu_cpp'), [])
        self.assertIn('imu_absolute_orientation', self.audit.scan_source(
            text.replace('message.wm << msg->angular_velocity.x', 'auto leaked = msg->orientation.w;\n  message.wm << msg->angular_velocity.x'), 'imu_cpp'))
        p = copy.deepcopy(self.p)
        p['permissions']['imu_fields'].append('orientation')
        self.assertIn('imu_absolute_orientation', self.audit.validate_protocol(p, self.s))

    def test_truth_relative_goal_rejected(self):
        text = (ROOT / 'src/modulation_rl/scripts/modulation/envs/combined_env.py').read_text()
        self.assertEqual(self.audit.scan_source(text, 'policy_python'), [])
        text = text.replace('world_to_relative_tf(robot_obs.base_tf, list(ee_plan_meters[-1]))',
                            'world_to_relative_tf(self.evaluation_truth()[1], list(ee_plan_meters[-1]))')
        self.assertIn('truth_in_policy', self.audit.scan_source(text, 'policy_python'))

    def test_two_pose_publishers_rejected(self):
        text = (ROOT / 'src/forem_husky/launch/husky_core.launch').read_text()
        text = text.replace('default="/ground_truth/state"', 'default="/task4/estimate/base"').replace('default="gazebo_reference"', 'default="openvins_stereo_imu"')
        self.assertEqual(self.audit.scan_source(text, 'launch_xml'), [])
        duplicate = '<node name="second_bridge" pkg="forem_husky" type="pose_bridge.py" />'
        self.assertIn('two_pose_publishers', self.audit.scan_source(text.replace('</launch>', duplicate + '</launch>'), 'launch_xml'))

    def test_current_task3_is_not_task4(self):
        text = (ROOT / 'scripts/task3_env.py').read_text()
        self.assertIn('truth_source_identity', self.audit.scan_source(text, 'policy_python'))
        launch = (ROOT / 'src/forem_husky/launch/husky_core.launch').read_text()
        self.assertIn('forbidden_pose_input', self.audit.scan_source(launch, 'launch_xml'))

    def test_public_bootstrap_cannot_be_truth_feedback(self):
        p = copy.deepcopy(self.p)
        p['initialization']['anchor_source'] = '/gazebo/model_states'
        self.assertIn('truth_bootstrap', self.audit.validate_protocol(p, self.s))
        p = copy.deepcopy(self.p)
        p['initialization']['policy_actions_during_bootstrap'] = True
        self.assertIn('bootstrap_policy_actions', self.audit.validate_protocol(p, self.s))

    def test_budget_requires_pilot_freeze(self):
        p = copy.deepcopy(self.p)
        p['budget']['formal']['enabled'] = True
        self.assertIn('formal_budget_unfrozen', self.audit.validate_protocol(p, self.s))

    def test_acceptance_and_all_330_hashes(self):
        self.assertEqual(self.audit.verify_accepted_core(ROOT, self.p), [])

if __name__ == '__main__':
    unittest.main()

class AcceptedArchiveDeltas(unittest.TestCase):
 def test_real_immutable_baseline_and_declared_delta(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('task4_audit',SCRIPT);audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
  p=yaml.safe_load((ROOT/'config/task4/protocol.yaml').read_text())
  self.assertEqual(audit.verify_accepted_core(ROOT,p),[])
