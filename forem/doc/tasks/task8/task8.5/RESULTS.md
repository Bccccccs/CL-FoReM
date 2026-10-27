# task8.5 — 结果与交接

状态：**done（2026-10-26本节点本次24图诊断由Sol及父核查通过；独立总验收待8.6）**。实际Sol gpt-6.1-sol/medium、Luna gpt-6-luna/low，推荐GPT6.1sol/Sonnet5.5 medium作合同/验收、Luna/Sonnet5.5 low固定执行；证据[SRC-0992](../../../SOURCES.md#src-0992)、[SRC-0996](../../../SOURCES.md#src-0996)。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

以下“尚未执行”模板为规划阶段历史，后续实际结果按run追加于下方；不沿用task7旧成绩作验收。

## 执行记录模板（每run追加，保留历史）

- run-id/开始结束：尚未执行。
- 目标/授权与输入：见[TASK](TASK.md)；依赖导入依8.1；环境逐图验证依8.4；可先做独立离线部分。
- 负责人：资产迁移Agent待派发；实际模型/推理强度：未知。
- 修改文件/版本/hash：尚无；限定TASK列出的文件。
- 实际命令/容器/设备/退出码、日志/产物：尚无。
- 验收项与结果：尚未验证，见[TASK](TASK.md)及[PROCEDURE](PROCEDURE.md)。
- 共享预算消耗/余额、全局墙钟/累计worker：尚未执行，向父领取余额。
- 问题/风险/证据来源：未实施；沿父任务限制，不假定PCD迁移或SAC已通过。
- 下一步：收到执行派发后先核依赖与范围；提交父复核，不自行将父状态标done。

## t8-exec-20261026 — Sol离线合同与实现（active）

负责人Codex，实际gpt-6.1-sol / medium；固定导入由父另派Luna low执行，Sol复核原产物。推荐Codex GPT6.1sol medium、Claude Sonnet5.5 medium，理由为协议/几何差异判断；固定命令推荐GPT6 Luna low。授权与方法沿[SRC-0987](../../../SOURCES.md#src-0987)、[SRC-0989](../../../SOURCES.md#src-0989)、[SRC-0990](../../../SOURCES.md#src-0990)，新增实测事实待父登记SOURCES。

已实现：`forem/src/task8_sim/import_mapgen.py`、`forem/scripts/task8_import_maps.py`、`forem/src/task8_sim/tests/test_mapgen_import.py`、`forem/config/task8/semantic_pool.json`。源PCD/JSON字节保留；严格复用8.1 load_asset核实际点数/有限/半开边界/hash；index schema不变、split smoke、difficulty使用源文件类别而非标定难度。每图格式状态及点/box差异写diagnostics；1e-6m仅诊断舍入容差，不影响PCD/体素/边界。objects只做明确primitive与box候选对应，复合或不明对象unknown、多候选ambiguous，不造点级语义。

测试先红后绿：共享账本owner8.5，RED `37d614326d` rc1/0.514844s（7项缺模块失败），GREEN `d650173dcd` rc0/0.414801s（7 passed）；CPU only、无GPU/训练/后台进程。完整命令、原始日志位置、范围与协议见[独立日志](../../../agent_logs/task8/task8.5/20261026-sol-import.md)。累计0.929645s/离线100s配额。父共享账本记录其他Agent并发使用，不能把本配额当新预算。

当前交接：CLI与固定75s导入命令已交父；等待Luna执行24对导入并由Sol核hash/报告，尚无正式semantic-pool结果。默认采样与逐图扫描/step依8.4及父放行，尚未运行。7单元测试不等于24图格式/几何或全链路验收，不标done。

## t8-exec-20261026 — Luna导入与Sol离线原证据验收（review）

实际执行GPT6 Luna / low，Sol验收gpt-6.1-sol / medium。Luna固定命令账本`27181bf341`，rc0/44.725895s；随后Sol独立脚本账本`ea1b1fa271`，rc0/3.018337s，CPU numpy float64。核验脚本、实际完整命令及证据路径见[独立日志](../../../agent_logs/task8/task8.5/20261026-sol-import.md#sol离线原产物审查2026-10-26)。

[import-sol-review.json](../../../../results/task8/t8-exec-20261026/import-sol-review.json)逐图保存PCD/sidecar hash、点数、差异及四实现文件SHA。Sol独立重读全部PCD数据行，24图3,193,408点，实际行数、POINTS与diagnostics一致，有限性/三轴半开边界通过。48份导入文件逐字节等于source，SHA同时等于旧map-assets-audit、index与diagnostics；完整JSON及未知语义字段保留。24 ID齐全，smoke/原类别difficulty/semantic_policy_input=false均核对。

[diagnostics.json](../../../../results/task8/t8-exec-20261026/semantic-pool/diagnostics.json)记录严格闭OBB未包含388,268点，1e-6m诊断容差未包含0点。该容差是工程诊断选择，仅展示严格边界判定敏感性，不作为几何等价、重建精度或根因结论；序列化/旋转/历史生成过滤/裁剪均只是待核机制。全部box解释无程序错误，PCD没有被修补。对象映射与空box等逐图诊断保留；unknown/ambiguous不猜测。

离线累计48.673877s（Sol3.947982s、Luna44.725895s），无GPU/训练/后台进程。新增实测主张已交父登记来源，沿[SRC-0987](../../../SOURCES.md#src-0987)范围。离线资产保真/格式门通过，**24图实际几何query门与运行门仍尚未执行**；后续必须逐图记录geometry查询及有界默认采样，至少一张真实语义图完成非零step。等待8.4接口与父放行，不标本任务done。

## 逐图诊断脚本准备（尚未执行）

父派Sol medium准备[run_maps.py](../../../../logs/task8/t8-exec-20261026/run_maps.py)与[固定命令清单](../../../../logs/task8/t8-exec-20261026/map-diagnostic-commands.json)。建议执行Luna low固定清单、Sol medium分类/验收；Claude备选Sonnet5.5同档，理由沿模型分工。当前未获8.4/cube全链路放行，不执行清单。

先24geometry再24runtime，单进程单图独立超时、阶段原子落盘；默认sampler未简化、不使用factory。geometry用原PCD独立floor参照、正距离入域ray期待/实际、占据/域外contains及底盘投影碰撞，避免只记nohit；runtime记录sampling拒绝、真实初/末FK、原Grid候选、非零动作attempt/commit/碰撞、新scan/Grid和完整provenance/hash/device/timing。每图仅少量query回归，不证明所有几何。

只有sample未接受而超时才reset_timeout；sample后reset/scan/query/step阶段超时记stage_timeout，异常记error，不伪装采样限制或自然truncated。24runtime每图账本30s合计≤720s，geometry计必要额外共享开销且仍受余额约束，GPU0串行须父另行放行。脚本仅语法检查`167279012f` rc0/0.164421s，无语义图执行，详情见[日志](../../../agent_logs/task8/task8.5/20261026-sol-import.md)。geometry/runtime门均仍not_run；准备脚本不是验收完成。

最终脚本语法复验`465c847cd3` rc0/0.164383s；本轮准备验证共0.328804s，无semantic执行。

## 逐图累计30s预算修订（执行前，尚未运行）

父核查后修正前节“geometry额外＋runtime每图30s”及旧48命令：**有效合同为每图geometry+runtime所有尝试的实际父账本elapsed累计≤30s**，含启动开销、错误/超时/重验，不重领预算；离线导入/box差异诊断仍单独计全局1800s。没有改变默认采样分布或科学合同。

[geometry固定清单](../../../../logs/task8/t8-exec-20261026/map-geometry-commands.json)含24条待父放行命令，账本owner=`8.5-geometry-<map_id>`，单次≤10s；[总清单](../../../../logs/task8/t8-exec-20261026/map-diagnostic-commands.json)的runtime argv全部置null并标需重算，旧无条件30s runtime命令失效，当前不可执行。

24geometry后Sol逐图关联精确账本id、rc、实际elapsed（所有geometry/runtime尝试/重验）和stage，remaining=30−累计实际耗时。几何门未通过/超时/缺记录仍阻止完成，不当采样限制。Sol审完24几何后才生成新runtime剩余额度命令，owner=`8.5-runtime-<map_id>`；账本limit=remaining−0.25s guard、容器limit−0.5s、脚本limit−1s，limit≤1s不运行并记预算耗尽/incomplete。新runtime清单需父批准后才交Luna固定执行。此轮未运行semantic query/采样/GPU，无新增验证计算；任务仍review。

## 24图geometry门原证据复核与运行命令READY（尚未运行runtime）

Luna按父放行的24条固定几何命令执行，Sol gpt-6.1-sol medium直接核原记录及不同目的复验。审查`e905636917` rc0/1.666582s、CPU only，重读原PCD/sidecar核hash并独立floor推占据与正距离ray期待，匹配24几何JSON实际query、版本、provenance及逐map精确账本id/argv/rc，无重复scene query。原命令见[日志](../../../agent_logs/task8/task8.5/20261026-sol-import.md)，[geometry-sol-review.json](../../../../results/task8/t8-exec-20261026/geometry-sol-review.json)记录24个reviewed_pass、实际点数3,193,408及逐图期待/实际；查询样本有限，不是穷尽几何正确性证明。24geometry父账本实际总计67.483677s。

[map-budget.json](../../../../results/task8/t8-exec-20261026/map-budget.json)逐图保存精确geometry账本id/owner/rc/elapsed及runtime owner/id槽。本轮保守扣离线导入逐图实际处理＋完整wrapper摊分，再扣离线Sol review与本几何review全命令实际耗时等额摊分；加全部geometry/runtime已执行命令（含失败/超时/重验），合计每图≤30s。remaining=24.352274–25.677165s；runtime账本limit=remaining−0.25s、容器limit−0.5s、脚本limit−1s，24runtime上限合计597.105509s。局部保守摊分不重复增加全局账本用时。

[新runtime固定清单](../../../../logs/task8/t8-exec-20261026/map-runtime-commands.json)READY待父审核，24条owner=`8.5-runtime-<mapid>`，Luna串行GPU0；旧总清单runtime argv仍null，避免误用。**本轮未运行runtime/default sample/scan/step**。父批准后Luna执行，Sol负责原证据与失败分类；任何重验继续计累计并须重算额度。几何门通过不等于地图任务可行或task8.5全部完成。新主张和证据已交父统一SOURCES登记。

## 24图默认采样与非零动作原证据验收（READY待8.6独立复核）

实际固定执行GPT6 Luna low；本节点Sol验收gpt-6.1-sol medium。推荐Codex GPT6.1sol medium、Claude Sonnet5.5 medium：逐图因果、时序、预算与产物一致性判断。未改冻结生产代码/运行脚本，未重复24runtime；独立8.6 high另行验收，本节点不自判父阶段done。

CPU原产物审查`afa3d68003` rc0/2.167054s（限额25s内）；[map-summary.json](../../../../results/task8/t8-exec-20261026/map-summary.json)含逐图状态、精确geometry/runtime账本id、hash与采样/FK/scan/Grid；[map-budget.json](../../../../results/task8/t8-exec-20261026/map-budget.json)保留原计划maps，追加actuals，本次复核全部实际耗时均分摊入各图。命令和完整证据见[日志](../../../agent_logs/task8/task8.5/20261026-sol-import.md)。

24图全部step_checked：默认sampler无factory，原分布/CBL_Q/witness64未改，每图接受1个episode并执行固定非零raw=[0,0,0.5]；均attempted=2/committed=2，实际base/q改变。CPU由实际base/q重算初末FK最大矩阵分量差1.1920929e-7（float32跨设备工程容差3e-6，平移分量单位m/旋转无量纲，不是控制精度阈值）。scene版本/hash、完整源sidecar字节、实际cuda:0/float32及逐attempt candidate_q→actual q全部核对。

48扫描/Grid NPZ核对通过；各图自动sensor_frames从1到2、automatic_render_count=1、Grid timestamp从0到0.1s，观测掩码保留并产生新depth。next NPZ为额外诊断renderer输出，Grid来自Core自动更新，不将额外诊断render计入自动帧。内部proposal拒绝原样保留；24均无reset_rejected/reset_timeout/error，不声称内部零拒绝。

24runtime账本实际165.619751s；每图累计加入离线导入/审查保守分摊、geometry/runtime和本轮Sol完整复核分摊后仍≤30s。下表累计采用此保守口径；精确id和余额见机读预算。

|map-id|状态|proposals（拒绝数）|attempt/commit|有效深度 初→后|runtime账本s|保守累计s|
|---|---|---:|---:|---:|---:|---:|
|home_map_000|step_checked|5（4）|2/2|24125→24145|6.974|12.097|
|home_map_001|step_checked|12（11）|2/2|24678→24691|7.274|12.452|
|home_map_002|step_checked|5（4）|2/2|24011→23993|6.874|12.050|
|hospital_map_000|step_checked|5（4）|2/2|26262→26153|7.074|12.812|
|hospital_map_001|step_checked|12（11）|2/2|23848→23899|6.974|11.990|
|hospital_map_002|step_checked|12（11）|2/2|23759→23633|6.723|11.411|
|laboratory_map_000|step_checked|9（8）|2/2|23857→23804|7.024|11.855|
|laboratory_map_001|step_checked|12（11）|2/2|23705→23753|6.773|11.352|
|laboratory_map_002|step_checked|3（2）|2/2|23415→23360|6.573|11.145|
|library_map_000|step_checked|5（4）|2/2|26117→26085|7.124|12.397|
|library_map_001|step_checked|2（1）|2/2|25624→25628|7.024|12.125|
|library_map_002|step_checked|5（4）|2/2|21644→21633|7.124|12.546|
|office_map_000|step_checked|5（4）|2/2|28656→28610|6.974|11.775|
|office_map_001|step_checked|3（2）|2/2|26304→26289|6.723|11.440|
|office_map_002|step_checked|5（4）|2/2|27287→27155|6.523|10.936|
|restaurant_map_000|step_checked|12（11）|2/2|22099→22131|7.124|12.025|
|restaurant_map_001|step_checked|5（4）|2/2|24169→24212|6.974|11.730|
|restaurant_map_002|step_checked|5（4）|2/2|22407→22394|7.074|11.872|
|warehouse_map_000|step_checked|9（8）|2/2|26061→26032|6.473|11.320|
|warehouse_map_001|step_checked|5（4）|2/2|24480→24265|6.773|12.030|
|warehouse_map_002|step_checked|3（2）|2/2|26154→26131|6.723|11.942|
|workshop_map_000|step_checked|3（2）|2/2|22202→22155|6.824|11.887|
|workshop_map_001|step_checked|15（14）|2/2|22588→22510|7.124|11.973|
|workshop_map_002|step_checked|3（2）|2/2|23515→23546|6.774|11.518|

限定结论：24图在本次seed=20261026默认采样与一次固定非零动作诊断中均可运行，all_maps_runnable_this_diagnostic=true；不是全任务到达性、跨种子成功率、SAC表现或WM效果证据。几何query样本有限。新增实测/工程容差主张已交父统一SOURCES登记；等待独立8.6复核。

正式逐图诊断入口为`forem/scripts/task8_map_diagnostics.py`，与本run已执行logs/run_maps.py原字节/hash相同，历史原件保留供证据复核；不增加功能，按AGENTS源码/入口归位。当前24图诊断不代表所有任务可达，完整限制见[SRC-0996](../../../SOURCES.md#src-0996)。
