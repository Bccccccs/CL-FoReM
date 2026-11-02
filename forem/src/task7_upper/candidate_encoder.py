"""Candidate projection/Transformer, task7.10 U.1/U.5/U.7 and D20; SRC-0501.

Defaults follow SRC-0903; explicit options remain available for contract fixtures.
No slot embeddings or running normalization statistics.
"""
import torch
from torch import nn


class CandidateEncoder(nn.Module):
    def __init__(self, *, geometry_dim=6, dropout=0., activation="gelu", norm_first=False, layer_norm_eps=1e-12, bias=True):
        super().__init__()
        if geometry_dim not in (6, 7):
            raise ValueError('Candidate geometry must have 6 (sync) or 7 (async) fields')
        self.geometry_dim = geometry_dim
        self.geometry = nn.Sequential(nn.Linear(geometry_dim, 128), nn.LayerNorm(128, eps=layer_norm_eps))
        self.features = nn.Linear(19, 128)
        self.state_token = nn.Linear(128, 128)
        layer = nn.TransformerEncoderLayer(128, 4, dim_feedforward=256,
                                          dropout=dropout, activation=activation,
                                          layer_norm_eps=layer_norm_eps, batch_first=True,
                                          norm_first=norm_first, bias=bias)
        self.transformer = nn.TransformerEncoder(layer, num_layers=2, enable_nested_tensor=False)

    @staticmethod
    def normalize(geometry, features, reachable_radius=3.2):
        if geometry.shape[-1] not in (6, 7) or features.shape[-1] != 19:
            raise ValueError('Expected geometry6/7 and D20 f_k v1 (19 fields)')
        # Legacy compatibility argument; SRC-0903 fixes delta_s scale to 3.2 m.
        radius = torch.as_tensor(reachable_radius, dtype=features.dtype, device=features.device)
        if not torch.isfinite(radius).all() or (radius <= 0).any():
            raise ValueError('A positive fixed reachable radius is required')
        t_seg = features[..., 8]
        if not torch.isfinite(t_seg).all() or (t_seg <= 0).any():
            raise ValueError('Positive T_seg is required for valid candidates')
        g = geometry.clone()
        g[..., [0, 1, 4]] = g[..., [0, 1, 4]] / 3.2
        if g.shape[-1] == 7:
            g[..., 6] = g[..., 6] / 3.2  # target delta_s_k (metres), SRC-0903 item 8
        f = features.clone()
        f[..., 7] = features[..., 7] / t_seg
        f[..., 8] = torch.ones_like(t_seg)
        f[..., [9, 10, 13, 16, 18]] = f[..., [9, 10, 13, 16, 18]] / 3.2
        f[..., 12] = features[..., 12] / 3.2
        return g, f

    def forward(self, state, geometry, features, mask, *, reachable_radius=3.2):
        if geometry.shape[-1] != self.geometry_dim:
            raise ValueError(f'Expected geometry{self.geometry_dim} for this variant')
        if mask.dtype != torch.bool or mask.shape != geometry.shape[:-1]:
            raise ValueError('Boolean mask must match candidate dimensions')
        if not mask.any(dim=-1).all():
            raise ValueError('Every decision must contain a valid candidate')
        # Remove arbitrary/nonfinite padding BEFORE projection and attention.
        geometry = torch.where(mask.unsqueeze(-1), geometry, torch.zeros_like(geometry))
        features = torch.where(mask.unsqueeze(-1), features, torch.zeros_like(features))
        features = features.clone()
        features[..., 8] = torch.where(mask, features[..., 8], torch.ones_like(features[..., 8]))
        g, f = self.normalize(geometry, features, reachable_radius)
        u = self.geometry(g) + self.features(f)
        u = u.masked_fill(~mask.unsqueeze(-1), 0.)
        tokens = torch.cat((self.state_token(state).unsqueeze(-2), u), dim=-2)
        padding = torch.cat((torch.zeros_like(mask[..., :1]), ~mask), dim=-1)
        encoded = self.transformer(tokens, src_key_padding_mask=padding)
        return encoded[..., 0, :], encoded[..., 1:, :].masked_fill(~mask.unsqueeze(-1), 0.), u
