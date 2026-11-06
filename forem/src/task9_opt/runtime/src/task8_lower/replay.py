"""Unchanged replay data and sampling with diagnostic-only failure/age metadata."""
import torch
from task7_lower.replay import Replay as V5Replay


class Replay(V5Replay):
    def __init__(self,capacity,vector_dim,seed,device):
        super().__init__(capacity,vector_dim,seed,device)
        self.inserted_at=torch.empty(capacity,dtype=torch.long,device=device)
        self.failed=torch.empty(capacity,dtype=torch.bool,device=device)
    def push(self,obs,action,reward,next_obs,mask,*,transfer,failed):
        ids=(torch.arange(len(action),device=self.device)+self.position)%self.capacity
        self.inserted_at[ids]=transfer;self.failed[ids]=failed
        super().push(obs,action,reward,next_obs,mask)
    def state_dict(self):
        state=super().state_dict()
        state['diagnostic']={k:getattr(self,k)[:self.size].cpu().clone() for k in ('inserted_at','failed')}
        return state
    def load_state_dict(self,state):
        super().load_state_dict(state)
        for k,v in state['diagnostic'].items():getattr(self,k)[:self.size]=v.to(self.device)
