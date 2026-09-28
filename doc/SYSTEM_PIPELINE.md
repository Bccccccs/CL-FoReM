# Husky/SAC 系统与世界模型闭环接口

> **参考（DOCS-028）**：现有系统背景；执行顺序与实验安排以 [ROADMAP](ROADMAP.md) 为准。

更新：2026-09-28；任务 RESEARCH-028-PIPE；执行 Agent：Codex /root/pipeline。审计主包提交 `2a1348a87b3b5c45f495fafacad526f7eaee7749`。本轮只读代码、配置和既有产物，没有重跑训练、ROS 或仿真。代码行号对应此提交；`scripts/wm/*` 已于 `06c0ee1`（P1-FIX-028）修改，其行号可能偏移。后续实现变动时需更新本文件和[任务日志](agent_logs/20260928-research-pipeline.md)。

用户最新明确范围：只向 Husky 引入世界模型闭环，排除 TopAY、NMoMA。机器人为 Husky + UR5 + Robotiq85；最终动作仍由 SAC 产生。本文中的方法接口是研究设计，不代表已实现或已经取得收益。

用户同时明确“现有可以沿用的就继续用”：沿用当前 planner、SAC、BioIK、控制器、日志/评测入口，只补研究所需缺口（执行顺序见 ROADMAP）。下述缓存时序、接口与日志覆盖范围是待核查的语义事实，不据此自动认定缺陷或顺带改算法。

## 1. 当前系统是什么

现有主线是 **任务/末端路径规划 + SAC 移动操作决策 + BioIK + 执行反馈**，不是“先生成 K 条全身轨迹，再按 TotalDuration 选一条”的系统。当前状态观测进入 SAC，SAC 每次产生一个归一化动作，环境执行一步，下一观测重新进入 SAC。已有反馈控制不意味着已经有世界模型反馈。

