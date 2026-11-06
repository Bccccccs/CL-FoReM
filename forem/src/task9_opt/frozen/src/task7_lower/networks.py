"""Independent actor/Q encoders, CBL MLP and distribution; SRC-0470.
New encoder (engineering choice for the authorized 128x128x3 input): three
stride-2 convs, 16/32/32 channels, flatten preserving spatial layout.
"""
import torch
from torch import nn
from torch.distributions import Normal


def init(m):
    if isinstance(m,nn.Linear):nn.init.xavier_uniform_(m.weight);nn.init.zeros_(m.bias)
    if isinstance(m,nn.Conv2d):nn.init.kaiming_normal_(m.weight,mode='fan_out',nonlinearity='relu');nn.init.zeros_(m.bias)

class MapEncoder(nn.Module):
    output_size=32*16*16
    def __init__(self):
        super().__init__();self.conv=nn.Sequential(nn.Conv2d(3,16,3,2,1),nn.ReLU(),nn.Conv2d(16,32,3,2,1),nn.ReLU(),nn.Conv2d(32,32,3,2,1),nn.ReLU())
    def forward(self,m):return self.conv(m.permute(0,3,1,2).contiguous(memory_format=torch.channels_last)).flatten(1)

def mlp(n):
    layers=[]
    for width in (512,512,256):layers.extend([nn.Linear(n,width),nn.ReLU()]);n=width
    return nn.Sequential(*layers)

class Actor(nn.Module):
    def __init__(self,vector_dim):
        super().__init__();self.encoder=MapEncoder();self.mlp=mlp(vector_dim+self.encoder.output_size)
        self.mean=nn.Linear(256,3);self.log_std=nn.Linear(256,3);self.apply(init)
    def params(self,m,v):
        x=self.mlp(torch.cat([v,self.encoder(m)],-1))
        return self.mean(x),self.log_std(x).clamp(-20,2)
    def sample(self,m,v):
        mean,std=self.params(m,v);dist=Normal(mean,std.exp());raw=dist.rsample();action=raw.tanh()
        # Same SB3 SquashedDiagGaussianDistribution correction (epsilon=1e-6).
        return action,dist.log_prob(raw).sum(-1)-torch.log(1-action.square()+1e-6).sum(-1)
    def predict(self,m,v,eval=False):
        return self.params(m,v)[0].tanh() if eval else self.sample(m,v)[0]

class Q(nn.Module):
    def __init__(self,vector_dim):
        super().__init__();self.encoder=MapEncoder();self.mlp=mlp(vector_dim+3+self.encoder.output_size);self.head=nn.Linear(256,1)
    def forward(self,m,v,a):return self.head(self.mlp(torch.cat([v,a,self.encoder(m)],-1)))

class TwinQ(nn.Module):
    def __init__(self,vector_dim):
        super().__init__();self.q1=Q(vector_dim);self.q2=Q(vector_dim);self.apply(init)
    def forward(self,m,v,a):return self.q1(m,v,a),self.q2(m,v,a)
