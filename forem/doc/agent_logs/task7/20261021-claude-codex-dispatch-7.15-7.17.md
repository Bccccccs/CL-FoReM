# 2026-10-21 Claude：task7.15–7.17 Codex派发提示（可并行）

- 作者：Claude（claude-opus-5-5，推理强度未知）；由用户派发，Claude不启动。三份提示互不依赖，可同时交给三个Codex会话；文件归属与GPU已在各TASK中分开（7.15用GPU1、7.16纯CPU、7.17用GPU2）。
- 推荐：Codex GPT6.1sol，medium。

## task7.15 规则候选生成器实施

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.15-CANDIDATES-20261021（规则候选生成器实施）。推荐GPT6.1sol / medium；日志写明实际模型与强度，无法核实写“未知”。

【授权】用户已授权（forem/doc/SOURCES.md SRC-0431）。授权边界、预算、GPU与文件归属以 forem/doc/tasks/task7/task7.15/TASK.md 为准；超出即停下报告。不训练、不启停或重建容器、不改阶段一代码与参考仓库（husky/、nmoma/、scwm/、mobile-rl/、archive/、mapgen/）、不提交git。

【并行】本任务与task7.15/7.16/7.17中的其他任务可能同时由别的Codex会话执行。只改TASK“文件归属”列出的文件；其他task7_sim模块只读调用，需要改动时停下报告。PROGRESS只改自己那一行、写前重读、定点编辑不整文件重写。SOURCES新条目只用本任务预留编号（SRC-0440–0449），写前重读。

【先读】根AGENTS.md（“功能范围硬性约束”“论据与引用来源”“性能优化共同要求”）；forem/AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；forem/ENV.md；本任务三文档 forem/doc/tasks/task7/task7.15/TASK.md、PROCEDURE.md、RESULTS.md 及其中列出的规格来源；task7.14 RESULTS（环境内核现状与Claude两轮复核）。

【开工】PROGRESS“项目级记录”加一行：TASK7.15-CANDIDATES-20261021｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.15/20261021-codex-candidates.md，先写开工核查。长任务写PID与停止方式，后台Python用python3 -u。

【要做的事】按PROCEDURE“执行步骤”顺序完成。规格是task7.9 RESULTS的A.1–A.8与R1–R8；s_k复用forem/src/task7_sim/search.py的同一规则。

【遇到规格问题】不发起文档复核轮次。歧义、冲突或缺数值时只停该部分，日志“待决定”列出位置、冲突与可选理解，其余继续；不自行补阈值、新语义或新功能。

【硬约束】不读真值的模块不得访问真值几何；GPU float32须有CPU float64对照；不为提速改变步长、子步、观测、奖励或终止语义；task7_sim原有73项测试不得回退。

【输出】RESULTS按run-id追加：改动文件、每项测试命令/退出码/日志/结果、计时、未通过项、已知限制、待决定问题。完成后PROGRESS本行改为review交Claude复核；做不完或预算用尽如实交接，不标完成。
```

## task7.16 A类程序化长方体地图生成器与地图池

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.16-MAPGEN-20261021（A类程序化长方体地图生成器与地图池）。推荐GPT6.1sol / medium；日志写明实际模型与强度，无法核实写“未知”。

【授权】用户已授权（forem/doc/SOURCES.md SRC-0431）。授权边界、预算、GPU与文件归属以 forem/doc/tasks/task7/task7.16/TASK.md 为准；超出即停下报告。不训练、不启停或重建容器、不改阶段一代码与参考仓库（husky/、nmoma/、scwm/、mobile-rl/、archive/、mapgen/）、不提交git。

【并行】本任务与task7.15/7.16/7.17中的其他任务可能同时由别的Codex会话执行。只改TASK“文件归属”列出的文件；其他task7_sim模块只读调用，需要改动时停下报告。PROGRESS只改自己那一行、写前重读、定点编辑不整文件重写。SOURCES新条目只用本任务预留编号（SRC-0450–0459），写前重读。

【先读】根AGENTS.md（“功能范围硬性约束”“论据与引用来源”“性能优化共同要求”）；forem/AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；forem/ENV.md；本任务三文档 forem/doc/tasks/task7/task7.16/TASK.md、PROCEDURE.md、RESULTS.md 及其中列出的规格来源；task7.14 RESULTS（环境内核现状与Claude两轮复核）。

【开工】PROGRESS“项目级记录”加一行：TASK7.16-MAPGEN-20261021｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.16/20261021-codex-mapgen.md，先写开工核查。长任务写PID与停止方式，后台Python用python3 -u。

【要做的事】按PROCEDURE“执行步骤”顺序完成。规格是mapgen/docs/husky_ur5_map_requirements.md的§3、§4、§5、§7、§10（只读，mapgen目录不改）；生成器写在forem/src/task7_sim/mapgen_a.py，纯numpy、不调用任何API。先小批试生成并估算全量耗时再全量生成；某档合格率过低或检验条件冲突时停下该档报告，不放宽合格条件。

【遇到规格问题】不发起文档复核轮次。歧义、冲突或缺数值时只停该部分，日志“待决定”列出位置、冲突与可选理解，其余继续；不自行补阈值、新语义或新功能。

【硬约束】不读真值的模块不得访问真值几何；GPU float32须有CPU float64对照；不为提速改变步长、子步、观测、奖励或终止语义；task7_sim原有73项测试不得回退。

【输出】RESULTS按run-id追加：改动文件、每项测试命令/退出码/日志/结果、计时、未通过项、已知限制、待决定问题。完成后PROGRESS本行改为review交Claude复核；做不完或预算用尽如实交接，不标完成。
```

