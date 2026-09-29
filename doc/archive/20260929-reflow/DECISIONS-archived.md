# 已归档决策（REFLOW-029，2026-09-29）

按用户“决策本来就删除了一些，你可以都整理一下”，从 [DECISIONS](../../DECISIONS.md) 原样移出以下条目（D61）：被取代的 D35、D38、D40、D43、D44，以及 PH2（全局模式闭环探索）已结束的实验判据 D47–D54、D56、D57。正文未改；相对链接已改写为从本目录出发。不具备当前指令效力。

## D35 — 投稿目标改为 CCF-A/B（2026-09-28，VENUE-028）

Agent：Claude Opus 5.5 /ybc。用户明确“我们想投一篇CCFA类的论文”，随后补充“CCFB也可以”。按 CCF 第七版（2026）目录（第三方整理页核对，官网 PDF 本机下载被拒，正式使用前须以 ccf.org.cn 为准），IROS 为 C 类，不满足该要求；ICRA 2027 已于 2026-09-16 截稿。因此 D30 及 AGENTS §0、RESEARCH_GOAL 中“以 IROS 2027 为目标”由本条取代，具体会议待用户在[候选](../../agent_logs/20260928-venue-ccf.md)中选定后再同步修改这两份文档。本条不改变 P0–P5 门槛、SAC 最终动作职责和当前“只引入 Husky”的范围；若选择 ML 会议路线而需扩展到多机器人/标准基准，属于范围变更，须用户另行确认。

## D38 — 最小闭环 = P2 + 简化 P4 一起实现与验收（2026-09-28，RUNPLAN-028）

Agent：Claude Opus 5.5 /ybc。用户确认“P2+简化P4一起做”。依据 LOOP-028：P2 单独使用时修正量只是 o_t 的函数；执行后用实际 a_t 与真实 o_(t+1) 更新世界模型，是闭环中引入新信息的部分。因此首个闭环研究验收改为：P2-MIN 前瞻修正 + 简化 P4（执行后一步预测器更新，每回合重置，首轮固定周期、不用 KL 触发）作为主方法 S4；仅 P2（S3）、同容量 adapter（S1）、历史条件 SAC（S2）和原 SAC（S0）为匹配对照。P4 不再依赖“P2 单独稳定、P3 固定”；P3、KL 触发、P1b/GRU 作为后续消融或扩展。P1 出口（D36 后补种子与独立 test）仍是前置条件，SAC 最终动作职责和“只引入 Husky”不变。失配来源、是否使用 Gazebo 仍待用户决定；本条不启动实验（用户：先不跑）。README/P2/P4 的依赖描述待实现开始前同步。

## D40 — 文档架构调整：ROADMAP 为唯一执行计划（2026-09-28，DOCS-028）

Agent：Claude Opus 5.5 /ybc。用户：“现有的流程组织架构太乱……你做一下调整”“没有用的就清理”。(1) 新建 [ROADMAP](../../ROADMAP.md) 为唯一执行计划：Stage0 前置验证 → G0 → F1 设计冻结 → Stage1 闭环筛查（S0–S4）→ G1（最迟11-20）→ Stage2 正式验证 → G2（约12-20）→ Stage3 写作；每阶段实验、对照、规模、预登记判据、种子登记见其 §4–§9。LOGIC-028 的 L1/L2 并入 R0-3/R0-4 判据，L4/L5/L7 列为 F1 必答项。各阶段规模（如 Stage1 3种子×100k、Stage2 5种子×500k、Stage2 正式测试 20000–20299）以 ROADMAP 为准，EVALUATION v1 中不同的数字不再适用于当前主线，其通用协议保留。P0–P5 仅作技术模块编号，不代表顺序。(2) README 重写为“维护中/参考/历史”三类；参考文档顶部加定位横幅；REVIEW、WORKFLOW_GUIDE、P0_ACCEPTANCE、P0_BASELINE、NODE01_DOCKER_ADMIN、P0/REMEDIATION_PLAN 移入 archive/20260928-docs028/（未删除）。(3) PROGRESS 顶部加看板，任务行不改内容，按“进行中/已完成/旧阶段行”分表。(4) 清理已退出的 11 个 mmhusky-p1-* 容器与 agent_logs/__pycache__；停止并清理被用户中止的 Stage0 执行残留，未完成失配代码备份为 patch 后还原（见 STAGE0-028 日志）。Stage0 从头重新执行。(5) 按用户“和现有决策冲突的旧决策也删除”，将 D02、D10、D14、D25、D26、D28、D29、D30 移至 archive/20260928-docs028/DECISIONS-superseded.md，D27 仅加测试集注释。AGENTS.md 的必读清单与 §4 阶段表尚未同步（本 Agent 读取该段被权限规则拒绝），待用户处理。

