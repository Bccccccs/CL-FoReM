# DOCS-028 文档架构调整与清理

- 执行Agent：Claude Opus 5.5 /ybc
- 开始：2026-09-28T15:44+08:00
- 状态：review（AGENTS.md 同步待用户处理，其余完成）
- 用户要求：“现有的流程组织架构……太乱了……你做一下调整，并写一份提示词告诉别的agent做了什么调整”；“没有用的就清理”；“一些和现有决策冲突的旧决策也删除”；“stage 0被我停止了，你消除一下他的残留进程和不完整数据，调整好我们的组织结构，然后再开始执行”。

## 做了什么

1. 新建 [ROADMAP.md](../ROADMAP.md)：唯一执行计划（方法、整体流程、Stage0–3 每阶段的实验/对照/规模/预登记判据、F1 设计冻结、种子登记、编号字典）。LOGIC-028 的 L1/L2 并入 R0-3/R0-4 判据，L4/L5/L7 列为 F1 必答项。
2. 重写 [README.md](../README.md)：先看 ROADMAP/PROGRESS/AGENTS；文档分“维护中/参考/历史”三类。改前副本在会话 scratchpad。
3. 参考文档顶部加定位横幅：SYSTEM_PIPELINE、WM_RESEARCH_DESIGN、RESEARCH_GOAL、RESEARCH_EXPERIMENTS、EVALUATION、P0/PLAN、P1–P5。
4. 归档（移动，不删除）到 `archive/20260928-docs028/`：REVIEW、WORKFLOW_GUIDE（已并入 ROADMAP）、P0_ACCEPTANCE、P0_BASELINE、NODE01_DOCKER_ADMIN、P0/REMEDIATION_PLAN；修正 README、P0/README 中的链接。
5. [PROGRESS](../PROGRESS.md)：顶部加看板；42 行任务内容不改，分为“进行中/待验收”(9)、“已完成”(27)、“旧阶段行”(6)；RUNPLAN-028 标为已并入 ROADMAP。改前副本在 scratchpad。
6. [DECISIONS](../DECISIONS.md)：新增 D40；把与现行决策冲突的 D02、D10、D14、D25、D26、D28、D29、D30 移到 [DECISIONS-superseded.md](../archive/20260928-docs028/DECISIONS-superseded.md)（原文及取代关系保留，编号不复用）；D27 只加注释（其测试集已被 D32 取代，训练配置仍为 D36 所用）。改前副本在 scratchpad。
7. 清理：删除 11 个已退出的 `mmhusky-p1-*` 容器（P1-FIX/RETRAIN 已完成，结果与日志均在 results/）；删除 `agent_logs/__pycache__`。运行中的 `mmhusky-node01`、`mmhusky-node01-gz` 未动。
8. Stage0 残留清理（详见 [STAGE0-028 日志](20260928-stage0.md)）：停止并删除 `mmhusky-r0-wm-s22/s33`，删除其半成品输出；未完成的失配代码备份为 patch 后还原。

## 未完成

- AGENTS.md 的“开工前必读”应加入 ROADMAP，§3 中 REVIEW 链接已失效，§4 阶段表应改为指向 ROADMAP。本 Agent 读取该段时被权限规则拒绝，未修改，待用户处理或授权。

## 给其他 Agent 的说明（提示词）

```text
【项目文档结构已于 2026-09-28 调整（DOCS-028 / D40），开工前请先读本说明】

1. 唯一执行计划是 doc/ROADMAP.md。做什么、按什么顺序、每阶段的实验/对照组/规模（种子×步数×回合）/预登记判据/决策点、种子登记，都以它为准。其他文档与之冲突时，以 ROADMAP 和 DECISIONS 最新条目为准。
2. 开工顺序：AGENTS.md（硬规则）→ doc/README.md（文档分类）→ doc/ROADMAP.md → doc/PROGRESS.md 顶部看板 → doc/DECISIONS.md → 与任务相关的参考文档。
3. 流程：Stage0 前置验证 → G0 → F1 设计冻结（需用户确认）→ Stage1 闭环筛查（S0–S4 五组 × 3 种子 × 100k）→ G1（最迟 11-20 去留）→ Stage2 正式验证（5 种子 × 500k，正式测试种子 20000–20299）→ G2（约 12-20 冻结）→ Stage3 写作，投 IJCAI 2027。
4. 编号：Stage0–3 是实验阶段；P0–P5 只是技术模块编号，不代表执行顺序（D38 起 P2 与简化 P4 在 Stage1 一起做，P3/P1b/KL 触发后置，P5 在主线外）；R0-x 是 Stage0 实验；S0–S4 是同时训练的对比组；G0–G2 是通过/停止检查点。
5. 文档分三类（见 README）：
   - 维护中：ROADMAP、PROGRESS、DECISIONS、EVALUATION（只保留通用协议，规模以 ROADMAP 为准）、ENV、agent_logs；
   - 参考：SYSTEM_PIPELINE、WM_RESEARCH_DESIGN、RELATED_WORK、RESEARCH_GOAL、RESEARCH_EXPERIMENTS、RESEARCH_RECORDS、P1_MEMORY_PLAN、P0–P5 模块文档，这些只提供背景，不决定顺序；
   - 历史：doc/archive/。REVIEW、WORKFLOW_GUIDE、P0_ACCEPTANCE、P0_BASELINE、NODE01_DOCKER_ADMIN、P0/REMEDIATION_PLAN 已移入 archive/20260928-docs028/，不要再引用或更新。
6. DECISIONS 只保留现行有效决策。D02、D10、D14、D25、D26、D28、D29、D30 因与现行决策冲突，已移到 archive/20260928-docs028/DECISIONS-superseded.md，不得再作为依据，编号不复用。追加新决策前先查当前最大编号（现为 D40）。
7. PROGRESS：顶部看板给出当前阶段与下一个检查点；任务分“进行中/待验收”“已完成”“旧阶段行”三表。新任务加到“进行中”表，完成后移到“已完成”。P1-B/P2-MIN/P2-SEQ/P3/P4/P5 这些旧模块行不再作为执行单元。
8. 当前状态：工作区已改名为 /home/ybc/projects/CL-FoReM（15:53，内容不变；文档中的旧路径按新路径理解）。Stage0 此前的执行已被用户停止、残留已清理，由用户按 doc/agent_logs/20260928-stage0-prompt-v2.md 启动新的执行 Agent；其他 Agent 不要并行启动 Stage0 或 Stage1 的实验。已退出的 mmhusky-p1-* 容器已删除；mmhusky-node01、mmhusky-node01-gz 仍在运行，不要停止。
9. 其余规则不变：遵守 AGENTS.md 第2节，在 doc 中登记、记录证据、交接；新行为默认关闭，关闭时与基线逐元素一致；判据先预登记；未经要求不 commit。
```
