# paper3.2 — 观测差异、任务相关表示与主动感知

状态：done（父已核关键原始证据并登记来源）。负责人：Codex observation_literature；实际模型/强度未知。推荐Codex GPT6.1sol、Claude Sonnet5.5：跨文献medium，新颖性/机制证据high。未运行外部代码、训练或仿真；所有迁移方案为建议。

## 检索记录与范围

检索日期2026-11-06（Asia/Shanghai），优先2024至当日；ActPerMoMa首版2023、正式ICRA2024，保留作为直接基础。实际查询：`mobile manipulation active perception ActPerMoMa occlusion 2024 2025`、`mobile manipulation partial observability active perception reachability 2025 2026`、`Learning on the Move Integrating Action paper`、`Affordance-Guided Coarse-to-Fine Exploration`；并沿作者主页/原文参考文献与父任务线索核查。覆盖公开网页搜索、arXiv原文、IEEE/AAAI官方记录、作者主页、官方GitHub。没有做穷尽检索，不能由本次未检索到推断领域不存在。

三篇核心已通读HTML全文（正文、公式、表格和局限），本地阅读证据保存在 `forem/results/paper3/literature/2310.00433v2.html`、`2602.01731v1.html`、`2609.12081v2.html`，同名txt/compact.txt仅为阅读提取；未把打开摘要计作精读。ActPerMoMa另核查部分官方源码。首次文本提取缺少bs4，改用Python标准库HTMLParser，未安装依赖；无实验失败。

## 初筛表（7篇，核心3篇）

