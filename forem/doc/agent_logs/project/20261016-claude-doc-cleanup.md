# 2026-10-16 Claude：文档两阶段整理与清理

- 用户要求：“我们现在的干扰很多，请你检查现在的文档，把现有的task作为对CBL项目的复现，然后task7开始我们从头构建我们的世界模型闭环项目，把无用文档删掉”。删除范围经用户在选项中逐项确认。
- 执行：Claude（claude-opus-5-5，推理强度未知）。只改文档，不改源码/配置/日志/产物，不触碰运行中的task5.5。
- 备份：`/home/ybc/projects/CL-FoReM-reset-backups/20261016-doc-cleanup/forem-doc-before-cleanup.tar.gz`（465文件，SHA256见同目录`SHA256SUMS`）。

## 改动

- 删除：`tasks/task1`、`tasks/task2`、`experiment/`、`tasks/task4/task4.{1..6,11,12,13}`；`agent_logs/task1`、`agent_logs/task2`、`agent_logs/experiment`、`agent_logs/task4/task4.{1..4}`、`agent_logs/task4`下视觉惯性时期的4个日志与2026-10-09文档快照目录及两份json。
- 恢复：`tasks/task4/task4.9`、`task4.10`（删除后发现含实际WM负结果与反馈臂实现，从备份恢复）。
- 移动：`agent_logs/20260930-claude-task0-fix3.md` → `agent_logs/task0/task0.12/`。
- 重写：`README.md`、`PLAN.md`、`PROGRESS.md`（旧版在备份）、`tasks/task4/{TASK,PROCEDURE,RESULTS}.md`、`forem/AGENTS.md`；根`AGENTS.md`改写§1、精简§2/§6并删除按日期追加的旧状态段与旧§4研究顺序。
- 追加：task0/3/5/6的TASK与RESULTS顶部阶段标注；新建`tasks/task7`三文档（draft）；`SOURCES.md` SRC-0321–0323及顶部删除说明；`DECISIONS.md`条目。

## 遗留

- SOURCES与历史日志中指向已删除路径的链接未逐条修改，以备份为准。
- task7的Q1–Q9待用户确认；task5.5训练中。
