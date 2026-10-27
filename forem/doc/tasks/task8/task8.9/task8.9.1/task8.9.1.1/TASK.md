# task8.9.1.1 — 跨场景批量射线（性能优化，语义等价）

状态：**done（2026-10-27 O1–O4独立PASS；仅优化交付，父P5/正式训练未完成）**。父[task8.9.1](../TASK.md)，授权[SRC-1190](../../../../../SOURCES.md#src-1190)，性能[SRC-1194](../../../../../SOURCES.md#src-1194)。

## 目标

消除`SceneBatch.raycast`（及profile显示必要时的`collide`）逐场景Python循环，使256环境扫描成本随batch近似并行扩展；**输出与现实现逐元素完全相同**。

## 依据

r2 profile：256环境raycast占单步91.69%（立方体）/94.67%（语义），batch 64→256吞吐17.70→17.99转移/s（`forem/results/task8/t8-perf-20261027/summary-r2.json`）。

## 范围与方法

- 把各环境行scene的BVH节点/叶子拼接为一个森林（行偏移），所有行的射线一次性遍历；`_slab`等逐射线算术保持相同顺序与dtype，保证结果比特一致。分块大小可调但须保证等价。
- 仅改`forem/src/task8_sim/scene.py`中SceneBatch批量路径（保留单scene路径与旧循环实现作参照/回退开关），不改VoxelScene几何、v3体素化、PcdPanorama量程/像素、地面处理。
- 若碰撞同样占比显著，可按同法批量化，同样逐元素等价。

## 验收

|门|内容|
|---|---|
|O1 等价|固定输入（24语义＋≥32立方体scene，batch 1/16/64/256，含域外起点、起点在占据内、空scene、掠边/角射线）CPU float64与GPU float32：距离与命中`torch.equal`；PcdPanorama Depth全字段相等；随机种子下≥50 Core step的Transition逐字段相等|
|O2 回归|`forem/src/task8_sim/tests`全部通过（CPU＋GPU），新增等价测试|
|O3 性能|重测batch 64/256立方体与语义吞吐与分项，报告提升倍数|
|O4 合规|无训练/optimizer；账本≤1500s；独立Sol high验收|

## 模型与强度（推荐）

|阶段|Codex|Claude备选|理由|
|---|---|---|---|
|实现|gpt-6.1-sol / high|Sonnet5.5 / high|GPU批量遍历与比特等价|
|固定profile执行|gpt-6.1-terra / low（不可用退gpt-6-luna）|Sonnet5.5 / low|判据固定|
|独立验收|gpt-6.1-sol / high（≠实施者）|Sonnet5.5 / high|终审|

## r3交付范围与结果

O1双设备严格等价、O2 CPU/GPU全回归和O3固定四组负载由不同Sol high核原件后O4 PASS。立方体b64/256109.5423/145.3530转移/s，语义94.6227/116.2889；相对R2完整窗口cube64/2566.190×/8.081×、semantic25610.620×，256重复窗口/连续20步差异及公共前缀对照见[RESULTS](RESULTS.md)、[SRC-1194](../../../../../SOURCES.md#src-1194)。优化验收不等于P5/48h门或长训授权。
