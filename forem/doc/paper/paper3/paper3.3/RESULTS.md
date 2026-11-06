# paper3.3 — 底座—机械臂协调文献结果

run-id：paper3.3-r1-20261106；负责人Codex子Agent；状态done（父已核关键原始证据并登记来源）。实际模型/推理强度未知。推荐Codex GPT6.1sol、Claude Sonnet5.5，跨文献核对medium、研究设计high。只做联网阅读和文档；无代码执行、训练、仿真或提交。

## 1. 检索范围、阅读证据与筛选

检索日期2026-11-06；优先2024—当日，保留直接上游2023及reachability先验2022。搜索词实际包括：`mobile manipulation reinforcement learning base arm coordination reachability 2024 2025`、`N2M2 learning navigation arbitrary mobile manipulation`、`Predictive Reachability mobile manipulation project`、`N2M Bridging Navigation github`、`mobile manipulation 2026 coordination reachability`、`MoTo 2509.01658`、`MoMa-Pos mobile manipulation 2024 2025`。搜索引擎发现线索后访问arXiv、PMLR、作者主页和官方仓库；没有以二手网站承担技术结论。

三篇核心论文PDF下载并以pdftotext阅读全部正文：N²M² 19页（正文至18页，末尾参考文献）、MMDirector 8页、N2M正式PMLR版20页（正文与附录均读；参考文献仅书目信息检索，未追读每条引用）。本地原件在`forem/results/paper3/literature/c-n2m2.pdf`、`c-mmdirector.pdf`、`c-n2m.pdf`；同名txt是阅读提取件，非复现实验。N²M² PDF提取有图形路径warning，但正文可读；不据无法辨认图形中的数值作结论。MMDirector、N2M指定HTML版本404后改用PDF，未伪称原文不可得。源码阅读深度：仅N2M、MoMa-Pos官方README及N²M²本地git remote身份，未审计算法实现。

