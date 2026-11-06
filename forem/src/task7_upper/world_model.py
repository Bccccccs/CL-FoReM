"""f_p and external fixed G3 affine coefficients, task7.11 W.1/2/5; SRC-0501."""
import torch
from torch import nn


class WorldModel(nn.Module):
    def __init__(self, *, random_frozen=False):
        super().__init__()
        self.core = nn.Sequential(nn.Linear(384, 256), nn.ReLU(), nn.Linear(256, 128))
        self.predictor = nn.Sequential(nn.Linear(128, 128), nn.GELU(), nn.Linear(128, 128))
        self.register_buffer('alignment_scale', torch.ones(128))
        self.register_buffer('alignment_shift', torch.zeros(128))
        self.random_frozen = random_frozen
        if random_frozen:
            super().requires_grad_(False)

    def requires_grad_(self, requires_grad=True):
        return super().requires_grad_(False if self.random_frozen else requires_grad)

    @torch.no_grad()
    def set_alignment(self, scale, shift):
        """Install task7.22's coefficients; no statistics fitting or epsilon policy here."""
        if not self.random_frozen:
            raise ValueError('Affine alignment is only defined for the G3 random model')
        for value in (scale, shift):
            if value.shape != (128,) or not torch.isfinite(value).all():
                raise ValueError('Expected finite 128 dimensional coefficients')
        self.alignment_scale.copy_(scale)
        self.alignment_shift.copy_(shift)

    def forward(self, context, e, u):
        context = context.unsqueeze(-2).expand_as(e)
        raw_h = self.core(torch.cat((context, e, u), dim=-1))
        prediction = self.predictor(raw_h)
        h = raw_h * self.alignment_scale + self.alignment_shift
        return h, prediction

    @staticmethod
    @torch.no_grad()
    def encode_target(f_enc, observation):
        return f_enc(observation).detach()
