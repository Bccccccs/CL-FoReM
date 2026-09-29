"""PH3-OBSMAP diagnostics (D60) and PH4.1 analysis (D62). Thresholds below are pre-registered and NOT tunable.

  D60 (PH3, diagnostic only since D62)  for each r in {10, 5, 3}: SR(r) - SR(nominal) <= -0.15 AND the 95% paired
        episode-bootstrap CI (10000 resamples, seed 0) of the difference has an upper bound < 0  ->  "harm passes".
        The nominal arm must reproduce R0-3c (SR 0.70; same device => trajectory_sha256 identical per episode).
  D62 (PH4.1)  for each r in {3, 5} separately: SR(G-std) - SR(K-std-r) >= 0.10 AND the lower bound of the 95%
        "training seed x episode" stratified bootstrap CI (10000, seed 0) of that difference > 0, AND
        SR(K-std-r) >= SR(random, r) + 0.30 (point estimate).  r_sel = the largest r that passes.
        G-std = {policy-100k (seed 11, = PH3 nominal arm, global), G-std-s22}; K-std-r = {seed 11, seed 22}.
        The stratified reading is the one used by CEIL-028 (strata = training seeds, same episode indices for both
        arms, the two seeds pair G seed 11 <-> K seed 11 and G seed 22 <-> K seed 22).

  D64 (convergence check, supplements D62)  two extra 300k-step runs K-std-r3-long / K-std-r5-long (seed 11): for each r the
        4.1 result additionally needs SR(G-std) - SR(K-std-r-long) >= 0.10 (POINT estimate is the criterion; the episode
        bootstrap CI is reported only). Not met -> "under-trained, not passed" at that r. The final 4.1 verdict waits for the long
        runs; the 100k part is reported first as an interim result. Learning curves (20k-step / 50k-step checkpoints) are diagnostic.

Point estimates are always written to disk (point.json) before any bootstrap runs.
"""
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np

import screen_analysis as sa
import screen_stats as st

D60_DROP = 0.15
D62_GAP = 0.10
D62_RANDOM_MARGIN = 0.30
PH3_ARMS = ('nominal', 'r10', 'r5', 'r3')
PH3_RADII = {'r10': 10.0, 'r5': 5.0, 'r3': 3.0}
PH4_RADII = {'r3': 3.0, 'r5': 5.0}
TRAIN_SEEDS = (11, 22)
EPS = 1e-12


def k_arm(r_key, seed):
    return 'K-std-%s-s%d' % (r_key, seed)


G_ARM_S22 = 'G-std-s22'
LONG_SEED = 11
JOB_STEPS = dict(short=100000, long=300000)
CURVE_INTERVAL = dict(short=20000, long=50000)


def configure_schedule(short_steps, short_interval, long_steps, long_interval):
    """Registered values are the defaults; the pipeline smoke test shrinks them."""
    JOB_STEPS.update(short=short_steps, long=long_steps)
    CURVE_INTERVAL.update(short=short_interval, long=long_interval)


def long_arm(r_key):
    return 'K-std-%s-long' % r_key


def curve_arm(job, step):
    return 'curve-%s-step%07d' % (job, step)


def job_names():
    out = ['G-std-s22']
    for rk in PH4_RADII:
        out += [k_arm(rk, s) for s in TRAIN_SEEDS] + [long_arm(rk)]
    return out


def job_kind(name):
    return 'long' if name.endswith('-long') else 'short'


def curve_steps(name):
    kind = job_kind(name)
    return list(range(CURVE_INTERVAL[kind], JOB_STEPS[kind] + 1, CURVE_INTERVAL[kind]))


def random_arm(r_key):
    return 'random-%s' % r_key


# ---------------------------------------------------------------------------------------------- reroute statistics

