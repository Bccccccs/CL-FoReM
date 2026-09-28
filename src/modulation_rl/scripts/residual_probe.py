"""STAGE0-028 R0-4: offline online-update residual probe.

Replays a stochastically-collected, single-condition episode batch (one mismatch config; see
doc/agent_logs/20260928-stage0-r04-collect.sh) through the trained action-conditioned world
model, three ways per episode:
  - frozen:  the trained weights, never updated.
  - copy:    the copy-model baseline (h_{t+1} := h_t), no learned weights at all.
  - updated: a private per-episode clone of the trained weights, predict-then-update online with
             Adam(lr), one gradient step every k steps using only the k transitions just scored.

Protocol (D45/ROADMAP §4 R0-4, LOGIC L1/L2): at every step t, the prediction at t always uses the
model state as of *before* transition t is incorporated into any update, so no reported error ever
comes from a model that has already been trained on the very transition it is scored on. Steps with
t < k for a given k use the still-un-updated clone (identical in expectation to frozen) and are
flagged post_warmup=False; only post_warmup=True steps (t >= k, i.e. at least one update already
applied) are used for the primary updated-vs-frozen comparison, per k. Everything resets per
episode (D11): a fresh optimizer and a fresh clone of the frozen weights every episode, no state
carried across episodes.

Reuses the same bounded FeatureCache/EpisodeDataset/WindowSource machinery as
train_offline.py/evaluate_prediction.py (build_cache, `EpisodeDataset.from_manifest`); nothing here
is a live SAC rollout, only a replay of already saved observations. A condition manifest tags every
episode with one split label (default 'cond', see --split) rather than a train/val/test partition;
this only reads wm/data.py's existing single-split filtering, unmodified.

Deliberately lives at scripts/residual_probe.py, not scripts/wm/residual_probe.py:
wm/cache.py:code_identity() globs every *.py file directly under scripts/wm/ and bakes that hash set
into every trained checkpoint; a new file inside that directory would permanently fail
validate_feature_identity() for every checkpoint trained before the file existed (not a transient
ordering issue - moving it back in would break this against the already-trained seed11/22/33
checkpoints forever, see the incident notes in agent_logs/20260928-stage0.md).
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

from wm.data import EpisodeDataset, file_sha256  # noqa: E402
from wm.dynamics import CopyModel, MLPDynamics, Normalizer  # noqa: E402
from wm.encoder import FixedEncoder  # noqa: E402
from wm.losses import block_mse  # noqa: E402
from wm.cache import build_cache, validate_feature_identity  # noqa: E402
from wm.evaluate_prediction import bootstrap_ci  # noqa: E402


def load_model(path, device):
    data = torch.load(path, map_location=device, weights_only=False)
    model = MLPDynamics(data['dim'], hidden=tuple(data.get('hidden', (256, 256))), use_action=data['use_action']).to(device)
    model.load_state_dict(data['state_dict'])
    norm = Normalizer(torch.zeros(data['dim']), torch.ones(data['dim'])).to(device)
    norm.load_state_dict(data['normalizer'])
    return model.eval(), norm, data


@torch.no_grad()
def _predict(model, z_t, a_t, dt_t):
    model.eval()
    return model(z_t, a_t, dt_t)


def episode_errors(base_model, feats, ds, i, norm, device, lr=None, k=None):
    """Predict-then-update replay of one episode.

    base_model=None selects the copy-model control (ignores lr/k). Otherwise a fresh deep copy of
    base_model is made (frozen weights never mutated); lr=None makes that copy a frozen control
    (no optimizer, no update, ever); lr set makes it the online-updated treatment with an Adam
    step every k steps. Returns a list of per-step dicts; never mutates base_model or feats.
    """
    n = int(ds.n_valid[i])
    if n < 1:
        return []
    o0, a0 = int(ds.obs_offset[i]), int(ds.act_offset[i])
    # feats is a FeatureCache; its __getitem__ takes an explicit index array (see WindowSource.take
    # in wm/train_offline.py), not a Python slice - a plain feats[o0:o0+n+1] raises inside
    # np.asarray(slice, dtype=int64).
    z = norm(torch.as_tensor(feats[np.arange(o0, o0 + n + 1)], dtype=torch.float32, device=device))
    actions = torch.as_tensor(ds.action[a0:a0 + n], dtype=torch.float32, device=device)
    dts = torch.as_tensor(ds.dt[a0:a0 + n], dtype=torch.float32, device=device)
    if base_model is None:
        model, opt = CopyModel().to(device), None
    else:
        model = copy.deepcopy(base_model).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=lr) if lr is not None else None
    rows, pending = [], []
    for t in range(n):
        pred = _predict(model, z[t:t + 1], actions[t:t + 1], dts[t:t + 1])
        total, robot, maps = block_mse(pred, z[t + 1:t + 2], reduce=False)
        rows.append(dict(step=t, total=float(total.item()), robot=float(robot.item()), maps=float(maps.item()),
                          post_warmup=bool(opt is not None and k is not None and t >= k)))
        if opt is not None:
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


def episode_mean(rows, key='total', min_step=None):
    """min_step=k restricts to steps t>=k (comparable across treatments by step index). Do not
    filter by a row's own 'post_warmup' flag here: that flag is only ever True for the updated
    treatment (opt is not None); frozen/copy rows always carry post_warmup=False by construction,
    so filtering on it would silently empty out every frozen/copy episode."""
    values = [r[key] for r in rows if (min_step is None or r['step'] >= min_step)]
    return float(np.mean(values)) if values else float('nan')


def run_condition(model, norm, ds, feats, device, lrs, ks, seed):
    """All per-episode replays for one condition. Frozen/copy are computed once and reused across
    every (lr, k); only the updated treatment depends on (lr, k)."""
    torch.manual_seed(seed)
    episodes = list(range(len(ds.episodes)))
    frozen = {i: episode_errors(model, feats, ds, i, norm, device, lr=None, k=None) for i in episodes}
    copy_rows = {i: episode_errors(None, feats, ds, i, norm, device) for i in episodes}
    updated = {}
    for lr in lrs:
        for k in ks:
            updated[(lr, k)] = {i: episode_errors(model, feats, ds, i, norm, device, lr=lr, k=k) for i in episodes}
    return frozen, copy_rows, updated


def paired_summary(a_by_ep, b_by_ep, episodes, seeds, key='total', min_step=None):
    """Per-episode mean(a) - mean(b), paired by episode index (already seed-aligned by caller),
    then an episode-level bootstrap CI matching evaluate_prediction.py's bootstrap_ci."""
    diffs = []
    for i in episodes:
        am = episode_mean(a_by_ep[i], key, min_step)
        bm = episode_mean(b_by_ep[i], key, min_step)
        if np.isfinite(am) and np.isfinite(bm):
            diffs.append(am - bm)
    diffs = np.asarray(diffs)
    return dict(mean=float(diffs.mean()) if len(diffs) else float('nan'), ci95=bootstrap_ci(diffs),
                episodes=int(len(diffs)), a_better_fraction=float((diffs < 0).mean()) if len(diffs) else float('nan'))


