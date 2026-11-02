# task7 — 流程（草案）

## 2026-10-26 当前冻结入口

**状态：paused（用户明确冻结task7及其全部后续执行）**。依据[SRC-0984](../../SOURCES.md#src-0984)。已完成成果保留，未完成项暂停；下文历史active/review/待执行/旧授权不构成继续运行许可，所有后代任务同样受本冻结入口约束。后续先按[task8](../task8/TASK.md)规划PCD地图迁移与ghost传感器；本轮不恢复训练、D10、7.24或诊断，不修改task7源码/配置/产物。

冻结快照：v5已停、未完成5M，下层未冻结验收；正式D10因OOM未闭合，7.18.7/7.18.8调查与7.24剩余工作保留，7.22仅部分流水线交付，上层正式训练/ManiSkill仍未放行。最新既有训练证据[SRC-0983](../../SOURCES.md#src-0983)，本轮源码/进程只读核查[SRC-0985](../../SOURCES.md#src-0985)。历史结果不删除、不改写成完成。

规划记录：[task8日志](../../agent_logs/task8/20261026-codex-pcd-plan.md)。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（跨任务合同及冻结边界核对），普通记录low；本轮实际模型/强度未知。

---

状态：**draft，未授权实施**。设计与未定事项见[TASK](TASK.md)。

## 递归规则

本层恰有TASK.md、PROCEDURE.md、RESULTS.md三份主要文档。子任务位于本目录内部、继承编号（task7.1、task7.1.1…），每个子节点同样恰有三文档；本流程须列明子节点顺序、依赖、负责人、三文档链接与验收关系，父RESULTS汇总子RESULTS，不以父计划代替子任务实测。编号稳定不复用。代码、配置、日志、产物分别放`forem/src`、`forem/config`、`forem/logs/task7/<run-id>`、`forem/results/task7/<run-id>`。

## 实施阶段草案（子任务尚未建立；2026-10-19按新框架修订）

下表是设计收敛后的实施顺序草案，不是已建立的子任务；编号不与task7.N对应。

|顺序|内容|依赖|验收要点|
|---|---|---|---|
|1|ManiSkill可行性冒烟：容器、Blackwell与Vulkan渲染、Husky+UR5导入与底盘建模方式、测FPS（U13）|用户授权安装|能加载机器人与长方体场景并测得吞吐；不训练|
|2|地图生成器：程序化随机立方体＋mapgen JSON读取；自动检验（可解性、通道净空、掉头空间、目标可达、可见性）|U8、U9、U11|统计分布与规则一致；不合格地图被拒|
|3|自写环境核心：底盘(v, ω)圆弧积分、长方体世界、360°扫描射线求交；简单规则候选生成器（TASK §2.8）；冻结下层SAC的批量推演接口（2026-10-20）；G7用的路径族生成与评估、分段执行与重规划的执行器（§2.9原规格）|阶段2|对解析解的单元测试；候选可行性统计；推演与执行用同一网络与观测构造；G7“被评分的即是要执行的”；吞吐实测|
|4|UR5正运动学与IK、碰撞检测、末端路线规划、任务、奖励与终止（半马尔可夫累积）|阶段3|IK与现有MoveIt/BioIK结果对照；固定场景下判定逐项对照|
|4L|下层SAC单独训练（阶段L，2026-10-20新增，[task7.13](task7.13/TASK.md)）：以候选点为子目标、10 Hz 3维（vel_norm, ω, v）、IK求机械臂；达标后冻结|阶段4|子目标到达率等冻结前验收（数值待task7.13）；端到端性能核查|
|5|规则选点对照与离散SAC基线（训练阶段1，不接f_p；冻结下层执行）及G7（上层SAC＋规则路径执行器）在自写环境中跑通|阶段4L（G7只依赖阶段4）|学习曲线与成功率；阶段L的交互、调参与墙钟作为共享前置成本单独登记，各组另报底层步数、仿真秒数与总墙钟；G7只作整套方案参考（2026-10-20按Codex复核#6补）；端到端性能核查（根AGENTS性能要求）|
|6|f_p监督预训练（训练阶段2）与偏置层接入（训练阶段3，冻结基线）（TASK §2.7）|阶段5|f_p留出误差与“忽略动作”检查；零初始化接入时输出与阶段1一致（沿用阶段1全部权重、编码/归一化/掩码不变，以实测输出比对验收，TASK §2.7第5步）；反馈确实改变选择|
|7|自写环境内对照组1–4|阶段6；U14、U15|按TASK第4节|
|8|ManiSkill验证侧：同格式扫描、转换层、地图导入；与自写环境的一致性验收|阶段1、3、4|几何、传感器、动作接口逐项对照|
|9|ManiSkill零样本与测试期适应（对照组4–6，U6）|阶段7、8|真实任务指标；适应开销|
|10|汇总与独立复核|全部|—|

阶段1与阶段2–5相互独立，确认授权后可并行；其余按依赖顺序推进。每个阶段确认后再建立对应task7.N三文档，写明负责人、输入输出、异常处理与验收。

## 异常处理原则

任何一步与验收不符时停止并记录，不通过改变任务、奖励、传感器或放宽判据来求通过；需要改设计时回到TASK更新并经用户确认。


## 2026-10-19调研子任务（非实施阶段）

用户授权依据[SRC-0340](../../SOURCES.md#src-0340)。下列三项只读调研可并行，共享SOURCES与父文档由父Codex独占整合，禁止把原“拟定阶段1–10”自动映射为同号子任务。

|子任务|范围|负责人|顺序/依赖|三文档与父验收|
|---|---|---|---|---|
|task7.1|TD-MPC2与序列规划|Codex子Agent tdmpc2_research|并行，无实施依赖|[TASK](task7.1/TASK.md) · [PROCEDURE](task7.1/PROCEDURE.md) · [RESULTS](task7.1/RESULTS.md)；父核对关键原文和代码|
|task7.2|SC²-WM状态反馈与SAC衔接|Codex子Agent scwm_research|并行，无共享写入|[TASK](task7.2/TASK.md) · [PROCEDURE](task7.2/PROCEDURE.md) · [RESULTS](task7.2/RESULTS.md)；父核对归属和建议边界|
|task7.3|IK失败与优化|Codex子Agent ik_research|并行，无共享写入|[TASK](task7.3/TASK.md) · [PROCEDURE](task7.3/PROCEDURE.md) · [RESULTS](task7.3/RESULTS.md)；父核对求解/执行/任务语义|

推荐Codex GPT6.1sol / Claude Sonnet5.5，medium，跨论文与实现核对；实际配置见各独立日志，未知不得猜测。父Agent读取交付、抽查来源后汇总，不将子Agent自报完成当作算法验证。

## 2026-10-19准备与设计子任务（三文档已建）

2026-10-20 21:35现状（Claude进度审核）：task7.4/7.5/7.7–7.11/7.13规格v1均已写，相应用户决定项已定（N1–N12、D1–D20、T1–T9、F1–F9、R1–R8、B类，SRC-0401–0418）；冻结前C类项延后到训练前；task7.6经Claude复核done；task7.14环境核心已授权（SRC-0419）、G1–G3已定（SRC-0421），待Codex恢复实施。以下为16:50原文——2026-10-20 16:50状态（按Codex复核#13更新；原句见git历史）：task7.1–7.3调研done；task7.5(A)审计done；task7.4、7.5(B)、7.7、7.8已有设计交付，结构多数由用户确定、数值待定，其中7.4、7.5依赖旧路径执行器的部分待按两层SAC重写；task7.6计时基准已交付（review，待复核）；task7.9 R1–R8已定（[SRC-0401](../../SOURCES.md#src-0401)）；task7.10–7.11尚未起草；task7.12暂缓；task7.13新建，第1步CBL代码核查由Codex执行中。设计文档交付不等于实现或训练已执行。下表负责人一列仍为建议；实际执行记录见各子任务RESULTS与PROGRESS。

依据[SRC-0359](../../SOURCES.md#src-0359)：用户要求为SIM、世界模型训练、前瞻点网络改造、VCM等做准备，授权Claude写文档。下列子任务均为准备/设计，不含实现；“需授权”的步骤在用户明确授权前只做计划。负责人为建议，未登记实际负责人。

|子任务|内容|建议负责|顺序/依赖|三文档|验收关系|
|---|---|---|---|---|---|
|task7.4|总体规格与接口：数据流、任务定义、失败处理、训练阶段、对照与评估|Claude与用户|最先起草；定稿依赖7.5–7.11|[TASK](task7.4/TASK.md) · [PROCEDURE](task7.4/PROCEDURE.md) · [RESULTS](task7.4/RESULTS.md)|汇总节点；定稿后回写本TASK|
|task7.5|SIM环境规格与代码复用审计|(A)Codex只读；(B)Claude|(A)可立即派发；(B)依赖7.4|[TASK](task7.5/TASK.md) · [PROCEDURE](task7.5/PROCEDURE.md) · [RESULTS](task7.5/RESULTS.md)|7.6、7.9的输入|
|task7.6|IK与路径评估计时基准|Codex|依赖7.5(A)；**运行需授权**|[TASK](task7.6/TASK.md) · [PROCEDURE](task7.6/PROCEDURE.md) · [RESULTS](task7.6/RESULTS.md)|决定路径数N与检查点间隔的可行范围|
|task7.7|场景、地图与扫描设计|Claude；查证/生成可由Codex|依赖7.4；与7.8协调；生成地图需授权|[TASK](task7.7/TASK.md) · [PROCEDURE](task7.7/PROCEDURE.md) · [RESULTS](task7.7/RESULTS.md)|7.8、7.9、7.11的输入|
|task7.8|VCM状态编码设计|Claude；SC²-WM核查可由Codex|依赖7.7、7.4|[TASK](task7.8/TASK.md) · [PROCEDURE](task7.8/PROCEDURE.md) · [RESULTS](task7.8/RESULTS.md)|7.10、7.11的输入|
|task7.9|前瞻点生成：规则版规格与生成网络改造方案|Claude；原文核查可由Codex|依赖7.5、7.7|[TASK](task7.9/TASK.md) · [PROCEDURE](task7.9/PROCEDURE.md) · [RESULTS](task7.9/RESULTS.md)|7.10的输入|
|task7.10|离散SAC选点与偏置层设计|Claude；Codex复核|依赖7.4、7.8、7.9|[TASK](task7.10/TASK.md) · [PROCEDURE](task7.10/PROCEDURE.md) · [RESULTS](task7.10/RESULTS.md)|7.11的输入|
|task7.11|世界模型f_p训练方案|Claude；Codex复核|依赖7.7、7.8、7.10|[TASK](task7.11/TASK.md) · [PROCEDURE](task7.11/PROCEDURE.md) · [RESULTS](task7.11/RESULTS.md)|交7.4汇总|
|task7.13|下层SAC（10 Hz，末端速度＋(ω, v)）设计：观测、奖励、子目标采样、推演与执行接口、到达/超时重定义（U31–U38）；2026-10-20新增，[SRC-0400](../../SOURCES.md#src-0400)|Claude；Codex复核CBL代码口径|与task7.4、7.10协调；成本以7.6为输入|[TASK](task7.13/TASK.md) · [PROCEDURE](task7.13/PROCEDURE.md) · [RESULTS](task7.13/RESULTS.md)|7.4、7.10的输入|
|task7.14|**环境核心实施**（2026-10-20用户授权，[SRC-0419](../../SOURCES.md#src-0419)）：地图与真值几何、底盘、全景深度与栅格、UR5 FK/IK/DLS、路线推进、L.0环境流程、批量推演接口、测试与有界计时|Codex执行；Claude复核|依赖7.4、7.5、7.13已定规格与G1–G3|[TASK](task7.14/TASK.md) · [PROCEDURE](task7.14/PROCEDURE.md) · [RESULTS](task7.14/RESULTS.md)|实施阶段3、4（环境部分）；之后为候选生成器与阶段L|
|task7.15|**规则候选生成器实施**（task7.9规格；2026-10-21授权，[SRC-0431](../../SOURCES.md#src-0431)）|Codex执行；Claude复核|依赖7.14；与7.16、7.17并行（文件归属互不重叠）|[TASK](task7.15/TASK.md) · [PROCEDURE](task7.15/PROCEDURE.md) · [RESULTS](task7.15/RESULTS.md)|7.18的输入|
|task7.16|**A类程序化长方体地图生成器与地图池**（forem模块，mapgen不动）|Codex执行；Claude复核|与7.15、7.17并行|[TASK](task7.16/TASK.md) · [PROCEDURE](task7.16/PROCEDURE.md) · [RESULTS](task7.16/RESULTS.md)|7.17集成、7.18训练与验证地图|
|task7.17|**回合环境**：任务采样、路线规划（照N²M²/CBL原代码）、批量reset封装、G1遮挡计数|Codex执行；Claude复核|依赖7.14；与7.15、7.16并行|[TASK](task7.17/TASK.md) · [PROCEDURE](task7.17/PROCEDURE.md) · [RESULTS](task7.17/RESULTS.md)|7.18的输入|
|task7.18|**阶段L**：下层SAC网络与训练（两变体各1种子×5M）|Codex执行；Claude复核|依赖7.15、7.16、7.17复核done|[TASK](task7.18/TASK.md) · [PROCEDURE](task7.18/PROCEDURE.md) · [RESULTS](task7.18/RESULTS.md)|冻结前验收见7.19|
|task7.19|**G7规则路径执行器与阶段L冻结验收**（D10）|G7-1–G7-4已定（2026-10-21，[SRC-0434](../../SOURCES.md#src-0434)）；Codex实现|实现待7.15、7.17 done；验收依赖7.18检查点|[TASK](task7.19/TASK.md) · [PROCEDURE](task7.19/PROCEDURE.md) · [RESULTS](task7.19/RESULTS.md)|决定下层是否冻结、进入阶段1|
|task7.20|**上层决策级批量环境与G1规则选点**（2026-10-21 Claude起草，**已授权**（[SRC-0439](../../SOURCES.md#src-0439)），[SRC-0438](../../SOURCES.md#src-0438)）|Codex执行；Claude复核|依赖7.15、7.17 done；与7.21并行|[TASK](task7.20/TASK.md) · [PROCEDURE](task7.20/PROCEDURE.md) · [RESULTS](task7.20/RESULTS.md)|供7.22训练与各组评估|
|task7.21|**上层网络模块**：VCM、候选编码、头A/B、偏置层、f_p（2026-10-21 Claude起草，**已授权**（[SRC-0439](../../SOURCES.md#src-0439)），[SRC-0438](../../SOURCES.md#src-0438)）|Codex执行；Claude复核|只依赖规格，可立即并行|[TASK](task7.21/TASK.md) · [PROCEDURE](task7.21/PROCEDURE.md) · [RESULTS](task7.21/RESULTS.md)|供7.22|
|task7.22|**上层训练流水线**：经验池、离散SAC、阶段1/2/3、评估；有界核查与试训，正式训练另行授权（2026-10-21 Claude起草，**已授权**（[SRC-0439](../../SOURCES.md#src-0439)），[SRC-0438](../../SOURCES.md#src-0438)）|Codex执行；Claude复核|依赖7.20、7.21 done；正式训练前提D10通过（7.19）|[TASK](task7.22/TASK.md) · [PROCEDURE](task7.22/PROCEDURE.md) · [RESULTS](task7.22/RESULTS.md)|交付正式训练墙钟推算，供用户授权|
|task7.12|ManiSkill可行性冒烟（U13）|Codex|**暂缓**（用户2026-10-19：现在只考虑sim，[SRC-0362](../../SOURCES.md#src-0362)）；恢复后建容器/安装/运行需授权|[TASK](task7.12/TASK.md) · [PROCEDURE](task7.12/PROCEDURE.md) · [RESULTS](task7.12/RESULTS.md)|实施阶段8的前提|

2026-10-20两层SAC决定（[SRC-0400](../../SOURCES.md#src-0400)）的影响：新增task7.13；下列子任务已有交付中按“路径计划/路径族/固定评分”写的部分须重写，现只在各自TASK状态行下注明，正文未改：task7.4合同⑦（到达与决策超时）、⑨（全部路径不可行时的分层排序）及上层训练阶段（前加阶段L）；task7.5 B6风险特征（[SRC-0393](../../SOURCES.md#src-0393)按“最优路径扫过区域”定义）、B7（不同步路径族s分配）；task7.6成本公式（IK计时仍可用）；task7.10候选特征e_k来源；task7.11 f_p输入中的候选特征。原路径执行器规格保留为对照组G7的定义。

建议批次（按数字顺序理解编号，task7.10在task7.9之后）：

1. 可立即开始：task7.4起草；task7.5(A)只读审计。task7.12暂缓。
2. 第二批：task7.7、task7.6（待授权）、task7.9。
3. 第三批：task7.8、task7.10、task7.11。
4. 收尾：task7.4汇总定稿，经用户确认后回写本TASK。

2026-10-20补充批次（两层SAC后）：task7.13先于task7.10接口定稿与task7.4汇总完成相关设计（输入：Codex CBL代码核查）；task7.13与task7.10/7.4的互相依赖字段（f_k字段、到达/超时、时序合同U39）作为协调项；task7.6成本公式在task7.13给出推演步定义后重算。

上午的调研子任务task7.1–7.3建立于旧讨论方案，其结论（TD-MPC2、SC²-WM反馈、IK）按新框架在task7.4、7.9–7.11中复核引用；其结项与来源SRC-0341–0355由Codex父任务处理。原“父Codex独占SOURCES与父文档”的安排：2026-10-19晚用户直接指示Claude写文档，Claude已在[交流文档](../../agent_logs/task7/20261019-claude-codex-sync.md)说明改动。

推荐模型：Codex GPT6.1sol / Claude Sonnet5.5，各子任务强度见其TASK；设计与审计多为medium。


## 2026-10-23 接手审核

新增task7.23（用户授权SRC-0960）：Codex父Agent统筹，task7.23.1–7.23.3只读并行审查，完成后父Agent核验汇总，不构成新实验授权。[TASK](task7.23/TASK.md) · [PROCEDURE](task7.23/PROCEDURE.md) · [RESULTS](task7.23/RESULTS.md)。


## 后续尝试：task7.24短程任务训练（2026-10-23草案）

按用户“用短任务代替较长训练任务”澄清新增task7.24。Codex负责文档与只读预查；建议顺序P0协议确认→P1隔离实现/测试→P2有界采样/性能检查→P3原分布/短路线A-B→P4判读。实现与试跑参数尚未确认，不自动开训；不依赖D10恢复才能写方案，也不替代冻结验收。[TASK](task7.24/TASK.md) · [PROCEDURE](task7.24/PROCEDURE.md) · [RESULTS](task7.24/RESULTS.md)。推荐Codex GPT6.1sol / Claude Sonnet5.5 medium；依据[SRC-0969](../../SOURCES.md#src-0969)。


## 2026-10-24 task7.25调研流程

负责人Codex；顺序为现状/旧资产核查→原论文/官方代码检索→三问题综合与待授权验证流程→文档和来源核查。文档工作不依赖D10恢复；未来候选标签/闭环比较依赖可靠下层与相应执行授权，不启动后续阶段。父结果汇总本轮已核事实与未执行项，不以调研替代实验验收。[TASK](task7.25/TASK.md) · [PROCEDURE](task7.25/PROCEDURE.md) · [RESULTS](task7.25/RESULTS.md)。本层及task7.25保持递归三文档规则；未新派子Agent。依据[SRC-0974](../../SOURCES.md#src-0974)、[SRC-0982](../../SOURCES.md#src-0982)。

推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium，因跨地图/候选/控制因果核对；实际配置未知。
