# task9.4 — 阶段2：B1/B2/第3种子＋T/H长训（原语后端）

状态：**active（2026-10-29用户“全部批准启动训练”，SRC-1322；G1–G3完成，G4长训于2026-10-30 08:21启动，SRC-1327）**。父[task9](../TASK.md)；设计依据[task9.3 S3](../../../../logs/task9/t9-b0diag-20261029/s3-report.md)及勘误`parent-errata.md`（[SRC-1320](../../../SOURCES.md#src-1320)、[SRC-1321](../../../SOURCES.md#src-1321)）。

## 目标

按task9.3设计，在primitive-obb-v1＋ghost-v1＋sync_v5上训练以下12个run（10个3M＋2个B3-5M），用预注册判据给出逐run、逐组结果，并为最终下层选配提供证据。

|组|相对B0（`config/task8/lower_train_B0_prim.json`）的唯一改动|地位|种子|
|---|---|---|---|
|B1|`update_every_transfers` 1→10（仍capped、α lr 1e-6、指数日程分母4,999,743）|预注册|4718、4719|
|B2|温度＋LR包，等于B3只把`update_every_transfers`改回1：`alpha_rule=rllib`、`alpha_lr_start=1e-4`、`lr_schedule=linear_transfers`|预注册|4718、4719|
|B0第3种子|只改seed|预注册补强|4720|
|B3第3种子|B3（`config/task8/lower_train_B3_prim.json`）只改seed|预注册补强|4720|
|T|只改温度包（`alpha_rule=rllib`、α初值1、α lr 1e-4按转移线性到1e-6、无冻结）；actor/critic仍按更新数指数日程；UTD 1。需新增独立`alpha_lr_schedule`|非预注册，已批准|4718、4719|
|B3-5M|B3只把`total_transfers`改为5,000,000（线性日程按5M），另报4.5M/4.75M/5M末3次（非预注册描述）|用户2026-10-29批准（SRC-1323）|4718、4719|
|B3-5M追加|同B3-5M，种子4720，配置`config/task9/stage2-extra/B3_5M_seed4720.json`|用户2026-10-30追加（SRC-1326）|4720|
|H|两个critic损失由MSE改为Huber δ=1（小误差0.5x²，大误差\|x\|−0.5），仍相加、单Adam、合并clip10；其余同B0。需新增`critic_loss`开关|非预注册，已批准|4718、4719|

其余条件全部不变：256环境、batch 256、回放100k、warmup动作1000、γ0.99、τ0.001、目标熵−3、clip10、网络、观测/动作/奖励/终止/mask、地图池与评估（每250k做100验证＋96迁移，迁移不选模）、诊断每1000转移、看门狗。

## 判据（沿task9预注册，SRC-1322解释）

- 退化P：最后3次验证（2.5M/2.75M/3M）严格成功均值≤该run峰值−0.15（等号计退化）。
- **发散停止计为退化**，同时如实记录“P字面不可判”。
- 组“消除退化”＝该组全部种子都不退化。所有种子都要报告；同时报告绝对成功率，“不退化”不代表性能合格。
- 停止：非有限值立即停；500k后|Q|max>10×500k参考时保存并停。

## 分阶段与门

|阶段|内容|门|
|---|---|---|
|G1 实现与测试|新增`alpha_lr_schedule`、`critic_loss`/`huber_delta`开关，默认值逐字保持旧行为；生成10份配置；单元/等价测试|旧B0/B3配置在新代码下，同状态同RNG的下一更新、下一动作、保存恢复与旧代码逐元素一致；T的LR公式、Huber数值/导数正确；任何失败即停报|
|G2 smoke|B1、B2、T、H各做task9.1式smoke（512→保存→恢复→1000→完整196评估），可4卡并行|各组S1–S6同9.1；实测耗时/显存，重算每run 3M外推≤48h|
|G3 并发探针（可选）|同一GPU并发2个短训练，比较总吞吐、显存、宿主内存|只有总吞吐提高且无时序/语义变化才采用2 run/卡，否则1 run/卡|
|G4 长训启动|按GPU队列启动10 run（宿主侧分离式队列），首条诊断后核查；250k按实测重算，>48h者STOP并报告|启动前核GPU/容器进程/显存/磁盘/宿主内存/代码与配置hash|

## 预算（工程选择）

G1中含GPU的测试≤1800s；G2每组≤4300s（同9.1），合计≤17200s worker；G3≤2400s；长训每run `--max-wall-s 172800`。新账本放`forem/logs/task9/t9-stage2-20261029/`。

## 不包括

改奖励/观测/动作/终止/mask/τ/采样/回放；为对齐RLlib而改target频率、log_std范围、回放放回方式（task9.3勘误列出的差异只记录）；缩步数或评估；重试失败run。

## 交付与验收

逐run、逐组按判据报告（Codex执行者写RESULTS执行者节）；长训结束后另派独立验收（≠执行者）。

## 模型与强度（推荐）

|角色|Codex|Claude|理由|
|---|---|---|---|
|G1实现与等价测试|GPT6.1sol / high|Sonnet5.5 / high|改训练合同，需逐元素等价|
|G2–G4执行与监控|GPT6.1sol / medium；固定巡检可gpt-6.1-terra / low（Sol复核）|Sonnet5.5 / medium|固定判据的执行与排队|
|独立验收与判定|GPT6.1sol / high（≠执行者）|Sonnet5.5 / high|跨run判定|
