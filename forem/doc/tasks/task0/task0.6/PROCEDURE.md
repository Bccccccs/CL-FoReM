# task0.6 独立审核 — 流程

遵守根 AGENTS 递归规则：一任务一目录，每层 TASK/PROCEDURE/RESULTS 三份；如继续拆分，先登记子编号、依赖、负责人、三文档与验收关系。

依赖 task0.1–0.5 已交付 review 记录。子Agent只读源码/历史证据，写自己的独立日志 forem/doc/agent_logs/20260930-codex-task0-code-review.md，不运行仿真、不修改共享文档。父Agent登记任务、核查容器无其他仿真、以新 run-id 重建与重复启动，分析 CSV 并核验发现，汇总本 RESULTS 和父 RESULTS/PROGRESS。异常只记录；只清理本次启动的进程。

## 模型与推理强度

推荐 Codex GPT6.1sol、Claude Sonnet5.5，中等（medium）：需要核对启动、反馈、验收逻辑的跨模块因果关系。推荐不等于实际配置；实际模型/强度无法核实时记未知。
