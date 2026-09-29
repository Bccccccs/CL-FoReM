"""SCREEN-028 automatic report (stage S8). States results only; the final line choice is the user's (D52)."""
import json
from pathlib import Path


def _load(path):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else None


def _pct(x):
    return 'n/a' if x is None else '%.3f' % x


def _ci(ci):
    return 'n/a' if not ci else '[%.3f, %.3f]' % (ci[0], ci[1])


def _dist(d):
    return ', '.join('%s:%d' % kv for kv in sorted((d or {}).items())) or '-'


def _yn(v):
    return 'n/a' if v is None else ('**通过**' if v else '不通过')


def stage_table(status):
    rows = ['| 阶段 | 状态 | 说明 |', '|---|---|---|']
    names = {'S0': '预检', 'S1': 'L1 伤害测试', 'S2': 'D0 可行性', 'S3': 'D1 训练（6）', 'S4': 'L2 训练（6）', 'S5': 'L3 探索臂',
             'S6': 'D2 评测', 'S7': 'L2 评测', 'S8': '汇总报告'}
    stages = (status or {}).get('stages', {})
    for key, name in names.items():
        s = stages.get(key, {})
        note = s.get('error', '') or ''
        if key in ('S3', 'S4') and s.get('jobs'):
            note = '; '.join('%s:%s' % (j, v.get('state')) for j, v in sorted(s['jobs'].items()))
        rows.append('| %s %s | %s | %s |' % (key, name, s.get('state', '未运行'), note[:300]))
    return '\n'.join(rows)


def l1_section(res):
    if not res:
        return '（S1 无结果）'
    a = res['analysis']
    out = ['种子 %d–%d，n=%d，policy-100k，确定性；判据 D53-L1：相对名义 SR 下降 ≥ 0.15 且配对 CI 上界 < 0。' % (
        a['seeds'][0], a['seeds'][1], a['n']), '',
        '| 配置 | SR | ΔSR vs 名义 | 配对 95% CI | perfect | 碰撞回合比例 | IK 失败回合比例 | 异常 | 失败原因 | 通过 |',
        '|---|---|---|---|---|---|---|---|---|---|']
    for name, arm in a['arms'].items():
        if not arm or arm.get('unavailable'):
            out.append('| %s | 缺失 | | | | | | | | |' % name)
            continue
        out.append('| %s | %s | %s | %s | %s | %s | %s | %d | %s | %s |' % (
            name, _pct(arm['success_rate']), _pct(arm.get('delta_vs_nominal')), _ci(arm.get('delta_ci95')),
            _pct(arm['perfect_success_rate']), _pct(arm['collision_episode_fraction']),
            _pct(arm['ik_failure_episode_fraction']), arm['exceptions'], _dist(arm['failure_distribution']),
            '—' if name == 'nominal' else _yn(arm.get('passes_l1'))))
    d = a['decision']
    out += ['', '**L1 结论**：档位 = `%s`；k_sel = %s（%s）；L2 %s。' % (
        d['tier'], d['k_sel'], d['mode'], '运行' if d['l2_runs'] else '不运行（L3 仍运行）')]
    if d.get('smoke_override'):
        out.append('**注意：这是冒烟测试，L1 结论被强制覆盖，仅用于走通流程。**')
    return '\n'.join(out)


def d0_section(res):
    if not res:
        return '（S2 无结果）'
    c = res.get('checks', {})
    return '\n'.join(['- 2000 步训练冒烟（`dynobstacle`，batch 256）完成：%s（返回码 %s）' % (c.get('train_completed'), c.get('train_returncode')),
                      '- 6 回合评测（current/future/past/frozen 各 2 回合，种子 10000–10001）无异常：%s' % c.get('eval_no_exceptions'),
                      '- **D0 %s**' % ('通过' if res.get('passes') else '不通过，D 线终止')])


def family_table(res):
    out = ['| 臂 | 训练种子 | SR | perfect | 碰撞回合比例 | IK 失败回合比例 | 失败原因 |', '|---|---|---|---|---|---|---|']
    for label, fam in res['arms'].items():
        for seed, arm in fam['per_seed'].items():
            if not arm:
                out.append('| %s | %s | 缺失 | | | | |' % (label, seed))
                continue
            out.append('| %s | %s | %s | %s | %s | %s | %s |' % (label, seed, _pct(arm['success_rate']), _pct(arm['perfect_success_rate']),
                                                             _pct(arm['collision_episode_fraction']), _pct(arm['ik_failure_episode_fraction']),
                                                             _dist(arm['failure_distribution'])))
        if fam['pooled']:
            p = fam['pooled']
            out.append('| **%s 合并** | 11+22 | **%s** | %s | %s | %s | |' % (label, _pct(p['success_rate']), _pct(p['perfect_success_rate']),
                                                                       _pct(p['collision_episode_fraction']), _pct(p['ik_failure_episode_fraction'])))
    return '\n'.join(out)