## D43 — 全量文档审查：过时路径与指令清理（2026-09-28，DOCREV-028）

Agent：Claude Opus 5.5 /ybc。用户：“审查一次全部的文档，把过时的目录修改，过时的指令删除或修改”。范围为维护中与参考文档；`archive/` 不改，已完成任务的历史日志正文不改写（只给作废的提示词加作废标注），DECISIONS 只追加。(1) AGENTS.md 重写 §0/§3–§6：ROADMAP 为唯一执行计划、单仓库与 GitHub 远端、node01 硬件/软件、当前阶段表；删除来源机器 §7/§8（2080 Ti、Python 3.8、`mmhusky-p0-ready`、pip 冲突）与已归档的 REVIEW.md 链接；§1/§2 原文保留。(2) ENV.md 重写为 node01 现行环境，删除来源机器环境、`cd /home/yanbochao/...`、`mm_husky:deps` 构建与“严格复现失败”等过时结论。(3) `docker/run.sh` 默认容器/镜像改为 `mmhusky-node01`/`mm_husky:node01`，`build` 默认用 `Dockerfile.node01`（旧 `Dockerfile` 路径保留为 `MM_DOCKERFILE=Dockerfile`）。(4) P0–P5 删除在当前环境不存在的“executing-plans 技能”指令；P1 文件清单由“拟创建”改为已实现；各参考文档中 D33/D29“待修复”的状态更新为 D34/D36 后的现状，RESEARCH_EXPERIMENTS 旧“下一步”计划删除并给出 B0–C2 与 S0–S4 的对应。(5) 6 份 09-22 P0 日志正文确认无副本，指向它们的跳转占位删除，引用处改为“正文缺失”标注。(6) Stage0 启动提示词更新为 v3（分支 `stage0-028` 提交、不 push；常驻容器可用），v2 作废。AGENTS/ENV/PROGRESS 审查前原文存于 `archive/20260928-docrev/`。不改变任何算法、评测协议或实验语义。

## D44 — 来源机器遗留文件与作废提示词移出现行目录（2026-09-28，DOCREV-028）

Agent：Claude Opus 5.5 /ybc。用户：“清理”。(1) `docker/Dockerfile`、`requirements-p0.txt`、`python-freeze.txt`、`dpkg-versions.txt`、`pip-check.txt` 及 `docker/validation/` 顶层与 `p0-ready/` 输出（来源机器 `mm_husky:p0-ready` 相关）`git mv` 至 `docker/legacy/`，附 README；`docker/validation/node01-20260922/`（本机验收证据）保留。`run.sh build` 只保留 `Dockerfile.node01` 路径，D43 中的 `MM_DOCKERFILE=Dockerfile` 选项随之取消。(2) 作废的 Stage0 提示词 handoff 与 v2 移入 `doc/archive/20260928-docrev/`，Stage0 日志中的链接同步更新。未删除任何文件内容；agent_logs 证据文件与 Stage0 正在使用的 patch/R0-1 脚本不动。archive 内快照的相对链接不再维护。

## D47 — R0-3b 探索性失配探针（2026-09-28，STAGE0-028，exploratory）

Agent：Claude Sonnet 5 /ybc。背景：R0-3 按 D45 判据不通过（15配置最大SR下降0.09，未达≥0.15）；收到跨会话协调指令 COORD-028（`doc/agent_logs/20260928-stage0-directive.md`，用户授权该会话协调），其只读复算与本任务`r03-analysis.json`一致，并建议在更强失配区间做探索性补充。**本条不修改、不替代 D45 判据，不作为 G0 R0-3 通过依据**，结果只供用户决定后续方向（备选方案B）参考。

