# task6.5 用原作者预训练模型复现N²M²的sim与Gazebo结果 — 详细流程

状态：**尚未执行（2026-10-14）**。目标、范围、验收见[TASK](TASK.md)；结果填写在[RESULTS](RESULTS.md)。

## 递归规则声明

本节点遵守根AGENTS的递归三文档规则：task6.5及今后拆出的task6.5.M都必须各有TASK、PROCEDURE、RESULTS三份文档。父节点[task6](../PROCEDURE.md)负责顺序、依赖与汇总；本节点结果以本RESULTS为准。执行者只更新本节点文档和自己的日志`agent_logs/task6/task6.5/`；父RESULTS与PROGRESS的汇总由Claude维护（执行者可追加自己产生证据的SRC条目）。执行者自报完成不能当作通过，须经Claude复核。当前无子节点；差异排查若展开为多项实验，由Claude拆为task6.5.M。

## 输入与依赖

- 原作者模型（只读）：`mobile-rl/scripts/model_checkpoints/{pr2,tiago}/`（`checkpoint-1000`、`checkpoint-1000_trainableState`、`config.yaml`、`ray_config.pkl`）。
- 环境：task6.4的`forem-t6.4-pr2`（同task5镜像、上游代码、Gazebo启动链已验证）及其包装脚本`forem/scripts/run_task6_4_eval.py`（可复制改名为本任务包装，不改task6.4的文件）。
- 依赖顺序：本任务阶段一须在task6.4的A正式评估**结束后**在同一容器运行（避免同容器两套ROS）；或用同镜像新建`forem-t6.5-pr2`（记录理由）。
- 不干扰task5两容器、`forem-t6-husky-gz`（G-B训练）、task6.4正在运行的进程。

## §1 开工

1. 登记PROGRESS与独立日志；记录主机CPU、各容器进程。
2. 计算原作者模型各文件sha256。`restore_ckpt_files`会在模型目录写`.tune_metadata`：把模型目录逐字节复制到`results/task6/<run-id>/model/`后再评估，不写`mobile-rl/`。
3. 核对原作者`config.yaml`中与评估相关的键（`env`、`task`、`learn_torso`、`ik_fail_thresh_eval`、`execute_style`、`time_step`），写入核对表；确认`evaluation_ray`对`--model_file`分支的配置覆盖方式（task6.4已记录utils.py L351–403）。

## §2 阶段一：原作者PR2模型

run-id：`t6.5-pr2-sim`、`t6.5-pr2-gz`（可各先跑`--nr_evaluations 3`冒烟，run-id加`-smoke`）。

- sim：`evaluation_ray.py --evaluation_only --eval_execs sim --env pr2 --eval_tasks simpleobstacle --model_file <副本>/checkpoint-1000 --num_gpus 0`。
- Gazebo：同上，`--eval_execs gazebo`，按task6.4 A已验证的启动方式（PR2启动30 s后物理步长0.002 s，照上游原样）。
- 有效性判据沿用task6.4 T64-D3：请求回合全部有“Eval ep”行且指标已导出；退出码照实记录。
- 超长episode按D21续跑拼接。
- 记录：每回合成功、步数、IK失败、碰撞次数与“Collision:”行中的碰撞对象、墙钟。

完成后写阶段一小结，RESULTS标“阶段一review”，**停止**，交Claude。

## §3 阶段二（Claude放行后）

按Claude在阶段一复核中写明的分支执行：

- **分支甲（Gazebo接近原文）**：PR2其余8任务Gazebo各50（picknplace、bookstorepnp、dynobstacle、picknplacedyn、door、drawer、roomdoor、spline；任务名与原文列的对应按task5记录）；然后TIAGo simpleobstacle sim＋Gazebo各50（先核查TIAGo Gazebo包，缺包停止交Claude）。
- **分支乙（Gazebo明显低于原文）**：按Claude列出的排查项逐项执行，先只读核查，需要运行的诊断每次只改一项并用新run-id。

## §4 汇总

1. 由stdout“Eval ep”逐回合行统计成功率（D23口径），W&B逐文件交叉核验。
2. 对照表（见TASK交付）；原文数值引用SRC-0269。
3. 写`results/task6/t6.5-summary/{comparison,manifest}.json`；新论据追加SOURCES。
4. RESULTS标review，交Claude复核。

## 异常处理

- 原作者模型无法被当前代码加载（版本/格式不兼容）、需要改上游代码、Gazebo启动链缺包、出现D21以外的评估中断：停止，写RESULTS，交Claude。
- 不自行增加任务、机器人或条件，不训练。只清理本任务自己启动的进程，并按身份核验。

## 交接要求

RESULTS至少写：运行位置、实际命令、run-id、退出码、模型sha256、结果表、失败形式统计、偏差清单、清理核查、未解决问题、下一步。
