"""P1-A2 offline training of the no-action baseline and the action-conditioned predictor.

Both models use identical data, seed, optimizer and budget. Checkpoint selection rule (fixed before testing):
the epoch with minimum validation block-MSE (standardized); stop after `patience` epochs without improvement
or at `epochs`. The test split is never read here.
"""
import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wm.data import EpisodeDataset, file_sha256  # noqa: E402
from wm.dynamics import MLPDynamics, Normalizer  # noqa: E402
from wm.encoder import FixedEncoder  # noqa: E402
from wm.losses import block_mse  # noqa: E402


def encode_split(dataset_path, split, encoder, cache_dir=None, encode_batch=128):
    from wm.cache import build_cache
    ds = EpisodeDataset.from_manifest(dataset_path, split)
    return ds, build_cache(ds, encoder, cache_dir, batch=encode_batch)


class WindowSource:
    """Small window index, owned current-batch features; never materialize the dataset on device."""
    def __init__(self, ds, features, k=1, exclude_goal_switch=False):
        self.ds, self.features, self.k = ds, features, k
        self.windows = ds.windows(k, exclude_goal_switch)

    def __len__(self):
        return len(self.windows)

    def take(self, idx, device):
        idx = np.asarray(idx, dtype=np.int64)
        e, t = idx[:, 0], idx[:, 1]
        if (e < 0).any() or (e >= len(self.ds.episodes)).any() or (t < 0).any():
            raise ValueError('invalid episode/time index')
        from wm.data import DataError
        if (t + self.k > self.ds.n_valid[e]).any():
            raise DataError('window crosses episode end')
        o = (self.ds.obs_offset[e] + t)[:, None] + np.arange(self.k + 1)
        a = (self.ds.act_offset[e] + t)[:, None] + np.arange(self.k)
        to = lambda x: torch.as_tensor(x, dtype=torch.float32, device=device)
        return dict(h=to(self.features[o]), action=to(self.ds.action[a]), dt=to(self.ds.dt[a]), episode=e, t=t)

    def batches(self, batch_size, device, order=None):
        if batch_size < 1:
            raise ValueError('batch size must be positive')
        for start in range(0, len(self), batch_size):
            ix = self.windows[start:start+batch_size] if order is None else self.windows[order[start:start+batch_size]]
            yield self.take(ix, device)


def window_tensors(ds, features, k, device, exclude_goal_switch=False):
    """Small correctness-reference API. All production consumers use WindowSource batches."""
    source = WindowSource(ds, features, k, exclude_goal_switch)
    if len(source) * (k+1) * features.shape[-1] * 4 > 128 << 20:
        raise ValueError('full-window reference exceeds 128MiB; use WindowSource.batches')
    return source.take(source.windows, device)


@torch.no_grad()
def validation_loss(model, norm, source, batch, device):
    total = np.zeros(3, np.float64)
    count = 0
    model.eval()
    for w in source.batches(batch, device):
        z = norm(w['h'])
        values = block_mse(model(z[:, 0], w['action'][:, 0], w['dt'][:, 0]), z[:, 1], reduce=False)
        total += np.array([v.double().sum().item() for v in values])
        count += len(z)
    if not count:
        raise ValueError('no valid windows')
    return total / count


def train_model(model, norm, train, val, args, log, save_epoch=None):
    # Caller seeds before model construction; resetting here cannot repair initial weights.
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=getattr(args, 'weight_decay', 0.))
    rng = np.random.default_rng(args.seed)
    device = next(model.parameters()).device
    best, best_state, stale, curve, completed = float('inf'), None, 0, [], 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        order = rng.permutation(len(train))  # same global uniform transition shuffle as before
        for w in train.batches(args.batch, device, order):
            z = norm(w['h'])
            loss = block_mse(model(z[:, 0], w['action'][:, 0], w['dt'][:, 0]), z[:, 1])[0]
            opt.zero_grad()
            loss.backward()
            opt.step()
            completed += 1
            if getattr(args, 'max_train_batches', 0) and completed >= args.max_train_batches:
                break
        vl = validation_loss(model, norm, val, args.batch, device)
        tl = validation_loss(model, norm, train, args.batch, device)[0]
        row = dict(epoch=epoch, train=float(tl), val=float(vl[0]), val_robot=float(vl[1]), val_map=float(vl[2]),
                   completed_train_batches=completed, train_diagnostic_windows=len(train), val_windows=len(val))
        curve.append(row)
        log.write(json.dumps(row) + '\n')
        log.flush()
        if row['val'] < best - 1e-7:
            best, stale = row['val'], 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
        if save_epoch is not None:
            save_epoch(dict(epoch=epoch, optimizer=opt.state_dict(), numpy_rng=rng.bit_generator.state,
                            torch_rng=torch.get_rng_state(), completed_train_batches=completed,
                            best_state=best_state, best_val=best, stale=stale,
                            cuda_rng=torch.cuda.get_rng_state(device) if device.type == 'cuda' else None))
        if stale >= args.patience:
            break
        if getattr(args, 'max_train_batches', 0) and completed >= args.max_train_batches:
            break
    model.load_state_dict(best_state)
    return dict(best_val=best, best_epoch=min(curve, key=lambda r: r['val'])['epoch'], epochs_run=len(curve),
                completed_train_batches=completed, validation_windows=len(val))


