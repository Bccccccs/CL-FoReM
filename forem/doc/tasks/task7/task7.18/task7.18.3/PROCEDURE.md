# task7.18.3 — 流程

状态：**review（2026-10-21：尝试与测量完成，严格连续等价失败，候选未采用；待Claude复核及口径决定）**。详见[RESULTS](RESULTS.md)、[SRC-0552](../../../../SOURCES.md#src-0552)。目标与验收见[TASK](TASK.md)。

## 递归规则

本节点恰有TASK.md、PROCEDURE.md、RESULTS.md三份主要文档；如需拆分，子任务放本目录并继承编号（task7.18.3.1…），每个子节点同样三文档；父RESULTS汇总子RESULTS，编号稳定不复用。

## 执行步骤

1. 开工核查：GPU3无compute进程；读task7.18 RESULTS性能节与SRC-0472；基线测更新耗时与E256训练步吞吐。
2. 逐项尝试优化，每项先写等价测试（≥1000次连续更新轨迹对照）。
3. 采用有收益且等价的方案，配置开关默认指向已验证路径。
4. 端到端E256≥2000步吞吐对照与5M墙钟推算。
5. 写RESULTS与日志；PROGRESS本行改review。

## 模型推荐

同[TASK](TASK.md)。

执行交接推荐：Codex GPT6.1sol/high（CUDA/RNG连续核查），Claude Sonnet5.5/medium（复核）。实际执行Codex gpt-6.1-sol/high；未改变原等价/预算规格。
