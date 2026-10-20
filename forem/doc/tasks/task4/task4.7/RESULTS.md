# task4.7 — 机制映射与执行合同核对结果与交接

> **当前状态（2026-10-19核对）：closed（随task4于2026-10-16关闭；未经独立复核）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**review（Claude已实施并交付合同；待父任务/4.13汇总核验）**。实施者：Claude主Agent（实际模型claude-sonnet-5-5，会话级effort high，见[独立日志](../../../agent_logs/task4/20261009-claude-task4-scwm-impl.md)）。2026-10-09。

> 本节点为只读审计＋合同登记：**没有修改`forem/src`下任何文件、没有启动仿真/训练**。唯一新运行是CPU上的策略反例脚本（见下）。合同值标注“已读源码/已测量/待4.8测量/工程选择”，未确认值不冻结。

## 1. 版本与证据

- 源码身份：[`source_manifest.json`](../../../../results/task4/t4.7-contract-audit-r1/source_manifest.json)（25个文件sha256；根HEAD 438c5f9，工作区dirty，以文件hash为准；scwm参考commit f2f2f5ff）。
- 反例：run-id `t4.7-contract-audit-r1`，命令`python3 scripts/audit_scwm_policy_tanh.py --out results/task4/t4.7-contract-audit-r1/policy_tanh_audit.json`（forem-dev内，CPU，退出码0），输出[`policy_tanh_audit.json`](../../../../results/task4/t4.7-contract-audit-r1/policy_tanh_audit.json)。

## 2. 状态/动作/奖励/终止合同（读自源码，4.8起运行核验）

| 项 | 合同内容 | 来源（文件:符号） |
|---|---|---|
| 任务 | `SimpleObstacleTask`（静态障碍场），robot `husky_ur5`，`world_type=gazebo`，BioIK，`perception_style=base`，`execute_style=direct` | `config/task3/task_contract.yaml` |
| 策略观测 | `(robot_state[41] float32, local_map[120,120,1] float32)`；41维字段见下；地图为3m×3m 0.025m滚动局部代价图（前向激光，非真值） | `scripts/task3_env.py:OBS_FIELDS`，`combined_env.py:_to_agent_obs` |
| 41维来源 | `[0:7]`相对夹爪TF（规划臂＋**实测**底盘）、`[7:14]`下一夹爪TF（规划）、`[14:21]`末端速度（规划）、`[21:28]`目标相对底盘（规划＋实测底盘）、`[28:34]`**规划IK关节**（不是实际关节反馈）、`[34:37]`腕到目标、`[37]`自碰撞（规划IK状态）、`[38:41]`上一策略动作 | `OBS_FIELDS`；`robot_env.cpp:step`（`perception_style=base`只用`setWorldJoint(latest_base)`更新底盘） |
| 底盘反馈 | Gazebo p3d(50Hz)`/ground_truth/state`→`pose_bridge`→TF `odom→base_footprint`（原样本stamp），每步重读。**这是两方法共同可得的“Gazebo当前底盘反馈”**；评估真值`/gazebo/model_states`仅评估，不进观测 | `config/task3/core_contract.yaml:pose_chain` |
| 动作 | 3维连续，范围[-1,1]：`[vel_norm, base_rot, base_vel]`；vel_norm→[0.01,0.3]m/s（末端规划速度），base_rot×1.0rad/s，base_vel×0.3m/s；臂由BioIK（timeout 0.01s）求解后以单点FollowJointTrajectory（`time_from_start=dt_exec=0.02s`）发送 | `combined_env.py:_convert_policy_to_env_actions`，`robotenv.py:step`，`robot_env.cpp:step/sendArmCommandCurrent` |
| 动作噪声 | `transition_noise_base=0.04`（Task3继承的argparse/best_defaults值）：底盘速度命令加高斯噪声。**本节点不改**（SRC0178：不自动设0）。两方法完全相同；在两方法共用的基线内它是任务本身的一部分 | `task_contract.yaml`，`robotenv.py:step` |
| 奖励 | `ee_reward`（规划进度/到达）−10·碰撞＋IK L2松弛惩罚−0.05|Δa|²；再乘vel_norm/max再减0.1·((max−v)/max)²。**不改** | `combined_env.py:calculate_reward` |
| 终止 | done＝（到达且无该步kin_failure）或kin_failure累计≥20或底盘碰撞累计≥20；另`MaxCloseStepsWrapper`close步≥500为截断；**replay mask＝float(not done)，截断也不自举（沿参考）** | `combined_env.py:step`，`utils.py:MaxCloseStepsWrapper`，`task3_sac_entry.py:make_mask` |
| 内部成功 | `episode_is_success=nr_kin_failures==0 and nr_base_collisions==0 and ee_done`；`ee_done`由`_is_done(robot_obs.gripper_tf)`得出，`gripper_tf`＝**规划臂关节＋实测底盘**的FK末端，阈值`success_thres_dist=0.025m`、`success_thres_rot=0.05`（`calc_rot_dist`） | `eeplanner.py:_is_done`，`tasks.py:146-147`，`utils.py:episode_is_success` |
| 物理成功 | 独立于规划：在done时用实测末端`gripper_tf_achieved`（`world_->getGripperTransformWorld()`，来自TF）对目标`gripper_goal_wrist`，位置<0.025m、`1−(qa·qb)²<0.05`，且0 kin_failure、0碰撞（沿SRC0108的公式，不新增阈值）；缺反馈单独计“缺反馈”。**物理成功只作评估/报告，不进奖励/终止/replay** | `robot_env.cpp:getRobotObs`（`gripper_tf_achieved`），SRC0108，SRC0161 |
| 关节通道 | `info['planned_arm_joints']`（IK）与`info['actual_arm_joints']`（`get_joint_values_world`，控制器/joint_states反馈）分开记录；观测中的关节标签恒为“规划”。控制器即时参考另需新增记录（4.8） | `task3_env.py:step` |

