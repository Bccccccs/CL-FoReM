"""P1-A3 one-shot held-out evaluation: 1-step and 5-step open-loop prediction for copy / no-action / action models.

Errors are aggregated per episode first; paired episode differences get a bootstrap 95% CI (fixed seed).
Open-loop rollouts feed predicted features back and use recorded actions/dt; no true intermediate features.
This is prediction for a given action sequence, not a closed-loop policy rollout.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wm.data import file_sha256  # noqa: E402
from wm.dynamics import CopyModel, MLPDynamics, Normalizer, rollout  # noqa: E402
from wm.cache import validate_feature_identity
from wm.encoder import FixedEncoder  # noqa: E402
from wm.losses import block_mse  # noqa: E402
from wm.train_offline import encode_split, WindowSource  # noqa: E402


def load_model(path, device):
    data = torch.load(path, map_location=device, weights_only=False)
    model = MLPDynamics(data['dim'], hidden=tuple(data.get('hidden', (256, 256))), use_action=data['use_action']).to(device)
    model.load_state_dict(data['state_dict'])
    norm = Normalizer(torch.zeros(data['dim']), torch.ones(data['dim'])).to(device)
    norm.load_state_dict(data['normalizer'])
    return model.eval(), norm, data


def bootstrap_ci(values, seed=0, n=10000):
    values = np.asarray(values)
    if not len(values):
        return [float('nan'), float('nan')]
    rng = np.random.default_rng(seed)
    means = np.empty(n, np.float64)
    batch = max(1, min(128, (1 << 20) // len(values)))
    for start in range(0, n, batch):
        count = min(batch, n-start)
        idx = rng.integers(0, len(values), size=(count, len(values)))
        means[start:start+count] = values[idx].mean(1)
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def per_episode(values, episodes, n):
    return np.array([values[episodes == i].mean() if (episodes == i).any() else np.nan for i in range(n)])


@torch.no_grad()
def prediction_errors(models, norm, source, batch, device):
    """Accumulate window errors per episode without retaining full-window predictions."""
    n = len(source.ds.episodes)
    keys = ['total', 'robot', 'map', 'raw_total', 'raw_robot', 'raw_map']
    sums = {name: np.zeros((n, len(keys)), np.float64) for name in models}
    counts = np.zeros(n, np.int64)
    for w in source.batches(batch, device):
        z = norm(w['h'])
        np.add.at(counts, w['episode'], 1)
        for name, model in models.items():
            model.eval()
            pred = rollout(model, z[:, 0], w['action'], w['dt'])[:, -1]
            values = block_mse(pred, z[:, -1], reduce=False) + block_mse(norm.inverse(pred), w['h'][:, -1], reduce=False)
            errors = np.stack([v.cpu().numpy() for v in values], 1)
            np.add.at(sums[name], w['episode'], errors)
    denominator = np.where(counts > 0, counts, np.nan)
    return {name: {key: value[:, i]/denominator for i, key in enumerate(keys)} for name, value in sums.items()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--models', required=True, help='directory from train_offline.py')
    p.add_argument('--encoder-checkpoint', required=True)
    p.add_argument('--split', default='test')
    p.add_argument('--output', required=True)
    p.add_argument('--device', default='cuda')
    p.add_argument('--batch', type=int, default=512)
    p.add_argument('--cache-dir')
    p.add_argument('--encode-batch', type=int, default=128)
    a = p.parse_args()
    out = Path(a.output)
    if out.exists():
        raise SystemExit('output exists; held-out evaluation is one-shot')
    encoder = FixedEncoder(a.encoder_checkpoint, a.device)
    action, norm, meta = load_model(Path(a.models) / 'action.pt', a.device)
    no_action, norm2, meta2 = load_model(Path(a.models) / 'no_action.pt', a.device)
    # The encoder must match exactly (features must be apples-to-apples). The test dataset file is
    # allowed to differ from the training dataset file: evaluating trained models against a separately
    # collected, never-before-touched test set is the intended one-shot workflow (see D26/D27).
    if meta['encoder_sha256'] != encoder.checkpoint_sha256 or meta2['encoder_sha256'] != encoder.checkpoint_sha256:
        raise SystemExit('encoder mismatch with trained models')
    if any(not torch.equal(norm.state_dict()[key], norm2.state_dict()[key]) for key in norm.state_dict()):
        raise SystemExit('model normalizers differ')
    if any(m.get('window_semantics') != 'time-aligned-v2' for m in (meta, meta2)):
        raise SystemExit('legacy P1 checkpoint affected by D33; retrain before research evaluation')
    validate_feature_identity(meta, encoder, a.encode_batch)
    validate_feature_identity(meta2, encoder, a.encode_batch)
    training_dataset_sha256 = meta['dataset_sha256']
    ds, feats = encode_split(a.dataset, a.split, encoder, a.cache_dir, a.encode_batch)
    manifest = json.loads(Path(a.dataset).read_text())
    success = {r['seed']: r.get('primary_reason') == 'success' for r in manifest['episodes']}
    ep_success = np.array([success[int(s)] for s in ds.seeds])
    models = dict(copy=CopyModel(), no_action=no_action, action=action)
    report = dict(task_id=os.environ.get('P0_TASK_ID', 'P1-A3'), split=a.split, episodes=len(ds.episodes),
                  success_episodes=int(ep_success.sum()), encoder_sha256=encoder.checkpoint_sha256,
                  eval_dataset_sha256=file_sha256(a.dataset), training_dataset_sha256=training_dataset_sha256,
                  dataset_is_separately_collected=(training_dataset_sha256 != file_sha256(a.dataset)), horizons={})
    for k in [1, 5]:
        source = WindowSource(ds, feats, k)
        horizon = dict(windows=len(source), models={}, paired={})
        per_ep = prediction_errors(models, norm, source, a.batch, a.device)
        for name, eps in per_ep.items():
            valid = ~np.isnan(eps['total'])
            horizon['models'][name] = {key: float(np.nanmean(v)) for key, v in eps.items()}
            horizon['models'][name]['by_outcome'] = {
                grp: float(np.nanmean(eps['total'][valid & (ep_success == flag)])) if (valid & (ep_success == flag)).any() else None
                for grp, flag in [('success', True), ('failure', False)]}
        horizon['per_episode'] = {name: {key: v.tolist() for key, v in eps.items()} for name, eps in per_ep.items()}
        for other in ['copy', 'no_action']:
            for key in ['total', 'robot', 'map']:
                d = per_ep['action'][key] - per_ep[other][key]
                d = d[~np.isnan(d)]
                horizon['paired']['action_minus_%s_%s' % (other, key)] = dict(
                    mean=float(d.mean()), ci95=bootstrap_ci(d), episodes=int(len(d)),
                    action_better_fraction=float((d < 0).mean()))
        report['horizons'][str(k)] = horizon
    feats.close()
    report['window_semantics'] = 'time-aligned-v2'
    report['gpu_peak_allocated_bytes'] = torch.cuda.max_memory_allocated() if a.device.startswith('cuda') else 0
    report['gpu_peak_reserved_bytes'] = torch.cuda.max_memory_reserved() if a.device.startswith('cuda') else 0
    out.mkdir(parents=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
