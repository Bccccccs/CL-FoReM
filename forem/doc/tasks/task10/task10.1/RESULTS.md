# task10.1 结果

2026-11-02 15:18 +08，负责人 Codex `b3_contract`，状态 **review**（子任务验证完成，待父复跑与全局来源登记）。实际模型 gpt-6.1-sol/medium；推荐 GPT6.1sol/medium、Sonnet5.5/medium，理由为跨模块接口核对。授权边界见 [TASK](TASK.md)；未训练、未配对、未采集真实决策、未提交。

## 实现与核验

- [lower.py](../../../../src/task10/lower.py)：`FrozenB3(device='cpu', artifact_root=原始forem根, source_root=None, inventory_path=None)`；容器用 `artifact_root='/reference'`，自动查 `/reference/source` 与 `/reference/inventory/parameter-inventory.json`。`__call__(obs)` / `select_action(obs, deterministic=True)` 输出原始 `[u, omega, v]`。提供 `.actor`、`.config`、`.actor_path`、`.actor_sha256`、`.hash_report`、`.versions`、`.synchronous=True`；无 optimizer / critic。
- 加载前核对 inventory 自身 SHA256 `4544b053846641106795792cccf458d1462efe8916246575666d899d235ad7bf`、69 个 source_sha256、三种子 actor/config 六项及地图/transfer/evaluation-seeds 三项，共 9 项产物。全部通过；另复查当前执行树中清单列出的 src/config/scripts，避免同权重配不同预处理。config 及 actor 哈希见 [冻结记录](../../../agent_logs/project/20261102-codex-sac-split.md)。未重算大型 full final.pt；它不是本加载器输入。地图池只核对清单字节，未重新扫描全部场景资产。
- 验证 actor 格式、顶层及 versions 的观测/动作/同步标记、vector_dim=74、step=steps=5000000；float32 有限权重与严格 state_dict。只加载 4718 final.actor.pt。actor 为 eval、requires_grad=False、推理 no_grad；初始化 Actor 消耗的 CPU RNG 在 fork_rng 退出后恢复。
- [test_lower.py](../../../../src/task10/tests/test_lower.py) 在同批 3 个非平凡原始观测上对照原版 `task8_lower.sac.LowerSAC.select_action`。CPU 与 CUDA:0 分别比较同设备网络拼接输入及输出，float32，两个最大绝对误差均 **0**；使用 atol=rtol=0，因为同设备、同网络、同权重、同运算路径应逐元素相同。**未宣称跨 CPU/CUDA 结果完全一致**。
- 格式错误、异步输入、错误 dtype、非有限输入、错误 route_points shape、请求随机路径与 hash 篡改均拒绝。无效设备不隐式回退 CPU。

命令（工作目录 `/home/ybc/projects/CL-FoReM-task10`）：

```bash
sg docker -c 'docker exec -e PYTHONPATH=/workspace/src -e TASK10_ARTIFACT_ROOT=/reference forem-task10-runtime python3 -m pytest -q -s -p no:cacheprovider /workspace/src/task10/tests/test_lower.py'
```

2026-11-02 15:17，退出码 0，**14 passed in 6.21s**，无 warning。独立日志见 [执行记录](../../../agent_logs/task10/task10.1/20261102-codex-contract.md)。仅运行本节点有界确定性测试，未运行可能包含训练或广泛采集的项目全套；父负责 task10 组合测试与训练预算。

## B3 预处理与动作审计

