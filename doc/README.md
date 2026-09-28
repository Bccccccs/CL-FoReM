# 文档索引

更新：2026-09-28（DOCS-028 文档架构调整）。项目：在 Husky+UR5 / N²M² / SAC 上加入 SC²-WM 式世界模型闭环，暂定投稿 IJCAI 2027（D37）。

## 先看这三份

1. **[ROADMAP.md](ROADMAP.md)：唯一执行计划**。方法、整体流程、每阶段的实验/对照/规模/判据/决策点。
2. **[PROGRESS.md](PROGRESS.md)**：现在谁在做什么，顶部看板给出当前阶段与下一个决策点。
3. **[AGENTS.md](../AGENTS.md)**：协作硬规则（文档登记、证据落盘、不越权操作）。

## 文档分三类

**A. 维护中（改计划/记决策/记进度就改这些）**

| 文档 | 职责 |
|---|---|
| [ROADMAP](ROADMAP.md) | 执行计划（唯一） |
| [PROGRESS](PROGRESS.md) | 任务状态 |
| [DECISIONS](DECISIONS.md) | 决策记录，追加前先查最大编号 |
| [EVALUATION](EVALUATION.md) | 通用评测与统计协议（manifest、指标、配对统计）；各阶段具体规模以 ROADMAP 为准 |
| [ENV](../ENV.md) | 运行环境与容器用法 |
| [agent_logs/](agent_logs/TEMPLATE.md) | 每个任务一份记录 |

**B. 参考（背景知识，按需读，不决定执行顺序）**

| 文档 | 内容 |
|---|---|
| [SYSTEM_PIPELINE](SYSTEM_PIPELINE.md) | 现有系统真实数据流/控制流与插入位置 |
| [WM_RESEARCH_DESIGN](WM_RESEARCH_DESIGN.md) | 方法因果时序、候选创新与 claim 账本 |
| [RELATED_WORK](RELATED_WORK.md) | 相关工作矩阵与创新边界 |
| [RESEARCH_GOAL](RESEARCH_GOAL.md) | 研究问题与停止条件 |
| [RESEARCH_EXPERIMENTS](RESEARCH_EXPERIMENTS.md) | 历史结果审计、数据版本与曝光记录 |
| [RESEARCH_RECORDS](RESEARCH_RECORDS.md) | 可用资产、复现与交接 |
| [P1_MEMORY_PLAN](P1_MEMORY_PLAN.md) | P1 有界内存链路 |
| 模块文档 [P0](P0/README.md) · [P1](P1_WORLD_MODEL.md) · [P2](P2_CORRECTION.md) · [P3](P3_MEMORY.md) · [P4](P4_ADAPTATION.md) · [P5](P5_LANGUAGE.md) | 各技术模块的接口与实现细节；其中的"依赖/顺序"已被 ROADMAP 与 D38 取代 |
| [agent_logs/20260928-logic-review.md](agent_logs/20260928-logic-review.md) | LOGIC-028 逻辑审查，ROADMAP §5 的来源 |

**C. 历史（不再维护，仅溯源）**

全部移入 [archive/](archive/)：`20260928-docs028/` 内为 DOCS-028 归档的 REVIEW（09-22 审查）、WORKFLOW_GUIDE（已并入 ROADMAP）、P0_ACCEPTANCE/P0_BASELINE（迁移占位）、NODE01_DOCKER_ADMIN（管理员配置）、P0-REMEDIATION_PLAN；另有 09-21 旧 AGENTS 与用户原始研究要求。09-22 的 4 份 P0 日志正文在迁移中缺失，详见 RESEARCH_RECORDS。

## 编号速查

Stage0–3 = 实验阶段；P0–P5 = 技术模块（不是顺序）；R0-x = Stage0 实验；S0–S4 = 对比组；G0–G2 = 通过/停止检查点；F1 = 设计冻结；Dxx = 决策。详见 ROADMAP §10。
