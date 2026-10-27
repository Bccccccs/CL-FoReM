# task8.10 — 原语场景几何后端（primitive-obb-v1）与PCD体素后端对照

状态：**done（2026-10-27，primitive-obb-v1作为可选后端验收通过，默认仍v3；见[RESULTS](RESULTS.md)）**。原状态：**已授权实施，待定执行者与预算（2026-10-27用户：“那我们先去做8.10，现在的8.9作废吧，要优化好了整体的地图再开始训练”，[SRC-1220](../../../SOURCES.md#src-1220)）；尚未派发、未实施、未运行**。原draft状态：2026-10-27 Claude只建三文档与对照验收方案。用户决定与工程选择[SRC-1181](../../../SOURCES.md#src-1181)；调研依据[SRC-1180](../../../SOURCES.md#src-1180)。

## 用户要求与授权边界

2026-10-27用户：“同意方向A，先建任务三文档和对照验收方案，暂不实施，也不影响正在跑的8.9 r2。”方向A即：**以原语场景JSON作唯一世界几何真值，PCD降为派生/可视化产物**（[调研记录](../../../agent_logs/project/20261027-claude-map-representation-survey.md)）。

本轮只写文档。**实施、运行和派发都需用户另行指示**；文档中的参数、门、预算建议不构成授权。不改task8现有文件、不碰8.9 r2的代码/产物/账本/进程；8.9是否改用新后端由用户在本任务验收后另行决定。

方向A改变了task8父合同第2条“有侧车时不从box代替读点云”和[SRC-0984](../../../SOURCES.md#src-0984)“PCD为实际几何来源”的口径。本任务以**新增可选后端**实现该改变：默认后端仍为`pcd-voxel-v3`，新后端须显式配置选择，旧结论与产物保留为历史。

不包括（需用户另行批准）：新原语类型（圆柱、网格+CoACD等）、ManiSkill/Gazebo/SDF导出、PCD派生导出、语义观测、改Grid/策略张量/奖励/动作/终止/IK/ghost传感器、改数据域或分辨率、任何训练或含optimizer更新的测试、更换8.9地图池、推送合并。

## 已核事实

1. 两类地图的几何源头都是盒体：语义池24张`mapgen/outputs/all_maps/*.json`的`boxes`为8列平铺盒体`[x,y,z,sx,sy,sz,cos,sin]`（最小角＋绕最小角的yaw），24/24图`objects`（墙/门直接盒体＋家具`parts`）展开后的数量与`boxes`一致；638个对象中233个带非零theta。立方体池由task7 mapgen_a的JSON盒体导出PCD（8.9.2 `cube-export-v2`，[SRC-1161](../../../SOURCES.md#src-1161)）。核查见[SRC-1181](../../../SOURCES.md#src-1181)。
2. PCD→体素往返造成的问题历史：v1/v2墙缝与射线漏墙（[SRC-0999](../../../SOURCES.md#src-0999)、[SRC-1006](../../../SOURCES.md#src-1006)），v3闭合面归属修复（[SRC-1087](../../../SOURCES.md#src-1087)），旋转格点混叠致内部缺格（[SRC-1125](../../../SOURCES.md#src-1125)）。
3. 现有解析实现可复用：task7 `geometry.py`的盒体最小角约定、`to_box`、`rectangle_hits`（底盘SAT）及线段–盒距离；task8 `scene.py`的`_slab`、`_segment_bounds_distance_squared`、`_rectangle_bounds_hits`、打包/BVH。task7 `load_map`会自动补墙，**task8禁止补墙**，新后端不得调用该补墙路径。

## 研究问题与假设

问题：以JSON原语直接做扫描、碰撞、reset与规划高度，能否在**保持task8全部接口与语义**的前提下，消除采样/体素化引入的几何缺陷，且性能可接受？

假设（待验证）：①解析后端与独立参照在float64下一致到数值精度；②墙体漏射线与内部缺格结构性为0；③与v3的差异集中在≤1个体素的边界层；④吞吐不低于v3到影响8.9规划的程度。**不以SAC成功率作为本任务验收**。

## 后端协议（primitive-obb-v1，规划）

1. **真值**：每图一个不可变`PrimitiveScene`，原语列表即JSON `boxes`（语义图）或与8.9.2立方体导出相同的盒体集合（立方体图，含其墙体处理）；`objects/scene/rooms`只作语义元数据，`semantic_policy_input=false`不变。v1只支持`type=box`，未知类型为导入错误，不得静默忽略。
2. **坐标**：world、米、float64预处理；最小角＋(cos,sin)沿task7约定，旋转单位误差容差沿task7 `1e-6`。盒体闭合；**不补墙、不缩放、不裁剪原语**。原语超出数据域`[-5,5)×[-5,5)×[0,1.6)`的部分仍是真实几何（射线/碰撞照常命中），逐图报告越域原语数及最大越域量（与v3“域外点报错”的差异须列明，工程选择见SRC-1181）。
3. **查询**（与`VoxelScene`/`SceneBatch`同名同签名）：`raycast`对OBB解析求交（射线变换到盒局部系后slab），闭合入射，原点在盒内返回0；`contains`闭合；`collide`底盘沿0.99×0.67全高度XY投影SAT、机械臂3D胶囊–OBB距离与地面检查，接触即碰撞；自碰撞与ghost豁免沿现有`robot.self_collision`。z=0解析地面独立处理不变。
4. **派生占据**：`occupancy()`=与闭合OBB相交（含接触）的数据域内体素（3D SAT精确判定），`planning_height()`沿v3“列内最高占据体素上表面”定义由此派生，保持规划保守高度语义。派生占据只用于规划高度和诊断，不参与扫描/碰撞。
5. **信息边界**：候选/局部推演仍只持Grid快照；Grid/LocalCollision仅从深度落点更新；全局200²/0.05m、局部128²、74/75维向量不变。
6. **版本**：`map_backend=primitive-obb-v1`、`environment_version=task8-prim-v1`，provenance记录JSON hash、原语数、越域统计、device/dtype、构建耗时；cache_key含版本，不与v3缓存混用。默认配置仍为`pcd-voxel-v3`。

## 对照设计（概要，细则见PROCEDURE）

|臂|内容|作用|
|---|---|---|
|R 独立参照|另写float64 OBB几何（不调用生产函数），含精确3D SAT体素化|正确性判据|
|P 候选|primitive-obb-v1|交付后端|
|V3 现行|pcd-voxel-v3；语义图用原mapgen PCD，立方体图用8.9.2 cube-export-v2 PCD|差异与收益对照|
|PV 诊断|P的派生占据经现有打包/BVH查询（`primitive-voxel-diag`）|区分“采样误差”与“体素离散误差”；非交付后端|

## 交付与验收门

|门|内容|性质|
|---|---|---|
|A 导入|24语义图＋8.1夹具＋立方体池全量解析；语义图`objects/parts`按mapgen源码组合规则展开后与`boxes`逐盒一致；源JSON/PCD hash不变；越域统计逐图|硬门|
|B 解析正确性|P vs R：contains/raycast/底盘/机械臂/派生占据，float64误差与布尔分歧在规定容差外为0；float32偏差另报|硬门|
|C 结构缺陷|P：全内部缺格0、派生占据=R闭合SAT体素化、每盒≥1格；深墙射线漏检0（沿[SRC-1081](../../../SOURCES.md#src-1081)深度门）|硬门|
|D 与V3差异|同扫描/同位姿的距离差、碰撞分歧、占据差、Grid差、reset采样差，逐图分类|报告，不设门|
|E 单一真值干预|改JSON→P输出按R预期变化；只改PCD→P输出逐位不变|硬门|
|F 接口与链路|接口一致；task8几何无关测试双后端通过；≥2语义图＋≥2立方体图＋8.1夹具真实step链路；profile沿父合同第7条|硬门|
|G 性能|构建、扫描、碰撞的延迟/吞吐/显存，P/PV/V3同输入对照|报告，不设吞吐门|
|H 保真隔离|task7/task8现有生产文件、资产、8.9 r2产物hash不变；无训练/optimizer测试|硬门|

通过A、B、C、E、F、H即可将P标为“可选后端已验收”；D、G只报告。**切换默认后端、8.9地图池改用P或重新划分实验，均须用户另行决定。**

<a id="model-routing"></a>
## 模型、强度与分工（推荐，非已执行配置）

|角色|Codex推荐|Claude推荐|理由|
|---|---|---|---|
|父协调|GPT6.1sol / medium|Sonnet5.5 / medium|跨task8接口、8.9隔离与证据汇总|
|S1 实现P与PV|GPT6.1sol / high|Sonnet5.5 / high|OBB射线/胶囊距离/闭合SAT体素化需几何推导与边界语义|
|S2 独立参照R|GPT6.1sol / high（≠S1）|Sonnet5.5 / high|独立推导，避免与实现同错|
|S3 固定执行|GPT6.1 terra / low（[SRC-1162](../../../SOURCES.md#src-1162)）|Sonnet5.5 / low|按已定命令跑导入、逐图诊断与性能脚本，无判定权|
|S4 独立验收|GPT6.1sol / high（≠S1/S2）|Sonnet5.5 / high|核diff、原产物与门判定|

S3仅执行输入/输出与判据都明确的步骤，遇异常交Sol；Sol必须查原产物，不能只签收总结。
