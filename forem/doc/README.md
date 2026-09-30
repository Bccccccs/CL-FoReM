# FoReM 文档入口

共同约定：[根AGENTS.md](../../AGENTS.md)。Claude已完成初次环境搭建；Codex独立审核后仍为review，下一步见task0.7修正计划。

## 总览与协作

- [总体计划](PLAN.md)
- [唯一活动进度表](PROGRESS.md)
- [决策记录](DECISIONS.md)
- [Agent日志模板](agent_logs/TEMPLATE.md)

## 任务节点

|节点|任务：目标与路线|流程：详细控制与执行|结果：实测与结论|
|---|---|---|---|
|task0环境配置|[TASK](tasks/task0/TASK.md)|[PROCEDURE](tasks/task0/PROCEDURE.md)|[RESULTS](tasks/task0/RESULTS.md)|
|task1正常跟踪|[TASK](tasks/task1/TASK.md)|[PROCEDURE](tasks/task1/PROCEDURE.md)|[RESULTS](tasks/task1/RESULTS.md)|

整个项目统一采用一任务一目录、递归编号和三文档；所有进一步拆出的子任务也一样。父流程串联子节点顺序、依赖和验收，父结果汇总子结果。环境初次搭建为task0.1–task0.5，task0.6为独立审核、task0.7为修正与重新验收，每个子节点都有独立三文档，入口见父流程。

计划与实测分开，未执行结果明确标注；同节点多次运行按run-id追加RESULTS。运行原始数据和日志不放doc，Agent过程日志单独在agent_logs。根doc仅保留兼容链接，不维护第二份活动状态。

编号与委派要求见根AGENTS；主任务目录为tasks/task0、tasks/task1。task1当前仅有计划草案，不在本轮环境实施范围。

当前执行交接：[task0.7 TASK](tasks/task0/task0.7/TASK.md)、[PROCEDURE](tasks/task0/task0.7/PROCEDURE.md)、[RESULTS](tasks/task0/task0.7/RESULTS.md)。修正尚未执行；task1仍是计划草案。
