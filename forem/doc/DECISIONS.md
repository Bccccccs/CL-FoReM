# 决策记录

> **2026-10-16文档整理**：下方历史条目中指向task1、task2、experiment/等已删除文档的链接已失效，原文见[SRC-0321](SOURCES.md#src-0321)所列备份。最新条目在文末。
>
> **2026-10-19说明**：2026-10-16之前的条目（固定底座时延路线、视觉惯性定位、旧Task4内的WM方案、Task4暂停等）大多已被两阶段结构取代，仅作历史记录，**不是当前方向或可执行安排**。当前方向以[PLAN](PLAN.md)、[task7 TASK](tasks/task7/TASK.md)和文末2026-10-16起的条目为准。

记录已经确定的约定，注明用户授权与依据。候选仿真及未冻结的参数不写成已确定结论；不复用旧研究D系列编号。

## LAYOUT-20260930：开发和文档组织

- 用户要求：后续开发构建仅在forem；根AGENTS用于Codex与Claude交流；同意按研究问题组织计划和报告，并将项目按doc/config/src等目录划分。
- 决定：统一配置目录为config；实现放src，入口放scripts，环境放docker；数据、结果、日志与构建输出分开。
- 决定：文档按研究问题组织，每个问题有计划和reports；总体计划、唯一活动进度、决策和Agent日志位于forem/doc。
- 迁移：原根doc/PROGRESS和agent_logs迁入forem/doc；根路径保留兼容链接，不维护第二份活动状态。
- 实施范围：仅结构与文档，不授权本次执行仿真或编译。Gazebo与误差方案仍是候选研究方向。

## ENV-20260930：首轮仿真技术栈

- 用户要求：第一步先配置环境，确定用什么环境实现控制误差。
- 当前实施选择：沿用现有mm_husky:node01镜像中的Gazebo Classic 11.15.1、ROS Noetic、Python3.10.18；UR5使用gazebo_ros_control的EffortJointInterface和effort_controllers/JointTrajectoryController。FoReM使用独立容器与本目录源码/构建路径。此为当前工作选择，不将候选误差参数写成用户批准的冻结参数。
- 依据：现有Husky/UR5模型、launch及控制器明确配置力矩接口；镜像及旧容器只读查询确认版本、effort-controllers0.22.0和gazebo-ros-control2.9.3已安装。无需为首轮测量迁移全部机器人和ROS接口。
- 范围：先固定底盘或固定安装机械臂、空场景、正常轨迹跟踪；先测误差再实现一种受控指令时延/响应滞后。具体固定方式与参数尚未冻结。
- 适用限制：Gazebo Classic/ROS1属于旧技术栈，本选择用于既有项目的最小验证，不宣称长期维护优势；原版源码是否能在镜像内重新构建仍待实测。
- 状态：完成版本与源码接口核对；FoReM独立环境、源码依赖准备、编译和仿真尚未执行。

## HANDOFF-20260930：Claude执行最小环境配置

用户要求“写文档，我让claude执行”。Codex只准备执行交接；Claude按00-environment/PLAN实施独立固定底座UR5场景、effort控制器和反馈连通性验收。允许在FoReM内准备最小源码、适配基础入口与必要依赖、构建和启动。先不注入延迟、不接IK/SAC/WM；两次独立启动和真实反馈为验收证据。新环境实际执行状态仍为尚未实施。

## DOC-NODES-20260930：递归三文档

用户明确每个节点内部均要任务、流程、结果三份，且流程写明这一要求。TASK写目标和大致路线，PROCEDURE写详细控制流程，RESULTS写实际配置、运行与验收。所有子节点同样遵循。现有00环境节点拆E1–E5，各自建立三份；01跟踪节点保留三份尚未执行草案，待实际需要再拆子节点。此前每节点README/PLAN/reports结构被取代，旧文档快照保存在工作区外before-recursive-three-documents.tar。

## PROJECT-TASKS-20260930：一任务一目录与递归编号

用户明确这些是项目总体要求：task0为当前环境配置，一个任务一个目录；其子任务在task0内部用task0.1等编号，更深层递归。每层三文档，详细流程必须写明这一规则。可顺序完成或委派子Agent，父Agent维护依赖、范围与最终验收。现有活动目录统一迁至doc/tasks/task0与task1，task0.1–task0.5保留原前置检查→UR5配置→构建→反馈→运动的依赖顺序。本轮没有启动子Agent或执行环境。

## TASK0-SOLVER-20260930：正常物理采用 ODE 直接求解器（world），偏离参考的 quick

- 问题：task0.6 发现 quick 求解器下固定底座 UR5 保持姿态时六个关节持续逐物理步（约 1 kHz）交替，125 Hz 采样看不见（混叠成“偏置/偶发翻转”）。
- 依据（task0.7 单因素诊断，见 [task0.7 RESULTS](tasks/task0/task0.7/RESULTS.md)）：步长 0.25 ms、迭代 50/200/1000、sor 0.5、P/D 增益缩放或归零、erp 0.1、cfm、惯量重缩放、真正生效的零重力、以及完全不启动力矩控制器的被动关节，交替全部仍在（逐步交替比例约 1，速度高频残差 ≥ 7×10⁻⁴ rad/s）；只把 ODE `solver type` 从 `quick` 改为 `world`，速度高频残差降到 ≤ 1.6×10⁻¹⁰ rad/s，恢复原配置后原振荡复现（原配置→候选→原配置恢复的证据链）。因此交替与求解器的迭代求解方式相关，与控制器无关；内部机理未进一步分析，不声称更细的根因。
- 决定：正式世界 `src/forem_sim/worlds/ur5_empty.world` 使用 `solver type=world`，其余物理参数（步长 0.5 ms、erp 0.2 等）沿用参考；控制器增益不改。iters/sor 元素保留仅作参考值说明（world 求解器不使用）。
- 代价与限制：实时运行下 gzserver 占用 CPU 39%（world）对 45%（quick），未见额外开销；最大仿真速度未能测出（试图取消实时限制未把实时因子提高到 1 以上）。单机械臂固定底座；换更复杂场景（多接触、移动底盘）后需重新确认求解器精度与耗时，不预设可外推。参考 N²M² 世界使用 quick，本决定只适用于 FoReM 的正常基线。
- 附带发现：参考世界把 `<gravity>` 写在 `<physics>` 内，Gazebo 忽略，实际重力是默认 −9.8 m/s²；现改写到 `<world>` 内并保持 −9.8，行为不变。
- 影响：task0.5 及以前用 quick 得到的速度/effort 读数、保持误差数值不再作为正常基线；task1 应使用本配置重测。

## ROOT-DOC-REMOVE-20260930：移除根 doc 兼容入口

- 用户要求：删除旧路径，减少根目录混乱。
- 决定：移除根 doc/README.md、doc/PROGRESS.md 与 doc/agent_logs 兼容入口及空 doc 目录；唯一文档入口为 forem/doc/README.md。
- 依据：根 doc 没有独立任务文档，两个链接指向 forem/doc；双入口使任务目录与日志目录容易混淆。
- 替代方案：继续保留兼容入口；用户已明确选择移除。
- 影响：上文 LAYOUT 决策中保留根兼容链接的安排被本决定取代；历史记录保留原文，现行流程改用 forem/doc 路径。本次仅处理文档旧入口。

## TASK1-BASELINE-20260930：先测正常跟踪，不注入控制误差

- 用户授权：开始编写Task1目标与流程、同步文档，并由Codex决定Task1完成什么任务。本轮仅文档；最新授权允许提前细化Task1计划，不等于运行实验。
- 决定：Task1交付固定底座UR5正常跟踪测量工具与基线报告。五子任务为配置冻结→链路核验→重复运行→分析→独立复核。计划8工况×3次fresh启动及2次高频诊断，参数与数据质量门槛在[流程](tasks/task1/PROCEDURE.md)维护，实施前做限位预检。
- 理由与依据：task0.13已完成环境验收，但仅小幅轨迹与环境检查，不能替代多方向、时间尺度和重复性基线。先分清参考/真实反馈/采样误差，后续才有依据选择受控时延大小。
- 替代方案：立即实现人为指令时延（缺少正常基线）；直接进入IK/SAC/WM（增加混杂与训练成本）。当前均不选。
- 验收：数据来源真实、时间对齐可信、原始数据可追溯、重复差异公开、分析可重算、独立复核完成。不设误差下限，不要求滞后必能辨识，也不预设世界模型收益。
- 影响：取代task1原“待细化”草案；Task0已done，旧review和尚未构建表述仅是历史。参考源码/PID/物理配置不变，新增人为误差与补偿均留给后续任务，编号暂不建立。
- 推荐Codex GPT6.1sol / Claude Sonnet5.5，常规文档与运行low/默认，跨模块测量及复核medium；实际配置另记未知或可核实值。

## EXPERIMENT-CANDIDATES-20260930：建立实验备选入口，区分方案与实施

- 用户要求：继续调研对照工作，新建experiment，每实验任务/流程/结果三文档；随后明确“先写在备选里面”。
- 决定：本轮新增方案全部放experiment/备选/，exp0记录调研与协议草案，exp1–6记录候选设计；各节点三文档并继承递归/模型推荐约定。工程任务仍在tasks，已有Task1不迁移、不覆盖Claude实施。
- 依据：实验方法比较与工程实施职责不同，引用同一run证据避免重复/伪造验收；调研明确动作时延、物理滞后、观测时延和推理延迟对应不同假设。[来源及适用性](experiment/备选/exp0/RESULTS.md)、[公平协议](experiment/备选/exp0/PROCEDURE.md)。
- 替代：立即进入正式实验（用户明确先备选）；把新实验继续散在doc根或直接改Task1（不符合指定目录且影响正在实施的任务）。
- 影响：没有确定算法赢家、未启动新训练/仿真；对照优先级、seed/预算和方法接口是待选方案，不能将本文的组织决定解释为执行授权或收益结论。
- 推荐Codex GPT6.1sol / Claude Sonnet5.5；常规整理low/默认，接口核验medium，研究设计审查high（识别混杂与信息泄漏）；本轮实际配置未知。

## TASK2-DELAY-PLAN-20261006：受控时延机制计划与实验归属

- 用户授权：Task1完成后，依据现有进度和总体安排给出Task2计划、详细流程。本次仅文档，不授权实现或运行。
- 计划决定：下一工程阶段Task2拟采用发送端到控制器之间整条JointTrajectory的固定传输时延，默认关闭，启用零时延作为代理开销对照。现有header.stamp=0和完整两点消息允许整体推迟开始而保留轨迹内容；明确不是电机滞后或SAC逐动作队列。
- 依据：[Task1.10](tasks/task1/task1.10/RESULTS.md)正常基线已done、误差小且位置误差可重复；现有发送器为完整轨迹，不必先改变控制器/物理。控制器参考与原任务参考必须各自留存，不能用执行轴对齐隐藏总时延。
- 组织：工程交付归[Task2](tasks/task2/PROCEDURE.md)；新实验机制协议放原备选exp2内部[exp2.1](experiment/备选/exp2/exp2.1/PROCEDURE.md)，保留exp2编号/历史。仅细化机制阶段，不将exp2预测器比较或全部备选变成已选执行范围。
- 替代与取舍：驱动响应滤波会改变物理动态，暂不选；直接补偿载荷偏移或接SAC/WM不能替代受控时延机制验证，留后续研究。固定80/160 ms与48+2矩阵为待冻结草案，不是已批准实施配置或硬件辨识结果。
- 影响：新增task2.1–2.5计划，Task1数据/冻结七文件及参考仓库不改；没有新实验/训练/预测收益结论。实施仍待用户新授权，不能把本文作为功能实施授权。
- 推荐Codex GPT6.1sol / Claude Sonnet5.5；普通文档和运行low/默认，时间/来源/复核medium，理由是跨模块因果核对。实际本轮模型/强度未知。


## HUSKY-CORE-SENSOR-BASELINE-20261007：Task3核心迁移与Task4估计定位

- 用户决定：删除Task3a/Task3b所有内容，Task3迁移Husky核心，Task4按讨论加入图像/IMU估计。采用最新纠正，未保留旧取消方案目录或全文快照。[SRC-0042](SOURCES.md#src-0042)
- 新Task3：单Husky+UR5模型/控制/末端规划与IK、任务/地图/观测/奖励、普通SAC及受控入口；来源闭包导入forem，原main prior支路不默认启用，差异显式登记。[SRC-0043](SOURCES.md#src-0043) [SRC-0044](SOURCES.md#src-0044)
- 新Task4：同核心上底盘固定双目/IMU原始数据→唯一估计器→估计TF→原策略，建立普通SAC任务基线；定位器/阈值/预算先导后冻结。真值只评价，不混入在线位置/相对目标。[SRC-0045](SOURCES.md#src-0045)
- 理由：用户希望先把核心统一再研究预测辅助决策；TF是接口，需替换真值来源。该路线先验收可运行基线，不需要同时开展所有执行误差研究。
- 替代与取舍：本次不保留旧Task3a/b执行路线；不同时做端到端图像策略、多个定位算法或实机部署，避免改变过多接口；不开展WM训练，留后续明确范围。
- 影响：本轮只写Task3/4父/子三文档与共享记录，未安装/迁移/构建/运行；Task0/1/2实现/数据不改，Git历史不动。Task3按用户要求重新编号为3.1–3.6；Task4为4.1–4.6。[验收](SOURCES.md#src-0046)
- 推荐Codex GPT6.1sol / Claude Sonnet5.5，常规low/默认，跨模块medium；实际模型/强度未知，未委派。

## TASK34-SAC-AND-HANDOFF-20261007

用户补充明确Task4包含IMU/相机位置估计方法设计与SAC重新训练，正式普通SAC基线采用新初始化/新训练状态/新估计观测数据；保持原观测结构与更新公式，不新增端到端视觉策略或旧权重迁移实验。[SRC-0047](SOURCES.md#src-0047)

用户建议查卡尔曼滤波融合：已核查OpenVINS官方EKF/MSCKF与Noetic构建说明，加入Task4.1有限选型核查，与VINS-Fusion优化候选最终只选一个；未宣布算法性能优劣或本项目可用性。[SRC-0048](SOURCES.md#src-0048)

用户要求迁移后详细讲原Husky各条线和用途：Task3.1审计、3.5结果内完整讲解/迁移对照、3.6复核；计数按分类及实际调用证据确定，不依据文件数猜测。[SRC-0049](SOURCES.md#src-0049)

## TASK3-RENUMBER-20261007

用户明确要求新Task3从3.1重新编号，已依次改为3.1–3.6：来源/契约、模型/控制、环境/IK/任务、普通SAC、集成/讲解/交接、独立复核。同步Task4前置和全部当前引用。覆盖先前避开已删除子号的编号选择，范围和任务依赖不变；旧删除事实与核验快照保留为历史，不恢复旧内容。[SRC-0050](SOURCES.md#src-0050)


## TASK3-IMPL-DECISIONS-20261007（Claude，用户授权实施3.1–3.5）

- **TASK3-GRAVITY**：参考bumper宏对全部机器人链接设turnGravityOff，底盘不可驱动。改为：宏参数gravity_off默认false，仅对15个UR5臂/夹爪链接保持开启（底盘/轮子有重力、臂保持参考的无重力）。依据：全链重力关底盘0.0075 m/s（t3.2-motion-r1）；全链重力开则臂PID在随机episode后不稳定、复位失败（t3.5-int-r2/resets-r1/quick1），臂无重力12/12复位成功（t3.5-resets-r2）。替代：全链重力开（不稳定）、改PID增益/容差（未做，会改变控制语义）、保持原样（底盘不可驱动）。影响：混合物理模型；原作者Gazebo行为未知。[SRC-0051](SOURCES.md#src-0051) [SRC-0059](SOURCES.md#src-0059)
- **TASK3-PYTHON310-BUILD**：workspace的catkin cmake-args改为Python3.10（`PYTHON_EXECUTABLE=/opt/python310/bin/python3`），全量重建；原配置备份于logs/task3/t3.2-build3。依据：pybind绑定须与容器运行时Python3.10同ABI。影响：全局构建配置变化，forem_sim无编译产物未受影响（未重跑Task0–2验收）。
- **TASK3-IMPORT-ORDER**：所有使用pybind模块的进程先`import ray`。依据：实测torch先于pybindings时std::bad_cast。[SRC-0052](SOURCES.md#src-0052)
- **TASK3-WORLD-SOLVER**：移动世界沿用task0.7的`world`求解器，使用空地面世界（参考launch默认modulation_tasks.world含门/抓取墙体，参考handle_launchfiles对simpleobstacle映射到空世界）；quick对比保留。待补：Husky上高频交替复测。[SRC-0055](SOURCES.md#src-0055)
- **TASK3-ENV-RECONSTRUCTION**：task_contract是argparse默认+best_defaults[husky_ur5]+main.py键集合的**工程重建**，execute_style=direct、perception_style=base；原作者实际命令行未知。[SRC-0053](SOURCES.md#src-0053)
- **TASK3-POSE-BRIDGE**：用`pose_bridge`取代`gdt_tf`（唯一TF作者，原样本戳，校验，状态话题）；接口为Task4替换来源的入口。
- **TASK3-SAC-PLAIN**：普通基线=`SAC.update_parameters`，入口新写，checkpoint带contract，预算显式；不迁移旧权重/prior。[SRC-0058](SOURCES.md#src-0058)
- **TASK3-CLOCK-RESET**：`/gazebo/reset_simulation`对运行中的RobotEnv进程不受支持（C++ tf监听器保持不连通树）；时钟回退使episode失效；恢复=重启仿真（新进程能否复用原仿真取决于robot_state_publisher何时重新发布臂关节TF：t3.5-clock-dev7内恢复，t3.5-int-r3 150 s内未恢复，故不作为支持的恢复路径）。
- **TASK3-GPU**：用户要求挂GPU；用户删除旧forem-dev，我用`FOREM_GPU=1 run.sh up`重建（nvidia runtime，镜像/挂载不变）。依据：一次性容器先验证`cuda True/4卡`；`t3.5-sac-gpu-r1`通过。
- 未做/待决：
Husky高频(2 kHz)交替复测；门槛事后修订（SRC-0054）。
- 推荐Codex GPT6.1sol / Claude Sonnet5.5，medium；实际Claude Sonnet5.5，强度未知。


## 2026-10-09 Task4暂停后的确定决定

- **TASK4-PAUSE-20261009**：用户明确暂停当前训练，Codex停止r6/r6b并设置live enabled=false；旧freeze/ledger/数据保留，禁止自动重启。替代“继续跑满后再看”未采用，因为seed0已无法满足冻结性能门且用户要求暂停；行政暂停产生的中断不当作算法根因。[SRC0161](SOURCES.md#src-0161) · [SRC0163](SOURCES.md#src-0163)
- **TASK4-POSE-SOURCE-20261009**：用户澄清后接受保留TF/双目IMU建议，真值仅独立评价。TF不是误差消除器；不以删除反馈制造WM必要性。轮速/激光/RGB-D为未实施备选，现有坐标/跟踪错误先修。[SRC0164](SOURCES.md#src-0164) · [SRC0165](SOURCES.md#src-0165)
- **TASK4-SCALE-20261009**：用户授权按服务器确定充分规模，下一版本建议3seed各100万步/replay10万、保留batch/更新公式；这替代2万步作为未来正式目标，尚未写入live配置或启动。三环境并行需隔离改造，是资源部署备选；性能与实际成本先测量。[SRC0167](SOURCES.md#src-0167)
- 文档Codex实际模型/强度未知；推荐GPT6.1sol/Sonnet5.5，复杂因果high、性能/回归medium、文档low。以上决定不授权世界模型训练/奖励语义改造/新增传感器融合。


## 2026-10-09 Task4闭环研究定稿与性能共同职责

- 用户明确惯性估计路线弃用；以普通SAC接入候选动作→后果预测→内部反馈修正→最终SAC动作作为Task4目标。使用Gazebo当前反馈，不制造误差，不要求先证明同类潜态漂移。取代此前保留双目IMU主线的决定；历史结果不删除。[SRC0178](SOURCES.md#src-0178)
- 首轮冻结WM，连续SAC条件分布在采样、logprob和更新中保持一致；实际执行后的观测用于监督，不能泄漏给执行前策略。首轮任务比较与后续适配分别报告。[SRC0179](SOURCES.md#src-0179)
- 预算依最新用户授权与有效协议，保留100万步/原3seed讨论/72小时要求，覆盖范围在4.7核对；旧作者自拟预算切片、额外实验组和固定阈值不作为授权。[SRC0178](SOURCES.md#src-0178)
- 按用户新增要求，性能优化写入根AGENTS并由forem/AGENTS链接：实际GPU核验、端到端测量、有效并行、语义不变、预算可行性与证据登记。该义务不扩大本轮仅文档权限。[SRC0181](SOURCES.md#src-0181)
- 推荐GPT6.1sol/Sonnet5.5，普通文档low/默认、跨模块medium；实际模型/强度未知。本轮不派发实施Agent。交接见[Task4 RESULTS](tasks/task4/RESULTS.md)。


## 2026-10-13 task6范围、task6.3与task7编号

- **TASK6-SCOPE-20261013**：用户明确task6只查Gazebo为何失败。依据task6.1（sim训练评估约0.43、Gazebo训练评估约0.05）与N²M²原文“sim训练、Gazebo零样本测试”的做法，新增task6.3：F0 sim策略在Gazebo零样本评估。主口径Z-A取原论文项目的Gazebo评估配置（上游`evaluation_ray.py`：track执行、评估IK阈值50、time_step 0.02、自由运行）；Z-B取task6.1 §9同口径，使其与R-48只差训练环境。替代方案：只用固定0.1 s窗口评估（不是原论文协议，未采用，需要时另行请示）。[SRC-0248](SOURCES.md#src-0248) · [SRC-0249](SOURCES.md#src-0249)
- **TASK7-NUMBER-20261013**：世界模型任务编号按用户指令定为task7，复用2026-10-12取消的编号（原task7无运行证据，存档保留），覆盖“编号不复用”约定；此前“顺延为task8”作废。方向参照N²M²与SC²-WM“仿真训练、零样本到更真实执行环境测试”（[SRC-0250](SOURCES.md#src-0250)），具体范围待用户确认后建立三文档。
- 文档作者Claude（claude-opus-5-5，强度未知）；推荐Codex GPT6.1sol / Claude Sonnet5.5，配置核对medium、评估执行low。


## 2026-10-16 两阶段结构与文档清理（Claude，用户指令）

- **PHASES-20261016**：现有任务归为阶段一“CBL复现”（task0基础设施、task3迁移、task4 Gazebo SAC基线与首次WM尝试、task5 sim对照训练、task6 Gazebo失败诊断）；task7起为阶段二“世界模型闭环”，从头构建，不沿用task4的WM实现。[SRC-0321](SOURCES.md#src-0321)
- **DOC-DELETE-20261016**：经用户逐项确认，删除task1、task2、experiment/、task4.1–4.6、task4.11–4.13及其agent_logs；根AGENTS删除按日期追加的旧状态段与旧“建议研究顺序”。删除前完整备份（同SRC-0321）。task4.9/4.10因含实际运行结果，删除后从备份恢复保留。替代方案“只加阶段标注不删”未采用：用户明确要求减少干扰。影响：SOURCES中指向已删路径的链接失效，以备份为准；代码、日志、产物未动。
- **TASK7-DIRECTION-20261016**：已定——SC²-WM式初步动作→预测→Δ修正→SAC最终动作；改造RL网络适配；WM只用sim训练、Gazebo测试期适应；先完成task5.5基线。网络结构（RSSM提议）、地图处理等Q1–Q9待用户确认，见[task7](tasks/task7/TASK.md)。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，low/默认。


## 2026-10-16 task7设计（Claude，用户决定）

- **TASK7-DESIGN-20261016**：自写理想执行训练环境（随机立方体，10×10 m）；Husky+UR5；方案一：训练只输出底盘(v, ω)，验证侧另写转换层；360°全景扫描，训练与验证同一传感器模型；ManiSkill只作验证（零样本＋测试期适应），不用于训练；每步闭环为初步动作→世界模型潜在空间预测→Δ→ψ更新潜在状态→最终动作→视情况更新世界模型。替代方案：沿用N²M² sim＋Gazebo（上午草案，被替换：感知差距与速度问题）；ManiSkill训练（用户认为成本高）；全向动作抽象（验证时有结构性不可实现动作，未采用）。依据[SRC-0327](SOURCES.md#src-0327)–[SRC-0332](SOURCES.md#src-0332)。未定事项U1–U15见[task7 TASK](tasks/task7/TASK.md)。只写文档，未实施。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。


## 2026-10-16 task7：子目标决策与运动学前瞻（Claude，用户决定）

- **TASK7-SUBGOAL-20261016**：上层改为SC²-WM式选位姿子目标，下层执行器以(v, ω)朝子目标执行，不再按速度×固定间隔决策；候选首版用简单规则从360°扫描生成，不训练航路点预测器；强化学习按半马尔可夫决策处理。替代：逐步输出(v, ω)（单步变化太小、前瞻信息弱，未采用）；仿照CWP训练预测器（留作后续）。[SRC-0337](SOURCES.md#src-0337)
- **TASK7-LOOKAHEAD-20261016**：前瞻闭环按用户大方向：VCM式记忆形成当前状态→SAC初步子目标→仿真器运动学模拟底盘移动与IK→差异反馈→SAC重新生成→真实执行；沿用CBL/N²M²“先移底盘、再求IK、再执行”的顺序。SC²-WM代码中的全部候选并行前瞻作为参考，首版不采用。运动学前瞻在验证中不含物理偏差，是否加学习修正项待定（U21）。[SRC-0338](SOURCES.md#src-0338)
- 只写文档，未实施。文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。


## 2026-10-19 task7：框架确定（Claude，用户决定）

- **TASK7-FRAMEWORK-20261019**：①不在10 Hz做学习决策；一次决策选一个前瞻点（子任务），子任务内目标不动，执行器内部仍按检查点做IK/碰撞检查。②候选前瞻点首版用规则生成；以后可借用SC²-WM“热力图→扇区取峰值→去障碍→合并→取前k”的结构自训练生成网络，不直接用其权重。③对每个候选点并行评估多条路径，按固定评分（精确运动学/IK/碰撞）取各点最优路径，其结果作为该候选的特征；在候选点之间由离散SAC选择；执行器执行被选点的最优路径，走一段再重规划路径，不重选点，直到到达/超时/失败。④全部候选同时预测与修正，不保留“先初选一个再修正”（用户同意建议b，改变TASK7-LOOKAHEAD-20261016中“首版不采用全部候选并行”的安排）。⑤精确信息（路径模拟结果）放进候选特征，所有组都有；学习的世界模型f_p只经零初始化门控残差偏置层进入，输出先detach（照SC²-WM代码）。⑥f_p预测到达后的360°扫描，只用实际执行候选的真实结果监督。⑦训练分阶段：基线SAC→f_p监督预训练→冻结基线、训练偏置层与输出头（用户同意建议c）→对比。⑧暂不做“结果摘要回送前瞻点生成网络”的子目标环。
- 替代方案及未采用原因：SAC直接输出连续底盘位移（差速底盘不能到达任意位姿，且偏离选候选点结构）；上下两层都学习（非平稳）；每个Δt做TD-MPC式序列规划（与选点不在同一层；理想SIM中路径层是精确模型采样MPC，不能称为TD-MPC）；先初选一个候选再修正（两遍选择带来动作概率定义问题，K≤13时全部候选并行代价可接受）。
- 依据：[SRC-0359](SOURCES.md#src-0359)（用户决定）、[SRC-0358](SOURCES.md#src-0358)、[SRC-0334](SOURCES.md#src-0334)、[SRC-0335](SOURCES.md#src-0335)（SC²-WM代码）。影响：task7 TASK §2.3、§2.7–§2.9、§3（U3、U4、U5、U16、U20、U21、U22收敛）、§4对照组；新增准备子任务task7.4–7.12。各参数均未冻结；只写文档，未实施。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。


## 2026-10-19 task7.4：任务定义与段中途失败处理（Claude，用户决定）

- **TASK7-TASKDEF-20261019**：①同步（末端按时间前进，底盘须跟上，N²M²/CBL式）与不同步（底盘与机械臂可以互相等）两种任务变体都做。②成功＝末端到达终点且整个回合失败次数为0，沿用N²M²/CBL严格口径，计数单位改为检查点/决策，并新增机械臂与环境碰撞。③段中途失败：停在最后可行检查点、记一次失败、回合继续，累计F次终止。④不屏蔽路径评估不可行的候选。替代方案：只做一种变体；第一次失败即终止（早期样本过少）；停下只算中止不算失败（理想SIM中几乎没有失败信号）；屏蔽不可行候选（训练中失败信号消失）。依据[SRC-0360](SOURCES.md#src-0360)、[SRC-0361](SOURCES.md#src-0361)。数值E1–E9未定，见[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md)。只写文档，未实施。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。


## 2026-10-19 task7.4：接口问题与设计原则（Claude，用户决定）

- **TASK7-INTERFACE-20261019**：①总原则：设计要符合SC²-WM的基本思想。②现在只考虑训练用sim，验证仿真（ManiSkill）接口与task7.12暂缓。③路径评估的碰撞检查只用扫描累积的局部地图，不用真值地图；真实碰撞由环境真值判定（I1）。④f_p只用到达候选点的样本监督（I2）。替代：用真值地图做路径评估（候选特征含特权信息，f_p预测未见区域的作用被替代）；中途停下样本以实际位姿为条件监督f_p（训练与决策输入不一致）。依据[SRC-0362](SOURCES.md#src-0362)。只写文档，未实施。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。


## 2026-10-19 task7.4：训练与sim内评估协议（Claude，用户决定）

- **TASK7-PROTOCOL-20261019**：①训练阶段0–3（环境验收→基线SAC→f_p预训练→冻结主干训练偏置层与输出头）。②对照组G1规则选点、G2基线续训（与G4同预算同可训练参数）、G3容量对照、G4完整版本、G6 sim内未见场景测试期适应；G5联合训练先不做。③预算按决策次数计。④地图由mapgen生成立方体、椭圆柱体这样的地图（替代Claude“训练地图在sim内现场生成”的推荐）。依据[SRC-0363](SOURCES.md#src-0363)。数值与地图细节待定。只写文档，未实施。
- 2026-10-19晚措辞更正（Claude，据[Codex回复](agent_logs/task7/20261019-claude-codex-sync.md#codex回复)第5条）：②中“G2与G4同可训练参数”不准确。G2与G4阶段3同预算、同冻结主干、都训练输出头，但G4另训练ψ，参数数量多一组ψ；容量差异由G3控制。决定本身不变。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。


## 2026-10-19 task7.7：mapgen地图范围（Claude，用户决定）

- **TASK7-MAPS-20261019**：本轮只由mapgen的A类程序生成**只含长方体**的地图（兼容Gazebo），不加椭圆柱体；稀疏、标准两档，每档验证50张、测试100张；B类语义场景本轮不做。取代TASK7-PROTOCOL-20261019第④项中的“椭圆柱体”。未定：训练用法、未见场景与G6所用场景。依据[SRC-0364](SOURCES.md#src-0364)。只改需求文档，未生成地图。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，low到medium。


## 2026-10-19 task7.7：观测与底盘碰撞（Claude，用户决定）

- **TASK7-OBS-20261019**：①照SC²-WM用360°全景深度观测（不用RGB），取代原“360°单层扫描”。②局部栅格以机器人为中心，从本回合累积全局栅格中裁出，0.05 m/格、128×128、两通道（是否观测到、最高高度）。③所有障碍都算挡底盘，不允许从上方驶过（URDF车体离地约0.132 m）。替代：单层扫描（看不到低矮障碍与障碍高度）；三层虚拟水平扫描；按URDF模拟两台VLP-16（贴近真机，但偏离SC²-WM全景观测）。依据[SRC-0372](SOURCES.md#src-0372)、[SRC-0373](SOURCES.md#src-0373)。安装高度、分辨率、累积与自遮挡细节（S1–S5）未定。只写文档，未实施。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。


## 2026-10-19 task7.8：VCM方案（Claude，用户决定）

- **TASK7-VCM-20261019**：VCM照SC²-WM：注意力记忆（最近4次决策，相对几何与步差编码零初始化，时间衰减）＋门控融合＋GRU状态递推；状态用未修正的递推，修正只作用在候选特征上；首版只用SAC Critic损失训练，阶段2、3与测试期适应中冻结；末端未来路线以栅格通道＋向量输入。替代：只用CNN＋GRU（偏离SC²-WM）；加辅助重建损失（留作以后）；路线只用向量。依据[SRC-0374](SOURCES.md#src-0374)、[SRC-0375](SOURCES.md#src-0375)。只写文档，未实施。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。


## 2026-10-19 task7.5(B)：末端坐标、IK与失败判定（Claude，用户决定）

- **TASK7-ENV-B2B3B11-20261019**：①B2：末端路线与成功判定用夹爪TCP，IK经固定变换在法兰tool0求解。②B3：IK用UR5解析多解，按上一有效解选最近分支；task7.6核对FK一致并计时后最终确认，DLS仅备选。③B11：失败只按真值判定——局部栅格只影响路径评分，只有IK失败或真值碰撞才停下记失败；不设安全层（取代父TASK §2.9原安全层）。替代：任务全用tool0或gripper_base_link；DLS或cuRobo；“看见就停”（局部栅格误判时会记未发生的失败）或独立安全层。依据[SRC-0377](SOURCES.md#src-0377)、[SRC-0378](SOURCES.md#src-0378)。只写文档，未实施。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。


## 2026-10-19 task7.5(B)：任务采样、地图大小与其余待定项（Claude，用户决定）

- **TASK7-ENV-REST-20261019**：用户“都按你推荐的走”。①地图保持10×10 m；起点在全图空闲区随机采样；终点距起点0.5–8 m、高度0.7–1.15 m；生成时做可达检查；路线真值A*（B12）。②不同步变体路径族含“匀速联动”与“先到位再推进”两种s分配（B7）。③未知格按空闲判定，另加两项风险特征（B6）。④墙厚0.15 m放在界内（B1）；自碰撞允许对按几何重定（B5）；关节限位查来源（B4）；决策超时＝规划时长×系数（B10）；B8、B9、B13、B14交task7.6。替代：起点固定原点、终点0.5–4.5 m（每回合仅3–6次决策）；地图加大到15×15或20×20 m（留待回合仍过短时）；未知格当占据（易卡住）或当空闲不加特征。依据[SRC-0381](SOURCES.md#src-0381)。只写文档，未实施。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。


## 2026-10-20 task7.4：合同缺口7–11（Claude，用户决定）

- **TASK7-CONTRACT-20261020**：用户“7–11都按你的推荐定”。⑦到达＝路径计划终点走完（底盘到位，且不同步s＝s_k、同步计划时长走完）；同步原地候选持续到末端走到当前底盘位姿IK可达的最远进度；决策超时＝决策开始时所选最优路径的计划仿真时长×κ，整次决策固定、不用墙钟（澄清TASK7-ENV-REST-20261019④）。⑧到达路线终点即terminated，有历史失败记“到达但非严格成功”；每检查点按“失败→到达终点→到达c*/决策超时→卡住→D_max/T_max截断”顺序判定，终止优先于截断，T_max只在决策边界检查。⑨全部路径不可行的候选按分层排序选路径（可行优先，再首个失败越靠后，再U25评分），特征按“首个预测失败点之前的前段”计算，无空值；G1无可行候选时用同一排序。⑩G3用随机初始化后冻结的f_p输出替代h_k。⑪归一化累计失败数n_f/F与卡住计数m/M进入观测。替代：⑦固定等待时长或同步不设原地候选，超时按重规划重算或按墙钟；⑧有失败后继续到卡住/超时；⑨只用连续评分加罚分，或只走可行前段不记失败；⑩零输入、噪声、同状态打乱h_k；⑪只靠VCM记忆。依据[SRC-0392](SOURCES.md#src-0392)。κ、F、M等数值待定。只写文档，未实施。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。

- **TASK7-ENV-DETAIL-20261020**：用户“①②③都按你的推荐定”。①终点距离0.5–8 m指底盘起始位置到TCP终点的水平距离。②终点姿态：TCP接近轴（gripper_base_link的x轴）水平、指向路线最后一段的水平方向，手指沿水平方向开合（本项目工程设计，非沿用N²M²）。③未知格风险特征：比例＝最优路径扫过区域（底盘轮廓与机械臂连杆地面投影）中未知格的格数比例；距离＝扫过区域到最近未知格的最小距离，无未知格时取3.2 m；局部栅格范围外按未知处理。替代：①从末端起点量或量三维距离；②手指沿竖直方向开合；③按检查点计比例、只算底盘轮廓。依据[SRC-0393](SOURCES.md#src-0393)。只写文档，未实施。
- 文档作者Claude（claude-opus-5-5），推理强度未知；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。
