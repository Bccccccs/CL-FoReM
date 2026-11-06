# task9 — 下层SAC长程对照（原语后端primitive-obb-v1）

状态：**review（2026-11-02：全部训练结束，子任务结果/独立验收分别记录，未自动冻结新下层）**。依据用户2026-10-28“批准，我们task8的最终目的就是完成地图的迁移，然后task9再开始启动训练哈”（[SRC-1313](../../SOURCES.md#src-1313)）。承接[task8](../task8/TASK.md)完成的地图迁移；协议原样移自已superseded的[task8.12](../task8/task8.12/TASK.md)（[SRC-1312](../../SOURCES.md#src-1312)），后者替代已作废的[task8.9.3](../task8/task8.9/task8.9.3/TASK.md)（[SRC-1220](../../SOURCES.md#src-1220)）。

## 研究问题（沿用8.9）

task7下层SAC约1.2–1.5M转移后退化（v5：500k 54/100→3M 5/100，Q均值+15→−415，[SRC-1101](../../SOURCES.md#src-1101)）。问题：换到task8环境（JSON原语几何＋ghost-v1传感器）后是否仍退化？更新/数据比、温度规则与学习率日程（RLlib对齐）能否消除？假设H0–H3及H4（只记录不改）与8.9.3 TASK“研究问题与假设”相同。不预设任何一组必然有效。

## 与8.9.3协议的差异

|项|8.9.3|本任务|理由|
|---|---|---|---|
|几何后端|pcd-voxel-v3|**primitive-obb-v1**（`config/task8/lower_train_B{0,3}_prim.json`显式指定，代码缺省仍v3）|用户“优化好整体地图再训练”（SRC-1220）；8.10验收P为JSON真值；8.11实测P 256环境初始化53.4s、干跑吞吐约为V3的2.0–2.5×|
|场景缓存|依赖8.9.1.2 V3缓存|不需要（P直接从JSON构建）|8.11 I门P无缓存在deadline内|
|检查点合同|不含原语文件|含`primitive_scene.py`/`primitive_assets.py`（[task8.13](../task8/task8.13/RESULTS.md)）|M1|
|其余|—|**不变**：sync_v5、cbl_continue、观测/动作/奖励/终止、网络、batch256、replay100k、γ0.99、τ0.001、目标熵−3、warmup1000、256环境、cube-pool-v2训练/验证＋24语义图迁移、B0/B3定义、评估/诊断/预注册判定/停止规则|只换环境几何，避免混入其他变量|

P与V3几何存在可测差异（8.10 D门：|Δ|>0.05m射线17.3%；8.11 R门：route/连通域拒绝略增、witness拒绝略减），本任务结果不得与V3结果混合比较；与task7的比较仅作背景。

## 子任务与分期

|子任务|内容|授权|
|---|---|---|
|[task9.1](task9.1/TASK.md)|smoke：B0、B3各primary至512转移→保存→真实恢复至1000→完整196评估；实测更新/评估/保存/恢复耗时与显存，推导长训成本|**已批准**（SRC-1313），上限4300s|
|[task9.2](task9.2/TASK.md)|长训：B0、B3各种子4718/4719×3M转移，GPU0–3各1 run，每250k评估，预注册判定|**已批准**（SRC-1316）；首个250k按实测重算，>48h者STOP报告|
|[task9.3](task9.3/TASK.md)|B0退化机制诊断与阶段2设计|S1–S3/V4已交付；后续授权见SRC-1322/1323/1326|
|[task9.4](task9.4/TASK.md)|阶段2及3个B3-5M；H已用户提前停止，余2个5M运行|已批准SRC-1322/1323/1326；H停止SRC-1344|
|[task9.5](task9.5/TASK.md)|完整参数盘点、三方向SAC优化与论文呈现建议；独立实施/审查/有界排队|用户授权父设计后派子Agent执行，固定任务语义、周一上班前结束（SRC-1336）|

## 预注册判定与停止规则（工程选择，沿用8.9.3）

- 退化：最后3次验证（2.5M/2.75M/3M）严格成功均值 ≤ 该run峰值−15个百分点；消除退化：该组2种子均不退化；值函数发散作为机制证据。结论按组内全部种子报告。
- 停止：非有限损失/Q立即停；|Q|max超过500k时10倍停并保存，记“发散停止”。

## 交付与验收

smoke见[task9.1 TASK](task9.1/TASK.md)；长训按预注册判定报告，独立验收≠执行者。

## 模型与强度（推荐）

|阶段|Codex|Claude|理由|
|---|---|---|---|
|父协调/成本推导|GPT6.1sol / medium|Sonnet5.5 / medium|调度、账本、成本推导需核对多处|
|smoke准备与执行|GPT6.1sol / medium（执行可gpt-6.1-terra / low）|Sonnet5.5 / high（准备）、low（执行）|wrapper改编涉及恢复/预算合同；执行判据固定|
|smoke独立验收、长训判定|GPT6.1sol / high|Sonnet5.5 / high|恢复/评估/预算跨模块核对|
|长训执行|GPT6.1sol / medium（Codex额度2026-11-02 15:08恢复后）|Sonnet5.5 / medium|长任务监控|

2026-11-02：新增[task9.6语义复评](task9.6/TASK.md)，用户要求现在启动、下午看结果；仅既有B3三5M final与24×4固定语义回合，不训练。[SRC-1354](../../SOURCES.md#src-1354)。

2026-11-02 14:14：[task9.6](task9.6/RESULTS.md) done，12:06三B3-5M语义复评完成、父逐case核验PASS，132/288=45.83%，与原成败全部一致；[SRC-1355](../../SOURCES.md#src-1355)。不替代9.4全批独立验收。

2026-11-02 · task9.7 依赖既有 task9.4–9.6 证据，负责人待派发；按失败核查→配对比较→对照草案顺序，仅验收文档，尚未执行。[TASK](task9.7/TASK.md) · [PROCEDURE](task9.7/PROCEDURE.md) · [RESULTS](task9.7/RESULTS.md)。

2026-11-03 · task9.10 下层能力/效率路线与单次动作机制对照，review（设计）。依赖9.8/9.9证据，监督Codex；准备→C三seed→T三seed→独立核验。训练对照仍沿9.7。[TASK](task9.10/TASK.md) · [PROCEDURE](task9.10/PROCEDURE.md) · [RESULTS](task9.10/RESULTS.md)。[SRC-1382](../../SOURCES.md#src-1382)。


2026-11-03 · task9.11 严格成功与效率下一轮规划 **review，待正式派发**。依赖9.7–9.10及9.10独立核验，Codex父；.1 sol证据审计→父单变量B1-L方案→.2另一sol独立审查→父核验。只读/文档交付，不改实现、不加载模型、不启动仿真/回放/训练。唯一训练提案为同期B1对B1-L、两seed各3M；本方案细化接替9.7未来执行入口，不重复启动两批；补证/预算/停止/独立任务测试与派工见子协议。[TASK](task9.11/TASK.md) · [PROCEDURE](task9.11/PROCEDURE.md) · [RESULTS](task9.11/RESULTS.md)。[SRC-1385–1391入口](../../SOURCES.md#src-1385)。推荐GPT6.1sol/high、Sonnet5.5/high，因跨模块因果/预算审查；实际父模型/强度未知，本轮只委派sol。

2026-11-06：用户授权隔离测试BioIK与完整Ray RLlib SAC，沿task9.12及新task9.13分别开展，不改变在跑9.11。计划/工程数值见[SRC-T9-EXPLORE-20261106](../../SOURCES.md#src-t9-explore-20261106)及两任务三文档；当前尚未执行。

2026-11-06T10:02:40+08:00 当前两支探索已实际执行（active），不再仅规划。task9.12固定3历史权重逐seed100/96与两IK后端对照；task9.13实际完整RLlib SAC Algorithm与同期C、两seed各3M，用户确认每run开发100/96周期及终点评估。父Codex管理共享台账/资源/原件核验，两子Agent实际GPT6.1sol/high，推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high（接口/恢复/因果核查）。当前A后台正式评估、B必要恢复smoke推进；未宣称严格成功改善或训练完成。[来源](../../SOURCES.md#src-t9-exec-20261106)。
