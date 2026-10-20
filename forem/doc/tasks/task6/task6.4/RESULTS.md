# task6.4 按N²M²原论文方法对task5 A/B做Gazebo零样本评估 — 结果与交接

> **当前状态（2026-10-19核对）：阶段一done（R3）；阶段二暂缓，待用户决定。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**阶段一done（2026-10-14 Claude复核R3通过）；阶段二暂缓，待task6.5结果再定**。原状态：**review（阶段一review，2026-10-14；A/B各50回合已完成并核验，停止等待Claude）**。计划见[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)。以下各节由执行者按实际运行填写；未执行的步骤保持“尚未执行”。

## 阶段状态

|阶段|结果|证据|
|---|---|---|
|§1 开工与隔离方案|阶段一冻结/依赖/网络及实际master已核；阶段二world资产核对待放行|[最终核查](../../../../results/task6/t6.4-R2/final_verification.json)|
|§2 Gazebo就绪与冒烟|A按R2/T64-D3接受原3完整回合；B-r3在0.0005/2000完整3回合/退出0通过|[B-r3核验](../../../../results/task6/t6.4-smoke-B-r3/verified_eval.json)|
|§3 阶段一（simpleobstacle）|A16/50、B36/50；全50种子及原始指标核查完成，review交Claude|[汇总/manifest](../../../../results/task6/t6.4-summary/manifest.json)|
|§4 阶段二（A其余8任务）|尚未执行（须Claude放行）||
|§5 汇总|仅阶段一已汇总；含A逐回合碰撞对象，阶段二尚未执行|[comparison](../../../../results/task6/t6.4-summary/comparison.json)|

## 结果表（§5填写）

|策略|任务|sim成功率（task5）|Gazebo成功率（本任务）|原文PR2 Gazebo（Table VI）|
|---|---|---|---|---|
|A（PR2）|simpleobstacle|39/50=78%（原stdout核对）|16/50=32%|81.6%（5种子均值）|
|B（Husky）|simpleobstacle|39/50=78%（原stdout核对）|36/50=72%|—（原文无Husky）|

