# CEIL-028 启动提示词（交给执行 Agent）

- 编写：Claude Opus 5.5 /ybc（协调方，仅文档），2026-09-29。
- 以下整段交给执行 Agent。

---

你负责 CL-FoReM 项目的 **CEIL-028：SAC 上限摸底**。按设计说明编写代码、完成验证、一次性启动无人值守流水线；确认训练和评测已经运行后即可结束，**不需要守着**（预计 11–14 小时）。

工作区：宿主 `/home/ybc/projects/CL-FoReM`，容器内 `/root/mm_husky_ws`。

## 一、开工前

1. 按顺序阅读：`AGENTS.md`（尤其第 2 节）；**`doc/agent_logs/20260929-ceil-spec.md`（完整设计，逐条照做）**；`doc/DECISIONS.md` 的 D55–D57（D57 为本任务预登记判据，不得修改）；`doc/agent_logs/20260929-screen-pipeline.md`（上一条流水线的实现、`--replay-compact-maps`、停止经过）；`ENV.md`；代码 `p0_runner.py`、`sac.py`（重点第 40–64 行的学习率调度）、`checkpointing.py`（`load_training` 的续训协议检查）、`screen_pipeline.py`、`screen_stats.py`。
2. 在 `doc/PROGRESS.md` 新增 CEIL-028 一行登记自己；在 `doc/agent_logs/20260929-ceil-pipeline.md` 建立任务日志并写接手记录。
3. 核查现场：当前分支应为 `screen-028`；`docker ps`、`nvidia-smi`、`free -g`；确认没有仍在运行的 `screen_pipeline`/`p0_runner` 进程；`mmhusky-node01` 内 analytical 仿真在运行。

## 二、要做的事

1. 从 `screen-028` 新建分支 `ceil-028`。
2. 实现设计说明 §3、§6：`--policy-override {random,mean,slow-ee}`（默认关闭）、编排脚本 `ceil_pipeline.py`、宿主启动脚本 `doc/agent_logs/20260929-ceil-launch.sh`、自动报告 `doc/agent_logs/20260929-ceil-report.md`。先核实 `num_steps` 取自 `--steps`。
3. 完成 §6 的启动前验证：默认关闭回归、单元测试、冒烟，结果写进任务日志。
4. 按路径提交到 `ceil-028`，启动正式流水线，确认两个训练进程与 E2 评测已运行。
5. 在任务日志写明启动命令、PID、日志与状态文件、监控、停止与续跑方式、提交列表；PROGRESS 状态改为“流水线运行中”；向用户汇报后结束。

## 三、硬约束

- 不从 policy-100k 续训；训练预算 300000 步从零开始，其余配置与 policy-100k 一致；主结论只用预算末端检查点。
- 新代码放在 `scripts/` 顶层，不放进、不修改 `scripts/wm/`；新行为默认关闭，关闭时输出逐字段不变；评测一律 `--ik-mode fixed --ik-iterations 100`。
- 统计先写点估计再算 CI。
- 判据只能照 D57 实现；无法按原文实现时，停下来询问用户。
- 种子：训练 11、22；评测 10000–10099；20000–20299 不得使用。
- episode-worker ≤ 64；启动新批次前可用内存 ≥ 60 GiB。
- 不停止或重建他人的容器与进程。
- Git：只按路径 `git add`；不用 `git add -A`、不用 `git stash`；不 push、不合并 main；不提交不属于本任务的文件。
- 遵守 AGENTS.md 第 2 节：关键节点和每 30 分钟更新任务日志。
