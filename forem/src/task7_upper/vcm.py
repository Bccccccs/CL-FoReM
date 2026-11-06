"""Concrete VCM and per-environment FIFO/GRU, task7.8 B; SRC-0503/0903.

Inputs are (NCHW grid, explicit observation vector), current world SE(2) pose,
integer decision step and previous-action/result features. Runtime memory is
not checkpoint state; reconstruct it from an episode prefix after loading.
"""
from collections import deque
from dataclasses import dataclass
import math
import torch
from torch import nn


class ObservationEncoder(nn.Module):
    def __init__(self, vector_dim):
        super().__init__()
        self.vector_dim = vector_dim
        self.cnn = nn.Sequential(nn.Conv2d(3, 16, 3, stride=2), nn.ReLU(),
                                 nn.Conv2d(16, 32, 3, stride=2), nn.ReLU(),
                                 nn.Conv2d(32, 32, 3, stride=2), nn.ReLU(), nn.Flatten())
        self.fusion = nn.Linear(32 * 15 * 15 + vector_dim, 128)

    def forward(self, observation):
        grid, vector = observation
        if grid.shape[1:] != (3, 128, 128) or vector.shape != (grid.shape[0], self.vector_dim):
            raise ValueError('Expected NCHW 3x128x128 grid and configured observation vector')
        return self.fusion(torch.cat((self.cnn(grid), vector), dim=-1))


class MemoryRetrieval(nn.Module):
    """One single-head postnorm block, adapted from SC²-WM CrossTransformerBlock.

    Its stored log scale is exponentiated (initial effective scale 10).
    Relative xy is the historical base origin in the current base frame.
    Both K and V use encoded memory, as in the reference query().
    """
    def __init__(self):
        super().__init__()
        self.q_proj, self.k_proj, self.v_proj = (nn.Linear(128, 128) for _ in range(3))
        self.attn_norm = nn.LayerNorm(128)
        self.ffn = nn.Sequential(nn.Linear(128, 512), nn.GELU(), nn.Linear(512, 128))
        self.ffn_norm = nn.LayerNorm(128)
        self.logit_scale = nn.Parameter(torch.tensor(math.log(10.)))
        self.time_decay = nn.Parameter(torch.tensor(.1))
        self.geometry = nn.Sequential(nn.Linear(5, 128), nn.LayerNorm(128))
        nn.init.zeros_(self.geometry[0].weight)
        nn.init.zeros_(self.geometry[0].bias)
        self.steps = nn.Embedding(5, 128)
        nn.init.zeros_(self.steps.weight)

    @staticmethod
    def relative_geometry(poses, current):
        delta = poses - current.unsqueeze(-2)
        c, s = current[..., 2].cos().unsqueeze(-1), current[..., 2].sin().unsqueeze(-1)
        x, y = c*delta[..., 0] + s*delta[..., 1], -s*delta[..., 0] + c*delta[..., 1]
        angle = delta[..., 2]
        return torch.stack((x, y, angle.sin(), angle.cos(), torch.linalg.vector_norm(delta[..., :2], dim=-1)), dim=-1)

    def forward_batch(self, v, features, poses, steps, valid, pose, step):
        delta = (step.unsqueeze(-1) - steps).clamp(0, 4)
        encoded = features + self.geometry(self.relative_geometry(poses, pose)) + self.steps(delta.long())
        q, k, value = self.q_proj(v), self.k_proj(encoded), self.v_proj(encoded)
        scores = (q.unsqueeze(-2)*k).sum(-1) / math.sqrt(128) * self.logit_scale.exp()
        scores = scores - self.time_decay.abs()*delta
        # Empty histories get a dummy valid token to keep softmax finite; bypass below.
        safe_valid = valid.clone()
        empty = ~valid.any(-1)
        safe_valid[:, 0] |= empty
        weights = scores.masked_fill(~safe_valid, -float('inf')).softmax(-1)
        x = self.attn_norm(v + (weights.unsqueeze(-1)*value).sum(-2))
        ctx = self.ffn_norm(x + self.ffn(x))
        return torch.where(empty.unsqueeze(-1), v, ctx)

    def forward(self, v, entries, pose, step):
        if not entries:
            return v
        return self.forward_batch(v[None], torch.stack([x.feature for x in entries])[None],
                                  torch.stack([x.pose for x in entries])[None],
                                  torch.stack([x.step for x in entries])[None],
                                  torch.ones(1, len(entries), dtype=torch.bool, device=v.device),
                                  pose[None], step[None])[0]


