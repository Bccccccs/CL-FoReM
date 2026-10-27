# task8.9.3 — 下层SAC长程对照（实验协议设计草案）

## r4当前覆盖（仅准备，pending，尚未执行）

依据[SRC-1210](../../../../SOURCES.md#src-1210)与[准备SRC-1216](../../../../SOURCES.md#src-1216)，本轮只准备C固定清单；旧r2/r3失败、原件与395.0120486840606秒费用完整保留。实际准备gpt-6.1-sol/high；推荐GPT6.1sol/high、Claude Sonnet5.5/high（恢复/完整评估/预算/版本核对），固定执行待父派Terra low，独立Sol high另人核原件。

父最新明确解释235→900仅primary，resume保留原1130；因此primary内部900/timeout920/+10/reservation940，resume1130/1155/+10/1175。8job仍preflight20→B0 primary940→preserve15→resume1175→B3 primary940→preserve15→resume1175→postflight20，合计4300秒。7200−395.0120486840606=6804.9879513159394秒，扣4300余2504.9879513159394秒，至少140秒收尾；这是预算推导，不保证运行能完成。原C账本当前仍3600、active空；父统一扩限前不改账本、不运行。

原r3 64项SHA已只读核对零漂移，新[r4 snapshot](../../../../../logs/task8/t8-train-stage0-20261027/r4-implementation-snapshot.json)保留期望hash且状态PENDING_INIT_DELIVERY_AND_INDEPENDENT_REVIEW，缓存接口null。须等task8.9.1.2生产接口/精确delta与不同Sol独立PASS后才冻结；不静默接受漂移。若10324全量验收在1200秒内不可行或诊断需用户决定，整轮停报，不执行smoke。

[r4固定清单](../../../../../logs/task8/t8-train-stage0-20261027/r4-smoke-plan.md)与[完整argv](../../../../../logs/task8/t8-train-stage0-20261027/r4-smoke-plan.json)、[wrapper](../../../../../logs/task8/t8-train-stage0-20261027/r4-smoke-serial-wrapper.py)均尚未执行。新输出/CSV/report用r4独立路径，256env/100k replay/种子/512→真实resume1000/100+96完整评估不变；首失败、timeout或incomplete停报，无重试、无fresh reset，不3M/mapgen/额外优化。所有剩余reservation+140秒和GPU1无compute每job核验；冻结hash/接口或父释放缺失时拒绝启动。

## C1/C2独立审查修复（2026-10-27，当前覆盖）

状态仍**review**，实际gpt-6.1-sol/high；推荐GPT6.1sol/high、Sonnet5.5/high（跨生产者/消费者身份及随机流核对）。独立报告`r2-independent-c-stage0.md/json`的FAIL及原13pass均保留，不能以13pass否定接口失败。本轮只改C，不改B冻结导出器或task8_sim生产。

- C1已核真实semantic-pool/index.json源split全部smoke；B seed记录split=semantic_transfer是评估角色。C现在严格校验角色、源split、map_id/episode_index/stream0、语义索引相对forem根路径/字节hash/内容身份，job/输出显式携带role/source_split，不放松身份门。
- C2现在每个job建立RandomStreams(episode_seed,1).for_env(0)，同一EnvironmentStreams经env.reset交sampler，并由choose_candidate消费独立other子流；不再由通用validation_seed和batch行号派生候选流。
- 新回归读取真实24语义index，按B冻结finalize实际schema/种子公式生成100+96记录；包括角色/源内容/hash/路径/id/重复/stream反例，以及同job不同batch位置、初始采样消耗不同而other一致的轻量回归。
- RED `0d8f3e7cdc` 2fail7pass（真实role失配与缺少新环境构造函数）；修后`6544bdfdf6` **22 passed/19.86s内部、20.893972854s外层、rc0**。同C账本当前**149.024231501855/3600s**、余**3450.975768498145s**、active空；旧测试/费用保留。没有smoke/196实际episode/长训。

当前snapshot已更新，原13项版本另存`r2-implementation-snapshot-before-review.json`，52冻结源/config仍无漂移；固定清单命令仍适用，测试数由13增至22。新增依据草稿[SRC-1149](../../../../SOURCES.md#src-1149)、[SRC-1150](../../../../SOURCES.md#src-1150)交父登记。下一步由不同Sol再验这两项；无需重跑旧大批量，正式种子发布后的实际接口/完整评估由父全门后安排，仍不加预算/缩协议。

## r2当前状态（2026-10-27）

**review：阶段0实现及13项GPU单测交不同Sol独立验收；未smoke、未完整196episode评估、未3M。** r2授权依据[SRC-1161](../../../../SOURCES.md#src-1161)、[SRC-1162](../../../../SOURCES.md#src-1162)，下方blocked是r1历史快照。实际实施者gpt-6.1-sol/high；推荐GPT6.1sol/high、Sonnet5.5/high（全状态恢复与训练顺序跨模块核对）。

已完成新`task8_lower.training`及`task8_lower_train.py`，消费顺序/旧replay先更新后插入与v5保持；B0原数学、分母4999743、α实际初值1；B3每10转移更新、RLlib温度与转移线性LR。检查点显式包装PCD环境/Core字段、sampler/planner/scene/RNG、SAC/optimizer/replay和pending批次，恢复不调用reset，保留生产拒绝直接pickle护栏。实际两组恢复后的下一更新及下一转移逐元素相同，仅限单测设置。[SRC-1145](../../../../SOURCES.md#src-1145)、[SRC-1146](../../../../SOURCES.md#src-1146)、[SRC-1147](../../../../SOURCES.md#src-1147)、[SRC-1148](../../../../SOURCES.md#src-1148)（条目草稿已交父统一登记）。

正式配置引用`cube-pool-v2/manifest.json`、同目录`evaluation-seeds.json`与既有`semantic-pool/index.json`，种子遵B逐图表：每job独立RandomStreams(episode_seed,1)，stream_index=0；验证100×1、迁移24×4，无test消费。评估实际循环/每250k调度已接入，但完整196episode仍待父在A/B/C全门后调度，不能以计划测试替代。测试＋后续smoke沿原3600s账本，余额以账本实时值为准；无子集开关、不改正式评估规模。

## r1历史快照

状态：**blocked（阶段0部分实现快照；立方体PCD池先导验收失败，父要求停止继续实施/测试；2026-10-27用户原授权阶段0与阶段1：B0、B3各2种子×3M，S3立方体PCD池，[SRC-1160](../../../../SOURCES.md#src-1160)）**。阶段2与其他组未授权；长训启动前须8.9.1成本模型满足启动门（单run≤48h且4卡显存足够），否则报告用户。父[task8.9](../TASK.md)；依据[SRC-1102](../../../../SOURCES.md#src-1102)、[SRC-1101](../../../../SOURCES.md#src-1101)、[SRC-1000](../../../../SOURCES.md#src-1000)。

## 研究问题与假设

问题：task7下层SAC在约1.2–1.5M转移后退化的机制是什么？换到task8环境后是否仍退化？哪种最小训练配置改动能消除它？

|编号|假设|依据|可检验预测|
|---|---|---|---|
|H0|退化依赖旧环境（扫描原点在臂内整帧无效等），新环境下B0不退化|SRC-0549、task8 ghost|B0在新环境中不满足“退化”判据|
|H1|高更新/数据比（UTD=1）导致值函数发散→策略崩塌|v5 Q均值+15→−415、critic loss约×2500（SRC-1101）；RLlib UTD≈0.1不退化（SRC-1000）|UTD 0.1时Q保持有界、不退化|
|H2|温度规则（0.35·exp、α lr 1e-6、0.05冻结）使熵调节失效|v5 α 0.35→0.107→0.556；RLlib α自由学习|α改RLlib规则后熵与α轨迹平稳、不退化|
|H3|学习率按更新数指数衰减过快/与UTD耦合|v5 1.5M时lr已降至2.5e-5|单独影响小于H1/H2（作为B3组成部分，不单列）|

H4（`cbl_continue`下失败惩罚累积导致Q偏负）属于奖励/终止语义，本协议**只记录诊断，不改**；若B0与B3都退化再提交用户决定。

## 实验设计

**共同条件**（所有组相同）：task8 v3＋ghost-v1，`sync_v5` profile（同步变体、`failure_mode=cbl_continue`、`async_time_penalty=0`、`episode_end_bootstrap=true`、`ik_avoid_collision=true`）；74/75维观测、动作、奖励、终止、网络结构、batch 256、replay 100k、γ0.99、τ0.001、目标熵−3、梯度裁剪10、动作随机预热1000转移、256环境；地图池按8.9.2决定（推荐S3：立方体同分布训练/验证＋24语义图迁移测试）。

|组|更新/数据比|温度规则|学习率日程|说明|
|---|---|---|---|---|
|B0|每转移1次|capped（0.35·exp，α lr 1e-6，≤0.05冻结）|按更新数指数1e-4→1e-6|v5配置在新环境的基线（检验H0）|
|B3|每10转移1次|RLlib（初值1.0，α lr 1e-4线性降至1e-6，无上限/下限）|按转移数线性1e-4→1e-6|RLlib对齐（同时检验H1–H3）|
|B1（阶段2）|每10转移1次|同B0|同B0|只换UTD，归因H1|
|B2（阶段2）|每转移1次|同B3|同B3|只换温度/学习率，归因H2/H3|

**分期**：阶段1跑B0、B3各2个种子，每run 3M转移（退化起点1.2–1.5M，v5在3M为5/100，留约2倍余量）。阶段2按阶段1结果决定：B0退化且B3不退化→加B1、B2各2种子并为B0/B3补第3种子；B0不退化→H0成立，报告并由用户决定后续；B0、B3都退化→H1–H3不足以解释，报告并请用户决定是否检验H4。

**评估**（确定性动作）：每250k转移一次；①task7协议的100张验证图（按S3导出为PCD）各1个episode，指标严格成功、到达/失败/超时率、失败类型；②24张语义图×每图4个固定种子共96个episode作迁移评估（不参与选模）。

**诊断**（每1000转移）：两个critic的Q均值与|Q|最大值、critic/actor/α loss、α、策略熵、log_std范围、回放奖励均值与失败转移比例、回放样本年龄；每次评估另算验证episode首步Q与折扣蒙特卡洛回报之差（值偏差）、动作分量分布。

## 预注册判定（工程选择，待用户确认）

- **退化**：最后3次验证（2.5M、2.75M、3M）严格成功均值 ≤ 该run峰值 − 15个百分点。理由：100图、p≈0.5时单次评估标准差约5个百分点，峰值取自12次评估的最大值有正偏，15个百分点约为3个标准差。
- **消除退化**：该组2个种子均不满足“退化”。
- **值函数发散**：|Q|均值超过 max|r|/(1−γ)（回放中观测到的最大单步奖励绝对值的折现上界），记录首次越界步数；作为机制证据，不单独作为成败判据。
- 结论只按组内全部种子报告，不挑选种子；迁移评估只报告，不用于判定或选模。

## 停止规则（工程选择）

损失或Q出现非有限值立即停止并保存；|Q|最大值超过该run在500k时的10倍时停止并保存（避免浪费算力，沿task7看门狗规则b思路）；停止的run记为“发散停止”，计入判定。

## 执行前置（执行阶段0，需随训练授权一并批准）

1. 训练入口接入task8环境：`task7_lower.training`的环境构造改为可注入`PcdEpisodeEnv`，验证/迁移评估协议按上文实现；旧task7入口保持不变。
2. 新增配置开关：每N转移更新一次（UTD）、RLlib温度规则（α初值1、α学习率线性衰减）、按转移数线性学习率；参考task6 D14已有实现（`forem/scripts/scwm_sac.py`，[task6.1 RESULTS](../../../task6/task6.1/RESULTS.md) L124），B0配置必须与v5逐项一致。
3. 这些开关的单元测试会执行SAC更新，属于训练操作，须在训练授权范围内运行。
4. 按8.9.1结论实施（或不实施）性能优化；有界端到端smoke确认吞吐后再启动长训。

## 成本（待8.9.1实测后填写）

阶段1：4个run×3M转移=12M转移。若环境成本接近task7（v5约48.7转移/s，UTD=1），单run约17h；B3更新次数减少约90%，按task7.18.3分项（该E2E窗口更新约占27%，剔除冷启动reset与checkpoint后约60%）估计长训中可快约1.5–2倍（推断，待8.9.1核实）。实际以8.9.1成本模型为准，定稿时给出GPU分配与墙钟预算，不足时报告而不缩短步数。

## 交付

定稿协议（本TASK修订版）＋执行PROCEDURE与派发prompt；执行后RESULTS按预注册判定报告。

## 模型与强度（推荐）

|阶段|Codex|Claude备选|理由|
|---|---|---|---|
|协议审查|gpt-6.1-sol / high|Sonnet5.5 / high|研究设计与统计判定|
|执行阶段0实现|gpt-6.1-sol / high|Sonnet5.5 / high|训练入口与SAC开关、等价性|
|长训运行与监控|gpt-6.1-sol / medium|Sonnet5.5 / medium|按固定协议运行、记录|
|结果分析与独立验收|gpt-6.1-sol / high（≠实施者）|Sonnet5.5 / high|归因与判定|


## 2026-10-27 阶段0当前交付边界

父因地图池先导验收失败要求停在可审阅快照，本节点不补做其余功能、不再测试/smoke。`task8_lower`只完成部分SAC开关、诊断与评估代码草稿；没有训练主循环、CLI、完整检查点与精确恢复，不能用于正式训练。实际测试4通过1失败，不满足阶段0验收。[当前RESULTS](RESULTS.md)、[SRC-1140–1143待父登记](../../../../SOURCES.md#src-1140)。

B0保留v5实际初值α=1、首次update后0.35·exp，以及指数日程分母4,999,743；本轮3M总转移预算没有把B0日程分母改成3M。B3按3M转移线性日程。固定迁移种子草稿与正式池manifest尚待对接；不宣称当前配置可执行。


## 有界smoke准备（尚未执行）

C修复后实现独立PASS；父本轮要求只准备。已建独立lower_smoke_B0_r2.json/lower_smoke_B3_r2.json，仅checkpoint_interval=1000，其余正式参数及3M/v5日程不变。每组先512（实际SAC更新并保存）→同配置/hash从primary-final恢复到1000触发1000诊断/完整196评估；在评估前覆盖真实恢复，禁止fresh reset。固定8job总reservation2970s，C当前余额3450.975768s，预留480.975768s收尾（≥140s）；没有执行任何job、未花新增测试/smoke预算。

完整计划/argv/每阶段deadline/监控/STOP/不完整边界：[计划](../../../../../logs/task8/t8-train-stage0-20261027/r2-smoke-plan.md)、[固定命令](../../../../../logs/task8/t8-train-stage0-20261027/r2-smoke-plan.json)。必须A完整profile与独立验收、B全10300/200与独立验收及父释放后才能派Terra执行；预算不足保留incomplete，不重跑196、不缩环境/回放/评估、不长训。显存/评估成本均仅条件推导，不能称就绪。依据草稿[SRC-1151](../../../../SOURCES.md#src-1151)、[SRC-1152](../../../../SOURCES.md#src-1152)已交父，实际Sol high，推荐GPT6.1sol/high、Sonnet5.5/high（跨恢复和预算约束）；固定执行Terra、Sol查原件。


## r3停止覆盖（blocked，真实smoke首失败）

优化O1–O4和正式池独立PASS后，按[SRC-1190](../../../../SOURCES.md#src-1190)释放原8job smoke。preflight通过，但B0-primary初次256环境reset采样触及235秒deadline，SamplingIncomplete/rc1；CLI243.166660481秒，0动作/0转移，已保存中断状态。按固定首失败即停，后六job（preserve/resume、B3和postflight）未执行；不重试、不增加额度、不3M。实际Terra/low，独立Sol/high后审，推荐GPT6.1sol/Sonnet5.5 high核验采样与恢复路径，固定执行Terra low。[SRC-1200](../../../../SOURCES.md#src-1200)、[独立SRC-1198](../../../../SOURCES.md#src-1198)。

C账本395.0120486840606/3600秒、余3204.9879513159394、active空。meta steps/action_calls/env_actions均0，resume_safe只是保存元数据，未验证正式CLI恢复，不构成恢复授权。无有效训练吞吐/完整196耗时/torch峰值；设备1Hz采样峰值11306MiB不能当正式训练峰值。执行表总stopped，局部running陈旧标签与exit_code1并存，现场以账本/进程核查为准。证据及原件详[SRC-1200](../../../../SOURCES.md#src-1200)。下一步交Claude决定有界初始采样诊断/预算方案，保持原协议与失败记录，未经新派发不继续。
