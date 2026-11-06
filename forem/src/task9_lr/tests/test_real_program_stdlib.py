"""Program boundary tests. Stdlib only: no model/environment/Docker execution."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from task9_lr import real_program as m,real_batch as b,real_g1 as g
from task9_lr.runtime import artifact_files,source_contract

class ProgramTests(unittest.TestCase):
    def test_fixed_program_arithmetic_and_order(self):
        seq=m.stages();self.assertEqual(len(seq),12)
        self.assertEqual(sum(x['transfers'] for x in seq),12000000)
        self.assertEqual(sum(x['evaluation_episodes'] for x in seq[:8]),9408)
        self.assertEqual(sum(x['evaluation_episodes'] for x in seq[8:]),1184)
        self.assertEqual(m.expected_before(seq[-1])+296,10592)
        self.assertEqual([(x['arm'],x['seed']) for x in seq[::2]][:4],list(m.ORDER))
        for i,x in enumerate(seq):self.assertEqual(x['previous'],None if i==0 else seq[i-1]['name'])
    def test_contract_new_authorization_front_gates_and_science(self):
        p=b.build('t9.11-real-program-fixture',program=True)
        self.assertEqual(p['max_diagnostic_log_bytes'],10*1024**3)
        self.assertEqual(p['consumed']['evaluation_episodes'],1176)
        self.assertEqual(p['authorization'],b.bound(b.APPROVAL))
        for key,value in [('max_diagnostic_log_bytes',8*1024**3),('max_gpu_seconds',208801),('completed_LON',p['completed_G1']),('consumed',{'evaluation_episodes':980})]:
            q=copy.deepcopy(p);q[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):b.validate(q)
    def test_explicit_fixed_activity_no_smoke_or_wrong_seed(self):
        p={'production_worker_adapter':m.ADAPTER}
        for x in m.stages():self.assertEqual(m.stage(p,x['phase'],x['arm'],x['seed']),x)
        for args in [('g1','C',4718),('gate-evaluate','L',4718),('profile','C',4717)]:
            with self.assertRaises(ValueError):m.stage(p,*args)
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError):m.stage(p)
        m.select(p,'profile','L',4719);self.assertEqual(b.stage(p)['name'],'profile-L-4719')
    def test_native_full_source_contract_covers_program_and_final_cli(self):
        p=b.build('t9.11-real-program-fixture',program=True)
        self.assertEqual(source_contract()['files'],p['source_manifest'])
        self.assertIn('src/task9_lr/real_program.py',p['source_manifest'])
        self.assertIn('scripts/task9_11/worker.py',p['source_manifest'])
        q=copy.deepcopy(p);q['source_digest']='0'*64
        with self.assertRaises(ValueError):b.validate(q)
    def test_worker_final_directory_and_4719_identity(self):
        p=b.build('t9.11-real-program-fixture',program=True)
        argv=b.worker_argv(p,'a'*64,'final-test','L',4719,'b'*32)
        self.assertIn('/output/test-L-seed4719',argv[-1]);self.assertIn('final-test-L-4719',argv[-1])
    def test_local_view_keeps_fixed_quota_no_repeated_growth(self):
        p=b.build('t9.11-real-program-fixture',program=True);m.select(p,'remaining','C',4718)
        snap={'files':{p['new_output_root']+'/prior.json':{'bytes':100,'diagnostic':True},str(b.HOST_ROOT/'doc/agent_logs/task9/task9.11/old.json'):{'bytes':500,'diagnostic':True}}}
        budget={'storage_upper_bytes':600,'diagnostic_upper_bytes':600,'historical_storage_snapshot':{}}
        with patch.object(m,'checked_budget',return_value=budget),patch.object(m,'review',return_value=snap):
            first=m.resource_view(p,{'budget_review':{}});second=m.resource_view(p,{'budget_review':{}})
        self.assertEqual(first,second);self.assertEqual(first['max_evaluation_episodes'],2352)
        self.assertEqual(first['external_output_roots'],[])
        self.assertEqual(first['max_output_bytes'],p['max_output_bytes']-500)
        self.assertEqual(first['max_diagnostic_log_bytes'],p['max_diagnostic_log_bytes']-500)
    def test_global_growth_deduplicates_past_and_charges_diagnostic_pt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'out';out.mkdir();logs=root/'logs';logs.mkdir();f=out/'x.diagnostics';f.mkdir();file=f/'window.pt';file.write_bytes(b'12345')
            p={'new_output_root':str(out),'new_log_root':str(logs)}
            snap={'files':{str(file):{'bytes':3,'diagnostic':True}}}
            with patch.object(g,'root',return_value=out),patch.object(b,'HOST_ROOT',root),patch.object(m,'review',return_value=snap):
                self.assertEqual(m.scan_growth(p,{'historical_storage_snapshot':{}}),(2,2))
                file.write_bytes(b'1');self.assertEqual(m.scan_growth(p,{'historical_storage_snapshot':{}}),(0,0))
    def test_second_stage_reads_pointer_to_independent_original(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'reviews').mkdir();seq=m.stages();first,second=seq[:2]
            ref={'path':str(m.AUDIT/'some-real-original.json'),'sha256':'a'*64}
            (root/'reviews'/(first['name']+'.json')).write_text(json.dumps({'independent_verdict':ref}))
            p={'run_id':'fixture','source_digest':'source'}
            verdict={'format':'task9-lr-real-program-stage-verdict-v1','status':'PASS_COMPLETE','reviewer':b.REVIEWER,'run_id':'fixture','activity':first['name'],'source_digest':'source','evaluation_episodes':196,'consumed_transfers':250000,'exact_container_stopped':True,'worker_enclosing_upper_s':100,'evidence':[{'path':'raw','sha256':'x'}]}
            token={'expected_evaluation_before':196,'evaluation_reservation':2156,'predecessor_review':ref}
            with patch.object(g,'root',return_value=root),patch.object(m,'review',return_value=verdict) as read,patch.object(b,'read_ref'):
                m.prerequisites(p,second,token);read.assert_called_once_with(ref)
                token['evaluation_reservation']=2352
                with self.assertRaises(ValueError):m.prerequisites(p,second,token)
    def test_independent_review_namespace_escape_refused(self):
        for path in [m.AUDIT/'..'/'task9.11.18.1/fake.json',Path('/tmp/fake-independent.json')]:
            with self.assertRaises(ValueError):m.review({'path':str(path),'sha256':'a'*64})
    def test_profile_restore_exact_config_and_step_boundary(self):
        from types import SimpleNamespace
        sac=SimpleNamespace(env_steps=250000);config={'total_transfers':3000000,'seed':4718};state={'steps':250000,'validation_pending':None}
        from task9_lr import real_lon
        with patch.object(real_lon,'actual_devices',return_value={'actual':'cuda:0'}):
            self.assertEqual(m.validate_profile_restore(sac,None,state,config,config),{'actual':'cuda:0'})
            for bad in [dict(config,seed=4719),dict(config,total_transfers=250000)]:
                with self.assertRaises(ValueError):m.validate_profile_restore(sac,None,state,bad,config)
            for bad in [dict(state,steps=249999),dict(state,unsafe_update=True),dict(state,validation_pending=250000)]:
                with self.assertRaises(ValueError):m.validate_profile_restore(sac,None,bad,config,config)
            sac.env_steps=249999
            with self.assertRaises(ValueError):m.validate_profile_restore(sac,None,state,config,config)
    def test_production_prepare_separate_allocation_and_receipts(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);out=base/'out';logs=base/'logs';stdout=base/'stdout';stdout.write_text('a'*64)
            p=b.build('t9.11-real-program-fixture',program=True);p.update(new_output_root=str(out),new_log_root=str(logs))
            p['_sealed_sha256']=hashlib.sha256((json.dumps(p,sort_keys=True)+'\n').encode()).hexdigest()
            token={'max_worker_seconds':100,'control_reserve_s':30,'expires_at':p['deadline'],'max_gpu_seconds':130}
            state={'Name':'/fixture','HostConfig':{'DeviceRequests':[{'DeviceIDs':[p['preferred_gpu_uuid']]}]}};seen=[]
            def wait(root,*args,**kw):seen.append(root);return {'path':'inert','sha256':'x'}
            with patch.object(b,'validate'),patch.object(m,'release',return_value=token),patch.object(g,'root',return_value=out),patch.object(m.subprocess,'check_output',return_value=''),patch.object(m.r,'wait_command',side_effect=wait),patch.object(m.r,'validate_wait',return_value={'exit_code':0,'stdout':{'path':str(stdout)}}),patch.object(m.r,'observe_container',return_value={}),patch.object(m.r,'inspection',return_value=(state,{})),patch.object(b,'bound',return_value={'path':'inert','sha256':'x'}):
                m.select(p,'profile','C',4718);m.prepare(p,'release')
                first=out/'allocations/profile-C-4718/allocation-lease.json';old=first.read_bytes()
                m.select(p,'remaining','C',4718);m.prepare(p,'release')
                self.assertTrue((out/'allocations/remaining-C-4718/allocation-lease.json').is_file())
                self.assertEqual(first.read_bytes(),old);self.assertNotEqual(seen[0],seen[1])
                with self.assertRaises(ValueError):m.prepare(p,'release')
    def test_actual_worker_program_profile_and_final_native_routes(self):
        import datetime as dt
        import sys
        import types
        from task9_lr import evaluation,diagnostics
        for phase in ('profile','final-test'):
            with self.subTest(phase=phase),tempfile.TemporaryDirectory() as d:
                root=Path(d);p=b.build('t9.11-real-program-fixture',program=True);p['container_output']=str(root);p['external_output_roots']=[]
                output=root/('formal-C-seed4718' if phase=='profile' else 'test-C-seed4718');(root/'releases').mkdir();(root/'releases'/(phase+'-C-4718.json')).write_text('{}')
                (root/'freeze').mkdir();cfg=b.local_path(p['scientific_configs']['C-4718']['path']);(root/'freeze/C_seed4718.json').write_bytes(cfg.read_bytes());config=json.loads(cfg.read_text())
                spec=importlib.util.spec_from_file_location('inert_program_worker',Path(__file__).resolve().parents[3]/'scripts/task9_11/worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
                order=[]
                class Replay:
                    map_s=types.SimpleNamespace(device='cuda:0')
                    def __len__(self):return 100000
                sac=types.SimpleNamespace(env_steps=250000 if phase=='profile' else 3000000,update_count=123,policy=types.SimpleNamespace(parameters=lambda:iter([types.SimpleNamespace(device='cuda:0')])))
                def load(path,device):
                    order.append('native-load');self.assertEqual(device,'cuda');self.assertEqual(Path(path).name,'profile.pt' if phase=='profile' else 'final.pt')
                    return sac,Replay(),None,{'steps':sac.env_steps,'pending':None,'env_actions':sac.env_steps,'validation_pending':None},config
                def train(cfg,out,**kw):
                    self.assertEqual(phase,'profile');self.assertEqual(kw['pause_after_consumed'],250000);self.assertNotIn('resume',kw);order.append('train');return {'steps':250000}
                def evaluate(*args,**kw):
                    self.assertEqual(phase,'final-test');self.assertEqual(kw['final_manifest'],{'independent':'manifest'});order.append('final296');return {'wall_s':.001,'complete':True}
                torch=types.ModuleType('torch');torch.cuda=types.SimpleNamespace(is_available=lambda:True);torch.set_num_threads=lambda n:None
                package=types.ModuleType('task8_lower');package.__path__=[];training=types.ModuleType('task8_lower.training');training.train=train;training.load_checkpoint=load
                token={'max_worker_seconds':1800,'save_reserve_s':120,'expires_at':p['deadline'],'final_checkpoint':{'path':str(root/'final.pt')}}
                with patch.object(worker,'load_protocol',return_value=p),patch.object(b,'validate'),patch.object(worker,'read_release',return_value=token),patch.object(worker,'prerequisites'),patch.object(worker,'check_resources'),patch.object(worker.subprocess,'check_output',return_value=''),patch.object(worker,'activate',side_effect=lambda:order.append('activate')),patch.object(m,'resource_view',return_value=p),patch.object(m,'final_admission',return_value={'independent':'manifest'}),patch.object(m,'file_ref',return_value=root/'final.pt'),patch.object(m,'validate_profile_restore',return_value={}),patch.object(__import__('task9_lr.real_lon',fromlist=['actual_devices']),'actual_devices',return_value={}),patch.object(evaluation,'evaluate',side_effect=evaluate),patch.object(diagnostics,'OUTPUT_BUDGET',None),patch.dict(sys.modules,{'torch':torch,'task8_lower':package,'task8_lower.training':training}),patch.dict(os.environ,CUDA_VISIBLE_DEVICES='0',TASK9_PHYSICAL_GPU_UUID=p['preferred_gpu_uuid']):
                    self.assertEqual(worker.main(['--arm','C','--seed','4718','--phase',phase,'--protocol',str(root/'protocol.json'),'--output',str(output)]),0)
                self.assertEqual(order,['activate','train','native-load'] if phase=='profile' else ['activate','native-load','final296'])
                self.assertEqual(json.loads((root/'ledger'/(phase+'-C-4718.json')).read_text())['status'],'PASS')
    def test_actual_resources_midstage_remaining_cap_and_nonce_identity(self):
        import datetime as dt
        from task9_lr.runtime import artifact_digest
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);(out/'releases').mkdir();name='profile-C-4718';folder=out/'supervision'/name;folder.mkdir(parents=True)
            p=b.build('t9.11-real-program-fixture',program=True);m.select(p,'profile','C',4718);p['_sealed_sha256']='a'*64
            p['new_output_root']=str(out)
            allocation=out/'allocations'/name;allocation.mkdir(parents=True);lease=allocation/'allocation-lease.json';lease.write_text(json.dumps({'lease_seconds':140}))
            token={'format':'task9-lr-real-program-release-v1','status':'PASS','reviewer_task':b.REVIEWER,'run_id':p['run_id'],'code_hash':artifact_digest(),'protocol_sha256':'a'*64,'stage':'profile','arm':'C','seed':4718,'intended_activity':name,'automatic_retry':False,'image':g.IMAGE,'gpu_uuid':p['preferred_gpu_uuid'],'container_id':'b'*64,'source_review':{},'budget_review':{},'max_worker_seconds':100,'control_reserve_s':20,'save_reserve_s':10,'max_gpu_seconds':140,'expires_at':dt.datetime.fromtimestamp(2101,dt.timezone.utc).isoformat(),'allocation_lease':b.bound(lease)}
            path=out/'releases'/(name+'.json');path.write_text(json.dumps(token));cap_sha=b.sha256(path)
            spec={'protocol':p,'activity':name,'container_id':'b'*64,'started_monotonic':1000,'reservation_id':'nonce','record':{'phase':'profile','arm':'C','seed':4718,'release_sha256':cap_sha,'cap_s':100}}
            reservation=folder/'reservation.json';reservation.write_text(json.dumps(spec))
            budget={'worker_upper_s':100,'gpu_upper_s':100,'open_worker_upper_rate':0,'open_gpu_upper_rate':0,'bound_clock':{'monotonic':900},'future_reserved':{'worker_seconds':120,'gpu_seconds':140},'storage_upper_bytes':100,'diagnostic_upper_bytes':100}
            with patch.object(b,'validate'),patch.object(g,'root',return_value=out),patch.object(g,'release_provenance'),patch.object(m,'source_review'),patch.object(m,'checked_budget',return_value=budget),patch.object(m,'prerequisites'),patch.object(m,'scan_growth',return_value=(0,0)),patch.object(m.time,'monotonic',return_value=1000),patch.object(m.time,'time',return_value=1980):
                self.assertEqual(m.release(path,p)['max_worker_seconds'],100)
                with patch.object(m.time,'monotonic',return_value=1050),patch.object(m.time,'time',return_value=2030):
                    # A fresh full-cap admission at this time must fail, while
                    # the sealed active reservation needs only its remaining50.
                    with self.assertRaises(ValueError):m.release(path,p)
                    result=m.resources(p,out,active_name=name,container_state={'Id':'b'*64,'HostConfig':{'DeviceRequests':[{'DeviceIDs':[p['preferred_gpu_uuid']]}]}})
                    self.assertEqual(result['evaluation_episodes'],1176)
                    with self.assertRaises(ValueError):m.resources(p,out,active_name=name,container_state={'Id':'c'*64})
                    with patch.dict(os.environ,TASK9_LR_RESERVATION='wrong'),patch.object(m,'ASSET_ROOT',Path('/workspace')),patch.object(b,'validate'):
                        with self.assertRaises(ValueError):m.resources(p,out,active_name=name)
                    changed=dict(spec);changed['container_id']='c'*64;reservation.write_text(json.dumps(changed))
                    with self.assertRaises(ValueError):m.resources(p,out,active_name=name)
                    reservation.write_text(json.dumps(spec))
                with patch.object(m.time,'monotonic',return_value=1100),patch.object(m.time,'time',return_value=2080):
                    with self.assertRaises(ValueError):m.resources(p,out,active_name=name)
    def test_single_physical_gpu_rejects_extra_request_or_uuid(self):
        p={'preferred_gpu_uuid':'GPU-only'}
        m.validate_single_gpu_allocation({'HostConfig':{'DeviceRequests':[{'DeviceIDs':['GPU-only']}]}},p)
        for req in [[],[{'DeviceIDs':['GPU-only','GPU-other']}],[{'DeviceIDs':['GPU-only']},{'DeviceIDs':['GPU-other']}],[{'DeviceIDs':['GPU-other']}]]:
            with self.assertRaises(ValueError):m.validate_single_gpu_allocation({'HostConfig':{'DeviceRequests':req}},p)
    def test_finite_independent_envelope_allows_new_caps_without_science_change(self):
        import datetime as dt
        p=b.build('t9.11-real-program-fixture',program=True)
        limits={'format':'task9-lr-program-resource-envelope-v1','status':'APPROVED_FINITE_LIMITS','reviewer':b.REVIEWER,'authorization':p['necessary_budget_authorization'],'original_started_at':p['started_at'],'simultaneous_gpu_cards':1,'historical_consumption_retained':True,'historical_unknown_preserved':True,'scientific_budget_changed':False,'basis':[{}],'max_worker_seconds':576000,'max_gpu_seconds':576000,'max_output_bytes':2*1024**4,'max_diagnostic_log_bytes':16*1024**3,'deadline':p['deadline'],'max_wall_seconds':p['max_wall_seconds']}
        ref={'path':str(m.AUDIT/'finite-envelope-fixture.json'),'sha256':'e'*64}
        actual_review=m.review;original=b.read_ref
        def review(e):return limits if e==ref else actual_review(e)
        with patch.object(m,'review',side_effect=review),patch.object(b,'read_ref',wraps=b.read_ref) as read:
            # Only the finite envelope basis is synthetic; original authorizations
            # and front gate receipts continue through the real reader.
            read.side_effect=lambda e:{} if e=={} else original(e)
            q=b.build('t9.11-real-program-fixture',program=True,budget_envelope=ref)
            self.assertEqual(q['max_worker_seconds'],576000);self.assertEqual(q['max_diagnostic_log_bytes'],16*1024**3)
            self.assertEqual(q['scientific_configs'],p['scientific_configs']);self.assertEqual(q['consumed'],p['consumed'])
            for field,bad in [('max_gpu_seconds',float('inf')),('historical_unknown_preserved',False),('max_wall_seconds',1),('simultaneous_gpu_cards',2)]:
                old=limits[field];limits[field]=bad
                with self.subTest(field=field),self.assertRaises(ValueError):b.build('t9.11-real-program-fixture',program=True,budget_envelope=ref)
                limits[field]=old
    def test_no_final_before_independent_development(self):
        with patch.object(m,'review',return_value={'status':'FAIL'}):
            with self.assertRaises(ValueError):m.final_admission({}, {'development_review':{}},'C',4718)
    def test_receipt_whitelist_both_writer_and_reader_include_program(self):
        import inspect
        from task9_lr import real_receipts
        for phase in ('profile','remaining','final-test'):
            self.assertIn(repr(phase),inspect.getsource(real_receipts.wait_command))
            self.assertIn(repr(phase),inspect.getsource(real_receipts.validate_wait))
    def test_cli_requires_explicit_activity_before_program_prepare(self):
        spec=importlib.util.spec_from_file_location('program_cli',Path(__file__).resolve().parents[3]/'scripts/task9_11/real_batch.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with patch.object(cli.batch,'read',return_value={'production_worker_adapter':m.ADAPTER}):
            with self.assertRaises(SystemExit):cli.main(['--prepare-program','--contract','/tmp/no-contract'])

class ContainerReferenceTests(unittest.TestCase):
    def test_actual_admission_release_identical_HOST_and_container_lease_reference(self):
        import datetime as dt
        from task9_lr import admission
        from task9_lr.runtime import artifact_digest
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);name='profile-C-4718';allocation=out/'allocations'/name;allocation.mkdir(parents=True)
            lease=allocation/'allocation-lease.json';lease.write_text(json.dumps({'lease_seconds':140}))
            p=b.build('t9.11-real-program-domain-fixture',program=True);m.select(p,'profile','C',4718);p['_sealed_sha256']='a'*64
            hostout=Path(p['new_output_root']);hostlease=hostout/'allocations'/name/'allocation-lease.json'
            lease_ref={'path':str(hostlease),'sha256':b.sha256(lease)}
            token={'format':'task9-lr-real-program-release-v1','status':'PASS','reviewer_task':b.REVIEWER,'run_id':p['run_id'],'code_hash':artifact_digest(),'protocol_sha256':'a'*64,'stage':'profile','arm':'C','seed':4718,'intended_activity':name,'automatic_retry':False,'image':g.IMAGE,'gpu_uuid':p['preferred_gpu_uuid'],'container_id':'b'*64,'source_review':{},'budget_review':{},'max_worker_seconds':100,'control_reserve_s':20,'save_reserve_s':10,'max_gpu_seconds':140,'expires_at':dt.datetime.fromtimestamp(2101,dt.timezone.utc).isoformat(),'allocation_lease':lease_ref}
            release=out/'release.json';release.write_text(json.dumps(token))
            budget={'worker_upper_s':100,'gpu_upper_s':100,'open_worker_upper_rate':0,'open_gpu_upper_rate':0,'bound_clock':{'monotonic':900},'future_reserved':{'worker_seconds':120,'gpu_seconds':140}}
            native_local=b.local_path
            def mapped(path):
                path=Path(path)
                if path.is_relative_to(hostout):return out/path.relative_to(hostout)
                if path.is_relative_to('/output'):return out/path.relative_to('/output')
                return path
            results=[]
            for domain in (b.HOST_ROOT,Path('/workspace')):
                with self.subTest(domain=domain),patch.object(b,'ASSET_ROOT',domain),patch.object(m,'ASSET_ROOT',domain),patch.object(g,'ASSET_ROOT',domain):
                    # Exercise the real host-to-/workspace mapper separately;
                    # substitute only filesystem locations unavailable on host.
                    self.assertEqual(native_local(hostlease),Path('/workspace')/hostlease.relative_to(b.HOST_ROOT) if domain==Path('/workspace') else hostlease)
                    with patch.object(b,'local_path',side_effect=mapped),patch.object(g,'release_provenance'),patch.object(m,'source_review'),patch.object(m,'checked_budget',return_value=budget),patch.object(m,'prerequisites'),patch.object(m.time,'time',return_value=1980),patch.object(m.time,'monotonic',return_value=1000):
                        self.assertEqual(m.allocation_reference(p),lease_ref)
                        self.assertEqual(g.root(p),Path('/output') if domain==Path('/workspace') else hostout)
                        results.append(admission.read_release(release,'profile',p,arm='C',seed=4718))
                        bad=dict(token,allocation_lease=dict(lease_ref,path='/output/allocations/'+name+'/allocation-lease.json'));release.write_text(json.dumps(bad))
                        with self.assertRaises(ValueError):admission.read_release(release,'profile',p,arm='C',seed=4718)
                        release.write_text(json.dumps(token))
            self.assertEqual(results[0],results[1])
    def test_program_other_evidence_references_are_HOST_canonical(self):
        # Predecessors are ref-only pointers to independent HOST originals;
        # final bundle refs are constrained to p.new_output_root, not /output.
        import inspect
        src=inspect.getsource(m.prerequisites)
        self.assertIn("review(pointer['independent_verdict'])",src)
        self.assertNotIn('b.bound(out',src)
        self.assertIn("Path(p['new_output_root'])",inspect.getsource(m.final_admission))
        self.assertIn("b.local_path(ref['path'])",inspect.getsource(m.file_ref))

if __name__=='__main__':unittest.main()
