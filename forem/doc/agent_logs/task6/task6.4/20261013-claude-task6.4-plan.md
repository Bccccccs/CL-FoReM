# TASK6.4-PLAN：按N²M²原论文方法对task5 A/B做Gazebo零样本评估（流程与派发提示词）

- Agent：Claude（claude-opus-5-5，推理强度未知）
- 状态：done（文档交付，尚未实施）；2026-10-13
- 用户要求：“按照原论文里的gazebo方法配置呀，复现不了n2m2那篇论文的吗”“评估做过了吗”“那去写个计划做一下”（[SRC-0257](../../../SOURCES.md#src-0257)）。
- 授权边界：本轮写文档；执行由用户派发。不改源码、不运行。

## 执行记录与证据

- 核查`results/task5/t5.{1,2}-eval-r1/commands.json`：全部`--eval_execs sim`；`t5.2-smoke-r1`实验状态`eval_execs ["sim"]`。task5 A/B从未在Gazebo评估。
- 核查上游`handle_launchfiles.py`（PR2启动30 s后物理步长设0.002 s）、`utils.py` L247–251（`--eval_execs gazebo`使`init_controllers`为真）、`robot_env.cpp` L240（TIAGo强制direct）。
- 现场：`forem-t5-pr2`、`forem-t5-husky`各运行roscore＋analytical launch＋move_group（可能属于task5 D21），两容器为bridge网络。
- 默认选择（用户未答，工程选择）：分阶段（先simpleobstacle，A其余8任务须Claude放行）；运行位置须与task5 D21隔离（等待或新容器）。
- 改动文件（仅文档）：新建`tasks/task6/task6.4/{TASK,PROCEDURE,RESULTS}.md`；更新task6父三文档、`PROGRESS.md`、`SOURCES.md`（SRC-0257）。

## 派发提示词（交用户转给Codex；尚未派发）

```text
你是Codex，执行FoReM项目的task6.4（按N²M²原论文方法对task5 A/B做Gazebo零样本评估）。工作区 /home/ybc/projects/CL-FoReM。

先读：根AGENTS.md、forem/AGENTS.md、forem/doc/PROGRESS.md末尾、forem/doc/tasks/task6/task6.4/{TASK,PROCEDURE,RESULTS}.md、
父forem/doc/tasks/task6/TASK.md、task6.3 RESULTS末尾“Claude复核R2/R3”、task5的task5.0/5.1/5.2 RESULTS（环境、启动脚本与sim评估）、
task6.2 RESULTS中r4（0.002 s复位失败诊断）与G-D9，以及forem/doc/SOURCES.md的SRC-0237、0238、0243、0249、0254、0256、0257。

授权范围：按task6.4 PROCEDURE §1→§3执行，阶段一（A、B的simpleobstacle各50 episode）完成后RESULTS标“阶段一review”并停止，等Claude决定是否放行§4阶段二。只评估不训练。
允许：评估包装脚本（启动、记录、D21续跑拼接）；B仅在出现task6.2 r4同类复位失败时改用0.0005 s／2000 Hz。A（PR2）用上游缺省track，B（Husky）用--execute_style direct。
禁止：改上游或Husky原版的策略/观测/奖励/任务代码、固定每步时长、增加任务或条件、训练。
不得停止或干扰task5的forem-t5-pr2、forem-t5-husky中现有进程（可能是D21补跑），不得在仍有其他任务ROS运行的容器里再起roscore；按PROCEDURE §1在“等待”与“同镜像新容器”之间选择并记录理由。不得触碰forem-t6-husky-gz及G-B训练。

在PROGRESS登记接手，独立日志写forem/doc/agent_logs/task6/task6.4/YYYYMMDD-codex-task6.4.md，结果写task6.4 RESULTS。
遇到PROCEDURE“异常处理”所列情况立即停止，写RESULTS交Claude。
推荐GPT6.1sol，§1–§2 medium，§3 low/默认；在日志中如实记录实际模型/强度（无法核实写未知）。
```

## 交接

- 已完成：task6.4三文档与全局记录同步。
- 未解决：A阶段二（8任务）待阶段一后由Claude放行；B其余任务未纳入。
- 下一步：用户派发Codex执行；阶段一完成后Claude复核。

## Agent模型与推理强度

- Codex推荐：GPT6.1sol；§1–§2 medium（ROS/Gazebo启动链与容器隔离），§3–§5 low/默认。
- Claude推荐：Sonnet5.5；复核medium。
- 实际：本文档由Claude claude-opus-5-5撰写，推理强度未知。

## 任务归属与委派

- task6.4，父task6；三文档见`tasks/task6/task6.4/`。
- 执行委派给Codex（用户派发），Claude负责门槛、复核与父汇总。