|编号|标题/年份与状态|原文与官方代码|问题与相关性|筛选理由和阅读深度|
|---|---|---|---|---|
|C01|N²M²: Learning Navigation for Arbitrary Mobile Manipulation Motions in Unseen and Dynamic Environments；2023 T-RO，arXiv首发2022|[论文v2](https://arxiv.org/abs/2206.08737v2)；[官方代码](https://github.com/robot-learning-freiburg/mobile-rl)|Q2直接；Q1直接局限|与给定末端轨迹＋IK＋底座SAC最接近；已读全文正文；[来源](../../../SOURCES.md#src-p3-c01)|
|C02|Predictive Reachability for Embodiment Selection in Mobile Manipulation Behaviors（MMDirector）；2024预印本，2025 RA-L/作者列IROS展示|[原文v1](https://arxiv.org/abs/2410.21059)；[RA-L DOI](https://doi.org/10.1109/LRA.2025.3539097)；未核到作者公开代码|Q2直接；Q1可迁移|预测到达和碰撞驱动动作主体选择，反驳“WM＋分层即新颖”；已读预印本全文，未核RA-L最终版差异；[来源](../../../SOURCES.md#src-p3-c02)|
|C03|N2M: Bridging Navigation and Manipulation by Learning Pose Preference from Rollout；2025预印本→ICML 2026正式PMLR|[正式论文](https://proceedings.mlr.press/v306/chai26a.html)；[代码](https://github.com/clvrai/N2M)|Q1/Q2直接但任务不同|观察视角鲁棒性＋固定操纵策略偏好底座姿态，最接近task12监督选点；已读正式全文含附录、仅README源码范围；[来源](../../../SOURCES.md#src-p3-c03)|
|C04|Whole-Body Model Predictive Control for Mobile Manipulation with Task Priority Transition；ICRA 2025|[作者页/PDF](https://wbmpc.github.io/)；页面未提供核验到的代码|Q2直接机制参考；Q1未处理|多任务和时间维共同优先级，明确协调不等于层次；仅摘要、引言与作者页，非精读；[来源](../../../SOURCES.md#src-p3-c04)|
|C05|MoTo: A Zero-shot Plug-in Interaction-aware Navigation for General Mobile Manipulation；CoRL 2025（arXiv及作者页注明）|[原文](https://arxiv.org/abs/2509.01658)；[作者页](https://gary3410.github.io/MoTo/)（未核到代码）|Q2直接；Q1可迁移|任务交互关键点和底座/臂几何优化，有RGB-D及自由臂姿态需求；已读摘要、引言、§3问题定义与作者机制页，非精读；[来源](../../../SOURCES.md#src-p3-c05)|
|C06|MoMa-Pos: An Efficient Object-Kinematic-Aware Base Placement Optimization Framework for Mobile Manipulation；2024 arXiv v2；作者仓库另列2026 LNCS正式版，标题Determination|[预印本](https://arxiv.org/abs/2403.19940)；[代码](https://github.com/AutonoBot-Lab/Project_MoMa-Pos)|Q1/Q2直接机制参考|任务相关对象筛选、物体运动学与逆可达性共同约束选位；摘要及README，非精读；未核正式版内容差异；[来源](../../../SOURCES.md#src-p3-c06)|
|C07|Robot Learning of Mobile Manipulation with Reachability Behavior Priors；RA-L 2022|[作者PDF](https://www.ias.informatik.tu-darmstadt.de/uploads/Team/SnehalJauhri/RAL22_Robot_Learning_of_Mobile_Manipulation_with_Reachability_Behavior_Priors.pdf)；[代码](https://github.com/iROSA-lab/rlmmbp)|Q2直接基础；Q1未覆盖|可达性先验＋连续底座/离散启臂混合动作；已读摘要/引言及作者说明，非精读；[来源](../../../SOURCES.md#src-p3-c07)|

另发现HERON（2026-10-28 obstacle-aware reachability）与IJCAI2026 Spatially Generalizable Mobile Manipulation via Adaptive Experience Selection and Dynamic Imagination，已交父作新颖性再查；在本节点没有读原文，不计入上述精读或作为结论依据。

## 2. C01 N²M²：协调已经存在，缺口在表示与执行约束的覆盖

依据[C01](../../../SOURCES.md#src-p3-c01)，原文§III-A–F、§IV-C/E/I/K、Fig.2/7、Table IV。

1. **对象、任务、观测、动作。** PR2/HSR/TIAGo，包括全向和差速底座；任务由末端运动生成器给定SE(3)运动，包含pick-place、开门/柜/抽屉和任意样条。策略看到基座系末端当前/下一目标姿态、下一运动速度、局部前瞻目标、关节状态、上一动作和基座中心2D占据图。输出底座速度、适用平台的torso速度、末端运动速度模长，剩余臂关节由BioIK求解。不是端到端全关节策略。
2. **机制。** §III-B Eq.(2)用期望与实际末端位置/旋转误差作为运动学可行性奖励，BioIK最小位移目标抑制配置跳变；§III-D Eq.(5)缩放给定末端速度方向，策略可使臂等待底座绕行；Eq.(8)结合IK误差、底座碰撞、动作变化和速度代价。末端路径训练生成器Eq.(9)还约束路径不要离底座可通行路径过远。这是任务→臂轨迹→底座决策、底座动作→IK残差→学习的双向耦合，并非两策略串联。
3. **两问题覆盖。** Q2已有明确直接解法，FoReM不能把“臂约束影响底座”重新包装成首创。Q1通过基座坐标系与局部多分辨率图处理表达，但训练时2D地图与底座碰撞不覆盖完整臂体3D扫掠；§IV-K/ Fig.7明确报告腕/肘碰撞与头部姿态分布外自碰撞。末端路径规划器与底座策略获得的信息也不等同：§IV-C非动态任务末端规划器看真值地图，策略仅局部图（解析环境真值，物理/真机传感器图）。这些是原文事实，不能自动认定FoReM仍具有同一缺口。
4. **实验证据。** Table IV逐项加BioIK＋L2＋跳变约束、torso、EE速度、地图/训练多样性；这是单种子递增消融，最后一项还同时换训练环境，不能独立归因为地图表示。Fig.5显示绕障时EE速度下降，是行为可视化而非因果消融。Table VI/VII是整体迁移证据，§IV-K细分失败说明未解决范围；不能横排其成功率与FoReM或其他论文比较。
5. **迁移。** 当前已有路径/IK/关节状态时，可直接复用“同轨迹相位下评估候选过程的IK残差、碰撞和进度”这一设计基准，无需增加自由关节动作。若增加3D臂相关表示，须先核现有扫描/碰撞信息以及策略可见性，再决定标签或编码。
6. **缺条件。** 原文torso控制不适用于无升降关节Husky+UR5；真机低层控制误差研究不能在理想IK环境中凭空宣称已解决；其地图尺寸/频率不得照搬为UR5合理值。
7. **空白与限制。** 单步可行与2D底座安全不等于整个未来片段臂体安全；固定末端路线可能自身过难。推荐研究前先区分信息缺失、候选覆盖不足、IK分支和执行器误差，不能全部归于观测。

## 3. C02 MMDirector：任务成功与碰撞预测用于主体选择，仍不是持续全身协调

依据[C02](../../../SOURCES.md#src-p3-c02)，预印本§III-A–C Eq.(1)–(8)、Table I、§IV-A–D/Fig.6–10、§V。

1. **对象与条件。** PyBullet Toyota HSR基本reaching；底座前后/偏航，臂仅3关节、手不动；工人策略以one-hot索引预定义动作数组。正文§IV-A观测含RGB、depth、本体状态，障碍环境还含2D rays；不能照摘要写“只有图像”。目标固定、初始底座位置/偏航随机，四种环境区分底座障碍、臂障碍及房间。
2. **核心机制。** RSSM重建观测并预测任务奖励和碰撞（Eq.1–2）。对当前潜变量imagined rollout，满足“至少一次预测成功奖励超过门限，且所有预测碰撞低于门限”才定义predictively reachable（§III-B/Fig.4）。选择器按Table I得到臂可达/不可达奖励，选择底座时为零；mask又条件化manager并过滤worker动作，确保同一阶段只动所选子系统。协调确切发生在**预测任务可达性→主体选择奖励→动作mask**，不是仅因有三层网络。
3. **两问题。** Q2明确处理“何时转臂”，并且预测碰撞使仅几何可达但受阻的区域不被选中。Q1使用视觉潜状态和任务/碰撞预测，具备任务相关表示思想；没有观测差异/遮挡的专门控制实验，不能称已解决底座与臂观测不一致。它按底座阶段/臂阶段分离，与FoReM持续末端轨迹＋底座同时运动的合同不同。
4. **实验/消融。** Fig.7臂选择底座位置、Table II选择时序和近目标比例支持选择行为，Fig.7(c)臂障碍侧的选择变化支持碰撞预测的合理性，但不是单独去碰撞预测因果消融。Fig.10只针对progress vs exploration奖励、manager-worker层次；Fig.6的DE/DG/NO改变示范使用，支持示范/目标条件重要性，不能全归功WM。其无障碍/房间表现并非处处最好；§IV-C分析56个失败，大部分是选对主体但臂动作未学好，§V承认策略依赖的可达性会不稳定。
5. **可借鉴。** 预测量应是决策相关的到达/碰撞/跟踪风险，不能只报图像或latent重建误差下降；“物理存在解”与“冻结策略实际会执行成功”必须区分。对FoReM可以预测固定下层在候选条件下的风险，保留既有动作权限，不照搬动作mask。
6. **新增要求。** 原方法需整套视觉WM、联合训练三层策略、示范与stage-goal标签。FoReM未因此具备视觉示范数据；换mask会改变任务，不兼容冻结下层的最小改动要求。其预测门限/18步horizon只属于该论文设置，不能当FoReM推荐参数。
7. **留下的空白。** 对本项目可研究的是在冻结执行器、持续轨迹和部分几何观测下，风险估计如何影响候选选择及何时失准；不是重新提出predictive reachability。必须加入相同候选数/推理预算的直接风险预测与短rollout参照，否则收益无法归因动态模型。

## 4. C03 N2M：最直接削弱“教师成功标签→选点网络”新颖性

依据[C03](../../../SOURCES.md#src-p3-c03)，正式论文§3 Eq.(1–2)、§5–7、Appendix A–D。

1. **对象/任务。** RoboCasa Panda-on-Omron，真机RB-Y1；固定操纵策略（BC/DP/ACT、π0）与导航模块之间插入选位器。输入单帧自身视角RGB点云，输出底座初始姿态分布；真机可含torso高度，初始臂关节固定以与底座姿态解耦。任务包括柜/抽屉操作、pick-place、取灯和连续pick/drop。
2. **机制。** 用成功policy rollout收集局部场景与偏好姿态(S,p)，训练时从重建场景渲染不同视角，所有样本和标签变换到机器人自身坐标系。Point-BERT＋MLP输出GMM参数（Eq.1），负对数似然训练（Eq.2，Appendix A.2加模式熵/分离正则）。推理从分布采样并做底座碰撞检查，再转移到姿态执行原策略。
3. **两问题的联系。** Q1处理导航终点带来的输入视角变化：不同视角的观测指向同一策略偏好位置，监督训练增加视角鲁棒性；Q2用操纵策略实际成功偏好反向决定底座终点，优于只看臂几何可达这一问题意识。其依据不是“异构传感器必须融合”，也不要求换操纵器。它没显式预测未知遮挡：augmentation过滤物体不可见视角，测试也要求物体可见；点云噪声/远距离是作者报告失败条件。
4. **证据强弱。** Fig.15/App.D.2去视角增强及视角数消融直接支持表示训练机制；Fig.16编码器/预训练消融显示不能把增益都归大骨干；Fig.5/6、Table1及真机Fig.7/8是整体表现。不同章节reachability基线实现有差异：多数是半径/区域启发式，benchmark App.B.6使用IK和碰撞。不能把所有比较一概写成击败严格全身规划。额外四项真机演示App.D.1.3使用人工规则、未训练操纵策略，不是四项端到端成功实验。
5. **可借鉴。** 冻结下层、policy-specific标签与当前task12有高度重叠。视角增强/坐标统一可作为对照，不必采用GMM或Point-BERT。必须训练/评测按地图与任务轨迹分离，且将“同状态候选排序”与“候选集是否覆盖成功动作”分开。
6. **目前不具备/接口差异。** FoReM没有因此获得RGB点云重建或torso动作；输入扫描是否可构造所需3D局部表征由系统核查决定。更关键：N2M仿真App.B.5直接用MuJoCo API把机器人放在预测姿态，真机App.C.5过渡规划未考虑碰撞；不能借其结果证明沿途可执行。其固定初始臂姿态与FoReM每次上层决策时不同q、轨迹相位也不同。
7. **具体研究空白候选。** 固定执行器下，**同一个底座终点因当前q、既定末端轨迹相位和沿途可见障碍不同而有不同安全性**。将终点偏好改为从当前状态实际可执行的整段风险，而保留动作/候选集；是否有价值需实验证伪。该差异仍需与更多2026轨迹/世界模型论文对查，不能据本篇未处理就宣称领域空白。

## 5. 横向比较与可供父融合的最小方案建议

|方法|协调发生处|观测/表示处理|对本项目最重要的局限|
|---|---|---|---|
|N²M²|末端轨迹条件＋IK奖励＋底座/EE速度联合学习|局部2D图与本体在基座系结合|不是独立创新起点；上游明确缺完整3D臂碰撞，FoReM是否已补必须核源码|
|MMDirector|潜在rollout奖励/碰撞→可达判定→embodiment mask|视觉RSSM、任务奖励预测|分阶段启底座/臂，非连续轨迹同时运动；无专门遮挡消融|
|N2M|操纵rollout偏好→导航终点分布|多视角渲染监督、ego点云|终点选好不保证过渡可执行；固定初始q及目标可见前提|

**建议而非实施**：先保留冻结下层、同一候选集及当前规则mask；构造候选条件下的“过程可执行性评分”而非另造底座/臂策略。输入应含当前合法观测、q、轨迹相位/局部末端片段、候选；输出可分解为臂碰撞、IK/跟踪失败、底座碰撞及路线进度。优先直接监督风险头作为小模型参照；只有存在长期传播证据时再比较动态预测。公式只是建议：`score(c)=predicted_progress(c)−λb risk_base(c)−λa risk_arm(c)−λk risk_IK(c)`，λ尚未定，不是已批准协议。

与Q1的连接必须来自**实际有限观测对风险相关几何/轨迹信息的遗漏**，不能凭空加RGB或假设双传感器；若当前策略已看到全部必要几何，则先研究表示是否能提取相关部分，不能以“不可观测”包装网络学习困难。必须保留未知与空闲的区别，并将风险分层的收益和增加输入/标签/容量的收益拆开。

可证伪检查建议：固定地图/初态/候选/下层，比较原上层、直接success-only排序、显式过程风险排序，按近臂障碍但底座可通行、IK受限、普通场景分组；去q/轨迹相位、去臂相关几何、终点特征替代过程特征、同容量随机辅助标签作为必要取舍候选。指标至少包括严格路线成功、臂/底座碰撞分解、IK失败、风险校准与候选漏选，另报同墙钟推理成本。若新增表示不改善风险识别、过程评分不优于等成本终点评分或收益仅来自更多候选/数据，应否定相应机制假设。所有采数/模型/新分组均需用户另授权。

## 6. 供父追加全局SOURCES的条目草案

以下稳定编号由本节点使用，父负责登记全局。核查日期均2026-11-06，核查人Codex（paper3.3）。均为外部文献；没有本项目实测。

### SRC-P3-C01
- 主张：给定末端运动、IK约束与底座SAC/末端速度已显式耦合；2D底座图不能覆盖原文所有臂碰撞。
- 作者/标题/版本：Daniel Honerkamp、Tim Welschehold、Abhinav Valada；N²M²；T-RO 2023，arXiv2206.08737v2。
- URL/DOI：https://arxiv.org/abs/2206.08737v2；10.1109/TRO.2023.3284346；原件`forem/results/paper3/literature/c-n2m2.pdf`。
- 精确位置：§III-B Eq.(2)、§III-C–F Eq.(4–9)、Fig.2、§IV-C/E Table IV、§IV-I/K Fig.7。
- 原始结论：IK残差等目标训练基座/速度协调；单种子递增消融及跨环境实验支持整体方案，原文列臂碰撞、控制器独立及轨迹过约束局限。
- 采用与限制：作上游对照与缺口界定；不能把其传感器/碰撞局限直接归给FoReM，不能迁移成功率或参数。
- 阅读：正文全文；代码仅核官方仓库身份，未审计源码。

### SRC-P3-C02
- 主张：世界模型预测成功/碰撞以判可达性，再通过奖励和mask控制底座/臂切换已有先例。
- 作者/标题/版本：Xiaoxu Feng、Takato Horii、Takayuki Nagai；Predictive Reachability for Embodiment Selection in Mobile Manipulation Behaviors；arXiv2410.21059v1(2024)，作者页确认RA-L 2025。
- URL/DOI：https://arxiv.org/abs/2410.21059；10.1109/LRA.2025.3539097；状态核查https://www.takatohorii.jp/en/research/mobile-manipulation-embodiment/；原件`forem/results/paper3/literature/c-mmdirector.pdf`。
- 精确位置：§III-B Fig.4/Table I、§III-C Eq.(1–8)、§IV-A观测与动作、§IV-C/D Fig.6–10、§V局限。
- 原始结论：HSR基础reaching中预测可达性改善主体选择；示范目标/层次对训练重要，仍有策略学习及预测稳定性问题。
- 采用与限制：预测任务风险的先例，不可把分离主体动作直接替代当前连续任务；未核最终发表版差异、未核官方代码；原文不是仅RGB输入。
- 阅读：预印本正文全文。

### SRC-P3-C03
- 主张：固定操纵策略rollout偏好＋多视角增强已用于底座选位；其任务不验证持续轨迹过渡可执行性。
- 作者/标题/版本：Kaixin Chai、Hyunjun Lee、Joseph J Lim；N2M: Bridging Navigation and Manipulation by Learning Pose Preference from Rollout；ICML2026/PMLR306 pp.12363–12382正式版。
- URL：https://proceedings.mlr.press/v306/chai26a.html；PDF https://raw.githubusercontent.com/mlresearch/v306/main/assets/chai26a/chai26a.pdf；代码https://github.com/clvrai/N2M；原件`forem/results/paper3/literature/c-n2m.pdf`。
- 精确位置：§3.2 Eq.(1–2)、§3.3.2；Appendix B.4–6/C.4–5；§7、App.D.1.3/D.2/Fig.15–16/D.4。
- 原始结论：policy-aware姿态分布和视角增强改善其设置表现；消融支持增强；仿真直接摆放姿态、真机过渡规划不处理碰撞、不可见视角被过滤、部分额外任务为人工标签演示。
- 采用与限制：作为task12/候选评分最接近工作，不以“rollout学选点”为独立贡献；当前q/轨迹相位和过程风险差异需另证。其timing含部分作者假设，不搬到FoReM估计。
- 阅读：正式全文正文及附录；官方README，未审计训练代码。

### SRC-P3-C04
- 主张：任务优先级在任务及时间维联合处理是显式全身协调的另一机制。
- 作者/标题/版本：Yushi Wang、Ruoqu Chen、Mingguo Zhao；Whole-Body Model Predictive Control for Mobile Manipulation with Task Priority Transition；ICRA2025（作者页）。
- URL：https://wbmpc.github.io/；https://wbmpc.github.io/static/pdfs/paper.pdf。
- 精确位置：作者页Abstract、论文p.1 Introduction及贡献。
- 原始结论：提出WBMPC、门开启/通过实验；本节点不引用摘要性能数字。
- 采用与限制：用于筛选/研究机制参照，不据此声称适配冻结下层，也不声称处理遮挡；未全文精读，代码未核。

### SRC-P3-C05
- 主张：互动关键点与联合几何优化已用于把固定操纵模型连接到底座泊位。
- 作者/标题/版本：Zhenyu Wu等；MoTo: A Zero-shot Plug-in Interaction-aware Navigation for General Mobile Manipulation；CoRL2025（arXiv及作者页）。
- URL：https://arxiv.org/abs/2509.01658；https://arxiv.org/html/2509.01658v1；https://gary3410.github.io/MoTo/。
- 精确位置：摘要、§1/§3、作者页Approach。
- 原始结论：VLM多视角关键点、底座与臂优化；§3观测为外部/腕部RGB-D，动作有底座和6DoF臂姿态。
- 采用与限制：与FoReM动作权限不同，不能因模块化直接接入；仅摘要/部分正文，未精读实验、未核代码，不引用增益数字。

### SRC-P3-C06
- 主张：任务相关对象重建与物体运动学约束已用于底座选位，不应把泛称task relevance作为新颖性。
- 作者/标题/版本：Beichen Shao等；MoMa-Pos；arXiv2403.19940v2(2024)，仓库引用2026 LNCS正式版Determination标题。
- URL：https://arxiv.org/abs/2403.19940；https://github.com/AutonoBot-Lab/Project_MoMa-Pos；作者仓库列DOI10.1007/978-981-95-8405-5_14。
- 精确位置：arXiv摘要；README Reference和project description。
- 原始结论：以对象重要性筛选重建、逆可达图和环境运动学决定底座位置。
- 采用与限制：只筛选与新颖性提醒；正文/正式版差异待核，不引用实验效果，未审计代码。

### SRC-P3-C07
- 主张：基于可达性先验的连续底座＋离散启臂学习已有基础方法。
- 作者/标题/版本：Snehal Jauhri、Jan Peters、Georgia Chalvatzaki；Robot Learning of Mobile Manipulation with Reachability Behavior Priors；RA-L2022 7(3)8399–8406。
- URL：https://www.ias.informatik.tu-darmstadt.de/uploads/Team/SnehalJauhri/RAL22_Robot_Learning_of_Mobile_Manipulation_with_Reachability_Behavior_Priors.pdf；https://pearl-lab.com/2022/02/24/rlmmbp/；代码https://github.com/iROSA-lab/rlmmbp。
- 精确位置：论文p.1摘要/引言，作者页Our Contributions/Boosted Hybrid RL。
- 原始结论：混合动作RL、可达性行为先验、残差Q及策略正则迁移；TIAGo++任务展示。
- 采用与限制：基础背景，非连续末端轨迹安全保证；只读摘要/引言/作者解释，不声称精读或复现。

## 7. 交接

已完成7篇初筛、3篇全文核心分析；父负责全局SOURCES登记、系统审计约束、与观测组去重以及方案最终取舍。没有启动新方法或实验。风险：MMDirector最终发表版未对读；C04–C07不作为精读计数；新颖性结论仅限已读范围。下一步按父综合结果形成用户可批准的建议，不能自动实施。

父验收更新（2026-11-06T11:51:18.109670+08:00）：关键原文/适用边界定向核对完成，SRC-P3来源已登记全局，研究交付done；原“待父登记”段为交接历史。无实施授权变化。
