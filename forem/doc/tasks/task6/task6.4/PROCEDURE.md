# task6.4 按N²M²原论文方法对task5 A/B做Gazebo零样本评估 — 详细流程

状态：**尚未执行（2026-10-13）**。目标、范围、验收见[TASK](TASK.md)；结果填写在[RESULTS](RESULTS.md)。

## 递归规则声明

本节点遵守根AGENTS的递归三文档规则：task6.4及今后拆出的task6.4.M都必须各有TASK、PROCEDURE、RESULTS三份文档。父节点[task6](../PROCEDURE.md)负责顺序、依赖与汇总；本节点结果以本RESULTS为准。执行者只更新本节点文档和自己的日志`agent_logs/task6/task6.4/`；父RESULTS与PROGRESS的汇总由Claude维护（执行者可追加自己产生证据的SRC条目）。执行者自报完成不能当作通过，须经Claude复核。当前无子节点。

## 输入与依赖

- 策略：`results/task5/t5.1-train-s40/local_model/checkpoint-1000`（A）、`results/task5/t5.2-train-s40/local_model/checkpoint-1000`（B）。
- sim对照：task5的`t5.1-eval-r1`、`t5.2-eval-r1`及D21补跑后的最终sim结果（以task5.3复核为准；未复核的数值标“待task5.3”）。
- 代码与镜像：task5.0建立的A、B两套环境（镜像、`build/task5/`下的工作区、`ws_husky`等）。不改上游或Husky原版源码。
- 容器：task5的`forem-t5-pr2`、`forem-t5-husky`目前各有一套analytical ROS（可能属于task5 D21补跑）。**不得停止或干扰。**
- 不得触碰task6.2的`forem-t6-husky-gz`。

## §1 开工与隔离方案

（2026-10-14 Claude R1：T64-D1 A与B解耦、A独立推进；T64-D2 B复用task6.2已准备的Gazebo依赖（只读挂载，不重建），并用`handle_launchfiles.start_launch_files`包装启动。详见RESULTS“Claude复核R1”。）

1. 登记PROGRESS与独立日志。记录主机CPU、GPU、各容器进程，确认两个task5容器中的ROS进程属于谁（task5 D21日志、PID启动时间）。
2. 选择运行位置（二选一，记录理由）：
   - **(a) 等待**：对应task5容器中的D21工作结束、且其进程已由所属任务清理后，在该容器中运行；
   - **(b) 新容器**：用同一镜像新建`forem-t6.4-pr2`、`forem-t6.4-husky`，挂载与task5容器相同的只读构建与模型目录，结果/日志写`results/task6/`、`logs/task6/`。须证明网络与ROS master和task5容器隔离（容器为bridge网络，各自11311）。
   不得在仍有其他任务ROS运行的容器内再起roscore。
3. 重算A、B checkpoint文件和所用评估入口（`evaluation_ray.py`、`modulation/{utils,evaluation,handle_launchfiles}.py`、`robot_env.cpp`）的sha256，与task5记录比对。
4. 核对上游`launch_ros`/`start_launch_files`在`--eval_execs gazebo`下的启动链（roscore、Gazebo world、控制器、move_group、costmap），以及task5包装脚本（如`build/task5/t52_r2_smoke.sh`）中手动启动analytical的部分在Gazebo评估中应如何替换。核对每个阶段一、二任务对应的world文件存在。

## §2 Gazebo就绪与冒烟

run-id：`t6.4-smoke-A`、`t6.4-smoke-B`。

1. 按上游方式启动Gazebo评估所需全部节点，记录物理步长、`max_update_rate`、控制器列表与状态。
2. 冒烟：`simpleobstacle`，`--nr_evaluations 3`。检查：底盘运动、episode正常终止、评估日志有“Eval ep”完成行、指标文件写出、进程退出后无遗留。
3. A为PR2：上游在启动30 s后把物理步长设为0.002 s，照原样。
4. B为Husky：先按Husky原版启动器设置运行。若复位失败（“Could not set start pose”或`resetArm failed`，同task6.2 r4），停止该次冒烟，改用0.0005 s／2000 Hz（task6.2 G-D9的实现方式），新run-id `t6.4-smoke-B-r2`重做；证据保留。其他异常停止交Claude。
5. 记录单个episode的墙钟与步数，据此估算阶段一、二总耗时。

## §3 阶段一正式评估

- run-id：`t6.4-A-simpleobstacle`、`t6.4-B-simpleobstacle`。
- 命令：上游`evaluation_ray.py --evaluation_only --eval_execs gazebo --eval_tasks simpleobstacle --model_file ... --num_gpus 0`，A加`--env pr2`，B加`--env husky_ur5 --execute_style direct`；其余用上游缺省（`nr_evaluations 50`、`eval_seed 999`）。准确命令写入`commands.json`。
- 超过100000步的断言：按task5 D21处理（确定性核查该种子再次超限→记失败→从下一种子`--eval_seed`续跑并`--nr_evaluations`补足→拼接为50个），保留每段日志。
- A与B在不同容器中可同时运行；启动前读主机CPU，与G-B、task5 D21合计不得超过56核。
- 完成后写阶段一小结，RESULTS标“阶段一review”，**停止**，交Claude决定阶段二。

## §4 阶段二（Claude放行后）

A其余8个任务，每任务50个episode，逐任务记录命令、退出码、耗时；D21同§3。`bookstorepnp`若遇task5中同类采样失败，按task5 D10记N/A并说明。

## §5 汇总

1. 由原始指标文件统计每个任务的成功率（上游`success`口径；另列goal_reached、IK失败、碰撞、episode长度），D21拼接后分母50。
2. 对照表（见TASK交付）；原文数值引用SRC-0249，注明为5种子平均。
3. 写`results/task6/t6.4-summary/{comparison,manifest}.json`（命令、sha、容器、物理步长、偏差清单）。新论据追加SOURCES。
4. RESULTS标review，交Claude复核。

## 异常处理

- checkpoint或源码哈希不一致；需改上游/Husky原版的策略、观测、奖励、任务代码；Gazebo启动链缺包；B在0.0005 s下仍复位失败；出现D21以外的评估中断：停止，写RESULTS，交Claude。
- 不自行增加任务或评估条件，不训练。
- 不停止或干预task5、task6.2的进程与容器；只清理本任务自己启动的进程，并按身份核验。

## 交接要求

RESULTS至少写：运行位置与理由、实际命令、run-id、退出码、物理步长与执行方式、sha256、结果表、偏差清单、清理核查、未解决问题、下一步。长时间运行时写监控与停止方法。
