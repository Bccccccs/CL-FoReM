# TASK6.3-PLAN：sim训练策略的Gazebo零样本迁移（流程与派发提示词）

- Agent：Claude（claude-opus-5-5，推理强度未知）
- 状态：done（文档交付，尚未实施）；开始2026-10-13T15:01+08:00
- 用户要求：“世界模型用task7，然后6里面验证一下sim的训练结果是否可以迁移到gazebo中，配置应该参考原论文项目对gazebo的测试，然后现在6只是验证gazebo为什么失败吧”（[SRC-0248](../../../SOURCES.md#src-0248)）。
- 授权边界：本轮只写文档；不改源码、不运行任何评估或训练；task6.2的G-B训练不触碰。

## 执行记录与证据

- 只读核查：task6.1 RESULTS §7–§10与R4；task6.2 RESULTS §5、R5及Codex接回；`t62_status.py`（14:52，33000步，无评估输出）。
- 原论文核查：N²M² arXiv HTML Sec. IV-I/IV-J（WebFetch摘录）；SC²-WM本地PDF附录训练细节与附录E（pdftotext）。
- 上游代码核查：`mobile-rl/scripts/evaluation_ray.py`、`modulation/utils.py`、`envs/robotenv.py`、`envs/eeplanner.py`、`src/robot_env.cpp`；本项目`forem/config/task3/task_contract.yaml`、`scripts/{scwm_env,task3_env,eval_task6_final}.py`、`src/modulation_rl/src/robot_husky.cpp`。
- 关键发现：上游Gazebo评估用`execute_style track`、`ik_fail_thresh_eval 50`、`time_step 0.02`、自由运行；Husky迁移栈契约为`direct`、`ik_fail_thresh 20`（task6.1 §9 Gazebo侧即此口径）。原论文Gazebo为异步30–70 Hz，不是固定0.1 s。
- 改动文件（仅文档）：新建`tasks/task6/task6.3/{TASK,PROCEDURE,RESULTS}.md`；更新`tasks/task6/{TASK,PROCEDURE,RESULTS}.md`、`PROGRESS.md`、`DECISIONS.md`、`SOURCES.md`（SRC-0248–0250）。

## 派发提示词（交用户转给Codex；尚未派发）

```text
你是Codex，执行FoReM项目的task6.3（sim训练策略的Gazebo零样本迁移）。工作区 /home/ybc/projects/CL-FoReM。

先读：根AGENTS.md、forem/AGENTS.md、forem/doc/PROGRESS.md末尾“task6.3新增”一节、
forem/doc/tasks/task6/task6.3/{TASK,PROCEDURE,RESULTS}.md、父forem/doc/tasks/task6/TASK.md、
task6.1 RESULTS的§9与R4、forem/doc/SOURCES.md的SRC-0246、SRC-0248、SRC-0249。

授权范围：按task6.3 PROCEDURE §1→§5执行。只允许改scripts/eval_task6_final.py（新增--execute_style、--ik_fail_thresh两个可选参数，缺省行为不变）并新增对应单元测试；只做评估，不训练。
不包括：Task4.8策略的Z-A评估、固定0.1 s窗口、其他执行因素拆分、改物理步长/奖励/观测/任务、追查场景分叉种子、任何世界模型工作。
不得触碰task6.2的容器forem-t6-husky-gz和其中的G-B训练；不停止任何非本任务进程。

在PROGRESS登记接手，独立日志写forem/doc/agent_logs/task6/task6.3/YYYYMMDD-codex-task6.3.md，结果写task6.3 RESULTS。
遇到PROCEDURE“异常处理”所列情况立即停止，写RESULTS交Claude。完成§5后RESULTS标review，不标done。
推荐模型GPT6.1sol，§1–§2 medium，§3–§5 low/默认；在日志中如实记录实际模型/强度（无法核实写未知）。
```

## 交接

- 已完成：task6.3三文档、父文档与全局记录同步。
- 未解决：task7三文档尚未建立（待用户确认范围）；固定0.1 s窗口、Task4.8策略的Z-A评估未纳入，需要时请示用户。
- 下一步：用户派发Codex执行task6.3；Claude在RESULTS为review后复核。

## Agent模型与推理强度

- Codex推荐：GPT6.1sol；§1–§2 medium（跨Python/C++评估语义核对），§3–§5 low/默认。
- Claude推荐：Sonnet5.5；复核medium。
- 实际：本文档由Claude claude-opus-5-5撰写，推理强度未知。

## 任务归属与委派

- task6.3，父task6；三文档见`tasks/task6/task6.3/`。前置task6.1 done。
- 执行委派给Codex（用户派发），Claude负责复核与父汇总。
