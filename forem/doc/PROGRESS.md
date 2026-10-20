# 当前进度

唯一活动进度表。状态：`active`执行中、`review`待核验、`blocked`明确依赖、`paused`用户要求暂停、`done`交付并验证完成、`closed`按用户指令结束、`draft`方向草案。

2026-10-16整理：旧进度表（925行，含task1/2、视觉惯性、旧Task4路线的全部历史）已替换为本精简版，原文见备份（[SRC-0321](SOURCES.md#src-0321)）；各任务的完整历史仍在其三文档与agent_logs中。

## 运行中

当前无本表登记的运行任务；task7.6基准已退出并清理，状态review（[SRC-0399](SOURCES.md#src-0399)）；task5.5训练与最终sim评估均已结束（[SRC-0394](SOURCES.md#src-0394)）。

- task7.6 IK与路径评估计时基准：**review**（TASK7.6-BENCH-20261020；Codex；开始2026-10-20T14:26:29.317991+08:00；交付2026-10-20T14:46:35.571249+08:00）。数值/CPU/GPU/顺序路径/BioIK参考及成本扫描已交付；已知奇异假阴性、分支/精度差与连续性跳变保留，B8/B13/B14/E7及求解器待用户决定；无环境实施、训练/评估或残留进程。[结果](tasks/task7/task7.6/RESULTS.md) / [日志](agent_logs/task7/task7.6/20261020-codex-ik-bench.md) / [SRC-0399](SOURCES.md#src-0399)。

## 阶段一：CBL复现

|任务|状态|待办|
|---|---|---|
|[task0](tasks/task0/RESULTS.md) 环境|done|—|
|[task3](tasks/task3/RESULTS.md) 核心迁移|done|—|
|[task4](tasks/task4/RESULTS.md) Gazebo普通SAC与首次WM|closed|—|
|[task5](tasks/task5/RESULTS.md) sim对照训练|5.0–5.3 done；[5.4](tasks/task5/task5.4/RESULTS.md) paused；[5.5](tasks/task5/task5.5/RESULTS.md) done|5.5最终sim评估内部成功32/33/30（各50，均值0.63；同批场景F0 1M为0.43），10-20 Claude复核通过（[SRC-0394](SOURCES.md#src-0394)）；Gazebo零样本评估需另行授权|
|[task6](tasks/task6/RESULTS.md) Gazebo失败诊断|6.1、6.3 done；[6.2](tasks/task6/task6.2/RESULTS.md) paused；[6.4](tasks/task6/task6.4/RESULTS.md)阶段一done、阶段二暂缓；[6.5](tasks/task6/task6.5/RESULTS.md)阶段一review|6.5阶段一待Claude复核；6.4/6.5阶段二待定|

## 阶段二：世界模型闭环

|任务|状态|待办|
|---|---|---|
|[task7](tasks/task7/TASK.md)|draft（框架已定，准备/设计子任务已建立；实施未授权）|10-19用户确认框架：规则候选点→每点多路径精确评估→离散SAC选点（零初始化门控偏置层接入f_p）→非学习执行器；准备子任务task7.4–7.12已建三文档（进度见task7 PROCEDURE）；task7.9草案v1已写，R1–R8待用户确认|

## 项目级记录（近期）

|任务ID|负责人|状态|记录|
|---|---|---|---|
|PROJECT-GIT-PUSH-20261020|Codex|active（2026-10-20T15:11:17+08:00开始；按用户要求提交并推送当前文件；只做Git同步及必要记录）|[记录](agent_logs/project/20261020-codex-git-push.md)|
|TASK7.6-BENCH-20261020|Codex|review（2026-10-20T14:46:35.571249+08:00交付；r1–r9有界基准、原件125项重算、清理/预算核查；非环境实施，待Claude/用户复核）|[日志](agent_logs/task7/task7.6/20261020-codex-ik-bench.md) · [结果](tasks/task7/task7.6/RESULTS.md) · [SRC-0399](SOURCES.md#src-0399)|
|TASK7-SECOND-REVIEW-A-20261019|Codex|done（2026-10-19T23:40:47+08:00开始；2026-10-19T23:54:56+08:00交付17项第二轮建议；仅只读核查与文档）|[记录](agent_logs/task7/20261019-codex-review-evidence.md)|
|TASK7-EVIDENCE-B-20261019|Codex|done（2026-10-20 Claude已采纳并写入task7文档，见[日志](agent_logs/task7/20261020-claude-second-review-fixes.md)；原记录：2026-10-19T23:40:47+08:00开始；2026-10-19T23:54:56+08:00八项核查/替换建议与SRC-0382–0390已交付；物理TCP等价未证实、R2D2原文未取得，官方代码已核）|[记录](agent_logs/task7/20261019-codex-review-evidence.md)|
|TASK7.6-DISPATCH-20261020|Claude（claude-opus-5-5）|review（2026-10-20 14:00起；task7.6派发提示已写、SRC-0398已登记；codex exec由用户启动（PID 1480576），Codex执行中；Claude不执行基准）|[派发日志](agent_logs/task7/task7.6/20261020-claude-codex-dispatch.md)|
|TASK7.9-RULE-SPEC-20261020|Claude（claude-opus-5-5）|review（2026-10-20T12:15–12:20+08:00；task7.9规则版规格(A)、改造方案(B)、子目标环暂缓条件(C)草案v1已写入三文档，来源SRC-0395–0397；R1–R8待用户确认；只写文档）|[日志](agent_logs/task7/task7.9/20261020-claude-rule-spec.md)|
|TASK5.5-FINAL-SIM-REVIEW-20261020|Claude（claude-opus-5-5）|done（2026-10-20T12:02–12:06+08:00；原件哈希、逐回合重算与F0同口径对照全部通过，task5.5标done，PLAN过时行已更正；只读结果、只写文档）|[日志](agent_logs/task5/task5.5/20261020-claude-final-sim-review.md)|
|TASK5.5-FINAL-SIM-RESULTS-20261020|Codex|done（2026-10-20T11:48:37+08:00开始；2026-10-20T11:55:08+08:00核对入账完成；task5.5为review待Claude/用户复核；仅文档，[SRC-0394](SOURCES.md#src-0394)）|[记录](agent_logs/task5/task5.5/20261020-codex-final-sim-results.md)|
|TASK5.5-FINAL-SIM-EVAL-20261019|Codex|done（10-19 22:52评估及实例清理结束；10-20本次结果入账，task5.5为review；[SRC-0394](SOURCES.md#src-0394)）|[记录](agent_logs/task5/task5.5/20261019-codex-final-sim-eval.md)|
|TASK5-CBL-STATUS-20261019|Codex|done（2026-10-19 22:40 +0800开始；已核对：5.2原版RLlib已评估，5.5自写SAC最终sim评估未执行；未启动实验）|[记录](agent_logs/task5/20261019-codex-cbl-status.md)|
|TASK7-STATUS-CHECK-20261019|Codex|done（2026-10-19 22:40–22:41 +0800；现状核查与汇总；未实施，未运行实验）|[记录](agent_logs/task7/20261019-codex-status-check.md)|
|TASK6.2-SAMPLER-STOP-20261020|Claude（claude-opus-5-5）|done（2026-10-20 13:19–13:22；按用户指示核实t6.2-stress-r2遗留CPU采样器无人使用后只停该进程（宿主PID 2994901），输出文件保留，容器未动）|[日志](agent_logs/task6/task6.2/20261020-claude-stop-stress-r2-sampler.md)|
|TASK5.5-DISPATCH-PROMPT-20261020|Claude（claude-opus-5-5）|done（2026-10-20；写好给Codex的派发提示：task5.5最终sim评估结果入账、PROGRESS更新、与F0同口径对照；Claude未派发，待用户转交）|[派发提示](agent_logs/task5/task5.5/20261020-claude-codex-dispatch-prompt.md)|
|TASK7-SECOND-REVIEW-FIXES-20261020|Claude（claude-opus-5-5）|done（2026-10-20 11:17–11:21改文档，11:32写入用户对距离锚点、终点姿态、风险特征定义的决定SRC-0393；只写文档）|[日志](agent_logs/task7/20261020-claude-second-review-fixes.md)|
|TASK7.4-CONTRACT-GAPS-20261020|Claude（claude-opus-5-5）|done（2026-10-20 11:10–11:12；用户决定合同缺口7–11按Claude推荐，写入task7.4/7.5/7.8/父TASK/DECISIONS并登记来源；只写文档）|[日志](agent_logs/task7/task7.4/20261020-claude-contract-gaps.md)|
|TASK7-CODEX-REPLY-ENVSPEC-20261019|Claude（claude-opus-5-5）|review（2026-10-19 21:40–21:51；Codex 7条意见的措辞修订完成；task7.5(B)规格草案v1已写，B1–B14待用户确认；只写文档）|[日志](agent_logs/task7/20261019-claude-codex-reply-and-env-spec.md)|
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
|TASK7.4-TASKDEF-20261019|Claude（claude-opus-5-5）|review（2026-10-19 19:45开始；任务定义、接口表与经验池字段草案v1已写；数值E1–E9与接口问题I1–I5待定）|[日志](agent_logs/task7/task7.4/20261019-claude-task-definition.md) · [task7.4](tasks/task7/task7.4/TASK.md)|
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
