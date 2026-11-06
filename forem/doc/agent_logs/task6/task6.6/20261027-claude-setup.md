# 2026-10-27 Claude：task6.6建档与no_grad发现登记

- 执行：Claude（claude-opus-5-5，推理强度未知）。推荐：Codex GPT6.1sol / Claude Sonnet5.5，文档整理low，检查点与动作映射核对medium。
- 用户要求（[SRC-1241](../../../SOURCES.md#src-1241)）：“建任务：用我们的sim和Gazebo评估协议（50回合）评估CBL自己的checkpoints_simpleobstacle和pnp_plus 4000，同时把no_grad的发现登记到SOURCES并更正SRC-0200”。
- 授权边界：建档、登记来源、只读预检。本轮没有评估、训练或修改源码；`archive/`、`husky/`只读。

## 背景

同一会话上一轮回答“能否完美复现CBL”时，读`husky/src/modulation_rl/scripts/sac.py`发现`update_parameters_modified`在`torch.no_grad()`内采样`state_action`，策略得不到梯度。

## 实际操作

1. 最小autograd测试与检查点只读比对（forem-dev，CPU，`CUDA_VISIBLE_DEVICES=`空）：脚本与输出在`forem/results/task6/t6.6-precheck/`（`nograd_check`、`ckpt_check`、`sig_check`的`.py/.out`，`archive_sha256.txt`）。检查点通过`docker cp`临时复制到容器`/tmp/t66check/`，用完已删除。三个脚本rc均为0。
   - 策略梯度为None、参数不变。
   - CBL `checkpoints/` 1000/2000/4000策略与pp4000逐位相同，策略优化器step停在4,101,606，critic继续到5,948,711。
   - so01/so14/pp4000的`policy_state_dict`与F0键集与形状一致。
2. SOURCES：新增[SRC-1240](../../../SOURCES.md#src-1240)（bug与证据）、[SRC-1241](../../../SOURCES.md#src-1241)（用户指令）、[SRC-1242](../../../SOURCES.md#src-1242)（兼容预检、双tanh动作映射T66-D1）；在[SRC-0200](../../../SOURCES.md#src-0200)、[SRC-0058](../../../SOURCES.md#src-0058)追加更正（原文保留）；[task3.4 RESULTS](../../../tasks/task3/task3.4/RESULTS.md)第2条追加更正。为执行者预留SRC-1243–1259。SOURCES由其他会话同时追加条目（SRC-13xx），本次用`>>`追加，没有覆盖。
3. 任务文档：新建[task6.6](../../../tasks/task6/task6.6/TASK.md)三文档；task6父TASK、PROCEDURE、RESULTS各加一行；PROGRESS登记。

## 设计要点

- 范围：15个检查点（so01–so14、pp4000）×S/Z-B/Z-A，共45条评估，种子2001–2050，与F0、task5.5、task6.3同场景可配对。
- 动作映射：CBL执行的是参考`predict`的双tanh；主口径用参考类，单tanh不纳入（改变动作语义，需用户另行决定）。评估脚本只新增缺省不变的`--policy-class`。
- 耗时估计（推导，非承诺）：Gazebo约0.52 h/条，30条约16 h累计，8并行约2–2.5 h墙钟。

## 下一步

待用户决定派发：Codex额度用尽至2026-11-02 15:08，期间可由Claude子Agent（Sonnet5.5）按PROCEDURE执行。

## 2026-10-27 18:40–18:55 复核（Claude，claude-opus-5-5）

子Agent（sonnet）18:38交回，状态review。独立复算45份`eval.json`（脚本`results/task6/t6.6-summary/claude_review_recompute.py`），核对检查点sha256、抽取manifest、脚本diff、回归诊断与场景哈希配对，全部一致；§2 steps偏差裁定为建档时PROCEDURE判据错误并在PROCEDURE追加更正。task6.6标done；更新task6.6三文档状态、task6父TASK/PROCEDURE/RESULTS行、PROGRESS两处，SOURCES追加SRC-1245。未训练、未运行新评估、未提交git。复核后无残留实例，`uptime`负载0.38。