参照：task6.3 F0 sim→Gazebo 0.433→0.16/0.20；R-48 0.053（[SRC-0256](../../../SOURCES.md#src-0256)）。

## 交接

- 目标与授权：见[TASK](TASK.md)，[SRC-0257](../../../SOURCES.md#src-0257)。
- 当前负责人：Codex已完成阶段一并停止；Claude负责独立复核与阶段二放行决定。
- 派发提示词：[20261013-claude-task6.4-plan.md](../../../agent_logs/task6/task6.4/20261013-claude-task6.4-plan.md)。
- 下一步：Claude核对本RESULTS末节及summary原始证据，决定是否放行§4；执行者当前已停止，不自动运行阶段二或新实验。


## 2026-10-13T21:30:52.276541+08:00 §1执行与异常停止

授权仅用户本轮§1–§3：A PR2/track、B Husky/direct，simpleobstacle冒烟各3后正式各50；阶段一review后停止。B只在r4同类reset失败后允许0.0005/2000，未获得安装/构建依赖授权。[授权/协议](PROCEDURE.md) · [本次证据SRC-0258](../../../SOURCES.md#src-0258)

### 运行位置与资源

选择§1(b)，同镜像新容器`forem-t6.4-pr2`、`forem-t6.4-husky`。task5两容器仍有2026-10-11启动的analytical ROS，虽然本次现场没有看到D21评估进程，不能替所属任务清理，故选择隔离，避免等待无法确定的清理时点。镜像完整ID沿task5：`sha256:42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915`。

两容器bridge不同IP（172.17.0.6、172.17.0.7）及不同网络sandbox，不发布宿主端口；预期各11311在各自命名空间。**尚未启动ROS master，不能声称已实测master隔离。** 配置/ID/mount/网络见[creation](../../../../results/task6/t6.4-preflight/container_creation.json)、[isolation](../../../../results/task6/t6.4-preflight/network_isolation.json)。task5 build/models/reference挂载ro，结果各写`t6.4-preflight/A|B`独立rw。A继承镜像工作区，并将task5已经批准的D2 mapencoder、D7 ray_utils、D9地图原样导出到`forem/build/task6/task6.4/`、ro挂到相同位置（没有改源码内容）；B直接ro使用task5 build工作区。导出文件是副本，不修改task5或参考仓库。

主机64逻辑CPU，GPU四卡本次preflight均无计算负载；两秒快照约16.69忙核，仅现场观测，不作为A/B+G-B并发≤56核的验证。未运行评估，不产生episode耗时、吞吐或阶段一/二工期预测。

### 哈希与输入

[hash_verification.json](../../../../results/task6/t6.4-preflight/hash_verification.json)：A/B各`evaluation_ray.py`、`modulation/utils.py`、`modulation/evaluation.py`、`modulation/handle_launchfiles.py`、`src/robot_env.cpp`均与task5当前对应容器一致；A五文件另与mobile-rl参考一致，B与task5.0原始源码manifest一致。两个checkpoint-1000与各自config_provenance所指原trial文件sha256相等。task5后处理在D21中断，最终freeze manifest未生成；当前验证不能替代缺失的历史checkpoint封存。

|策略|checkpoint-1000 sha256|
|---|---|
|A|`4f9a81a4fc39ba2c0c27a6e440273fe3320fdf4c730742fa2144e15a3e5cde6e`|
|B|`b5a7b04f91d0352ef59e367b5c4b836a0d09fa17c539f983cfdaad77cdce4553`|

尚未加载模型。原版`restore_ckpt_files`会在模型目录写`.tune_metadata`，因此后续包装须把同run模型/配置/metadata逐字节复制到独立可写目录并再核哈希；不能写task5只读模型目录。当前未创建这类评估副本，未调用restore。

### 实际静态命令与退出码

两边先source `/opt/ros/melodic/setup.bash`及对应devel；B保留task5已批准`ROS_PACKAGE_PATH=/forem_build/deps/lms1xx:$ROS_PACKAGE_PATH`。完整命令/标准输出/错误分别保存在[ A收据](../../../../results/task6/t6.4-preflight/A-launch-static.json)、[B收据](../../../../results/task6/t6.4-preflight/B-launch-static.json)，日志见`forem/logs/task6/t6.4-preflight/`。

```sh
# A（仅XML枚举，退出0；不是启动）
roslaunch --files modulation_rl pr2_empty_world.launch gui:=false BIOIK:=true world_name:=empty.world
# B（仅XML枚举，退出1）
roslaunch --files modulation_rl n2m2_husky_empty_world.launch gui:=false world_name:=empty.world
# B错误
Resource not found: husky_control
```

静态读取表明A launch包含Gazebo、PR2控制器、move_group、costmap；B原版入口应为`gazebo_world/husky_ur5/handle_launchfiles.py`（scripts/modulation启动器没有Husky选项，B evaluation_ray的launch_ros已注释）。其原版流程30秒后设置0.002/500；本次未执行。B的缺包在include链解析阶段，不是r4臂reset失败，**不能通过改0.0005/2000处理**。因此命中PROCEDURE“Gazebo启动链缺包”即停条件：未补包、未构建、未移用G-B构建产物，没有继续A冒烟或任何评估。其余任务world文件存在性未完成核对，后续依赖/插件是否缺失未知。

### 清理、限制与交接

run-id实际为`t6.4-preflight`；`t6.4-smoke-A/B`、正式A/B和D21续跑均**尚未执行**，episode数0，不填写成功率0，不标阶段一review。评估包装脚本尚未编写。原配置未变，物理步长、控制器运行状态与底盘运动均未实测。

新容器末次docker top均仅`sleep infinity`，没有启动过ROS/Gazebo，无自有长任务需停止或恢复；容器保留，非自动恢复入口。task5首尾ROS PID一致，未停止/干扰；G-B仅外部docker top只读快照，无docker exec/信号/配置修改。证据目录各`*-final-top.json`与`protected-gb-final-top.json`可复核。无训练、源码补丁、依赖安装或构建、额外任务、固定每步时长。

下一步Claude核查[B原始错误](../../../../logs/task6/t6.4-preflight/B-launch-static.log)，决定依赖准备范围与恢复入口。此前task6.2缺包曾单独审批准备依赖，但本任务没有继承该安装/构建授权；不自动复制依赖或复用G-B容器。收到明确放行后再核对隔离/输入/全部启动依赖，接续§1→§2→§3；阶段二仍必须等待Claude放行。

模型推荐：Codex GPT6.1sol / Claude Sonnet5.5；§1–§2 medium（跨启动栈/隔离/合同核对）、§3 low或默认（明确步骤评估）；实际模型/强度未知，未切换、未委派。独立日志：[20261013-codex-task6.4.md](../../../agent_logs/task6/task6.4/20261013-codex-task6.4.md)。


## 2026-10-14T00:16:03.286963+08:00 再次接手：t6.4-preflight-r2

用户再次授权原PROCEDURE §1→§3及异常即停规则。重读最新task6.4三文档和PROGRESS，未见Claude新增缺包处理/放行决定；此前过程保留，不新建重复容器。沿用同镜像隔离的forem-t6.4-pr2/husky，两者仍仅sleep infinity。

在forem-t6.4-husky重复原静态命令（source melodic/devel与task5已批准LMS路径后）：`roslaunch --files modulation_rl n2m2_husky_empty_world.launch gui:=false world_name:=empty.world`，**退出1，仍为Resource not found: husky_control**。再次命中异常停止条件，立即停止实施；仅整理证据和交接。

原始命令/退出码/错误：[B-launch-static.json](../../../../results/task6/t6.4-preflight-r2/B-launch-static.json)、[原始日志](../../../../logs/task6/t6.4-preflight-r2/B-launch-static.log)；[manifest](../../../../results/task6/t6.4-preflight-r2/manifest.json)和evidence_sha256.json冻结本次证据。task5两容器top仍为原analytical ROS PID；没有停止、清理或更改它们。G-B本轮没有docker exec/top或其他容器操作。

本轮没有启动ROS/Gazebo、安装/复制依赖、构建、改源码或物理步长；A启动核查/全部哈希不重复，上一轮证据只作历史，不冒充本次实测。冒烟/正式episode均0，阶段一**尚未执行**，不标阶段一review，阶段二未放行。下一步Claude明确缺包依赖准备范围或交付修复环境后重新登记接手。依据[SRC-0258续记](../../../SOURCES.md#src-0258)。

负责人Codex已停止并交Claude；模型/强度实际未知，未切换/委派。推荐仍Codex GPT6.1sol、Claude Sonnet5.5，§1–§2 medium（启动栈核查）、§3 low/默认。独立日志：[20261014-codex-task6.4.md](../../../agent_logs/task6/task6.4/20261014-codex-task6.4.md)。


## Claude复核R1（2026-10-14，用户：“一切按你的推荐”）

- **§1已完成部分通过**：新容器`forem-t6.4-pr2`、`forem-t6.4-husky`（同镜像、bridge、未发布端口）、只读挂载、五个评估入口文件与两个checkpoint哈希均核实；B缺`husky_control`的停止判断正确（PROCEDURE列为即停条件，本任务未继承安装授权）。task5、G-B未被干预。
- **T64-D1：A与B解耦，A立即继续。** A的启动链静态枚举退出0，不依赖B。A按PROCEDURE §1剩余核对→§2冒烟→§3正式评估独立推进；B的问题不再阻塞A。
- **T64-D2：B复用task6.2已准备的Gazebo依赖。** 同一镜像的Husky Gazebo依赖已在task6.2准备并经Claude R2接受（G-D8）、实际运行通过：`build/task6.2/deps/`（gazebo_snapshot中的husky_control、pcl_configure、robotiq_85_moveit_config；UR 1.5.0的ur5_moveit_config；ros_control 0.18.4、ros_controllers 0.17.3、gazebo_ros_pkgs 2.8.7、teleop_twist_joy 0.1.3、interactive_marker_twist_server 1.2.1、roboticsgroup_gazebo_plugins及其构建产物），来源与sha见`results/task6/t6.2-env-r1/additional_dependency_manifest.json`、`t6.2-env-r2/new_dependency_sources.json`、`t6.2-env-r3/dependency_manifest.json`。
  - 做法：把这些依赖目录及其devel/install**只读**挂载进`forem-t6.4-husky`（不可只读挂载时复制到`build/task6/task6.4/deps/`并逐文件核sha）；环境前缀顺序沿用task6.2 r3修正后的做法（依赖devel在Husky devel之后source，避免CMAKE_PREFIX_PATH被覆盖）。不重新构建、不改任何依赖源码、不写入task6.2目录、不进入`forem-t6-husky-gz`。
  - 启动方式：Husky原版`evaluation_ray`的`launch_ros`已注释，B须先用包装脚本调用`gazebo_world/husky_ur5/handle_launchfiles.py`的`start_launch_files("husky_ur5","rl","simpleobstacle",False)`（与task6.2 G-D7相同的原样导入方式；本容器网络独立，用默认11311即可），再运行`evaluation_ray.py --evaluation_only --eval_execs gazebo --env husky_ur5 --execute_style direct ...`。
  - 物理步长按TASK原规则：先用原启动器设置；出现task6.2 r4同类复位失败时改0.0005 s／2000 Hz（G-D9做法），新run-id重做。
  - 先做`roslaunch --files`静态枚举，退出0后才启动；其余缺包或启动失败仍按异常处理停止交Claude。
- 两者都完成阶段一后RESULTS标“阶段一review”并停止；阶段二仍须Claude放行。依据[SRC-0259](../../../SOURCES.md#src-0259)。


## 2026-10-14T00:31:28.049747+08:00 R1接续实施（进行中）

已按SRC-0259继续，A/B独立容器沿用。B复制复用依赖，逐文件核sha并只重定位副本绝对软链，未重建或改源；静态枚举rc0。五入口/两checkpoint复查一致。A t6.4-smoke-A-r1、B t6.4-smoke-B各3episode正运行；launcher/health rc0，原物理0.002/500，无回退。尚未有正式50episode结果。准确命令commands.json、health/status/cleanup在各run目录；独立日志详记路径/监控/停止。后续实测追加SOURCES，当前不标阶段一review。


## 2026-10-14T00:38:59.475798+08:00 R1执行结果与停止交接

依据[SRC-0259](../../../SOURCES.md#src-0259)，A/B解耦，B依赖复用执行。本轮新证据统一登记[SRC-0262](../../../SOURCES.md#src-0262)，此前blocked/接手与“进行中”记录保留为历史。

### 依赖部署与版本核对

已有容器不新建、不重启。B追加bind mount尝试被容器权限拒绝（没有生效挂载），采用R1已允许的复制：host `build/task6/task6.4/deps`及`gazebo_deps_ws`来自task6.2；另为独立可写日志入口复制task5 `ws_husky`。全部普通文件SHA与软链字面目标在复制时逐项一致，见同目录`*-copy-verification.json`（保留源目录与条目）。未构建、未改依赖源码/二进制、未写task6.2；不进入G-B。docker cp到B `/t64_runtime`后，349条副本中原`/forem_build/...`绝对软链重定位至`/t64_runtime/...`，生成链接映射在[原始映射](../../../../results/task6/t6.4-preflight/B/runtime_link_relocation.json)。只调整副本链接以适配已有容器，不将其宣称原路径的只读bind已生效。

Husky原devel后source复制依赖devel --extend，再保留依赖CMAKE_PREFIX_PATH、ROS_PACKAGE_PATH和LD_LIBRARY_PATH。B静态枚举rc0：[B-static.json](../../../../results/task6/t6.4-R1/B-static.json)。A使用原脚本handle_launchfiles的PR2/Gazebo入口，B用授权原start_launch_files包装（源函数未改）。A active代码仍镜像任务5入口；B active评估代码是task5逐字节副本`/t64_runtime/ws_husky`，ROS launch读取原只读`/forem_build/ws_husky`。本轮五入口/两checkpoint首尾不变：[freeze](../../../../results/task6/t6.4-R1/freeze_recheck.json)、[postrun](../../../../results/task6/t6.4-R1/postrun_source_verification.json)。模型每run复制可写local_model，仅恢复metadata在副本写入，task5模型不写。

### §2实际冒烟

|run-id|设置|已结束回合|success|评估退出码|结论|
|---|---|---|---|---|---|
|t6.4-smoke-A-r1|PR2 track，0.002 s/500 Hz|3：seed999–1001，1523/679/1804步|0/3|134|三个回合正常终止但进程异常退出；冒烟未通过|
|t6.4-smoke-B|Husky direct，0.002 s/500 Hz|0|未产生|1|内置reset重试耗尽，Could not set start pose；符合授权回退条件|
|t6.4-smoke-B-r2|Husky direct，0.0005 s/2000 Hz|1：seed999，642步|1/1（部分结果）|1|按A异常停止规则主动清理时出现TF外推错误；完整冒烟未通过|

三个run launcher、独立health均退出0，physics实际值在各health.json；A九控制器running，B必要五控制器running、joint_group_eff_controller initialized。启动/physics服务的主机sleep仅沿原启动器等待，未固定策略每步时间；time_step仍0.02，IK评估阈值50，确定性动作，无exec action额外缩放。CPU真实运行日志为TorchPolicy running on CPU，num_gpus0沿task5冻结。[准确commands.json/health/status/cleanup](../../../../results/task6/)以run-id索引。

A预先建立`t6.4-smoke-A`仅是未执行准备目录；实际使用新`t6.4-smoke-A-r1`，不重复计数。其eval.log的3条Eval ep与offline原始指标一致：success0、goal_reached0、base_collisions比例1、IK均0、epoch_len1335.333；每回合base coll50。**退出134发生于三回合及W&B指标写出后，末尾有ClassLoader卸载警告；目前只知道异常退出，不能证明根因就是该警告或某个析构器。** 不将回合数据写成正式验收，不直接忽略134重跑或进入§3。

B原0.002完整保留resetArm failed/50trials/9reset重试错误，随后身份清理after=[]；按授权新run-r2服务序列保留gravity/ode_config，只改time_step/max_update_rate。r2实际health0.0005/2000，第一回合成功、IK0、base coll0。发现A rc134后按PROCEDURE即停，使用本runT64_RUN+PID start ticks核身份发SIGINT/SIGTERM；[interruption.json](../../../../results/task6/t6.4-smoke-B-r2/interruption.json)记录原因。r2在第二回合reset附近出现future extrapolation（请求67.0965、最新66.616，base_footprint→map），最终rc1；清理与异常时序重叠，不把它认定为0.0005下的独立自然reset失败，也不认定剩余回合可运行。日志保留，不进行额外诊断/重跑。

底盘被动/model_states观察写pose_observer.json，无额外控制命令；A/B位置变化包含reset搬迁，不能当轨迹距离。B-r2同时记录twist速度峰值0.505m/s，支持确有底盘运动，不能代替控制跟踪精度。metric文件来自原W&B二进制日志，用task5只读export工具导出offline_raw_export.json。model_file分支W&B config有意保留训练sim/50，运行CLI覆盖在另一个DotDict（utils.py L351–403）；实际本次gazebo/3由命令、prefix与Eval ep数量核查，不能误将保存的训练配置当评估生效参数。

### 耗时、资源与未执行项

A已结束回合日志墙钟53.4/46.2/65.4秒，均55秒，线性50约45.83分钟；B-r2单回合24秒，线性50约20分钟。只是失败/部分冒烟的算术估计，非可靠工期；启动、收尾、复位失败和长episode尾部未覆盖，不能据此放行正式任务。A eval命令实际墙钟202.725秒含初始化/收尾，整体runner251.838秒；B原runner87.100秒，B-r2中止runner111.732秒。源数据status/commands均为实际秒，分钟来自两位小数日志。阶段二未建立可靠估计。

B启动前两秒host总忙核11.07，包含A/其他任务（cpu_pre_B.json）；不当完整性能profile或并发峰值证明。§1各任务world文件全表存在性核对未形成交付，阶段一empty.world实际已加载；阶段二仍需核对并等放行。§3 A/B正式50均**尚未启动**，无D21/拼接，§4未放行，§5正式结果对照未生成。表中A/B sim值仍待task5.3，不擅自验收另一任务；无新训练。

### 清理与交Claude

三run cleanup均after=[]，最终forem-t6.4-pr2、forem-t6.4-husky仅sleep，见R1目录`*-final-top.json`。无本任务后台进程；当前容器保留，不自动恢复。task5原analytical ROS PID保留，task5其他Agent同期D21工作未被发信号/重启/改源；G-B本轮无docker exec/top、信号或配置操作。

新增包装：[run_task6_4_eval.py](../../../../scripts/run_task6_4_eval.py)，语法检查通过；只做启动/记录/恢复metadata副本/被动物理观察/身份清理，不改策略、环境、奖励或任务。具体运行命令、run-id、退出码/时间、stdout、sha、复制依赖链接映射均在上述证据。当前blocked交Claude：先决定A rc134该如何诊断/处理，明确B r2中止/TF错误的复核方式，再放行重做尚未通过的冒烟；本轮不自行忽略退出码或调控制参数。**阶段一未完成，不能标“阶段一review”。**

模型推荐Codex GPT6.1sol / Claude Sonnet5.5，§1–§2 medium（跨启动栈/隔离/路径核对），§3 low/默认；实际模型/推理强度未知，未切换、未委派。负责人Codex停止交Claude；[续写日志](../../../agent_logs/task6/task6.4/20261014-codex-task6.4.md)。


## Claude复核R2（2026-10-14 08:3x）

- **依赖复用与启动**：只读挂载被拒后改为复制并逐文件核sha、重定位软链，符合R1“不可只读挂载时复制”的规定，接受。B静态枚举rc0，A九个、B五个控制器running。
- **A退出码134**：三个回合的“Eval ep”行完整、W&B指标已写出，134出现在其后，日志末尾为pluginlib“SEVERE WARNING!!! Attempting to unload library while objects created by this loader exist in the heap”——ROS进程退出时卸载插件库的常见中止，发生在评估完成之后。**T64-D3**：A的评估有效性以“请求的回合数全部有‘Eval ep’行且指标已导出”为准，退出码照实记录为偏差，不作为失败；若134出现在回合未完成时，仍按异常停止。
- **A三个回合全部因底盘碰撞终止（各50次）**：Claude查日志，碰撞对象是真实的Gazebo障碍物（`pr2::base_footprint…base_link_collision_1`与`obstacle16/18/19::link::collision`，每回合一个障碍）。同种子在sim中（task5 r1）为1/0/1成功、0碰撞、82–314步；Gazebo中679–1804步。这是Gazebo中的真实行为，不是检测错误；上游README所述缺失的后方测距传感器可能相关（待查，不在本任务诊断范围）。冒烟只有3回合，不据此下结论。
- **放行A**：§3正式`t6.4-A-simpleobstacle`（50回合，约46分钟）。§5另统计每回合碰撞对象（日志“Collision:”行），用于说明失败形式。
- **B**：0.002 s下复位失败与task6.2 r4一致，按规则改0.0005 s／2000 Hz，正确。r2的中止是执行者因A异常主动停止所致——R1已规定A、B解耦，**A的异常不应停止B**。r2的TF外推错误与中止清理时间重叠，不作为B的失败证据。
- **放行B**：新run-id `t6.4-smoke-B-r3`（0.0005 s，3回合，不中断）；通过后§3正式`t6.4-B-simpleobstacle`（50回合）。
- A、B都完成阶段一后RESULTS标“阶段一review”并停止。依据[SRC-0265](../../../SOURCES.md#src-0265)。


### 2026-10-14T08:34:52.250097+08:00 R2 B-r3完整冒烟通过

`t6.4-smoke-B-r3`自然退出0，三个episode653/1893/652步，成功3/3、goal_reached1.0、IK均0、base_collisions0，cleanup after=[]。原始W&B导出与Eval ep计数/指标交叉一致，见[verified_eval](../../../../results/task6/t6.4-smoke-B-r3/verified_eval.json)。物理0.0005/2000，direct；不人为中止。按已授权启动`t6.4-B-simpleobstacle`正式50，A独立继续。当前未完成阶段一。后续证据汇总关联SOURCES。

本轮B-r3与阶段一运行依据/原文单任务对照统一登记[SRC-0266](../../../SOURCES.md#src-0266)；原文Table VI PR2 simpleobstacle=81.6%，mean79.2%不作单任务值。正式结果尚未完成。


## Claude注（2026-10-14）

新增task6.5用原作者预训练模型复现N²M²。本任务阶段二（我们的A其余8任务）暂缓，待task6.5阶段一结果再定；阶段一（A、B simpleobstacle）照常进行。


## 2026-10-14T09:26:35.046606+08:00 R2/T64-D3阶段一最终结果与交接

**阶段一review：A/B各50回合均已完成，原始日志与指标已核验，按用户要求停止。** 不是整个task6.4 done；阶段二未放行、未执行。历史中断/blocked/进行中记录保持，当前以本节与顶部阶段表为准。依据[SRC-0266](../../../SOURCES.md#src-0266)；协议变化沿[SRC-0265](../../../SOURCES.md#src-0265)。

### 有效设置与准确执行

沿用两容器、相同镜像与已核复制依赖，不新建/重建。A为PR2 track、physics0.002 s/500 Hz；B为Husky direct、0.0005 s/2000 Hz（原0.002失败证据与G-D9回退历史保留）。两边模型为task5各自checkpoint-1000/训练seed40；确定性50回合、eval_seed999（实际seed999–1048）、policy time_step0.02、评估IK阈值50、Gazebo上限100000、自由运行，无额外exec动作缩放或固定步时长。num_gpus0，TorchPolicy真实CPU日志保留。

准确shell/env/启动/physics/health/评估命令、起止时间、退出码均在[ A commands](../../../../results/task6/t6.4-A-simpleobstacle/commands.json)、[B commands](../../../../results/task6/t6.4-B-simpleobstacle/commands.json)；共同评估入口如下（在各自原版/逐字节评估副本目录运行，输出和恢复metadata只写独立run副本）：

```sh
# A
/opt/conda/bin/python -u scripts/evaluation_ray.py --evaluation_only --eval_execs gazebo --env pr2 --eval_tasks simpleobstacle --model_file /t64_results/t6.4-A-simpleobstacle/local_model/checkpoint-1000 --num_gpus 0 --nr_evaluations 50 --eval_seed 999
# B
/opt/conda/bin/python -u scripts/evaluation_ray.py --evaluation_only --eval_execs gazebo --env husky_ur5 --execute_style direct --eval_tasks simpleobstacle --model_file /t64_results/t6.4-B-simpleobstacle/local_model/checkpoint-1000 --num_gpus 0 --nr_evaluations 50 --eval_seed 999
```

A原评估退出134，发生在50条Eval ep、汇总和W&B写出之后；DataStore导出0且指标/计数一致，按T64-D3接受并标偏差，未把原退出码改0。B完整50自然退出0，未因A退出而中断。两侧全种子各一次，无D21超限/续跑/拼接，无删除失败样本。两边最大步数分别2435、4137，未近100000上限。

### 结果与对照

上游success与goal_reached口径保留；不新增独立物理success测量。sim引用task5原simpleobstacle.stdout同模型/种子各50只读复算，不取代task5.3九任务验收。原文列为Table VI同任务PR2 81.6%，不是九任务均值79.2%；本轮直接读arXiv原文HTML，详见[SRC-0266原文登记](../../../SOURCES.md#src-0266)。

|项|A：PR2|B：Husky+UR5|
|---|---|---|
|Gazebo上游success|16/50（32%）|36/50（72%）|
|task5 sim上游success|39/50（78%）|39/50（78%）|
|Gazebo − sim|−46个百分点|−6个百分点|
|原文同任务Gazebo|81.6%（5种子平均）|无Husky结果|
|goal_reached|16/50|39/50|
|有底盘碰撞的回合|31/50（30回合计50、1回合计34）|5/50（4回合计50、1回合计7）|
|有IK失败的回合 / IK均次|3/50 / 2.40|10/50 / 6.62|
|IK计数达到50的回合|2/50|6/50|
|selfcollision（上游二元指标）|6/50|8/50|
|success_nojumps|14/50（28%）|20/50（40%）|
|平均步数 / 范围 / 总步数|1029.62 / 232–2435 / 51481|1364.06 / 512–4137 / 68203|
|原eval退出码|134，按T64-D3记偏差|0|

**描述性结论**：同一策略与请求任务/评估种子下，B保留了大部分sim成功率（下降6个百分点），不能把Husky的Gazebo执行笼统视为必然严重失败。A在本冻结公开代码/镜像/单种子条件的simpleobstacle只到32%，比论文同任务低49.6个百分点，尚未达到原文PR2量级；34个非成功回合中31个有真实底盘接触，呈现的主要失败形式是碰撞。没有在本任务分离传感器缺失、控制、地图或时序各自的因果贡献，也不能由一个任务宣称整篇不可复现。

并列参照（已有[SRC-0266 / SRC-0256](../../../SOURCES.md#src-0256)）：task6.3 F0 sim0.433→Gazebo Z-A0.200/Z-B0.160，R-48 0.053。本次B0.720高于这些参考值，但训练器、ROS/Gazebo运行栈、策略/评估种子不同，仅并列，不能单因素归因于某个训练参数或迁移代码，更不证明世界模型必要性。

### A逐回合碰撞对象

[ A_collision_objects.json](../../../../results/task6/t6.4-summary/A_collision_objects.json)为全部50回合逐seed表：成功标记、上游base collision计数、打印事件数、对象名与原eval.log行号。共1158条Collision打印，机器人侧全为`pr2::base_footprint::base_footprint_fixed_joint_lump__base_link_collision_1`，环境侧18种障碍mesh字符串。按字符串聚合最多为obstacle24（140）、obstacle16（128）、obstacle33（100）、obstacle29（81）；不推断跨seed为同一实体。

分配窗口为前一条Eval ep结束后到本条结束前，包含该回合reset与rollout；日志事件数和上游counter分别保存，不强求一致。本次task开始前/最后完成后的未分配Collision行均0。原始真实Gazebo接触按R2已认可；未改检测器、奖励、碰撞阈值/任务，也不把打印事件差异包装成检测错误。

### 耗时、资源、冻结及清理

A runner2724.803秒（45.413分），B2368.486秒（39.475分）；正式两侧全局墙钟2724.803秒、累计runner5093.289秒（84.888分），包括启动/恢复/评估/收尾/清理，不当累计CPU时间或串并行等价提速验证。B-r3另188.215秒且与A重叠；这不是新训练预算。

[CPU采样](../../../../results/task6/t6.4-summary/cpu_sampling_summary.json)：538个约5秒全主机CPU-time样本，时间加权均12.481核、样本峰28.118核、>56样本0；不证明更短瞬态峰。只读监控通过自己stop标记退出0，未向任何训练发送信号。

[最终核查](../../../../results/task6/t6.4-R2/final_verification.json)：两侧指定五文件与原/复制checkpoint首尾完全一致；物理值/控制器/master记录在各health.json。不同网络sandbox、独立127.0.0.1:11311 master且无发布端口；ROS/Gazebo退出后11311/11345不监听，两容器仅sleep。cleanup均after=[]，所有本轮runner/observer/监控已退出，无本任务需恢复的后台工作；未触碰G-B容器，task5仅只读记录，未发送信号/重启/改源。

完整命令、模型/源码sha、镜像、物理/执行方式、raw指标/退出码、资源、偏差与后续范围见[manifest](../../../../results/task6/t6.4-summary/manifest.json)；[verification](../../../../results/task6/t6.4-summary/verification.json)核计数与输入/清理；原始指标[ A](../../../../results/task6/t6.4-A-simpleobstacle/offline_raw_export.json)/[B](../../../../results/task6/t6.4-B-simpleobstacle/offline_raw_export.json)，原始日志logs/task6/同run/，原生W&B保留。证据sha索引在summary/evidence_sha256.json。

### 偏差、限制与Claude下一步

- 单训练seed40、50回合，与原文5种子均值不同；只完成simpleobstacle，不构成全Table VI九任务复现。
- A既有镜像/costmap差异和公开后方测距传感器限制沿task5冻结保留；没有证明哪项解释多少损失。B使用差速direct与授权0.0005回退，版本/依赖沿G-D8；不是原作者硬件/环境完全重建。
- 原版解析/Gazebo的障碍几何与感知不同；同eval seed不证明逐场景/起止完全一致，未做额外场景校验实验。原生W&B config保留训练配置，生效评估CLI/DotDict与rollout前缀另核实。
- 采用原版success，不用新物理成功实现改口径；IK、自碰撞和底盘接触指标可能重叠，不把非互斥计数拼成互斥原因表。

**当前负责人**：Codex交付阶段一review并停止；Claude独立复核。从本节→comparison/manifest→两原始日志/指标→逐seed碰撞对象与SHA/清理证据核查；再决定是否放行§4。阶段二尚未执行，world资产全表核查亦应在放行后补齐；未增B其他任务、传感器、训练、人工误差或世界模型。

模型推荐：Codex GPT6.1sol、Claude Sonnet5.5；§3执行/整理low或默认，必要跨模块核查medium。实际模型/推理强度未知，未切换/委派。独立日志：[20261014-codex-task6.4.md](../../../agent_logs/task6/task6.4/20261014-codex-task6.4.md)。


## Claude复核R3（2026-10-14 11:1x，阶段一）

- **独立复算一致**：Claude从`logs/task6/t6.4-{A,B}-simpleobstacle/eval.log`的50条“Eval ep”行重算：A（PR2）16/50＝0.32，B（Husky）36/50＝0.72。同口径sim（task5 r1 simpleobstacle）：A 39/50＝0.78，B 39/50＝0.78。
- **失败形式**：A有31个回合出现底盘碰撞，其中30个达到50次碰撞而终止；碰撞对象全部是PR2底盘与Gazebo障碍物（“Collision:”行共1158条）。A在sim中0碰撞。B只有5个回合出现碰撞（车轮与障碍物），10个回合有IK失败。
- **配对**（同eval_seed 999起的回合序号；sim障碍约一半为椭圆、Gazebo全为矩形，场景不完全相同，只作参考）：A只在sim成功25、只在Gazebo成功2；B只在sim成功7、只在Gazebo成功4。
- **结论**：
  1. **Husky用N²M²原版方法从sim迁移到Gazebo，损失很小**：0.78→0.72（约6个百分点），与原文PR2/HSR/TIAGo的0.3–9个百分点同量级。所以task6.3中我们链路约27个百分点的损失，主要不是“Husky在Gazebo中本身难以迁移”，而在我们的链路（ScwmSAC策略、Task3迁移栈或二者）。
  2. **PR2在我们的Gazebo中损失很大**：0.78→0.32，原文Gazebo为81.6%。失败几乎都是底盘真实撞障碍。这是我们训练的A，不能区分是训练问题还是我们的PR2 Gazebo环境问题（如README所述缺失后方测距传感器）；task6.5用原作者模型回答。
- **偏差**：A退出码134（T64-D3，评估完成后）；B物理步长0.0005 s（原启动器0.002 s复位失败）；B用direct（差速底盘上游行为）；单种子、50回合；无D21超限。
- **阶段二暂缓**：先执行task6.5（原作者PR2模型），其结果决定PR2侧是否继续。依据[SRC-0270](../../../SOURCES.md#src-0270)。
