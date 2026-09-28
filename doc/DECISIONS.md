# 决策记录

> **2026-09-28 DOCS-028 清理**：按用户“和现有决策冲突的旧决策也删除”，已将 D02、D10、D14、D25、D26、D28、D29、D30 移至 [archive/20260928-docs028/DECISIONS-superseded.md](archive/20260928-docs028/DECISIONS-superseded.md)（原文保留，编号不再复用）。本文件只保留现行有效决策。

起始日期：2026-09-22；最近增补：2026-09-28。按日期更晚的明确变更执行，保留历史证据与决定。

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

## D35 — 投稿目标改为 CCF-A/B（2026-09-28，VENUE-028）

Agent：Claude Opus 5.5 /ybc。用户明确“我们想投一篇CCFA类的论文”，随后补充“CCFB也可以”。按 CCF 第七版（2026）目录（第三方整理页核对，官网 PDF 本机下载被拒，正式使用前须以 ccf.org.cn 为准），IROS 为 C 类，不满足该要求；ICRA 2027 已于 2026-09-16 截稿。因此 D30 及 AGENTS §0、RESEARCH_GOAL 中“以 IROS 2027 为目标”由本条取代，具体会议待用户在[候选](agent_logs/20260928-venue-ccf.md)中选定后再同步修改这两份文档。本条不改变 P0–P5 门槛、SAC 最终动作职责和当前“只引入 Husky”的范围；若选择 ML 会议路线而需扩展到多机器人/标准基准，属于范围变更，须用户另行确认。

## D36 — 修复后1000回合正式train/val诊断（2026-09-28，P1-RETRAIN-028）

按用户明确授权执行D27/D34协议：train seeds0–999/val9600–9899、seed11、hidden64/lr3e-4/wd1e-3/batch512/max200epoch/patience20，无max-train-batches。没有修改训练算法或控制语义。无动作86epoch/best66/40678batch；动作107epoch/best87/50611batch，均完整epoch并正常早停。

300val逐回合等权标准化total：一步copy0.253411/no_action0.173332/action0.167075，五步copy0.492552/no_action0.405974/action0.389825。action相对copy改善34.07%/20.86%，相对no_action改善3.61%/3.98%；四组配对episode-bootstrap95%CI均负。全部回合纳入，包括高误差9881和五步唯一略差于no_action的9699。完整结果见[报告](agent_logs/20260928-p1-retrain-report.md)。训练+评测1031.71s；RSS3.029GiB/cgroup3.032GiB/GPU compute合计1482MiB/task swap0/宿主swap增量0，16GiB/no-swap硬隔离通过。65测试复跑通过；best-val重评与最佳曲线完全一致。

解释边界：这是单训练seed、用于早停的验证集上的P1a初步预测证据。没有独立最终test或跨seed稳定结论，不将CI视为包含选型与训练seed变化。原采集初始观测与floorplan图像精确hash跨split无交集，但近重复场景/场景族隔离未验证。本轮不使用旧test，不扩大9600，不进入P2，不声明闭环控制改善。建议先保持配置验证seed22/33并完善未曝光独立test协议（尚未执行）。P1研究出口review；P2–P5保持blocked。无精确resume CLI，latest包含完整epoch状态不等于支持精确续训。

## D37 — 暂定投稿目标 IJCAI 2027（2026-09-28，VENUE-028）

Agent：Claude Opus 5.5 /ybc。用户要求“今年底投、明年初截稿”，并决定“暂时按IJCAI 2027做准备”。IJCAI 在 CCF 2026 为 B 类；2027 截稿按历年规律约为1月中旬，官方 CFP 未发布，发布后须核对日期、页数、摘要预注册与双投政策。IJCAI 与 ICML 2027 时间重叠，同一论文只投其一。按只计实验时间的倒排：10月中前完成P1出口、最小闭环与差异来源设置及100k筛查；约2026-11-20为去留点，届时核心闭环无正结果则放弃1月会议、改投 NeurIPS 2027；约12-20冻结结果后写作。已同步修改 AGENTS §0、RESEARCH_GOAL、README 的目标描述。本条不改变 P0–P5 门槛、SAC 最终动作职责和“只引入 Husky”范围；闭环阶段顺序（P2+简化P4 合并为最小闭环）与差异来源仍待用户决定（见 LOOP-028）。


