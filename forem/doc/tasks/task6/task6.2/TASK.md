# task6.2 RLlib Gazebo组：Task5 B改在Gazebo中训练 — 任务

> **当前状态（2026-10-19核对）：paused（2026-10-14用户要求停止于26.9万步；不要恢复）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**尚未执行（2026-10-12登记）**。父任务：[task6](../TASK.md)。执行：Codex；决策与复核：Claude。本节点即原task7的内容，按用户要求合并进task6（[SRC-0229](../../../SOURCES.md#src-0229)），原授权见[SRC-0227](../../../SOURCES.md#src-0227)；原文档存档于[archive](../../../agent_logs/task6/archive-20261012-pre-restart/task7/)。

## 背景与研究问题

[Task5 B](../../task5/task5.2/RESULTS.md)（Husky原版RLlib配方，sim）训练中评估成功率最高约0.82（52.5万步，单种子，50 episode）。[Task4.8 plain](../../task4/task4.8/RESULTS.md)（ScwmSAC，Gazebo）100万步时最终验证内部成功0/15。两者除执行环境外，还差训练器、更新频率、α规则、学习率调度、预热、设备、代码版本与运行栈、评估口径（逐项见下文“差异清单”）。

本任务只改一个因素：**沿用Task5 B的代码、训练器、超参数、种子和验证协议，只把`world_type`从`sim`改为`gazebo`**。

**问题**：B的训练配方在Gazebo执行下还能不能学会？
- 能学会（明显高于Task4.8）：Gazebo执行条件本身不是致命因素，Task4.8失败的主因更可能在训练器设置或代码/运行栈。
- 也学不会（接近Task4.8）：Gazebo执行条件是主因，与训练器无关。
- 介于两者之间：如实报告，不强行归类。

不预设结论。它与[task6.1](../task6.1/TASK.md)的F0（Task4.8训练器只改到sim）互为镜像，合起来是2×2对照：

| | sim | Gazebo |
|---|---|---|
| RLlib配方（Task5 B） | task5.2 | **task6.2** |
| ScwmSAC（Task4.8） | task6.1 F0 | task4.8 |

## 差异清单：Task5 B 与 Task4.8 plain

来源：B实际生效配置`results/task5/t5.2-train-s40/effective_wandb_original_config.json`、Husky快照`scripts/main_ray.py`、`modulation/myray/ray_utils.py::get_sac_conf`、`custom_sac.py`；Task4.8的`config/task4_scwm/plain.yaml`、`config/task3/{sac,task_contract}.yaml`、`scripts/scwm_sac.py`、`src/modulation_rl/scripts/sac.py`。逐项来源见SRC-0227。

**A. 随`world_type`一起改变的项（本任务改变这些，属于被测因素）**

|项|sim（B）|Gazebo（task6.2/Task4.8）|
|---|---|---|
|状态更新|理想积分+IK解|控制器+物理执行，回读底盘实际位姿|
|局部地图|真值floorplan裁剪|前激光costmap|
|碰撞|地图重叠|接触话题|
|reset|直接设置内部状态|`set_model_state`+spawn障碍|
|`MaxCloseStepsWrapper`|50|500（`wrap_in_task`按world_type自动取）|
|`init_controllers`|false|true（`utils.py:250-251`由world_type推出）|

**B. 训练器与算法（本任务保持B的值不变）**

|项|Task5 B / task6.2|Task4.8 plain|
|---|---|---|
|框架|RLlib `SACTrainerCustom`（`main_ray.py`）|`scwm_train.py`+`ScwmSAC`|
|采样|20个rollout worker并行+1个并行评估worker|单环境串行|
|更新频率|`training_intensity` 0.1：每10环境步1次更新|每环境步1次更新（10倍）|
|随机预热|0（`learning_starts=0`，task5 D7）|1000步|
|α|初值1.0，无上限；熵学习率1e-4|exp(log α)×0.35，≤0.05后冻结；熵学习率1e-6|
|学习率调度|按环境步线性1e-4→1e-6，视界1M|按更新次数指数衰减，视界5000001|
|设备|CPU（`num_gpus 0`）|cuda|
|种子|40（1个）|0/1/2|

**C. 代码与运行栈**：B为Husky快照原版+task5已披露偏差，melodic镜像`dhonerkamp/mobile_rl:11.1-latest`（Gazebo 9，Ray 1.6.0，Torch 1.11.0）；Task4.8为Task3迁移版`forem/src`+`ScwmEnv`包装，noetic `forem-dev`（Gazebo 11，Ray 1.13.0，Torch 2.7.1）。**因此task6.2与Task4.8之间仍差训练器和代码/运行栈两类，不是单因素；task6.2只与task5.2构成单因素对照。**

**D. 评估口径**：B训练中评估每7.5万步50 episode、`eval_seed 999`、评估时`transition_noise_base 0`、确定性动作；Task4.8每10万步5个种子（101–105）、确定性动作。成功判据都是`episode_is_success`。

**相同项**：任务simpleobstacle（代码内覆盖为3.0/0.8）、奖励、动作、观测、`transition_noise_base 0.04`、`ik_fail_thresh 20`、网络[512,512,256]+LocalDoubleMapCNN、γ 0.99、τ 0.001、batch 256、buffer 10万、grad_clip 10；`execute_style`两边实际都是`direct`（`main_ray.py`不把该键传入env_config，`create_env`默认`direct`）。

## 对齐口径（执行者不得更改）

- 代码：task5的`forem/build/task5/ws_husky`复制到`forem/build/task6.2/ws_husky`，只做PROCEDURE §3允许的多实例映射改动。不修改task5的工作区。
- 训练命令：与`results/task5/t5.2-train-s40/launch.json`逐字相同，只改两处：加`--world_type gazebo`；`--num_workers`取PROCEDURE §4确定的N（目标20）。`init_controllers`由代码自动推出。
- 种子40，100万环境步，`training_intensity 0.1`，`--load_best_defaults`，`num_gpus 0`，评估频率75000、50 episode、`eval_seed 999`，均与B相同。
- task5已批准、在B中生效的偏差（D5–D9等，以task5.2 RESULTS为准）原样沿用，逐项列入manifest。

## Claude决策（2026-10-12）

- **G-D1（终止阈值）**：Gazebo下`MaxCloseStepsWrapper`按代码默认取500，不强制改为50。理由：这是上游代码中world_type自带的一部分，与Task4.8一致；与B（50）的差异作为被测因素的一部分披露。
- **G-D2（多实例）**：RLlib的`env_creator`不按worker隔离ROS master（`modulation/utils.py:534-541`直接调用`create_env`），所有worker会连到同一个Gazebo、控制同一台机器人。按用户选择，每个rollout worker和评估worker各配一套隔离的ROS/Gazebo实例；只在task6.2工作区副本中加入“worker→实例”的环境变量映射，不改变env的step/reset/奖励/观测/终止语义。
- **G-D3（worker数）**：目标N=20，与B相同。若§4实测CPU不允许，停下报告Claude，不自行减少worker。N≠20时作为偏差披露：`training_intensity`固定时，更新与采样之比不变，但每次策略更新之间的采样分布会变化。
- **G-D4（评估）**：主指标为RLlib训练中评估`evaluation/custom_metrics/success_mean`，口径与B完全相同，可直接逐点对比。最终评估用最终checkpoint在Gazebo中跑simpleobstacle 50 episode（同`eval_seed 999`），见PROCEDURE §6。不做9任务Gazebo评估（Husky其他任务的Gazebo世界未验证，且未授权）。

## Claude审核R1决策（2026-10-12）：G-D5启动入口、G-D6安全性能优化

依据：[SRC-0231](../../../SOURCES.md#src-0231)（Codex §2阻塞记录）、[SRC-0232](../../../SOURCES.md#src-0232)。

- **审核结论（§1–§2）**：§1复制4616/1004条一致，配置哈希与继承偏差D1–D11已写；新容器`forem-t6-husky-gz`按规定挂载创建。从快照补`husky_control`、`pcl_configure`、`robotiq_85_moveit_config`，并加入已复制的`ur5_moveit_config`包路径，属于§2.6允许的“与Husky快照Gazebo启动直接相关的包”，接受，须在manifest列出。Codex按异常处理停下是正确的。
- **G-D5（启动入口，更正Claude原PROCEDURE的错误）**：原PROCEDURE写的`scripts/modulation/handle_launchfiles.py`是上游版本，`--env`只允许pr2/tiago/hsr，不含Husky，属于Claude写错路径。Husky快照的Gazebo启动器是`src/modulation_rl/gazebo_world/husky_ur5/handle_launchfiles.py`（`gazebo_cmds`只有`husky_ur5: roslaunch modulation_rl n2m2_husky_empty_world.launch`；simpleobstacle用`empty.world`；启动后把物理步长设为0.002、`max_update_rate` 500）。改用该启动器，原样不改。端口处理见PROCEDURE §3.1a。
- **G-D6（安全性能优化）**：用户要求“加入安全的性能优化”。B的learner在CPU上运行（镜像torch 1.11+cu102不支持本机GPU），不涉及GPU优化。
  - **一类：允许，实测有收益才启用**
    - 每个Gazebo实例及其ROS节点设CPU亲和，避免实例之间互相抢占。
    - rollout/评估worker进程限制库线程数（如`OMP_NUM_THREADS=1`），减少21个实例下的过量调度；learner进程的线程数只有实测更快才调整。
    - 关闭不给env提供数据的可视化节点（如rviz），只能通过launch参数关闭，不改launch文件。
    - W&B离线日志与监控采样保持低频；监控不得占用明显CPU。
  - **禁止**
    - 改Gazebo物理步长与`max_update_rate`（按G-D9固定为0.0005 s／2000 Hz），或改ODE迭代次数。
    - 改激光/传感器频率、costmap参数、控制器参数。
    - 改reset逻辑、env代码、worker数、`training_intensity`、batch或其他训练参数。
    - 超过20+1个实例。
  - 说明：线程数变化可能带来CPU浮点运算顺序的舍入级差异，与原B运行本身的非确定性同级，不视为科学条件改变，但须在manifest中写明实际线程设置。

## Claude审核R2决策（2026-10-12）：G-D7实例roscore、G-D8控制器依赖

依据：[SRC-0234](../../../SOURCES.md#src-0234)（Codex r2端口探针与依赖构建）、[SRC-0235](../../../SOURCES.md#src-0235)。

- **审核结论**：Codex实测普通`roscore`忽略`ROS_MASTER_URI`的端口，即使12400已有master，仍会另开11311的默认master。§3.1a原先“自带roscore会因端口占用而退出”的假设不成立，Codex停下是正确的。多实例下这会留下一个11311的游离master，没设好环境变量的进程会悄悄连上它而不报错，不能接受。
- **G-D7（实例roscore）**：不修改启动器文件，改为用一个包装脚本按启动器`__main__`的原样顺序执行，唯一区别是roscore带端口：
  1. `Popen(["roscore", "-p", str(12400+K)])`，`sleep 5`；
  2. `import handle_launchfiles`（即快照中的`gazebo_world/husky_ur5/handle_launchfiles.py`，模块原样导入），调用`handle_launchfiles.start_launch_files("husky_ur5", "rl", "simpleobstacle", False)`。
  - 与`__main__`相比只差roscore的端口参数；`get_world_file`、costmap膨胀参数、30秒等待、物理步长0.002与`max_update_rate` 500全部由原函数执行。用与启动器相同的系统python（去掉conda）运行。
  - 包装脚本放`forem/build/task6.2/scripts/`，与`__main__`的逐行对照写入diff。
  - 就绪核查增加：容器内除各实例端口外不存在11311的master（`getUri`探测须失败）。
- **G-D8（控制器依赖）**：镜像缺ROS控制器运行包，Codex从官方Git源码固定版本构建了ros_control 0.18.4、ros_controllers 0.17.3、gazebo_ros_pkgs 2.8.7、teleop_twist_joy 0.1.3（含controller_manager），无源码改动、无运行参数改动，只在task6.2的依赖ws中引用。属于§2.6允许范围，接受。
  - 须在manifest中列出URL、tag、commit。
  - 须在对照限制中注明：G-B的Gazebo控制栈（melodic、Gazebo 9、上述版本）与Task4.8（noetic、Gazebo 11）不同，这属于已披露的运行栈差异。
  - ros_controllers未能取到0.18.2，改用实际存在的0.17.3；这是工程选择，若§2就绪核查发现控制器行为异常（例如底盘不跟随速度指令），停下报告。
- **另注（障碍几何）**：Gazebo中障碍全为矩形，而R-B（task5.2，sim）约一半是椭圆柱，见父TASK与[SRC-0235](../../../SOURCES.md#src-0235)。G-B与R-B因此同时差执行环境和障碍形状，汇总时须注明。

## Claude审核R3决策（2026-10-12）：G-D9物理步长

依据：[SRC-0237](../../../SOURCES.md#src-0237)（子Agent r4诊断）、[SRC-0238](../../../SOURCES.md#src-0238)。

- **审核结论**：r4诊断可信。同一实例、同一代码与控制器参数下只改物理步长：0.002 s时reset多数失败（内层`resetArm failed`共420行），0.001 s与0.0005 s各12次reset全部成功。机理是0.002 s下UR5 shoulder_pan/lift在折叠复位姿态附近力矩饱和颤振；0.001 s下pan仍力矩饱和（幅度约0.01 rad，低于容差），只算勉强可用。Gazebo日志中的“Joints on incoming goal don't match”来自夹爪goal关节名，是上游既有现象，与复位失败无关，每次reset出现一次，照常披露。
- **G-D9**：G-B的Gazebo物理步长改为**0.0005 s、`max_update_rate` 2000**。
  - 理由：0.002 s不可用（worker会因复位失败崩溃）；0.0005 s与Task3/Task4.8所用世界文件（`forem_husky/worlds/husky_empty.world`）一致，可以消掉G-B与R-48之间的一项物理差异；0.001 s在本实测中仍有力矩饱和。
  - 实现：在G-D7包装脚本中，`start_launch_files()`返回后，按原`gazebo_set_pyhsics_properties`相同的服务序列（get→pause→set→unpause）把步长设为0.0005、`max_update_rate`设为2000，其他物理属性（重力、ODE配置）原样保留。启动器文件仍不修改。
  - G-D6中“禁止改物理步长0.002、`max_update_rate` 500”一条改为：**物理步长固定为0.0005 s／2000 Hz，不得再改**。其余禁止项不变。
  - 对照限制须写明：G-B与原Husky启动器（0.002）不同，与R-48（Task4.8）相同。
- **新增就绪要求**：r5须记录0.0005 s下shoulder_pan/lift复位后的力矩饱和比例和摆幅；§4须在20+1实例下实测每个实例的实时因子和每步仿真时长，与单实例相比中位数偏差不超过5%（工程选择）。若多实例下跟不上实时、使每步仿真时长缩短，停下报告，不自行减少实例或改步长。

## Claude审核R4决策（2026-10-12，用户已同意）：G-D10每步固定0.1 s、G-D11 N=10

依据：[SRC-0240](../../../SOURCES.md#src-0240)、[SRC-0241](../../../SOURCES.md#src-0241)（子Agent r5/iso/冒烟）、[SRC-0242](../../../SOURCES.md#src-0242)。用户2026-10-12在选项中选择“固定每步0.1秒”和“现在用N=10”。

- **问题**：Gazebo模式下末端规划器每步时长取两次`env.step`之间实际流逝的仿真时间（`eeplanner.py` L162–176，上限0.5 s；`robotenv.py` L243–247的`rate.sleep`被注释），sim固定为0.1 s。实测G-B冒烟约0.34 s/步，Task4.8约0.04 s/步。若原样运行，G-B的步长语义会随N、CPU负载和线程设置变化。
- **G-D10（每步固定推进0.1 s仿真时间）**：只在task6.2工作区副本中，由`env_creator`在`create_env`之后套一层包装（环境变量`T62_FIXED_WINDOW_S=0.1`时启用，未设置时为空操作，sim路径不受影响）：
  1. `reset`：原样执行内层`reset`（复位需要物理运行，保持不暂停）；返回后推进一个0.1 s窗口再暂停物理，然后返回reset的观测。这样第一步的规划时长也是0.1 s。
  2. `step(a)`：物理处于暂停状态时调用内层`step(a)`（发送指令、读取观测、计算奖励，与原Gazebo模式一样，观测反映的是上一个窗口结束时的状态）；返回后恢复物理，等仿真时钟推进0.1 s，再暂停。
  3. 窗口推进用`/gazebo/unpause_physics`、`/gazebo/pause_physics`与`/clock`实现，可参考`forem/scripts/scwm_clock.py::FixedWindowClock.advance`的做法并记录每步超出量。**不得**使用其`unthrottle`（不改`max_update_rate`，G-D9固定0.0005 s／2000 Hz）。
  4. 不改env、规划器、控制器、奖励、观测、终止的代码；只是让每步之间流逝的仿真时间固定。
  - 验收（工程选择）：规划器每步`dt`的中位数与0.1 s之差≤0.002 s，最大值≤0.12 s；每步仿真时长与实例数、CPU负载无关（N=2与N=10下中位数之差≤0.002 s）。
  - 结果：G-B的步长语义与R-B（sim，0.1 s）一致；与R-48（Task4.8，约0.04 s、自由运行）不同，汇总时须注明。原G-D9中“20+1实例下实时因子与单实例中位数偏差≤5%”的要求随之作废：实例数和负载只影响墙钟。
  - 观测滞后：Gazebo模式下观测落后一个窗口是上游既有结构（[SRC-0161](../../../SOURCES.md#src-0161)），本机制不改变它，须在对照限制中注明。
- **G-D11（N=10）**：训练worker数取10，另加1个评估实例，共11个Gazebo实例。与B的20不同，按G-D3作偏差披露：`training_intensity`固定，更新次数与采样步数之比不变，但每轮采样的worker数减半。启动前核对CPU合计持续不超过56核（含task5后处理评估与task6.1）。
- **G-D6修订**：在G-D10下，线程数与CPU亲和不再改变每步仿真时长，可按一类优化实测启用（仍须有收益）。

## 范围

- **包含**：新容器与工作区副本、melodic下Husky Gazebo启动核查、多实例隔离及回归、冒烟与profile、一条100万步正式训练、训练中评估、最终Gazebo评估、与task5.2和Task4.8的对照。
- **不包括**：修改训练器/超参数/奖励/观测/任务/终止；Task4.8策略的Gazebo侧评估（属于task6.1）；物理成功测量（原版env不提供，需新增代码，未授权）；用B的sim策略做Gazebo零样本评估（未授权）；多种子；世界模型；修改`husky/`、`mobile-rl/`、`forem/src`、task5工作区；干预task5和task6.1的运行。

## 交付与验收

- 容器、镜像digest、工作区副本sha256清单，以及相对task5工作区的完整diff（只允许多实例映射）。
- 单实例Gazebo就绪证据；多实例隔离回归证据（节点集合不相交、参数不串、一个实例中移动机器人不影响另一个）。
- 冒烟、profile、N的确定依据和100万步时长估计。
- 正式训练的完整配置导出、日志、checkpoint、训练中评估序列。
- 最终Gazebo评估原始记录。
- 对照表：task6.2与task5.2逐评估点并列（success、goal_reached、ik_fails、base_collisions、episode_len）；Task4.8作参照，注明口径不同。
- 偏差全部披露；由Claude复核后才能标done。单种子结论只用于诊断。

## 模型与推理强度推荐

|工作|Codex|Claude|强度与理由|
|---|---|---|---|
|容器、melodic Gazebo启动与多实例隔离|GPT6.1sol|Sonnet5.5|medium：跨RLlib worker进程、ROS/Gazebo master和容器网络核对因果|
|正式训练与评估执行|GPT6.1sol|Sonnet5.5|medium：按流程执行，注意资源与实例隔离|
|长训监控子Agent|gpt-6.1-sol|Sonnet5.5|low：只读监控，不改配置|
|复核|—|Sonnet5.5|medium|

只有多实例隔离已记录至少两种不同思路都失败、且原因不明时，才允许升级到gpt-6-astra/high，并须写明理由。本文档作者为Claude claude-opus-5-5，推理强度未知。
