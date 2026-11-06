# task12.1 结果与交接

状态：review，2026-11-03 只读复审完成，交父审核；**task12 A 未证明通过**，B/C 不可据此放行。本节点未运行测试、真实环境或GPU、未修改task10。首次停止门原证据见 [SRC-T12-004](../../../SOURCES.md#src-t12-004)；本次新增源码定位由父登记来源后补链。执行者 Codex，实际模型/强度未知；推荐 GPT6.1sol/high、Sonnet5.5/high，因需跨层核对教师与执行语义。

|要求|已核查原件及限制|结论|
|---|---|---|
|真实B3身份/加载|task10 `forem/src/task10/lower.py` 的 `FrozenB3` 校验固定actor及配置；`tests/test_lower.py::test_real_actor_matches_original_sac_and_freezes` 使用3组合成观测，与原SAC同设备对照，不进行环境步进；task10.1结果自报该测试通过|仅是加载和推理证据，不是联合教师验收|
|真实B3、真实机器人几何，同完全已知场景和子目标逐尝试对照|`tests/test_environment.py::fixture_core` 使用 `KinematicsFixture`、空capsules；`policy` 固定脚本动作。`test_known_collision_prediction_matches_real_continuation_and_attempt_clock` 比较最终feature、失败计数和时间，不记录逐步动作/状态；task10真实训练及当前评估未见此配对原件|缺直接证据|
|部分观测隔离|同文件 `test_partial_observation_prediction_can_disagree_with_truth_without_leak` 仅在上述脚本和简化几何夹具下对照；`environment.py::predict_candidates` 静态使用复制的局部grid及 `LocalCollision`，无renderer|夹具及源码支持意图，真实B3与真实几何下隔离尚未直接验收|
|原状态/RNG不变|同文件 `test_prediction_isolates_state_counters_grid_queue_rng_and_invalid_slots` 检查部分原状态、grid、计数和Python/NumPy/Torch CPU RNG，仍是脚本夹具；NumPy只比state数组，未覆盖完整状态、CUDA及实际环境私有流|联合原件缺失，不能外推完整不变|

核查的 task10 工作树 `/home/ybc/projects/CL-FoReM-task10` HEAD `91f538cf2ee10bebffd6b643d5c908fa0d419ced`；该树有未提交改动且 task10.14 正在运行，本结论只覆盖2026-11-03 15:12前所读原件，不将进行中评估视为已通过。本次只读命令与范围见 [独立日志](../../../agent_logs/task12/task12.1/20261103-codex-teacher-review.md)。

**最小补验建议，尚未执行：** 等当前GPU任务结束并取得固定可审计代码版本；以一份固定决策快照、同一子目标、冻结B3和真实机器人运动学/碰撞几何构造完全已知且两侧碰撞表达一致的配对，从同一起点分别运行推演与执行，记录并逐尝试比较观测、原始动作、尝试/提交、base/q/路线进度、失败类别、首次失败尝试时钟和终态及限制，保存配置、哈希、完整轨迹与比较结果。若所选状态未触发失败，则不能声称失败路径已由该轨迹覆盖，应保留缺口。用同一观测快照仅改变未观测真值作隔离检查，并在预测前后比较原状态、route、grid、queue、计数、时间戳及Python/NumPy/Torch CPU、适用CUDA和环境私有RNG的完整状态；记录精确比较方式和未覆盖项。任何不一致均交差异、停A。

这些检查是否能在既有1状态及600秒共享总限额内完成尚无实测，不能作工期承诺；不增加状态或预算，遇限额/超时保留原件并停A。完成后父审核原始证据、固定版本与已消费预算，决定是否放行；本节点不执行采集。

**下一执行轮的具体入口（设计，尚未实现）：** 使用固定 task10 `task10.lower.FrozenB3`，从一份带真实 `Core`/机器人几何与局部grid的决策快照构造同一 `CandidateBatch`，一侧调用 `task10.environment.predict_candidates`，另一侧调用与 `Task10Env.step` 相同的 `episodes.begin` → `policy(core.current_observation())` → `_first_failure_step(core, lambda: episodes.step(raw))` 迭代。先确认执行侧碰撞后端与预测侧 `LocalCollision(grid)` 对选定场景完全一致，且执行侧扫描不会使后续观测改变；否则先明确控制条件，不能将差异归为教师错误。给actor调用加只读包装以保存每步输入和raw；给 `PredictionCore.step` 及执行侧每次step加取证包装，深拷贝前后状态、计数、首次失败和终态，保留每次新增 `Core.attempts` 与 `Core.trace`。一个 `Core.step` 可有两个0.05秒尝试，不能把一次actor调用当一次尝试；逐尝试状态需按 `attempts.active/committed` 与提交 `trace` 顺序关联，失败继承前态，核对条数；若无法无歧义关联则补充只读记录钩子并固定其差异，不得伪造逐尝试状态。记录应保留原始tensor与对照报告、版本/actor和场景哈希，以及不一致字段；额外持久化开销计入同一限额。

补验调用不授予新增预算：沿父协议所有A/B/C共用的1状态、每扇区至多3移动候选、至多10更新及总墙钟600秒；单次A补验所耗时间和状态计入共同账本，B/C仅使用剩余预算，实际耗尽即停止，不用子阶段重新计时。隔离对照仅改变该同一决策快照未观测真值，不增加第二采样状态；如果协议解释或状态计数仍不明确，由父审核确定，不能私自增加预算。
