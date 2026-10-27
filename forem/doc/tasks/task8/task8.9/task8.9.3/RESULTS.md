# task8.9.3 — 结果与交接

**2026-10-27 已作废（closed）**：用户指令“现在的8.9作废吧，要优化好了整体的地图再开始训练”（[SRC-1220](../../../../SOURCES.md#src-1220)）。本节点不再执行；以下为作废前的历史状态与记录，原样保留。

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

## r2当前交付（2026-10-27）

**review：实现者13 passed，待Terra固定验证及不同Sol high独立验收；未smoke、未完整196评估、未3M。** 实际gpt-6.1-sol/high，推荐GPT6.1sol/high、Sonnet5.5/high；理由为恢复与SAC逐元素等价核对。原r1失败保留于下方，r2沿原账本继续，没有重置预算。

新增`task8_lower/training.py`、`scripts/task8_lower_train.py`、`tests/test_recovery.py`，更新SAC护栏/浮点测试、正式池与评估种子读取、B0/B3配置。仅改本节点授权代码与文档；未改task7/task8_sim生产。52冻结源/config SHA256与父r1前照一致，限制为该52文件集，不泛称全部历史产物。[snapshot](../../../../../logs/task8/t8-train-stage0-20261027/r2-implementation-snapshot.json)。[SRC-1145](../../../../SOURCES.md#src-1145)、[SRC-1146](../../../../SOURCES.md#src-1146)、[SRC-1147](../../../../SOURCES.md#src-1147)、[SRC-1148](../../../../SOURCES.md#src-1148)（条目草稿已交父统一登记）。

### 新鲜验证与保留失败

最终调试测试`918e2b4bb1`：**13 passed / 20.45s内部、21.494841542s外层，rc0，无timeout**，物理GPU1/TASK89_DEVICE=cuda/forem-dev；[原日志](../../../../../logs/task8/t8-train-stage0-20261027/918e2b4bb1.log)。全部受原run_budget.py约束，账本当前累计**103.252727066167/3600s**、余**3496.747272933833s**、active空；后续以账本为准。

- B0一次真实更新loss/网络与只读v5逐元素一致；B0/B3各自实际PCD环境（1环境、batch2、replay8；旧prepare夹具池，仅作恢复测试）的完整checkpoint，恢复后先消费保存的pending转移并做下一真实更新，再执行下一环境transition；loss、全部SAC/Adam/scheduler/alpha、replay内容/采样RNG与转移全部张量torch.equal，恢复没有reset。已开启dls_cuda_graph配置，但不声称特定测试必触发非空DLS graph cache；纯缓存省略并重建。
- B3线性中点/终点、自由α>1与日程roundtrip、UTD整除编号；末LR断言仅改为rel0/abs=4×ulp(1e-4)，原日程不动。
- 非有限奖励在critic optimizer前停止；新注入NaN梯度在critic写前停止且参数未改；非有限policy动作在环境动作前拒绝；合成500k/10倍Q规则通过。
- STOP文件与SIGTERM在初始reset前保存完整interrupted状态，信号handler恢复；属于停止控制单测，没有训练主循环环境交互。诊断测试证明全局CPU/CUDA随机流未扰动，奖励/失败/年龄字段正确。
- 100+96固定计划的数量/唯一性/test排除通过，非真实196episode评估。

r2首次RED `b4428694ed` 2fail（training模块缺失）；`cdc44a99aa` 1fail6pass（恢复测试夹具无train split，改用该夹具已有split）；`c5eb771b8b` 1fail6pass（cuda设备别名元数据不等，canonical重建修复）；`4967924086` 7pass；梯度RED `9f8e50f551` 显示NaN梯度可先污染critic再在policy Q拦截，已加写前梯度护栏；`8adad713a6` 9pass；`b291bd3dba` 11pass1fail（诊断均值17/3的binary64末位精确断言，容差修测试）；动作RED `dba021b06b` 1fail（原select_action未拒绝NaN），新护栏后最终13pass。所有失败/耗时原件保留在同账本，不把中间通过当最终验收。

### 实现边界、风险与下一步

主循环/CLI接入UTD、每1000诊断、250k评估与checkpoint、写前环境动作账本、STOP/信号/有界deadline、非有限/Q看门狗；恢复显式保存env属性/Core属性，保留共享scene/kin/robot引用、planner/streams/replay/SAC/RNG/pending，生产环境pickle/load_state_dict护栏未改。部分optimizer写入后异常的checkpoint仅供取证，明确unsafe_update拒绝续跑。

B0逐项配置表在[日志](../../../../agent_logs/task8/task8.9/task8.9.3/20261027-sol-training.md)：除已授权task8接入schema、3M总额、PCD池/后端差异，其余v5原config字段相等；数学/网络/优化器实际属性继承原类。正式逐图种子来自B的`evaluation-seeds.json`，不宣称与v5评估随机流相同。

下一步父派Terra执行[固定清单](../../../../../logs/task8/t8-train-stage0-20261027/r2-fixed-verification.json)，不同Sol读原件独立验收；当前没有本节点后台任务/优化实施。待A/B/C全门后，父在剩余C预算内调度B0/B3各短run并覆盖完整评估/checkpoint/resume，之后停交Claude。当前真实196评估墙钟/训练吞吐/峰值显存仍无实测，不作长训就绪、≤48h或四卡可运行结论；不缩评估子集，预算不足保留incomplete报告。

## r1历史快照（保留失败与费用）

状态：**blocked（阶段0部分实现，未通过；2026-10-27父因地图池先导验收失败要求停止）**。当前负责人Codex；实际显式派发gpt-6.1-sol/high。推荐GPT6.1sol/high、Sonnet5.5/high，理由为SAC等价性及精确恢复跨模块核对。训练授权依据[SRC-1160](../../../../SOURCES.md#src-1160)，停止依赖由父task8.9.2记录，本节点不自行判定地图门。

## 当前快照

已新增`forem/src/task8_lower/{__init__,sac,replay,diagnostics,evaluation}.py`、`tests/test_stage0.py`、`forem/config/task8/lower_train_B0.json`与`lower_train_B3.json`。代码位于新目录，不修改task7_lower原文件、task7配置或产物。无提交/推送/合并。[SRC-1140](../../../../SOURCES.md#src-1140)。

- SAC保留原Actor/TwinQ/观测与loss表达式，实现全局转移编号每N条更新判定（旧replay>256且编号整除N）、RLlib alpha与转移线性学习率开关、非有限loss/Q保护。B0实际alpha初值1，首次更新后应用0.35；B0 total_updates仍4999743（5M v5日程），本轮total_transfers=3M；B3线性日程分母3M。代码尚未被训练主循环消费。
- Replay只在原数据/采样外增加插入转移编号及失败元数据；诊断草稿含双critic Q、loss、alpha/熵/log_std、回放奖励/失败/年龄；Q保留v5前256物理ring slot口径，奖励/失败/年龄统计全有效ring。诊断使用fork_rng防止额外熵采样扰动训练随机流，但尚未测试验证。
- 评估计划合成测试确认100张50/50立方体验证图×1、24语义图×4固定种子、test条目不被使用。实际评估循环草稿含首步双Q/折扣MC/动作分布与不完整标记；未在真实环境跑过，不能宣称196episode协议通过。

## 有界测试原始证据

共享新账本：[budget.json](../../../../../logs/task8/t8-train-stage0-20261027/budget.json)，同目录run_budget.py复制旧task8.8 runner；外层reservation与容器内timeout双重限制。[SRC-1141](../../../../SOURCES.md#src-1141)。全部命令使用已运行forem-dev、CUDA_VISIBLE_DEVICES=1、TASK89_DEVICE=cuda、PYTHONDONTWRITEBYTECODE=1、PYTHONPATH=/root/mm_husky_ws/src及pytest no:cacheprovider，没有启动环境smoke或长训。

|账本ID|阶段|外层墙钟s|退出码|实际结果|
|---|---|---:|---:|---|
|f98ea56f2e|RED，外50s/内45s上限|1.916767674|1|5 failed：新sac/diagnostics/evaluation模块缺失|
|228e1208fd|首次实现验证，外90s/内85s上限|5.872172734|1|4 passed，1 failed；pytest内部4.87s|

原日志：[RED](../../../../../logs/task8/t8-train-stage0-20261027/f98ea56f2e.log)、[首次实现验证](../../../../../logs/task8/t8-train-stage0-20261027/228e1208fd.log)。当前累计**7.788940408/3600s**，余额3592.211059592s，active={}；父要求停止时第二命令已提交，允许正常退出后记账，没有再启其他测试。[SRC-1142](../../../../SOURCES.md#src-1142)。

通过项：①B0一次真实网络SAC更新的全部返回loss及Actor/双critic/target参数，与只读v5在相同初始状态/随机流下逐元素torch.equal一致，初值alpha和更新后LR一致；②含NaN奖励时更新在critic optimizer写入前抛错，critic参数不变且update_count=0；③500k Q参考/10倍停止与非有限规则合成测试；④评估计划数量、唯一性及test排除。

失败项：`test_b3_transition_schedule_alpha_unbounded_and_roundtrip`最后一条精确等于1e-6断言失败，实际9.999999999999972e-7。该测试此前断言（中点actor/critic/alpha LR约5.05e-5、两次真实SAC更新、alpha>1未冻结、SAC roundtrip恢复env_steps和alpha）执行通过，但**整项仍失败**。当前未改代码或测试、未重跑。不能宣称全测试通过或阶段0完成。

## 尚未实施/验证与风险

1. **没有**`task8_lower/training.py`或`scripts/task8_lower_train.py`，未完成训练入口/UTD接入、STOP/信号处理与保存、全状态checkpoint/精确恢复、实际1000转移诊断、评估调度。
2. PcdEpisodeEnv.__setstate__/load_state_dict明确拒绝恢复，因此不能照搬task7 pickle env；显式包装/重建方案仅已向父说明，**未实现**。必须保留Core/state/scene/route/Grid/episode RNG/采样器与planner/pending批次等并逐元素比较恢复后的下一转移和更新；fresh reset不能充当恢复。
3. 配置`transfer_pool`仍是最初占位错误路径`.../t8-voxv3-20261026/r4/source/manifest.json`；父后来提供的正式路径为`.../t8-exec-20261026/semantic-pool/index.json`，停止时尚未改。正式cube-pool先导失败、全量未导出，配置不能运行。迁移四种子草稿[14718,24718,34718,44718]尚未与pool提供的evaluation-seeds.json核对，不能当最终冻结协议。
4. Replay诊断、实际环境评估、完整恢复、梯度/alpha非有限保护覆盖、设备/optimizer/峰值显存与正式B0/B3逐项差异验收均未完成；没有CPU回归、task8_sim全目录回归或独立验收。没有停止/重建他人进程/容器。
5. 未执行smoke、未测训练吞吐/196episode评估成本，不作≤48h/四卡可启动结论，不把SAC局部更新测试当训练效果或退化根因证明。

## 交接

目标与授权仍按TASK/SRC-1160；当前负责人Codex已停止本轮实施，未留后台训练/测试。下一步先由用户决定地图池导出处理，父重新指派后再核本快照与账本，完成上述缺项、修当前失败、独立验收后才考虑同账本smoke。具体命令、代码归属与SOURCES草稿见[独立日志](../../../../agent_logs/task8/task8.9/task8.9.3/20261027-sol-training.md)。[SRC-1143](../../../../SOURCES.md#src-1143)。1144–1159未使用，不补造证据。

## 父汇总补记

不同Sol high已只读核查本节点保存原件/预算/入口存在性，确认部分成果与未完成项；没有新运行本节点测试/性能，**不是本节点全项独立验收通过**。地图严格内部缺格已独立成立，详[SRC-1125](../../../../SOURCES.md#src-1125)与[独立报告](../../../../../results/task8/t8-phase2-20261027/independent-review.md)。当前继续保持blocked、无smoke/长训，等待用户采样规则决定。


## 有界smoke准备（尚未执行）

C修复后实现独立PASS；父本轮要求只准备。已建独立lower_smoke_B0_r2.json/lower_smoke_B3_r2.json，仅checkpoint_interval=1000，其余正式参数及3M/v5日程不变。每组先512（实际SAC更新并保存）→同配置/hash从primary-final恢复到1000触发1000诊断/完整196评估；在评估前覆盖真实恢复，禁止fresh reset。固定8job总reservation2970s，C当前余额3450.975768s，预留480.975768s收尾（≥140s）；没有执行任何job、未花新增测试/smoke预算。

完整计划/argv/每阶段deadline/监控/STOP/不完整边界：[计划](../../../../../logs/task8/t8-train-stage0-20261027/r2-smoke-plan.md)、[固定命令](../../../../../logs/task8/t8-train-stage0-20261027/r2-smoke-plan.json)。必须A完整profile与独立验收、B全10300/200与独立验收及父释放后才能派Terra执行；预算不足保留incomplete，不重跑196、不缩环境/回放/评估、不长训。显存/评估成本均仅条件推导，不能称就绪。依据草稿[SRC-1151](../../../../SOURCES.md#src-1151)、[SRC-1152](../../../../SOURCES.md#src-1152)已交父，实际Sol high，推荐GPT6.1sol/high、Sonnet5.5/high（跨恢复和预算约束）；固定执行Terra、Sol查原件。


## r3停止覆盖（blocked，真实smoke首失败）

优化O1–O4和正式池独立PASS后，按[SRC-1190](../../../../SOURCES.md#src-1190)释放原8job smoke。preflight通过，但B0-primary初次256环境reset采样触及235秒deadline，SamplingIncomplete/rc1；CLI243.166660481秒，0动作/0转移，已保存中断状态。按固定首失败即停，后六job（preserve/resume、B3和postflight）未执行；不重试、不增加额度、不3M。实际Terra/low，独立Sol/high后审，推荐GPT6.1sol/Sonnet5.5 high核验采样与恢复路径，固定执行Terra low。[SRC-1200](../../../../SOURCES.md#src-1200)、[独立SRC-1198](../../../../SOURCES.md#src-1198)。

C账本395.0120486840606/3600秒、余3204.9879513159394、active空。meta steps/action_calls/env_actions均0，resume_safe只是保存元数据，未验证正式CLI恢复，不构成恢复授权。无有效训练吞吐/完整196耗时/torch峰值；设备1Hz采样峰值11306MiB不能当正式训练峰值。执行表总stopped，局部running陈旧标签与exit_code1并存，现场以账本/进程核查为准。证据及原件详[SRC-1200](../../../../SOURCES.md#src-1200)。下一步交Claude决定有界初始采样诊断/预算方案，保持原协议与失败记录，未经新派发不继续。
