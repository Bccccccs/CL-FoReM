# task8.9.3 — 执行流程（草案）

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

## r2执行与交接（2026-10-27）

**review：稳定实现交固定验证和不同Sol验收；下文r1停止记录保留。** 实际gpt-6.1-sol/high；推荐GPT6.1sol/high、Sonnet5.5/high（精确恢复、控制与数据顺序）。本层仍恰有TASK/PROCEDURE/RESULTS，不新增子任务。

1. 只用已运行forem-dev、核空的GPU1，原`logs/task8/t8-train-stage0-20261027/run_budget.py`覆盖全部测试/验收/smoke，累计≤3600s，不另建额度。
2. 新训练CLI：`python3 -B scripts/task8_lower_train.py --config config/task8/lower_train_B0.json --output <独立run目录> --transfers <总停止转移数> --max-wall-s <本次上限>`；B3切配置，恢复加`--resume <完整checkpoint.pt>`，保持相同配置。实际CLI正式运行尚未执行。
3. 主循环在环境ID升序逐条消费pending batch；先根据全局下一转移号判UTD并从旧replay更新，后插入该转移。随机动作预热1000条、诊断固定1000条；checkpoint间隔正式250k，checkpoint持有validation_pending以便中断恢复继续评估。
4. 环境构造可注入PcdEpisodeEnv，科学profile必须sync_v5；环境reset只用于新run/结束episode，load_checkpoint恢复显式字段后禁止fresh reset。显式保存版本/源码合同和池hash；不兼容或半次optimizer失败的forensic checkpoint拒绝续跑。
5. STOP文件、SIGTERM/SIGINT、max-wall、SamplingIncomplete保存interrupted.pt；Q/损失/梯度/动作/α非有限或500k后Q超过参考10倍保存diverged.pt。损失/梯度在optimizer写入前检查；若更新中途已产生写入，unsafe_update标记使后续恢复拒绝。不静默跳过样本/更新。
6. 完整checkpoint、独立actor及meta均临时文件写入后原子替换；沿用写前interaction intent/complete账本。恢复若未保存的环境动作比checkpoint多，budget-safe门拒绝预算倒退。
7. 评估严格使用B种子表的100个validation与96个semantic_transfer job；每job独立stream0，迁移不选模；保存首步双Q、折扣MC/值偏差、动作分量与失败指标。取消/超时时保存incomplete，不能当196通过。
8. 固定验证清单`logs/task8/t8-train-stage0-20261027/r2-fixed-verification.json`交父派Terra：真实GPU13项、CLI help、PCD后端回归（TASK84_DEVICE=cpu避免覆盖旧integration产物）；失败停下交Sol推理，不自行修复或加预算。独立Sol验收另人，生产52冻结文件sha核查结果见snapshot。
9. 全门后由父安排B0/B3有界完整评估smoke；不擅自缩评估集。总额不足则保存incomplete并如实交接，不追加预算；本实施者未运行smoke。单run≤48h、四卡显存门仍由A成本及smoke实测决定，随后停交Claude，禁止自启3M。

