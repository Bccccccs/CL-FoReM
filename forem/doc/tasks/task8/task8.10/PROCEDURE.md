# task8.10 PROCEDURE — 原语场景后端实施与对照验收流程（规划）

状态：**已执行完毕（done，见[RESULTS](RESULTS.md)；r1/r2过程见§6–§8）**。原状态：已授权实施（[SRC-1220](../../../SOURCES.md#src-1220)），尚未执行；执行者与预算待用户确定。8.9已于2026-10-27作废关闭且无进程，下文§0.2的8.9 r2隔离条件解除：可直接在现有文件上做场景工厂接线（仍须最小改动并列diff），V3立方体臂可读取已发布并独立PASS的`forem/results/task8/t8-pool-20261027/cube-pool-v2/`。原状态：draft。本文所有命令、样本量、容差和预算均为规划建议，派发时须用户确认；未执行步骤不得写成结果。依据[TASK](TASK.md)、[SRC-1181](../../../SOURCES.md#src-1181)。

## 递归规则声明

本节点遵循根AGENTS项目级任务组织规则：每层恰有TASK/PROCEDURE/RESULTS三份文档；若执行时拆分子任务，子任务位于本目录内并继承编号（task8.10.1、task8.10.2…），各自建三文档，本PROCEDURE补列其编号、顺序、依赖、负责人和验收关系并链接；父结果汇总子结果，不能以父计划代替子任务实测。当前未拆分，S1–S4为本节点内角色。

## 0 开工前置条件（全部满足才可开始）

1. 用户明确授权实施，并确定执行预算（建议：沿8.8口径设单一墙钟账本，主调用计入；具体秒数由用户定）。
2. **8.9 r2隔离**：核实`TASK8.9-PHASE2-R2`状态及其进程。r2仍active时，不修改其会导入的任何文件（`forem/src/task7_sim/`、`forem/src/task8_sim/`现有文件、`forem/config/task8/`现有文件），不写其results/logs目录，不占用其GPU；新代码只写新文件，接线改动（第3步）在r2结束后或在独立worktree中进行。V3立方体对照只读取r2已完成并验收的cube-export-v2产物；未完成则立方体V3臂只用8.1夹具与自导出的对照副本（须标注来源，不冒充8.9产物）。
3. 登记PROGRESS、agent_logs/task8/task8.10/日志；记录根HEAD、forem-dev状态、GPU占用及开工保真快照（task7/task8生产文件、mapgen资产、8.9 r2产物目录的SHA256清单）。

## 1 文件归属（实施时）

|文件|内容|负责人|
|---|---|---|
|`forem/src/task8_sim/primitive_assets.py`（新）|JSON→原语读取、校验、语义图objects/parts展开核对、越域统计|S1|
|`forem/src/task8_sim/primitive_scene.py`（新）|`PrimitiveScene`/批量接口、解析查询、闭合SAT派生占据、PV诊断构造|S1|
|`forem/src/task8_sim/tests/test_primitive_*.py`（新）|单元/夹具/边界测试|S1|
|`forem/results/task8/t8-prim-<run>/reference/`（新）|独立参照R脚本与输出，不import生产几何函数|S2|
|`forem/config/task8/primitive_scene.json`（新）|后端版本、容差、样本量、种子|S1，父核|
|场景工厂接线（改现有episode/env调用点，最小改动）|按`map_backend`选择V3或P，默认V3|S1，仅在第0.2条允许后|
|`forem/scripts/task8_prim_verify.py`（新）|A–H门的固定执行入口|S1写，S3执行|

只复用task7/task8函数（import或注明来源的局部复制），不改其原文件语义；task7文件只读。

## 2 执行顺序与依赖

|步|角色|内容|依赖|
|---|---|---|---|
|1|S1|原语读取与A门实现；P查询与派生占据；PV诊断；单元测试RED→GREEN|0|
|2|S2（与1并行）|独立参照R：float64 OBB射线/contains/SAT/胶囊距离与3D闭合SAT体素化，自写不调用生产几何|0|
|3|S1|场景工厂接线、F门测试参数化|1，0.2|
|4|S3|按固定命令跑A–H全部诊断脚本，产出原始JSON/日志|1–3|
|5|S1/父|对4的失败分类；必要修复后回到4（保留失败原证据）|4|
|6|S4|独立验收A–H，查diff、原产物和必要复算|5|
|7|父|RESULTS汇总、PROGRESS/SOURCES更新、交接|6|

## 3 对照验收细则（规划值）

样本与种子固定写入`primitive_scene.json`；“边界构造样本”指针对每个盒的面/棱/角及其±1e-9 m外移点、贴面/掠射射线、恰接触的底盘与胶囊姿态。

**A 导入（硬门）**
- 范围：24语义图、8.1全部夹具（从其`fixture_boxes`读取，不读PCD）、立方体池全部JSON（10300）。
- 检查：有限、size>0、`|cos²+sin²−1|≤1e-6`、z≥0；语义图按mapgen源码的部件组合规则（执行者先定位并引用`mapgen/mapgen/`代码行）展开`objects/parts`，与`boxes`逐盒最大绝对差≤1e-9 m；原JSON/PCD字节hash前后一致；逐图越域原语数/最大越域量。
- 判定：任一解析错误、展开不一致或hash漂移即FAIL；越域只报告。

**B 解析正确性（P vs R，硬门）**
- 每图：≥1e5均匀随机点＋全部边界构造点做contains；≥20个随机合法位姿的完整360×90扫描＋掠射构造射线做raycast；≥1e4底盘位姿（含恰接触）；≥1e4机械臂胶囊姿态（含恰接触）。
- 判据（float64）：距离|Δ|≤1e-9 m；布尔分歧仅允许落在|带符号间隙|≤1e-9 m的边界带内，且须逐条列出；带外分歧数=0。
- float32（若下游实际用float32）：报告距离误差分布与命中/未命中分歧数，不作为硬门；分歧须分类。

**C 结构缺陷（P，硬门）**
- 派生占据满足`R(tol=−1e-9) ⊆ P ⊆ R(tol=+1e-9)`（2026-10-27用户批准，[SRC-1221](../../../SOURCES.md#src-1221)；原规划为“与R逐格相等”），并逐格列出P与R(tol=0)差异，须全部在该接触带内；完全位于闭合盒内的体素缺失数=0；每盒≥1个占据格（含薄盒）；占据⊆闭合盒supercover。
- 深墙射线：沿[SRC-1081](../../../SOURCES.md#src-1081)，解析墙内弦长≥0.05 m的合格射线，P命中距离与R入射距离一致（按B容差），漏检数=0。

**D 与V3差异（报告）**
- 同一组位姿与射线：P−V3距离差分布（分位数、|Δ|>0.05 m占比及位置分类：墙/非墙、边界层/内部）；底盘/机械臂碰撞分歧率；V3占据与P派生占据逐格差（多/少格按类别）；同扫描序列后的Grid差；同种子reset采样接受/拒绝差。
- 同样输出PV−V3、P−PV，用于把差异归因到“采样往返”还是“体素离散”。
- 不设门；凡超出1个体素层的差异须逐例解释。

**E 单一真值干预（硬门）**
- 至少3图×3种干预（平移某盒0.3 m、删除、新增）：P的扫描/碰撞/reset/Grid变化与R预测一致（按B容差）。
- 只改PCD（加/删点）、JSON不变：P全部输出逐位不变。V3同干预结果作对照记录。

**F 接口与链路（硬门）**
- `PrimitiveScene`/批量接口提供`raycast/contains/collide/occupancy/planning_height/provenance/select/replace`及pickle往返，签名与V3一致；后端选择只经配置，默认仍V3。
- task8现有测试中几何无关部分对P参数化运行通过；**禁止**运行task7_lower、任何含SAC/optimizer更新的测试（8.6越界教训，[SRC-0997](../../../SOURCES.md#src-0997)），执行者须先列出拟运行测试清单并由父核准。
- 真实链路：≥2语义图、≥2立方体图、8.1全部夹具，默认reset→非零动作→IK/碰撞/状态提交→新扫描/Grid；`sync_v5`与两种decision profile各做接口级回归；冻结actor仅做接口冒烟，不恢复旧环境/replay/optimizer。
- 信息边界：候选/推演对象不持有`PrimitiveScene`或JSON（沿task8.4检查方式）。

**G 性能（报告）**
- 同设备同输入：单图构建耗时；360×90扫描在批量{1,64,256}下的CUDA事件与墙钟延迟分布；碰撞批量延迟；显存峰值；P/PV/V3三臂对照。记录device/dtype、GPU编号，无CPU静默回退。
- 不设吞吐门；给出对8.9规划吞吐的影响估算作为信息项。

**H 保真隔离（硬门）**
- 收尾快照与开工快照比对：task7/task8现有生产文件、mapgen资产、8.9 r2产物/账本零漂移（第3步接线改动的文件单列，按diff审查）。
- 无训练、无optimizer更新、无后台遗留进程。

## 4 异常处理

- 解析/几何错误、R与P系统性不一致：停止该门，保留原证据，由S1/S2分别复核推导；不得以放宽容差通过。
- 发现语义图`objects/parts`与`boxes`不一致：停止，报告具体图/盒，请用户决定以哪一方为真值，不自行修资产。
- 8.9 r2需要的资源冲突：让出资源并暂停本任务，记录，不终止r2进程。
- 平台容量中断：记录为中断而非失败，原账本续用。

## 5 交接要求

RESULTS须含：实际模型/强度、命令与退出码、各门原始产物路径与hash、逐图表、失败与分类、账本、保真快照比对、未解决问题；交接按根AGENTS格式。

## 6 派发r1（2026-10-27，Claude子Agent临时执行）

用户2026-10-27选择：Codex额度恢复（11-02 15:08）前由临时Claude子Agent执行；验证墙钟账本上限**3600s**（含导入、A–H门诊断、性能对照与开发期测试命令，不含写代码时间）。[SRC-1220](../../../SOURCES.md#src-1220)

|角色|执行者（实际）|范围|写入|
|---|---|---|---|
|父|Claude claude-opus-5-5（强度未知）|协调、接口合同、复核、三文档/PROGRESS/SOURCES|共享文档|
|S1|Claude子Agent claude-sonnet-5-5 / high|P与PV、测试、配置、接线、`task8_prim_verify.py`|`src/task8_sim/primitive_*.py`、`tests/test_primitive_*.py`、`config/task8/primitive_scene.json`、`scripts/task8_prim_verify.py`、接线最小diff、`results/task8/t8-prim-20261027/s1/`|
|S2|Claude子Agent claude-sonnet-5-5 / high（≠S1）|独立参照R|`results/task8/t8-prim-20261027/reference/`|
|S3|待S1/S2完成后派发，Sonnet5.5 / low|固定执行A–H|run目录|
|S4|待S3后派发，Sonnet5.5 / high（≠S1/S2）|独立验收|验收报告|

**账本**：`forem/logs/task8/t8-prim-20261027/ledger-<角色>.jsonl`，每条命令一行`{role,cmd,start_utc,wall_s,rc,device}`；全部文件合计≤3600s。软份额S1≤700s、S2≤500s、S3≈2000s、S4≈400s；超份额先停并报父。GPU：S1用GPU0、S2用GPU1，用前查无compute进程。

**R接口合同**（父定，S1/S2并行据此对接；R只用numpy float64，不import torch/task7_sim/task8_sim）：盒体数组`[N,8]=[x,y,z,sx,sy,sz,cos,sin]`（最小角＋绕最小角yaw，闭合）。`contains(boxes,p)->bool[M]`；`signed_gap(boxes,p)->float[M]`（外正内负，取各盒最小）；`raycast(boxes,o,d,max_range)->float[M]`（无地面，未命中inf，原点在盒内0）；`ray_box_intervals(boxes,o,d)->(t_in[M,N],t_out[M,N])`（未相交inf/−inf）；`chassis_hits(boxes,base[K,3])->bool[K]`（x,y,yaw；底盘XY投影语义按task7/task8现行合同，接触即命中）；`capsule_distance(boxes,a[K,3],b[K,3],r[K])->float[K]`（≤0即命中）；`voxelize_closed_sat(boxes,origin,h,shape_zyx)->bool[Z,Y,X]`（与闭合OBB相交即占据，仅数据域内）。文件`results/task8/t8-prim-20261027/reference/reference.py`＋推导说明`reference/DERIVATION.md`＋自测`reference/selftest.json`。

S1与S2互不阅读对方代码，直到S3开始；分歧由B门暴露。子Agent只写自己的文件和日志（`doc/agent_logs/task8/task8.10/20261027-s1-impl.md`、`20261027-s2-reference.md`），不改PROGRESS/SOURCES/三文档，不提交git；父汇总。

## 7 r1续：C门修订与GPU顺序（2026-10-27）

用户批准C门接触带判据并要求“先跑CPU部分，GPU等空闲”（[SRC-1221](../../../SOURCES.md#src-1221)）。S1按修订判据改`task8_prim_verify.py` C门判定（带由R的`voxelize_closed_sat(tol=±1e-9)`给出，不用生产函数自定带）后，S3先执行A–E与F（`--device cpu`）；F的CUDA路径与G门待GPU0无其他compute进程时另派。H门基线按RESULTS“H门基线缺失”所述补救方案重建并注明。

## 8 r2：账本追加与S3续跑（2026-10-27）

用户“加大预算让他去做”，验证账本合计上限3600s→**7200s**（[SRC-1309](../../../SOURCES.md#src-1309)），判据/样本/配置不变。已用2560.4s，余4639.6s；软份额S3-r2≤3800s、S4≤600s、父备用≈240s。

S3-r2（Claude子Agent claude-sonnet-5-5 / medium，因含GPU核查与H基线重建）顺序执行，run目录`results/task8/t8-prim-20261027/s3-r2/`：
1. **单图计时先导**：B/C/D/F（CPU）各`--maps-limit 1`或`--maps-only <最慢类图>`一次，据`elapsed_s`外推全量；若外推合计超S3份额，停下报父，不缩样本。
2. **CPU全量**：B、C、D、F（float32 CPU），每mode `--mode-budget-s`按外推×1.3设定，中止后`--resume`补完。
3. **GPU**：每条命令前`nvidia-smi --query-compute-apps`确认目标GPU无其他compute进程；F CUDA路径与G门（批量1/64/256）在GPU0执行；被占则跳过并报告，不停他人进程。
4. **H门**：按RESULTS“H门基线缺失”补救方案重建基线后`--h-action compare`，结论注明重建基线。
5. 每步更新S3日志`agent_logs/task8/task8.10/20261027-s3-r2-run.md`；不改共享文档、不提交git。