def reroute_stats(rows, seeds):
    """Pooled reroute statistics over the episodes that carry `obsmap_*` fields (D60 'must report')."""
    have = [rows[s] for s in seeds if s in rows and 'obsmap_reroute_count' in rows[s]]
    if not have:
        return None
    counts = np.array([r['obsmap_reroute_count'] for r in have], dtype=np.float64)
    total = float(counts.sum())
    ik_hits = col_hits = 0.0
    for r in have:
        n = r['obsmap_reroute_count']
        if n:
            ik_hits += r['obsmap_post_reroute_ik_rate'] * n       # rate = hits / n  ->  hits recovered exactly
            col_hits += r['obsmap_post_reroute_collision_rate'] * n
    ok = [r for r in have if r.get('success')]
    bad = [r for r in have if not r.get('success')]
    fr = [r['obsmap_observed_fraction_final'] for r in have if r.get('obsmap_observed_fraction_final') is not None]
    return dict(
        episodes=len(have), reroutes_total=int(total), reroutes_per_episode_mean=float(counts.mean()),
        reroutes_per_episode_max=int(counts.max()), episodes_with_reroute=float((counts > 0).mean()),
        reroute_count_distribution={str(k): v for k, v in sorted(Counter(int(c) for c in counts).items())},
        reroute_dist_max_m=float(max([max(r['obsmap_reroute_dists']) for r in have if r['obsmap_reroute_dists']] or [0.0])),
        post_reroute_ik_rate=(ik_hits / total) if total else None,
        post_reroute_collision_rate=(col_hits / total) if total else None,
        reroutes_per_episode_success=float(np.mean([r['obsmap_reroute_count'] for r in ok])) if ok else None,
        reroutes_per_episode_failed=float(np.mean([r['obsmap_reroute_count'] for r in bad])) if bad else None,
        weight_updates_per_episode_mean=float(np.mean([r['obsmap_weight_updates'] for r in have])),
        observed_fraction_final_mean=float(np.mean(fr)) if fr else None,
        obsmap_seconds_per_step_mean=float(np.mean([r['obsmap_seconds_mean'] for r in have])))


# ---------------------------------------------------------------------------------------------- PH3 (D60)

def load_rows_or_none(path):
    path = Path(path)
    return st.load_rows(path) if path.exists() else None


def ph3_points(ph3_dir, seeds, baseline_dir=None):
    ph3_dir = Path(ph3_dir)
    out = dict(eval_seeds=[seeds[0], seeds[-1]], n_episodes=len(seeds), arms={}, reroutes={})
    rows = {a: sa.arm_rows(ph3_dir, a) for a in PH3_ARMS}
    for a in PH3_ARMS:
        out['arms'][a] = sa.describe_arm(rows[a], seeds)
        out['reroutes'][a] = reroute_stats(rows[a], seeds) if rows[a] else None
    nominal = out['arms']['nominal']
    out['diffs_point'] = {}
    for a in PH3_RADII:
        if nominal and out['arms'][a]:
            out['diffs_point'][a] = dict(success=out['arms'][a]['success_rate'] - nominal['success_rate'],
                                         perfect=out['arms'][a]['perfect_success_rate'] - nominal['perfect_success_rate'],
                                         point_meets_drop=bool(out['arms'][a]['success_rate'] - nominal['success_rate'] <= -D60_DROP + EPS))
    base_rows = load_rows_or_none(Path(baseline_dir) / 'episodes.jsonl') if baseline_dir else None
    if base_rows and rows['nominal'] and all(s in rows['nominal'] and s in base_rows for s in seeds):
        same = sum(rows['nominal'][s].get('trajectory_sha256') == base_rows[s].get('trajectory_sha256') for s in seeds)
        base_sr = float(np.mean([bool(base_rows[s].get('success')) for s in seeds]))
        out['nominal_reproduction'] = dict(
            reference=str(baseline_dir), reference_sr=base_sr, nominal_sr=nominal['success_rate'] if nominal else None,
            trajectory_sha256_identical=int(same), episodes=len(seeds),
            success_flags_identical=int(sum(bool(rows['nominal'][s].get('success')) == bool(base_rows[s].get('success')) for s in seeds)),
            reproduces=bool(same == len(seeds)))
    else:
        out['nominal_reproduction'] = None
    return out