## task7.17 回合环境：任务采样、路线规划与批量reset封装

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.17-EPISODE-20261021（回合环境：任务采样、路线规划与批量reset封装）。推荐GPT6.1sol / medium；日志写明实际模型与强度，无法核实写“未知”。

【授权】用户已授权（forem/doc/SOURCES.md SRC-0431）。授权边界、预算、GPU与文件归属以 forem/doc/tasks/task7/task7.17/TASK.md 为准；超出即停下报告。不训练、不启停或重建容器、不改阶段一代码与参考仓库（husky/、nmoma/、scwm/、mobile-rl/、archive/、mapgen/）、不提交git。

【并行】本任务与task7.15/7.16/7.17中的其他任务可能同时由别的Codex会话执行。只改TASK“文件归属”列出的文件；其他task7_sim模块只读调用，需要改动时停下报告。PROGRESS只改自己那一行、写前重读、定点编辑不整文件重写。SOURCES新条目只用本任务预留编号（SRC-0460–0469），写前重读。

【先读】根AGENTS.md（“功能范围硬性约束”“论据与引用来源”“性能优化共同要求”）；forem/AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；forem/ENV.md；本任务三文档 forem/doc/tasks/task7/task7.17/TASK.md、PROCEDURE.md、RESULTS.md 及其中列出的规格来源；task7.14 RESULTS（环境内核现状与Claude两轮复核）。

【开工】PROGRESS“项目级记录”加一行：TASK7.17-EPISODE-20261021｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.17/20261021-codex-episode.md，先写开工核查。长任务写PID与停止方式，后台Python用python3 -u。

【要做的事】按PROCEDURE“执行步骤”顺序完成。路线A*、高度/姿态插值、末端起终点与机械臂初始关节须先核对N²M²/CBL原代码（forem/src/modulation_rl内迁入代码与上游只读参考），写核对表并登记出处（代码路径:行号）后再照此实现；因本项目合同不得不偏离处单列。core.py只允许做按环境reset所需的最小改动与G1遮挡计数，并逐元素比对证明原语义不变。开发用小型夹具地图；若task7.16的地图池已交付，最后做一次读入集成测试。

【遇到规格问题】不发起文档复核轮次。歧义、冲突或缺数值时只停该部分，日志“待决定”列出位置、冲突与可选理解，其余继续；不自行补阈值、新语义或新功能。

【硬约束】不读真值的模块不得访问真值几何；GPU float32须有CPU float64对照；不为提速改变步长、子步、观测、奖励或终止语义；task7_sim原有73项测试不得回退。

【输出】RESULTS按run-id追加：改动文件、每项测试命令/退出码/日志/结果、计时、未通过项、已知限制、待决定问题。完成后PROGRESS本行改为review交Claude复核；做不完或预算用尽如实交接，不标完成。
```
