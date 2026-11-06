"""Production development-task evaluation adapter smoke, plus action/RNG parity."""
import sys,argparse,types,copy,json,time
from pathlib import Path
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
sys.path.insert(0,'/workspace/src')
from task9_lr.runtime import activate
activate()
import torch
from engineering_load import load_smoke
from task9_rllib.training import restore_environment
from task9_rllib.observer import MetricsObserver
from task7_lower.training import rng_state,restore_rng,choose_candidate
from task9_lr.diagnostics import observing,digest
from task8_lower import evaluation as base
from task9_rllib import evaluation as adapted
p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--output',required=True);a=p.parse_args()
torch.set_num_threads(2)
torch.backends.cudnn.deterministic=True
torch.backends.cudnn.benchmark=False
sac,replay,env,state,cfg=load_smoke(a.checkpoint)
snapshot=torch.load(a.checkpoint,weights_only=False,map_location='cuda');other=restore_environment(snapshot['environment'],'cuda')
saved=rng_state();choose_candidate(env);restore_rng(saved);choose_candidate(other)
obs=env.core.current_observation();action=sac.select_action(obs,True)
observer=MetricsObserver();observer.attach(env,[{}]*env.batch)
saved=rng_state()
with observing(observer):tr=env.step(action).transition
observer.close();restore_rng(saved);other_tr=other.step(action).transition
for k in tr.next_observation:assert torch.equal(tr.next_observation[k],other_tr.next_observation[k]),k
assert torch.equal(tr.reward,other_tr.reward) and torch.equal(tr.done,other_tr.done)
assert observer.ik_timing and all('cuda_ms' in r for r in observer.ik_timing)
# Use the first two frozen DEVELOPMENT records per domain; keep every row identity.
# No admission.test_jobs/final manifest is accessed.
def plan(*args,**kwargs):
 val,semantic=base.evaluation_plan(*args,**kwargs)
 return val[:2],semantic[:2]
underlying=base.evaluate.__wrapped__
g=dict(underlying.__globals__);g['evaluation_plan']=plan
small=types.FunctionType(underlying.__code__,g,underlying.__name__,underlying.__defaults__,underlying.__closure__);small.__kwdefaults__=underlying.__kwdefaults__
small=torch.no_grad()(small)
g=dict(adapted.evaluate.__globals__);g['original_evaluate']=small
run=types.FunctionType(adapted.evaluate.__code__,g,adapted.evaluate.__name__,adapted.evaluate.__defaults__,adapted.evaluate.__closure__);run.__kwdefaults__=adapted.evaluate.__kwdefaults__
result=run(sac,cfg,a.output)
assert result['complete'] and result['validation']['episodes']==2 and result['transfer']['episodes']==2
for domain in ('validation','transfer'):
 for row in result[domain]['rows']:
  assert row['ik_residual']['semantics']=='post_acceptance_hold_execution' and row['ik_residual_raw_returned']['semantics']=='solver returned residual before acceptance hold'
  assert not (row['no_rejection_stall'] and row['original_success'])
  assert 'original_success' in row and 'first_rejection' in row and 'no_rejection_stall' in row and 'rejection_action_counts' in row
  assert row['strict_success']==(row['original_success'] and row['failures']==0)
result['observer_action_next_observation_exact_parity']=True;result['engineering_evaluation_episodes']=4
Path(a.output).write_text(json.dumps(result,indent=2));print(json.dumps({'status':'PASS','arm':cfg['group'],'episodes':4,'observer_parity':True,'wall_s':result['wall_s'],'IK_calls':len(result['observer']['ik_timing'])},indent=2))
if hasattr(sac,'close'):sac.close()