**配置（5组，超出 D45 原登记的增益{0.6–1.4}×延迟{0–2}范围）**：延迟{5,10}步@增益1.0；增益{1.6,1.8}@延迟0；增益1.4+延迟5。每配置20回合，种子10000–10019（D45同名义种子子集，配对比较），policy-100k，`--ik-mode fixed --ik-iterations 100 --policy-mode deterministic`。报告：SR、perfect-success、有IK失败回合比例、collision>0回合比例、命令-执行差均值、`primary_reason`分布，与名义（同20种子子集）配对episode-bootstrap 95%CI。

**同时补充**：D45已登记的15配置全集，按 perfect-success（而非仅success）重算与名义的配对CI（`results/stage0-028-r03/r03-analysis-perfect.json`），作为诊断补充，不改变 D45 以 success 为主判据的既有判定（R0-3不通过）。是否改用 perfect-success 作主指标需用户另行决策（备选方案A），本条不预先采纳。

## D48 — R0-3c 更强失配扫描登记（2026-09-28，STAGE0-028，用户确认执行）

Agent：Claude Sonnet 5 /ybc。背景：G0首轮判定不通过后，用户经AskUserQuestion明确选择"都执行"COORD-028-2建议的R0-3c+R0-4b两批追加实验。R0-3b（D47，探索性，n=20）已提示更强失配下有显著信号，本条把范围扩大后按D45同等严格度正式重测。

**配置**：增益{0.6,1.0,1.4,1.6,1.8} × 延迟{0,5,10} 共15组（名义1.0/0**重新跑**，不复用D45已有的`gain1.0_delay0`结果，因为这15组要用同一批同种子完整重跑以保证跨组配对一致）。规模：每配置100回合，种子10000–10099，policy-100k，`--ik-mode fixed --ik-iterations 100 --policy-mode deterministic`；同种子跨配置配对，与D45相同方法（`bootstrap_ci`，episode级，10000次重采样，种子固定为0）。

**判据**：与D45相同——至少一个非名义配置SR相对名义下降≥0.15且配对CI上界<0；不因结果调整。诊断（次要）：perfect-success同款配对分析、有IK失败回合比例、collision>0回合比例、命令-执行差均值、`primary_reason`分布。

**产出用途**：按结果为F1提供training随机化范围（中度掉点档，供S0–S4训练时随机采样使用）与留出测试档（更强/范围外档，供Stage1/2评测但不参与训练随机化）建议，写入Stage0日志，不在本条自行冻结为最终F1决定（F1仍需用户确认后正式登记）。

**并发/资源纪律**（吸取此前两次事故教训）：总episode-worker并发≤72；每批启动前`free -g`确认无持续增长趋势；启动脚本沿用`doc/agent_logs/20260928-stage0-shard-eval.py`（固定迭代IK预算，并发只影响墙钟不影响正确性/确定性）。

## D49 — R0-4b 在线适应机制比较登记（2026-09-28，STAGE0-028，用户确认执行）

Agent：Claude Sonnet 5 /ybc。背景：R0-4（D45同批）显示当前"每k步全参数梯度更新"机制虽在7个条件下相对冻结统计显著更优，但挽回的残差仅占失配gap的0.57%~8.65%（多数<2%），效果量过小，S4很可能与S3（仅前瞻修正、无在线更新）区分不开。COORD-028-2建议在换用别的适应机制前先确认是否存在"实质挽回"的可能，避免Stage1开工后才发现S4本质等价于S3。用户已确认执行。

**范围声明**：这是在**已训练WM checkpoint之上做离线机制探测**，不改SAC/奖励/终止、不改WM训练协议、不引入新checkpoint训练；代码放在`scripts/`而非`scripts/wm/`内（沿用`residual_probe.py`已确立的规避`code_identity()`的做法）。这是Stage0范围内的诊断性探测（回答"当前WM能否被某种在线机制实质纠偏"），不是Stage1/F1的机制选型决定——若某变体达标，仍需用户在F1阶段正式登记该机制后才能写入Stage1的S4实现；若不达标，直接支持备选方案D（重审"在线适应"这条设计假设）的证据强度上升。

**数据**：复用R0-4已采的`gain1.0_delay0`（名义）与`gain1.4_delay0`（`results/stage0-028-r04/{gain1.0_delay0,gain1.4_delay0}/`）；新采`gain1.8_delay0`、`gain1.0_delay5`、`gain1.4_delay5` 各100回合，种子9600–9699，`p0_runner.py eval --save-observations --policy-mode stochastic --ik-mode fixed --ik-iterations 100`，policy-100k，与R0-4同协议（`doc/agent_logs/20260928-stage0-shard-eval.py`）。模型统一用`trainval-1000-r1`（seed11）action checkpoint，与R0-4一致，便于直接对比。

