# 冻结下层与当前改进方案比较

任务ID TASK9-COMPARE-20261104；Codex；开始2026-11-04T09:19:57.967381+08:00；active。用户要求解释当前改进相对冻结下层的主要变化；仅只读配置/任务记录与文档，不运行模型/实验。已沿本次状态核查读取AGENTS/README/PROGRESS与相关任务；分支codex/task9-lower-improve，既有dirty保留。实际模型/强度未知；推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，因需区分历史B3与同期B1的不同对照关系。

## 结果与交接

状态done（比较说明交付）。原始逐字段核查见[配置快照](20261104-codex-sac-comparison-configs.json)。

- 冻结版本是B3-5M三final，沿SRC-1356；新提案是从头B1-L，正式同期对照为从头B1，不是旧B3。
- 对历史B3-5M：B1-L的actor/critic仍是linear_transfers、1e-4到1e-6，归一化预算5M变3M；alpha从rllib及1e-4到1e-6，改为capped规则及固定alpha LR1e-6。capped只是现实现名，不应解释成严格alpha上界。更新间隔10、环境256、batch256和replay100k未变。3M与5M预算差异不能直接作因果优劣判断。
- 对同期B1：只有actor/critic的exp_updates改成linear_transfers；alpha两组相同。B1原3M末LR约7.586e-5，L在3M末1e-6；这是待验证假设，不是已证更优。
- 新诊断覆盖首拒绝实际输入/动作、IK/碰撞、候选与零动作stall、最终原因；字段不可得保持unknown。诊断并非新策略输入。工程监督/恢复/成本/时效与独立检查加强不等于策略能力提高。
- 正式长训尚0（沿SRC-1416），没有新能力/效率改善实测。网络/观测/奖励/动作/碰撞等科学语义保持；没有加入世界模型或恢复包装。9.5/9.10负结果不自动组合入B1-L。
- 证据：SRC-1356/1359/1387/1388/1390/1413/1414及[SRC-1418](../../SOURCES.md#src-1418)。下一步仍以已定9.11门与预算为准，本轮无运行任务/待停止进程，也不授权恢复。

记录维护：原拟SRC-1417已由另项只读审核占用，首次追加断言中止并保留其内容；重读后使用新稳定编号。未覆盖其审核/进度。git diff --check通过。