def ph3_add_cis(ph3_dir, seeds, points, n_boot=st.N_BOOT):
    result = json.loads(json.dumps(points))
    rows = {a: sa.arm_rows(ph3_dir, a) for a in PH3_ARMS}
    if not all(rows[a] and all(s in rows[a] for s in seeds) for a in PH3_ARMS):
        return result
    nom = st.flags(rows['nominal'], seeds)
    nom_p = st.flags(rows['nominal'], seeds, 'perfect_success')
    for a in PH3_RADII:
        d = st.diff_with_ci(st.flags(rows[a], seeds), nom, n_boot=n_boot, seed=0)
        dp = st.diff_with_ci(st.flags(rows[a], seeds, 'perfect_success'), nom_p, n_boot=n_boot, seed=0)
        result['diffs_point'][a].update(success_ci95=d['ci95'], perfect_ci95=dp['ci95'], n_boot=n_boot,
                                        harm_passes=bool(d['point'] <= -D60_DROP + EPS and d['ci95'][1] < 0))
    passing = sorted((PH3_RADII[a] for a in PH3_RADII if result['diffs_point'][a].get('harm_passes')), reverse=True)
    result['d60'] = dict(passing_radii=passing, r_largest_passing=passing[0] if passing else None,
                         note='diagnostic only (D62): it no longer decides whether to train or which r to use')
    return result


def analyze_ph3(ph3_dir, seeds, baseline_dir, n_boot=st.N_BOOT, on_points=None):
    ph3_dir = Path(ph3_dir)
    points = ph3_points(ph3_dir, seeds, baseline_dir)
    sa._dump(ph3_dir / 'analysis-point.json', points)
    if on_points:
        on_points(points)
    result = ph3_add_cis(ph3_dir, seeds, points, n_boot=n_boot)
    sa._dump(ph3_dir / 'analysis.json', result)
    return points, result


# ---------------------------------------------------------------------------------------------- PH4.1 (D62)

def ph4_points(ph3_dir, ph4_dir, seeds):
    """Points per arm. G-std seed 11 is policy-100k = the PH3 nominal arm (global planner, identical episodes)."""
    ph3_dir, ph4_dir = Path(ph3_dir), Path(ph4_dir)
    ev = ph4_dir / 's3-eval'
    arms = {'G-std-s11(policy-100k)': sa.describe_arm(sa.arm_rows(ph3_dir, 'nominal'), seeds), G_ARM_S22: sa.describe_arm(sa.arm_rows(ev, G_ARM_S22), seeds)}
    reroutes = {}
    for rk in PH4_RADII:
        for s in TRAIN_SEEDS:
            name = k_arm(rk, s)
            rows = sa.arm_rows(ev, name)
            arms[name] = sa.describe_arm(rows, seeds)
            reroutes[name] = reroute_stats(rows, seeds) if rows else None
        rows = sa.arm_rows(ev, random_arm(rk))
        arms[random_arm(rk)] = sa.describe_arm(rows, seeds)
        reroutes[random_arm(rk)] = reroute_stats(rows, seeds) if rows else None
    for rk in PH4_RADII:
        rows = sa.arm_rows(ev, long_arm(rk))
        arms[long_arm(rk)] = sa.describe_arm(rows, seeds)
        reroutes[long_arm(rk)] = reroute_stats(rows, seeds) if rows else None
    out = dict(eval_seeds=[seeds[0], seeds[-1]], n_episodes=len(seeds), arms=arms, reroutes=reroutes, per_r={})
    g = [arms['G-std-s11(policy-100k)'], arms[G_ARM_S22]]
    for rk in PH4_RADII:
        k = [arms[k_arm(rk, s)] for s in TRAIN_SEEDS]
        rnd = arms[random_arm(rk)]
        if all(g) and all(k):
            sr_g = float(np.mean([x['success_rate'] for x in g]))
            sr_k = float(np.mean([x['success_rate'] for x in k]))
            d = dict(sr_g=sr_g, sr_k=sr_k, gap=sr_g - sr_k, gap_threshold=D62_GAP, gap_point_passes=bool(sr_g - sr_k >= D62_GAP - EPS),
                     per_seed_gap={str(s): g[i]['success_rate'] - k[i]['success_rate'] for i, s in enumerate(TRAIN_SEEDS)})
            if rnd:
                d.update(sr_random=rnd['success_rate'], k_minus_random=sr_k - rnd['success_rate'], random_margin=D62_RANDOM_MARGIN,
                         random_passes=bool(sr_k - rnd['success_rate'] >= D62_RANDOM_MARGIN - EPS))
            kl = arms[long_arm(rk)]
            if kl:
                d.update(sr_k_long=kl['success_rate'], gap_long=sr_g - kl['success_rate'],
                         long_passes=bool(sr_g - kl['success_rate'] >= D62_GAP - EPS))
            out['per_r'][rk] = d
    out['curves'] = ph4_curves(ph4_dir, seeds)
    return out


