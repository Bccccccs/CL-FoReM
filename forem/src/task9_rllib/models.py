"""FoReM network capacity and byte observation adapter; no SAC loss implementation."""
import gymnasium as gym
import torch
from ray.rllib.algorithms.sac.sac_torch_model import SACTorchModel
from ray.rllib.models.torch.torch_modelv2 import TorchModelV2
from task7_lower.networks import Actor, Q, init
from task7_lower.observation import decode_grid


class ActorModel(TorchModelV2, torch.nn.Module):
    def __init__(self, obs_space, action_space, name):
        torch.nn.Module.__init__(self)
        TorchModelV2.__init__(self, obs_space, action_space, 6, {}, name)
        self.net = Actor(74)
    def forward(self, inputs, state, seq_lens):
        obs=inputs['obs']; mean, logstd=self.net.params(decode_grid(obs['map']),obs['vector'].float())
        return torch.cat((mean,logstd),-1), state


class QModel(TorchModelV2, torch.nn.Module):
    def __init__(self, obs_space, action_space, name):
        torch.nn.Module.__init__(self)
        TorchModelV2.__init__(self,gym.spaces.Tuple((obs_space,action_space)),action_space,1,{},name)
        self.net=Q(74); self.net.apply(init)
    def forward(self, inputs, state, seq_lens):
        obs, action=inputs['obs']
        return self.net(decode_grid(obs['map']),obs['vector'].float(),action),state


class FoReMSACModel(SACTorchModel):
    def build_policy_model(self, obs_space, num_outputs, policy_model_config, name):
        return ActorModel(obs_space,self.action_space,name)
    def build_q_model(self, obs_space, action_space, num_outputs, q_model_config,name):
        self.concat_obs_and_actions=False
        return QModel(obs_space,action_space,name)
