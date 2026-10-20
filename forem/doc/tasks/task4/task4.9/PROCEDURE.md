# task4.9 — 动作条件世界模型详细流程

> 以下步骤均为将来计划，尚未执行。本轮不得实施；未来收到明确实施授权后登记接手，再按依赖推进。

**递归规则：** 本节点恰有TASK.md、PROCEDURE.md、RESULTS.md；进一步拆分须位于本目录内、继承编号并先建三文档，父流程列依赖顺序、负责人、三文档链接和验收关系。当前无更深子任务、无委派；不另建第四份同职责文档。

**Goal：** 预测下一步任务相关表征，证明数据因果、独立验证及动作信息使用可靠。
**Architecture：** 继承父共享合同，以本节点交付作为下一节点输入；实际证据只写本RESULTS。
**Tech Stack：** FoReM现有ROS/Gazebo/Husky/SAC及拟议WM接口，不恢复惯性估计。
**Spec：** [本TASK](TASK.md)、[父PROCEDURE](../PROCEDURE.md)、[本RESULTS](RESULTS.md)。

## 输入与输出

依赖：task4.8基线接口/先导证据。输入：4.7批准的数据/预算覆盖、4.8真实transition接口及来源版本。输出：数据manifest与分割、固定参考encoder/归一化、F_phi模型及checkpoint、训练/验证/恒等/动作信息检查结果；所有实际运行待将来授权。

## 文件职责与顺序步骤

未来文件职责：forem/src下WM模块承担`encode(o)->z`与`predict(z,a)->z_next_hat`；forem/scripts入口做数据检查/训练/验证；配置记录结构与已有预算；不在scwm参考仓库改代码。模块名称在4.7文件清单冻结。

- [ ] 校验transition的run/episode/epoch、观测/命令/next时间及实际执行动作；跨reset/旧epoch/缺失next/未来观测样本拒绝并统计，不拼接两个episode。
- [ ] 将状态信息限制在已批准的policy可得观测；Gazebo当前base许可不等于未来truth或额外物理状态可偷偷进入输入。规划状态监督也不能宣传为纯物理动力学辨识。
- [ ] 按完整episode/运行段划分train/validation，策略评估集隔离；只在训练侧拟合normalization与表征，参考encoder固定版本/哈希。若用基线预训练数据/共同前缀，按4.7计入两方法信息和预算。
- [ ] 先实现最小动作条件下一表征预测，记录网络/超参与工程理由；不自动采用未批准的512层宽/epoch或单独训练时限。模型训练只使用执行后的next监督。
- [ ] 同验证记录同时计算恒等预测误差，分别查看运动/静止段；改变或打乱action保持其他输入可比，检查预测是否实际利用动作，防靠大段静态样本取得虚假低loss。
- [ ] 记录误差分布、数据覆盖、数值有效性及按episode结果；模型选择只看训练/验证，不能用test任务成功选择WM参数。
- [ ] 导出带encoder/normalization/数据/动作合同hash的模型，提供4.10需要的确定性预测接口；变更参考encoder后旧模型拒绝混用。
- [ ] 交付F及预测局限；首轮策略比较中冻结F和参考encoder，在线更新留4.12。

## 验收、异常和记录

验收：无数据/未来泄漏，同表征空间比较，输出有限且匹配动作合同；恒等与动作信息诊断有证据。模型不优于恒等或忽略动作时标尚无可信前瞻信息，不能仅用训练loss宣称通过；不预设任务收益。

实际执行后在本RESULTS追加run-id、源码/配置/模型/数据hash、命令/退出码、指标与失败、剩余风险/下一步；原日志和产物分别放forem/logs/task4/<run-id>与forem/results/task4/<run-id>，Agent日志放forem/doc/agent_logs/task4/task4.9/。不把计划CLI/测试写成已执行。未满足前置不自动启动下一节点。

## 负责人、模型与来源

当前文档Codex /root；未来实施拟Claude，阶段独立核验拟Codex，均未接手/派发。推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**；普通文档low/平台默认，跨模块机制/状态/时间/概率/验收核对medium。当前Codex实际模型/强度未知；未来执行方须另记实际配置，不能把推荐写成已执行。

依据：[最新文档范围](../../../SOURCES.md#src-0178) · [机制](../../../SOURCES.md#src-0171) · [连续策略/数据因果](../../../SOURCES.md#src-0179) · [验收流程](../../../SOURCES.md#src-0180)。
