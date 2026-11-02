# 2026-10-21 Claude：task7.18.1 Codex派发提示

- 作者：Claude（claude-opus-5-5，推理强度未知）；由用户派发，Claude不启动。授权[SRC-0521](../../../../SOURCES.md#src-0521)。
- 推荐：Codex GPT6.1sol，medium。现在可派（GPU0空闲）。

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.18.1-DIAG-20261021（阶段L自碰撞与IK只读诊断）。推荐GPT6.1sol / medium；日志写明实际模型与强度，无法核实写“未知”。

【授权】用户已授权（forem/doc/SOURCES.md SRC-0521）。范围、文件归属与预算以 forem/doc/tasks/task7/task7.18/task7.18.1/TASK.md 为准；超出即停下报告。**只读诊断**：不改forem/src/task7_sim、forem/src/task7_lower、配置与阈值；不停止、暂停或改动task7.18正式训练（GPU2、GPU3）及其目录forem/results/task7/t7.18-20261021/formal-*（只读，检查点先复制再用，仅用已有.meta.json的完整检查点）；不安装依赖（容器内无trimesh/fcl/pybullet/open3d，网格用numpy读STL/DAE自行加密采样）；不训练、不启停容器、不改阶段一代码与参考仓库、不提交git。

【GPU与预算】只用GPU0（CUDA_VISIBLE_DEVICES=0）；开工与每次运行前用nvidia-smi核实GPU0无其他进程，被占用则停下报告。单条命令≤10分钟、累计容器计算≤60分钟，命令与耗时记账。

【先读】根AGENTS.md（“功能范围硬性约束”“论据与引用来源”“性能优化共同要求”）；forem/AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；forem/ENV.md；task7.18三文档（含正式训练监控与formal manifest）；本任务三文档（TASK中“背景”“待回答的问题1–6”为本任务规格）；task7.14 RESULTS（胶囊包络、0.02 m余量、允许对表、车体盒、IK合同与Claude复核中的限制）；task7.13 RESULTS L.0、D19；task7.4 RESULTS N1；SRC-0403、SRC-0405、SRC-0418（CBL的BioIK与自碰撞设定）。

【开工】PROGRESS“项目级记录”加一行：TASK7.18.1-DIAG-20261021｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.18/task7.18.1/20261021-codex-diag.md，先写开工核查（GPU0、可用检查点、源码与formal manifest是否一致）。后台Python用python3 -u并写PID与停止方式。

【要做的事】按PROCEDURE“执行步骤”1–6，逐条回答TASK问题1–6：自碰撞几何体对与段内发生时刻、当时关节角/IK路径；URDF原始碰撞网格复判误报比例（写明网格来源、采样密度、判定阈值）；回合与段初始姿态到自碰撞的最小间距分布；DLS回退原因分解（超出可达/限位/精确容差/变换问题，分变体）；不同步超时段的u、v、ω分布；CBL对照的事实陈述（代码路径:行号）。

【发现严重问题】若发现会使正式训练结果无效的确定性错误（如坐标或TCP变换错误），立即写入日志与PROGRESS本行并报告，不自行停止训练、不修代码。

【输出】RESULTS按run-id追加：每项的数据、命令/退出码、产物路径（forem/results/task7/t7.18.1-<run-id>/）、结论；分清事实、推断与待验证假设；修复建议只写改动点、对奖励/终止/动作/观测语义的影响与需用户决定的项，不实施。完成后PROGRESS本行改为review交Claude复核。
```
