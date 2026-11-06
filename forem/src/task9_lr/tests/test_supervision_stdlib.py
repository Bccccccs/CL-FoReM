"""Run directly with python3 -B; never collect conftest or the old suite.

Only stdlib, temporary files and bounded placeholder subprocesses. No Docker,
model, array, environment, simulator, replay, smoke or training invocation.
"""
import ast
import datetime as dt
import fcntl
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
from task9_lr import admission, gpu_costs
spec=importlib.util.spec_from_file_location('supervision_under_test',FOREM/'scripts/task9_11/supervise.py')
supervision=importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervision)
SELF=Path(__file__).resolve()


class PlaceholderBackend:
    """A temp-directory namespace; exact identities only, no Docker calls."""
    def __init__(self,value):self.value=value;self.root=Path(value['supervision_dir'])
    @property
    def terminal_budget_s(self):return .05+self.value.get('slow_quiet_s',0)+self.value.get('slow_stop_s',0)
    def resources(self):
        event=self.value.get('resource_event')
        if event and not (self.root/'resource-event-fired').exists():
            (self.root/'resource-event-fired').touch()
            if event=='watcher-killed':
                identity=json.loads((self.root/'watcher-ready.json').read_text())['identity'];os.kill(identity['pid'],signal.SIGKILL)
            elif event=='terminal':
                supervision.create_json(self.root/'terminal.json',dict(status='FAIL',injected=True))
            elif event=='time':time.sleep(self.value['cap_s'])
            elif event=='owner-exit':os.kill(self.value['owner']['pid'],signal.SIGKILL)
        if (self.root/'resource-failure').exists():raise ValueError('injected resource failure')
    def quiet(self):
        if self.value.get('slow_quiet_s'):time.sleep(self.value['slow_quiet_s'])
        residual=self.root/'residual-child.json'
        if residual.exists() and supervision.alive(json.loads(residual.read_text())['identity']):raise RuntimeError('client exited; worker still active')
        if (self.root/'residual-worker').exists():raise RuntimeError('client exited; worker still active')
        return dict(worker_absent=True,synthetic=True)
    def stop(self):
        if self.value.get('slow_stop_s'):time.sleep(self.value['slow_stop_s'])
        (self.root/'stopped').touch()
        path=self.root/'worker-started.json'
        if path.exists():
            identity=json.loads(path.read_text())['identity']
            if supervision.alive(identity):
                try:os.killpg(identity['pid'],signal.SIGKILL)
                except ProcessLookupError:pass
        residual=self.root/'residual-child.json'
        if residual.exists():
            identity=json.loads(residual.read_text())['identity']
            if supervision.alive(identity):
                try:os.killpg(identity['pid'],signal.SIGKILL)
                except ProcessLookupError:pass
        return dict(container_stopped=True,synthetic=True)


