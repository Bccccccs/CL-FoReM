# task5.5 cbl自写SAC GPU版sim训练500万步 — 任务

> **当前状态（2026-10-20 Claude复核）：done（训练与最终sim评估完成，入账经独立复核通过）——以本节点RESULTS为准。** 本文件下方的启动/监控表述为历史流程，不授权新的执行。依据[SRC-0394](../../../SOURCES.md#src-0394)。

状态：**done（训练及最终sim评估结束，10-20 Codex入账、Claude复核通过；见[RESULTS](RESULTS.md#claude独立复核2026-10-20)）**。上级：[task5](../TASK.md)。启动与监控：Claude；最终评估执行人Codex（2026-10-19用户明确派发）。

## 用户要求与授权

用户2026-10-14：先要求把cbl的SAC训练500万步；得知RLlib版（task5.4）只能用CPU后，明确改为“用cbl写的那个sac做，然后改成在gpu跑”“方法一样就可以不必追求细节”；并选择：用Task3已迁移链路、sim训练、停掉task5.4、3个种子并行、不做额外性能优化“直接启动”。

## 背景

- “cbl写的SAC”指Husky快照`scripts/main.py`+`sac.py`（PyTorch自写SAC，`sac.py:34`本身用cuda；`main.py:138` `num_steps=5000001`）。原`main.py`先加载不存在的`/home/cbl/.../sac_checkpoint_husky_ur5_4000`作prior并`resume`，走`update_parameters_modified`，无法原样从头训练。
- Task3已把该SAC迁移到forem-dev（torch 2.7.1+cu128、ray 1.13、noetic），派生`ScwmSAC`：更新数学逐行沿用`SAC.update_parameters`（普通更新，无prior），另含task4.7的单tanh predict修正与GPU replay。task4.8（Gazebo）与task6.1 F0（sim，1M×3种子，sim内部成功平均43.3%）用的就是这条链路。
- 学习率按`lr_horizon_updates=5000001`指数衰减（1e-4→1e-6），这正是cbl `main.py`的5M设定；F0的1M只走完该日程的前1/5。因此本任务前1M的日程与F0相同。
- 与RLlib版（cbl移植+上游`main_ray.py`，task5.2 1M时simpleobstacle sim 0.78）不是同一实现，不能把两者当同配方比较。

## 目标

用F0协议、只把总步数改为500万，看cbl自写SAC在完整设计步数下能否明显超过1M（43%）的水平，并给出可用于后续世界模型工作的基线候选。

## 范围

- 包含：3种子（0/1/2）×5M，sim，GPU 0/1/2；训练中D15筛选评估（50种子3001–3050）与验证（101–105）按F0协议；训练完成后按task6.1最终评估口径评估。
- 不包含：任何算法/超参/观测/奖励改动；性能优化改造；Gazebo训练或评估；世界模型。需要时另行授权。

## 交付与验收

- 三条run正常训练到5M（或如实记录异常）；1M/2.5M/5M读数与task6.1 F0同步数并列。
- 最终评估结果及与F0（1M）、task5.2（RLlib 1M）的对照，注明实现与评估口径差异。

## 模型与推理强度

|角色|Codex推荐|Claude推荐|理由|
|---|---|---|---|
|监控/读数|GPT6.1sol / low|Sonnet5.5 / low|只读进度文件|
|最终评估与汇总|GPT6.1sol / medium|Sonnet5.5 / medium|需核对评估口径与跨实现对照|

实际配置：启动由Claude（claude-opus-5-5）完成。

## 2026-10-19用户派发

用户要求“你启动一下验证”，已启动上述既定三策略最终sim评估；范围及协议不变，证据[SRC-0380](../../../SOURCES.md#src-0380)。运行状态以RESULTS与原始日志为准。

## 2026-10-20已有结果入账

本轮只读现有产物并写文档，没有运行评估/训练或容器/实例操作。最终sim内部成功32/33/30（各50），与F0场景逐种子一致；配置追溯与限制见[RESULTS](RESULTS.md#最终评估)及[SRC-0394](../../../SOURCES.md#src-0394)。本节点review，待Claude/用户复核；推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（核对脚本版本与评估口径），实际模型/强度未知。
