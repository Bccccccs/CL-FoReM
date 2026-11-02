# task7.18.6 — 流程

状态：**训练中（见RESULTS）**。目标见[TASK](TASK.md)。

## 递归规则

本节点恰有TASK.md、PROCEDURE.md、RESULTS.md三份主要文档；如需拆分，子任务放本目录并继承编号，每个子节点同样三文档；父RESULTS汇总子RESULTS，编号稳定不复用。

## 执行步骤

1. 实现C″（训练开关，同failure_mode）与IK避碰分支选择（生产默认启用，因属IK选择规则，影响执行/推演/G7）。
2. 测试与对照、吞吐。
3. 初次启动v5同步5M时规则a/b沿用；**当前续训以[SRC-0916](../../../../SOURCES.md#src-0916)及[RESULTS第6节](RESULTS.md)为准：看门狗须用`--share-min-step 6000000`停用规则a，保留b。** 不得按旧≥1M参数重启。2026-10-23接手审核核实当前进程参数正确，见[SRC-0963](../../../../SOURCES.md#src-0963)。
4. 写RESULTS。

## 模型推荐

|Agent|模型|推理强度|理由|
|---|---|---|---|
|Claude子Agent（执行）|Sonnet5.5|medium|跨IK/环境/训练入口的小范围改动与验证|
|Codex（额度恢复后）|GPT6.1sol|medium|同上|

文档作者：Claude（claude-opus-5-5，推理强度未知），2026-10-22。
