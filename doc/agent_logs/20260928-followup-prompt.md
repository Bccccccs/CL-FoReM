# FOLLOWUP-028 启动提示词（交给执行 Agent）

- 编写：Claude Opus 5.5 /ybc（协调方，仅文档），2026-09-28。
- 以下整段交给执行 Agent。

---

你负责 CL-FoReM 项目的 **FOLLOWUP-028：G0 后续双线检验**。你的工作是按设计说明编写代码、完成验证、一次性启动无人值守流水线；启动确认后即可结束，**不需要守着流水线跑完**。

工作区：宿主 `/home/ybc/projects/CL-FoReM`，容器内 `/root/mm_husky_ws`。

## 一、开工前

1. 按顺序阅读：
   - `AGENTS.md`（尤其第 2 节文档规则）；
   - **`doc/agent_logs/20260928-followup-spec.md`（本任务的完整设计，逐条照做）**；
   - `doc/DECISIONS.md` 的 D45–D51（D50、D51 是本任务的预登记判据，**不得修改**）；
   - `doc/agent_logs/20260928-stage0.md` 中 R0-3、R0-3c、R0-4、R0-4b 各节与 G0 最终判定表；
   - `ENV.md`；
   - 以下现有代码：`src/modulation_rl/scripts/p0_runner.py`、`adaptation_probe.py`、`residual_probe.py`、`wm/encoder.py`、`wm/dynamics.py`、`model.py`（`GaussianPolicy`）、`doc/agent_logs/20260928-stage0-shard-eval.py`、`doc/agent_logs/20260928-stage0-r03-analyze.py`。
2. 接手登记：`doc/PROGRESS.md` 中已有 FOLLOWUP-028 一行，把执行 Agent 改成你自己；在 `doc/agent_logs/20260928-followup-pipeline.md` 末尾追加接手记录。
3. 核查现场：`git status`、当前分支（应为 `stage0-028`）、`docker ps`、`nvidia-smi`、`free -g`、容器 `mmhusky-node01` 内 analytical 仿真是否在运行。

## 二、要做的事

1. 从 `stage0-028` 新建分支 `followup-028`。
2. 按设计说明 §3–§5 实现：
   - `p0_runner.py` 的两个默认关闭开关 `--save-step-info`、`--shield-config`，并转发到 `episode_command()` 和分片启动脚本；
   - A 线结构化适应探针（V4/V5/V6）；
   - B1 可避免性分析；
   - B2 特征模块（离线与在线共用）、标签、四类分类器、阈值选择与分类器包；
   - B3 干预模块；
   - 编排脚本 `followup_pipeline.py`、宿主启动脚本 `doc/agent_logs/20260928-followup-launch.sh`；
   - S6 自动报告，生成 `doc/agent_logs/20260928-followup-report.md`。
3. 按设计说明 §6 完成全部验证：默认关闭回归、单元测试、小规模冒烟，并把结果写进任务日志。
4. 按路径提交到 `followup-028` 分支，然后启动正式流水线，确认各阶段已进入运行。
5. 在任务日志写明：启动命令、宿主 PID、容器内进程、日志与状态文件路径、监控命令、停止与续跑方式，以及分支上的提交列表。把 PROGRESS 中本任务状态改为“流水线运行中”，然后向用户汇报并结束。

## 三、硬约束

- 新脚本放在 `src/modulation_rl/scripts/` 顶层，**不要放进或修改 `scripts/wm/`**，否则会破坏已训练世界模型的 `code_identity()` 校验。
- 所有新行为默认关闭，关闭时输出逐字段不变；不训练 SAC；不改奖励、终止、IK、动作语义；评测一律 `--ik-mode fixed --ik-iterations 100`。
- 判据只能照 D50、D51 实现；实现中发现判据无法按原文执行时，停下来在日志中说明并询问用户，不得自行改写。
- 种子只用设计说明登记的范围；20000–20299 不得使用。
- 并发 episode-worker 总数 ≤ 64，启动新批次前可用内存 ≥ 60 GiB；流水线自身也要实现内存守护。
- 不停止或重建他人的容器与进程；`mmhusky-node01` 内的 analytical 仿真可以使用。
- Git：只按路径 `git add`；不用 `git add -A`，不用 `git stash`，不 push，不合并 main；不要提交不属于本任务的未跟踪文件。
- 遵守 AGENTS.md 第 2 节：关键节点和每 30 分钟更新任务日志。