依据：[SRC-1145](../../../../SOURCES.md#src-1145)、[SRC-1146](../../../../SOURCES.md#src-1146)、[SRC-1147](../../../../SOURCES.md#src-1147)、[SRC-1148](../../../../SOURCES.md#src-1148)；条目草稿交父登记。代码、原命令/退出码、失败定位与固定执行清单见本节点RESULTS和独立日志。

## r1历史快照

状态：**blocked（2026-10-27已授权阶段0部分实施；父因地图池依赖失败要求停止，未smoke/长训）**。协议见[TASK](TASK.md)，当前快照见[RESULTS](RESULTS.md)。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档。定稿后若执行需拆分（如阶段0实现、阶段1运行、阶段2运行），子目录继承`task8.9.3.N`，先建三文档并登记顺序、依赖、负责人、模型/强度、输入输出与验收关系；编号稳定不复用。

## 定稿流程

1. 收到8.9.1成本模型与8.9.2用户池决定后，Claude修订TASK：填入池、评估集、成本与GPU分配，确认或调整阶段1种子数与长度（不得为赶工期缩短步数；不足时报告用户）。
2. 独立Sol high审查协议（假设—分组—判定—停止规则是否对应，有无泄漏与混杂）。
3. 提交用户批准；获批的同时明确训练授权范围（组、种子、步数、GPU、墙钟预算）。

## 执行（获批后）

阶段0实现与测试→有界smoke（吞吐、显存、诊断字段齐全）→阶段1长训（每run独立目录、账本、看门狗、STOP文件）→阶段1判定→按TASK分期规则请用户决定阶段2。长训进程写清容器、PID、日志、监控与停止/恢复方式；Claude后台监督。

## 不变量

不改奖励/动作/观测/终止/网络；B0与v5逐项一致；不使用测试集或迁移评估调参；不恢复task7冻结任务。


## 阶段0当前状态与恢复工作顺序

负责人Codex，实际派发gpt-6.1-sol/high；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，原因是SAC逐元素等价与环境恢复跨模块核对。已应用TDD及verification-before-completion技能，未派子Agent。

1. 已读取v5静态/运行配置及实际SAC实现；先写5项测试，RED均因新模块缺失失败。
2. 实现部分task8_lower SAC/回放元数据/诊断/评估草稿，再跑同5项真实GPU SAC测试，4通过1失败；原始命令与退出码见RESULTS。
3. 依父停止指令保留当前快照；不修失败、不增加测试、不smoke、不长训。
4. 待用户解决地图导出规则、父重新指派后，从阅读本RESULTS与日志开始，核实当前代码/账本/正式池；不能把本次部分测试当验收通过。
5. 尚需：修复并验证终点学习率断言/约定；核对语义manifest及固定种子；训练主循环与CLI、1000转移诊断接入、STOP/信号/非有限与Q看门狗保存、完整task8环境/replay/SAC/RNG/pending批次检查点与逐元素恢复测试。PcdEpisodeEnv生产恢复拒绝护栏保持不改，禁止fresh reset伪装恢复。
6. 以上实现与三条独立验收后，父才可另通知有界B0/B3 smoke；仍共用本次3600s测试+smoke账本，不能另起账本重置额度。smoke之后停交Claude复核，不能自行3M长训。

SOURCES1140–1143草稿在[实施者日志](../../../../agent_logs/task8/task8.9/task8.9.3/20261027-sol-training.md)，共享SOURCES由父登记；1144–1159保留未用。


## 有界smoke准备（尚未执行）

C修复后实现独立PASS；父本轮要求只准备。已建独立lower_smoke_B0_r2.json/lower_smoke_B3_r2.json，仅checkpoint_interval=1000，其余正式参数及3M/v5日程不变。每组先512（实际SAC更新并保存）→同配置/hash从primary-final恢复到1000触发1000诊断/完整196评估；在评估前覆盖真实恢复，禁止fresh reset。固定8job总reservation2970s，C当前余额3450.975768s，预留480.975768s收尾（≥140s）；没有执行任何job、未花新增测试/smoke预算。

完整计划/argv/每阶段deadline/监控/STOP/不完整边界：[计划](../../../../../logs/task8/t8-train-stage0-20261027/r2-smoke-plan.md)、[固定命令](../../../../../logs/task8/t8-train-stage0-20261027/r2-smoke-plan.json)。必须A完整profile与独立验收、B全10300/200与独立验收及父释放后才能派Terra执行；预算不足保留incomplete，不重跑196、不缩环境/回放/评估、不长训。显存/评估成本均仅条件推导，不能称就绪。依据草稿[SRC-1151](../../../../SOURCES.md#src-1151)、[SRC-1152](../../../../SOURCES.md#src-1152)已交父，实际Sol high，推荐GPT6.1sol/high、Sonnet5.5/high（跨恢复和预算约束）；固定执行Terra、Sol查原件。


## r3停止覆盖（blocked，真实smoke首失败）

优化O1–O4和正式池独立PASS后，按[SRC-1190](../../../../SOURCES.md#src-1190)释放原8job smoke。preflight通过，但B0-primary初次256环境reset采样触及235秒deadline，SamplingIncomplete/rc1；CLI243.166660481秒，0动作/0转移，已保存中断状态。按固定首失败即停，后六job（preserve/resume、B3和postflight）未执行；不重试、不增加额度、不3M。实际Terra/low，独立Sol/high后审，推荐GPT6.1sol/Sonnet5.5 high核验采样与恢复路径，固定执行Terra low。[SRC-1200](../../../../SOURCES.md#src-1200)、[独立SRC-1198](../../../../SOURCES.md#src-1198)。

C账本395.0120486840606/3600秒、余3204.9879513159394、active空。meta steps/action_calls/env_actions均0，resume_safe只是保存元数据，未验证正式CLI恢复，不构成恢复授权。无有效训练吞吐/完整196耗时/torch峰值；设备1Hz采样峰值11306MiB不能当正式训练峰值。执行表总stopped，局部running陈旧标签与exit_code1并存，现场以账本/进程核查为准。证据及原件详[SRC-1200](../../../../SOURCES.md#src-1200)。下一步交Claude决定有界初始采样诊断/预算方案，保持原协议与失败记录，未经新派发不继续。