## D38 — 最小闭环 = P2 + 简化 P4 一起实现与验收（2026-09-28，RUNPLAN-028）

Agent：Claude Opus 5.5 /ybc。用户确认“P2+简化P4一起做”。依据 LOOP-028：P2 单独使用时修正量只是 o_t 的函数；执行后用实际 a_t 与真实 o_(t+1) 更新世界模型，是闭环中引入新信息的部分。因此首个闭环研究验收改为：P2-MIN 前瞻修正 + 简化 P4（执行后一步预测器更新，每回合重置，首轮固定周期、不用 KL 触发）作为主方法 S4；仅 P2（S3）、同容量 adapter（S1）、历史条件 SAC（S2）和原 SAC（S0）为匹配对照。P4 不再依赖“P2 单独稳定、P3 固定”；P3、KL 触发、P1b/GRU 作为后续消融或扩展。P1 出口（D36 后补种子与独立 test）仍是前置条件，SAC 最终动作职责和“只引入 Husky”不变。失配来源、是否使用 Gazebo 仍待用户决定；本条不启动实验（用户：先不跑）。README/P2/P4 的依赖描述待实现开始前同步。


## D39 — 失配来源：analytical 注入执行失配 + Gazebo 自然失配（2026-09-28，RUNPLAN-028）

Agent：Claude Opus 5.5 /ybc。用户决定“注入失配加Gazebo一起用”。分工：(1) analytical 中新增版本化、默认关闭的系统性执行失配开关（每回合底盘速度增益、动作延迟步数），用于训练时随机化和受控主实验（可复现、可画强度-效果曲线）；关闭时必须与现基线逐元素一致。现有 `transition_noise_base` 为零均值噪声，保留但不作为可适应失配。(2) Gazebo 作为“analytical 训练→Gazebo 执行”的自然失配评测，不在 Gazebo 训练。Gazebo 进入正式评测前须先在本文件选定实时方案（P0 日志 A–D），并对齐控制周期（训练 TIME_STEP_TRAIN=0.1s，Gazebo 当前 time_step 0.02s）与回合时长；此前 4 个 Gazebo 回合使用 2000 步策略，不作为可用性结论。未见布局（需解除 map.py:837 间距硬编码）与 dynobstacle 留作泛化备选。两项均属环境语义扩展，实现时单列版本与测试。本条不启动实验。


## D40 — 文档架构调整：ROADMAP 为唯一执行计划（2026-09-28，DOCS-028）

Agent：Claude Opus 5.5 /ybc。用户：“现有的流程组织架构太乱……你做一下调整”“没有用的就清理”。(1) 新建 [ROADMAP](ROADMAP.md) 为唯一执行计划：Stage0 前置验证 → G0 → F1 设计冻结 → Stage1 闭环筛查（S0–S4）→ G1（最迟11-20）→ Stage2 正式验证 → G2（约12-20）→ Stage3 写作；每阶段实验、对照、规模、预登记判据、种子登记见其 §4–§9。LOGIC-028 的 L1/L2 并入 R0-3/R0-4 判据，L4/L5/L7 列为 F1 必答项。各阶段规模（如 Stage1 3种子×100k、Stage2 5种子×500k、Stage2 正式测试 20000–20299）以 ROADMAP 为准，EVALUATION v1 中不同的数字不再适用于当前主线，其通用协议保留。P0–P5 仅作技术模块编号，不代表顺序。(2) README 重写为“维护中/参考/历史”三类；参考文档顶部加定位横幅；REVIEW、WORKFLOW_GUIDE、P0_ACCEPTANCE、P0_BASELINE、NODE01_DOCKER_ADMIN、P0/REMEDIATION_PLAN 移入 archive/20260928-docs028/（未删除）。(3) PROGRESS 顶部加看板，任务行不改内容，按“进行中/已完成/旧阶段行”分表。(4) 清理已退出的 11 个 mmhusky-p1-* 容器与 agent_logs/__pycache__；停止并清理被用户中止的 Stage0 执行残留，未完成失配代码备份为 patch 后还原（见 STAGE0-028 日志）。Stage0 从头重新执行。(5) 按用户“和现有决策冲突的旧决策也删除”，将 D02、D10、D14、D25、D26、D28、D29、D30 移至 archive/20260928-docs028/DECISIONS-superseded.md，D27 仅加测试集注释。AGENTS.md 的必读清单与 §4 阶段表尚未同步（本 Agent 读取该段被权限规则拒绝），待用户处理。


