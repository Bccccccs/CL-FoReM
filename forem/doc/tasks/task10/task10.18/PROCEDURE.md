# task10.18 流程

递归规则：子任务继承编号且各具TASK/PROCEDURE/RESULTS；父登记输入/负责人/模型/独占写入范围/依赖/交付与验收。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，涉及SCWM机制适用性与SAC因果排错；实际模型/强度须登记。执行者可自主选平台模型/强度并先建档委派，Terra/Luna按难度可用；父核原件统一交接。

A并行只读证据：18.1 SCWM原文及官方实现的纠正与训练机制；18.2旧三检查点退化状态/全部12初态的预测、评分和执行原件。父独立审核task10当前学习/模型输入/奖励与已有训练曲线。B交叉归因：区别实现bug、已登记设计、论文平台差异与待验证假设。C确认bug才修对应路径、做一次必要定向回归，不重跑已有效全套测试。涉及新机制列具体研究问题/对照/成本/验收，待用户决定。D写来源、结果、决策和交接；本轮不替换运行快照，不启动扩训。

18.1（SCWM机制对照）由Terra/high独占子文档及独立日志，输出精确原文/代码位置，未运行Habitat。[TASK](task10.18.1/TASK.md) · [PROCEDURE](task10.18.1/PROCEDURE.md) · [RESULTS](task10.18.1/RESULTS.md)。18.2（已保存原件诊断）由Terra/high独占子文档/日志及results/task10/t10-diagnosis-20261106/behavior子目录，禁止修改生产代码/旧原件，零新环境交互。[TASK](task10.18.2/TASK.md) · [PROCEDURE](task10.18.2/PROCEDURE.md) · [RESULTS](task10.18.2/RESULTS.md)。两子任务独立无共享写入；父审核其原始证据并统一登记SOURCES。模型选择为跨论文实现与学习因果核查的工程选择，并非性能主张。

## 18.3 原数据价值诊断

依赖18.2策略熵/低softQ KL读数，由Terra/high独占子三文档/日志、task10_value_probe.py及value-probe结果；父核目标/输入与结论。现有终局SAC Q损失下仅诊断现有头拟合，不改变生产或新研究机制。[TASK](task10.18.3/TASK.md) · [PROCEDURE](task10.18.3/PROCEDURE.md) · [RESULTS](task10.18.3/RESULTS.md)。

## 18.4 最小首步干预

18.3表明旧训练单步终局表征并非无信号，下一步不直接调超参，做同退化图两回合首步干预。18.4独占新诊断入口/日志/产物，父核初态与入口后可启动，0更新、不改生产合同。[TASK](task10.18.4/TASK.md) · [PROCEDURE](task10.18.4/PROCEDURE.md) · [RESULTS](task10.18.4/RESULTS.md)。模型/委派权限沿子流程，实际启动后遵用户退出监督偏好。
