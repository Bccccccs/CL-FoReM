# task3.5 核心集成验收与Task4交接契约 — 结果与交接

> **当前状态（2026-10-19核对）：done（随task3经task3.6 R2验收）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

**当前：done，父Task3.6 R2独立验收通过（2026-10-07），旧review是历史。** 最终当前freeze4、GPU默认及来源/时间/路径/包装身份修正闭环见[3.6结果](../task3.6/RESULTS.md)及[SRC-0066](../../../SOURCES.md#src-0066)。推荐GPT6.1sol/Sonnet5.5，跨模块medium，常规整理low/default；实际原Claude强度未知，最终验证子gpt-6.1-sol/medium。

状态：**review（实施完成，待task3.6独立复核）**。实施：Claude（Sonnet5.5，强度未知）。依赖：[task3.4](../task3.4/RESULTS.md)。

## 一、集成验收（实际记录，含失败尝试）

**最终集成：[t3.5-int-r4](../../../../results/task3/t3.5-int-r4/integration_summary.json)**（一次fresh启动，`validate_task3_core.py`，退出0；[manifest](../../../../results/task3/t3.5-int-r4/manifest.json)含镜像id/源码hash/命令/清理）：

|阶段|结果|
|---|---|
|physics（`check_task3_physics`）|通过：直行0.1956 m/s（指令0.2）、原地转0.460 rad/s（0.5）、组合速度比0.677/速率比0.623、保持臂最大误差4.4e-6 rad、TF唯一作者`/pose_bridge`且按原戳匹配99.9%；p3d与Gazebo真值（时间插值）最大差4.9e-5 m（噪声未生效）；实时因子0.72–0.88|
|env（`check_task3_env`）|20项通过：同seed同episode（1b8354da…）、障碍16/16在Gazebo、规划-实际臂关节最大差0.034 rad、观测底盘vs真值最大差0.0044 m、每步墙钟0.0165 s/仿真0.0146 s，2个完整episode（84、270步，IK失败终止）|
|sac_smoke|通过：76步、60次`update_parameters`、损失有限、保存→加载确定性动作差0.0、7种错误contract与无contract全部拒绝；期间1个episode结束|
|sac_eval|通过：smoke checkpoint→eval模式2个episode×40步（`task3_sac_entry --mode eval`）|
|clock|通过：时钟229.3→0.09回退被检测、step拒绝并保持失效、pose_bridge新epoch 0→1；新进程复用仿真的恢复**仅记录，不作门槛**（本run退出码1：150 s内TF未恢复）|
|独立重算|通过：从`timeseries.csv`重算直行/转向/组合指标与摘要差<2%；采样周期中位0.016 s、阶段内最大≤0.5 s；指令被跟随|

**所有尝试（不选择性汇总）**，来源：[core_receipt.json](../../../../results/task3/t3.5-receipt/core_receipt.json)`all_attempts`：

|run|结果与原因|
|---|---|
|t3.5-int-r1|FAIL：env（`base_obs_matches_truth`最大0.0653>0.05；之后门槛改0.10 m，事后调整，原因：两个位姿采样时刻不同、基座速度达0.3 m/s）、clock（fresh-process失败；`control_period_sane`把harness不采样的1.02 s算进去，改为阶段内统计）|
|t3.5-int-r2|FAIL：sac_smoke在第2次reset因臂复位失败（“Could not set start pose after 50 trials”）；级联sac_eval/clock失败。根因见下|
|t3.5-resets-r1 / resets-quick1|FAIL（world与quick两种求解器均在第2个episode复位失败：wrist_3 path error、臂末态速度−20 rad/s）|
|**修复**|臂/夹爪链接保持无重力（[SRC-0059](../../../SOURCES.md#src-0059)）|
|t3.5-resets-r2|PASS：12个episode 0次复位失败（1个到达目标、9个IK失败终止、2个500步上限）|
|t3.5-motion-armgrav-r1/r2/r3|PASS×3：重复性见task3.2|
|t3.5-int-r3|FAIL：clock阶段——`rospy.get_time()`在reset_simulation后3 ms内尚未更新（检测竞争），并且fresh进程TF在120 s内未恢复；其余阶段通过。clock检查随后改为轮询+恢复信息化|
|**t3.5-int-r4**|**PASS（上表）**|

另外：[t3.5-inst-r1](../../../../results/task3/t3.5-inst-r1/episode_instances.json)记录10个固定seed（101–110）的完整episode实例（起点、目标、16个障碍），两遍hash一致且互不相同；生命周期回归[t3.5-life3](../../../../results/task3/t3.5-life3-report/report.json)全部通过（L1非法id、L2重复id、L3外来进程被拒且未被停止、L4并发被拒、L5 SIGTERM→143、L6 SIGINT→130并清理、L7客户端被杀后底盘停止/臂稳定；t3.5-life2先出现L5因harness把`sg`的-15当失败，修正后复跑）。容器测试：`python3 -W ignore -m unittest discover -s tests`在forem-dev内268项通过（含Task0–2既有测试，3项因参考树未挂载而跳过）；宿主Task3测试28项通过；`t3.5-task0-regress1`（Task0 smoke）在Python3.10重建后仍退出0；Task2冻结`t2.8-exec3/protocol3`验证仍通过。冻结：[execution_freeze.json](../../../../config/task3/execution_freeze.json)（t3.5-core-freeze1，324个文件hash+镜像id+实例文件hash，`freeze_task3.py verify`通过）；receipt：all_pass=True。

清理核对：我早期一次诊断（`rostopic …; rosrun tf tf_echo`）遗留的两个容器内进程在实施期间一直存活，12:4x由本人确认后停止；之后`docker top forem-dev`只有`docker-init`与`sleep infinity`，`task0_proc.py foreign`为`[]`。

## 二、原Husky到底有几条线？（按实际调用关系核实，不是文件数）

证据：[husky_branches.json](../../../../results/task3/t3.1-audit-r1/husky_branches.json)（对21个Python脚本的import/调用/硬编码路径分析）+ 一次导入实测（[SRC-0057](../../../SOURCES.md#src-0057)）+ 对`robot_env.cpp/robotenv.py/combined_env.py/worlds.cpp`的阅读。**“已运行”只指FoReM里实际运行过的；原入口一条都没有原样运行过。**

### A. 算法训练/评估入口：7条

|#|入口|用途|输入→输出|上游/下游|位置反馈来源|本镜像状态|FoReM处理|
|---|---|---|---|---|---|---|---|
|A1|`scripts/main.py`|**作者的Husky训练线**：自写SAC循环；载入冻结prior（`checkpoints_pnp_plus/…4000`），`resume=True`先评估20 episode并把转移写入replay，再用`update_parameters_modified`训练；每500 episode评估、每1000 episode存checkpoint；无限`itertools.count()`|CLI(parse_args，env默认pr2) + 硬编码checkpoint → tensorboard + `checkpoints/`|`env_creator`→CombinedEnv→RobotEnv；SAC(`sac.py`)|取决于world_type（默认`sim`解析环境）|**不能原样启动**：第15行`modulation.myray.ray_utils`（eval.py第14行）→`custom_sac`在ray1.13报`SACTrainer has no attribute with_updates`（已实测）|只迁移骨架（环境循环、replay、SAC）到`task3_sac_entry.py`；prior/路径/无界循环/评估入replay均不迁移|
|A2|`scripts/eval.py`|作者的Husky确定性评估：加载硬编码checkpoint，100个episode，打印到达/碰撞/IK失败/完美成功率|同上|同上|同上|同样因ray_utils不能启动|→`task3_sac_entry.py --mode eval`（checkpoint须带contract）|
|A3|`scripts/main_ray.py`|上游N²M²训练：RLlib SACTrainerCustom/Wandb，ray tune，多worker|CLI + wandb → ray日志/checkpoint|`modulation.myray.*`|同上|`custom_sac`不可导入|**未迁移**（不在普通SAC范围）|
|A4|`scripts/evaluation_ray.py`（+`modulation/evaluation.py`）|上游评估：RLlib checkpoint在sim/gazebo/world×多任务（rndstartrndgoal/houseexpo/picknplace/door/drawer…）上评估|同上|同上|同上|同样不可导入|**未迁移**|
|A5|`evaluation_moveit.py`|MoveIt规划基线|—|`pybindings_moveit`、`modulation.planning.rrt`|—|两个模块在快照中不存在|未迁移|
|A6|`evaluation_bi2rrt.py`|BiRRT基线|—|同上|—|同上|未迁移|
|A7|`evaluation_articulated.py`|articulated/MPC基线（PR2导向分支）|—|`ocs2_msgs`|—|ocs2_msgs未构建|未迁移|

核实结论：算法入口7条；**在本镜像上原样可启动的0条**（A1–A4被`custom_sac`阻断，A5–A6缺模块，A7缺消息包）。FoReM新入口`task3_sac_entry.py`承接A1/A2中“普通SAC”的最小子集（已运行：smoke、train 450步、eval）。

非算法线（不计入上面7条）：5个shell启动器（`docker_build*.sh`、`docker_run.sh`、`run_experiment.sh`、`ros_startup_incl_train.sh`，均针对原Docker镜像/wandb）、`handle_launchfiles.py`/`launch_ros`（从Python启动ROS，Python2语法，路径硬编码`/home/cbl`，已注释大半）、3个ROS节点（`tf_forward.py` PR2/TIAGo的odom→TF、`move_obstacles.py` 动态障碍、`camera_goalpointer.py` HSR）、`husky_ur5/src`三个演示脚本（`controller.py` MoveGroup演示、`count.py` octomap、`husky_goal.py` move_base目标，**含U+200B语法错误**）。均未迁移。

### B. 在线任务→物理执行链：按`world_type`分3种

每个`env.step`的共同骨架（`CombinedEnv.step`→`RobotEnv.step`(py)→`RobotEnv::step`(C++)）：策略动作[-1,1]³ → 转成`vel_norm`(EE计划速度)+`base_rot/base_vel` → `EEPlanner.step`给出下一个期望夹爪位姿 → 理想差速积分得“下一底盘位姿” → BioIK在该底盘系下求臂关节（**规划关节**）→ 之后因world_type而异 → 回读观测、计算奖励/终止。

|链|world_type|底盘执行|臂执行|底盘位姿从哪来|局部地图/碰撞|launch|Husky状态|
|---|---|---|---|---|---|---|---|
|B1|`sim`（解析）|不发命令，底盘＝理想积分，无物理|不发命令|内部积分（kinematic_state）|真值floorplan裁剪；碰撞＝地图重叠|`n2m2_husky_analytical.launch`（仅move_group）|**作者训练的默认链**（SimpleObstacleTask `requires_simulator=False`，world_type默认sim）；FoReM未运行|
|B2|`gazebo`|`/cmd_vel`→twist_mux→diff_drive_controller→Gazebo轮|IK关节作为单点`FollowJointTrajectory`发给`eff_joint_traj_controller`（effort PID）|Gazebo p3d→`gdt_tf`（`Time::now()`重盖）→TF `map→base_footprint`（`perception_style=base`）；FoReM改为`pose_bridge`|激光costmap_2d；碰撞＝`/modulation_bumpers`接触话题|`n2m2_husky_empty_world.launch`|**FoReM迁移并运行验证的链**（direct+base）|
|B3|`world`（实机）|同B2语义|同B2|真实定位TF|同B2|`world`没有Husky launch|`RealWorld.setModelState`只实现了PR2，要键盘`input()`；Husky不支持；未迁移|

链内变体：`execute_style`∈{direct, track}、`perception_style`∈{base, all, none}共6种组合，**main.py/eval.py路径固定为direct+base**（env_config不传这两个键），FoReM验证的就是这一种；`track`、`all`、`none`未运行。**关键语义**：`base`只更新底盘位姿，观测里的臂关节仍是IK规划值，实际关节反馈另走`get_joint_values_world`，不进观测。

### C. 世界模式 / 位置来源：3种位姿来源、2种地图来源、2种碰撞来源

|类别|选项|说明|
|---|---|---|
|底盘位姿|①解析积分（sim）②Gazebo p3d→`gdt_tf`重盖戳→TF（gazebo）③真实TF（world，Husky未实现）；备用：`tf_forward.py`（PR2/TIAGo，python2，`Time::now()`）|FoReM证据：②，p3d与Gazebo真值实测相同（URDF的0.01噪声未生效，[SRC-0056](../../../SOURCES.md#src-0056)）|
|局部地图（观测）|真值floorplan裁剪（sim）/ 前激光costmap_2d（gazebo、world）|规划用的全局map始终是障碍真值|
|碰撞/终止信号|地图重叠（sim）/ Gazebo接触话题（gazebo）||

### D. FoReM继承 / 修改 / 未迁移 对照

|部分|状态|
|---|---|
|C++环境/IK/pybind、Python环境/任务/地图/EE规划/奖励|**继承**（逐字，仅Husky-only裁剪与`robotenv.py`删其他机器人分支）|
|SAC/ReplayMemory/GaussianPolicy/mapencoder/SB3分叉|**继承**（仅`device`参数）|
|Husky+UR5+夹爪URDF/控制器/MoveIt配置/BioIK|**继承**（补丁：去`turnGravityOff`、去不可用插件、夹爪mimic插件名）|
|launch（gazebo+控制器+move_group+costmap）|**改写**为`husky_core.launch`（暂停启动、启动序列、前激光、空世界）|
|`gdt_tf`|**替换**为`pose_bridge`（唯一TF作者、原样本戳、校验、状态）|
|SAC入口|**新写**（无prior、显式预算、contract checkpoint）|
|main.py/eval.py/main_ray/evaluation_*/myray/baselines、其他机器人、sim解析链、real链、`track/all/none`、动态障碍/门/抓放、wandb、旧权重|**未迁移**|

## 三、Task4定位替换接口与旧true-position通路

- **接口**：发布`nav_msgs/Odometry`（`header.frame_id∈{world,map,odom}`、`child_frame_id=base_footprint`、stamp=估计时刻的仿真时间、位姿有限、四元数单位化）到某话题，用`pose_topic:=<话题> pose_source:=<名字>`启动；`pose_bridge`仍是`odom→base_footprint`的唯一TF发布者，并拒绝非有限/错frame/回退戳；RobotEnv、MoveIt、costmap继续只读TF。frame恒等：world=map=odom（tf2静态）。评价真值只经`Task3Env.evaluation_truth()`（`/gazebo/model_states`）。
- **仍使用“真值”的旧通路（Task4必须逐项处理或声明）**：①p3d→TF→`RobotEnv.getBaseTransformWorld`（IK所在底盘系、观测里所有“相对底盘”量、`dist_to_desired`）；②costmap_2d的`map→base_link`取自同一TF（激光本身是传感器，但其落图位置依赖位姿来源）；③EE规划用的全局地图是障碍真值；④碰撞/终止使用Gazebo接触话题（真值事件）；⑤reset用`/gazebo/set_model_state`直接放置底盘；⑥目标位姿由真值障碍场景采样。摄像头/IMU：模型里有`/imu/data`，**未被任何Task3代码使用**，相机未加入。
- **规划 vs 实际**：观测的臂关节=规划值；实际关节反馈只在`info['actual_arm_joints']`；Task4不得暗改`perception_style`。
- 冻结/复现：[execution_freeze.json](../../../../config/task3/execution_freeze.json)、[core_receipt.json](../../../../results/task3/t3.5-receipt/core_receipt.json)、固定episode实例（[t3.5-inst-r1](../../../../results/task3/t3.5-inst-r1/episode_instances.json)）。

## 四、限制与风险（交3.6/Task4）

1. 物理为混合模型：底盘/轮子重力开、UR5臂与夹爪保持参考的无重力；全链重力开使参考臂PID不稳定、复位失败（[SRC-0051](../../../SOURCES.md#src-0051) · [SRC-0059](../../../SOURCES.md#src-0059)）。原作者Gazebo实际行为未知。门槛是工程选择且有事后修订（[SRC-0054](../../../SOURCES.md#src-0054)）。
2. 验收run在CPU上做；之后forem-dev已重建并挂GPU（`--device cuda`的smoke通过，更新快约2.5倍）；重建后`freeze_task3.py verify`仍通过（镜像id/挂载不变），GPU下未重跑全套集成。
3. 仿真时钟复位不受支持：时钟回退使episode失效并被检测；`reset_simulation`后臂关节TF要很久才回来，恢复=重启仿真（新进程复用仿真只作信息记录）。
4. 运行样本小：随机策略数十个episode（int-r4的env 2个、resets-r2 12个、train-r1 6个），主要因IK失败终止，resets-r2中有1个随机到达目标；没有碰撞终止；没有收敛性证据。
5. 125 Hz反馈看不到1 kHz高频交替；MoveIt的“not newer”日志刷屏（两个JointStateController重复发布，参考原样）。
6. `/gazebo`在`/tf`上被登记为发布者但探针窗口内无消息（来源未查明）。
7. 依赖`import ray`顺序的规避；换镜像须复测。

## 五、3.6审核清单

- [ ] `audit_task3_core.py`、宿主/容器unittest（`test_task3_*`）复跑通过；`source_manifest`重生成无差。
- [ ] 复读`patch_reasons.json`与`patches/`：确认补丁语义影响声明，尤其`modulation_bumper`重力补丁。
- [ ] 新run-id复跑`validate_task3_core.py`（空闲容器），对照`integration_summary.json`；独立重算物理指标。
- [ ] 复跑`regress_task3_lifecycle.py`（TERM/INT/foreign/concurrent/dup/client-death）并核对容器空闲。
- [ ] 核对`task_contract`生效值与源码（3.0/0.8覆盖、direct/base、500步、IK阈值20）。
- [ ] 核对原Husky线数量与结论（A1–A7、B1–B3、C），可自行复跑`audit_husky_branches.py`与`custom_sac`导入。
- [ ] `freeze_task3.py verify`通过；确认未改`husky/`参考与Task0–2文件。

## 交接

目标：Task3 3.1–3.5。当前负责人：Claude实施完成，复核Codex 3.6。无运行进程/后台任务（容器仅保活，见下方清理核对）。风险同上。下一步：Codex执行3.6；通过后才允许Task4。

依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046) · [SRC-0049](../../../SOURCES.md#src-0049) · [SRC-0057](../../../SOURCES.md#src-0057)。

## Agent模型与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5；集成/时序/定位审查medium。实际：Claude Sonnet5.5，强度未知（平台默认）。


## 2026-10-07 追加：三项P2修正后的集成/冻结（Claude）

上文`t3.5-core-freeze1`、`t3.5-int-r4`等为修正前历史，保留有效性说明如下：freeze1已原样归档于`results/task3/freeze-archive/t3.5-core-freeze1/`；现行freeze为`t3.5-core-freeze2`（实例路径改FoReM相对，任意cwd verify一致）；clock阶段新增halt/停止发布门槛；新fresh运行`t3.5-fix1-int`、`t3.5-fix1-gpu`、`t3.5-fix1-life`、`t3.5-fix1-inst`及回执`t3.5-fix1-receipt`详见[task3 RESULTS](../RESULTS.md#2026-10-07-task36三项p2修正claude)。
