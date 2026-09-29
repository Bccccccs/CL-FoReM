# 决策记录

整理：2026-09-29（REFLOW-029，D61）。**本文件只保留现行有效的决策**；被取代或所属阶段已结束的条目原文移入归档，编号不再复用，索引见下文“已归档条目”。新条目追加到文末，编号取当前最大值+1（写前重读）。阶段编号见 [ROADMAP](ROADMAP.md) §3（PH0–PH8）。

## 现行条目速查

| 主题 | 条目 |
|---|---|
| 基础约定 | D01、D03–D09、D11–D13（下表） |
| 环境与评测语义（PH0） | D15–D24（修复语义 v2、Gazebo 链路、复现口径、BioIK 固定预算 fixed100） |
| 世界模型（PH1） | D27 训练配置、D31 沿用资产与有界内存、D32 测试曝光、D33/D34 窗口修复与有界链路、D36 val 结果、D46 独立 test 种子与结果 |
| 投稿 | D37 IJCAI 2027 |
| 失配来源与可复用开关 | D39 注入失配 + Gazebo 自然失配（阶段安排按 D59）、D45 `mismatch-v1` 实现、D55 `--replay-compact-maps` 与评测 checkpoint 导出 |
| 仓库、环境与数据 | D41 工作区路径、D42 单仓库、D58 数据清理 |
| 当前主线 | **D59 非全局模式与 PH0–PH8 流程**、D60 PH3 诊断口径、D61 本次整理、**D62 PH4.1 预登记（r∈{3,5}，当晚训练）**、D63 开关实现选择、**D64 收敛检查（30 万步长训练）** |

## 基础约定

| ID | 决定 | 理由/边界 |
|---|---|---|
| D01 | 主代码固定在 `src/modulation_rl` | runtime 与手工副本仅作参考，逐项移植修复 |
| D03 | P0 analytical 与 Gazebo 分线 | 离线预测不依赖完整 Gazebo 场景；Gazebo 性能结论仍须单独验收 |
| D04 | 原始/修复后基线分开 | actor 梯度、动作变换和 bootstrap 修正会影响训练或评估语义 |
| D05 | P1a 使用固定编码器、一步确定性预测 | 先确认动作条件预测有用，避免表征坍塌与时序复杂性同时引入 |
| D06 | P1b 保留概率后验/先验与 GRU | 是完整时序迁移路线；需连续数据与 burn-in，不强塞入单步 replay |
| D07 | P2 最小版使用特征残差，初始输出为零 | 保留 SAC 最终动作职责，关闭开关恢复基线；不保证训练后关开关仍与原基线相同 |
| D08 | 前瞻策略用同 actor 的未修正分支 | 冻结先验只用于 prior-SAC 正则；两者不能混称 |
| D09 | 一致性正则默认权重为 0 | 是待检验设计，先避免压制有效修正；非论文监督损失的等价替换 |
| D11 | P4 默认逐 episode 重置 | 防止场景顺序污染测试；跨 episode 持续适应需单列协议 |
| D12 | P5 不自动启动 | 核心修正收益优先，RGB-D/语言是独立扩展 |
| D13 | 所有 Agent 通过 doc 交流 | 用户硬性要求，包含进度、证据、失败和交接 |


## 变更方式

新增决策记录需包含：日期、任务 ID、Agent、替代的决策 ID、证据、影响的阶段/协议、是否需要重跑基线。禁止通过覆盖旧记录隐藏研究路径变化。

