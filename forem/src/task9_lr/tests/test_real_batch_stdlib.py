"""Real .18 contract/receipt boundaries; no Docker, model, environment or GPU."""
import copy
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from task9_lr import real_batch as b, real_receipts as r


class RealBatchTests(unittest.TestCase):
    def setUp(self):
        self.p=b.build('t9.11-real-contract-tests')
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def changed(self,key,value):
        p=copy.deepcopy(self.p);p[key]=value
        with self.assertRaises((ValueError,KeyError)):b.validate(p)
    def test_calendar_only_authorized_limits_and_science_fixed(self):
        self.assertEqual(b.validate(self.p),self.p)
        self.assertEqual(self.p['max_wall_seconds'],82*3600)
        self.assertEqual(self.p['max_worker_seconds'],58*3600)
        self.assertEqual(self.p['max_gpu_seconds'],58*3600)
        self.assertEqual(self.p['started_at'],'2026-11-03T17:18:20+08:00')
        self.assertEqual(sum(s['transfers'] for s in self.p['stage_dag']),12000000)
        self.assertEqual(sum(s['evaluation_episodes'] for s in self.p['stage_dag']),10788)
        self.assertFalse(Path(self.p['new_output_root']).exists())
    def test_unauthorized_limits_calendar_or_science_rejected(self):
        for k,v in [('max_worker_seconds',295200),('max_gpu_seconds',295200),
            ('max_wall_seconds',295201),('deadline','2026-11-08T03:18:20+08:00'),
            ('started_at','2026-11-04T00:00:00+08:00'),('max_evaluation_episodes',11964),
            ('max_formal_transfers',2500000),('automatic_retry',True)]:
            with self.subTest(key=k):self.changed(k,v)
    def test_old_namespace_or_candidate_flag_cannot_enable_real_protocol(self):
        for k,v in [('run_id','t9.11-lr-20261103T171820+0800'),('execution_allowed',True),
                    ('continuation',{}),('candidate_accounting',{}),('science_dispatch_available',True)]:
            with self.subTest(key=k):self.changed(k,v)
    def test_source_and_scientific_manifest_cannot_drift(self):
        for key in ('source_manifest','scientific_configs','input_manifest'):
            self.changed(key,{})
        self.changed('source_digest','0'*64)
    def test_stage_budget_and_unknown_lineage_cannot_disappear(self):
        self.changed('remaining',{})
        self.changed('historical_preparation',{})
        self.changed('stage_dag',[])
        self.changed('admission_dependencies',[])
    def test_literal_exact_id_argv_roundtrip(self):
        ident='a'*64
        command=b.container_argv(ident,['printf','a b; $(literal)'])
        self.assertEqual(shlex.split(command[3]),['docker','exec',ident,'printf','a b; $(literal)'])
        r.container_command(command,ident)
        for bad in ('forem-task9','a'*12,'a'*63,'A'*64,'a'*64+';'):
            with self.subTest(id=bad),self.assertRaises(ValueError):b.container_argv(bad,['true'])
    def test_worker_argv_binds_exact_stage_reservation_and_container(self):
        command=b.worker_argv(self.p,'b'*64,'profile','C',4718,'c'*32)
        argv=shlex.split(command[3])
        self.assertEqual(argv[:3],['docker','exec','b'*64])
        self.assertIn('TASK9_LR_RESERVATION='+'c'*32,argv)
        self.assertIn('/output/formal-C-seed4718',argv)
        for args in [('smoke1000','C',4718,'c'*32),('profile','C',999,'c'*32),('profile','C',4718,'short')]:
            with self.subTest(args=args),self.assertRaises(ValueError):b.worker_argv(self.p,'b'*64,*args)
    def test_receipt_roots_are_run_specific_and_escape_refused(self):
        other=copy.deepcopy(self.p);other['run_id']='t9.11-real-second-valid-run'
        self.assertNotEqual(b.receipt_root(self.p),b.receipt_root(other))
        for bad in ('../escape','t9.11-real-../escape','t9.11-real-a/b',''):
            with self.subTest(run=bad),self.assertRaises(ValueError):b.receipt_root(dict(run_id=bad))
    def test_control_receipt_cannot_use_another_runs_subtree(self):
        other=copy.deepcopy(self.p);other['run_id']='t9.11-real-second-valid-run'
        command=['sg','docker','-c','docker inspect '+'a'*64]
        with patch.object(r,'wait_command',side_effect=AssertionError('cross-run must not launch')):
            with self.assertRaisesRegex(ValueError,'this real run'):
                b.record_control(self.p,b.receipt_root(other)/'inspect','a'*64,command)

    def test_contract_write_stays_in_review_logs(self):
        with self.assertRaises(ValueError):b.write(Path(self.p['new_output_root'])/'protocol.json',self.p['run_id'])
    def test_missing_costs_or_independent_stage_never_reaches_science(self):
        with self.assertRaisesRegex(ValueError,'historical'):b.require_science_admission(self.p)
        with self.assertRaisesRegex(ValueError,'independent'):b.require_science_admission(self.p,historical_cost_review={})
        with self.assertRaisesRegex(ValueError,'release references'):
            b.require_science_admission(self.p,historical_cost_review={},source_review={},stage_release={})
    def test_control_inspect_whitelist_before_launch(self):
        with patch.object(r,'wait_command',side_effect=AssertionError('must not launch')):
            with self.assertRaises(ValueError):b.record_control(self.p,b.RECEIPT_ROOT/'test','a'*64,['docker','kill','a'*64])
            with self.assertRaises(ValueError):b.record_control(self.p,self.root/'test','a'*64,['sg','docker','-c','docker inspect '+'a'*64])
    def test_control_probe_requires_independent_review_before_launch(self):
        ref=r.bound(b.APPROVAL)
        with patch.object(r,'wait_command',side_effect=AssertionError('must not launch')):
            with self.assertRaises(ValueError):b.record_container_probe(self.p,b.RECEIPT_ROOT/'test','a'*64,source_review=ref)
    def actual_wait(self,run_id=None):
        with patch.object(b,'RECEIPT_ROOT',self.root):
            ref=r.wait_command(self.root/self.p['run_id']/'actual',[sys.executable,'-I','-S','-c','print("actual")'],
                cwd=self.root,run_id=run_id or self.p['run_id'])
        return ref
    def test_actual_writer_to_reader_missing_device_remains_unknown(self):
        ref=self.actual_wait()
        with patch.object(b,'RECEIPT_ROOT',self.root),self.assertRaises((ValueError,KeyError)):
            b.source_from_wait(self.p,ref,None)
        self.assertGreater(r.validate_wait(ref)['wall_s'],0)
    def test_actual_writer_bridge_uses_production_reader_and_keeps_tail_unknown(self):
        ref=self.actual_wait()
        # The allocator is a mock, not a claim of a real device admission.
        with patch.object(b,'RECEIPT_ROOT',self.root),patch.object(b.gpu_costs,'command',return_value=[]) as reader:
            result=b.source_from_wait(self.p,ref,{'path':'/mock/review','sha256':'0'*64})
        reader.assert_called_once()
        self.assertEqual(reader.call_args.args[1]['real_wait_receipt'],ref)
        self.assertEqual(result['source']['argv'],r.read(ref)['argv'])
        self.assertEqual(result['full_session_cost'],'UNKNOWN')
        self.assertFalse(result['budget_admissible'])
    def test_foreign_wait_namespace_rejected_before_device_reader(self):
        ref=self.actual_wait('foreign')
        with patch.object(b,'RECEIPT_ROOT',self.root),self.assertRaisesRegex(ValueError,'foreign-batch'):
            b.source_from_wait(self.p,ref,None)
    def test_actual_execute_cli_root_wait_is_isolated_for_two_runs(self):
        from task9_lr import real_g1 as g
        spec=importlib.util.spec_from_file_location('real_batch_inert_cli_namespaces',ROOT/'scripts/task9_11/real_batch.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        contract=self.root/'inert-contract.json';contract.write_text('{}')
        captured=[]
        def mock_wait(directory,argv,**kwargs):
            directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
            self.assertIn('--g1-inner',argv)
            path=directory/'mock-wait.json';path.write_text(json.dumps(dict(exit_code=0)))
            captured.append(directory);return b.bound(path)
        with patch.object(b,'RECEIPT_ROOT',self.root/'commands'),\
             patch.object(g,'release',return_value=dict(max_worker_seconds=120,control_reserve_s=120)),\
             patch.object(r,'wait_command',side_effect=mock_wait),patch.object(r,'validate_wait',side_effect=b.read_ref):
            for label in ('first','second'):
                p=copy.deepcopy(self.p);p['run_id']='t9.11-real-cli-'+label
                with patch.object(b,'read',return_value=p):
                    self.assertEqual(cli.main(['--execute-g1','--contract',str(contract)]),0)
                    self.assertEqual(captured[-1],b.receipt_root(p)/'real-G1-root-wait')
            self.assertEqual(len(set(captured)),2)
            with patch.object(b,'read',return_value=p),self.assertRaises(FileExistsError):
                cli.main(['--execute-g1','--contract',str(contract)])

    def test_existing_production_worker_rejects_real_contract_before_model_import(self):
        spec=importlib.util.spec_from_file_location('real_worker_check',ROOT/'scripts/task9_11/worker.py')
        worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        path=self.root/'protocol.json';path.write_text(json.dumps(self.p))
        with patch.object(worker,'activate',side_effect=AssertionError('model import forbidden')):
            with self.assertRaises((ValueError,FileNotFoundError)):worker.main(['--arm','C','--seed','4718','--phase','g1','--protocol',str(path),'--output',str(self.root/'science')])
        self.assertFalse((self.root/'science').exists())


if __name__=='__main__':unittest.main(verbosity=2)
