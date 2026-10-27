# task8.7 — 结果与交接

状态：**closed（被task8.8的pcd-voxel-v3取代，v2历史FAIL保留）**。2026-10-26按用户条件在v3全门通过后关闭：[SRC-1081](../../../SOURCES.md#src-1081)、[SRC-1087](../../../SOURCES.md#src-1087)、[SRC-1089](../../../SOURCES.md#src-1089)。原结果与产物不删不改判。

推荐模型/强度见[TASK分工表](TASK.md#model-routing)；以下各run由执行者登记实际模型/强度，无法核实写“未知”。


## 父协调最终交接 — t8-voxfix-20261026

**总体未通过，blocked等待用户决定。** A/B/E PASS；C FAIL；D NOT_RUN；F FAIL（无训练、预算合规子项PASS；独立总验收通过条件FAIL）。最小ε修复保留，首图西墙仍有32格整列欠覆盖，不用JSON补PCD、不自行改协议或继续其余23图。[SRC-1002](../../../SOURCES.md#src-1002)、[SRC-1004](../../../SOURCES.md#src-1004)、[SRC-1006](../../../SOURCES.md#src-1006)。

|角色|实际派发模型/强度|交付|
|---|---|---|
|父协调|codex exec元数据gpt-6.1-sol / medium；底层服务模型无法独立核实|亲读diff/原日志、登记来源/预算、复核保护文件、共享收尾|
|S1|gpt-6.1-sol / high，显式平台覆盖|RED→GREEN、最小修复、CPU/GPU完整回归|
|S2|gpt-6-luna / low，显式平台覆盖|固定首图命令，非零立即停，未继续23图|
|S3|gpt-6.1-sol / medium，显式平台覆盖|独立原PCD/墙体/非墙/射线残差复核及24图状态表|
|S4|gpt-6.1-sol / high，与S1不同Agent|Decimal/角点/32400射线独立复核、逐门FAIL总验收|

推荐沿TASK：Codex协调medium、固定执行Luna low、几何编码/独立验收Sol high；Claude Sonnet5.5对应medium/low/high备选，均为几何与证据复杂度需要，未实际派Claude执行。来源[SRC-1001](../../../SOURCES.md#src-1001)。

最终证据：[acceptance.json](../../../../results/task8/t8-voxfix-20261026/acceptance.json)、[账本](../../../../logs/task8/t8-voxfix-20261026/budget.json)、[保真检查](../../../../results/task8/t8-voxfix-20261026/preservation.json)、[父日志](../../../agent_logs/task8/task8.7/20261026-codex-coordination.md)。最终账本223.416167s/900s，剩676.583833s（包含开工90s保守计费），active为空；首图全部验证累计9.319208463s/30s。最终文档链接/来源锚点检查通过，GPU无compute，forem-dev仅保活sleep，HEAD未变；证据[parent-final-check.json](../../../../results/task8/t8-voxfix-20261026/parent-final-check.json)、账本1acc5afac2。[SRC-1005](../../../SOURCES.md#src-1005)、[SRC-1006](../../../SOURCES.md#src-1006)。未训练、未运行task7_lower/optimizer更新测试、未提交推送合并、未启停容器/他人进程。

剩余事项：现行world `[p,p+h)`归属不能覆盖首图负向旋转格点的末端整列，超出单纯边界舍入修复。待用户决定是否另行授权审查旋转格点到实体的重建协议/生成条件，再设计后续方案；本次不默认增加新功能、改资产或放宽墙门。24图运行及更广残差未验收，不能从本次单图推断SAC、语义任务或WM有效。

## 输入证据（执行前）

- 缺陷复算：[SRC-0999](../../../SOURCES.md#src-0999)，`forem/results/task8/t8-review-claude-20261026/`（严格floor：每图hole 23,620–57,748、射线穿墙4.6–8.0%；+1e-3后14/24图hole≤40）。这是Claude只读参照，不是本节点验收结果。
- 工程选择/预算：[SRC-1001](../../../SOURCES.md#src-1001)。

## 运行记录

以下保留S1–S4原始阶段记录，含RED、首轮回归失败与首图墙门失败。

### S2 首图受控执行（2026-10-26）

- 执行者：Codex子Agent，实际模型/强度：gpt-6-luna / low（显式指定）。仅在父级确认S1通过后执行`commands.json`的`jobs[0].argv`一次；父级仅放行`home_map_000`，其余23图未放行。
- 执行前账本：`limit_s=900.0`、`used_s=189.3349457476288`、`active={}`，余额710.6650542523712s（>179.5s）；首图授权字段为`parent_approved_first_map`。
- 原始job：`1bb65b0a7f`；外层`run_budget.py`退出码2，计费耗时4.119814422912896s，运行后余额706.5452398294583s，`active={}`；非零退出后立即停止，未执行余下23图。
- 机器记录：[原始账本记录](../../../../logs/task8/t8-voxfix-20261026/1bb65b0a7f.log)、[首图几何JSON](../../../../results/task8/t8-voxfix-20261026/map-diagnostics/home_map_000-geometry.json)、[首图NPZ](../../../../results/task8/t8-voxfix-20261026/map-diagnostics/home_map_000-geometry.npz)与[panorama NPZ](../../../../results/task8/t8-voxfix-20261026/map-diagnostics/home_map_000-panorama.npz)。JSON记录`status=geometry_checked`、`stage=geometry_complete`、`geometry_gate=failed_wall_holes`、`runtime_gate=not_run`；v1/v2 occupied分别84947/131445，`hole`分别29948/32、`holeXY`分别861/1；v2 `upper_clamped_count=0`。此处仅转录程序字段，不作根因判断或科学结论。
- 单图程序墙钟字段：JSON内仅有`max_wall_s=28.5`，未记录实际单图stage墙钟值；外层run-budget计时见上。原始attempt JSON与stderr/stdout记录见上述路径。结果待Sol复核；在收到父级明确指示前不重跑或继续。

## S3 固定24图清单与独立参照准备（尚未执行验证）

负责人Codex，实际gpt-6.1-sol / medium；推荐Codex GPT6.1sol medium、Claude Sonnet5.5 medium（几何/时序证据判断）；固定执行沿分工Luna low。授权、方法/预算见[SRC-1001](../../../SOURCES.md#src-1001)。

已准备[commands.json](../../../../logs/task8/t8-voxfix-20261026/commands.json)、v1原字节scene快照、新run map-index及正式入口`forem/scripts/task8_voxel_diagnostics.py`。独立5³ JSON参照不使用Claude bounds64；JSON不进入PCD scene。实际v1/v2完整PcdPanorama同历史默认初态位姿比较墙后>0.3m比例，逐对象匹配与残差证据留JSON/NPZ供后续S3判断。C后D同一单图命令累计限29.5s、内部28.5s；D复用原诊断runtime，不改采样/动作/奖励/IK。

清单待父亲读及S1放行：CPU、串行、首图后再决策；每命令使用新共享run_budget.py，余额须留150s给后续审查/保真核查。准备阶段仅静态读取/写代码，**syntax/24几何/24链路均尚未验证**，没有新增验证账本命令。细节与限制见[独立日志](../../../agent_logs/task8/task8.7/20261026-sol-s3.md)。后续必须亲读Luna原产物并完成残差分类，当前不作C/D通过结论。

## t8-voxfix-20261026 — S1 实施与测试（2026-10-26）

负责人Codex S1，实际平台`gpt-6.1-sol / high`（显式派发）；状态`review`，待父与独立S4核验。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为浮点边界/原域校验与版本联合核查；推荐不是Claude实际执行。本段仅S1交付，不替代C–F门。

授权协议依据[SRC-1001](../../../SOURCES.md#src-1001)。实际改动：scene以float64执行`floor((p-origin)/h+1e-3)`，先检查原半开域，再将合法上界进位截至shape−1；provenance新增`index_epsilon`与逐原始点`upper_clamped_count`；运行后端/环境/cache身份改v2。原PCD schema格式仍v1，manifest的geometry_backend v1/v2可读，均重新构建v2几何；新export/import标v2。其余仅必要版本行及测试证据输出移新run，ghost/碰撞算法/其他环境合同未改。

项目实测原证据：[SRC-1002](../../../SOURCES.md#src-1002)。

|阶段|账本ID / 原日志|退出码|墙钟s|结果|
|---|---|---:|---:|---|
|格点RED v1|[9275eea6d5](../../../../logs/task8/t8-voxfix-20261026/9275eea6d5.log)|1|3.418717|7 failed / 8 passed|
|格点GREEN v2|[a686fb6e25](../../../../logs/task8/t8-voxfix-20261026/a686fb6e25.log)|0|3.519107|15 passed|
|CPU原oracle回归|[cba99959ad](../../../../logs/task8/t8-voxfix-20261026/cba99959ad.log)|1|20.441895|95 passed / 11 skipped / 1 failed|
|独立差异复算|[b306f8fe7a](../../../../logs/task8/t8-voxfix-20261026/b306f8fe7a.log)|0|2.317315|随机point33进入ε带，v1/v2 cell与胶囊17距离差异解释原oracle失败|
|最终CPU全目录|[e3a1e8503a](../../../../logs/task8/t8-voxfix-20261026/e3a1e8503a.log)|0|20.341887|96 passed / 11 skipped|
|最终GPU0全目录|[85881b536f](../../../../logs/task8/t8-voxfix-20261026/85881b536f.log)|0|49.081659|107 passed / 0 skipped|

GPU前compute查询[885a011e17](../../../../logs/task8/t8-voxfix-20261026/885a011e17.log)为空（rc0、0.214366s），随后单卡串行。全部验证经[共享账本](../../../../logs/task8/t8-voxfix-20261026/budget.json)；S1累计99.334946s，此刻共享总189.334946/900s，剩710.665054s，后续以实时账本为准。未训练、未执行task7_lower或optimizer测试。

旧独立oracle仍strict-floor导致point33 x=0.14999584727454318从cell x102变x103，胶囊17最小距离平方0.0017833100970163459→0.00023019640906310989（半径平方0.0016）。经父追加授权，`test_scene.independent_cells`改为独立scalar math.floor按v2协议计算，保留随机采样、原碰撞断言及旧失败日志；不是修改碰撞算法或放宽断言。格点用例字面占据期望独立于该oracle。

交接产物：[完整diff](../../../../results/task8/t8-voxfix-20261026/s1-changes.diff)、[前后hash](../../../../results/task8/t8-voxfix-20261026/s1-changed-hashes.json)、[原文件](../../../../results/task8/t8-voxfix-20261026/s1-original/)、[点/胶囊差异](../../../../results/task8/t8-voxfix-20261026/s1-oracle-diagnostic.json)、[S1独立记录](../../../agent_logs/task8/task8.7/20261026-sol-s1.md)。新run的GPU/CPU几何与integration证据已落盘。

S3注意：旧map_diagnostics geometry阶段仍是v1参照，不可用作v2几何验收；runtime可沿用更新后的版本声明。task8_pcd_verify保持历史v1逻辑。C/D 24图尚由S3/S2执行，E最终零漂移由父核，F独立验收由S4核；S1不将A/B自报当本节点通过。没有持久化scene缓存加载API，现有cache_key以v2隔离；旧完整环境恢复仍一律拒绝。当前无S1运行任务；未提交、未推送、未合并。

## S3 首图独立复核与异常停止（review；C未通过）

实际gpt-6.1-sol / medium；推荐Codex GPT6.1sol medium、Claude Sonnet5.5 medium（逐图因果与原证据判断）。诊断合同[SRC-1003](../../../SOURCES.md#src-1003)，以下首图、独立局部PCD与非墙/扫描结论统一见[SRC-1004](../../../SOURCES.md#src-1004)，预算见[SRC-1005](../../../SOURCES.md#src-1005)。

父在S2首图rc2后停止后续执行；S3亲读原JSON/NPZ/ledger，不重复完整诊断。自写CPU复核不调用scene：逐点scalar math.floor结果完全等于原v2占据；独立125子样本和8角点确认缺洞参照成立。`75c23df373` rc0/3.168344094s；非墙/spur补查`e61fb5c8a2` rc0/.264512491s。与S2外层4.119814423s合计本图**7.552671009s≤30s**。原JSON实际记有geometry_elapsed_s=3.6394075966和total_elapsed_s=3.6457661269，纠正上方S2“未记录实际单图stage墙钟值”的转录；预算始终用外层ledger。

**C FAIL：** objects[4] `Wall_West:segment_0` / boxes[4]仍缺32格，zyx=[0..31,8,7]；world x[-4.65,-4.60]、y[-4.60,-4.55]、z[0,1.6]。原PCD此XY列0样本，自写原mapgen式格点/float32七位小数重建也0样本。长边沿负Y取样从4.6到约−4.55，世界[p,p+h)体素朝正Y延展，负Y末端一列欠覆盖；这是旋转采样与已批准表示的端点问题，非ε实现丢点、非JSON参照假洞。JSON未输入scene，未补PCD、未改参数或验收。

128个spur=4个全高列(x,y)=(6,192),(7,192),(192,192),(192,193)，最近OBB关联均为West/North/East墙，等距的两处保留多归属。17个非墙对象全部映射完整，逐对象hole=0且其一格扩展AABB内global spur=0，记录no_measured_residual；有旋转/半格属性不作为残差原因。逐对象记录见[补查JSON](../../../../results/task8/t8-voxfix-20261026/s3-residual-appendix.json)，只对本图/有限参照成立，不推广其余地图。

真实90×360 PcdPanorama原NPZ逐像素复数一致：总32400，eligible墙射线12890；v1深入墙后>0.3m为880/12890=6.8269977%，v2=16/12890=.12412723%（全部像素分母2.7160494%→.049382716%）。改善仍不满足墙类全占据门，不得表述为无穿墙。证据[独立复核JSON](../../../../results/task8/t8-voxfix-20261026/s3-first-review.json)、[S3日志](../../../agent_logs/task8/task8.7/20261026-sol-s3.md)。

D首图not_run；余23图C/D均not_run。逐图表如下，缺省值不得用Claude或旧v1结果填充；v1/v2数字均仅本run实际首图诊断。

|map-id|v1→v2 occupied|v1→v2 hole / holeXY|v1→v2 spur / spurXY|C|D|
|---|---:|---:|---:|---|---|
|home_map_000|84947→131445|29948/861→32/1|1963/66→128/4|FAIL（墙洞）|not_run|
|home_map_001|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|home_map_002|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|hospital_map_000|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|hospital_map_001|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|hospital_map_002|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|laboratory_map_000|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|laboratory_map_001|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|laboratory_map_002|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|library_map_000|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|library_map_001|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|library_map_002|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|office_map_000|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|office_map_001|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|office_map_002|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|restaurant_map_000|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|restaurant_map_001|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|restaurant_map_002|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|warehouse_map_000|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|warehouse_map_001|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|warehouse_map_002|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|workshop_map_000|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|workshop_map_001|not_run|not_run|not_run|not_run（首图阻断）|not_run|
|workshop_map_002|not_run|not_run|not_run|not_run（首图阻断）|not_run|

按TASK异常协议停止，未继续23图、未重领单图预算、未改生产算法/ε/判据。当前交付为**已执行C失败的证据与分类**，不是本节点完成；D未验收，独立S4及父按已执行A/B/C/合规复核。后续待用户决定是否另行授权研究格点/实体重建语义，或保留最小修复并明确墙门未通过；S3不自行实施新方案。无运行进程、无训练/optimizer测试、无提交/推送。

## S4 独立总验收 — FAIL（2026-10-26）

负责人为与S1不同的Codex S4，实际显式`gpt-6.1-sol / high`；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需联合核浮点几何、原产物与执行合规。亲读完整S1 diff、RED/GREEN/初失败与最终CPU/GPU原日志、Luna原JSON/NPZ/账本、S3自写参照与残差分类、父保真脚本/原输出。未将自报通过当总验收。

父放行后独立复核job[7df4ec767c](../../../../logs/task8/t8-voxfix-20261026/7df4ec767c.log) rc0，外层1.766537454s。自写Decimal直接解析133401原PCD点，v2完整占据逐格等于原NPZ（131445格）；缺32格的XY列确实0点，每格独立八角点均在墙盒内。另用世界AABB独立重算本图所有轴对齐墙的完整32400射线参照，与原expected/eligible一致，eligible12890，v1/v2墙后>0.3m计数880/16；没有调用生产scene或重render。S1当前13改动文件与12原副本hash一致。[独立证据](../../../../results/task8/t8-voxfix-20261026/s4-independent-evidence.json)、[完整S4日志](../../../agent_logs/task8/task8.7/20261026-sol-s4.md)。结论由父登记[SRC-1006](../../../SOURCES.md#src-1006)，原测量依据[SRC-1002](../../../SOURCES.md#src-1002)、[SRC-1004](../../../SOURCES.md#src-1004)、[SRC-1005](../../../SOURCES.md#src-1005)。

|门|最终判定|依据与限制|
|---|---|---|
|A RED→GREEN|PASS|v1原RED7fail/8pass、v2原GREEN15pass；字面占据与射线预期、上界计数/原域保护/中心点稳定有原证据|
|B 回归|PASS|最终CPU96pass11skip、GPU0107pass；初次旧floor oracle失败保留，必要更新经点33/胶囊17独立诊断支持，无放宽断言|
|C 24图几何|FAIL|首图Wall_West:segment_0缺32内部体素；余23图NOT_RUN，墙门未达成|
|D 24图链路|NOT_RUN|首图C硬门阻断，24图v2 runtime未执行；cube回归与历史v1结果不能替代|
|E 版本与哈希|PASS|v2版本/provenance/cache_key及旧完整环境拒绝；157冻结、48源、19342 mapgen/archive、289旧v1产物零漂移。没有持久化scene cache加载API；保真仅比既有枚举文件，不证明无新增文件|
|F 合规与独立总验收|FAIL|无训练/SAC更新PASS、预算PASS、不同S1的Sol high审查已执行；但“独立总验收通过”FAIL，不能因已审查就全PASS|

机读[acceptance.json](../../../../results/task8/t8-voxfix-20261026/acceptance.json)：总体**FAIL**。首图S2+S3+S4累计9.319208463s/30s；交接时账本223.051617883s/900，余676.948382117s、active={}。纠正S2转录：原JSON实际有geometry_elapsed_s3.6394075966/total_elapsed_s3.6457661269，计费始终按外层4.119814423s。无训练、未运行task7_lower/optimizer测试，未改生产协议/PCD/墙门，未提交推送。

本次S4审查完成不代表节点通过。task8.7不标done，父task8保持review；后续格点到实体重建语义/生成条件或验收范围须用户另行决定并授权。当前不继续余23图或runtime，不自动扩大ε/补PCD/训练。

## Claude复核（2026-10-26，claude-opus-5-5）

- 亲读父交接、S1 diff（`scene.py`仅改索引为`floor(·+1e-3)`、上界计数、版本/provenance；其余为版本行与测试）、acceptance.json、preservation.json（157/48/19342/289零漂移passed）与账本（223.42/900s，active空，14条命令无task7_lower/optimizer）。**同意S4判定：A/B/E PASS，C FAIL，D NOT_RUN，节点不通过**；停在首图并请用户决定的处理符合TASK异常协议。
- 成因复核：θ使格点沿世界负方向时样本代表`[p−h,p]`，ε规则的`[p,p+h)`归属在末端少一列，PCD无θ信息，属表示问题而非实现bug。
- 备选规则只读复算（[SRC-1020](../../../SOURCES.md#src-1020)）：“落在体素面上的点同时归属两侧体素”使24/24图墙类内部缺格为0、22/24图全部缺格为0（library_001剩33、workshop_001剩548，非墙），代价为网格面处≤1体素外扩（每图3千–1.9万格）。该方案未实施，待用户决定。

2026-10-26关闭交接：v3独立A–F通过后按授权关闭本节点，历史v2失败事实保留，见[task8.8 RESULTS](../task8.8/RESULTS.md)与[SRC-1089](../../../SOURCES.md#src-1089)。关闭文档维护推荐Codex GPT6.1sol/Claude Sonnet5.5 low（常规状态更新无特殊推理需求），父实际gpt-6.1-sol/medium承担整体核验；独立验收实际Sol high。未启动新运行或新增功能。
