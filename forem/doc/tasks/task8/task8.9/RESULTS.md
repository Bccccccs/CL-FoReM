# task8.9 — 结果与交接

**2026-10-27 已作废（closed）**：用户指令“现在的8.9作废吧，要优化好了整体的地图再开始训练”（[SRC-1220](../../../SOURCES.md#src-1220)）。本节点不再执行；以下为作废前的历史状态与记录，原样保留。

状态：**blocked（r2：A严格P2/P5未通过，按遇需决定停下报告；B部分资产保留，C实现门通过，未smoke/3M）**。

## 子结果汇总

|子任务|状态|结果|
|---|---|---|
|8.9.1 批量性能核查|部分：64+24预采样；未测batch吞吐/热点/成本|[RESULTS](task8.9.1/RESULTS.md)|
|8.9.2 地图池划分|blocked：24诊断图导出，6先导全内部门FAIL，全量未启动|[RESULTS](task8.9.2/RESULTS.md)|
|8.9.3 长程对照设计|阶段0部分：4pass1fail；无训练入口/完整恢复，未smoke|[RESULTS](task8.9.3/RESULTS.md)|

## 规划阶段输入证据

- v5退化与值函数发散：[SRC-0983](../../../SOURCES.md#src-0983)、[SRC-1101](../../../SOURCES.md#src-1101)。
- CBL RLlib对照：[SRC-1000](../../../SOURCES.md#src-1000)。
- task8 v3地图后端：[SRC-1100](../../../SOURCES.md#src-1100)。
- 规划工程选择：[SRC-1102](../../../SOURCES.md#src-1102)。

## 2026-10-27 首次执行登记

负责人Codex，父实际模型/强度按派发为gpt-6.1-sol / medium（内部运行标识未独立核验）；三个实施Agent显式指定gpt-6.1-sol / high。模型推荐：Codex GPT6.1sol、Claude Sonnet5.5，协调medium、跨模块实施/独立验收high。

- A `/root/perf`：GPU0、task8.9.1，1800s累计/300s单命令，无optimizer。
- B `/root/pool`：CPU、task8.9.2阶段B，先实测速率再定总预算；阶段A暂缓。
- C `/root/training`：GPU1、task8.9.3阶段0；测试与后续smoke共3600s。
- 三者只写各自节点/代码/日志；共享SOURCES、PROGRESS和父文档由父维护。独立验收尚未执行。
- 初检无旧执行账本/产物，不重跑task8.8。冻结文件初始摘要：`forem/results/task8/t8-phase2-20261027/preservation-before.json`，覆盖task7_lower、task8_sim、config/task7非缓存文件52项；最终仍须复核。
- 完整过程与授权边界：[协调日志](../../../agent_logs/task8/task8.9/20261027-codex-phase2-coordination.md)。

## 当前停止结果与长训启动门

- A累计81.768796781/1800s，64立方体与24语义各1episode采样完成；P1/P6部分，P2/P3未执行、P4/P5未成立。256环境吞吐/热点、每百万转移成本均没有结果。[SRC-1103](../../../SOURCES.md#src-1103)、[SRC-1114](../../../SOURCES.md#src-1114)、[SRC-1115](../../../SOURCES.md#src-1115)。
- B测速24图/66,706,458B/2,546,383点，1.825751s、13.1453图/s；六个split×difficulty先导sampled/exact内部缺格7337/7303，墙缺格0、33432深墙射线漏0。生产v3与独立占据逐格一致，但M3 FAIL。仅诊断资产，不发布正式manifest/种子表，不继续10300图或200图抽样。[SRC-1122](../../../SOURCES.md#src-1122)、[SRC-1123](../../../SOURCES.md#src-1123)、[SRC-1124](../../../SOURCES.md#src-1124)。
- C累计7.788940408/3600s；真实SAC单测4pass1fail，B0一次更新与v5逐元素相同，B3末LR精确相等断言失败。无training.py/CLI/全状态恢复，评估与诊断仍是未接入草稿，配置有未修占位路径；不称阶段0通过。[SRC-1140](../../../SOURCES.md#src-1140)、[SRC-1141](../../../SOURCES.md#src-1141)、[SRC-1143](../../../SOURCES.md#src-1143)。
- [长训启动就绪报告：NOT_READY](../../../../results/task8/t8-phase2-20261027/long-training-readiness.md)：每run墙钟、训练峰值显存、分配/可执行命令、STOP/恢复尚无通过证据；B0/B3 smoke吞吐均未测，不能判≤48h或四卡显存门。52个冻结源/配置文件前后SHA256无漂移（不泛称大型历史产物全部核查），现场末检与报告依据[SRC-1144](../../../SOURCES.md#src-1144)。

需要用户决定：是否授权修订PCD导出采样规则以满足全部内部占据门。世界体素对齐采样仅为待审工程候选，未实现、未验证，不纳入已授权执行范围；不自行改门、补点、改v3或生产量程。各阶段继续时先读现有账本/代码与诊断资产，保留费用和失败，不重做已完成部分。

推荐模型保持GPT6.1sol/Sonnet5.5，协调medium、跨模块几何/训练与独立验收high；实施三Agent明确指定gpt-6.1-sol/high，独立验收另人Sol high。当前没有后台训练/导出需要停止，所有待实施项须在用户决定后重新派发。

## 不同Sol独立审查

[独立报告](../../../../results/task8/t8-phase2-20261027/independent-review.md)与[单次复算](../../../../results/task8/t8-phase2-20261027/independent-probe.json)：sparse_train_00000 box4、zyx=(1,14,22)、z=.05–.10m；8角严格内部最小余隙0.00868081513087117m，对含v3面容差的扩展格PCD候选点0、生产占据False。独立解析与生产PCD解析一致，源盒采样/fixture等价及持久坐标误差门通过；确认M3真实FAIL，需用户决定采样规则。A/C仅审现有局部原件，均未完整通过，不将失败确认为任务交付完成。B同账本复算及行政核查后18.968597744592/1800s、active=null。[SRC-1125](../../../SOURCES.md#src-1125)。

最终末检：2026-10-27T11:24:38+08:00，164链接/锚点通过、52冻结文件无漂移，三账本active均空，GPU compute空、forem-dev仅保活。证据[parent-final-check.json](../../../../results/task8/t8-phase2-20261027/parent-final-check.json)，依据[SRC-1144](../../../SOURCES.md#src-1144)。本轮以blocked交接，不称任务完成。


## 2026-10-27 r2续接覆盖（当前执行）

按[SRC-1161](../../../SOURCES.md#src-1161)恢复执行；上方r1停止/blocked为历史快照，保留不抹除。A继续原账本性能核查、B按cube-export-v2重做先导后全量、C继续阶段0实现；固定重复步骤依[SRC-1162](../../../SOURCES.md#src-1162)交Terra，独立Sol另人验收。当前三线active，尚未通过新门；全部门后有界B0/B3 smoke，停止于就绪报告，不启动3M。负责人/实际模型按父派发gpt-6.1-sol medium（内部标识未独立核验）；实施Sol high，推荐Claude Sonnet5.5同强度，跨几何/训练/性能因果核查需要high。过程见[r2日志](../../../agent_logs/task8/task8.9/20261027-codex-r2-coordination.md)。


## r2最终交接覆盖（当前状态：blocked）

依据[SRC-1164](../../../SOURCES.md#src-1164)，独立Sol确认A P2严格分项partial、P5完整周期成本未通过，因此“全部通过后smoke”前置不成立；本轮按遇需决定即停，不执行smoke/3M、不实施优化。原r1/r2失败与费用全部保留。当前Codex交Claude/用户复核；实际父按派发gpt-6.1-sol/medium（内部标识未独立核验），实施/验收Sol high、固定Terra low；推荐Claude Sonnet5.5同角色强度，理由为跨性能/几何/恢复因果核查。

|线|最终交接门与关键证据|
|---|---|
|A|cube batch1/16/64/256为5.161773/14.553979/17.695761/17.986311转移/s，semantic256为10.949585；各20完整步，原两次124与重复轨迹披露。P1/P3有限负载/P4/P6通过，P2/P5未整体通过；累计1597.584848462604/1800秒。[RESULTS](task8.9.1/RESULTS.md)、[SRC-1163](../../../SOURCES.md#src-1163)。|
|B|先导六图独立PASS，exact洞0/33432深墙射线漏0；已有效4013图/390420026点/7430074651B（3855训练/54验证/104测试），40块后安全停。全4013 hash/行数等复核与12新图逐点范围详节点；未10300全量/未200几何审查/未发布manifest与种子表。累计1128.2773682428524/5400秒。[RESULTS](task8.9.2/RESULTS.md)、[SRC-1130](../../../SOURCES.md#src-1130)。|
|C|22测试与修复后不同Sol实现门PASS；显式恢复局部下一更新/转移逐元素一致，原两接口FAIL保留。完整196、CLI真实smoke、吞吐/正式显存未测。累计149.024231501855/3600秒。[RESULTS](task8.9.3/RESULTS.md)、[SRC-1139](../../../SOURCES.md#src-1139)。|

三账本active均空，无本轮导出/训练后台任务（末检以保存原件为准）。B从执行表job40/offset4000续接，余6287图，先核4013缓存/冻结hash/原费用，不从0重导。所有未发布PCD仅部分资产，不得当正式训练池。

交付：[长训启动就绪报告r2](../../../../results/task8/t8-phase2-20261027/long-training-readiness-r2.md)、[独立A审查](../../../../results/task8/t8-phase2-20261027/r2-independent-a-review.md)、[独立smoke计划审查](../../../../results/task8/t8-phase2-20261027/r2-independent-smoke-plan-review.md)、[协调日志](../../../agent_logs/task8/task8.9/20261027-codex-r2-coordination.md)。报告含每run条件成本、候选GPU0–3分配/可执行命令/看门狗/STOP/恢复/监控；全部NOT_READY未启动。smoke清单只是准备，不是执行结果。

待Claude/用户决定：A P2补证据方案与预算，P5完整评估/保存成本和smoke前置的顺序，条件B0 3M基础57.725h>48h、B3 47.471h加未知项的处理。未知项不填0，不自行豁免门/扩预算/缩规模/实施优化。交接后只待明确新指令，不自动续导出或长训。

原r1首页状态留存（历史）：状态：**blocked（2026-10-27，PCD先导全内部门失败，需要用户决定采样合同；本轮未完成）**。按SRC-1160执行，三条实施线已停止新命令，独立Sol核验保存失败证据；未smoke、未启动3M。


## 2026-10-27 r3续接覆盖（执行中）

当前 **active**，按[SRC-1190](../../../SOURCES.md#src-1190)及本轮明确派发恢复；r2 blocked及失败/费用均保留。仅授权task8.9.1.1森林批量射线优化（新1500s账本）、B从job40/offset4000续原5400s账本到10300/200审查/发布、优化独立验收与池发布后C在原3600s内执行固定8job smoke。P5周期成本由smoke提供，之后补成本模型与r3就绪报告，停止交Claude；不启动3M长训。

父Codex负责共享文件；实施gpt-6.1-sol/high，固定导出/profile/smoke为gpt-6.1-terra/low，各交付由不同gpt-6.1-sol/high独立验收。推荐Claude Sonnet5.5同角色强度，优化等价与恢复需high、固定执行无特殊推理要求。实际派发标识记录于各Agent日志，不把推荐当实际。过程见[r3协调日志](../../../agent_logs/task8/task8.9/20261027-codex-r3-coordination.md)。来源新增仅1191–1209。


## r3最终交接覆盖（2026-10-27T13:04:58.502798+08:00；blocked / NOT_READY）

task8.9.1.1等价/回归/提速O1–O4独立PASS；B10300图、200审查、manifest/种子表发布独立PASS，原包装器后审文件名错误及费用保留，未重finalize。C预检通过后B0-primary在初次256环境reset采样触及235秒deadline，0动作/0转移保存中断，CLI243.166660481秒；首失败后六job未跑，不重试、不增额、不启动3M。不同Sol独立核原件确认NOT_READY。[SRC-1198](../../../SOURCES.md#src-1198)、[SRC-1200](../../../SOURCES.md#src-1200)。

因此无法用真实CLI重算B0/B3四run的完整3M墙钟、196/恢复开销或通过48h/四卡显存门；未知不填0，也不推断新版本已超48h。报告含候选命令/STOP/看门狗/恢复/监控与全部限制：[就绪报告r3](../../../../results/task8/t8-phase2-20261027/long-training-readiness-r3.md)。成本与交接依据[SRC-1201](../../../SOURCES.md#src-1201)、[SRC-1202](../../../SOURCES.md#src-1202)。

当前负责人Codex交Claude，已停止；下一步需决定有界初始采样分项诊断/执行预算和后续满回放成本方案，未经新派发不继续采样/训练。实际Sol high实施/独立验收、Terra low固定步骤；推荐Codex GPT6.1sol/Claude Sonnet5.5同角色强度，父medium协调、跨几何/恢复/成本high、简单固定low；不把推荐当实际。


## 2026-10-27 r4续接覆盖（active）

按[SRC-1210](../../../SOURCES.md#src-1210)及本轮明确派发，当前执行新[task8.9.1.2](task8.9.1/task8.9.1.2/TASK.md)有界初始化诊断、严格等价派生缓存/解析与一次全10324校验；不改采样分布/拒绝规则/witness/几何。新init总1200秒。I1是380秒仪器化部分76/256、非完整reset；95.14%资产/场景准备，依据[SRC-1212](../../../SOURCES.md#src-1212)。96图先导独立PASS，余10228全量有界执行中，不重复先导，依据[SRC-1213](../../../SOURCES.md#src-1213)、[SRC-1214](../../../SOURCES.md#src-1214)。

I2–I6独立通过后才释放C固定smoke，原费用保留，获准上限7200秒；当前C实际账本仍3600、未执行r4 smoke。新8job计划4300秒、primary900与resume原1130保留，严格冻结与缓存合同pending，依据[SRC-1216](../../../SOURCES.md#src-1216)。终止于r4就绪报告交Claude，禁止3M长训；全部历史失败/费用保留。

父Codex按派发gpt-6.1-sol/medium（内部标识未独立核验）；实施/归因与独立验收显式gpt-6.1-sol/high、固定执行gpt-6.1-terra/low。推荐Claude Sonnet5.5同角色强度，high用于跨模块严格等价/恢复归因，固定执行low；推荐不冒充实际。共享文件由父维护，[协调日志](../../../agent_logs/task8/task8.9/20261027-codex-r4-coordination.md)登记精确边界和运行。
