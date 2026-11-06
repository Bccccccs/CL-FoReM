"""Arrival-only f_p supervision and fixed G3 alignment; W.2–5, SRC-0510."""
import math
import random
import torch
from torch.nn import functional as F


def split_episodes(keys, seed):
    """Deterministic episode-level 10% split, rounded up; never split fragments."""
    keys = sorted(keys, key=repr)
    if len(keys) < 2:
        raise ValueError('at least two episodes required for disjoint holdout')
    random.Random(seed).shuffle(keys)
    n = math.ceil(.1*len(keys))
    return set(keys[n:]), set(keys[:n])


def prediction_diagnostics(prediction, target, selected, mask, arrived):
    rows = torch.arange(len(selected), device=selected.device)
    cosine = F.cosine_similarity(prediction, target[:, None], dim=-1)
    chosen = cosine[rows, selected]
    other = mask.clone(); other[rows, selected] = False
    comparable = arrived & other.any(-1)
    other_mean = cosine.masked_fill(~other, 0.).sum(-1)/other.sum(-1).clamp_min(1)
    count = mask.sum(-1).clamp_min(1)
    mean = prediction.masked_fill(~mask[..., None], 0.).sum(-2)/count[:, None]
    dispersion = ((prediction-mean[:, None]).square().mean(-1).masked_fill(~mask, 0.).sum(-1)/count)
    return dict(loss=(1-chosen)[arrived].detach(),
                chosen_minus_other=(chosen-other_mean)[comparable].detach(),
                dispersion=dispersion[arrived].detach(), comparable_count=int(comparable.sum()))


class FPTrainer:
    def __init__(self, model):
        if model.stage not in ('2', '3'):
            raise ValueError('f_p optimization requires stage 2 or 3')
        self.model = model
        self.optimizer = torch.optim.Adam(model.world_model.parameters(), lr=1e-4)
        self.updates = 0; self.best = math.inf; self.bad_epochs = 0

    def update(self, prediction, target, selected, arrived):
        if not arrived.any():
            return dict(loss=None, arrivals=0, updates=self.updates)
        rows = torch.arange(len(selected), device=selected.device)
        loss = (1-F.cosine_similarity(prediction[rows, selected], target.detach(), dim=-1))[arrived].mean()
        if not torch.isfinite(loss):
            raise FloatingPointError('nonfinite f_p loss')
        self.optimizer.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.world_model.parameters(), 10., error_if_nonfinite=True)
        self.optimizer.step(); self.updates += 1
        return dict(loss=float(loss.detach()), arrivals=int(arrived.sum()), updates=self.updates)

    def end_epoch(self, holdout_loss):
        if not math.isfinite(holdout_loss):
            raise FloatingPointError('nonfinite or empty holdout')
        if holdout_loss < self.best:
            self.best = holdout_loss; self.bad_epochs = 0
        else:
            self.bad_epochs += 1
        return self.bad_epochs >= 5

    def state_dict(self):
        return dict(optimizer=self.optimizer.state_dict(), updates=self.updates,
                    best=self.best, bad_epochs=self.bad_epochs)

    def load_state_dict(self, state):
        self.optimizer.load_state_dict(state['optimizer'])
        self.updates, self.best, self.bad_epochs = (state[k] for k in ('updates','best','bad_epochs'))


@torch.no_grad()
def fit_g3_alignment(random_model, trained_h, random_h):
    if not random_model.random_frozen:
        raise ValueError('expected frozen random model')
    if getattr(random_model, '_alignment_fitted', False):
        raise RuntimeError('G3 alignment already fitted')
    if trained_h.shape != random_h.shape or trained_h.ndim != 2 or trained_h.shape[0] < 1:
        raise ValueError('matching holdout observations [samples,128] required')
    # Population moments over the explicitly supplied holdout population.
    sigma_random = random_h.std(0, unbiased=False)
    zero = sigma_random == 0
    scale = torch.where(zero, 0., trained_h.std(0, unbiased=False)/torch.where(zero, 1., sigma_random))
    shift = trained_h.mean(0)-scale*random_h.mean(0)
    random_model.set_alignment(scale, shift)
    random_model._alignment_fitted = True
    return scale.clone(), shift.clone()


def arrival_samples(replay, keys):
    """One unique arrived decision per full length-8 prefix ending there.

    The first four positions burn in; three intermediate suffix states rebuild
    recurrence without labels. Only the final decision is this sample's label.
    Early episode decisions without a complete eight-step window are counted
    explicitly, never padded or joined across episodes.
    """
    samples=[];omitted=0
    for key,seq in replay.episodes.items():
        if key not in keys:continue
        for t,row in enumerate(seq):
            if not bool(row['arrival_label_valid']):continue
            if t<7:omitted+=1;continue
            samples.append((key,t-7))
    return samples,omitted


def materialize_samples(replay, samples):
    from copy import copy
    fragments=[]
    for key,start in samples:
        fragment=[]
        for offset,row in enumerate(replay.episodes[key][start:start+8]):
            x=copy(row)
            x['arrival_label_valid']=row['arrival_label_valid'] & (offset==7)
            fragment.append(x)
        fragments.append(fragment)
    return fragments


def fp_arrival_batch(model, fragments, adapter, trainer=None):
    """Latest user batch256 protocol; remainder batch visits each sample once."""
    from .stages import sequence_outputs,concatenate
    current,_,target=sequence_outputs(model,fragments,adapter,gradients=trainer is not None)
    out=concatenate(current)
    rows=[seq[t] for t in range(4,8) for seq in fragments]
    device=next(model.parameters()).device
    selected=torch.stack([r['selected'] for r in rows]).to(device)
    arrived=torch.stack([r['arrival_label_valid'] for r in rows]).to(device)
    mask=torch.stack([r['candidates']['mask'] for r in rows]).to(device)
    diag=prediction_diagnostics(out['prediction'].detach(),target,selected,mask,arrived)
    diag['new_observed_cells']=torch.stack([r['new_observed_cells'] for r in rows]).to(device)[arrived]
    result=None if trainer is None else trainer.update(out['prediction'],target,selected,arrived)
    if not torch.isfinite(diag['loss']).all():raise FloatingPointError('nonfinite holdout')
    if trainer is None:
        h,unused=model.random_world_model(out['context'],out['e'],out['u'])
        # G3 statistics use every valid candidate at the holdout states.
        valid=mask&arrived[:,None]
        diag['trained_h']=out['h'][valid].detach();diag['random_h']=h[valid].detach()
    model.vcm.reset()
    return result,diag


def split_arrival_episodes(replay, seed):
    """Split the supervised f_p dataset, not episodes without any usable label.

    W.3's dataset consists of arrival samples. Filter by label/prefix validity
    before the seeded episode-level 10% split; no loss/value-based selection.
    """
    samples,_=arrival_samples(replay,set(replay.episodes))
    eligible={key for key,start in samples}
    return split_episodes(eligible,seed)