def ph4_curves(ph4_dir, seeds):
    """Diagnostic learning curves: SR per checkpoint (100 deterministic episodes, own training condition)."""
    ev, cv = Path(ph4_dir) / 's3-eval', Path(ph4_dir) / 's6-curves'
    out = {}
    for name in job_names():
        steps = curve_steps(name)
        row = {}
        for step in steps:
            arm_dir, arm = (ev, name) if step == steps[-1] else (cv, curve_arm(name, step))
            d = sa.describe_arm(sa.arm_rows(arm_dir, arm), seeds)
            row[str(step)] = None if d is None else dict(success_rate=d['success_rate'], perfect_success_rate=d['perfect_success_rate'])
        out[name] = row
    return out


def ph4_add_cis(ph3_dir, ph4_dir, seeds, points, n_boot=st.N_BOOT):
    result = json.loads(json.dumps(points))
    ev = Path(ph4_dir) / 's3-eval'
    g_rows = [sa.arm_rows(Path(ph3_dir), 'nominal'), sa.arm_rows(ev, G_ARM_S22)]
    for rk, d in result['per_r'].items():
        k_rows = [sa.arm_rows(ev, k_arm(rk, s)) for s in TRAIN_SEEDS]
        G = np.stack([st.flags(r, seeds) for r in g_rows])
        K = np.stack([st.flags(r, seeds) for r in k_rows])
        pooled = st.diff_with_ci(G, K, n_boot=n_boot, seed=0)
        d['gap_ci95'] = pooled['ci95']
        d['n_boot'] = n_boot
        d['gap_passes'] = bool(d['gap_point_passes'] and pooled['ci95'][0] > 0)
        for i, s in enumerate(TRAIN_SEEDS):
            d['per_seed_gap_ci95_descriptive'] = d.get('per_seed_gap_ci95_descriptive', {})
            d['per_seed_gap_ci95_descriptive'][str(s)] = st.diff_with_ci(G[i], K[i], n_boot=n_boot, seed=1 + i)['ci95']
        rand_rows = sa.arm_rows(ev, random_arm(rk))
        if rand_rows and all(s in rand_rows for s in seeds):
            R = np.tile(st.flags(rand_rows, seeds), (len(TRAIN_SEEDS), 1))
            d['k_minus_random_ci95_descriptive'] = st.diff_with_ci(K, R, n_boot=n_boot, seed=3)['ci95']
        d['passes_100k'] = bool(d['gap_passes'] and d.get('random_passes', False))     # D62 alone (interim)
        long_rows = sa.arm_rows(ev, long_arm(rk))
        if 'long_passes' in d and long_rows and all(s in long_rows for s in seeds):
            KL = np.tile(st.flags(long_rows, seeds), (len(TRAIN_SEEDS), 1))
            d['gap_long_ci95_descriptive'] = st.diff_with_ci(G, KL, n_boot=n_boot, seed=4)['ci95']   # not a criterion (1 seed)
            d['passes'] = bool(d['passes_100k'] and d['long_passes'])                                # D62 + D64
            d['not_passed_reason'] = None if d['passes'] else (
                'under-trained: SR(G-std) - SR(K-std-r-long) < 0.10' if d['passes_100k'] else 'D62 100k criteria not met')
    ordered = sorted(PH4_RADII, key=lambda rk: -PH4_RADII[rk])
    interim = [PH4_RADII[rk] for rk in ordered if rk in result['per_r'] and result['per_r'][rk].get('passes_100k')]
    passing = [PH4_RADII[rk] for rk in ordered if rk in result['per_r'] and result['per_r'][rk].get('passes')]
    complete100 = len(result['per_r']) == len(PH4_RADII) and all('random_passes' in d for d in result['per_r'].values())
    complete = complete100 and all('passes' in d for d in result['per_r'].values())
    if not complete100:
        outcome = 'incomplete data'
    elif not complete:
        outcome = ('interim (100k runs only): D62 passes at r = %s; final 4.1 verdict waits for the 300k runs' % (interim or 'none'))
    elif passing:
        outcome = 'r_sel = %g m' % passing[0]
    else:
        outcome = ('no radius passes (see per-r reasons): stop and discuss with the user'
                   if not interim else 'D62 passed at r = %s on 100k but the 300k check shows under-training: 4.1 not passed there; stop and discuss with the user' % interim)
    result['d62'] = dict(interim_passing_radii=interim, interim_r_sel=interim[0] if interim else None,
                         passing_radii=passing, r_sel=passing[0] if passing else None, complete=complete, complete_100k=complete100, outcome=outcome)
    return result


