# FoReM 文档入口

共同约定：[根AGENTS.md](../../AGENTS.md)。当前只完成目录与文档整理，尚未迁移源码、编译或运行仿真。

## 总览与协作

- [总体计划](PLAN.md)：问题、建议研究顺序、当前范围。
- [当前进度](PROGRESS.md)：唯一活动任务表，记录Codex/Claude负责人和状态。
- [决策记录](DECISIONS.md)：已确定的约定及依据，区分候选研究方案。
- [Agent日志模板](agent_logs/TEMPLATE.md)：执行过程、证据与交接。

## 研究问题

- [01 正常执行与跟踪误差](experiments/01-tracking/README.md)：[计划](experiments/01-tracking/PLAN.md)、[报告说明与模板](experiments/01-tracking/reports/README.md)。尚未实施。

每个研究问题的计划、报告与结论放在一起。新问题进入实际讨论或实施时再建目录；不预建所有后续阶段。

报告记录实验配置和实测结果，Agent日志记录工作过程和交接，互相链接而不重复全文。更新计划不能覆盖历史报告；无实测时明确写“尚未执行”。

根doc保留兼容入口，PROGRESS与agent_logs通过链接指向本目录，只有一份活动记录。已有恢复、仓库审计和目录整理记录作为历史保留在agent_logs中。
