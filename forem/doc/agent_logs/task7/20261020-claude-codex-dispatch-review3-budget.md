# 2026-10-20 Claude：给Codex的派发提示——第三轮复核（A）与阶段L/各组成本推算（B）

- 作者：Claude（claude-opus-5-5，推理强度未知）；由用户派发，Claude不启动。
- 写作时（约20:20）核对：task7.10上层规格草案v1已由另一Claude会话写好（[日志](task7.10/20261020-claude-upper-spec.md)，SRC-0412），故原拟“task7.10起草前证据核查”并入A的第4点，不单独派发。
- A、B只写各自日志、PROGRESS各自一行，以及B的一个新SRC条目，写入文件不重叠，可以并行。派发前确认没有其他Codex会话在改相同文件。

|提示|任务ID|推荐Codex|推荐Claude（若改由Claude执行）|理由|
|---|---|---|---|---|
|A|TASK7-SPEC-REVIEW3-20261020|GPT6.1sol，medium|Sonnet5.5，medium|跨多份文档核对一致性与“主张—来源”对应，需要核对多处因果关系|
|B|TASK7-BUDGET-ESTIMATE-20261020|GPT6.1sol，medium|Sonnet5.5，medium|只推导不运行；需核对单位、周期换算与各实测的适用条件|

实际模型/强度由执行方记录，无法核实写“未知”。

## A：第三轮复核（D13–D20、忠于原项目、task7.10草案v1）

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7-SPEC-REVIEW3-20261020。推荐模型GPT6.1sol、推理强度medium；在日志里写明你实际的模型与强度，无法核实写“未知”。

【先读】根 AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；你上一轮复核日志 forem/doc/agent_logs/task7/task7.13/20261020-codex-lower-spec-review.md；Claude的处理与后续日志：forem/doc/agent_logs/task7/task7.13/20261020-claude-lower-spec-review-fixes.md（含“D13–D20确定与忠于原项目”节）、forem/doc/agent_logs/task7/task7.10/20261020-claude-upper-spec.md；forem/doc/SOURCES.md 的 SRC-0382、SRC-0400–SRC-0412；forem/doc/DECISIONS.md 中2026-10-20的各条。

【开工登记】在 forem/doc/PROGRESS.md“项目级记录”表加一行（写前重读，保留他人内容）：TASK7-SPEC-REVIEW3-20261020｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/20261020-codex-spec-review3.md。

【背景】你第二轮的14项意见（11必须改、3建议改）已由Claude处理；用户随后确定D13–D20（SRC-0409）、要求设计“忠于三个原项目”（CBL、N²M²、SC²-WM），并决定一致性表#5上一动作时序改回CBL做法（观测中上一动作滞后一步，取代D9）、#6–#11保留（SRC-0410）；验证平台选择暂缓为U40（SRC-0411）。另一Claude会话写了task7.10上层离散SAC与偏置层规格草案v1（U.1–U.8，T1–T9待用户确认；SC²-WM打分结构核查SRC-0412）。以上只是设计文档，未实施。

【复核范围】forem/doc/tasks/task7/TASK.md（“2026-10-20 两层SAC”入口节、“与三个原项目的一致性”表、§2.7、§2.9、§3 U31–U40、§4）；task7.13/RESULTS.md（L.1–L.10、D1–D12表、D13–D20节）；task7.10/RESULTS.md（草案v1全文）与task7.10/TASK.md；task7.4/RESULTS.md文首“两层SAC下的修订与标注”节；task7.6/RESULTS.md §6R；task7.11/TASK.md状态行。检查：
1. 第二轮14项是否处理到位；处理后有无新矛盾或遗漏。
2. #5改回CBL后，所有写到“上一动作/无额外滞后/D9”的地方是否已同步（L.1、L.2、D表、父TASK、task7.4、DECISIONS），有没有残留旧口径。
3. D13–D20与L节、task7.4接口/经验池（I4）、task7.10输入（f_k字段D20）之间是否一致。
4. task7.10草案v1：离散SAC的Critic/Actor/温度损失、目标熵0.98·log K(x)是否与SRC-0382原文/官方代码一致（核对原文位置，未读原文须写明）；掩码处理（无效候选在π、V̄、熵中的处理）是否自洽；半马尔可夫折扣γ^(Δt/τ)中Δt、τ的口径是否与父TASK §2.7及task7.13 L.6一致；截断自举与task7.4协议一致；SRC-0412对SC²-WM代码的行号与结论是否准确（只读scwm/ commit f2f2f5f核对），哪些写成“沿用SC²-WM”的实际是本项目合同。
5. “忠于三个原项目”：一致性表各行对原项目做法的描述是否有来源支撑、是否准确；被判为“保留现状”的偏离是否写明了理由与影响。
6. 主张—来源：Claude建议是否被写成用户决定，工程选择是否被写成证据，T1–T9是否被误写为已定。
7. 未经用户决定的语义改动（奖励、终止、动作、观测）或超出已定范围的新增功能/实验。

