"""Zero initialized gated residual, task7.10 U.1/U.4; SOURCES SRC-0501."""
import torch
from torch import nn


class BiasLayer(nn.Module):
    def __init__(self):
        super().__init__()
        self.gate = nn.Linear(256, 128)
        self.delta = nn.Linear(256, 128)
        for layer in (self.gate, self.delta):
            nn.init.zeros_(layer.weight)
            nn.init.zeros_(layer.bias)

    def forward(self, e, h):
        h = h.detach()
        g = torch.sigmoid(self.gate(torch.cat((e, h), dim=-1)))
        delta = self.delta(torch.cat((h, e), dim=-1))
        return e + g * delta
