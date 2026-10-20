"""task3.3 reference-semantics tests (host-capable: ast + yaml only): reward / IK reward / termination / task code is identical to the
read-only reference, and the constants the reference code overrides are recorded in the task contract."""
import ast
import os
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
FOREM = os.path.abspath(os.path.join(HERE, ".."))
REF = os.path.abspath(os.path.join(FOREM, "..", "husky", "src", "modulation_rl", "scripts", "modulation", "envs"))
MINE = os.path.join(FOREM, "src", "modulation_rl", "scripts", "modulation", "envs")
CONTRACT = yaml.safe_load(open(os.path.join(FOREM, "config", "task3", "task_contract.yaml")))


def func_dump(path, names):
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef,)) and n.name in names:
            out[n.name] = ast.dump(n)
    return out


class ReferenceSemanticsTest(unittest.TestCase):
    @unittest.skipUnless(os.path.isdir(REF), "reference tree not present")
    def test_reward_components_preserved(self):
        # reward / IK reward / done logic are byte-identical in AST to the reference
        names = {"calculate_reward", "ik_reward", "step", "_to_agent_obs", "_convert_policy_to_env_actions", "reset", "check_collision", "calc_jumps"}
        a, b = func_dump(os.path.join(REF, "combined_env.py"), names), func_dump(os.path.join(MINE, "combined_env.py"), names)
        self.assertEqual(set(a), names)
        self.assertEqual(a, b)
        t_ref, t_mine = func_dump(os.path.join(REF, "tasks.py"), {"draw_goal", "reset", "step"}), func_dump(os.path.join(MINE, "tasks.py"), {"draw_goal", "reset", "step"})
        self.assertEqual(t_ref, t_mine)

    @unittest.skipUnless(os.path.isdir(REF), "reference tree not present")
    def test_overridden_task_constants_are_in_the_contract(self):
        src = open(os.path.join(MINE, "map.py"), encoding="utf-8").read()
        self.assertIn("self._obstacle_spacing = 3.0", src)
        self.assertIn("self.offset_std = 0.8", src)
        eo = CONTRACT["effective_override"]
        self.assertEqual(eo["SimpleObstacleMap._obstacle_spacing"], 3.0)
        self.assertEqual(eo["SimpleObstacleMap.offset_std"], 0.8)
        self.assertEqual(eo["MaxCloseStepsWrapper.max_close_steps"], 500)




if __name__ == "__main__":
    unittest.main()
