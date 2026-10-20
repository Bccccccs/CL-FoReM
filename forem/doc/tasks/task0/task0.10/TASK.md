# task0.10 task0.9复核问题修正 — 任务

状态：done（经task0.13独立复核；当前固定底座UR5环境范围验收通过）。

历史状态记录：状态：review（Claude 已于2026-09-30执行并自测，结果见[RESULTS](RESULTS.md)；待Codex复核，父task0保持review）。来源：[task0.9 RESULTS](../task0.9/RESULTS.md) 的复核结论“复核不通过”，用户要求修改。

## 目标与范围

闭环处理 task0.9 指出的 4 项失败路径，并追加“失败→修正→通过”的回归证据：

1. P1 `task0_proc.py` 在 root 身份失效（PID 被复用）后仍按裸 PID 收养外来子树，可能向外来进程发信号。
2. P2 原 root 先退出、子进程被 reparent 后，stop 漏清理仍返回成功；已有 cleanup 记录时不复核残留。
3. P2 高频分析对空数据、2 行、全 NaN、缺列、少于 100 个连续步三元组仍 pass=true、退出 0。
4. P2 高频判定用整个 bag，没有绑定请求窗口，也没有单独评价运动段，安静段会稀释异常。

范围只在 forem：`scripts/task0_proc.py`、`analyze_task0_feedback.py`、`run_task0_smoke.sh`、相关测试与文档。不改物理/控制配置（world 求解器结论不变），不启动 task1、误差注入、IK、SAC、世界模型，不提交/推送（除非用户另说），不碰他人进程。

## 交付与完成条件

- 每个问题：先有会失败的回归（真实进程或合成数据，不动外来进程），再修正，再通过；复核者的复现脚本给出的输入在新逻辑下必须被拒绝/不误杀。
- 用新的 run-id 重跑 fresh 启动、60 s 保持、高频保持/运动复测，高频判据按请求窗口、运动段、停稳段分别评价；旧数据按正确窗口重算，不因此否定或夸大 world 求解器的收益。
- RESULTS 给出问题—修正—证据对应表、命令与退出码、hash、未解决项；置 review 交 Codex 再审，不自行把 task0 标 done。

## 模型与推理强度

- Codex：GPT6.1sol，medium；Claude：Sonnet5.5，medium（跨模块核对进程所有权、判据与窗口）。实际 Claude：Sonnet5.5，档位平台默认（未能核实，记未知）。
