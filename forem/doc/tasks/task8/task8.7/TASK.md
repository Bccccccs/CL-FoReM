# task8.7 — PCD体素化格点边界修复（pcd-voxel-v2）

状态：**closed（被task8.8的pcd-voxel-v3取代，v2历史FAIL保留）**。2026-10-26按用户条件在v3全门通过后关闭：[SRC-1081](../../../SOURCES.md#src-1081)、[SRC-1087](../../../SOURCES.md#src-1087)、[SRC-1089](../../../SOURCES.md#src-1089)。原结果与产物不删不改判。

## 用户要求与授权

2026-10-26用户：审查后由Claude只写文档，派发Codex实施；Codex可再派子Agent——需要高推理的编码交Sol，简单固定步骤交Luna，最后由Sol验收。本节点只授权修复[SRC-0999](../../../SOURCES.md#src-0999)指出的PCD→体素索引缺陷及其必要测试/复验，**不包括**：任何网络训练或含SAC/optimizer更新的测试、下层SAC长程对照、ghost/velodyne豁免改动、语义策略输入、批量性能优化、改mapgen/archive/task7文件、改奖励/动作/终止/IK/地图表示。

## 问题（已核事实）

mapgen `_voxelize_box`在box最小角起按`k·0.05m`取格点（`mapgen/map_builder.py` L17–43），点恰落在世界体素边界；PCD以float32十进制写出。`VoxelScene.from_asset`严格`floor((p-origin)/h)`（`forem/src/task8_sim/scene.py`），相邻格点随舍入落入同一体素：24图每图丢失约2.4–5.8万个完全在实体内的体素（26–40%），墙体出现周期性全高贯穿缝，4.6–8.0%随机扫描射线深入墙后>0.3m。8.1/8.2夹具在体素中心采样、8.5复核用同一floor规则，因此未暴露。复算与运行记录占据数逐图一致（office_map_000=81692），即问题存在于t8-exec-20261026实际运行几何。

## 目标与研究问题

让PCD体素占据忠实代表mapgen格点样本所表示的实体：墙体不漏、射线不穿墙，同时保持PCD权威、不用JSON盒体修补、不改其他环境语义。问题：索引容差能否在不引入可见膨胀的前提下消除边界舍入空洞？假设：样本表示`[p, p+h)`单元，浮点误差≤1e-5索引单位，`+1e-3`索引容差（5e-5m）足够且远小于体素。对照：同一PCD的v1（严格floor）与v2占据、真实`PcdPanorama`扫描，JSON盒体只作诊断参照。

## 协议变更（新版本，旧结果保留）

1. 索引：`idx = floor((p - origin)/h + ε)`，ε=1e-3（索引单位，等于5e-5m），float64计算；数据域校验仍对原始坐标做三轴半开检查，规则不变。
2. 上界：原始坐标合法但加ε后等于shape的点（仅可能在上界下5e-5m内）截到shape−1，逐图计数写provenance；不得静默丢点。
3. 版本：`map_backend=pcd-voxel-v2`、`environment_version=task8-pcd-v2`；provenance新增`index_epsilon`、`upper_clamped_count`；cache_key含版本，v1缓存/运行目录不复用。`ghost-v1`、profile、Grid/策略接口及其他全部合同不变。
4. v1产物（t8-exec-20261026）保留为历史，不覆盖、不改写结论；文档注明v1几何有空洞缺陷。

## 交付与验收

|门|内容|
|---|---|
|A RED→GREEN|新增mapgen式格点夹具：box最小角在网格上（如−4.8）与不在网格上（如−4.875）、经float32十进制往返写PCD；v1上可复现缺洞（RED原证据保留），v2：box完全内部的体素全部占据，垂直穿墙射线在0.5m高、多个x位置全部在墙面±h内命中；上界截断计数测试；原体素中心夹具结果不变|
|B 回归|`forem/src/task8_sim/tests`全部通过（CPU；GPU用例在授权GPU上串行）；不运行task7_lower或任何含optimizer更新的测试|
|C 24图几何|v1/v2逐图：占据数、hole/holeXY/spur/spurXY（独立JSON子采样参照）、真实PcdPanorama同位姿穿墙>0.3m射线比例；**墙类对象（JSON category=wall）v2内部体素必须全部占据**；非墙残差逐对象分类（旋转/半格偏移/裁剪/其他）并解释，不修补PCD|
|D 24图链路|v2下按8.5同规则重跑默认采样→一次非零动作→新扫描/Grid；状态分类同8.5，解析/几何错误、崩溃、缺记录阻断完成|
|E 版本与哈希|provenance/版本字段正确，v1缓存被拒；task7冻结157文件、48源地图、mapgen/archive零漂移|
|F 合规|无训练/无SAC更新；账本内完成；独立Sol high验收通过|

父task8在本节点验收前保持review；本节点通过不代表SAC问题解决或语义任务可行。

<a id="model-routing"></a>
## 模型、强度与分工（推荐，不等于实际配置）

按用户[SRC-0989](../../../SOURCES.md#src-0989)及本次要求：推理/编码用Sol，简单固定步骤用Luna，Luna交付必须由Sol检查原产物后验收，最后由独立Sol验收。

|阶段|Codex推荐|Claude备选|理由|
|---|---|---|---|
|父协调（派发、账本、文档汇总）|gpt-6.1-sol / medium|Sonnet5.5 / medium|跨文件证据核查与依赖调度|
|S1 修复实现＋测试|gpt-6.1-sol / high|Sonnet5.5 / high|浮点/边界几何推导，易出漏碰或膨胀|
|S2 固定命令执行（24图几何/链路清单、hash核对、表格汇总）|gpt-6-luna / low|Sonnet5.5 / low|输入输出与判据已固定，无判断权|
|S3 残差分类与S2复核|gpt-6.1-sol / medium|Sonnet5.5 / medium|需解释几何差异并核Luna原产物|
|S4 独立总验收（不同于S1实施者）|gpt-6.1-sol / high|Sonnet5.5 / high|几何正确性与合规终审|

Luna不得修改接口/参数/判据，不判断根因或放宽验收；遇问题交Sol。若平台不支持显式模型覆盖，如实记录，不冒称已按Luna/Sol执行。

2026-10-26关闭交接：v3独立A–F通过后按授权关闭本节点，历史v2失败事实保留，见[task8.8 RESULTS](../task8.8/RESULTS.md)与[SRC-1089](../../../SOURCES.md#src-1089)。关闭文档维护推荐Codex GPT6.1sol/Claude Sonnet5.5 low（常规状态更新无特殊推理需求），父实际gpt-6.1-sol/medium承担整体核验；独立验收实际Sol high。未启动新运行或新增功能。
