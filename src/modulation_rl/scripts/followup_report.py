"""FOLLOWUP-028 S6: builds doc/agent_logs/20260928-followup-report.md from the pipeline's own
stage outputs. States results only; does not propose changing D50/D51."""
import json
from pathlib import Path

import numpy as np


def _read(path):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else None


def _episode_stats(episodes_jsonl):
    rows = [json.loads(l) for l in Path(episodes_jsonl).read_text().splitlines()] if Path(episodes_jsonl).exists() else []
    if not rows:
        return None
    sr = float(np.mean([r.get('success', False) for r in rows]))
    perfect = float(np.mean([r.get('perfect_success', False) for r in rows]))
    ik_frac = float(np.mean([r.get('primary_reason') == 'ik_limit' for r in rows]))
    triggers = [r.get('shield_trigger_count', 0) for r in rows if 'shield_trigger_count' in r]
    steps = [r.get('steps', 0) for r in rows]
    return dict(episodes=len(rows), success_rate=sr, perfect_success_rate=perfect,
                ik_limit_fraction=ik_frac, mean_steps=float(np.mean(steps)) if steps else None,
                mean_shield_triggers=float(np.mean(triggers)) if triggers else None)


def build_report(root):
    root = Path(root)
    a_report = _read(root / 's1-a-structured' / 'probe' / 'report.json')
    b1_report = _read(root / 's2-b1-avoidability' / 'analysis' / 'report.json')
    b2_report = _read(root / 's4-b2-foresight' / 'train' / 'report.json')

    lines = ['# FOLLOWUP-028 G0 后续双线检验：自动汇总报告', '',
             '本报告由 `followup_pipeline.py` S6 阶段自动生成，只陈述结果，不建议修改 D50/D51 判据。', '']

    lines += ['## A 线（结构化低维适应，D50）', '']
    if a_report is None:
        lines.append('S1 未完成或失败，无数据。')
    else:
        lines.append('D50 通过：**%s**' % a_report.get('d50_pass'))
        lines.append('')
        lines.append('| 变体 | 达标强失配条件数(/4) | 名义未变差 | 通过 |')
        lines.append('|---|---|---|---|')
        for vname, v in a_report.get('d50', {}).items():
            lines.append('| %s | %d | %s | %s |' % (vname, v['qualifying_strong_conditions'], v['nominal_not_worse'], v['passes_d50']))
    lines.append('')

    lines += ['## B1 可避免性（D51-B1）', '']
    if b1_report is None:
        lines.append('S2 未完成或失败，无数据。')
    else:
        lines.append('D51-B1 通过：**%s**' % b1_report.get('passes_d51_b1'))
        lines.append('')
        lines.append('- fail_to_success_fraction (mild) = %.3f' % b1_report.get('fail_to_success_fraction_mild', float('nan')))
        lines.append('- success_to_fail_fraction (mild) = %.3f' % b1_report.get('success_to_fail_fraction_mild', float('nan')))
        lines.append('- diff 95%% CI = %s' % b1_report.get('diff_mild_ci95'))
    lines.append('')

    lines += ['## B2 可预测性（D51-B2，H=5，测试集）', '']
    if b2_report is None:
        lines.append('S4 未完成或失败，无数据。')
    else:
        lines.append('D51-B2 通过：**%s**' % b2_report.get('d51_b2_pass'))
        lines.append('')
        lines.append('| 分类器 | 测试 AUROC | 95% CI | 测试 AUPRC |')
        lines.append('|---|---|---|---|')
        for cname, c in b2_report.get('classifiers', {}).items():
            auroc = c['test_auroc']
            auprc = c['test_auprc']
            lines.append('| %s | %.4f | %s | %.4f |' % (cname, auroc['point'], auroc['ci95'], auprc['point']))
        lines.append('')
        lines.append('| 比较 | 均值差 | 95% CI |')
        lines.append('|---|---|---|')
        for key, d in b2_report.get('d51_b2', {}).items():
            lines.append('| %s | %.4f | %s |' % (key, d['mean'], d['ci95']))
    lines.append('')

    lines += ['## B3 闭环干预（探索性，不作通过依据）', '']
    lines.append('| 臂 | 回合数 | SR | perfect-success | ik_limit比例 | 平均触发次数 |')
    lines.append('|---|---|---|---|---|---|')
    for arm in ['none', 'random', 'geo', 'cur', 'hist', 'wm']:
        stats = _episode_stats(root / 's5-b3-shield' / arm / 'episodes' / 'episodes.jsonl')
        if stats is None:
            lines.append('| %s | - | - | - | - | - |' % arm)
        else:
            lines.append('| %s | %d | %.3f | %.3f | %.3f | %s |' % (
                arm, stats['episodes'], stats['success_rate'], stats['perfect_success_rate'],
                stats['ik_limit_fraction'], ('%.2f' % stats['mean_shield_triggers']) if stats['mean_shield_triggers'] is not None else '-'))
    lines.append('')

    lines += ['## 产物路径', '',
              '- A 线：`%s`' % (root / 's1-a-structured' / 'probe' / 'report.json'),
              '- B1：`%s`' % (root / 's2-b1-avoidability' / 'analysis' / 'report.json'),
              '- B2 采数：`%s`' % (root / 's3-b2-collect' / 'episodes'),
              '- B2 分类器：`%s`' % (root / 's4-b2-foresight' / 'train' / 'report.json'),
              '- B3 六臂：`%s`' % (root / 's5-b3-shield'), '']

    a_pass = a_report.get('d50_pass') if a_report else None
    b1_pass = b1_report.get('passes_d51_b1') if b1_report else None
    b2_pass = b2_report.get('d51_b2_pass') if b2_report else None
    lines += ['## 结论（不超过10行）', '',
              '- A 线（D50）：%s。' % ('通过' if a_pass else ('不通过' if a_pass is not None else '未完成')),
              '- B1（D51-B1）：%s。' % ('通过' if b1_pass else ('不通过' if b1_pass is not None else '未完成')),
              '- B2（D51-B2）：%s。' % ('通过' if b2_pass else ('不通过' if b2_pass is not None else '未完成')),
              '- B3 为探索性证据，六臂对比结果见上表，不作为独立通过依据。',
              '- 本报告只陈述预登记判据的通过/不通过结果，不建议修改 D50/D51；最终解读与后续方向由用户决定。', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    print(build_report(sys.argv[1]))
