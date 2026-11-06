"""Explicit-action environment equality and pending/full-state disk recovery check."""
import argparse,copy,json,sys
from pathlib import Path
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
sys.path.insert(0,'/workspace/src')
from task9_lr.runtime import activate
activate()
import torch
from task9_rllib.training import load_checkpoint,restore_environment
from task7_lower.training import rng_state,restore_rng,choose_candidate
from task9_lr.diagnostics import digest
p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--output',required=True);a=p.parse_args()
torch.set_num_threads(2)
torch.backends.cudnn.deterministic=True
torch.backends.cudnn.benchmark=False
sac,replay,env,state,cfg=load_checkpoint(a.checkpoint,'cuda')
assert cfg['total_transfers']==3000000 and state['steps'] in (512,513)
pending=state['pending'];pending_sha=digest(pending)
queued=len(getattr(replay,'queued',[]))
if cfg['learner_stack']=='rllib':assert queued==state['steps']%10 and sac.algorithm._counters['num_env_steps_sampled']==state['steps']//10*10
# Independent serialized load gives an independent env state and preserved RNG.
saved_rng=rng_state()
snapshot=torch.load(a.checkpoint,weights_only=False,map_location='cuda')
other=restore_environment(snapshot['environment'],'cuda')
assert digest(snapshot['state']['pending'])==pending_sha
errors=[];compared=0
for index in range(3):
 restore_rng(saved_rng);choose_candidate(env);ref_rng=rng_state()
 restore_rng(saved_rng);choose_candidate(other)
 def rd(s):return digest({**s,'numpy':[s['numpy'][0],s['numpy'][1].tolist(),*s['numpy'][2:]]})
 assert rd(ref_rng)==rd(rng_state())
 obs=env.core.current_observation();other_obs=other.core.current_observation()
 for k in obs:assert torch.equal(obs[k],other_obs[k]),k
 deterministic=sac.select_action(obs,True)
 assert torch.equal(deterministic,sac.select_action(obs,True))
 # Explicit, identical sequence independent of policy stochasticity.
 action=torch.tensor([.15,-.1,.2],device='cuda').expand(env.batch,-1).clone()*(1-index*.2)
 restore_rng(ref_rng);tr=env.step(action).transition;after_rng=rng_state()
 restore_rng(ref_rng);other_tr=other.step(action).transition
 for name in ('raw_action','reward','mask','active','done','attempted','committed','reason','dt'):
  x,y=getattr(tr,name),getattr(other_tr,name)
  if x.is_floating_point():
   e=float((x-y).abs().max());assert torch.allclose(x,y,atol=1e-5,rtol=1e-5),(name,e);errors.append(e)
  else:assert torch.equal(x,y),name
  compared+=1
 for name in tr.next_observation:
  x,y=tr.next_observation[name],other_tr.next_observation[name]
  assert torch.allclose(x,y,atol=1e-5,rtol=1e-5),name;compared+=1
 for name in ('base','q','s'):assert torch.allclose(getattr(env.core.state,name),getattr(other.core.state,name),atol=1e-5,rtol=1e-5),name
 saved_rng=after_rng
report=dict(status='PASS',arm=cfg['group'],restored_consumed=state['steps'],restored_generated=state['env_actions'],updates=sac.update_count,pending=None if pending is None else {'cursor':pending['cursor'],'remaining':len(pending['ids'])-pending['cursor']},native_queued=queued,explicit_action_calls=3,batch=env.batch,compared_fields=compared,max_abs_error=max(errors),atol=1e-5,rtol=1e-5,deterministic_action_repeat_equal=True,policy_device=str(next(sac.policy.parameters()).device),replay_device=str(replay.map_s.device),pending_disk_digest_equal=True)
Path(a.output).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if hasattr(sac,'close'):sac.close()
