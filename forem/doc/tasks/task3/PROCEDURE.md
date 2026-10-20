# Task3 Husky核心迁移 — 实施计划与详细流程

**当前状态（2026-10-07T14:41:26.104979+08:00）：done，Task3.6 R2必要验收通过，T3-A01–A04闭环，GPU默认auto已实际验证；下方旧review/未实施是历史。** 最终冻结t3.6-core-freeze4、330文件；当前结果与限制见Task3.6 RESULTS。[SRC-0066](../../SOURCES.md#src-0066)。用户已授权自动推进Task4；实际委派默认GPT6.1sol/medium，Claude替代Sonnet5.5/medium，父模型/强度未知。

**2026-10-07独立审查更新：** task3.6审查交付done，3项P2尚未闭环，父Task3继续review；不以审查报告完成替代必要验收通过，Task4前置未满足。当前以[task3.6 RESULTS](task3.6/RESULTS.md)为准，旧“未接手/待复核”描述为此前快照。[SRC-0060](../../SOURCES.md#src-0060)


> 后续实施者：使用superpowers:executing-plans逐节点推进；本轮无委派，不自动创建Agent或执行产品实现。

**Goal：** 在FoReM恢复Husky+UR5单机器人核心并验收，交付Task4可替换定位来源的稳定接口。

**Architecture：** 保留参考ROS包名/pybind与核心语义，在forem/src导入可达依赖，并以forem_husky组装移动模型和运行入口；普通SAC入口独立于含prior的原main。位姿来源通过受控adapter与TF接入，为Task4替换来源而保留接口。

**Tech Stack：** 现有容器ROS Noetic、Gazebo Classic、ROS control、MoveIt/BioIK、原C++/pybind及Python/PyTorch SAC，实际版本由3.1核对。**Spec：** [TASK](TASK.md)。

**授权更新（2026-10-07）：** 用户明确授权实施task3.1–3.5（必要源码迁移、容器依赖适配、构建、启动与验证），不含Task4定位/人工误差/补偿/世界模型/新任务/大规模训练；原“仅计划、尚未执行”是历史状态。实施结果与证据见同目录RESULTS，3.6由Codex独立复核。

**递归规则：** 每层恰有TASK.md、PROCEDURE.md、RESULTS.md；子任务放父目录内并继承编号，更深拆分同样先建三文档；父流程列顺序、依赖、负责人、三文档及验收关系，父结果仅汇总实际子结果。编号稳定不复用，不另建同职责README/PLAN/reports。当前无委派；如后续委派先登记输入、范围、模型/强度、日志与验收，父Agent独立核验。


## 全局约束与审查重点

只在forem修改/构建/运行；保留Task0/1/2及其他人改动；Docker使用sg docker，现有监督/同仿真锁拒绝并发，停止只针对本run身份。所有引用在SOURCES，数字参数声明来源/工程选择，不推断通用值。当前容器只保活的检查仅本轮快照，接手须再查。

重点检查：①同名Python树/旧devel遮蔽来源；②旧prior/checkpoint被悄悄启用；③规划关节被标成actual；④TF双发布或重盖时间/reset旧状态；⑤checkpoint动作/观测契约及失败清理。对应测试明确分配3.1、3.2、3.3、3.4、3.5/3.6。[SRC-0042](../../SOURCES.md#src-0042) · [SRC-0043](../../SOURCES.md#src-0043) · [SRC-0044](../../SOURCES.md#src-0044) · [SRC-0046](../../SOURCES.md#src-0046)

## 子任务顺序与父验收

|顺序|子任务|依赖|拟负责人|交付/验收关系|三文档|
|---|---|---|---|---|---|
|1|task3.1 核心来源、任务和接口冻结|Task0/1/2当前验收；新Task3范围|Claude（已实施，待复核）|确定唯一可运行的Husky核心导入清单、普通SAC入口和任务契约，禁止遗漏隐式依赖或引入旧prior机制。|[TASK](task3.1/TASK.md) · [PROCEDURE](task3.1/PROCEDURE.md) · [RESULTS](task3.1/RESULTS.md)|
|2|task3.2 移动模型、控制器与参考位姿链|task3.1已核验|Claude（已实施，待复核）|在FoReM独立构建并启动Husky+UR5物理模型，验证底盘/机械臂控制与参考位姿来源。|[TASK](task3.2/TASK.md) · [PROCEDURE](task3.2/PROCEDURE.md) · [RESULTS](task3.2/RESULTS.md)|
|3|task3.3 机器人、IK、观测与任务核心迁移|task3.2已核验|Claude（已实施，待复核）|迁移原环境reset/step链与任务/地图，验证底盘动作、末端计划和关节执行角色一致。|[TASK](task3.3/TASK.md) · [PROCEDURE](task3.3/PROCEDURE.md) · [RESULTS](task3.3/RESULTS.md)|
|4|task3.4 普通SAC、回放与checkpoint接口迁移|task3.3已核验|Claude（已实施，待复核）|让现有普通SAC推理/更新/存取接通新Husky环境，不依赖旧先验模型。|[TASK](task3.4/TASK.md) · [PROCEDURE](task3.4/PROCEDURE.md) · [RESULTS](task3.4/RESULTS.md)|
|5|task3.5 核心集成验收与Task4交接契约|task3.4已核验|Claude（已实施，待复核）|冻结可复现的核心运行入口和向Task4交付的定位替换边界。|[TASK](task3.5/TASK.md) · [PROCEDURE](task3.5/PROCEDURE.md) · [RESULTS](task3.5/RESULTS.md)|
|6|task3.6 核心迁移独立复核|task3.5交审；复核者与实现者不同|Codex（待接手）|独立核实核心迁移、普通SAC与可重复运行证据，决定Task3是否done并解锁Task4。|[TASK](task3.6/TASK.md) · [PROCEDURE](task3.6/PROCEDURE.md) · [RESULTS](task3.6/RESULTS.md)|

3.1–3.5拟Claude逐项实施，3.6拟Codex独立复核；模型推荐见各三文档，不等于委派/接手。父Task3仅在独立复核所有必要项后done，Task4实际执行依赖此结果。

## 核心文件职责与迁移规则

|目标|职责与来源|
|---|---|
|forem/src/modulation_rl/|原C++机器人/环境与Python任务/SAC可达核心；保留模块/包名，patch与source_manifest对应|
|forem/src/husky_description、husky_control、husky_ur5及必要MoveIt/依赖包|模型/控制/IK配置，3.1决定实际闭包与导入映射，不全仓复制|
|forem/src/forem_husky/|FoReM组装launch/URDF与位姿adapter，隔离原固定UR5入口|
|forem/config/task3/|source/core/task/SAC/物理配置及execution_freeze，唯一工程配置来源|
|forem/scripts/run_task3_core.sh、task3_sac_entry.py、检查/采集/复核脚本|本run进程管理、运行、数据/冻结验证，不直接调用原硬编码main|
|forem/tests/test_task3_*.py|具体来源/语义/生命周期/存取反例，非只镜像实现|

以上均是未来计划文件，本轮没有复制或实现。依赖按实际错误追踪，不删除本项目必需功能；非Husky可选依赖的剥离必须证明不在可达闭包。每次源码/资源导入记root/source commit、逐文件SHA256、license、目标路径、diff、镜像/ABI版本。

## 配置与接口契约

- source_manifest schema=1：source/destination、hash/license、core role、import path、dependency、patch理由；禁用宿主参考目录可写绑定。
- core_contract：robot/task/mode、关节/frame、控制周期/物理步长、limits/controller/IK、pose_source=gazebo_reference、感知字段真实/规划语义、代码/依赖hash。
- task_contract：SimpleObstacleTask版本、场景与完整episode实例、公开初态/目标/map、动作维度/缩放/限制、观测字段顺序/类型、奖励/termination/truncation/success、seed与reset。值由3.1对应源码读取，缺项禁止freeze。
- pose接口：nav_msgs/Odometry，原sim stamp、base frame、source/status；policy TF发布者唯一。评价真值另读原采样位姿/关节，不能使用规划值。
- SAC包装：reset(seed,episode_spec)→契约obs；step(action)→obs/reward/done/info与明确truncation；mode=smoke/train/eval，配置、run-id、输出/上限显式给定。checkpoint包含obs/action/config/source hash，错契约拒绝。

不要将原main.py的五百万步/无限episode循环、旧绝对权重路径或别的平台参数复制为当前预算。Task3 smoke只检查有效经验、一次普通更新与保存加载，正式任务性能训练属于Task4被冻结预算。[SRC-0043](../../SOURCES.md#src-0043) · [SRC-0046](../../SOURCES.md#src-0046)

## 执行与证据流

- [x] 接手读AGENTS/README/PROGRESS/ENV和三文档，查Git/容器/锁/foreign/资源，登记实际负责人模型。
- [x] 按3.1输出来源/任务/core契约，随后导入3.2模型/依赖并在容器独立build。
- [x] 3.2确认真实控制/位姿链；3.3确认任务/IK/obs/reward/reset；3.4检查普通SAC/replay/checkpoint。
- [x] 3.5运行集成/中断/恢复并冻结完整实际环境；3.6独立新ID复核。
- [x] 将实际freeze与差异/限制交Task4（见task3.5 RESULTS）；3.6未通过前不运行后续定位/训练。

实际运行接口（已实现并运行，见ENV.md与task3.5 RESULTS；下行为原计划写法，实际入口为`scripts/run_task3_core.sh RUN_ID -- CHECK_CMD`）：`sg docker -c 'bash forem/scripts/run_task3_core.sh --stage check --config /root/mm_husky_ws/config/task3/core_contract.yaml --run-id NEW_ID'`。实现后再由入口帮助输出核对实际参数，不能把这行当可执行验证结果。构建由容器catkin按3.1清单指定包，日志落forem/logs/task3/<run-id>，产物forem/results/task3/<run-id>；不写husky/build。

## 失败、恢复与完成条件

未读来源、缺依赖、import错树、未冻结task、非有限输入、限位/控制不稳定、混淆期望与actual、TF来源/时间错、终止/截断不明、旧checkpoint误用、无身份清理均失败，留run记录；不通过新增误差机制/改奖励绕过。修复需要改配置/代码时新版本/hash、新run-id，重做受影响阶段。resume只能明确checkpoint+同契约，epoch/reset不跨episode串状态。子结果报告源码/依赖/build/start/任务IO/SAC接口分别状态，不将文档核验或脚本退出0当任务性能通过。

## 迁移后的用户讲解交付

用户要求迁移完成后详细说明原Husky“有几条线、各自什么用途”。3.1审计原运行入口/调用图，3.5在本层RESULTS交付完整说明，3.6按源码和运行证据核对。按“算法训练/评估分支”“在线任务到物理执行链”“世界模式/位置来源”分别给核实计数；不把重复源码树或入口文件数冒充有效运行线。每条说明目的、入口、输入输出、上下游、活跃/历史状态和迁移保留/改造/未迁移范围，并标未运行项。迁移完成后向用户逐条讲解，不只交文件清单；本轮尚未迁移，也未核实最终数量。审核说明其他分支不扩大本次移植范围。[SRC-0049](../../SOURCES.md#src-0049)

## Agent与推理强度

推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**。常规文档/明确步骤运行low或平台默认；来源迁移、坐标/时间/观测与验收的跨模块核对medium，理由是需要追踪完整因果链。当前文档作者Codex /root，实际模型/强度未知；拟Claude实施、Codex独立复核，均未接手，不自动启动Agent。实施时记录实际配置，推荐不冒充执行配置。

2026-10-07用户要求重编号：当前Task3为3.1–3.6（3.1–3.5实施、3.6独立复核），Task4前置为新Task3.6通过。旧编号及旧核验报告仅为此前快照，当前检查见[SRC-0050](../../SOURCES.md#src-0050)。

## 按新编号给Claude的执行提示词（尚未派发）

```text
请在 /home/ybc/projects/CL-FoReM 执行Task3核心迁移，按最新编号顺序完成task3.1–task3.5，交给Codex进行task3.6独立复核。
先读根AGENTS、forem/doc/README.md、PROGRESS.md、SOURCES.md、ENV.md，以及Task3父子TASK/PROCEDURE/RESULTS；核查实际状态并登记接手。
模型推荐Sonnet5.5，跨模块迁移/排错medium，不支持则默认并记录实际配置。
执行顺序：3.1来源/任务/接口冻结；3.2移动模型/控制/参考位姿；3.3环境/IK/观测/任务；3.4普通SAC/replay/checkpoint短流程；3.5集成/生命周期/冻结/Task4交接。
本提示词用于授权上述阶段必要源码迁移、容器依赖适配、构建启动与验证；不只交计划，也不重复确认已明确授权步骤。实施时登记收到本提示词的实际授权，不把本轮文档写入当成已派发。
只在forem开发，husky只读；保留Task0/1/2和他人改动。ROS仅容器，Docker用sg docker -c。普通SAC用update_parameters，禁旧prior硬编码依赖；保持原任务/动作/奖励/终止语义，区分计划状态与实际反馈。
不实施Task4，不增加传感器定位、人工误差、补偿、世界模型、新任务或大规模训练；不推送/合并，不操作他人进程或擅自启动其他Agent。
按阶段验收，失败留证据并以新run-id修复复测；同步三文档/进度/日志/来源。实际版本、命令、退出码、配置、原数据和限制可追溯。
迁移后在task3.5/RESULTS.md及最终回复详细解释原Husky各训练/评估分支、在线任务执行链及世界/位置来源：按分类核实数量、用途、入口、输入输出、调用关系、已运行/未运行和迁移对应。
交付实际入口、验证证据、风险、Task4定位替换合同和task3.6审核清单；父Task3保持review直到独立审核通过。
```
