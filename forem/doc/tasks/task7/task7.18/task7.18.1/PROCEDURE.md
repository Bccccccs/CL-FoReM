# task7.18.1 — 流程

状态：**review（2026-10-21，诊断已交付；正式训练已STOP、不恢复；修复未实施）**。目标与验收见[TASK](TASK.md)。

## 递归规则

本节点恰有TASK.md、PROCEDURE.md、RESULTS.md三份主要文档。如需拆分，子任务放在本目录内并继承编号（如task7.18.1.1），每个子节点同样恰有三文档；本流程列明子节点顺序、依赖、负责人与验收关系；父RESULTS汇总子RESULTS，不以父计划代替子任务实测。编号稳定不复用。

2026-10-21 20:00更新以[TASK更新](TASK.md)与[SRC-0530](../../../../SOURCES.md#src-0530)为准；下列与“运行训练并行”有关的文字仅保留历史背景，不构成恢复权限。

## 共同要求

- 开工：读根AGENTS（含“功能范围硬性约束”“论据与引用来源”“性能优化共同要求”）、`forem/doc/README.md`、`PROGRESS.md`、`forem/ENV.md`、父[task7.18](../TASK.md)三文档与本节点三文档；PROGRESS“项目级记录”加本任务一行（写前重读、只改自己的行、定点编辑）；建独立日志`forem/doc/agent_logs/task7/task7.18/task7.18.1/YYYYMMDD-codex-diag.md`。
- 并行：task7.18正式训练（GPU2、GPU3）、task7.20等可能同时运行；不读写训练进程的内存或文件锁，只复制已完成的检查点（以`.meta.json`存在为准）。
- 规格或现象有歧义：日志“待决定”列出，继续其余部分；不自行修改阈值、几何或语义。

## 执行步骤

1. 开工核查：GPU0空闲；列出可用检查点（250k、500k等）并复制到产物目录；记录源码版本（与formal manifest对照）。
2. 训练日志与验证结果的统计复核（问题5的动作分布可直接从回放得到）。
3. 回放：每变体在验证地图上用固定种子回放一批段（数量按预算定，并记录），逐子步记录失败类型、几何体对、关节角、IK路径（精确/DLS）及其原因。
4. 网格复判（问题2、3）与DLS原因分解（问题4）。
5. CBL对照的事实陈述（问题6，代码路径:行号）。
6. RESULTS写结论与修复建议（不实施）；PROGRESS本行改review交Claude复核。

## 依赖与顺序

依赖task7.18已产生的检查点；与正式训练并行，不影响其运行。

## 异常处理

- 发现会让正式训练结果无效的确定性错误（如坐标变换错误）：立即在日志与PROGRESS本行标注，报告用户；不自行停止训练。

## 模型推荐

|Agent|模型|推理强度|理由|
|---|---|---|---|
|Codex|GPT6.1sol|medium|见TASK|
|Claude|Sonnet5.5|medium|同上（复核）|

推荐不等于实际配置；执行方在日志中记录实际模型与强度，无法核实写“未知”。

文档作者：Claude（claude-opus-5-5，推理强度未知），2026-10-21。

## 本次复核入口（run t7.18.1-r1-20261021）

实际方法与命令以[RESULTS](RESULTS.md)为准，来源[SRC-0530–0535](../../../../SOURCES.md#src-0530)。先查看原始JSONL/NPZ与commands账本；GPU0空闲并确认剩余累计预算后，可用`forem/scripts/task7_diag_run.py LABEL python3 -B -u scripts/task7_diag_summarize.py`、`task7_diag_verify.py`、`task7_diag_containment.py`复算（容器内cwd /root/mm_husky_ws）。不需要加载完整replay或恢复训练。首轮记录器的候选IK混入已在r2重跑排除，按最终playback.npz复核。

当前无进一步生产操作授权；后续修复另派。初态间隙分布在RESULTS明确按现有代理几何定义，网格复判和误报/漏报分母另列，不混用。
