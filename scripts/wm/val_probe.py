"""Diagnostic helper (train/val only, never touches test): report 1-step block-MSE for the copy
baseline plus any trained model checkpoints on the validation split, for hyperparameter selection."""
import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wm.dynamics import CopyModel, MLPDynamics, Normalizer  # noqa: E402
from wm.encoder import FixedEncoder  # noqa: E402
from wm.losses import block_mse  # noqa: E402
from wm.train_offline import encode_split, window_tensors  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--encoder-checkpoint', required=True)
    p.add_argument('--model', action='append', default=[], help='name=path.pt, repeatable')
    p.add_argument('--split', default='val')
    p.add_argument('--device', default='cuda')
    a = p.parse_args()
    if a.split == 'test':
        raise SystemExit('val_probe is for train/val-only diagnosis; use evaluate_prediction.py for test')
    encoder = FixedEncoder(a.encoder_checkpoint, a.device)
    # Use TRAIN-split statistics for standardization, matching train_offline.py, so numbers are
    # comparable to the frozen evaluation; the split under inspection contributes no statistics.
    _, ftrain = encode_split(a.dataset, 'train', encoder)
    norm = Normalizer(ftrain.mean(0), ftrain.std(0)).to(a.device)
    ds, feats = encode_split(a.dataset, a.split, encoder)
    w = window_tensors(ds, feats, 1, a.device)
    z = norm(w['h'])
    out = {'copy': float(block_mse(z[:, 0], z[:, 1])[0])}
    for spec in a.model:
        name, path = spec.split('=', 1)
        data = torch.load(path, map_location=a.device, weights_only=False)
        model = MLPDynamics(data['dim'], use_action=data['use_action']).to(a.device).eval()
        model.load_state_dict(data['state_dict'])
        mnorm = Normalizer(torch.zeros(data['dim']), torch.ones(data['dim'])).to(a.device)
        mnorm.load_state_dict(data['normalizer'])
        zz = mnorm(w['h'])
        with torch.no_grad():
            out[name] = float(block_mse(model(zz[:, 0], w['action'][:, 0], w['dt'][:, 0]), zz[:, 1])[0])
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
