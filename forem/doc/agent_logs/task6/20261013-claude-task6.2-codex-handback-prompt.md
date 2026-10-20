# task6.2 交回Codex的提示词（Claude编写，用户派发）

推荐配置：**gpt-6.1-sol（GPT6.1sol），推理强度medium**（以监控和读数为主，但遇到卡死/崩溃需要跨RLlib、Gazebo、helper排查）。如挂长训监控子Agent，用gpt-6.1-sol/low。

---

```text
你是Codex，额度恢复后接回FoReM项目的 task6.2（RLlib Gazebo组：Task5 B的Husky原版RLlib配方原样改在Gazebo中训练，即G-B）。你额度耗尽期间（2026-10-12 15:00起），由Claude子Agent（claude-sonnet-5-5）临时代行。决策者与流程制定者是Claude主会话；你按文档执行，不自行改动口径。工作目录：/home/ybc/projects/CL-FoReM。Docker命令一律用 sg docker -c '...'。

当前状态（Claude 2026-10-13 14:44核查）：正式训练 t6.2-gz-train-s40 自 10-13 11:23 起在容器 forem-t6-husky-gz 中运行，32000步，约2.7步/s，11个gzserver与11个t62_gzstep helper存活，main_ray 1个，train.log 0错误，helper卡死事件1次已自动恢复。用户决定“先跑30w”：训练不改设置、不在30万步停止（上游不支持续训），30万步评估后由用户决定是否跑满100万步。

开工前必读：
1. 根 AGENTS.md（全部规则）
2. forem/doc/PROGRESS.md 末尾 task6 相关各条
3. forem/doc/tasks/task6/TASK.md、PROCEDURE.md（父任务、资源与优先级）
4. forem/doc/tasks/task6/task6.2/TASK.md（G-D1至G-D11，尤其R3的G-D9物理步长0.0005 s／2000 Hz、R4的G-D10每步固定0.1 s与G-D11 N=10）、PROCEDURE.md、RESULTS.md（含Claude审核R1–R5，以及§5正式训练一节）
5. forem/doc/agent_logs/task6/task6.2/20261012-claude-task6.2.md（子Agent日志：G-D10实现、常驻helper t62_gzstep、卡死自动恢复、监督脚本自动清理）
6. forem/doc/SOURCES.md 的 SRC-0237、SRC-0238、SRC-0240至SRC-0245
7. 原 Codex 日志 forem/doc/agent_logs/task6/task6.2/20261012-codex-task6.2.md

你的任务：
1. 接手登记：在PROGRESS的task6.2行把负责人改回Codex并追加接手事件；新日志写在 forem/doc/agent_logs/task6/task6.2/20261013-codex-task6.2.md，注明实际模型与推理强度（无法核实写未知）。
2. 核实现场：用 `python3 forem/build/task6.2/scripts/t62_status.py t6.2-gz-train-s40` 及 docker top 核对训练、11个实例、helper、监督进程（PID见 forem/results/task6/t6.2-gz-train-s40/supervisor.pid）均存活，规划器dt全为0.100，记录当前步数。
3. 持续监控，至少每30分钟写一次日志：步数与吞吐、实例/helper存活、helper卡死事件数（*.stalls.jsonl）、窗口超出量、train.log错误、主机CPU。
4. 训练中评估读数：B的配方每7.5万步做一次50-episode评估。在7.5万、15万、22.5万、30万步各出结果时，把 evaluation/custom_metrics 的 success_mean、goal_reached_mean、ik_fails_mean、base_collisions_mean、episode_len_mean 写入task6.2 RESULTS的对照表，并与R-B（forem/results/task5/t5.2-train-s40/train_eval_series.csv，同步数）逐点并列。7.5万步时特别核实：评估确实在评估实例K10上执行、50个episode完成、评估是否阻塞训练迭代（记录前后迭代墙钟）。
5. 30万步评估出结果后：写好读数与对照，停止你的工作并汇报给用户/Claude，**不要停止训练**。是否跑满100万步由用户决定。
6. 异常处理：
   - helper卡死由现有机制自动恢复，只记录；若卡死频繁到明显拖慢吞吐（例如单小时内多于10次或吞吐低于1.5步/s持续1小时），记录并报告，不自行改机制。
   - 训练或实例崩溃：监督脚本会自动停掉本run全部实例与helper；你核实清理收据（cleanup_remaining.txt）、保留全部证据、写入RESULTS并报告。上游不支持续训，**不得自动重训或续训**。
   - 需要停止训练时（只有用户或Claude明确要求）：`sg docker -c 'docker exec forem-t6-husky-gz kill -TERM $(cat /forem_results/t6.2-gz-train-s40/supervisor.pid)'`，然后核实清理。
   - 遇到文档未覆盖、超出授权的问题：停下，写入RESULTS和日志，交Claude决定。

硬性约束：
- 不改训练命令、worker数、training_intensity、物理步长0.0005/2000、固定窗口0.1 s、helper机制、env/规划器/控制器/奖励/观测/终止。
- 不触碰 forem-t5-pr2、forem-t5-husky、forem-dev 及其进程；只操作本run自有的进程与实例。
- 只更新task6.2自己的RESULTS和日志、PROGRESS中task6.2的行与追加事件、SOURCES新条目（带 <a id="src-XXXX"></a> 锚点，编号取当前最大+1并在写入前复核）。修改共享文件前先重读最新内容。
- 不要把task6.2标为done；正式训练结束或用户决定停止后，由Claude复核。
```