|论文|年份/状态|原文、官方代码或主页|问题/相关性|为何入选；阅读深度|来源|
|---|---|---|---|---|---|
|Active-Perceptive Motion Generation for Mobile Manipulation（ActPerMoMa）|ICRA2024；arXiv v2 2024-03-04|[全文](https://arxiv.org/html/2310.00433v2)、[官方代码](https://github.com/pearl-robot-lab/ActPerMoMa)|Q1+Q2；直接相关|路径信息增益与末端可达性共同决定底座目标；已读全文+部分源码|[O01](../../../SOURCES.md#src-p3-o01)|
|Uncertainty-Aware Non-Prehensile Manipulation with Mobile Manipulators under Object-Induced Occlusion（CURA-PPO）|2026预印本；作者主页标ICRA2026，正式论文集本轮未另核|[全文](https://arxiv.org/html/2602.01731v1)、[作者主页](https://jiw0o.github.io/cura-ppo/)；主页未提供可核实源码链接|Q1+Q2；直接相关问题、迁移参考方法|单一LiDAR遮挡、碰撞分布和运动冗余；已读全文，未核源码|[O02](../../../SOURCES.md#src-p3-o02)|
|MoPA: Coordinated Mobile Manipulation via Subsystem-Specific Perception Alignment|2026预印本；v2 2026-09-14|[全文](https://arxiv.org/html/2609.12081v2)、[主页](https://mopa-policy.github.io/)、[主页Code所指XPolicyLab](https://github.com/XPolicyLab/XPolicyLab)|Q1+Q2；直接相关科学问题，方法迁移参考|显式区分子系统感知条件、动作层保持通信，是“不同空间尺度＋协调”叙事强最近邻；已读全文，代码仅核入口不核实现|[O03](../../../SOURCES.md#src-p3-o03)|
|Affordance-Guided Coarse-to-Fine Exploration for Base Placement in Open-Vocabulary Mobile Manipulation|AAAI2026正式论文；2025首版|[正式记录](https://ojs.aaai.org/index.php/AAAI/article/view/38909)、[原文](https://arxiv.org/html/2511.06240v2)；本轮未核官方代码|Q1+Q2；直接相关基座选择，机制可迁移|把自中心图像信息转到空间地图并结合任务可供性、几何；仅读摘要/引言与正式出版记录，不计精读|[O04](../../../SOURCES.md#src-p3-o04)|
|AnywhereVLA: Language-Conditioned Exploration and Mobile Manipulation|2025预印本|[原文入口](https://arxiv.org/abs/2509.21006)；官方代码本轮未核|Q1+Q2；可迁移参考|摘要明确预抓取基座姿态同时考虑可见性与可达性；任务是开放词汇抓放，非给定轨迹跟踪；仅读摘要|[O05](../../../SOURCES.md#src-p3-o05)|
|TAMPAgent: Agentic Belief-Space Planning for Mobile Manipulation|2026-11-02预印本|[原文](https://arxiv.org/html/2611.03584v1)、[主页](https://umishra.me/TAMPAgent/)；代码未核|Q1+Q2；可迁移参考|观测行动进入belief-space计划，几何约束在运动前验证；只读摘要、引言与结构，不计精读|[O06](../../../SOURCES.md#src-p3-o06)|
|When to Make a Decision: Task-Sufficient Active Perception for Mobile Manipulator Robots|2026概念性预印本，页面日期2026-09-28；无已实现实验结论|[原文](https://arxiv.org/html/2610.23891v1)；代码未核|Q1；背景|强调“何时信息已足够”而非无限提高覆盖；只读摘要/引言/章节结构，原文明示planned evaluation，不用于效果证据|[O07](../../../SOURCES.md#src-p3-o07)|

`Learning on the Move`检索结果含学位论文/报告页面，未进入核心；AAWR虽为NeurIPS2025且主动感知相关，本子任务已有直接移动操作原文，未用固定臂通用结果替代主线。

## 核心精读

### O01 ActPerMoMa：信息价值必须联系任务执行，但收益依场景而变

**原文事实。** TIAGo++在未知杂乱场景抓取指定对象；头部RGB-D累积TSDF，目标区域粗定位已知。机器人采样底座/相机路径，末端抓取由VGN检测并规划执行，非端到端关节RL。§II-B式(1)以信息增益与可执行性之和选路径；式(2)沿途目标区域后侧体素增益按距离平方衰减；式(3)把候选终点下最高抓取可达性按路径长度归一。协调实际发生在“底座终点→末端姿态坐标变换→离线可达图→路径效用”，不是分层名称。§III-B表I/II去掉可达性项的IG-only在普通场景反而更好；复杂侧向hard-grasp条件完整方法61.8%、IG-only56.2%。§III-E指出遮挡严重时IG估计和来回振荡仍有问题。官方代码`actpermoma.py::draw_action`约L407–433、`reachability_utilities`L996–1072与此相符。[O01](../../../SOURCES.md#src-p3-o01)

**证据边界。** “信息增益＋可达性一定更好”被其普通场景消融直接反驳。表III跨方法结果仅支持整套规划表现；可达性图并不等价于沿完整路线无碰撞，原文分离底座、相机、末端姿态也没有解决我们给定末端路径下的连续可行性。代码仅核上述符号，不声称完整复现。

**FoReM迁移判断（推导/建议）。** 我们不需要VGN或目标识别，因为末端路线已给定。可借鉴“把信息限制在任务相关区域，并由末端可行性反向决定底座候选价值”；相关区域应由冻结B3实际推演出的手臂/车体扫掠区域定义，不能直接复制围绕目标物的IG。所需新增量是原始观测的3D已知/未知结构、候选运动与该结构的关系。当前已有ghost全景扫描且没有独立头部动作，原方法5D视角采样和两臂选择均不兼容；只能通过合法底座候选改变视角。原文未覆盖冻结学习控制器诱导的轨迹误差，也未验证任务相关3D信息相对现有2.5D编码的边际收益。

### O02 CURA-PPO：单传感器也会有任务相关信息缺失

**原文事实。** Ridgeback+Franka以底座2D LiDAR推箱；物体遮挡、障碍可在回合中出现。§V-B式(2)置信地图随时间衰减，VAE编码后连同底座系末端/物体/目标状态输入策略；策略输出全向底座和末端速度，经微分IK执行。§V-C式(3)预测折扣碰撞累计量分布，式(5)(6)取均值和方差；§V-D式(8)–(10)以风险TD成本与方差变化修正PPO优势。表II G2分别移除置信、风险、不确定性项；G3比较仅底座推物，图4–7展示利用臂冗余保持接触同时侧移观测。实验仅仿真，§VII把真机部署列为未来工作。[O02](../../../SOURCES.md#src-p3-o02)

**证据边界。** G2较整体基线更能支持机制，但全量模型并非每一格均最优：例如小物体adversarial条件的去risk版本78.20高于完整77.12。分布方差不是已经分离/校准的认知不确定性：也可能包含环境随机、策略结果差异和碰撞累计量尺度。图示方差下降只给案例证据，不能证明任何方差下降都带来信息收益。G3改变机器人运动能力，支持冗余有用，不能单独量化固定平台上的协调模块贡献。

**FoReM迁移判断（推导/建议）。** 这是反对“必须异构传感器才产生观测问题”的直接参考，但我们没有推物任务、动态新障碍或任意末端速度权。静态场景直接加时间衰减会人为遗忘有效观测，未经验证不应采用。可借鉴“任务条件风险估计与观测可靠性分开记录”，在上层预测各候选的碰撞/IK失败分项与置信，而不修改冻结SAC奖励。需要候选实际rollout事件、未知区域掩码及校准数据；不能把现有单张压缩图中的未知区域补成确定真值。待验证空白是：在既有B3+IK推演已经提供耦合信号后，额外信息状态是否仍改善风险校准和最终选点，而非只因多一次模型/更多数据。

### O03 MoPA：两个问题的直接最近邻，不能再把双流本身当新贡献

**原文事实。** §III-A头/腕RGB、本体状态和语言输入，输出臂/夹爪与躯干/底座动作块；§III-C图2和式(2)两组互相屏蔽query从同一VLM上下文提取感知信息。§III-D式(5)各query只匹配本分支动作，但动作分支彼此通信；§III-E式(6)–(9)用同一示教时段的动作训练联合flow，同步生成两块。§IV-B表III固定总query容量的Shared Query为74.7、完整88.3；去query-action联动70.3，开放跨query访问66.3。所有这些消融都保留两动作专家及其通信。仿真为Fetch/ManiSkill-HAB，真机为全向底座、升降和双臂。[O03](../../../SOURCES.md#src-p3-o03)

**证据边界。** 表III支持该架构中感知分工和匹配接口的贡献，但没有去除动作通信的独立对照，不单独证明通信或联合flow本身的因果收益。注意力图、t-SNE只说明表征差异，不说明已完整分解真实任务信息；分工也不是可达性或碰撞的硬保证。整体任务成功率不能与FoReM轨迹完成率排序。

**FoReM迁移判断（推导/建议）。** 其问题描述与会议两问题高度重合，削弱“底座看全局、机械臂看局部、用双流协调”作为创新的充分性。我们可以采用功能分工原则，但应把新增量明确为**同一已观测几何如何针对给定末端路径与候选底座运动产生可检验的可行性信息**。直接移植MoPA须新增视觉语言输入、全身示教、动作分支和大模型，且破坏冻结下层，当前不具备/未授权。该论文未检验单一ghost扫描、已知末端轨迹、只能选候选点的受限接口；这一适用差异本身仍不等于创新，必须提出比换平台更明确的机制并与几何基线比较。

## 按科学问题横向比较与建议

|维度|ActPerMoMa|CURA-PPO|MoPA|对FoReM的约束|
|---|---|---|---|---|
|Q1缺失是什么|目标表面未观测、抓取估计不稳定|物体遮挡及过时观测|共享感知条件未对齐不同动作需求|应拆开原始感知缺失与2.5D压缩损失，不能混作同一误差|
|Q1处理位置|3D地图和候选视角效用|地图置信与碰撞分布|感知到动作的query接口|冻结下层时优先上层附加任务条件几何摘要，不改B3输入|
|Q2耦合位置|抓取可达性决定底座路径分数|底座/末端共同动作、保持接触时改变视角|动作分支通信及同步联合生成|已有B3+IK推演必须作为主对照，不能声称首次引入协调|
|最强机制证据|hard-grasp消融；普通场景负结果|表II组件/冗余对照；仿真限定|表III同query容量分工对照|要设计信息损失确会改变候选排序的测试，不能只看整体成功率|

**给父任务的方案建议，不构成实施授权。** 优先研究“候选条件的任务几何充分性”：使用同一合法扫描，分别估计底座通行相关几何与给定末端轨迹执行相关几何，将两者在候选B3推演中汇合；显式输出已知安全、已知危险、未知三类证据，而非把未知当自由空间。能直接复用原始观测时先做几何计算，不预设学习世界模型。只有几何摘要仍不足且候选风险有可预测残差时，再考虑学习任务风险分布。主动感知分支必须证明它改变合法候选决策，并以同候选数、相同计算预算、相同控制器比较；避免单纯增加候选搜索密度。父任务最新发现的Visibility-Aware Mobile Grasping需重点再核：此处不以“任务扫掠体可见性”宣称新颖。

**最小反证设计建议。** 在物理几何/奖励不变的同一组场景，隔离①完整可用扫描与现有2.5D压缩，②保留/去除臂轨迹条件，③几何分项与学习风险头，④同样预算增加候选数。Q1指标应包括任务相关占据/自由/未知分类错误、风险校准及同输入表征混淆；Q2记录整机碰撞、IK失败、末端跟踪误差、路线进度，以及候选排序的误判。若新增表征只能降低重建损失而不能减少候选错误/任务失败，或收益被等算力搜索解释，则核心假设不成立。具体样本量和算力本子任务不拍数；原文其他平台训练配置不作为FoReM成本估计。

## 可供父任务追加的SOURCES条目草案

以下编号尚待父统一追加；原文事实与本项目推导分开。共同核查日期2026-11-06，核查人Codex observation_literature。

<a id="src-p3-o01-draft"></a>
### SRC-P3-O01 — ActPerMoMa原文与部分官方实现
- 类型：外部文献＋官方源码只读核查。Jauhri、Lueth、Chalvatzaki，*Active-Perceptive Motion Generation for Mobile Manipulation*，ICRA2024，DOI `10.1109/ICRA57147.2024.10610714`；[原文v2](https://arxiv.org/html/2310.00433v2)、[出版记录](https://ieeexplore.ieee.org/document/10610714/)。全文已读。
- 精确位置：§II-B–D式(1)–(3)，§III-B表I/II，§III-C表III，§III-E。官方仓库commit `fdc15f5dd6b6c2cafbdbe18e98e97170e7cf5cd0`，`actpermoma/algos/actpermoma.py::draw_action` L407–433、`reachability_utilities` L996–1072、`ig_fn_parallel` L904–922；仅这些路径核查，未运行。
- 原始结论/支撑：沿路径信息增益与末端抓取可达性共同选底座路径；普通场景IG-only较优，hard-grasp才表现可达性优势；局部reactive规划仍振荡且严重遮挡影响IG。
- 采用/限制：借鉴任务相关信息价值、可达性对底座选择的反馈；不得宣称全面优于去可达性、不把抓取末端目标扩展为连续给定轨迹无碰撞保证。FoReM需要另验其已有B3耦合推演之外的增益。
- 本地证据：`forem/results/paper3/literature/2310.00433v2.html`、`actpermoma-readonly.py.txt`。核查日期/人见本节共同说明。

### SRC-P3-O02 — CURA-PPO的遮挡、分布碰撞与冗余证据
- 类型：外部文献。Hwang、Yang、Jeong、Yoon、Yoon，*Uncertainty-Aware Non-Prehensile Manipulation with Mobile Manipulators under Object-Induced Occlusion*，arXiv:2602.01731v1，2026-02-02；[全文](https://arxiv.org/html/2602.01731v1)、[作者主页](https://jiw0o.github.io/cura-ppo/)标ICRA2026，正式论文集本轮未另核。已读全文，未核源码。
- 精确位置：§V-B式(2)/策略观测动作；§V-C式(3)–(7)；§V-D式(8)–(10)；§VI-C/E表II G2/G3、图4–7；§VII。
- 原始结论/支撑：2D LiDAR局部观测＋时变置信图，条件碰撞累计量分布均值/方差成本引导推物；组件与仅底座消融说明风险、信息及运动冗余的作用。实验均仿真；真机为未来工作。
- 采用/限制：作为单传感器部分可观测性与任务风险估计参考；方差不是已校准纯认知不确定性，静态FoReM不直接采用动态置信衰减，不复制自由末端速度动作或修改冻结下层。
- 本地证据：`forem/results/paper3/literature/2602.01731v1.html`。核查日期/人见共同说明。

### SRC-P3-O03 — MoPA子系统感知对齐与协调最近邻
- 类型：外部预印本＋项目入口核验。Chen等（Guangyu Chen、Qiwei Liang、Shaolong Zhu、Tianxing Chen等），*MoPA: Coordinated Mobile Manipulation via Subsystem-Specific Perception Alignment*，arXiv:2609.12081v2，2026-09-14；[全文](https://arxiv.org/html/2609.12081v2)、[主页](https://mopa-policy.github.io/)。已读全文；主页Code指向[XPolicyLab](https://github.com/XPolicyLab/XPolicyLab)，已核入口含MoPA，不声称实现审计。
- 精确位置：§III-A–E式(1)–(9)/图2，§IV-A输入/动作/示教设置，§IV-B表III，§IV-C图4/5，§IV-D真机设置。
- 原始结论/支撑：共享视觉语言上下文产生隔离query，匹配两动作流并允许动作通信；联合flow同步生成。固定总query容量消融支持分工，但该组消融全部保留动作通信。
- 采用/限制：是两个科学问题叙事强最近邻，不能把双流分工/信息交换本身写成首次；示教全身控制与FoReM冻结受限动作不同；注意力可视化不构成物理安全或充分表示证明。
- 本地证据：`forem/results/paper3/literature/2609.12081v2.html`。核查日期/人见共同说明。

### SRC-P3-O04 — Affordance-Guided基座选择初筛
- 类型：外部正式论文书目及摘要/引言核查。Tzu-Jung Lin、Jia-Fong Yeh、Hung-Ting Su、Chung-Yi Lin、Yi-Ting Chen、Winston H. Hsu，*Affordance-Guided Coarse-to-Fine Exploration for Base Placement in Open-Vocabulary Mobile Manipulation*，AAAI2026 40(22):18443–18451，DOI `10.1609/aaai.v40i22.38909`；[官方记录](https://ojs.aaai.org/index.php/AAAI/article/view/38909)、[原文v2](https://arxiv.org/html/2511.06240v2)。
- 精确位置/深度：官方出版页日期2026-03-14，原文摘要/§1/图1；非全文精读，源码未核。
- 原始主张：任务可供性与空间几何联合决定底座位置，Affordance RGB/Obstacle Map+弥补单RGB视野约束。
- 采用/限制：候选检索与近邻比较线索；不据此声称FoReM需要VLM，不援引未核实验/消融支持具体机制。核查日期/人见共同说明。

### SRC-P3-O05 — AnywhereVLA初筛
- 类型：预印本摘要。Gubernatorov等，*AnywhereVLA: Language-Conditioned Exploration and Mobile Manipulation*，arXiv:2509.21006v1，2025-09-25；[原文入口](https://arxiv.org/abs/2509.21006)。
- 精确位置/深度：摘要；未读全文，未核源码。原始主张：LiDAR/相机SLAM与任务图、语义地图和探索，预抓取基座姿态选择考虑可见性与可达性。
- 采用/限制：证明已有公开方法声称同时考虑两种条件，作为待深核近邻，不能拿摘要整体成功率比较FoReM或证明组件因果。核查日期/人见共同说明。

### SRC-P3-O06 — TAMPAgent最新belief-space方向初筛
- 类型：预印本摘要/引言。Utkarsh A. Mishra、Alperen Degirmenci、Yongxin Chen、Danfei Xu、Tucker Hermans、Caelan Garrett，*TAMPAgent: Agentic Belief-Space Planning for Mobile Manipulation*，arXiv:2611.03584v1，2026-11-02；[原文](https://arxiv.org/html/2611.03584v1)。
- 精确位置/深度：摘要、§1及图1/结构；未通读全文/附录，未核源码。原始主张：计划包含观测与执行行动，执行前须用工具绑定满足几何约束的参数，过程中更新belief。
- 采用/限制：反例说明“将观测与约束共同纳入决策”并非空白；只是最新线索，不能以LVLM工具编排替代FoReM受限控制方案，更不引用未核效果。核查日期/人见共同说明。

### SRC-P3-O07 — Task-Sufficient Active Perception概念性工作
- 类型：概念性预印本。Mariana da Silva Barros、Matthias Kerzel、Cornelius Weber、Stefan Wermter，*When to Make a Decision: Task-Sufficient Active Perception for Mobile Manipulator Robots*，arXiv:2610.23891v1（页面标2026-09-28）；[原文](https://arxiv.org/html/2610.23891v1)。
- 精确位置/深度：摘要/§1/§4.2 Planned Evaluation结构；未全文精读。原始主张：对象belief与符号决策判断任务信息是否足够，提出而非完成实验。
- 采用/限制：只作任务信息充分性的概念背景；不作为效果证据、实现已完成或正式发表证据。核查日期/人见共同说明。

## 交接

完成：7项初筛、3篇全文精读、一篇部分源码核查、逐篇迁移/限制、来源草案。待父：与paper3.1系统原件合并、核对最近邻Visibility-Aware方法、在全局SOURCES追加后检查链接并形成优先方案。风险：2026预印本稳定性/代码完整性未保证，单平台收益不可外推；无方法实施授权。下一步仅父汇总与文档检查；无运行任务、无需要停止/恢复的进程。

父验收更新（2026-11-06T11:51:18.109670+08:00）：关键原文/适用边界定向核对完成，SRC-P3来源已登记全局，研究交付done；原“待父登记”段为交接历史。无实施授权变化。
