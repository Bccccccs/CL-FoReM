# task8.9.2 — 地图池划分

状态：**blocked（2026-10-27 r2在40批后安全停止，依赖A的P2/P5硬门决定；现有4013图，10300全量与200抽样未完成）**。旧blocked/r1失败快照在下文保留。阶段A语义统计暂缓，授权[SRC-1160](../../../../SOURCES.md#src-1160)、[SRC-1161](../../../../SOURCES.md#src-1161)，实测见[RESULTS](RESULTS.md)。父[task8.9](../TASK.md)；依据[SRC-1102](../../../../SOURCES.md#src-1102)。

## 目标

为下层SAC第二阶段确定训练/验证/测试地图池：先对24张语义图做逐图可行性与难度统计，再给出候选划分方案与推荐，**由用户决定**采用哪种；获批后（阶段B）构建对应池的manifest。

## 已知事实（输入）

- 语义池：24张mapgen图，8类场景（home、hospital、laboratory、library、office、restaurant、warehouse、workshop）×3，当前全部`split=smoke`、`difficulty`为场景类别而非标定难度（`forem/results/task8/t8-exec-20261026/semantic-pool/index.json`）；v3几何已验收（[SRC-1100](../../../../SOURCES.md#src-1100)），24图采样拒绝数逐图记录在task8.8 r4表。
- task7训练池：mapgen_a随机立方体图10,300张——train 5000 sparse＋5000 standard、validation 50＋50、test 100＋100（`forem/config/task7/mapgen_a.json`、`forem/results/task7/maps/a/20261021T021400Z/index.json`）；v3–v5的退化均在此分布上观察到。
- 24张图相对1万张训练图多样性大幅下降，过拟合与评估方差风险高；用户已说明需要重新生成地图时可以找他（[SRC-1021](../../../../SOURCES.md#src-1021)）。

## 阶段A（统计与方案，执行时不需另批）

1. **逐图统计**（v3后端、固定种子、只读）：可通行面积比例、房间/门数与对象类别计数（来自sidecar）、固定K=200个提案种子下的采样接受率与拒绝原因分布、路线长度与“路线/直线”比、跨门路线比例、witness通过率。
2. **候选划分方案**：
   - **S1 类内留出**：每类2张训练、1张测试（固定规则，如`*_002`为测试），训练图上另取固定episode种子作验证 → 16/8图。检验同类新布局泛化。
   - **S2 留类**：6类训练、2类整体留作测试 → 检验跨场景类型泛化；需说明留出类别的选择规则与理由。
   - **S3 立方体训练＋语义迁移评估**：训练/验证沿用task7 mapgen_a同分布（按v3协议导出为PCD），24张语义图只作迁移测试。与v5历史可比，最适合8.9.3的机制诊断。
   - 对每种方案给训练图数、episode多样性估计、泄漏风险、与v5可比性、评估方差（每图episode数×图数）。
3. **推荐**：给出Claude/Sol的推荐及理由，并列出需用户决定的事项（方案选择；是否请用户用mapgen补生成更多语义图及每类数量）。

## 阶段B（构建所选池，需用户选定方案后执行）

按选定方案生成manifest（split/difficulty/hash/来源/v3后端），S3需把mapgen_a的JSON盒体按task8.1夹具规则（体素中心采样）确定性导出为PCD并核对hash；固定验证/测试episode种子表；验证不得读取测试图。不改源地图与mapgen。

## 不包括

训练或SAC更新；改v3几何/采样/奖励/终止；调用mapgen生成新图（如需由用户执行）；以测试集结果调参。

## 交付与验收

|门|内容|
|---|---|
|M1|24图逐图统计表（机读JSON＋md），种子与命令可复现|
|M2|S1–S3方案对比表与推荐，待决定事项清单|
|M3（阶段B）|所选池manifest、hash、episode种子表；立方体PCD导出的抽样几何复核（墙/内部全占据门沿task8.8）|
|M4|无训练、账本内；独立Sol验收|

## 预算（工程选择）

阶段A验证累计≤900s；阶段B另计，立方体PCD全量导出以CPU为主，预算在阶段B派发时按实测速率定。

## 模型与强度（推荐）

|阶段|Codex|Claude备选|理由|
|---|---|---|---|
|父协调|gpt-6.1-sol / medium|Sonnet5.5 / medium|调度与账本|
|统计规则与方案分析|gpt-6.1-sol / medium|Sonnet5.5 / medium|分布、泄漏与方差判断|
|固定统计/导出执行|gpt-6-luna / low|Sonnet5.5 / low|判据固定|
|独立验收|gpt-6.1-sol / high（≠实施者）|Sonnet5.5 / high|终审|

## 2026-10-27用户决定（SRC-1160）

采用**S3**：mapgen_a全部10,000训练＋100验证＋200测试图按v3协议导出PCD（task8.1夹具“体素中心采样”规则，确定性、记录生成器hash与源JSON hash），manifest保留原split/difficulty/seed；24张语义图作迁移评估集（每图4个固定种子）。阶段A暂缓。阶段B验收：抽样≥200张导出图按task8.8口径复核墙类/全部内部全占据与穿透深度门；全量逐图hash/点数/边界有效性；导出预算按实测速率由父决定并记账，CPU并行进程数需核容器资源。ASCII PCD约4MB/图、总计约40GB，放`forem/results/task8/<run-id>/cube-pool/`，不入Git；如需派生缓存（如压缩占据），必须以PCD hash＋v3版本为键并与生产scene逐格核等。

## 阶段B实施状态（2026-10-27）

实施者父显式派发gpt-6.1-sol/high；复杂几何门推荐GPT6.1sol/Sonnet5.5 high，固定导出low，理由是必须区分角点语义、采样格与world体素的覆盖关系。只导出24张先导图，未发布全量manifest/评估种子表，未开始10300图全量导出。6图生产v3与独立占据完全相同，但内部sampled/exact缺格7337/7303，墙缺格与深墙漏检均0；已知不合格池不得交训练。父已批准1800s总预算，当前保守累计12.286453545s，剩1787.713546455s，active空。不得将剩余预算视为修改采样规则授权。[SRC-1122](../../../../SOURCES.md#src-1122)、[SRC-1123](../../../../SOURCES.md#src-1123)、[SRC-1124](../../../../SOURCES.md#src-1124)。

## 2026-10-27 导出规则修订（SRC-1161）

先导因旋转局部格点混叠FAIL后，Claude按用户授权改用`cube-export-v2`：目标占据=中心落在闭合盒内的世界体素∪含局部格点样本的世界体素，PCD写这些体素的世界中心；验收按SRC-1161①–⑥（替代原先导口径）。旧先导24图为诊断资产保留，不供训练。

实施/几何审查推荐GPT6.1sol/high、Claude Sonnet5.5/high（闭合OBB离散与生产等价）；固定命令导出按[SRC-1162](../../../../SOURCES.md#src-1162)推荐gpt-6.1-terra/low。实际r2实施由父派gpt-6.1-sol/high；Terra与独立Sol实际配置须后续记录。


r2二次交接时：不同Sol/high六图独立PASS(SRC1138)，Terra24图profile与实施Sol原件复核通过；父据新率批准累计5400s，原r1账本/失败保留。全量10300＋200审查＋最终独立验收仍尚未执行，见RESULTS及固定清单；不扩大科学规模。


## r2当前停止边界（覆盖早前执行状态）

因父协调A的P2/P5硬门partial，需要Claude决定补证据/预算或smoke顺序，B按父指令停止。Terra安全完成offset3900后退出，40个100图批次rc0；现4013图（前4000原索引ID＋批外13张先导/profile），不是全量10300通过。独立六图PASS保留，200审查/finalize/正式manifest/evaluation-seeds未执行或发布，部分池禁止训练消费。[SRC-1130](../../../../SOURCES.md#src-1130)草稿交父登记，原件与费用见RESULTS。当前不允许新导出/几何/测试；仅已完成原件收尾。

后续须父协调Claude决定并明确恢复，再从固定清单next_job_index40/offset4000与原B账本继续，现有有效图按身份hash resume，不重复生成；不重置r1/r2失败与费用、不自动加预算。推荐GPT6.1sol/high、Sonnet5.5/high判断依赖/验收；固定续导出Terra/low，实际角色由续接日志记录。

2026-10-27 r3状态：固定续导执行至生产finalize rc0，但包装器后审文件名错误而stopped；独立Sol终验待完成，验收前不得消费。细节和原件见[RESULTS](RESULTS.md)。推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high核对全量原件和发布合同；Terra实际执行low，不把推荐当实际配置。


## r3父验收覆盖（阶段B done）

阶段B全10300图、200图①–⑤审查、manifest与evaluation-seeds已发布并经不同Sol独立验收PASS；阶段A继续暂缓，不将阶段B完成当作阶段A统计完成。[执行SRC-1195](../../../../SOURCES.md#src-1195)、[独立SRC-1198](../../../../SOURCES.md#src-1198)。原包装器finalize-report.json误读导致stopped保留；生产finalize rc0真实final-report通过，独立核验后消费门通过，未重复发布。B账本3132.918237945065/5400s、active空。

独立审查全部10300真实PCD字节hash/header/实际行数/源侧车身份及保存边界证据；额外12图实际逐点边界、200保存几何审查逐门及100验证+200测试+96迁移种子复算通过；不是全量重做逐点/几何射线。证据见[独立报告](../../../../../results/task8/t8-phase2-20261027/r3-independent-pool-final.md)。实际固定Terra/low、独立Sol/high，推荐GPT6.1sol/Sonnet5.5 high验收（几何、身份与协议核查），普通固定步骤Terra low。后续不再导出或改池。
