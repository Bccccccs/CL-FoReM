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


## D43 — 全量文档审查：过时路径与指令清理（2026-09-28，DOCREV-028）

Agent：Claude Opus 5.5 /ybc。用户：“审查一次全部的文档，把过时的目录修改，过时的指令删除或修改”。范围为维护中与参考文档；`archive/` 不改，已完成任务的历史日志正文不改写（只给作废的提示词加作废标注），DECISIONS 只追加。(1) AGENTS.md 重写 §0/§3–§6：ROADMAP 为唯一执行计划、单仓库与 GitHub 远端、node01 硬件/软件、当前阶段表；删除来源机器 §7/§8（2080 Ti、Python 3.8、`mmhusky-p0-ready`、pip 冲突）与已归档的 REVIEW.md 链接；§1/§2 原文保留。(2) ENV.md 重写为 node01 现行环境，删除来源机器环境、`cd /home/yanbochao/...`、`mm_husky:deps` 构建与“严格复现失败”等过时结论。(3) `docker/run.sh` 默认容器/镜像改为 `mmhusky-node01`/`mm_husky:node01`，`build` 默认用 `Dockerfile.node01`（旧 `Dockerfile` 路径保留为 `MM_DOCKERFILE=Dockerfile`）。(4) P0–P5 删除在当前环境不存在的“executing-plans 技能”指令；P1 文件清单由“拟创建”改为已实现；各参考文档中 D33/D29“待修复”的状态更新为 D34/D36 后的现状，RESEARCH_EXPERIMENTS 旧“下一步”计划删除并给出 B0–C2 与 S0–S4 的对应。(5) 6 份 09-22 P0 日志正文确认无副本，指向它们的跳转占位删除，引用处改为“正文缺失”标注。(6) Stage0 启动提示词更新为 v3（分支 `stage0-028` 提交、不 push；常驻容器可用），v2 作废。AGENTS/ENV/PROGRESS 审查前原文存于 `archive/20260928-docrev/`。不改变任何算法、评测协议或实验语义。


## D44 — 来源机器遗留文件与作废提示词移出现行目录（2026-09-28，DOCREV-028）

Agent：Claude Opus 5.5 /ybc。用户：“清理”。(1) `docker/Dockerfile`、`requirements-p0.txt`、`python-freeze.txt`、`dpkg-versions.txt`、`pip-check.txt` 及 `docker/validation/` 顶层与 `p0-ready/` 输出（来源机器 `mm_husky:p0-ready` 相关）`git mv` 至 `docker/legacy/`，附 README；`docker/validation/node01-20260922/`（本机验收证据）保留。`run.sh build` 只保留 `Dockerfile.node01` 路径，D43 中的 `MM_DOCKERFILE=Dockerfile` 选项随之取消。(2) 作废的 Stage0 提示词 handoff 与 v2 移入 `doc/archive/20260928-docrev/`，Stage0 日志中的链接同步更新。未删除任何文件内容；agent_logs 证据文件与 Stage0 正在使用的 patch/R0-1 脚本不动。archive 内快照的相对链接不再维护。


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

Agent：Claude Opus 5.5 /ybc（协调方，仅文档；实现交执行 Agent）。依据用户“两边都执行一下”与 [设计说明](agent_logs/20260928-followup-spec.md) §3。在 R0-4/R0-4b 已采 10 个条件（种子 9600–9699）上离线比较无梯度的低维适应：V4 增益标量（robot 块最小二乘，截断 [0,3]；另报 robot/map 各一标量）、V5 延迟选择（d∈{0,1,2,3,5,10}，只延迟底盘两维，初始取 0，残差 EMA α=0.2 选择）、V6（V5+V4），对照 V0 冻结。协议沿用 D49：先预测后更新、每回合重置、只在未用于更新的后续步评估、配对 episode-bootstrap。**通过判据（登记后不改）**：至少一个变体在 {gain1.4_delay0, gain1.8_delay0, gain1.4_delay5, gain1.0_delay5} 中 ≥2 个条件上挽回比例 ≥30% 且“变体−冻结”配对 CI 上界 <0，且名义条件下“变体−冻结”均值 ≤ 冻结名义残差的 1%。另报估计增益与真值的相关、所选延迟与真值一致率。解读边界：通过只说明低维辨识改善预测，不证明优于历史条件 SAC（S2）；延迟 5–10 步为压力档，非现实误差（LIT-MISMATCH-028）。

## D51 — FOLLOWUP-028 B 线：IK 失败前瞻判据预登记（2026-09-28，运行前）

Agent：同 D50；设计见 [设计说明](agent_logs/20260928-followup-spec.md) §4。**种子登记**：B1 用 R0-3/R0-3c 已有 10000–10099；B2 新采 1000–1999（确定性策略、名义条件，训练 1000–1699 / 验证 1700–1799 / 测试 1800–1999；当前世界模型仅用 0–999 训练，1000–1999 曾以随机策略采入 dataset-v2-10k 但未被当前模型使用）；B3 用 10000–10099。**B1 判据**：名义 `ik_limit` 失败种子在 8 个温和配置（增益∈[0.8,1.2]、延迟∈{0,1,2}，不含名义）中至少一次成功的比例 ≥0.30，且该比例减去“名义成功种子在同配置中至少一次失败”比例的 bootstrap 95% CI 下界 >0。**B2 判据**（测试集步级 AUROC，标签 H=5：fail[t..t+4] 中是否出现 IK 失败，仅在 fail[t−1]=0 的步评估；按测试回合 bootstrap 10000 次）：AUROC(C-wm)−AUROC(C-cur) ≥0.02 且 CI 下界 >0；AUROC(C-wm)−AUROC(C-hist) CI 下界 >0；AUROC(C-wm)−AUROC(C-geo) CI 下界 >0；三项全满足才通过。C-wm 的推演只用策略对预测特征的确定性动作，不得使用记录的未来动作。H=10 与数据效率曲线为次要报告。**B3**（探索性，不作通过依据）：六臂（none/wm/cur/hist/geo/random），风险超阈值时将末端参考速度维设为 −1；各分类器阈值在 B2 验证集上定为步级触发率 10%，random 臂触发概率取 wm 臂验证集触发率；看 B3 结果后不得调整。所有新行为默认关闭，关闭时输出逐字段不变。
