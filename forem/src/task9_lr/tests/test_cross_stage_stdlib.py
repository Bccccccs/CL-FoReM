"""Production cross-stage clock + additional reviewed cost integration; stdlib only."""
import copy
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import threading
import unittest
from unittest import mock

FOREM=Path(__file__).resolve().parents[3];sys.path.insert(0,str(FOREM/'src'))
from task9_lr import admission, continuation as c, clock, costs, cost_control, gpu_costs
from task9_lr.runtime import sha256,artifact_digest

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

life=module('cross_lifecycle',Path(__file__).with_name('test_lifecycle_candidate_stdlib.py'))
f=life.fixtures;s=life.s


def fixture(base, *, envelope=30.):
    # Old fixture prepares metadata only; the opted-in protocol is frozen before
    # any release/reservation. It does not migrate an existing stage.
    p=f.make_fixture(base);out=Path(p['new_output_root'])
    import shutil
    shutil.rmtree(out/'freeze')
    p.pop('_sealed_sha256')
    anchor=clock.initialize(Path(p['continuation']['host_workspace'])/'fixture-clock',dt.datetime.fromisoformat('2026-11-04T00:00:00+08:00').timestamp())
    p['candidate_accounting']['control_envelope_s']=envelope
    p['fixture_clock']=dict(root=str(Path(anchor['path']).parent),anchor=anchor)
    p['dynamic_cost_policy']=costs.make_policy(p)
    source=Path(base)/'forem/doc/agent_logs/task9/task9.11/dynamic-protocol.json';f.bound(source,p)
    f.prepare.freeze_candidate_protocol(source,out/'freeze');p=admission.load_protocol(out/'freeze/protocol.json')
    (out/'activities').mkdir();(out/'releases').mkdir()
    state=dict(Id='synthetic-exact-container',Name='/synthetic',Image='synthetic',Mounts=[],Config=dict(User='synthetic'),HostConfig=dict(DeviceRequests=[]),State=dict(Running=True))
    f.bound(out/'container-inspect.json',state)
    costs.review(p,reviewer=p['dynamic_cost_policy']['reviewer'],expires_at='2026-11-04T00:10:00+08:00')
    return p


def release(p,stage='g1',arm='C',seed=4718,seconds=2400):
    token=f.fixture_release(p,stage,arm,seed)
    token.update(max_worker_seconds=4.,save_reserve_s=.3,
        expires_at=dt.datetime.fromtimestamp(clock.epoch(p)+seconds,dt.timezone.utc).isoformat(),
        budget_snapshot=costs.current_ref(p))
    return f.bound(Path(p['new_output_root'])/'releases'/f'{stage}-{arm}-{seed}.json',token)


def command(p,name='additional-review',wall=.01,parent=None,stage='review'):
    root=Path(p['external_activity_roots'][0]);end=clock.epoch(p)
    return costs.publish_source(p,name,dict(format='task9-lr-measured-command-v1',
        status='CLOSED',argv=[sys.executable,'-B','-c','pass'],exit_code=0,wall_s=wall,
        gpu_evidence=gpu_costs.fixture_evidence(p,end-wall,end,[]),
        started_epoch=end-wall,finished_epoch=end,synthetic_fixture=True,execution_allowed=False,
        stage=stage,parent_event_id=parent,
        started_clock=dict(clock.capture(p),epoch=end-wall,monotonic=end-wall-clock.capture(p)['offset']),
        completed_clock=dict(clock.capture(p),epoch=end,monotonic=end-clock.capture(p)['offset'])),writer=p['dynamic_cost_policy']['event_writer'])


def append(p,name='additional-review',wall=.01,parent=None,stage='review'):
    source=command(p,name,wall,parent,stage)
    return costs.append_event(p,name,stage,source,parent_event_id=parent,writer=p['dynamic_cost_policy']['event_writer'])


class RaceBackend(life.Backend):
    def resources(self):
        super().resources()
        marker=self.root/'race-added-cost'
        if marker.exists():return
        marker.touch();p=self.value['protocol']
        source=costs.measured_command(p,'late-cost','review',[sys.executable,'-B','-c','pass'],writer=p['dynamic_cost_policy']['event_writer'],gpu_devices=[])
        costs.append_event(p,'late-cost','review',source,writer=p['dynamic_cost_policy']['event_writer'])


