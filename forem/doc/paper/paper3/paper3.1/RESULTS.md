# paper3.1 — 当前系统事实与研究对象核查

状态：done（只读核查交付，父任务统一验收）。核查日期2026-11-06；负责人Codex；实际平台模型/强度未知。推荐GPT6.1sol/medium、Sonnet5.5/medium；跨层动作因果审查可high。本次独立完成，未委派、未运行模型、测试、训练或仿真。

所有下述代码事实及有条件推导统一对应 [SRC-P3-SYSTEM](../../../SOURCES.md#src-p3-system)（由父任务统一登记）；既有结果沿原任务来源，不重复实测。

## 1. 一段任务定义

当前用于上层研究的系统是自写理想执行环境中的Husky+UR5、primitive-obb-v1场景及ghost-v1传感器。冻结下层是B3-5M seed4718的确定性SAC：输入共享的底盘局部128×128×3已观测/高度/路线投影图及74维q、TCP、下一TCP、未来路线采样、子目标等向量，输出归一化三维[u,ω,v]。u只调节**给定世界坐标系末端位姿轨迹的推进速度**，ω、v控制非完整底座；UR5关节由每个试探底座位姿对应的解析IK（必要时DLS）求解，策略不能自由输出关节、改变末端路径或独立选择IK分支。上层在规则生成的12个一米移动点加1个原地点中选一个，经冻结B3在当前已观测地图快照上推演得到候选特征；真实执行更新扫描并返回反馈。当前task10是stage1上层选择基线，已有VCM记忆、候选编码及显式模型推演，学习型世界模型预测—修正未参与当前评分。task12已实施独立轻量U-Net候选热力网络及离线教师评价，尚不能写成已正式接入上层或已提高完整任务成功率。

## 2. 哪个工作树有效

|对象|有效证据入口|版本/边界|
|---|---|---|
|冻结下层接口|[task10 lower.py](/home/ybc/projects/CL-FoReM-task10/forem/src/task10/lower.py:1)、[task10流程](/home/ybc/projects/CL-FoReM-task10/forem/doc/tasks/task10/PROCEDURE.md)|读取B3 4718；actor SHA256 `3db11d9f00317849e35a523d66d0935ebc2e3567d82c519ccc42f3d8de42f7ae`；运行源依赖69文件清单。此次仅阅读现有核验记录，未重复全量hash。|
|上层|`/home/ybc/projects/CL-FoReM-task10`；task10三文档及task10.17/18/19|HEAD `91f538cf2ee10bebffd6b643d5c908fa0d419ced` 加未提交修改；HEAD不代表完整执行源码。10k实际版本看run `t10-long-20261104-s101-r2` 的frozen-code/检查点与启动SHA。|
|下层后续探索|`/home/ybc/projects/CL-FoReM-task9`；task9三文档及task9.12/13|HEAD `d198e5ca48f86071c05274f9da753f393ce058b4` 加修改。BioIK和原生RLlib探索不等于task10已升级冻结下层。|
|候选生成学习|主树`/home/ybc/projects/CL-FoReM`；task12三文档及task12.7|run `t12-expand-20261105-r8` 已结束交review，冻结版本以code-version.json为准；不是旧TASK顶部“仅调研”阶段。|

本轮读了根AGENTS、README、PROGRESS、DECISIONS、会议记录、paper主线与各相关TASK/PROCEDURE/RESULTS及必要源码。ENV仅为旧环境概览，当前任务记录更晚；不以其“task7尚未容器”等旧句定义现状。工作区已有大量dirty更改和其他进程，全部保留。

## 3. 实际观测及坐标系

### 3.1 共享传感链而非两套异构传感器

- 当前[传感器配置](/home/ybc/projects/CL-FoReM-task10/forem/config/task8/sensor.json:1)及[PcdPanorama](/home/ybc/projects/CL-FoReM-task10/forem/src/task8_sim/perception.py:13)：相对`base_footprint`固定(0,0,0.5)m；360水平×90垂直角度采样，像素中心射线，最远斜距6m。垂直范围−45°到45°；实际中心−44.5°到44.5°。随底座yaw旋转。没有独立腕部相机输入，没有VLM输入，也没有底座/机械臂分别拿到不同实测传感器的证据。
- ghost-v1明确忽略**整个机器人本体对扫描的遮挡**，不是只有传感器外壳；场景遮挡、地面射线和距离/FOV限制仍在。不能把旧task7自遮挡诊断套到当前冻结B3。
- [Grid.update/crop](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_sim/perception.py:96)：有效射线**落点**更新世界200×200、5cm栅格；不沿整条射线标记自由空间。每格记录是否有落点及历次最大高度；z≤.05m按地面0高度落图。策略局部裁剪128×128、5cm，即6.4m见方，以底盘XY/yaw对齐；高度按1cm量化。已观测不是完整三维可见性或自由空间证书；未知0高度仍由独立known通道区分。
- [Core.observe](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_sim/core.py:166)：TCP、next_TCP和未来15个路线xyz以URDF `base_link`表达，包含`base_footprint→base_link`固定安装变换；图像XY同底座朝向，但高度是世界地面以上高度，不能把它当TCP坐标系的相对z。路线图是已给定任务路线的XY投影，不是感知出来的物体轨迹。

### 3.2 下层字段（74维向量+图）

|字段|维度|实际含义|
|---|---|---|
|q|6|当前已提交关节状态除软件限位尺度[2π,2π,π,2π,2π,2π]；不是IK目标冒充实机反馈。此处本来就是理想运动学状态。|
|tcp / next_tcp|7+7|当前FK TCP及路线前方0.01m的给定位姿（xyz+xyzw）；底盘base_link系。|
|route_points|45|当前弧长之后0.1至1.5m、每0.1m一个，共15个xyz，末端截断；没有对应15个未来姿态。完整位姿路线仍供环境IK查询。|
|subgoal|5|当前底盘系dx、dy、sin/cos相对yaw、原地标志；同步模式不向策略提供自由末端目标。|
|synchronous / previous_action|1+3|同步标志及既有动作历史字段。|
|grid|128×128×3|顺序是**已观测、最大高度、未来路线XY投影**。|

[preprocess](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_lower/observation.py:1)只消费上述字段；`scan_timestamp`与世界全局位姿不进入冻结下层向量，未来路线三维采样可部分补偿投影信息，但不能补回障碍垂直结构。

### 3.3 上层与task12

上层从相同grid、q、tcp、route_points，加上一段结果、前一候选在当前底座系位姿、同步标志、累计失败及停滞占限额比例建立状态；VCM有最多4条历史和GRU，不能说系统完全无记忆。候选每槽6维几何及19维推演特征（到达/末因、首次失败比例、尝试时长/时限、终态相对位姿、路线进展、误差、风险）。[environment_inputs](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_upper/stages.py:214)、[VCM](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_upper/vcm.py:114)。

尤其已有[sweep_metrics](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_sim/risk.py:31)会遍历初态和已提交离散状态，把**底座和机械臂投影覆盖区域的并集**用于未知比例，并计算整机最小间距/最近未知距离。它不是只看底座风险，但把分部位、分高度、分时刻结构压为3标量；没有子步之间连续插值。提“加未知率/扫掠风险”时必须以这个真实基线为对照。

task12输入同3通道图，加q/tcp/三维route_points（58维条件）进入U-Net瓶颈；输出每格logit，按扇区取点及几何筛选。目前固定采样支持为两环0.5/1.5m、12扇区，原地点独立。标签后来升级为零失败安全到点或严格完成路线的utility v1；不是VLM/扩散网络生成自由关节动作，也不是每个像素都有真值。父级原始三文档与新task12.7结果一起读，不能仅沿旧首轮“到点二分类”描述。对应[task12流程](../../../tasks/task12/PROCEDURE.md)、[热力代码](/home/ybc/projects/CL-FoReM/forem/scripts/task12_heatmap.py:59)、[task12.7结果](../../../tasks/task12/task12.7/RESULTS.md)。

## 4. 动作权限与协调已经在哪里发生

1. [motion.actions](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_sim/motion.py:13)：同步下层u=.01+.145(raw_u+1)∈[.01,.30]m/s，ω∈[−1,1]rad/s，v∈[−.3,.3]m/s；原地槽强制ω=v=0。u推进固定末端路线弧长，不是自由TCP三维速度。
2. [Core.step](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_sim/core.py:246)：每次策略动作最多两次0.05s试探，先做非完整底座运动、推进末端路线，再由新底座变换和世界末端目标求IK。解与底座/臂/自碰撞通过才共同提交；失败不提交且消耗尝试时间。名义策略周期0.1s，但失败时仅一次0.05s尝试，不能把每条transition无条件写作0.1s实执行。
3. [Kinematics.solve_world/solve_tcp_in_arm](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_sim/kinematics.py:162)：解析八分支、最近上一q的合法解，已配置时考虑自身与地面碰撞的分支偏好；无解析解时DLS。分支筛选并不是全场景障碍优化。输出受软件限位与位置/CBL旋转残差判据约束；IK接纳位置阈值0.1m、CBL旋转残差0.05，与严格成功的0.025m/0.05rad不能混淆。关节速度越限只作为diagnostic字段，当前不是电机动态或力矩闭环。
4. [generate_candidates](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_sim/candidates.py:74)：当前task10 12个30°间隔、一米固定点，候选yaw指向移动方向；以已观测正高度栅格检查1.6×0.67m通道，未知不自动阻断；mask只保证生成几何条件，不保证整段臂可达/安全。第13槽原地，根据当前底座下沿固定路线的IK前缀搜索进展。移动同步槽不是让上层直接指定末端进展量。
5. [predict_candidates](/home/ybc/projects/CL-FoReM-task10/forem/src/task10/environment.py:64)：每个有效候选复制同一状态/路线/已观测Grid/计数，在相同B3下整段推演；局部图快照无新扫描、无未来真值。实际执行用原语场景碰撞并在有提交动作后扫描，因此可出现新障碍导致的推演—执行差异。这是已有显式运动学/局部几何前向预测，不是完全model-free层次策略串接。
6. task10 stage1只能选择索引，不能改路线、关节、IK、传感器位姿或下层权重。若建议自由全身速度控制、腕部主动视角、臂收拢动作，必须明确它是新增权限，与当前冻结下层直接不兼容。

可用来解释协调的关系为：`q_(t+1)=IK(T_base(t+1)^−1 T_route(s_t+uΔt), q_t)`；因此v、ω改变臂目标在基座中的相对位姿及分支，而u改变必须被跟随的路线进度。上层利用每个底座子目标诱导的整段B3+IK+碰撞结果反过来选底座。这一关系是源码推导，不是本轮新实验。

## 5. 两科学问题应如何收紧

**问题1可检验定义**：同一底座安装传感器/共享2.5D栅格，是否保留了判定“这个底座候选所诱导的固定末端路线/全臂扫掠是否可执行”所需的信息？底座需要平面占用和通行信息，臂还需要高度层的占据/空隙、沿给定位姿路线的可达性和关节连续性、未来暴露但当前被场景遮挡的几何。该差异是任务所需信息不同及表示压缩问题，而不是已证明的异构观测矛盾。

具体可区分三类，不混作同一成因：

- **不可观测**：当前视角FOV/场景遮挡内没有观测到的几何；只能通过移动获得新扫描或维护不确定性，不能靠重编码凭空恢复确定真值。
- **已观测但压缩**：深度落点压成最大高度，丢失垂直多层结构，LocalCollision进一步把它变成从地面到最大高度的实心柱。即使已看到桌面或横杆，也未必能表达其下空隙；是否会影响当前地图须以具体场景检查，不由表示能力局限直接推断现有失败率。
- **已知但摘要不足**：给定路线/关节本身可得，但候选19维特征与3风险数压缩了部位、时刻与分支结构；未来15点仅xyz，未来姿态主要隐含在IK推演中。需和已有VCM/全身风险/IK推演比较，不能宣称此前毫无协调信息。

**问题2可检验定义**：在上层只选底座子目标、下层只调固定路径速度及底座速度的权限下，能否提前区分“底座可通行但臂沿路径不可达/碰撞/分支跳变”与“底座稍绕行却保留后续末端可执行性”的候选？要研究的是现有段推演/摘要/部分观测下，如何用任务约束反向改变选点，而不是仅将两个SAC按层次连接。

两者联系：决定候选价值的变量不是整张图恢复得多逼真，而是**在给定轨迹、当前q和冻结B3条件下，哪些未知/丢失信息会改变可执行性判断**。适合最小方案的补充量可以针对分部位/分高度/沿程风险或可执行性不确定性；但要先确认现有输入和日志能提供标签，避免真值泄漏或靠多候选/更大预算取得表面收益。

## 6. 不应做的因果推断与实现状态

- task10当前[学习器](/home/ybc/projects/CL-FoReM-task10/forem/src/task10/learning.py:138)要求stage1；[UpperModel](/home/ybc/projects/CL-FoReM-task10/forem/src/task7_upper/model.py:76)只在2/3等阶段调用学习WM。代码库有WM类不代表当前模型已使用、训练或有效。
- task10.17已报告单种子10k最终9/12对uniform10/12，样本少且此前反复使用validation；按既有来源 [SRC-T10-FINAL-20261106](../../../SOURCES.md#src-t10-final-20261106) 只能说该验证未显示长训收益，不能据此证明观测差异致败。
- task12.7状态review是已完成流水线交审核，不能沿会议“还在探索”说完全未实现；但点/状态级局部教师结果不等于新传感视角下的真实完整回合改善。此轮不重算收益，引用[SRC-T12-025](../../../SOURCES.md#src-t12-025)。
- 活动task9 BioIK/RLlib实验仍单独运行，不能把这些探索当成冻结B3已经使用BioIK，也不能把运动学IK残差叫做机械臂电机跟踪误差。
- 不能由共享图高度压缩推断所有失败都来自观测。已有IK、自碰、原地零进展、学习目标/样本量等替代解释；新增研究需要匹配场景因子与干预，而非只看总成功率。

## 7. 父任务用来源条目草案

<a id="source-draft"></a>
**SRC-P3-SYSTEM**（建议父追加SOURCES稳定锚点`src-p3-system`）：

- 主张：2026-11-06当前task10冻结B3观测、动作、给定末端轨迹+IK权限，ghost-v1共享传感、2.5D落点图及已有全身推演/风险/记忆机制；task12实现与未接入边界。
- 类型：项目源码/任务原始记录；附有明确标注的能力推导，不是新实测。
- 作者/版本：FoReM；task10 HEAD `91f538cf2ee10bebffd6b643d5c908fa0d419ced`+dirty，task9 HEAD `d198e5ca48f86071c05274f9da753f393ce058b4`+dirty；冻结actor SHA见本文；10k运行精确源码看`t10-long-20261104-s101-r2`冻结清单，不以HEAD替代。
- 精确位置：本文§2–4的链接；关键`task10.lower.FrozenB3.select_action`，`task7_lower.observation.FIELDS/preprocess`，`task8_sim.perception.PcdPanorama.__call__`，`task7_sim.perception.Grid.update/crop, LocalCollision`，`Core.observe/step/feature_vector`，`motion.actions/Route`，`Kinematics.solve_world/solve_tcp_in_arm`，`candidates.generate_candidates`，`risk.sweep_metrics`，`task10.environment.predict_candidates/_upper_observation`，`task7_upper.stages.environment_inputs`、`vcm.VCM`、`model.UpperModel.forward`；task12.7 RESULTS。
- 核查：2026-11-06 Codex，只读原始源码和任务记录；未运行推理/实验、未复做既有全量hash。
- 原始结论：共享传感、固定路径与IK驱动、底座和末端路线速度有限权限；当前显式推演已有耦合但局部图无未来扫描；学习WM评分尚未启用。
- 项目采用/限制：用于界定paper3研究对象、排除不兼容方法。2.5D几何信息丢失和未知区域是结构性局限，尚未证明其导致当前任何比例的失败；不把理想运动学状态当真机反馈，不将局部教师结果当完整任务收益。

## 8. 交接

目标和授权已完成：只读查明当前观测/动作/层级权限，为父文献适用性筛选提供限制。剩余为父整合文献与方案、将来源草案登记SOURCES并检验链接。无运行任务由本节点接管。新方法、标签收集、场景干预、实验与实现全部尚未执行，需另行授权。
