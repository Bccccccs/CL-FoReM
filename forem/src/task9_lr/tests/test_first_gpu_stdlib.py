"""First review device declarations: fresh namespaces, production readers only."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
FOREM=Path(__file__).resolve().parents[3];sys.path.insert(0,str(FOREM/'src'))
from task9_lr import admission, costs, cost_control
from task9_lr.runtime import artifact_digest, sha256
spec=importlib.util.spec_from_file_location('first_gpu_fixture',Path(__file__).with_name('test_cross_stage_stdlib.py'))
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)

class FirstGpu(unittest.TestCase):
    def case(self,label,declared,sealed_devices,current_devices,accepted,increment=None,missing_current=False):
        with tempfile.TemporaryDirectory(prefix='t9-first-'+label+'-') as tmp:
            # Do not let the helper create a history snapshot before our inputs.
            with patch.object(costs,'review'):p=x.fixture(tmp)
            out=Path(p['new_output_root']);gpu=p['preferred_gpu_uuid']
            sealed=json.loads((out/'container-inspect.json').read_text());sealed['State']={'Running':False,'FinishedAt':'2026-11-03T15:59:59+00:00'}
            def requests(devices):return [] if devices==[] else [dict(DeviceIDs=[gpu if d=='GPU' else d for d in devices],Count=0)]
            sealed['HostConfig']['DeviceRequests']=requests(sealed_devices)
            current=copy.deepcopy(sealed);current['HostConfig']['DeviceRequests']=requests(current_devices)
            if missing_current:current.pop('HostConfig')
            record=dict(container_id=sealed['Id'],started_epoch=1793721594.)
            if declared!='MISSING':record['gpu_uuid']=gpu if declared=='GPU' else declared
            for name,v in [('container.json',record),('container-inspect.json',sealed),('container-stopped.json',current)]:x.f.bound(out/name,v)
            self.assertEqual(costs.snapshots(p),[])
            notes=dict(label=label,source_sha=artifact_digest(),input_declaration=record,sealed=sealed,current=current)
            try:
                # Both readers see the defect before any snapshot exists.
                if accepted:
                    ref=costs.review(p,reviewer=p['dynamic_cost_policy']['reviewer'],expires_at=p['deadline'])
                    post=admission.check_resources(p,out);snap=json.loads(Path(ref['path']).read_text())
                    self.assertEqual(post['gpu_seconds'],110.+increment)
                    self.assertEqual(post['worker_seconds'],133.)
                    self.assertEqual(snap['cumulative']['gpu_seconds'],post['gpu_seconds'])
                    release=x.release(p);admission.read_release(release['path'],'g1',p,arm='C',seed=4718)
                    # Re-review preserves the same device basis and union.
                    costs.review(p,reviewer=p['dynamic_cost_policy']['reviewer'],expires_at=p['deadline'])
                    self.assertEqual(admission.check_resources(p,out)['gpu_seconds'],post['gpu_seconds'])
                    notes.update(first_review='PASS',resources='PASS',gpu_increment=increment,successor_admission=True)
                else:
                    errors=[]
                    for fn in (lambda:admission.check_resources(p,out),lambda:costs.review(p,reviewer=p['dynamic_cost_policy']['reviewer'],expires_at=p['deadline']),lambda:admission.check_resources(p,out)):
                        with self.assertRaises(ValueError) as ctx:fn()
                        errors.append(str(ctx.exception))
                    self.assertIn('UNKNOWN',errors[1])
                    self.assertEqual(costs.snapshots(p),[])
                    self.assertFalse(list((out/'costs/snapshot-commits').glob('*.json')))
                    self.assertFalse(list((out/'releases').glob('*.json')))
                    with self.assertRaisesRegex(ValueError,'snapshot missing'):x.release(p)
                    # Real dispatcher must refuse before invoking its adapter.
                    adapter=x.life.Adapter(p)
                    self.assertEqual(x.s.dispatch(p,'synthetic','g1','C',4718,execution_adapter=adapter),'hold')
                    self.assertEqual(adapter.calls,0)
                    inventory=costs.inventory(p);control=cost_control.inventory(p)
                    self.assertEqual(control['control_charged_s'],30.);self.assertEqual(inventory['worker_seconds'],33.)
                    denials=list((out/'costs/review-denials').glob('*.json'));self.assertEqual(len(denials),1)
                    self.assertEqual(json.loads(denials[0].read_text())['status'],'DENIED')
                    self.assertFalse(list((out/'costs/controls').glob('*/pending.json')))
                    notes.update(first_review='DENIED',resources='DENIED',gpu_increment='UNKNOWN',successor_admission=False,errors=errors,denial_worker_s=inventory['worker_seconds'])
            finally:
                destination=os.environ.get('TASK9_FIRST_GPU_ARCHIVE')
                if destination:
                    target=Path(destination)/label;shutil.copytree(tmp,target/'raw')
                    notes['original_root']=tmp
                    notes['files']={str(q.relative_to(target)):sha256(q) for q in sorted(target.rglob('*')) if q.is_file()}
                    (target/'result.json').write_text(json.dumps(notes,indent=2)+'\n')
    def test_explicit_same_gpu(self):self.case('same-gpu','GPU',['GPU'],['GPU'],True,5.)
    def test_explicit_no_gpu(self):self.case('no-gpu',None,[],[],True,0.)
    def test_original_counterexample(self):self.case('original','GPU',[],[],False)
    def test_reverse_conflict(self):self.case('reverse',None,['GPU'],['GPU'],False)
    def test_record_different_gpu(self):self.case('other-record','GPU-other',['GPU'],['GPU'],False)
    def test_sealed_different_gpu(self):self.case('other-sealed','GPU',['GPU-other'],['GPU-other'],False)
    def test_inspect_mismatch(self):self.case('inspect-mismatch','GPU',['GPU'],[],False)
    def test_inspect_reverse_mismatch(self):self.case('inspect-reverse',None,[],['GPU'],False)
    def test_missing_record_follows_protocol(self):self.case('legacy-gpu','MISSING',['GPU'],['GPU'],True,5.)
    def test_missing_record_is_not_no_gpu(self):self.case('legacy-conflict','MISSING',[],[],False)
    def test_missing_current_is_unknown(self):self.case('missing-current','GPU',['GPU'],['GPU'],False,missing_current=True)

if __name__=='__main__':unittest.main(verbosity=2)
