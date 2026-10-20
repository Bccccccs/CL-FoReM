# task3.2 移动模型、控制器与参考位姿链 — 结果与交接

> **当前状态（2026-10-19核对）：done（随task3经task3.6 R2验收）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

**当前：done，父Task3.6 R2独立验收通过（2026-10-07），旧review是历史。** 最终当前freeze4、GPU默认及来源/时间/路径/包装身份修正闭环见[3.6结果](../task3.6/RESULTS.md)及[SRC-0066](../../../SOURCES.md#src-0066)。推荐GPT6.1sol/Sonnet5.5，跨模块medium，常规整理low/default；实际原Claude强度未知，最终验证子gpt-6.1-sol/medium。

状态：**review（实施完成，待task3.6独立复核）**。实施：Claude（Sonnet5.5，强度未知）。依赖：[task3.1](../task3.1/RESULTS.md)。

## 实际构建与启动

- 容器：现有`forem-dev`（镜像`mm_husky:node01`，sha256:e674db49…dfc430，未重建、未换镜像）。无GPU（forem-dev创建时未带GPU）。
- 构建：`catkin build`，9个包+forem_sim；首次（Python3.8 ABI）[t3.2-build2](../../../../logs/task3/t3.2-build2/catkin.log)退出0，随后发现绑定ABI为cp38，运行用Python3.10，**改catkin cmake-args为`PYTHON_EXECUTABLE=/opt/python310/bin/python3`并全量重建**（[t3.2-build3](../../../../logs/task3/t3.2-build3/catkin.log)退出0；原配置备份于同目录`catkin-config-before-py310.yaml`）。早先build1因husky_control/robotiq_85_description的`roslaunch_add_file_check(launch)`指向未导入的launch目录失败（已补丁，保留日志）。重建改变的是工作区全局cmake参数；forem_sim无编译产物，Task0–2不受影响（未重跑其验收）。
- 导入来源：`modulation/sac/model/replay_memory`来自`forem/src/modulation_rl/scripts`，`pybindings*`来自`forem/devel`，`stable_baselines3`为参考附带分叉（`forem/src/modulation_rl/scripts/stable_baselines3`）。证据：[env_summary.json](../../../../results/task3/t3.3-env-r1/env_summary.json)`module_provenance`；`check_task3_env`的`import_from_forem_only`通过。
- 入口：`forem_husky/launch/husky_core.launch`（Gazebo先暂停→`forem_sim/start_controllers.py`设臂初始姿态、加载并启动5个控制器后解除暂停；moveit move_group、twist_mux、两个costmap_2d、pose_bridge）。与参考launch的差异逐条写在launch头注释。

## 关键发现（均有run证据）

1. **重力被关**：参考bumper宏对所有带bumper的链接设`turnGravityOff`；Gazebo中底盘悬空、轮子空转，0.2 m/s指令只产生0.0075 m/s（[t3.2-motion-r1](../../../../results/task3/t3.2-motion-r1/physics_summary.json)；spawn z=0下z漂到0.12 m、0.019 m/s：[grav-off-diag1](../../../../results/task3/t3.2-motion-grav-off-diag1/physics_summary.json)；link探针[t3.2-links-diag1](../../../../logs/task3/t3.2-links-diag1/check.log)）。先是移除全部`turnGravityOff`（r2–r4，底盘可驱动），**但3.5发现全链重力开会使参考臂PID在随机episode后不稳定、复位失败**（[SRC-0059](../../../SOURCES.md#src-0059)），最终改为：**底盘/轮子重力开，UR5臂与夹爪15个链接保持参考的无重力**（patch，semantic_impact=declared）。[SRC-0051](../../../SOURCES.md#src-0051)
2. **导入顺序**：`import torch`在pybindings之前会`std::bad_cast`，需先`import ray`。[SRC-0052](../../../SOURCES.md#src-0052)
3. **p3d噪声未生效**：URDF请求0.01，实测p3d与Gazebo真值相差~1e-10 m。[SRC-0056](../../../SOURCES.md#src-0056)
4. 仿真时钟复位后RobotEnv的C++ tf监听器保持不连通树（见task3.5），故`/gazebo/reset_simulation`不被支持。
5. 参考launch两个JointStateController重复发布`/joint_states`，MoveIt状态监视器每40 ms警告“not newer”（日志噪声，参考原样保留，未处理）。

## 运动/位姿链检查（`scripts/check_task3_physics.py`，门槛为工程选择，见[PROCEDURE](PROCEDURE.md)与[SRC-0054](../../../SOURCES.md#src-0054)）

|run|world solver|结果|直行0.2 m/s实测|原地转0.5 rad/s实测|组合速度比/速率比|说明|
|---|---|---|---|---|---|---|
|t3.2-motion-r1|world,重力关,z=0.2|FAIL|0.0075 m/s|0.0 rad/s|—|底盘不动|
|grav-off-diag1|world,重力关,z=0|FAIL|0.0192|0.006|—|同上|
|t3.2-motion-r2|world,重力开|FAIL(turn_xy,coord)|0.1975|0.531|—|门槛首版过严：原地转平移0.384 m>0.10；coord用弦长速度|
|t3.2-motion-r3|同上|FAIL(coord)|0.1974|0.542|0.108路径速度|coord门槛仍用±25%|
|t3.2-motion-r4|world,**全链**重力开|PASS 19项（模型已被取代）|0.1974|0.530|0.74/0.85|门槛v3（见SRC-0054）后的新run；该模型后被3.5发现臂复位不稳定|
|**t3.5-motion-armgrav-r1/r2/r3**|world,**底盘重力开+臂无重力（最终模型）**|**PASS 19项×3**|0.1955/0.1954/0.1955|0.456/0.461/0.460|0.665/0.578；0.682/0.605；0.674/0.619|重复性：直行速度差≤1e-4 m/s；原地转平移0.17–0.18 m；实时因子0.80–0.81；臂终值误差≤2.9e-5 rad|
|t3.2-motion-quick-diag2|quick,重力开|PASS|0.1976|0.424|0.68/0.60|只作对比，未选用|

最终模型细节（armgrav-r1）：保持3 s臂最大误差1.5e-5 rad；上面的r4细节（全链重力开）：保持3 s基座漂移0.0、臂最大误差1.0e-5 rad；臂动作（+0.3/+0.2 rad）终值误差≤6.1e-4 rad；TF：`/tf`发布者仅`/pose_bridge`与`/robot_state_publisher`，`odom→base_footprint`唯一作者`/pose_bridge`，p3d样本与TF按原时间戳匹配99.9%、值差2e-16，`map→odom`恒等；实时因子0.72–0.82。**门槛修订发生在看到r2/r3数据之后**（事后调整），r1–r3的FAIL原始数据保留。

solver选择：沿用FoReM task0.7的`world`；quick对比见[SRC-0055](../../../SOURCES.md#src-0055)。Husky上未复测2 kHz高频交替（待补证据）。

## 位姿桥接口

`forem_husky/scripts/pose_bridge.py`+纯逻辑`pose_gate.py`：输入`nav_msgs/Odometry`（`pose_topic`，默认`/ground_truth/state`），拒绝非有限、四元数范数偏离、非期望frame/child、零戳、回退戳（<1 s回退拒绝；>1 s回退记新epoch而不是静默接收）；输出TF `odom→base_footprint`，**用输入戳**，状态JSON在`/pose_bridge/status`含`pose_source`。参考`gdt_tf`用`ros::Time::now()`重盖戳且无校验。测试`tests/test_task3_pose_bridge.py`（10项，含`test_duplicate_pose_authority_rejected`、`test_wrong_frame_rejected`、`test_backdated_epoch_rejected`）。Task4替换接口见[core_contract.pose_chain](../../../../config/task3/core_contract.yaml)。

## 验收对照

|验收项|结果|
|---|---|
|catkin构建退出0、模块路径在forem|通过（build3；provenance）|
|唯一pose/TF链、原采样戳|通过（r4及后续int-r1）|
|四种动作有命令和实际证据|通过（timeseries.csv含命令、truth、odom、臂desired/actual）|
|限位/非有限/振荡|通过：无非有限；臂速度RMS 1.6e-4 rad/s（125 Hz反馈）|
|截图不代替数据|仅用数据|

## 限制与未做

仅静止开阔地面、一次运动序列（r4），重复性依赖task3.5的int-r1及后续；125 Hz反馈看不到1 kHz振荡；未测碰撞/斜坡；GUI未验证；原地转向平移、组合弧线减速是skid-steer特性，会影响“策略指令→实际位姿”的一致性，RL通过TF实测位姿闭环补偿（direct模式）。

## 交接

注意：本节点前面r1–r4运行时的模型与最终模型不同（r2–r4全链重力开，已取代）；最终模型的证据是t3.5-motion-armgrav-r1/r2/r3与3.5的int-r3。

复核方法：`sg docker -c 'bash forem/scripts/run_task3_core.sh NEWID -- python3 scripts/check_task3_physics.py --run-id NEWID'`（需forem-dev空闲）；`python3 -m unittest tests.test_task3_pose_bridge`。停止/清理：脚本自动用身份监督清理；手动：`bash forem/docker/run.sh exec python3 scripts/task0_proc.py stop --dir logs/task3/<run> --name launch`。无后台进程。

依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046) · [SRC-0051](../../../SOURCES.md#src-0051) · [SRC-0052](../../../SOURCES.md#src-0052) · [SRC-0054](../../../SOURCES.md#src-0054) · [SRC-0055](../../../SOURCES.md#src-0055) · [SRC-0056](../../../SOURCES.md#src-0056)。

## Agent模型与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5；跨模块物理/TF排错medium（实际问题：重力/ABI/导入顺序）。实际：Claude Sonnet5.5，强度未知。


## 2026-10-07 追加：T3-A02位姿门控修正（Claude；上文为原始实现的历史描述）

原规则“>1 s回退戳记新epoch并接受”已被task3.6审查证明有误（迟到样本/旧epoch排队消息被当作reset）。现行为：reset只由独立`/clock`话题回退>`~reset_jump`(1 s)确认；确认后epoch+1一次并**halt**（不再发布，状态`halted=true`，后续样本记`rejected_halted`），需重启仿真+bridge（`/gazebo/reset_simulation`仍不支持）；戳不严格递增（无论多大）记`rejected_backdated`；戳超前时钟>`~future_tolerance`(1 s)记`rejected_future`；未收到时钟记`rejected_no_clock`；原戳从不改写。修正前后证据与测试见[task3 RESULTS](../RESULTS.md#2026-10-07-task36三项p2修正claude)。[SRC-0062](../../../SOURCES.md#src-0062)
