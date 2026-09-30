# 决策记录

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
