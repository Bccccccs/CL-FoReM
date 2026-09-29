"""CEIL-028 analysis (D57, pre-registered before implementation; thresholds below are NOT tunable).

  C-learn  (learning headroom): mean SR of the two 300k budget-end checkpoints (training seeds 11, 22)
           minus SR(policy-100k) >= 0.10 AND the lower bound of the 95% "training seed x episode"
           stratified bootstrap CI of that difference > 0. Reading (recorded in the task log): one
           pooled difference, strata = the two training seeds, the same episode indices resampled for the
           trained arm and for the (replicated) policy-100k arm; the per-seed views are reported as
           descriptive extras, not criteria.
  C-policy (policy matters):    SR(policy-100k) - max(SR(random), SR(mean)) >= 0.30 (point estimates).

slow-ee, mid-training checkpoints, perfect-success, IK/collision episode fractions and training time are
reported only. Point estimates are written to disk (`point.json`) before any bootstrap runs, so a
timeout or crash while computing CIs can never lose them.
"""
import json
import time
from pathlib import Path

import numpy as np

import screen_analysis as sa
import screen_stats as st

C_LEARN_MIN = 0.10
C_POLICY_MIN = 0.30
SIMPLE_ARMS = ('random', 'mean', 'slow-ee')
NEXT_STEP = {  # D57 pre-registered table (C-learn, C-policy)
    (True, True): ('SAC 的决策重要，且还有学习空间',
                   '做“世界模型帮 SAC 学习”：先做辅助预测任务（重点预测 IK 可行性），比较相同训练步数下的学习曲线'),
    (False, True): ('SAC 已接近该任务的天花板', '换任务（door / drawer 等），先做同样的上限摸底'),
    (False, False): ('任务对策略不敏感', '换任务'),
    (True, False): ('结果矛盾，需检查实验', '停下来核查后再决定'),
}


def ckpt_arm(seed, step):
    return 'E1-s%d-step%07d' % (seed, step)


def expected_steps(train_steps, save_interval):
    return list(range(save_interval, train_steps + 1, save_interval))


def _write(path, value):
    sa._dump(path, value)


def load_baseline(baseline_dir):
    path = Path(baseline_dir) / 'episodes.jsonl'
    return st.load_rows(path) if path.exists() else None


def collect_points(root, cfg):
    """Point estimates for every arm that has all its episodes; unavailable arms are None."""
    root = Path(root)
    seeds, steps = cfg.eval_seeds, expected_steps(cfg.train_steps, cfg.save_interval)
    baseline = sa.describe_arm(load_baseline(cfg.baseline_dir), seeds)
    simple = {a: sa.describe_arm(sa.arm_rows(root / 's1-e2-simple', a), seeds) for a in SIMPLE_ARMS}
    curves = {str(s): {str(step): sa.describe_arm(sa.arm_rows(root / 's3-ckpt-eval', ckpt_arm(s, step)), seeds)
                       for step in steps} for s in cfg.train_seeds}
    final = steps[-1]
    finals = {str(s): curves[str(s)][str(final)] for s in cfg.train_seeds}
    out = dict(eval_seeds=[seeds[0], seeds[-1]], n_episodes=len(seeds), train_seeds=list(cfg.train_seeds),
               train_steps=cfg.train_steps, checkpoint_steps=steps, baseline=baseline, simple=simple, curves=curves)

    # C-policy: pure point estimates
    if baseline and simple['random'] and simple['mean']:
        best = max(simple['random']['success_rate'], simple['mean']['success_rate'])
        diff = baseline['success_rate'] - best
        out['c_policy'] = dict(sr_policy=baseline['success_rate'], sr_random=simple['random']['success_rate'],
                               sr_mean=simple['mean']['success_rate'], best_simple=best, diff=diff, threshold=C_POLICY_MIN,
                               passes=bool(diff >= C_POLICY_MIN - 1e-12))
    else:
        out['c_policy'] = None

    # C-learn point part
    if baseline and all(finals.values()):
        mean_final = float(np.mean([finals[str(s)]['success_rate'] for s in cfg.train_seeds]))
        out['c_learn'] = dict(mean_final_sr=mean_final, sr_policy=baseline['success_rate'],
                              diff_point=mean_final - baseline['success_rate'], threshold=C_LEARN_MIN,
                              point_passes=bool(mean_final - baseline['success_rate'] >= C_LEARN_MIN - 1e-12),
                              per_seed={str(s): dict(sr=finals[str(s)]['success_rate'],
                                                     diff_point=finals[str(s)]['success_rate'] - baseline['success_rate'])
                                        for s in cfg.train_seeds})
    else:
        out['c_learn'] = None
    return out


