"""Independent Actor/twin Q heads, task7.10 U.2/U.7; SRC-0501."""
import torch
from torch import nn


class Heads(nn.Module):
    def __init__(self, *, critic_activation=nn.ReLU):
        super().__init__()
        self.actor = nn.Sequential(nn.Linear(128, 128), nn.ReLU(),
                                   nn.LayerNorm(128), nn.Linear(128, 1))
        self.q1 = self._critic(critic_activation)
        self.q2 = self._critic(critic_activation)

    @staticmethod
    def _critic(activation):
        return nn.Sequential(nn.Linear(256, 256), activation(), nn.Linear(256, 256),
                             activation(), nn.Linear(256, 1))

    def copy_from(self, other):
        self.load_state_dict(other.state_dict())

    def forward(self, state, candidates, *, actor_candidates=None):
        expanded = state.unsqueeze(-2).expand_as(candidates)
        q_input = torch.cat((expanded, candidates), dim=-1)
        actor_input = candidates if actor_candidates is None else actor_candidates
        return (self.actor(actor_input).squeeze(-1),
                self.q1(q_input).squeeze(-1), self.q2(q_input).squeeze(-1))
