# task10.16.1 · 流程

递归规则：每层恰有 TASK、PROCEDURE、RESULTS 三文档；如拆分子任务须先建三文档并由父登记编号、负责人、依赖和验收。本次无子任务。执行者可按难度选模型与强度，并按根 AGENTS 先建档后决定是否委派，共享父范围和预算；本次独立完成。推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需审查变时长目标、梯度及温度的一致性。

读取 task10.15 结果与实际 learning.py、sac_discrete.py；检查每决策软值、相对熵、按时长熵与任务Q替代方向；写明Bellman、actor、温度的完整条件与不可辨识数据，列反例及待执行验收。输出供父核验，不编辑生产代码或执行更新、采集、GPU操作。
