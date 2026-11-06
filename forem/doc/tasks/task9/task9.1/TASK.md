# task9.1 — 原语后端SAC smoke（B0/B3，512→恢复→1000＋完整196评估）

状态：**active（2026-10-28用户批准；准备中，尚未运行）**。父[task9](../TASK.md)。授权[SRC-1313](../../../SOURCES.md#src-1313)。

## 目标

在primitive-obb-v1上用真实训练CLI（`forem/scripts/task8_lower_train.py`）跑通B0、B3的短窗训练：primary至512转移→完整保存→从保存点真实恢复至1000转移→完整196评估（100验证＋96迁移）。实测SAC更新、评估、保存、恢复的耗时与显存，供父推导task9.2长训成本。**这是含SAC更新的训练**，已获用户批准，但只限本清单。

## 范围

包括：固定8 job（下表）；新配置`forem/config/task9/lower_smoke_B{0,3}_prim.json`（相对`config/task8/lower_train_B{0,3}_prim.json`仅`checkpoint_interval` 250000→1000，与8.9.3 r2 smoke同一差异）；新账本、新输出；独立验收。

不包括：3M或任何超出1000转移的训练；改环境数/回放/batch/评估规模；改奖励/动作/观测/终止/采样；生产代码修改或优化；重试失败job；`task7_lower`测试或任何其他optimizer测试。

## 固定job（沿8.9.3 r4结构，[r4-smoke-plan.md](../../../../logs/task8/t8-train-stage0-20261027/r4-smoke-plan.md)）

|序|job|账本预留s|CLI `--max-wall-s`|外timeout/kill-after|内容|
|---|---|---:|---:|---|---|
|1|preflight|20|—|—|冻结hash、配置差异、池/种子、100+96计划、GPU空闲、账本余额|
|2|B0-primary|940|900|920/+10|256环境、100k容量至512转移、完整保存|
|3|B0-preserve|15|—|—|核512/255更新、cuda设备、resume_safe；primary五文件改名primary-*|
|4|B0-resume|1175|1130|1155/+10|`--resume primary-final.pt`至1000、743更新、完整196|
|5|B3-primary|940|900|920/+10|同上至512，26更新|
|6|B3-preserve|15|—|—|同上|
|7|B3-resume|1175|1130|1155/+10|至1000，75更新、完整196|
|8|postflight|20|—|—|汇总状态、诊断、吞吐/显存/耗时原件|

合计4300s（推导，非实测；SRC-1313批准上限）。更新数按[SRC-1194](../../../SOURCES.md#src-1194) `U_k(N)=max(0,floor(N/k)-floor(257/k))`。

## 验收门

|门|判据|
|---|---|
|S1 执行|8 job按序rc=0、各恰1条账本记录、无timeout；账本合计≤4300s|
|S2 primary|steps=meta.steps=env_actions=512；updates B0 255 / B3 26；policy/replay设备cuda；resume_safe|
|S3 恢复|只从同目录`primary-final.pt`经`safe_to_resume`/`load_checkpoint`恢复，无fresh reset；steps 1000；updates B0 743 / B3 75；诊断恰1条（step 1000）；validation_pending为空|
|S4 评估|validation 100、transfer 96均complete；transfer不用于模型选择；无incomplete文件|
|S5 实测|primary wall、resume至1000的训练elapsed、196评估wall、检查点大小、`peak_gpu_bytes`与GPU CSV峰值分别报告；runtime/检查点`map_backend`=primitive-obb-v1|
|S6 合规|preflight冻结的代码/配置/计划hash全程不变；单GPU串行且job前compute为空；无重试；独立验收者≠执行者|

## 输出位置

计划/wrapper/账本/日志：`forem/logs/task9/t9-smoke-20261028/`；训练产物：`forem/results/task9/t9-smoke-20261028/{B0,B3}/`（容器内`/root/mm_husky_ws/...`）。

## 模型与强度（推荐）

|角色|Codex|Claude|理由|
|---|---|---|---|
|P1 准备＋执行|GPT6.1sol / medium（固定执行可gpt-6.1-terra / low）|Sonnet5.5 / high|改编r4 wrapper需核对恢复/预算/路径合同；执行判据固定|
|P2 独立验收|GPT6.1sol / high|Sonnet5.5 / high（≠P1）|跨恢复/评估/账本原件核对|
|父汇总与成本推导|GPT6.1sol / medium|Sonnet5.5 / medium|成本公式与未知项|