def add_cis(root, cfg, points, n_boot=st.N_BOOT):
    """Bootstrap the C-learn CI (pooled, stratified by training seed) and the per-seed extras."""
    result = json.loads(json.dumps(points))
    cl = result.get('c_learn')
    if cl:
        seeds, final = cfg.eval_seeds, points['checkpoint_steps'][-1]
        base = st.flags(load_baseline(cfg.baseline_dir), seeds)
        trained = np.stack([st.flags(sa.arm_rows(Path(root) / 's3-ckpt-eval', ckpt_arm(s, final)), seeds) for s in cfg.train_seeds])
        pooled = st.diff_with_ci(trained, np.tile(base, (len(cfg.train_seeds), 1)), n_boot=n_boot, seed=0)
        cl['pooled'] = pooled
        cl['ci95'] = pooled['ci95']
        cl['n_boot'] = n_boot
        cl['passes'] = bool(cl['point_passes'] and st.lower_bound_positive(pooled['ci95']))
        for i, s in enumerate(cfg.train_seeds):
            cl['per_seed'][str(s)]['ci95'] = st.diff_with_ci(trained[i], base, n_boot=n_boot, seed=1 + i)['ci95']
        cl['both_seeds_each_ge_threshold'] = bool(all(v['diff_point'] >= C_LEARN_MIN - 1e-12 for v in cl['per_seed'].values()))
    return result


def verdict(result):
    """(c_learn_pass, c_policy_pass, meaning, next_step) or None when a criterion could not be evaluated."""
    cl, cp = result.get('c_learn'), result.get('c_policy')
    if not cl or 'passes' not in cl or not cp:
        return None
    key = (bool(cl['passes']), bool(cp['passes']))
    return key[0], key[1], NEXT_STEP[key][0], NEXT_STEP[key][1]


def training_info(root, cfg):
    """Wall/compute time per training job from artifacts (not from the PID-bound status file)."""
    out = {}
    for seed in cfg.train_seeds:
        job_dir = Path(root) / 'train' / ('E1-s%d' % seed)
        attempts = sorted(job_dir.glob('a*/summary.json'))
        secs = 0.0
        final = None
        for a in attempts:
            summary = json.loads(a.read_text())
            secs += float(summary.get('seconds', 0.0))
            final = summary
        started = Path(root) / 's2-train' / 'started.json'
        wall = None
        if started.exists() and (job_dir / 'DONE').exists():
            wall = (job_dir / 'DONE').stat().st_mtime - json.loads(started.read_text())['epoch']
        out[str(seed)] = dict(attempt_dirs=len([x for x in job_dir.glob('a*') if x.is_dir()]), summed_attempt_seconds=secs,
                              wall_seconds_first_log_to_done=wall,
                              final_counters={k: final.get(k) for k in ('steps', 'updates', 'episodes')} if final else None,
                              done=(job_dir / 'DONE').exists())
    return out


def analyze(root, cfg, n_boot=st.N_BOOT, on_points=None):
    """Point estimates first (point.json; `on_points(points)` lets the caller write a draft report
    before any bootstrap runs), then CIs (result.json)."""
    root = Path(root)
    points = collect_points(root, cfg)
    points['training'] = training_info(root, cfg)
    _write(root / 's4-report' / 'point.json', points)
    if on_points is not None:
        on_points(points)
    result = add_cis(root, cfg, points, n_boot=n_boot)
    _write(root / 's4-report' / 'result.json', result)
    return points, result


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _f(x, nd=2):
    return '—' if x is None else '%.*f' % (nd, x)


def _arm_row(name, d):
    if d is None:
        return '| %s | （数据不全） | | | | | | |' % name
    fd = ', '.join('%s %d' % (k, v) for k, v in sorted(d['failure_distribution'].items()))
    return '| %s | %d | %s | %s | %s | %s | %.0f | %d | %s |' % (
        name, d['n'], _f(d['success_rate']), _f(d['perfect_success_rate']), _f(d['ik_failure_episode_fraction']),
        _f(d['collision_episode_fraction']), d['mean_steps'], d['exceptions'], fd)


