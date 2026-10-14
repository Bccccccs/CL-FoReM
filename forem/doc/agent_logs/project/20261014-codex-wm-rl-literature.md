# 世界模型 + 强化学习文献阅读（2026-10-14）

- 工作 ID：PROJECT-WM-RL-LITERATURE-20261014；类型：项目级文献调研；负责人：Codex /root。
- 状态：review（待独立复核或用户确认，未标done）；开始：2026-10-14T11:04:22+08:00。
- 用户要求：按指定清单精读优先论文，其余阅读摘要、方法与实验设置；逐篇九字段、对比表、Task4启示与候选补读；登记来源并提交本轮文件。
- 授权边界：只阅读、写本日志、追加 SOURCES、登记 PROGRESS。不改源码/配置/Task4协议，不装依赖、不运行仿真或训练、不新建任务目录、不派发子 Agent。所有启发均为建议（待用户授权）。
- 计划处理文件：本日志、`forem/doc/PROGRESS.md`、`forem/doc/SOURCES.md`，只有三份。
- 推荐：Codex GPT6.1sol / medium；Claude Sonnet5.5 / medium；跨论文方法/条件与Task4机制核对需要medium，检索/格式可low。
- 实际模型：GPT-6（系统仅披露该系列名，精确型号未知）；实际推理档位：未知。未切换模型，未执行任何其他Agent。
- 开工：已阅读根AGENTS、README、PROGRESS、SOURCES规则与Task4三文档；Task4父文档历史状态与PROGRESS实际实施记录不一致，本轮不修任务文档。目标理解：候选动作→动作条件预测→内部表征反馈→最终SAC连续动作；Husky+UR5、Gazebo、现有局部地图与当前底盘反馈。
- Git：main，已有大量tracked/staged/untracked改动；SOURCES.md开工时untracked。保留全部他人内容，不使用git add -A，不推送/合并。进程检查见现存Codex/Claude/ROS/Python进程，仅只读、不停止。

## 工作记录

- 11:04+08：开工登记；原文下载/文本提取仅使用现有工具，临时副本存工作区外，不安装依赖。阅读深度按实际记载；不能将下载全文等同已阅读全文。

- 2026-10-14T11:26:15+08:00：34篇原文与Genie 3官方博客阅读/数表核对，形成35条九字段笔记；未安装/运行论文代码。SOURCES追加前用rg核到最大SRC-0273，分配SRC-0274–0308；开工历史重复含0266，追加前重复仅0183–0190（各2次），本轮未修任何旧编号。

## 阅读口径与获取情况

本清单35项：34篇论文的原文PDF已获取，另1项为Genie 3官方博客。优先9篇的研究问题、机制、方法、实验与限制作细读；其中V-JEPA 2侧重行动规划，未逐段阅读全文中的视频理解/VQA章节。其余逐篇读摘要、方法与实验设置；4篇综述只选读分类、评测与补漏部分。全文指主文逐节读，不表示附录证明、所有引用和代码逐行审计；下文分别列实际深度与位置。

元数据记录实际所读arXiv版本；截至检索时优先下载版本列表最新PDF。发表场合与所读文本版本分开，不把后续正式版结果回填到旧版。DreamerV3按用户给出的原题读取v2，未以2025年Nature改题版本替换；WMPO找到ICLR 2026正式稿入口但PDF访问返回403，实际读arXiv 2511.09515v1；正式稿与该版差异未核验。Dream-MPC首次下载短暂失败后已取得v3。未有仅摘要代替方法原文的主清单条目；候选补读仅是综述二手线索。

数值是论文原报或明确注明的表内推导，不是FoReM复现。未报告/未从所读位置核出时写未知，不猜频率、机器人、硬件或耗时。FPS、动作频率、采样周期、仿真时间与墙钟分开；不将导航/游戏参数作为UR5合理取值证据。开源只表示核到作者链接或公开入口，未安装、运行、审核许可或承诺完整可复现。

每篇标题旁的来源条目覆盖其九字段中的原文事实；FoReM关系与汇总相关度是本轮条件映射的工程判断，全部为建议（待用户授权），并非任务协议或效果验证。

<a id="paper-dreamer4"></a>

## 01. ★ Dreamer 4 — [SRC-0274](../../SOURCES.md#src-0274)

