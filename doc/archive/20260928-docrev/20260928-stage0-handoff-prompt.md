# STAGE0-028 交接提示词（已作废）

> **作废（2026-09-28 15:56）**：计划已并入 ROADMAP、工作区已改名，改用 [20260928-stage0-prompt-v3.md](../../agent_logs/20260928-stage0-prompt-v3.md)（v2 亦已作废）。

以下为交给执行 Agent 的完整提示词（2026-09-28，Claude Opus 5.5 /ybc 生成；用户授权阶段0执行，但要求由其他 Agent 执行）。

---

你接手 Husky 世界模型闭环项目的**阶段0（STAGE0-028）**。工作区 `/home/ybc/projects/mm_husky_ws`，唯一开发代码 `src/modulation_rl`（算法入口 `scripts/`）。本任务只做阶段0的前置验证，**不实现 P2/P4、不训练 SAC、不进入阶段1**。

## 0. 开工前必须做

1. 按顺序完整阅读：`AGENTS.md`（第2节“通过文档交流进度”是硬性规则）、`doc/README.md`、`doc/PROGRESS.md`、`doc/DECISIONS.md`（重点 D32–D39）、`ENV.md`、`doc/EVALUATION.md`、`doc/P1_WORLD_MODEL.md`，以及本任务记录 `doc/agent_logs/20260928-stage0.md`、方案 `doc/agent_logs/20260928-runplan-ijcai.md`、闭环对照 `doc/agent_logs/20260928-scwm-loop-alignment.md`、P1 重训报告 `doc/agent_logs/20260928-p1-retrain-report.md`。
2. 登记接手：在 `doc/PROGRESS.md` 的 STAGE0-028 行填入你的 Agent 名称，状态改为 active；在 `doc/agent_logs/20260928-stage0.md` 追加接手记录（时间、已读文档、核实过的关键状态）。
3. 记录规则：每个子任务开始、完成、失败、改方案、启动长任务时都要更新该日志；持续工作每30分钟至少写一次。写明改动文件、实际命令、容器/PID、退出码、日志与产物路径、未解决问题。计划命令标“尚未执行”，不得把计划或启动成功写成通过。
4. 共享文档写前先重读。`DECISIONS.md` 追加前先查当前最大编号再加一：今天已出现一次 D36 重号，本文中“D40/D41…”只是占位名，以实际编号为准。其他 Agent（如 Codex）可能同时在写文档，保留他人内容。

## 1. 背景与已定决策

- 目标：把 SC²-WM 式闭环引入现有 Husky+UR5+Robotiq85 / N²M² / SAC 系统。投稿暂定 IJCAI 2027（CCF-B，约2027年1月中旬截稿，D37）。最终动作始终由 SAC 输出。
- D38：最小闭环 = P2（世界模型前瞻 Δ → 特征修正 → SAC 出动作）+ 简化 P4（执行后用实际动作和真实下一帧，对世界模型预测器做一步更新，每回合重置）。
- D39：失配来源 = analytical 中注入系统性执行失配（训练随机化 + 受控实验），加上 Gazebo 自然失配（只评测、不训练）。
- 用户约 15:14 批准的 Gazebo 实时方案：控制周期对齐训练的 0.1s，并改为按仿真时间的截止式等待；不改物理步长，不降 IK 预算。
- 时间节点：G0（本任务门槛）目标约 10-03；阶段1筛查 10-04–10-20；约 11-20 为去留点。

## 2. 已核实事实（接手前）

