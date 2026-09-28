"""STAGE0-028 R0-4b (D49): compare online-adaptation mechanisms against the frozen/copy controls
already used by R0-4's residual_probe.py, reporting the fraction of the frozen-residual mismatch
gap each mechanism actually recovers - not just statistical significance.

Lives outside scripts/wm/ for the same reason as residual_probe.py (see its docstring): any new
file inside scripts/wm/ permanently fails wm/cache.py:code_identity() against checkpoints trained
before the file existed.

Three treatments, all predict-then-update (a step's prediction always uses the model/correction
state from *before* that step's own transition is folded in) and reset every episode (D11):
  - V1 full_update: reference from R0-4, all MLPDynamics parameters, Adam(lr), every k steps.
      Reuses residual_probe.episode_errors as-is.
  - V2 output_update: identical loop, but the optimizer only ever touches the final Linear
      layer (model.net[-1], weight+bias) - the rest of the network is frozen.
  - V3 residual_ema: no gradient ever touches the model. Maintains an exponential moving average
      of the actual prediction residual (standardized feature space) and adds it to each new
      prediction; ema is updated from the residual *observed at* step t only after step t's own
      (pre-update) prediction has been scored. block='robot' restricts the correction to the
      robot-state dims (ROBOT_DIM=41), leaving the CNN map features exactly as the frozen model
      predicts them.
"""
import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

from wm.data import EpisodeDataset, ROBOT_DIM, file_sha256
from wm.dynamics import MLPDynamics
from wm.encoder import FixedEncoder
from wm.losses import block_mse
from wm.cache import build_cache, validate_feature_identity
from wm.evaluate_prediction import bootstrap_ci
from residual_probe import load_model, episode_errors, episode_mean, paired_summary


def episode_errors_output_update(base_model, feats, ds, i, norm, device, lr, k):
    """V2: episode_errors' predict-then-update loop, but Adam only ever steps model.net[-1]."""
    n = int(ds.n_valid[i])
    if n < 1:
        return []
    o0, a0 = int(ds.obs_offset[i]), int(ds.act_offset[i])
    z = norm(torch.as_tensor(feats[np.arange(o0, o0 + n + 1)], dtype=torch.float32, device=device))
    actions = torch.as_tensor(ds.action[a0:a0 + n], dtype=torch.float32, device=device)
    dts = torch.as_tensor(ds.dt[a0:a0 + n], dtype=torch.float32, device=device)
    model = copy.deepcopy(base_model).to(device)
    opt = torch.optim.Adam(model.net[-1].parameters(), lr=lr)
    rows, pending = [], []
    for t in range(n):
        model.eval()
        with torch.no_grad():
            pred = model(z[t:t + 1], actions[t:t + 1], dts[t:t + 1])
        total, robot, maps = block_mse(pred, z[t + 1:t + 2], reduce=False)
        rows.append(dict(step=t, total=float(total.item()), robot=float(robot.item()), maps=float(maps.item())))
        pending.append(t)
        if len(pending) == k:
            model.train()
            ix = torch.as_tensor(pending, dtype=torch.long, device=device)
            loss = block_mse(model(z[ix], actions[ix], dts[ix]), z[ix + 1])[0]
            opt.zero_grad()
            loss.backward()
            opt.step()
            pending = []
    return rows


def episode_errors_residual_ema(base_model, feats, ds, i, norm, device, alpha, block='total'):
    """V3: frozen weights throughout (no optimizer, no backward pass). ema starts at zero every
    episode (D11 reset); mask restricts the correction to the robot-state block when block='robot'."""
    n = int(ds.n_valid[i])
    if n < 1:
        return []
    o0, a0 = int(ds.obs_offset[i]), int(ds.act_offset[i])
    z = norm(torch.as_tensor(feats[np.arange(o0, o0 + n + 1)], dtype=torch.float32, device=device))
    actions = torch.as_tensor(ds.action[a0:a0 + n], dtype=torch.float32, device=device)
    dts = torch.as_tensor(ds.dt[a0:a0 + n], dtype=torch.float32, device=device)
    dim = z.shape[-1]
    mask = torch.zeros(dim, device=device)
    mask[:ROBOT_DIM] = 1.0
    if block != 'robot':
        mask[:] = 1.0
    ema = torch.zeros(dim, device=device)
    rows = []
    base_model.eval()
    with torch.no_grad():
        for t in range(n):
            raw_pred = base_model(z[t:t + 1], actions[t:t + 1], dts[t:t + 1])
            corrected = raw_pred + (ema * mask).unsqueeze(0)
            total, robot, maps = block_mse(corrected, z[t + 1:t + 2], reduce=False)
            rows.append(dict(step=t, total=float(total.item()), robot=float(robot.item()), maps=float(maps.item())))
            residual = (z[t + 1] - raw_pred[0]).detach()
            ema = (1 - alpha) * ema + alpha * residual
    return rows


def encode_condition(dataset_path, split, encoder, cache_dir, encode_batch):
    ds = EpisodeDataset.from_manifest(dataset_path, split=split)
    feats = build_cache(ds, encoder, cache_dir, batch=encode_batch)
    return ds, feats