def diff_table(res):
    out = ['| 比较 | 点估计 | 分层 bootstrap 95% CI |', '|---|---|---|']
    for name in res['point_diffs']:
        d = res.get('diffs', {}).get(name)
        out.append('| %s | %s | %s |' % (name, _pct(res['point_diffs'][name]), _ci(d['ci95']) if d else '（CI 未生成）'))
    return '\n'.join(out)


def l2_section(res):
    if not res:
        return '（S7 无结果：L1 未通过而跳过，或训练/评测失败）'
    a = res['analysis']
    v = a['verdict']
    return '\n\n'.join([
        'k_sel = %s（%s 延迟）。判据 D53-L2：SR(oracle)−SR(hist) ≥ 0.10 且 CI 下界 > 0，并且 SR(oracle)−SR(stale) 的 CI 下界 > 0。' % (a['k_sel'], a['latency_mode']),
        family_table(a), diff_table(a),
        '**L2 结论**：%s（oracle−hist 条件：%s；oracle−stale 条件：%s）。' % (_yn(v.get('passes')), v.get('oracle_minus_hist_ok'), v.get('oracle_minus_stale_ok'))
        + ('' if not res.get('missing') else ' 缺失的臂：%s。' % res['missing'])])


def l3_section(res):
    if not res:
        return '（S5 无结果）'
    a = res['analysis']
    arms = a['arms']
    lines = ['探索性，不作通过依据。延迟配置 = 模式 `%s`，k = %s；stale 臂取自 L1 配置 `%s`。' % (res.get('mode'), res.get('k'), a['stale_arm']), '',
             '| 臂 | SR | perfect | 碰撞回合比例 | IK 失败回合比例 |', '|---|---|---|---|---|']
    for label, key in [('名义', 'nominal'), ('stale', 'stale'), ('wm-comp', 'wm_comp')]:
        arm = arms.get(key)
        lines.append('| %s | %s | %s | %s | %s |' % ((label,) + ((_pct(arm['success_rate']), _pct(arm['perfect_success_rate']),
                                                                   _pct(arm['collision_episode_fraction']), _pct(arm['ik_failure_episode_fraction']))
                                                                  if arm else ('缺失', '', '', ''))))
    if 'sr_wm_minus_stale' in a:
        lines += ['', '- SR(wm-comp) − SR(stale) = %s，配对 95%% CI %s' % (_pct(a['sr_wm_minus_stale']), _ci((a.get('wm_minus_stale') or {}).get('ci95'))),
                  '- 名义与 stale 的 SR 差距 = %s；**SR 恢复比例** = %s，bootstrap 95%% CI %s%s' % (
                      _pct(a.get('sr_gap_nominal_minus_stale')), _pct(a.get('recovery_ratio')), _ci((a.get('recovery') or {}).get('ci95')),
                      '' if a.get('recovery_ratio') is not None else '（名义 ≤ stale，比例无定义）')]
    return '\n'.join(lines)


def d2_section(res):
    if not res:
        return '（S6 无结果：D0 未通过而跳过，或训练/评测失败）'
    a = res['analysis']
    v = a['verdict']
    out = ['判据 D54：harm = SR(D-std 冻结) − SR(D-std 移动) ≥ 0.15 且 CI 下界 > 0；headroom = SR(oracle) − SR(hist) ≥ 0.10 且 CI 下界 > 0，并且 SR(oracle) − SR(std) 的 CI 下界 > 0；两者都要满足。',
           family_table(a), diff_table(a),
           '**D54-harm**：%s；**D54-headroom**：%s；**D 线总体**：%s。' % (_yn(v.get('harm')), _yn(v.get('headroom')), _yn(v.get('passes')))]
    if a.get('task_too_hard_warning'):
        out.append('**警告：D-std 在移动障碍下合并 SR = %s < 0.2，任务整体过难，结论应谨慎解读（D54）。**' % _pct(a.get('d_std_moving_success_rate')))
    if res.get('missing'):
        out.append('缺失的臂：%s。' % res['missing'])
    return '\n\n'.join(out)


