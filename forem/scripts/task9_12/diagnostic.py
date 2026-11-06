"""Freeze stratified actual requests before calling BioIK. All repeats retained."""
import sys,os,time,json,gzip,hashlib
from pathlib import Path
import numpy as np,torch
sys.path[:0]=['/workspace/src','/work/src']
from task9_lr.runtime import activate
activate()
from task7_sim.kinematics import Kinematics,base_transform,LOW,HIGH,metrics,fk
from task8_sim.robot import GhostRobotGeometry
from task8_sim.primitive_scene import load_backend_scene
from task9_lr.diagnostics import observing,plain
from backend import Bridge,BioKinematics
from run import OUT,CONFIG,dump,sha,check

def freeze():
 protocol=json.loads((CONFIG/'diagnostic-protocol.json').read_text());wanted=protocol['target_per_stratum'];samples={k:[] for k in protocol['strata']};unavailable=[];eligible={k:0 for k in samples}
 dirs=sorted(OUT.glob('formal-current-*'))
 assert sum(len(json.loads((p/'result.json').read_text())['rows']) for p in dirs if p.is_dir() and (p/'result.json').exists())==588,'full current 588 required'
 for p in dirs:
  if not p.is_dir() or not (p/'result.json').exists():continue
  result=json.loads((p/'result.json').read_text());summary={(r['domain'],r['domain_index']):r for r in result['rows']};chosen={};candidates={}
  for key,r in summary.items():
   st='first_ik_rejection' if r['first_failure_kind']==1 else 'first_collision_rejection' if r['first_failure_kind'] in (2,3,4) else 'zero_progress_no_rejection' if r['failures']==0 and not r['original_success'] else 'executable' if r['strict_success'] else None
   if st is not None:candidates[key]=st;eligible[st]+=1
  with gzip.open(p/'requests.jsonl.gz','rt') as f:
   for line in f:
    r=json.loads(line);key=(r['domain'],r['domain_index']);st=candidates.get(key)
    if st is None or key in chosen:continue
    s=summary[key]
    take=(r['case_id']==s['first_failure_case']) if st.startswith('first_') else bool(r['commit']) if st=='executable' else (r['commit'] and r['trials']==r['s'] and r['base_trial']==r['base_before'])
    if take:chosen[key]=r
  for key,st in candidates.items():
   if key not in chosen:unavailable.append(dict(training_seed=result['training_seed'],domain=key[0],domain_index=key[1],stratum=st,reason='no suitable real IK request; not fabricated'));continue
   if len(samples[st])<wanted:samples[st].append(dict(**chosen[key],stratum=st,source_file=str(p/'requests.jsonl.gz')))
 rows=[r for st in protocol['strata'] for r in samples[st]]
 manifest=dict(schema='task9.12-paired-request-v1',protocol=protocol,rows=rows,counts={k:len(v) for k,v in samples.items()},eligible_episodes=eligible,unavailable=unavailable,main_timeout_s=json.loads((CONFIG/'frozen-budget.json').read_text())['timeout_s'],frozen_epoch=time.time(),no_bioik_outcome_selection=True)
 dump(CONFIG/'paired-request-manifest.json',manifest);return manifest

class Capture:
 def ik_pre_hold(self,kin,q,r,prev):self.q=q.detach().clone();self.r={n:getattr(r,n).detach().clone() for n in r.__dataclass_fields__}

def collision(scene,robot,base,q):
 caps=robot(base,q);r=scene.collide(base,caps,robot=robot,q=q,allowed=None)
 return dict(base=bool(r.base[0]),arm=bool(r.arm[0]),self_collision=bool(r.self_collision[0]),any=bool(r.any[0]),pair='unknown: original boolean API')

