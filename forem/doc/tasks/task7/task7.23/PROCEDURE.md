# task7.23 — 审核执行流程

递归规则：每层恰有TASK/PROCEDURE/RESULTS；子任务先建三文档再派发，父结果只汇总已核查的子结果。

|子任务|范围|负责人及实际请求配置|依赖与顺序|三文档|验收关系|
|---|---|---|---|---|---|
|task7.23.1|文档状态与授权边界|Codex audit_1，gpt-6.1-sol / medium|可并行，无共享写入|[TASK](task7.23.1/TASK.md) · [PROCEDURE](task7.23.1/PROCEDURE.md) · [RESULTS](task7.23.1/RESULTS.md)|父Agent交叉核验后汇总|
|task7.23.2|训练结果与故障证据|Codex audit_2，gpt-6.1-sol / medium|可并行，无共享写入|[TASK](task7.23.2/TASK.md) · [PROCEDURE](task7.23.2/PROCEDURE.md) · [RESULTS](task7.23.2/RESULTS.md)|父Agent交叉核验后汇总|
|task7.23.3|代码合同与运行现场|Codex audit_3，gpt-6.1-sol / medium|可并行，无共享写入|[TASK](task7.23.3/TASK.md) · [PROCEDURE](task7.23.3/PROCEDURE.md) · [RESULTS](task7.23.3/RESULTS.md)|父Agent交叉核验后汇总|

父Agent先读取现场并登记→三个只读子任务并行→父Agent复核关键证据→登记SRC-0961–0964并更新当前状态。共享文档仅父Agent写，每次先重读。异常或失联不停止既有运行；无法核验的项目保留review/未核验。

Codex推荐 GPT6.1sol / medium；Claude推荐 Sonnet5.5 / medium。理由：需交叉核对协议、代码、产物与时间线。此次实际子Agent显式请求 gpt-6.1-sol / medium（平台允许名）；不调用Claude。父Agent实际模型/强度未独立核验，记未知。模型路由为沿用用户默认的工程选择，见[SRC-0960](../../../SOURCES.md#src-0960)。
