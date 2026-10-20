# task6 Task4.8失败原因对照组 — 详细流程

状态：**尚未执行（2026-10-12重新开始）**。流程制定、资源协调、汇总与复核：Claude。子任务执行：Codex。

## 递归规则声明

本任务遵守根AGENTS的递归三文档规则：task6及其每个子任务task6.K（以及今后拆出的task6.K.M）都必须各有TASK、PROCEDURE、RESULTS三份文档。父节点只负责目标、顺序、依赖、资源协调和汇总，不代替子任务的实测；子任务的结果以各自RESULTS为准。子Agent只更新自己子任务的文档和日志；父RESULTS由Claude汇总。子Agent自报完成不能直接当作通过，须经Claude复核。

## 子任务、顺序与依赖

|编号|三文档|负责人|依赖|验收关系|
|---|---|---|---|---|
|task6.1 ScwmSAC sim组|[TASK](task6.1/TASK.md) · [PROCEDURE](task6.1/PROCEDURE.md) · [RESULTS](task6.1/RESULTS.md)|Codex（会话1）|无|提供F0–F6结果和两侧最终评估|
|task6.2 RLlib Gazebo组|[TASK](task6.2/TASK.md) · [PROCEDURE](task6.2/PROCEDURE.md) · [RESULTS](task6.2/RESULTS.md)|Codex（会话2）|无；正式训练须等task5 A/B训练退出|提供G-B结果|
|task6.3 sim策略Gazebo零样本迁移|[TASK](task6.3/TASK.md) · [PROCEDURE](task6.3/PROCEDURE.md) · [RESULTS](task6.3/RESULTS.md)|Codex（用户派发）|task6.1 done；与task6.2独立，可并行|提供Z-A/Z-B结果，判断“在Gazebo里训练”与“Gazebo执行”哪个是主因|
|task6.4 task5 A/B按原论文Gazebo零样本评估|[TASK](task6.4/TASK.md) · [PROCEDURE](task6.4/PROCEDURE.md) · [RESULTS](task6.4/RESULTS.md)|Codex（用户派发）|task5 A/B checkpoint；运行位置须与task5 D21、task6.2隔离|判断N²M²方法本身能否迁移，区分“我们的链路”与“Husky本身”|
|task6.5 原作者模型复现N²M²|[TASK](task6.5/TASK.md) · [PROCEDURE](task6.5/PROCEDURE.md) · [RESULTS](task6.5/RESULTS.md)|Codex（用户派发）|task6.4环境；A正式评估结束后|确认N²M²在我们环境中能否复现sim与Gazebo结果，为27个百分点损失的排查定基准|
|父汇总|本目录[RESULTS](RESULTS.md)|Claude|6.1–6.5均review|四组对照、F1–F6结论与迁移结论|

两个子任务互相独立（不同容器、不同代码副本、不同run-id前缀`t6.1-`/`t6.2-`），可以同时开工。各自的Claude门槛（6.1筛选后、6.2确定N时）通过用户转达。

## 资源与优先级

主机64核、251 GB内存、4块GPU。task5的A/B训练只用CPU，预计今天下午结束。

1. **CPU总预算**：本任务所有进程加上主机其他负载，持续不超过56核（沿用task5 D11告警线）。各子任务的profile须给出每条run/每个实例的实测CPU占用，以便统一分配。
2. **优先级**（从高到低）：
   1. task5 A/B训练（不得干预）；
   2. task6.1的F0三种子×100万步；
   3. task6.2的G-B正式训练（task5 A/B退出后）；
   4. task6.1的F1–F6筛选，用剩余容量；
   5. task6.1的确认训练（Claude门槛之后）。
   6. task6.3只做评估（约6个Gazebo实例、约12核），与G-B训练同时运行时合计仍低于预算；启动前读主机CPU，超出则分批（2026-10-13补充）。
   理由：F0和G-B是判断“Gazebo还是训练配方”的两条关键对照，F1–F6只在F0学不会时才是失败原因的答案。
3. **冲突处理**：后启动的一方在启动前读取当前主机CPU和另一子任务的RESULTS/监控记录；若加上自己会超出预算，则排队等待或缩小并行度（task6.1可减少同时运行的筛选run；task6.2不得自行减少worker，须报告Claude）。不得为了腾资源停止别的任务。
4. **GPU**：task6.1使用forem-dev的GPU，task6.2的RLlib训练沿用B的`num_gpus 0`（CPU训练），不占GPU。

## 父节点汇总（Claude，两个子任务review后）

1. 核验两个子任务的RESULTS、manifest和原始记录，抽查关键数字（成功率由原始评估记录重新计算）。
2. 在父RESULTS中给出：
   - 四组对照表：R-B（task5.2训练中评估）、R-48（Task4.8验证及6.1的Gazebo侧最终评估）、F0（6.1）、G-B（6.2），注明各自评估口径；
   - F1–F6筛选表与确认结果；
   - 按TASK解读表给出结论、置信程度和限制。
3. 新论据登记SOURCES，更新PROGRESS和DECISIONS（如形成确定决策）。

## 历史

原task6（R0–R3，单因素对照→对照组改造）和原task7（B改在Gazebo）的文档已存档于[archive-20261012-pre-restart](../../agent_logs/task6/archive-20261012-pre-restart/)。原task6 §1预检的证据（`results/task6/baseline_source_diff.json`、`t6-preflight-r1`、`t6-d12-preflight-r1`）保留；新流程在task6.1 §1重新做基线冻结，不覆盖这些文件。

## 模型与推理强度

见[TASK](TASK.md#模型与推理强度推荐)。
