"""SCREEN-028 analyses (D53 L1/L2/L3, D54 D-line). One function per stage, each writing

    <analysis_dir>/point.json    point estimates only (written FIRST)
    <analysis_dir>/result.json   point estimates + bootstrap CIs + pre-registered verdicts

so a timeout or crash during the CI step can never lose the point estimates (FOLLOWUP-028's S4 did).
Arms with missing/incomplete episodes are reported as unavailable, never silently imputed.
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np

import screen_stats as st

L1_ARMS = [('nominal', None, 0), ('full1', 'full', 1), ('full2', 'full', 2), ('full3', 'full', 3), ('full5', 'full', 5),
           ('map2', 'map', 2), ('map5', 'map', 5)]
TRAIN_SEEDS = (11, 22)


def _dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True))


def eval_seeds_from(lo, hi):
    return list(range(lo, hi))


def arm_rows(stage_dir, arm):
    path = Path(stage_dir) / arm / 'episodes.jsonl'
    return st.load_rows(path) if path.exists() else None


def describe_arm(rows, seeds):
    """Point-estimate block for one arm. Returns None if any seed is missing."""
    if rows is None or any(s not in rows for s in seeds):
        return None
    f = st.episode_flags(rows, seeds)
    return dict(n=len(seeds), success_rate=float(f['success'].mean()), perfect_success_rate=float(f['perfect'].mean()),
                collision_episode_fraction=float(f['collision'].mean()), ik_failure_episode_fraction=float(f['ik'].mean()),
                exceptions=int(f['exception'].sum()),
                failure_distribution=dict(Counter(rows[s].get('primary_reason', 'unknown') for s in seeds)),
                mean_steps=float(np.mean([rows[s].get('steps', 0) for s in seeds])))


def _success(stage_dir, arm, seeds):
    rows = arm_rows(stage_dir, arm)
    return None if rows is None or any(s not in rows for s in seeds) else st.flags(rows, seeds)


# ---------------------------------------------------------------------------
# L1
# ---------------------------------------------------------------------------

def analyze_l1(stage_dir, seeds, analysis_dir, n_boot=st.N_BOOT):
    stage_dir, analysis_dir = Path(stage_dir), Path(analysis_dir)
    arms = {name: describe_arm(arm_rows(stage_dir, name), seeds) for name, _, _ in L1_ARMS}
    nominal = arms['nominal']
    point = dict(seeds=[seeds[0], seeds[-1]], n=len(seeds), arms=arms)
    if nominal:
        for name, kind, k in L1_ARMS[1:]:
            if arms[name]:
                arms[name]['delta_vs_nominal'] = arms[name]['success_rate'] - nominal['success_rate']
    _dump(analysis_dir / 'point.json', point)                     # 1) points first
    passes = dict(full={}, map={})
    result = dict(point, criterion='D53-L1: SR drop >= 0.15 and paired CI upper bound < 0', n_boot=n_boot)
    nominal_flags = _success(stage_dir, 'nominal', seeds)
    for name, kind, k in L1_ARMS[1:]:
        flags = _success(stage_dir, name, seeds)
        if flags is None or nominal_flags is None:
            arms[name] = arms[name] or dict(unavailable=True)
            passes[kind][k] = False
            arms[name]['passes_l1'] = False
            continue
        diff = st.diff_with_ci(flags, nominal_flags, n_boot=n_boot, seed=k)
        arms[name]['delta_ci95'] = diff['ci95']
        arms[name]['passes_l1'] = st.l1_config_passes(diff['point'], diff['ci95'])
        passes[kind][k] = arms[name]['passes_l1']
    result['decision'] = st.l1_decision(passes)
    result['passes'] = {kind: {str(k): v for k, v in d.items()} for kind, d in passes.items()}
    _dump(analysis_dir / 'result.json', result)
    return result


# ---------------------------------------------------------------------------
# L2 / D2: stratified (training seed x episode) comparisons over per-seed arm families
# ---------------------------------------------------------------------------

def _family(stage_dir, template, seeds, train_seeds=TRAIN_SEEDS):
    """Stack per-training-seed success arrays into (S,N); None if any is unavailable."""
    stacks = [_success(stage_dir, template % s, seeds) for s in train_seeds]
    return None if any(x is None for x in stacks) else np.stack(stacks)


def _family_point(stage_dir, template, seeds, train_seeds=TRAIN_SEEDS):
    per_seed = {str(s): describe_arm(arm_rows(stage_dir, template % s), seeds) for s in train_seeds}
    if any(v is None for v in per_seed.values()):
        return dict(per_seed=per_seed, pooled=None)
    pooled = {key: float(np.mean([v[key] for v in per_seed.values()]))
              for key in ('success_rate', 'perfect_success_rate', 'collision_episode_fraction', 'ik_failure_episode_fraction')}
    return dict(per_seed=per_seed, pooled=pooled)


def analyze_l2(stage_dir, seeds, analysis_dir, k_sel, mode, n_boot=st.N_BOOT):
    arms = {'L-oracle': 'L-oracle-s%d', 'L-stale': 'L-stale-s%d', 'L-hist': 'L-hist-s%d'}
    return _analyze_headroom(stage_dir, seeds, analysis_dir, arms, n_boot,
                             extra=dict(k_sel=k_sel, latency_mode=mode, criterion=(
                                 'D53-L2: SR(L-oracle)-SR(L-hist) >= 0.10 and CI lower bound > 0, and '
                                 'SR(L-oracle)-SR(L-stale) CI lower bound > 0')),
                             pairs=[('oracle_minus_hist', 'L-oracle', 'L-hist'), ('oracle_minus_stale', 'L-oracle', 'L-stale')],
                             verdict_fn=_l2_verdict)


def _l2_verdict(diffs):
    hist, stale = diffs.get('oracle_minus_hist'), diffs.get('oracle_minus_stale')
    if not hist or not stale:
        return dict(passes=None, reason='arms incomplete')
    c1 = st.headroom_passes(hist['point'], hist['ci95'])
    c2 = st.lower_bound_positive(stale['ci95'])
    return dict(passes=bool(c1 and c2), oracle_minus_hist_ok=c1, oracle_minus_stale_ok=c2)


def analyze_d(stage_dir, seeds, analysis_dir, n_boot=st.N_BOOT):
    arms = {'D-std': 'D-std-s%d', 'D-stdfrozen': 'D-stdfrozen-s%d', 'D-oracle': 'D-oracle-s%d', 'D-hist': 'D-hist-s%d'}
    return _analyze_headroom(stage_dir, seeds, analysis_dir, arms, n_boot,
                             extra=dict(criterion=(
                                 'D54-harm: SR(D-std frozen)-SR(D-std moving) >= 0.15 and CI lower bound > 0; '
                                 'D54-headroom: SR(D-oracle)-SR(D-hist) >= 0.10 and CI lower bound > 0, and '
                                 'SR(D-oracle)-SR(D-std) CI lower bound > 0; both required')),
                             pairs=[('frozen_minus_moving', 'D-stdfrozen', 'D-std'), ('oracle_minus_hist', 'D-oracle', 'D-hist'),
                                    ('oracle_minus_std', 'D-oracle', 'D-std')],
                             verdict_fn=_d_verdict)


def _d_verdict(diffs, points=None):
    harm, hist, std = diffs.get('frozen_minus_moving'), diffs.get('oracle_minus_hist'), diffs.get('oracle_minus_std')
    out = dict(harm=None, headroom=None, passes=None)
    if harm:
        out['harm'] = bool(harm['point'] >= 0.15 and harm['ci95'][0] > 0)
    if hist and std:
        out['headroom'] = bool(st.headroom_passes(hist['point'], hist['ci95']) and st.lower_bound_positive(std['ci95']))
    if out['harm'] is not None and out['headroom'] is not None:
        out['passes'] = bool(out['harm'] and out['headroom'])
    return out


def _analyze_headroom(stage_dir, seeds, analysis_dir, arms, n_boot, extra, pairs, verdict_fn):
    stage_dir, analysis_dir = Path(stage_dir), Path(analysis_dir)
    families = {label: _family_point(stage_dir, template, seeds) for label, template in arms.items()}
    point = dict(extra, seeds=[seeds[0], seeds[-1]], n=len(seeds), train_seeds=list(TRAIN_SEEDS), arms=families, point_diffs={})
    stacks = {label: _family(stage_dir, template, seeds) for label, template in arms.items()}
    for name, a, b in pairs:
        if stacks[a] is not None and stacks[b] is not None:
            point['point_diffs'][name] = st.point_diff(stacks[a], stacks[b])
    _dump(analysis_dir / 'point.json', point)                     # 1) points first
    diffs = {}
    for i, (name, a, b) in enumerate(pairs):
        if stacks[a] is not None and stacks[b] is not None:
            diffs[name] = st.diff_with_ci(stacks[a], stacks[b], n_boot=n_boot, seed=i)
    result = dict(point, diffs=diffs, n_boot=n_boot, verdict=verdict_fn(diffs))
    std_moving = families.get('D-std', {}).get('pooled') if 'D-std' in families else None
    if std_moving is not None:
        result['d_std_moving_success_rate'] = std_moving['success_rate']
        result['task_too_hard_warning'] = bool(std_moving['success_rate'] < 0.2)
    _dump(analysis_dir / 'result.json', result)
    return result


# ---------------------------------------------------------------------------
# L3 (exploratory)
# ---------------------------------------------------------------------------

def analyze_l3(l1_dir, l3_dir, seeds, analysis_dir, stale_arm, n_boot=st.N_BOOT):
    l1_dir, l3_dir, analysis_dir = Path(l1_dir), Path(l3_dir), Path(analysis_dir)
    nominal = _success(l1_dir, 'nominal', seeds)
    stale = _success(l1_dir, stale_arm, seeds)
    comp = _success(l3_dir, 'wm-comp', seeds)
    point = dict(seeds=[seeds[0], seeds[-1]], n=len(seeds), stale_arm=stale_arm, exploratory=True,
                 arms=dict(nominal=describe_arm(arm_rows(l1_dir, 'nominal'), seeds),
                           stale=describe_arm(arm_rows(l1_dir, stale_arm), seeds),
                           wm_comp=describe_arm(arm_rows(l3_dir, 'wm-comp'), seeds)))
    if nominal is not None and stale is not None and comp is not None:
        gap = float(nominal.mean() - stale.mean())
        point['sr_gap_nominal_minus_stale'] = gap
        point['sr_wm_minus_stale'] = float(comp.mean() - stale.mean())
        point['recovery_ratio'] = float((comp.mean() - stale.mean()) / gap) if gap > 0 else None
    _dump(analysis_dir / 'point.json', point)                     # 1) points first
    result = dict(point, n_boot=n_boot)
    if nominal is not None and stale is not None and comp is not None:
        result['wm_minus_stale'] = st.diff_with_ci(comp, stale, n_boot=n_boot, seed=0)
        result['recovery'] = st.recovery_ratio(nominal, stale, comp, n_boot=n_boot, seed=1)
    _dump(analysis_dir / 'result.json', result)
    return result
