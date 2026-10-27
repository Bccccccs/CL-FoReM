# task8.4 — 整环境与决策接口迁入PCD

状态：**done（2026-10-26本节点父及独立Sol high验收通过；语义图与总验收待后续）**。实际实施/独立复核均gpt-6.1-sol/high；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨模块状态合同需推理。证据[SRC-0995](../../../SOURCES.md#src-0995)，历史过程保留。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 依赖、文件范围与交付

依赖：8.2、8.3完整验收；不能只靠mock开始最终集成验收。

- 新建`forem/src/task8_sim/episode.py`、`routes.py`、`env.py`、`decision_env.py`，`tests/test_pcd_env.py`、`tests/test_pcd_decision.py`、`forem/config/task8/environment.json`。
- 只读复用task7 Core/运动学/route基础原语/Grid/候选/局部rollout；必要小段复制注明原文件符号与hash，不改原文件。
- 不改SAC训练器/奖励公式/候选生成/终止判据，不恢复旧full checkpoint环境。

## 接口

输出PcdEpisodeSampler/PcdTruthPlanner/PcdEpisodeEnv/PcdDecisionEnv，签名依父PROCEDURE；Episode以scene替代boxes。新环境显式profile，sync_v5与两种decision_*_legacy参数取父TASK；决策环境只能用decision profile，不能将cbl_continue传给execute=False的局部推演。通过原transition和observation接口供下层调用，不引入truth字段。

## 验收与范围限制

`test_pcd_env.py`核PCD-only从reset至step、新扫描时间戳、base/arm/self三类失败、点云输入越界错误/动作出域不新增终止、mask reset逐字段不变、seed/RNG复现。`test_pcd_decision.py`核候选→本地推演→选点→下层动作→执行→下一边界、两变体张量形状、profile不串线、truth泄露反例与旧pickle环境拒绝。不以随机策略到不了目标判定接口失败，也不以只跑零动作判定全链路完成。

遵守父任务不改科学条件、仅有界验收、task7只读、无训练的约束。实现后的子结果只由父复核后纳入父验收，不自行更新共享文档。日志路径`forem/doc/agent_logs/task8/task8.4/YYYYMMDD-agent-topic.md`。本节点交付不等于整个task8完成。
