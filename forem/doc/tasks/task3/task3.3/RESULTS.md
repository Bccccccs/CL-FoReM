# task3.3 机器人、IK、观测与任务核心迁移 — 结果与交接

> **当前状态（2026-10-19核对）：done（随task3经task3.6 R2验收）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

**当前：done，父Task3.6 R2独立验收通过（2026-10-07），旧review是历史。** 最终当前freeze4、GPU默认及来源/时间/路径/包装身份修正闭环见[3.6结果](../task3.6/RESULTS.md)及[SRC-0066](../../../SOURCES.md#src-0066)。推荐GPT6.1sol/Sonnet5.5，跨模块medium，常规整理low/default；实际原Claude强度未知，最终验证子gpt-6.1-sol/medium。

状态：**review（实施完成，待task3.6独立复核）**。实施：Claude（Sonnet5.5，强度未知）。依赖：[task3.2](../task3.2/RESULTS.md)。

## 迁移内容与适配

- C++（`robot_env/robot_husky/worlds/validity_fun/myutils/gaussian_mixture_model/mycostmap/my_static_layer/pybindings*`）逐字导入，仅`pybindings_robots.cpp`、CMake、package.xml做Husky-only裁剪；Python`modulation/envs/*`（含`combined_env/eeplanner/tasks/map/simulator_api/env_utils`）**逐字**，仅`robotenv.py`去掉其他机器人分支（AST对`calculate_reward/ik_reward/step/_to_agent_obs/reset/draw_goal…`与参考一致：`tests/test_task3_semantics.py`通过）。
- 参考中的`/home/cbl`和旧workspace硬编码路径只存在于未导入的main.py/eval.py/handle_launchfiles；迁移闭包内无（audit prior检查）。离线日志不需要外部账号：本入口不使用wandb。
- 新增`scripts/task3_env.py`（`Task3Env`）：`reset(seed, episode_spec)`、`step(action)`，校验动作（形状3、有限、∈[-1,1]）；返回经典4元组并在`info`加`terminated/truncated/success/planned_arm_joints/actual_arm_joints/obs_arm_joint_labels/base_tf_obs/pose_source`；Gazebo真值只经`evaluation_truth()`；仿真时钟回退使当前episode失效。参考行为保持：随机采样、碰撞来自Gazebo接触话题、局部地图来自前激光costmap。
- 观测/动作契约冻结在[task_contract.yaml](../../../../config/task3/task_contract.yaml)：动作`[vel_norm, base_rot, base_vel]`；41维robot_state字段表；`joint_values_scaled`是**IK规划值**。

> 注意：t3.3-env-r1/t3.4-*-r1是在**全链重力开**的旧模型上运行的（后被3.5取代，见[SRC-0059](../../../SOURCES.md#src-0059)）；最终模型的同类证据是[t3.5-int-r4的env阶段](../../../../results/task3/t3.5-int-r4/env/env_summary.json)（20项通过，规划-实际臂差0.034 rad、观测底盘vs真值最大0.0044 m、2 episode 84/270步均IK失败终止）。下表为旧模型数值，保留为历史尝试。

## 运行证据（`scripts/check_task3_env.py`，run [t3.3-env-r1](../../../../results/task3/t3.3-env-r1/env_summary.json)，fresh启动，退出0，20项全过）

|检查|结果|
|---|---|
|导入全来自forem|通过（8个模块路径见`module_provenance`）|
|空间|动作Box(3,)[-1,1]；观测(41,)float32+(120,120,1)|
|obs字段顺序|`relative_gripper_tf`、`joint_values_scaled`、`previous_action_mean`与由RobotObs/动作历史重算值最大差5.0e-8/1.4e-8/1.2e-8|
|规划≠实际|观测关节==IK规划值；实际关节来自`get_joint_values_world`，两通道最大差0.120 rad（均值0.040），故是不同数据|
|同seed同episode|seed 11两次hash相同（1b8354da…）；seed 12不同；`episode_spec`不匹配被拒绝|
|障碍真的在Gazebo|spec 16个障碍全在`/gazebo/model_states`（共18模型）|
|reset|清空previous action（obs[38:41]=0）与计数；连续两次reset可用|
|非法动作|形状2/4/标量/嵌套、NaN、Inf、1.5均`ValueError`，之后env仍可用|
|观测底盘 vs Gazebo真值|xy最大差0.0485 m（均值0.0053 m），贴近门槛0.05——来源是TF/真值采样时间错位，运动中偏大|
|完整尝试|随机策略2个episode：181步、409步，均因IK失败累计20终止（`terminated=True,truncated=False,success=False`）；随机动作失败不等于迁移失败|
|时间|每步：墙钟0.0173 s、仿真0.0152 s（20步，无学习）；reset约10 s墙钟|

测试：`tests/test_task3_env_contract.py`（`test_action_shape_rejected`、`test_observation_field_order`、`test_expected_joint_not_labeled_actual`等）、`test_task3_semantics.py`（`test_reward_components_preserved`）。`test_reset_clears_previous_action`由运行检查`reset_clears_previous_action`承担（需要仿真）。

## 值得知道的行为（未改，参考原样）

- `reset`把底盘放到z=0.05 m再释放；臂用4 s轨迹回到固定折叠姿态（`drawJointValues`总返回该姿态，随机分布实际是固定的）；reset失败最多重试10次（参考逻辑）。
- 在线规划地图（`PointToPointPlanner`用的floorplan）是障碍的**真值**；只有观测的本地地图来自激光costmap。
- 仿真不暂停：策略/SAC更新耗时会让仿真时间流逝。
- 3.0/0.8障碍间距/偏移覆盖、500步MaxCloseSteps、IK失败阈值20见契约。

## 真值读取的一个教训

t3.5-int-r2发现：`evaluation_truth()`最初用常驻订阅缓存，C++ `reset`持有GIL时，缓存会在整个episode内停在reset前的消息（机器人仍在x=30的“出镜”位置），与TF相差30 m；改为每次新鲜阻塞读取`/gazebo/model_states`。此外在reset刚结束的1–2步内`model_states`本身也比p3d落后（t3.5-truthdbg1：reset后`model_states`仍为x=29.997，p3d已在0.524），评价时应跳过reset后最初几步。

## 限制

没有成功到达目标的episode被记录（未写目标导向的脚本策略，避免新增功能）；奖励分项只通过源码逐字一致证明，没有运行时分项分解；局部地图obstacle内容的正确性只证明“障碍在Gazebo且地图非空”，未与障碍真值逐格比较；采样次数很小（2 episodes）。

## 交接

复核：`sg docker -c 'bash forem/scripts/run_task3_core.sh NEWID -- python3 scripts/check_task3_env.py --run-id NEWID'`（约5分钟）。`python3 -m unittest tests.test_task3_env_contract tests.test_task3_semantics`（前者在容器内）。无后台进程。

依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046) · [SRC-0053](../../../SOURCES.md#src-0053)。

## Agent模型与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5；时序/观测/规划-实际核对medium。实际：Claude Sonnet5.5，强度未知。
