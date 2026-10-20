# task4.7 — 机制映射与执行合同核对详细流程

> 以下步骤均为将来计划，尚未执行。本轮不得实施；未来收到明确实施授权后登记接手，再按依赖推进。

**递归规则：** 本节点恰有TASK.md、PROCEDURE.md、RESULTS.md；进一步拆分须位于本目录内、继承编号并先建三文档，父流程列依赖顺序、负责人、三文档链接和验收关系。当前无更深子任务、无委派；不另建第四份同职责文档。

**Goal：** 建立后续唯一有效的状态/动作/成功/数据/预算合同，给出SCWM与Husky对应关系。
**Architecture：** 继承父共享合同，以本节点交付作为下一节点输入；实际证据只写本RESULTS。
**Tech Stack：** FoReM现有ROS/Gazebo/Husky/SAC及拟议WM接口，不恢复惯性估计。
**Spec：** [本TASK](TASK.md)、[父PROCEDURE](../PROCEDURE.md)、[本RESULTS](RESULTS.md)。

## 输入与输出

依赖：用户新方向、Task3既有合同。输入：根/forem AGENTS、Task3任务/环境/SAC合同、父TASK/PROCEDURE、SRC0170–0180及旧实现审计。输出：在本RESULTS登记版本化合同、方法映射、字段权限、已授权预算覆盖表、文件职责及尚缺授权项；不另写同职责协议文档。

## 文件职责与顺序步骤

源码只读定位：`forem/scripts/task3_env.py`、`task3_sac_entry.py`；`forem/config/task3/{core_contract,task_contract,sac}.yaml`；`forem/src/modulation_rl/scripts/{sac,model}.py`及`modulation/envs/{robotenv,combined_env,eeplanner}.py`；`src/modulation_rl/src/{robot_env,worlds}.cpp`。SCWM参考`scwm/vlnce_baselines/models/etp/vilmodel_cmt.py`与`ss_trainer_ETP.py`，第三方目录禁止写实现。

- [ ] 读取当前版本/hash，列明policy观测、地图、base、计划/实际关节、末端、reward/done每个字段来源和时间；不要凭名称断言truth/actual。
- [ ] 对照“候选→预测→修正→最终动作”、模型监督与条件适配。列原论文、实际代码、拟Husky接口、未迁移项；不把MLP/连续SAC叫完整原论文复现。
- [ ] 核对现有action order/scale/squash/logprob与predict/sample路径，记录静态疑点及将来反例；未复现的疑点不能当性能根因或直接修改。当前不运行代码测试。
- [ ] 核对实际末端frame、目标定义、时间匹配、IK/slack与跟踪失败分类；登记既有成功门及适用限制，不创建新阈值。
- [ ] 整理预算表：方法/seed/交互/更新、模型数据准备/预训练、验证/测试、条件适配覆盖与来源。保留100万规模/72h一轮约束；共同前缀若采用须列唯一实际成本与每方法成本，不预设10万前缀。缺口只明确缺什么及对哪个阶段构成依赖，不能擅自填额外预算。
- [ ] 确定数据拆分、normalization/encoder版本、checkpoint选择及失败分母；旧已见测试用途明确，不自行指定201–220或增加样本矩阵。
- [ ] 将新模块/入口/配置和测试职责映射到forem合法目录；接口遵循父流程，参数初值要有工程理由与待验证事项，不默认照抄SRC0174。
- [ ] 交付合同表与依赖清单；仅在输入权限、动作/时间/成功语义及拟先导预算清楚后允许未来4.8接手。

## 验收、异常和记录

验收：每项主张能指向来源/版本，未确认值明确非冻结；没有额外功能/组/预算进入执行范围。合同差异会影响比较时，先回父范围说明；预算缺项阻止相应正式运行，不伪装已批准。

实际执行后在本RESULTS追加run-id、源码/配置/模型/数据hash、命令/退出码、指标与失败、剩余风险/下一步；原日志和产物分别放forem/logs/task4/<run-id>与forem/results/task4/<run-id>，Agent日志放forem/doc/agent_logs/task4/task4.7/。不把计划CLI/测试写成已执行。未满足前置不自动启动下一节点。

## 负责人、模型与来源

当前文档Codex /root；未来实施拟Claude，阶段独立核验拟Codex，均未接手/派发。推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**；普通文档low/平台默认，跨模块机制/状态/时间/概率/验收核对medium。当前Codex实际模型/强度未知；未来执行方须另记实际配置，不能把推荐写成已执行。

依据：[最新文档范围](../../../SOURCES.md#src-0178) · [机制](../../../SOURCES.md#src-0171) · [连续策略/数据因果](../../../SOURCES.md#src-0179) · [验收流程](../../../SOURCES.md#src-0180)。
