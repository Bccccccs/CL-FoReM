# 当前进度

唯一活动进度表。状态：`active`执行中、`review`待核验、`blocked`明确依赖、`paused`用户要求暂停、`done`交付并验证完成、`closed`按用户指令结束、`draft`方向草案。

2026-10-16整理：旧进度表（925行，含task1/2、视觉惯性、旧Task4路线的全部历史）已替换为本精简版，原文见备份（[SRC-0321](SOURCES.md#src-0321)）；各任务的完整历史仍在其三文档与agent_logs中。

## 运行中

当前无本任务运行程序（2026-10-21T00:51:39+08:00收尾核查：forem-dev只原入口与sleep，GPU均14MiB/0%）。task7.14 r2已补完P1–P7，73项测试通过，完整几何/CPU64对照/E=1/16/64/256有界计时已记录，状态review，待Claude复核（[SRC-0428](SOURCES.md#src-0428)）。G1部分姿态原点与胶囊相交已报告，未移动传感器。

- task7.6 IK与路径评估计时基准：**done**（2026-10-20T21:35 Claude复核通过：清单哈希与关键数字从原始数组重算一致；开放项已由N1/SRC-0418定下或转入task7.14测试）。[结果](tasks/task7/task7.6/RESULTS.md)（末节“Claude复核”）。

## 阶段一：CBL复现

|任务|状态|待办|
|---|---|---|
|[task0](tasks/task0/RESULTS.md) 环境|done|—|
|[task3](tasks/task3/RESULTS.md) 核心迁移|done|—|
|[task4](tasks/task4/RESULTS.md) Gazebo普通SAC与首次WM|closed|—|
|[task5](tasks/task5/RESULTS.md) sim对照训练|5.0–5.3 done；[5.4](tasks/task5/task5.4/RESULTS.md) paused；[5.5](tasks/task5/task5.5/RESULTS.md) done|5.5最终sim评估内部成功32/33/30（各50，均值0.63；同批场景F0 1M为0.43），10-20 Claude复核通过（[SRC-0394](SOURCES.md#src-0394)）；Gazebo零样本评估需另行授权|
|[task6](tasks/task6/RESULTS.md) Gazebo失败诊断|6.1、6.3 done；[6.2](tasks/task6/task6.2/RESULTS.md) paused；[6.4](tasks/task6/task6.4/RESULTS.md)阶段一done、阶段二暂缓；[6.5](tasks/task6/task6.5/RESULTS.md) closed（10-20用户：不再继续，[SRC-0422](SOURCES.md#src-0422)）|6.4阶段二待定|

## 阶段二：世界模型闭环

|任务|状态|待办|
|---|---|---|
|[task7](tasks/task7/TASK.md)|draft；**[task7.14](tasks/task7/task7.14/TASK.md)环境核心已授权**（[SRC-0419](SOURCES.md#src-0419)）|2026-10-21 09:50：后续实施已授权（[SRC-0431](SOURCES.md#src-0431)）：task7.15候选生成器、7.16地图生成器与地图池、7.17回合环境可并行派发；7.18阶段L（两变体各1种子×5M）待前三者done；7.19 G7与冻结验收待G7设计。2026-10-21：**task7.14环境核心已实现并复核done**（`forem/src/task7_sim`，73项测试；G1遮挡已定先不改、阶段L统计，SRC-0429）。下一实施任务（task7.9规则候选生成器、阶段L下层SAC网络与训练）需另行授权；训练前须补C类项（冻结验收分母与配对、G6多地图状态隔离、G7预算）。此前：2026-10-21 00:51现状：两层SAC框架（[SRC-0400](SOURCES.md#src-0400)、[SRC-0401](SOURCES.md#src-0401)）下task7.4/7.5/7.7–7.11/7.13规格v1均已写，用户决定项已定（N1–N12、D1–D20、T1–T9、F1–F9、R1–R8、冻结前B类；SRC-0408–0418）；task7.6 done；task7.14 G1–G3已定（[SRC-0421](SOURCES.md#src-0421)），**环境核心r2已实施，73项测试通过，review待Claude复核**（详task7.14 RESULTS）；训练前须补C类项（冻结验收分母与配对、G6多地图状态隔离、G7预算）；候选生成器、网络与训练需另行授权；task7.12暂缓|

## 实验主线

尚未开始（2026-10-21建立入口，[experiments/](experiments/README.md)，[SRC-0430](SOURCES.md#src-0430)）。

## 论文主线

尚未开始（2026-10-21建立入口，[paper/](paper/README.md)，[SRC-0430](SOURCES.md#src-0430)）。

## 项目级记录（近期）

|任务ID|负责人|状态|记录|
|---|---|---|---|
|PROJECT-DOC-MAINLINES-20261021|Claude（claude-opus-5-5）|done（2026-10-21；按用户指令把文档分为项目/实验/论文三条主线：新建experiments/与paper/入口README，更新doc README、PROGRESS、AGENTS、DECISIONS、SRC-0430；只写文档，未设计具体实验或论文内容）|[日志](agent_logs/project/20261021-claude-doc-mainlines.md)|
|TASK7-IMPL-SETUP-20261021|Claude（claude-opus-5-5）|done（2026-10-21T09:30–09:50；用户授权后续实施（SRC-0431）：建task7.15–7.19三文档、父PROCEDURE表、7.15–7.17派发提示（可并行）；7.18待前三者done、7.19待G7设计；只写文档）|[日志](agent_logs/task7/20261021-claude-impl-setup.md) · [派发提示](agent_logs/task7/20261021-claude-codex-dispatch-7.15-7.17.md)|
|TASK7.14-ENVCORE-20261020|Codex|done（2026-10-21 Claude复核r2通过；原：review 2026-10-21T00:51:39+08:00；r2 P1–P7补完，73项通过；完整几何/CPU64对照/有界E扩展完成；累计1007.432s；SRC-0428）|[日志](agent_logs/task7/task7.14/20261020-codex-envcore.md) · [结果](tasks/task7/task7.14/RESULTS.md)|
|TASK7.14-REVIEW-R2-20261021|Claude（claude-opus-5-5）|done（2026-10-21T09:00–09:20；重跑73 passed；P5/P6/P3代码对照SRC-0425一致、信息隔离核对；记录“上臂–顶板”整对放行的漏检限制、G1遮挡报告与推演性能瓶颈；task7.14标done）|[复核](tasks/task7/task7.14/RESULTS.md) · [日志](agent_logs/task7/task7.14/20261021-claude-review-r2.md)|
|TASK7.14-REVIEW-R1-20261020|Claude（claude-opus-5-5）|done（2026-10-20T22:30–22:50；重跑46 passed；core.py对照L.0/L.3/D13–D20/N2/N4–N6无语义偏差；用户按推荐确定P1–P7（SRC-0425）；指出推演重复观测等性能风险；第二轮派发提示已写，由用户派发）|[日志](agent_logs/task7/task7.14/20261020-claude-review-r1.md) · [复核](tasks/task7/task7.14/RESULTS.md) · [派发提示](agent_logs/task7/task7.14/20261020-claude-codex-dispatch.md) · [SRC-0425](SOURCES.md#src-0425)|
|PROJECT-PROGRESS-AUDIT-20261020|Claude（claude-opus-5-5）|done（2026-10-20T21:25–21:40；进度审核；用户确认G1–G3（SRC-0421）、关闭task6.5（SRC-0422）；task7.6复核done；更正PROGRESS/PLAN/task7 TASK与PROCEDURE过时状态；只读核查与写文档）|[日志](agent_logs/project/20261020-claude-progress-audit.md)|
|TASK7-SPEC-FREEZE-REVIEW-20261020|Codex|done（交付复核意见；2026-10-20T20:33:37+08:00开始，20:44:08交付；18项：13必须改、5建议改；含上轮14项、一致性表26行与实现前接口缺口；仅本行和日志，未运行程序）|[日志](agent_logs/task7/20261020-codex-spec-freeze-review.md)|
|TASK7-SPEC-REVIEW3-20261020|Codex|done（2026-10-20T20:24:39+08:00开始，20:34:45交付；第三轮规格复核14项：8必须改、6建议改，含第二轮逐项核对；只写本行与日志，未运行程序）|[日志](agent_logs/task7/20261020-codex-spec-review3.md)|
|TASK7-BUDGET-ESTIMATE-20261020|Codex|done（交付推算；2026-10-20T20:24:37+08:00开始，20:34:35交付；输入/假设、L与冻结验收、G1–G7、两变体全局/worker参数表及有界核查清单；纳入收尾N1的DLS回退补算；未选预算、未运行实验，仅本行/日志/新增来源）|[日志](agent_logs/task7/20261020-codex-budget-estimate.md) · [SRC-0418](SOURCES.md#src-0418)|
|TASK7-REVIEW3-BUDGET-DISPATCH-20261020|Claude（claude-opus-5-5）|done（2026-10-20约20:20；写好两份Codex派发提示：A第三轮复核（D13–D20、忠于原项目、task7.10草案v1）、B阶段L与各组成本静态推算（供U15）；由用户派发，Claude未启动）|[派发提示](agent_logs/task7/20261020-claude-codex-dispatch-review3-budget.md)|
|TASK7-LOWER-SPEC-REVIEW-20261020|Codex|done（2026-10-20T17:06:01+08:00开始，17:13:19交付；D1–D12及上轮处理复核，14项意见：11必须改、3建议改；仅独立日志与本行，未运行程序）|[日志](agent_logs/task7/task7.13/20261020-codex-lower-spec-review.md)|
|TASK7.13-CBL-AUDIT-20261020|Codex|done（2026-10-20 Claude抽查复核采用，见task7.13 RESULTS；原记录：review（2026-10-20T16:26:04+08:00开始，16:37:42交付；CBL动作/时序IK/观测/奖励/实际SAC链路五项静态核查，含SRC-0401补充，待Claude复核；仅文档）|[日志](agent_logs/task7/task7.13/20261020-codex-cbl-audit.md) · [结果](tasks/task7/task7.13/RESULTS.md) · [SRC-0402–0406](SOURCES.md#src-0402)|
|TASK7-LOWER-SAC-REVIEW-20261020|Codex|done（2026-10-20T16:25:56+08:00开始，16:32:38交付；按SRC-0401及用户补充复核三维下层SAC，14项意见：9必须改、5建议改；仅独立日志与本行）|[日志](agent_logs/task7/20261020-codex-lower-sac-review.md)|
|TASK7.14-SETUP-20261020|Claude（claude-opus-5-5）|done（2026-10-20T21:03起；task7.14三文档、实现合同与Codex实施提示已写；G1–G3于21:35确认（SRC-0421）；只写文档）|[日志](agent_logs/task7/task7.14/20261020-claude-envcore-setup.md) · [派发提示](agent_logs/task7/task7.14/20261020-claude-codex-dispatch.md)|
|TASK7-SPEC-FREEZE-FIXES-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:49–20:55；B类5项登记SRC-0418；A类纠错与整合写入task7.13（L.0统一流程、f_k v1）、7.10（路由表、温度loss）、7.11（数据合同、触发谓词）、7.5（IK合同）、7.4、父TASK一致性表（#27、#28新增）与SOURCES更正；C类延后；只写文档）|[日志](agent_logs/task7/20261020-claude-spec-freeze-review-assessment.md#处理)|
|TASK7-SPEC-FREEZE-REVIEW-ASSESS-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:44；审核Codex第三轮18项：抽查6项源码均属实；分A类Claude直接修正、B类5项需用户决定、C类延后；只读与记录）|[日志](agent_logs/task7/20261020-claude-spec-freeze-review-assessment.md)|
|TASK7-SPEC-FREEZE-REVIEW-DISPATCH-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:32；写好Codex第三轮整体复核提示，由用户派发，Claude未启动）|[派发提示](agent_logs/task7/20261020-claude-codex-dispatch-review3.md)|
|TASK7-NUMBERS-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:25–20:32；N1–N12推荐写入task7.4 RESULTS（SRC-0416），用户“按照你的推荐”确定（SRC-0417），回写父TASK U15/§2.2/一致性表#8、task7.5 B.R、7.7 S1–S5、7.8 V4/V5、7.13 L.3；只写文档）|[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md)|
|TASK7.11-SPEC-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:11–20:18；核对SC²-WM预测损失与适应代码（SRC-0414），f_p训练方案v1；用户“忠于原项目”：F1–F9按忠于原项目选项确定、F7(b)、ψ保持代码形式（SRC-0415），回写父TASK与task7.4；只写文档）|[日志](agent_logs/task7/task7.11/20261020-claude-fp-spec.md)|
|TASK7.10-SPEC-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:06起；T1–T9已由用户确定（SRC-0413）并回写；核对SC²-WM打分结构（SRC-0412），task7.10上层离散SAC与偏置层规格草案v1写入RESULTS，T1–T9待用户确认；只写文档）|[日志](agent_logs/task7/task7.10/20261020-claude-upper-spec.md)|
|TASK7-FAITHFUL-20261020|Claude（claude-opus-5-5）|done（2026-10-20T19:53–20:03；D13–D20确定（D17/D18/D19按原则改取CBL做法）；三个原项目＝CBL、N²M²、SC²-WM（用户确认）；一致性表#5改回CBL、#6–#11保留（SRC-0410）；只写文档）|[日志](agent_logs/task7/task7.13/20261020-claude-lower-spec-review-fixes.md#d13d20确定与忠于原项目)|
|TASK7-LOWER-SPEC-REVIEW-FIXES-20261020|Claude（claude-opus-5-5）|done（2026-10-20T19:36–19:39；D13–D20已于19:53由用户确定；处理Codex第二轮14项：文字与公式更正已改入task7.13/7.4/7.6/7.10、父TASK、SOURCES、DECISIONS；接口补充D13–D20写入task7.13 RESULTS待用户确认；只写文档）|[日志](agent_logs/task7/task7.13/20261020-claude-lower-spec-review-fixes.md)|
|TASK7-LOWER-SPEC-REVIEW-DISPATCH-20261020|Claude（claude-opus-5-5）|done（2026-10-20T17:05；写好Codex第二轮复核提示，由用户派发，Claude未启动）|[派发提示](agent_logs/task7/task7.13/20261020-claude-codex-dispatch-review2.md)|
|TASK7-LOWER-SPEC-WRITEBACK-20261020|Claude（claude-opus-5-5）|done（2026-10-20T17:01–17:04；D1–D12登记SRC-0408与DECISIONS，回写父TASK、task7.4/7.5/7.6/7.10/7.13；只写文档）|[日志](agent_logs/task7/task7.13/20261020-claude-lower-spec.md#d1d12确定后的回写)|
|TASK7.13-SPEC-20261020|Claude（claude-opus-5-5）|done（2026-10-20T16:52起；D1–D12已由用户确定（SRC-0408）；复核Codex CBL核查并采用；task7.13下层规格草案v1写入RESULTS，SRC-0407登记；D1–D12待用户确认；只写文档）|[日志](agent_logs/task7/task7.13/20261020-claude-lower-spec.md)|
|TASK7-LOWER-SAC-REVIEW-FIXES-20261020|Claude（claude-opus-5-5）|done（2026-10-20T16:45–16:51；Codex两层SAC复核14项全部处理：父task7三文档、task7.4 TASK/RESULTS（文首修订节）、7.5/7.6/7.7/7.8/7.10/7.11/7.13 TASK、PLAN、DECISIONS、SRC-0400/0401更正与导航；新增待定U39与“同步上层奖励是否加时间项”；只改文档）|[日志](agent_logs/task7/20261020-claude-lower-sac-review-fixes.md)|
|TASK7-DEFAULTS-20261020|Claude（claude-opus-5-5）|done（2026-10-20；用户“都按你的推荐来”：下层3维动作、确定性执行、CBL自写SAC、下层无记忆与子目标均匀抽、task7.9 R1–R8、热力图处理写入task7文档，SRC-0401与DECISIONS登记；只写文档）|[日志](agent_logs/task7/20261020-claude-lower-sac.md#2026-10-20稍后用户按推荐确定的一批项)|
|TASK7.13-DISPATCH-20261020|Claude（claude-opus-5-5）|done（2026-10-20；写好两份Codex派发提示：A task7.13 CBL下层代码核查、B两层SAC文档复核；由用户派发，Claude未启动）|[派发提示](agent_logs/task7/task7.13/20261020-claude-codex-dispatch.md)|
|TASK7-LOWER-SAC-20261020|Claude（claude-opus-5-5）|done（2026-10-20T16:08起；用户决定两层SAC写入task7文档、新建task7.13、SRC-0400与DECISIONS登记；只写文档）|[日志](agent_logs/task7/20261020-claude-lower-sac.md)|
|PROJECT-GIT-PUSH-20261020|Codex|done（2026-10-20T15:12:00+08:00；当前文件提交2380ff5及此前42提交已推送origin/main，远程哈希一致；本条及日志作为收尾记录提交）|[记录](agent_logs/project/20261020-codex-git-push.md)|
|TASK7.6-BENCH-20261020|Codex|done（21:35 Claude复核通过；原：2026-10-20T14:46:35.571249+08:00交付；r1–r9有界基准、原件125项重算、清理/预算核查；非环境实施，待Claude/用户复核）|[日志](agent_logs/task7/task7.6/20261020-codex-ik-bench.md) · [结果](tasks/task7/task7.6/RESULTS.md) · [SRC-0399](SOURCES.md#src-0399)|
|TASK7-SECOND-REVIEW-A-20261019|Codex|done（2026-10-19T23:40:47+08:00开始；2026-10-19T23:54:56+08:00交付17项第二轮建议；仅只读核查与文档）|[记录](agent_logs/task7/20261019-codex-review-evidence.md)|
|TASK7-EVIDENCE-B-20261019|Codex|done（2026-10-20 Claude已采纳并写入task7文档，见[日志](agent_logs/task7/20261020-claude-second-review-fixes.md)；原记录：2026-10-19T23:40:47+08:00开始；2026-10-19T23:54:56+08:00八项核查/替换建议与SRC-0382–0390已交付；物理TCP等价未证实、R2D2原文未取得，官方代码已核）|[记录](agent_logs/task7/20261019-codex-review-evidence.md)|
|TASK7.6-DISPATCH-20261020|Claude（claude-opus-5-5）|done（Codex已交付，task7.6 done；原：2026-10-20 14:00起；task7.6派发提示已写、SRC-0398已登记；codex exec由用户启动（PID 1480576），Codex执行中；Claude不执行基准）|[派发日志](agent_logs/task7/task7.6/20261020-claude-codex-dispatch.md)|
|TASK7.9-RULE-SPEC-20261020|Claude（claude-opus-5-5）|done（R1–R8已由用户确定，SRC-0401；原：2026-10-20T12:15–12:20+08:00；task7.9规则版规格(A)、改造方案(B)、子目标环暂缓条件(C)草案v1已写入三文档，来源SRC-0395–0397；R1–R8待用户确认；只写文档）|[日志](agent_logs/task7/task7.9/20261020-claude-rule-spec.md)|
|TASK5.5-FINAL-SIM-REVIEW-20261020|Claude（claude-opus-5-5）|done（2026-10-20T12:02–12:06+08:00；原件哈希、逐回合重算与F0同口径对照全部通过，task5.5标done，PLAN过时行已更正；只读结果、只写文档）|[日志](agent_logs/task5/task5.5/20261020-claude-final-sim-review.md)|
|TASK5.5-FINAL-SIM-RESULTS-20261020|Codex|done（2026-10-20T11:48:37+08:00开始；2026-10-20T11:55:08+08:00核对入账完成；task5.5为review待Claude/用户复核；仅文档，[SRC-0394](SOURCES.md#src-0394)）|[记录](agent_logs/task5/task5.5/20261020-codex-final-sim-results.md)|
|TASK5.5-FINAL-SIM-EVAL-20261019|Codex|done（10-19 22:52评估及实例清理结束；10-20本次结果入账，task5.5为review；[SRC-0394](SOURCES.md#src-0394)）|[记录](agent_logs/task5/task5.5/20261019-codex-final-sim-eval.md)|
|TASK5-CBL-STATUS-20261019|Codex|done（2026-10-19 22:40 +0800开始；已核对：5.2原版RLlib已评估，5.5自写SAC最终sim评估未执行；未启动实验）|[记录](agent_logs/task5/20261019-codex-cbl-status.md)|
|TASK7-STATUS-CHECK-20261019|Codex|done（2026-10-19 22:40–22:41 +0800；现状核查与汇总；未实施，未运行实验）|[记录](agent_logs/task7/20261019-codex-status-check.md)|
|TASK6.2-SAMPLER-STOP-20261020|Claude（claude-opus-5-5）|done（2026-10-20 13:19–13:22；按用户指示核实t6.2-stress-r2遗留CPU采样器无人使用后只停该进程（宿主PID 2994901），输出文件保留，容器未动）|[日志](agent_logs/task6/task6.2/20261020-claude-stop-stress-r2-sampler.md)|
|TASK5.5-DISPATCH-PROMPT-20261020|Claude（claude-opus-5-5）|done（2026-10-20；写好给Codex的派发提示：task5.5最终sim评估结果入账、PROGRESS更新、与F0同口径对照；Claude未派发，待用户转交）|[派发提示](agent_logs/task5/task5.5/20261020-claude-codex-dispatch-prompt.md)|
|TASK7-SECOND-REVIEW-FIXES-20261020|Claude（claude-opus-5-5）|done（2026-10-20 11:17–11:21改文档，11:32写入用户对距离锚点、终点姿态、风险特征定义的决定SRC-0393；只写文档）|[日志](agent_logs/task7/20261020-claude-second-review-fixes.md)|
|TASK7.4-CONTRACT-GAPS-20261020|Claude（claude-opus-5-5）|done（2026-10-20 11:10–11:12；用户决定合同缺口7–11按Claude推荐，写入task7.4/7.5/7.8/父TASK/DECISIONS并登记来源；只写文档）|[日志](agent_logs/task7/task7.4/20261020-claude-contract-gaps.md)|
|TASK7-CODEX-REPLY-ENVSPEC-20261019|Claude（claude-opus-5-5）|done（B1–B14已由用户确定，SRC-0377/0378/0381；原：2026-10-19 21:40–21:51；Codex 7条意见的措辞修订完成；task7.5(B)规格草案v1已写，B1–B14待用户确认；只写文档）|[日志](agent_logs/task7/20261019-claude-codex-reply-and-env-spec.md)|
|TASK7-CODEX-SUPERVISION-20261019|Claude（claude-opus-5-5）|done（2026-10-19 21:21–21:30只读核查task7.5(A)与7.1–7.3收尾；2026-10-20复查：task5.5最终sim评估10-19 22:52已结束rc=0、内部成功32/33/30（/50），但结果未入账、PROGRESS未更新；Codex第二轮17项待Claude处理；10-20 13:20复查：Codex task5.5入账11:55完成、数字与哈希经抽查一致，已由Claude复核标done）|[记录](agent_logs/task7/20261019-claude-codex-supervision.md)|
|TASK7.5-A-REUSE-AUDIT-20261019|Codex|done（2026-10-19 20:55–21:15 +0800；a–g静态复用审计、SRC-0365–0371、文档核对完成；(B)未写，未运行程序）|[记录](agent_logs/task7/task7.5/20261019-codex-reuse-audit.md)|
|TASK7.1-7.3-CLOSEOUT-20261019|Codex|done（2026-10-19 20:55–21:15 +0800；SRC-0341–0355补登、父抽查、日志与新框架适用性收尾；仅文档验收）|[记录](agent_logs/task7/20261019-codex-research-closeout.md)|
|PROJECT-MAPGEN-AGENTS-20261016|Codex|done（新增mapgen/AGENTS.md；静态文档检查通过，入口因宿主缺numpy未运行成功）|[记录](agent_logs/project/20261016-codex-mapgen-agents.md)|
|PROJECT-WM-RL-LITERATURE-20261014|Codex|review|[文献笔记](agent_logs/project/20261014-codex-wm-rl-literature.md)|
|PROJECT-SC2WM-SENSORS-20261016|Codex|done（2026-10-16 15:15 +08:00开始；平台与传感器只读核查）|[记录](agent_logs/project/20261016-codex-scwm-sensors.md)|
|PROJECT-SC2WM-READING-20261016|Codex|done|[阅读笔记](agent_logs/project/20261016-codex-sc2wm-reading.md)|
|CBL-ARCHIVE-AUDIT-20261016|Claude|done（只读核查与复核）|[核查](agent_logs/project/20261016-claude-cbl-archive-audit.md) · [复核](agent_logs/project/20261016-claude-cbl-archive-recheck.md)|
|DOC-CLEANUP-20261016|Claude（claude-opus-5-5）|done|[日志](agent_logs/project/20261016-claude-doc-cleanup.md)|
|MAPGEN-REQ-20261016|Claude（claude-opus-5-5）|done（需求文档交付；地图未生成）|[需求文档](../../mapgen/docs/husky_ur5_map_requirements.md) · [task7 RESULTS](tasks/task7/RESULTS.md)|
|DOC-FIX-20261019|Claude（claude-opus-5-5）|done|[日志](agent_logs/project/20261019-claude-doc-fix.md)|
|TASK7-CLAUDE-CODEX-SYNC-20261019|Claude（claude-opus-5-5）|done（Codex已于21:15回复7条意见与Q4；另一Claude会话21:40–21:51已按意见修订措辞）|[记录](agent_logs/task7/20261019-claude-codex-sync.md)|
|TASK7-FRAMEWORK-DOCS-20261019|Claude（claude-opus-5-5）|done（2026-10-19 19:03–19:35；框架写入与task7.4–7.12三文档，未派发未运行）|[日志](agent_logs/task7/20261019-claude-framework-docs.md)|
|TASK7.4-TASKDEF-20261019|Claude（claude-opus-5-5）|done（草案已交付，后续数值由N1–N12定，SRC-0417；原：2026-10-19 19:45开始；任务定义、接口表与经验池字段草案v1已写；数值E1–E9与接口问题I1–I5待定）|[日志](agent_logs/task7/task7.4/20261019-claude-task-definition.md) · [task7.4](tasks/task7/task7.4/TASK.md)|
|TASK7.7-MAPGEN-REQ-20261019|Claude（claude-opus-5-5）|done（2026-10-19；mapgen需求改为只生成长方体、每档验证50/测试100、B类不做；未生成地图）|[日志](agent_logs/task7/task7.7/20261019-claude-mapgen-req-update.md) · [需求文档](../../mapgen/docs/husky_ur5_map_requirements.md)|
|TASK7.7-OBS-20261019|Claude（claude-opus-5-5）|done（2026-10-19；全景深度、128×128×2局部栅格、所有障碍挡底盘已定；S1–S5待定）|[日志](agent_logs/task7/task7.7/20261019-claude-scan-design.md) · [task7.7 RESULTS](tasks/task7/task7.7/RESULTS.md)|
|TASK7.8-VCM-20261019|Claude（claude-opus-5-5）|done（2026-10-19；VCM方案V1–V3已定，V4网络尺寸、V5是否单独检验待定）|[日志](agent_logs/task7/task7.8/20261019-claude-vcm-design.md) · [task7.8 RESULTS](tasks/task7/task7.8/RESULTS.md)|
|TASK7.5-B-ITEMS-20261019|Claude（claude-opus-5-5）|done（2026-10-19 22:35起；B2、B3（SRC-0377）、B11（SRC-0378）、B1/B4–B10/B12–B14与地图大小（SRC-0381）已定；B8/B9/B13/B14与各数值交task7.6）|[日志](agent_logs/task7/task7.5/20261019-claude-b-items.md)|

|TASK7-DESIGN-REVIEW-20261019|Codex|done（2026-10-19 09:54 +0800开始；整体实验设计文档审查完成，未实施）|[记录](agent_logs/task7/20261019-codex-design-review.md)|

|TASK7-SEQUENCE-RESEARCH-20261019|Codex（父；上午3个调研子Agent，本次未再委派）|done（2026-10-19 10:04开始，21:15收尾；task7.1–7.3来源登记/父抽查/新框架适用性完成；仅调研文档）|[记录](agent_logs/task7/20261019-codex-sequence-design.md)；本次[收尾](agent_logs/task7/20261019-codex-research-closeout.md)|
|TASK7-CLAUDE-DISCUSSION-20261019|Claude（claude-opus-5-5）|done（仅讨论与只读核查；未重复派子Agent）|[记录](agent_logs/task7/20261019-claude-design-discussion.md)|

|PROJECT-N2M-READING-20261019|Codex|done（2026-10-19 16:47 +0800开始；原文核查与来源登记完成，未实施）|[记录](agent_logs/project/20261019-codex-n2m-pose-preference.md)|

## 容器

`forem-dev`（task5.5训练已结束，10-19无训练进程）；task5/6另有上游与Husky原版容器，使用前先核实状态，不停止未经核实的进程。
