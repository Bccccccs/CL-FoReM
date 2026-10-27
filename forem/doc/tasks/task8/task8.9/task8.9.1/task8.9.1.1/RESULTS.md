# task8.9.1.1 — 结果与交接

**2026-10-27 已作废（closed）**：用户指令“现在的8.9作废吧，要优化好了整体的地图再开始训练”（[SRC-1220](../../../../../SOURCES.md#src-1220)）。本节点不再执行；以下为作废前的历史状态与记录，原样保留。

状态：**done（O1–O4不同Sol独立PASS；仅优化交付，父P5仍待smoke与缺项）**。本轮只交付编码与必要测试，不声称优化吞吐已证明，不启动训练。[SRC-1190](../../../../../SOURCES.md#src-1190)

## 目标、授权、负责人

按用户/Claude SRC1190仅实现SceneBatch跨场景森林raycast，逐射线算术不变，保留旧循环参照。实际负责人Codex `/root/opt_r3`，父显式指定gpt-6.1-sol/high；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由是GPU几何遍历、设备与状态等价需跨层核查。固定profile交Terra low，不同Sol high终验由父安排。本实施者没有再派Agent。

## 实际改动及版本

生产改动仅 [scene.py](../../../../../../src/task8_sim/scene.py) 的SceneBatch：默认 `raycast_backend='forest'`，可显式 `'loop'` 使用原逐场景循环；唯一scene的BVH节点拼接，children加节点偏移，每行保留自己的root；每packet最多65536射线，调用原_slab及同一amin归约。65536是有界工作存储的工程选择，未声称最优。没有修改VoxelScene、_slab、v3体素化、量程、地面、PcdPanorama、碰撞、Core或task7。碰撞占比小，本次不优化。[SRC-1191](../../../../../SOURCES.md#src-1191)

select继承后端，replace仅更新行引用并失效森林；序列化剔除纯派生森林缓存，恢复后基于实际scene张量惰性重建，兼容没有新字段的旧SceneBatch状态，不改task8_lower检查点协议。新增 [test_scene_forest.py](../../../../../../src/task8_sim/tests/test_scene_forest.py) 覆盖映射/空scene/select/replace/恢复/输入拒绝；新增 [task8_forest_accept.py](../../../../../../scripts/task8_forest_accept.py) 执行O1。仅在现有test_pcd_env.py增加可选TASK8_TEST_ARTIFACT_ROOT，防全GPU回归覆盖旧cube-default证据，默认输出不变。[SRC-1191](../../../../../SOURCES.md#src-1191)、[SRC-1192](../../../../../SOURCES.md#src-1192)

原始scene SHA256 `d9d98d98d0dd51094eecb999d24e0eaf44fb6bcd7611275bf818732fb7f6de55`；交付SHA256 `d8a9dfdd261161b3e65aa38b6e19a5a61496a0781334213cb5ef8b3028507041`。原件/明确diff在 [scene-before.py](../../../../../../results/task8/t8-perf-opt-20261027/scene-before.py)、[scene.diff](../../../../../../results/task8/t8-perf-opt-20261027/scene.diff)。测试路径原文件保存在同目录test-pcd-env-before.py，原hash `3b5fc6ed116a5d435cab2220ae961324b98048efe0f3c40039aac7fd0c209f7e`。

## 实际验证

全部命令完整argv、开始UTC、退出码、外层wall及stdout以 [budget.json](../../../../../../logs/task8/t8-perf-opt-20261027/budget.json) 和同名log为准；未使用容差替代相等。[SRC-1191](../../../../../SOURCES.md#src-1191)、[SRC-1192](../../../../../SOURCES.md#src-1192)

|命令|结果|外层wall(s)|
|---|---|---:|
|red-forest|3 fail，均因缺少raycast_backend接口；预期RED|2.598671|
|green-forest|3 passed|2.614233|
|o1-cpu64|完整O1 PASS|122.907701|
|o2-cpu|131 passed / 11 CUDA专门项skip|27.404309|
|o1-gpu32|完整O1 PASS|113.898000|
|o2-gpu|142 passed / 0 skip|55.851225|
|freeze-profile-inputs|4个冻结hash匹配，4jobs未执行|0.029858|

O1分别读取固定32张立方体和24张语义PCD构建CPU float64/GPU float32场景，再加empty及闭合面/边角fixture。每设备b1/16/64/256均覆盖全部58scene（小batch轮转），每行96射线包括域外进出、占据内起点、精确packed面、轴向、掠边/角；距离和有限命中torch.equal。每设备四个batch还各做完整360×90 Panorama，Depth的distance/valid/self_hit/points/origin_inside_self/sensor_policy/self_occlusion七字段全部相等。CPU/GPU各自与自身旧路径比较，不要求跨dtype位等。[O1 CPU原件](../../../../../../results/task8/t8-perf-opt-20261027/o1-cpu64.json)、[O1 GPU原件](../../../../../../results/task8/t8-perf-opt-20261027/o1-gpu32.json)，依据[SRC-1191](../../../../../SOURCES.md#src-1191)。

每设备50次真实Core.step、100条active转移；CPU提交199子步，GPU179子步；全部Transition13字段（含前后完整observation与raw_action）及实际base/q/s、Grid.height逐元素相同。输入用原接受的两个非空立方体episode与固定随机动作，无新采样/训练。GPU每步断言forest/loop后端，reset次数0；CPU执行版accept-cpu-executed.py保留，后续reset即使发生也只replace，保持loop。[SRC-1191](../../../../../SOURCES.md#src-1191)

O1/O2运行时禁止Optimizer构造与Tensor/autograd backward，所有guard零。GPU每次前nvidia-smi compute为空，使用已运行forem-dev、物理GPU0；未建停容器/他人进程。GPU回归输出保存在本run `regression-gpu/`，未覆盖旧测试JSON。CPU的GPU写产物专门项skip。新账本累计 **325.3039954025 / 1500s**，余 **1174.6960045975s**，active=null；全部命令正常退出，无本节点后台任务。[SRC-1192](../../../../../SOURCES.md#src-1192)

## O3/O4与交接

已准备未执行 [r3-fixed-profile-jobs.json](../../../../../../results/task8/t8-perf-opt-20261027/r3-fixed-profile-jobs.json)：cube/semantic各b64/256，warmup2+20完整测量step，原profile脚本/actor/episodes/随机seed不变，新root仅复制prepare描述并引用R2原缓存。每job上限210s、脚本200s，逐命令核GPU0空闲、冻结hash及账本余额，保留>=150s给独立验收/P5；首非零/不完整/guard非零即停，不自动重试。由父安排Terra执行，本实施者未重复profile。[SRC-1194](../../../../../SOURCES.md#src-1194)待原件后补；Terra执行来源1193独立记录。

父接下来安排不同Sol high核diff/原始结果与必要有界复核，再固定profile；所有测试/profile/独立验收及后续P5额外成本继续同1500s账本，不重置。完成后父followup本实施者汇总性能及来源1194。当前没有新吞吐/提速倍数，不以O1/O2替代O3/O4，也不据此允许正式长训。风险仅固定输入覆盖有限、未证明连续全集/完整正式地图分布/训练工期，场景缓存显存/完整训练显存待O3及C smoke实测。

来源草稿 [sources-r3-draft.md](../../../../../../results/task8/t8-perf-opt-20261027/sources-r3-draft.md)，共享SOURCES/PROGRESS及父文档由父登记。本次无提交/推送/合并，无task7文件和历史产物修改。

## r3固定性能原件复核与最终优化交付

上文“未执行/待办”为编码交接时快照，本节覆盖其当前状态，历史日志/费用保留。Terra gpt-6.1-terra/low于12:31–12:33按固定四job执行，Sol `/root/opt_r3` gpt-6.1-sol/high复核全部JSON/CSV/固定日志/账本；不同于实施者的Sol `/root/review_r3` gpt-6.1-sol/high已判O3固定负载PASS、O4 PASS。[SRC-1193](../../../../../SOURCES.md#src-1193)、[SRC-1194](../../../../../SOURCES.md#src-1194)，[独立最终原件](../../../../../../results/task8/t8-phase2-20261027/r3-independent-opt-final.json)。推荐GPT6.1sol/Sonnet5.5 high作跨模块归因/验收，固定执行Terra low；实际与推荐严格区分。

|负载|有效转移/测量秒|转移/s|相对R2全窗口|Torch allocated/reserved峰值GiB|
|---|---|---:|---:|---|
|cube64|1280/11.684982|109.542321|6.190×|3.369/4.211|
|cube256|5120/35.224586|145.353020|8.081×|3.764/4.809|
|semantic64|1270/13.421731|94.622670|无R2基准|4.655/5.930|
|semantic256|5074/43.632694|116.288947|10.620×|5.069/6.645|

每组warmup2+20完整连续测量step，guard0；全部raw分项n/sum/p50/p95/max/CUDA events累计、逐步transfer/wall/sim、hash/CSV已重算。cold独立；semantic64/256测量期分别2/4次cached factory ended-reset，所以raycast22/24次合法；不是cold污染，也不是随机新episode采样成本。[summary-r3.json](../../../../../../results/task8/t8-perf-opt-20261027/summary-r3.json) / [summary-r3.md](../../../../../../results/task8/t8-perf-opt-20261027/summary-r3.md)，依据[SRC-1194](../../../../../SOURCES.md#src-1194)。

R2 cube256/semantic256为重复10+10/8+6+6前缀，R3连续20步；表中倍数仅同“有效转移/loop wall”完整窗口比，不声称20步严格配对。旧每窗公共前缀step非wall元数据逐字段一致，按旧窗口长度加权R3前缀后cube64/256、semantic256比为6.190×/7.518×/11.867×；复用原样本，不是新增独立测量/置信区间。语义64无旧基准。新64→256吞吐cube1.327×、semantic1.229×，环境数4×不等于吞吐4×。[SRC-1194](../../../../../SOURCES.md#src-1194)

cube256的raycast13.543362s/loop38.45%，collision24.11%、IK12.22%、replay13.61%；semantic256分别raycast14.991536s/34.36%、collision25.20%、IK16.20%、replay10.90%。嵌套项不能相加。设备/线程同R2，CUDA0 float32；GPU CSV为全命令1Hz，不能解释成纯GPU kernel活跃时间。固定64/24缓存场景、replay1024、冻结actor、仪器同步及旧无更新消费路径，不代表正式B0/B3、10000正式池或四worker训练显存/工期。[SRC-1194](../../../../../SOURCES.md#src-1194)

### P5静态设计与保留缺项

`U_k(N)=max(0,floor(N/k)-floor(257/k))`（B0 k1/B3 k10）；1000转移更新743/75、3M更新2,999,743/299,975。smoke更新密度.743/.075低于长期约1/.1，不直接以smoke吞吐乘3M。修正式 `c_steady_g=c_observed_loop_g+(rho_formal_g-rho_observed_g)*c_update_g+delta_replay_fill_g+delta_state_distribution_g`；loop先剥离cold/reset/diagnostic/save/eval，独立c_update当前CLI计时不可识别，须留符号。[SRC-1194](../../../../../SOURCES.md#src-1194)

3M公式含3000诊断、12次完整100+96合并评估、12次周期完整CP+1次final完整CP、随机reset、明示恢复情景及日志/四worker争用；详细单位/定义/提取方法在summary.cost_framework。smoke512/1000 CP只存[:size]，不是满100k；每行98,925B、正式100k有效行仅回放payload9,892,500,000B。满回放保存/restore时延、同组更新增量、后warmup分布与缓存增长等仍未知，不填0、不伪造评估100/96独立计时，不用旧task7更新均值当新测量。等待父在C smoke后followup成本，不因本节点done启动3M。[SRC-1194](../../../../../SOURCES.md#src-1194)

### 最终预算、失败与交接

首次只读汇总rc1为报告脚本argv切片含`--`，不是O1/数据不一致；修正后rc0，日志全部保留。仅复算numpy/stdlib分位数允许1e-12末位差，不放宽O1 torch.equal。新增汇总脚本 `forem/scripts/task8_profile_summarize_r3.py`；没有新测试/profile或生产代码修改。四profile新增147.433309339s，报告复算合计0.295809982s。

最终新账本 **473.033114723861/1500s**，余 **1026.966885276139s**、active=null；旧R2账本/失败未重置。scene冻结hash仍d8a9dfdd261161b3e65aa38b6e19a5a61496a0781334213cb5ef8b3028507041。父获完整1194草稿及summary，8.9.1父三文档同步此汇总；共享SOURCES/PROGRESS/task8.9父文档仍由父维护。无本节点后台任务，无提交/推送/合并；本轮结束，待C smoke后followup P5。
