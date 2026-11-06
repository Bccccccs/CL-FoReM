"""Control-only regressions: no model, GPU work, Docker or training."""
import importlib.util
from pathlib import Path
import tempfile
import json
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('shards_resource_test', ROOT/'scripts/task9_11_program_shards.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

class ResourceWait(unittest.TestCase):
    def fixture(self, root):
        c = object.__new__(s.Coordinator)
        c.root = root
        c.jobs = {n: {'name': n} for n in ('L4718', 'C4719', 'L4719')}
        c.policy = {'allowed_gpu_uuids': ['GPU0', 'GPU2'], 'allocation_seconds': {n:50400 for n in c.jobs}}
        c.p = {'new_output_root': str(root), 'deadline': '2099-01-01T00:00:00+08:00'}
        c.a = {'control_reserve_s':120, 'save_reserve_s':1800}
        c.state = {'jobs': {}}
        c.active = {}
        c.save = lambda: None
        return c

    def test_busy_second_card_does_not_stop_first_worker(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'busy_gpu_uuids', return_value={'GPU2'}):
            c = self.fixture(Path(tmp))
            c.active['L4718'] = {'gpu_index':0}
            with patch.object(c, 'launch') as launch:
                c.schedule()
            launch.assert_not_called()
            self.assertIn('L4718', c.active)
            self.assertEqual(c.state['status'], 'RUNNING')
            self.assertIn('C4719', c.state['waiting_jobs'])

    def test_all_cards_busy_waits_without_output_directories(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'busy_gpu_uuids', return_value={'GPU0','GPU2'}):
            c = self.fixture(Path(tmp))
            with patch.object(c, 'launch') as launch:
                c.schedule()
            launch.assert_not_called()
            self.assertEqual(c.state['status'], 'WAITING_FOR_GPU')
            self.assertFalse((Path(tmp)/'shards').exists())

    def test_launch_recheck_busy_does_not_create_phase(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'busy_gpu_uuids', return_value={'GPU2'}):
            c = self.fixture(Path(tmp))
            with self.assertRaises(s.ResourceBusy):
                c.launch('C4719','profile',1)
            self.assertFalse((Path(tmp)/'shards').exists())
            self.assertFalse(c.active)

    def test_schedule_race_busy_waits_then_dispatches(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'busy_gpu_uuids', return_value=set()):
            c = self.fixture(Path(tmp))
            c.active['L4718']={'gpu_index':0}
            with patch.object(c, 'launch', side_effect=s.ResourceBusy('GPU2')):
                c.schedule()
            with patch.object(c, 'launch') as launch:
                c.schedule()
            launch.assert_called_once_with('C4719','profile',1)

    def test_idle_wait_still_checks_global_deadline(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s.m, 'prerequisites'), patch.object(s, 'busy_gpu_uuids', return_value={'GPU0','GPU2'}), patch.object(s.time, 'sleep'):
            c = self.fixture(Path(tmp))
            with patch.object(c,'guard',side_effect=[None,InterruptedError('deadline')]) as guard:
                with self.assertRaisesRegex(InterruptedError,'deadline'):
                    c.run()
            self.assertEqual(guard.call_count,2)
            self.assertEqual(c.state['status'],'WAITING_FOR_GPU')

    def test_failed_phase_is_not_blindly_retried(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s.m,'prerequisites'):
            c=self.fixture(Path(tmp))
            c.state['jobs']['L4718']={'phases':{'profile':{'status':'FAIL_CONTROL_CLOSURE'}}}
            with patch.object(c,'launch') as launch:
                with self.assertRaisesRegex(RuntimeError,'explicit recovery preparation'):
                    c.run()
            launch.assert_not_called()

    def test_gpu_query_failure_is_not_treated_as_idle(self):
        with patch.object(s.subprocess,'check_output',side_effect=TimeoutError('query')):
            with self.assertRaises(TimeoutError):s.busy_gpu_uuids()

    def test_empty_prior_preflight_directory_does_not_block_launch(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s,'busy_gpu_uuids',return_value=set()):
            c=self.fixture(Path(tmp));c.p.update(new_log_root=str(Path(tmp)/'logs'),max_output_bytes=100,max_diagnostic_log_bytes=100)
            c.budget={'storage_upper_bytes':0,'diagnostic_upper_bytes':0}
            stage=Path(tmp)/'shards/C4719/profile';stage.mkdir(parents=True)
            # Stop deliberately after phase spec publication, before any Docker call.
            with patch.object(s.u,'publish',side_effect=RuntimeError('reached spec')):
                with self.assertRaisesRegex(RuntimeError,'reached spec'):
                    c.launch('C4719','profile',1)

    def test_nonempty_prior_phase_evidence_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s,'busy_gpu_uuids',return_value=set()):
            c=self.fixture(Path(tmp));stage=Path(tmp)/'shards/C4719/profile';stage.mkdir(parents=True)
            (stage/'old.json').write_text('original')
            with self.assertRaisesRegex(ValueError,'prior evidence'):
                c.launch('C4719','profile',1)
            self.assertEqual((stage/'old.json').read_text(),'original')

    def zero_fixture(self, root, steps=0):
        c=self.fixture(root);c.root=root/'parallel-shards';c.root.mkdir()
        c.jobs['L4718'].update(arm='L',seed=4718,config={'path':str(root/'config.json')})
        (root/'config.json').write_text('{}')
        out=root/'formal-L-seed4718';out.mkdir()
        for name,value in [('config.json',{}),('interrupted.meta.json',dict(steps=steps,env_actions=steps,action_calls=steps,resume_safe=True))]:
            (out/name).write_text(json.dumps(value))
        (out/'interrupted.pt').write_bytes(b'fixture only; not a model')
        (out/'STOP').write_text('old stop')
        stage=root/'shards/L4718/profile';stage.mkdir(parents=True)
        inspect={'State':{'Running':False,'Pid':0}}
        (stage/'container-stopped.json').write_text(json.dumps(dict(container_stopped=True,inspect=inspect)))
        result=stage/'result.json';result.write_text(json.dumps(dict(container_id='fixture',actual_outer_wall_s=18.7)))
        c.state['jobs']['L4718']=dict(worker_s=18.7,gpu_s=18.7,phases={'profile':dict(status='FAIL_CONTROL_CLOSURE',result=dict(path=str(result),sha256=s.u.sha(result)))})
        return c,out,inspect

    def test_explicit_zero_recovery_preserves_failure_and_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,out,inspect=self.zero_fixture(Path(tmp))
            original=(out/'interrupted.pt').read_bytes()
            with patch.object(s.u,'inspection',return_value=inspect),patch.object(s.u.g,'container_identity',return_value='fixture'),patch.object(s.u,'refpath',side_effect=lambda ref:Path(ref['path'])):
                value=c.prepare_zero_retry('L4718')
            self.assertTrue(Path(value['original_result']['path']).exists())
            self.assertEqual((Path(value['evidence_root'])/'interrupted.pt').read_bytes(),original)
            self.assertEqual((Path(value['evidence_root'])/'STOP').read_text(),'old stop')
            self.assertFalse((out/'STOP').exists())
            self.assertEqual(c.state['jobs']['L4718']['worker_s'],18.7)
            self.assertEqual(len(c.state['jobs']['L4718']['failed_phases']),1)
            self.assertFalse(Path(value['phase_root']).exists())

    def test_preparation_copy_failure_is_retryable(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,out,inspect=self.zero_fixture(Path(tmp))
            with patch.object(s.u,'inspection',return_value=inspect),patch.object(s.u.g,'container_identity',return_value='fixture'),patch.object(s.u,'refpath',side_effect=lambda ref:Path(ref['path'])):
                with patch.object(s.shutil,'copy2',side_effect=OSError('disk failure')):
                    with self.assertRaises(OSError):c.prepare_zero_retry('L4718')
                self.assertTrue((out/'STOP').exists())
                c.prepare_zero_retry('L4718')
            self.assertFalse((out/'STOP').exists())

    def test_state_commit_failure_retains_STOP_and_can_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,out,inspect=self.zero_fixture(Path(tmp))
            with patch.object(s.u,'inspection',return_value=inspect),patch.object(s.u.g,'container_identity',return_value='fixture'),patch.object(s.u,'refpath',side_effect=lambda ref:Path(ref['path'])):
                with patch.object(c,'save',side_effect=OSError('state write failure')):
                    with self.assertRaises(OSError):c.prepare_zero_retry('L4718')
                self.assertTrue((out/'STOP').exists())
                c.prepare_zero_retry('L4718')
                expected=c.state['jobs']['L4718']['zero_retry']
                self.assertEqual(c.prepare_zero_retry('L4718'),expected)
            self.assertEqual(len(c.state['jobs']['L4718']['failed_phases']),1)
            (out/'STOP').write_text('new user stop')
            with self.assertRaisesRegex(ValueError,'STOP changed'):c.prepare_zero_retry('L4718')
            self.assertEqual((out/'STOP').read_text(),'new user stop')

    def test_new_identical_STOP_is_not_cleared(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,out,inspect=self.zero_fixture(Path(tmp));(out/'STOP').write_bytes(b'')
            with patch.object(s.u,'inspection',return_value=inspect),patch.object(s.u.g,'container_identity',return_value='fixture'),patch.object(s.u,'refpath',side_effect=lambda ref:Path(ref['path'])):
                c.prepare_zero_retry('L4718')
            (out/'STOP').write_bytes(b'')
            with self.assertRaisesRegex(ValueError,'STOP changed'):c.prepare_zero_retry('L4718')
            self.assertTrue((out/'STOP').exists())

    def test_nonzero_recovery_refused_without_clearing_STOP(self):
        with tempfile.TemporaryDirectory() as tmp:
            c,out,inspect=self.zero_fixture(Path(tmp),steps=1)
            with patch.object(s.u,'inspection',return_value=inspect),patch.object(s.u.g,'container_identity',return_value='fixture'):
                with self.assertRaisesRegex(ValueError,'consumed run'):
                    c.prepare_zero_retry('L4718')
            self.assertTrue((out/'STOP').exists())
            self.assertFalse((c.root/'L4718-zero-retry-evidence').exists())

if __name__ == '__main__':unittest.main()
