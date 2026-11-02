# experiment0 PROCEDURE

递归规则：每层恰有TASK/PROCEDURE/RESULTS；如拆experiment0.1等子实验，先建三文档/编号/依赖/模型/输入与验收。本轮不再拆平行协议；project/task9.5子节点承担实现和执行。

顺序：task9.5实际参数归档→独立预审→隔离实现/审查→有界smoke/profile→按截止准入训练→全结果核查→论文基线选择证据。各角色/预算/命令及组别全部引用[执行PROCEDURE](../../tasks/task9/task9.5/PROCEDURE.md)，不新增实验调用或变更任务定义。

对比使用同种子B3-3M及固定终点/末三，语义迁移不调参，200test尚未调用；少种子不宣称普适提升，逐失败/未执行run保留。依据SRC-1340/1342。

Codex GPT6.1sol/high、Claude Sonnet5.5/high推荐，固定执行medium；实际执行见项目日志。
