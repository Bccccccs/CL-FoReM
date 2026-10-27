# task8.9.3 阶段0训练实现

负责人Codex；平台派发gpt-6.1-sol/high；双Agent推荐GPT6.1sol/high、Sonnet5.5/high，理由为SAC等价性与精确恢复跨模块核验。

2026-10-27开始；状态active。用户授权依据SRC-1160；父已负责PROGRESS登记。独占task8_lower、task8_lower_train.py、新task8训练配置、本节点三文档与此日志。不改task7源码/配置/产物、task8生产几何/接口。只先实现与含SAC更新的必要测试；父通知前不smoke，不3M长训，不改科学语义，不提交推送合并。

已读根AGENTS、ENV、doc README/PROGRESS、task8及task8.9父三文档、本节点三文档、SOURCES0983/1000/1100/1101/1102/1160、task8.8 RESULTS。仓库main且大量既有未提交修改，保留。使用TDD与verification-before-completion技能约束：先观测缺失行为失败，再实现，必要验证后才报告。using-superpowers对受派子Agent显式不适用；不再派Agent。

关键核查：v5配置与运行config一致（父交叉核验），total_updates4999743；LowerSAC alpha初值1，首次更新后capped；旧训练每条转移插入前对旧replay len>256更新。PcdEpisodeEnv.__setstate__拒绝pickle，因此task8_lower需显式版本验证与完整状态重建，不改生产护栏。

## 当前停止与交接（2026-10-27）

父消息：8.9.2先导6图非墙内部全占据门失败；按prompt停止，不改导出规则、不全量，要求我停在当前可审阅快照。我收到时首次实现验证命令228e1208fd已经运行，允许正常退出后记账；随后没有再启动测试、smoke或训练，没有为收尾补做功能。

实际新增8文件：src/task8_lower/__init__.py、sac.py、replay.py、diagnostics.py、evaluation.py、tests/test_stage0.py与config/task8/lower_train_B0.json、lower_train_B3.json。另更新本节点三文档，创建本日志及logs/task8/t8-train-stage0-20261027/{run_budget.py,budget.json,implementation-snapshot.json}。snapshot保存8实现文件SHA256；原task7不写，不提交推送合并。

账本完整argv记录在budget.json。RED f98ea56f2e rc1/1.916767674s，5项因模块缺失失败。首次实现验证228e1208fd rc1/5.872172734s（pytest4.87s），4passed1failed。累计7.788940408267081s，余额3592.211059591733s/3600s，active={}。全部在forem-dev经sg docker，物理GPU1/TASK89_DEVICE=cuda。父前置核卡空；测试真实网络更新使用cuda输入，未单测optimizer设备/峰值显存。

4通过：B0单次更新loss及policy/critic/target state tensors与v5 torch.equal、初始alpha/LR；NaN奖励在critic写入前停止且参数不变；合成Q看门狗规则；100+96评估计划数量/唯一性/test排除。1失败：B3测试最后精确LR==1e-6失败，实际9.999999999999972e-7；此前中点LR、两次更新、alpha>1自由变化、SAC roundtrip assertions通过，但整项不通过。未修未重跑。

未实施：training.py与CLI、训练诊断/UTD/STOP/检查点实际接入、PcdEpisodeEnv显式全状态保存恢复。评估/回放诊断草稿未真实环境验证，100+96episode没有运行。配置尚有错误transfer_pool占位路径；父确认应使用results/task8/t8-exec-20261026/semantic-pool/index.json，停止时未改。cube正式池先导未过而未生成，固定迁移种子草稿待与pool对接。不能执行正式配置，不能声称阶段0/独立验收通过、不能给训练工期。收到停止后只做文档/只读hash与进程核查：无本任务pytest/train存活。

恢复风险：task8_sim/env.py PcdEpisodeEnv.__setstate__/load_state_dict拒绝pickle；不能直接复用task7 save env。父已授权只在task8_lower显式包装/重建完整状态，保持生产护栏。后续须真实Core/route/Grid/scene/streams/sampler planner/replay/SAC/optimizer/global RNG/pending批次等恢复，并对连续下一转移/更新逐元素核对；方案未实现，不能用fresh reset代替。

目标与授权：SRC1160阶段0与后续B0/B3各2seed×3M仍为用户已授权范围；本轮停止是地图前置依赖失败。阶段2/改奖励/终止/网络/损失/几何/性能优化未实施。下一步由用户解决地图导出规则、父重新指派后，再核本RESULTS/snapshot/账本，补缺项并独立验收，之后才由父通知同账本smoke；smoke后仍交Claude复核，不自动3M长训。

## SOURCES条目草稿（父统一登记；1144–1159未用）

<a id="draft-src-1140"></a>
### SRC-1140 — task8.9.3阶段0部分实现与B0日程保留