## 3. 时间合同（部分待4.8测量）

- 已读：`dt_exec=0.02s`是传给规划器/IK的名义步长（`robotenv.py:step`的`rate.sleep_dur`），**`rate.sleep`在Python中被注释**；环境对着**不暂停的实时Gazebo**运行，策略计算耗时计入仿真时间（`core_contract.yaml:timing.note`）。Task3实测：无学习时每`env.step`仿真0.0152s／墙钟0.0173s（20步均值，`t3.3-env-r1`）。
- 含义：实际仿真动作区间随策略推理＋更新耗时变化（SRC0161曾观察评估相邻步sim间隔中位0.054s）。WM前瞻增加推理耗时，会改变同一动作被执行的物理时间。**4.8必须测量实际sim间隔分布；若耗时波动足以混淆比较，需对两方法共同修复调度（固定仿真时间决策窗口），不能让反馈组因为“多算”而物理时间不同。当前不改.02s、不改求解器、不改噪声（SRC0178）。**

## 4. SC²-WM→Husky 机制映射（文献事实／工程适配／待验证）

| 环节 | SC²-WM（论文/已读代码） | Husky工程适配（本任务） | 性质 |
|---|---|---|---|
| 候选 | 对每个图候选节点（`gmap_embeds[:,2:]`）并行评估 | 当前actor对**当前观测**的**确定性**候选动作a0（均值的tanh），不执行 | 工程适配 |
| 预测 | `world_model([NAV,V_mixed,V_raw])→vis_predictor`预测候选到达后的视觉特征`V_pred` | `F_phi(z_t, a0)→ẑ_{t+1}`：固定参考编码器得到的256维任务相关表征的动作条件MLP；监督用**真实执行的最终动作**和执行后真实`o_{t+1}` | 工程适配（非复现Transformer/语言/图） |
| 反馈 | `H_rebuild.detach()`，`g=σ(W[a;H])`，`δ=W[H;a]`，`H_enh=a+g·δ`，再用`enhanced_sap_head`二次评分（zero-init） | `δ̂=F(z,a0)−z`作为预测变化，经门控残差`G(h,δ̂)`修正策略表征，再由原SAC动作头输出最终分布；**零初始化，使开始时≈普通SAC** | 工程适配 |
| 输出角色 | 二次评分选择路点；IK/控制由环境执行 | 最终动作仍由SAC输出，IK/控制器角色不变；`δ̂`是预测量，**不是要最小化的误差标签** | 保持角色 |
| 梯度 | 反馈支路对`H_rebuild`使用detach（官方选择，离散选择） | **本任务首轮：冻结F与参考编码器权重，但保留SAC actor所需经F输入到候选的导数；不统一no_grad**（SRC0179）。若改用detach截断须另论证 | 与官方不同，待4.10验证 |
| 测试期适配 | 评估时对“已执行候选的旧预测vs到达后真实特征”做余弦损失，KL分位触发更新，L2到初始权重 | 4.12独立因素，首轮不启用 | 后续 |
| 未迁移 | 语言指令、VCM、图路点/拓扑、Transformer、导航数据 | 全部不迁移，不加载SCWM权重，**不称完整复现** | 文献/工程差异 |