本节为已读本地源码的事实，待父登记下方来源草稿后补正式链接；当前采用依据见 [SRC-T10-001](../../../SOURCES.md#src-t10-001)。

1. `task7_lower.observation.preprocess`：grid 是 `[B,128,128,3]`，通道 observed、height、route；height `round(height/.01).clamp(0,255).uint8` 后再 `float * .01`；其余通道转 uint8 后 float。不是原始高度直接喂网络。测试含 .014/.015/3m，编码后 .01/.02/2.55m。
2. vector 顺序 `q(6), tcp(7), next_tcp(7), route_points(15×3), subgoal(5), synchronous(1), previous_action(3)`，合计 74。Core.observe 已将 q 除以 `[2π,2π,π,2π,2π,2π]`；TCP/next TCP 是 body_mount 系 xyz + xyzw quaternion，future route_points 为该系 xyz；subgoal 是底盘系 dx、dy、sin(dyaw)、cos(dyaw)、inplace。加载器不再次归一化。额外 scan_timestamp 不进入 actor vector，但推演必须保留真实 grid.timestamp。
3. `Actor.predict(eval=True)` 是 `tanh(mean)`；加载器不额外裁剪或缩放。`motion.actions` 接受 raw `[u,omega,v]∈[-1,1]`，同步 `u=.01+.145*(raw0+1)` m/s、`omega=raw1` rad/s、`v=.3*raw2` m/s；最后 inplace 将 omega/v 置零。Core 先映射动作，再两次最多 .05s 子步；不能把 raw 当成 `[v,omega]`，不能将路由进展 u 删掉。
4. `Core.current_observation` 首步用 visible_previous，随后用 queue。Core.step 的 after observation 产生于 queue 更新之前；仅有提交才更新 queue。推演须复制两者，不能简单令 previous_action=当前raw。

## 给父集成的推演交接

未修改共享 Core、旧 DecisionEnv 或 rollout。下列为源审计所得必要适配，尚不代表父已完成：

- 决策边界克隆 state.base/q/s、route、grid.observed/height/timestamp、future_offsets、queue、visible_previous、time/attempt_time、failures、stalls、decisions、attempted_total/committed_total、terminated/truncated/strict_success；从相同段起点 begin，保留 failure_mode=cbl_continue、failure_limit=20、async_time_penalty=0、episode_end_bootstrap 等 B3 合同。局部 collision、allowed 和机器人/IK 几何一致；无 renderer/未来扫描，无真实环境 RNG 修改。
- 旧 `core.rollout` 新建 Core 时为 `execute=False` 且默认 failure_mode=terminal，累积计数从零开始；`Core._finish` 对 execute=False 直接 return，不更新回合失败、停滞、决策、终局。不能原样承接父协议 B。
- `Core.step` 的 first_failure_time 每次失败都覆盖，且以提交子步数计时；父合同要求首次失败的**尝试**时间。不得直接使用现有字段声称符合首次失败。
- 旧 `feature_vector` 槽 7/8 为提交秒数与段上限原值，`CandidateEncoder.normalize` 才做时间除法；父须先用 attempted_segment*.05 替换原时长槽，避免用提交时钟或重复归一化。19维顺序为到达(1)、末因onehot(5)、首次失败比例(1)、时长(1)、段上限(1)、终态相对位姿(3)、进展(1)、位置/CBL/角度误差(3)、风险(3)。
- 旧 DecisionEnv 失败比例分母写死 5、dt 用 committed*.05、失败触发阈值也写死 5，均需在 task10 适配层按实际 Core.failure_limit 与尝试时钟改写。
- 终止前成功须取 Core.strict_success，不能用 arrived 或路线已完成代替。完全已知与部分观测推演/执行夹具留给父集成验证，本节点未运行。

## 全局 SOURCES 条目草稿（由父分配编号登记）

建议 `SRC-T10-003`，类型：项目源码核验 + 小夹具实测；作者/机构：FoReM/Codex；年份版本：2026-11-02，工作树 `CL-FoReM-task10`（基于 lower-sac-baseline-v1，未提交）。主张：冻结69项源码与9项推理依赖全部一致，seed4718 actor格式严格通过；同设备CPU/CUDA float32原版输入/输出误差0；上述预处理、动作与旧推演差异。精确位置：`forem/src/task10/lower.py::{verify_frozen_manifest,validate_payload,FrozenB3}`、`tests/test_lower.py`，原源码 `task7_lower/observation.py::{FIELDS,preprocess}`、`task7_lower/networks.py::Actor.predict`、`task7_sim/motion.py::actions`、`task7_sim/core.py::{observe,current_observation,step,_finish,feature_vector,rollout}`、`task7_sim/decision_env.py`。证据路径：本RESULTS与独立日志；核查人：Codex gpt-6.1-sol/medium；核查日2026-11-02。原始结论：14passed/rc0，最大误差0，无性能或任务成功主张。采用：task10统一用此actor读入；父按本节差异适配推演。限制：合成三观测、同设备对照，未执行训练、场景复评、完整推演/执行一致性，不证明研究收益；SOURCES登记前此草稿不作为全局已登记条目。

父统一登记来源：[SRC-T10-003](../../../SOURCES.md#src-t10-003)。父集成复跑与签收以父RESULTS后续记录为准。

2026-11-02父签收：done（本节点确定性实现/审查交付）；父最终组合120passed/2既有条件skipped/rc0，唯一试训16/0及配对0/4对3/4按[父RESULTS](../RESULTS.md)如实保留。正式门NOT_READY，未将子自报作为总通过。最终证据见[SRC-T10-009](../../../SOURCES.md#src-t10-009)。
