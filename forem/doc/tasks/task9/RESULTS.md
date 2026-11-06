# task9 RESULTS — 原语后端下层SAC长程对照

状态：**review（2026-11-02：全部训练已退出；9.5六run完成3M，三5M全部完成，最终验收按子任务分别记录）**。依据[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)、[SRC-1351](../../SOURCES.md#src-1351)。

|子任务|状态|结果|
|---|---|---|
|9.1|done with conditions：B0/B3 512→恢复→1000＋196评估全部完成，账本1409.94/4300s；B0-preserve因检查脚本缺陷重做一次（SRC-1314）；成本推导B0≈21.3h、B3≈7.9h/run（不含训练中重置等未知项）|[RESULTS](task9.1/RESULTS.md)|
|9.2|done with conditions：B3×2到3M不退化（3M验证0.63/0.64）；B0×2看门狗发散停止（1.645M/2.463M）；L5独立验收通过（SRC-1317）|[RESULTS](task9.2/RESULTS.md)|
|9.3|done with conditions：S1–S3＋V4（SRC-1320/1321）；阶段2已批准（SRC-1322/1323/1326）|[RESULTS](task9.3/RESULTS.md)|
|9.4|review：13run已退出（6正常完成、5保护停止、2用户停H）；三5M最终67/63/64%，本批全13run最终独立验收仍待|[RESULTS](task9.4/RESULTS.md)|
|9.5|done：六run均3M且未触退化，三新方向未观察改善；独立执行/协议验收PASS（SRC-1352）|[RESULTS](task9.5/RESULTS.md)|

以下为历史快照，不代表当前运行：

2026-10-31最新状态以[task9.4本次复核](task9.4/RESULTS.md)和[SRC-1329](../../SOURCES.md#src-1329)为准：2正常完成、4发散停止、4运行、3等待；首个5M已到3.5M，最终独立验收未完成。

2026-10-31 20:43最新状态：[task9.4 RESULTS](task9.4/RESULTS.md)、[SRC-1332](../../SOURCES.md#src-1332)。首个5M正常完成，另外两个5M及H两路运行，已无等待run。

2026-11-02：新优化三方向/原5M完整结果见9.5第11节及SRC-1351；本轮未新开训练、不自动替换基线。状态汇总推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，跨协议独立验收high；实际父模型/强度未知。

2026-11-02：新增[task9.6语义复评](task9.6/RESULTS.md)，用户要求现在启动、下午看结果；仅既有B3三5M final与24×4固定语义回合，不训练。[SRC-1354](../../SOURCES.md#src-1354)。

2026-11-02 14:14：[task9.6](task9.6/RESULTS.md) done，12:06三B3-5M语义复评完成、父逐case核验PASS，132/288=45.83%，与原成败全部一致；[SRC-1355](../../SOURCES.md#src-1355)。不替代9.4全批独立验收。

2026-11-02 · task9.7 依赖既有 task9.4–9.6 证据，负责人待派发；按失败核查→配对比较→对照草案顺序，仅验收文档，尚未执行。[TASK](task9.7/TASK.md) · [PROCEDURE](task9.7/PROCEDURE.md) · [RESULTS](task9.7/RESULTS.md)。

2026-11-02 · [task9.8 诊断设计](task9.8/RESULTS.md) review，已交付派工协议，尚无回放结果。[SRC-1363](../../SOURCES.md#src-1363)

2026-11-02 · task9.8 C独立复核完成，回放数据通过，人工收尾例外保留。[裁决](task9.8/RESULTS.md) · [SRC-1377](../../SOURCES.md#src-1377)。

2026-11-02 · [task9.9离线机制分析](task9.9/RESULTS.md) **done**：独立读30原JSONL，对账无拒绝18/R1/N11/U0；12受阻案例8例原动作全同、4例变化，后续拒绝类别均未变；case05末五begin为选中原地零进展项、无实际动作，未选候选未知。建议下一项优先检验首次拒绝后的一次动作选择，仅草案待监督决定，未实施。完整两表/复算命令/证据与限制见子结果；[SRC-1379](../../SOURCES.md#src-1379) · [SRC-1380](../../SOURCES.md#src-1380) · [SRC-1381](../../SOURCES.md#src-1381)。推荐GPT6.1sol/high、Sonnet5.5/high，跨轨迹与源码因果核查；实际底层型号/强度未知。

2026-11-03 · task9.10 下层能力/效率路线与单次动作机制对照，review（设计）。依赖9.8/9.9证据，监督Codex；准备→C三seed→T三seed→独立核验。训练对照仍沿9.7。[TASK](task9.10/TASK.md) · [PROCEDURE](task9.10/PROCEDURE.md) · [RESULTS](task9.10/RESULTS.md)。[SRC-1382](../../SOURCES.md#src-1382)。

2026-11-03 task9.10 done，1176回合/独立PASS，R1→2但最终success与strict无改善，保留基线。详[9.10结果](task9.10/RESULTS.md)；task9.4原整批验收仍单独待办。


2026-11-03 · task9.11 严格成功与效率下一轮规划 **review，待正式派发**。依赖9.7–9.10及9.10独立核验，Codex父；.1 sol证据审计→父单变量B1-L方案→.2另一sol独立审查→父核验。只读/文档交付，不改实现、不加载模型、不启动仿真/回放/训练。唯一训练提案为同期B1对B1-L、两seed各3M；本方案细化接替9.7未来执行入口，不重复启动两批；补证/预算/停止/独立任务测试与派工见子协议。[TASK](task9.11/TASK.md) · [PROCEDURE](task9.11/PROCEDURE.md) · [RESULTS](task9.11/RESULTS.md)。[SRC-1385–1391入口](../../SOURCES.md#src-1385)。推荐GPT6.1sol/high、Sonnet5.5/high，因跨模块因果/预算审查；实际父模型/强度未知，本轮只委派sol。

2026-11-06：两条探索可派发三文档完成，BioIK任务9.12细化、新RLlib任务9.13建立；主变量隔离、资源/源码写入边界与成本核查已规定，尚未测试。见[SRC-T9-EXPLORE-20261106](../../SOURCES.md#src-t9-explore-20261106)。

2026-11-06T10:02:40+08:00 两支实际实施增量：A已真实BioIK隔离构建、32校准及两后端smoke并部署独立后台，正式current588正在运行，诊断与BioIK588待连续执行；父核32原件及首48现役行与历史同结果。B已锁Ray2.40.0完整原生Algorithm训练链、合成1000/75更新及下一update恢复，C真实1000/75和54字段环境合同已完成；具体queue遮蔽/Ray CUBLAS配置与非空pending问题正在定向修复/最终验证，尚无新的按计划正式训练结果。子任务[9.12 RESULTS](task9.12/RESULTS.md)、[9.13 RESULTS](task9.13/RESULTS.md)为配置/成本/身份/结果事实入口，父仅汇总新增事实，不替代原件。状态active，未结论胜负；推荐GPT6.1sol/high、Sonnet5.5/high，实际两子GPT6.1sol/high，父平台型号/强度未知。[来源](../../SOURCES.md#src-t9-exec-20261106)。

2026-11-06T10:18:37+08:00 · TASK9-EXPLORE-EXEC · Codex父/独立后台 **active**。A现役正式已296/588，32校准/32smoke与接口通过，诊断最多256及BioIK588按后台队列连续进行；B最终两臂真实1000/75、非空255(+R queued3)恢复下一更新差0、observer各4回合parity通过，10:15:13启动封存正式12M矩阵，首C4718实际21000消费/2075更新，profile含3M而非额外预算。GPU1/2分别独立，无收益/胜负结论，完整评估/250k成本尚待。A driver2522044/913872408；B queue2541557/914007182、首worker2541568/914007196；PID/CID/UUID/STOP/恢复及原件见[9.12 RESULTS](task9.12/RESULTS.md)、[9.13 RESULTS](task9.13/RESULTS.md)。父资源采集PID2541972/914011403只读运行。原失败/工程评估/未知成本保留，未使用9.11保留测试。[父日志](../../agent_logs/task9/20261106-codex-bioik-rllib-execution.md) · [来源](../../SOURCES.md#src-t9-exec-20261106)。
