# task7.18.5 — 流程

状态：**review**（实际执行与偏差见[RESULTS](RESULTS.md)第一节）。目标见[TASK](TASK.md)。

## 递归规则

本节点恰有TASK.md、PROCEDURE.md、RESULTS.md三份主要文档；如需拆分，子任务放本目录并继承编号，每个子节点同样三文档；父RESULTS汇总子RESULTS，编号稳定不复用。

## 执行步骤

1. 读task7.19 RESULTS（G7/D10工具用法、计时）与d10_protocol.json；核实GPU0/1无compute进程。
2. 小规模试跑估时，再按≤150分钟预算选回合数。
3. 两变体分别评估，汇总G7可行比例、可行候选上下层到达率/失败分类/超时、G7失败率，Wilson区间。
4. 写RESULTS与日志。

## 模型推荐

同[TASK](TASK.md)。
