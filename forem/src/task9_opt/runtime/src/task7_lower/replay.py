"""D11 uint8 GPU ring; CBL uniform random.sample without replacement.
Height bytes are never bit-packed as binary. Full state preserves byte values.
"""
import random
import torch
from .observation import encode_grid,decode_grid,vector

class Replay:
    def __init__(self,capacity,vector_dim,seed,device):
        self.capacity=capacity;self.device=torch.device(device);self.rng=random.Random(seed);self.position=self.size=0
        self.map_s=torch.empty(capacity,128,128,3,dtype=torch.uint8,device=device);self.map_n=torch.empty_like(self.map_s)
        self.rob_s=torch.empty(capacity,vector_dim,device=device);self.rob_n=torch.empty_like(self.rob_s)
        self.act=torch.empty(capacity,3,device=device);self.rew=torch.empty(capacity,device=device);self.mask=torch.empty_like(self.rew)
    def __len__(self):return self.size
    def push(self,obs,action,reward,next_obs,mask):
        n=len(action)
        if n>self.capacity:raise ValueError('insertion larger than ring')
        ids=(torch.arange(n,device=self.device)+self.position)%self.capacity
        for key,value in dict(map_s=encode_grid(obs['grid']),map_n=encode_grid(next_obs['grid']),rob_s=vector(obs),rob_n=vector(next_obs),act=action,rew=reward,mask=mask).items():getattr(self,key)[ids]=value
        self.position=(self.position+n)%self.capacity;self.size=min(self.size+n,self.capacity)
    def sample_indices(self,batch_size):return self.rng.sample(range(self.size),batch_size)
    def gather(self,indices):
        ids=torch.as_tensor(indices,device=self.device,dtype=torch.long)
        return decode_grid(self.map_s[ids]),self.rob_s[ids],self.act[ids],self.rew[ids,None],decode_grid(self.map_n[ids]),self.rob_n[ids],self.mask[ids,None]
    def sample(self,batch_size):return self.gather(self.sample_indices(batch_size))
    def state_dict(self):
        return dict(capacity=self.capacity,position=self.position,size=self.size,rng=self.rng.getstate(),tensors={k:getattr(self,k)[:self.size].cpu().clone() for k in ('map_s','map_n','rob_s','rob_n','act','rew','mask')})
    def load_state_dict(self,s):
        if self.capacity!=s['capacity']:raise ValueError('replay capacity mismatch')
        for k,v in s['tensors'].items():getattr(self,k)[:s['size']]=v.to(self.device)
        self.position=s['position'];self.size=s['size'];self.rng.setstate(s['rng'])
