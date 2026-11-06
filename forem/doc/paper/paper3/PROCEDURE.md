# paper3 执行流程

推荐Codex GPT6.1sol、Claude Sonnet5.5；跨证据核对medium，研究设计与新颖性审查high。实际父模型/强度未知。执行者可按难度选模与委派，先建档划分独占范围；所有子任务只读代码、只写指定文档，不执行下载代码、训练、仿真，不提交推送。

递归规则：每层恰有TASK、PROCEDURE、RESULTS；子任务按父编号递归、独立日志，父核原始证据后汇总。

1. paper3.1系统只读核查，与文献初筛并行；完成后约束文献适用性。
2. paper3.2观测/部分可观测文献，paper3.3协调/可达性文献并行，写入无交叉。
3. 父核原文机制/消融，综合方案并主动检索最近邻，维护全局来源与索引。
4. 定向检查链接、阅读深度、授权边界与两个问题覆盖，不运行实验。

|子任务|负责人|输入与独占写入|交付/验收|
|---|---|---|---|
|paper3.1|Codex子Agent|[TASK](paper3.1/TASK.md) / [PROCEDURE](paper3.1/PROCEDURE.md)；本节点与独立日志|[RESULTS](paper3.1/RESULTS.md)，父核证据与适用性|
|paper3.2|Codex子Agent|[TASK](paper3.2/TASK.md) / [PROCEDURE](paper3.2/PROCEDURE.md)；本节点与独立日志|[RESULTS](paper3.2/RESULTS.md)，父核证据与适用性|
|paper3.3|Codex子Agent|[TASK](paper3.3/TASK.md) / [PROCEDURE](paper3.3/PROCEDURE.md)；本节点与独立日志|[RESULTS](paper3.3/RESULTS.md)，父核证据与适用性|

## 实际完成

2026-11-06T11:51:18.109670+08:00：三子任务原始证据已定向核查，父汇总19篇/8核心、三方案及反新颖性检索；本地链接与来源对应检查完成。未触发新实验。所有子任务仅只读/文档交付验收；后续实施须另行授权。
