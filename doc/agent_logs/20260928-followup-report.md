# FOLLOWUP-028 G0 后续双线检验：自动汇总报告

本报告由 `followup_pipeline.py` S6 阶段自动生成，只陈述结果，不建议修改 D50/D51 判据。

## A 线（结构化低维适应，D50）

D50 通过：**False**

| 变体 | 达标强失配条件数(/4) | 名义未变差 | 通过 |
|---|---|---|---|
| V4_robot | 0 | True | False |
| V4_both | 0 | True | False |
| V5_delay | 0 | True | False |
| V6_delay_gain | 0 | False | False |

## B1 可避免性（D51-B1）

D51-B1 通过：**False**

- fail_to_success_fraction (mild) = 0.310
- success_to_fail_fraction (mild) = 0.286
- diff 95% CI = [-0.17044334975369457, 0.22561576354679808]

## B2 可预测性（D51-B2，H=5，测试集）

S4 未完成或失败，无数据。

## B3 闭环干预（探索性，不作通过依据）

| 臂 | 回合数 | SR | perfect-success | ik_limit比例 | 平均触发次数 |
|---|---|---|---|---|---|
| none | - | - | - | - | - |
| random | - | - | - | - | - |
| geo | - | - | - | - | - |
| cur | - | - | - | - | - |
| hist | - | - | - | - | - |
| wm | - | - | - | - | - |

## 产物路径

- A 线：`/root/mm_husky_ws/results/followup-028/s1-a-structured/probe/report.json`
- B1：`/root/mm_husky_ws/results/followup-028/s2-b1-avoidability/analysis/report.json`
- B2 采数：`/root/mm_husky_ws/results/followup-028/s3-b2-collect/episodes`
- B2 分类器：`/root/mm_husky_ws/results/followup-028/s4-b2-foresight/train/report.json`
- B3 六臂：`/root/mm_husky_ws/results/followup-028/s5-b3-shield`

## 结论（不超过10行）

- A 线（D50）：不通过。
- B1（D51-B1）：不通过。
- B2（D51-B2）：未完成。
- B3 为探索性证据，六臂对比结果见上表，不作为独立通过依据。
- 本报告只陈述预登记判据的通过/不通过结果，不建议修改 D50/D51；最终解读与后续方向由用户决定。
