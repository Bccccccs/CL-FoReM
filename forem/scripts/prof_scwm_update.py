import ray, sys, time
sys.path.insert(0,'/root/mm_husky_ws/scripts'); sys.path.insert(0,'/root/mm_husky_ws/src/modulation_rl/scripts')
import torch, numpy as np, gym
from scwm_sac import GpuReplay, ScwmSAC
from torch.profiler import profile, ProfilerActivity
obs = gym.spaces.Tuple([gym.spaces.Box(-100,100,(41,),dtype=np.float32), gym.spaces.Box(-1.1,10.1,(120,120,1),dtype=np.float32)])
act = gym.spaces.Box(-1.,1.,(3,),dtype=np.float32)
args = dict(gamma=.99,tau=.001,initial_alpha=1.,device='cuda:0',model=dict(custom_model_config=dict(post_fcnet_hiddens=[512,512,256])))
ag = ScwmSAC(obs,act,1,args,5000001); g = GpuReplay(3000,0,'cuda:0')
r=np.random.RandomState(0)
for i in range(3000):
    g.push((r.rand(120,120,1)>.93).astype(np.float32), r.randn(41).astype(np.float32), np.tanh(r.randn(3)).astype(np.float32), 0.1,(r.rand(120,120,1)>.93).astype(np.float32), r.randn(41).astype(np.float32),1.0,
           dict(episode_id=0,step_in_episode=0,epoch=0,t_obs=0.,t_cmd=0.,t_next=0.,done=False))
for k in range(20): ag.update_parameters(g,256,k)
torch.cuda.synchronize()
with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as p:
    for k in range(20): ag.update_parameters(g,256,k)
    torch.cuda.synchronize()
print(p.key_averages().table(sort_by="cuda_time_total", row_limit=12, max_name_column_width=50))
