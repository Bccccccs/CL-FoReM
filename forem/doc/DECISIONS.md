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