- P1（D36）：seed11、train 0–999 / val 9600–9899，动作模型一步/五步均优于 copy 与 no_action，配对 CI 均<0；相对 no_action 仅好约3.6–4%。单种子，val 参与了早停，没有独立 test。模型在 `results/p1-retrain-20260928/trainval-1000-r1/`，数据协议 `protocol-1000/dataset.json`，特征缓存 `feature-cache/`。
- 数据与编码器策略：`results/p1a-20260923/policy-100k.pt`（SHA-256 前缀 `e341262c`）。100k 验证 20 回合：SR .80、perfect .55，4 个失败**全部为 ik_limit**，碰撞 0。
- `robotenv.py:286–287` 已有 `transition_noise_base`（`modulation/utils.py:114`，默认0），是零均值高斯噪声，无法被预测或适应，**不能作为闭环失配来源**；新失配注入放在同一个 `step` 里。
- `map.py:837` 把障碍间距写死为 `3.0`，`--simpleobstacle_spacing` 实际无效。**本任务不修**，只在日志中保留该发现。
- Gazebo：`src/robot_env.cpp:257–258` 为固定阻塞 `ros::Duration(dt_exec).sleep()`；`--time_step` 在 `modulation/utils.py:106` 默认 0.02，`p0_runner.py` 没有透传；analytical 训练步长 `TIME_STEP_TRAIN=0.1`（`eeplanner.py:22`）。P0 实测每步墙钟 p50 52.8ms、物理 RTF 0.72、C++ step 持有 GIL。此前只跑过 4 个 Gazebo 回合，用的是 2000 步弱策略 `sac-fixed100`，**不能据此判断 Gazebo 可不可用**。
- 吞吐参考：SAC 100k 步约 3.3h；采数 48 进程约 137 回合/分钟；WM 训练 1000 回合约 17 分钟/次（含评测）。本机 64 核、251GB RAM、4×RTX PRO 6000（96GB）。
- `p0_runner.py:40` 的 `read_seeds`：采数只允许种子 0–9999。评测必须带 `--ik-mode fixed --ik-iterations 100`；`--policy-mode stochastic` 只允许与 `--save-observations` 一起用于采数。
- **此前没有执行过任何阶段0实验。**已备好但未运行的 R0-1 runner：`doc/agent_logs/20260928-stage0-r01-runner.py`，由 `20260928-p1-retrain-runner.py` 改写，只改了 seed 和输出路径。使用前先审查。

## 3. 硬约束

- 不改 SAC、奖励、终止、IK 语义。所有新行为必须有开关、默认关闭；关闭时与现有基线**逐元素一致**，需实测验证（同 P0 gate：相同种子 20 回合，所有字段差 0）。环境语义扩展要按 AGENTS 的 P0 规则单独记录版本。
- 不把旧 test 9000–9199、旧 val 8000–8099 当未见测试集；20000–20299 预留给闭环最终测试，不得使用。
- 阈值和判据要在看结果**之前**写入 DECISIONS（预登记），看完结果后不得放宽。
- 资源与进程：docker 命令用 `sg docker -c`；容器按 ENV.md 创建，名称加 `r0` 前缀；启动前检查空闲 GPU、RAM 和已有容器（`mmhusky-node01`、`mmhusky-node01-gz` 已运行5天，先确认有没有人在用）。**不得停止非本任务的容器或进程**。后台 Python 用 `python3 -u`，记录容器名、PID、日志、输出目录和停止方式。
- results 与大文件不入 Git。未经用户要求不 commit；根目录和嵌套仓库都有他人未提交的改动，必须保留，改哪个仓库就检查哪个仓库的 diff。
- 失败或阻塞时如实记录并向用户汇报，不要绕过检查或降低标准。

## 4. 子任务

### R0-1：P1 世界模型补种子 22、33

- 审查并使用 `doc/agent_logs/20260928-stage0-r01-runner.py`（环境变量 `R0_SEED`）。仿照 `doc/agent_logs/20260928-p1-retrain-launch.sh` 写启动脚本：每个种子一个独立容器（`--network none`、`--memory=16g --memory-swap=16g`、各占一张空闲 GPU、镜像 ID `sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`）。启动前在宿主创建 `results/p1-retrain-20260928/diagnostic-s{seed}/`，并确认 `trainval-1000-s{seed}` 不存在。共享特征缓存只读复用，先确认其完成标记。
- 验收：两个种子都退出码 0、资源预算通过；与 seed11 在 val 上的结果一起列表比较。

### R0-2：独立 test 与 P1 出口（在 R0-1 完成后评测）

