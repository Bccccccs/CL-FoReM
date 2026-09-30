# 当前进度

|任务|Agent|状态|范围|开始时间|记录|
|---|---|---|---|---|---|
|ROOT-RESET|Codex /root|paused|恢复原始Husky源码、整理目录、克隆参考项目、核验仿真建议|2026-09-30 09:09 +08:00|[记录](agent_logs/20260930-original-reset.md)|
|FOREM-AGENTS|Codex /root|done|根AGENTS共同约定（Codex/Claude），仅文档|2026-09-30T09:35:52.388344+08:00|[记录](agent_logs/20260930-forem-agents.md)|
|FOREM-DOC|Codex /root|done|建立forem/doc入口并提出按研究问题组织的结构，仅文档|2026-09-30T09:44:30.639270+08:00|[记录](agent_logs/20260930-forem-doc.md)|
|FOREM-LAYOUT|Codex /root|done|落实FoReM目录与文档结构，统一协作记录入口|2026-09-30T09:47:54.714128+08:00|[记录](agent_logs/20260930-forem-layout.md)|
|FOREM-ENV-CHOICE|Codex /root|done|核对现有环境，确定控制误差仿真技术栈|2026-09-30T09:52:14.984153+08:00|[记录](agent_logs/20260930-env-choice.md)|
|GIT-CLEAN|Claude|done|按用户要求，把当前工作树作为唯一状态一次性提交，使 `git status` 干净；不推送、不删分支|2026-09-30 09:56 +08:00|[记录](agent_logs/20260930-claude-git-clean.md)|
|ENV-HANDOFF-DOC|Codex /root|done|编写Claude执行的环境配置与验收计划，仅文档|2026-09-30T09:56:36.515845+08:00|[记录](agent_logs/20260930-codex-env-handoff.md)|
|DOC-THREE-PARTS|Codex /root|done|每个研究任务统一任务/流程/结果三文档，迁移现有两项|2026-09-30T10:02:54.489087+08:00|[记录](agent_logs/20260930-codex-three-documents.md)|
|DOC-TASK-NUMBERS|Codex /root|done|任务独立目录与递归编号，支持顺序或子Agent执行|2026-09-30T10:11:00.499218+08:00|[记录](agent_logs/20260930-codex-task-numbers.md)|
|TASK0-FIX-HANDOFF|Codex /root|done|编写task0.7修正及重新验收计划，仅文档|2026-09-30T10:54:13.549267+08:00|[记录](agent_logs/20260930-codex-task0-remediation-handoff.md)|
|TASK0-REVIEW (task0.6)|Codex /root|done|审核交付；构建及两次复测通过连通性，但持续高频振荡与验收漏项需修正；task0仍review|2026-09-30T10:44:12.018767+08:00|[记录](agent_logs/20260930-codex-task0-review.md)|
|ENV-SETUP (task0)|Claude|review|按tasks/task0执行：task0.1→0.5全部完成并有实测证据（forem-dev、forem_sim构建、两次独立启动通过）；待核验，含一项已记录的读数异常；不委派子Agent|2026-09-30 10:22 +08:00|[记录](agent_logs/20260930-claude-env-setup.md)|

用户选择原版本 `1ccedd0`。旧路线已取消；实际验证见任务记录。最后更新：2026-09-30T09:27:17.468838+08:00。

当前状态（2026-09-30 10:37，Claude更新）：task0 环境配置已执行完毕并进入 review——`forem-dev` 已创建，`forem_sim` 构建成功，两次独立启动（t0.5-r1/r2）及 60 s 保持（t0.5-x1）通过基本检查；证据见 [task0 RESULTS](tasks/task0/RESULTS.md) 与 [ENV](../ENV.md)。已记录一项未解释的读数异常（effort/velocity 单样本符号翻转）。task1（正常跟踪测量）尚未开始，也未接入任何延迟/扰动/IK/SAC/WM。原版源码核验见agent_logs/20260930-reset-verification.json。

最新审核（Codex，2026-09-30）：task0暂不标done。task0.6-r1/r2确认连通性；高频诊断证实约1kHz真实关节状态振荡，非单纯读数偏置。需定位基线振荡、补齐自动验收/进程清理并纠正误差符号，再复核。详见[task0.6 RESULTS](tasks/task0/task0.6/RESULTS.md)。task1尚未实施。

后续计划：task0.7修正与重新验收三文档已交付，拟Claude执行、尚未接手；执行时登记TASK0-REMEDIATION active。Codex本轮仅写交接，没有实施修正；task0保持review。

|TASK0-REMEDIATION (task0.7)|Claude|review|task0.7全部执行并自测：solver quick→world消除1kHz交替（单因素+恢复复现+阴性对照）、验收重写（20项测试）、入口清理/互斥/run-id保护（8项回归PASS）、误差符号与因果更正、修正后两次启动+60s保持+高频复测通过；待Codex复核，task0仍review；不启动task1|2026-09-30 11:08 +08:00|[记录](agent_logs/20260930-claude-task0-remediation.md)|
|CONTAINER-CLEANUP (task0.8)|Codex /root|done|清理确认无用的旧容器，保留forem-dev；运行中的旧任务等待用途确认|2026-09-30T11:01:27.677603+08:00|[记录](agent_logs/20260930-codex-container-cleanup.md)|

当前容器：仅forem-dev运行。用户确认废弃的3个旧容器已删，镜像/宿主数据保留；清理完成不能代替task0.7修正验收。

最新（Claude，2026-09-30 11:53）：task0.7 已执行并置 review，证据与问题—修正—证据对应表见 [task0.7 RESULTS](tasks/task0/task0.7/RESULTS.md)；实测入口见 [ENV](../ENV.md)。task0 父节点仍 review，等 Codex 复核；task1 尚未开始。
