import time
import unittest
from task10.profiling import Profiler, patch_methods

class ProfilingTest(unittest.TestCase):
    def test_nested_wall_and_restore_on_exception(self):
        class Work:
            def inner(self): time.sleep(.002)
            def outer(self): self.inner(); raise ValueError('stop')
        original = Work.outer
        p = Profiler()
        with self.assertRaises(ValueError):
            with patch_methods(p, [(Work, 'outer', 'outer'), (Work, 'inner', 'inner')]):
                Work().outer()
        self.assertIs(Work.outer, original)
        self.assertEqual(p.records['outer']['calls'], 1)
        self.assertGreater(p.records['inner']['wall_inclusive_s'], 0)
        self.assertLess(p.records['outer']['wall_exclusive_s'], p.records['outer']['wall_inclusive_s'])
        self.assertGreaterEqual(p.records['outer']['wall_exclusive_s'], 0)

    def test_wrapper_preserves_return_and_arguments(self):
        class Work:
            def f(self, x, *, y): return x + y
        p = Profiler()
        with patch_methods(p, [(Work, 'f', 'function')]):
            self.assertEqual(Work().f(2, y=3), 5)
        self.assertEqual(p.records['function']['calls'], 1)

if __name__ == '__main__': unittest.main()

class ComparisonTest(unittest.TestCase):
    def test_only_explicit_wall_diagnostic_is_ignored(self):
        from task10.profiling import comparable_candidates
        a = {'c_k': [1], 'mask': [True], 'f_k': [2], 'progress': [3],
             'inplace': [False], 'world_pose': [4],
             'diagnostics': {'search_wall_seconds': 1., 'n_gen': 1}}
        b = {'c_k': [1], 'mask': [True], 'f_k': [2], 'progress': [3],
             'inplace': [False], 'world_pose': [4],
             'diagnostics': {'search_wall_seconds': 2., 'n_gen': 1}}
        self.assertEqual(comparable_candidates(a), comparable_candidates(b))
        b['diagnostics']['n_gen'] = 2
        self.assertNotEqual(comparable_candidates(a), comparable_candidates(b))
        del b['diagnostics']['search_wall_seconds']
        with self.assertRaises(KeyError): comparable_candidates(b)
        self.assertIn('search_wall_seconds', a['diagnostics'])

    def test_nested_phase_assigns_function_to_innermost_stage(self):
        p = Profiler()
        with p.phase('reset'):
            with p.measure('ik'): pass
            with p.phase('prediction'):
                with p.measure('ik'): pass
        self.assertEqual(p.records['reset.ik']['calls'], 1)
        self.assertEqual(p.records['prediction.ik']['calls'], 1)