class RaceAdapter(life.Adapter):
    backend_factory=RaceBackend
    def owner_command(self,path):return [sys.executable,'-B',str(Path(__file__).resolve()),'--race','owner',str(path)]


def race_fixture(role,path):
    value=json.loads(Path(path).read_text());folder=Path(value['supervision_dir']);self=Path(__file__).resolve()
    if role=='owner':
        os.environ.update(TASK9_LR_ACTIVITY=value['activity'],TASK9_LR_RESERVATION=value['reservation_id'],TASK9_LR_LOG_PATH=value['log_path'])
        return s.owner(path,int(os.environ['TASK9_LR_LOCK_FD']),guard_command=[sys.executable,'-B',str(self),'--race','guard',str(folder/'owned-spec.json')])
    command=[sys.executable,'-B',str(life.SELF),'--fixture','watch',str(folder/'watch-spec.json')]
    return s.guard(path,int(os.environ['TASK9_LR_LOCK_FD']),backend_factory=RaceBackend,watch_command=command)


class CrossStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='t9-cross-');self.p=fixture(self.tmp.name);self.out=Path(self.p['new_output_root'])
    def tearDown(self):self.tmp.cleanup()
    def dispatch(self,stage='g1',arm='C',seed=4718,duration=.08):
        return s.dispatch(self.p,'synthetic',stage,arm,seed,execution_adapter=life.Adapter(self.p,duration=duration))
    def review(self):return costs.review(self.p,reviewer=self.p['dynamic_cost_policy']['reviewer'],expires_at='2026-11-05T00:00:00+08:00')
    def test_joint_production_cross_time_added_review_cost_next_stage_and_immutable_history(self):
        first=release(self.p);self.assertEqual(self.dispatch(),'passed')
        closure=self.out/'supervision/g1-C-4718/closure.json';protocol=self.out/'freeze/protocol.json'
        hashes={str(p):sha256(p) for p in (protocol,Path(first['path']),closure)}
        before=admission.check_resources(self.p,self.out)
        clock.advance(self.p,3600) # old stage release AND original snapshot expire
        rows=admission.activity_rows(self.out,protocol=self.p);self.assertEqual(len(rows),1)
        # Natural expiry never revokes closed evidence; current budget must be renewed.
        self.assertEqual(self.dispatch(),'already_passed')
        script="import json,sys; sys.path.insert(0,"+repr(str(FOREM/'src'))+"); from task9_lr import admission; p=admission.load_protocol(sys.argv[1]); assert len(admission.activity_rows(p['new_output_root'],protocol=p))==1; print('independent historical review PASS')"
        source=costs.measured_command(self.p,'additional-review','review',[sys.executable,'-B','-c',script,str(protocol)],writer=self.p['dynamic_cost_policy']['event_writer'],gpu_devices=[])
        measured=json.loads(Path(source['path']).read_text());extra=measured['wall_s'];self.assertGreater(extra,0);self.assertEqual(measured['exit_code'],0)
        appendref=costs.append_event(self.p,'additional-review','review',source,writer=self.p['dynamic_cost_policy']['event_writer'])
        with self.assertRaisesRegex(ValueError,'stale|expired'):admission.check_resources(self.p,self.out)
        snap=self.review();release(self.p,'gate-evaluate','L')
        self.assertEqual(self.dispatch('gate-evaluate','L'),'passed')
        after=admission.check_resources(self.p,self.out);rows=admission.activity_rows(self.out,protocol=self.p)
        self.assertAlmostEqual(after['worker_seconds'],before['worker_seconds']+extra+90.+rows[1]['wall_s'])
        adapter=life.Adapter(self.p);self.assertEqual(s.dispatch(self.p,'synthetic','g1','C',4718,execution_adapter=adapter),'already_passed');self.assertEqual(adapter.calls,0)
        self.assertEqual(admission.check_resources(self.p,self.out)['worker_seconds'],after['worker_seconds'])
        self.assertEqual(hashes,{p:sha256(p) for p in hashes})
        for stage in ('g1-C-4718','gate-evaluate-L-4718'):
            self.assertTrue((self.out/'supervision'/stage/'production-worker-admission-completed').exists())
            self.assertEqual(json.loads((self.out/'ledger'/(stage+'.json')).read_text())['status'],'PASS')
        print(json.dumps(dict(joint='PASS',protocol_sha256=hashes[str(protocol)],old_release=first,old_closure_sha256=hashes[str(closure)],event=appendref,new_snapshot=snap,charged_added_payload_cost=extra,charged_added_metadata_control=90.,old_and_new_closed=2)),flush=True)
    def test_expired_unstarted_and_caller_clock_rejected(self):
        ref=release(self.p);clock.advance(self.p,2401)
        with self.assertRaises(ValueError):self.dispatch()
        with self.assertRaisesRegex(ValueError,'caller clock'):admission.read_release(ref['path'],'g1',self.p,arm='C',seed=4718,clock=dt.datetime.fromisoformat('2026-11-04T00:00:00+08:00'))
        self.assertFalse((self.out/'supervision').exists())
    def test_closure_fields_cannot_forge_completion_time(self):
        release(self.p);self.dispatch();path=self.out/'supervision/g1-C-4718/lifecycle.json';value=json.loads(path.read_text())
        value['completion_clock']['epoch']-=100;f.bound(path,value)
        closure=self.out/'supervision/g1-C-4718/closure.json';cl=json.loads(closure.read_text());cl['lifecycle_sha256']=sha256(path);f.bound(closure,cl)
        with self.assertRaises(ValueError):admission.activity_rows(self.out,protocol=self.p)
    def test_explicit_revocation_differs_from_natural_expiry(self):
        ref=release(self.p);self.dispatch();clock.advance(self.p,2401)
        self.review();before=admission.check_resources(self.p,self.out)['worker_seconds']
        costs.revoke(self.p,ref,reviewer=self.p['reviewer'],reason='explicit independent revoke')
        with self.assertRaisesRegex(ValueError,'explicitly revoked'):admission.activity_rows(self.out,protocol=self.p)
        self.assertEqual(admission.check_resources(self.p,self.out)['worker_seconds'],before)
    def test_extra_command_unreviewed_event_and_stale_release_block(self):
        ref=release(self.p);source=command(self.p)
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
        costs.append_event(self.p,'additional-review','review',source,writer=self.p['dynamic_cost_policy']['event_writer'])
        with self.assertRaises(ValueError):self.dispatch()
        self.review()
        with self.assertRaises(ValueError):self.dispatch() # release remains bound to old snapshot
        self.assertFalse((self.out/'supervision').exists())
    def test_duplicate_event_and_source_rejected_without_duplicate_charge(self):
        source=command(self.p);costs.append_event(self.p,'review-1','review',source,writer=self.p['dynamic_cost_policy']['event_writer'])
        for ident in ('review-1','different-id'):
            with self.assertRaisesRegex(ValueError,'duplicate'):costs.append_event(self.p,ident,'review',source,writer=self.p['dynamic_cost_policy']['event_writer'])
        self.review();self.assertEqual(costs.validate_snapshot(self.p)['worker_seconds'],123.01)
    def test_unknown_missing_wall_and_tamper_rejected(self):
        source=command(self.p);path=Path(source['path']);v=json.loads(path.read_text());v['wall_s']=None;source=f.bound(path,v)
        with self.assertRaises(ValueError):costs.append_event(self.p,'bad','review',source,writer=self.p['dynamic_cost_policy']['event_writer'])
        with self.assertRaises(ValueError):self.review()
    def test_missing_changed_event_or_source_blocks(self):
        event=append(self.p);self.review();path=Path(event['path']);old=path.read_bytes();path.unlink()
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
        path.write_bytes(old);source=Path(self.p['external_activity_roots'][0])/'additional-review-command.json';source.write_text('{}')
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
    def test_outside_root_source_rejected(self):
        source=f.bound(Path(self.tmp.name)/'outside-command.json',dict(wall_s=.1))
        with self.assertRaises(ValueError):costs.append_event(self.p,'outside','review',source,writer=self.p['dynamic_cost_policy']['event_writer'])
    def test_snapshot_expiry_and_independent_reviewer(self):
        with self.assertRaisesRegex(ValueError,'independent'):costs.review(self.p,reviewer=self.p['dynamic_cost_policy']['event_writer'],expires_at='2026-11-05T00:00:00+08:00')
        clock.advance(self.p,601)
        with self.assertRaisesRegex(ValueError,'expired'):admission.check_resources(self.p,self.out)
    def test_total_deadline_and_insufficient_budget_rejected(self):
        clock.advance(self.p,60*60*60)
        with self.assertRaises(TimeoutError):admission.check_resources(self.p,self.out)
    def test_fixture_anchor_tamper_and_rewind_rejected(self):
        with self.assertRaises(ValueError):clock.advance(self.p,-1)
        anchor=Path(self.p['fixture_clock']['anchor']['path']);v=json.loads(anchor.read_text());v['offset']-=100;f.bound(anchor,v)
        with self.assertRaises(ValueError):clock.epoch(self.p)
    def test_new_cost_after_original_resources_before_launch_ack_never_creates_worker(self):
        release(self.p)
        with self.assertRaises(RuntimeError):s.dispatch(self.p,'synthetic','g1','C',4718,execution_adapter=RaceAdapter(self.p))
        folder=self.out/'supervision/g1-C-4718'
        self.assertTrue((folder/'race-added-cost').exists());self.assertTrue((folder/'launch-ack.json').exists())
        self.assertFalse((folder/'worker-started.json').exists());self.assertFalse((self.out/'launched-g1-C-4718').exists())
        self.assertTrue((folder/'stopped').exists());self.assertFalse((folder/'closure.json').exists())
    def test_thread_concurrent_append_is_serialized_and_unique(self):
        source=command(self.p);barrier=threading.Barrier(3);results=[]
        def write(ident):
            barrier.wait()
            try:costs.append_event(self.p,ident,'review',source,writer=self.p['dynamic_cost_policy']['event_writer']);results.append('PASS')
            except ValueError:results.append('DENY')
        threads=[threading.Thread(target=write,args=(name,)) for name in ('parallel-a','parallel-b')]
        for t in threads:t.start()
        barrier.wait()
        for t in threads:t.join(3);self.assertFalse(t.is_alive())
        self.assertEqual(sorted(results),['DENY','PASS']);self.review()
        self.assertAlmostEqual(costs.validate_snapshot(self.p)['worker_seconds'],123.01)
    def test_review_self_cost_no_stage_cannot_be_zero(self):
        before=costs.validate_snapshot(self.p);self.assertEqual(before['cumulative']['worker_seconds'],133.)
        self.review();after=costs.validate_snapshot(self.p)
        self.assertEqual(after['cumulative']['worker_seconds']-before['cumulative']['worker_seconds'],30.)
        self.assertEqual(after['closed_activities'],[])
        self.assertEqual(admission.check_resources(self.p,self.out)['worker_seconds'],163.)
        for ref in after['control_reservations']:cost_control.validate(self.p,ref)
    def test_source_event_and_review_control_costs_each_once(self):
        before=admission.check_resources(self.p,self.out)['worker_seconds']
        source=costs.measured_command(self.p,'control-boundary','review',[sys.executable,'-B','-c','pass'],writer=self.p['dynamic_cost_policy']['event_writer'],gpu_devices=[])
        payload=json.loads(Path(source['path']).read_text())['wall_s']
        event=costs.append_event(self.p,'control-boundary','review',source,writer=self.p['dynamic_cost_policy']['event_writer'])
        self.review();snapshot=costs.validate_snapshot(self.p)
        self.assertAlmostEqual(snapshot['cumulative']['worker_seconds']-before,payload+90.)
        refs=snapshot['control_reservations'];self.assertEqual(len(refs),4);self.assertEqual(snapshot['control_charged_s'],120.)
        operations=sorted(cost_control.validate(self.p,r)['operation'] for r in refs)
        self.assertEqual(operations,['event-append','snapshot-review','snapshot-review','source-publish'])
        for _ in range(3):self.assertEqual(admission.check_resources(self.p,self.out)['worker_seconds'],snapshot['cumulative']['worker_seconds'])
    def test_review_publication_disk_failure_preserves_old_snapshot_cost_and_denies(self):
        old=costs.current_ref(self.p);before=costs.validate_snapshot(self.p)['cumulative']['worker_seconds'];original=clock.publish
        def fail(path,value):
            if Path(path).parent.name=='snapshots':raise OSError('injected snapshot write failure')
            return original(path,value)
        with mock.patch.object(clock,'publish',side_effect=fail),self.assertRaises(OSError):self.review()
        self.assertEqual(costs.validate_snapshot(self.p,old,historical=True)['cumulative']['worker_seconds'],before)
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
    def test_review_failure_after_commit_keeps_unknown_not_free_snapshot(self):
        old=costs.current_ref(self.p);original=clock.publish
        def fail(path,value):
            result=original(path,value)
            if Path(path).parent.name=='snapshot-commits':raise OSError('injected post-commit directory failure')
            return result
        with mock.patch.object(clock,'publish',side_effect=fail),self.assertRaises(OSError):self.review()
        self.assertEqual(costs.validate_snapshot(self.p,old,historical=True)['cumulative']['worker_seconds'],133.)
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
    def test_source_and_event_publication_failure_leave_charged_unknown(self):
        original=clock.publish
        def fail_source(path,value):
            if Path(path).name=='failing-source-command.json':raise OSError('injected source publication')
            return original(path,value)
        with mock.patch.object(clock,'publish',side_effect=fail_source),self.assertRaises(OSError):command(self.p,'failing-source')
        reservations=list((Path(self.p['dynamic_cost_policy']['root'])/'controls').glob('*/reservation.json'))
        self.assertEqual(len(reservations),2)
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
    def test_event_publication_failure_preserves_source_and_denies(self):
        source=command(self.p,'failing-event')
        original=clock.publish
        def fail(path,value):
            if Path(path).parent.name=='events':raise OSError('injected event publication')
            return original(path,value)
        with mock.patch.object(clock,'publish',side_effect=fail),self.assertRaises(OSError):costs.append_event(self.p,'failing-event','review',source,writer=self.p['dynamic_cost_policy']['event_writer'])
        self.assertTrue(Path(source['path']).exists())
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
    def test_control_symlink_cannot_escape_output(self):
        initial=costs.validate_snapshot(self.p);control=initial['control_reservation'];folder=Path(control['path']).parent
        import shutil
        outside=Path(self.tmp.name)/'outside-controls';shutil.copytree(folder,outside);shutil.rmtree(folder);folder.symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):costs.validate_snapshot(self.p)
    def test_unreviewed_control_directory_loss_does_not_restore_previous_budget(self):
        source=command(self.p,'lost-control');value=json.loads(Path(source['path']).read_text());folder=Path(value['control_reservation']['path']).parent
        import shutil
        shutil.rmtree(folder);Path(source['path']).unlink()
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
    def test_review_control_tail_over_envelope_does_not_certify(self):
        with tempfile.TemporaryDirectory(prefix='t9-small-control-') as base:
            p=fixture(base,envelope=.1);old=costs.current_ref(p);original=clock.publish
            def slow(path,value):
                result=original(path,value)
                if Path(path).parent.name=='snapshot-commits':time.sleep(.15)
                return result
            with mock.patch.object(clock,'publish',side_effect=slow),self.assertRaisesRegex(ValueError,'envelope'):costs.review(p,reviewer=p['dynamic_cost_policy']['reviewer'],expires_at='2026-11-05T00:00:00+08:00')
            self.assertAlmostEqual(costs.validate_snapshot(p,old,historical=True)['cumulative']['worker_seconds'],103.1)
            with self.assertRaises(ValueError):admission.check_resources(p,p['new_output_root'])
    def test_deadline_interrupts_cost_lock_wait_without_releasing_other_process(self):
        release(self.p);ready=Path(self.tmp.name)/'deadline-holder-ready';stop=Path(self.tmp.name)/'deadline-holder-stop'
        code="""import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from task9_lr import admission,costs
p=admission.load_protocol(sys.argv[2])
with costs.locked(p):
 Path(sys.argv[3]).touch()
 cutoff=time.monotonic()+5
 while not Path(sys.argv[4]).exists():
  if time.monotonic()>cutoff:raise TimeoutError('fixture holder bounded')
  time.sleep(.01)
"""
        proc=subprocess.Popen([sys.executable,'-B','-c',code,str(FOREM/'src'),str(self.out/'freeze/protocol.json'),str(ready),str(stop)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        results=[]
        def launch():
            try:self.dispatch();results.append('UNEXPECTED')
            except TimeoutError:results.append('DEADLINE_DENY')
        t=threading.Thread(target=launch)
        try:
            cutoff=time.monotonic()+3
            while not ready.exists() and proc.poll() is None and time.monotonic()<cutoff:time.sleep(.005)
            self.assertTrue(ready.exists());t.start();time.sleep(.04);self.assertTrue(t.is_alive())
            clock.advance(self.p,60*60*60);t.join(1)
            self.assertFalse(t.is_alive());self.assertEqual(results,['DEADLINE_DENY']);self.assertIsNone(proc.poll())
            self.assertFalse((self.out/'supervision').exists())
        finally:
            stop.touch()
            if t.ident is not None:t.join(2)
            stdout,stderr=proc.communicate(timeout=3);self.assertEqual(proc.returncode,0,stderr)
    def test_process_cost_append_and_dispatch_share_generation_lock(self):
        release(self.p);ready=Path(self.tmp.name)/'writer-ready';go=Path(self.tmp.name)/'writer-go'
        code="""import json,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from task9_lr import admission,costs
p=admission.load_protocol(sys.argv[2])
with costs.locked(p):
 Path(sys.argv[3]).touch()
 cutoff=time.monotonic()+3
 while not Path(sys.argv[4]).exists():
  if time.monotonic()>cutoff:raise TimeoutError('fixture writer bounded')
  time.sleep(.005)
 source=costs.measured_command(p,'process-review','review',[sys.executable,'-B','-c','pass'],writer=p['dynamic_cost_policy']['event_writer'],gpu_devices=[])
 costs.append_event(p,'process-review','review',source,writer=p['dynamic_cost_policy']['event_writer'])
"""
        proc=subprocess.Popen([sys.executable,'-B','-c',code,str(FOREM/'src'),str(self.out/'freeze/protocol.json'),str(ready),str(go)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        results=[];adapter=life.Adapter(self.p)
        def launch():
            try:results.append(s.dispatch(self.p,'synthetic','g1','C',4718,execution_adapter=adapter))
            except ValueError:results.append('DENY_STALE')
        thread=threading.Thread(target=launch)
        try:
            cutoff=time.monotonic()+3
            while not ready.exists() and proc.poll() is None and time.monotonic()<cutoff:time.sleep(.005)
            self.assertTrue(ready.exists());thread.start();time.sleep(.04)
            self.assertTrue(thread.is_alive());self.assertFalse((self.out/'supervision').exists())
            go.touch();stdout,stderr=proc.communicate(timeout=4);self.assertEqual(proc.returncode,0,stderr)
            thread.join(4);self.assertFalse(thread.is_alive());self.assertEqual(results,['DENY_STALE']);self.assertEqual(adapter.calls,0)
        finally:
            go.touch()
            if proc.poll() is None:proc.kill()
            proc.wait(timeout=3)
            if thread.ident is not None:thread.join(4)
    def test_pending_measured_command_blocks_review_and_admission_until_wait(self):
        release(self.p);result=[]
        def measure():result.append(costs.measured_command(self.p,'waiting-review','review',[sys.executable,'-B','-c','import time; time.sleep(.3)'],writer=self.p['dynamic_cost_policy']['event_writer'],gpu_devices=[]))
        t=threading.Thread(target=measure);t.start();pending=Path(self.p['external_activity_roots'][0])/'waiting-review.cost-pending'
        cutoff=time.monotonic()+2
        while not pending.exists() and time.monotonic()<cutoff:time.sleep(.005)
        self.assertTrue(pending.exists())
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):self.review()
        with self.assertRaises(ValueError):self.dispatch()
        t.join(3);self.assertEqual(len(result),1)
        with self.assertRaises(ValueError):self.dispatch() # closed command still lacks event/review
        costs.append_event(self.p,'waiting-review','review',result[0],writer=self.p['dynamic_cost_policy']['event_writer']);self.review()
        self.assertGreater(costs.validate_snapshot(self.p)['worker_seconds'],3.)
    def test_nested_costs_are_enclosed_same_stage_and_charged_once(self):
        root=Path(self.p['external_activity_roots'][0]);end=clock.capture(self.p)
        def envelope(name,start_delta,end_delta,parent):
            start=dict(end,epoch=end['epoch']-start_delta,monotonic=end['monotonic']-start_delta)
            finish=dict(end,epoch=end['epoch']-end_delta,monotonic=end['monotonic']-end_delta)
            return costs.publish_source(self.p,name,dict(format='task9-lr-measured-command-v1',status='CLOSED',gpu_evidence=gpu_costs.fixture_evidence(self.p,start['epoch'],finish['epoch'],[]),argv=['synthetic-enclosed',name],exit_code=0,wall_s=start_delta-end_delta,started_epoch=start['epoch'],finished_epoch=finish['epoch'],started_clock=start,completed_clock=finish,stage='review',parent_event_id=parent,synthetic_fixture=True,execution_allowed=False),writer=self.p['dynamic_cost_policy']['event_writer'])
        parent=envelope('parent',2,0,None);child=envelope('child',1,.5,'parent')
        costs.append_event(self.p,'parent','review',parent,writer=self.p['dynamic_cost_policy']['event_writer'])
        costs.append_event(self.p,'child','review',child,parent_event_id='parent',writer=self.p['dynamic_cost_policy']['event_writer'])
        self.review();self.assertEqual(costs.validate_snapshot(self.p)['worker_seconds'],185.)
        outside=envelope('outside',3,0,'parent')
        with self.assertRaisesRegex(ValueError,'not enclosed'):costs.append_event(self.p,'outside','review',outside,parent_event_id='parent',writer=self.p['dynamic_cost_policy']['event_writer'])
    def test_missing_snapshot_generation_and_snapshot_tamper_block(self):
        self.review();root=Path(self.p['dynamic_cost_policy']['root']);latest=root/'snapshots/00000002.json';old=latest.read_bytes();latest.unlink()
        with self.assertRaises(ValueError):costs.current_ref(self.p)
        latest.write_bytes(old);v=json.loads(old);v['worker_seconds']=0;f.bound(latest,v)
        with self.assertRaises(ValueError):costs.current_ref(self.p)
    def test_unreviewed_event_and_source_deletion_cannot_restore_old_snapshot(self):
        event=append(self.p);Path(event['path']).unlink()
        (Path(self.p['external_activity_roots'][0])/'additional-review-command.json').unlink()
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
    def test_newer_snapshot_corruption_does_not_rewrite_historical_original_cost(self):
        release(self.p);self.dispatch();rows=admission.activity_rows(self.out,protocol=self.p);old=rows[0]['wall_s']
        self.review();path=Path(self.p['dynamic_cost_policy']['root'])/'snapshots/00000002.json';path.unlink()
        historical=admission.activity_rows(self.out,protocol=self.p);self.assertEqual(historical[0]['wall_s'],old)
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
    def test_extra_unreviewed_event_and_unknown_command_never_zero(self):
        append(self.p);self.review();root=Path(self.p['dynamic_cost_policy']['root'])
        f.bound(root/'events/extra.json',dict(event_id='extra',wall_s=0))
        with self.assertRaises(ValueError):admission.check_resources(self.p,self.out)
    def test_insufficient_remaining_budget_cannot_be_released(self):
        ref=release(self.p);path=Path(ref['path']);v=json.loads(path.read_text());v['remaining_resource_budget']['worker_seconds']=208800;f.bound(path,v)
        with self.assertRaisesRegex(ValueError,'reviewed remaining'):self.dispatch()
        self.assertFalse((self.out/'supervision').exists())
    def test_costs_over_total_budget_block_independent_snapshot(self):
        # Synthetic measured interval exceeds the cumulative worker allowance.
        append(self.p,'over-budget',wall=208800.)
        with self.assertRaisesRegex(ValueError,'cap|exceeds budget'):self.review()
    def test_original_stage_cap_and_finish_time_remain_bound(self):
        release(self.p);self.dispatch();folder=self.out/'supervision/g1-C-4718';path=folder/'lifecycle.json';v=json.loads(path.read_text())
        v['completion_clock']['monotonic']+=3000;v['completion_clock']['epoch']+=3000;v['owner_wait_returned_monotonic']+=3000;v['actual_owner_wait_wall_s']+=3000
        f.bound(path,v);clpath=folder/'closure.json';cl=json.loads(clpath.read_text());cl['lifecycle_sha256']=sha256(path);cl['job_wall_s']+=3000;cl['charged_wall_s']+=3000;f.bound(clpath,cl)
        with self.assertRaises(ValueError):admission.activity_rows(self.out,protocol=self.p)
    def test_real_entrypoints_remain_hard_denied(self):
        with self.assertRaisesRegex(ValueError,'NOT_READY'):s.dispatch(self.p,'synthetic','g1','C',4718)
        self.assertFalse(set(sys.modules)&{'torch','numpy','pytest','task7_sim','task8_sim'})

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--race':raise SystemExit(race_fixture(sys.argv[2],sys.argv[3]))
    unittest.main(verbosity=2)
