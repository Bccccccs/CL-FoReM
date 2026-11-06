"""New real-wait/draft boundaries only; no model, environment or Docker calls."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

FOREM=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(FOREM/'src'))
from task9_lr import admission, clock, continuation, execution_draft as draft, gpu_costs, real_receipts as r


class WaitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def wait(self,code='pass',**kwargs):
        return r.wait_command(self.root/'job',[sys.executable,'-I','-S','-c',code],
            cwd=self.root,run_id=draft.PREP_RUN,**kwargs)
    def changed(self,ref,change):
        value=r.read(ref);change(value)
        return clock.publish(self.root/('changed-'+str(len(list(self.root.glob('changed-*'))))+'.json'),value)
    def test_real_wait_zero_does_not_claim_full_cost_or_device(self):
        ref=self.wait();v=r.validate_wait(ref)
        self.assertEqual(v['exit_code'],0);self.assertGreater(v['wall_s'],0)
        self.assertFalse(v['synthetic_fixture']);self.assertEqual(v['publisher_exit'],'UNKNOWN')
        self.assertEqual(v['device_attribution'],'UNKNOWN')
    def test_actual_failure_cost_retained(self):
        v=r.validate_wait(self.wait('raise SystemExit(7)'))
        self.assertEqual(v['exit_code'],7);self.assertGreater(v['wall_s'],0)
    def test_timeout_root_is_reaped(self):
        v=r.validate_wait(self.wait('import time; time.sleep(30)',timeout=.03))
        self.assertTrue(v['timed_out']);self.assertLess(v['exit_code'],0)
        self.assertLess(v['wall_s'],2)
    def test_output_hash_mutation_rejected(self):
        ref=self.wait();v=r.read(ref);Path(v['stdout']['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):r.validate_wait(ref)
    def test_frozen_sources_survive_later_source_edits(self):
        path=self.root/'payload.py';path.write_text('pass\n')
        ref=self.wait(sources=[path]);path.write_text('raise SystemExit(4)\n')
        self.assertEqual(r.validate_wait(ref)['source_integrity'],'UNCHANGED')
    def test_source_changes_during_wait_keep_failure_cost(self):
        path=self.root/'payload.py';path.write_text('before')
        ref=self.wait('from pathlib import Path; Path("payload.py").write_text("after")',sources=[path])
        v=r.validate_wait(ref);self.assertEqual(v['source_integrity'],'CHANGED')
        self.assertGreater(v['wall_s'],0)
    def test_source_snapshot_tamper_rejected(self):
        path=self.root/'payload.py';path.write_text('pass')
        ref=self.wait(sources=[path]);v=r.read(ref)
        Path(v['source_snapshots_before'][0]['path']).write_text('tampered')
        with self.assertRaises(ValueError):r.validate_wait(ref)
    def test_epoch_shift_cannot_move_gpu_scope(self):
        ref=self.wait()
        def shift(v):
            for point in ('started_clock','completed_clock'):v[point]['epoch']+=3600
            v['started_epoch']+=3600;v['finished_epoch']+=3600
        with self.assertRaises(ValueError):r.validate_wait(self.changed(ref,shift))
    def test_clock_domain_and_fixture_generation_rejected(self):
        ref=self.wait()
        for key,value in [('domain','fixture:invented'),('generation',0),('boot','wrong')]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                r.validate_wait(self.changed(ref,lambda v:v['completed_clock'].__setitem__(key,value)))
    def test_no_self_certified_control_tail(self):
        ref=self.wait()
        with self.assertRaises(ValueError):r.validate_wait(self.changed(ref,lambda v:v.__setitem__('publisher_exit',0)))
    def test_real_source_without_allocation_rejected_by_production_gpu_reader(self):
        source=r.cost_source(self.wait())
        p=dict(run_id=draft.PREP_RUN,real_receipt_policy=r.POLICY)
        with self.assertRaises((ValueError,KeyError)):gpu_costs.command(p,source)
    def test_shell_expansion_newline_and_attached_separator_not_container_proof(self):
        ident='a'*64
        for payload in ('docker exec '+ident+' $(nvidia-smi)', 'docker exec '+ident+' true\nnvidia-smi', 'docker exec '+ident+' true;nvidia-smi'):
            with self.subTest(payload=payload),self.assertRaises(ValueError):
                r.container_command(['sg','docker','-c',payload],ident)
        r.container_command(['docker','exec',ident,'true'],ident)
        r.container_command(['sg','docker','-c','docker exec '+ident+' true'],ident)
    def test_real_source_cannot_enter_fixture_reader(self):
        source=r.cost_source(self.wait());source['synthetic_fixture']=True
        with self.assertRaises(ValueError):gpu_costs.command(dict(real_receipt_policy=r.POLICY),source)


class DraftTests(unittest.TestCase):
    def setUp(self):self.p=draft.build('t9.11-continuation-test-preparation-contract')
    def bad(self,change):
        p=copy.deepcopy(self.p);change(p)
        with self.assertRaises((ValueError,KeyError)):draft.validate(p)
    def test_real_draft_preserves_science_consumption_and_unknown(self):
        p=self.p;self.assertEqual(draft.validate(p),p)
        a=p['accounting'];self.assertIsNone(a['worker_exact_remaining_s'])
        self.assertEqual(a['consumed']['formal'],0);self.assertEqual(a['remaining']['evaluation_episodes'],10788)
        self.assertEqual(a['C_host']['actual_host_exit_code'],None)
        self.assertAlmostEqual(a['C_host']['increase_s'],1181.203807115555)
        self.assertEqual(sum(x['transfers'] for x in p['stage_dag']),12000000)
        self.assertEqual(sum(x['evaluation_episodes'] for x in p['stage_dag']),10788)
        self.assertFalse(Path(p['new_output_root']).exists())
    def test_all_execution_and_release_resource_gates_reject_draft(self):
        with self.assertRaises(ValueError):continuation.assert_execution_allowed(self.p)
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.p['new_output_root'])
        with self.assertRaises(ValueError):admission.read_release('/missing','g1',self.p)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'p.json';path.write_text(json.dumps(self.p))
            self.assertEqual(admission.load_protocol(path)['format'],draft.FORMAT)
    def test_actual_production_entrypoints_reject_before_any_execution(self):
        modules={}
        for name in ('prepare','supervise','worker'):
            spec=importlib.util.spec_from_file_location('real_draft_'+name,FOREM/f'scripts/task9_11/{name}.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);modules[name]=module
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'protocol.json';path.write_text(json.dumps(self.p));out=Path(tmp)/'out'
            with self.assertRaises(ValueError):modules['prepare'].prepare(path,out)
            with patch.object(modules['worker'],'activate',side_effect=AssertionError('model imports forbidden')):
                with self.assertRaises(ValueError):modules['worker'].main(['--arm','C','--seed','4718','--phase','g1','--protocol',str(path),'--output',str(out)])
            with patch.object(sys,'argv',['supervise','--protocol',str(path),'--phase','train']),patch.object(modules['supervise'],'create_container',side_effect=AssertionError('Docker control forbidden')):
                with self.assertRaises(ValueError):modules['supervise'].main()
            self.assertFalse(out.exists());self.assertFalse(Path(self.p['new_output_root']).exists())
    def test_no_flag_flip_deadline_or_budget_reset(self):
        for key,val in [('execution_allowed',True),('deadline','2026-11-07T03:18:20+08:00'),('max_worker_seconds',208801),('max_evaluation_episodes',11964)]:
            with self.subTest(key=key):self.bad(lambda p:p.__setitem__(key,val))
    def test_old_C_fail_never_becomes_pass(self):
        self.bad(lambda p:p['legacy_C'].__setitem__('host_integrity','PASS'))
        self.bad(lambda p:p['legacy_C'].__setitem__('PASS_migration',True))
    def test_unknown_and_control_value_cannot_be_removed(self):
        self.bad(lambda p:p['accounting'].__setitem__('unknown',[]))
        self.bad(lambda p:p['accounting'].__setitem__('worker_exact_remaining_s',1))
        self.bad(lambda p:p['control_accounting'].__setitem__('control_envelope_s',30))
    def test_science_and_pending_stages_frozen(self):
        self.bad(lambda p:p['stage_dag'][2].__setitem__('transfers',249999))
        self.bad(lambda p:p['remaining_blockers'].pop())
        self.bad(lambda p:p['source_manifest'].pop(next(iter(p['source_manifest']))))
    def test_foreign_receipts_not_importable_as_this_preparation_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ref=r.wait_command(root/'job',[sys.executable,'-I','-S','-c','pass'],cwd=root,run_id='other-task')
            with self.assertRaises(ValueError):draft.policy_accounting(self.p['accounting']['baseline_review'],self.p['accounting']['baseline_account'],receipts=[ref])
    def test_draft_file_cannot_be_written_to_experiment_namespace(self):
        with self.assertRaises(ValueError):draft.write(Path(self.p['new_output_root'])/'protocol.json',self.p['run_id'])


if __name__=='__main__':unittest.main(verbosity=2)
