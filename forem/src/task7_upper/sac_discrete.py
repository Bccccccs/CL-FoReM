"""Masked semi-Markov discrete SAC; task7.10 U.3/4/6, SRC-0510.

The caller supplies recurrent outputs from exact replay, not stored latents.
Targets require online next policy and target next Q from separate recurrences.
"""
from copy import deepcopy
import math
import torch
from torch import nn


def distribution(logits, mask):
    if mask.dtype != torch.bool or not mask.any(-1).all():
        raise ValueError('nonempty Boolean candidate mask required')
    if not torch.isfinite(logits[mask]).all():
        raise FloatingPointError('nonfinite valid logits')
    logp = logits.masked_fill(~mask, -torch.inf).log_softmax(-1)
    return logp.exp(), logp.masked_fill(~mask, 0.)


def bellman(reward, terminated, dt, next_logits, next_q1, next_q2, next_mask, alpha):
    p, logp = distribution(next_logits, next_mask)
    q = torch.minimum(next_q1, next_q2).masked_fill(~next_mask, 0.)
    value = (p * (q - alpha * logp)).sum(-1)
    return reward + (~terminated).to(reward.dtype) * (.99 ** (dt/.1)) * value


class CappedTemperature:
    def __init__(self, device, log_alpha=0., fixed=False):
        self.log_alpha = nn.Parameter(torch.tensor(float(log_alpha), device=device))
        self.optimizer = torch.optim.Adam([self.log_alpha], lr=1e-6)
        self.fixed = bool(fixed)

    @property
    def alpha(self):
        return self.log_alpha.new_tensor(.05) if self.fixed else .35*self.log_alpha.detach().exp()

    def update(self, p, logp, mask):
        if self.fixed:
            return 0.
        target = .98*mask.sum(-1).to(p.dtype).log()
        loss = -self.log_alpha*(p*(logp+target[:, None])).sum(-1).detach().mean()
        if not torch.isfinite(loss):
            raise FloatingPointError('nonfinite temperature loss')
        self.optimizer.zero_grad(); loss.backward(); self.optimizer.step()
        if self.alpha <= .05:
            self.fixed = True
        return float(loss.detach())

    def state_dict(self):
        return dict(log_alpha=self.log_alpha.detach().clone(), fixed=self.fixed,
                    optimizer=self.optimizer.state_dict())

    def load_state_dict(self, state):
        with torch.no_grad():
            self.log_alpha.copy_(state['log_alpha'])
        self.fixed = state['fixed']; self.optimizer.load_state_dict(state['optimizer'])


class DiscreteSAC:
    def __init__(self, model, total_updates, temperature=None):
        if model.stage not in ('1', '3', 'G2', 'G3') or total_updates <= 0:
            raise ValueError('RL stage and positive schedule length required')
        self.model, self.total_updates = model, int(total_updates)
        self.target = deepcopy(model).requires_grad_(False).eval()
        self.temperature = temperature or CappedTemperature(next(model.parameters()).device)
        # Shared psi receives both RL losses in one backward/optimizer step.
        # World-model loss has its own optimizer and cannot enter this one.
        params = [p for name, group in model.trainable_parameters().items()
                  if name != 'world_model' for p in group]
        self.optimizer = torch.optim.Adam(params, lr=1e-4)
        self.scheduler = torch.optim.lr_scheduler.LambdaLR(
            self.optimizer, lambda n: (.01)**(min(n, self.total_updates)/self.total_updates))
        self.updates = 0

    def update(self, current, next_online, next_target, batch):
        alpha = self.temperature.alpha
        with torch.no_grad():
            y = bellman(batch['reward'], batch['terminated'], batch['dt'],
                        next_online['logits'], next_target['q1'], next_target['q2'],
                        batch['next_mask'], alpha)
        index = batch['selected'][:, None]
        qloss = .5*sum((current[k].gather(-1, index).squeeze(-1)-y).square().mean()
                       for k in ('q1', 'q2'))
        p, logp = distribution(current['logits'], batch['mask'])
        aq = torch.minimum(current['actor_q1'], current['actor_q2']).masked_fill(~batch['mask'], 0.)
        actor = (p*(alpha*logp-aq)).sum(-1).mean()
        loss = qloss+actor
        if not torch.isfinite(loss):
            raise FloatingPointError('nonfinite RL loss; stop without changing parameters')
        self.optimizer.zero_grad(); loss.backward()
        parameters = [p for g in self.optimizer.param_groups for p in g['params']]
        norm = nn.utils.clip_grad_norm_(parameters, 10., error_if_nonfinite=True)
        self.optimizer.step(); self.scheduler.step()
        temperature_loss = self.temperature.update(p.detach(), logp.detach(), batch['mask'])
        with torch.no_grad():
            online = dict(self.model.named_parameters())
            for name, target in self.target.named_parameters():
                if online[name].requires_grad and not name.startswith('world_model.'):
                    target.lerp_(online[name], .001)
                else:
                    target.copy_(online[name])
        self.updates += 1
        return dict(critic=float(qloss.detach()), actor=float(actor.detach()),
                    temperature_loss=temperature_loss, alpha=float(self.temperature.alpha),
                    gradient_norm=float(norm), updates=self.updates)

    def state_dict(self):
        return dict(model=self.model.state_dict(), target=self.target.state_dict(),
                    optimizer=self.optimizer.state_dict(), scheduler=self.scheduler.state_dict(),
                    temperature=self.temperature.state_dict(), updates=self.updates,
                    stage=self.model.stage, total_updates=self.total_updates)

    def load_state_dict(self, state):
        if state['stage'] != self.model.stage or state['total_updates'] != self.total_updates:
            raise ValueError('resume stage/schedule mismatch')
        self.model.load_state_dict(state['model']); self.target.load_state_dict(state['target'])
        self.optimizer.load_state_dict(state['optimizer']); self.scheduler.load_state_dict(state['scheduler'])
        self.temperature.load_state_dict(state['temperature']); self.updates = state['updates']
