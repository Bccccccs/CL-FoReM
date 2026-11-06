"""Directed native loss/gradient/device/replay/target/RNG recovery evidence."""
import sys,json,copy,inspect,time,random
from pathlib import Path
import numpy as np
import torch
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
sys.path.insert(0,'/workspace/src')
from task9_lr.runtime import activate
activate()
torch.set_num_threads(2)
torch.backends.cudnn.deterministic=True
torch.backends.cudnn.benchmark=False
from task9_rllib.native import NativeSAC
from task9_rllib.replay import add_weights
from task8_lower.sac import LowerSAC
from task7_lower.training import rng_state,restore_rng
from ray.rllib.policy.sample_batch import SampleBatch
from ray.rllib.algorithms.sac.sac_torch_policy import actor_critic_loss
from ray.rllib.algorithms.dqn.dqn import calculate_rr_weights
from ray.rllib.utils.torch_utils import huber_loss
OUT=Path('/workspace/results/task9/task9.13-setup/native-final');OUT.mkdir(exist_ok=True,parents=True)
cfg=json.load(open('/workspace/config/task9/task9_11/C_seed4718.json'))
random.seed(4718);np.random.seed(4718);torch.manual_seed(4718);torch.cuda.manual_seed_all(4718)
sac=NativeSAC(74,'cuda',cfg); p=sac.native_policy; model=p.model
m=torch.zeros(4,128,128,3,device='cuda');v=torch.randn(4,74,device='cuda')*.01
a=torch.tensor([[.1,.2,-.2]]*4,device='cuda'); obs={'map':m.to(torch.uint8),'vector':v}
logits,_=model.get_action_model_outputs(obs);mean,logstd=sac.policy.params(m,v)
assert torch.equal(logits,torch.cat((mean,logstd),-1))
dist=p.dist_class(logits,model)
assert torch.allclose(dist.deterministic_sample(),mean.tanh(),atol=1e-6,rtol=1e-5)
expected=torch.distributions.Normal(mean,logstd.exp()).log_prob(torch.atanh(a)).sum(-1)-torch.log(1-a*a+1e-6).sum(-1)
logprob_error=float((expected-dist.logp(a)).abs().max());assert logprob_error<1e-5
batch=SampleBatch(obs=obs,new_obs=obs,actions=a,rewards=torch.tensor([.5,-.2,.1,.3],device='cuda'),terminateds=torch.tensor([False,True,False,True],device='cuda'),weights=torch.ones(4,device='cuda'))
p.config['_deterministic_loss']=True
losses=actor_critic_loss(p,model,p.dist_class,batch)
with torch.no_grad():
 pi=dist.deterministic_sample();logp=dist.logp(pi)[:,None]
 tq1,tq2=sac.critic_target(m,v,pi);q1,q2=sac.critic(m,v,a)
 target=batch['rewards']+.99*(~batch['terminateds'])*(torch.minimum(tq1,tq2)-sac.alpha*logp).squeeze(1)
 ref=[(sac.alpha*logp-torch.minimum(*sac.critic(m,v,pi))).mean(),huber_loss((q1.squeeze(1)-target).abs()).mean(),huber_loss((q2.squeeze(1)-target).abs()).mean(),-(sac.log_alpha*(logp+model.target_entropy).detach()).mean()]
errors=[float((x-y).abs()) for x,y in zip(losses,ref)]
assert max(errors)<1e-5,errors
native_grad=torch.autograd.grad(losses[1],next(model.q_net.net.parameters()),retain_graph=True)[0]
q1=model.q_net.net(m,v,a);reference_loss=huber_loss((q1.squeeze(1)-target).abs()).mean()
ref_grad=torch.autograd.grad(reference_loss,next(model.q_net.net.parameters()))[0]
assert torch.allclose(native_grad,ref_grad,atol=1e-6,rtol=1e-5)
p.config['_deterministic_loss']=False
# Run native sampling→insertion→uniform replay→75 real update/target operations.
raw={'map':np.zeros((10,128,128,3),np.uint8),'vector':np.zeros((10,74),np.float32)}
def learn(step):
 b=SampleBatch(obs=raw,new_obs=raw,actions=np.zeros((10,3),np.float32),rewards=np.linspace(-.1,.1,10,dtype=np.float32),terminateds=np.zeros(10,np.bool_),truncateds=np.zeros(10,np.bool_))
 sac.set_transfer(step);return sac.train_native_batch(b)
initial={n:x.detach().clone() for n,x in model.named_parameters()}
for step in range(10,1001,10):learn(step)
assert sac.update_count==75
assert sac.algorithm._counters['num_target_updates']==75
changed={prefix:any(not torch.equal(initial[n],x) for n,x in model.named_parameters() if n.startswith(prefix)) for prefix in ('action_model','q_net','twin_q_net','log_alpha')}
assert all(changed.values()),changed
saved={'sac':sac.full_state_dict(),'replay':sac.algorithm.local_replay_buffer.get_state(),'rng':rng_state()}
torch.save(saved,OUT/'synthetic-recovery.pt')
# Native replay indices and next loss/update must match after an actual disk round trip.
learn(1010);reference={n:x.detach().clone() for n,x in model.state_dict().items()};counters=dict(sac.algorithm._counters)
s=torch.load(OUT/'synthetic-recovery.pt',weights_only=False,map_location='cpu')
sac.load_full_state_dict(s['sac']);sac.algorithm.local_replay_buffer.set_state(s['replay']);restore_rng(s['rng']);learn(1010)
restore_error=max(float((reference[n]-x).abs().max()) for n,x in model.state_dict().items());assert restore_error==0.,restore_error
assert counters==dict(sac.algorithm._counters)
devices={str(x.device) for x in model.parameters()};assert devices=={'cuda:0'}
optimizer_devices=[{str(v.device) for st in opt.state.values() for k,v in st.items() if torch.is_tensor(v) and k!='step'} for opt in p._optimizers]
assert all(x=={'cuda:0'} for x in optimizer_devices)
report=dict(status='PASS',ray=__import__('ray').__version__,torch=torch.__version__,gymnasium=__import__('gymnasium').__version__,pyarrow=__import__('pyarrow').__version__,rr=calculate_rr_weights(sac.algorithm.config),logprob_abs_error=logprob_error,loss_abs_errors=errors,gradient_abs_error=float((native_grad-ref_grad).abs().max()),gradient_atol=1e-6,rtol=1e-5,model_changed=changed,smoke_transfers=1000,smoke_updates=75,next_update_restore_abs_error=restore_error,counters=counters,optimizer_devices=[sorted(x) for x in optimizer_devices],native_replay=type(sac.algorithm.local_replay_buffer).__module__,training_step_source=inspect.getfile(sac.algorithm.training_step),loss_source=inspect.getfile(actor_critic_loss))
(OUT/'native-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
sac.close()
