# task4.8 — 普通SAC基线与有限性能先导详细流程

> 以下步骤均为将来计划，尚未执行。本轮不得实施；未来收到明确实施授权后登记接手，再按依赖推进。

**递归规则：** 本节点恰有TASK.md、PROCEDURE.md、RESULTS.md；进一步拆分须位于本目录内、继承编号并先建三文档，父流程列依赖顺序、负责人、三文档链接和验收关系。当前无更深子任务、无委派；不另建第四份同职责文档。

**Goal：** 在Gazebo当前反馈与现有地图条件下建立可审计普通SAC基线，规划有限先导和端到端性能验证。
**Architecture：** 继承父共享合同，以本节点交付作为下一节点输入；实际证据只写本RESULTS。
**Tech Stack：** FoReM现有ROS/Gazebo/Husky/SAC及拟议WM接口，不恢复惯性估计。
**Spec：** [本TASK](TASK.md)、[父PROCEDURE](../PROCEDURE.md)、[本RESULTS](RESULTS.md)。

## 输入与输出

依赖：task4.7合同/权限/预算口径。输入：4.7合同、Task3真值入口与旧反馈审计作为线索。输出：基线来源/动作/时间/实际末端核验、有限先导收据、分阶段耗时与预算可行性，不把Task3 smoke结果当本节点新结果。

## 文件职责与顺序步骤

相关文件：`forem/scripts/{task3_env,task3_sac_entry,task0_proc}.py 与 forem/scripts/run_task3_core.sh`（shell入口实际为`run_task3_core.sh`）；`forem/src/forem_husky/launch/husky_core.launch`；物理记录/评估参考`record_task4_quality.py`、`evaluate_task4_baseline.py`，但不得复用其中VIO权限假设。

- [ ] 未来接手先检查实施授权/先导预算、进程/容器/锁/他人占用；旧配置enabled=false不在本轮修改，也不直接重启旧runner。
- [ ] 按4.7合同使用Gazebo当前base、现有local map和原SAC；记录实际代码/镜像/配置，不加载旧VIO或prior权重冒充新baseline。
- [ ] 同时标记q_plan、控制器即时参考、q_actual、TF/FK末端、独立物理末端及对应stamp。检查frame/单位/实际目标，发送指令不回填actual；继承的平面投影限制公开。
- [ ] 核验名义dt、实际sim动作区间、观测age及GPU计算wall时间。先测再判断是否有共同调度修复需求，不直接改.02s/solver/噪声/perception_style。
- [ ] 在已登记有限范围内规划动作→真实反馈→replay→普通update→save/load回归；完整训练状态/RNG/计数和源码身份检查独立于“任务是否成功”。
- [ ] 分段计时reset、环境/IK、采样/H2D、GPU推理/update、日志/保存；包含周期性开销计算有效吞吐，不用纯网络benchmark或旧VIO吞吐承诺72h。
- [ ] 对有依据的多线程/GPU数据路径方案规划前后同输入/同语义验证；如需多进程环境，先列隔离与预算需求，不直接三开共享ROS/锁/账本。现有CPU/GPU分工与新优化收益分开报告。
- [ ] 用有效预算和实测成本估算后续WM/对照可行性，交4.9数据接口与先导原证据。不能靠降低基线成功率、删失败、缩动作时间或延长总预算达标。

## 验收、异常和记录

验收：真实反馈与规划值可区分，有限基线链无未解释接口错误，物理成功判据可复算，性能成本口径完整。全零成功或残差失配不能叫基线可用；先记录原因，不把测量修复交给世界模型“自动吸收”。性能不足时报告差距，不扩大预算/功能。

实际执行后在本RESULTS追加run-id、源码/配置/模型/数据hash、命令/退出码、指标与失败、剩余风险/下一步；原日志和产物分别放forem/logs/task4/<run-id>与forem/results/task4/<run-id>，Agent日志放forem/doc/agent_logs/task4/task4.8/。不把计划CLI/测试写成已执行。未满足前置不自动启动下一节点。

## 负责人、模型与来源

当前文档Codex /root；未来实施拟Claude，阶段独立核验拟Codex，均未接手/派发。推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**；普通文档low/平台默认，跨模块机制/状态/时间/概率/验收核对medium。当前Codex实际模型/强度未知；未来执行方须另记实际配置，不能把推荐写成已执行。

依据：[最新文档范围](../../../SOURCES.md#src-0178) · [机制](../../../SOURCES.md#src-0171) · [连续策略/数据因果](../../../SOURCES.md#src-0179) · [验收流程](../../../SOURCES.md#src-0180)。


**性能共同约定：** 后续实施必须同时遵循[根AGENTS性能优化要求](../../../../../AGENTS.md#performance-optimization)，不只停留在建议；本轮文档不触发profile或实现。依据[SRC0181](../../../SOURCES.md#src-0181)。
