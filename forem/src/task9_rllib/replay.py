"""Metadata/observation bridge around the unchanged native RLlib replay buffer."""
import numpy as np
import torch
from ray.rllib.policy.sample_batch import SampleBatch,DEFAULT_POLICY_ID,concat_samples
from task7_lower.observation import encode_grid,decode_grid,vector


def add_weights(batch,*args):
    for sub in batch.policy_batches.values():sub['weights']=np.ones(sub.count,np.float32)
    return batch

class NativeReplayView:
    def __init__(self,sac,capacity,device):
        self.sac=sac;self.capacity=capacity;self.device=torch.device(device)
        self.native=sac.algorithm.local_replay_buffer;self.queued=[];self.position=0;self.size=0
        # Native replay lives on CPU; only sampled learning batches move to GPU.
        self.map_s=torch.empty(0,dtype=torch.uint8)
        self.rew=torch.empty(capacity,device=device);self.failed=torch.empty(capacity,dtype=torch.bool,device=device)
        self.inserted_at=torch.empty(capacity,dtype=torch.long,device=device)
    def __len__(self):return self.size
    def push(self,obs,action,reward,next_obs,mask,*,transfer,failed):
        def pack(o):return {'map':encode_grid(o['grid']).cpu().numpy(),'vector':vector(o).cpu().numpy()}
        batch=SampleBatch({SampleBatch.OBS:pack(obs),SampleBatch.NEXT_OBS:pack(next_obs),
                           SampleBatch.ACTIONS:action.cpu().numpy(),SampleBatch.REWARDS:reward.cpu().numpy(),
                           SampleBatch.TERMINATEDS:(mask==0).cpu().numpy(),SampleBatch.TRUNCATEDS:np.zeros(1,np.bool_)})
        self.queued.append(batch)
        self.rew[self.position]=reward[0];self.failed[self.position]=failed[0];self.inserted_at[self.position]=transfer
        self.position=(self.position+1)%self.capacity;self.size=min(self.size+1,self.capacity)
        if len(self.queued)==10:
            batch=concat_samples(self.queued);self.queued=[]
            return self.sac.train_native_batch(batch)
        return None
    def gather(self,indices):
        buffer=self.native.replay_buffers[DEFAULT_POLICY_ID]
        batch=concat_samples([buffer._storage[i] for i in indices])
        def t(x):return torch.as_tensor(x,device=self.device)
        return (decode_grid(t(batch['obs']['map'])),t(batch['obs']['vector']),t(batch['actions']),
                t(batch['rewards'])[:,None],decode_grid(t(batch['new_obs']['map'])),t(batch['new_obs']['vector']),
                1-t(batch['terminateds']).float()[:,None])
    def state_dict(self):
        return dict(format='task9.13-native-replay-v1',capacity=self.capacity,position=self.position,size=self.size,
                    native=self.native.get_state(),queued=self.queued,
                    metadata={k:getattr(self,k)[:self.size].cpu() for k in ('rew','failed','inserted_at')})
    def load_state_dict(self,s):
        if s['capacity']!=self.capacity:raise ValueError('native replay capacity mismatch')
        self.native.set_state(s['native']);self.queued=s['queued'];self.position=s['position'];self.size=s['size']
        for k,v in s['metadata'].items():getattr(self,k)[:self.size]=v.to(self.device)
