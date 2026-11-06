# Derived from original parallel-run-v1 metadata fixture; retry-directory coverage.
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
F=Path('/home/ybc/projects/CL-FoReM-task9/forem');spec=importlib.util.spec_from_file_location('shard_review',F/'scripts/task9_11_parallel_review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class T(unittest.TestCase):
 def test_profile_remaining_closed_native_evidence_and_order(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);out=root/'out';audit=root/'audit';folder=out/'formal-L-seed4718';folder.mkdir(parents=True);audit.mkdir()
   native=F/'results/task9/t9.11-real-program-20261104-r3/formal-C-seed4718'
   def put(q,v):
    q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(v))
    if q.name=='result.json':
     control=out/'parallel-shards/state.json';control.parent.mkdir(exist_ok=True)
     c=json.loads(control.read_text()) if control.exists() else {'jobs':{'L4718':{'phases':{}}}}
     c['jobs']['L4718']['phases'][v['phase']]={'result':m.ref(q)}
     control.write_text(json.dumps(c))
    return m.ref(q)
   def raw(q):q.write_text('{}\n');return m.ref(q)
   p=json.loads((F/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.1/save-repair-v1/real-contract-program-r3-v1.json').read_text());p['new_output_root']=str(out)
   policy={'allowed_gpu_uuids':['gpu0','gpu2'],'allocation_seconds':{'L4718':50400}}
   a={'jobs':[{'name':'L4718','arm':'L','seed':4718,'gpu_index':0,'config':p['scientific_configs']['L-4718']}],'save_reserve_s':1800,'control_reserve_s':120}
   state=dict(Id='fixturecid',Image=m.g.IMAGE,HostConfig={'DeviceRequests':[{'DeviceIDs':['gpu0']}]},State=dict(Running=False,Pid=0,StartedAt='2026-11-05T00:00:00Z',FinishedAt='2026-11-05T00:02:00Z'))
   summary=json.loads((native/'profile-summary.json').read_text());sr=put(folder/'profile-summary.json',summary);ev=json.loads((native/'validation-0250000.json').read_text());er=put(folder/'validation-0250000.json',ev)
   rr=put(folder/'profile-restore.json',dict(steps=250000,scientific_limit=3000000,actual_devices={'fixture':'cuda:0'}))
   pe={'profile_checkpoint':raw(folder/'profile.pt'),'profile_summary':sr,'profile_restore':rr,'profile_evaluation':er,'checkpoint_costs':raw(folder/'profile-checkpoint-costs.jsonl'),'interactions':raw(folder/'profile-interactions.jsonl'),'diagnostic_account':put(folder/'profile-diagnostic-account.json',{'bytes':1})}
   put(folder/'episodes-started.jsonl',{'count':196})
   base=dict(status='PASS',run_id=p['run_id'],source_digest=m.SOURCE,job='L4718',phase='profile',arm='L',seed=4718,episodes_before=0,episodes_after=196,folder=str(folder),exact_stopped={'container_stopped':True,'inspect':state},container_id='fixturecid',gpu_uuid='gpu0',actual_outer_wall_s=130,actual_worker_wall_s=120,summary=sr,profile_restore=rr,profile_evidence=pe)
   result=out/'shards/L4718/profile-retry1/result.json';put(result,base)
   with patch.object(m.m,'AUDIT',audit):
    cert=m.review_phase(a,p,policy,'L4718','profile');self.assertEqual(m.b.read_ref(cert['independent_verdict'])['evaluation_episodes'],196)
    wrong=copy.deepcopy(base);wrong['gpu_uuid']='gpu2';put(result,wrong)
    with self.assertRaises(ValueError):m.review_phase(a,p,policy,'L4718','profile')
    put(result,base)
    remaining=copy.deepcopy(base);remaining.update(phase='remaining',episodes_before=196,episodes_after=2352,summary=put(folder/'summary.json',{'state':{'steps':3000000,'env_actions':3000000},'updates':299975}))
    put(out/'shards/L4718/remaining/result.json',remaining);put(folder/'episodes-started.jsonl',{'count':2352})
    for step in range(250000,3000001,250000):put(folder/f'validation-{step:07d}.json',dict(ev,step=step))
    for name in ['final.pt','final.actor.pt','final.meta.json']:raw(folder/name)
    r=m.review_phase(a,p,policy,'L4718','remaining');self.assertEqual(m.b.read_ref(r['independent_verdict'])['consumed_transfers'],2750000)
    self.assertEqual(m.publish_ordered(a,p)['waiting_for'],'profile-C-4718')
    for phase in ('profile','remaining'):
     cr=put(audit/(phase+'C.json'),dict(status='PASS_COMPLETE',activity=phase+'-C-4718',source_digest=m.SOURCE));put(out/'reviews'/(phase+'-C-4718.json'),{'independent_verdict':cr})
    pub=m.publish_ordered(a,p);self.assertEqual(pub['published'],['profile-L-4718','remaining-L-4718']);self.assertEqual(pub['waiting_for'],'profile-C-4719')
if __name__=='__main__':unittest.main()
