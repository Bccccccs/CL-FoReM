# FoReM 文档入口

共同约定：[根AGENTS.md](../../AGENTS.md)。当前状态见[PROGRESS](PROGRESS.md)，总体计划见[PLAN](PLAN.md)。

2026-10-16按用户指令整理：现有任务归为阶段一“CBL复现”，task7起为阶段二“世界模型闭环”；无用文档已删除，原文备份见[SRC-0321](SOURCES.md#src-0321)。

## 三条主线

2026-10-21按用户指令分为三条并行主线（[SRC-0430](SOURCES.md#src-0430)）：

|主线|入口|内容|
|---|---|---|
|项目主线|本文与[tasks/](tasks/)|现有全部文档；开发工作继续在这里推进|
|实验主线|[experiments/](experiments/README.md)|论文所需实验的设计、协议与结果汇总（尚未设计）|
|论文主线|[paper/](paper/README.md)|论文的设计与写作（尚未设计）|

`PROGRESS`、`DECISIONS`、`SOURCES`三条主线共用。

## 目录

```text
forem/doc/
  README.md      本入口
  PLAN.md        两阶段总体计划与阶段一结论
  PROGRESS.md    唯一活动进度表
  DECISIONS.md   决策记录
  SOURCES.md     论据来源台账
  tasks/         一任务一目录，每层 TASK / PROCEDURE / RESULTS 三文档
  experiments/   实验主线（入口README）
  paper/         论文主线（入口README）
  agent_logs/    Agent过程记录，按 project/ 与 taskN/taskN.M/ 镜像任务编号；TEMPLATE.md为模板
```

`agent_logs/`是各次会话的**历史过程记录**，记载当时的判断与计划，可能已被后续决定取代（例如2026-10-07至10-09关于视觉惯性定位和旧Task4路线的日志）。它们不是指令；当前事实以任务三文档、PROGRESS、PLAN和DECISIONS文末条目为准。

## 任务

|阶段|任务|内容|状态|三文档|
|---|---|---|---|---|
|一 CBL复现|task0|forem-dev容器与ROS/Gazebo环境（基础设施）|done|[TASK](tasks/task0/TASK.md) · [PROCEDURE](tasks/task0/PROCEDURE.md) · [RESULTS](tasks/task0/RESULTS.md)|
|一|task3|CBL（Husky+UR5）核心迁移到FoReM|done|[TASK](tasks/task3/TASK.md) · [PROCEDURE](tasks/task3/PROCEDURE.md) · [RESULTS](tasks/task3/RESULTS.md)|
|一|task4|Gazebo普通SAC基线与首次WM尝试|closed|[TASK](tasks/task4/TASK.md) · [PROCEDURE](tasks/task4/PROCEDURE.md) · [RESULTS](tasks/task4/RESULTS.md)|
|一|task5|上游N²M²与CBL原版的sim对照训练；5.5 cbl自写SAC sim 5M|5.0–5.3 done；5.4 paused；5.5 done|[TASK](tasks/task5/TASK.md) · [PROCEDURE](tasks/task5/PROCEDURE.md) · [RESULTS](tasks/task5/RESULTS.md)|
|一|task6|Task4.8 Gazebo失败原因诊断|6.1/6.3 done；6.2 paused；6.4阶段一done；6.5阶段一review|[TASK](tasks/task6/TASK.md) · [PROCEDURE](tasks/task6/PROCEDURE.md) · [RESULTS](tasks/task6/RESULTS.md)|
|二 世界模型闭环|task7|SC²-WM式预测—修正闭环接入SAC；自写环境训练，ManiSkill验证|draft（未授权实施）|[TASK](tasks/task7/TASK.md) · [PROCEDURE](tasks/task7/PROCEDURE.md) · [RESULTS](tasks/task7/RESULTS.md)|

task1、task2编号已删除，不复用。子任务入口见各任务PROCEDURE。

## 放置规则

任务计划/流程/结果只写在对应`tasks/`节点三文档；Agent过程记录放`agent_logs/<project | taskN | taskN/taskN.M>/`（实验主线、论文主线分别放`agent_logs/experiments/`、`agent_logs/paper/`），文件名`YYYYMMDD-agent-topic.md`；代码、配置、日志、产物分别放`forem/src`、`config`、`logs`、`results`。
