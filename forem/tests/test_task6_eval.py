"""CLI routing regression: ROS/Gazebo and checkpoint I/O are external boundaries."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import ray  # import before torch / pybindings
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import eval_task6_final as E
from task3_env import load_env_config


class EvaluationOptions(unittest.TestCase):
    def run_cli(self, world='gazebo', extra=()):
        configs, calls = [], []
        def make_env(seed=0, **kwargs):
            calls.append(dict(seed=seed, **kwargs))
            overrides = kwargs.get('overrides')
            if kwargs.get('world') == 'sim':
                overrides = dict(overrides or {}, world_type='sim', init_controllers=False,
                                 max_close_steps=kwargs['max_close_steps'])
            cfg, _ = load_env_config(overrides=overrides)
            configs.append(cfg)
            robot = SimpleNamespace(execute_style=cfg['execute_style'],
                                    rate=SimpleNamespace(sleep_dur=SimpleNamespace(to_sec=lambda: cfg['time_step'])))
            base = SimpleNamespace(cfg=cfg, env=SimpleNamespace(_max_close_steps=500),
                                   unwrapped_env=SimpleNamespace(_robot=robot, _ik_fail_thresh=cfg['ik_fail_thresh']))
            return SimpleNamespace(base=base, clock=None, observation_space=None, action_space=None,
                                   episode_spec={'hash': 'scene'}, close=lambda: None)
        policy = SimpleNamespace(load_state_dict=lambda s: None, eval=lambda: None)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'eval.json'
            argv = ['eval_task6_final.py', '--world', world, '--policy', 'unused.pt',
                    '--seeds', '2001', '--out', str(out), *extra]
            with patch.object(sys, 'argv', argv), patch.object(E, 'ScwmEnv', side_effect=make_env), \
                 patch.object(E, 'ScwmSAC', return_value=SimpleNamespace(policy=policy)), \
                 patch.object(E.torch, 'load', return_value={}), \
                 patch.object(E, 'run_eval', return_value=[dict(seed=2001, steps=21, done=True,
                     internal_success=False, physical_success=False, nr_kin_failures=20)]), \
                 contextlib.redirect_stdout(io.StringIO()):
                E.main()
            return configs[0], calls[0], json.loads(out.read_text())

    def test_default_gazebo_matches_original_config_and_constructor(self):
        cfg, call, result = self.run_cli()
        original, _ = load_env_config()
        self.assertEqual(cfg, original)
        self.assertEqual(call, {'seed': 0})
        self.assertEqual(result['effective_config'], dict(execute_style='direct', ik_fail_thresh=20,
                          time_step=.02, max_close_steps=500, window_s=None))

    def test_gazebo_override_changes_only_two_contract_keys(self):
        cfg, _, result = self.run_cli(extra=['--execute_style', 'track', '--ik_fail_thresh', '50'])
        original, _ = load_env_config()
        self.assertEqual({k for k in cfg if cfg[k] != original[k]}, {'execute_style', 'ik_fail_thresh'})
        self.assertEqual((cfg['execute_style'], cfg['ik_fail_thresh']), ('track', 50))
        self.assertEqual(result['effective_config']['ik_fail_thresh'], 50)
        self.assertEqual(result['effective_config']['execute_style'], 'track')

    def test_each_override_can_be_used_independently(self):
        for extra, key, want in [(['--execute_style', 'track'], 'execute_style', 'track'),
                                 (['--ik_fail_thresh', '50'], 'ik_fail_thresh', 50)]:
            with self.subTest(key=key):
                cfg, _, _ = self.run_cli(extra=extra)
                original, _ = load_env_config()
                self.assertEqual({k for k in cfg if cfg[k] != original[k]}, {key})
                self.assertEqual(cfg[key], want)

    def test_sim_ignores_gazebo_options_and_preserves_original_config(self):
        before, before_call, _ = self.run_cli(world='sim')
        after, after_call, _ = self.run_cli(world='sim', extra=['--execute_style', 'track', '--ik_fail_thresh', '50'])
        self.assertEqual(after, before)
        self.assertEqual(after_call, before_call)
        self.assertEqual(before_call, {'seed': 0, 'world': 'sim', 'max_close_steps': 500})


if __name__ == '__main__':
    unittest.main()