1. **元数据与深度**：Training Agents Inside of Scalable World Models；作者：Hafner, Danijar；Yan, Wilson；Lillicrap, Timothy；机构：Google DeepMind；首稿/公开日期：2025/09/29；发表场合：arXiv预印本（所读版本）；实际所读：**arXiv 2509.24527v1**；[原文](https://arxiv.org/abs/2509.24527v1)；DOI：本轮未核到DOI。开源：本次作者项目页未找到官方实现；不将第三方复现算官方开源。[链接](https://danijar.com/project/dreamer4/)。阅读深度：**正文全文精读；附录A数据、B任务及表7/8选读**；核查位置：正文§1–6，pp.1–18；附录A、B；表1/2/3/7；图3/4/7。
2. **问题与思想**：研究能否仅用离线视频与动作，在复杂游戏中学习可交互动力学并在想象中提高策略。关键是规模、精细动作条件和足够快的逐帧生成。
3. **WM与RL结合 / 最终动作**：先视频模型预训练，再多任务BC/奖励头微调，最后在冻结Transformer的想象轨迹中用PMPO更新policy/value头；最终动作由任务条件policy头输出。在线不是CEM或SAC内部残差反馈。
4. **模型细节**：连续token潜空间；随机shortcut-forcing Transformer，确定性因果tokenizer。输入历史表示、键鼠动作、噪声级/步长；tokenizer用MSE+0.2 LPIPS，动力学用x-space flow/自蒸馏损失；每帧4次前向，MTP长度8；RL用λ-return与行为先验KL。
5. **实验条件**：Minecraft离线VPT 2541 h，360×640、20 FPS，23二值键+121类鼠标；2B参数（400M tokenizer+1.6B动力学），256–1024 TPU-v5p。训练集/验证集90/10按5分钟块隔离；1000个60分钟真实游戏评估回合。模型消融各48 h，不等于完整agent总训练时长；RL rollout数值未在所读正文找到。另有SOAR 180 h、7维末端相对动作、5 FPS的模型生成展示。
6. **主要结果与基线**：表7：钻石Dreamer4 0.7%，WM+BC、VLA(Gemma3)、BC与VPT均0%；铁镐29.0% vs WM+BC16.9%、VLA11.2%。表1：单H100生成21 FPS、交互任务14/16，Oasis large5/16；表2 FVD57 vs最初diffusion-forcing306。机器人图6仅生成展示，无机器人RL收益表。
7. **时延与执行偏差**：未涉及受控观测/传输/控制器/驱动时延。9.6 s是192帧历史窗口；21 FPS是模型计算吞吐，均不是执行器延迟。
8. **局限与失败模式**：作者：记忆短、背包物品不清/变化。核查：钻石成功率仍低；任务序列提示见表6；VPT额外270k h与Dreamer4数据量不等，不能称严格同数据比较；机器人视觉生成不能推出UR5控制有效。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：检查预测是否受动作控制、保持训练/验证时间块隔离及分别评价真实任务和预测。 只能借鉴思路、条件不同：借鉴冻结模型学习头、控制因果与生成效率；需大规模离线预训练，条件不同。 不适用或本轮不得采用：直接替换普通SAC为PMPO或把21 FPS当FoReM吞吐承诺。

<a id="paper-dreamer3"></a>

## 02. ★ DreamerV3 — [SRC-0275](../../SOURCES.md#src-0275)

1. **元数据与深度**：Mastering Diverse Domains through World Models；作者：Hafner, Danijar；Pasukonis, Jurgis；Ba, Jimmy；Lillicrap, Timothy；机构：Google DeepMind、University of Toronto；首稿/公开日期：2023/01/10；发表场合：arXiv所读v2；首稿2023、修订2024（未用后续Nature版替代正文）；实际所读：**arXiv 2301.04104v2**；[原文](https://arxiv.org/abs/2301.04104v2)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/danijar/dreamerv3)（论文项目入口；本轮未运行）。阅读深度：**正文全文精读；附录算法、表2/4/9/10选读**；核查位置：正文Learning algorithm、Results；表2/4/9/10；图3/6。
2. **问题与思想**：研究一套固定超参数能否覆盖不同任务、观测与奖励尺度。通过RSSM想象训练和归一化/损失平衡改善跨域稳定性。
3. **WM与RL结合 / 最终动作**：真实交互训练RSSM；actor/critic在潜态想象中训练。真实环境只从actor采样，无lookahead；最终由Dreamer actor输出，不是SAC。
4. **模型细节**：确定性循环h+32组类别随机z；输入图像/向量、上一动作；重建/奖励/continue NLL和分离stop-grad KL（1 nat free bits、1% unimix）；symlog、symexp twohot、5–95百分位return归一化。正文T=16与表4 H=15按计数约定分别记录；actor用REINFORCE，critic λ-return。
5. **实验条件**：8域>150任务；表2 Atari200M原始帧/重复4、Atari100k400k原始帧=100k决策、控制500k/1M；单A100每agent，控制模型12M，其他默认200M；Minecraft64环境、100M步、8.9 GPU-days。视觉/本体控制重复2；周期不能跨任务统一换秒。
6. **主要结果与基线**：表9/10 Atari100k gamer均值125%、中位49%，IRIS105%/29%、TWM96%/51%；其单A100约0.1 GPU-days vs IRIS3.5（原文换算）。图6模型规模/训练比例消融支持特定基准可扩展性，未提供Husky实验。
7. **时延与执行偏差**：未涉及显式时延；记忆/预测误差与通信/驱动延迟不能混称。
8. **局限与失败模式**：作者承认不同Atari100k协议影响比较，EfficientZero有提前reset；核查：固定超参数不等于固定算力/模型大小，表2环境数和replay比率跨域变化。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：区分模型损失与任务收益，检查表征/模型/策略训练的梯度边界。 只能借鉴思路、条件不同：借鉴损失尺度稳定化与历史表征；应先核查FoReM信号尺度。 不适用或本轮不得采用：照搬RSSM/奖励变换/replay比例或据此宣称所有任务无需调参。

<a id="paper-dreamer2"></a>

## 03. DreamerV2 — [SRC-0276](../../SOURCES.md#src-0276)

1. **元数据与深度**：Mastering Atari with Discrete World Models；作者：Hafner, Danijar；Lillicrap, Timothy；Norouzi, Mohammad；Ba, Jimmy；机构：Google Research、University of Toronto；首稿/公开日期：2020/10/05；发表场合：ICLR 2021；所读arXiv v4修订2022；实际所读：**arXiv 2010.02193v4**；[原文](https://arxiv.org/abs/2010.02193v4)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/danijar/dreamerv2)。阅读深度：**部分：摘要、§2方法、§3实验、表1/2、讨论**；核查位置：§2.1/2.2、§3；表1；附录超参。
2. **问题与思想**：作者研究离散随机潜变量能否改善Atari想象学习，相比连续潜变量验证表征与KL平衡的作用。
3. **WM与RL结合 / 最终动作**：真实数据训练模型，冻结模型权重时在想象中训练actor/critic；最终actor出动作，无在线搜索。
4. **模型细节**：RSSM确定性循环+32×32类别变量；图像/动作输入；图像、奖励、discount NLL+KL balancing（0.8）；straight-through采样。想象H=15（附录），价值λ-return和actor梯度估计。
5. **实验条件**：55个Atari、200M原始帧（重复4后50M输入）；单V100、单环境、<10天；另模拟humanoid连续控制；非机器人真机。
6. **主要结果与基线**：表1 human-normalized median2.15、mean11.33，Rainbow1.47/9.12，IQN1.29/8.85；不是统一机器人成功率。
7. **时延与执行偏差**：未涉及显式时延。
8. **局限与失败模式**：游戏事件分布与控制误差不同；离散潜态与固定像素重建代价不能直接预期在局部地图中占优。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：权重冻结与输入梯度分开核查。 只能借鉴思路、条件不同：离散/随机表征与KL稳定化。 不适用或本轮不得采用：直接把Atari成绩和200M帧预算变成UR5依据。

<a id="paper-dreamer1"></a>

## 04. DreamerV1 — [SRC-0277](../../SOURCES.md#src-0277)

1. **元数据与深度**：Dream to Control: Learning Behaviors by Latent Imagination；作者：Hafner, Danijar；Lillicrap, Timothy；Ba, Jimmy；Norouzi, Mohammad；机构：Google Research、DeepMind、University of Toronto（正文署名）；首稿/公开日期：2019/12/03；发表场合：ICLR 2020；首稿2019；实际所读：**arXiv 1912.01603v3**；[原文](https://arxiv.org/abs/1912.01603v3)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/danijar/dreamer)。阅读深度：**部分：摘要、§2–4方法、§6实验、结论及附录A**；核查位置：§2–4/6；图6；附录A。
2. **问题与思想**：短模型horizon如何支持长时序行为：用预测奖励及bootstrap value的解析梯度训练策略。
3. **WM与RL结合 / 最终动作**：在潜态想象中通过可微模型优化action/value网络；部署action网络，非在线CEM。
4. **模型细节**：高斯随机潜态+确定性循环RSSM；图像64×64和动作；ELBO重建+奖励+KL，比较contrastive/仅reward；continuous actor经tanh、λ-return反传；附录H=15。
5. **实验条件**：20个DMC像素控制任务，1–12维动作、重复2、回合1000步；5 seeds；单V100+10CPU核，约3h/1M原始环境步。
6. **主要结果与基线**：图6：5M步平均return823，PlaNet332；D4PG100M步786。交互预算不同，不能写成同预算全面优势。
7. **时延与执行偏差**：未涉及显式时延。
8. **局限与失败模式**：仅reward表征在该研究中不足；不同模型学习方式任务成绩明显不同；主比较为小型控制仿真。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：bootstrap让模型预测horizon和任务horizon分开。 只能借鉴思路、条件不同：可微预测辅助训练、表征损失的任务关联性。 不适用或本轮不得采用：据此改变SAC更新为Dreamer或直接回传模型奖励。

<a id="paper-planet"></a>

## 05. PlaNet — [SRC-0278](../../SOURCES.md#src-0278)

1. **元数据与深度**：Learning Latent Dynamics for Planning from Pixels；作者：Hafner, Danijar；Lillicrap, Timothy；Fischer, Ian；Villegas, Ruben；Ha, David；Lee, Honglak；Davidson, James；机构：Google AI/DeepMind等，见署名；首稿/公开日期：2018/11/12；发表场合：ICML 2019；首稿2018；实际所读：**arXiv 1811.04551v5**；[原文](https://arxiv.org/abs/1811.04551v5)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/danijar/planet)。阅读深度：**部分：摘要、§2–5方法/实验、表1与附录A**；核查位置：§2/3/4/5；算法2；表1；附录A/D。
2. **问题与思想**：从像素学习足够准确的潜态动力学，在未知环境中在线计划。
3. **WM与RL结合 / 最终动作**：CEM优化有限动作序列的预测reward；只执行首动作再重规划；最终由CEM输出，没有学习actor。
4. **模型细节**：确定性GRU+高斯随机RSSM；图像/动作；ELBO，讨论latent overshooting多步KL；明确最终RSSM不必用overshooting。附录默认CEM horizon12、10迭代、1000候选、100精英（附录A；各任务action repeat不同）。
5. **实验条件**：六个DMC像素任务64×64；任务分别设置action repeat，单V100约10–20h；在线收集，1000回合比较D4PG100000回合。
6. **主要结果与基线**：表1 cheetah PlaNet662 vs D4PG524；walker951 vs968；因此不能写成所有任务胜出。
7. **时延与执行偏差**：未涉及显式时延。
8. **局限与失败模式**：模型偏差、在线搜索开销；overshooting并非最终系统必需；基线数据量/输入权限不同。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：明确当前观测与未来预测的因果边界。 只能借鉴思路、条件不同：receding horizon和多步预测误差检查。 不适用或本轮不得采用：把CEM输出动作称为最终SAC动作，或把DMC动作重复作为FoReM周期。

<a id="paper-muzero"></a>

## 06. MuZero — [SRC-0279](../../SOURCES.md#src-0279)

1. **元数据与深度**：Mastering Atari, Go, Chess and Shogi by Planning with a Learned Model；作者：Schrittwieser, Julian；Antonoglou, Ioannis；Hubert, Thomas；Simonyan, Karen；Sifre, Laurent；Schmitt, Simon；Guez, Arthur；Lockhart, Edward；等（完整署名见原文）；机构：DeepMind；首稿/公开日期：2019/11/19；发表场合：Nature 2020；所读arXiv v2；DOI 10.1038/s41586-020-03051-4；实际所读：**arXiv 1911.08265v2**；[原文](https://arxiv.org/abs/1911.08265v2)；DOI：10.1038/s41586-020-03051-4。开源：本次未核到完整官方论文复现代码；[链接](https://github.com/google-deepmind/muzero) 仅作官方伪代码入口，未核完整训练实现。阅读深度：**部分：摘要、§3方法/§4结果、Methods训练设置**；核查位置：§3/4；式1；表1；Methods。
2. **问题与思想**：无已知规则时能否用仅预测决策相关量的模型树搜索。
3. **WM与RL结合 / 最终动作**：确定性潜态模型预测policy/reward/value，MCTS形成改进策略；真实动作从搜索visit分布选取，非policy头直接最终输出。
4. **模型细节**：表示h、动力学g、预测f；无像素重建；训练展开K=5，reward/value损失+MCTS policy交叉熵+L2；随机环境由确定性模型近似。
5. **实验条件**：棋类800 simulations/决策，Atari50 simulations且动作重复4；1M训练batch（棋2048、Atari1024）；棋/游戏，不涉及机器人。Atari每game 8 TPU-v3训练+32 TPU-v3 selfplay，棋类16训练+1000 selfplay；12h是Atari主表特定分布式配置，不能当单卡时间。
6. **主要结果与基线**：表1：MuZero20B帧mean4999.2%/median2041.1%；Reanalyze200M帧2168.9%/731.1%，LASER200M帧median431%。两个MuZero预算不能混合。
7. **时延与执行偏差**：未涉及观测或驱动时延；thinking time是搜索耗时。
8. **局限与失败模式**：不直接处理Poker式不完备信息；确定性latent非物理状态；离散树搜索及巨大并行预算不同于Husky。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：控制相关预测与像素重建可分开讨论。 只能借鉴思路、条件不同：候选预测价值但要独立验证模型误差。 不适用或本轮不得采用：套MCTS/离散化SAC动作作为本轮实施或拿游戏成绩证明机器人收益。

<a id="paper-genie"></a>

## 07. Genie — [SRC-0280](../../SOURCES.md#src-0280)

1. **元数据与深度**：Genie: Generative Interactive Environments；作者：Bruce, Jake；Dennis, Michael；Edwards, Ashley；Parker-Holder, Jack；Shi, Yuge；Hughes, Edward；Lai, Matthew；Mavalankar, Aditi；等（完整署名见原文）；机构：Google DeepMind；首稿/公开日期：2024/02/23；发表场合：ICML 2024（所读arXiv v1）；实际所读：**arXiv 2402.15391v1**；[原文](https://arxiv.org/abs/2402.15391v1)；DOI：本轮未核到DOI。开源：作者项目页本次未找到官方训练代码：[链接](https://sites.google.com/view/genie-2024/)。阅读深度：**部分：摘要、§2方法、§3实验/数据与§5讨论**；核查位置：§2/3；表2/3；图15；附录B/C。
2. **问题与思想**：无动作标签的视频能否学习可控交互世界；以潜动作模型从相邻帧推断低维动作。
3. **WM与RL结合 / 最终动作**：主要是生成环境；§3.3给latent-action行为克隆转移，而非证明在其模型中RL成功；用户或已训练policy选择潜动作。
4. **模型细节**：VQ tokenizer、VQ潜动作、ST Transformer MaskGIT；token CE和VQ重建/commitment；随机token采样、逐帧自回归。潜动作索引不是机器人实际命令。
5. **实验条件**：6.8M×16s platformer视频约30k h，10 FPS、160×90，11B模型；另机器人视频验证，未给UR5控制实验。
6. **主要结果与基线**：表2 Platformers pixel-input FVD40.1/动作可控ΔPSNR1.91，token-input38.8/1.33：更低FVD不等于更可控；图15约200真实专家样本映射latent后达oracle BC相近（图示，未读出精确百分比）。
7. **时延与执行偏差**：未涉及显式时延。
8. **局限与失败模式**：图像生成与可执行动作不等价；latent映射需真实动作标定；不是SAC反馈实证。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：动作条件依赖与视觉指标分开核查。 只能借鉴思路、条件不同：少标签视频/潜动作思路。 不适用或本轮不得采用：用无标定latent直接接UR5或把BC转移叫RL收益。

<a id="paper-genie3"></a>

## 08. Genie 3（官方博客） — [SRC-0281](../../SOURCES.md#src-0281)

1. **元数据与深度**：Genie 3: A New Frontier for World Models；作者：Jack Parker-Holder、Shlomi Fruchter（官方署名）；机构：Google DeepMind；Jack Parker-Holder、Shlomi Fruchter；首稿/公开日期：2025-08-05；发表场合：官方博客，2025-08-05；无论文版本号；实际所读：**官方博客2025-08-05；无arXiv版本号**；[原文](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/)；DOI：无。开源：未公开实现/权重于所读博客；[链接](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/)。阅读深度：**原始博客全文；技术未披露项明确未知**；核查位置：Towards world simulation、Capabilities、Fueling embodied agent research；无论文表图编号。
2. **问题与思想**：生成可实时导航的长时一致世界，供交互与未来agent研究。
3. **WM与RL结合 / 最终动作**：演示SIMA在生成环境中导航；博客未交付完整RL训练、对照和优化目标；最终导航动作由SIMA/用户给出。
4. **模型细节**：博客未披露潜/像素建模内部架构、随机性、具体训练损失或动作条件细节；只知道视频输出及navigation/text world-event输入，不能借其他Genie版本补齐。
5. **实验条件**：24 FPS、720p、持续数分钟的公开演示；数据量、训练硬件/时长、机器人型号与控制频率未披露。
6. **主要结果与基线**：上述为官方功能描述，无统计对照表、标准化任务SR或UR5实验，不列成研究验收通过。
7. **时延与执行偏差**：未涉及受控观测/传输/控制器/物理时延；24 FPS是生成显示速率，不是通信或执行偏差的测量。
8. **局限与失败模式**：技术/评测不可审计；demo长时一致性不等于可靠物理接触；研究预览不是开源训练基础设施。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：暂无可直接迁移的具体方法。 只能借鉴思路、条件不同：交互世界应响应真实动作、可测试反事实。 不适用或本轮不得采用：将演示性能/分辨率作为FoReM控制证据。

<a id="paper-unisim"></a>

## 09. UniSim — [SRC-0282](../../SOURCES.md#src-0282)

1. **元数据与深度**：Learning Interactive Real-World Simulators；作者：Yang, Sherry；Du, Yilun；Ghasemipour, Kamyar；Tompson, Jonathan；Kaelbling, Leslie；Schuurmans, Dale；Abbeel, Pieter；机构：Google DeepMind、MIT、UC Berkeley（作者联合署名）；首稿/公开日期：2023/10/09；发表场合：ICLR 2024；所读arXiv v3；实际所读：**arXiv 2310.06114v3**；[原文](https://arxiv.org/abs/2310.06114v3)；DOI：本轮未核到DOI。开源：作者项目页本次未找到官方完整训练代码：[链接](https://universal-simulator.github.io/)。阅读深度：**部分：摘要、§2方法、§4政策训练/评估、§6局限**；核查位置：§2.1/2.2/4.1/4.2/6；表2/3；附录C/D。
2. **问题与思想**：异构视频与动作怎样统一成可交互模拟器，用模拟经验训练策略。
3. **WM与RL结合 / 最终动作**：hindsight数据增强训练VLM；另一分支VLA在生成视频内用REINFORCE+学得reward优化，部署VLA动作，部分高层视频通过逆动力学执行。
4. **模型细节**：视频空间条件扩散U-Net，内部非Dreamer RSSM；历史帧+T5语言/离散连续控制混合编码，去噪MSE；预测变长视频段、接着自回归。
5. **实验条件**：5.6B，512 TPU-v3、20天模型训练；Language Table二维末端控制、真实机器人部署图；VLM生成10k长轨迹；RL定量表3评估48个模型内任务，不等于48真机回合。统一动作Hz未报告。
6. **主要结果与基线**：表3模拟SR .81 vs VLA-BC .58，pointing .71 vs .12；表2模型内RDG(all) .34±.13 vs .07±.11；真机图8给定性迁移，不能把这些SR称真机SR。
7. **时延与执行偏差**：未涉及显式时延。
8. **局限与失败模式**：作者：不可能动作幻觉、短记忆、未知形态泛化有限；模型内奖励/评测自身偏差可能放大，真实定量证据有限。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：区分模型内与真实环境成绩。 只能借鉴思路、条件不同：失败数据覆盖、学得模型和真实部署接口对齐。 不适用或本轮不得采用：将VLA/逆动力学作为最终SAC或迁移其数据/奖励合同。

<a id="paper-gamengen"></a>

## 10. GameNGen — [SRC-0283](../../SOURCES.md#src-0283)

1. **元数据与深度**：Diffusion Models Are Real-Time Game Engines；作者：Valevski, Dani；Leviathan, Yaniv；Arar, Moab；Fruchter, Shlomi；机构：Google Research、Tel Aviv University（原文署名）；首稿/公开日期：2024/08/27；发表场合：ICLR 2025；首稿2024、所读v2修订2025；实际所读：**arXiv 2408.14837v2**；[原文](https://arxiv.org/abs/2408.14837v2)；DOI：本轮未核到DOI。开源：项目页未找到官方训练代码：[链接](https://gamengen.github.io/)。阅读深度：**部分：摘要、§3方法、§4实验设置、§5结果/局限**；核查位置：§3.1–3.3/4/5；表1/2/3；图4。
2. **问题与思想**：神经网络能否高质量实时模拟DOOM；关键是模型自回归上下文噪声增强与decoder细节修复。
3. **WM与RL结合 / 最终动作**：PPO先在真实游戏采数据，之后训练神经游戏引擎；不是在世界模型中优化PPO。最终动作来自玩家/外部agent。
4. **模型细节**：Stable Diffusion1.4 VAE潜态扩散，动作embedding+历史帧潜态；velocity去噪MSE，context噪声增强，decoder像素MSE；预测下一帧。
5. **实验条件**：DOOM；§4.1 PPO收集50M环境步、8个并行游戏；§4.2模型用70M样本子集、700k训练updates、128 TPU-v5e、320×240图像pad至320×256；默认64帧/动作历史。§3.3单TPU-v5推理20 FPS（4次denoise共40ms+decoder10ms）；游戏键动作，非机器人控制频率。完整训练wall-time未报告。
6. **主要结果与基线**：§5 teacher-forced PSNR29.43/LPIPS .249；人类短片鉴别58–60%。表2更多context提升预测；这些是引擎质量指标，没有模型内RL任务收益对照。
7. **时延与执行偏差**：计算20FPS涉及推理耗时；未涉及观测/执行时延注入。
8. **局限与失败模式**：有限context导致长期状态不一致，数据受policy覆盖限制；视觉相似不保证内部计分/物理正确。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：区分模型采数和策略用模型训练。 只能借鉴思路、条件不同：context鲁棒性与生成细节。 不适用或本轮不得采用：把游戏引擎吞吐、视觉PSNR证明SAC收益。

<a id="paper-vjepa2"></a>

## 11. ★ V-JEPA 2 — [SRC-0284](../../SOURCES.md#src-0284)

1. **元数据与深度**：V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning；作者：Assran, Mido；Bardes, Adrien；Fan, David；Garrido, Quentin；Howes, Russell；Mojtaba；Komeili；Muckley, Matthew；等（完整署名见原文）；机构：FAIR at Meta、Mila/Polytechnique Montréal；首稿/公开日期：2025/06/11；发表场合：arXiv预印本，2025（所读v1）；实际所读：**arXiv 2506.09985v1**；[原文](https://arxiv.org/abs/2506.09985v1)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/facebookresearch/vjepa2)。阅读深度：**部分精读：§1–4完整控制方法/结果，§2预训练；附录B.1/B.4；§5–7理解/QA未逐项精读**；核查位置：§2.1/3.1/3.2/4.1–4.3；表2/3；附录B.1/B.4。
2. **问题与思想**：互联网自监督表征能否用少量机器人数据获得动作后果模型，再在新环境规划。须区分无动作预训练V-JEPA2和后训有动作V-JEPA2-AC。
3. **WM与RL结合 / 最终动作**：AC在冻结encoder上学动力学；执行时CEM最小化未来与image goal的latent L1，执行首动作再重规划。该机器人分支不训练RL actor；最终由CEM输出。
4. **模型细节**：确定性latent预测Transformer（AC≈300M、24层；encoder≈1B）；帧表示+末端位姿+动作；预训mask特征L1+EMA/stop-grad，AC teacher-forcing L1+2步rollout L1。动作标签由相邻实测末端状态差构造，不是原始控制命令。
5. **实验条件**：>1M h互联网视频与1M图像；AC筛选DROID约23k轨迹、<62h，256²、4FPS、7维末端/夹爪；两实验室Franka+RobotiQ，未收集部署场地训练数据，但手选camera视角。CEM horizon1、800样本×10轮，单4090约16s/动作；阻塞式等待执行完成，没有固定servo Hz。
6. **主要结果与基线**：表2跨lab PnP杯80%/盒65%，Octo15%/10%；每task10trials。表3 Lab2 Cosmos80样本×10轮约4min/动作，PnP杯0%/盒0%，AC80%/50%。4FPS数据与16s规划必须分开。
7. **时延与执行偏差**：未研究受控时延；16s是计算延迟，阻塞执行机制，不是UR5驱动时延。
8. **局限与失败模式**：作者：相机坐标轴歧义、长rollout误差、搜索空间和image-subgoal依赖；核查：10trial样本小，目标子图与外部选择不能称完全自主长时任务；动作标签实际差分可能混合控制响应。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：固定目标encoder、监督空间一致、动作标签来源分开核查。 只能借鉴思路、条件不同：不必重建像素的动作条件预测；teacher-forcing与rollout验证分开。 不适用或本轮不得采用：把CEM替换SAC/手选视角或4FPS沿用为UR5周期。

<a id="paper-nwm"></a>

## 12. Navigation World Models — [SRC-0285](../../SOURCES.md#src-0285)

1. **元数据与深度**：Navigation World Models；作者：Bar, Amir；Zhou, Gaoyue；Tran, Danny；Darrell, Trevor；LeCun, Yann；机构：Meta、UC Berkeley等（作者署名）；首稿/公开日期：2024/12/04；发表场合：CVPR 2025；首稿2024、所读v2；实际所读：**arXiv 2412.03572v2**；[原文](https://arxiv.org/abs/2412.03572v2)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/facebookresearch/nwm/)。阅读深度：**部分：摘要、§3方法、§4实验/结果与附录8运行成本**；核查位置：§3.1–3.3/4；表2/3；附录表8。
2. **问题与思想**：用可控视频模型模拟导航动作后果，既能规划，也能对外部策略候选排序。
3. **WM与RL结合 / 最终动作**：CDiT预测每个候选未来；CEM规划或NoMaD多候选rerank，最终由CEM/最低能量候选输出；不更新SAC。
4. **模型细节**：VAE latent随机扩散；历史帧、平面平移u、yaw、time shift（±16s）；clean-state MSE+variance VLB；多goal/time条件避免动作被时间变量替代。
5. **实验条件**：SCAND/TartanDrive/RECON/HuRoN、Ego4D视频，模型最高1B；评估主要离线轨迹2s/视频16s，导航相对动作非UR5控制；实验含1/4FPS设置。
6. **主要结果与基线**：表2 RECON ATE：NoMaD1.93±.04，NWM+NoMaD32候选1.78±.03，NWM planning1.13±.02；RPE .52/.48/.35。附录表8完整trajectory30.3s，time-skip14.7s、distill .4s，4bit .1s仅估计，不能当已测。
7. **时延与执行偏差**：未涉及受控时延；time shift是预测时间跨度，不是传输/执行延迟。
8. **局限与失败模式**：轨迹相似/ATE不等于真实碰撞成功；动作常从实际pose差近似，镜头/场景OOD；distill计算和估计成本不能直接保证FoReM实时。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：明确候选来源及执行者。 只能借鉴思路、条件不同：动作后果排序最贴近候选预测思想；需另审最终SAC概率合同。 不适用或本轮不得采用：搬导航单位/时延或把rerank称SAC反馈等价。

<a id="paper-cosmos"></a>

## 13. Cosmos — [SRC-0286](../../SOURCES.md#src-0286)

1. **元数据与深度**：Cosmos World Foundation Model Platform for Physical AI；作者：NVIDIA；:；Agarwal, Niket；Ali, Arslan；Bala, Maciej；Balaji, Yogesh；Barker, Erik；Cai, Tiffany；等（完整署名见原文）；机构：NVIDIA团队（全体贡献者见附录A）；首稿/公开日期：2025/01/07；发表场合：技术报告2025；所读arXiv v3；实际所读：**arXiv 2501.03575v3**；[原文](https://arxiv.org/abs/2501.03575v3)；DOI：本轮未核到DOI。开源：官方公开代码/权重有各自许可：[链接](https://github.com/nvidia-cosmos/cosmos-predict1)；本轮未审核许可兼容性。阅读深度：**部分：摘要、§5.1/5.2模型、§5.3实验、§6.2机器人后训与讨论**；核查位置：§3/5/6.2；表10/19；Discussion。
2. **问题与思想**：建立视频数据处理、tokenizer和可后训世界基础模型平台。
3. **WM与RL结合 / 最终动作**：主要提供模拟/数据基础设施；此报告机器人后训做动作条件生成，未给同任务SAC训练比较；外部策略/控制输入动作。
4. **模型细节**：连续latent扩散（EDM加权denoise MSE）和离散token自回归（next-token CE）两族；文本/视频prompt，后训增加相机/末端动作条件；生成horizon跨各模型不统一。
5. **实验条件**：20M h原始视频筛约100M 2–60s clips；报告整体10k H100集群、3个月覆盖所有WFMs（非单模型成本）。机器人Bridge约20k episodes、5FPS、7维末端动作；1X EVE≈200h/30FPS。
6. **主要结果与基线**：表19 7B Text2World pose-estimation成功62.6% vs VideoLDM4.4%，PSNR33.02 vs26.23；这是生成多视角一致性，不是机器人任务成功。
7. **时延与执行偏差**：未研究显式时延；视频fps不是机器人controller周期。
8. **局限与失败模式**：作者承认不遵守物理规律的生成仍存在；大规模/视频重建成本、动作后训与真实可控性须另验。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：不把视觉一致性指标叫任务SR。 只能借鉴思路、条件不同：基础模型后训动作grounding、数据整理性能思路。 不适用或本轮不得采用：安装大模型/更换任务观测/拿集群成本作FoReM期限承诺。

<a id="paper-tdmpc2"></a>

## 14. ★ TD-MPC2 — [SRC-0287](../../SOURCES.md#src-0287)

1. **元数据与深度**：TD-MPC2: Scalable, Robust World Models for Continuous Control；作者：Hansen, Nicklas；Su, Hao；Wang, Xiaolong；机构：UC San Diego；首稿/公开日期：2023/10/25；发表场合：ICLR 2024；实际所读：**arXiv 2310.16828v2**；[原文](https://arxiv.org/abs/2310.16828v2)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/nicklashansen/tdmpc2)。阅读深度：**精读正文方法/实验/讨论；附录H架构与表8，相关工作选读**；核查位置：§3.1–3.3/4/5；表1/8；图7/8/9/10。
2. **问题与思想**：让任务导向模型在多任务连续控制中稳定扩展，避免仅靠增加规模反而退化。
3. **WM与RL结合 / 最终动作**：联合学encoder/dynamics/reward/Q与max-entropy policy prior；执行时MPPI搜索，policy只提供部分候选，最终输出规划分布首动作。它不是保留SAC actor最终输出的结构。
4. **模型细节**：确定性decoder-free latent MLP；LayerNorm+Mish、SimNorm，输入状态/像素、动作、任务embedding；latent stop-grad一致性MSE+reward/value log-space CE，5个Q随机取2最小；policy entropy/归一化价值目标。默认horizon3、6轮、512候选、24policy候选、64精英（表8）。
5. **实验条件**：104在线任务DMC/Meta-World/ManiSkill2/MyoSuite；3seed，主要5M参数，batch256、UTD1。多任务80任务545M transitions由240单任务agent回放产生；317M模型单3090约33 GPU-days；39维动作上限，非UR5Gazebo。10像素DMC任务另验；各域控制周期未统一给出。
6. **主要结果与基线**：表1多任务：1M模型score16.0/3.7GPU-days，5M49.5/4.2，317M70.6/33；图8 20k步新任务fine-tune47.0 vs从头24.0。图10视觉控制与DrQ-v2/DreamerV3相当，不能称全领域胜出。
7. **时延与执行偏差**：未涉及受控时延；MPPI额外计算不是驱动滞后。
8. **局限与失败模式**：作者：离散动作扩展尚开放、奖励错设/物理安全和多任务数据规模；核查：数据采集成本不含在表1纯预训时长中，基线UTD/参数不同，同交互不是同计算。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：把policy候选和最终执行动作区别记录，latent一致性目标要有稳定语义。 只能借鉴思路、条件不同：任务相关decoder-free预测、规范化、Q/模型偏差检查。 不适用或本轮不得采用：自动把SAC改为MPPI、复制表8超参或用多任务吞吐承诺72h。

<a id="paper-tdmpc"></a>

## 15. ★ TD-MPC — [SRC-0288](../../SOURCES.md#src-0288)

1. **元数据与深度**：Temporal Difference Learning for Model Predictive Control；作者：Hansen, Nicklas；Wang, Xiaolong；Su, Hao；机构：UC San Diego；首稿/公开日期：2022/03/09；发表场合：ICML 2022；实际所读：**arXiv 2203.04955v2**；[原文](https://arxiv.org/abs/2203.04955v2)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/nicklashansen/tdmpc)。阅读深度：**精读方法§3/4、实验§5、结论；附录超参和运行成本选读，相关工作浏览**；核查位置：§3/4/5；式7–11；表1/2；附录F/H。
2. **问题与思想**：有限模型预测horizon怎样覆盖长期return：TOLD latent与terminal Q联合TD学习。
3. **WM与RL结合 / 最终动作**：policy-guided MPPI优化短序列+末端value bootstrap；学习policy用于proposal/TD目标，最终是规划动作，非policy直接执行。
4. **模型细节**：确定性MLP h/d/R/Q/p，无RNN随机模型或decoder；reward MSE+TD Q MSE+EMA encoder latent一致性，多步反传；policy最大化Q；默认H5、512候选、6迭代（Dog8/Humanoid12）。
5. **实验条件**：92控制任务、DMC状态/像素、Meta-World；图像3×84²帧堆叠，state主评5seed，像素100k表10run；单RTX3090 wall-time；任务各自action repeat，未统一servo Hz。
6. **主要结果与基线**：表1 100k像素Finger Spin943±59 vs DrQ901±104，但Cheetah222±88 vs DrQ344±67；表2 Walker达到940分：.47h vs LOOP7.72h、SAC .41h；500k步TD-MPC5.60h vs SAC1.41h。并非比SAC所有wall-time更快。
7. **时延与执行偏差**：未注入显式时延；附录约20ms推理是该GPU模型规划成本，不能当UR5控制/传输延迟。
8. **局限与失败模式**：作者：Finger Turn Hard探索不足、模型/规划精度与算力权衡；核查：state任务优势不等于视觉任务全面优于所有方法。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：预测步长、任务horizon、值函数与真实步耗时分别记。 只能借鉴思路、条件不同：多步latent一致性与task-oriented模型。 不适用或本轮不得采用：据20ms固定FoReM动作周期或将MPPI叫SAC输出。

<a id="paper-mbpo"></a>

## 16. ★ MBPO — [SRC-0289](../../SOURCES.md#src-0289)

1. **元数据与深度**：When to Trust Your Model: Model-Based Policy Optimization；作者：Janner, Michael；Fu, Justin；Zhang, Marvin；Levine, Sergey；机构：UC Berkeley；首稿/公开日期：2019/06/19；发表场合：NeurIPS 2019；所读arXiv v3修订2021；实际所读：**arXiv 1906.08253v3**；[原文](https://arxiv.org/abs/1906.08253v3)；DOI：本轮未核到DOI。开源：公开作者代码：[链接](https://github.com/jannerm/mbpo)。阅读深度：**正文全文精读；附录C超参表，证明按假设/定理核查而非逐行复证**；核查位置：§4.1–4.3/5/6/7；算法2；图2/3/4；附录C表1。
2. **问题与思想**：何时信任模型样本：权衡新策略分布、模型误差和rollout长度，避免长想象误差累计。
3. **WM与RL结合 / 最终动作**：从真实replay状态branched短rollout生成训练样本，给SAC额外更新；部署仍由SAC actor输出，没有候选未来反馈修正。
4. **模型细节**：原观测/状态空间概率ensemble（7个MLP），预测next与reward的对角高斯，NLL；随机选择ensemble成员表示不确定性；非潜空间/非像素decoder。模型horizon按任务1→15/25或固定1；SAC Q与actor照常训练。
5. **实验条件**：六个MuJoCo控制任务、标准1000步回合、5trial；20–40 SAC更新/真实步，400模型rollouts/真实步（附录C）；原文所读段未提供统一GPU/总训练时长/控制Hz，不能据sim-time分钟推wall-time。
6. **主要结果与基线**：图2 Ant300k真实步达到SAC3M步的相近回报（曲线口径，无精确数字硬读）；图3 Hopper固定1步rollout已强，500步失效，200步不如短rollout。图4 model/real return相关为Hopper诊断。
7. **时延与执行偏差**：未涉及显式时延或执行器动态。
8. **局限与失败模式**：严格误差界过于悲观，经验model generalization用于动机，不是实用算法对任意机器人必单调提升；部署策略变更会带来模型distribution shift；同交互下更新数/模型计算不同。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：普通SAC最终actor与模型用途区别；计入模型训练/生成/额外更新成本。 只能借鉴思路、条件不同：短预测降低误差累计与新policy分布下检查模型。 不适用或本轮不得采用：未经授权往replay加合成数据/改UTD；把理论界当Task4收益保证。

<a id="paper-dreammpc"></a>

## 17. Dream-MPC — [SRC-0290](../../SOURCES.md#src-0290)

1. **元数据与深度**：Dream-MPC: Gradient-Based Model Predictive Control with Latent Imagination；作者：Spieler, Jonathan；Behnke, Sven；机构：University of Bonn；首稿/公开日期：2026/05/06；发表场合：ICML 2026（作者官方代码标注）；所读arXiv v3；实际所读：**arXiv 2605.04568v3**；[原文](https://arxiv.org/abs/2605.04568v3)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/jspieler/dream-mpc)。阅读深度：**部分：摘要、§4完整规划方法、§5设置/结果/消融**；核查位置：§4/5.1–5.5；表1/2/3/4；算法1。
2. **问题与思想**：将少量policy候选的可微模型梯度规划做得稳定、经济，降低population搜索开销。
3. **WM与RL结合 / 最终动作**：policy rollout产生候选；加不确定性正则、跨步复用，梯度上升优化序列；最终选择预测return最高序列首动作。优化后的动作通常不是原policy采样。
4. **模型细节**：TD-MPC2/BMPC确定性latent+reward/Q；Dreamer分支RSSM；继承原模型loss，推理优化return-uncertainty，不是重新定义SAC loss；默认示例5候选×1迭代×H3，前向次数比较不能当含backward wall-time。
5. **实验条件**：24状态连续控制（DMC、HumanoidBench、Meta-World），另6视觉DMC；3seed×10eval；部分试验仅替换预训planner，另有从头训练。动作Hz、完整wall-time本次未查到；代码未运行。
6. **主要结果与基线**：表1 DMC TD-MPC2规划657±225、policy-only367±247、Dream-MPC433±259：并未击败原MPPI。§5.1 BMPC基础上IQM+26.7%、mean+20.5%；表3 Dreamer Cheetah751±111→836±49，Walker575±33→632±52。
7. **时延与执行偏差**：未研究显式时延；推理优化耗时要另测。
8. **局限与失败模式**：作者：依赖好policy初值，局部极值与value精度；核查：5×1×3与512×6×3前向数比较忽略梯度反传/批量并行，不能说wall-time快同样倍数。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：区分候选动作与优化后执行动作。 只能借鉴思路、条件不同：模型不确定性、跨时刻warm-start，仅作为设计思路。 不适用或本轮不得采用：将梯度MPC追加成当前SAC执行链或认为保留policy prior就仍是SAC最终动作。

<a id="paper-iris"></a>

## 18. IRIS — [SRC-0291](../../SOURCES.md#src-0291)

1. **元数据与深度**：Transformers are Sample-Efficient World Models；作者：Micheli, Vincent；Alonso, Eloi；Fleuret, François；机构：University of Geneva等（作者署名）；首稿/公开日期：2022/09/01；发表场合：ICLR 2023；实际所读：**arXiv 2209.00588v2**；[原文](https://arxiv.org/abs/2209.00588v2)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/eloialonso/iris)。阅读深度：**部分：摘要、§2方法、§3实验、表1与附录训练成本**；核查位置：§2.1–2.3/3；表1；附录Horizon/compute。
2. **问题与思想**：少量交互下学习长时可信的token Transformer模型，再让agent在想象中学行为。
3. **WM与RL结合 / 最终动作**：VQ表示+GPT世界模型；actor/critic在解码出的想象像素上学习；部署actor。token dynamics不等于actor直接使用latent。
4. **模型细节**：16个离散image tokens+actions；transition/termination CE、reward MSE或CE；VQ L1/感知/commitment；policy/value CNN-LSTM与REINFORCE/λ-return，H20。
5. **实验条件**：Atari26任务、100k actions、5seed、每game最终100eval；8A10040GB、同GPU两个任务约7d，即3.5GPU-days/game（不是2h训练）。
6. **主要结果与基线**：表1 meanHNS1.046/IQM.501，SPR .616/.337；10/26超人；EfficientZero mean1.943，不能称所有算法SOTA。
7. **时延与执行偏差**：未涉及时延。
8. **局限与失败模式**：Frostbite新关卡事件罕见使模型/agent受分布限制；median优势不显著；自回归token成本大。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：记录actor实际输入而非仅模型latent。 只能借鉴思路、条件不同：多步事件覆盖、模型数据不足影响策略。 不适用或本轮不得采用：换tokenizer/游戏预算或按2h gameplay承诺墙钟。

<a id="paper-diamond"></a>

## 19. DIAMOND — [SRC-0292](../../SOURCES.md#src-0292)

1. **元数据与深度**：Diffusion for World Modeling: Visual Details Matter in Atari；作者：Alonso, Eloi；Jelley, Adam；Micheli, Vincent；Kanervisto, Anssi；Storkey, Amos；Pearce, Tim；Fleuret, François；机构：University of Geneva等（作者署名）；首稿/公开日期：2024/05/20；发表场合：NeurIPS 2024；所读arXiv v2；实际所读：**arXiv 2405.12399v2**；[原文](https://arxiv.org/abs/2405.12399v2)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/eloialonso/diamond)。阅读深度：**部分：摘要、§3方法、§4实验、§5细节分析与表1**；核查位置：§3.1/3.2/4/5；表1；附录D/E。
2. **问题与思想**：离散压缩会丢失任务关键视觉细节，直接扩散预测是否提高模型内RL。
3. **WM与RL结合 / 最终动作**：在预测像素+reward/termination模型内训练CNN-LSTM actor/critic；部署actor，无online搜索。
4. **模型细节**：像素空间EDM U-Net next-frame，context图像+动作；denoise MSE，独立CNN-LSTM reward/termination，REINFORCE/λ-return；随机生成。附录Atari配置3NFE、想象H15；不迁移为FoReM默认值。
5. **实验条件**：Atari26任务×5seeds，100k动作；单4090≈12GB、2.9天/run；另CS:GO离线生成不是机器人RL；真实gameplay2h不是训练wall-time。
6. **主要结果与基线**：表1 meanHNS1.459 vs STORM1.266/IRIS1.046，IQM.641 vs STORM.636；11/26超人。强调细节收益依任务，而非扩散普遍优于所有latent模型。
7. **时延与执行偏差**：未涉及时延。
8. **局限与失败模式**：rare events、分布外行为和扩散生成开销；模型奖励误差；像素细节对游戏关键不证明局部地图SAC需视频扩散。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：模型任务效用与图像指标分开。 只能借鉴思路、条件不同：任务关键细节不能随意压缩。 不适用或本轮不得采用：直接引入像素生成或把CS:GO引擎当robot控制证据。

<a id="paper-simulus"></a>

## 20. Simulus — [SRC-0293](../../SOURCES.md#src-0293)

1. **元数据与深度**：Simulus: Combining Improvements in Sample-Efficient World Model Agents；作者：Cohen, Lior；Wang, Kaixin；Kang, Bingyi；Gadot, Uri；Mannor, Shie；机构：Technion、Microsoft Research、ByteDance Seed；首稿/公开日期：2025/02/17；发表场合：arXiv预印本，首稿2025、所读v4修订2026；实际所读：**arXiv 2502.11537v4**；[原文](https://arxiv.org/abs/2502.11537v4)；DOI：本轮未核到DOI。开源：公开官方代码：[链接](https://github.com/leor-c/Simulus)。阅读深度：**部分：摘要、§2方法、§3实验、消融及附录表9/compute**；核查位置：§2/3；图4/5；附录表9、Hardware/Run Times。
2. **问题与思想**：把世界模型agent的已知改进合并，检验是否互补。
3. **WM与RL结合 / 最终动作**：token模型想象训练actor/critic，非执行时规划；最终controller出动作。内在奖励改变探索/训练目标。
4. **模型细节**：REM/RetNet+parallel observation prediction，按模态tokenization；token CE、reward/value regression-as-classification；4个prediction head disagreement JSD作intrinsic reward，prioritized WM replay；CNN/MLP-LSTM controller、REINFORCE λ-return。
5. **实验条件**：Atari100k、DMC本体500k、Craftax1M；DMC连续向量和Craftax多模态token；附录AtariV100≈29h/4090≈12h、DMCV100≈40h；非Gazebo；统一控制Hz未报告。
6. **主要结果与基线**：附录表9 Atarimean1.645/IQM.990，DIAMOND1.459/.641、REM1.222/.673；图4 DMCmean796 vs DreamerV3 754；版本v4不可和v1结果混用。
7. **时延与执行偏差**：未涉及时延。
8. **局限与失败模式**：作者指出有限数据下intrinsic探索可能耗在无关区域；复合改进效应不能分配为单机制收益；公开后续Simulus-A不是本篇v4全部结果。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：明确每项训练机制的对照/成本。 只能借鉴思路、条件不同：模块化、动作模态与预测效用检查。 不适用或本轮不得采用：擅自加内在奖励/优先回放/额外探索，改变当前Task4合同。

<a id="paper-daydreamer"></a>

## 21. ★ DayDreamer — [SRC-0294](../../SOURCES.md#src-0294)

1. **元数据与深度**：DayDreamer: World Models for Physical Robot Learning；作者：Wu, Philipp；Escontrela, Alejandro；Hafner, Danijar；Goldberg, Ken；Abbeel, Pieter；机构：UC Berkeley；首稿/公开日期：2022/06/28；发表场合：CoRL 2022（所读arXiv v1）；实际所读：**arXiv 2206.14176v1**；[原文](https://arxiv.org/abs/2206.14176v1)；DOI：本轮未核到DOI。开源：公開官方代码：[链接](https://github.com/danijar/daydreamer)。阅读深度：**正文全文精读；附录D和机器人设置选读**；核查位置：§2/3.1–3.4/5；图4/5/6/7；附录D。
2. **问题与思想**：检验Dreamer能否在真实硬件低交互量下直接学习，而不是只在仿真成功。
3. **WM与RL结合 / 最终动作**：DreamerV2 RSSM监督训练，imagined actor/critic优化；actor和learner异步线程，最终actor出动作；没有SAC内部candidate反馈。
4. **模型细节**：多模态encoder、确定性h+离散z RSSM，重建/动力学KL/reward；continuous用重参数梯度、discrete用REINFORCE。正文H16与附录D H15分开保留计数；batch32×length32。
5. **实验条件**：A1 20Hz、12电机角经PD+Butterworth；UR5 2Hz离散XYZ末端增量+夹爪，Z仅抓物时允许/目标bin上自动开夹爪；XArm约.5Hz；Sphero2Hz扭矩。直接真机在线学习、无仿真/专家预训练。单GPU学习（正文未给统一GPU型号）；UR5 8h、XArm10h是实验wall-time。
6. **主要结果与基线**：图5 UR5 8h约2.5 objects/min，Rainbow/PPO只抓起后原bin放下；图4 A1≈1h翻身站立行走，SAC未站立/行走；图7 Sphero距离.15（场地归一单位），DrQv2表现相近。不能挑前两图宣称WM各平台必胜。
7. **时延与执行偏差**：未注入显式时延。异步用于减少动作计算阻塞，不等于识别/补偿驱动延迟；2Hz是任务动作频率。
8. **局限与失败模式**：作者：磨损/人为干预/长训练边界；核查：A1图是单run，UR5空间和抓放逻辑强约束，UR5基线离散Rainbow/PPO不是普通连续SAC，同型号不等于同控制条件。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：记录实际机器人动作限制和真实结果，保留不优于基线的案例。 只能借鉴思路、条件不同：异步训练与输入多模态；需经授权再做时序/性能验证。 不适用或本轮不得采用：将2Hz、8h和离散任务奖励当HuskyUR5合同/吞吐依据。

<a id="paper-wmpo"></a>

## 22. WMPO — [SRC-0295](../../SOURCES.md#src-0295)

1. **元数据与深度**：WMPO: World Model-based Policy Optimization for Vision-Language-Action Models；作者：Zhu, Fangqi；Yan, Zhengyang；Hong, Zicong；Shou, Quanxin；Ma, Xiao；Guo, Song；机构：HKUST、ByteDance Seed；首稿/公开日期：2025/11/12；发表场合：ICLR 2026身份由会议页面确认；正文实际读arXiv v1（2025），会议PDF本次403；实际所读：**arXiv 2511.09515v1**；[原文](https://arxiv.org/abs/2511.09515v1)；DOI：本轮未核到DOI。开源：官方公开代码：[链接](https://github.com/WM-PO/WMPO)（本轮只核页面/链接，未审计许可证兼容性或运行）。阅读深度：**部分：摘要、§3完整方法、§4实验/结果、附录A**；核查位置：§3.2–3.4/4.1/4.6；表1/2；附录A。
2. **问题与思想**：VLA的真实online RL代价大，用符合policy失败分布的视频模型支持on-policy GRPO。
3. **WM与RL结合 / 最终动作**：OXE视频预训→policy真实rollouts对齐WM→模型内GRPO；VideoMAE reward判别。最终VLA action head给动作；发生恢复行为不是显式candidate→feedback→SAC结构。
4. **模型细节**：OpenSora-STDiT-v3视频latent扩散但policy接口像素；去噪loss、noisy conditioning、逐帧action AdaLN；VideoMAE BCE success；action每维256bins，chunk8、context4帧、预测8帧；GRPO clipped ratio、动态丢弃同奖励组。
5. **实验条件**：MimicGen四task：每task300专家轨迹，另外P128/1280 policy真实轨迹做WM对齐，eval128初态；真实Cobot Mobile ALOHA：200专家+128policy，30trial、5mm插接间隙。附录policyBC8H100，WM/GRPO32H100；未核到统一controlHz/总wall-time。
6. **主要结果与基线**：表1 P128平均47.1%，DPO37.3/GRPO33.2/base33.6；P1280为57.6 vs42.4/37.1。§4.6真机base53%/DPO60%/WMPO70%；不是完全零真实数据。
7. **时延与执行偏差**：未研究显式时延；frame alignment是动作-视频对应关系。
8. **局限与失败模式**：failure分布对齐和reward classifier可靠性重要；动态丢弃组影响采样成本/口径；会议原文未读，结果对应arXiv版本；不能将对齐数据免费。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：WM需覆盖失败/当前policy分布，动作帧配对。 只能借鉴思路、条件不同：固定模型内训练的on-policy一致性；但GRPO非SAC。 不适用或本轮不得采用：加载VLA/额外轨迹/改变任务奖励或复制256动作bins。

<a id="paper-world4rl"></a>

## 23. World4RL — [SRC-0296](../../SOURCES.md#src-0296)

1. **元数据与深度**：World4RL: Diffusion World Models for Policy Refinement with Reinforcement Learning for Robotic Manipulation；作者：Jiang, Zhennan；Liu, Kai；Qin, Yuxin；Tian, Shuai；Zheng, Yupeng；Zhou, Mingcai；Yu, Chao；Li, Haoran；等（完整署名见原文）；机构：CAS/UCAS、Zhongguancun Academy、Tsinghua等（正文署名）；首稿/公开日期：2025/09/23；发表场合：arXiv预印本，2025；所读v2修订2026；实际所读：**arXiv 2509.19080v2**；[原文](https://arxiv.org/abs/2509.19080v2)；DOI：本轮未核到DOI。开源：项目页为占位链接，本次未找到可用官方实现：[链接](https://world4rl.github.io/)；不将YOUR_GITHUB_USERNAME模板当代码。阅读深度：**部分：摘要、§III方法、§IV实验/§V消融**；核查位置：§III/IV/V；表I/II/III/IV。
2. **问题与思想**：用高保真动作条件扩散模拟器，在固定离线数据上提高BC manipulation policy。
3. **WM与RL结合 / 最终动作**：先BC与reward classifier/WM预训，冻结WM，用想象PPO优化policy；部署policy，不在执行时额外搜索。
4. **模型细节**：像素EDM随机next-frame，4历史帧+连续动作twohot；denoise MSE、ResNet18成功BCE；PPO clipped目标并限制探索std，防分布外rollout。330M模型，不是RSSM。
5. **实验条件**：Meta-World六任务各50专家+150BC+30random轨迹、每条50步；真机Franka六任务各50专家+50BC+50random，固定初始场景、20eval/task。模型4A80040GB≈20h，policy单A800≈6h；controlHz未找到。
6. **主要结果与基线**：表II六个Meta-World任务平均SR67.5%；表III真机WORLD4RL报告93.3%、DP88.3%、BC68.3%。但BC逐行13/20、8/20、12/20、12/20、12/20、15/20，加总72/120=60.0%，与表中68.3%不一致；WORLD4RL112/120=93.3%、DP106/120=88.3%与均值一致。这里的60%仅是表内算术核查，未拿到原始trial数据，不能确定哪一项印错；原文“↑25”不作为已证提升。Put bread in WORLD4RL16/20低于DP18/20。表I policy-rollout FVD326.5 vs NWM547.4。
7. **时延与执行偏差**：未研究显式时延。
8. **局限与失败模式**：模型/成功classifier可能共同幻觉，动作support/std限制依赖数据；真机固定初态/少trial；WM组230轨迹vsBC50，不是同总信息预算。 核查发现表III BC汇总与分项算术矛盾，待独立复核/作者勘误；不以冲突值做收益结论。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：失败数据、OOD模型输出和任务SR分别审计。 只能借鉴思路、条件不同：冻结WM用于训练，模型高保真与task结果双证据。 不适用或本轮不得采用：改变SAC为PPO、加入成功classifier奖励或额外数据而不计预算。

<a id="paper-worldgymnast"></a>

## 24. World-Gymnast — [SRC-0297](../../SOURCES.md#src-0297)

1. **元数据与深度**：World-Gymnast: Training Robots with Reinforcement Learning in a World Model；作者：Sharma, Ansh Kumar；Sun, Yixiang；Lu, Ninghao；Zhang, Yunzhe；Liu, Jiarao；Yang, Sherry；机构：NYU、NYU Shanghai、UC Berkeley；首稿/公开日期：2026/02/02；发表场合：arXiv预印本2026，v1；实际所读：**arXiv 2602.02454v1**；[原文](https://arxiv.org/abs/2602.02454v1)；DOI：本轮未核到DOI。开源：官方公开代码：[链接](https://github.com/world-gymnast/world-gymnast)。阅读深度：**部分：摘要、§2/3方法、§4设置/主结果和适配说明**；核查位置：§3.1–3.4/4.1/4.2；表1/2；附录A.4。
2. **问题与思想**：训练VLA于视频WM能否超越SFT/传统软件仿真并迁移真机；另探索test-time训练与模型迭代。
3. **WM与RL结合 / 最终动作**：WorldGym生成视频，VLM给binary completion，GRPO优化OpenVLA-OFT；动作最终由VLA出。后续adaptation修改policy，而不是Task4冻结WM的首轮反馈。
4. **模型细节**：继承WorldGym600M latent diffusion（policy接口视频）；group相对优势、PPO式clipping，去KL、dynamic sampling；actionchunk5、rollout≤40模型步；模型具体损失见继承平台，不新造RSSM。
5. **实验条件**：Bridge/WidowX，17训练任务；AutoEval4真实任务，各10trial×5重复。4H200140GB full-policy finetune1–2天；对比SIMPLER有不同reward设计/任务覆盖；统一真实controlHz未找到。
6. **主要结果与基线**：表1开drawer58±4% vsSIMPLER34±7%，close62±6%低于74±5%；蓝sink72±10% vs32±10%。表2蓝sink SFT4±4%→72±10%即18×，不能泛称所有任务18×。
7. **时延与执行偏差**：未研究显式时延。
8. **局限与失败模式**：作者/方法：离线WM在policy distribution外误差累计，建议迭代真实数据；核查：VLM奖励、dynamic sampling成本与不同sim奖励需审；并非零采集成本/所有任务超过软件仿真。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：保留失败与不胜出任务，记录额外生成与reward计算。 只能借鉴思路、条件不同：模型/策略分布迭代风险和test-time compute单列。 不适用或本轮不得采用：把test-time GRPO混进Task4首轮或接VLM奖励。

<a id="paper-interactive"></a>

## 25. Interactive World Simulator — [SRC-0298](../../SOURCES.md#src-0298)

1. **元数据与深度**：Interactive World Simulator for Robot Policy Training and Evaluation；作者：Wang, Yixuan；Syed, Rhythm；Wu, Fangyu；Zhang, Mengchao；Onol, Aykut；Barreiros, Jose；Nayyeri, Hooshang；Dear, Tony；等（完整署名见原文）；机构：Columbia、Toyota Research Institute、Amazon、UIUC；首稿/公开日期：2026/03/09；发表场合：RSS 2026由官方代码标注；正文arXiv v1；实际所读：**arXiv 2603.08546v1**；[原文](https://arxiv.org/abs/2603.08546v1)；DOI：本轮未核到DOI。开源：官方公开代码：[链接](https://github.com/WangYixuan12/interactive_world_sim)。阅读深度：**部分：摘要、§III方法、§IV设置/预测/训练/评测结果**；核查位置：§III.B/C/D、IV.A–D；表I；图7。
2. **问题与思想**：以中等量robot交互数据获得实时长时稳定模型，供示范生成和policy评测。
3. **WM与RL结合 / 最终动作**：人/策略在WM中采合成示范后做imitation training（DP/ACT/π0等），以及policy evaluation；本篇不是在线SAC/GRPO训练收益。最终动作由外部imitation policy输出。
4. **模型细节**：image encoder+consistency decoder，冻结autoencoder后学latent consistency dynamics；3Dconv/FiLM、观测历史+动作；两阶段加权回归损失，context噪声训练；单帧自回归，随机模型。
5. **实验条件**：ALOHA双臂6真实task（绳、mug、piles等）+MuJoCo T-push；每task≈600×200step play episodes≈6h采集，T-pushsim10kepisodes；128²图像，动作空间有平面限制。训练单H2006h+12h，单4090最高15FPS/>10min稳定生成；192step=19.2s是评测视频时轴。
6. **主要结果与基线**：图7所绘四组真实/model相关r=.8553/.8455/.8869/.9908；只限所评task/policies。表I对比包括community Dreamer4实现（非作者官方），不能写成击败原作者配置。
7. **时延与执行偏差**：未研究受控时延；15FPS是model生成，不是ALOHA控制器Hz。
8. **局限与失败模式**：作者可访问生成demo不证明所有接触准确；任务限制/覆盖量、imitation示范人工开销；相关性不能替代真实反馈。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：区分仿真器指标和真实SR，基线实现身份透明。 只能借鉴思路、条件不同：consistency模型提速、闭环交互质量验证。 不适用或本轮不得采用：把合成示范训练算普通SAC或直接新增图像生成平台。

<a id="paper-worldgym"></a>

## 26. WorldGym — [SRC-0299](../../SOURCES.md#src-0299)

1. **元数据与深度**：WorldGym: World Model as An Environment for Policy Evaluation；作者：Quevedo, Julian；Sharma, Ansh Kumar；Sun, Yixiang；Suryavanshi, Varad；Liang, Percy；Yang, Sherry；机构：Stanford University、NYU、Google DeepMind；首稿/公开日期：2025/05/31；发表场合：arXiv预印本2025，v3仍标Under review；实际所读：**arXiv 2506.00613v3**；[原文](https://arxiv.org/abs/2506.00613v3)；DOI：本轮未核到DOI。开源：作者项目页本次未找到完整代码仓库（页面链接需后续核验）：[链接](https://world-model-eval.github.io/)。阅读深度：**部分：摘要、§3方法、§4实验、附录A参数**；核查位置：§3.1/3.2/4.1–4.3；图4；表1/2。
2. **问题与思想**：降低真实policy评估成本，用学得环境保持策略相对排名。
3. **WM与RL结合 / 最终动作**：外部VLA在action-conditioned WM中Monte Carlo rollout，GPT-4o评分；不是在这篇里用RL提高policy。
4. **模型细节**：latent DiT diffusion forcing，动作线性embedding/AdaLN、action dropout/CFG，因果temporalattention；horizon按policychunk变化，生成像素给policy，VLMreward不等于真实成功测量。
5. **实验条件**：OXE多机器人视频含Bridge/RT1/VIOLA/BerkeleyUR5；17个Bridge未见task，Octo/RT1X/OpenVLA对照；256²图像、7维动作；模型2A10080GB、300kupdates、batch16、10diffusionsteps。评估公开既有真机结果，非本轮新UR5训练。
6. **主要结果与基线**：图4/§4.1真实vsmodel：RT1-X14.0%vs15.5%，Octo20.0%vs23.82%，OpenVLA70.6%vs67.4%；对照为policy身份，不是baseline训练改进。
7. **时延与执行偏差**：未研究显式时延。
8. **局限与失败模式**：作者：精细物体交互仍难；VLM判分、fewpolicy相关和OOD生成幻觉；正确排序不意味着逐seed/绝对SR无偏。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：世界模型评测只作辅助，不能取代真实环境。 只能借鉴思路、条件不同：显式动作sweep和分布外相对排名检查。 不适用或本轮不得采用：用modelSR替代Gazebo物理末端成功验收。

<a id="paper-worldeval"></a>

## 27. WorldEval — [SRC-0300](../../SOURCES.md#src-0300)

1. **元数据与深度**：WorldEval: World Model as Real-World Robot Policies Evaluator；作者：Li, Yaxuan；Zhu, Yichen；Wen, Junjie；Shen, Chaomin；Xu, Yi；机构：Midea Group、East China Normal University；首稿/公开日期：2025/05/25；发表场合：arXiv预印本2025，v1；实际所读：**arXiv 2505.19017v1**；[原文](https://arxiv.org/abs/2505.19017v1)；DOI：本轮未核到DOI。开源：官方公开代码：[链接](https://github.com/liyaxuanliyaxuan/Worldeval)。阅读深度：**部分：摘要、§3方法、§4实验/表1/2、附录A/B**；核查位置：§3.2/3.3/4；表1/2；附录A/B。
2. **问题与思想**：以policy内部latent action作为video控制信号，构造相对performance评测代理。
3. **WM与RL结合 / 最终动作**：Policy2Vec latent+language+首图生成视频，Gemini2.0判断success；不做模型内RL，最终动作仍由被评policy产生。latent action不是最终执行指令。
4. **模型细节**：WAN2.1 14B image-to-video latent扩散、LoRA+projection；条件是policy输出前latent embedding与语言；依赖生成模型原去噪目标，未引入物理state监督。附录81帧、50diffusionsteps。
5. **实验条件**：AgileX ALOHA式双6DoF，14维联合动作/状态，top RealSense457，采集50Hz；5tasks每task40eval、总>1000rollouts；部分tasks100/50轨迹。附录8H800约11h LoRA训练，非推理Hz。
6. **主要结果与基线**：表1 WorldEval vs RoboTwin real-to-sim平均Pearson .942 vs .411、MMRV .044 vs .261；表2 Policy2Vec .939 vsVQVAE -.862，一种编码依赖此policy/dataset条件。
7. **时延与执行偏差**：未受控研究时延；50Hz数据采样不能作为UR5频率依据。
8. **局限与失败模式**：作者：低成绩policy幻觉/ghosting和未知场景泛化；核查：用最终checkpoint latent训练WM可能混淆“latent更接近训练分布”与真实policy更好（附录B对此现象有描述），跨policy latent语义不必共通。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：评测代理与独立物理反馈分开，数据/策略身份审计。 只能借鉴思路、条件不同：行为表征对齐和排名而非像素指标评估。 不适用或本轮不得采用：拿policy latent代替真实执行动作监督或用Pearson作Task4任务验收。

<a id="paper-ctrlworld"></a>

## 28. Ctrl-World — [SRC-0301](../../SOURCES.md#src-0301)

1. **元数据与深度**：Ctrl-World: A Controllable Generative World Model for Robot Manipulation；作者：Guo, Yanjiang；Shi, Lucy Xiaoyang；Chen, Jianyu；Finn, Chelsea；机构：Stanford University、Tsinghua University；首稿/公开日期：2025/10/11；发表场合：ICLR 2026；首稿2025，所读v3；实际所读：**arXiv 2510.10125v3**；[原文](https://arxiv.org/abs/2510.10125v3)；DOI：本轮未核到DOI。开源：官方公开代码：[链接](https://github.com/Robert-gyj/Ctrl-World)。阅读深度：**部分：摘要、§4方法、§5设置/结果及§6局限**；核查位置：§4.1/4.2/5.1–5.4/6；表1；图9。
2. **问题与思想**：让视频WM支持现代多视角VLA的精确动作控制和长rollout，再用于评测/数据改善。
3. **WM与RL结合 / 最终动作**：多视角预测→外部policy rollout评测；搜索并人选成功合成轨迹后SFT改善policy，非RL。最终π0.5等policy出动作。
4. **模型细节**：SVD1.5B latent diffusion，三视角jointtokens、pose-conditioned sparse history memory+frameaction crossattention；diffusion x0 MSE；历史7帧、间隔1–2s、下一15动作=1schunk。
5. **实验条件**：DROID95,599轨迹、564场景、约76k成功/19k失败；192×320×3camera，16H100、batch64、2–3天；数据15动作/s不等于FoReM动作Hz；每task生成400轨迹人选25–50成功、SFT2kupdates。
6. **主要结果与基线**：表1第三视角PSNR23.56/FVD97.4 vs WPE单视角20.33/156.4；图9新指令任务成功38.7%→83.4%，提高44.7个百分点，非相对44.7%；是合成data SFT。
7. **时延与执行偏差**：未研究通信/执行时延；历史1–2s采样间隔非delay。
8. **局限与失败模式**：作者明确不够精确以改善已见指令低层success；精细接触/长推理/初态敏感；人选/成功过滤成本不可省略。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：成功率差分单位和额外人工/数据成本写清。 只能借鉴思路、条件不同：长期history re-anchoring、action细粒度对齐。 不适用或本轮不得采用：把SFT提升当冻结WM反馈SAC收益或直接新增multi-camera。

<a id="paper-delayfixed"></a>

## 29. ★ 固定观测延迟 Dreamer — [SRC-0302](../../SOURCES.md#src-0302)

1. **元数据与深度**：Reinforcement Learning from Delayed Observations via World Models；作者：Karamzade, Armin；Kim, Kyungmin；Kalsi, Montek；Fox, Roy；机构：UC Irvine；首稿/公开日期：2024/03/18；发表场合：RLC/RLJ 2024（所读arXiv v2）；实际所读：**arXiv 2403.12309v2**；[原文](https://arxiv.org/abs/2403.12309v2)；DOI：本轮未核到DOI。开源：官方公开代码：[链接](https://github.com/indylab/DelayedDreamer)。阅读深度：**正文全文精读；理论定义/命题按假设核查；附录B各数据表选读**；核查位置：§3.1/3.3/4.1–4.4/5/6；图3/4；附录B表1–3。
2. **问题与思想**：观测延迟叠加partial observability时，如何利用latent历史/动作缓冲实现可靠控制。
3. **WM与RL结合 / 最终动作**：Extended actor以延迟latent+其后已执行actions为输入；Latent actor把模型推进d步；Memoryless不用动作buffer，Agnostic在无delay训练后仅推理补偿。Dreamer模型内actor学习，最终actor输出，不是candidate下一步反馈。
4. **模型细节**：DreamerV3 RSSM deterministic+stochastic，继承重建/奖励/continue+KL；model监督按真实时间重新对齐；Extended actor/critic值监督再对齐；模型理论等价要求congruent，不声称学得模型精确满足。H16正文，与episode/d相关会影响有效想象。
5. **实验条件**：MuJoCo4任务Dreamer500k steps，对照DCAC1M、D-TRPO5M；DMC6任务本体/图像，图像1M，5seeds。无真机；控制Hz和GPU/总wall-time正文未报告，不能把步数换毫秒。
6. **主要结果与基线**：附录B表3 Cheetah Run图像d20：Extended493.3±21.8、Memoryless395.5±21.2、Latent273.1±24.6、Agnostic118.8±11.4（SEM）；§5.2视觉DMC归一均值相对Agnostic约+250%（作者汇总，不能用该单task数字重建它）。
7. **时延与执行偏差**：观测/奖励到达层：固定d∈{2,5,10,20}环境/决策步，agent得到o(t-d)/r(t-d)，动作不故意迟发。reset初期随机动作等首观测；监督完成后重排为真实(o,a,r)。原文不提供统一秒数，未沿用为UR5取值。
8. **局限与失败模式**：作者：Latent多步误差累积、Extended架构与超参敏感、Reacher弱；核查：不同baselines交互预算不等，未知delay训练与已知训练不能合并；固定delay证明不涵盖随机乱序。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：测量stamp、已执行动作历史与监督配对。 只能借鉴思路、条件不同：把到达观测前的belief预测与训练信息权限分开。 不适用或本轮不得采用：新增delay机制、把d20换成UR5毫秒、宣称能补偿物理驱动动态。

<a id="paper-delayrandom"></a>

## 30. ★ 随机观测延迟 DA-Dreamer — [SRC-0303](../../SOURCES.md#src-0303)

1. **元数据与深度**：Model-Based Reinforcement Learning under Random Observation Delays；作者：Karamzade, Armin；Kim, Kyungmin；Lanier, JB；Corsi, Davide；Fox, Roy；机构：UC Irvine；首稿/公开日期：2025/09/25；发表场合：L4DC 2026，PMLR331；首稿2025，所读arXiv v2；实际所读：**arXiv 2509.20869v2**；[原文](https://arxiv.org/abs/2509.20869v2)；DOI：本轮未核到DOI。开源：官方公开代码：[链接](https://github.com/indylab/DA-Dreamer)。阅读深度：**正文全文精读；附录A/B.1–B.4；证明/滤波近似按条件核查**；核查位置：§3/4.1/4.2/5/7；式3–6；算法1；表1/2；附录A/B。
2. **问题与思想**：随机sensor delay导致旧观测乱序到达，怎样保留可用信息并推当前belief。
3. **WM与RL结合 / 最终动作**：timestamped buffer，重放从最早未到达观测前的belief checkpoint；有观测用posterior、没有用prior，policy根据belief采样；model完整顺序数据训练，policy按received information；最终Dreamer actor。
4. **模型细节**：RSSM ELBO/重建+KL；approximate posterior filtering，可Kparticles（默认1），确定性路径保留history；等待episode末所有pending观测再入replay；imagination没有新真实观测，作者承认训练分布有偏差。
5. **实验条件**：MuJoCo6任务/Meta-World4视觉任务、64²、1M envsteps、5seed；Meta-World repeat2→500k decision steps，回合人为缩到50步（主动放大deadline效应），无真机。GPU/总时长/统一Hz未报告。
6. **主要结果与基线**：表1 U{0,10} HalfCheetah DA4985.40±253.10 vs Encoding4189.26±401.81；U{0,20} DA2958.56±54.19低于Encoding4242.77±213.47。表2 N+(20,1) buttonpress SR .91±.13 vs memoryless .12±.14；均为mean/95%CI。
7. **时延与执行偏差**：sensor观测生成后独立整数d，到达t+d，允许0/多个/OOS；假设已知生成stamp及有界maxD。分布U{0,10}/U{0,20}，MetaU{0,5}、N+(10,3)/N+(20,1)（按文中记号，Gaussian截断后round整数，参数第二项遵原文方差约定）；不提供统一秒数，无UR5换算。
8. **局限与失败模式**：作者：递归误差、开销随最大delay线性增加；核查：近似belief不是精确posterior，K1缺全面不确定性表达，50步Metaepisode改变条件，逐task不全面占优。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：到达时刻与采样时刻分开、乱序重播及跨episode边界。 只能借鉴思路、条件不同：历史belief与实时信息权限。 不适用或本轮不得采用：擅自新增乱序队列/重写观察合同/搬delay步数为硬件设定。

<a id="paper-residualdelay"></a>

## 31. Residual RL Teleoperation — [SRC-0304](../../SOURCES.md#src-0304)

1. **元数据与深度**：Residual Reinforcement Learning for Robot Teleoperation under Stochastic Delays；作者：Deng, Kaize；Yang, Zewen；机构：Technical University of Munich；首稿/公开日期：2026/05/14；发表场合：arXiv预印本2026，v1；实际所读：**arXiv 2605.15480v1**；[原文](https://arxiv.org/abs/2605.15480v1)；DOI：本轮未核到DOI。开源：原文未给可核的官方代码链接，本次开源状态未知。阅读深度：**部分：摘要、§2系统/§3方法、§4实验与附录训练说明**；核查位置：§2.1–2.4/3.1/3.2/4.1–4.3；表1。
2. **问题与思想**：随机通信延迟造成遥操作状态跳变/抖振，用LSTM平滑预测和residualSAC补偿torque。
3. **WM与RL结合 / 最终动作**：LSTM重建当前leader状态，nominal computed-torque PD+SAC residual torque；最终力矩为两项合成，不是Task4 SAC高层动作全量输出。
4. **模型细节**：数值state空间LSTM+residual head，history q/qdot/delay，监督state估计与smoothness；SAC critic/actor和tracking/velocity代价；没有视觉生成latent WM。
5. **实验条件**：同构leader/follower Franka Panda，MuJoCo训练后真机部署无重训；采样4ms=250Hz；7关节力矩、任务Cartesian轨迹；总steps/GPU/完整wall-time未从已读设置中核出，保留未核验。
6. **主要结果与基线**：表1高delay/highvariance sim meanCartesian error .037m/max.063m，real .045m/.078m；1.22×/1.24×是sim-to-real误差比，不是相对baseline提高倍数。PD/PMDC为性能图基线，未从曲线猜精确值。
7. **时延与执行偏差**：leader→agent状态传输U(120,160)/U(200,240)/U(40,240)ms；agent–follower action/observation链正文写ωo=ωa=50ms；作者报告总170–210/250–290/90–290ms，仅加一次50。符号/链路累计有歧义，不能自作解释加两次。4ms采样中状态delay分别30–40/50–60/10–60周期（端点整除无取整）；50ms=12.5周期，原文未给离散取整，本轮不补造。
8. **局限与失败模式**：本体/torque/nominalcontroller与UR5位置控制不同；LSTM真实监督依仿真可得state，传递延迟不是servo响应；稳定性描述不构成任意policy正式证明。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：采样周期、链路层次与不确定符号明确记。 只能借鉴思路、条件不同：残差分工、tracking与smoothness冲突。 不适用或本轮不得采用：未经授权新增torque residual控制/teleop或沿用Panda delay值为UR5合理范围。

<a id="paper-survey1"></a>

## 32. World Model for Robot Learning: A Comprehensive Survey — [SRC-0305](../../SOURCES.md#src-0305)

1. **元数据与深度**：World Model for Robot Learning: A Comprehensive Survey；作者：Hou, Bohan；Li, Gen；Jia, Jindou；An, Tuo；Guo, Xinying；Leng, Sicong；Geng, Haoran；Ze, Yanjie；等（完整署名见原文）；机构：NTU及Berkeley/Stanford/Tokyo/Oxford/Microsoft/ETH/Princeton/Harvard联合团队；首稿/公开日期：2026/04/30；发表场合：arXiv综述预印本（版本/日期见元数据）；实际所读：**arXiv 2605.00080v1**；[原文](https://arxiv.org/abs/2605.00080v1)；DOI：本轮未核到DOI。开源：[链接](https://github.com/NTUMARS/Awesome-World-Model-for-Robotics-Policy)。阅读深度：**部分原文：摘要、§3分类/§4 simulator、§7评测、§8.4–8.6挑战；对被引方法的讨论属于二手线索，不视为已读其原文**；核查位置：§3.1/3.2–3.6/4/7/8；表1/5/6。
2. **问题与思想**：按policy结合架构、learned simulator与robotvideo model功能组织文献。
3. **WM与RL结合 / 最终动作**：综述覆盖想象训练、规划、候选筛选、数据生成/评测；最终动作输出者随被引方法变化。所引其他论文本轮未精读，标二手线索。
4. **模型细节**：包含像素/latent/几何/随机/确定性各族，不存在本综述单一模型、预测horizon或训练loss；应回原始方法核验。
5. **实验条件**：非新训练/实验研究；机器人、动作频率、数据/compute来自不同文献，不能合并为统一设定。
6. **主要结果与基线**：表1分类、表5/6摘录他文benchmark；没有新机器人运行或统一实验预算，不能直接把表中汇总当同协议排名。
7. **时延与执行偏差**：没有本综述自己的受控时延实测；被引方法时延参数未在本条核验，不登记成UR5依据。
8. **局限与失败模式**：综述分类是作者整理框架，非所有方法的独立复现；跨版本/平台/预算数值不能直接排名，近期期刊模板页眉不当发表场合。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：仅用分类检查当前方法描述和评测是否混淆。 只能借鉴思路、条件不同：候选补读定位与predictive fidelity/control utility分离。 不适用或本轮不得采用：凭综述二手数值设Task4参数或扩大正式精读/实施范围。

<a id="paper-survey2"></a>

## 33. World-Action Models for Robot Learning and Control: A Survey — [SRC-0306](../../SOURCES.md#src-0306)

1. **元数据与深度**：World-Action Models for Robot Learning and Control: A Survey；作者：Lu, Zuxing；Zhai, Hongjia；Wang, Guanzhi；Zeng, Huajian；Yang, Jiaqi；Liu, Jingyu；Cheng, Lei；Zhang, Yuantai；等（完整署名见原文）；机构：MBZUAI及Caltech/Amazon/UVA/Georgia Tech/NYU/Berkeley联合团队；首稿/公开日期：2026/09/13；发表场合：arXiv综述预印本（版本/日期见元数据）；实际所读：**arXiv 2609.16074v1**；[原文](https://arxiv.org/abs/2609.16074v1)；DOI：本轮未核到DOI。开源：原文官方项目清单：[链接](https://rcl-robotics.github.io/Awesome-World-Action-Models)；这是文献资源入口，不是本综述训练实现。阅读深度：**部分原文：摘要、§II概念、§III模型分类、应用/§V评测与挑战；对被引方法的讨论属于二手线索，不视为已读其原文**；核查位置：§II/III/V；表II/III；参考[74]。
2. **问题与思想**：统一未来world prediction与可执行action的WAM分类，区分transition、actioninterface和训练流程。
3. **WM与RL结合 / 最终动作**：综述覆盖想象训练、规划、候选筛选、数据生成/评测；最终动作输出者随被引方法变化。所引其他论文本轮未精读，标二手线索。
4. **模型细节**：包含像素/latent/几何/随机/确定性各族，不存在本综述单一模型、预测horizon或训练loss；应回原始方法核验。
5. **实验条件**：非新训练/实验研究；机器人、动作频率、数据/compute来自不同文献，不能合并为统一设定。
6. **主要结果与基线**：表II为HNS/SR/轨迹/生成等指标定义、表III资源映射；无原创RL性能表或统一训练预算。
7. **时延与执行偏差**：没有本综述自己的受控时延实测；被引方法时延参数未在本条核验，不登记成UR5依据。
8. **局限与失败模式**：综述分类是作者整理框架，非所有方法的独立复现；跨版本/平台/预算数值不能直接排名，近期期刊模板页眉不当发表场合。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：仅用分类检查当前方法描述和评测是否混淆。 只能借鉴思路、条件不同：候选补读定位与predictive fidelity/control utility分离。 不适用或本轮不得采用：凭综述二手数值设Task4参数或扩大正式精读/实施范围。

<a id="paper-survey3"></a>

## 34. World Models for Robotic Manipulation: A Survey — [SRC-0307](../../SOURCES.md#src-0307)

1. **元数据与深度**：World Models for Robotic Manipulation: A Survey；作者：Wang, Fangyuan；Wang, Ziyuan；Pei, Guorui；Zhang, Mengshi；Liang, Canxi；Hu, Jun；Li, Zhongxuan；Wu, Jinsong；等（完整署名见原文）；机构：Hong Kong PolyU、Great Bay University、KTH等（全机构见原文署名）；首稿/公开日期：2026/05/27；发表场合：arXiv综述预印本（版本/日期见元数据）；实际所读：**arXiv 2606.00113v1**；[原文](https://arxiv.org/abs/2606.00113v1)；DOI：本轮未核到DOI。开源：本轮未核到独立官方代码/清单repo。阅读深度：**部分原文：摘要、representation分类、§IV/V/VI功能与§VIII评测、候选引用条目；对被引方法的讨论属于二手线索，不视为已读其原文**；核查位置：§IV/V.B/V.C/V.D/VI/VIII；参考[69]/[84]/[85]/[90]。
2. **问题与思想**：按预测表征、预测与动作怎样联系、在流程何处使用三个问题分类，区分candidate filtering、search、learned environment与验证。
3. **WM与RL结合 / 最终动作**：综述覆盖想象训练、规划、候选筛选、数据生成/评测；最终动作输出者随被引方法变化。所引其他论文本轮未精读，标二手线索。
4. **模型细节**：包含像素/latent/几何/随机/确定性各族，不存在本综述单一模型、预测horizon或训练loss；应回原始方法核验。
5. **实验条件**：非新训练/实验研究；机器人、动作频率、数据/compute来自不同文献，不能合并为统一设定。
6. **主要结果与基线**：综述称覆盖34个manipulation datasets；分类表不是新实验数值，对被引方法只作二手定位。
7. **时延与执行偏差**：没有本综述自己的受控时延实测；被引方法时延参数未在本条核验，不登记成UR5依据。
8. **局限与失败模式**：综述分类是作者整理框架，非所有方法的独立复现；跨版本/平台/预算数值不能直接排名，近期期刊模板页眉不当发表场合。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：仅用分类检查当前方法描述和评测是否混淆。 只能借鉴思路、条件不同：候选补读定位与predictive fidelity/control utility分离。 不适用或本轮不得采用：凭综述二手数值设Task4参数或扩大正式精读/实施范围。

<a id="paper-survey4"></a>

## 35. A Step Toward World Models: A Survey on Robotic Manipulation — [SRC-0308](../../SOURCES.md#src-0308)

1. **元数据与深度**：A Step Toward World Models: A Survey on Robotic Manipulation；作者：Zhang, Peng-Fei；Cheng, Ying；Sun, Xiaofan；Wang, Shijie；Li, Fengling；Zhu, Lei；Shen, Heng Tao；机构：作者联合机构详见正文署名；本轮未逐机构核验；首稿/公开日期：2025/10/31；发表场合：arXiv综述预印本（版本/日期见元数据）；实际所读：**arXiv 2511.02097v2**；[原文](https://arxiv.org/abs/2511.02097v2)；DOI：本轮未核到DOI。开源：本轮未核到独立官方代码/清单repo。阅读深度：**部分原文：摘要、§II概念、§III概览、§IV决策/训练功能与§V挑战/结论；对被引方法的讨论属于二手线索，不视为已读其原文**；核查位置：§II/III/IV/V；表I；参考[22]/[30]/[63]。
2. **问题与思想**：不限定worldmodel名词，用perception/prediction/control功能讨论机器人方法和缺口。
3. **WM与RL结合 / 最终动作**：综述覆盖想象训练、规划、候选筛选、数据生成/评测；最终动作输出者随被引方法变化。所引其他论文本轮未精读，标二手线索。
4. **模型细节**：包含像素/latent/几何/随机/确定性各族，不存在本综述单一模型、预测horizon或训练loss；应回原始方法核验。
5. **实验条件**：非新训练/实验研究；机器人、动作频率、数据/compute来自不同文献，不能合并为统一设定。
6. **主要结果与基线**：表I列方法组成、输入/输出/architecture；没有原创training run或跨论文统一胜负实验。
7. **时延与执行偏差**：没有本综述自己的受控时延实测；被引方法时延参数未在本条核验，不登记成UR5依据。
8. **局限与失败模式**：综述分类是作者整理框架，非所有方法的独立复现；跨版本/平台/预算数值不能直接排名，近期期刊模板页眉不当发表场合。
9. **FoReM关系（以下均为建议，待用户授权）**：可直接借鉴的记录/分析原则：仅用分类检查当前方法描述和评测是否混淆。 只能借鉴思路、条件不同：候选补读定位与predictive fidelity/control utility分离。 不适用或本轮不得采用：凭综述二手数值设Task4参数或扩大正式精读/实施范围。

## 方法对比表

“高/中/低”是对Task4机制的条件映射，不是推荐执行顺序或性能排名。像素接口与内部latent建模分开；时延栏只指论文明确建模的时延。所有选择均为建议（待用户授权）。
|方法（来源）|结合方式|最终动作由谁输出|潜空间|涉及时延|平台|开源|Task4相关度与理由|
|---|---|---|---|---|---|---|---|
|[★ Dreamer 4](#paper-dreamer4) / [SRC-0274](../../SOURCES.md#src-0274)|想象训练|policy头|是（连续token）|未涉及|Minecraft；SOAR展示|未核到/未知|中：冻结模型和动作因果有启发，RL与动作合同不同|
|[★ DreamerV3](#paper-dreamer3) / [SRC-0275](../../SOURCES.md#src-0275)|想象训练|Dreamer actor|是（RSSM）|未涉及|仿真/游戏|官方公开入口|中：表征与训练稳定性有用，但不是最终SAC反馈|
|[DreamerV2](#paper-dreamer2) / [SRC-0276](../../SOURCES.md#src-0276)|想象训练|Dreamer actor|是（离散RSSM）|未涉及|Atari/仿真humanoid|官方公开入口|中：历史表征有用，非SAC反馈|
|[DreamerV1](#paper-dreamer1) / [SRC-0277](../../SOURCES.md#src-0277)|想象训练|action网络|是（高斯RSSM）|未涉及|DMC等仿真|官方公开入口|中：预测与价值区分有用，训练不同|
|[PlaNet](#paper-planet) / [SRC-0278](../../SOURCES.md#src-0278)|在线CEM|CEM首动作|是（RSSM）|未涉及|DMC仿真|官方公开入口|中：决策前预测，但替换动作决策者|
|[MuZero](#paper-muzero) / [SRC-0279](../../SOURCES.md#src-0279)|MCTS|搜索策略|是（隐状态）|未涉及|棋类/Atari|未核到/未知|低：动作/资源差异大|
|[Genie](#paper-genie) / [SRC-0280](../../SOURCES.md#src-0280)|生成环境/BC转移|用户/latent policy|是（离散token）|未涉及|平台游戏/机器人视频|未核到/未知|低：缺实际动作合同与SAC反馈|
|[Genie 3（官方博客）](#paper-genie3) / [SRC-0281](../../SOURCES.md#src-0281)|生成环境演示|SIMA/用户|内部未知|未涉及|交互视频|未核到/未知|低：只有产品级原始描述|
|[UniSim](#paper-unisim) / [SRC-0282](../../SOURCES.md#src-0282)|模型内RL/数据增强|VLA或IDM|视频生成（非RSSM）|未涉及|Language Table等|未核到/未知|中：训练和评测分层有用，模型成本不同|
|[GameNGen](#paper-gamengen) / [SRC-0283](../../SOURCES.md#src-0283)|RL采数据→生成引擎|玩家/外部policy|是（VAE扩散）|未涉及|DOOM|未核到/未知|低：并未用WM改善部署策略|
|[★ V-JEPA 2](#paper-vjepa2) / [SRC-0284](../../SOURCES.md#src-0284)|latent CEM（无机器人RL）|CEM首动作|是（JEPA）|未涉及|Franka真机|官方公开入口|高：直接动作条件/固定表征，但最终动作仍不同|
|[Navigation World Models](#paper-nwm) / [SRC-0285](../../SOURCES.md#src-0285)|CEM/外部候选排序|CEM或rerank候选|是（VAE扩散）|未涉及|导航视频/轨迹|官方公开入口|高：候选预测排序，执行者不同|
|[Cosmos](#paper-cosmos) / [SRC-0286](../../SOURCES.md#src-0286)|生成平台/后训练|外部policy/控制|是（连续/离散）|未涉及|视频；Bridge/EVE后训|官方公开入口|低：基础设施贡献，缺普通SAC对照|
|[★ TD-MPC2](#paper-tdmpc2) / [SRC-0287](../../SOURCES.md#src-0287)|MPPI+policy prior|MPPI首动作|是（确定性）|未涉及|连续控制仿真|官方公开入口|高：模型/价值/候选关系直接相关，执行结构不同|
|[★ TD-MPC](#paper-tdmpc) / [SRC-0288](../../SOURCES.md#src-0288)|MPPI+terminal Q|MPPI首动作|是（确定性）|未涉及|DMC/Meta-World|官方公开入口|高：连续候选后果/终端value关系|
|[★ MBPO](#paper-mbpo) / [SRC-0289](../../SOURCES.md#src-0289)|短模型rollout训练SAC|SAC actor|否（原观测向量）|未涉及|MuJoCo|官方公开入口|高：清单中最直接保留SAC的例子，用途非内部反馈|
|[Dream-MPC](#paper-dreammpc) / [SRC-0290](../../SOURCES.md#src-0290)|policy候选→梯度MPC|梯度优化首动作|是（随基础模型）|未涉及|控制仿真|官方公开入口|高：预测后动作修正很贴近，最终决策与SAC不同|
|[IRIS](#paper-iris) / [SRC-0291](../../SOURCES.md#src-0291)|想象训练|CNN-LSTM actor|模型是；actor用解码像素|未涉及|Atari|官方公开入口|低：游戏/离散动作，token细节与当前不同|
|[DIAMOND](#paper-diamond) / [SRC-0292](../../SOURCES.md#src-0292)|像素想象RL|CNN-LSTM actor|否（像素EDM）|未涉及|Atari/CS:GO|官方公开入口|低：观测/动作与Task4差异大|
|[Simulus](#paper-simulus) / [SRC-0293](../../SOURCES.md#src-0293)|token想象训练|controller|是（token）|未涉及|Atari/DMC/Craftax|官方公开入口|中：连续向量和模型训练组织有关|
|[★ DayDreamer](#paper-daydreamer) / [SRC-0294](../../SOURCES.md#src-0294)|潜态想象训练|Dreamer actor|是（RSSM）|未涉及|A1/UR5/XArm/Sphero真机|未核到/未知|高：有真实UR5证据，但动作与基线不同|
|[WMPO](#paper-wmpo) / [SRC-0295](../../SOURCES.md#src-0295)|WM内GRPO|VLA动作头|WM是latent，策略用像素|未涉及|MimicGen/ALOHA真机|官方公开入口|中：分布/失败对齐有关，策略体系不同|
|[World4RL](#paper-world4rl) / [SRC-0296](../../SOURCES.md#src-0296)|像素WM内PPO|PPO policy|否（像素EDM）|未涉及|Meta-World/Franka|未核到/未知|中：冻结WM真机收益，机制不同|
|[World-Gymnast](#paper-worldgymnast) / [SRC-0297](../../SOURCES.md#src-0297)|WM内GRPO/后续适配|VLA policy|WM是latent，策略用像素|未涉及|WidowX真机/SIMPLER|官方公开入口|中：真实RL效果，但模型与训练权限不同|
|[Interactive World Simulator](#paper-interactive) / [SRC-0298](../../SOURCES.md#src-0298)|合成数据imitation/评测|外部policy/操作人|是（consistency latent）|未涉及|ALOHA/仿真T-push|官方公开入口|中：闭环预测效用与测量，非SAC反馈|
|[WorldGym](#paper-worldgym) / [SRC-0299](../../SOURCES.md#src-0299)|policy评测|外部VLA|是（DiT）|未涉及|Bridge/WidowX等|未核到/未知|中：适用评测风险，非训练反馈|
|[WorldEval](#paper-worldeval) / [SRC-0300](../../SOURCES.md#src-0300)|policy评测|被评policy|是（video latent/latent action）|未涉及|AgileX双臂真机|官方公开入口|中：latent来源/评测混淆风险直接相关|
|[Ctrl-World](#paper-ctrlworld) / [SRC-0301](../../SOURCES.md#src-0301)|评测/成功合成data SFT|外部VLA|是（SVD latent）|未涉及|DROID/Franka|官方公开入口|中：动作对齐与记忆，非SAC更新|
|[★ 固定观测延迟 Dreamer](#paper-delayfixed) / [SRC-0302](../../SOURCES.md#src-0302)|delay belief/想象训练|Dreamer actor|是（RSSM）|观测，固定步数|MuJoCo/DMC|官方公开入口|高：时间/动作配对；目标不是当前Task4误差注入|
|[★ 随机观测延迟 DA-Dreamer](#paper-delayrandom) / [SRC-0303](../../SOURCES.md#src-0303)|OOS belief/想象训练|Dreamer actor|是（RSSM）|观测，随机/OOS|MuJoCo/Meta-World|官方公开入口|高：实际时间/历史正确性，但非候选反馈证明|
|[Residual RL Teleoperation](#paper-residualdelay) / [SRC-0304](../../SOURCES.md#src-0304)|state预测+residualSAC|nominal PD+SAC torque合成|否（数值state）|通信状态/动作（累计歧义）|Franka仿真/真机|未核到/未知|中：时延+SAC，控制层/目标显著不同|
|[World Model for Robot Learning: A Comprehensive Survey](#paper-survey1) / [SRC-0305](../../SOURCES.md#src-0305)|分类综述|随方法|覆盖多类|无本综述实测|跨平台文献|文献清单|中：补漏与评测分类，非新实证|
|[World-Action Models for Robot Learning and Control: A Survey](#paper-survey2) / [SRC-0306](../../SOURCES.md#src-0306)|分类综述|随方法|覆盖多类|无本综述实测|跨平台文献|文献清单|中：补漏与评测分类，非新实证|
|[World Models for Robotic Manipulation: A Survey](#paper-survey3) / [SRC-0307](../../SOURCES.md#src-0307)|分类综述|随方法|覆盖多类|无本综述实测|跨平台文献|未核到/未知|中：补漏与评测分类，非新实证|
|[A Step Toward World Models: A Survey on Robotic Manipulation](#paper-survey4) / [SRC-0308](../../SOURCES.md#src-0308)|分类综述|随方法|覆盖多类|无本综述实测|跨平台文献|未核到/未知|中：补漏与评测分类，非新实证|

## 对 Task4 的启示（待授权建议）

以下仅登记推论/建议，不增加Task4执行范围、参数、实验组或预算。现有合同从已读Task4三文档理解；其历史“未实施”状态与较新PROGRESS记录不一致，本轮不据此验收或修改任何运行结论。
1. **先按最终决策权比较机制**。MBPO保留SAC、以模型短rollout供训练数据，TD-MPC/PlaNet/Dream-MPC在决策时直接优化动作，Dreamer系列在想象中训练另一个actor，NWM可重排外部候选。这些分别支持训练数据、后果搜索或策略学习；本清单没有直接验证Husky+UR5同合同下的‘候选→预测→内部反馈→最终SAC’四阶段收益。建议逐环说明从哪篇借鉴，不能把组合写成文献已证方案。[SRC-0289](../../SOURCES.md#src-0289)、[SRC-0287](../../SOURCES.md#src-0287)、[SRC-0285](../../SOURCES.md#src-0285)、[SRC-0274](../../SOURCES.md#src-0274)。
2. **动作标签与反馈身份需要明确**。V-JEPA 2-AC使用相邻实际末端状态差构造动作标签，Genie潜动作是视频识别的token；这些不等同于FoReM发送的底盘/末端命令。建议核查预测输入是候选指令、已实现运动还是规划状态，保持真实反馈与内部表征分开。此为方法适用性判断，不授权改观测。[SRC-0284](../../SOURCES.md#src-0284)、[SRC-0280](../../SOURCES.md#src-0280)。
3. **冻结WM后的策略分布变化是待检风险**。World4RL限制PPO探索且加入随机轨迹、WMPO用额外policy轨迹对齐模型；MBPO短rollout减少特定条件下的模型误差。建议未来授权评审时明确模型覆盖与分布外动作、逐任务负结果，不把‘模型固定’或‘预测loss低’直接当闭环可靠性。World4RL表III的BC数值冲突必须先复核。[SRC-0296](../../SOURCES.md#src-0296)、[SRC-0295](../../SOURCES.md#src-0295)、[SRC-0289](../../SOURCES.md#src-0289)。
4. **任务收益与预测/评测保真分开**。Cosmos的pose-estimation生成成功、Ctrl-World的合成SFT改善、WorldGym/WorldEval的policy排名相关，均不能等价于SAC真实交互收益。建议只按未来已批准合同检查真实任务指标，并把模型指标作为诊断；这不新增评测条件。[SRC-0286](../../SOURCES.md#src-0286)、[SRC-0301](../../SOURCES.md#src-0301)、[SRC-0299](../../SOURCES.md#src-0299)、[SRC-0300](../../SOURCES.md#src-0300)。
5. **动作周期不能由生成FPS确定**。V-JEPA 2的4FPS训练数据对应4090约16s一次规划；NWM的4bit .1s只是估计；DayDreamer UR5 2Hz是受约束离散抓取动作。建议在已有性能职责内检查整个候选/模型/修正/SAC链的端到端耗时；不得将这些数值直接变成UR5周期、时延或工期承诺。[SRC-0284](../../SOURCES.md#src-0284)、[SRC-0285](../../SOURCES.md#src-0285)、[SRC-0294](../../SOURCES.md#src-0294)。
6. **延迟文献只在对应层次提供条件依据**。固定/随机延迟研究对旧观测的belief重建，不证明机械伺服响应滞后；ResidualRL采用Panda力矩遥操作且累计50ms符号有歧义。建议保留timestamp/采样时刻/到达时刻差别，若未来有已授权的实际问题再评估适用性；本轮不提议注入人为延迟、恢复旧VIO或修改控制层。[SRC-0302](../../SOURCES.md#src-0302)、[SRC-0303](../../SOURCES.md#src-0303)、[SRC-0304](../../SOURCES.md#src-0304)。
7. **公平性包括额外数据与计算**。Dreamer4离线数据、TD-MPC2多任务回放、VLA方法额外policy轨迹/预训练，不能算普通SAC同预算对照。建议任何未来选用都显式登记数据来源、WM准备、策略update与实际wall-time；不给本轮新增预算或阈值。[SRC-0274](../../SOURCES.md#src-0274)、[SRC-0287](../../SOURCES.md#src-0287)、[SRC-0295](../../SOURCES.md#src-0295)。

## 候选补读

仅由已读原始综述中的参考表定位，**未读这些论文原文 / 对具体方法属于二手线索**。列入清单不代表选定、启动补读或增加Task4实施范围；补读须用户授权。来源为manipulation综述§V.B/V.C及对应参考编号，[SRC-0307](../../SOURCES.md#src-0307)。
|候选（实际查到的书目信息）|为何可能更贴近|本轮证据深度|
|---|---|---|
|Q. Bu等，Closed-loop visuomotor control with generative expectation for robotic manipulation，NeurIPS 2024，[会议条目](https://openreview.net/forum?id=1ptdkwZbMG)，综述[69]|预测后果与闭环视觉动作，可能更接近执行前反馈|仅综述书目/分类，原文未读|
|H. Qi等，Inference-time enhancement of generative robot policies via predictive world modeling，IEEE RAL 11(5):5534–5541，2026，综述[84]；本轮未核DOI/原文链接|推理时预测与候选选择/优化，需核最后动作权限|仅综述书目/分类，原文未读|
|V. Kurtz、J. W. Burdick，Generative predictive control: Flow matching policies for dynamic and difficult-to-demonstrate tasks，ICRA 2026，综述[85]；本轮未核DOI/原文链接|生成策略与预测控制之间的接口；与上一条不同论文，不能混同标题|仅综述书目/分类，原文未读|
|G. Zhou、H. Pan、Y. LeCun、L. Pinto，DINO-WM: World models on pre-trained visual features enable zero-shot planning，ICML 2025，[正式论文](https://proceedings.mlr.press/v267/zhou25t.html)，综述[90]|预训练特征预测与规划，需核对SAC内部反馈能否类比|仅综述书目/分类，原文未读|

## 阅读与数值核查限制补记

- DreamerV3正文写预测T=16而表4列H=15；DayDreamer亦有正文16/附录15。笔记保留两处记法，本轮不替作者统一、推断控制周期或把其中一个设为FoReM值。
- 作者自述限制已在能定位的条目中注明“作者”；没有该标记的限制是本轮方法/平台适用性分析或原文实验负结果，不能当成作者逐字结论。未逐行验证论文证明，未运行代码或独立复现数表。
- 所读版本不保证与当前仓库默认分支完全对应；“公开官方代码”指作者入口，未核固定代码commit、许可证兼容性或执行完整性。未知开源状态保持未知。
- 文献指出的收益、延迟设定与硬件吞吐均不等于本项目事实；全文阅读也不等于取得原始实验数据。所有FoReM建议只保存在本项目级日志，没有写入任务协议。

## 文档核验

- 2026-10-14T11:28:19+08:00：35篇目/九字段/比较表35行逐项检查通过；34个PDF SHA256与所读版本标记核对（PDF打印版本时）；35个新增SRC均含模板11字段、正反链接；本日志本地链接与标题空行检查通过。
- SOURCES写入前字节快照与写入后前缀一致，旧条目未改；已有重复编号不修。PROGRESS只替换本项状态并追加交接；源码/配置/Task三文档未由本轮改动。文档检查不是独立学术复核，状态为review。
- 检查使用现有Python/文本提取/只读检索工具；过程副本在 `/tmp/forem-wm-literature-20261014-i2t1lcy5/`，该临时目录不是长期事实来源。长期证据为每篇固定版本URL、原文章节/表图和SOURCES中的PDF SHA256。未将PDF、代码、数据或构建产物加入Git。

## 交接（review）

- 目标/授权：用户指定35项原文阅读、九字段笔记、来源登记；仅文档。负责人Codex /root；接收方为用户或后续独立复核者，不自动派发Claude。
- 已读深度：主文全文精读6篇（Dreamer 4、DreamerV3、MBPO、DayDreamer、固定观测延迟 Dreamer、随机观测延迟 DA-Dreamer）；优先部分精读3篇（V-JEPA 2、TD-MPC2、TD-MPC），范围详见各条第1字段；其余25篇原始论文读摘要/方法/实验设置，Genie 3官方博客完整读取，4篇综述选读（这里“其余”含综述，不能称逐篇全文）。
- 未能获取：主清单无完全未取得原文的篇目。WMPO ICLR 2026正式PDF返回403，仅arXiv v1已读；会议稿一致性待核。Genie 3只是官方博客，未披露的架构/损失/数据/算力无法核验。
- 来源：新增 **SRC-0274–SRC-0308，共35条**，每篇一条；本轮读取前最大SRC-0273（开工最大268，期间他人追加269–273）。重复编号开工含0183–0190及0266，追加前0183–0190各2次；本轮没有修改任何旧条目或修编号。
- 改动文件：`forem/doc/agent_logs/project/20261014-codex-wm-rl-literature.md`、`forem/doc/SOURCES.md`、`forem/doc/PROGRESS.md`。SOURCES开工为untracked，本次首次入Git保留完整旧台账；PROGRESS计划通过临时Git索引只提交本项新增登记/交接（此行写入时尚未执行，提交结果以Git历史及本轮交付为准），既有其他修改留在工作区，其他文件原暂存状态保留。不会推送/合并。提交号在本轮聊天交付中报告，亦可用本日志的Git历史定位。
- 风险：World4RL表III BC均值与计数算术不一致；ResidualRL链路50ms累计有歧义；所有跨平台/跨预算对比保留限制。V-JEPA规划算力/动作标签、导航值与UR5频率不能直接迁移。部分频率/训练步数/硬件未报告或未核出，笔记明确未知。
- 剩余/下一步（待授权建议）：独立复核固定版本、数表、上述冲突与Task4条件映射；用户若同意再选择补读/方法评估。不新增实施、实验组、时延扫描、控制器或训练预算；不以本笔记改变现行任务验收。无本轮运行任务，研究下载/提取已退出，无须停止其他Agent进程。
