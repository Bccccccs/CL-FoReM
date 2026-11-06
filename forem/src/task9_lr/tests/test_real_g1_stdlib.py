"""Real G1 admission integration with inert review/subprocess doubles only."""
import copy
import datetime as dt
import importlib.util
import json
import hashlib
import shlex
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from task9_lr import clock, real_batch as b, real_g1 as g


class RealG1GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.p=b.build('t9.11-real-g1-gate-tests');self.p['_sealed_sha256']='a'*64
        basis=b.bound(b.APPROVAL)
        self.budget=dict(format='task9-lr-real-G1-budget-admission-v1',status='PASS_G1_ONLY',
            reviewer=g.ROLE,run_id=self.p['run_id'],original_started_at=self.p['started_at'],deadline=self.p['deadline'],
            classification='EVIDENCE_UPPER_BOUND_NOT_EXACT_HISTORY',
            basis={key:basis for key in ('historical-worker','historical-gpu','C-policy','open-participants','background-inventory')},
            bound_clock=clock.capture(self.p),participants=[dict(thread_id='inert-thread',turn_id='inert-turn')],
            rolling_rule='sum-each-listed-open-turn-to-current-monotonic-plus-stage-reservation',
            worker_upper_s=50000,gpu_upper_s=110000,open_worker_upper_rate=4,open_gpu_upper_rate=4,
            storage_upper_bytes=35000000000,diagnostic_upper_bytes=1000000000,historical_unknown_preserved=True)
        self.source=dict(format='task9-lr-real-G1-source-review-v1',status='PASS',reviewer=g.ROLE,
            run_id=self.p['run_id'],source_digest=self.p['source_digest'],source_manifest=self.p['source_manifest'],
            scope='REAL_G1_ONLY',evidence=[basis])
        self.token=dict(format='task9-lr-real-G1-release-v1',status='PASS',reviewer_task=g.ROLE,
            run_id=self.p['run_id'],code_hash=self.p['source_digest'],protocol_sha256=self.p['_sealed_sha256'],
            stage='g1',arm='C',seed=4718,automatic_retry=False,image=g.IMAGE,gpu_uuid=self.p['preferred_gpu_uuid'],
            source_review={'path':'mock-source'},budget_review={'path':'mock-budget'},container_id='b'*64,
            max_worker_seconds=1800,max_gpu_seconds=1860,control_reserve_s=60,save_reserve_s=10,
            expires_at=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat())
        self.path=self.root/'release.json'
        self.token['independent_release_path']=str(self.path)
        (self.root/'allocation-lease.json').write_text(json.dumps(dict(lease_seconds=1860,admission_deadline_epoch=9999999999)))
        self.token['allocation_lease']=b.bound(self.root/'allocation-lease.json')
    def tearDown(self):self.tmp.cleanup()
    def reviewed(self,ref):
        # Deliberate unit double, never published as an actual independent review.
        return self.source if ref['path']=='mock-source' else self.budget
    def release(self,token=None):
        self.path.write_text(json.dumps(token or self.token))
        with patch.object(g,'reference',side_effect=self.reviewed),patch.object(g,'ISSUER_ROOT',self.root),patch.object(g,'root',return_value=self.root),patch.object(g,'allocation_reference',return_value=self.token['allocation_lease']):return g.release(self.path,self.p)
    def test_valid_upper_bound_not_exact_is_accepted(self):
        result=self.release();self.assertEqual(result['stage'],'g1')
        self.assertTrue(self.budget['historical_unknown_preserved'])
    def test_different_source_container_or_protocol_refused(self):
        for key,value in [('code_hash','c'*64),('container_id','name'),('protocol_sha256','d'*64),
                          ('stage','profile'),('arm','L'),('seed',4719),('automatic_retry',True),('gpu_uuid','other')]:
            token=copy.deepcopy(self.token);token[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.release(token)
    def test_missing_old_gpu_basis_or_worker_participants_refused(self):
        self.budget['basis'].pop('historical-gpu')
        with self.assertRaises(ValueError):self.release()
    def test_unknown_preserved_cannot_be_removed(self):
        self.budget['historical_unknown_preserved']=False
        with self.assertRaises(ValueError):self.release()
    def test_current_full_team_and_gpu_roll_forward_refuse_budget_overrun(self):
        self.budget['worker_upper_s']=207000
        with self.assertRaisesRegex(ValueError,'budget exceeded'):self.release()
        self.budget['worker_upper_s']=50000;self.budget['gpu_upper_s']=207000
        with self.assertRaisesRegex(ValueError,'budget exceeded'):self.release()
    def test_three_participant_assumption_not_accepted(self):
        self.budget['open_worker_upper_rate']=3
        with self.assertRaisesRegex(ValueError,'four'):self.release()
    def test_stage_expiry_and_control_reserved_separately(self):
        token=copy.deepcopy(self.token);token['expires_at']=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=1800)).isoformat()
        with self.assertRaises(ValueError):self.release(token)
        token=copy.deepcopy(self.token);token['control_reserve_s']=0
        with self.assertRaises(ValueError):self.release(token)
        token=copy.deepcopy(self.token);token['max_gpu_seconds']=1800
        with self.assertRaises(ValueError):self.release(token)
    def test_container_allocation_evidence_preserves_host_path_identity(self):
        host=Path(self.p['new_output_root'])/'allocation-lease.json'
        with patch.object(b,'ASSET_ROOT',Path('/workspace')),patch.object(b,'sha256',return_value='f'*64) as digest:
            ref=g.allocation_reference(self.p)
        self.assertEqual(ref,dict(path=str(host),sha256='f'*64))
        self.assertEqual(digest.call_args.args[0],Path('/workspace')/host.relative_to(b.HOST_ROOT))
    def test_short_worker_does_not_refund_longer_allocation_lease(self):
        token=copy.deepcopy(self.token);token.update(max_worker_seconds=120,max_gpu_seconds=180)
        with self.assertRaisesRegex(ValueError,'allocation reservation'):self.release(token)
        token['max_gpu_seconds']=1860
        self.assertEqual(self.release(token)['max_gpu_seconds'],1860)
    def test_release_outside_independent_namespace_refused(self):
        token=copy.deepcopy(self.token);token['independent_release_path']='/tmp/untrusted.json'
        with self.assertRaisesRegex(ValueError,'independent immutable'):self.release(token)
    def test_exact_cleanup_identity_does_not_reopen_expired_admission(self):
        self.path.write_text(json.dumps(self.token))
        out=self.root/'output';(out/'releases').mkdir(parents=True)
        copied=out/'releases/g1-C-4718.json';copied.write_bytes(self.path.read_bytes())
        spec=dict(protocol=self.p,activity='g1-C-4718',container_id=self.token['container_id'],
                  record={'release_sha256':b.sha256(copied)})
        with patch.object(g,'root',return_value=out),patch.object(g,'ISSUER_ROOT',self.root),\
             patch.object(g,'release',side_effect=AssertionError('expired admission must not block exact cleanup')):
            self.assertEqual(g.spec_gate(spec)['container_id'],self.token['container_id'])
            spec['container_id']='name'
            with self.assertRaises(ValueError):g.spec_gate(spec)
    def test_same_id_restart_changes_temporal_allocation_identity(self):
        state=dict(Id='a'*64,Image=g.IMAGE,Mounts=[],Config={'User':'1000:1000'},
                   HostConfig={'DeviceRequests':[]},State={'StartedAt':'2026-11-04T01:00:00Z'},RestartCount=0)
        original=g.container_identity(state)
        state['RestartCount']=1
        self.assertNotEqual(g.container_identity(state),original)
        state['RestartCount']=0;state['State']['StartedAt']='2026-11-04T02:00:00Z'
        self.assertNotEqual(g.container_identity(state),original)
    def test_mount_order_is_not_allocation_identity_but_all_fields_are(self):
        mounts=[dict(Type='bind',Source='/host/output',Destination='/output',RW=True,Propagation='rprivate'),
                dict(Type='bind',Source='/host/workspace',Destination='/workspace',RW=False,Propagation='rprivate')]
        state=dict(Id='a'*64,Image=g.IMAGE,Mounts=mounts,Config={'User':'1000:1000'},
                   HostConfig={'DeviceRequests':[]},State={'StartedAt':'2026-11-04T01:00:00Z'},RestartCount=0)
        original=g.container_identity(state)
        state['Mounts']=list(reversed(mounts))
        self.assertEqual(g.container_identity(state),original)
        # container and host readers must normalize the same raw Docker facts;
        # ASSET_ROOT must not rewrite Source/Destination mount identity.
        with patch.object(b,'ASSET_ROOT',Path('/workspace')):
            self.assertEqual(g.container_identity(state),original)
        for key,value in [('Source','/other'),('Destination','/elsewhere'),('RW',True),
                          ('Propagation','shared'),('Type','volume'),('ExtraField','must-remain-visible')]:
            changed=copy.deepcopy(state);changed['Mounts'][0][key]=value
            with self.subTest(key=key):self.assertNotEqual(g.container_identity(changed),original)
        duplicate=copy.deepcopy(state);duplicate['Mounts'].append(copy.deepcopy(duplicate['Mounts'][0]))
        self.assertNotEqual(g.container_identity(duplicate),original)

    def test_actual_prepare_route_keeps_two_run_receipts_independent(self):
        # Every device/Docker operation is an explicit inert double. The actual
        # production prepare path, namespaces, freeze and receipt roots execute.
        infrastructure=self.root/'independent-infrastructure.json'
        infrastructure.write_text('{}')
        token=dict(max_worker_seconds=1800,control_reserve_s=120,max_gpu_seconds=1920,
                   expires_at=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat())
        waits=[];inspects=[]
        def mock_wait(directory,argv,**kwargs):
            directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
            self.assertEqual(shlex.split(argv[3])[:2],['docker','run'])
            cid=hashlib.sha256(kwargs['run_id'].encode()).hexdigest()
            (directory/'stdout.txt').write_text(cid+'\n')
            (directory/'mock-wait.json').write_text(json.dumps(dict(exit_code=0,stdout={'path':str(directory/'stdout.txt')})))
            waits.append(directory)
            return b.bound(directory/'mock-wait.json')
        def mock_observe(directory,cid,**kwargs):
            directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
            (directory/'mock-inspect.json').write_text(json.dumps(dict(Id=cid,Name='/inert-'+cid[:8])))
            inspects.append(directory)
            return b.bound(directory/'mock-inspect.json')
        with patch.object(b,'validate',side_effect=lambda p:p),patch.object(b,'RECEIPT_ROOT',self.root/'commands'),\
             patch.object(g,'release',return_value=token),patch.object(g.subprocess,'check_output',return_value=''),\
             patch.object(g.r,'wait_command',side_effect=mock_wait),\
             patch.object(g.r,'validate_wait',side_effect=b.read_ref),\
             patch.object(g.r,'observe_container',side_effect=mock_observe),\
             patch.object(g.r,'inspection',side_effect=lambda ref:(b.read_ref(ref),None)):
            for label in ('first','second'):
                p=copy.deepcopy(self.p);p.pop('_sealed_sha256')
                p.update(run_id='t9.11-real-inert-'+label,new_output_root=str(self.root/('output-'+label)),
                         new_log_root=str(self.root/('logs-'+label)))
                p['_sealed_sha256']=hashlib.sha256((json.dumps(p,sort_keys=True)+'\n').encode()).hexdigest()
                result=g.prepare(p,infrastructure)
                self.assertEqual(result['container_id'],hashlib.sha256(p['run_id'].encode()).hexdigest())
                self.assertEqual(waits[-1],b.receipt_root(p)/'infrastructure-launch')
                self.assertEqual(inspects[-1],b.receipt_root(p)/'infrastructure-inspect')
                with self.assertRaisesRegex(ValueError,'already consumed'):g.prepare(p,infrastructure)
        self.assertEqual(len(set(waits)),2);self.assertEqual(len(set(inspects)),2)

    def test_actual_worker_route_reaches_only_g1_subprocess_after_gates(self):
        spec=importlib.util.spec_from_file_location('real_g1_worker_inert_check',ROOT/'scripts/task9_11/worker.py')
        worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        (self.root/'releases').mkdir()
        (self.root/'releases/g1-C-4718.json').write_text(json.dumps(self.token))
        output=self.root/'g1';protocol_path=self.root/'protocol.json';protocol_path.write_text('{}')
        p=copy.deepcopy(self.p);p['container_output']=str(self.root)
        # Validator, reviewer, resource and nvidia calls are explicit inert
        # doubles; the actual worker parser/ledger/phase/G1 code executes.
        def fake_run(argv,**kwargs):
            self.assertEqual(argv,worker.g1_test_command())
            (output/'device-path.json').write_text(json.dumps(dict(policy_device='cuda:0',replay_device='cuda:0')))
            return type('Result',(),{'returncode':0})()
        with patch.object(worker,'load_protocol',return_value=p),patch.object(b,'validate',return_value=p),\
             patch.object(worker,'read_release',return_value=self.token),patch.object(worker,'prerequisites'),\
             patch.object(worker,'check_resources'),patch.object(worker.subprocess,'check_output',return_value=''),\
             patch.object(worker.subprocess,'run',side_effect=fake_run),\
             patch.object(worker,'activate',side_effect=AssertionError('model import forbidden in G1 worker')),\
             patch.dict('os.environ',CUDA_VISIBLE_DEVICES='0',TASK9_PHYSICAL_GPU_UUID=p['preferred_gpu_uuid']):
            self.assertEqual(worker.main(['--arm','C','--seed','4718','--phase','g1','--protocol',str(protocol_path),'--output',str(output)]),0)
        record=json.loads((self.root/'ledger/g1-C-4718.json').read_text())
        self.assertEqual(record['status'],'PASS');self.assertGreater(record['worker_wall_s'],0)


if __name__=='__main__':unittest.main(verbosity=2)
