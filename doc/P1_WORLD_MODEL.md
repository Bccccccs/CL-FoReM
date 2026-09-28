# P1 - 离线世界模型详细安排

> **模块参考（DOCS-028）**：接口与实现细节；执行顺序与出口判据以 [ROADMAP](ROADMAP.md) 为准。

> 2026-09-28最新审计：P1训练/评测窗口漏加时间偏移（D33），旧预测报告仅作受影响历史，不能据此判定P1出口；跨版本测试曝光见D32。修复与内存方案见 [P1_MEMORY_PLAN](P1_MEMORY_PLAN.md)，实验增补见 [RESEARCH_EXPERIMENTS](RESEARCH_EXPERIMENTS.md)。原阶段任务与历史记录保留。

> 2026-09-28工程更新：P1-FIX-028已修复正确窗口并完成有界链路、65测试与三级有限资源验收（D34）。仅每模型8batch及全val工程验证；旧结果仍受D33影响，正式重训/新测试/P1出口尚未验收。见[交接](agent_logs/20260928-p1-fix.md)。

> 2026-09-28正式诊断：P1-RETRAIN-028已完成1000train/300val、seed11完整重训；动作模型一步/五步均优于复制/无动作，配对CI均低于0。仅P1a初步预测证据，独立test与跨seed未验收，不放行P2。见[报告](agent_logs/20260928-p1-retrain-report.md)与D36。

> 执行 Agent：遵守 AGENTS.md 文档交流规则，使用 executing-plans 技能逐任务落实；先登记 P1-A 或 P1-B。阶段产物与收益分别验收。

**目标**：证明机器人状态与局部图包含可学习的动作条件动态，并提供 P2 可消费的稳定预测接口。

**架构**：P1a 固定编码器、确定性一步预测；P1b 再引入 GRU 后验和概率先验。数据来自完整 episode，SAC 原有单步 replay 暂不改成时序 replay。

**技术栈**：现有 PyTorch、LocalDoubleMapCNN、NumPy、分片轨迹数据；node01初始GPU预算8GiB，实际资源证据见P1-FIX-028；旧11GB为来源机器历史。

**依据**：[总体约束](../AGENTS.md)、[决策](DECISIONS.md)、[评测](EVALUATION.md)、[P0](P0/PLAN.md)。

## 文件与接口

拟创建 `src/modulation_rl/scripts/wm/`：`data.py`、`encoder.py`、`dynamics.py`、`losses.py`、`train_offline.py`、`evaluate_prediction.py`，以及 `scripts/collect_rollouts.py`。对应测试放 `scripts/tests/test_wm_data.py`、`test_wm_prediction.py`。

数据协议：每 episode 包含 `observations[0:T+1]`、`actions[0:T]`、reward、terminated、truncated、dt、info、初始种子及 manifest；动作必须是送入 step 的归一化动作，另存物理控制量及变换版本。末帧不可用时标记 invalid_target，不能用下一回合首帧补齐。

P1a 表征 `h_t = E(o_t)`，E 为修复后基线 actor 的 CNN 与机器人状态拼接接口，记录特征维度和编码器 checkpoint 哈希；直接复用该接口可减少 P2 的映射歧义。E 全部固定，机器人状态和地图特征分别使用训练集统计量归一化。

`predict(h_t, a_t, dt) -> h_pred_next`：输出与输入位于同一个固定特征空间；批维为 B，特征维为 D，动作维为 3。固定 analytical dt 仍写入数据；不把可变 Gazebo dt 默认为常数。

P1b 另定义 `posterior(previous_corrected_state, previous_action, observation_feature, dt) -> mean, log_std, hidden`；`prior(state, action, dt) -> mean, log_std`；`decode(state) -> observation_feature`。hidden 和随机潜在状态分开命名，P2 的差值只能在同一潜在坐标系计算。

## P1-A1：轨迹采集与数据校验

- [ ] 使用 P0 固定 rollout 入口采集成功和失败轨迹；记录 policy、环境、地图与数据版本，不改变评测集。
- [ ] 按 EVALUATION.md 的训练/验证/测试种子划分完整 episode；先计算数据规模与磁盘预算，再增加采集量。首轮每组采集量写入 manifest 后固定。
- [ ] 数据 reader 校验 T/T+1、动作边界、dtype/shape、dt>0、NaN/Inf、末帧掩码及 episode 身份；跨回合窗口必须拒绝。
- [ ] 建立同 seed 数据读取复现、分片尾部窗口、极短 episode 和截断末帧测试；训练 shuffle 不改变划分。
- [ ] 若增加随机动作/扰动策略采集，独立标记 policy_id，评估在原分布和新增分布的覆盖度；禁止把测试场景用于补数据。

