# task9 PROCEDURE — 原语后端下层SAC长程对照

## 2026-11-04 当前预算与审核原则（优先于历史冲突条款）

按[用户下层同步指令](../../SOURCES.md#src-task9-budget-review-20261104)和[全局规则](../../../../AGENTS.md#budget-review)，合理训练预算由执行者按实际成本自主安排，必要排错/恢复/重跑无需逐次申请。已经通过的G1、LON及保存恢复等证据，在版本和适用条件一致时直接复用；仅对新增代码、实际失败或具体疑点做一次定向核查，不强制逐阶段另开独审、重复全量hash/测试或重审政策。必要检查通过后直接推进已授权训练与评估。

历史预算、消耗、FAIL/UNKNOWN如实保留；未知历史账不填零，也不为还原全部历史反复阻塞已有授权训练，除非确实影响当前安全运行或结论。工程预估和执行者设定的细碎上限可合理调整并登记；单卡隔离、用户明确交付截止、科学可比性及真实bug修复要求保留。旧首失败即停报调整为保留失败、必要修复并定向复验后自主推进；相同原因反复失败先定位，不盲目重试。活动task9.11.18流程由当前执行者按本节落实，本轮未覆盖其源码、运行配置或科学协议。

推荐GPT6.1sol/low、Sonnet5.5/low用于常规执行/文档；跨模块真实故障按需medium/high。执行者可自主选模或先建档委派，审核不强制另派Agent。下文旧阶段安排及历史验收保留，不作为重复审核要求。

状态：**review（2026-11-02全部训练结束；9.5最终验收通过，9.4整批验收另待）**。依据[TASK](TASK.md)。

## 递归规则声明

遵守根AGENTS项目级任务组织规则：每层恰有TASK/PROCEDURE/RESULTS；子任务在本目录内继承编号（task9.1、task9.2…），各自三文档；父流程列明顺序、依赖、负责人与验收关系，父结果汇总子结果，不以父计划代替子任务实测。编号稳定不复用。

## 顺序、依赖、负责人

|顺序|子任务|三文档|依赖|负责人与验收|
|---|---|---|---|---|
|1|task9.1 smoke|[TASK](task9.1/TASK.md) / [PROCEDURE](task9.1/PROCEDURE.md) / [RESULTS](task9.1/RESULTS.md)|task8.11 done、task8.13 done、用户批准（SRC-1313）|Claude父规划；P1准备/执行Claude子Agent Sonnet5.5 high；P2独立验收另一Sonnet5.5 high子Agent；父汇总核验|
|2|task9.2 长训|[TASK](task9.2/TASK.md) / [PROCEDURE](task9.2/PROCEDURE.md) / [RESULTS](task9.2/RESULTS.md)|9.1独立验收done with conditions；用户批准（SRC-1316）|Claude父启动与监控；独立验收另一Agent（Codex额度2026-11-02恢复后可交回）|
|3|task9.3 B0退化诊断|[TASK](task9.3/TASK.md) / [PROCEDURE](task9.3/PROCEDURE.md) / [RESULTS](task9.3/RESULTS.md)|task9.2 done with conditions；用户指令SRC-1319|Codex GPT6.1sol / high执行S1–S3（可派terra抽取，Sol复核）；V4另一Sol独立核验；Claude父汇总|
|4|task9.4 阶段2长训|[TASK](task9.4/TASK.md) / [PROCEDURE](task9.4/PROCEDURE.md) / [RESULTS](task9.4/RESULTS.md)|task9.3 done with conditions；用户批准SRC-1322|Codex GPT6.1sol / high执行G1–G4；Claude父监控；独立验收另一Agent|
|5|task9.5参数与多方向优化|[TASK](task9.5/TASK.md) / [PROCEDURE](task9.5/PROCEDURE.md) / [RESULTS](task9.5/RESULTS.md)|用户SRC-1336，旧5M保护|Codex父协调，.1预审/.2实施/.3独立验收/.4性能审计|

## 共同约束

不改奖励/动作/观测/终止/采样规则与B0/B3定义；9.5仅在新隔离副本新增明确SAC参数轴，历史组定义不变；不缩环境数/回放/评估规模、不放宽门、不延预算；首失败即停报；不停止或重建他人进程/容器；`sg docker -c`进forem-dev；子Agent不写PROGRESS/DECISIONS/SOURCES，主张交父登记。

2026-11-02：新增[task9.6语义复评](task9.6/PROCEDURE.md)，用户要求现在启动、下午看结果；仅既有B3三5M final与24×4固定语义回合，不训练。[SRC-1354](../../SOURCES.md#src-1354)。

2026-11-02 14:14：[task9.6](task9.6/RESULTS.md) done，12:06三B3-5M语义复评完成、父逐case核验PASS，132/288=45.83%，与原成败全部一致；[SRC-1355](../../SOURCES.md#src-1355)。不替代9.4全批独立验收。

2026-11-02 · task9.7 依赖既有 task9.4–9.6 证据，负责人待派发；按失败核查→配对比较→对照草案顺序，仅验收文档，尚未执行。[TASK](task9.7/TASK.md) · [PROCEDURE](task9.7/PROCEDURE.md) · [RESULTS](task9.7/RESULTS.md)。

2026-11-02 · task9.8 固定案例迁移诊断依赖9.6复评与9.7已有分析；准备执行者 A → 经用户核定预算的回放执行者 B → 独立核验人 C → 监督者汇总。按案例身份与逐步证据验收。[TASK](task9.8/TASK.md) · [PROCEDURE](task9.8/PROCEDURE.md) · [RESULTS](task9.8/RESULTS.md)。

2026-11-02 · task9.9 依赖9.8 C通过，Codex顺序离线复算→调用链核验→监督建议，验收逐例证据/18/R1/N11/U0对账；无子Agent/实验。[TASK](task9.9/TASK.md) · [PROCEDURE](task9.9/PROCEDURE.md) · [RESULTS](task9.9/RESULTS.md)。推荐GPT6.1sol/high、Sonnet5.5/high，跨轨迹和源码因果核查。

2026-11-03 · task9.10 下层能力/效率路线与单次动作机制对照，review（设计）。依赖9.8/9.9证据，监督Codex；准备→C三seed→T三seed→独立核验。训练对照仍沿9.7。[TASK](task9.10/TASK.md) · [PROCEDURE](task9.10/PROCEDURE.md) · [RESULTS](task9.10/RESULTS.md)。[SRC-1382](../../SOURCES.md#src-1382)。


2026-11-03 · task9.11 严格成功与效率下一轮规划 **review，待正式派发**。依赖9.7–9.10及9.10独立核验，Codex父；.1 sol证据审计→父单变量B1-L方案→.2另一sol独立审查→父核验。只读/文档交付，不改实现、不加载模型、不启动仿真/回放/训练。唯一训练提案为同期B1对B1-L、两seed各3M；本方案细化接替9.7未来执行入口，不重复启动两批；补证/预算/停止/独立任务测试与派工见子协议。[TASK](task9.11/TASK.md) · [PROCEDURE](task9.11/PROCEDURE.md) · [RESULTS](task9.11/RESULTS.md)。[SRC-1385–1391入口](../../SOURCES.md#src-1385)。推荐GPT6.1sol/high、Sonnet5.5/high，因跨模块因果/预算审查；实际父模型/强度未知，本轮只委派sol。

2026-11-05：用户授权BioIK探索归task9，新增task9.12；负责人待task9执行者接手，依赖既有IK/首次拒绝证据，独立于9.11在跑条件。按接口核对→隔离接线→小规模配对→task9验收推进。[TASK](task9.12/TASK.md) · [PROCEDURE](task9.12/PROCEDURE.md) · [RESULTS](task9.12/RESULTS.md)。[授权](../../SOURCES.md#src-task9-bioik-20261105)。

2026-11-06 当前并行探索派发：task9.12（BioIK子Agent）与task9.13（RLlib子Agent）互不依赖，先各自接口/成本校准，再分别冻结策略闭环及同预算学习对照。父task9协调资源和共享文档、核结论；不与9.11共写冻结源码/产物/测试集。各层恰三文档，继续委派先建立下级三文档及边界。
- task9.12：[TASK](task9.12/TASK.md) / [PROCEDURE](task9.12/PROCEDURE.md) / [RESULTS](task9.12/RESULTS.md)。
- task9.13：[TASK](task9.13/TASK.md) / [PROCEDURE](task9.13/PROCEDURE.md) / [RESULTS](task9.13/RESULTS.md)。
依据[SRC-T9-EXPLORE-20261106](../../SOURCES.md#src-t9-explore-20261106)，Codex GPT6.1sol/high、Claude Sonnet5.5/high；本次只规划，未实际派发或执行。

2026-11-06T09:39:41+08:00 · 当前实际执行派发：task9.12 A `/root/bioik_task9_12`、task9.13 B `/root/rllib_task9_13`，请求GPT6.1sol/high，各自按现有三文档输入/交付/验收执行。父Codex负责共享台账、资源与最终原件核验；子Agent不写共享文件。启动前复查GPU1/2 UUID/占用，CPU最多8线程/支，现役任务保留。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨接口/训练语义核查；实际派发结果记[执行日志](../../agent_logs/task9/20261106-codex-bioik-rllib-execution.md)。
