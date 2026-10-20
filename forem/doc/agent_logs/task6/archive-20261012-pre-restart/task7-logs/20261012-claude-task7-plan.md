# TASK7-PLAN：Task5 B改在Gazebo中训练（流程制定）

- Agent：Claude（claude-opus-5-5，推理强度未知）。状态：done（文档交付）。日期：2026-10-12。
- 用户要求：把Task5 B的sim换成Gazebo训练，判断Task4.8失败是否源于Gazebo以外的设置；列出Task5与Task4.8的训练设置差异。用户选择N个隔离Gazebo实例；新建task7，世界模型闭环顺延为task8。见[SRC-0227](../../SOURCES.md#src-0227)。
- 已读：B的launch/生效配置、Husky快照`main_ray.py`、`ray_utils.py`、`custom_sac.py`、`modulation/utils.py`（env_creator、launch_ros、init_controllers、MaxCloseSteps）、Task4.8的`plain.yaml`、`sac.yaml`、`task_contract.yaml`、`scwm_sac.py`、`sac.py`、`scwm_train.py::run_eval`、task4.8.1隔离做法；只读核查两个容器的ray/Gazebo/ROS版本、主机64核/251 GB。
- 中期数据（09:03）：A 64.9万步，评估最高0.82、60万步0.74；B 59.9万步，52.5万步0.82；Task4.8 plain最终0/15。
- 产出：`forem/doc/tasks/task7/{TASK,PROCEDURE,RESULTS}.md`、SRC-0227、PROGRESS task7段、交接提示词。
- 关键决策：T7-D1 Gazebo终止阈值按代码默认500；T7-D2只在task7工作区副本的env_creator加worker→实例映射；T7-D3目标N=20，CPU不够则停下报告；T7-D4主指标为与B相同的训练中评估，最终评估只做simpleobstacle 50 episode。
- 更正：本会话中曾向用户说Task6仍卡在max_close_steps决策，实际另一Claude会话已于09:11做出R2放行（SRC-0226），已向用户更正。
- 没有修改代码，没有启动容器或运行任何训练；task5/task6未受影响。
- 下一步：用户派发Codex执行task7；Claude负责复核。用户随后提出把task6扩成训练参数对照组，待用户确认设计后另行登记。
