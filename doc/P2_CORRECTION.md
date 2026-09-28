# P2 - 执行前状态修正详细安排

> **模块参考（DOCS-028）**：接口与实现细节；按 D38，P2 与简化 P4 在 Stage1 一起实现，下文“依赖/顺序”已被 [ROADMAP](ROADMAP.md) 取代。

> 执行 Agent：遵守 AGENTS.md 文档交流规则，先在 PROGRESS 登记任务；所有算法开关默认关闭。Stage1 的对比组与判据以 ROADMAP §6 为准（本文 P2-MIN 对应 S3，与简化 P4 合成 S4）。

**目标**：证明前瞻产生的状态修正，在匹配结构和训练条件下提升移动操作表现。

**架构**：P2-MIN 使用 P1a 的固定特征空间与预测器，插入残差修正后由 SAC 决策；P2-SEQ 单独引入 GRU 状态及连续采样。固定先验不是前瞻策略。

**技术栈**：PyTorch、现有 GaussianPolicy/QNetwork、P1 的 wm 模块。

**依据**：[决策](DECISIONS.md)、[P1](P1_WORLD_MODEL.md)、[评测](EVALUATION.md)。

## 文件与接口

- 拟修改：主 `scripts/model.py` 分离特征编码与 actor head；`sac.py`、`main.py`、`eval.py` 增加受控调用与 checkpoint 元数据。
- 拟新增：`wm/correction.py`、`wm/policy_adapter.py`、`wm/sequence_replay.py`（仅 P2-SEQ），以及 `tests/test_wm_correction.py`、`test_wm_sac_gradients.py`、`test_wm_sequence_replay.py`。
- `correct(h, delta) -> corrected_h` 保持特征维度；前瞻和最终策略使用同一 actor head，前瞻采用确定性均值动作，最终动作按训练/评估模式生成。
- 拟配置：`wm_enabled=false`、`wm_variant=one_step`、`wm_correction=false`、`wm_joint_train=false`、`wm_consistency_weight=0`；配置必须写入 checkpoint，版本不兼容时明确报错。

## P2-MIN1：保留基线行为的接口拆分

- [ ] 将 actor 分成 `encode_observation` 和 `distribution_from_features`，保留原 forward 的数值路径及 state_dict 兼容映射。
- [ ] 明确原 actor head 接收的原始特征与 P1 标准化特征之间的变换：在固定统计量下标准化后预测/修正，送入原 head 前逆标准化。零修正必须通过往返变换一致性测试，不能直接把标准化向量喂给旧 head。
- [ ] 新模块关闭时，对同 checkpoint/输入核验确定性动作一致；随机动作比较时恢复相同 RNG。CNN/归一化统计保持 P1a 对应版本。
- [ ] P2-MIN 初期 critic 继续消费原始观测和实际动作，其状态已足以确定 h 和确定性修正，不强制与 actor 内部表示相同。固定编码器策略的对照也必须固定相同部分。
- [ ] 为 critic 使用潜在输入的方案另列消融，不能因“表示必须相同”同时改掉 QNetwork。若 h 存在记忆依赖，按 P2-SEQ 处理。

## P2-MIN2：前瞻与残差修正

每步计算：`h=E(o)`；`a_preview=actor_mean(h)`；`h_next=wm(h,a_preview,dt)`；`delta=h_next-h`；`h_corrected=h+g*psi(h,delta)`；最终动作 `actor(h_corrected)`。所有预览都不调用真实环境 step。

- [ ] psi 首轮使用两层宽度 128 的 MLP，输出维=D，最后一层零初始化，g 固定为 1；不要同时把 g 与 psi 全部置零造成梯度无法启动。
- [ ] delta 在 P1 固定空间内计算，记录其范数；不将 `||delta||` 作为要压到零的损失。
- [ ] 最小版固定 E 和 world model，detach 预览动作/预测信号，actor loss 只训练最终 actor head 与 psi；优化器显式包含 psi。后续允许梯度穿过预览的版本单列实验。
- [ ] critic 更新使用 replay 中实际执行动作；actor 更新重新计算当前候选动作、修正和最终动作，不能复用 no_grad target 分支。
- [ ] 验证 psi 与 actor 有梯度，固定 E/world model/prior 无参数变化，TD target 无反向图；覆盖 B=1 和 B>1 的 log-prob/Q 对齐。
- [ ] 对无修正基线、零初始化修正、训练后修正分别检查前瞻次数和真实 step 次数，确保每次决策只执行一个动作。

## P2-MIN3：训练与诊断

- [ ] 先完成一个短训练与保存/恢复烟测，再按固定预算运行 EVALUATION.md 的结构匹配对照。
- [ ] 正式比较修正关闭/开启两套独立训练；额外对同一个训练后模型做 delta=0、跨样本打乱和修正幅度扫描，仅作为机制诊断。
- [ ] 记录动作变化、修正范数、预览/最终策略 KL、失败类型变化、控制耗时和预测误差；不以“大幅改变动作”当作收益。
- [ ] 若新策略导致预测误差上升，采集训练场景新轨迹、形成新数据版本后再训练预测器；该新版本的所有对照需要匹配数据和预算。
- [ ] 固定世界模型有效后才试联合训练；明确每个 loss 更新哪些参数，重建目标仍固定，使用同结构和同额外训练预算的对照。

## P2-SEQ：历史状态与离策略训练

- [ ] 接入 P1b 前写清 `posterior -> preview -> correction -> executed action -> next posterior` 的时间索引；posterior 接收上一步 corrected state 和实际动作。
- [ ] replay 存原始序列、实际动作、dt、episode/任务边界和终止掩码；不得仅存旧网络算出的潜在状态作为永久标签。
- [ ] 连续窗口先 burn-in 再训练，从当前参数重建历史；窗口开始于回合中段时使用前缀或已声明的有限历史近似，不假装零 hidden 等价于真实历史。
- [ ] 首轮时序版固定世界模型，actor 与 critic 都消费当前重建的历史状态信息；分别重建目标 Q 所需的下一历史状态，terminal/truncated mask 沿用 P0 协议。
- [ ] 在统一参数与随机种子下，验证在线滚动与离线重建得到的 corrected state 一致；episode reset 清空历史，截断边界不串接下一回合。
- [ ] 对照包括相同 GRU/编码器但关闭修正；除修正外训练预算、数据、head 容量匹配。GRU 与最小版单独报告，不能把记忆收益归给 delta。

## 验收与停止规则

- 工程验收：关闭开关的旧 checkpoint 数值兼容，零初始化保持原动作，梯度边界/序列重建/checkpoint 回归通过。
- 研究验收：按 EVALUATION.md 预注册主指标与配对比较；若仅点估计上升、区间跨 0，记为证据不足，不宣称收益成立。
- 在 simpleobstacle 通过后评测 picknplace；未通过 picknplace 不能声称跨任务泛化。
- 若预测准确但修正无收益，先检查 delta 是否含任务相关信息、psi 是否受梯度训练、离线分布是否覆盖当前策略，再决定修订；不通过堆叠 P3/P4 掩盖失败。

## 合理性与审查重点

残差方式限制接口改动，先固定预测器减少训练不稳定因素；同 actor 的两次查询隔离前瞻作用。actor/critic 内部表示不必一模一样，但训练时必须有足够且一致的状态信息，尤其不能忽略记忆依赖。

审查重点：actor/psi 梯度断链、修正永远为零、预览动作误执行、未来信息泄漏、目标状态索引错误、关闭修正对照训练条件不匹配。原论文的双专家监督不等价于策略间 KL，一致性正则默认不启用。