- 先审计种子 9901–9999：在 `results/` 下全部 manifest、dataset.json、episodes.jsonl 和种子文件，以及 doc 中查找是否用过（9900 是 dataset-v2-10k 的占位回合）。
- 若未用过：先在 DECISIONS 登记“P1 独立 test v1”，内容包括：种子 9901–9999（99 回合）；采集协议与 protocol-1000 相同（policy-100k、stochastic、simpleobstacle、fixed100、max 2000 步）；seed11/22/33 的 action/no_action 最佳模型各评一次；判据按 `P1_WORLD_MODEL.md:54`（一步动作模型相对 copy 与 no_action，配对 episode-bootstrap 95% CI 上界 <0；五步如实报告）；局限写明布局近重复隔离未验证，只做了与 train/val 的精确哈希互斥检查。登记后再采集。采集参考 `dataset-freshtest` 的做法（train/val 放占位），用 `wm/evaluate_prediction.py --split test`，特征缓存用新目录。
- 若已被用过：停止并向用户汇报，由用户决定新的命名空间（这需要带版本地修改 `read_seeds`）。
- 每个模型只评一次，结果无论好坏都报告。

### M：注入执行失配开关（R0-3/R0-4/R0-5 的前提）

- 位置：`scripts/modulation/envs/robotenv.py` 的 `step`。顺序：命令速度（含现有噪声与 `apply_action_exec` 加速度裁剪）→ `_prev_base_actions_scaled` **仍保存命令值** → 施加延迟 → 施加增益 → `_calculate_base_command(执行值)`。只作用于底盘，手臂不变。
- 参数（默认关闭）：`base_vel_gain`（固定值，默认 1.0）；`base_vel_gain_range`（可选，每回合在 [lo,hi] 均匀采样）；`action_delay_steps`（默认 0，底盘命令延迟，队列每回合用 0 初始化）。
- 随机源：用由回合种子派生的独立 RNG，不能消耗环境的 `np_random`。这样同一种子在不同失配配置下，布局和目标完全相同，才能做配对比较。
- 透传：`p0_runner.py` 与 `collect_rollouts.py` 新增 `--base-vel-gain`、`--base-vel-gain-range LO HI`、`--action-delay-steps`。manifest 记录失配配置，非默认时加语义标签（如 `mismatch-v1`）；episodes.jsonl 记录每回合增益、延迟，以及命令与实际执行的底盘速度。
- 测试：单元测试覆盖增益、延迟队列顺序与 reset、默认关闭恒等、RNG 独立性。回归 gate：policy-100k、种子 10000–10019、fixed100、确定性，分别跑“不带参数”和“显式传默认值”，与现基线所有字段差 0。现有 Python/C++ 测试全部通过。
- 在 DECISIONS 记录为版本化的环境语义扩展。

### R0-3：失配敏感性扫描

- 先在 DECISIONS 预登记：policy-100k 确定性评测；种子 10000–10099（EVALUATION 的验证范围）；配置为增益 {0.6,0.8,1.0,1.2,1.4} × 延迟 {0,1,2}，共 15 个配置、各 100 回合；fixed100。
- 判据（预登记）：至少存在一个配置，SR 相对名义条件（1.0, 0）下降 ≥0.15，且配对 bootstrap 95% CI 上界 <0。
- 输出：各配置的 SR、perfect、失败分布、IK 失败步数均值、路径长度；与名义条件的配对差和 CI。据此给出建议：训练用的失配随机化范围（中度掉点）和训练外测试档位（重度掉点）。这些由用户在阶段1前确认。
- 多个 eval 进程可以共用同一个 ROS master（P0 已验证过并发复现），请自行确认并发方式并记录。

### R0-4：闭环后半段的信号检查（离线）