def analyze_ph4(ph3_dir, ph4_dir, seeds, n_boot=st.N_BOOT, on_points=None):
    ph4_dir = Path(ph4_dir)
    points = ph4_points(ph3_dir, ph4_dir, seeds)
    sa._dump(ph4_dir / 'point.json', points)
    if on_points:
        on_points(points)
    result = ph4_add_cis(ph3_dir, ph4_dir, seeds, points, n_boot=n_boot)
    sa._dump(ph4_dir / 'analysis.json', result)
    return points, result


# ---------------------------------------------------------------------------------------------- reports

def _f(x, nd=2):
    return '—' if x is None else '%.*f' % (nd, x)


HEADER = ('| 臂 | 回合 | SR | perfect | IK失败回合比例 | 碰撞回合比例 | 平均步数 | 异常 | 结束原因 |\n|---|---|---|---|---|---|---|---|---|')


def arm_row(name, d):
    if d is None:
        return '| %s | （数据不全） | | | | | | | |' % name
    fd = ', '.join('%s %d' % (k, v) for k, v in sorted(d['failure_distribution'].items()))
    return '| %s | %d | %s | %s | %s | %s | %.0f | %d | %s |' % (
        name, d['n'], _f(d['success_rate']), _f(d['perfect_success_rate']), _f(d['ik_failure_episode_fraction']),
        _f(d['collision_episode_fraction']), d['mean_steps'], d['exceptions'], fd)


