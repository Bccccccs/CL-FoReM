"""P1-A2 offline training of the no-action baseline and the action-conditioned predictor.

Both models use identical data, seed, optimizer and budget. Checkpoint selection rule (fixed before testing):
the epoch with minimum validation block-MSE (standardized); stop after `patience` epochs without improvement
or at `epochs`. The test split is never read here.
"""
import argparse
import json
import os
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


def encode_split(dataset_path, split, encoder):
    ds = EpisodeDataset.from_manifest(dataset_path, split)
    return ds, encoder.encode_numpy(ds.robot, ds.map)


def window_tensors(ds, features, k, device, exclude_goal_switch=False):
    w = ds.windows(k, exclude_goal_switch)
    e, t = w[:, 0], w[:, 1]
    o = ds.obs_offset[e][:, None] + np.arange(k + 1)
    a = ds.act_offset[e][:, None] + np.arange(k)
    to = lambda x: torch.as_tensor(x, dtype=torch.float32, device=device)
    return dict(h=to(features[o]), action=to(ds.action[a]), dt=to(ds.dt[a]), episode=e, t=t)


def train_model(model, norm, train, val, args, log):
    torch.manual_seed(args.seed)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=getattr(args,'weight_decay',0.))
    zt, zv = norm(train['h']), norm(val['h'])
    rng = np.random.default_rng(args.seed)
    best, best_state, stale, curve = float('inf'), None, 0, []
    for epoch in range(1, args.epochs + 1):
        model.train()
        order = torch.as_tensor(rng.permutation(len(zt)), device=zt.device)
        for s in range(0, len(order), args.batch):
            i = order[s:s + args.batch]
            loss = block_mse(model(zt[i, 0], train['action'][i, 0], train['dt'][i, 0]), zt[i, 1])[0]
            opt.zero_grad()
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            vl = block_mse(model(zv[:, 0], val['action'][:, 0], val['dt'][:, 0]), zv[:, 1])
            tl = block_mse(model(zt[:, 0], train['action'][:, 0], train['dt'][:, 0]), zt[:, 1])[0]
        row = dict(epoch=epoch, train=float(tl), val=float(vl[0]), val_robot=float(vl[1]), val_map=float(vl[2]))
        curve.append(row)
        log.write(json.dumps(row) + '\n')
        log.flush()
        if row['val'] < best - 1e-7:
            best, stale = row['val'], 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
            if stale >= args.patience:
                break
    model.load_state_dict(best_state)
    return dict(best_val=best, best_epoch=min(curve, key=lambda r: r['val'])['epoch'], epochs_run=len(curve))


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
    a = p.parse_args()
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=False)
    started = time.time()
    torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark = True, False
    encoder = FixedEncoder(a.encoder_checkpoint, a.device)
    train_ds, ftrain = encode_split(a.dataset, 'train', encoder)
    val_ds, fval = encode_split(a.dataset, 'val', encoder)
    norm = Normalizer(ftrain.mean(0), ftrain.std(0)).to(a.device)
    train, val = window_tensors(train_ds, ftrain, 1, a.device), window_tensors(val_ds, fval, 1, a.device)
    results = {}
    for name, use_action in [('no_action', False), ('action', True)]:
        hidden=tuple(int(x) for x in a.hidden.split(','))
        model = MLPDynamics(encoder.dim, hidden=hidden, use_action=use_action).to(a.device)
        with (out / (name + '-curve.jsonl')).open('w') as log:
            results[name] = train_model(model, norm, train, val, a, log)
        torch.save(dict(state_dict=model.state_dict(), use_action=use_action, dim=encoder.dim, hidden=list(hidden),
                        normalizer=norm.state_dict(), encoder_sha256=encoder.checkpoint_sha256,
                        dataset_sha256=file_sha256(a.dataset), config=vars(a)), out / (name + '.pt'))
    summary = dict(task_id=os.environ.get('P0_TASK_ID', 'P1-A2'), results=results, feature_dim=encoder.dim,
                   robot_dim=41, map_feature_dim=encoder.map_dim, encoder_sha256=encoder.checkpoint_sha256,
                   dataset_sha256=file_sha256(a.dataset), train_transitions=len(train['h']), val_transitions=len(val['h']),
                   dead_feature_dims=int((ftrain.std(0) < 1e-3).sum()), seconds=time.time() - started,
                   gpu_peak_allocated_bytes=torch.cuda.max_memory_allocated() if a.device == 'cuda' else 0,
                   selection_rule='min validation standardized block-MSE; patience %d; max %d epochs' % (a.patience, a.epochs))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
