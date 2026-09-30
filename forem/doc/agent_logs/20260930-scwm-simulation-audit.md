# SC²-WM 仿真与执行偏差审计

- Agent：Codex /root；核对时间：2026-09-30T09:13:29+08:00。
- 任务：PH4-WORKSPACE-LAYOUT跟进，用户要求恢复旧工作区并研究SC²-WM控制偏差仿真。此记录为当前工作事实，不延续旧PH0–PH8路线决策。
- 官方源码：scwm/，HEAD f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b；本次只读，未运行Habitat。

## 核对结果

1. run_r2r/r2r_vlnce.yaml:4–12为Habitat Sim-v1、ACTION_SPACE_CONFIG v0、FORWARD_STEP_SIZE0.25、TURN_ANGLE15、ALLOW_SLIDING True；不是UR5机械臂物理仿真。
2. habitat_extensions/nav.py:178–191把转角量化到turn_unit；:195–225训练分支设置朝向并将距离拆成固定前进步；评测分支含转向、固定步推进、碰撞/tryout。整数距离步数可能造成目标位移与实际移动不一致，但不是关节驱动增益/时延模型。
3. habitat_extensions/habitat_simulator.py:62–95 的step_without_obs直接agent.act并读state，step_world物理推进代码在该方法里注释。这个事实限该方法，不能推出整个Habitat所有物理功能关闭。
4. run_r2r/iter_train.yaml:48的loc_noise=0.5，在models/graph_utils.py:161–176是图节点最近位置匹配的距离阈值，不是高斯控制噪声；ghost_aug另有随机位置增强，但该配置ghost_aug=0.0。
5. 全文/已读配置未找到机械臂、关节电机、执行增益或时延注入；原论文主张的是视觉语言导航的潜在状态漂移校正。不能称其证明了机械臂控制误差补偿，也不能把ALLOW_SLIDING叫轮胎打滑。
6. README说明Matterport3D场景与预训练权重需另外获取；clone不等于仿真可运行。没有安装Python3.7/Habitat0.2.1依赖，也没有使用其数据/权重。

## 对Husky的建议（设计草案，尚未实施）

- 用户提出“先建立可控执行偏差，再验证WM”的顺序可取；但同类偏差须匹配移动操作。优先沿用Gazebo+UR5+现有joint controller，在命令→关节实际响应之间建立独立执行层。Habitat可用于导航复现，不直接替代机械臂仿真。
- 最小误差族先选一种可辨识、持续的关节跟踪滞后/指令时延，示例一阶模型q_dot=clip((q_cmd_delayed-q_actual)/tau, joint_velocity_limits)。这是我们另行提出的模型，不是SC²-WM实现，参数需依据现有Gazebo/实机响应校准；白噪声不能保证可预测。
- 同时记录q_cmd/q_actual、目标/实际夹爪位姿、时间戳；观测读取实际状态，不能回填IK目标当执行结果。动作饱和、IK求解偏差、低层执行误差和感知误差分别记；不混淆。
- 先验证误差层关闭恒等、开启有命令—执行差且量纲/关节边界正确；再评测重训的SAC/同信息历史对照能否吸收，并检验准确预测信息能否改善任务。产生误差只是研究条件，不保证WM有必要或能改善。
- Husky恢复源版本待用户选定，不在旧代码上继续堆新功能。当前不部署仿真、不装依赖、不改控制器、不重训。

## 实际命令与限制

- rg/sed/cat核对scwm的YAML、动作类、simulator wrapper、GraphMap和主脚本；各有效文件读取成功。一次cat不存在habitat_extensions/config/vlnce_task.yaml与克隆中尚未有HEAD的nmoma返回错误；后续克隆完成后git状态/HEAD复核全部成功。
- 原文网页：https://arxiv.org/html/2608.07548；官方仓库：https://github.com/sunrise-yuze/SC2_WM。
- 两个Habitat0.2.1 raw源码链接web返回cache miss，未据此确认底层全部行为。
- Git克隆状态新实测见workspace-layout日志。原Husky代码、进程、实验结果均未清理。
- 恢复待选项：收到时的Husky移植原样快照1ccedd0（不是移除Husky的纯上游N²M²）；或研究前但保留P0语义/固定IK修复的节点（待精确定位）。根工作区备份见/tmp/cl-forem-reset-backup-path所指外部目录。
