"""Diagnostic helper (train/val only, never touches test): report 1-step block-MSE for the copy
baseline plus any trained model checkpoints on the validation split, for hyperparameter selection."""
import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wm.dynamics import CopyModel, MLPDynamics, Normalizer  # noqa: E402
from wm.cache import validate_feature_identity
from wm.encoder import FixedEncoder  # noqa: E402
from wm.losses import block_mse  # noqa: E402
from wm.train_offline import encode_split, WindowSource, validation_loss
from wm.evaluate_prediction import load_model  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--encoder-checkpoint', required=True)
    p.add_argument('--model', action='append', default=[], help='name=path.pt, repeatable')
    p.add_argument('--split', default='val')
    p.add_argument('--device', default='cuda')
    p.add_argument('--batch', type=int, default=512)
    p.add_argument('--cache-dir')
    p.add_argument('--encode-batch', type=int, default=128)
    a = p.parse_args()
    if a.split == 'test':
        raise SystemExit('val_probe is for train/val-only diagnosis; use evaluate_prediction.py for test')
    encoder = FixedEncoder(a.encoder_checkpoint, a.device)
    loaded = []
    for spec in a.model:
        name, path = spec.split('=', 1)
        model, norm, meta = load_model(path, a.device)
        if meta['encoder_sha256'] != encoder.checkpoint_sha256:
            raise SystemExit('encoder mismatch with checkpoint')
        if meta.get('window_semantics') != 'time-aligned-v2':
            raise SystemExit('legacy P1 checkpoint affected by D33; retrain before diagnosis')
        validate_feature_identity(meta, encoder, a.encode_batch)
        loaded.append((name, model, norm))
    ds, feats = encode_split(a.dataset, a.split, encoder, a.cache_dir, a.encode_batch)
    source = WindowSource(ds, feats)
    if loaded:
        # Checkpoint statistics and hidden architecture; no train reload or refit.
        norm = loaded[0][2]
    else:
        _, ftrain = encode_split(a.dataset, 'train', encoder, a.cache_dir, a.encode_batch)
        norm = Normalizer(*ftrain.statistics()).to(a.device)
        ftrain.close()
    out = {'copy': float(validation_loss(CopyModel(), norm, source, a.batch, a.device)[0])}
    for name, model, mnorm in loaded:
        out[name] = float(validation_loss(model, mnorm, source, a.batch, a.device)[0])
    out['windows'] = len(source)
    feats.close()
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
