# task0.13 采集器修正独立复核 — 流程

遵循根AGENTS递归规则：一任务一目录，每层TASK/PROCEDURE/RESULTS；若拆分先建立子三文档，登记编号、负责人、依赖及验收链接。本节点不拆分，依赖task0.12提交review。子Agent只读采集器监督/退出码和回归代码、只写agent_logs/task0/task0.13/20260930-codex-collector-code-review.md，不启动Docker/仿真。父Agent核查完整docker top，重跑宿主/容器45tests，4项采集器回归、9项入口回归、新fresh启动与高频窗口验收，核查旧60s保持源文件身份及原始数据。每轮结束完整进程清单必须无本次采集器/监督/ROS/Gazebo，不能仅用foreign=[]。历史数据不覆盖，新run-id task0.13前缀。共享文档写前重读并保留文档整理任务的其他改动。通过才标done，否则review；不进入task1。

## 模型与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5 medium：容器中断、采集器生命周期与退出码需跨模块核查；实际模型/档位未知。