- 数据：`collect_rollouts.py --save-observations`，policy-100k、stochastic、fixed100。种子 9600–9699（protocol-1000 的 val，不是 test）。7 个条件：增益 {0.6,0.8,1.0,1.2,1.4}（延迟 0），加上延迟 {1,2}（增益 1.0），各 100 回合。输出 `results/stage0-20260928/r04-<条件>/`。
- 新脚本 `scripts/wm/residual_probe.py`（附测试）：固定编码器，加 seed11 的 action 模型（R0-1 完成后再加 s22/s33）和 checkpoint 自带的 normalizer；复用现有 FeatureCache/WindowSource，内存有界，不整体加载。
- 协议（预测后更新，严格因果）：每回合内，对每个 t 先用当前模型预测 `WM(z_t, a_t, dt_t)`，记录残差（total、robot 块、map 块，能识别的话单列底盘位姿相关维度），然后在自适应变体里用这一条转移对**预测器参数**做一步更新（每 k 步一次，k∈{1,5}；lr∈{1e-5,1e-4,1e-3}，全部报告）。每回合重置权重和优化器。同时报告 copy 基线。
- 判据（预登记）：
  - 冻结模型的残差随 |增益−1| 和延迟增大，至少最极端档位显著高于名义；
  - 至少一组 (lr,k) 下，失配条件中自适应残差低于冻结残差（回合后半段，配对 CI 上界 <0），名义条件下不显著变差。
- 注意混杂：失配下策略访问的状态分布也会变。要分开报告 robot 块，并说明残差上升里有多少可能来自分布偏移。

### R0-5：Gazebo 对齐与差距检查（工程，限时约1天工作量）

- 实现用户批准的方案，作为新的版本化选项、默认关闭（旧行为保留）：
  - `p0_runner.py` 透传 `--gz-time-step`（映射到 config `time_step`，目标 0.1）；
  - `--gz-deadline-wait`：把 `robot_env.cpp:257–258` 的固定等待改为“从上一次下发命令起，按 ROS/仿真时间睡到 +dt_exec 为止”，并记录实际周期。
  - 在容器内 catkin 重编译，C++ 与 Python 测试回归，并确认 analytical gate 差 0。
  - 回合步数上限要使 Gazebo 的仿真时长与 analytical 可比。
- 容器：先确认 `mmhusky-node01-gz` 是否有人在用；如有，按 ENV.md 另建 `r0` 前缀的 Gazebo 容器。
- 先确认 simpleobstacle 能否在 Gazebo 下运行（`SimpleObstacleTask.requires_simulator()` 为 False，需核实障碍物是否会被生成）。不能的话，analytical 与 Gazebo 两边都改用 picknplace（`modulation_tasks.world`，参考 P0 日志），并记录原因。
- 评测：policy-100k 确定性，种子 10000–10019，analytical 与对齐后的 Gazebo 各 20 回合。报告 SR、失败分布、路径、每步周期 p50/p95/p99、仿真时间。另在 Gazebo 用训练范围种子（如 9700–9719）stochastic `--save-observations` 采数，用 `residual_probe.py` 与 analytical 同种子比较冻结/自适应残差。
- 超过限时仍阻塞时，记录阻塞点并汇报。R0-5 不决定 G0，但阶段2之前必须完成。

## 5. G0 门槛与汇报

| 项 | 通过标准 |
|---|---|
| P1 出口 | R0-2：seed11/22/33 三个种子的一步动作模型都满足相对 copy 与 no_action 的 CI 上界 <0；五步如实报告 |
| 失配有效 | R0-3 预登记判据 |
| 回路有信号 | R0-4 预登记判据 |
| Gazebo（参考） | R0-5 对齐已实现并量化了差距 |

前三项任一不通过：停止，不进入阶段1，向用户汇报原因和备选方案（如改用 dynobstacle 或布局族作失配来源，或调整 WM 目标）。

## 6. 交付

- `doc/agent_logs/20260928-stage0.md`：完整过程、命令、容器/PID、产物路径与 G0 判定表。
- DECISIONS 中本任务的新条目：Gazebo 实时方案、P1 独立 test v1、失配语义版本、R0-3/R0-4 预登记判据（编号以实际为准）。
- PROGRESS：STAGE0-028 状态（全部验证后才能标 done，否则 review/blocked）。
- 代码改动清单与测试结果；未解决问题和下一步建议（包括阶段1训练随机化范围和测试档位的建议值）。
- 最后向用户简要汇报 G0 结论。