@torch.no_grad()
def main():
 torch.set_num_threads(2);torch.set_num_interop_threads(1)
 manifest=freeze();kin=Kinematics();kin.dls_cuda_graph=True;robot=GhostRobotGeometry();cache={};baseline=[];summary=[]
 def tensor(v):return torch.tensor(v,device='cuda',dtype=torch.float32).unsqueeze(0)
 def solve(row,backend):
  check();base=tensor(row['base_trial']);target=tensor(row['target_world']);prev=tensor(row['q_seed']);key=(row['pool'],row['map_id'])
  if key not in cache:cache[key]=load_backend_scene('primitive-obb-v1',*key,device='cuda',dtype=torch.float32)
  scene=cache[key];capture=Capture();torch.cuda.synchronize();t=time.perf_counter();cpu=time.process_time()
  with observing(capture):result=backend.solve_world(base,target,prev,robot=robot)
  torch.cuda.synchronize();wall=time.perf_counter()-t;cput=time.process_time()-cpu
  arm=torch.linalg.solve(base_transform(base)@kin.fixed('mount',prev),target)
  direct=kin._result(capture.q,arm,torch.tensor([-2],device='cuda'),torch.tensor([False],device='cuda'))
  assert torch.equal(direct.accepted,result.accepted),'acceptance mismatch'
  coll=collision(scene,robot,base,result.q);dq=(capture.q-prev)[0]
  return dict(case_id=row['case_id'],stratum=row['stratum'],backend='bioik' if isinstance(backend,BioKinematics) else 'current',q_raw=plain(capture.q[0]),q_held=plain(result.q[0]),position_m=float(capture.r['position'][0]),cbl=float(capture.r['cbl'][0]),angle_rad=float(capture.r['angle'][0]),ik_accepted=bool(result.accepted[0]),collision=coll,accepted=bool(result.accepted[0]) and not coll['any'],joint_delta_l2=float(dq.norm()),joint_delta_peak=float(dq.abs().max()),wall_s=wall,cpu_s=cput,gpu_timer='not separately available for synchronous CPU bridge; GPU operations inside wall',solver=None if not isinstance(backend,BioKinematics) else backend.last_meta[0],original_current_ik_accepted=row['ik_accepted'],original_current_commit=row['commit'],q_seed=row['q_seed'],base_trial=row['base_trial'],target_world=row['target_world'])
 for row in manifest['rows']:baseline.append(solve(row,kin))
 dump(OUT/'paired-current.json',baseline)
 for repetition in range(manifest['protocol']['diagnostic_repetitions']):
  bridge=Bridge();bio=BioKinematics(bridge,manifest['main_timeout_s']);rows=[]
  try:
   for row in manifest['rows']:rows.append(dict(repetition=repetition,**solve(row,bio)))
  finally:bridge.close()
  dump(OUT/f'paired-bioik-repeat{repetition}.json',rows)
  transitions={f'{a}->{b}':0 for a in (False,True) for b in (False,True)}
  for a,b in zip(baseline,rows):assert a['case_id']==b['case_id'];transitions[f"{a['accepted']}->{b['accepted']}"]+=1
  summary.append(dict(repetition=repetition,n=len(rows),transitions=transitions,current_wall_s=sum(r['wall_s'] for r in baseline),bioik_wall_s=sum(r['wall_s'] for r in rows),by_stratum={st:dict(n=sum(r['stratum']==st for r in rows),current_accepted=sum(a['accepted'] for a in baseline if a['stratum']==st),bioik_accepted=sum(a['accepted'] for a in rows if a['stratum']==st)) for st in manifest['counts']},current_joint_delta_median=float(np.median([r['joint_delta_l2'] for r in baseline])),bioik_joint_delta_median=float(np.median([r['joint_delta_l2'] for r in rows]))))
 dump(OUT/'paired-summary.json',dict(status='complete',manifest_sha256=sha(CONFIG/'paired-request-manifest.json'),main_repetition=0,repetitions=summary,candidate_callback_difference='current avoids self/ground among analytic branches; BioIK has no internal candidate callback; all final collision checks unchanged',geometric_unreachable='unknown unless independently proved; no inference from solver failure'))
 print(json.dumps(dict(event='paired_done',summary=summary)),flush=True)
if __name__=='__main__':main()
