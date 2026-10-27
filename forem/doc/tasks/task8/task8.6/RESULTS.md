# task8.6 — 结果与交接

状态：**review（功能验证/性能/证据交付已完成；执行越界使严格合规失败，不能标无偏差done）**。实际独立Agent gpt-6.1-sol/high；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨模块证据核查需高强度；父已亲自复验。证据[SRC-0997](../../../SOURCES.md#src-0997)、[SRC-0998](../../../SOURCES.md#src-0998)。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

**规划阶段历史（实施前）**：当时尚未执行，只建立规划；无本节点实现、测试、仿真、地图生成或性能结果。不沿用task7旧成绩作验收。

## 执行记录模板（每run追加，保留历史）

- run-id/开始结束：尚未执行。
- 目标/授权与输入：见[TASK](TASK.md)；依赖8.1–8.5实现/结果交齐；不得仅采信子Agent自报。
- 负责人：独立验收Agent，父亲自复核待派发；实际模型/推理强度：未知。
- 修改文件/版本/hash：尚无；限定TASK列出的文件。
- 实际命令/容器/设备/退出码、日志/产物：尚无。
- 验收项与结果：尚未验证，见[TASK](TASK.md)及[PROCEDURE](PROCEDURE.md)。
- 共享预算消耗/余额、全局墙钟/累计worker：尚未执行，向父领取余额。
- 问题/风险/证据来源：未实施；沿父任务限制，不假定PCD迁移或SAC已通过。
- 下一步：收到执行派发后先核依赖与范围；提交父复核，不自行将父状态标done。

## P0规划独立审查（2026-10-26）

只读审查已结束，审查Agent `task8_plan_review`；实际模型/强度未知；发现三项合同问题，父已核实并修订。此阶段只审文档及必要代码，8.6实现/运行验收仍尚未执行。日志见[规划审查记录](../../../agent_logs/task8/task8.6/20261026-codex-plan-review.md)。


P0发现与父修订：

1. 域外规则未映射旧Core：明确数据域不生成墙/天花板；reset沿原合法性，查询可出入域，step不新增越域终止/碰撞/奖励，机械臂高于1.6m允许但保留地面/自碰撞；输入点越界仍拒绝。
2. PCD/JSON不一致处理冲突：结构/单位/hash错误拒绝，boxes几何差异只诊断；干预测试更新manifest/hash。
3. 部分地图可行性与verify退出码冲突：required_gates与map_diagnostics分开；24图格式/几何与记录完整、至少1语义图默认链路通过，其他仅采样预算不足可pass_with_map_limitations；异常、后端错误、缺记录仍失败。

P0是独立初审＋父修订/静态复核，没有声称独立审查者已对修订版再次运行验收。后续实现阶段仍由8.6独立核实上述门。

## t8-exec-20261026 — 独立总验收交付（2026-10-26，review）

实际负责人：独立Codex `gpt-6.1-sol / high`，未参与8.1–8.5实现；父另行亲自复查。推荐Codex **GPT6.1sol / high**、Claude **Sonnet5.5 / high**，理由是跨几何/状态/信息边界/原产物/预算核对；推荐不冒充实际Claude执行。

**结论分开登记：技术功能A–F通过；严格执行合规失败，整体仍review/qualified，不能宣布本批全程合规。** 非预期网络更新详[SRC-0997](../../../SOURCES.md#src-0997)；新技术/性能核查详父登记的[SRC-0998](../../../SOURCES.md#src-0998)。未启动任务训练、未恢复task7/D10、未修改生产SAC算法或task7源码，但误选旧参考测试确实进行了8次CPU SAC更新，不能用“未长训”掩盖。父已向用户披露；本节点不自行将父任务标done。

### 授权、文件与原证据

授权仅task8第一阶段独立验收、最小smoke/verify工具、必要有界性能与证据交接。只新增`forem/scripts/task8_pcd_smoke.py`、`task8_pcd_verify.py`、`forem/src/task8_sim/tests/test_pcd_integration.py`，自身RESULTS及[独立日志](../../../agent_logs/task8/task8.6/20261026-sol-acceptance.md)；辅助审查/捕获脚本位于本run logs，原件不删除。生产模块、config、旧产物、原integration和map-diagnostics未覆盖。无提交/推送/合并。

审查输入：父/6子任务三文档，SRC-0984–0996，完整review-task8-all.diff与当前assets/fixtures/scene/robot/perception/episode/routes/env/decision_env/import_mapgen及tests，父账本与原逐图JSON/NPZ。未以子Agent汇总代替原证据。旧源码157文件分为容器可读148和仅宿主可读mapgen9；逐一对规划baseline hash核对为零漂移，48源资产同时对旧map-assets-audit及新导入资产hash核对。容器缺mapgen挂载时verify显式依赖宿主9文件哈希证据快照，不假称容器直接复读了宿主文件。

新产物目录为[acceptance](../../../../results/task8/t8-exec-20261026/acceptance/)，包括：

- `acceptance.json`：required_gates A–F与map_diagnostics、execution_deviation分开；`no_network_optimizer_execution=false`，`execution_compliance=fail`。
- `manifest.json`：冻结新源码/config/资产、148旧文件和原始诊断/本次smoke；411项文件hash；另外链接9文件宿主核查。活跃共享文档不作固定源码验收。
- `raw-map-audit.json`、`ledger-map-audit.json`：逐24原记录/48NPZ/默认接受/真实提交/版本/PCD hash、独立floor占据与入域射线期待、CPU实际FK复算及账本owner/argv/rc关联。
- `performance.json`：实际样本、设备/dtype、峰内存与未测项；`map-budget-supplement.json`追加本节点semantic复验扣账，保持8.5原预算文件。
- `review.json`、`tests.json`、`deviation-filesystem-audit.json`、`mapgen-hash-audit.json`、`verification.json`：审查、所有失败/纠正与严格合规机读结果。
- `scan-trajectory.png`：office_map_002初/末深度、真实Grid、实际base/FK/joints，仅一次动作轨迹；已亲自查看图像，不表示完整任务到达。

### 技术门与适用限制

|门|技术判定|原证据与独立核查|
|---|---|---|
|A PCD权威/协议|pass|严格ASCII/hash/半开域/不可写float64；新PCD干预保持相同semantics时射线与碰撞变化；PCD-only；27原资产/fixture回归与本次原hash核查。|
|B 扫描/碰撞同源|pass|scene仅XYZ构建占据；显式lo/hi closed-union，base原XY投影、arm三维胶囊/地面；闭接触fix原反例/SAT审查记录保留；24原geometry独立floor/正入域射线期待再次核对。|
|C ghost/非sensor碰撞|pass|只两个明确velodyne body检测豁免；整机自身扫描遮挡按ghost忽略，场景遮挡保留；原ground/topplate/arm/self回归及本次传感器测试，未扩大豁免。|
|D 整环境/reset/局部边界|pass|独立GPU两controlled短路线decision legacy完整边界/执行、truth替换不改变Grid-only候选推演；原profile/Core对照/恢复拒绝代码及原测试；新增CPU与CUDA ragged reset核查。|
|E 立方体/语义链路|pass|fresh默认random_cubes b1再b2，各一次动作/每行commit2/自动scan；原24图各一次合法默认episode与一次动作/48NPZ均再次核对；补office_map_002默认semantic局部推演→选择→单动作→scan。|
|F 版本/hash/设备/profile|pass（功能证据）|新三版本/显式profile、cuda:0 float32、157/48hash、1800s共享账本与有界短窗；不包含“全程无optimizer”这一已违反约束，严格合规另为fail。|

24/24在**此次**诊断均step_checked，all_maps_runnable=true的含义仅为本次每图一次采样+动作，不是普遍可达或完整任务成功。CPU从原actual base/q重算FK最大矩阵分量差`1.1920928955078125e-7`；3e-6仅沿8.5原工程验证容差，不是控制精度结论。语义图额外slice包含真实Grid-only rollout，但不称完整默认长DecisionEnv.step；完整decision接口证据仍是两变体controlled短route，二者明确分开。

Ragged部分reset：选中行从2个节点变9个真实节点并切换empty→axis_aligned；未选行xyz/quat/s原存储前缀、length、17点Route.at物理路线、全部current_observation tensor、Grid、queue、计数器与RNG保持。整个batch的route存储宽度2→9，新增部分仅相同终点padding；**没有宣称shape或全部padding后的tensor逐字不变**。此为原表示逻辑的语义核验，不改变生产合同。

### 验证、命令与失败

完整真实argv/起止/rc/timeout/elapsed与日志以[共享budget.json](../../../../logs/task8/t8-exec-20261026/budget.json)为权威。所有计算经owner8.6前缀run_budget，容器forem-dev、内部timeout、PYTHONDONTWRITEBYTECODE/PYTHONPATH；GPU0串行。新smoke均max-steps1，远低于64，内部≤30s；语义slice内部15s/外17s。

- RED `854392b5b2`：缺verify模块，4failed/2passed；GREEN `c5555a4d2d`六项通过。
- `8e747bc371`：7passed（含CPU ragged）；`11aa8b6172`：GPU四项通过（两decision变体、truth替换、ragged），23.446160s。未重复会覆盖integration快照的旧default cube测试。
- `2e2dc38e0f`、`a02356ca91`：新smoke b1→b2 rc0，外账本5.020983/5.521904s；`c4234dbbbe`：office_map_002 slice rc0/12.281019s；该图原累计10.936490s＋新增=23.217509s<30s，补充账本不覆盖原计划。
- `c88bf75471`误选旧整文件：71passed/2skip/4fail；4个失败是屏蔽CUDA后旧Core/kin测试硬编码GPU，后仅精确四纯Core/IK节点`83dc84c05b`重验4passed/4.620512s。**同一误选命令还执行了违规SAC更新，详下一节，不作clean通过依据。**
- 最终安全精确allowlist `0f9682dfed`：9passed/3.719320s，含缺门/fail/not_run、hash篡改、原geometry error及临时asset hash负例；原产物不改。门状态负例随后强化为先提供有效其他证据并精确匹配B失败，`65f31d6ffa`三项通过。
- 父发现summary flags可能矛盾掩盖非空execution_deviation后，先RED `7d9297b287`两项，再最小helper要求两summary正确且deviation为空，GREEN `26e0e0de8a`共6项纯字典/hash门禁通过；无torch/环境/网络执行。
- 打包/审计辅助失败均保留：9a9f710717、c7ccb6bd18误读账本jobs键（实际commands），be3736d5d1容器不可读宿主mapgen，ddfe843b4a宿主写root-owned产物权限、288ff42311缺此前输出；e874362589外壳重定向落在错误cwd。只修辅助路径/schema，未改生产模块，未绕账。成功修正及最终verify见账本末次8.6-package/final-verify条目。

verify CLI：`python3 -B scripts/task8_pcd_verify.py --run-dir results/task8/t8-exec-20261026`。它对A–F失败/缺失/not_run、证据/hash/资产/几何异常返回非零；24图解析/geometry必须通过，运行只允许无accepted的reset采样限制且至少1图完整链路；已知执行违规使严格结果fail/rc1，即使两summary被误标pass也不能吞掉非空偏差。第一次完整verify `77b6b4e491`已实际返回rc1、functional_status=pass、execution_compliance=fail、24图；源冻结后还需以最终verification.json及末次命令为准。

### 执行偏差与旧产物检查

误选节点准确为`src/task7_lower/tests/test_lower.py::test_sac_matches_reference_and_full_resume[False]`、`[True]`，各四调用：s/update0、AST reference/update0、s/update1、clone/update1；总8次，次数为执行后源码推导，没有重跑。LowerSAC显式cpu、batch和优化器参数均CPU；不能把临时单测称为授权训练。源码full_state_dict/load_full_state_dict只做内存deepcopy/加载，没有torch.save或磁盘checkpoint调用，不能称“恢复旧checkpoint”；测试模块也曾在内存操作Replay，故后续禁止相关节点。

容器root只读metadata核查`62cb0d67db`：results/task7、logs/task7、config/task7、src/task7_sim/lower/upper共36,116文件，unsafe命令开始后mtime修改0、错误0；157源码/config独立hash零漂移。**没有旧训练产物的全量事前字节hash，不以mtime无变化证明绝对所有历史字节不变**。未清理/tmp证据。最终docker top仅原sleep、nvidia-smi无compute；无本节点后台任务。偏差不能撤销，由父保持review并如实报告用户，不再运行网络/optimizer/SAC/replay相关测试。

### 性能与SAC证据交接

短窗数据：新sync_v5 b1/b2 cold reset1.311007/1.718271s，单Core step（含IK/collision/scan）.694458/.715528s；wrapper总5.020983/5.521904s，脚本wall4.315196/4.863798s，每行提交sim .1s；batch2累计worker sim .2s并非全局sim .2s。实际cuda:0、torch.float32，峰allocated72,941,568/171,028,992 bytes；process ru_maxrss和CPU preprocessing/device upload实值在performance.json。semantic legacy slice脚本wall11.576709s、wrapper12.281019s、GPU峰257,145,856bytes；不是同步profile或长任务吞吐比较。

每组件每变体仅1样本，p50/p95为N/A；24语义图采样阶段的p50/p95由24份原timing实值计算，注明异图异工作量，非重复性基准。冷加载与scene preprocessing/upload有实测；warm cache单独收益、独立IK/碰撞与raycast/Grid拆分、CUDA event时长、冻结NN推理均not_run/N/A，不能造数。脚本actor不是冻结NN；误选单测更新不作性能测量证据。未实施性能优化、未外推长训工期。

供下阶段用户另行决定的输入：新环境PCD/ghost、域外空+解析地面、base全高度投影/规划高度保守、策略仍原Grid和74/75维、无语义通道；默认初始化/64 witness可行性及实际成本、24图本次一次episode/action、版本/hash与恢复拒绝证据。旧v5退化、STOP、未到5M、D10 OOM及未闭合工作仅引用[SRC-0983](../../../SOURCES.md#src-0983)，没有修复、恢复或新增实验组。环境链路通过不等于SAC稳定/成功率提高或WM有效。

下一步：父亲自复查最终代码/manifest/原产物/verify rc1与合规偏差，统一来源/进度与最终账本；本节点交付review，不再自行启动训练或地图批次。

最终冻结打包`4f63d737f1` rc0/1.466127s；最终CLI实际复核`e078400de4` rc1/20.541937s（这是预期严格合规拒绝）：`functional_status=pass`、`required_gates A–F=pass`、`map_count=24`、`execution_compliance=fail`，非空execution_deviation保留。最终verification.json已由真实CLI输出捕获，不是手工填pass。退出后容器只剩docker-init/sleep，nvidia-smi无compute，未留运行任务。最终预算以父共享账本为准，后续父只读复核可能继续增加。

退出时共享账本：本节点26条命令累计149.636356s（≤300s配额，含所有失败/负例/绘图/复验），全任务used674.951172s、remaining1125.048828s、active={}。performance.json为打包时快照，不伪称包含之后末次verify；精确最终余额以上述账本为准。

## r2补齐F组件profile（active，尚未执行）

父亲核指出第一版F只有端到端/融合计时，独立IK/碰撞、raycast/Grid及warm缓存未齐；因此第一版“F profile完整通过”需要本补充证据限定。保留acceptance原件与原verify，最终补充放acceptance-r2。仍为同一300s配额，n=3为有界工程选择，非新实验/训练。

执行前精确allowlist：load_asset、VoxelScene.from_asset/occupancy/provenance、Kinematics.world_tcp/solve_world、GhostRobotGeometry.__call__、SceneCollision.__call__、PcdPanorama.__call__、Grid.empty/update、PcdEpisodeSampler.sample（RandomStreams同seed新流）、route/base/q/witness张量相等比较、torch no_grad/synchronize/CUDA events、NumPy压缩及JSON/hash输出。仅random_cubes，CPU64和CUDA0 float32；scripted actor是tensor操作。禁止任何NN/optimizer/replay/旧整测试文件。父后续登记SRC-0998；实际未执行项不先写通过。

### r2纯环境组件测量结果

`7b7809a89a` owner8.6-component-profile rc0/9.927845s（脚本wall7.832650s）；在torch.no_grad下，CPU float64及cuda:0 float32的既有random_cubes固定实际输入各测3次，未执行NN、optimizer、replay或旧测试。原始samples/小样本p50/p95、GPU stream events与单位均在[component-performance.json](../../../../results/task8/t8-exec-20261026/acceptance-r2/component-performance.json)。n=3只为有界工程补测；p95是三样本的线性分位数，不能当稳定尾延迟/训练工期依据。

|组件wall p50秒（各n3）|CPU float64|CUDA0 float32|
|---|---:|---:|
|load_asset（host parse）|.077250|.076929|
|scene CPU预处理+实际device upload总构建|.127991|.126376|
|IK solve_world，同Ghost|.011643|.016899|
|SceneCollision|.002721|.003834|
|PcdPanorama（场景raycast+解析地面）|.017093|.028870|
|Grid.update（预分配全新Grid，分离分配）|.001645|.000526|
|scripted actor tensor操作|.0000105|.0000477|
|压缩+文件输出（host）|.004321|.002836|
|CPU→GPU实际base/q搬运|N/A|.0000508|

Scene总构建n3，CPU preprocessing/device upload的末次真实provenance分项单列，未伪称这些内部字段也有n3统计；GPU事件仅stream时间区间，包含host launch gaps/idle，不是纯kernel时间。GPU IK三样本的首样本冷启动明显，实际p95 .406780s，原样保留，不去掉慢样本。NN冻结推理继续N/A，不能用scripted actor或违规单测更新替代。全部无动作提交，sim_time_s=0、actions_committed=0；采样/IK是计算wall工作。

缓存对照各3对：每对新建sampler/planner采样，再对同sampler的同scene/planner cache使用重新构造的相同seed RNG流采样；base/q/route xyz/quat/s/length、witness base/q及proposal seed逐字相等，缓存对象identity保持。CPU fresh/warm p50 .508072/.278339s；CUDA .574956/.353517s。没有flush磁盘/OS缓存，因此fresh仅指新sampler/planner，不能称磁盘cold；只证明此次固定输入下缓存减少重建开销，不作全图/长训/GPU提速结论。dtype不同、n小且初始化费用不同，不能把CPU/CUDA列当公平设备优劣基准。

新目录[acceptance-r2](../../../../results/task8/t8-exec-20261026/acceptance-r2/)复制原验收文件并追加组件证据；`original-preservation.json`核原acceptance每文件前后hash完全一致，原performance/verification保留；新manifest增加helper、新组件报告/NPZ及旧performance原快照hash。A–F仍按原有技术门，F独立计时缺项由上述证据补齐；严格execution_deviation、no_network_optimizer_execution=false、execution_compliance=fail原样保留。verify以acceptance-r2为run-dir，map_run_dir仍为..，不改变任何map诊断或旧源文件。

r2最终打包+真实CLI验证`ff10b8016a` rc1/20.642633s，421项manifest、原12份acceptance文件hash前后不变；真实输出`functional_status=pass`、24图、`execution_compliance=fail`，符合保留执行偏差的预期。新增本轮30.570479s，本节点累计180.206835s≤300s；r2结束无运行任务，容器仅原sleep、GPU无compute。第一版数字/旧报告保持历史，不以补测抹除违规；父最后复核并登记SRC-0998。

### 父最终复核

父已亲读smoke/verify/新tests/纯组件profile代码、原24图状态/代表实际base-q-FK-scan、最终r2报告和小样本限制，并查看PNG。父56174f13bd实际只读复验rc1：功能pass、A–F pass、24图，执行合规fail/8更新调用；738c605416原157与48源三处hash检查rc0。新r2补齐拆分性能，原acceptance保留；[最终来源SRC-0998](../../../SOURCES.md#src-0998)。本节点交付收尾完成但严格状态review，不自动SAC修复或训练。