**协议**：与R0-4相同的"先预测后更新，只在未用于更新的后续步评估，每回合reset，随机种子固定"（`residual_probe.py`的`episode_errors`已实现，min_step=k过滤已修复）。

**变体**：
- V0 冻结（对照，R0-4已有）；copy（对照，R0-4已有）。
- V1 现有全参数梯度更新，取R0-4最佳lr=1e-5、k=1作参照（不重新扫描）。
- V2 只更新输出层（`MLPDynamics.net[-1]`，含weight+bias）：lr∈{1e-3,1e-2,1e-1}×k∈{1,5}，共6组合。
- V3 无梯度残差滑动平均修正：`pred_corrected = pred + ema_residual`，`ema_residual`在标准化特征空间逐维指数滑动平均更新（`ema = (1-α)*ema + α*(z_true_prev - pred_prev)`，用上一次实际观测到的残差，同样满足predict-then-update不作弊），α∈{0.05,0.2,0.5}；额外报告只作用于robot块（41维，map块保持冻结预测）的版本，共3+3=6组合。

**指标**：挽回比例 = (冻结残差 − 变体残差) / (该条件冻结残差 − 名义条件冻结残差)，total及robot/map分块分别报告；变体−冻结的配对episode-bootstrap CI（同R0-4方法）。

**判据（登记后不放宽）**：至少一个变体配置在≥2个强失配条件（从`gain1.4_delay0`、`gain1.8_delay0`、`gain1.4_delay5`中选）上挽回比例≥30%且配对CI上界<0；同时该变体在名义条件下"变体−冻结"配对差均值 ≤ 冻结名义残差的1%（不明显变差）。若无变体达标，如实报告并列出方向：残差摘要作为SAC/ψ输入、换失配类型、重审研究动机（备选方案C/D）。

## D50 — FOLLOWUP-028 A 线：结构化低维适应判据预登记（2026-09-28，运行前）

Agent：Claude Opus 5.5 /ybc（协调方，仅文档；实现交执行 Agent）。依据用户“两边都执行一下”与 [设计说明](../../agent_logs/20260928-followup-spec.md) §3。在 R0-4/R0-4b 已采 10 个条件（种子 9600–9699）上离线比较无梯度的低维适应：V4 增益标量（robot 块最小二乘，截断 [0,3]；另报 robot/map 各一标量）、V5 延迟选择（d∈{0,1,2,3,5,10}，只延迟底盘两维，初始取 0，残差 EMA α=0.2 选择）、V6（V5+V4），对照 V0 冻结。协议沿用 D49：先预测后更新、每回合重置、只在未用于更新的后续步评估、配对 episode-bootstrap。**通过判据（登记后不改）**：至少一个变体在 {gain1.4_delay0, gain1.8_delay0, gain1.4_delay5, gain1.0_delay5} 中 ≥2 个条件上挽回比例 ≥30% 且“变体−冻结”配对 CI 上界 <0，且名义条件下“变体−冻结”均值 ≤ 冻结名义残差的 1%。另报估计增益与真值的相关、所选延迟与真值一致率。解读边界：通过只说明低维辨识改善预测，不证明优于历史条件 SAC（S2）；延迟 5–10 步为压力档，非现实误差（LIT-MISMATCH-028）。

## D51 — FOLLOWUP-028 B 线：IK 失败前瞻判据预登记（2026-09-28，运行前）

