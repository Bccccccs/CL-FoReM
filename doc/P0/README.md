# P0 文档中心

当前状态（2026-09-23 验收，2026-09-28 复核）：analytical 出口在 node01 通过（D24）；Gazebo 出口未通过，对齐工作并入 ROADMAP Stage0 R0-5。总状态以 [PROGRESS](../PROGRESS.md) 为准。

- [完整阶段计划与清单](PLAN.md)（09-22 制定，环境描述为来源机器历史）
- [验收报告](ACCEPTANCE.md)
- [当前执行记录：node01 接手](logs/20260923-p0-node01.md)
- [统一评测协议](../EVALUATION.md)、[决策记录](../DECISIONS.md)、[运行环境](../../ENV.md)
- 已归档：[09-22 剩余问题计划](../archive/20260928-docs028/P0-REMEDIATION_PLAN.md)

**缺失的历史日志**：以下 2026-09-22 来源机器日志正文在迁移到 node01 时丢失，本机与容器内均查无副本（DOCREV-028 复查），结论仅以 ACCEPTANCE 历史节和 `results/` 产物为准：`20260922-p0-closure.md`、`20260922-p0-execution.md`、`20260922-p0-code-review.md`、`20260922-p0-fixes.md`、`20260922-docker-env.md`、`20260922-p0-env-review.md`。

大型日志、checkpoint 和轨迹保留在 Git 忽略的 `results/`；本目录保存计划、执行证据索引与验收结论。
