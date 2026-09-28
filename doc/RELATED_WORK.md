# 相关工作矩阵与创新边界

更新/检索：2026-09-28（Asia/Shanghai）。任务：RESEARCH-028-LIT；状态：首轮 `review`。检索、失败与原文核查记录见 [任务日志](agent_logs/20260928-research-literature.md)。

本轮只服务“将世界模型闭环引入 Husky + UR5 + Robotiq85”；按用户最新澄清，不开展 TopAY、NMoMA 或 planner tuning 路线。下面九篇是关键机制的首轮样本，**不是穷尽检索，也不能据此认定新颖性已经成立**。仅采用作者论文、作者项目页和正式会议原文；未运行这些方法，论文报告不等于本项目复现。

项目事实以 [进度](PROGRESS.md)、[决策 D28/D29/D33](DECISIONS.md) 和[实验审计](RESEARCH_EXPERIMENTS.md)为准：P1a 已有预测器，但本轮确认训练/评测的窗口索引遗漏起点 t；D26–D28 数值保留为受缺陷影响的历史产物，不能作为完整轨迹上的有效正/负结论。P1a 尚无有效出口证据，需先修正确性并重训重测；P2 尚未实现。当前输入为状态向量与局部占据图，最终动作仍由 SAC 输出。不能把原论文实验数值、RGB-D/语言能力或完整世界模型闭环写成项目成果。

## 阅读口径与机制定位

`F` 表示已获取全文并核对所列关键章节，**不表示逐公式、逐代码或逐超参数复现**；`A` 仅摘要核实；`U` 未核实。本轮九项均为 F。数据规模/硬件等未逐项核验时，不凭摘要补数。以下“本项目差异/适用边界”是研究分析；作者明确的局限会单独指出。

| ID | 来源与机制 | 模型影响决策的位置 | 对本项目的直接约束 |
|---|---|---|---|
| RW01 | N²M²：观测驱动 SAC + IK | 当前观测直接更新策略动作 | 基线已有感知反馈；不能整体称开环 |
| RW02 | SC²-WM：潜在前瞻修正 | 执行前修正状态，再由策略决策 | 是明确方法来源；迁移本身不能充当新机制 |
| RW03 | I2A：学习解释模型 rollout | 前瞻编码加入策略上下文 | “模型增强策略”已有，同结构 copy 对照也已有 |
| RW04 | PlaNet：潜在模型预测控制 | 模型搜索直接产生动作 | 属外部方法家族对比，非本项目最终动作架构 |
| RW05 | TD-MPC2：任务相关潜在 MPC | 回报/价值引导在线搜索 | 预测 MSE 改善不等于控制收益 |
| RW06 | MBPO：短模型 rollout + SAC | 训练数据生成 | SAC 加世界模型已有；需明确推理时修正的区别 |
| RW07 | PETS：概率集成 + MPC | 不确定性传播后搜索动作 | 集成/方差并不自动给出安全保证 |
| RW08 | Visual Foresight：视觉 MPC | 新观测更新预测、滚动重规划 | 模型预测加执行反馈不是新概念 |
| RW09 | BADGR：事件预测 + 滚动控制 | 预测执行事件用于在线决策 | 碰撞/结果预测再决策已有，需超越通用包装 |

## 九篇紧凑记录

### RW01 — N²M²（Honerkamp, Welschehold, Valada；T-RO 2023）

