# task7 — 流程（草案）

状态：**draft，未授权实施**。设计与未定事项见[TASK](TASK.md)。

## 递归规则

本层恰有TASK.md、PROCEDURE.md、RESULTS.md三份主要文档。子任务位于本目录内部、继承编号（task7.1、task7.1.1…），每个子节点同样恰有三文档；本流程须列明子节点顺序、依赖、负责人、三文档链接与验收关系，父RESULTS汇总子RESULTS，不以父计划代替子任务实测。编号稳定不复用。代码、配置、日志、产物分别放`forem/src`、`forem/config`、`forem/logs/task7/<run-id>`、`forem/results/task7/<run-id>`。

## 实施阶段草案（子任务尚未建立；2026-10-19按新框架修订）

下表是设计收敛后的实施顺序草案，不是已建立的子任务；编号不与task7.N对应。

|顺序|内容|依赖|验收要点|
|---|---|---|---|
|1|ManiSkill可行性冒烟：容器、Blackwell与Vulkan渲染、Husky+UR5导入与底盘建模方式、测FPS（U13）|用户授权安装|能加载机器人与长方体场景并测得吞吐；不训练|
|2|地图生成器：程序化随机立方体＋mapgen JSON读取；自动检验（可解性、通道净空、掉头空间、目标可达、可见性）|U8、U9、U11|统计分布与规则一致；不合格地图被拒|
|3|自写环境核心：底盘(v, ω)圆弧积分、长方体世界、360°扫描射线求交；简单规则候选生成器（TASK §2.8）；路径族生成与评估、分段执行与重规划的执行器（§2.9）|阶段2|对解析解的单元测试；候选可行性统计；“被评分的即是要执行的”；吞吐实测|
|4|UR5正运动学与IK、碰撞检测、末端路线规划、任务、奖励与终止（半马尔可夫累积）|阶段3|IK与现有MoveIt/BioIK结果对照；固定场景下判定逐项对照|
|5|规则选点对照与离散SAC基线（训练阶段1，不接f_p）在自写环境中跑通|阶段4|学习曲线与成功率；端到端性能核查（根AGENTS性能要求）|
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

2026-10-20状态：task7.1–7.3调研done；task7.5(A)审计done；task7.4、7.5(B)、7.7、7.8已有设计交付，结构由用户确定、数值待定；task7.6（计时，运行需授权）与task7.10–7.11未开始；task7.9草案v1已写（R1–R8待用户确认）；task7.12暂缓。下表负责人一列仍为建议；实际执行记录见各子任务RESULTS与PROGRESS。

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
|task7.12|ManiSkill可行性冒烟（U13）|Codex|**暂缓**（用户2026-10-19：现在只考虑sim，[SRC-0362](../../SOURCES.md#src-0362)）；恢复后建容器/安装/运行需授权|[TASK](task7.12/TASK.md) · [PROCEDURE](task7.12/PROCEDURE.md) · [RESULTS](task7.12/RESULTS.md)|实施阶段8的前提|

建议批次（按数字顺序理解编号，task7.10在task7.9之后）：

1. 可立即开始：task7.4起草；task7.5(A)只读审计。task7.12暂缓。
2. 第二批：task7.7、task7.6（待授权）、task7.9。
3. 第三批：task7.8、task7.10、task7.11。
4. 收尾：task7.4汇总定稿，经用户确认后回写本TASK。

上午的调研子任务task7.1–7.3建立于旧讨论方案，其结论（TD-MPC2、SC²-WM反馈、IK）按新框架在task7.4、7.9–7.11中复核引用；其结项与来源SRC-0341–0355由Codex父任务处理。原“父Codex独占SOURCES与父文档”的安排：2026-10-19晚用户直接指示Claude写文档，Claude已在[交流文档](../../agent_logs/task7/20261019-claude-codex-sync.md)说明改动。

推荐模型：Codex GPT6.1sol / Claude Sonnet5.5，各子任务强度见其TASK；设计与审计多为medium。