def condition_report(model, norm, ds, feats, device, lrs, ks, seed):
    frozen, copy_rows, updated = run_condition(model, norm, ds, feats, device, lrs, ks, seed)
    episodes = list(range(len(ds.episodes)))
    report = dict(episodes=len(episodes), seeds=ds.seeds.tolist(),
                  frozen_mean=dict(total=float(np.mean([episode_mean(frozen[i]) for i in episodes])),
                                   robot=float(np.mean([episode_mean(frozen[i], 'robot') for i in episodes])),
                                   maps=float(np.mean([episode_mean(frozen[i], 'maps') for i in episodes]))),
                  copy_mean=dict(total=float(np.mean([episode_mean(copy_rows[i]) for i in episodes])),
                                 robot=float(np.mean([episode_mean(copy_rows[i], 'robot') for i in episodes])),
                                 maps=float(np.mean([episode_mean(copy_rows[i], 'maps') for i in episodes]))),
                  updated={})
    for (lr, k), by_ep in updated.items():
        key = '%.0e_k%d' % (lr, k)
        report['updated'][key] = dict(
            lr=lr, k=k,
            mean_post_warmup=dict(total=float(np.mean([episode_mean(by_ep[i], 'total', k) for i in episodes])),
                                  robot=float(np.mean([episode_mean(by_ep[i], 'robot', k) for i in episodes])),
                                  maps=float(np.mean([episode_mean(by_ep[i], 'maps', k) for i in episodes]))),
            updated_minus_frozen_post_warmup=paired_summary(by_ep, frozen, episodes, ds.seeds, 'total', k),
            updated_minus_frozen_post_warmup_robot=paired_summary(by_ep, frozen, episodes, ds.seeds, 'robot', k),
            updated_minus_frozen_post_warmup_map=paired_summary(by_ep, frozen, episodes, ds.seeds, 'maps', k))
    return report, frozen


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True, help='single-condition manifest (all episodes share one split label)')
    p.add_argument('--split', default='cond', help='split label every episode in --dataset was tagged with')
    p.add_argument('--condition', required=True, help='free-text label, e.g. gain0.6_delay0')
    p.add_argument('--model', required=True, help='trained action.pt from train_offline.py')
    p.add_argument('--encoder-checkpoint', required=True)
    p.add_argument('--cache-dir')
    p.add_argument('--encode-batch', type=int, default=128)
    p.add_argument('--output', required=True)
    p.add_argument('--device', default='cuda')
    p.add_argument('--lrs', default='1e-5,1e-4,1e-3')
    p.add_argument('--ks', default='1,5')
    p.add_argument('--seed', type=int, default=0)
    a = p.parse_args()
    out = Path(a.output)
    if out.exists():
        raise SystemExit('output exists; R0-4 probe is one-shot per condition')
    lrs = [float(x) for x in a.lrs.split(',')]
    ks = [int(x) for x in a.ks.split(',')]
    encoder = FixedEncoder(a.encoder_checkpoint, a.device)
    model, norm, meta = load_model(a.model, a.device)
    if meta['encoder_sha256'] != encoder.checkpoint_sha256:
        raise SystemExit('encoder mismatch with trained model')
    if meta.get('window_semantics') != 'time-aligned-v2':
        raise SystemExit('legacy P1 checkpoint affected by D33; retrain before research evaluation')
    validate_feature_identity(meta, encoder, a.encode_batch)
    started = time.time()
    ds = EpisodeDataset.from_manifest(a.dataset, split=a.split)
    feats = build_cache(ds, encoder, a.cache_dir, batch=a.encode_batch)
    report, _ = condition_report(model, norm, ds, feats, a.device, lrs, ks, a.seed)
    report.update(task_id=os.environ.get('P0_TASK_ID', 'STAGE0-028-R0-4'), condition=a.condition,
                  dataset_sha256=file_sha256(a.dataset), model_sha256=file_sha256(a.model),
                  model_dataset_sha256=meta['dataset_sha256'], encoder_sha256=encoder.checkpoint_sha256,
                  lrs=lrs, ks=ks, seed=a.seed, protocol='predict-then-update; per-episode reset; post_warmup=t>=k',
                  seconds=time.time() - started,
                  gpu_peak_allocated_bytes=torch.cuda.max_memory_allocated() if str(a.device).startswith('cuda') else 0,
                  gpu_peak_reserved_bytes=torch.cuda.max_memory_reserved() if str(a.device).startswith('cuda') else 0)
    feats.close()
    out.mkdir(parents=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ['condition', 'episodes', 'frozen_mean', 'copy_mean', 'seconds']}, indent=2))


if __name__ == '__main__':
    main()