- 支撑主张：新task8_lower与B0/B3配置只实现部分SAC/诊断/评估草稿；B0 alpha初值1、首次更新后capped，指数日程分母4999743，3M转移未改该日程。不是训练就绪结论。
- 类型：项目源码直接核查＋授权工程选择，非外部论文、非训练效果实测。
- 作者/版本：Codex，2026-10-27，未提交工作区，run-id t8-train-stage0-20261027；SHA256清单logs/task8/t8-train-stage0-20261027/implementation-snapshot.json。
- 精确位置：src/task8_lower/sac.py LowerSAC.__init__/set_transfer/update_from_batch；config/task8/lower_train_B0.json total_updates/total_transfers/alpha_rule/lr_schedule；只读原src/task7_lower/sac.py LowerSAC.__init__及results/task7/t7.18-v5-20261022/formal-v5-sync/config.json/runtime.json。
- 核查日期/人：2026-10-27，Codex（gpt-6.1-sol/high显式派发）。
- 原始结论：B0继承原初值1与exp-updates更新数学，配置3M预算仍使用4999743指数分母；B3每10转移判定与3M转移线性LR；尚无训练主循环/CLI/完整恢复。
- 本项目采用：TASK/PROCEDURE/RESULTS记录当前可审阅快照，待重新指派补完；局限：运行配置尚有语义池错误占位路径、正式cube池前置失败、迁移种子尚待对接，不能运行正式训练。

<a id="draft-src-1141"></a>
### SRC-1141 — task8.9.3阶段0真实SAC更新测试（4通过1失败）

- 支撑主张：当前局部测试4通过1失败，B0一次真实网络更新与v5逐元素一致；不能宣称全测试或阶段0通过。
- 类型：项目有界GPU测试实测，非长训/真实环境评估。
- 作者/版本：Codex，2026-10-27，tests/test_stage0.py与implementation-snapshot.json对应工作区版本，run-id t8-train-stage0-20261027。
- 精确位置：logs/task8/t8-train-stage0-20261027/f98ea56f2e.log（RED5failed）；228e1208fd.log（4passed1failed）；src/task8_lower/tests/test_stage0.py test_b0_matches_v5_actual_update_and_initial_alpha/test_nonfinite_sac_update_stops_before_optimizer_mutates/test_watchdog_500k_baseline_and_nonfinite/test_protocol_has_exact_validation_and_transfer_pairs/test_b3_transition_schedule_alpha_unbounded_and_roundtrip。
- 核查日期/人：2026-10-27，Codex（gpt-6.1-sol/high）。
- 原始结论：B0同初始化/随机流一次更新的loss/三网络参数torch.equal，alpha初始1和LR相等；NaN奖励更新前停止；合成watchdog与评估plan通过。B3末条LR精确等于1e-6失败，实际9.999999999999972e-7，整项失败保留。测试容器forem-dev、CUDA_VISIBLE_DEVICES1、TASK89_DEVICEcuda，真实网络SAC更新。
- 本项目采用：记录局部等价证据与公开失败；限制：仅一次B0更新/两次B3更新和合成批次，未完整回归、未真实环境196episode、未检查点恢复，不能证明长程一致、成功率或根因。

<a id="draft-src-1142"></a>
### SRC-1142 — task8.9.3阶段0测试预算与无后续运行

- 支撑主张：本轮两条测试累计7.788940408s/3600s，active空；无smoke或长训。
- 类型：项目执行账本直接核查；预算3600s为父派发工程约束，非性能预测。
- 作者/版本：Codex，2026-10-27，logs/task8/t8-train-stage0-20261027/budget.json及同目录run_budget.py。
- 精确位置：budget.json commands IDs f98ea56f2e、228e1208fd的argv/start/end/elapsed_s/exit_code/timeout；used_s7.788940408267081、active{}；本日志“当前停止与交接”。
- 核查日期/人：2026-10-27，Codex（gpt-6.1-sol/high）。
- 原始结论：RED1.916767674s与首次验证5.872172734s均rc1/未timeout，余额3592.211059592s。父停止指令收到时第二命令已提交，正常退出后未新启测试；只读ps未见本任务pytest/train。无训练主循环/CLI，因此未smoke/长训。
- 本项目采用：阶段0后续如重启应延续同账本而不重置；限制：账本为测试外层墙钟，不是开发工时/累计GPU核时，也不证明未来smoke或3M预算可行。

<a id="draft-src-1143"></a>
### SRC-1143 — task8恢复护栏与阶段0未完成风险

