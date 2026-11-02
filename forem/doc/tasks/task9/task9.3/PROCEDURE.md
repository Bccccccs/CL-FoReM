# task9.3 PROCEDURE — B0退化机制诊断与解决流程

状态：**active**。依据[TASK](TASK.md)；授权[SRC-1319](../../../SOURCES.md#src-1319)。

## 递归规则声明

遵守根AGENTS项目级任务组织规则：每层恰有TASK/PROCEDURE/RESULTS；如需拆分，在本目录内建task9.3.1…并各自三文档，父列明顺序、依赖、负责人与验收，父结果汇总子结果。当前S1–S3作为本节点内的阶段，由同一执行者顺序完成，不拆子节点；阶段2实验获批后另建子任务。

## 顺序与负责人

|阶段|内容|依赖|负责人|
|---|---|---|---|
|S1|代码对照审计|—|Codex GPT6.1sol / high（可派terra抽取，Sol复核）|
|S2|离线诊断|S1的差异清单|同上|
|S3|报告与阶段2设计，停止|S1、S2|同上|
|V4|独立核验|S3|另一Sol / high（父另派）|

## S1 代码对照审计

输入（只读）：
- CBL自写：`archive/husky_ur5/mm_husky_ws/src/modulation_rl/scripts/sac.py`；task5.5所用版本（见[task5 RESULTS](../../task5/RESULTS.md)的5.5节及`forem/scripts/scwm_sac.py`，SRC-0470）。
- 本项目：`forem/src/task7_lower/{sac.py,networks.py,training.py}`、`forem/src/task8_lower/{sac.py,training.py,replay.py,diagnostics.py}`。
- RLlib：`mobile-rl/scripts/modulation/myray/{custom_sac.py,ray_utils.py}`、`mobile-rl/scripts/modulation/utils.py`、`mobile-rl/scripts/configs/best_defaults_ray.yaml`、`mobile-rl/scripts/model_checkpoints/*/config.yaml`；CBL运行时`archive/husky_ur5/mm_husky_runtime/`（SRC-1000）；所用ray版本中被custom_sac导入的内置SAC函数（在上游容器如`forem-t5-pr2`、`forem-t5-husky`内只读查找site-packages，记录版本；不修改容器）。

逐项对照（至少）：critic损失形式（MSE/Huber及delta、0.5系数、两critic是否分开优化）；TD目标（min双Q、熵项、n_step、done/截断mask，与`cbl_continue`、`episode_end_bootstrap`的交互）；actor损失（α是否detach、用哪个critic）；α参数化/初值/学习率/日程/上下限/冻结；target entropy；actor/critic学习率与日程（按更新数或时间步）；梯度裁剪；tau与目标网络更新频率；UTD/training_intensity换算；批量、回放容量与优先回放；采样方式（256同步环境 vs RLlib worker）；动作压缩与log_prob修正、log_std范围；网络结构与初始化；观测预处理；warmup。每项标明：B0取值、B3取值、RLlib取值、是否已有实测。另外列出本项目实现中的可疑点：α张量是否带计算图进入下一步、调度器步进时机、`update_due`判定、诊断统计口径等。

产物：`forem/logs/task9/t9-b0diag-20261029/s1-code-audit.md`。

## S2 离线诊断

只读原件：task9.2四run（`forem/results/task9/t9-long-20261028/*/learning.jsonl`、`validation-*.json`中的rows `first_Q`/`discounted_MC_return`/`Q_minus_MC`/失败码）；task7 v5（`forem/results/task7/t7.18-v5-20261022/formal-v5-sync/`，SRC-1101）；task5.5 CBL自写SAC sim 5M日志；CBL RLlib的result.json（SRC-1000）。

要做的分析：
1. 四run（及v5）以下指标的时间线：熵−目标、α、Q均值/|Q|max、critic loss、回放奖励均值、失败比例、样本年龄、验证/迁移成功率、评估`Q_minus_MC`。给出关键事件的首次出现步数（熵<目标、熵<目标−1、Q均值<0、critic loss>1、失败比例翻倍、验证从峰值下降≥0.15），判断先后顺序。
2. task5.5与RLlib运行中是否有同类信号（熵是否越过目标、α轨迹），用来检验M1/M2的普适性。
3. 按M1–M5逐条写支持/反驳证据。
4. 可选只推理探针：在一块经`nvidia-smi --query-compute-apps`核实为空的GPU上，加载task9.2已有检查点（B0 250k/500k/…/diverged、B3同步数），在固定状态集上计算Q、熵等，不做optimizer step，不写回原件。累计≤3600s，用新账本`forem/logs/task9/t9-b0diag-20261029/budget.json`记录每次的命令、GPU、耗时；检查点30GB+，注意宿主内存；不需要时就不跑。

产物：`forem/logs/task9/t9-b0diag-20261029/s2-diagnosis.md`（及抽取脚本、CSV）。

## S3 报告与阶段2设计（停止点）

产物：`forem/logs/task9/t9-b0diag-20261029/s3-report.md`，以及本节点RESULTS的执行者节。内容：
- 根因排序与置信度；明确哪些已证、哪些是推断。
- “推进是否必须解决B0”的结论与理由。
- 阶段2最小实验集：预注册B1（只改UTD）、B2（只改温度/学习率），以及S1/S2提出的新候选（如“B0+RLlib α”“B0+Huber”）；逐组写出相对B0的唯一差异、对应假设、可检验预测、种子数、步数、判据（沿task9预注册，另需处理“发散停止是否等同退化”的待决问题）、按task9.2实测外推的成本、GPU分配。新候选组须单独标明“非预注册，待用户批准”。
- 如需改代码（例如新增Huber开关），只写补丁设计与测试计划，不改生产代码。

**到这里停止**，不启动任何训练，交父汇总、V4复核、用户批准。

## 共同约束

- 不启动训练，不改生产代码语义，不改task7/8/9已有原件（results目录归root，只读）。
- 不停止他人进程/容器；docker使用`sg docker -c`。
- 只写本任务产物目录`forem/logs/task9/t9-b0diag-20261029/`、本节点RESULTS的“执行者”节、自己的日志`forem/doc/agent_logs/task9/task9.3/20261029-codex-b0-diagnosis.md`；不写PROGRESS/DECISIONS/SOURCES，主张草稿写到`.../sources-draft.md`交父登记。
- 外部文献（如高UTD可塑性、温度调节相关论文）只有在读过原文后才能写成“已核验”，否则标“待核验”。