def atomic_checkpoint(payload, path):
    path = Path(path)
    temporary = path.with_name(path.name + '.partial')
    torch.save(payload, temporary)
    os.replace(temporary, path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--encoder-checkpoint', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--epochs', type=int, default=200)
    p.add_argument('--patience', type=int, default=20)
    p.add_argument('--batch', type=int, default=512)
    p.add_argument('--lr', type=float, default=1e-3)
    p.add_argument('--weight-decay', type=float, default=0.)
    p.add_argument('--hidden', default='256,256')
    p.add_argument('--seed', type=int, default=11)
    p.add_argument('--device', default='cuda')
    p.add_argument('--cache-dir')
    p.add_argument('--encode-batch', type=int, default=128)
    p.add_argument('--max-train-batches', type=int, default=0, help='finite engineering check only; 0 = full training')
    a = p.parse_args()
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=False)
    def interrupted(signum, frame):
        (out / 'interrupted.json').write_text(json.dumps(dict(signal=signal.Signals(signum).name, time=time.time(),
            recovery='latest complete epoch checkpoint retained; no exact resume CLI; use a new output for restart')))
        raise KeyboardInterrupt
    signal.signal(signal.SIGINT, interrupted)
    signal.signal(signal.SIGTERM, interrupted)
    started = time.time()
    torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark = True, False
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    encoder = FixedEncoder(a.encoder_checkpoint, a.device)
    train_ds, ftrain = encode_split(a.dataset, 'train', encoder, a.cache_dir, a.encode_batch)
    val_ds, fval = encode_split(a.dataset, 'val', encoder, a.cache_dir, a.encode_batch)
    mean, std = ftrain.statistics()
    norm = Normalizer(mean, std).to(a.device)
    train, val = WindowSource(train_ds, ftrain), WindowSource(val_ds, fval)
    results = {}
    for name, use_action in [('no_action', False), ('action', True)]:
        hidden=tuple(int(x) for x in a.hidden.split(','))
        torch.manual_seed(a.seed)  # fix initialization before creating each predictor
        model = MLPDynamics(encoder.dim, hidden=hidden, use_action=use_action).to(a.device)
        def payload():
            return dict(state_dict=model.state_dict(), use_action=use_action, dim=encoder.dim, hidden=list(hidden),
                        normalizer=norm.state_dict(), encoder_sha256=encoder.checkpoint_sha256,
                        dataset_sha256=file_sha256(a.dataset), config=vars(a), window_semantics='time-aligned-v2',
                        feature_cache_identity=ftrain.meta['identity'])
        def save_epoch(state):
            atomic_checkpoint(dict(payload(), training_state=state), out / (name + '-latest.pt'))
        with (out / (name + '-curve.jsonl')).open('w') as log:
            results[name] = train_model(model, norm, train, val, a, log, save_epoch=save_epoch)
        atomic_checkpoint(payload(), out / (name + '.pt'))
    summary = dict(task_id=os.environ.get('P0_TASK_ID', 'P1-A2'), results=results, feature_dim=encoder.dim,
                   robot_dim=41, map_feature_dim=encoder.map_dim, encoder_sha256=encoder.checkpoint_sha256,
                   dataset_sha256=file_sha256(a.dataset), train_transitions=len(train), val_transitions=len(val),
                   dead_feature_dims=int((std < 1e-3).sum()), seconds=time.time() - started,
                   gpu_peak_allocated_bytes=torch.cuda.max_memory_allocated() if a.device == 'cuda' else 0,
                   selection_rule='min validation standardized block-MSE; patience %d; max %d epochs' % (a.patience, a.epochs))
    summary['gpu_peak_reserved_bytes'] = torch.cuda.max_memory_reserved() if a.device.startswith('cuda') else 0
    summary['feature_cache_train'] = str(ftrain.root)
    summary['feature_cache_val'] = str(fval.root)
    summary['window_semantics'] = 'time-aligned-v2'
    ftrain.close()
    fval.close()
    (out / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
