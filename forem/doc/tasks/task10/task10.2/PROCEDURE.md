# task10.2 流程

递归规则：当前无子节点；若拆分须稳定继承编号，每层恰有 TASK、PROCEDURE、RESULTS，登记顺序、依赖、负责人及父验收关系。

1. 先读本节点TASK、父A→B→C合同与根AGENTS；核实代码及实际运行解释器。
2. 先建有区分力的确定性夹具，再在独占文件中实现并复测。
3. 更新RESULTS及日志，向父报告文件、命令、证据、问题，父审查和复跑；禁止将自报完成当父通过。

推荐 GPT6.1sol/high、Sonnet5.5/high；理由：终局折扣及回放边界需严谨因果核对。实际派发 gpt-6.1-sol/high。

## 实际实现接口与验收顺序

依据父 [B/C 合同](../PROCEDURE.md#b--环境时钟与奖励)及 [SRC-T10-001](../../../SOURCES.md#src-t10-001)。

1. runner 在真实执行后、自动复位前调用 `attempt_reward(progress_before, progress_after, total_length, attempted_steps, *, terminated=False, truncated=False, strict_success=False, success_already=False)`。进展与总弧长单位米；尝试数必须为非负整数；Core.begin立即判定无进展inplace时可为零（dt=0、g=1），仍是一条真实决策，提交数不用于计算折扣。返回 `reward/base_reward/shaping/discount/dt/bootstrap_mask`。`truncated` 在本接口指任务内真实限额，采集切块和进程中断不得伪造该标志。
2. 每次真实选择调用 `EpisodeReplay(capacity=100000, seed=101).append(episode_key, row)`；同回合索引从零连续递增。row 保留 `observation/candidates/next_observation/next_candidates/selected/reward/dt/terminated/truncated/bootstrap_mask/decision_index` 及审计字段。`candidates/next_candidates` 的 `mask` 均须为非空布尔向量，selected 必须有效；终局后不得沿用同回合key。复位首帧不替代终局下一边界。
3. 使用 `UpperModel(...).set_stage('1')`、`Stage1Learner(model,total_updates)`；每新增一条真实选择由 runner 调用一次 `update_sequences(learner,replay,decisions,adapter,profile=False)`，其中 adapter 的 `adapter(rows,next_state=...)` 合同兼容 `task7_upper.stages.ReplayAdapter`。预热前不更新；满足1000决策与32真实采样起点后，每次调用只更新一次，无隐式追赶或预算扩增。
4. `sample(batch=32)` 在全部真实决策起点间无放回抽32段。Fragment 含 `episode_key/start/prefix/burn_in/steps`：prefix 是同回合初始历史，burn_in 最多4步，steps 最多8步。先无梯度重建完整prefix/burn-in，再对真实steps求损失；不补齐虚假位置，不丢弃前四个真实决策。容量超过上限时淘汰完整最旧回合，保留回合从初态重建所需历史；单回合超过容量明确报错。本父协议单回合最多150次选择，远小于默认容量；此为合同边界而非吞吐优化结论。
5. `Stage1Learner` 继承 `DiscreteSAC`，复用温度、优化器、学习率调度、裁剪和目标软更新，只在调用时将独立bootstrap_mask映射给其既有Bellman入口。原始terminated/truncated留在row内。完整恢复复用 `task7_upper.stages.save_checkpoint/load_checkpoint`；无环境状态的检查点明确仅恢复学习器，不能声称支持任意环境中途恢复。
6. 先执行本节点确定性测试，再执行旧task7_upper回归；父重跑并核查与真实环境的观察/候选时刻、GPU设备、下层哈希及梯度后，才进入父C的有界冒烟。测试不替代真实闭环或性能验收。
