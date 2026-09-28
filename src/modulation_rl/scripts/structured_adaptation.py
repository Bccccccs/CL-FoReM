"""FOLLOWUP-028 A line (D50): structured, gradient-free low-dimensional online correction of the
frozen world model, evaluated on the same R0-4/R0-4b episode batches used by residual_probe.py /
adaptation_probe.py (seeds 9600-9699, 10 mismatch conditions; no new data collection).

Lives outside scripts/wm/ for the same code_identity() reason as residual_probe.py/
adaptation_probe.py (see their docstrings).

All variants are gradient-free (the base MLPDynamics weights are never touched) and causal
(predict-then-update: the correction applied to step t's prediction is built only from steps
0..t-1's revealed ground truth, then updated using step t's own outcome for step t+1):

  - V0 frozen: no correction at all (== residual_probe.episode_errors with lr=None,k=None).
  - V4 gain scalar: online least-squares scalar s = sum(<delta_hat,delta>)/sum(<delta_hat,delta_hat>)
      over past steps, clipped to [0,3], applied to the robot block only:
      pred = z + [s*delta_hat_robot, delta_hat_map]. 'V4_both' additionally estimates an
      independent map-block scalar the same way.
  - V5 delay selection: for each candidate delay d in {0,1,2,3,5,10}, evaluate what the frozen
      model would have predicted if the chassis action dims (index 1,2; index 0 is the
      end-effector reference speed, matching mismatch-v1/shield.py's dim convention) were taken
      from d steps ago (zero for t-d<0, matching mismatch-v1's initial zero buffer); track an EMA
      (alpha=0.2) of each candidate's past robot-block MSE; pick the currently-best d for this
      step's prediction, then update all candidates' EMAs with this step's outcome.
  - V6: V5's selected delay, then V4's gain scalar on top of the delay-corrected prediction.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from wm.data import ROBOT_DIM, file_sha256
from wm.losses import block_mse
from wm.cache import validate_feature_identity
from wm.evaluate_prediction import bootstrap_ci  # noqa: F401 (re-exported for callers/tests)
from residual_probe import load_model, episode_errors, episode_mean, paired_summary
from adaptation_probe import encode_condition

DELAYS = (0, 1, 2, 3, 5, 10)


def _delayed_action(actions, t, d):
    """actions: (n,3) tensor. Returns a (1,3) action with dims [1,2] replaced by actions[t-d,1:3]
    (or zero if t-d<0), dim 0 left at actions[t,0]."""
    a = actions[t:t + 1].clone()
    src = t - d
    a[0, 1:3] = actions[src, 1:3] if src >= 0 else torch.zeros(2, dtype=actions.dtype, device=actions.device)
    return a


def episode_replay(base_model, feats, ds, i, norm, device, mode, ema_alpha=0.2, delays=DELAYS):
    n = int(ds.n_valid[i])
    if n < 1:
        return [], []
    o0, a0 = int(ds.obs_offset[i]), int(ds.act_offset[i])
    z = norm(torch.as_tensor(feats[np.arange(o0, o0 + n + 1)], dtype=torch.float32, device=device))
    actions = torch.as_tensor(ds.action[a0:a0 + n], dtype=torch.float32, device=device)
    dts = torch.as_tensor(ds.dt[a0:a0 + n], dtype=torch.float32, device=device)
    base_model.eval()
    rows, diag = [], []
    num_r = den_r = num_m = den_m = 0.0
    ema = {d: None for d in delays}
    for t in range(n):
        with torch.no_grad():
            pred_frozen = base_model(z[t:t + 1], actions[t:t + 1], dts[t:t + 1])
        delta_hat_frozen = pred_frozen - z[t:t + 1]
        s_r = min(3.0, max(0.0, num_r / den_r)) if den_r > 0 else 1.0
        s_m = min(3.0, max(0.0, num_m / den_m)) if den_m > 0 else 1.0
        if mode == 'V0':
            pred = pred_frozen
        elif mode in ('V4_robot', 'V4_both'):
            corrected_robot = z[t:t + 1, :ROBOT_DIM] + s_r * delta_hat_frozen[:, :ROBOT_DIM]
            corrected_map = (z[t:t + 1, ROBOT_DIM:] + s_m * delta_hat_frozen[:, ROBOT_DIM:]) if mode == 'V4_both' else pred_frozen[:, ROBOT_DIM:]
            pred = torch.cat([corrected_robot, corrected_map], dim=-1)
        elif mode in ('V5', 'V6'):
            valid = {d: v for d, v in ema.items() if v is not None}
            d_star = min(valid, key=lambda d: valid[d]) if valid else 0
            a_delayed = _delayed_action(actions, t, d_star)
            with torch.no_grad():
                pred_delayed = base_model(z[t:t + 1], a_delayed, dts[t:t + 1])
            if mode == 'V5':
                pred = pred_delayed
            else:
                delta_hat_d = pred_delayed - z[t:t + 1]
                corrected_robot = z[t:t + 1, :ROBOT_DIM] + s_r * delta_hat_d[:, :ROBOT_DIM]
                pred = torch.cat([corrected_robot, pred_delayed[:, ROBOT_DIM:]], dim=-1)
        else:
            raise ValueError('unknown mode ' + mode)
        total, robot, maps = block_mse(pred, z[t + 1:t + 2], reduce=False)
        rows.append(dict(step=t, total=float(total.item()), robot=float(robot.item()), maps=float(maps.item())))
        delta_true = z[t + 1:t + 2] - z[t:t + 1]
        dr_hat, dr_true = delta_hat_frozen[:, :ROBOT_DIM], delta_true[:, :ROBOT_DIM]
        num_r += float((dr_hat * dr_true).sum()); den_r += float((dr_hat * dr_hat).sum())
        dm_hat, dm_true = delta_hat_frozen[:, ROBOT_DIM:], delta_true[:, ROBOT_DIM:]
        num_m += float((dm_hat * dm_true).sum()); den_m += float((dm_hat * dm_hat).sum())
        if mode in ('V5', 'V6'):
            diag.append(d_star)
            for d in delays:
                a_d = _delayed_action(actions, t, d)
                with torch.no_grad():
                    pred_d = base_model(z[t:t + 1], a_d, dts[t:t + 1])
                resid = float(((pred_d[:, :ROBOT_DIM] - z[t + 1:t + 2, :ROBOT_DIM]) ** 2).mean().item())
                ema[d] = resid if ema[d] is None else (1 - ema_alpha) * ema[d] + ema_alpha * resid
        else:
            diag.append(s_r if mode in ('V4_robot', 'V4_both') else None)
    return rows, diag


def parse_condition_name(name):
    """'gain1.4_delay5' -> (1.4, 5); returns (None, None) if the name does not match (e.g. 'nominal')."""
    try:
        gain_s, delay_s = name.replace('gain', '').split('_delay')
        return float(gain_s), int(delay_s)
    except ValueError:
        return None, None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--conditions', required=True, help='comma-separated name:dataset_path:split')
    p.add_argument('--nominal', required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--encoder-checkpoint', required=True)
    p.add_argument('--cache-dir')
    p.add_argument('--encode-batch', type=int, default=128)
    p.add_argument('--output', required=True)
    p.add_argument('--device', default='cuda')
    p.add_argument('--ema-alpha', type=float, default=0.2)
    p.add_argument('--seed', type=int, default=0)
    a = p.parse_args()
    out = Path(a.output)
    if out.exists():
        raise SystemExit('output exists; A-line probe is one-shot')

    from wm.encoder import FixedEncoder
    encoder = FixedEncoder(a.encoder_checkpoint, a.device)
    model, norm, meta = load_model(a.model, a.device)
    if meta['encoder_sha256'] != encoder.checkpoint_sha256:
        raise SystemExit('encoder mismatch with trained model')
    if meta.get('window_semantics') != 'time-aligned-v2':
        raise SystemExit('legacy P1 checkpoint affected by D33; retrain before research evaluation')
    validate_feature_identity(meta, encoder, a.encode_batch)

    conditions = {}
    for entry in a.conditions.split(','):
        name, dataset_path, split = entry.split(':')
        conditions[name] = dataset_path, split
    if a.nominal not in conditions:
        raise SystemExit('--nominal must name one of --conditions')

    started = time.time()
    variant_names = ['V0_frozen', 'V4_robot', 'V4_both', 'V5_delay', 'V6_delay_gain']
    report = dict(nominal=a.nominal, conditions={}, ema_alpha=a.ema_alpha, delays=list(DELAYS))
    frozen_total = {}
    for name, (dataset_path, split) in conditions.items():
        ds, feats = encode_condition(dataset_path, split, encoder, a.cache_dir, a.encode_batch)
        episodes = list(range(len(ds.episodes)))
        torch.manual_seed(a.seed)
        frozen = {i: episode_errors(model, feats, ds, i, norm, a.device, lr=None, k=None) for i in episodes}
        by_variant = {}
        diag_by_variant = {}
        for vname, mode in zip(variant_names[1:], ['V4_robot', 'V4_both', 'V5', 'V6']):
            rows, diags = {}, {}
            for i in episodes:
                r, d = episode_replay(model, feats, ds, i, norm, a.device, mode, a.ema_alpha)
                rows[i], diags[i] = r, d
            by_variant[vname] = rows
            diag_by_variant[vname] = diags
        frozen_mean = float(np.mean([episode_mean(frozen[i]) for i in episodes]))
        frozen_total[name] = frozen_mean
        cond = dict(episodes=len(episodes), frozen_mean=frozen_mean, variants={})
        true_gain, true_delay = parse_condition_name(name)
        for vname in variant_names[1:]:
            rows = by_variant[vname]
            variant_mean = float(np.mean([episode_mean(rows[i]) for i in episodes]))
            diff = paired_summary(rows, frozen, episodes, ds.seeds, 'total', None)
            entry = dict(mean=variant_mean, variant_minus_frozen=diff)
            if vname in ('V4_robot', 'V4_both'):
                final_s = [diag_by_variant[vname][i][-1] for i in episodes if diag_by_variant[vname][i]]
                entry['final_gain_estimate_mean'] = float(np.mean(final_s)) if final_s else None
                if true_gain is not None and len(final_s) > 1 and np.std(final_s) > 0:
                    entry['gain_estimate_correlation_with_true_gain_note'] = (
                        'single-condition run: true gain is constant within this condition, '
                        'so within-condition correlation is undefined; see cross-condition summary')
            if vname in ('V5_delay', 'V6_delay_gain'):
                final_d = [diag_by_variant[vname][i][-1] for i in episodes if diag_by_variant[vname][i]]
                entry['final_delay_selected_mode'] = int(np.bincount(final_d).argmax()) if final_d else None
                if true_delay is not None and final_d:
                    entry['delay_match_rate'] = float(np.mean(np.asarray(final_d) == true_delay))
            cond['variants'][vname] = entry
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

    # D50 pass/fail (predetermined, not re-derived): >=1 variant with recovery_fraction>=0.30 and
    # paired CI upper<0 on >=2 of the four designated strong conditions, and that same variant's
    # nominal variant_minus_frozen mean <= 1% of the nominal frozen residual (not meaningfully worse).
    strong_conditions = ['gain1.4_delay0', 'gain1.8_delay0', 'gain1.4_delay5', 'gain1.0_delay5']
    d50 = {}
    for vname in variant_names[1:]:
        qualifying = 0
        for cname in strong_conditions:
            if cname not in report['conditions']:
                continue
            entry = report['conditions'][cname]['variants'][vname]
            if entry['recovery_fraction'] is not None and entry['recovery_fraction'] >= 0.30 and entry['variant_minus_frozen']['ci95'][1] < 0:
                qualifying += 1
        nominal_entry = report['conditions'][a.nominal]['variants'][vname]
        nominal_ok = nominal_entry['variant_minus_frozen']['mean'] <= 0.01 * nominal_frozen
        d50[vname] = dict(qualifying_strong_conditions=qualifying, nominal_not_worse=bool(nominal_ok),
                           passes_d50=bool(qualifying >= 2 and nominal_ok))
    report['d50'] = d50
    report['d50_pass'] = bool(any(v['passes_d50'] for v in d50.values()))
    report['seconds'] = time.time() - started
    out.mkdir(parents=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(nominal=a.nominal, d50_pass=report['d50_pass'], seconds=report['seconds']), indent=2))


if __name__ == '__main__':
    main()
