"""Actual production dispatch and admission with only external execution replaced.

Direct stdlib runner; no pytest/conftest, models, environment, or Docker calls.
"""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

FOREM=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(FOREM/'src'))
from task9_lr import admission, clock
from task9_lr.runtime import sha256

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

s=module('candidate_supervise',FOREM/'scripts/task9_11/supervise.py')
fixtures=module('candidate_json_fixture',Path(__file__).with_name('test_continuation_stdlib.py'))
legacy=module('candidate_process_fixture',Path(__file__).with_name('test_supervision_stdlib.py'))
SELF=Path(__file__).resolve()


class Backend(legacy.PlaceholderBackend):
    terminal_budget_s=.1
    def resources(self):
        super().resources()
        state=json.loads((Path(self.value['output'])/'container-inspect.json').read_text())
        s.dump(self.root/'container-observed.json',dict(observed_epoch=clock.epoch(self.value['protocol']),inspect=state))
        admission.check_resources(self.value['protocol'],self.value['output'],active_name=self.value['activity'],container_state=state)
        (self.root/'production-resources-checked').touch()


class Adapter:
    terminal_budget_s=.1
    backend_factory=Backend
    def __init__(self,p,duration=.08,owner_sleep=False):self.p=p;self.duration=duration;self.owner_sleep=owner_sleep;self.calls=0
    def inspect(self,container):
        self.calls+=1
        return json.loads((Path(self.p['new_output_root'])/'container-inspect.json').read_text())
    def worker_command(self,phase,arm,seed,reservation):
        path=Path(self.p['new_output_root'])/'supervision'/f'{phase}-{arm}-{seed}'/'guard-spec.json'
        return [sys.executable,'-B',str(SELF),'--worker',str(path),str(self.duration)]
    def owner_command(self,path):
        if self.owner_sleep:return [sys.executable,'-B','-c','import time; time.sleep(10)']
        return [sys.executable,'-B',str(SELF),'--fixture','owner',str(path)]


def fixture(role,path):
    value=json.loads(Path(path).read_text());folder=Path(value['supervision_dir'])
    if role=='owner':
        os.environ.update(TASK9_LR_ACTIVITY=value['activity'],TASK9_LR_RESERVATION=value['reservation_id'],TASK9_LR_LOG_PATH=value['log_path'])
        command=[sys.executable,'-B',str(SELF),'--fixture','guard',str(folder/'owned-spec.json')]
        return s.owner(path,int(os.environ['TASK9_LR_LOCK_FD']),guard_command=command)
    if role=='guard':
        command=[sys.executable,'-B',str(SELF),'--fixture','watch',str(folder/'watch-spec.json')]
        return s.guard(path,int(os.environ['TASK9_LR_LOCK_FD']),backend_factory=Backend,watch_command=command)
    return s.watch(value,Backend(value))


class WorkerExecutionAdapter:
    """Only replace scientific execution after actual production worker admission."""
    def __init__(self,spec,duration):self.spec=spec;self.duration=duration
    def run(self,a,protocol,out,token):
        root=Path(protocol['new_output_root']);name=self.spec['activity']
        ledger=json.loads((root/'ledger'/(name+'.json')).read_text())
        if ledger['status']!='started' or ledger['release_sha256']!=sha256(root/'releases'/(name+'.json')):
            raise ValueError('production worker write-ahead ledger missing before callback')
        if os.environ.get('TASK9_LR_RESERVATION')!=self.spec['reservation_id']:
            raise ValueError('worker callback reservation mismatch')
        # This marker is reached only after real main.load/read_release /
        # prerequisites / check_resources and its write-ahead ledger.
        (root/('launched-'+name)).write_text(self.spec['reservation_id'])
        (Path(self.spec['supervision_dir'])/'production-worker-admission-completed').touch()
        time.sleep(self.duration)
        return dict(status='PASS')


