# task8.4 独立规格与代码审查

状态：**done（本次独立审查完成；父任务验收由父协调负责）**。审查者 `t84_review`，实际模型 `gpt-6.1-sol` / high。日期 2026-10-26，run-id `t8-exec-20261026`。推荐 Codex GPT6.1sol / high、Claude Sonnet5.5 / high：需要核对 reset/Core/decision/profile 跨模块状态和信息边界；推荐与实际分开记录。[模型依据 SRC-0989](../../../SOURCES.md#src-0989)

## 目标、授权与结论

本次仅审 task8.4 已冻结实现和原始证据，只写本日志；不改实现、RESULTS、共享文档，不派子 Agent、不训练、不提交。读取根/forem AGENTS、ENV、README、PROGRESS、task8 父与 8.4 三文档及 SRC-0984–0990；核 main 及既有 dirty 状态和活动进程，保留其他工作。父独占共享进度和来源登记。[授权 SRC-0990](../../../SOURCES.md#src-0990)

- **Spec compliance：PASS。** 当前实现符合 [8.4 TASK](../../../tasks/task8/task8.4/TASK.md) 和 [PROCEDURE](../../../tasks/task8/task8.4/PROCEDURE.md) 的本节点合同，未发现阻断 8.5 运行依赖门的问题。
- **Code quality：PASS。** 未发现需修复的正确性、信息边界或科学条件漂移问题。新层复用旧纯组件及状态机，真值访问集中在 sampler/planner/renderer/execution collision；未修改旧 task7 实现。
- 此结论只覆盖 8.4 集成。24 图默认采样/运行、总性能验收由 8.5/8.6 继续处理，不代表 SAC 稳定、WM 有效或真实传感器效果。[范围 SRC-0987](../../../SOURCES.md#src-0987)

本轮具体实现与验证证据由父统一登记 **[SRC-0995](../../../SOURCES.md#src-0995)**（报告写入时待父落账）；本日志提供精确主张、原产物和限制，不能用聊天替代来源台账。

## 亲读范围与逐项核查

已亲读 [review-8.4.diff](../../../../logs/task8/t8-exec-20261026/review-8.4.diff) 全部新增实现与测试；以当前源码为最终依据，特别包含后补的 env observation/action versions。逐个读取新 `episode.py/routes.py/env.py/decision_env.py`、两个环境测试及 `environment.json`；读取继承的旧 `EpisodeSampler`、`TruthPlanner`、`EpisodeEnv`、`DecisionEnv`、`Core.reset/observe/step/rollout` 与下层 observation 编码，核 ghost/scene 适配接线。未重审已验收的 8.2 几何算法。

|合同|独立核查结果|
|---|---|
|所有旧真值入口迁移|新 sampler 只 `load_asset → VoxelScene → PcdTruthPlanner`；goal 用 scene.contains，initial/witness 用 SceneCollision；Core 与每次 reset scan 均消费同 SceneBatch。无 `load_map`/JSON boxes/旧 pool fallback；pool 必填，目录需唯一 manifest/index。|
|随机分布、CBL、见证|原 `RandomStreams/sample_base/sample_goal/CBL_Q/validate_initial_state/validate_goal_witness` 直接继承；map draw、proposal seed、局部 RNG、候选排序/yaw 和 64 分块顺序保持；无重试上限或容易地图替代。|
|规划科学条件|继承原 plan/cells/witness_cells、pyastar 与 original_heights；height 来自 scene，膨胀/成本/连通规则保持；clear 在占据 XY 闭格内按低于最高障碍顶拒绝，保守向下外挤明确记录，不借离地空腔放宽规划。|
|profile 与真实状态|三 profile 显式且与 environment.json 相同；decision 拒 sync_v5。Core 使用同一 GhostRobotGeometry 对象进行 IK/capsules/self/execution collision；state 从实际 base/q 得 FK，成功提交后扫描来自实际状态，未回填目标或失败 IK。|
|部分 reset|旧 Core.reset 保留未选 state/route/Grid/counters/segment 字段；新层仅替换选中 scene、地图 ID、proposal seed 和独立 RNG 流。异图 active 未选行测试逐字段对照，scene 对象身份保持，故其不可变 hash 也保持。无旧 renderer.boxes/collision.boxes 依赖。|
|信息边界与形状|继承 DecisionEnv._boundary，只给候选 Grid crop，只给 rollout Grid snapshot/kin/ghost robot；rollout 构造 LocalCollision，无 scene/sidecar。隐藏 truth 置换而冻结 scan 的候选/f_k/Grid 不变原测试通过。lower 74/75、三通道 Grid、decision 13×19 均保持。|
|结束/域/恢复|step 未加域边界失败；out_of_map 只诊断。sampling deadline/cancel 抛 SamplingIncomplete，不置自然 truncated，不放宽采样。new env/decision load_state_dict 和 __setstate__ 拒绝恢复，旧 actor-only 加载独立。|
|版本与审计|env/decision 含 environment/backend/ghost/profile/旧观察动作版本；decision 保留 geometry hash、code_commit/config_hash 和 lower versions。运行原 JSON 含 PCD/sidecar hash、scene/device/dtype/cache key；源码/配置 hash 见下表原 manifest。|

## 原始运行证据

已读取共享 [budget.json](../../../../logs/task8/t8-exec-20261026/budget.json) 中 8.4 的实际 argv、时间、退出码及原日志，而非只读总结。

- 最终 GPU0 全集合：[`d3f8267465.log`](../../../../logs/task8/t8-exec-20261026/d3f8267465.log)，rc0，**19 passed / pytest 28.98s**，账本 worker 29.804659s；真实 CUDA float32。包含新 random_cubes controlled 短路线的两 decision 变体、隐藏 truth 反例、异图 mask reset、真实越域、base/arm 执行失败及三 profile 原 Core 输出对照。
- 默认 random_cubes 原采样另查 [`cube-default-batch1.json`](../../../../results/task8/t8-exec-20261026/integration/cube-default-batch1.json) 与 [`cube-default-batch2.json`](../../../../results/task8/t8-exec-20261026/integration/cube-default-batch2.json)：batch1 accepted1/proposals2，batch2 accepted2/proposals4；均 cuda:0/float32，每行真实非零 TCP 进度动作提交 2 子步，s≈0.03m、实际 FK、sensor_frames=2、scan_timestamp≈0.1s。PCD SHA `946d9d170652083bc6db02abc38328f9aaeee504dd8d417d0beb61fee73fe087`。原始首次默认采样验收命令 `d1a26f1ef9`，最终集合再次生成现存 JSON；不能把这些 JSON 当两种 decision 默认采样的证据。
- 取消后统计修复：[`1911ef61ff.log`](../../../../logs/task8/t8-exec-20261026/1911ef61ff.log) RED 明确 witness_targets=0；当前代码先记已完成 n/result.branch 与 witness 耗时、后查取消，不接受 episode；[`1e2e3f6967.log`](../../../../logs/task8/t8-exec-20261026/1e2e3f6967.log) GREEN，12 passed/2 GPU skips。最终 GPU19项亦覆盖此用例。
- decision 外 deadline 原 RED [`1a9d03fde5.log`](../../../../logs/task8/t8-exec-20261026/1a9d03fde5.log) 为旧继承 reset 不接受 deadline；现显式 override，过期预算在采样前拒绝。指定 map 的 persistent factory 读取当前 sampling 控制，初次临时 deadline 在 finally 恢复，不把已过期 deadline 捕获进后续 autoreset。
- 早期 [`384338e2d6.log`](../../../../logs/task8/t8-exec-20261026/384338e2d6.log) 为4 passed，只有早期测试版本，不替代最终19项；所有失败历史保留，不把 RED 隐去。

## 独立最小复验

目的与实施者现有测试不同：验证**真实默认 sampler 同 seed 完整重现、other RNG 不动、CBL 关节精确继承、实际 lower 向量维度、同 ghost 对象接线、真正 pickle 反序列化拒绝以及最终源码 hash**。全经父 run_budget，owner `8.4-review`；容器 forem-dev，CPU float64，CUDA_VISIBLE_DEVICES 空，torch/OMP/BLAS 单线程，`python3 -B`、PYTHONDONTWRITEBYTECODE、PYTHONPATH 显式；账本 limit20s/内部 timeout18s。完整 argv 在 budget 中。

1. [`842e099d3b.log`](../../../../logs/task8/t8-exec-20261026/842e099d3b.log)：rc1、3.218529s。审查脚本尝试 pickle 带匿名 factory 的对象，被 Python PicklingError 提前拒绝；属于审查脚本错误，不能宣称触发了 __setstate__。未改产品代码。
2. [`50edcf0dfe.log`](../../../../logs/task8/t8-exec-20261026/50edcf0dfe.log)：改用不含匿名函数的新鲜 PcdEpisodeEnv 做 pickle roundtrip；rc0、3.519062s。真实默认 sampler 两次 base/q/witness/route/seed/stats 逐元素相同，other RNG 不变，CBL q 精确相同；74/74/75 维通过；Core/capsules/collision.robot/env.robot 同对象；pickle.loads 确实触发 restore rejected；[source-hashes.json](../../../../results/task8/t8-exec-20261026/integration/source-hashes.json) 11 个新旧文件 SHA 全部匹配，三 profile 配置与代码完全相同。

独立验证累计 **6.737591s**，无 timeout，在授予35s额度内；最后工具报告全局余额1511.654436s。未重复跑完整 GPU 回归，未占 GPU。

## 限制、交接与剩余事项

未发现代码阻断项；父可据本审查继续复核并明确放行 8.5。初读时实施者 RESULTS 仍为模板；提交本报告后已重读其追加的 `t8-exec-20261026 实施交付` 全节和实施日志，确认15条原命令、119.026474504s累计worker、6次非零退出及0timeout、最终默认cube快照归属和科学限制均已记入主要 RESULTS。父应在 SRC-0995 落账和自身复核后再将任务状态写 done，不能把本日志替代主要 RESULTS。

两种 decision 闭环是 random_cubes 几何上的受控初态/短路线与 scripted policy，分别证明候选→rollout→执行→下一边界及 autoreset 接线；未验证默认随机 decision 任务分布或冻结训练 actor。CPU 同 seed 复现仅声称同 dtype/batch/seed 条件内一致；不声称不同 batch 的 GPU 数值逐位相同。解析地面、ghost 自遮挡忽略、最高高度规划和二维 Grid 的空腔局限仍按新协议保留。下一步为父复核本日志/最终 RESULTS/来源登记，然后由父调度 8.5 运行和 8.6 总验收；无本审查遗留进程。
