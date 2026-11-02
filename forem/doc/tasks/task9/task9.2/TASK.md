# task9.2 — 原语后端下层SAC长训（B0/B3×2种子×3M）

状态：**active（2026-10-28用户“启动训练”，SRC-1316）**。父[task9](../TASK.md)；成本依据[task9.1](../task9.1/RESULTS.md)（[SRC-1315](../../../SOURCES.md#src-1315)）。

## 目标

在primitive-obb-v1＋ghost-v1环境中，从头训练下层SAC：B0、B3各种子4718/4719，每run 3M转移，每250k做100验证＋96迁移评估，按[task9 TASK](../TASK.md)预注册判定回答“是否退化、B3能否消除”。研究问题与假设沿task8.9.3（H0–H3，H4只记录）。

## 范围

|run|配置|GPU|输出|
|---|---|---|---|
|B0-seed4718|`config/task9/lower_train_B0_prim_seed4718.json`|0|`results/task9/t9-long-20261028/B0-seed4718`|
|B0-seed4719|`..._B0_prim_seed4719.json`|1|`.../B0-seed4719`|
|B3-seed4718|`..._B3_prim_seed4718.json`|2|`.../B3-seed4718`|
|B3-seed4719|`..._B3_prim_seed4719.json`|3|`.../B3-seed4719`|

配置相对正式模板`config/task8/lower_train_{B0,B3}_prim.json`仅seed不同（[SRC-1316](../../../SOURCES.md#src-1316)，种子/GPU沿[SRC-1158](../../../SOURCES.md#src-1158)）。不包括：B1/B2、第3种子、H4、任何协议/规模改动、自动续训。

## 验收

|门|判据|
|---|---|
|L1 启动|预检通过（与smoke共有文件零漂移、配置仅seed差异、GPU/进程空、磁盘≥1TB）；4 run各在指定GPU运行|
|L2 250k重算|首个250k评估后按实测外推；>48h的run放STOP保存并报告用户（SRC-1316）|
|L3 完成|每run至3M有`summary.json`，或因看门狗/墙钟/STOP保存`diverged.pt`/`interrupted.pt`并如实记录；12次评估均complete|
|L4 判定|按预注册退化判据逐run、逐组报告；全部种子报告，迁移不选模|
|L5 独立验收|验收者≠执行/监控者，复核原件|

## 模型与强度（推荐）

|角色|Codex|Claude|理由|
|---|---|---|---|
|启动与监控|GPT6.1sol / medium（固定巡检可gpt-6.1-terra / low）|Sonnet5.5 / medium|长任务监控与外推判断|
|独立验收与判定|GPT6.1sol / high|Sonnet5.5 / high|跨评估/诊断/判定原件核对|
