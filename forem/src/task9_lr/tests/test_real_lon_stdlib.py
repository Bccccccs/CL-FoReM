"""Single L ON admission and exact historical loader bridge; no models or GPU."""
import copy
import ast
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from task9_lr import clock,real_batch as b,real_g1 as g,real_lon as l
from task9_lr.admission import prerequisites,read_release


class RealLOnTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.p=b.build('t9.11-real-l-on-inert-tests',l_on=True)
    def tearDown(self):self.tmp.cleanup()
    def test_fresh_container_import_preserves_host_evidence_identity(self):
        spec=importlib.util.spec_from_file_location('task9_lr._lon_container_import_probe',ROOT/'src/task9_lr/real_lon.py')
        probe=importlib.util.module_from_spec(spec)
        with patch.object(b,'ASSET_ROOT',Path('/workspace')),patch.object(b,'REVIEW_ROOT',Path('/workspace/doc/agent_logs/task9/task9.11/task9.11.18')):
            spec.loader.exec_module(probe)
            self.assertEqual(probe.g1_reference(),l.g1_reference())
            self.assertEqual(probe.BRIDGE,l.BRIDGE);self.assertEqual(probe.INPUTS,l.INPUTS)
            self.assertTrue(b.local_path(probe.G1).is_relative_to('/workspace'))
            self.assertTrue(b.local_path(probe.BRIDGE['science']['path']).is_relative_to('/workspace'))

    def test_exact_consumption_and_single_stage_prerequisites(self):
        self.assertEqual(b.stage(self.p)['name'],'gate-evaluate-L-4718')
        self.assertTrue(self.p['science_dispatch_available']);self.assertEqual(self.p['science_dispatch_scope'],'L_ON196_ONLY')
        self.assertEqual(self.p['consumed']['evaluation_episodes'],980)
        self.assertEqual(self.p['remaining']['L_ON'],196)
        self.assertEqual(self.p['completed_G1']['sha256'],l.G1_SHA)
        prerequisites(self.root,'gate-evaluate','L',4718,protocol=self.p)
        for stage,arm,seed in [('g1','C',4718),('gate-evaluate','C',4718),('gate-evaluate','L',4719),('profile','L',4718),('smoke1000','L',4718),('final-test','L',4718)]:
            with self.subTest(stage=stage,arm=arm),self.assertRaises(ValueError):
                prerequisites(self.root,stage,arm,seed,protocol=self.p)
    def test_missing_or_changed_G1_old_config_off_parity_rejected(self):
        for key in ('completed_G1','lon_inputs','legacy_contract_basis'):
            p=copy.deepcopy(self.p);p[key]={}
            with self.subTest(key=key),self.assertRaises(ValueError):b.validate(p)
        for key in ('checkpoint','config','summary','off','parity'):
            p=copy.deepcopy(self.p);p['lon_inputs'][key]['sha256']='0'*64
            with self.subTest(key=key),self.assertRaises(ValueError):l.validate_inputs(p)
    def test_input_verification_finishes_before_any_model_import(self):
        # Full real old checkpoint hash is checked once, without torch.load or
        # model/environment imports; its cost belongs to the enclosing receipt.
        before=set(sys.modules)
        checkpoint=l.preflight(self.p,self.root)
        self.assertEqual(checkpoint,b.local_path(l.INPUTS['checkpoint']['path']))
        self.assertNotIn('torch',set(sys.modules)-before)
        proof=json.loads((self.root/'legacy-input-validation.json').read_text())
        self.assertEqual(proof['status'],'PASS_BYTES_BEFORE_MODEL_LOAD')
    def test_bad_checkpoint_hash_rejected_before_receipt_and_model(self):
        real=l.stream_sha
        def digest(path):return '0'*64 if Path(path).name=='final.pt' else real(path)
        with patch.object(l,'stream_sha',side_effect=digest),self.assertRaisesRegex(ValueError,'checkpoint'):
            l.preflight(self.p,self.root)
        self.assertFalse((self.root/'legacy-input-validation.json').exists())
    def test_resource_view_charges_980_and_old_storage_and_bounds_this196(self):
        p=copy.deepcopy(self.p)
        budget=dict(storage_upper_bytes=40000000000,diagnostic_upper_bytes=1000000000)
        with patch.object(g,'checked_budget',return_value=budget):view=l.resource_view(p,{'budget_review':{}})
        self.assertEqual(p,self.p)
        self.assertEqual(view['remaining_global_evaluation_episodes'],10788)
        self.assertEqual(view['max_evaluation_episodes'],196)
        self.assertEqual(view['max_output_bytes'],p['max_output_bytes']-40000000000)
        self.assertEqual(view['max_diagnostic_log_bytes'],p['max_diagnostic_log_bytes']-1000000000)
    def test_limited_loader_preserves_exact_code_all_checks_and_original_globals(self):
        old=l.legacy_contract(self.p)
        namespace={'_contract':lambda:{'CURRENT_NEW_SOURCE':True},'expected_old':old}
        exec("def loader(path,device):\n value=path\n if value['contract']!=_contract():raise ValueError('contract mismatch')\n if value['pool']!='good':raise ValueError('pool mismatch')\n if value['unsafe']:raise ValueError('unsafe')\n return device\n",namespace)
        original=namespace['loader'];adapted=l.limited_loader(original,old)
        self.assertIs(adapted.__code__,original.__code__)
        self.assertEqual(namespace['_contract'](),{'CURRENT_NEW_SOURCE':True})
        payload=dict(contract=copy.deepcopy(old),pool='good',unsafe=False)
        self.assertEqual(adapted(payload,'cuda'),'cuda')
        for key,value in [('contract',{'unknown':True}),('pool','changed'),('unsafe',True)]:
            modified=copy.deepcopy(payload);modified[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):adapted(modified,'cuda')
        self.assertEqual(namespace['_contract'](),{'CURRENT_NEW_SOURCE':True})
    def test_actual_device_observer_accepts_cpu_step_but_not_cpu_moments(self):
        tensor=lambda device:types.SimpleNamespace(device=device)
        parameter=types.SimpleNamespace(device='cuda:0')
        class Network:
            def parameters(self):return [parameter]
        def optimizer():return types.SimpleNamespace(param_groups=[dict(params=[parameter],capturable=False,fused=False)],
            state={1:dict(step=tensor('cpu'),exp_avg=tensor('cuda:0'),exp_avg_sq=tensor('cuda:0'))})
        sac=types.SimpleNamespace(policy=Network(),critic=Network(),critic_target=Network(),log_alpha=parameter,
                                 policy_optim=optimizer(),critic_optim=optimizer(),alpha_optim=optimizer())
        replay=types.SimpleNamespace(map_s=tensor('cuda:0'),map_n=tensor('cuda:0'),rob_s=tensor('cuda:0'))
        value=l.actual_devices(sac,replay)
        self.assertEqual(value['optimizers']['actor']['states_by_field']['step'],['cpu'])
        self.assertEqual(value['optimizers']['actor']['states_by_field']['exp_avg'],['cuda:0'])
        self.assertEqual(sac.policy_optim.state[1]['step'].device,'cpu')
        sac.policy_optim.state[1]['exp_avg']=tensor('cpu')
        with self.assertRaisesRegex(ValueError,'optimizer'):l.actual_devices(sac,replay)
        sac.policy_optim.state[1]['exp_avg']=tensor('cuda:0');replay.map_s=tensor('cpu')
        with self.assertRaisesRegex(ValueError,'replay'):l.actual_devices(sac,replay)

    def test_original_loader_source_keeps_contract_map_pool_unsafe_and_rng_checks(self):
        path=ROOT/'src/task9_lr/runtime/src/task8_lower/training.py'
        tree=ast.parse(path.read_text());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='load_checkpoint')
        config=json.loads(b.local_path(l.INPUTS['config']['path']).read_text());old=l.legacy_contract(self.p)
        payload=dict(format='format',observation_version='obs',action_version='action',contract=old,
                     config=config,map_backend=config['map_backend'],pool_hashes={'pool':'exact'},
                     state={'steps':1000},sac={},replay={'capacity':1},environment={},rng={'exact_rng':True})
        restored=[]
        class SAC:
            def __init__(self,*args):
                self.policy_optim=self.critic_optim=self.alpha_optim=types.SimpleNamespace(param_groups=[])
            def load_full_state_dict(self,value):pass
        class Replay:
            def __init__(self,*args):pass
            def load_state_dict(self,value):pass
        namespace=dict(torch=types.SimpleNamespace(load=lambda *args,**kw:copy.deepcopy(payload),is_tensor=lambda x:False),
            FORMAT='format',VERSION='obs',ACTION_VERSION='action',_contract=lambda:{'current':'new-source'},
            resolve_map_backend=lambda cfg:cfg['map_backend'],_pool_hashes=lambda cfg:{'pool':'exact'},
            LowerSAC=SAC,Replay=Replay,restore_environment=lambda state,device:'restored-env',restore_rng=lambda rng:restored.append(rng))
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
        original=namespace['load_checkpoint'];adapted=l.limited_loader(original,old)
        self.assertIs(adapted.__code__,original.__code__)
        self.assertEqual(adapted('exact-reviewed-path','cuda')[3]['steps'],1000)
        self.assertEqual(restored,[{'exact_rng':True}]);self.assertEqual(namespace['_contract'](),{'current':'new-source'})
        good=copy.deepcopy(payload)
        variants=[]
        changed=copy.deepcopy(good);changed['contract']['files']['scripts/task9_11/worker.py']='0'*64;variants.append(changed)
        changed=copy.deepcopy(good);changed['config']['map_backend']='foreign-backend';variants.append(changed)
        changed=copy.deepcopy(good);changed['pool_hashes']={'pool':'foreign'};variants.append(changed)
        changed=copy.deepcopy(good);changed['state']['unsafe_update']=True;variants.append(changed)
        for changed in variants:
            payload.clear();payload.update(changed)
            with self.assertRaises(ValueError):adapted('exact-reviewed-path','cuda')
        self.assertEqual(len(restored),1)
    def test_missing_or_foreign_preflight_proof_refuses_before_model_import(self):
        exact=b.local_path(l.INPUTS['checkpoint']['path'])
        with self.assertRaises(FileNotFoundError):l.load_legacy_checkpoint(self.p,exact,'cuda',self.root)
        proof=dict(status='PASS_BYTES_BEFORE_MODEL_LOAD',inputs=l.INPUTS,completed_G1=self.p['completed_G1'],legacy_contract_basis={})
        (self.root/'legacy-input-validation.json').write_text(json.dumps(proof))
        with self.assertRaisesRegex(ValueError,'pre-model'):l.load_legacy_checkpoint(self.p,exact,'cuda',self.root)

    def test_bridge_refuses_other_checkpoint_or_device_without_import(self):
        for path,device in [(self.root/'unreviewed.pt','cuda'),(b.local_path(l.INPUTS['checkpoint']['path']),'cpu')]:
            with self.subTest(path=path,device=device),self.assertRaises(ValueError):
                l.load_legacy_checkpoint(self.p,path,device,self.root)
    def test_exact151_changed_science_cannot_use_legacy_bridge(self):
        real=l.stream_sha
        target='src/task9_lr/runtime/src/task8_lower/training.py'
        with patch.object(l,'stream_sha',side_effect=lambda path:'0'*64 if str(path).endswith(target) else real(path)):
            with self.assertRaisesRegex(ValueError,'scientific byte changed'):l.legacy_contract(self.p)
    def test_resource_reader_charges_tensor_windows_in_diagnostics_directory(self):
        p=copy.deepcopy(self.p);out=self.root/'output';out.mkdir()
        p['new_output_root']=str(out);p['new_log_root']=str(self.root/'logs')
        (out/'releases').mkdir();release=out/'releases/gate-evaluate-L-4718.json';release.write_text('{}')
        supervision=out/'supervision/gate-evaluate-L-4718';supervision.mkdir(parents=True)
        (supervision/'reservation.json').write_text(json.dumps(dict(record={'release_sha256':b.sha256(release),'cap_s':1800},reservation_id='test')))
        tensors=out/'recording-on-evaluation.diagnostics';tensors.mkdir();(tensors/'window.pt').write_bytes(b'x'*4096)
        budget=dict(worker_upper_s=60000,gpu_upper_s=120000,storage_upper_bytes=40000000000,
                    diagnostic_upper_bytes=p['max_diagnostic_log_bytes']-2048)
        docroot=b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18'
        with patch.object(b,'validate',return_value=p),patch.object(g,'root',return_value=out),\
             patch.object(g,'release',return_value=dict(max_worker_seconds=1800,budget_review={})),\
             patch.object(g,'checked_budget',return_value=budget),\
             patch.object(b,'local_path',side_effect=lambda path:self.root/'no-agent-logs' if Path(path)==docroot else Path(path)):
            with self.assertRaisesRegex(ValueError,'storage/diagnostic'):
                g.resources(p,out,active_name='gate-evaluate-L-4718')

    def test_exact_L_ON_source_budget_release_schema_and_wrong_stage_refused(self):
        p=self.p;p['_sealed_sha256']='a'*64
        basis=b.bound(b.APPROVAL)
        budget=dict(format='task9-lr-real-L-ON-budget-admission-v1',status='PASS_L_ON_ONLY',reviewer=g.ROLE,
            run_id=p['run_id'],original_started_at=p['started_at'],deadline=p['deadline'],classification='EVIDENCE_UPPER_BOUND_NOT_EXACT_HISTORY',
            basis={key:basis for key in ('historical-worker','historical-gpu','C-policy','open-participants','background-inventory')},
            bound_clock=clock.capture(p),participants=[dict(thread_id='inert',turn_id='inert')],
            rolling_rule='sum-each-listed-open-turn-to-current-monotonic-plus-stage-reservation',worker_upper_s=60000,gpu_upper_s=120000,
            open_worker_upper_rate=4,open_gpu_upper_rate=4,storage_upper_bytes=40000000000,diagnostic_upper_bytes=1000000000,historical_unknown_preserved=True)
        source=dict(format='task9-lr-real-L-ON-source-review-v1',status='PASS',reviewer=g.ROLE,run_id=p['run_id'],
                    source_digest=p['source_digest'],source_manifest=p['source_manifest'],scope='REAL_L_ON_ONLY',evidence=[basis])
        path=self.root/'L_ON_release.json';lease=self.root/'lease.json';lease.write_text(json.dumps(dict(lease_seconds=2220)))
        lease_ref=b.bound(lease)
        token=dict(format='task9-lr-real-L-ON-release-v1',status='PASS',reviewer_task=g.ROLE,run_id=p['run_id'],
            code_hash=p['source_digest'],protocol_sha256=p['_sealed_sha256'],stage='gate-evaluate',arm='L',seed=4718,
            automatic_retry=False,image=g.IMAGE,gpu_uuid=p['preferred_gpu_uuid'],container_id='b'*64,
            independent_release_path=str(path),source_review={'path':'inert-source'},budget_review={'path':'inert-budget'},
            completed_G1=p['completed_G1'],lon_inputs=p['lon_inputs'],legacy_contract_basis=p['legacy_contract_basis'],evaluation_reservation=196,
            max_worker_seconds=1800,control_reserve_s=120,save_reserve_s=120,max_gpu_seconds=2220,allocation_lease=lease_ref,
            expires_at=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat())
        with patch.object(g,'reference',side_effect=lambda ref:source if ref['path']=='inert-source' else budget),\
             patch.object(g,'ISSUER_ROOT',self.root),patch.object(g,'allocation_reference',return_value=lease_ref):
            path.write_text(json.dumps(token));self.assertEqual(g.release(path,p,arm='L')['evaluation_reservation'],196)
            for key,value in [('stage','g1'),('arm','C'),('seed',4719),('evaluation_reservation',392),('max_gpu_seconds',1920)]:
                changed=copy.deepcopy(token);changed[key]=value;path.write_text(json.dumps(changed))
                with self.subTest(key=key),self.assertRaises(ValueError):g.release(path,p,arm='L')
    def test_actual_worker_L_ON_success_route_only_loads_and_evaluates(self):
        from task9_lr import evaluation,diagnostics
        spec=importlib.util.spec_from_file_location('real_lon_inert_success_worker',ROOT/'scripts/task9_11/worker.py')
        worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        p=copy.deepcopy(self.p);p['container_output']=str(self.root)
        output=self.root/'smoke-L-seed4718';contract=self.root/'protocol.json';contract.write_text('{}')
        (self.root/'releases').mkdir();(self.root/'releases/gate-evaluate-L-4718.json').write_text('{}')
        (self.root/'freeze').mkdir();(self.root/'freeze/L_seed4718.json').write_bytes((ROOT/'config/task9/task9_11/L_seed4718.json').read_bytes())
        config=json.loads((self.root/'freeze/L_seed4718.json').read_text());config['total_transfers']=1000
        order=[];checkpoint=b.local_path(l.INPUTS['checkpoint']['path'])
        def preflight(protocol,out):order.append('bytes');return checkpoint
        def load(protocol,path,device,out):
            self.assertEqual(path,checkpoint);order.append('load');return types.SimpleNamespace(env_steps=1000),None,None,{'steps':1000},config
        def evaluate(sac,cfg,path,**kwargs):
            order.append('evaluate');self.assertEqual(cfg,config)
            self.assertTrue(kwargs['recording']);self.assertTrue(kwargs['parity'])
            self.assertEqual(kwargs['protocol']['max_evaluation_episodes'],196)
            return dict(complete=True,wall_s=0.001)
        torch=types.ModuleType('torch');torch.cuda=types.SimpleNamespace(is_available=lambda:True);torch.set_num_threads=lambda n:None
        package=types.ModuleType('task8_lower');package.__path__=[]
        training=types.ModuleType('task8_lower.training')
        training.train=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('training forbidden'))
        training.load_checkpoint=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('unadapted legacy loader forbidden'))
        token=dict(max_worker_seconds=1800,save_reserve_s=120,budget_review={},expires_at=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat())
        with patch.object(worker,'load_protocol',return_value=p),patch.object(b,'validate',return_value=p),\
             patch.object(worker,'read_release',return_value=token),patch.object(worker,'prerequisites'),patch.object(worker,'check_resources'),\
             patch.object(worker.subprocess,'check_output',return_value=''),patch.object(l,'preflight',side_effect=preflight),\
             patch.object(worker,'activate',side_effect=lambda:order.append('activate')),patch.object(l,'load_legacy_checkpoint',side_effect=load),\
             patch.object(g,'checked_budget',return_value=dict(storage_upper_bytes=40000000000,diagnostic_upper_bytes=1000000000)),\
             patch.object(evaluation,'evaluate',side_effect=evaluate),patch.object(diagnostics,'OUTPUT_BUDGET',None),\
             patch.dict(sys.modules,{'torch':torch,'task8_lower':package,'task8_lower.training':training}),\
             patch.dict('os.environ',CUDA_VISIBLE_DEVICES='0',TASK9_PHYSICAL_GPU_UUID=p['preferred_gpu_uuid']):
            self.assertEqual(worker.main(['--arm','L','--seed','4718','--phase','gate-evaluate','--protocol',str(contract),'--output',str(output)]),0)
        self.assertEqual(order,['bytes','activate','load','evaluate'])
        self.assertEqual(json.loads((self.root/'ledger/gate-evaluate-L-4718.json').read_text())['status'],'PASS')

    def test_worker_checkpoint_failure_precedes_activate_and_load(self):
        spec=importlib.util.spec_from_file_location('real_lon_inert_worker',ROOT/'scripts/task9_11/worker.py')
        worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        p=copy.deepcopy(self.p);p['container_output']=str(self.root)
        output=self.root/'smoke-L-seed4718';contract=self.root/'protocol.json';contract.write_text('{}')
        (self.root/'releases').mkdir();release=self.root/'releases/gate-evaluate-L-4718.json';release.write_text('{}')
        with patch.object(worker,'load_protocol',return_value=p),patch.object(b,'validate',return_value=p),\
             patch.object(worker,'read_release',return_value=dict(max_worker_seconds=1800,save_reserve_s=120,expires_at=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat())),\
             patch.object(worker,'prerequisites'),patch.object(worker,'check_resources'),\
             patch.object(worker.subprocess,'check_output',return_value=''),\
             patch.object(l,'preflight',side_effect=ValueError('bad legacy hash')),\
             patch.object(worker,'activate',side_effect=AssertionError('model import must follow hash validation')),\
             patch.dict('os.environ',CUDA_VISIBLE_DEVICES='0',TASK9_PHYSICAL_GPU_UUID=p['preferred_gpu_uuid']):
            with self.assertRaisesRegex(ValueError,'bad legacy hash'):
                worker.main(['--arm','L','--seed','4718','--phase','gate-evaluate','--protocol',str(contract),'--output',str(output)])
        self.assertEqual(json.loads((self.root/'ledger/gate-evaluate-L-4718.json').read_text())['status'],'FAIL')


if __name__=='__main__':unittest.main(verbosity=2)
