# task8.9.2 — 结果与交接

**2026-10-27 已作废（closed）**：用户指令“现在的8.9作废吧，要优化好了整体的地图再开始训练”（[SRC-1220](../../../../SOURCES.md#src-1220)）。本节点不再执行；以下为作废前的历史状态与记录，原样保留。

状态：**blocked（2026-10-27 r2完成40批后安全停机，依赖A的P2/P5硬门决定；4013图部分产物，10300全量/200抽样/发布未完成）**。r1真实FAIL及账本保留如下。授权[SRC-1160](../../../../SOURCES.md#src-1160)/[SRC-1161](../../../../SOURCES.md#src-1161)，阶段A暂缓。负责人Codex；父显式派发gpt-6.1-sol/high，底层配置不可独立核实。推荐GPT6.1sol/Sonnet5.5 high审查旋转格覆盖/全占据/穿透，固定导出Terra low；推荐不等于实际Claude执行。

## r1交付状态（历史快照）

|门|结果|
|---|---|
|M1/M2|阶段A暂缓，未执行|
|M3|**FAIL先导**：24张导出用于测速，6张全内部审查全失败；未执行全量10300图和≥200抽样；无全量manifest/固定评估种子表|
|M4|本节点无训练/optimizer/mapgen/GPU使用，生产代码只读；新账本内，独立Sol已确认M3 FAIL，M4只核本轮执行边界|

失败摘要[blocked-summary.json](../../../../../results/task8/t8-pool-20261027/blocked-summary.json)，[6图先导](../../../../../results/task8/t8-pool-20261027/profile-audit.json)，[最小反例](../../../../../results/task8/t8-pool-20261027/internal-hole-counterexample.json)，独立日志[实施日志](../../../../agent_logs/task8/task8.9/task8.9.2/20261027-sol-pool.md)。来源已由父统一入账；完整草稿保留于日志，见[SRC-1120–1124](../../../../SOURCES.md#src-1120)。

## 源、实现与资源

源`results/task7/maps/a/20261021T021400Z/index.json` SHA256 `95976a0767b5bcb89a550c9602d68b60cbcd5813cad582433859c31bf6330109`；10300条：训练10000、验证100、测试200，各分sparse/standard。盒体`[x,y,z,sx,sy,sz,cos,sin]`为最小角局部坐标，不是中心。依据`task7_sim/mapgen_a.py`模块说明与`corners`、`geometry.to_box`；采样沿`task8_sim/fixtures.py::_sample`每轴ceil(size/.05)等间距中心，然后旋转平移。没有补洞/扩大地图/改变生产v3。[SRC-1121](../../../../SOURCES.md#src-1121)。

新增[导出脚本](../../../../../scripts/task8_build_pool.py)、[配置](../../../../../config/task8/pool_s3.json)。脚本冻结SHA256 `8f14949c6a3989863302e4730171c734d20effd53aa67470a587d8625296f2c0`。每图records保存PCD/JSONhash、源生成器版本、导出器hash、原split/difficulty/seed、点数/字节数/边界；侧车按源原字节复制。ASCII体积/点数/坐标读回只验证了24张先导，不能称全量验证。

forem-dev运行；cpu.max `max 100000`、cpuset/affinity `0-63`、Python64 CPU；OMP/OPENBLAS_NUM_THREADS=2导致nproc=2，不是硬限。4 worker各OMP/OpenBLAS/MKL=1，CPU float64；未使用GPU。剩余磁盘约18TiB、可用内存237GiB为开工快照。[SRC-1120](../../../../SOURCES.md#src-1120)。

## 命令、测速和预算

以下容器命令均经`sg docker -c 'docker exec forem-dev ...'`执行，项目挂载`/root/mm_husky_ws`；环境`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`。

- 合同测试：`python3 results/task8/t8-pool-20261027/test_export_contract.py`。RED缺脚本rc1；实现后GREEN rc0，90°最小角盒体8点位置断言通过。
- `python3 -u scripts/task8_build_pool.py --mode profile --budget-limit 120 --timeout 100`。第一次rc1/0.819061096s：内部读回跳过10行，实际header9行，导致丢首点；已修正，原临时PCD保留`failed-profile-header-skip/`。第二次rc0/1.825751014s，24图、2,546,383点、66,706,458B，13.145275459图/s。[profile-report](../../../../../results/task8/t8-pool-20261027/cube-pool/profile-report.json)。
- `timeout --signal=TERM --kill-after=5 60 python3 -u results/task8/t8-pool-20261027/profile_audit.py`。rc0/3.636233290s是**诊断运行完成**，报告6图passed均false，不能把rc0称几何通过。
- `python3 results/task8/t8-pool-20261027/inspect_hole.py`。rc0，提取保存反例；父要求停止后未新增几何运行，随后仅行政汇总/文档。

预算推导：10300 / 13.145275459 ≈783.55s；66,706,458/24×10300≈28.63GB（十进制）。父依实测批准1800s总预算，含既用、全量校验、≥200抽样和独立验收，不重置。此为先导外推工程估计，不是全量工期保证。[SRC-1122](../../../../SOURCES.md#src-1122)。

[账本](../../../../../logs/task8/t8-pool-20261027/budget.json)当前 **12.286453545094/1800s，余1787.713546454906s，active=null**。其中6.286453545094s为3次程序精确计时；合同RED/GREEN、反例提取各保守计1s，资源/源/产物读取与静态收尾保守计3s，共加6s。该附加项明确为上界记账而非伪造实测。全部失败保留，不继续消耗预算做已知失败的大规模导出。

## 先导几何原件

各图JSON为`cube-pool/audit/<id>.json`，逐盒分类和scene provenance完整保留。[SRC-1123](../../../../SOURCES.md#src-1123)。

|图|sampled内部缺格|exact全8角内部缺格|墙sampled/exact缺格|深墙射线/漏检|生产与独立占据|
|---|---:|---:|---|---|---|
|sparse_test_00000|1427|1427|0/0|5572/0|逐格相同|
|standard_test_00000|607|605|0/0|5572/0|逐格相同|
|sparse_train_00000|395|395|0/0|5572/0|逐格相同|
|standard_train_00000|1771|1748|0/0|5572/0|逐格相同|
|sparse_validation_00000|789|780|0/0|5572/0|逐格相同|
|standard_validation_00000|2348|2348|0/0|5572/0|逐格相同|
|合计|7337|7303|0/0|33432/0|6/6相同|

内部孔全部在非墙盒体：full_height/arm_band/base_only均出现。`box_masks`沿8.8每格5³子采样，`closed_box_masks`以8角区间包含核exact内部；深墙用`wall_depth`0.05m inset和`unbounded_voxel_depth`，不加6m量程/弦长预筛。只测试base=(0,0,0)的360×90方向，不能声称覆盖全部机器人姿态。

保存反例：sparse_train_00000 box4，缺格zyx=(0,14,22)，world最小(-3.9,-4.3,0)，最大(-3.85,-4.25,.05)。8角在原OBB闭合体内（z底面接触0），局部x范围0.066676122946–0.137204809156、y范围0.008680815131–0.079209501341；此world格中原局部中心采样点数0。原盒size=(.648266600739,.901246916804,.458810740508)。该证据说明真正exact-full格缺失，不能按部分外壳豁免；生产/独立相同说明不是两种v3占据实现差异。根因归纳为旋转局部中心格点不足以保证world体素覆盖，独立Sol尚待复核，不将归纳替代独立验收。

## 停止与交接

父收到先导失败后明确要求停止全量，不补200样本、不再做几何运行、不改采样规则；本节点遵守。24图PCD与records是诊断资产，**没有发布manifest.json或evaluation-seeds.json，不得供训练消费**。训练Agent已由父接收阻塞信息。全量hash/点数/边界及≥200门尚未完成，不能标done。[SRC-1124](../../../../SOURCES.md#src-1124)。

目标与授权：S3全量池、SRC1160；当前负责人本实施Sol交父。已完成：资源与源语义核查、24图测速、6图先导与反例、账本/失败保留。剩余：不同Sol high读取原件及最小复算；若确认合同冲突，父向用户报告并取得采样规则决定后再议继续。风险：现有局部中心规则与全部内部硬门冲突，任何偷偷补点/提高密度/改v3均越范围。无后台导出或训练；停止/恢复：当前无需停止进程，未来不得直接运行build，先解决合同与独立复核。未提交、推送、合并。

## 不同Sol独立复核与终账（父补记）

不同实施者的gpt-6.1-sol/high仅做一次CPU最小复算，确认离地严格内部格zyx=(1,14,22)缺占据；8角最小余隙8.680815mm，所有PCD点在含面容差的扩展格候选数0、生产v3占据False。最小角解析/旋转公式、fixture等价与PCD解析/持久精度核对通过，因此M3真实FAIL，不能豁免为外壳或解析错误。详[独立报告](../../../../../results/task8/t8-phase2-20261027/independent-review.md)、[SRC-1125](../../../../SOURCES.md#src-1125)。独立仅复算一格，6图孔总数仍是实施原件统计。

原账本含复核及行政终额**18.968597744592/1800s**，余1781.031402255408s、active=null；上文12.286453545094为实施停机快照保留，不能重置。未全量/未200图抽样/未发布正式manifest或种子表，等待用户采样规则决定，整体blocked。

## r2 cube-export-v2实施先导（旧记录保留）

按SRC-1161继续，实际派发Sol/high；推荐Codex GPT6.1sol/high与Claude Sonnet5.5/high（闭合格几何与生产加载多环节核查）。新配置`pool_s3_v2.json`，新池`cube-pool-v2/`；旧24图/r1失败不动。本轮无训练/optimizer/mapgen/GPU，生产v3、语义池、task7只读。[SRC-1126](../../../../SOURCES.md#src-1126)来源草稿已交父登记。

导出器冻结SHA256 `a6055e44be7fd5ffb846596ef2971839c5849f8130960b37537f5dda582bebb7`。合同回归先RED缺target实现，再RED发现float64精确格面比较不能表示数学格面；按16ε×最大坐标界限纠正后GREEN，r1严格内部反例/薄盒/格面样本三项通过。此为≤1.78e-14m的数值表示纠正，逐盒写明余量与最大残差，不引入生产5e-5m面容差扩张O。

实际命令（forem-dev、CUDA_VISIBLE_DEVICES空、PYTHONDONTWRITEBYTECODE=1、OMP/OpenBLAS/MKL=1）：`python3 -B -u scripts/task8_build_pool.py --mode pilot --budget-limit 1800 --timeout 100`，rc0。每split/difficulty首图共6图；真实严格PCD解析、真实生产VoxelScene CPUfloat64=O，六图①–⑤均通过，exact全内部洞0、每盒O越自身supercover0、每盒≥1、33432深墙射线漏0。独立SAT仍沿1e-10m数值slack。每图audit与record位于新池。[SRC-1127](../../../../SOURCES.md#src-1127)草稿交父；全量/独立尚未通过。

先导6图合计600683点、11442562B；导出及全量门①④⑥3.447354611941s（1.740464987图/s，含worker冷导入）、几何审查3.736034994014s、账本总计7.189561844803s。另合同/资源保守记3s，账本现**29.158159589395/1800s**、active=null。仅按六图线性推导全10300导出约5918s、200审查约125s、约19.64GB；含冷导入的小先导外推保守且不稳定，父要求Terra先24图测速再定全量预算。24中6已缓存，只有18张新导出，不能用24/时长冒充新图吞吐。

固定24图清单已放[r2日志](../../../../agent_logs/task8/task8.9/task8.9.2/20261027-sol-pool-r2.md)，交父派Terra。当前无后台进程/全量导出、无manifest/种子表，M3尚未完成，不能供训练消费。正式路径已通知C。来源、共享PROGRESS和父三文档仍由父维护。

## r2二次交接：24图与5400s预算（全量尚未执行）

Terra实际gpt-6.1-terra/low，24图profile rc0、wall6.722011715173721s（账本6.726704303175211s）。6缓存＋18新增，新增率**2.6777698050374217图/s**；24图2480445点/47156941B。实施Sol/high逐一读24真实PCD及全部源/侧车hash、逐点有限/半开边界、header/点数/极值、身份及保存生产=O/逐盒非空记录，全过；7.435084942728281s已追加原账本，原件`r2-profile-sol-review.json`。[SRC-1128](../../../../SOURCES.md#src-1128)草稿见r2日志，父统一入账。

不同Sol/high已独立重建6图88盒longdouble目标=生产CPU64、逐盒supercover0/非空，先导独立PASS见[SRC-1138](../../../../SOURCES.md#src-1138)。此不等于全量完成。

父依据18新增速率批准**累计5400s**：剩10276图线性约3837.5s，200审查约124.5s，hash/独立预留300s及约20%波动余量；条件外推非保证，实际不足即停报告。旧r1全部失败/费用保留，当前**50.67397289350629/5400s，余5349.326027106494s，active=null**。5400是导出预算选择，不增地图数/实验组/科学范围。

固定清单[pool_s3_v2_batch.json](../../../../../config/task8/pool_s3_v2_batch.json)，105job=103×build100(offset0..10200)→audit200→finalize；SHA429b626b35a21493ab77054643c1e29dcec32791b302d9ba8bdf11522ac77715。脚本/配置hash不变，4 worker单线程CPU。Terra按argv严格顺序执行、余量不足700/660/420或任何失败即停，保留有效图resume身份验证，不重新导出。详细命令、账本/监控/恢复与判据见[r2日志](../../../../agent_logs/task8/task8.9/task8.9.2/20261027-sol-pool-r2.md)。[SRC-1129](../../../../SOURCES.md#src-1129)是待执行清单草稿，不能写结果已通过。

当前24图、新manifest/评估表仍不存在；全量/200/最终不同Sol验收均待办，无本Sol后台任务。本次只交清单，待父派Terra，M3/M4整体未完成。


## r2当前部分产物与安全停止（最终交接，覆盖早前快照）

父因A的P2/P5硬门partial要求停止新任务并等待Claude决定补证据/预算或smoke前置顺序。本节点状态**blocked**，不是B几何先导再次失败；独立六图PASS(SRC1138)仍有效。Terra实际gpt-6.1-terra/low，安全等offset3900当前块rc0后退出wrapper2554024与exporter2554333，未再启动offset4000。`fixed-full-r2.json` status=blocked、jobs40、next_job_index40；逐块日志`fixed-full-r2-logs/000-build.log`至`039-build.log`与执行表计数/冻结hash/rc0已由Sol纯读核一致。

现有**4013**张PCD/sidecars/records：原索引前4000ID完整＋批外13张先导/profile；原索引顺序包含测试/验证，不能把40批误称4000训练图。实际分布和产物总量如下，来源[SRC-1130](../../../../SOURCES.md#src-1130)草稿由父登记。

|划分|图数|点数|PCD字节数|
|---|---:|---:|---:|
|训练|3855|374965652|7135881416|
|验证|54|5342583|101687405|
|测试|104|10111791|192505830|
|合计|4013|390420026|7430074651|

难度分布：train sparse3851/standard4，validation sparse50/standard4，test sparse100/standard4。这是执行到当前原索引位置的部分资产分布，不是新训练池划分。尚有**6287张**未导出。未跑200图审查和finalize；`manifest.json`、`evaluation-seeds.json`、`audit-report.json`、`final-report.json`均不存在，不能供训练消费，不能写全量①④⑥/200①–⑤完成。语义池与task7/生产v3未改。

Sol实施者实际gpt-6.1-sol/high，获父明确同意后仅一次≤110s纯原件读回：全部4013核PCD/源JSON/侧车hash、实际PCD行数/header点数、原ID/split/difficulty/seed、保存record有限边界/极值、导出器/配置hash、production_target_equal真/每盒target非空（保存最小16格）；固定12张新图逐点重新核实际有限/半开边界/极值通过。**其余4001张本轮没有重新逐点解析**，仅核保存极值及导出时真实strict parser/生产scene的通过记录；未重新运行任何target、scene、SAT、DDA、几何、测试或导出。不能把保存生产标志的复核称本轮重新生成/几何验收。报告[r2-partial-originals-review.json](../../../../../results/task8/t8-pool-20261027/r2-partial-originals-review.json)，纯读脚本同目录同名.py。12张具体ID、批外13ID和全部统计在报告中。

本次rc0、**16.873170921579s**实测加入原B账本，停机前1111.4041973212734s变为**1128.2773682428524/5400s**，余**4271.722631757148s**、active=null、status=blocked_A_gate_decision；r1/r2全部失败与费用保留。只读前现场forem-dev仅init/sleep/本次ps，无wrapper/exporter写进程；本次进程已正常退出，无后台任务。推荐GPT6.1sol/Sonnet5.5 high核验依赖/几何，固定续导出Terra low；推荐不等于实际Claude执行。

交接：目标仍SRC1160/1161全部10300图＋200抽样，不变科学语义/上限；当前负责人Sol交父，证据如上。剩余为6287导出、200审查、最终hash/发布/种子表及不同Sol终验。风险为部分池比例偏斜、未发布不准消费，A门未决使父整体NOT_READY，smoke未执行。下一步必须先有Claude/父对A门及恢复的明确决定，再从**固定plan job40 / build --offset4000 --count100**在原账本继续；前40块与现有4013有效图不重复生成，块外13图后续按原身份hash resume。不得擅自启动旧wrapper从job0重跑、不加预算、不降低门。未提交/推送/合并。

### 2026-10-27 r3 固定续导（待独立终验）

Terra实际 gpt-6.1-terra / low，推荐不同Codex GPT6.1sol / high、Claude Sonnet5.5 / high复核全量身份和发布原件。按父转达授权从job40续导；job40–102 build均通过，audit200报告passed、failed空、exact洞/深墙漏/盒外点均0；生产finalize rc0、final-report passed/count10300（train10000/validation100/test200），records/maps/sidecars各10300，1082925316点、20599609701字节。续导包装器后审错误地寻找不存在的 `finalize-report.json`，生产实际写 `final-report.json`，故r3执行表stopped；保留错误，未重试。原账本3087.1794338710606/5400秒、active空，后续独立验收可能另计。原件、哈希、PID、证据及SRC-1195草稿见[Terra r3日志](../../../../agent_logs/task8/task8.9/task8.9.2/20261027-terra-r3-full.md)。独立Sol终验尚未完成，池不得供smoke消费。


## r3父验收覆盖（阶段B done）

阶段B全10300图、200图①–⑤审查、manifest与evaluation-seeds已发布并经不同Sol独立验收PASS；阶段A继续暂缓，不将阶段B完成当作阶段A统计完成。[执行SRC-1195](../../../../SOURCES.md#src-1195)、[独立SRC-1198](../../../../SOURCES.md#src-1198)。原包装器finalize-report.json误读导致stopped保留；生产finalize rc0真实final-report通过，独立核验后消费门通过，未重复发布。B账本3132.918237945065/5400s、active空。

独立审查全部10300真实PCD字节hash/header/实际行数/源侧车身份及保存边界证据；额外12图实际逐点边界、200保存几何审查逐门及100验证+200测试+96迁移种子复算通过；不是全量重做逐点/几何射线。证据见[独立报告](../../../../../results/task8/t8-phase2-20261027/r3-independent-pool-final.md)。实际固定Terra/low、独立Sol/high，推荐GPT6.1sol/Sonnet5.5 high验收（几何、身份与协议核查），普通固定步骤Terra low。后续不再导出或改池。