Agent：同 D50；设计见 [设计说明](../../agent_logs/20260928-followup-spec.md) §4。**种子登记**：B1 用 R0-3/R0-3c 已有 10000–10099；B2 新采 1000–1999（确定性策略、名义条件，训练 1000–1699 / 验证 1700–1799 / 测试 1800–1999；当前世界模型仅用 0–999 训练，1000–1999 曾以随机策略采入 dataset-v2-10k 但未被当前模型使用）；B3 用 10000–10099。**B1 判据**：名义 `ik_limit` 失败种子在 8 个温和配置（增益∈[0.8,1.2]、延迟∈{0,1,2}，不含名义）中至少一次成功的比例 ≥0.30，且该比例减去“名义成功种子在同配置中至少一次失败”比例的 bootstrap 95% CI 下界 >0。**B2 判据**（测试集步级 AUROC，标签 H=5：fail[t..t+4] 中是否出现 IK 失败，仅在 fail[t−1]=0 的步评估；按测试回合 bootstrap 10000 次）：AUROC(C-wm)−AUROC(C-cur) ≥0.02 且 CI 下界 >0；AUROC(C-wm)−AUROC(C-hist) CI 下界 >0；AUROC(C-wm)−AUROC(C-geo) CI 下界 >0；三项全满足才通过。C-wm 的推演只用策略对预测特征的确定性动作，不得使用记录的未来动作。H=10 与数据效率曲线为次要报告。**B3**（探索性，不作通过依据）：六臂（none/wm/cur/hist/geo/random），风险超阈值时将末端参考速度维设为 −1；各分类器阈值在 B2 验证集上定为步级触发率 10%，random 臂触发概率取 wm 臂验证集触发率；看 B3 结果后不得调整。所有新行为默认关闭，关闭时输出逐字段不变。

## D52 — G0 后续两线均不利，转入前瞻场景筛选（2026-09-29，SCREEN-028）

Agent：Claude Opus 5.5 /ybc（协调方，仅文档）。依据 FOLLOWUP-028 核查（[日志](../../agent_logs/20260928-followup-pipeline.md)）：D50 不通过（结构化低维适应使预测变差）；D51-B1 不通过（失败/成功翻转比例无差别）；D51-B2 依点估计不通过（C-geo 0.979 ≥ C-wm 0.976，C-wm−C-cur 仅 +0.011，S4 超时未生成 CI）；B3 未运行且不补跑。结论：当前 simpleobstacle 设定下前瞻与在线适应均无空间。用户确认“按你推荐的方式走”：先对“感知延迟”（L 线）与“动态障碍”（D 线）做伤害测试 + 开卷上限测试，要求开卷信息明显优于历史信息，才进入方法实现。**决策规则（预登记）**：仅 L 通过 → 主线改为学习型世界模型感知延迟补偿；仅 D 通过 → 主线改为动态障碍前瞻（需 P1b）；两者都通过 → 取“开卷−历史”差距更大者为主线；都不通过 → 停止“闭环前瞻”论点，11-20 前由用户决定重新定位。最终由用户确认。ROADMAP 的 Stage1 暂停，待筛选结论后重写。设计见 [SCREEN 设计说明](../../agent_logs/20260929-screen-spec.md)。

## D53 — SCREEN-028 L 线（感知延迟）判据预登记（2026-09-29，运行前）

开关 `latency-v1`（默认关闭）：`--obs-latency-steps k`（完整观测延迟）、`--map-latency-steps k`（仅地图延迟）、`--obs-action-history k`（robot_state 追加最近 k 个已执行动作）；延迟只作用于策略输入，奖励/终止/碰撞/IK 用真实当前状态。**L1**：policy-100k 确定性，种子 10000–10099，配置 = 名义、全延迟 k∈{1,2,3,5}、仅地图 k∈{2,5}；判据：某配置 SR 相对名义下降 ≥0.15 且配对 CI 上界 <0；k≤3 达到为“现实档通过”，仅 k=5 为“压力档通过”。**L2**（仅 L1 通过时）：k_sel = 全延迟中最小通过 k，否则仅地图延迟中最小通过 k；训练 L-oracle（k=0）、L-stale（k_sel）、L-hist（k_sel + 最近 k_sel 个动作）各 2 个种子（11/22）×100k 步，预算末端 checkpoint，在各自输入条件下评测种子 10000–10099；判据：SR(L-oracle)−SR(L-hist) ≥0.10 且“训练种子×回合”分层 bootstrap 95% CI 下界 >0，并且 SR(L-oracle)−SR(L-stale) 的 CI 下界 >0。**L3**（探索性，不作通过依据）：policy-100k 在 k_sel（L1 不通过则 k=3）下比较 stale 与 wm-comp（世界模型用已执行动作把延迟特征推演到当前，送入 SAC 动作头），报告 SR 恢复比例与配对 CI。

## D54 — SCREEN-028 D 线（动态障碍）判据预登记（2026-09-29，运行前）