论文原文：[SC²-WM](https://arxiv.org/html/2608.07548)。本项目提出的 GRU、残差接口和评测选择是迁移设计，不宣称逐模块复现。P1b 实施前须逐条建立公式到代码映射；原论文未明确的实现细节应标为本项目约定。

## 已归档条目

原文见 [archive/20260928-docs028/DECISIONS-superseded.md](archive/20260928-docs028/DECISIONS-superseded.md)（DOCS-028）与 [archive/20260929-reflow/DECISIONS-archived.md](archive/20260929-reflow/DECISIONS-archived.md)（REFLOW-029）。

| ID | 内容 | 归档原因 |
|---|---|---|
| D02、D10、D14、D25、D26、D28、D29、D30 | 早期 P0/P1 边界、P1a 旧结果与旧研究范围 | 与后续决策冲突（DOCS-028） |
| D35 | 投稿目标改为 CCF-A/B | 由 D37 具体化 |
| D38 | 最小闭环 = P2+简化P4，S0–S4 对比组 | 由 D59 取代（主方法由 G4 决定，对比组改名） |
| D40 | Stage0–3 执行计划与文档架构 | 由 D59 取代（PH0–PH8）；“ROADMAP 唯一执行计划”保留于 D59 |
| D43、D44 | 全量文档审查、来源机器遗留文件移出 | 一次性整理，结果已体现在现行文件中 |
| D47、D48、D49 | R0-3b/R0-3c 失配扫描、R0-4b 适应机制比较 | PH2 已结束；结果见 [Stage0 日志](agent_logs/20260928-stage0.md) |
| D50、D51、D52 | FOLLOWUP A/B 线判据、转入场景筛选 | PH2 已结束；结果见 [FOLLOWUP 日志](agent_logs/20260928-followup-pipeline.md) |
| D53、D54、D56 | SCREEN 感知延迟/动态障碍判据（`latency-v1`/`dynmap-v1` 开关语义也在其中） | PH2 已结束；复用这两个开关前先读原文 |
| D57 | CEIL SAC 上限摸底判据 | PH2 已结束；结果见 [CEIL 日志](agent_logs/20260929-ceil-pipeline.md) |

## 现行条目

## D15 — P0 修复语义 v2（2026-09-22，P0-RUN-022）

主目录修复 sample/predict 双 tanh 和密度缩放，旧权重仅 warm-start，正式结果重测。
普通 SAC actor 为 E[alpha logπ−Q]；prior_sac 固定 beta 为 E[alpha logπ−Q−beta log prior]，
TD target 同样含 −alpha logπ+beta log prior；prior_sac_legacy_alpha 则明确令 beta=alpha。
alpha 仅为熵温度并保持既有 0.35 缩放/0.05 下界策略。默认新入口使用普通 SAC。
MAX_CLOSE_STEPS 是现有目标附近任务失败条件，保留 terminal；外加总步数时限为 truncated。
此记录不声称新算法性能；所有结果必须注明 action/termination v2 与旧结果隔离。

## D16 — Gazebo 重力修复（2026-09-22，P0-RUN-022）

接触传感器宏 modulation_bumper.gazebo.xacro 隐含 turnGravityOff=true，导致 Husky
所有挂传感器的链接无重力。实测轮子 z≈0.32–0.39m、半径0.1651m，悬空转动。
保持其他惯量/接触/速度参数不变，仅服务试验启用链接重力后，原位移检查由
0.0115356m 失败变为 0.270553m 通过。正式修复改 turnGravityOff=false，须重启验证。
这是 P0 物理语义修正，旧 Gazebo 结果不可混比；analytical 动作/奖励未因本项改变。

## D17 — analytical 数值复现口径（2026-09-22，P0-RUN-022）

按 P0 文档“先定位或量化，再定义允许误差”执行：eval-a/b 严格轨迹哈希失败永久保留，
量化到 FP32 微小差异、离散结果相同。正式新一组复测前冻结 EVALUATION v1.1 误差界限，
用新产物 eval-c/d 验证，不能事后放宽。初始观测仍要求字节相同；后继只声称数值复现。

## D18 — BioIK 随机源与执行反变换（2026-09-22，P0-RUN-022）

c/d 未通过冻结的数值标准，不能放宽。查本地 BioIK lookupParam 默认从random_device
取种子且自动线程；P0新入口在创建环境前明确设定随机种子和单线程，参数进manifest。
这属于P0基线配置变化，训练/评估同配置重测。求解时间预算保持原值。
Gazebo 差动执行原函数直接抛“未实现”，按既有analytical积分（先转向再平移）补其反变换，
不变更analytical积分。数学回归覆盖正/反向、原地转与跨±π。

## D19 — Gazebo 控制与观测（2026-09-22，P0-RUN-022）

实测20步虽然可返回，但原物理路径没有等待控制周期；恢复Gazebo命令后等待dt_exec，
再读实际状态。P0物理入口固定execute_style=direct、perception_style=all（原base分支使用
期望关节值，不能作为实际运动验收）。Robotiq命令原为不存在的两个finger_joint，改为
控制器声明的gripper_finger1_joint，采用本地官方driver相同宽度→角度公式。
均仅影响Gazebo/真实控制入口，analytical不等待、不改奖励；物理性能须重测。

## D20 — Gazebo 观测链路缺口（2026-09-22，P0-RUN-022）

任务场景实测/front/scan无publisher，旧costmap不能证明传感器感知。新增主包P0显式ray
传感器wrapper（720束、10Hz、0.05–10m、前方270度），launch开关默认false；docker
Gazebo入口显式开启，与analytical观测尺度保持120×120。没有添加RGB或语言。
任务reset另复现costmap全图只在首次订阅发送，诊断订阅保留时重新建图超时；启用
always_send_full_costmap仅改变消息发布方式，不修改占据数值。新物理基线需据此单列。

## D21：评测回合进程隔离与物理冷启动（2026-09-22）

双次有序manifest通过但倒序20回合 seed10010 状态差1.2003e-5超v1.1；两个单独回合探针通过不能替代完整验证。BioIK内部随机流持续推进，env.seed不重置它。决定默认每评测回合新进程构建环境，使同一回合不依赖前序求解调用；保留失败证据，不扩大容差。训练不每回合重建，checkpoint仍部分恢复。子进程仅允许顺序访问同一Gazebo世界，禁止与训练并发；Gazebo不承诺数值复现。

Gazebo零关节角spawn在重力下机械臂下落，首次大幅复位轨迹失败；小幅controller probe成功、预热后任务rollout有效。增加默认关闭p0_start_pose，Docker入口显式使用既有robot_config中的初始臂关节值spawn，待冷启动复测。不修改控制器容差。

## D22：P0文档集中与可选BioIK诊断插件（2026-09-22，P0-CLOSE-022）

用户明确要求启动解决剩余问题并集中P0文档。正式P0正文迁到doc/P0；共享协议仍在doc根，旧路径保留跳转。本轮日志doc/P0/logs/20260922-p0-closure.md。

在权威modulation_rl内生成独立modulation_p0_bioik插件，引用当前bio_ik源码但不编辑/覆盖其源文件或已有库；重命名插件和并行调度类，复用原query-options registry，保留BSD许可。插件显式选择才启用，固定预算环境变量默认0仍为原墙钟逻辑。诊断每次实际step/迭代、耗时、退出类型；固定预算只允许单线程，保留成功提前退出，替换所有外层墙钟停止条件，不改目标函数/梯度solver。先验证诊断与原行为一致，再冻结预算与版本重测。该设计未经实测前不宣称确定性通过。

## D23 — node01 从头构建环境（ENV-AUDIT-022）

2026-09-22，用户明确旧镜像无法迁移，并授权 Python3.10 适配及 ROS Python 绑定重编。新宿主为 Blackwell，拟使用支持该架构的 PyTorch/CUDA，版本需通过完整环境回归；原 Noetic 容器路线保留，Python3.8 限制仅对本次迁移被新指令替代。旧环境与新依赖下的结果分开记录，正式研究基线须在新环境重测。当前未完成构建或 GPU 验收。

## D24 — BioIK 固定迭代预算取值与因果检验协议（2026-09-23，P0-NODE01-023）

Agent：Claude P0执行人 /ybc。补充 D22，不替代。源码审查（bio_ik/src）：默认 `bio2_memetic`、threads=1 时，影响停止条件的仅 `ik_parallel.h` 两处 `WallTime<timeout` 判断；`ik_cppoptlib` 墙钟停止仅在 cppoptlib 模式、profiler 的 rand/WallTime 仅在 profiler=true 时触发，本项目均不使用；求解器 RNG 为构造时播种的 `minstd_rand`（已由 D21 每回合新进程隔离）。诊断实测：来源机器 2 回合 243 次 IK 调用、node01 2 回合 207 次调用 **全部**以 10ms 墙钟预算退出、无一次提前成功退出，迭代数分别约 91 与 103（`results/p0-closure-20260922/diagnostic-b`、`results/p0-node01-20260923/diag-legacy-wall`）。故 IK 结果直接取决于 10ms 内 CPU 能完成的迭代数，是机器/负载依赖的。

决定：固定预算模式 `--ik-mode fixed --ik-iterations 100`（每迭代 4 次 solver step，与原循环计数一致），语义命名 `p0-ik-budget-v1`；100 取 node01 名义 10ms 中位数附近，在因果检验前冻结，不根据复现结果调整。原 legacy 墙钟模式保持默认、不变。因果检验：同 checkpoint/种子在 wall 与 fixed 模式下，分别无负载与人为 CPU 超订负载运行，按 EVALUATION v1.1 冻结容差比较；预期 wall 模式受负载改变迭代数，fixed 模式不受影响。固定预算属于 IK 语义变化：用它训练/评测的基线须单独标注，不与 wall 模式结果混比；受影响的 SAC/prior-SAC 工程基线在该语义下重训重测。

## D27 — P1a v2 训练配置冻结（train/val 诊断后，测试前，2026-09-24，P1-A）

诊断过程（仅用 dataset-v1 的 train/val，未再碰 test）：默认配置（lr1e-3、hidden 256×256、无权重衰减）两模型均于 epoch1 验证最优后过拟合发散；lr 降到 1e-4 仍在 epoch1 最优（说明不是单纯学习率问题）；排查特征数值范围无异常离群值；扫描发现 robot_state 41 维中有 4 维（21/22/34/35）方差大且与动作中度到强相关（corr .57–.85，物理上合理，如 ee 速度反馈随命令速度变化），另 4 维（37–40）在当前数据中恒定。

**冻结配置 v2**（用于唯一一次最终测试）：hidden=(64,)、lr=3e-4、weight_decay=1e-3、batch=512、patience=20（从诊断的30略降）、max epoch=200，其余不变。该配置在 val 上两模型均明显优于复制基线（标准化误差 .300→约.187，降约37%），但 action 相对 no_action 在 val 上无明显优势（仍需最终配对检验判断）。此为唯一将用于最终测试评测的配置，此后不再根据测试结果调整超参数。

**新测试集**（2026-09-28注：该集合已被 dataset-v2-10k 训练集包含，不再是未见测试，见D32与ROADMAP §9；本条训练配置仍为D36所用）：seeds 9100–9199（全新、此前未用于任何采集/训练/评测）。原 test seeds 9000–9099（D26）继续标记为探索性，不参与最终判据。

## D31 — 沿用资产与现有内存内修复（2026-09-28，RESEARCH-028）

Agent：Codex /root。用户明确“现有可以沿用的就继续用”，并要求上次内存爆炸的合理解决方案。沿用现有Husky/SAC、planner/IK/controller、数据产物、训练/评测入口及doc文档；不建立另一套研究系统。D29问题按完整数据→编码→窗口→训练/验证/评测链路处理，首选固定encoder的有界特征缓存，而不是只缩batch或增加swap；具体容量、文件、预算和验证在P1_MEMORY_PLAN。预算尚未实测，方案尚未实现。只改变存储/批处理的部分应验证语义一致；独立发现的索引正确性问题另列D33，不能用“纯内存优化”掩盖其影响。主包当前实际路径/home/ybc/projects/mm_husky_ws/src/modulation_rl，node01环境使用D23–D25及ENV，不套用来源机器11GB显存限制。

## D32 — 扩量数据跨版本测试曝光（2026-09-28，RESEARCH-028-EXP）

Agent：Codex /root，依据experiments独立审计。dataset-v2-10k的train seeds0–9599包含旧test9000–9099、9100–9199，逐条manifest分片SHA相同（共200）；也包含旧val8000–8099的100条。同一数据集当前train/val/test互斥并不保证跨版本隔离。旧数据保留可复用，未来扩量模型不得再用这些回合作为未见测试。后续需冻结跨版本曝光登记、新train/val/test身份和布局去重，再进行正式评估；不凭不同manifest文件哈希认定独立性。D28历史模型训练集没有因为后续扩量而追溯变化；但其窗口索引正确性由D33独立审查。审计证据见RESEARCH_EXPERIMENTS及20260928-research-experiments日志。未执行新训练或测试。

## D33 — P1窗口时间索引缺陷与历史结论降级（2026-09-28，RESEARCH-028）

Agent：Codex /root发现，/root/experiments独立复核。主包2a1348a的`wm/train_offline.py:29–35`中，`window_tensors`取得`e,t`，但观测与动作索引只用episode offset加0..k，漏掉t。同一episode所有窗口因而重复其开头；训练、evaluate_prediction及val_probe共用此函数。独立CPU NumPy最小probe中，窗口(0,0)/(0,1)/(0,2)均返回观测[0,1]，正确应分别[0,1]/[1,2]/[2,3]；另一个episode也复现。命令与输出见20260928-research-experiments日志。测试原覆盖EpisodeDataset.gather的t偏移，但未覆盖训练实际调用的window_tensors。

D26–D28数值及所有产物原样保留，**降级为受采样索引缺陷影响的历史输出，不再作为全轨迹动作预测有效性、无效性或P1a出口的可信判据**。此前以其解释数据不足/递归误差的研究判断待重验；本条比D28“最终判定”和D29“评测不受影响”的早期判断更新。此缺陷不同于D32跨版本测试曝光，后者没有追溯改变旧训练集。P0 SAC训练/评测不调用这个WM窗口函数，本次不据此撤销P0验收。

后续先在小型非恒定轨迹上修复t对齐并覆盖k=1/5、episode边界、动作/dt与末帧，再完成有界内存重构。新实现需相对独立正确参考验证，不能把旧错误曲线当golden。受影响预测器需重训、验证、重新登记未曝光测试协议后重测；不覆盖旧目录，不因当前结论降级而放行P2。本轮只完成诊断和方案，未修算法。

## D34 — P1正确窗口与有界特征链路（2026-09-28，P1-FIX-028）

Agent：Codex /root。落实D31/D33，沿用原NPZ、固定encoder、1041维FP32特征、MLP、block-MSE与Adam，不改变SAC、奖励、终止或IK。真实训练/验证/evaluate/val_probe共用WindowSource，观测obs_offset[e]+t+(0..k)、动作/dt act_offset[e]+t+(0..k−1)。不完整末帧和子目标排除开关保持原规则；全局均匀转移shuffle保持numpy RNG与顺序。修复t会改变有效监督分布与评测目标，**属于正确性语义修复，不是纯性能优化**；旧P1 checkpoint/报告原样保留，正式评测入口拒绝D33旧语义模型，必须重训。

存储改动：manifest仅读取轻量元数据/动作索引，逐回合校验和解压（预先拒绝解压量>256MiB），按128帧编码直接写≤128MiB未压缩NPY块。压缩NPZ不当作mmap。FeatureCache进程范围合计≤4个映射/512MiB，无worker/预取；batch拥有独立内存后才能淘汰映射。缓存绑定manifest与分片SHA、encoder SHA、wm代码及实际CNN定义代码、FP32格式/顺序/维度/split与源语义；完成标记+原子目录rename，损坏或未完成正式缓存拒绝，.partial中断产物不冒充完整缓存；原NPZ不覆盖。评测同时检查checkpoint特征代码身份。

归约/复现变化分别记录：训练集每个观测（含末帧）只计一次，ddof=0及std<1e-3→1规则保持；统计用FP64稳定合并、落盘FP32，数值归约不要求复现旧FP32全集误差。模型构造**之前**固定seed，不能通过训练函数内部重新设seed修复初始权重。批量loss按样本数加权，研究评测仍逐episode聚合再配对bootstrap（bootstrap也分块）。val_probe从checkpoint读取hidden与normalizer，有模型时不加载train拟合统计。

独立CPU正确参考的同权重/同样本序更新逐张量一致；node01完整Python测试59项通过（日志[任务记录](agent_logs/20260928-p1-fix.md)）。独立审查发现CNN身份、全局映射上限及manifest seed校验三个问题，均已RED→GREEN处理。100级资源验证通过，1000/9600级此时仍待实测；以任务日志后续最终证据为准。本工程修复不代表P1研究出口，不放行P2。下一轮仅1000回合train/val重训诊断；D32旧test9000–9199与旧val8000–8099的扩量曝光保留，不再用作未见test。

D34完成增补（2026-09-28 10:42 +08）：最终65项测试及100→1000→9600有限三级资源、GPU原始切片参考、SIGINT保留epoch checkpoint与两轮特征/参数一致验证均通过，P1-FIX-028工程任务done。缓存身份进一步绑定数值后端/版本/TF32/encoding batch，统一使用原训练deterministic配置；TF32训练配置继承且FP32存储不变。每epoch原子latest checkpoint和中止标记已实现；不声称精确断点恢复。M5与正式研究出口仍待验收，详见任务记录。

## D36 — 修复后1000回合正式train/val诊断（2026-09-28，P1-RETRAIN-028）

按用户明确授权执行D27/D34协议：train seeds0–999/val9600–9899、seed11、hidden64/lr3e-4/wd1e-3/batch512/max200epoch/patience20，无max-train-batches。没有修改训练算法或控制语义。无动作86epoch/best66/40678batch；动作107epoch/best87/50611batch，均完整epoch并正常早停。

300val逐回合等权标准化total：一步copy0.253411/no_action0.173332/action0.167075，五步copy0.492552/no_action0.405974/action0.389825。action相对copy改善34.07%/20.86%，相对no_action改善3.61%/3.98%；四组配对episode-bootstrap95%CI均负。全部回合纳入，包括高误差9881和五步唯一略差于no_action的9699。完整结果见[报告](agent_logs/20260928-p1-retrain-report.md)。训练+评测1031.71s；RSS3.029GiB/cgroup3.032GiB/GPU compute合计1482MiB/task swap0/宿主swap增量0，16GiB/no-swap硬隔离通过。65测试复跑通过；best-val重评与最佳曲线完全一致。

解释边界：这是单训练seed、用于早停的验证集上的P1a初步预测证据。没有独立最终test或跨seed稳定结论，不将CI视为包含选型与训练seed变化。原采集初始观测与floorplan图像精确hash跨split无交集，但近重复场景/场景族隔离未验证。本轮不使用旧test，不扩大9600，不进入P2，不声明闭环控制改善。建议先保持配置验证seed22/33并完善未曝光独立test协议（尚未执行）。P1研究出口review；P2–P5保持blocked。无精确resume CLI，latest包含完整epoch状态不等于支持精确续训。

## D37 — 暂定投稿目标 IJCAI 2027（2026-09-28，VENUE-028）

Agent：Claude Opus 5.5 /ybc。用户要求“今年底投、明年初截稿”，并决定“暂时按IJCAI 2027做准备”。IJCAI 在 CCF 2026 为 B 类；2027 截稿按历年规律约为1月中旬，官方 CFP 未发布，发布后须核对日期、页数、摘要预注册与双投政策。IJCAI 与 ICML 2027 时间重叠，同一论文只投其一。按只计实验时间的倒排：10月中前完成P1出口、最小闭环与差异来源设置及100k筛查；约2026-11-20为去留点，届时核心闭环无正结果则放弃1月会议、改投 NeurIPS 2027；约12-20冻结结果后写作。已同步修改 AGENTS §0、RESEARCH_GOAL、README 的目标描述。本条不改变 P0–P5 门槛、SAC 最终动作职责和“只引入 Husky”范围；闭环阶段顺序（P2+简化P4 合并为最小闭环）与差异来源仍待用户决定（见 LOOP-028）。

## D39 — 失配来源：analytical 注入执行失配 + Gazebo 自然失配（2026-09-28，RUNPLAN-028）

Agent：Claude Opus 5.5 /ybc。用户决定“注入失配加Gazebo一起用”。分工：(1) analytical 中新增版本化、默认关闭的系统性执行失配开关（每回合底盘速度增益、动作延迟步数），用于训练时随机化和受控主实验（可复现、可画强度-效果曲线）；关闭时必须与现基线逐元素一致。现有 `transition_noise_base` 为零均值噪声，保留但不作为可适应失配。(2) Gazebo 作为“analytical 训练→Gazebo 执行”的自然失配评测，不在 Gazebo 训练。Gazebo 进入正式评测前须先在本文件选定实时方案（P0 日志 A–D），并对齐控制周期（训练 TIME_STEP_TRAIN=0.1s，Gazebo 当前 time_step 0.02s）与回合时长；此前 4 个 Gazebo 回合使用 2000 步策略，不作为可用性结论。未见布局（需解除 map.py:837 间距硬编码）与 dynobstacle 留作泛化备选。两项均属环境语义扩展，实现时单列版本与测试。本条不启动实验。

## D41 — 工作区改名为 CL-FoReM，常驻容器按新路径重建（2026-09-28，PATHSYNC-028）

Agent：Claude Opus 5.5 /ybc。工作区于约 15:53 由 `/home/ybc/projects/mm_husky_ws` 改名为 `/home/ybc/projects/CL-FoReM`（内容不变）。用户要求“同步一下路径，容器也重新挂载”。(1) 宿主路径以 `/home/ybc/projects/CL-FoReM` 为准；**容器内挂载点仍为 `/root/mm_husky_ws`**，devel、runner、launch 脚本和 docker/ 下的容器内路径不改。D31 等历史条目及已完成任务日志/证据 JSON 中的旧宿主路径是当时实测记录，不改写，按新路径理解。AGENTS §0/§3、ENV 已同步。(2) `mmhusky-node01`、`mmhusky-node01-gz` 用同一镜像 `mm_husky:node01`（`sha256:e674db49…c430`）与原参数（bridge、nvidia runtime、shm 8g、无内存限制）经 `docker/run.sh up` 重建，仅挂载源改为新路径；重建前两容器仅有遗留 analytical launch 与 Xvfb、可写层只有 NVIDIA 注入和缓存。重建后 CUDA、train-smoke、analytical 20 步、Gazebo 启动检查均通过，证据见 [PATHSYNC-028 日志](agent_logs/20260928-path-sync.md)。本条不改变任何算法、评测协议或实验语义。

## D42 — src/modulation_rl 并入根仓库形成单仓库 CL-FoReM（2026-09-28，PATHSYNC-028）

Agent：Claude Opus 5.5 /ybc。用户选择“合并为单仓库”、GitHub 私有仓库。(1) 先在原子仓库 `p0-node01` 分支把 P1-FIX-028 此前未提交的改动原样提交为 `06c0ee1`（wm/data、encoder、evaluate_prediction、train_offline、val_probe、cache、streaming 测试、wm_resource_check）；根仓库待提交的 doc/docker/AGENTS/ENV 提交为 `9293083`。(2) 原 `.git` 移至 `/home/ybc/projects/CL-FoReM-backups/modulation_rl-dotgit-20260928`，另有全引用镜像 `modulation_rl-20260928.git`；根 `.gitignore` 去掉 `/src/modulation_rl/`，以 `merge -s ours --allow-unrelated-histories` + `read-tree --prefix=src/modulation_rl/` 合并为 `ac8d686`，工作区文件未变动。文档引用的 `1ccedd0/68b8d0b/b23aa39/2a1348a` 仍可在本仓库解析；注意 `git log -- src/modulation_rl/...` 不会跨越 subtree 前缀追溯旧提交，查旧历史直接按哈希。(3) 溯源影响：`p0_runner.provenance` 对原子仓库路径将记录 `git unavailable`（有异常兜底），根仓库条目已覆盖全部代码；`wm_resource_check.py` 的 `git_head` 改为读根仓库（原写法会因 .git 不存在直接崩溃），仍用显式 `--git-dir` 以避开容器内 safe.directory。不改变任何算法、评测或实验语义。其他第三方 ROS 包仍为独立仓库。(4) 远端：用户创建 GitHub 私有仓库，根仓库 origin = `git@github.com:Bccccccs/CL-FoReM.git`，首推 `7890c80`。

## D45 — mismatch-v1 实现与 M/R0-3 判据登记（2026-09-28，STAGE0-028）

Agent：Claude Sonnet 5 /ybc。按 ROADMAP §4 M 行与 v3 提示词实现失配开关：`scripts/modulation/envs/robotenv.py` 新增 `base_vel_gain`（固定）、`base_vel_gain_range`（每回合从独立 `_mismatch_rng` 采样，不消耗 `self.np_random`）、`action_delay_steps`（仅底盘命令，`deque` 实现，仅在 `_apply_execution_mismatch` 中作用，臂/torso 不受影响）。执行顺序：现有噪声+`apply_action_exec`（含加速度裁剪）→ `_prev_base_actions_scaled` 记录裁剪后的**命令值**（非执行值，保证下一步加速度裁剪连续性与开关状态无关）→ 延迟队列 → 增益 → `_calculate_base_command`。`_mismatch_enabled = gain!=1.0 or gain_range is not None or delay_steps!=0`；关闭（默认或显式默认值）时 `robot_info` 不新增 `mismatch_*` 键，`p0_runner.py` 的 `episodes.jsonl`/`trajectory.npz` 相应不新增字段（由 `if mismatch_cmd:` 等门控，非独立开关标志，避免与上一次尝试同类问题）。`modulation/utils.py:create_env`、`p0_runner.py`（CLI `--base-vel-gain`/`--base-vel-gain-range`/`--action-delay-steps`，`episode_command` 透传给 per-episode worker 子进程）、`collect_rollouts.py`（同参数透传）随之更新；`config['mismatch_semantics']='mismatch-v1'` 仅在启用时写入 manifest（provenance 层面的 config/arguments 字段始终包含默认值，不算作评测输出新增字段）。

新增单元测试 `scripts/tests/test_robotenv_mismatch.py`（15项，覆盖恒等默认、增益/延迟数值、跨回合重置、独立 RNG 派生与 CLI 校验），容器内 `python3 -m pytest tests/ -q` 全部 80 项通过（65 项 D34 基线 + 15 项新增）。发现并记录一个预先存在、与本次改动无关的环境现象：`from modulation.envs.robotenv import RobotEnv` 作为进程内首个原生扩展导入会抛 `std::bad_cast`（在未改动的 `robotenv.py` 上用 `git stash` 复现同样崩溃），先 `import modulation.utils`（真实入口 `p0_runner.py`/`main.py` 的实际导入顺序）可规避；测试文件按此顺序导入并在注释中记录，未改动任何生产代码来"修复"它，与 ENV.md §4 "已知现象"同类、不视为阻断项。

固定 IK 回归（policy-100k，种子10000–10019，`--ik-mode fixed --ik-iterations 100`，确定性；ROADMAP规格写10000–10099，本轮按D24既有先例20回合一批实测，结果见下）：与 pre-mismatch 基线（`git stash` 还原后跑出的 baseline）及本分支代码下"不带参数"、"显式默认值"（`--base-vel-gain 1.0 --action-delay-steps 0`）三份各跑一遍，比较 `trajectory_sha256`/`states`/`actions`/`base_xy`/`success`/`primary_reason`/`ik_count`/`collision_count`（不比较 `wall_seconds`/`control_seconds` 等非确定性计时字段）。**结果：PASS**——20个种子×2个对比（无参数、显式默认值）共40组，所有登记字段与轨迹 npz 数组（`base_xy`/`states`/`actions`）逐元素相同，且两份运行的 `episodes.jsonl`/npz 均未出现任何 `mismatch_*` 键（校验脚本 `results/stage0-028-m-regression/compare.py`，产物 `results/stage0-028-m-regression/{baseline,no-args,explicit-defaults}/`）。**M 通过**。

事故记录：R0-4 的 `wm/residual_probe.py` 编写与 `wm/data.py` 修改在 R0-1（s22/s33 WM 补训练）后台运行期间落盘，触发 `wm/cache.py:code_identity()`（对 `scripts/wm/*.py` glob 取 sha256、写入 checkpoint）身份校验失败，导致 s33 的 `prediction` 阶段崩溃（s22 当时仍在训练未受影响）。已回滚 `wm/data.py`、移出 `residual_probe.py`/其测试到会话外，清理 s33 不完整产物并重新后台启动；R0-4 代码改动将在 R0-1 完全跑完后重新应用。详见 [Stage0 日志](agent_logs/20260928-stage0.md) 的事故记录段。教训：R0-1（或任何调用 `wm/train_offline.py`/`evaluate_prediction.py` 的后台任务）运行期间不改动 `scripts/wm/*.py`、`model.py`、`modulation/models/mapencoder.py`。

**R0-3 判据预登记（运行前）**：配置 = 增益{0.6,0.8,1.0,1.2,1.4} × 延迟{0,1,2} 共15组（名义=增益1.0/延迟0，即 M 关闭状态）；规模 = 每配置100回合，种子10000–10099，policy-100k checkpoint，`--ik-mode fixed --ik-iterations 100 --policy-mode deterministic`；同种子跨配置配对。通过判据：至少一个非名义配置的 SR（`success`）相对名义下降 ≥0.15，且该配置与名义的配对 episode-bootstrap 95% CI 上界 <0（`evaluate_prediction.py` 的 `bootstrap_ci` 同款 episode-level bootstrap，10000次重采样，seed固定）。判据登记后不因结果不理想而放宽。诊断记录（区分失败原因，LOGIC L1，不要求严格单调）：`mismatch_cmd_exec_mean_abs_diff/max`（底盘命令-执行差，仅失配开启时存在）作为底盘跟踪代理；`subtasks_completed`/`subtasks_total`/`trajectory_length_m`作为参考进度代理；`primary_reason`/`reasons`/`failure_distribution`/`ik_count`/`collision_count`按配置分布，及每回合 `episode-*-tail.json`（末50步 `dist_to_desired`/`rot_dist_to_desired`/`kin_failure` 时间序列）作为 IK 失败前兆；均为已有字段的分析组合，未新增底盘/末端专用埋点。

## D46 — P1 独立 test v1 种子曝光审计与协议登记（2026-09-28，STAGE0-028 R0-2）

Agent：Claude Sonnet 5 /ybc。按 ROADMAP §4 R0-2 与 v3 提示词“先审计种子 9901–9999 在 `results/` 全部 manifest 和 doc 中是否被用过”执行。审计方法：(1) 解析 `results/p1-retrain-20260928/protocol-1000/dataset.json` 的 `train_seeds`/`val_seeds`/`episodes[].seed`，与目标集合 `{9901..9999}` 求交，结果为空。(2) 对 `results/` 全树 `*.json`/`*.jsonl` 用正则 `"seed":\s*99[0-9][1-9]|"seed":\s*99[1-9][0-9]` 搜索，唯一命中的历史占位种子是 9900（`results/p1a-20260923/dataset-v2-10k/test-00/`），不在 9901–9999 范围内。(3) 核对 `doc/RESEARCH_EXPERIMENTS.md`（D32审计正文）：dataset-v1 test=9000–9099，dataset-freshtest test=9100–9199（D28所用），dataset-v2-10k train=0–9599（含旧val8000–8099、旧test9000–9099/9100–9199）、val=9600–9899、test=9900（占位单回合，不作判据）。三处均未触及 9901–9999。**结论：种子 9901–9999 从未被用于任何采集、训练或评测，可登记为 P1 独立 test v1。**

**协议登记**：种子 9901–9999（99个）；采集协议与 protocol-1000 训练数据同款（`p0_runner.py eval --save-observations --policy-mode stochastic --ik-mode fixed --ik-iterations 100`，checkpoint policy-100k）；特征缓存用独立目录 `results/stage0-028-r02/feature-cache`（不复用 protocol-1000 的 train/val 缓存目录，避免身份混淆，但复用同一 `wm/cache.py:FeatureCache` 有界实现）；对种子11/22/33各自训练出的 action/no_action 两模型分别跑 `wm/evaluate_prediction.py --split test`（因非 train/val/test 三分 manifest，需按分片重命名 episodes 的 `split` 字段为 `test`，或用等价的手工单一 split 采集清单，采集时直接以 `--test 9901:10000` 传入而不使用 `--train`/`--val` 的占位区间，避免像 R0-4 那样借用其他已登记区间）。判据（ROADMAP§4 R0-2，不因结果不理想而放宽）：3个种子的 action 模型一步预测相对 copy、no_action 两对照的配对 CI 上界都 <0；五步如实报告（不要求同样通过）。执行依赖 R0-1（s22/s33 训练完成）；本条只完成审计与协议登记，采集与评测尚未执行。

实际执行更新（约17:15）：采集用 `doc/agent_logs/20260928-stage0-shard-eval.py --seeds 9901:10000 --shards 6 --policy-mode stochastic --save-observations`（直接单一区间，未借用 train/val 占位区间，比登记时设想的更简洁），manifest 由新写的 `doc/agent_logs/20260928-stage0-build-manifest.py --split test` 转换为 `wm/data.py:EpisodeDataset.from_manifest` 可读的 `dataset.json` schema（与 `collect_rollouts.py` 同字段：`split`/`seed`/`path`/`sha256`/`usable`/`complete`/`terminated`/`truncated`），复用 `wm/data.py:load_episode` 做同款校验。99回合全部usable。

**结果（约17:42）**：`wm/evaluate_prediction.py --split test` 对种子11/22/33三个action/no_action模型对分别跑完（99回合，59回合success）。一步预测：三个种子的action相对copy配对CI均为`[-0.088,-0.084]`附近（全负）、相对no_action配对CI均为`[-0.0069,-0.0056]`附近（全负）；五步预测同样三个种子相对copy、no_action的CI也全负（约`[-0.10,-0.091]`与`[-0.018,-0.013]`）。**R0-2 通过**（三种子一步、五步对两对照的配对CI上界均<0，五步按登记不要求也通过）。产物：`results/stage0-028-r02/prediction-test-{r1,s22,s33}/report.json`。这是在从未接触过的种子上独立复现的正结果，与D36单种子val上的初步正结果方向一致。

## D55 — SCREEN-028 实现决策：replay 地图紧凑存储、观测对齐、评测 checkpoint 导出（2026-09-29，运行前）

Agent：Claude Sonnet 5.5 /ybc（SCREEN-028 执行 Agent）。三条只影响实现方式、不改 D52–D54/D56 判据的决策：(1) **`--replay-compact-maps`（默认关闭，SCREEN 全部训练开启）**：replay 里的局部地图以 bool 存储、采样时还原 float32。地图严格是 0/1，采样出的 batch 与 float32 存储逐位相同（单测 `test_replay_compact_maps_samples_bit_identical_to_float32_storage`），只是把进程内 replay 与 checkpoint 缩小 4 倍。理由：policy-100k 训练的单个 checkpoint 11.7 GB，12 个进程并行常驻约 140 GB 再加保存时 pickle 缓冲的瞬时峰值，会逼近 251 GiB，且用户要求不靠加内存/swap 解决；未改 batch、replay 容量与更新规则。写入训练 protocol（`replay_compact_maps`），关闭时 protocol 与之前一致。(2) **观测对齐**：`CombinedEnv.step` 先取局部地图和做碰撞检查、后移动障碍，故策略在第 k 步看到的障碍位置是 P_{k−1}（重置时为 P_0）；dynmap-v1 的“当前”定义为观测里实际出现的位置，future/past 为 P_{c±h}（c = max(k−1,0)，h = 20，D56）。以“h=0 时叠加图逐位等于原观测”的环境级测试验证对齐。(3) **评测 checkpoint 导出**：训练 checkpoint 含 replay，64 个评测 worker 各加载一份会耗尽内存，故训练结束后导出仅含策略权重的 v2 checkpoint（与 `policy-100k.pt` 同布局，`derived_from` 记录源文件与 SHA-256），评测用它；预算末端 checkpoint（100k 步），不挑最优。另：`--obs-latency-steps` 与 `--map-latency-steps` 同时给出时，robot 延迟 k、地图延迟 max(k, m)（流水线不组合使用）。

## D58 — 清理无用数据与 policy-100k 训练过程检查点（2026-09-29，CLEAN-028）

Agent：Claude Opus 5.5 /ybc（协调方），用户确认（“AB删掉吧，我们不是要重新训练吗”）。删除：冒烟/探测输出（screen-028-smoke、followup-028-smoke、screen-028-probe）、SCREEN-028 叫停且无检查点的 D 线训练目录、P1-FIX 资源检查的可再生特征缓存（6 个 `check-*/cache`），以及 `p1a-20260923/sac-screen-100k/` 下 11 个含经验池的完整训练检查点（latest、step-*、validation-*.pt）。这修订了 AGENTS §1 “保留旧 checkpoint” 在该目录上的适用：运行与评测使用的 `policy-100k.pt`（sha256 e341262c…）完整保留，因此已验证基线仍可恢复；失去的只是从这些中间状态精确续训的能力（D57 已决定不续训）。清单与大小见 [清理记录](agent_logs/20260929-data-cleanup.md)。results/ 123 GiB → 20 GiB。

## D59 — 转入非全局模式；全流程重写为 PH0–PH8 统一编号；分支收拢到 main（2026-09-29，REFLOW-029）

Agent：Claude Opus 5.5 /ybc。用户：“之前SAC拿到的是全局地图，然后对于整个路线的规划导致控制误差难以起作用，世界模型也就无法接入，这里我们要调整为非全局模式的地图，一步一步的走……重新设计这里的流程和对比”“整理出一份完整的新流程”“测试无用的分支就删掉”“统一整个项目的流程阶段名的顺序”。(1) **依据**：代码核对（[REFLOW 日志](agent_logs/20260929-reflow.md)）确认 `PointToPointPlanner` 用整张真值地图生成 A* 代价并每步重跑（`eeplanner.py:579,617,651`），路径高度也读全图（`eeplanner.py:629`）；结合阶段2（原 Stage0/FOLLOWUP/SCREEN/CEIL）全部负结果，主线改为非全局模式：规划器只用至今观测到的地图。(2) **统一命名**：阶段按执行顺序编号 PH0–PH8（PH0 基线环境、PH1 世界模型离线预测、PH2 全局模式闭环探索〔结束〕、PH3 非全局伤害测试、PH4 非全局 SAC 重训与上限摸底、PH5 世界模型重训+方法冻结、PH6 闭环筛查、PH7 正式验证、PH8 写作），实验记 N.k，检查点记 GN，对比组改为 `B-sac/B-cap/B-hist/M-look/M-full`，任务 ID 记 `PHN-主题`，分支记 `phN-主题`。Stage0–3、R0-x、S0–S4、F1、G0–G2 及各流水线内部的 A/B、L/D、E1/E2 线名停止使用，对照表见 ROADMAP §12。P0–P5 只作模块文档文件名。(3) **取代**：D40 的 Stage 结构、D38 中 S0–S4 的命名与“P2+简化P4 为首个验收”的固定安排（改由 G4 决定主方法是 `M-full` 还是 `M-look`）；D39 的注入失配保留为 PH4.2 与 PH6/PH7 的条件，Gazebo 对齐（原 R0-5）移入 PH7。PH4 及以后的判据在 ROADMAP 中为草案，进入该阶段、产生数据前由用户确认后另行登记。(4) **分支**：`main`、`screen-028`、`ceil-028` 为同一条直线历史；本地 `main` 快进到 `ceil-028` 顶端（92778d0），删除已完全并入的 `screen-028`、`ceil-028`；不 push（由用户决定）。此后只有 `main` 长期存在，任务分支用后即删（ROADMAP §10）。本条不改任何算法、环境或评测语义。

## D60 — PH3-OBSMAP 非全局伤害测试判据预登记（2026-09-29，运行前）

Agent：Claude Opus 5.5 /ybc。规格采自协调方 OBSMAP 指令（[原文](agent_logs/20260929-obsmap-directive.md)，该指令原拟编号 D59，因 D59 已用于流程重写而顺延为 D60，内容不变）。**开关 `observed-map-v1`（默认关闭，关闭时输出逐字段不变）**：规划器 A* 代价与路径高度插值只使用“已观测地图”——每步以底盘为中心、朝前 270° 视角、半径 r 射线投射写入真值，被遮挡区域不写入，未观测区域按空地处理，回合开始只含初始位置一次扫描；SAC 局部地图、碰撞、IK、奖励、终止保持真值。**配置**：r ∈ {3, 5, 10} m + 名义全图；policy-100k 确定性，`--ik-mode fixed --ik-iterations 100`，种子 10000–10099 同种子配对；名义须复现 R0-3c 名义 SR 0.70。**判据**：某个 r 下 SR 相对名义下降 ≥0.15，且配对 episode-bootstrap 95% CI（10000 次重采样，种子 0）上界 <0，为“伤害通过”。**必报**：perfect-success、IK 失败/碰撞回合比例、失败原因分布；改道统计——相邻两步完整规划路线最大偏离 >0.3 m 记一次改道，报告每回合改道次数、改道后 20 步内 IK 失败/碰撞率。**G3 后续**：通过则 PH4 取 r_sel = 满足判据的最大 r；不通过则停下与用户讨论（SAC 局部地图也遮挡、更小 r、随机布局等需新登记）。登记后不因结果修改；实现细节（遮挡高度规则、增量更新）不属于判据，但须在任务日志写明依据。

## D61 — DECISIONS 整理：只保留现行条目（2026-09-29，REFLOW-029）

Agent：Claude Opus 5.5 /ybc。用户：“决策本来就删除了一些，你可以都整理一下”。延续 DOCS-028 的做法，把被取代的 D35、D38、D40、D43、D44 与 PH2 已结束的实验判据 D47–D54、D56、D57 原文移入 [archive/20260929-reflow/DECISIONS-archived.md](archive/20260929-reflow/DECISIONS-archived.md)（仅把相对链接改为从归档目录出发），本文件顶部新增“现行条目速查”与“已归档条目”索引。保留的条目正文一字不改，编号不复用。今后规则：新条目追加到文末；某条被新决策取代或其所属阶段结束时，由做出新决策的 Agent 在同一次提交中移入当期归档并更新索引。AGENTS §3 的“只追加”相应改为“新条目只追加、编号不复用；被取代的条目移入 archive”。不改任何算法、环境或评测语义。

## D62 — PH3 不再作为关卡；PH4.1 预登记并在开关验证后立即训练（2026-09-29，运行前）

Agent：Claude Opus 5.5 /ybc。用户：“不应该先训好了非全局的SAC吗”“可以调整，今晚最好就能开始训练”。**依据**：PH3 用全局模式训练的 policy-100k 测非全局伤害，掉点混有“未在该设定下训练”的分布偏移，“通过”不能说明重训后仍有空间，只有 PH4.1 能回答。**调整**：(1) PH3 改为“开关实现 + 诊断评测”，不设 G3；D60 的配置与阈值保留，照常作为诊断报告，不再决定是否训练，也不再用于选 r。(2) **PH4.1 预登记**：感知半径事先固定为 r ∈ {3, 5} m（视角 270°、遮挡高度 0.5 m，同 PH3 开关默认）；训练 `K-std-r3`、`K-std-r5`（非全局训练）各种子 11/22，`G-std` 补训全局种子 22（与 policy-100k 种子 11 组成 2 个），共 5 次；配置同 policy-100k（`--steps 100000 --save-interval 20000 --batch 256 --replay-capacity 100000 --random-steps 1000 --ik-mode fixed --ik-iterations 100 --eval-interval 0 --replay-compact-maps`），用 100k 预算末端 checkpoint（导出仅策略权重，同 D55），不挑最优。评测：各策略在自身训练条件下确定性评测种子 10000–10099；random 策略（`--policy-override random`）在 r=3、r=5 下各评 100 回合。**判据（每个 r 分别判定）**：SR(G-std) − SR(K-std-r) ≥ 0.10，且“训练种子×回合”分层 bootstrap 95% CI（10000 次，种子 0）下界 > 0；并且 SR(K-std-r) ≥ SR(random, r) + 0.30。**r_sel = 通过的最大 r**；两个 r 都不通过 → 重训的反应式 SAC 已足够，停下与用户讨论。4.2/4.3 在 r_sel 下进行，判据仍为 ROADMAP 草案、进入前登记。(3) 开关验证（设计说明 §4）通过后，训练与 PH3 诊断评测并行启动；训练优先，评测并发相应降低。登记后不因结果修改。

## D63 — observed-map-v1 实现选择（2026-09-29，PH3-OBSMAP，运行前）

Agent：Claude Sonnet 5.5 /ybc。不改 D60/D62 的任何判据或实验语义，只记录判据未规定的实现细节：(1) **射线**：从底盘连续位置出发，视角 F 以底盘朝向为中心，射线角间隔在有效半径 R_eff=min(R, 最远地图角+1 像素) 处 ≤0.5 像素（设计说明只要求 ≤1 像素，取更密以便 1 像素宽的细障碍在全可见设置下不漏，全可见等价性需要），径向步长 0.5 像素，采样点四舍五入取格，超出地图的采样终止射线且不标记。(2) **遮挡**：高度 >H 的格挡住其后，遮挡格本身可见；遮挡与可见性读 `_floorplan_img_filled`（实心），`_floorplan_img`（`add_objects_to_floormap` 里只画轮廓）与 `_floorplan_img_filled` 都乘已观测掩码后交给规划器。(3) **规划器地图视图**：`ObservedMapView` 用 `Map` 的未绑定函数（`get_inflated_map`/`binary_floorplan`/`in_collision`/坐标换算）以视图自身为 `self` 运行并有自己的膨胀缓存，只把不可变几何/配置属性转发给真值地图；`planner._map` 在 `set_ee_planner` 里、`planner.reset()` 之前替换，SAC 局部地图、碰撞、IK、奖励、终止仍用真值 `CombinedEnv.map`。(4) **重算权重**：仅当新观测到的格含障碍（真值 filled 或 img >0）时，用当前底盘位姿作为起点调用回合开始同一函数 `generate_base_feasible_eeweights`（膨胀调用为 ROS costmap C++，单次约 47 ms，约占重算 200 ms 的大部分，属规划器自身开销，未改算法）。(5) **改道统计**：每步取 `planner._last_global_plan_meters` 的 xy，改道距离 = 新路径各点到上一步路径点集最近距离的最大值，>0.3 m 记一次；改道发生在第 s 步生成新规划，“改道后 20 步”窗口取第 s+1..s+20 步内出现 `kin_failure`/`base_collision`；已观测占比分母为整张地图格数（含外框）；训练模式不收集统计。(6) **开关**：训练与评测共用 `--obsmap-radius`（>0 开启），`--obsmap-log-reroutes` 仅评测（名义配置的改道基准）；可与 `--policy-override` 组合，不可与 `--dyn-*`/`--latency-wm-comp`/`--shield-config`/非 simpleobstacle 任务组合；参数与 `obsmap_semantics='observed-map-v1'` 只在开启时进入 manifest，`obsmap_*` 字段只在开启时进入 episodes.jsonl。默认关闭时 episodes.jsonl/trajectory npz/tail.json 与干净代码逐位一致（PH3-OBSMAP 日志回归记录），因此不需要重跑任何已有基线。

## D64 — PH4.1 收敛检查（补充 D62，2026-09-29，运行前）

Agent：Claude Opus 5.5 /ybc。用户：“跑一个收敛检查吧”（针对“10万步够吗”）。**依据**：全局模式下 10 万步已收敛（policy-100k 0.70；CEIL 30 万步预算 15–25 万步 0.66–0.69，未超过），但非全局模式无证据；若 `K-std` 只是训练不足，SR(G-std) − SR(K-std) 会被夸大，4.1 可能假通过。**补充内容**（D62 其余不变）：(1) 另训 `K-std-r3-long`、`K-std-r5-long` 各 1 次：种子 11，`--steps 300000`（学习率按 30 万步预算衰减），`--save-interval 50000`，其余同 D62，与 5 次 10 万步训练同时启动；用 30 万预算末端 checkpoint 评测（种子 10000–10099，各自 r）。(2) 学习曲线（诊断）：5 次 10 万步训练的 2 万步间隔 checkpoint 与长训练的 5 万步间隔 checkpoint 各评测 100 回合（种子 10000–10099），报告是否走平。(3) **4.1 通过条件增加一条**：对每个 r，还须 SR(G-std) − SR(K-std-r-long) ≥ 0.10（点估计；长训练只有 1 个种子，CI 按回合 bootstrap 另报、不作判据）；不满足则 4.1 在该 r 记为“训练不足，未通过”。4.1 的最终判定等长训练完成后给出；10 万步部分可先出点估计与 CI 作为中间结果。登记后不因结果修改。
