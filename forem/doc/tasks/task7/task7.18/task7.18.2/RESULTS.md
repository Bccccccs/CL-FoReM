# task7.18.2 — 结果

当前状态：**review（r2多球修复已交、生产schema3已启用；329项全目录＋125项并发版本补验通过）**。当前run-id `t7.18.2-r2-20261021`，详文末第二轮；r1以下为历史记录。

历史r1状态：**review（部分交付；修复验收失败；生产启用与集成局部待决定）**。run-id：`t7.18.2-r1-20261021`，收尾时间2026-10-21T21:44:21.578043+08:00。本节替代原“尚未执行”，不标done，不恢复阶段L训练。[SRC-0540](../../../../SOURCES.md#src-0540)

## 目标、负责人和授权

任务`TASK7.18.2-SELFCOLL-FIX-20261021`，负责人Codex；实际GPT6.1sol / medium（宿主PID2980886的codex exec argv核实）。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium：需要几何/网格逐对及来源核对；推荐不等于执行。独立[日志](../../../../agent_logs/task7/task7.18/task7.18.2/20261021-codex-selfcoll-fix.md)。

授权按SRC-0906与本次派发：臂臂无20mm余量、默认零关节夹爪9-link胶囊、网格证实Always、同样本验收、GPU2目录测试/G1/E256对照。未改奖励、终止、动作、观测、IK、任何容差；无在线网格窄相位、训练重启、git提交、容器启停或非本任务进程停止。其他模块只读。根main/HEAD `cac6c15599efcbe47a1a7ed30f59a475e4997fd4 (host verified; uncommitted files separately hashed)`；既有未提交/并行工作保留。

## 结论与局部待决定

**当前全部约束同时执行时，候选FPR为100%，无法满足约6.9%的验收。** 所有13个真碰撞及上臂–顶板6次真实相交均检出，但全部375个网格无碰撞链式姿态也报警。不能把“全报警所以无FN”称可用修复。[SRC-0542](../../../../SOURCES.md#src-0542)

最小充分冲突：旧上臂胶囊＋20mm与顶板盒在388/388姿态重叠。要求臂车体包络不变、同时取消上臂–顶板整对豁免，就必然全部报警。新胶囊沿用旧allowed时仍复现原诊断B：39报警＝13真＋26纯FP，26/375＝6.933%；仅增加上臂–顶板检查即388报警。原约6.9%估计的前提明确是**旧允许表**，不适用于本任务新规则。[SRC-0542](../../../../SOURCES.md#src-0542)、[SRC-0544](../../../../SOURCES.md#src-0544)

**待决定，仅停止这部分**：在“臂车体包络不变、必须检查上臂顶板、不得用网格窄相位/新增未经验证豁免”限制下，现有外接包络无法达到目标；需要用户决定如何处理这些确定的包络假接触。本任务未自行改变任何一条限制，也未实施备选几何或额外豁免。

生产`robot_geometry.json`保持v1；已保存`robot_geometry_v1.json`，两者SHA256相同。候选版本`selfcoll-v2-20261021`只在[robot_geometry_v2.json](../../../../../results/task7/t7.18.2-r1-20261021/robot_geometry_v2.json)，未放入正式配置或训练元数据。可靠接入独立self几何还需要最小geometry/core/perception显式q接线与training版本字段；TASK将这些模块列只读，范围询问未获答复，未实施。本任务尚未交付可直接重训的修复。[SRC-0540](../../../../SOURCES.md#src-0540)

## 已实现、配置与不变量

|文件/产物|本次改动与状态|
|---|---|
|`src/task7_sim/robot.py`|复用原FK拆出`_transforms/_capsules`；`__call__`继续返回环境v1的8胶囊；增加显式q的`self_capsules/self_pair_contacts`与schema2自碰撞草稿；schema1行为不变；schema2缺q明确报错，不偷偷使用旧夹爪几何|
|`config/task7/robot_geometry_v1.json`|保存开工原配置；生产JSON最终与其字节哈希相同|
|run下`robot_geometry_v2.json`|16个self胶囊＝7个UR5＋9个夹爪；臂臂余量0；臂车体仍用原8胶囊（含单一夹爪并集）与8车体盒；版本与新self/arm-body允许表保存；旧Always明确标为v1历史字段|
|`src/task7_sim/tests/test_selfcoll_v2.py`|新增4项独立候选测试；不修改任何既有数值期望或失败阈值|
|`scripts/task7_selfcoll_*.py`|本任务构建/Always/逐姿态参考/组件审计/汇总/验收/回归/G1性能/完整性有界脚本；只读原诊断输入与网格|
|本节点三文档、独立日志、PROGRESS本行、[SRC-0540](../../../../SOURCES.md#src-0540)–0544|记录执行、失败、证据和待决定；不改父任务共享结论|

9-link在URDF零关节展开后的gripper_base坐标中分别沿原`fit_capsule`拟合；完整三角面顶点参与，未切片，不存在按顶点分组遗漏跨片三角面的处理。全顶点外接检查见[fit-audit](../../../../../results/task7/t7.18.2-r1-20261021/fit-audit.json)。旧环境源配置capsules/body/mesh_sources完全相同；GPU64和GPU32各512组随机底盘/q，以原`robot_v1.py`独立类逐元素比较环境胶囊、车体盒、臂车体原始接触矩阵，均`torch.equal`。另三个原数据集合共21278个q批量比较环境胶囊/车体盒相同。新允许表导致的报警变化单独计入，不混称包络未改。[SRC-0540](../../../../SOURCES.md#src-0540)

## 原姿态样本与逐对混淆

只重判原保存q，未运行新策略轨迹。输入仍为task7.18.1的chain.npz及sync/async playback.npz；执行尝试含失败候选，不回填成实际提交状态。自碰撞在base_footprint坐标计算，世界刚体变换不改变相交关系。完整参考、方法与相同样本索引见[summary](../../../../../results/task7/t7.18.2-r1-20261021/summary.json)、[完整性](../../../../../results/task7/t7.18.2-r1-20261021/verification.json)。[SRC-0544](../../../../SOURCES.md#src-0544)

|集合|N|v1 TP/FP/TN/FN|候选 TP/FP/TN/FN|候选FPR|
|---|---:|---|---|---:|
|链式IK|388|13 / 216 / 159 / 0|13 / 375 / 0 / 0|100.00%|
|同步执行尝试|1582|0 / 44 / 1538 / 0|0 / 1582 / 0 / 0|100.00%|
|不同步执行尝试|19308|0 / 21 / 19287 / 0|0 / 19308 / 0 / 0|100.00%|

逐对计数按同一姿态可多对相交；不能加总pair当姿态数。FPR＝FP/(FP+TN)，无真碰撞的FNR为N/A。下表列chain出现TP/FP/FN的全部对，其余被检查对为TN；所有被检查对（含旧Always对）的完整新旧TP/FP/TN/FN均在[chain CSV](../../../../../results/task7/t7.18.2-r1-20261021/pair-confusion-chain.csv)、[sync CSV](../../../../../results/task7/t7.18.2-r1-20261021/pair-confusion-sync.csv)、[async CSV](../../../../../results/task7/t7.18.2-r1-20261021/pair-confusion-async.csv)。保留物理相邻/same-link排除的对未冒充已做无限构型网格验收。

|chain几何对|TP|FP|TN|FN|
|---|---:|---:|---:|---:|
|ur5_base_link_inertia–ur5_upper_arm_link|0|388|0|0|
|ur5_shoulder_link–base_link|0|388|0|0|
|ur5_shoulder_link–top_plate_link|0|388|0|0|
|ur5_upper_arm_link–base_link|0|7|381|0|
|ur5_upper_arm_link–top_plate_link|6|382|0|0|
|ur5_upper_arm_link–velodyne2_base_link|2|6|380|0|
|ur5_forearm_link–ur5_wrist_2_link|0|30|358|0|
|ur5_forearm_link–ur5_wrist_3_link|0|13|375|0|
|ur5_forearm_link–gripper_base_link|7|24|357|0|
|ur5_forearm_link–base_link|0|7|381|0|
|ur5_forearm_link–front_left_wheel_link|0|6|382|0|
|ur5_forearm_link–top_plate_link|6|2|380|0|
|ur5_wrist_2_link–gripper_base_link|0|388|0|0|

原始网格参考沿task7.18.1的三角面距离、射线包含和密采样界，未替换为代理碰撞真值。对扩展新对的7个containment结果复用原独立连通组件＋三角面审计，纠正1项：同步pose1410 forearm–wrist2原单代表点包含为误判，组件不包含、表面距离0.013547487849719743m，最终分离。审计前副本与[审计差异](../../../../../results/task7/t7.18.2-r1-20261021/containment-audit.json)完整保留；不是生产FN，不影响原诊断未检查该Always对时的结论。没有修改原诊断产物或任何生产容差。[SRC-0544](../../../../SOURCES.md#src-0544)

字面[验收门](../../../../../results/task7/t7.18.2-r1-20261021/acceptance.json)实际退出1：样本齐全、13真检出、顶板6真检出三项满足；FP≤26不满足，实际FP375。原始[验收日志](../../../../../logs/task7/t7.18.2-r1-20261021/acceptance.log)。

## Always逐对证据

seed20261021，限位LOW/HIGH（rad）内独立均匀10000组，复用历史seed便于配对；输入[allowed-q.npz](../../../../../results/task7/t7.18.2-r1-20261021/allowed-q.npz)，哈希见fit-audit。所有新self对/臂车体对逐样本包络检查，[计数矩阵](../../../../../results/task7/t7.18.2-r1-20261021/screen-counts.json)。下表覆盖原8项非相邻Always。[SRC-0541](../../../../SOURCES.md#src-0541)

|原Always对|新包络接触/10000|新决定与网格证据|
|---|---:|---|
|base inertia–upper arm|10000|检查；q索引0网格采样距离下界0.006765041942422601m，分离|
|base inertia–top plate|10000|保留固定安装接触；两端URDF固定，相对变换10000样本元素差0；原始网格相交，刚性不变性覆盖10000/10000|
|shoulder–base|10000|检查；索引0原网格AABB严格分离，下界0.04645884253644944m|
|shoulder–top plate|10000|检查；索引0原网格AABB严格分离，下界0.022608842613190405m|
|upper arm–top plate|10000|必须检查；索引0网格相交、索引1网格AABB分离，下界0.028231692942827014m|
|forearm–wrist2|6363|检查；新原始外接胶囊已有3637组分离，不能是网格恒接触；同样本网格矩阵另附|
|wrist1–wrist3|0|检查；全部新外接胶囊分离，原网格也不可能全样本恒接触|
|wrist2–gripper|10000（掌部片即已恒重叠）|检查；索引0掌部原网格采样下界0.022800585255972942m，分离；不因包络重叠整组放行|

[always-audit.json](../../../../../results/task7/t7.18.2-r1-20261021/always-audit.json)记录6项仍为新包络Always的逐对mesh_queries、反例q和决定。拒绝项找到反例即停止，不虚报查完10000次网格或完整mesh接触比例；唯一保留对用URDF固定关系＋全样本相同相对变换证明，而非把活动关节采样冒充永恒证明。仅固定base inertia–top plate新增mesh Always保留，无Never排除。

原相邻关系保留。夹爪9片是原同一固定零开度夹爪并集的表示细化，内部仍按原same-link组排除；wrist3–夹爪保持原相邻group排除。没有把分片新引入的内部pair自动变成额外研究条件。早期r2曾审计这些内部pair，r3恢复原组语义，历史输出仍在always-r2.log。

## G1与E256对照

G1继续用原环境/传感器包络，不用self-only小胶囊替换遮挡体；原点仍(0,0,0.5m)。10000组中包络内原点3219组；候选经自碰撞/地面条件后合法0组，合法且inside 0组。合法子集归零来自新允许表误报，不是传感器改善。[SRC-0543](../../../../SOURCES.md#src-0543)

E256固定bench_full完整机器人/地图/扫描快照、零raw动作、float32 cuda:0（物理GPU2）；2次预热＋5次同步墙钟计时，Core/begin准备在步计时外。不含SAC或新训练。两档输入相同、无失败样本删除。[当前完整profile](../../../../../results/task7/t7.18.2-r1-20261021/profile-g1.json)，首轮[profile-g1-r1](../../../../../results/task7/t7.18.2-r1-20261021/profile-g1-r1.json)也保留。

|几何|p50 ms|p95 ms|含失败的动作转移/s|每批尝试子步|每批提交子步|每批自碰撞失败|
|---|---:|---:|---:|---:|---:|---:|
|v1|262.302|262.514|976.291|512|512|0|
|candidate-v2|68.172|68.258|3753.931|256|0|256|

**吞吐验收不可判通过**：候选所有行第一次检查就失败，实际提交工作量为0。调用更快不能作为性能提升或“不明显下降”的证据；当前候选不存在可用于相同有效执行工作的合法初态。共享主机有外部并行任务，结果也不作为训练工期承诺。私有OfflineRobot只在本脚本同步记录当前q以调用候选self判定，不是生产接口、未写Core/Truth/LocalCollision。[SRC-0543](../../../../SOURCES.md#src-0543)

## 全目录回归与失败记录

精确入口为`python3 -u forem/scripts/task7_selfcoll_run.py LABEL ...`；forem-dev、CUDA_VISIBLE_DEVICES=2、PYTHONPATH=/root/mm_husky_ws/src、OMP/MKL=2、禁写pyc、timeout590s。`task7_selfcoll_tests.py`为各目录启动独立pytest进程，GPU可选测试设TASK722_GPU=1（只控制opt-in，未选择GPU1；CUDA掩码始终2）。当前每项名称/耗时与断言结果在对应JUnit；目录源码before/after哈希在[tests-manifest](../../../../../results/task7/t7.18.2-r1-20261021/tests-manifest.json)。[SRC-0543](../../../../SOURCES.md#src-0543)

|目录|tests|failures|errors|skipped|JUnit|
|---|---:|---:|---:|---:|---|
|task7_sim|228|0|0|0|[XML](../../../../../results/task7/t7.18.2-r1-20261021/pytest-task7_sim.xml)|
|task7_lower|18|0|0|0|[XML](../../../../../results/task7/t7.18.2-r1-20261021/pytest-task7_lower.xml)|
|task7_upper|65|0|0|0|[XML](../../../../../results/task7/t7.18.2-r1-20261021/pytest-task7_upper.xml)|

新增4项分别核对：①GPU64/32环境/臂车体逐元素不变；②16片原顶点外接与只在self去20mm；③schema2必须显式q；④同6个上臂顶板真碰撞的该对检查开启。既有依赖数值断言改动**0条**。生产配置仍v1，目录通过属于现状回归＋独立候选接口测试，不能替代失败的v2 FPR验收。

执行中的失败均保留：

- `always`初版因覆盖gripper union字典后再索引其parts而IndexError退出1；修复保留原parts后重跑。r3保留原same-link/相邻组，实际Always审计退出0。
- `tests-all`默认合并目录同名测试模块冲突退出2；`tests-all-r2`的importlib模式不兼容既有本地test_core/test_env导入，也退出2。随后按既有每目录默认导入独立进程，不改测试源码规避。
- 首轮独立目录224+15+64通过、1项缺GPU opt-in跳过；最终补flag后重跑。第二轮sim226通过/1失败、lower18及upper65通过；运行中core.py外部并发变更，旧导入版本发生缓存所有权回归。当前core的单项重测1 passed，本任务未修改该文件；随后第三轮完整目录重跑，以本节最终JUnit为准。各轮XML/manifest以-r1/-r2保留。
- 新候选接触率验收命令退出1，属于真实未通过，未改期望使其变绿。新增测试在代码草稿之后补写，未声称满足PROCEDURE“先写失败测试”的时序。
- 宿主辅助统计曾无numpy退出1、汇总脚本async保留字SyntaxError退出1，改标准库/字典写法后成功；修改root产物的宿主尝试PermissionError退出1，改由容器内metadata命令成功。未安装依赖。

最终测试期间外部源码变化列表：`[]`；profile期间变化列表：`[]`。完整性/设备/源与产物SHA256见verification；如列表非空，不能声称这些外部最终文件已全部在同一静态版本测试。

## 实际命令、日志与预算

[完整argv账本](../../../../../logs/task7/t7.18.2-r1-20261021/commands.jsonl)逐条记录GPU compute核查、开始时间、真实退出码和墙钟。每LABEL的原始输出保存在同目录LABEL.log；所有CUDA均掩码2，其他GPU compute未当作GPU2占用，Xorg未当作占用。

|LABEL|退出码|容器调用墙钟s|
|---|---:|---:|
|build|0|7.381|
|always|1|9.920|
|always-r2|0|14.760|
|always-group-r3|0|11.017|
|chain|0|24.395|
|sync|0|106.193|
|async-0-5000|0|133.334|
|tests-all|2|2.236|
|tests-all-r2|2|2.425|
|tests-separate|0|243.800|
|profile-g1|0|6.359|
|async-5000-10000|0|147.599|
|async-10000-15000|0|133.782|
|async-15000-19308|0|115.417|
|containment-audit|0|80.743|
|tests-final|1|261.702|
|ownership-current|0|3.679|
|metadata|0|0.126|
|tests-final-r3|0|259.649|
|profile-g1-final|0|6.379|
|final-integrity|0|9.804|

总计1580.700s＝26.345min＜90min，最长261.702s＜600s。包含所有失败、重复和并行CPU审计各自墙钟，不把重跑成本删掉；该数不是全局顺序墙钟。宿主标准库summary退出0、acceptance退出1，日志另存acceptance.log，不伪装成容器/GPU工作。所有本任务容器命令均已退出，GPU2 compute收尾为空，未停止其他GPU或容器进程。

## 交接与限制

- 当前负责人Codex，状态review，交Claude核验本次**部分交付与局部规格冲突**，不发起额外文档复核轮次。先读本RESULTS、[SRC-0540](../../../../SOURCES.md#src-0540)–0544、acceptance、逐对CSV/JSONL与命令账本；实际生产仍v1，训练维持STOP。
- 已交付：v1保全、独立9-link/self无余量草稿、10000样本候选与Always反例、全部21278个原姿态的参考/混淆、G1、E256含失败对照、当前目录回归和设备/哈希核查。
- 待决定/未完成：解决“保持臂车体包络＋检查顶板”使FPR必为100%的局部冲突；明确最小q接线/元数据文件范围；再据授权落入生产配置并重新完成FPR与有效执行吞吐验收。不得从旧checkpoint连续训练，修复复核后从头重训须另派，本次未做。
- 限制：原静态q与离散检查、固定零开度夹爪、原网格数值方法和圆柱离散限制沿SRC-0531；没有真实硬件/ManiSkill、连续扫掠、其他夹爪开度或在线网格窄相位验收。没有成功率提升或训练工期结论。


# 第二轮 run-id `t7.18.2-r2-20261021`

状态：**review（r2实现、同样本验收、生产发布、全目录回归与完整性收尾已完成，交Claude核验）**。本节是第二轮事实来源，r1的失败与待决定保留为历史；第二轮新增授权已解决r1包络与q接线范围冲突。[SRC-0909](../../../../SOURCES.md#src-0909)

负责人Codex；实际GPT6.1sol / high（宿主codex exec PID3070869 argv核实）。推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high：完整三角面覆盖拟合、原网格证书及执行/推演q接线需跨模块核对；默认模型未切换、未派生Agent。本轮仅GPU2、追加7200s，单命令timeout590s；未提交Git、未改decision_env.py、未启动或恢复正式训练。

## r2验收与发布

同原始388/1582/19308个q重判，参考沿r1独立审计后的原网格分类；不是新策略回放或训练收益。9个gripper link聚合回原组之前，显式检查没有组内隐藏报警。[SRC-0547](../../../../SOURCES.md#src-0547)

|集合|N|TP|FP|TN|FN|FPR|
|---|---:|---:|---:|---:|---:|---:|
|chain|388|13|17|358|0|4.5333%|
|同步执行尝试|1582|0|0|1582|0|0.0000%|
|不同步执行尝试|19308|0|0|19308|0|0.0000%|

上臂–顶板该对**TP6/FP0/TN382/FN0**；13个原真碰撞姿态全部检出，FPR17/375=4.5333%＜6.9%。逐对全表：[chain](../../../../../results/task7/t7.18.2-r2-20261021/pair-confusion-chain.csv)、[sync](../../../../../results/task7/t7.18.2-r2-20261021/pair-confusion-sync.csv)、[async](../../../../../results/task7/t7.18.2-r2-20261021/pair-confusion-async.csv)；[汇总](../../../../../results/task7/t7.18.2-r2-20261021/summary.json)、pairs-*.npz、reference-*.jsonl保留每pose/pair。各pair真/假接触可能属于同一姿态，不能相加当独立姿态。

生产已切schema3：`selfcoll-multisphere-v3-20261021`，**1234个self球**；旧`robot_geometry_v1.json`原字节保留，r1候选schema2仍留旧run与旧回归。生产SHA256 `62f5c1361ec0f918cbdd4f5ae0a58df938168c82b284398bf977e7eca292fa5a`。训练输入`lower_train.json`加入robot_geometry_version/sha256/config，既有训练代码原样把整个config写config.json和full-checkpoint.config，且env.robot.data也包含版号；本次没有为了写元数据启动训练。[发布记录](../../../../../results/task7/t7.18.2-r2-20261021/publication.json)。[SRC-0548](../../../../SOURCES.md#src-0548)

## r2三角面包络与拟合质量

读取原collision STL及URDF origin/scale，先把跨切片三角面完整裁成凸多边形，再外接各片；球凸性保证每片所有面被覆盖，不只按原顶点分组。全部片顶点最大覆盖超差为0，另检查全部原顶点与≤4mm面采样。self余量0，半径只作浮点向外nextafter。UR5e参考数量只作起点，不复制其坐标/余量；TopAY只借零位球重叠分类。[SRC-0545](../../../../SOURCES.md#src-0545)

|原link|球数|cuRobo UR5e数量起点|球并集体积/网格体积代理|采样外凸距离上界 mm|solver非success片数|
|---|---:|---:|---:|---:|---:|
|ur5_base_link_inertia|1|—|9.397|83.512|0|
|ur5_shoulder_link|1|1|1.921|31.452|0|
|ur5_upper_arm_link|8|8|1.581|47.982|0|
|ur5_forearm_link|512|9|1.087|19.871|67|
|ur5_wrist_1_link|256|4|1.017|12.934|42|
|ur5_wrist_2_link|256|4|1.023|13.021|41|
|ur5_wrist_3_link|128|1|1.513|12.868|14|
|gripper_base_link|16|—|2.446|21.793|0|
|gripper_finger1_knuckle_link|4|—|3.281|9.759|0|
|gripper_finger2_knuckle_link|4|—|3.283|9.696|0|
|gripper_finger1_finger_link|8|—|3.199|7.812|1|
|gripper_finger2_finger_link|8|—|3.198|7.861|0|
|gripper_finger1_inner_knuckle_link|8|—|7.720|17.197|2|
|gripper_finger2_inner_knuckle_link|8|—|7.710|17.137|0|
|gripper_finger1_finger_tip_link|8|—|2.726|8.546|2|
|gripper_finger2_finger_tip_link|8|—|2.729|8.622|0|

[逐片审计/源哈希](../../../../../results/task7/t7.18.2-r2-20261021/fit-audit.json)。上臂8球用轴向三角面裁切，其余空间细分。SLSQP有169片未返回success，最终仍按该中心重新取足以覆盖全部片顶点的半径，再实际验证覆盖；不声称这些球或全球集最优。表中体积是65536点Sobol球并集估计除以带符号三角积分代理，未做精确实体布尔体积；采样外凸是每球1024表面方向到面密样点的距离上界，不是全表面最大值。另在JSON逐link给2×最大球半径的保守全局上界；全面覆盖证明只对原三角面，不宣称任意实体内部包含或连续扫掠完整性。[SRC-0545](../../../../SOURCES.md#src-0545)

负候选与选型：首版轴向球FP139；较粗空间球FP342；上臂空间32球导致顶板误报，混合后FP45；前臂细到512、腕128/128/64为FP27；把上臂轴向细到32反而产生顶板376次FP（整姿态FP370），未采用。最终保留上臂8、前臂512、腕256/256/128，夹爪各link16/4/4/8/8/8/8/8/8，FP17。多球/切片数增加并不单调缩小并集；调整依据与失败日志都保留，未新增放行或阈值迎合验收。链式样本用于拟合选择，4.53%不是独立泛化结果。

## r2放行表：每对10000原网格核实

按用户TopAY式**零位球重叠**规则，和相邻/固定安装分类，最终25对；零位球重叠不是零位网格真接触，更不是恒接触证明。上臂–顶板始终检查。动态对每q都保留原三角交叉/支持分离平面或完整参考；连通组件凸包分离只作充分分离证明，凸包重叠不会被当作网格接触。固定对由有效活动关节路径一致＋10000相对变换不变（误差≤1e−12）与一次原始网格查询推出全部，同时报告queries=1。[SRC-0546](../../../../SOURCES.md#src-0546)

|pair（self_names扩展body索引）|link A / B|类别|网格接触/10000|刚性相对变换|
|---|---|---|---:|---|
|0,1|ur5_base_link_inertia / ur5_shoulder_link|adjacent|10000|变化|
|0,2|ur5_base_link_inertia / ur5_upper_arm_link|zero_sphere_overlap|412|变化|
|0,16|ur5_base_link_inertia / base_link|adjacent|0|固定|
|0,21|ur5_base_link_inertia / top_plate_link|fixed_installation|10000|固定|
|1,2|ur5_shoulder_link / ur5_upper_arm_link|adjacent|0|变化|
|1,21|ur5_shoulder_link / top_plate_link|zero_sphere_overlap|0|变化|
|2,3|ur5_upper_arm_link / ur5_forearm_link|adjacent|10000|变化|
|3,4|ur5_forearm_link / ur5_wrist_1_link|adjacent|10000|变化|
|4,5|ur5_wrist_1_link / ur5_wrist_2_link|adjacent|0|变化|
|5,6|ur5_wrist_2_link / ur5_wrist_3_link|adjacent|0|变化|
|6,7|ur5_wrist_3_link / gripper_base_link|adjacent|10000|固定|
|7,8|gripper_base_link / gripper_finger1_knuckle_link|adjacent|10000|固定|
|7,9|gripper_base_link / gripper_finger2_knuckle_link|adjacent|10000|固定|
|7,12|gripper_base_link / gripper_finger1_inner_knuckle_link|adjacent|10000|固定|
|7,13|gripper_base_link / gripper_finger2_inner_knuckle_link|adjacent|10000|固定|
|8,10|gripper_finger1_knuckle_link / gripper_finger1_finger_link|adjacent|10000|固定|
|8,12|gripper_finger1_knuckle_link / gripper_finger1_inner_knuckle_link|zero_sphere_overlap|0|固定|
|9,11|gripper_finger2_knuckle_link / gripper_finger2_finger_link|adjacent|10000|固定|
|9,13|gripper_finger2_knuckle_link / gripper_finger2_inner_knuckle_link|zero_sphere_overlap|0|固定|
|10,12|gripper_finger1_finger_link / gripper_finger1_inner_knuckle_link|zero_sphere_overlap|0|固定|
|10,14|gripper_finger1_finger_link / gripper_finger1_finger_tip_link|fixed_installation|10000|固定|
|11,13|gripper_finger2_finger_link / gripper_finger2_inner_knuckle_link|zero_sphere_overlap|0|固定|
|11,15|gripper_finger2_finger_link / gripper_finger2_finger_tip_link|fixed_installation|10000|固定|
|12,14|gripper_finger1_inner_knuckle_link / gripper_finger1_finger_tip_link|adjacent|10000|固定|
|13,15|gripper_finger2_inner_knuckle_link / gripper_finger2_finger_tip_link|adjacent|10000|固定|

[完整25对审计](../../../../../results/task7/t7.18.2-r2-20261021/allowed-audit-final-v3.json)、[独立参考/URDF路径复核](../../../../../results/task7/t7.18.2-r2-20261021/allowed-independent-verification.json)、allowed-pair-*-certificates.npz及其JSON。动态对另以64或更多原完整参考查询抽核，结果一致。

**实质限制**：base–upper因零位球重叠被允许，但原网格零位分离，10000组里实际有412次网格接触；此表按用户规则屏蔽这些接触，不能称整个限位域安全或零漏检。当前388样本该对无真实接触，13/13检出仅限本样本被检查对。其他0/10000的许可对也不包装成恒接触。早期8717次直接查询与两轮TIME_BOUND都是未完成历史，不冒充25对全完成；最终组件证书审计约102s完成且有独立原参考复核。

## r2接线、环境/渲染不变量与性能

本任务对`core.py`只有`Core.step`两行局部修改：显式传ik.q到碰撞；未改其余函数。启动时快照至今还包含task7.22在其他Core函数的并行route-raster改动，均保留，不能把整文件diff称本任务改动；[本任务step补丁](../../../../../results/task7/t7.18.2-r2-20261021/core-step-only.patch)与[包含并行内容的总diff](../../../../../results/task7/t7.18.2-r2-20261021/core-vs-start-with-parallel.patch)区分记录。`geometry.py::TruthCollision.__call__`、`perception.py::LocalCollision.__call__`最小q接线。旧episode/g7直接调用以每个caps值拥有的q快照兼容，不用共享last-q；显式q优先，复制丢失q后必须显式传入。render/risk仍拿旧8胶囊和原车体盒。[SRC-0548](../../../../SOURCES.md#src-0548)

环境参数（capsules/body/mesh_sources/URDF hash）逐字段相同；所有21278原q的环境胶囊/车体盒逐元素相同。CPU64/GPU64/GPU32各128姿态的Truth/Local环境base/arm与各2姿态全部Depth字段，和开工前源快照逐元素一致：[环境不变量](../../../../../results/task7/t7.18.2-r2-20261021/environment-invariance.json)。没有改变环境0.02m、floor、机器人尺寸或原点。

每簇≤16球的保守世界AABB仅裁掉不可能相交的簇，最终仍同一个球–球/球–盒精确比较，无线上网格窄相位。与无裁剪版本GPU64/32各10000姿态、CPU64 512姿态比较0差异：[等价](../../../../../results/task7/t7.18.2-r2-20261021/cluster-equivalence.json)。首版未分组时E256慢约6.5%，因此落实这一纯几何加速。[SRC-0549](../../../../SOURCES.md#src-0549)

|几何|p50 ms|p95 ms|动作转移/s|尝试/提交子步（每批）|self失败|
|---|---:|---:|---:|---|---:|
|v1|263.041178|263.466384|973.080008|512/512|0|
|v3|264.669616|264.913481|967.097881|512/512|0|

最终p50+0.619%、吞吐−0.615%，同有效工作量下接近v1；没有把早停当加速。两版最终base/q/s/reward/reason/committed逐元素相同。协议为同bench_full快照、GPU2 float32、2预热＋7次同步墙钟，准备/begin不计入步计时；实际设备cuda:0对应物理GPU2，外部GPU1任务并行。[最终profile/G1](../../../../../results/task7/t7.18.2-r2-20261021/profile-g1.json)，[未分组负对照](../../../../../results/task7/t7.18.2-r2-20261021/profile-g1-before-clusters.json)。该批前后源hash无变化，且最终现行代码hash相同。未作训练工期承诺。

G1同10000 q：原点仍(0,0,0.5m)，旧环境胶囊inside3219；新self＋旧floor合法2460，其中826仍inside。G1风险保留，未用self小球替换自遮挡体或移动传感器。[SRC-0549](../../../../SOURCES.md#src-0549)

## r2回归、异常与预算

最终全目录GPU回归已完成：sim241、lower18、upper70，共329 passed，无fail/error/skip；三目录按原导入规则分进程，TASK722_GPU只启用测试、物理GPU仍2。源码before/after无变化。首次定向10 passed/2 failed，完整首轮sim240 passed/1 failed、lower18 passed、upper69 passed，源before/after无变化；失败分别保存在tests-geometry-green与tests-all-production日志及JUnit.first-failed。

旧几何期望逐条修订（不改输入）：①q=[0,−1,1,−0.5,1,0] self True→False，原腕1–夹爪网格AABB分离26.7876mm；②elbow_fixture self False→True，此为保守FP，原先“包含”被独立组件＋三角面距离纠正为False，实际间隙3.24548mm，不称真碰撞；③同一q平移±1.5m端点旧全旗标False改为(base=False,arm=False,self=True)，环境清空含义仍检查。另有一处纯q接口适配：人工下移的caps.clone丢失元数据，显式传原q来只测试环境floor；生产不增加last-q兜底。[夹具原网格证据](../../../../../results/task7/t7.18.2-r2-20261021/test-expectation-evidence.json)，[SRC-0548](../../../../SOURCES.md#src-0548)。

异常保留：GPU bool scatter_reduce不支持，审计聚合改int32后修复；宿主summary cwd错、旧reference完成行误沿用到新hit列均有失败/纠正重跑；初次快照模块少__file__失败，补正确源文件身份后3设备不变量通过；肘部最初包含结论未经三角面相交证实，独立组件审计纠正；SLSQP非success片按重新取覆盖半径处理；不把任何失败删账或写成验收通过。

本轮所有容器计算命令从`task7_selfcoll_run.py`进入，SELFCOLL_RUN=t7.18.2-r2-20261021、SELFCOLL_BUDGET_S=7200；forem-dev、CUDA_VISIBLE_DEVICES=2、OMP/MKL=2、PYTHONPATH、禁pyc、timeout590s。每次只用compute-apps判断GPU2占用，Xorg不算。[完整argv/退出码/累计墙钟](../../../../../logs/task7/t7.18.2-r2-20261021/commands.jsonl)；逐LABEL.log保留原输出。预算是各调用墙钟之和（并行也各计），不是理论GPU工期；全局本轮时间另由本日志时间戳界定。

## r2交接

当前负责人Codex；状态review，交Claude按原证据核验。目标/授权为SRC-0909及本轮派发；生产新版本已发布，旧v1保留，formal-sync/async STOP不得移除。本次不重启训练、不提交Git、不停止外部进程，下一步仅Claude核验以上原证据，之后是否从头重训另派。

最终测试、命令表、完整性和GPU2资源收尾均已登记；已知限制包括本样本拟合选择偏差、允许base–upper的412次网格接触、旧肘部夹具的保守FP、原网格/圆柱离散参考误差、固定开度与离散q、实体包含与连续扫掠未作一般证明。未承诺消除所有自碰撞误报或提升任务成功率。


### r2最终测试与并发版本补验

|完整目录|tests|failures/errors/skipped|证据|
|---|---:|---|---|
|task7_sim|241|0/0/0|[JUnit](../../../../../results/task7/t7.18.2-r2-20261021/pytest-task7_sim.xml)|
|task7_lower|18|0/0/0|[JUnit](../../../../../results/task7/t7.18.2-r2-20261021/pytest-task7_lower.xml)|
|task7_upper|70|0/0/0|[JUnit](../../../../../results/task7/t7.18.2-r2-20261021/pytest-task7_upper.xml)|

完整329项是同一轮已结束的GPU目录回归，源未在该轮内改变。之后task7.22又改`decision_env.py`（本任务未改）：48e2599ff437339df0735675904f4e6161ed8b35e798edae0526e02d51e48bb8 → b7669f66bceb589950cb3a0e953201d7a569865cba14744c962ba4ac79c4c247。首轮final-integrity据此拒绝当前源hash新鲜度（退出1），没有覆盖对方代码或把旧通过当新通过。随后对全部直接引用DecisionEnv的sim测试、完整几何/多球回归及上下层全目录补验：37＋18＋70＝125 passed，无fail/error/skip，补验前后源不变；[补验manifest](../../../../../results/task7/t7.18.2-r2-20261021/post-test-revalidation.json)与post-tests-*.xml、[外部差异](../../../../../results/task7/t7.18.2-r2-20261021/post-tests-external-changes.json)。最终完整性接受这一明确的版本补验链，未篡改329项原manifest。E256路径不调用decision_env，Core/robot/kinematics/perception/motion/risk实际执行依赖hash仍相同；此差异另存verification。

新增4项回归核对原13真/6顶板真及FP门、显式Truth/Local q一致、交错调用与调用者原地改q不污染旧caps、失去q快照且无显式q时拒绝。期望只在test_full_geometry的上述三处布尔值改动，另地面人工clone的调用补显式q；test_selfcoll_v2未改，lower/upper代码与测试未改。现有pytest record_property警告和lower两种Torch警告保留，没有为消警告改算法。

### r2最终命令账本与交接完整性

|LABEL|退出码|容器墙钟s|
|---|---:|---:|
|red-multisphere|1|3.272|
|build-multisphere|0|12.526|
|allowed-init|0|15.738|
|allowed-init-r2|0|15.847|
|chain-v3|1|8.142|
|chain-v3-r2|0|8.577|
|build-multisphere-cells|0|14.324|
|allowed-init-cells|0|15.693|
|chain-cells|0|8.541|
|chain-cells-current|0|8.622|
|build-multisphere-dense|0|18.636|
|allowed-init-dense|0|15.765|
|chain-dense|0|8.846|
|build-multisphere-hybrid|0|20.675|
|allowed-init-hybrid|0|15.827|
|allowed-audit-01|0|481.950|
|chain-hybrid|0|8.702|
|build-multisphere-forearm512|0|28.465|
|allowed-init-forearm512|0|15.842|
|chain-forearm512|0|8.899|
|allowed-fast-01|0|481.966|
|build-multisphere-upper32|0|29.245|
|allowed-init-upper32|0|15.742|
|allowed-components-01|0|101.550|
|allowed-fast-dense|0|481.959|
|chain-upper32|0|9.166|
|build-multisphere-wrists|0|31.158|
|allowed-init-wrists|0|15.983|
|chain-wrists|0|9.105|
|finish-final-table|0|0.115|
|profile-v1-v3|0|10.922|
|matrix-sync|0|11.118|
|cluster-equivalence|0|22.129|
|matrix-async|0|40.789|
|invariants|1|1.855|
|profile-clusters|0|10.119|
|verify-allowed-mesh|0|41.553|
|invariants-r2|0|4.181|
|tests-geometry-green|1|17.418|
|fixtures-evidence|0|7.453|
|fixtures-exact-confirm|1|7.615|
|fixtures-component-confirm|0|7.611|
|tests-all-production|1|360.511|
|tests-all-final|0|361.647|
|final-integrity|1|7.622|
|post-tests-revalidate|0|164.116|
|final-integrity-r2|0|8.029|

本轮累计**2995.565432s＝49.926091min＜120min**，47条容器计算命令；最长481.966198s＜600s，含红测、失败、未完成TIME_BOUND、重复与并行各调用墙钟。最后final-integrity-r2退出0；[verification](../../../../../results/task7/t7.18.2-r2-20261021/verification.json)逐项核对生产/config元数据、v1原字节、25对10k、全部参考集合、329/125回归版本链、E256有效工作量和hash，给acceptance=true；[资源收尾](../../../../../results/task7/t7.18.2-r2-20261021/resource-final.json)时间2026-10-21T22:57:07.086249+08:00，GPU2无compute，formal-sync/async STOP均在。其他GPU/用户进程保留；本任务没有后台计算，故无需停止或恢复命令。本run自己的容器产物已恢复宿主uid/gid1004所有权，未处理其他run。

实际修改限于robot/geometry/perception与Core.step、robot_geometry.json、lower_train.json、自己的测试/脚本/日志/三文档/本行PROGRESS和SRC-0545–0549。Core其他变化属于7.22，decision_env仅只读与补验，未覆盖。生产发布的宿主操作为：读最终robot_geometry_v3.json，保留数值字段并标注fit/provenance_sources/mesh_coverage，写robot_geometry.json并计算SHA256，向原lower_train.json追加三字段，保存publication.json；原训练代码和已存在formal配置/检查点均未改。

交接已完成，当前review；下一步Claude先读本节、SRC-0545–0549及verification/逐对表，核验几何许可的适用限制，再由用户另行派发是否从头重训。本次不启动训练，也不把旧v1 checkpoint作为v3连续训练证据。模型/强度推荐仍Codex GPT6.1sol / high、Claude Sonnet5.5 / high，实际本次Codex配置已核实。

## Claude复核 t7.18.2-r2（2026-10-21T23:00–23:10，claude-opus-5-5，推理强度未知）

- 读RESULTS：FPR 4.53%、13/13真碰撞与顶板6/6检出、329＋125项测试通过、臂/底盘–环境与渲染逐元素不变、E256耗时＋0.62%；拟合按三角面裁片外接球、全片覆盖超差0；25对放行逐对网格证书。
- 问题：TopAY零位重叠规则被实现为连杆对级，base_inertia–upper_arm整对放行屏蔽412/10000网格接触。TopAY原实现为球对级（moma_param.h:128–143）。用户决定改球对级（SRC-0910）→ r3。其余可接受。


## r3开工阻塞：来源编号无剩余（2026-10-21T23:03:56.234550+08:00）

run-id：`t7.18.2-r3-20261021`。负责人Codex；状态blocked，**修复和验证尚未执行**。实际模型GPT6.1sol / high（派发进程3153672 argv核实）；复核推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high，理由为球对豁免语义与原网格混淆统计核查。

目标与授权：[SRC-0910](../../../../SOURCES.md#src-0910)决定零位球重叠仅豁免球对；其他类别不变。第三轮另要求只用GPU2、单命令≤10min、累计容器计算≤60min；core.py不再改、不启动训练、不提交Git、不停止其他任务进程。

实际开工核查：原始TopAY `moma_param.h:128–143`的collision_matrix按球索引初始化，与SRC-0910描述一致；已读r2复核。**用户明确规定“SOURCES只用SRC-0545–0549剩余编号（不够则停下报告）”，而这五个编号已全部用于r2，剩余0个**：[拟合0545](../../../../SOURCES.md#src-0545)、[放行0546](../../../../SOURCES.md#src-0546)、[混淆0547](../../../../SOURCES.md#src-0547)、[回归0548](../../../../SOURCES.md#src-0548)、[性能0549](../../../../SOURCES.md#src-0549)。故按该明确条件停止实施，没有覆盖稳定编号，也没有自行向r2条目加入r3证据。

本run代码/配置/测试修改：无；容器计算：尚未执行，0s；新10k/388/sync/async混淆、零位附近误报、全目录GPU测试、schema/名称递增、训练元数据：均尚未执行。生产仍是r2，不把其旧结果称为r3通过；其base–upper整对放行问题仍未修复。GPU1已有task7.22计算，未干预。

交接：原日志已续写，PROGRESS仅本行登记active→blocked。剩余为全部第三轮实施与验证。下一步需要提供可用来源编号，或明确允许保留既有r2条目并追加r3分节；明确后按原范围继续。当前无本任务后台程序，不需要停止或恢复命令。


## r3编号更正后续接（2026-10-21T23:15:50.200530+08:00）

原编号阻塞已由用户明确更正解除，改用预留SRC-0560–0569；延续run-id `t7.18.2-r3-20261021`，不重做r2已完成核查。当前负责人Codex，状态active；实际GPT6.1sol / high（派发PID3160481 argv），推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high，因球对许可语义和原网格混淆核查需要高强度。

球对实现与schema4已落地，10k/近零探针/同388与sync/async静态复判已完成，数值见[SRC-0560](../../../../SOURCES.md#src-0560)、[SRC-0561](../../../../SOURCES.md#src-0561)、[SRC-0562](../../../../SOURCES.md#src-0562)。完整GPU回归仍在运行，最终测试、性能、元数据与完整性尚未完成，不把定向6项通过当作全目录通过。完整交接与新证据表在本run完成后追加；预算累计账本为`forem/logs/task7/t7.18.2-r3-20261021/commands.jsonl`。core.py开工hash一致、不训练、不提交、不停止其他进程。


## r3最终交付：球对级零位许可（2026-10-21T23:22:50.785346+08:00）

run-id **`t7.18.2-r3-20261021`**；负责人Codex；状态**review**，交Claude复核。编号更正已解除原阻塞，实际仅新用SRC-0560–0564，未占用0565–0569、未复用r2编号。实际模型**GPT6.1sol / high**（本轮codex exec PID3160481 argv核实）；复核推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high，理由为具体球索引mask、原网格混淆和裁剪等价需交叉核查。授权为[SRC-0910](../../../../SOURCES.md#src-0910)及本轮派发，不含训练。

### 修改和版本

仅零位重叠类别由整连杆对改为具体primitive对豁免，构建时float64零位严格`dist < r_i+r_j`；运行碰撞仍用原包含相切的`<=`。旧相邻和固定安装类别仍按连杆对放行。原1234球坐标/半径、8环境胶囊、车体盒、self余量0与其他科学条件未变。core.py与开工字节hash相同，geometry.py/perception.py/IK/训练代码本轮未改。[SRC-0560](../../../../SOURCES.md#src-0560)

- base–upper只豁免球索引(0,8)、(0,9)，其余6/8组合照常检查。
- 肩–顶板已有表示仅1个肩球–1个盒，按具体索引(1,5)豁免该组合，未将车体改球化。
- 夹爪4个原零位类别分别豁免2/32、2/32、4/64、4/64个球组合；其他组合继续检查。总14球对＋1球–盒对。

生产版本**schema4 / `selfcoll-multisphere-v4-spherepairs-20261021`**，SHA256 `6c41120ad85bdea61a24b1089e825febf4f6b62eb93da0474e51f386167b084a`；`lower_train.json`三几何元数据更新，JSON和内存torch配置序列化读回相等，既有full checkpoint代码保存完整config。未生成训练检查点、未回填旧训练产物；v1和本轮前v3快照均保留。全目录测试后仅补审计指针/来源说明三个字段，[geometry-tested-before-metadata.json](../../../../../results/task7/t7.18.2-r3-20261021/geometry-tested-before-metadata.json)保留被测数值配置，完整性确认mask及几何不变。[SRC-0563](../../../../SOURCES.md#src-0563)，[publication.json](../../../../../results/task7/t7.18.2-r3-20261021/publication.json)、[metadata-readback.json](../../../../../results/task7/t7.18.2-r3-20261021/metadata-readback.json)。

实际改动文件：`forem/src/task7_sim/robot.py`（零位primitive mask与裁剪/未裁剪一致接口）、`tests/test_selfcoll_multisphere.py`（schema3→4及2个球对回归）；`forem/config/task7/robot_geometry.json`、`lower_train.json`；9个`forem/scripts/task7_selfcoll_spherepairs_*.py`；本节点三文档、原Agent日志、PROGRESS本行、SOURCES0560–0564与DECISIONS用户决定补登记。没有修改其他任务源码或参考仓库。[robot-r3.patch](../../../../../results/task7/t7.18.2-r3-20261021/robot-r3.patch)记录相对r2源码差异。

### 同10000 q：全部原零位类别

使用r2已核实的同10000 q和原网格证书，未重做r2拟合/三角网格核查；按新mask重算完整逐q矩阵，动态对采用已核实逐q证书，夹爪刚性对采用原网格结果和全部相对变换相同证明。TP/FP/TN/FN按原网格接触为真值。[SRC-0561](../../../../SOURCES.md#src-0561)

|原零位类别|豁免/总primitive对|TP|FP|TN|FN|
|---|---:|---:|---:|---:|---:|
|ur5_base_link_inertia–ur5_upper_arm_link|2/8|412|1850|7738|0|
|ur5_shoulder_link–top_plate_link|1/1|0|0|10000|0|
|gripper_finger1_knuckle_link–gripper_finger1_inner_knuckle_link|2/32|0|0|10000|0|
|gripper_finger2_knuckle_link–gripper_finger2_inner_knuckle_link|2/32|0|0|10000|0|
|gripper_finger1_finger_link–gripper_finger1_inner_knuckle_link|4/64|0|0|10000|0|
|gripper_finger2_finger_link–gripper_finger2_inner_knuckle_link|4/64|0|0|10000|0|

base–upper原412次真接触全部恢复检出，r2该对整对豁免为FN412，本轮FN0；但FP1850，**FPR=1850/9588=19.294952%**，如实保留，不新增豁免。这是限位内均匀q的该对FPR，不能替代正常任务分布。[10000-confusion.json](../../../../../results/task7/t7.18.2-r3-20261021/10000-confusion.json)、[10000-pairs.npz](../../../../../results/task7/t7.18.2-r3-20261021/10000-pairs.npz)、[zero-pair-audit.json](../../../../../results/task7/t7.18.2-r3-20261021/zero-pair-audit.json)；继承证据SHA登记在[verification.json](../../../../../results/task7/t7.18.2-r3-20261021/verification.json)。

正常零位附近探针：shoulder_pan单独−0.1至+0.1rad、shoulder_lift单独同范围，步长0.001rad，各201（零位重复），其余q=0。原6对均TP0/FP0/TN402/FN0，没有在本批观察到新增误报；有限探针不能证明连续邻域无误报。逐轴明细和原q见[near-zero-confusion.json](../../../../../results/task7/t7.18.2-r3-20261021/near-zero-confusion.json)、[near-zero-pairs.npz](../../../../../results/task7/t7.18.2-r3-20261021/near-zero-pairs.npz)。该扫描为有界工程核查，不将范围称为文献推荐或平台通用阈值。[SRC-0561](../../../../SOURCES.md#src-0561)

### task7.18.1同样本全表与总FPR

|原样本|N|TP|FP|TN|FN|姿态FPR|逐对完整83行表|
|---|---:|---:|---:|---:|---:|---:|---|
|chain|388|13|17|358|0|4.533333%|[pair-confusion-chain.csv](../../../../../results/task7/t7.18.2-r3-20261021/pair-confusion-chain.csv)|
|sync|1582|0|0|1582|0|0.000000%|[pair-confusion-sync.csv](../../../../../results/task7/t7.18.2-r3-20261021/pair-confusion-sync.csv)|
|async|19308|0|0|19308|0|0.000000%|[pair-confusion-async.csv](../../../../../results/task7/t7.18.2-r3-20261021/pair-confusion-async.csv)|

13个原网格真碰撞全检出；上臂–顶板**TP6/FP0/TN382/FN0**，6次全检出；base–upper在chain为0/0/388/0。原83对（包括零报警行）分母与原参考保留，每表含TP/FP/TN/FN和FPR/FNR；完整夹爪内部masked报警0。原q、参考文件及其SHA在`summary-*.json`，每次新判定矩阵在`pairs-*.npz`；没有新策略回放、删失败样本或用旧hit列冒充新结果。chain FPR=17/375=4.5333%，仍为同拟合/验收样本，不是留出泛化证据。[SRC-0562](../../../../SOURCES.md#src-0562)

### 环境、回归与性能

全部原21278个q的8胶囊和车体盒与v1逐元素相同。独立旧源码环境对照CPU64/GPU64/GPU32：Truth/Local base与arm旗标、Depth的distance/valid/self_hit/points/origin_inside_self均相同。生产裁剪与独立未裁剪球矩阵GPU64和GPU32各10000 q、CPU64 512 q，额外底盘平移/转动后仍零差异。[environment-invariance.json](../../../../../results/task7/t7.18.2-r3-20261021/environment-invariance.json)、[cluster-equivalence.json](../../../../../results/task7/t7.18.2-r3-20261021/cluster-equivalence.json)。[SRC-0564](../../../../SOURCES.md#src-0564)

全目录GPU：**243 sim＋18 lower＋70 upper＝331 passed**，无fail/error/skip，测试前后源hash一致且与当前版本一致。另6个定向测试退出0；新增2项核查同连杆其余球/相切仍检查、严格零位对和相邻/固定许可保留。旧chain FP门`<=38`未放宽；现有6条pytest/Torch警告保留。三份`pytest-*.xml`、[tests-manifest.json](../../../../../results/task7/t7.18.2-r3-20261021/tests-manifest.json)与[host-final-hash-check.json](../../../../../results/task7/t7.18.2-r3-20261021/host-final-hash-check.json)可复核。[SRC-0563](../../../../SOURCES.md#src-0563)

|GPU2 E256，同快照|p50 ms|p95 ms|转移/s|每次尝试/提交子步|自碰撞失败|
|---|---:|---:|---:|---|---:|
|v1|263.958765|264.803896|969.155568|512/512|0|
|v4|265.491646|265.509823|964.871136|512/512|0|

p50增加0.580727%，吞吐下降0.442079%；同有效工作量，base/q/s/reward/reason/committed逐元素相同。每版2预热＋7次同步墙钟，不计准备/begin，不作长训工期承诺。G1同10k仍inside3219、合法2460、合法inside826，原点(0,0,0.5m)与传感器包络未动；遮挡风险保留。[profile-g1.json](../../../../../results/task7/t7.18.2-r3-20261021/profile-g1.json)。[SRC-0564](../../../../SOURCES.md#src-0564)

### 命令、异常、预算与交接

每条经`SELFCOLL_RUN=t7.18.2-r3-20261021 SELFCOLL_BUDGET_S=3600 python3 forem/scripts/task7_selfcoll_run.py LABEL python3 -B ...`进入forem-dev，物理GPU2、OMP/MKL=2、timeout590s、禁pyc。完整argv/PID/设备/退出码/墙钟见[本run命令账本](../../../../../logs/task7/t7.18.2-r3-20261021/commands.jsonl)。

|LABEL|退出码|容器wall s|
|---|---:|---:|
|build-spherepairs|0|1.911217|
|audit-spherepairs|0|26.368632|
|matrix-chain|0|3.495933|
|matrix-sync|0|5.070988|
|matrix-async|0|29.507089|
|tests-spherepairs|0|3.368410|
|tests-all-production|0|357.269081|
|metadata-readback|0|1.738701|
|equivalence-spherepairs|0|43.658316|
|environment-invariance|0|3.976988|
|profile-e256-g1|0|10.134776|
|final-integrity|0|0.476341|

容器计算累计**486.976472s＝8.116275min＜60min**；最长357.269081s＜600s。12条全部退出0。全局续接时间约23:05至2026-10-21T23:22:50.785346+08:00，与容器累计成本分开。宿主两项异常保留：补结果元数据时因root属主PermissionError退出1，改由有界容器metadata命令成功；宿主最终hash脚本误把相对路径按绝对路径解析，ValueError退出1，修正路径映射重跑退出0。两者不占容器计算，没有将失败覆写为通过。

最终完整性[verification.json](../../../../../results/task7/t7.18.2-r3-20261021/verification.json) acceptance=true，配置hash、数值mask、全目录源、继承参考、STOP和预算均核对；宿主再核对现行源码hash零差异。[resource-final.json](../../../../../results/task7/t7.18.2-r3-20261021/resource-final.json)显示GPU2无compute，GPU1外部PID3171511保留，Xorg不作为占用。无本任务后台计算，无停止/恢复命令；formal-sync/async STOP均在，**未重启训练、未提交Git、未停止非本任务程序、未改core.py或奖励/终止/动作/观测/IK**。[SRC-0564](../../../../SOURCES.md#src-0564)

剩余：仅Claude按本run原始证据复核；若随后重训，须另派task7.18，不自行启动。风险：base–upper均匀10k仍1850次FP、同样本拟合偏差、有限近零探针、相邻/固定安装整对许可、原网格参考和离散q/固定夹爪开度限制；不称全域无误报/零漏检。生产球对修复和必要验证已交付，PROGRESS仅本行改review，未改其他任务状态。

## Claude复核 t7.18.2-r3（2026-10-21T23:25–23:30，claude-opus-5-5，推理强度未知）

- 读交付：schema4球对级零位放行；base–upper在10000随机q上TP412/FP1850/FN0（该对随机姿态FPR 19.29%）；链式388总FPR 4.53%、13真碰撞与顶板6次全检出；sync/async执行回放0误报；全目录GPU 331 passed（Codex）。
- 复验：生产`robot_geometry.json` schema 4，v1保留；GPU2重跑test_robot/test_full_geometry/test_selfcoll_v2/test_core/test_env **35 passed**。
- 判断：base–upper的随机姿态误报集中在折叠姿态，任务相关样本（链式与执行回放）未见增加，可接受，记为已知限制。
- 结论：**task7.18.2 done**；可从头重训阶段L。
