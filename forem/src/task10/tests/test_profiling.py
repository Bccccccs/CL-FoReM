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

class ReplayCanonicalizationTest(unittest.TestCase):
    def test_exact_cpu_canonicalizes_grid_and_only_ignores_search_time(self):
        try:
            import torch
            from task7_upper.replay import exact_cpu
        except ImportError:
            self.skipTest('torch unavailable')
        from task10.profiling import comparison_snapshot
        old = {'observation': {'grid_uint8': torch.tensor([3], dtype=torch.uint8)},
               'candidates': {'c_k': torch.tensor([1.]), 'diagnostics': {'search_wall_seconds': 1., 'n_gen': 1}}}
        new = {'observation': {'grid': torch.tensor([0.]), 'grid_uint8': torch.tensor([3], dtype=torch.uint8)},
               'candidates': {'c_k': torch.tensor([1.]), 'diagnostics': {'search_wall_seconds': 3., 'n_gen': 1}}}
        snapshot = comparison_snapshot(new, exact_cpu)
        self.assertEqual(set(old['observation']), set(snapshot['observation']))
        self.assertTrue(torch.equal(old['observation']['grid_uint8'], snapshot['observation']['grid_uint8']))
        self.assertEqual(snapshot['candidates']['diagnostics'], {'n_gen': 1})
        self.assertEqual(comparison_snapshot(old, exact_cpu)['candidates']['diagnostics'], snapshot['candidates']['diagnostics'])
        self.assertIn('grid', new['observation'])

    def test_batch_budget_rejects_excess_and_missing_baseline(self):
        from task10.profiling import validate_batch_budget
        self.assertEqual(validate_batch_budget(2, 1, 24), (2, 1, 24))
        for args in [(2, 2, 24), (1, 2, 24), (3, 1, 32), (2, 1, 25)]:
            with self.assertRaises(ValueError): validate_batch_budget(*args)

class BoundaryHashTest(unittest.TestCase):
    def test_digest_detects_scientific_changes_and_is_stable(self):
        try:
            import torch
        except ImportError:
            self.skipTest('torch unavailable')
        from task10.profiling import snapshot_digest
        a = {'obs': torch.tensor([1, 2]), 'candidates': {'n': 3}}
        self.assertEqual(snapshot_digest(a), snapshot_digest({'candidates': {'n': 3}, 'obs': torch.tensor([1, 2])}))
        self.assertNotEqual(snapshot_digest(a), snapshot_digest({'obs': torch.tensor([1, 3]), 'candidates': {'n': 3}}))
