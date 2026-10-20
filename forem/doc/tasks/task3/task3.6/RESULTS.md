# task3.6 核心迁移独立复核 — 结果与交接

> **当前状态（2026-10-19核对）：done（审查与R2必要验收交付）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

## 2026-10-07 R2最终验收（当前有效）

**状态：done；Task3迁移验收通过。** 原审查失败、Claude自测和R2过程均为历史事实，不覆盖。父已独立读取源码delta/实际摘要/探针/清理、复查当前330文件与参考371文件、checkpoint hash及freeze verify，不以子自报完成代替验收。[SRC-0066](../../../SOURCES.md#src-0066)

|问题|最终结果与证据|
|---|---|
|T3-A01 来源闭包|底层环境/控制/模型/配置改动拒绝，同契约允许；补齐runtime包装后共同关闭|
|T3-A02 迟到/reset epoch|真实ROS回调迟到10→8不发布；clock回退后halt且无旧epoch发布，原stamp纳秒保留|
|T3-A03 freeze CWD|仓库根/forem/其他目录一致0，真实实例内容变化拒绝|
|T3-A04 包装遗漏|临时reward/mask/身份实现变更全部拒绝真实CUDA checkpoint；旧schema2无runtime及实际freeze3 checkpoint也拒绝|

完整fresh `task3.6-r2-int-20261007-r1`五阶段0，默认auto的SAC smoke/eval实际cuda:0；父先启动，执行子接管监督。子新启动生命周期8/8、0。freeze3→4仅身份实现/测试增量，物理/环境/clock/lifecycle源码和实例/环境未变，以逐hashdelta关联全套证据；不称freeze4重新跑过全套。子追加fresh `task3.6.1-wrapper-gpu-20261007-r1`（CLI不指定device）实际auto→cuda:0，76步/60更新、有限loss、更新/保存加载/载入环境驱动通过，确定性动作差0，入口和清理0。最新容器unittest298项/3 reference-tree skip/0。[执行子完整交付](task3.6.1/RESULTS.md) · [父核验](../../../../results/task3/task3.6-r2-20261007/parent-final-verification.json) · [来源](../../../SOURCES.md#src-0066)

最终执行冻结`t3.6-core-freeze4`330文件；freeze2原328、freeze3原329文件原样归档，旧run与失败全部保留。父最终verify0、foreign=[]、容器仅init/sleep。基于新raw重算94/385步两episode、IK各20/碰撞0、末done1及奖励/动作有限性一致；此为接口验收，不能宣称训练收敛或成功率。底盘/臂混合重力、reset_simulation不支持、恢复探测失败及reset后的ODE警告保留，不能当性能结果。

父实际模型/强度未知；执行子实际gpt-6.1-sol/medium；推荐Codex GPT6.1sol、Claude Sonnet5.5，跨模块medium/常规整理low或默认。下一步依据用户条件授权自动派发Task4.1，输入为当前freeze4、Task3 receipt及本次最终证据；后续位置链须重新建立契约，不加载旧truth权重。[SRC-0065](../../../SOURCES.md#src-0065)


历史首轮状态：**done（审查报告交付、当时3项P2未闭环）**。用户2026-10-07要求“审查task3”；负责人Codex /root，实际模型/强度未知。本轮仅审查与必要验证，不修改实现、不启动Task4、不委派Agent。证据依据：[SRC-0060](../../../SOURCES.md#src-0060)。

## 2026-10-07 R2独立复核与GPU修正（执行中）

用户要求重新审查并优先GPU、修改后派发子Agent执行，随后授权Task3验收通过后自动执行Task4。GPU入口auto及集成传递已实现，设备5项测试green；实际执行子task3.6.1为gpt-6.1-sol/medium，接管父已启动测试/fresh并执行剩余验证，父仍负责核验。新freeze3及旧freeze2逐hash328文件归档；运行证据见本轮日志。[SRC-0063](../../../SOURCES.md#src-0063)

三原问题：原底层source变更/legacy保护、pose迟到/reset halt、三CWD冻结/真实实例变更拒绝已获子独立探针支持，最终以父核验汇总为准。仍有T3-A04/P2：包装奖励及replay mask入口文件没有进入身份，临时改动仍接受旧checkpoint；证据为父/子两份wrapper-counterexamples.json。为满足原T3-A01完整语义身份验收，会在冻结执行空闲后补齐并由子复核，正式任务数学不变。[SRC-0064](../../../SOURCES.md#src-0064)

Task3当前保持review，Task4实际实施尚未开始，必要验收通过后再自动派发。[SRC-0065](../../../SOURCES.md#src-0065)

## 独立审查发现

### T3-A01 / P2：checkpoint来源契约遗漏环境和控制语义

`forem/scripts/task3_sac_entry.py:77–89`的`source_hashes`仅涵盖sac/model/replay_memory、顶层utils和mapencoder五文件；不包含CombinedEnv/RobotEnv/任务/EEPlanner/C++控制、组装模型及core_contract。这些源码改变奖励、观测或执行语义而不改空间形状/task YAML时，`make_contract`仍与旧checkpoint相同，`load_checkpoint_checked`会接受。独立反例仅在/tmp复制件改变combined_env.py的`return reward`，前后contract完全相等且真实checkpoint加载accepted；正式源码/配置未动。

证据：[probe脚本](../../../../results/task3/task3.6-review-20261007/probe_contract.py)、[反例结果](../../../../results/task3/task3.6-review-20261007/contract-counterexample.json)、[执行日志](../../../../logs/task3/task3.6-review-20261007/contract-counterexample.log)。

修正要求：checkpoint绑定实际环境/控制/任务语义闭包或完整core执行契约身份，并核验加载时的一致性；不能只校验五个学习模块。为环境奖励/终止/C++控制或模型变更增加错来源反例。Task4接入前应修正，否则旧truth策略的误加载保护也不完整。

### T3-A02 / P2：位姿门控用旧消息时间戳推断reset，未隔离epoch

`forem/src/forem_husky/scripts/pose_gate.py:41–49`仅凭消息戳回退>1秒就增加epoch并accept，没有独立核实仿真时钟真的回退。`pose_bridge.cb`对accept直接发布TF。无reset时10→8秒延迟样本会被接受；真实reset后10→0.1→10.02(旧epoch队列消息)→0.12全被接受，epoch从1又跳2。旧样本可被发布、混入新epoch，已有单测只覆盖小回退与干净的大回退，不覆盖该边界。

证据：[迟到反例](../../../../results/task3/task3.6-review-20261007/pose-counterexample.json)、[epoch混入反例](../../../../results/task3/task3.6-review-20261007/pose-epoch-contamination.json)。纯逻辑复现，未往正式ROS话题注入数据，未断言当前p3d已出现此问题。

修正要求：由独立仿真时钟/明确生命周期事件确认epoch变化，拒绝属于旧epoch/超出当前时钟的样本；若reset_simulation明确不支持，可采用失败后停止发布而不是自动复用旧状态。保留原消息戳，不通过重盖戳隐藏问题。补迟到>1秒及reset后旧消息反例。

### T3-A03 / P2：冻结核验依赖工作目录，交接入口从仓库根失败

`forem/scripts/freeze_task3.py:91–93`直接用`Path(ti['path'])`解析实例路径。现有freeze保存`results/task3/t3.5-inst-r1/episode_instances.json`，从仓库根执行文档推荐命令会跟到根results兼容Husky链接，退出1报changed task_instances；进入forem执行同一脚本退出0。实例文件/324文件/镜像/挂载未变，误报来自CWD。

证据：[两工作目录反例/退出码](../../../../results/task3/task3.6-review-20261007/freeze-cwd-counterexample.json)。

修正要求：保存相对于FoReM的实例路径、verify按FOREM解析（或规范为明确绝对路径并兼容历史freeze）；验证仓库根、forem和其他目录结果一致，同时真实实例改动仍应失败。不得通过改历史实例/覆盖freeze隐藏错误。

## 已完成的核验与限制

- 静态audit六项通过；独立核对266文件（254逐字/12补丁）源/目标SHA256均一致，补丁理由和diff已阅读，独立生成的12份diff与登记一致。原modulation_rl全部371个Git文件与1ccedd0快照一致；没有改husky或Task0–2实现。[哈希](../../../../results/task3/task3.6-review-20261007/independent-source-hashes.json) · [原版快照](../../../../results/task3/task3.6-review-20261007/reference-snapshot-check.json) · [diff核对](../../../../results/task3/task3.6-review-20261007/independent-patch-diffs.json)
- 容器268项单元测试退出0（3项因参考树未挂载跳过），宿主28项退出0。[容器日志](../../../../logs/task3/task3.6-review-20261007/unittest-container.log) · [宿主日志](../../../../logs/task3/task3.6-review-20261007/unittest-host.log)。已有测试通过不关闭上面三项独立反例。
- fresh `task3.6-int-20261007-r1`：物理20项通过；原始CSV独立重算保持/直行/转向/组合指标与摘要误差<1e-4（CSV输出精度的工程核对容差）。直行0.195738 m/s、转向0.457669 rad/s；样本非有限/时间不递增检查均无异常。[重算](../../../../results/task3/task3.6-review-20261007/independent-physics.json)
- 重算定义：按CSV phase分组，Δt=t_sim末−t_sim首（秒），v_path=Σsqrt(Δx²+Δy²)/Δt（m/s），ω=wrap(yaw末−yaw首)/Δt（rad/s），保持漂移=sqrt((x末−x首)²+(y末−y首)²)（m）。输入为fresh physics/timeseries.csv原始truth列，条件为同阶段时戳严格递增、所有数值有限、Δt>0；重算不依赖检查器/集成器函数，容差1e-4分别以m/s、rad/s比较摘要，不是性能合格阈值。[SRC-0060](../../../SOURCES.md#src-0060)
- 独立任务结果重算：fresh env/steps.csv的ep0/ep1分别76/247条，逐行累计IK失败20/20、碰撞0/0、最后done均1，与摘要一致；奖励求和误差4.71e-6/1.85e-5，均小于CSV五位小数的累计舍入界n×0.5e-5（原reward分数单位）。field段从planned/actual列重算最大差与摘要差1.64e-6 rad（五位小数差值界1e-5 rad），底盘/真值四位小数xy最大差与摘要差8.04e-6 m（界sqrt(2)×1e-4 m）。动作各列有限且在[-1,1]。舍入界仅为独立摘要核对，不是新增实验合格阈值。[独立脚本](../../../../results/task3/task3.6-review-20261007/independent_env_result.py) · [结果](../../../../results/task3/task3.6-review-20261007/independent-env.json) · [SRC-0060](../../../SOURCES.md#src-0060)
- 原Husky21入口/库脚本审计复跑；7算法入口分类与3世界分支说明获源码支持，未把文件数当有效算法线数。原custom_sac在当前ray1.13仍于第516行因SACTrainer.with_updates缺失不能导入。[审计](../../../../results/task3/task3.6-review-20261007/branches/husky_branches.json) · [导入日志](../../../../logs/task3/task3.6-review-20261007/reference-custom-sac-import.log)。其余算法入口及实机未运行，不宣称原训练复现。
- 底盘开重力/臂与夹爪关重力、规划臂观测/实际反馈分离、direct/base、原参数覆盖和普通update的迁移声明与代码对应；重力混合与原运行CLI未知是已披露限制，不当作物理真实性/任务成功率结论。
- 完整fresh集成`task3.6-int-20261007-r1`退出0，五阶段均返回0：physics22.5 s、env279.8 s、CPU smoke94.0 s、CPU eval62.5 s、clock259.2 s。[集成摘要](../../../../results/task3/task3.6-int-20261007-r1/integration_summary.json) · [manifest](../../../../results/task3/task3.6-int-20261007-r1/manifest.json)。env20项通过（76/247步2episode均IK失败终止），CPU SAC76步/60更新，确定性存取动作差0；时钟4项门槛通过，fresh-process复用仿真信息化探测退出1（TF不连通），不是遗漏的成功项；恢复仍需重启仿真。
- GPU `task3.6-gpu-20261007-r1`退出0（清理0），原支持的--device cuda；76步/60更新、损失有限、策略/目标Q参数更新、checkpoint确定性动作差0、载入策略驱动真实环境通过。[GPU摘要](../../../../results/task3/task3.6-gpu-20261007-r1/sac_summary.json) · [GPU manifest](../../../../results/task3/task3.6-gpu-20261007-r1/manifest.json)。收集更新16.120 s；CPU51.013 s含1个episode结束/reset、GPU0个，且仿真持续运行，这不是公平加速比/任务性能实验。硬件4卡可见；未改集成器/冻结文件。GPU checkpoint实际policy tensors为cuda:0（[设备证据](../../../../logs/task3/task3.6-review-20261007/gpu-checkpoint-devices.log)）。
- 生命周期`task3.6-life-20261007-r1`退出0，8/8通过：非法/重复run-id、外来进程拒绝且未停止、并发拒绝、SIGTERM143/SIGINT130身份清理、客户端死亡后底盘停止/臂停稳、最终空闲。L7末速2.04e-5 m/s、臂末速度2.11e-4 rad/s；这些仅支持有限指令结束后的停止检查，不是控制性能结论。[回归报告](../../../../results/task3/task3.6-life-20261007-r1-report/report.json) · [日志](../../../../logs/task3/task3.6-review-20261007/lifecycle.log)。

## 交接与下一步

负责人：Codex /root（独立审查）；实现者Claude。已完成源码/契约/单元/反例/物理重算、fresh五阶段、GPU SAC及生命周期核验。结束2026-10-07T13:15:24.411997+08:00。三项P2均未修正，Task3保持review、Task4前置尚未满足；本次不自动启动修正或后续定位/训练。建议由实现者在原授权范围修正、保留旧run/freeze，独立复核受影响入口和反例后再决定Task3验收。

运行任务：全部结束，forem-dev仅docker-init/sleep，foreign=[]；没有需要继续监控/停止/恢复的本次进程。全部新run/失败信息化探测、manifest和清理证据保留，GPU前的CPU结果也保留，未覆盖旧运行。结束身份核查：[docker top](../../../../logs/task3/task3.6-review-20261007/container-final.log) · [foreign](../../../../logs/task3/task3.6-review-20261007/foreign-final.json)。从forem目录最终freeze verify退出0；仓库根的误报仍为T3-A03。[审查汇总](../../../../results/task3/task3.6-review-20261007/review_verification.json)。

## Agent模型与推理强度

推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**，medium（跨模块checkpoint来源、TF时序/epoch、冻结路径与证据核对）；常规文档low或平台默认。实际Codex模型/强度未知，未换模型、未委派；推荐不是实际运行配置。[SRC-0046](../../../SOURCES.md#src-0046)


## 2026-10-07 给Claude的三项P2修改提示词

用户要求编写修改提示词；本轮仅交接文档，尚未派发、未启动修正。范围沿T3-A01/A02/A03，不增加后续功能。推荐Claude Sonnet5.5 / Codex GPT6.1sol，跨模块修正medium，普通交接low或默认；实际本轮Codex模型/强度未知。[SRC-0061](../../../SOURCES.md#src-0061)

```text
请在 /home/ybc/projects/CL-FoReM 修正 Task3 独立审查发现的三项 P2，并完成必要验证后交回 Codex。按以下范围执行，不只交计划。

先读根 AGENTS.md、forem/doc/README.md、PROGRESS.md、SOURCES.md、forem/ENV.md，以及 Task3 父子三文档；重点读 forem/doc/tasks/task3/task3.6/RESULTS.md 和 SRC-0060。反例与脚本在 forem/results/task3/task3.6-review-20261007/。

推荐 Claude Sonnet5.5 / Codex GPT6.1sol，修正与跨模块核对 medium；记录实际模型/强度，不可核实写未知。核对 Git、容器、GPU、进程及仿真锁，在 PROGRESS 和相应 Agent 日志登记接手。工作区有大量未提交内容，保留原实现及他人改动。

本次只修 T3-A01/A02/A03，更新必要测试、检查入口、契约/冻结和文档。实现归原 Task3.1–3.5，Task3.6 独立复核仍留 Codex。只在 forem 开发；husky 及其他参考仓库只读，ROS 仅容器，Docker 使用 sg docker -c。不启动 Task4、定位、人工误差、补偿、世界模型、大规模训练，不改任务/动作/观测/奖励、物理模型或控制器语义，不推送/合并。

1. T3-A01：checkpoint 的 source_hashes 目前只覆盖五个学习模块。绑定实际环境、任务、控制、模型及必要配置的语义身份，加载时核对当前实际文件；仅哈希未核验的旧 manifest/freeze 不能解决问题。用临时副本分别改变奖励/终止、C++控制或机器人模型，保持观测/动作形状不变，旧 checkpoint 必须被拒绝；同契约保存加载仍应一致。旧版缺完整身份的 checkpoint 明确拒绝，不自动补契约冒充兼容。

2. T3-A02：PoseGate 不能仅凭位姿消息时间戳的大回退判断 reset。通过独立仿真时钟或明确生命周期事件确认状态，拒绝迟到消息和旧 epoch 消息，保留原采样戳。复现无 reset 的 10→8 秒旧样本，以及真实 reset 后 10→0.1→10.02（旧消息）→0.12；不能发布旧消息或错误累加 epoch。reset_simulation 仍可保持不支持：检测后停止发布、使 episode 失效并要求 fresh 重启，不以新增自动恢复为目标。同步检查脚本和限制记录，保留错误样本拒绝与 episode 失效的真实门槛。

3. T3-A03：实例路径统一按 FoReM 根解析；正确处理 create 输入和已有 freeze 的路径，避免根 results 兼容链接参与解析。从仓库根、forem、另一个目录调用同一 verify，结果必须一致；临时副本中实例内容真的改变时仍必须失败。不得改历史实例来绕过核验。

先复现反例，再修正并记录修正前失败、修正后通过。运行相关新增测试、宿主来源/语义检查及容器全量测试；用新 run-id 完成受影响的 fresh 核验和生命周期检查。SAC 核验使用 --device cuda，确认实际 tensor device、普通 update、有限损失、保存加载与加载后驱动环境。现有集成器若仍硬编码 CPU，可保留其完整集成证据并另跑 GPU SAC 链，不为换设备扩展接口。仅使用原短核验预算，不启动收敛训练；仿真顺序独占。

修正需要更新 freeze 时，先按旧 freeze-id 原样归档，再生成新 freeze-id，记录受影响字段及历史有效性；保留所有旧 run、失败尝试和审查反例。源码导入文件发生变化时同步 manifest、patch 理由/diff 和来源台账。证据分别放 forem/logs/task3/<新run-id>/、forem/results/task3/<新run-id>/，保持递归三文档规则；不要覆盖 Codex 的历史审查记录。

最终交付逐项表：问题编号、根因、修改文件、反例前后结果、命令/退出码、证据、新 freeze/入口、剩余限制。同步 PROGRESS、相关 RESULTS、ENV 和 SOURCES，结束核对自身进程清零。三项自测修正后交 review，父 Task3 保持 review，等待 Codex 独立复核通过；不得因修正完成或报告 done 自动进入 Task4。
```

## 历史：计划交付记录

# task3.6 核心迁移独立复核 — 结果与交接

状态：**review（本轮只交付计划；实施尚未执行）**。

## 本轮实际记录

本轮Codex编写TASK/PROCEDURE/RESULTS；未创建上述计划源码、未装依赖、未构建/启动本节点、未运行训练或性能评估。新run-id、运行命令/退出码、实际参数/模型、测量、模型权重及验收结论均无，不能填作已执行。文档核验汇总在[父结果](../RESULTS.md)。

## 后续run记录规则

每次执行追加run-id、负责人/实际模型强度、开始结束时间、完整命令/退出码、来源/镜像/契约hash、配置差异、日志/原数据/产物、有效性/失败与清理。保留所有尝试，不将后次结果覆盖前次失败。没有证据的主张标“待补证据”。

## 交接

- 目标/授权：独立核实核心迁移、普通SAC与可重复运行证据，决定Task3是否done并解锁Task4。 本轮仅计划。
- 当前负责人：Codex文档；拟Codex后续接手，尚未登记。
- 已完成：三文档计划，未实施节点交付。
- 前置与剩余：task3.5交审；复核者与实现者不同；执行PROCEDURE全部步骤并核验。
- 风险：来源/依赖、帧/时间/状态语义、有效输入与失败分母及资源预算需实际验证。
- 下一步：读根AGENTS、父/子三文档、PROGRESS/ENV，核查实际状态和实施授权后登记接手。
- 运行任务：无本节点PID、无停止/恢复动作；后续运行须写容器/PID/身份、日志和控制方法。

依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046)。不得因本计划完整把节点标done。

## 迁移后的用户讲解交付

用户要求迁移完成后详细说明原Husky“有几条线、各自什么用途”。3.1审计原运行入口/调用图，3.5在本层RESULTS交付完整说明，3.6按源码和运行证据核对。按“算法训练/评估分支”“在线任务到物理执行链”“世界模式/位置来源”分别给核实计数；不把重复源码树或入口文件数冒充有效运行线。每条说明目的、入口、输入输出、上下游、活跃/历史状态和迁移保留/改造/未迁移范围，并标未运行项。迁移完成后向用户逐条讲解，不只交文件清单；本轮尚未迁移，也未核实最终数量。审核说明其他分支不扩大本次移植范围。[SRC-0049](../../../SOURCES.md#src-0049)

## Agent与推理强度

推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**。常规文档/明确步骤运行low或平台默认；来源迁移、坐标/时间/观测与验收的跨模块核对medium，理由是需要追踪完整因果链。当前文档作者Codex /root，实际模型/强度未知；拟Claude实施、Codex独立复核，均未接手，不自动启动Agent。实施时记录实际配置，推荐不冒充执行配置。


## 2026-10-07 实现者修正已交付（Claude，待Codex独立复核）

三项P2已由Claude按原Task3.1–3.5范围修正并自测，详见[task3 RESULTS](../RESULTS.md#2026-10-07-task36三项p2修正claude)。本节点审查记录未改；修正是否关闭三项P2由Codex独立复核决定，自测不等于验收。
