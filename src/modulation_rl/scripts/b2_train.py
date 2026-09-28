"""FOLLOWUP-028 B2 (D51-B2): builds the four foresight classifiers (C-geo/C-cur/C-hist/C-wm) from
--save-observations + --save-step-info data (seeds 1000-1999, deterministic policy, nominal
condition; train 1000-1699 / val 1700-1799 / test 1800-1999, D51), evaluates AUROC/AUPRC on the
test split with episode-clustered bootstrap CIs, selects B3 thresholds on the validation split at a
10% step-level trigger rate, and saves a ClassifierPack per classifier for shield.py.

All feature/label construction goes through foresight.py - the exact module shield.py also
imports - so offline and online features are identical by construction, not by convention.

Lives outside scripts/wm/ (code_identity() reasons, see residual_probe.py's docstring).
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

import foresight
from wm.encoder import FixedEncoder
from residual_probe import load_model as load_dynamics

SPLIT_RANGES = dict(train=(1000, 1700), val=(1700, 1800), test=(1800, 2000))
DATA_EFFICIENCY_EPISODES = (100, 300, 700)


def discover_episodes(data_dir):
    """Scans a flat shard-eval output directory for seeds with both an -observations.npz and a
    -stepinfo.npz (both required; --save-step-info without --save-observations, or vice versa,
    yields nothing usable). Returns {seed: (obs_path, stepinfo_path)}."""
    data_dir = Path(data_dir)
    out = {}
    for obs_path in sorted(data_dir.glob('episode-*-observations.npz')):
        seed = int(obs_path.name.split('-')[1])
        step_path = data_dir / ('episode-%05d-stepinfo.npz' % seed)
        if step_path.exists():
            out[seed] = (obs_path, step_path)
    return out


def split_of(seed, split_ranges=SPLIT_RANGES):
    for name, (lo, hi) in split_ranges.items():
        if lo <= seed < hi:
            return name
    return None


@torch.no_grad()
def episode_features(obs_path, step_path, encoder, dyn_norm, device):
    """Returns a dict of per-decision-step (t=0..n-1) arrays for one episode: z_std (n,dim),
    action (n,3), and the raw stepinfo fields (n,) each (kin_failure etc., aligned to action
    index t = outcome of executing action t)."""
    with np.load(obs_path) as d:
        robot, local_map, action = d['robot_state'], d['local_map'], d['action']
    with np.load(step_path) as d:
        step = {k: d[k] for k in d.files}
    n = len(action)
    if len(robot) < n + 1:
        return None  # incomplete episode (exception mid-rollout); skip, do not fabricate
    raw = encoder.encode_numpy(robot[:n + 1], local_map[:n + 1], batch=128)
    z_std = dyn_norm(torch.as_tensor(raw, dtype=torch.float32, device=device)).cpu().numpy().astype(np.float64)
    return dict(z_std=z_std, action=action.astype(np.float64), n=n, step=step)


def build_split_features(episode_seeds, episodes, dynamics, dyn_norm_dyn, policy, K, device, compute_wm):
    """episodes: {seed: episode_features(...) result}. Builds concatenated per-step feature/label
    arrays across all given episode seeds, in the order given."""
    rows = dict(geo=[], cur=[], hist=[], wm=[] if compute_wm else None,
                y5=[], m5=[], y10=[], m10=[], episode_id=[], seed=[])
    for seed in episode_seeds:
        ep = episodes[seed]
        if ep is None:
            continue
        n, z, a, step = ep['n'], ep['z_std'], ep['action'], ep['step']
        labels5, mask5 = foresight.label_new_failure(step['kin_failure'], foresight.H_PRIMARY)
        labels10, mask10 = foresight.label_new_failure(step['kin_failure'], foresight.H_SECONDARY)
        prev_dist = np.r_[0.0, step['dist_to_desired'][:-1]]
        prev_rot = np.r_[0.0, step['rot_dist_to_desired'][:-1]]
        prev_goal_base = np.r_[0.0, step['goal_to_base_distance'][:-1]]
        for t in range(n):
            rows['geo'].append(foresight.geo_feature(prev_dist[t], prev_rot[t], prev_goal_base[t]))
            rows['cur'].append(foresight.cur_feature(z[t], a[t]))
            past_pairs = [(z[t - j], a[t - j]) for j in range(1, K + 1) if t - j >= 0]
            rows['hist'].append(foresight.hist_feature(z[t], a[t], past_pairs, K=K))
            if compute_wm:
                rows['wm'].append(foresight.wm_feature(z[t], a[t], dynamics, dyn_norm_dyn, policy, K=K, device=device))
            rows['y5'].append(labels5[t]); rows['m5'].append(mask5[t])
            rows['y10'].append(labels10[t]); rows['m10'].append(mask10[t])
            rows['episode_id'].append(seed); rows['seed'].append(seed)
    out = dict(geo=np.asarray(rows['geo']), cur=np.asarray(rows['cur']), hist=np.asarray(rows['hist']),
               y5=np.asarray(rows['y5'], dtype=bool), m5=np.asarray(rows['m5'], dtype=bool),
               y10=np.asarray(rows['y10'], dtype=bool), m10=np.asarray(rows['m10'], dtype=bool),
               episode_id=np.asarray(rows['episode_id']))
    if compute_wm:
        out['wm'] = np.asarray(rows['wm'])
    return out


def train_and_evaluate(name, kind, X, split_data, H_key, mask_key, device, train_episode_subset=None):
    tr_mask = split_data['train'][mask_key]
    va_mask = split_data['val'][mask_key]
    te_mask = split_data['test'][mask_key]
    X_tr, y_tr = X['train'][tr_mask], split_data['train'][H_key][tr_mask]
    if train_episode_subset is not None:
        keep = np.isin(split_data['train']['episode_id'][tr_mask], train_episode_subset)
        X_tr, y_tr = X_tr[keep], y_tr[keep]
    X_va, y_va = X['val'][va_mask], split_data['val'][H_key][va_mask]
    X_te, y_te = X['test'][te_mask], split_data['test'][H_key][te_mask]
    ep_te = split_data['test']['episode_id'][te_mask]
    heads, norm, val_auroc = foresight.train_classifier(kind, X_tr, y_tr, X_va, y_va, device=device)
    test_scores = foresight.classifier_score(heads, norm, X_te, device)
    val_scores = foresight.classifier_score(heads, norm, X_va, device)
    test_auroc = foresight.point_metric_and_ci(foresight.auroc, test_scores, y_te, ep_te)
    test_auprc = foresight.point_metric_and_ci(foresight.auprc, test_scores, y_te, ep_te)
    return dict(name=name, n_train=int(len(X_tr)), n_val=int(len(X_va)), n_test=int(len(X_te)),
                val_auroc=val_auroc, test_auroc=test_auroc, test_auprc=test_auprc,
                heads=heads, norm=norm, val_scores=val_scores, test_scores=test_scores)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data-dir', required=True, help='flat directory from shard-eval.py with --save-observations --save-step-info, seeds 1000-1999')
    p.add_argument('--encoder-checkpoint', required=True)
    p.add_argument('--dynamics-checkpoint', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--device', default='cuda')
    p.add_argument('--history-k', type=int, default=foresight.HISTORY_K)
    p.add_argument('--trigger-rate', type=float, default=0.10)
    p.add_argument('--split-ranges', default=None,
                   help='JSON {"train":[lo,hi],"val":[lo,hi],"test":[lo,hi]} overriding the D51 '
                        '1000-1699/1700-1799/1800-1999 registration; smoke-test use only.')
    p.add_argument('--data-efficiency-episodes', default=None,
                   help='comma-separated episode counts overriding DATA_EFFICIENCY_EPISODES (100,300,700); smoke-test use only.')
    a = p.parse_args()
    out = Path(a.output)
    if out.exists():
        raise SystemExit('output exists; B2 is one-shot')
    split_ranges = {k: tuple(v) for k, v in json.loads(a.split_ranges).items()} if a.split_ranges else SPLIT_RANGES
    data_efficiency_episodes = [int(x) for x in a.data_efficiency_episodes.split(',')] if a.data_efficiency_episodes else DATA_EFFICIENCY_EPISODES

    started = time.time()
    seed_files = discover_episodes(a.data_dir)
    by_split = {'train': [], 'val': [], 'test': []}
    for seed in sorted(seed_files):
        s = split_of(seed, split_ranges)
        if s:
            by_split[s].append(seed)
    if not all(by_split.values()):
        raise SystemExit('missing episodes in one or more splits: %s' % {k: len(v) for k, v in by_split.items()})

    encoder = FixedEncoder(a.encoder_checkpoint, a.device)
    dynamics, dyn_norm, meta = load_dynamics(a.dynamics_checkpoint, a.device)
    if meta['encoder_sha256'] != encoder.checkpoint_sha256:
        raise SystemExit('encoder mismatch with trained dynamics model')
    policy = foresight.load_full_policy(a.encoder_checkpoint, a.device)

    print('ENCODING', {k: len(v) for k, v in by_split.items()}, flush=True)
    episodes = {}
    for i, seed in enumerate(sorted(seed_files)):
        obs_path, step_path = seed_files[seed]
        episodes[seed] = episode_features(obs_path, step_path, encoder, dyn_norm, a.device)
        if (i + 1) % 100 == 0:
            print('ENCODED', i + 1, len(seed_files), 'seconds=%.1f' % (time.time() - started), flush=True)

    split_data = {}
    for split in ['train', 'val', 'test']:
        split_data[split] = build_split_features(by_split[split], episodes, dynamics, dyn_norm, policy,
                                                  a.history_k, a.device, compute_wm=True)
        print('FEATURES', split, len(split_data[split]['episode_id']), 'seconds=%.1f' % (time.time() - started), flush=True)

    X = {split: dict(geo=split_data[split]['geo'], cur=split_data[split]['cur'],
                      hist=split_data[split]['hist'], wm=split_data[split]['wm']) for split in split_data}

    report = dict(seeds=dict(train=by_split['train'], val=by_split['val'], test=by_split['test']),
                  n_steps=dict((s, int(len(split_data[s]['episode_id']))) for s in split_data),
                  n_eligible_H5=dict((s, int(split_data[s]['m5'].sum())) for s in split_data),
                  n_eligible_H10=dict((s, int(split_data[s]['m10'].sum())) for s in split_data),
                  classifiers={})
    classifier_defs = [('C-geo', 'geo', 'logistic'), ('C-cur', 'cur', 'mlp'),
                        ('C-hist', 'hist', 'mlp'), ('C-wm', 'wm', 'mlp')]
    trained = {}
    for cname, key, kind in classifier_defs:
        Xh = {split: X[split][key] for split in X}
        result = train_and_evaluate(cname, kind, Xh, split_data, 'y5', 'm5', a.device)
        trained[cname] = result
        report['classifiers'][cname] = dict(kind=kind, dim=int(Xh['train'].shape[1]),
                                             n_train=result['n_train'], n_val=result['n_val'], n_test=result['n_test'],
                                             val_auroc=result['val_auroc'], test_auroc=result['test_auroc'],
                                             test_auprc=result['test_auprc'])
        print('CLASSIFIER DONE', cname, 'test_auroc=%.4f' % result['test_auroc']['point'], flush=True)

    # D51-B2 (H=5, full training set): three CI-based comparisons, all must hold.
    wm_scores = trained['C-wm']['test_scores']
    y_test = split_data['test']['y5'][split_data['test']['m5']]
    ep_test = split_data['test']['episode_id'][split_data['test']['m5']]
    d51 = {}
    for other in ['C-cur', 'C-hist', 'C-geo']:
        diff = foresight.episode_bootstrap_metric_diff(foresight.auroc, wm_scores, trained[other]['test_scores'], y_test, ep_test)
        d51['wm_minus_%s' % other] = diff
    passes = (d51['wm_minus_C-cur']['mean'] >= 0.02 and d51['wm_minus_C-cur']['ci95'][0] > 0 and
              d51['wm_minus_C-hist']['ci95'][0] > 0 and d51['wm_minus_C-geo']['ci95'][0] > 0)
    report['d51_b2'] = d51
    report['d51_b2_pass'] = bool(passes)

    # H=10 secondary report (not gating).
    report['h10_secondary'] = {}
    for cname, key, kind in classifier_defs:
        Xh = {split: X[split][key] for split in X}
        result = train_and_evaluate(cname, kind, Xh, split_data, 'y10', 'm10', a.device)
        report['h10_secondary'][cname] = dict(test_auroc=result['test_auroc'], test_auprc=result['test_auprc'])

    # Data-efficiency curve (secondary report, val AUROC only, H=5).
    report['data_efficiency'] = {}
    train_seeds_sorted = sorted(by_split['train'])
    for n_eps in data_efficiency_episodes:
        subset = np.asarray(train_seeds_sorted[:n_eps])
        report['data_efficiency'][str(n_eps)] = {}
        for cname, key, kind in classifier_defs:
            Xh = {split: X[split][key] for split in X}
            result = train_and_evaluate(cname, kind, Xh, split_data, 'y5', 'm5', a.device, train_episode_subset=subset)
            report['data_efficiency'][str(n_eps)][cname] = dict(n_train=result['n_train'], val_auroc=result['val_auroc'])

    # Thresholds at the requested step-level trigger rate on the validation split (pre-registered
    # 10%, D51); random arm's probability = C-wm's realized validation trigger rate.
    classifier_dir = out / 'classifiers'
    thresholds = {}
    for cname, key, kind in classifier_defs:
        result = trained[cname]
        thr = foresight.select_threshold_for_rate(result['val_scores'], a.trigger_rate)
        pack = foresight.ClassifierPack(cname, kind, X['train'][key].shape[1], result['heads'], result['norm'], thr,
                                         meta=dict(trigger_rate=a.trigger_rate, val_auroc=result['val_auroc']))
        pack.save(classifier_dir / key)
        realized_rate = float((result['val_scores'] > thr).mean())
        thresholds[cname] = dict(threshold=thr, requested_rate=a.trigger_rate, realized_val_rate=realized_rate)
    report['thresholds'] = thresholds
    report['random_probability'] = thresholds['C-wm']['realized_val_rate']

    report['seconds'] = time.time() - started
    out.mkdir(parents=True, exist_ok=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(d51_b2_pass=report['d51_b2_pass'], seconds=report['seconds'],
                           random_probability=report['random_probability']), indent=2))


if __name__ == '__main__':
    main()