当前正式入口是 [main.py](../src/modulation_rl/scripts/main.py#L1) / [eval.py](../src/modulation_rl/scripts/eval.py#L1) → [p0_runner.py](../src/modulation_rl/scripts/p0_runner.py#L307)。runner 固定构建 `husky_ur5`，默认任务 `simpleobstacle`、默认 analytical `sim`、默认普通 SAC。IK 固定预算必须显式传入 `--ik-mode fixed --ik-iterations 100`；源码默认仍为 `legacy`，不能把默认值与正式实验协议混同。新入口从仓库自己的 [sac.py](../src/modulation_rl/scripts/sac.py#L67) 和 [model.py](../src/modulation_rl/scripts/model.py#L83) 调用策略；原始 [readme.md](../src/modulation_rl/readme.md) 的 Melodic/Python 3.7/Ray 命令属于来源项目历史，当前环境按 [ENV.md](../ENV.md)。

```text
任务、目标、地图、机器人初始状态
  → 任务包装器设定末端目标和 EE planner
  → 末端路径/下一参考位姿 + 当前机器人状态 + 局部占据图
  → SAC：地图 CNN → 与状态拼接 → actor head → 一个动作 a_t
  → 动作映射：末端参考速度 + Husky 转向/前进速度
  → EE planner 推进参考位姿
  → 预测下一底盘位姿处求 BioIK → UR5 关节目标
  → analytical 状态更新，或 Gazebo 发送底盘/手臂命令并等待
  → 读取更新状态、局部图、碰撞/IK结果
  → 构造 o_(t+1)、reward、done、info
  → 下一次 SAC 决策
```

### 模块存在性与适用边界

| 用户关心的模块 | 本次核实的事实 | 不能据此宣称 |
|---|---|---|
| Global / topological planning | 当前 simpleobstacle 使用 `PointToPointPlanner`：地图代价上的 2D A*，再插值高度与姿态；[tasks.py:329](../src/modulation_rl/scripts/modulation/envs/tasks.py#L329)、[eeplanner.py:590](../src/modulation_rl/scripts/modulation/envs/eeplanner.py#L590) | 不是已验证的多拓扑候选轨迹系统；本轮未审计仓库所有独立规划入口 |
| EE reference planning | 明确存在，`generate_obs_step` 每步重算后续参考；A* 从上一计划末端位置 `_prev_plan` 起步，[eeplanner.py:617](../src/modulation_rl/scripts/modulation/envs/eeplanner.py#L617) | 不等于每步从实际末端状态重新锚定整条全身轨迹 |
| Trajectory optimizer | 当前 SAC 活跃链中查到 BioIK 单步位姿优化、路径插值；独立文件还存在 articulated/OCS2 和 BiRRT 基线入口，以及机器人包 CHOMP 配置 | 不应因其他文件存在就认定主线调用了 MPC/CHOMP；也不应写成“仓库没有 optimizer” |
| Candidate scoring / selection | 当前 runner 的执行循环直接调用一次 `select_action` 后 `step`，[p0_runner.py:133](../src/modulation_rl/scripts/p0_runner.py#L133)；未发现该链有 K 候选轨迹 ranking 或 TotalDuration selection 调用 | SAC 的 Q 值是训练价值估计，不是当前线上候选轨迹打分器 |
| Controller | Husky 底盘发 `/cmd_vel`；UR5 发 FollowJointTrajectory；UR5 配置为带 PID gains 的 effort trajectory controller，[robot_env.cpp:288](../src/modulation_rl/src/robot_env.cpp#L288)、[robot_husky.cpp:91](../src/modulation_rl/src/robot_husky.cpp#L91)、[ur5_controllers.yaml:5](../src/husky_ur5/config/ur5_controllers.yaml#L5) | 本轮未在线探测控制器频率、参数加载值或低层执行稳定性 |
| Logging / evaluation | 当前 runner 保存逐回合、末 50 步、轨迹、控制耗时、manifest；[p0_runner.py:101](../src/modulation_rl/scripts/p0_runner.py#L101) | 记录了执行结果不等于世界模型已利用这些结果改变在线决策 |

独立规划代码仅作存在性说明：[evaluation_articulated.py](../src/modulation_rl/scripts/evaluation_articulated.py#L72)、[evaluation_bi2rrt.py](../src/modulation_rl/scripts/evaluation_bi2rrt.py#L27)、[chomp_planning.yaml](../src/husky_ur5/config/chomp_planning.yaml)。其依赖、Husky 兼容性与当前可运行性未在本任务验证，也不纳入新的平台研究路线。

## 2. 一步内的真实时间顺序

| 顺序 | 调用与数据 | 对闭环研究的含义 |
|---|---|---|
| 1 | runner 持有 `state=o_t`，`SAC.select_action` 调用 `policy.predict`；训练随机采样，正式评估默认确定性均值动作 | 决策使用截至当前的观测；不能接入未来日志字段 |
| 2 | [CombinedEnv.step:356](../src/modulation_rl/scripts/modulation/envs/combined_env.py#L356) 转换动作，并令 EE planner 按 `vel_norm` 推进一步 | SAC 不直接输出 6 个 UR5 关节目标 |
| 3 | [RobotEnv.step:264](../src/modulation_rl/scripts/modulation/envs/robotenv.py#L264) 映射底盘物理速度、执行已有 clip/scaling 逻辑，调用 C++ | P1 保存的归一化动作必须对应这里真正输入的动作；不能悄悄换动作语义 |
| 4 | [robot_env.cpp:191](../src/modulation_rl/src/robot_env.cpp#L191) 先积分出期望下一底盘位姿，再在该底盘位姿下求末端目标的 IK | 已有运动学前视计算，但不是学习世界模型或未来任务结果预测 |
| 5a | analytical：使用积分/IK 后的状态；不通过 Gazebo 物理控制器执行 | 可检验算法机制，不能据此证明克服摩擦、负载、跟踪滞后等物理误差 |
| 5b | Gazebo：发送 arm/base 命令，等待 `dt_exec`，在 `perception_style=all` 下更新实际关节状态与底盘 TF；[robot_env.cpp:239](../src/modulation_rl/src/robot_env.cpp#L239) | 命令下发成功、等待一次与控制目标实际到达是不同事件；耗时不能只算网络推理 |
| 6 | planner 生成下一次观测参考，获取局部图，计算碰撞、IK、reward、done，构造下一观测 | [CombinedEnv.step:367](../src/modulation_rl/scripts/modulation/envs/combined_env.py#L367) 是执行 outcome 与模型目标对齐位置 |
| 7 | 更新 `prev_robot_obs` 和动作缓存；然后 `map.update`，若变化则更新 planner weights | 当前代码先构造 obs，后 `_prev_action.put(action)`；返回 obs 中动作缓存不可未经核对就标成“刚执行的 a_t” |
| 8 | 任务包装器可能切换子目标并重建 planner；runner 保存 transition，再以 next_state 决策 | [tasks_chained.py:79](../src/modulation_rl/scripts/modulation/envs/tasks_chained.py#L79) 的目标切换会引入非平滑特征变化，必须标记边界 |

analytical 的步长在现有数据与 runner 中为 0.1s。Gazebo 的配置 `time_step` 与实际总决策耗时不同；当前入口设 `perception_style=all`、`execute_style=direct`，[p0_runner.py:342](../src/modulation_rl/scripts/p0_runner.py#L342)。EE planner 按 ROS 时间推进并对过大 dt 截断，机器人执行另按 `dt_exec` 等待；因此不能把理想配置周期当成实测控制周期。

现有反馈分三层：SAC 每步重新消费更新状态；EE 参考/地图代价按代码更新；物理控制器执行关节目标并反馈状态。局部仍有计划驱动成分：EE 路径从上一参考起点推进，analytical 假定积分/IK 状态可实现，执行命令在一个控制间隔内保持。应按层描述这些边界，而非给整个系统贴“open-loop”或“closed-loop”单一标签。

## 3. 观测、动作与世界模型接口

以下维度同时得到当前源码常量与 **2026-09-23/24 历史产物** 支持；2026-09-28 只重读产物，没有创建环境重新测量。新配置运行前仍需检查 manifest 的 shape。历史依据：[P1 策略 manifest](../results/p1a-20260923/sac-screen-100k/manifest.json)、[P1 v2 summary](../results/p1a-20260923/wm-v2/summary.json)。产物不入 Git，交接时需保留原路径或补充外部存储位置。

| 接口 | 当前历史配置/源码 | 边界 |
|---|---|---|
| `o_t=(robot_state,local_map)` | `(41,)`、`(120,120,1)`；`concat_prev_action=True`、`concat_plan=False`、`overlay_plan=False` | RGB/语言未接入；更改配置会改变 shape，P1 loader 当前固定维度 |
| 状态语义 | 相对末端位姿、下一参考末端位姿、参考末端速度、局部计划末端相对目标、关节值、目标差、自碰撞与动作缓存；[combined_env.py:401](../src/modulation_rl/scripts/modulation/envs/combined_env.py#L401) | 不等于纯物理状态；含 planner 条件和缓存。局部计划末端通常不是全任务最终目标 |
| `a_t` | `(3,)`，范围 `[-1,1]` | 默认配置依次为 EE 参考速度、底盘角速度、底盘前进速度；不能用旧变量名字推断相反顺序 |
| 物理映射 | EE speed `[0.01,0.3]` m/s；角速度缩放 1.0 rad/s、前进速度缩放 0.3 m/s；[动作映射](../src/modulation_rl/scripts/modulation/envs/combined_env.py#L435)、[底盘映射](../src/modulation_rl/scripts/modulation/envs/robotenv.py#L325)、[robot_config](../src/modulation_rl/gazebo_world/husky_ur5/robot_config.yaml#L15) | 指默认配置的映射，后续 clip/scaling/noise 可能影响执行量；不是三个末端笛卡尔动作 |
| `h_t=E(o_t)` | 固定 actor CNN 的地图特征 1000 维 + robot 41 维 = 1041 维；[encoder.py:12](../src/modulation_rl/scripts/wm/encoder.py#L12) | 接口位于 actor 的 post-FC 之前；不是 GRU 状态或物理状态向量 |
| `z_t=N(h_t)` | 训练集统计标准化；[dynamics.py:13](../src/modulation_rl/scripts/wm/dynamics.py#L13) | actor 原 head 接收原特征；将修正结果送入旧 head 前须逆标准化 |
| `F(z_t,a_t,dt)` | 输出同维下一特征，MLP 预测残差；复制与无动作对照已实现 | 源码已是 residual `z + MLP(...)`；不能将“第一次改成残差预测”作为新贡献 |

状态中的参考速度/参考位姿受 planner 与当前动作共同影响；地图 CNN 特征也未被证明足以编码安全距离或接触风险。1041 维预测误差降低可能主要来自可预测的参考信号，未必改善机器人执行。应分别报告 robot/map/任务相关分量，而不是只看总 MSE。

`E(o)` 未显式包括全部 planner 内部状态、控制器积分状态、传感器延迟和历史；将其称为“充分 Markov 状态”目前证据不足。时序模型若引入历史，应明确历史变量与可用信息，而不能将现有拼接向量改名后声称具有记忆。

## 4. P1 已有内容与尚未存在的闭环

已有采集入口 [collect_rollouts.py](../src/modulation_rl/scripts/collect_rollouts.py#L26) 调用固定预算 P0 rollout，按完整 episode 保存 `T+1` 观测、`T` 动作、reward、dt、done、子目标索引、终止标志。归一化动作由 runner 原样保存。[data.py](../src/modulation_rl/scripts/wm/data.py#L21) 校验 shape、有限值、动作范围和边界；2a1348a 时把所有 episode 地图拼入内存（D29 内存阻塞），已由 P1-FIX-028 改为按回合校验 + 有界特征缓存（`wm/cache.py`，D34）。现有 observations NPZ 没有逐步完整物理命令与全部 info 标签；若训练碰撞/跟踪 outcome 头，必须先补齐对齐的数据协议，不能假设这些标签已经齐备。

已有 P1a 训练/评估模块：固定 encoder、训练集 normalizer、action/no_action/copy 模型、一步与五步给定动作预测。五步评估在首帧后递归喂预测特征、使用记录的真实动作序列，不注入中间真实特征；[dynamics.py:55](../src/modulation_rl/scripts/wm/dynamics.py#L55)、[evaluate_prediction.py:74](../src/modulation_rl/scripts/wm/evaluate_prediction.py#L74)。这是 **开放循环预测评估**，不是在线策略闭环，也不是 MPC。

现有活跃 `SAC.select_action` 没有调用 wm；`model.py` 没有 P2 的 encode/head 拆分或 correction 接口；`wm/` 中尚无 `correction.py`、`policy_adapter.py`、`sequence_replay.py`。P1b GRU、P2 修正、P3 记忆校准、P4 测试时参数更新均未实现，安排见 [ROADMAP](ROADMAP.md)。D28（已归档）曾依据受索引缺陷影响的历史产物记录 P1a 未通过出口，该批数字已作废。当前 P1 仅有单 seed val 初步正结果（D36），P2 待 Stage0 G0 后进入，不能把“模块已写完”标成“研究通过”。

**2026-09-28 审计警示（D33，已由 D34 修复、D36 重训；以下为缺陷原始记录）**：实验子 Agent 已通过独立 CPU probe 确认 [train_offline.py:29](../src/modulation_rl/scripts/wm/train_offline.py#L29) 的 `window_tensors` 取出了窗口时间 `t`，却未将其加进观测/动作偏移；同一回合的不同窗口重复读取回合开头。训练、正式评测和 `val_probe` 共用该函数，因此 D26-D28 数字须保留为受缺陷影响的历史产物，不能继续解释为正常全轨迹预测的正/负结论。P1a 尚无通过出口的可靠证据；先修正索引及内存链路，登记新的曝光/评测协议，再重训重测。本文前述P1模块描述为代码意图和接口，不能理解为当前实现已正确兑现全部窗口语义。详细证据由[实验审计](RESEARCH_EXPERIMENTS.md)维护。

## 5. 在 Husky/SAC 内建立可检验的世界模型闭环

先严格区分三个对象：

1. **预测变化量** `delta_t = F(z_t,a_preview,dt)-z_t`：未来与当前的差，当前时刻可得；不是执行误差。
2. **执行后的预测残差** `e_(t+1)=N(E(o_(t+1)))-F(z_t,a_t,dt_t)`：必须等待实际执行反馈；模型条件是实际执行动作 `a_t`，不能拿预览动作的预测与另一动作的结果比较后声称是模型误差。
3. **决策反馈**：下一次 SAC 决策是否因最新观测、残差或更新后的状态而改变，以及这种变化是否改善 outcome。仅把残差写入日志不构成利用残差的反馈机制。

现有 [P2-MIN 设计](P2_CORRECTION.md) 的最小循环为：

```text
o_t → 固定编码/标准化 z_t
    → 同一 SAC head 给确定性预览动作 a_preview（不执行）
    → WM 一步预测 → delta_t
    → 残差修正 z_corrected → 逆标准化 → 同一 SAC head 给最终 a_t
    → 环境只执行 a_t 一次
    → 实际 o_(t+1) → 下一步重新编码、预测和决策
```

这种设计若每步重新读取实际反馈并重新预测/决策，可以称为“基于反馈的逐步预测修正策略”。它本身不等于“在线更新世界模型”或“根据预测误差校准”；若未消费 `e_t`，论文不能写成已实现误差驱动自适应。每回合只在执行前预测一次并选定条件，随后不再更新模型侧决策，应单列为一次预测对照。单纯让普通 SAC 继续读状态，不能替代验证世界模型侧重复前瞻是否增加了收益。

### 三条同平台研究路径（候选设计，均未实施）

| 路径 | 问题与机制 | 改动/计算代价 | 必需证据与边界 |
|---|---|---|---|
| A：固定一步预测 → 每步特征修正 | 现有 reactive SAC 是否缺少动作条件前视；使用 P2-MIN 的 `delta` 修正，再由 SAC 输出动作 | actor 编码/head 拆分、固定 normalizer/WM、修正网络；每步增加一次 actor head 和 WM 调用 | 与相同 encoder/head/容量/训练预算关闭修正相比；复制/无动作/打乱 delta；每步预测 vs 每回合一次预测。当前受 P1a 出口阻塞，不能仅凭预测均值改善宣称有效 |
| B：任务相关预测目标 → 每步修正 | 总特征预测是否把容量用于无关或已知参考量；仅在失败分析支持时设计 IK/碰撞/跟踪/目标进展的未来目标，并作为 SAC 修正条件 | 补逐步 outcome 标签、定义时间窗/校准指标、训练目标重构；若多步则增加递归误差与耗时 | 与同数据的监督 outcome predictor、仅当前状态风险头、纯反应式修正比较；证明机制带来任务收益，不能把增加一个预测头本身称为创新。仍保留 SAC 最终动作，无候选轨迹替代 |
| C：执行残差 → 因果校准/时序状态 → 下一步修正 | 模型与实际执行不匹配时，显式用截至 t 的 `e_t` 更新状态或限频适应，再预测 | 历史状态/重置/连续数据；若改参数另需 P4 协议和计算预算；不是 A 的自动附属项 | 同结构 w/o feedback、延迟/打乱反馈、冻结/适应对照，扰动前后恢复过程与校准、SR/安全和总耗时；必须区分状态校准与参数更新，严禁用未来误差修正当前动作 |

**当前选择**：ROADMAP 采用路径 A（前瞻修正，S3）+ 路径 C 的参数更新形式（简化 P4 在线更新，S4），失配来源见 D39；路径 B 未进入主线。优先级按“问题—机制—证据”决定，不按实现容易程度决定。路径 A 是现有阶段计划的最小验证接口；B/C 是收窄后的 Husky 内候选，不构成对未通过阶段门槛的放行。路线若改变预测目标、阶段入口或评测协议，应先更新 DECISIONS 和实验预注册；不自动启动 P3/P4 掩盖 P1/P2 负结果。

## 6. 内部 surrogate 与机器人 outcome

| 量 | 当前含义 | 研究使用边界 |
|---|---|---|
| A* 占据/高度/膨胀代价 | 参考路径生成的几何 surrogate，[eeplanner.py:503](../src/modulation_rl/scripts/modulation/envs/eeplanner.py#L503) | 不等于真实碰撞概率或物理可执行性 |
| BioIK 位姿目标、关节正则 | 当前控制步的解质量/可行性，[robot_env.cpp:431](../src/modulation_rl/src/robot_env.cpp#L431) | 不能替代未来轨迹稳定性或成功率 |
| reward 与 Q | 奖励含碰撞/IK、动作幅度/变化、速度项，[combined_env.py:325](../src/modulation_rl/scripts/modulation/envs/combined_env.py#L325)；Q 是该目标的价值估计 | 更高 return/Q 不自动证明更安全、更快或更可靠 |
| P1 feature MSE | 标准化 robot/map 块预测误差 | 是模型指标，不是移动操作收益；不能据此跳过 copy 对照 |
| goal-reached SR / perfect-success | runner 基于终止原因；perfect 要求成功且整个回合碰撞/IK计数为零 | 必须同时报失败分类；不是“从未碰撞”与“到达目标”任选其一 |
| collision_count / ik_count | 累计发生该标志的步数，[p0_runner.py:155](../src/modulation_rl/scripts/p0_runner.py#L155) | 连续接触可计多步，不是独立碰撞事件数量；跨控制频率比较需注意曝光时间 |
| 路径长度、任务墙钟/仿真时间 | 已保存实际 rollout 的底盘路径和时间 | analytical 和 Gazebo 分开报告；不能把 reference path length 冒充实际轨迹长度 |
| control_seconds | runner 计时范围是策略调用 + env.step，[p0_runner.py:134](../src/modulation_rl/scripts/p0_runner.py#L134) | 含 IK/planner/等待等，不能标为纯 WM inference latency；WM 新增耗时应另测且保留总耗时 |
| tracking / terminal error / safety margin | 部分末端误差存在 robot_info；当前核心 summary 未统一覆盖 minimum clearance、近碰撞、全程关节加速度等 | 需要对应任务/传感器定义和逐步日志，不能把未记录指标写成已验证 |

当前核实的是数据流与插入位置，尚未验证任何新增方法的成功率、安全性或闭环增益。后续实验仍须遵守 [EVALUATION.md](EVALUATION.md)、[PROGRESS.md](PROGRESS.md) 与当前研究协议，以匹配结构、预算、数据和种子对照区分世界模型、重复预测、执行反馈及额外容量各自的作用。
