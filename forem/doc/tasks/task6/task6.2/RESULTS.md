# task6.2 RLlib Gazebo组 — 结果与交接

> **当前状态（2026-10-19核对）：paused（2026-10-14用户要求停止于26.9万步；不要恢复）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**paused（2026-10-14 14:55+08:00按用户明确指令“task6.2 G-B这个停下吧不要这个”停止t6.2-gz-train-s40，于26.9万步；未到30万步评估，见文末“用户要求停止”节）**。此前状态：active（2026-10-13 11:23起G-B正式训练运行中，N=10+1、每步固定0.1 s）。原状态行：**blocked（§4.3：N=20的CPU门槛与5%实时因子判据均不满足，停下等Claude决策；§2 r5、§3 r2、§4冒烟已通过）**。本文件只记录实际执行结果；计划内容见[TASK](TASK.md)和[PROCEDURE](PROCEDURE.md)。

## 阶段状态

|阶段|状态|run-id|证据|
|---|---|---|---|
|§1 开工与基线冻结|已执行|`t6.2-baseline`|[SRC-0231](../../../SOURCES.md#src-0231) / 下文|
|§2 容器与单实例Gazebo就绪|**通过**（G-D9 0.0005 s，r5）；r1–r4保留：r3第三reset失败，r4诊断根因|`t6.2-env-r1…r5`|[SRC-0237](../../../SOURCES.md#src-0237) / [SRC-0240](../../../SOURCES.md#src-0240) / 下文|
|§3 多实例隔离|**通过**（r1未过自设1 mm阈值，r2 12/12）|`t6.2-iso-r1/r2`|[SRC-0240](../../../SOURCES.md#src-0240) / 下文|
|§4 冒烟、profile、确定N|冒烟通过；profile部分完成；**N=20不可行，停下**|`t6.2-smoke-r1`、`t6.2-bench-r1/r2`|[SRC-0241](../../../SOURCES.md#src-0241) / 下文|
|§5 正式训练|active（既有训练，Codex接回监控）|`t6.2-gz-train-s40`|[SRC-0247](../../../SOURCES.md#src-0247)|
|§6 最终Gazebo评估|尚未执行|`t6.2-gz-eval-s40`|—|
|§7 对照汇总|尚未执行|`t6.2-summary`|—|

## 对照表（由§7填写）

|评估步|task5.2 B（sim）success|task6.2 G-B（Gazebo）success|Task4.8 plain参照（内部成功/5，口径不同）|
|---|---|---|---|
|75000…1000000|待填|待填|待填|

## 交接

- 目标与授权：见[TASK](TASK.md)、父[task6](../TASK.md)、[SRC-0227](../../../SOURCES.md#src-0227)、[SRC-0229](../../../SOURCES.md#src-0229)。
- 当前负责人：Codex（已接手；当前停止实施交Claude决策）；Claude负责确定N（如需）与复核。
- 风险：melodic下Husky Gazebo启动未验证过；RLlib worker进程中ROS初始化时机可能使环境变量映射失效；21个Gazebo实例的CPU占用未知；上游代码不支持续训。
- 下一步：Claude明确§2启动入口和允许的适配范围后再继续；§5仍须Task5 A/B训练退出及N=20预算门槛。

## 开工 2026-10-12T09:35:33.222479+08:00

负责人Codex；用户已派发§1–7，正式训练受Task5退出和N=20资源门槛限制。实际模型系统标识GPT-6，精确型号/强度未知。推荐GPT6.1sol/Sonnet5.5，medium（跨进程隔离核对）。[日志](../../../agent_logs/task6/task6.2/20261012-codex-task6.2.md)。

## §1 实际冻结（2026-10-12T09:41:29.725539+08:00）

[SRC-0231](../../../SOURCES.md#src-0231)。`python3 forem/build/task6.2/scripts/t62_freeze.py`退出0；`cp -a forem/build/task5/ws_husky forem/build/task6.2/`及deps复制退出0。工作区4616条、依赖1004条（普通文件SHA256+软链字面目标）一致。Task5三个配置SHA、完整清单和副本比对：[baseline](../../../../results/task6/t6.2-baseline/)；D1–D11逐项继承/不适用说明在`inherited_deviations.json`。软链不沿宿主绝对路径读取，容器挂载仍为/forem_build，原scripts/logs软链保留，未开始训练也未写入该Task5 run-id路径。

开工`docker ps`、GPU/free/进程检查：Task5两CPU trainer仍运行（主机2141240/2265226）；GPU四卡0%计算占用、内存约167GiB可用。末次两秒/proc/stat主机快照5.68核，仅当时快照，不算profile或N依据。`source_diff_vs_task5.json`确认Task5冻结已有条目未变，task6.2副本已有条目未变；env_creator映射尚未写。

## §2 实际执行与失败

镜像digest与Task5一致；完整docker run argv、退出码0、容器ID和inspect记录在[container_create.json](../../../../results/task6/t6.2-env-r1/container_create.json)。bridge、shm120gb、无GPU请求；5个挂载与PROCEDURE一致。容器`forem-t6-husky-gz`保留。

source melodic与新副本devel后，`import ray; import modulation.myray.ray_utils; import pybindings_robots`成功，绑定路径`/forem_build/ws_husky/devel/lib/python3/dist-packages/pybindings_robots.cpython-37m-x86_64-linux-gnu.so`；无需重新构建，尚未做Gazebo依赖构建。记录[devel_launch_preflight.json](../../../../results/task6/t6.2-env-r1/devel_launch_preflight.json)。

`roslaunch --files modulation_rl n2m2_husky_empty_world.launch gui:=false world_name:=empty.world`首次因husky_control缺失退出1。按§2.6仅把快照husky_control/pcl_configure/robotiq_85_moveit_config复制到build/task6.2/deps/gazebo_snapshot，并添加已复制UR1.5.0的ur5_moveit_config包路径；第二次缺ur5_moveit_config退出1，第三次XML枚举退出0。全部未启动ROS/Gazebo，未将枚举当就绪。新增依赖路径、来源SHA见[additional_dependency_manifest.json](../../../../results/task6/t6.2-env-r1/additional_dependency_manifest.json)，原ws_husky未改。

`timeout 55 apt-get update`退出0（但ROS bionic索引连接失败，日志apt-update.log）；`apt-get -s install ros-melodic-husky-control ros-melodic-diff-drive-controller ros-melodic-teleop-twist-joy`退出100，无法定位包。**未安装任何apt包，未修改apt源，未构建新增依赖。**

实际入口（完整shell/错误见[launcher_execution.json](../../../../results/task6/t6.2-env-r1/launcher_execution.json)）：

```sh
/opt/conda/bin/python -u modulation/handle_launchfiles.py --env husky_ur5 --pure_analytical no --bioik --algo rl --task simpleobstacle
```

容器执行设置K=0私有ROS12400/Gazebo12500/IGN分区、独立HOME/ROS_HOME/ROS_LOG_DIR；未传--gui。**退出2：invalid choice husky_ur5；有效choices仅pr2/tiago/hsr，gazebo_cmds也无Husky。** 指定入口与现有代码不一致；不自行修改handle_launchfiles、不把直接roslaunch静态解析当入口已通过。按“未覆盖且超出允许范围”停下交Claude。未运行launch_ros。

## §3–§7 尚未执行

没有worker映射、隔离回归、冒烟/profile/N决策、正式训练、训练中评估或最终评估；无100万步成功/失败结果可报。不能改review/done。

## 当前交接与监控

- 目标/授权不变；Codex按异常处理停止，Claude决定是否采用直接原版launch及其参数/依赖方式，或另行授权启动器适配。模型/世界/控制器/env未改。
- 已完成：§1、新容器/完整副本、绑定导入、启动静态预检、指定入口失败证据；未完成：§2就绪及§3–7。
- 容器最终`docker top`只sleep infinity（主机PID750976；[final_own_top.json](../../../../results/task6/t6.2-env-r1/final_own_top.json)）；无本任务ROS/Gazebo/训练长任务。不存在需停止的训练或实例。没有停止任何容器/外来进程。
- 监控：`sg docker -c 'docker top forem-t6-husky-gz -eo pid,ppid,stat,args'`，日志[launcher.log](../../../../logs/task6/t6.2-env-r1/launcher.log)。如用户要求停止本任务容器，`sg docker -c 'docker stop forem-t6-husky-gz'`；当前按交付要求保留，恢复须Claude决策后新记录，不能自动重训。
- 风险：Gazebo依赖的可执行文件/插件/控制器尚未构建或运行核验；未证明N20可行。Task5退出条件仍未满足。不能以本次失败推断B在Gazebo不能学习。

阶段证据manifest已写：[manifest.json](../../../../results/task6/t6.2-env-r1/manifest.json)，明确blocked/§2/无正式训练；不是§7正式交付manifest。


## Claude审核 R1（2026-10-12）

- §1与§2已完成部分审核通过；补充的三个快照包和`ur5_moveit_config`路径接受，须列入manifest。
- 阻塞原因是Claude在PROCEDURE中写错了启动器路径。决策见[TASK G-D5/G-D6](TASK.md#claude审核r1决策2026-10-12g-d5启动入口g-d6安全性能优化)：改用`gazebo_world/husky_ur5/handle_launchfiles.py`原样启动（PROCEDURE §2.4、§3.1a已修订）；性能优化只做G-D6一类。[SRC-0232](../../../SOURCES.md#src-0232)
- 放行：用新run-id `t6.2-env-r2`重做§2.4–§2.5（r1记录保留），通过后继续§3、§4。§5仍须等task5 A/B训练退出。

## 2026-10-12T09:48:46.148987+08:00 R1继续执行

Codex按G-D5/G-D6接手t6.2-env-r2；r1记录保留，§1–2.3沿已接受结果，不重新复制/建容器。新就绪尚未通过。

## t6.2-env-r2 §2.4/§3.1a前置核查 — 2026-10-12T09:55:23.315525+08:00

[SRC-0234](../../../SOURCES.md#src-0234)。已重读R1/G-D5/G-D6、PROCEDURE与SRC0232；正确启动器与只读参考SHA相同。r1保留，§1–2.3不重复；没有修改原ws_husky。

### 依赖实际准备

- 独立`gazebo_deps_ws`原样构建快照pcl_configure：系统PATH、melodic，`catkin build pcl_configure -j2 -p1`退出0，23.2s；[日志](../../../../logs/task6/t6.2-env-r2/dependency-build.log)与`dependency-build.exit`。
- 镜像缺ROS控制器运行包。固定官方源：[new_dependency_sources.json](../../../../results/task6/t6.2-env-r2/new_dependency_sources.json)，含URL/tag/commit/全部SHA及工程选择理由：ros_control0.18.4、ros_controllers0.17.3、gazebo_ros_pkgs2.8.7、teleop_twist_joy0.1.3；只在build/task6.2/deps及独立依赖ws引用缺包。没有插件/控制器源码改动，没有改任何运行参数。ros_control/gazebo版本分别对齐镜像现有controller_interface/gazebo_ros；其余为固定ROS1依赖选择，并非Task5 Gazebo实测版本。
- 首次ros_controllers0.18.2不存在（clone退出128），ls-remote后取实际存在0.17.3；其余clone成功，无源码patch。ROS官方仓库HTTPS探针因证书主机名不匹配退出60；未关闭验证或改apt源，使用官方Git源码。
- `catkin build -j2 -p1 --no-status`第一轮退出1（缺controller_manager测试依赖）；补同ros_control版本controller_manager及msgs后第二轮退出0，12/12，实际时长见[build-r2日志](../../../../logs/task6/t6.2-env-r2/controller-dependency-build-r2.log)和[完整命令/退出收据](../../../../results/task6/t6.2-env-r2/controller-dependency-build-r2.json)。该依赖构建在端口阻塞发现前已启动，等其自然结束，没有启动新的实验步骤。

### 端口实际结果

探针由系统python3包装系统roscore，去掉conda PATH为`/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`，source melodic。私有HOME/ROS_HOME/ROS_LOG_DIR，ROS_MASTER_URI12400/ROS_IP127.0.0.1。完整命令见两份`roscore-*-probe.json`。

|条件|11311 TCP/getUri|12400 TCP/getUri|结果|
|---|---|---|---|
|普通roscore|监听，URI11311|未监听，connection refused|忽略实例URI端口|
|先roscore -p12400，再普通roscore|监听，URI11311|监听，URI12400|普通core未退出，另开默认master|

原始[端口收据](../../../../results/task6/t6.2-env-r2/roscore_precore_probe.json)、[core日志](../../../../logs/task6/t6.2-env-r2/precore-probe/roscore.log)显示`WARNING: ROS_MASTER_URI port [12400] does not match this roscore [11311]`及`auto-starting new master`。两个探针自建进程组均SIGINT退出0，未接触其他容器/进程。

该行为不符合§3.1a“自带roscore会因端口已占用而退出”的预期，按“未覆盖且超出允许范围”停止，交Claude明确额外默认master处理方式。不自行拦截core、修改启动器或改变隔离约定。**正确启动器尚未实际运行，Gazebo/move_group/costmap未启动；reset/50步就绪无结果。** 原启动器0.002/500与膨胀参数未执行，不写成已验证值。

§3 worker映射/隔离、§4冒烟/profile/N20/G-D6优化及§5–7均未执行。没有策略训练失败可报。Task5退出与CPU预算门槛不变。Codex停止实施交Claude决策；容器按要求保留。实际模型/强度仍精确未知，推荐GPT6.1sol/Sonnet5.5 medium。

最终核验：依赖build-r2退出0，12/12，95.4s；ws_husky与r1副本哈希不变。容器仅sleep infinity，无core/构建/仿真/训练残留，保留供Claude审核。监控`sg docker -c 'docker top forem-t6-husky-gz -eo pid,ppid,stat,args'`；停止仅限自有容器`docker stop forem-t6-husky-gz`（当前不执行）。[r2阶段manifest](../../../../results/task6/t6.2-env-r2/manifest.json)含命令/源版本/哈希/接受的依赖路径；不是正式训练交付manifest。


## Claude审核 R2（2026-10-12）

- r2端口探针与依赖构建审核通过：普通roscore另开11311的实测成立，按异常处理停下正确；控制器依赖从官方源码固定版本构建、无源码改动，接受（G-D8），须列入manifest。
- 决策见[TASK G-D7/G-D8](TASK.md#claude审核r2决策2026-10-12g-d7实例roscoreg-d8控制器依赖)：用包装脚本先`roscore -p (12400+K)`，再原样导入启动器调用`start_launch_files("husky_ur5","rl","simpleobstacle",False)`；就绪核查须确认不存在11311的master。[SRC-0235](../../../SOURCES.md#src-0235)
- 放行：用`t6.2-env-r3`做§2.4–§2.5单实例就绪（r1、r2保留），通过后继续§3、§4。§5条件不变。

## 2026-10-12T10:51:20.058557+08:00 R2接手r3

按用户放行G-D7/G-D8，r3重做§2.4–5；r1/r2证据保留，§1/副本/容器/已构建依赖沿用。正确启动器未改；就绪尚未通过。

## t6.2-env-r3 实际启动、reset结果与交接 — 2026-10-12T11:01:09.597997+08:00

[SRC-0236](../../../SOURCES.md#src-0236)。G-D7包装已写`build/task6.2/scripts/t62_launch.py`，系统/usr/bin/python执行Popen-p12400、sleep5、原模块start_launch_files；[逐行对照](../../../../results/task6/t6.2-env-r3/launcher_main_diff.json) / [diff](../../../../results/task6/t6.2-env-r3/launcher_main.diff)。原启动器没有改，原函数负责costmap/30秒等待/物理参数。

### 首次运行接线失败（证据保留）

本Agent写的`t62_system_env.sh`先source依赖后sourcehusky，后者移除了依赖CMAKE_PREFIX_PATH，虽然lib已建仍找不到pcl/teleop可执行及DefaultRobotHWSim。记录[inst0-attempt1/launch.log](../../../../logs/task6/t6.2-env-r3/inst0-attempt1/launch.log)、`inst0.attempt1.json`与cleanup。修正本任务包装前缀（加依赖devel），只清理自有启动实例再检查；未改插件、控制器、模型或世界。

原launch仍固定请求缺失的marker_server与原gripper mimic库。按§2.6补官方interactive_marker_twist_server1.2.1及原快照roboticsgroup_gazebo_plugins，无源码patch，`catkin build interactive_marker_twist_server roboticsgroup_gazebo_plugins -j2 -p1 --no-status`退出0，15.9s（2/2）。完整URL/tag/commit/文件SHA与G-D8已接受四库见[dependency_manifest.json](../../../../results/task6/t6.2-env-r3/dependency_manifest.json)，G-D8运行栈差异/障碍几何差异仍披露，不称完全单因素。

### 第二次启动核查通过（不代替完整§2.5）

[start收据](../../../../results/task6/t6.2-env-r3/start-inst0-attempt2.json)、[实例/环境](../../../../results/task6/t6.2-env-r3/inst0.json)、[启动日志](../../../../logs/task6/t6.2-env-r3/inst0/launch.log)、[health](../../../../results/task6/t6.2-env-r3/health-inst0.json)。原wrapper正常结束后ROS/Gazebo子进程仍被本任务唯一环境marker识别。

- `/gazebo`、`/move_group`、两costmap的URI/PID与进程环境均指向12400；容器内11311 XMLRPC getUri失败。
- 实测physics time_step0.002、max_update_rate500、pause false；costmap膨胀enabled false/radius0/radius0。
- 五必要控制器running；joint_group_eff_controller仅initialized（原停用合同）。
- 底盘控制器速度话题有1个订阅，发0.2m/s、wall2s后停零，实际XY位移0.40083444156123405m；仅控制器就绪检查，不是物理成功评估。

### 环境reset随机步探针未通过

第一次probe因本Agent脚本不在模块目录（没有导入cwd）报ModuleNotFoundError并退出1，尚未创建env；保留`env-reset-step-probe.json/.log`，仅补probe sys.path后第二次执行。原env源码未动。parse_args会创建logs目录，因此只把副本scripts/logs软链由原t5.2路径改指/forem_results/t6.2-env-r3，避免任何Task5路径写入；所有代码哈希不变，[diff](../../../../results/task6/t6.2-env-r3/source_diff_vs_task5.json)。

|trial|reset wall秒|随机动作步数|结果|
|---|---|---|---|
|0|13.059493269771338|50|完成|
|1|20.583092346787453|50|完成|
|2|失败；未返回有效obs|0|内置10次retry耗尽，退出1|

100步每步墙钟均值0.015526116872206331s，所有逐步时延/动作/奖励/observation有限性在[env_readiness.json](../../../../results/task6/t6.2-env-r3/env_readiness.json)，不是完整训练profile/N预算证明。第2轮日志连续The arm_client_ failed/resetArm failed，最终`Reached 9 reset attempts, exception: Could not set start pose after 50 trials!!!`。此外Gazebo日志出现两次`Joints on incoming goal don't match the controller joints`。**尚未把该错误映射到具体action/goal，未证明根因。** 只读源码RobotHusky::getArmSuccess/sendArmCommands与combined_env::reset，没有改变它们。

更正本轮早期聊天阶段判断：异常发生在第3轮，不是第1轮；以原始step/reset完整记录为准。内置retry是原env行为，未增加外部重试。探针自然退出1且env_closed true；不是被中止的成功结果。

### 停止与交接

按用户“控制器行为异常停下”及PROCEDURE异常处理停止§3/§4/§5，不改关节名、PID、轨迹、reset、训练器/任务语义。只清理自有inst0（匹配环境marker+PID start ticks；`inst0.cleanup.json`）和只读TF探针（核对12400环境/完整argv，`tf_probe_cleanup.json`）。最终容器仅sleep infinity，[final_own_top.json](../../../../results/task6/t6.2-env-r3/final_own_top.json)；容器保留供Claude复核，无长训/仿真/采集残留。

当前负责人Codex停止实施→Claude决策。已完成G-D7启动接线、实例master/physics/controller/底盘响应核查；未完成§2.5三次reset×50。§3映射/隔离、§4profile/N20/G-D6优化、§5训练、§6评估、§7正式汇总均未执行。Task5退出/N20资源门槛不变。不能将本次失败当Gazebo策略性能结论。

[r3阶段manifest](../../../../results/task6/t6.2-env-r3/manifest.json)含digest/依赖URL-tag-commit/原源码diff/实例/命令/退出/SHA；私有HOME/ROS_HOME运行缓存未纳入SHA，ROS日志/launch/probe原证据已纳入。尚无正式训练manifest，状态blocked，非review/done。监控`sg docker -c 'docker top forem-t6-husky-gz -eo pid,ppid,stat,args'`；只可停止本任务容器（当前保留）：`sg docker -c 'docker stop forem-t6-husky-gz'`。实际模型/强度精确未知，推荐GPT6.1sol/Sonnet5.5 medium。


## t6.2-env-r4 reset失败根因诊断（Claude子Agent，2026-10-12 15:02–15:35）

执行者：Claude子Agent（claude-sonnet-5-5，推理强度未知），临时代替Codex；[日志](../../../agent_logs/task6/task6.2/20261012-claude-task6.2.md)；[SRC-0237](../../../SOURCES.md#src-0237)。**只做诊断探针，未改env代码、控制器参数、关节名、PID、轨迹容差、模型、世界、launch、启动器、训练参数；未做§3及以后。**产物：[results/task6/t6.2-env-r4](../../../../results/task6/t6.2-env-r4/)（含[diagnosis_summary.json](../../../../results/task6/t6.2-env-r4/diagnosis_summary.json)）、[logs/task6/t6.2-env-r4](../../../../logs/task6/t6.2-env-r4/)；脚本`build/task6.2/scripts/t62_{arm_probe,pan_probe,set_dt,reset_stats,dt002_repeat,dump_param,versions,chatter_summary_an,diag_summary}.*`。

### 结论（已证实 / 推测分开）

**已证实（实测）**

1. 失败不在接线：G-D7实例、master隔离、控制器running、底盘响应都正常（r3已证）；r4用同一包装脚本重启，现象相同。URDF中**全部链接**`turnGravityOff true`（底盘、轮、臂、夹爪），所以不是重力载荷；臂静止时各关节力矩为0。
2. 单goal探针（dt=0.002，复制`sendArmCommands`的形态：6关节、单点、4 s）：控制器轨迹本身在运动阶段跟随良好（前约3 s误差≤0.004 rad），**轨迹末端/停止后shoulder_pan进入±150 N·m的符号逐步翻转颤振**（125 Hz的/joint_states里pan、lift力矩99–100%样本达150 N·m限幅，速度峰值3.2–3.9 rad/s，位置在目标上下摆动且均值偏离0.08–0.13 rad）。第一次goal的结果`error_code −5 GOAL_TOLERANCE_VIOLATED`；颤振已在场时再发goal，则在**0.102 s sim**内`error_code −4 PATH_TOLERANCE_VIOLATED`（pan误差>0.1 rad的路径容差）被中止。
3. 机理链（对应原代码）：`setJointValuesFromDict`里每次`sendArmCommandCurrent(4.0)`→`getArmSuccess()`因goal被立即中止而立刻返回→`checkArmValues()`发现pan与目标差0.10–0.13 rad（阈值0.1）→重试10次只消耗约1 s sim（不够4 s到达），→抛“Could not set start pose after 50 trials”；`combined_env.reset`外层再试9次共约100次内层都失败。注意：被中止的goal对应的轨迹**仍在控制器内继续执行**，（pan-goal1.json中goal在0.1 s被中止后，臂仍按轨迹在约4 s内到达目标）所以偶尔后几次内层重试会因臂已移到位而通过——这应是r3前两次reset“成功”的原因（推测，r3未记录逐goal结果）。
4. 受控单因素对照（同一实例、同一代码和同一控制器参数，仅用`/gazebo/set_physics_properties`改步长，流程与原`gazebo_set_pyhsics_properties`相同）：

|步长（max_update_rate）|env.reset()调用|最终成功|inner `resetArm failed`行|备注|
|---|---|---|---|---|
|0.002（500，原启动器设定）|6次（4次独立创建env）|2|420（pan 400）|4次最终失败，均“Reached 9 reset attempts”|
|0.001（1000，Gazebo默认）|12+3|15/15|0|3×50随机步：reset 11.1/17.7/17.9 s，步均墙钟15.5 ms，步均仿真15.0 ms（与r3 dt0.002的15.5 ms相同）|
|0.0005（2000）|12|12/12|0|reset墙钟约21–23 s|

   dt=0.001时pan仍100%样本饱和但速度峰值约1.5 rad/s、摆幅约0.01 rad（< 0.1 rad容差），lift不再饱和；故0.001“可用”不是“无颤振”。
5. 每次reset一次的`Joints on incoming goal don't match the controller joints`来自**夹爪**goal（`openGripper`的关节名gripper_finger1_finger_joint/finger2_finger_joint ≠ `/gripper_controller/joints=[gripper_finger1_joint]`），与臂reset失败无关，0.001下也有，属上游代码的既有怪癖（原代码注释还写“THE GRIPPER WILL FAIL TO OPEN / CLOSE WITH THIS STEP SIZE”）。每次reset一次的`The arm_client_ failed`在0.001下也有，因为`success=checkArmValues()`才是判据，`getArmSuccess()`的结果被忽略。
6. 环境版本（只读）：Gazebo `9.0.0+dfsg5-3ubuntu1+ppa2`；镜像自带hardware_interface/controller_interface 0.18.4、control_toolbox 1.18.2、gazebo_ros 2.8.7；controller_manager、joint_trajectory_controller、effort_controllers、gazebo_ros_control来自Codex按G-D8源码构建（ros_controllers 0.17.3）。

**推测（未证实）**

- 颤振机理：折叠臂姿态（lift −1.57、wrist_1 −1.57）下pan的等效惯量很小。以符号逐步翻转的±150 N·m估算I≈F·dt/(2|v|)≈0.047（dt 0.002）/0.053（dt 0.001）kg·m²；对离散PD的D项经验判据D·dt/I<2（pan D=200）给出dt约<0.0005 s。与上表方向一致，但这是估算，未用URDF惯量核算，未做改增益对照（约束不允许）。
- 为什么原作者在0.002下能用：未知。候选：Gazebo小版本、ros_controllers/control_toolbox版本、他们没有遇到（或者靠reset重试吞下）。**待补证据**。Task3在`config/task3/world.yaml`选用了0.0005 s/2000 Hz/world求解器，并因另一原因（重力全开不稳）把臂链接设为无重力（[SRC-0059](../../../SOURCES.md#src-0059)）。

### 为什么停下

唯一已验证的最小修复是把Gazebo物理步长从0.002 s改为0.001 s（或更小），这违反[G-D6](TASK.md)中“禁止改Gazebo物理步长0.002、max_update_rate 500”，且偏离“只改world_type”的单因素口径，需要Claude决定。我没有在包装脚本或启动器里应用它，也没有跑§2.5的“正式”重做（r4实例已按`t62_instance.py stop`身份清理，容器仅sleep）。

### 供Claude选择的最小修复候选（我的建议，非授权）

- **A（推荐，证据最强）**：在G-D7包装脚本里于`start_launch_files(...)`返回后，再按同一服务序列把步长设为0.001 s / max_update_rate 1000（或0.0005/2000），其余不动。须在manifest和对照限制中披露“Gazebo步长0.001≠Task5/原启动器0.002”；注意它同时让G-B更接近Task3/Task4.8（0.0005）而不是原作者设定。已测：reset 15/15成功、步时延不变；**未测**：训练规模下的整体吞吐、20+1实例的CPU占用、实时因子。代价：CPU/物理步数翻倍（0.001）或翻四倍（0.0005），§4 profile要重做。
- B：先验证“Gazebo小版本”假设再决定（只读风险较大，需新装/升级gazebo9，OSRF仓库容器内可达；会改变镜像运行栈，我未做）。
- C：改PID（pan D增益）或轨迹容差——违反约束，不建议。
- D：接受reset失败并保留原样——不可行，worker会因AssertionError崩溃（dt=0.002下最终失败率约4/6）。

### 清理与状态

自有实例K=0（run `t6.2-env-r4`）已用`t62_instance.py stop`清理（`inst0.cleanup.json`，after=[]）；`docker top forem-t6-husky-gz`仅`sleep infinity`（PID 750976）；无本任务训练/仿真/后台进程。Task5、forem-dev、forem-t5-*均未触碰。`ws_husky`副本源码不变（`modulation/utils.py` sha256与Task5相同a2d851e7…；只把`scripts/logs`软链改指`/forem_results/t6.2-env-r4`以落产物）。r4目录属主已改回ybc。§3–§7均未执行。


## Claude审核 R3（2026-10-12）

- r4诊断审核通过：根因定位与单因素步长对照证据充分，未改禁止项，按异常处理停下正确。补加SRC-0237缺失的锚点。
- 决策见[TASK G-D9](TASK.md#claude审核r3决策2026-10-12g-d9物理步长)：物理步长改为0.0005 s／`max_update_rate` 2000（与Task3/Task4.8世界一致），由G-D7包装脚本在`start_launch_files()`之后按原服务序列设置；G-D6对应禁止项改为“固定0.0005/2000”。[SRC-0238](../../../SOURCES.md#src-0238)
- 放行：用`t6.2-env-r5`重做§2.5（3次reset×50步，加≥10次reset统计，记录pan/lift复位后力矩饱和比例与摆幅），通过后继续§3、§4；§4须核对20+1实例下实时因子与每步仿真时长。§5条件不变。

## t6.2-env-r5 §2.5单实例就绪（G-D9 0.0005 s／2000 Hz，Claude子Agent，2026-10-12 15:3x）

[SRC-0238](../../../SOURCES.md#src-0238)。通过。`t62_launch.py`在`start_launch_files()`之后用**原函数**`gazebo_set_pyhsics_properties(time_step=0.0005)`（新python进程，服务序列get→pause→set→unpause，`max_update_rate=int(1/0.0005)=2000`，重力和ODE配置取自当前值）；启动器文件不变（sha256 38c50bcc…，与Task5副本一致）；对照diff：[launcher_main.diff](../../../../results/task6/t6.2-env-r5/launcher_main.diff)。汇总：[readiness_summary.json](../../../../results/task6/t6.2-env-r5/readiness_summary.json)。

- 实测physics：time_step 0.0005、max_update_rate 2000、重力[0,0,−9.8]；costmap膨胀false/0/0；节点/gazebo/move_group/costmap均在12400 master；11311 master不存在；五控制器running（joint_group_eff_controller initialized，原停用合同）。底盘0.2 m/s、墙钟2 s位移0.346 m（RTF<1所致，仅控制器响应检查）。
- §2.5：env创建后reset 3次×50随机步全部完成（reset 13.9/20.1/20.7 s，步墙钟均值17.4 ms、中位16.4 ms）；另做12次reset统计（每次10步）：12/12成功，inner `resetArm failed`与outer `Reset k failed`均为0；reset墙钟约21 s、仿真约7.7 s。
- 复位后保持3 s墙钟窗口：shoulder_pan力矩饱和比例在12次中全部为1.0，位置摆幅0.0007–0.037 rad（均<0.1容差）；shoulder_lift饱和比例0、摆幅约0.0003 rad。**即0.0005 s下pan仍有颤振（力矩饱和），只是幅度被限制在容差内；披露，不处理。**
- Gazebo日志`Joints on incoming goal don't match`共15行（夹爪goal关节名不匹配，上游既有，每次reset一次，不处理）。
- 单实例步仿真时长：中位约0.0131 s/步（各reset均值0.0112–0.0205），墙钟约0.0165 s/步，即单实例RTF约0.8（Task3在forem-dev测得0.72–0.88同量级）；此为§4与20+1实例对照的单实例参考，宿主当时load average 10–18（task5/6.1同时运行），§4须在相同条件下重测。
- 实例已按身份清理（`inst0.cleanup.json`after=[]），容器仅sleep。产物属主已改回ybc。脚本：`t62_launch.py`（G-D9）、`t62_health.py`（断言改为0.0005/2000）、`t62_reset_stats.py`（加复位后保持窗口）、`t62_r5_run.sh`。

## §3 多实例隔离实现与回归（`t6.2-iso-r1` 未过自设阈值；`t6.2-iso-r2` 通过）

[SRC-0240](../../../SOURCES.md#src-0240)。**worker→实例映射**只在副本`modulation/utils.py`加`_t62_bind_instance()`并在`env_creator`首行调用；未设`T62_ROS_PORT_BASE`时为空操作（sim与其他用法不变）。训练worker_index i（node_handle `train_env`，1…N）→实例K=i−1，评估worker（`eval_env`）→K=N；设置`ROS_MASTER_URI=…:12400+K`、`GAZEBO_MASTER_URI=…:12500+K`、`IGN_PARTITION=t62_inst<K>`、`ROS_IP/GAZEBO_IP/IGN_IP=127.0.0.1`、独立`ROS_HOME/ROS_LOG_DIR`；断言进程中rospy尚未初始化，且同进程二次绑定必须同一K；每次绑定追加`worker_map.jsonl`。依据Ray 1.6.0源码（`rollout_worker.py` L396–400）：driver本地worker（worker_index 0且num_workers>0）不创建训练env，评估worker集合同理，所以只有远程worker创建env；实际是否如此在§4冒烟中用`worker_map.jsonl`核对。**driver**：`main_ray.py`在`ray.init`前执行`rospy.init_node('kinematic_feasibility_py')`，需要一个master——driver的`ROS_MASTER_URI`设为评估实例（K=N）的master，不创建11311。源码diff：[source_diff_vs_task5.json](../../../../results/task6/t6.2-baseline/source_diff_vs_task5.json)（ws_husky/src下仅`utils.py`与`scripts/logs`软链不同，含utils.py的unified diff）。

回归脚本`build/task6.2/scripts/t62_iso_regress.py`（含`t62_query.py`、`t62_iso_env.py`）。

- `t6.2-iso-r1`（[isolation.json](../../../../results/task6/t6.2-iso-r1/isolation.json)）：11/12项通过，`A_moved_B_not`未过：A位移0.852 m，B位移1.04 mm，而我预设的阈值是B<1 mm。原因：health检查刚刚驱动过两个底盘，B仍在滑行/漂移。保留此结果，不删。
- `t6.2-iso-r2`（[isolation.json](../../../../results/task6/t6.2-iso-r2/isolation.json)，退出0，12/12通过）：新增“等待20 s、测B空闲8 s漂移”，判据在跑r2前写明为`dB ≤ max(1 mm, 2×空闲漂移)`；实测B空闲8 s漂移1.26 mm（**此底盘在无重力下自身会缓慢漂移**），A驱动期间B位移1.17 mm（在空闲漂移范围内），A位移0.857 m。其余项：两实例节点URI集合不相交、都含/gazebo、/move_group；两master不同；A上`rosparam set`在B中不可见；启动两实例后11311无master；用真实`env_creator`+RLlib `EnvContext`验证映射——调用方环境里故意把ROS_MASTER_URI设成“错误”的实例，`train_env`（worker 1）仍绑定K=0(12400)，`eval_env`仍绑定K=1(12401)，各自节点列表只含自己的env节点，env创建前rospy均未初始化；停止A后A的端口12400/12500关闭，B的控制器仍running、`get_model_state`成功；结束时残留端口为空，两个实例按身份清理。
- 限制：回归只覆盖2个实例（与Task4.8.1相同）；K>2的隔离由§4冒烟/20+1运行间接检验。


## §4 冒烟、profile、确定N（`t6.2-smoke-r1`、`t6.2-bench-r1/r2`；停在§4.3）

[SRC-0241](../../../SOURCES.md#src-0241)。执行者：Claude子Agent（claude-sonnet-5-5）。训练命令由`build/task6.2/scripts/t62_train.sh`生成，与`launch.json`相同，仅加`--world_type gazebo`、`--num_workers N`（冒烟另加`--total_steps 5000 --evaluation_frequency 2500 --nr_evaluations 2`）；driver节点`rospy.init_node('kinematic_feasibility_py')`连到评估实例的master（不用11311）。

### 冒烟（N=2训练+1评估实例，[smoke_summary.json](../../../../results/task6/t6.2-smoke-r1/smoke_summary.json)）
- 退出码0，5004步，墙钟1917 s（含ray/实例启动后的训练），checkpoint_000005已保存；W&B离线；无CUDA错误。
- worker映射（[worker_map.jsonl](../../../../logs/task6/t6.2-smoke-r1/worker_map.jsonl)）：worker1→K0(12400)、worker2→K1(12401)、评估worker→K2(12402)，共3条；driver没有建env，与Ray 1.6.0源码分析一致。事后用同一映射在K0上建env并reset，Gazebo里有18个模型（16障碍），说明训练env在自己的实例里生成场景。
- 评估：result.json中出现1次评估结果（第3次迭代，2个episode，success_mean 0.0，episode_len_mean 512，随机初始策略）；评估env在K2。第二次评估的结果在训练结束前没有出现在结果文件里（评估间隔2500、`timesteps_per_iteration`1000），未核查具体原因。
- 吞吐：5个迭代耗时420/328/362/403/371 s，整体2.66步/s（2个训练worker，约1.3步/s·worker）；每迭代18/13/15/17/15个episode，平均episode长度约62步；每episode的reset墙钟约21 s（仿真约8 s）；规划器每步`dt`约0.34 s（仿真时间）。

### profile
- learner：`learn_time_ms`≈415–436 ms/次（batch 256，CPU），每1000环境步约111次更新（`num_steps_trained`/256）→约48 s/1000步；采样段约280–350 s/1000步（N=2）。**N=2时采样受限**；按线性外推N=20时采样约32 s + learn 48 s，**转为learner受限**（RLlib 1.6的store/replay在driver中轮转，采样与更新不重叠）。B在sim中17步/s即59 s/1000步，其中learn同量级，所以B本来也主要是learner受限。该外推未实测（不能在20个worker下实测，见下）。
- 每实例CPU（[bench_summary.json r1](../../../../results/task6/t6.2-bench-r1/bench_summary.json)、[r2](../../../../results/task6/t6.2-bench-r2/bench_summary.json)、冒烟cpu.jsonl）：实例树（gzserver约1.7–1.8核＋约20个ROS辅助进程约1.1核）训练中位约2.75–2.8核；环境驱动并发时3.0–3.2核。**21个实例仅实例树就需约58–67核**，尚未计worker（每个约0.2–0.3核）、driver/learner、task5后处理与task6.1。
- 单实例实时因子：空闲RTF 0.645（仿真时间/墙钟，宿主busy约24核时）；单步仿真时长中位0.0150 s、步墙钟中位17.2 ms。即使单实例，0.0005 s步长下Gazebo已跑不到实时（≈0.65）。
- 9实例并发（K0–K8，宿主busy约49核，含task5后处理与task6.1）：空闲RTF中位0.629（范围0.597–0.732）；单步仿真时长中位0.0108 s（范围0.0100–0.0115）、步墙钟中位16.6 ms。与单实例相比：空闲RTF中位−2.5%，但实例间离散±16%；单步仿真时长−28%（宿主负载也不同：24→49核，非同条件）。**按G-D9的“偏差≤5%”判据，9实例就已不满足**；21实例未跑（CPU会超56核，并挤占优先级更高的task5后处理和task6.1 F0）。
- 重要发现（影响“性能优化是否科学中性”）：Gazebo模式下`EEPlannerFullPython.dt = rospy.get_time() − …`（`robotenv.py`的`rate.sleep`被注释掉），规划器每步时间取决于两次env.step之间的**仿真时钟间隔**，即worker策略推理、Ray采样、learner占用driver等造成的延迟。自由跑的探针每步仅0.015 s，训练中约0.34 s。所以限制线程数、绑核等会改变每步dt，不是舍入级差异；**我没有应用任何G-D6优化**，仅报告该风险，由Claude决定。
- 其他G-D6候选（未实施）：learner线程数（learner是N=20时的瓶颈，需单独实测，不改变env语义）、实例CPU亲和（不降低总核数需求，对实时因子离散可能有帮助）、W&B离线低频（已是离线）。

### N的确定（停止）
- 按PROCEDURE §4.3：实例树合计≈58–67核已超过56核门槛，且未计其余进程与外部负载 → **N=20不满足**，停下。
- 可行N粗估（实例树3.1核＋worker 0.3核＝约3.4核/实例，learner/driver约3核，56核总预算）：外部负载15核时N≈10，外部负载0时N≈15；N=20在任何外部负载下都超出。这是线性外推，未在对应N实测。
- 100万步墙钟粗估（假设每worker 1.56步/s（由N=2推得）、learn 48 s/1000步、采样与更新不重叠）：N=10约30 h，N=20约21 h，**另加评估**：评估episode约500步×0.45 s＋reset 21 s≈4 min，50个episode约3.4 h/次，13次评估（每7.5万步）最坏约44 h，是否阻塞训练迭代未测。不是承诺。
- 未启动§5。task5 B训练进程已退出（exit_code 0），但其后处理评估仍在运行，task6.1 F0也在forem-dev运行；这两项都比本任务优先。

### 清理
实例均按身份清理（`t62_multi.py stop`均退出0），容器仅`sleep infinity`；ray已随训练结束；`ws_husky`副本中`scripts/logs`软链指向最后一次bench目录；Task5/forem-dev/forem-t5-*未触碰。


## Claude审核 R4（2026-10-12，待用户决定）

- §2（r5）、§3（iso-r2）、§4冒烟审核通过；补加SRC-0240、SRC-0241缺失的锚点。§5未启动，处理正确。
- **关键问题（核实成立）**：Gazebo模式下每步的规划时长取实际流逝的仿真时间（`eeplanner.py` L162–176，`robotenv.py` L243–247的`rate.sleep`被注释，单步上限裁到0.5 s），而sim固定为0.1 s（`TIME_STEP_TRAIN`）。实测：G-B冒烟每步约0.34 s；Task4.8每步约0.04 s（`logs/task4/t4s-plain-s*/progress.jsonl`的`sim_interval_s`中位0.037–0.040 s，RTF约0.43–0.53）。因此Gazebo中的步长语义随吞吐、N和CPU负载变化，G-B若原样运行，结果会混入“时间步长不同”这个因素，且N、线程、绑核都会改变科学条件。
- Claude建议（尚未授权，需用户同意）：G-B每步固定推进0.1 s仿真时间（暂停/恢复物理，仿照Task4.8已有的`scwm_clock.FixedWindowClock`），使步长语义与sim一致，N和CPU负载只影响墙钟。此为新增机制，按根AGENTS须用户同意后才写入流程。
- 在用户决定前：§5不启动，task6.2保持blocked。
- **用户决定（2026-10-12 17:0x）**：同意固定每步0.1 s（G-D10）、N=10（G-D11）。见[TASK“Claude审核R4决策”](TASK.md#claude审核r4决策2026-10-12用户已同意g-d10每步固定01-sg-d11-n10)、[SRC-0242](../../../SOURCES.md#src-0242)。task6.2解除blocked，实现G-D10后重做冒烟与profile，再启动§5。


## G-D10实现与验证（`t6.2-fw-r1…r8`；Claude子Agent，运行17:1x–17:4x，21:1x按文件核对补记）

[SRC-0244](../../../SOURCES.md#src-0244)，逐运行数据[fw_runs_summary.json](../../../../results/task6/t6.2-fw-summary/fw_runs_summary.json)。代码：副本`modulation/utils.py::_t62_fixed_window`，`env_creator`在`create_env`之后调用；`T62_FIXED_WINDOW_S`未设置时为空操作；与Task5的源码差异仍只有`utils.py`与`scripts/logs`软链。

|运行|机制|结果|
|---|---|---|
|fw-r1|pause/unpause|失败：测试脚本在env进程内订阅latched costmap，env的OccupancyGridManager拿不到数据；改为独立监控进程。保留|
|fw-r2|pause/unpause（持久服务）|可运行，但规划器dt长尾：非首步中位0.108、p95 0.313、最大0.822；首步dt 0.25/0.15/0.69|
|fw-r3|脱离env的pause窗口诊断|300窗口：窗口后仿真时间中位0.1010、p95 0.105、最大0.1445 s（pause调用中位1.2 ms）|
|fw-r4|pause/unpause＋逐窗口拆分|pause调用墙钟中位5.8 ms、p95 0.44 s、最大1.5 s；规划器dt中位0.105、最大1.245|
|fw-r5|同上，非持久服务连接|pause调用中位24 ms、p95 0.31 s、最大2.3 s；dt中位0.116、最大1.87；未改善|
|fw-r6|脱离env的`gz world -m 200`诊断|200窗口全为0.10000 s；墙钟中位0.353 s|
|fw-r7|env内multistep|规划器dt恒0.1000（n=176）、首步dt 0.1000；costmap监控进程因import错误未工作（`OccupancyGridUpdate`应从`map_msgs`导入），保留|
|fw-r8|env内multistep＋前进指令＋costmap监控|dt恒0.1000（n=192），首步0.1000；前进指令25步底盘位移0.267 m、臂关节最大变化1.75 rad；costmap步末滞后中位17.5 ms、最大37.5 ms；步墙钟中位0.52 s|

结论与偏离（须Claude复核）：G-D10文字规定用`/gazebo/pause_physics`＋`unpause`＋`/clock`。在本机栈中该方案在env运行时无法满足“dt最大≤0.12 s”（pause服务调用有长尾，原因未定位，脱离env时正常）。因此改用`gz world -m <n>`（Gazebo自己执行n=0.1/0.0005=200次迭代后保持暂停；仍不改步长、max_update_rate，未用unthrottle）；reset后用ROS pause再把规划器`_rostime_at_start`设为第一窗口起点，使首步dt也等于0.1。代价：每步墙钟约0.52 s（`gz`进程启动＋暂停下逐步推进，约1.75 ms/迭代）。pause方案仍可用`T62_WINDOW_MODE=pause`选择。观测落后一个窗口的结构不变。


## 补记：额度中断后的核对（2026-10-13 10:1x）、持久helper、N=2冒烟、N=10+1 profile

[SRC-0245](../../../SOURCES.md#src-0245)。执行者：Claude子Agent（claude-sonnet-5-5）。以下均按文件核对，不凭记忆。

**孤儿实例（事实）**：`t6.2-prof-r1`的11个Gazebo实例因额度中断在prof结束后留下空转，约11小时44分（2026-10-12 22:45–10-13 10:08）；脚本当时没有清理步骤。10-13 10:09用`t62_multi.py stop t6.2-prof-r1 10`按环境marker＋PID启动时间逐个停止，11份`inst*.cleanup.json`的after均为空；容器只剩`sleep infinity`，端口12400–12410、12500–12510、11311均关闭。其他容器未碰。

**G-D10实现方式的变化（须Claude复核）**：见上节fw-r1…r8。`gz world -m`子进程在gzserver中泄漏fd（`t6.2-smoke-r2`：训练退出码1，worker2的实例gzserver fd=1007/1024，`default.log`有`Too many open files`，评估实例82）。改为持久helper：
- 源码：`forem/build/task6.2/src_helper/t62_gzstep.cc`（约30行）；编译：`g++ -std=c++11 t62_gzstep.cc -o /forem_build/bin/t62_gzstep $(pkg-config --cflags --libs gazebo)`（容器内，退出0）；产物`forem/build/task6.2/bin/t62_gzstep`。
- 作用：一个长期运行的gz transport发布者，从stdin读`step N`，向`~/world_control`发布`multi_step=N`，Gazebo自己执行N次迭代并保持暂停。每个env一个helper进程，env关闭时发`quit`，父进程消失时stdin EOF自动退出。
- 不改变受限项：不改物理步长/max_update_rate/求解器、env代码、规划器、控制器、奖励、观测、终止；只是替代pause/unpause服务来推进固定窗口。副本`utils.py`新增`_t62_fixed_window`、`T62_WORKER_THREADS`钩子（默认不启用）。已写入`source_diff_vs_task5.json`的added_components。

**运行记录**

|run|内容|退出码与结论|
|---|---|---|
|t6.2-smoke-r2|N=2+1，multistep用`gz`子进程|1；fd泄漏导致一个实例失效，1000步684 s|
|t6.2-fw-r9|脱离env，1500个helper窗口|0；窗口恒0.10000 s，墙钟中位0.106 s，gzserver fd 81→80|
|t6.2-fw-r10|env内helper|0；规划器dt（非首步）n=229恒0.1000，首步0.1000，步墙钟中位0.1325 s，前进指令底盘位移0.269 m、臂关节最大变化2.0 rad，costmap步末滞后中位6 ms/最大26 ms|
|**t6.2-smoke-r3**|**N=2+1，5004步，评估频率2500×2episode，T62_FIXED_WINDOW_S=0.1**|**0，通过**：2148 s，checkpoint_000005，W&B离线，无CUDA提及；映射worker1→K0、worker2→K1、eval→K2；5250条规划器dt打印全为0.100；评估结果1次（2 episode，success 0，episode_len_mean 123）；窗口超出量约1e-14 s；gzserver fd 83–84|
|t6.2-prof-r1a|N=10+1，4000步，默认线程|1；第4次迭代时worker6（K=5）在reset后第7步卡死（/clock 120 s不推进），前3次迭代：291/363/377 s|
|t6.2-prof-r1b|同上，T62_WORKER_THREADS=1|0；4000步，迭代280/381/410/379 s。Ray默认已把worker的torch线程设为1（worker_map中`torch_threads: 1`），故a/b无差别，线程优化无收益，不采用|
|t6.2-prof-r2|N=10+1，监督脚本首次使用，含重试逻辑|1；约3分钟内某worker卡死（重试后仍120 s不推进）；监督脚本在训练退出后自动清理，remaining=[]|
|t6.2-prof-r3|N=10+1，4000步，监督脚本，含卡死诊断|0；1461 s，迭代265/402/393/367 s，整体2.80步/s；窗口超出量最大2.3e-14 s，重试0次；dt打印4000条全为0.100；CPU宿主平均13.9核、p95 22.8、最大52.6（含task6.1），实例树合计平均8.0核；每次学习0.417–0.444 s|

**吞吐结论**：N=10的整体吞吐（2.8步/s）与N=2（2.37步/s）几乎相同，不随worker数线性增长。原因（源码＋测量推断）：RLlib 1.6 SAC执行计划为`ParallelRollouts(mode="bulk_sync")`，每轮每个worker一步，任一worker处于约21 s的Gazebo reset时其余worker都在等待。按2.8步/s，100万步约99 h；训练中评估开销另计，未实测其是否阻塞训练迭代。CPU不是瓶颈。N=20也不会明显提高吞吐（同一屏障）。

**间歇卡死（未解决）**：N=10运行中观察到约每1小时一次worker的/clock不再推进（prof-r1a、prof-r2；N=2的smoke-r2是fd泄漏，已修复）。prof-r3之后加了卡死时的诊断记录（`window_*.stalls.jsonl`）和重试，但只有在真实卡死时才会产生记录。

### 间歇卡死的定位与修复（t6.2-stress-r1/r2/r3，2026-10-13 10:4x–11:3x）

问题：N=10运行里worker在某次窗口命令后/clock不再推进，120 s后抛`simulation clock did not advance`（prof-r1a、prof-r2）。为复现，写了独立的压力驱动（`t62_stress_env.py`，10个env各占一个实例，只做随机动作的episode循环，reset密度约为训练的9倍，卡死时保留实例600–900 s）。
- `t6.2-stress-r1`：约5分钟内复现；诊断记录（`window_*.stalls.jsonl`）显示：该实例**世界处于paused=true、helper进程存活、ROS服务可答复、`step 200`被反复发送但/clock完全不动**。随后手工用新的`gz world -m 100`客户端对同一实例发命令，时钟立即前进0.05 s。结论（已证实）：实例本身没坏，是长期运行的helper的gz-transport发布连接在某个时刻悄悄不再送达消息（`Publish`仍返回）；具体触发条件未查明（可能与reset期间模型删除/生成有关，未验证）。
- 修复：卡死3 s（`T62_WINDOW_STALL_S`）无时钟进展就杀掉并重启helper，按时钟计算剩余迭代数再发命令，并记录诊断与重试次数。`t6.2-stress-r2`暴露我的实现缺陷（循环里仍用旧helper的句柄，BrokenPipe），已修正。
- `t6.2-stress-r3`（修正后）：10个驱动，前约14分钟约1.7万步、约290个episode、6次卡死事件，全部由重启helper恢复，没有驱动失败，窗口超出量仍≈1e-14 s。
- 影响：每次卡死约多花3–5 s；N=10压力下约每200个窗口1次，100万步训练预计数千次，合计约数小时量级，已计入墙钟估算的不确定度，不改变科学条件（重发只补足被丢失的迭代数，窗口仍恒0.1000 s）。若重启后仍不推进，120 s后仍抛错，由监督脚本清理并退出。
- 副产物：`ray::`僵尸进程（容器PID 1是`sleep infinity`，不回收孤儿）会累积，不占CPU/内存；监督脚本清理的是实例与训练进程组。

## §5 正式训练 `t6.2-gz-train-s40`（运行中；2026-10-13 11:23启动）

状态：**active（运行中）**。启动者：Claude子Agent（claude-sonnet-5-5），按R4第4点（G-D9/G-D10/G-D11）。[SRC-0245](../../../SOURCES.md#src-0245)。

- 启动条件核对：task5 B训练与后处理已结束；G-D10验收（规划器dt恒0.1000、N=2与N=10每步仿真时长均0.1000，首步dt 0.1000，指令在暂停下被执行，costmap滞后中位6 ms）；smoke-r3与prof-r3通过；CPU：prof-r3宿主平均13.9核、最大52.6核（含task6.1 F0），实例树平均8核；启动时宿主负载约3核（task6.1的F0已结束）。
- 命令（[train_command.txt](../../../../results/task6/t6.2-gz-train-s40/train_command.txt)、[launch.json](../../../../results/task6/t6.2-gz-train-s40/launch.json)）：`/opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 10 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env husky_ur5 --total_steps 1000000 --world_type gazebo`，相对B只有`--num_workers 10`（G-D11）、`--world_type gazebo`；环境`T62_FIXED_WINDOW_S=0.1`、W&B离线。配置对照[effective_config_diff_vs_task5_params.json](../../../../results/task6/t6.2-gz-train-s40/effective_config_diff_vs_task5_params.json)：除`init_controllers`、`world_type`、`num_workers`外，仅`device`记录为cpu（B记录为cuda：B的容器可见GPU；两边`num_gpus 0`，learner都在CPU上）。
- 监督与停止：`build/task6.2/scripts/t62_run.sh`（setsid nohup于容器内）。训练进程退出（正常、崩溃）或监督进程收到TERM时，自动停止训练进程组、CPU采样器和本run全部11个实例（环境marker＋PID启动时间校验），并写`cleanup_remaining.txt`核对无遗留。**手动停止**：`sg docker -c 'docker exec forem-t6-husky-gz kill -TERM $(cat /forem_results/t6.2-gz-train-s40/supervisor.pid)'`（supervisor.pid=462341；已用N=2压力运行验证该路径，清理后无遗留）。上游不支持续训：崩溃后保留证据，不自动重训。
- 监控：`python3 build/task6.2/scripts/t62_status.py t6.2-gz-train-s40`（进度、实例/helper存活数、卡死事件、窗口重试、规划器dt、错误计数）；原始日志`logs/task6/t6.2-gz-train-s40/{train.log,supervisor.log,window_*.jsonl,*.stalls.jsonl,worker_map.jsonl}`，CPU 5 s采样`results/task6/t6.2-gz-train-s40/cpu_5s.jsonl`，训练曲线`results/task6/t6.2-gz-train-s40/ray/.../progress.csv`。
- 启动后健康检查（11:23–11:40）：worker映射10个训练worker→K0–K9、评估worker→K10；11个gzserver与11个helper存活；已完成2次迭代（1000步296 s，2000步724 s）；规划器dt打印共约2000条全为0.100；窗口重试0；train.log无错误；1次卡死诊断记录（由压力运行之外的训练内事件，已由helper重启恢复，训练继续）。**首个训练中评估要在75000步时触发（按2.8步/s约7–8 h后），启动时尚无法验证；评估env已创建在K10，N=2冒烟中评估已执行过一次。**
- 预计：2.8步/s（N=10屏障限制，见上）→100万步约100 h，另加评估开销（50个episode/次，13次，是否阻塞训练迭代未测）。**这比R4决策时的30 h估计长约3倍，原因是RLlib的bulk_sync屏障与Gazebo reset（约21 s）相互作用，增加worker几乎不提高吞吐（N=2 2.4步/s，N=10 2.8步/s）。如果这个时长不可接受，需要Claude/用户决定（例如停止训练、改变采样配置——超出task6.2“只改world_type”的口径）。**


## Claude审核 R5（2026-10-13 11:4x）

- **正式训练核实**：11:39 `t62_status.py`：2次迭代、2000步、724 s；11个gzserver与11个helper存活、main_ray 1个；规划器dt打印2550条全为0.100；窗口超出量约1e-14 s；train.log无错误；helper卡死事件1次已恢复。主机负载约8核。
- **G-D10实现偏离，接受**：
  - 用常驻C++ helper `t62_gzstep`发送`WorldControl.multi_step`（Gazebo自身执行200次0.0005 s迭代后保持暂停），替代pause/unpause服务。理由：服务方案在env运行时延迟长尾使dt达0.82–1.87 s，`gz world -m`子进程方案泄漏fd。物理步长、`max_update_rate`、env、规划器、控制器均不变，仿真时间只在窗口内推进，比服务方案更精确。
  - reset后把规划器对象的`_rostime_at_start`重置为第一个窗口起点，使首步dt为0.1 s。只改运行时对象状态，不改规划器代码，符合G-D10“首步也为0.1 s”的要求。
  - helper静默失效时3 s无进展自动重启并按时钟补足剩余迭代。卡死只影响墙钟，不改变仿真时间语义；卡死次数须作为监控指标持续记录。
  - 原G-D10验收的“pause/unpause”写法以本实现为准；验收数值（dt中位0.1、最大≤0.12）已满足。
- **吞吐**：约2.3–2.8步/s，几乎不随N增长。原因是RLlib 1.6 SAC的bulk_sync采样，任一worker reset（约21 s）时其余worker等待。100万步约100–120小时，是R4估计的3倍多。改采样方式会改变B的训练器口径，不做。
- **Claude建议（待用户决定）**：训练继续运行，不改设置。在训练中评估到15万步（约15 h）和30万步（约30 h）时读数；R-B在15万、30万步已分别为0.52、0.66，30万步足以判断“B配方在Gazebo中能否学会”。到30万步时再决定是否继续到100万步。
- **用户决定（2026-10-13 14:2x）**：“先跑30w”。执行方式：上游不支持续训，故训练不在30万步处停止，继续运行；Claude在30万步训练中评估出结果后读数，由用户决定是否跑满100万步或用监督脚本停止。


## 2026-10-13 Codex接回：监控与30万步决策交接

接手时间2026-10-13T14:48:23.768691+08:00；当前负责人Codex，Claude继续负责决策、流程及复核。仅监控既有训练，无配置/代码改动、无重训或续训。实际模型/强度未知；推荐GPT6.1sol/Sonnet5.5，监控low/默认、评估时序核对medium。[日志](../../../agent_logs/task6/task6.2/20261013-codex-task6.2.md) · [SRC-0247](../../../SOURCES.md#src-0247)。本节优先于上方历史交接。

现场32次迭代/32000步，训练计时11922 s，累计约2.684步/s（32000÷11922，仅训练开始后累计墙钟）；11实例/11helper/main_ray/监督器存活，dt打印全0.100，窗口超出量最大2.273e-14 s，卡死累计1次已恢复，train.log匹配错误0。监督器容器PID462341/宿主PID3056653。CPU最新5s样本约14.02核，仅瞬时采样。旧stress-r2 CPU采样器另存活，未触碰。

### 训练中评估对照（持续填写）

来源R-B `results/task5/t5.2-train-s40/train_eval_series.csv`；G-B本run `ray/*/*/progress.csv` 的evaluation字段，待实际输出后填写。episode_len_mean位于`evaluation/episode_len_mean`，其余四项位于`evaluation/custom_metrics`，不混用训练custom_metrics。

|步数|组|success_mean|goal_reached_mean|ik_fails_mean|base_collisions_mean|episode_len_mean|完成episode|
|---|---|---|---|---|---|---|---|
|75000|R-B（sim）|0.06|0.12|17.76|0.4|85.18|50|
|75000|G-B（Gazebo）|0.04|0.1|18.62|0.0|70.72|50（Claude R7从result.json读取）|
|150000|R-B（sim）|0.52|0.66|6.78|2.08|248.78|50|
|150000|G-B（Gazebo）|0.04|0.08|18.96|0.0|78.64|50（Claude R8从result.json读取）|
|225000|R-B（sim）|0.68|0.7|4.9|0.46|266.74|50|
|225000|G-B（Gazebo）|0.02|0.04|19.38|—|—|50（Claude 2026-10-14从result.json读取）|
|300000|R-B（sim）|0.66|0.66|5.6|0.0|259.08|50|
|300000|G-B（Gazebo）|待出结果|待出结果|待出结果|待出结果|待出结果|待核验|

首次7.5万评估：尚未执行/核验；届时对应worker_map的eval_env PID469661/K10，核查实际窗口活动、50个完成episode（episodes_this_iter/hist_stats/result日志）、迭代74/75/76墙钟并记录评估是否延长训练迭代。配置“并行评估”不能代替运行时证据。

下一步：持续监控，至少每30分钟登记步数/吞吐、实例/helper/监督器、stalls、窗口超出量、错误计数和CPU。达到30万步评估结果后写完本表、报告用户/Claude并结束本会话工作，训练继续；不标done。崩溃仅核验监督器自动清理收据并报告，不重训；频繁卡死或持续低吞吐按用户阈值记录报告，不改机制。


## Claude审核 R6（2026-10-13 15:0x，Codex接回）

- **通过**：接手登记、现场核查（11实例/11 helper/main_ray/监督器存活，worker_map K0–9训练、K10评估，dt全0.100）属实；Claude 14:54复核：33000步、约2.69步/s、0错误。R-B对照列（7.5万0.06、15万0.52、22.5万0.68、30万0.66）与`train_eval_series.csv`一致。7.5万步评估的核查计划（K10执行、50个episode、是否阻塞迭代）合理。
- **问题1（须整改）**：持续监控进程宿主PID 3232689以`python3 -u -`从标准输入运行，源码没有落盘，无法审计和复现；按其自述还会自动写RESULTS并登记SOURCES。要求：
  1. 把监控源码保存到`forem/build/task6.2/scripts/`（文件名注明codex_monitor），日志里记录sha256与启动命令；能不中断现有监控就补存同一份源码并说明，否则用落盘版本重启监控（只重启监控，不碰训练）。
  2. 监控脚本只写自己的快照文件（jsonl）和本日志；task6.2 RESULTS的评估读数与SOURCES条目由Codex核验后人工写入，不由脚本自动写。SOURCES是共享文件，task5的Codex会话也在写。
  3. 写明该监控依赖Codex工具会话存活；会话结束时监控随之停止，训练不受影响。
- **问题2（待用户决定）**：容器`forem-t6-husky-gz`中仍有Claude子Agent在`t6.2-stress-r2`留下的CPU采样器（宿主PID 2994901，`t62_cpu_sample.py t6.2-stress-r2 1000000 5`，已运行约4小时，CPU约0%），会持续写`results/task6/t6.2-stress-r2/cpu_5s.jsonl`。它不属于本run，Codex未处理是正确的。是否停止由用户决定。

## Codex落实Claude R6监控整改 — 2026-10-13T15:01:35.821845+08:00

旧stdin监控PID3232689经cmdline/父进程/启动ticks核验，仅SIGTERM该监控退出；训练监督器3056653及main_ray3064108前后PID/start_ticks相同。落盘源码[ t62_codex_monitor.py](../../../../build/task6.2/scripts/t62_codex_monitor.py)，SHA256 `64c87c1acd6d0cda6c4daee963e3c078e378a30b4924b2415bfabe2cd4eb9935`；命令`python3 -u /home/ybc/projects/CL-FoReM/forem/build/task6.2/scripts/t62_codex_monitor.py`，新PID3260562/工具session20851。

py_compile、AST写入/信号审计、真实--once退出0，核查写入仅codex_monitor_snapshots.jsonl和Agent日志；**脚本不读写本RESULTS或SOURCES。** 评估候选必须Codex人工核验完成数、K10执行与相邻迭代后再写本表/共享来源；没有新评估，不填读数。[重启收据](../../../../results/task6/t6.2-gz-train-s40/codex_monitor_restart.json)与[日志](../../../agent_logs/task6/task6.2/20261013-codex-task6.2.md)。

**监控依赖Codex工具会话存活，会话结束时监控停止，训练不受影响。** PR_SET_PDEATHSIG=SIGTERM处理工具父进程退出；没有后台独立daemon或nohup监控，也不调用训练停止命令。本次不触碰stress-r2遗留CPU采样器。既有训练仍active，原30万步评估交接/用户决策合同不变。


## Claude审核 R7（2026-10-14 00:3x，只读）

- **7.5万步评估已完成**：迭代75（2026-10-13 19:24+08:00）evaluation：success 0.04、goal_reached 0.10、ik_fails 18.62、base_collisions 0.0、episode_len 70.72、50个episode。同步数R-B（sim）为0.06/0.12/17.76/0.4/85.18，两者接近（早期，单次50 episode）。
- **读数位置更正**：`progress.csv`没有evaluation列——Tune的CSV logger表头在第一次写入时固定，之后才出现的evaluation字段不会写入。评估结果须从同目录`result.json`读取（每行一个迭代的完整结果）。上方“训练中评估对照”中“读progress.csv的evaluation字段”的说明以本条为准。
- **评估worker（K10，PID 469661）的状态**：19:23后K10仿真时间停在25799.48 s、物理暂停、进程睡眠，这是两次评估之间的正常空闲（G-D10下仿真只在env发出窗口时推进），不是卡死。只读核查：`get_world_properties`间隔20 s两次读数相同，K0同期前进1.1 s；RLlib 1.6 `trainer_template.py` L203–207在评估迭代内`eval_future.result()`阻塞，训练已越过迭代75说明该次评估已返回。
- 注意：K10 `launch.log`在评估期间反复出现“Joints on incoming goal don't match the controller joints”和`arm_client failed`，未阻止评估完成；15万步评估时继续观察。
- 下一次评估在迭代150（15万步），按约2.7步/s约在00:3x后2–3 h。


## Claude审核 R8（2026-10-14 08:3x，只读）

- **15万步评估**（迭代150，2026-10-14 03:07+08:00，result.json）：success 0.04、goal_reached 0.08、ik_fails 18.96、base_collisions 0.0、episode_len 78.64，50 episode。R-B（sim）同步数为0.52/0.66/6.78/2.08/248.78。
- 7.5万→15万步G-B没有提高（0.04→0.04，IK失败均值不降），而R-B从0.06升到0.52。与Task4.8（ScwmSAC，Gazebo）在Gazebo中学不会的现象一致。单种子、单次50 episode，30万步读数后再下结论。
- 现场08:2x：20.5万步，11实例/helper存活，dt全0.100，卡死30次均恢复，train.log匹配错误2条（未展开，Codex监控时核对）。按约2.7步/s，30万步约在10小时后。


## 用户要求停止（2026-10-14 14:55+08:00，Claude执行）

- 用户明确指令：“task6.2 G-B这个停下吧不要这个”。执行者：Claude（会话“世界模型与强化学习文献”，claude-opus-5-5）。
- 操作：核对`/forem_results/t6.2-gz-train-s40/supervisor.pid`=462341（容器内）对应`bash /forem_build/scripts/t62_run.sh t6.2-gz-train-s40 10 --total_steps 1000000`，运行1天3小时32分；按本文件“监督与停止”节的手动停止方法执行`docker exec forem-t6-husky-gz kill -TERM 462341`，rc0。
- 结果：supervisor.log `2026-10-14T06:55:57Z cleanup start`→`stopped 11 bad 0`→`06:56:16Z cleanup done; remaining marker processes: []`；`cleanup_remaining.txt`为空。容器`docker top`剩`sleep infinity`和此前遗留的`t62_cpu_sample.py t6.2-stress-r2`（不属本run，未触碰）；容器内若干`[t62_gzstep] <defunct>`僵尸为历史残留，无资源占用，未处理。
- 训练停止位置：`progress.csv`最后一行迭代269、`timesteps_total`=269000；已存checkpoint为`checkpoint_000100`、`checkpoint_000200`（同目录`ray/.../SACTrainerCustom_modulation_rl_env_8c458_00000_0_2026-10-13_03-24-07/`），产物原样保留。
- 已有训练中评估（result.json，各50 episode）：7.5万0.04、15万0.04、22.5万0.02（R-B sim同步数0.06/0.52/0.68）。**30万步评估未执行；单种子、未完成训练，不作为G-B最终结论。**
- 未改源码/配置；未启动任何新run。task6.2后续是否恢复须用户另行明确指令。

## 2026-10-20 停止stress-r2遗留CPU采样器（Claude，用户指示）

- 用户原话：“核实那个t6.2采样进程确实是遗留、无人使用后，只停掉这一个进程，并记录在task6.2 RESULTS。”对应上文“问题2（待用户决定）”。
- 核实：宿主PID 2994901＝容器`forem-t6-husky-gz`内PID 415730，命令`t62_cpu_sample.py t6.2-stress-r2 1000000 5 /forem_results/t6.2-stress-r2/cpu_5s.jsonl`，已运行约7天；父进程已是容器init `sleep infinity`，原启动者不在；容器内无其他进程，宿主无引用，task6.2为paused；输出中最后一条含实例数据的样本为2026-10-13T10:57:13，之后全为空样本。
- 操作：2026-10-20 13:20 `docker exec forem-t6-husky-gz kill -TERM 415730`，rc=0。进程退出，宿主显示为`<defunct>`僵尸（容器init不回收，不占资源，清除需重启容器，本次不做）。
- 结果：`results/task6/t6.2-stress-r2/cpu_5s.jsonl`停止增长（12,921,302字节，122,553行，最后一条2026-10-20T13:20:09，SHA256 `73de0039…24b4`），保留未删；容器仍运行，只剩`sleep infinity`。task6.2状态不变（paused）。
- 记录：[日志](../../../agent_logs/task6/task6.2/20261020-claude-stop-stress-r2-sampler.md)。