ARM_HEADER = ('| 臂 | 回合 | SR | perfect | IK失败回合比例 | 碰撞回合比例 | 平均步数 | 异常 | 结束原因 |\n'
              '|---|---|---|---|---|---|---|---|---|')


def build_report(root, cfg, points=None, result=None, final=False):
    """Markdown report. `final=False` is the point-estimate-only draft written before any CI exists."""
    root = Path(root)
    points = points if points is not None else json.loads((root / 's4-report' / 'point.json').read_text())
    result = result if result is not None else points
    steps = points['checkpoint_steps']
    cp, cl = result.get('c_policy'), result.get('c_learn')
    v = verdict(result) if final else None
    L = ['# CEIL-028 SAC 上限摸底：自动报告', '',
         '- 生成：%s；%s' % (time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                            '**终稿（含 CI 与判据结论）**' if final else '**点估计草稿（CI 尚未计算，判据结论待定）**'),
         '- 判据：D57（预登记，本报告只陈述结果；最终方向由用户确认）。设计见 [设计说明](20260929-ceil-spec.md)，运行记录见 [任务日志](20260929-ceil-pipeline.md)。',
         '- 评测：simpleobstacle，确定性，`--ik-mode fixed --ik-iterations 100`，种子 %d–%d 共 %d 回合；训练种子 %s，预算 %d 步，每 %d 步存检查点。' % (
             points['eval_seeds'][0], points['eval_seeds'][1], points['n_episodes'], points['train_seeds'], points['train_steps'], cfg.save_interval),
         '- policy-100k 基线 = R0-3c 名义 100 回合（`%s`）；**主结论只看预算末端检查点（%d 步），不挑中间最好的**。' % (cfg.baseline_dir, steps[-1]), '']

    L += ['## 判据结果（D57）', '']
    if cp:
        L += ['**C-policy**（SR(policy-100k) − max(SR(random), SR(mean)) ≥ %.2f）：SR(policy-100k) = %.2f，SR(random) = %.2f，SR(mean) = %.2f，'
              'max = %.2f，差 = **%+.2f** → **%s**' % (C_POLICY_MIN, cp['sr_policy'], cp['sr_random'], cp['sr_mean'], cp['best_simple'], cp['diff'],
                                                     '通过' if cp['passes'] else '不通过'), '']
    else:
        L += ['**C-policy**：数据不全，无法评估（见下方各臂表）。', '']
    if cl:
        line = ('**C-learn**（两个 %d 步预算末端检查点的平均 SR − SR(policy-100k) ≥ %.2f，且分层 bootstrap 95%% CI 下界 > 0）：末端 SR 平均 = %.3f，'
                'SR(policy-100k) = %.2f，差点估计 = **%+.3f**（阈值 %.2f，点估计%s）' % (
                    steps[-1], C_LEARN_MIN, cl['mean_final_sr'], cl['sr_policy'], cl['diff_point'], C_LEARN_MIN, '达标' if cl['point_passes'] else '未达标'))
        if 'ci95' in cl:
            line += '；95%% CI = [%.3f, %.3f]（%d 次重采样）→ **%s**' % (cl['ci95'][0], cl['ci95'][1], cl['n_boot'], '通过' if cl['passes'] else '不通过')
        else:
            line += '；CI 待计算 → 判据结论待定'
        L += [line, '']
        L += ['每个训练种子的末端检查点相对 policy-100k（描述性，非判据；较严格的“两个种子各自都达标”读法）：', '',
              '| 训练种子 | 末端 SR | 相对 policy-100k 差（点估计） | 95% CI |', '|---|---|---|---|']
        for s, d in cl['per_seed'].items():
            L.append('| %s | %.2f | %+.3f | %s |' % (s, d['sr'], d['diff_point'],
                                                       '[%.3f, %.3f]' % tuple(d['ci95']) if 'ci95' in d else '待计算'))
        if 'both_seeds_each_ge_threshold' in cl:
            L += ['', '两个种子各自的点估计是否都 ≥ %.2f：**%s**。' % (C_LEARN_MIN, '是' if cl['both_seeds_each_ge_threshold'] else '否')]
        L += ['', 'CI 读法：分层 = 训练种子（各 %d 回合），训练臂与复制的 policy-100k 臂使用相同回合下标；它只反映评测回合与训练种子的抽样波动，'
                  '不含 policy-100k 自身训练随机性（基线只有 1 个训练种子）。' % points['n_episodes'], '']
    else:
        L += ['**C-learn**：末端检查点评测数据不全，无法评估（见下方学习曲线；训练是否失败见状态文件）。', '']

    L += ['## 对应的下一步（D57 预登记表）', '']
    if v:
        L += ['C-learn = %s，C-policy = %s → **%s**：%s。' % ('通过' if v[0] else '不通过', '通过' if v[1] else '不通过', v[2], v[3]),
              '', '（预登记的映射，报告只陈述结果；最终方向由用户确认。）', '']
    else:
        L += ['判据结论尚未齐备（%s），因此不给出映射。预登记表：' % ('点估计草稿' if not final else '数据不全'), '']
    L += ['| C-learn | C-policy | 含义 | 下一步 |', '|---|---|---|---|']
    for (a, b), (meaning, nxt) in NEXT_STEP.items():
        L.append('| %s | %s | %s | %s |' % ('通过' if a else '不通过', '通过' if b else '不通过', meaning, nxt))
    L.append('')

    L += ['## E2 简单策略对照（policy-100k 与三种简单策略，%d 回合）' % points['n_episodes'], '', ARM_HEADER,
          _arm_row('policy-100k（基线，R0-3c 名义）', points['baseline'])]
    for a in SIMPLE_ARMS:
        L.append(_arm_row(a + ('（探索性，不作判据）' if a == 'slow-ee' else ''), points['simple'][a]))
    L += ['', 'mean 动作（由 R0-3c 名义 100 回合逐步动作逐维平均得出，未手调）见 `s0-preflight/mean-action.json`。', '']

    L += ['## E1 学习曲线（每检查点 %d 回合；中间点只作报告）' % points['n_episodes'], '',
          '| 训练种子 | ' + ' | '.join('%gk' % (x / 1000) for x in steps) + ' |', '|---|' + '---|' * len(steps)]
    for s in points['train_seeds']:
        cells = []
        for step in steps:
            d = points['curves'][str(s)][str(step)]
            cells.append('—' if d is None else '%.2f' % d['success_rate'])
        L.append('| %d | ' % s + ' | '.join(cells) + ' |')
    if points['baseline']:
        L.append('| policy-100k（10 万步，学习率已衰减到底，仅作参照） | ' + ' | '.join([_f(points['baseline']['success_rate'])] * len(steps)) + ' |')
    L += ['', '注：本任务的 10 万步检查点学习率仍在衰减途中（预算 30 万步），与 policy-100k 不等价，只作曲线上的一个点。', '',
          '### 末端检查点（%d 步）完整指标' % steps[-1], '', ARM_HEADER]
    for s in points['train_seeds']:
        L.append(_arm_row('E1 seed %d @ %gk' % (s, steps[-1] / 1000), points['curves'][str(s)][str(steps[-1])]))
    L.append(_arm_row('policy-100k（基线）', points['baseline']))

    L += ['', '## 训练耗时与状态', '', '| 训练种子 | 完成 | 汇总的训练进程秒数（不含未正常结束的尝试） | 阶段起点到完成的墙钟（h） | 尝试目录数 | 最终计数 |', '|---|---|---|---|---|---|']
    for s, t in points.get('training', {}).items():
        wall = t.get('wall_seconds_first_log_to_done')
        L.append('| %s | %s | %.0f（%.1f h） | %s | %s | %s |' % (
            s, '是' if t['done'] else '否', t['summed_attempt_seconds'], t['summed_attempt_seconds'] / 3600,
            _f(wall / 3600 if wall else None, 1), t['attempt_dirs'], t['final_counters']))
    L += ['', '## 数据与出处', '',
          '- 原始产物：`results/ceil-028/`（`status.json`、`pipeline.log`、`train/`、`s1-e2-simple/`、`s3-ckpt-eval/`、`s4-report/{point,result}.json`）；不入 Git。',
          '- 训练配置与 policy-100k 相同（batch 256、random_steps 1000、replay_capacity 100000、ik fixed 100、max_episode_steps 2000），除预算 30 万步、'
          '`--save-interval 50000`、`--replay-compact-maps`（D55，采样逐位相同）与 `--eval-interval 0`；从零训练，不续训 policy-100k。',
          '- 不使用种子 20000–20299；评测种子 10000–10099 与 R0-3c/SCREEN 相同。', '']
    return '\n'.join(L)