class MemoryGate(nn.Linear):
    """Returns gate logits; VCM applies sigmoid once."""
    def __init__(self):
        super().__init__(256, 128)
        nn.init.normal_(self.weight, std=1e-4)
        nn.init.constant_(self.bias, 2.)

    def forward(self, v, ctx):
        return super().forward(torch.cat((v, ctx), dim=-1))


@dataclass
class MemoryEntry:
    feature: torch.Tensor
    pose: torch.Tensor
    step: torch.Tensor


class VCM(nn.Module):
    def __init__(self, f_enc=None, retrieval=None, gate=None, *, vector_dim=None,
                 asynchronous=False, action_result_dim=None):
        super().__init__()
        if f_enc is None:
            if vector_dim is None:
                raise ValueError('Observation vector_dim must be explicit (depends on route layout)')
            f_enc = ObservationEncoder(vector_dim)
        self.f_enc = f_enc
        self.retrieval = MemoryRetrieval() if retrieval is None else retrieval
        self.gate = MemoryGate() if gate is None else gate
        self.action_result_dim = (24 if asynchronous else 23) if action_result_dim is None else action_result_dim
        self.gru = nn.GRUCell(128 + self.action_result_dim, 128)
        self.memory, self.hidden = {}, {}

    @staticmethod
    def previous_features(previous_world_pose, current_world_pose, result_v1, delta_s=None):
        """f_k v1 is supplied in its 19-field order; no result conversion is guessed.

        For the asynchronous variant, pass previous candidate delta_s in metres.
        No running statistics or implicit unit conversion is applied here.
        """
        if result_v1.shape[-1] != 19:
            raise ValueError('Previous execution result must use f_k v1 (19 fields)')
        relative = MemoryRetrieval.relative_geometry(previous_world_pose.unsqueeze(-2), current_world_pose)[..., 0, :4]
        parts = [relative]
        if delta_s is not None:
            parts.append(delta_s.unsqueeze(-1))
        return torch.cat((*parts, result_v1), dim=-1)

    def reset(self, env_ids=None):
        if env_ids is None:
            self.memory.clear(); self.hidden.clear()
        else:
            for env_id in env_ids:
                self.memory.pop(env_id, None); self.hidden.pop(env_id, None)

    def forward(self, observation, action_result, pose, step, env_ids, *, reset_ids=()):
        if len(set(env_ids)) != len(env_ids):
            raise ValueError('Duplicate environment IDs in one step')
        if action_result.shape != (len(env_ids), self.action_result_dim):
            raise ValueError('Incorrect previous-action/result width for this variant')
        self.reset(reset_ids)
        v = self.f_enc(observation)
        if v.shape != (len(env_ids), 128):
            raise ValueError('f_enc must return [environments, 128]')
        histories = [self.memory.get(env_id, ()) for env_id in env_ids]
        if isinstance(self.retrieval, MemoryRetrieval):
            features, poses, steps, valid = [], [], [], []
            for entries in histories:
                pad = 4-len(entries)
                features.append(torch.stack([x.feature for x in entries] + [torch.zeros_like(v[0])]*pad))
                poses.append(torch.stack([x.pose for x in entries] + [torch.zeros_like(pose[0])]*pad))
                steps.append(torch.stack([x.step for x in entries] + [torch.zeros_like(step[0])]*pad))
                valid.append([True]*len(entries) + [False]*pad)
            ctx = self.retrieval.forward_batch(v, torch.stack(features), torch.stack(poses), torch.stack(steps),
                                               torch.tensor(valid, device=v.device), pose, step)
        else:
            ctx = torch.stack([self.retrieval(v[i], entries, pose[i], step[i]) for i, entries in enumerate(histories)])
        alpha = torch.sigmoid(self.gate(v, ctx))
        calibrated = alpha*v + (1-alpha)*ctx
        if isinstance(self.retrieval, MemoryRetrieval):
            calibrated = torch.where(torch.tensor([not x for x in histories], device=v.device)[:, None], v, calibrated)
        previous = torch.stack([self.hidden.get(env_id, torch.zeros_like(v[i])) for i, env_id in enumerate(env_ids)])
        state = self.gru(torch.cat((calibrated, action_result), dim=-1), previous)
        for i, env_id in enumerate(env_ids):
            self.memory.setdefault(env_id, deque(maxlen=4)).append(MemoryEntry(calibrated[i], pose[i].clone(), step[i].clone()))
            self.hidden[env_id] = state[i]  # uncorrected recurrent state
        return state

    @torch.no_grad()
    def rebuild_prefix(self, sequence):
        sequence = list(sequence)
        self.reset({env_id for item in sequence for env_id in item['env_ids']})
        state = None
        for item in sequence:
            state = self(**item)
        return state
