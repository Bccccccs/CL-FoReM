# task8.9 — 执行流程

**2026-10-27 已作废（closed）**：用户指令“现在的8.9作废吧，要优化好了整体的地图再开始训练”（[SRC-1220](../../../SOURCES.md#src-1220)）。本节点不再执行；以下为作废前的历史状态与记录，原样保留。

状态：**draft（规划，尚未执行）**。目标见[TASK](TASK.md)，来源[SRC-1102](../../../SOURCES.md#src-1102)。

## 递归规则

每层恰有TASK/PROCEDURE/RESULTS三文档；子任务位于父目录内、继承编号（task8.9.N，再拆为task8.9.N.M）。再拆分前先建三文档并登记顺序、依赖、负责人、模型/强度、输入输出和父验收关系；编号稳定不复用。父RESULTS只汇总子RESULTS，不以父计划代替子任务实测。代码/配置/日志/产物分别归`forem/src`、`config`、`logs/task8`、`results/task8`。

## 子任务、顺序与验收关系

|顺序|任务|三文档|负责人（推荐）|依赖|父验收关系|
|---|---|---|---|---|---|
|1a|task8.9.1 批量性能核查|[TASK](task8.9.1/TASK.md) / [PROCEDURE](task8.9.1/PROCEDURE.md) / [RESULTS](task8.9.1/RESULTS.md)|Codex父→Sol high实施、Luna low固定执行、独立Sol high验收|task8.8 done|实测profile与成本模型交8.9.3|
|1b|task8.9.2 地图池划分|[TASK](task8.9.2/TASK.md) / [PROCEDURE](task8.9.2/PROCEDURE.md) / [RESULTS](task8.9.2/RESULTS.md)|Codex父→Sol medium、Luna low、独立Sol high验收|task8.8 done|划分方案交用户决定后交8.9.3|
|2|task8.9.3 长程对照设计|[TASK](task8.9.3/TASK.md) / [PROCEDURE](task8.9.3/PROCEDURE.md) / [RESULTS](task8.9.3/RESULTS.md)|Claude定稿协议、Sol high审查；执行另行授权|1a成本＋1b池决定|协议经用户批准方可执行|

1a/1b真正独立（写入文件不重叠），可同时派发；GPU使用由父串行调度，只用核实无compute进程的卡。

## 共同边界（所有子任务）

- 只读：task7全部源码/配置/产物（含v5、7.18.8诊断）、mapgen、archive、task8.8前的v1/v2产物。
- 不训练：8.9.1/8.9.2不得执行任何optimizer step，不运行`task7_lower`测试或任何含SAC更新的代码；冻结actor只做推理。
- 不改奖励/动作/观测/终止/IK/Grid/策略接口与v3几何；不增实验组。
- 每个子任务新账本，预算见各TASK；不足时停止报告，不自行加预算。
- SOURCES编号：8.9.1用SRC-1103–1119，8.9.2用SRC-1120–1139，8.9.3定稿用SRC-1140–1159；共享PROGRESS/SOURCES/父文档由父协调维护。

## 派发

2026-10-27按用户授权（[SRC-1160](../../../SOURCES.md#src-1160)）派发下列prompt（原“本轮未派发”为规划时状态）。改为一个Codex父协调并行执行8.9.1、8.9.2阶段B与8.9.3阶段0，smoke后停下交Claude复核；3M长训由Claude复核启动就绪报告后另行派发。Claude后台监督。

## 派发prompt r1（2026-10-27，Claude→Codex父协调）

```text
你是FoReM task8.9第二阶段的执行协调者（Codex，推荐gpt-6.1-sol / medium）。工作区/home/ybc/projects/CL-FoReM。Claude写文档并派发你，你可再派子Agent：高推理编码/归因用gpt-6.1-sol（high），判据固定的简单执行用gpt-6-luna（low），每项交付由与实施者不同的gpt-6.1-sol（high）独立验收；Luna交付须Sol查原产物。显式选择模型并在各RESULTS登记实际模型/强度。

先读：AGENTS.md、forem/ENV.md、forem/doc/README.md、forem/doc/PROGRESS.md、forem/doc/tasks/task8/task8.9/{TASK,PROCEDURE,RESULTS}.md及task8.9.1、task8.9.2、task8.9.3各三文档，forem/doc/SOURCES.md中SRC-0181、0983、1000、1021、1081、1100、1101、1102、1160，以及task8.8 RESULTS。

用户授权（SRC-1160）：①8.9.1批量性能核查（不训练）；②8.9.2阶段B S3：mapgen_a全部10,000训练＋100验证＋200测试图（forem/results/task7/maps/a/20261021T021400Z/，盒体格式[x,y,z,sx,sy,sz,cos,sin]为最小角局部坐标系，与mapgen语义JSON相同）按v3协议确定性导出PCD池，24张语义图作迁移评估集；阶段A暂缓；③8.9.3阶段0：新建task8训练入口（不改task7_lower原文件，例如forem/src/task8_lower/），可注入PcdEpisodeEnv，实现每N转移更新（UTD）、RLlib温度规则（α初值1、α学习率1e-4按转移数线性降至1e-6、无上下限）、按转移数线性学习率；B0配置与v5（forem/config/task7/lower_train.json及其运行时实际行为）逐项一致；验证协议为100张立方体验证图各1 episode＋24语义图×4固定种子迁移评估（不参与选模）；诊断字段按8.9.3 TASK；含SAC更新的单元测试在此授权内可运行。

执行顺序：A=8.9.1（GPU0）、B=8.9.2阶段B导出（CPU为主，先核容器CPU并合理设并行进程数）、C=8.9.3阶段0实现与测试（GPU1）三条并行，互不写同一文件；PROGRESS/SOURCES/父文档只由你维护（SOURCES编号：8.9.1用1103–1119，8.9.2用1120–1139，8.9.3用1140–1159）。三者独立验收通过后：用8.9.1成本模型＋C的实现做有界端到端smoke（B0与B3各一个短run，确认吞吐、显存、诊断字段、检查点/恢复、验证协议），然后**停下**，写“长训启动就绪报告”（每run预计墙钟、显存、GPU分配、命令、看门狗/STOP/恢复方式）交Claude复核，不要自行启动3M长训。启动门：预计单run>48h或4卡显存不足则如实报告。

边界：不改奖励/动作/观测/终止/网络结构/SAC损失数学、v3几何与生产量程；不恢复task7冻结任务（v5续训、D10、7.24、7.18.8），task7产物只读；不调用mapgen；阶段2与其他实验组未授权。8.9.1性能优化只出方案不实施，除非是阶段0 smoke必需且语义等价（逐元素一致）并单独记录理由——若需要，先停下报告。各子任务新账本：8.9.1≤1800s；8.9.2导出预算按实测速率定并记账；8.9.3阶段0测试与smoke≤3600s。GPU只用核实无compute进程的卡；用已运行forem-dev，不建/停容器或他人进程。不提交、不推送、不合并。

完成时last message给简短中文总结：各子任务各门结果、关键数字（256环境吞吐与热点、导出图数/体积/复核结果、smoke吞吐）、长训启动就绪报告位置、未解决问题和需用户决定事项。遇到需要用户决定的问题停下报告，不自行扩展范围。
```

## 2026-10-27 执行状态覆盖

按[SRC-1160](../../../SOURCES.md#src-1160)及派发prompt r1，当前执行A性能核查、B的S3全量导出、C阶段0实现/测试，三者并行并分别独立验收；然后有界B0/B3 smoke并停止交Claude复核。前文只写规划、阶段A先行和未授权阶段0等描述是原规划快照，现行范围以本段、派发prompt及最新用户指令为准。3M长训本轮不启动，阶段2未授权。

## 本轮停止覆盖

2026-10-27已停止后续执行：task8.9.2局部中心采样的先导全内部门FAIL；本轮blocked，不继续全量/200抽样，不补性能/测试/smoke或启动3M，先独立复核保存证据并报告用户采样合同决定。当前部分成果、费用与未完成项以[RESULTS](RESULTS.md)为准，依据[SRC-1123](../../../SOURCES.md#src-1123)、[SRC-1144](../../../SOURCES.md#src-1144)。

## 派发prompt r2（2026-10-27，Claude→Codex父协调；用户“你看着跑吧”）

```text
你是FoReM task8.9第二阶段r2的执行协调者（Codex，推荐gpt-6.1-sol / medium）。工作区/home/ybc/projects/CL-FoReM。这是r1的续接。r1结果：8.9.2立方体PCD先导6图exact全内部缺格7303（墙0、深墙射线漏0），根因为随机yaw盒体的局部中心格点在世界体素上混叠（反例sparse_train_00000 box4），全量未导出；8.9.1只完成prepare（64立方体夹具＋24语义各1 episode），run/batch profile未跑；8.9.3阶段0部分实现（task8_lower sac/replay/diagnostics/evaluation草稿，真实SAC测试4过1败：B3末LR精确等于1e-6断言，实际9.999999999999972e-7），无training.py/CLI/全状态恢复，配置transfer_pool为占位错误路径。

Claude按用户授权（“ok，你看着跑吧”）决定SRC-1161：立方体池改用导出规则cube-export-v2——每个盒体（JSON最小角闭合OBB）目标占据O=A∪B，A=中心落在闭合盒内的数据域内世界体素，B=包含task8.1局部中心格点样本的世界体素；PCD写O中各体素的世界中心坐标。验收①生产v3占据与O逐格相等②exact全内部缺格=0③占据⊆闭合盒supercover④每盒≥1格⑤穿透深度门（SRC-1081）漏检0⑥逐图hash/点数/边界；抽样≥200图做①–⑤，全量做①④⑥。语义池与v3体素化不变。

先读：AGENTS.md、forem/doc/PROGRESS.md、forem/doc/tasks/task8/task8.9/及三个子任务三文档（含r1全部记录）、forem/doc/SOURCES.md中SRC-1081、1100–1124、1140–1144、1160、1161，以及forem/doc/agent_logs/task8/task8.9/下全部日志与各账本。从现有代码/账本/产物继续，不重复已完成且仍有效的部分，保留r1全部失败记录与费用。

三条线并行（文件互不重叠，共享PROGRESS/SOURCES/父文档只由你维护；SOURCES：8.9.1用剩余1103–1119未用号、8.9.2用1125–1139、8.9.3用1145–1159）：
A 8.9.1（GPU0，沿用t8-perf-20261027账本，累计≤1800s）：完成run/batch 1/16/64/256 profile、热点、优化方案（只出方案）、成本模型；导出池可用后可在其子集上补测一次。
B 8.9.2阶段B（CPU为主，沿用其账本，导出预算按实测速率定并记账）：实现cube-export-v2，先6图先导过①–⑤再全量10,300图；发布manifest（split/difficulty/seed/源hash/生成器hash/cube-export-v2/v3）与evaluation-seeds.json（验证100图×1、24语义图×4固定种子）；验证/测试与训练严格分离。
C 8.9.3阶段0（GPU1，沿用t8-train-stage0-20261027账本，测试＋smoke累计≤3600s）：修B3末LR断言（按浮点误差给出有依据的容差，不改日程定义）；完成训练主循环与CLI（注入PcdEpisodeEnv、UTD每N转移、RLlib温度、线性lr、1000转移诊断、评估调度、STOP/信号/非有限与Q看门狗保存）、全状态检查点与精确恢复（PcdEpisodeEnv拒绝pickle，需显式状态包装；恢复后下一转移与下一次更新逐元素一致，禁止fresh reset冒充恢复）；配置改用B发布的正式池路径；B0与v5逐项一致核对表。
三者各由与实施者不同的gpt-6.1-sol high独立验收。用户2026-10-27新指示（SRC-1162）：重复、简单、判据固定的步骤（固定命令清单执行、批量导出、hash/计数核对、表格汇总等）改派**gpt-6.1-terra**（平台上6.1 terra的实际模型名以平台列表为准；不可用时如实记录并退回gpt-6-luna），其交付须Sol复核原产物；需要推理的编码/归因/验收仍用gpt-6.1-sol。全部通过后做有界smoke：B0与B3各一个短run（在C账本内，覆盖至少一次评估、一次检查点与一次恢复），测吞吐与峰值显存，然后**停下**写“长训启动就绪报告”（每run预计墙钟、显存、GPU分配0–3、可执行命令、看门狗/STOP/恢复/监控方式），交Claude复核；不要自行启动3M长训。启动门：预计单run>48h或4卡显存不足则如实报告。

边界：不改奖励/动作/观测/终止/网络结构/SAC损失数学、v3几何与生产量程；不改task7_lower等task7文件与产物；不调用mapgen；阶段2与其他组未授权；性能优化只出方案（若smoke必需，先停下报告）。GPU只用核实无compute进程的卡；用已运行forem-dev，不建/停容器或他人进程。显式选择gpt-6.1-sol/gpt-6.1-terra（备选gpt-6-luna）并在RESULTS登记实际模型/强度。不提交、不推送、不合并。

完成时last message给简短中文总结：三条线各门结果与关键数字、导出图数/体积/复核结果、smoke吞吐与显存、长训启动就绪报告路径、未解决问题和需用户/Claude决定事项。遇到需要决定的问题停下报告。
```


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

## 派发prompt r3（2026-10-27，Claude→Codex父协调）

```text
你是FoReM task8.9第二阶段r3的执行协调者（Codex，推荐gpt-6.1-sol / medium）。工作区/home/ybc/projects/CL-FoReM。这是r2的续接。r2结果：A立方体256环境17.99转移/s、raycast占91.69%/94.67%，64→256几乎不增；B导出4013/10300图（7.43GB），六图先导①–⑤独立PASS，未发布manifest；C 22项GPU测试通过、独立验收（修复后）PASS；smoke未执行；B0条件3M约57.7h超48h门。就绪报告forem/results/task8/t8-phase2-20261027/long-training-readiness-r2.md。

Claude按用户授权决定SRC-1190：①执行新子任务task8.9.1.1（三文档已建）：SceneBatch跨场景批量射线（拼接BVH森林、所有行射线同批遍历，逐射线算术不变），必要时同法批量化碰撞；验收O1固定输入CPU float64与GPU float32距离/命中torch.equal、PcdPanorama Depth全字段相等、≥50 Core step Transition逐字段相等，O2 task8_sim全回归，O3重测batch64/256吞吐，O4独立Sol high；新账本forem/logs/task8/t8-perf-opt-20261027/budget.json≤1500s；做不到逐元素相等就停下报告，不用容差替代。②B从fixed-full-r2.json next_job_index40（offset4000）续导至10300，完成≥200图①–⑤审查，finalize发布manifest与evaluation-seeds.json（沿用B账本5400s）。③优化验收且池发布后，C执行已准备的smoke清单（8 jobs，沿用C账本3600s），其实测提供P5所需的100验证＋96迁移评估、checkpoint、恢复成本——smoke不再以P5通过为前置；之后A用smoke数据补齐P5成本模型（A原账本余额不足的部分记入task8.9.1.1账本）。

先读：AGENTS.md、forem/doc/PROGRESS.md、forem/doc/tasks/task8/task8.9/下全部三文档（含task8.9.1.1）、上述就绪报告、forem/doc/SOURCES.md中SRC-1100、1160–1164、1190及r2各来源条目，以及forem/doc/agent_logs/task8/task8.9/下日志与各账本。从现有代码/账本/产物继续，不重复已完成部分，保留全部失败记录与费用。SOURCES只用SRC-1191–1209（1180段已被其他会话使用）。

模型：编码/归因/验收用gpt-6.1-sol（high），每项交付由与实施者不同的gpt-6.1-sol high独立验收；重复/简单固定步骤（批量导出续跑、hash/计数核对、固定profile/smoke命令执行、表格汇总）用gpt-6.1-terra（不可用退gpt-6-luna并记录），交付须Sol复核原产物。显式选择并在RESULTS登记实际模型/强度。

完成后写long-training-readiness-r3.md：用smoke实测的真实CLI吞吐、峰值显存、评估/保存/恢复耗时重算每run 3M墙钟（B0/B3，GPU0–3），给出可执行命令、看门狗/STOP/恢复/监控方式，然后**停下**交Claude复核，不要自行启动3M长训。

边界：不改奖励/动作/观测/终止/网络结构/SAC损失数学、v3几何、生产量程与PcdPanorama语义；不改task7文件与产物；不调用mapgen；阶段2与其他组未授权；除task8.9.1.1外不做其他性能优化。GPU只用核实无compute进程的卡；用已运行forem-dev，不建/停容器或他人进程。不提交、不推送、不合并。

完成时last message给简短中文总结：task8.9.1.1等价与提速倍数、池发布结果、smoke吞吐/显存/评估成本、重算的每run墙钟与48h门判断、就绪报告路径、未解决问题和需决定事项。遇到需要决定的问题停下报告。
```


## 2026-10-27 r3续接覆盖（执行中）

当前 **active**，按[SRC-1190](../../../SOURCES.md#src-1190)及本轮明确派发恢复；r2 blocked及失败/费用均保留。仅授权task8.9.1.1森林批量射线优化（新1500s账本）、B从job40/offset4000续原5400s账本到10300/200审查/发布、优化独立验收与池发布后C在原3600s内执行固定8job smoke。P5周期成本由smoke提供，之后补成本模型与r3就绪报告，停止交Claude；不启动3M长训。

父Codex负责共享文件；实施gpt-6.1-sol/high，固定导出/profile/smoke为gpt-6.1-terra/low，各交付由不同gpt-6.1-sol/high独立验收。推荐Claude Sonnet5.5同角色强度，优化等价与恢复需high、固定执行无特殊推理要求。实际派发标识记录于各Agent日志，不把推荐当实际。过程见[r3协调日志](../../../agent_logs/task8/task8.9/20261027-codex-r3-coordination.md)。来源新增仅1191–1209。


## r3最终交接覆盖（2026-10-27T13:04:58.502798+08:00；blocked / NOT_READY）

task8.9.1.1等价/回归/提速O1–O4独立PASS；B10300图、200审查、manifest/种子表发布独立PASS，原包装器后审文件名错误及费用保留，未重finalize。C预检通过后B0-primary在初次256环境reset采样触及235秒deadline，0动作/0转移保存中断，CLI243.166660481秒；首失败后六job未跑，不重试、不增额、不启动3M。不同Sol独立核原件确认NOT_READY。[SRC-1198](../../../SOURCES.md#src-1198)、[SRC-1200](../../../SOURCES.md#src-1200)。

因此无法用真实CLI重算B0/B3四run的完整3M墙钟、196/恢复开销或通过48h/四卡显存门；未知不填0，也不推断新版本已超48h。报告含候选命令/STOP/看门狗/恢复/监控与全部限制：[就绪报告r3](../../../../results/task8/t8-phase2-20261027/long-training-readiness-r3.md)。成本与交接依据[SRC-1201](../../../SOURCES.md#src-1201)、[SRC-1202](../../../SOURCES.md#src-1202)。

当前负责人Codex交Claude，已停止；下一步需决定有界初始采样分项诊断/执行预算和后续满回放成本方案，未经新派发不继续采样/训练。实际Sol high实施/独立验收、Terra low固定步骤；推荐Codex GPT6.1sol/Claude Sonnet5.5同角色强度，父medium协调、跨几何/恢复/成本high、简单固定low；不把推荐当实际。

## 派发prompt r4（2026-10-27，Claude→Codex父协调）

```text
你是FoReM task8.9第二阶段r4的执行协调者（Codex，推荐gpt-6.1-sol / medium）。工作区/home/ybc/projects/CL-FoReM。这是r3的续接。r3结果：task8.9.1.1批量射线严格等价并独立验收，256环境145.35/116.29转移/s（8.08×/10.62×）；正式池10300图20.60GB发布并独立验收；smoke首job（B0-primary，ba918a165a）在初始256环境env.reset→sample→check_sampling触及235s内部上限，0动作/0转移；就绪报告forem/results/task8/t8-phase2-20261027/long-training-readiness-r3.md为NOT_READY。

Claude按用户授权决定SRC-1210：①执行新子任务task8.9.1.2（三文档已建）：对初始256环境采样做有界分项诊断（PCD读取/解析、体素化/打包/BVH、上传、提案与拒绝原因、初态校验、规划、witness），并估计训练期每百万转移reset次数；新账本forem/logs/task8/t8-init-20261027/budget.json≤1200s。②按诊断占比实施逐元素等价修复：(a)派生场景缓存（键=PCD sha256＋scene.py实现hash＋v3版本，全量10300＋24图逐图加载结果与from_asset逐张量torch.equal一次性校验，运行时键不匹配即拒绝）；(b)更快的PCD解析（全部PCD逐值float64比特相等，格式校验行为一致）；(c)仅当(a)(b)不足时，跨环境并行采样，各环境RNG流/采样结果/Episode字段须与串行逐字段相等。不改采样分布、拒绝规则、witness判据与几何；若根因是采样规则本身，停下报告。③之后重跑C的smoke清单：单job内部上限由235s放宽至900s，C账本上限由3600s增至7200s（不缩评估集/步数/种子）；用smoke实测补齐P5（真实CLI吞吐、峰值显存、100验证＋96迁移评估、checkpoint与恢复耗时）。④写long-training-readiness-r4.md，用实测重算B0/B3每run 3M墙钟与48h门，给可执行命令（GPU0–3）、看门狗/STOP/恢复/监控方式，然后**停下**交Claude复核，不要自行启动3M长训。

先读：AGENTS.md、forem/doc/PROGRESS.md、forem/doc/tasks/task8/task8.9/下全部三文档（含task8.9.1.1、task8.9.1.2）、r3就绪报告、forem/doc/SOURCES.md中SRC-1190–1210，以及forem/doc/agent_logs/task8/task8.9/下日志与各账本。从现有代码/账本/产物继续，不重复已完成部分，保留全部失败记录与费用。SOURCES只用SRC-1211–1229。

模型：诊断/编码/归因/验收用gpt-6.1-sol（high），每项交付由与实施者不同的gpt-6.1-sol high独立验收；全量缓存生成与逐图校验、固定smoke命令执行、hash/计数核对、表格汇总用gpt-6.1-terra（不可用退gpt-6-luna并记录），交付须Sol复核原产物。显式选择并在RESULTS登记实际模型/强度。

边界：不改奖励/动作/观测/终止/网络结构/SAC损失数学、v3几何、生产量程、PcdPanorama语义与采样规则；不改task7文件与产物；不调用mapgen；阶段2与其他组未授权；除task8.9.1.1与本次授权的(a)(b)(c)外不做其他性能优化。GPU只用核实无compute进程的卡；用已运行forem-dev，不建/停容器或他人进程。派生缓存放forem/results/task8/<run-id>/下，不入Git。不提交、不推送、不合并。

完成时last message给简短中文总结：初始采样分项占比与根因、所做修复及等价验收、初始化/ reset新耗时、smoke吞吐/显存/评估/保存/恢复成本、重算的每run墙钟与48h门判断、就绪报告路径、未解决问题和需决定事项。遇到需要决定的问题停下报告。
```


## 2026-10-27 r4续接覆盖（active）

按[SRC-1210](../../../SOURCES.md#src-1210)及本轮明确派发，当前执行新[task8.9.1.2](task8.9.1/task8.9.1.2/TASK.md)有界初始化诊断、严格等价派生缓存/解析与一次全10324校验；不改采样分布/拒绝规则/witness/几何。新init总1200秒。I1是380秒仪器化部分76/256、非完整reset；95.14%资产/场景准备，依据[SRC-1212](../../../SOURCES.md#src-1212)。96图先导独立PASS，余10228全量有界执行中，不重复先导，依据[SRC-1213](../../../SOURCES.md#src-1213)、[SRC-1214](../../../SOURCES.md#src-1214)。

I2–I6独立通过后才释放C固定smoke，原费用保留，获准上限7200秒；当前C实际账本仍3600、未执行r4 smoke。新8job计划4300秒、primary900与resume原1130保留，严格冻结与缓存合同pending，依据[SRC-1216](../../../SOURCES.md#src-1216)。终止于r4就绪报告交Claude，禁止3M长训；全部历史失败/费用保留。

父Codex按派发gpt-6.1-sol/medium（内部标识未独立核验）；实施/归因与独立验收显式gpt-6.1-sol/high、固定执行gpt-6.1-terra/low。推荐Claude Sonnet5.5同角色强度，high用于跨模块严格等价/恢复归因，固定执行low；推荐不冒充实际。共享文件由父维护，[协调日志](../../../agent_logs/task8/task8.9/20261027-codex-r4-coordination.md)登记精确边界和运行。
