# task4.10 — 冻结世界模型的执行前反馈详细流程

> 以下步骤均为将来计划，尚未执行。本轮不得实施；未来收到明确实施授权后登记接手，再按依赖推进。

**递归规则：** 本节点恰有TASK.md、PROCEDURE.md、RESULTS.md；进一步拆分须位于本目录内、继承编号并先建三文档，父流程列依赖顺序、负责人、三文档链接和验收关系。当前无更深子任务、无委派；不另建第四份同职责文档。

**Goal：** 使世界模型在执行前影响策略表征，最终仍由连续SAC输出动作，并保持采样/logprob/更新一致。
**Architecture：** 继承父共享合同，以本节点交付作为下一节点输入；实际证据只写本RESULTS。
**Tech Stack：** FoReM现有ROS/Gazebo/Husky/SAC及拟议WM接口，不恢复惯性估计。
**Spec：** [本TASK](TASK.md)、[父PROCEDURE](../PROCEDURE.md)、[本RESULTS](RESULTS.md)。

## 输入与输出

依赖：task4.9预测接口/数据质量核验。输入：4.7动作/概率合同、4.8基线、4.9固定模型/encoder。输出：反馈policy接口、参数更新边界和因果/概率回归、额外计算测量；不是任务收益结果。

## 文件职责与顺序步骤

核查接入位置：`forem/src/modulation_rl/scripts/sac.py:SAC.select_action/update_parameters`、`model.py:GaussianPolicy.forward/predict/sample`与actor头、target动作/alpha路径。未来反馈模块实现`distribution(o)`并暴露候选/预测/修正诊断，环境只接收最终`act`结果。

- [ ] 确定候选为当前未修正actor的确定性动作，避免额外随机候选引入未处理的混合分布；原scale/squash先经公共合同检查。
- [ ] 计算固定参考z、F(z,a0)及预测变化，再经修正模块得到h_refined；只用当前已可得信息，delta不是实际误差目标。
- [ ] 最终actor头给连续分布，训练仅最终采样一次，eval按同分布定义决定动作；只把最终动作送原IK/控制链。
- [ ] 同时接入在线act、actor loss、critic target的next-action及alpha/logprob，不能只改select_action。critic仍使用真实最终动作/next transition，没有想象样本。
- [ ] 冻结F/E_ref权重与归一化，允许actor所需导数经过F输入/候选路径；actor训练不整体no_grad。核验F无参数变化与actor/修正模块梯度正确。若采用截断梯度，必须另明示论证，不能把它说成完整SAC链式梯度。
- [ ] 写因果/概率反例：候选被误执行、future进入当步、错误logprob/双squash、target漏反馈、模型被optimizer改动、跨encoder版本应被发现。
- [ ] 关闭反馈走严格baseline旁路：同参数/同RNG动作及logprob一致，不额外消耗采样；这是必要接口回归，不自动增加正式off实验组。
- [ ] 在已授权有限先导内核验实际最终指令与replay记录一致、额外延迟/动作时间无混淆，交4.11。模型无效输出必须显式记失效，不静默回退后当反馈组成功。

## 验收、异常和记录

验收：候选未执行、最终动作由SAC、模型固定、policy全部训练/推理路径一致、数值/梯度与off旁路通过。动作改变只能证明反馈被使用，不能证明任务改善。

实际执行后在本RESULTS追加run-id、源码/配置/模型/数据hash、命令/退出码、指标与失败、剩余风险/下一步；原日志和产物分别放forem/logs/task4/<run-id>与forem/results/task4/<run-id>，Agent日志放forem/doc/agent_logs/task4/task4.10/。不把计划CLI/测试写成已执行。未满足前置不自动启动下一节点。

## 负责人、模型与来源

当前文档Codex /root；未来实施拟Claude，阶段独立核验拟Codex，均未接手/派发。推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**；普通文档low/平台默认，跨模块机制/状态/时间/概率/验收核对medium。当前Codex实际模型/强度未知；未来执行方须另记实际配置，不能把推荐写成已执行。

依据：[最新文档范围](../../../SOURCES.md#src-0178) · [机制](../../../SOURCES.md#src-0171) · [连续策略/数据因果](../../../SOURCES.md#src-0179) · [验收流程](../../../SOURCES.md#src-0180)。
