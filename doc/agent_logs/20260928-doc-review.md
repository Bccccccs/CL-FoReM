# DOCREV-028 全量文档审查：过时路径与过时指令清理

- 任务 ID：DOCREV-028
- 执行 Agent：Claude Opus 5.5 /ybc
- 开始时间：2026-09-28T16:11+08:00
- 状态：active
- 用户要求：“审查一次全部的文档，把过时的目录修改，过时的指令删除或修改”；此前一条请求为“现在是否可以开启第一阶段流程，请给出提示词”，Stage0 提示词 v2 已过时，并入本任务一起更新。
- 范围：维护中与参考文档（AGENTS、ENV、doc/*.md、doc/P0/*、docker 下说明性文件、Stage0 提示词）。不改写 `doc/archive/`（用户：不再看）与已完成任务的历史日志/证据（实测记录，只能追加说明）；DECISIONS 只追加，不改写旧条目。
- 依据：D40（ROADMAP 唯一执行计划）、D41（路径 CL-FoReM）、D42（单仓库、GitHub origin）。

## 进度记录
- 16:11 登记。通读 AGENTS、ENV、README、PROGRESS、ROADMAP、DECISIONS、EVALUATION、SYSTEM_PIPELINE、WM_RESEARCH_DESIGN、RELATED_WORK、RESEARCH_GOAL/EXPERIMENTS/RECORDS、P1_MEMORY_PLAN、P0–P5；脚本检查全部相对链接。
- 发现（摘要）：AGENTS §4 阶段表与 D40 冲突、§3 链接已归档 REVIEW.md、§5–§8 为 09-22/来源机器状态；ENV 后半为来源机器命令（`cd /home/yanbochao`、默认容器 `mmhusky-p0-ready`、`mm_husky:deps` 构建、“严格复现失败”），run.sh 默认值同样过时；P0–P5 共 6 处要求使用本环境不存在的 “executing-plans 技能”；多份参考文档仍写 D33/D29 待修；RESEARCH_EXPERIMENTS §8 旧计划与 ROADMAP 冲突；RESEARCH_RECORDS“根仓库不跟踪主包”已被 D42 推翻；Stage0 提示词 v2 含“不得重建 node01 容器”“不 commit”等过时指令；PROGRESS/P0 文档共 14 处链接指向丢失的 09-22 日志（宿主与容器 find 均无副本）。
- 改动：AGENTS/ENV 重写（原文存 archive/20260928-docrev/）；run.sh 默认 node01 + build 用 Dockerfile.node01；PROGRESS 删过时优先事项行与底部历史小节（存快照）、断链改“正文缺失”、DOCS-028 行置 done；P0 README 重写、PLAN/ACCEPTANCE 断链处理；P1–P5/P0 删 executing-plans；P1 状态横幅合并、文件清单改为已实现；EVALUATION/SYSTEM_PIPELINE/WM_DESIGN/RELATED_WORK/RESEARCH_*/P1_MEMORY_PLAN 状态更新；README/ROADMAP §11 更新；删除 6 个 agent_logs 跳转占位；新增 Stage0 提示词 v3，v2/handoff 标注作废；DECISIONS 追加 D43。
- 验证（实测）：`bash -n docker/run.sh` 通过；`sg docker -c 'bash docker/run.sh exec true'` 用新默认值成功；p0_runner 参数表核对 ENV 中命令的全部 flag 存在；链接检查：维护中/参考文档 0 断链、agent_logs 0 断链；过时关键词（executing-plans、/home/yanbochao、projects/mm_husky_ws、REVIEW.md、prompt-v2）在现行文档中仅剩带“来源机器/历史”标注的出现。
- 未改：archive、历史任务日志正文、DECISIONS 旧条目、ENV 中节选保留的 node01 验收原文。
- 状态：done。