来源：[作者论文](https://arxiv.org/abs/2206.08737)、[作者项目页](https://mobile-rl.cs.uni-freiburg.de/)。核验：F，§III、§IV-B/C/K。

- **Problem / Method**：任意末端运动与底盘协调、避障；分解末端运动生成、SAC 调制和 IK。
- **Input → Output / Model**：机器人状态、目标/下一末端运动、局部占据图 → 底盘及平台支持的躯干/末端速度控制；地图 CNN + SAC actor/critic。
- **Environment / Data**：程序生成 analytical 训练；PR2、HSR、TIAGo 的仿真/实机评测。未核验全部训练数据数量。
- **Baseline / Metrics**：MPC、E2E RL、LKF、RRTConnect、Bi2RRT*；任务成功、规划时间、相对末端路径等。原文成功还约束碰撞、跟踪偏差，analytical 含关节配置跳变；不能直接等同本项目 goal-reached SR。
- **Contribution / Limitation / 项目差异**：通用运动分解与跨场景反应能力；作者指出地图精度、底盘/臂独立控制器误差等限制。本项目新增 Husky 平台与待验证前瞻修正，不能把平台替换本身当新算法。

### RW02 — SC²-WM（Yao et al.；2026，作者 arXiv 标注 ICML 2026）

来源：[作者全文](https://arxiv.org/html/2608.07548)、[作者仓库](https://github.com/sunrise-yuze/SC2_WM)。核验：F，§3、§4、Algorithm 1/2；代码未逐项核验。

- **Problem / Method**：VLN-CE 的内部状态漂移；前瞻差异修正状态，条件触发测试时世界模型更新。
- **Input → Output / Model**：RGB-D、语言、历史 → 潜在前瞻/修正状态 → 导航策略；概率后验/先验、Transformer prior、视觉特征解码与记忆校准。
- **Environment / Data**：R2R-CE、RxR-CE；任务为导航。本文不据其结果推定 Husky 操作收益。
- **Baseline / Metrics**：VLN-3DFF、ETPNav 等及模块消融；SR、SPL、NE、TL、OSR、NDTW/SDTW。
- **Contribution / Limitation / 项目差异**：状态与模型两层修正是已有贡献；连续 SAC、状态/占据图、零初始化残差是本项目迁移约定。没有 RGB-D/语言，不是完整 VLN 复现。时间索引疑点见下节，禁止直接照搬。

### RW03 — Imagination-Augmented Agents（I2A；Racanière et al.；NeurIPS 2017）

来源：[会议原文](https://proceedings.neurips.cc/paper_files/paper/2017/file/9e82757e9a1c12cb710ad680db11f6f1-Paper.pdf)。核验：F，§2–5，尤其 §3.3。

- **Problem / Method**：不完美模型预测仍可能有用；学习解释 imagined rollout，将其加入策略上下文。
- **Input → Output / Model**：观测与候选动作 → 预测观测/奖励序列 → rollout 编码 → 策略/价值；CNN 模型、LSTM 编码、A3C。
- **Environment / Data**：Sokoban、MiniPacman；交互数据预训练模型后训练代理。
- **Baseline / Metrics**：普通/增大容量 model-free、同结构 copy-model、规划对照；解题率、回报、样本/模型调用预算。
- **Contribution / Limitation / 项目差异**：让策略学习采用或忽略不可靠预测；证据主要是离散游戏。本项目是连续移动操作与显式潜在差异，但“策略使用前瞻信息”及“复制模型匹配容量”均已有。

### RW04 — Learning Latent Dynamics for Planning from Pixels（PlaNet；Hafner et al.；ICML 2019）

来源：[会议原文](https://proceedings.mlr.press/v97/hafner19a/hafner19a.pdf)。核验：F，§3–5。

- **Problem / Method**：从图像学可用于多步控制的动态；潜在空间 CEM/MPC 与 latent overshooting。
- **Input → Output / Model**：图像、动作/历史 → 潜在状态、奖励预测 → 在线规划动作；确定性+随机状态空间模型。
- **Environment / Data**：DeepMind Control Suite 六任务，在线交互采集；输入像素。
- **Baseline / Metrics**：A3C、D4PG、真动态规划及模型/规划消融；回报、交互回合、训练时间。
- **Contribution / Limitation / 项目差异**：将潜在动态用于规划；控制基准结果不构成 Husky 碰撞/IK 证据。本项目由 SAC 输出最终动作，不能把 latent MPC 的既有闭环能力改称本项目创新。

### RW05 — TD-MPC2（Hansen, Su, Wang；ICLR 2024）

来源：[作者论文](https://arxiv.org/abs/2310.16828)。核验：F，§3–5、附录 A/H。

- **Problem / Method**：稳定扩展任务相关世界模型；潜在 MPPI、价值终端项、策略先验与训练稳定化。
- **Input → Output / Model**：状态/动作（另有视觉实验）→ 潜在转移、奖励、价值 → 搜索动作；无观测解码器的 MLP 世界模型。
- **Environment / Data**：DMControl、Meta-World、ManiSkill2、MyoSuite，共104在线任务；另有多任务数据实验。
- **Baseline / Metrics**：SAC、DreamerV3、TD-MPC；归一化回报/成功率、样本效率、计算与规模分析。
- **Contribution / Limitation / 项目差异**：强调控制相关预测和跨任务稳定性；不直接验证 Husky。策略先验辅助 MPC，不等于本项目“最终动作始终由 SAC 输出”。论文大模型规模不作为本机预算依据。

### RW06 — When to Trust Your Model: Model-Based Policy Optimization（MBPO；Janner et al.；NeurIPS 2019）

来源：[会议原文](https://proceedings.neurips.cc/paper/2019/file/5faf461eff3099671ad63c6f3f094f7f-Paper.pdf)。核验：F，§4–6。

- **Problem / Method**：模型偏差随 rollout 累积；从真实 replay 状态分叉短模型轨迹，提供策略训练数据。
- **Input → Output / Model**：状态、动作 → 下一状态/奖励分布；bootstrap 概率集成；策略优化为 SAC。
- **Environment / Data**：MuJoCo 连续控制，真实与模型生成转移。
- **Baseline / Metrics**：SAC、PPO、PETS、STEVE、SLBO，含匹配 SAC 更新次数消融；回报、环境样本效率、rollout 长度效应。
- **Contribution / Limitation / 项目差异**：研究如何限制模型使用以控制偏差；训练期合成数据与执行前特征修正不同。不能以“世界模型+SAC”单独主张新颖；若比较必须核算模型数据与额外梯度预算。

### RW07 — Deep RL in a Handful of Trials using Probabilistic Dynamics Models（PETS；Chua et al.；NeurIPS 2018）

来源：[会议原文](https://proceedings.neurips.cc/paper/2018/file/3de568f8597b94bda53149c7d7f5958c-Paper.pdf)。核验：F，§4–7。

- **Problem / Method**：模型误差使 MBRL 控制不稳；概率集成配合粒子轨迹采样和 MPC。
- **Input → Output / Model**：状态、动作 → 下一状态分布 → 回报评估/规划动作；概率网络表示 aleatoric，bootstrap 集成表示 epistemic 不确定性。
- **Environment / Data**：Cartpole、7-DOF Reacher/Pusher、Half-cheetah；任务交互数据。
- **Baseline / Metrics**：SAC、PPO、DDPG、MBMF、GP 模型及传播消融；回报和采样效率。
- **Contribution / Limitation / 项目差异**：不确定性建模与传播已有；回报优化不等于碰撞概率校准或安全保证。本项目尚无通过验证的不确定性模块，若后续采用需单独证明失效识别和收益。

### RW08 — Visual Foresight（Ebert et al.；2018 arXiv）

来源：[作者论文](https://arxiv.org/abs/1812.00568)。核验：F，§3–7、§9.1–9.4、结论；本轮不推定正式发表信息。

- **Problem / Method**：从机器人经验学习未知物体操作；动作条件视频预测、目标评分、视觉 MPC，并用执行观测更新跟踪。
- **Input → Output / Model**：图像、动作、像素/图像目标 → 未来图像/像素分布 → 动作；视频模型与可选配准网络。
- **Environment / Data**：真实桌面操作，自监督交互，刚性/柔性物体。
- **Baseline / Metrics**：DNA/SNA、预测传播/OpenCV/配准跟踪、标定相机控制；像素距离、任务成功率。
- **Contribution / Limitation / 项目差异**：执行观测用于校正预测位置已有直接证据；作者指出可见性、长程与定位精度限制。§9.4 多任务比较双方均采用文中所称 open-loop 设置，不能把该表所有收益归因于执行反馈。本项目无 RGB，且最终为 SAC。

### RW09 — BADGR（Kahn, Abbeel, Levine；2020 arXiv）

来源：[作者论文](https://arxiv.org/abs/2002.05700)。核验：F，§III、§IV、Algorithm 1/2；本轮不补未经核验的正式卷期。

- **Problem / Method**：几何可通行性未必对应物理执行效果；自监督事件预测用于滚动决策。
- **Input → Output / Model**：相机观测与候选动作序列 → 碰撞、颠簸、位置事件 → 执行首动作；CNN+循环预测器。
- **Environment / Data**：Jackal 城市/越野实机，传感器自监督标签、离策略交互；并非 Husky 操作。
- **Baseline / Metrics**：LIDAR 策略、直行策略、跨域再训练对照；到达/碰撞/受困、路径/耗时与地形表现。
- **Contribution / Limitation / 项目差异**：预测执行事件并重复规划已有；作者仍需偶发人工复位。其新增数据后再训练实验不能说成每控制步测试时更新；碰撞标签也不是形式安全证明。本项目需检验操作可行性和 IK，而非照搬导航评分器。

## SC²-WM 迁移必须保留的边界

原文 §3.1 的 `Δ_t = s̃_(t+1) − s_t` 是**预计动作诱发的潜在变化**，不是已观察的预测误差，原文也不要求将其压到零。Algorithm 1 包含真实执行后读取新观测，再进行下一轮后验更新。本项目若记录执行误差，应另用实际执行动作计算 `e_(t+1) = E(o_(t+1)) − wm(E(o_t), a_executed, dt)`，不能以 preview 动作的预测冒充实际动作的误差。[原文 §3.1](https://arxiv.org/html/2608.07548#S3.SS1)

原文 Eq10 是一般 `ψ(s,Δ)`；本项目零初始化残差、同 actor 双次查询、固定编码器和 SAC 训练均是本项目约定。原文 Eq11 的两分支专家动作监督不能替换成“原文采用策略间 KL 正则”。Transformer prior 与项目拟议 GRU 也须区分。[原文 §3.1–3.2](https://arxiv.org/html/2608.07548#S3.SS2)

**未消除的原文疑点**：Eq13 的重建目标为下一时刻视觉特征；§3.3 说测试时使用此目标，但 Algorithm 2 第9行写当前校准特征。两者时间索引不一致；本文仅记录，未核对作者实现，不能选一个当权威答案。P4 前需建立“预测时刻—执行动作—真实目标可用时刻—更新参数”映射。测试时政策 KL 变化只是作者触发依据，不是已校准的模型错误概率。[原文 §3.3](https://arxiv.org/html/2608.07548#S3.SS3)

## 候选 claim 审视与所需机制证据

以下是研究审查，不批准新增模块或跳过 P1/P2 gate。

| 候选表述 | 已有相近工作 / 当前判断 | 本项目至少还需的证据 |
|---|---|---|
| “首次用世界模型闭环控制机器人” | RW04/05/08/09 已覆盖；不能这样写 | 改成针对明确移动操作失败机制的窄问题 |
| “世界模型增强 SAC，而 SAC 仍输出动作” | RW03 已有模型前瞻增强策略；RW06 已有模型+SAC | 区分训练数据增强、推理特征增强和显式修正；同容量/计算/数据对照 |
| “迁移 SC²-WM 后更有效” | 迁移是可测研究假设，不是新机制已成立 | 关闭修正、零/复制/无动作预测、打乱 delta；多训练种子、配对任务结果、真实控制耗时；先通过P1入口 |
| “潜在差异定位并修正执行失败” | delta 本身不是真实误差；目前没有证据 | 记录preview/最终动作、实际动作条件预测残差、碰撞/IK前兆；验证干预delta后的因果效应，而非仅相关性 |
| “执行反馈比一次前瞻更有用” | RW08/09 已有此思想；N²M²自身已有观测反馈 | 隔离模型分支刷新/历史反馈，保留SAC正常观测；在匹配预算下比较首次预测固定、逐步刷新、必要的反应控制对照 |
| “更安全或更会判断不确定性” | RW07已建模不确定性，RW09已有风险事件预测；项目尚未实现 | 碰撞/IK、校准/置信覆盖、分布外失效与误触发；关掉不确定性模块的同预算对照；不能仅报告方差或MSE |
| “修复物理执行误差并可实时部署” | N²M²已指出控制器/定位限制；analytical不能覆盖全部物理误差 | Gazebo/硬件闭环验收、真实反馈来源、时延分位数/超期率、模型失配；当前Gazebo限制必须公开 |

因此当前可维护的中心假设是：**在可信基线与固定预算下，动作条件前瞻经可关闭的策略状态修正，能否减少 Husky 移动操作的特定失败，并优于相同结构但无有效前瞻信息的对照？** 这是待检验问题，尚不是已获支持的论文结论。

## 后续最小检索工作（尚未执行）

1. P1b/P4 启动前，对 SC²-WM 作者代码核对时间索引、先验/后验、双策略关系与更新范围；保留代码版本。
2. 候选 claim 变具体后，以“imagination-augmented policy / latent state correction / mobile manipulation execution error”为词扩展近年研究，检查遗漏与反例；本轮未完成系统性新颖性检索。
3. 若未来主张风险或安全，补校准/约束控制的直接对照文献；本轮 PETS/BADGR 足以界定“采用不确定性/风险预测并非新概念”，不足以建立形式安全主张。
4. 选定可运行外部 baseline 后才核查作者代码依赖、数据许可和本机计算预算；当前矩阵不承诺九个方法全部移植。
