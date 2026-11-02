# 实验主线入口

2026-10-21按用户指令建立（[SRC-0430](../SOURCES.md#src-0430)）。FoReM文档分三条并行主线：

|主线|位置|内容|
|---|---|---|
|项目主线|[doc根目录](../README.md)与[tasks/](../tasks/)|现有全部文档；环境、实现、训练等开发工作继续在这里推进|
|**实验主线**|本目录`experiments/`|论文所需实验的设计、协议与结果汇总|
|论文主线|[paper/](../paper/README.md)|论文的设计与写作|

2026-10-31开始[experiment0](experiment0/TASK.md)下层SAC基线选择与优化设计；运行授权/边界以SRC-1336及task9.5为准，本文不额外授权其他实验。

## 与其他主线的关系

- 实验所需的代码、环境与训练流程在项目主线的任务中实现；实验文档链接对应任务，不复制其参数与协议。代码、配置、日志、产物仍分别放`forem/src`、`config`、`logs`、`results`。
- 论文主线引用本目录的实验设计与结果，不另记一套实验数字。
- `SOURCES.md`（论据台账）、`DECISIONS.md`（决策记录）、`PROGRESS.md`（唯一活动进度表）为三条主线共用；根[AGENTS](../../../AGENTS.md)的全部约定（授权、论据登记、三文档、模型推荐等）同样适用。

## 放置规则

- 每项实验一个目录，内含TASK / PROCEDURE / RESULTS三文档，沿用根AGENTS项目级任务组织规则；目录编号与命名在建立第一项实验时确定。
- Agent过程记录放`../agent_logs/experiments/`（建立第一项实验时再创建）。

## 实验索引

|编号|内容|状态|三文档|关联项目任务|
|---|---|---|---|---|
|experiment0|下层SAC参数/更新机制优化与基线选择|active，新增训练尚未执行|[TASK](experiment0/TASK.md) / [PROCEDURE](experiment0/PROCEDURE.md) / [RESULTS](experiment0/RESULTS.md)|[task9.5](../tasks/task9/task9.5/TASK.md)|

## Agent模型与推理强度

建立和维护本入口属普通文档整理：Codex推荐GPT6.1sol，Claude推荐Sonnet5.5，推理强度低（low）或平台默认，无特殊推理要求。具体实验设计的推荐在各实验三文档中另写。