- 支撑主张：task8不能直接恢复旧pickle env，当前阶段0尚无完整训练恢复；真实评估与训练工期未验证。
- 类型：项目源码直接核查与未实施状态；恢复方案为待实施工程选择。
- 作者/版本：Codex，2026-10-27，src/task8_sim/env.py PcdEpisodeEnv.__setstate__/load_state_dict；本节点RESULTS与本日志。
- 精确位置：上述两个方法显式raise ValueError；src/task8_lower仅sac/replay/diagnostics/evaluation/__init__/tests，无training.py；scripts/task8_lower_train.py未创建。
- 核查日期/人：2026-10-27，Codex（gpt-6.1-sol/high）。
- 原始结论：现有生产恢复拒绝护栏保持；父允许仅task8_lower显式保存/重建完整Core/scene/route/Grid/随机流/采样缓存/回放/SAC/pending，实际尚未实现。仅构想，不能称通过。
- 本项目采用：下次执行须先解决地图前置、补全训练/精确恢复并独立验收，后再同账本smoke；限制：没有恢复运行证据、吞吐/显存/196episode评估成本或≤48h工期证据，不作启动就绪判断。

## r2续接（active，2026-10-27）

父重新派发阶段0 C；实际gpt-6.1-sol/high，推荐GPT6.1sol/high、Sonnet5.5/high。已复读根及forem AGENTS、ENV/README/PROGRESS、8.9父与本节点三文档、8.9全部历史日志、SRC1140–1144/1160–1162及现有实现。原7.788940408267081s账本沿用；首次GPU现场compute空，forem-dev运行。只改task8_lower/本训练CLI/config及自己节点，不改task7/task8_sim生产。应用systematic-debugging定位浮点断言、TDD/verification-before-completion完成必要验证；不另派Agent。固定执行清单交父派Terra，推理性测试调试由本实施者做。尚不smoke、不3M。

浮点失败根因：1e-4+(1e-6-1e-4)*1的binary64减法消去导致终点误差约2.75e-21；拟仅改测试采用rel=0/abs=4*ulp(1e-4)（两次算术的保守舍入界），不改日程。正式池改cube-pool-v2/manifest.json，评估逐图种子表由B发布，旧同种子草稿不冻结。

## r2 B0逐项配置核对（静态）

