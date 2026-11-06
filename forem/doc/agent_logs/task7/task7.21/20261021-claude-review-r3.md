# 2026-10-21 Claude：task7.21 r3复核与r4派发提示

- Agent：Claude（claude-opus-5-5），推理强度未知。复核结论见[task7.21 RESULTS](../../../tasks/task7/task7.21/RESULTS.md)“Claude复核t7.21-r3”。
- 命令：两次pytest（CPU、GPU0）各40 passed；独立检查脚本`/tmp/claude-1004/.../scratchpad/check721.py`（CPU，阶段1梯度隔离与阶段3接入等价），输出见RESULTS。
- 结论：退回r4，只修不同步候选几何缺Δs_k。

## r4派发提示（由用户派发；推荐GPT6.1sol / medium）

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.21-UPPER-MODEL-20261021 r4（小修）。授权沿SRC-0439；文件归属与预算沿 forem/doc/tasks/task7/task7.21/TASK.md（剩余额度内）；只用GPU0（运行前nvidia-smi核实无其他进程；若task7.18.1诊断正在用GPU0，则只跑CPU测试并记录GPU测试推迟）。不提交git，不改task7_upper以外文件（PROGRESS本行、RESULTS、日志、SOURCES 0505–0509除外）。

先读：task7.21 RESULTS末节“Claude复核t7.21-r3”、task7.10 RESULTS U.1与U.5、SOURCES SRC-0903第8项。

要做：
1. 候选几何按变体：同步6维(Δx, Δy, sinΔθ, cosΔθ, 距离, 原地标志)，不同步7维（另加目标进度Δs_k，单位m，按SRC-0903除以3.2）。CandidateEncoder接收变体或几何维数；UpperModel(asynchronous=True)传入7维；形状检查按变体拒绝错误维数。
2. 测试：两变体几何维数与归一化；不同步Δs_k变化会改变输出而同步不受该维影响；原40项回归（调整为两变体）；CPU与GPU（如可用）。
3. 不改其他结构、不改T_seg处理（复核第2项已记录接受）。

输出：RESULTS按run-id追加改动、命令/退出码/结果；PROGRESS本行改review交Claude复核。
```
