# task6 Task4.8失败原因对照组 — 结果与交接

> **当前状态（2026-10-19核对）：active：6.1、6.3 done；6.2 paused；6.4阶段一done、阶段二暂缓；6.5阶段一review待复核。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

> **阶段一（CBL复现）· Gazebo失败诊断**（2026-10-16归类）：6.1 done——F0（cbl自写SAC，sim）0.433，F1–F6单参数无显著提升；6.2（RLlib在Gazebo训练）paused于26.9万步，评估0.02–0.04；6.3 done——F0零样本到Gazebo 0.16/0.20；6.4阶段一done——CBL原版B sim 0.78→Gazebo 0.72、上游PR2 0.78→0.32；6.5阶段一review——原作者PR2 sim 0.86→Gazebo 0.52。世界模型不在本任务，见[task7](../task7/TASK.md)。

状态：**active（2026-10-13：task6.1 done；task6.2 G-B正式训练运行中，30万步后由用户决定是否跑满）**。本文件只汇总子任务结果，不替代子RESULTS；计划内容见[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)。

## 子任务状态

|节点|状态|结果|
|---|---|---|
|task6.1 ScwmSAC sim组|done（Claude复核R4）|[RESULTS](task6.1/RESULTS.md)|
|task6.2 RLlib Gazebo组|active（t6.2-gz-train-s40运行中）|[RESULTS](task6.2/RESULTS.md)|
|task6.3 sim策略Gazebo零样本迁移|done（Claude复核R3）：sim 0.433 → Gazebo 0.160（R-48同口径）/0.200（原论文配置）；R-48 0.053|[RESULTS](task6.3/RESULTS.md)|
|task6.4 task5 A/B按原论文Gazebo零样本评估|尚未执行（2026-10-13文档交付，待用户派发）|[RESULTS](task6.4/RESULTS.md)|
|task6.5 原作者模型复现N²M²|尚未执行（2026-10-14文档交付，待用户派发）|[RESULTS](task6.5/RESULTS.md)|
|task6.6 评估CBL自己的检查点|done（2026-10-27，Claude复核通过）：15个CBL检查点合计S 360/750＝0.480（单个19–27/50），Z-B 0.223，Z-A 0.236；全部低于task5.5的sim最低种子30/50，Gazebo同样约降一半|[RESULTS](task6.6/RESULTS.md)|

## 四组对照表（父汇总时填写）

|组|训练器/环境|15万步|30万步|100万步/最终|最终50 episode|口径|
|---|---|---|---|---|---|---|
|R-B|RLlib/sim|0.52|0.66（30万）|待task5完成|待task5.3|RLlib训练中评估，50 ep，eval_seed 999|
|R-48|ScwmSAC/Gazebo|—|—|最终验证0/15|待6.1 Gazebo侧评估|5种子验证；最终评估种子2001–2050|
|F0|ScwmSAC/sim|尚未执行|尚未执行|尚未执行|尚未执行|D15评估与5种子验证|
|G-B|RLlib/Gazebo|尚未执行|尚未执行|尚未执行|尚未执行|RLlib训练中评估，同R-B|

R-B数值来自`results/task5/t5.2-train-s40/monitor_30min.jsonl`的中期读数（2026-10-12 08:40），不是task5最终验收。

## 历史（重新开始前）

- 原task6 R0（SRC-0222）：单因素对照，ScwmSAC只改到sim。
- Codex §1预检：Task4.8 plain三个manifest的54项源码hash与当时工作树全部一致；发现sim切换会改变近目标终止阈值（SRC-0223）；D12参数转发缺口（SRC-0225）。证据：`results/task6/baseline_source_diff.json`、`results/task6/t6-preflight-r1/`、`results/task6/t6-d12-preflight-r1/`，均保留。
- Claude R1（D12强制sim为500、D13以当前代码为基线）、R2（D12改两处，放行拟议patch；SRC-0224、SRC-0226）。R2放行后patch**未被应用**：2026-10-12 09:27核查`modulation/utils.py` sha256仍为`a2d851e7…`。
- Claude R3（SRC-0228）：改造为F0–F6对照组。
- 原task7（SRC-0227）：B改在Gazebo，只有文档，无任何运行或容器。
- 2026-10-12 用户要求task6重头开始，并把task7合并进来（SRC-0229）。上述全部文档原文存档于[archive-20261012-pre-restart](../../agent_logs/task6/archive-20261012-pre-restart/)；D12、D13及R2的patch审查结论由task6.1沿用。

## 交接

- 当前负责人：Claude（流程，已交付）；task6.1、task6.2由用户派发Codex执行。
- 派发提示词：[20261012-claude-task6-restart-prompts.md](../../agent_logs/task6/20261012-claude-task6-restart-prompts.md)。
- 下一步：两个Codex会话分别执行task6.1和task6.2；F0到15万/30万步、6.1筛选完成、6.2确定N时回报Claude。