def decision_section(l2, d2):
    lv = ((l2 or {}).get('analysis') or {}).get('verdict', {}).get('passes')
    dv = ((d2 or {}).get('analysis') or {}).get('verdict', {}).get('passes')
    lines = ['- L 线（感知延迟）通过：%s' % ('未评估' if lv is None else lv), '- D 线（动态障碍）通过：%s' % ('未评估' if dv is None else dv), '']
    if lv is None or dv is None:
        lines.append('某条线未能评估（跳过或失败），按 D52 表格无法唯一确定对应行；见上文各阶段状态。')
    elif lv and not dv:
        lines.append('对应 D52 行：**只有 L 线通过** → 主线改为“学习型世界模型做感知延迟补偿”，L3 结果作为方法原型的第一份证据。')
    elif dv and not lv:
        lines.append('对应 D52 行：**只有 D 线通过** → 主线改为“动态障碍下的世界模型前瞻”，需 P1b（带历史的世界模型）预测障碍运动。')
    elif lv and dv:
        lg = l2['analysis']['point_diffs'].get('oracle_minus_hist')
        dg = d2['analysis']['point_diffs'].get('oracle_minus_hist')
        pick = 'L 线' if (lg or 0) >= (dg or 0) else 'D 线'
        lines.append('对应 D52 行：**两者都通过** → 取“开卷 − 历史”差距更大者为主线：L 线 %s vs D 线 %s，较大者为 **%s**，另一条作补充实验。' % (_pct(lg), _pct(dg), pick))
    else:
        lines.append('对应 D52 行：**都不通过** → 停止“闭环前瞻”这一论点；在 11-20 去留点前由用户决定论文重新定位。')
    lines.append('\n最终选择由用户确认；本报告只陈述结果。')
    return '\n'.join(lines)


def build_report(root, cfg=None):
    root = Path(root)
    status = _load(root / 'status.json')
    s0 = _load(root / 's0-preflight' / 'manifest.json') or {}
    l1 = _load(root / 's1-l1' / 'result.json')
    d0 = _load(root / 's2-d0' / 'result.json')
    l2 = _load(root / 's7-l2-eval' / 'result.json')
    l3 = _load(root / 's5-l3' / 'result.json')
    d2 = _load(root / 's6-d2-eval' / 'result.json')
    git = s0.get('git', {})
    parts = [
        '# SCREEN-028 前瞻场景筛选报告（自动生成）',
        '',
        '- 生成时间：%s' % (status or {}).get('updated', 'n/a'),
        '- 输出根目录：`%s`；分支 `%s`，HEAD `%s`（工作区 %s）' % (root, git.get('branch'), (git.get('head') or '')[:10], '有未提交改动' if git.get('dirty') else '干净'),
        '- 判据：D52–D54 预登记（运行前），D56 修订 D 线时长为 20 步；统计：成功 = `primary_reason == success`（异常记失败），按种子配对，分层（训练种子×回合）bootstrap 10000 次；`result.json` 均先写点估计（`point.json`）。',
        '- 评测一律 `--ik-mode fixed --ik-iterations 100`，确定性策略；训练种子 11、22，评测种子 10000–10099。',
        '',
        '## 1. 阶段状态', '', stage_table(status), '',
        '## 2. L1 伤害测试（感知延迟）', '', l1_section(l1), '',
        '## 3. D0 可行性', '', d0_section(d0), '',
        '## 4. L2 上限测试（仅 L1 通过时）', '', l2_section(l2), '',
        '## 5. L3 探索：世界模型补偿', '', l3_section(l3), '',
        '## 6. D2 评测（动态障碍）', '', d2_section(d2), '',
        '## 7. 按 D52 决策规则对应的行', '', decision_section(l2, d2), '',
        '## 8. 解读边界', '',
        '- 障碍位移：直径 0.3 m、速度 0.10–0.15 m/s；D56 后 2 s 内约 20–30 cm。future/past 地图是策略输入的并集叠加，不改变碰撞与奖励。',
        '- L1 的 k=5（0.5 s）为压力档，k≤3 为现实档；仅压力档通过时，L2 结论应按压力档解读。',
        '- L3 为探索性、不训练、不作通过依据；SR 恢复比例在名义与 stale 差距很小时不稳定，见其 CI。',
        '- 若任一阶段失败/跳过/超时，上文已如实标注；点估计文件在各阶段 `analysis/point.json`。',
        '',
        '## 9. 产物位置', '',
        '- `%s/s1-l1/`、`s5-l3/`、`s6-d2-eval/`、`s7-l2-eval/`：各臂 `episodes.jsonl`、`analysis/{point,result}.json`。' % root,
        '- `%s/train/<臂>-s<种子>/`：训练尝试目录 `a*/`（含 `latest.pt`、`summary.json`）、`policy.pt`（评测用仅策略 checkpoint）、`DONE`。' % root,
        '- `%s/status.json`、`pipeline.log`：运行状态与顶层日志。' % root,
        '']
    return '\n'.join(parts)
