# task8.10 RESULTS — 原语场景几何后端

状态：**done（2026-10-27）**：primitive-obb-v1作为**可选后端**验收通过，默认仍`pcd-voxel-v3`。A–H各门结果见下表，经S4独立验收，条件见文末“r2收尾”。原规划说明：2026-10-27 Claude（claude-opus-5-5）建立三文档与对照验收方案，依据[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)、[SRC-1181](../../../SOURCES.md#src-1181)；授权见[SRC-1220](../../../SOURCES.md#src-1220)。下文按时间保留各轮历史。

## 门状态（最终，2026-10-27）

|门|状态|证据|
|---|---|---|
|A 导入|pass|`s3-r1/gate_A.json`；S4用最终脚本重跑同值`s4/rerun/`|
|B 解析正确性|**pass_approved**（严格FAIL保留，[SRC-1310](../../../SOURCES.md#src-1310)）|`s3-r2/gate_B.json`；S4全量括号重放54图带外0（`s4/s4_b_full_summary.json`）|
|C 结构缺陷|pass（[SRC-1221](../../../SOURCES.md#src-1221)接触带判据）|`s3-r2/gate_C.json`|
|D 与V3差异（报告）|report|`s3-r2/gate_D.json`|
|E 单一真值干预|pass|`s3-r1/gate_E.json`；S4重跑`s4/rerun/`|
|F 接口与链路|pass（现有测试参数化以替代证据接受，[SRC-1311](../../../SOURCES.md#src-1311)）|`s3-r2/gate_F.json`（CPU）、`s3-r2/cuda/gate_F.json`（CUDA）|
|G 性能（报告）|report|`s3-r2/gate_G.json`；S4批量碰撞复核`s4/s4_g_*.json`|
|H 保真隔离|pass（**重建基线**）|`s3-r2/gate_H.json`、`s3-r2/h-baseline/`|

产物根目录`forem/results/task8/t8-prim-20261027/`。

## 交接（2026-10-27 规划）

- 目标与授权：用户同意方向A，只建文档；实施需另行授权并确定预算。当前负责人Claude（规划）；执行负责人待派发。
- 已完成：TASK/PROCEDURE/RESULTS三文档；父task8流程表、PROGRESS、SOURCES（SRC-1181）登记；[规划日志](../../../agent_logs/task8/task8.10/20261027-claude-primitive-plan.md)。
- 剩余：用户决定是否派发、预算与执行时机（须在8.9 r2结束后或隔离worktree中接线）；PROCEDURE中的样本量/容差待派发时确认。
- 风险：语义图`objects/parts`组合规则尚未从mapgen源码核对（A门首项）；原语越域处理与v3“域外点报错”口径不同（已列为工程选择）；接线改动若与8.9后续代码并发须协调。
- 推荐模型：见[TASK模型表](TASK.md#model-routing)。

## r1 S2独立参照R（2026-10-27，父Claude核查）

- 执行：Claude子Agent claude-sonnet-5-5 / high（S2）。交付`forem/results/task8/t8-prim-20261027/reference/`：`reference.py`（仅json+numpy，SHA256 `54404624d36a234d4fd089aa3185c9b440871ac9182ae2d6bf24cc7a27c9f312`）、`DERIVATION.md`、`selftest.py`/`selftest.json`；[S2日志](../../../agent_logs/task8/task8.10/20261027-s2-reference.md)。
- 父核查（读原件）：selftest.json summary 154/154 passed、0 failed、wall 29.84s（forem-dev CPU，numpy 1.23.5）；ledger-S2 15条合计236.6s（≤500s份额），其中3条rc1为开发期自测脚本迭代，末次全套rc0；reference.py import仅json/numpy。
- 含义限制：只证明R内部自洽并与手算/暴力判据一致；**未与S1比较，A–H门均未执行**。
- 合同附加（S2自报，非范围扩展）：`chassis_margin`、`tol`可选参数、`ray_box_intervals(clip=True)`，供B门边界带判定。约定依据：mapgen `map_builder.py` L17–36、task7 `geometry.py` L24–28/L54–65、task8 `scene.py` L119–133（S2引用，父未逐行复核）；立方体sidecar旋转约定未对照原导出代码（推测）。
- **待用户决定（C门判据）**：盒面恰落0.05网格线时“与闭合OBB接触”的体素是否计入取决于末位舍入；S2实测R(−1e-9)与R(+1e-9)之间带内单元library_map_001 16382、hospital_map_001 6653、sparse_test_00000 24704、standard_test_00000 24566（立方体图约19%）。S2建议C门“与R逐格相等”改为`R(−1e-9) ⊆ P ⊆ R(+1e-9)`并逐格列出P与R(0)之差均在带内；此为门修订，须用户批准，未采纳。
- 其他线索（源码阅读，未实测）：mapgen PCD体素化不含远端面点；超高盒在PCD中被裁剪而JSON保留原size——供D门归因。CPU吞吐：R单位姿360×90扫描0.56–0.78s，B门20位姿×24图约340s，S3份额需据此规划。
- 账本：ledger-S1当前20.5s（S1仍在执行），合计约257s/3600s。

## r1 S1实现P/PV（2026-10-27，父Claude核查）

- 执行：Claude子Agent claude-sonnet-5-5 / high（S1），[S1日志](../../../agent_logs/task8/task8.10/20261027-s1-impl.md)。新增`src/task8_sim/primitive_assets.py`、`primitive_scene.py`、`tests/test_primitive_{assets,scene,wiring}.py`、`config/task8/primitive_scene.json`、`scripts/task8_prim_verify.py`（A–H mode、内置账本检查rc=3）；接线最小改`episode.py`/`env.py`/`decision_env.py`，默认仍`pcd-voxel-v3`，diff见`results/task8/t8-prim-20261027/s1/wiring.diff`（父已读，仅新增`map_backend`参数与分派、versions随后端）。
- S1自报（父未复跑）：新测试51 passed；4个故意错误变体全检出；v3默认回归子集8 passed（`test_pcd_env.py`5个node＋`test_scene_forest.py`），未运行task7_lower/SAC/optimizer测试。各mode `--smoke`（CPU）：A/B/E/F pass，D/G报告跑通，H可运行；C严格逐格不等、带外分歧0（见下）。A门：mapgen仅有字节码，S1反汇编`map_builder.cpython-314.pyc`得组合规则，24图2848盒展开与`boxes`最大差8.9e-16；立方体sidecar `boxes`（含4面墙）即cube-export-v2盒体集合。
- 账本（父读原件）：ledger-S1 31条470.8s、ledger-S2 15条236.6s，合计707.4s/3600s，余2892.6s。
- **C门口径**：P按数学闭合（接触计入，`CONTACT_SLACK=1e-12`），网格对齐盒面外侧一层接触格也计为占据（例8.1 axis_aligned：P 22×22×21=10164格，R 21×21×20=8820格）；全部差异格在±1e-9接触带内，随机朝向立方体图逐格相等。与S2发现同源，待用户决定C门判据。
- **未在GPU上运行**：F/G的CUDA路径与CUDA事件计时未跑。父核查：GPU0–3各有2个非本任务compute进程（各708MiB），宿主还有task5/task6容器；按规则未停止、未占用。
- 性能风险（S1自报）：P批量射线为暴力ray×box分块，CPU冒烟约比V3 BVH慢3倍，GPU未知；G门只报告。
- **H门基线缺失（父的疏漏）**：PROCEDURE §0.3要求的开工保真快照未在派发前采集；task7/task8源码均未入git。补救方案：task7文件对照`results/task8/t8-plan-20261026/source-manifest.json`哈希；三处接线文件以S1日志原版sha256（episode `e0286c3a…0a78`、env `8d2bdf74…df92`、decision_env `7eabf8b3…f3b7`）＋反向应用wiring.diff核对；其余生产文件、mapgen资产以既有manifest哈希与mtime早于S1开工（2026-10-27 15:53）佐证；H结论须注明为重建基线。

## r1 C门修订（SRC-1221）与S3派发（2026-10-27）

- S1只改`scripts/task8_prim_verify.py` `gate_C`：带由R `voxelize_closed_sat(tol=±1e-9)`给出，判据`R(−1e-9)⊆P⊆R(+1e-9)`，per-box同带判据；`status`用`pass_approved`，原严格判定保留为`pass_strict`。父读`results/task8/t8-prim-20261027/s1/smoke_c2/gate_C.json`：status pass、8图pass_approved全True、all_pass_strict False（语义图/夹具差异格全在带内，如home_map_000 5527格带外0）。这只是冒烟，不是C门全量结果。B门`occupancy_compare`与E门规划高度带仍用生产函数定带，只作报告。ledger-S1 480.6s。
- 派发S3（Claude子Agent claude-sonnet-5-5 / low）：按固定命令CPU执行A–F全量，run目录`results/task8/t8-prim-20261027/s3-r1/`，份额≤2000s；F的CUDA路径、G、H不在本轮。

## r1 S3 CPU A–F执行结果（2026-10-27，父Claude核查原件）

执行者Claude子Agent claude-sonnet-5-5 / low，[S3日志](../../../agent_logs/task8/task8.10/20261027-s3-run.md)，产物`forem/results/task8/t8-prim-20261027/s3-r1/`，日志`forem/logs/task8/t8-prim-20261027/s3-r1-{A..F}.log`。

|门|rc|wall_s|status|父核查|
|---|---|---|---|---|
|A|0|5.84|pass|gate_A.json|
|B|1|630.4|error|全部地图循环已跑完，末尾`res['totals']`汇总`KeyError: 'contains'`（`task8_prim_verify.py` L501），异常处理只写错误、**逐图结果全部丢失**；不是B门判定失败，也不是通过|
|C|2|400.8|incomplete_budget|预算耗尽时未保存任何已完成地图结果|
|D|2|400.2|incomplete_budget|同上|
|E|0|62.4|pass|gate_E.json|
|F（float32，CPU）|2|251.0|incomplete_budget|同上|

- 账本：全部角色合计2467.8s/3600s，余1132.2s。宿主load average约26（64核），另有task5/task6容器运行。
- 父的问题：派发S3前未要求先做单图计时先导，也未核实verify脚本在预算中止时会逐图落盘；导致约1680s（B 630s＋C/D/F 1051s）未留下可用逐图证据。
- 状态：A、E通过；B、C、D、F无结论；G、H未执行。不能据此推出P正确或有缺陷。

## r1 verify脚本健壮性修复（2026-10-27）

S1只改`scripts/task8_prim_verify.py`（不改几何/判据/样本量/配置）：B门totals KeyError根因为空fixture `empty`记录缺`contains`键，已修；异常/预算中止保留已完成maps（`completed_maps/remaining_maps/stopped_reason/traceback`）；B/C/D/E逐图、F逐`map:profile`原子落盘；逐图`elapsed_s`与子项`timing_s`；新增`--maps-only`、`--resume`，种子改用稳定下标（全量顺序下数值不变）。CPU smoke：B 8图pass、中止后`--resume`补完；C 8图pass_approved；D/E/F可运行与中止保留已验证。父读`s1/smoke_ab/gate_B.json`核对resume字段。ledger-S1 573.3s。全量B/C/D/F待预算决定。

## r2 账本追加与S3续跑派发（2026-10-27）

用户批准验证账本上限追加到7200s（[SRC-1309](../../../SOURCES.md#src-1309)），已用2560.4s（S1 573.3/S2 236.6/S3 1750.6），余4639.6s。派发S3-r2按[PROCEDURE §8](PROCEDURE.md)：单图计时先导→CPU全量B/C/D/F→GPU空闲时F CUDA与G→重建基线H。父派发时GPU0–3均无compute进程（14MiB）。结果待S3-r2完成后父核查原件补记；当前B/C/D/F/G/H仍无结论。

### r2 单图计时先导（S3-r2，父核查原件）

S3-r2（Claude子Agent claude-sonnet-5-5 / medium，[日志](../../../agent_logs/task8/task8.10/20261027-s3-r2-run.md)）先导产物`results/task8/t8-prim-20261027/s3-r2/pilot/gate_{B,C,D,F}.json`，CPU：B 32.3s pass、C 24.7s pass、D 44.9s report（B/C/D为`warehouse_map_001`，167盒，语义图最多盒）；F 123.5s pass（home_map_000×3 profile，decision两profile各约60s）。仅单图先导，不是全量结论。账本合计2785.9s/7200s。
- 外推（S3自报，父复核口径）：按盒数线性B≈630s（与r1 B全循环630.4s一致）、C≈480s、D≈405s、F（11图×3 profile）≈1360s，CPU合计约3000s；按最慢图保守上界约5650s。F CUDA与G未测。
- 发现：`config/task8/primitive_scene.json`的`ledger.limit_s`仍为3600，脚本据此截断。父按用户批准的7200s（[SRC-1309](../../../SOURCES.md#src-1309)）将该值改为7200（仅此一字段；config_sha256随之改变，先导产物记录的是旧hash），几何/判据/样本量不变。
- 父决定：S3在合计≤6600s（为S4留600s）内续跑CPU全量B/C/D/F；GPU前先做F CUDA单图与G先导，若剩余不足以完成F CUDA全量＋G＋H，停下由父报用户，不缩样本。

## r2 S3全量结果（2026-10-27，父Claude核查原件）

执行者Claude子Agent claude-sonnet-5-5 / medium，[S3-r2日志](../../../agent_logs/task8/task8.10/20261027-s3-r2-run.md)，产物`forem/results/task8/t8-prim-20261027/s3-r2/gate_{B,C,D,F,G,H}.json`（config sha `ae67ff5e…`），日志`forem/logs/task8/t8-prim-20261027/s3-r2-*.log`。父读各gate JSON核对status/完成图数及B totals。

|门|status|完成|要点（S3自报，父已核对标*项）|
|---|---|---|---|
|B|**fail***|55/0|totals*：contains/chassis/capsule带外0，raycast带外**1**（office_map_001构造掠射射线648861）；float32命中/未命中分歧**1**（sparse_test_00000 ray 127923，射线到盒线段距离6.5e-8m，float32轮廓擦边；2026-10-27 S4指出更正，原写0有误）|
|C|pass（SRC-1221判据）*|55/0|带外0、内部缺格0、深墙射线漏检0（12,102,217条）；严格逐格相等26/55，P与R(0)差208,646格全在带内|
|D|report*|55/0|中止后`--resume`补完；P−V3 \|Δ\|>0.05m占比0.173；碰撞分歧P−V3底盘1.18%/机械臂1.59%；墙/非墙子分位与reset接受差未汇总|
|E|pass（r1）|—|见r1|
|F CPU float32|pass*|33/0|11图×3 profile链路ok，签名/pickle/信息边界通过|
|F CUDA|**未执行全量**|单图先导pass|先导home_map_000 81.6s；外推全量700–900s，超S3份额停下|
|G|report*|—|GPU0 cuda/float32无回退，峰值373MB；360×90扫描p50 P/PV/V3：b1 2.21/5.75/6.29ms，b64 115.6/171.1/188.5ms，b256 463.1/677.7/746.7ms；碰撞p50 P在b1/64/256均≈5.3–5.5ms（待S4核对工作量是否随批量一致）|
|H|pass（**重建基线**）*|—|73个task7文件对manifest一致；3接线文件`patch -R`后与原版sha256一致；其余90个文件仅mtime佐证；无训练/optimizer/遗留进程|

### B门带外记录父诊断（只用R）

脚本`results/task8/t8-prim-20261027/s3-r2/parent_diag_b_ray{,2}.py`（forem-dev，R-only，记入`ledger-parent.jsonl`约3s）。该射线为B门880条构造掠射射线之一（下标≥648000），原点(3.67998,3.31999,0.455)、方向≈(7.3e-6,−1,0)，与桌腿box70（x∈[3.60,3.68]）和桌面box72（x∈[3.68,4.72]）共享的x=3.68面平行，沿t∈[2.32,2.68]贴面而行：对box70带符号间隙最小−1.25e-16，对box72最小+2.2e-16。R按闭合接触在t=2.32计命中；P对两盒均判未相交，下一命中为墙box12（真实深入0.05m）t=2.77。即命中/未命中翻转发生在|gap|≈1e-16（远小于1e-9带），但两臂都有“首个命中”，被B门按both_hit距离差|Δ|=0.45m记为带外。随机射线（20位姿完整扫描）带外0。

父判断（建议，非结论）：这是与SRC-1221同类的接触带歧义，不是P几何错误；但现行B判据把它判为FAIL，父不自行改判。待用户决定：按“首个命中因带内相切翻转”归入带内（B记pass_approved，严格FAIL保留），或要求S1让P对相切面按闭合计命中再复跑B。

### 账本

全部角色合计5786.8s/7200s（S1 573.3、S2 236.6、S3 4973.9、parent 3.0），余1413.2s。待办：F CUDA全量（外推700–900s）、S4独立验收（份额600s）。

### 用户裁决（SRC-1310）

用户选“按带内歧义处理”：B门记**pass_approved**（严格FAIL保留，`gate_B.json`原件不改），待S4独立核实该射线确属带内相切翻转且为唯一带外记录。账本上限→8400s（config `ledger.limit_s` 8400，sha随之改变）。下一步：S3续跑F CUDA全量，之后派S4独立验收。

### F CUDA全量（S3-r2，父核查原件）

`results/task8/t8-prim-20261027/s3-r2/cuda/gate_F.json`：status pass，device cuda、dtype torch.float32，remaining空（S3自报33/33 chain ok、信息泄漏0、cuda:0 pickle往返相等；rc0、wall 965.4s，GPU0用前无他人compute进程，收尾无残留）。账本合计6752.2s/8400s。下一步派S4独立验收（份额≤600s）。

## r2 S4独立验收（2026-10-27，父Claude核查要点）

执行者Claude子Agent claude-sonnet-5-5 / high（≠S1/S2/S3），报告`forem/results/task8/t8-prim-20261027/s4/acceptance.md`/`acceptance.json`，[S4日志](../../../agent_logs/task8/task8.10/20261027-s4-acceptance.md)。ledger-S4 16条197.0s；全部角色合计**6949.2s/8400s**。

|必查项|S4结论|要点|
|---|---|---|
|样本量/判据|PASS|B每图contains≥100182点、20位姿完整扫描＋掠射、chassis/capsule≥10012；B/C/D 55图完成；B raycast带内判定是扰动启发式（§3的一种操作化，未放宽）|
|B唯一带外射线|PASS|R膨胀/腐蚀1e-9括号重放office_map_001全部24条raycast分歧均在括号内；648861对box70/72间隙≤7e-16，P首命中2.7699917720＝R腐蚀版2.7699917730，S3启发式判带外为假阴性；contains 27条全为边界构造点|
|新种子抽检|PASS|种子4040404，office_map_001/sparse_test_00056/standard_train_02101括号外0；1e-7膨胀负对照被检出；另4图重放全括号内|
|G碰撞批量不变|PASS（解释）|b256与逐环境调用逐元素相等；CUDA event p50 b1/64/256/1024/4096=3.9/5.3/5.4/14.0/49.3ms，小批量受kernel启动开销主导，不能读作“与批量无关”|
|S1/S2独立|PASS|R只import json/numpy，非平凡共享行0|
|接线|PASS|默认pcd-voxel-v3，v3分支未动；S4复跑56测试全过|
|H|PASS（重建基线）|manifest 157文件一致；90个mtime佐证文件最新13:20早于15:53；宿主mapgen 24 JSON与池sidecar一致|
|合规|PASS|76条账本命令无task7_lower/SAC/optimizer/训练|
|文档一致|存疑→已更正|float32分歧数（上表已更正）|

S4另用最终脚本重跑A、E（`s4/rerun/`）：A同值pass，E 9/9＋pcd_only 3/3逐位不变。父核对：`gate_B.json` float32分歧合计1、`gate_F.json` `existing_tests_note`为“Not executed in this mode”、账本合计6949.2s、无残留GPU进程。

**待用户决定的两项（判done前）**：①F门§3“task8现有测试几何无关部分对P参数化运行”未按字面执行（现有测试为v3专用），是否以S1新测51个＋S4复跑56测（含v3回归）＋CPU/CUDA真实链路33+33替代；②B门“带外仅1条”跨55图仍依赖S3启发式（S4括号重放覆盖5图228条，余50图1067条带内记录未重放），是否补全量括号重放。状态：**review**。

## r2收尾（2026-10-27，父Claude）

- S4补B门全量括号重放（SRC-1311）：54图（除无原语`empty`）35,021,172条射线、5,984,948个contains点；逐图raycast/contains分歧数与`gate_B.json`完全一致（1296/2161），R膨胀/腐蚀1e-9括号外均为0，射线648861亦在括号内。父读`s4/s4_b_full_summary.json`复算合计一致。chassis/capsule未全量重放（S3带外0，S4新种子3图抽检括号外0）。
- 账本：全部角色合计**7484.8s/8400s**（S1 573.3、S2 236.6、S3 5939.3、S4 732.6、parent 3.0）；S4超原600s软份额系用户追加重放所致。无残留进程。
- 结论：primitive-obb-v1作为可选后端done。限制：B pass_approved依赖SRC-1310接触带裁决；F现有v3专用测试未对P参数化（SRC-1311替代）；H为重建基线（90文件仅mtime佐证）；float32报告1条擦边分歧；G小批量碰撞延迟受kernel启动开销主导；P批量射线CPU上慢于V3 BVH，GPU上更快（b256 463 vs 747ms）。D门显示P−V3 |Δ|>0.05m射线占比0.173，用v3训练出的结论不能直接迁移到P。
- 不在本任务：是否把默认后端切为primitive-obb-v1、地图完成后的训练重新规划，均须用户另行决定。
- 实际模型：父claude-opus-5-5（强度未知）；S1/S2 sonnet-5-5 high、S3 sonnet-5-5 low(r1)/medium(r2)、S4 sonnet-5-5 high。后续推荐：Codex GPT6.1sol / Claude Sonnet5.5，常规low，跨后端对比与训练规划high。