def reroute_table(reroutes, names):
    L = ['| 配置 | 有改道的回合比例 | 平均每回合改道 | 最多 | 改道后20步内 IK 失败率 | 改道后20步内碰撞率 | 成功回合平均改道 | 失败回合平均改道 | 每回合重算权重 | 回合末已观测占比 | 扫描+重算 每步(ms) |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    for n in names:
        r = reroutes.get(n)
        if not r:
            L.append('| %s | — | | | | | | | | | |' % n)
            continue
        L.append('| %s | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |' % (
            n, _f(r['episodes_with_reroute']), _f(r['reroutes_per_episode_mean']), r['reroutes_per_episode_max'],
            _f(r['post_reroute_ik_rate']), _f(r['post_reroute_collision_rate']), _f(r['reroutes_per_episode_success']),
            _f(r['reroutes_per_episode_failed']), _f(r['weight_updates_per_episode_mean'], 1), _f(r['observed_fraction_final_mean']),
            _f(1000 * r['obsmap_seconds_per_step_mean'], 1)))
    return L


def build_ph3_report(points, result=None, final=False, extra_links=None):
    result = result if result is not None else points
    L = ['# PH3-OBSMAP 诊断报告：规划器只用已观测地图（policy-100k，未重训）', '',
         '- 生成：%s；%s' % (time.strftime('%Y-%m-%dT%H:%M:%S%z'), '**终稿（含 CI 与 D60 判定）**' if final else '**点估计草稿（CI 待计算）**'),
         '- 依据：D60（判据不变），D62 起本任务只作**诊断**，不再是关卡，也不再用于选 r。设计见 [设计说明](20260929-ph3-obsmap-spec.md)，运行记录见 [任务日志](20260929-ph3-obsmap.md)。',
         '- 评测：simpleobstacle，policy-100k（`results/p1a-20260923/policy-100k.pt`）确定性，`--ik-mode fixed --ik-iterations 100`，种子 %d–%d 共 %d 回合，同种子配对；'
         '视角 270°、遮挡高度 0.5 m；名义 = 全局地图规划器 + `--obsmap-log-reroutes`（只记录改道，不改规划）。' % (
             points['eval_seeds'][0], points['eval_seeds'][1], points['n_episodes']), '']
    L += ['## 各配置结果', '', HEADER]
    for a in PH3_ARMS:
        L.append(arm_row('名义（全局）' if a == 'nominal' else 'r=%g m' % PH3_RADII[a], points['arms'][a]))
    nr = points.get('nominal_reproduction')
    L += ['', '### 名义复现（R0-3c）', '']
    if nr:
        L.append('名义 SR = %s，R0-3c 名义 SR = %s；逐回合 `trajectory_sha256` 一致 %d/%d，成败一致 %d/%d → **%s**。' % (
            _f(nr['nominal_sr']), _f(nr['reference_sr']), nr['trajectory_sha256_identical'], nr['episodes'], nr['success_flags_identical'],
            nr['episodes'], '复现' if nr['reproduces'] else '哈希不完全一致（如实记录；若设备不同，浮点差异会使哈希不同）'))
    else:
        L.append('数据不全，无法核对。')
    L += ['', '## D60 判定（每个 r 相对名义）', '',
          '| 配置 | SR 差（点估计） | SR 差 95% CI | perfect 差（诊断） | perfect 差 95% CI | 点估计 ≤ −0.15 | 伤害通过（点估计且 CI 上界<0） |', '|---|---|---|---|---|---|---|']
    for a in PH3_RADII:
        d = result['diffs_point'].get(a)
        if not d:
            L.append('| r=%g m | — | | | | | |' % PH3_RADII[a])
            continue
        ci = d.get('success_ci95')
        pci = d.get('perfect_ci95')
        L.append('| r=%g m | %+.3f | %s | %+.3f | %s | %s | %s |' % (
            PH3_RADII[a], d['success'], '[%.3f, %.3f]' % tuple(ci) if ci else '待计算', d['perfect'],
            '[%.3f, %.3f]' % tuple(pci) if pci else '待计算', '是' if d['point_meets_drop'] else '否',
            ('**通过**' if d.get('harm_passes') else '**不通过**') if ci else '待定'))
    d60 = result.get('d60')
    if d60:
        L += ['', '通过的 r：%s；%s。' % (d60['passing_radii'] or '无', d60['note'])]
    L += ['', '## 改道统计（>0.3 m 记一次改道；改道后 20 步内的 IK 失败/底盘碰撞）', '']
    L += reroute_table(points['reroutes'], PH3_ARMS)
    L += ['', '说明：改道 = 相邻两步规划器完整 A* 路径的有向最大偏离 > 0.3 m；改道后窗口取改道后第 1..20 步；两个改道后比率按改道次数加权汇总；'
              '名义配置的改道来自规划起点（EE 参考点）移动本身，是“全局模式下的改道基准”。', '']
    if extra_links:
        L += extra_links
    return '\n'.join(L)


def curve_table(curves):
    L = ['| 训练任务 | 检查点（k 步）→ SR（100 回合，确定性，自身训练条件） | 末 3 点极差 | 末点相对前一点 |', '|---|---|---|---|']
    for name, row in curves.items():
        steps = curve_steps(name)
        cells = ['%gk: %s' % (st_ / 1000, '—' if row.get(str(st_)) is None else '%.2f' % row[str(st_)]['success_rate']) for st_ in steps]
        vals = [row[str(x)]['success_rate'] for x in steps if row.get(str(x)) is not None]
        last3 = vals[-3:]
        rng = _f(max(last3) - min(last3)) if len(last3) == 3 else '—'
        delta = ('%+.2f' % (vals[-1] - vals[-2])) if len(vals) >= 2 and row.get(str(steps[-1])) is not None else '—'
        L.append('| %s | %s | %s | %s |' % (name, '；'.join(cells), rng, delta))
    return L


def build_ph4_report(points, result=None, final=False, training=None):
    result = result if result is not None else points
    d62 = result.get('d62')
    is_final = final and bool(d62 and d62.get('complete'))
    L = ['# PH4.1 报告：非全局（已观测地图）下重训 SAC', '',
         '- 生成：%s；%s' % (time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                            '**终稿（D62+D64 全部数据，含 CI 与判定）**' if is_final else
                            ('**中间报告（10 万步部分；30 万步长训练未完成，4.1 最终判定待定）**' if final else '**点估计草稿（CI 待计算）**')),
         '- 判据：D62、D64（预登记，不得修改）。K-std-r = 在 r 米已观测地图下训练并评测；G-std = 全局训练并评测（policy-100k 为种子 11，补训 G-std-s22 为种子 22）；'
         '10 万步末端 checkpoint（导出仅策略权重，不挑最优），评测种子 %d–%d 共 %d 回合，确定性；`K-std-r-long` = 种子 11、30 万步预算、末端 checkpoint。' % (
             points['eval_seeds'][0], points['eval_seeds'][1], points['n_episodes']), '']
    L += ['## D62 判定（每个 r 分别，10 万步）', '',
          '| r | SR(G-std) | SR(K-std-r) | 差（点估计） | 差 95% CI（训练种子×回合分层） | 差 ≥0.10 且 CI 下界>0 | SR(random, r) | K − random | ≥0.30 | D62 通过 |', '|---|---|---|---|---|---|---|---|---|---|']
    for rk, d in result['per_r'].items():
        ci = d.get('gap_ci95')
        L.append('| %g m | %.3f | %.3f | %+.3f | %s | %s | %s | %s | %s | %s |' % (
            PH4_RADII[rk], d['sr_g'], d['sr_k'], d['gap'], '[%.3f, %.3f]' % tuple(ci) if ci else '待计算',
            ('是' if d.get('gap_passes') else '否') if ci else '待定', _f(d.get('sr_random')), _f(d.get('k_minus_random'), 3),
            ('是' if d.get('random_passes') else '否') if 'random_passes' in d else '—',
            ('**通过**' if d.get('passes_100k') else '**不通过**') if ci else '待定'))
    L += ['', '## D64 收敛检查（SR(G-std) − SR(K-std-r-long) ≥ 0.10，点估计为判据）', '',
          '| r | SR(G-std) | SR(K-std-r-long)（30 万步） | 差（点估计） | 差 95% CI（回合 bootstrap，仅报告、不作判据；1 个种子） | ≥0.10 | 4.1 通过（D62 与 D64） | 未通过原因 |', '|---|---|---|---|---|---|---|---|']
    for rk, d in result['per_r'].items():
        if 'sr_k_long' in d:
            ci = d.get('gap_long_ci95_descriptive')
            L.append('| %g m | %.3f | %.3f | %+.3f | %s | %s | %s | %s |' % (
                PH4_RADII[rk], d['sr_g'], d['sr_k_long'], d['gap_long'], '[%.3f, %.3f]' % tuple(ci) if ci else '待计算',
                '是' if d['long_passes'] else '否', ('**通过**' if d.get('passes') else '**不通过**') if 'passes' in d else '待定', d.get('not_passed_reason') or ''))
        else:
            L.append('| %g m | %.3f | （长训练未完成） | | | | 待定 | |' % (PH4_RADII[rk], d['sr_g']))
    L.append('')
    if d62:
        if d62['r_sel'] is not None:
            L.append('**4.1 结论：r_sel = %g m**（D62 与 D64 都通过的最大 r）。4.2/4.3 在 r_sel 下进行，判据仍为 ROADMAP 草案，进入前须登记。' % d62['r_sel'])
        elif d62['complete']:
            L.append('**4.1 结论：%s。**' % d62['outcome'])
        elif d62.get('complete_100k'):
            L.append('**中间结论（仅 10 万步 D62 部分）**：D62 通过的 r = %s（最大者 %s）；%s。' % (
                d62['interim_passing_radii'] or '无', d62['interim_r_sel'] if d62['interim_r_sel'] is not None else '—', d62['outcome']))
        else:
            L.append('数据尚不齐全，暂无结论（%s）。' % d62['outcome'])
        L.append('')
    L += ['每个训练种子的差（描述性，非判据）：', '', '| r | 种子 | SR(G) − SR(K) | 95% CI（描述性） |', '|---|---|---|---|']
    for rk, d in result['per_r'].items():
        for s in TRAIN_SEEDS:
            ci = d.get('per_seed_gap_ci95_descriptive', {}).get(str(s))
            L.append('| %g m | %d | %+.3f | %s |' % (PH4_RADII[rk], s, d['per_seed_gap'][str(s)], '[%.3f, %.3f]' % tuple(ci) if ci else '—'))
    L += ['', '## 学习曲线（诊断，非判据）', '',
          '检查点为 10 万步训练的每 2 万步与长训练的每 5 万步，边训练边评测；末 3 点极差与末点相对前一点的变化是描述性数字（无预登记阈值），是否走平由读者按曲线判断。', '']
    L += curve_table(result.get('curves') or points.get('curves') or {})
    L += ['', '## 各臂完整指标（末端 checkpoint）', '', HEADER]
    for name, d in points['arms'].items():
        L.append(arm_row(name, d))
    L += ['', '## 改道统计', '']
    L += reroute_table(points['reroutes'], [n for n in points['reroutes']])
    if training:
        L += ['', '## 训练耗时', '', '| 任务 | 完成 | 汇总训练进程秒数 | 最终计数 |', '|---|---|---|---|']
        for name, t in training.items():
            L.append('| %s | %s | %.0f（%.1f h） | %s |' % (name, '是' if t['done'] else '否', t['summed_attempt_seconds'], t['summed_attempt_seconds'] / 3600, t['final_counters']))
    L += ['', '## 数据与出处', '',
          '- 原始产物：`results/ph4-train/`（`status.json`、`pipeline.log`、`train/`、`s3-eval/`、`s6-curves/`、`point.json`、`analysis.json`），PH3 诊断 `results/ph3-obsmap/`；不入 Git。',
          '- 10 万步训练配置同 policy-100k：`--steps 100000 --save-interval 20000 --batch 256 --replay-capacity 100000 --random-steps 1000 --ik-mode fixed --ik-iterations 100 --eval-interval 0 --replay-compact-maps`；'
          '长训练同配置但 `--steps 300000 --save-interval 50000`（学习率按 30 万步预算衰减）。',
          '- 不使用种子 20000–20299。', '']
    return '\n'.join(L)


def training_info(ph4_dir, job_names):
    out = {}
    for name in job_names:
        job_dir = Path(ph4_dir) / 'train' / name
        secs, final = 0.0, None
        for a in sorted(job_dir.glob('a*/summary.json')):
            summary = json.loads(a.read_text())
            secs += float(summary.get('seconds', 0.0))
            final = summary
        out[name] = dict(summed_attempt_seconds=secs, done=(job_dir / 'DONE').exists(),
                         final_counters={k: final.get(k) for k in ('steps', 'updates', 'episodes')} if final else None)
    return out