使用现有 `dynObstacle` 任务；开关 `dynmap-v1`（默认关闭）：`--dyn-freeze`（评测时障碍不动）、`--dyn-map-mode {current,future,past}`（策略输入地图中另叠加障碍 5 步后/前的位置，并集单通道；future 须复制障碍对象与随机数状态前推，不得改变真实障碍序列；碰撞与奖励用真实当前位置）。训练 D-std（current）、D-oracle（future）、D-hist（past）各 2 个种子（11/22）×100k 步，评测种子 10000–10099（本任务首次使用）。**D54-harm**：SR(D-std, 冻结)−SR(D-std, 移动) ≥0.15 且 CI 下界 >0。**D54-headroom**：SR(D-oracle)−SR(D-hist) ≥0.10 且 CI 下界 >0，并且 SR(D-oracle)−SR(D-std) 的 CI 下界 >0。两者都满足才通过。D-std 移动条件 SR <0.2 时结论标注“任务过难，谨慎解读”。D0 可行性不通过则 D 线终止并报告原因。

## D56 — 修订 D54：动态障碍线前瞻/历史时长由 5 步改为 20 步（2026-09-29，SCREEN-028，运行前）

Agent：Claude Opus 5.5 /ybc（协调方），用户同意（“我同意”）。依据 SCREEN-028 执行 Agent 的早期实测（[日志](../../agent_logs/20260929-screen-pipeline.md)“早期实测发现”第 4 条）：障碍直径 0.3 m、速度 0.10–0.15 m/s，5 步（0.5 s）内仅移动 5–7.5 cm（约 2–3 像素），D54 登记的 `future`/`past` 地图信息量过小，可能使 D 线因开卷过弱而出现假阴性。**修订**：`--dyn-map-mode future/past` 叠加的障碍位置改为 **20 步（2.0 s）后/前**（2 s 内位移约 20–30 cm，约一个障碍直径），`future` 与 `past` 保持对称；其余 D54 内容（训练臂、种子、D54-harm 与 D54-headroom 判据及阈值）不变。前推 20 步时障碍可能到达目标并重新采样目标，须用复制的障碍对象与随机数状态前推（执行 Agent 已确认 deepcopy 共享 memo 可与真实未来一致且不触碰真实 RNG），并以测试证明。本修订发生在任何 D 线数据产生之前，属于运行前预登记修订，不是看结果后调整。编号说明：D55 预留给 SCREEN-028 执行 Agent 的 `--replay-compact-maps` 决策。

## D57 — CEIL-028：SAC 上限摸底判据预登记（2026-09-29，运行前）

Agent：Claude Opus 5.5 /ybc（协调方，仅文档），用户确认（“那先做一个实验，看看能不能涨”“确认”）；SCREEN-028 已按用户要求停止（L1 不通过，D 线无结果）。设计见 [CEIL 设计说明](../../agent_logs/20260929-ceil-spec.md)。**依据**：`sac.py:45` 学习率按总预算指数衰减，policy-100k 在 10 万步已衰减到底，且续训协议记录 `total_steps`，故不续训，改为从零训练预算 300000 步、训练种子 11/22、其余配置同 policy-100k（可用 D55 `--replay-compact-maps`），每 5 万步存检查点并在种子 10000–10099 上确定性评测 100 回合（fixed100）；主结论只用 300k 预算末端检查点。简单策略（`--policy-override`，默认关闭）：random（均匀随机，回合种子派生）、mean（policy-100k 在 R0-3c 名义 100 回合动作的逐维均值）、slow-ee（policy-100k，第 0 维固定为 −1，探索性）。**判据**：C-learn = 两个 300k 末端检查点 SR 相对 policy-100k（0.70，同评测种子）提升 ≥0.10 且“训练种子×回合”分层 bootstrap 95% CI 下界 >0；C-policy = SR(policy-100k) − max(SR(random), SR(mean)) ≥ 0.30。**下一步规则**：两者通过 → 世界模型帮 SAC 学习（先做 IK 可行性辅助预测，比较学习曲线）；C-learn 不通过而 C-policy 通过 → 换任务（door/drawer 等）并先做同样摸底；两者都不通过 → 换任务；C-learn 通过而 C-policy 不通过 → 核查实验。最终方向由用户确认。
