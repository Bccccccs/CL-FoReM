"""GPU two-ledger acceptance through real production readers/dispatch; stdlib only."""
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

FOREM=Path(__file__).resolve().parents[3];sys.path.insert(0,str(FOREM/'src'))
from task9_lr import admission, clock, continuation, costs, gpu_costs
from task9_lr.runtime import sha256,artifact_digest
spec=importlib.util.spec_from_file_location('gpu_cross',Path(__file__).with_name('test_cross_stage_stdlib.py'))
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
f=x.f;life=x.life


def source(p,name,start,end,devices,intervals=None):
    capture=clock.capture(p);offset=capture['offset']
    evidence=gpu_costs.fixture_evidence(p,start,end,devices)
    if intervals is not None:evidence['intervals']=intervals
    return costs.publish_source(p,name,dict(format='task9-lr-measured-command-v1',status='CLOSED',
        argv=['synthetic-inert-attribution',name],exit_code=0,wall_s=end-start,
        started_epoch=start,finished_epoch=end,
        started_clock=dict(capture,epoch=start,monotonic=start-offset),
        completed_clock=dict(capture,epoch=end,monotonic=end-offset),
        synthetic_fixture=True,execution_allowed=False,stage='review',parent_event_id=None,
        gpu_evidence=evidence),writer=p['dynamic_cost_policy']['event_writer'])


def append(p,name,start,end,devices,intervals=None):
    ref=source(p,name,start,end,devices,intervals)
    return costs.append_event(p,name,'review',ref,writer=p['dynamic_cost_policy']['event_writer'])


def review(p):
    return costs.review(p,reviewer=p['dynamic_cost_policy']['reviewer'],expires_at=p['deadline'])


def container(p,start,end=None):
    out=Path(p['new_output_root']);device=p['preferred_gpu_uuid']
    state=json.loads((out/'container-inspect.json').read_text());state['HostConfig']['DeviceRequests']=[dict(DeviceIDs=[device],Count=0)]
    f.bound(out/'container-inspect.json',state)
    f.bound(out/'container.json',dict(container_id=state['Id'],name='synthetic',started_epoch=start,gpu_uuid=device))
    if end is not None:
        state['State']=dict(Running=False,FinishedAt=dt.datetime.fromtimestamp(end,dt.timezone.utc).isoformat())
        f.bound(out/'container-stopped.json',state)
    return state


def archive(p,label,summary):
    destination=os.environ.get('TASK9_GPU_JOINT_ARCHIVE')
    if not destination:return
    target=Path(destination)/label;target.mkdir(parents=True,exist_ok=False);base=Path(p['continuation']['host_workspace']).parent
    manifest=[]
    for path in sorted(base.rglob('*')):
        if not path.is_file() or path.is_symlink():continue
        relative=path.relative_to(base);copy=target/'files'/relative;copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,copy)
        manifest.append(dict(original_path=str(path),archive=str(copy),sha256=sha256(copy)))
    f.bound(target/'manifest.json',dict(source_artifact=artifact_digest(),files=manifest,summary=summary))


class GpuAccountingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='t9-gpu-');self.p=x.fixture(self.tmp.name);self.out=Path(self.p['new_output_root'])
    def tearDown(self):self.tmp.cleanup()
    def dispatch(self,stage='g1',arm='C'):
        return x.s.dispatch(self.p,'synthetic',stage,arm,4718,execution_adapter=life.Adapter(self.p,duration=.03))
    def test_joint_cpu_added_review_expired_token_successor_keeps_gpu_unchanged(self):
        first=x.release(self.p);self.assertEqual(self.dispatch(),'passed')
        closure=self.out/'supervision/g1-C-4718/closure.json';protocol=self.out/'freeze/protocol.json'
        hashes={str(p):sha256(p) for p in (protocol,Path(first['path']),closure)}
        before=admission.check_resources(self.p,self.out);clock.advance(self.p,3600)
        script='import json,sys;sys.path.insert(0,'+repr(str(FOREM/'src'))+');from task9_lr import admission;p=admission.load_protocol(sys.argv[1]);assert len(admission.activity_rows(p["new_output_root"],protocol=p))==1;print("independent CPU review PASS")'
        ref=costs.measured_command(self.p,'cpu-independent-review','review',[sys.executable,'-B','-c',script,str(protocol)],writer=self.p['dynamic_cost_policy']['event_writer'],gpu_devices=[])
        measured=json.loads(Path(ref['path']).read_text());self.assertEqual(measured['exit_code'],0)
        event=costs.append_event(self.p,'cpu-independent-review','review',ref,writer=self.p['dynamic_cost_policy']['event_writer'])
        with self.assertRaisesRegex(ValueError,'stale'):admission.check_resources(self.p,self.out)
        snapshot=review(self.p);middle=admission.check_resources(self.p,self.out)
        self.assertAlmostEqual(middle['worker_seconds']-before['worker_seconds'],measured['wall_s']+90.)
        self.assertEqual(middle['gpu_seconds'],before['gpu_seconds']);self.assertEqual(middle['reserved_gpu_seconds'],0)
        release=x.release(self.p,'gate-evaluate','L');self.assertEqual(self.dispatch('gate-evaluate','L'),'passed')
        after=admission.check_resources(self.p,self.out);rows=admission.activity_rows(self.out,protocol=self.p)
        self.assertAlmostEqual(after['worker_seconds']-middle['worker_seconds'],rows[1]['job_wall_s']+30.)
        self.assertEqual(after['gpu_seconds'],110.)
        self.assertEqual(self.dispatch(),'already_passed');self.assertEqual(admission.check_resources(self.p,self.out)['worker_seconds'],after['worker_seconds'])
        self.assertEqual(hashes,{path:sha256(path) for path in hashes})
        summary=dict(before=before,middle=middle,after=after,first=first,event=event,snapshot=snapshot,release=release,measured_payload_s=measured['wall_s'],old_sha=hashes)
        archive(self.p,'cpu-joint',summary);print(json.dumps(dict(case='cpu-joint',**summary)),flush=True)
    def test_joint_gpu_held_container_actual_worker_cpu_review_then_successor(self):
        now=clock.epoch(self.p);state=container(self.p,now-10)
        # The reviewer reuses existing explicit inspect input, never fabricates a
        # stopped receipt or calls Docker. Unknown default remains fail closed.
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):review(self.p)
        first_snapshot=costs.review(self.p,reviewer=self.p['dynamic_cost_policy']['reviewer'],expires_at=self.p['deadline'],container_state=state)
        x.release(self.p);self.assertEqual(self.dispatch(),'passed')
        closed=self.out/'supervision/g1-C-4718/closure.json';old_hash=sha256(closed)
        before=admission.check_resources(self.p,self.out,container_state=state);clock.advance(self.p,3600)
        ref=costs.measured_command(self.p,'held-cpu-review','review',[sys.executable,'-B','-c','pass'],writer=self.p['dynamic_cost_policy']['event_writer'],gpu_devices=[])
        wall=json.loads(Path(ref['path']).read_text())['wall_s']
        costs.append_event(self.p,'held-cpu-review','review',ref,writer=self.p['dynamic_cost_policy']['event_writer'])
        snap=costs.review(self.p,reviewer=self.p['dynamic_cost_policy']['reviewer'],expires_at=self.p['deadline'],container_state=state)
        value=json.loads(Path(snap['path']).read_text());self.assertEqual(value['cumulative']['gpu_seconds'],gpu_costs.seconds(value['cumulative_gpu_intervals']))
        basis=value['gpu_container_evidence'];self.assertEqual(basis['resource_observed_epoch'],value['resource_observed_epoch'])
        self.assertAlmostEqual(value['cumulative']['gpu_seconds'],110+value['resource_observed_epoch']-now+10)
        self.assertAlmostEqual(value['cumulative']['worker_seconds']-before['worker_seconds'],wall+90.)
        x.release(self.p,'gate-evaluate','L');self.assertEqual(self.dispatch('gate-evaluate','L'),'passed')
        self.assertEqual(sha256(closed),old_hash)
        after=admission.check_resources(self.p,self.out,container_state=state)
        self.assertGreater(after['gpu_seconds']-before['gpu_seconds'],3600.)
        # Only held-window elapsed contributes GPU; the CPU review/control90 is
        # absent from the raw start/end oracle and metadata reservations are0.
        self.assertAlmostEqual(after['gpu_seconds'],110+after['resource_observed_epoch']-now+10)
        archive(self.p,'gpu-held-joint',dict(before=before,after=after,first_snapshot=first_snapshot,snapshot=snap))
    def test_inherited_command_gpu_overlap_is_counted_once(self):
        p=f.make_fixture(Path(self.tmp.name)/'inherited-overlap');entry=p['continuation']['external_cost_inventory'][0];path=Path(entry['path']);item=json.loads(path.read_text())
        item['gpu_evidence']=gpu_costs.fixture_evidence(p,item['started_epoch'],item['finished_epoch'],[p['preferred_gpu_uuid']]);changed=f.bound(path,item)
        p['continuation']['external_cost_inventory'][0]=changed
        account_path=Path(p['continuation']['accounting_snapshot']['path']);account=json.loads(account_path.read_text());account['command_components']=[changed]
        p['continuation']['accounting_snapshot']=f.bound(account_path,account)
        self.assertEqual(admission.check_resources(p,p['new_output_root'])['gpu_seconds'],110.)
        item['started_epoch']+=120;item['finished_epoch']+=120
        item['gpu_evidence']=gpu_costs.fixture_evidence(p,item['started_epoch'],item['finished_epoch'],[p['preferred_gpu_uuid']])
        changed=f.bound(path,item);p['continuation']['external_cost_inventory'][0]=changed;account['command_components']=[changed];p['continuation']['accounting_snapshot']=f.bound(account_path,account)
        with self.assertRaisesRegex(ValueError,'contradicts'):admission.check_resources(p,p['new_output_root'])
    def test_union_container_idle_partial_command_duplicates_and_separate_interval(self):
        now=clock.epoch(self.p);gpu=self.p['preferred_gpu_uuid']
        container(self.p,now-30,now-10);review(self.p)
        before=admission.check_resources(self.p,self.out);self.assertAlmostEqual(before['gpu_seconds'],130.,places=5)
        interval=dict(device=gpu,started_epoch=now-25,finished_epoch=now-20)
        append(self.p,'gpu-partial-20s',now-30,now-10,[gpu],[interval,interval]);review(self.p)
        duplicate=admission.check_resources(self.p,self.out);self.assertAlmostEqual(duplicate['gpu_seconds'],130.,places=5)
        append(self.p,'gpu-distinct',now-5,now-2,[gpu]);review(self.p)
        after=admission.check_resources(self.p,self.out);self.assertAlmostEqual(after['gpu_seconds'],133.,places=5)
        self.assertAlmostEqual(after['worker_seconds']-before['worker_seconds'],20+3+180.)
        archive(self.p,'gpu-union',dict(before=before,duplicate=duplicate,after=after))
    def test_near_balance_cpu_controls_no_false_reject_genuine_gpu_reserve_reject(self):
        start=dt.datetime.fromisoformat(self.p['started_at']).timestamp();deadline=dt.datetime.fromisoformat(self.p['deadline']).timestamp()
        # Move within the original window; no caller clock override or changed cap.
        clock.advance(self.p,deadline-2000-clock.epoch(self.p));state=container(self.p,start)
        costs.review(self.p,reviewer=self.p['dynamic_cost_policy']['reviewer'],expires_at=self.p['deadline'],container_state=state);before=admission.check_resources(self.p,self.out,container_state=state)
        now=clock.epoch(self.p);append(self.p,'near-balance-cpu',now-1900.,now,[]);costs.review(self.p,reviewer=self.p['dynamic_cost_policy']['reviewer'],expires_at=self.p['deadline'],container_state=state)
        after=admission.check_resources(self.p,self.out,container_state=state)
        old_false_gpu=after['gpu_seconds']+110+costs.inventory(self.p)['worker_seconds']
        self.assertGreater(old_false_gpu,self.p['max_gpu_seconds'])
        allowed=admission.check_resources(self.p,self.out,new_worker_seconds=34,new_gpu_seconds=4,container_state=state)
        self.assertEqual(allowed['reserved_gpu_seconds'],4.)
        self.assertLess(allowed['gpu_seconds']+4,self.p['max_gpu_seconds'])
        with self.assertRaisesRegex(ValueError,'GPU cap'):admission.check_resources(self.p,self.out,new_gpu_seconds=2001,container_state=state)
        self.assertAlmostEqual(after['gpu_seconds']-before['gpu_seconds'],after['resource_observed_epoch']-before['resource_observed_epoch'])
        token=x.release(self.p,seconds=1950)
        value=json.loads(Path(token['path']).read_text());value['remaining_resource_budget']=json.loads(Path(value['budget_snapshot']['path']).read_text())['remaining_resource_budget'];token=f.bound(Path(token['path']),value)
        self.assertEqual(self.dispatch(),'passed')
        archive(self.p,'near-balance',dict(before=before,after=after,allowed=allowed,old_false_gpu=old_false_gpu,release=token))
    def test_missing_or_contradictory_attribution_is_unknown(self):
        for kind in ('missing','cpu-interval','wrong-device','out-of-scope','not-complete','real-assertion'):
            with self.subTest(kind=kind):
                p=x.fixture(Path(self.tmp.name)/kind);now=clock.epoch(p);gpu=p['preferred_gpu_uuid']
                ref=source(p,kind,now-2,now,[]);path=Path(ref['path']);item=json.loads(path.read_text())
                if kind=='missing':item.pop('gpu_evidence')
                elif kind=='cpu-interval':item['gpu_evidence']['intervals']=[dict(device=gpu,started_epoch=now-2,finished_epoch=now)]
                elif kind=='wrong-device':item['gpu_evidence']['devices']=['GPU-unauthorized']
                elif kind=='out-of-scope':item['gpu_evidence'].update(devices=[gpu],intervals=[dict(device=gpu,started_epoch=now-3,finished_epoch=now)])
                elif kind=='not-complete':item['gpu_evidence']['complete']=False
                else:item['synthetic_fixture']=False
                # Rebinding source alone cannot repair its immutable control receipt.
                changed=f.bound(path,item)
                with self.assertRaises(ValueError):costs.append_event(p,kind,'review',changed,writer=p['dynamic_cost_policy']['event_writer'])
                with self.assertRaises(ValueError):admission.check_resources(p,p['new_output_root'])
    def test_attribution_validation_rejects_direct_contradictions(self):
        now=clock.epoch(self.p);gpu=self.p['preferred_gpu_uuid'];item=dict(synthetic_fixture=True,gpu_evidence=gpu_costs.fixture_evidence(self.p,now-3,now,[]))
        for change in (dict(devices=[gpu],intervals=[]),dict(intervals=[dict(device=gpu,started_epoch=now-2,finished_epoch=now)]),dict(complete=False),dict(devices=['other'])):
            with self.subTest(change=change),self.assertRaises(ValueError):gpu_costs.evidence(self.p,dict(item,gpu_evidence=dict(item['gpu_evidence'],**change)))
    def test_inherited_disjoint_intervals_reconcile_scalar_and_union(self):
        account=json.loads(Path(self.p['continuation']['accounting_snapshot']['path']).read_text());gpu=self.p['preferred_gpu_uuid'];start=account['gpu_evidence']['started_epoch']
        evidence=dict(account['gpu_evidence'],finished_epoch=start+120,intervals=[dict(device=gpu,started_epoch=start,finished_epoch=start+50),dict(device=gpu,started_epoch=start+60,finished_epoch=start+120)])
        self.assertEqual(gpu_costs.seconds(gpu_costs.evidence(self.p,dict(account,gpu_evidence=evidence))),110.)
        account['gpu_evidence']=evidence;path=Path(self.p['continuation']['accounting_snapshot']['path'])
        self.p['continuation']['accounting_snapshot']=f.bound(path,account)
        self.assertEqual(continuation.inherited_accounting(self.p)['gpu_seconds'],110.)
        account['exact_costs']['gpu_seconds']=111.;self.p['continuation']['accounting_snapshot']=f.bound(path,account)
        with self.assertRaisesRegex(ValueError,'aggregate/interval'):continuation.inherited_accounting(self.p)
    def test_real_command_api_missing_attribution_refuses_before_execution(self):
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):costs.measured_command(self.p,'no-evidence','review',[sys.executable,'-B','-c','raise Exception("must not run")'],writer=self.p['dynamic_cost_policy']['event_writer'])
        p=dict(self.p,continuation=dict(self.p['continuation'],synthetic_fixture=False));p.pop('fixture_clock')
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):costs.measured_command(p,'no-real-api','review',[sys.executable,'-B','-c','raise Exception("must not run")'],writer=p['dynamic_cost_policy']['event_writer'],gpu_devices=[])
        self.assertFalse(list(Path(self.p['external_activity_roots'][0]).glob('no-*-command.json')))
    def test_first_container_basis_rejects_mismatched_or_missing_identity(self):
        for defect in ('alien-record-current','missing-sealed','missing-current','all-missing'):
            with self.subTest(defect=defect):
                p=x.fixture(Path(self.tmp.name)/defect);out=Path(p['new_output_root']);state=container(p,clock.epoch(p)-10)
                record=json.loads((out/'container.json').read_text());sealed=json.loads((out/'container-inspect.json').read_text())
                if defect=='alien-record-current':record['container_id']='alien-container';state['Id']='alien-container'
                elif defect=='missing-sealed':sealed.pop('Id')
                elif defect=='missing-current':state.pop('Id')
                else:record.pop('container_id');sealed.pop('Id');state.pop('Id')
                f.bound(out/'container.json',record);f.bound(out/'container-inspect.json',sealed)
                with self.assertRaisesRegex(ValueError,'identity mismatch UNKNOWN'):admission.check_resources(p,out,container_state=state)
                with self.assertRaisesRegex(ValueError,'identity mismatch UNKNOWN'):costs.review(p,reviewer=p['dynamic_cost_policy']['reviewer'],expires_at=p['deadline'],container_state=state)
    def test_audited_stopped_five_second_idle_window(self):
        now=clock.epoch(self.p);container(self.p,now-10,now-5);review(self.p)
        observed=admission.check_resources(self.p,self.out)
        self.assertAlmostEqual(observed['gpu_seconds'],115.,places=5)
        self.assertEqual(observed['worker_seconds'],163.) # No worker payload for idle GPU hold.
    def test_reviewed_container_evidence_tampering_or_loss_blocks(self):
        for defect in ('later-start','CPU-allocation','earlier-stop','later-stop','restart','missing-record'):
            with self.subTest(defect=defect):
                p=x.fixture(Path(self.tmp.name)/defect);out=Path(p['new_output_root']);now=clock.epoch(p);container(p,now-20,now-10);snapshot=review(p)
                paths={name:out/name for name in ('container.json','container-inspect.json','container-stopped.json')}
                if defect=='later-start':
                    item=json.loads(paths['container.json'].read_text());item['started_epoch']+=5;f.bound(paths['container.json'],item)
                elif defect=='CPU-allocation':
                    for name in ('container-inspect.json','container-stopped.json'):
                        item=json.loads(paths[name].read_text());item['HostConfig']['DeviceRequests']=[];f.bound(paths[name],item)
                elif defect in ('earlier-stop','later-stop'):
                    item=json.loads(paths['container-stopped.json'].read_text());item['State']['FinishedAt']=dt.datetime.fromtimestamp(now-(15 if defect=='earlier-stop' else 5),dt.timezone.utc).isoformat();f.bound(paths['container-stopped.json'],item)
                elif defect=='restart':
                    item=json.loads(paths['container-stopped.json'].read_text());item['State']['Running']=True;f.bound(paths['container-stopped.json'],item)
                else:paths['container.json'].unlink()
                with self.assertRaisesRegex(ValueError,'GPU'):admission.check_resources(p,out)
                with self.assertRaisesRegex(ValueError,'GPU'):review(p)
                self.assertEqual(sha256(snapshot['path']),snapshot['sha256'])
    def test_running_to_stopped_retains_reviewed_span_and_rejects_earlier_end(self):
        now=clock.epoch(self.p);state=container(self.p,now-10)
        ref=costs.review(self.p,reviewer=self.p['dynamic_cost_policy']['reviewer'],expires_at=self.p['deadline'],container_state=state)
        prior=json.loads(Path(ref['path']).read_text())['resource_observed_epoch']
        clock.advance(self.p,1.);end=clock.epoch(self.p)-.01
        stopped=dict(state,State=dict(Running=False,FinishedAt=dt.datetime.fromtimestamp(end,dt.timezone.utc).isoformat()))
        f.bound(self.out/'container-stopped.json',stopped);review(self.p)
        value=admission.check_resources(self.p,self.out);self.assertGreater(end,prior);self.assertAlmostEqual(value['gpu_seconds'],110+end-now+10,places=5)
        # Fresh namespace for the invalid live->past-stop contradiction.
        p=x.fixture(Path(self.tmp.name)/'shorter');out=Path(p['new_output_root']);now=clock.epoch(p);state=container(p,now-10)
        costs.review(p,reviewer=p['dynamic_cost_policy']['reviewer'],expires_at=p['deadline'],container_state=state)
        stopped=dict(state,State=dict(Running=False,FinishedAt=dt.datetime.fromtimestamp(now-1,dt.timezone.utc).isoformat()))
        f.bound(out/'container-stopped.json',stopped)
        with self.assertRaisesRegex(ValueError,'shortened'):admission.check_resources(p,out)
    def test_container_ambiguous_all_or_changed_device_unknown(self):
        now=clock.epoch(self.p);state=container(self.p,now-5,now-1)
        for request in (dict(Count=-1),dict(DeviceIDs=[]),dict(DeviceIDs=[self.p['preferred_gpu_uuid']],Count=-1),dict(DeviceIDs=['GPU-other'])):
            with self.subTest(request=request),self.assertRaisesRegex(ValueError,'UNKNOWN'):
                gpu_costs.allocation(self.p,dict(HostConfig=dict(DeviceRequests=[request])))
        changed=dict(state,HostConfig=dict(DeviceRequests=[]))
        with self.assertRaisesRegex(ValueError,'differs'):admission.check_resources(self.p,self.out,container_state=changed)
    def test_inherited_or_static_legacy_missing_evidence_cannot_be_zero(self):
        p=f.make_fixture(Path(self.tmp.name)/'static');entry=p['continuation']['external_cost_inventory'][-1];path=Path(entry['path']);item=json.loads(path.read_text());item.pop('gpu_evidence');p['continuation']['external_cost_inventory'][-1]=f.bound(path,item)
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):continuation.validate_external_costs(p)
        account=json.loads(Path(p['continuation']['accounting_snapshot']['path']).read_text());account.pop('gpu_evidence');p['continuation']['accounting_snapshot']=f.bound(Path(p['continuation']['accounting_snapshot']['path']),account)
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):continuation.inherited_accounting(p)
    def test_noncontinuation_external_gpu_interval_is_charged_and_missing_rejected(self):
        legacy=dict(self.p);legacy['format']='task9-lr-protocol-v1';legacy.pop('continuation');legacy.pop('dynamic_cost_policy');legacy.pop('fixture_clock');legacy['synthetic_fixture']=True
        root=Path(self.tmp.name)/'legacy-external';root.mkdir();legacy['external_activity_roots']=[str(root)]
        now=clock.epoch(legacy);item=dict(synthetic_fixture=True,wall_s=5.,started_epoch=now-5,finished_epoch=now,gpu_evidence=gpu_costs.fixture_evidence(legacy,now-5,now,[legacy['preferred_gpu_uuid']]))
        path=root/'legacy-command.json';f.bound(path,item)
        self.assertEqual(admission.check_resources(legacy,self.out)['gpu_seconds'],5.)
        legacy['max_gpu_seconds']=4. # Isolated legacy reader fixture only.
        with self.assertRaisesRegex(ValueError,'GPU cap'):admission.check_resources(legacy,self.out)
        legacy['max_gpu_seconds']=self.p['max_gpu_seconds']
        item.pop('gpu_evidence');f.bound(path,item)
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):admission.check_resources(legacy,self.out)


if __name__=='__main__':unittest.main(verbosity=2)