def worker_fixture(path,duration):
    spec=json.loads(Path(path).read_text());record=spec['record'];root=Path(spec['output'])
    os.environ.update(TASK9_LR_ACTIVITY=spec['activity'],TASK9_LR_RESERVATION=spec['reservation_id'],TASK9_LR_LOG_PATH=spec['log_path'])
    worker=module('candidate_production_worker',FOREM/'scripts/task9_11/worker.py')
    argv=['--phase',record['phase'],'--arm',record['arm'],'--seed',str(record['seed']),
          '--protocol',str(root/'freeze/protocol.json'),'--output',str(Path(spec['stop_path']).parent)]
    return worker.main(argv,execution_adapter=WorkerExecutionAdapter(spec,float(duration)))


class CandidateLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='t9-lifecycle-')
        self.p=fixtures.make_fixture(self.tmp.name);self.out=Path(self.p['new_output_root']);self.processes=[]
        (self.out/'activities').mkdir();(self.out/'releases').mkdir()
        state=dict(Id='synthetic-exact-container',Name='/synthetic',Image='synthetic',Mounts=[],
                   Config=dict(User='synthetic'),HostConfig=dict(DeviceRequests=[]),State=dict(Running=True))
        fixtures.bound(self.out/'container-inspect.json',state)
    def tearDown(self):
        for p in self.processes:
            if p.poll() is None:p.kill()
            p.wait(timeout=3)
        for path in self.out.rglob('*-ready.json'):
            try:
                identity=json.loads(path.read_text())['identity']
                if identity['pid']!=os.getpid():s.exact_kill(identity,group=True)
            except (OSError,KeyError):pass
        for path in self.out.rglob('worker-started.json'):
            try:s.exact_kill(json.loads(path.read_text())['identity'],group=True)
            except OSError:pass
        self.tmp.cleanup()
    def release(self,stage='g1',arm='C',seed=4718,cap=3.):
        token=fixtures.fixture_release(self.p,stage,arm,seed);token.update(max_worker_seconds=cap,save_reserve_s=.3)
        path=self.out/'releases'/f'{stage}-{arm}-{seed}.json';fixtures.bound(path,token);return path
    def dispatch(self,stage='g1',arm='C',seed=4718,adapter=None):
        return s.dispatch(self.p,'synthetic',stage,arm,seed,execution_adapter=adapter or Adapter(self.p))
    def until(self,path,timeout=4):
        cutoff=time.monotonic()+timeout
        while not path.exists():
            if time.monotonic()>cutoff:self.fail('bounded fixture timeout '+str(path))
            time.sleep(.01)
        return json.loads(path.read_text())
    def test_dispatch_actual_chain_closed_then_next_legal_stage_and_idempotent(self):
        self.release();adapter=Adapter(self.p)
        self.assertEqual(self.dispatch(adapter=adapter),'passed')
        rows=admission.activity_rows(self.out,protocol=self.p);self.assertEqual(len(rows),1)
        row=rows[0];closure=json.loads((self.out/'supervision/g1-C-4718/closure.json').read_text())
        self.assertEqual(closure['status'],'CLOSED');self.assertEqual(closure['execution_allowed'],False)
        self.assertGreater(row['job_wall_s'],0);self.assertEqual(row['control_charged_s'],30.)
        life=json.loads((self.out/'supervision/g1-C-4718/lifecycle.json').read_text())
        self.assertEqual(life['chain_status'],'PASS');self.assertFalse(s.alive(life['owner']['identity']))
        self.assertEqual(life['owner']['waiter'],s.process_identity())
        self.assertEqual(set(life['waits']),{'guardian','watcher'})
        self.assertTrue((self.out/'supervision/g1-C-4718/production-worker-admission-completed').exists())
        self.assertEqual(json.loads((self.out/'ledger/g1-C-4718.json').read_text())['status'],'PASS')
        before=admission.check_resources(self.p,self.out)
        self.assertAlmostEqual(before['worker_seconds'],103+row['wall_s'])
        calls=adapter.calls;self.assertEqual(self.dispatch(adapter=adapter),'already_passed');self.assertEqual(adapter.calls,calls)
        self.assertEqual(admission.check_resources(self.p,self.out)['worker_seconds'],before['worker_seconds'])
        with self.assertRaisesRegex(ValueError,'NOT_READY'):s.dispatch(self.p,'synthetic','g1','C',4718)
        self.release('gate-evaluate','L');self.assertEqual(self.dispatch('gate-evaluate','L'),'passed')
        self.assertEqual(len(admission.activity_rows(self.out,protocol=self.p)),2)
    def test_entire_continuation_DAG_runs_through_production_dispatch(self):
        jobs=[]
        for phase in ('smoke-and-gates','train','final-test'):jobs+=s.continuation.jobs(self.p,phase)
        self.assertEqual(len(jobs),14)
        self.release('profile','C',4718)
        with self.assertRaisesRegex(ValueError,'prerequisite'):self.dispatch('profile','C',4718)
        self.assertFalse((self.out/'supervision').exists())
        for stage,arm,seed in jobs:
            self.release(stage,arm,seed,cap=6.)
            self.assertEqual(self.dispatch(stage,arm,seed,adapter=Adapter(self.p,duration=.01)),'passed')
            self.assertTrue((self.out/'supervision'/f'{stage}-{arm}-{seed}'/'production-resources-checked').exists())
            self.assertTrue((self.out/'supervision'/f'{stage}-{arm}-{seed}'/'production-worker-admission-completed').exists())
            self.assertEqual(json.loads((self.out/'ledger'/f'{stage}-{arm}-{seed}.json').read_text())['status'],'PASS')
        rows=admission.activity_rows(self.out,protocol=self.p)
        self.assertEqual([(r['phase'],r['arm'],r['seed']) for r in rows],sorted(jobs))
        cost=admission.check_resources(self.p,self.out)
        self.assertAlmostEqual(cost['worker_seconds'],103.+sum(r['job_wall_s']+30. for r in rows))
        self.assertEqual(cost['evaluation_episodes'],980)
        for row in rows:
            self.assertNotIn(row['phase'],('smoke512','smoke1000'))
            self.assertFalse(row['phase']=='gate-evaluate' and row['arm']=='C')
    def test_closed_receipt_tamper_or_missing_blocks_reuse(self):
        self.release();self.dispatch();path=self.out/'supervision/g1-C-4718/closure.json';original=path.read_text()
        for defect in ('missing','wrong-charge','wrong-run','wrong-wait'):
            with self.subTest(defect=defect):
                value=json.loads(original)
                if defect=='missing':path.unlink()
                else:
                    if defect=='wrong-charge':value['charged_wall_s']+=1
                    if defect=='wrong-run':value['run_id']='old'
                    if defect=='wrong-wait':value['owner_wait']['exit_code']=9
                    path.write_text(json.dumps(value))
                with self.assertRaises((ValueError,FileNotFoundError)):admission.check_resources(self.p,self.out)
                path.write_text(original)
    def test_outer_wait_timeout_stops_and_actually_reaps_without_cap_plus_tail(self):
        self.release(cap=.9);before=time.monotonic()
        with self.assertRaises((RuntimeError,FileNotFoundError,ValueError)):self.dispatch(adapter=Adapter(self.p,owner_sleep=True))
        self.assertLess(time.monotonic()-before,1.7)
        folder=self.out/'supervision/g1-C-4718';self.assertTrue((folder/'stopped').exists());self.assertFalse((folder/'closure.json').exists())
        life=json.loads((folder/'lifecycle.json').read_text())
        self.assertEqual(life['chain_status'],'UNKNOWN');self.assertEqual(life['owner']['exit_code'],-signal.SIGKILL)
        self.assertFalse(s.alive(life['owner']['identity']))
    def test_outer_identity_read_failure_stops_and_remains_unknown(self):
        self.release()
        original=s.process_identity
        def failing(pid=None):
            if pid is not None:raise PermissionError('injected identity read denied')
            return original()
        with mock.patch.object(s,'process_identity',side_effect=failing):
            with self.assertRaises((RuntimeError,FileNotFoundError,ValueError)):self.dispatch()
        folder=self.out/'supervision/g1-C-4718';self.assertTrue((folder/'stopped').exists());self.assertFalse((folder/'closure.json').exists())
        life=json.loads((folder/'lifecycle.json').read_text());self.assertEqual(life['chain_status'],'UNKNOWN')
        self.assertTrue(any('identity' in error for error in life['errors']))
    def test_corrupt_terminal_and_closure_publication_failure_stop_no_admission(self):
        self.release();original=s.outer_wait
        def corrupt(spec,process,**kw):
            value=original(spec,process,**kw);(Path(spec['supervision_dir'])/'terminal.json').write_text('{');return value
        with mock.patch.object(s,'outer_wait',side_effect=corrupt):
            with self.assertRaises(ValueError):self.dispatch()
        self.assertFalse((self.out/'supervision/g1-C-4718/closure.json').exists())
        self.assertTrue((self.out/'supervision/g1-C-4718/stopped').exists())
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
    def test_linked_closure_publication_failure_leaves_deny_marker(self):
        self.release();original=s.create_json
        def fail_after_link(path,value):
            original(path,value)
            if Path(path).name=='closure.json':raise OSError('injected directory fsync after link')
        with mock.patch.object(s,'create_json',side_effect=fail_after_link):
            with self.assertRaisesRegex(OSError,'after link'):self.dispatch()
        folder=self.out/'supervision/g1-C-4718'
        self.assertTrue((folder/'closure.json').exists());self.assertTrue((folder/'closure-pending.json').exists())
        self.assertTrue((folder/'stopped').exists())
        with self.assertRaisesRegex(ValueError,'publication UNKNOWN'):admission.activity_rows(self.out,protocol=self.p)
        with self.assertRaises(ValueError):self.dispatch()
    def test_slow_closure_publication_cannot_exceed_envelope_and_pass(self):
        self.p['candidate_accounting']['control_envelope_s']=.6
        freeze=self.out/'freeze/protocol.json';unsealed=dict(self.p);unsealed.pop('_sealed_sha256')
        fixtures.bound(freeze,unsealed);self.p['_sealed_sha256']=sha256(freeze)
        self.release();original=s.create_json
        def slow(path,value):
            original(path,value)
            if Path(path).name=='closure.json':time.sleep(.7)
        with mock.patch.object(s,'create_json',side_effect=slow):
            with self.assertRaisesRegex(ValueError,'after publication'):self.dispatch()
        self.assertTrue((self.out/'supervision/g1-C-4718/closure-pending.json').exists())
        with self.assertRaisesRegex(ValueError,'publication UNKNOWN'):admission.activity_rows(self.out,protocol=self.p)
    def test_slow_final_marker_unlink_denies_and_failed_marker_restore_revokes(self):
        for deny_failure in (False,True):
            with self.subTest(deny_restore_failure=deny_failure):
                if deny_failure:
                    self.tearDown();self.setUp()
                self.p['candidate_accounting']['control_envelope_s']=.6
                freeze=self.out/'freeze/protocol.json';unsealed=dict(self.p);unsealed.pop('_sealed_sha256')
                fixtures.bound(freeze,unsealed);self.p['_sealed_sha256']=sha256(freeze);self.release()
                original_unlink=Path.unlink;original_publish=s.create_json;pending_calls=0
                def slow_unlink(path,*a,**kw):
                    if path.name=='closure-pending.json':time.sleep(.7)
                    return original_unlink(path,*a,**kw)
                def deny_restore(path,value):
                    nonlocal pending_calls
                    if Path(path).name=='closure-pending.json':
                        pending_calls+=1
                        if deny_failure and pending_calls==2:raise OSError('injected denial restore publication failure')
                    return original_publish(path,value)
                with mock.patch.object(Path,'unlink',slow_unlink),mock.patch.object(s,'create_json',side_effect=deny_restore):
                    with self.assertRaisesRegex(ValueError,'after marker unlink'):self.dispatch()
                folder=self.out/'supervision/g1-C-4718'
                self.assertTrue((folder/'stopped').exists())
                with self.assertRaises((ValueError,FileNotFoundError)):admission.activity_rows(self.out,protocol=self.p)
                if deny_failure:self.assertFalse((folder/'closure.json').exists())
    def test_deleted_lifecycle_evidence_cannot_be_rehashed_as_complete(self):
        self.release();self.dispatch();folder=self.out/'supervision/g1-C-4718'
        life_path=folder/'lifecycle.json';life=json.loads(life_path.read_text());life['evidence_sha256']={}
        life_path.write_text(json.dumps(life));path=folder/'closure.json';closure=json.loads(path.read_text())
        closure['lifecycle_sha256']=sha256(life_path);path.write_text(json.dumps(closure))
        with self.assertRaisesRegex(ValueError,'incomplete lifecycle'):admission.activity_rows(self.out,protocol=self.p)
    def test_failed_closure_unlink_does_not_admit(self):
        self.release();original=Path.unlink
        def fail_pending(path,*a,**kw):
            if path.name=='closure-pending.json':raise PermissionError('injected marker unlink failure')
            return original(path,*a,**kw)
        with mock.patch.object(Path,'unlink',fail_pending):
            with self.assertRaisesRegex(PermissionError,'marker unlink'):self.dispatch()
        with self.assertRaisesRegex(ValueError,'publication UNKNOWN'):admission.activity_rows(self.out,protocol=self.p)
    def test_candidate_refused_by_real_backend_and_cli_before_external_call(self):
        self.release()
        with mock.patch.object(s.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'NOT_READY'):s.DockerBackend(dict(protocol=self.p))
            run.assert_not_called()
        with mock.patch.object(s.subprocess,'check_output') as call:
            with self.assertRaisesRegex(ValueError,'NOT_READY'):s.dispatch(self.p,'synthetic','g1','C',4718)
            call.assert_not_called()
        result=subprocess.run([sys.executable,'-B',str(FOREM/'scripts/task9_11/supervise.py'),'--protocol',str(self.out/'freeze/protocol.json'),'--phase','smoke-and-gates'],capture_output=True,text=True,timeout=5)
        self.assertNotEqual(result.returncode,0);self.assertIn('NOT_READY',result.stderr)
        self.assertFalse((self.out/'supervision').exists())
    def test_outermost_process_death_watcher_stops_exact_namespace(self):
        self.release(cap=3)
        process=subprocess.Popen([sys.executable,'-B',str(SELF),'--outer',str(self.out/'freeze/protocol.json')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        self.processes.append(process)
        folder=self.out/'supervision/g1-C-4718';self.until(folder/'worker-started.json')
        reservation=json.loads((folder/'reservation.json').read_text());self.assertEqual(reservation['outer']['pid'],process.pid)
        process.kill();process.wait(timeout=2)
        terminal=self.until(folder/'terminal.json');self.assertEqual(terminal['status'],'FAIL')
        self.assertTrue((folder/'stopped').exists());self.assertFalse((folder/'closure.json').exists())
        self.assertFalse(s.alive(json.loads((folder/'worker-started.json').read_text())['identity']))
    def test_no_forbidden_imports(self):
        self.assertFalse(set(sys.modules)&{'torch','numpy','pytest','task7_lower','task7_sim','task8_lower','task8_sim'})


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--worker':sys.exit(worker_fixture(sys.argv[2],sys.argv[3]))
    if len(sys.argv)==4 and sys.argv[1]=='--fixture':sys.exit(fixture(sys.argv[2],sys.argv[3]))
    if len(sys.argv)==3 and sys.argv[1]=='--outer':
        p=admission.load_protocol(sys.argv[2]);sys.exit(0 if s.dispatch(p,'synthetic','g1','C',4718,execution_adapter=Adapter(p,duration=10))=='passed' else 1)
    unittest.main(verbosity=2)
