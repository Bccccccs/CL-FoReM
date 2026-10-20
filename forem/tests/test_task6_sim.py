"""task6.1 sim routing and D12 contract; no simulator required."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import ray
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import scwm_env as S
import task3_env as T

class SimRouting(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch("rospy.get_param", return_value=False).start()
        patch("rospy.set_param").start()

    def test_only_three_sim_overrides(self):
        with patch.object(T, 'Task3Env') as ctor:
            e = S.ScwmEnv(world='sim', window_s=.02, fast_reset=True)
            self.assertEqual(ctor.call_args.kwargs['overrides'],
                             dict(world_type='sim', init_controllers=False, max_close_steps=500))
            self.assertIsNone(e.clock)
            self.assertIsNone(e.pacing)

    def test_sim_physical_is_na_without_service(self):
        with patch.object(T, 'Task3Env'):
            e = S.ScwmEnv(world='sim')
            with patch.object(e, 'physical_gripper_pose', side_effect=AssertionError('Gazebo accessed')):
                self.assertEqual(e.physical_outcome({}), dict(valid=False, success=None, reason='sim: no physics'))

    def test_gazebo_default_preserves_constructor(self):
        with patch.object(T, 'Task3Env') as ctor:
            S.ScwmEnv(seed=17)
            ctor.assert_called_once_with(seed=17, overrides=None)

    def test_d12_wrapper_defaults_and_override(self):
        import modulation.utils as U
        class Core:
            ikslack_dist=.1
            ikslack_rot_dist=.05
            def __init__(self, analytical): self.analytical=analytical
            def is_analytical_world(self): return self.analytical
        class Task:
            def __init__(self, core, **kw):
                self.core=core
                self.action_space=None
                self.observation_space=None
                self.reward_range=(-1,0)
                self.metadata={}
            def requires_simulator(self): return False
        with patch.object(U, 'CombinedEnv', Core), patch.dict(U.ALL_TASKS, {'probe': Task}):
            for analytical, key, expected in [(True,None,50),(False,None,500),(True,500,500)]:
                e=U.wrap_in_task(Core(analytical), 'probe', {'frame_skip':0}, max_close_steps=key)
                self.assertEqual(e._max_close_steps, expected)

    def test_d12_create_env_forward(self):
        import modulation.utils as U
        cfg,_=T.load_env_config(overrides=dict(world_type='sim',init_controllers=False,max_close_steps=500))
        with patch.object(U,'RobotEnv'), patch.object(U,'CombinedEnv'), patch.object(U,'wrap_in_task') as wrap:
            U.create_env(cfg, cfg['task'], cfg['node_handle'], False)
            self.assertEqual(wrap.call_args.kwargs['max_close_steps'],500)

if __name__ == '__main__': unittest.main()
