# task9 PROCEDURE — 原语后端下层SAC长程对照

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
