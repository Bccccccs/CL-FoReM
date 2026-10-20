# task0.11 四项修正的最终复核 — 流程

遵循根AGENTS递归规则：一任务一目录、每层TASK/PROCEDURE/RESULTS；继续拆分前登记编号、依赖、负责人、三文档与验收关系。本节点无子任务，依赖task0.10提交review。委派代码复核只读代码/数据、只写forem/doc/agent_logs/task0/task0.11/20260930-codex-task0-fix2-code-review.md，不启动仿真或写共享文档。父Agent先查foreign=[]，重跑39项测试、旧坏输入及窗口阴性对照、入口回归、两个新运动launch和高频窗口验收；生产物理配置未变，复核历史60s保持证据。若4项全部关闭，更新task0.10/task0.7与父task0为done，并明确验收范围及task1尚未实施；失败则review。测试仅清理自建进程，日志/results用task0.11前缀、不覆盖历史。

## 模型与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5 medium：核对进程所有权与数据判据的跨模块因果。实际模型/档位未知。
