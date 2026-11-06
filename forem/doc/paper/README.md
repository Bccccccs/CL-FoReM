# 论文主线入口

2026-10-21按用户指令建立（[SRC-0430](../SOURCES.md#src-0430)）。FoReM文档分三条并行主线：

|主线|位置|内容|
|---|---|---|
|项目主线|[doc根目录](../README.md)与[tasks/](../tasks/)|现有全部文档；环境、实现、训练等开发工作继续在这里推进|
|实验主线|[experiments/](../experiments/README.md)|论文所需实验的设计、协议与结果汇总|
|**论文主线**|本目录`paper/`|论文的设计与写作|

已开展[paper3前沿调研](paper3/RESULTS.md)、paper0投稿调研、paper1叙事候选与[paper2](paper2/TASK.md)SAC实现/消融呈现建议；论文题目、主贡献与venue仍未定，未写完整论文。

## 与其他主线的关系

- 论文中的实验设置与数字以实验主线文档为准，通过链接引用，不在本目录另记一套。
- 论文中需要论据的表述同样在`../SOURCES.md`登记出处；`DECISIONS.md`、`PROGRESS.md`为三条主线共用；根[AGENTS](../../../AGENTS.md)的全部约定同样适用。

## 放置规则

- 本目录内部的文档结构（提纲、各章草稿、图表等）在开始实际论文设计时确定。
- Agent过程记录放`../agent_logs/paper/`（首次需要时再创建）。

## 文档索引

|文档|内容|状态|
|---|---|---|
|[paper0](paper0/TASK.md)|投稿venue（CCF-A）、发表门槛与实验设计调研（只调研，SRC-0600）|已授权，Codex执行|
|[paper1](paper1/TASK.md)|叙事框架候选：两层SAC与生物运动系统分工的类比（SRC-1300；文献待核验）|draft，仅记录|
|[paper2](paper2/TASK.md)|下层SAC实现说明与基线消融呈现（SRC-1341）|review，建议已记录|

|[paper3](paper3/TASK.md) · [完整报告](paper3/RESULTS.md)|观测差异与底座—机械臂协调：19篇筛选/8篇核心原文，3方案及最小验证|done（仅调研交付，方案未实施）|

## Agent模型与推理强度

建立和维护本入口属普通文档整理：Codex推荐GPT6.1sol，Claude推荐Sonnet5.5，推理强度低（low）或平台默认，无特殊推理要求。论文设计的推荐在相应文档中另写。