SC²-WM在导航与离散候选上给出收益证据，**不保证**Husky连续控制收益（SRC0171/0176）。

## 5. 静态疑点→反例结论（已运行）

`GaussianPolicy.predict()`对`action_dist.actions_from_params(...)`的结果再次`tanh`，而`SquashedDiagGaussianDistribution.sample()/mode()`已含`tanh`：

- 同参数同输入、固定torch RNG：`eval`模式的`predict`与单tanh模式的最大绝对差0.0161；随机模式`predict`与`sample()`的动作最大绝对差0.2356；`predict == tanh(sample动作)`为真（即**双tanh确认**）。
- 后果：**在线执行的动作被压缩到±tanh(1)=0.7616**（观测`executed_action_abs_max`0.7595，`sampled_action_abs_max`0.9951），而`update_parameters`的actor损失、critic目标和log_prob都针对单tanh策略；replay里存的是双tanh后的执行动作，critic学到的是被压缩动作的Q，actor却在(−1,1)全域优化。这是**采样—logprob—更新三处不一致**，正好违背本任务“在线采样、logprob、actor、critic目标和温度更新使用一致策略分布”的硬要求。
- 处理：**两方法共同修复**——4.8在新的`scwm_policy.py`中以子类修正`predict`为单tanh（`FixedGaussianPolicy`），迁移的`model.py/sac.py`原文件不改（保持Task3 hash），并在回归测试中固化“predict与sample同分布”。这是公共正确性修复（动作语义由“压缩的双tanh”变为“与训练一致的单tanh”），在4.8 RESULTS中单列影响，不是只修反馈组。**历史Task3/Task4训练与旧先导结果因含双tanh，不能当新基线比较**。

## 6. 数据/表征/拆分合同（冻结的选择）

- WM数据记录字段：`(run_id, seed, episode_id, epoch, step, t_obs, o_t, a_final, t_cmd, t_next, o_next, done, mask, source_hash)`，时间同一仿真时钟；reset后新初态不冒充terminal next。
- 表征`z=E_ref(o)`：**取共同前缀结束时普通SAC的actor trunk（CNN＋FC）的冻结副本**，256维；该副本版本号与sha256写入WM checkpoint，策略自己的trunk继续学习，因此WM的输入输出空间不随策略漂移。
- 拆分：按**完整episode**稳定hash划分训练/验证，归一化只用训练侧拟合；WM模型选择只看验证；不用任务成功选WM参数。
- 评估实例：沿SRC0108，训练实例种子0–99、验证101–105；**不新增确认测试201–220**；已见的旧测试106–110仅作历史说明、不用于选择。最终报告的测试实例沿“有效协议”：见预算表“尚缺口径”。
- checkpoint选择：只用验证（成功→完整反馈→回报→最早）。

