# task5 N²M²上游与Husky原版的sim模式对照训练 — 结果与交接

> **当前状态（2026-10-20核对）：5.0–5.3 done；5.4 paused；5.5 done（最终sim评估已入账并经Claude复核）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

> **阶段一（CBL复现）· sim对照训练**（2026-10-16归类）：5.0–5.3 done——上游N²M² PR2 9任务sim平均0.856（原文0.882）；CBL原版RLlib（B）simpleobstacle 0.78、8任务平均0.248。5.4（B 5M）paused。**5.5 done**：cbl自写SAC sim 5M×3种子，最终sim评估（2001–2050）内部成功32/33/30（/50，均值0.63），同批场景F0 1M为0.43（描述性，未做显著性检验）；与RLlib约0.78口径不同，不直接比较（[task5.5 RESULTS](task5.5/RESULTS.md#claude独立复核2026-10-20)、[SRC-0394](../../SOURCES.md#src-0394)）。

状态：**done（2026-10-14 task5.3 R13最终复核通过：A 9任务sim平均0.856对原文88.2%；B simpleobstacle 0.78、8任务平均0.248）**。原状态：**review（A/B最终sim评估已按D21/D22/D23交付，待Claude5.3最终复核）**。本文件汇总子任务的结果，不替代子RESULTS。

## 子任务状态

|节点|状态|结果|
|---|---|---|
|task5.0|done（Claude R4）|[RESULTS](task5.0/RESULTS.md)|
|task5.1|review（最终评估交付，待5.3）|[RESULTS](task5.1/RESULTS.md)|
|task5.2|review（最终评估交付，待5.3）|[RESULTS](task5.2/RESULTS.md)|
|task5.3|review（R12决策交付；最终复核待执行）|[RESULTS](task5.3/RESULTS.md)|
|task5.4|尚未执行（2026-10-14追加：B 5M＋性能优化，文档交付）|[RESULTS](task5.4/RESULTS.md)|

## 已完成的准备（Claude，2026-10-11）

- 克隆上游`robot-learning-freiburg/mobile-rl`到`mobile-rl/`，HEAD为6281205846b1bac4525d05ee230a47bddf42023d。
- 后台启动`docker pull dhonerkamp/mobile_rl:11.1-latest`，日志在`forem/logs/task5/t5-image-pull.log`；完成情况待执行者核实。
- 编写task5及5.0–5.3三文档（5.0于2026-10-11按用户要求从5.1/5.2拆出），登记[SRC-0198](../../SOURCES.md#src-0198)–[SRC-0201](../../SOURCES.md#src-0201)，并写好[交接提示词](../../agent_logs/task5/20261011-claude-task5-handoff-prompt.md)。

## 汇总表（由task5.3填写）

|对照|机器人|环境|步数|训练中验证|最终9任务sim平均成功率|原文表III|
|---|---|---|---|---|---|---|
|A|PR2|sim|100万|待填|待填|88.2%（5种子平均）|
|B|husky_ur5|sim|100万|待填|待填|无|
|参照：Task4.8|husky_ur5|Gazebo|100万|物理成功0/5|未做|—|

## 交接

目标与授权见[TASK](TASK.md)。当前负责人：Claude负责流程，Codex拟执行（尚未派发）。下一步：用户派发Codex执行5.1→5.2。

## 执行状态同步 2026-10-11T23:15:17.578172+08:00

上述准备/原交接中的“尚未派发”为历史；当前Codex实施5.1/5.2、Claude决策/复核。5.0经R4 done，A/B均已正式启动；表中100万为协议目标，实际进度见各节点原trial/监控，不能当已达成。R7/D11只告警不自动停训练，A原PID34861保持，B PID36511；D10 bookstore不挡B冒烟，最终原逻辑30min/N/A与8/9口径。父只汇总子RESULTS，不另维护一套参数结果。来源[SRC0221](../../SOURCES.md#src-0221)。
模型推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（跨合同/运行核验），監控gpt-6.1-sol/low；主会话实际精确型号/强度未知，子Agent派发低档已记录，推荐不等于实际。

## 状态同步（Claude，2026-10-13 14:4x）

- A、B正式训练均已结束，退出码0，100万步。训练中评估最后读数：A 0.80（97.5万步）、B 0.76（90万步）。
- 最终9任务评估均中断，`posttrain_status.json`为blocked：A于2026-10-12 16:40在door任务失败，B于18:12在spline任务失败，原因都是上游评估脚本的断言`EPISODE OF 20001 STEPS!`（单个episode超过20000步）。当时Codex额度耗尽，无人处理。
- 已完成任务的成功率（只从`logs/task5/t5.{1,2}-eval-r1/eval-*.log`末行粗读，未经task5.3复核）：A simpleobstacle 0.78、picknplace 0.98、dynobstacle 0.78、picknplacedyn 0.74、bookstorepnp 0.70；B simpleobstacle 0.78、door 0.26、drawer 0.20、dynobstacle 0.44、picknplacedyn 0.14、picknplace 0.08、roomdoor 0.00，bookstorepnp未读到。
- 待决：如何处理超长episode断言并补完剩余任务（A：door、drawer、roomdoor、spline；B：spline，及bookstorepnp结果核实），之后task5.3复核。尚未派发。

## D21执行收尾（2026-10-14T00:57:15.939110+08:00）

Codex使用新r2，保留r1/原模型/源码/训练历史。A核查8回合退出0、成功8/8，但3个步数不符，按D21停止，不运行后续、不拼接。[SRC-0260](../../SOURCES.md#src-0260)。B独立核查符合R11并补齐spline0/50（47自然失败+3超限失败），但原r1 W&B导出checksum断言rc1，按未覆盖异常停止，9任务原始指标核验/最终汇总尚未完成。[SRC-0263](../../SOURCES.md#src-0263)

当前5.1/5.2均blocked，交Claude决定两项阻塞，不标review/done。B旧stdout标准picknplace8/50/fwdO4/50，上方2026-10-13粗读0.08对应fwdO；r1原始指标交叉核验仍待处理。命令/证据/剩余事项以子RESULTS为准。无运行评估、原ROS保留、CPU300样本无>56，task6.2/forem-dev不触碰。推荐GPT6.1sol/Sonnet5.5 medium核查、文档low/默认；实际模型/强度未知。

## 2026-10-14T08:54:42.608553+08:00 D22/D23最终交接

A九任务标准朝向均值85.555556%；B八可运行均值24.75%，9任务含bookstorepnp N/A、完整九均值N/A。两子节点review，最终事实与限制以其RESULTS/最终JSON为准；Claude5.3独立复核待执行，不标done。[SRC-0268](../../SOURCES.md#src-0268)。
