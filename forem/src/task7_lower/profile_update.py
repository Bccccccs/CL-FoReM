import json,time,torch
from .sac import LowerSAC
from .replay import Replay
from .tests.test_lower import obs

def main():
 torch.set_num_threads(2);torch.manual_seed(47);s=LowerSAC(74,'cuda');r=Replay(300,74,47,'cuda');o=obs(300,device='cuda');r.push(o,torch.zeros(300,3,device='cuda'),torch.zeros(300,device='cuda'),o,torch.ones(300,device='cuda'))
 times=[]
 for i in range(15):
  torch.cuda.synchronize();t=time.perf_counter();s.update_from_batch(r.sample(256),i);torch.cuda.synchronize();times.append(time.perf_counter()-t)
 print(json.dumps(dict(update_wall_s=times,policy_device=str(next(s.policy.parameters()).device),optimizer_devices=sorted(set(str(v.device) for state in s.policy_optim.state.values() for v in state.values() if torch.is_tensor(v))),peak_bytes=torch.cuda.max_memory_allocated())))
if __name__=='__main__':main()