【输出】只写自己的日志：按编号列发现，每条含“位置（文件:行）—问题—建议改法—依据”，标严重程度（必须改/建议改/可选）；另列“已核对无问题”的要点。不修改任何task或共享文档（由Claude统一处理）；完成后把PROGRESS本行改为done（交付复核意见），写明开始/交付时间。

【禁止】不运行程序、容器、训练或评估；不修改代码、参考仓库（scwm/等只读），也不修改PROGRESS本行与自己日志以外的任何文件；不新增功能、实验或设计决定。
```

## B：阶段L与各组成本的静态推算（为U15预算提供依据）

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7-BUDGET-ESTIMATE-20261020。推荐模型GPT6.1sol、推理强度medium；在日志里写明你实际的模型与强度，无法核实写“未知”。

【先读】根 AGENTS.md（尤其“论据与引用来源”和“性能优化共同要求”第6条）；forem/doc/README.md；forem/doc/PROGRESS.md；forem/doc/tasks/task7/TASK.md（两层SAC入口节、§2.7、§3 U15、§4对照组G1–G7与预算段）；task7.4/RESULTS.md（文首修订节、§14–§18训练阶段与协议）；task7.13/RESULTS.md（L.4、L.6、L.8、L.9、D表）；task7.10/RESULTS.md（草案v1，候选数与推演次数）；task7.9/RESULTS.md（候选数）；task7.6/RESULTS.md（§5实测、§6成本扫描、§6R主方案成本公式、§7）；task5/task5.5/RESULTS.md（5M×3种子实测墙钟、步速与分阶段耗时）；SOURCES.md 的 SRC-0394、SRC-0399、SRC-0406、SRC-0407。

【开工登记】在 forem/doc/PROGRESS.md“项目级记录”表加一行（写前重读，保留他人内容）：TASK7-BUDGET-ESTIMATE-20261020｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/20261020-codex-budget-estimate.md。

【目的】U15（各组种子数、步数/决策数、阶段L预算）是task7当前主要待定项，需要用户决定。本任务只给出成本推算，供用户决定时参考，不替用户选定任何数值。

【要求】
1. 列出推算用到的每个输入：数值、单位、来源（SRC编号或文件:行）、测量条件（硬件、环境、是否含reset/评估/日志/检查点）。task5.5是CBL sim环境上的连续SAC，自写理想执行环境尚未实现：逐项说明哪些耗时可以沿用、哪些要换算、哪些未知，未知项给出区间并标“待验证假设”，不得写成实测。
2. 阶段L（下层SAC单独训练）：按每百万环境步给出墙钟（单种子）与累计worker耗时，分开写env步、IK/碰撞子步（0.05 s子步，每0.1 s两个）、渲染/扫描、update、reset，以及冻结验收（L.9）。周期换算与取整方式要写明。
3. 上层各组（G1–G6，以及G7）：按每万次上层决策给出成本，包括每次决策对K个候选的冻结下层确定性推演（以task7.6 §6R公式为基础核算，K取task7.9/task7.10的设定，未定时给几档）、执行段的底层步数、上层update、f_p训练与偏置层（G4等）。同步与不同步两种变体分开列。
4. 汇总成参数化表：若干档“种子数×阶段L步数×上层决策数”组合下的全局墙钟与累计worker耗时，说明可用GPU/CPU数与并行假设（以 forem/ENV.md 和 task7.6 §7 已记录的为准，不自行实测）。不得把理论多卡算力写成工期承诺。
5. 列出最影响总成本的前3项因素，以及正式长训前需要哪些有界性能核查才能把区间收窄（只列，不执行）。

【登记】推算整体在 SOURCES.md 末尾新增一个条目（写前重读文件取当时最大编号+1，类型写“推导＋待验证假设”，列输入来源、公式、单位、条件、限制，核查人写Codex及实际模型）。不修改task7及子任务的三文档（由Claude回写）。完成后把PROGRESS本行改为done（交付推算），写明开始/交付时间。

【禁止】不运行程序、容器、基准、训练或评估；不修改代码与参考仓库；不修改SOURCES新增条目、PROGRESS本行与自己日志以外的任何文件；不设定或推荐超出已定范围的新实验组、不自行缩减步数或放宽验收。
```