原件：`results/task7/t7.18-v5-20261022/formal-v5-sync/config.json`；与`config/task7/lower_train.json`完全相同。下表为直接读取，未将配置等同长训效果。[SRC-1148待父登记](../../../../SOURCES.md#src-1148)

|v5字段|v5实际值|B0值|判定|
|---|---|---|---|
|schema|`1`|`"task8-lower-train-v1"`|task8配置版本|
|total_transfers|`5000000`|`3000000`|用户授权3M|
|total_updates|`4999743`|`4999743`|逐项相等|
|seed|`4718`|`4718`|逐项相等|
|validation_seed|`14718`|`14718`|逐项相等|
|synchronous|`true`|`true`|逐项相等|
|environments|`256`|`256`|逐项相等|
|pool|`"/root/mm_husky_ws/results/task7/maps/a/20261021T021400Z"`|`"/root/mm_husky_ws/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json"`|用户授权task8立方体PCD|
|batch_size|`256`|`256`|逐项相等|
|replay_capacity|`100000`|`100000`|逐项相等|
|warmup_transfers|`1000`|`1000`|逐项相等|
|checkpoint_interval|`250000`|`250000`|逐项相等|
|log_interval|`1000`|`1000`|逐项相等|
|dls_cuda_graph|`true`|`true`|逐项相等|
|robot_geometry_version|`"selfcoll-multisphere-v4-spherepairs-20261021"`|`"selfcoll-multisphere-v4-spherepairs-20261021"`|逐项相等|
|robot_geometry_sha256|`"6c41120ad85bdea61a24b1089e825febf4f6b62eb93da0474e51f386167b084a"`|`"6c41120ad85bdea61a24b1089e825febf4f6b62eb93da0474e51f386167b084a"`|逐项相等|
|robot_geometry_config|`"config/task7/robot_geometry.json"`|`"config/task7/robot_geometry.json"`|逐项相等|
|environment_geometry_version|`"v1-unchanged"`|`"pcd-voxel-v3"`|用户授权v3|
|failure_mode|`"cbl_continue"`|`"cbl_continue"`|逐项相等|
|async_time_penalty|`0.0`|`0.0`|逐项相等|
|episode_end_bootstrap|`true`|`true`|逐项相等|

新增控制字段：update_every_transfers=1、alpha_rule=capped、lr_schedule=exp_updates、alpha_lr_start/end=1e-6、lr_start=1e-4/lr_end=1e-6，均对应v5源码实际行为；profile=sync_v5补齐默认ik_avoid_collision=true。group、device/threads、train_split、transfer_pool/evaluation_seeds、validation_environments/sensor_policy属任务8接入与固定评估协议。正式评估使用B发布的逐图种子表，validation_seed为兼容配置字段，不能声称与v5评估随机流相同。网络/γ=.99/τ=.001/目标熵−3/梯度裁剪10/target interval1，原类直接继承；单次与下一更新等价由单测验证。

## r2稳定交付点与下一步（2026-10-27T11:40+08:00）

当前源码冻结待独立审查，13 passed（918e2b4bb1，20.45s内部/21.494841542s外层，rc0），原账本累计103.2527270661667/3600s、active空、余3496.7472729338333s。没有smoke/长训。恢复测试B0/B3各执行实际PCD一步与batch2更新，比较全部SAC/Adam/scheduler/alpha/replay与下一transition，torch.equal；生产环境拒绝pickle护栏保持。不以1环境/replay8/旧prepare夹具的单测证明正式256环境/100k回放/196评估通过。

开发失败原件：b4428694ed 缺training模块RED；cdc44a99aa 夹具split非train，改测试读本fixture split；c5eb771b8b cuda与cuda:0设备元数据比较失败，重建canonical设备；4967924086 7pass；9f8e50f551 梯度RED发现先污染critic才在policy Q拦截，补写前grad有限护栏；8adad713a6 9pass；b291bd3dba 11pass1fail为double均值末位精确断言，容差修测试；dba021b06b 非有限actor动作RED；918e2b4bb1 最终13pass。原日程公式、SAC数学与网络未改；安全护栏只拒绝/保存，不替换数据。沿v5保留detached GPU loss直至诊断/保存，不逐转移转CPU scalar。

显式checkpoint：environment=dict(attributes,core attrs)，不pickle PcdEpisodeEnv对象，不调用reset；命名包装保留Core state/route/Grid/队列/观测、scene引用关系、streams/sampler/planner、kin/robot、episode计数，checkpoint另含pending cursor/transition、replay ring/RNG/meta、SAC三网络/三optimizer/两scheduler/alpha/global RNG/源合同/池hash。仅省略DLS graph/fixed tensor纯缓存，恢复canonical device并重建；半次optimizer出错标unsafe_update，仅取证，拒绝续跑。SIGINT/SIGTERM标志在安全边界保存，STOP/墙钟/采样中断同理，保持budget-safe interaction ledger门。

固定验证清单：`forem/logs/task8/t8-train-stage0-20261027/r2-fixed-verification.json`，交父派gpt-6.1-terra low执行，未由我再执行。三项：GPU stage0全13项（130s reservation）、CLI --help（15s）、PCD后端现有回归（180s，TASK84_DEVICE=cpu避免写旧integration证据）；每条同原C run_budget.py且failure停止，不重置费用。源码SHA256与52冻结原件核查：`r2-implementation-snapshot.json`，52无漂移。独立Sol high须≠实施者，原件复核与必要复跑沿C账本。

完整196评估成本未实测；只从A batch16约14.554转移/s推导：若每episode100有效转移则约1347s/196评估、两组2694s，未计reset/训练/checkpoint，实际episode长度未知，不能保证余额足够。父已要求保持完整196、不加子集开关；全门后父调度有界尝试，不足保留incomplete报告，不追加3600s。

目标授权与负责人：C阶段0继续由本Sol负责到实现交付，源码稳定交父/不同Sol验收；未解决项为正式池发布核验、实际196评估/吞吐/峰值显存/CLI smoke，下一步父调度，不自动长训。推荐仍GPT6.1sol/high、Sonnet5.5/high；无新Agent、无提交推送合并、无生产语义/性能优化修改。

## r2 SOURCES草稿（父统一登记1145–1148，其余1149–1159未用）

### SRC-1145 — B3末LR断言的binary64容差与安全护栏

- 主张：B3原线性日程未改，末值9.999999999999972e-7与目标1e-6差约2.75e-21；测试以rel0/abs4×ulp(1e-4)判断。真实NaN梯度/动作在写入critic/环境前拒绝。
- 类型：项目原测试实测＋浮点误差推导＋授权工程护栏，非外部文献或SAC效果。
- 作者/年份版本：Codex gpt-6.1-sol/high，2026-10-27，run t8-train-stage0-20261027；源码摘要r2-implementation-snapshot.json。
- 位置/证据：src/task8_lower/tests/test_stage0.py::test_b3_transition_schedule_alpha_unbounded_and_roundtrip/test_nonfinite_gradient_stops_before_critic_step/test_nonfinite_policy_action_rejected_before_environment；sac.py::LowerSAC.set_transfer/_clip/select_action；logs/task8/t8-train-stage0-20261027/{228e1208fd,9f8e50f551,dba021b06b,918e2b4bb1}.log。
- 推导：输入start=1e-4,end=1e-6,progress=1（无量纲）；式start+(end-start)*progress，单位学习率；binary64两次加减带来消去，保守界4×ulp(start)=5.421010862427522e-20，大于实测残差，远小于学习率量级；不改变日程边界或科学条件。
- 核查日期/人：2026-10-27 Codex实施Sol；独立验收待另人Sol。
- 原结论/采用限制：最终13项GPU单测通过；仅边界/保护测试，不能证明训练性能或根因。非有限更新中途可能已写入前一optimizer，forensic checkpoint明确unsafe_update，不声称回滚或可续跑。

### SRC-1146 — task8显式全状态恢复与下一更新/转移逐元素验证

- 主张：PcdEpisodeEnv生产拒绝pickle/load_state_dict保持；task8_lower显式包装属性/Core字段，恢复不reset；B0/B3恢复后下一pending消费、SAC更新和环境transition逐元素一致。
- 类型：项目工程实现＋有界真实GPU单测；非长训/正式PCD池验收。
- 作者/年份版本：Codex gpt-6.1-sol/high，2026-10-27，r2-implementation-snapshot.json；run t8-train-stage0-20261027。
- 位置/证据：src/task8_lower/training.py::environment_state/restore_environment/save_checkpoint/load_checkpoint/consume_transition；tests/test_recovery.py::test_explicit_environment_resume_next_transition_and_update[B0/B3]；918e2b4bb1.log，代码格式task8-lower-full-v1/pcd-explicit-state-v1。
- 核查日期/人：2026-10-27 Codex实施Sol；独立终审待另人Sol。
- 原始结论：两组各1环境、batch2/replay8、旧prepare PCD夹具，torch.equal覆盖全SAC state（网络、Adam、scheduler、α等）、replay/rng/pending及下一transition所有张量；初始设dls_cuda_graph=true，不保证本特定样本一定形成非空graph cache。此前cuda vs cuda:0元数据失败已按实际tensor设备canonical修复；失败日志c5eb771b8b保留。
- 采用/限制：仅省略纯DLS/fixed缓存并重建；配置/源合同/池hash不兼容与unsafe_update拒绝恢复。未覆盖跨硬件/版本的位级一致，也不证明正式256环境/100k回放/长训恢复吞吐；旧prepare夹具仅单测不参与正式评估。

### SRC-1147 — r2阶段0十三测试、预算、停止控制与未执行边界

- 主张：阶段0最终13pass，STOP/SIGTERM保存、诊断RNG/字段测试通过；测试沿原C账本103.2527270661667s，未smoke或完整196评估，不作就绪结论。
- 类型：项目有界GPU单测与执行账本；非训练成功率/性能实测。
- 作者/年份版本：Codex gpt-6.1-sol/high，2026-10-27，run t8-train-stage0-20261027。
- 精确证据：logs/task8/t8-train-stage0-20261027/budget.json commands b4428694ed/cdc44a99aa/c5eb771b8b/4967924086/9f8e50f551/8adad713a6/b291bd3dba/dba021b06b/918e2b4bb1；最终13 passed in20.45s，外21.494841542094946s、rc0/timeoutfalse；r2-fixed-verification.json与本节点RESULTS。
- 核查日期/人：2026-10-27 Codex实施Sol，已直接读最终原日志/账本；固定验证及不同Sol独立审查待执行。
- 原结论/采用：13项包含B0与v5一次更新、两组精确恢复、非有限奖励/梯度/动作、Q规则、评估计划100+96、STOP/SIGTERM及诊断RNG/元数据；所有历史失败费用保留，未reset账本。3600s为既有授权上限，非新增性能预测。
- 限制：初始STOP/SIGTERM控制单测在reset前中断，没有训练主循环环境交互；真实CLI/196episode/吞吐/峰值显存仍待全门后smoke，同账本预算不足保留incomplete，不缩评估。

### SRC-1148 — B0与v5逐项配置核对、正式池/逐图评估协议及冻结保真

- 主张：除用户授权task8接入差异，v5原配置字段逐项相等；B0保留实际α初值1与4999743指数分母；正式池改cube-pool-v2、逐图种子表消费100验证+96迁移且test排除。52冻结原件无变化。
- 类型：项目原始配置/源码直接核查＋授权工程接入，非训练表现或正式池已通过证明。
- 作者/年份版本：Codex实施Sol，2026-10-27，config/task8/lower_train_B0.json/lower_train_B3.json；snapshot r2-implementation-snapshot.json。
- 精确证据：results/task7/t7.18-v5-20261022/formal-v5-sync/{config,runtime}.json、config/task7/lower_train.json、src/task7_lower/{sac,replay,training}.py只读；本日志“r2 B0逐项配置核对”逐字段表；src/task8_lower/evaluation.py::evaluation_plan/evaluate；test_protocol_has_exact_validation_and_transfer_pairs；父preservation-before.json与本snapshot frozen_checked52/frozen_changed[]。
- 核查日期/人：2026-10-27 Codex实施Sol；正式种子表/全池仍待B发布，终审待另人。
- 原结论：schema、total_transfers(用户3M)、pool与environment_geometry_version是明确接入差异；原配置其余字段相等，新训练开关对应v5实际行为。B按原固定hash规则生成每图episode_seed，C按每job RandomStreams(seed,1)/stream0，不声称与v5评估随机流相同；验证100、迁移24×4且不选模。
- 采用/限制：路径预定results/task8/t8-pool-20261027/cube-pool-v2/{manifest,evaluation-seeds}.json及results/task8/t8-exec-20261026/semantic-pool/index.json；发布前不能执行正式配置。快照仅覆盖52源/config，不涵盖所有历史产物；只作阶段0条件核对，不宣称196实评、可长训或科学分布与task7完全相同。

## C1/C2独立审查修复（2026-10-27）

已应用receiving-code-review技能，先读独立FAIL报告/真实index/B冻结finalize源码，确认两项有效，不改B冻结hash。C1：B split是role，源index split=smoke；新消费严格role/source_split，另绑定relative-to-forem semantic_manifest路径、字节hash与实际内容。C2：sampler和candidate以前不同根种子/不同batch位置；新evaluation_environment将同一per-job EnvironmentStreams交env.reset factory与choose_candidate，各purpose maps/initial/other保持独立。

新test_evaluation_contract.py读取真实semantic index、pool_s3 run_id，按冻结B finalize schema与hash公式生成seed记录，未跑B finalize/全量；包含7种反例和跨batch位置随机流轻量测试。RED0d8f3e7cdc rc1/2.066950819s，2fail7pass；GREEN6544bdfdf6 rc0/20.893972854s，22pass in19.86s。C总149.024231501855s/3600s，余3450.975768498145s、active空。未smoke/196episode/长训。原13pass并不能覆盖这两个实际接口错误，保留独立FAIL与旧日志。

r2-implementation-snapshot.json更新；原13pass源码摘要保留r2-implementation-snapshot-before-review.json，52冻结文件无漂移。三文档已补当前覆盖，固定验证json命令仍适用（现22项）。交父/independent_r2再验，原预算不重置。

### SRC-1149 — 真实语义池与B种子表角色/源split接口修复

- 主张：B正式seed v1记录split=semantic_transfer代表评估角色，真实semantic-pool/index.json全部source split=smoke；C旧等同检查使完整评估前置失败，现明确区分且加强源身份绑定。
- 类型：独立代码审查问题＋项目真实manifest/冻结导出源码核查＋回归实测，非196episode评估。
- 作者/年份版本：独立Sol /root/independent_r2发现，实施Codex gpt-6.1-sol/high修复，2026-10-27，C1-C2-review-fix；旧/新源码摘要分别r2-implementation-snapshot-before-review.json与r2-implementation-snapshot.json。
- 位置：src/task8_lower/evaluation.py::evaluation_plan；scripts/task8_build_pool.py::finalize种子构造只读；results/task8/t8-exec-20261026/semantic-pool/index.json；tests/test_evaluation_contract.py::producer_fixture/test_real_semantic_source_split_and_producer_role_contract/test_real_evaluation_identity_mismatch_rejected；results/task8/t8-phase2-20261027/r2-independent-c-stage0.md/json；logs/task8/t8-train-stage0-20261027/{0d8f3e7cdc,6544bdfdf6}.log。
- 核查日期/人：2026-10-27 Codex实施Sol，独立Sol已确认问题与修复方向，改后待独立再验。
- 原结论：RED2fail7pass暴露真实角色错误；修后全22pass。validation role/source均validation；transfer role=semantic_transfer/source=smoke；记录map_id/index/stream0、源manifest相对forem根路径/sha256/实际内容严格校验，job与输出含role/source_split；无B生产修改/冻结hash漂移。
- 采用/限制：测试读取真实24语义map，cube100为合成身份夹具，seed按B实际schema/已核sha256(run_id:map_id:j)前8hex生成；正式全池seed文件尚待发布，不把合同回归当完整196实评或全池通过。

### SRC-1150 — 每episode固定随机流覆盖采样与候选选择

- 主张：原评估sampler使用job seed，但候选choose_candidate使用validation_seed按batch行号，违反完整episode固定种子；现同job的maps/initial/other来自同一RandomStreams(seed,1).for_env0，候选不受batch位置影响。
- 类型：项目源码因果核查＋授权合同修复＋轻量随机流回归；非算法/分布新增、非成功率实测。
- 作者/版本：独立Sol /root/independent_r2发现，实施Codex gpt-6.1-sol/high，2026-10-27；C1-C2-review-fix摘要同SRC1149。
- 精确位置：task7_sim/episode.py::RandomStreams（purpose0/1/2）、task7_lower/training.py::choose_candidate只读；task8_lower/evaluation.py::EvaluationStreams/evaluation_environment/evaluate；test_evaluation_contract.py::test_fixed_episode_streams_same_at_different_batch_positions；6544bdfdf6.log。
- 核查日期/人：2026-10-27 Codex实施Sol；独立Sol已核原问题属实，改后再验待执行。
- 原结论：实际PCD评估环境构造（不reset/不step）把同一job放单行row0与双行row1；两者.initial不同消耗后，other32整数均与独立seed参考逐元素一致，maps流也相等。env.reset factory直接消费env.streams传入对象，与choose_candidate为同一EnvironmentStreams的独立purpose子流。
- 采用/限制：固定全episode随机根种子，未改task7候选分布或生产环境代码；轻量流绑定测试不声称不同batch数的实际浮点几何/网络结果必逐位相同，也未完成196episode或训练效果验证。C累计149.024231501855s含旧费用，smoke继续受同3600s约束。

## 完整smoke固定清单准备（尚未执行）

父本轮只要求准备；已核当前training/CLI及C独立PASS报告，A条件成本/256窗口/回放容量，B仍全量导出。未执行任何smoke job，C账本保持149.02423150185496/3600s、余3450.975768498145s。新增`config/task8/lower_smoke_{B0,B3}_r2.json`，只改checkpoint_interval为1000；正式配置/seed4718未改。

固定清单与人读报告：`logs/task8/t8-train-stage0-20261027/r2-smoke-plan.json/.md`。每组primary到512，正式256环境/100k回放/256batch，B0已有255次/B3已有26次SAC更新；保存primary-final后，同config字节hash真实CLI恢复至1000（B0共743/B3共75次update），先覆盖恢复再在1000触发诊断/checkpoint/完整100验证＋96迁移评估。不fresh reset、不缩规模、不优化。每组CLI outer275+1175=1450s，primary maxwall235/timeout255 kill10，resume maxwall1130/timeout1155 kill10；preflight20+preserve15×2+postflight20，加上两组总reservation2970s，最坏预留480.975768s收尾，超过父要求140s。

所有命令argv/Python监控wrapper/预检/归档/后检已写JSON，仅AST静态解析8命令体，无运行；source C代码未改。预检核source/config hash、正式10300+≥200发布、完整196 plan、GPU1空与预算；每次CLI wrapper再核GPU1 compute空。监控只启动/清理本job的nvidia-smi，stdout由原C预算runner留UUID日志，GPUCSV/device memory与summary Torch allocated peak分开记录。primary config/output config SHA需完全相同；保存final/meta/actor/summary/runtime为primary-*以免resume覆盖历史；safe_to_resume与原load_checkpoint合同继续生效。

主run若235s未完成512则停报告，不重试；resume遇1130s评估deadline，源evaluate写validation-0001000.incomplete.json、train写interrupted.pt（validation_pending1000/完整trainingenv/pending）。不恢复重跑完整196耗超；父可在已有reservation下派下一独立组一次，任何非预期失败返回父/Sol。评估未保存逐episode中间执行状态，incomplete只记录完成的整组，不能声称部分评估可无成本续接。STOP不自动清除，unmatched intent/unsafe_update不伪造恢复。

条件成本已反馈父：A B0 3M约57.725h（缺reset/评估等，非正式可行性证明）超过48h，只阻止长训；父明确本轮另授权有界smoke完整协议尝试。每episode若100转移，则按cube16约14.554/s＋semantic256窗口10.551/s混合条件推导，196约1597s（批次不同/未计sampling/reset/训练），不能承诺1130s完成。没有调整实际episode长度或评估集，只作风险说明。

显存已知项：formal replay100k基础9,891,600,000B＋diagnostic inserted_at/failed900,000B；A1024回放256窗口峰值4,041,034,240B，按容量替换已知项约13,832,244,256B。额外critic/target/Adam/grad/activation与正式256随机scene/评估额外峰值尚未实测，不把已知分项当完整上界或96GB验收；未发现必超卡容量的证据，仍以有界实际峰值为准。

已核本节点与Claude阶段2原规划：只定“每组2训练种子”，除继承4718外未找到第二训练seed；14718等旧数为评估草稿。父将[4718,4719]两组配对、GPU0/1 B0与2/3 B3作为明确工程choice登记SRC1158，仅生成待审核正式命令，不启动；我未改正式seed。当前下一步父派独立Sol看清单预算/恢复/监控/失败保存，A/B全门后才派Terra，仍不3M。

### SRC-1151 — 有界完整smoke的512→同配置恢复1000顺序与2970s固定预算（未执行）

- 主张：准备两组正式256环境/100k回放的有界smoke，每组先512保存，再同配置/hash恢复1000触发完整196；全部外层reservation2970s，原C余额3450.975768s中保留480.975768s≥140s收尾。只是准备，不是运行结果。
- 类型：父明确授权内工程执行计划＋源码直接核查＋预算/更新次数推导，非项目实测吞吐或效果。
- 作者/年份版本：Codex gpt-6.1-sol/high，2026-10-27，`r2-smoke-plan.json` schema task8-stage0-full-smoke-plan-v1/status PREPARED_NOT_EXECUTED；推荐GPT6.1sol/high、Sonnet5.5/high，固定命令Terra/Sol验收。
- 精确位置：logs/task8/t8-train-stage0-20261027/r2-smoke-plan.json/.md；config/task8/lower_smoke_B0_r2.json SHAe9a250c764450383922e9e6fc8de579e8af798a68b1558de48de7bfe8d800e6c、lower_smoke_B3_r2.json SHA0d5bf3f1877f3be969d6dcd69d8597510d28a9e4268cbf2a809aab49cb888ab0；training.py::train/save_checkpoint/load_checkpoint与sac.py::update_due只读；原budget.json used149.02423150185496/limit3600。
- 核查日期/人：2026-10-27 Codex实施Sol，8个准备命令体仅AST解析未执行；父已读顺序，独立Sol清单审待执行。
- 推导：512=2×256，旧replay>256故B0有效update数512−257=255，B3全局倍10于260..510共26；到1000分别743、75。预算20+2×(275+15+1175)+20=2970s；3600−149.02423150185496−2970=480.97576849814504s。CLI maxwall235/1130、硬timeout255/1155加kill10，外层275/1175留保存/清理余量，为工程上限非完成承诺。
- 采用/限制：smoke仅checkpoint_interval=1000，正式仍250k，log1000/schedule3M/B0分母4999743/seed4718不变；预算runner原账本、GPU1空、A/B/C独立全门后父释放；deadline incomplete不重试196或缩水。还未测真实CLI训练/完整评估/峰值显存；新清单不授权3M。

### SRC-1152 — 完整smoke的条件显存/评估成本与不完整边界

- 主张：现有profile不能保证完整196在smoke deadline内，已知回放/分项内存不构成正式训练峰值验收；源代码能在有界评估deadline保存incomplete及完整训练checkpoint，计划先恢复后评估以优先留恢复证据。
- 类型：项目原profile读取＋明确条件推导＋已审源码行为/工程边界，非正式smoke实测或外部文献结论。
- 作者/年份版本：A实施profile原件（2026-10-27）与Codex C gpt-6.1-sol/high静态核查；C计划版本同SRC1151。
- 精确位置：results/task8/t8-perf-20261027/cube-run-b16.json::transfers_per_s14.55397859883984；cube-run-b256-r2-w1.json::runtime.peak_gpu_allocated_bytes4041034240/replay_capacity1024/capacity100k_replay_tensor_bytes9891600000；semantic-run-b256-r2-w1.json::status incomplete/transfers_per_s10.55099282853315；r2-cost-framework.json::conditional_hours；task8_lower/replay.py inserted_at/failed；evaluation.py::evaluate异常分支、training.py::train/save_checkpoint/load_checkpoint；r2-smoke-plan.md“判据与限制”。
- 核查日期/人：2026-10-27 Codex实施Sol直接读JSON/源码；正式完整smoke尚未执行。
- 推导/条件：回放100k=2×100000×128×128×3 uint8＋2×100000×74×4B向量＋100000×3×4B动作＋2×100000×4B reward/mask=9,891,600,000B；诊断100000×(8+1)B=900,000B。A窗口已知峰值替换1024→100k回放：4,041,034,240+9,891,600,000×(1−1024/100000)+900,000=13,832,244,256B。未计新增SAC critic/target/Adam/grad/activation、正式256随机scene和评估不同峰值，不是完整上界。若每episode100有效转移（仅说明预算风险的假设，不用来改协议），100×100/14.55397859883984+96×100/10.55099282853315≈1597s；两种profile批次不同/旧有限资产，仅条件推导，未计reset/sampling/训练，实际episode转移数未知。
- 原结论/采用：A条件B0 3M约57.725h、B3约47.471h均不含未测项，不能长训放行；父明确当前有界smoke另已授权，不因此实施优化/缩规模。完整评估超1130s会incomplete，训练保存interrupted.pt/validation_pending1000；部分评估不缓存逐episode状态，续恢复会重跑196，故计划不安排此重试。完整通过须实际100+96 complete与1000最终checkpoint/diagnostics/updates，不以postflight exit0代替；budget不足、初始化/保存失败均如实partial。
