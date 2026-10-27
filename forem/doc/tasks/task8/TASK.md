# task8 — PCD地图迁移与下层SAC问题处理

状态：**review（PCD后端与本次24图链路已通过；8.6存在执行越界，严格合规失败，交付已归档）**。执行依据[SRC-0990](../../SOURCES.md#src-0990)，功能证据[SRC-0991–0996](../../SOURCES.md#src-0996)，执行偏差[SRC-0997](../../SOURCES.md#src-0997)；SAC下一阶段未启动。父实际模型/强度未知，子Agent按显式Sol/Luna分工记录，推荐见下文及执行日志。

## 目标、顺序与边界

本周目标是迁移到现有带场景语义的mapgen PCD，并处理下层SAC训练问题。**第一阶段先让PCD成为整环境的实际几何来源**：随机立方体PCD→机器人扫描→累积地图→原规则候选/局部推演→下层动作→IK/碰撞/状态提交→新扫描；再接现有语义场景资产。第二阶段待地图验收后整理下层SAC问题与修复协议；本轮不指定原因、不调参、不开始训练，不创建空泛训练子任务。[SRC-0984](../../SOURCES.md#src-0984)

传感器按用户确认采用**ghost**：相对底盘固定、随机器人移动；取消传感器实体碰撞，忽略整个机器人自身对扫描的遮挡；场景障碍仍遮挡。底盘/机械臂对环境、机械臂非传感器自碰撞、地面碰撞保留。该简化是研究条件变更，须记录为新协议，不宣称真实相机效果。[SRC-0984](../../SOURCES.md#src-0984)

不包括：语义分割/语义观测通道、候选U-Net、改高度图表示、改奖励/动作/终止/IK规则、WM实验、ROS/Gazebo/ManiSkill接入、付费LLM生成、正式地图训练池和长训、task7续训/D10/旧诊断恢复、推送合并。保留语义元数据不等于实现语义导航。

## 已核事实与研究问题

现有路径读JSON盒体，`load_map`补墙；`Panorama`对盒体求交，不消费PCD。reset、规划、碰撞、DecisionEnv都显式绑定旧入口。机器人自遮挡可能令扫描无效；当前URDF的D435宏为注释，不能混同真实D435自碰撞。现有24对mapgen资产PCD只有xyz，JSON含objects/scene；完整证据[代码SRC-0985](../../SOURCES.md#src-0985)、[资产SRC-0986](../../SOURCES.md#src-0986)。

本阶段问题：从PCD构造的同一环境几何能否被扫描感知、被真实碰撞检查使用，并贯通回合及决策接口？假设：沿现有尺度体素化可作为最小迁移后端；旋转/薄结构/掠射误差及性能待验证。对照是解析立方体/独立体素参照、同一场景有无遮挡关系和点云变更干预，不以SAC成功率提升作为此次验收。[SRC-0987](../../SOURCES.md#src-0987)

## 路线与取舍（规划者建议）

|路线|取舍|
|---|---|
|PCD派生固定world占据，扫描/碰撞/初始化共用查询|**本计划采用**；输入PCD确实控制环境，保留离地几何；需明确体素误差、空间索引和性能|
|JSON盒体作运行真值、PCD只显示/对照|改动小，但PCD改动不影响环境；不满足本次完整迁移，不作为最终交付|
|新物理引擎或新三维策略网络|扩大科学与环境变更，不纳入本轮|

以上是Codex实现规划，不假称用户逐项选了体素算法。工程选择、数值及限制统一登记[SRC-0987](../../SOURCES.md#src-0987)。

## 统一合同

1. `forem/src/task8_sim/`实现新适配层，`forem/config/task8/`新协议；旧task7源码/配置/产物只读继承，哈希见[基线](../../../results/task8/t8-plan-20261026/source-manifest.json)。允许复用纯组件或局部复制并注明来源，不改task7原文件、不全库复制、不沿用旧run目录。
2. 资产先支持现有PCD v0.7 ASCII xyz体内采样；不偷偷把binary/surface-only点云当已支持。坐标world、米；原PCD字节和JSON语义可追溯。`semantic_policy_input=false`。无JSON的立方体PCD由manifest显式声明元数据；有侧车时不从box代替读点云。
3. PCD→体素索引：h=0.05m，origin=(-5,-5,0)m，shape_zyx=(32,200,200)，`floor((p-origin)/h)`，float64解析；不自动补墙/补洞/地面点/缩放。场景显式保留z=0解析地面（旧环境已有），不能新增围墙冒称PCD障碍。**数据域不等于物理围墙**：PCD坐标采用三轴半开域，越界输入报错；reset的base中心/目标沿原[-5,5)相关校验（base/goal仍按原严格内部条件），包络碰撞按实际占据而非虚拟边界。射线从域外进入可命中，从域内离开未遇占据则无障碍命中，解析地面独立处理。真实step不新增越域终止/碰撞规则；无PCD围墙处可走出数据域，域外无点云障碍，Grid沿原规则将域外视为未知。机械臂高于1.6m也不产生虚拟天花板碰撞；非传感器自碰撞/关节限位及z=0地面检测仍有效。底盘包络部分出域只检测其与真实体素的交集，非有限输入属于调用错误。记录out_of_map诊断但不改变Core失败码/奖励、状态提交与transition。闭合体素接触算碰撞，索引半开，射线掠边/角同协议。[SRC-0986](../../SOURCES.md#src-0986)、[SRC-0987](../../SOURCES.md#src-0987)
4. 所有运行环境几何来自同一个`VoxelScene`（plus显式地面/域规则）。深度射线有遮挡/量程，机器人base采用原全高度XY投影、arm采用3D胶囊与地面检查；规划继续原保守高度路线语义，**不把离地空腔底盘通行作为本阶段能力**。不得用PCD做扫描而JSON做碰撞/初始化。
5. `Grid`/`LocalCollision`及策略张量沿旧合同，仅从新深度落点更新。候选/推演只能持有Grid快照，不持有PCD/真值occupancy/语义sidecar；真实执行器、reset规划可读真值。全局200²/0.05m、局部128²、原路线通道、74/75维下层向量不新增字段。[SRC-0985](../../SOURCES.md#src-0985)
6. 扫描沿360×90、水平360°/垂直90°、6m量程、base相对(0,0,0.5)m及原像素中心射线/时间戳；`self_hit=false`、`origin_inside_self=false`表达ghost模式下禁用遮挡判定，日志另写`self_occlusion=ignored`，不能称实测无几何相交。传感器link豁免从明确名单派生，不动URDF、不关闭全机器人碰撞。
7. 动作、Core物理子步、IK、路线与终止沿**显式**基线profile。`sync_v5`传`synchronous=true,failure_mode=cbl_continue,async_time_penalty=0.0,episode_end_bootstrap=true,ik_avoid_collision=true`（前四项核实际v5 config，IK为当前Core默认）；用于下层接口。决策环境另用`decision_sync_legacy` / `decision_async_legacy`，均`failure_mode=terminal,async_time_penalty=1.0,episode_end_bootstrap=false,ik_avoid_collision=true`，synchronous由名称确定，与当前DecisionEnv默认一致；不将同步v5补丁外推异步/上层。此次只接口回归，不混合两变体历史结果。
8. `environment_version=task8-pcd-v1`、`map_backend=pcd-voxel-v1`、`sensor_policy=ghost-v1`连同PCD/sidecar/配置/hash和variant写入每次运行。旧checkpoint仅可提取冻结actor做接口冒烟；不得恢复旧pickle环境/replay/optimizer作为新地图续训，不绕过格式校验。

## 子任务、交付与验收

|任务|独立交付|依赖|负责人/状态|
|---|---|---|---|
|[task8.1](task8.1/TASK.md)|点云读取/manifest/随机立方体PCD夹具、完整字段与索引验证|无|执行者派发；review待执行|
|[task8.2](task8.2/TASK.md)|共享体素几何、遮挡射线/碰撞查询、独立参照测试|8.1|执行者派发；review待执行|
|[task8.3](task8.3/TASK.md)|ghost机器人传感器策略及扫描接入|8.1接口，集成依8.2|执行者派发；review待执行|
|[task8.4](task8.4/TASK.md)|PCD回合/路线/Core/决策适配，部分reset与信息边界|8.2＋8.3|执行者派发；review待执行|
|[task8.5](task8.5/TASK.md)|24对语义地图导入、逐图诊断、语义保留和场景可运行证据|8.1可先导入；运行依8.4|执行者派发；review待执行|
|[task8.6](task8.6/TASK.md)|全链路独立验收、有界性能、SAC下一阶段交接|8.1–8.5|独立验收者；review待执行|
|[task8.7](task8.7/TASK.md)|PCD体素化格点边界修复（pcd-voxel-v2）：墙体空洞/射线穿墙，SRC-0999|8.1–8.6产物|blocked：v2墙门失败（SRC-1006），被8.8取代|
|[task8.8](task8.8/TASK.md)|PCD体素化闭合面归属（pcd-voxel-v3），地图尺寸不变，SRC-1021|8.7 v2代码与证据|2026-10-26 Claude建档、派Codex；尚未执行|
|[task8.9](task8.9/TASK.md)|第二阶段：下层SAC训练问题——8.9.1批量性能核查、8.9.2地图池划分、8.9.3长程对照设计，SRC-1102|8.8 v3|closed：2026-10-27用户作废（SRC-1220），未smoke/未长训，历史保留|
|[task8.10](task8.10/TASK.md)|原语场景几何后端primitive-obb-v1（JSON原语为真值、PCD降为派生）与v3对照验收，SRC-1181|8.8 v3（8.9已关闭，隔离条件解除）|2026-10-27用户授权实施（SRC-1220）；执行者/预算待定，未实施|

父验收：PCD-only夹具可运行；改PCD不改JSON影响扫描/碰撞；ghost语义正确；真实动作链路/局部推演隔离/批量reset通过；24图导入与逐图状态完整且存在语义图真实运行证据；所有未运行/不可行图单列，不以数量遮盖失败。必须24图格式/几何查询验证完整、24图有界采样均有记录，且至少一张语义图默认采样到真实step完成；仅采样预算耗尽或未找到可行任务可作为已报告限制，解析/几何错误、异常崩溃、少图/缺记录或关键链路未通过均阻止完成。源资产与task7哈希保持，计时/设备/限制齐全。若关键链路失败则父task8保持review/blocked，不以文档齐备代替运行通过。

<a id="model-routing"></a>
## 模型、强度与验收分工（2026-10-26更新）

按用户[SRC-0989](../../SOURCES.md#src-0989)：**简单工作可交Luna，需推理的工作交Sol，Luna交付必须由Sol验收**。以下是计划配置，不是已经运行的模型。

|任务/角色|执行模型与强度|Sol负责的部分与验收|
|---|---|---|
|父协调|GPT6.1sol / medium；复杂冲突high|确定接口/依赖、资源与全局证据，不能把判断交Luna|
|8.1 资产/夹具|Sol medium先核协议；GPT6 Luna / low执行固定格式清单、hash、夹具导出与已明确的读写步骤|Sol medium确定解析/异常合同，核PCD-only和反例后放行；歧义/解析故障由Sol处理|
|8.2 几何/射线/碰撞|GPT6.1sol / high|实现需几何推导；独立Sol high核参照、边界和碰撞语义|
|8.3 ghost传感器|GPT6.1sol / medium|审查豁免索引、IK与扫描接线；Sol medium验收，复杂误碰/遮挡归因升high|
|8.4 整环境集成|GPT6.1sol / high|跨reset/Core/DecisionEnv/profile状态关系；独立Sol high验收|
|8.5 地图批量迁移|Sol medium先固定导入/诊断规则；GPT6 Luna / low执行复制/hash、固定导入命令及逐图记录|Sol medium负责语义保真、几何差异解释、失败分类和验收；Luna不能决定忽略坏图|
|8.6 独立总验收|独立GPT6.1sol / high|检查代码/真实证据、必要复验、性能归因与最终验收；Luna仅可整理固定格式清单，无判定权|

Luna仅执行输入/输出和判据都明确的步骤，不自主修改接口、参数、碰撞/终止语义，不判断失败根因或放宽验收。遇到这些问题交Sol；不能让Luna提高到high代替Sol。Sol必须检查diff、原产物及必要测试，不能只签收Luna总结。混合任务按“Sol定合同→Luna执行→Sol验收”顺序交接，同一文件不并发写；每阶段在已有子任务RESULTS/日志登记负责人和模型。

Claude备选推荐仍为Sonnet5.5：普通固定步骤low、合同/一般推理medium、几何/状态/总审查high；理由同上表。**本次需要推理和验收的实际派发按用户要求选Sol**，仅用户另行指定Claude时采用该备选，不以此替代Sol验收。

平台模型名明确选择`gpt-6-luna`与`gpt-6.1-sol`；若平台不同先核对应名称，不静默继承父模型。若使用本会话的spawn_agent显式模型覆盖，需`fork_turns="none"`，并完整附根AGENTS、任务三文档、日志、输入产物、文件归属和验收条件；这不改变任务范围或授权。本轮只更新建议，不派发实施。
