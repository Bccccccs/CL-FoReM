# Husky原项目执行链路只读核查

时间：2026-10-06T21:25:56.049066+08:00；负责人Codex /root；状态done（源码说明交付，非运行验收）。实际模型/强度未知。用户问原项目Husky如何使用机器人；范围为只读启动/动作/反馈源码核查，无运行、无参考源码修改。

证据：husky/src/modulation_rl/src/robot_husky.cpp:34为eff_joint_traj_controller/follow_joint_trajectory ActionClient，:90起组装轨迹、当前时间header并sendGoal；robot_env.cpp:239仅非analytical执行时发臂/底盘命令，:283发布Twist，:294每步一个关节目标time_from_start=exec_duration；:396区分gazebo/world/sim。gazebo_world/husky_ur5/robot_config.yaml:15配置/cmd_vel。gazebo_world/husky_ur5/n2m2_husky_empty_world.launch加载Gazebo、spawn_husky、effort轨迹控制器。husky/src/husky_ur5/launch/inc/load_ur5.launch.xml:10为EffortJointInterface；config/ur5_controllers.yaml为effort_controllers/JointTrajectoryController。husky/src/husky/husky_description/urdf/husky.urdf.xacro:243加载gazebo_ros_control。

尤其husky/src/husky_ur5/launch/ur5_bringup.launch开头明确说明：本文件为Gazebo虚拟UR5、类似但不等于ur_robot_driver，不模拟控制柜，不能据名称认定使用真实UR驱动。

反馈限制：robot_env.cpp:257附近perception_style=base仅更新底盘、all用state monitor更新全部、none保留目标；:486另取非解析环境实际末端位姿。因此不能不看配置就把原joint_values当真实执行反馈。原项目有world抽象分支，但本次找到的Husky启动为Gazebo，不证明Husky实机链路已接通或曾成功运行。sim解析分支不发控制器命令；显示Gazebo不等于动作走物理控制。

交付为当前参考源码解释，不是恢复前容器或历史训练模式核验。查找/读取完成，未仿真/训练/提交/推送。无本任务运行PID。后续若需确定某次历史运行模式，需其配置及日志，不能只凭代码支持分支推断。推荐Codex GPT6.1sol / Claude Sonnet5.5，medium（跨启动/动作/反馈核对），推荐不等于实际。
