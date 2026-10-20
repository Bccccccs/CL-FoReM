# Task5 最终评估补完（D21）Codex提示词（Claude编写，用户派发）

推荐配置：**gpt-6.1-sol（GPT6.1sol），推理强度medium**（要做确定性核查与拼接计数，跨评估日志、后处理脚本与两容器）。不需要子Agent；如挂监控子Agent用gpt-6.1-sol/low。

---

```text
你是Codex，负责补完FoReM项目task5的最终9任务sim评估（按Claude决策D21）。决策者是Claude主会话；你按文档执行，不自行改动口径。工作目录：/home/ybc/projects/CL-FoReM。Docker命令一律用 sg docker -c '...'。

背景：A（上游N²M²+PR2，容器forem-t5-pr2）与B（Husky原版，容器forem-t5-husky）均已训练完100万步、退出0。两者的后处理最终评估都因上游 mobile-rl/scripts/modulation/evaluation.py L222–224 的assert（单回合超过20000步）中断，posttrain_status.json为blocked。用户已确认：超限回合记为失败。

开工前必读：
1. 根 AGENTS.md（全部规则）
2. forem/doc/PROGRESS.md 中task5段与末尾各条
3. forem/doc/tasks/task5/TASK.md、PROCEDURE.md、RESULTS.md（含2026-10-13状态同步）
4. forem/doc/tasks/task5/task5.3/RESULTS.md 的 R7–R8（D10：B的bookstorepnp记N/A）、**R10（D21）**、**R11**
5. forem/doc/tasks/task5/task5.1/RESULTS.md、task5.2/RESULTS.md 末尾，以及 forem/build/task5/task5_posttrain.py（原后处理：评估命令、模型路径、离线W&B设置、输出软链）
6. forem/doc/SOURCES.md 的 SRC-0243

任务（新run-id：A用 t5.1-eval-r2，B用 t5.2-eval-r2；原 t5.1-eval-r1、t5.2-eval-r1 全部保留，不覆盖）：

A（forem-t5-pr2）：
1. D21第2条确定性核查，用原入口、原模型、原参数，不改代码：
   (a) door `--eval_seed 1029 --nr_evaluations 8`，逐回合步数与成功与否须与原日志 logs/task5/t5.1-eval-r1/eval-door.log 的ep30–37完全一致；
   (b) door `--eval_seed 1037 --nr_evaluations 1`，预期再次超过20000步并触发同一assert。
   (a)不一致，或(b)未超限：停下，不拼接，交Claude。
2. 补完door：`--eval_seed 1038 --nr_evaluations 11`（原i=39–49）。若再次超限，该回合记失败，用下一个种子和剩余回合数继续。door结果 = 38 + 补跑成功数，分母50。
3. drawer、roomdoor、spline：原入口、原参数，各50回合、eval_seed 999。若某回合超限，按D21同法：记失败，从下一个种子续跑剩余回合数。

B（forem-t5-husky）：
4. spline：先 `--eval_seed 999 --nr_evaluations 1` 复现i=0应再次超限（不超限则停下交Claude）；再 `--eval_seed 1000 --nr_evaluations 49` 补完i=1–49，超限同法处理。spline结果 = 补跑成功数，分母50（i=0记失败）。B其余任务不重跑；bookstorepnp按D10记N/A。

通用：
5. 评估命令与原后处理一致（evaluation_ray.py --evaluation_only --eval_execs sim --env <env> --eval_tasks <task> --model_file <原模型> --num_gpus 0，W&B离线），只增加 --eval_seed/--nr_evaluations。每次调用的完整命令、起止时间、退出码、日志路径写入 forem/results/task5/t5.{1,2}-eval-r2/commands.json。输出软链 scripts/logs 改指新run-id目录前后都要记录；不得写入原r1目录。
6. 不改任何源码（mobile-rl/、husky/、forem/build/task5/ws_husky 内代码），不改模型、任务、world、max_len、seed协议。补充后处理/汇总脚本放 forem/build/task5/，命名清楚。
7. 汇总：在 forem/results/task5/t5.{1,2}-eval-r2/ 输出 final_eval_summary.json，包含9个任务每个任务的成功数/分母、成功率、拼接说明（哪些回合来自哪次运行、哪些超限记失败），以及picknplace、bookstorepnp的fwdO朝向原始指标单列。成功数须用stdout“Eval ep”行逐回合计数核验，与evaluation_ray输出的汇总指标一致；不一致就停下报告。B的9任务平均同时给出“8个可运行任务平均”和“9任务含N/A”两种口径（D10）。
8. 资源：两容器只用CPU；task6.2的G-B训练正在forem-t6-husky-gz中运行（约8核），主机CPU合计须持续≤56核。不得触碰forem-t6-husky-gz、forem-dev及其进程。可A、B并行或先后，以CPU为准。
9. 记录：在PROGRESS登记（负责人Codex、范围D21补评估、开始时间）；日志写在 forem/doc/agent_logs/task5/task5.1/20261013-codex-task5-d21.md 与 task5.2/ 下同名文件，注明实际模型与推理强度（无法核实写未知）；结果写入task5.1、task5.2各自RESULTS；新的实测论据登记SOURCES（带 <a id="src-XXXX"></a> 锚点，编号取当前最大+1并在写入前复核）。修改共享文件前先重读。
10. 完成后把task5.1、task5.2的RESULTS状态改为review，停下交Claude做task5.3最终复核。不要自行标done。

遇到D21未覆盖的失败（地图缺失、采样失败、进程异常等）：停下，保留证据，写入RESULTS和日志，交Claude决定。
```