def variant_report(variant_fn, base_model, norm, ds, feats, device, episodes, seed, **kwargs):
    torch.manual_seed(seed)
    by_ep = {i: variant_fn(base_model, feats, ds, i, norm, device, **kwargs) for i in episodes}
    return by_ep


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--conditions', required=True,
                   help='comma-separated name:dataset_path:split, e.g. nominal:/path/dataset.json:cond')
    p.add_argument('--nominal', required=True, help='name (from --conditions) to use as the recovery-fraction baseline')
    p.add_argument('--model', required=True)
    p.add_argument('--encoder-checkpoint', required=True)
    p.add_argument('--cache-dir')
    p.add_argument('--encode-batch', type=int, default=128)
    p.add_argument('--output', required=True)
    p.add_argument('--device', default='cuda')
    p.add_argument('--v1-lr', type=float, default=1e-5)
    p.add_argument('--v1-k', type=int, default=1)
    p.add_argument('--v2-lrs', default='1e-3,1e-2,1e-1')
    p.add_argument('--v2-ks', default='1,5')
    p.add_argument('--v3-alphas', default='0.05,0.2,0.5')
    p.add_argument('--seed', type=int, default=0)
    a = p.parse_args()
    out = Path(a.output)
    if out.exists():
        raise SystemExit('output exists; R0-4b probe is one-shot')
    v2_lrs = [float(x) for x in a.v2_lrs.split(',')]
    v2_ks = [int(x) for x in a.v2_ks.split(',')]
    v3_alphas = [float(x) for x in a.v3_alphas.split(',')]

    encoder = FixedEncoder(a.encoder_checkpoint, a.device)
    model, norm, meta = load_model(a.model, a.device)
    if meta['encoder_sha256'] != encoder.checkpoint_sha256:
        raise SystemExit('encoder mismatch with trained model')
    if meta.get('window_semantics') != 'time-aligned-v2':
        raise SystemExit('legacy P1 checkpoint affected by D33; retrain before research evaluation')
    validate_feature_identity(meta, encoder, a.encode_batch)

    started = time.time()
    conditions = {}
    for entry in a.conditions.split(','):
        name, dataset_path, split = entry.split(':')
        conditions[name] = dataset_path, split
    if a.nominal not in conditions:
        raise SystemExit('--nominal must name one of --conditions')

    report = dict(nominal=a.nominal, conditions={})
    frozen_total = {}
    for name, (dataset_path, split) in conditions.items():
        ds, feats = encode_condition(dataset_path, split, encoder, a.cache_dir, a.encode_batch)
        episodes = list(range(len(ds.episodes)))
        frozen = variant_report(episode_errors, model, norm, ds, feats, a.device, episodes, a.seed, lr=None, k=None)
        copy_rows = variant_report(episode_errors, None, norm, ds, feats, a.device, episodes, a.seed)
        v1 = variant_report(episode_errors, model, norm, ds, feats, a.device, episodes, a.seed, lr=a.v1_lr, k=a.v1_k)
        variants = {'V1_full_lr%g_k%d' % (a.v1_lr, a.v1_k): (v1, a.v1_k)}
        for lr in v2_lrs:
            for k in v2_ks:
                key = 'V2_output_lr%g_k%d' % (lr, k)
                variants[key] = (variant_report(episode_errors_output_update, model, norm, ds, feats, a.device,
                                                episodes, a.seed, lr=lr, k=k), k)
        for alpha in v3_alphas:
            for block in ['total', 'robot']:
                key = 'V3_ema_a%g_%s' % (alpha, block)
                variants[key] = (variant_report(episode_errors_residual_ema, model, norm, ds, feats, a.device,
                                                episodes, a.seed, alpha=alpha, block=block), 0)

        frozen_mean = float(np.mean([episode_mean(frozen[i]) for i in episodes]))
        copy_mean = float(np.mean([episode_mean(copy_rows[i]) for i in episodes]))
        frozen_total[name] = frozen_mean
        cond = dict(episodes=len(episodes), frozen_mean=frozen_mean, copy_mean=copy_mean, variants={})
        for vname, (by_ep, min_step) in variants.items():
            variant_mean = float(np.mean([episode_mean(by_ep[i], 'total', min_step) for i in episodes]))
            diff = paired_summary(by_ep, frozen, episodes, ds.seeds, 'total', min_step)
            cond['variants'][vname] = dict(mean=variant_mean, variant_minus_frozen=diff)
        report['conditions'][name] = cond
        feats.close()
        print('CONDITION DONE', name, 'frozen=%.5f' % frozen_mean, 'seconds=%.1f' % (time.time() - started), flush=True)

    nominal_frozen = frozen_total[a.nominal]
    for name, cond in report['conditions'].items():
        gap = cond['frozen_mean'] - nominal_frozen
        cond['gap_vs_nominal'] = gap
        for vname, v in cond['variants'].items():
            recovered = -v['variant_minus_frozen']['mean']
            v['recovered'] = recovered
            v['recovery_fraction'] = (recovered / gap) if gap > 0 else None

    report['seconds'] = time.time() - started
    out.mkdir(parents=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(nominal=a.nominal, seconds=report['seconds']), indent=2))


if __name__ == '__main__':
    main()