## D41 — 工作区改名为 CL-FoReM，常驻容器按新路径重建（2026-09-28，PATHSYNC-028）

Agent：Claude Opus 5.5 /ybc。工作区于约 15:53 由 `/home/ybc/projects/mm_husky_ws` 改名为 `/home/ybc/projects/CL-FoReM`（内容不变）。用户要求“同步一下路径，容器也重新挂载”。(1) 宿主路径以 `/home/ybc/projects/CL-FoReM` 为准；**容器内挂载点仍为 `/root/mm_husky_ws`**，devel、runner、launch 脚本和 docker/ 下的容器内路径不改。D31 等历史条目及已完成任务日志/证据 JSON 中的旧宿主路径是当时实测记录，不改写，按新路径理解。AGENTS §0/§3、ENV 已同步。(2) `mmhusky-node01`、`mmhusky-node01-gz` 用同一镜像 `mm_husky:node01`（`sha256:e674db49…c430`）与原参数（bridge、nvidia runtime、shm 8g、无内存限制）经 `docker/run.sh up` 重建，仅挂载源改为新路径；重建前两容器仅有遗留 analytical launch 与 Xvfb、可写层只有 NVIDIA 注入和缓存。重建后 CUDA、train-smoke、analytical 20 步、Gazebo 启动检查均通过，证据见 [PATHSYNC-028 日志](agent_logs/20260928-path-sync.md)。本条不改变任何算法、评测协议或实验语义。


## D42 — src/modulation_rl 并入根仓库形成单仓库 CL-FoReM（2026-09-28，PATHSYNC-028）

Agent：Claude Opus 5.5 /ybc。用户选择“合并为单仓库”、GitHub 私有仓库。(1) 先在原子仓库 `p0-node01` 分支把 P1-FIX-028 此前未提交的改动原样提交为 `06c0ee1`（wm/data、encoder、evaluate_prediction、train_offline、val_probe、cache、streaming 测试、wm_resource_check）；根仓库待提交的 doc/docker/AGENTS/ENV 提交为 `9293083`。(2) 原 `.git` 移至 `/home/ybc/projects/CL-FoReM-backups/modulation_rl-dotgit-20260928`，另有全引用镜像 `modulation_rl-20260928.git`；根 `.gitignore` 去掉 `/src/modulation_rl/`，以 `merge -s ours --allow-unrelated-histories` + `read-tree --prefix=src/modulation_rl/` 合并为 `ac8d686`，工作区文件未变动。文档引用的 `1ccedd0/68b8d0b/b23aa39/2a1348a` 仍可在本仓库解析；注意 `git log -- src/modulation_rl/...` 不会跨越 subtree 前缀追溯旧提交，查旧历史直接按哈希。(3) 溯源影响：`p0_runner.provenance` 对原子仓库路径将记录 `git unavailable`（有异常兜底），根仓库条目已覆盖全部代码；`wm_resource_check.py` 的 `git_head` 改为读根仓库（原写法会因 .git 不存在直接崩溃），仍用显式 `--git-dir` 以避开容器内 safe.directory。不改变任何算法、评测或实验语义。其他第三方 ROS 包仍为独立仓库。(4) 远端：用户创建 GitHub 私有仓库，根仓库 origin = `git@github.com:Bccccccs/CL-FoReM.git`，首推 `7890c80`。
