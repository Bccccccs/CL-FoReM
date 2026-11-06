"""One real generated batch, nonempty pending snapshot, and next-update equality."""
import argparse,json,sys,copy,time
from pathlib import Path
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
sys.path.insert(0,'/workspace/src')
from task9_lr.runtime import activate
activate()
import torch
from task9_rllib.training import load_checkpoint,save_checkpoint,consume_transition
from task7_lower.training import choose_candidate,rng_state,restore_rng,drain_history
from task9_lr.diagnostics import digest
p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--output',required=True);a=p.parse_args()
torch.set_num_threads(2)
torch.backends.cudnn.deterministic=True
torch.backends.cudnn.benchmark=False
from engineering_load import load_smoke
sac,replay,env,state,cfg=load_smoke(a.checkpoint)
original_steps=state['steps'];generated=0
if state['pending'] is None or state['pending']['cursor']==len(state['pending']['ids']):
 choose_candidate(env);raw=sac.select_action(env.core.current_observation(),False)
 tr=env.step(raw).transition;generated=int(tr.active.sum());state['env_actions']+=generated;state['action_calls']+=1
 state['pending']={'transition':tr,'ids':torch.where(tr.active)[0].tolist(),'cursor':0,'failed':(env.core.last_step_failure>0).clone()}
 drain_history(env.core)
 pending=state['pending'];i=pending['ids'][0]
 consume_transition(sac,replay,state,tr,i,cfg,pending['failed'])
# R513 already has255 unconsumed transitions and3 rows queued before native replay.
assert len(state['pending']['ids'])-state['pending']['cursor']>10
out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
start=time.monotonic();save_checkpoint(out/'pending.pt',sac,replay,env,state,cfg)
checkpoint_steps=state['steps'];cursor=state['pending']['cursor'];native_queued=len(getattr(replay,'queued',[]))
def collect_tensors(value,prefix=''):
 result={}
 if torch.is_tensor(value):result[prefix]=value.detach().cpu().clone()
 elif isinstance(value,dict):
  for k,v in value.items():result.update(collect_tensors(v,prefix+'/'+str(k)))
 elif isinstance(value,(list,tuple)):
  for k,v in enumerate(value):result.update(collect_tensors(v,prefix+'/'+str(k)))
 return result

def consume_ten(sac,replay,state):
 p=state['pending']
 for _ in range(10):
  i=p['ids'][p['cursor']];consume_transition(sac,replay,state,p['transition'],i,cfg,p['failed'])
 weights={'policy':sac.policy.state_dict(),'critic':sac.critic.state_dict(),'target':sac.critic_target.state_dict(),'optimizers':[o.state_dict() for o in (sac.native_policy._optimizers if hasattr(sac,'native_policy') else [sac.policy_optim,sac.critic_optim,sac.alpha_optim])],'updates':sac.update_count}
 return {'tensors':collect_tensors(weights),'weights':digest(weights),'cursor':p['cursor'],'steps':state['steps'],'replay':digest(replay.gather(list(range(min(16,len(replay)))))),'rng':rd(rng_state())}
def rd(s):return digest({**s,'numpy':[s['numpy'][0],s['numpy'][1].tolist(),*s['numpy'][2:]]})
reference=consume_ten(sac,replay,state)
# Explicitly release old learner/replay GPU tensors before restoring a second copy.
if hasattr(sac,'close'):sac.close()
del sac,replay,env,state;torch.cuda.empty_cache()
sac,replay,env,state,cfg=load_checkpoint(out/'pending.pt','cuda')
restored=consume_ten(sac,replay,state)
# Native policy get_state contains numpy arrays; weights digest uses helper below.
rt=reference.pop('tensors');st=restored.pop('tensors');assert rt.keys()==st.keys()
max_error=0.
for key in rt:
 x,y=rt[key],st[key]
 if x.is_floating_point():
  error=float((x-y).abs().max()) if x.numel() else 0.;max_error=max(max_error,error)
  assert torch.allclose(x,y,atol=1e-6,rtol=1e-5),(key,error)
 else:assert torch.equal(x,y),key
exact=reference['weights']==restored['weights']
reference.pop('weights');restored.pop('weights')
assert reference==restored,(reference,restored)
result={'status':'PASS','arm':cfg['group'],'initial_checkpoint_steps':original_steps,'engineering_generated_additional':generated,'engineering_consumed_additional':checkpoint_steps-original_steps+20,'saved_steps':checkpoint_steps,'saved_pending_cursor':cursor,'saved_pending_remaining':len(state['pending']['ids'])-cursor,'native_queued':native_queued,'next_consumed_transfers_each_branch':10,'exact_weights_equal':exact,'weights_optimizer_max_abs_error':max_error,'weights_atol':1e-6,'weights_rtol':1e-5,'next_update_weights_within_tolerance':True,'replay_rng_cursor_exact_equal':True,'wall_s':time.monotonic()-start}
(out/'pending-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if hasattr(sac,'close'):sac.close()
