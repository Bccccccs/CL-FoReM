# task8.8 — 执行流程

状态：**done（r4独立S4 A–F全部PASS；C/D各24图通过、0失败；历史失败保留）**。证据[SRC-1087](../../../SOURCES.md#src-1087)、[父收尾SRC-1089](../../../SOURCES.md#src-1089)及[RESULTS](RESULTS.md)。非墙残差限制保留；不代表SAC问题解决或下一阶段授权。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；当前不再拆分子任务，S1–S4为同一节点内串行阶段（沿task8.7做法），各阶段在本RESULTS和独立日志登记负责人与实际模型/强度。若确需拆分，子目录继承`task8.8.N`，先建三文档并登记顺序、依赖、负责人、模型/强度与验收关系；编号稳定不复用。代码/配置/日志/产物分别归`forem/src`、`config`、`logs/task8`、`results/task8`。

## 输入、文件归属与资源

- run-id：`t8-voxv3-20261026`（按实际开工日期记录）。产物`forem/results/task8/<run-id>/`，账本`forem/logs/task8/<run-id>/budget.json`，Agent日志`forem/doc/agent_logs/task8/task8.8/YYYYMMDD-agent-topic.md`。
- 起点：当前工作树中task8.7的v2代码（`forem/results/task8/t8-voxfix-20261026/s1-changes.diff`），开工先记录task8_sim/config/scripts各文件hash。
- 独占写：`forem/src/task8_sim/scene.py`、`tests/test_scene_lattice.py`（扩展）、旧oracle所在测试（仅按v3协议更新）、版本相关行（config/task8、task8脚本、assets/env/import等，仅版本常量与校验）。其他改动先列清单与原因。
- 只读：task7、mapgen、archive、t8-exec-20261026与t8-voxfix-20261026产物。源24图取`forem/results/task8/t8-exec-20261026/source/`，开工核hash。
- 可复用：task8.7的`forem/scripts/task8_voxel_diagnostics.py`与commands格式，改为v2/v3对比；Claude参照`forem/results/task8/t8-review-claude-20261026/closed_face.py`只作交叉核对，S1/S3/S4须自写独立参照。
- 预算：新账本累计≤900s（含失败/超时），单图几何+链路≤30s，单命令timeout取余额与子上限较小值；CPU优先，GPU仅核实无compute进程的一块卡串行。已运行`forem-dev`，不建/停容器或他人进程。
- SOURCES：本节点使用预留**SRC-1022–SRC-1039**。

## 阶段与顺序

1. **父开工**：读根AGENTS、forem/ENV.md、doc/README、PROGRESS、task8父三文档、task8.7与本节点三文档、SRC-0999/1004/1006/1020/1021；核git、容器/GPU、源hash；登记PROGRESS与日志；建账本。
2. **S1（Sol high）**：先写A门夹具并在v2上运行保存RED；实现v3归属（TASK协议2–4）；跑A、B门；保存diff、前后hash、原日志。
3. **父放行**：读diff与测试原输出；S3（Sol）写固定24图清单（v2/v3几何指标、同位姿PcdPanorama穿墙数、v3链路），参数/位姿规则写死。
4. **S2（Luna low）**：串行执行清单，任一命令非零立即停并上报，不解释结果。
5. **S3（Sol medium）**：核Luna原产物与账本；判C/D；非墙残差与spur逐对象分类。若C硬门不过：判断是否属于“必须改PCD资产才能解决”，是则停并写明请用户决定重新生成；否则退回S1，不放宽门。
6. **S4（独立Sol high，≠S1）**：亲读diff/测试/原产物，自写参照抽样复验，逐门PASS/FAIL，含合规与尺寸不变断言。
7. **父收尾**：汇总本RESULTS与父task8子结果行，登记SOURCES，更新PROGRESS；task8.7若本节点通过则标closed（被v3取代）由父记录。不提交、不推送。

## 异常处理

- 需要重新生成地图：停止，在RESULTS与last message明确“需要用户重新生成”，附原因与证据；不调用mapgen。
- 任何改动触及域/分辨率/栅格尺寸或奖励/动作/终止/IK/Grid/策略接口：停止报告。
- 测试只运行`forem/src/task8_sim/tests`及明确node；禁止`task7_lower`及任何optimizer/SAC更新测试（[SRC-0997](../../../SOURCES.md#src-0997)）。
- 超预算写incomplete，不续预算。子Agent只写本节点文件与日志；PROGRESS/SOURCES/父文档由父维护。

## 验证命令（规划，尚未执行）

```bash
# forem-dev内，工作目录/root/mm_husky_ws
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests
```

24图命令由S3写入`forem/logs/task8/<run-id>/commands.json`后执行。

## 派发prompt（Claude→Codex父协调，可直接复制）

```text
你是FoReM task8.8的执行协调者（Codex，推荐gpt-6.1-sol / medium）。工作区/home/ybc/projects/CL-FoReM。用户2026-10-26决定：PCD体素化改用“闭合面归属”规则（pcd-voxel-v3），整体训练地图大小必须与原来一致；如需重新生成地图要停下来喊用户。Claude只写文档并派发你；你可再派子Agent——高推理编码交gpt-6.1-sol，简单固定步骤交gpt-6-luna，最后由与实现者不同的gpt-6.1-sol验收。

先读：AGENTS.md、forem/ENV.md、forem/doc/README.md、forem/doc/PROGRESS.md、forem/doc/tasks/task8/{TASK,PROCEDURE,RESULTS}.md、forem/doc/tasks/task8/task8.7/{TASK,PROCEDURE,RESULTS}.md、forem/doc/tasks/task8/task8.8/{TASK,PROCEDURE,RESULTS}.md，以及forem/doc/SOURCES.md中SRC-0997、0999、1004、1006、1020、1021。

任务：在task8.7的v2代码基础上，把forem/src/task8_sim/scene.py的PCD→体素归属改为TASK“协议（v3）”：每轴|f−round(f)|<1e-3索引单位时归属两侧体素（候选笛卡尔积），否则floor；域外候选丢弃计数、不丢点；数据域/h/origin/shape(32,200,200)、Grid200²、局部128²、74/75维观测全部不变；版本pcd-voxel-v3/task8-pcd-v3，provenance与cache_key更新；v1/v2产物保留。按PROCEDURE阶段S1（Sol high：RED→GREEN）→S2（Luna low执行Sol写好的24图固定清单）→S3（Sol medium复核原产物、分类残差与外扩）→S4（独立Sol high总验收）。验收门A–F见TASK；硬门：24/24图墙类内部缺格=0且墙类合格射线穿墙>0.3m计数=0，24图v3链路按8.5规则完成。JSON只作诊断参照，不能补PCD。

边界：不训练，不运行task7_lower或任何含optimizer/SAC更新的测试；不改task7、mapgen、archive、v1/v2产物，不调用mapgen重新生成（需要时停下报告“需要用户重新生成”）；不改奖励/动作/终止/IK/Grid/策略接口、ghost或velodyne豁免，不做性能优化或语义输入。新账本forem/logs/task8/<run-id>/budget.json累计≤900s、单图≤30s，CPU优先，GPU仅核实无compute进程的一块并串行；用已运行forem-dev，不建/停容器或他人进程。SOURCES只用预留SRC-1022–1039。子Agent只写本节点文件与日志；PROGRESS/SOURCES/父文档由你维护。显式选择gpt-6.1-sol/gpt-6-luna并在RESULTS登记实际模型/强度。不提交、不推送、不合并。

完成时：本节点RESULTS逐门PASS/FAIL与证据、RED/GREEN原输出、v2/v3逐图表（含外扩spur）、残差分类、账本、实际模型/强度；更新父task8 RESULTS与PROGRESS；last message给简短中文总结（各门结果、关键数字、是否需要用户重新生成地图、待用户决定事项）。遇到需要用户决定的问题停下报告，不自行扩展范围。
```

## r2续跑派发prompt（2026-10-26，Claude→Codex父协调）

```text
你是FoReM task8.8 r2的执行协调者（Codex，推荐gpt-6.1-sol / medium）。工作区/home/ybc/projects/CL-FoReM。这是task8.8的续跑：r1已实现pcd-voxel-v3（闭合面归属），首图home_map_000墙内部缺格0，但按原墙射线硬门FAIL（16/12890条），并因archive两条漂移使E门FAIL。Claude复核（SRC-1040）认定这16条射线墙内弦长0.0014–0.0395m<0.05m、从1.6m墙顶穿出，是亚体素擦边，不需重新生成地图；archive漂移来自用户并发rsync上传（已结束）。用户2026-10-26批准（SRC-1041）：①墙射线门只计解析墙内弦长≥0.05m的合格射线，其穿墙>0.3m计数须为0，弦长<0.05m擦边射线逐图单列报告（数量、弦长、入墙z、所属墙），不计失败；②重建mapgen/archive保真基线后比对，r1漂移记录保留；③续跑。

先读：AGENTS.md、forem/ENV.md、forem/doc/PROGRESS.md、forem/doc/tasks/task8/task8.8/{TASK,PROCEDURE,RESULTS}.md（含r1全部记录与Claude复核）、forem/doc/SOURCES.md中SRC-1021、1025–1027、1040、1041，以及forem/doc/agent_logs/task8/task8.8/下r1日志。

任务（沿用r1 run-id t8-voxv3-20261026与同一账本forem/logs/task8/t8-voxv3-20261026/budget.json，余约728s，不重置、不自行加预算）：
1. 父：核当前代码hash与r1 S1交付一致（v3不改）；确认无rsync/他人写入后重建mapgen/archive基线（新文件，不覆盖r1基线）；登记r2于RESULTS与日志。
2. 先按修订门复判首图（用r1已保存原产物重算弦长分类，不重跑生成），再继续：S3（Sol）把修订门写入固定清单 → S2（Luna low）串行执行余23图C几何＋D链路（单图≤30s，任一非零立即停并上报）→ S3（Sol medium）亲读原产物复核、分类非墙残差/spur/擦边。
3. 补B门GPU回归：仅在核实无compute进程的一块GPU上串行运行forem/src/task8_sim/tests。
4. S4：与r1 S1不同的独立gpt-6.1-sol / high总验收，逐门A–F PASS/FAIL（C按修订门）。
5. 父收尾：RESULTS按r2追加、父task8 RESULTS子结果行、PROGRESS、SOURCES（只用预留SRC-1042–1059）。

边界：不训练，不运行task7_lower或任何含optimizer/SAC更新的测试；不改v3归属/τ/域/分辨率/接口，不改task7、mapgen、archive、v1/v2产物，不调用mapgen；不改奖励/动作/终止/IK/Grid/策略、ghost或velodyne豁免；不做性能优化。若预计余额不足以完成全部23图与验收，先停在已完成部分并报告，不放宽单图30s。用已运行forem-dev，不建/停容器或他人进程。显式选择gpt-6.1-sol/gpt-6-luna并登记实际模型/强度。不提交、不推送、不合并。

完成时last message给简短中文总结：各门结果、24图逐图通过/失败计数、擦边射线总数与范围、非墙残差、采样拒绝变化、账本、未解决问题和待用户决定事项。遇到需要用户决定的问题（含任何似需重新生成地图的情况）停下报告。
```

## r3续跑派发prompt（2026-10-26，Claude→Codex父协调）

```text
你是FoReM task8.8 r3的执行协调者（Codex，推荐gpt-6.1-sol / medium）。工作区/home/ybc/projects/CL-FoReM。这是task8.8第三轮续跑。r2中home_map_000/001的C/D通过，home_map_002两条射线解析入墙5.99m、体素首命中6.005/6.003m（约1cm亚体素偏差跨6m量程被截为inf）导致按旧口径C FAIL，余21图未跑。Claude复核SRC-1060；用户2026-10-26“全部批准”（SRC-1061）：穿墙诊断改用不限量程的体素首命中d_v与解析入墙d_a比较，墙内弦长≥0.05m且d_v−d_a>0.3m才计穿墙，须为0；弦长<0.05m擦边、以及d_a≤6m但d_v>6m的量程边界射线都逐图单列（数量、弦长、d_a/d_v、入墙z、所属墙），不计失败；生产PcdPanorama与6m量程不变（不限量程只用于诊断参照，不改生产代码）。

先读：AGENTS.md、forem/doc/PROGRESS.md、forem/doc/tasks/task8/task8.8/{TASK,PROCEDURE,RESULTS}.md（含r1/r2全部记录与Claude复核）、forem/doc/SOURCES.md中SRC-1021、1040、1041、1046、1049、1060、1061，以及forem/doc/agent_logs/task8/task8.8/下日志。

任务（沿用run-id t8-voxv3-20261026与同一账本forem/logs/task8/t8-voxv3-20261026/budget.json，r2后余约599s，不重置、不自行加预算）：
1. 父：核v3代码hash与S1交付一致；登记r3于RESULTS与日志。
2. S3（Sol）把新诊断口径写入固定清单；先用已保存产物复判home_map_000–002（不重跑生成，D已通过的不重跑）；然后S2（Luna low）串行执行余21图C几何＋D链路（单图≤30s，任一非零立即停并上报），S3（Sol medium）亲读原产物复核，分类非墙残差、spur、擦边与量程边界射线，报告采样拒绝变化。
3. S4：与S1不同的独立gpt-6.1-sol / high总验收，逐门A–F（C按SRC-1061口径）。B门GPU已在r2通过，代码未变则引用即可。E门沿用r2重建基线复核零漂移。
4. 父收尾：RESULTS追加r3、父task8 RESULTS子结果行、PROGRESS、SOURCES（只用预留SRC-1062–1079）；若全部门PASS，task8.8标done、task8.7标closed（被v3取代，历史保留）。

边界：不训练，不运行task7_lower或任何含optimizer/SAC更新的测试；不改v3归属/τ/域/分辨率/接口/生产量程，不改task7、mapgen、archive、v1/v2产物，不调用mapgen；不改奖励/动作/终止/IK/Grid/策略、ghost或velodyne豁免；不做性能优化。若预计余额不足以完成全部21图与验收，先停在已完成部分并报告，不放宽单图30s。用已运行forem-dev，不建/停容器或他人进程。显式选择gpt-6.1-sol/gpt-6-luna并登记实际模型/强度。不提交、不推送、不合并。

完成时last message给简短中文总结：各门结果、24图C/D逐图通过/失败计数、擦边与量程边界射线总数及范围、非墙残差、采样拒绝变化、账本、未解决问题和待用户决定事项。遇到新的需要用户决定的问题（含任何似需重新生成地图的情况）停下报告。
```

## r4续跑派发prompt（2026-10-26，Claude→Codex父协调）

```text
你是FoReM task8.8 r4的执行协调者（Codex，推荐gpt-6.1-sol / medium）。工作区/home/ybc/projects/CL-FoReM。这是task8.8第四轮续跑。r3已检10图：C 9过、library_map_000按旧口径停（15条“长弦无命中”），D 9过（home_map_002已补），余14图未跑。Claude复核SRC-1080：这15条射线经过的体素都只有50%在解析墙内、最大墙内深度0.021m、无PCD候选（半体素外壳），6条止于地面、9条出顶。用户2026-10-26批准（SRC-1081）统一替代此前射线口径：穿墙门按穿透深度判定——射线（不限量程）在解析墙内到达“距最近墙面≥0.05m”的点之前必须有体素命中，否则计穿墙且须为0；深度<0.05m的外壳射线（擦边、量程边界、地面/顶面出域）逐图单列计数与深度分布，不计失败。墙类内部全占据硬门不变；生产PcdPanorama与6m量程、v3归属、τ、尺寸不变（新口径只改诊断参照，不改生产代码）。

先读：AGENTS.md、forem/doc/PROGRESS.md、forem/doc/tasks/task8/task8.8/{TASK,PROCEDURE,RESULTS}.md（含r1–r3记录与Claude复核）、forem/doc/SOURCES.md中SRC-1021、1040、1060、1061、1080、1081，以及forem/doc/agent_logs/task8/task8.8/下日志与forem/results/task8/t8-voxv3-20261026/r3/。

任务（沿用run-id t8-voxv3-20261026与同一账本forem/logs/task8/t8-voxv3-20261026/budget.json，r3后余约497.5s，不重置、不自行加预算）：
1. 父：核v3生产代码hash与S1交付一致；登记r4于RESULTS与日志。
2. S3（Sol）把穿透深度口径写入诊断与固定清单；用已保存产物复判已检10图（不重跑生成，已通过的D不重跑）；然后S2（Luna low）串行执行余14图C几何＋D链路（单图≤30s，任一非零立即停并上报）；S3（Sol medium）亲读原产物复核，分类非墙残差、spur与外壳射线，报告采样拒绝变化。
3. S4：与S1不同的独立gpt-6.1-sol / high总验收，逐门A–F（C按SRC-1081口径），E沿r2重建基线复核零漂移；B门GPU在r2已通过且代码未变时引用。
4. 父收尾：RESULTS追加r4、24图逐项表、父task8 RESULTS子结果行、PROGRESS、SOURCES（只用预留SRC-1082–1099）；若全部门PASS，task8.8标done、task8.7标closed（被v3取代，历史保留）。

边界：不训练，不运行task7_lower或任何含optimizer/SAC更新的测试；不改v3/τ/域/分辨率/接口/生产量程，不改task7、mapgen、archive、v1/v2产物，不调用mapgen；不改奖励/动作/终止/IK/Grid/策略、ghost或velodyne豁免；不做性能优化。预计余额不足以完成全部14图与验收时，停在已完成部分并报告，不放宽单图30s。用已运行forem-dev，不建/停容器或他人进程。显式选择gpt-6.1-sol/gpt-6-luna并登记实际模型/强度。不提交、不推送、不合并。

完成时last message给简短中文总结：各门结果、24图C/D逐图通过/失败计数、外壳射线总数与深度范围、非墙残差、采样拒绝变化、账本、未解决问题和待用户决定事项。遇到新的需要用户决定的问题（含任何似需重新生成地图的情况）停下报告。
```
