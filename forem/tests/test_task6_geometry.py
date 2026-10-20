"""D20: preserve real map RNG stream and all fields other than obstacle geometry."""
import ray
import sys,unittest,ast
from pathlib import Path
from unittest.mock import patch
import numpy as np
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
import task3_env
from modulation.envs import map as M
import scwm_env as S

class Geometry(unittest.TestCase):
    def draw(self,seed,force=None,legacy=False):
        with patch.object(M.rospy,'get_param',side_effect=lambda key,default=None: force if key=='/forem/force_rectangle_obstacles' and force is not None else default):
            m=M.SimpleObstacleMap(.025,.025,'sim','base_link',.3)
        self.assertEqual(m.force_rectangle_obstacles,bool(force))
        m.np_random=np.random.RandomState(seed)
        base=m._draw_initial_base_pose()
        if legacy:
            path=root/'results/task6/t6.1-baseline/original/src/modulation_rl/scripts/modulation/envs/map.py'
            tree=ast.parse(path.read_text())
            c=next(c for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='SimpleObstacleMap')
            fn=next(x for x in c.body if isinstance(x,ast.FunctionDef) and x.name=='get_varying_scene_objects')
            ns=dict(vars(M));exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'),ns)
            objects=ns[fn.name](m)
        else: objects=m.get_varying_scene_objects()
        fields=[];geometries=[]
        for o in objects:
            p=o.pose;w=o.world_object
            fields.append((o.name,w.x,w.y,w.z,p.position.x,p.position.y,p.position.z,p.orientation.x,p.orientation.y,p.orientation.z,p.orientation.w))
            geometries.append(w.geometry)
        # Exact state after production map draws, so all downstream goal sampling receives the same RNG.
        return base,fields,geometries,m.np_random.get_state()

    def assert_rng_equal(self,a,b):
        self.assertEqual(a[0],b[0]);np.testing.assert_array_equal(a[1],b[1]);self.assertEqual(a[2:],b[2:])

    def test_switch_only_changes_geometry_preserves_rng(self):
        changed=0
        for seed in range(101,111):
            a=self.draw(seed,False);b=self.draw(seed,True)
            self.assertEqual(a[:2],b[:2]);self.assert_rng_equal(a[3],b[3])
            self.assertTrue(all(g==M.ObjectGeometry.RECTANGLE for g in b[2]))
            changed+=sum(x!=y for x,y in zip(a[2],b[2]))
        self.assertGreater(changed,0)

    def test_missing_param_matches_frozen_sampler(self):
        for seed in (101,102,110):
            a=self.draw(seed);b=self.draw(seed,legacy=True)
            self.assertEqual(a[:3],b[:3]);self.assert_rng_equal(a[3],b[3])

    def test_sim_sets_param_before_env_constructor(self):
        calls=[]
        with patch('rospy.set_param',side_effect=lambda *a:calls.append(('param',a))),patch.object(S.T3,'Task3Env',side_effect=lambda **kw:calls.append(('env',kw)) or unittest.mock.MagicMock()):
            S.ScwmEnv(world='sim')
        self.assertEqual(calls[0],('param',('/forem/force_rectangle_obstacles',True)))
        self.assertEqual(calls[1][0],'env')

    def test_gazebo_refuses_param_true_without_setting(self):
        with patch('rospy.get_param',return_value=True),patch('rospy.set_param') as setter,patch.object(S.T3,'Task3Env') as ctor:
            with self.assertRaises(AssertionError): S.ScwmEnv()
            setter.assert_not_called();ctor.assert_not_called()

if __name__=='__main__':unittest.main()