## 7. 预算覆盖表（沿用户接受的规模；不使用草案切片）

用户规模：**100万步／原讨论3种子／一轮完整训练＋评估≤72h**。

| 项 | 本节点登记 | 状态 |
|---|---|---|
| 方法 | 普通SAC（plain）、冻结WM反馈SAC（feedback）；feedback的“关闭旁路”只是接口回归，**不是正式第三组**；TTA（4.12）独立 | 已明确 |
| 种子 | 3 | 用户“原3种子讨论” |
| 每方法每种子 | 1,000,000环境步，每步1次SAC更新（`updates_per_step=1`，`batch=256`，沿`sac.yaml`） | 沿用户规模，按“每run 100万名义步”理解 |
| 共同前缀（工程选择，非草案固定值照搬） | 每种子先训练普通SAC到前缀步数K，记录全部转移；feedback从该状态**分叉**继续（plain也继续）。K由4.8吞吐＋WM所需样本量确定后登记；前缀交互在两方法中**各计一次**（按方法汇报），唯一实际交互另列 | **K未定，待4.8/4.9证据**；这是总预算口径的唯一歧义，见下 |
| WM训练 | 在前缀数据上训练；其环境交互已含在前缀内，**不额外采集**；额外计算（GPU时间）单列 | 机制已定，规模待定 |
| 评估 | 验证用于checkpoint选择；最终固定分母的测试集合在4.11前须由有效协议明确 | **尚缺**：测试实例数/次数 |
| 72h | 全局墙钟（含前缀、WM、两方法后缀并行、评估），与累计worker小时分开报告 | 由4.8实测吞吐估算 |

**唯一待用户确认的口径**（影响总预算，不阻塞4.8）：(a) “100万步”是否按**每方法每种子一个run**理解（即plain 3×100万＋feedback 3×100万，含共同前缀按方法各计）；(b) 采用共同前缀分叉（feedback与plain获得相同的前缀信息，WM无额外交互）是否可接受，或要求feedback从零开始、WM数据另列；(c) 最终测试实例数（草案的201–220/20集不是授权）。在这些确认前，4.8按“plain 1M×3种子”的最小共同需要推进。

## 8. 文件职责（将新建，均在forem合法目录）

| 路径 | 职责 |
|---|---|
| `scripts/scwm_policy.py` | `FixedGaussianPolicy`（单tanh修复）、反馈策略（4.10） |
| `scripts/scwm_sac.py` | `ScwmSAC`（沿原`update_parameters`，仅换策略类；GPU回放；计数） |
| `scripts/scwm_env.py` | 包装`Task3Env`：物理成功、实际关节/控制器参考记录、sim时间戳、不改奖励/终止 |
| `scripts/scwm_train.py` | 训练入口：预算/账本/检查点/恢复/日志 |
| `scripts/scwm_wm.py` | WM数据集、F_phi、训练与验证（4.9） |
| `scripts/scwm_*` 并行启动脚本 | 多实例隔离启动（4.8子任务） |
| `config/task4_scwm/*.yaml` | 新协议配置（不覆盖`config/task4`旧VIO） |
| `tests/test_scwm_*.py` | 回归测试 |

## 9. 风险与剩余

- 双tanh为已确认的公共缺陷；修复前不得做任何“基线”性能结论。
- 动作窗口依赖墙钟计算时间（实时Gazebo）；WM额外耗时可能混淆，4.8测。
- 物理成功现有实现需新增（读`gripper_tf_achieved`与规划目标）；并存在平面投影限制（SRC0161），4.8复核。
- 预算口径待用户确认(a)(b)(c)；此前不得启动正式长训。

下一步：task4.8（基线实现与有限先导/性能）。