## P1-A2：最小动作条件预测器

- [ ] 固定 E 与训练集归一化统计，建立复制当前特征和无动作预测器两种基准。
- [ ] 初始模型使用两层宽度 256 的 MLP、ReLU，输入 `[h,a,dt]`，预测特征增量；这是首轮工程配置，不是论文超参数。
- [ ] 训练目标为机器人状态块和地图特征块分别求平均的标准化 MSE，再等权相加；同时报告未标准化误差，避免大维地图块淹没机器人状态。
- [ ] 测试编码器无梯度、输出维度稳定、保存/加载预测一致、输入动作改变可影响输出；“能影响”不能替代留出集上的动作消融收益。
- [ ] 用验证集选择训练时长和 checkpoint，固定选择规则；训练后一次性评测留出集的一步误差。

## P1-A3：多步评测与诊断

- [ ] 评估 1 步和 5 步开放循环预测：首帧编码后递归喂预测特征，使用轨迹中实际动作/dt；中间不注入真实未来特征。明确这是给定动作序列的预测，不是策略闭环 rollout。
- [ ] 比较复制与无动作模型，分别报告状态/地图误差、成功/失败分组、训练/留出布局误差。
- [ ] 计算成对 episode 误差差值置信区间；若动作模型不优于无动作模型，优先检查采样间隔、动作变化范围与物理量对齐，而非直接扩大模型。
- [ ] 可选训练独立地图解码探针，报告 IoU/占据图可视化；不把像素重建或 rviz 作为只预测特征的硬性验收。

**P1a 出口**：数据校验通过，留出集一步误差相对两个对照均有稳定改善，五步误差有限且明确报告；若只有一步有效，可进入仅一步的 P2-MIN，但不得宣称多步预测已通过。

## P1-B：概率时序模型

- [ ] 先对照 SC²-WM 原文建立 posterior/prior/decoder/修正反馈的公式与实现映射，记录 GRU 替代等本项目差异。
- [ ] 首轮 GRU hidden=128、随机潜在维=64，数据窗口为 8 步 burn-in + 16 步训练；不同长度 episode 使用 mask，不能跨 episode。记录并测量显存峰值，再调 batch。
- [ ] posterior 用截至当前的真实观测、上一步实际动作和状态；prior 使用相同时间步的动作预测，KL 对齐同一时刻的后验与先验分布。
- [ ] 使用 `L_rec + beta_KL * L_KL`，beta_KL 首轮从 0 线性升到 1（前 10% 更新）；编码重建目标固定并 detach。记录 log_std 范围、KL、状态方差，避免仅降低 KL 导致潜在状态失效。
- [ ] 离线无修正阶段明确 `previous_corrected_state = previous_state`；P2 时序版再消费实际 corrected state，不能声称 P1 已训练完整闭环分布。
- [ ] 单元验证 KL 有限、重置不泄漏、burn-in 无梯度但建立历史、训练区有梯度、mask 不计损失；对确定性均值预测进行开放循环 1/5 步评测。
- [ ] 对比 P1a，报告新增收益与计算成本；若时序模型无增益，保留 P1a 为主线并记录，不自动阻塞已有效的 P2-MIN。

## 合理性与风险

- 两步安排使表征、预测与时序复杂性可分别定位；固定编码器防止目标随预测器一起坍塌。
- 数据不包含策略未尝试动作的真实反事实，不能把拟合好解释为任意候选动作都可靠。P2 新策略偏离离线分布时，需要单独版本的数据补充和再训练。
- 机器人状态含目标/规划信息，必须保留当前任务条件；遇到目标切换时标记边界，不能把随机新目标当成平滑物理动力学。
- 暂不加入 IK/碰撞预测头；若失败分析支持其价值，再独立设计监督与消融，避免同时改变研究问题。

## 交付与审查重点

交付数据 schema/manifest、固定编码器、预测 checkpoint、1/5 步曲线、复制/无动作对照、显存和耗时记录。重点审查未来信息泄漏、特征坍塌、跨 episode 窗口、动作/dt 错位、时序与非时序状态接口混淆。