def fixture(mode,path):
    path=Path(path)
    if mode=='owner':
        value=json.loads(path.read_text())
        lock=open(Path(value['supervision_dir'])/'namespace.lock','a')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if value.get('owner_exit_after') is not None:
            # Existing owner/worker race fixture, separate bounded signal process.
            subprocess.Popen([sys.executable,'-B','-c',
                'import os,signal,time; time.sleep('+repr(value['owner_exit_after'])+'); os.kill('+str(os.getpid())+',signal.SIGKILL)'])
        command=[sys.executable,'-B',str(SELF),'--fixture','guard',str(Path(value['supervision_dir'])/'owned-spec.json')]
        return supervision.owner(path,lock.fileno(),guard_command=command)
    if mode=='guard':
        value=json.loads(path.read_text())
        command=[sys.executable,'-B',str(SELF),'--fixture','watch',str(Path(value['supervision_dir'])/'watch-spec.json')]
        return supervision.guard(path,int(os.environ['TASK9_LR_LOCK_FD']),backend_factory=PlaceholderBackend,watch_command=command)
    value=json.loads(path.read_text())
    if value.get('write_failure'):
        def failed(*a,**k):raise OSError('injected terminal publication failure')
        supervision.dump=failed
    return supervision.watch(value,PlaceholderBackend(value))


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.root=Path(self.temporary.name);self.children=[]
    def tearDown(self):
        for process in self.children:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
        # Explicitly clean every placeholder by exact PID/start identity. These
        # tests never inspect or signal any process outside their temp specs.
        for path in self.root.rglob('*-ready.json'):
            identity=json.loads(path.read_text())['identity']
            if identity['pid']!=os.getpid() and supervision.alive(identity):
                try:os.kill(identity['pid'],signal.SIGKILL)
                except ProcessLookupError:pass
        for path in list(self.root.rglob('worker-started.json'))+list(self.root.rglob('residual-child.json')):
            identity=json.loads(path.read_text())['identity']
            if supervision.alive(identity):
                try:os.killpg(identity['pid'],signal.SIGKILL)
                except ProcessLookupError:pass
        self.temporary.cleanup()
    def until(self,path,timeout=5):
        deadline=time.monotonic()+timeout
        while not path.exists():
            if time.monotonic()>deadline:self.fail('bounded fixture timeout: '+str(path))
            time.sleep(.01)
        return json.loads(path.read_text()) if path.suffix=='.json' else path
    def start(self,*,duration=.15,cap=2,**extras):
        root=self.root/str(len(self.children));root.mkdir();record_path=root/'activity.json'
        record=dict(phase='g1',arm='C',seed=4718,status='reserved')
        supervision.create_json(record_path,record)
        command=[sys.executable,'-B','-c',f'import time,pathlib; pathlib.Path({str(root/"worker-launched")!r}).touch(); time.sleep({duration}); print("placeholder")']
        if extras.get('residual_child'):
            code="import subprocess,sys,pathlib,json; p=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(3)'],start_new_session=True); fields=pathlib.Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split(); pathlib.Path("+repr(str(root/'residual-child.json'))+").write_text(json.dumps({'identity':{'pid':p.pid,'start_ticks':fields[19]}}))"
            command=[sys.executable,'-B','-c',code]
        value=dict(supervision_dir=str(root),activity='g1-C-4718',reservation_id='temp-only',record=record,
            record_path=str(record_path),started_monotonic=time.monotonic(),command=command,
            cap_s=cap,save_reserve_s=.2,force_stop_tail_s=.15,deadline_epoch=time.time()+cap+1,poll_s=.02,
            stop_path=str(root/'STOP'),log_path=str(root/'placeholder.txt'),**extras)
        path=root/'spec.json';supervision.create_json(path,value)
        stream=(root/'fixture-output.txt').open('w')
        process=subprocess.Popen([sys.executable,'-B',str(SELF),'--fixture','owner',str(path)],stdout=stream,stderr=subprocess.STDOUT)
        stream.close();self.children.append(process)
        self.until(root/'watcher-ready.json');return root,process
    def terminal(self,root):return self.until(root/'terminal.json')
    def test_child_first_persists_actual_exit_and_wall(self):
        root,parent=self.start();value=self.terminal(root)
        self.assertEqual(value['status'],'PASS');parent.wait(timeout=5)
        row=json.loads((root/'activity.json').read_text())
        self.assertEqual(row['exit_code'],0);self.assertGreater(row['wall_s'],0)
        self.assertEqual(value['record_sha256'],supervision.sha256(root/'activity.json'))
    def test_parent_sigterm_survives_outside_terminal(self):
        root,parent=self.start(duration=3);self.until(root/'worker-started.json');parent.terminate();parent.wait(timeout=5)
        self.assertEqual(self.terminal(root)['status'],'FAIL');self.assertTrue((root/'stopped').exists())
    def test_parent_sigkill_survives_outside_terminal(self):
        root,parent=self.start(duration=3);self.until(root/'worker-started.json');parent.kill();parent.wait(timeout=5)
        self.assertEqual(self.terminal(root)['status'],'FAIL');self.assertTrue((root/'stopped').exists())
    def test_guard_sigkill_has_independent_watchdog(self):
        root,parent=self.start(duration=3);self.until(root/'worker-started.json')
        identity=json.loads((root/'guardian-ready.json').read_text())['identity'];os.kill(identity['pid'],signal.SIGKILL)
        self.assertEqual(self.terminal(root)['status'],'FAIL');self.assertTrue((root/'stopped').exists())
    def test_parent_child_completion_race_has_terminal(self):
        root,parent=self.start(duration=.04,owner_exit_after=.12)
        value=self.terminal(root);self.assertIn(value['status'],('PASS','FAIL'))
        if value['status']=='PASS':self.assertTrue(value['owner_alive'])
        else:self.assertTrue((root/'stopped').exists())
    def test_both_guards_killed_preserves_unknown_and_lock_reject(self):
        root,parent=self.start(duration=3);self.until(root/'worker-started.json')
        for role in ('guardian','watcher'):
            identity=json.loads((root/(role+'-ready.json')).read_text())['identity'];os.kill(identity['pid'],signal.SIGKILL)
        parent.wait(timeout=5);self.assertFalse((root/'terminal.json').exists())
        self.assertEqual(json.loads((root/'activity.json').read_text())['status'],'reserved')
    def test_deadline_force_stop_is_bounded(self):
        root,parent=self.start(duration=3,cap=.5);value=self.terminal(root)
        self.assertEqual(value['status'],'FAIL');self.assertTrue((root/'STOP').exists());self.assertTrue((root/'stopped').exists())
    def test_slow_stop_uses_original_cap_tail(self):
        root,parent=self.start(duration=3,cap=.8,slow_stop_s=.08)
        value=self.terminal(root);self.assertEqual(value['status'],'FAIL')
        row=json.loads((root/'activity.json').read_text())
        self.assertLess(row['wall_s'],.8)
    def test_slow_quiet_failure_and_stop_chain_inside_cap(self):
        root=self.root/'tail-chain';root.mkdir();record_path=root/'activity.json'
        record=dict(phase='g1',arm='C',seed=4718,status='reserved')
        record_path.write_text(json.dumps(record));(root/'residual-worker').touch()
        (root/'worker-result.json').write_text('{"exit_code":0}')
        value=dict(supervision_dir=str(root),activity='g1-C-4718',reservation_id='nonce',record=record,
            record_path=str(record_path),owner=supervision.process_identity(),guardian=supervision.process_identity(),
            started_monotonic=time.monotonic()-.59,cap_s=.8,force_stop_tail_s=.2,save_reserve_s=.25,
            deadline_epoch=time.time()+2,poll_s=.01,stop_path=str(root/'STOP'),slow_quiet_s=.07,slow_stop_s=.07)
        self.assertEqual(supervision.watch(value,PlaceholderBackend(value)),1)
        self.assertLess(json.loads(record_path.read_text())['wall_s'],.8)
    def test_write_failure_stops_and_never_publishes_pass(self):
        root,parent=self.start(write_failure=True);parent.wait(timeout=5)
        self.assertTrue((root/'stopped').exists());self.assertFalse((root/'terminal.json').exists())
        self.assertEqual(json.loads((root/'activity.json').read_text())['status'],'reserved')
    def test_exec_client_exit_does_not_prove_worker_absent(self):
        root,parent=self.start(residual_child=True)
        identity=self.until(root/'residual-child.json')['identity']
        self.assertEqual(self.terminal(root)['status'],'FAIL');self.assertTrue((root/'stopped').exists())
        deadline=time.monotonic()+2
        while supervision.alive(identity) and time.monotonic()<deadline:time.sleep(.01)
        self.assertFalse(supervision.alive(identity))
    def test_independent_lock_prevents_concurrent_phase(self):
        root,parent=self.start(duration=.5)
        with (root/'namespace.lock').open('a') as stream:
            with self.assertRaises(BlockingIOError):fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.terminal(root)
    def test_resource_failure_fail_closed(self):
        root,parent=self.start(duration=3);(root/'resource-failure').touch()
        self.assertEqual(self.terminal(root)['status'],'FAIL');self.assertTrue((root/'stopped').exists())
    def test_initial_write_failure_does_not_launch(self):
        with mock.patch.object(supervision,'create_json',side_effect=OSError('disk full')),mock.patch.object(supervision.subprocess,'Popen') as launch:
            path=self.root/'spec.json';path.write_text(json.dumps(dict(supervision_dir=str(self.root),reservation_id='test')))
            with self.assertRaises(OSError):supervision.guard(path,0)
            launch.assert_not_called()

    def test_resource_watch_kill_never_launches_worker(self):
        root,parent=self.start(resource_event='watcher-killed');parent.wait(timeout=5)
        self.assertTrue((root/'resource-event-fired').exists());self.assertFalse((root/'worker-started.json').exists());self.assertFalse((root/'worker-launched').exists())
    def test_resource_terminal_never_launches_worker(self):
        root,parent=self.start(resource_event='terminal');parent.wait(timeout=5)
        self.assertTrue((root/'resource-event-fired').exists());self.assertFalse((root/'worker-started.json').exists());self.assertFalse((root/'worker-launched').exists())
    def test_resource_deadline_never_launches_worker(self):
        root,parent=self.start(resource_event='time',cap=.6);parent.wait(timeout=5)
        self.assertTrue((root/'resource-event-fired').exists());self.assertFalse((root/'worker-started.json').exists());self.assertFalse((root/'worker-launched').exists())
    def test_resource_owner_exit_never_launches_worker(self):
        root,parent=self.start(resource_event='owner-exit');parent.wait(timeout=5)
        self.terminal(root)
        self.assertTrue((root/'resource-event-fired').exists());self.assertFalse((root/'worker-started.json').exists());self.assertFalse((root/'worker-launched').exists())
    def test_outer_witnesses_actual_wait_chain_but_tail_unknown(self):
        root,parent=self.start()
        value=json.loads((root/'spec.json').read_text())
        lifecycle=supervision.outer_wait(value,parent,backend_factory=PlaceholderBackend)
        self.assertEqual(lifecycle['chain_status'],'PASS')
        self.assertEqual(set(lifecycle['waits']),{'guardian','watcher'})
        self.assertEqual(lifecycle['owner']['exit_code'],0)
        self.assertEqual(lifecycle['closed_wall_s'],'UNKNOWN')
        self.assertEqual(lifecycle['accounting_status'],'UNKNOWN')
        row=json.loads((root/'activity.json').read_text())
        self.assertGreater(lifecycle['observed_chain_wall_s'],row['stage_terminal_wall_s'])
    def test_outer_owner_sigkill_preserves_missing_wait_unknown(self):
        root,parent=self.start(duration=3);self.until(root/'worker-started.json');parent.kill()
        value=json.loads((root/'spec.json').read_text())
        lifecycle=supervision.outer_wait(value,parent,backend_factory=PlaceholderBackend)
        self.assertEqual(lifecycle['owner']['exit_code'],-signal.SIGKILL)
        self.assertEqual(lifecycle['chain_status'],'UNKNOWN');self.assertEqual(lifecycle['accounting_status'],'UNKNOWN')
        self.assertTrue(lifecycle['errors'])

    def test_outer_wait_receipt_tamper_never_certifies_chain(self):
        root,parent=self.start();self.until(root/'guardian-wait.json')
        path=root/'watcher-wait.json';record=json.loads(path.read_text());record['reservation_id']='wrong'
        path.write_text(json.dumps(record))
        value=json.loads((root/'spec.json').read_text())
        lifecycle=supervision.outer_wait(value,parent,backend_factory=PlaceholderBackend)
        self.assertEqual(lifecycle['chain_status'],'UNKNOWN');self.assertEqual(lifecycle['closed_wall_s'],'UNKNOWN')
    def test_outer_terminal_publisher_tamper_never_certifies_chain(self):
        root,parent=self.start();self.until(root/'guardian-wait.json')
        path=root/'terminal.json';record=json.loads(path.read_text());record['watcher']=supervision.process_identity()
        path.write_text(json.dumps(record))
        value=json.loads((root/'spec.json').read_text())
        lifecycle=supervision.outer_wait(value,parent,backend_factory=PlaceholderBackend)
        self.assertEqual(lifecycle['chain_status'],'UNKNOWN')
        self.assertTrue(any('publisher identity mismatch' in error for error in lifecycle['errors']))
    def test_outer_publication_failure_never_creates_closed_receipt(self):
        root,parent=self.start();self.until(root/'guardian-wait.json')
        value=json.loads((root/'spec.json').read_text())
        with mock.patch.object(supervision,'create_json',side_effect=OSError('injected outer fsync error')) as publish:
            with self.assertRaisesRegex(OSError,'injected outer fsync error'):supervision.outer_wait(value,parent,backend_factory=PlaceholderBackend)
            publish.assert_called_once()
        self.assertFalse((root/'lifecycle.json').exists())


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'activities').mkdir();(self.root/'logs').mkdir()
        clock=dt.datetime.now(dt.timezone.utc)
        self.p=dict(deadline=(clock+dt.timedelta(hours=1)).isoformat(),started_at=(clock-dt.timedelta(seconds=10)).isoformat(),
            save_allowance_s=1,max_worker_seconds=100,max_gpu_seconds=100,max_wall_seconds=3600,max_evaluation_episodes=10,
            max_output_bytes=100*1024**3,max_diagnostic_log_bytes=1024**2,new_output_root=str(self.root),new_log_root=str(self.root/'logs'),
            container_output='/output',container_logs='/runlogs',synthetic_fixture=True,preferred_gpu_uuid='synthetic-GPU0')
        (self.root/'container-inspect.json').write_text(json.dumps(dict(Id='exact',HostConfig=dict(DeviceRequests=[]))))
    def tearDown(self):self.tmp.cleanup()
    def row(self,name='g1-C-4718',**changes):
        value=dict(phase='g1',arm='C',seed=4718,status='PASS',exit_code=0,wall_s=3,started_epoch=time.time()-3);value.update(changes)
        if value.get('supervision_format')=='task9-lr-supervision-v2':
            directory=self.root/'supervision'/name;directory.mkdir(parents=True,exist_ok=True)
            path=directory/'reservation.json'
            if not path.exists():path.write_text(json.dumps(dict(activity=name,reservation_id=value.get('reservation_id','nonce'),cap_s=value.get('cap_s'))))
            value.setdefault('reservation_id','nonce');value.setdefault('reservation_sha256',supervision.sha256(path))
        (self.root/'activities'/(name+'.json')).write_text(json.dumps(value));return value
    def test_legacy_started_with_zero_wall_blocks_every_phase(self):
        self.row(status='started',wall_s=0)
        for stage in ('profile','remaining','final-test'):
            with self.assertRaisesRegex(ValueError,'unfinished'):admission.prerequisites(self.root,stage,'C',4718)
        with self.assertRaisesRegex(ValueError,'unfinished'):admission.check_resources(self.p,self.root)
    def test_duplicate_and_misnamed_activities_rejected(self):
        row=self.row();self.row('different',**row)
        with self.assertRaises(ValueError):admission.activity_rows(self.root)
    def test_duplicate_dispatch_does_not_rebill_or_launch(self):
        self.row();self.p['new_log_root']=str(self.root/'logs')
        with mock.patch.object(supervision.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(ValueError,'lifecycle accounting UNKNOWN'):supervision.dispatch(self.p,'never-docker','g1','C',4718)
            launch.assert_not_called()
        with self.assertRaisesRegex(ValueError,'lifecycle accounting UNKNOWN'):admission.check_resources(self.p,self.root)
    def test_legacy_pass_without_closure_cannot_skip_or_bill_as_closed(self):
        for format_name in (None,'task9-lr-supervision-v1','unapproved-closed-format'):
            with self.subTest(format=format_name):
                row=self.row()
                if format_name is not None:
                    row['supervision_format']=format_name
                    (self.root/'activities/g1-C-4718.json').write_text(json.dumps(row))
                with self.assertRaisesRegex(ValueError,'lifecycle accounting UNKNOWN'):admission.activity_rows(self.root)
                with self.assertRaisesRegex(ValueError,'lifecycle accounting UNKNOWN'):admission.check_resources(self.p,self.root)
                with mock.patch.object(supervision.subprocess,'Popen') as launch:
                    with self.assertRaisesRegex(ValueError,'lifecycle accounting UNKNOWN'):supervision.dispatch(self.p,'never-docker','g1','C',4718)
                    launch.assert_not_called()
    def test_stage_receipt_cannot_skip_or_bill_as_closed(self):
        row=self.row(supervision_format='task9-lr-supervision-v2',code_hash='test',protocol_sha256='sealed')
        directory=self.root/'supervision/g1-C-4718';directory.mkdir(parents=True,exist_ok=True)
        (self.root/'releases').mkdir();release=self.root/'releases/g1-C-4718.json';release.write_text('{}')
        row['release_sha256']=supervision.sha256(release);self.row(**row)
        (directory/'terminal.json').write_text(json.dumps(dict(status='PASS',activity='g1-C-4718',owner_alive=True,guardian_alive=True,record_sha256=supervision.sha256(self.root/'activities/g1-C-4718.json'))))
        self.p['_sealed_sha256']='sealed'
        with mock.patch.object(supervision,'artifact_digest',return_value='test'),mock.patch.object(supervision.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(ValueError,'lifecycle accounting UNKNOWN'):supervision.dispatch(self.p,'never-docker','g1','C',4718)
            launch.assert_not_called()
        with self.assertRaisesRegex(ValueError,'lifecycle accounting UNKNOWN'):admission.check_resources(self.p,self.root)
    def test_exact_container_identity_mismatch_refuses_kill(self):
        value=dict(Id='unexpected',Image='image',Mounts=[],Config=dict(User='1:1'),HostConfig=dict(DeviceRequests=[]))
        backend=supervision.DockerBackend(dict(container_id='full-exact-id',container_identity={}))
        result=subprocess.CompletedProcess([],0,stdout=json.dumps([value]),stderr='')
        with mock.patch.object(supervision.subprocess,'run',return_value=result) as run:
            with self.assertRaisesRegex(RuntimeError,'identity changed'):backend.stop()
            self.assertEqual(run.call_count,1)
            self.assertIn('full-exact-id',str(run.call_args))
    def test_completed_identity_change_refuses_skip(self):
        row=self.row(supervision_format='task9-lr-supervision-v2',code_hash='old',protocol_sha256='sealed')
        directory=self.root/'supervision/g1-C-4718';directory.mkdir(parents=True,exist_ok=True)
        (self.root/'releases').mkdir();release=self.root/'releases/g1-C-4718.json';release.write_text('{}')
        row['release_sha256']=supervision.sha256(release);self.row(**row)
        (directory/'terminal.json').write_text(json.dumps(dict(status='PASS',activity='g1-C-4718',owner_alive=True,guardian_alive=True,record_sha256=supervision.sha256(self.root/'activities/g1-C-4718.json'))))
        self.p['_sealed_sha256']='sealed'
        with mock.patch.object(supervision,'artifact_digest',return_value='new'),mock.patch.object(supervision.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(ValueError,'lifecycle accounting UNKNOWN'):supervision.dispatch(self.p,'never-docker','g1','C',4718)
            launch.assert_not_called()
    def test_valid_active_reservation_charged_once(self):
        name='g1-C-4718';directory=self.root/'supervision'/name;directory.mkdir(parents=True,exist_ok=True)
        reservation=dict(activity=name,reservation_id='nonce',cap_s=20)
        path=directory/'reservation.json';path.write_text(json.dumps(reservation))
        for role in ('guardian','watcher'):(directory/(role+'-ready.json')).write_text(json.dumps(dict(reservation_id='nonce',identity=supervision.process_identity())))
        self.row(status='reserved',wall_s=0,cap_s=20,supervision_format='task9-lr-supervision-v2',reservation_id='nonce',reservation_sha256=supervision.sha256(path))
        value=admission.check_resources(self.p,self.root,active_name=name,new_worker_seconds=20)
        self.assertAlmostEqual(value['worker_seconds']+value['reserved_worker_seconds'],20,places=4)
        with self.assertRaisesRegex(ValueError,'cap mismatch'):admission.check_resources(self.p,self.root,active_name=name,new_worker_seconds=21)
    def test_unknown_nonfinite_and_failed_costs_rejected(self):
        for value in (None,-1,float('nan'),float('inf'),True):
            self.row(wall_s=value)
            with self.assertRaises(ValueError):admission.check_resources(self.p,self.root)
        self.row(status='FAIL')
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.root)
    def test_external_host_mapping_and_no_duplicate_charge(self):
        self.p['execution_allowed']=False
        external=self.root/'external';external.mkdir();(external/'a-command.json').write_text(json.dumps(dict(wall_s=7,started_epoch=time.time()-7,finished_epoch=(end:=time.time()),synthetic_fixture=True,gpu_evidence=gpu_costs.fixture_evidence(self.p,end-7,end,[]))))
        self.p['external_activity_roots']=['/workspace/external','/workspace/external']
        with mock.patch.object(admission,'ASSET_ROOT',self.root):
            self.assertEqual(admission.check_resources(self.p,self.root)['worker_seconds'],7)
        (external/'a-command.json').write_text('{}')
        with mock.patch.object(admission,'ASSET_ROOT',self.root),self.assertRaisesRegex(ValueError,'external wall'):
            admission.check_resources(self.p,self.root)
    def test_host_container_path_layout(self):
        self.assertEqual(admission.host_path('/workspace/doc/a',self.p,self.root),admission.ASSET_ROOT/'doc/a')
        self.assertEqual(admission.host_path(str(self.root/'logs/x'),self.p,'/output'),Path('/runlogs/x'))
        self.assertEqual(admission.host_path(str(self.root/'x'),self.p,'/output'),Path('/output/x'))
        self.assertEqual(admission.host_path('/runlogs/x',self.p,self.root),self.root/'logs/x')
    def test_stopped_container_exposure_uses_verified_finish(self):
        start=time.time()-20;(self.root/'container.json').write_text(json.dumps(dict(name='only-own',container_id='exact',started_epoch=start)))
        (self.root/'container-inspect.json').write_text(json.dumps(dict(Id='exact',HostConfig=dict(DeviceRequests=[dict(DeviceIDs=['synthetic-GPU0'])]))))
        state=dict(Id='exact',Name='/only-own',State=dict(Running=False,FinishedAt=dt.datetime.fromtimestamp(start+5,dt.timezone.utc).isoformat()))
        # This legacy API has no immutable temporal anchor; it cannot certify
        # even an apparently stopped5s window. Dynamic positive coverage lives
        # in test_gpu_accounting_stdlib with independent snapshot history.
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):admission.check_resources(self.p,self.root,container_state=state)
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):admission.check_resources(self.p,self.root)
    def test_active_reservation_requires_receipt_identity(self):
        self.row(status='reserved',wall_s=0,cap_s=20,supervision_format='task9-lr-supervision-v2')
        with self.assertRaises((ValueError,FileNotFoundError)):admission.check_resources(self.p,self.root,active_name='g1-C-4718')
    def test_terminal_pass_requires_matching_independent_receipt(self):
        self.row(supervision_format='task9-lr-supervision-v2')
        with self.assertRaises(FileNotFoundError):admission.activity_rows(self.root)
    def test_global_worker_wall_episode_and_diagnostic_limits(self):
        with self.assertRaisesRegex(ValueError,'worker cap'):admission.check_resources(self.p,self.root,new_worker_seconds=101)
        (self.root/'episodes-started.jsonl').write_text('{"count":11}\n')
        with self.assertRaisesRegex(ValueError,'episode cap'):admission.check_resources(self.p,self.root)
        (self.root/'episodes-started.jsonl').unlink();folder=self.root/'diagnostics';folder.mkdir();(folder/'snapshot.pt').write_bytes(b'x'*32)
        self.p['max_diagnostic_log_bytes']=1
        with self.assertRaisesRegex(ValueError,'diagnostic'):admission.check_resources(self.p,self.root)
    def test_unknown_historical_cost_is_blocker(self):
        self.p['unknown_resource_costs']=['historical ON host terminal']
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):admission.check_resources(self.p,self.root)
    def test_no_forbidden_runtime_imports(self):
        forbidden={'torch','numpy','pytest','task7_sim','task8_sim','task7_lower','task8_lower'}
        self.assertFalse(forbidden & {name.split('.')[0] for name in sys.modules})


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--fixture':sys.exit(fixture(sys.argv[2],sys.argv[3]))
    unittest.main(verbosity=2)
