"""Standalone stdlib JSON fixtures for production continuation readers.

Run directly with python3 -B; never pytest/conftest, models, or Docker.
"""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

FOREM=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(FOREM/'src'))
from task9_lr import continuation as c
from task9_lr import admission, gpu_costs
from task9_lr.runtime import artifact_digest, sha256

prepare_spec=importlib.util.spec_from_file_location('task9_continuation_prepare',FOREM/'scripts/task9_11/prepare.py')
prepare=importlib.util.module_from_spec(prepare_spec)
prepare_spec.loader.exec_module(prepare)


def bound(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')
    return dict(path=str(path),sha256=sha256(path))


def make_fixture(base):
    """Pure synthetic independent old ledger. Never reads real old activity/costs."""
    root=Path(base)/'forem';logs=root/'doc/agent_logs/task9/task9.11'
    old=json.loads((FOREM/'config/task9/task9_11/protocol.json').read_text())
    old.update(new_output_root=str(root/'results/task9'/c.ORIGINAL_RUN),
               new_log_root=str(root/'logs/task9'/c.ORIGINAL_RUN))
    baseline=bound(root/'config/task9/task9_11/protocol.json',old)
    proof=bound(logs/'synthetic-old-science.json',{'synthetic_fixture':True,'scientific_only':True})
    stop=bound(logs/'task9.11.4/gate-evaluate-C-4718-FAIL-STOP.json',dict(
        run_id=c.ORIGINAL_RUN,status='FAIL_INCOMPLETE_SUPERVISION',next_stage_release=False,evidence=[proof]))
    epoch=dt.datetime.fromisoformat(c.START).timestamp()
    synthetic=dict(execution_allowed=False,continuation=dict(synthetic_fixture=True),preferred_gpu_uuid=old['preferred_gpu_uuid'])
    def cpu(wall):return dict(wall_s=wall,started_epoch=epoch,finished_epoch=epoch+wall,synthetic_fixture=True,gpu_evidence=gpu_costs.fixture_evidence(synthetic,epoch,epoch+wall,[]))
    old_command=bound(logs/'old-command.json',cpu(2.))
    new_command=bound(logs/'new-review-command.json',cpu(3.))
    account=bound(logs/'synthetic-accounting.json',dict(format='task9-lr-synthetic-accounting-v1',
        synthetic_fixture=True,original_run_id=c.ORIGINAL_RUN,started_at=c.START,deadline=c.DEADLINE,
        original_limits=c.LIMITS,consumed=c.CONSUMED,remaining=c.REMAINING,unknown=[],
        gpu_evidence=gpu_costs.fixture_evidence(synthetic,epoch,epoch+110.,[old['preferred_gpu_uuid']]),
        command_components=[old_command],exact_costs=dict(worker_seconds=100.,gpu_seconds=110.,
        evaluation_episodes=980,output_bytes=1000,diagnostic_log_bytes=200)))
    name='t9.11-continuation-synthetic'
    p=dict(old);p.update(format=c.FORMAT,run_id=name,execution_allowed=False,
        new_output_root=str(root/'results/task9'/name),new_log_root=str(root/'logs/task9'/name),
        reviewer='task9.11.10',stage_releases=[],external_activity_roots=[str(logs)],external_output_roots=[str(logs)],
        candidate_accounting=dict(format='task9-lr-candidate-accounting-v1',job_scope='launch-through-actual-owner-wait',control_envelope_s=30.),
        path_mappings=[dict(host=str(root/'results/task9'/name),container='/output'),
                       dict(host=str(root/'logs/task9'/name),container='/runlogs'),
                       dict(host=str(root),container='/workspace'),dict(host=str(Path(base)/'history'),container='/history')],
        continuation=dict(format='task9-lr-continuation-adapter-v1',synthetic_fixture=True,
            host_workspace=str(root),host_history=str(Path(base)/'history'),reviewer='task9.11.10',
            baseline_protocol=baseline,legacy_stop=stop,accounting_snapshot=account,
            consumed=copy.deepcopy(c.CONSUMED),remaining=copy.deepcopy(c.REMAINING),legacy_PASS_migration=False,
            legacy_C_integrity='FAIL_INCOMPLETE_SUPERVISION',external_cost_inventory=[old_command,new_command],
            pending_user_decisions=[dict(id=k,status='SYNTHETIC_FIXTURE_ONLY',applied=False) for k in sorted(c.DECISIONS)]))
    Path(p['new_output_root']).mkdir(parents=True)
    Path(p['new_log_root']).mkdir(parents=True)
    # Inputs are metadata-only substitutes; all four scientific configs are the
    # actual unchanged matrix, frozen by the production pure preparation path.
    for config in prepare.validate_matrix().values():
        for key in ('pool','transfer_pool','evaluation_seeds'):
            bound(c.resolve_path(config[key],p),dict(synthetic_fixture=True,metadata_only=True))
    source=logs/'synthetic-candidate-protocol.json';bound(source,p)
    frozen=prepare.freeze_candidate_protocol(source,Path(p['new_output_root'])/'freeze')
    fixture_path=frozen/'protocol.json'
    p['_sealed_sha256']=sha256(fixture_path)
    return p


def fixture_release(p,stage='g1',arm='C',seed=4718):
    output=Path(p['new_output_root']);entries=[]
    for kind in ('new-code-review','legacy-scientific-reference','new-lifecycle-review','development-review'):
        if kind=='legacy-scientific-reference':
            stop=json.loads(Path(p['continuation']['legacy_stop']['path']).read_text())
            value=dict(reference_only=True,status='REFERENCE_ONLY',original_run_id=c.ORIGINAL_RUN,
                legacy_C_integrity='FAIL_INCOMPLETE_SUPERVISION',source=stop['evidence'][0])
        else:
            value=dict(format='task9-lr-continuation-review-v1',status='PASS',run_id=p['run_id'],
                protocol_sha256=p['_sealed_sha256'],code_hash=artifact_digest(),reviewer_task=p['reviewer'],
                stage=stage,arm=arm,seed=seed,synthetic_fixture=True,execution_allowed=False)
        entry=bound(output/'review'/f'{stage}-{arm}-{seed}-{kind}.json',value)
        entry['kind']=kind;entries.append(entry)
    return dict(stage=stage,arm=arm,seed=seed,run_id=p['run_id'],code_hash=artifact_digest(),
        protocol_sha256=p['_sealed_sha256'],reviewer_task=p['reviewer'],status='PASS',synthetic_fixture=True,
        expires_at='2026-11-06T02:18:20+08:00',evidence=entries,
        remaining_resource_budget=dict(worker_seconds=200000,gpu_seconds=190000,wall_seconds=180000,
            output_bytes=100000,evaluation_episodes=10788,consumed_transfers=12000000),
        max_worker_seconds=30.,save_reserve_s=5.)


class ContinuationAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='t9-continuation-')
        self.p=make_fixture(self.tmp.name)
        self.clock=dt.datetime.fromisoformat('2026-11-03T23:00:00+08:00')
    def tearDown(self):self.tmp.cleanup()
    def release(self,token=None,**kwargs):
        return c.validate_release(token or fixture_release(self.p),kwargs.pop('stage','g1'),self.p,
            arm=kwargs.pop('arm','C'),seed=kwargs.pop('seed',4718),code_hash=artifact_digest(),clock=self.clock,**kwargs)
    def test_production_protocol_and_release_readers(self):
        path=Path(self.p['new_output_root'])/'freeze/protocol.json'
        p=admission.load_protocol(path)
        self.assertEqual(p['_sealed_sha256'],self.p['_sealed_sha256'])
        token=fixture_release(p);entry=bound(Path(p['new_output_root'])/'release.json',token)
        self.assertEqual(admission.read_release(entry['path'],'g1',p,arm='C',seed=4718,clock=self.clock),token)
    def test_production_prepare_freezes_exact_configs_inputs_and_namespace(self):
        freeze=Path(self.p['new_output_root'])/'freeze';inventory=json.loads((freeze/'inventory.json').read_text())
        self.assertEqual(inventory['protocol_sha256'],self.p['_sealed_sha256'])
        self.assertFalse(inventory['execution_allowed'])
        for arm,seed in c.ORDER:
            source=FOREM/f'config/task9/task9_11/{arm}_seed{seed}.json'
            self.assertEqual((freeze/source.name).read_bytes(),source.read_bytes())
        for source,alias in inventory['input_aliases'].items():
            self.assertEqual(inventory['inputs'][source],sha256(alias))
            self.assertTrue(Path(alias).is_relative_to(Path(self.tmp.name)/'history'))
        with self.assertRaises(ValueError):
            prepare.freeze_candidate_protocol(freeze/'protocol.json',Path(self.tmp.name)/'wrong-freeze')
    def test_mount_mapping_no_existence_fallback_or_cross_run(self):
        host=Path(self.p['new_output_root'])/'review/e.json';entry=bound(host,{'x':1})
        inside=dict(entry,path='/output/review/e.json')
        self.assertEqual(admission.evidence(inside,self.p),host)
        self.assertEqual(c.resolve_path(str(host),self.p,container=True),Path('/output/review/e.json'))
        self.assertEqual(c.resolve_path('/workspace/config/task9/task9_11/protocol.json',self.p),Path(self.p['continuation']['baseline_protocol']['path']))
        for path in ('/other-run/e.json','/output/../wrong.json','relative.json'):
            with self.subTest(path=path),self.assertRaises(ValueError):c.resolve_path(path,self.p)
        inside['sha256']='0'*64
        with self.assertRaises(ValueError):admission.evidence(inside,self.p)
    def test_inherited_and_external_costs_exact_and_nonoverlapping(self):
        cost=c.inherited_accounting(self.p);external=c.validate_external_costs(self.p)
        self.assertEqual((cost['worker_seconds'],cost['gpu_seconds'],cost['evaluation_episodes']),(100.,110.,980))
        self.assertEqual(external['worker_seconds'],3.)
        self.assertEqual(len(external['accounted_paths']),1)
    def test_production_resource_check_accumulates_old_980(self):
        result=admission.check_resources(self.p,self.p['new_output_root'])
        self.assertEqual(result['worker_seconds'],103.)
        self.assertEqual(result['evaluation_episodes'],980)
    def test_omitted_new_changed_unknown_external_costs_rejected(self):
        root=Path(self.p['external_activity_roots'][0])
        for case in ('omitted','new','changed','unknown'):
            with self.subTest(case=case):
                p=copy.deepcopy(self.p)
                if case=='omitted':p['continuation']['external_cost_inventory'].pop()
                elif case=='new':bound(root/'extra-command.json',dict(wall_s=1.))
                elif case=='changed':Path(p['continuation']['external_cost_inventory'][-1]['path']).write_text('{}')
                else:
                    entry=bound(root/'new-review-command.json',dict(wall_s=None));p['continuation']['external_cost_inventory'][-1]=entry
                with self.assertRaises(ValueError):c.validate_external_costs(p)
                # Restore independent fixture so a prior defect cannot mask the next.
                self.tmp.cleanup();self.tmp=tempfile.TemporaryDirectory(prefix='t9-continuation-');self.p=make_fixture(self.tmp.name)
                root=Path(self.p['external_activity_roots'][0])
    def test_original_window_limits_consumption_and_science_rejected(self):
        for key,value in [('started_at','2026-11-03T23:00:00+08:00'),('max_output_bytes',2*1024**4+1),
                          ('deadline','2026-11-07T03:18:20+08:00'),('first_update',261),('reviewer','task9.11.4')]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                p=copy.deepcopy(self.p);p[key]=value;c.validate_protocol(p)
        for key in ('smoke','extra_C_ON','L_ON','formal_validation','final_test'):
            with self.subTest(key=key),self.assertRaises(ValueError):
                p=copy.deepcopy(self.p);p['continuation']['remaining'][key]+=1;c.validate_protocol(p)
    def test_real_unknown_cannot_be_disguised_as_fixture(self):
        account_path=Path(self.p['continuation']['accounting_snapshot']['path'])
        account=json.loads(account_path.read_text());account.update(format='task9-lr-cumulative-budget-lower-bound-v2',unknown=['historical tail'],worker_exact_remaining_s=None,execution_release=False)
        self.p['continuation']['accounting_snapshot']=bound(account_path,account)
        with self.assertRaisesRegex(ValueError,'cannot import real historical UNKNOWN'):c.inherited_accounting(self.p)
    def test_unknown_never_becomes_zero(self):
        path=Path(self.p['continuation']['accounting_snapshot']['path']);account=json.loads(path.read_text())
        for key in ('worker_seconds','gpu_seconds','output_bytes','diagnostic_log_bytes'):
            with self.subTest(key=key):
                changed=copy.deepcopy(account);changed['exact_costs'][key]=None
                self.p['continuation']['accounting_snapshot']=bound(path,changed)
                with self.assertRaises(ValueError):c.inherited_accounting(self.p)
    def test_release_namespace_code_protocol_reviewer_and_typed_evidence(self):
        for key,value in [('run_id',c.ORIGINAL_RUN),('code_hash','0'*64),('protocol_sha256','f'*64),
                          ('reviewer_task','task9.11.4'),('synthetic_fixture',False),('expires_at','2026-11-03T22:00:00+08:00')]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                token=fixture_release(self.p);token[key]=value;self.release(token)
        token=fixture_release(self.p,'gate-evaluate','L',4718);token['evidence']=[token['evidence'][0]]
        with self.assertRaises(ValueError):self.release(token,stage='gate-evaluate',arm='L')
    def test_new_DAG_no_smoke_no_extra_C_ON_or_old_PASS(self):
        self.assertEqual(c.jobs(self.p,'smoke-and-gates'),[('g1','C',4718),('gate-evaluate','L',4718)])
        rows=[]
        for stage,arm,seed in c.jobs(self.p,'smoke-and-gates')+c.jobs(self.p,'train')+c.jobs(self.p,'final-test'):
            c.prerequisites(self.p,stage,arm,seed,rows)
            rows.append(dict(run_id=self.p['run_id'],protocol_sha256=self.p['_sealed_sha256'],phase=stage,arm=arm,seed=seed,status='PASS'))
        with self.assertRaises(ValueError):c.prerequisites(self.p,'gate-evaluate','C',4718,rows)
        with self.assertRaises(ValueError):c.prerequisites(self.p,'smoke512','L',4718,rows)
        rows[0]['run_id']=c.ORIGINAL_RUN
        with self.assertRaises(ValueError):c.prerequisites(self.p,'profile','C',4718,rows)
    def test_relabelled_legacy_FAIL_PASS_or_wrong_new_review_rejected(self):
        for change in ({'status':'FAIL'},{'run_id':c.ORIGINAL_RUN},{'protocol_sha256':'0'*64},
                       {'code_hash':'0'*64},{'reviewer_task':'task9.11.4'}):
            with self.subTest(change=change):
                token=fixture_release(self.p);entry=token['evidence'][0]
                value=json.loads(Path(entry['path']).read_text());value.update(change)
                token['evidence'][0]=dict(bound(entry['path'],value),kind=entry['kind'])
                with self.assertRaisesRegex(ValueError,'review contents'):self.release(token)
        token=fixture_release(self.p,'gate-evaluate','L');entry=token['evidence'][1]
        value=json.loads(Path(entry['path']).read_text());value['status']='PASS'
        token['evidence'][1]=dict(bound(entry['path'],value),kind=entry['kind'])
        with self.assertRaisesRegex(ValueError,'cannot certify new PASS'):self.release(token,stage='gate-evaluate',arm='L')
    def test_missing_prerequisite_and_final_development_review_block(self):
        with self.assertRaises(ValueError):c.prerequisites(self.p,'profile','C',4718,[])
        token=fixture_release(self.p,'final-test');token['evidence']=[e for e in token['evidence'] if e['kind']!='development-review']
        with self.assertRaises(ValueError):self.release(token,stage='final-test')
    def test_all_candidates_refuse_real_execution(self):
        with self.assertRaisesRegex(ValueError,'no Docker/worker/CLI'):c.assert_execution_allowed(self.p)
    def test_no_heavy_runtime_imports(self):
        self.assertFalse(set(sys.modules)&{'torch','numpy','pytest','task7_lower','task7_sim','task8_lower','task8_sim'})


if __name__=='__main__':unittest.main(verbosity=2)
